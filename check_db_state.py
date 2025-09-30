#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
현재 DB 상태 상세 확인
"""

import sqlite3
from datetime import datetime


def check_current_db_state():
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    print('🔐 secure_keys 테이블 전체 내용:')
    cursor.execute('SELECT id, key_type, LENGTH(key_value) as key_size, created_at, updated_at FROM secure_keys ORDER BY id')
    rows = cursor.fetchall()
    for row in rows:
        print(f'   ID: {row[0]}, Type: {row[1]}, Size: {row[2]}bytes')
        print(f'      Created: {row[3]}')
        print(f'      Updated: {row[4]}')
        print()

    # 최근 1시간 이내 변경된 레코드가 있는지 확인
    cursor.execute('''
        SELECT COUNT(*) as recent_count
        FROM secure_keys
        WHERE updated_at > datetime("now", "-1 hour", "localtime")
    ''')
    recent_count = cursor.fetchone()[0]
    print(f'📅 최근 1시간 내 업데이트된 레코드 수: {recent_count}')

    # 테이블의 마지막 수정 시간 확인
    cursor.execute('SELECT MAX(updated_at) FROM secure_keys')
    last_updated = cursor.fetchone()[0]
    print(f'🕐 테이블 마지막 업데이트: {last_updated}')

    conn.close()


if __name__ == "__main__":
    check_current_db_state()
