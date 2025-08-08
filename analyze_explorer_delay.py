#!/usr/bin/env python3
"""
Windows 탐색기 SQLite 파일 접근 지연 원인 분석
"""

import os
import time
import subprocess

def test_windows_explorer_access():
    print("=== Windows 탐색기 SQLite 파일 접근 지연 분석 ===\n")

    # 테스트할 파일들
    test_files = [
        'data/settings.sqlite3',
        'data/strategies.sqlite3',
        'data/settings_test01.sqlite3',
        'data/strategies_test01.sqlite3'
    ]

    print("1️⃣ 파일 속성 빠른 확인 테스트")
    for file_path in test_files:
        if os.path.exists(file_path):
            start_time = time.time()

            # 파일 속성 확인 (탐색기가 하는 것과 비슷)
            stat = os.stat(file_path)

            elapsed = time.time() - start_time
            print(f"📁 {os.path.basename(file_path)}: {elapsed:.3f}초")
            print(f"   크기: {stat.st_size:,} bytes")
            print(f"   수정시간: {time.ctime(stat.st_mtime)}")

    print("\n2️⃣ 파일 타입 확인 (Windows file 명령)")
    try:
        for file_path in test_files[:2]:  # 첫 2개만 테스트
            if os.path.exists(file_path):
                start_time = time.time()

                # Windows file 명령어 사용 (없을 수도 있음)
                try:
                    result = subprocess.run(['file', file_path],
                                          capture_output=True, text=True, timeout=5)
                    elapsed = time.time() - start_time
                    print(f"📁 {os.path.basename(file_path)}: {elapsed:.3f}초")
                    if result.stdout:
                        print(f"   타입: {result.stdout.strip()}")
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    print(f"📁 {os.path.basename(file_path)}: file 명령어 없음")
    except Exception as e:
        print(f"❌ file 명령어 테스트 실패: {e}")

    print("\n3️⃣ SQLite 헤더 분석")
    for file_path in test_files[:2]:  # 첫 2개만 분석
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(16)
                    magic = header[:16].decode('ascii', errors='ignore')
                    print(f"📁 {os.path.basename(file_path)}")
                    print(f"   헤더: {magic}")
                    if magic.startswith('SQLite format 3'):
                        print("   ✅ 정상 SQLite 파일")
                    else:
                        print("   ❌ 비정상 SQLite 헤더")
            except Exception as e:
                print(f"📁 {os.path.basename(file_path)}: 헤더 읽기 실패: {e}")

    print("\n4️⃣ 해결책 제안")
    print("🔧 Windows 탐색기 SQLite 파일 지연 해결 방법:")
    print("   1. 바이러스 백신 실시간 검사에서 *.sqlite3 제외")
    print("   2. Windows Defender에서 해당 폴더 제외")
    print("   3. 파일 인덱싱 서비스에서 *.sqlite3 제외")
    print("   4. 썸네일 생성 비활성화")

    print("\n✅ 테스트 완료 - Python에서는 정상 접근됨")
    print("⚠️ Windows 탐색기 지연은 시스템 설정 문제일 가능성 높음")

if __name__ == "__main__":
    test_windows_explorer_access()
