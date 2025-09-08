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


class BasicCollectionTester:
    """
    베이직 수집 테스트를 위한 CandleCollectionTester 래퍼
    """

    def __init__(self):
        self.db_cleaner = CandleDBCleaner()
        self.analyzer = CandleDBAnalyzer()
        self.time_utils = CandleTimeUtils()

    async def test_scenario_1_collect_100(self):
        """
        시나리오 1: 표준 100개 수집 테스트
        - 현재 시점부터 100개 캔들 요청
        - 완전 신규 수집 (DB 완전 초기화)
        """
        print("\n🔍 === 시나리오 1: 표준 100개 수집 테스트 ===")

        # 1. DB 완전 초기화
        print("1. DB 완전 초기화...")
        self.db_cleaner.clean_table()
        print("   ✅ DB 테이블 재생성 완료")

        # 2. 수집 전 상태 확인
        print("\n2. 수집 전 상태 확인...")
        initial_analysis = self.analyzer.analyze_with_display()

        # 3. CandleCollectionTester를 사용하여 100개 캔들 수집
        print("\n3. 100개 캔들 수집 실행...")

        # 수집 시나리오 정의
        symbol = "KRW-BTC"
        timeframe = "1m"
        count = 100
        print(f"  심볼: {symbol}")
        print(f"  시간틀: {timeframe}")
        print(f"  개수: {count}개")

        # CandleCollectionTester를 사용한 수집 및 분석
        async with CandleCollectionTester() as tester:
            collection_stats = await tester.collect_and_analyze(
                symbol=symbol,
                timeframe=timeframe,
                count=count
            )

            # 4. 수집 결과 분석
            print("\n4. 수집 결과 분석...")
            tester.print_detailed_analysis(collection_stats)

            # 5. 상세 검증
            print("\n5. 상세 검증...")
            self._verify_collection_results(collection_stats)

        return collection_stats

    def _verify_collection_results(self, collection_stats):
        """수집 결과 검증"""
        print("📊 === 검증 결과 ===")

        # 기본 성공 여부
        if collection_stats.collection_success:
            print("  ✅ 수집 성공")
        else:
            print("  ❌ 수집 실패")
            return

        # 요청 vs 수집 비교
        requested = collection_stats.requested_count
        collected = collection_stats.collected_count
        db_stored = collection_stats.db_after.total_count

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

        # 파편화 분석
        fragment_count = len(collection_stats.db_after.fragments)
        if fragment_count == 1:
            print("  ✅ 파편화 없음 (연속 데이터)")
        else:
            print(f"  ⚠️ 파편화 감지: {fragment_count}개 조각")

        # 시간 범위 검증
        if collection_stats.db_after.total_count > 0:
            db_duration = collection_stats.db_after.duration_minutes
            expected_duration = requested - 1  # n개 캔들 = n-1분 구간

            if abs(db_duration - expected_duration) <= 1:  # 1분 허용 오차
                print(f"  ✅ 시간 범위 정상: {db_duration}분")
            else:
                print(f"  ⚠️ 시간 범위 이상: {db_duration}분 (예상: {expected_duration}분)")


async def run_basic_collection_test():
    """베이직 수집 테스트 실행"""
    print("🚀 === CandleCollectionTester 래퍼 활용 베이직 수집 테스트 ===")

    tester = BasicCollectionTester()

    try:
        # 시나리오 1 실행
        result = await tester.test_scenario_1_collect_100()

        print("\n🎯 === 테스트 완료 ===")
        print(f"수집 성공: {result.collection_success}")
        print(f"요청/수집/저장: {result.requested_count}/{result.collected_count}/{result.db_after.total_count}")
        print(f"응답 시간: {result.response_time_ms:.1f}ms")
        print(f"데이터 소스: {result.data_source}")

        if result.error_message:
            print(f"오류: {result.error_message}")

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
