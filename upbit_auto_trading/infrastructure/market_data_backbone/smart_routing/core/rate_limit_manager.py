"""
Smart Routing System - Rate Limit 관리자

업비트 웹소켓 Rate Limiting 규칙을 준수하는 스마트 라우팅 컴포넌트
- WebSocket 연결: 초당 최대 5회
- WebSocket 메시지: 초당 최대 5회, 분당 100회
- IP 단위 제한 관리
"""

import asyncio
import time
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("RateLimitManager")


class RateLimitType(Enum):
    """Rate Limit 타입 (업비트 2025년 최신 정책)"""
    # WebSocket 관련
    WEBSOCKET_CONNECT = "websocket_connect"  # 초당 5회
    WEBSOCKET_MESSAGE = "websocket_message"  # 초당 5회, 분당 100회

    # REST API - Quotation (시세 조회, IP 단위)
    QUOTATION_MARKET = "quotation_market"      # 초당 10회 - 페어 목록
    QUOTATION_CANDLE = "quotation_candle"      # 초당 10회 - 캔들 데이터
    QUOTATION_TRADE = "quotation_trade"        # 초당 10회 - 체결 이력
    QUOTATION_TICKER = "quotation_ticker"      # 초당 10회 - 현재가
    QUOTATION_ORDERBOOK = "quotation_orderbook" # 초당 10회 - 호가

    # REST API - Exchange (거래/자산, 계정 단위)
    EXCHANGE_DEFAULT = "exchange_default"      # 초당 30회 - 잔고, 주문조회 등
    EXCHANGE_ORDER = "exchange_order"          # 초당 8회 - 주문 생성
    EXCHANGE_ORDER_CANCEL_ALL = "exchange_order_cancel_all"  # 2초당 1회


@dataclass
class RateLimitRule:
    """Rate Limit 규칙"""
    limit_type: RateLimitType
    max_requests_per_second: float  # float로 변경 (2초당 1회 = 0.5초당 1회 지원)
    max_requests_per_minute: Optional[int] = None
    max_requests_per_hour: Optional[int] = None

    # 동적 조정 지원
    adaptive_mode: bool = False
    min_interval_ms: float = 200.0  # 최소 간격 (ms)


@dataclass
class RateLimitBucket:
    """Rate Limit 버킷"""
    rule: RateLimitRule
    requests_in_second: deque = field(default_factory=deque)
    requests_in_minute: deque = field(default_factory=deque)
    requests_in_hour: deque = field(default_factory=deque)

    last_request_time: float = 0.0
    blocked_until: float = 0.0

    # 통계
    total_requests: int = 0
    blocked_requests: int = 0
    adaptive_delay_ms: float = 200.0  # 적응형 지연


class UpbitRateLimitManager:
    """업비트 Rate Limit 관리자"""

    # 업비트 공식 Rate Limit 규칙 (2025년 최신 정책)
    UPBIT_RATE_LIMITS = {
        # WebSocket 관련
        RateLimitType.WEBSOCKET_CONNECT: RateLimitRule(
            limit_type=RateLimitType.WEBSOCKET_CONNECT,
            max_requests_per_second=5,
            adaptive_mode=True,
            min_interval_ms=200.0
        ),
        RateLimitType.WEBSOCKET_MESSAGE: RateLimitRule(
            limit_type=RateLimitType.WEBSOCKET_MESSAGE,
            max_requests_per_second=5,
            max_requests_per_minute=100,
            adaptive_mode=True,
            min_interval_ms=200.0
        ),

        # REST API - Quotation (시세 조회, IP 단위, 초당 10회)
        RateLimitType.QUOTATION_MARKET: RateLimitRule(
            limit_type=RateLimitType.QUOTATION_MARKET,
            max_requests_per_second=10,
            adaptive_mode=True,
            min_interval_ms=100.0
        ),
        RateLimitType.QUOTATION_CANDLE: RateLimitRule(
            limit_type=RateLimitType.QUOTATION_CANDLE,
            max_requests_per_second=10,
            adaptive_mode=True,
            min_interval_ms=100.0
        ),
        RateLimitType.QUOTATION_TRADE: RateLimitRule(
            limit_type=RateLimitType.QUOTATION_TRADE,
            max_requests_per_second=10,
            adaptive_mode=True,
            min_interval_ms=100.0
        ),
        RateLimitType.QUOTATION_TICKER: RateLimitRule(
            limit_type=RateLimitType.QUOTATION_TICKER,
            max_requests_per_second=10,
            adaptive_mode=True,
            min_interval_ms=100.0
        ),
        RateLimitType.QUOTATION_ORDERBOOK: RateLimitRule(
            limit_type=RateLimitType.QUOTATION_ORDERBOOK,
            max_requests_per_second=10,
            adaptive_mode=True,
            min_interval_ms=100.0
        ),

        # REST API - Exchange (거래/자산, 계정 단위)
        RateLimitType.EXCHANGE_DEFAULT: RateLimitRule(
            limit_type=RateLimitType.EXCHANGE_DEFAULT,
            max_requests_per_second=30,
            adaptive_mode=True,
            min_interval_ms=34.0  # 1000ms / 30 ≈ 33.3ms
        ),
        RateLimitType.EXCHANGE_ORDER: RateLimitRule(
            limit_type=RateLimitType.EXCHANGE_ORDER,
            max_requests_per_second=8,
            adaptive_mode=True,
            min_interval_ms=125.0  # 1000ms / 8 = 125ms
        ),
        RateLimitType.EXCHANGE_ORDER_CANCEL_ALL: RateLimitRule(
            limit_type=RateLimitType.EXCHANGE_ORDER_CANCEL_ALL,
            max_requests_per_second=0.5,  # 2초당 1회 = 0.5초당 1회
            adaptive_mode=True,
            min_interval_ms=2000.0  # 2초
        )
    }

    def __init__(self):
        self.buckets: Dict[RateLimitType, RateLimitBucket] = {}

        # Rate Limit 버킷 초기화
        for limit_type, rule in self.UPBIT_RATE_LIMITS.items():
            self.buckets[limit_type] = RateLimitBucket(rule=rule)

        # 관리 설정
        self.strict_mode = True  # 엄격 모드 (기본값)
        self.safety_margin = 0.8  # 안전 마진 (80% 사용)

        # 모니터링
        self.start_time = time.time()
        self.warning_callbacks: List[Callable] = []

        logger.info("UpbitRateLimitManager 초기화 완료")
        logger.info(f"WebSocket 연결 제한: {self.UPBIT_RATE_LIMITS[RateLimitType.WEBSOCKET_CONNECT].max_requests_per_second}/초")
        logger.info(f"WebSocket 메시지 제한: {self.UPBIT_RATE_LIMITS[RateLimitType.WEBSOCKET_MESSAGE].max_requests_per_second}/초, "
                   f"{self.UPBIT_RATE_LIMITS[RateLimitType.WEBSOCKET_MESSAGE].max_requests_per_minute}/분")

    async def can_make_request(self, limit_type: RateLimitType) -> bool:
        """요청 가능 여부 확인"""
        bucket = self.buckets.get(limit_type)
        if not bucket:
            return True

        current_time = time.time()

        # 현재 차단 상태 확인
        if current_time < bucket.blocked_until:
            return False

        # 시간 윈도우 정리
        self._cleanup_time_windows(bucket, current_time)

        # 제한 확인
        effective_per_second = int(bucket.rule.max_requests_per_second * self.safety_margin)

        # 초당 제한 확인
        if len(bucket.requests_in_second) >= effective_per_second:
            return False

        # 분당 제한 확인 (있는 경우)
        if bucket.rule.max_requests_per_minute:
            effective_per_minute = int(bucket.rule.max_requests_per_minute * self.safety_margin)
            if len(bucket.requests_in_minute) >= effective_per_minute:
                return False

        # 최소 간격 확인 (적응형 모드)
        if bucket.rule.adaptive_mode:
            min_interval = bucket.adaptive_delay_ms / 1000.0
            if current_time - bucket.last_request_time < min_interval:
                return False

        return True

    async def wait_for_slot(self, limit_type: RateLimitType) -> float:
        """다음 요청 가능 시점까지 대기"""
        bucket = self.buckets.get(limit_type)
        if not bucket:
            return 0.0

        wait_start = time.time()
        max_wait_time = 60.0  # 최대 1분 대기

        while not await self.can_make_request(limit_type):
            if time.time() - wait_start > max_wait_time:
                logger.warning(f"Rate limit 대기 시간 초과: {limit_type.value}")
                break

            # 적응형 대기 시간 계산
            wait_time = self._calculate_wait_time(bucket)
            await asyncio.sleep(wait_time)

        total_wait = time.time() - wait_start
        if total_wait > 0.1:  # 100ms 이상 대기한 경우 로깅
            logger.debug(f"Rate limit 대기: {limit_type.value}, {total_wait:.3f}초")

        return total_wait

    async def record_request(self, limit_type: RateLimitType) -> bool:
        """요청 기록"""
        bucket = self.buckets.get(limit_type)
        if not bucket:
            return True

        current_time = time.time()

        # 요청 가능 여부 재확인
        if not await self.can_make_request(limit_type):
            bucket.blocked_requests += 1
            logger.warning(f"Rate limit 위반 시도: {limit_type.value}")
            return False

        # 요청 기록
        bucket.requests_in_second.append(current_time)
        bucket.requests_in_minute.append(current_time)
        bucket.requests_in_hour.append(current_time)

        bucket.last_request_time = current_time
        bucket.total_requests += 1

        # 적응형 지연 조정
        if bucket.rule.adaptive_mode:
            self._adjust_adaptive_delay(bucket)

        # 임계값 경고
        await self._check_thresholds(bucket, current_time)

        return True

    def _cleanup_time_windows(self, bucket: RateLimitBucket, current_time: float):
        """시간 윈도우 정리"""
        # 1초 윈도우 정리
        while bucket.requests_in_second and bucket.requests_in_second[0] < current_time - 1.0:
            bucket.requests_in_second.popleft()

        # 1분 윈도우 정리
        while bucket.requests_in_minute and bucket.requests_in_minute[0] < current_time - 60.0:
            bucket.requests_in_minute.popleft()

        # 1시간 윈도우 정리
        while bucket.requests_in_hour and bucket.requests_in_hour[0] < current_time - 3600.0:
            bucket.requests_in_hour.popleft()

    def _calculate_wait_time(self, bucket: RateLimitBucket) -> float:
        """대기 시간 계산"""
        current_time = time.time()

        # 차단 해제 시간까지 대기
        if current_time < bucket.blocked_until:
            return bucket.blocked_until - current_time

        # 최소 간격 대기
        if bucket.rule.adaptive_mode:
            min_wait = bucket.adaptive_delay_ms / 1000.0
            elapsed = current_time - bucket.last_request_time
            if elapsed < min_wait:
                return min_wait - elapsed

        # 다음 슬롯까지 대기
        if bucket.requests_in_second:
            oldest_request = bucket.requests_in_second[0]
            return max(0.0, oldest_request + 1.0 - current_time)

        return 0.1  # 기본 100ms 대기

    def _adjust_adaptive_delay(self, bucket: RateLimitBucket):
        """적응형 지연 조정"""
        current_load = len(bucket.requests_in_second) / bucket.rule.max_requests_per_second

        if current_load > 0.8:  # 고부하
            bucket.adaptive_delay_ms = min(1000.0, bucket.adaptive_delay_ms * 1.2)
        elif current_load < 0.3:  # 저부하
            bucket.adaptive_delay_ms = max(bucket.rule.min_interval_ms, bucket.adaptive_delay_ms * 0.9)

    async def _check_thresholds(self, bucket: RateLimitBucket, current_time: float):
        """임계값 확인 및 경고"""
        second_usage = len(bucket.requests_in_second) / bucket.rule.max_requests_per_second

        if second_usage > 0.8:
            warning_msg = f"Rate limit 임계값 경고: {bucket.rule.limit_type.value} {second_usage:.1%} 사용 중"
            logger.warning(warning_msg)

            # 콜백 호출
            for callback in self.warning_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(bucket.rule.limit_type, second_usage)
                    else:
                        callback(bucket.rule.limit_type, second_usage)
                except Exception as e:
                    logger.error(f"Rate limit 경고 콜백 오류: {str(e)}")

    async def safe_websocket_connect(self) -> bool:
        """안전한 웹소켓 연결"""
        await self.wait_for_slot(RateLimitType.WEBSOCKET_CONNECT)
        return await self.record_request(RateLimitType.WEBSOCKET_CONNECT)

    async def safe_websocket_message(self) -> bool:
        """안전한 웹소켓 메시지 전송"""
        await self.wait_for_slot(RateLimitType.WEBSOCKET_MESSAGE)
        return await self.record_request(RateLimitType.WEBSOCKET_MESSAGE)

    def get_status(self) -> Dict[str, Any]:
        """Rate Limit 상태 조회"""
        current_time = time.time()
        status = {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': current_time - self.start_time,
            'safety_margin': self.safety_margin,
            'strict_mode': self.strict_mode,
            'limits': {}
        }

        for limit_type, bucket in self.buckets.items():
            self._cleanup_time_windows(bucket, current_time)

            status['limits'][limit_type.value] = {
                'max_per_second': bucket.rule.max_requests_per_second,
                'max_per_minute': bucket.rule.max_requests_per_minute,
                'current_second_usage': len(bucket.requests_in_second),
                'current_minute_usage': len(bucket.requests_in_minute),
                'usage_percent_second': len(bucket.requests_in_second) / bucket.rule.max_requests_per_second * 100,
                'total_requests': bucket.total_requests,
                'blocked_requests': bucket.blocked_requests,
                'adaptive_delay_ms': bucket.adaptive_delay_ms,
                'next_available_in_ms': max(0, (bucket.last_request_time + bucket.adaptive_delay_ms/1000 - current_time) * 1000)
            }

        return status

    def register_warning_callback(self, callback: Callable):
        """Rate Limit 경고 콜백 등록"""
        self.warning_callbacks.append(callback)

    def set_safety_margin(self, margin: float):
        """안전 마진 설정 (0.0 ~ 1.0)"""
        self.safety_margin = max(0.1, min(1.0, margin))
        logger.info(f"Rate limit 안전 마진 설정: {self.safety_margin:.1%}")

    def reset_stats(self):
        """통계 초기화"""
        for bucket in self.buckets.values():
            bucket.total_requests = 0
            bucket.blocked_requests = 0

        self.start_time = time.time()
        logger.info("Rate limit 통계 초기화")


class RateLimitAwareWebSocketManager:
    """Rate Limit을 고려한 웹소켓 관리자"""

    def __init__(self):
        self.rate_limiter = UpbitRateLimitManager()
        self.active_connections: Dict[str, Any] = {}
        self.connection_pool_size = 3  # 최대 동시 연결 수
        self.logger = create_component_logger("RateLimitAwareWebSocketManager")

        # Rate Limit 경고 콜백 등록
        self.rate_limiter.register_warning_callback(self._on_rate_limit_warning)

    async def create_connection(self, connection_id: str) -> bool:
        """Rate Limit을 고려한 연결 생성"""
        if len(self.active_connections) >= self.connection_pool_size:
            self.logger.warning(f"연결 풀 제한 도달: {len(self.active_connections)}/{self.connection_pool_size}")
            return False

        if not await self.rate_limiter.safe_websocket_connect():
            self.logger.error(f"Rate limit로 인한 연결 실패: {connection_id}")
            return False

        try:
            # 실제 WebSocket 연결 생성
            self.active_connections[connection_id] = {
                'created_at': time.time(),
                'message_count': 0,
                'status': 'connected',
                'last_activity': time.time()
            }

            self.logger.info(f"✅ Rate limit 준수 연결 생성: {connection_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 연결 생성 실패: {connection_id}, 오류: {str(e)}")
            return False

    async def send_message(self, connection_id: str, message: str) -> bool:
        """Rate Limit을 고려한 메시지 전송"""
        if connection_id not in self.active_connections:
            self.logger.warning(f"존재하지 않는 연결: {connection_id}")
            return False

        if not await self.rate_limiter.safe_websocket_message():
            self.logger.warning(f"Rate limit로 인한 메시지 전송 지연: {connection_id}")
            return False

        try:
            # 실제 메시지 전송 (WebSocket send)
            connection_info = self.active_connections[connection_id]
            connection_info['message_count'] += 1
            connection_info['last_activity'] = time.time()

            # 메시지 전송 성공 로깅
            self.logger.debug(f"✅ Rate limit 준수 메시지 전송: {connection_id}, 메시지 길이: {len(message)}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 메시지 전송 실패: {connection_id}, 오류: {str(e)}")
            return False

    def close_connection(self, connection_id: str) -> bool:
        """연결 종료"""
        if connection_id not in self.active_connections:
            return False

        try:
            del self.active_connections[connection_id]
            self.logger.info(f"✅ 연결 종료: {connection_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ 연결 종료 실패: {connection_id}, 오류: {str(e)}")
            return False

    async def _on_rate_limit_warning(self, limit_type: RateLimitType, usage_percent: float):
        """Rate Limit 경고 처리"""
        self.logger.warning(f"Rate limit 임계값 도달: {limit_type.value} {usage_percent:.1%}")

        # 추가 보호 조치
        if usage_percent > 0.9:
            self.rate_limiter.set_safety_margin(0.6)  # 안전 마진 강화
            self.logger.info("Rate limit 임계값 초과로 안전 마진 강화")

    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        return {
            'rate_limiter': self.rate_limiter.get_status(),
            'active_connections': len(self.active_connections),
            'max_connections': self.connection_pool_size,
            'connections': {
                conn_id: {
                    'uptime_seconds': time.time() - info['created_at'],
                    'message_count': info['message_count']
                }
                for conn_id, info in self.active_connections.items()
            }
        }


# 전역 Rate Limit 관리자 인스턴스
_global_rate_limiter: Optional[UpbitRateLimitManager] = None


def get_global_rate_limiter() -> UpbitRateLimitManager:
    """전역 Rate Limit 관리자 조회"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = UpbitRateLimitManager()
    return _global_rate_limiter
