"""
데이터 라우터 추상 인터페이스

이 모듈은 Smart Routing의 핵심 인터페이스를 정의합니다.
구현체는 이 인터페이스를 통해 완전한 추상화를 제공하며,
내부 시스템은 업비트 API 구조를 알 필요가 없습니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, Callable
from datetime import datetime

from ..models import TradingSymbol, Timeframe
from ..utils.exceptions import DataRouterException


class IDataRouter(ABC):
    """데이터 라우터 추상 인터페이스

    이 인터페이스는 거래소 독립적인 데이터 요청 API를 제공합니다.
    구현체는 자동으로 최적의 채널(REST/WebSocket)을 선택하고,
    통일된 형태로 데이터를 반환합니다.
    """

    @abstractmethod
    async def get_candle_data(
        self,
        symbol: TradingSymbol,
        timeframe: Timeframe,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """캔들 데이터 조회

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            count: 조회할 캔들 개수 (기본값: 200)
            start_time: 시작 시간 (선택사항)
            end_time: 종료 시간 (선택사항)

        Returns:
            표준화된 캔들 데이터
            {
                "symbol": "KRW-BTC",
                "timeframe": "15m",
                "data": [
                    {
                        "timestamp": "2025-08-20T10:00:00",
                        "open": 95000000,
                        "high": 96000000,
                        "low": 94500000,
                        "close": 95500000,
                        "volume": 123.45
                    }
                ]
            }
        """
        pass

    @abstractmethod
    async def get_ticker_data(self, symbol: TradingSymbol) -> Dict[str, Any]:
        """현재 시세 정보 조회

        Args:
            symbol: 거래 심볼

        Returns:
            표준화된 티커 데이터
            {
                "symbol": "KRW-BTC",
                "price": 95500000,
                "change": 500000,
                "change_rate": 0.0052,
                "volume_24h": 1234.56,
                "timestamp": "2025-08-20T10:00:00"
            }
        """
        pass

    @abstractmethod
    async def get_orderbook_data(
        self,
        symbol: TradingSymbol,
        depth: int = 10
    ) -> Dict[str, Any]:
        """호가 정보 조회

        Args:
            symbol: 거래 심볼
            depth: 호가 깊이 (기본값: 10)

        Returns:
            표준화된 호가 데이터
            {
                "symbol": "KRW-BTC",
                "bids": [{"price": 95000000, "size": 0.1}, ...],
                "asks": [{"price": 95500000, "size": 0.2}, ...],
                "timestamp": "2025-08-20T10:00:00"
            }
        """
        pass

    @abstractmethod
    async def get_trade_history(
        self,
        symbol: TradingSymbol,
        count: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """최근 거래 내역 조회

        Args:
            symbol: 거래 심볼
            count: 조회할 거래 개수 (기본값: 100)
            cursor: 페이지네이션 커서 (선택사항)

        Returns:
            표준화된 거래 내역
            {
                "symbol": "KRW-BTC",
                "trades": [
                    {
                        "timestamp": "2025-08-20T10:00:00",
                        "price": 95500000,
                        "size": 0.01,
                        "side": "buy"
                    }
                ],
                "next_cursor": "..."
            }
        """
        pass

    @abstractmethod
    async def subscribe_realtime(
        self,
        symbol: TradingSymbol,
        data_types: list[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """실시간 데이터 구독

        Args:
            symbol: 거래 심볼
            data_types: 데이터 타입 목록 ["ticker", "orderbook", "trade"]
            callback: 데이터 수신 콜백 함수

        Returns:
            구독 ID (unsubscribe 시 사용)
        """
        pass

    @abstractmethod
    async def unsubscribe_realtime(self, subscription_id: str) -> bool:
        """실시간 데이터 구독 해제

        Args:
            subscription_id: 구독 ID

        Returns:
            성공 여부
        """
        pass

    @abstractmethod
    async def get_market_list(self) -> list[TradingSymbol]:
        """지원하는 마켓 목록 조회

        Returns:
            지원하는 심볼 목록
        """
        pass

    @abstractmethod
    async def get_routing_stats(self) -> Dict[str, Any]:
        """라우팅 통계 정보

        Returns:
            라우팅 성능 및 통계 정보
            {
                "total_requests": 1000,
                "websocket_requests": 300,
                "rest_requests": 700,
                "avg_response_time_ms": 150,
                "error_rate": 0.001
            }
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """라우터 상태 확인

        Returns:
            라우터 상태 정보
            {
                "status": "healthy",
                "websocket_connected": true,
                "rest_api_available": true,
                "last_check": "2025-08-20T10:00:00"
            }
        """
        pass


class IRealtimeDataStream(ABC):
    """실시간 데이터 스트림 인터페이스"""

    @abstractmethod
    async def start_stream(
        self,
        symbol: TradingSymbol,
        data_types: list[str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """실시간 데이터 스트림 시작

        Args:
            symbol: 거래 심볼
            data_types: 데이터 타입 목록

        Yields:
            실시간 데이터
        """
        pass

    @abstractmethod
    async def stop_stream(self) -> None:
        """실시간 데이터 스트림 중지"""
        pass


class IChannelSelector(ABC):
    """채널 선택 전략 인터페이스"""

    @abstractmethod
    def should_use_websocket(
        self,
        symbol: TradingSymbol,
        data_type: str,
        request_params: Dict[str, Any]
    ) -> bool:
        """WebSocket 사용 여부 결정

        Args:
            symbol: 거래 심볼
            data_type: 데이터 타입 ("candle", "ticker", "orderbook", "trade")
            request_params: 요청 파라미터

        Returns:
            WebSocket 사용 여부
        """
        pass

    @abstractmethod
    def get_channel_priority(
        self,
        symbol: TradingSymbol,
        data_type: str
    ) -> list[str]:
        """채널 우선순위 반환

        Args:
            symbol: 거래 심볼
            data_type: 데이터 타입

        Returns:
            채널 우선순위 목록 ["websocket", "rest"] 또는 ["rest", "websocket"]
        """
        pass
