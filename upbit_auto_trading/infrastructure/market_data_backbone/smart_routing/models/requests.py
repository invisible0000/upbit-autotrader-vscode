"""
Smart Routing 요청 모델

내부 시스템에서 사용하는 표준화된 요청 모델들입니다.
업비트 API 구조와 완전히 독립적입니다.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

from .symbols import TradingSymbol
from .timeframes import Timeframe


@dataclass(frozen=True)
class CandleDataRequest:
    """캔들 데이터 요청

    시간 범위 요청 우선순위:
    1. start_time이 주어지면 시작점으로 사용
    2. 업비트 API 최대 200개 제한 준수
    3. 200개 초과 예상 시 에러 반환 → Coordinator가 분할 처리

    스냅샷/실시간 구분:
    - realtime_only: 실시간 업데이트만 (stream_type: REALTIME)
    - snapshot_only: 스냅샷 데이터만 (stream_type: SNAPSHOT)
    - 둘 다 False: 스냅샷 + 실시간 모두 (기본값)
    """

    symbol: TradingSymbol
    timeframe: Timeframe
    count: Optional[int] = None      # 조회할 개수 (기본: 200)
    start_time: Optional[datetime] = None  # 시작 시간
    end_time: Optional[datetime] = None    # 종료 시간
    realtime_only: bool = False      # 실시간 데이터만 요청
    snapshot_only: bool = False      # 스냅샷 데이터만 요청

    def __post_init__(self):
        """요청 파라미터 검증"""
        if self.count is not None and self.count <= 0:
            raise ValueError("count는 양수여야 합니다")

        if self.count is not None and self.count > 200:
            raise ValueError(
                f"count({self.count})가 최대 제한(200)을 초과합니다. "
                "Coordinator에서 분할 요청하세요"
            )

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValueError("start_time은 end_time보다 이전이어야 합니다")

        # 상호배타적 옵션 검증
        if self.realtime_only and self.snapshot_only:
            raise ValueError("realtime_only와 snapshot_only는 동시에 설정할 수 없습니다")

    @property
    def has_time_range(self) -> bool:
        """시간 범위가 지정되었는지 확인"""
        return self.start_time is not None or self.end_time is not None

    @property
    def effective_count(self) -> int:
        """실제 사용할 count 값 (기본값 적용)"""
        return self.count if self.count is not None else 200


@dataclass(frozen=True)
class TickerDataRequest:
    """티커 데이터 요청"""

    symbol: TradingSymbol

    # 티커 데이터는 항상 최신 데이터이므로 추가 파라미터 없음


@dataclass(frozen=True)
class OrderbookDataRequest:
    """호가창 데이터 요청"""

    symbol: TradingSymbol
    depth: int = 10  # 호가 깊이 (기본: 10레벨)

    def __post_init__(self):
        """요청 파라미터 검증"""
        if self.depth <= 0:
            raise ValueError("depth는 양수여야 합니다")
        if self.depth > 30:  # 업비트 최대 제한
            raise ValueError("depth는 최대 30까지 지원됩니다")


@dataclass(frozen=True)
class TradeDataRequest:
    """체결 데이터 요청"""

    symbol: TradingSymbol
    count: int = 100           # 조회할 체결 개수 (기본: 100)
    cursor: Optional[str] = None  # 페이지네이션 커서

    def __post_init__(self):
        """요청 파라미터 검증"""
        if self.count <= 0:
            raise ValueError("count는 양수여야 합니다")
        if self.count > 500:  # 업비트 최대 제한
            raise ValueError("count는 최대 500까지 지원됩니다")


@dataclass(frozen=True)
class RealtimeDataRequest:
    """실시간 데이터 구독 요청"""

    symbol: TradingSymbol
    data_types: List[str]  # ["ticker", "orderbook", "trade"]

    def __post_init__(self):
        """요청 파라미터 검증"""
        valid_types = {"ticker", "orderbook", "trade"}
        invalid_types = set(self.data_types) - valid_types

        if invalid_types:
            raise ValueError(f"지원하지 않는 데이터 타입: {invalid_types}")

        if not self.data_types:
            raise ValueError("최소 하나의 데이터 타입이 필요합니다")


# 자주 사용되는 요청 패턴들을 팩토리 메서드로 제공
class RequestFactory:
    """요청 객체 생성을 위한 팩토리 클래스"""

    @staticmethod
    def recent_candles(
        symbol: TradingSymbol,
        timeframe: Timeframe,
        count: int = 200
    ) -> CandleDataRequest:
        """최근 캔들 데이터 요청 (스크리너용)"""
        return CandleDataRequest(
            symbol=symbol,
            timeframe=timeframe,
            count=count
        )

    @staticmethod
    def historical_candles(
        symbol: TradingSymbol,
        timeframe: Timeframe,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> CandleDataRequest:
        """과거 캔들 데이터 요청 (백테스트용)"""
        return CandleDataRequest(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            snapshot_only=True  # 과거 데이터는 스냅샷만
        )

    @staticmethod
    def realtime_candles(
        symbol: TradingSymbol,
        timeframe: Timeframe
    ) -> CandleDataRequest:
        """실시간 캔들 데이터 요청 (트레이딩용)"""
        return CandleDataRequest(
            symbol=symbol,
            timeframe=timeframe,
            count=1,  # 현재 캔들만
            realtime_only=True
        )

    @staticmethod
    def hybrid_candles(
        symbol: TradingSymbol,
        timeframe: Timeframe,
        count: int = 200
    ) -> CandleDataRequest:
        """하이브리드 캔들 요청 (스냅샷 + 실시간)"""
        return CandleDataRequest(
            symbol=symbol,
            timeframe=timeframe,
            count=count
            # realtime_only=False, snapshot_only=False (기본값)
        )

    @staticmethod
    def current_ticker(symbol: TradingSymbol) -> TickerDataRequest:
        """현재 시세 요청"""
        return TickerDataRequest(symbol=symbol)

    @staticmethod
    def full_orderbook(
        symbol: TradingSymbol,
        depth: int = 30
    ) -> OrderbookDataRequest:
        """전체 호가창 요청"""
        return OrderbookDataRequest(symbol=symbol, depth=depth)

    @staticmethod
    def recent_trades(
        symbol: TradingSymbol,
        count: int = 100
    ) -> TradeDataRequest:
        """최근 체결 내역 요청"""
        return TradeDataRequest(symbol=symbol, count=count)

    @staticmethod
    def realtime_ticker(symbol: TradingSymbol) -> RealtimeDataRequest:
        """실시간 티커 구독"""
        return RealtimeDataRequest(symbol=symbol, data_types=["ticker"])

    @staticmethod
    def realtime_all(symbol: TradingSymbol) -> RealtimeDataRequest:
        """실시간 전체 데이터 구독"""
        return RealtimeDataRequest(
            symbol=symbol,
            data_types=["ticker", "orderbook", "trade"]
        )
