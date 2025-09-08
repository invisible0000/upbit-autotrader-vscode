"""
테스트 00: 기본 기능 동작 테스트
- DB 초기화
- 2025-09-08T00:00:00 기준 100개 캔들 생성
- 생성된 데이터 확인
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.candle_data_logic.candle_db_cleaner import CandleDBCleaner
from tests.candle_data_logic.candle_db_generator import CandleDBGenerator
from tests.candle_data_logic.candle_db_analyzer import CandleDBAnalyzer
from tests.candle_data_logic.candle_time_utils import CandleTimeUtils


def test_basic_functionality():
    """기본 기능 동작 테스트"""

    print("🧪 === 테스트 00: 기본 기능 동작 테스트 ===")

    # 테스트 설정
    symbol = "KRW-BTC"
    timeframe = "1m"
    start_time = "2025-09-08T00:00:00"
    count = 100

    print(f"심볼: {symbol}, 타임프레임: {timeframe}, 시작: {start_time}, 개수: {count}")

    print("\n📋 테스트 조건:")
    print(f"  - 심볼: {symbol}")
    print(f"  - 타임프레임: {timeframe}")
    print(f"  - 시작 시간: {start_time}")
    print(f"  - 캔들 개수: {count}개")

    # 유틸리티 초기화
    cleaner = CandleDBCleaner()
    generator = CandleDBGenerator()
    analyzer = CandleDBAnalyzer()
    time_utils = CandleTimeUtils()

    try:
        # 1단계: 예상 시간 범위 계산
        print("\n1️⃣ 예상 시간 범위 계산:")
        time_info = time_utils.get_time_info(start_time, count)

        print(f"  최신 캔들: {time_info['start_utc']} (UTC)")
        print(f"  과거 캔들: {time_info['end_utc']} (UTC)")
        print(f"  시간 범위: {time_info['duration_minutes']}분")

        # 2단계: DB 초기화
        print("\n2️⃣ DB 초기화:")
        table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"
        print(f"  테이블: {table_name}")

        result = cleaner.clear_candle_table(table_name)
        if result.get('success', False):
            print("  ✅ DB 초기화 완료")
            print(f"  삭제된 레코드: {result.get('records_before', 0)}개")
        else:
            print("  ❌ DB 초기화 실패")
            print(f"  오류: {result.get('error', '알 수 없는 오류')}")
            return False

        # 3단계: 테스트 데이터 생성
        print("\n3️⃣ 테스트 데이터 생성:")
        print(f"  생성 중... {count}개 캔들")

        result = generator.generate_candle_data(
            start_time=start_time,
            count=count
        )

        if result.get('success', False):
            print("  ✅ 테스트 데이터 생성 완료")
            print(f"  생성된 레코드: {result.get('saved_count', 0)}개")
            print(f"  시간 범위: {result.get('start_time')} ~ {result.get('end_time')}")
        else:
            print("  ❌ 테스트 데이터 생성 실패")
            print(f"  오류: {result.get('error', '알 수 없는 오류')}")
            return False

        # 4단계: 생성된 데이터 분석
        print("\n4️⃣ 생성된 데이터 분석:")
        analysis_result = analyzer.analyze()

        if analysis_result.get('success', False):
            basic_stats = analysis_result.get('basic_stats', {})
            fragments = analysis_result.get('fragments', [])

            print(f"  총 레코드: {basic_stats.get('total_count', 0)}개")
            print(f"  파편 개수: {len(fragments)}개")
            print(f"  시간 범위: {basic_stats.get('start_utc', '없음')} ~ {basic_stats.get('end_utc', '없음')}")
            print(f"  완성도: {basic_stats.get('completeness_percent', 0):.1f}%")
        else:
            print(f"  ❌ 분석 실패: {analysis_result.get('error', '알 수 없는 오류')}")        # 5단계: 수동 검증용 정보 출력
        print("\n5️⃣ 수동 검증용 정보:")
        print("  DB 파일: data/market_data.sqlite3")
        print(f"  테이블명: {table_name}")
        print("  확인 쿼리:")
        print(f"    SELECT COUNT(*) FROM {table_name};")
        print(f"    SELECT candle_date_time_utc FROM {table_name} ORDER BY candle_date_time_utc DESC LIMIT 5;")
        print(f"    SELECT candle_date_time_utc FROM {table_name} ORDER BY candle_date_time_utc ASC LIMIT 5;")

        return True

    except Exception as e:
        print("\n❌ 테스트 실행 중 오류 발생:")
        print(f"  오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_time_calculation():
    """시간 계산 검증 (추가 확인용)"""

    print(f"\n🔍 === 시간 계산 검증 ===")

    utils = CandleTimeUtils()
    start_time = "2025-09-08T00:00:00"
    count = 100

    # 계산 결과
    time_info = utils.get_time_info(start_time, count)

    print(f"계산 결과:")
    print(f"  시작: {time_info['start_utc']}")
    print(f"  종료: {time_info['end_utc']}")
    print(f"  기간: {time_info['duration_minutes']}분")

    # 수동 검증
    print(f"\n수동 검증:")
    print(f"  1번째 캔들: {start_time}")
    print(f"  2번째 캔들: {utils.add_minutes(start_time, -1)}")
    print(f"  3번째 캔들: {utils.add_minutes(start_time, -2)}")
    print(f"  100번째 캔들: {utils.add_minutes(start_time, -99)}")

    # 계산 검증
    manual_end = utils.add_minutes(start_time, -99)
    print(f"\n검증:")
    print(f"  계산된 종료: {time_info['end_utc']}")
    print(f"  수동 계산:   {manual_end}")
    print(f"  일치 여부:   {'✅ 일치' if time_info['end_utc'] == manual_end else '❌ 불일치'}")


def main():
    """메인 실행 함수"""
    print("🚀 캔들 테스트 00 - 기본 기능 동작 테스트 시작")

    # 시간 계산 검증
    verify_time_calculation()

    # 기본 기능 테스트
    success = test_basic_functionality()

    if success:
        print("\n✅ 테스트 00 완료 - 성공")
        print("이제 DB를 열어서 생성된 데이터를 확인하세요!")
    else:
        print("\n❌ 테스트 00 완료 - 실패")

    return success


if __name__ == "__main__":
    main()
