#!/usr/bin/env python3
"""
Market Data DB Schema Analyzer & Initializer v4.0

CandleDataProvider v4.0과 호환되는 market_data.sqlite3 스키마 분석 및 초기화 도구
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path


class MarketDataDBManager:
    """Market Data SQLite 데이터베이스 관리자"""

    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(exist_ok=True)

    def analyze_current_schema(self):
        """현재 스키마 분석"""
        print("📊 현재 market_data.sqlite3 스키마 분석:")
        print("=" * 60)

        if not os.path.exists(self.db_path):
            print(f"❌ 데이터베이스 파일이 존재하지 않습니다: {self.db_path}")
            print("🔧 새로운 데이터베이스가 초기화됩니다.")
            return

        conn = sqlite3.connect(self.db_path)

        # 모든 테이블 목록
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        print(f"🗂️ 총 테이블 수: {len(tables)}")

        total_records = 0
        candle_tables = []

        for table in tables:
            table_name = table[0]
            print(f"\n📋 테이블: {table_name}")

            # 테이블 구조
            schema = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            print("  🏗️ 스키마:")
            for col in schema:
                col_name, col_type, not_null, default, pk = col[1], col[2], col[3], col[4], col[5]
                pk_marker = " (PK)" if pk else ""
                not_null_marker = " NOT NULL" if not_null else ""
                default_marker = f" DEFAULT {default}" if default else ""
                print(f"    - {col_name}: {col_type}{pk_marker}{not_null_marker}{default_marker}")

            # 레코드 수
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                print(f"  📊 레코드 수: {count:,}")
                total_records += count

                # 캔들 테이블 식별
                if table_name.startswith("candles_"):
                    candle_tables.append((table_name, count))

            except Exception as e:
                print(f"  ❌ 레코드 수 조회 실패: {e}")

        print("\n📈 전체 통계:")
        print(f"  - 총 레코드 수: {total_records:,}")
        print(f"  - 캔들 테이블 수: {len(candle_tables)}")

        if candle_tables:
            print("\n🕯️ 캔들 테이블 상세:")
            for table_name, count in candle_tables:
                print(f"  - {table_name}: {count:,} 레코드")

        conn.close()

    def backup_existing_db(self):
        """기존 DB 백업"""
        if not os.path.exists(self.db_path):
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"market_data_backup_{timestamp}.sqlite3"

        import shutil
        shutil.copy2(self.db_path, backup_path)
        print(f"📦 기존 DB 백업 완료: {backup_path}")
        return backup_path

    def initialize_clean_schema(self):
        """CandleDataProvider v4.0 호환 깨끗한 스키마 초기화"""
        print("\n🔧 CandleDataProvider v4.0 호환 스키마 초기화:")
        print("=" * 60)

        # 기존 DB 백업
        backup_path = self.backup_existing_db()

        # 새로운 DB 생성
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        conn = sqlite3.connect(self.db_path)

        # WAL 모드 활성화 (성능 최적화)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")

        # 기본 테이블들 생성
        self._create_base_tables(conn)

        # 샘플 캔들 테이블 생성 (테스트용)
        self._create_sample_candle_tables(conn)

        conn.commit()
        conn.close()

        print("✅ 깨끗한 스키마 초기화 완료!")
        print(f"📊 데이터베이스 위치: {os.path.abspath(self.db_path)}")
        if backup_path:
            print(f"📦 백업 위치: {os.path.abspath(backup_path)}")

    def _create_base_tables(self, conn: sqlite3.Connection):
        """기본 테이블들 생성"""
        print("🏗️ 기본 테이블 생성...")

        # market_symbols 테이블 (심볼 관리)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS market_symbols (
            symbol TEXT PRIMARY KEY,
            base_currency TEXT NOT NULL,
            quote_currency TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 기본 심볼들 추가
        symbols = [
            ("KRW-BTC", "BTC", "KRW"),
            ("KRW-ETH", "ETH", "KRW"),
            ("KRW-XRP", "XRP", "KRW"),
            ("KRW-ADA", "ADA", "KRW"),
            ("KRW-DOT", "DOT", "KRW")
        ]

        conn.executemany("""
        INSERT OR IGNORE INTO market_symbols (symbol, base_currency, quote_currency)
        VALUES (?, ?, ?)
        """, symbols)

        print("  ✅ market_symbols 테이블 생성 완료")

    def _create_sample_candle_tables(self, conn: sqlite3.Connection):
        """샘플 캔들 테이블들 생성 (PRD v4.0 준수 스키마)"""
        print("🕯️ 샘플 캔들 테이블 생성...")

        # 주요 심볼과 타임프레임 조합
        sample_tables = [
            ("KRW-BTC", "1m"),
            ("KRW-BTC", "5m"),
            ("KRW-BTC", "1h"),
            ("KRW-ETH", "1m"),
            ("KRW-ETH", "5m")
        ]

        for symbol, timeframe in sample_tables:
            table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"

            # PRD v4.0 준수 스키마: candle_date_time_utc PRIMARY KEY
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                market TEXT NOT NULL,
                candle_date_time_utc DATETIME PRIMARY KEY,
                candle_date_time_kst DATETIME NOT NULL,
                opening_price DECIMAL(20,8) NOT NULL,
                high_price DECIMAL(20,8) NOT NULL,
                low_price DECIMAL(20,8) NOT NULL,
                trade_price DECIMAL(20,8) NOT NULL,
                timestamp BIGINT NOT NULL,
                candle_acc_trade_price DECIMAL(30,8) NOT NULL,
                candle_acc_trade_volume DECIMAL(30,8) NOT NULL,
                unit INTEGER DEFAULT 1,
                trade_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- 성능 최적화 인덱스
            CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp);
            CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at);
            CREATE INDEX IF NOT EXISTS idx_{table_name}_market ON {table_name}(market);
            """

            conn.executescript(create_sql)
            print(f"  ✅ {table_name} 테이블 생성 완료")

    def verify_schema_compliance(self):
        """PRD v4.0 스키마 준수 여부 검증"""
        print("\n🔍 PRD v4.0 스키마 준수 검증:")
        print("=" * 60)

        if not os.path.exists(self.db_path):
            print("❌ 데이터베이스 파일이 존재하지 않습니다.")
            return False

        conn = sqlite3.connect(self.db_path)

        # 캔들 테이블들 검사
        tables = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'candles_%'
        ORDER BY name
        """).fetchall()

        all_compliant = True

        for table in tables:
            table_name = table[0]
            print(f"\n📋 검증 중: {table_name}")

            # PRIMARY KEY 확인
            pragma_result = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            pk_columns = [row[1] for row in pragma_result if row[5] == 1]  # pk=1인 컬럼

            if pk_columns == ["candle_date_time_utc"]:
                print(f"  ✅ PRIMARY KEY: {pk_columns[0]}")
            else:
                print(f"  ❌ PRIMARY KEY 오류: {pk_columns} (예상: ['candle_date_time_utc'])")
                all_compliant = False

            # 필수 컬럼 확인
            required_columns = [
                "market", "candle_date_time_utc", "candle_date_time_kst",
                "opening_price", "high_price", "low_price", "trade_price",
                "timestamp", "candle_acc_trade_price", "candle_acc_trade_volume"
            ]

            existing_columns = [row[1] for row in pragma_result]
            missing_columns = [col for col in required_columns if col not in existing_columns]

            if not missing_columns:
                print(f"  ✅ 필수 컬럼: 모두 존재 ({len(required_columns)}개)")
            else:
                print(f"  ❌ 누락 컬럼: {missing_columns}")
                all_compliant = False

        conn.close()

        if all_compliant:
            print("\n🎉 모든 테이블이 PRD v4.0 스키마를 준수합니다!")
        else:
            print("\n⚠️ 일부 테이블이 PRD v4.0 스키마를 준수하지 않습니다.")

        return all_compliant

    def test_insert_or_ignore(self):
        """INSERT OR IGNORE 동작 테스트"""
        print("\n🧪 INSERT OR IGNORE 중복 방지 테스트:")
        print("=" * 60)

        if not os.path.exists(self.db_path):
            print("❌ 데이터베이스 파일이 존재하지 않습니다.")
            return

        conn = sqlite3.connect(self.db_path)

        # 테스트용 데이터
        test_table = "candles_KRW_BTC_1m"
        test_data = [
            ("KRW-BTC", "2024-01-01T10:00:00", "2024-01-01T19:00:00",
             50000, 51000, 49000, 50500, 1704099600, 1000000, 20.5, 1, 100),
            ("KRW-BTC", "2024-01-01T10:00:00", "2024-01-01T19:00:00",
             50000, 51000, 49000, 50500, 1704099600, 1000000, 20.5, 1, 100),  # 중복
            ("KRW-BTC", "2024-01-01T10:01:00", "2024-01-01T19:01:00",
             50500, 51500, 49500, 51000, 1704099660, 1000000, 20.5, 1, 100)
        ]

        # 기존 테스트 데이터 삭제
        conn.execute(f"DELETE FROM {test_table} WHERE market = 'KRW-BTC' AND candle_date_time_utc LIKE '2024-01-01%'")

        insert_sql = f"""
        INSERT OR IGNORE INTO {test_table} (
            market, candle_date_time_utc, candle_date_time_kst,
            opening_price, high_price, low_price, trade_price,
            timestamp, candle_acc_trade_price, candle_acc_trade_volume,
            unit, trade_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # INSERT OR IGNORE 실행
        conn.executemany(insert_sql, test_data)
        conn.commit()

        # 결과 확인
        count_query = (f"SELECT COUNT(*) FROM {test_table} "
                       f"WHERE market = 'KRW-BTC' AND candle_date_time_utc LIKE '2024-01-01%'")
        count = conn.execute(count_query).fetchone()[0]

        print("📊 테스트 결과:")
        print(f"  - 삽입 시도: {len(test_data)}개")
        print(f"  - 실제 저장: {count}개")
        print(f"  - 중복 무시: {len(test_data) - count}개")

        if count == 2:  # 중복 1개 제외하고 2개만 저장되어야 함
            print("✅ INSERT OR IGNORE 중복 방지 테스트 성공!")
        else:
            print("❌ INSERT OR IGNORE 중복 방지 테스트 실패!")

        # 테스트 데이터 정리
        conn.execute(f"DELETE FROM {test_table} WHERE market = 'KRW-BTC' AND candle_date_time_utc LIKE '2024-01-01%'")
        conn.commit()
        conn.close()


def main():
    """메인 실행 함수"""
    print("🚀 Market Data DB Schema Analyzer & Initializer v4.0")
    print("=" * 60)

    manager = MarketDataDBManager()

    print("\n옵션을 선택하세요:")
    print("1. 현재 스키마 분석")
    print("2. 깨끗한 DB 초기화 (기존 데이터 백업)")
    print("3. PRD v4.0 스키마 준수 검증")
    print("4. INSERT OR IGNORE 테스트")
    print("5. 전체 실행 (분석 → 초기화 → 검증 → 테스트)")

    choice = input("\n선택 (1-5): ").strip()

    if choice == "1":
        manager.analyze_current_schema()
    elif choice == "2":
        manager.initialize_clean_schema()
    elif choice == "3":
        manager.verify_schema_compliance()
    elif choice == "4":
        manager.test_insert_or_ignore()
    elif choice == "5":
        manager.analyze_current_schema()
        print("\n" + "=" * 60)
        manager.initialize_clean_schema()
        print("\n" + "=" * 60)
        manager.verify_schema_compliance()
        print("\n" + "=" * 60)
        manager.test_insert_or_ignore()
    else:
        print("❌ 잘못된 선택입니다.")


if __name__ == "__main__":
    main()
