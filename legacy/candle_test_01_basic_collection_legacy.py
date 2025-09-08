"""
테스트 01: 베이직 수집 테스트
BASIC_COLLECTION_TEST_SCENARIOS.md의 시나리오에 따른 실제 CandleDataProvider 테스트
CandleCollectionTester 래퍼 활용으로 통계 추적 자동화
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.candle_data_logic.candle_db_cleaner import CandleDBCleaner
from tests.candle_data_logic.candle_db_analyzer import CandleDBAnalyzer
from tests.candle_data_logic.candle_time_utils import CandleTimeUtils
from tests.candle_data_logic.candle_collection_tester import CandleCollectionTester


class BasicCollectionTester:
    """베이직 수집 테스트 실행기"""

    def __init__(self):
        self.cleaner = CandleDBCleaner()
        self.analyzer = CandleDBAnalyzer()
        self.time_utils = CandleTimeUtils()
        self.provider = CandleDataProvider()

        # 공통 설정 (시나리오 문서 기준)
        self.symbol = "KRW-BTC"
        self.timeframe = "1m"
        self.end_time = datetime(2025, 9, 8, 0, 0, 0, tzinfo=timezone.utc)

    async def test_scenario_1_collect_100(self) -> dict:
        """시나리오 1: 겹침없이 그냥 수집 100개"""

        print("🧪 === 테스트 시나리오 1: 100개 수집 ===")

        # 1단계: 예상 결과 계산
        print("\n1️⃣ 예상 결과 계산:")
        expected = self.time_utils.get_time_info("2025-09-08T00:00:00", 100)
        print(f"  예상 시간 범위: {expected['start_utc']} → {expected['end_utc']}")
        print(f"  예상 기간: {expected['duration_minutes']}분")

        # 2단계: DB 초기화
        print("\n2️⃣ DB 초기화:")
        table_name = f"candles_{self.symbol.replace('-', '_')}_{self.timeframe}"
        clear_result = self.cleaner.clear_candle_table(table_name)

        if clear_result.get('success', False):
            print(f"  ✅ DB 초기화 완료 (삭제: {clear_result.get('records_before', 0)}개)")
        else:
            print(f"  ❌ DB 초기화 실패: {clear_result.get('error')}")
            return {'success': False, 'error': 'DB 초기화 실패'}

        # 3단계: 초기 DB 상태 확인
        print("\n3️⃣ 초기 DB 상태:")
        initial_analysis = self.analyzer.analyze()
        if initial_analysis.get('success'):
            initial_count = initial_analysis['basic_stats']['total_count']
            print(f"  초기 레코드 수: {initial_count}개")

        # 4단계: CandleDataProvider 테스트 실행
        print("\n4️⃣ CandleDataProvider 수집 실행:")
        print(f"  심볼: {self.symbol}")
        print(f"  타임프레임: {self.timeframe}")
        print(f"  개수: 100개")
        print(f"  종료시간: {self.end_time}")

        try:
            # 실제 CandleDataProvider 호출
            response = await self.provider.get_candles(
                symbol=self.symbol,
                timeframe=self.timeframe,
                count=100,
                end_time=self.end_time
            )

            print(f"  응답 성공: {response.success}")
            print(f"  데이터 개수: {len(response.candles) if response.candles else 0}개")
            print(f"  총 개수: {response.total_count}개")
            print(f"  데이터 소스: {response.data_source}")
            print(f"  응답 시간: {response.response_time_ms:.1f}ms")

            if not response.success and response.error_message:
                print(f"  오류 메시지: {response.error_message}")

        except Exception as e:
            print(f"  ❌ 실행 오류: {str(e)}")
            return {'success': False, 'error': f'실행 오류: {str(e)}'}

        # 5단계: 결과 DB 상태 분석
        print("\n5️⃣ 결과 DB 상태 분석:")
        final_analysis = self.analyzer.analyze()

        if final_analysis.get('success'):
            stats = final_analysis['basic_stats']
            fragments = final_analysis['fragments']

            print(f"  최종 레코드 수: {stats['total_count']}개")
            print(f"  파편 개수: {len(fragments)}개")

            if stats['total_count'] > 0:
                print(f"  시간 범위: {stats['start_utc']} → {stats['end_utc']}")
                print(f"  실제 기간: {stats['duration_minutes']}분")        # 6단계: 검증 기준 확인
        print("\n6️⃣ 검증 기준 확인:")
        result = {
            'success': True,
            'scenario': 'basic_100',
            'expected': expected,
            'response': response,
            'db_analysis': final_analysis
        }

        # 검증 1: DB 레코드 수 ≥ 100개
        final_count = stats.get('total_count', 0) if final_analysis.get('success') else 0
        if final_count >= 100:
            print(f"  ✅ DB 레코드 수: {final_count}개 ≥ 100개")
            result['check_record_count'] = True
        else:
            print(f"  ❌ DB 레코드 수: {final_count}개 < 100개")
            result['check_record_count'] = False

        # 검증 2: 시간 범위 포함
        if stats.get('total_count', 0) > 0:
            db_start = stats['start_utc']
            db_end = stats['end_utc']
            expected_start = expected['start_utc']
            expected_end = expected['end_utc']

            # 시간 포함 여부 확인 (DB 범위가 예상 범위를 포함하는지)
            time_range_ok = (db_start >= expected_start and db_end <= expected_end) or \
                           (db_start <= expected_start and db_end >= expected_end)

            if time_range_ok:
                print(f"  ✅ 시간 범위 포함: {db_start} → {db_end}")
                result['check_time_range'] = True
            else:
                print(f"  ❌ 시간 범위 불일치:")
                print(f"     예상: {expected_start} → {expected_end}")
                print(f"     실제: {db_start} → {db_end}")
                result['check_time_range'] = False
        else:
            print(f"  ❌ 시간 범위 확인 불가 (레코드 없음)")
            result['check_time_range'] = False

        # 검증 3: 응답 성공
        if response.success:
            print(f"  ✅ 응답 성공: {response.success}")
            result['check_response_success'] = True
        else:
            print(f"  ❌ 응답 실패: {response.message}")
            result['check_response_success'] = False

        # 7단계: 전체 결과 판정
        all_checks = [
            result.get('check_record_count', False),
            result.get('check_time_range', False),
            result.get('check_response_success', False)
        ]

        overall_success = all(all_checks)
        result['overall_success'] = overall_success

        print(f"\n🎯 전체 테스트 결과: {'✅ 성공' if overall_success else '❌ 실패'}")

        return result

    async def run_all_scenarios(self):
        """모든 시나리오 실행"""

        print("🚀 === 베이직 수집 테스트 시작 ===")
        print("문서 기준: BASIC_COLLECTION_TEST_SCENARIOS.md")

        results = {}

        # 시나리오 1: 100개 수집
        try:
            results['scenario_1'] = await self.test_scenario_1_collect_100()
        except Exception as e:
            print(f"❌ 시나리오 1 실행 중 오류: {str(e)}")
            results['scenario_1'] = {'success': False, 'error': str(e)}

        # 결과 요약
        print(f"\n📊 === 테스트 결과 요약 ===")

        for scenario_name, result in results.items():
            success = result.get('overall_success', False)
            status = "✅ 성공" if success else "❌ 실패"
            print(f"  {scenario_name}: {status}")

            if not success and 'error' in result:
                print(f"    오류: {result['error']}")

        return results


async def main():
    """메인 실행 함수"""
    tester = BasicCollectionTester()
    results = await tester.run_all_scenarios()

    # 상세 결과 출력
    print(f"\n🔍 === 상세 디버깅 정보 ===")
    for scenario_name, result in results.items():
        if result.get('overall_success') is False:
            print(f"\n❌ {scenario_name} 실패 분석:")

            # 각 검증 항목별 상세 정보
            checks = ['check_record_count', 'check_time_range', 'check_response_success']
            for check in checks:
                if check in result:
                    status = "✅" if result[check] else "❌"
                    print(f"  {check}: {status}")

    return results


if __name__ == "__main__":
    asyncio.run(main())
