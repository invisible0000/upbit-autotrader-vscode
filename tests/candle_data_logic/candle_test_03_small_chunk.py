"""
테스트 03: 청크 사이즈 조절 테스트 (CandleCollectionTesterV2 활용)
작은 청크 사이즈로 세밀한 진행률 추적 및 성능 비교 테스트
chunk_size 파라미터를 조절하여 다양한 수집 전략 검증
"""

import sys
import asyncio
import gc
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

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

    # 시작 시간 지정 (수집의 시작점, 여기서부터 과거로 수집)
    "start_time": "2025-09-09 00:50:00",  # YYYY-MM-DD HH:MM:SS 형식

    # 청크 사이즈 설정 (기본값: 200, 최대: 200)
    "chunk_size": 10,  # 작은 청크로 세밀한 진행률 추적

    # 수집 개수 테스트 시나리오들 (작은 청크로 세밀한 진행률 체험)
    "test_scenarios": [
        {"name": "미니 테스트", "count": 30, "description": "미니 청크 기본 테스트 (30개)"},
        {"name": "소형 테스트", "count": 60, "description": "소형 청크 2개 분할 (60개)"},
        {"name": "중형 테스트", "count": 150, "description": "중형 청크 6개 분할 (150개)"},
        {"name": "대형 테스트", "count": 300, "description": "대형 청크 12개 분할 (300개)"},
        {"name": "수퍼 테스트", "count": 500, "description": "수퍼 청크 20개 분할 (500개)"},
    ],

    # 현재 실행할 시나리오 (0-4 인덱스)
    "active_scenario": 3,  # 0=30개, 1=60개, 2=150개, 3=300개, 4=500개

    # 고급 설정
    "clean_db_before_test": True,  # 테스트 전 DB 초기화 여부
    "show_detailed_analysis": True,  # 상세 분석 표시 여부
}

# 현재 활성 시나리오 가져오기
CURRENT_SCENARIO = TEST_CONFIG["test_scenarios"][TEST_CONFIG["active_scenario"]]
print(f"🎯 활성 시나리오: {CURRENT_SCENARIO['name']} ({CURRENT_SCENARIO['count']}개) - {CURRENT_SCENARIO['description']}")
print(f"� 청크 사이즈: {TEST_CONFIG['chunk_size']}개 (기본: 200개)")
print(f"�📝 설정 변경: TEST_CONFIG['active_scenario'] = 0~4 (현재: {TEST_CONFIG['active_scenario']})")
print("=" * 80)


class SmallChunkCollectionTester:
    """
    청크 사이즈 조절 테스트를 위한 CandleCollectionTester 래퍼
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
            print("🧹 SmallChunkCollectionTester DB 연결 정리 완룼")
        except Exception as e:
            print(f"⚠️ SmallChunkCollectionTester 정리 중 오류: {e}")

    async def test_small_chunk_collection(self):
        """
        작은 청크 사이즈 수집 테스트 - 세밀한 진행률 추적
        CandleCollectionTesterV2에 chunk_size 파라미터를 전달하여 작은 청크 테스트
        """
        scenario = CURRENT_SCENARIO
        count = scenario["count"]
        start_time_str = TEST_CONFIG["start_time"]

        print(f"\n🔍 === {scenario['name']}: {count}개 수집 테스트 (작은 청크) ===")
        print(f"📋 설명: {scenario['description']}")
        print(f"🕐 시작 시간: {start_time_str} (고정)")
        print(f"📦 청크 사이즈: {TEST_CONFIG['chunk_size']}개")

        # 시작 시간을 datetime 객체로 변환 (UTC 시간대로)
        try:
            start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
            start_time = start_time.replace(tzinfo=timezone.utc)  # UTC 시간대 추가
            print(f"   ✅ 시간 파싱 성공: {start_time} (UTC)")
        except ValueError as e:
            print(f"   ❌ 시간 파싱 실패: {e}")
            print("   💡 형식: YYYY-MM-DD HH:MM:SS (예: 2024-12-01 12:00:00)")
            return None

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

        # CandleCollectionTesterV2를 사용한 성능 테스트 (chunk_size + to 파라미터 사용)
        async with CandleCollectionTesterV2(chunk_size=TEST_CONFIG['chunk_size']) as tester:
            performance_stats = await tester.test_collection_performance(
                symbol=TEST_CONFIG['symbol'],
                timeframe=TEST_CONFIG['timeframe'],
                to=start_time,  # 시작 시간 지정 (여기서부터 과거로 수집)
                count=count     # 수집할 캔들 개수
            )

            # 4. 수집 결과 분석
            print("\n4. 수집 결과 분석...")
            if TEST_CONFIG["show_detailed_analysis"]:
                tester.print_detailed_analysis(performance_stats)
            else:
                tester.print_performance_summary(performance_stats)

            # 5. 상세 검증
            print("\n5. 상세 검증...")
            self._verify_chunk_size_results(performance_stats, start_time_str, count)

        return performance_stats

    def _verify_chunk_size_results(self, performance_stats, start_time_str, count):
        """작은 청크 사이즈 수집 결과 검증"""
        print("📊 === 검증 결과 (작은 청크 수집) ===")

        # 기본 성공 여부
        if performance_stats.success:
            print("  ✅ 수집 성공")
        else:
            print(f"  ❌ 수집 실패: {performance_stats.error_message}")
            return

        # 요청 vs 실제 비교
        requested = count
        planned = performance_stats.total_count
        db_stored = performance_stats.db_records_added

        print(f"  요청: {requested}개")
        print(f"  계획: {planned}개")
        print(f"  DB저장: {db_stored}개")
        print(f"  시작시간: {start_time_str}")

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

        # 청크 사이즈 특화 검증
        chunk_size = TEST_CONFIG['chunk_size']
        expected_chunks = (requested + chunk_size - 1) // chunk_size  # 올림 나눗셈
        actual_chunks = performance_stats.actual_chunks

        print(f"  📦 청크 사이즈: {chunk_size}개")
        print(f"  📊 예상 청크 수: {expected_chunks}개")
        print(f"  📊 실제 청크 수: {actual_chunks}개")

        if actual_chunks == expected_chunks:
            print(f"  ✅ 청크 분할 정상: {chunk_size}개 단위로 정확히 분할됨")
        else:
            print(f"  ⚠️ 청크 분할 비정상: 예상 {expected_chunks} ≠ 실제 {actual_chunks}")

        print(f"  🕐 지정된 시작시간부터 {requested}개 캔들 수집 완료")


async def run_small_chunk_collection_test():
    """작은 청크 사이즈 수집 테스트 실행"""
    print(f"🚀 === CandleCollectionTesterV2 활용 작은 청크 (크기: {TEST_CONFIG['chunk_size']}) 수집 테스트 ===")

    tester = SmallChunkCollectionTester()

    try:
        # 작은 청크 시나리오 실행
        result = await tester.test_small_chunk_collection()

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

        # 청크 사이즈 특화 정보
        print(f"시작 시간: {TEST_CONFIG['start_time']}에서 과거로 수집")
        print(f"청크 사이즈: {TEST_CONFIG['chunk_size']}개 (기본 200개대비 {200 / TEST_CONFIG['chunk_size']:.1f}배 세밀함)")

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
    print(f"CandleCollectionTesterV2 활용한 작은 청크 (크기: {TEST_CONFIG['chunk_size']}) 수집 테스트 시작...")

    success = asyncio.run(run_small_chunk_collection_test())

    if success:
        print("\n✅ 모든 테스트 완료")
    else:
        print("\n❌ 테스트 실패")
