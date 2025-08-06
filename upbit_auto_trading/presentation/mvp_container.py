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
    SettingsPresenter,
    LiveTradingPresenter
)


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

    def create_live_trading_presenter(self) -> LiveTradingPresenter:
        """실시간 거래 Presenter 생성

        Returns:
            LiveTradingPresenter: 실시간 거래 Presenter
        """
        if "live_trading" not in self._presenters:
            # 실시간 거래 관련 서비스들
            # (실제 구현에 따라 조정 필요)
            trading_service = None  # TODO: 실시간 거래 서비스 구현 후 연결
            market_service = None   # TODO: 시장 데이터 서비스 구현 후 연결

            self._presenters["live_trading"] = lambda view: LiveTradingPresenter(
                view=view,
                trading_service=trading_service,
                market_service=market_service
            )

        return self._presenters["live_trading"]

    def create_strategy_maker_mvp(self):
        """전략 메이커 MVP 조합 생성

        Presenter와 View를 연결한 완전한 MVP 구조를 반환합니다.

        Returns:
            tuple: (presenter, view) 튜플
        """
        from upbit_auto_trading.presentation.views.strategy_maker_view import StrategyMakerView

        # Presenter 팩토리 함수 생성
        presenter_factory = self.create_strategy_maker_presenter()

        # View를 먼저 생성하고 Presenter에 연결하는 방식으로 순환 의존성 해결
        def create_mvp_pair():
            # 임시 Presenter (View 없이)
            temp_presenter = StrategyMakerPresenter(
                view=None,  # 나중에 설정
                strategy_service=self._app_container.get_strategy_service()
            )

            # View 생성 (Presenter와 연결)
            view = StrategyMakerView(presenter=temp_presenter)

            # Presenter에 View 연결
            temp_presenter._view = view

            return temp_presenter, view

        return create_mvp_pair()

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
