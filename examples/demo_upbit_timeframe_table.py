#!/usr/bin/env python3
"""업비트 타임프레임별 시간 정보 테이블 출력"""

import urllib.request
import urllib.parse
import json
import time
from datetime import datetime

def get_upbit_timeframe_table():
    """모든 타임프레임의 시간 정보를 테이블로 출력"""

    # 헤더 정보 출력
    current_time = datetime.now().isoformat()
    print("캔들 데이터 실제 시간 형식 확인 테스트")
    print(f"수집 시점: {current_time}, count = 5")
    print("=" * 80)

    timeframes = {
        '1s': 'seconds',
        '1m': 'minutes/1',
        '3m': 'minutes/3',
        '5m': 'minutes/5',
        '15m': 'minutes/15',
        '30m': 'minutes/30',
        '60m': 'minutes/60',
        '240m': 'minutes/240',
        '1d': 'days',
        '1w': 'weeks',
        '1M': 'months',
        '1y': 'years'
    }

    print("timeframe | candle_date_time_utc | candle_date_time_kst | timestamp")
    print("-" * 80)

    for tf, endpoint in timeframes.items():
        try:
            url = f"https://api.upbit.com/v1/candles/{endpoint}?market=KRW-BTC&count=5"

            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))

            for candle in data:
                utc_time = candle['candle_date_time_utc']
                kst_time = candle['candle_date_time_kst']
                timestamp = candle['timestamp']

                print(f"{tf:>9} | {utc_time:>19} | {kst_time:>19} | {timestamp}")

            time.sleep(0.1)  # Rate limit

        except Exception as e:
            print(f"{tf:>9} | ERROR: {e}")

if __name__ == "__main__":
    get_upbit_timeframe_table()
