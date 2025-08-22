# d:\projects\upbit-autotrader-vscode\tests\infrastructure\smart_router_test\real_api_demo_smart_router.py

import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Callable

# smart_router 모듈 임포트
from smart_router.request import MarketDataRequest
from smart_router.core.metrics_collector import MetricsCollector
from smart_router.core.rate_limit_manager import RateLimitManager
from smart_router.core.adaptive_routing_engine import AdaptiveRoutingEngine
from smart_router.executors.rest_executor import RestExecutor
from smart_router.executors.websocket_executor import WebSocketExecutor
from smart_router.transformers.data_converter import DataConverter
from smart_router.router import SmartRouter, InMemoryCache
from smart_router.models.canonical_ticker import CanonicalTicker
from smart_router.models.canonical_candle import CanonicalCandle

# ==============================================================================
# 사용자 설정: 실제 Upbit API 클라이언트 및 자격 증명
# ==============================================================================

# TODO: 여기에 실제 Upbit API 클라이언트 클래스를 임포트하세요.
# 예시:
# from upbit_auto_trading.infrastructure.api.upbit_rest_client import UpbitRestClient
# from upbit_auto_trading.infrastructure.api.upbit_websocket_client import UpbitWebSocketClient

# 경고: 실제 API 키를 코드에 직접 하드코딩하지 마십시오.
# 환경 변수, 설정 파일 또는 보안 저장소를 사용하세요.
UPBIT_ACCESS_KEY = "YOUR_UPBIT_ACCESS_KEY"  # 실제 액세스 키로 교체하세요.
UPBIT_SECRET_KEY = "YOUR_UPBIT_SECRET_KEY"  # 실제 시크릿 키로 교체하세요.

# TODO: 여기에 실제 Upbit API 클라이언트 인스턴스를 생성하세요.
# 이 클라이언트들은 smart_router/executors/rest_executor.py 및
# smart_router/executors/websocket_executor.py에 있는 플레이스홀더 클래스를 대체합니다.
# 이 클라이언트들은 비동기 메서드(예: get_market_data, get_account_info, connect, send_message)를
# 제공해야 합니다.
# 예시:
# real_rest_client = UpbitRestClient(access_key=UPBIT_ACCESS_KEY, secret_key=UPBIT_SECRET_KEY)
# real_websocket_client = UpbitWebSocketClient(access_key=UPBIT_ACCESS_KEY, secret_key=UPBIT_SECRET_KEY)
#
# 현재는 데모를 위해 임시 플레이스홀더를 사용합니다.
# 사용자는 이 부분을 실제 클라이언트로 교체해야 합니다.
class RealUpbitRestClientPlaceholder:
    async def get_market_data(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[실제REST-플레이스홀더] {endpoint} 호출 시뮬레이션 (실제 클라이언트로 교체 필요)")
        await asyncio.sleep(0.1)
        # 실제 API 응답과 유사하게 Remaining-Req 헤더를 포함해야 합니다.
        return {"data": {"market": "KRW-BTC", "trade_price": 55000000}, "headers": {'Remaining-Req': '120:110:60'}}
    async def get_account_info(self) -> Dict[str, Any]:
        print("[실제REST-플레이스홀더] 계정 정보 호출 시뮬레이션 (실제 클라이언트로 교체 필요)")
        await asyncio.sleep(0.1)
        return {"data": "실제 계정 정보 데이터", "headers": {'Remaining-Req': '10:5:60'}}

class RealUpbitWebSocketClientPlaceholder:
    def __init__(self):
        self._message_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._is_connected = False
    async def connect(self):
        if not self._is_connected:
            print("[실제WS-플레이스홀더] WebSocket 연결 시뮬레이션 (실제 클라이언트로 교체 필요)")
            await asyncio.sleep(0.1)
            self._is_connected = True
    async def disconnect(self):
        if self._is_connected:
            print("[실제WS-플레이스홀더] WebSocket 연결 해제 시뮬레이션 (실제 클라이언트로 교체 필요)")
            await asyncio.sleep(0.05)
            self._is_connected = False
    async def send_message(self, message: str):
        print(f"[실제WS-플레이스홀더] 메시지 전송 시뮬레이션: {message[:50]}... (실제 클라이언트로 교체 필요)")
        await asyncio.sleep(0.01)
        # 실제 WS 클라이언트는 수신된 메시지를 _message_callback으로 전달해야 합니다.
        # 여기서는 간단한 티커 응답을 시뮬레이션합니다.
        try:
            msg_obj = json.loads(message)
            if isinstance(msg_obj, list) and len(msg_obj) > 1:
                for item in msg_obj[1:]:
                    if item.get('type') == 'ticker' and 'codes' in item:
                        for code in item['codes']:
                            simulated_data = {"type": "ticker", "code": code, "trade_price": 50000000, "trade_volume": 1.0}
                            if self._message_callback:
                                asyncio.create_task(self._async_callback(simulated_data))
        except json.JSONDecodeError:
            pass
    def set_message_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self._message_callback = callback
    async def _async_callback(self, data: Dict[str, Any]):
        await asyncio.sleep(0.001)
        self._message_callback(data)

# 실제 클라이언트 인스턴스 (사용자가 교체해야 함)
real_rest_client = RealUpbitRestClientPlaceholder()
real_websocket_client = RealUpbitWebSocketClientPlaceholder()


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
    print("SmartRouter 실제 API 데모 시작...")
    print("경고: 이 데모는 실제 Upbit API 호출을 시도합니다. API 키를 올바르게 설정했는지 확인하세요.")
    print("경고: 실제 API 호출은 속도 제한에 영향을 미치며, 과도한 사용은 계정 제한으로 이어질 수 있습니다.")

    # SmartRouter 초기화 (실제 클라이언트 주입)
    router = SmartRouter(
        rest_client=real_rest_client,
        websocket_client=real_websocket_client,
        metrics_collector=MetricsCollector(),
        rate_limit_manager=RateLimitManager(),
        data_converter=DataConverter(),
        cache=InMemoryCache()
    )

    # WebSocket 연결
    await router.connect_websocket()

    # SmartRouter에서 수신되는 실시간 데이터를 처리하는 콜백 등록
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
    # 이 시나리오가 WebSocket으로 전환되려면, metrics_collector의 임계값을 넘을 만큼
    # 충분히 많은 요청이 발생해야 합니다. 실제 API 호출이므로 속도 제한에 주의하세요.
    for i in range(1, 5): # 실제 API 호출이므로 요청 횟수를 줄입니다.
        req = MarketDataRequest(data_type='ticker', symbols=['KRW-BTC'], realtime=False) # 스냅샷 요청
        start_time = time.time()
        result = await router.get_data(req)
        end_time = time.time()
        print(f"요청 {i}: 채널 결정 및 응답 수신 (소요 시간: {end_time - start_time:.4f}초)")
        if result:
            print(f"  결과: {result.symbol} - {result.trade_price}")
        await asyncio.sleep(0.5) # 실제 API 호출이므로 요청 간 지연을 늘립니다.
    print("--- 시나리오 종료: 빈번한 티커 요청 ---")
    print("-" * 50)

    # --- 시나리오 3: 캔들 데이터 요청 (REST 전용) ---
    await run_demo_scenario(router, "캔들 데이터 요청 (REST 전용)",
                            MarketDataRequest(data_type='candle', symbols=['KRW-XRP'], interval='1m', count=1))

    # --- 시나리오 4: 속도 제한 트리거 및 대기 관찰 ---
    print("\n--- 시나리오 시작: 속도 제한 트리거 및 대기 관찰 ---")
    # 실제 API 호출이므로 속도 제한에 주의하세요.
    # RateLimitManager의 configure_limit은 SmartRouter 초기화 시 설정된 기본값을 사용합니다.
    # 필요하다면 router.rate_limit_manager.configure_limit(...)을 사용하여 재설정할 수 있습니다.
    for i in range(1, 7): # 속도 제한을 트리거할 만큼 충분히 요청
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
    await asyncio.sleep(2) # 일괄 처리 메시지 전송 및 실제 데이터 수신 대기
    print("--- 시나리오 종료: WebSocket 일괄 처리 ---")
    print("-" * 50)

    # WebSocket 연결 해제
    await router.disconnect_websocket()
    print("\nSmartRouter 실제 API 데모 완료.")

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
