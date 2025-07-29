#!/usr/bin/env python3
"""
데이터베이스 스키마 분석 스크립트
Phase 2 시작 전 현재 DB 구조 상세 분석
"""

import sqlite3
import os
from pathlib import Path

def analyze_db_schema(db_path, db_name):
    """데이터베이스 스키마 상세 분석"""
    if not os.path.exists(db_path):
        print(f'❌ {db_name}: 파일이 존재하지 않음 - {db_path}')
        return
    
    print(f'\n📊 {db_name} 스키마 분석: {db_path}')
    print('=' * 80)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 목록 조회
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
        tables = cursor.fetchall()
        
        if not tables:
            print('⚠️ 테이블이 없습니다.')
            conn.close()
            return
            
        print(f'📋 총 테이블 수: {len(tables)}개')
        
        for (table_name,) in tables:
            print(f'\n📋 테이블: {table_name}')
            
            # 테이블 스키마 조회
            cursor.execute(f'PRAGMA table_info({table_name})')
            columns = cursor.fetchall()
            
            print('  컬럼 구조:')
            for col in columns:
                pk = 'PRIMARY KEY ' if col[5] else ''
                notnull = 'NOT NULL ' if col[3] else ''
                default = f'DEFAULT {col[4]} ' if col[4] else ''
                print(f'    - {col[1]} ({col[2]}) {pk}{notnull}{default}')
            
            # 데이터 개수 확인
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cursor.fetchone()[0]
            print(f'  📊 데이터 개수: {count}행')
            
            # 인덱스 확인
            cursor.execute(f'PRAGMA index_list({table_name})')
            indexes = cursor.fetchall()
            if indexes:
                print(f'  🔍 인덱스: {len(indexes)}개')
                for idx in indexes:
                    print(f'    - {idx[1]} (unique: {idx[2]})')
            
            # 샘플 데이터 (최대 3개, 안전하게)
            if count > 0:
                try:
                    cursor.execute(f'SELECT * FROM {table_name} LIMIT 3')
                    samples = cursor.fetchall()
                    print('  🔍 샘플 데이터:')
                    for i, row in enumerate(samples, 1):
                        # 긴 데이터는 잘라서 표시
                        row_str = str(row)
                        if len(row_str) > 100:
                            row_str = row_str[:100] + '...'
                        print(f'    {i}. {row_str}')
                except Exception as e:
                    print(f'    ⚠️ 샘플 데이터 조회 실패: {e}')
        
        conn.close()
        print('\n✅ 스키마 분석 완료')
        
    except Exception as e:
        print(f'❌ 오류 발생: {e}')

def main():
    """메인 분석 함수"""
    print('🔍 현재 데이터베이스 스키마 상세 분석')
    print('Phase 2 시작 전 보수적 검토')
    print('=' * 80)

    # 분석할 데이터베이스 목록
    databases = [
        ('data/app_settings.sqlite3', 'APP_SETTINGS (설정 데이터)'),
        ('data/upbit_auto_trading.sqlite3', 'UPBIT_AUTO_TRADING (전략 데이터)'),
        ('trading_variables.db', 'TRADING_VARIABLES (거래 변수)'),
        ('data/market_data.sqlite3', 'MARKET_DATA (시장 데이터)')
    ]
    
    for db_path, db_name in databases:
        analyze_db_schema(db_path, db_name)
    
    print('\n' + '=' * 80)
    print('🎯 분석 완료 - 이제 안전하게 Phase 2를 진행할 수 있습니다')
    print('💡 중요한 데이터가 있는 테이블들을 확인했으니 보수적으로 마이그레이션하겠습니다')

if __name__ == "__main__":
    main()
