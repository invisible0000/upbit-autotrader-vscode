"""
Datetime 벡터화 연산 방식 비교 테스트

목적: datetime 형식에서 직접 벡터화 연산 vs timestamp 변환 방식 성능 비교
- 방법 1: datetime -> timestamp(int) -> numpy array (현재 방식)
- 방법 2: datetime -> numpy datetime64 array (직접 방식)
- 방법 3: pandas DatetimeIndex 방식

Created: 2025-09-21
"""

import sys
import time
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import List
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 프로젝트 imports
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils

logger = create_component_logger("DatetimeVectorizationTest")


class DatetimeVectorizationComparison:
    """datetime 벡터화 연산 방식 성능 비교"""

    def __init__(self):
        self.timeframe = "1m"
        self.timeframe_delta_ms = TimeUtils.get_timeframe_seconds(self.timeframe) * 1000

    def create_test_datetime_sequence(self, count: int, gap_density: float = 0.1) -> List[datetime]:
        """테스트용 datetime 시퀀스 생성 (Gap 포함)"""
        base_time = datetime.now(timezone.utc)
        aligned_base = TimeUtils.align_to_candle_boundary(base_time, self.timeframe)

        sequence = []
        current_time = aligned_base

        for i in range(count):
            sequence.append(current_time)

            # Gap 생성 확률
            if np.random.random() < gap_density:
                # 1-3틱 건너뛰기
                skip_ticks = np.random.randint(1, 4)
                current_time = TimeUtils.get_time_by_ticks(current_time, self.timeframe, -skip_ticks)
            else:
                current_time = TimeUtils.get_time_by_ticks(current_time, self.timeframe, -1)

        # 업비트 내림차순 정렬
        return sorted(sequence, reverse=True)

    def method1_timestamp_conversion(self, datetime_list: List[datetime]) -> np.ndarray:
        """방법 1: datetime -> timestamp -> numpy array (현재 방식)"""
        timestamps = np.array([int(dt.timestamp() * 1000) for dt in datetime_list])
        deltas = timestamps[:-1] - timestamps[1:]
        return deltas

    def method2_numpy_datetime64(self, datetime_list: List[datetime]) -> np.ndarray:
        """방법 2: numpy datetime64 직접 사용"""
        # datetime64[ms] 배열 생성
        dt64_array = np.array(datetime_list, dtype='datetime64[ms]')

        # 벡터화 차분 연산
        deltas = dt64_array[:-1] - dt64_array[1:]  # 결과는 timedelta64[ms]

        # 밀리초 정수로 변환
        delta_ms = deltas.astype(int)
        return delta_ms

    def method3_pandas_datetimeindex(self, datetime_list: List[datetime]) -> np.ndarray:
        """방법 3: pandas DatetimeIndex 사용"""
        dt_index = pd.to_datetime(datetime_list)

        # diff() 메서드로 차분 계산
        deltas = dt_index.to_series().diff()

        # 밀리초로 변환
        delta_ms = deltas.dt.total_seconds() * 1000

        # NaN 제거 후 numpy 배열로 반환
        return delta_ms.dropna().values.astype(int)

    def method4_pure_numpy_datetime64(self, datetime_list: List[datetime]) -> np.ndarray:
        """방법 4: 순수 numpy datetime64 (최적화 버전)"""
        # 더 직접적인 변환
        dt64_array = np.asarray(datetime_list, dtype='datetime64[ms]')

        # 차분 연산
        deltas = np.diff(dt64_array[::-1])  # 역순으로 뒤집어서 diff

        # 밀리초로 변환
        return deltas.astype('timedelta64[ms]').astype(int)

    def benchmark_method(self, method_func, datetime_list: List[datetime], method_name: str, repeat_count: int = 100) -> dict:
        """개별 메서드 벤치마크"""
        times = []
        results = []

        for _ in range(repeat_count):
            start_time = time.perf_counter()
            result = method_func(datetime_list)
            end_time = time.perf_counter()

            times.append((end_time - start_time) * 1000)  # ms
            results.append(len(result))

        return {
            "method": method_name,
            "mean_time_ms": np.mean(times),
            "std_time_ms": np.std(times),
            "min_time_ms": np.min(times),
            "max_time_ms": np.max(times),
            "result_size": results[0] if results else 0
        }

    def compare_all_methods(self, test_sizes: List[int]) -> List[dict]:
        """모든 방법 비교 테스트"""
        print("🔍 Datetime 벡터화 연산 방식 비교 테스트")
        print("=" * 80)

        all_results = []

        for size in test_sizes:
            print(f"\n📊 테스트 크기: {size}개 datetime")

            # 테스트 데이터 생성
            datetime_list = self.create_test_datetime_sequence(size)
            print(f"생성된 시퀀스: {len(datetime_list)}개 datetime")

            # 각 방법 벤치마크
            methods = [
                (self.method1_timestamp_conversion, "방법1: timestamp 변환"),
                (self.method2_numpy_datetime64, "방법2: numpy datetime64"),
                (self.method3_pandas_datetimeindex, "방법3: pandas DatetimeIndex"),
                (self.method4_pure_numpy_datetime64, "방법4: 순수 numpy datetime64")
            ]

            size_results = {"test_size": size, "methods": []}

            for method_func, method_name in methods:
                try:
                    result = self.benchmark_method(method_func, datetime_list, method_name)
                    size_results["methods"].append(result)
                    print(f"  {method_name}: {result['mean_time_ms']:.3f}ms ±{result['std_time_ms']:.3f}")
                except Exception as e:
                    print(f"  {method_name}: 실패 - {e}")

            all_results.append(size_results)

            # 결과 정확성 검증
            self.verify_result_accuracy(datetime_list)

        return all_results

    def verify_result_accuracy(self, datetime_list: List[datetime]):
        """결과 정확성 검증"""
        print(f"\n🔍 정확성 검증 (샘플 크기: {len(datetime_list)})")

        try:
            result1 = self.method1_timestamp_conversion(datetime_list)
            result2 = self.method2_numpy_datetime64(datetime_list)
            result4 = self.method4_pure_numpy_datetime64(datetime_list)

            # 절댓값 차이로 비교 (부호 차이 무시)
            match_1_2 = np.allclose(np.abs(result1), np.abs(result2))
            match_1_4 = np.allclose(np.abs(result1), np.abs(result4))

            print(f"  방법1 vs 방법2: {'✅ 일치' if match_1_2 else '❌ 불일치'}")
            print(f"  방법1 vs 방법4: {'✅ 일치' if match_1_4 else '❌ 불일치'}")

            if not match_1_2:
                print(f"    차이 예시: {result1[:5]} vs {result2[:5]}")

        except Exception as e:
            print(f"  정확성 검증 실패: {e}")

    def print_final_comparison(self, all_results: List[dict]):
        """최종 비교 결과 출력"""
        print("\n" + "="*80)
        print("🎯 === Datetime 벡터화 연산 방식 최종 비교 ===")
        print("="*80)

        # 각 테스트 크기별 최고 성능 방법 찾기
        for result in all_results:
            size = result["test_size"]
            methods = result["methods"]

            if not methods:
                continue

            # 평균 시간 기준 정렬
            sorted_methods = sorted(methods, key=lambda x: x["mean_time_ms"])
            best_method = sorted_methods[0]
            worst_method = sorted_methods[-1]

            improvement_ratio = worst_method["mean_time_ms"] / best_method["mean_time_ms"]

            print(f"\n📊 테스트 크기: {size}개")
            print(f"🏆 최고 성능: {best_method['method']} ({best_method['mean_time_ms']:.3f}ms)")
            print(f"🐌 최저 성능: {worst_method['method']} ({worst_method['mean_time_ms']:.3f}ms)")
            print(f"📈 성능 차이: {improvement_ratio:.1f}배")

            # 상세 결과 테이블
            print("\n상세 결과:")
            for method in sorted_methods:
                relative_speed = best_method["mean_time_ms"] / method["mean_time_ms"] * 100
                print(f"  {method['method']}: {method['mean_time_ms']:.3f}ms ({relative_speed:.1f}%)")

        # 종합 권장사항
        print(f"\n💡 권장사항:")

        # 평균 성능 계산
        method_names = ["방법1: timestamp 변환", "방법2: numpy datetime64", "방법4: 순수 numpy datetime64"]
        avg_times = {}

        for method_name in method_names:
            times = []
            for result in all_results:
                for method in result["methods"]:
                    if method["method"] == method_name:
                        times.append(method["mean_time_ms"])
            if times:
                avg_times[method_name] = np.mean(times)

        if avg_times:
            best_overall = min(avg_times.items(), key=lambda x: x[1])
            print(f"  🚀 전체 평균 최고 성능: {best_overall[0]} ({best_overall[1]:.3f}ms)")

            if "numpy datetime64" in best_overall[0]:
                print(f"  ✅ datetime 형식에서 직접 벡터화 연산 권장!")
                print(f"  ✅ timestamp 변환 단계 불필요!")
            else:
                print(f"  ⚠️ timestamp 변환 방식이 여전히 최고 성능")


def main():
    """메인 테스트 실행"""
    print("🔍 Datetime 벡터화 연산 방식 성능 비교")
    print("목적: datetime 직접 벡터화 vs timestamp 변환 방식 비교")
    print("-" * 60)

    # numpy 시드 설정
    np.random.seed(42)

    # 테스트 실행
    comparator = DatetimeVectorizationComparison()

    # 다양한 크기로 테스트
    test_sizes = [100, 1000, 5000, 10000]

    try:
        all_results = comparator.compare_all_methods(test_sizes)
        comparator.print_final_comparison(all_results)

        logger.info("✅ datetime 벡터화 연산 비교 테스트 완료")
        return True

    except Exception as e:
        logger.error(f"❌ 테스트 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Datetime 벡터화 연산 방식 비교 테스트 시작...")
    success = main()

    if success:
        print("\n✅ 비교 테스트 완료")
    else:
        print("\n❌ 비교 테스트 실패")
