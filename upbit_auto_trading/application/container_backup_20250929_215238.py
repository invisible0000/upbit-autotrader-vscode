"""
Application Service Container - 의존성 주입 컨테이너

Application Service들의 의존성을 관리하고 인스턴스를 제공합니다.
Singleton 패턴으로 구현하여 하나의 서비스 인스턴스만 존재하도록 보장합니다.
"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from upbit_auto_trading.infrastructure.services.api_key_service import ApiKeyService
    from upbit_auto_trading.application.factories.settings_view_factory import SettingsViewFactory

from upbit_auto_trading.application.services.strategy_application_service import StrategyApplicationService
from upbit_auto_trading.application.services.trigger_application_service import TriggerApplicationService
from upbit_auto_trading.application.services.backtest_application_service import BacktestApplicationService
from upbit_auto_trading.application.event_handlers.event_handler_registry import EventHandlerRegistry
from upbit_auto_trading.application.notifications.notification_service import NotificationService
from upbit_auto_trading.application.caching.cache_invalidation_service import CacheInvalidationService
from upbit_auto_trading.domain.events.domain_event_publisher import get_domain_event_publisher

# Settings 관련 Application Services
from upbit_auto_trading.application.services.logging_application_service import (
    ApplicationLoggingService,
    create_application_logging_service
)
from upbit_auto_trading.application.services.settings_application_services import (
    ComponentLifecycleService,
    SettingsValidationService,
    SettingsApplicationService,
    create_component_lifecycle_service,
    create_settings_validation_service,
    create_settings_application_service
)


class ApplicationServiceContainer:
    """Application Service들의 의존성 주입 컨테이너

    Repository Container를 받아서 필요한 Application Service들을 생성하고 관리합니다.
    """

    def __init__(self, repository_container):
        """컨테이너 초기화

        Args:
            repository_container: Repository들을 제공하는 컨테이너
        """
        self._repo_container = repository_container
        self._services = {}

    def get_strategy_service(self) -> StrategyApplicationService:
        """전략 Application Service 조회

        Returns:
            StrategyApplicationService: 전략 관리 서비스
        """
        if "strategy" not in self._services:
            self._services["strategy"] = StrategyApplicationService(
                self._repo_container.get_strategy_repository(),
                self._repo_container.get_compatibility_service()
            )
        return self._services["strategy"]

    def get_trigger_service(self) -> TriggerApplicationService:
        """트리거 Application Service 조회

        Returns:
            TriggerApplicationService: 트리거 관리 서비스
        """
        if "trigger" not in self._services:
            self._services["trigger"] = TriggerApplicationService(
                self._repo_container.get_trigger_repository(),
                self._repo_container.get_strategy_repository(),
                self._repo_container.get_settings_repository(),
                self._repo_container.get_compatibility_service()
            )
        return self._services["trigger"]

    def get_backtest_service(self) -> BacktestApplicationService:
        """백테스팅 Application Service 조회

        Returns:
            BacktestApplicationService: 백테스팅 관리 서비스
        """
        if "backtest" not in self._services:
            self._services["backtest"] = BacktestApplicationService(
                self._repo_container.get_strategy_repository(),
                self._repo_container.get_backtest_repository(),
                self._repo_container.get_market_data_repository()
            )
        return self._services["backtest"]

    def get_notification_service(self) -> NotificationService:
        """알림 서비스 조회

        Returns:
            NotificationService: 알림 관리 서비스
        """
        if "notification" not in self._services:
            self._services["notification"] = NotificationService()
        return self._services["notification"]

    def get_cache_invalidation_service(self) -> CacheInvalidationService:
        """캐시 무효화 서비스 조회

        Returns:
            CacheInvalidationService: 캐시 무효화 서비스
        """
        if "cache_invalidation" not in self._services:
            self._services["cache_invalidation"] = CacheInvalidationService()
        return self._services["cache_invalidation"]

    def get_event_handler_registry(self) -> EventHandlerRegistry:
        """이벤트 핸들러 레지스트리 조회

        Returns:
            EventHandlerRegistry: 이벤트 핸들러 관리 서비스
        """
        if "event_handler_registry" not in self._services:
            self._services["event_handler_registry"] = EventHandlerRegistry(
                self.get_notification_service(),
                self.get_cache_invalidation_service()
            )
        return self._services["event_handler_registry"]

    # =============================================================================
    # Settings 관련 Application Services
    # =============================================================================

    def get_logging_service(self) -> ApplicationLoggingService:
        """로깅 Application Service 조회

        Returns:
            ApplicationLoggingService: 로깅 관리 서비스
        """
        if "logging_service" not in self._services:
            self._services["logging_service"] = create_application_logging_service()
        return self._services["logging_service"]

    def get_component_lifecycle_service(self) -> ComponentLifecycleService:
        """컴포넌트 생명주기 관리 서비스 조회

        Returns:
            ComponentLifecycleService: 컴포넌트 생명주기 관리 서비스
        """
        if "component_lifecycle_service" not in self._services:
            self._services["component_lifecycle_service"] = create_component_lifecycle_service(
                self.get_logging_service()
            )
        return self._services["component_lifecycle_service"]

    def get_settings_validation_service(self) -> SettingsValidationService:
        """Settings 유효성 검증 서비스 조회

        Returns:
            SettingsValidationService: Settings 유효성 검증 서비스
        """
        if "settings_validation_service" not in self._services:
            self._services["settings_validation_service"] = create_settings_validation_service(
                self.get_logging_service()
            )
        return self._services["settings_validation_service"]

    def get_settings_application_service(self) -> SettingsApplicationService:
        """Settings 통합 Application Service 조회

        Returns:
            SettingsApplicationService: Settings 통합 관리 서비스
        """
        if "settings_application_service" not in self._services:
            self._services["settings_application_service"] = create_settings_application_service(
                self.get_logging_service(),
                self.get_component_lifecycle_service(),
                self.get_settings_validation_service()
            )
        return self._services["settings_application_service"]

    def get_api_key_service(self) -> 'ApiKeyService':
        """API Key Service 조회

        Infrastructure DI Container에서 ApiKeyService를 가져옵니다.

        Returns:
            ApiKeyService: API 키 관리 서비스
        """
        if "api_key_service" not in self._services:
            # Infrastructure DI Container에서 ApiKeyService 가져오기
            from upbit_auto_trading.infrastructure.dependency_injection.container import get_global_container

            infrastructure_container = get_global_container()
            self._services["api_key_service"] = infrastructure_container.api_key_service()

        return self._services["api_key_service"]

    def get_settings_view_factory(self) -> 'SettingsViewFactory':
        """Settings View Factory 조회

        Returns:
            SettingsViewFactory: Settings 컴포넌트 생성 Factory
        """
        if "settings_view_factory" not in self._services:
            from upbit_auto_trading.application.factories.settings_view_factory import (
                create_settings_view_factory
            )

            self._services["settings_view_factory"] = create_settings_view_factory(
                settings_app_service=self.get_settings_application_service(),
                logging_service=self.get_logging_service(),
                lifecycle_service=self.get_component_lifecycle_service(),
                validation_service=self.get_settings_validation_service(),
                api_key_service=self.get_api_key_service()
            )
        return self._services["settings_view_factory"]

    def initialize_event_integration(self) -> None:
        """이벤트 시스템 통합 초기화

        DomainEventPublisher와 EventHandlerRegistry를 연동합니다.
        Application 시작 시 한 번 호출되어야 합니다.
        """
        # EventHandlerRegistry 인스턴스 생성
        event_registry = self.get_event_handler_registry()

        # DomainEventPublisher에 EventHandlerRegistry를 글로벌 비동기 핸들러로 등록
        domain_publisher = get_domain_event_publisher()
        domain_publisher.subscribe_global_async(event_registry.handle_event)

        # 로깅
        from upbit_auto_trading.infrastructure.logging import create_component_logger
        logger = create_component_logger("ApplicationContainer")
        logger.info("이벤트 시스템 통합 초기화 완료: DomainEventPublisher ↔ EventHandlerRegistry")

    def clear_cache(self) -> None:
        """서비스 캐시 초기화

        테스트나 재설정이 필요할 때 사용합니다.
        """
        self._services.clear()


# 전역 컨테이너 인스턴스 (필요 시 사용)
_global_container: Optional[ApplicationServiceContainer] = None


def get_application_container() -> Optional[ApplicationServiceContainer]:
    """전역 Application Service Container 조회

    Returns:
        ApplicationServiceContainer: 전역 컨테이너 (없으면 None)
    """
    return _global_container


def set_application_container(container: ApplicationServiceContainer) -> None:
    """전역 Application Service Container 설정

    Args:
        container: 설정할 컨테이너
    """
    global _global_container
    _global_container = container
