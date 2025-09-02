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
from decimal import Decimal, InvalidOperation


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

    @classmethod
    def get_candle_types(cls) -> List['DataType']:
        """캔들 데이터 타입들"""
        return [
            cls.CANDLE_1S, cls.CANDLE_1M, cls.CANDLE_3M, cls.CANDLE_5M,
            cls.CANDLE_10M, cls.CANDLE_15M, cls.CANDLE_30M, cls.CANDLE_60M, cls.CANDLE_240M
        ]

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
    """현재가 이벤트 (업비트 공식 문서 완전 반영)"""
    # 기본 정보
    symbol: Optional[str] = None  # code 필드에서 변환

    # 가격 정보
    opening_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    trade_price: Optional[Decimal] = None
    prev_closing_price: Optional[Decimal] = None

    # 변화 정보
    change: Optional[str] = None  # RISE/EVEN/FALL
    change_price: Optional[Decimal] = None
    signed_change_price: Optional[Decimal] = None
    change_rate: Optional[Decimal] = None
    signed_change_rate: Optional[Decimal] = None

    # 거래량/거래대금
    trade_volume: Optional[Decimal] = None
    acc_trade_volume: Optional[Decimal] = None
    acc_trade_volume_24h: Optional[Decimal] = None
    acc_trade_price: Optional[Decimal] = None
    acc_trade_price_24h: Optional[Decimal] = None

    # 거래 시간 정보
    trade_date: Optional[str] = None  # yyyyMMdd
    trade_time: Optional[str] = None  # HHmmss
    trade_timestamp: Optional[int] = None  # ms

    # 매수/매도 정보
    ask_bid: Optional[str] = None  # ASK/BID
    acc_ask_volume: Optional[Decimal] = None
    acc_bid_volume: Optional[Decimal] = None

    # 52주 고/저가
    highest_52_week_price: Optional[Decimal] = None
    highest_52_week_date: Optional[str] = None  # yyyy-MM-dd
    lowest_52_week_price: Optional[Decimal] = None
    lowest_52_week_date: Optional[str] = None  # yyyy-MM-dd

    # 거래 상태 (일부 Deprecated)
    trade_status: Optional[str] = None  # Deprecated
    market_state: Optional[str] = None  # PREVIEW/ACTIVE/DELISTED
    market_state_for_ios: Optional[str] = None  # Deprecated
    is_trading_suspended: Optional[bool] = None  # Deprecated
    delisting_date: Optional[str] = None
    market_warning: Optional[str] = None  # NONE/CAUTION

    # 시스템 정보
    timestamp_ms: Optional[int] = None  # timestamp 필드에서 변환
    stream_type: Optional[str] = None  # SNAPSHOT/REALTIME


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
    level: int = 0  # 호가 모아보기 단위 (기본: 0, 기본 호가단위)
    stream_type: Optional[str] = None  # SNAPSHOT/REALTIME


@dataclass
class TradeEvent(BaseWebSocketEvent):
    """체결 이벤트 (업비트 공식 문서 완전 반영)"""
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

    # 최우선 호가 정보
    best_ask_price: Optional[Decimal] = None
    best_ask_size: Optional[Decimal] = None
    best_bid_price: Optional[Decimal] = None
    best_bid_size: Optional[Decimal] = None

    # 스트림 타입
    stream_type: Optional[str] = None


@dataclass
class CandleEvent(BaseWebSocketEvent):
    """캔들 이벤트 (업비트 공식 문서 완전 반영)"""
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

    # 캔들 기준 시각 (핵심 필드)
    candle_date_time_utc: Optional[str] = None
    candle_date_time_kst: Optional[str] = None

    # 스트림 타입
    stream_type: Optional[str] = None


@dataclass
class MyOrderEvent(BaseWebSocketEvent):
    """내 주문 및 체결 이벤트 (업비트 공식 문서 완전 반영)"""
    # 기본 주문 정보
    symbol: Optional[str] = None  # code 필드에서 변환
    uuid: Optional[str] = None  # 주문의 유일 식별자
    ask_bid: Optional[str] = None  # 매수/매도 구분 (ASK/BID)
    order_type: Optional[str] = None  # 주문 타입 (limit/price/market/best)
    state: Optional[str] = None  # 주문 상태 (wait/watch/trade/done/cancel/prevented)

    # 체결 정보
    trade_uuid: Optional[str] = None  # 체결의 유일 식별자
    price: Optional[Decimal] = None  # 주문 가격 또는 체결 가격
    avg_price: Optional[Decimal] = None  # 평균 체결 가격
    volume: Optional[Decimal] = None  # 주문량 또는 체결량
    remaining_volume: Optional[Decimal] = None  # 체결 후 주문 잔량
    executed_volume: Optional[Decimal] = None  # 체결된 수량
    trades_count: Optional[int] = None  # 해당 주문에 걸린 체결 수

    # 수수료 및 자금 정보
    reserved_fee: Optional[Decimal] = None  # 수수료로 예약된 비용
    remaining_fee: Optional[Decimal] = None  # 남은 수수료
    paid_fee: Optional[Decimal] = None  # 사용된 수수료
    locked: Optional[Decimal] = None  # 거래에 사용중인 비용
    executed_funds: Optional[Decimal] = None  # 체결된 금액
    trade_fee: Optional[Decimal] = None  # 체결 시 발생한 수수료

    # 주문 조건 및 메타데이터
    time_in_force: Optional[str] = None  # IOC, FOK, POST_ONLY 설정
    is_maker: Optional[bool] = None  # 메이커/테이커 여부 (체결 시에만)
    identifier: Optional[str] = None  # 클라이언트 지정 주문 식별자

    # SMP (자전거래 체결 방지) 관련 (2025.07.02 신규 추가)
    smp_type: Optional[str] = None  # reduce/cancel_maker/cancel_taker
    prevented_volume: Optional[Decimal] = None  # 자전거래 방지로 취소된 수량
    prevented_locked: Optional[Decimal] = None  # 자전거래 방지로 취소된 금액

    # 타임스탬프
    trade_timestamp: Optional[int] = None  # 체결 타임스탬프 (ms)
    order_timestamp: Optional[int] = None  # 주문 타임스탬프 (ms)
    timestamp_ms: Optional[int] = None  # 타임스탬프 (ms)

    # 스트림 타입
    stream_type: Optional[str] = None  # REALTIME/SNAPSHOT


@dataclass
class AssetItem:
    """자산 개별 아이템"""
    currency: str
    balance: Decimal
    locked: Decimal


@dataclass
class MyAssetEvent(BaseWebSocketEvent):
    """내 자산 이벤트 (업비트 공식 문서 완전 반영)"""
    # 자산 고유 식별자
    asset_uuid: Optional[str] = None

    # 자산 목록 (List of Objects)
    assets: List[AssetItem] = field(default_factory=list)

    # 자산 타임스탬프 (ms)
    asset_timestamp: Optional[int] = None

    # 타임스탬프 (ms)
    timestamp_ms: Optional[int] = None

    # 스트림 타입
    stream_type: Optional[str] = None


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
    # 기본 정보
    'type': 'ticker',
    'code': '마켓 코드 (ex. KRW-BTC)',

    # 가격 정보
    'opening_price': '시가',
    'high_price': '고가',
    'low_price': '저가',
    'trade_price': '현재가',
    'prev_closing_price': '전일 종가',

    # 변화 정보
    'change': '전일 종가 대비 가격 변동 방향 (RISE/EVEN/FALL)',
    'change_price': '전일 대비 가격 변동의 절대값',
    'signed_change_price': '전일 대비 가격 변동 값',
    'change_rate': '전일 대비 등락율의 절대값',
    'signed_change_rate': '전일 대비 등락율',

    # 거래량/거래대금
    'trade_volume': '가장 최근 거래량',
    'acc_trade_volume': '누적 거래량(UTC 0시 기준)',
    'acc_trade_volume_24h': '24시간 누적 거래량',
    'acc_trade_price': '누적 거래대금(UTC 0시 기준)',
    'acc_trade_price_24h': '24시간 누적 거래대금',

    # 거래 시간 정보
    'trade_date': '최근 거래 일자(UTC) - yyyyMMdd',
    'trade_time': '최근 거래 시각(UTC) - HHmmss',
    'trade_timestamp': '체결 타임스탬프(ms)',

    # 매수/매도 정보
    'ask_bid': '매수/매도 구분 (ASK: 매도, BID: 매수)',
    'acc_ask_volume': '누적 매도량',
    'acc_bid_volume': '누적 매수량',

    # 52주 고/저가
    'highest_52_week_price': '52주 최고가',
    'highest_52_week_date': '52주 최고가 달성일 (yyyy-MM-dd)',
    'lowest_52_week_price': '52주 최저가',
    'lowest_52_week_date': '52주 최저가 달성일 (yyyy-MM-dd)',

    # 거래 상태 (일부 Deprecated)
    'trade_status': '거래상태 (Deprecated - 참조 대상에서 제외 권장)',
    'market_state': '거래상태 (PREVIEW: 입금지원, ACTIVE: 거래지원가능, DELISTED: 거래지원종료)',
    'market_state_for_ios': '거래 상태 (Deprecated - 참조 대상에서 제외 권장)',
    'is_trading_suspended': '거래 정지 여부 (Deprecated - 참조 대상에서 제외 권장)',
    'delisting_date': '거래지원 종료일',
    'market_warning': '유의 종목 여부 (NONE: 해당없음, CAUTION: 투자유의)',

    # 기타
    'timestamp': '타임스탬프 (ms)',
    'stream_type': '스트림 타입 (SNAPSHOT: 스냅샷, REALTIME: 실시간)'
}

TRADE_FIELDS = {
    'type': 'trade',
    'code': '마켓 코드',
    'trade_price': '체결 가격',
    'trade_volume': '체결량',
    'ask_bid': '매수/매도 구분 (ASK: 매도, BID: 매수)',
    'change': '전일 종가 대비 가격 변동 방향 (RISE: 상승, EVEN: 보합, FALL: 하락)',
    'change_price': '전일 대비 가격 변동의 절대값',
    'trade_date': '체결 일자(UTC 기준) - yyyy-MM-dd',
    'trade_time': '체결 시각(UTC 기준) - HH:mm:ss',
    'trade_timestamp': '체결 타임스탬프(ms)',
    'timestamp': '타임스탬프(ms)',
    'sequential_id': '체결 번호(Unique)',
    'prev_closing_price': '전일 종가',
    'best_ask_price': '최우선 매도 호가',
    'best_ask_size': '최우선 매도 잔량',
    'best_bid_price': '최우선 매수 호가',
    'best_bid_size': '최우선 매수 잔량',
    'stream_type': '스트림 타입 (SNAPSHOT: 스냅샷, REALTIME: 실시간)'
}

ORDERBOOK_FIELDS = {
    'type': 'orderbook',
    'code': '마켓 코드',
    'total_ask_size': '호가 매도 총 잔량',
    'total_bid_size': '호가 매수 총 잔량',
    'orderbook_units': '호가 리스트',
    'orderbook_units.ask_price': '매도 호가',
    'orderbook_units.bid_price': '매수 호가',
    'orderbook_units.ask_size': '매도 잔량',
    'orderbook_units.bid_size': '매수 잔량',
    'timestamp': '타임스탬프 (ms)',
    'level': '호가 모아보기 단위 (기본: 0, 기본 호가단위) - 원화마켓(KRW)에서만 지원',
    'stream_type': '스트림 타입 (SNAPSHOT: 스냅샷, REALTIME: 실시간)'
}

CANDLE_FIELDS = {
    'type': ('캔들 타입 (candle.1s: 초봉, candle.1m: 1분봉, candle.3m: 3분봉, '
             'candle.5m: 5분봉, candle.10m: 10분봉, candle.15m: 15분봉, '
             'candle.30m: 30분봉, candle.60m: 60분봉, candle.240m: 240분봉)'),
    'code': '마켓 코드 (ex. KRW-BTC)',
    'candle_date_time_utc': '캔들 기준 시각(UTC 기준) - yyyy-MM-dd\'T\'HH:mm:ss',
    'candle_date_time_kst': '캔들 기준 시각(KST 기준) - yyyy-MM-dd\'T\'HH:mm:ss',
    'opening_price': '시가',
    'high_price': '고가',
    'low_price': '저가',
    'trade_price': '종가',
    'candle_acc_trade_price': '누적 거래 금액',
    'candle_acc_trade_volume': '누적 거래량',
    'unit': '캔들 단위',
    'change': '전일 대비',
    'change_price': '변화 가격',
    'change_rate': '변화율',
    'prev_closing_price': '전일 종가',
    'timestamp': '타임스탬프 (ms)',
    'stream_type': '스트림 타입 (SNAPSHOT: 스냅샷, REALTIME: 실시간)'
}

MY_ORDER_FIELDS = {
    'type': 'myOrder',
    'code': '페어 코드(예시:KRW-BTC)',
    'uuid': '주문의 유일 식별자',
    'ask_bid': '매수/매도 구분 (ASK: 매도, BID: 매수)',
    'order_type': '주문 타입 (limit: 지정가, price: 시장가 매수, market: 시장가 매도, best: 최유리 지정가)',
    'state': '주문 상태 (wait: 체결 대기, watch: 예약 주문 대기, trade: 체결 발생, done: 전체 체결 완료, cancel: 주문 취소, prevented: 체결 방지)',
    'trade_uuid': '체결의 유일 식별자',
    'price': '주문 가격 또는 체결 가격(state: trade 일 때)',
    'avg_price': '평균 체결 가격',
    'volume': '주문량 또는 체결량 (state: trade 일 때)',
    'remaining_volume': '체결 후 주문 잔량',
    'executed_volume': '체결된 수량',
    'trades_count': '해당 주문에 걸린 체결 수',
    'reserved_fee': '수수료로 예약된 비용',
    'remaining_fee': '남은 수수료',
    'paid_fee': '사용된 수수료',
    'locked': '거래에 사용중인 비용',
    'executed_funds': '체결된 금액',
    'time_in_force': 'IOC, FOK, POST ONLY 설정 (ioc/fok/post_only)',
    'trade_fee': '체결 시 발생한 수수료 (state:trade가 아닐 경우 null)',
    'is_maker': '체결이 발생한 주문의 메이커/테이커 여부 (true: 메이커, false: 테이커)',
    'identifier': '클라이언트 지정 주문 식별자',
    'smp_type': '자전거래 체결 방지 타입 (reduce: 주문 줄이고 진행, cancel_maker: 메이커 주문 취소, cancel_taker: 테이커 주문 취소)',
    'prevented_volume': '자전거래 체결 방지로 인해 취소된 주문 수량',
    'prevented_locked': '자전거래 체결 방지 설정으로 인해 취소된 금액/수량',
    'trade_timestamp': '체결 타임스탬프 (ms)',
    'order_timestamp': '주문 타임스탬프 (ms)',
    'timestamp': '타임스탬프 (ms)',
    'stream_type': '스트림 타입 (REALTIME: 실시간, SNAPSHOT: 스냅샷)'
}

MY_ASSET_FIELDS = {
    'type': 'myAsset',
    'asset_uuid': '자산 고유 식별자 (UUID)',
    'assets': '자산 목록 (List of Objects)',
    'assets.currency': '화폐 코드 (KRW, BTC, ETH 등)',
    'assets.balance': '주문가능 수량/금액',
    'assets.locked': '주문 중 묶여있는 수량/금액',
    'asset_timestamp': '자산 타임스탬프 (ms)',
    'timestamp': '타임스탬프 (ms)',
    'stream_type': '스트림 타입 (REALTIME: 실시간)'
}


# ================================================================
# 유틸리티 함수
# ================================================================

def create_ticker_event(data: Dict[str, Any], epoch: int = 0,
                        connection_type: WebSocketType = WebSocketType.PUBLIC) -> TickerEvent:
    """Dict에서 TickerEvent 생성 (업비트 공식 문서 모든 필드 지원)"""
    def safe_decimal(value, default=None):
        if value is None:
            return default
        try:
            return Decimal(str(value))
        except (ValueError, TypeError, InvalidOperation):
            return default

    def safe_bool(value, default=None):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)

    return TickerEvent(
        epoch=epoch,
        timestamp=time.time(),
        connection_type=connection_type,

        # 기본 정보
        symbol=data.get('code'),

        # 가격 정보
        opening_price=safe_decimal(data.get('opening_price')),
        high_price=safe_decimal(data.get('high_price')),
        low_price=safe_decimal(data.get('low_price')),
        trade_price=safe_decimal(data.get('trade_price')),
        prev_closing_price=safe_decimal(data.get('prev_closing_price')),

        # 변화 정보
        change=data.get('change'),  # RISE/EVEN/FALL
        change_price=safe_decimal(data.get('change_price')),
        signed_change_price=safe_decimal(data.get('signed_change_price')),
        change_rate=safe_decimal(data.get('change_rate')),
        signed_change_rate=safe_decimal(data.get('signed_change_rate')),

        # 거래량/거래대금
        trade_volume=safe_decimal(data.get('trade_volume')),
        acc_trade_volume=safe_decimal(data.get('acc_trade_volume')),
        acc_trade_volume_24h=safe_decimal(data.get('acc_trade_volume_24h')),
        acc_trade_price=safe_decimal(data.get('acc_trade_price')),
        acc_trade_price_24h=safe_decimal(data.get('acc_trade_price_24h')),

        # 거래 시간 정보
        trade_date=data.get('trade_date'),  # yyyyMMdd
        trade_time=data.get('trade_time'),  # HHmmss
        trade_timestamp=data.get('trade_timestamp'),  # ms

        # 매수/매도 정보
        ask_bid=data.get('ask_bid'),  # ASK/BID
        acc_ask_volume=safe_decimal(data.get('acc_ask_volume')),
        acc_bid_volume=safe_decimal(data.get('acc_bid_volume')),

        # 52주 고/저가
        highest_52_week_price=safe_decimal(data.get('highest_52_week_price')),
        highest_52_week_date=data.get('highest_52_week_date'),  # yyyy-MM-dd
        lowest_52_week_price=safe_decimal(data.get('lowest_52_week_price')),
        lowest_52_week_date=data.get('lowest_52_week_date'),  # yyyy-MM-dd

        # 거래 상태 (일부 Deprecated)
        trade_status=data.get('trade_status'),  # Deprecated
        market_state=data.get('market_state'),  # PREVIEW/ACTIVE/DELISTED
        market_state_for_ios=data.get('market_state_for_ios'),  # Deprecated
        is_trading_suspended=safe_bool(data.get('is_trading_suspended')),  # Deprecated
        delisting_date=data.get('delisting_date'),
        market_warning=data.get('market_warning'),  # NONE/CAUTION

        # 시스템 정보
        timestamp_ms=data.get('timestamp'),
        stream_type=data.get('stream_type')  # SNAPSHOT/REALTIME
    )


def create_trade_event(data: Dict[str, Any], epoch: int = 0,
                       connection_type: WebSocketType = WebSocketType.PUBLIC) -> TradeEvent:
    """Dict에서 TradeEvent 생성 (업비트 공식 문서 모든 필드 지원)"""
    def safe_decimal(value, default=None):
        if value is None:
            return default
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return default

    return TradeEvent(
        epoch=epoch,
        timestamp=time.time(),
        connection_type=connection_type,
        symbol=data.get('code'),
        trade_price=safe_decimal(data.get('trade_price')),
        trade_volume=safe_decimal(data.get('trade_volume')),
        ask_bid=data.get('ask_bid'),
        change=data.get('change'),
        change_price=safe_decimal(data.get('change_price')),
        trade_date=data.get('trade_date'),
        trade_time=data.get('trade_time'),
        trade_timestamp=data.get('trade_timestamp'),
        timestamp_ms=data.get('timestamp'),
        sequential_id=data.get('sequential_id'),
        prev_closing_price=safe_decimal(data.get('prev_closing_price')),

        # 최우선 호가 정보
        best_ask_price=safe_decimal(data.get('best_ask_price')),
        best_ask_size=safe_decimal(data.get('best_ask_size')),
        best_bid_price=safe_decimal(data.get('best_bid_price')),
        best_bid_size=safe_decimal(data.get('best_bid_size')),

        # 스트림 타입
        stream_type=data.get('stream_type')
    )


def create_candle_event(data: Dict[str, Any], epoch: int = 0,
                        connection_type: WebSocketType = WebSocketType.PUBLIC) -> CandleEvent:
    """Dict에서 CandleEvent 생성 (업비트 공식 문서 모든 필드 지원)"""
    def safe_decimal(value, default=None):
        if value is None:
            return default
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return default

    return CandleEvent(
        epoch=epoch,
        timestamp=time.time(),
        connection_type=connection_type,
        symbol=data.get('code'),
        unit=data.get('unit'),
        opening_price=safe_decimal(data.get('opening_price')),
        high_price=safe_decimal(data.get('high_price')),
        low_price=safe_decimal(data.get('low_price')),
        trade_price=safe_decimal(data.get('trade_price')),
        candle_acc_trade_price=safe_decimal(data.get('candle_acc_trade_price')),
        candle_acc_trade_volume=safe_decimal(data.get('candle_acc_trade_volume')),
        change=data.get('change'),
        change_price=safe_decimal(data.get('change_price')),
        change_rate=safe_decimal(data.get('change_rate')),
        prev_closing_price=safe_decimal(data.get('prev_closing_price')),
        timestamp_ms=data.get('timestamp'),

        # 캔들 기준 시각 (핵심 필드)
        candle_date_time_utc=data.get('candle_date_time_utc'),
        candle_date_time_kst=data.get('candle_date_time_kst'),

        # 스트림 타입
        stream_type=data.get('stream_type')
    )


def create_orderbook_event(data: Dict[str, Any], epoch: int = 0,
                           connection_type: WebSocketType = WebSocketType.PUBLIC) -> OrderbookEvent:
    """Dict에서 OrderbookEvent 생성"""
    def safe_decimal(value, default=Decimal('0')):
        if value is None:
            return default
        try:
            return Decimal(str(value))
        except (ValueError, TypeError, InvalidOperation):
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
        level=data.get('level', 0),  # 호가 모아보기 단위 (기본: 0)
        stream_type=data.get('stream_type')  # SNAPSHOT/REALTIME
    )


def create_myasset_event(data: Dict[str, Any], epoch: int = 0,
                         connection_type: WebSocketType = WebSocketType.PRIVATE) -> MyAssetEvent:
    """Dict에서 MyAssetEvent 생성 (업비트 공식 문서 모든 필드 지원)"""
    def safe_decimal(value, default=Decimal('0')):
        if value is None:
            return default
        try:
            return Decimal(str(value))
        except (ValueError, TypeError, InvalidOperation):
            return default

    # assets 목록 처리
    assets = []
    assets_data = data.get('assets', [])
    for asset_data in assets_data:
        assets.append(AssetItem(
            currency=asset_data.get('currency', ''),
            balance=safe_decimal(asset_data.get('balance')),
            locked=safe_decimal(asset_data.get('locked'))
        ))

    return MyAssetEvent(
        epoch=epoch,
        timestamp=time.time(),
        connection_type=connection_type,
        asset_uuid=data.get('asset_uuid'),
        assets=assets,
        asset_timestamp=data.get('asset_timestamp'),
        timestamp_ms=data.get('timestamp'),
        stream_type=data.get('stream_type')
    )


def create_myorder_event(data: Dict[str, Any], epoch: int = 0,
                         connection_type: WebSocketType = WebSocketType.PRIVATE) -> MyOrderEvent:
    """Dict에서 MyOrderEvent 생성 (업비트 공식 문서 모든 필드 지원)"""
    def safe_decimal(value, default=None):
        if value is None:
            return default
        try:
            return Decimal(str(value))
        except (ValueError, TypeError, InvalidOperation):
            return default

    def safe_bool(value, default=None):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)

    return MyOrderEvent(
        epoch=epoch,
        timestamp=time.time(),
        connection_type=connection_type,

        # 기본 주문 정보
        symbol=data.get('code'),
        uuid=data.get('uuid'),
        ask_bid=data.get('ask_bid'),
        order_type=data.get('order_type'),
        state=data.get('state'),

        # 체결 정보
        trade_uuid=data.get('trade_uuid'),
        price=safe_decimal(data.get('price')),
        avg_price=safe_decimal(data.get('avg_price')),
        volume=safe_decimal(data.get('volume')),
        remaining_volume=safe_decimal(data.get('remaining_volume')),
        executed_volume=safe_decimal(data.get('executed_volume')),
        trades_count=data.get('trades_count'),

        # 수수료 및 자금 정보
        reserved_fee=safe_decimal(data.get('reserved_fee')),
        remaining_fee=safe_decimal(data.get('remaining_fee')),
        paid_fee=safe_decimal(data.get('paid_fee')),
        locked=safe_decimal(data.get('locked')),
        executed_funds=safe_decimal(data.get('executed_funds')),
        trade_fee=safe_decimal(data.get('trade_fee')),

        # 주문 조건 및 메타데이터
        time_in_force=data.get('time_in_force'),
        is_maker=safe_bool(data.get('is_maker')),
        identifier=data.get('identifier'),

        # SMP (자전거래 체결 방지) 관련
        smp_type=data.get('smp_type'),
        prevented_volume=safe_decimal(data.get('prevented_volume')),
        prevented_locked=safe_decimal(data.get('prevented_locked')),

        # 타임스탬프
        trade_timestamp=data.get('trade_timestamp'),
        order_timestamp=data.get('order_timestamp'),
        timestamp_ms=data.get('timestamp'),

        # 스트림 타입
        stream_type=data.get('stream_type')
    )


# ================================================================
# 타입 감지 함수들 - format_utils.py로 이관됨
# ================================================================

# 하위 호환성을 위한 래퍼 함수들
def get_data_type_from_message(message: Dict[str, Any]) -> Optional[DataType]:
    """메시지에서 데이터 타입 추론 (format_utils로 이관)"""
    # 순환 import 방지를 위해 지연 import
    from ..support.format_utils import get_message_formatter
    formatter = get_message_formatter()
    return formatter.detect_message_type(message)


def infer_message_type(data: Dict[str, Any]) -> Optional[str]:
    """메시지 타입 추론 (v5 호환성) - format_utils로 이관"""
    data_type = get_data_type_from_message(data)
    return data_type.value if data_type else None


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
            return create_trade_event(message_data, epoch, connection_type)
        elif msg_type and msg_type.startswith('candle.'):
            return create_candle_event(message_data, epoch, connection_type)
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
    'TradeEvent', 'CandleEvent', 'MyOrderEvent', 'MyAssetEvent', 'AssetItem',

    # 구독 및 성능
    'SubscriptionSpec', 'ComponentSubscription', 'PerformanceMetrics',
    'HealthStatus', 'BackpressureConfig', 'ConnectionMetrics',

    # 필드 문서
    'TICKER_FIELDS', 'TRADE_FIELDS', 'ORDERBOOK_FIELDS', 'CANDLE_FIELDS',
    'MY_ORDER_FIELDS', 'MY_ASSET_FIELDS',

    # 유틸리티 함수
    'create_ticker_event', 'create_trade_event', 'create_candle_event', 'create_orderbook_event',
    'create_myasset_event', 'create_myorder_event', 'get_data_type_from_message', 'infer_message_type',
    'convert_dict_to_event', 'validate_symbols', 'normalize_symbols'
]
