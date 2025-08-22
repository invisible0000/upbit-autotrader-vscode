# d:\projects\upbit-autotrader-vscode\upbit_auto_trading\infrastructure\market_data_backbone\smart_router\executors\rest_executor.py

import asyncio
from typing import Dict, Any, Optional

from smart_router.request import MarketDataRequest
from smart_router.core.rate_limit_manager import RateLimitManager

# TODO: 기존 업비트 REST API 클라이언트에 대한 실제 임포트 경로로 교체하세요.
# from upbit_auto_trading.infrastructure.api.upbit_rest_client import UpbitRestClient
# 현재는 플레이스홀더 클래스를 사용합니다.
class UpbitRestClient:
    def get_market_data(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """실제 REST API 호출을 위한 플레이스홀더입니다."""
        print(f"디버그: UpbitRestClient.get_market_data 호출 중: {endpoint}, 파라미터: {params}")
        # 응답 및 헤더 시뮬레이션
        headers = {'Remaining-Req': '120:119:60'} # 업비트 헤더 예시
        return {"data": f"response_from_rest_{endpoint}", "headers": headers}

    def get_account_info(self) -> Dict[str, Any]:
        """실제 계정 정보 호출을 위한 플레이스홀더입니다."""
        print("디버그: UpbitRestClient.get_account_info 호출 중")
        headers = {'Remaining-Req': '120:119:60'}
        return {"data": "account_info_from_rest", "headers": headers}


class RestExecutor:
    """
    업비트 REST API를 통해 요청을 실행하고, 속도 제한을 준수합니다.
    인프라 계층의 기존 업비트 REST 클라이언트를 활용합니다.
    """
    def __init__(self, rest_client: UpbitRestClient, rate_limit_manager: RateLimitManager):
        self.rest_client = rest_client
        self.rate_limit_manager = rate_limit_manager
        self.rest_api_limit_type = 'upbit_rest_general' # REST 호출을 위한 기본 제한 유형

    async def execute(self, request: MarketDataRequest) -> Dict[str, Any]:
        """
        속도 제한을 확인한 후 REST API 요청을 실행합니다.
        """
        # 이 유형에 대한 속도 제한이 구성되었는지 확인
        if not self.rate_limit_manager._limits.get(self.rest_api_limit_type, {}).get('limit'):
            # 설정되지 않은 경우 기본 제한 구성 (예: 분당 120 요청)
            self.rate_limit_manager.configure_limit(self.rest_api_limit_type, 120, 60)

        # 속도 제한에 걸린 경우 대기
        while not self.rate_limit_manager.allow_request(self.rest_api_limit_type):
            throttle_time = self.rate_limit_manager.get_throttle_time(self.rest_api_limit_type)
            print(f"정보: {self.rest_api_limit_type}에 대한 속도 제한. {throttle_time:.2f}초 대기 중.")
            await asyncio.sleep(throttle_time)

        response = {}
        if request.data_type == 'account_info':
            response = await self.rest_client.get_account_info()
        elif request.data_type == 'ticker':
            # 예시: get_market_data가 티커 스냅샷을 가져올 수 있다고 가정
            endpoint = "/v1/ticker"
            params = {"markets": ",".join(request.symbols)}
            response = await self.rest_client.get_market_data(endpoint, params)
        elif request.data_type == 'candle':
            endpoint = f"/v1/candles/{request.interval}"
            params = {"market": request.symbols[0], "count": request.count} # 캔들의 경우 단일 시장이라고 가정
            response = await self.rest_client.get_market_data(endpoint, params)
        # REST API에 필요한 더 많은 data_type 매핑을 추가합니다.
        else:
            raise ValueError(f"REST에 대해 지원되지 않는 data_type: {request.data_type}")

        # 응답 헤더로 속도 제한 관리자 업데이트
        if 'headers' in response:
            self.rate_limit_manager.update_from_response(self.rest_api_limit_type, response['headers'])
            del response['headers'] # 데이터를 반환하기 전에 헤더 제거

        return response
