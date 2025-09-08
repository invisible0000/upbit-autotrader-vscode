"""
테스트 01: 베이직 수집 테스트 (CandleCollectionTester 래퍼 활용)
BASIC_COLLECTION_TEST_SCENARIOS.md의 시나리오에 따른 실제 CandleDataProvider 테스트
CandleCollectionTester를 사용하여 통계 추적 자동화
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


# ================================================================
# 🎛️ 테스트 설정 (원하는 값으로 수정하여 테스트)
# ================================================================
TEST_CONFIG = {
    # 기본 설정
    "symbol": "KRW-BTC",
    "timeframe": "1m",
    "table_name": "candles_KRW_BTC_1m",

    # 수집 개수 테스트 시나리오들
    "test_scenarios": [
        {"name": "소량 테스트", "count": 50, "description": "빠른 검증용"},
        {"name": "표준 테스트", "count": 100, "description": "기본 테스트"},
        {"name": "중량 테스트", "count": 200, "description": "청크 분할 확인"},
        {"name": "대량 테스트", "count": 500, "description": "다중 청크 테스트"},
        {"name": "문제 재현", "count": 700, "description": "700→464 문제 재현용"},
    ],

    # 현재 실행할 시나리오 (0-4 인덱스)
    "active_scenario": 3,  # 0=50개, 1=100개, 2=200개, 3=500개, 4=700개

    # 고급 설정
    "clean_db_before_test": True,  # 테스트 전 DB 초기화 여부
    "show_detailed_analysis": True,  # 상세 분석 표시 여부
}

# 현재 활성 시나리오 가져오기
CURRENT_SCENARIO = TEST_CONFIG["test_scenarios"][TEST_CONFIG["active_scenario"]]
print(f"🎯 활성 시나리오: {CURRENT_SCENARIO['name']} ({CURRENT_SCENARIO['count']}개) - {CURRENT_SCENARIO['description']}")
print(f"📝 설정 변경: TEST_CONFIG['active_scenario'] = 0~4 (현재: {TEST_CONFIG['active_scenario']})")
print("=" * 80)


class BasicCollectionTester:
    """
    베이직 수집 테스트를 위한 CandleCollectionTester 래퍼
    """

    def __init__(self):
        self.db_cleaner = CandleDBCleaner()
        self.analyzer = CandleDBAnalyzer()
        self.time_utils = CandleTimeUtils()

    async def test_dynamic_collection(self):
        """
        동적 수집 테스트 - TEST_CONFIG 설정에 따라 개수 조정
        """
        scenario = CURRENT_SCENARIO
        count = scenario["count"]

        print(f"\n🔍 === {scenario['name']}: {count}개 수집 테스트 ===")
        print(f"📋 설명: {scenario['description']}")

        # 1. DB 초기화 (설정에 따라)
        if TEST_CONFIG["clean_db_before_test"]:
            print("1. DB 완전 초기화...")
            clear_result = self.db_cleaner.clear_candle_table(TEST_CONFIG["table_name"])
            if clear_result.get('success', False):
                print(f"   ✅ DB 테이블 재생성 완료 (삭제: {clear_result.get('records_before', 0)}개)")
            else:
                print(f"   ❌ DB 초기화 실패: {clear_result.get('error')}")
                return None
        else:
            print("1. DB 초기화 생략 (기존 데이터 유지)")

        # 2. 수집 전 상태 확인
        print("\n2. 수집 전 상태 확인...")
        initial_analysis = self.analyzer.analyze()
        if initial_analysis.get('success'):
            print(f"   초기 레코드 수: {initial_analysis['basic_stats']['total_count']}개")
        else:
            print("   ⚠️ 분석 불가")

        # 3. CandleCollectionTester를 사용하여 동적 개수 캔들 수집
        print(f"\n3. {count}개 캔들 수집 실행...")

        print(f"  심볼: {TEST_CONFIG['symbol']}")
        print(f"  시간틀: {TEST_CONFIG['timeframe']}")
        print(f"  개수: {count}개")

        # CandleCollectionTester를 사용한 수집 및 분석
        async with CandleCollectionTester() as tester:
            collection_stats = await tester.collect_and_analyze(
                symbol=TEST_CONFIG['symbol'],
                timeframe=TEST_CONFIG['timeframe'],
                count=count
            )

            # 4. 수집 결과 분석
            print(f"\n4. 수집 결과 분석...")
            if TEST_CONFIG["show_detailed_analysis"]:
                tester.print_detailed_analysis(collection_stats)
            else:
                print("   (상세 분석 생략 - TEST_CONFIG['show_detailed_analysis'] = False)")

            # 5. 상세 검증
            print("\n5. 상세 검증...")
            self._verify_collection_results(collection_stats)

        return collection_stats

    def _verify_collection_results(self, collection_stats):
        """수집 결과 검증"""
        print("📊 === 검증 결과 ===")

        # 기본 성공 여부
        if collection_stats.success:
            print("  ✅ 수집 성공")
        else:
            print("  ❌ 수집 실패")
            return

        # 요청 vs 수집 비교
        requested = collection_stats.count or 0
        collected = collection_stats.collected_count
        db_stored = collection_stats.db_records_after

        print(f"  요청: {requested}개")
        print(f"  수집: {collected}개")
        print(f"  DB저장: {db_stored}개")

        if collected >= requested:
            print("  ✅ 수집 개수 충족")
        else:
            print(f"  ⚠️ 수집 부족: {requested - collected}개 누락")

        if db_stored >= requested:
            print("  ✅ DB 저장 충족")
        else:
            print(f"  ⚠️ DB 저장 부족: {requested - db_stored}개 누락")

        # 시간 범위 검증
        if collection_stats.db_time_range_after:
            print(f"  📅 시간 범위: {collection_stats.db_time_range_after}")
        else:
            print("  ⚠️ 시간 범위 정보 없음")

async def run_basic_collection_test():
    """베이직 수집 테스트 실행"""
    print("🚀 === CandleCollectionTester 래퍼 활용 베이직 수집 테스트 ===")

    tester = BasicCollectionTester()

    try:
        # 시나리오 실행
        result = await tester.test_dynamic_collection()

        if result is None:
            print("\n❌ 테스트 초기화 실패")
            return False

        print("\n🎯 === 테스트 완료 ===")
        print(f"수집 성공: {result.success}")
        print(f"요청/수집/저장: {result.count}/{result.collected_count}/{result.db_records_after}")
        print(f"응답 시간: {result.response_time_ms:.1f}ms")
        print(f"데이터 소스: {result.data_source}")

        # API 호출 통계
        print(f"API 요청: {result.api_requests_made}회")
        print(f"캐시 히트: {result.cache_hits}회")

    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")
        return False

    return True
if __name__ == "__main__":
    print("CandleCollectionTester 래퍼를 활용한 베이직 수집 테스트 시작...")

    success = asyncio.run(run_basic_collection_test())

    if success:
        print("\n✅ 모든 테스트 완료")
    else:
        print("\n❌ 테스트 실패")
