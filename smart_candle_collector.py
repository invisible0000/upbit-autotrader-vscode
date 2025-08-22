"""
스마트 캔들 수집기 - 빈 캔들과 미수집 캔들 구분
실제 거래가 없는 캔들과 아직 수집하지 않은 캔들을 메타데이터로 구분하여 처리
"""
import asyncio
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from upbit_auto_trading.infrastructure.logging import create_component_logger


class CollectionStatus(Enum):
    """캔들 수집 상태"""
    PENDING = "PENDING"      # 아직 수집 시도하지 않음
    COLLECTED = "COLLECTED"  # 실제 데이터 수집 완료
    EMPTY = "EMPTY"         # 실제로 거래가 없음 (API 확인됨)
    FAILED = "FAILED"       # 수집 실패 (네트워크/API 오류)


@dataclass
class CandleCollectionRecord:
    """캔들 수집 기록"""
    symbol: str
    timeframe: str
    target_time: datetime
    status: CollectionStatus
    last_attempt_at: Optional[datetime] = None
    attempt_count: int = 0
    api_response_code: Optional[int] = None


class CandleCollectionStatusManager:
    """캔들 수집 상태 관리자"""

    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path
        self.logger = create_component_logger("CandleCollectionStatusManager")
        self._init_tables()

    def _init_tables(self):
        """수집 상태 테이블 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS candle_collection_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    target_time TEXT NOT NULL,  -- 'YYYY-MM-DD HH:MM:SS'
                    collection_status TEXT NOT NULL,  -- 'COLLECTED', 'EMPTY', 'PENDING', 'FAILED'
                    last_attempt_at TEXT,
                    attempt_count INTEGER DEFAULT 0,
                    api_response_code INTEGER,  -- 200, 404, etc
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

                    UNIQUE(symbol, timeframe, target_time)
                );
            """)

            # 인덱스 생성
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_candle_collection_lookup
                ON candle_collection_status(symbol, timeframe, target_time);
            """)

            conn.commit()
            self.logger.info("캔들 수집 상태 테이블 초기화 완료")

    def get_collection_status(self, symbol: str, timeframe: str,
                            target_time: datetime) -> Optional[CandleCollectionRecord]:
        """수집 상태 조회"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, timeframe, target_time, collection_status,
                       last_attempt_at, attempt_count, api_response_code
                FROM candle_collection_status
                WHERE symbol = ? AND timeframe = ? AND target_time = ?
            """, (symbol, timeframe, target_time.strftime("%Y-%m-%d %H:%M:%S")))

            result = cursor.fetchone()

            if result:
                return CandleCollectionRecord(
                    symbol=result[0],
                    timeframe=result[1],
                    target_time=datetime.fromisoformat(result[2]),
                    status=CollectionStatus(result[3]),
                    last_attempt_at=datetime.fromisoformat(result[4]) if result[4] else None,
                    attempt_count=result[5],
                    api_response_code=result[6]
                )

            return None

    def insert_collection_status(self, symbol: str, timeframe: str,
                               target_time: datetime, status: CollectionStatus):
        """새 수집 상태 등록"""

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO candle_collection_status
                (symbol, timeframe, target_time, collection_status, last_attempt_at, attempt_count)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
            """, (
                symbol, timeframe,
                target_time.strftime("%Y-%m-%d %H:%M:%S"),
                status.value
            ))
            conn.commit()

    def update_collection_status(self, symbol: str, timeframe: str,
                               target_time: datetime, status: CollectionStatus,
                               api_response_code: Optional[int] = None):
        """수집 상태 업데이트"""

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE candle_collection_status
                SET collection_status = ?, last_attempt_at = CURRENT_TIMESTAMP,
                    attempt_count = attempt_count + 1, api_response_code = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE symbol = ? AND timeframe = ? AND target_time = ?
            """, (
                status.value, api_response_code,
                symbol, timeframe, target_time.strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

    def get_status_summary(self, symbol: str, timeframe: str,
                         start_time: datetime, end_time: datetime) -> Dict[str, int]:
        """시간 범위 내 수집 상태 요약"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT collection_status, COUNT(*)
                FROM candle_collection_status
                WHERE symbol = ? AND timeframe = ?
                  AND target_time BETWEEN ? AND ?
                GROUP BY collection_status
            """, (
                symbol, timeframe,
                start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time.strftime("%Y-%m-%d %H:%M:%S")
            ))

            results = cursor.fetchall()
            return {status: count for status, count in results}

class SmartCandleCollector:
    """빈 캔들과 미수집 캔들을 구분하는 지능형 수집기"""

    def __init__(self, upbit_client, candle_db_manager):
        self.upbit_client = upbit_client
        self.candle_db_manager = candle_db_manager
        self.status_manager = CandleCollectionStatusManager()
        self.logger = create_component_logger("SmartCandleCollector")

    async def ensure_candle_range(self, symbol: str, timeframe: str,
                                start_time: datetime, end_time: datetime) -> List[Dict]:
        """지정된 시간 범위의 모든 캔들 확보 (빈 캔들 포함)"""

        self.logger.info(f"캔들 범위 확보 시작: {symbol} {timeframe} {start_time} ~ {end_time}")

        # 1. 시간 범위 내 모든 예상 캔들 시간 생성
        expected_times = self._generate_expected_candle_times(
            start_time, end_time, timeframe
        )

        self.logger.debug(f"예상 캔들 시간 {len(expected_times)}개 생성")

        # 2. 각 시간의 수집 상태 확인
        collection_status = self._check_collection_status(
            symbol, timeframe, expected_times
        )

        # 3. 미수집/실패 캔들 재수집
        await self._collect_missing_candles(symbol, timeframe, collection_status)

        # 4. 최종 캔들 데이터 구성 (실제 + 채움)
        final_candles = await self._build_final_candle_data(
            symbol, timeframe, expected_times
        )

        self.logger.info(f"캔들 범위 확보 완료: {len(final_candles)}개")
        return final_candles

    def _generate_expected_candle_times(self, start_time: datetime,
                                      end_time: datetime, timeframe: str) -> List[datetime]:
        """예상되는 모든 캔들 시간 생성"""
        times = []
        current = start_time

        # 타임프레임에 따른 시간 간격 설정
        timeframe_deltas = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1)
        }

        if timeframe not in timeframe_deltas:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        delta = timeframe_deltas[timeframe]

        while current <= end_time:
            times.append(current)
            current += delta

        return times

    def _check_collection_status(self, symbol: str, timeframe: str,
                               expected_times: List[datetime]) -> Dict[datetime, CollectionStatus]:
        """각 시간의 수집 상태 확인"""

        status_map = {}
        new_pending_count = 0

        for target_time in expected_times:
            # DB에서 수집 상태 조회
            record = self.status_manager.get_collection_status(
                symbol, timeframe, target_time
            )

            if record is None:
                # 처음 보는 시간 → PENDING
                status_map[target_time] = CollectionStatus.PENDING
                self.status_manager.insert_collection_status(
                    symbol, timeframe, target_time, CollectionStatus.PENDING
                )
                new_pending_count += 1
            else:
                status_map[target_time] = record.status

        if new_pending_count > 0:
            self.logger.debug(f"새 PENDING 캔들 {new_pending_count}개 등록")

        # 상태별 통계
        status_counts = {}
        for status in status_map.values():
            status_counts[status] = status_counts.get(status, 0) + 1

        self.logger.debug(f"수집 상태 분포: {status_counts}")
        return status_map

    async def _collect_missing_candles(self, symbol: str, timeframe: str,
                                     status_map: Dict[datetime, CollectionStatus]):
        """미수집 또는 실패한 캔들들 수집"""

        missing_times = [
            time for time, status in status_map.items()
            if status in [CollectionStatus.PENDING, CollectionStatus.FAILED]
        ]

        if not missing_times:
            self.logger.debug("미수집 캔들 없음")
            return

        self.logger.info(f"미수집 캔들 {len(missing_times)}개 수집 시작: {symbol} {timeframe}")

        # 배치로 처리 (API 효율성)
        batch_size = 200  # 업비트 API 최대 200개
        collected_count = 0
        empty_count = 0
        failed_count = 0

        for i in range(0, len(missing_times), batch_size):
            batch_times = missing_times[i:i + batch_size]

            try:
                # 배치 범위 계산
                batch_start = min(batch_times)
                batch_end = max(batch_times) + timedelta(minutes=1)

                # API 요청
                candles = await self._request_candle_batch(
                    symbol, timeframe, batch_start, batch_end
                )

                # 수집된 캔들과 요청 시간 매칭
                collected_times = set()
                if candles:
                    for candle in candles:
                        candle_time = self._parse_candle_time(candle)
                        if candle_time in batch_times:
                            # 실제 캔들 데이터 저장
                            await self._save_candle_data(candle)
                            self.status_manager.update_collection_status(
                                symbol, timeframe, candle_time,
                                CollectionStatus.COLLECTED, api_response_code=200
                            )
                            collected_times.add(candle_time)
                            collected_count += 1

                # 수집되지 않은 시간들 → EMPTY 처리
                for target_time in batch_times:
                    if target_time not in collected_times:
                        self.status_manager.update_collection_status(
                            symbol, timeframe, target_time,
                            CollectionStatus.EMPTY, api_response_code=404
                        )
                        empty_count += 1

                # API 요청 간격 (Rate Limit 고려)
                if i + batch_size < len(missing_times):
                    await asyncio.sleep(0.1)

            except Exception as e:
                # 배치 전체 실패 처리
                for target_time in batch_times:
                    self.status_manager.update_collection_status(
                        symbol, timeframe, target_time,
                        CollectionStatus.FAILED, api_response_code=500
                    )
                    failed_count += 1

                self.logger.error(f"배치 수집 실패: {batch_start} ~ {batch_end}, {e}")

        self.logger.info(f"수집 완료 - 수집됨: {collected_count}, 빈캔들: {empty_count}, 실패: {failed_count}")

    async def _request_candle_batch(self, symbol: str, timeframe: str,
                                  start_time: datetime, end_time: datetime) -> List[Dict]:
        """배치 캔들 요청"""

        try:
            # 업비트 API 호출
            candles = await self.upbit_client.get_candles_minutes(
                symbol=symbol,
                unit=int(timeframe.replace('m', '')),  # '1m' -> 1
                to=end_time.isoformat(),
                count=200
            )

            self.logger.debug(f"API 응답: {len(candles) if candles else 0}개 캔들")
            return candles or []

        except Exception as e:
            self.logger.error(f"API 요청 실패: {symbol} {timeframe} {start_time}~{end_time}, {e}")
            raise

    def _parse_candle_time(self, candle: Dict) -> datetime:
        """캔들 시간 파싱"""
        time_str = candle.get('candle_date_time_kst', '')
        return datetime.fromisoformat(time_str.replace('T', ' ').replace('Z', ''))

    async def _save_candle_data(self, candle: Dict):
        """캔들 데이터 저장"""
        try:
            await self.candle_db_manager.insert_candle(candle)
        except Exception as e:
            self.logger.error(f"캔들 저장 실패: {candle.get('candle_date_time_kst')}, {e}")

    async def _build_final_candle_data(self, symbol: str, timeframe: str,
                                     expected_times: List[datetime]) -> List[Dict]:
        """최종 캔들 데이터 구성 (실제 + 채움)"""

        final_candles = []
        last_real_price = None
        fill_count = 0

        for target_time in expected_times:
            # 수집 상태 확인
            status_record = self.status_manager.get_collection_status(
                symbol, timeframe, target_time
            )

            if status_record and status_record.status == CollectionStatus.COLLECTED:
                # 실제 데이터 조회
                real_candle = await self._get_stored_candle_data(
                    symbol, timeframe, target_time
                )

                if real_candle:
                    # 실제 캔들 추가
                    candle_data = {
                        **real_candle,
                        'is_real_trade': True,
                        'fill_method': None
                    }
                    final_candles.append(candle_data)
                    last_real_price = real_candle.get('trade_price')

            elif status_record and status_record.status == CollectionStatus.EMPTY:
                # 빈 캔들 → 채움 데이터 생성
                if last_real_price is not None:
                    fill_candle = self._create_fill_candle(
                        symbol, timeframe, target_time, last_real_price
                    )
                    final_candles.append(fill_candle)
                    fill_count += 1
                else:
                    self.logger.warning(f"채움 불가 (이전 가격 없음): {target_time}")

            else:
                # PENDING 또는 FAILED → 경고 로그
                status = status_record.status if status_record else "UNKNOWN"
                self.logger.warning(f"미처리 캔들: {target_time}, 상태: {status}")

        if fill_count > 0:
            self.logger.info(f"빈 캔들 {fill_count}개 채움 완료")

        return final_candles

    async def _get_stored_candle_data(self, symbol: str, timeframe: str,
                                    target_time: datetime) -> Optional[Dict]:
        """저장된 캔들 데이터 조회"""
        try:
            return await self.candle_db_manager.get_candle(
                symbol, timeframe, target_time
            )
        except Exception as e:
            self.logger.error(f"캔들 조회 실패: {symbol} {timeframe} {target_time}, {e}")
            return None

    def _create_fill_candle(self, symbol: str, timeframe: str,
                          target_time: datetime, last_price: float) -> Dict:
        """채움 캔들 데이터 생성"""

        return {
            'market': symbol,
            'candle_date_time_kst': target_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'opening_price': last_price,
            'high_price': last_price,
            'low_price': last_price,
            'trade_price': last_price,
            'timestamp': int(target_time.timestamp() * 1000),
            'candle_acc_trade_price': 0.0,
            'candle_acc_trade_volume': 0.0,
            'is_real_trade': False,
            'fill_method': 'last_price',
            'created_by': 'SmartCandleCollector'
        }

class ChartDataProvider:
    """차트용 연속 데이터 제공자"""

    def __init__(self, smart_collector: SmartCandleCollector):
        self.smart_collector = smart_collector
        self.logger = create_component_logger("ChartDataProvider")

    async def get_continuous_candles(self, symbol: str, timeframe: str,
                                   start_time: datetime, end_time: datetime,
                                   include_empty: bool = True) -> List[Dict]:
        """차트용 연속 캔들 데이터 제공"""

        self.logger.info(f"연속 캔들 데이터 요청: {symbol} {timeframe}, 빈캔들포함={include_empty}")

        # 스마트 수집기로 완전한 데이터 확보
        all_candles = await self.smart_collector.ensure_candle_range(
            symbol, timeframe, start_time, end_time
        )

        if include_empty:
            # 빈 캔들 포함 (차트용)
            result = all_candles
        else:
            # 실제 거래 캔들만 반환 (매매 지표 계산용)
            result = [candle for candle in all_candles if candle.get('is_real_trade', True)]

        real_count = len([c for c in all_candles if c.get('is_real_trade', True)])
        fill_count = len(all_candles) - real_count

        self.logger.info(f"데이터 제공 완료: 전체 {len(result)}개 (실제: {real_count}, 채움: {fill_count})")
        return result

    def is_candle_empty(self, candle: Dict) -> bool:
        """빈 캔들 여부 확인"""
        return not candle.get('is_real_trade', True)

    def get_fill_method(self, candle: Dict) -> Optional[str]:
        """채움 방식 확인"""
        return candle.get('fill_method')

    def separate_data_for_chart_and_indicators(self, candles: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """차트용과 지표계산용 데이터 분리"""

        chart_data = candles  # 모든 캔들 (연속성)
        indicator_data = [c for c in candles if c.get('is_real_trade', True)]  # 실제 거래만

        return chart_data, indicator_data
