"""
Database Configuration Application Service

데이터베이스 설정 관련 모든 Use Case를 조합하여 일관된 애플리케이션 서비스를 제공합니다.
DDD Application Layer의 주요 진입점 역할을 합니다.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.dto.database_config_dto import (
    DatabaseProfileDto, CreateProfileRequestDto, UpdateProfileRequestDto,
    SwitchProfileRequestDto, DatabaseValidationResultDto, ValidationRequestDto,
    DatabaseStatusDto, DatabaseTypeEnum, BackupRecordDto, CreateBackupRequestDto,
    RestoreBackupRequestDto, TradingStateDto, DatabaseHealthCheckDto,
    DatabaseStatsDto
)
from upbit_auto_trading.application.use_cases.database_configuration.database_profile_management_use_case import (
    DatabaseProfileManagementUseCase
)
from upbit_auto_trading.application.use_cases.database_configuration.database_backup_management_use_case import (
    DatabaseBackupManagementUseCase
)
from upbit_auto_trading.application.use_cases.database_configuration.database_validation_use_case import (
    DatabaseValidationUseCase
)
from upbit_auto_trading.application.use_cases.database_configuration.database_status_query_use_case import (
    DatabaseStatusQueryUseCase
)

class DatabaseConfigurationService:
    """데이터베이스 설정 애플리케이션 서비스"""

    def __init__(
        self,
        profile_management_use_case: DatabaseProfileManagementUseCase,
        backup_management_use_case: DatabaseBackupManagementUseCase,
        validation_use_case: DatabaseValidationUseCase,
        status_query_use_case: DatabaseStatusQueryUseCase
    ):
        self._profile_management = profile_management_use_case
        self._backup_management = backup_management_use_case
        self._validation = validation_use_case
        self._status_query = status_query_use_case
        self._logger = create_component_logger("DatabaseConfigurationService")

    # ========================================
    # 프로필 관리 메서드들
    # ========================================

    async def create_database_profile(
        self,
        request: CreateProfileRequestDto
    ) -> DatabaseProfileDto:
        """새로운 데이터베이스 프로필을 생성합니다."""
        self._logger.info(f"🔧 프로필 생성 요청: {request.profile_name}")
        return await self._profile_management.create_profile(request)

    async def update_database_profile(
        self,
        request: UpdateProfileRequestDto
    ) -> DatabaseProfileDto:
        """데이터베이스 프로필을 업데이트합니다."""
        self._logger.info(f"🔧 프로필 업데이트 요청: {request.profile_id}")
        return await self._profile_management.update_profile(request)

    async def switch_database_profile(
        self,
        request: SwitchProfileRequestDto,
        trading_state: Optional[TradingStateDto] = None
    ) -> DatabaseProfileDto:
        """데이터베이스 프로필을 전환합니다."""
        self._logger.info(f"🔄 프로필 전환 요청: {request.target_profile_id}")

        # 전환 전 검증
        validation_request = ValidationRequestDto(
            profile_id=request.target_profile_id,
            validate_schema=True,
            check_performance=False
        )
        validation_result = await self._validation.validate_database_profile(validation_request)

        if not validation_result.is_valid:
            raise ValueError(f"대상 프로필이 유효하지 않습니다: {', '.join(validation_result.validation_errors)}")

        return await self._profile_management.switch_database_profile(request, trading_state)

    async def remove_database_profile(self, profile_id: str) -> bool:
        """데이터베이스 프로필을 제거합니다."""
        self._logger.info(f"🗑️ 프로필 제거 요청: {profile_id}")
        return await self._profile_management.remove_profile(profile_id)

    async def get_database_profile(self, profile_id: str) -> Optional[DatabaseProfileDto]:
        """프로필 정보를 조회합니다."""
        return await self._profile_management.get_profile_by_id(profile_id)

    async def get_profiles_by_type(self, database_type: DatabaseTypeEnum) -> List[DatabaseProfileDto]:
        """타입별 프로필 목록을 조회합니다."""
        return await self._profile_management.get_profiles_by_type(database_type)

    async def get_active_profile(self, database_type: DatabaseTypeEnum) -> Optional[DatabaseProfileDto]:
        """타입별 활성 프로필을 조회합니다."""
        return await self._profile_management.get_active_profile(database_type)

    # ========================================
    # 백업 관리 메서드들
    # ========================================

    async def create_backup(
        self,
        request: CreateBackupRequestDto,
        trading_state: Optional[TradingStateDto] = None
    ) -> BackupRecordDto:
        """데이터베이스 백업을 생성합니다."""
        self._logger.info(f"💾 백업 생성 요청: {request.profile_id}")
        return await self._backup_management.create_backup(request, trading_state)

    async def restore_backup(
        self,
        request: RestoreBackupRequestDto,
        trading_state: Optional[TradingStateDto] = None
    ) -> bool:
        """백업에서 데이터베이스를 복원합니다."""
        self._logger.info(f"🔄 백업 복원 요청: {request.backup_id}")
        return await self._backup_management.restore_backup(request, trading_state)

    async def get_backup_records(self, profile_id: str) -> List[BackupRecordDto]:
        """프로필별 백업 기록을 조회합니다."""
        return await self._backup_management.get_backup_records_by_profile(profile_id)

    async def get_backup_record(self, backup_id: str) -> Optional[BackupRecordDto]:
        """백업 기록을 조회합니다."""
        return await self._backup_management.get_backup_record(backup_id)

    async def delete_backup(self, backup_id: str) -> bool:
        """백업을 삭제합니다."""
        self._logger.info(f"🗑️ 백업 삭제 요청: {backup_id}")
        return await self._backup_management.delete_backup(backup_id)

    async def cleanup_old_backups(self, cutoff_date: datetime) -> int:
        """오래된 백업들을 정리합니다."""
        self._logger.info(f"🧹 백업 정리 요청: {cutoff_date} 이전")
        return await self._backup_management.cleanup_old_backups(cutoff_date)

    # ========================================
    # 검증 메서드들
    # ========================================

    async def validate_database_profile(
        self,
        request: ValidationRequestDto
    ) -> DatabaseValidationResultDto:
        """데이터베이스 프로필을 검증합니다."""
        self._logger.info(f"🔍 데이터베이스 검증 요청: {request.profile_id}")
        return await self._validation.validate_database_profile(request)

    async def validate_backup(self, backup_id: str) -> DatabaseValidationResultDto:
        """백업 파일을 검증합니다."""
        self._logger.info(f"🔍 백업 검증 요청: {backup_id}")
        return await self._backup_management.validate_backup(backup_id)

    async def validate_database_compatibility(
        self,
        source_profile_id: str,
        target_profile_id: str
    ) -> DatabaseValidationResultDto:
        """두 프로필 간의 호환성을 검증합니다."""
        self._logger.info(f"🔄 호환성 검증 요청: {source_profile_id} -> {target_profile_id}")
        return await self._validation.validate_database_compatibility(source_profile_id, target_profile_id)

    async def perform_health_check(
        self,
        database_type: Optional[DatabaseTypeEnum] = None
    ) -> List[DatabaseHealthCheckDto]:
        """데이터베이스 건강 상태를 확인합니다."""
        self._logger.info(f"🏥 건강 상태 확인 요청: {database_type}")
        return await self._validation.perform_health_check(database_type)

    # ========================================
    # 상태 조회 메서드들
    # ========================================

    async def get_database_status(
        self,
        database_type: Optional[DatabaseTypeEnum] = None
    ) -> List[DatabaseStatusDto]:
        """데이터베이스 상태를 조회합니다."""
        return await self._status_query.get_current_database_status(database_type)

    async def get_database_statistics(
        self,
        profile_id: str,
        include_table_stats: bool = True
    ) -> Optional[DatabaseStatsDto]:
        """데이터베이스 통계를 조회합니다."""
        return await self._status_query.get_database_statistics(profile_id, include_table_stats)

    async def monitor_database_connections(self) -> Dict[str, Any]:
        """데이터베이스 연결 상태를 모니터링합니다."""
        return await self._status_query.monitor_database_connections()

    async def get_database_activity_log(
        self,
        profile_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """데이터베이스 활동 로그를 조회합니다."""
        return await self._status_query.get_database_activity_log(profile_id, hours)

    async def check_database_disk_usage(self) -> Dict[str, Any]:
        """데이터베이스 디스크 사용량을 확인합니다."""
        return await self._status_query.check_database_disk_usage()

    # ========================================
    # 복합 작업 메서드들 (여러 Use Case 조합)
    # ========================================

    async def safe_profile_switch_with_backup(
        self,
        request: SwitchProfileRequestDto,
        trading_state: Optional[TradingStateDto] = None,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """백업을 생성한 후 안전하게 프로필을 전환합니다."""
        self._logger.info(f"🔄 안전한 프로필 전환 시작: {request.target_profile_id}")

        result = {
            "success": False,
            "profile": None,
            "backup_id": None,
            "validation_result": None,
            "error": None
        }

        try:
            # 1. 대상 프로필 검증
            validation_request = ValidationRequestDto(
                profile_id=request.target_profile_id,
                validate_schema=True,
                check_performance=True
            )
            validation_result = await self._validation.validate_database_profile(validation_request)
            result["validation_result"] = validation_result

            if not validation_result.is_valid:
                result["error"] = f"대상 프로필이 유효하지 않습니다: {', '.join(validation_result.validation_errors)}"
                return result

            # 2. 현재 활성 프로필의 백업 생성 (요청 시)
            if create_backup:
                current_profile = await self._profile_management.get_active_profile(request.database_type)
                if current_profile:
                    backup_request = CreateBackupRequestDto(
                        profile_id=current_profile.profile_id,
                        description=f"프로필 전환 전 자동 백업 - {datetime.now().isoformat()}"
                    )
                    backup_record = await self._backup_management.create_backup(backup_request, trading_state)
                    result["backup_id"] = backup_record.backup_id

            # 3. 프로필 전환
            switched_profile = await self._profile_management.switch_database_profile(request, trading_state)
            result["profile"] = switched_profile
            result["success"] = True

            self._logger.info(f"✅ 안전한 프로필 전환 완료: {request.target_profile_id}")

        except Exception as e:
            self._logger.error(f"❌ 안전한 프로필 전환 실패: {e}")
            result["error"] = str(e)

        return result

    async def comprehensive_database_health_report(self) -> Dict[str, Any]:
        """포괄적인 데이터베이스 건강 상태 보고서를 생성합니다."""
        self._logger.info("📋 종합 건강 상태 보고서 생성 시작")

        report = {
            "timestamp": datetime.now(),
            "overall_status": "healthy",
            "database_statuses": [],
            "health_checks": [],
            "disk_usage": {},
            "connection_monitoring": {},
            "recommendations": []
        }

        try:
            # 1. 모든 데이터베이스 상태 조회
            all_statuses = await self._status_query.get_current_database_status()
            report["database_statuses"] = all_statuses

            # 2. 건강 상태 확인
            health_checks = await self._validation.perform_health_check()
            report["health_checks"] = health_checks

            # 3. 디스크 사용량 확인
            disk_usage = await self._status_query.check_database_disk_usage()
            report["disk_usage"] = disk_usage

            # 4. 연결 모니터링
            connection_info = await self._status_query.monitor_database_connections()
            report["connection_monitoring"] = connection_info

            # 5. 전체 상태 평가
            error_count = sum(1 for status in all_statuses if status.status == "ERROR")
            warning_count = sum(1 for status in all_statuses if status.status == "WARNING")

            if error_count > 0:
                report["overall_status"] = "error"
                report["recommendations"].append("오류가 있는 데이터베이스를 즉시 확인하세요")
            elif warning_count > 0:
                report["overall_status"] = "warning"
                report["recommendations"].append("경고가 있는 데이터베이스를 검토하세요")

            # 6. 권장사항 추가
            total_size = report["disk_usage"].get("total_database_size", 0)
            if total_size > 1024 * 1024 * 1024:  # 1GB
                report["recommendations"].append("데이터베이스 크기가 큽니다. 백업 및 정리를 고려하세요")

            self._logger.info("✅ 종합 건강 상태 보고서 생성 완료")

        except Exception as e:
            self._logger.error(f"❌ 종합 건강 상태 보고서 생성 실패: {e}")
            report["error"] = str(e)
            report["overall_status"] = "error"

        return report
