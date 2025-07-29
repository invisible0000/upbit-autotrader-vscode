"""
데이터베이스 초기화 모듈

프로그램 최초 실행 시 또는 DB 파일이 없을 때 기본 데이터베이스 파일들을 생성합니다.
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Tuple


def ensure_data_directory():
    """데이터 디렉토리가 존재하는지 확인하고 없으면 생성"""
    data_dir = Path("upbit_auto_trading/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def create_basic_settings_db(db_path: str):
    """기본 설정 데이터베이스 생성"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 기본 설정 테이블들 생성
    tables = [
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            theme TEXT DEFAULT 'light',
            language TEXT DEFAULT 'ko',
            notifications_enabled BOOLEAN DEFAULT 1,
            auto_backup BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS api_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exchange TEXT DEFAULT 'upbit',
            api_key_encrypted TEXT,
            secret_key_encrypted TEXT,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
    
    # 기본 설정값 삽입
    default_settings = [
        ('app_version', '1.0.0', '애플리케이션 버전'),
        ('database_version', '1.0.0', '데이터베이스 스키마 버전'),
        ('first_run', '1', '최초 실행 여부'),
        ('backup_interval_days', '7', '백업 주기 (일)'),
        ('log_level', 'INFO', '로그 레벨'),
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO app_settings (key, value, description) VALUES (?, ?, ?)",
        default_settings
    )
    
    # 기본 사용자 설정 삽입
    cursor.execute(
        """INSERT OR IGNORE INTO user_preferences 
           (user_id, theme, language, notifications_enabled, auto_backup) 
           VALUES ('default', 'light', 'ko', 1, 1)"""
    )
    
    conn.commit()
    conn.close()


def create_basic_strategies_db(db_path: str):
    """기본 전략 데이터베이스 생성"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 기본 전략 테이블들 생성
    tables = [
        """
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            strategy_type TEXT DEFAULT 'custom',
            is_active BOOLEAN DEFAULT 0,
            parameters TEXT,  -- JSON 형태로 저장
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS strategy_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER,
            symbol TEXT,
            action TEXT,  -- buy, sell
            quantity REAL,
            price REAL,
            status TEXT DEFAULT 'pending',
            executed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES strategies (id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS strategy_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER,
            total_profit REAL DEFAULT 0,
            total_trades INTEGER DEFAULT 0,
            win_rate REAL DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES strategies (id)
        )
        """
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
    
    # 기본 전략 예시 삽입
    cursor.execute(
        """INSERT OR IGNORE INTO strategies 
           (name, description, strategy_type, parameters) 
           VALUES ('기본 RSI 전략', 'RSI 지표를 활용한 기본 매매 전략', 'rsi', 
                   '{"rsi_period": 14, "buy_threshold": 30, "sell_threshold": 70}')"""
    )
    
    conn.commit()
    conn.close()


def create_basic_market_data_db(db_path: str):
    """기본 시장 데이터 데이터베이스 생성"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 기본 시장 데이터 테이블들 생성
    tables = [
        """
        CREATE TABLE IF NOT EXISTS market_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            close_price REAL,
            volume REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS supported_symbols (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            korean_name TEXT,
            english_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS data_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT UNIQUE NOT NULL,
            cache_value TEXT,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
    
    # 기본 지원 코인 삽입
    default_symbols = [
        ('KRW-BTC', '비트코인', 'Bitcoin'),
        ('KRW-ETH', '이더리움', 'Ethereum'),
        ('KRW-XRP', '리플', 'Ripple'),
        ('KRW-ADA', '에이다', 'Cardano'),
        ('KRW-DOT', '폴카닷', 'Polkadot'),
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO supported_symbols (symbol, korean_name, english_name) VALUES (?, ?, ?)",
        default_symbols
    )
    
    conn.commit()
    conn.close()


def initialize_default_databases() -> List[Tuple[str, bool]]:
    """기본 데이터베이스 파일들을 초기화"""
    
    # 데이터 디렉토리 확인/생성
    data_dir = ensure_data_directory()
    
    # 생성할 데이터베이스 정보
    databases = [
        ("settings.sqlite3", create_basic_settings_db),
        ("strategies.sqlite3", create_basic_strategies_db),
        ("market_data.sqlite3", create_basic_market_data_db),
    ]
    
    results = []
    
    for db_name, create_function in databases:
        db_path = data_dir / db_name
        
        try:
            if not db_path.exists():
                print(f"📊 {db_name} 데이터베이스 생성 중...")
                create_function(str(db_path))
                results.append((db_name, True))
                print(f"✅ {db_name} 생성 완료")
            else:
                print(f"ℹ️ {db_name} 이미 존재함")
                results.append((db_name, False))
        except Exception as e:
            print(f"❌ {db_name} 생성 실패: {e}")
            results.append((db_name, False))
    
    return results


def check_and_repair_databases() -> bool:
    """데이터베이스 파일들의 무결성을 확인하고 필요시 복구"""
    
    data_dir = Path("upbit_auto_trading/data")
    db_files = ["settings.sqlite3", "strategies.sqlite3", "market_data.sqlite3"]
    
    all_healthy = True
    
    for db_name in db_files:
        db_path = data_dir / db_name
        
        if not db_path.exists():
            print(f"⚠️ {db_name} 파일이 없습니다. 생성합니다...")
            initialize_default_databases()
            continue
        
        try:
            # 간단한 연결 테스트
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            conn.close()
            print(f"✅ {db_name} 정상")
            
        except Exception as e:
            print(f"❌ {db_name} 손상됨: {e}")
            print(f"🔧 {db_name} 백업 후 재생성합니다...")
            
            # 손상된 파일 백업
            backup_path = db_path.with_suffix(f".backup_{int(os.path.getmtime(db_path))}.sqlite3")
            if db_path.exists():
                db_path.rename(backup_path)
            
            # 새로 생성
            initialize_default_databases()
            all_healthy = False
    
    return all_healthy


if __name__ == "__main__":
    print("🚀 데이터베이스 초기화 시작...")
    results = initialize_default_databases()
    
    print("\n📋 초기화 결과:")
    for db_name, created in results:
        status = "생성됨" if created else "기존재"
        print(f"  - {db_name}: {status}")
    
    print("\n🔍 데이터베이스 무결성 검사...")
    healthy = check_and_repair_databases()
    
    if healthy:
        print("✅ 모든 데이터베이스가 정상입니다.")
    else:
        print("⚠️ 일부 데이터베이스가 복구되었습니다.")
    
    print("🏁 초기화 완료!")
