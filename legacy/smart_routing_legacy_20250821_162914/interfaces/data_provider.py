"""
데이터 제공자 추상 인터페이스

업비트 전용 데이터 제공자 인터페이스입니다.
Smart Router가 사용하는 저수준 API 추상화입니다.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import (
    TradingSymbol,
    Timeframe,
    CandleDataRequest,
    TickerDataRequest,
    OrderbookDataRequest,
    TradeDataRequest,
    CandleDataResponse,
    TickerDataResponse,
    OrderbookDataResponse,
    TradeDataResponse
)


class IDataProvider(ABC):
    """데이터 제공자 추상 인터페이스

    업비트 API에 특화된 저수준 데이터 제공 인터페이스
    Smart Router가 내부적으로 사용합니다.
    """

    @abstractmethod
    async def get_candle_data(self, request: CandleDataRequest) -> CandleDataResponse:
        """캔들 데이터 조회

        Args:
            request: 캔들 데이터 요청 (검증된 상태)

        Returns:
            캔들 데이터 응답
        """
        pass

    @abstractmethod
    async def get_ticker_data(self, request: TickerDataRequest) -> TickerDataResponse:
        """티커 데이터 조회

        Args:
            request: 티커 데이터 요청

        Returns:
            티커 데이터 응답
        """
        pass

    @abstractmethod
    async def get_orderbook_data(
        self,
        request: OrderbookDataRequest
    ) -> OrderbookDataResponse:
        """호가창 데이터 조회

        Args:
            request: 호가창 데이터 요청

        Returns:
            호가창 데이터 응답
        """
        pass

    @abstractmethod
    async def get_trade_data(self, request: TradeDataRequest) -> TradeDataResponse:
        """체결 데이터 조회

        Args:
            request: 체결 데이터 요청

        Returns:
            체결 데이터 응답
        """
        pass

    @abstractmethod
    async def get_market_list(self) -> List[TradingSymbol]:
        """지원하는 마켓 목록 조회

        Returns:
            지원하는 심볼 목록
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """제공자 상태 확인

        Returns:
            제공자 상태 정보
        """
        pass


class IWebSocketProvider(ABC):
    """WebSocket 데이터 제공자 인터페이스

    실시간 데이터 구독을 위한 WebSocket 제공자
    """

    @abstractmethod
    async def connect(self) -> bool:
        """WebSocket 연결

        Returns:
            연결 성공 여부
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """WebSocket 연결 해제"""
        pass

    @abstractmethod
    async def subscribe_ticker(
        self,
        symbols: List[TradingSymbol],
        callback: Any
    ) -> str:
        """티커 구독

        Args:
            symbols: 구독할 심볼 목록
            callback: 데이터 수신 콜백

        Returns:
            구독 ID
        """
        pass

    @abstractmethod
    async def subscribe_orderbook(
        self,
        symbols: List[TradingSymbol],
        callback: Any
    ) -> str:
        """호가창 구독

        Args:
            symbols: 구독할 심볼 목록
            callback: 데이터 수신 콜백

        Returns:
            구독 ID
        """
        pass

    @abstractmethod
    async def subscribe_trades(
        self,
        symbols: List[TradingSymbol],
        callback: Any
    ) -> str:
        """체결 구독

        Args:
            symbols: 구독할 심볼 목록
            callback: 데이터 수신 콜백

        Returns:
            구독 ID
        """
        pass

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 해제

        Args:
            subscription_id: 구독 ID

        Returns:
            해제 성공 여부
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """연결 상태 확인

        Returns:
            연결 상태
        """
        pass
