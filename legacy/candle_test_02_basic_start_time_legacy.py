"""
테스트 02: 시작 시간 지정 수집 테스트 (CandleCollectionTester 래퍼 활용)
고정된 시작 시간(2025-09-08T00:00:00)을 기준으로 일관된 테스트 결과 확보
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
from tests.candle_data_logic.candle_collection_tester import CandleCollectionTesterV2


# ================================================================
# 🎛️ 테스트 설정 (시작 시간 지정 테스트용)
# ================================================================
TEST_CONFIG = {
    # 기본 설정
    "symbol": "KRW-BTC",
    "timeframe": "1m",
    "table_name": "candles_KRW_BTC_1m",

    # 🕐 고정 시작 시간 (일관된 테스트를 위해)
    "start_time": "2025-09-08T00:00:00",  # UTC 기준
    "start_time_desc": "2025년 9월 8일 자정 (UTC)",

    # 수집 개수 테스트 시나리오들
    "test_scenarios": [
        {"name": "소량 테스트", "count": 50, "description": "빠른 검증용 (50분 과거)"},
        {"name": "표준 테스트", "count": 100, "description": "기본 테스트 (100분 과거)"},
        {"name": "중량 테스트", "count": 200, "description": "청크 분할 확인 (200분 과거)"},
        {"name": "대량 테스트", "count": 500, "description": "다중 청크 테스트 (500분 과거)"},
        {"name": "문제 재현", "count": 700, "description": "700→464 문제 재현용 (700분 과거)"},
    ],

    # 현재 실행할 시나리오 (0-4 인덱스)
    "active_scenario": 4,  # 0=50개, 1=100개, 2=200개, 3=500개, 4=700개

    # 고급 설정
    "clean_db_before_test": True,  # 테스트 전 DB 초기화 여부
    "show_detailed_analysis": True,  # 상세 분석 표시 여부
    "show_expected_range": True,  # 예상 시간 범위 표시 여부
}

# 현재 활성 시나리오 가져오기
CURRENT_SCENARIO = TEST_CONFIG["test_scenarios"][TEST_CONFIG["active_scenario"]]
print(f"🎯 활성 시나리오: {CURRENT_SCENARIO['name']} ({CURRENT_SCENARIO['count']}개)")
print(f"📋 설명: {CURRENT_SCENARIO['description']}")
print(f"🕐 고정 시작 시간: {TEST_CONFIG['start_time']} ({TEST_CONFIG['start_time_desc']})")
print(f"📝 설정 변경: TEST_CONFIG['active_scenario'] = 0~4 (현재: {TEST_CONFIG['active_scenario']})")
print("=" * 80)


class StartTimeCollectionTester:
    """
    시작 시간 지정 수집 테스트를 위한 CandleCollectionTester 래퍼
    """

    def __init__(self):
        self.db_cleaner = CandleDBCleaner()
        self.analyzer = CandleDBAnalyzer()
        self.time_utils = CandleTimeUtils()

    async def test_start_time_collection(self):
        """
        시작 시간 지정 수집 테스트 - 고정된 시작 시간에서 과거로 수집
        """
        scenario = CURRENT_SCENARIO
        count = scenario["count"]
        start_time_str = TEST_CONFIG["start_time"]

        print(f"\n🔍 === {scenario['name']}: {count}개 수집 테스트 (시작 시간 지정) ===")
        print(f"📋 설명: {scenario['description']}")
        print(f"🕐 시작 시간: {start_time_str} (고정)")

        # 시작 시간을 datetime 객체로 변환
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        # 예상 시간 범위 계산 및 표시
        if TEST_CONFIG["show_expected_range"]:
            print(f"\n📊 예상 결과 계산...")
            expected = self.time_utils.get_time_info(start_time_str, count)
            print(f"   📅 예상 시간 범위: {expected['start_utc']} → {expected['end_utc']}")
            print(f"   ⏱️  예상 기간: {expected['duration_minutes']}분 ({count}개 캔들)")

        # 1. DB 초기화 (설정에 따라)
        if TEST_CONFIG["clean_db_before_test"]:
            print("\n1. DB 완전 초기화...")
            clear_result = self.db_cleaner.clear_candle_table(TEST_CONFIG["table_name"])
            if clear_result.get('success', False):
                print(f"   ✅ DB 테이블 재생성 완료 (삭제: {clear_result.get('records_before', 0)}개)")
            else:
                print(f"   ❌ DB 초기화 실패: {clear_result.get('error')}")
                return None
        else:
            print("\n1. DB 초기화 생략 (기존 데이터 유지)")

        # 2. 수집 전 상태 확인
        print("\n2. 수집 전 상태 확인...")
        initial_analysis = self.analyzer.analyze()
        if initial_analysis.get('success'):
            print(f"   초기 레코드 수: {initial_analysis['basic_stats']['total_count']}개")
        else:
            print("   ⚠️ 분석 불가")

        # 3. CandleCollectionTester를 사용하여 시작 시간 지정 수집
        print(f"\n3. {count}개 캔들 수집 실행 (시작 시간 지정)...")

        print(f"  심볼: {TEST_CONFIG['symbol']}")
        print(f"  시간틀: {TEST_CONFIG['timeframe']}")
        print(f"  개수: {count}개")
        print(f"  시작 시간: {start_time_str}")

        # CandleCollectionTester를 사용한 수집 및 분석
        async with CandleCollectionTester() as tester:
            collection_stats = await tester.collect_and_analyze(
                symbol=TEST_CONFIG['symbol'],
                timeframe=TEST_CONFIG['timeframe'],
                count=count,
                start_time=start_time  # 시작 시간 지정
            )

            # 4. 수집 결과 분석
            print("\n4. 수집 결과 분석...")

            print("\n📊 === 성능 테스트 결과 ===")
            print(f"🎯 요청: {TEST_CONFIG['symbol']} {TEST_CONFIG['timeframe']}")
            print(f"   📝 개수: {count}개")
            print(f"   🕐 시작 시간: {start_time_str}")

            if TEST_CONFIG["show_detailed_analysis"]:
                # 상세 성능 분석 출력
                from tests.candle_data_logic.candle_collection_tester import print_performance_stats
                print_performance_stats(collection_stats)
            else:
                # 요약 정보만 출력
                print(f"   ✅ 수집 완료: {collection_stats.actual_duration_ms:.1f}ms")
                print(f"   📊 처리 성능: {collection_stats.candles_per_second:.1f} 캔들/초")
                print(f"   🌐 API 호출: {collection_stats.api_calls}회")

            # 5. 상세 검증
            print("\n5. 상세 검증...")
            self._verify_start_time_results(collection_stats, start_time_str, count)

        return collection_stats

    def _verify_start_time_results(self, collection_stats, start_time_str, count):
        """시작 시간 지정 수집 결과 검증"""
        print("📊 === 검증 결과 ===")

        # 기본 성공 여부 (PerformanceStats는 성공을 db_records_after > 0으로 판단)
        success = collection_stats.db_records_after > 0
        if success:
            print("  ✅ 수집 성공")
        else:
            print("  ❌ 수집 실패")
            return

        # 요청 vs 수집 비교
        requested = count
        planned = collection_stats.planned_count
        db_stored = collection_stats.db_records_after - collection_stats.db_records_before

        print(f"  요청: {requested}개")
        print(f"  계획: {planned}개")
        print(f"  DB저장: {db_stored}개")

        if planned >= requested:
            print("  ✅ 계획 수립 정상")
        else:
            print(f"  ⚠️ 계획 부족: {requested - planned}개 누락")

        if db_stored >= requested:
            print("  ✅ DB 저장 확인")
        else:
            print(f"  ⚠️ DB 저장 부족: {requested - db_stored}개 누락")

        # 성능 지표
        print(f"  � 청크 처리 성능: {collection_stats.chunks_per_second:.2f} 청크/초")
        print(f"  📊 캔들 처리 성능: {collection_stats.candles_per_second:.1f} 캔들/초")


async def run_start_time_collection_test():
    """시작 시간 지정 수집 테스트 실행"""
    print("🚀 === CandleCollectionTester 래퍼 활용 시작 시간 지정 수집 테스트 ===")

    tester = StartTimeCollectionTester()

    try:
        # 시작 시간 지정 시나리오 실행
        result = await tester.test_start_time_collection()

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

        # 시작 시간 정보
        print(f"지정 시작 시간: {TEST_CONFIG['start_time']}")
        if result.start_time:
            print(f"실제 시작 시간: {result.start_time}")

    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")
        return False

    return True
if __name__ == "__main__":
    print("CandleCollectionTester 래퍼를 활용한 시작 시간 지정 수집 테스트 시작...")

    success = asyncio.run(run_start_time_collection_test())

    if success:
        print("\n✅ 모든 테스트 완료")
    else:
        print("\n❌ 테스트 실패")
