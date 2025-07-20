"""
단계별 데이터 수집 테스트
"""
import sys
import os

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def step1_test_basic_import():
    """1단계: 기본 모듈 import 테스트"""
    print("📋 1단계: 기본 모듈 import 테스트")
    
    try:
        from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
        print("✅ UpbitAPI import 성공")
        
        from upbit_auto_trading.data_layer.storage.market_data_storage import MarketDataStorage
        print("✅ MarketDataStorage import 성공")
        
        return True
    except Exception as e:
        print(f"❌ import 실패: {e}")
        return False

def step2_test_object_creation():
    """2단계: 객체 생성 테스트"""
    print("\n📋 2단계: 객체 생성 테스트")
    
    try:
        from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
        from upbit_auto_trading.data_layer.storage.market_data_storage import MarketDataStorage
        
        print("⏳ UpbitAPI 객체 생성 중...")
        api = UpbitAPI()
        print("✅ UpbitAPI 객체 생성 성공")
        
        print("⏳ MarketDataStorage 객체 생성 중...")
        storage = MarketDataStorage()
        print("✅ MarketDataStorage 객체 생성 성공")
        
        return api, storage
    except Exception as e:
        print(f"❌ 객체 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def step3_test_simple_api_call(api):
    """3단계: 간단한 API 호출 테스트"""
    print("\n📋 3단계: 간단한 API 호출 테스트")
    
    try:
        print("⏳ 티커 목록 조회 중...")
        tickers = api.get_tickers()
        
        if tickers and len(tickers) > 0:
            print(f"✅ 티커 조회 성공: {len(tickers)}개")
            krw_tickers = [t for t in tickers if t.startswith('KRW-')]
            print(f"📊 KRW 마켓 코인: {len(krw_tickers)}개")
            return True
        else:
            print("❌ 티커 조회 실패")
            return False
            
    except Exception as e:
        print(f"❌ API 호출 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def step4_test_candle_data(api):
    """4단계: 캔들 데이터 조회 테스트"""
    print("\n📋 4단계: 캔들 데이터 조회 테스트")
    
    try:
        print("⏳ KRW-BTC 최근 2일 데이터 조회 중...")
        
        # get_candles_range 대신 get_candles 메서드 사용
        data = api.get_candles("KRW-BTC", "1d", count=2)
        
        if data is not None and not data.empty:
            print(f"✅ 캔들 데이터 조회 성공: {len(data)}개")
            print(f"📊 컬럼: {list(data.columns)}")
            print("📈 데이터 샘플:")
            print(data.head())
            return data
        else:
            print("❌ 캔들 데이터 조회 실패")
            return None
            
    except Exception as e:
        print(f"❌ 캔들 데이터 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def step5_test_db_creation():
    """5단계: 데이터베이스 생성 테스트"""
    print("\n📋 5단계: 데이터베이스 생성 테스트")
    
    try:
        import sqlite3
        
        # data 디렉토리 생성
        if not os.path.exists('data'):
            os.makedirs('data')
            print("✅ data 디렉토리 생성")
        
        db_path = "data/upbit_auto_trading.sqlite3"
        print(f"⏳ DB 파일 생성 테스트: {db_path}")
        
        conn = sqlite3.connect(db_path)
        
        # 테이블 생성
        conn.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                timestamp TEXT,
                symbol TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                timeframe TEXT,
                PRIMARY KEY (timestamp, symbol, timeframe)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ 데이터베이스 및 테이블 생성 성공")
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 생성 실패: {e}")
        return False

def step6_test_data_save(storage, data):
    """6단계: 데이터 저장 테스트"""
    print("\n📋 6단계: 데이터 저장 테스트")
    
    if data is None:
        print("❌ 저장할 데이터가 없습니다")
        return False
    
    try:
        print("⏳ 데이터 저장 중...")
        success = storage.save_market_data(data)
        
        if success:
            print("✅ 데이터 저장 성공")
            return True
        else:
            print("❌ 데이터 저장 실패")
            return False
            
    except Exception as e:
        print(f"❌ 데이터 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def step7_verify_saved_data():
    """7단계: 저장된 데이터 확인"""
    print("\n📋 7단계: 저장된 데이터 확인")
    
    try:
        import sqlite3
        import pandas as pd
        
        db_path = "data/upbit_auto_trading.sqlite3"
        
        if not os.path.exists(db_path):
            print(f"❌ DB 파일이 없습니다: {db_path}")
            return False
        
        file_size = os.path.getsize(db_path)
        print(f"📁 DB 파일 크기: {file_size:,} bytes")
        
        if file_size == 0:
            print("❌ DB 파일이 비어있습니다")
            return False
        
        conn = sqlite3.connect(db_path)
        
        # 데이터 개수 확인
        count_result = pd.read_sql_query("SELECT COUNT(*) as count FROM market_data", conn)
        count = count_result.iloc[0]['count']
        print(f"📊 저장된 데이터 개수: {count}개")
        
        if count > 0:
            # 샘플 데이터 조회
            sample_data = pd.read_sql_query("SELECT * FROM market_data LIMIT 2", conn)
            print("📈 저장된 데이터 샘플:")
            print(sample_data)
            
        conn.close()
        return count > 0
        
    except Exception as e:
        print(f"❌ 데이터 확인 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("="*50)
    print("🧪 단계별 데이터 수집 테스트")
    print("="*50)
    
    # 1단계: 모듈 import
    if not step1_test_basic_import():
        return
    
    # 2단계: 객체 생성
    api, storage = step2_test_object_creation()
    if api is None or storage is None:
        return
    
    # 3단계: 기본 API 호출
    if not step3_test_simple_api_call(api):
        return
    
    # 4단계: 캔들 데이터 조회
    data = step4_test_candle_data(api)
    
    # 5단계: DB 생성
    if not step5_test_db_creation():
        return
    
    # 6단계: 데이터 저장 (데이터가 있는 경우에만)
    if data is not None:
        step6_test_data_save(storage, data)
    
    # 7단계: 저장된 데이터 확인
    step7_verify_saved_data()
    
    print("\n" + "="*50)
    print("🎉 단계별 테스트 완료!")
    print("="*50)

if __name__ == "__main__":
    main()
