#!/usr/bin/env python3
"""
이상한 DB 파일들을 생성해서 상태 위젯 테스트
- 손상된 SQLite 파일
- 빈 파일
- 텍스트 파일
- 권한 없는 파일
"""

import os
import sqlite3
from pathlib import Path

def create_problematic_databases():
    print("=== 문제가 있는 테스트 DB 파일들 생성 ===\n")

    data_dir = Path("data")

    # 1. 완전히 빈 파일
    print("1️⃣ 빈 파일 생성")
    empty_file = data_dir / "settings_empty.sqlite3"
    empty_file.touch()
    print(f"   ✅ 생성: {empty_file} (0 bytes)")

    # 2. 텍스트 파일 (SQLite 아님)
    print("\n2️⃣ 텍스트 파일 생성 (SQLite 아님)")
    text_file = data_dir / "settings_text.sqlite3"
    with open(text_file, 'w') as f:
        f.write("이것은 SQLite 파일이 아닙니다!\nJust plain text.")
    print(f"   ✅ 생성: {text_file} ({text_file.stat().st_size} bytes)")

    # 3. 손상된 SQLite 파일 (헤더만 있음)
    print("\n3️⃣ 손상된 SQLite 파일 생성")
    corrupted_file = data_dir / "settings_corrupted.sqlite3"
    with open(corrupted_file, 'wb') as f:
        # SQLite 헤더만 쓰고 중간에 손상
        f.write(b'SQLite format 3\000')
        f.write(b'\x00' * 50)  # 일부 헤더
        f.write(b'CORRUPTED DATA!!!' * 10)  # 손상된 데이터
    print(f"   ✅ 생성: {corrupted_file} ({corrupted_file.stat().st_size} bytes)")

    # 4. 유효한 SQLite이지만 테이블 없음
    print("\n4️⃣ 빈 SQLite 파일 생성")
    empty_sqlite = data_dir / "settings_notables.sqlite3"
    conn = sqlite3.connect(str(empty_sqlite))
    conn.close()
    print(f"   ✅ 생성: {empty_sqlite} ({empty_sqlite.stat().st_size} bytes)")

    # 5. 잘못된 스키마를 가진 SQLite
    print("\n5️⃣ 잘못된 스키마 SQLite 생성")
    wrong_schema = data_dir / "settings_wrongschema.sqlite3"
    conn = sqlite3.connect(str(wrong_schema))
    cursor = conn.cursor()
    # 설정 DB가 아닌 전혀 다른 테이블들
    cursor.execute("CREATE TABLE movies (id INTEGER, title TEXT)")
    cursor.execute("CREATE TABLE actors (id INTEGER, name TEXT)")
    cursor.execute("INSERT INTO movies VALUES (1, 'Matrix')")
    cursor.execute("INSERT INTO actors VALUES (1, 'Keanu Reeves')")
    conn.commit()
    conn.close()
    print(f"   ✅ 생성: {wrong_schema} ({wrong_schema.stat().st_size} bytes)")

    # 6. 거대한 파일 (성능 테스트용)
    print("\n6️⃣ 거대한 SQLite 파일 생성")
    large_file = data_dir / "settings_large.sqlite3"
    conn = sqlite3.connect(str(large_file))
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE dummy_data (id INTEGER, data TEXT)")

    # 대량 데이터 삽입
    large_data = "A" * 1000  # 1KB 문자열
    for i in range(1000):  # 1MB 정도
        cursor.execute("INSERT INTO dummy_data VALUES (?, ?)", (i, large_data))

    conn.commit()
    conn.close()
    print(f"   ✅ 생성: {large_file} ({large_file.stat().st_size:,} bytes)")

    print("\n=== 테스트 파일 생성 완료 ===")
    print("다음 파일들로 UI에서 테스트해보세요:")

    test_files = [
        ("settings_empty.sqlite3", "빈 파일"),
        ("settings_text.sqlite3", "텍스트 파일"),
        ("settings_corrupted.sqlite3", "손상된 SQLite"),
        ("settings_notables.sqlite3", "테이블 없는 SQLite"),
        ("settings_wrongschema.sqlite3", "잘못된 스키마"),
        ("settings_large.sqlite3", "거대한 파일")
    ]

    for filename, description in test_files:
        file_path = data_dir / filename
        size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"   📁 {filename}: {description} ({size_mb:.2f}MB)")

if __name__ == "__main__":
    create_problematic_databases()
