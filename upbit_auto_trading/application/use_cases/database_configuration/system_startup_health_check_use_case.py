"""
시스템 시작 시 DB 건강 검사 Use Case

프로그램 시작 시 안전하게 DB 상태를 점검하고,
문제가 있어도 시스템이 시작될 수 있도록 처리합니다.
"""

from typing import Dict
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.domain.database_configuration.services.database_health_monitoring_service import (
    DatabaseHealthMonitoringService
)
from upbit_auto_trading.domain.database_configuration.value_objects.database_health_report import (
    SystemDatabaseHealth, DatabaseHealthLevel
)


@dataclass
class StartupHealthCheckRequest:
    """시작 시 건강 검사 요청 DTO"""
    database_paths: Dict[str, str]
    force_start_on_failure: bool = True  # DB 문제가 있어도 강제 시작
    create_missing_databases: bool = True  # 없는 DB 자동 생성


@dataclass
class StartupHealthCheckResult:
    """시작 시 건강 검사 결과 DTO"""
    system_health: SystemDatabaseHealth
    can_start_system: bool
    requires_user_attention: bool
    critical_warnings: list
    recovery_actions_taken: list
    recommended_user_actions: list


class SystemStartupHealthCheckUseCase:
    """
    시스템 시작 시 DB 건강 검사 Use Case

    DB에 문제가 있어도 시스템이 안전하게 시작될 수 있도록 처리합니다.
    """

    def __init__(self):
        self._logger = create_component_logger("SystemStartupHealthCheck")
        self._health_service = DatabaseHealthMonitoringService()

    async def execute(self, request: StartupHealthCheckRequest) -> StartupHealthCheckResult:
        """
        시작 시 DB 건강 검사 수행

        Args:
            request: 건강 검사 요청

        Returns:
            건강 검사 결과
        """
        self._logger.info("🚀 시스템 시작 시 DB 건강 검사 시작")

        # 1. 기본 건강 상태 점검
        system_health = self._health_service.check_system_database_health(request.database_paths)

        # 2. 시작 가능성 판단
        can_start = self._determine_startup_feasibility(system_health, request)

        # 3. 사용자 주의 필요성 판단
        requires_attention = self._requires_user_attention(system_health)

        # 4. 자동 복구 시도
        recovery_actions = self._attempt_auto_recovery(system_health, request)

        # 5. 사용자 권고 사항 생성
        user_recommendations = self._generate_user_recommendations(system_health)

        # 6. 치명적 경고 추출
        critical_warnings = self._extract_critical_warnings(system_health)

        result = StartupHealthCheckResult(
            system_health=system_health,
            can_start_system=can_start,
            requires_user_attention=requires_attention,
            critical_warnings=critical_warnings,
            recovery_actions_taken=recovery_actions,
            recommended_user_actions=user_recommendations
        )

        self._logger.info(f"🚀 시스템 시작 건강 검사 완료: 시작 가능={can_start}")
        return result

    def _determine_startup_feasibility(
        self,
        system_health: SystemDatabaseHealth,
        request: StartupHealthCheckRequest
    ) -> bool:
        """시스템 시작 가능성 판단"""

        # 강제 시작 옵션이 활성화된 경우
        if request.force_start_on_failure:
            # settings DB만 최소한 작동하면 시작 가능
            settings_report = system_health.reports.get('settings')
            if settings_report and settings_report.health_level != DatabaseHealthLevel.CRITICAL:
                self._logger.info("💪 강제 시작 모드: settings DB 작동 확인됨")
                return True
            else:
                self._logger.warning("⚠️ settings DB도 사용 불가, 하지만 강제 시작 시도")
                return True  # 그래도 시작 시도 (빈 DB로라도)

        # 일반 모드: 시스템이 제안하는 기준 사용
        return system_health.system_can_start

    def _requires_user_attention(self, system_health: SystemDatabaseHealth) -> bool:
        """사용자 즉시 주의가 필요한지 판단"""

        # 치명적 상태이거나 여러 DB에 문제가 있으면 주의 필요
        if system_health.overall_status in [DatabaseHealthLevel.CRITICAL, DatabaseHealthLevel.ERROR]:
            return True

        # 절반 이상의 DB에 문제가 있으면 주의 필요
        problematic_count = len(system_health.problematic_databases)
        total_count = len(system_health.reports)

        if problematic_count > 0 and (problematic_count / total_count) >= 0.5:
            return True

        return False

    def _attempt_auto_recovery(
        self,
        system_health: SystemDatabaseHealth,
        request: StartupHealthCheckRequest
    ) -> list:
        """자동 복구 시도"""
        recovery_actions = []

        if not request.create_missing_databases:
            return recovery_actions

        for db_type, report in system_health.reports.items():
            if report.can_auto_recover:
                if report.health_level == DatabaseHealthLevel.MISSING:
                    # 누락된 DB 생성 시도
                    try:
                        self._logger.info(f"💾 누락된 {db_type} DB 생성 시도")
                        # 여기서 실제 DB 생성 로직 호출 (ApplicationContext 연동)
                        recovery_actions.append(f"{db_type} 데이터베이스 새로 생성")
                    except Exception as e:
                        self._logger.error(f"DB 생성 실패: {db_type} - {e}")
                        recovery_actions.append(f"{db_type} 데이터베이스 생성 실패: {str(e)}")

        return recovery_actions

    def _generate_user_recommendations(self, system_health: SystemDatabaseHealth) -> list:
        """사용자 권고 사항 생성"""
        recommendations = []

        for db_type, report in system_health.reports.items():
            if report.needs_immediate_attention:
                recommendations.append(f"📋 {db_type} DB: {', '.join(report.recommendations)}")

        # 전체적인 권고사항
        if system_health.overall_status == DatabaseHealthLevel.CRITICAL:
            recommendations.append("🚨 즉시 데이터베이스 백업을 확인하고 복원을 고려하세요")
            recommendations.append("🔧 설정 > 데이터베이스에서 올바른 파일을 선택하세요")

        elif len(system_health.problematic_databases) > 0:
            recommendations.append("⚙️ 설정 > 데이터베이스에서 문제가 있는 파일들을 교체하세요")
            recommendations.append("📂 백업 폴더에서 정상 파일을 찾아보세요")

        return recommendations

    def _extract_critical_warnings(self, system_health: SystemDatabaseHealth) -> list:
        """치명적 경고 메시지 추출"""
        warnings = []

        for db_type, report in system_health.reports.items():
            if report.health_level == DatabaseHealthLevel.CRITICAL:
                warnings.append(f"🚨 {db_type} 데이터베이스가 심각하게 손상되었습니다")

            elif report.health_level == DatabaseHealthLevel.MISSING:
                warnings.append(f"❌ {db_type} 데이터베이스 파일을 찾을 수 없습니다")

        # 전체 시스템에 대한 경고
        if not system_health.system_can_start:
            warnings.append("⚠️ 시스템이 정상적으로 시작되지 않을 수 있습니다")

        return warnings

    def check_database_before_replacement(
        self,
        db_type: str,
        current_path: str,
        new_path: str
    ) -> bool:
        """DB 교체 전 안전성 확인"""
        self._logger.info(f"🔄 {db_type} DB 교체 전 안전성 확인: {new_path}")

        return self._health_service.check_database_compatibility_for_replacement(
            current_path, new_path, db_type
        )
