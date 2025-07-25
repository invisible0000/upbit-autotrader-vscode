#!/usr/bin/env python3
"""
데이터베이스 테이블 구조 확인 및 올바른 데이터 찾기
"""

import sqlite3
import pandas as pd
import os

def explore_database():
    """데이터베이스 전체 구조 탐색"""
    print("🔍 데이터베이스 구조 탐색 시작")
    print("="*60)
    
    db_path = 'data/market_data.sqlite3'
    
    if not os.path.exists(db_path):
        print(f"❌ DB 파일 없음: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 모든 테이블 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 총 {len(tables)}개 테이블 발견:")
        for i, table in enumerate(tables, 1):
            print(f"  {i:2d}. {table}")
        
        # OHLCV 관련 테이블 찾기
        ohlcv_tables = [t for t in tables if any(keyword in t.lower() for keyword in ['ohlc', 'candle', 'btc', 'krw', 'market'])]
        print(f"\n💰 OHLCV/시장 관련 테이블 ({len(ohlcv_tables)}개):")
        for table in ohlcv_tables:
            print(f"  - {table}")
        
        # 각 관련 테이블 상세 분석
        for table in ohlcv_tables[:3]:  # 상위 3개만 분석
            print(f"\n📊 테이블 '{table}' 분석:")
            
            # 컬럼 구조 확인
            cursor.execute(f'PRAGMA table_info({table})')
            columns = cursor.fetchall()
            print(f"   컬럼 구조 ({len(columns)}개):")
            for col in columns:
                print(f"     {col[1]} ({col[2]})")
            
            # 데이터 개수 확인
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"   데이터 개수: {count:,}개")
            
            # 샘플 데이터 확인
            if count > 0:
                cursor.execute(f'SELECT * FROM {table} LIMIT 3')
                samples = cursor.fetchall()
                print(f"   샘플 데이터:")
                for j, sample in enumerate(samples, 1):
                    print(f"     {j}. {sample}")
        
        conn.close()
        return True, ohlcv_tables
        
    except Exception as e:
        print(f"❌ DB 탐색 오류: {e}")
        return False, []

def find_btc_data(ohlcv_tables):
    """BTC 관련 실제 데이터 찾기"""
    print(f"\n🎯 BTC 관련 실제 데이터 찾기")
    print("="*60)
    
    db_path = 'data/market_data.sqlite3'
    
    try:
        conn = sqlite3.connect(db_path)
        
        for table in ohlcv_tables:
            print(f"\n📈 테이블 '{table}' BTC 데이터 검색:")
            
            try:
                # 테이블 컬럼 확인
                cursor = conn.cursor()
                cursor.execute(f'PRAGMA table_info({table})')
                columns = [col[1] for col in cursor.fetchall()]
                
                # 가능한 BTC 관련 데이터 찾기
                possible_queries = []
                
                # 1. 심볼/마켓 컬럼이 있는 경우
                symbol_cols = [col for col in columns if any(keyword in col.lower() for keyword in ['symbol', 'market', 'pair', 'coin'])]
                if symbol_cols:
                    for col in symbol_cols:
                        query = f"SELECT DISTINCT {col} FROM {table} WHERE {col} LIKE '%BTC%' OR {col} LIKE '%KRW%' LIMIT 10"
                        possible_queries.append((f"심볼 검색 ({col})", query))
                
                # 2. 날짜 관련 컬럼 확인
                date_cols = [col for col in columns if any(keyword in col.lower() for keyword in ['date', 'time', 'timestamp'])]
                price_cols = [col for col in columns if any(keyword in col.lower() for keyword in ['price', 'close', 'open', 'high', 'low'])]
                
                if date_cols and price_cols:
                    date_col = date_cols[0]
                    price_col = price_cols[0]
                    query = f"SELECT {date_col}, {price_col} FROM {table} ORDER BY {date_col} DESC LIMIT 5"
                    possible_queries.append((f"최신 가격 데이터 ({date_col}, {price_col})", query))
                
                # 쿼리 실행
                for desc, query in possible_queries:
                    try:
                        print(f"   {desc}:")
                        cursor.execute(query)
                        results = cursor.fetchall()
                        if results:
                            for result in results:
                                print(f"     {result}")
                        else:
                            print(f"     (데이터 없음)")
                    except Exception as e:
                        print(f"     ❌ 쿼리 오류: {e}")
                
            except Exception as e:
                print(f"   ❌ 테이블 분석 오류: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ BTC 데이터 검색 오류: {e}")

def update_simulation_engine(correct_table, correct_columns):
    """올바른 테이블 정보로 시뮬레이션 엔진 업데이트"""
    print(f"\n🔧 시뮬레이션 엔진 업데이트")
    print("="*60)
    
    print(f"발견된 테이블: {correct_table}")
    print(f"사용할 컬럼: {correct_columns}")
    
    # 실제 데이터 시뮬레이션 파일 업데이트 제안
    print(f"\n📝 real_data_simulation.py 업데이트 필요:")
    print(f"  - 테이블명: 'krw_btc_daily_candles' → '{correct_table}'")
    print(f"  - 컬럼 매핑 확인 필요")

def main():
    """메인 실행"""
    print("🚀 데이터베이스 구조 분석 및 실제 데이터 찾기")
    print("="*80)
    
    # 1. 데이터베이스 전체 구조 탐색
    success, ohlcv_tables = explore_database()
    
    if not success:
        print("❌ 데이터베이스 탐색 실패")
        return
    
    # 2. BTC 관련 데이터 찾기
    if ohlcv_tables:
        find_btc_data(ohlcv_tables)
    else:
        print("⚠️ OHLCV 관련 테이블을 찾을 수 없습니다")
    
    print(f"\n" + "="*80)
    print("🎯 분석 완료!")
    print("다음 단계: 발견된 올바른 테이블명으로 real_data_simulation.py 업데이트")

if __name__ == "__main__":
    main()
