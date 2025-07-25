#!/usr/bin/env python3
"""
데이터베이스 구조 확인 스크립트
"""
import sqlite3
import os

def check_database_structure():
    """데이터베이스 구조 확인"""
    print("🔍 데이터베이스 구조 확인 스크립트")
    print("="*80)
    
    # 데이터베이스 파일들 확인
    data_dir = 'data'
    if os.path.exists(data_dir):
        print(f"📂 {data_dir} 디렉토리 내 파일들:")
        for file in os.listdir(data_dir):
            if file.endswith('.sqlite3') or file.endswith('.db'):
                file_path = os.path.join(data_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"  📄 {file} ({file_size} bytes)")
        print()
    
    # 각 데이터베이스 파일의 테이블 구조 확인
    db_files = [
        'data/upbit_auto_trading.sqlite3',
        'data/app_settings.sqlite3',
        'data/market_data.sqlite3'
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"🗄️ {db_file} 데이터베이스 분석:")
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # 테이블 목록 조회
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                if tables:
                    for table in tables:
                        table_name = table[0]
                        print(f"  📋 테이블: {table_name}")
                        
                        # 테이블 스키마 확인
                        cursor.execute(f"PRAGMA table_info({table_name});")
                        columns = cursor.fetchall()
                        
                        for col in columns:
                            col_name = col[1]
                            col_type = col[2]
                            print(f"    • {col_name} ({col_type})")
                        
                        # 레코드 수 확인
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                        count = cursor.fetchone()[0]
                        print(f"    📊 레코드 수: {count}")
                        print()
                else:
                    print("  ❌ 테이블이 없습니다.")
                
                conn.close()
                
            except Exception as e:
                print(f"  ❌ 오류: {e}")
            
            print("-"*60)
    
    print("🏁 데이터베이스 구조 확인 완료!")

if __name__ == "__main__":
    check_database_structure()
