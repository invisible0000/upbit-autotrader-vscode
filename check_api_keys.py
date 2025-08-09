#!/usr/bin/env python3
"""
API 키 상태 확인 스크립트
"""

import sqlite3
from pathlib import Path

def check_api_keys():
    """현재 settings.sqlite3의 API 키 상태 확인"""

    db_path = Path("data/settings.sqlite3")

    if not db_path.exists():
        print("❌ settings.sqlite3 파일이 존재하지 않습니다")
        return

    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()

            # 전체 키 개수 확인
            cursor.execute('SELECT COUNT(*) FROM secure_keys')
            total_count = cursor.fetchone()[0]

            # 암호화 키 개수 확인
            cursor.execute('SELECT COUNT(*) FROM secure_keys WHERE key_type = "encryption"')
            encryption_count = cursor.fetchone()[0]

            print(f"📊 키 상태 요약:")
            print(f"   전체 키: {total_count}개")
            print(f"   암호화키: {encryption_count}개")
            print()

            # 모든 키 상세 정보
            cursor.execute('SELECT key_type, created_at, updated_at FROM secure_keys ORDER BY created_at')
            keys = cursor.fetchall()

            if keys:
                print("📋 저장된 키 목록:")
                for i, (key_type, created_at, updated_at) in enumerate(keys, 1):
                    print(f"   {i}. 키 타입: {key_type}")
                    print(f"      생성일: {created_at}")
                    print(f"      수정일: {updated_at}")
                    print()
            else:
                print("✅ 저장된 키가 없습니다 (완전히 삭제됨)")

    except Exception as e:
        print(f"❌ 데이터베이스 확인 중 오류: {e}")

if __name__ == "__main__":
    check_api_keys()
