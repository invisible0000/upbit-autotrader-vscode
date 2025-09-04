"""
동적 조정 기능이 추가된 업비트 Rate Limiter 래퍼
- 기존 Rate Limiter를 래핑하여 동적 조정 기능 추가
- 429 발생 시 자동 Rate Limit 감소
- 시간 기반 점진적 복구
- 전역 공유 구조 유지
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import (
    get_global_rate_limiter, UpbitRateLimitGroup, GCRAConfig
)


class AdaptiveStrategy(Enum):
    """적응형 전략"""
    CONSERVATIVE = "conservative"  # 안전 우선
    BALANCED = "balanced"         # 균형
    AGGRESSIVE = "aggressive"     # 성능 우선


@dataclass
class DynamicConfig:
    """동적 조정 설정"""
    # 429 감지 임계치
    error_429_threshold: int = 3          # 연속 429 몇 번이면 제한 강화
    error_429_window: float = 60.0        # 임계치 체크 윈도우(초)

    # Rate Limit 조정 비율
    reduction_ratio: float = 0.8          # 429 발생 시 80%로 감소
    min_ratio: float = 0.5                # 최소 50%까지만 감소

    # 복구 설정
    recovery_delay: float = 180.0         # 3분 후 복구 시작
    recovery_step: float = 0.1            # 10%씩 점진적 복구
    recovery_interval: float = 30.0       # 30초마다 복구 단계

    # 전략
    strategy: AdaptiveStrategy = AdaptiveStrategy.BALANCED


@dataclass
class GroupStats:
    """그룹별 통계"""
    total_requests: int = 0
    error_429_count: int = 0
    error_429_history: List[float] = field(default_factory=list)
    current_rate_ratio: float = 1.0
    last_reduction_time: Optional[float] = None
    last_recovery_time: Optional[float] = None
    original_configs: Optional[List[GCRAConfig]] = None

    def add_429_error(self, timestamp: float):
        """429 에러 기록"""
        self.error_429_count += 1
        self.error_429_history.append(timestamp)

        # 1시간 이상 된 기록 정리
        cutoff = timestamp - 3600.0
        self.error_429_history = [t for t in self.error_429_history if t > cutoff]


class DynamicUpbitRateLimiter:
    """동적 조정 기능이 추가된 업비트 Rate Limiter"""

    def __init__(self, config: Optional[DynamicConfig] = None):
        self.config = config or DynamicConfig()
        self.group_stats: Dict[UpbitRateLimitGroup, GroupStats] = {}
        self._base_limiter = None
        self._adjustment_lock = asyncio.Lock()
        self._recovery_task = None
        self._running = True

        # 알림 콜백
        self.on_rate_reduced: Optional[Callable] = None
        self.on_rate_recovered: Optional[Callable] = None
        self.on_429_detected: Optional[Callable] = None

        print("🔄 동적 Rate Limiter 초기화 완료")

    async def get_base_limiter(self):
        """기존 Rate Limiter 획득"""
        if self._base_limiter is None:
            self._base_limiter = await get_global_rate_limiter()
            # 원본 설정 백업
            await self._backup_original_configs()
        return self._base_limiter

    async def _backup_original_configs(self):
        """원본 설정 백업"""
        for group in UpbitRateLimitGroup:
            if group not in self.group_stats:
                self.group_stats[group] = GroupStats()

            # 원본 설정 저장
            original_configs = self._base_limiter._GROUP_CONFIGS.get(group, [])
            self.group_stats[group].original_configs = original_configs.copy()

    async def start_monitoring(self):
        """백그라운드 모니터링 시작"""
        if self._recovery_task is None:
            self._recovery_task = asyncio.create_task(self._recovery_loop())
            print("🔍 동적 조정 모니터링 시작")

    async def stop_monitoring(self):
        """모니터링 중지 (개선된 정리 - 이벤트 루프 안전성)"""
        self._running = False
        if self._recovery_task and not self._recovery_task.done():
            try:
                # 현재 이벤트 루프 확인
                current_loop = asyncio.get_running_loop()
                task_loop = getattr(self._recovery_task, '_loop', None)

                if task_loop is not None and task_loop != current_loop:
                    print("⚠️  다른 이벤트 루프의 Task 감지 - 안전하게 스킵")
                    self._recovery_task = None
                    return

                # 같은 루프의 Task이면 정상 취소
                self._recovery_task.cancel()
                await asyncio.wait_for(self._recovery_task, timeout=2.0)

            except (asyncio.CancelledError, asyncio.TimeoutError):
                # 정상적인 정리 또는 타임아웃
                pass
            except Exception as e:
                print(f"⚠️  모니터링 정리 중 오류: {e}")
            finally:
                self._recovery_task = None
        print("⏹️  동적 조정 모니터링 중지")

    async def acquire(self, endpoint: str, method: str = 'GET', **kwargs):
        """Rate Limit 획득 (동적 조정 포함)"""
        limiter = await self.get_base_limiter()
        group = limiter._get_rate_limit_group(endpoint, method)

        # 통계 초기화
        if group not in self.group_stats:
            self.group_stats[group] = GroupStats()

        stats = self.group_stats[group]
        stats.total_requests += 1

        try:
            # 기존 Rate Limiter 호출
            await limiter.acquire(endpoint, method, **kwargs)

        except Exception as e:
            # 실제 429 에러만 감지 (TimeoutError는 제외)
            error_str = str(e)
            error_type = str(type(e).__name__)
            is_real_429 = "429" in error_str and "HTTP" in error_str and "TimeoutError" not in error_type

            if is_real_429:
                await self._handle_429_error(group, stats)

                # 429 감지 콜백
                if self.on_429_detected:
                    self.on_429_detected(group, endpoint, str(e))
            raise

    async def _handle_429_error(self, group: UpbitRateLimitGroup, stats: GroupStats):
        """429 에러 처리 및 동적 조정"""
        now = time.monotonic()
        stats.add_429_error(now)

        print(f"⚠️  429 에러 감지: {group.value} (총 {stats.error_429_count}회)")

        async with self._adjustment_lock:
            # 최근 윈도우 내 429 에러 수 확인
            recent_errors = [
                t for t in stats.error_429_history
                if now - t <= self.config.error_429_window
            ]

            print(f"📊 최근 {self.config.error_429_window}초 내 429 에러: {len(recent_errors)}회")

            # 임계치 초과 시 Rate Limit 감소
            if len(recent_errors) >= self.config.error_429_threshold:
                await self._reduce_rate_limit(group, stats, now)

    async def _reduce_rate_limit(self, group: UpbitRateLimitGroup, stats: GroupStats, timestamp: float):
        """Rate Limit 감소"""
        # 이미 최소 비율에 도달한 경우
        if stats.current_rate_ratio <= self.config.min_ratio:
            print(f"⚠️  {group.value} 이미 최소 비율({self.config.min_ratio:.0%})에 도달")
            return

        # Rate 감소 적용
        old_ratio = stats.current_rate_ratio
        stats.current_rate_ratio *= self.config.reduction_ratio
        stats.current_rate_ratio = max(stats.current_rate_ratio, self.config.min_ratio)
        stats.last_reduction_time = timestamp

        # 실제 Rate Limiter 설정 업데이트
        await self._update_rate_limiter_config(group, stats.current_rate_ratio)

        # 알림
        if self.on_rate_reduced:
            self.on_rate_reduced(group, old_ratio, stats.current_rate_ratio)

        print(f"🔻 Rate Limit 감소 적용: {group.value} {old_ratio:.1%} → {stats.current_rate_ratio:.1%}")

    async def _recovery_loop(self):
        """백그라운드 복구 루프"""
        while self._running:
            try:
                await asyncio.sleep(self.config.recovery_interval)
                await self._check_recovery()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"복구 모니터링 오류: {e}")

    async def _check_recovery(self):
        """복구 가능한 그룹들 확인 및 복구"""
        now = time.monotonic()

        async with self._adjustment_lock:
            for group, stats in self.group_stats.items():
                # 복구 조건 확인
                if (stats.current_rate_ratio < 1.0 and
                    stats.last_reduction_time and
                    now - stats.last_reduction_time >= self.config.recovery_delay):

                    # 최근 429 에러 없는지 확인
                    recent_errors = [
                        t for t in stats.error_429_history
                        if now - t <= self.config.recovery_delay
                    ]

                    if len(recent_errors) == 0:
                        await self._recover_rate_limit(group, stats, now)

    async def _recover_rate_limit(self, group: UpbitRateLimitGroup, stats: GroupStats, timestamp: float):
        """Rate Limit 점진적 복구"""
        old_ratio = stats.current_rate_ratio
        stats.current_rate_ratio = min(1.0, stats.current_rate_ratio + self.config.recovery_step)
        stats.last_recovery_time = timestamp

        # 실제 Rate Limiter 설정 업데이트
        await self._update_rate_limiter_config(group, stats.current_rate_ratio)

        # 알림
        if self.on_rate_recovered:
            self.on_rate_recovered(group, old_ratio, stats.current_rate_ratio)

        print(f"🔺 Rate Limit 복구: {group.value} {old_ratio:.1%} → {stats.current_rate_ratio:.1%}")

    async def _update_rate_limiter_config(self, group: UpbitRateLimitGroup, ratio: float):
        """실제 Rate Limiter 설정 업데이트"""
        limiter = await self.get_base_limiter()
        stats = self.group_stats[group]

        if stats.original_configs:
            # 원본 설정에 비율 적용
            new_configs = []
            for original_config in stats.original_configs:
                # RPS 기반 설정의 경우
                if hasattr(original_config, 'T_seconds'):
                    new_rps = (1.0 / original_config.T_seconds) * ratio
                    new_config = GCRAConfig.from_rps(
                        new_rps,
                        burst_capacity=max(1, int(original_config.burst_capacity * ratio))
                    )
                    new_configs.append(new_config)

            # 전역 설정 업데이트
            limiter._GROUP_CONFIGS[group] = new_configs

            # 기존 컨트롤러들 재초기화
            from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import GCRA
            limiter._controllers[group] = [GCRA(config) for config in new_configs]

        print(f"⚙️  {group.value} 설정 업데이트 완료 (비율: {ratio:.1%})")

    def get_dynamic_status(self) -> Dict[str, Any]:
        """동적 조정 상태 반환"""
        now = time.monotonic()

        # 디버깅: config 상태 확인
        if not hasattr(self, 'config') or self.config is None:
            print("⚠️ DynamicUpbitRateLimiter.config가 None입니다!")
            return {'config': {}, 'groups': {}}

        return {
            'config': {
                'strategy': self.config.strategy.value,
                'error_threshold': self.config.error_429_threshold,
                'reduction_ratio': self.config.reduction_ratio,
                'recovery_delay': self.config.recovery_delay,
            },
            'groups': {
                group.value: {
                    'total_requests': stats.total_requests,
                    'error_429_count': stats.error_429_count,
                    'current_rate_ratio': stats.current_rate_ratio,
                    'recent_429_errors': len([
                        t for t in stats.error_429_history
                        if now - t <= self.config.error_429_window
                    ]),
                    'time_since_last_reduction':
                        now - stats.last_reduction_time if stats.last_reduction_time else None,
                    'time_since_last_recovery':
                        now - stats.last_recovery_time if stats.last_recovery_time else None,
                }
                for group, stats in self.group_stats.items()
            }
        }


# 전역 동적 Rate Limiter 인스턴스
_GLOBAL_DYNAMIC_LIMITER: Optional[DynamicUpbitRateLimiter] = None


async def get_dynamic_rate_limiter(config: Optional[DynamicConfig] = None) -> DynamicUpbitRateLimiter:
    """전역 동적 Rate Limiter 획득"""
    global _GLOBAL_DYNAMIC_LIMITER

    if _GLOBAL_DYNAMIC_LIMITER is None:
        _GLOBAL_DYNAMIC_LIMITER = DynamicUpbitRateLimiter(config)
        await _GLOBAL_DYNAMIC_LIMITER.start_monitoring()

    return _GLOBAL_DYNAMIC_LIMITER


# 편의 함수
async def dynamic_gate_rest_public(endpoint: str, method: str = 'GET') -> None:
    """동적 조정이 포함된 REST Public API 게이트"""
    limiter = await get_dynamic_rate_limiter()
    await limiter.acquire(endpoint, method)
