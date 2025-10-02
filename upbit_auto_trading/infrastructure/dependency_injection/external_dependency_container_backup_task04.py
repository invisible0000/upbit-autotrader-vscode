"""
External Dependency Container - Infrastructure Layer 전담
DDD Architecture 기반 외부 시스템 통합 전용 DI 컨테이너
"""

from dependency_injector import containers, providers

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("ExternalDependencyContainer")


class ExternalDependencyContainer(containers.DeclarativeContainer):
    """
    외부 의존성 DI 컨테이너 - Infrastructure Layer 전담

    External Systems Integration:
    - Database Connections (3-DB 분리 구조)
    - API Clients (Upbit Public/Private)
    - Logging Systems (Component Logger)
    - Configuration Management (Config Loader)
    - Security Services (API Key Management)
    - Path Management (File System Access)

    Clean Architecture Infrastructure Layer의 모든 외부 의존성을
    중앙 집중식으로 관리하여 Domain Layer의 순수성을 보장합니다.
    """

    # =============================================================================
    # Configuration Provider - 환경별 설정 관리
    # =============================================================================
    config = providers.Configuration()

    # =============================================================================
    # Core Infrastructure Providers - 기본 인프라 서비스
    # =============================================================================

    # Logging Service (가장 기본이 되는 서비스)
    logging_service = providers.Factory(
        "upbit_auto_trading.infrastructure.logging.create_component_logger",
        name="ExternalDependencyContainer"
    )

    # Application Layer Logging Service - Settings 컴포넌트용
    application_logging_service = providers.Singleton(
        "upbit_auto_trading.application.services.logging_application_service.create_application_logging_service"
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
    # Domain Layer Providers - 도메인 서비스 (Infrastructure 의존성 주입)
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
    # UI Infrastructure Providers - Presentation Layer Infrastructure
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

    # =============================================================================
    # Repository Container Factory - Application Layer 연동용
    # =============================================================================

    def create_repository_container(container_instance):
        """Repository Container 생성 (ApplicationServiceContainer용)"""
        class RepositoryContainer:
            def __init__(self, container):
                self._container = container

            def get_strategy_repository(self):
                return self._container.strategy_repository()

            def get_trigger_repository(self):
                return self._container.trigger_repository()

            def get_settings_repository(self):
                return self._container.settings_repository()

            def get_compatibility_service(self):
                return self._container.strategy_compatibility_service()

            def get_api_key_service(self):
                return self._container.api_key_service()

            def get_theme_service(self):
                return self._container.theme_service()

            def get_database_manager(self):
                return self._container.database_manager()

        return RepositoryContainer(container_instance)

    # Repository Container - self 참조 방식으로 순환 참조 해결
    repository_container = providers.Factory(
        create_repository_container,
        container_instance=providers.Self
    )


# =============================================================================
# Container 유틸리티 함수들
# =============================================================================

def create_external_dependency_container() -> ExternalDependencyContainer:
    """
    ExternalDependencyContainer 인스턴스 생성 및 기본 설정 로드

    Returns:
        ExternalDependencyContainer: 새로 생성된 컨테이너 인스턴스
    """
    container = ExternalDependencyContainer()

    # 기본 설정 로드 (환경변수 PYTHONUTF8=1로 UTF-8 보장)
    try:
        container.config.from_yaml("config/config.yaml")
        logger.info("✅ ExternalDependencyContainer 생성 완료 (config.yaml 로드)")
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
        logger.info("✅ ExternalDependencyContainer 생성 완료 (기본 설정 사용)")

    return container


def wire_external_dependency_modules(container: ExternalDependencyContainer) -> None:
    """
    Container에 Infrastructure 모듈들을 연결 (Wiring)

    @inject 데코레이터를 사용하는 Infrastructure 모듈을 여기에 등록

    Args:
        container: 연결할 ExternalDependencyContainer 인스턴스
    """
    try:
        # Infrastructure Layer wiring할 모듈들 목록
        wiring_modules = [
            # Infrastructure Services
            "upbit_auto_trading.infrastructure.services",
            "upbit_auto_trading.infrastructure.repositories",

            # External API Modules
            "upbit_auto_trading.infrastructure.external_apis",

            # Configuration Modules
            "upbit_auto_trading.infrastructure.configuration",

            # UI Infrastructure (Theme, Style Manager)
            "upbit_auto_trading.ui.desktop.common.styles",
        ]

        # @inject 데코레이터 활성화를 위한 wiring
        container.wire(modules=wiring_modules)

        logger.info(f"✅ External Dependency Container wiring 완료: {len(wiring_modules)}개 Infrastructure 모듈")

    except Exception as e:
        logger.error(f"❌ External Dependency Container wiring 실패: {e}")
        raise


def validate_external_dependency_container(container: ExternalDependencyContainer) -> bool:
    """
    ExternalDependencyContainer의 모든 Provider가 정상적으로 등록되었는지 검증

    Args:
        container: 검증할 ExternalDependencyContainer 인스턴스

    Returns:
        bool: 모든 Provider가 정상 등록된 경우 True
    """
    try:
        # 핵심 External Dependency Provider들의 등록 상태 확인
        core_providers = [
            "config",
            "logging_service",
            "database_manager",
            "path_service",
            "config_loader",
            "settings_service",
            "api_key_service"
        ]

        for provider_name in core_providers:
            if not hasattr(container, provider_name):
                logger.error(f"❌ 핵심 External Dependency Provider 누락: {provider_name}")
                return False

        logger.info("✅ External Dependency Container 등록 검증 완료")
        return True

    except Exception as e:
        logger.error(f"❌ External Dependency Container 등록 검증 실패: {e}")
        return False


# =============================================================================
# 전역 External Dependency Container 관리
# =============================================================================

_global_external_container: ExternalDependencyContainer = None


def get_external_dependency_container() -> ExternalDependencyContainer:
    """
    전역 ExternalDependencyContainer 조회

    싱글톤 패턴으로 전역 외부 의존성 컨테이너 관리
    Infrastructure Layer의 모든 외부 시스템 연동을 담당합니다.

    Returns:
        ExternalDependencyContainer: 전역 외부 의존성 컨테이너 인스턴스
    """
    global _global_external_container
    if _global_external_container is None:
        _global_external_container = create_external_dependency_container()
        logger.info("🌍 전역 ExternalDependencyContainer 초기화 완료")
    return _global_external_container


def set_external_dependency_container(container: ExternalDependencyContainer) -> None:
    """
    전역 ExternalDependencyContainer 설정

    Args:
        container: 설정할 ExternalDependencyContainer 인스턴스
    """
    global _global_external_container
    _global_external_container = container
    logger.info("🌍 전역 ExternalDependencyContainer 변경 완료")


def reset_external_dependency_container() -> None:
    """
    전역 ExternalDependencyContainer 초기화
    """
    global _global_external_container
    _global_external_container = None
    logger.info("🌍 전역 ExternalDependencyContainer 초기화 완료")


# =============================================================================
# Legacy 호환성 (기존 get_global_container 호출 지원)
# =============================================================================

def get_global_container() -> ExternalDependencyContainer:
    """
    Legacy 호환성을 위한 get_global_container() 별칭

    Warning: 이 함수는 하위 호환성을 위해 제공되며,
             새 코드에서는 get_external_dependency_container()를 사용하세요.

    Returns:
        ExternalDependencyContainer: 외부 의존성 컨테이너 인스턴스
    """
    logger.warning("⚠️ Legacy get_global_container() 호출 감지. get_external_dependency_container() 사용을 권장합니다.")
    return get_external_dependency_container()
