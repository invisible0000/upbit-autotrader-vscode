"""
Presentation Layer Presenters - MVP 패턴

모든 Presenter 클래스들을 관리하는 패키지입니다.
각 Presenter는 View와 Application Service 사이의 중재자 역할을 수행합니다.
"""

from .strategy_maker_presenter import StrategyMakerPresenter
from .trigger_builder_presenter import TriggerBuilderPresenter, BacktestPresenter
from .settings_presenter import SettingsPresenter

# TODO: LiveTradingPresenter는 아직 구현되지 않음
# from .live_trading_presenter import LiveTradingPresenter

__all__ = [
    'StrategyMakerPresenter',
    'TriggerBuilderPresenter',
    'BacktestPresenter',
    'SettingsPresenter',
    # 'LiveTradingPresenter'  # TODO: 구현 후 활성화
]
