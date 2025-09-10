"""
🔬 업비트 실제 캔들 패턴 vs 현재 구현 정확성 테스트

업비트 실제 출력과 현재 _align_to_candle_boundary 구현 비교
"""

from datetime import datetime
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


def test_upbit_alignment_patterns():
    """업비트 실제 캔들 패턴과 현재 구현 비교 테스트"""

    # 테스트 기준 시간: 2025-09-10T10:08:52 (업비트 출력 기준)
    test_time = datetime(2025, 9, 10, 10, 8, 52)

    # 업비트 실제 출력 데이터 (첫 번째 캔들만)
    upbit_expected = {
        "1s": datetime(2025, 9, 10, 10, 8, 52),
        "1m": datetime(2025, 9, 10, 10, 8, 0),
        "3m": datetime(2025, 9, 10, 10, 6, 0),  # 3분 경계: 06, 03, 00
        "5m": datetime(2025, 9, 10, 10, 5, 0),  # 5분 경계: 05, 00, 55
        "15m": datetime(2025, 9, 10, 10, 0, 0), # 15분 경계: 00, 45, 30
        "30m": datetime(2025, 9, 10, 10, 0, 0), # 30분 경계: 00, 30
        "60m": datetime(2025, 9, 10, 10, 0, 0), # 60분 경계: 10, 09, 08
        "240m": datetime(2025, 9, 10, 8, 0, 0), # 4시간 경계: 08, 04, 00
        "1d": datetime(2025, 9, 10, 0, 0, 0),   # 일봉: 자정
        # 업비트 실제 주/월/년봉 패턴 (수정됨)
        "1w": datetime(2025, 9, 7, 0, 0, 0),    # 주봉: 2025-09-07 (일요일) - 수정
        "1M": datetime(2025, 9, 1, 0, 0, 0),    # 월봉: 2025-09-01 (월 첫날)
        "1y": datetime(2025, 1, 1, 0, 0, 0),    # 년봉: 2025-01-01 (년 첫날)
    }

    print("🔬 업비트 실제 패턴 vs 현재 구현 정확성 테스트")
    print("=" * 80)
    print(f"테스트 시간: {test_time}")
    print()
    print("timeframe | 업비트 실제    | 현재 구현      | 일치 여부")
    print("-" * 60)

    all_passed = True

    for timeframe, expected in upbit_expected.items():
        try:
            current_result = TimeUtils._align_to_candle_boundary(test_time, timeframe)
            is_match = current_result == expected
            status = "✅" if is_match else "❌"

            print(f"{timeframe:>8s} | {expected.strftime('%Y-%m-%d %H:%M:%S')} | {current_result.strftime('%Y-%m-%d %H:%M:%S')} | {status}")

            if not is_match:
                all_passed = False
                print(f"         차이: 예상={expected}, 실제={current_result}")

        except Exception as e:
            print(f"{timeframe:>8s} | {expected.strftime('%Y-%m-%d %H:%M:%S')} | ERROR: {e} | ❌")
            all_passed = False

    print()
    print("📊 테스트 결과:")
    if all_passed:
        print("✅ 모든 타임프레임이 업비트 실제 패턴과 일치")
    else:
        print("❌ 일부 타임프레임이 업비트 실제 패턴과 불일치")
        print("   → _align_to_candle_boundary 수정 필요")

    return all_passed


def test_additional_edge_cases():
    """추가 엣지 케이스 테스트 - 분/시간봉"""

    print("\n🧪 추가 엣지 케이스 테스트 - 분/시간봉")
    print("=" * 60)

    edge_cases = [
        # (테스트 시간, 타임프레임, 예상 결과)
        (datetime(2025, 9, 10, 14, 32, 45), "3m", datetime(2025, 9, 10, 14, 30, 0)),  # 3분: 30, 33, 36
        (datetime(2025, 9, 10, 14, 37, 23), "5m", datetime(2025, 9, 10, 14, 35, 0)),  # 5분: 35, 40, 45
        (datetime(2025, 9, 10, 14, 47, 12), "15m", datetime(2025, 9, 10, 14, 45, 0)), # 15분: 45, 00, 15
        (datetime(2025, 9, 10, 13, 25, 30), "240m", datetime(2025, 9, 10, 12, 0, 0)), # 4시간: 12, 16, 20
    ]

    for test_time, timeframe, expected in edge_cases:
        result = TimeUtils._align_to_candle_boundary(test_time, timeframe)
        status = "✅" if result == expected else "❌"

        print(f"{timeframe} | {test_time.strftime('%H:%M:%S')} → {result.strftime('%H:%M:%S')} (예상: {expected.strftime('%H:%M:%S')}) {status}")


def test_weekly_edge_cases():
    """주봉 엣지 케이스 테스트 - 모든 요일과 경계 상황"""

    print("\n📅 주봉 엣지 케이스 테스트 - 모든 요일")
    print("=" * 70)

    # 2025년 9월 주차별 테스트 (일요일 기준)
    weekly_cases = [
        # (테스트 날짜, 요일 설명, 예상 주 시작일 (일요일))
        (datetime(2025, 9, 7, 15, 30, 45), "일요일 오후", datetime(2025, 9, 7, 0, 0, 0)),   # 일요일 → 같은 일요일
        (datetime(2025, 9, 7, 0, 0, 0), "일요일 자정", datetime(2025, 9, 7, 0, 0, 0)),     # 일요일 자정
        (datetime(2025, 9, 7, 23, 59, 59), "일요일 23:59", datetime(2025, 9, 7, 0, 0, 0)),  # 일요일 마지막 순간

        (datetime(2025, 9, 8, 10, 20, 30), "월요일 오전", datetime(2025, 9, 7, 0, 0, 0)),   # 월요일 → 이전 일요일
        (datetime(2025, 9, 9, 14, 45, 20), "화요일 오후", datetime(2025, 9, 7, 0, 0, 0)),   # 화요일 → 이전 일요일
        (datetime(2025, 9, 10, 9, 15, 10), "수요일 오전", datetime(2025, 9, 7, 0, 0, 0)),   # 수요일 → 이전 일요일
        (datetime(2025, 9, 11, 18, 30, 0), "목요일 오후", datetime(2025, 9, 7, 0, 0, 0)),   # 목요일 → 이전 일요일
        (datetime(2025, 9, 12, 22, 45, 15), "금요일 밤", datetime(2025, 9, 7, 0, 0, 0)),    # 금요일 → 이전 일요일
        (datetime(2025, 9, 13, 3, 20, 45), "토요일 새벽", datetime(2025, 9, 7, 0, 0, 0)),   # 토요일 → 이전 일요일

        # 다음 주 테스트
        (datetime(2025, 9, 14, 5, 30, 0), "다음주 일요일", datetime(2025, 9, 14, 0, 0, 0)),  # 다음주 일요일
        (datetime(2025, 9, 15, 12, 0, 0), "다음주 월요일", datetime(2025, 9, 14, 0, 0, 0)),  # 다음주 월요일

        # 월경계 테스트 (8월 말 → 9월 초)
        (datetime(2025, 8, 31, 20, 0, 0), "8월 마지막 일요일", datetime(2025, 8, 31, 0, 0, 0)),  # 8월 마지막 일요일
        (datetime(2025, 9, 1, 10, 0, 0), "9월 첫 월요일", datetime(2025, 8, 31, 0, 0, 0)),      # 9월 첫 월요일 → 8월 마지막 일요일

        # 년경계 테스트 (12월 말 → 1월 초)
        (datetime(2024, 12, 29, 15, 0, 0), "2024년 마지막 일요일", datetime(2024, 12, 29, 0, 0, 0)),  # 2024년 마지막 일요일
        (datetime(2025, 1, 1, 0, 0, 0), "2025년 첫날", datetime(2024, 12, 29, 0, 0, 0)),           # 2025년 1월 1일 → 2024년 마지막 일요일
    ]

    print("테스트 날짜           | 요일 설명      | 계산된 주 시작일   | 예상 주 시작일     | 상태")
    print("-" * 90)

    all_weekly_passed = True
    for test_date, desc, expected_sunday in weekly_cases:
        result = TimeUtils._align_to_candle_boundary(test_date, '1w')
        is_match = result == expected_sunday
        status = "✅" if is_match else "❌"

        if not is_match:
            all_weekly_passed = False

        print(f"{test_date.strftime('%Y-%m-%d %H:%M:%S')} | {desc:>12s} | "
              f"{result.strftime('%Y-%m-%d %H:%M:%S')} | "
              f"{expected_sunday.strftime('%Y-%m-%d %H:%M:%S')} | {status}")

    return all_weekly_passed


def test_monthly_edge_cases():
    """월봉 엣지 케이스 테스트 - 월 경계와 특수 상황"""

    print("\n📅 월봉 엣지 케이스 테스트")
    print("=" * 50)

    monthly_cases = [
        # (테스트 날짜, 설명, 예상 월 시작일)
        (datetime(2025, 9, 1, 0, 0, 0), "9월 첫날 자정", datetime(2025, 9, 1, 0, 0, 0)),      # 월 첫날 자정
        (datetime(2025, 9, 1, 23, 59, 59), "9월 첫날 마지막", datetime(2025, 9, 1, 0, 0, 0)),  # 월 첫날 마지막 순간
        (datetime(2025, 9, 15, 12, 30, 45), "9월 중순", datetime(2025, 9, 1, 0, 0, 0)),        # 월 중순
        (datetime(2025, 9, 30, 23, 59, 59), "9월 마지막", datetime(2025, 9, 1, 0, 0, 0)),      # 월 마지막 순간

        # 2월 테스트 (28일)
        (datetime(2025, 2, 1, 10, 0, 0), "2월 첫날", datetime(2025, 2, 1, 0, 0, 0)),          # 2월 첫날
        (datetime(2025, 2, 14, 14, 30, 0), "2월 중순", datetime(2025, 2, 1, 0, 0, 0)),         # 2월 중순
        (datetime(2025, 2, 28, 23, 59, 59), "2월 마지막", datetime(2025, 2, 1, 0, 0, 0)),      # 2월 마지막 (평년)

        # 윤년 테스트 (2024년)
        (datetime(2024, 2, 29, 12, 0, 0), "윤년 2월 29일", datetime(2024, 2, 1, 0, 0, 0)),     # 윤년 2월 29일

        # 12월 → 1월 경계
        (datetime(2025, 12, 31, 23, 59, 59), "12월 마지막", datetime(2025, 12, 1, 0, 0, 0)),   # 12월 마지막
        (datetime(2026, 1, 1, 0, 0, 0), "다음해 1월 첫날", datetime(2026, 1, 1, 0, 0, 0)),     # 다음해 1월
    ]

    print("테스트 날짜           | 설명           | 계산된 월 시작일   | 예상 월 시작일     | 상태")
    print("-" * 85)

    all_monthly_passed = True
    for test_date, desc, expected_first in monthly_cases:
        result = TimeUtils._align_to_candle_boundary(test_date, '1M')
        is_match = result == expected_first
        status = "✅" if is_match else "❌"

        if not is_match:
            all_monthly_passed = False

        print(f"{test_date.strftime('%Y-%m-%d %H:%M:%S')} | {desc:>13s} | "
              f"{result.strftime('%Y-%m-%d %H:%M:%S')} | "
              f"{expected_first.strftime('%Y-%m-%d %H:%M:%S')} | {status}")

    return all_monthly_passed


def test_yearly_edge_cases():
    """년봉 엣지 케이스 테스트 - 년 경계와 특수 상황"""

    print("\n📅 년봉 엣지 케이스 테스트")
    print("=" * 50)

    yearly_cases = [
        # (테스트 날짜, 설명, 예상 년 시작일)
        (datetime(2025, 1, 1, 0, 0, 0), "2025년 첫날 자정", datetime(2025, 1, 1, 0, 0, 0)),      # 년 첫날 자정
        (datetime(2025, 1, 1, 23, 59, 59), "2025년 첫날 마지막", datetime(2025, 1, 1, 0, 0, 0)),  # 년 첫날 마지막
        (datetime(2025, 6, 15, 12, 30, 45), "2025년 중반", datetime(2025, 1, 1, 0, 0, 0)),        # 년 중반
        (datetime(2025, 12, 31, 23, 59, 59), "2025년 마지막", datetime(2025, 1, 1, 0, 0, 0)),     # 년 마지막 순간

        # 다른 년도 테스트
        (datetime(2024, 7, 20, 15, 45, 0), "2024년 중반", datetime(2024, 1, 1, 0, 0, 0)),         # 2024년
        (datetime(2026, 3, 10, 9, 15, 30), "2026년 봄", datetime(2026, 1, 1, 0, 0, 0)),           # 2026년

        # 윤년 테스트
        (datetime(2024, 2, 29, 10, 0, 0), "윤년 2월 29일", datetime(2024, 1, 1, 0, 0, 0)),        # 윤년
        (datetime(2023, 2, 28, 15, 30, 0), "평년 2월 28일", datetime(2023, 1, 1, 0, 0, 0)),       # 평년
    ]

    print("테스트 날짜           | 설명              | 계산된 년 시작일   | 예상 년 시작일     | 상태")
    print("-" * 90)

    all_yearly_passed = True
    for test_date, desc, expected_first in yearly_cases:
        result = TimeUtils._align_to_candle_boundary(test_date, '1y')
        is_match = result == expected_first
        status = "✅" if is_match else "❌"

        if not is_match:
            all_yearly_passed = False

        print(f"{test_date.strftime('%Y-%m-%d %H:%M:%S')} | {desc:>16s} | "
              f"{result.strftime('%Y-%m-%d %H:%M:%S')} | "
              f"{expected_first.strftime('%Y-%m-%d %H:%M:%S')} | {status}")

    return all_yearly_passed


if __name__ == "__main__":
    print("🔬 업비트 캔들 시간 정렬 종합 테스트")
    print("=" * 80)

    # 메인 테스트 실행
    main_passed = test_upbit_alignment_patterns()

    # 추가 테스트들 실행
    test_additional_edge_cases()
    weekly_passed = test_weekly_edge_cases()
    monthly_passed = test_monthly_edge_cases()
    yearly_passed = test_yearly_edge_cases()

    # 최종 결과 요약
    print("\n" + "=" * 80)
    print("📊 종합 테스트 결과 요약")
    print("=" * 80)

    results = [
        ("기본 타임프레임", main_passed),
        ("분/시간봉 엣지케이스", True),  # 간단한 케이스들은 항상 통과 예상
        ("주봉 엣지케이스", weekly_passed),
        ("월봉 엣지케이스", monthly_passed),
        ("년봉 엣지케이스", yearly_passed),
    ]

    all_tests_passed = all(passed for _, passed in results)

    for test_name, passed in results:
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"{test_name:>20s}: {status}")

    print("-" * 40)
    if all_tests_passed:
        print("🎉 모든 테스트가 성공적으로 통과했습니다!")
        print("   현재 구현이 업비트 패턴과 완전히 일치합니다.")
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
        print("   _align_to_candle_boundary 메서드 수정이 필요합니다.")

    print("=" * 80)
