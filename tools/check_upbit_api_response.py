"""
업비트 캔들 API 응답 구조 확인
"""
import requests
import json

def check_upbit_candle_response():
    """업비트 캔들 API 응답 구조 확인"""
    try:
        # 업비트 캔들 API 호출
        url = "https://api.upbit.com/v1/candles/minutes/1"
        params = {
            "market": "KRW-BTC",
            "count": 2
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        print("=== 업비트 캔들 API 응답 구조 ===")
        print(f"응답 타입: {type(data)}")
        print(f"데이터 개수: {len(data)}")

        if data:
            print("\n=== 첫 번째 캔들 데이터 구조 ===")
            first_candle = data[0]
            print(f"캔들 데이터 타입: {type(first_candle)}")

            print("\n=== 모든 필드명과 값 ===")
            for key, value in first_candle.items():
                print(f"{key}: {value} (타입: {type(value).__name__})")

            print("\n=== JSON 포맷 (첫 번째 캔들) ===")
            print(json.dumps(first_candle, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"캔들 API 호출 오류: {e}")


def check_upbit_ticker_response():
    """업비트 티커 API 응답 구조 확인"""
    try:
        # 업비트 티커 API 호출
        url = "https://api.upbit.com/v1/ticker"
        params = {
            "markets": "KRW-BTC"
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        print("\n=== 업비트 티커 API 응답 구조 ===")
        print(f"응답 타입: {type(data)}")
        print(f"데이터 개수: {len(data)}")

        if data:
            print("\n=== 첫 번째 티커 데이터 구조 ===")
            first_ticker = data[0]
            print(f"티커 데이터 타입: {type(first_ticker)}")

            print("\n=== 모든 필드명과 값 ===")
            for key, value in first_ticker.items():
                print(f"{key}: {value} (타입: {type(value).__name__})")

            print("\n=== JSON 포맷 (첫 번째 티커) ===")
            print(json.dumps(first_ticker, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"티커 API 호출 오류: {e}")


if __name__ == "__main__":
    check_upbit_candle_response()
    check_upbit_ticker_response()
