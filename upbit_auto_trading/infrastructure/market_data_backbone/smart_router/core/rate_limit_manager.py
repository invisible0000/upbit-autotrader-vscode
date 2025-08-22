# d:\projects\upbit-autotrader-vscode\upbit_auto_trading\infrastructure\market_data_backbone\smart_router\core\rate_limit_manager.py

import time
from collections import defaultdict
from typing import Dict, Optional, Any

class RateLimitManager:
    """
    다양한 요청 유형 또는 엔드포인트에 대한 API 속도 제한을 관리합니다.
    고정 창 및 누출 버킷(간소화된) 접근 방식을 모두 지원합니다.
    """
    def __init__(self):
        # 각 제한 유형에 대한 마지막 요청 시간과 카운트를 저장합니다.
        # 키: limit_type (예: 'rest_general', 'rest_order_placement')
        # 값: {'last_reset_time': float, 'current_requests': int, 'limit': int, 'window_seconds': int}
        self._limits: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'last_reset_time': 0.0,
            'current_requests': 0,
            'limit': 0, # 최대 요청 수
            'window_seconds': 0 # 시간 창 (초)
        })
        self._throttled_until: Dict[str, float] = defaultdict(float) # 제한 유형이 스로틀링되는 시점

    def configure_limit(self, limit_type: str, limit: int, window_seconds: int):
        """
        특정 요청 유형에 대한 속도 제한을 구성합니다.
        :param limit_type: 제한에 대한 고유 식별자 (예: 'rest_public', 'rest_private').
        :param limit: 창 내에서 허용되는 최대 요청 수.
        :param window_seconds: 시간 창 (초).
        """
        self._limits[limit_type].update({
            'limit': limit,
            'window_seconds': window_seconds,
            'last_reset_time': time.time() # 마지막 재설정 시간 초기화
        })

    def update_from_response(self, limit_type: str, headers: Dict[str, str]):
        """
        응답 헤더(예: 업비트의 Remaining-Req)를 기반으로 속도 제한 상태를 업데이트합니다.
        :param limit_type: 업데이트할 제한 유형.
        :param headers: 응답 헤더 딕셔너리.
        """
        # 업비트 예시: 'Remaining-Req': '120:10' (제한:남은) 또는 '120:10:30' (제한:남은:재설정_초)
        remaining_req = headers.get('Remaining-Req')
        if remaining_req:
            parts = remaining_req.split(':')
            if len(parts) >= 2:
                try:
                    # 업비트의 Remaining-Req 형식은 종종 'limit:remaining' 또는 'limit:remaining:reset_seconds'입니다.
                    # 우리는 제한에 가까운지 알기 위해 'remaining' 부분에 관심이 있으며,
                    # 사용 가능한 경우 'reset_seconds'에도 관심이 있습니다.
                    current_limit = int(parts[0])
                    current_remaining = int(parts[1])

                    # reset_seconds가 제공되면 다음 재설정 시간을 계산하는 데 사용합니다.
                    reset_seconds = int(parts[2]) if len(parts) == 3 else None

                    # 서버의 현재 보기를 기반으로 내부 상태를 업데이트합니다.
                    limit_info = self._limits[limit_type]
                    limit_info['limit'] = current_limit # 서버에서 보고한 실제 제한으로 업데이트
                    limit_info['current_requests'] = current_limit - current_remaining # 서버에서 보고한 남은 요청 수로 현재 요청 수 계산

                    if reset_seconds is not None:
                        # 서버에서 제공한 재설정 시간을 기반으로 last_reset_time을 계산합니다.
                        # 이는 window_seconds가 서버의 실제 창과 다를 수 있기 때문에 중요합니다.
                        limit_info['last_reset_time'] = time.time() + reset_seconds - limit_info['window_seconds']
                    else:
                        # reset_seconds가 없으면 고정 창으로 가정하고 창이 지나면 재설정합니다.
                        if time.time() - limit_info['last_reset_time'] >= limit_info['window_seconds']:
                            limit_info['current_requests'] = 0
                            limit_info['last_reset_time'] = time.time()

                except ValueError:
                    # 헤더 값이 예상과 다른 경우 처리
                    pass

    def allow_request(self, limit_type: str, cost: int = 1) -> bool:
        """
        구성된 제한 내에서 요청이 허용되는지 확인합니다.
        허용되지 않으면 암시적으로 스로틀링하거나 False를 반환할 수 있습니다.
        :param limit_type: 확인할 제한 유형.
        :param cost: 현재 요청의 비용 (기본값 1).
        :return: 요청이 허용되면 True, 그렇지 않으면 False.
        """
        limit_info = self._limits[limit_type]
        if not limit_info['limit']: # 제한이 구성되지 않음
            return True

        current_time = time.time()

        # 현재 스로틀링 중인지 확인
        if current_time < self._throttled_until[limit_type]:
            return False

        # 시간이 지나면 창 재설정
        if current_time - limit_info['last_reset_time'] >= limit_info['window_seconds']:
            limit_info['current_requests'] = 0
            limit_info['last_reset_time'] = current_time

        if limit_info['current_requests'] + cost <= limit_info['limit']:
            limit_info['current_requests'] += cost
            return True
        else:
            # 허용되지 않으면 스로틀 기간 설정
            self._throttled_until[limit_type] = current_time + limit_info['window_seconds'] - (current_time - limit_info['last_reset_time']) + 0.1 # 작은 버퍼 추가
            return False

    def get_throttle_time(self, limit_type: str) -> float:
        """
        이 제한 유형에 대해 다음 요청이 허용될 때까지의 시간(초)을 반환합니다.
        활성 스로틀링이 없으면 0을 반환합니다.
        """
        current_time = time.time()
        throttle_end_time = self._throttled_until[limit_type]
        if current_time < throttle_end_time:
            return throttle_end_time - current_time
        return 0.0

    def reset_all_limits(self):
        """추적되는 모든 속도 제한을 재설정합니다."""
        current_time = time.time()
        for limit_type in self._limits:
            self._limits[limit_type]['current_requests'] = 0
            self._limits[limit_type]['last_reset_time'] = current_time
            self._throttled_until[limit_type] = 0.0
