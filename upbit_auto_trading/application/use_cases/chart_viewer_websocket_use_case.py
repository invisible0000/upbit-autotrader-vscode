"""
차트뷰어 WebSocket 데이터 처리 UseCase (Application Layer)

호가창과 차트뷰의 실시간 데이터 요청 및 구독 관리를 담당.
DDD 아키텍처: Presentation -> Application -> Infrastructure
"""

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.services.websocket_market_data_service import WebSocketMarketDataService


class ChartViewerWebSocketUseCase:
    """
    차트뷰어 WebSocket 데이터 처리 UseCase (Application Layer)

    - 호가창 실시간 데이터 구독/해제
    - 현재가 실시간 데이터 구독/해제
    - WebSocket 서비스 생명주기 관리
    - Presentation Layer와 Infrastructure Layer 연결
    """

    def __init__(self, websocket_service: WebSocketMarketDataService):
        """UseCase 초기화"""
        self._logger = create_component_logger("ChartViewerWebSocketUseCase")
        self._websocket_service = websocket_service

    async def request_orderbook_subscription(self, symbol: str) -> bool:
        """
        호가창 실시간 구독 요청

        Args:
            symbol: 심볼 (예: "KRW-BTC")

        Returns:
            bool: 구독 성공 여부
        """
        try:
            self._logger.info(f"호가창 실시간 구독 요청: {symbol}")

            # WebSocket 서비스가 실행되지 않았다면 시작
            if not self._websocket_service.is_running():
                started = await self._websocket_service.start_service()
                if not started:
                    self._logger.error("WebSocket 서비스 시작 실패")
                    return False

            # 호가창 구독
            success = await self._websocket_service.subscribe_orderbook(symbol)
            if success:
                self._logger.info(f"호가창 구독 성공: {symbol}")
            else:
                self._logger.error(f"호가창 구독 실패: {symbol}")

            return success

        except Exception as e:
            self._logger.error(f"호가창 구독 요청 오류 - {symbol}: {e}")
            return False

    async def request_ticker_subscription(self, symbol: str) -> bool:
        """
        현재가 실시간 구독 요청

        Args:
            symbol: 심볼 (예: "KRW-BTC")

        Returns:
            bool: 구독 성공 여부
        """
        try:
            self._logger.info(f"현재가 실시간 구독 요청: {symbol}")

            # WebSocket 서비스가 실행되지 않았다면 시작
            if not self._websocket_service.is_running():
                started = await self._websocket_service.start_service()
                if not started:
                    self._logger.error("WebSocket 서비스 시작 실패")
                    return False

            # 현재가 구독
            success = await self._websocket_service.subscribe_ticker(symbol)
            if success:
                self._logger.info(f"현재가 구독 성공: {symbol}")
            else:
                self._logger.error(f"현재가 구독 실패: {symbol}")

            return success

        except Exception as e:
            self._logger.error(f"현재가 구독 요청 오류 - {symbol}: {e}")
            return False

    async def cancel_symbol_subscription(self, symbol: str) -> None:
        """
        심볼의 모든 구독 해제

        Args:
            symbol: 심볼 (예: "KRW-BTC")
        """
        try:
            self._logger.info(f"심볼 구독 해제: {symbol}")
            await self._websocket_service.unsubscribe_symbol(symbol)

        except Exception as e:
            self._logger.error(f"심볼 구독 해제 오류 - {symbol}: {e}")

    async def start_websocket_service(self) -> bool:
        """
        WebSocket 서비스 수동 시작

        Returns:
            bool: 시작 성공 여부
        """
        try:
            self._logger.info("WebSocket 서비스 수동 시작 요청")
            return await self._websocket_service.start_service()

        except Exception as e:
            self._logger.error(f"WebSocket 서비스 시작 오류: {e}")
            return False

    async def stop_websocket_service(self) -> None:
        """WebSocket 서비스 중지"""
        try:
            self._logger.info("WebSocket 서비스 중지 요청")
            await self._websocket_service.stop_service()

        except Exception as e:
            self._logger.error(f"WebSocket 서비스 중지 오류: {e}")

    def get_service_status(self) -> dict:
        """
        WebSocket 서비스 상태 조회

        Returns:
            dict: 서비스 상태 정보
        """
        return {
            'is_running': self._websocket_service.is_running(),
            'subscribed_symbols': self._websocket_service.get_subscribed_symbols(),
            'subscriber_count': len(self._websocket_service.get_subscribed_symbols())
        }
