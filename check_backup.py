import sqlite3
import os

# 백업 파일 확인
backup_path = 'data/settings - 복사본.sqlite3'
try:
    conn = sqlite3.connect(backup_path)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
    table_count = cursor.fetchone()[0]
    conn.close()
    print(f'✅ 백업 파일 정상: {table_count}개 테이블')

    # 파일 크기 비교
    original_size = os.path.getsize('data/settings.sqlite3')
    backup_size = os.path.getsize(backup_path)
    print(f'손상된 파일: {original_size:,} bytes')
    print(f'백업 파일: {backup_size:,} bytes')

except Exception as e:
    print(f'❌ 백업 파일도 문제: {e}')
