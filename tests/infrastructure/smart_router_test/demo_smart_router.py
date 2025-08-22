# d:\projects\upbit-autotrader-vscode\tests\infrastructure\smart_router_test\demo_smart_router.py

import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Callable

# smart_router 모듈 임포트
from smart_router.request import MarketDataRequest
from smart_router.core.metrics_collector import MetricsCollector
from smart_router.core.rate_limit_manager import RateLimitManager
from smart_router.core.adaptive_routing_engine import AdaptiveRoutingEngine
from smart_router.core.batch_subscription_manager import BatchSubscriptionManager
from smart_router.executors.rest_executor import RestExecutor
from smart_router.executors.websocket_executor import WebSocketExecutor
from smart_router.transformers.data_converter import DataConverter
from smart_router.router import SmartRouter, InMemoryCache
from smart_router.models.canonical_ticker import CanonicalTicker
from smart_router.models.canonical_candle import CanonicalCandle

# ==============================================================================
# Mock Clients for Demonstration (More verbose than test mocks)
# ==============================================================================

class DemoUpbitRestClient:
    """
    실제 REST API 호출을 시뮬레이션하는 모의 클라이언트입니다.
    응답과 헤더를 시뮬레이션하고 디버그 메시지를 출력합니다.
    """
    def __init__(self):
        self._call_count = 0

    async def get_market_data(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        self._call_count += 1
        print(f"[DemoREST] API 호출 시뮬레이션: {endpoint} (params: {params})")
        await asyncio.sleep(0.05) # 네트워크 지연 시뮬레이션
        # Remaining-Req: limit:remaining:reset_seconds
        # 여기서는 간단하게 100개 중 99개 남았고 60초 후 재설정된다고 가정
        headers = {'Remaining-Req': f'100:{100 - self._call_count % 100}:60'}

        # 티커 데이터 시뮬레이션
        if endpoint == "/v1/ticker":
            market = params.get('markets', 'UNKNOWN').split(',')[0]
            return {"data": [{"market": market, "trade_price": 50000000 + self._call_count * 100, "trade_volume": 1.0}], "headers": headers}
        elif "candles" in endpoint:
            market = params.get('market', 'UNKNOWN')
            return {"data": [{"market": market, "opening_price": 100, "trade_price": 105, "candle_acc_trade_volume": 1000}], "headers": headers}

        return {"data": f"시뮬레이션된 REST 응답 for {endpoint}", "headers": headers}

    async def get_account_info(self) -> Dict[str, Any]:
        self._call_count += 1
        print("[DemoREST] API 호출 시뮬레이션: 계정 정보")
        await asyncio.sleep(0.03) # 네트워크 지연 시뮬레이션
        headers = {'Remaining-Req': f'10:{(10 - self._call_count % 10)}:60'}
        return {"data": "시뮬레이션된 계정 정보", "headers": headers}


class DemoUpbitWebSocketClient:
    """
    실제 WebSocket 통신을 시뮬레이션하는 모의 클라이언트입니다.
    연결, 메시지 전송, 메시지 수신 콜백을 시뮬레이션합니다.
    """
    def __init__(self):
        self._message_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._is_connected = False
        self._send_count = 0
        print("[DemoWS] WebSocket 클라이언트 초기화됨.")

    async def connect(self):
        if not self._is_connected:
            print("[DemoWS] WebSocket 연결 시뮬레이션 중...")
            await asyncio.sleep(0.1) # 연결 지연 시뮬레이션
            self._is_connected = True
            print("[DemoWS] WebSocket 연결됨.")
        else:
            print("[DemoWS] WebSocket 이미 연결됨.")

    async def disconnect(self):
        if self._is_connected:
            print("[DemoWS] WebSocket 연결 해제 시뮬레이션 중...")
            await asyncio.sleep(0.05)
            self._is_connected = False
            print("[DemoWS] WebSocket 연결 해제됨.")
        else:
            print("[DemoWS] WebSocket 이미 연결 해제됨.")

    async def send_message(self, message: str):
        self._send_count += 1
        print(f"[DemoWS] 메시지 전송 시뮬레이션 ({self._send_count}번째): {message[:100]}...")
        await asyncio.sleep(0.01) # 전송 지연 시뮬레이션
        # 메시지 전송 후 즉시 시뮬레이션된 응답을 콜백으로 보낼 수 있습니다.
        # 실제 WS에서는 서버에서 비동기적으로 데이터가 도착합니다.
        # 여기서는 간단한 티커 응답을 시뮬레이션합니다.
        try:
            msg_obj = json.loads(message)
            if isinstance(msg_obj, list) and len(msg_obj) > 1:
                # 구독 메시지라고 가정
                for item in msg_obj[1:]:
                    if item.get('type') == 'ticker' and 'codes' in item:
                        for code in item['codes']:
                            simulated_data = {
                                "type": "ticker",
                                "code": code,
                                "trade_price": 50000000 + self._send_count * 1000,
                                "trade_volume": 1.23,
                                "change": "RISE",
                                "trade_timestamp": int(time.time() * 1000)
                            }
                            if self._message_callback:
                                # 비동기적으로 콜백 호출
                                asyncio.create_task(self._async_callback(simulated_data))
        except json.JSONDecodeError:
            print(f"[DemoWS] JSON 디코딩 오류: {message}")

    def set_message_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self._message_callback = callback
        print("[DemoWS] 메시지 콜백 설정됨.")

    async def _async_callback(self, data: Dict[str, Any]):
        """비동기적으로 메시지 콜백을 호출하기 위한 헬퍼."""
        await asyncio.sleep(0.001) # 콜백 호출 지연 시뮬레이션
        self._message_callback(data)

# ==============================================================================
# Demo Scenarios
# ==============================================================================

async def run_demo_scenario(smart_router: SmartRouter, description: str, request: MarketDataRequest):
    """단일 시나리오를 실행하고 결과를 출력합니다."""
    print(f"\n--- 시나리오 시작: {description} ---")
    start_time = time.time()

    result = await smart_router.get_data(request)

    end_time = time.time()
    print(f"--- 시나리오 종료: {description} (소요 시간: {end_time - start_time:.4f}초) ---")
    if result is not None:
        print(f"결과: {result}")
    else:
        print("결과: (실시간 스트림 또는 캐시 적중으로 인해 직접 반환된 데이터 없음)")
    print("-" * 50)

async def main():
    print("SmartRouter 데모 시작...")

    # 클라이언트 초기화
    rest_client = DemoUpbitRestClient()
    websocket_client = DemoUpbitWebSocketClient()

    # SmartRouter 초기화
    router = SmartRouter(
        rest_client=rest_client,
        websocket_client=websocket_client,
        metrics_collector=MetricsCollector(),
        rate_limit_manager=RateLimitManager(),
        data_converter=DataConverter(),
        cache=InMemoryCache()
    )

    # WebSocket 연결 (필요한 경우 SmartRouter 내부에서 처리되지만, 명시적으로 연결할 수도 있습니다.)
    await router.connect_websocket()

    # SmartRouter에서 수신되는 실시간 데이터를 처리하는 콜백 등록
    # 이 콜백은 DemoUpbitWebSocketClient가 시뮬레이션된 데이터를 보낼 때 호출됩니다.
    def realtime_data_handler(data):
        print(f"[실시간 데이터 수신] {data.symbol}: {data.trade_price}")

    # SmartRouter의 _process_realtime_ticker 메서드가 CanonicalTicker를 반환하므로,
    # 이를 외부로 전달하는 메커니즘이 필요합니다. 여기서는 간단히 SmartRouter 내부에
    # 임시로 콜백을 추가하여 처리합니다. 실제 구현에서는 더 정교한 Pub/Sub 시스템이 필요합니다.
    router._process_realtime_ticker_original = router._process_realtime_ticker # 원본 저장
    router._realtime_subscribers = [] # 구독자 목록
    def custom_process_realtime_ticker(raw_data):
        canonical_ticker = router.data_converter.convert_websocket_ticker_to_canonical(raw_data)
        print(f"정보: 실시간 티커 수신 및 처리: {canonical_ticker.symbol} - {canonical_ticker.trade_price}")
        for sub_callback in router._realtime_subscribers:
            sub_callback(canonical_ticker)
    router._process_realtime_ticker = custom_process_realtime_ticker # 커스텀 콜백으로 교체


    router._realtime_subscribers.append(realtime_data_handler)


    # --- 시나리오 1: 계정 정보 요청 (REST 전용) ---
    await run_demo_scenario(router, "계정 정보 요청 (REST 전용)",
                            MarketDataRequest(data_type='account_info'))

    # --- 시나리오 2: 빈번한 티커 요청 (WebSocket으로 전환되어야 함) ---
    print("\n--- 시나리오 시작: 빈번한 티커 요청 (WebSocket 전환 예상) ---")
    for i in range(1, 15): # 14번 요청
        req = MarketDataRequest(data_type='ticker', symbols=['KRW-BTC'], realtime=False) # 스냅샷 요청
        start_time = time.time()
        result = await router.get_data(req)
        end_time = time.time()
        print(f"요청 {i}: 채널 결정 및 응답 수신 (소요 시간: {end_time - start_time:.4f}초)")
        if result:
            print(f"  결과: {result.symbol} - {result.trade_price}")
        await asyncio.sleep(0.05) # 요청 간 짧은 지연
    print("--- 시나리오 종료: 빈번한 티커 요청 ---")
    print("-" * 50)

    # --- 시나리오 3: 캔들 데이터 요청 (REST 전용) ---
    await run_demo_scenario(router, "캔들 데이터 요청 (REST 전용)",
                            MarketDataRequest(data_type='candle', symbols=['KRW-XRP'], interval='1m', count=1))

    # --- 시나리오 4: 속도 제한 트리거 및 대기 관찰 ---
    print("\n--- 시나리오 시작: 속도 제한 트리거 및 대기 관찰 ---")
    # REST API 제한을 낮게 설정하여 쉽게 트리거
    router.rate_limit_manager.configure_limit('upbit_rest_general', 3, 5) # 5초에 3개 요청
    for i in range(1, 10):
        req = MarketDataRequest(data_type='ticker', symbols=['KRW-DOGE'], realtime=False)
        start_time = time.time()
        result = await router.get_data(req)
        end_time = time.time()
        print(f"요청 {i}: 채널 결정 및 응답 수신 (소요 시간: {end_time - start_time:.4f}초)")
        if result:
            print(f"  결과: {result.symbol} - {result.trade_price}")
        await asyncio.sleep(0.1) # 요청 간 짧은 지연
    print("--- 시나리오 종료: 속도 제한 트리거 ---")
    print("-" * 50)

    # --- 시나리오 5: WebSocket 일괄 처리 관찰 ---
    print("\n--- 시나리오 시작: WebSocket 일괄 처리 관찰 ---")
    # BatchSubscriptionManager의 batch_interval_seconds를 짧게 설정하여 효과 확인
    router.websocket_executor.batch_manager.batch_interval_seconds = 0.2

    # 여러 실시간 구독 요청을 빠르게 보냄
    await router.get_data(MarketDataRequest(data_type='realtime_ticker', symbols=['KRW-ADA'], realtime=True))
    await router.get_data(MarketDataRequest(data_type='realtime_ticker', symbols=['KRW-DOT'], realtime=True))
    await router.get_data(MarketDataRequest(data_type='realtime_ticker', symbols=['KRW-SOL'], realtime=True))

    print("실시간 구독 요청을 보냈습니다. 잠시 후 일괄 처리된 메시지가 전송되는 것을 확인하세요.")
    await asyncio.sleep(0.5) # 일괄 처리 메시지 전송 및 시뮬레이션된 데이터 수신 대기
    print("--- 시나리오 종료: WebSocket 일괄 처리 ---")
    print("-" * 50)

    # WebSocket 연결 해제
    await router.disconnect_websocket()
    print("\nSmartRouter 데모 완료.")

if __name__ == "__main__":
    # Windows에서 asyncio.run()이 RuntimeError를 발생시키는 경우를 대비
    # Python 3.8+에서는 기본적으로 ProactorEventLoop가 사용될 수 있습니다.
    # 그러나 일부 환경에서는 SelectorEventLoop가 더 안정적일 수 있습니다.
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            print("경고: 이벤트 루프가 이미 닫혔습니다. 새로운 루프를 생성합니다.")
            policy = asyncio.WindowsSelectorEventLoopPolicy()
            asyncio.set_event_loop_policy(policy)
            asyncio.run(main())
        else:
            raise
