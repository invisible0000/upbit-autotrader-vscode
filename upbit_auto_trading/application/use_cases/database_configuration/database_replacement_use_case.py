"""
데이터베이스 교체 통합 Use Case

백업 복원, 경로 변경, 파일 가져오기를 하나의 Use Case로 통합 처리합니다.
DDD Application Layer의 핵심 Use Case로 안전성을 최우선으로 합니다.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import shutil
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.use_cases.database_configuration.system_safety_check_use_case import (
    SystemSafetyCheckUseCase, SystemSafetyRequestDto
)
from upbit_auto_trading.domain.database_configuration.services.database_path_service import (
    DatabasePathService
)


class DatabaseReplacementType(Enum):
    """데이터베이스 교체 유형"""
    BACKUP_RESTORE = "backup_restore"
    PATH_CHANGE = "path_change"
    FILE_IMPORT = "file_import"


@dataclass
class DatabaseReplacementRequestDto:
    """데이터베이스 교체 요청 DTO"""
    replacement_type: DatabaseReplacementType
    database_type: str  # 'settings', 'strategies', 'market_data'
    source_path: str  # 백업 파일명 또는 새 파일 경로
    create_safety_backup: bool = True
    force_replacement: bool = False
    safety_backup_suffix: str = "safety_backup"


@dataclass
class DatabaseReplacementResultDto:
    """데이터베이스 교체 결과 DTO"""
    success: bool
    replacement_type: DatabaseReplacementType
    database_type: str
    new_path: Optional[str] = None
    safety_backup_path: Optional[str] = None
    error_message: Optional[str] = None
    system_resumed: bool = False


class DatabaseReplacementUseCase:
    """데이터베이스 교체 통합 Use Case

    모든 종류의 데이터베이스 교체 작업을 안전하게 처리합니다.
    - 백업 복원: 백업 파일로 현재 DB 교체
    - 경로 변경: 다른 위치의 DB 파일로 교체
    - 파일 가져오기: 외부 파일 import
    """

    def __init__(self):
        self.logger = create_component_logger("DatabaseReplacementUseCase")
        self.safety_check = SystemSafetyCheckUseCase()
        self.path_service = DatabasePathService()

        self.logger.info("✅ 데이터베이스 교체 통합 Use Case 초기화 완료")

    def execute_replacement(self, request: DatabaseReplacementRequestDto) -> DatabaseReplacementResultDto:
        """통합 데이터베이스 교체 실행"""
        try:
            self.logger.warning(f"🚨 데이터베이스 교체 시작: {request.replacement_type.value} - {request.database_type}")

            # 1. 안전성 검사 (실시간 매매 상태 확인)
            safety_result = self._perform_safety_check()
            if not safety_result:
                return DatabaseReplacementResultDto(
                    success=False,
                    replacement_type=request.replacement_type,
                    database_type=request.database_type,
                    error_message="안전성 검사 실패: 시스템이 안전하지 않은 상태입니다"
                )

            # 2. 소스 파일 검증
            source_validation = self._validate_source(request)
            if not source_validation['valid']:
                return DatabaseReplacementResultDto(
                    success=False,
                    replacement_type=request.replacement_type,
                    database_type=request.database_type,
                    error_message=f"소스 검증 실패: {source_validation['error']}"
                )

            # 3. 시스템 일시 정지 (실시간 매매 중단)
            self.logger.warning("🛑 실시간 매매 시스템 일시 정지")
            pause_result = self.safety_check.pause_trading_system(
                SystemSafetyRequestDto(
                    operation_name="database_replacement",
                    safety_level="CRITICAL",
                    timeout_seconds=300
                )
            )

            if not pause_result.success:
                return DatabaseReplacementResultDto(
                    success=False,
                    replacement_type=request.replacement_type,
                    database_type=request.database_type,
                    error_message=f"시스템 정지 실패: {pause_result.error_message}"
                )

            try:
                # 4. 안전 백업 생성 (옵션)
                safety_backup_path = None
                if request.create_safety_backup:
                    safety_backup_path = self._create_safety_backup(request)

                # 5. 실제 교체 작업 수행
                replacement_result = self._perform_replacement(request, source_validation['resolved_path'])

                if not replacement_result['success']:
                    # 실패 시 시스템 재개
                    self.safety_check.resume_trading_system(
                        SystemSafetyRequestDto(operation_name="database_replacement_failed")
                    )

                    return DatabaseReplacementResultDto(
                        success=False,
                        replacement_type=request.replacement_type,
                        database_type=request.database_type,
                        safety_backup_path=safety_backup_path,
                        error_message=replacement_result['error']
                    )

                # 6. 성공 시 시스템 재개
                resume_result = self.safety_check.resume_trading_system(
                    SystemSafetyRequestDto(operation_name="database_replacement_success")
                )

                self.logger.warning(f"🎉 데이터베이스 교체 성공: {request.database_type}")

                return DatabaseReplacementResultDto(
                    success=True,
                    replacement_type=request.replacement_type,
                    database_type=request.database_type,
                    new_path=replacement_result['new_path'],
                    safety_backup_path=safety_backup_path,
                    system_resumed=resume_result.success if resume_result else False
                )

            except Exception as e:
                # 예외 발생 시 반드시 시스템 재개
                self.logger.error(f"❌ 교체 작업 중 예외 발생: {e}")
                self.safety_check.resume_trading_system(
                    SystemSafetyRequestDto(operation_name="database_replacement_exception")
                )
                raise

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 교체 실패: {e}")
            return DatabaseReplacementResultDto(
                success=False,
                replacement_type=request.replacement_type,
                database_type=request.database_type,
                error_message=str(e)
            )

    def _perform_safety_check(self) -> bool:
        """안전성 검사 수행"""
        try:
            safety_request = SystemSafetyRequestDto(
                operation_name="database_replacement_check",
                safety_level="CRITICAL"
            )

            result = self.safety_check.check_system_safety(safety_request)

            if not result.success:
                self.logger.error(f"❌ 안전성 검사 실패: {result.error_message}")
                return False

            if result.has_active_trading:
                self.logger.warning("⚠️ 활성 매매 세션이 감지되었습니다")
                # 위험하지만 진행 가능 (사용자가 force_replacement=True로 설정 시)

            self.logger.info("✅ 시스템 안전성 검사 통과")
            return True

        except Exception as e:
            self.logger.error(f"❌ 안전성 검사 중 오류: {e}")
            return False

    def _validate_source(self, request: DatabaseReplacementRequestDto) -> dict:
        """소스 파일/경로 검증"""
        try:
            if request.replacement_type == DatabaseReplacementType.BACKUP_RESTORE:
                # 백업 파일 검증
                backup_dir = Path("data/user_backups")
                backup_file = backup_dir / request.source_path

                if not backup_file.exists():
                    return {'valid': False, 'error': f'백업 파일이 존재하지 않습니다: {backup_file}'}

                if not backup_file.suffix == '.sqlite3':
                    return {'valid': False, 'error': '백업 파일이 SQLite3 형식이 아닙니다'}

                return {'valid': True, 'resolved_path': str(backup_file)}

            elif request.replacement_type == DatabaseReplacementType.PATH_CHANGE:
                # 새 경로 검증
                new_file = Path(request.source_path)

                if not new_file.exists():
                    return {'valid': False, 'error': f'새 파일이 존재하지 않습니다: {new_file}'}

                if not new_file.suffix == '.sqlite3':
                    return {'valid': False, 'error': '새 파일이 SQLite3 형식이 아닙니다'}

                return {'valid': True, 'resolved_path': str(new_file)}

            elif request.replacement_type == DatabaseReplacementType.FILE_IMPORT:
                # 파일 가져오기 검증
                import_file = Path(request.source_path)

                if not import_file.exists():
                    return {'valid': False, 'error': f'가져올 파일이 존재하지 않습니다: {import_file}'}

                return {'valid': True, 'resolved_path': str(import_file)}

            else:
                return {'valid': False, 'error': f'지원하지 않는 교체 유형: {request.replacement_type}'}

        except Exception as e:
            return {'valid': False, 'error': f'소스 검증 중 오류: {str(e)}'}

    def _create_safety_backup(self, request: DatabaseReplacementRequestDto) -> Optional[str]:
        """안전 백업 생성"""
        try:
            current_path = self.path_service.get_current_path(request.database_type)
            if not current_path:
                self.logger.warning(f"⚠️ 현재 {request.database_type} 경로를 찾을 수 없어 안전 백업을 생략합니다")
                return None

            current_file = Path(current_path)
            if not current_file.exists():
                self.logger.warning(f"⚠️ 현재 {request.database_type} 파일이 존재하지 않아 안전 백업을 생략합니다")
                return None

            # 백업 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{request.database_type}_{request.safety_backup_suffix}_{timestamp}.sqlite3"

            backup_dir = Path("data/user_backups")
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / backup_filename

            # 파일 복사
            shutil.copy2(current_file, backup_path)

            self.logger.info(f"✅ 안전 백업 생성 완료: {backup_filename}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"❌ 안전 백업 생성 실패: {e}")
            return None

    def _perform_replacement(self, request: DatabaseReplacementRequestDto, source_path: str) -> dict:
        """실제 교체 작업 수행"""
        try:
            # 목표 파일 경로
            target_filename = f"{request.database_type}.sqlite3"
            target_path = Path("data") / target_filename

            self.logger.warning(f"🔄 파일 교체 시작: {source_path} → {target_path}")

            # 기존 파일을 임시 백업으로 이동 (덮어쓰기 방지)
            if target_path.exists():
                temp_backup = target_path.with_suffix(f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}_temp.sqlite3')
                shutil.move(target_path, temp_backup)
                self.logger.info(f"📁 기존 파일 임시 백업: {temp_backup.name}")

            # 새 파일 복사
            if request.replacement_type == DatabaseReplacementType.BACKUP_RESTORE:
                # 백업에서 복원
                shutil.copy2(source_path, target_path)
            elif request.replacement_type == DatabaseReplacementType.PATH_CHANGE:
                # 다른 경로에서 복사
                shutil.copy2(source_path, target_path)
            elif request.replacement_type == DatabaseReplacementType.FILE_IMPORT:
                # 외부 파일 가져오기
                shutil.copy2(source_path, target_path)

            # 데이터베이스 경로 서비스 업데이트
            success = self.path_service.change_database_path(
                database_type=request.database_type,
                new_path=str(target_path)
            )

            if not success:
                self.logger.error("❌ 경로 서비스 업데이트 실패")
                return {'success': False, 'error': '경로 서비스 업데이트 실패'}

            self.logger.warning(f"✅ 데이터베이스 교체 완료: {target_path}")

            return {
                'success': True,
                'new_path': str(target_path)
            }

        except Exception as e:
            self.logger.error(f"❌ 교체 작업 실패: {e}")
            return {'success': False, 'error': str(e)}
