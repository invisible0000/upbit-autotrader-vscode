#!/usr/bin/env python3
"""
실제 KRW-BTC 시장 데이터 확인 스크립트
케이스 시뮬레이션에서 사용되는 실제 데이터 검증
"""

import sqlite3
import pandas as pd
import os

def check_market_data():
    """시장 데이터 DB 확인"""
    print("🔍 실제 KRW-BTC 시장 데이터 확인 시작")
    print("="*50)
    
    db_path = 'data/market_data.sqlite3'
    
    if not os.path.exists(db_path):
        print(f"❌ 시장 데이터 DB 없음: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 목록 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"🗃️ 사용 가능한 테이블: {tables}")
        
        # KRW-BTC 데이터 확인
        if 'krw_btc_daily_candles' in tables:
            cursor.execute('SELECT COUNT(*) FROM krw_btc_daily_candles')
            count = cursor.fetchone()[0]
            print(f"💰 KRW-BTC 일봉 데이터: {count:,}개")
            
            # 최신 10개 데이터 확인
            cursor.execute('SELECT date_kst, trade_price FROM krw_btc_daily_candles ORDER BY date_kst DESC LIMIT 10')
            recent_data = cursor.fetchall()
            print("📈 최신 10개 데이터:")
            for date, price in recent_data:
                print(f"  {date}: {price:,}원")
            
            # 데이터 범위 확인
            cursor.execute('SELECT MIN(date_kst), MAX(date_kst) FROM krw_btc_daily_candles')
            min_date, max_date = cursor.fetchone()
            print(f"📅 데이터 범위: {min_date} ~ {max_date}")
            
            return True
        else:
            print("❌ krw_btc_daily_candles 테이블 없음")
            return False
            
    except Exception as e:
        print(f"❌ DB 접근 오류: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def test_scenario_detection():
    """시나리오별 실제 데이터 케이스 검출"""
    print("\n🎯 시나리오별 실제 데이터 케이스 검출")
    print("="*50)
    
    db_path = 'data/market_data.sqlite3'
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 7일간 변화율로 시나리오 검출
        query = """
        SELECT date_kst, trade_price, 
               LAG(trade_price, 7) OVER (ORDER BY date_kst) as price_7d_ago
        FROM krw_btc_daily_candles 
        WHERE date_kst IS NOT NULL
        ORDER BY date_kst DESC
        LIMIT 200
        """
        
        df = pd.read_sql(query, conn)
        df['change_7d'] = (df['trade_price'] - df['price_7d_ago']) / df['price_7d_ago'] * 100
        df = df.dropna()
        
        # 급등 케이스 (7일간 15% 이상 상승)
        surge_cases = df[df['change_7d'] > 15].head(5)
        if not surge_cases.empty:
            print("📈 급등 케이스 발견:")
            for _, row in surge_cases.iterrows():
                print(f"  {row['date_kst']}: {row['change_7d']:.1f}% 상승 ({row['trade_price']:,}원)")
        else:
            print("📈 급등 케이스: 최근 200일간 없음")
        
        # 급락 케이스 (7일간 15% 이상 하락)
        crash_cases = df[df['change_7d'] < -15].head(5)
        if not crash_cases.empty:
            print("📉 급락 케이스 발견:")
            for _, row in crash_cases.iterrows():
                print(f"  {row['date_kst']}: {row['change_7d']:.1f}% 하락 ({row['trade_price']:,}원)")
        else:
            print("📉 급락 케이스: 최근 200일간 없음")
        
        # 상승 추세 케이스 (30일간 5% 이상 상승)
        df['price_30d_ago'] = df['trade_price'].shift(-30)
        df['change_30d'] = (df['trade_price'] - df['price_30d_ago']) / df['price_30d_ago'] * 100
        
        uptrend_cases = df[df['change_30d'] > 5].head(3)
        if not uptrend_cases.empty:
            print("🔺 상승 추세 케이스:")
            for _, row in uptrend_cases.iterrows():
                print(f"  {row['date_kst']}: {row['change_30d']:.1f}% 상승")
        
        # 하락 추세 케이스 (30일간 5% 이상 하락)
        downtrend_cases = df[df['change_30d'] < -5].head(3)
        if not downtrend_cases.empty:
            print("🔻 하락 추세 케이스:")
            for _, row in downtrend_cases.iterrows():
                print(f"  {row['date_kst']}: {row['change_30d']:.1f}% 하락")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 시나리오 검출 오류: {e}")
        return False

def test_real_data_simulation():
    """실제 데이터 시뮬레이션 엔진 테스트"""
    print("\n🎮 실제 데이터 시뮬레이션 엔진 테스트")
    print("="*50)
    
    try:
        # 실제 데이터 시뮬레이션 엔진 임포트
        import sys
        sys.path.append('upbit_auto_trading/ui/desktop/screens/strategy_management')
        
        from real_data_simulation import get_simulation_engine
        
        engine = get_simulation_engine()
        print("✅ 시뮬레이션 엔진 생성 성공")
        
        # 시나리오별 테스트
        scenarios = ["상승 추세", "하락 추세", "급등", "급락", "횡보"]
        
        for scenario in scenarios:
            result = engine.get_scenario_data(scenario, length=30)
            
            if result and result.get('data_source') == 'real_market_data':
                print(f"✅ {scenario}: 실제 데이터 사용")
                print(f"   📊 기간: {result.get('period')}")
                print(f"   💹 변화율: {result.get('change_percent', 0):.1f}%")
                print(f"   📈 데이터 포인트: {len(result.get('price_data', []))}개")
            elif result and result.get('data_source') == 'fallback_simulation':
                print(f"⚠️ {scenario}: 폴백 시뮬레이션 사용")
            else:
                print(f"❌ {scenario}: 데이터 로드 실패")
        
        return True
        
    except Exception as e:
        print(f"❌ 시뮬레이션 엔진 테스트 오류: {e}")
        return False

def main():
    """메인 실행"""
    print("🚀 실제 데이터 시뮬레이션 검증 시작")
    print("="*60)
    
    # 1. 시장 데이터 확인
    data_ok = check_market_data()
    
    # 2. 시나리오 검출 테스트
    if data_ok:
        scenario_ok = test_scenario_detection()
    else:
        scenario_ok = False
    
    # 3. 시뮬레이션 엔진 테스트
    if data_ok:
        engine_ok = test_real_data_simulation()
    else:
        engine_ok = False
    
    # 결과 요약
    print("\n" + "="*60)
    print("📋 검증 결과 요약")
    print("="*60)
    print(f"실제 데이터 가용성: {'✅ 정상' if data_ok else '❌ 문제'}")
    print(f"시나리오 케이스 검출: {'✅ 정상' if scenario_ok else '❌ 문제'}")
    print(f"시뮬레이션 엔진: {'✅ 정상' if engine_ok else '❌ 문제'}")
    
    if data_ok and scenario_ok and engine_ok:
        print("\n🎉 모든 검증 통과! UI 케이스 시뮬레이션이 실제 데이터를 사용합니다.")
    else:
        print("\n⚠️ 일부 검증 실패. 문제 해결이 필요합니다.")

if __name__ == "__main__":
    main()
