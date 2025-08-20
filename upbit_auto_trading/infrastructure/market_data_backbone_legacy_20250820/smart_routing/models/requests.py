"""
데이터 요청 모델 정의

이 모듈은 Smart Router에서 사용하는 요청 모델들을 정의합니다.
각 요청 모델은 불변(immutable) 객체로 설계되어 스레드 안전성을 보장합니다.
"""

from dataclasses import dataclass
from typing import Optional, List, Callable, Dict, Any
from datetime import datetime
from enum import Enum

from .symbols import TradingSymbol
from .timeframes import Timeframe


class RealtimeDataType(Enum):
    """실시간 데이터 타입"""
    TICKER = "ticker"           # 현재가
    ORDERBOOK = "orderbook"     # 호가
    TRADE = "trade"             # 체결

    def __str__(self) -> str:
        return self.value


class DataRequestPriority(Enum):
    """데이터 요청 우선순위"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def timeout_seconds(self) -> int:
        """우선순위별 타임아웃 시간"""
        timeouts = {
            self.LOW: 30,
            self.NORMAL: 15,
            self.HIGH: 10,
            self.CRITICAL: 5
        }
        return timeouts[self]


@dataclass(frozen=True)
class CandleDataRequest:
    """캔들 데이터 요청 모델"""

    symbol: TradingSymbol
    timeframe: Timeframe
    count: Optional[int] = None          # 조회할 캔들 개수 (기본값: 200)
    start_time: Optional[datetime] = None  # 시작 시간
    end_time: Optional[datetime] = None    # 종료 시간
    priority: DataRequestPriority = DataRequestPriority.NORMAL
    force_rest: bool = False             # REST API 강제 사용

    def __post_init__(self):
        """초기화 후 유효성 검증"""
        if self.count is not None and self.count <= 0:
            raise ValueError("count는 양수여야 합니다")

        if self.count is not None and self.count > 1000:
            raise ValueError("count는 1000 이하여야 합니다")

        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValueError("start_time은 end_time보다 이전이어야 합니다")

        # 기본값 설정
        if self.count is None and not self.start_time and not self.end_time:
            object.__setattr__(self, 'count', 200)

    @property
    def is_realtime_request(self) -> bool:
        """실시간 요청인지 확인 (최신 1-2개 캔들)"""
        return (
            self.count is not None and
            self.count <= 2 and
            not self.start_time and
            not self.end_time
        )

    @property
    def is_historical_request(self) -> bool:
        """과거 데이터 요청인지 확인"""
        return not self.is_realtime_request

    @property
    def estimated_response_size(self) -> int:
        """예상 응답 크기 (캔들 개수 기준)"""
        if self.count:
            return self.count
        elif self.start_time and self.end_time:
            # 시간 범위로부터 대략적인 캔들 개수 추정
            duration = self.end_time - self.start_time
            return min(int(duration.total_seconds() / (self.timeframe.minutes * 60)), 1000)
        else:
            return 200  # 기본값


@dataclass(frozen=True)
class TickerDataRequest:
    """티커 데이터 요청 모델"""

    symbol: TradingSymbol
    priority: DataRequestPriority = DataRequestPriority.NORMAL
    force_rest: bool = False

    @property
    def is_realtime_preferred(self) -> bool:
        """실시간 데이터 선호 여부"""
        return not self.force_rest and self.priority in [
            DataRequestPriority.HIGH,
            DataRequestPriority.CRITICAL
        ]


@dataclass(frozen=True)
class OrderbookDataRequest:
    """호가 데이터 요청 모델"""

    symbol: TradingSymbol
    depth: int = 10                      # 호가 깊이
    priority: DataRequestPriority = DataRequestPriority.NORMAL
    force_rest: bool = False

    def __post_init__(self):
        """초기화 후 유효성 검증"""
        if self.depth <= 0 or self.depth > 30:
            raise ValueError("depth는 1-30 사이여야 합니다")


@dataclass(frozen=True)
class TradeHistoryRequest:
    """거래 내역 요청 모델"""

    symbol: TradingSymbol
    count: Optional[int] = None          # 조회할 거래 개수 (기본값: 100)
    cursor: Optional[str] = None         # 페이지네이션 커서
    priority: DataRequestPriority = DataRequestPriority.NORMAL
    force_rest: bool = False

    def __post_init__(self):
        """초기화 후 유효성 검증"""
        if self.count is not None and (self.count <= 0 or self.count > 500):
            raise ValueError("count는 1-500 사이여야 합니다")

        # 기본값 설정
        if self.count is None:
            object.__setattr__(self, 'count', 100)


@dataclass(frozen=True)
class RealtimeSubscriptionRequest:
    """실시간 구독 요청 모델"""

    symbol: TradingSymbol
    data_types: List[RealtimeDataType]
    callback: Callable[[Dict[str, Any]], None]
    auto_reconnect: bool = True          # 자동 재연결
    buffer_size: int = 1000              # 버퍼 크기
    priority: DataRequestPriority = DataRequestPriority.NORMAL

    def __post_init__(self):
        """초기화 후 유효성 검증"""
        if not self.data_types:
            raise ValueError("data_types는 비어있을 수 없습니다")

        if not callable(self.callback):
            raise ValueError("callback은 호출 가능한 객체여야 합니다")

        if self.buffer_size <= 0 or self.buffer_size > 10000:
            raise ValueError("buffer_size는 1-10000 사이여야 합니다")

    @property
    def data_type_strings(self) -> List[str]:
        """문자열 형태의 데이터 타입 목록"""
        return [dt.value for dt in self.data_types]


@dataclass(frozen=True)
class MarketStatusRequest:
    """마켓 상태 요청 모델"""

    priority: DataRequestPriority = DataRequestPriority.LOW

    @property
    def is_low_priority(self) -> bool:
        """낮은 우선순위 요청인지 확인"""
        return self.priority == DataRequestPriority.LOW


@dataclass(frozen=True)
class MarketListRequest:
    """마켓 목록 요청 모델"""

    quote_currency: Optional[str] = None  # 견적 통화 필터 (예: "KRW", "USDT")
    active_only: bool = True             # 활성 마켓만 조회
    priority: DataRequestPriority = DataRequestPriority.LOW

    def __post_init__(self):
        """초기화 후 유효성 검증"""
        if self.quote_currency:
            # 대문자로 정규화
            object.__setattr__(self, 'quote_currency', self.quote_currency.upper())


# 편의 함수들
def create_candle_request(
    symbol_str: str,
    timeframe_str: str,
    count: Optional[int] = None,
    exchange: str = "upbit"
) -> CandleDataRequest:
    """간편한 캔들 요청 생성"""
    from .symbols import parse_symbol
    from .timeframes import parse_timeframe

    symbol = parse_symbol(symbol_str, exchange)
    timeframe = parse_timeframe(timeframe_str)

    return CandleDataRequest(
        symbol=symbol,
        timeframe=timeframe,
        count=count
    )


def create_realtime_request(
    symbol_str: str,
    data_types: List[str],
    callback: Callable[[Dict[str, Any]], None],
    exchange: str = "upbit"
) -> RealtimeSubscriptionRequest:
    """간편한 실시간 구독 요청 생성"""
    from .symbols import parse_symbol

    symbol = parse_symbol(symbol_str, exchange)
    parsed_data_types = [RealtimeDataType(dt) for dt in data_types]

    return RealtimeSubscriptionRequest(
        symbol=symbol,
        data_types=parsed_data_types,
        callback=callback
    )


def create_ticker_request(
    symbol_str: str,
    exchange: str = "upbit"
) -> TickerDataRequest:
    """간편한 티커 요청 생성"""
    from .symbols import parse_symbol

    symbol = parse_symbol(symbol_str, exchange)
    return TickerDataRequest(symbol=symbol)


# 상수
DEFAULT_CANDLE_COUNT = 200
DEFAULT_TRADE_COUNT = 100
DEFAULT_ORDERBOOK_DEPTH = 10
MAX_CANDLE_COUNT = 1000
MAX_TRADE_COUNT = 500
MAX_ORDERBOOK_DEPTH = 30
