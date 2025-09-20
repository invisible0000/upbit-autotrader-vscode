"""
테스트 05: 오버랩 부분 데이터 테스트 (OverlapAnalyzer 검증)
기존 DB에 파편화된 데이터가 있을 때 get_candles()가 올바르게 동작하는지 검증
OverlapAnalyzer의 PARTIAL 처리 능력 테스트

테스트 순서:
1. DB 청소
2. 파편화 레코드 생성 (부분적 캔들 데이터)
3. 파편화 확인 및 사용자 검토 시간 제공
4. 캔들 수집 (get_candles 사용)
5. 결과 확인 및 검증
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

# Test helper imports
from tests.candle_data_logic.candle_db_cleaner import CandleDBCleaner
from tests.candle_data_logic.candle_db_analyzer import CandleDBAnalyzer
from tests.candle_data_logic.candle_db_generator import CandleDBGenerator


# ================================================================
# 🎛️ 테스트 설정 (원하는 값으로 수정하여 테스트)
# ================================================================
TEST_CONFIG = {
    # 기본 설정
    "symbol": "KRW-BTC",
    "timeframe": "1m",
    # "start_time": "2025-09-09 00:50:00",
    "start_time": "2025-07-30 16:22:00",  # 빈캔들 3개 전 시점
    "count": 200,
    "chunk_size": 5,

    # 파편 레코드 설정 (오버랩 상황 시뮬레이션)
    # "partial_records": [],
    "partial_records": [
        {"start_time": "2025-09-09 00:47:00", "count": 2},  # 2개 캔들 조각
        {"start_time": "2025-09-09 00:41:00", "count": 2},   # 2개 캔들 조각
        {"start_time": "2025-09-09 00:37:00", "count": 1}
    ],

    # 고급 설정
    "table_name": "candles_KRW_BTC_1m",
    "pause_for_verification": False,  # 파편 생성 후 사용자 확인 대기
    "complete_db_table_view": False  # 테스트 후 DB 테이블 전체 보기
}


class OverlapPartialDataTester:
    """
    오버랩 부분 데이터 테스트
    OverlapAnalyzer가 부분적으로 겹치는 데이터를 올바르게 처리하는지 검증
    """

    def __init__(self):
        self.db_cleaner = CandleDBCleaner()
        self.analyzer = CandleDBAnalyzer()
        self.generator = CandleDBGenerator()
        self.candle_provider = None

    async def setup_candle_provider(self):
        """CandleDataProvider 초기화 (작은 청크 사이즈 적용)"""
        try:
            # 동적 import
            from upbit_auto_trading.infrastructure.database.database_manager import DatabaseConnectionProvider
            from upbit_auto_trading.infrastructure.repositories.sqlite_candle_repository import SqliteCandleRepository
            from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
            from upbit_auto_trading.infrastructure.market_data.candle.overlap_analyzer import OverlapAnalyzer
            from upbit_auto_trading.infrastructure.market_data.candle.candle_data_provider import CandleDataProvider

            # DatabaseConnectionProvider 초기화
            db_provider = DatabaseConnectionProvider()
            db_provider.initialize({
                'settings': 'data/settings.sqlite3',
                'strategies': 'data/strategies.sqlite3',
                'market_data': 'data/market_data.sqlite3'
            })

            # 의존성 생성
            from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils

            repository = SqliteCandleRepository(db_provider.get_manager())
            upbit_client = UpbitPublicClient()
            time_utils = TimeUtils()
            overlap_analyzer = OverlapAnalyzer(repository, time_utils)

            # 작은 청크 사이즈로 CandleDataProvider 생성
            self.candle_provider = CandleDataProvider(
                repository=repository,
                upbit_client=upbit_client,
                overlap_analyzer=overlap_analyzer,
                chunk_size=TEST_CONFIG["chunk_size"]  # 작은 청크 사이즈 적용
            )

            print(f"✅ CandleDataProvider 초기화 완료 (chunk_size: {TEST_CONFIG['chunk_size']})")
            return True

        except Exception as e:
            print(f"❌ CandleDataProvider 초기화 실패: {e}")
            return False

    def cleanup(self):
        """모든 리소스 정리"""
        try:
            # CandleDataProvider 정리
            if self.candle_provider and hasattr(self.candle_provider, 'upbit_client'):
                asyncio.create_task(self.candle_provider.upbit_client.close())

            # DB 연결 강제 정리
            from upbit_auto_trading.infrastructure.database.database_manager import DatabaseConnectionProvider
            provider = DatabaseConnectionProvider()
            if hasattr(provider, '_db_manager') and provider._db_manager:
                provider._db_manager.close_all()

            # SQLite 연결 강제 종료
            for obj in gc.get_objects():
                if isinstance(obj, sqlite3.Connection):
                    try:
                        obj.close()
                    except Exception:
                        pass

            gc.collect()
            print("🧹 리소스 정리 완료")

        except Exception as e:
            print(f"⚠️ 리소스 정리 중 오류: {e}")

    async def run_overlap_test(self):
        """오버랩 부분 데이터 테스트 실행"""
        print("🔍 === 오버랩 부분 데이터 테스트 ===")
        print(f"심볼: {TEST_CONFIG['symbol']}")
        print(f"타임프레임: {TEST_CONFIG['timeframe']}")
        print(f"수집 시작: {TEST_CONFIG['start_time']}")
        print(f"수집 개수: {TEST_CONFIG['count']}개")
        print(f"청크 크기: {TEST_CONFIG['chunk_size']}개")
        print(f"파편 레코드: {len(TEST_CONFIG['partial_records'])}개")
        print("=" * 60)

        # 1. DB 청소
        print(" 1️⃣ DB 청소...")
        clear_result = self.db_cleaner.clear_candle_table(TEST_CONFIG["table_name"])
        if not clear_result.get('success', False):
            print(f"❌ DB 청소 실패: {clear_result.get('error')}")
            return False

        print(f"✅ DB 청소 완료 (이전 레코드: {clear_result.get('records_before', 0)}개)")

        # 2. 파편화 레코드 생성
        print(" 2️⃣ 파편화 레코드 생성...")
        partial_records = TEST_CONFIG["partial_records"]

        if not partial_records:
            print("ℹ️ 파편 레코드 설정이 없습니다. 빈 DB로 테스트 진행")
        else:
            for i, record in enumerate(partial_records, 1):
                start_time = record["start_time"]
                count = record["count"]

                print(f"  생성 {i}: {start_time}부터 {count}개")

                # 시간 형식 변환 (YYYY-MM-DD HH:MM:SS → YYYY-MM-DDTHH:MM:SS)
                iso_time = start_time.replace(" ", "T")

                result = self.generator.generate_candle_data(
                    start_time=iso_time,
                    count=count
                )

                if result.get('success'):
                    print(f"    ✅ 생성 완료: {result.get('records_created', 0)}개")
                else:
                    print(f"    ❌ 생성 실패: {result.get('error')}")
                    return False

        # 3. 파편화 확인
        print(" 3️⃣ 파편화 데이터 확인...")
        analysis = self.analyzer.analyze()
        if analysis.get('success'):
            total_count = analysis['basic_stats']['total_count']
            print(f"✅ 현재 DB 레코드: {total_count}개")

            if total_count > 0:
                # 시간 범위 확인
                time_stats = analysis.get('time_stats', {})
                if time_stats:
                    print(f"  시간 범위: {time_stats.get('earliest_utc')} ~ {time_stats.get('latest_utc')}")

        else:
            print("⚠️ DB 분석 실패")

        # 4. 사용자 확인 대기 (설정에 따라)
        if TEST_CONFIG["pause_for_verification"]:
            print(" ⏸️  파편화 데이터 생성 완료. DB 상태를 확인하고 엔터를 눌러 계속...")
            input()

        # 5. CandleDataProvider 초기화
        print(" 4️⃣ CandleDataProvider 초기화...")
        if not await self.setup_candle_provider():
            return False

        # 6. 캔들 수집 (get_candles 사용)
        print(" 5️⃣ 캔들 수집 실행...")
        start_time_str = TEST_CONFIG["start_time"]
        count = TEST_CONFIG["count"]

        # 시작 시간 파싱
        try:
            start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
            start_time = start_time.replace(tzinfo=timezone.utc)
            print(f"  수집 시작 시간: {start_time} (UTC)")
        except ValueError as e:
            print(f"❌ 시간 파싱 실패: {e}")
            return False

        # get_candles 호출
        try:
            print(f"  📥 get_candles 호출: {TEST_CONFIG['symbol']} {TEST_CONFIG['timeframe']} count={count}")

            # ⏱️ 성능 측정 시작
            import time
            start_performance = time.time()

            collected_candles = await self.candle_provider.get_candles(
                symbol=TEST_CONFIG['symbol'],
                timeframe=TEST_CONFIG['timeframe'],
                count=count,
                to=start_time
            )

            # ⏱️ 성능 측정 완료
            end_performance = time.time()
            total_duration = end_performance - start_performance
            avg_per_candle = (total_duration / len(collected_candles)) * 1000 if len(collected_candles) > 0 else 0

            print(f"✅ 캔들 수집 완료: {len(collected_candles)}개 수집됨")
            print(f"📊 성능: 총 {total_duration:.1f}초, 캔들당 평균 {avg_per_candle:.2f}ms")

        except Exception as e:
            print(f"❌ 캔들 수집 실패: {e}")
            return False

        # 7. 결과 확인
        print(" 6️⃣ 결과 확인 및 검증...")

        # 최종 DB 분석
        final_analysis = self.analyzer.analyze()
        if final_analysis.get('success'):
            final_count = final_analysis['basic_stats']['total_count']
            print(f"  최종 DB 레코드: {final_count}개")

            # 수집 전후 비교
            initial_count = analysis['basic_stats']['total_count'] if analysis.get('success') else 0
            added_records = final_count - initial_count
            print(f"  추가된 레코드: {added_records}개")

        else:
            print("  ⚠️ 최종 분석 실패")

        # 간결한 최종 결과
        print(" 📋 === 최종 결과 ===")
        print(f"요청 수집: {count}개")
        print(f"실제 반환: {len(collected_candles)}개")
        print(f"파편 레코드: {len(TEST_CONFIG['partial_records'])}개 조각")
        print(f"청크 크기: {TEST_CONFIG['chunk_size']}개")

        if len(collected_candles) == count:
            print("✅ 수집 개수 일치")
        else:
            print(f"⚠️ 수집 개수 불일치 (요청: {count}, 실제: {len(collected_candles)})")

        # 8. 설정에 따른 DB 테이블 전체 출력 (대용량 테스트 시 생략)
        if TEST_CONFIG["complete_db_table_view"]:
            print(" 📊 === 최종 DB 상태 ===")
            try:
                import sqlite3
                conn = sqlite3.connect('data/market_data.sqlite3')
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT candle_date_time_utc, candle_date_time_kst, timestamp '
                    'FROM candles_KRW_BTC_1m ORDER BY candle_date_time_utc DESC'
                )
                results = cursor.fetchall()
                print('=== KRW-BTC 1분 캔들 데이터 (UTC 시간 내림차순) ===')
                print('UTC 시간\t\t\tKST 시간\t\t\t타임스탬프')
                print('-' * 80)
                for row in results:
                    print(f'{row[0]}\t{row[1]}\t{row[2]}')
                conn.close()
                print(f" 총 {len(results)}개 레코드")
            except Exception as e:
                print(f"DB 조회 실패: {e}")
        else:
            # 간결한 DB 통계만 표시
            try:
                import sqlite3
                conn = sqlite3.connect('data/market_data.sqlite3')
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM candles_KRW_BTC_1m')
                total_records = cursor.fetchone()[0]

                cursor.execute(
                    'SELECT MIN(candle_date_time_utc), MAX(candle_date_time_utc) '
                    'FROM candles_KRW_BTC_1m'
                )
                min_time, max_time = cursor.fetchone()
                conn.close()

                print(f" 📊 === DB 요약 ===   총 {total_records}개 레코드")
                if min_time and max_time:
                    print(f" 🕐 시간범위: {min_time} ~ {max_time}")

            except Exception as e:
                print(f"간결 DB 조회 실패: {e}")

        return True


async def run_overlap_partial_test():
    """오버랩 부분 데이터 테스트 실행"""
    print("🚀 === OverlapAnalyzer 부분 데이터 처리 테스트 ===")
    print("목적: 기존 DB 파편과 새로운 수집 데이터의 오버랩 처리 검증")
    print("=" * 60)

    tester = OverlapPartialDataTester()

    try:
        result = await tester.run_overlap_test()

        print(" 🎯 === 테스트 완료 ===")
        if result:
            print("✅ 오버랩 부분 데이터 테스트 성공")
        else:
            print("❌ 오버랩 부분 데이터 테스트 실패")

        return result

    except Exception as e:
        print(f" ❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        tester.cleanup()


if __name__ == "__main__":
    print("OverlapAnalyzer 부분 데이터 처리 테스트 시작...")

    success = asyncio.run(run_overlap_partial_test())

    if success:
        print(" ✅ 모든 테스트 완료")

    else:
        print(" ❌ 테스트 실패")
