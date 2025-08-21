"""
Smart Routing 응답 모델

표준화된 응답 형태를 정의합니다.
내부 시스템이 일관된 형태로 데이터를 받을 수 있도록 합니다.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

from .symbols import TradingSymbol
from .timeframes import Timeframe
from .market_data_types import (
    CandleData,
    TickerData,
    OrderbookData,
    TradeData
)


@dataclass(frozen=True)
class ResponseMetadata:
    """응답 메타데이터

    요청 처리에 대한 부가 정보
    """

    request_time: datetime
    response_time: datetime
    data_source: str  # "rest" 또는 "websocket"
    cache_hit: bool = False

    @property
    def processing_time_ms(self) -> float:
        """처리 시간 (밀리초)"""
        delta = self.response_time - self.request_time
        return delta.total_seconds() * 1000


@dataclass(frozen=True)
class CandleDataResponse:
    """캔들 데이터 응답"""

    symbol: TradingSymbol
    timeframe: Timeframe
    data: List[CandleData]
    metadata: ResponseMetadata

    @property
    def count(self) -> int:
        """데이터 개수"""
        return len(self.data)

    @property
    def is_empty(self) -> bool:
        """데이터가 비어있는지 확인"""
        return len(self.data) == 0

    @property
    def latest_candle(self) -> Optional[CandleData]:
        """가장 최신 캔들"""
        return self.data[-1] if self.data else None

    @property
    def earliest_candle(self) -> Optional[CandleData]:
        """가장 오래된 캔들"""
        return self.data[0] if self.data else None


@dataclass(frozen=True)
class TickerDataResponse:
    """티커 데이터 응답"""

    symbol: TradingSymbol
    data: TickerData
    metadata: ResponseMetadata

    @property
    def current_price(self) -> float:
        """현재가 (편의 메서드)"""
        return float(self.data.current_price)

    @property
    def change_percentage(self) -> float:
        """변화율 퍼센트 (편의 메서드)"""
        return float(self.data.change_percentage)


@dataclass(frozen=True)
class OrderbookDataResponse:
    """호가창 데이터 응답"""

    symbol: TradingSymbol
    data: OrderbookData
    metadata: ResponseMetadata

    @property
    def bid_count(self) -> int:
        """매수 호가 개수"""
        return len(self.data.bids)

    @property
    def ask_count(self) -> int:
        """매도 호가 개수"""
        return len(self.data.asks)

    @property
    def spread(self) -> Optional[float]:
        """호가 스프레드 (편의 메서드)"""
        spread = self.data.spread
        return float(spread) if spread else None


@dataclass(frozen=True)
class TradeDataResponse:
    """체결 데이터 응답"""

    symbol: TradingSymbol
    data: List[TradeData]
    metadata: ResponseMetadata
    next_cursor: Optional[str] = None  # 페이지네이션용

    @property
    def count(self) -> int:
        """체결 개수"""
        return len(self.data)

    @property
    def is_empty(self) -> bool:
        """데이터가 비어있는지 확인"""
        return len(self.data) == 0

    @property
    def latest_trade(self) -> Optional[TradeData]:
        """가장 최신 체결"""
        return self.data[-1] if self.data else None

    @property
    def has_more(self) -> bool:
        """더 많은 데이터가 있는지 확인"""
        return self.next_cursor is not None


@dataclass(frozen=True)
class RoutingStatsResponse:
    """라우팅 통계 응답"""

    total_requests: int
    websocket_requests: int
    rest_requests: int
    avg_response_time_ms: float
    error_rate: float
    cache_hit_rate: float
    metadata: ResponseMetadata

    @property
    def websocket_usage_rate(self) -> float:
        """WebSocket 사용률"""
        if self.total_requests == 0:
            return 0.0
        return self.websocket_requests / self.total_requests

    @property
    def rest_usage_rate(self) -> float:
        """REST API 사용률"""
        if self.total_requests == 0:
            return 0.0
        return self.rest_requests / self.total_requests


@dataclass(frozen=True)
class HealthCheckResponse:
    """상태 확인 응답"""

    status: str  # "healthy", "degraded", "unhealthy"
    websocket_connected: bool
    rest_api_available: bool
    last_check: datetime
    metadata: ResponseMetadata
    details: Optional[Dict[str, Any]] = None

    @property
    def is_healthy(self) -> bool:
        """정상 상태인지 확인"""
        return self.status == "healthy"

    @property
    def is_degraded(self) -> bool:
        """성능 저하 상태인지 확인"""
        return self.status == "degraded"

    @property
    def is_unhealthy(self) -> bool:
        """비정상 상태인지 확인"""
        return self.status == "unhealthy"


# 응답 생성을 위한 팩토리 클래스
class ResponseFactory:
    """응답 객체 생성을 위한 팩토리"""

    @staticmethod
    def create_metadata(
        request_time: datetime,
        data_source: str,
        cache_hit: bool = False
    ) -> ResponseMetadata:
        """메타데이터 생성"""
        return ResponseMetadata(
            request_time=request_time,
            response_time=datetime.now(),
            data_source=data_source,
            cache_hit=cache_hit
        )

    @staticmethod
    def candle_response(
        symbol: TradingSymbol,
        timeframe: Timeframe,
        data: List[CandleData],
        request_time: datetime,
        data_source: str,
        cache_hit: bool = False
    ) -> CandleDataResponse:
        """캔들 데이터 응답 생성"""
        metadata = ResponseFactory.create_metadata(
            request_time, data_source, cache_hit
        )
        return CandleDataResponse(
            symbol=symbol,
            timeframe=timeframe,
            data=data,
            metadata=metadata
        )

    @staticmethod
    def ticker_response(
        symbol: TradingSymbol,
        data: TickerData,
        request_time: datetime,
        data_source: str,
        cache_hit: bool = False
    ) -> TickerDataResponse:
        """티커 데이터 응답 생성"""
        metadata = ResponseFactory.create_metadata(
            request_time, data_source, cache_hit
        )
        return TickerDataResponse(
            symbol=symbol,
            data=data,
            metadata=metadata
        )
