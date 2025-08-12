"""
MVP Container - Presenter와 View를 관리하는 의존성 주입 컨테이너

MVP 패턴의 Presenter들과 View들의 의존성을 관리하고
Application Service Container와 연동하여 완전한 MVP 구조를 제공합니다.
"""

from typing import Optional, Dict, Any

from upbit_auto_trading.application.container import ApplicationServiceContainer
from upbit_auto_trading.presentation.presenters import (
    StrategyMakerPresenter,
    TriggerBuilderPresenter,
    BacktestPresenter,
    SettingsPresenter
)

# Smart Logging v3.0
from upbit_auto_trading.infrastructure.logging import create_component_logger

# TODO: LiveTradingPresenter 구현 후 추가

class MVPContainer:
    """MVP 패턴 구성 요소들의 의존성 주입 컨테이너

    Presenter와 View들을 생성하고 관리하며,
    Application Service Container와 연동하여 완전한 MVP 구조를 제공합니다.
    """

    def __init__(self, application_container: ApplicationServiceContainer):
        """MVP 컨테이너 초기화

        Args:
            application_container: Application Service 컨테이너
        """
        self._app_container = application_container
        self._presenters: Dict[str, Any] = {}
        self._views: Dict[str, Any] = {}

    def create_strategy_maker_presenter(self) -> StrategyMakerPresenter:
        """전략 메이커 Presenter 생성

        Returns:
            StrategyMakerPresenter: 전략 메이커 Presenter
        """
        if "strategy_maker" not in self._presenters:
            strategy_service = self._app_container.get_strategy_service()

            # View는 나중에 연결 (Presenter 생성 후 View에서 주입)
            self._presenters["strategy_maker"] = lambda view: StrategyMakerPresenter(
                view=view,
                strategy_service=strategy_service
            )

        return self._presenters["strategy_maker"]

    def create_trigger_builder_presenter(self) -> TriggerBuilderPresenter:
        """트리거 빌더 Presenter 생성

        Returns:
            TriggerBuilderPresenter: 트리거 빌더 Presenter
        """
        if "trigger_builder" not in self._presenters:
            trigger_service = self._app_container.get_trigger_service()

            self._presenters["trigger_builder"] = lambda view: TriggerBuilderPresenter(
                view=view,
                trigger_service=trigger_service
            )

        return self._presenters["trigger_builder"]

    def create_backtest_presenter(self) -> BacktestPresenter:
        """백테스팅 Presenter 생성

        Returns:
            BacktestPresenter: 백테스팅 Presenter
        """
        if "backtest" not in self._presenters:
            backtest_service = self._app_container.get_backtest_service()

            self._presenters["backtest"] = lambda view: BacktestPresenter(
                view=view,
                backtest_service=backtest_service
            )

        return self._presenters["backtest"]

    def create_settings_presenter(self) -> SettingsPresenter:
        """설정 Presenter 생성

        Returns:
            SettingsPresenter: 설정 Presenter
        """
        if "settings" not in self._presenters:
            # 설정 서비스는 Infrastructure Layer에서 가져옴
            # (설정은 Infrastructure 영역이므로)
            from upbit_auto_trading.infrastructure.services.settings_service import SettingsService
            settings_service = SettingsService()

            self._presenters["settings"] = lambda view: SettingsPresenter(
                view=view,
                settings_service=settings_service
            )

        return self._presenters["settings"]

    # TODO: LiveTradingPresenter 구현 후 활성화
    # def create_live_trading_presenter(self) -> LiveTradingPresenter:
    #     """실시간 거래 Presenter 생성
    #
    #     Returns:
    #         LiveTradingPresenter: 실시간 거래 Presenter
    #     """
    #     if "live_trading" not in self._presenters:
    #         # 실시간 거래 관련 서비스들
    #         # (실제 구현에 따라 조정 필요)
    #         trading_service = None  # TODO: 실시간 거래 서비스 구현 후 연결
    #         market_service = None   # TODO: 시장 데이터 서비스 구현 후 연결
    #
    #         self._presenters["live_trading"] = lambda view: LiveTradingPresenter(
    #             view=view,
    #             trading_service=trading_service,
    #             market_service=market_service
    #         )
    #
    #     return self._presenters["live_trading"]

    def create_strategy_maker_mvp(self):
        """전략 메이커 MVP 조합 생성

        Presenter와 View를 연결한 완전한 MVP 구조를 반환합니다.

        Returns:
            tuple: (presenter, view) 튜플
        """
        from upbit_auto_trading.presentation.views.strategy_maker_view import StrategyMakerView
        from upbit_auto_trading.presentation.presenters.strategy_maker_presenter import StrategyMakerPresenter

        logger = create_component_logger("MVPContainer")

        try:
            # Strategy Service 확보
            strategy_service = self._app_container.get_strategy_service()
            logger.info("📋 StrategyApplicationService 확보 완료")

            # MVP 패턴: View 없이 Presenter 생성 후 연결하는 방식
            # 1. MockView로 임시 초기화 (타입 안전성 확보)
            class DummyView:
                """MVP 초기화용 임시 View"""
                def __getattr__(self, name):
                    return lambda *args, **kwargs: None

            dummy_view = DummyView()

            # 2. Presenter 생성 (dummy_view로 초기화)
            presenter = StrategyMakerPresenter(
                view=dummy_view,  # type: ignore
                strategy_service=strategy_service
            )
            logger.info("🎭 StrategyMakerPresenter 생성 완료")

            # 3. 실제 View 생성 (Presenter와 연결)
            view = StrategyMakerView(presenter=presenter)
            logger.info("🖼️ StrategyMakerView 생성 완료")

            # 4. Presenter에 실제 View 연결 (순환 의존성 해결)
            presenter._view = view
            logger.info("🔗 MVP 패턴 Presenter-View 연결 완료")

            return presenter, view

        except Exception as e:
            logger.error(f"❌ Strategy Maker MVP 생성 실패: {e}")
            raise RuntimeError(f"Strategy Maker MVP 생성 중 오류 발생: {e}") from e

    def create_settings_mvp(self, settings_service=None, parent=None):
        """설정 MVP 조합 생성

        Presenter와 View를 연결한 완전한 Settings MVP 구조를 반환합니다.

        Args:
            settings_service: 외부에서 주입된 SettingsService (옵션)
            parent: 부모 위젯 (DI Container 접근을 위해 필요)

        Returns:
            tuple: (view, presenter) 튜플 - view가 MainWindow에서 사용될 QWidget
        """
        from upbit_auto_trading.ui.desktop.screens.settings.settings_screen import SettingsScreen
        from upbit_auto_trading.presentation.presenters.settings_presenter import SettingsPresenter

        # Settings Service 사용 (외부에서 주입받거나 직접 생성)
        if settings_service is None:
            # 폴백: Infrastructure Layer에서 직접 생성
            try:
                from upbit_auto_trading.infrastructure.services.settings_service import SettingsService
                from upbit_auto_trading.infrastructure.config.config_loader import ConfigLoader
                config_loader = ConfigLoader()
                settings_service = SettingsService(config_loader)
            except Exception:
                settings_service = None

        # View 생성 (QWidget) - parent 파라미터 전달
        settings_view = SettingsScreen(settings_service=settings_service, parent=parent)

        # Presenter 생성 (View와 연결)
        settings_presenter = SettingsPresenter(
            view=settings_view,  # ISettingsView 인터페이스로 전달
            settings_service=settings_service
        )

        return settings_view, settings_presenter

    def clear_cache(self) -> None:
        """Presenter 캐시 초기화"""
        self._presenters.clear()
        self._views.clear()

# 전역 MVP 컨테이너 인스턴스 (필요 시 사용)
_global_mvp_container: Optional[MVPContainer] = None

def get_mvp_container() -> Optional[MVPContainer]:
    """전역 MVP Container 조회

    Returns:
        MVPContainer: 전역 MVP 컨테이너 (없으면 None)
    """
    return _global_mvp_container

def set_mvp_container(container: MVPContainer) -> None:
    """전역 MVP Container 설정

    Args:
        container: 설정할 MVP 컨테이너
    """
    global _global_mvp_container
    _global_mvp_container = container

def initialize_mvp_system(application_container: ApplicationServiceContainer) -> MVPContainer:
    """MVP 시스템 초기화

    Application Container를 받아서 MVP Container를 생성하고 전역으로 설정합니다.

    Args:
        application_container: Application Service 컨테이너

    Returns:
        MVPContainer: 초기화된 MVP 컨테이너
    """
    mvp_container = MVPContainer(application_container)
    set_mvp_container(mvp_container)

    import logging
    logger = logging.getLogger(__name__)
    logger.info("MVP 시스템 초기화 완료: Presenter-View 의존성 주입 준비")

    return mvp_container
