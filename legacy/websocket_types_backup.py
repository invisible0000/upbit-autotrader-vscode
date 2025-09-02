"""
WebSocket v6.0 통합 타입 시스템
=============================

types.py + models.py 통합으로 v5 호환성과 v6 타입 안전성을 동시에 제공

핵심 기능:
- @dataclass 기반 타입 안전성
- v5 필드 호환성 유지
- 메시지 변환 (dict ↔ Event)
- SIMPLE 포맷 지원
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from decimal import Decimal


# ================================================================
# 기본 열거형 (Enums)
# ================================================================

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
    """업비트 웹소켓 지원 데이터 타입"""
    # Public 데이터
    TICKER = "ticker"
    TRADE = "trade"
    ORDERBOOK = "orderbook"

    # 캔들 데이터
    CANDLE_1S = "candle.1s"
    CANDLE_1M = "candle.1m"
    CANDLE_3M = "candle.3m"
    CANDLE_5M = "candle.5m"
    CANDLE_10M = "candle.10m"
    CANDLE_15M = "candle.15m"
    CANDLE_30M = "candle.30m"
    CANDLE_60M = "candle.60m"
    CANDLE_240M = "candle.240m"

    # Private 데이터
    MYORDER = "myOrder"
    MYASSET = "myAsset"

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

    def is_public(self) -> bool:
        return self in self.get_public_types()

    def is_private(self) -> bool:
        return self in self.get_private_types()


class GlobalManagerState(Enum):
    """전역 매니저 상태"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"


class BackpressureStrategy(Enum):
    """백프레셔 처리 전략"""
    DROP_OLDEST = "drop_oldest"
    COALESCE = "coalesce"
    THROTTLE = "throttle"
    BLOCK = "block"


class StreamType(str, Enum):
    """WebSocket 스트림 타입 (v5 호환성)"""
    SNAPSHOT = "SNAPSHOT"
    REALTIME = "REALTIME"


# ================================================================
# 이벤트 클래스
# ================================================================

@dataclass
class BaseWebSocketEvent:
    """WebSocket 이벤트 기본 클래스"""
    epoch: int = 0
    timestamp: float = field(default_factory=time.time)
    connection_type: WebSocketType = WebSocketType.PUBLIC


@dataclass
class TickerEvent(BaseWebSocketEvent):
    """현재가 이벤트"""
    symbol: Optional[str] = None
    trade_price: Optional[Decimal] = None
    change: Optional[str] = None
    change_price: Optional[Decimal] = None
    change_rate: Optional[Decimal] = None
    signed_change_price: Optional[Decimal] = None
    signed_change_rate: Optional[Decimal] = None
    trade_volume: Optional[Decimal] = None
    acc_trade_volume: Optional[Decimal] = None
    acc_trade_price: Optional[Decimal] = None
    trade_date: Optional[str] = None
    trade_time: Optional[str] = None
    trade_timestamp: Optional[int] = None
    ask_bid: Optional[str] = None
    acc_trade_volume_24h: Optional[Decimal] = None
    acc_trade_price_24h: Optional[Decimal] = None
    highest_52_week_price: Optional[Decimal] = None
    highest_52_week_date: Optional[str] = None
    lowest_52_week_price: Optional[Decimal] = None
    lowest_52_week_date: Optional[str] = None
    opening_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    prev_closing_price: Optional[Decimal] = None
    timestamp_ms: Optional[int] = None


@dataclass
class OrderbookUnit:
    """호가 단위"""
    ask_price: Decimal
    bid_price: Decimal
    ask_size: Decimal
    bid_size: Decimal


@dataclass
class OrderbookEvent(BaseWebSocketEvent):
    """호가 이벤트"""
    symbol: Optional[str] = None
    orderbook_units: List[OrderbookUnit] = field(default_factory=list)
    timestamp_ms: Optional[int] = None
    total_ask_size: Optional[Decimal] = None
    total_bid_size: Optional[Decimal] = None
    level: int = 15


@dataclass
class TradeEvent(BaseWebSocketEvent):
    """체결 이벤트"""
    symbol: Optional[str] = None
    trade_price: Optional[Decimal] = None
    trade_volume: Optional[Decimal] = None
    ask_bid: Optional[str] = None
    change: Optional[str] = None
    change_price: Optional[Decimal] = None
    trade_date: Optional[str] = None
    trade_time: Optional[str] = None
    trade_timestamp: Optional[int] = None
    timestamp_ms: Optional[int] = None
    sequential_id: Optional[int] = None
    prev_closing_price: Optional[Decimal] = None


@dataclass
class CandleEvent(BaseWebSocketEvent):
    """캔들 이벤트"""
    symbol: Optional[str] = None
    unit: Optional[str] = None
    opening_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    trade_price: Optional[Decimal] = None
    candle_acc_trade_price: Optional[Decimal] = None
    candle_acc_trade_volume: Optional[Decimal] = None
    change: Optional[str] = None
    change_price: Optional[Decimal] = None
    change_rate: Optional[Decimal] = None
    prev_closing_price: Optional[Decimal] = None
    timestamp_ms: Optional[int] = None


@dataclass
class MyOrderEvent(BaseWebSocketEvent):
    """내 주문 이벤트"""
    order_uuid: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    ord_type: Optional[str] = None
    price: Optional[Decimal] = None
    avg_price: Optional[Decimal] = None
    state: Optional[str] = None
    volume: Optional[Decimal] = None
    remaining_volume: Optional[Decimal] = None
    executed_volume: Optional[Decimal] = None
    trades_count: Optional[int] = None
    timestamp_ms: Optional[int] = None


@dataclass
class MyAssetEvent(BaseWebSocketEvent):
    """내 자산 이벤트"""
    currency: Optional[str] = None
    balance: Optional[Decimal] = None
    locked: Optional[Decimal] = None
    avg_buy_price: Optional[Decimal] = None
    avg_buy_price_modified: Optional[bool] = None
    unit_currency: Optional[str] = None
    timestamp_ms: Optional[int] = None


# ================================================================
# 구독 및 성능 관련 타입
# ================================================================

@dataclass
class SubscriptionSpec:
    """구독 규격"""
    data_type: DataType
    symbols: List[str] = field(default_factory=list)
    unit: Optional[str] = None  # 캔들 단위


@dataclass
class ComponentSubscription:
    """컴포넌트 구독 정보"""
    component_id: str
    subscriptions: List[SubscriptionSpec]
    callback: Optional[Callable[[BaseWebSocketEvent], None]] = None
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)


@dataclass
class PerformanceMetrics:
    """성능 지표"""
    messages_per_second: float = 0.0
    active_connections: int = 0
    total_components: int = 0
    last_updated: float = field(default_factory=time.time)
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


@dataclass
class HealthStatus:
    """상태 정보"""
    status: str = "unknown"
    uptime_seconds: float = 0.0
    total_messages_processed: int = 0
    connection_errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None


@dataclass
class BackpressureConfig:
    """백프레셔 설정"""
    strategy: BackpressureStrategy = BackpressureStrategy.DROP_OLDEST
    max_queue_size: int = 1000
    warning_threshold: int = 800
    coalesce_window_ms: int = 100
    throttle_interval_ms: int = 50


@dataclass
class ConnectionMetrics:
    """연결 메트릭"""
    connection_type: WebSocketType
    state: ConnectionState = ConnectionState.DISCONNECTED
    connected_at: Optional[float] = None
    last_message_at: Optional[float] = None
    total_messages: int = 0
    reconnect_count: int = 0
    error_count: int = 0


# ================================================================
# v5 호환성 필드 문서
# ================================================================

TICKER_FIELDS = {
    'type': 'ticker',
    'code': '마켓 코드 (ex. KRW-BTC)',
    'opening_price': '시가',
    'high_price': '고가',
    'low_price': '저가',
    'trade_price': '현재가',
    'prev_closing_price': '전일 종가',
    'change': '전일 대비 (RISE/FALL/EVEN)',
    'change_price': '변화 가격',
    'change_rate': '변화율',
    'signed_change_price': '부호 포함 변화 가격',
    'signed_change_rate': '부호 포함 변화율',
    'trade_volume': '체결량',
    'acc_trade_volume': '누적 체결량',
    'acc_trade_price': '누적 체결 대금',
    'trade_date': '체결 일자 (UTC)',
    'trade_time': '체결 시각 (UTC)',
    'trade_timestamp': '체결 타임스탬프',
    'ask_bid': '매수/매도 구분 (ASK/BID)',
    'acc_trade_volume_24h': '24시간 누적 체결량',
    'acc_trade_price_24h': '24시간 누적 체결 대금',
    'highest_52_week_price': '52주 최고가',
    'highest_52_week_date': '52주 최고가 달성일',
    'lowest_52_week_price': '52주 최저가',
    'lowest_52_week_date': '52주 최저가 달성일',
    'timestamp': '타임스탬프'
}

TRADE_FIELDS = {
    'type': 'trade',
    'code': '마켓 코드',
    'trade_price': '체결 가격',
    'trade_volume': '체결량',
    'ask_bid': '매수/매도 구분',
    'change': '전일 대비',
    'change_price': '변화 가격',
    'trade_date': '체결 일자',
    'trade_time': '체결 시각',
    'trade_timestamp': '체결 타임스탬프',
    'timestamp': '타임스탬프',
    'sequential_id': '체결 번호',
    'prev_closing_price': '전일 종가'
}

ORDERBOOK_FIELDS = {
    'type': 'orderbook',
    'code': '마켓 코드',
    'total_ask_size': '호가 매도 총 잔량',
    'total_bid_size': '호가 매수 총 잔량',
    'orderbook_units': '호가 리스트',
    'timestamp': '타임스탬프'
}

CANDLE_FIELDS = {
    'type': 'candle',
    'code': '마켓 코드',
    'opening_price': '시가',
    'high_price': '고가',
    'low_price': '저가',
    'trade_price': '종가',
    'candle_acc_trade_price': '누적 체결 대금',
    'candle_acc_trade_volume': '누적 체결량',
    'unit': '캔들 단위',
    'change': '전일 대비',
    'change_price': '변화 가격',
    'change_rate': '변화율',
    'prev_closing_price': '전일 종가',
    'timestamp': '타임스탬프'
}

MY_ORDER_FIELDS = {
    'type': 'myOrder',
    'order_uuid': '주문 고유 아이디',
    'code': '마켓 코드',
    'side': '주문 종류 (bid/ask)',
    'ord_type': '주문 방식 (limit/price/market)',
    'price': '주문 가격',
    'avg_price': '평균 체결 가격',
    'state': '주문 상태',
    'volume': '주문량',
    'remaining_volume': '미체결량',
    'executed_volume': '체결량',
    'trades_count': '체결 건수',
    'timestamp': '타임스탬프'
}

MY_ASSET_FIELDS = {
    'type': 'myAsset',
    'currency': '화폐를 의미하는 영문 대문자 코드',
    'balance': '주문가능 금액/수량',
    'locked': '주문 중 묶여있는 금액/수량',
    'avg_buy_price': '매수평균가',
    'avg_buy_price_modified': '매수평균가 수정 여부',
    'unit_currency': '평가 화폐 단위',
    'timestamp': '타임스탬프'
}


# ================================================================
# 유틸리티 함수
# ================================================================

def create_ticker_event(data: Dict[str, Any], epoch: int = 0,
                       connection_type: WebSocketType = WebSocketType.PUBLIC) -> TickerEvent:
    """Dict에서 TickerEvent 생성"""
    def safe_decimal(value, default=None):
        if value is None:
            return default
        try:
            return Decimal(str(value))
        except:
            return default

    return TickerEvent(
        epoch=epoch,
        timestamp=time.time(),
        connection_type=connection_type,
        symbol=data.get('code'),
        trade_price=safe_decimal(data.get('trade_price')),
        change=data.get('change'),
        change_price=safe_decimal(data.get('change_price')),
        change_rate=safe_decimal(data.get('change_rate')),
        signed_change_price=safe_decimal(data.get('signed_change_price')),
        signed_change_rate=safe_decimal(data.get('signed_change_rate')),
        trade_volume=safe_decimal(data.get('trade_volume')),
        acc_trade_volume=safe_decimal(data.get('acc_trade_volume')),
        acc_trade_price=safe_decimal(data.get('acc_trade_price')),
        trade_date=data.get('trade_date'),
        trade_time=data.get('trade_time'),
        trade_timestamp=data.get('trade_timestamp'),
        ask_bid=data.get('ask_bid'),
        acc_trade_volume_24h=safe_decimal(data.get('acc_trade_volume_24h')),
        acc_trade_price_24h=safe_decimal(data.get('acc_trade_price_24h')),
        highest_52_week_price=safe_decimal(data.get('highest_52_week_price')),
        highest_52_week_date=data.get('highest_52_week_date'),
        lowest_52_week_price=safe_decimal(data.get('lowest_52_week_price')),
        lowest_52_week_date=data.get('lowest_52_week_date'),
        opening_price=safe_decimal(data.get('opening_price')),
        high_price=safe_decimal(data.get('high_price')),
        low_price=safe_decimal(data.get('low_price')),
        prev_closing_price=safe_decimal(data.get('prev_closing_price')),
        timestamp_ms=data.get('timestamp')
    )


def create_orderbook_event(data: Dict[str, Any], epoch: int = 0,
                          connection_type: WebSocketType = WebSocketType.PUBLIC) -> OrderbookEvent:
    """Dict에서 OrderbookEvent 생성"""
    def safe_decimal(value, default=Decimal('0')):
        if value is None:
            return default
        try:
            return Decimal(str(value))
        except:
            return default

    units = []
    orderbook_units = data.get('orderbook_units', [])
    for unit_data in orderbook_units:
        units.append(OrderbookUnit(
            ask_price=safe_decimal(unit_data.get('ask_price')),
            bid_price=safe_decimal(unit_data.get('bid_price')),
            ask_size=safe_decimal(unit_data.get('ask_size')),
            bid_size=safe_decimal(unit_data.get('bid_size'))
        ))

    return OrderbookEvent(
        epoch=epoch,
        timestamp=time.time(),
        connection_type=connection_type,
        symbol=data.get('code'),
        orderbook_units=units,
        timestamp_ms=data.get('timestamp'),
        total_ask_size=safe_decimal(data.get('total_ask_size')),
        total_bid_size=safe_decimal(data.get('total_bid_size')),
        level=len(units)
    )


def get_data_type_from_message(message: Dict[str, Any]) -> Optional[DataType]:
    """메시지에서 데이터 타입 추론"""
    msg_type = message.get('type', '').lower()

    if msg_type == 'ticker':
        return DataType.TICKER
    elif msg_type == 'trade':
        return DataType.TRADE
    elif msg_type == 'orderbook':
        return DataType.ORDERBOOK
    elif 'candle' in msg_type:
        # candle.1m, candle.5m 등
        return DataType(msg_type) if msg_type in [dt.value for dt in DataType.get_candle_types()] else None
    elif msg_type == 'myorder':
        return DataType.MYORDER
    elif msg_type == 'myasset':
        return DataType.MYASSET

    return None


def infer_message_type(data: Dict[str, Any]) -> Optional[str]:
    """메시지 타입 추론 (v5 호환성)"""
    if 'type' in data:
        return data['type'].lower()

    # 필드 기반 추론
    if 'trade_price' in data and 'change' in data:
        return 'ticker'
    elif 'orderbook_units' in data:
        return 'orderbook'
    elif 'trade_price' in data and 'ask_bid' in data:
        return 'trade'
    elif 'opening_price' in data and 'high_price' in data:
        return 'candle'
    elif 'order_uuid' in data:
        return 'myorder'
    elif 'currency' in data and 'balance' in data:
        return 'myasset'

    return None


def convert_dict_to_event(message_data: Dict[str, Any], epoch: int = 0,
                         connection_type: Optional[WebSocketType] = None) -> Optional[BaseWebSocketEvent]:
    """Dict 메시지를 이벤트 객체로 변환"""
    if not connection_type:
        connection_type = WebSocketType.PUBLIC

    msg_type = infer_message_type(message_data)

    try:
        if msg_type == 'ticker':
            return create_ticker_event(message_data, epoch, connection_type)
        elif msg_type == 'orderbook':
            return create_orderbook_event(message_data, epoch, connection_type)
        elif msg_type == 'trade':
            return TradeEvent(
                epoch=epoch,
                timestamp=time.time(),
                connection_type=connection_type,
                symbol=message_data.get('code'),
                trade_price=Decimal(str(message_data.get('trade_price', 0))),
                trade_volume=Decimal(str(message_data.get('trade_volume', 0))),
                ask_bid=message_data.get('ask_bid'),
                change=message_data.get('change'),
                change_price=Decimal(str(message_data.get('change_price', 0))),
                trade_date=message_data.get('trade_date'),
                trade_time=message_data.get('trade_time'),
                trade_timestamp=message_data.get('trade_timestamp'),
                timestamp_ms=message_data.get('timestamp'),
                sequential_id=message_data.get('sequential_id'),
                prev_closing_price=Decimal(str(message_data.get('prev_closing_price', 0)))
            )
        # 추가 타입들은 필요시 구현
        else:
            return None
    except Exception:
        return None


def validate_symbols(symbols: List[str]) -> List[str]:
    """심볼 목록 검증"""
    validated = []
    for symbol in symbols:
        if isinstance(symbol, str) and '-' in symbol:
            validated.append(symbol.upper())
    return validated


def normalize_symbols(symbols: List[str]) -> List[str]:
    """심볼 목록 정규화"""
    return [symbol.upper().strip() for symbol in symbols if symbol and isinstance(symbol, str)]


# ================================================================
# 패키지 정보
# ================================================================

__all__ = [
    # 열거형
    'ConnectionState', 'SubscriptionState', 'WebSocketType', 'DataType',
    'GlobalManagerState', 'BackpressureStrategy', 'StreamType',

    # 이벤트 클래스
    'BaseWebSocketEvent', 'TickerEvent', 'OrderbookEvent', 'OrderbookUnit',
    'TradeEvent', 'CandleEvent', 'MyOrderEvent', 'MyAssetEvent',

    # 구독 및 성능
    'SubscriptionSpec', 'ComponentSubscription', 'PerformanceMetrics',
    'HealthStatus', 'BackpressureConfig', 'ConnectionMetrics',

    # 필드 문서
    'TICKER_FIELDS', 'TRADE_FIELDS', 'ORDERBOOK_FIELDS', 'CANDLE_FIELDS',
    'MY_ORDER_FIELDS', 'MY_ASSET_FIELDS',

    # 유틸리티 함수
    'create_ticker_event', 'create_orderbook_event', 'get_data_type_from_message',
    'infer_message_type', 'convert_dict_to_event', 'validate_symbols', 'normalize_symbols'
]
