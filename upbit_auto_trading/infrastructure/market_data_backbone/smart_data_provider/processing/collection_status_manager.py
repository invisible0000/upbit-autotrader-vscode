"""
수집 상태 관리자
Smart Data Provider V3.0의 스마트 캔들 콜렉터 핵심 로직
"""

import sqlite3
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.models.collection_models import (
    CollectionStatus,
    CollectionStatusRecord,
    CandleWithStatus,
    TimeRange,
    CollectionSummary
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.processing.time_utils import (
    generate_candle_times
)


class CollectionStatusManager:
    """수집 상태 관리 핵심 클래스"""

    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path
        self.logger = create_component_logger("CollectionStatusManager")

    def get_collection_status(
        self,
        symbol: str,
        timeframe: str,
        target_time: datetime
    ) -> Optional[CollectionStatusRecord]:
        """특정 시간의 수집 상태 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, symbol, timeframe, target_time, collection_status,
                       last_attempt_at, attempt_count, api_response_code,
                       created_at, updated_at
                FROM candle_collection_status
                WHERE symbol = ? AND timeframe = ? AND target_time = ?
            """, (symbol, timeframe, target_time.isoformat()))

            row = cursor.fetchone()
            if not row:
                return None

            return CollectionStatusRecord(
                id=row[0],
                symbol=row[1],
                timeframe=row[2],
                target_time=datetime.fromisoformat(row[3]),
                collection_status=CollectionStatus(row[4]),
                last_attempt_at=datetime.fromisoformat(row[5]) if row[5] else None,
                attempt_count=row[6],
                api_response_code=row[7],
                created_at=datetime.fromisoformat(row[8]) if row[8] else None,
                updated_at=datetime.fromisoformat(row[9]) if row[9] else None
            )

    def update_collection_status(self, record: CollectionStatusRecord) -> None:
        """수집 상태 업데이트 또는 삽입"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # UPSERT 쿼리
            cursor.execute("""
                INSERT INTO candle_collection_status (
                    symbol, timeframe, target_time, collection_status,
                    last_attempt_at, attempt_count, api_response_code,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, timeframe, target_time) DO UPDATE SET
                    collection_status = excluded.collection_status,
                    last_attempt_at = excluded.last_attempt_at,
                    attempt_count = excluded.attempt_count,
                    api_response_code = excluded.api_response_code,
                    updated_at = excluded.updated_at
            """, (
                record.symbol,
                record.timeframe,
                record.target_time.isoformat(),
                record.collection_status.value,
                record.last_attempt_at.isoformat() if record.last_attempt_at else None,
                record.attempt_count,
                record.api_response_code,
                record.created_at.isoformat() if record.created_at else datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            conn.commit()
            self.logger.debug(
                f"수집 상태 업데이트: {record.symbol} {record.timeframe} "
                f"{record.target_time} -> {record.collection_status.value}"
            )

    def get_missing_candle_times(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[datetime]:
        """
        수집되지 않은 캔들 시간 목록 반환

        Returns:
            PENDING 또는 FAILED 상태인 캔들 시간 목록
        """
        # 예상되는 모든 캔들 시간 생성
        expected_times = generate_candle_times(start_time, end_time, timeframe)

        if not expected_times:
            return []

        # DB에서 수집 상태 조회
        with sqlite3.connect(self.db_path) as conn:
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
                datetime.fromisoformat(row[0]): CollectionStatus(row[1])
                for row in cursor.fetchall()
            }

        # 미수집 시간 필터링
        missing_times = []
        for time in expected_times:
            status = existing_statuses.get(time)
            if status is None or status in [CollectionStatus.PENDING, CollectionStatus.FAILED]:
                missing_times.append(time)

        return missing_times

    def get_empty_candle_times(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[datetime]:
        """빈 캔들 시간 목록 반환"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT target_time
                FROM candle_collection_status
                WHERE symbol = ? AND timeframe = ?
                AND collection_status = ?
                AND target_time BETWEEN ? AND ?
                ORDER BY target_time
            """, (
                symbol,
                timeframe,
                CollectionStatus.EMPTY.value,
                start_time.isoformat(),
                end_time.isoformat()
            ))

            return [datetime.fromisoformat(row[0]) for row in cursor.fetchall()]

    def fill_empty_candles(
        self,
        candles: List[dict],
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[CandleWithStatus]:
        """
        실제 캔들 데이터에 빈 캔들을 채워서 연속된 데이터 생성

        Args:
            candles: 실제 캔들 데이터 목록
            symbol: 심볼
            timeframe: 타임프레임
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            빈 캔들이 채워진 연속 데이터
        """
        # 예상되는 모든 캔들 시간 생성
        expected_times = generate_candle_times(start_time, end_time, timeframe)

        # 실제 캔들을 시간별로 인덱싱
        candle_by_time = {}
        for candle in candles:
            candle_time = datetime.fromisoformat(candle['candle_date_time_utc'].replace('Z', '+00:00'))
            candle_by_time[candle_time] = candle

        # 빈 캔들 시간 조회
        empty_times = set(self.get_empty_candle_times(symbol, timeframe, start_time, end_time))

        # 연속 데이터 생성
        continuous_candles = []
        last_price = None

        for time in expected_times:
            if time in candle_by_time:
                # 실제 캔들 데이터
                candle = candle_by_time[time]
                last_price = Decimal(str(candle['trade_price']))

                continuous_candles.append(CandleWithStatus(
                    market=candle['market'],
                    candle_date_time_utc=datetime.fromisoformat(
                        candle['candle_date_time_utc'].replace('Z', '+00:00')
                    ),
                    candle_date_time_kst=datetime.fromisoformat(
                        candle['candle_date_time_kst'].replace('Z', '+00:00')
                    ),
                    opening_price=Decimal(str(candle['opening_price'])),
                    high_price=Decimal(str(candle['high_price'])),
                    low_price=Decimal(str(candle['low_price'])),
                    trade_price=Decimal(str(candle['trade_price'])),
                    timestamp=candle['timestamp'],
                    candle_acc_trade_price=Decimal(str(candle['candle_acc_trade_price'])),
                    candle_acc_trade_volume=Decimal(str(candle['candle_acc_trade_volume'])),
                    unit=candle.get('unit', 1),
                    is_empty=False,
                    collection_status=CollectionStatus.COLLECTED
                ))

            elif time in empty_times and last_price is not None:
                # 빈 캔들 생성 (마지막 가격으로 채움)
                continuous_candles.append(CandleWithStatus.create_empty(symbol, time, last_price))

        return continuous_candles

    def get_collection_summary(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> CollectionSummary:
        """수집 상태 요약 정보 반환"""
        expected_times = generate_candle_times(start_time, end_time, timeframe)
        total_expected = len(expected_times)

        if total_expected == 0:
            return CollectionSummary(
                symbol=symbol,
                timeframe=timeframe,
                time_range=TimeRange(start_time, end_time),
                total_expected=0,
                collected_count=0,
                empty_count=0,
                pending_count=0,
                failed_count=0
            )

        # 상태별 카운트
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            placeholders = ','.join(['?' for _ in expected_times])
            time_strings = [t.isoformat() for t in expected_times]

            cursor.execute(f"""
                SELECT collection_status, COUNT(*)
                FROM candle_collection_status
                WHERE symbol = ? AND timeframe = ?
                AND target_time IN ({placeholders})
                GROUP BY collection_status
            """, [symbol, timeframe] + time_strings)

            status_counts = {CollectionStatus(row[0]): row[1] for row in cursor.fetchall()}

        collected_count = status_counts.get(CollectionStatus.COLLECTED, 0)
        empty_count = status_counts.get(CollectionStatus.EMPTY, 0)
        failed_count = status_counts.get(CollectionStatus.FAILED, 0)

        # PENDING은 DB에 없는 시간들도 포함
        recorded_count = sum(status_counts.values())
        pending_count = total_expected - recorded_count

        return CollectionSummary(
            symbol=symbol,
            timeframe=timeframe,
            time_range=TimeRange(start_time, end_time),
            total_expected=total_expected,
            collected_count=collected_count,
            empty_count=empty_count,
            pending_count=pending_count,
            failed_count=failed_count
        )

    def mark_candle_collected(
        self,
        symbol: str,
        timeframe: str,
        target_time: datetime,
        api_response_code: int = 200
    ) -> None:
        """캔들을 수집 완료로 마킹"""
        existing = self.get_collection_status(symbol, timeframe, target_time)

        if existing:
            updated = existing.mark_collected(api_response_code)
        else:
            updated = CollectionStatusRecord.create_pending(symbol, timeframe, target_time)
            updated = updated.mark_collected(api_response_code)

        self.update_collection_status(updated)

    def mark_candle_empty(
        self,
        symbol: str,
        timeframe: str,
        target_time: datetime,
        api_response_code: int = 200
    ) -> None:
        """캔들을 빈 캔들로 마킹"""
        existing = self.get_collection_status(symbol, timeframe, target_time)

        if existing:
            updated = existing.mark_empty(api_response_code)
        else:
            updated = CollectionStatusRecord.create_pending(symbol, timeframe, target_time)
            updated = updated.mark_empty(api_response_code)

        self.update_collection_status(updated)

    def mark_candle_failed(
        self,
        symbol: str,
        timeframe: str,
        target_time: datetime,
        api_response_code: Optional[int] = None
    ) -> None:
        """캔들 수집을 실패로 마킹"""
        existing = self.get_collection_status(symbol, timeframe, target_time)

        if existing:
            updated = existing.mark_failed(api_response_code)
        else:
            updated = CollectionStatusRecord.create_pending(symbol, timeframe, target_time)
            updated = updated.mark_failed(api_response_code)

        self.update_collection_status(updated)
