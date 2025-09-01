"""
WebSocket v6.0 타입 정의
=======================

이벤트 시스템, 구독 규격, 성능 지표 등 핵심 타입 정의
@dataclass 기반 타입 안전성 강화

핵심 타입:
- WebSocket 이벤트 (TickerEvent, OrderbookEvent, CandleEvent)
- 구독 규격 (SubscriptionSpec, ComponentSubscription)
- 성능 지표 (PerformanceMetrics)
- 상태 관리 (ConnectionState, SubscriptionState)
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from decimal import Decimal


class ConnectionState(Enum):
    """WebSocket 연결 상태"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SUBSCRIBING = "subscribing"
    ACTIVE = "active"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class SubscriptionState(Enum):
    """구독 상태"""
    IDLE = "idle"
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class WebSocketType(Enum):
    """WebSocket 연결 타입"""
    PUBLIC = "public"
    PRIVATE = "private"


class DataType(str, Enum):
    """업비트 웹소켓 지원 데이터 타입 - 공식 API 기준"""
    # Public 데이터 타입
    TICKER = "ticker"           # 현재가
    TRADE = "trade"             # 체결
    ORDERBOOK = "orderbook"     # 호가

    # 캔들 데이터 (업비트 공식 형식)
    CANDLE_1S = "candle.1s"     # 초봉
    CANDLE_1M = "candle.1m"     # 1분봉
    CANDLE_3M = "candle.3m"     # 3분봉
    CANDLE_5M = "candle.5m"     # 5분봉
    CANDLE_10M = "candle.10m"   # 10분봉
    CANDLE_15M = "candle.15m"   # 15분봉
    CANDLE_30M = "candle.30m"   # 30분봉
    CANDLE_60M = "candle.60m"   # 60분봉 (1시간)
    CANDLE_240M = "candle.240m"  # 240분봉 (4시간)

    # Private 데이터 타입
    MYORDER = "myOrder"         # 내 주문 및 체결
    MYASSET = "myAsset"         # 내 자산

    @classmethod
    def get_public_types(cls) -> List['DataType']:
        """Public 연결용 데이터 타입들"""
        return [
            cls.TICKER, cls.TRADE, cls.ORDERBOOK,
            cls.CANDLE_1S, cls.CANDLE_1M, cls.CANDLE_3M, cls.CANDLE_5M,
            cls.CANDLE_10M, cls.CANDLE_15M, cls.CANDLE_30M, cls.CANDLE_60M, cls.CANDLE_240M
        ]

    @classmethod
    def get_private_types(cls) -> List['DataType']:
        """Private 연결용 데이터 타입들"""
        return [cls.MYORDER, cls.MYASSET]

    @classmethod
    def get_candle_types(cls) -> List['DataType']:
        """캔들 데이터 타입들"""
        return [
            cls.CANDLE_1S, cls.CANDLE_1M, cls.CANDLE_3M, cls.CANDLE_5M,
            cls.CANDLE_10M, cls.CANDLE_15M, cls.CANDLE_30M, cls.CANDLE_60M, cls.CANDLE_240M
        ]

    def is_public(self) -> bool:
        """Public 연결용 데이터인지 확인"""
        return self in self.get_public_types()

    def is_private(self) -> bool:
        """Private 연결용 데이터인지 확인"""
        return self in self.get_private_types()

    def is_candle(self) -> bool:
        """캔들 데이터인지 확인"""
        return self in self.get_candle_types()


class GlobalManagerState(Enum):
    """글로벌 매니저 상태"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    ACTIVE = "active"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    ERROR = "error"


# =============================================================================
# 이벤트 시스템 (타입 안전성)
# =============================================================================

@dataclass
class BaseWebSocketEvent:
    """WebSocket 이벤트 기본 클래스"""
    epoch: int                    # 재연결 구분용 세대 번호
    timestamp: float             # 수신 시각 (monotonic time)
    connection_type: WebSocketType
    symbol: Optional[str] = None

    @property
    def data_type(self) -> DataType:
        """이벤트 데이터 타입 반환"""
        # 클래스 이름에서 DataType 추출
        class_name = self.__class__.__name__
        if 'Ticker' in class_name:
            return DataType.TICKER
        elif 'Orderbook' in class_name:
            return DataType.ORDERBOOK
        elif 'Trade' in class_name:
            return DataType.TRADE
        elif 'Candle' in class_name:
            # 캔들은 기본적으로 1분봉으로 설정 (구체적인 타입은 별도 처리 필요)
            return DataType.CANDLE_1M
        elif 'MyOrder' in class_name:
            return DataType.MYORDER
        elif 'MyAsset' in class_name:
            return DataType.MYASSET
        else:
            return DataType.TICKER  # 기본값


@dataclass
class TickerEvent(BaseWebSocketEvent):
    """현재가 이벤트 - models.py 완전 호환"""
    # 기본 가격 정보
    trade_price: Decimal = field(default_factory=lambda: Decimal('0'))         # 체결가
    trade_volume: Decimal = field(default_factory=lambda: Decimal('0'))        # 체결량
    acc_trade_price: Decimal = field(default_factory=lambda: Decimal('0'))     # 누적 거래 대금
    acc_trade_volume: Decimal = field(default_factory=lambda: Decimal('0'))    # 누적 거래량
    high_price: Decimal = field(default_factory=lambda: Decimal('0'))          # 고가
    low_price: Decimal = field(default_factory=lambda: Decimal('0'))           # 저가
    prev_closing_price: Decimal = field(default_factory=lambda: Decimal('0'))  # 전일 종가

    # 추가 가격 정보 (models.py 호환)
    opening_price: Decimal = field(default_factory=lambda: Decimal('0'))       # 시가

    # 변화량 정보
    change: str = 'EVEN'          # 변화 (RISE, EVEN, FALL)
    change_price: Decimal = field(default_factory=lambda: Decimal('0'))        # 변화 대금
    change_rate: Decimal = field(default_factory=lambda: Decimal('0'))         # 변화율
    signed_change_price: Decimal = field(default_factory=lambda: Decimal('0'))  # 부호 포함 변화금액
    signed_change_rate: Decimal = field(default_factory=lambda: Decimal('0'))   # 부호 포함 변화율

    # 24시간 통계
    acc_trade_price_24h: Decimal = field(default_factory=lambda: Decimal('0'))  # 24시간 누적 거래대금
    acc_trade_volume_24h: Decimal = field(default_factory=lambda: Decimal('0'))  # 24시간 누적 거래량

    # 52주 통계
    highest_52_week_price: Decimal = field(default_factory=lambda: Decimal('0'))  # 52주 최고가
    highest_52_week_date: Optional[str] = None                                    # 52주 최고가 달성일
    lowest_52_week_price: Decimal = field(default_factory=lambda: Decimal('0'))   # 52주 최저가
    lowest_52_week_date: Optional[str] = None                                     # 52주 최저가 달성일    # 시장 상태
    market_state: str = 'ACTIVE'  # 시장 상태 (ACTIVE, PREVIEW, DELISTED)
    is_trading_suspended: Optional[bool] = None    # 거래 중단 여부
    delisting_date: Optional[str] = None           # 상장폐지일
    market_warning: str = 'NONE'                   # 시장 경고 (NONE, CAUTION)

    # 체결 정보
    ask_bid: str = ''             # 매수/매도 구분
    trade_timestamp: int = 0      # 체결 시각 (업비트 timestamp)

    # 시간 정보
    trade_date: Optional[str] = None        # 최근거래일자 (UTC)
    trade_time: Optional[str] = None        # 최근거래시각 (UTC)
    trade_date_kst: Optional[str] = None    # 최근거래일자 (KST)
    trade_time_kst: Optional[str] = None    # 최근거래시각 (KST)


@dataclass
class OrderbookUnit:
    """호가 단위"""
    ask_price: Decimal = field(default_factory=lambda: Decimal('0'))          # 매도호가
    bid_price: Decimal = field(default_factory=lambda: Decimal('0'))          # 매수호가
    ask_size: Decimal = field(default_factory=lambda: Decimal('0'))           # 매도잔량
    bid_size: Decimal = field(default_factory=lambda: Decimal('0'))           # 매수잔량


@dataclass
class OrderbookEvent(BaseWebSocketEvent):
    """호가 이벤트"""
    orderbook_units: List[OrderbookUnit] = field(default_factory=list)  # 호가 리스트 (15단계)
    total_ask_size: Decimal = field(default_factory=lambda: Decimal('0'))      # 총 매도량
    total_bid_size: Decimal = field(default_factory=lambda: Decimal('0'))      # 총 매수량
    orderbook_timestamp: int = 0     # 호가 시각 (업비트 timestamp)


@dataclass
class TradeEvent(BaseWebSocketEvent):
    """체결 이벤트"""
    trade_price: Decimal = field(default_factory=lambda: Decimal('0'))         # 체결가
    trade_volume: Decimal = field(default_factory=lambda: Decimal('0'))        # 체결량
    ask_bid: str = ''                 # 매수/매도 구분
    trade_timestamp: int = 0         # 체결 시각 (업비트 timestamp)
    sequential_id: int = 0           # 체결 번호
    prev_closing_price: Decimal = field(default_factory=lambda: Decimal('0'))  # 전일 종가


@dataclass
class CandleEvent(BaseWebSocketEvent):
    """캔들 이벤트"""
    opening_price: Decimal = field(default_factory=lambda: Decimal('0'))       # 시가
    high_price: Decimal = field(default_factory=lambda: Decimal('0'))          # 고가
    low_price: Decimal = field(default_factory=lambda: Decimal('0'))           # 저가
    trade_price: Decimal = field(default_factory=lambda: Decimal('0'))         # 종가
    candle_acc_trade_price: Decimal = field(default_factory=lambda: Decimal('0'))  # 누적 거래 대금
    candle_acc_trade_volume: Decimal = field(default_factory=lambda: Decimal('0'))  # 누적 거래량
    unit: int = 1                    # 시간 단위 (0:초봉, 1,3,5,15,30,60,240:분봉)
    candle_timestamp: int = 0        # 캔들 시각 (업비트 timestamp)


@dataclass
class MyOrderEvent(BaseWebSocketEvent):
    """내 주문 이벤트 (Private)"""
    uuid: str = ''                    # 주문 고유 아이디
    order_type: str = ''              # 주문 타입 (limit, price, market)
    ord_type: str = ''                # 주문 방식 (bid, ask)
    state: str = ''                   # 주문 상태 (wait, done, cancel)
    market: str = ''                  # 마켓 ID
    created_at: str = ''              # 주문 생성 시간
    price: Optional[Decimal] = None     # 주문 당일 단가
    avg_price: Optional[Decimal] = None     # 체결 가격 평균값
    volume: Optional[Decimal] = None    # 사용자가 입력한 주문 양
    remaining_volume: Optional[Decimal] = None  # 미체결 수량
    reserved_fee: Optional[Decimal] = None      # 수수료로 예약된 비용
    remaining_fee: Optional[Decimal] = None     # 남은 수수료
    paid_fee: Optional[Decimal] = None          # 사용된 수수료
    locked: Optional[Decimal] = None            # 거래에 사용중인 비용 또는 수량
    executed_volume: Optional[Decimal] = None   # 체결된 양
    trades_count: Optional[int] = None          # 해당 주문에 걸린 체결 수


@dataclass
class MyAssetEvent(BaseWebSocketEvent):
    """내 자산 이벤트 (Private)"""
    currency: str = ''                # 화폐를 의미하는 영문 대문자 코드
    balance: Decimal = field(default_factory=lambda: Decimal('0'))             # 주문가능 금액/수량
    locked: Decimal = field(default_factory=lambda: Decimal('0'))              # 주문 중 묶여있는 금액/수량
    avg_buy_price: Optional[Decimal] = None     # 매수평균가
    avg_buy_price_modified: Optional[bool] = None  # 매수평균가 수정 여부
    unit_currency: Optional[str] = None         # 평단가 기준 화폐


# =============================================================================
# 구독 규격
# =============================================================================

@dataclass
class SubscriptionSpec:
    """구독 규격"""
    data_type: DataType
    symbols: List[str] = field(default_factory=list)
    callback: Optional[Callable[[BaseWebSocketEvent], None]] = None
    error_handler: Optional[Callable[[Exception], None]] = None

    # Private 전용
    markets: Optional[List[str]] = None  # Private에서는 markets 사용

    def __post_init__(self):
        """검증 로직"""
        if self.data_type in [DataType.MYORDER, DataType.MYASSET]:
            # Private 데이터는 symbols 대신 markets 사용
            if not self.markets and not self.symbols:
                raise ValueError("Private 데이터는 markets 또는 symbols 필요")
        else:
            # Public 데이터는 symbols 필수
            if not self.symbols:
                raise ValueError("Public 데이터는 symbols 필수")


@dataclass
class ComponentSubscription:
    """컴포넌트별 구독 정보 (상태 관리 전용)"""
    component_id: str            # 컴포넌트 식별자
    subscription_specs: List[SubscriptionSpec]
    created_at: float = field(default_factory=time.monotonic)
    last_data_received: Optional[float] = None
    error_count: int = 0
    is_active: bool = True

    @property
    def subscriptions(self) -> List[SubscriptionSpec]:
        """호환성을 위한 별칭"""
        return self.subscription_specs


# =============================================================================
# 성능 지표
# =============================================================================

@dataclass
class PerformanceMetrics:
    """성능 지표"""
    # 연결 관련
    connection_count: int = 0
    active_connections: int = 0
    uptime_seconds: float = 0.0
    reconnect_count: int = 0

    # 메시지 관련
    messages_received_total: int = 0
    messages_per_second: float = 0.0
    data_routing_latency_ms: float = 0.0

    # 구독 관련
    active_subscriptions: int = 0
    active_components: int = 0
    total_components: int = 0
    subscription_conflicts: int = 0

    # 타임스탬프
    last_updated: float = 0.0

    # 에러 관련
    callback_errors: int = 0
    connection_errors: int = 0
    rate_limit_hits: int = 0

    # 메모리 관련
    queue_depth_public: int = 0
    queue_depth_private: int = 0
    dropped_messages: int = 0

    # 백프레셔 관련
    backpressure_events: int = 0
    coalesced_messages: int = 0
    throttled_callbacks: int = 0


@dataclass
class HealthStatus:
    """시스템 건강 상태"""
    status: str  # healthy, degraded, critical
    public_connection: ConnectionState
    private_connection: ConnectionState
    active_subscriptions: Dict[str, int]  # data_type -> count
    performance: PerformanceMetrics
    alerts: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.monotonic)


# =============================================================================
# 백프레셔 처리
# =============================================================================

class BackpressureStrategy(Enum):
    """백프레셔 처리 전략"""
    DROP_OLDEST = "drop_oldest"           # 오래된 데이터 삭제
    COALESCE_BY_SYMBOL = "coalesce_by_symbol"  # 심볼별 최신 데이터만 유지
    THROTTLE = "throttle"                 # 콜백 호출 빈도 제한
    BLOCK = "block"                       # 대기 (비권장)


@dataclass
class BackpressureConfig:
    """백프레셔 설정"""
    strategy: BackpressureStrategy = BackpressureStrategy.DROP_OLDEST
    max_queue_size: int = 1000           # 큐 최대 크기
    warning_threshold: float = 0.8       # 경고 임계값 (80%)
    coalesce_window_ms: int = 100        # 통합 윈도우 (밀리초)
    throttle_interval_ms: int = 50       # 스로틀 간격 (밀리초)


# =============================================================================
# 에러 처리 (exceptions.py에서 import)
# =============================================================================

# 예외 클래스들은 exceptions.py에 정의되어 있음
# 필요시 from .exceptions import WebSocketException, ConnectionError 등으로 사용


# =============================================================================
# 설정 (config.py에서 import)
# =============================================================================

# WebSocketConfig는 config.py에서 정의됨 - 중복 제거
# from .config import WebSocketConfig, ConnectionConfig, etc. 으로 사용


# =============================================================================
# 연결 및 성능 메트릭스
# =============================================================================

@dataclass(frozen=True)
class ConnectionMetrics:
    """WebSocket 연결 성능 지표"""
    connected_clients: int = 0
    total_subscriptions: int = 0
    messages_per_second: float = 0.0
    average_latency_ms: float = 0.0
    error_rate: float = 0.0
    uptime_seconds: float = 0.0


@dataclass(frozen=True)
class DataStreamEvent:
    """데이터 스트림 이벤트"""
    data_type: DataType
    symbol: str
    data: Dict[str, Any]
    source_connection: str
    sequence_id: int
    timestamp: float = field(default_factory=time.monotonic)


# =============================================================================
# 유틸리티 함수
# =============================================================================

def create_ticker_event(data: Dict[str, Any], epoch: int, connection_type: WebSocketType) -> TickerEvent:
    """업비트 데이터에서 TickerEvent 생성 - models.py 완전 호환"""
    return TickerEvent(
        epoch=epoch,
        timestamp=time.monotonic(),
        connection_type=connection_type,
        symbol=data.get('code'),
        # 기본 가격 정보
        trade_price=Decimal(str(data.get('trade_price', 0))),
        trade_volume=Decimal(str(data.get('trade_volume', 0))),
        acc_trade_price=Decimal(str(data.get('acc_trade_price', 0))),
        acc_trade_volume=Decimal(str(data.get('acc_trade_volume', 0))),
        high_price=Decimal(str(data.get('high_price', 0))),
        low_price=Decimal(str(data.get('low_price', 0))),
        prev_closing_price=Decimal(str(data.get('prev_closing_price', 0))),
        opening_price=Decimal(str(data.get('opening_price', 0))),
        # 변화량 정보
        change=data.get('change', 'EVEN'),
        change_price=Decimal(str(data.get('change_price', 0))),
        change_rate=Decimal(str(data.get('change_rate', 0))),
        signed_change_price=Decimal(str(data.get('signed_change_price', 0))),
        signed_change_rate=Decimal(str(data.get('signed_change_rate', 0))),
        # 24시간 통계
        acc_trade_price_24h=Decimal(str(data.get('acc_trade_price_24h', 0))),
        acc_trade_volume_24h=Decimal(str(data.get('acc_trade_volume_24h', 0))),
        # 52주 통계
        highest_52_week_price=Decimal(str(data.get('highest_52_week_price', 0))),
        highest_52_week_date=data.get('highest_52_week_date'),
        lowest_52_week_price=Decimal(str(data.get('lowest_52_week_price', 0))),
        lowest_52_week_date=data.get('lowest_52_week_date'),
        # 시장 상태
        market_state=data.get('market_state', 'ACTIVE'),
        is_trading_suspended=data.get('is_trading_suspended'),
        delisting_date=data.get('delisting_date'),
        market_warning=data.get('market_warning', 'NONE'),
        # 체결 정보
        ask_bid=data.get('ask_bid', ''),
        trade_timestamp=data.get('trade_timestamp', 0),
        # 시간 정보
        trade_date=data.get('trade_date'),
        trade_time=data.get('trade_time'),
        trade_date_kst=data.get('trade_date_kst'),
        trade_time_kst=data.get('trade_time_kst')
    )


def create_orderbook_event(data: Dict[str, Any], epoch: int, connection_type: WebSocketType) -> OrderbookEvent:
    """업비트 데이터에서 OrderbookEvent 생성"""
    orderbook_units = []
    for unit_data in data.get('orderbook_units', []):
        unit = OrderbookUnit(
            ask_price=Decimal(str(unit_data.get('ask_price', 0))),
            bid_price=Decimal(str(unit_data.get('bid_price', 0))),
            ask_size=Decimal(str(unit_data.get('ask_size', 0))),
            bid_size=Decimal(str(unit_data.get('bid_size', 0)))
        )
        orderbook_units.append(unit)

    return OrderbookEvent(
        epoch=epoch,
        timestamp=time.monotonic(),
        connection_type=connection_type,
        symbol=data.get('code'),
        orderbook_units=orderbook_units,
        total_ask_size=Decimal(str(data.get('total_ask_size', 0))),
        total_bid_size=Decimal(str(data.get('total_bid_size', 0))),
        orderbook_timestamp=data.get('timestamp', 0)
    )


def get_data_type_from_message(data: Dict[str, Any]) -> Optional[DataType]:
    """업비트 메시지에서 DataType 추론"""
    if 'type' in data:
        type_str = data['type']
        if type_str == 'ticker':
            return DataType.TICKER
        elif type_str == 'orderbook':
            return DataType.ORDERBOOK
        elif type_str == 'trade':
            return DataType.TRADE
        elif type_str.startswith('candle'):
            # 구체적인 캔들 타입 반환
            if type_str == 'candle.1s':
                return DataType.CANDLE_1S
            elif type_str == 'candle.1m':
                return DataType.CANDLE_1M
            elif type_str == 'candle.3m':
                return DataType.CANDLE_3M
            elif type_str == 'candle.5m':
                return DataType.CANDLE_5M
            elif type_str == 'candle.10m':
                return DataType.CANDLE_10M
            elif type_str == 'candle.15m':
                return DataType.CANDLE_15M
            elif type_str == 'candle.30m':
                return DataType.CANDLE_30M
            elif type_str == 'candle.60m':
                return DataType.CANDLE_60M
            elif type_str == 'candle.240m':
                return DataType.CANDLE_240M
            else:
                return DataType.CANDLE_1M  # 기본값
        elif type_str == 'myOrder':
            return DataType.MYORDER
        elif type_str == 'myAsset':
            return DataType.MYASSET

    # 메시지 구조로 추론
    if 'trade_price' in data and 'trade_volume' in data:
        if 'orderbook_units' in data:
            return None  # 애매한 경우
        return DataType.TICKER
    elif 'orderbook_units' in data:
        return DataType.ORDERBOOK
    elif 'uuid' in data and 'state' in data:
        return DataType.MYORDER
    elif 'currency' in data and 'balance' in data:
        return DataType.MYASSET

    return None


def validate_symbols(symbols: List[str]) -> bool:
    """심볼 형식 검증"""
    if not symbols:
        return False

    for symbol in symbols:
        if not isinstance(symbol, str):
            return False
        if not symbol or len(symbol) < 3:
            return False
        # 업비트 형식: KRW-BTC, BTC-ETH 등
        if '-' not in symbol:
            return False

    return True


def normalize_symbols(symbols: List[str]) -> List[str]:
    """심볼 정규화 (대문자 변환)"""
    return [symbol.upper().strip() for symbol in symbols if symbol and symbol.strip()]
