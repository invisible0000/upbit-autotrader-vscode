#!/usr/bin/env python3
"""
기존 KRW-BTC 데이터 분석 스크립트
"""
import sqlite3
import pandas as pd
from datetime import datetime

def analyze_existing_data():
    """기존 upbit_auto_trading.sqlite3 데이터 분석"""
    print("📊 === 기존 KRW-BTC 데이터 분석 ===")
    
    try:
        conn = sqlite3.connect('data/upbit_auto_trading.sqlite3')
        cursor = conn.cursor()
        
        # 테이블 목록 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"🔸 총 테이블 수: {len(tables)}개")
        print("=" * 60)
        
        # 각 테이블 분석
        for table_name, in tables:
            print(f"\n📋 테이블: {table_name}")
            print("-" * 40)
            
            # 스키마 정보
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("컬럼 구조:")
            for col in columns:
                col_id, name, data_type, not_null, default_val, pk = col
                pk_mark = " (PK)" if pk else ""
                null_mark = " NOT NULL" if not_null else ""
                default_mark = f" DEFAULT {default_val}" if default_val else ""
                print(f"  • {name}: {data_type}{pk_mark}{null_mark}{default_mark}")
            
            # 데이터 수
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"데이터 수: {count}개")
            
            # KRW-BTC 데이터 확인
            if 'symbol' in [col[1] for col in columns]:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE symbol = 'KRW-BTC';")
                btc_count = cursor.fetchone()[0]
                if btc_count > 0:
                    print(f"🪙 KRW-BTC 데이터: {btc_count}개")
                    
                    # 샘플 데이터 (최신 3개)
                    if 'timestamp' in [col[1] for col in columns]:
                        cursor.execute(f"SELECT * FROM {table_name} WHERE symbol = 'KRW-BTC' ORDER BY timestamp DESC LIMIT 3;")
                        samples = cursor.fetchall()
                        print("최신 샘플 데이터:")
                        for i, sample in enumerate(samples, 1):
                            print(f"  {i}. {sample}")
            
            # 일반 샘플 데이터 (3개)
            elif count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                samples = cursor.fetchall()
                print("샘플 데이터:")
                for i, sample in enumerate(samples, 1):
                    print(f"  {i}. {sample}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 분석 실패: {e}")

def check_market_data_availability():
    """시장 데이터 가용성 확인"""
    print("\n🎯 === 시뮬레이션용 데이터 가용성 검토 ===")
    
    try:
        conn = sqlite3.connect('data/upbit_auto_trading.sqlite3')
        
        # OHLCV 데이터 테이블 찾기
        potential_tables = ['market_data', 'candles', 'ohlcv', 'price_data', 'candle_data']
        
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        print("📊 시장 데이터 테이블 검색:")
        for table in potential_tables:
            if table in existing_tables:
                print(f"  ✅ {table} - 존재")
                
                # 데이터 범위 확인
                try:
                    cursor.execute(f"SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM {table} WHERE symbol = 'KRW-BTC';")
                    min_date, max_date, count = cursor.fetchone()
                    if count and count > 0:
                        print(f"     📅 기간: {min_date} ~ {max_date}")
                        print(f"     📈 데이터 수: {count:,}개")
                except Exception as e:
                    print(f"     ❌ 데이터 확인 실패: {e}")
            else:
                print(f"  ❌ {table} - 없음")
        
        # 모든 테이블에서 KRW-BTC 관련 데이터 검색
        print("\n🔍 모든 테이블에서 KRW-BTC 데이터 검색:")
        for table in existing_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE symbol = 'KRW-BTC' OR market = 'KRW-BTC';")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"  🪙 {table}: {count:,}개 KRW-BTC 데이터")
            except:
                # symbol 또는 market 컬럼이 없는 테이블은 무시
                pass
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 가용성 검토 실패: {e}")

def suggest_implementation_plan():
    """실제 데이터 기반 구현 계획 제안"""
    print("\n💡 === 실제 데이터 기반 구현 계획 ===")
    
    recommendations = [
        "1. 📊 기존 KRW-BTC 데이터 활용",
        "   - data/upbit_auto_trading.sqlite3에서 실제 캔들 데이터 추출",
        "   - 시나리오별로 적절한 기간 데이터 선택",
        "   - 실제 시장 패턴을 반영한 시뮬레이션",
        "",
        "2. 🎯 시나리오별 데이터 추출 전략",
        "   - 📈 상승: 강세장 기간 데이터 (예: 2023년 초반)",
        "   - 📉 하락: 약세장 기간 데이터 (예: 2022년 하반기)",
        "   - 🚀 급등: 급등 구간 데이터 추출",
        "   - 💥 급락: 급락 구간 데이터 추출",
        "   - ➡️ 횡보: 변동성 낮은 구간 데이터",
        "   - 🔄 지수크로스: 이평선 교차 구간 데이터",
        "",
        "3. 🔄 데이터 처리 파이프라인",
        "   - 기존 DB → 시뮬레이션 테이블 복사",
        "   - RSI, SMA 등 기술적 지표 실시간 계산",
        "   - 시나리오에 맞는 데이터 세그먼트 선택",
        "",
        "4. 🎮 즉시 구현 가능한 범위",
        "   - 현재 2개 트리거 (RSI, SMA) 테스트",
        "   - 실제 데이터 기반 현실적 시뮬레이션",
        "   - 가짜 데이터 생성 없이 안전한 구현"
    ]
    
    for rec in recommendations:
        print(rec)

if __name__ == "__main__":
    print(f"🕐 분석 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    analyze_existing_data()
    check_market_data_availability()
    suggest_implementation_plan()
    
    print(f"\n✅ 분석 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
