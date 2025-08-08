#!/usr/bin/env python3
"""
간단한 데이터베이스 상태 확인 스크립트
"""

import yaml
import os
import sqlite3

def main():
    print("=== 데이터베이스 상태 진단 ===\n")

    # 1. database_config.yaml 읽기
    with open('config/database_config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    databases = config.get('databases', {})

    # 2. 각 데이터베이스 상태 확인
    for db_type, conf in databases.items():
        db_path = conf.get('path', '')
        print(f"📁 {db_type}:")
        print(f"   경로: {db_path}")

        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"   ✅ 파일 존재 ({size:,} bytes)")

            # SQLite 검증
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                conn.close()
                print(f"   ✅ 유효한 SQLite (테이블 {table_count}개)")

                # 파일 락 테스트
                try:
                    with open(db_path, 'r+b') as f:
                        pass
                    print("   ✅ 파일 락 없음")
                except Exception as e:
                    print(f"   ⚠️ 파일 락 가능성: {e}")

            except Exception as e:
                print(f"   ❌ SQLite 오류: {e}")
        else:
            print("   ❌ 파일 없음")
        print()

    # 3. 백업 파일들 확인
    print("📦 백업 파일들:")
    data_files = [f for f in os.listdir('data') if f.endswith('.sqlite3')]
    for f in data_files:
        if '복사본' in f or 'backup' in f or 'copy' in f:
            print(f"   {f}")

    print("\n=== 진단 완료 ===")

if __name__ == "__main__":
    main()
