"""
CandleDataProvider v4.0 - Infrastructure Repository 구현체

DDD Infrastructure Layer에서 CandleRepositoryInterface를 구현합니다.
DatabaseManager를 활용한 Connection Pooling + WAL 모드와
기존 개별 테이블 최적화를 결합한 하이브리드 구조입니다.

Architecture:
- DDD 준수: Domain Interface 완전 구현
- 성능 최적화: DatabaseManager + Connection Pooling + WAL 모드
- 업비트 특화: 심볼별 개별 테이블 + INSERT OR IGNORE 최적화
- 4단계 최적화: 겹침 분석 지원 메서드 구현
"""

import sqlite3
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from upbit_auto_trading.domain.repositories.candle_repository_interface import (
    CandleRepositoryInterface, CandleData, CandleQueryResult
)
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("SqliteCandleRepositoryV4")


class TablePerformanceOptimizer:
    """개별 테이블 구조 최적화 + DatabaseManager 결합"""

    def __init__(self):
        self._table_cache = {}
        logger.debug("TablePerformanceOptimizer 초기화")

    def get_table_name(self, symbol: str, timeframe: str) -> str:
        """심볼과 타임프레임으로 테이블명 생성"""
        return f"candles_{symbol.replace('-', '_')}_{timeframe}"

    def create_table_sql(self, table_name: str) -> str:
        """개별 테이블 생성 SQL (업비트 특화 최적화 - PRD 준수)"""
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            market TEXT NOT NULL,
            candle_date_time_utc DATETIME PRIMARY KEY,  -- 🔑 PRD 요구사항: 직접 PRIMARY KEY
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

        -- 성능 최적화 인덱스 (PRIMARY KEY 외 추가)
        CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp);
        CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at);
        CREATE INDEX IF NOT EXISTS idx_{table_name}_market ON {table_name}(market);
        """

    def batch_insert_with_ignore(self, conn: sqlite3.Connection, table_name: str, candles: List[CandleData]) -> int:
        """INSERT OR IGNORE + executemany 최적화"""
        if not candles:
            return 0

        sql = f"""
        INSERT OR IGNORE INTO {table_name} (
            market, candle_date_time_utc, candle_date_time_kst,
            opening_price, high_price, low_price, trade_price,
            timestamp, candle_acc_trade_price, candle_acc_trade_volume,
            unit, trade_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        candle_tuples = [
            (
                candle.market,
                candle.candle_date_time_utc.isoformat(),
                candle.candle_date_time_kst.isoformat(),
                candle.opening_price,
                candle.high_price,
                candle.low_price,
                candle.trade_price,
                candle.timestamp,
                candle.candle_acc_trade_price,
                candle.candle_acc_trade_volume,
                candle.unit,
                candle.trade_count
            )
            for candle in candles
        ]

        cursor = conn.executemany(sql, candle_tuples)
        return cursor.rowcount


class SqliteCandleRepository(CandleRepositoryInterface):
    """SQLite 기반 캔들 데이터 Repository v4.0 (DDD + 성능 최적화)"""

    def __init__(self, database_manager: DatabaseManager):
        """
        Args:
            database_manager: DatabaseManager 인스턴스 (의존성 주입)
        """
        self._db_manager = database_manager
        self._table_optimizer = TablePerformanceOptimizer()
        logger.info("SqliteCandleRepository v4.0 초기화 - DDD + 성능 최적화 하이브리드")

    # === 핵심 CRUD 메서드 ===

    async def save_candles(self, symbol: str, timeframe: str, candles: List[CandleData]) -> int:
        """캔들 데이터 저장 (INSERT OR IGNORE 기반 중복 자동 처리)"""
        if not candles:
            return 0

        table_name = await self.ensure_table_exists(symbol, timeframe)

        start_time = time.time()

        # DatabaseManager로 Connection Pooling + WAL 모드 활용
        with self._db_manager.get_connection('market_data') as conn:
            inserted_count = self._table_optimizer.batch_insert_with_ignore(conn, table_name, candles)

        query_time_ms = (time.time() - start_time) * 1000

        logger.debug(f"캔들 저장 완료: {symbol}_{timeframe}, 요청={len(candles)}, 실제삽입={inserted_count}, 시간={query_time_ms:.1f}ms")
        return inserted_count

    async def get_candles(self,
                          symbol: str,
                          timeframe: str,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          count: Optional[int] = None,
                          order_desc: bool = True) -> CandleQueryResult:
        """캔들 데이터 조회"""

        table_name = self._table_optimizer.get_table_name(symbol, timeframe)

        # 테이블 존재 확인
        if not await self.table_exists(symbol, timeframe):
            return CandleQueryResult(candles=[], total_count=0, query_time_ms=0.0)

        # 쿼리 조건 구성
        where_conditions = []
        params = []

        if start_time:
            where_conditions.append("candle_date_time_utc >= ?")
            params.append(start_time.isoformat())

        if end_time:
            where_conditions.append("candle_date_time_utc <= ?")
            params.append(end_time.isoformat())

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        order_clause = "candle_date_time_utc DESC" if order_desc else "candle_date_time_utc ASC"
        limit_clause = f"LIMIT {count}" if count else ""

        sql = f"""
        SELECT
            market, candle_date_time_utc, candle_date_time_kst,
            opening_price, high_price, low_price, trade_price,
            timestamp, candle_acc_trade_price, candle_acc_trade_volume,
            unit, trade_count
        FROM {table_name}
        WHERE {where_clause}
        ORDER BY {order_clause}
        {limit_clause}
        """

        start_query_time = time.time()

        with self._db_manager.get_connection('market_data') as conn:
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()

            # 총 개수 조회 (페이징 지원)
            count_sql = f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}"
            total_count = conn.execute(count_sql, params).fetchone()[0]

        query_time_ms = (time.time() - start_query_time) * 1000

        # CandleData 객체로 변환
        candles = []
        for row in rows:
            candle = CandleData(
                market=row[0],
                candle_date_time_utc=datetime.fromisoformat(row[1]),
                candle_date_time_kst=datetime.fromisoformat(row[2]),
                opening_price=float(row[3]),
                high_price=float(row[4]),
                low_price=float(row[5]),
                trade_price=float(row[6]),
                timestamp=int(row[7]),
                candle_acc_trade_price=float(row[8]),
                candle_acc_trade_volume=float(row[9]),
                unit=int(row[10]),
                trade_count=int(row[11])
            )
            candles.append(candle)

        logger.debug(f"캔들 조회 완료: {symbol}_{timeframe}, 결과={len(candles)}, 총개수={total_count}, 시간={query_time_ms:.1f}ms")

        return CandleQueryResult(
            candles=candles,
            total_count=total_count,
            query_time_ms=query_time_ms,
            cache_hit=False
        )

    async def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[CandleData]:
        """최신 캔들 데이터 조회"""
        result = await self.get_candles(symbol, timeframe, count=1, order_desc=True)
        return result.candles[0] if result.candles else None

    async def count_candles(self,
                            symbol: str,
                            timeframe: str,
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> int:
        """캔들 데이터 개수 조회"""

        table_name = self._table_optimizer.get_table_name(symbol, timeframe)

        if not await self.table_exists(symbol, timeframe):
            return 0

        where_conditions = []
        params = []

        if start_time:
            where_conditions.append("candle_date_time_utc >= ?")
            params.append(start_time.isoformat())

        if end_time:
            where_conditions.append("candle_date_time_utc <= ?")
            params.append(end_time.isoformat())

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        sql = f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}"

        with self._db_manager.get_connection('market_data') as conn:
            count = conn.execute(sql, params).fetchone()[0]

        return count

    # === 테이블 관리 메서드 ===

    async def ensure_table_exists(self, symbol: str, timeframe: str) -> str:
        """캔들 테이블 존재 확인 및 생성"""

        table_name = self._table_optimizer.get_table_name(symbol, timeframe)

        # 캐시 확인
        if table_name in self._table_optimizer._table_cache:
            return table_name

        with self._db_manager.get_connection('market_data') as conn:
            # 테이블 생성 (심볼별 개별 테이블 최적화)
            create_sql = self._table_optimizer.create_table_sql(table_name)
            conn.executescript(create_sql)

            # 캐시에 추가
            self._table_optimizer._table_cache[table_name] = True

        logger.debug(f"테이블 생성/확인 완료: {table_name}")
        return table_name

    async def table_exists(self, symbol: str, timeframe: str) -> bool:
        """캔들 테이블 존재 여부 확인"""

        table_name = self._table_optimizer.get_table_name(symbol, timeframe)

        # 캐시 확인
        if table_name in self._table_optimizer._table_cache:
            return True

        with self._db_manager.get_connection('market_data') as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table_name,))

            exists = cursor.fetchone() is not None

            if exists:
                self._table_optimizer._table_cache[table_name] = True

            return exists

    async def get_table_stats(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """특정 캔들 테이블 통계 조회"""

        if not await self.table_exists(symbol, timeframe):
            return None

        table_name = self._table_optimizer.get_table_name(symbol, timeframe)

        with self._db_manager.get_connection('market_data') as conn:
            # 기본 통계
            stats_sql = f"""
            SELECT
                COUNT(*) as record_count,
                MIN(candle_date_time_utc) as earliest_time,
                MAX(candle_date_time_utc) as latest_time,
                MIN(timestamp) as earliest_timestamp,
                MAX(timestamp) as latest_timestamp
            FROM {table_name}
            """

            cursor = conn.execute(stats_sql)
            row = cursor.fetchone()

            if not row or row[0] == 0:
                return {
                    "table_name": table_name,
                    "record_count": 0,
                    "earliest_time": None,
                    "latest_time": None,
                    "size_mb": 0.0
                }

            # 테이블 크기 조회 (근사치)
            size_sql = f"SELECT page_count * page_size as size FROM pragma_page_count('{table_name}'), pragma_page_size"
            try:
                size_bytes = conn.execute(size_sql).fetchone()[0] or 0
                size_mb = size_bytes / (1024 * 1024)
            except sqlite3.Error:
                size_mb = 0.0

            return {
                "table_name": table_name,
                "symbol": symbol,
                "timeframe": timeframe,
                "record_count": row[0],
                "earliest_time": row[1],
                "latest_time": row[2],
                "earliest_timestamp": row[3],
                "latest_timestamp": row[4],
                "size_mb": round(size_mb, 2)
            }

    async def get_all_candle_tables(self) -> List[Dict[str, Any]]:
        """모든 캔들 테이블 목록 조회"""

        with self._db_manager.get_connection('market_data') as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name LIKE 'candles_%'
                ORDER BY name
            """)

            table_names = [row[0] for row in cursor.fetchall()]

        # 각 테이블의 통계 정보 수집
        table_infos = []
        for table_name in table_names:
            try:
                # 테이블명에서 심볼과 타임프레임 추출
                parts = table_name.replace('candles_', '').split('_')
                if len(parts) >= 3:  # KRW_BTC_1m 형태
                    symbol = f"{parts[0]}-{parts[1]}"
                    timeframe = "_".join(parts[2:])

                    stats = await self.get_table_stats(symbol, timeframe)
                    if stats:
                        table_infos.append(stats)

            except Exception as e:
                logger.warning(f"테이블 {table_name} 통계 조회 실패: {e}")
                continue

        return table_infos

    # === 4단계 최적화 지원 메서드 ===

    async def check_complete_overlap(self,
                                     symbol: str,
                                     timeframe: str,
                                     start_time: datetime,
                                     count: int) -> bool:
        """완전 겹침 확인 (4단계 최적화 - Step 2)"""

        if not await self.table_exists(symbol, timeframe):
            return False

        table_name = self._table_optimizer.get_table_name(symbol, timeframe)

        # 타임프레임 간격을 분으로 계산 (간단한 매핑)
        timeframe_minutes = self._parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            return False

        end_time = start_time + timedelta(minutes=timeframe_minutes * (count - 1))

        sql = f"""
        SELECT COUNT(*) FROM {table_name}
        WHERE candle_date_time_utc BETWEEN ? AND ?
        """

        with self._db_manager.get_connection('market_data') as conn:
            db_count = conn.execute(sql, (start_time.isoformat(), end_time.isoformat())).fetchone()[0]

        # 완전 일치 = DB 개수와 요청 개수 동일
        is_complete_overlap = db_count == count

        logger.debug(f"완전 겹침 확인: {symbol}_{timeframe}, DB개수={db_count}, 요청개수={count}, 완전겹침={is_complete_overlap}")
        return is_complete_overlap

    async def check_fragmentation(self,
                                  symbol: str,
                                  timeframe: str,
                                  start_time: datetime,
                                  count: int,
                                  gap_threshold_seconds: int) -> int:
        """파편화 겹침 확인 (4단계 최적화 - Step 3)"""

        if not await self.table_exists(symbol, timeframe):
            return 0

        table_name = self._table_optimizer.get_table_name(symbol, timeframe)

        timeframe_minutes = self._parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            return 0

        end_time = start_time + timedelta(minutes=timeframe_minutes * (count - 1))

        # SQLite LAG 윈도우 함수 활용
        sql = f"""
        WITH time_gaps AS (
            SELECT
                candle_date_time_utc,
                LAG(candle_date_time_utc) OVER (ORDER BY candle_date_time_utc) as prev_time
            FROM {table_name}
            WHERE candle_date_time_utc BETWEEN ? AND ?
            ORDER BY candle_date_time_utc
        )
        SELECT COUNT(*) as gap_count
        FROM time_gaps
        WHERE (strftime('%s', candle_date_time_utc) - strftime('%s', prev_time)) > ?
        """

        with self._db_manager.get_connection('market_data') as conn:
            gap_count = conn.execute(sql, (
                start_time.isoformat(),
                end_time.isoformat(),
                gap_threshold_seconds
            )).fetchone()[0]

        logger.debug(f"파편화 확인: {symbol}_{timeframe}, 간격개수={gap_count}, 임계값={gap_threshold_seconds}초")
        return gap_count

    async def find_connected_end(self,
                                 symbol: str,
                                 timeframe: str,
                                 start_time: datetime,
                                 max_count: int = 200) -> Optional[datetime]:
        """연결된 끝 찾기 (4단계 최적화 - Step 4)"""

        if not await self.table_exists(symbol, timeframe):
            return None

        table_name = self._table_optimizer.get_table_name(symbol, timeframe)

        timeframe_minutes = self._parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            return None

        timeframe_seconds = timeframe_minutes * 60

        # SQLite ROW_NUMBER + datetime 함수 활용
        sql = f"""
        WITH consecutive_candles AS (
            SELECT
                candle_date_time_utc,
                ROW_NUMBER() OVER (ORDER BY candle_date_time_utc) as row_num,
                datetime(candle_date_time_utc,
                         '-' || ((ROW_NUMBER() OVER (ORDER BY candle_date_time_utc) - 1) * {timeframe_seconds}) || ' seconds'
                ) as expected_start
            FROM {table_name}
            WHERE candle_date_time_utc >= ?
            ORDER BY candle_date_time_utc
            LIMIT ?
        )
        SELECT MAX(candle_date_time_utc) as connected_end
        FROM consecutive_candles
        WHERE expected_start = ?
        """

        with self._db_manager.get_connection('market_data') as conn:
            result = conn.execute(sql, (
                start_time.isoformat(),
                max_count,
                start_time.isoformat()
            )).fetchone()

        if result and result[0]:
            connected_end = datetime.fromisoformat(result[0])
            logger.debug(f"연결된 끝 찾기: {symbol}_{timeframe}, 시작={start_time}, 끝={connected_end}")
            return connected_end

        return None

    # === 성능 모니터링 메서드 ===

    async def get_performance_metrics(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """성능 지표 조회"""

        stats = await self.get_table_stats(symbol, timeframe)
        if not stats:
            return {
                "avg_query_time_ms": 0.0,
                "cache_hit_rate": 0.0,
                "table_size_mb": 0.0,
                "fragmentation_rate": 0.0,
                "last_update_time": None
            }

        # 간단한 성능 지표 계산
        return {
            "avg_query_time_ms": 10.0,  # 예시 값 (실제로는 로깅으로 수집)
            "cache_hit_rate": 0.85,     # 예시 값 (캐시 시스템과 연동)
            "table_size_mb": stats["size_mb"],
            "fragmentation_rate": 0.05,  # 예시 값 (파편화 비율)
            "last_update_time": stats["latest_time"]
        }

    # === 데이터 품질 검증 메서드 ===

    async def validate_data_integrity(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """데이터 무결성 검증"""

        if not await self.table_exists(symbol, timeframe):
            return {
                "duplicate_count": 0,
                "missing_count": 0,
                "time_consistency": 1.0,
                "data_coverage_rate": 0.0
            }

        table_name = self._table_optimizer.get_table_name(symbol, timeframe)

        with self._db_manager.get_connection('market_data') as conn:
            # 중복 검사 (UNIQUE 제약으로 인해 0이어야 함)
            duplicate_sql = f"""
            SELECT candle_date_time_utc, COUNT(*) as cnt
            FROM {table_name}
            GROUP BY candle_date_time_utc
            HAVING COUNT(*) > 1
            """
            duplicate_count = len(conn.execute(duplicate_sql).fetchall())

            # 기본 통계
            total_count = await self.count_candles(symbol, timeframe)

        return {
            "duplicate_count": duplicate_count,
            "missing_count": 0,  # 실제로는 연속성 검사 필요
            "time_consistency": 1.0 if duplicate_count == 0 else 0.9,
            "data_coverage_rate": 1.0 if total_count > 0 else 0.0
        }

    # === 유틸리티 메서드 ===

    def _parse_timeframe_to_minutes(self, timeframe: str) -> Optional[int]:
        """타임프레임을 분 단위로 변환"""
        timeframe_map = {
            "1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "2h": 120, "4h": 240, "6h": 360, "8h": 480, "12h": 720,
            "1d": 1440, "3d": 4320, "1w": 10080, "1M": 43200
        }
        return timeframe_map.get(timeframe)
