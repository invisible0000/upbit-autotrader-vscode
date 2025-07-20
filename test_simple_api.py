"""
간단한 업비트 API 테스트
"""
import sys
import os
import requests

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_basic_upbit_api():
    """기본 업비트 API 테스트 (requests 사용)"""
    print("🔄 기본 업비트 API 테스트...")
    
    try:
        # 업비트 공개 API로 티커 목록 조회
        url = "https://api.upbit.com/v1/market/all"
        response = requests.get(url)
        
        if response.status_code == 200:
            tickers = response.json()
            krw_tickers = [t for t in tickers if t['market'].startswith('KRW-')]
            print(f"✅ API 연결 성공! KRW 마켓 코인 수: {len(krw_tickers)}")
            print(f"📊 예시 코인: {[t['market'] for t in krw_tickers[:5]]}")
            return True
        else:
            print(f"❌ API 요청 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API 테스트 실패: {e}")
        return False

def test_candle_api():
    """캔들 데이터 API 테스트"""
    print("\n🔄 캔들 데이터 API 테스트...")
    
    try:
        # KRW-BTC 일봉 데이터 최근 5개 조회
        url = "https://api.upbit.com/v1/candles/days"
        params = {
            "market": "KRW-BTC",
            "count": 5
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            candles = response.json()
            print(f"✅ 캔들 데이터 조회 성공! 데이터 수: {len(candles)}")
            
            if candles:
                latest = candles[0]
                print(f"📈 최신 데이터 (KRW-BTC):")
                print(f"   - 날짜: {latest['candle_date_time_kst']}")
                print(f"   - 시가: {latest['opening_price']:,}")
                print(f"   - 고가: {latest['high_price']:,}")
                print(f"   - 저가: {latest['low_price']:,}")
                print(f"   - 종가: {latest['trade_price']:,}")
                print(f"   - 거래량: {latest['candle_acc_trade_volume']:,.2f}")
            
            return candles
        else:
            print(f"❌ 캔들 데이터 요청 실패: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 캔들 데이터 테스트 실패: {e}")
        return None

def test_module_import():
    """모듈 import 테스트"""
    print("\n🔄 모듈 import 테스트...")
    
    try:
        # UpbitAPI 모듈 import 테스트
        from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
        print("✅ UpbitAPI 모듈 import 성공")
        
        api = UpbitAPI()
        print("✅ UpbitAPI 객체 생성 성공")
        
        # MarketDataStorage 모듈 import 테스트
        from upbit_auto_trading.data_layer.storage.market_data_storage import MarketDataStorage
        print("✅ MarketDataStorage 모듈 import 성공")
        
        storage = MarketDataStorage()
        print("✅ MarketDataStorage 객체 생성 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ 모듈 import 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    print("="*50)
    print("🧪 간단한 업비트 API 테스트")
    print("="*50)
    
    # 1. 기본 API 테스트
    if not test_basic_upbit_api():
        print("\n❌ 기본 API 테스트 실패")
        return
    
    # 2. 캔들 데이터 테스트
    candles = test_candle_api()
    if not candles:
        print("\n❌ 캔들 데이터 테스트 실패")
        return
    
    # 3. 모듈 import 테스트
    if not test_module_import():
        print("\n❌ 모듈 import 테스트 실패")
        return
    
    print("\n" + "="*50)
    print("🎉 모든 테스트 성공!")
    print("="*50)

if __name__ == "__main__":
    main()
