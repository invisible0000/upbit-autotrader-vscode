# d:\projects\upbit-autotrader-vscode\upbit_auto_trading\infrastructure\market_data_backbone\smart_router\router.py

import asyncio
from typing import Any, Dict, Union, List, Optional, Callable

from smart_router.request import MarketDataRequest
from smart_router.core.metrics_collector import MetricsCollector
from smart_router.core.rate_limit_manager import RateLimitManager
from smart_router.core.adaptive_routing_engine import AdaptiveRoutingEngine
from smart_router.executors.rest_executor import RestExecutor, UpbitRestClient # UpbitRestClient는 플레이스홀더
from smart_router.executors.websocket_executor import WebSocketExecutor, UpbitWebSocketClient # UpbitWebSocketClient는 플레이스홀더
from smart_router.transformers.data_converter import DataConverter

# TODO: 시연을 위한 간단한 인메모리 캐시 구현.
# 실제 애플리케이션에서는 더 정교한 캐싱 메커니즘이 필요합니다.
class InMemoryCache:
    def __init__(self):
        self._cache: Dict[Any, Any] = {}

    def get(self, key: Any) -> Optional[Any]:
        return self._cache.get(key)

    def set(self, key: Any, value: Any, ttl_seconds: Optional[int] = None):
        # 단순화를 위해 이 기본 캐시에서는 ttl_seconds가 구현되지 않았습니다.
        self._cache[key] = value

    def clear(self):
        self._cache.clear()


class SmartRouter:
    """
    지능형 시장 데이터 라우팅 시스템의 주요 파사드입니다.
    요청을 조정하고, 라우팅 로직을 적용하며, 속도 제한을 관리하고,
    데이터를 표준 형식으로 변환합니다.
    """
    def __init__(self,
                 rest_client: UpbitRestClient, # 주입된 기존 REST 클라이언트
                 websocket_client: UpbitWebSocketClient, # 주입된 기존 WebSocket 클라이언트
                 metrics_collector: Optional[MetricsCollector] = None,
                 rate_limit_manager: Optional[RateLimitManager] = None,
                 data_converter: Optional[DataConverter] = None,
                 cache: Optional[InMemoryCache] = None):

        self.metrics_collector = metrics_collector or MetricsCollector()
        self.rate_limit_manager = rate_limit_manager or RateLimitManager()
        self.adaptive_routing_engine = AdaptiveRoutingEngine(
            self.metrics_collector, self.rate_limit_manager
        )
        self.rest_executor = RestExecutor(rest_client, self.rate_limit_manager)
        self.websocket_executor = WebSocketExecutor(websocket_client)
        self.data_converter = data_converter or DataConverter()
        self.cache = cache or InMemoryCache()

        # 수신되는 실시간 데이터를 처리하고 표준 형식으로 변환하기 위해 WebSocket 데이터 리스너를 등록합니다.
        # 이는 각 데이터 유형에 대해 단일 리스너가 있으며, 이 리스너가 외부 구독자에게
        # 디스패치한다고 가정합니다.
        self.websocket_executor.register_data_listener(
            'realtime_ticker', self._process_realtime_ticker
        )
        # TODO: 다른 실시간 데이터 유형(호가창, 체결)에 대한 리스너 등록

    async def connect_websocket(self):
        """기본 WebSocket 클라이언트를 연결합니다."""
        await self.websocket_executor.connect()

    async def disconnect_websocket(self):
        """기본 WebSocket 클라이언트를 연결 해제합니다."""
        await self.websocket_executor.disconnect()

    async def get_data(self, request: MarketDataRequest) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """
        요청에 따라 최적의 채널을 사용하여 시장 데이터를 검색합니다.
        표준 데이터 모델을 반환합니다.
        """
        # 1. 캐시 확인
        cache_key = hash(request) # 요청 객체의 해시를 캐시 키로 사용
        cached_data = self.cache.get(cache_key)
        if cached_data:
            print(f"정보: 요청에 대한 캐시 적중: {request.data_type} {request.symbols}")
            self.metrics_collector.record_request(str(request), count=0) # 적중 기록, API 호출 없음
            return cached_data

        # 2. 채널 결정
        channel = self.adaptive_routing_engine.decide_channel(request)
        print(f"정보: 요청에 대해 {channel} 채널 사용 결정: {request.data_type} {request.symbols}")

        raw_response = None
        if channel == 'REST':
            raw_response = await self.rest_executor.execute(request)
        elif channel == 'WEBSOCKET':
            # WebSocket 연결이 활성 상태인지 확인하고, 아니면 연결합니다.
            # NOTE: 실제 UpbitWebSocketClient는 연결 상태를 확인하는 메서드를 제공해야 합니다.
            # 현재 플레이스홀더는 이를 지원하지 않으므로, 항상 연결을 시도하거나
            # 연결 상태를 추적하는 내부 플래그를 사용해야 합니다.
            # 여기서는 간단하게 항상 connect를 호출하도록 합니다.
            # 실제 구현에서는 is_connected()와 같은 메서드를 사용해야 합니다.
            await self.websocket_executor.connect() # WebSocket 연결 보장

            # WebSocket의 경우, 구독을 시작합니다. 데이터는 콜백을 통해 수신됩니다.
            # 이 메서드는 실시간 요청에 대해 데이터를 직접 반환하지 않습니다.
            # 웹소켓을 사용할 수 있는 스냅샷 요청의 경우, 웹소켓 실행기는
            # 단일 스냅샷을 반환하는 메커니즘을 구현해야 합니다.
            await self.websocket_executor.execute(request)
            print(f"정보: {request.data_type} {request.symbols}에 대한 WebSocket 구독이 시작되었습니다. 데이터는 리스너를 통해 도착합니다.")
            # 실시간 요청의 경우, 데이터가 스트리밍되므로 여기서는 None을 반환합니다.
            return None
        # 'CACHE' 채널은 시작 부분의 캐시 확인에서 처리됩니다.

        # 3. 표준 형식으로 변환 (REST 응답용)
        canonical_data = None
        if raw_response:
            # raw_response['data']에 실제 데이터 목록/딕셔너리가 포함되어 있다고 가정합니다.
            canonical_data = self.data_converter.convert_to_canonical(
                request.data_type, channel, raw_response.get('data', raw_response)
            )
            # 4. 결과 캐싱 (REST 응답용)
            self.cache.set(cache_key, canonical_data)

        # 5. 메트릭 기록
        self.metrics_collector.record_request(str(request))

        return canonical_data

    def _process_realtime_ticker(self, raw_data: Dict[str, Any]):
        """
        WebSocket에서 수신되는 실시간 티커 데이터를 처리하기 위한 내부 콜백입니다.
        표준 형식으로 변환하고 외부 구독자에게 디스패치할 수 있습니다.
        """
        canonical_ticker = self.data_converter.convert_websocket_ticker_to_canonical(raw_data)
        print(f"정보: 실시간 티커 수신 및 처리: {canonical_ticker.symbol} - {canonical_ticker.trade_price}")
        # TODO: 이 표준 티커를 SmartRouter의 외부 구독자에게 디스패치합니다.
        # 예를 들어, pub-sub 시스템 또는 큐.

    # TODO: 외부 구성 요소가 표준 실시간 데이터를 구독할 수 있도록 메서드 추가
    # def subscribe_to_realtime_data(self, data_type: str, callback: Callable[[Any], None]):
    #     pass # 표준 데이터에 대한 콜백을 등록하는 메커니즘 구현
