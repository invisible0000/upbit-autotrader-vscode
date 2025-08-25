"""
Market Data Manager - 데이터 통합 관리 시스템

Layer 3: 고도화된 데이터 관리 기능 통합
- BatchDB (200개 제한, 겹침 정책)
- OverlapAnalyzer (중복 감지 최적화)
- TimeUtils (캔들 시간 경계 정렬)
- CollectionStatus (빈 캔들 추적)
- BackgroundProcessor (진행률 추적)
"""
import sqlite3
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import time
import uuid

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .market_data_models import (
    CollectionStatus, CollectionStatusRecord, CandleWithStatus,
    TaskStatus, ProgressStep, MarketCondition
)

logger = create_component_logger("MarketDataManager")


class TimeUtils:
    """시간 유틸리티 - 캔들 시간 경계 정렬"""

    @staticmethod
    def parse_timeframe_to_minutes(timeframe: str) -> Optional[int]:
        """타임프레임 문자열을 분 단위로 변환"""
        timeframe = timeframe.lower().strip()

        if timeframe.endswith('m'):
            return int(timeframe[:-1])
        elif timeframe.endswith('h'):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 60 * 24
        elif timeframe.endswith('w'):
            return int(timeframe[:-1]) * 60 * 24 * 7
        else:
            try:
                return int(timeframe)
            except ValueError:
                return None

    @staticmethod
    def align_to_candle_boundary(dt: datetime, timeframe_minutes: int) -> datetime:
        """주어진 시간을 캔들 경계에 맞춰 정렬"""
        if timeframe_minutes < 60:
            # 1시간 미만: 분 단위로 정렬
            aligned_minute = (dt.minute // timeframe_minutes) * timeframe_minutes
            return dt.replace(minute=aligned_minute, second=0, microsecond=0)
        elif timeframe_minutes < 1440:  # 24시간 미만
            # 시간 단위로 정렬
            hours = timeframe_minutes // 60
            aligned_hour = (dt.hour // hours) * hours
            return dt.replace(hour=aligned_hour, minute=0, second=0, microsecond=0)
        else:
            # 일 단위 이상: 자정으로 정렬
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def generate_candle_times(start_time: datetime, end_time: datetime, timeframe: str) -> List[datetime]:
        """시작 시간부터 종료 시간까지 예상되는 캔들 시간 목록 생성"""
        timeframe_minutes = TimeUtils.parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        aligned_start = TimeUtils.align_to_candle_boundary(start_time, timeframe_minutes)
        times = []
        current_time = aligned_start

        while current_time <= end_time:
            times.append(current_time)
            current_time += timedelta(minutes=timeframe_minutes)

        return times


class OverlapAnalyzer:
    """중복 감지 및 최적화 분석기"""

    def __init__(self):
        self._request_history: Dict[str, datetime] = {}
        self._overlap_count = 0
        self._total_requests = 0

    def check_overlap(self, request_key: str, current_time: datetime, ttl_seconds: float = 0.2) -> bool:
        """중복 요청 감지"""
        self._total_requests += 1

        if request_key in self._request_history:
            last_request_time = self._request_history[request_key]
            time_diff = (current_time - last_request_time).total_seconds()

            if time_diff < ttl_seconds:
                self._overlap_count += 1
                return True

        self._request_history[request_key] = current_time
        return False

    def cleanup_expired(self, current_time: datetime, ttl_seconds: float = 0.2) -> int:
        """만료된 요청 기록 정리"""
        expired_keys = []

        for key, timestamp in self._request_history.items():
            if (current_time - timestamp).total_seconds() > ttl_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            del self._request_history[key]

        return len(expired_keys)

    def get_overlap_stats(self) -> Dict[str, Any]:
        """중복 통계 반환"""
        overlap_rate = (self._overlap_count / self._total_requests * 100) if self._total_requests > 0 else 0
        return {
            'total_requests': self._total_requests,
            'overlap_count': self._overlap_count,
            'overlap_rate': round(overlap_rate, 2),
            'active_keys': len(self._request_history)
        }


class BatchDbManager:
    """배치 DB 관리자 - 200개 제한 및 겹침 정책"""

    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path
        self._batch_size = 200
        self._pending_candles: List[Dict[str, Any]] = []
        self._overlap_analyzer = OverlapAnalyzer()

    async def add_candle_batch(self, candles: List[Dict[str, Any]]) -> int:
        """캔들 데이터 배치 추가"""
        if not candles:
            return 0

        # 중복 검사 및 필터링
        filtered_candles = []
        current_time = datetime.now()

        for candle in candles:
            candle_key = f"{candle['symbol']}_{candle['timeframe']}_{candle['timestamp']}"

            if not self._overlap_analyzer.check_overlap(candle_key, current_time):
                filtered_candles.append(candle)

        self._pending_candles.extend(filtered_candles)

        # 200개 단위로 DB에 저장
        saved_count = 0
        while len(self._pending_candles) >= self._batch_size:
            batch = self._pending_candles[:self._batch_size]
            self._pending_candles = self._pending_candles[self._batch_size:]

            saved_count += await self._save_batch_to_db(batch)

        return saved_count

    async def _save_batch_to_db(self, batch: List[Dict[str, Any]]) -> int:
        """배치를 DB에 저장 (UPSERT)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # UPSERT 쿼리 (중복시 업데이트)
                query = """
                INSERT OR REPLACE INTO candles
                (symbol, timeframe, timestamp, open_price, high_price, low_price, close_price, volume, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                batch_data = [
                    (
                        candle['symbol'],
                        candle['timeframe'],
                        candle['timestamp'],
                        candle.get('open_price'),
                        candle.get('high_price'),
                        candle.get('low_price'),
                        candle.get('close_price'),
                        candle.get('volume'),
                        datetime.now()
                    )
                    for candle in batch
                ]

                cursor.executemany(query, batch_data)
                conn.commit()

                logger.debug(f"배치 DB 저장 완료: {len(batch)}개")
                return len(batch)

        except Exception as e:
            logger.error(f"배치 DB 저장 실패: {e}")
            return 0

    async def flush_pending(self) -> int:
        """대기 중인 모든 데이터 강제 저장"""
        if not self._pending_candles:
            return 0

        saved_count = await self._save_batch_to_db(self._pending_candles)
        self._pending_candles.clear()
        return saved_count

    def get_batch_stats(self) -> Dict[str, Any]:
        """배치 통계 반환"""
        overlap_stats = self._overlap_analyzer.get_overlap_stats()
        return {
            'pending_count': len(self._pending_candles),
            'batch_size': self._batch_size,
            'overlap_stats': overlap_stats
        }


class CollectionStatusManager:
    """수집 상태 관리자 - 빈 캔들 추적"""

    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path

    def fill_empty_candles(self, candles: List[Dict[str, Any]], symbol: str,
                          timeframe: str, start_time: datetime, end_time: datetime) -> List[CandleWithStatus]:
        """빈 캔들을 채워서 연속 데이터 생성"""

        # 예상되는 모든 캔들 시간 생성
        expected_times = TimeUtils.generate_candle_times(start_time, end_time, timeframe)

        # 실제 캔들 데이터를 시간별로 매핑
        candle_map = {}
        for candle in candles:
            timestamp = candle.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            candle_map[timestamp] = candle

        # 연속 데이터 생성
        result = []
        for expected_time in expected_times:
            if expected_time in candle_map:
                # 실제 캔들 데이터 존재
                candle_data = candle_map[expected_time]
                candle_with_status = CandleWithStatus(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=expected_time,
                    open_price=Decimal(str(candle_data.get('open_price', 0))),
                    high_price=Decimal(str(candle_data.get('high_price', 0))),
                    low_price=Decimal(str(candle_data.get('low_price', 0))),
                    close_price=Decimal(str(candle_data.get('close_price', 0))),
                    volume=Decimal(str(candle_data.get('volume', 0))),
                    collection_status=CollectionStatus.COLLECTED,
                    is_empty=False
                )
            else:
                # 빈 캔들 생성
                candle_with_status = CandleWithStatus(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=expected_time,
                    collection_status=CollectionStatus.EMPTY,
                    is_empty=True
                )

            result.append(candle_with_status)

        return result


class BackgroundProcessor:
    """백그라운드 작업 진행률 추적"""

    def __init__(self):
        self._active_tasks: Dict[str, Dict[str, Any]] = {}

    def create_task(self, task_id: str, description: str, total_steps: int) -> str:
        """새로운 작업 생성"""
        if not task_id:
            task_id = str(uuid.uuid4())

        self._active_tasks[task_id] = {
            'id': task_id,
            'description': description,
            'status': TaskStatus.PENDING,
            'total_steps': total_steps,
            'completed_steps': 0,
            'started_at': None,
            'completed_at': None,
            'error': None
        }

        logger.info(f"백그라운드 작업 생성: {task_id} - {description}")
        return task_id

    def start_task(self, task_id: str) -> bool:
        """작업 시작"""
        if task_id not in self._active_tasks:
            return False

        self._active_tasks[task_id]['status'] = TaskStatus.RUNNING
        self._active_tasks[task_id]['started_at'] = datetime.now()

        logger.info(f"백그라운드 작업 시작: {task_id}")
        return True

    def update_progress(self, task_id: str, completed_steps: int) -> bool:
        """진행률 업데이트"""
        if task_id not in self._active_tasks:
            return False

        task = self._active_tasks[task_id]
        task['completed_steps'] = min(completed_steps, task['total_steps'])

        # 완료 확인
        if task['completed_steps'] >= task['total_steps']:
            task['status'] = TaskStatus.COMPLETED
            task['completed_at'] = datetime.now()
            logger.info(f"백그라운드 작업 완료: {task_id}")

        return True

    def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """작업 진행률 조회"""
        if task_id not in self._active_tasks:
            return None

        task = self._active_tasks[task_id]
        progress_percentage = (task['completed_steps'] / task['total_steps'] * 100) if task['total_steps'] > 0 else 0

        return {
            'task_id': task_id,
            'description': task['description'],
            'status': task['status'].value,
            'progress_percentage': round(progress_percentage, 1),
            'completed_steps': task['completed_steps'],
            'total_steps': task['total_steps'],
            'started_at': task['started_at'],
            'completed_at': task['completed_at'],
            'error': task['error']
        }

    def cleanup_completed_tasks(self) -> int:
        """완료된 작업 정리"""
        completed_tasks = [
            task_id for task_id, task in self._active_tasks.items()
            if task['status'] in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]

        for task_id in completed_tasks:
            del self._active_tasks[task_id]

        return len(completed_tasks)


class MarketDataManager:
    """데이터 통합 관리 시스템 - Layer 3 메인 클래스"""

    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path
        self.time_utils = TimeUtils()
        self.overlap_analyzer = OverlapAnalyzer()
        self.batch_db_manager = BatchDbManager(db_path)
        self.collection_status_manager = CollectionStatusManager(db_path)
        self.background_processor = BackgroundProcessor()

        logger.info("MarketDataManager 초기화 완료")

    async def process_candle_data(self, candles: List[Dict[str, Any]],
                                symbol: str, timeframe: str) -> Dict[str, Any]:
        """캔들 데이터 종합 처리"""
        start_time = time.time()

        # 1. 배치 DB 저장
        saved_count = await self.batch_db_manager.add_candle_batch(candles)

        # 2. 중복 분석
        overlap_stats = self.overlap_analyzer.get_overlap_stats()

        # 3. 처리 시간 계산
        processing_time_ms = (time.time() - start_time) * 1000

        return {
            'processed_candles': len(candles),
            'saved_candles': saved_count,
            'processing_time_ms': processing_time_ms,
            'overlap_stats': overlap_stats
        }

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """종합 통계 반환"""
        return {
            'batch_stats': self.batch_db_manager.get_batch_stats(),
            'overlap_stats': self.overlap_analyzer.get_overlap_stats(),
            'active_tasks': len(self.background_processor._active_tasks),
            'db_path': self.db_path
        }

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """종합 상태 정보 (API 호환)"""
        return self.get_comprehensive_stats()

    def get_candle_data(self, symbol: str, candle_type: str, count: int = 200) -> Optional[List[Dict[str, Any]]]:
        """캔들 데이터 조회 (API 호환 메서드)"""
        try:
            # 실제 구현에서는 DB 쿼리 수행
            # 여기서는 시뮬레이션 데이터 반환
            import random
            from datetime import timedelta

            candles = []
            base_time = datetime.now()

            for i in range(count):
                candle_time = base_time - timedelta(minutes=i)
                candles.append({
                    'candle_date_time_kst': candle_time.isoformat(),
                    'opening_price': random.uniform(50000, 100000),
                    'high_price': random.uniform(50000, 100000),
                    'low_price': random.uniform(50000, 100000),
                    'trade_price': random.uniform(50000, 100000),
                    'candle_acc_trade_volume': random.uniform(1, 1000),
                    'candle_acc_trade_price': random.uniform(1000000, 10000000)
                })

            return candles

        except Exception as e:
            logger.error(f"캔들 데이터 조회 오류: {e}")
            return None
