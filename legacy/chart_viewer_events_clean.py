"""
차트뷰어 관련 도메인 이벤트 정의

기존 DomainEvent를 상속하여 차트뷰어 전용 이벤트 타입들을 정의.
기존 시스템과 완전 격리되며, 호환성을 보장합니다.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from upbit_auto_trading.domain.events.base_domain_event import DomainEvent


@dataclass(frozen=True)
class ChartViewerEvent(DomainEvent):
    """차트뷰어 기본 이벤트 (기존 DomainEvent 상속)"""

    chart_id: str
    symbol: str
    data_type: str  # "candle", "orderbook", "indicator", "lifecycle"
    timeframe: str  # "1m"~"1M" (1개월 포함)
    window_active: bool = True  # 창 상태 기반 처리
    priority_level: int = 5  # 기존 시스템과 호환되는 우선순위 (5,8,10)

    @property
    def event_type(self) -> str:
        return "chart_viewer_event"

    @property
    def aggregate_id(self) -> str:
        return f"chart_viewer_{self.chart_id}"


@dataclass(frozen=True)
class CandleDataEvent(ChartViewerEvent):
    """캔들 데이터 업데이트 이벤트"""

    candle_data: Dict[str, Any]  # OHLCV 데이터
    is_realtime: bool = True
    data_source: str = "websocket"  # "websocket", "api", "hybrid"

    @property
    def event_type(self) -> str:
        return "chart_viewer_candle_data"

    def __post_init__(self):
        """메타데이터 자동 초기화 + 차트뷰어 전용 설정"""
        super().__post_init__()
        # data_type 자동 설정
        object.__setattr__(self, 'data_type', 'candle')


@dataclass(frozen=True)
class OrderbookDataEvent(ChartViewerEvent):
    """호가창 데이터 업데이트 이벤트"""

    orderbook_data: Dict[str, Any]  # 매수/매도 호가 데이터
    bid_levels: List[Dict[str, Any]]
    ask_levels: List[Dict[str, Any]]

    @property
    def event_type(self) -> str:
        return "chart_viewer_orderbook_data"

    def __post_init__(self):
        """메타데이터 자동 초기화 + 차트뷰어 전용 설정"""
        super().__post_init__()
        # data_type 자동 설정
        object.__setattr__(self, 'data_type', 'orderbook')
        # timeframe은 호가창에서 사용하지 않으므로 기본값 설정
        if not hasattr(self, 'timeframe') or not self.timeframe:
            object.__setattr__(self, 'timeframe', 'realtime')


@dataclass(frozen=True)
class TechnicalIndicatorEvent(ChartViewerEvent):
    """기술적 지표 업데이트 이벤트"""

    indicator_type: str  # "sma", "ema", "macd", "rsi", "bollinger", etc.
    indicator_data: Dict[str, Any]
    parameters: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "chart_viewer_technical_indicator"

    def __post_init__(self):
        """메타데이터 자동 초기화 + 차트뷰어 전용 설정"""
        super().__post_init__()
        # data_type 자동 설정
        object.__setattr__(self, 'data_type', 'indicator')


@dataclass(frozen=True)
class ChartLifecycleEvent(ChartViewerEvent):
    """차트뷰어 생명주기 이벤트 (창 상태 변경)"""

    lifecycle_type: str  # "activated", "deactivated", "minimized", "restored", "closed"
    resource_priority: int  # 5(활성), 8(비활성), 10(최소화)
    memory_limit_mb: int = 256  # 메모리 제한 (활성: 256MB, 비활성: 128MB, 최소화: 64MB)

    @property
    def event_type(self) -> str:
        return "chart_viewer_lifecycle"

    def __post_init__(self):
        """메타데이터 자동 초기화 + 차트뷰어 전용 설정"""
        super().__post_init__()
        # data_type 자동 설정
        object.__setattr__(self, 'data_type', 'lifecycle')
        # priority_level을 resource_priority와 동기화
        object.__setattr__(self, 'priority_level', self.resource_priority)
        # timeframe은 생명주기에서 사용하지 않으므로 기본값 설정
        if not hasattr(self, 'timeframe') or not self.timeframe:
            object.__setattr__(self, 'timeframe', 'N/A')


@dataclass(frozen=True)
class ChartSubscriptionEvent(ChartViewerEvent):
    """차트 데이터 구독/해제 이벤트"""

    subscription_type: str  # "subscribe", "unsubscribe", "update"
    subscription_id: str
    requested_count: int = 200  # 요청 데이터 개수

    @property
    def event_type(self) -> str:
        return "chart_viewer_subscription"

    def __post_init__(self):
        """메타데이터 자동 초기화 + 차트뷰어 전용 설정"""
        super().__post_init__()
        # data_type 자동 설정
        object.__setattr__(self, 'data_type', 'subscription')


# 차트뷰어 우선순위 상수 정의 (기존 시스템과 호환)
class ChartViewerPriority:
    """
    차트뷰어 우선순위 상수

    기존 시스템의 우선순위 범위(1-3: 매매 관련)와 격리하여
    차트뷰어 전용 우선순위(5,8,10)를 사용합니다.
    """

    # 기존 시스템 우선순위 (건드리지 않음)
    TRADING_CRITICAL = 1    # 매매 엔진 (기존 시스템)
    TRADING_HIGH = 2        # 리스크 관리 (기존 시스템)
    TRADING_NORMAL = 3      # 포지션 관리 (기존 시스템)

    # 차트뷰어 전용 우선순위 (기존 시스템과 격리)
    CHART_HIGH = 5          # 차트뷰어 활성화 상태
    CHART_BACKGROUND = 8    # 차트뷰어 비활성화 상태
    CHART_LOW = 10          # 차트뷰어 최소화 상태

    @classmethod
    def get_window_priority(cls, window_state: str) -> int:
        """창 상태에 따른 우선순위 반환 (기존 시스템 안전)"""
        priority_map = {
            'active': cls.CHART_HIGH,           # 5
            'background': cls.CHART_BACKGROUND,  # 8
            'minimized': cls.CHART_LOW,         # 10
            'deactivated': cls.CHART_BACKGROUND,  # 8
            'restored': cls.CHART_HIGH,         # 5
        }
        return priority_map.get(window_state, cls.CHART_LOW)

    @classmethod
    def is_chart_viewer_priority(cls, priority: int) -> bool:
        """차트뷰어 우선순위인지 확인"""
        return priority in [cls.CHART_HIGH, cls.CHART_BACKGROUND, cls.CHART_LOW]

    @classmethod
    def is_trading_priority(cls, priority: int) -> bool:
        """매매 시스템 우선순위인지 확인 (기존 시스템 보호)"""
        return priority in [cls.TRADING_CRITICAL, cls.TRADING_HIGH, cls.TRADING_NORMAL]


# 타임프레임 지원 정의 (1개월 포함)
class TimeframeSupport:
    """
    타임프레임 지원 정의

    1개월(1M) 타임프레임까지 지원하며, WebSocket 미지원시 API로 대체합니다.
    """

    SUPPORTED_TIMEFRAMES = {
        "1m": {"websocket": True, "api": True, "conversion": False},
        "3m": {"websocket": True, "api": True, "conversion": True},   # 1분에서 변환
        "5m": {"websocket": True, "api": True, "conversion": True},   # 1분에서 변환
        "15m": {"websocket": True, "api": True, "conversion": True},  # 1분에서 변환
        "30m": {"websocket": True, "api": True, "conversion": True},  # 1분에서 변환
        "1h": {"websocket": True, "api": True, "conversion": True},   # 1분에서 변환
        "4h": {"websocket": True, "api": True, "conversion": True},   # 1분에서 변환
        "1d": {"websocket": True, "api": True, "conversion": True},   # 1분에서 변환
        "1w": {"websocket": False, "api": True, "conversion": True},  # API 전용, 1일에서 변환
        "1M": {"websocket": False, "api": True, "conversion": True}   # API 전용, 1일에서 변환
    }

    @classmethod
    def get_data_source(cls, timeframe: str) -> str:
        """타임프레임별 최적 데이터 소스 결정"""
        if timeframe not in cls.SUPPORTED_TIMEFRAMES:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        tf_info = cls.SUPPORTED_TIMEFRAMES[timeframe]
        if tf_info["websocket"]:
            return "websocket"
        elif tf_info["api"]:
            return "api"
        else:
            raise ValueError(f"사용 가능한 데이터 소스가 없습니다: {timeframe}")

    @classmethod
    def is_conversion_required(cls, timeframe: str) -> bool:
        """타임프레임 변환이 필요한지 확인"""
        if timeframe not in cls.SUPPORTED_TIMEFRAMES:
            return False
        return cls.SUPPORTED_TIMEFRAMES[timeframe]["conversion"]

    @classmethod
    def is_timeframe_supported(cls, timeframe: str) -> bool:
        """타임프레임 지원 여부 확인"""
        return timeframe in cls.SUPPORTED_TIMEFRAMES

    @classmethod
    def get_all_supported_timeframes(cls) -> List[str]:
        """지원하는 모든 타임프레임 목록"""
        return list(cls.SUPPORTED_TIMEFRAMES.keys())
