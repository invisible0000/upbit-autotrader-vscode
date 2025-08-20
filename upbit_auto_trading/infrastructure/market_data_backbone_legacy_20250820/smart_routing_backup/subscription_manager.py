"""
WebSocket 구독 관리자 - Smart Router와 실제 WebSocket 클라이언트 연결

기능:
1. 구독 요청 관리 (구독/해지/상태 추적)
2. 자동 연결/재연결 처리
3. 데이터 수신 및 분배
4. 에러 처리 및 복구
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient, WebSocketDataType, WebSocketMessage
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


class SubscriptionStatus(Enum):
    """구독 상태"""
    INACTIVE = "inactive"
    CONNECTING = "connecting"
    ACTIVE = "active"
    ERROR = "error"
    RECONNECTING = "reconnecting"


@dataclass
class SubscriptionRequest:
    """구독 요청 정보"""
    symbol: str
    data_type: WebSocketDataType
    callback: Optional[Callable[[Dict[str, Any]], None]] = None
    created_at: datetime = field(default_factory=datetime.now)
    status: SubscriptionStatus = SubscriptionStatus.INACTIVE
    retry_count: int = 0


class WebSocketSubscriptionManager:
    """WebSocket 구독 관리자"""

    def __init__(self):
        self._logger = create_component_logger("WebSocketSubscriptionManager")

        # WebSocket 클라이언트
        self._ws_client: Optional[UpbitWebSocketQuotationClient] = None

        # 구독 관리
        self._subscriptions: Dict[str, SubscriptionRequest] = {}  # subscription_id -> request
        self._symbol_subscriptions: Dict[str, Set[str]] = {}  # symbol -> subscription_ids
        self._active_symbols: Set[str] = set()

        # 콜백 관리
        self._global_handlers: Dict[WebSocketDataType, List[Callable]] = {}
        self._data_buffer: Dict[str, Dict[str, Any]] = {}  # symbol -> latest_data

        # 연결 상태
        self._connection_status = SubscriptionStatus.INACTIVE
        self._last_heartbeat: Optional[datetime] = None
        self._reconnect_task: Optional[asyncio.Task] = None

        # 설정
        self.max_retry_attempts = 5
        self.reconnect_delay = 5.0
        self.heartbeat_interval = 30.0

    def _generate_subscription_id(self, symbol: str, data_type: WebSocketDataType) -> str:
        """구독 ID 생성"""
        return f"{symbol}:{data_type.value}:{datetime.now().timestamp()}"

    async def subscribe(self, symbol: str, data_type: WebSocketDataType,
                        callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> str:
        """
        데이터 구독

        Args:
            symbol: 심볼 (예: KRW-BTC)
            data_type: 데이터 타입 (ticker, trade, orderbook)
            callback: 데이터 수신 콜백

        Returns:
            subscription_id: 구독 ID (해지용)
        """
        subscription_id = self._generate_subscription_id(symbol, data_type)

        # 구독 요청 생성
        request = SubscriptionRequest(
            symbol=symbol,
            data_type=data_type,
            callback=callback,
            status=SubscriptionStatus.CONNECTING
        )

        self._subscriptions[subscription_id] = request

        # 심볼별 구독 추적
        if symbol not in self._symbol_subscriptions:
            self._symbol_subscriptions[symbol] = set()
        self._symbol_subscriptions[symbol].add(subscription_id)

        self._logger.info(f"구독 요청: {symbol} ({data_type.value}) -> {subscription_id}")

        # 연결 확보 및 실제 구독
        await self._ensure_connection()
        await self._subscribe_to_websocket(symbol, data_type)

        # 구독 성공
        request.status = SubscriptionStatus.ACTIVE
        self._active_symbols.add(symbol)

        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 해지"""
        if subscription_id not in self._subscriptions:
            self._logger.warning(f"구독 ID 없음: {subscription_id}")
            return False

        request = self._subscriptions[subscription_id]
        symbol = request.symbol

        # 구독 제거
        del self._subscriptions[subscription_id]
        self._symbol_subscriptions[symbol].discard(subscription_id)

        # 해당 심볼의 다른 구독이 없으면 WebSocket에서도 해지
        if not self._symbol_subscriptions[symbol]:
            self._active_symbols.discard(symbol)
            # TODO: WebSocket 개별 해지 (현재 업비트는 전체 해지만 지원)

        self._logger.info(f"구독 해지: {subscription_id} ({symbol})")
        return True

    async def unsubscribe_symbol(self, symbol: str) -> int:
        """심볼의 모든 구독 해지"""
        if symbol not in self._symbol_subscriptions:
            return 0

        subscription_ids = list(self._symbol_subscriptions[symbol])
        count = 0

        for sub_id in subscription_ids:
            if await self.unsubscribe(sub_id):
                count += 1

        return count

    async def get_latest_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """최신 데이터 조회 (캐시된 데이터)"""
        return self._data_buffer.get(symbol)

    def add_global_handler(self, data_type: WebSocketDataType,
                           handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """전역 데이터 핸들러 추가"""
        if data_type not in self._global_handlers:
            self._global_handlers[data_type] = []
        self._global_handlers[data_type].append(handler)

    async def _ensure_connection(self) -> None:
        """WebSocket 연결 확보"""
        if self._ws_client and self._ws_client.is_connected:
            return

        self._connection_status = SubscriptionStatus.CONNECTING

        try:
            # 새 클라이언트 생성
            self._ws_client = UpbitWebSocketQuotationClient()

            # 데이터 핸들러 등록 (동기 함수로 래핑)
            self._ws_client.add_message_handler(WebSocketDataType.TICKER, self._handle_ticker_data)
            self._ws_client.add_message_handler(WebSocketDataType.TRADE, self._handle_trade_data)
            self._ws_client.add_message_handler(WebSocketDataType.ORDERBOOK, self._handle_orderbook_data)

            # 연결
            success = await self._ws_client.connect()
            if success:
                self._connection_status = SubscriptionStatus.ACTIVE
                self._last_heartbeat = datetime.now()
                self._logger.info("WebSocket 연결 성공")

                # 백그라운드에서 메시지 리스닝 시작
                asyncio.create_task(self._listen_messages())
            else:
                raise Exception("WebSocket 연결 실패")

        except Exception as e:
            self._connection_status = SubscriptionStatus.ERROR
            self._logger.error(f"WebSocket 연결 실패: {e}")

            # 재연결 시도
            if not self._reconnect_task:
                self._reconnect_task = asyncio.create_task(self._reconnect_loop())
            raise

    async def _listen_messages(self) -> None:
        """메시지 리스닝 루프"""
        if not self._ws_client:
            return

        try:
            async for message in self._ws_client.listen():
                # 메시지를 동기 핸들러로 전달
                if message.type in self._ws_client.message_handlers:
                    for handler in self._ws_client.message_handlers[message.type]:
                        try:
                            handler(message)
                        except Exception as e:
                            self._logger.error(f"메시지 핸들러 실행 실패: {e}")
        except Exception as e:
            self._logger.error(f"메시지 리스닝 실패: {e}")
            self._connection_status = SubscriptionStatus.ERROR

    async def _subscribe_to_websocket(self, symbol: str, data_type: WebSocketDataType) -> None:
        """실제 WebSocket 구독"""
        if not self._ws_client or not self._ws_client.is_connected:
            raise Exception("WebSocket 연결되지 않음")

        try:
            if data_type == WebSocketDataType.TICKER:
                await self._ws_client.subscribe_ticker([symbol])
            elif data_type == WebSocketDataType.TRADE:
                await self._ws_client.subscribe_trade([symbol])
            elif data_type == WebSocketDataType.ORDERBOOK:
                await self._ws_client.subscribe_orderbook([symbol])
            else:
                raise ValueError(f"지원하지 않는 데이터 타입: {data_type}")

        except Exception as e:
            self._logger.error(f"WebSocket 구독 실패: {symbol} ({data_type.value}) - {e}")
            raise

    def _handle_ticker_data(self, message: WebSocketMessage) -> None:
        """Ticker 데이터 처리 (동기 함수)"""
        try:
            symbol = message.market
            data = message.data

            # 데이터 캐시
            self._data_buffer[symbol] = data
            self._last_heartbeat = datetime.now()

            # 개별 콜백 호출 (비동기 처리를 위해 태스크 생성)
            asyncio.create_task(self._dispatch_to_callbacks(symbol, WebSocketDataType.TICKER, data))

            # 전역 핸들러 호출
            asyncio.create_task(self._dispatch_to_global_handlers(WebSocketDataType.TICKER, symbol, data))

        except Exception as e:
            self._logger.error(f"Ticker 데이터 처리 실패: {e}")

    def _handle_trade_data(self, message: WebSocketMessage) -> None:
        """Trade 데이터 처리 (동기 함수)"""
        try:
            symbol = message.market
            data = message.data

            # 개별 콜백 호출
            asyncio.create_task(self._dispatch_to_callbacks(symbol, WebSocketDataType.TRADE, data))

            # 전역 핸들러 호출
            asyncio.create_task(self._dispatch_to_global_handlers(WebSocketDataType.TRADE, symbol, data))

        except Exception as e:
            self._logger.error(f"Trade 데이터 처리 실패: {e}")

    def _handle_orderbook_data(self, message: WebSocketMessage) -> None:
        """Orderbook 데이터 처리 (동기 함수)"""
        try:
            symbol = message.market
            data = message.data

            # 개별 콜백 호출
            asyncio.create_task(self._dispatch_to_callbacks(symbol, WebSocketDataType.ORDERBOOK, data))

            # 전역 핸들러 호출
            asyncio.create_task(self._dispatch_to_global_handlers(WebSocketDataType.ORDERBOOK, symbol, data))

        except Exception as e:
            self._logger.error(f"Orderbook 데이터 처리 실패: {e}")

    async def _dispatch_to_callbacks(self, symbol: str, data_type: WebSocketDataType,
                                     data: Dict[str, Any]) -> None:
        """개별 구독 콜백 호출"""
        if symbol not in self._symbol_subscriptions:
            return

        for sub_id in self._symbol_subscriptions[symbol]:
            if sub_id not in self._subscriptions:
                continue

            request = self._subscriptions[sub_id]
            if request.data_type == data_type and request.callback:
                try:
                    # 콜백이 코루틴인지 확인
                    if asyncio.iscoroutinefunction(request.callback):
                        await request.callback(data)
                    else:
                        request.callback(data)
                except Exception as e:
                    self._logger.error(f"콜백 실행 실패: {sub_id} - {e}")

    async def _dispatch_to_global_handlers(self, data_type: WebSocketDataType,
                                           symbol: str, data: Dict[str, Any]) -> None:
        """전역 핸들러 호출"""
        if data_type not in self._global_handlers:
            return

        for handler in self._global_handlers[data_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(symbol, data)
                else:
                    handler(symbol, data)
            except Exception as e:
                self._logger.error(f"전역 핸들러 실행 실패: {e}")

    async def _reconnect_loop(self) -> None:
        """재연결 루프"""
        retry_count = 0

        while retry_count < self.max_retry_attempts and self._connection_status == SubscriptionStatus.ERROR:
            retry_count += 1
            self._logger.info(f"재연결 시도 {retry_count}/{self.max_retry_attempts}")

            await asyncio.sleep(self.reconnect_delay)

            try:
                await self._ensure_connection()

                # 기존 구독 복원
                await self._restore_subscriptions()

                self._logger.info("재연결 성공")
                break

            except Exception as e:
                self._logger.error(f"재연결 실패: {e}")

        self._reconnect_task = None

    async def _restore_subscriptions(self) -> None:
        """구독 복원"""
        for symbol in self._active_symbols:
            # 각 심볼의 데이터 타입별로 구독 복원
            data_types = set()
            for sub_id in self._symbol_subscriptions.get(symbol, set()):
                if sub_id in self._subscriptions:
                    data_types.add(self._subscriptions[sub_id].data_type)

            for data_type in data_types:
                try:
                    await self._subscribe_to_websocket(symbol, data_type)
                except Exception as e:
                    self._logger.error(f"구독 복원 실패: {symbol} ({data_type.value}) - {e}")

    async def disconnect(self) -> None:
        """연결 해제"""
        self._connection_status = SubscriptionStatus.INACTIVE

        # 재연결 태스크 정리
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None

        # WebSocket 연결 해제
        if self._ws_client:
            await self._ws_client.disconnect()
            self._ws_client = None

        # 구독 정리
        self._subscriptions.clear()
        self._symbol_subscriptions.clear()
        self._active_symbols.clear()
        self._data_buffer.clear()

        self._logger.info("WebSocket 구독 관리자 종료")

    def get_status(self) -> Dict[str, Any]:
        """상태 정보 조회"""
        return {
            "connection_status": self._connection_status.value,
            "active_subscriptions": len(self._subscriptions),
            "active_symbols": list(self._active_symbols),
            "last_heartbeat": self._last_heartbeat.isoformat() if self._last_heartbeat else None,
            "is_connected": self._ws_client.is_connected if self._ws_client else False
        }


def create_subscription_manager() -> WebSocketSubscriptionManager:
    """구독 관리자 팩토리"""
    return WebSocketSubscriptionManager()
