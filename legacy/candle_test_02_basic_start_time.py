"""
테스트 02: 시작 시간 지정 수집 테스트 (CandleCollectionTesterV2 활용)
고정된 시작 시간(2025-09-08T00:00:00)을 기준으로 일관된 테스트 결과 확보
CandleDataProvider v4.1과 CandleCollectionTesterV2를 사용한 성능 측정
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

# 테스트 의존성 import
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

    # 🕐 고정 시작 시간 (일관된 테스트를 위해) - 과거 시간으로 설정
    "start_time": "2025-09-12T10:00:00",  # UTC 기준 (현재 시각 이전)
    "start_time_desc": "2025년 9월 12일 10시 (UTC)",

    # 수집 개수 테스트 시나리오들
    "test_scenarios": [
        {"name": "소량 테스트", "count": 50, "description": "빠른 검증용 (50분 과거)"},
        {"name": "표준 테스트", "count": 100, "description": "기본 테스트 (100분 과거)"},
        {"name": "중량 테스트", "count": 200, "description": "청크 분할 확인 (200분 과거)"},
        {"name": "대량 테스트", "count": 500, "description": "다중 청크 테스트 (500분 과거)"},
        {"name": "문제 재현", "count": 700, "description": "700→464 문제 재현용 (700분 과거)"},
    ],

    # 현재 실행할 시나리오 (0-4 인덱스)
    "active_scenario": 1,  # 0=50개, 1=100개, 2=200개, 3=500개, 4=700개

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
    시작 시간 지정 수집 테스트를 위한 CandleCollectionTesterV2 래퍼
    """

    def __init__(self):
        self.db_cleaner = CandleDBCleaner()
        self.analyzer = CandleDBAnalyzer()
        self.time_utils = CandleTimeUtils()

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

        # 예상 시간 범위 계산 및 표시
        if TEST_CONFIG["show_expected_range"]:
            print("\n📊 예상 결과 계산...")
            expected = self.time_utils.get_time_info(start_time_str, count)
            print(f"   📅 예상 시간 범위: {expected['start_utc']} → {expected['end_utc']}")
            print(f"   ⏱️ 예상 기간: {expected['duration_minutes']}분 ({count}개 캔들)")

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

        # 3. CandleCollectionTesterV2를 사용하여 시작 시간 지정 수집
        print(f"\n3. {count}개 캔들 수집 실행 (시작 시간 지정)...")
        print(f"  심볼: {TEST_CONFIG['symbol']}")
        print(f"  시간틀: {TEST_CONFIG['timeframe']}")
        print(f"  개수: {count}개")
        print(f"  시작 시간: {start_time_str}")

        # CandleCollectionTesterV2를 사용한 성능 테스트 (end 파라미터 사용)
        async with CandleCollectionTesterV2() as tester:
            collection_stats = await tester.test_collection_performance(
                symbol=TEST_CONFIG['symbol'],
                timeframe=TEST_CONFIG['timeframe'],
                count=count,
                end=start_time  # end 파라미터로 시작 시간 지정 (업비트 방향)
            )

            # 4. 수집 결과 분석
            print("\n4. 수집 결과 분석...")

            print("\n📊 === 성능 테스트 결과 ===")
            print(f"🎯 요청: {TEST_CONFIG['symbol']} {TEST_CONFIG['timeframe']}")
            print(f"   📝 개수: {count}개")
            print(f"   🕐 시작 시간: {start_time_str}")

            # 성능 분석 출력 (간단한 형태)
            print("\n📋 계획 vs 실제:")
            print(f"   📊 캔들: 예상 {collection_stats.total_count}개")
            print(f"   📦 청크: 예상 {collection_stats.estimated_chunks}개 → 실제 {collection_stats.actual_chunks}개")
            duration_actual = collection_stats.actual_duration_ms / 1000
            print(f"   ⏱️ 소요시간: 예상 {collection_stats.estimated_duration_seconds:.1f}초 → 실제 {duration_actual:.1f}초")

            print("\n🚀 성능 지표:")
            print(f"   📦 청크/초: {collection_stats.chunks_per_second:.2f}")
            print(f"   📊 캔들/초: {collection_stats.candles_per_second:.1f}")
            print(f"   🌐 API 호출: {collection_stats.total_api_calls}회")

            print("\n💾 DB 상태:")
            print(f"   📋 이전: {collection_stats.db_records_before}개")
            print(f"   📋 이후: {collection_stats.db_records_after}개")
            print(f"   📈 증가: +{collection_stats.db_records_after - collection_stats.db_records_before}개")

            if TEST_CONFIG["show_detailed_analysis"]:
                print("\n⏱️ 청크 처리 시간:")
                print(f"   평균: {collection_stats.avg_chunk_time_ms:.1f}ms")
                print(f"   최소: {collection_stats.min_chunk_time_ms:.1f}ms")
                print(f"   최대: {collection_stats.max_chunk_time_ms:.1f}ms")

            # 5. 상세 검증
            print("\n5. 상세 검증...")
            self._verify_start_time_results(collection_stats, start_time_str, count)

        return collection_stats

    def _verify_start_time_results(self, collection_stats, start_time_str, count):
        """시작 시간 지정 수집 결과 검증 (PerformanceStats 기준)"""
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
        planned = collection_stats.total_count
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
        print(f"  📦 청크 처리 성능: {collection_stats.chunks_per_second:.2f} 청크/초")
        print(f"  📊 캔들 처리 성능: {collection_stats.candles_per_second:.1f} 캔들/초")

        # 시간 정보 확인
        if collection_stats.end:
            print(f"  🕐 실제 end 파라미터: {collection_stats.end}")
            # end 파라미터가 지정한 시작 시간과 일치하는지 확인
            if start_time_str in str(collection_stats.end):
                print("  ✅ 시작 시간 일치 확인")
            else:
                print(f"  ⚠️ 시작 시간 불일치: 지정({start_time_str}) vs 실제({collection_stats.end})")


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
        success = result.db_records_after > 0
        requested = CURRENT_SCENARIO['count']
        db_stored = result.db_records_after - result.db_records_before

        print(f"수집 성공: {success}")
        print(f"요청/계획/저장: {requested}/{result.total_count}/{db_stored}")
        print(f"실행 시간: {result.actual_duration_ms:.1f}ms")
        print(f"처리 성능: {result.candles_per_second:.1f} 캔들/초")
        print(f"청크 처리: {result.actual_chunks}개")
        print(f"평균 청크 시간: {result.avg_chunk_time_ms:.1f}ms")

        # 시작 시간 정보
        print(f"지정 시작 시간: {TEST_CONFIG['start_time']}")
        if result.end:
            print(f"실제 end 파라미터: {result.end}")

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
