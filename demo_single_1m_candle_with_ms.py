"""
업비트 API 밀리초 지원 확인 테스트
KRW-BTC 1분봉 1개 요청하여 timestamp 정밀도 확인
"""

import requests
from datetime import datetime


def test_upbit_millisecond_support():
    """업비트 API가 밀리초까지 지원하는지 확인"""

    # 업비트 캔들 API URL
    url = "https://api.upbit.com/v1/candles/minutes/1"

    # 요청 시간 출력 (밀리초 포함)
    # request_time = datetime.now()  # 현재 시간 (참고용)
    # print(f"요청시간: {request_time.isoformat()}")

    # 특정 시간으로 테스트: 2025-09-11T23:27:00.000001
    test_time = "2025-09-11T23:27:00.00001"
    print(f"요청시간: {test_time}")

    # 파라미터: KRW-BTC 1분봉 1개, 특정 시간 to 파라미터 추가
    params = {
        "market": "KRW-BTC",
        "count": 1,
        "to": test_time
    }

    try:
        # API 요청
        response = requests.get(url, params=params)
        response.raise_for_status()

        # 응답 데이터
        candles = response.json()

        if candles and len(candles) > 0:
            candle = candles[0]

            # timestamp 필드들 추출
            utc_timestamp = candle.get("candle_date_time_utc", "N/A")
            kst_timestamp = candle.get("candle_date_time_kst", "N/A")
            timestamp_field = candle.get("timestamp", "N/A")

            # 한 줄로 출력
            print(f"응답: UTC={utc_timestamp}, KST={kst_timestamp}, timestamp={timestamp_field}")

        else:
            print("응답: 캔들 데이터 없음")

    except requests.RequestException as e:
        print(f"API 요청 실패: {e}")
    except Exception as e:
        print(f"처리 오류: {e}")


if __name__ == "__main__":
    test_upbit_millisecond_support()
