#!/usr/bin/env python3
"""
DB 구조 및 테이블 확인 스크립트
- 데이터베이스 파일 존재 여부 확인
- 테이블 목록 및 구조 확인
- 데이터 개수 확인
- trading_strategies 테이블이 없으면 생성
"""

import sqlite3
import os
from datetime import datetime

def check_db_files():
    """DB 파일들 확인"""
    print("=== DB 파일 확인 ===")
    
    db_files = [
        'data/upbit_auto_trading.db',
        'data/upbit_auto_trading.sqlite3'
    ]
    
    existing_files = []
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"✅ 발견: {db_file}")
            size = os.path.getsize(db_file)
            print(f"   📁 크기: {size:,} bytes")
            existing_files.append(db_file)
        else:
            print(f"❌ 없음: {db_file}")
    
    return existing_files

def check_table_structure(db_file):
    """테이블 구조 확인"""
    print(f"\n=== {db_file} 테이블 구조 ===")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 테이블 목록 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ 테이블이 없습니다!")
            return False
        
        print(f"📋 테이블 목록: {[t[0] for t in tables]}")
        
        # 각 테이블의 구조 확인
        for table in tables:
            table_name = table[0]
            print(f"\n📊 {table_name} 테이블:")
            
            # 컬럼 정보
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                print(f"   - {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")
            
            # 데이터 개수
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📈 데이터 개수: {count:,}개")
            
            # trading_strategies 테이블이면 샘플 데이터도 확인
            if table_name == 'trading_strategies' and count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_data = cursor.fetchall()
                print(f"   🔍 샘플 데이터:")
                for i, row in enumerate(sample_data, 1):
                    print(f"      {i}. {row}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ {db_file} 확인 중 오류: {e}")
        return False

def create_trading_strategies_table(db_file):
    """trading_strategies 테이블 생성"""
    print(f"\n=== {db_file}에 trading_strategies 테이블 생성 ===")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 테이블 생성 SQL
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS trading_strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            strategy_type TEXT NOT NULL,
            signal_type TEXT DEFAULT 'BUY/SELL',
            parameters TEXT,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        
        # 인덱스 생성
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_strategy_id ON trading_strategies(strategy_id)",
            "CREATE INDEX IF NOT EXISTS idx_strategy_type ON trading_strategies(strategy_type)",
            "CREATE INDEX IF NOT EXISTS idx_signal_type ON trading_strategies(signal_type)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        conn.close()
        
        print("✅ trading_strategies 테이블 생성 완료")
        return True
        
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        return False

def add_sample_strategies(db_file):
    """샘플 전략 데이터 추가"""
    print(f"\n=== {db_file}에 샘플 전략 추가 ===")
    
    sample_strategies = [
        {
            'strategy_id': 'entry_ma_cross_01',
            'name': '이동평균 교차 (예제)',
            'strategy_type': '이동평균 교차',
            'signal_type': 'BUY/SELL',
            'parameters': '{"short_period": 5, "long_period": 20, "ma_type": "SMA", "enabled": true}',
            'description': '단기 이동평균이 장기 이동평균을 상향/하향 돌파하는 신호'
        },
        {
            'strategy_id': 'entry_rsi_01',
            'name': 'RSI 과매수/과매도 (예제)',
            'strategy_type': 'RSI 과매수/과매도',
            'signal_type': 'BUY/SELL',
            'parameters': '{"period": 14, "oversold_threshold": 30.0, "overbought_threshold": 70.0, "enabled": true}',
            'description': 'RSI 지표를 이용한 과매수/과매도 구간 신호'
        },
        {
            'strategy_id': 'mgmt_trailing_stop_01',
            'name': '트레일링 스탑 (예제)',
            'strategy_type': '트레일링 스탑',
            'signal_type': 'MANAGEMENT',
            'parameters': '{"trailing_percent": 5.0, "min_profit_percent": 2.0, "enabled": true}',
            'description': '수익이 발생한 상태에서 일정 비율 하락 시 자동 매도'
        },
        {
            'strategy_id': 'mgmt_time_based_01',
            'name': '시간 기반 청산 (예제)',
            'strategy_type': '시간 기반 청산',
            'signal_type': 'MANAGEMENT',
            'parameters': '{"max_hold_hours": 24, "force_close": true, "enabled": true}',
            'description': '일정 시간 보유 후 강제 청산'
        }
    ]
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 기존 데이터 확인
        cursor.execute("SELECT COUNT(*) FROM trading_strategies")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"📋 기존 전략 {existing_count}개 발견. 샘플 추가를 건너뜁니다.")
            conn.close()
            return True
        
        # 샘플 데이터 삽입
        insert_sql = """
        INSERT INTO trading_strategies 
        (strategy_id, name, strategy_type, signal_type, parameters, description, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        current_time = datetime.now().isoformat()
        
        for strategy in sample_strategies:
            cursor.execute(insert_sql, (
                strategy['strategy_id'],
                strategy['name'],
                strategy['strategy_type'],
                strategy['signal_type'],
                strategy['parameters'],
                strategy['description'],
                current_time,
                current_time
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 샘플 전략 {len(sample_strategies)}개 추가 완료")
        return True
        
    except Exception as e:
        print(f"❌ 샘플 전략 추가 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("🔍 DB 구조 및 테이블 확인 도구")
    print("=" * 50)
    
    # 1. DB 파일 확인
    existing_files = check_db_files()
    
    if not existing_files:
        print("\n❌ DB 파일이 없습니다!")
        
        # data 디렉토리 생성
        os.makedirs('data', exist_ok=True)
        
        # 기본 DB 파일 생성
        default_db = 'data/upbit_auto_trading.db'
        print(f"\n🔧 {default_db} 생성 중...")
        
        if create_trading_strategies_table(default_db):
            add_sample_strategies(default_db)
            existing_files = [default_db]
        else:
            return
    
    # 2. 각 DB 파일의 구조 확인
    trading_strategies_exists = False
    target_db = None
    
    for db_file in existing_files:
        has_table = check_table_structure(db_file)
        
        # trading_strategies 테이블 존재 확인
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trading_strategies'")
            if cursor.fetchone():
                trading_strategies_exists = True
                target_db = db_file
            conn.close()
        except:
            pass
    
    # 3. trading_strategies 테이블이 없으면 생성
    if not trading_strategies_exists:
        print(f"\n❌ trading_strategies 테이블이 없습니다!")
        
        # 첫 번째 DB 파일을 타겟으로 설정
        target_db = existing_files[0] if existing_files else 'data/upbit_auto_trading.db'
        
        if create_trading_strategies_table(target_db):
            add_sample_strategies(target_db)
            check_table_structure(target_db)  # 다시 확인
    else:
        print(f"\n✅ trading_strategies 테이블 발견: {target_db}")
    
    print("\n" + "=" * 50)
    print("🏁 DB 확인 완료!")
    print("=" * 50)

if __name__ == "__main__":
    main()
