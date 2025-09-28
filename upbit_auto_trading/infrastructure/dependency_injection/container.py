"""
DDD Architecture 기반 애플리케이션 DI 컨테이너
Clean Architecture + dependency-injector 라이브러리 활용
"""

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("DIContainer")


class ApplicationContainer(containers.DeclarativeContainer):
    """
    DDD 아키텍처 기반 애플리케이션 DI 컨테이너

    Clean Architecture 계층별 Provider 구성:
    - Configuration: 환경별 설정 관리
    - Infrastructure: DB, 로깅, 외부 API 클라이언트
    - Domain: 도메인 서비스, 리포지토리 인터페이스
    - Application: 애플리케이션 서비스, Use Case
    - Presentation: UI 서비스, 테마 관리
    """

    # =============================================================================
    # Configuration Provider - 환경별 설정 관리
    # =============================================================================
    config = providers.Configuration()

    # =============================================================================
    # Infrastructure Layer Providers
    # =============================================================================

    # Logging Service (가장 기본이 되는 서비스)
    logging_service = providers.Factory(
        "upbit_auto_trading.infrastructure.logging.create_component_logger",
        name="DIContainer"
    )

    # Database Manager - 3-DB 분리 구조 지원
    database_manager = providers.Singleton(
        "upbit_auto_trading.infrastructure.services.database_connection_service.DatabaseConnectionService"
    )

    # Path Service - 설정 파일 및 DB 경로 관리
    path_service = providers.Singleton(
        "upbit_auto_trading.infrastructure.configuration.get_path_service"
    )

    # Config Loader - 설정 파일 로더
    config_loader = providers.Singleton(
        "upbit_auto_trading.infrastructure.config.loaders.config_loader.ConfigLoader"
    )

    # Settings Service - 애플리케이션 설정 관리
    settings_service = providers.Factory(
        "upbit_auto_trading.infrastructure.services.settings_service.SettingsService",
        config_loader=config_loader
    )

    # =============================================================================
    # Repository Providers - Infrastructure Layer 구현체
    # =============================================================================

    # Secure Keys Repository (SQLite 구현체) - ApiKeyService 의존성
    secure_keys_repository = providers.Singleton(
        "upbit_auto_trading.infrastructure.repositories.sqlite_secure_keys_repository.SqliteSecureKeysRepository",
        db_manager=database_manager
    )

    # Strategy Repository (SQLite 구현체)
    strategy_repository = providers.Singleton(
        "upbit_auto_trading.infrastructure.repositories.sqlite_strategy_repository.SqliteStrategyRepository",
        db_manager=database_manager
    )

    # Trigger Repository (SQLite 구현체)
    trigger_repository = providers.Singleton(
        "upbit_auto_trading.infrastructure.repositories.sqlite_trigger_repository.SqliteTriggerRepository",
        db_manager=database_manager
    )

    # Settings Repository (SQLite 구현체) - 향후 구현 예정
    settings_repository = providers.Singleton(
        # 향후 구현: "upbit_auto_trading.infrastructure.repositories.sqlite_settings_repository.SqliteSettingsRepository",
        # database_manager=database_manager,
        lambda: logger.debug("SettingsRepository Provider - 향후 구현 예정")
    )

    # =============================================================================
    # External API Providers - Infrastructure Layer
    # =============================================================================

    # API Key Service - 보안 키 관리 (SecureKeysRepository 의존성 주입)
    api_key_service = providers.Factory(
        "upbit_auto_trading.infrastructure.services.api_key_service.ApiKeyService",
        secure_keys_repository=secure_keys_repository
    )

    # Upbit Public Client
    upbit_public_client = providers.Singleton(
        # 향후 구현: "upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client.UpbitPublicClient",
        lambda: logger.debug("UpbitPublicClient Provider - 향후 구현 예정")
    )

    # Upbit Private Client
    upbit_private_client = providers.Factory(
        # 향후 구현: "upbit_auto_trading.infrastructure.external_apis.upbit.upbit_private_client.UpbitPrivateClient",
        # api_key_service=api_key_service,
        lambda: logger.debug("UpbitPrivateClient Provider - 향후 구현 예정")
    )

    # =============================================================================
    # Domain Layer Providers - 도메인 서비스
    # =============================================================================

    # Strategy Compatibility Service
    strategy_compatibility_service = providers.Factory(
        "upbit_auto_trading.domain.services.strategy_compatibility_service.StrategyCompatibilityService",
        settings_repository=settings_repository
    )

    # Domain Event Publisher
    domain_event_publisher = providers.Singleton(
        "upbit_auto_trading.domain.events.domain_event_publisher.DomainEventPublisher"
    )

    # =============================================================================
    # Application Layer Providers - Use Case 및 애플리케이션 서비스
    # =============================================================================

    # Trigger Application Service
    trigger_application_service = providers.Factory(
        "upbit_auto_trading.application.services.trigger_application_service.TriggerApplicationService",
        trigger_repository=trigger_repository,
        strategy_repository=strategy_repository,
        settings_repository=settings_repository,
        compatibility_service=strategy_compatibility_service
    )

    # Chart Data Service
    chart_data_service = providers.Factory(
        # 향후 구현: "upbit_auto_trading.application.services.chart_data_service.ChartDataService",
        # upbit_public_client=upbit_public_client,
        lambda: logger.debug("ChartDataService Provider - 향후 구현 예정")
    )

    # Websocket Application Service
    websocket_application_service = providers.Factory(
        # 향후 구현: "upbit_auto_trading.application.services.websocket_application_service.WebsocketApplicationService",
        # upbit_public_client=upbit_public_client,
        lambda: logger.debug("WebsocketApplicationService Provider - 향후 구현 예정")
    )

    # =============================================================================
    # UI Layer Providers - Presentation Layer 서비스
    # =============================================================================

    # Style Manager - 전역 스타일 관리 (Theme Service보다 먼저 정의)
    style_manager = providers.Singleton(
        "upbit_auto_trading.ui.desktop.common.styles.style_manager.StyleManager"
    )

    # Theme Service - UI 테마 관리
    theme_service = providers.Factory(
        "upbit_auto_trading.infrastructure.services.theme_service.ThemeService",
        settings_service=settings_service,
        style_manager=style_manager
    )

    # Navigation Bar Service - 네비게이션 관리
    navigation_service = providers.Factory(
        "upbit_auto_trading.ui.desktop.common.widgets.navigation_bar.NavigationBar"
    )

    # Status Bar Service - 상태 바 관리
    status_bar_service = providers.Factory(
        "upbit_auto_trading.ui.desktop.common.widgets.status_bar.StatusBar",
        database_health_service=providers.Factory(
            "upbit_auto_trading.application.services.database_health_service.DatabaseHealthService"
        )
    )

    # Main Window - 메인 애플리케이션 윈도우
    main_window = providers.Factory(
        "upbit_auto_trading.ui.desktop.main_window.MainWindow"
    )


# =============================================================================
# Container 유틸리티 함수들
# =============================================================================

def create_application_container() -> ApplicationContainer:
    """
    ApplicationContainer 인스턴스 생성 및 기본 설정 로드

    Returns:
        ApplicationContainer: 새로 생성된 컨테이너 인스턴스
    """
    container = ApplicationContainer()

    # 기본 설정 로드 (환경변수 PYTHONUTF8=1로 UTF-8 보장)
    try:
        container.config.from_yaml("config/config.yaml")
        logger.info("✅ ApplicationContainer 생성 완료 (config.yaml 로드)")
    except Exception as e:
        logger.warning(f"⚠️ config.yaml 로드 실패, 기본 설정 사용: {e}")
        # 기본 설정으로 폴백
        container.config.from_dict({
            "database": {
                "fallback_settings_db": "data/settings.sqlite3",
                "fallback_strategies_db": "data/strategies.sqlite3",
                "fallback_market_data_db": "data/market_data.sqlite3"
            },
            "logging": {
                "level": "INFO",
                "console_enabled": True
            },
            "app_name": "Upbit Auto Trading",
            "app_version": "1.0.0"
        })
        logger.info("✅ ApplicationContainer 생성 완료 (기본 설정 사용)")

    return container


def wire_container_modules(container: ApplicationContainer) -> None:
    """
    Container에 애플리케이션 모듈들을 연결 (Wiring)

    @inject 데코레이터를 사용하는 모든 모듈을 여기에 등록해야 함

    Args:
        container: 연결할 ApplicationContainer 인스턴스
    """
    try:
        # wiring할 모듈들 목록
        wiring_modules = [
            # UI Layer
            "upbit_auto_trading.ui.desktop.main_window",
            # "upbit_auto_trading.ui.desktop.screens",

            # Presentation Layer
            # "upbit_auto_trading.presentation.presenters",

            # Application Layer
            # "upbit_auto_trading.application.services",
        ]

        # @inject 데코레이터 활성화를 위한 wiring
        container.wire(modules=wiring_modules)

        logger.info(f"✅ Container wiring 완료: {len(wiring_modules)}개 모듈")

    except Exception as e:
        logger.error(f"❌ Container wiring 실패: {e}")
        raise


def validate_container_registration(container: ApplicationContainer) -> bool:
    """
    Container의 모든 Provider가 정상적으로 등록되었는지 검증

    Args:
        container: 검증할 ApplicationContainer 인스턴스

    Returns:
        bool: 모든 Provider가 정상 등록된 경우 True
    """
    try:
        # 핵심 Provider들의 등록 상태 확인
        core_providers = [
            "config",
            "logging_service",
            "database_manager",
            "path_service"
        ]

        for provider_name in core_providers:
            if not hasattr(container, provider_name):
                logger.error(f"❌ 핵심 Provider 누락: {provider_name}")
                return False

        logger.info("✅ Container 등록 검증 완료")
        return True

    except Exception as e:
        logger.error(f"❌ Container 등록 검증 실패: {e}")
        return False


# =============================================================================
# 전역 Container 관리 (선택적 사용)
# =============================================================================

_global_container: ApplicationContainer = None


def get_global_container() -> ApplicationContainer:
    """
    전역 ApplicationContainer 조회

    싱글톤 패턴으로 전역 컨테이너 관리

    Returns:
        ApplicationContainer: 전역 컨테이너 인스턴스
    """
    global _global_container
    if _global_container is None:
        _global_container = create_application_container()
        logger.info("🌍 전역 ApplicationContainer 초기화 완료")
    return _global_container


def set_global_container(container: ApplicationContainer) -> None:
    """
    전역 ApplicationContainer 설정

    Args:
        container: 설정할 ApplicationContainer 인스턴스
    """
    global _global_container
    _global_container = container
    logger.info("🌍 전역 ApplicationContainer 변경 완료")


def reset_global_container() -> None:
    """
    전역 ApplicationContainer 초기화
    """
    global _global_container
    _global_container = None
    logger.info("🌍 전역 ApplicationContainer 초기화 완료")


# =============================================================================
# Legacy DIContainer 호환성 (임시)
# =============================================================================

# 기존 코드와의 하위 호환성을 위한 임시 Wrapper
# 향후 모든 코드가 @inject 패턴으로 마이그레이션 되면 제거 예정

class LegacyDIContainerWrapper:
    """
    기존 DIContainer와의 호환성을 위한 임시 Wrapper

    Warning: 이 클래스는 마이그레이션 기간 동안만 사용하며,
             향후 모든 코드가 @inject 패턴으로 변경되면 제거됩니다.
    """

    def __init__(self, modern_container: ApplicationContainer):
        self._container = modern_container

    def resolve(self, service_type):
        """기존 resolve() 호출을 새 Container로 위임"""
        logger.warning(f"⚠️ Legacy resolve() 호출 감지: {service_type}. @inject 패턴으로 마이그레이션을 권장합니다.")

        # 기본적인 타입 매핑 (향후 확장)
        type_mapping = {
            # 예시: "ILoggingService": self._container.logging_service,
        }

        provider = type_mapping.get(str(service_type))
        if provider:
            return provider()
        else:
            raise ValueError(f"Legacy 호환성 매핑이 없습니다: {service_type}")
