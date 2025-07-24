#!/usr/bin/env python3
"""
원자적 전략 빌더 테이블 확인 스크립트
Atomic Strategy Builder Tables Checker
"""

import sqlite3
import os

def check_atomic_tables():
    """새로 생성된 atomic 테이블들 확인"""
    
    db_path = 'data/upbit_auto_trading.sqlite3'
    
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return
    
    print("🧩 원자적 전략 빌더 테이블 검사 시작...")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # atomic_ 테이블들 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'atomic_%' ORDER BY name")
        atomic_tables = cursor.fetchall()
        
        if not atomic_tables:
            print("❌ atomic_ 테이블이 발견되지 않았습니다!")
            print("   💡 atomic_strategy_db_schema.py를 실행했는지 확인하세요.")
            return
        
        print(f"✅ {len(atomic_tables)}개의 atomic 테이블 발견!")
        print()
        
        for table in atomic_tables:
            table_name = table[0]
            print(f"📋 {table_name}:")
            
            # 테이블 구조 확인
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                is_pk = " (PK)" if col[5] else ""
                not_null = " NOT NULL" if col[3] else ""
                print(f"  - {col_name} ({col_type}){is_pk}{not_null}")
            
            # 데이터 개수 확인
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  📊 데이터 개수: {count}개")
            
            # 샘플 데이터 확인 (있는 경우)
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                samples = cursor.fetchall()
                print(f"  🔍 샘플 데이터:")
                for i, sample in enumerate(samples, 1):
                    # 첫 번째 필드만 표시 (ID 또는 이름)
                    first_field = str(sample[0])[:50] + "..." if len(str(sample[0])) > 50 else str(sample[0])
                    print(f"     {i}. {first_field}")
            
            print()
        
        print("=" * 60)
        print("🎉 원자적 전략 빌더 테이블 검사 완료!")
        
        # 추가로 템플릿 데이터가 있는지 확인
        if any('template' in table[0] for table in atomic_tables):
            print("\n🎯 템플릿 데이터 확인:")
            cursor.execute("SELECT name, description FROM atomic_strategy_templates WHERE is_featured = 1")
            templates = cursor.fetchall()
            if templates:
                for template in templates:
                    print(f"  ⭐ {template[0]}: {template[1][:80]}...")
            else:
                print("  ❌ 추천 템플릿이 없습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """메인 함수"""
    check_atomic_tables()

if __name__ == "__main__":
    main()
