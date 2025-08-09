"""
통합 데이터베이스 교체 Use Case

백업 복원과 DB 경로 변경을 통합 처리하여 중복 로직을 제거합니다.
두 작업 모두 본질적으로 "현재 DB → 다른 DB"로 교체하는 동일한 작업입니다.
"""

from typing import List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from upbit_auto_trading.infrastructure.logging import create_component_logger


class DatabaseReplacementSourceType(Enum):
    """DB 교체 소스 타입"""
    BACKUP_FILE = "backup_file"      # 백업 파일에서 복원
    EXTERNAL_FILE = "external_file"  # 외부 DB 파일로 교체


class DatabaseReplacementMode(Enum):
    """DB 교체 모드"""
    SAFE_MODE = "safe_mode"          # 안전성 우선 (권장)
    FORCE_MODE = "force_mode"        # 강제 교체 (위험)
    VALIDATION_ONLY = "validation_only"  # 검증만 수행


@dataclass(frozen=True)
class DatabaseReplacementRequestDto:
    """데이터베이스 교체 요청 DTO"""

    database_type: str                            # "settings", "strategies", "market_data"
    source_path: str                              # 소스 파일 경로
    source_type: DatabaseReplacementSourceType    # 소스 타입
    replacement_mode: DatabaseReplacementMode     # 교체 모드
    create_safety_backup: bool = True             # 교체 전 안전 백업 생성
    validate_schema_compatibility: bool = True     # 스키마 호환성 검증
    force_system_pause: bool = False              # 강제 시스템 일시 정지
    rollback_on_failure: bool = True              # 실패 시 자동 롤백


@dataclass(frozen=True)
class DatabaseReplacementResultDto:
    """데이터베이스 교체 결과 DTO"""

    success: bool
    database_type: str
    source_path: str
    target_path: str
    safety_backup_path: Optional[str]
    replacement_timestamp: datetime
    validation_warnings: List[str]
    error_message: Optional[str]
    rollback_performed: bool = False

    def get_summary(self) -> str:
        """교체 결과 요약"""
        if self.success:
            return f"✅ {self.database_type} DB 교체 성공: {Path(self.source_path).name}"
        else:
            return f"❌ {self.database_type} DB 교체 실패: {self.error_message}"


class DatabaseReplacementUseCase:
    """통합 데이터베이스 교체 Use Case"""

    def __init__(self):
        self.logger = create_component_logger("DatabaseReplacementUseCase")

    async def replace_database(self, request: DatabaseReplacementRequestDto) -> DatabaseReplacementResultDto:
        """데이터베이스 교체 실행"""
        try:
            self.logger.info(f"🔄 통합 DB 교체 시작: {request.database_type} <- {Path(request.source_path).name}")

            # 1. 소스 검증
            validation_result = await self._validate_source(request)
            if not validation_result.is_valid:
                return DatabaseReplacementResultDto(
                    success=False,
                    database_type=request.database_type,
                    source_path=request.source_path,
                    target_path="",
                    safety_backup_path=None,
                    replacement_timestamp=datetime.now(),
                    validation_warnings=[],
                    error_message=f"소스 검증 실패: {validation_result.error_message}"
                )

            # 2. 시스템 안전성 검사
            safety_check_result = await self._check_system_safety(request)
            if not safety_check_result.is_safe and request.replacement_mode != DatabaseReplacementMode.FORCE_MODE:
                return DatabaseReplacementResultDto(
                    success=False,
                    database_type=request.database_type,
                    source_path=request.source_path,
                    target_path="",
                    safety_backup_path=None,
                    replacement_timestamp=datetime.now(),
                    validation_warnings=safety_check_result.warnings,
                    error_message="시스템이 안전하지 않은 상태입니다. FORCE_MODE를 사용하거나 안전한 상태에서 다시 시도하세요."
                )

            # 3. 검증만 수행하는 경우
            if request.replacement_mode == DatabaseReplacementMode.VALIDATION_ONLY:
                return DatabaseReplacementResultDto(
                    success=True,
                    database_type=request.database_type,
                    source_path=request.source_path,
                    target_path="검증만 수행",
                    safety_backup_path=None,
                    replacement_timestamp=datetime.now(),
                    validation_warnings=validation_result.warnings,
                    error_message=None
                )

            # 4. 실제 교체 수행
            replacement_result = await self._perform_replacement(request, validation_result, safety_check_result)

            self.logger.info(f"🔄 통합 DB 교체 완료: {replacement_result.get_summary()}")
            return replacement_result

        except Exception as e:
            self.logger.error(f"❌ 통합 DB 교체 실패: {e}")
            return DatabaseReplacementResultDto(
                success=False,
                database_type=request.database_type,
                source_path=request.source_path,
                target_path="",
                safety_backup_path=None,
                replacement_timestamp=datetime.now(),
                validation_warnings=[],
                error_message=str(e)
            )

    async def _validate_source(self, request: DatabaseReplacementRequestDto) -> 'SourceValidationResult':
        """소스 파일 검증"""
        try:
            source_path = Path(request.source_path)

            # 기본 파일 존재성 검증
            if not source_path.exists():
                return SourceValidationResult(
                    is_valid=False,
                    error_message=f"소스 파일이 존재하지 않습니다: {source_path}",
                    warnings=[]
                )

            if not source_path.is_file():
                return SourceValidationResult(
                    is_valid=False,
                    error_message=f"디렉토리는 지원하지 않습니다: {source_path}",
                    warnings=[]
                )

            # SQLite 파일 검증
            sqlite_validation = await self._validate_sqlite_file(source_path)
            if not sqlite_validation.is_valid:
                return sqlite_validation

            # 백업 파일 특별 검증
            warnings = []
            if request.source_type == DatabaseReplacementSourceType.BACKUP_FILE:
                backup_validation = self._validate_backup_filename(source_path.name)
                if not backup_validation:
                    warnings.append("백업 파일명이 표준 형식이 아닙니다")

            # 스키마 호환성 검증 (요청 시)
            if request.validate_schema_compatibility:
                schema_validation = await self._validate_schema_compatibility(request, source_path)
                warnings.extend(schema_validation.warnings)

            return SourceValidationResult(
                is_valid=True,
                error_message=None,
                warnings=warnings
            )

        except Exception as e:
            return SourceValidationResult(
                is_valid=False,
                error_message=f"소스 검증 중 오류: {str(e)}",
                warnings=[]
            )

    async def _validate_sqlite_file(self, file_path: Path) -> 'SourceValidationResult':
        """SQLite 파일 무결성 검증"""
        try:
            import sqlite3

            # 연결 테스트
            with sqlite3.connect(str(file_path)) as conn:
                cursor = conn.cursor()

                # 기본 쿼리 테스트
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()

                # 무결성 검사
                cursor.execute("PRAGMA integrity_check;")
                integrity_result = cursor.fetchone()

                if integrity_result[0] != "ok":
                    return SourceValidationResult(
                        is_valid=False,
                        error_message=f"SQLite 무결성 검사 실패: {integrity_result[0]}",
                        warnings=[]
                    )

                self.logger.info(f"✅ SQLite 검증 성공: {len(tables)}개 테이블")
                return SourceValidationResult(
                    is_valid=True,
                    error_message=None,
                    warnings=[]
                )

        except sqlite3.Error as e:
            return SourceValidationResult(
                is_valid=False,
                error_message=f"SQLite 파일 오류: {str(e)}",
                warnings=[]
            )
        except Exception as e:
            return SourceValidationResult(
                is_valid=False,
                error_message=f"파일 검증 오류: {str(e)}",
                warnings=[]
            )

    async def _validate_schema_compatibility(self, request: DatabaseReplacementRequestDto, source_path: Path) -> 'SourceValidationResult':
        """스키마 호환성 검증"""
        # TODO: 향후 구현
        # 현재 DB와 소스 DB의 스키마 비교
        return SourceValidationResult(
            is_valid=True,
            error_message=None,
            warnings=["스키마 호환성 검증은 향후 구현 예정"]
        )

    async def _check_system_safety(self, request: DatabaseReplacementRequestDto) -> 'SystemSafetyResult':
        """시스템 안전성 검사"""
        try:
            from upbit_auto_trading.application.use_cases.database_configuration.system_safety_check_use_case import (
                SystemSafetyCheckUseCase
            )

            safety_checker = SystemSafetyCheckUseCase()
            safety_status = safety_checker.check_backup_safety()

            return SystemSafetyResult(
                is_safe=safety_status.is_safe_for_backup,
                warnings=safety_status.warning_messages,
                blocking_operations=safety_status.blocking_operations,
                safety_status=safety_status
            )

        except Exception as e:
            self.logger.warning(f"⚠️ 시스템 안전성 검사 실패: {e}")
            return SystemSafetyResult(
                is_safe=False,
                warnings=[f"안전성 검사 오류: {str(e)}"],
                blocking_operations=["시스템 상태 확인 불가"],
                safety_status=None
            )

    async def _perform_replacement(self, request: DatabaseReplacementRequestDto,
                                 validation_result: 'SourceValidationResult',
                                 safety_result: 'SystemSafetyResult') -> DatabaseReplacementResultDto:
        """실제 DB 교체 수행"""
        import shutil

        source_path = Path(request.source_path)
        target_path = Path("data") / f"{request.database_type}.sqlite3"
        safety_backup_path = None
        rollback_performed = False

        try:
            # 1. 안전 백업 생성
            if request.create_safety_backup and target_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safety_backup_name = f"{request.database_type}_safety_backup_{timestamp}.sqlite3"
                safety_backup_path = Path("data/user_backups") / safety_backup_name
                safety_backup_path.parent.mkdir(exist_ok=True)

                shutil.copy2(target_path, safety_backup_path)
                self.logger.info(f"🛡️ 안전 백업 생성: {safety_backup_name}")

            # 2. 시스템 일시 정지 (필요 시)
            system_paused = False
            if not safety_result.is_safe or request.force_system_pause:
                if safety_result.safety_status:
                    from upbit_auto_trading.application.use_cases.database_configuration.system_safety_check_use_case import (
                        SystemSafetyCheckUseCase
                    )
                    safety_checker = SystemSafetyCheckUseCase()
                    system_paused = safety_checker.request_system_pause()
                    self.logger.info("⏸️ 시스템 일시 정지 완료")

            # 3. DB 파일 교체
            shutil.copy2(source_path, target_path)
            self.logger.info(f"🔄 DB 파일 교체 완료: {source_path.name} → {target_path}")

            # 4. 시스템 재개
            if system_paused and safety_result.safety_status:
                safety_checker.request_system_resume()
                self.logger.info("▶️ 시스템 재개 완료")

            return DatabaseReplacementResultDto(
                success=True,
                database_type=request.database_type,
                source_path=str(source_path),
                target_path=str(target_path),
                safety_backup_path=str(safety_backup_path) if safety_backup_path else None,
                replacement_timestamp=datetime.now(),
                validation_warnings=validation_result.warnings,
                error_message=None,
                rollback_performed=rollback_performed
            )

        except Exception as e:
            # 롤백 수행
            if request.rollback_on_failure and safety_backup_path and safety_backup_path.exists():
                try:
                    shutil.copy2(safety_backup_path, target_path)
                    rollback_performed = True
                    self.logger.info("🔄 롤백 완료: 이전 상태로 복구")
                except Exception as rollback_error:
                    self.logger.error(f"❌ 롤백 실패: {rollback_error}")

            return DatabaseReplacementResultDto(
                success=False,
                database_type=request.database_type,
                source_path=str(source_path),
                target_path=str(target_path),
                safety_backup_path=str(safety_backup_path) if safety_backup_path else None,
                replacement_timestamp=datetime.now(),
                validation_warnings=validation_result.warnings,
                error_message=str(e),
                rollback_performed=rollback_performed
            )

    def _validate_backup_filename(self, filename: str) -> bool:
        """백업 파일명 형식 검증"""
        # {database_type}_backup_{timestamp}.sqlite3 형식 확인
        import re
        pattern = r'^(settings|strategies|market_data)_backup_\d{8}_\d{6}\.sqlite3$'
        return bool(re.match(pattern, filename))


@dataclass(frozen=True)
class SourceValidationResult:
    """소스 검증 결과"""
    is_valid: bool
    error_message: Optional[str]
    warnings: List[str]


@dataclass(frozen=True)
class SystemSafetyResult:
    """시스템 안전성 검사 결과"""
    is_safe: bool
    warnings: List[str]
    blocking_operations: List[str]
    safety_status: Optional[Any]  # SystemSafetyStatusDto
