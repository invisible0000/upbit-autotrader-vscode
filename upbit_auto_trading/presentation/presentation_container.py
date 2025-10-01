"""
Presentation Container - UI Layer 전담 DI 컨테이너
Clean Architecture Presentation Layer의 모든 UI 서비스를 중앙 관리

DDD Architecture:
- Presentation Layer만 전담하는 독립적인 Container
- Infrastructure Layer (ExternalDependencyContainer) 의존성
- Application Layer (ApplicationServiceContainer) 의존성
- UI Services, MVP Presenters, Style Management 총괄
"""

from dependency_injector import containers, providers
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("PresentationContainer")


class PresentationContainer(containers.DeclarativeContainer):
    """
    Presentation Layer 전담 DI 컨테이너

    UI Services Management:
    - MainWindow Presenter (MVP 패턴 핵심)
    - Application UI Services (Screen, Window, Menu)
    - UI Infrastructure (Navigation, StatusBar)
    - Theme & Style Management (UI 일관성)

    External Dependencies:
    - ExternalDependencyContainer (Infrastructure 서비스)
    - ApplicationServiceContainer (Business 서비스)
    """

    # Configuration
    config = providers.Configuration()

    # External Container Dependencies (주입받을 예정)
    external_container = providers.Dependency()
    application_container = providers.Dependency()

    # =============================================================================
    # UI Infrastructure Providers
    # =============================================================================

    # Style Manager는 ExternalDependencyContainer에서 관리됨 (Infrastructure Layer)

    # Navigation Bar Service
    navigation_service = providers.Factory(
        "upbit_auto_trading.ui.desktop.common.widgets.navigation_bar.NavigationBar"
    )

    # Status Bar Service (DatabaseHealthService 의존성)
    status_bar_service = providers.Factory(
        "upbit_auto_trading.ui.desktop.common.widgets.status_bar.StatusBar",
        database_health_service=providers.Factory(
            "upbit_auto_trading.application.services.database_health_service.DatabaseHealthService"
        )
    )

    # =============================================================================
    # Application UI Services Providers
    # =============================================================================

    # Screen Manager Service (ApplicationServiceContainer 연동 - 백업본과 동일)
    screen_manager_service = providers.Factory(
        "upbit_auto_trading.application.services.screen_manager_service.ScreenManagerService",
        application_container=application_container
    )

    # Window State Service (순수 UI 상태 관리)
    window_state_service = providers.Factory(
        "upbit_auto_trading.application.services.window_state_service.WindowStateService"
    )

    # Menu Service (UI 메뉴 관리)
    menu_service = providers.Factory(
        "upbit_auto_trading.application.services.menu_service.MenuService"
    )

    # =============================================================================
    # MainWindow Presenter - MVP 패턴 완전 구현
    # =============================================================================

    # MainWindowPresenter - MVP 패턴 완전 구현 (백업본과 동일한 services Dict 패턴)
    main_window_presenter = providers.Factory(
        "upbit_auto_trading.presentation.presenters.main_window_presenter.MainWindowPresenter",
        services=providers.Dict(
            # Infrastructure Services (ExternalDependencyContainer에서)
            theme_service=external_container.provided.theme_service,
            api_key_service=external_container.provided.api_key_service,

            # UI Infrastructure (현재 Container에서)
            navigation_bar=navigation_service,
            database_health_service=providers.Factory(
                "upbit_auto_trading.application.services.database_health_service.DatabaseHealthService"
            ),

            # Application UI Services (현재 Container에서 - 백업본 순서와 동일)
            screen_manager_service=screen_manager_service,
            window_state_service=window_state_service,
            menu_service=menu_service
        )
    )


# =============================================================================
# Container 유틸리티 함수들
# =============================================================================

def create_presentation_container(
    external_container,
    application_container
) -> PresentationContainer:
    """
    PresentationContainer 인스턴스 생성 및 외부 의존성 주입

    Args:
        external_container: ExternalDependencyContainer 인스턴스
        application_container: ApplicationServiceContainer 인스턴스

    Returns:
        PresentationContainer: 의존성이 주입된 컨테이너 인스턴스
    """
    container = PresentationContainer()

    # 외부 Container 의존성 주입
    container.external_container.override(external_container)
    container.application_container.override(application_container)

    logger.info("✅ PresentationContainer 생성 완료 (외부 의존성 주입)")
    return container
