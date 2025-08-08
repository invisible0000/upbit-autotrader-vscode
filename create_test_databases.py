#!/usr/bin/env python3
"""
테스트용 데이터베이스 파일 생성 스크립트
각 데이터베이스의 _test01.sqlite3 버전을 생성합니다.
"""

import os
import shutil
import sqlite3

def create_test_databases():
    print("=== 테스트용 데이터베이스 파일 생성 ===\n")

    # 원본 데이터베이스 파일들
    original_files = {
        'settings': 'data/settings.sqlite3',
        'strategies': 'data/strategies.sqlite3',
        'market_data': 'data/market_data.sqlite3'
    }

    # 테스트용 파일들 생성
    for db_type, original_path in original_files.items():
        test_path = original_path.replace('.sqlite3', '_test01.sqlite3')

        print(f"📁 {db_type} 데이터베이스:")
        print(f"   원본: {original_path}")
        print(f"   테스트: {test_path}")

        if os.path.exists(original_path):
            # 파일 복사
            shutil.copy2(original_path, test_path)

            # 크기 확인
            original_size = os.path.getsize(original_path)
            test_size = os.path.getsize(test_path)

            print(f"   ✅ 복사 완료 ({original_size:,} -> {test_size:,} bytes)")

            # SQLite 유효성 검증
            try:
                conn = sqlite3.connect(test_path)
                cursor = conn.cursor()
                cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                conn.close()
                print(f"   ✅ 유효한 SQLite 파일 (테이블 {table_count}개)")
            except Exception as e:
                print(f"   ❌ SQLite 검증 실패: {e}")
        else:
            print(f"   ❌ 원본 파일 없음")

        print()

    # 생성된 테스트 파일들 목록
    print("📦 생성된 테스트 파일들:")
    test_files = [f for f in os.listdir('data') if f.endswith('_test01.sqlite3')]
    for f in sorted(test_files):
        size = os.path.getsize(f'data/{f}')
        print(f"   {f} ({size:,} bytes)")

    print(f"\n✅ 총 {len(test_files)}개 테스트 파일 생성 완료")
    print("\n=== 이제 안전하게 DB 경로 교체 테스트를 할 수 있습니다! ===")

if __name__ == "__main__":
    create_test_databases()
