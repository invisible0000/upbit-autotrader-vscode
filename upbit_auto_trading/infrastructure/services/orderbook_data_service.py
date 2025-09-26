"""
호가창 데이터 서비스 - Infrastructure Layer

WebSocket과 REST API를 통합하여 호가창 데이터를 제공합니다.
- WebSocket 우선 정책 (QAsync 기반)
- REST API 백업 (DDD Infrastructure 준수)
- 실시간 데이터 통합
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal
from qasync import asyncSlot

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.events.bus.in_memory_event_bus import InMemoryEventBus
from upbit_auto_trading.infrastructure.services.websocket_market_data_service import WebSocketMarketDataService
from upbit_auto_trading.application.use_cases.chart_viewer_websocket_use_case import ChartViewerWebSocketUseCase
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient


class OrderbookDataService(QObject):
    """호가창 데이터 서비스 - QAsync 기반 실시간 WebSocket + REST 백업"""

    # QAsync 시그널 정의
    subscription_completed = pyqtSignal(str, bool)  # symbol, success
    unsubscription_completed = pyqtSignal(str)      # symbol

    def __init__(self, event_bus: Optional[InMemoryEventBus] = None):
        """서비스 초기화"""
        super().__init__()
        self._logger = create_component_logger("OrderbookDataService")
        self._event_bus = event_bus

        # WebSocket 관련
        self._websocket_service: Optional[WebSocketMarketDataService] = None
        self._websocket_use_case: Optional[ChartViewerWebSocketUseCase] = None
        self._websocket_initialized = False
        self._websocket_connected = False

        # REST API 클라이언트 (DDD Infrastructure Layer)
        self._rest_client: Optional[UpbitPublicClient] = None
        self._rest_client_ready = False

        # 현재 상태
        self._current_symbol = "KRW-BTC"
        self._current_market = "KRW"

        # 지연 초기화 (PyQt6 환경에서 안전)
        self._initialize_websocket_delayed()
        self._initialize_rest_client_delayed()

    def _initialize_websocket_delayed(self) -> None:
        """WebSocket 지연 초기화"""
        if not self._event_bus:
            self._logger.warning("이벤트 버스가 없어 WebSocket 초기화 불가")
            return

        try:
            self._websocket_service = WebSocketMarketDataService(self._event_bus)
            self._websocket_use_case = ChartViewerWebSocketUseCase(self._websocket_service)
            self._websocket_initialized = True

            self._logger.info("✅ OrderbookDataService WebSocket 초기화 완료")
        except Exception as e:
            self._logger.error(f"WebSocket 초기화 실패: {e}")

    def _initialize_rest_client_delayed(self) -> None:
        """REST 클라이언트 지연 초기화 - DDD Infrastructure Layer 준수"""
        try:
            self._rest_client = UpbitPublicClient()
            self._rest_client_ready = True
            self._logger.info("✅ OrderbookDataService REST 클라이언트 초기화 완료")
        except Exception as e:
            self._logger.error(f"❌ REST 클라이언트 초기화 실패: {e}")

    @asyncSlot(str)
    async def subscribe_symbol(self, symbol: str) -> bool:
        """심볼 WebSocket 구독 - QAsync 기반"""
        if not self._websocket_use_case:
            self._logger.warning("WebSocket UseCase가 초기화되지 않음")
            self.subscription_completed.emit(symbol, False)
            return False

        try:
            # QAsync를 통해 안전하게 비동기 작업 실행
            success = await self._websocket_use_case.request_orderbook_subscription(symbol)

            if success:
                self._websocket_connected = True
                self._current_symbol = symbol
                self._logger.info(f"✅ WebSocket 구독 성공: {symbol}")
            else:
                self._logger.warning(f"⚠️ WebSocket 구독 실패: {symbol}")

            # 시그널 발생
            self.subscription_completed.emit(symbol, success)
            return success

        except asyncio.CancelledError:
            self._logger.info(f"WebSocket 구독 취소됨: {symbol}")
            self.subscription_completed.emit(symbol, False)
            return False
        except Exception as e:
            self._logger.error(f"❌ WebSocket 구독 오류 - {symbol}: {e}")
            self.subscription_completed.emit(symbol, False)
            return False

    @asyncSlot(str)
    async def unsubscribe_symbol(self, symbol: str) -> None:
        """심볼 WebSocket 구독 해제 - QAsync 기반"""
        if not self._websocket_use_case:
            self._logger.warning("WebSocket UseCase가 초기화되지 않음")
            self.unsubscription_completed.emit(symbol)
            return

        try:
            # QAsync를 통해 안전하게 비동기 작업 실행
            await self._websocket_use_case.cancel_symbol_subscription(symbol)

            self._websocket_connected = False
            self._logger.info(f"✅ WebSocket 구독 해제: {symbol}")

            # 시그널 발생
            self.unsubscription_completed.emit(symbol)

        except asyncio.CancelledError:
            self._logger.info(f"WebSocket 구독 해제 취소됨: {symbol}")
            self.unsubscription_completed.emit(symbol)
        except Exception as e:
            self._logger.error(f"❌ WebSocket 구독 해제 오류 - {symbol}: {e}")
            self.unsubscription_completed.emit(symbol)

    async def load_rest_orderbook(self, symbol: str) -> Optional[Dict[str, Any]]:
        """DDD Infrastructure Layer를 통한 호가 데이터 로드"""
        if not self._rest_client_ready or not self._rest_client:
            self._logger.warning(f"⚠️ REST 클라이언트 준비되지 않음: {symbol}")
            return None

        try:
            # DDD Infrastructure Layer 준수: UpbitPublicClient 사용
            orderbooks_data = await self._rest_client.get_orderbooks([symbol])

            if not orderbooks_data:
                self._logger.warning(f"⚠️ 호가 데이터 없음: {symbol}")
                return None

            orderbook = orderbooks_data[0]
            asks = []
            bids = []

            for unit in orderbook.get("orderbook_units", []):
                asks.append({
                    "price": float(unit["ask_price"]),
                    "quantity": float(unit["ask_size"]),
                    "total": float(unit["ask_size"])
                })

                bids.append({
                    "price": float(unit["bid_price"]),
                    "quantity": float(unit["bid_size"]),
                    "total": float(unit["bid_size"])
                })

            # 정렬
            asks.sort(key=lambda x: x["price"])
            bids.sort(key=lambda x: x["price"], reverse=True)

            # 누적 수량 계산
            asks_total = 0
            for ask in asks:
                asks_total += ask["quantity"]
                ask["total"] = asks_total

            bids_total = 0
            for bid in bids:
                bids_total += bid["quantity"]
                bid["total"] = bids_total

            result = {
                "symbol": symbol,
                "asks": asks,
                "bids": bids,
                "timestamp": orderbook.get("timestamp", datetime.now().isoformat()),
                "market": symbol.split("-")[0],
                "source": "infrastructure_layer"  # DDD 준수 표시
            }

            self._logger.info(f"✅ DDD Infrastructure 호가 데이터 로드: {symbol} (매도 {len(asks)}개, 매수 {len(bids)}개)")
            return result

        except Exception as e:
            self._logger.error(f"❌ DDD Infrastructure 호가 데이터 로드 실패: {symbol} - {str(e)}")
            return None

    def get_connection_status(self) -> Dict[str, Any]:
        """연결 상태 정보 반환"""
        return {
            "websocket_initialized": self._websocket_initialized,
            "websocket_connected": self._websocket_connected,
            "rest_client_ready": self._rest_client_ready,
            "current_symbol": self._current_symbol,
            "current_market": self._current_market
        }

    def is_websocket_connected(self) -> bool:
        """WebSocket 연결 상태 확인"""
        return self._websocket_connected

    def get_current_symbol(self) -> str:
        """현재 구독 중인 심볼 반환"""
        return self._current_symbol
