"""
업비트 API 정렬 방식 검증 테스트

실제 업비트 API 응답과 align_to_candle_boundary 내림 정렬 결과 비교
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

    # 현재 시간에서 1시간 전으로 테스트 (확실히 거래가 있었던 시간)
    import datetime as dt
    now = dt.datetime.now(timezone.utc)
    test_time = now.replace(minute=32, second=30, microsecond=0) - dt.timedelta(hours=2)
    test_time_str = test_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    print(f"📅 테스트 기준 시간: {test_time} ({test_time_str})")
    print()

    # 1. 우리의 내림 정렬 결과
    print("🔧 우리의 내림 정렬 결과:")
    try:
        aligned_time = TimeUtils.align_to_candle_boundary(test_time, "1m")
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

    # 4. 추가 검증: 여러 시간대 테스트 (모든 케이스에서 업비트 API 요청)
    print("🔄 추가 검증: 다양한 초 값 테스트 (모든 케이스 업비트 API 요청)")
    print("-" * 50)

    # 현재 시간 기준으로 다양한 초 값 테스트
    base_time = now - dt.timedelta(hours=1)  # 1시간 전
    test_cases = [
        base_time.replace(second=0).strftime('%Y-%m-%dT%H:%M:%SZ'),   # 정각
        base_time.replace(second=15).strftime('%Y-%m-%dT%H:%M:%SZ'),  # 15초
        base_time.replace(second=30).strftime('%Y-%m-%dT%H:%M:%SZ'),  # 30초
        base_time.replace(second=45).strftime('%Y-%m-%dT%H:%M:%SZ'),  # 45초
        base_time.replace(second=59).strftime('%Y-%m-%dT%H:%M:%SZ'),  # 59초
    ]

    match_count = 0
    total_count = len(test_cases)

    for i, test_case in enumerate(test_cases):
        try:
            print(f"\n   📋 테스트 케이스 {i + 1}/{total_count}: {test_case}")

            # 시간 파싱
            test_dt = datetime.fromisoformat(test_case[:-1] + '+00:00')

            # 우리의 정렬
            our_aligned = TimeUtils.align_to_candle_boundary(test_dt, "1m")

            # 모든 케이스에서 업비트 API 요청
            print("      🌐 업비트 API 요청 중...")
            api_result = fetch_upbit_candle("KRW-BTC", "1", test_case, 1)

            if api_result and len(api_result) > 0:
                api_time_str = api_result[0]["candle_date_time_utc"]
                if api_time_str.endswith('Z'):
                    api_dt = datetime.fromisoformat(api_time_str[:-1] + '+00:00')
                else:
                    api_dt = datetime.fromisoformat(api_time_str)

                # timezone 정보가 없으면 UTC로 설정
                if api_dt.tzinfo is None:
                    api_dt = api_dt.replace(tzinfo=timezone.utc)

                match = (our_aligned == api_dt)
                if match:
                    match_count += 1

                time_diff = (our_aligned - api_dt).total_seconds()
                status_icon = "✅" if match else "❌"

                # 업비트 원본 응답 형식과 동일하게 우리 시간 변환
                our_time_str = our_aligned.strftime('%Y-%m-%dT%H:%M:%S')

                print(f"      입력: {test_case}")
                print(f"      우리: {our_time_str}")
                print(f"      API:  {api_time_str}")
                print(f"      일치: {status_icon} (차이: {time_diff:+.1f}초)")

            else:
                print("      ❌ API 응답 없음 또는 데이터 없음")

        except Exception as e:
            print(f"      ❌ 에러: {e}")

    print(f"\n   📊 1분봉 테스트 결과: {match_count}/{total_count}개 일치")

    # 5. 다양한 타임프레임 테스트 (업비트 API 요청)
    print("\n🔄 다양한 타임프레임 테스트 (모든 케이스 업비트 API 요청)")
    print("-" * 50)

    # 현재 시간 기준으로 타임프레임별 테스트
    tf_base = now - dt.timedelta(hours=2)  # 2시간 전
    timeframe_tests = [
        ("3", "3m", tf_base.replace(minute=2, second=30).strftime('%Y-%m-%dT%H:%M:%SZ')),    # 3분봉: 2분30초 → 0분
        ("5", "5m", tf_base.replace(minute=7, second=45).strftime('%Y-%m-%dT%H:%M:%SZ')),    # 5분봉: 7분45초 → 5분
        ("15", "15m", tf_base.replace(minute=12, second=30).strftime('%Y-%m-%dT%H:%M:%SZ')),  # 15분봉: 12분30초 → 0분
        ("30", "30m", tf_base.replace(minute=25, second=30).strftime('%Y-%m-%dT%H:%M:%SZ')),  # 30분봉: 25분30초 → 0분
    ]

    timeframe_match_count = 0
    timeframe_total = len(timeframe_tests)

    for tf_api, tf_utils, test_time_str in timeframe_tests:
        try:
            print(f"\n   📋 {tf_utils} 타임프레임 테스트: {test_time_str}")

            # 시간 파싱
            test_dt = datetime.fromisoformat(test_time_str[:-1] + '+00:00')

            # 우리의 정렬
            our_aligned = TimeUtils.align_to_candle_boundary(test_dt, tf_utils)

            # 업비트 API 요청
            print("      🌐 업비트 API 요청 중...")
            api_result = fetch_upbit_candle("KRW-BTC", tf_api, test_time_str, 1)

            if api_result and len(api_result) > 0:
                api_time_str = api_result[0]["candle_date_time_utc"]
                if api_time_str.endswith('Z'):
                    api_dt = datetime.fromisoformat(api_time_str[:-1] + '+00:00')
                else:
                    api_dt = datetime.fromisoformat(api_time_str)

                # timezone 정보가 없으면 UTC로 설정
                if api_dt.tzinfo is None:
                    api_dt = api_dt.replace(tzinfo=timezone.utc)

                match = (our_aligned == api_dt)
                if match:
                    timeframe_match_count += 1

                time_diff = (our_aligned - api_dt).total_seconds()
                status_icon = "✅" if match else "❌"

                # 업비트 원본 응답 형식과 동일하게 우리 시간 변환
                our_time_str = our_aligned.strftime('%Y-%m-%dT%H:%M:%S')

                print(f"      입력: {test_time_str}")
                print(f"      우리: {our_time_str}")
                print(f"      API:  {api_time_str}")
                print(f"      일치: {status_icon} (차이: {time_diff:+.1f}초)")

            else:
                print("      ❌ API 응답 없음 또는 데이터 없음")

        except Exception as e:
            print(f"      ❌ 에러: {e}")

    print(f"\n   📊 다양한 타임프레임 테스트 결과: {timeframe_match_count}/{timeframe_total}개 일치")

    # 전체 결과 계산
    total_tests = total_count + timeframe_total
    total_matches = match_count + timeframe_match_count

    print()
    print("=" * 80)
    print(f"📊 최종 결과: {result_status}")
    print(f"🎯 전체 일치율: {total_matches}/{total_tests}개 ({total_matches / total_tests * 100:.1f}%)")

    if result_status == "SUCCESS" and total_matches == total_tests:
        print("✅ 우리의 내림 정렬 방식이 업비트 API와 완벽히 일치합니다!")
        print("   → 현재 구현이 올바름")
        final_success = True
    elif total_matches >= total_tests * 0.8:  # 80% 이상 일치
        print("⚠️  대부분 일치하지만 일부 불일치가 있습니다.")
        print("   → 추가 검토 필요")
        final_success = False
    else:
        print("❌ 상당한 불일치가 발견되었습니다.")
        print("   → 정렬 방식 재검토 필요 (올림 vs 내림)")
        final_success = False

    return final_success


if __name__ == "__main__":
    success = test_upbit_alignment_comparison()

    print(f"\n🏁 테스트 {'성공' if success else '실패'}!")
