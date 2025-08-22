"""
동적 캔들 테이블 관리자
개별 심볼별, 타임프레임별 캔들 테이블을 동적으로 생성하고 관리합니다.
"""
import sqlite3
from typing import List, Dict, Optional
from pathlib import Path

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("CandleTableManager")


class CandleTableManager:
    """캔들 테이블 동적 생성 및 관리"""

    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """DB 연결 생성"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def create_candle_table(self, symbol: str, timeframe: str) -> str:
        """개별 캔들 테이블 생성

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1h')

        Returns:
            생성된 테이블명
        """
        # 테이블명 생성 (하이픈을 언더스코어로 변경)
        table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"

        # 캔들 테이블 생성 SQL (업비트 API 완전 호환)
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- 업비트 API 응답과 100% 동일한 필드명
            market TEXT NOT NULL,
            candle_date_time_utc TEXT NOT NULL,
            candle_date_time_kst TEXT NOT NULL,
            opening_price REAL NOT NULL,
            high_price REAL NOT NULL,
            low_price REAL NOT NULL,
            trade_price REAL NOT NULL,
            timestamp INTEGER NOT NULL,
            candle_acc_trade_price REAL NOT NULL,
            candle_acc_trade_volume REAL NOT NULL,
            unit INTEGER NOT NULL,
            trade_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- 유니크 제약 (동일한 타임스탬프 중복 방지)
            UNIQUE(candle_date_time_kst),
            UNIQUE(timestamp)
        );
        """

        # 인덱스 생성 SQL (업비트 API 필드명 사용)
        create_indexes_sql = [
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp DESC);",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_kst_time ON {table_name}(candle_date_time_kst DESC);",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at);"
        ]

        # 데이터 유효성 검증 트리거 (업비트 API 필드명 사용)
        create_trigger_sql = f"""
        CREATE TRIGGER IF NOT EXISTS validate_{table_name}
            BEFORE INSERT ON {table_name}
            FOR EACH ROW
        BEGIN
            SELECT CASE
                WHEN NEW.opening_price <= 0 OR NEW.high_price <= 0 OR
                     NEW.low_price <= 0 OR NEW.trade_price <= 0 THEN
                    RAISE(ABORT, 'Invalid price: all prices must be positive')
                WHEN NEW.high_price < NEW.low_price THEN
                    RAISE(ABORT, 'Invalid price: high price cannot be less than low price')
                WHEN NEW.high_price < NEW.opening_price OR NEW.high_price < NEW.trade_price THEN
                    RAISE(ABORT, 'Invalid price: high price must be >= opening and trade price')
                WHEN NEW.low_price > NEW.opening_price OR NEW.low_price > NEW.trade_price THEN
                    RAISE(ABORT, 'Invalid price: low price must be <= opening and trade price')
                WHEN NEW.candle_acc_trade_volume < 0 OR NEW.candle_acc_trade_price < 0 THEN
                    RAISE(ABORT, 'Invalid volume: volume cannot be negative')
            END;
        END;
        """

        # 테이블 상태 업데이트 트리거 (업비트 API 필드명 사용)
        update_stats_trigger_sql = f"""
        CREATE TRIGGER IF NOT EXISTS update_stats_{table_name}
            AFTER INSERT ON {table_name}
            FOR EACH ROW
        BEGIN
            INSERT OR REPLACE INTO candle_tables (
                table_name, symbol, timeframe, last_update_at,
                record_count, oldest_timestamp, newest_timestamp
            )
            SELECT
                '{table_name}',
                '{symbol}',
                '{timeframe}',
                CURRENT_TIMESTAMP,
                COUNT(*),
                MIN(candle_date_time_kst),
                MAX(candle_date_time_kst)
            FROM {table_name};
        END;
        """

        try:
            with self.get_connection() as conn:
                # 테이블 생성
                conn.execute(create_table_sql)

                # 인덱스 생성
                for index_sql in create_indexes_sql:
                    conn.execute(index_sql)

                # 트리거 생성
                conn.execute(create_trigger_sql)
                conn.execute(update_stats_trigger_sql)

                # candle_tables에 등록
                conn.execute("""
                    INSERT OR IGNORE INTO candle_tables
                    (table_name, symbol, timeframe, record_count)
                    VALUES (?, ?, ?, 0)
                """, (table_name, symbol, timeframe))

                conn.commit()
                logger.info(f"캔들 테이블 생성 완료: {table_name}")

        except Exception as e:
            logger.error(f"캔들 테이블 생성 실패 {table_name}: {e}")
            raise

        return table_name

    def get_table_name(self, symbol: str, timeframe: str) -> str:
        """심볼과 타임프레임으로 테이블명 생성"""
        return f"candles_{symbol.replace('-', '_')}_{timeframe}"

    def table_exists(self, symbol: str, timeframe: str) -> bool:
        """테이블 존재 여부 확인"""
        table_name = self.get_table_name(symbol, timeframe)

        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table_name,))
            return cursor.fetchone() is not None

    def ensure_table_exists(self, symbol: str, timeframe: str) -> str:
        """테이블이 없으면 생성, 있으면 테이블명 반환"""
        if not self.table_exists(symbol, timeframe):
            return self.create_candle_table(symbol, timeframe)
        return self.get_table_name(symbol, timeframe)

    def get_all_candle_tables(self) -> List[Dict[str, any]]:
        """모든 캔들 테이블 목록 조회"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    table_name, symbol, timeframe, record_count,
                    oldest_timestamp, newest_timestamp
                FROM candle_tables
                ORDER BY symbol, timeframe
            """)

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_table_stats(self, symbol: str, timeframe: str) -> Optional[Dict[str, any]]:
        """특정 테이블 통계 조회"""
        table_name = self.get_table_name(symbol, timeframe)

        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    table_name, symbol, timeframe, record_count,
                    oldest_timestamp, newest_timestamp, data_quality_score,
                    last_update_at
                FROM candle_tables
                WHERE table_name = ?
            """, (table_name,))

            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
        return None

    def update_table_stats(self, symbol: str, timeframe: str) -> None:
        """테이블 통계 수동 업데이트"""
        table_name = self.get_table_name(symbol, timeframe)

        if not self.table_exists(symbol, timeframe):
            logger.warning(f"테이블이 존재하지 않음: {table_name}")
            return

        with self.get_connection() as conn:
            # 실제 테이블에서 통계 계산
            cursor = conn.execute(f"""
                SELECT
                    COUNT(*) as record_count,
                    MIN(timestamp) as oldest_timestamp,
                    MAX(timestamp) as newest_timestamp
                FROM {table_name}
            """)

            stats = cursor.fetchone()
            if stats:
                conn.execute("""
                    UPDATE candle_tables
                    SET record_count = ?,
                        oldest_timestamp = ?,
                        newest_timestamp = ?,
                        last_update_at = CURRENT_TIMESTAMP
                    WHERE table_name = ?
                """, (*stats, table_name))

                conn.commit()
                logger.info(f"테이블 통계 업데이트 완료: {table_name}")

    def insert_candles(self, symbol: str, timeframe: str, candles: List[Dict]) -> int:
        """캔들 데이터 삽입

        Args:
            symbol: 심볼
            timeframe: 타임프레임
            candles: 캔들 데이터 리스트

        Returns:
            삽입된 레코드 수
        """
        table_name = self.ensure_table_exists(symbol, timeframe)

        if not candles:
            return 0

        insert_sql = f"""
            INSERT OR REPLACE INTO {table_name}
            (market, candle_date_time_utc, candle_date_time_kst,
             opening_price, high_price, low_price, trade_price,
             timestamp, candle_acc_trade_price, candle_acc_trade_volume, unit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        candle_tuples = []
        for candle in candles:
            candle_tuples.append((
                candle['market'],
                candle['candle_date_time_utc'],
                candle['candle_date_time_kst'],
                candle['opening_price'],
                candle['high_price'],
                candle['low_price'],
                candle['trade_price'],
                candle['timestamp'],
                candle['candle_acc_trade_price'],
                candle['candle_acc_trade_volume'],
                candle['unit']
            ))

        try:
            with self.get_connection() as conn:
                cursor = conn.executemany(insert_sql, candle_tuples)
                conn.commit()

                inserted_count = cursor.rowcount
                logger.info(f"캔들 데이터 삽입 완료: {table_name}, {inserted_count}개")
                return inserted_count

        except Exception as e:
            logger.error(f"캔들 데이터 삽입 실패 {table_name}: {e}")
            raise

    def get_candles(self,
                   symbol: str,
                   timeframe: str,
                   start_time: Optional[str] = None,
                   end_time: Optional[str] = None,
                   limit: Optional[int] = None) -> List[Dict]:
        """캔들 데이터 조회

        Args:
            symbol: 심볼
            timeframe: 타임프레임
            start_time: 시작 시간 (ISO format)
            end_time: 종료 시간 (ISO format)
            limit: 최대 조회 개수

        Returns:
            캔들 데이터 리스트
        """
        table_name = self.get_table_name(symbol, timeframe)

        if not self.table_exists(symbol, timeframe):
            return []

        # 쿼리 조건 구성
        conditions = []
        params = []

        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time)

        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time)

        where_clause = ""
        if conditions:
            where_clause = f"WHERE {' AND '.join(conditions)}"

        limit_clause = ""
        if limit:
            limit_clause = f"LIMIT {limit}"

        query = f"""
            SELECT
                market, candle_date_time_utc, candle_date_time_kst,
                opening_price, high_price, low_price, trade_price,
                timestamp, candle_acc_trade_price, candle_acc_trade_volume,
                unit, created_at
            FROM {table_name}
            {where_clause}
            ORDER BY timestamp DESC
            {limit_clause}
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"캔들 데이터 조회 실패 {table_name}: {e}")
            return []

    def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """오래된 실시간 데이터 정리"""
        cleanup_queries = [
            f"""
            DELETE FROM real_time_tickers
            WHERE updated_at < datetime('now', '-{days_to_keep} days')
            """,
            f"""
            DELETE FROM real_time_orderbooks
            WHERE updated_at < datetime('now', '-{days_to_keep} days')
            """
        ]

        try:
            with self.get_connection() as conn:
                for query in cleanup_queries:
                    cursor = conn.execute(query)
                    if cursor.rowcount > 0:
                        logger.info(f"오래된 데이터 정리: {cursor.rowcount}개 삭제")
                conn.commit()

        except Exception as e:
            logger.error(f"데이터 정리 실패: {e}")


# 편의 함수들
def create_candle_table(symbol: str, timeframe: str) -> str:
    """캔들 테이블 생성 편의 함수"""
    manager = CandleTableManager()
    return manager.create_candle_table(symbol, timeframe)

def ensure_candle_table(symbol: str, timeframe: str) -> str:
    """캔들 테이블 존재 확인 및 생성 편의 함수"""
    manager = CandleTableManager()
    return manager.ensure_table_exists(symbol, timeframe)

def get_all_tables() -> List[Dict[str, any]]:
    """모든 캔들 테이블 조회 편의 함수"""
    manager = CandleTableManager()
    return manager.get_all_candle_tables()
