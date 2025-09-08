import sqlite3

conn = sqlite3.connect('data/market_data.sqlite3')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'candles_%'")
count = cursor.fetchone()[0]
print(f'📊 현재 캔들 테이블 수: {count}개')

# 스키마 오류 없는 새 테이블들만 확인
cursor.execute("""
    SELECT name FROM sqlite_master
    WHERE type='table' AND name LIKE 'candles_%'
    AND name NOT LIKE '%_KRW_BTC_%'
    AND name NOT LIKE '%_KRW_ETH_%'
    AND name NOT LIKE '%_KRW_ADA_%'
    ORDER BY name DESC
    LIMIT 10
""")
new_tables = cursor.fetchall()

print('\n📋 최근 생성된 새 테이블들 (일부):')
for table in new_tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
    row_count = cursor.fetchone()[0]
    print(f'   {table[0]} ({row_count}개 레코드)')

conn.close()
