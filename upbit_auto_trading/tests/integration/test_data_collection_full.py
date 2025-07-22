"""
업비트 데이터 수집 및 저장 통합 테스트
"""
import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_full_data_collection():
    """전체 데이터 수집 및 저장 테스트"""
    print("🔄 전체 데이터 수집 및 저장 테스트...")
    
    try:
        # 모듈 import
        from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
        from upbit_auto_trading.data_layer.storage.market_data_storage import MarketDataStorage
        
        # 객체 생성
        api = UpbitAPI()
        storage = MarketDataStorage()
        print("✅ 객체 생성 완료")
        
        # 테스트 파라미터
        symbol = "KRW-BTC"
        timeframe = "1d"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)  # 최근 3일
        
        print(f"📅 수집 파라미터:")
        print(f"   - 코인: {symbol}")
        print(f"   - 타임프레임: {timeframe}")
        print(f"   - 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        # 데이터 수집
        print("⏳ 데이터 수집 중...")
        data = api.get_candles_range(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if data is None or data.empty:
            print("❌ 데이터 수집 실패 - 빈 데이터")
            return False
        
        print(f"✅ 데이터 수집 성공! {len(data)}개 캔들 수집됨")
        print(f"📊 데이터 컬럼: {list(data.columns)}")
        print("\n📈 수집된 데이터 샘플:")
        print(data.head(2))
        
        # 데이터 저장
        print("\n⏳ 데이터 저장 중...")
        success = storage.save_market_data(data)
        
        if not success:
            print("❌ 데이터 저장 실패")
            return False
        
        print("✅ 데이터 저장 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_saved_data():
    """저장된 데이터 확인"""
    print("\n🔄 저장된 데이터 확인...")
    
    try:
        db_path = "data/upbit_auto_trading.sqlite3"
        
        if not os.path.exists(db_path):
            print(f"❌ DB 파일이 없습니다: {db_path}")
            return
        
        file_size = os.path.getsize(db_path)
        print(f"📁 DB 파일: {db_path} ({file_size:,} bytes)")
        
        if file_size == 0:
            print("❌ DB 파일이 비어있습니다")
            return
        
        conn = sqlite3.connect(db_path)
        
        # 테이블 목록
        tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
        tables = list(tables_df['name']) if not tables_df.empty else []
        print(f"📋 테이블 목록: {tables}")
        
        if 'market_data' not in tables:
            print("❌ market_data 테이블이 없습니다")
            conn.close()
            return
        
        # 전체 데이터 개수
        total_count = pd.read_sql_query("SELECT COUNT(*) as count FROM market_data", conn)
        print(f"📊 전체 데이터 개수: {total_count.iloc[0]['count']}개")
        
        # KRW-BTC 1일 데이터 개수
        btc_count = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM market_data WHERE symbol='KRW-BTC' AND timeframe='1d'", 
            conn
        )
        print(f"📈 KRW-BTC 1일 데이터: {btc_count.iloc[0]['count']}개")
        
        # 최근 데이터 확인
        if btc_count.iloc[0]['count'] > 0:
            recent_data = pd.read_sql_query("""
                SELECT timestamp, symbol, timeframe, open, high, low, close, volume 
                FROM market_data 
                WHERE symbol='KRW-BTC' AND timeframe='1d' 
                ORDER BY timestamp DESC 
                LIMIT 3
            """, conn)
            
            print("\n📊 최근 저장된 데이터:")
            for _, row in recent_data.iterrows():
                print(f"   {row['timestamp']}: O:{row['open']:,} H:{row['high']:,} L:{row['low']:,} C:{row['close']:,}")
        
        conn.close()
        print("✅ 데이터 확인 완료")
        
    except Exception as e:
        print(f"❌ 데이터 확인 실패: {e}")
        import traceback
        traceback.print_exc()

def test_backtest_data_collection_simulation():
    """백테스팅 데이터 수집 시뮬레이션"""
    print("\n🔄 백테스팅 데이터 수집 시뮬레이션...")
    
    try:
        from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
        from upbit_auto_trading.data_layer.storage.market_data_storage import MarketDataStorage
        
        api = UpbitAPI()
        storage = MarketDataStorage()
        
        # 백테스팅 시나리오: KRW-BTC, KRW-ETH 최근 7일 데이터
        coins = ["KRW-BTC", "KRW-ETH"]
        timeframes = ["1d"]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        print(f"📊 백테스팅 시나리오:")
        print(f"   - 코인: {coins}")
        print(f"   - 타임프레임: {timeframes}")
        print(f"   - 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        total_tasks = len(coins) * len(timeframes)
        current_task = 0
        
        for coin in coins:
            for timeframe in timeframes:
                current_task += 1
                progress = int((current_task / total_tasks) * 100)
                
                print(f"\n⏳ ({progress}%) {coin} {timeframe} 데이터 수집 중...")
                
                # 데이터 수집
                data = api.get_candles_range(
                    symbol=coin,
                    timeframe=timeframe,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                
                if data is not None and not data.empty:
                    # 데이터 저장
                    success = storage.save_market_data(data)
                    if success:
                        print(f"✅ {coin} {timeframe} 저장 완료: {len(data)}개")
                    else:
                        print(f"❌ {coin} {timeframe} 저장 실패")
                else:
                    print(f"❌ {coin} {timeframe} 데이터 없음")
        
        print(f"\n🎉 백테스팅 데이터 수집 완료! (총 {total_tasks}개 작업)")
        return True
        
    except Exception as e:
        print(f"❌ 백테스팅 시뮬레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    print("="*60)
    print("🚀 업비트 데이터 수집 및 저장 통합 테스트")
    print("="*60)
    
    # 1. 기본 데이터 수집 및 저장 테스트
    if not test_full_data_collection():
        print("\n❌ 기본 테스트 실패로 종료")
        return
    
    # 2. 저장된 데이터 확인
    check_saved_data()
    
    # 3. 백테스팅 시나리오 시뮬레이션
    test_backtest_data_collection_simulation()
    
    # 4. 최종 데이터 확인
    check_saved_data()
    
    print("\n" + "="*60)
    print("🎉 모든 테스트 완료!")
    print("="*60)

if __name__ == "__main__":
    main()
