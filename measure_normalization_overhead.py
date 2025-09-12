"""
CandleDataProvider 요청 정규화 오버헤드 측정 도구
현재 복잡한 정규화 vs 단순한 순차 처리 성능 비교
"""

import time
import tracemalloc
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import statistics

from upbit_auto_trading.infrastructure.market_data.candle.candle_data_provider_new01 import CandleDataProvider
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import RequestInfo


class PerformanceMeasurer:
    """성능 측정 도구"""

    def __init__(self):
        self.provider = CandleDataProvider()

    def measure_normalization_overhead(self, test_cases: List[dict], iterations: int = 100) -> dict:
        """요청 정규화 오버헤드 측정"""

        results = {
            "test_cases": [],
            "summary": {}
        }

        print(f"🔍 요청 정규화 오버헤드 측정 시작 (반복: {iterations}회)")
        print("=" * 60)

        for i, case in enumerate(test_cases):
            print(f"\n📋 테스트 케이스 {i+1}: {case['name']}")

            # 메모리 추적 시작
            tracemalloc.start()

            times = []
            memory_peaks = []

            for iteration in range(iterations):
                # 시간 측정 시작
                start_time = time.perf_counter()
                start_memory = tracemalloc.get_traced_memory()[0]

                try:
                    # 실제 정규화 실행
                    chunks = self.provider.get_candles(**case['params'])

                    # 시간 측정 종료
                    end_time = time.perf_counter()
                    end_memory = tracemalloc.get_traced_memory()[1]  # peak

                    execution_time = (end_time - start_time) * 1000  # ms
                    memory_used = end_memory - start_memory  # bytes

                    times.append(execution_time)
                    memory_peaks.append(memory_used)

                    # 첫 번째 반복에서만 결과 정보 출력
                    if iteration == 0:
                        total_candles = sum(chunk.count for chunk in chunks)
                        print(f"   결과: {len(chunks)}개 청크, {total_candles}개 캔들")

                except Exception as e:
                    print(f"   ❌ 오류: {e}")
                    break

            tracemalloc.stop()

            if times:
                # 통계 계산
                avg_time = statistics.mean(times)
                median_time = statistics.median(times)
                min_time = min(times)
                max_time = max(times)
                std_time = statistics.stdev(times) if len(times) > 1 else 0

                avg_memory = statistics.mean(memory_peaks) / 1024  # KB

                case_result = {
                    "name": case['name'],
                    "params": case['params'],
                    "avg_time_ms": round(avg_time, 3),
                    "median_time_ms": round(median_time, 3),
                    "min_time_ms": round(min_time, 3),
                    "max_time_ms": round(max_time, 3),
                    "std_time_ms": round(std_time, 3),
                    "avg_memory_kb": round(avg_memory, 2),
                    "iterations": len(times)
                }

                results["test_cases"].append(case_result)

                print(f"   ⏱️ 평균: {avg_time:.3f}ms, 중앙값: {median_time:.3f}ms")
                print(f"   📊 범위: {min_time:.3f}ms ~ {max_time:.3f}ms (표준편차: {std_time:.3f}ms)")
                print(f"   💾 메모리: {avg_memory:.2f}KB")

        # 전체 요약
        if results["test_cases"]:
            all_times = [case["avg_time_ms"] for case in results["test_cases"]]
            all_memory = [case["avg_memory_kb"] for case in results["test_cases"]]

            results["summary"] = {
                "total_cases": len(results["test_cases"]),
                "overall_avg_time_ms": round(statistics.mean(all_times), 3),
                "overall_avg_memory_kb": round(statistics.mean(all_memory), 2),
                "fastest_case": min(results["test_cases"], key=lambda x: x["avg_time_ms"])["name"],
                "slowest_case": max(results["test_cases"], key=lambda x: x["avg_time_ms"])["name"]
            }

        return results

    def simulate_simple_approach_overhead(self, iterations: int = 100) -> dict:
        """단순한 순차 처리 방식의 시뮬레이션 오버헤드"""
        print(f"\n🚀 단순 순차 처리 시뮬레이션 (반복: {iterations}회)")
        print("=" * 60)

        times = []

        for iteration in range(iterations):
            start_time = time.perf_counter()

            # 단순 접근법 시뮬레이션
            # 1. 현재 시간 찍기
            current_time = datetime.now(timezone.utc)

            # 2. 첫 번째 요청 파라미터만 생성 (정규화 없음)
            first_request = {
                "market": "KRW-BTC",
                "count": 200,
                # to 파라미터 없음 - API가 알아서 처리
            }

            # 3. 후속 청크들은 실제 응답 기반으로 생성 (시뮬레이션)
            chunk_count = 35  # 7000개 캔들 가정
            for i in range(chunk_count):
                # 실제로는 이전 응답의 마지막 시간 사용
                mock_previous_end = current_time - timedelta(minutes=200 * i)
                next_request = {
                    "market": "KRW-BTC",
                    "count": 200,
                    "to": mock_previous_end
                }

            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # ms
            times.append(execution_time)

        if times:
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            min_time = min(times)
            max_time = max(times)

            print(f"   ⏱️ 평균: {avg_time:.3f}ms, 중앙값: {median_time:.3f}ms")
            print(f"   📊 범위: {min_time:.3f}ms ~ {max_time:.3f}ms")

            return {
                "avg_time_ms": round(avg_time, 3),
                "median_time_ms": round(median_time, 3),
                "min_time_ms": round(min_time, 3),
                "max_time_ms": round(max_time, 3),
                "approach": "simple_sequential"
            }

        return {}


def main():
    """메인 측정 함수"""
    print("🎯 CandleDataProvider 성능 측정 도구")
    print(f"측정 시각: {datetime.now().isoformat()}")
    print("=" * 60)

    measurer = PerformanceMeasurer()

    # 다양한 테스트 케이스 준비
    test_cases = [
        {
            "name": "소량 요청 (count=100)",
            "params": {
                "symbol": "KRW-BTC",
                "timeframe": "1m",
                "count": 100
            }
        },
        {
            "name": "중간 요청 (count=1000)",
            "params": {
                "symbol": "KRW-BTC",
                "timeframe": "1m",
                "count": 1000
            }
        },
        {
            "name": "대량 요청 (count=7000)",
            "params": {
                "symbol": "KRW-BTC",
                "timeframe": "1m",
                "count": 7000
            }
        },
        {
            "name": "기간 요청 (to+end)",
            "params": {
                "symbol": "KRW-BTC",
                "timeframe": "1m",
                "to": datetime.now(timezone.utc),
                "end": datetime.now(timezone.utc) - timedelta(hours=12)
            }
        },
        {
            "name": "종료점 요청 (end만)",
            "params": {
                "symbol": "KRW-BTC",
                "timeframe": "1m",
                "end": datetime.now(timezone.utc) - timedelta(hours=6)
            }
        }
    ]

    # 현재 정규화 방식 측정
    normalization_results = measurer.measure_normalization_overhead(test_cases, iterations=50)

    # 단순 순차 방식 시뮬레이션
    simple_results = measurer.simulate_simple_approach_overhead(iterations=50)

    # 결과 비교
    print("\n" + "=" * 60)
    print("📊 성능 비교 결과")
    print("=" * 60)

    if normalization_results.get("summary"):
        summary = normalization_results["summary"]
        print(f"현재 정규화 방식 평균: {summary['overall_avg_time_ms']}ms")
        print(f"메모리 사용량 평균: {summary['overall_avg_memory_kb']}KB")
        print(f"가장 빠른 케이스: {summary['fastest_case']}")
        print(f"가장 느린 케이스: {summary['slowest_case']}")

    if simple_results:
        print(f"단순 순차 방식 평균: {simple_results['avg_time_ms']}ms")

        # 속도 비교
        if normalization_results.get("summary"):
            current_avg = normalization_results["summary"]["overall_avg_time_ms"]
            simple_avg = simple_results["avg_time_ms"]

            if simple_avg < current_avg:
                speedup = current_avg / simple_avg
                print(f"🚀 단순 방식이 {speedup:.1f}배 빠름")
            else:
                slowdown = simple_avg / current_avg
                print(f"⚠️ 단순 방식이 {slowdown:.1f}배 느림")

    print("\n💡 결론:")
    print("- 현재 정규화의 실제 오버헤드 수치")
    print("- 단순 순차 처리와의 성능 차이")
    print("- 메모리 사용량 비교")
    print("- 코드 복잡성 vs 성능 트레이드오프 판단 자료")


if __name__ == "__main__":
    main()
