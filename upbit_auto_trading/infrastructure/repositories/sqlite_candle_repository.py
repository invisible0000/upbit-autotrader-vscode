"""
SQLite 캔들 Repository 구현체

DDD Infrastructure Layer에서 CandleRepositoryInterface를 구현합니다.
DatabaseManager를 통해 올바른 DB 연결을 관리하고, FOREIGN KEY 제약을 해결합니다.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any

from upbit_auto_trading.domain.repositories.candle_repository_interface import CandleRepositoryInterface
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("SqliteCandleRepository")


class SqliteCandleRepository(CandleRepositoryInterface):
    """SQLite 기반 캔들 데이터 Repository"""

    def __init__(self, db_manager: DatabaseManager):
        """
        Args:
            db_manager: DatabaseManager 인스턴스 (의존성 주입)
        """
        self.db_manager = db_manager
        logger.info("SqliteCandleRepository 초기화 완료 - DatabaseManager 연결")

    async def ensure_symbol_exists(self, symbol: str) -> bool:
        """심볼이 market_symbols 테이블에 존재하는지 확인하고 없으면 등록"""
        try:
            with self.db_manager.get_connection("market_data") as conn:
                # 심볼 존재 여부 확인
                cursor = conn.execute("""
                    SELECT symbol FROM market_symbols WHERE symbol = ?
                """, (symbol,))

                if cursor.fetchone():
                    return True

                # 심볼이 없으면 자동 등록
                base_currency, quote_currency = symbol.split('-')
                conn.execute("""
                    INSERT OR IGNORE INTO market_symbols
                    (symbol, base_currency, quote_currency, is_active, created_at)
                    VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                """, (symbol, base_currency, quote_currency))

                logger.info(f"새로운 심볼 등록 완료: {symbol}")
                return True

        except Exception as e:
            logger.error(f"심볼 등록 실패 {symbol}: {e}")
            return False

    async def ensure_table_exists(self, symbol: str, timeframe: str) -> str:
        """캔들 테이블 존재 확인 및 생성"""
        # 먼저 심볼이 등록되어 있는지 확인
        if not await self.ensure_symbol_exists(symbol):
            raise ValueError(f"심볼 등록 실패: {symbol}")

        table_name = self._get_table_name(symbol, timeframe)

        if not await self.table_exists(symbol, timeframe):
            return await self._create_candle_table(symbol, timeframe)

        return table_name

    async def table_exists(self, symbol: str, timeframe: str) -> bool:
        """캔들 테이블 존재 여부 확인"""
        table_name = self._get_table_name(symbol, timeframe)

        try:
            with self.db_manager.get_connection("market_data") as conn:
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name=?
                """, (table_name,))
                return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"테이블 존재 여부 확인 실패 {table_name}: {e}")
            return False

    async def _create_candle_table(self, symbol: str, timeframe: str) -> str:
        """개별 캔들 테이블 생성"""
        table_name = self._get_table_name(symbol, timeframe)

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

        # 인덱스 생성 SQL
        create_indexes_sql = [
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp DESC);",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_kst_time ON {table_name}(candle_date_time_kst DESC);",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at);"
        ]

        # 데이터 유효성 검증 트리거
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

        # 테이블 상태 업데이트 트리거
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
            with self.db_manager.get_connection("market_data") as conn:
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

                logger.info(f"캔들 테이블 생성 완료: {table_name}")
                return table_name

        except Exception as e:
            logger.error(f"캔들 테이블 생성 실패 {table_name}: {e}")
            raise

    async def insert_candles(self, symbol: str, timeframe: str, candles: List[Dict]) -> int:
        """캔들 데이터 삽입"""
        if not candles:
            return 0

        table_name = await self.ensure_table_exists(symbol, timeframe)

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
            with self.db_manager.get_connection("market_data") as conn:
                cursor = conn.executemany(insert_sql, candle_tuples)
                inserted_count = cursor.rowcount

                logger.info(f"캔들 데이터 삽입 완료: {table_name}, {inserted_count}개")
                return inserted_count

        except Exception as e:
            logger.error(f"캔들 데이터 삽입 실패 {table_name}: {e}")
            raise

    async def get_candles(self,
                          symbol: str,
                          timeframe: str,
                          start_time: Optional[str] = None,
                          end_time: Optional[str] = None,
                          limit: Optional[int] = None) -> List[Dict]:
        """캔들 데이터 조회"""
        if not await self.table_exists(symbol, timeframe):
            return []

        table_name = self._get_table_name(symbol, timeframe)

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
            with self.db_manager.get_connection("market_data") as conn:
                cursor = conn.execute(query, params)
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"캔들 데이터 조회 실패 {table_name}: {e}")
            return []

    async def get_table_stats(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """특정 캔들 테이블 통계 조회"""
        table_name = self._get_table_name(symbol, timeframe)

        try:
            with self.db_manager.get_connection("market_data") as conn:
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

        except Exception as e:
            logger.error(f"테이블 통계 조회 실패 {table_name}: {e}")
            return None

    async def get_all_candle_tables(self) -> List[Dict[str, Any]]:
        """모든 캔들 테이블 목록 조회"""
        try:
            with self.db_manager.get_connection("market_data") as conn:
                cursor = conn.execute("""
                    SELECT
                        table_name, symbol, timeframe, record_count,
                        oldest_timestamp, newest_timestamp
                    FROM candle_tables
                    ORDER BY symbol, timeframe
                """)

                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"모든 캔들 테이블 조회 실패: {e}")
            return []

    def _get_table_name(self, symbol: str, timeframe: str) -> str:
        """심볼과 타임프레임으로 테이블명 생성"""
        return f"candles_{symbol.replace('-', '_')}_{timeframe}"

    # === 수집 상태 관리 메서드 (Smart Candle Collector 기능) ===

    async def get_collection_status(
        self,
        symbol: str,
        timeframe: str,
        target_time: datetime
    ) -> Optional[Dict[str, Any]]:
        """특정 시간의 수집 상태 조회"""
        try:
            with self.db_manager.get_connection("market_data") as conn:
                cursor = conn.execute("""
                    SELECT id, symbol, timeframe, target_time, collection_status,
                           last_attempt_at, attempt_count, api_response_code,
                           created_at, updated_at
                    FROM candle_collection_status
                    WHERE symbol = ? AND timeframe = ? AND target_time = ?
                """, (symbol, timeframe, target_time.isoformat()))

                row = cursor.fetchone()
                if not row:
                    return None

                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))

        except Exception as e:
            logger.error(f"수집 상태 조회 실패: {symbol} {timeframe} {target_time}, {e}")
            return None

    async def update_collection_status(
        self,
        symbol: str,
        timeframe: str,
        target_time: datetime,
        status: str,
        api_response_code: Optional[int] = None
    ) -> None:
        """수집 상태 업데이트"""
        try:
            with self.db_manager.get_connection("market_data") as conn:
                cursor = conn.cursor()

                # UPSERT 쿼리
                cursor.execute("""
                    INSERT INTO candle_collection_status (
                        symbol, timeframe, target_time, collection_status,
                        last_attempt_at, attempt_count, api_response_code,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(symbol, timeframe, target_time) DO UPDATE SET
                        collection_status = excluded.collection_status,
                        last_attempt_at = excluded.last_attempt_at,
                        attempt_count = attempt_count + 1,
                        api_response_code = excluded.api_response_code,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    symbol,
                    timeframe,
                    target_time.isoformat(),
                    status,
                    datetime.now().isoformat(),
                    api_response_code
                ))

                conn.commit()
                logger.debug(f"수집 상태 업데이트: {symbol} {timeframe} {target_time} -> {status}")

        except Exception as e:
            logger.error(f"수집 상태 업데이트 실패: {symbol} {timeframe} {target_time}, {e}")
            raise

    async def get_missing_candle_times(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[datetime]:
        """미수집 캔들 시간 목록 조회"""
        from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.processing.time_utils import (
            generate_candle_times
        )

        try:
            # 예상되는 모든 캔들 시간 생성
            expected_times = generate_candle_times(start_time, end_time, timeframe)

            if not expected_times:
                return []

            # DB에서 수집 상태 조회
            with self.db_manager.get_connection("market_data") as conn:
                cursor = conn.cursor()

                # IN 절을 위한 placeholder 생성
                placeholders = ','.join(['?' for _ in expected_times])
                time_strings = [t.isoformat() for t in expected_times]

                cursor.execute(f"""
                    SELECT target_time, collection_status
                    FROM candle_collection_status
                    WHERE symbol = ? AND timeframe = ?
                    AND target_time IN ({placeholders})
                """, [symbol, timeframe] + time_strings)

                existing_statuses = {
                    datetime.fromisoformat(row[0]): row[1]
                    for row in cursor.fetchall()
                }

            # 미수집 시간 필터링
            missing_times = []
            for time in expected_times:
                status = existing_statuses.get(time)
                if status is None or status in ['PENDING', 'FAILED']:
                    missing_times.append(time)

            return missing_times

        except Exception as e:
            logger.error(f"미수집 캔들 시간 조회 실패: {symbol} {timeframe}, {e}")
            return []

    async def get_empty_candle_times(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[datetime]:
        """빈 캔들 시간 목록 조회"""
        try:
            with self.db_manager.get_connection("market_data") as conn:
                cursor = conn.execute("""
                    SELECT target_time
                    FROM candle_collection_status
                    WHERE symbol = ? AND timeframe = ?
                    AND collection_status = 'EMPTY'
                    AND target_time BETWEEN ? AND ?
                    ORDER BY target_time
                """, (
                    symbol,
                    timeframe,
                    start_time.isoformat(),
                    end_time.isoformat()
                ))

                return [datetime.fromisoformat(row[0]) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"빈 캔들 시간 조회 실패: {symbol} {timeframe}, {e}")
            return []

    async def get_continuous_candles(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        include_empty: bool = True
    ) -> List[Dict[str, Any]]:
        """연속된 캔들 데이터 조회 (빈 캔들 포함/제외 선택 가능)"""
        try:
            if include_empty:
                # 차트용: CollectionStatusManager 사용
                from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.processing import (
                    collection_status_manager
                )

                db_path = "data/market_data.sqlite3"  # 기본 경로 사용
                collection_manager = collection_status_manager.CollectionStatusManager(db_path)

                # 실제 캔들 데이터 조회
                actual_candles = await self.get_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat()
                )

                # 빈 캔들 채움
                continuous_candles = collection_manager.fill_empty_candles(
                    candles=actual_candles,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_time=start_time,
                    end_time=end_time
                )

                # CandleWithStatus를 Dict로 변환
                result = []
                for candle_with_status in continuous_candles:
                    candle_dict = {
                        'market': candle_with_status.market,
                        'candle_date_time_utc': candle_with_status.candle_date_time_utc.isoformat() + 'Z',
                        'candle_date_time_kst': candle_with_status.candle_date_time_kst.isoformat() + 'Z',
                        'opening_price': float(candle_with_status.opening_price),
                        'high_price': float(candle_with_status.high_price),
                        'low_price': float(candle_with_status.low_price),
                        'trade_price': float(candle_with_status.trade_price),
                        'timestamp': candle_with_status.timestamp,
                        'candle_acc_trade_price': float(candle_with_status.candle_acc_trade_price),
                        'candle_acc_trade_volume': float(candle_with_status.candle_acc_trade_volume),
                        'unit': candle_with_status.unit,
                        'is_empty': candle_with_status.is_empty,
                        'collection_status': candle_with_status.collection_status.value
                    }
                    result.append(candle_dict)

                return result

            else:
                # 지표용: 기존 get_candles 사용 (실제 거래 데이터만)
                return await self.get_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat()
                )

        except Exception as e:
            logger.error(f"연속 캔들 조회 실패: {symbol} {timeframe}, {e}")
            return []
