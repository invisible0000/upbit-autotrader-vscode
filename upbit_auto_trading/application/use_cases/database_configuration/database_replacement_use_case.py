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
from upbit_auto_trading.infrastructure.configuration import PathServiceFactory
from upbit_auto_trading.infrastructure.repositories.repository_container import RepositoryContainer

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
        self.path_service = PathServiceFactory.get_path_service()
        self.repository_container = RepositoryContainer()

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

            if not pause_result.is_safe_for_backup:
                return DatabaseReplacementResultDto(
                    success=False,
                    replacement_type=request.replacement_type,
                    database_type=request.database_type,
                    error_message=f"시스템 정지 실패: {', '.join(pause_result.blocking_operations)}"
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
                    system_resumed=resume_result.is_safe_for_backup if resume_result else False
                )

            except Exception as e:
                # 예외 발생 시 반드시 시스템 재개 및 임시 파일 정리
                self.logger.error(f"❌ 교체 작업 중 예외 발생: {e}")

                # 시스템 재개
                self.safety_check.resume_trading_system(
                    SystemSafetyRequestDto(operation_name="database_replacement_exception")
                )

                # 임시 파일 정리 (실패 시에도 실행)
                try:
                    self._cleanup_temp_files(request.database_type)
                    self.logger.info("✅ 실패 시 임시 파일 정리 완료")
                except Exception as cleanup_error:
                    self.logger.warning(f"⚠️ 실패 시 임시 파일 정리 실패: {cleanup_error}")

                raise

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 교체 실패: {e}")

            # 최종 실패 시에도 임시 파일 정리 시도
            try:
                self._cleanup_temp_files(request.database_type)
                self.logger.info("✅ 최종 실패 시 임시 파일 정리 완료")
            except Exception as cleanup_error:
                self.logger.warning(f"⚠️ 최종 실패 시 임시 파일 정리 실패: {cleanup_error}")

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

            if not result.is_safe_for_backup:
                self.logger.error(f"❌ 안전성 검사 실패: {', '.join(result.blocking_operations)}")
                return False

            if result.is_trading_active:
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

            # 백업 파일명 생성 (표준 형식: {database_type}_backup_{timestamp}.sqlite3)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{request.database_type}_backup_{timestamp}.sqlite3"

            self.logger.info(f"🏷️ 표준 백업 파일명 생성: {backup_filename}")

            backup_dir = Path("data/user_backups")
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / backup_filename

            self.logger.info(f"📁 백업 디렉토리 준비: {backup_dir}")
            self.logger.info(f"📋 백업 대상: {current_file} → {backup_path}")

            # 파일 복사 (상세 로깅)
            self.logger.info(f"📥 파일 복사 시작: {current_file.stat().st_size} bytes")
            shutil.copy2(current_file, backup_path)
            self.logger.info(f"✅ 파일 복사 완료: {backup_path.stat().st_size} bytes")

            # 백업 메타데이터 설정 (타입별 자동 설명)
            backup_type = "복원생성" if "restore" in request.safety_backup_suffix else "경로변경"
            self._set_backup_metadata(backup_filename, backup_type)
            self.logger.info(f"📋 백업 메타데이터 설정 완료: {backup_type}")

            self.logger.info(f"✅ 안전 백업 생성 완료: {backup_filename}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"❌ 안전 백업 생성 실패: {e}")
            return None

    def _perform_replacement(self, request: DatabaseReplacementRequestDto, source_path: str) -> dict:
        """실제 교체 작업 수행 (대용량 파일 최적화)"""
        try:
            # 목표 파일 경로 (절대 경로로 변환)
            target_filename = f"{request.database_type}.sqlite3"
            target_path = Path("data").resolve() / target_filename

            # 파일 크기 확인 및 처리 전략 결정
            source_size = Path(source_path).stat().st_size
            size_mb = source_size / (1024 * 1024)

            self.logger.warning(f"🔄 파일 교체 시작: {source_path} → {target_path}")
            self.logger.info(f"📊 파일 크기: {size_mb:.1f} MB")

            # 🔒 CRITICAL: 모든 데이터베이스 연결 해제 (Infrastructure Layer 활용)
            self.logger.info("🔌 모든 데이터베이스 연결 해제 중...")
            self.repository_container.close_all_connections()

            # Windows에서 파일 잠금 해제를 위한 충분한 대기 시간
            import time
            import gc

            # 가비지 컬렉션 강제 실행으로 파일 핸들 정리
            gc.collect()

            # Windows 파일 잠금 해제를 위한 대기 (2초)
            self.logger.info("⏳ Windows 파일 잠금 해제 대기 중... (2초)")
            time.sleep(2.0)

            # 추가 검증: 파일 접근 가능 여부 확인
            max_retries = 5
            for retry in range(max_retries):
                try:
                    # 임시로 파일 열어보기 (배타적 모드로 테스트)
                    with open(target_path, 'r+b'):
                        pass  # 단순히 열기만 하고 닫기
                    self.logger.info("✅ 파일 잠금 해제 확인됨")
                    break
                except (PermissionError, OSError) as e:
                    if retry < max_retries - 1:
                        self.logger.warning(f"⚠️ 파일 여전히 잠김 (재시도 {retry + 1}/{max_retries}): {e}")
                        time.sleep(1.0)
                    else:
                        self.logger.error(f"❌ 파일 잠금 해제 실패: {e}")
                        raise PermissionError(f"데이터베이스 파일이 사용 중입니다: {target_path}")

            self.logger.info("✅ 데이터베이스 연결 해제 및 파일 잠금 해제 완료")

            # 성능 최적화: 대용량 파일(100MB 이상)의 경우 원본 이동 전략 사용
            if size_mb > 100 and request.replacement_type == DatabaseReplacementType.PATH_CHANGE:
                self.logger.info("🚀 대용량 파일 최적화 모드: 이동 전략 사용")
                return self._perform_optimized_replacement(target_path, source_path, request)
            else:
                # 기존 안전한 복사 전략 사용
                return self._perform_safe_replacement(target_path, source_path, request)

        except Exception as e:
            self.logger.error(f"❌ 교체 작업 실패: {e}")
            return {'success': False, 'error': str(e)}

    def _perform_safe_replacement(self, target_path: Path, source_path: str, request: DatabaseReplacementRequestDto) -> dict:
        """안전한 복사 기반 교체 (기존 방식)"""
        try:
            # 기존 파일을 임시 백업으로 이동 (덮어쓰기 방지)
            if target_path.exists():
                temp_backup = target_path.with_suffix(f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}_temp.sqlite3')
                shutil.move(target_path, temp_backup)
                self.logger.info(f"📁 기존 파일 임시 백업: {temp_backup.name}")

            # 새 파일 복사
            if request.replacement_type == DatabaseReplacementType.BACKUP_RESTORE:
                shutil.copy2(source_path, target_path)
                self.logger.info("✅ 백업에서 복원 완료")
            elif request.replacement_type == DatabaseReplacementType.PATH_CHANGE:
                shutil.copy2(source_path, target_path)
                self.logger.info("✅ 경로 변경 복사 완료")
            elif request.replacement_type == DatabaseReplacementType.FILE_IMPORT:
                shutil.copy2(source_path, target_path)
                self.logger.info("✅ 외부 파일 가져오기 완료")

            return self._finalize_replacement(target_path, request)

        except Exception as e:
            self.logger.error(f"❌ 안전한 교체 실패: {e}")
            return {'success': False, 'error': str(e)}

    def _perform_optimized_replacement(self, target_path: Path, source_path: str,
                                       request: DatabaseReplacementRequestDto) -> dict:
        """최적화된 이동 기반 교체 (대용량 파일용)"""
        try:
            # 기존 파일 임시 이름으로 이동 (복사 없이 이동만)
            if target_path.exists():
                temp_backup = target_path.with_suffix(f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}_temp.sqlite3')
                shutil.move(target_path, temp_backup)
                self.logger.info(f"📁 기존 파일 임시 이동: {temp_backup.name}")

            # 소스 파일을 목표 위치로 이동 (복사 없음 - 빠름)
            if request.replacement_type == DatabaseReplacementType.PATH_CHANGE:
                shutil.move(source_path, target_path)
                self.logger.info("🚀 최적화 이동 완료 (복사 생략)")
            else:
                # 백업 복원이나 외부 가져오기는 여전히 복사 필요
                shutil.copy2(source_path, target_path)
                self.logger.info("✅ 복사 기반 교체 완료")

            return self._finalize_replacement(target_path, request)

        except Exception as e:
            self.logger.error(f"❌ 최적화 교체 실패: {e}")
            return {'success': False, 'error': str(e)}

    def _finalize_replacement(self, target_path: Path, request: DatabaseReplacementRequestDto) -> dict:
        """교체 작업 마무리"""
        try:
            success = self.path_service.change_database_path(
                database_type=request.database_type,
                new_path=str(target_path)
            )

            if not success:
                self.logger.error("❌ 경로 서비스 업데이트 실패")
                return {'success': False, 'error': '경로 서비스 업데이트 실패'}

            # 임시 파일 정리 (temp.sqlite3 파일들 삭제)
            self._cleanup_temp_files(request.database_type)

            self.logger.warning(f"✅ 데이터베이스 교체 완료: {target_path}")

            return {
                'success': True,
                'new_path': str(target_path)
            }

        except Exception as e:
            self.logger.error(f"❌ 교체 작업 실패: {e}")
            return {'success': False, 'error': str(e)}

    def _set_backup_metadata(self, backup_filename: str, backup_type: str) -> None:
        """백업 메타데이터 설정"""
        try:
            import json
            import os

            # 메타데이터 파일 경로
            metadata_path = Path("data/user_backups/backup_metadata.json")
            metadata = {}

            # 기존 메타데이터 로드
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            # 백업 ID 생성 (확장자 포함으로 일관성 유지)
            backup_id = backup_filename if backup_filename.endswith('.sqlite3') else f"{backup_filename}.sqlite3"

            # 타입별 설명 생성 (간소화된 형식)
            timestamp = datetime.now().isoformat()
            type_descriptions = {
                "복원생성": "[복원생성] 복원 전 안전 백업",
                "경로변경": "[경로변경] 경로 변경 전 안전 백업",
                "수동생성": "[수동생성] 수동 백업"
            }

            # 메타데이터 업데이트
            metadata[backup_id] = {
                "description": type_descriptions.get(backup_type, f"{backup_type} - {timestamp}"),
                "backup_type": backup_type,
                "updated_at": timestamp
            }

            # 메타데이터 저장
            os.makedirs(metadata_path.parent, exist_ok=True)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            self.logger.info(f"✅ 백업 메타데이터 설정: {backup_type} - {backup_id}")

        except Exception as e:
            self.logger.error(f"❌ 백업 메타데이터 설정 실패: {e}")
            # 메타데이터 설정 실패는 백업 프로세스를 중단하지 않음

    def _cleanup_temp_files(self, database_type: str) -> None:
        """임시 파일 정리 (temp.sqlite3 파일들 삭제)"""
        try:
            data_dir = Path("data")
            if not data_dir.exists():
                return

            # 해당 데이터베이스 타입의 임시 파일들 찾기
            temp_pattern = f"{database_type}.*_temp.sqlite3"
            temp_files = list(data_dir.glob(temp_pattern))

            if not temp_files:
                self.logger.debug(f"🗑️ 정리할 임시 파일 없음: {temp_pattern}")
                return

            # 임시 파일들 삭제
            deleted_count = 0
            for temp_file in temp_files:
                try:
                    temp_file.unlink()
                    deleted_count += 1
                    self.logger.info(f"🗑️ 임시 파일 삭제: {temp_file.name}")
                except Exception as e:
                    self.logger.warning(f"⚠️ 임시 파일 삭제 실패: {temp_file.name} - {e}")

            if deleted_count > 0:
                self.logger.info(f"✅ 임시 파일 정리 완료: {deleted_count}개 삭제")

        except Exception as e:
            self.logger.warning(f"⚠️ 임시 파일 정리 중 오류: {e}")
            # 임시 파일 정리 실패는 전체 프로세스를 중단하지 않음
