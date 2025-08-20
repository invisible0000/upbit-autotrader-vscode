"""
최적화된 DB 관리자 - 실전 성능 고려

설계 개선점:
1. 심볼+타임프레임별 개별 테이블 (성능 최적화)
2. 직접 수집 vs 변환 비용 분석 및 자동 선택
3. 시간 범위 겹침 처리 및 Gap 관리
4. 고성능 인덱싱 및 쿼리 최적화
"""

import sqlite3
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class TimeRange:
    """시간 범위 정보"""
    start: datetime
    end: datetime

    def overlaps(self, other: 'TimeRange') -> bool:
        """다른 범위와 겹치는지 확인"""
        return self.start <= other.end and other.start <= self.end

    def merge(self, other: 'TimeRange') -> 'TimeRange':
        """다른 범위와 병합"""
        return TimeRange(
            min(self.start, other.start),
            max(self.end, other.end)
        )


@dataclass
class DataGap:
    """데이터 누락 구간"""
    symbol: str
    timeframe: str
    start: datetime
    end: datetime
    priority: int = 1  # 1=높음, 2=보통, 3=낮음


class OptimizedDBManager:
    """최적화된 DB 관리자"""

    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path
        self._logger = create_component_logger("OptimizedDBManager")
        self._table_cache = {}  # 테이블 존재 여부 캐시
        self._ensure_metadata_tables()

    def _ensure_metadata_tables(self) -> None:
        """메타데이터 테이블 생성"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 데이터 범위 추적 테이블
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_ranges (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        record_count INTEGER NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, timeframe, start_time, end_time)
                    )
                """)

                # 성능 통계 테이블
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS performance_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        operation TEXT NOT NULL,  -- 'convert', 'fetch', 'cache_hit'
                        duration_ms REAL NOT NULL,
                        data_count INTEGER NOT NULL,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 인덱스 생성
                conn.execute("CREATE INDEX IF NOT EXISTS idx_ranges_symbol_tf ON data_ranges(symbol, timeframe)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_stats_symbol_tf ON performance_stats(symbol, timeframe)")

                conn.commit()

        except Exception as e:
            self._logger.error(f"메타데이터 테이블 생성 실패: {e}")

    def _get_table_name(self, symbol: str, timeframe: str) -> str:
        """심볼+타임프레임별 테이블명 생성"""
        # 특수문자 제거 및 정규화
        clean_symbol = symbol.replace('-', '_').replace('.', '_')
        return f"candles_{clean_symbol}_{timeframe}"

    def _ensure_candle_table(self, symbol: str, timeframe: str) -> None:
        """심볼+타임프레임별 캔들 테이블 생성"""
        table_name = self._get_table_name(symbol, timeframe)

        # 캐시 확인
        if table_name in self._table_cache:
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        timestamp TEXT PRIMARY KEY,
                        opening_price REAL NOT NULL,
                        high_price REAL NOT NULL,
                        low_price REAL NOT NULL,
                        trade_price REAL NOT NULL,
                        candle_acc_trade_volume REAL NOT NULL,
                        candle_acc_trade_price REAL NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 고성능 인덱스 생성
                conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp)")
                conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_price ON {table_name}(trade_price)")

                conn.commit()
                self._table_cache[table_name] = True

        except Exception as e:
            self._logger.error(f"캔들 테이블 생성 실패 {table_name}: {e}")

    def store_candles(self, symbol: str, timeframe: str, candles: List[Dict[str, Any]]) -> int:
        """캔들 데이터 저장 (UPSERT 방식)"""
        if not candles:
            return 0

        self._ensure_candle_table(symbol, timeframe)
        table_name = self._get_table_name(symbol, timeframe)

        start_time = time.time()
        stored_count = 0

        try:
            with sqlite3.connect(self.db_path) as conn:
                for candle in candles:
                    conn.execute(f"""
                        INSERT OR REPLACE INTO {table_name}
                        (timestamp, opening_price, high_price, low_price, trade_price,
                         candle_acc_trade_volume, candle_acc_trade_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        candle.get('timestamp', candle.get('candle_date_time_utc')),
                        float(candle['opening_price']),
                        float(candle['high_price']),
                        float(candle['low_price']),
                        float(candle['trade_price']),
                        float(candle['candle_acc_trade_volume']),
                        float(candle['candle_acc_trade_price'])
                    ))
                    stored_count += 1

                conn.commit()

                # 데이터 범위 업데이트
                self._update_data_range(conn, symbol, timeframe, candles)

                # 성능 통계 기록
                duration_ms = (time.time() - start_time) * 1000
                self._record_performance(conn, symbol, timeframe, "store", duration_ms, stored_count)

        except Exception as e:
            self._logger.error(f"캔들 저장 실패 {symbol} {timeframe}: {e}")
            return 0

        self._logger.info(f"DB 저장 완료: {symbol} {timeframe} ({stored_count}개)")
        return stored_count

    def get_candles(self, symbol: str, timeframe: str, start_time: str, end_time: str) -> Optional[List[Dict[str, Any]]]:
        """캔들 데이터 조회 (시간 범위)"""
        table_name = self._get_table_name(symbol, timeframe)

        # 테이블 존재 확인
        if not self._table_exists(table_name):
            return None

        start_query_time = time.time()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(f"""
                    SELECT timestamp, opening_price, high_price, low_price, trade_price,
                           candle_acc_trade_volume, candle_acc_trade_price
                    FROM {table_name}
                    WHERE timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp ASC
                """, (start_time, end_time))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row[0],
                        'opening_price': row[1],
                        'high_price': row[2],
                        'low_price': row[3],
                        'trade_price': row[4],
                        'candle_acc_trade_volume': row[5],
                        'candle_acc_trade_price': row[6]
                    })

                # 성능 통계 기록
                duration_ms = (time.time() - start_query_time) * 1000
                self._record_performance(conn, symbol, timeframe, "fetch", duration_ms, len(results))

                return results if results else None

        except Exception as e:
            self._logger.error(f"캔들 조회 실패 {symbol} {timeframe}: {e}")
            return None

    def find_data_gaps(self, symbol: str, timeframe: str, requested_start: str, requested_end: str) -> List[DataGap]:
        """데이터 누락 구간 찾기"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT start_time, end_time FROM data_ranges
                    WHERE symbol = ? AND timeframe = ?
                    ORDER BY start_time ASC
                """, (symbol, timeframe))

                existing_ranges = [TimeRange(
                    datetime.fromisoformat(row[0]),
                    datetime.fromisoformat(row[1])
                ) for row in cursor.fetchall()]

                if not existing_ranges:
                    # 데이터가 전혀 없음
                    return [DataGap(
                        symbol, timeframe,
                        datetime.fromisoformat(requested_start),
                        datetime.fromisoformat(requested_end),
                        priority=1
                    )]

                # 요청된 범위와 기존 범위 비교하여 Gap 찾기
                requested_range = TimeRange(
                    datetime.fromisoformat(requested_start),
                    datetime.fromisoformat(requested_end)
                )

                gaps = []
                current_pos = requested_range.start

                for existing in existing_ranges:
                    if existing.end < requested_range.start:
                        continue  # 요청 범위 이전
                    if existing.start > requested_range.end:
                        break     # 요청 범위 이후

                    # Gap이 있으면 추가
                    if current_pos < existing.start:
                        gaps.append(DataGap(
                            symbol, timeframe,
                            current_pos,
                            min(existing.start, requested_range.end),
                            priority=2
                        ))

                    current_pos = max(current_pos, existing.end)

                # 마지막 Gap 확인
                if current_pos < requested_range.end:
                    gaps.append(DataGap(
                        symbol, timeframe,
                        current_pos,
                        requested_range.end,
                        priority=2
                    ))

                return gaps

        except Exception as e:
            self._logger.error(f"Gap 분석 실패 {symbol} {timeframe}: {e}")
            return []

    def get_conversion_cost_analysis(self, symbol: str, target_timeframe: str, data_count: int) -> Dict[str, float]:
        """변환 vs 직접수집 비용 분석"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 1분봉 변환 성능 통계
                cursor = conn.execute("""
                    SELECT AVG(duration_ms / data_count) as avg_convert_cost
                    FROM performance_stats
                    WHERE symbol = ? AND timeframe = '1m' AND operation = 'convert'
                    AND timestamp > datetime('now', '-7 days')
                    LIMIT 50
                """, (symbol,))

                convert_result = cursor.fetchone()
                convert_cost_per_item = convert_result[0] if convert_result[0] else 0.1

                # 직접 수집 성능 통계
                cursor = conn.execute("""
                    SELECT AVG(duration_ms / data_count) as avg_fetch_cost
                    FROM performance_stats
                    WHERE symbol = ? AND timeframe = ? AND operation = 'fetch'
                    AND timestamp > datetime('now', '-7 days')
                    LIMIT 50
                """, (symbol, target_timeframe))

                fetch_result = cursor.fetchone()
                fetch_cost_per_item = fetch_result[0] if fetch_result[0] else 0.05

                # 변환 비용 (1분봉 → 타겟 타임프레임)
                conversion_ratio = self._get_conversion_ratio(target_timeframe)
                total_convert_cost = (data_count * conversion_ratio * convert_cost_per_item) + \
                                   (data_count * 0.02)  # 변환 오버헤드

                # 직접 수집 비용
                total_fetch_cost = data_count * fetch_cost_per_item + 100  # API 호출 오버헤드

                return {
                    'convert_cost_ms': total_convert_cost,
                    'fetch_cost_ms': total_fetch_cost,
                    'recommended': 'convert' if total_convert_cost < total_fetch_cost else 'fetch',
                    'cost_ratio': total_convert_cost / total_fetch_cost if total_fetch_cost > 0 else 1.0
                }

        except Exception as e:
            self._logger.error(f"비용 분석 실패: {e}")
            return {
                'convert_cost_ms': 1000,
                'fetch_cost_ms': 500,
                'recommended': 'fetch',
                'cost_ratio': 2.0
            }

    def _get_conversion_ratio(self, timeframe: str) -> int:
        """타임프레임별 1분봉 대비 비율"""
        ratios = {
            '1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '2h': 120, '4h': 240, '6h': 360, '12h': 720, '1d': 1440
        }
        return ratios.get(timeframe, 1)

    def _table_exists(self, table_name: str) -> bool:
        """테이블 존재 확인"""
        if table_name in self._table_cache:
            return True

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM sqlite_master
                    WHERE type='table' AND name=?
                """, (table_name,))
                exists = cursor.fetchone()[0] > 0
                if exists:
                    self._table_cache[table_name] = True
                return exists
        except:
            return False

    def _update_data_range(self, conn: sqlite3.Connection, symbol: str, timeframe: str, candles: List[Dict[str, Any]]) -> None:
        """데이터 범위 메타데이터 업데이트"""
        if not candles:
            return

        timestamps = [c.get('timestamp', c.get('candle_date_time_utc')) for c in candles]
        start_time = min(timestamps)
        end_time = max(timestamps)

        conn.execute("""
            INSERT OR REPLACE INTO data_ranges
            (symbol, timeframe, start_time, end_time, record_count)
            VALUES (?, ?, ?, ?, ?)
        """, (symbol, timeframe, start_time, end_time, len(candles)))

    def _record_performance(self, conn: sqlite3.Connection, symbol: str, timeframe: str,
                          operation: str, duration_ms: float, data_count: int) -> None:
        """성능 통계 기록"""
        conn.execute("""
            INSERT INTO performance_stats
            (symbol, timeframe, operation, duration_ms, data_count)
            VALUES (?, ?, ?, ?, ?)
        """, (symbol, timeframe, operation, duration_ms, data_count))

    def get_storage_summary(self) -> Dict[str, Any]:
        """저장 현황 요약"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 테이블별 통계
                cursor = conn.execute("""
                    SELECT symbol, timeframe,
                           MIN(start_time) as earliest,
                           MAX(end_time) as latest,
                           SUM(record_count) as total_records
                    FROM data_ranges
                    GROUP BY symbol, timeframe
                    ORDER BY symbol, timeframe
                """)

                storage_info = []
                for row in cursor.fetchall():
                    storage_info.append({
                        'symbol': row[0],
                        'timeframe': row[1],
                        'earliest': row[2],
                        'latest': row[3],
                        'total_records': row[4]
                    })

                # 전체 통계
                cursor = conn.execute("SELECT COUNT(*) FROM data_ranges")
                total_ranges = cursor.fetchone()[0]

                cursor = conn.execute("SELECT SUM(record_count) FROM data_ranges")
                total_records = cursor.fetchone()[0] or 0

                return {
                    'total_ranges': total_ranges,
                    'total_records': total_records,
                    'storage_detail': storage_info,
                    'generated_at': datetime.now().isoformat()
                }

        except Exception as e:
            self._logger.error(f"저장 현황 조회 실패: {e}")
            return {'error': str(e)}


class SmartDataManager:
    """지능형 데이터 관리자 (최적 전략 자동 선택)"""

    def __init__(self):
        self.db_manager = OptimizedDBManager()
        self._logger = create_component_logger("SmartDataManager")

    def get_optimal_data(self, symbol: str, timeframe: str, start_time: str, end_time: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """최적 전략으로 데이터 획득"""

        # 1. 기존 데이터 확인 및 Gap 분석
        gaps = self.db_manager.find_data_gaps(symbol, timeframe, start_time, end_time)

        # 2. 기존 데이터 로드
        existing_data = self.db_manager.get_candles(symbol, timeframe, start_time, end_time) or []

        if not gaps:
            # Gap 없음 - 기존 데이터만 반환
            return existing_data, {
                'strategy': 'cache_hit',
                'gaps_filled': 0,
                'existing_records': len(existing_data),
                'performance': 'optimal'
            }

        # 3. Gap 채우기 전략 결정
        filled_data = []
        total_gap_records = sum((gap.end - gap.start).total_seconds() // 60 for gap in gaps)

        cost_analysis = self.db_manager.get_conversion_cost_analysis(symbol, timeframe, total_gap_records)
        strategy = cost_analysis['recommended']

        for gap in gaps:
            if strategy == 'convert':
                # 1분봉 변환 방식
                gap_data = self._fill_gap_by_conversion(gap)
            else:
                # 직접 수집 방식
                gap_data = self._fill_gap_by_fetch(gap)

            if gap_data:
                filled_data.extend(gap_data)
                # DB에 저장
                self.db_manager.store_candles(symbol, timeframe, gap_data)

        # 4. 전체 데이터 재조회 (정렬된 상태)
        final_data = self.db_manager.get_candles(symbol, timeframe, start_time, end_time) or []

        return final_data, {
            'strategy': strategy,
            'gaps_filled': len(gaps),
            'existing_records': len(existing_data),
            'new_records': len(filled_data),
            'total_records': len(final_data),
            'cost_analysis': cost_analysis,
            'performance': 'optimized'
        }

    def _fill_gap_by_conversion(self, gap: DataGap) -> List[Dict[str, Any]]:
        """1분봉 변환으로 Gap 채우기 (현재 비활성화)"""
        # 마켓 데이터 백본에서 직접 타임프레임별 데이터를 제공하므로 변환 불필요
        self._logger.info(f"변환 방식 Gap 채우기 비활성화: {gap.symbol} {gap.timeframe}")
        return []

    def _fill_gap_by_fetch(self, gap: DataGap) -> List[Dict[str, Any]]:
        """직접 수집으로 Gap 채우기"""
        # TODO: CollectionEngine 연동
        self._logger.info(f"직접 수집 Gap 채우기: {gap.symbol} {gap.timeframe}")
        return []
