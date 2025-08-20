"""
데이터 라우터 추상 인터페이스

기존 IDataRouter를 기반으로 개선된 완전 추상화 인터페이스입니다.
내부 시스템이 업비트 API 구조를 전혀 몰라도 되도록 설계되었습니다.

주요 개선사항:
1. 완전한 도메인 모델 기반 (TradingSymbol, Timeframe)
2. 자율적 채널 선택 (REST ↔ WebSocket 자동 전환)
3. API 제한 준수 (200개 초과 시 명시적 에러)
4. 시간 범위 요청 우선순위 명확화
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime

from ..models import (
    TradingSymbol,
    Timeframe,
    CandleDataResponse,
    TickerDataResponse,
    OrderbookDataResponse,
    TradeDataResponse,
    RoutingStatsResponse,
    HealthCheckResponse
)
from ..utils.exceptions import SmartRoutingException


class IDataRouter(ABC):
    """완전 추상화된 데이터 라우터 인터페이스

    이 인터페이스는:
    1. 거래소 독립적인 도메인 모델만 사용
    2. 자율적으로 최적 채널(REST/WebSocket) 선택
    3. 업비트 API 제한(200개)을 준수하여 에러 반환
    4. 내부 빈도 분석으로 WebSocket 전환 결정
    """

    @abstractmethod
    async def get_candle_data(
        self,
        symbol: TradingSymbol,
        timeframe: Timeframe,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> CandleDataResponse:
        """캔들 데이터 조회

        시간 범위 요청 우선순위:
        1. start_time이 주어지면 시작점으로 사용
        2. 업비트 API 최대 200개 제한 준수
        3. 200개 초과 예상 시 DataRangeExceedsLimitException 발생
        4. 스크리너: 현재 시간부터 역순으로 N개 (최신 데이터 우선)
        5. 백테스트: start_time부터 순서대로 최대 200개

        Args:
            symbol: 거래 심볼 (도메인 모델)
            timeframe: 타임프레임 (도메인 모델)
            count: 조회할 캔들 개수 (기본값: 200, 최대: 200)
            start_time: 시작 시간 (선택사항)
            end_time: 종료 시간 (선택사항)

        Returns:
            표준화된 캔들 데이터 응답

        Raises:
            DataRangeExceedsLimitException: 200개 초과 요청 시
            SymbolNotSupportedException: 지원하지 않는 심볼
            TimeframeNotSupportedException: 지원하지 않는 타임프레임
            InvalidRequestException: 잘못된 요청 파라미터
        """
        pass

    @abstractmethod
    async def get_ticker_data(self, symbol: TradingSymbol) -> TickerDataResponse:
        """현재 시세 정보 조회

        자율적으로 최적 채널 선택:
        - 고빈도 요청: WebSocket 구독 전환
        - 저빈도 요청: REST API 사용

        Args:
            symbol: 거래 심볼 (도메인 모델)

        Returns:
            표준화된 티커 데이터 응답

        Raises:
            SymbolNotSupportedException: 지원하지 않는 심볼
            ApiRateLimitException: API 제한 도달
        """
        pass

    @abstractmethod
    async def get_orderbook_data(
        self,
        symbol: TradingSymbol,
        depth: int = 10
    ) -> OrderbookDataResponse:
        """호가 정보 조회

        Args:
            symbol: 거래 심볼 (도메인 모델)
            depth: 호가 깊이 (기본값: 10, 최대: 30)

        Returns:
            표준화된 호가 데이터 응답

        Raises:
            SymbolNotSupportedException: 지원하지 않는 심볼
            InvalidRequestException: 잘못된 depth 값
        """
        pass

    @abstractmethod
    async def get_trade_data(
        self,
        symbol: TradingSymbol,
        count: int = 100,
        cursor: Optional[str] = None
    ) -> TradeDataResponse:
        """최근 거래 내역 조회

        Args:
            symbol: 거래 심볼 (도메인 모델)
            count: 조회할 거래 개수 (기본값: 100, 최대: 500)
            cursor: 페이지네이션 커서 (선택사항)

        Returns:
            표준화된 거래 내역 응답

        Raises:
            SymbolNotSupportedException: 지원하지 않는 심볼
            InvalidRequestException: 잘못된 count 값
        """
        pass

    @abstractmethod
    async def subscribe_realtime(
        self,
        symbol: TradingSymbol,
        data_types: List[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """실시간 데이터 구독

        Note: 이 기능은 Layer 1에서는 기본 구현만 제공하고,
              실제 실시간 처리는 상위 Layer에서 구현하는 것을 권장

        Args:
            symbol: 거래 심볼 (도메인 모델)
            data_types: 데이터 타입 목록 ["ticker", "orderbook", "trade"]
            callback: 데이터 수신 콜백 함수

        Returns:
            구독 ID (unsubscribe 시 사용)

        Raises:
            SymbolNotSupportedException: 지원하지 않는 심볼
            WebSocketConnectionException: WebSocket 연결 실패
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
    async def get_market_list(self) -> List[TradingSymbol]:
        """지원하는 마켓 목록 조회

        Returns:
            지원하는 심볼 목록 (도메인 모델)
        """
        pass

    @abstractmethod
    async def get_routing_stats(self) -> RoutingStatsResponse:
        """라우팅 통계 정보

        자율적 채널 선택의 성과를 모니터링

        Returns:
            라우팅 성능 및 통계 정보
        """
        pass

    @abstractmethod
    async def health_check(self) -> HealthCheckResponse:
        """라우터 상태 확인

        Returns:
            라우터 상태 정보
        """
        pass


class IChannelSelector(ABC):
    """자율적 채널 선택 전략 인터페이스

    내부 빈도 분석을 통해 REST ↔ WebSocket 자동 전환
    """

    @abstractmethod
    def should_use_websocket(
        self,
        symbol: TradingSymbol,
        data_type: str,
        recent_request_count: int
    ) -> bool:
        """WebSocket 사용 여부 자율적 결정

        Args:
            symbol: 거래 심볼
            data_type: 데이터 타입 ("candle", "ticker", "orderbook", "trade")
            recent_request_count: 최근 요청 빈도

        Returns:
            WebSocket 사용 여부 (내부 분석 기반)
        """
        pass

    @abstractmethod
    def update_request_pattern(
        self,
        symbol: TradingSymbol,
        data_type: str,
        request_time: datetime
    ) -> None:
        """요청 패턴 업데이트

        자율적 분석을 위한 요청 이력 누적

        Args:
            symbol: 거래 심볼
            data_type: 데이터 타입
            request_time: 요청 시간
        """
        pass


class IFrequencyAnalyzer(ABC):
    """요청 빈도 분석 인터페이스

    Smart Router가 자율적으로 최적 채널을 선택하기 위한
    요청 패턴 분석 기능
    """

    @abstractmethod
    def analyze_request_frequency(
        self,
        symbol: TradingSymbol,
        data_type: str,
        time_window_minutes: int = 5
    ) -> float:
        """요청 빈도 분석

        Args:
            symbol: 거래 심볼
            data_type: 데이터 타입
            time_window_minutes: 분석 시간 윈도우 (분)

        Returns:
            분당 요청 횟수
        """
        pass

    @abstractmethod
    def get_websocket_threshold(self, data_type: str) -> float:
        """WebSocket 전환 임계값

        Args:
            data_type: 데이터 타입

        Returns:
            분당 요청 횟수 임계값 (이 이상이면 WebSocket 사용)
        """
        pass
