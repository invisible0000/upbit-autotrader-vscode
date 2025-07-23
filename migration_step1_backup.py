#!/usr/bin/env python3
"""
데이터베이스 통합 마이그레이션 스크립트
Step 1: 백업 생성
"""

import sqlite3
import os
import shutil
from datetime import datetime
import json

def create_backup():
    """모든 데이터베이스 백업 생성"""
    
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    databases_to_backup = [
        'strategies.db',
        'data/trading_conditions.db'
    ]
    
    # 추가 db 파일들도 백업
    if os.path.exists('data/upbit_auto_trading.db'):
        databases_to_backup.append('data/upbit_auto_trading.db')
    
    backup_info = {
        "backup_created": datetime.now().isoformat(),
        "original_files": [],
        "backup_directory": backup_dir
    }
    
    print(f"📦 백업 디렉토리 생성: {backup_dir}")
    
    for db_path in databases_to_backup:
        if os.path.exists(db_path):
            backup_file = os.path.join(backup_dir, os.path.basename(db_path))
            shutil.copy2(db_path, backup_file)
            
            # 파일 크기 확인
            original_size = os.path.getsize(db_path)
            backup_size = os.path.getsize(backup_file)
            
            print(f"✅ {db_path} → {backup_file} ({original_size} bytes)")
            
            backup_info["original_files"].append({
                "original_path": db_path,
                "backup_path": backup_file,
                "size": original_size,
                "verified": original_size == backup_size
            })
        else:
            print(f"⚠️ 파일 없음: {db_path}")
    
    # 백업 정보 저장
    info_file = os.path.join(backup_dir, "backup_info.json")
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(backup_info, f, indent=2, ensure_ascii=False)
    
    print(f"📋 백업 정보 저장: {info_file}")
    return backup_dir, backup_info

def verify_backup(backup_dir, backup_info):
    """백업 파일 무결성 검증"""
    
    print("\n🔍 백업 무결성 검증...")
    
    all_verified = True
    
    for file_info in backup_info["original_files"]:
        original_path = file_info["original_path"]
        backup_path = file_info["backup_path"]
        
        if os.path.exists(original_path) and os.path.exists(backup_path):
            # 파일 크기 비교
            original_size = os.path.getsize(original_path)
            backup_size = os.path.getsize(backup_path)
            
            if original_size == backup_size:
                print(f"✅ {os.path.basename(backup_path)}: 크기 일치 ({original_size} bytes)")
                
                # 데이터베이스 스키마 검증
                try:
                    original_conn = sqlite3.connect(original_path)
                    backup_conn = sqlite3.connect(backup_path)
                    
                    original_cursor = original_conn.cursor()
                    backup_cursor = backup_conn.cursor()
                    
                    # 테이블 목록 비교
                    original_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    original_tables = set(row[0] for row in original_cursor.fetchall())
                    
                    backup_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    backup_tables = set(row[0] for row in backup_cursor.fetchall())
                    
                    if original_tables == backup_tables:
                        print(f"  📋 스키마 일치: {len(original_tables)}개 테이블")
                    else:
                        print(f"  ⚠️ 스키마 불일치: 원본({len(original_tables)}) vs 백업({len(backup_tables)})")
                        all_verified = False
                    
                    original_conn.close()
                    backup_conn.close()
                    
                except Exception as e:
                    print(f"  ❌ 스키마 검증 오류: {str(e)}")
                    all_verified = False
            else:
                print(f"❌ {os.path.basename(backup_path)}: 크기 불일치 (원본: {original_size}, 백업: {backup_size})")
                all_verified = False
        else:
            print(f"❌ 파일 없음: {backup_path}")
            all_verified = False
    
    return all_verified

if __name__ == "__main__":
    print("🚀 데이터베이스 백업 시작")
    print("=" * 50)
    
    backup_dir, backup_info = create_backup()
    
    print("\n" + "=" * 50)
    verified = verify_backup(backup_dir, backup_info)
    
    if verified:
        print("✅ 모든 백업이 성공적으로 생성되고 검증되었습니다!")
        print(f"📂 백업 위치: {backup_dir}")
    else:
        print("❌ 백업 검증에 실패했습니다. 마이그레이션을 중단하세요.")
        exit(1)
    
    print("\n🎯 다음 단계: 통합 데이터베이스 생성")
    print("   python migration_step2_create_unified_db.py")
