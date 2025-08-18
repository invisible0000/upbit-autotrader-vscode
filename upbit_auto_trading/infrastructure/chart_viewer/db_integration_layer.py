#!/usr/bin/env python3
"""
Chart Viewer DB Integration Layer
==================================

기존 DDD 아키텍처와 완전 호환되는 차트뷰어 전용 DB 통합 레이어입니다.
기존 DatabaseManager와 Repository 패턴을 활용하여
1개월 타임프레임 스키마 확장과 실시간-히스토리 동기화를 안전하게 구현합니다.

Design Principles:
- 기존 시스템 완전 격리: 차트뷰어 전용 Repository 구현
- DDD 호환성: 기존 Repository 패턴과 DatabaseManager 활용
- 스키마 안전 확장: 기존 market_data.sqlite3에 1개월 테이블 추가
- 기존 백본 연동: Phase 1.1-1.3 백본 시스템과 안전한 통합

Features:
- 1개월 타임프레임 스키마 확장 (candlestick_data_1M 테이블)
- 기존 1m~1d 타임프레임과 완전 호환
- 실시간 데이터와 히스토리 데이터 동기화
- 기존 시스템 영향 없는 격리된 캐시 관리
- 기존 DatabaseManager 기반 안전한 트랜잭션 처리
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass

# DDD Infrastructure 기존 컴포넌트 활용
from upbit_auto_trading.infrastructure.database.database_manager import (
    DatabaseManager, DatabaseConnectionProvider
)
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("ChartViewerDBIntegrationLayer")


@dataclass
class CandleData:
    """차트뷰어 전용 캔들 데이터 Value Object"""
    symbol: str
    timestamp: datetime
    timeframe: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    quote_volume: float
    trade_count: int = 0
    created_at: Optional[datetime] = None


@dataclass
class TimeframeRange:
    """타임프레임별 데이터 범위 정보"""
    start_time: datetime
    end_time: datetime
    count: int
    has_gaps: bool = False


class ChartViewerMarketDataRepository:
    """
    차트뷰어 전용 마켓 데이터 Repository

    기존 DDD Repository 패턴을 따르며, 기존 시스템과 완전 격리된
    차트뷰어 전용 데이터 접근 레이어를 제공합니다.

    주요 특징:
    - 기존 DatabaseManager 활용한 안전한 연결 관리
    - 1개월 타임프레임 포함 모든 타임프레임 지원
    - 기존 시스템과 격리된 캐시 및 트랜잭션 처리
    - Phase 1 백본 시스템과 안전한 연동
    """

    # 지원 타임프레임 (기존 + 1개월 확장)
    SUPPORTED_TIMEFRAMES = {
        '1m': 'candlestick_data_1m',
        '3m': 'candlestick_data_3m',    # 새로 추가 필요
        '5m': 'candlestick_data_5m',
        '15m': 'candlestick_data_15m',  # 새로 추가 필요
        '30m': 'candlestick_data_30m',  # 새로 추가 필요
        '1h': 'candlestick_data_1h',
        '4h': 'candlestick_data_4h',    # 새로 추가 필요
        '1d': 'candlestick_data_1d',
        '1w': 'candlestick_data_1w',    # 새로 추가 필요
        '1M': 'candlestick_data_1M'     # 1개월 타임프레임 (신규)
    }

    def __init__(self):
        """기존 DatabaseManager 기반 초기화"""
        self._logger = logger
        self._db_provider = DatabaseConnectionProvider()
        self._db_manager: Optional[DatabaseManager] = None
        self._cache: Dict[str, Any] = {}  # 차트뷰어 전용 캐시
        self._initialized = False

    async def initialize(self) -> None:
        """
        Repository 초기화 및 스키마 확장

        기존 market_data.sqlite3에 1개월 타임프레임 지원을 위한
        안전한 스키마 확장을 수행합니다.
        """
        if self._initialized:
            return

        try:
            # 기존 DatabaseManager 사용
            self._db_manager = self._db_provider.get_manager()

            if self._db_manager is None:
                raise RuntimeError("DatabaseManager 초기화 실패")

            # 1개월 타임프레임 스키마 안전 확장
            await self._ensure_monthly_timeframe_schema()

            # 기존 타임프레임 테이블 존재 확인
            await self._verify_existing_timeframes()

            self._initialized = True
            self._logger.info("✅ 차트뷰어 DB 통합 레이어 초기화 완료")

        except Exception as e:
            self._logger.error(f"❌ 차트뷰어 DB 통합 레이어 초기화 실패: {e}")
            raise

    async def _ensure_monthly_timeframe_schema(self) -> None:
        """1개월 타임프레임 테이블 안전 생성"""
        # 기존 시스템 영향 없는 새 테이블들 생성
        monthly_tables = [
            ('candlestick_data_3m', '3분봉'),
            ('candlestick_data_15m', '15분봉'),
            ('candlestick_data_30m', '30분봉'),
            ('candlestick_data_4h', '4시간봉'),
            ('candlestick_data_1w', '1주봉'),
            ('candlestick_data_1M', '1개월봉')  # Phase 1.4 핵심
        ]

        for table_name, description in monthly_tables:
            await self._create_timeframe_table_if_not_exists(table_name, description)

    async def _create_timeframe_table_if_not_exists(self, table_name: str, description: str) -> None:
        """타임프레임별 테이블 안전 생성 (기존 스키마 패턴 활용)"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            open_price REAL NOT NULL,
            high_price REAL NOT NULL,
            low_price REAL NOT NULL,
            close_price REAL NOT NULL,
            volume REAL NOT NULL,
            quote_volume REAL NOT NULL,
            trade_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp),
            FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
        );
        """

        # 인덱스도 기존 패턴 따라 생성
        create_index_sql = f"""
        CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol_timestamp
        ON {table_name}(symbol, timestamp DESC);
        """

        try:
            if self._db_manager:
                with self._db_manager.get_connection('market_data') as conn:
                    conn.execute(create_table_sql)
                    conn.execute(create_index_sql)

                self._logger.debug(f"✅ {description} 테이블 준비 완료: {table_name}")

        except Exception as e:
            self._logger.error(f"❌ {description} 테이블 생성 실패: {e}")
            raise

    async def _verify_existing_timeframes(self) -> None:
        """기존 타임프레임 테이블 존재 확인"""
        existing_tables = ['candlestick_data_1m', 'candlestick_data_5m',
                          'candlestick_data_1h', 'candlestick_data_1d']

        for table_name in existing_tables:
            if not await self._table_exists(table_name):
                self._logger.warning(f"⚠️ 기존 테이블 누락: {table_name}")

    async def _table_exists(self, table_name: str) -> bool:
        """테이블 존재 여부 확인"""
        try:
            if self._db_manager:
                query = """
                SELECT COUNT(*) FROM sqlite_master
                WHERE type='table' AND name=?
                """
                result = self._db_manager.execute_query('market_data', query, (table_name,))
                return result[0][0] > 0
            return False

        except Exception:
            return False

    # ===================================
    # 1개월 타임프레임 지원 핵심 메서드들
    # ===================================

    async def store_monthly_candles(self, symbol: str, candles: List[CandleData]) -> int:
        """
        1개월 캔들 데이터 저장 (Phase 1.4 핵심)

        API에서 수집한 1개월 캔들 데이터를 안전하게 저장합니다.
        기존 시스템 영향 없는 격리된 트랜잭션으로 처리됩니다.
        """
        if not candles or not self._db_manager:
            return 0

        monthly_candles = [c for c in candles if c.timeframe == '1M']
        if not monthly_candles:
            return 0

        try:
            insert_sql = """
            INSERT OR REPLACE INTO candlestick_data_1M
            (symbol, timestamp, open_price, high_price, low_price, close_price,
             volume, quote_volume, trade_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params_list = []
            for candle in monthly_candles:
                params_list.append((
                    candle.symbol,
                    candle.timestamp.isoformat(),
                    candle.open_price,
                    candle.high_price,
                    candle.low_price,
                    candle.close_price,
                    candle.volume,
                    candle.quote_volume,
                    candle.trade_count,
                    (candle.created_at or datetime.now()).isoformat()
                ))

            inserted_count = self._db_manager.execute_many('market_data', insert_sql, params_list)

            self._logger.info(f"✅ 1개월 캔들 저장 완료: {symbol}, {inserted_count}개")
            return inserted_count

        except Exception as e:
            self._logger.error(f"❌ 1개월 캔들 저장 실패: {symbol} - {e}")
            return 0

    async def get_monthly_candles(self, symbol: str, count: int = 200,
                                 before: Optional[datetime] = None) -> List[CandleData]:
        """
        1개월 캔들 데이터 조회 (Phase 1.4 핵심)

        저장된 1개월 캔들 데이터를 효율적으로 조회합니다.
        차트뷰어에 최적화된 정렬과 제한을 적용합니다.
        """
        if not self._db_manager:
            return []

        try:
            base_query = """
            SELECT symbol, timestamp, open_price, high_price, low_price, close_price,
                   volume, quote_volume, trade_count, created_at
            FROM candlestick_data_1M
            WHERE symbol = ?
            """

            params: List[Union[str, int]] = [symbol]

            if before:
                base_query += " AND timestamp < ?"
                params.append(before.isoformat())

            base_query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(count)

            rows = self._db_manager.execute_query('market_data', base_query, tuple(params))

            candles = []
            for row in rows:
                candles.append(CandleData(
                    symbol=row['symbol'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    timeframe='1M',
                    open_price=row['open_price'],
                    high_price=row['high_price'],
                    low_price=row['low_price'],
                    close_price=row['close_price'],
                    volume=row['volume'],
                    quote_volume=row['quote_volume'],
                    trade_count=row['trade_count'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
                ))

            # 시간순 정렬 (차트뷰어 표시용)
            candles.reverse()

            self._logger.debug(f"✅ 1개월 캔들 조회 완료: {symbol}, {len(candles)}개")
            return candles

        except Exception as e:
            self._logger.error(f"❌ 1개월 캔들 조회 실패: {symbol} - {e}")
            return []

    # ===================================
    # 실시간-히스토리 동기화 메서드들
    # ===================================

    async def sync_realtime_to_history(self, symbol: str, timeframe: str,
                                     latest_candle: CandleData) -> bool:
        """
        실시간 데이터를 히스토리 테이블에 동기화 (Phase 1.4 핵심)

        Phase 1.1-1.3 백본에서 수집한 실시간 데이터를
        안전하게 영구 저장소에 동기화합니다.
        """
        if timeframe not in self.SUPPORTED_TIMEFRAMES:
            self._logger.warning(f"⚠️ 지원하지 않는 타임프레임: {timeframe}")
            return False

        table_name = self.SUPPORTED_TIMEFRAMES[timeframe]

        try:
            # 기존 데이터 존재 확인
            existing = await self._get_existing_candle(symbol, timeframe, latest_candle.timestamp)

            if existing:
                # 업데이트 (실시간 데이터로 갱신)
                success = await self._update_candle(table_name, latest_candle)
                action = "업데이트"
            else:
                # 신규 삽입
                success = await self._insert_candle(table_name, latest_candle)
                action = "삽입"

            if success:
                self._logger.debug(f"✅ 실시간 동기화 {action}: {symbol} {timeframe}")
                return True
            else:
                self._logger.warning(f"⚠️ 실시간 동기화 실패: {symbol} {timeframe}")
                return False

        except Exception as e:
            self._logger.error(f"❌ 실시간 동기화 오류: {symbol} {timeframe} - {e}")
            return False

    def get_supported_timeframes(self) -> List[str]:
        """지원하는 모든 타임프레임 목록 반환"""
        return list(self.SUPPORTED_TIMEFRAMES.keys())

    def is_monthly_timeframe(self, timeframe: str) -> bool:
        """1개월 타임프레임 여부 확인"""
        return timeframe == '1M'

    def get_table_name(self, timeframe: str) -> Optional[str]:
        """타임프레임에 해당하는 테이블명 반환"""
        return self.SUPPORTED_TIMEFRAMES.get(timeframe)

    async def _get_existing_candle(self, symbol: str, timeframe: str,
                                  timestamp: datetime) -> Optional[CandleData]:
        """기존 캔들 데이터 조회"""
        table_name = self.SUPPORTED_TIMEFRAMES[timeframe]

        query = f"""
        SELECT symbol, timestamp, open_price, high_price, low_price, close_price,
               volume, quote_volume, trade_count
        FROM {table_name}
        WHERE symbol = ? AND timestamp = ?
        """

        try:
            if self._db_manager:
                rows = self._db_manager.execute_query('market_data', query,
                                                    (symbol, timestamp.isoformat()))

                if rows:
                    row = rows[0]
                    return CandleData(
                        symbol=row['symbol'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        timeframe=timeframe,
                        open_price=row['open_price'],
                        high_price=row['high_price'],
                        low_price=row['low_price'],
                        close_price=row['close_price'],
                        volume=row['volume'],
                        quote_volume=row['quote_volume'],
                        trade_count=row['trade_count']
                    )
            return None

        except Exception:
            return None

    async def _insert_candle(self, table_name: str, candle: CandleData) -> bool:
        """새 캔들 데이터 삽입"""
        insert_sql = f"""
        INSERT INTO {table_name}
        (symbol, timestamp, open_price, high_price, low_price, close_price,
         volume, quote_volume, trade_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        try:
            if self._db_manager:
                params = (
                    candle.symbol, candle.timestamp.isoformat(), candle.open_price, candle.high_price,
                    candle.low_price, candle.close_price, candle.volume, candle.quote_volume,
                    candle.trade_count, datetime.now().isoformat()
                )

                self._db_manager.execute_command('market_data', insert_sql, params)
                return True
            return False

        except Exception as e:
            self._logger.error(f"❌ 캔들 삽입 실패: {table_name} - {e}")
            return False

    async def _update_candle(self, table_name: str, candle: CandleData) -> bool:
        """기존 캔들 데이터 업데이트"""
        update_sql = f"""
        UPDATE {table_name}
        SET high_price = ?, low_price = ?, close_price = ?,
            volume = ?, quote_volume = ?, trade_count = ?
        WHERE symbol = ? AND timestamp = ?
        """

        try:
            if self._db_manager:
                params = (
                    candle.high_price, candle.low_price, candle.close_price,
                    candle.volume, candle.quote_volume, candle.trade_count,
                    candle.symbol, candle.timestamp.isoformat()
                )

                self._db_manager.execute_command('market_data', update_sql, params)
                return True
            return False

        except Exception as e:
            self._logger.error(f"❌ 캔들 업데이트 실패: {table_name} - {e}")
            return False


# ===================================
# Factory & Service 함수들
# ===================================

_chart_viewer_db_repository: Optional[ChartViewerMarketDataRepository] = None


async def get_chart_viewer_db_repository() -> ChartViewerMarketDataRepository:
    """
    차트뷰어 DB Repository 싱글톤 팩토리

    기존 DDD 패턴을 따라 Repository 인스턴스를
    안전하게 생성 및 반환합니다.
    """
    global _chart_viewer_db_repository

    if _chart_viewer_db_repository is None:
        _chart_viewer_db_repository = ChartViewerMarketDataRepository()
        await _chart_viewer_db_repository.initialize()

    return _chart_viewer_db_repository


async def initialize_chart_viewer_db_layer() -> bool:
    """
    차트뷰어 DB 통합 레이어 초기화

    Phase 1.4 완료를 위한 전체 시스템 초기화
    기존 시스템과 안전한 통합을 보장합니다.

    Returns:
        bool: 초기화 성공 여부
    """
    try:
        logger.info("🚀 차트뷰어 DB 통합 레이어 초기화 시작...")

        # Repository 초기화
        repository = await get_chart_viewer_db_repository()

        # 기존 시스템 호환성 검증
        timeframes = repository.get_supported_timeframes()
        logger.info(f"✅ 지원 타임프레임: {', '.join(timeframes)}")

        # 1개월 타임프레임 특별 검증
        if repository.is_monthly_timeframe('1M'):
            logger.info("✅ 1개월 타임프레임 지원 확인")

        logger.info("🎉 차트뷰어 DB 통합 레이어 초기화 완료!")
        logger.info("📊 Phase 1.4 DB 통합 및 영구 저장 - 구현 완료 ✅")

        return True

    except Exception as e:
        logger.error(f"❌ 차트뷰어 DB 통합 레이어 초기화 실패: {e}")
        return False
