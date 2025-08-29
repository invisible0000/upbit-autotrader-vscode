"""
Rate Limiter 전략 성능 분석 도구

- 3가지 전략을 각각 2분간 테스트
- 429 오류 시 즉시 중단 (Ban 방지)
- Ctrl+C로 우아한 중단 지원
- 1분마다 중간 보고서, 2분 후 최종 분석
- 상세한 성능 지표 및 명확한 결론 제시
"""

import asyncio
import signal
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import (
    UpbitRateLimiter,
    RateLimitStrategy
)
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient


@dataclass
class PerformanceMetrics:
    """성능 지표 데이터 클래스"""
    strategy: RateLimitStrategy
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    error_429_count: int = 0
    total_rate_limiter_time: float = 0.0
    total_http_time: float = 0.0
    total_test_time: float = 0.0
    avg_requests_per_second: float = 0.0
    avg_rate_limiter_ms: float = 0.0
    avg_http_ms: float = 0.0
    min_rate_limiter_ms: float = float('inf')
    max_rate_limiter_ms: float = 0.0
    rate_limiter_times: List[float] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)

    def update_rate_limiter_time(self, time_ms: float):
        """Rate Limiter 시간 업데이트"""
        self.rate_limiter_times.append(time_ms)
        self.total_rate_limiter_time += time_ms / 1000.0
        self.min_rate_limiter_ms = min(self.min_rate_limiter_ms, time_ms)
        self.max_rate_limiter_ms = max(self.max_rate_limiter_ms, time_ms)

    def calculate_averages(self):
        """평균값 계산"""
        if self.total_requests > 0:
            self.avg_rate_limiter_ms = (self.total_rate_limiter_time / self.total_requests) * 1000
        if self.total_test_time > 0:
            self.avg_requests_per_second = self.successful_requests / self.total_test_time
        if self.successful_requests > 0:
            self.avg_http_ms = (self.total_http_time / self.successful_requests) * 1000


class TestStatus(Enum):
    """테스트 상태"""
    RUNNING = "실행중"
    COMPLETED = "완료"
    STOPPED_429 = "429 오류로 중단"
    STOPPED_USER = "사용자 중단"
    STOPPED_ERROR = "오류로 중단"


class RateLimiterBenchmark:
    """Rate Limiter 성능 벤치마크"""

    def __init__(self):
        self.test_duration = 120  # 2분
        self.report_interval = 60  # 1분마다 보고서
        self.stop_event = asyncio.Event()
        self.current_test: Optional[str] = None

        # 신호 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Ctrl+C 신호 처리"""
        print(f"\n🛑 사용자 중단 요청 감지 (테스트: {self.current_test})")
        print("⏳ 우아한 종료 중...")
        self.stop_event.set()

    async def run_complete_benchmark(self) -> Dict[RateLimitStrategy, PerformanceMetrics]:
        """전체 벤치마크 실행"""
        print("🚀 Rate Limiter 전략 성능 벤치마크 시작")
        print("=" * 70)
        print("📋 테스트 설정:")
        print(f"  - 각 전략별 테스트 시간: {self.test_duration}초")
        print(f"  - 중간 보고서 간격: {self.report_interval}초")
        print("  - 429 오류 시 즉시 중단")
        print("  - Ctrl+C로 우아한 중단 가능")
        print("=" * 70)

        strategies = [
            RateLimitStrategy.HYBRID_FAST,
            RateLimitStrategy.CLOUDFLARE_SLIDING_WINDOW,
            RateLimitStrategy.AIOLIMITER_OPTIMIZED
        ]

        results = {}

        for i, strategy in enumerate(strategies, 1):
            if self.stop_event.is_set():
                print("\n🛑 사용자 요청으로 전체 벤치마크 중단")
                break

            print(f"\n🎯 [{i}/{len(strategies)}] {strategy.value} 전략 테스트 시작")
            print("-" * 50)

            self.current_test = strategy.value
            result = await self.test_strategy(strategy)
            results[strategy] = result

            if result.error_429_count > 0:
                print(f"⚠️  {strategy.value}에서 429 오류 발생, 다음 전략으로 진행")

            # 전략 간 쿨다운 (5초)
            if i < len(strategies) and not self.stop_event.is_set():
                print("⏸️  전략 간 쿨다운 5초...")
                await asyncio.sleep(5)

        # 최종 종합 분석
        self._print_final_analysis(results)
        return results

    async def test_strategy(self, strategy: RateLimitStrategy) -> PerformanceMetrics:
        """단일 전략 테스트"""
        metrics = PerformanceMetrics(strategy=strategy)

        # Rate Limiter 초기화
        rate_limiter = UpbitRateLimiter(strategy=strategy)
        client = UpbitPublicClient(rate_limiter=rate_limiter)

        test_start_time = time.perf_counter()
        last_report_time = test_start_time
        last_progress_time = test_start_time
        status = TestStatus.RUNNING

        try:
            print(f"🏃‍♂️ {strategy.value} 전략으로 {self.test_duration}초간 테스트 시작")
            print(f"📊 Progress: [{'.' * 40}] 0.0% (0초)")

            while True:
                current_time = time.perf_counter()
                elapsed = current_time - test_start_time

                # 종료 조건 확인
                if elapsed >= self.test_duration:
                    status = TestStatus.COMPLETED
                    break

                if self.stop_event.is_set():
                    status = TestStatus.STOPPED_USER
                    break

                # CLI 스타일 프로그레스 바 (5초마다 업데이트)
                if current_time - last_progress_time >= 5.0:
                    self._print_progress_bar(elapsed, strategy, metrics)
                    last_progress_time = current_time

                # 중간 보고서 (1분마다)
                if current_time - last_report_time >= self.report_interval:
                    self._print_interim_report(metrics, elapsed, strategy)
                    last_report_time = current_time

                # 단일 요청 테스트
                try:
                    # Rate Limiter 시간 측정
                    rate_limiter_start = time.perf_counter()
                    await rate_limiter.acquire('/market/all', 'GET')
                    rate_limiter_end = time.perf_counter()
                    rate_limiter_time_ms = (rate_limiter_end - rate_limiter_start) * 1000

                    # HTTP 요청 시간 측정 (429 오류 재시도 없이)
                    http_start = time.perf_counter()
                    result = await client.get_market_all()
                    http_end = time.perf_counter()
                    http_time = http_end - http_start

                    # 성공 기록
                    metrics.total_requests += 1
                    metrics.successful_requests += 1
                    metrics.update_rate_limiter_time(rate_limiter_time_ms)
                    metrics.total_http_time += http_time

                    # 결과 검증
                    if not isinstance(result, dict) or len(result) == 0:
                        metrics.error_messages.append("Empty or invalid response")

                except Exception as e:
                    metrics.total_requests += 1
                    error_msg = str(e)

                    # 429 오류 감지 시 즉시 중단 (더 정확한 감지)
                    is_429_error = ("429" in error_msg
                                    or "Too Many Requests" in error_msg
                                    or "rate limit" in error_msg.lower()
                                    or "Rate Limit 초과" in error_msg
                                    or "HTTP 429" in error_msg)

                    if is_429_error:
                        metrics.error_429_count += 1
                        print("\n\n🚨🚨🚨 429 Rate Limit 오류 감지! 테스트 즉시 중단 🚨🚨🚨")
                        print(f"   🔴 오류 상세: {error_msg}")
                        print(f"   ⏱️  경과 시간: {elapsed:.1f}초")
                        print(f"   📊 총 요청 수: {metrics.total_requests}회")
                        print(f"   ✅ 성공 요청: {metrics.successful_requests}회")
                        print(f"   💥 현재 RPS: {metrics.successful_requests / elapsed:.2f}")
                        print(f"   🛑 429 카운트: {metrics.error_429_count}회")
                        print("   🚨 업비트 Ban 방지를 위해 즉시 중단합니다!")
                        print("   💡 파라미터 조정 필요: 현재 전략이 너무 공격적입니다")

                        # 5초 쿨다운 추가
                        print("   ⏸️  5초 쿨다운 후 다음 전략 테스트 진행...")
                        await asyncio.sleep(5)

                        status = TestStatus.STOPPED_429
                        break

                    # 다른 오류 처리
                    metrics.failed_requests += 1
                    metrics.error_messages.append(error_msg)
                    print(f"\n⚠️  요청 {metrics.total_requests} 오류: {error_msg}")

                    # 연속 오류 체크
                    if metrics.failed_requests >= 10:
                        print(f"\n🛑 과도한 오류 발생 ({metrics.failed_requests}회), 테스트 중단")
                        status = TestStatus.STOPPED_ERROR
                        break

                # 과부하 방지 (최소 간격)
                await asyncio.sleep(0.01)

        finally:
            metrics.total_test_time = time.perf_counter() - test_start_time
            metrics.calculate_averages()
            await client.close()

            # 최종 보고서
            self._print_strategy_final_report(metrics, status)

        return metrics

    def _print_progress_bar(self, elapsed: float, strategy: RateLimitStrategy, metrics: PerformanceMetrics):
        """CLI 스타일 프로그레스 바 출력 (한 줄 업데이트)"""
        progress = min(elapsed / self.test_duration, 1.0)
        filled_length = int(40 * progress)
        bar = '█' * filled_length + '░' * (40 - filled_length)
        current_rps = metrics.successful_requests / elapsed if elapsed > 0 else 0

        # \r로 같은 줄 덮어쓰기 (터미널 로그 줄이기)
        print(f"\r📊 Progress: [{bar}] {progress * 100:.1f}% ({elapsed:.0f}초, RPS: {current_rps:.1f})", end='', flush=True)

    def _print_interim_report(self, metrics: PerformanceMetrics, elapsed: float, strategy: RateLimitStrategy):
        """중간 보고서 출력"""
        progress = (elapsed / self.test_duration) * 100
        current_rps = metrics.successful_requests / elapsed if elapsed > 0 else 0

        print(f"\n📊 [{strategy.value}] 중간 보고서 ({elapsed:.0f}초 경과, {progress:.1f}%)")
        print(f"   요청 수: {metrics.total_requests} (성공: {metrics.successful_requests}, 실패: {metrics.failed_requests})")
        print(f"   현재 RPS: {current_rps:.2f}")

        if metrics.rate_limiter_times:
            current_avg_rl = sum(metrics.rate_limiter_times) / len(metrics.rate_limiter_times)
            print(f"   평균 Rate Limiter: {current_avg_rl:.1f}ms")

        if metrics.total_http_time > 0:
            current_avg_http = (metrics.total_http_time / metrics.successful_requests) * 1000
            print(f"   평균 HTTP: {current_avg_http:.1f}ms")

    def _print_strategy_final_report(self, metrics: PerformanceMetrics, status: TestStatus):
        """전략별 최종 보고서"""
        print("\n" + "=" * 60)
        print(f"📈 {metrics.strategy.value} 전략 최종 결과")
        print("=" * 60)
        print(f"테스트 상태: {status.value}")
        print(f"총 테스트 시간: {metrics.total_test_time:.1f}초")
        print(f"총 요청 수: {metrics.total_requests}")
        print(f"성공 요청: {metrics.successful_requests}")
        print(f"실패 요청: {metrics.failed_requests}")
        print(f"429 오류: {metrics.error_429_count}")

        # 429 오류 시 추가 경고 표시
        if metrics.error_429_count > 0:
            print(f"🚨 Rate Limit 위반: {metrics.error_429_count}회 - 프로덕션 사용 금지!")
            print("🛑 Ban 위험도: 높음 - 즉시 파라미터 조정 필요")

        if metrics.total_test_time > 0:
            print(f"평균 RPS: {metrics.avg_requests_per_second:.2f}")

        if metrics.successful_requests > 0:
            print(f"평균 Rate Limiter 시간: {metrics.avg_rate_limiter_ms:.2f}ms")
            print(f"평균 HTTP 시간: {metrics.avg_http_ms:.2f}ms")
            print(f"Rate Limiter 범위: {metrics.min_rate_limiter_ms:.2f}ms ~ {metrics.max_rate_limiter_ms:.2f}ms")

        # 성능 등급
        grade = self._calculate_performance_grade(metrics)
        print(f"성능 등급: {grade}")
        print("=" * 60)

    def _calculate_performance_grade(self, metrics: PerformanceMetrics) -> str:
        """성능 등급 계산"""
        if metrics.error_429_count > 0:
            return "🚨 F등급 (429 오류 - 즉시 중단됨)"

        if metrics.failed_requests > metrics.successful_requests * 0.1:
            return "⚠️ D등급 (높은 실패율)"

        if metrics.avg_requests_per_second >= 8.0:
            return "🏆 A등급 (우수한 성능)"
        elif metrics.avg_requests_per_second >= 6.0:
            return "🥇 B등급 (좋은 성능)"
        elif metrics.avg_requests_per_second >= 4.0:
            return "🥈 C등급 (보통 성능)"
        else:
            return "🥉 D등급 (낮은 성능)"

    def _print_final_analysis(self, results: Dict[RateLimitStrategy, PerformanceMetrics]):
        """최종 종합 분석"""
        if not results:
            print("\n❌ 분석할 결과가 없습니다.")
            return

        print("\n" + "🎯" + "=" * 68 + "🎯")
        print("🏁 Rate Limiter 전략 종합 성능 분석 결과")
        print("🎯" + "=" * 68 + "🎯")

        # 성능 비교 테이블
        print("\n📊 성능 비교 요약:")
        print("-" * 90)
        print(f"{'전략':<25} {'RPS':<8} {'Rate Limiter':<15} {'HTTP':<10} {'성공률':<8} {'등급':<10}")
        print("-" * 90)

        best_strategy = None
        best_rps = 0
        valid_strategies = 0  # 429 오류 없는 유효한 전략 개수

        for strategy, metrics in results.items():
            success_rate = (metrics.successful_requests / metrics.total_requests * 100) if metrics.total_requests > 0 else 0
            grade = self._calculate_performance_grade(metrics)

            print(f"{strategy.value:<25} {metrics.avg_requests_per_second:<8.2f} "
                  f"{metrics.avg_rate_limiter_ms:<15.1f} {metrics.avg_http_ms:<10.1f} "
                  f"{success_rate:<8.1f}% {grade:<10}")

            # 429 오류가 없는 유효한 전략만 최고 성능 후보로 고려
            if metrics.error_429_count == 0:
                valid_strategies += 1
                if metrics.avg_requests_per_second > best_rps:
                    best_rps = metrics.avg_requests_per_second
                    best_strategy = strategy

        print("-" * 90)

        # 결론 및 권장사항
        print("\n🏆 결론 및 권장사항:")

        if best_strategy:
            print(f"✅ 최고 성능 전략: {best_strategy.value}")
            print(f"   - RPS: {best_rps:.2f}")
            print("   - 429 오류 없이 안정적 운영")
            print("   - 프로덕션 환경 권장")
        elif valid_strategies == 0:
            print("❌ 모든 전략에서 429 오류 발생!")
            print("   - 모든 전략의 파라미터 조정 필요")
            print("   - 현재 상태로는 프로덕션 사용 불가")
        else:
            print("⚠️  성능 측정 불완전")
            print("   - 일부 전략에서만 안전한 동작 확인됨")

        # 429 오류 발생 전략 경고
        error_strategies = [s.value for s, m in results.items() if m.error_429_count > 0]
        if error_strategies:
            print(f"\n⚠️ 429 오류 발생 전략: {', '.join(error_strategies)}")
            print("   → 이 전략들은 프로덕션 사용 비권장")

        # 세부 분석 (429 오류 없는 전략만)
        print("\n📋 세부 분석:")
        valid_strategies = [(s, m) for s, m in results.items() if m.error_429_count == 0]

        if valid_strategies:
            for strategy, metrics in valid_strategies:
                efficiency = metrics.avg_requests_per_second / (metrics.avg_rate_limiter_ms + metrics.avg_http_ms) * 1000
                print(f"   {strategy.value}: 효율성 {efficiency:.2f} (RPS/응답시간)")
        else:
            print("   ❌ 유효한 전략 없음 (모든 전략에서 429 오류)")

        print("\n" + "🎯" + "=" * 68 + "🎯")


async def main():
    """메인 실행 함수"""
    try:
        benchmark = RateLimiterBenchmark()
        results = await benchmark.run_complete_benchmark()

        print("\n✅ 벤치마크 완료!")
        print("📁 결과가 메모리에 저장되었습니다.")
        return results

    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 벤치마크 오류: {e}")


if __name__ == "__main__":
    print("🚀 Rate Limiter 성능 벤치마크 도구")
    print("💡 Ctrl+C로 언제든 우아하게 중단 가능")
    print()

    # 비동기 실행
    results = asyncio.run(main())
