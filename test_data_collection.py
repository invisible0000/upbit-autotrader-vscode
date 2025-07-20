"""
실제 업비트 API 데이터 수집 테스트 스크립트
"""
import sys
import os
import logging
from datetime import datetime, timedelta

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_upbit_api():
    """업비트 API 연결 테스트"""
    print("🔄 업비트 API 테스트 중...")
    
    try:
        from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
        
        api = UpbitAPI()
        print("✅ UpbitAPI 객체 생성 성공")
        
        # 기본 API 테스트 - 티커 목록 조회
        print("📋 티커 목록 조회 중...")
        tickers = api.get_tickers()
        
        if tickers and len(tickers) > 0:
            print(f"✅ API 연결 성공! 총 {len(tickers)}개 코인 조회됨")
            print(f"📊 KRW 마켓 코인 예시: {[t for t in tickers if t.startswith('KRW-')][:5]}")
            return True
        else:
            print("❌ 티커 조회 실패")
            return False
            
    except Exception as e:
        print(f"❌ API 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_collection():
    """실제 데이터 수집 테스트"""
    print("\n🔄 데이터 수집 테스트 중...")
    
    try:
        from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
        
        api = UpbitAPI()
        
        # 최근 5일간의 KRW-BTC 1일 차트 데이터 수집
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)
        
        print(f"📅 수집 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        print("⏳ KRW-BTC 1일 차트 데이터 수집 중...")
        
        data = api.get_candles_range(
            symbol="KRW-BTC",
            timeframe="1d",
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if data is not None and not data.empty:
            print(f"✅ 데이터 수집 성공! {len(data)}개 캔들 데이터 수집됨")
            print("\n📊 수집된 데이터 미리보기:")
            print(data.head(3))
            print(f"\n📈 데이터 컬럼: {list(data.columns)}")
            return data
        else:
            print("❌ 데이터 수집 실패 - 빈 데이터")
            return None
            
    except Exception as e:
        print(f"❌ 데이터 수집 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_data_storage(data):
    """데이터 저장 테스트"""
    print("\n🔄 데이터 저장 테스트 중...")
    
    try:
        from upbit_auto_trading.data_layer.storage.market_data_storage import MarketDataStorage
        
        storage = MarketDataStorage()
        print("✅ MarketDataStorage 객체 생성 성공")
        
        success = storage.save_market_data(data)
        
        if success:
            print("✅ 데이터 저장 성공!")
            return True
        else:
            print("❌ 데이터 저장 실패")
            return False
            
    except Exception as e:
        print(f"❌ 데이터 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database():
    """데이터베이스 내용 확인"""
    print("\n🔄 데이터베이스 확인 중...")
    
    try:
        import sqlite3
        import pandas as pd
        
        db_path = "data/upbit_auto_trading.sqlite3"
        
        if not os.path.exists(db_path):
            print(f"❌ 데이터베이스 파일이 없습니다: {db_path}")
            return
        
        file_size = os.path.getsize(db_path)
        print(f"📁 DB 파일: {db_path} ({file_size} bytes)")
        
        conn = sqlite3.connect(db_path)
        
        # 테이블 목록 확인
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
        print(f"📋 테이블 목록: {list(tables['name']) if not tables.empty else '없음'}")
        
        # market_data 테이블 확인
        try:
            count_query = "SELECT COUNT(*) as count FROM market_data WHERE symbol='KRW-BTC' AND timeframe='1d'"
            count_result = pd.read_sql_query(count_query, conn)
            count = count_result.iloc[0]['count']
            print(f"📈 KRW-BTC 1일 데이터 개수: {count}개")
            
            if count > 0:
                recent_data = pd.read_sql_query(
                    "SELECT * FROM market_data WHERE symbol='KRW-BTC' AND timeframe='1d' ORDER BY timestamp DESC LIMIT 3", 
                    conn
                )
                print("\n📊 최근 저장된 데이터:")
                print(recent_data)
                
        except Exception as e:
            print(f"market_data 테이블 조회 실패: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 데이터베이스 확인 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 테스트 함수"""
    print("="*60)
    print("🚀 업비트 자동매매 데이터 수집 테스트 시작")
    print("="*60)
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 1. API 연결 테스트
    if not test_upbit_api():
        print("\n❌ API 테스트 실패로 종료")
        return
    
    # 2. 데이터 수집 테스트
    data = test_data_collection()
    if data is None:
        print("\n❌ 데이터 수집 실패로 종료")
        return
    
    # 3. 데이터 저장 테스트
    if not test_data_storage(data):
        print("\n❌ 데이터 저장 실패")
    
    # 4. 데이터베이스 확인
    check_database()
    
    print("\n" + "="*60)
    print("🎉 테스트 완료!")
    print("="*60)

if __name__ == "__main__":
    main()
