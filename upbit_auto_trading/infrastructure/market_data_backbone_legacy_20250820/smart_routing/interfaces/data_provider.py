"""
데이터 제공자 추상 인터페이스

이 모듈은 거래소별 데이터 제공자의 추상 인터페이스를 정의합니다.
각 거래소(업비트, 바이낸스 등)는 이 인터페이스를 구현하여
통일된 데이터 접근 방식을 제공합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..models import TradingSymbol, Timeframe


class IDataProvider(ABC):
    """데이터 제공자 추상 인터페이스

    거래소별 구현체가 이 인터페이스를 구현하여
    REST API와 WebSocket 통신을 담당합니다.
    """

    @property
    @abstractmethod
    def exchange_name(self) -> str:
        """거래소 이름"""
        pass

    @property
    @abstractmethod
    def supported_timeframes(self) -> List[Timeframe]:
        """지원하는 타임프레임 목록"""
        pass

    @property
    @abstractmethod
    def supports_websocket(self) -> bool:
        """WebSocket 지원 여부"""
        pass

    # REST API 메서드들
    @abstractmethod
    async def fetch_candle_data(
        self,
        symbol: TradingSymbol,
        timeframe: Timeframe,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """REST API를 통한 캔들 데이터 조회"""
        pass

    @abstractmethod
    async def fetch_ticker_data(self, symbol: TradingSymbol) -> Dict[str, Any]:
        """REST API를 통한 티커 데이터 조회"""
        pass

    @abstractmethod
    async def fetch_orderbook_data(
        self,
        symbol: TradingSymbol,
        depth: int = 10
    ) -> Dict[str, Any]:
        """REST API를 통한 호가 데이터 조회"""
        pass

    @abstractmethod
    async def fetch_trade_history(
        self,
        symbol: TradingSymbol,
        count: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """REST API를 통한 거래 내역 조회"""
        pass

    @abstractmethod
    async def fetch_market_list(self) -> List[TradingSymbol]:
        """REST API를 통한 마켓 목록 조회"""
        pass

    # WebSocket 메서드들
    @abstractmethod
    async def subscribe_ticker(
        self,
        symbols: List[TradingSymbol]
    ) -> str:
        """WebSocket 티커 구독"""
        pass

    @abstractmethod
    async def subscribe_orderbook(
        self,
        symbols: List[TradingSymbol]
    ) -> str:
        """WebSocket 호가 구독"""
        pass

    @abstractmethod
    async def subscribe_trades(
        self,
        symbols: List[TradingSymbol]
    ) -> str:
        """WebSocket 거래 내역 구독"""
        pass

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """WebSocket 구독 해제"""
        pass

    @abstractmethod
    async def disconnect_websocket(self) -> None:
        """WebSocket 연결 해제"""
        pass

    # 상태 관리 메서드들
    @abstractmethod
    async def is_healthy(self) -> bool:
        """제공자 상태 확인"""
        pass

    @abstractmethod
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """레이트 제한 상태 조회"""
        pass

    @abstractmethod
    def get_last_error(self) -> Optional[Exception]:
        """마지막 오류 정보"""
        pass


class IFieldMapper(ABC):
    """필드 매핑 인터페이스

    거래소별 응답 형식을 표준 형식으로 변환합니다.
    """

    @abstractmethod
    def map_candle_fields(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """캔들 데이터 필드 매핑"""
        pass

    @abstractmethod
    def map_ticker_fields(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """티커 데이터 필드 매핑"""
        pass

    @abstractmethod
    def map_orderbook_fields(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """호가 데이터 필드 매핑"""
        pass

    @abstractmethod
    def map_trade_fields(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """거래 데이터 필드 매핑"""
        pass


class IRateLimiter(ABC):
    """레이트 제한 관리 인터페이스"""

    @abstractmethod
    async def acquire_permit(self, endpoint: str) -> bool:
        """API 호출 허가 요청

        Args:
            endpoint: API 엔드포인트

        Returns:
            호출 가능 여부
        """
        pass

    @abstractmethod
    async def release_permit(self, endpoint: str) -> None:
        """API 호출 허가 반납

        Args:
            endpoint: API 엔드포인트
        """
        pass

    @abstractmethod
    def get_remaining_calls(self, endpoint: str) -> int:
        """남은 호출 횟수

        Args:
            endpoint: API 엔드포인트

        Returns:
            남은 호출 횟수
        """
        pass

    @abstractmethod
    def get_reset_time(self, endpoint: str) -> Optional[datetime]:
        """제한 초기화 시간

        Args:
            endpoint: API 엔드포인트

        Returns:
            제한 초기화 시간
        """
        pass


class IConnectionManager(ABC):
    """연결 관리 인터페이스"""

    @abstractmethod
    async def connect(self) -> bool:
        """연결 수립"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """연결 해제"""
        pass

    @abstractmethod
    async def reconnect(self) -> bool:
        """재연결"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """연결 상태 핑 테스트"""
        pass


class IErrorHandler(ABC):
    """오류 처리 인터페이스"""

    @abstractmethod
    async def handle_api_error(
        self,
        error: Exception,
        endpoint: str,
        retry_count: int = 0
    ) -> bool:
        """API 오류 처리

        Args:
            error: 발생한 오류
            endpoint: 오류가 발생한 엔드포인트
            retry_count: 재시도 횟수

        Returns:
            재시도 여부
        """
        pass

    @abstractmethod
    async def handle_websocket_error(
        self,
        error: Exception,
        reconnect: bool = True
    ) -> bool:
        """WebSocket 오류 처리

        Args:
            error: 발생한 오류
            reconnect: 재연결 여부

        Returns:
            복구 성공 여부
        """
        pass

    @abstractmethod
    def should_retry(self, error: Exception, retry_count: int) -> bool:
        """재시도 여부 판단

        Args:
            error: 발생한 오류
            retry_count: 현재 재시도 횟수

        Returns:
            재시도 여부
        """
        pass


class IDataValidator(ABC):
    """데이터 유효성 검증 인터페이스"""

    @abstractmethod
    def validate_symbol(self, symbol: TradingSymbol) -> bool:
        """심볼 유효성 검증"""
        pass

    @abstractmethod
    def validate_timeframe(self, timeframe: Timeframe) -> bool:
        """타임프레임 유효성 검증"""
        pass

    @abstractmethod
    def validate_response_data(
        self,
        data: Dict[str, Any],
        data_type: str
    ) -> bool:
        """응답 데이터 유효성 검증

        Args:
            data: 응답 데이터
            data_type: 데이터 타입 ("candle", "ticker", "orderbook", "trade")

        Returns:
            유효성 검증 결과
        """
        pass
