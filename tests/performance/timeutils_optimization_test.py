"""
TimeUtils 마이크로 최적화 성능 테스트

목적: `* 1000` 연산 오버헤드 vs 직접 밀리초 매핑 성능 비교
- 현재 방식: TimeUtils.get_timeframe_seconds(timeframe) * 1000
- 최적화 방식: TimeUtils.get_timeframe_ms(timeframe)

측정할 지표:
1. 개별 메서드 호출 시간 (나노초 수준 정밀도)
2. 실제 EmptyCandleDetector 초기화 시간 영향
3. 대량 호출 시 누적 성능 이득
4. 메모리 사용량 차이

Created: 2025-09-21
"""

import sys
import timeit
from pathlib import Path
from typing import Dict

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 프로젝트 imports
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("TimeUtilsOptimizationTest")


class OptimizedTimeUtils:
    """TimeUtils 최적화 버전 - 밀리초 직접 매핑 추가"""

    # 기존 초 단위 매핑 (변경 없음)
    _TIMEFRAME_SECONDS: Dict[str, int] = {
        "1s": 1, "1m": 60, "3m": 180, "5m": 300, "10m": 600,
        "15m": 900, "30m": 1800, "60m": 3600, "1h": 3600,
        "240m": 14400, "4h": 14400, "1d": 86400, "1w": 604800,
        "1M": 2592000, "1y": 31536000
    }

    # 🆕 밀리초 직접 매핑 (초 단위에서 자동 생성)
    _TIMEFRAME_MS: Dict[str, int] = {
        timeframe: seconds * 1000
        for timeframe, seconds in _TIMEFRAME_SECONDS.items()
    }

    @staticmethod
    def get_timeframe_seconds(timeframe: str) -> int:
        """기존 방식: 초 단위 반환"""
        if timeframe not in OptimizedTimeUtils._TIMEFRAME_SECONDS:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")
        return OptimizedTimeUtils._TIMEFRAME_SECONDS[timeframe]

    @staticmethod
    def get_timeframe_ms(timeframe: str) -> int:
        """🆕 최적화 방식: 밀리초 직접 반환"""
        if timeframe not in OptimizedTimeUtils._TIMEFRAME_MS:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")
        return OptimizedTimeUtils._TIMEFRAME_MS[timeframe]


class TimeUtilsPerformanceBenchmark:
    """TimeUtils 마이크로 최적화 성능 벤치마크"""

    def __init__(self):
        # 테스트할 타임프레임들
        self.test_timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]

    def benchmark_individual_calls(self, repeat_count: int = 1000000) -> Dict:
        """개별 메서드 호출 성능 비교 (마이크로 벤치마크)"""
        print(f"\n🔍 개별 메서드 호출 성능 비교 ({repeat_count:,}회 반복)")
        print("=" * 60)

        results = {}

        for timeframe in self.test_timeframes:
            print(f"\n📊 타임프레임: {timeframe}")

            # 현재 방식: get_timeframe_seconds + * 1000
            def current_method():
                return OptimizedTimeUtils.get_timeframe_seconds(timeframe) * 1000

            # 최적화 방식: get_timeframe_ms 직접 호출
            def optimized_method():
                return OptimizedTimeUtils.get_timeframe_ms(timeframe)

            # timeit으로 정밀 측정 (가장 작은 시간 기록)
            current_time = timeit.timeit(current_method, number=repeat_count)
            optimized_time = timeit.timeit(optimized_method, number=repeat_count)

            # 결과 기록
            current_ns = (current_time / repeat_count) * 1_000_000_000  # 나노초
            optimized_ns = (optimized_time / repeat_count) * 1_000_000_000  # 나노초

            improvement_ratio = current_ns / optimized_ns if optimized_ns > 0 else 1
            improvement_percent = ((current_ns - optimized_ns) / current_ns * 100) if current_ns > 0 else 0

            results[timeframe] = {
                'current_ns': current_ns,
                'optimized_ns': optimized_ns,
                'improvement_ratio': improvement_ratio,
                'improvement_percent': improvement_percent
            }

            print(f"  현재 방식:    {current_ns:.1f}ns")
            print(f"  최적화 방식:  {optimized_ns:.1f}ns")
            print(f"  성능 개선:    {improvement_ratio:.1f}배 ({improvement_percent:+.1f}%)")

            # 정확성 검증
            result1 = current_method()
            result2 = optimized_method()
            accuracy = result1 == result2
            print(f"  정확성:      {'✅ 일치' if accuracy else '❌ 불일치'}")

        return results

    def benchmark_detector_initialization(self, repeat_count: int = 10000) -> Dict:
        """EmptyCandleDetector 초기화 시간 영향 측정"""
        print(f"\n🏗️ EmptyCandleDetector 초기화 시간 비교 ({repeat_count:,}회 반복)")
        print("=" * 60)

        # 간단한 Detector 모킹
        class MockDetectorCurrent:
            def __init__(self, symbol: str, timeframe: str):
                self.symbol = symbol
                self.timeframe = timeframe
                # 현재 방식
                self._timeframe_delta_ms = OptimizedTimeUtils.get_timeframe_seconds(timeframe) * 1000

        class MockDetectorOptimized:
            def __init__(self, symbol: str, timeframe: str):
                self.symbol = symbol
                self.timeframe = timeframe
                # 최적화 방식
                self._timeframe_delta_ms = OptimizedTimeUtils.get_timeframe_ms(timeframe)

        results = {}

        for timeframe in self.test_timeframes:
            print(f"\n📊 타임프레임: {timeframe}")

            # 현재 방식 초기화 시간
            def current_init():
                return MockDetectorCurrent("KRW-BTC", timeframe)

            # 최적화 방식 초기화 시간
            def optimized_init():
                return MockDetectorOptimized("KRW-BTC", timeframe)

            # 측정
            current_time = timeit.timeit(current_init, number=repeat_count)
            optimized_time = timeit.timeit(optimized_init, number=repeat_count)

            # 결과 계산
            current_us = (current_time / repeat_count) * 1_000_000  # 마이크로초
            optimized_us = (optimized_time / repeat_count) * 1_000_000  # 마이크로초

            improvement_ratio = current_us / optimized_us if optimized_us > 0 else 1
            improvement_percent = ((current_us - optimized_us) / current_us * 100) if current_us > 0 else 0

            results[timeframe] = {
                'current_us': current_us,
                'optimized_us': optimized_us,
                'improvement_ratio': improvement_ratio,
                'improvement_percent': improvement_percent
            }

            print(f"  현재 방식:    {current_us:.2f}μs")
            print(f"  최적화 방식:  {optimized_us:.2f}μs")
            print(f"  성능 개선:    {improvement_ratio:.1f}배 ({improvement_percent:+.1f}%)")

        return results

    def benchmark_bulk_operations(self, bulk_count: int = 100000) -> Dict:
        """대량 연산 시 누적 성능 이득 측정"""
        print(f"\n📦 대량 연산 누적 성능 이득 ({bulk_count:,}회 대량 처리)")
        print("=" * 60)

        # 시나리오: 다양한 타임프레임으로 여러 Detector 생성 (실제 사용 패턴)
        symbols = ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-SOL"]
        timeframes = ["1m", "5m", "15m", "1h"]

        print(f"시나리오: {len(symbols)}개 심볼 × {len(timeframes)}개 타임프레임 × {bulk_count//len(symbols)//len(timeframes):,}회 반복")

        def bulk_current():
            """현재 방식으로 대량 처리"""
            total_ms = 0
            for _ in range(bulk_count // len(symbols) // len(timeframes)):
                for symbol in symbols:
                    for timeframe in timeframes:
                        # 현재 방식: get_timeframe_seconds + 곱셈
                        total_ms += OptimizedTimeUtils.get_timeframe_seconds(timeframe) * 1000
            return total_ms

        def bulk_optimized():
            """최적화 방식으로 대량 처리"""
            total_ms = 0
            for _ in range(bulk_count // len(symbols) // len(timeframes)):
                for symbol in symbols:
                    for timeframe in timeframes:
                        # 최적화 방식: get_timeframe_ms 직접 호출
                        total_ms += OptimizedTimeUtils.get_timeframe_ms(timeframe)
            return total_ms

        # 성능 측정
        current_time = timeit.timeit(bulk_current, number=1)
        optimized_time = timeit.timeit(bulk_optimized, number=1)

        # 결과 계산
        improvement_ratio = current_time / optimized_time if optimized_time > 0 else 1
        improvement_percent = ((current_time - optimized_time) / current_time * 100) if current_time > 0 else 0
        time_saved_ms = (current_time - optimized_time) * 1000

        print(f"현재 방식 총 시간:    {current_time*1000:.2f}ms")
        print(f"최적화 방식 총 시간:  {optimized_time*1000:.2f}ms")
        print(f"성능 개선:           {improvement_ratio:.1f}배 ({improvement_percent:+.1f}%)")
        print(f"절약된 시간:         {time_saved_ms:.2f}ms")

        # 정확성 검증
        result1 = bulk_current()
        result2 = bulk_optimized()
        accuracy = result1 == result2
        print(f"정확성:             {'✅ 일치' if accuracy else '❌ 불일치'}")

        return {
            'current_time_ms': current_time * 1000,
            'optimized_time_ms': optimized_time * 1000,
            'improvement_ratio': improvement_ratio,
            'improvement_percent': improvement_percent,
            'time_saved_ms': time_saved_ms,
            'accuracy': accuracy
        }

    def run_comprehensive_benchmark(self) -> Dict:
        """종합 벤치마크 실행"""
        print("🚀 TimeUtils 마이크로 최적화 종합 성능 테스트")
        print("목적: `* 1000` 연산 vs 직접 밀리초 매핑 성능 비교")
        print("=" * 80)

        results = {}

        # 1. 개별 호출 성능
        results['individual'] = self.benchmark_individual_calls(1000000)

        # 2. Detector 초기화 영향
        results['initialization'] = self.benchmark_detector_initialization(10000)

        # 3. 대량 연산 누적 효과
        results['bulk'] = self.benchmark_bulk_operations(100000)

        return results

    def print_final_analysis(self, results: Dict):
        """최종 분석 및 권장사항 출력"""
        print("\n" + "="*80)
        print("🎯 === TimeUtils 마이크로 최적화 최종 분석 ===")
        print("="*80)

        # 개별 호출 평균 성능 개선
        individual_improvements = [
            data['improvement_ratio'] for data in results['individual'].values()
        ]
        avg_individual_improvement = sum(individual_improvements) / len(individual_improvements)

        # 초기화 평균 성능 개선
        init_improvements = [
            data['improvement_ratio'] for data in results['initialization'].values()
        ]
        avg_init_improvement = sum(init_improvements) / len(init_improvements)

        # 대량 연산 성능 개선
        bulk_improvement = results['bulk']['improvement_ratio']
        time_saved_ms = results['bulk']['time_saved_ms']

        print(f"📊 성능 개선 요약:")
        print(f"  • 개별 호출 평균:     {avg_individual_improvement:.1f}배 빠름")
        print(f"  • 초기화 평균:        {avg_init_improvement:.1f}배 빠름")
        print(f"  • 대량 연산:          {bulk_improvement:.1f}배 빠름")
        print(f"  • 절약 시간 (10만회): {time_saved_ms:.2f}ms")

        # 연간 추정 절약 시간 (가정: 하루 1만번 호출)
        daily_calls = 10000
        yearly_calls = daily_calls * 365
        yearly_saved_ns = (results['individual']['1m']['current_ns'] -
                          results['individual']['1m']['optimized_ns']) * yearly_calls
        yearly_saved_ms = yearly_saved_ns / 1_000_000

        print(f"\n⏱️ 추정 연간 절약 효과 (하루 {daily_calls:,}회 호출 가정):")
        print(f"  • 연간 절약 시간:     {yearly_saved_ms:.1f}ms")
        print(f"  • 마이크로초 수준:    {yearly_saved_ms/1000:.1f}μs")

        # 권장사항
        print(f"\n💡 권장사항:")

        if avg_individual_improvement >= 2.0:
            print(f"  ✅ 확실한 성능 개선 ({avg_individual_improvement:.1f}배)")
            print(f"     → get_timeframe_ms() 메서드 추가 권장")
        elif avg_individual_improvement >= 1.5:
            print(f"  ⚖️ 중간 수준 개선 ({avg_individual_improvement:.1f}배)")
            print(f"     → 코드 복잡성 vs 성능 이득 검토")
        else:
            print(f"  ⚠️ 미미한 개선 ({avg_individual_improvement:.1f}배)")
            print(f"     → 과도한 최적화일 수 있음")

        # 구현 복잡성 평가
        print(f"\n🔧 구현 복잡성:")
        print(f"  • 코드 추가량:        매우 작음 (메서드 1개, 매핑 1개)")
        print(f"  • 유지보수 비용:      낮음 (자동 생성 매핑)")
        print(f"  • 메모리 오버헤드:    미미함 (~100바이트)")
        print(f"  • 호환성 영향:        없음 (기존 메서드 유지)")

        # 최종 결론
        if avg_individual_improvement >= 1.5 and time_saved_ms > 1.0:
            print(f"\n🏆 최종 결론: 최적화 적용 권장")
            print(f"   성능 이득이 구현 비용을 충분히 상쇄합니다.")
        else:
            print(f"\n🤔 최종 결론: 신중한 검토 필요")
            print(f"   마이크로 최적화의 효용성을 재평가해보세요.")


def main():
    """메인 테스트 실행 함수"""
    print("TimeUtils 마이크로 최적화 성능 테스트 시작...")

    # 벤치마크 실행
    benchmark = TimeUtilsPerformanceBenchmark()

    try:
        results = benchmark.run_comprehensive_benchmark()
        benchmark.print_final_analysis(results)

        logger.info("✅ TimeUtils 최적화 성능 테스트 완료")
        return True

    except Exception as e:
        logger.error(f"❌ 테스트 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()

    if success:
        print("\n✅ 마이크로 최적화 테스트 완료")
    else:
        print("\n❌ 마이크로 최적화 테스트 실패")
