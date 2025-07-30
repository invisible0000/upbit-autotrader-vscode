import sqlite3

conn = sqlite3.connect('upbit_auto_trading/data/settings.sqlite3')
cursor = conn.cursor()

# SMA 변수 확인
cursor.execute('SELECT * FROM tv_trading_variables WHERE variable_id = ?', ('SMA',))
sma_result = cursor.fetchone()
print('SMA 변수:', sma_result)

# 모든 변수 목록 확인
cursor.execute('SELECT variable_id, display_name_ko FROM tv_trading_variables ORDER BY variable_id')
all_vars = cursor.fetchall()
print('모든 변수 개수:', len(all_vars))
print('처음 10개 변수:', all_vars[:10])

conn.close()
