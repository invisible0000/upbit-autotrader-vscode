"""
Database Validation Use Case

데이터베이스 무결성 검증 및 상태 체크를 담당하는 Use Case입니다.
실거래/백테스팅 환경에서 데이터베이스의 안전성을 보장합니다.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import sqlite3
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.dto.database_config_dto import (
    DatabaseValidationResultDto, DatabaseStatusDto, DatabaseTypeEnum,
    ValidationRequestDto, DatabaseHealthCheckDto
)
from upbit_auto_trading.domain.database_configuration.repositories.idatabase_config_repository import (
    IDatabaseConfigRepository
)
from upbit_auto_trading.domain.exceptions.domain_exceptions import DomainException


class DatabaseValidationUseCase:
    """데이터베이스 검증 Use Case"""

    def __init__(self, repository: IDatabaseConfigRepository):
        self._repository = repository
        self._logger = create_component_logger("DatabaseValidation")

    async def validate_database_profile(
        self,
        request: ValidationRequestDto
    ) -> DatabaseValidationResultDto:
        """데이터베이스 프로필의 무결성을 검증합니다."""
        self._logger.info(f"🔍 데이터베이스 검증 시작: {request.profile_id}")

        try:
            # 프로필 로드
            profile = await self._repository.load_profile(request.profile_id)
            if profile is None:
                return DatabaseValidationResultDto(
                    profile_id=request.profile_id,
                    is_valid=False,
                    validation_errors=["프로필을 찾을 수 없습니다"],
                    warnings=[],
                    validation_performed_at=datetime.now()
                )

            validation_errors = []
            warnings = []

            # 1. 파일 존재 확인
            if not profile.file_path.exists():
                validation_errors.append(f"데이터베이스 파일이 존재하지 않습니다: {profile.file_path}")
            else:
                # 2. 파일 접근 권한 확인
                if not self._check_file_permissions(profile.file_path):
                    validation_errors.append("데이터베이스 파일에 대한 읽기/쓰기 권한이 없습니다")

                # 3. SQLite 형식 검증
                sqlite_validation = await self._validate_sqlite_format(profile.file_path)
                if not sqlite_validation["is_valid"]:
                    validation_errors.extend(sqlite_validation["errors"])
                warnings.extend(sqlite_validation["warnings"])

                # 4. 스키마 검증 (요청 시)
                if request.validate_schema:
                    schema_validation = await self._validate_database_schema(
                        profile.file_path,
                        profile.database_type
                    )
                    if not schema_validation["is_valid"]:
                        validation_errors.extend(schema_validation["errors"])
                    warnings.extend(schema_validation["warnings"])

                # 5. 성능 검증 (요청 시)
                if request.check_performance:
                    performance_validation = await self._validate_database_performance(profile.file_path)
                    warnings.extend(performance_validation["warnings"])

            is_valid = len(validation_errors) == 0

            result = DatabaseValidationResultDto(
                profile_id=request.profile_id,
                is_valid=is_valid,
                validation_errors=validation_errors,
                warnings=warnings,
                validation_performed_at=datetime.now(),
                file_size_bytes=profile.file_path.stat().st_size if profile.file_path.exists() else None,
                schema_version=await self._get_schema_version(profile.file_path) if is_valid else None
            )

            self._logger.info(f"✅ 데이터베이스 검증 완료: {request.profile_id} (유효: {is_valid})")
            return result

        except Exception as e:
            self._logger.error(f"❌ 데이터베이스 검증 실패: {e}")
            return DatabaseValidationResultDto(
                profile_id=request.profile_id,
                is_valid=False,
                validation_errors=[f"검증 중 시스템 오류 발생: {e}"],
                warnings=[],
                validation_performed_at=datetime.now()
            )

    async def perform_health_check(
        self,
        database_type: Optional[DatabaseTypeEnum] = None
    ) -> List[DatabaseHealthCheckDto]:
        """데이터베이스 건강 상태를 확인합니다."""
        self._logger.info(f"🏥 데이터베이스 건강 상태 확인 시작: {database_type}")

        try:
            health_checks = []

            # 모든 활성 프로필의 건강 상태 확인
            active_profiles = await self._repository.get_active_profiles()

            for db_type, profile in active_profiles.items():
                # 타입 필터 적용
                if database_type:
                    profile_type = self._map_domain_to_dto_type(db_type)
                    if profile_type != database_type:
                        continue

                health_check = await self._check_profile_health(profile)
                health_checks.append(health_check)

            self._logger.info(f"✅ 건강 상태 확인 완료: {len(health_checks)}개 프로필")
            return health_checks

        except Exception as e:
            self._logger.error(f"❌ 건강 상태 확인 실패: {e}")
            return []

    async def validate_database_compatibility(
        self,
        source_profile_id: str,
        target_profile_id: str
    ) -> DatabaseValidationResultDto:
        """두 데이터베이스 간의 호환성을 검증합니다."""
        self._logger.info(f"🔄 호환성 검증 시작: {source_profile_id} -> {target_profile_id}")

        try:
            source_profile = await self._repository.load_profile(source_profile_id)
            target_profile = await self._repository.load_profile(target_profile_id)

            validation_errors = []
            warnings = []

            if source_profile is None:
                validation_errors.append(f"원본 프로필을 찾을 수 없습니다: {source_profile_id}")

            if target_profile is None:
                validation_errors.append(f"대상 프로필을 찾을 수 없습니다: {target_profile_id}")

            if source_profile and target_profile:
                # 타입 호환성 확인
                if source_profile.database_type != target_profile.database_type:
                    validation_errors.append(
                        f"데이터베이스 타입이 다릅니다: {source_profile.database_type} vs {target_profile.database_type}"
                    )

                # 스키마 버전 호환성 확인
                source_version = await self._get_schema_version(source_profile.file_path)
                target_version = await self._get_schema_version(target_profile.file_path)

                if source_version and target_version:
                    if source_version != target_version:
                        warnings.append(
                            f"스키마 버전이 다릅니다: 원본={source_version}, 대상={target_version}"
                        )

            is_valid = len(validation_errors) == 0

            result = DatabaseValidationResultDto(
                profile_id=f"{source_profile_id}->{target_profile_id}",
                is_valid=is_valid,
                validation_errors=validation_errors,
                warnings=warnings,
                validation_performed_at=datetime.now()
            )

            self._logger.info(f"✅ 호환성 검증 완료: {is_valid}")
            return result

        except Exception as e:
            self._logger.error(f"❌ 호환성 검증 실패: {e}")
            return DatabaseValidationResultDto(
                profile_id=f"{source_profile_id}->{target_profile_id}",
                is_valid=False,
                validation_errors=[f"호환성 검증 중 오류 발생: {e}"],
                warnings=[],
                validation_performed_at=datetime.now()
            )

    def _check_file_permissions(self, file_path: Path) -> bool:
        """파일 권한 확인"""
        try:
            # 읽기 권한 확인
            with open(file_path, 'rb') as f:
                f.read(1)

            # 쓰기 권한 확인 (임시 파일로 테스트)
            test_file = file_path.with_suffix('.permission_test')
            test_file.touch()
            test_file.unlink()

            return True

        except (PermissionError, OSError):
            return False

    async def _validate_sqlite_format(self, file_path: Path) -> Dict[str, Any]:
        """SQLite 파일 형식 검증"""
        errors = []
        warnings = []

        try:
            with sqlite3.connect(str(file_path)) as conn:
                # 기본 SQLite 무결성 검사
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]

                if integrity_result != "ok":
                    errors.append(f"SQLite 무결성 검사 실패: {integrity_result}")

                # WAL 모드 확인
                cursor.execute("PRAGMA journal_mode")
                journal_mode = cursor.fetchone()[0]
                if journal_mode.lower() != "wal":
                    warnings.append(f"권장되지 않는 저널 모드: {journal_mode} (WAL 권장)")

                # 외래 키 제약조건 확인
                cursor.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                if fk_violations:
                    errors.append(f"외래 키 제약조건 위반: {len(fk_violations)}개")

        except sqlite3.Error as e:
            errors.append(f"SQLite 접근 오류: {e}")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def _validate_database_schema(
        self,
        file_path: Path,
        database_type: str
    ) -> Dict[str, Any]:
        """데이터베이스 스키마 검증"""
        errors = []
        warnings = []

        try:
            with sqlite3.connect(str(file_path)) as conn:
                cursor = conn.cursor()

                # 필수 테이블 확인
                required_tables = self._get_required_tables(database_type)
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = {row[0] for row in cursor.fetchall()}

                missing_tables = required_tables - existing_tables
                if missing_tables:
                    errors.extend([f"필수 테이블 누락: {table}" for table in missing_tables])

                # 테이블 구조 검증
                for table in existing_tables & required_tables:
                    table_validation = await self._validate_table_structure(cursor, table, database_type)
                    errors.extend(table_validation["errors"])
                    warnings.extend(table_validation["warnings"])

        except sqlite3.Error as e:
            errors.append(f"스키마 검증 중 오류: {e}")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def _validate_database_performance(self, file_path: Path) -> Dict[str, Any]:
        """데이터베이스 성능 검증"""
        warnings = []

        try:
            file_size = file_path.stat().st_size

            # 파일 크기 경고
            if file_size > 100 * 1024 * 1024:  # 100MB
                warnings.append(f"데이터베이스 파일이 큽니다: {file_size / 1024 / 1024:.1f}MB")

            with sqlite3.connect(str(file_path)) as conn:
                cursor = conn.cursor()

                # 인덱스 사용률 확인 (간단한 체크)
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
                index_count = cursor.fetchone()[0]

                if index_count == 0:
                    warnings.append("인덱스가 정의되어 있지 않습니다 (성능 저하 가능)")

        except Exception as e:
            warnings.append(f"성능 검증 중 오류: {e}")

        return {"warnings": warnings}

    async def _check_profile_health(self, profile) -> DatabaseHealthCheckDto:
        """프로필 건강 상태 확인"""
        health_status = "healthy"
        issues = []
        last_checked = datetime.now()

        try:
            # 파일 존재 확인
            if not profile.file_path.exists():
                health_status = "error"
                issues.append("데이터베이스 파일이 존재하지 않습니다")
                return DatabaseHealthCheckDto(
                    profile_id=profile.profile_id,
                    database_type=self._map_domain_to_dto_type(profile.database_type),
                    health_status=health_status,
                    issues=issues,
                    last_checked=last_checked
                )

            # 기본 연결 테스트
            with sqlite3.connect(str(profile.file_path), timeout=5.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")

                # 파일 크기 확인
                file_size = profile.file_path.stat().st_size
                if file_size > 500 * 1024 * 1024:  # 500MB
                    health_status = "warning"
                    issues.append(f"데이터베이스 파일이 큽니다: {file_size / 1024 / 1024:.1f}MB")

        except sqlite3.OperationalError as e:
            health_status = "error"
            issues.append(f"데이터베이스 연결 실패: {e}")
        except Exception as e:
            health_status = "warning"
            issues.append(f"건강 상태 확인 중 오류: {e}")

        return DatabaseHealthCheckDto(
            profile_id=profile.profile_id,
            database_type=self._map_domain_to_dto_type(profile.database_type),
            health_status=health_status,
            issues=issues,
            last_checked=last_checked,
            file_size_bytes=profile.file_path.stat().st_size if profile.file_path.exists() else None
        )

    async def _get_schema_version(self, file_path: Path) -> Optional[str]:
        """스키마 버전 확인"""
        try:
            with sqlite3.connect(str(file_path)) as conn:
                cursor = conn.cursor()
                # 스키마 버전 테이블이 있는지 확인
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='schema_version'
                """)

                if cursor.fetchone():
                    cursor.execute("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1")
                    result = cursor.fetchone()
                    return result[0] if result else None

                return "unknown"

        except sqlite3.Error:
            return None

    async def _validate_table_structure(
        self,
        cursor,
        table_name: str,
        database_type: str
    ) -> Dict[str, Any]:
        """테이블 구조 검증"""
        errors = []
        warnings = []

        try:
            # 테이블 정보 조회
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            # 기본적인 컬럼 존재 확인 (id, created_at 등)
            column_names = {col[1] for col in columns}

            # 공통 필수 컬럼 확인
            if 'id' not in column_names:
                warnings.append(f"테이블 {table_name}에 id 컬럼이 없습니다")

            # 데이터베이스 타입별 특정 검증 로직은 향후 추가

        except sqlite3.Error as e:
            errors.append(f"테이블 {table_name} 구조 검증 오류: {e}")

        return {
            "errors": errors,
            "warnings": warnings
        }

    def _get_required_tables(self, database_type: str) -> set:
        """데이터베이스 타입별 필수 테이블 목록"""
        table_mapping = {
            "settings": {
                "tv_trading_variables", "tv_variable_parameters",
                "tv_comparison_groups", "tv_placeholder_texts", "tv_help_texts"
            },
            "strategies": {
                "trading_conditions", "strategy_profiles", "backtest_results"
            },
            "market_data": {
                "price_data", "volume_data", "indicator_cache"
            }
        }
        return table_mapping.get(database_type, set())

    @staticmethod
    def _map_domain_to_dto_type(domain_type: str) -> DatabaseTypeEnum:
        """도메인 타입을 DTO 타입으로 변환"""
        mapping = {
            "settings": DatabaseTypeEnum.SETTINGS,
            "strategies": DatabaseTypeEnum.STRATEGIES,
            "market_data": DatabaseTypeEnum.MARKET_DATA
        }
        return mapping.get(domain_type, DatabaseTypeEnum.SETTINGS)
