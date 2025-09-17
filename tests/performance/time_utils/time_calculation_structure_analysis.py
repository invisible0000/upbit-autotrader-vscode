"""
시간 계산 메서드 구조 분석 및 개선 연구 테스트 v3.0
TimeUtils.get_aligned_time_by_ticks vs 기존 timedelta 방식

목적: 경쟁이 아닌 이해와 개선을 위한 구조 분석
1. 순수 로직 구조 파악 (align_to_candle_boundary 오버헤드 제외)
2. 메서드 개선 방향 도출
3. 로직 복잡도 및 성능 특성 이해
4. 코드 가독성과 유지보수성 평가

개선 사항:
1. 모든 테스트에 동일하게 정렬된 시간 제공 (공정한 재료)
2. 순수 로직에서 align_to_candle_boundary 완전 제거
3. 경쟁 구도 제거, 이해 중심의 분석
4. 명확한 네이밍과 목적 지향적 구조
"""

import time
import tracemalloc
from datetime import datetime, timezone, timedelta
from typing import Tuple

from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


class TimeCalculationStructureAnalysis:
    """시간 계산 방식 구조 분석 클래스 - 이해와 개선을 위한 연구"""

    def __init__(self):
        self.test_timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M', '1y']
        self.base_time = datetime(2024, 6, 15, 14, 32, 45, tzinfo=timezone.utc)

    # ===========================================
    # 준비 단계: 모든 테스트에 동일한 정렬된 시간 제공
    # ===========================================

    def prepare_aligned_time(self, base_time: datetime, timeframe: str) -> datetime:
        """모든 테스트에 제공할 정렬된 시간 준비"""
        return TimeUtils.align_to_candle_boundary(base_time, timeframe)

    # ===========================================
    # 기존 방식 (timedelta 기반)
    # ===========================================

    def old_method_single_tick_backward(self, aligned_time: datetime, timeframe: str) -> datetime:
        """기존 방식: 1틱 뒤로 이동 (정렬된 시간 기준)"""
        dt = TimeUtils.get_timeframe_delta(timeframe)
        return aligned_time - dt

    def old_method_multiple_ticks_backward(self, aligned_time: datetime, timeframe: str, tick_count: int) -> datetime:
        """기존 방식: 여러 틱 뒤로 이동 (정렬된 시간 기준)"""
        timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
        total_seconds = timeframe_seconds * tick_count
        return aligned_time - timedelta(seconds=total_seconds)

    def old_method_calculate_end_time(self, aligned_start: datetime, timeframe: str, count: int) -> datetime:
        """기존 방식: count 기반 종료 시간 계산 (정렬된 시간 기준)"""
        timeframe_seconds = TimeUtils.get_timeframe_delta(timeframe).total_seconds()
        return aligned_start - timedelta(seconds=(count - 1) * timeframe_seconds)

    # ===========================================
    # 순수 로직 방식 (get_aligned_time_by_ticks 내부 로직만, align 제외)
    # ===========================================

    def pure_logic_by_ticks_single_backward(self, aligned_base: datetime, timeframe: str) -> datetime:
        """순수 틱 로직: 1틱 뒤로 이동 (정렬 오버헤드 완전 제거)"""
        # tick_count = -1 로직 직접 구현 (align_to_candle_boundary 제거)
        tick_count = -1

        # timeframe에 따른 틱 간격 계산 (get_aligned_time_by_ticks 핵심 로직만)
        if timeframe in ['1w', '1M', '1y']:
            # 주/월/년봉은 특별 처리 (정확한 날짜 산술)
            if timeframe == '1w':
                # 주봉: 7일 단위
                tick_delta = timedelta(weeks=abs(tick_count))
                return aligned_base - tick_delta
                # 주의: 원본에서는 여기서도 align_to_candle_boundary를 호출하지만 제거

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

                # 월 첫날로 설정 (timezone 정보 제거됨 - 이것이 차이점!)
                return datetime(year, month, 1, 0, 0, 0)

            elif timeframe == '1y':
                # 년봉: 정확한 년 단위 계산
                year = aligned_base.year + tick_count
                return datetime(year, 1, 1, 0, 0, 0)  # timezone 정보 제거됨
        else:
            # 초/분/시간/일봉: 고정 길이, 빠른 계산
            timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
            total_seconds_offset = timeframe_seconds * tick_count
            return aligned_base + timedelta(seconds=total_seconds_offset)

    def pure_logic_by_ticks_multiple_backward(self, aligned_base: datetime, timeframe: str, tick_count: int) -> datetime:
        """순수 틱 로직: 여러 틱 뒤로 이동 (정렬 오버헤드 완전 제거)"""
        # 음수 tick_count 적용
        negative_tick_count = -tick_count

        # timeframe에 따른 틱 간격 계산
        if timeframe in ['1w', '1M', '1y']:
            # 주/월/년봉은 특별 처리
            if timeframe == '1w':
                # 주봉: 7일 단위
                tick_delta = timedelta(weeks=abs(negative_tick_count))
                if negative_tick_count > 0:
                    return aligned_base + tick_delta
                else:
                    return aligned_base - tick_delta
                # align_to_candle_boundary 호출 제거

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

    def pure_logic_by_ticks_calculate_end_time(self, aligned_base: datetime, timeframe: str, count: int) -> datetime:
        """순수 틱 로직: count 기반 종료 시간 계산 (정렬 오버헤드 완전 제거)"""
        # tick_count = -(count - 1) 로직 적용
        tick_count = -(count - 1)

        # timeframe에 따른 틱 간격 계산
        if timeframe in ['1w', '1M', '1y']:
            # 주/월/년봉은 특별 처리
            if timeframe == '1w':
                # 주봉: 7일 단위
                tick_delta = timedelta(weeks=abs(tick_count))
                if tick_count > 0:
                    return aligned_base + tick_delta
                else:
                    return aligned_base - tick_delta

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
    # 구조 분석 테스트 (이해 중심)
    # ===========================================

    def analyze_single_tick_structure(self) -> dict:
        """1틱 이동 구조 분석 - 로직 복잡도와 성능 특성 이해"""
        results = {}

        print("🔍 1틱 이동 구조 분석 - 로직 이해와 개선점 도출")
        print("=" * 80)

        for timeframe in self.test_timeframes:
            print(f"\n📊 {timeframe} - 1틱 뒤로 이동 분석")

            # 동일한 정렬된 시간 준비
            aligned_time = self.prepare_aligned_time(self.base_time, timeframe)

            # 1. 기존 방식 분석
            old_time, old_result = self.measure_execution_time(
                self.old_method_single_tick_backward, aligned_time, timeframe
            )
            old_memory, _ = self.measure_memory_usage(
                self.old_method_single_tick_backward, aligned_time, timeframe
            )

            # 2. 순수 틱 로직 분석
            pure_time, pure_result = self.measure_execution_time(
                self.pure_logic_by_ticks_single_backward, aligned_time, timeframe
            )
            pure_memory, _ = self.measure_memory_usage(
                self.pure_logic_by_ticks_single_backward, aligned_time, timeframe
            )

            # 성능 차이 계산 (개선 여부가 아닌 특성 이해)
            time_difference_percent = ((old_time - pure_time) / old_time) * 100
            memory_difference_percent = ((old_memory - pure_memory) / old_memory) * 100 if old_memory > 0 else 0

            # 로직 복잡도 분석
            complexity_analysis = self._analyze_logic_complexity(timeframe)

            results[timeframe] = {
                'old_time_us': round(old_time, 3),
                'pure_time_us': round(pure_time, 3),
                'time_difference_percent': round(time_difference_percent, 2),
                'old_memory_bytes': old_memory,
                'pure_memory_bytes': pure_memory,
                'memory_difference_percent': round(memory_difference_percent, 2),
                'results_match': old_result == pure_result,
                'old_result': old_result,
                'pure_result': pure_result,
                'complexity_analysis': complexity_analysis,
                'aligned_input_time': aligned_time
            }

            print(f"  기존 방식: {old_time:.3f}μs, {old_memory}bytes")
            print(f"  순수 로직: {pure_time:.3f}μs, {pure_memory}bytes")
            print(f"  시간 차이: {time_difference_percent:+.2f}%, 메모리 차이: {memory_difference_percent:+.2f}%")
            print(f"  결과 일치: {'✅' if old_result == pure_result else '❌'}")
            print(f"  복잡도: {complexity_analysis['level']} ({complexity_analysis['reason']})")

            if old_result != pure_result:
                print(f"  🔍 결과 차이 분석:")
                print(f"     기존방식: {old_result}")
                print(f"     순수로직: {pure_result}")
                print(f"     차이원인: {self._analyze_result_difference(timeframe, old_result, pure_result)}")

        return results

    def analyze_multiple_ticks_structure(self) -> dict:
        """다중 틱 이동 구조 분석 - 스케일링 특성 이해"""
        tick_counts = [10, 100, 1000, 10000]
        results = {}

        print("\n🔍 다중 틱 이동 구조 분석 - 스케일링 특성 이해")
        print("=" * 80)

        for timeframe in ['1m', '5m', '1h', '1d']:  # 대표적인 타임프레임으로 제한
            results[timeframe] = {}

            aligned_time = self.prepare_aligned_time(self.base_time, timeframe)

            for tick_count in tick_counts:
                print(f"\n📊 {timeframe} - {tick_count}틱 분석")

                # 1. 기존 방식
                old_time, old_result = self.measure_execution_time(
                    self.old_method_multiple_ticks_backward, aligned_time, timeframe, tick_count
                )

                # 2. 순수 틱 로직
                pure_time, pure_result = self.measure_execution_time(
                    self.pure_logic_by_ticks_multiple_backward, aligned_time, timeframe, tick_count
                )

                time_difference_percent = ((old_time - pure_time) / old_time) * 100

                results[timeframe][tick_count] = {
                    'old_time_us': round(old_time, 3),
                    'pure_time_us': round(pure_time, 3),
                    'time_difference_percent': round(time_difference_percent, 2),
                    'results_match': old_result == pure_result,
                    'old_result': old_result,
                    'pure_result': pure_result,
                    'scaling_efficiency': self._calculate_scaling_efficiency(old_time, pure_time, tick_count)
                }

                print(f"  기존: {old_time:.3f}μs | 순수로직: {pure_time:.3f}μs | 차이: {time_difference_percent:+.2f}%")
                print(f"  결과 일치: {'✅' if old_result == pure_result else '❌'}")
                print(f"  스케일링 효율: {results[timeframe][tick_count]['scaling_efficiency']}")

        return results

    def analyze_end_time_calculation_structure(self) -> dict:
        """종료 시간 계산 구조 분석 - 실용성 평가"""
        counts = [200, 1000, 5000, 10000]
        results = {}

        print("\n🔍 종료 시간 계산 구조 분석 - 실용성 평가")
        print("=" * 80)

        for timeframe in ['1m', '5m', '1h', '1d']:
            results[timeframe] = {}

            aligned_time = self.prepare_aligned_time(self.base_time, timeframe)

            for count in counts:
                print(f"\n📊 {timeframe} - {count}개 캔들 종료시간 분석")

                # 1. 기존 방식
                old_time, old_result = self.measure_execution_time(
                    self.old_method_calculate_end_time, aligned_time, timeframe, count
                )

                # 2. 순수 틱 로직
                pure_time, pure_result = self.measure_execution_time(
                    self.pure_logic_by_ticks_calculate_end_time, aligned_time, timeframe, count
                )

                time_difference_percent = ((old_time - pure_time) / old_time) * 100

                # 실용성 평가
                practicality = self._evaluate_practicality(timeframe, count, old_time, pure_time)

                results[timeframe][count] = {
                    'old_time_us': round(old_time, 3),
                    'pure_time_us': round(pure_time, 3),
                    'time_difference_percent': round(time_difference_percent, 2),
                    'results_match': old_result == pure_result,
                    'old_result': old_result,
                    'pure_result': pure_result,
                    'practicality': practicality
                }

                print(f"  기존: {old_time:.3f}μs | 순수로직: {pure_time:.3f}μs | 차이: {time_difference_percent:+.2f}%")
                print(f"  결과 일치: {'✅' if old_result == pure_result else '❌'}")
                print(f"  실용성: {practicality['score']}/10 ({practicality['reason']})")

        return results

    # ===========================================
    # 분석 헬퍼 메서드들
    # ===========================================

    def _analyze_logic_complexity(self, timeframe: str) -> dict:
        """로직 복잡도 분석"""
        if timeframe in ['1w', '1M', '1y']:
            if timeframe == '1w':
                return {'level': '중간', 'reason': 'timedelta + 재정렬'}
            elif timeframe == '1M':
                return {'level': '높음', 'reason': '월 오버플로우 처리 + datetime 생성'}
            elif timeframe == '1y':
                return {'level': '낮음', 'reason': '단순 년 계산'}
        else:
            return {'level': '매우 낮음', 'reason': '단순 초 계산 + timedelta'}

    def _analyze_result_difference(self, timeframe: str, old_result: datetime, pure_result: datetime) -> str:
        """결과 차이 원인 분석"""
        if timeframe in ['1M', '1y']:
            if hasattr(old_result, 'tzinfo') and old_result.tzinfo:
                if not hasattr(pure_result, 'tzinfo') or not pure_result.tzinfo:
                    return "timezone 정보 차이 (기존: UTC, 순수로직: naive)"

        if old_result != pure_result:
            time_diff = abs((old_result - pure_result).total_seconds())
            return f"시간 차이 {time_diff}초 - 로직 구현 차이"

        return "알 수 없는 차이"

    def _calculate_scaling_efficiency(self, old_time: float, pure_time: float, tick_count: int) -> str:
        """스케일링 효율성 계산"""
        if tick_count <= 10:
            return "소규모 - 차이 미미"
        elif tick_count <= 1000:
            diff_percent = abs(((old_time - pure_time) / old_time) * 100)
            if diff_percent < 5:
                return "중규모 - 효율성 유사"
            else:
                return f"중규모 - {'순수로직' if pure_time < old_time else '기존방식'} 우세 ({diff_percent:.1f}%)"
        else:
            diff_percent = abs(((old_time - pure_time) / old_time) * 100)
            if diff_percent > 15:
                return f"대규모 - {'순수로직' if pure_time < old_time else '기존방식'} 명확 우세"
            else:
                return "대규모 - 효율성 유사"

    def _evaluate_practicality(self, timeframe: str, count: int, old_time: float, pure_time: float) -> dict:
        """실용성 평가"""
        # 실제 사용 시나리오 고려
        if count <= 200:  # 작은 청크
            if abs(old_time - pure_time) < 0.5:  # 0.5μs 미만 차이
                return {'score': 9, 'reason': '소규모에서 성능 차이 무의미'}
            else:
                return {'score': 7, 'reason': '소규모지만 성능 차이 존재'}

        elif count <= 1000:  # 중간 청크
            time_diff_percent = abs(((old_time - pure_time) / old_time) * 100)
            if time_diff_percent < 10:
                return {'score': 8, 'reason': '중규모에서 적절한 성능'}
            else:
                return {'score': 6, 'reason': '중규모에서 성능 차이 주목할 만함'}

        else:  # 대규모
            time_diff_percent = abs(((old_time - pure_time) / old_time) * 100)
            if time_diff_percent > 20:
                return {'score': 5, 'reason': '대규모에서 성능 차이 중요함'}
            else:
                return {'score': 7, 'reason': '대규모에서도 합리적 성능'}

    # ===========================================
    # 종합 분석 및 개선점 도출
    # ===========================================

    def run_comprehensive_structure_analysis(self) -> dict:
        """종합적인 구조 분석 실행 - 이해와 개선점 도출"""
        print("🚀 시간 계산 메서드 구조 분석 및 개선 연구 v3.0")
        print("🎯 목적: 경쟁이 아닌 이해와 개선을 위한 연구")
        print("=" * 80)

        all_results = {}

        # 1. 단일 틱 구조 분석
        all_results['single_tick_analysis'] = self.analyze_single_tick_structure()

        # 2. 다중 틱 스케일링 분석
        all_results['multiple_ticks_analysis'] = self.analyze_multiple_ticks_structure()

        # 3. 종료 시간 계산 실용성 분석
        all_results['end_time_analysis'] = self.analyze_end_time_calculation_structure()

        # 4. 종합 인사이트 도출
        print("\n📋 종합 인사이트 도출")
        all_results['comprehensive_insights'] = self.generate_comprehensive_insights(all_results)

        print("\n✅ 구조 분석 완료 - 개선 방향 도출됨")
        print("=" * 80)

        return all_results

    def generate_comprehensive_insights(self, all_results: dict) -> dict:
        """종합적인 인사이트 도출"""
        insights = {
            'performance_characteristics': {},
            'complexity_analysis': {},
            'accuracy_concerns': [],
            'improvement_recommendations': [],
            'usage_guidelines': []
        }

        # 성능 특성 분석
        single_tick_results = all_results['single_tick_analysis']

        time_differences = [result['time_difference_percent'] for result in single_tick_results.values()]
        avg_time_difference = sum(time_differences) / len(time_differences)

        insights['performance_characteristics'] = {
            'average_time_difference_percent': round(avg_time_difference, 2),
            'best_case_timeframe': min(single_tick_results.items(), key=lambda x: abs(x[1]['time_difference_percent']))[0],
            'worst_case_timeframe': max(single_tick_results.items(), key=lambda x: abs(x[1]['time_difference_percent']))[0],
            'memory_impact': (
                'minimal' if all(r['memory_difference_percent'] < 10 for r in single_tick_results.values())
                else 'notable'
            )
        }

        # 복잡도 분석
        complexity_levels = {}
        for timeframe, result in single_tick_results.items():
            level = result['complexity_analysis']['level']
            complexity_levels[level] = complexity_levels.get(level, []) + [timeframe]

        insights['complexity_analysis'] = complexity_levels

        # 정확성 문제 수집
        for timeframe, result in single_tick_results.items():
            if not result['results_match']:
                insights['accuracy_concerns'].append({
                    'timeframe': timeframe,
                    'issue': (
                        f"결과 불일치 - "
                        f"{self._analyze_result_difference(timeframe, result['old_result'], result['pure_result'])}"
                    )
                })

        # 개선 권장사항 도출
        insights['improvement_recommendations'] = [
            "🔍 구조적 개선점:",
        ]

        if avg_time_difference > 10:
            insights['improvement_recommendations'].append(
                f"⚡ 순수 로직이 평균 {avg_time_difference:.1f}% 효율적 - 단순화 가능성 검토"
            )
        elif avg_time_difference < -10:
            insights['improvement_recommendations'].append(
                f"🔧 기존 방식이 평균 {abs(avg_time_difference):.1f}% 효율적 - 순수 로직 최적화 필요"
            )
        else:
            insights['improvement_recommendations'].append(
                "⚖️ 성능 차이 미미 - 가독성과 유지보수성 중심으로 선택"
            )

        if len(insights['accuracy_concerns']) > 0:
            insights['improvement_recommendations'].append(
                f"🎯 정확성 개선 필요: {len(insights['accuracy_concerns'])}개 타임프레임에서 결과 차이"
            )

        if 'high' in [result['complexity_analysis']['level'] for result in single_tick_results.values()]:
            insights['improvement_recommendations'].append(
                "🧩 복잡도 높은 타임프레임(월/년봉) 리팩터링 고려"
            )

        # 사용 가이드라인 도출
        insights['usage_guidelines'] = [
            "📋 사용 권장사항:",
            "• 소규모 연산(~200회): 성능보다 가독성 우선",
            "• 중규모 연산(200~1000회): 벤치마크 후 결정",
            "• 대규모 연산(1000회+): 성능 테스트 필수",
            "• 월/년봉 계산: 정확성 검증 강화 필요",
            "• 개발 초기: 기존 방식으로 프로토타입, 최적화는 나중에"
        ]

        return insights


# ===========================================
# 실행 함수들
# ===========================================

def run_structure_analysis():
    """구조 분석 실행 함수"""
    analysis = TimeCalculationStructureAnalysis()
    results = analysis.run_comprehensive_structure_analysis()

    print("\n📊 구조 분석 결과 요약:")
    insights = results['comprehensive_insights']

    print(f"평균 성능 차이: {insights['performance_characteristics']['average_time_difference_percent']}%")
    print(f"최적 타임프레임: {insights['performance_characteristics']['best_case_timeframe']}")
    print(f"정확성 이슈: {len(insights['accuracy_concerns'])}건")

    print("\n개선 권장사항:")
    for rec in insights['improvement_recommendations']:
        print(f"  {rec}")

    print("\n사용 가이드라인:")
    for guideline in insights['usage_guidelines']:
        print(f"  {guideline}")

    return results


if __name__ == "__main__":
    # 구조 분석 실행
    analysis = TimeCalculationStructureAnalysis()
    results = analysis.run_comprehensive_structure_analysis()

    # 결과를 JSON으로 저장
    import json
    with open('tests/performance/time_utils/time_calculation_structure_analysis.json', 'w', encoding='utf-8') as f:
        def datetime_converter(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        json.dump(results, f, indent=2, default=datetime_converter, ensure_ascii=False)

    print("\n💾 구조 분석 결과가 'tests/performance/time_utils/time_calculation_structure_analysis.json'에 저장되었습니다.")
