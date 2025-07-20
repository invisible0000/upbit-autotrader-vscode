"""
데이터 수집 상태 확인 스크립트
"""
import os
import sqlite3
import pandas as pd
from datetime import datetime

def check_database_status():
    """데이터베이스 상태 확인"""
    print("="*50)
    print("📊 데이터베이스 상태 확인")
    print("="*50)
    
    db_path = "data/upbit_auto_trading.sqlite3"
    
    if not os.path.exists(db_path):
        print(f"❌ DB 파일이 없습니다: {db_path}")
        return
    
    file_size = os.path.getsize(db_path)
    print(f"📁 DB 파일: {db_path}")
    print(f"📊 파일 크기: {file_size:,} bytes")
    
    if file_size == 0:
        print("❌ DB 파일이 비어있습니다")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 테이블 목록 확인
        tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
        tables = list(tables_df['name']) if not tables_df.empty else []
        print(f"📋 테이블 목록: {tables}")
        
        if 'market_data' in tables:
            # 전체 데이터 개수
            total_count = pd.read_sql_query("SELECT COUNT(*) as count FROM market_data", conn)
            print(f"📈 총 데이터 개수: {total_count.iloc[0]['count']}개")
            
            # 코인별 데이터 개수 (간단 버전)
            symbol_counts = pd.read_sql_query("""
                SELECT symbol, timeframe, COUNT(*) as count 
                FROM market_data 
                GROUP BY symbol, timeframe 
                ORDER BY symbol, timeframe
            """, conn)
            
            if not symbol_counts.empty:
                print("\n📊 코인별 데이터 현황:")
                for _, row in symbol_counts.iterrows():
                    print(f"   {row['symbol']} {row['timeframe']}: {row['count']}개")
                
                # 데이터 수집 기간 확인 (상세 버전)
                date_range = pd.read_sql_query("""
                    SELECT 
                        symbol,
                        timeframe,
                        MIN(timestamp) as start_date,
                        MAX(timestamp) as end_date,
                        COUNT(*) as count,
                        ROUND(JULIANDAY(MAX(timestamp)) - JULIANDAY(MIN(timestamp)), 1) as period_days
                    FROM market_data 
                    GROUP BY symbol, timeframe 
                    ORDER BY symbol, timeframe
                """, conn)
                
                print("\n📅 수집 기간별 데이터 현황:")
                for _, row in date_range.iterrows():
                    period_info = f"({row['period_days']}일간)" if row['period_days'] else ""
                    print(f"   {row['symbol']} {row['timeframe']}: {row['start_date']} ~ {row['end_date']} {period_info}")
                    print(f"     └─ 총 {row['count']}개 데이터")
                
                # 가장 오래된 데이터와 최신 데이터 확인
                oldest_data = pd.read_sql_query("""
                    SELECT timestamp, symbol, timeframe, open, close 
                    FROM market_data 
                    ORDER BY timestamp ASC 
                    LIMIT 1
                """, conn)
                
                newest_data = pd.read_sql_query("""
                    SELECT timestamp, symbol, timeframe, open, close 
                    FROM market_data 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, conn)
                
                if not oldest_data.empty and not newest_data.empty:
                    print(f"\n🕐 데이터 범위:")
                    oldest = oldest_data.iloc[0]
                    newest = newest_data.iloc[0]
                    print(f"   📅 가장 오래된 데이터: {oldest['timestamp']} ({oldest['symbol']}) - 시가 {oldest['open']:,}")
                    print(f"   📅 가장 최신 데이터: {newest['timestamp']} ({newest['symbol']}) - 종가 {newest['close']:,}")
                
                # 최근 데이터 샘플
                recent_data = pd.read_sql_query("""
                    SELECT timestamp, symbol, timeframe, open, high, low, close, volume 
                    FROM market_data 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                """, conn)
                
                print("\n📈 최근 저장된 데이터:")
                for _, row in recent_data.iterrows():
                    print(f"   {row['timestamp']} | {row['symbol']} {row['timeframe']} | "
                          f"O:{row['open']:,} H:{row['high']:,} L:{row['low']:,} C:{row['close']:,}")
            else:
                print("❌ 저장된 데이터가 없습니다")
        else:
            print("❌ market_data 테이블이 없습니다")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ DB 확인 실패: {e}")

def monitor_data_collection():
    """데이터 수집 모니터링"""
    print("\n" + "="*50)
    print("⏱️  데이터 수집 모니터링")
    print("="*50)
    print("백테스팅 UI에서 '📥 차트 데이터 수집' 버튼을 눌러보세요!")
    print("이 스크립트를 주기적으로 실행하여 데이터가 추가되는지 확인할 수 있습니다.")
    
    # 현재 시간 기록
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🕐 확인 시간: {current_time}")
    
    check_database_status()

def create_test_data():
    """테스트 데이터 생성 (실제 DB 스키마 확인용)"""
    print("\n" + "="*50)
    print("🧪 테스트 데이터 생성")
    print("="*50)
    
    try:
        # data 디렉토리 생성
        if not os.path.exists('data'):
            os.makedirs('data')
            print("✅ data 디렉토리 생성")
        
        db_path = "data/upbit_auto_trading.sqlite3"
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
        
        # 샘플 데이터 삽입
        sample_data = [
            ('2025-07-20 09:00:00', 'KRW-BTC', 161000000, 162000000, 160000000, 161500000, 100.5, '1d'),
            ('2025-07-19 09:00:00', 'KRW-BTC', 160000000, 161500000, 159000000, 161000000, 150.3, '1d'),
            ('2025-07-18 09:00:00', 'KRW-BTC', 159500000, 161000000, 158000000, 160000000, 200.7, '1d'),
        ]
        
        conn.executemany('''
            INSERT OR REPLACE INTO market_data 
            (timestamp, symbol, open, high, low, close, volume, timeframe) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)
        
        conn.commit()
        conn.close()
        
        print("✅ 테스트 데이터 생성 완료")
        print("📊 KRW-BTC 3일간의 샘플 데이터가 추가되었습니다")
        
    except Exception as e:
        print(f"❌ 테스트 데이터 생성 실패: {e}")

def main():
    """메인 함수"""
    print("📊 업비트 자동매매 데이터 수집 상태 확인")
    
    # 1. 현재 데이터베이스 상태 확인
    check_database_status()
    
    # 2. 테스트 데이터 생성 (DB가 비어있는 경우)
    db_path = "data/upbit_auto_trading.sqlite3"
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        create_test_data()
        check_database_status()
    
    # 3. 모니터링 안내
    monitor_data_collection()

if __name__ == "__main__":
    main()
