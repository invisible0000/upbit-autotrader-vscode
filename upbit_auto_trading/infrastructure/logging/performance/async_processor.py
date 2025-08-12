"""
Asynchronous Log Processing System for LLM Agent Performance Optimization
비동기 로그 처리 시스템 - 메인 스레드 블로킹 방지
"""
import asyncio
import time
import threading
from asyncio import Queue
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

@dataclass
class LogEntry:
    """로그 엔트리 정의"""
    timestamp: datetime
    level: str
    component: str
    message: str
    metadata: Dict[str, Any]
    priority: int = 1  # 1(낮음) ~ 5(긴급)

@dataclass
class ProcessingResult:
    """로그 처리 결과"""
    success: bool
    processed_count: int
    failed_count: int
    processing_time: float
    errors: List[str]

class AsyncLogProcessor:
    """비동기 로그 처리기"""

    def __init__(self, queue_size: int = 10000, worker_count: int = 3,
                 batch_size: int = 100):
        self.queue_size = queue_size
        self.worker_count = worker_count
        self.batch_size = batch_size

        # 비동기 큐와 상태 관리
        self.log_queue: Optional[Queue] = None
        self.priority_queue: Optional[Queue] = None
        self.is_running = False
        self.workers = []

        # 성능 메트릭
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = None

        # 처리 핸들러들
        self.handlers: List[Callable[[LogEntry], None]] = []

        # 스레드 풀 (I/O 집약적 작업용)
        self.thread_pool = ThreadPoolExecutor(max_workers=2)

    async def initialize(self):
        """비동기 프로세서 초기화"""
        self.log_queue = Queue(maxsize=self.queue_size)
        self.priority_queue = Queue(maxsize=1000)  # 우선순위 큐는 작게
        self.is_running = True
        self.start_time = time.time()

        # 워커 코루틴들 시작
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.workers.append(worker)

        # 우선순위 처리 워커
        priority_worker = asyncio.create_task(self._priority_worker_loop())
        self.workers.append(priority_worker)

        print(f"✅ AsyncLogProcessor 초기화 완료 ({self.worker_count} workers)")

    async def add_log_entry(self, log_entry: LogEntry, force_priority: bool = False):
        """로그 엔트리 추가"""
        try:
            if force_priority or log_entry.priority >= 4:
                # 긴급 로그는 우선순위 큐로
                await self.priority_queue.put(log_entry)
            else:
                # 일반 로그는 메인 큐로
                await self.log_queue.put(log_entry)

        except asyncio.QueueFull:
            # 큐가 가득 찬 경우 오래된 엔트리 제거 후 추가
            await self._handle_queue_overflow(log_entry)

    async def _handle_queue_overflow(self, new_entry: LogEntry):
        """큐 오버플로우 처리"""
        try:
            # 가장 오래된 엔트리 제거 (논블로킹)
            old_entry = self.log_queue.get_nowait()
            await self.log_queue.put(new_entry)
            print(f"⚠️ 로그 큐 오버플로우: 오래된 엔트리 제거됨")
        except asyncio.QueueEmpty:
            # 큐가 비어있다면 그냥 추가
            await self.log_queue.put(new_entry)

    async def _worker_loop(self, worker_name: str):
        """워커 루프 - 배치 처리"""
        while self.is_running:
            try:
                batch = []

                # 배치 수집 (타임아웃 포함)
                for _ in range(self.batch_size):
                    try:
                        entry = await asyncio.wait_for(
                            self.log_queue.get(), timeout=0.1
                        )
                        batch.append(entry)
                    except asyncio.TimeoutError:
                        break

                # 배치 처리
                if batch:
                    await self._process_batch(batch, worker_name)

                # 짧은 휴식
                await asyncio.sleep(0.01)

            except Exception as e:
                print(f"❌ Worker {worker_name} error: {e}")
                await asyncio.sleep(0.1)

    async def _priority_worker_loop(self):
        """우선순위 로그 전용 워커"""
        while self.is_running:
            try:
                # 우선순위 로그는 즉시 처리
                entry = await asyncio.wait_for(
                    self.priority_queue.get(), timeout=0.5
                )
                await self._process_single_entry(entry, "priority-worker")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Priority worker error: {e}")
                await asyncio.sleep(0.1)

    async def _process_batch(self, batch: List[LogEntry], worker_name: str):
        """배치 로그 처리"""
        start_time = time.time()

        try:
            # 핸들러들 병렬 실행
            tasks = []
            for handler in self.handlers:
                for entry in batch:
                    task = asyncio.create_task(self._safe_handle_entry(handler, entry))
                    tasks.append(task)

            # 모든 핸들러 완료 대기
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            self.processed_count += len(batch)
            processing_time = time.time() - start_time

            if processing_time > 0.1:  # 100ms 이상 걸린 경우 로그
                print(f"⚠️ {worker_name}: 배치 처리 시간 {processing_time:.3f}s ({len(batch)} entries)")

        except Exception as e:
            self.failed_count += len(batch)
            print(f"❌ 배치 처리 실패 ({worker_name}): {e}")

    async def _process_single_entry(self, entry: LogEntry, worker_name: str):
        """단일 엔트리 처리 (우선순위용)"""
        try:
            tasks = []
            for handler in self.handlers:
                task = asyncio.create_task(self._safe_handle_entry(handler, entry))
                tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            self.processed_count += 1

        except Exception as e:
            self.failed_count += 1
            print(f"❌ 우선순위 엔트리 처리 실패: {e}")

    async def _safe_handle_entry(self, handler: Callable, entry: LogEntry):
        """안전한 핸들러 실행 (예외 처리 포함)"""
        try:
            # I/O 집약적 핸들러는 스레드 풀에서 실행
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.thread_pool, handler, entry)

        except Exception as e:
            print(f"❌ Handler 실행 실패: {e}")

    def add_handler(self, handler: Callable[[LogEntry], None]):
        """로그 처리 핸들러 추가"""
        self.handlers.append(handler)
        print(f"✅ 핸들러 추가됨: {handler.__name__}")

    def remove_handler(self, handler: Callable[[LogEntry], None]):
        """로그 처리 핸들러 제거"""
        if handler in self.handlers:
            self.handlers.remove(handler)
            print(f"🗑️ 핸들러 제거됨: {handler.__name__}")

    async def shutdown(self):
        """비동기 프로세서 종료"""
        print("🔄 AsyncLogProcessor 종료 중...")
        self.is_running = False

        # 모든 워커 완료 대기
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)

        # 스레드 풀 종료
        self.thread_pool.shutdown(wait=True)

        print("✅ AsyncLogProcessor 종료 완료")

    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        runtime = time.time() - (self.start_time or time.time())

        return {
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "success_rate": (self.processed_count / max(self.processed_count + self.failed_count, 1)) * 100,
            "runtime_seconds": runtime,
            "throughput_per_second": self.processed_count / max(runtime, 0.001),
            "queue_sizes": {
                "main_queue": self.log_queue.qsize() if self.log_queue else 0,
                "priority_queue": self.priority_queue.qsize() if self.priority_queue else 0
            },
            "worker_count": self.worker_count,
            "is_running": self.is_running
        }

    async def wait_for_completion(self, timeout: float = 5.0) -> bool:
        """모든 큐가 비워질 때까지 대기"""
        start_wait = time.time()

        while time.time() - start_wait < timeout:
            main_empty = not self.log_queue or self.log_queue.empty()
            priority_empty = not self.priority_queue or self.priority_queue.empty()

            if main_empty and priority_empty:
                return True

            await asyncio.sleep(0.1)

        return False

# 글로벌 프로세서 인스턴스 관리
_global_processor: Optional[AsyncLogProcessor] = None

async def get_async_processor(queue_size: int = 10000,
                             worker_count: int = 3) -> AsyncLogProcessor:
    """글로벌 비동기 프로세서 인스턴스 반환"""
    global _global_processor

    if _global_processor is None:
        _global_processor = AsyncLogProcessor(queue_size, worker_count)
        await _global_processor.initialize()

    return _global_processor

async def shutdown_global_processor():
    """글로벌 프로세서 종료"""
    global _global_processor

    if _global_processor:
        await _global_processor.shutdown()
        _global_processor = None
