#!/usr/bin/env python3
"""
데이터베이스 파일 위치 및 정보 확인 스크립트
"""

import os
import sqlite3
from datetime import datetime

def find_database_files():
    """모든 데이터베이스 파일 위치 확인"""
    
    print("🔍 데이터베이스 파일 위치 확인")
    print("=" * 60)
    
    # 현재 작업 디렉토리
    current_dir = os.getcwd()
    print(f"📂 현재 작업 디렉토리: {current_dir}")
    
    # 찾을 데이터베이스 파일들
    db_files_to_find = [
        "strategies.db",
        "upbit_trading_unified.db",
        "data/trading_conditions.db",
        "data/upbit_auto_trading.db",
        "upbit_auto_trading/ui/desktop/data/trading_conditions.db"
    ]
    
    print("\n📋 데이터베이스 파일 위치:")
    
    found_files = []
    
    for db_file in db_files_to_find:
        full_path = os.path.abspath(db_file)
        
        if os.path.exists(db_file):
            file_size = os.path.getsize(db_file)
            modified_time = datetime.fromtimestamp(os.path.getmtime(db_file))
            
            print(f"✅ {db_file}")
            print(f"   📍 전체 경로: {full_path}")
            print(f"   📏 파일 크기: {file_size:,} bytes")
            print(f"   🕒 수정 시간: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 데이터베이스 내용 간단 확인
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                print(f"   📊 테이블 수: {len(tables)}개 ({', '.join(tables[:3])}{'...' if len(tables) > 3 else ''})")
            except:
                print(f"   ❌ 데이터베이스 읽기 오류")
            
            found_files.append({
                'relative_path': db_file,
                'absolute_path': full_path,
                'size': file_size,
                'modified': modified_time
            })
            print()
        else:
            print(f"❌ {db_file}")
            print(f"   📍 예상 경로: {full_path}")
            print()
    
    return found_files

def recommend_database_location():
    """권장 데이터베이스 위치 제안"""
    
    print("💡 데이터베이스 위치 권장사항")
    print("=" * 60)
    
    current_dir = os.getcwd()
    
    # 가능한 위치들
    locations = [
        {
            "name": "프로젝트 루트 (현재)",
            "path": current_dir,
            "pros": ["접근 용이", "상대 경로 단순"],
            "cons": ["버전 관리에 포함될 수 있음"]
        },
        {
            "name": "data 폴더",
            "path": os.path.join(current_dir, "data"),
            "pros": ["논리적 분리", "백업 용이"],
            "cons": ["상대 경로 복잡"]
        },
        {
            "name": "사용자 문서 폴더",
            "path": os.path.expanduser("~/Documents/upbit_autotrader"),
            "pros": ["시스템 독립적", "사용자별 분리"],
            "cons": ["절대 경로 필요"]
        },
        {
            "name": "AppData 폴더 (Windows)",
            "path": os.path.expanduser("~/AppData/Local/upbit_autotrader"),
            "pros": ["표준 위치", "자동 백업 제외"],
            "cons": ["찾기 어려움"]
        }
    ]
    
    for i, location in enumerate(locations, 1):
        print(f"{i}. {location['name']}")
        print(f"   📍 경로: {location['path']}")
        print(f"   ✅ 장점: {', '.join(location['pros'])}")
        print(f"   ⚠️ 단점: {', '.join(location['cons'])}")
        print()

def check_backup_directories():
    """백업 디렉토리 확인"""
    
    print("📦 백업 디렉토리 확인")
    print("=" * 60)
    
    backup_dirs = []
    
    # backup_* 패턴의 디렉토리 찾기
    for item in os.listdir('.'):
        if os.path.isdir(item) and item.startswith('backup_'):
            backup_size = 0
            backup_files = []
            
            for file in os.listdir(item):
                file_path = os.path.join(item, file)
                if os.path.isfile(file_path):
                    backup_size += os.path.getsize(file_path)
                    backup_files.append(file)
            
            backup_dirs.append({
                'name': item,
                'size': backup_size,
                'files': backup_files,
                'path': os.path.abspath(item)
            })
    
    if backup_dirs:
        backup_dirs.sort(key=lambda x: x['name'], reverse=True)  # 최신 백업부터
        
        print(f"발견된 백업: {len(backup_dirs)}개")
        
        for backup in backup_dirs:
            print(f"\n📂 {backup['name']}")
            print(f"   📍 경로: {backup['path']}")
            print(f"   📏 크기: {backup['size']:,} bytes")
            print(f"   📄 파일: {', '.join(backup['files'])}")
    else:
        print("백업 디렉토리가 없습니다.")

def provide_copy_commands():
    """데이터베이스 복사 명령어 제공"""
    
    print("\n💾 데이터베이스 복사 명령어")
    print("=" * 60)
    
    unified_db = "upbit_trading_unified.db"
    
    if os.path.exists(unified_db):
        full_path = os.path.abspath(unified_db)
        
        print("🎯 통합 데이터베이스 복사 방법:")
        print(f"원본 위치: {full_path}")
        print()
        
        # Windows 명령어
        print("📋 Windows (PowerShell/CMD):")
        print(f'Copy-Item "{full_path}" "백업위치\\upbit_trading_unified.db"')
        print(f'copy "{full_path}" "백업위치\\upbit_trading_unified.db"')
        print()
        
        # 파일 탐색기에서 복사
        print("🖱️ 파일 탐색기에서:")
        print(f"1. 파일 탐색기에서 다음 경로로 이동:")
        print(f"   {os.path.dirname(full_path)}")
        print(f"2. '{os.path.basename(unified_db)}' 파일을 찾아서")
        print(f"3. 마우스 오른쪽 클릭 → 복사 → 원하는 위치에 붙여넣기")
        print()
        
        # Python으로 복사
        print("🐍 Python 스크립트로 복사:")
        print(f"""
import shutil
import os
from datetime import datetime

source = r"{full_path}"
backup_name = f"upbit_trading_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.db"
destination = os.path.join("백업폴더경로", backup_name)

shutil.copy2(source, destination)
print(f"백업 완료: {{destination}}")
        """)
    else:
        print("❌ 통합 데이터베이스 파일을 찾을 수 없습니다.")

if __name__ == "__main__":
    # 데이터베이스 파일 위치 확인
    found_files = find_database_files()
    
    # 백업 디렉토리 확인
    check_backup_directories()
    
    # 위치 권장사항
    recommend_database_location()
    
    # 복사 명령어 제공
    provide_copy_commands()
    
    print("\n" + "=" * 60)
    print("📝 요약:")
    print(f"✅ 발견된 DB 파일: {len(found_files)}개")
    
    # 통합 데이터베이스가 있는지 확인
    unified_exists = any(f['relative_path'] == 'upbit_trading_unified.db' for f in found_files)
    if unified_exists:
        print("🎯 통합 데이터베이스 사용 가능 - 이 파일 하나만 백업하면 됩니다!")
    else:
        print("⚠️ 통합 데이터베이스가 없습니다. 마이그레이션을 먼저 완료하세요.")
