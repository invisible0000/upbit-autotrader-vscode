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
from datetime import datetime, timezone, timedelta
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
    # 기본 설정 (table_name은 symbol + timeframe으로 자동 생성)
    "symbol": "KRW-BTC",
    "timeframe": "1m",

    # 수집설정(get_cadles 파라미터로 변환)
    # 시간대 표기 예시:
    # "start_time": "2025-09-22 21:11:00 KST",     # KST → UTC 자동변환 (KST -9시간)
    # "start_time": "2025-09-22 12:11:00 UTC",     # UTC (변환 없음)
    # "start_time": "2025-09-22 21:11:00 +09:00",  # UTC 오프셋 표기
    # "start_time": "2025-09-22 12:11:00",         # 시간대 없음 (UTC 기본)

    "start_time": "",  # UTC 오프셋 형식 테스트 (UTC 02:00)
    "end_time": "",                        # to_count 패턴
    "count": 15,                           # 15개 수집

    # 청크사이즈 설정(CandleDataProvider에 전달, 작게 설정하여 여러 청크로 나누어 수집 테스트)
    "chunk_size": 5,

    # 파편 레코드 설정 (오버랩 상황 시뮬레이션, candle_db_generator 사용)
    "partial_records": [],
    # "partial_records": [
    #     {"start_time": "2025-09-09 00:47:00", "count": 2},  # 2개 캔들 조각
    #     {"start_time": "2025-09-09 00:41:00", "count": 2},   # 2개 캔들 조각
    #     {"start_time": "2025-09-09 00:37:00", "count": 1}
    # ],

    # 고급 제어 설정
    "enable_db_clean": True,  # False이면 DB 청소 건너뜀
    # "enable_db_clean": False,  # False이면 DB 청소 건너뜀 (candle_db_cleaner 사용 여부)
    "pause_for_verification": False,  # 파편 생성 후 사용자 확인 대기
    "complete_db_table_view": False  # 테스트 후 DB 테이블 전체 보기
}


def get_table_name(symbol: str, timeframe: str) -> str:
    """
    symbol과 timeframe으로 테이블명 생성
    예: KRW-BTC, 1m → candles_KRW_BTC_1m
    """
    return f"candles_{symbol.replace('-', '_')}_{timeframe}"


def parse_time_with_timezone(time_str: str) -> datetime:
    """
    시간대 표준 표현을 포함한 시간 문자열을 UTC datetime으로 변환

    지원 형식:
    - 2025-09-22 12:11:00 KST (한국 표준시)
    - 2025-09-22 12:11:00 JST (일본 표준시, KST와 동일)
    - 2025-09-22 12:11:00 UTC (UTC)
    - 2025-09-22 12:11:00 GMT (그리니치 평균시, UTC와 동일)
    - 2025-09-22 12:11:00 +09:00 (UTC 오프셋)
    - 2025-09-22 12:11:00 +0900 (UTC 오프셋, 콜론 없음)
    - 2025-09-22 12:11:00 (시간대 없음, UTC로 처리)

    Args:
        time_str: 시간 문자열

    Returns:
        datetime: UTC로 변환된 datetime 객체

    Raises:
        ValueError: 지원하지 않는 형식일 때
    """
    time_str = time_str.strip()

    # KST/JST (+9시간) 처리
    if time_str.upper().endswith(' KST') or time_str.upper().endswith(' JST'):
        base_time = time_str[:-4].strip()  # ' KST' 또는 ' JST' 제거
        try:
            local_dt = datetime.strptime(base_time, "%Y-%m-%d %H:%M:%S")
            # KST/JST는 UTC+9이므로 9시간을 빼서 UTC로 변환
            utc_dt = local_dt - timedelta(hours=9)
            return utc_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"KST/JST 시간 형식 오류: '{time_str}' (예: 2025-09-22 12:11:00 KST)")

    # UTC/GMT (변환 불필요) 처리
    elif time_str.upper().endswith(' UTC') or time_str.upper().endswith(' GMT'):
        base_time = time_str[:-4].strip()  # ' UTC' 또는 ' GMT' 제거
        try:
            utc_dt = datetime.strptime(base_time, "%Y-%m-%d %H:%M:%S")
            return utc_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"UTC/GMT 시간 형식 오류: '{time_str}' (예: 2025-09-22 03:11:00 UTC)")

    # UTC 오프셋 (+09:00, +0900, -05:00 등) 처리
    elif '+' in time_str or time_str.count('-') > 2:  # 날짜의 '-' 2개를 초과하면 오프셋
        # +09:00 또는 +0900 형식 찾기
        parts = time_str.split()
        if len(parts) >= 2:
            offset_str = parts[-1]  # 마지막 부분이 오프셋
            base_time = ' '.join(parts[:-1])  # 오프셋을 제외한 시간 부분

            try:
                local_dt = datetime.strptime(base_time, "%Y-%m-%d %H:%M:%S")

                # 오프셋 파싱 (+09:00 또는 +0900)
                if ':' in offset_str:
                    # +09:00 형식
                    sign = 1 if offset_str[0] == '+' else -1
                    hours = int(offset_str[1:3])
                    minutes = int(offset_str[4:6])
                else:
                    # +0900 형식
                    sign = 1 if offset_str[0] == '+' else -1
                    hours = int(offset_str[1:3])
                    minutes = int(offset_str[3:5])

                # UTC로 변환 (로컬 시간 - 오프셋 = UTC)
                offset_delta = timedelta(hours=sign * hours, minutes=sign * minutes)
                utc_dt = local_dt - offset_delta
                return utc_dt.replace(tzinfo=timezone.utc)

            except (ValueError, IndexError):
                raise ValueError(f"UTC 오프셋 형식 오류: '{time_str}' (예: 2025-09-22 12:11:00 +09:00)")
        else:
            raise ValueError(f"UTC 오프셋 형식 오류: '{time_str}' (예: 2025-09-22 12:11:00 +09:00)")

    # 시간대 표기 없음 (기본: UTC로 처리)
    else:
        try:
            utc_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            return utc_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"시간 형식 오류: '{time_str}' (지원 형식: YYYY-MM-DD HH:MM:SS [KST/UTC/+09:00])")


def validate_test_config() -> dict:
    """
    TEST_CONFIG 검증 및 파싱된 시간 반환

    Returns:
        dict: {
            'success': bool,
            'error': str (실패시),
            'start_time': datetime or None,
            'end_time': datetime or None,
            'pattern': str (성공시)
        }
    """
    try:
        # 기본값 추출
        start_time_str = TEST_CONFIG.get('start_time', '').strip()
        end_time_str = TEST_CONFIG.get('end_time', '').strip()
        count = TEST_CONFIG.get('count', 0)

        # 시간 파싱
        start_time = None
        end_time = None

        if start_time_str:
            try:
                start_time = parse_time_with_timezone(start_time_str)
            except ValueError as e:
                return {
                    'success': False,
                    'error': f"start_time 형식 오류 '{start_time_str}': {e}"
                }

        if end_time_str:
            try:
                end_time = parse_time_with_timezone(end_time_str)
            except ValueError as e:
                return {
                    'success': False,
                    'error': f"end_time 형식 오류 '{end_time_str}': {e}"
                }

        # 패턴 결정 및 검증
        pattern = determine_call_pattern(start_time, end_time, count)
        if not pattern:
            return {
                'success': False,
                'error': f"잘못된 파라미터 조합: start_time={start_time_str}, end_time={end_time_str}, count={count}"
            }

        # 시간 순서 검증 (패턴별 다른 규칙)
        if start_time and end_time:
            if pattern == 'to_end':
                # to_end 패턴: to(start_time)가 end(end_time)보다 미래여야 함
                if start_time <= end_time:
                    return {
                        'success': False,
                        'error': f"to_end 패턴에서는 start_time(to)이 end_time보다 미래여야 합니다: {start_time_str} <= {end_time_str}"
                    }
            else:
                # 일반적인 경우: start_time이 end_time보다 과거여야 함
                if start_time > end_time:
                    return {
                        'success': False,
                        'error': f"start_time이 end_time보다 늦습니다: {start_time_str} > {end_time_str}"
                    }

        return {
            'success': True,
            'start_time': start_time,
            'end_time': end_time,
            'pattern': pattern
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"TEST_CONFIG 검증 중 오류: {e}"
        }


def determine_call_pattern(start_time, end_time, count) -> str:
    """
    호출 패턴 결정

    Args:
        start_time: datetime or None
        end_time: datetime or None
        count: int

    Returns:
        str: 'count_only', 'to_count', 'to_end', 'end_only', '' (잘못된 조합)
    """
    has_start = start_time is not None
    has_end = end_time is not None
    has_count = count > 0

    if not has_start and not has_end and has_count:
        return 'count_only'  # 최신부터 count개
    elif has_start and not has_end and has_count:
        return 'to_count'    # start_time부터 과거로 count개
    elif has_start and has_end:
        return 'to_end'      # start_time부터 end_time까지 (count 무시)
    elif not has_start and has_end:
        return 'end_only'    # end_time까지 모든 데이터 (count 무시)
    else:
        return ''            # 잘못된 조합


def build_call_params(pattern: str, symbol: str, timeframe: str, start_time, end_time, count: int) -> dict:
    """
    패턴에 맞는 get_candles 파라미터 구성

    Args:
        pattern: 'count_only', 'to_count', 'to_end', 'end_only'
        symbol: 심볼
        timeframe: 타임프레임
        start_time: datetime or None
        end_time: datetime or None
        count: int

    Returns:
        dict: get_candles에 전달할 파라미터
    """
    base_params = {
        'symbol': symbol,
        'timeframe': timeframe
    }

    if pattern == 'count_only':
        base_params['count'] = count
    elif pattern == 'to_count':
        base_params['count'] = count
        base_params['to'] = start_time
    elif pattern == 'to_end':
        # to_end 패턴: count 파라미터 제외 (구간 수집이므로 count 무시)
        base_params['to'] = start_time
        base_params['end'] = end_time
    elif pattern == 'end_only':
        # end_only 패턴: count 파라미터 제외 (종료시점까지 모든 데이터)
        base_params['end'] = end_time

    return base_params


def format_call_description(pattern: str, params: dict) -> str:
    """호출 패턴별 설명 문자열 생성"""
    symbol = params.get('symbol', '')
    timeframe = params.get('timeframe', '')

    if pattern == 'count_only':
        count = params.get('count', 0)
        return f"📥 get_candles 호출 (최신 {count}개): {symbol} {timeframe}"
    elif pattern == 'to_count':
        count = params.get('count', 0)
        to_str = params.get('to', '').strftime('%Y-%m-%d %H:%M:%S') if params.get('to') else ''
        return f"📥 get_candles 호출 (특정시점부터 {count}개): {symbol} {timeframe}\n    to={to_str} count={count}"
    elif pattern == 'to_end':
        to_str = params.get('to', '').strftime('%Y-%m-%d %H:%M:%S') if params.get('to') else ''
        end_str = params.get('end', '').strftime('%Y-%m-%d %H:%M:%S') if params.get('end') else ''
        return f"📥 get_candles 호출 (구간 수집): {symbol} {timeframe}\n    to={to_str} end={end_str}"
    elif pattern == 'end_only':
        end_str = params.get('end', '').strftime('%Y-%m-%d %H:%M:%S') if params.get('end') else ''
        return f"📥 get_candles 호출 (종료시점까지 모든 데이터): {symbol} {timeframe}\n    end={end_str}"
    else:
        return f"📥 get_candles 호출: {symbol} {timeframe}"


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
        # 0. TEST_CONFIG 검증
        print("🔍 === 오버랩 부분 데이터 테스트 ===")
        print(" 0️⃣ TEST_CONFIG 검증...")

        validation_result = validate_test_config()
        if not validation_result['success']:
            print(f"❌ TEST_CONFIG 검증 실패: {validation_result['error']}")
            return False

        # 검증된 값들 추출
        start_time = validation_result['start_time']
        end_time = validation_result['end_time']
        call_pattern = validation_result['pattern']

        # 테이블명 동적 생성
        table_name = get_table_name(TEST_CONFIG['symbol'], TEST_CONFIG['timeframe'])

        print("✅ TEST_CONFIG 검증 완료")
        print(f"심볼: {TEST_CONFIG['symbol']}")
        print(f"타임프레임: {TEST_CONFIG['timeframe']}")
        print(f"테이블명: {table_name}")
        print(f"호출 패턴: {call_pattern}")
        if start_time:
            print(f"수집 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC)")
        if end_time:
            print(f"수집 종료: {end_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC)")
        if call_pattern in ['count_only', 'to_count']:
            print(f"수집 개수: {TEST_CONFIG['count']}개")
        print(f"청크 크기: {TEST_CONFIG['chunk_size']}개")
        print(f"DB 청소: {'활성화' if TEST_CONFIG.get('enable_db_clean', True) else '비활성화'}")
        print(f"파편 레코드: {len(TEST_CONFIG['partial_records'])}개")
        print("=" * 60)

        # 1. DB 청소 (조건부)
        step_number = 1
        if TEST_CONFIG.get('enable_db_clean', True):
            print(f" {step_number}️⃣ DB 청소...")
            clear_result = self.db_cleaner.clear_candle_table(table_name)
            if not clear_result.get('success', False):
                print(f"❌ DB 청소 실패: {clear_result.get('error')}")
                return False
            print(f"✅ DB 청소 완료 (이전 레코드: {clear_result.get('records_before', 0)}개)")
            step_number += 1
        else:
            print(" 🚫 DB 청소 건너뜀 (enable_db_clean: False)")

        # 2. 파편화 레코드 생성
        print(f" {step_number}️⃣ 파편화 레코드 생성...")
        step_number += 1
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
        print(f" {step_number}️⃣ 파편화 데이터 확인...")
        step_number += 1
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

        # CandleDataProvider 초기화
        print(f" {step_number}️⃣ CandleDataProvider 초기화...")
        if not await self.setup_candle_provider():
            return False
        step_number += 1

        # 캔들 수집 (get_candles 사용)
        print(f" {step_number}️⃣ 캔들 수집 실행...")
        step_number += 1

        # get_candles 호출 파라미터 구성
        try:
            call_params = build_call_params(
                pattern=call_pattern,
                symbol=TEST_CONFIG['symbol'],
                timeframe=TEST_CONFIG['timeframe'],
                start_time=start_time,
                end_time=end_time,
                count=TEST_CONFIG['count']
            )

            # 호출 정보 출력
            call_description = format_call_description(call_pattern, call_params)
            print(f"  {call_description}")

            # ⏱️ 성능 측정 시작
            import time
            start_performance = time.time()

            collected_candles = await self.candle_provider.get_candles(**call_params)

            # ⏱️ 성능 측정 완료
            end_performance = time.time()
            total_duration = end_performance - start_performance
            avg_per_candle = (total_duration / len(collected_candles)) * 1000 if len(collected_candles) > 0 else 0

            print(f"✅ 캔들 수집 완료: {len(collected_candles)}개 수집됨")
            print(f"📊 성능: 총 {total_duration:.1f}초, 캔들당 평균 {avg_per_candle:.2f}ms")

        except Exception as e:
            print(f"❌ 캔들 수집 실패: {e}")
            return False

        # 결과 확인
        print(f" {step_number}️⃣ 결과 확인 및 검증...")

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
        print(f"호출 패턴: {call_pattern}")

        if call_pattern in ['count_only', 'to_count']:
            expected_count = TEST_CONFIG['count']
            print(f"요청 수집: {expected_count}개")
            print(f"실제 반환: {len(collected_candles)}개")

            if len(collected_candles) == expected_count:
                print("✅ 수집 개수 일치")
            else:
                print(f"⚠️ 수집 개수 불일치 (요청: {expected_count}, 실제: {len(collected_candles)})")
        else:
            print(f"수집된 캔들: {len(collected_candles)}개")
            print("ℹ️ 구간/전체 수집 모드 - 개수 비교 불가")

        print(f"파편 레코드: {len(TEST_CONFIG['partial_records'])}개 조각")
        print(f"청크 크기: {TEST_CONFIG['chunk_size']}개")

        # 8. 설정에 따른 DB 테이블 전체 출력 (대용량 테스트 시 생략)
        if TEST_CONFIG["complete_db_table_view"]:
            print(" 📊 === 최종 DB 상태 ===")
            try:
                import sqlite3
                conn = sqlite3.connect('data/market_data.sqlite3')
                cursor = conn.cursor()
                cursor.execute(
                    f'SELECT candle_date_time_utc, candle_date_time_kst, timestamp '
                    f'FROM {table_name} ORDER BY candle_date_time_utc DESC'
                )
                results = cursor.fetchall()
                print(f'=== {TEST_CONFIG["symbol"]} {TEST_CONFIG["timeframe"]} 캔들 데이터 (UTC 시간 내림차순) ===')
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
                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                total_records = cursor.fetchone()[0]

                cursor.execute(
                    f'SELECT MIN(candle_date_time_utc), MAX(candle_date_time_utc) '
                    f'FROM {table_name}'
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
