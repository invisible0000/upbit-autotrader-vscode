"""
Rate Limiter 최대 부하 스트레스 테스트
실제 API 없이 순수 알고리즘 성능 및 리소스 사용량 측정
"""

import asyncio
import time
import psutil
import gc
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import (
    UpbitRateLimiter, RateLimitStrategy
)


@dataclass
class StressTestMetrics:
    """스트레스 테스트 메트릭"""
    strategy: str
    total_requests: int
    duration_seconds: float
    rps_achieved: float
    cpu_usage_percent: float
    memory_usage_mb: float
    peak_memory_mb: float
    total_wait_time_ms: float
    avg_acquire_time_ms: float
    lock_contention_count: int
    gc_collections: int


class ResourceMonitor:
    """시스템 리소스 모니터링"""

    def __init__(self):
        self.process = psutil.Process()
        self.start_memory = 0
        self.peak_memory = 0
        self.cpu_samples = []

    def start_monitoring(self):
        """모니터링 시작"""
        tracemalloc.start()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024
        self.peak_memory = self.start_memory

    def sample_cpu(self):
        """CPU 사용률 샘플링"""
        cpu = self.process.cpu_percent()
        self.cpu_samples.append(cpu)

        # 메모리 피크 업데이트
        current_memory = self.process.memory_info().rss / 1024 / 1024
        self.peak_memory = max(self.peak_memory, current_memory)

    def get_current_memory_mb(self) -> float:
        """현재 메모리 사용량 (MB)"""
        return self.process.memory_info().rss / 1024 / 1024

    def get_avg_cpu_percent(self) -> float:
        """평균 CPU 사용률"""
        return sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0

    def stop_monitoring(self) -> Dict[str, float]:
        """모니터링 종료 및 결과 반환"""
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            'avg_cpu_percent': self.get_avg_cpu_percent(),
            'current_memory_mb': self.get_current_memory_mb(),
            'peak_memory_mb': self.peak_memory,
            'traced_peak_mb': peak_memory / 1024 / 1024
        }


async def stress_test_single_strategy(
    strategy: RateLimitStrategy,
    target_rps: int = 1000,
    duration_seconds: int = 30,
    enable_monitoring: bool = True
) -> StressTestMetrics:
    """단일 전략 스트레스 테스트"""

    print(f"\n🚀 {strategy.name} 스트레스 테스트 시작")
    print(f"   목표 RPS: {target_rps}, 지속시간: {duration_seconds}초")

    # Rate Limiter 생성
    limiter = UpbitRateLimiter(strategy=strategy, client_id=f"stress_test_{strategy.name}")

    # 리소스 모니터링 시작
    monitor = ResourceMonitor() if enable_monitoring else None
    if monitor:
        monitor.start_monitoring()

    # 테스트 메트릭
    total_requests = 0
    total_wait_time = 0.0
    acquire_times = []
    lock_contention = 0

    start_time = time.perf_counter()
    end_time = start_time + duration_seconds

    # 🔥 극한 부하 생성 - 목표 RPS로 연속 요청
    request_interval = 1.0 / target_rps  # 요청 간 간격

    while time.perf_counter() < end_time:
        loop_start = time.perf_counter()

        # Rate Limiter acquire 시간 측정
        acquire_start = time.perf_counter()
        await limiter.acquire('/market/all', 'GET')
        acquire_end = time.perf_counter()

        acquire_time = (acquire_end - acquire_start) * 1000  # ms 변환
        acquire_times.append(acquire_time)
        total_wait_time += acquire_time
        total_requests += 1

        # 🎯 CPU/메모리 샘플링 (매 100회마다)
        if monitor and total_requests % 100 == 0:
            monitor.sample_cpu()

        # 목표 RPS 유지를 위한 정밀한 타이밍 제어
        loop_end = time.perf_counter()
        elapsed = loop_end - loop_start

        if elapsed < request_interval:
            sleep_time = request_interval - elapsed
            await asyncio.sleep(sleep_time)

        # 매 1000회마다 진행 상황 출력
        if total_requests % 1000 == 0:
            elapsed_time = time.perf_counter() - start_time
            current_rps = total_requests / elapsed_time
            current_memory = monitor.get_current_memory_mb() if monitor else 0
            print(f"   진행: {total_requests:,}회 | {current_rps:.1f} RPS | "
                  f"메모리: {current_memory:.1f}MB | 평균대기: {sum(acquire_times[-1000:]) / 1000:.2f}ms")

    # 최종 측정
    final_time = time.perf_counter()
    actual_duration = final_time - start_time
    actual_rps = total_requests / actual_duration

    # 리소스 모니터링 결과
    resource_stats = monitor.stop_monitoring() if monitor else {
        'avg_cpu_percent': 0, 'current_memory_mb': 0, 'peak_memory_mb': 0
    }

    # GC 상태 확인
    gc_stats = gc.get_stats()
    total_gc_collections = sum(stat['collections'] for stat in gc_stats)

    print(f"✅ {strategy.name} 완료: {total_requests:,}회 요청, {actual_rps:.1f} RPS 달성")

    return StressTestMetrics(
        strategy=strategy.name,
        total_requests=total_requests,
        duration_seconds=actual_duration,
        rps_achieved=actual_rps,
        cpu_usage_percent=resource_stats['avg_cpu_percent'],
        memory_usage_mb=resource_stats['current_memory_mb'],
        peak_memory_mb=resource_stats['peak_memory_mb'],
        total_wait_time_ms=total_wait_time,
        avg_acquire_time_ms=sum(acquire_times) / len(acquire_times) if acquire_times else 0,
        lock_contention_count=lock_contention,
        gc_collections=total_gc_collections
    )


async def stress_test_concurrent_clients(
    strategy: RateLimitStrategy,
    num_clients: int = 10,
    requests_per_client: int = 1000
) -> Dict[str, Any]:
    """다중 클라이언트 동시성 스트레스 테스트"""

    print(f"\n🔀 {strategy.name} 동시성 테스트: {num_clients}개 클라이언트")

    async def client_task(client_id: int) -> Dict[str, float]:
        """개별 클라이언트 작업"""
        limiter = UpbitRateLimiter(strategy=strategy, client_id=f"client_{client_id}")

        start_time = time.perf_counter()
        acquire_times = []

        for i in range(requests_per_client):
            acquire_start = time.perf_counter()
            await limiter.acquire('/market/all', 'GET')
            acquire_end = time.perf_counter()

            acquire_times.append((acquire_end - acquire_start) * 1000)

        end_time = time.perf_counter()
        duration = end_time - start_time

        return {
            'client_id': client_id,
            'duration': duration,
            'rps': requests_per_client / duration,
            'avg_acquire_ms': sum(acquire_times) / len(acquire_times),
            'max_acquire_ms': max(acquire_times),
            'min_acquire_ms': min(acquire_times)
        }

    # 🚀 모든 클라이언트 동시 실행
    monitor = ResourceMonitor()
    monitor.start_monitoring()

    start_time = time.perf_counter()

    # 동시 실행
    tasks = [client_task(i) for i in range(num_clients)]
    client_results = await asyncio.gather(*tasks)

    end_time = time.perf_counter()
    resource_stats = monitor.stop_monitoring()

    # 📊 결과 집계
    total_requests = num_clients * requests_per_client
    total_duration = end_time - start_time
    aggregate_rps = total_requests / total_duration

    avg_client_rps = sum(r['rps'] for r in client_results) / len(client_results)
    avg_acquire_time = sum(r['avg_acquire_ms'] for r in client_results) / len(client_results)

    print(f"✅ 동시성 테스트 완료: 총 {total_requests:,}회, 집계 RPS {aggregate_rps:.1f}")

    return {
        'strategy': strategy.name,
        'num_clients': num_clients,
        'total_requests': total_requests,
        'aggregate_rps': aggregate_rps,
        'avg_client_rps': avg_client_rps,
        'avg_acquire_time_ms': avg_acquire_time,
        'cpu_usage_percent': resource_stats['avg_cpu_percent'],
        'peak_memory_mb': resource_stats['peak_memory_mb'],
        'client_results': client_results
    }


async def run_comprehensive_stress_test():
    """포괄적인 스트레스 테스트 실행"""

    print("=" * 80)
    print("🎯 Rate Limiter 포괄적 스트레스 테스트")
    print("=" * 80)

    strategies = [
        RateLimitStrategy.CLOUDFLARE_SLIDING_WINDOW,
        RateLimitStrategy.AIOLIMITER_OPTIMIZED,
        RateLimitStrategy.HYBRID_FAST,
        RateLimitStrategy.LEGACY_CONSERVATIVE,
        RateLimitStrategy.RESPONSE_INTERVAL_SIMPLE,
        RateLimitStrategy.SMART_RESPONSE_ADAPTIVE
    ]

    # Phase 1: 단일 클라이언트 극한 부하 테스트
    print("\n📈 Phase 1: 극한 부하 테스트 (목표 1000 RPS, 30초)")
    single_results = []

    for strategy in strategies:
        try:
            result = await stress_test_single_strategy(
                strategy=strategy,
                target_rps=1000,
                duration_seconds=30
            )
            single_results.append(result)

            # 전략 간 정리 시간
            await asyncio.sleep(2)
            gc.collect()  # 강제 GC

        except Exception as e:
            print(f"❌ {strategy.name} 스트레스 테스트 실패: {e}")

    # Phase 2: 다중 클라이언트 동시성 테스트
    print("\n🔀 Phase 2: 동시성 테스트 (10개 클라이언트, 각 1000회)")
    concurrent_results = []

    for strategy in [RateLimitStrategy.HYBRID_FAST, RateLimitStrategy.AIOLIMITER_OPTIMIZED]:
        try:
            result = await stress_test_concurrent_clients(
                strategy=strategy,
                num_clients=10,
                requests_per_client=1000
            )
            concurrent_results.append(result)

            await asyncio.sleep(3)
            gc.collect()

        except Exception as e:
            print(f"❌ {strategy.name} 동시성 테스트 실패: {e}")

    # 📊 최종 결과 요약
    print("\n" + "=" * 90)
    print("📊 스트레스 테스트 결과 요약")
    print("=" * 90)

    print("\n🚀 극한 부하 테스트 결과:")
    print("전략명                    | 달성RPS | 평균대기 | CPU사용 | 피크메모리 | 총요청수")
    print("-" * 85)

    for result in single_results:
        name = result.strategy[:22].ljust(22)
        rps = f"{result.rps_achieved:.1f}".rjust(7)
        wait = f"{result.avg_acquire_time_ms:.2f}ms".rjust(8)
        cpu = f"{result.cpu_usage_percent:.1f}%".rjust(7)
        memory = f"{result.peak_memory_mb:.1f}MB".rjust(10)
        requests = f"{result.total_requests:,}".rjust(8)

        print(f"{name} | {rps} | {wait} | {cpu} | {memory} | {requests}")

    if concurrent_results:
        print("\n🔀 동시성 테스트 결과:")
        for result in concurrent_results:
            print(f"{result['strategy']}: {result['aggregate_rps']:.1f} RPS "
                  f"(클라이언트당 평균 {result['avg_client_rps']:.1f} RPS)")

    # 💡 성능 분석 및 권장사항
    if single_results:
        best_rps = max(single_results, key=lambda x: x.rps_achieved)
        best_efficiency = min(single_results, key=lambda x: x.avg_acquire_time_ms)
        best_memory = min(single_results, key=lambda x: x.peak_memory_mb)

        print(f"\n🏆 성능 우수 전략:")
        print(f"   최고 RPS: {best_rps.strategy} ({best_rps.rps_achieved:.1f} RPS)")
        print(f"   최고 효율성: {best_efficiency.strategy} ({best_efficiency.avg_acquire_time_ms:.2f}ms)")
        print(f"   최저 메모리: {best_memory.strategy} ({best_memory.peak_memory_mb:.1f}MB)")


if __name__ == "__main__":
    # 시스템 리소스 확인
    print(f"💻 시스템 정보:")
    print(f"   CPU 코어: {psutil.cpu_count()} 개")
    print(f"   메모리: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f}GB")
    print(f"   Python: {psutil.Process().memory_info().rss / 1024 / 1024:.1f}MB 사용 중")

    asyncio.run(run_comprehensive_stress_test())
