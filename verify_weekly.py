"""
주봉 테스트 케이스 수정 및 재검증
"""

from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(__file__))

from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


def verify_weekly_test_cases():
    """주봉 테스트 케이스 재검증"""
    print("=== 주봉 테스트 케이스 재검증 ===")

    # 원래 테스트 케이스들
    test_cases = [
        # 2025년 9월 11일 = 목요일 (weekday=3)
        # 해당 주 일요일 = 2025년 9월 7일 (올바름)
        (datetime(2025, 9, 11, 14, 32, 30), datetime(2025, 9, 7, 0, 0, 0)),   # 목요일 → 일요일

        # 2025년 9월 8일 = 월요일 (weekday=0)
        # 해당 주 일요일 = 2025년 9월 7일 (올바름)
        (datetime(2025, 9, 8, 14, 32, 30), datetime(2025, 9, 7, 0, 0, 0)),    # 월요일 → 일요일

        # 2025년 9월 7일 = 일요일 (weekday=6)
        # 해당 주 일요일 = 2025년 9월 7일 (올바름) - 원래 테스트는 9월 1일로 잘못 설정
        (datetime(2025, 9, 7, 14, 32, 30), datetime(2025, 9, 7, 0, 0, 0)),    # 일요일 → 일요일
    ]

    weekday_names = ['월', '화', '수', '목', '금', '토', '일']

    for dt, expected in test_cases:
        result = TimeUtils._align_to_candle_boundary(dt, "1w")
        status = '✓' if result == expected else '✗'
        dt_weekday = weekday_names[dt.weekday()]
        result_weekday = weekday_names[result.weekday()]

        print(f"1w: {dt}({dt_weekday}) → {result}({result_weekday}) (예상: {expected}) {status}")

    print()


def comprehensive_weekly_test():
    """종합적인 주봉 테스트"""
    print("=== 종합적인 주봉 테스트 ===")

    # 여러 달의 다양한 날짜들로 테스트
    test_dates = [
        # 2025년 1월 (1월 1일 = 수요일)
        (datetime(2025, 1, 1), datetime(2024, 12, 29)),   # 수요일 → 전년 12월 29일(일)
        (datetime(2025, 1, 5), datetime(2025, 1, 5)),     # 일요일 → 1월 5일(일)

        # 2025년 2월 (2월 1일 = 토요일)
        (datetime(2025, 2, 1), datetime(2025, 1, 26)),    # 토요일 → 1월 26일(일)
        (datetime(2025, 2, 2), datetime(2025, 2, 2)),     # 일요일 → 2월 2일(일)

        # 2025년 12월 (연말)
        (datetime(2025, 12, 31), datetime(2025, 12, 28)), # 12월 31일(수) → 12월 28일(일)
    ]

    weekday_names = ['월', '화', '수', '목', '금', '토', '일']

    for dt, expected in test_dates:
        result = TimeUtils._align_to_candle_boundary(dt, "1w")
        status = '✓' if result.date() == expected.date() else '✗'
        dt_weekday = weekday_names[dt.weekday()]
        result_weekday = weekday_names[result.weekday()]

        print(f"{dt.strftime('%Y-%m-%d')}({dt_weekday}) → "
              f"{result.strftime('%Y-%m-%d')}({result_weekday}) "
              f"(예상: {expected.strftime('%Y-%m-%d')}) {status}")

    print()


def edge_case_weekly_test():
    """주봉 엣지 케이스 테스트"""
    print("=== 주봉 엣지 케이스 테스트 ===")

    # 윤년 테스트
    leap_year_cases = [
        (datetime(2024, 2, 29), datetime(2024, 2, 25)),   # 윤년 2월 29일(목) → 2월 25일(일)
        (datetime(2024, 3, 1), datetime(2024, 2, 25)),    # 윤년 다음날 3월 1일(금) → 2월 25일(일)
    ]

    # 연도 경계 테스트
    year_boundary_cases = [
        (datetime(2024, 12, 31), datetime(2024, 12, 29)), # 2024년 마지막날(화) → 12월 29일(일)
        (datetime(2025, 1, 1), datetime(2024, 12, 29)),   # 2025년 첫날(수) → 2024년 12월 29일(일)
    ]

    all_cases = leap_year_cases + year_boundary_cases
    weekday_names = ['월', '화', '수', '목', '금', '토', '일']

    for dt, expected in all_cases:
        result = TimeUtils._align_to_candle_boundary(dt, "1w")
        status = '✓' if result.date() == expected.date() else '✗'
        dt_weekday = weekday_names[dt.weekday()]
        result_weekday = weekday_names[result.weekday()]

        print(f"{dt.strftime('%Y-%m-%d')}({dt_weekday}) → "
              f"{result.strftime('%Y-%m-%d')}({result_weekday}) "
              f"(예상: {expected.strftime('%Y-%m-%d')}) {status}")

    print()


if __name__ == "__main__":
    verify_weekly_test_cases()
    comprehensive_weekly_test()
    edge_case_weekly_test()
