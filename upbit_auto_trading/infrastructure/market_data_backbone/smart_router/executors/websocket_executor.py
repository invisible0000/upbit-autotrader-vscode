# d:\projects\upbit-autotrader-vscode\upbit_auto_trading\infrastructure\market_data_backbone\smart_router\executors\websocket_executor.py

import asyncio
from typing import Dict, Any, Callable, Optional

from smart_router.request import MarketDataRequest
from smart_router.core.batch_subscription_manager import BatchSubscriptionManager

# TODO: 기존 업비트 WebSocket 클라이언트에 대한 실제 임포트 경로로 교체하세요.
# from upbit_auto_trading.infrastructure.api.upbit_websocket_client import UpbitWebSocketClient
# 현재는 플레이스홀더 클래스를 사용합니다.
class UpbitWebSocketClient:
    def __init__(self):
        self._message_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        print("디버그: UpbitWebSocketClient 초기화됨 (플레이스홀더)")

    async def connect(self):
        print("디버그: UpbitWebSocketClient 연결 중 (플레이스홀더)")
        # 연결 시뮬레이션
        await asyncio.sleep(0.1)
        print("디버그: UpbitWebSocketClient 연결됨 (플레이스홀더)")

    async def disconnect(self):
        print("디버그: UpbitWebSocketClient 연결 해제 중 (플레이스홀더)")
        await asyncio.sleep(0.1)

    async def send_message(self, message: str):
        print(f"디버그: UpbitWebSocketClient 메시지 전송 중: {message}")
        # 전송 시뮬레이션
        await asyncio.sleep(0.05)

    def set_message_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self._message_callback = callback
        print("디버그: UpbitWebSocketClient 메시지 콜백 설정됨.")

    # 실제 클라이언트에서는 메시지를 수신하고 _message_callback을 호출하는 백그라운드 작업이 있을 것입니다.
    # 이 플레이스홀더에서는 시뮬레이션만 합니다.
    async def _simulate_incoming_message(self, data: Dict[str, Any]):
        if self._message_callback:
            self._message_callback(data)


class WebSocketExecutor:
    """
    일괄 처리 메커니즘과 인프라 계층의 기존 업비트 WebSocket 클라이언트를 활용하여
    시장 데이터에 대한 WebSocket 통신을 관리합니다.
    """
    def __init__(self, websocket_client: UpbitWebSocketClient):
        self.websocket_client = websocket_client
        self.batch_manager = BatchSubscriptionManager(
            send_websocket_message_func=self.websocket_client.send_message
        )
        # 수신되는 데이터를 처리하기 위해 WebSocket 클라이언트에 대한 메시지 콜백을 설정합니다.
        self.websocket_client.set_message_callback(self._process_incoming_message)
        self._data_listeners: Dict[str, Callable[[Dict[str, Any]], None]] = {} # 수신되는 데이터를 라우팅하기 위함

    async def connect(self):
        """WebSocket 연결을 설정합니다."""
        await self.websocket_client.connect()

    async def disconnect(self):
        """WebSocket 연결을 닫습니다."""
        await self.websocket_client.disconnect()

    async def execute(self, request: MarketDataRequest) -> None:
        """
        WebSocket 데이터 스트림을 구독합니다.
        참고: WebSocket 실행은 일반적으로 연속 스트리밍을 위한 것이므로,
        REST처럼 단일 응답을 반환하지 않습니다.
        대신, 구독을 관리하고 수신되는 데이터는 콜백을 통해 처리됩니다.
        """
        print(f"디버그: WebSocketExecutor가 받은 data_type: {request.data_type}, realtime: {request.realtime}")

        if not request.realtime:
            raise ValueError("WebSocketExecutor는 주로 실시간 요청을 위한 것입니다.")

        if request.data_type in ['realtime_ticker', 'realtime_orderbook', 'realtime_trade']:
            # 업비트 WS API는 메시지에서 'ticker', 'orderbook', 'trade'를 유형으로 사용합니다.
            # 내부 'realtime_ticker'를 WS 메시지용 'ticker'로 매핑합니다.
            ws_data_type = request.data_type.replace('realtime_', '')
            await self.batch_manager.subscribe(ws_data_type, request.symbols)
        else:
            raise ValueError(f"WebSocket에 대해 지원되지 않는 data_type: {request.data_type}")

    def register_data_listener(self, data_type: str, listener: Callable[[Dict[str, Any]], None]):
        """
        특정 유형의 수신되는 WebSocket 데이터를 수신하기 위한 콜백 함수를 등록합니다.
        """
        self._data_listeners[data_type] = listener

    def _process_incoming_message(self, message: Dict[str, Any]):
        """
        WebSocket 클라이언트로부터 수신된 메시지를 처리하기 위한 내부 콜백입니다.
        메시지를 등록된 리스너에게 라우팅합니다.
        """
        # 업비트 WS 메시지에 'type' 필드가 있다고 가정합니다.
        message_type = message.get('type')
        if message_type:
            # 업비트 WS 유형을 리스너를 위한 내부 'realtime_' 유형으로 다시 매핑합니다.
            internal_data_type = f"realtime_{message_type}"
            if internal_data_type in self._data_listeners:
                self._data_listeners[internal_data_type](message)
            else:
                print(f"경고: WebSocket 데이터 유형에 대한 리스너가 등록되지 않았습니다: {internal_data_type}")
        else:
            print(f"경고: 'type' 필드가 없는 WebSocket 메시지를 수신했습니다: {message}")
