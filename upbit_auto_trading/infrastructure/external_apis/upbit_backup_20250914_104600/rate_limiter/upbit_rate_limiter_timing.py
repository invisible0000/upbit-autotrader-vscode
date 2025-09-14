"""
업비트 Rate Limiter 고정밀 타이밍 시스템
- 나노초 정밀도 시간 관리, Clock drift 보상
- 검색 키워드: timing, precision, nanosecond, clock
"""

import time
from decimal import Decimal, getcontext
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
import threading
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .upbit_rate_limiter_types import TimeConfig


# 고정밀 연산을 위한 Decimal 정밀도 설정 (Redis 방식)
getcontext().prec = 28  # 28자리 정밀도로 2048년까지 안전


class PrecisionTimeManager:
    """
    Redis-style 고정밀 시간 관리자

    주요 특징:
    1. 나노초 정밀도 시간 측정
    2. Decimal 기반 정확한 부동소수점 연산
    3. 2017년 기준 offset으로 숫자 크기 최소화
    4. Clock drift 자동 보상
    5. Thread-safe 시간 동기화
    """

    def __init__(self, config: Optional[TimeConfig] = None):
        self.config = config or TimeConfig()
        self.logger = create_component_logger("PrecisionTimeManager")

        # Clock drift 추적
        self._last_system_time = time.time()
        self._last_monotonic_time = time.monotonic()
        self._drift_offset = Decimal('0')
        self._drift_lock = threading.Lock()

        # 통계
        self._stats = {
            'total_time_calls': 0,
            'drift_corrections': 0,
            'max_precision_used': 0,
            'avg_call_overhead_ns': 0
        }

        # Decimal 컨텍스트 설정
        getcontext().prec = self.config.DECIMAL_PRECISION

        self.logger.info(f"⏰ 고정밀 시간 관리자 초기화 - 정밀도: {self.config.DECIMAL_PRECISION}자리")
        self.logger.info(f"📅 기준 시점: {datetime.fromtimestamp(self.config.EPOCH_OFFSET).isoformat()}")

    def get_precise_time(self) -> Decimal:
        """
        Redis 방식 고정밀 시간 획득

        Returns:
            Decimal: 2017년 기준 offset된 고정밀 시간 (초 단위)
        """
        call_start = time.perf_counter_ns()

        if self.config.NANOSECOND_PRECISION:
            # 나노초 정밀도
            now_ns = time.time_ns()
            now_seconds = Decimal(now_ns) / Decimal('1000000000')
        else:
            # 마이크로초 정밀도 (기존 방식)
            now_seconds = Decimal(str(time.time()))

        # Redis 방식: 기준점 offset 적용
        precise_time = now_seconds - Decimal(str(self.config.EPOCH_OFFSET))

        # Drift 보상 적용
        with self._drift_lock:
            if self._drift_offset != 0:
                precise_time += self._drift_offset

        # 통계 업데이트
        call_end = time.perf_counter_ns()
        call_overhead = call_end - call_start

        self._stats['total_time_calls'] += 1
        if self._stats['total_time_calls'] == 1:
            self._stats['avg_call_overhead_ns'] = call_overhead
        else:
            # 지수 이동 평균
            self._stats['avg_call_overhead_ns'] = (
                0.9 * self._stats['avg_call_overhead_ns'] + 0.1 * call_overhead
            )

        # 정밀도 추적
        precision_used = len(str(precise_time).split('.')[-1]) if '.' in str(precise_time) else 0
        self._stats['max_precision_used'] = max(self._stats['max_precision_used'], precision_used)

        return precise_time

    def get_monotonic_precise(self) -> Decimal:
        """
        모노토닉 고정밀 시간 (상대적 측정용)

        Returns:
            Decimal: 모노토닉 시간 (나노초 정밀도)
        """
        if self.config.NANOSECOND_PRECISION:
            mono_ns = time.monotonic_ns()
            return Decimal(mono_ns) / Decimal('1000000000')
        else:
            return Decimal(str(time.monotonic()))

    def calculate_wait_duration(self, target_time: Decimal) -> float:
        """
        정확한 대기 시간 계산

        Args:
            target_time: 목표 시점 (get_precise_time 형식)

        Returns:
            float: 대기해야 할 시간 (초, asyncio.sleep 호환)
        """
        current_time = self.get_precise_time()
        wait_duration = target_time - current_time

        # float로 변환 (asyncio.sleep 호환성)
        return float(max(Decimal('0'), wait_duration))

    def check_and_correct_drift(self) -> Optional[float]:
        """
        Clock drift 체크 및 보정

        Returns:
            Optional[float]: 감지된 드리프트 (초), None이면 정상
        """
        current_system = time.time()
        current_monotonic = time.monotonic()

        with self._drift_lock:
            # 이전 측정 이후 경과 시간 계산
            system_elapsed = current_system - self._last_system_time
            monotonic_elapsed = current_monotonic - self._last_monotonic_time

            # 드리프트 계산 (시스템 시간 vs 모노토닉 시간)
            drift = system_elapsed - monotonic_elapsed

            if abs(drift) > self.config.MAX_DRIFT_TOLERANCE:
                # 드리프트 감지 - 보정 적용
                self._drift_offset += Decimal(str(drift))
                self._stats['drift_corrections'] += 1

                self.logger.warning(f"🔄 Clock drift 보정: {drift:.6f}초, 누적: {float(self._drift_offset):.6f}초")

                # 기준점 업데이트
                self._last_system_time = current_system
                self._last_monotonic_time = current_monotonic

                return drift

            # 정상 범위 내 - 기준점만 업데이트
            if time.monotonic() - self._last_monotonic_time > self.config.DRIFT_CHECK_INTERVAL:
                self._last_system_time = current_system
                self._last_monotonic_time = current_monotonic

        return None

    def benchmark_precision(self, iterations: int = 1000) -> Dict[str, Any]:
        """
        시간 정밀도 벤치마크

        Args:
            iterations: 측정 반복 횟수

        Returns:
            Dict: 벤치마크 결과
        """
        self.logger.info(f"🔬 시간 정밀도 벤치마크 시작: {iterations}회 측정")

        # 연속 시간 측정
        times = []
        intervals = []

        for i in range(iterations):
            t = self.get_precise_time()
            times.append(t)

            if i > 0:
                interval = t - times[i-1]
                intervals.append(float(interval))

        # 통계 계산
        min_interval = min(intervals) if intervals else 0
        max_interval = max(intervals) if intervals else 0
        avg_interval = sum(intervals) / len(intervals) if intervals else 0

        # 정밀도 분석
        precisions = []
        for t in times:
            decimal_part = str(t).split('.')[-1] if '.' in str(t) else '0'
            precisions.append(len(decimal_part))

        return {
            'config': {
                'iterations': iterations,
                'nanosecond_precision': self.config.NANOSECOND_PRECISION,
                'decimal_precision': self.config.DECIMAL_PRECISION
            },
            'intervals': {
                'min_seconds': min_interval,
                'max_seconds': max_interval,
                'avg_seconds': avg_interval,
                'min_nanoseconds': min_interval * 1e9,
                'avg_nanoseconds': avg_interval * 1e9
            },
            'precision': {
                'min_decimal_places': min(precisions),
                'max_decimal_places': max(precisions),
                'avg_decimal_places': sum(precisions) / len(precisions)
            },
            'performance': {
                'avg_call_overhead_ns': self._stats['avg_call_overhead_ns'],
                'total_calls': self._stats['total_time_calls']
            }
        }

    def create_precise_timer(self, interval_seconds: float) -> Callable[[], bool]:
        """
        고정밀 타이머 생성

        Args:
            interval_seconds: 타이머 간격 (초)

        Returns:
            Callable: 호출할 때마다 간격이 지났는지 확인하는 함수
        """
        interval_decimal = Decimal(str(interval_seconds))
        last_trigger = self.get_precise_time()

        def check_timer() -> bool:
            nonlocal last_trigger
            current = self.get_precise_time()

            if current - last_trigger >= interval_decimal:
                last_trigger = current
                return True
            return False

        return check_timer

    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 조회"""
        current_drift = float(self._drift_offset) if self._drift_offset != 0 else 0.0

        return {
            'time_calls': self._stats['total_time_calls'],
            'drift_corrections': self._stats['drift_corrections'],
            'current_drift_seconds': current_drift,
            'max_precision_used': self._stats['max_precision_used'],
            'avg_call_overhead_ns': self._stats['avg_call_overhead_ns'],
            'config': {
                'nanosecond_precision': self.config.NANOSECOND_PRECISION,
                'decimal_precision': self.config.DECIMAL_PRECISION,
                'epoch_offset': self.config.EPOCH_OFFSET
            }
        }


class PreciseRateLimitTimer:
    """
    정밀 Rate Limit 타이밍 제어

    기존 GCRA와 통합하여 정확한 토큰 배출 타이밍 제공
    """

    def __init__(self, emission_interval: float, time_manager: Optional[PrecisionTimeManager] = None):
        self.emission_interval = Decimal(str(emission_interval))
        self.time_manager = time_manager or PrecisionTimeManager()

        # 다음 토큰 사용 가능 시점
        self._next_token_time = self.time_manager.get_precise_time()

        self.logger = create_component_logger("PreciseRateLimitTimer")

    def get_next_available_time(self) -> Decimal:
        """다음 토큰 사용 가능 시점"""
        return self._next_token_time

    def consume_token(self) -> bool:
        """토큰 소모 시도"""
        current_time = self.time_manager.get_precise_time()

        if current_time >= self._next_token_time:
            # 토큰 사용 가능 - 다음 시점 업데이트
            self._next_token_time = current_time + self.emission_interval
            return True
        else:
            # 토큰 사용 불가
            return False

    def calculate_wait_time(self) -> float:
        """필요한 대기 시간 계산 (초)"""
        return self.time_manager.calculate_wait_duration(self._next_token_time)

    def schedule_next_token(self) -> None:
        """다음 토큰 예약 (버스트 처리용)"""
        if self._next_token_time <= self.time_manager.get_precise_time():
            self._next_token_time = self.time_manager.get_precise_time() + self.emission_interval
        else:
            self._next_token_time += self.emission_interval


# 전역 시간 관리자
_global_time_manager: Optional[PrecisionTimeManager] = None


def get_global_time_manager() -> PrecisionTimeManager:
    """전역 고정밀 시간 관리자 획득"""
    global _global_time_manager

    if _global_time_manager is None:
        _global_time_manager = PrecisionTimeManager()

    return _global_time_manager


# 편의 함수들
def get_precise_now() -> Decimal:
    """현재 고정밀 시간"""
    return get_global_time_manager().get_precise_time()


def calculate_precise_wait(target_time: Decimal) -> float:
    """정확한 대기 시간 계산"""
    return get_global_time_manager().calculate_wait_duration(target_time)


def create_precision_timer(interval: float) -> Callable[[], bool]:
    """고정밀 타이머 생성"""
    return get_global_time_manager().create_precision_timer(interval)
