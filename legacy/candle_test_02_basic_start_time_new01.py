"""
테스트 02: 시작 시간 지정 수집 테스트 (CandleCollectionTesterV2 활용)
고정된 시작 시간을 기준으로 일관된 테스트 결과 확보
CandleDataProvider v4.1과 CandleCollectionTesterV2를 사용하여 end 파라미터로 시작점 지정
CandleCollectionTesterV2를 사용하여 통계 추적 자동화
"""

import sys
import asyncio
import gc
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.candle_data_logic.candle_db_cleaner import CandleDBCleaner
from tests.candle_data_logic.candle_db_analyzer import CandleDBAnalyzer
from tests.candle_data_logic.candle_collection_tester import CandleCollectionTesterV2

# CandleTimeUtils는 선택적 import (현재 사용하지 않음)
try:
    from tests.candle_data_logic.candle_time_utils import CandleTimeUtils
except ImportError:
    CandleTimeUtils = None


# ================================================================
# 🎛️ 테스트 설정 (원하는 값으로 수정하여 테스트)
# ================================================================
TEST_CONFIG = {
    # 기본 설정
    "symbol": "KRW-BTC",
    "timeframe": "1m",
    "table_name": "candles_KRW_BTC_1m",

    # 🕐 고정 시작 시간 (일관된 테스트를 위해) - 과거 시간으로 설정
    "start_time": "2025-09-12T08:00:00",  # UTC 기준 (현재 시각 이전)
    "start_time_desc": "2025년 9월 12일 08시 (UTC)",

    # 수집 개수 테스트 시나리오들
    "test_scenarios": [
        {"name": "소량 테스트", "count": 50, "description": "빠른 검증용 (50분 과거)"},
        {"name": "표준 테스트", "count": 100, "description": "기본 테스트 (100분 과거)"},
        {"name": "중량 테스트", "count": 200, "description": "청크 분할 확인 (200분 과거)"},
        {"name": "대량 테스트", "count": 500, "description": "다중 청크 테스트 (500분 과거)"},
        {"name": "문제 재현", "count": 700, "description": "700→464 문제 재현용 (700분 과거)"},
    ],

    # 현재 실행할 시나리오 (0-4 인덱스)
    "active_scenario": 3,  # 0=50개, 1=100개, 2=200개, 3=500개, 4=700개

    # 고급 설정
    "clean_db_before_test": True,  # 테스트 전 DB 초기화 여부
    "show_detailed_analysis": True,  # 상세 분석 표시 여부
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
    시작 시간 지정 수집 테스트를 위한 CandleCollectionTesterV2 래퍼
    """

    def __init__(self):
        self.db_cleaner = CandleDBCleaner()
        self.analyzer = CandleDBAnalyzer()
        self.time_utils = CandleTimeUtils() if CandleTimeUtils else None

    def cleanup(self):
        """모든 DB 연결 정리"""
        try:
            # 각 컴포넌트의 DB 연결 정리 (필요한 경우)
            # CandleDBCleaner와 CandleDBAnalyzer는 with 구문을 사용하므로 자동 정리되어야 함
            print("🧹 StartTimeCollectionTester DB 연결 정리 완룼")
        except Exception as e:
            print(f"⚠️ StartTimeCollectionTester 정리 중 오류: {e}")

    async def test_start_time_collection(self):
        """
        시작 시간 지정 수집 테스트 - 고정된 시작 시간에서 과거로 수집
        CandleDataProvider v4.1의 end 파라미터를 사용하여 시작점 지정
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

        # 끝 시간 계산 (시작 시간에서 count만큼 과거로)
        from datetime import timedelta
        end_time = start_time - timedelta(minutes=count-1)

        print(f"\n📊 예상 수집 범위:")
        print(f"   📅 시작: {start_time_str}")
        print(f"   📅 종료: {end_time.strftime('%Y-%m-%dT%H:%M:%S')}")
        print(f"   ⏱️ 기간: {count-1}분 ({count}개 캔들)")

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

        # CandleCollectionTesterV2를 사용한 성능 테스트 (to/end 파라미터 사용)
        async with CandleCollectionTesterV2() as tester:
            performance_stats = await tester.test_collection_performance(
                symbol=TEST_CONFIG['symbol'],
                timeframe=TEST_CONFIG['timeframe'],
                to=end_time,    # 종료 시점 (과거)
                end=start_time  # 시작 시점 (현재에 가까운)
            )

            # 4. 수집 결과 분석
            print("\n4. 수집 결과 분석...")
            if TEST_CONFIG["show_detailed_analysis"]:
                tester.print_detailed_analysis(performance_stats)
            else:
                tester.print_performance_summary(performance_stats)

            # 5. 상세 검증
            print("\n5. 상세 검증...")
            self._verify_performance_results(performance_stats)

        return performance_stats

    def _verify_performance_results(self, performance_stats):
        """성능 결과 검증"""
        print("📊 === 검증 결과 ===")

        # 기본 성공 여부
        if performance_stats.success:
            print("  ✅ 수집 성공")
        else:
            print(f"  ❌ 수집 실패: {performance_stats.error_message}")
            return

        # 요청 vs 실제 비교
        requested = performance_stats.count or 0
        planned = performance_stats.total_count
        db_stored = performance_stats.db_records_added

        print(f"  요청: {requested}개")
        print(f"  계획: {planned}개")
        print(f"  DB저장: {db_stored}개")

        if planned >= requested:
            print("  ✅ 계획 수립 정상")
        else:
            print(f"  ⚠️ 계획 부족: {requested - planned}개 차이")

        if db_stored > 0:
            print("  ✅ DB 저장 확인")
        else:
            print("  ⚠️ DB 저장 없음")

        # 성능 지표 검증
        if performance_stats.chunks_per_second > 0:
            print(f"  � 청크 처리 성능: {performance_stats.chunks_per_second:.2f} 청크/초")

        if performance_stats.candles_per_second > 0:
            print(f"  📊 캔들 처리 성능: {performance_stats.candles_per_second:.1f} 캔들/초")


async def run_start_time_collection_test():
    """시작 시간 지정 수집 테스트 실행"""
    print("🚀 === CandleCollectionTesterV2 활용 시작 시간 지정 수집 테스트 ===")

    tester = StartTimeCollectionTester()

    try:
        # 시작 시간 지정 시나리오 실행
        result = await tester.test_start_time_collection()

        if result is None:
            print("\n❌ 테스트 초기화 실패")
            return False

        print("\n🎯 === 테스트 완료 ===")
        print(f"수집 성공: {result.success}")
        print(f"요청/계획/저장: {result.count or 0}/{result.total_count}/{result.db_records_added}")
        print(f"실행 시간: {result.actual_duration_ms:.1f}ms")
        print(f"처리 성능: {result.candles_per_second:.1f} 캔들/초")

        # 청크 처리 통계
        print(f"청크 처리: {result.actual_chunks}개")
        print(f"평균 청크 시간: {result.avg_chunk_time_ms:.1f}ms")

    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")
        return False
    finally:
        # 모든 DB 연결 강제 정리
        try:
            from upbit_auto_trading.infrastructure.database.database_manager import DatabaseConnectionProvider

            # 1. DatabaseConnectionProvider 인스턴스의 DB 매니저 정리
            provider = DatabaseConnectionProvider()
            if hasattr(provider, '_db_manager') and provider._db_manager:
                provider._db_manager.close_all()
                print("🧹 전역 DB 연결 정리 완료")

            # 2. 모든 sqlite3.Connection 객체를 찾아서 강제 종료
            for obj in gc.get_objects():
                if isinstance(obj, sqlite3.Connection):
                    try:
                        obj.close()
                        print("🔧 SQLite 연결 강제 종료")
                    except Exception:
                        pass  # 이미 닫힌 연결일 수 있음

            # 3. 가비지 컬렉션 강제 실행
            collected = gc.collect()
            print(f"🧹 메모리 정리 완료 (정리된 객체: {collected}개)")
        except Exception as e:
            print(f"⚠️ DB 연결 정리 중 오류: {e}")

    return True
if __name__ == "__main__":
    print("CandleCollectionTesterV2 활용한 시작 시간 지정 수집 테스트 시작...")

    success = asyncio.run(run_start_time_collection_test())

    if success:
        print("\n✅ 모든 테스트 완료")
    else:
        print("\n❌ 테스트 실패")
