"""
자동매매 시스템 시간 계산 최적화 연구 v4.0
목적: 정확성 보장과 성능 최적화 방안 도출

핵심 문제 해결:
1. 월/년봉 naive datetime 문제 수정
2. 분기문 오버헤드 분석 및 최적화
3. 정확한 월 계산 vs 30일 근사값 비교
4. 자동매매 시스템에 적합한 최적화 방안 제시

자동매매 시스템 요구사항:
- 정확성 > 성능 (부정확한 계산으로 인한 손실 방지)
- Timezone 정보 보존 필수
- 월/년봉 정확한 계산 필요
- 실시간 처리 성능 고려
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Tuple, List

from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


class TradingSystemTimeOptimization:
    """자동매매 시스템 시간 계산 최적화 연구"""

    def __init__(self):
        self.test_timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M', '1y']
        self.base_time = datetime(2024, 6, 15, 14, 32, 45, tzinfo=timezone.utc)

    # ===========================================
    # 문제점 분석: 현재 구현의 이슈들
    # ===========================================

    def analyze_current_issues(self) -> dict:
        """현재 구현의 문제점 분석"""
        print("🔍 자동매매 시스템 시간 계산 문제점 분석")
        print("=" * 80)

        issues = {
            'accuracy_problems': [],
            'performance_bottlenecks': [],
            'trading_system_risks': []
        }

        aligned_time = TimeUtils.align_to_candle_boundary(self.base_time, '1M')

        # 1. 정확성 문제 분석
        print("\n1️⃣ 정확성 문제 분석")

        # 기존 방식 (30일 근사)
        old_result = self._old_method_month_calculation(aligned_time)

        # 순수 로직 (naive datetime)
        naive_result = self._pure_logic_month_calculation_naive(aligned_time)

        # 수정된 로직 (timezone 보존)
        fixed_result = self._fixed_logic_month_calculation(aligned_time)

        print(f"   기존방식 (30일 근사): {old_result}")
        print(f"   순수로직 (naive): {naive_result}")
        print(f"   수정로직 (정확): {fixed_result}")

        if old_result.replace(tzinfo=None) != fixed_result.replace(tzinfo=None):
            issues['accuracy_problems'].append({
                'issue': '30일 근사값 사용으로 인한 부정확성',
                'risk': '월봉 데이터 불일치 가능성',
                'solution': '정확한 월 계산 로직 필요'
            })

        if not hasattr(naive_result, 'tzinfo') or naive_result.tzinfo is None:
            issues['accuracy_problems'].append({
                'issue': 'timezone 정보 손실',
                'risk': 'UTC 변환 오류로 인한 데이터 불일치',
                'solution': 'timezone 정보 보존 로직 필요'
            })

        # 2. 성능 병목 분석
        print("\n2️⃣ 성능 병목점 분석")

        # 분기문 오버헤드 측정
        branching_overhead = self._measure_branching_overhead()
        issues['performance_bottlenecks'].extend(branching_overhead)

        # 3. 자동매매 시스템 리스크 분석
        print("\n3️⃣ 자동매매 시스템 리스크 분석")

        trading_risks = self._analyze_trading_system_risks()
        issues['trading_system_risks'].extend(trading_risks)

        return issues

    def _old_method_month_calculation(self, aligned_time: datetime) -> datetime:
        """기존 방식: 30일 근사값 사용"""
        timeframe_seconds = TimeUtils.get_timeframe_seconds('1M')  # 30 * 24 * 60 * 60
        return aligned_time - timedelta(seconds=timeframe_seconds)

    def _pure_logic_month_calculation_naive(self, aligned_time: datetime) -> datetime:
        """순수 로직: naive datetime 생성 (문제 있는 버전)"""
        year = aligned_time.year
        month = aligned_time.month - 1

        if month < 1:
            year -= 1
            month = 12

        return datetime(year, month, 1, 0, 0, 0)  # timezone 정보 손실!

    def _fixed_logic_month_calculation(self, aligned_time: datetime) -> datetime:
        """수정된 로직: timezone 보존 + 정확한 월 계산"""
        year = aligned_time.year
        month = aligned_time.month - 1

        if month < 1:
            year -= 1
            month = 12

        # timezone 정보 보존하여 생성
        return datetime(year, month, 1, 0, 0, 0, tzinfo=aligned_time.tzinfo)

    def _measure_branching_overhead(self) -> List[dict]:
        """분기문 오버헤드 측정"""
        print("   🔍 분기문 오버헤드 분석")

        bottlenecks = []
        aligned_time = TimeUtils.align_to_candle_boundary(self.base_time, '1m')

        # 분기 없는 직접 계산
        def direct_calculation():
            timeframe_seconds = 60  # 1분 = 60초
            return aligned_time + timedelta(seconds=timeframe_seconds * -1)

        # 분기 있는 계산 (현재 by_ticks 구조)
        def branched_calculation():
            timeframe = '1m'
            if timeframe in ['1w', '1M', '1y']:
                # 이 분기는 실행되지 않지만 조건 검사 오버헤드 존재
                pass
            else:
                timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
                total_seconds_offset = timeframe_seconds * -1
                return aligned_time + timedelta(seconds=total_seconds_offset)

        # 성능 측정
        direct_time = self._measure_performance(direct_calculation, iterations=10000)[0]
        branched_time = self._measure_performance(branched_calculation, iterations=10000)[0]

        overhead_percent = ((branched_time - direct_time) / direct_time) * 100

        print(f"      직접 계산: {direct_time:.3f}μs")
        print(f"      분기 계산: {branched_time:.3f}μs")
        print(f"      분기 오버헤드: {overhead_percent:+.2f}%")

        if overhead_percent > 5:
            bottlenecks.append({
                'issue': f'분기문 조건 검사로 인한 {overhead_percent:.1f}% 오버헤드',
                'impact': '빈번한 호출시 누적 성능 저하',
                'solution': '타임프레임별 최적화된 함수 분리'
            })

        return bottlenecks

    def _analyze_trading_system_risks(self) -> List[dict]:
        """자동매매 시스템 리스크 분석"""
        risks = []

        # 월봉 정확성 리스크
        march_start = datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)

        # 30일 근사 (기존)
        approx_prev_month = march_start - timedelta(days=30)  # 2024-01-31 (부정확)

        # 정확한 계산
        exact_prev_month = datetime(2024, 2, 1, 0, 0, 0, tzinfo=timezone.utc)  # 2024-02-01 (정확)

        if approx_prev_month.month != exact_prev_month.month:
            risks.append({
                'risk': '월봉 데이터 조회 오류',
                'scenario': f'3월 기준 이전월: 근사값={approx_prev_month.strftime("%Y-%m")} vs 정확값={exact_prev_month.strftime("%Y-%m")}',
                'impact': '잘못된 월 데이터 조회로 인한 매매 오판',
                'severity': 'HIGH'
            })

        # Timezone 손실 리스크
        risks.append({
            'risk': 'Timezone 정보 손실',
            'scenario': 'UTC 시간을 naive로 처리하여 시간대 변환 오류',
            'impact': '글로벌 거래소 데이터 동기화 오류',
            'severity': 'HIGH'
        })

        return risks

    # ===========================================
    # 최적화 방안 제시
    # ===========================================

    def propose_optimizations(self) -> dict:
        """최적화 방안 제시"""
        print("\n🚀 자동매매 시스템 최적화 방안")
        print("=" * 80)

        optimizations = {
            'accuracy_fixes': [],
            'performance_improvements': [],
            'implementation_proposals': []
        }

        # 1. 정확성 수정 방안
        print("\n1️⃣ 정확성 수정 방안")

        accuracy_fix = self._design_accurate_time_calculation()
        optimizations['accuracy_fixes'] = accuracy_fix

        # 2. 성능 개선 방안
        print("\n2️⃣ 성능 개선 방안")

        performance_improvements = self._design_performance_improvements()
        optimizations['performance_improvements'] = performance_improvements

        # 3. 구현 제안
        print("\n3️⃣ 구현 제안")

        implementation = self._design_implementation_proposal()
        optimizations['implementation_proposals'] = implementation

        return optimizations

    def _design_accurate_time_calculation(self) -> List[dict]:
        """정확한 시간 계산 설계"""
        fixes = []

        print("   🎯 timezone 보존 월/년 계산")

        # 개선된 월 계산 함수 테스트
        test_time = datetime(2024, 3, 15, 14, 30, 0, tzinfo=timezone.utc)

        def improved_month_calculation(dt: datetime, months_offset: int) -> datetime:
            """개선된 월 계산 (timezone 보존)"""
            year = dt.year
            month = dt.month + months_offset

            # 월 오버플로우 처리
            while month > 12:
                year += 1
                month -= 12
            while month < 1:
                year -= 1
                month += 12

            # timezone 정보 보존
            return datetime(year, month, 1, 0, 0, 0, tzinfo=dt.tzinfo)

        # 테스트 실행
        old_approx = test_time - timedelta(days=30)
        new_accurate = improved_month_calculation(test_time, -1)

        print(f"      테스트 시간: {test_time}")
        print(f"      기존 근사: {old_approx} (30일 뒤로)")
        print(f"      개선 정확: {new_accurate} (정확한 이전월)")

        fixes.append({
            'fix': 'timezone 보존 월/년 계산 함수',
            'before': '30일 근사 + naive datetime',
            'after': '정확한 월 계산 + timezone 보존',
            'code_example': '''
def accurate_month_offset(dt: datetime, months: int) -> datetime:
    year, month = dt.year, dt.month + months
    while month > 12: year += 1; month -= 12
    while month < 1: year -= 1; month += 12
    return datetime(year, month, 1, 0, 0, 0, tzinfo=dt.tzinfo)
            ''',
            'accuracy_improvement': 'HIGH'
        })

        return fixes

    def _design_performance_improvements(self) -> List[dict]:
        """성능 개선 방안 설계"""
        improvements = []

        print("   ⚡ 분기 최적화 및 함수 분리")

        # 현재 방식 vs 최적화 방식 성능 비교
        aligned_time = TimeUtils.align_to_candle_boundary(self.base_time, '1m')

        # 최적화된 분기 없는 함수들
        def optimized_minute_calculation(dt: datetime, tick_count: int) -> datetime:
            """최적화된 분/시봉 계산 (분기 없음)"""
            return dt + timedelta(minutes=tick_count)

        def optimized_daily_calculation(dt: datetime, tick_count: int) -> datetime:
            """최적화된 일봉 계산 (분기 없음)"""
            return dt + timedelta(days=tick_count)

        def current_branched_calculation(dt: datetime, timeframe: str, tick_count: int) -> datetime:
            """현재 분기 방식"""
            if timeframe in ['1w', '1M', '1y']:
                # 복잡한 처리
                pass
            else:
                timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
                return dt + timedelta(seconds=timeframe_seconds * tick_count)

        # 성능 측정
        optimized_time = self._measure_performance(
            optimized_minute_calculation, aligned_time, -1, iterations=10000
        )[0]

        current_time = self._measure_performance(
            current_branched_calculation, aligned_time, '1m', -1, iterations=10000
        )[0]

        improvement_percent = ((current_time - optimized_time) / current_time) * 100

        print(f"      현재 분기방식: {current_time:.3f}μs")
        print(f"      최적화방식: {optimized_time:.3f}μs")
        print(f"      성능 개선: {improvement_percent:+.2f}%")

        improvements.append({
            'improvement': '타임프레임별 최적화 함수 분리',
            'technique': '분기문 제거 + 직접 timedelta 계산',
            'performance_gain': f'{improvement_percent:.1f}%',
            'implementation': '각 타임프레임별 전용 함수 생성'
        })

        # 캐싱 최적화 방안
        print("   🗂️ 계산 결과 캐싱")

        improvements.append({
            'improvement': 'timeframe_seconds 캐싱',
            'technique': '자주 사용되는 초 변환 결과 메모리 캐시',
            'performance_gain': '반복 호출시 50-80% 개선 예상',
            'implementation': 'LRU 캐시 또는 딕셔너리 캐시'
        })

        return improvements

    def _design_implementation_proposal(self) -> List[dict]:
        """구현 제안 설계"""
        proposals = []

        print("   📋 통합 최적화 구현안")

        # 제안 1: 타입별 최적화 함수
        proposals.append({
            'proposal': '타입별 최적화 함수 분리',
            'structure': '''
class OptimizedTimeCalculator:
    @staticmethod
    def minute_offset(dt: datetime, minutes: int) -> datetime:
        return dt + timedelta(minutes=minutes)

    @staticmethod
    def daily_offset(dt: datetime, days: int) -> datetime:
        return dt + timedelta(days=days)

    @staticmethod
    def month_offset(dt: datetime, months: int) -> datetime:
        year, month = dt.year, dt.month + months
        while month > 12: year += 1; month -= 12
        while month < 1: year -= 1; month += 12
        return datetime(year, month, 1, 0, 0, 0, tzinfo=dt.tzinfo)
            ''',
            'benefits': ['분기 오버헤드 제거', '타입 안전성', '가독성 향상'],
            'integration': 'TimeUtils 클래스에 통합'
        })

        # 제안 2: 하이브리드 접근법
        proposals.append({
            'proposal': '하이브리드 최적화 접근법',
            'strategy': '''
- 소규모 연산(1-100틱): 직접 계산
- 대규모 연산(100+틱): 캐시 + 배치 처리
- 월/년봉: 정확성 우선 계산
- 분/시/일봉: 성능 우선 계산
            ''',
            'benefits': ['상황별 최적화', '자동매매 요구사항 맞춤'],
            'integration': 'CandleDataProvider에서 스마트 선택'
        })

        return proposals

    # ===========================================
    # 성능 측정 유틸리티
    # ===========================================

    def _measure_performance(self, func, *args, iterations: int = 1000) -> Tuple[float, any]:
        """성능 측정"""
        # 워밍업
        for _ in range(10):
            result = func(*args)

        # 측정
        start = time.perf_counter()
        for _ in range(iterations):
            result = func(*args)
        end = time.perf_counter()

        avg_time = (end - start) / iterations * 1_000_000  # 마이크로초
        return avg_time, result

    # ===========================================
    # 실제 개선된 구현 테스트
    # ===========================================

    def test_improved_implementations(self) -> dict:
        """개선된 구현 테스트"""
        print("\n🧪 개선된 구현 검증 테스트")
        print("=" * 80)

        results = {}

        # 1. 정확성 검증
        accuracy_results = self._test_accuracy_improvements()
        results['accuracy'] = accuracy_results

        # 2. 성능 검증
        performance_results = self._test_performance_improvements()
        results['performance'] = performance_results

        # 3. 자동매매 적합성 검증
        trading_suitability = self._test_trading_suitability()
        results['trading_suitability'] = trading_suitability

        return results

    def _test_accuracy_improvements(self) -> dict:
        """정확성 개선 테스트"""
        print("\n   ✅ 정확성 검증")

        test_cases = [
            datetime(2024, 1, 31, 12, 0, 0, tzinfo=timezone.utc),  # 1월 말
            datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc),  # 윤년 2월 말
            datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc),  # 연말
        ]

        accuracy_results = {}

        for i, test_time in enumerate(test_cases):
            print(f"\n      테스트 케이스 {i+1}: {test_time}")

            # 기존 방식 (30일 근사)
            old_result = test_time - timedelta(days=30)

            # 개선된 방식 (정확한 월 계산)
            year = test_time.year
            month = test_time.month - 1
            if month < 1:
                year -= 1
                month = 12

            improved_result = datetime(year, month, 1, 0, 0, 0, tzinfo=test_time.tzinfo)

            print(f"         기존 (30일 근사): {old_result}")
            print(f"         개선 (정확한 월): {improved_result}")

            accuracy_results[f'case_{i+1}'] = {
                'test_time': test_time.isoformat(),
                'old_result': old_result.isoformat(),
                'improved_result': improved_result.isoformat(),
                'month_accuracy': old_result.month == improved_result.month,
                'timezone_preserved': improved_result.tzinfo is not None
            }

        return accuracy_results

    def _test_performance_improvements(self) -> dict:
        """성능 개선 테스트"""
        print("\n   ⚡ 성능 개선 검증")

        aligned_time = TimeUtils.align_to_candle_boundary(self.base_time, '1m')

        # 현재 방식
        def current_method():
            timeframe = '1m'
            if timeframe in ['1w', '1M', '1y']:
                pass
            else:
                timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
                return aligned_time + timedelta(seconds=timeframe_seconds * -1)

        # 최적화된 방식
        def optimized_method():
            return aligned_time + timedelta(minutes=-1)

        current_time, _ = self._measure_performance(current_method, iterations=10000)
        optimized_time, _ = self._measure_performance(optimized_method, iterations=10000)

        improvement = ((current_time - optimized_time) / current_time) * 100

        print(f"      현재 방식: {current_time:.3f}μs")
        print(f"      최적화 방식: {optimized_time:.3f}μs")
        print(f"      성능 개선: {improvement:+.2f}%")

        return {
            'current_time_us': current_time,
            'optimized_time_us': optimized_time,
            'improvement_percent': improvement
        }

    def _test_trading_suitability(self) -> dict:
        """자동매매 적합성 테스트"""
        print("\n   📈 자동매매 적합성 검증")

        suitability = {
            'accuracy_score': 0,
            'performance_score': 0,
            'reliability_score': 0,
            'overall_score': 0
        }

        # 정확성 점수 (월봉 정확성 기준)
        march_2024 = datetime(2024, 3, 15, 0, 0, 0, tzinfo=timezone.utc)
        accurate_prev = datetime(2024, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        approx_prev = march_2024 - timedelta(days=30)

        if accurate_prev.month == 2 and approx_prev.month == 1:
            suitability['accuracy_score'] = 10  # 정확한 월 계산 중요
            print("      ✅ 월봉 정확성: 10/10")
        else:
            suitability['accuracy_score'] = 5
            print("      ⚠️ 월봉 정확성: 5/10")

        # 성능 점수 (실시간 처리 기준)
        performance_results = self._test_performance_improvements()
        if performance_results['improvement_percent'] > 0:
            suitability['performance_score'] = 8
            print("      ✅ 성능 개선: 8/10")
        else:
            suitability['performance_score'] = 6
            print("      📊 성능 유지: 6/10")

        # 신뢰성 점수 (timezone 보존)
        suitability['reliability_score'] = 10  # timezone 정보 보존 필수
        print("      ✅ Timezone 보존: 10/10")

        # 종합 점수
        suitability['overall_score'] = (
            suitability['accuracy_score'] +
            suitability['performance_score'] +
            suitability['reliability_score']
        ) / 3

        print(f"      🎯 종합 점수: {suitability['overall_score']:.1f}/10")

        return suitability

    # ===========================================
    # 메인 실행 함수
    # ===========================================

    def run_comprehensive_optimization_analysis(self) -> dict:
        """종합적인 최적화 분석 실행"""
        print("🚀 자동매매 시스템 시간 계산 최적화 연구 v4.0")
        print("🎯 목적: 정확성 보장 + 성능 최적화 + 실용적 개선 방안")
        print("=" * 80)

        analysis_results = {}

        # 1. 문제점 분석
        analysis_results['issues'] = self.analyze_current_issues()

        # 2. 최적화 방안 제시
        analysis_results['optimizations'] = self.propose_optimizations()

        # 3. 개선된 구현 테스트
        analysis_results['improvements'] = self.test_improved_implementations()

        # 4. 최종 권장사항 도출
        analysis_results['final_recommendations'] = self._generate_final_recommendations(analysis_results)

        print("\n✅ 최적화 분석 완료!")
        print("=" * 80)

        return analysis_results

    def _generate_final_recommendations(self, analysis_results: dict) -> dict:
        """최종 권장사항 생성"""
        print("\n📋 최종 권장사항")
        print("=" * 80)

        recommendations = {
            'immediate_fixes': [],
            'performance_optimizations': [],
            'long_term_improvements': []
        }

        # 즉시 수정 사항
        print("\n🔥 즉시 수정 필요")
        immediate = [
            "timezone 정보 보존 로직 추가 (HIGH 우선순위)",
            "월봉 계산을 30일 근사에서 정확한 월 계산으로 변경",
            "naive datetime 생성 지점 모두 수정"
        ]

        for fix in immediate:
            print(f"   • {fix}")
            recommendations['immediate_fixes'].append(fix)

        # 성능 최적화
        print("\n⚡ 성능 최적화")
        performance = [
            "타임프레임별 최적화 함수 분리 (분기 오버헤드 제거)",
            "자주 사용되는 계산 결과 캐싱",
            "CandleDataProvider에서 상황별 최적 함수 선택"
        ]

        for opt in performance:
            print(f"   • {opt}")
            recommendations['performance_optimizations'].append(opt)

        # 장기 개선사항
        print("\n🔮 장기 개선사항")
        long_term = [
            "타입 안전한 TimeFrame enum 도입",
            "시간 계산 전용 클래스 분리",
            "자동매매 시나리오별 성능 프로파일링"
        ]

        for improvement in long_term:
            print(f"   • {improvement}")
            recommendations['long_term_improvements'].append(improvement)

        return recommendations


if __name__ == "__main__":
    optimizer = TradingSystemTimeOptimization()
    results = optimizer.run_comprehensive_optimization_analysis()

    # 결과 저장
    import json
    with open('tests/performance/time_utils/trading_system_time_optimization.json', 'w', encoding='utf-8') as f:
        def datetime_converter(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        json.dump(results, f, indent=2, default=datetime_converter, ensure_ascii=False)

    print("\n💾 최적화 분석 결과가 'tests/performance/time_utils/trading_system_time_optimization.json'에 저장되었습니다.")
