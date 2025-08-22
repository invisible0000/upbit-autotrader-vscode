# d:\projects\upbit-autotrader-vscode\upbit_auto_trading\infrastructure\market_data_backbone\smart_router\core\adaptive_routing_engine.py

from typing import Literal
from smart_router.request import MarketDataRequest
from smart_router.core.metrics_collector import MetricsCollector
from smart_router.core.rate_limit_manager import RateLimitManager

class AdaptiveRoutingEngine:
    """
    요청 유형, 빈도 메트릭 및 API 속도 제한을 기반으로
    최적의 통신 채널(REST, WebSocket 또는 캐시)을 결정합니다.
    """
    def __init__(self, metrics_collector: MetricsCollector, rate_limit_manager: RateLimitManager):
        self.metrics_collector = metrics_collector
        self.rate_limit_manager = rate_limit_manager
        # 적응형 라우팅을 위한 임계값 정의 (외부에서 구성 가능)
        self.websocket_frequency_threshold = 0.5 # 초당 요청 수가 이 값 이상이면 WS가 선호됩니다.
        self.rest_api_limit_type = 'upbit_rest_general' # 기본 REST 제한 유형

    def decide_channel(self, request: MarketDataRequest) -> Literal['REST', 'WEBSOCKET', 'CACHE']:
        """
        시장 데이터 요청을 이행하기 위한 최상의 채널을 결정합니다.
        """
        # 1. 캐시 우선 순위 (SmartRouter 파사드에서 처리되지만 여기에 명시하는 것이 좋습니다.)
        # SmartRouter는 이 엔진을 호출하기 전에 캐시를 확인합니다.

        # 2. 독점 채널 처리 (하나의 메서드를 통해서만 사용 가능한 데이터)
        if request.data_type in ['account_info', 'order_history', 'deposit_address']:
            return 'REST' # 이들은 일반적으로 REST 전용입니다.

        if request.data_type in ['realtime_ticker', 'realtime_orderbook', 'realtime_trade']:
            return 'WEBSOCKET' # 이들은 일반적으로 실시간 웹소켓 전용입니다.

        # 3. 중복 데이터 유형에 대한 적응형 선택 (예: 과거 티커, 캔들)
        # REST 및 WebSocket을 통해 가져올 수 있는 데이터 유형의 경우 (예: 매우 최근이거나
        # 해당 WS 연결이 이미 활성화된 경우 WS를 통해 사용 가능한 과거 데이터).
        # 업비트의 경우 대부분의 과거 데이터는 REST이고, 실시간은 WS입니다.
        # 이 섹션은 기술적으로 둘 중 하나가 제공될 수 있는 중복이 있는 경우에 주로 적용됩니다.

        # 예시: 'ticker'가 요청되었고 'realtime'으로 표시되지 않은 경우,
        # REST를 통한 스냅샷이거나 사용 가능한 경우 WS를 통한 최근 스냅샷일 수 있습니다.
        if request.data_type == 'ticker' and not request.realtime:
            # REST API가 현재 속도 제한에 걸렸는지 확인
            if self.rate_limit_manager.get_throttle_time(self.rest_api_limit_type) > 0:
                # REST가 스로틀링되면, 데이터 제공이 가능하다면 WebSocket을 시도합니다.
                # (WebSocket이 최근 스냅샷 티커를 제공할 수 있다고 가정)
                return 'WEBSOCKET'

            # 이 특정 요청 키에 대한 빈도 확인
            request_key = f"{request.data_type}/{'-'.join(request.symbols)}"
            frequency = self.metrics_collector.get_frequency(request_key)

            if frequency >= self.websocket_frequency_threshold:
                return 'WEBSOCKET' # 빈도가 높으면 WebSocket 선호
            else:
                return 'REST' # 빈도가 낮으면 REST 선호

        # 명시적으로 처리되지 않거나 실시간이 아닌 다른 유형의 경우 REST로 기본 설정
        return 'REST'
