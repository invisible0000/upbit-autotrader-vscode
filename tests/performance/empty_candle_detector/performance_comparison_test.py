"""
Performance Comparison Test - 기존 vs 벡터화 방식 성능 비교

목적: 독립적인 환경에서 두 Gap 감지 방식의 성능과 정확성을 엄격히 비교
- 기존 루프 방식 vs 벡터화 방식
- 성능 측정 (실행 시간, 메모리 사용량)
- 정확성 검증 (Gap 개수, 시간 범위)
- 청크 경계 문제 해결 검증

Created: 2025-09-21
"""

import sys
import time
import gc
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple
from pathlib import Path
import numpy as np
import psutil
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 독립 구현된 감지기들 import
from tests.performance.empty_candle_detector.original_gap_detector import OriginalGapDetector
from tests.performance.empty_candle_detector.vectorized_gap_detector import VectorizedGapDetector
from tests.performance.empty_candle_detector.optimized_gap_detector import OptimizedGapDetector
from tests.performance.empty_candle_detector.pure_numpy_gap_detector import PureNumpyGapDetector

# ================================================================
# 🎛️ 테스트 설정
# ================================================================
TEST_CONFIGS = [
    {
        "name": "소규모_연속",
        "candle_count": 50,
        "gap_density": 0.0,  # Gap 없음
        "timeframe": "1m"
    },
    {
        "name": "소규모_Gap있음",
        "candle_count": 50,
        "gap_density": 0.1,  # 10% Gap
        "timeframe": "1m"
    },
    {
        "name": "중간규모",
        "candle_count": 200,
        "gap_density": 0.15,  # 15% Gap
        "timeframe": "1m"
    },
    {
        "name": "대규모  ",
        "candle_count": 2000,
        "gap_density": 0.2,  # 20% Gap
        "timeframe": "1m"
    },
    {
        "name": "초대규모",
        "candle_count": 5000,
        "gap_density": 0.1,  # 10% Gap
        "timeframe": "1m"
    }
]

REPEAT_COUNT = 10  # 각 테스트 반복 횟수


class PerformanceComparison:
    """독립적인 성능 비교 실행기"""

    def __init__(self):
        self.results = []

    def create_mock_api_candles(self, config: Dict) -> Tuple[List[Dict], datetime, datetime]:
        """
        테스트용 Mock API 캔들 데이터 생성

        Args:
            config: 테스트 설정

        Returns:
            Tuple[api_candles, api_start, api_end]
        """
        candle_count = config["candle_count"]
        gap_density = config["gap_density"]
        timeframe = config["timeframe"]

        # 각 테스트마다 다른 시드 적용 (config name 기반)
        seed_value = hash(config["name"]) % 10000
        np.random.seed(seed_value)

        print(f"🎲 테스트 '{config['name']}' 시드: {seed_value}")

        # 기준 시간 설정 (테스트마다 다른 시작 시간)
        base_time = datetime(2025, 9, 21, 12, 0, 0, tzinfo=timezone.utc)
        time_offset = np.random.randint(0, 1440)  # 0-1440분 랜덤 오프셋
        base_time = base_time + timedelta(minutes=time_offset)

        # api_start = base_time
        api_start = self._get_previous_time(base_time, timeframe)  # 지출점에서 +1틱 을 하므로 -1틱

        # Mock 캔들 데이터 생성 (업비트 API 형식)
        candles = []
        current_time = api_start

        for i in range(candle_count):
            # Gap 생성 확률 적용
            if np.random.random() < gap_density:
                # Gap 생성: 1-3틱 건너뛰기
                skip_ticks = np.random.randint(1, 4)
                for _ in range(skip_ticks):
                    current_time = self._get_previous_time(current_time, timeframe)
            else:
                current_time = self._get_previous_time(current_time, timeframe)

            # Mock 캔들 Dict 생성
            candle_dict = {
                "market": "KRW-BTC",
                "candle_date_time_utc": current_time.strftime('%Y-%m-%dT%H:%M:%S'),
                "opening_price": 50000000.0,
                "high_price": 50050000.0,
                "low_price": 49950000.0,
                "trade_price": 50000000.0,
                "timestamp": int(current_time.timestamp() * 1000),
                "candle_acc_trade_price": 1000000000.0,
                "candle_acc_trade_volume": 20.0
            }
            candles.append(candle_dict)

        api_end = current_time

        # 업비트 정렬 (최신 → 과거)
        candles.sort(key=lambda x: x["candle_date_time_utc"], reverse=True)

        # # 🔍 디버그: 생성된 캔들 시간 정보 출력
        # print(f"\n📅 생성된 캔들 시간 정보 ({config['name']}):")
        # print(f"  • api_start: {api_start}")
        # print(f"  • api_end: {api_end}")
        # print(f"  • 총 캔들 개수: {len(candles)}개")
        # if candles:
        #     print(f"  • 첫 번째 캔들: {candles[0]['candle_date_time_utc']}")
        #     print(f"  • 마지막 캔들: {candles[-1]['candle_date_time_utc']}")

        #     # 처음 10개와 마지막 5개 캔들 시간 출력
        #     print("  • 처음 10개 캔들 시간:")
        #     for i, candle in enumerate(candles[:10]):
        #         print(f"    [{i+1}] {candle['candle_date_time_utc']}")

        #     if len(candles) > 15:
        #         print("  • ... (중간 생략)")
        #         print("  • 마지막 5개 캔들 시간:")
        #         for i, candle in enumerate(candles[-5:]):
        #             print(f"    [{len(candles)-5+i+1}] {candle['candle_date_time_utc']}")

        return candles, api_start, api_end

    def _get_previous_time(self, current_time: datetime, timeframe: str) -> datetime:
        """시간 단위에 따라 이전 시간 계산"""
        if timeframe == "1m":
            return current_time - timedelta(minutes=1)
        elif timeframe == "5m":
            return current_time - timedelta(minutes=5)
        elif timeframe == "1h":
            return current_time - timedelta(hours=1)
        else:
            return current_time - timedelta(minutes=1)  # 기본값

    def measure_performance(self, func, *args, **kwargs) -> Dict[str, float]:
        """함수 성능 측정"""
        # 메모리 측정 시작
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # 실행 시간 측정
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        # 메모리 측정 완료
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = memory_after - memory_before

        execution_time = (end_time - start_time) * 1000  # ms

        return {
            "execution_time_ms": execution_time,
            "memory_delta_mb": memory_delta,
            "result_count": len(result) if isinstance(result, list) else 0,
            "result": result
        }

    def run_comparison_test(self, config: Dict) -> Dict:
        """
        단일 설정에 대한 4가지 방식 비교 테스트

        Args:
            config: 테스트 설정

        Returns:
            Dict: 성능 비교 결과
        """
        symbol = "KRW-BTC"
        timeframe = config["timeframe"]

        # 테스트 데이터 생성
        api_candles, api_start, api_end = self.create_mock_api_candles(config)

        # 🚀 4가지 감지기 생성
        original_detector = OriginalGapDetector(symbol, timeframe)
        vectorized_detector = VectorizedGapDetector(symbol, timeframe)
        optimized_detector = OptimizedGapDetector(symbol, timeframe)
        pure_numpy_detector = PureNumpyGapDetector(symbol, timeframe)

        # 반복 테스트를 위한 결과 저장
        all_detectors = {
            "original": (original_detector, "detect_gaps_with_preprocessing"),
            "vectorized": (vectorized_detector, "detect_gaps_no_preprocessing"),
            "optimized": (optimized_detector, "detect_gaps_no_preprocessing"),
            "pure_numpy": (pure_numpy_detector, "detect_gaps_no_preprocessing")
        }

        results = {}
        for method_name, (detector, method_func) in all_detectors.items():
            results[method_name] = {
                "times": [],
                "memories": [],
                "gap_count": 0,
                "detector": detector
            }

        print(f"🔍 성능 테스트: {config['name']} ({REPEAT_COUNT}회 반복, 4가지 방식)")

        # 반복 테스트 실행
        for i in range(REPEAT_COUNT):
            for method_name, (detector, method_func) in all_detectors.items():
                # 가비지 컬렉션으로 메모리 정리
                gc.collect()

                try:
                    # 메서드 호출
                    func = getattr(detector, method_func)
                    if method_name == "original":
                        metrics = self.measure_performance(
                            func, api_candles, api_start, api_end, "test_ref"
                        )
                    else:
                        metrics = self.measure_performance(
                            func, api_candles, api_start, api_end, "test_ref", is_first_chunk=True
                        )

                    results[method_name]["times"].append(metrics["execution_time_ms"])
                    results[method_name]["memories"].append(metrics["memory_delta_mb"])

                    if i == 0:  # 첫 번째 결과만 저장
                        results[method_name]["gap_count"] = metrics["result_count"]

                except Exception as e:
                    print(f"{method_name} 방식 실패 (#{i + 1}): {e}")
                    continue

        # 결과 정확성 검증 (모든 방식의 Gap 개수가 일치하는지)
        gap_counts = [results[method]["gap_count"] for method in results.keys()]
        accuracy_match = len(set(gap_counts)) <= 1  # 모든 값이 동일하면 True

        # 통계 계산
        def calculate_stats(values):
            if not values:
                return {"mean": 0, "min": 0, "max": 0, "std": 0}
            return {
                "mean": np.mean(values),
                "min": np.min(values),
                "max": np.max(values),
                "std": np.std(values)
            }

        # 4가지 방식의 통계 계산
        stats_results = {}
        for method_name, data in results.items():
            stats_results[method_name] = {
                "time_stats": calculate_stats(data["times"]),
                "memory_stats": calculate_stats(data["memories"]),
                "gap_count": data["gap_count"],
                "method": data["detector"].get_stats()
            }

        # 성능 개선율 계산 (기존 방식 대비)
        original_time = stats_results["original"]["time_stats"]["mean"]
        comparisons = {}

        for method_name, stats in stats_results.items():
            if method_name != "original" and original_time > 0:
                speed_improvement = ((original_time - stats["time_stats"]["mean"])
                                   / original_time * 100)
                comparisons[method_name] = speed_improvement
            else:
                comparisons[method_name] = 0

        result = {
            "config": config,
            "test_data": {
                "candle_count": len(api_candles),
                "api_start": api_start,
                "api_end": api_end
            },
            "methods": stats_results,
            "comparisons": comparisons,
            "accuracy_match": accuracy_match,
            "valid_runs": min(len(data["times"]) for data in results.values())
        }

        return result

    def test_chunk_boundary_fix(self):
        """청크 경계 문제 해결 테스트"""
        print("\n🔧 청크 경계 문제 해결 테스트")

        symbol = "KRW-BTC"
        timeframe = "1m"

        # 청크 경계 시나리오 생성
        base_time = datetime(2025, 9, 21, 12, 20, 0, tzinfo=timezone.utc)

        # 청크1 데이터: [17,15,14,12] (16과 13 빈 캔들)
        chunk1_times = [
            base_time - timedelta(minutes=3),   # 17
            base_time - timedelta(minutes=5),   # 15 (16 빈 캔들)
            base_time - timedelta(minutes=6),   # 14
            base_time - timedelta(minutes=8),   # 12 (13 빈 캔들)
        ]

        # 청크2 데이터: [14,12,11,10] (13은 여전히 누락)
        chunk2_times = [
            base_time - timedelta(minutes=6),   # 14 (오버랩)
            base_time - timedelta(minutes=8),   # 12
            base_time - timedelta(minutes=9),   # 11
            base_time - timedelta(minutes=10),  # 10
        ]

        vectorized_detector = VectorizedGapDetector(symbol, timeframe)

        # 청크1 테스트 (is_first_chunk=True)
        chunk1_gaps = vectorized_detector.detect_gaps_vectorized(
            chunk1_times, symbol,
            base_time - timedelta(minutes=3),  # api_start = 17
            base_time - timedelta(minutes=8),  # api_end = 12
            "test_ref", is_first_chunk=True
        )

        # 청크2 테스트 (is_first_chunk=False, api_start +1틱 추가)
        chunk2_gaps = vectorized_detector.detect_gaps_vectorized(
            chunk2_times, symbol,
            base_time - timedelta(minutes=6),   # api_start = 14
            base_time - timedelta(minutes=10),  # api_end = 10
            "test_ref", is_first_chunk=False
        )

        print(f"  • 청크1 Gap 개수: {len(chunk1_gaps)}개")
        print(f"  • 청크2 Gap 개수: {len(chunk2_gaps)}개")
        print(f"  • 청크2 api_start +1틱 동작: {'✅ 성공' if len(chunk2_gaps) > 0 else '❌ 실패'}")

        return len(chunk1_gaps), len(chunk2_gaps)

    def run_all_tests(self) -> List[Dict]:
        """모든 테스트 설정에 대한 성능 비교 실행"""
        print("🚀 독립적인 성능 비교 테스트 시작")
        print(f"테스트 설정: {len(TEST_CONFIGS)}개, 반복: {REPEAT_COUNT}회")

        all_results = []

        for i, config in enumerate(TEST_CONFIGS):
            print(f"\n📊 테스트 {i + 1}/{len(TEST_CONFIGS)}: {config['name']}")

            try:
                result = self.run_comparison_test(config)
                all_results.append(result)
                self.print_result_summary(result)

            except Exception as e:
                print(f"테스트 실행 실패: {e}")

        # 청크 경계 테스트
        self.test_chunk_boundary_fix()

        return all_results

    def print_result_summary(self, result: Dict):
        """개별 테스트 결과 요약 출력 (4가지 방식)"""
        methods = result["methods"]
        comparisons = result["comparisons"]

        print("  📈 결과:")
        for method_name, stats in methods.items():
            improvement = comparisons.get(method_name, 0)
            method_display = {
                "original": "기존 방식",
                "vectorized": "벡터화",
                "optimized": "TimeUtils최적화",
                "pure_numpy": "순수Numpy"
            }.get(method_name, method_name)

            print(f"    • {method_display}: {stats['time_stats']['mean']:.2f}ms "
                  f"(±{stats['time_stats']['std']:.2f}) [{improvement:+.1f}%]")

        # Gap 정확성 표시
        gap_counts = [stats["gap_count"] for stats in methods.values()]
        gap_display = " / ".join(str(count) for count in gap_counts)
        accuracy_icon = "✅ 일치" if result["accuracy_match"] else "❌ 불일치"
        print(f"    • Gap 정확성: {accuracy_icon} ({gap_display})")

    def print_final_report(self, all_results: List[Dict]):
        """최종 종합 리포트 출력 (4가지 방식)"""
        print("\n" + "=" * 90)
        print("🎯 === 4가지 Gap 감지 방식 성능 비교 최종 리포트 ===")
        print("=" * 90)

        # 종합 통계
        total_tests = len(all_results)
        successful_tests = len([r for r in all_results if r["accuracy_match"]])

        # 평균 성능 개선율 계산
        method_improvements = {"vectorized": [], "optimized": [], "pure_numpy": []}
        for result in all_results:
            for method in method_improvements.keys():
                if method in result["comparisons"]:
                    method_improvements[method].append(result["comparisons"][method])

        avg_improvements = {
            method: np.mean(improvements) if improvements else 0
            for method, improvements in method_improvements.items()
        }

        print("📊 테스트 개요:")
        print(f"  • 총 테스트: {total_tests}개")
        print(f"  • 정확성 통과: {successful_tests}개")
        print(f"  • 정확성 통과율: {successful_tests / total_tests * 100:.1f}%")

        print("\n🚀 성능 개선 결과 (기존 방식 대비):")
        for method, improvement in avg_improvements.items():
            method_display = {
                "vectorized": "벡터화 방식",
                "optimized": "TimeUtils 최적화",
                "pure_numpy": "순수 Numpy"
            }.get(method, method)
            print(f"  • {method_display}: {improvement:+.1f}%")

        # 상세 결과 테이블
        print("\n📋 상세 결과:")
        print("테스트명\t캔들수\t기존(ms) 벡터화\tTimeUtils최적화\t순수Numpy 정확성")
        print("-" * 90)

        for result in all_results:
            config = result["config"]
            test_data = result["test_data"]
            methods = result["methods"]
            accuracy = "✅" if result["accuracy_match"] else "❌"

            times = {
                method: f"{stats['time_stats']['mean']:.2f}"
                for method, stats in methods.items()
            }

            print(f"{config['name']:<8}\t{test_data['candle_count']}\t"
                  f"{times.get('original', 'N/A')}\t"
                  f"{times.get('vectorized', 'N/A')}\t"
                  f"{times.get('optimized', 'N/A')}\t"
                  f"{times.get('pure_numpy', 'N/A')}\t{accuracy}")

        # 권장사항
        print("\n💡 최종 결론:")
        best_method = max(avg_improvements.items(), key=lambda x: x[1])
        best_improvement = best_method[1]
        best_name = {
            "vectorized": "벡터화 방식",
            "optimized": "TimeUtils 최적화",
            "pure_numpy": "순수 Numpy"
        }.get(best_method[0], best_method[0])

        if best_improvement > 100:
            print(f"  🎉 {best_name}이 {best_improvement:.1f}% 빠름 → {best_name} 강력 권장!")
        elif best_improvement > 50:
            print(f"  ✅ {best_name}이 {best_improvement:.1f}% 빠름 → {best_name} 권장")
        elif best_improvement > 20:
            print(f"  ⚠️ {best_name}이 {best_improvement:.1f}% 빠름 → 적정한 개선")
        elif best_improvement > 0:
            print(f"  ⚠️ {best_name}이 {best_improvement:.1f}% 빠름 → 미미한 개선")
        else:
            print("  ❌ 모든 최적화가 기존 방식보다 느림 → 기존 방식 유지")

        print("\n" + "=" * 90)


def main():
    """메인 테스트 실행 함수"""
    print("🔍 4가지 Gap 감지 방식 성능 비교")
    print("목적: 기존/벡터화/TimeUtils최적화/순수Numpy 방식 엄격한 성능 비교")
    print("-" * 70)

    # 각 테스트별로 다른 시드를 사용하도록 전역 시드 설정 제거
    print("🎲 각 테스트마다 고유 시드 사용")

    # 성능 비교 실행
    comparison = PerformanceComparison()

    try:
        all_results = comparison.run_all_tests()
        comparison.print_final_report(all_results)

        print("\n✅ 모든 성능 비교 테스트 완료")
        return True

    except Exception as e:
        print(f"\n❌ 테스트 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()

    if success:
        print("\n🎉 4가지 방식 성능 비교 완료")
    else:
        print("\n💥 성능 비교 실패")
