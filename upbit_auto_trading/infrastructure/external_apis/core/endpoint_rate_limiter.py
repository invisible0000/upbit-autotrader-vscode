"""
엔드포인트별 세밀한 Rate Limiting 시스템

업비트 공식 문서의 복잡한 Rate Limit 규칙을 지원:
- 전역 제한: 초당 10회 (모든 REST API)
- 그룹별 제한: Quotation(30회/초), Order(8회/초), Order-cancel-all(1회/2초)
- 엔드포인트별 개별 제한
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class UpbitRateLimitGroup(Enum):
    """업비트 API Rate Limit 그룹"""
    GLOBAL = "global"                # 전역 제한: 초당 10회
    QUOTATION = "quotation"          # 시세 조회: 초당 30회
    EXCHANGE_DEFAULT = "exchange_default"  # 거래소 기본: 초당 30회
    ORDER = "order"                  # 주문: 초당 8회
    ORDER_CANCEL_ALL = "order_cancel_all"  # 전체 취소: 2초당 1회
    WEBSOCKET_CONNECT = "websocket_connect"  # WebSocket 연결: 초당 5회
    WEBSOCKET_MESSAGE = "websocket_message"  # WebSocket 메시지: 초당 5회


@dataclass
class RateLimitRule:
    """Rate Limit 규칙"""
    requests_per_second: int
    requests_per_minute: int
    window_seconds: int = 1  # 시간 윈도우 (order-cancel-all은 2초)
    max_requests_per_window: int = 0  # 윈도우당 최대 요청 (0이면 requests_per_second 사용)

    def __post_init__(self):
        if self.max_requests_per_window == 0:
            self.max_requests_per_window = self.requests_per_second * self.window_seconds


@dataclass
class EndpointRateLimitConfig:
    """엔드포인트별 Rate Limit 설정"""
    global_rule: RateLimitRule
    group_rules: Dict[UpbitRateLimitGroup, RateLimitRule]
    endpoint_mappings: Dict[str, UpbitRateLimitGroup] = field(default_factory=dict)

    @classmethod
    def for_upbit(cls) -> 'EndpointRateLimitConfig':
        """업비트 공식 Rate Limit 설정"""
        global_rule = RateLimitRule(
            requests_per_second=10,
            requests_per_minute=600
        )

        group_rules = {
            UpbitRateLimitGroup.GLOBAL: global_rule,
            UpbitRateLimitGroup.QUOTATION: RateLimitRule(
                requests_per_second=30,
                requests_per_minute=1800
            ),
            UpbitRateLimitGroup.EXCHANGE_DEFAULT: RateLimitRule(
                requests_per_second=30,
                requests_per_minute=1800
            ),
            UpbitRateLimitGroup.ORDER: RateLimitRule(
                requests_per_second=8,
                requests_per_minute=480
            ),
            UpbitRateLimitGroup.ORDER_CANCEL_ALL: RateLimitRule(
                requests_per_second=1,
                requests_per_minute=30,
                window_seconds=2,
                max_requests_per_window=1
            ),
            UpbitRateLimitGroup.WEBSOCKET_CONNECT: RateLimitRule(
                requests_per_second=5,
                requests_per_minute=100
            ),
            UpbitRateLimitGroup.WEBSOCKET_MESSAGE: RateLimitRule(
                requests_per_second=5,
                requests_per_minute=100
            )
        }

        # 엔드포인트별 그룹 매핑 (업비트 공식 문서 기준)
        endpoint_mappings = {
            # Quotation 그룹 (시세 조회)
            '/ticker': UpbitRateLimitGroup.QUOTATION,
            '/tickers': UpbitRateLimitGroup.QUOTATION,
            '/orderbook': UpbitRateLimitGroup.QUOTATION,
            '/trades': UpbitRateLimitGroup.QUOTATION,
            '/candles/minutes': UpbitRateLimitGroup.QUOTATION,
            '/candles/days': UpbitRateLimitGroup.QUOTATION,
            '/candles/weeks': UpbitRateLimitGroup.QUOTATION,
            '/candles/months': UpbitRateLimitGroup.QUOTATION,
            '/market/all': UpbitRateLimitGroup.QUOTATION,

            # Exchange Default 그룹 (계좌/자산 조회)
            '/accounts': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
            '/orders/chance': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
            '/orders?': UpbitRateLimitGroup.EXCHANGE_DEFAULT,  # GET 조회용
            '/withdraws': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
            '/deposits': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
            '/deposits/coin_addresses': UpbitRateLimitGroup.EXCHANGE_DEFAULT,

            # Order 그룹 (주문 생성/취소) - 메서드별 구분은 _get_endpoint_group에서 처리

            # Order Cancel All 그룹 (전체 주문 취소)
            '/orders/cancel_all': UpbitRateLimitGroup.ORDER_CANCEL_ALL,
        }

        return cls(
            global_rule=global_rule,
            group_rules=group_rules,
            endpoint_mappings=endpoint_mappings
        )


class EndpointRateLimiter:
    """
    엔드포인트별 세밀한 Rate Limiting

    특징:
    - 전역 제한과 그룹별 제한 동시 적용
    - 엔드포인트별 자동 그룹 매핑
    - HTTP 메서드별 다른 제한 적용 가능
    """

    def __init__(self, config: EndpointRateLimitConfig, client_id: Optional[str] = None):
        self.config = config
        self.client_id = client_id or f"endpoint_limiter_{id(self)}"

        # 전역 제한 추적
        self._global_requests: List[float] = []

        # 그룹별 제한 추적
        self._group_requests: Dict[UpbitRateLimitGroup, List[float]] = {
            group: [] for group in UpbitRateLimitGroup
        }

        # 특별한 윈도우 추적 (order-cancel-all 등)
        self._window_requests: Dict[UpbitRateLimitGroup, List[float]] = {
            group: [] for group in UpbitRateLimitGroup
        }

        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(f"EndpointRateLimiter.{self.client_id}")

    async def acquire(self, endpoint: str, method: str = 'GET') -> None:
        """
        엔드포인트별 Rate Limit 획득

        Args:
            endpoint: API 엔드포인트 (예: '/ticker', '/orders')
            method: HTTP 메서드 (GET, POST, DELETE)
        """
        async with self._lock:
            # 1. 전역 제한 확인
            await self._enforce_global_limit()

            # 2. 엔드포인트별 그룹 제한 확인
            group = self._get_endpoint_group(endpoint, method)
            if group != UpbitRateLimitGroup.GLOBAL:
                await self._enforce_group_limit(group)

            # 3. 요청 기록
            self._record_request(group)

            self._logger.debug(f"Rate limit 획득: {endpoint} [{method}] -> {group.value}")

    def _get_endpoint_group(self, endpoint: str, method: str) -> UpbitRateLimitGroup:
        """엔드포인트와 메서드를 기반으로 Rate Limit 그룹 결정"""
        # 특별 케이스: /orders는 메서드에 따라 다른 그룹
        if endpoint == '/orders':
            if method.upper() in ['POST', 'DELETE']:
                return UpbitRateLimitGroup.ORDER
            else:  # GET
                return UpbitRateLimitGroup.EXCHANGE_DEFAULT

        # 일반적인 매핑
        for pattern, group in self.config.endpoint_mappings.items():
            if endpoint.startswith(pattern):
                return group

        # 기본값: 전역 제한
        return UpbitRateLimitGroup.GLOBAL

    async def _enforce_global_limit(self) -> None:
        """전역 Rate Limit 강제 적용"""
        now = time.time()
        rule = self.config.global_rule

        # 1초 이상 지난 요청 제거
        self._global_requests = [ts for ts in self._global_requests if now - ts < 1]

        if len(self._global_requests) >= rule.requests_per_second:
            wait_time = 1.0 / rule.requests_per_second
            self._logger.warning(f"전역 Rate Limit 대기: {wait_time:.2f}초")
            await asyncio.sleep(wait_time)

    async def _enforce_group_limit(self, group: UpbitRateLimitGroup) -> None:
        """그룹별 Rate Limit 강제 적용"""
        if group not in self.config.group_rules:
            return

        now = time.time()
        rule = self.config.group_rules[group]

        # 윈도우 시간에 따른 요청 제거
        window = rule.window_seconds
        self._group_requests[group] = [
            ts for ts in self._group_requests[group] if now - ts < window
        ]

        if len(self._group_requests[group]) >= rule.max_requests_per_window:
            wait_time = window / rule.max_requests_per_window
            self._logger.warning(
                f"{group.value} Rate Limit 대기: {wait_time:.2f}초 "
                f"({len(self._group_requests[group])}/{rule.max_requests_per_window})"
            )
            await asyncio.sleep(wait_time)

    def _record_request(self, group: UpbitRateLimitGroup) -> None:
        """요청 기록"""
        now = time.time()

        # 전역 요청 기록
        self._global_requests.append(now)

        # 그룹별 요청 기록
        if group in self._group_requests:
            self._group_requests[group].append(now)

    def get_status(self) -> Dict[str, Any]:
        """현재 Rate Limit 상태 조회"""
        now = time.time()

        # 전역 상태
        global_count = len([ts for ts in self._global_requests if now - ts < 1])

        # 그룹별 상태
        group_status = {}
        for group, requests in self._group_requests.items():
            if group in self.config.group_rules:
                rule = self.config.group_rules[group]
                window_count = len([ts for ts in requests if now - ts < rule.window_seconds])
                group_status[group.value] = {
                    'current': window_count,
                    'limit': rule.max_requests_per_window,
                    'window_seconds': rule.window_seconds
                }

        return {
            'client_id': self.client_id,
            'global': {
                'current': global_count,
                'limit': self.config.global_rule.requests_per_second
            },
            'groups': group_status,
            'endpoint_mappings': {k: v.value for k, v in self.config.endpoint_mappings.items()}
        }


# 팩토리 함수
def create_upbit_endpoint_limiter(client_id: Optional[str] = None) -> EndpointRateLimiter:
    """업비트용 엔드포인트 Rate Limiter 생성"""
    config = EndpointRateLimitConfig.for_upbit()
    return EndpointRateLimiter(config, client_id)
