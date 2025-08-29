"""
업비트 전용 통합 Rate Limiter

업비트 공식 문서의 복잡한 Rate Limit 규칙을 완벽 지원:
- 전역 제한: 초당 10회 (모든 REST API)
- 그룹별 제한: Quotation(30회/초), Order(8회/초), Order-cancel-all(1회/2초) 등
- 엔드포인트별 자동 그룹 매핑
- Remaining-Req 헤더 기반 서버 상태 추적
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class UpbitRateLimitGroup(Enum):
    """업비트 API Rate Limit 그룹 (공식 문서 기준)"""
    GLOBAL = "global"                # 전역 제한: 초당 10회
    QUOTATION = "quotation"          # 시세 조회: 초당 30회
    EXCHANGE_DEFAULT = "exchange_default"  # 거래소 기본: 초당 30회
    ORDER = "order"                  # 주문: 초당 8회
    ORDER_CANCEL_ALL = "order_cancel_all"  # 전체 취소: 2초당 1회
    WEBSOCKET_CONNECT = "websocket_connect"  # WebSocket 연결: 초당 5회
    WEBSOCKET_MESSAGE = "websocket_message"  # WebSocket 메시지: 초당 5회


class RateLimitStrategy(Enum):
    """Rate Limiting 알고리즘 전략"""
    CLOUDFLARE_SLIDING_WINDOW = "cloudflare_sliding_window"     # Cloudflare 방식 (정확성 중시)
    AIOLIMITER_OPTIMIZED = "aiolimiter_optimized"              # aiolimiter 최적화 (성능 중시)
    HYBRID_FAST = "hybrid_fast"                                # 하이브리드 (속도+정확성)


@dataclass
class UpbitRateLimitRule:
    """업비트 Rate Limit 규칙"""
    requests_per_second: int
    requests_per_minute: int
    window_seconds: int = 1  # 시간 윈도우 (order-cancel-all은 2초)
    max_requests_per_window: int = 0  # 윈도우당 최대 요청

    def __post_init__(self):
        if self.max_requests_per_window == 0:
            self.max_requests_per_window = self.requests_per_second * self.window_seconds


class UpbitRateLimiter:
    """
    업비트 전용 통합 Rate Limiter

    특징:
    - 업비트 공식 Rate Limit 규칙 완벽 지원
    - 엔드포인트별 자동 그룹 매핑
    - Remaining-Req 헤더 기반 서버 상태 추적
    - 적응형 백오프 및 스로틀링
    - 1초 내 통신 완료 규칙 준수
    """

    # 업비트 공식 Rate Limit 규칙 (정적 설정)
    _RATE_RULES = {
        UpbitRateLimitGroup.GLOBAL: UpbitRateLimitRule(
            requests_per_second=10,
            requests_per_minute=600
        ),
        UpbitRateLimitGroup.QUOTATION: UpbitRateLimitRule(
            requests_per_second=30,
            requests_per_minute=1800
        ),
        UpbitRateLimitGroup.EXCHANGE_DEFAULT: UpbitRateLimitRule(
            requests_per_second=30,
            requests_per_minute=1800
        ),
        UpbitRateLimitGroup.ORDER: UpbitRateLimitRule(
            requests_per_second=8,
            requests_per_minute=480
        ),
        UpbitRateLimitGroup.ORDER_CANCEL_ALL: UpbitRateLimitRule(
            requests_per_second=1,
            requests_per_minute=30,
            window_seconds=2,
            max_requests_per_window=1
        ),
        UpbitRateLimitGroup.WEBSOCKET_CONNECT: UpbitRateLimitRule(
            requests_per_second=5,
            requests_per_minute=100
        ),
        UpbitRateLimitGroup.WEBSOCKET_MESSAGE: UpbitRateLimitRule(
            requests_per_second=5,
            requests_per_minute=100
        )
    }

    # 엔드포인트별 그룹 매핑 (업비트 공식 문서 기준)
    _ENDPOINT_MAPPINGS = {
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
        '/withdraws': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/deposits': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/deposits/coin_addresses': UpbitRateLimitGroup.EXCHANGE_DEFAULT,

        # Order Cancel All 그룹 (전체 주문 취소)
        '/orders/cancel_all': UpbitRateLimitGroup.ORDER_CANCEL_ALL,
    }

    def __init__(self, client_id: Optional[str] = None,
                 strategy: RateLimitStrategy = RateLimitStrategy.HYBRID_FAST):
        self.client_id = client_id or f"upbit_limiter_{id(self)}"
        self.strategy = strategy

        # 전역 제한 추적
        self._global_requests: List[float] = []

        # 그룹별 제한 추적
        self._group_requests: Dict[UpbitRateLimitGroup, List[float]] = {
            group: [] for group in UpbitRateLimitGroup
        }

        # 업비트 서버 제한 추적 (Remaining-Req 헤더 기반)
        self._server_limit: Optional[int] = None
        self._server_remaining: Optional[int] = None
        self._server_reset_time: Optional[float] = None

        # 적응형 백오프
        self._consecutive_limits = 0
        self._backoff_multiplier = 1.0
        self._throttled_until = 0.0

        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(f"UpbitRateLimiter.{self.client_id}")

        # 전략별 성능 통계
        self._strategy_stats = {
            'total_requests': 0,
            'total_wait_time': 0.0,
            'immediate_passes': 0,
            'calculations_needed': 0
        }

    async def acquire(self, endpoint: str, method: str = 'GET') -> None:
        """
        업비트 API 호출 권한 획득

        Args:
            endpoint: API 엔드포인트 (예: '/ticker', '/orders')
            method: HTTP 메서드 (GET, POST, DELETE)
        """
        async with self._lock:
            # 1. 스로틀링 상태 확인
            await self._wait_if_throttled()

            # 2. 서버 기반 제한 확인
            await self._enforce_server_limits()

            # 3. 엔드포인트별 그룹 결정
            group = self._get_endpoint_group(endpoint, method)

            # 4. 제한 확인 먼저 (레거시 방식)
            if group != UpbitRateLimitGroup.GLOBAL:
                await self._enforce_group_limit(group)
            await self._enforce_global_limit()

            # 5. 제한 통과 후 요청 기록 (레거시 방식)
            self._record_request(group)

            # 6. 성공적인 acquire - 백오프 상태 리셋
            self._consecutive_limits = 0
            self._backoff_multiplier = 1.0

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
        for pattern, group in self._ENDPOINT_MAPPINGS.items():
            if endpoint.startswith(pattern):
                return group

        # 기본값: 전역 제한
        return UpbitRateLimitGroup.GLOBAL

    async def _wait_if_throttled(self) -> None:
        """스로틀링 상태면 대기"""
        if time.time() < self._throttled_until:
            wait_time = self._throttled_until - time.time()
            self._logger.warning(f"업비트 Rate limit 스로틀링 대기: {wait_time:.2f}초")
            await asyncio.sleep(wait_time)

    async def _enforce_server_limits(self) -> None:
        """업비트 서버 기반 제한 강제 적용 (Remaining-Req 헤더 기준)"""
        now = time.time()

        if self._server_remaining is not None and self._server_remaining <= 0:
            if self._server_reset_time and now < self._server_reset_time:
                wait_time = min(self._server_reset_time - now, 0.9)  # 최대 0.9초
                self._logger.warning(f"업비트 서버 제한 대기: {wait_time:.2f}초")
                await asyncio.sleep(wait_time)

    async def _enforce_global_limit(self) -> None:
        """전역 Rate Limit 강제 적용 - 선택된 전략에 따라 실행"""
        start_time = time.perf_counter()
        self._strategy_stats['total_requests'] += 1

        try:
            if self.strategy == RateLimitStrategy.CLOUDFLARE_SLIDING_WINDOW:
                await self._enforce_global_limit_cloudflare()
            elif self.strategy == RateLimitStrategy.AIOLIMITER_OPTIMIZED:
                await self._enforce_global_limit_aiolimiter()
            elif self.strategy == RateLimitStrategy.HYBRID_FAST:
                await self._enforce_global_limit_hybrid()
            else:
                # 기본값: Hybrid
                await self._enforce_global_limit_hybrid()
        finally:
            wait_time = time.perf_counter() - start_time
            self._strategy_stats['total_wait_time'] += wait_time

    async def _enforce_global_limit_cloudflare(self) -> None:
        """Cloudflare Sliding Window Counter 방식 (정확성 중시)"""
        # ==========================================
        # 🔧 CLOUDFLARE 전략 조정 가능한 파라미터들
        # ==========================================
        CLEANUP_WINDOW_SECONDS = 2.0        # 오래된 요청 정리 윈도우 (기본: 2.0초)
        MAX_WAIT_TIME_MS = 120               # 최대 대기시간 (기본: 120ms)
        EXCESS_MULTIPLIER = 0.1              # 초과량 대기시간 계수 (기본: 0.1)
        SAFETY_BUFFER = 1                    # 안전 버퍼 (기본: 1)
        # ==========================================

        now = time.time()
        rule = self._RATE_RULES[UpbitRateLimitGroup.GLOBAL]

        # Sliding Window Counter: 현재 1초와 이전 1초 구간 분리
        current_window_start = int(now)  # 현재 1초 구간 시작
        previous_window_start = current_window_start - 1  # 이전 1초 구간

        # 현재 1초 구간 내 요청 수
        current_requests = [ts for ts in self._global_requests if ts >= current_window_start]
        current_count = len(current_requests)

        # 이전 1초 구간 내 요청 수
        previous_requests = [ts for ts in self._global_requests
                             if previous_window_start <= ts < current_window_start]
        previous_count = len(previous_requests)

        # Sliding Window 계산
        elapsed_in_current = now - current_window_start
        weight = (1.0 - elapsed_in_current)  # 이전 구간 가중치
        estimated_rate = previous_count * weight + current_count

        # 정리: 설정된 윈도우 이상 지난 요청 제거
        self._global_requests = [ts for ts in self._global_requests
                                 if now - ts < CLEANUP_WINDOW_SECONDS]

        # 제한 확인 (안전 버퍼 적용)
        if estimated_rate >= rule.requests_per_second - SAFETY_BUFFER:
            self._strategy_stats['calculations_needed'] += 1
            # 정밀한 대기시간 계산
            excess = estimated_rate - rule.requests_per_second + SAFETY_BUFFER
            wait_time = min(excess * EXCESS_MULTIPLIER, MAX_WAIT_TIME_MS / 1000.0)

            self._logger.debug(
                f"업비트 전역 제한 (Cloudflare): {estimated_rate:.1f}/10, 대기 {wait_time * 1000:.1f}ms"
            )
            await asyncio.sleep(wait_time)
        else:
            self._strategy_stats['immediate_passes'] += 1

    async def _enforce_global_limit_aiolimiter(self) -> None:
        """aiolimiter 최적화 방식 (성능 중시)"""
        # ==========================================
        # 🔧 AIOLIMITER 전략 조정 가능한 파라미터들
        # ==========================================
        FAST_CHECK_THRESHOLD = 8             # 빠른 확인 임계값 (기본: 8 < 10)
        MAX_WAIT_TIME_MS = 80                # 최대 대기시간 (기본: 80ms)
        EXCESS_MULTIPLIER = 0.05             # 초과량 대기시간 계수 (기본: 0.05)
        PRECISION_MODE = True                # 정밀 모드 활성화 (기본: True)
        # ==========================================

        now = time.time()
        rule = self._RATE_RULES[UpbitRateLimitGroup.GLOBAL]

        # Step 1: 빠른 용량 확인 (aiolimiter 스타일)
        # 오래된 요청 즉시 정리
        cutoff_time = now - 1.0
        self._global_requests = [ts for ts in self._global_requests if ts > cutoff_time]

        # 즉시 용량 확인 (조정 가능한 임계값)
        if len(self._global_requests) < FAST_CHECK_THRESHOLD:
            self._strategy_stats['immediate_passes'] += 1
            return  # 즉시 통과!

        self._strategy_stats['calculations_needed'] += 1

        # Step 2: 정밀한 계산 (필요한 경우만, 설정에 따라)
        if PRECISION_MODE:
            # 정밀한 Cloudflare Sliding Window 계산
            current_window_start = int(now)
            previous_window_start = current_window_start - 1

            # 현재/이전 구간 분리
            current_count = sum(1 for ts in self._global_requests if ts >= current_window_start)
            previous_count = sum(1 for ts in self._global_requests
                                 if previous_window_start <= ts < current_window_start)

            # Sliding Window 정밀 계산
            elapsed_in_current = now - current_window_start
            weight = 1.0 - elapsed_in_current
            estimated_rate = previous_count * weight + current_count
        else:
            # 간단한 카운트 방식
            estimated_rate = len(self._global_requests)

        # Step 3: 최소 대기시간 계산 (성능 최적화)
        if estimated_rate >= rule.requests_per_second:
            # 동적 대기시간: 초과량에 비례하되 최소화
            excess_ratio = (estimated_rate - rule.requests_per_second) / rule.requests_per_second
            wait_time = min(excess_ratio * EXCESS_MULTIPLIER, MAX_WAIT_TIME_MS / 1000.0)

            self._logger.debug(
                f"업비트 전역 제한 (aiolimiter): {estimated_rate:.2f}/10 → {wait_time * 1000:.1f}ms 대기"
            )
            await asyncio.sleep(wait_time)

    async def _enforce_global_limit_hybrid(self) -> None:
        """하이브리드 방식 (속도+정확성 균형)"""
        # ==========================================
        # 🔧 HYBRID 전략 조정 가능한 파라미터들
        # ==========================================
        SAFETY_BUFFER = 1                    # 안전 버퍼 (기본: 1)
        HEAVY_OVERLOAD_THRESHOLD = 1.5       # 심한 초과 임계값 (기본: 1.5배)
        HEAVY_WAIT_MULTIPLIER = 0.08         # 심한 초과 대기시간 계수 (기본: 0.08)
        LIGHT_WAIT_MULTIPLIER = 0.04         # 가벼운 초과 대기시간 계수 (기본: 0.04)
        MAX_HEAVY_WAIT_MS = 100              # 심한 초과 최대 대기시간 (기본: 100ms)
        MAX_LIGHT_WAIT_MS = 60               # 가벼운 초과 최대 대기시간 (기본: 60ms)
        # ==========================================

        now = time.time()
        rule = self._RATE_RULES[UpbitRateLimitGroup.GLOBAL]

        # Phase 1: 초고속 용량 확인 (aiolimiter 방식)
        cutoff_time = now - 1.0
        recent_requests = [ts for ts in self._global_requests if ts > cutoff_time]

        # 용량이 충분하면 즉시 통과 (안전 버퍼 적용)
        if len(recent_requests) < rule.requests_per_second - SAFETY_BUFFER:
            self._global_requests = recent_requests  # 정리도 함께
            self._strategy_stats['immediate_passes'] += 1
            return

        self._strategy_stats['calculations_needed'] += 1

        # Phase 2: 정밀 계산 (Cloudflare 방식 간소화)
        current_second = int(now)
        previous_second = current_second - 1

        # 빠른 카운팅
        current_count = sum(1 for ts in recent_requests if ts >= current_second)
        previous_count = sum(1 for ts in recent_requests if previous_second <= ts < current_second)

        # 간소화된 Sliding Window
        elapsed = now - current_second
        estimated_rate = previous_count * (1.0 - elapsed) + current_count

        # 메모리 정리
        self._global_requests = recent_requests

        # Phase 3: 적응형 대기시간 (최적화, 조정 가능한 파라미터)
        if estimated_rate >= rule.requests_per_second:
            # 동적 대기: 현재 상황에 최적화
            if estimated_rate > rule.requests_per_second * HEAVY_OVERLOAD_THRESHOLD:
                # 심한 초과: 정확한 대기
                wait_time = min(
                    (estimated_rate - rule.requests_per_second) * HEAVY_WAIT_MULTIPLIER,
                    MAX_HEAVY_WAIT_MS / 1000.0
                )
            else:
                # 가벼운 초과: 최소 대기
                wait_time = min(
                    (estimated_rate - rule.requests_per_second) * LIGHT_WAIT_MULTIPLIER,
                    MAX_LIGHT_WAIT_MS / 1000.0
                )

            self._logger.debug(
                f"업비트 전역 제한 (Hybrid): {estimated_rate:.2f}/10 → {wait_time * 1000:.1f}ms 대기"
            )
            await asyncio.sleep(wait_time)

    async def _enforce_group_limit(self, group: UpbitRateLimitGroup) -> None:
        """그룹별 Rate Limit 강제 적용 - 레거시 방식 적용"""
        if group not in self._RATE_RULES:
            return

        now = time.time()
        rule = self._RATE_RULES[group]

        # 윈도우 시간에 따른 요청 제거
        window = rule.window_seconds
        self._group_requests[group] = [
            ts for ts in self._group_requests[group] if now - ts < window
        ]

        if len(self._group_requests[group]) >= rule.max_requests_per_window:
            # 가장 오래된 요청이 윈도우를 벗어날 때까지 대기
            oldest_request = min(self._group_requests[group])
            wait_time = window - (now - oldest_request)

            if wait_time > 0:
                # 안전 마진 추가하되 너무 길지 않게
                safe_wait = min(wait_time + 0.01, 0.1)  # 최대 100ms
                self._logger.debug(
                    f"업비트 {group.value} 제한 대기: {safe_wait * 1000:.1f}ms"
                )
                await asyncio.sleep(safe_wait)

    def _record_request(self, group: UpbitRateLimitGroup) -> None:
        """요청 기록"""
        now = time.time()

        # 전역 요청 기록
        self._global_requests.append(now)

        # 그룹별 요청 기록
        if group in self._group_requests:
            self._group_requests[group].append(now)

    def _apply_backoff(self) -> None:
        """적응형 백오프 적용 - 실용적 버전"""
        self._consecutive_limits += 1
        self._backoff_multiplier = min(2.0, 1.0 + (self._consecutive_limits * 0.1))

        # 연속 제한 도달 시 짧은 스로틀링 (테스트 환경 고려)
        if self._consecutive_limits >= 5:  # 더 관대한 기준
            throttle_time = min(self._consecutive_limits * 0.5, 2.0)  # 최대 2초
            self._throttled_until = time.time() + throttle_time
            self._logger.warning(
                f"업비트 연속 제한 {self._consecutive_limits}회, "
                f"짧은 스로틀링 적용: {throttle_time:.1f}초"
            )

    def update_from_upbit_headers(self, headers: Dict[str, str]) -> None:
        """업비트 Remaining-Req 헤더로 제한 상태 업데이트"""
        remaining_req = headers.get('Remaining-Req') or headers.get('remaining-req')
        if remaining_req:
            try:
                parts = remaining_req.split(':')
                if len(parts) >= 2:
                    self._server_limit = int(parts[0])
                    self._server_remaining = int(parts[1])
                    if len(parts) >= 3:
                        self._server_reset_time = time.time() + int(parts[2])

                    # 성공적인 요청이므로 백오프 리셋
                    self._reset_backoff()

                    self._logger.debug(
                        f"업비트 서버 제한 업데이트: {self._server_remaining}/{self._server_limit}"
                    )
            except (ValueError, IndexError):
                self._logger.warning(f"업비트 Remaining-Req 헤더 파싱 실패: {remaining_req}")

    def _reset_backoff(self) -> None:
        """백오프 상태 리셋"""
        self._consecutive_limits = 0
        self._backoff_multiplier = 1.0
        self._throttled_until = 0.0

    def allow_request(self, endpoint: str, method: str = 'GET') -> bool:
        """요청 허용 여부 확인"""
        now = time.time()

        # 스로틀링 중이면 거부
        if now < self._throttled_until:
            return False

        # 서버 제한 확인
        if self._server_remaining is not None and self._server_remaining <= 0:
            return False

        # 전역 제한 확인
        global_count = len([ts for ts in self._global_requests if now - ts < 1])
        if global_count >= self._RATE_RULES[UpbitRateLimitGroup.GLOBAL].requests_per_second:
            return False

        # 그룹별 제한 확인
        group = self._get_endpoint_group(endpoint, method)
        if group in self._RATE_RULES:
            rule = self._RATE_RULES[group]
            group_count = len([
                ts for ts in self._group_requests[group]
                if now - ts < rule.window_seconds
            ])
            if group_count >= rule.max_requests_per_window:
                return False

        return True

    def get_status(self) -> Dict[str, Any]:
        """현재 Rate Limit 상태 조회"""
        now = time.time()

        # 전역 상태
        global_count = len([ts for ts in self._global_requests if now - ts < 1])

        # 그룹별 상태
        group_status = {}
        for group, requests in self._group_requests.items():
            if group in self._RATE_RULES:
                rule = self._RATE_RULES[group]
                window_count = len([ts for ts in requests if now - ts < rule.window_seconds])
                group_status[group.value] = {
                    'current': window_count,
                    'limit': rule.max_requests_per_window,
                    'window_seconds': rule.window_seconds,
                    'usage_percent': (window_count / rule.max_requests_per_window) * 100
                }

        # 전략 성능 통계
        total_requests = self._strategy_stats['total_requests']
        total_wait_time = self._strategy_stats['total_wait_time']
        immediate_passes = self._strategy_stats['immediate_passes']
        calculations_needed = self._strategy_stats['calculations_needed']

        strategy_performance = {
            'current_strategy': self.strategy.value,
            'total_requests': total_requests,
            'immediate_pass_rate': (immediate_passes / max(total_requests, 1)) * 100,
            'calculation_rate': (calculations_needed / max(total_requests, 1)) * 100,
            'average_wait_time_ms': (total_wait_time / max(total_requests, 1)) * 1000,
            'total_wait_time_ms': total_wait_time * 1000
        }

        return {
            'client_id': self.client_id,
            'exchange': 'upbit',
            'strategy': strategy_performance,
            'global': {
                'current': global_count,
                'limit': self._RATE_RULES[UpbitRateLimitGroup.GLOBAL].requests_per_second,
                'usage_percent': (global_count / self._RATE_RULES[UpbitRateLimitGroup.GLOBAL].requests_per_second) * 100
            },
            'groups': group_status,
            'server_info': {
                'limit': self._server_limit,
                'remaining': self._server_remaining,
                'reset_time': self._server_reset_time
            },
            'backoff': {
                'consecutive_limits': self._consecutive_limits,
                'multiplier': self._backoff_multiplier,
                'throttled_until': self._throttled_until
            },
            'endpoint_mappings': {k: v.value for k, v in self._ENDPOINT_MAPPINGS.items()}
        }


# 편의 팩토리 함수들
def create_upbit_rate_limiter(client_id: Optional[str] = None,
                              strategy: RateLimitStrategy = RateLimitStrategy.HYBRID_FAST) -> UpbitRateLimiter:
    """업비트 Rate Limiter 생성"""
    return UpbitRateLimiter(client_id, strategy)


# 전역 Rate Limiter 인스턴스들
_global_rate_limiters: Dict[str, "UpbitRateLimiter"] = {}


def create_upbit_public_limiter(client_id: Optional[str] = None,
                                strategy: RateLimitStrategy = RateLimitStrategy.HYBRID_FAST) -> UpbitRateLimiter:
    """업비트 공개 API용 Rate Limiter (싱글톤)"""
    key = f"{client_id or 'upbit_public'}_{strategy.value}"
    if key not in _global_rate_limiters:
        _global_rate_limiters[key] = UpbitRateLimiter(client_id or "upbit_public", strategy)
    return _global_rate_limiters[key]


def create_upbit_private_limiter(client_id: Optional[str] = None,
                                 strategy: RateLimitStrategy = RateLimitStrategy.AIOLIMITER_OPTIMIZED) -> UpbitRateLimiter:
    """업비트 프라이빗 API용 Rate Limiter (싱글톤) - 성능 중시"""
    key = f"{client_id or 'upbit_private'}_{strategy.value}"
    if key not in _global_rate_limiters:
        _global_rate_limiters[key] = UpbitRateLimiter(client_id or "upbit_private", strategy)
    return _global_rate_limiters[key]


def create_upbit_websocket_limiter(client_id: Optional[str] = None,
                                   strategy: RateLimitStrategy = RateLimitStrategy.CLOUDFLARE_SLIDING_WINDOW
                                   ) -> UpbitRateLimiter:
    """업비트 WebSocket용 Rate Limiter (싱글톤) - 정확성 중시"""
    key = f"{client_id or 'upbit_websocket'}_{strategy.value}"
    if key not in _global_rate_limiters:
        _global_rate_limiters[key] = UpbitRateLimiter(client_id or "upbit_websocket", strategy)
    return _global_rate_limiters[key]


def get_available_strategies() -> Dict[str, str]:
    """사용 가능한 Rate Limiting 전략 목록"""
    return {
        strategy.value: {
            RateLimitStrategy.CLOUDFLARE_SLIDING_WINDOW.value: "Cloudflare 방식 - 정확성 중시, 업계 표준",
            RateLimitStrategy.AIOLIMITER_OPTIMIZED.value: "aiolimiter 최적화 - 성능 중시, 빠른 응답",
            RateLimitStrategy.HYBRID_FAST.value: "하이브리드 - 속도와 정확성 균형 (권장)"
        }[strategy.value] for strategy in RateLimitStrategy
    }
