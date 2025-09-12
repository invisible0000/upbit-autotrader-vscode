"""
업비트 API 밀리초 지원 확인 테스트
KRW-BTC 1분봉 1개 요청하여 timestamp 정밀도 확인
"""

import requests
from datetime import datetime
from urllib.parse import quote


def test_upbit_millisecond_support():
    """업비트 API가 밀리초까지 지원하는지 확인"""

    # 업비트 캔들 API URL
    url = "https://api.upbit.com/v1/candles/minutes/1"

    # 요청 시간 출력 (밀리초 포함)
    # request_time = datetime.now()  # 현재 시간 (참고용)
    
    # 업비트 문서 예시 형식들 + 밀리초 테스트
    test_formats = [
        "2025-09-11T23:27:00.000001",      # 마이크로초 (6자리)
        "2025-09-11T23:27:00.001",         # 밀리초 (3자리)
        "2025-09-11T23:27:00",             # 기본 ISO 8601
        "2025-09-11T23:27:00Z",            # UTC 명시
        "2025-09-11 23:27:00",             # 공백 구분자
        "2025-09-11T23:27:00+09:00",       # KST 타임존
    ]
    
    for test_time in test_formats:
        print(f"\n=== 요청시간: {test_time} ===")
        
        # URL 인코딩 확인
        encoded_time = quote(test_time)
        print(f"URL 인코딩: {encoded_time}")
        
        # 파라미터: KRW-BTC 1분봉 1개
        params = {
            "market": "KRW-BTC",
            "count": 1,
            "to": test_time  # requests가 자동 인코딩
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
