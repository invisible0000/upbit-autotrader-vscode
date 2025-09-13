import sqlite3

conn = sqlite3.connect('data/market_data.sqlite3')
cursor = conn.execute('SELECT candle_date_time_utc FROM candles_KRW_BTC_1m ORDER BY candle_date_time_utc DESC')
rows = cursor.fetchall()

print(f'총 레코드 수: {len(rows)}')
print('저장된 캔들 시간들:')
for i, row in enumerate(rows):
    print(f'  {i+1:2d}. {row[0]}')

conn.close()
