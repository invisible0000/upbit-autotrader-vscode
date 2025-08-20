"""
레이트 리미터 - Upbit API 제한 준수

기능:
1. REST API: 8-30 req/s 제한 (80% 안전 마진)
2. WebSocket: 5 req/s 제한 (80% 안전 마진)
3. 동적 제한 조정 (에러 응답 시)
4. 백오프 로직
"""

import time
from typing import Dict, Any

from upbit_auto_trading.infrastructure.logging import create_component_logger


class RateLimitGuard:
    """레이트 제한 가드 (Upbit API 보호)"""

    def __init__(self):
        # 80% 안전 마진 적용한 기본 제한
        self.rest_limit = 6.4  # 8 * 0.8
        self.websocket_limit = 4.0  # 5 * 0.8

        # 요청 추적
        self.rest_requests = []
        self.websocket_requests = []

        # 백오프 상태
        self.backoff_until = None
        self.backoff_level = 0

        self._logger = create_component_logger("RateLimitGuard")

    def can_make_request(self, is_websocket: bool = False) -> bool:
        """요청 가능 여부 확인"""
        now = time.time()

        # 백오프 중인지 확인
        if self.backoff_until and now < self.backoff_until:
            return False

        # 1초 창에서 요청 수 확인
        requests = self.websocket_requests if is_websocket else self.rest_requests
        limit = self.websocket_limit if is_websocket else self.rest_limit

        # 1초 이내 요청만 유지
        requests[:] = [req_time for req_time in requests if now - req_time < 1.0]

        return len(requests) < limit

    def record_request(self, is_websocket: bool = False) -> None:
        """요청 기록"""
        now = time.time()

        if is_websocket:
            self.websocket_requests.append(now)
        else:
            self.rest_requests.append(now)

    def handle_rate_limit_error(self) -> None:
        """레이트 제한 에러 처리 (백오프)"""
        self.backoff_level = min(self.backoff_level + 1, 5)
        backoff_time = 2 ** self.backoff_level  # 2, 4, 8, 16, 32초

        self.backoff_until = time.time() + backoff_time
        self._logger.warning(f"레이트 제한 에러 - {backoff_time}초 백오프")

    def reset_backoff(self) -> None:
        """백오프 리셋 (성공 후)"""
        if self.backoff_level > 0:
            self._logger.info("백오프 리셋 - 정상 요청 재개")
            self.backoff_level = 0
            self.backoff_until = None

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 정보"""
        now = time.time()

        # 최근 1초 요청 수
        rest_recent = len([t for t in self.rest_requests if now - t < 1.0])
        ws_recent = len([t for t in self.websocket_requests if now - t < 1.0])

        return {
            "rest_usage": f"{rest_recent}/{self.rest_limit}",
            "websocket_usage": f"{ws_recent}/{self.websocket_limit}",
            "backoff_active": self.backoff_until and now < self.backoff_until,
            "backoff_remaining": max(0, self.backoff_until - now) if self.backoff_until else 0,
            "can_request_rest": self.can_make_request(False),
            "can_request_websocket": self.can_make_request(True)
        }
