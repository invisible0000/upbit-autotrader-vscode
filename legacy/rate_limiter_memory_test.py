"""
Rate Limiter 장시간 운영 안정성 테스트
메모리 누수, 성능 저하, 자동 정리 로직 검증
"""

import asyncio
import time
import gc
import psutil
import tracemalloc
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import (
    UpbitRateLimiter, RateLimitStrategy
)


@dataclass
class MemorySnapshot:
    """메모리 스냅샷"""
    timestamp: datetime
    rss_mb: float
    vms_mb: float
    percent: float
    traced_current: int
    traced_peak: int
    gc_stats: Dict[str, int]


@dataclass
class LongRunMetrics:
    """장시간 운영 메트릭"""
    strategy: str
    test_duration_hours: float
    total_requests: int
    avg_rps: float
    memory_snapshots: List[MemorySnapshot] = field(default_factory=list)
    memory_growth_mb: float = 0.0
    memory_leak_detected: bool = False
    performance_degradation: float = 0.0
    max_acquire_time_ms: float = 0.0
    gc_pressure_score: float = 0.0


class LongRunningStabilityTester:
    """장시간 운영 안정성 테스터"""

    def __init__(self, strategy: RateLimitStrategy, snapshot_interval_minutes: int = 5):
        self.strategy = strategy
        self.snapshot_interval = snapshot_interval_minutes * 60  # 초 변환
        self.limiter = UpbitRateLimiter(strategy=strategy, client_id=f"longrun_{strategy.name}")
        self.process = psutil.Process()

        self.snapshots: List[MemorySnapshot] = []
        self.start_time = None
        self.total_requests = 0
        self.acquire_times = []

    def take_memory_snapshot(self) -> MemorySnapshot:
        """현재 메모리 상태 스냅샷"""
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()

        # tracemalloc 정보
        try:
            traced_current, traced_peak = tracemalloc.get_traced_memory()
        except:
            traced_current = traced_peak = 0

        # GC 통계
        gc_stats = gc.get_stats()
        total_collections = sum(stat['collections'] for stat in gc_stats)
        total_collected = sum(stat['collected'] for stat in gc_stats)
        total_uncollectable = sum(stat['uncollectable'] for stat in gc_stats)

        snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            rss_mb=memory_info.rss / 1024 / 1024,
            vms_mb=memory_info.vms / 1024 / 1024,
            percent=memory_percent,
            traced_current=traced_current,
            traced_peak=traced_peak,
            gc_stats={
                'collections': total_collections,
                'collected': total_collected,
                'uncollectable': total_uncollectable
            }
        )

        self.snapshots.append(snapshot)
        return snapshot

    def analyze_memory_trend(self) -> Dict[str, float]:
        """메모리 사용 트렌드 분석"""
        if len(self.snapshots) < 3:
            return {'growth_rate': 0.0, 'leak_probability': 0.0}

        # 초기 vs 최근 메모리 비교 (처음 20% vs 마지막 20%)
        n = len(self.snapshots)
        initial_avg = sum(s.rss_mb for s in self.snapshots[:max(1, n//5)]) / max(1, n//5)
        recent_avg = sum(s.rss_mb for s in self.snapshots[-max(1, n//5):]) / max(1, n//5)

        growth_mb = recent_avg - initial_avg
        growth_rate = growth_mb / initial_avg * 100 if initial_avg > 0 else 0

        # 메모리 누수 가능성 평가
        # 1. 지속적인 증가 패턴 확인
        increasing_count = 0
        for i in range(1, len(self.snapshots)):
            if self.snapshots[i].rss_mb > self.snapshots[i-1].rss_mb:
                increasing_count += 1

        increasing_ratio = increasing_count / (len(self.snapshots) - 1)

        # 2. GC 압박도 확인
        gc_pressure = 0.0
        if len(self.snapshots) >= 2:
            initial_gc = self.snapshots[0].gc_stats['collections']
            final_gc = self.snapshots[-1].gc_stats['collections']
            gc_rate = (final_gc - initial_gc) / len(self.snapshots)
            gc_pressure = min(gc_rate / 10.0, 1.0)  # 정규화

        # 누수 확률 계산 (성장률 + 증가패턴 + GC압박)
        leak_probability = min((growth_rate * 0.4 + increasing_ratio * 0.4 + gc_pressure * 0.2), 1.0)

        return {
            'growth_rate': growth_rate,
            'growth_mb': growth_mb,
            'increasing_ratio': increasing_ratio,
            'gc_pressure': gc_pressure,
            'leak_probability': leak_probability
        }

    async def run_stability_test(self, duration_hours: float = 1.0, target_rps: int = 50) -> LongRunMetrics:
        """장시간 안정성 테스트 실행"""

        print(f"\n⏰ {self.strategy.name} 장시간 테스트 시작")
        print(f"   지속시간: {duration_hours}시간, 목표 RPS: {target_rps}")

        tracemalloc.start()
        self.start_time = time.perf_counter()
        end_time = self.start_time + (duration_hours * 3600)

        # 초기 스냅샷
        initial_snapshot = self.take_memory_snapshot()
        print(f"   초기 메모리: {initial_snapshot.rss_mb:.1f}MB")

        last_snapshot_time = self.start_time
        request_interval = 1.0 / target_rps

        rps_samples = []  # 성능 저하 추적용

        while time.perf_counter() < end_time:
            loop_start = time.perf_counter()

            # Rate Limiter 요청
            acquire_start = time.perf_counter()
            await self.limiter.acquire('/market/all', 'GET')
            acquire_end = time.perf_counter()

            acquire_time = (acquire_end - acquire_start) * 1000
            self.acquire_times.append(acquire_time)
            self.total_requests += 1

            # 📸 주기적 스냅샷 (5분마다)
            current_time = time.perf_counter()
            if current_time - last_snapshot_time >= self.snapshot_interval:
                snapshot = self.take_memory_snapshot()
                elapsed_hours = (current_time - self.start_time) / 3600
                current_rps = self.total_requests / (current_time - self.start_time)

                print(f"   {elapsed_hours:.1f}h: {self.total_requests:,}회 | "
                      f"{current_rps:.1f} RPS | {snapshot.rss_mb:.1f}MB | "
                      f"평균대기: {sum(self.acquire_times[-1000:]) / min(1000, len(self.acquire_times)):.2f}ms")

                rps_samples.append(current_rps)
                last_snapshot_time = current_time

                # 🧹 메모리 정리 (선택적)
                if len(self.acquire_times) > 10000:
                    self.acquire_times = self.acquire_times[-5000:]  # 최근 5000개만 유지

            # 타이밍 제어
            loop_end = time.perf_counter()
            elapsed = loop_end - loop_start
            if elapsed < request_interval:
                await asyncio.sleep(request_interval - elapsed)

        # 최종 분석
        final_snapshot = self.take_memory_snapshot()
        final_time = time.perf_counter()
        actual_duration_hours = (final_time - self.start_time) / 3600
        avg_rps = self.total_requests / (final_time - self.start_time)

        # 메모리 트렌드 분석
        memory_analysis = self.analyze_memory_trend()

        # 성능 저하 분석
        performance_degradation = 0.0
        if len(rps_samples) >= 3:
            initial_rps = sum(rps_samples[:len(rps_samples)//3]) / (len(rps_samples)//3)
            final_rps = sum(rps_samples[-len(rps_samples)//3:]) / (len(rps_samples)//3)
            performance_degradation = (initial_rps - final_rps) / initial_rps * 100 if initial_rps > 0 else 0

        tracemalloc.stop()

        print(f"✅ {self.strategy.name} 장시간 테스트 완료")
        print(f"   총 {self.total_requests:,}회 요청, 평균 {avg_rps:.1f} RPS")
        print(f"   메모리 증가: {memory_analysis['growth_mb']:.1f}MB ({memory_analysis['growth_rate']:.1f}%)")
        print(f"   누수 확률: {memory_analysis['leak_probability']*100:.1f}%")

        return LongRunMetrics(
            strategy=self.strategy.name,
            test_duration_hours=actual_duration_hours,
            total_requests=self.total_requests,
            avg_rps=avg_rps,
            memory_snapshots=self.snapshots,
            memory_growth_mb=memory_analysis['growth_mb'],
            memory_leak_detected=memory_analysis['leak_probability'] > 0.7,
            performance_degradation=performance_degradation,
            max_acquire_time_ms=max(self.acquire_times) if self.acquire_times else 0,
            gc_pressure_score=memory_analysis['gc_pressure']
        )


async def run_memory_leak_detection():
    """메모리 누수 탐지 테스트"""

    print("=" * 80)
    print("🔍 Rate Limiter 메모리 누수 탐지 테스트")
    print("=" * 80)

    # 테스트할 전략들 (의심스러운 것들 우선)
    test_strategies = [
        RateLimitStrategy.SMART_RESPONSE_ADAPTIVE,    # 복잡한 적응 로직
        RateLimitStrategy.CLOUDFLARE_SLIDING_WINDOW,  # 슬라이딩 윈도우
        RateLimitStrategy.HYBRID_FAST,                # 하이브리드 로직
        RateLimitStrategy.AIOLIMITER_OPTIMIZED        # 최적화된 버전
    ]

    results = []

    for strategy in test_strategies:
        try:
            tester = LongRunningStabilityTester(strategy, snapshot_interval_minutes=2)

            # 🎯 1시간 연속 테스트 (실제로는 더 긴 시간도 가능)
            result = await tester.run_stability_test(
                duration_hours=0.5,  # 30분 테스트 (시연용)
                target_rps=100       # 적당한 부하
            )

            results.append(result)

            # 전략 간 휴식
            await asyncio.sleep(5)
            gc.collect()

        except Exception as e:
            print(f"❌ {strategy.name} 장시간 테스트 실패: {e}")

    # 📊 종합 분석 결과
    print("\n" + "=" * 90)
    print("🔬 메모리 누수 및 안정성 분석 결과")
    print("=" * 90)

    print("\n전략명                    | 지속시간 | 총요청  | 평균RPS | 메모리증가 | 누수위험 | 성능저하")
    print("-" * 90)

    for result in results:
        name = result.strategy[:22].ljust(22)
        duration = f"{result.test_duration_hours:.1f}h".rjust(8)
        requests = f"{result.total_requests:,}".rjust(7)
        rps = f"{result.avg_rps:.1f}".rjust(7)
        memory = f"{result.memory_growth_mb:+.1f}MB".rjust(10)
        leak = "🚨높음" if result.memory_leak_detected else "✅낮음"
        leak = leak.rjust(8)
        perf = f"{result.performance_degradation:+.1f}%".rjust(8)

        print(f"{name} | {duration} | {requests} | {rps} | {memory} | {leak} | {perf}")

    # 🏆 안정성 순위
    if results:
        print(f"\n🏆 안정성 평가:")

        # 메모리 효율성 (적은 증가가 좋음)
        best_memory = min(results, key=lambda x: abs(x.memory_growth_mb))
        print(f"   메모리 효율성: {best_memory.strategy} ({best_memory.memory_growth_mb:+.1f}MB)")

        # 성능 안정성 (저하가 적은 것이 좋음)
        best_performance = min(results, key=lambda x: abs(x.performance_degradation))
        print(f"   성능 안정성: {best_performance.strategy} ({best_performance.performance_degradation:+.1f}%)")

        # 전체 안정성 점수
        safe_strategies = [r for r in results if not r.memory_leak_detected]
        if safe_strategies:
            most_stable = min(safe_strategies,
                            key=lambda x: abs(x.memory_growth_mb) + abs(x.performance_degradation))
            print(f"   전체 안정성: {most_stable.strategy}")

        # ⚠️ 주의 대상
        risky_strategies = [r for r in results if r.memory_leak_detected]
        if risky_strategies:
            print(f"\n⚠️  메모리 누수 의심 전략: {', '.join(r.strategy for r in risky_strategies)}")


if __name__ == "__main__":
    print(f"💻 시스템 환경:")
    print(f"   CPU: {psutil.cpu_count()}코어")
    print(f"   메모리: {psutil.virtual_memory().total / 1024**3:.1f}GB")
    print(f"   현재 Python 메모리: {psutil.Process().memory_info().rss / 1024**2:.1f}MB")

    asyncio.run(run_memory_leak_detection())
