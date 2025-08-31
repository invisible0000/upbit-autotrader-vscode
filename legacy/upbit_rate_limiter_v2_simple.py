"""
업비트 Rate Limiter V2 - Legacy 아키텍처 + 웜업 시스템 + PRG 통합

🎯 핵심 설계 원칙:
- Legacy의 탄탄한 아키텍처 유지 (전역 제한, 멀티 윈도우, 카테고리 관리)
- 새로운 웜업 시스템 추가 (콜드 스타트 보상)
- PRG (PreemptiveRateGuard): Cloudflare RLWait을 순간적으로 강하게 보상
- Rate Limiter는 절대 실패하지 않음 (항상 적절한 대기시간 제공)

핵심 특징:
- 전역 제한: 모든 인스턴스가 동일한 제한 공유
- 멀티 윈도우: WebSocket 5 RPS + 100 RPM 동시 지원
- 체계적 카테고리: UpbitApiCategory Enum + 상세 매핑
- 내장 웜업: 콜드 스타트 시 점진적 성능 향상
- PRG 시스템: 순간적 부하 억제를 위한 예방적 대기시간 보상
"""

import asyncio
import time
import math
import threading
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("RateLimiterV2Legacy")


class UpbitApiCategory(Enum):
    """업비트 API 카테고리 - 완전한 지원"""
    QUOTATION = "quotation"                    # 시세 조회: 10 RPS
    EXCHANGE_DEFAULT = "exchange_default"      # 기본 거래소: 30 RPS
    EXCHANGE_ORDER = "exchange_order"          # 주문 생성/수정: 8 RPS
    EXCHANGE_CANCEL_ALL = "exchange_cancel_all"  # 일괄 취소: 0.5 RPS
    WEBSOCKET = "websocket"                    # WebSocket: 5 RPS + 100 RPM


@dataclass
class RateWindow:
    """Rate Limit 윈도우"""
    max_requests: int
    window_seconds: int

    @property
    def requests_per_second(self) -> float:
        return self.max_requests / self.window_seconds


@dataclass
class PRGStatus:
    """PRG (PreemptiveRateGuard) 상태 - 윈도우별"""
    is_active: bool = False
    trigger_count: int = 0
    consecutive_triggers: int = 0
    last_trigger_time: float = 0.0
    should_reset: bool = False  # 다음 요청에서 리셋 예약
    air_history: Optional[List[float]] = None  # AIR 히스토리 (요청별 실제 간격)

    def __post_init__(self):
        if self.air_history is None:
            self.air_history = []


@dataclass
class RateLimitRule:
    """Rate Limit 규칙"""
    windows: List[RateWindow]
    category: UpbitApiCategory
    name: str

    def get_strictest_rps(self) -> float:
        """가장 엄격한 RPS 반환"""
        return min(w.requests_per_second for w in self.windows)


class CloudflareSlidingWindowWithWarmupAndPRG:
    """
    Cloudflare Sliding Window + 웜업 시스템 + PRG

    🎯 Legacy 기능 + 새로운 웜업 + PRG:
    - 멀티 윈도우 지원 (WebSocket 5 RPS + 100 RPM)
    - 전역 공유 상태
    - 웜업 기반 콜드 스타트 보상
    - PRG: Cloudflare RLWait을 순간적으로 강하게 보상
    - Rate Limiter는 절대 실패하지 않음
    """

    # 전역 공유 상태 (Legacy 호환)
    _global_limiters: Dict[str, 'CloudflareSlidingWindowWithWarmupAndPRG'] = {}
    _global_lock = threading.Lock()

    def __init__(self, windows: List[RateWindow], limiter_id: str):
        self.windows = windows
        self.limiter_id = limiter_id

        # Cloudflare 멀티 윈도우 시스템
        self.window_data = {}
        for i, window in enumerate(windows):
            self.window_data[i] = {
                'current_count': 0,
                'previous_count': 0,
                'window_start_time': time.time(),
                'window_seconds': window.window_seconds,
                'max_requests': window.max_requests
            }

        # 웜업 시스템 (새로운 기능)
        self.warmup_history: Dict[int, List[float]] = {}  # 윈도우별 요청 히스토리
        self.warmup_factor = 0.8  # 초기 80% 성능 (개선됨)
        self.is_cold_start = True
        self.warmup_requests = 0

        # PRG (PreemptiveRateGuard) 시스템 (새로운 기능)
        self.prg_statuses: Dict[int, PRGStatus] = {}  # 윈도우별 PRG 상태
        for i in range(len(windows)):
            self.prg_statuses[i] = PRGStatus()

        # PRG 설정값
        self.prg_threshold_factor = 0.98  # 98% 임계값
        self.prg_wait_base_factor = 0.1   # TIR * 0.1 기본 대기
        self.prg_wait_increment = 0.1     # 매번 TIR * 0.1씩 증가
        self.prg_max_triggers = 20        # 최대 20회까지 누적

        # 통계 및 시간 추적
        self.total_requests = 0
        self.last_request_time = 0.0  # 마지막 요청 시간 (AIR 계산용)
        self._lock = asyncio.Lock()

        # 전역 등록 (Legacy 호환)
        with self._global_lock:
            self._global_limiters[limiter_id] = self

    @classmethod
    def get_global_limiter(cls, limiter_id: str) -> Optional['CloudflareSlidingWindowWithWarmupAndPRG']:
        """전역 Limiter 조회 (Legacy 호환)"""
        with cls._global_lock:
            return cls._global_limiters.get(limiter_id)

    @classmethod
    def get_all_global_usage(cls) -> Dict[str, Dict]:
        """모든 전역 Limiter 사용량 조회"""
        with cls._global_lock:
            usage = {}
            now = time.time()
            for limiter_id, limiter in cls._global_limiters.items():
                usage[limiter_id] = limiter.get_usage_info(now)
            return usage

    def _update_window_if_needed(self, window_id: int, now: float) -> None:
        """윈도우 갱신 (Cloudflare 공식 로직)"""
        data = self.window_data[window_id]
        window_seconds = data['window_seconds']
        elapsed = now - data['window_start_time']

        if elapsed >= window_seconds:
            periods_passed = int(elapsed // window_seconds)
            if periods_passed == 1:
                data['previous_count'] = data['current_count']
            else:
                data['previous_count'] = 0

            data['current_count'] = 0
            data['window_start_time'] = now

    def _update_warmup_status(self, window_id: int, now: float) -> float:
        """
        웜업 상태 업데이트 (개선된 알고리즘)

        콜드 스타트 시 빠른 성능 향상
        초기 5개 요청 동안 80% → 100% 성능으로 웜업
        """
        if window_id not in self.warmup_history:
            self.warmup_history[window_id] = []

        history = self.warmup_history[window_id]
        window_seconds = self.windows[window_id].window_seconds

        # 윈도우 범위 내 요청만 유지
        cutoff_time = now - window_seconds * 1.5  # 더 짧은 범위
        history[:] = [req_time for req_time in history if req_time > cutoff_time]

        # 웜업 팩터 계산 (5개 요청까지 빠른 증가)
        warmup_requests = len(history)
        if warmup_requests < 5:
            self.warmup_factor = 0.8 + (warmup_requests / 5) * 0.2  # 80% → 100%
            self.is_cold_start = True
        else:
            self.warmup_factor = 1.0
            self.is_cold_start = False

        return self.warmup_factor

    def _update_air_history(self, window_id: int, actual_interval_ms: float, now: float) -> None:
        """
        AIR 히스토리 업데이트 (PRG용) - 정확한 N개 유지

        Args:
            window_id: 윈도우 ID
            actual_interval_ms: 실제 요청 간격 (밀리초)
            now: 현재 시간
        """
        prg_status = self.prg_statuses[window_id]
        window = self.windows[window_id]

        # air_history가 None이면 초기화
        if prg_status.air_history is None:
            prg_status.air_history = []

        # AIR 히스토리에 추가
        prg_status.air_history.append(actual_interval_ms)

        # 정확히 required_samples만 유지 (10 RPS면 10개, 8 RPS면 8개)
        rps = window.requests_per_second
        required_samples = math.ceil(rps) if rps >= 1.0 else 1

        if len(prg_status.air_history) > required_samples:
            prg_status.air_history = prg_status.air_history[-required_samples:]

    def _check_prg_trigger_with_provisional(
        self, window_id: int, provisional_air_ms: float, rl_wait_ms: float, now: float
    ) -> bool:
        """
        PRG 트리거 조건 확인 (선제적 로직 - 잠정 AIR 포함)

        선제적 조건: (N-1개AIR + 잠정AIR + RLWait) <= TIR * 0.98 * N
        - 10RPS: (9개AIR + 잠정AIR + RLWait) <= 980ms일 때 PRG 활성화
        - 8RPS: (7개AIR + 잠정AIR + RLWait) <= 784ms일 때 PRG 활성화

        Args:
            window_id: 윈도우 ID
            provisional_air_ms: 현재 요청의 잠정 AIR (밀리초)
            rl_wait_ms: Cloudflare Rate Limiter 대기시간 (밀리초)
            now: 현재 시간

        Returns:
            bool: PRG 트리거 여부
        """
        window = self.windows[window_id]
        prg_status = self.prg_statuses[window_id]

        # air_history가 None이면 False 반환
        if prg_status.air_history is None:
            return False

        # RPS별 샘플 수와 TIR 계산
        rps = window.requests_per_second
        if rps >= 1.0:
            required_samples = math.ceil(rps)
            target_interval_ms = 1000.0 / rps
        else:
            required_samples = 1
            target_interval_ms = 1000.0 / rps

        if len(prg_status.air_history) < 1:  # 최소 1개 필요
            return False

        # 정확한 N개AIR 계산 (기존 히스토리 + 잠정AIR)
        if len(prg_status.air_history) >= required_samples:
            # 이미 N개가 있다면: 마지막 (N-1)개 + 잠정AIR = N개
            recent_air_sum = sum(prg_status.air_history[-(required_samples - 1):])
        else:
            # 아직 N개 미만이라면: 모든 기존 + 잠정AIR
            recent_air_sum = sum(prg_status.air_history)

        # 선제적 총합: 기존AIR + 잠정AIR (정확한 N개)
        current_n_air_sum = recent_air_sum + provisional_air_ms

        # PRG 트리거 조건: N개AIR < TIR * 0.98 * N (429 위험 감지, <= 제거)
        threshold_factor = 0.98
        threshold = target_interval_ms * threshold_factor * required_samples

        logger.debug(f"PRG 선제체크 (윈도우 {window_id}): "
                     f"({recent_air_sum:.1f} + {provisional_air_ms:.1f}) = "
                     f"{current_n_air_sum:.1f}ms < {threshold:.1f}ms "
                     f"({'✅ 429위험' if current_n_air_sum < threshold else '❌ 안전'}) "
                     f"[{required_samples}샘플, TIR:{target_interval_ms:.1f}ms]")

        return current_n_air_sum < threshold

    def _check_prg_trigger(self, window_id: int, now: float) -> bool:
        """
        PRG 트리거 조건 확인 (기존 로직 - 호환성 유지)

        조건: N개AIR < TIR * 0.98 * N
        - 10RPS: 10AIR < 980ms
        - 8RPS: 8AIR < 784ms

        Args:
            window_id: 윈도우 ID
            now: 현재 시간

        Returns:
            bool: PRG 트리거 여부
        """
        window = self.windows[window_id]
        prg_status = self.prg_statuses[window_id]

        # air_history가 None이면 False 반환
        if prg_status.air_history is None:
            return False

        # RPS별 샘플 수와 TIR 계산
        rps = window.requests_per_second
        if rps >= 1.0:
            required_samples = math.ceil(rps)
            target_interval_ms = 1000.0 / rps
        else:
            required_samples = 1
            target_interval_ms = 1000.0 / rps

        if len(prg_status.air_history) < required_samples:
            return False

        # 최근 N개 요청의 AIR 합계 계산
        recent_air_sum = sum(prg_status.air_history[-required_samples:])

        # PRG 트리거 조건: N개AIR < TIR * 0.98 * N
        threshold_factor = 0.98
        threshold = target_interval_ms * threshold_factor * required_samples

        logger.debug(f"PRG 체크 (윈도우 {window_id}): {recent_air_sum:.1f}ms < {threshold:.1f}ms "
                     f"({'✅' if recent_air_sum < threshold else '❌'}) "
                     f"[{required_samples}샘플, TIR:{target_interval_ms:.1f}ms]")

        return recent_air_sum < threshold

    def _calculate_prg_wait_with_provisional(
        self, window_id: int, provisional_air_ms: float, rl_wait_ms: float, now: float
    ) -> float:
        """
        PRG 대기시간 계산 (선제적 로직)

        선제적 공식: PRGWait = (N × TIR) - ((N-1)개AIR + 잠정AIR + RLWait)
        예시: 1000ms - (280ms + 31ms + 95ms) = 594ms

        Args:
            window_id: 윈도우 ID
            provisional_air_ms: 현재 요청의 잠정 AIR (밀리초)
            rl_wait_ms: Cloudflare Rate Limiter 대기시간 (밀리초)
            now: 현재 시간

        Returns:
            float: PRG 대기시간 (밀리초)
        """
        window = self.windows[window_id]
        prg_status = self.prg_statuses[window_id]

        # TIR 및 샘플 수 계산
        rps = window.requests_per_second
        if rps >= 1.0:
            required_samples = math.ceil(rps)
            target_interval_ms = 1000.0 / rps
        else:
            required_samples = 1
            target_interval_ms = 1000.0 / rps

        # 정확한 (N-1)개AIR 계산
        if prg_status.air_history and len(prg_status.air_history) >= required_samples:
            # 이미 N개가 있다면: 마지막 (N-1)개 사용
            current_air_sum = sum(prg_status.air_history[-(required_samples - 1):])
        elif prg_status.air_history and len(prg_status.air_history) >= required_samples - 1:
            # (N-1)개가 있다면: 모든 기존 사용
            current_air_sum = sum(prg_status.air_history[-(required_samples - 1):])
        else:
            # 부족하다면: 모든 기존 사용
            current_air_sum = sum(prg_status.air_history) if prg_status.air_history else 0

        # 선제적 PRG 계산: (N × TIR) - (기존AIR + 잠정AIR)
        target_total_time = target_interval_ms * required_samples
        current_n_air_sum = current_air_sum + provisional_air_ms
        prg_wait_ms = max(0, target_total_time - current_n_air_sum)

        # PRG 상태 업데이트
        prg_status.consecutive_triggers = 1
        prg_status.trigger_count += 1
        prg_status.last_trigger_time = now
        prg_status.is_active = True

        logger.debug(f"PRG 선제계산 (윈도우 {window_id}): "
                     f"목표시간: {target_total_time:.1f}ms, "
                     f"현재N개AIR: {current_n_air_sum:.1f}ms "
                     f"({current_air_sum:.1f}+{provisional_air_ms:.1f}), "
                     f"PRGWait: {prg_wait_ms:.1f}ms")

        # 목표 달성 시 다음 요청에서 리셋
        if prg_wait_ms > 0:
            prg_status.should_reset = True

        return prg_wait_ms

    def _calculate_prg_wait(self, window_id: int, now: float) -> float:
        """
        PRG 대기시간 계산 (기존 로직 - 호환성 유지)

        단순 공식: PRGWait = (N × TIR) - 현재 N개AIR
        예시: 1000ms - 280ms = 720ms

        Args:
            window_id: 윈도우 ID
            now: 현재 시간

        Returns:
            float: PRG 대기시간 (밀리초)
        """
        window = self.windows[window_id]
        prg_status = self.prg_statuses[window_id]

        # TIR 및 샘플 수 계산
        rps = window.requests_per_second
        if rps >= 1.0:
            required_samples = math.ceil(rps)
            target_interval_ms = 1000.0 / rps
        else:
            required_samples = 1
            target_interval_ms = 1000.0 / rps

        # 현재 N개AIR 계산
        if prg_status.air_history and len(prg_status.air_history) >= required_samples:
            current_air_sum = sum(prg_status.air_history[-required_samples:])
        else:
            current_air_sum = 0

        # 단순 PRG 계산: (N × TIR) - 현재 N개AIR
        target_total_time = target_interval_ms * required_samples
        prg_wait_ms = max(0, target_total_time - current_air_sum)

        # PRG 상태 업데이트
        prg_status.consecutive_triggers = 1  # 단순화: 항상 1회로 표시
        prg_status.trigger_count += 1
        prg_status.last_trigger_time = now
        prg_status.is_active = True

        logger.debug(f"PRG 활성화 (윈도우 {window_id}): 단순계산 → "
                     f"목표시간: {target_total_time:.1f}ms, 현재AIR: {current_air_sum:.1f}ms, "
                     f"PRGWait: {prg_wait_ms:.1f}ms")

        # 목표 달성 시 다음 요청에서 리셋
        if prg_wait_ms > 0:
            prg_status.should_reset = True

        return prg_wait_ms

    def _reset_prg_if_stable(self, window_id: int, now: float) -> None:
        """
        윈도우가 안정화되면 PRG 리셋

        Args:
            window_id: 윈도우 ID
            now: 현재 시간
        """
        prg_status = self.prg_statuses[window_id]

        if prg_status.is_active and not self._check_prg_trigger(window_id, now):
            prg_status.consecutive_triggers = 0
            prg_status.is_active = False
            logger.debug(f"PRG 리셋 (윈도우 {window_id}): 윈도우 안정화")

    def calculate_optimal_wait_time_with_provisional(
        self, now: float, provisional_air_ms: float = 0
    ) -> Tuple[bool, float, Dict]:
        """
        🎯 선제적 PRG: 잠정 AIR을 포함한 최적 대기시간 계산

        Args:
            now: 현재 시간
            provisional_air_ms: 현재 요청의 잠정 AIR (밀리초)

        Returns:
            Tuple[bool, float, Dict]: (성공여부, 대기시간(초), 상태정보)
        """
        # PRG 리셋 처리 (먼저 확인)
        for window_id in range(len(self.windows)):
            prg_status = self.prg_statuses[window_id]
            if prg_status.should_reset:
                logger.debug(f"PRG 리셋 (윈도우 {window_id}): {prg_status.consecutive_triggers}회 → 0회")
                prg_status.consecutive_triggers = 0
                prg_status.is_active = False
                prg_status.should_reset = False

        max_wait_needed = 0.0
        status_info = {
            'warmup_factor': 1.0,
            'is_cold_start': False,
            'window_states': [],
            'total_requests': self.total_requests,
            'prg_triggered': False,
            'prg_wait_ms': 0.0,
            'rl_wait_ms': 0.0
        }

        for window_id, window in enumerate(self.windows):
            # 1. 웜업 상태 업데이트
            warmup_factor = self._update_warmup_status(window_id, now)
            status_info['warmup_factor'] = warmup_factor
            status_info['is_cold_start'] = self.is_cold_start

            # 2. 윈도우 업데이트
            self._update_window_if_needed(window_id, now)

            data = self.window_data[window_id]
            elapsed = now - data['window_start_time']
            window_seconds = data['window_seconds']
            max_requests = data['max_requests']

            # 3. 웜업 적용 (콜드 스타트 시 성능 제한)
            effective_max_requests = max_requests * warmup_factor

            # 4. Cloudflare 공식 sliding window 계산
            remaining_ratio = (window_seconds - elapsed) / window_seconds
            estimated_rate = data['previous_count'] * remaining_ratio + data['current_count']

            # 5. Cloudflare Rate Limiter 대기시간 계산
            wait_time = 0.0
            rl_wait_ms = 0.0

            usage_percent = (estimated_rate / effective_max_requests) * 100 if effective_max_requests > 0 else 0

            if estimated_rate + 1 > effective_max_requests:
                # Cloudflare 대기시간 계산
                excess_requests = (estimated_rate + 1) - effective_max_requests
                slots_per_second = effective_max_requests / window_seconds
                base_wait = 1.0 / slots_per_second

                # 웜업 단계별 안전 계수 적용
                if self.is_cold_start:
                    safety_factor = 1.05
                else:
                    safety_factor = 0.95

                wait_time = base_wait * excess_requests * safety_factor
                rl_wait_ms = wait_time * 1000.0  # 초를 밀리초로 변환

            # 6. 🎯 선제적 PRG 시스템 적용
            prg_wait_ms = 0.0

            # 잠정AIR에 Cloudflare 대기시간 포함 (더 정확한 예측)
            provisional_air_with_rl_ms = provisional_air_ms + rl_wait_ms

            # 선제적 PRG 체크: 실제 예상 간격 사용
            if self._check_prg_trigger_with_provisional(window_id, provisional_air_with_rl_ms, 0.0, now):
                prg_wait_ms = self._calculate_prg_wait_with_provisional(window_id, provisional_air_with_rl_ms, 0.0, now)
                status_info['prg_triggered'] = True
                logger.debug(f"🚨 선제적 PRG 활성화 (윈도우 {window_id}): "
                             f"기본AIR: {provisional_air_ms:.1f}ms, "
                             f"RLWait: {rl_wait_ms:.1f}ms, "
                             f"실제예상: {provisional_air_with_rl_ms:.1f}ms, "
                             f"PRGWait: {prg_wait_ms:.1f}ms")
            else:
                self._reset_prg_if_stable(window_id, now)

            # 7. 총 대기시간: RLWait + PRGWait
            total_wait_time = wait_time + (prg_wait_ms / 1000.0)  # PRG는 ms 단위이므로 초로 변환

            # 최대 대기 시간 제한
            max_allowed_wait = window_seconds * 0.5
            total_wait_time = min(total_wait_time, max_allowed_wait)

            max_wait_needed = max(max_wait_needed, total_wait_time)

            # 상태 정보 저장
            status_info['rl_wait_ms'] = max(status_info['rl_wait_ms'], rl_wait_ms)
            status_info['prg_wait_ms'] = max(status_info['prg_wait_ms'], prg_wait_ms)

            # 윈도우 상태 저장
            prg_status = self.prg_statuses[window_id]
            status_info['window_states'].append({
                'window_id': window_id,
                'window_seconds': window_seconds,
                'max_requests': max_requests,
                'current': data['current_count'],
                'previous': data['previous_count'],
                'estimated_rate': estimated_rate,
                'effective_limit': effective_max_requests,
                'usage_percent': usage_percent,
                'prg_status': {
                    'is_active': prg_status.is_active,
                    'trigger_count': prg_status.trigger_count,
                    'consecutive_triggers': prg_status.consecutive_triggers,
                    'air_history_count': len(prg_status.air_history) if prg_status.air_history else 0
                }
            })

        return True, max_wait_needed, status_info

    def calculate_optimal_wait_time(self, now: float) -> Tuple[bool, float, Dict]:
        """
        🎯 기존 호환성: 잠정 AIR 없이 계산 (호환성 유지)
        """
        return self.calculate_optimal_wait_time_with_provisional(now, 0.0)

    async def acquire(self, max_retries: int = 3) -> bool:
        """Rate Limit 토큰 획득 (선제적 PRG 적용)"""
        async with self._lock:
            now = time.time()

            # AIR (Actual Interval Rate) 계산 - 선제적 PRG용
            provisional_air_ms = 0.0
            if self.last_request_time > 0:
                provisional_air_ms = (now - self.last_request_time) * 1000

            # 🎯 선제적 PRG: 잠정 AIR 포함 최적 대기시간 계산
            allowed, wait_time, status_info = self.calculate_optimal_wait_time_with_provisional(
                now, provisional_air_ms
            )

            # 대기시간이 있다면 적용
            if wait_time > 0:
                await asyncio.sleep(wait_time)

            # 모든 윈도우의 카운트 업데이트 및 PRG 히스토리 업데이트
            request_time = time.time()  # 실제 요청 실행 시점

            # 실제 AIR 재계산 (대기시간 적용 후)
            actual_interval_ms = 0.0
            if self.last_request_time > 0:
                actual_interval_ms = (request_time - self.last_request_time) * 1000

            for window_id in range(len(self.windows)):
                self.window_data[window_id]['current_count'] += 1

                # 웜업 히스토리에 추가
                if window_id in self.warmup_history:
                    self.warmup_history[window_id].append(request_time)

                # PRG AIR 히스토리 업데이트 (첫 요청이 아닌 경우)
                if self.total_requests > 0:
                    self._update_air_history(window_id, actual_interval_ms, request_time)

            self.total_requests += 1
            self.last_request_time = request_time  # 다음 AIR 계산을 위해 저장

            if self.is_cold_start:
                self.warmup_requests += 1

            return True  # 항상 성공

    async def acquire_with_status(self) -> Tuple[bool, Dict]:
        """상세 상태 정보와 함께 토큰 획득 (선제적 PRG 적용)"""
        async with self._lock:
            now = time.time()

            # AIR (Actual Interval Rate) 계산 - 선제적 PRG용
            provisional_air_ms = 0.0
            if self.last_request_time > 0:
                provisional_air_ms = (now - self.last_request_time) * 1000

            # 🎯 선제적 PRG: 잠정 AIR 포함 최적 대기시간 계산
            allowed, wait_time, status_info = self.calculate_optimal_wait_time_with_provisional(
                now, provisional_air_ms
            )

            # PRG 정보 추출
            prg_wait_ms = status_info.get('prg_wait_ms', 0.0)
            rl_wait_ms = status_info.get('rl_wait_ms', 0.0)
            prg_triggered = status_info.get('prg_triggered', False)

            # 대기시간이 있다면 적용
            if wait_time > 0:
                await asyncio.sleep(wait_time)

            # 모든 윈도우의 카운트 업데이트 및 PRG 히스토리 업데이트
            request_time = time.time()

            # 실제 AIR 재계산 (대기시간 적용 후)
            actual_interval_ms = 0.0
            if self.last_request_time > 0:
                actual_interval_ms = (request_time - self.last_request_time) * 1000

            for window_id in range(len(self.windows)):
                self.window_data[window_id]['current_count'] += 1

                # 웜업 히스토리에 추가
                if window_id in self.warmup_history:
                    self.warmup_history[window_id].append(request_time)

                # PRG AIR 히스토리 업데이트 (첫 요청이 아닌 경우)
                if self.total_requests > 0:
                    self._update_air_history(window_id, actual_interval_ms, request_time)

            self.total_requests += 1
            self.last_request_time = request_time

            if self.is_cold_start:
                self.warmup_requests += 1

            # 상세 상태 정보 업데이트 (선제적 PRG 포함)
            total_wait_ms = rl_wait_ms + prg_wait_ms  # TWait = RLWait + PRGWait

            status_info.update({
                'wait_time_applied': wait_time,
                'total_requests': self.total_requests,
                'warmup_requests': self.warmup_requests,
                'rl_wait_ms': rl_wait_ms,
                'prg_wait_ms': prg_wait_ms,
                'total_wait_ms': total_wait_ms,
                'prg_triggered': prg_triggered,
                'provisional_air_ms': provisional_air_ms,
                'actual_air_ms': actual_interval_ms,
                'prg_type': 'preemptive' if prg_triggered else 'none'
            })

            return True, status_info

    def get_usage_info(self, now: float) -> Dict[str, Any]:
        """현재 사용량 정보 반환 (Legacy 호환)"""
        usage_info = {}

        for i, window in enumerate(self.windows):
            self._update_window_if_needed(i, now)

            data = self.window_data[i]
            elapsed = now - data['window_start_time']

            remaining_ratio = (data['window_seconds'] - elapsed) / data['window_seconds']
            estimated_rate = data['previous_count'] * remaining_ratio + data['current_count']
            usage_percent = (estimated_rate / window.max_requests) * 100

            usage_info[f'window_{i}'] = {
                'window_seconds': window.window_seconds,
                'limit': window.max_requests,
                'current': data['current_count'],
                'previous': data['previous_count'],
                'estimated_rate': estimated_rate,
                'usage_percent': usage_percent,
                'rps': window.requests_per_second,
                'elapsed_in_window': elapsed
            }

        return usage_info


class UpbitRateLimiterV2:
    """
    업비트 Rate Limiter V2 - Legacy 아키텍처 + 웜업 시스템

    🎯 핵심 특징:
    - Legacy의 탄탄한 아키텍처 유지
    - 전역 제한 지원 (모든 인스턴스 영향)
    - 멀티 윈도우 지원 (WebSocket 등)
    - 체계적 카테고리 관리
    - 새로운 웜업 시스템
    """

    # 업비트 공식 Rate Limit 규칙 (Legacy 호환)
    UPBIT_RULES = {
        UpbitApiCategory.QUOTATION: RateLimitRule(
            windows=[RateWindow(10, 1)],  # 10 RPS
            category=UpbitApiCategory.QUOTATION,
            name="시세 조회"
        ),
        UpbitApiCategory.EXCHANGE_DEFAULT: RateLimitRule(
            windows=[RateWindow(30, 1)],  # 30 RPS
            category=UpbitApiCategory.EXCHANGE_DEFAULT,
            name="기본 거래소"
        ),
        UpbitApiCategory.EXCHANGE_ORDER: RateLimitRule(
            windows=[RateWindow(8, 1)],  # 8 RPS
            category=UpbitApiCategory.EXCHANGE_ORDER,
            name="주문 생성/수정"
        ),
        UpbitApiCategory.EXCHANGE_CANCEL_ALL: RateLimitRule(
            windows=[RateWindow(1, 2)],  # 0.5 RPS (1 per 2 seconds)
            category=UpbitApiCategory.EXCHANGE_CANCEL_ALL,
            name="일괄 취소"
        ),
        UpbitApiCategory.WEBSOCKET: RateLimitRule(
            windows=[RateWindow(5, 1), RateWindow(100, 60)],  # 5 RPS + 100 RPM
            category=UpbitApiCategory.WEBSOCKET,
            name="WebSocket"
        ),
    }

    # 엔드포인트 → 카테고리 매핑 (Legacy 호환)
    ENDPOINT_MAPPINGS = {
        # 시세 조회 (QUOTATION)
        '/market/all': UpbitApiCategory.QUOTATION,
        '/candles/': UpbitApiCategory.QUOTATION,
        '/v1/candles': UpbitApiCategory.QUOTATION,
        '/ticker': UpbitApiCategory.QUOTATION,
        '/v1/ticker': UpbitApiCategory.QUOTATION,
        '/tickers': UpbitApiCategory.QUOTATION,
        '/v1/tickers': UpbitApiCategory.QUOTATION,
        '/trades/ticks': UpbitApiCategory.QUOTATION,
        '/v1/trades/ticks': UpbitApiCategory.QUOTATION,
        '/orderbook': UpbitApiCategory.QUOTATION,
        '/v1/orderbook': UpbitApiCategory.QUOTATION,

        # 기본 거래소 (EXCHANGE_DEFAULT)
        '/accounts': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/v1/accounts': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/orders/chance': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/v1/orders/chance': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/order': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/v1/order': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/orders/uuids': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/v1/orders/uuids': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/orders/open': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/v1/orders/open': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/orders/closed': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/v1/orders/closed': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/withdraws': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/v1/withdraws': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/deposits': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/v1/deposits': UpbitApiCategory.EXCHANGE_DEFAULT,

        # WebSocket
        '/websocket': UpbitApiCategory.WEBSOCKET,
        '/v1/websocket': UpbitApiCategory.WEBSOCKET,
    }

    # 특수 메서드 매핑 (endpoint, method) → category
    SPECIAL_METHOD_MAPPINGS = {
        # 주문 생성/수정 (EXCHANGE_ORDER)
        ('/order', 'POST'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/v1/order', 'POST'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/orders', 'POST'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/v1/orders', 'POST'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/order', 'DELETE'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/v1/order', 'DELETE'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/orders', 'DELETE'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/v1/orders', 'DELETE'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/orders/cancel_and_new', 'POST'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/v1/orders/cancel_and_new', 'POST'): UpbitApiCategory.EXCHANGE_ORDER,

        # 일괄 취소 (EXCHANGE_CANCEL_ALL)
        ('/orders/cancel_all', 'DELETE'): UpbitApiCategory.EXCHANGE_CANCEL_ALL,
        ('/v1/orders/cancel_all', 'DELETE'): UpbitApiCategory.EXCHANGE_CANCEL_ALL,
        ('/orders/open', 'DELETE'): UpbitApiCategory.EXCHANGE_CANCEL_ALL,
        ('/v1/orders/open', 'DELETE'): UpbitApiCategory.EXCHANGE_CANCEL_ALL,
    }

    def __init__(self, user_type: str = "anonymous"):
        """Rate Limiter 초기화"""
        self.user_type = user_type
        self.client_id = f"upbit_v2_{user_type}_{id(self)}"

        # 카테고리별 Limiter 생성 (전역 공유)
        self.limiters: Dict[UpbitApiCategory, CloudflareSlidingWindowWithWarmupAndPRG] = {}
        for category, rule in self.UPBIT_RULES.items():
            limiter_id = f"global_{category.value}"

            # 전역에서 기존 Limiter 확인
            existing_limiter = CloudflareSlidingWindowWithWarmupAndPRG.get_global_limiter(limiter_id)
            if existing_limiter:
                self.limiters[category] = existing_limiter
                logger.debug(f"재사용 전역 Limiter: {limiter_id}")
            else:
                self.limiters[category] = CloudflareSlidingWindowWithWarmupAndPRG(
                    windows=rule.windows,
                    limiter_id=limiter_id
                )
                logger.debug(f"새 전역 Limiter 생성: {limiter_id}")

        # 통계
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'category_counts': {cat.value: 0 for cat in UpbitApiCategory}
        }

    def resolve_category(self, endpoint: str, method: str = 'GET') -> UpbitApiCategory:
        """엔드포인트 → 카테고리 해결 (Legacy 호환)"""
        method_upper = method.upper()

        # 1. 특수 메서드 매핑 우선 확인
        special_key = (endpoint, method_upper)
        if special_key in self.SPECIAL_METHOD_MAPPINGS:
            return self.SPECIAL_METHOD_MAPPINGS[special_key]

        # 2. 정확한 엔드포인트 매핑
        if endpoint in self.ENDPOINT_MAPPINGS:
            return self.ENDPOINT_MAPPINGS[endpoint]

        # 3. 패턴 매칭 (prefix)
        for pattern, category in self.ENDPOINT_MAPPINGS.items():
            if endpoint.startswith(pattern):
                return category

        # 4. 기본값: 시세 조회 (가장 안전한 선택)
        return UpbitApiCategory.QUOTATION

    async def acquire(self, endpoint: str, method: str = 'GET') -> None:
        """Rate Limit 토큰 획득 (항상 성공)"""
        # 카테고리 결정
        category = self.resolve_category(endpoint, method)

        # 통계 업데이트
        self.stats['total_requests'] += 1
        self.stats['category_counts'][category.value] += 1

        # Rate Limit 획득 (항상 성공)
        limiter = self.limiters[category]
        success = await limiter.acquire()

        if success:
            self.stats['successful_requests'] += 1
        else:
            # 이론적으로는 발생하지 않음 (항상 성공)
            self.stats['failed_requests'] += 1
            logger.warning(f"Rate limiter returned failure (unexpected): {category.value}")

        logger.debug(f"Rate limit acquired: {endpoint} → {category.value}")

    async def acquire_with_status(self, endpoint: str, method: str = 'GET') -> Tuple[bool, Dict]:
        """상세 상태 정보와 함께 토큰 획득"""
        # 카테고리 결정
        category = self.resolve_category(endpoint, method)

        # 통계 업데이트
        self.stats['total_requests'] += 1
        self.stats['category_counts'][category.value] += 1

        # Rate Limit 획득 (상태 포함)
        limiter = self.limiters[category]
        success, status = await limiter.acquire_with_status()

        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1

        # 상태에 카테고리 정보 추가
        status['category'] = category.value
        status['endpoint'] = endpoint

        return success, status

    def get_status(self) -> Dict[str, Any]:
        """현재 Rate Limiter 상태 조회 (Legacy 호환)"""
        now = time.time()
        status = {}

        for category, limiter in self.limiters.items():
            rule = self.UPBIT_RULES[category]
            usage = limiter.get_usage_info(now)

            # 주요 윈도우 정보
            main_window = usage.get('window_0', {})
            strictest_rps = rule.get_strictest_rps()

            status[category.value] = {
                'current': main_window.get('current', 0),
                'limit': main_window.get('limit', 0),
                'usage_percent': main_window.get('usage_percent', 0),
                'rule_name': rule.name,
                'strictest_rps': f"{strictest_rps:.2f}",
                'windows_count': len(rule.windows)  # 멀티 윈도우 정보
            }

        return {
            'client_id': self.client_id,
            'user_type': self.user_type,
            'architecture': 'legacy_with_warmup',
            'global_sharing': True,  # 전역 공유 지원
            'categories': status,
            'statistics': self.stats,
            'total_limiters': len(self.limiters)
        }

    @classmethod
    def get_global_status(cls) -> Dict[str, Any]:
        """모든 전역 Limiter 상태 조회"""
        return CloudflareSlidingWindowWithWarmupAndPRG.get_all_global_usage()


class RateLimitExceededException(Exception):
    """Rate Limit 초과 예외 (Legacy 호환)"""

    def __init__(self, message: str, retry_after: float = 0.0):
        super().__init__(message)
        self.retry_after = retry_after


# ================================================================
# 팩토리 함수들 (Legacy 호환)
# ================================================================

def create_upbit_public_limiter() -> UpbitRateLimiterV2:
    """업비트 공개 API 전용 Rate Limiter 생성"""
    return UpbitRateLimiterV2(user_type="anonymous")


def create_upbit_private_limiter(client_id: str) -> UpbitRateLimiterV2:
    """업비트 프라이빗 API 전용 Rate Limiter 생성"""
    return UpbitRateLimiterV2(user_type="authenticated")


def create_upbit_unified_limiter(access_key: Optional[str] = None) -> UpbitRateLimiterV2:
    """업비트 통합 Rate Limiter 생성 (권장)"""
    user_type = "authenticated" if access_key else "anonymous"
    return UpbitRateLimiterV2(user_type=user_type)
