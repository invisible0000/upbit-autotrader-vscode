"""
시간 계산 메서드 성능 비교 테스트
TimeUtils.get_aligned_time_by_ticks vs 기존 timedelta 방식

목적:
1. 성능 비교 (실행 시간)
2. 정확성 검증 (소수점 오차, 월/년봉 계산)
3. 메모리 사용량 비교
4. 다양한 시나리오에서의 동작 검증
"""

import time
import tracemalloc
from datetime import datetime, timezone, timedelta
from typing import Tuple

from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


class TimeCalculationComparison:
    """시간 계산 방식 비교 클래스"""

    def __init__(self):
        self.test_timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M', '1y']
        self.base_time = datetime(2024, 6, 15, 14, 32, 45, tzinfo=timezone.utc)

    # ===========================================
    # 기존 방식 (timedelta 기반)
    # ===========================================

    def old_method_single_tick_backward(self, base_time: datetime, timeframe: str) -> datetime:
        """기존 방식: 1틱 뒤로 이동"""
        aligned_time = TimeUtils.align_to_candle_boundary(base_time, timeframe)
        dt = TimeUtils.get_timeframe_delta(timeframe)
        return aligned_time - dt

    def old_method_multiple_ticks_backward(self, base_time: datetime, timeframe: str, tick_count: int) -> datetime:
        """기존 방식: 여러 틱 뒤로 이동"""
        aligned_time = TimeUtils.align_to_candle_boundary(base_time, timeframe)
        timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
        total_seconds = timeframe_seconds * tick_count
        return aligned_time - timedelta(seconds=total_seconds)

    def old_method_calculate_end_time(self, start_time: datetime, timeframe: str, count: int) -> datetime:
        """기존 방식: count 기반 종료 시간 계산"""
        timeframe_seconds = TimeUtils.get_timeframe_delta(timeframe).total_seconds()
        return start_time - timedelta(seconds=(count - 1) * timeframe_seconds)

    # ===========================================
    # 새로운 방식 (get_aligned_time_by_ticks 기반)
    # ===========================================

    def new_method_single_tick_backward(self, base_time: datetime, timeframe: str) -> datetime:
        """새로운 방식: 1틱 뒤로 이동"""
        return TimeUtils.get_aligned_time_by_ticks(base_time, timeframe, -1)

    def new_method_multiple_ticks_backward(self, base_time: datetime, timeframe: str, tick_count: int) -> datetime:
        """새로운 방식: 여러 틱 뒤로 이동"""
        return TimeUtils.get_aligned_time_by_ticks(base_time, timeframe, -tick_count)

    def new_method_calculate_end_time(self, start_time: datetime, timeframe: str, count: int) -> datetime:
        """새로운 방식: count 기반 종료 시간 계산"""
        return TimeUtils.get_aligned_time_by_ticks(start_time, timeframe, -(count - 1))

    # ===========================================
    # 성능 측정 유틸리티
    # ===========================================

    def measure_execution_time(self, func, *args, iterations: int = 10000) -> Tuple[float, any]:
        """실행 시간 측정"""
        # 워밍업
        for _ in range(100):
            result = func(*args)

        # 실제 측정
        start_time = time.perf_counter()
        for _ in range(iterations):
            result = func(*args)
        end_time = time.perf_counter()

        avg_time = (end_time - start_time) / iterations
        return avg_time * 1_000_000, result  # 마이크로초 단위로 반환

    def measure_memory_usage(self, func, *args) -> Tuple[int, any]:
        """메모리 사용량 측정"""
        tracemalloc.start()

        result = func(*args)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return peak, result

    # ===========================================
    # 성능 비교 테스트
    # ===========================================

    def test_single_tick_performance(self) -> dict:
        """1틱 이동 성능 비교"""
        results = {}

        for timeframe in self.test_timeframes:
            print(f"\n📊 1틱 이동 성능 비교 - {timeframe}")

            # 기존 방식
            old_time, old_result = self.measure_execution_time(
                self.old_method_single_tick_backward, self.base_time, timeframe
            )
            old_memory, _ = self.measure_memory_usage(
                self.old_method_single_tick_backward, self.base_time, timeframe
            )

            # 새로운 방식
            new_time, new_result = self.measure_execution_time(
                self.new_method_single_tick_backward, self.base_time, timeframe
            )
            new_memory, _ = self.measure_memory_usage(
                self.new_method_single_tick_backward, self.base_time, timeframe
            )

            # 결과 비교
            time_improvement = ((old_time - new_time) / old_time) * 100
            memory_improvement = ((old_memory - new_memory) / old_memory) * 100 if old_memory > 0 else 0

            results[timeframe] = {
                'old_time_us': round(old_time, 3),
                'new_time_us': round(new_time, 3),
                'time_improvement_percent': round(time_improvement, 2),
                'old_memory_bytes': old_memory,
                'new_memory_bytes': new_memory,
                'memory_improvement_percent': round(memory_improvement, 2),
                'results_match': old_result == new_result,
                'old_result': old_result,
                'new_result': new_result
            }

            print(f"  기존 방식: {old_time:.3f}μs, {old_memory}bytes")
            print(f"  새 방식: {new_time:.3f}μs, {new_memory}bytes")
            print(f"  성능 개선: {time_improvement:+.2f}%, 메모리: {memory_improvement:+.2f}%")
            print(f"  결과 일치: {old_result == new_result}")

            if old_result != new_result:
                print("  ❌ 결과 불일치!")
                print(f"     기존: {old_result}")
                print(f"     새로운: {new_result}")

        return results

    def test_multiple_ticks_performance(self) -> dict:
        """여러 틱 이동 성능 비교"""
        tick_counts = [10, 100, 1000, 10000]
        results = {}

        for timeframe in ['1m', '5m', '1h', '1d']:  # 대표적인 타임프레임만 테스트
            results[timeframe] = {}

            for tick_count in tick_counts:
                print(f"\n📊 {tick_count}틱 이동 성능 비교 - {timeframe}")

                # 기존 방식
                old_time, old_result = self.measure_execution_time(
                    self.old_method_multiple_ticks_backward, self.base_time, timeframe, tick_count
                )

                # 새로운 방식
                new_time, new_result = self.measure_execution_time(
                    self.new_method_multiple_ticks_backward, self.base_time, timeframe, tick_count
                )

                time_improvement = ((old_time - new_time) / old_time) * 100

                results[timeframe][tick_count] = {
                    'old_time_us': round(old_time, 3),
                    'new_time_us': round(new_time, 3),
                    'time_improvement_percent': round(time_improvement, 2),
                    'results_match': old_result == new_result,
                    'old_result': old_result,
                    'new_result': new_result
                }

                print(f"  기존 방식: {old_time:.3f}μs")
                print(f"  새 방식: {new_time:.3f}μs")
                print(f"  성능 개선: {time_improvement:+.2f}%")
                print(f"  결과 일치: {old_result == new_result}")

                if old_result != new_result:
                    print(f"  ❌ 결과 불일치!")
                    print(f"     기존: {old_result}")
                    print(f"     새로운: {new_result}")

        return results

    def test_end_time_calculation_performance(self) -> dict:
        """종료 시간 계산 성능 비교"""
        counts = [200, 1000, 5000, 10000]  # 청크 사이즈 기준
        results = {}

        for timeframe in ['1m', '5m', '1h', '1d']:
            results[timeframe] = {}

            for count in counts:
                print(f"\n📊 {count}개 종료시간 계산 성능 비교 - {timeframe}")

                # 기존 방식
                old_time, old_result = self.measure_execution_time(
                    self.old_method_calculate_end_time, self.base_time, timeframe, count
                )

                # 새로운 방식
                new_time, new_result = self.measure_execution_time(
                    self.new_method_calculate_end_time, self.base_time, timeframe, count
                )

                time_improvement = ((old_time - new_time) / old_time) * 100

                results[timeframe][count] = {
                    'old_time_us': round(old_time, 3),
                    'new_time_us': round(new_time, 3),
                    'time_improvement_percent': round(time_improvement, 2),
                    'results_match': old_result == new_result,
                    'old_result': old_result,
                    'new_result': new_result
                }

                print(f"  기존 방식: {old_time:.3f}μs")
                print(f"  새 방식: {new_time:.3f}μs")
                print(f"  성능 개선: {time_improvement:+.2f}%")
                print(f"  결과 일치: {old_result == new_result}")

                if old_result != new_result:
                    print(f"  ❌ 결과 불일치!")
                    print(f"     기존: {old_result}")
                    print(f"     새로운: {new_result}")

        return results

    # ===========================================
    # 정확성 검증 테스트
    # ===========================================

    def test_accuracy_edge_cases(self) -> dict:
        """경계 조건에서의 정확성 검증"""
        results = {}

        edge_cases = [
            # 월말 경계
            datetime(2024, 2, 29, 14, 30, 0, tzinfo=timezone.utc),  # 윤년 2월 29일
            datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc),     # 3월 1일 자정
            datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc),  # 연말 마지막

            # 주말 경계
            datetime(2024, 6, 16, 23, 59, 0, tzinfo=timezone.utc),  # 일요일 늦은 시간
            datetime(2024, 6, 17, 0, 0, 0, tzinfo=timezone.utc),    # 월요일 자정

            # DST 경계 (미국 기준, UTC로는 영향 없지만 테스트용)
            datetime(2024, 3, 10, 2, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 11, 3, 2, 0, 0, tzinfo=timezone.utc),
        ]

        for i, test_time in enumerate(edge_cases):
            results[f'edge_case_{i}'] = {}
            print(f"\n📊 경계 조건 정확성 테스트 - {test_time}")

            for timeframe in ['1M', '1w', '1d', '1h']:
                old_result = self.old_method_single_tick_backward(test_time, timeframe)
                new_result = self.new_method_single_tick_backward(test_time, timeframe)

                results[f'edge_case_{i}'][timeframe] = {
                    'test_time': test_time,
                    'old_result': old_result,
                    'new_result': new_result,
                    'results_match': old_result == new_result
                }

                print(f"  {timeframe}: 일치={old_result == new_result}")
                if old_result != new_result:
                    print(f"    기존: {old_result}")
                    print(f"    새로운: {new_result}")

        return results

    def test_precision_loss(self) -> dict:
        """소수점 정밀도 손실 테스트"""
        results = {}

        # 매우 큰 틱 수로 정밀도 테스트
        large_tick_counts = [100000, 1000000, 10000000]

        for timeframe in ['1s', '1m', '1h']:
            results[timeframe] = {}

            for tick_count in large_tick_counts:
                print(f"\n📊 정밀도 테스트 - {timeframe}, {tick_count:,}틱")

                # 기존 방식
                try:
                    old_result = self.old_method_multiple_ticks_backward(
                        self.base_time, timeframe, tick_count
                    )
                    old_success = True
                except Exception as e:
                    old_result = str(e)
                    old_success = False

                # 새로운 방식
                try:
                    new_result = self.new_method_multiple_ticks_backward(
                        self.base_time, timeframe, tick_count
                    )
                    new_success = True
                except Exception as e:
                    new_result = str(e)
                    new_success = False

                results[timeframe][tick_count] = {
                    'old_result': old_result,
                    'new_result': new_result,
                    'old_success': old_success,
                    'new_success': new_success,
                    'results_match': old_result == new_result if old_success and new_success else False
                }

                print(f"  기존 방식: {'성공' if old_success else '실패'}")
                print(f"  새 방식: {'성공' if new_success else '실패'}")
                if old_success and new_success:
                    print(f"  결과 일치: {old_result == new_result}")

        return results

    # ===========================================
    # 전체 테스트 실행
    # ===========================================

    def run_comprehensive_test(self) -> dict:
        """포괄적인 성능 및 정확성 테스트 실행"""
        print("🚀 시간 계산 메서드 포괄적 성능 비교 테스트 시작\n")
        print("=" * 80)

        all_results = {}

        # 1. 1틱 이동 성능 테스트
        print("\n1️⃣ 단일 틱 이동 성능 테스트")
        all_results['single_tick'] = self.test_single_tick_performance()

        # 2. 다중 틱 이동 성능 테스트
        print("\n2️⃣ 다중 틱 이동 성능 테스트")
        all_results['multiple_ticks'] = self.test_multiple_ticks_performance()

        # 3. 종료 시간 계산 성능 테스트
        print("\n3️⃣ 종료 시간 계산 성능 테스트")
        all_results['end_time_calculation'] = self.test_end_time_calculation_performance()

        # 4. 경계 조건 정확성 테스트
        print("\n4️⃣ 경계 조건 정확성 테스트")
        all_results['edge_cases'] = self.test_accuracy_edge_cases()

        # 5. 정밀도 손실 테스트
        print("\n5️⃣ 정밀도 손실 테스트")
        all_results['precision_loss'] = self.test_precision_loss()

        # 6. 종합 요약 생성
        print("\n6️⃣ 종합 요약 생성")
        all_results['summary'] = self.generate_summary(all_results)

        print("\n✅ 포괄적 테스트 완료!")
        print("=" * 80)

        return all_results

    def generate_summary(self, all_results: dict) -> dict:
        """테스트 결과 종합 요약"""
        summary = {
            'overall_performance_improvement': {},
            'accuracy_issues': [],
            'recommendations': []
        }

        # 1. 전체 성능 개선률 계산
        all_improvements = []

        # 단일 틱 성능
        for timeframe, result in all_results['single_tick'].items():
            all_improvements.append(result['time_improvement_percent'])

        # 다중 틱 성능
        for timeframe, counts in all_results['multiple_ticks'].items():
            for count, result in counts.items():
                all_improvements.append(result['time_improvement_percent'])

        summary['overall_performance_improvement'] = {
            'average': round(sum(all_improvements) / len(all_improvements), 2),
            'best': round(max(all_improvements), 2),
            'worst': round(min(all_improvements), 2),
            'total_tests': len(all_improvements)
        }

        # 2. 정확성 문제 수집
        # 단일 틱 정확성
        for timeframe, result in all_results['single_tick'].items():
            if not result['results_match']:
                summary['accuracy_issues'].append(f"단일틱 {timeframe}: 결과 불일치")

        # 경계 조건 정확성
        for case_name, timeframes in all_results['edge_cases'].items():
            for timeframe, result in timeframes.items():
                if not result['results_match']:
                    summary['accuracy_issues'].append(f"경계조건 {case_name} {timeframe}: 결과 불일치")

        # 3. 권장사항 생성
        avg_improvement = summary['overall_performance_improvement']['average']

        if avg_improvement > 20:
            summary['recommendations'].append("✅ 높은 성능 개선 효과 (20%+) - 적극 도입 권장")
        elif avg_improvement > 10:
            summary['recommendations'].append("⚠️ 중간 성능 개선 효과 (10~20%) - 도입 고려")
        elif avg_improvement > 0:
            summary['recommendations'].append("📊 낮은 성능 개선 효과 (0~10%) - 신중한 고려 필요")
        else:
            summary['recommendations'].append("❌ 성능 저하 - 현재 방식 유지 권장")

        if len(summary['accuracy_issues']) == 0:
            summary['recommendations'].append("✅ 정확성 문제 없음 - 안전한 교체 가능")
        else:
            summary['recommendations'].append("⚠️ 정확성 문제 발견 - 추가 검토 필요")

        return summary


# ===========================================
# 실제 테스트 실행 함수들
# ===========================================

def test_time_calculation_comparison():
    """pytest용 테스트 함수"""
    comparison = TimeCalculationComparison()
    results = comparison.run_comprehensive_test()

    # 기본적인 검증
    assert 'single_tick' in results
    assert 'summary' in results

    # 성능 개선이 있는지 확인 (최소 하나의 케이스에서)
    # single_tick_results = results['single_tick']
    # has_improvement 체크는 필요시 사용    print("\n📊 테스트 결과 요약:")
    print(f"평균 성능 개선: {results['summary']['overall_performance_improvement']['average']}%")
    print(f"정확성 문제: {len(results['summary']['accuracy_issues'])}건")
    print("권장사항:")
    for rec in results['summary']['recommendations']:
        print(f"  {rec}")

    return results


if __name__ == "__main__":
    # 직접 실행시 포괄적 테스트 수행
    comparison = TimeCalculationComparison()
    results = comparison.run_comprehensive_test()

    # 결과를 JSON으로 저장 (선택사항)
    import json
    with open('time_calculation_comparison_results.json', 'w', encoding='utf-8') as f:
        # datetime 객체를 문자열로 변환하여 저장
        def datetime_converter(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        json.dump(results, f, indent=2, default=datetime_converter, ensure_ascii=False)

    print("\n💾 결과가 'time_calculation_comparison_results.json'에 저장되었습니다.")
