#!/usr/bin/env python3
"""
임시 DB 분석 스크립트
- 프로젝트 내 모든 SQLite DB 파일을 찾아서 구조와 내용 분석
"""

import os
import sqlite3
import glob
from pathlib import Path


def find_db_files():
    """프로젝트 내 모든 DB 파일 찾기"""
    db_files = []
    
    # 프로젝트 루트에서 시작
    project_root = Path(__file__).parent.parent
    
    # .db 파일들 찾기
    for db_file in project_root.rglob("*.db"):
        db_files.append(str(db_file))
    
    # .sqlite3 파일들 찾기
    for db_file in project_root.rglob("*.sqlite3"):
        db_files.append(str(db_file))
    
    return db_files


def analyze_db_structure(db_path):
    """DB 파일 구조 분석"""
    print(f"\n{'='*60}")
    print(f"📊 DB 파일 분석: {db_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(db_path):
        print("❌ 파일이 존재하지 않습니다.")
        return
    
    # 파일 크기 확인
    file_size = os.path.getsize(db_path)
    print(f"📏 파일 크기: {file_size:,} bytes ({file_size/(1024*1024):.2f} MB)")
    
    if file_size == 0:
        print("⚠️ 빈 파일입니다.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 목록 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"🗂️ 테이블 개수: {len(tables)}")
        
        for table_name, in tables:
            print(f"\n📋 테이블: {table_name}")
            
            # 테이블 스키마 조회
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("  📑 컬럼 구조:")
            for col in columns:
                col_id, name, type_, not_null, default, pk = col
                nullable = "NOT NULL" if not_null else "NULL"
                primary = "PK" if pk else ""
                print(f"    - {name} ({type_}) {nullable} {primary}")
            
            # 데이터 개수 조회
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  📊 데이터 개수: {count:,} 행")
            
            # 샘플 데이터 조회 (최대 3개)
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                samples = cursor.fetchall()
                
                print("  📄 샘플 데이터:")
                for i, sample in enumerate(samples, 1):
                    print(f"    {i}. {sample}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ DB 오류: {e}")
    except Exception as e:
        print(f"❌ 일반 오류: {e}")


def analyze_specific_settings():
    """설정 관련 테이블 특별 분석"""
    print(f"\n{'='*60}")
    print("🔍 설정 관련 데이터 상세 분석")
    print(f"{'='*60}")
    
    db_files = find_db_files()
    
    for db_path in db_files:
        if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            continue
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 설정 관련 테이블 찾기
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]
            
            settings_tables = [t for t in tables if 'setting' in t.lower() or 'config' in t.lower() or 'preference' in t.lower()]
            
            if settings_tables:
                print(f"\n📁 {os.path.basename(db_path)}의 설정 테이블:")
                
                for table in settings_tables:
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    
                    print(f"  🔧 {table} ({len(rows)} 설정):")
                    for row in rows:
                        print(f"    {row}")
            
            conn.close()
            
        except Exception as e:
            continue


def main():
    """메인 실행 함수"""
    print("🔍 업비트 자동매매 시스템 DB 파일 분석")
    print("=" * 60)
    
    # 모든 DB 파일 찾기
    db_files = find_db_files()
    
    print(f"📁 발견된 DB 파일 개수: {len(db_files)}")
    for db_file in db_files:
        print(f"  - {db_file}")
    
    # 각 DB 파일 구조 분석
    for db_file in db_files:
        analyze_db_structure(db_file)
    
    # 설정 관련 상세 분석
    analyze_specific_settings()
    
    print(f"\n{'='*60}")
    print("✅ 분석 완료!")


if __name__ == "__main__":
    main()
