"""
업비트 API 정렬 방식 검증 테스트

실제 업비트 API 응답과 _align_to_candle_boundary 내림 정렬 결과 비교
"""

import sys
import os
import requests
from datetime import datetime, timezone
import json

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


def fetch_upbit_candle(market="KRW-BTC", timeframe="1", to_time="2025-09-07T00:00:30Z", count=1):
    """
    업비트 API에서 캔들 데이터 조회

    Args:
        market: 마켓 코드 (KRW-BTC)
        timeframe: 타임프레임 (1분봉)
        to_time: 기준 시간 (ISO 형식)
        count: 조회할 캔들 수

    Returns:
        API 응답 JSON 데이터
    """
    url = f"https://api.upbit.com/v1/candles/minutes/{timeframe}"

    params = {
        "market": market,
        "to": to_time,
        "count": count
    }

    print("🌐 업비트 API 요청")
    print("   URL: {}".format(url))
    print("   파라미터: {}".format(params))

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        print("✅ API 응답 성공: {}개 캔들 수신".format(len(data)))

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ API 요청 실패: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")
        return None


def test_upbit_alignment_comparison():
    """업비트 API vs 내림 정렬 비교 테스트"""

    print("🧪 업비트 API 정렬 방식 검증 테스트")
    print("=" * 80)

    # 테스트 시간: 2025-09-07 00:00:30 (30초)
    test_time_str = "2025-09-07T00:00:30Z"
    test_time = datetime(2025, 9, 7, 0, 0, 30, 0, timezone.utc)

    print(f"📅 테스트 기준 시간: {test_time} ({test_time_str})")
    print()

    # 1. 우리의 내림 정렬 결과
    print("🔧 우리의 내림 정렬 결과:")
    try:
        aligned_time = TimeUtils._align_to_candle_boundary(test_time, "1m")
        print(f"   입력: {test_time}")
        print(f"   정렬: {aligned_time}")
        print(f"   변화: {(test_time - aligned_time).total_seconds()}초")
    except Exception as e:
        print(f"   ❌ 정렬 실패: {e}")
        return False

    print()

    # 2. 업비트 API 응답
    print("🌐 업비트 API 응답:")
    api_data = fetch_upbit_candle(
        market="KRW-BTC",
        timeframe="1",
        to_time=test_time_str,
        count=1
    )

    if not api_data:
        print("❌ API 데이터를 가져올 수 없어서 비교를 중단합니다.")
        return False

    if len(api_data) == 0:
        print("❌ API에서 캔들 데이터가 없습니다.")
        return False

    # API 응답 분석
    candle = api_data[0]
    api_candle_time_utc = candle.get("candle_date_time_utc")
    api_candle_time_kst = candle.get("candle_date_time_kst")

    print(f"   API 캔들 시간 (UTC): {api_candle_time_utc}")
    print(f"   API 캔들 시간 (KST): {api_candle_time_kst}")

    # UTC 시간을 datetime 객체로 변환
    try:
        # ISO 형식 파싱 (Z 또는 +00:00 처리)
        if api_candle_time_utc.endswith('Z'):
            api_datetime = datetime.fromisoformat(api_candle_time_utc[:-1] + '+00:00')
        else:
            api_datetime = datetime.fromisoformat(api_candle_time_utc)

        # timezone 정보 확실히 UTC로 설정
        if api_datetime.tzinfo is None:
            api_datetime = api_datetime.replace(tzinfo=timezone.utc)

        print(f"   파싱된 API 시간: {api_datetime}")
        print(f"   API 시간 timezone: {api_datetime.tzinfo}")

    except Exception as e:
        print(f"   ❌ API 시간 파싱 실패: {e}")
        return False

    print()

    # 3. 비교 분석
    print("🔍 비교 분석:")
    print("-" * 50)

    # timezone 정보 확인 및 디버깅
    print(f"   우리 정렬 timezone: {aligned_time.tzinfo}")
    print(f"   API 시간 timezone: {api_datetime.tzinfo}")

    time_match = (aligned_time == api_datetime)
    time_diff = (aligned_time - api_datetime).total_seconds()

    print(f"   우리 정렬 결과: {aligned_time}")
    print(f"   업비트 API 시간: {api_datetime}")
    print(f"   시간 일치 여부: {time_match}")
    print(f"   시간 차이: {time_diff:+.1f}초")

    if time_match:
        print("✅ 완벽 일치! 우리의 내림 정렬이 업비트와 동일합니다.")
        result_status = "SUCCESS"
    else:
        print("❌ 불일치 발견!")
        if time_diff > 0:
            print("   → 우리가 더 미래 시간 (올림이 필요할 수 있음)")
        else:
            print("   → 우리가 더 과거 시간 (내림이 맞는 것 같음)")
        result_status = "MISMATCH"

    print()

    # 4. 추가 검증: 여러 시간대 테스트
    print("🔄 추가 검증: 다양한 초 값 테스트")
    print("-" * 50)

    test_cases = [
        "2025-09-07T00:00:00Z",  # 정각
        "2025-09-07T00:00:15Z",  # 15초
        "2025-09-07T00:00:30Z",  # 30초
        "2025-09-07T00:00:45Z",  # 45초
        "2025-09-07T00:00:59Z",  # 59초
    ]

    match_count = 0
    total_count = len(test_cases)

    for test_case in test_cases:
        try:
            # 시간 파싱
            test_dt = datetime.fromisoformat(test_case[:-1] + '+00:00')

            # 우리의 정렬
            our_aligned = TimeUtils._align_to_candle_boundary(test_dt, "1m")

            # API 요청 (간단히 하기 위해 첫 번째만 상세 비교)
            if test_case == test_cases[0]:  # 첫 번째만 실제 API 호출
                api_result = fetch_upbit_candle("KRW-BTC", "1", test_case, 1)
                if api_result and len(api_result) > 0:
                    api_time_str = api_result[0]["candle_date_time_utc"]
                    if api_time_str.endswith('Z'):
                        api_dt = datetime.fromisoformat(api_time_str[:-1] + '+00:00')
                    else:
                        api_dt = datetime.fromisoformat(api_time_str)

                    match = (our_aligned == api_dt)
                    if match:
                        match_count += 1

                    print(f"   {test_case}: 우리={our_aligned.strftime('%H:%M:%S')}, API={api_dt.strftime('%H:%M:%S')}, 일치={match}")
                else:
                    print(f"   {test_case}: API 응답 없음")
            else:
                # 나머지는 우리의 정렬 결과만 표시
                print(f"   {test_case}: 우리={our_aligned.strftime('%H:%M:%S')} (API 미확인)")

        except Exception as e:
            print(f"   {test_case}: 에러 - {e}")

    print()
    print("=" * 80)
    print(f"📊 최종 결과: {result_status}")

    if result_status == "SUCCESS":
        print("✅ 우리의 내림 정렬 방식이 업비트 API와 일치합니다!")
        print("   → 현재 구현이 올바름")
    else:
        print("❌ 불일치가 발견되었습니다.")
        print("   → 정렬 방식 재검토 필요 (올림 vs 내림)")

    return result_status == "SUCCESS"


if __name__ == "__main__":
    success = test_upbit_alignment_comparison()

    print(f"\n🏁 테스트 {'성공' if success else '실패'}!")
