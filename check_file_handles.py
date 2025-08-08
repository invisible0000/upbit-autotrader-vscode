#!/usr/bin/env python3
"""
SQLite 파일 핸들 및 접근 상태 확인 스크립트
"""

import os
import sqlite3
import time
import psutil
from pathlib import Path

def check_file_handles():
    print("=== SQLite 파일 핸들 및 접근 상태 확인 ===\n")

    # SQLite 파일들
    sqlite_files = [
        'data/settings.sqlite3',
        'data/strategies.sqlite3',
        'data/market_data.sqlite3',
        'data/settings_test01.sqlite3',
        'data/strategies_test01.sqlite3',
        'data/market_data_test01.sqlite3'
    ]

    # 1. 파일 존재 및 크기 확인
    print("1️⃣ 파일 존재 및 크기 확인")
    for file_path in sqlite_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path}: {size:,} bytes")
        else:
            print(f"❌ {file_path}: 파일 없음")
    print()

    # 2. 파일 락 상태 확인
    print("2️⃣ 파일 락 상태 확인")
    for file_path in sqlite_files:
        if os.path.exists(file_path):
            print(f"🔍 {os.path.basename(file_path)} 테스트 중...")

            # 읽기 전용 접근 테스트
            try:
                start_time = time.time()
                with open(file_path, 'rb') as f:
                    f.read(1024)  # 1KB만 읽기
                read_time = time.time() - start_time
                print(f"   ✅ 읽기 접근: {read_time:.3f}초")
            except Exception as e:
                print(f"   ❌ 읽기 실패: {e}")

            # 쓰기 접근 테스트 (SQLite 특화)
            try:
                start_time = time.time()
                conn = sqlite3.connect(file_path, timeout=1)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                conn.close()
                sqlite_time = time.time() - start_time
                print(f"   ✅ SQLite 접근: {sqlite_time:.3f}초")
            except Exception as e:
                print(f"   ❌ SQLite 접근 실패: {e}")

            print()

    # 3. Python 프로세스의 열린 파일 확인
    print("3️⃣ Python 프로세스의 열린 파일 확인")
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'python.exe':
                try:
                    open_files = proc.open_files()
                    sqlite_files_open = [f for f in open_files if f.path.endswith('.sqlite3')]

                    if sqlite_files_open:
                        print(f"🔍 PID {proc.info['pid']}가 열고 있는 SQLite 파일들:")
                        for f in sqlite_files_open:
                            print(f"   📁 {f.path}")
                    else:
                        print(f"✅ PID {proc.info['pid']}: SQLite 파일 없음")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    print(f"❌ PID {proc.info['pid']}: 접근 권한 없음")
    except Exception as e:
        print(f"❌ psutil 확인 실패: {e}")

    print("\n=== 확인 완료 ===")

if __name__ == "__main__":
    check_file_handles()
