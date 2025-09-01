"""
업비트 Rate Limiter 동적 조정 기능 향상 제안

현재 Rate Limiter에 추가할 수 있는 고급 동적 조정 기능들:
1. 429 빈도 기반 자동 Rate Limit 감소
2. 시간 기반 점진적 복구
3. 통계 기반 적응형 조정
4. 실시간 모니터링 및 알림
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum


class AdaptiveStrategy(Enum):
    """적응형 전략 타입"""
    CONSERVATIVE = "conservative"  # 안전 우선, 느린 복구
    BALANCED = "balanced"         # 균형, 중간 복구
    AGGRESSIVE = "aggressive"     # 성능 우선, 빠른 복구


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
    recovery_delay: float = 300.0         # 5분 후 복구 시작
    recovery_step: float = 0.1            # 10%씩 점진적 복구
    recovery_interval: float = 60.0       # 1분마다 복구 단계

    # 전략
    strategy: AdaptiveStrategy = AdaptiveStrategy.BALANCED


@dataclass
class GroupStats:
    """그룹별 통계"""
    total_requests: int = 0
    error_429_count: int = 0
    error_429_history: List[float] = field(default_factory=list)  # 429 발생 시간들
    current_rate_ratio: float = 1.0       # 현재 rate 비율 (1.0 = 100%)
    last_reduction_time: Optional[float] = None
    last_recovery_time: Optional[float] = None

    def add_429_error(self, timestamp: float):
        """429 에러 기록"""
        self.error_429_count += 1
        self.error_429_history.append(timestamp)

        # 오래된 기록 정리 (1시간 이상)
        cutoff = timestamp - 3600.0
        self.error_429_history = [t for t in self.error_429_history if t > cutoff]


class EnhancedUpbitRateLimiter:
    """
    동적 조정 기능이 추가된 업비트 Rate Limiter

    기존 UpbitGCRARateLimiter를 래핑하여 동적 기능 추가
    """

    def __init__(self, base_limiter, config: DynamicConfig = None):
        self.base_limiter = base_limiter
        self.config = config or DynamicConfig()

        # 그룹별 통계 및 동적 상태
        self.group_stats: Dict[str, GroupStats] = {}
        self._adjustment_lock = asyncio.Lock()

        # 백그라운드 복구 태스크
        self._recovery_task = None
        self._running = True

        # 알림 콜백
        self.on_rate_reduced: Optional[Callable] = None
        self.on_rate_recovered: Optional[Callable] = None

    async def start_recovery_monitor(self):
        """백그라운드 복구 모니터링 시작"""
        if self._recovery_task is None:
            self._recovery_task = asyncio.create_task(self._recovery_loop())

    async def stop_recovery_monitor(self):
        """백그라운드 모니터링 중지"""
        self._running = False
        if self._recovery_task:
            self._recovery_task.cancel()
            try:
                await self._recovery_task
            except asyncio.CancelledError:
                pass

    async def acquire(self, endpoint: str, method: str = 'GET', **kwargs):
        """Rate Limit 획득 (동적 조정 포함)"""
        group_key = self._get_group_key(endpoint, method)

        # 통계 초기화
        if group_key not in self.group_stats:
            self.group_stats[group_key] = GroupStats()

        stats = self.group_stats[group_key]
        stats.total_requests += 1

        try:
            # 기존 Rate Limiter 호출
            await self.base_limiter.acquire(endpoint, method, **kwargs)

        except Exception as e:
            # 429 에러 감지 및 처리
            if "429" in str(e) or "Rate limit" in str(e):
                await self._handle_429_error(group_key, stats)
            raise

    async def _handle_429_error(self, group_key: str, stats: GroupStats):
        """429 에러 처리 및 동적 조정"""
        now = time.monotonic()
        stats.add_429_error(now)

        async with self._adjustment_lock:
            # 최근 윈도우 내 429 에러 수 확인
            recent_errors = [
                t for t in stats.error_429_history
                if now - t <= self.config.error_429_window
            ]

            # 임계치 초과 시 Rate Limit 감소
            if len(recent_errors) >= self.config.error_429_threshold:
                await self._reduce_rate_limit(group_key, stats, now)

    async def _reduce_rate_limit(self, group_key: str, stats: GroupStats, timestamp: float):
        """Rate Limit 감소"""
        # 이미 최소 비율에 도달한 경우
        if stats.current_rate_ratio <= self.config.min_ratio:
            return

        # Rate 감소 적용
        old_ratio = stats.current_rate_ratio
        stats.current_rate_ratio *= self.config.reduction_ratio
        stats.current_rate_ratio = max(stats.current_rate_ratio, self.config.min_ratio)
        stats.last_reduction_time = timestamp

        # 실제 Rate Limiter 설정 업데이트
        await self._update_rate_limiter_config(group_key, stats.current_rate_ratio)

        # 알림
        if self.on_rate_reduced:
            self.on_rate_reduced(group_key, old_ratio, stats.current_rate_ratio)

        print(f"🔻 Rate Limit 감소: {group_key} {old_ratio:.2f} → {stats.current_rate_ratio:.2f}")

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
            for group_key, stats in self.group_stats.items():
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
                        await self._recover_rate_limit(group_key, stats, now)

    async def _recover_rate_limit(self, group_key: str, stats: GroupStats, timestamp: float):
        """Rate Limit 점진적 복구"""
        old_ratio = stats.current_rate_ratio
        stats.current_rate_ratio = min(1.0, stats.current_rate_ratio + self.config.recovery_step)
        stats.last_recovery_time = timestamp

        # 실제 Rate Limiter 설정 업데이트
        await self._update_rate_limiter_config(group_key, stats.current_rate_ratio)

        # 알림
        if self.on_rate_recovered:
            self.on_rate_recovered(group_key, old_ratio, stats.current_rate_ratio)

        print(f"🔺 Rate Limit 복구: {group_key} {old_ratio:.2f} → {stats.current_rate_ratio:.2f}")

    async def _update_rate_limiter_config(self, group_key: str, ratio: float):
        """실제 Rate Limiter 설정 업데이트"""
        # TODO: 기존 Rate Limiter의 _GROUP_CONFIGS를 동적으로 수정
        # 현재는 로그만 출력
        print(f"📊 {group_key} Rate Limit 업데이트: {ratio:.2f} 배율")

    def _get_group_key(self, endpoint: str, method: str) -> str:
        """엔드포인트/메서드를 그룹 키로 변환"""
        # 기존 Rate Limiter의 그룹 매핑 로직 활용
        group = self.base_limiter._get_rate_limit_group(endpoint, method)
        return f"{group.value}_{method}"

    def get_dynamic_status(self) -> Dict:
        """동적 조정 상태 반환"""
        now = time.monotonic()

        return {
            'config': {
                'strategy': self.config.strategy.value,
                'error_threshold': self.config.error_429_threshold,
                'reduction_ratio': self.config.reduction_ratio,
                'recovery_delay': self.config.recovery_delay,
            },
            'groups': {
                group_key: {
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
                for group_key, stats in self.group_stats.items()
            }
        }


# =============================================================================
# 사용 예시
# =============================================================================

async def demo_dynamic_rate_limiter():
    """동적 Rate Limiter 데모"""
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import get_global_rate_limiter

    # 기존 Rate Limiter 획득
    base_limiter = await get_global_rate_limiter()

    # 동적 기능 추가
    config = DynamicConfig(
        error_429_threshold=2,      # 2번 429 발생하면 제한
        reduction_ratio=0.7,        # 70%로 감소
        recovery_delay=180.0,       # 3분 후 복구 시작
        strategy=AdaptiveStrategy.BALANCED
    )

    enhanced_limiter = EnhancedUpbitRateLimiter(base_limiter, config)

    # 알림 콜백 설정
    enhanced_limiter.on_rate_reduced = lambda group, old, new: print(
        f"🚨 {group} Rate Limit 감소: {old:.1%} → {new:.1%}"
    )
    enhanced_limiter.on_rate_recovered = lambda group, old, new: print(
        f"✅ {group} Rate Limit 복구: {old:.1%} → {new:.1%}"
    )

    # 백그라운드 모니터링 시작
    await enhanced_limiter.start_recovery_monitor()

    try:
        # 실제 사용
        await enhanced_limiter.acquire('/market/all', 'GET')

        # 상태 확인
        status = enhanced_limiter.get_dynamic_status()
        print("동적 조정 상태:", status)

    finally:
        await enhanced_limiter.stop_recovery_monitor()


if __name__ == "__main__":
    print("🔄 동적 Rate Limiter 기능 향상 제안")
    print("=" * 60)
    print()
    print("✅ 현재 구현된 기능:")
    print("   - 429 응답 시 그룹별 패널티")
    print("   - 지수 백오프 + 지터")
    print("   - 그룹별 독립적 제한")
    print()
    print("🚀 추가 가능한 고급 기능:")
    print("   - 429 빈도 기반 자동 Rate Limit 감소")
    print("   - 시간 기반 점진적 복구")
    print("   - 통계 기반 적응형 조정")
    print("   - 실시간 모니터링 및 알림")
    print("   - 전략별 조정 (Conservative/Balanced/Aggressive)")
    print()
    print("💡 구현 방식:")
    print("   - 기존 Rate Limiter 래핑 (호환성 유지)")
    print("   - 백그라운드 복구 모니터링")
    print("   - 그룹별 독립적 통계 및 조정")
    print("   - 콜백 기반 알림 시스템")
