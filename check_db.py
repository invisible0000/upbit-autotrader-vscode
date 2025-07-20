import sqlite3
import pandas as pd
import os

# 두 DB 파일 모두 확인
db_files = ['data/upbit_auto_trading.sqlite3', 'data/upbit_auto_trading.db']

for db_file in db_files:
    print(f"\n{'='*50}")
    print(f"📁 DB 파일: {db_file}")
    
    if os.path.exists(db_file):
        file_size = os.path.getsize(db_file)
        print(f"파일 크기: {file_size} bytes")
        
        # DB 연결
        conn = sqlite3.connect(db_file)
        
        # 테이블 목록 확인
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
        print('📋 테이블 목록:')
        print(tables)
        
        # OHLCV 테이블이 있다면 데이터 확인
        try:
            ohlcv_data = pd.read_sql_query('SELECT * FROM ohlcv ORDER BY timestamp DESC LIMIT 5', conn)
            print('\n📊 최근 OHLCV 데이터 (최대 5개):')
            print(ohlcv_data)
        except Exception as e:
            print(f'OHLCV 테이블 조회 실패: {e}')
        
        # 총 데이터 개수 확인
        try:
            count = pd.read_sql_query('SELECT COUNT(*) as count FROM ohlcv WHERE symbol="KRW-BTC" AND timeframe="1d"', conn)
            print(f'\n📈 KRW-BTC 1일 차트 데이터 개수: {count.iloc[0]["count"]}개')
        except Exception as e:
            print(f'데이터 개수 조회 실패: {e}')
        
        conn.close()
    else:
        print(f"파일이 존재하지 않습니다.")
