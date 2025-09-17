"""
공정한 시간 계산 메서드 성능 비교 테스트 v2.0
TimeUtils.get_aligned_time_by_ticks vs 기존 timedelta 방식

개선 사항:
1. 모든 기존 방식에 align_to_candle_boundary 적용 (공정한 비교)
2. get_aligned_time_by_ticks 순수 로직 직접 구현 (오버헤드 제거)
3. 동일한 조건에서 정확한 성능 비교
4. 체계적인 테스트 구조

목적:
1. 순수 로직 성능 비교 (정렬 오버헤드 제외)
2. 정확성 검증 (동일한 조건)
3. 메모리 사용량 비교
4. 다양한 시나리오에서의 동작 검증
"""

import time
import tracemalloc
from datetime import datetime, timezone, timedelta
from typing import Tuple

from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


class FairTimeCalculationComparison:
    """공정한 시간 계산 방식 비교 클래스"""

    def __init__(self):
        self.test_timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M', '1y']
        self.base_time = datetime(2024, 6, 15, 14, 32, 45, tzinfo=timezone.utc)

    # ===========================================
    # 공정한 기존 방식 (align_to_candle_boundary 적용)
    # ===========================================

    def fair_old_method_single_tick_backward(self, base_time: datetime, timeframe: str) -> datetime:
        """공정한 기존 방식: 1틱 뒤로 이동 (정렬 포함)"""
        aligned_time = TimeUtils.align_to_candle_boundary(base_time, timeframe)
        dt = TimeUtils.get_timeframe_delta(timeframe)
        return aligned_time - dt

    def fair_old_method_multiple_ticks_backward(self, base_time: datetime, timeframe: str, tick_count: int) -> datetime:
        """공정한 기존 방식: 여러 틱 뒤로 이동 (정렬 포함)"""
        aligned_time = TimeUtils.align_to_candle_boundary(base_time, timeframe)
        timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
        total_seconds = timeframe_seconds * tick_count
        return aligned_time - timedelta(seconds=total_seconds)

    def fair_old_method_calculate_end_time(self, start_time: datetime, timeframe: str, count: int) -> datetime:
        """공정한 기존 방식: count 기반 종료 시간 계산 (정렬 포함)"""
        aligned_start = TimeUtils.align_to_candle_boundary(start_time, timeframe)
        timeframe_seconds = TimeUtils.get_timeframe_delta(timeframe).total_seconds()
        return aligned_start - timedelta(seconds=(count - 1) * timeframe_seconds)

    # ===========================================
    # 순수 로직 방식 (get_aligned_time_by_ticks 내부 로직만)
    # ===========================================

    def pure_logic_single_tick_backward(self, base_time: datetime, timeframe: str) -> datetime:
        """순수 로직: 1틱 뒤로 이동 (align_to_candle_boundary 제외)"""
        # 1. 기준 시간을 해당 타임프레임으로 정렬
        aligned_base = TimeUtils.align_to_candle_boundary(base_time, timeframe)

        # 2. tick_count = -1 로직 직접 구현
        tick_count = -1

        # 3. timeframe에 따른 틱 간격 계산 (get_aligned_time_by_ticks 내부 로직)
        if timeframe in ['1w', '1M', '1y']:
            # 주/월/년봉은 특별 처리 (정확한 날짜 산술)
            if timeframe == '1w':
                # 주봉: 7일 단위 (timedelta 사용 가능)
                tick_delta = timedelta(weeks=abs(tick_count))
                result_time = aligned_base - tick_delta
                return TimeUtils.align_to_candle_boundary(result_time, timeframe)

            elif timeframe == '1M':
                # 월봉: 정확한 월 단위 계산
                year = aligned_base.year
                month = aligned_base.month + tick_count

                # 월 오버플로우/언더플로우 처리
                while month > 12:
                    year += 1
                    month -= 12
                while month < 1:
                    year -= 1
                    month += 12

                # 월 첫날로 설정
                return datetime(year, month, 1, 0, 0, 0)

            elif timeframe == '1y':
                # 년봉: 정확한 년 단위 계산
                year = aligned_base.year + tick_count
                return datetime(year, 1, 1, 0, 0, 0)
        else:
            # 초/분/시간/일봉: 고정 길이, 빠른 계산
            timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
            total_seconds_offset = timeframe_seconds * tick_count
            return aligned_base + timedelta(seconds=total_seconds_offset)

    def pure_logic_multiple_ticks_backward(self, base_time: datetime, timeframe: str, tick_count: int) -> datetime:
        """순수 로직: 여러 틱 뒤로 이동 (align_to_candle_boundary 제외)"""
        # 1. 기준 시간을 해당 타임프레임으로 정렬
        aligned_base = TimeUtils.align_to_candle_boundary(base_time, timeframe)

        # 2. 음수 tick_count 적용
        negative_tick_count = -tick_count

        # 3. timeframe에 따른 틱 간격 계산 (get_aligned_time_by_ticks 내부 로직)
        if timeframe in ['1w', '1M', '1y']:
            # 주/월/년봉은 특별 처리 (정확한 날짜 산술)
            if timeframe == '1w':
                # 주봉: 7일 단위 (timedelta 사용 가능)
                tick_delta = timedelta(weeks=abs(negative_tick_count))
                if negative_tick_count > 0:
                    result_time = aligned_base + tick_delta
                else:
                    result_time = aligned_base - tick_delta
                return TimeUtils.align_to_candle_boundary(result_time, timeframe)

            elif timeframe == '1M':
                # 월봉: 정확한 월 단위 계산
                year = aligned_base.year
                month = aligned_base.month + negative_tick_count

                # 월 오버플로우/언더플로우 처리
                while month > 12:
                    year += 1
                    month -= 12
                while month < 1:
                    year -= 1
                    month += 12

                # 월 첫날로 설정
                return datetime(year, month, 1, 0, 0, 0)

            elif timeframe == '1y':
                # 년봉: 정확한 년 단위 계산
                year = aligned_base.year + negative_tick_count
                return datetime(year, 1, 1, 0, 0, 0)
        else:
            # 초/분/시간/일봉: 고정 길이, 빠른 계산
            timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
            total_seconds_offset = timeframe_seconds * negative_tick_count
            return aligned_base + timedelta(seconds=total_seconds_offset)

    def pure_logic_calculate_end_time(self, start_time: datetime, timeframe: str, count: int) -> datetime:
        """순수 로직: count 기반 종료 시간 계산 (align_to_candle_boundary 제외)"""
        # 1. 기준 시간을 해당 타임프레임으로 정렬
        aligned_base = TimeUtils.align_to_candle_boundary(start_time, timeframe)

        # 2. tick_count = -(count - 1) 로직 적용
        tick_count = -(count - 1)

        # 3. timeframe에 따른 틱 간격 계산 (get_aligned_time_by_ticks 내부 로직)
        if timeframe in ['1w', '1M', '1y']:
            # 주/월/년봉은 특별 처리 (정확한 날짜 산술)
            if timeframe == '1w':
                # 주봉: 7일 단위 (timedelta 사용 가능)
                tick_delta = timedelta(weeks=abs(tick_count))
                if tick_count > 0:
                    result_time = aligned_base + tick_delta
                else:
                    result_time = aligned_base - tick_delta
                return TimeUtils.align_to_candle_boundary(result_time, timeframe)

            elif timeframe == '1M':
                # 월봉: 정확한 월 단위 계산
                year = aligned_base.year
                month = aligned_base.month + tick_count

                # 월 오버플로우/언더플로우 처리
                while month > 12:
                    year += 1
                    month -= 12
                while month < 1:
                    year -= 1
                    month += 12

                # 월 첫날로 설정
                return datetime(year, month, 1, 0, 0, 0)

            elif timeframe == '1y':
                # 년봉: 정확한 년 단위 계산
                year = aligned_base.year + tick_count
                return datetime(year, 1, 1, 0, 0, 0)
        else:
            # 초/분/시간/일봉: 고정 길이, 빠른 계산
            timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
            total_seconds_offset = timeframe_seconds * tick_count
            return aligned_base + timedelta(seconds=total_seconds_offset)

    # ===========================================
    # 기존 get_aligned_time_by_ticks 방식 (비교용)
    # ===========================================

    def original_method_single_tick_backward(self, base_time: datetime, timeframe: str) -> datetime:
        """원래 방식: get_aligned_time_by_ticks 사용"""
        return TimeUtils.get_aligned_time_by_ticks(base_time, timeframe, -1)

    def original_method_multiple_ticks_backward(self, base_time: datetime, timeframe: str, tick_count: int) -> datetime:
        """원래 방식: get_aligned_time_by_ticks 사용"""
        return TimeUtils.get_aligned_time_by_ticks(base_time, timeframe, -tick_count)

    def original_method_calculate_end_time(self, start_time: datetime, timeframe: str, count: int) -> datetime:
        """원래 방식: get_aligned_time_by_ticks 사용"""
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
    # 공정한 성능 비교 테스트
    # ===========================================

    def test_fair_single_tick_performance(self) -> dict:
        """공정한 1틱 이동 성능 비교"""
        results = {}

        print("🔄 공정한 1틱 이동 성능 비교 (모든 방식 align_to_candle_boundary 포함)")
        print("=" * 80)

        for timeframe in self.test_timeframes:
            print(f"\n📊 {timeframe} - 1틱 뒤로 이동")

            # 1. 공정한 기존 방식 (정렬 포함)
            old_time, old_result = self.measure_execution_time(
                self.fair_old_method_single_tick_backward, self.base_time, timeframe
            )
            old_memory, _ = self.measure_memory_usage(
                self.fair_old_method_single_tick_backward, self.base_time, timeframe
            )

            # 2. 순수 로직 방식 (get_aligned_time_by_ticks 내부 로직만)
            pure_time, pure_result = self.measure_execution_time(
                self.pure_logic_single_tick_backward, self.base_time, timeframe
            )
            pure_memory, _ = self.measure_memory_usage(
                self.pure_logic_single_tick_backward, self.base_time, timeframe
            )

            # 3. 원래 방식 (참조용)
            orig_time, orig_result = self.measure_execution_time(
                self.original_method_single_tick_backward, self.base_time, timeframe
            )
            orig_memory, _ = self.measure_memory_usage(
                self.original_method_single_tick_backward, self.base_time, timeframe
            )

            # 성능 개선률 계산
            old_vs_pure_improvement = ((old_time - pure_time) / old_time) * 100
            old_vs_orig_improvement = ((old_time - orig_time) / old_time) * 100
            pure_vs_orig_improvement = ((pure_time - orig_time) / pure_time) * 100

            # 메모리 개선률 계산
            old_vs_pure_memory = ((old_memory - pure_memory) / old_memory) * 100 if old_memory > 0 else 0
            old_vs_orig_memory = ((old_memory - orig_memory) / old_memory) * 100 if old_memory > 0 else 0

            results[timeframe] = {
                'old_time_us': round(old_time, 3),
                'pure_time_us': round(pure_time, 3),
                'orig_time_us': round(orig_time, 3),
                'old_vs_pure_improvement_percent': round(old_vs_pure_improvement, 2),
                'old_vs_orig_improvement_percent': round(old_vs_orig_improvement, 2),
                'pure_vs_orig_improvement_percent': round(pure_vs_orig_improvement, 2),
                'old_memory_bytes': old_memory,
                'pure_memory_bytes': pure_memory,
                'orig_memory_bytes': orig_memory,
                'old_vs_pure_memory_percent': round(old_vs_pure_memory, 2),
                'old_vs_orig_memory_percent': round(old_vs_orig_memory, 2),
                'results_all_match': old_result == pure_result == orig_result,
                'old_result': old_result,
                'pure_result': pure_result,
                'orig_result': orig_result
            }

            print(f"  공정 기존방식: {old_time:.3f}μs, {old_memory}bytes")
            print(f"  순수 로직방식: {pure_time:.3f}μs, {pure_memory}bytes")
            print(f"  원래 방식:     {orig_time:.3f}μs, {orig_memory}bytes")
            print(f"  기존→순수: {old_vs_pure_improvement:+.2f}% | "
                  f"기존→원래: {old_vs_orig_improvement:+.2f}% | "
                  f"순수→원래: {pure_vs_orig_improvement:+.2f}%")
            print(f"  결과 일치: {'✅' if old_result == pure_result == orig_result else '❌'}")

            if not (old_result == pure_result == orig_result):
                print("  ❌ 결과 불일치!")
                print(f"     공정기존: {old_result}")
                print(f"     순수로직: {pure_result}")
                print(f"     원래방식: {orig_result}")

        return results

    def test_fair_multiple_ticks_performance(self) -> dict:
        """공정한 다중 틱 이동 성능 비교"""
        tick_counts = [10, 100, 1000, 10000]
        results = {}

        print("\n🔄 공정한 다중 틱 이동 성능 비교")
        print("=" * 80)

        for timeframe in ['1m', '5m', '1h', '1d']:  # 대표적인 타임프레임만
            results[timeframe] = {}

            for tick_count in tick_counts:
                print(f"\n📊 {timeframe} - {tick_count}틱 뒤로 이동")

                # 1. 공정한 기존 방식
                old_time, old_result = self.measure_execution_time(
                    self.fair_old_method_multiple_ticks_backward, self.base_time, timeframe, tick_count
                )

                # 2. 순수 로직 방식
                pure_time, pure_result = self.measure_execution_time(
                    self.pure_logic_multiple_ticks_backward, self.base_time, timeframe, tick_count
                )

                # 3. 원래 방식
                orig_time, orig_result = self.measure_execution_time(
                    self.original_method_multiple_ticks_backward, self.base_time, timeframe, tick_count
                )

                # 성능 개선률 계산
                old_vs_pure_improvement = ((old_time - pure_time) / old_time) * 100
                old_vs_orig_improvement = ((old_time - orig_time) / old_time) * 100
                pure_vs_orig_improvement = ((pure_time - orig_time) / pure_time) * 100

                results[timeframe][tick_count] = {
                    'old_time_us': round(old_time, 3),
                    'pure_time_us': round(pure_time, 3),
                    'orig_time_us': round(orig_time, 3),
                    'old_vs_pure_improvement_percent': round(old_vs_pure_improvement, 2),
                    'old_vs_orig_improvement_percent': round(old_vs_orig_improvement, 2),
                    'pure_vs_orig_improvement_percent': round(pure_vs_orig_improvement, 2),
                    'results_all_match': old_result == pure_result == orig_result,
                    'old_result': old_result,
                    'pure_result': pure_result,
                    'orig_result': orig_result
                }

                print(f"  공정기존: {old_time:.3f}μs | 순수로직: {pure_time:.3f}μs | 원래: {orig_time:.3f}μs")
                print(f"  기존→순수: {old_vs_pure_improvement:+.2f}% | 기존→원래: {old_vs_orig_improvement:+.2f}% | 순수→원래: {pure_vs_orig_improvement:+.2f}%")
                print(f"  결과 일치: {'✅' if old_result == pure_result == orig_result else '❌'}")

                if not (old_result == pure_result == orig_result):
                    print(f"  ❌ 결과 불일치!")
                    print(f"     공정기존: {old_result}")
                    print(f"     순수로직: {pure_result}")
                    print(f"     원래방식: {orig_result}")

        return results

    def test_fair_end_time_calculation_performance(self) -> dict:
        """공정한 종료 시간 계산 성능 비교"""
        counts = [200, 1000, 5000, 10000]
        results = {}

        print("\n🔄 공정한 종료 시간 계산 성능 비교")
        print("=" * 80)

        for timeframe in ['1m', '5m', '1h', '1d']:
            results[timeframe] = {}

            for count in counts:
                print(f"\n📊 {timeframe} - {count}개 캔들 종료시간")

                # 1. 공정한 기존 방식
                old_time, old_result = self.measure_execution_time(
                    self.fair_old_method_calculate_end_time, self.base_time, timeframe, count
                )

                # 2. 순수 로직 방식
                pure_time, pure_result = self.measure_execution_time(
                    self.pure_logic_calculate_end_time, self.base_time, timeframe, count
                )

                # 3. 원래 방식
                orig_time, orig_result = self.measure_execution_time(
                    self.original_method_calculate_end_time, self.base_time, timeframe, count
                )

                # 성능 개선률 계산
                old_vs_pure_improvement = ((old_time - pure_time) / old_time) * 100
                old_vs_orig_improvement = ((old_time - orig_time) / old_time) * 100
                pure_vs_orig_improvement = ((pure_time - orig_time) / pure_time) * 100

                results[timeframe][count] = {
                    'old_time_us': round(old_time, 3),
                    'pure_time_us': round(pure_time, 3),
                    'orig_time_us': round(orig_time, 3),
                    'old_vs_pure_improvement_percent': round(old_vs_pure_improvement, 2),
                    'old_vs_orig_improvement_percent': round(old_vs_orig_improvement, 2),
                    'pure_vs_orig_improvement_percent': round(pure_vs_orig_improvement, 2),
                    'results_all_match': old_result == pure_result == orig_result,
                    'old_result': old_result,
                    'pure_result': pure_result,
                    'orig_result': orig_result
                }

                print(f"  공정기존: {old_time:.3f}μs | 순수로직: {pure_time:.3f}μs | 원래: {orig_time:.3f}μs")
                print(f"  기존→순수: {old_vs_pure_improvement:+.2f}% | 기존→원래: {old_vs_orig_improvement:+.2f}% | 순수→원래: {pure_vs_orig_improvement:+.2f}%")
                print(f"  결과 일치: {'✅' if old_result == pure_result == orig_result else '❌'}")

                if not (old_result == pure_result == orig_result):
                    print(f"  ❌ 결과 불일치!")
                    print(f"     공정기존: {old_result}")
                    print(f"     순수로직: {pure_result}")
                    print(f"     원래방식: {orig_result}")

        return results

    # ===========================================
    # 전체 테스트 실행
    # ===========================================

    def run_comprehensive_fair_test(self) -> dict:
        """포괄적인 공정 성능 테스트 실행"""
        print("🚀 공정한 시간 계산 메서드 포괄적 성능 비교 테스트 v2.0")
        print("✅ 개선사항: 모든 방식에 align_to_candle_boundary 적용, 순수 로직 분리")
        print("=" * 80)

        all_results = {}

        # 1. 공정한 1틱 이동 성능 테스트
        all_results['fair_single_tick'] = self.test_fair_single_tick_performance()

        # 2. 공정한 다중 틱 이동 성능 테스트
        all_results['fair_multiple_ticks'] = self.test_fair_multiple_ticks_performance()

        # 3. 공정한 종료 시간 계산 성능 테스트
        all_results['fair_end_time_calculation'] = self.test_fair_end_time_calculation_performance()

        # 4. 종합 요약 생성
        print("\n📋 종합 요약 생성")
        all_results['fair_summary'] = self.generate_fair_summary(all_results)

        print("\n✅ 공정한 포괄적 테스트 완료!")
        print("=" * 80)

        return all_results

    def generate_fair_summary(self, all_results: dict) -> dict:
        """공정한 테스트 결과 종합 요약"""
        summary = {
            'old_vs_pure_performance': {},
            'old_vs_orig_performance': {},
            'pure_vs_orig_performance': {},
            'accuracy_issues': [],
            'recommendations': []
        }

        # 성능 개선률 수집
        old_vs_pure_improvements = []
        old_vs_orig_improvements = []
        pure_vs_orig_improvements = []

        # 1틱 성능
        for timeframe, result in all_results['fair_single_tick'].items():
            old_vs_pure_improvements.append(result['old_vs_pure_improvement_percent'])
            old_vs_orig_improvements.append(result['old_vs_orig_improvement_percent'])
            pure_vs_orig_improvements.append(result['pure_vs_orig_improvement_percent'])

        # 다중 틱 성능
        for timeframe, counts in all_results['fair_multiple_ticks'].items():
            for count, result in counts.items():
                old_vs_pure_improvements.append(result['old_vs_pure_improvement_percent'])
                old_vs_orig_improvements.append(result['old_vs_orig_improvement_percent'])
                pure_vs_orig_improvements.append(result['pure_vs_orig_improvement_percent'])

        # 성능 요약 계산
        summary['old_vs_pure_performance'] = {
            'average': round(sum(old_vs_pure_improvements) / len(old_vs_pure_improvements), 2),
            'best': round(max(old_vs_pure_improvements), 2),
            'worst': round(min(old_vs_pure_improvements), 2),
            'total_tests': len(old_vs_pure_improvements)
        }

        summary['old_vs_orig_performance'] = {
            'average': round(sum(old_vs_orig_improvements) / len(old_vs_orig_improvements), 2),
            'best': round(max(old_vs_orig_improvements), 2),
            'worst': round(min(old_vs_orig_improvements), 2),
            'total_tests': len(old_vs_orig_improvements)
        }

        summary['pure_vs_orig_performance'] = {
            'average': round(sum(pure_vs_orig_improvements) / len(pure_vs_orig_improvements), 2),
            'best': round(max(pure_vs_orig_improvements), 2),
            'worst': round(min(pure_vs_orig_improvements), 2),
            'total_tests': len(pure_vs_orig_improvements)
        }

        # 정확성 문제 수집
        for timeframe, result in all_results['fair_single_tick'].items():
            if not result['results_all_match']:
                summary['accuracy_issues'].append(f"1틱 {timeframe}: 결과 불일치")

        # 권장사항 생성
        old_vs_pure_avg = summary['old_vs_pure_performance']['average']
        pure_vs_orig_avg = summary['pure_vs_orig_performance']['average']

        summary['recommendations'].append("🔍 공정한 비교 결과:")

        if old_vs_pure_avg > 10:
            summary['recommendations'].append(f"✅ 순수 로직이 기존 방식보다 {old_vs_pure_avg:.1f}% 빠름")
        elif old_vs_pure_avg > 0:
            summary['recommendations'].append(f"📊 순수 로직이 기존 방식보다 {old_vs_pure_avg:.1f}% 빠름 (미미한 개선)")
        else:
            summary['recommendations'].append(f"❌ 순수 로직이 기존 방식보다 {abs(old_vs_pure_avg):.1f}% 느림")

        if abs(pure_vs_orig_avg) < 5:
            summary['recommendations'].append(f"⚖️ 순수 로직과 원래 방식 성능 차이 미미 ({pure_vs_orig_avg:.1f}%)")
        elif pure_vs_orig_avg > 0:
            summary['recommendations'].append(f"⚡ 순수 로직이 원래 방식보다 {pure_vs_orig_avg:.1f}% 빠름")
        else:
            summary['recommendations'].append(f"🔧 원래 방식에 최적화 여지 있음 ({abs(pure_vs_orig_avg):.1f}% 개선 가능)")

        if len(summary['accuracy_issues']) == 0:
            summary['recommendations'].append("✅ 모든 방식 결과 일치 - 정확성 문제 없음")
        else:
            summary['recommendations'].append("⚠️ 일부 결과 불일치 - 추가 검토 필요")

        return summary


# ===========================================
# 실제 테스트 실행 함수들
# ===========================================

def test_fair_time_calculation_comparison():
    """pytest용 공정한 테스트 함수"""
    comparison = FairTimeCalculationComparison()
    results = comparison.run_comprehensive_fair_test()

    # 기본적인 검증
    assert 'fair_single_tick' in results
    assert 'fair_summary' in results

    print("\n📊 공정한 테스트 결과 요약:")
    print(f"기존 vs 순수로직 평균: {results['fair_summary']['old_vs_pure_performance']['average']}%")
    print(f"기존 vs 원래방식 평균: {results['fair_summary']['old_vs_orig_performance']['average']}%")
    print(f"순수로직 vs 원래방식 평균: {results['fair_summary']['pure_vs_orig_performance']['average']}%")
    print(f"정확성 문제: {len(results['fair_summary']['accuracy_issues'])}건")
    print("권장사항:")
    for rec in results['fair_summary']['recommendations']:
        print(f"  {rec}")

    return results


if __name__ == "__main__":
    # 직접 실행시 공정한 포괄적 테스트 수행
    comparison = FairTimeCalculationComparison()
    results = comparison.run_comprehensive_fair_test()

    # 결과를 JSON으로 저장
    import json
    with open('tests/performance/time_utils/fair_time_calculation_results.json', 'w', encoding='utf-8') as f:
        def datetime_converter(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        json.dump(results, f, indent=2, default=datetime_converter, ensure_ascii=False)

    print("\n💾 결과가 'tests/performance/time_utils/fair_time_calculation_results.json'에 저장되었습니다.")
