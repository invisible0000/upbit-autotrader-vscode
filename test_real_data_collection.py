"""
실제 데이터 수집 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
from upbit_auto_trading.data_layer.storage.market_data_storage import MarketDataStorage
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)

def test_data_collection():
    """실제 데이터 수집 테스트"""
    try:
        print("🔄 API 연결 테스트...")
        api = UpbitAPI()
        
        # 간단한 API 테스트 - 현재 시세 조회
        tickers = api.get_tickers()
        print(f"✅ API 연결 성공! 코인 개수: {len(tickers)}")
        
        print("\n🔄 데이터 수집 테스트 중...")
        # 최근 3일간의 KRW-BTC 1일 데이터 수집
        data = api.get_candles_range(
            symbol="KRW-BTC",
            timeframe="1d", 
            start_date="2025-01-08",  # 3일 전
            end_date="2025-01-10"     # 오늘
        )
        
        if data is not None and not data.empty:
            print(f"✅ 데이터 수집 성공! 데이터 개수: {len(data)}")
            print("📋 수집된 데이터 미리보기:")
            print(data.head())
            
            print("\n🔄 데이터 저장 테스트...")
            storage = MarketDataStorage()
            success = storage.save_market_data(data)
            
            if success:
                print("✅ 데이터 저장 성공!")
            else:
                print("❌ 데이터 저장 실패!")
        else:
            print("❌ 데이터 수집 실패!")
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_collection()
