"""
배치 DB 관리자 (Batch DB Manager)

대용량 데이터의 배치 처리를 최적화하여 DB 성능을 극대화합니다.

핵심 기능:
- 배치 INSERT/UPDATE 최적화
- 비동기 저장 큐 시스템
- WAL 모드 + PRAGMA 튜닝
- 트랜잭션 배치 처리
- 메모리 효율적 대용량 처리
"""
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import sqlite3
import threading
import time
from collections import deque
import json

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("BatchDBManager")


class OperationType(Enum):
    """작업 타입"""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    UPSERT = "UPSERT"           # INSERT OR REPLACE
    DELETE = "DELETE"


class Priority(Enum):
    """작업 우선순위"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class BatchOperation:
    """배치 작업"""
    operation_id: str
    table_name: str
    operation_type: OperationType
    data_rows: List[Dict[str, Any]]
    priority: Priority = Priority.NORMAL

    # 메타데이터
    created_at: datetime = field(default_factory=datetime.now)
    estimated_size_mb: float = 0.0
    callback: Optional[Callable] = None

    # 상태
    is_processed: bool = False
    processing_time: Optional[float] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        # 데이터 크기 추정 (JSON 직렬화 기준)
        try:
            sample_size = len(json.dumps(self.data_rows[:10]))
            self.estimated_size_mb = (sample_size * len(self.data_rows) / 10) / (1024 * 1024)
        except Exception:
            self.estimated_size_mb = len(self.data_rows) * 0.001  # 대략적 추정


@dataclass
class BatchConfig:
    """배치 처리 설정"""
    # 배치 크기
    insert_batch_size: int = 1000
    update_batch_size: int = 500
    max_memory_mb: float = 100.0

    # 처리 타이밍
    flush_interval_seconds: float = 10.0
    max_queue_size: int = 10000

    # DB 최적화
    wal_checkpoint_interval: int = 3600  # 1시간
    vacuum_interval: int = 86400         # 24시간
    analyze_interval: int = 3600         # 1시간

    # 성능 튜닝
    enable_concurrent_processing: bool = True
    max_concurrent_batches: int = 3
    timeout_seconds: float = 30.0


class BatchDBManager:
    """
    배치 DB 관리자

    대용량 데이터를 효율적으로 배치 처리합니다.
    """

    def __init__(self, db_connection_factory: Callable[[], sqlite3.Connection]):
        self.db_factory = db_connection_factory
        self.config = BatchConfig()

        # 작업 큐 (우선순위별)
        self.operation_queues: Dict[Priority, deque] = {
            priority: deque() for priority in Priority
        }

        # 상태 관리
        self._is_running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._queue_lock = threading.RLock()

        # 통계
        self.stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "total_rows_processed": 0,
            "total_processing_time": 0.0,
            "last_flush_time": datetime.now(),
            "last_vacuum_time": datetime.now(),
            "last_analyze_time": datetime.now()
        }

        # DB 연결 풀 (간단한 구현)
        self._connection_pool: List[sqlite3.Connection] = []
        self._pool_lock = threading.Lock()

        logger.info("배치 DB 관리자 초기화 완료")

    async def start(self) -> None:
        """배치 처리 시작"""
        if self._is_running:
            logger.warning("배치 DB 관리자가 이미 실행 중입니다")
            return

        self._is_running = True

        # DB 최적화 설정 적용
        await self._optimize_database()

        # 백그라운드 처리 태스크 시작
        self._processor_task = asyncio.create_task(self._background_processor())

        logger.info("배치 DB 관리자 시작됨")

    async def stop(self) -> None:
        """배치 처리 중지"""
        if not self._is_running:
            return

        self._is_running = False

        # 남은 작업 모두 처리
        await self._flush_all_queues()

        # 백그라운드 태스크 중지
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        # 연결 풀 정리
        await self._cleanup_connection_pool()

        logger.info("배치 DB 관리자 중지됨")

    # =====================================
    # 공개 API
    # =====================================

    async def queue_operation(self,
                             table_name: str,
                             operation_type: OperationType,
                             data_rows: List[Dict[str, Any]],
                             priority: Priority = Priority.NORMAL,
                             callback: Optional[Callable] = None) -> str:
        """
        배치 작업 큐에 추가

        Args:
            table_name: 테이블 명
            operation_type: 작업 타입
            data_rows: 데이터 행들
            priority: 우선순위
            callback: 완료 콜백

        Returns:
            작업 ID
        """
        if not self._is_running:
            raise RuntimeError("배치 DB 관리자가 실행되지 않았습니다")

        if not data_rows:
            logger.warning(f"빈 데이터 행: {table_name}")
            return ""

        # 작업 생성
        operation_id = f"{table_name}_{operation_type.value}_{int(time.time() * 1000)}"
        operation = BatchOperation(
            operation_id=operation_id,
            table_name=table_name,
            operation_type=operation_type,
            data_rows=data_rows.copy(),
            priority=priority,
            callback=callback
        )

        # 큐 크기 확인
        total_queue_size = sum(len(queue) for queue in self.operation_queues.values())
        if total_queue_size >= self.config.max_queue_size:
            logger.warning(f"큐 크기 초과: {total_queue_size}, 강제 플러시 실행")
            await self._flush_all_queues()

        # 메모리 사용량 확인
        if operation.estimated_size_mb > self.config.max_memory_mb:
            logger.warning(f"대용량 작업: {operation.estimated_size_mb:.1f}MB, 즉시 처리")
            await self._process_operation(operation)
            return operation_id

        # 큐에 추가
        with self._queue_lock:
            self.operation_queues[priority].append(operation)

        logger.debug(f"배치 작업 큐 추가: {operation_id}, {len(data_rows)}행, "
                    f"크기={operation.estimated_size_mb:.2f}MB")

        return operation_id

    async def insert_candles_batch(self,
                                  symbol: str,
                                  timeframe: str,
                                  candles: List[Dict[str, Any]],
                                  priority: Priority = Priority.NORMAL) -> str:
        """캔들 데이터 배치 삽입"""
        if not candles:
            return ""

        # 데이터 정규화
        normalized_candles = []
        for candle in candles:
            normalized = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': candle.get('candle_date_time_kst') or candle.get('timestamp'),
                'open_price': float(candle.get('opening_price', 0)),
                'high_price': float(candle.get('high_price', 0)),
                'low_price': float(candle.get('low_price', 0)),
                'close_price': float(candle.get('trade_price', 0)),
                'volume': float(candle.get('candle_acc_trade_volume', 0)),
                'value': float(candle.get('candle_acc_trade_price', 0)),
                'created_at': datetime.now().isoformat()
            }
            normalized_candles.append(normalized)

        return await self.queue_operation(
            table_name="candles",
            operation_type=OperationType.UPSERT,
            data_rows=normalized_candles,
            priority=priority
        )

    async def get_queue_status(self) -> Dict[str, Any]:
        """큐 상태 조회"""
        with self._queue_lock:
            queue_sizes = {
                priority.name: len(queue)
                for priority, queue in self.operation_queues.items()
            }

        total_size = sum(queue_sizes.values())
        estimated_memory = sum(
            sum(op.estimated_size_mb for op in queue)
            for queue in self.operation_queues.values()
        )

        return {
            "is_running": self._is_running,
            "total_queued_operations": total_size,
            "queue_sizes_by_priority": queue_sizes,
            "estimated_memory_mb": estimated_memory,
            "max_queue_size": self.config.max_queue_size,
            "stats": self.stats.copy()
        }

    # =====================================
    # 내부 처리 로직
    # =====================================

    async def _background_processor(self) -> None:
        """백그라운드 처리 루프"""
        while self._is_running:
            try:
                await asyncio.sleep(self.config.flush_interval_seconds)

                if not self._is_running:
                    break

                # 큐가 비어있지 않으면 처리
                if self._has_pending_operations():
                    await self._process_next_batch()

                # 정기 유지보수
                await self._periodic_maintenance()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"백그라운드 처리 오류: {e}")
                await asyncio.sleep(1.0)  # 오류 시 짧은 대기

    async def _process_next_batch(self) -> None:
        """다음 배치 처리"""
        # 우선순위 순으로 처리
        for priority in [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW]:
            with self._queue_lock:
                if not self.operation_queues[priority]:
                    continue

                # 배치 크기만큼 추출
                batch_operations = []
                queue = self.operation_queues[priority]

                while queue and len(batch_operations) < self.config.max_concurrent_batches:
                    batch_operations.append(queue.popleft())

            if batch_operations:
                # 병렬 처리
                if self.config.enable_concurrent_processing:
                    tasks = [self._process_operation(op) for op in batch_operations]
                    await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    # 순차 처리
                    for operation in batch_operations:
                        await self._process_operation(operation)

                break  # 한 번에 하나의 우선순위만 처리

    async def _process_operation(self, operation: BatchOperation) -> None:
        """개별 작업 처리"""
        start_time = time.time()

        try:
            conn = await self._get_connection()

            if operation.operation_type == OperationType.INSERT:
                await self._execute_insert_batch(conn, operation)
            elif operation.operation_type == OperationType.UPDATE:
                await self._execute_update_batch(conn, operation)
            elif operation.operation_type == OperationType.UPSERT:
                await self._execute_upsert_batch(conn, operation)
            elif operation.operation_type == OperationType.DELETE:
                await self._execute_delete_batch(conn, operation)

            # 성공 처리
            processing_time = time.time() - start_time
            operation.processing_time = processing_time
            operation.is_processed = True

            # 통계 업데이트
            self.stats["successful_operations"] += 1
            self.stats["total_rows_processed"] += len(operation.data_rows)
            self.stats["total_processing_time"] += processing_time

            logger.debug(f"배치 작업 완료: {operation.operation_id}, "
                        f"{len(operation.data_rows)}행, {processing_time:.2f}s")

            # 콜백 실행
            if operation.callback:
                try:
                    await operation.callback(operation)
                except Exception as e:
                    logger.warning(f"콜백 실행 실패: {operation.operation_id}, {e}")

        except Exception as e:
            # 실패 처리
            operation.error_message = str(e)
            self.stats["failed_operations"] += 1

            logger.error(f"배치 작업 실패: {operation.operation_id}, {e}")

        finally:
            self.stats["total_operations"] += 1
            await self._return_connection(conn)

    async def _execute_upsert_batch(self, conn: sqlite3.Connection, operation: BatchOperation) -> None:
        """UPSERT 배치 실행"""
        if operation.table_name == "candles":
            await self._upsert_candles_optimized(conn, operation.data_rows)
        else:
            # 일반적인 UPSERT 로직
            await self._execute_generic_upsert(conn, operation)

    async def _upsert_candles_optimized(self, conn: sqlite3.Connection, candles: List[Dict]) -> None:
        """캔들 데이터 최적화 UPSERT"""
        if not candles:
            return

        # 배치 크기로 분할 처리
        batch_size = self.config.insert_batch_size

        for i in range(0, len(candles), batch_size):
            batch = candles[i:i + batch_size]

            # 최적화된 INSERT OR REPLACE 쿼리
            query = """
            INSERT OR REPLACE INTO candles (
                symbol, timeframe, timestamp,
                open_price, high_price, low_price, close_price,
                volume, value, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # 데이터 준비
            data_tuples = []
            for candle in batch:
                data_tuples.append((
                    candle['symbol'],
                    candle['timeframe'],
                    candle['timestamp'],
                    candle['open_price'],
                    candle['high_price'],
                    candle['low_price'],
                    candle['close_price'],
                    candle['volume'],
                    candle['value'],
                    candle['created_at']
                ))

            # 배치 실행
            cursor = conn.cursor()
            cursor.executemany(query, data_tuples)
            conn.commit()

            logger.debug(f"캔들 배치 UPSERT 완료: {len(batch)}행")

    async def _execute_generic_upsert(self, conn: sqlite3.Connection, operation: BatchOperation) -> None:
        """일반적인 UPSERT 실행"""
        # 이 부분은 테이블 스키마에 따라 동적으로 구현
        logger.warning(f"일반적인 UPSERT는 아직 구현되지 않음: {operation.table_name}")

    async def _execute_insert_batch(self, conn: sqlite3.Connection, operation: BatchOperation) -> None:
        """INSERT 배치 실행"""
        # 구현 필요
        pass

    async def _execute_update_batch(self, conn: sqlite3.Connection, operation: BatchOperation) -> None:
        """UPDATE 배치 실행"""
        # 구현 필요
        pass

    async def _execute_delete_batch(self, conn: sqlite3.Connection, operation: BatchOperation) -> None:
        """DELETE 배치 실행"""
        # 구현 필요
        pass

    # =====================================
    # DB 최적화 및 유지보수
    # =====================================

    async def _optimize_database(self) -> None:
        """데이터베이스 최적화 설정"""
        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            # WAL 모드 활성화
            cursor.execute("PRAGMA journal_mode=WAL")

            # 성능 최적화 설정
            optimizations = [
                "PRAGMA synchronous=NORMAL",           # 동기화 모드
                "PRAGMA cache_size=10000",            # 캐시 크기 (페이지 수)
                "PRAGMA temp_store=MEMORY",           # 임시 저장소
                "PRAGMA mmap_size=268435456",         # 메모리 맵 크기 (256MB)
                "PRAGMA busy_timeout=30000",          # 대기 시간 (30초)
                "PRAGMA optimize"                     # 최적화 실행
            ]

            for pragma in optimizations:
                cursor.execute(pragma)

            conn.commit()
            await self._return_connection(conn)

            logger.info("데이터베이스 최적화 설정 완료")

        except Exception as e:
            logger.error(f"데이터베이스 최적화 실패: {e}")

    async def _periodic_maintenance(self) -> None:
        """정기 유지보수"""
        now = datetime.now()

        try:
            # WAL 체크포인트
            last_checkpoint = self.stats.get("last_checkpoint_time", self.stats["last_flush_time"])
            if isinstance(last_checkpoint, datetime):
                checkpoint_age = (now - last_checkpoint).total_seconds()
                if checkpoint_age >= self.config.wal_checkpoint_interval:
                    await self._execute_wal_checkpoint()
                    self.stats["last_checkpoint_time"] = now

            # ANALYZE 실행
            analyze_age = (now - self.stats["last_analyze_time"]).total_seconds()
            if analyze_age >= self.config.analyze_interval:
                await self._execute_analyze()
                self.stats["last_analyze_time"] = now

            # VACUUM 실행 (덜 빈번하게)
            vacuum_age = (now - self.stats["last_vacuum_time"]).total_seconds()
            if vacuum_age >= self.config.vacuum_interval:
                await self._execute_vacuum()
                self.stats["last_vacuum_time"] = now

        except Exception as e:
            logger.error(f"정기 유지보수 실패: {e}")

    async def _execute_wal_checkpoint(self) -> None:
        """WAL 체크포인트 실행"""
        try:
            conn = await self._get_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA wal_checkpoint(PASSIVE)")
            await self._return_connection(conn)
            logger.debug("WAL 체크포인트 실행 완료")
        except Exception as e:
            logger.warning(f"WAL 체크포인트 실패: {e}")

    async def _execute_analyze(self) -> None:
        """ANALYZE 실행"""
        try:
            conn = await self._get_connection()
            cursor = conn.cursor()
            cursor.execute("ANALYZE")
            await self._return_connection(conn)
            logger.debug("ANALYZE 실행 완료")
        except Exception as e:
            logger.warning(f"ANALYZE 실패: {e}")

    async def _execute_vacuum(self) -> None:
        """VACUUM 실행"""
        try:
            conn = await self._get_connection()
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            await self._return_connection(conn)
            logger.info("VACUUM 실행 완료")
        except Exception as e:
            logger.warning(f"VACUUM 실패: {e}")

    # =====================================
    # 연결 풀 관리
    # =====================================

    async def _get_connection(self) -> sqlite3.Connection:
        """연결 풀에서 연결 가져오기"""
        with self._pool_lock:
            if self._connection_pool:
                return self._connection_pool.pop()

        # 새 연결 생성
        conn = self.db_factory()
        conn.execute("PRAGMA foreign_keys=ON")  # 외래키 제약 활성화
        return conn

    async def _return_connection(self, conn: sqlite3.Connection) -> None:
        """연결을 풀로 반환"""
        if conn:
            with self._pool_lock:
                if len(self._connection_pool) < 10:  # 최대 10개 연결 유지
                    self._connection_pool.append(conn)
                else:
                    conn.close()

    async def _cleanup_connection_pool(self) -> None:
        """연결 풀 정리"""
        with self._pool_lock:
            for conn in self._connection_pool:
                try:
                    conn.close()
                except Exception:
                    pass
            self._connection_pool.clear()

    # =====================================
    # 유틸리티 메서드
    # =====================================

    def _has_pending_operations(self) -> bool:
        """대기 중인 작업이 있는지 확인"""
        with self._queue_lock:
            return any(len(queue) > 0 for queue in self.operation_queues.values())

    async def _flush_all_queues(self) -> None:
        """모든 큐 비우기"""
        while self._has_pending_operations():
            await self._process_next_batch()

    def __str__(self) -> str:
        total_queued = sum(len(queue) for queue in self.operation_queues.values())
        return (f"BatchDBManager("
                f"running={self._is_running}, "
                f"queued={total_queued}, "
                f"processed={self.stats['total_operations']})")
