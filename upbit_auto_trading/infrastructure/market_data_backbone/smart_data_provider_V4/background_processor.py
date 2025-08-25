"""
백그라운드 진행률 추적 시스템

대용량 데이터 수집 작업의 진행률을 추적하고
클라이언트에게 실시간 피드백을 제공합니다.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import uuid

from upbit_auto_trading.infrastructure.logging import create_component_logger


logger = create_component_logger("BackgroundProcessor")


class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"        # 대기 중
    RUNNING = "running"        # 실행 중
    COMPLETED = "completed"    # 완료
    FAILED = "failed"          # 실패
    CANCELLED = "cancelled"    # 취소


class TaskType(Enum):
    """작업 유형"""
    CANDLE_COLLECTION = "candle_collection"
    TICKER_BATCH = "ticker_batch"
    ORDERBOOK_BATCH = "orderbook_batch"
    DATA_EXPORT = "data_export"
    CACHE_WARMUP = "cache_warmup"


@dataclass
class ProgressStep:
    """진행률 스텝"""
    step_id: str
    description: str
    total_items: int
    completed_items: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """진행률 백분율"""
        if self.total_items == 0:
            return 100.0
        return (self.completed_items / self.total_items) * 100.0

    @property
    def is_completed(self) -> bool:
        """완료 여부"""
        return self.completed_items >= self.total_items

    @property
    def estimated_time_remaining(self) -> Optional[timedelta]:
        """예상 남은 시간"""
        if not self.started_at or self.completed_items == 0:
            return None

        elapsed = datetime.now() - self.started_at
        rate = self.completed_items / elapsed.total_seconds()

        if rate > 0:
            remaining_items = self.total_items - self.completed_items
            remaining_seconds = remaining_items / rate
            return timedelta(seconds=remaining_seconds)

        return None


@dataclass
class BackgroundTask:
    """백그라운드 작업"""
    task_id: str
    task_type: TaskType
    description: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Any] = None

    # 진행률 추적
    steps: List[ProgressStep] = field(default_factory=list)
    current_step_index: int = 0

    # 콜백 함수들
    progress_callback: Optional[Callable] = None
    completion_callback: Optional[Callable] = None

    # 설정
    priority: int = 5  # 1(높음) ~ 10(낮음)
    timeout_seconds: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3

    @property
    def total_progress_percentage(self) -> float:
        """전체 진행률"""
        if not self.steps:
            return 0.0

        total_percentage = sum(step.progress_percentage for step in self.steps)
        return total_percentage / len(self.steps)

    @property
    def current_step(self) -> Optional[ProgressStep]:
        """현재 스텝"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def estimated_total_time_remaining(self) -> Optional[timedelta]:
        """전체 예상 남은 시간"""
        if not self.started_at:
            return None

        current_step = self.current_step
        if not current_step or not current_step.estimated_time_remaining:
            return None

        # 현재 스텝 남은 시간 + 남은 스텝들의 예상 시간
        remaining_time = current_step.estimated_time_remaining

        # 완료된 스텝들의 평균 시간으로 남은 스텝들 시간 추정
        completed_steps = [step for step in self.steps[:self.current_step_index]
                           if step.started_at and step.completed_at]

        if completed_steps:
            avg_step_duration = sum(
                (step.completed_at - step.started_at).total_seconds()
                for step in completed_steps
            ) / len(completed_steps)

            remaining_steps = len(self.steps) - self.current_step_index - 1
            remaining_time += timedelta(seconds=avg_step_duration * remaining_steps)

        return remaining_time

    @property
    def is_expired(self) -> bool:
        """타임아웃 여부"""
        if not self.timeout_seconds or not self.created_at:
            return False

        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.timeout_seconds


class BackgroundProcessor:
    """백그라운드 작업 처리기"""

    def __init__(self, max_concurrent_tasks: int = 3):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: Dict[str, BackgroundTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: List[str] = []  # 최근 완료된 작업 ID 목록

        self.logger = logger
        self._shutdown = False
        self._monitor_task: Optional[asyncio.Task] = None

    async def start(self):
        """백그라운드 처리기 시작"""
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._monitor_tasks())
            self.logger.info("Background processor started")

    async def stop(self):
        """백그라운드 처리기 종료"""
        self._shutdown = True

        # 실행 중인 모든 작업 취소
        for task in self.running_tasks.values():
            task.cancel()

        # 모든 작업이 종료될 때까지 대기
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)

        # 모니터 작업 취소
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        self.logger.info("Background processor stopped")

    def submit_task(
        self,
        task_type: TaskType,
        description: str,
        steps: List[Dict[str, Any]],
        worker_function: Callable,
        worker_args: tuple = (),
        worker_kwargs: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        timeout_seconds: Optional[float] = None,
        progress_callback: Optional[Callable] = None,
        completion_callback: Optional[Callable] = None
    ) -> str:
        """작업 제출"""

        task_id = str(uuid.uuid4())

        # 진행률 스텝 생성
        progress_steps = [
            ProgressStep(
                step_id=f"{task_id}_step_{i}",
                description=step["description"],
                total_items=step["total_items"]
            )
            for i, step in enumerate(steps)
        ]

        task = BackgroundTask(
            task_id=task_id,
            task_type=task_type,
            description=description,
            steps=progress_steps,
            priority=priority,
            timeout_seconds=timeout_seconds,
            progress_callback=progress_callback,
            completion_callback=completion_callback
        )

        # 작업자 함수와 인수 저장
        task.worker_function = worker_function
        task.worker_args = worker_args
        task.worker_kwargs = worker_kwargs or {}

        self.tasks[task_id] = task

        self.logger.info(
            f"Background task submitted: {description}",
            extra={
                "task_id": task_id,
                "task_type": task_type.value,
                "steps_count": len(progress_steps),
                "priority": priority
            }
        )

        return task_id

    async def _monitor_tasks(self):
        """작업 모니터링 루프"""

        while not self._shutdown:
            try:
                # 새로운 작업 시작
                await self._start_pending_tasks()

                # 완료된 작업 정리
                await self._cleanup_completed_tasks()

                # 타임아웃된 작업 처리
                await self._handle_timeout_tasks()

                # 진행률 콜백 호출
                await self._notify_progress_callbacks()

                await asyncio.sleep(1.0)  # 1초마다 모니터링

            except Exception as e:
                self.logger.error(f"Error in task monitoring: {e}")
                await asyncio.sleep(5.0)  # 오류 시 5초 대기

    async def _start_pending_tasks(self):
        """대기 중인 작업 시작"""

        if len(self.running_tasks) >= self.max_concurrent_tasks:
            return

        # 우선순위순으로 대기 중인 작업 찾기
        pending_tasks = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING and task.task_id not in self.running_tasks
        ]

        pending_tasks.sort(key=lambda t: t.priority)

        slots_available = self.max_concurrent_tasks - len(self.running_tasks)

        for task in pending_tasks[:slots_available]:
            await self._start_task(task)

    async def _start_task(self, task: BackgroundTask):
        """개별 작업 시작"""

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        # 첫 번째 스텝 시작
        if task.steps:
            task.steps[0].started_at = datetime.now()

        # 비동기 작업 생성
        async_task = asyncio.create_task(self._execute_task(task))
        self.running_tasks[task.task_id] = async_task

        self.logger.info(
            f"Background task started: {task.description}",
            extra={"task_id": task.task_id}
        )

    async def _execute_task(self, task: BackgroundTask):
        """작업 실행"""

        try:
            # 작업자 함수 실행
            if asyncio.iscoroutinefunction(task.worker_function):
                result = await task.worker_function(
                    task, *task.worker_args, **task.worker_kwargs
                )
            else:
                # 동기 함수는 스레드에서 실행
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, task.worker_function, task, *task.worker_args, **task.worker_kwargs
                )

            # 성공 완료
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

            # 모든 스텝 완료 처리
            for step in task.steps:
                if not step.completed_at:
                    step.completed_items = step.total_items
                    step.completed_at = datetime.now()

            self.logger.info(
                f"Background task completed: {task.description}",
                extra={"task_id": task.task_id, "duration_seconds":
                       (task.completed_at - task.started_at).total_seconds()}
            )

            # 완료 콜백 호출
            if task.completion_callback:
                try:
                    if asyncio.iscoroutinefunction(task.completion_callback):
                        await task.completion_callback(task)
                    else:
                        task.completion_callback(task)
                except Exception as e:
                    self.logger.error(f"Error in completion callback: {e}")

        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            self.logger.warning(f"Background task cancelled: {task.task_id}")
            raise

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)

            self.logger.error(
                f"Background task failed: {task.description} - {e}",
                extra={"task_id": task.task_id}
            )

        finally:
            # 실행 목록에서 제거
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]

            # 완료된 작업 목록에 추가
            self.completed_tasks.append(task.task_id)

            # 완료된 작업 목록 크기 제한
            if len(self.completed_tasks) > 100:
                self.completed_tasks = self.completed_tasks[-50:]

    async def _cleanup_completed_tasks(self):
        """완료된 작업 정리"""

        # 1시간 이상 된 완료/실패 작업 제거
        cutoff_time = datetime.now() - timedelta(hours=1)

        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                and task.completed_at and task.completed_at < cutoff_time):
                tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            if task_id in self.completed_tasks:
                self.completed_tasks.remove(task_id)

    async def _handle_timeout_tasks(self):
        """타임아웃된 작업 처리"""

        for task in self.tasks.values():
            if task.status == TaskStatus.RUNNING and task.is_expired:
                # 실행 중인 태스크 취소
                if task.task_id in self.running_tasks:
                    self.running_tasks[task.task_id].cancel()

                task.status = TaskStatus.FAILED
                task.error = "Task timeout"
                task.completed_at = datetime.now()

                self.logger.warning(
                    f"Background task timed out: {task.task_id}",
                    extra={"timeout_seconds": task.timeout_seconds}
                )

    async def _notify_progress_callbacks(self):
        """진행률 콜백 알림"""

        for task in self.tasks.values():
            if task.status == TaskStatus.RUNNING and task.progress_callback:
                try:
                    if asyncio.iscoroutinefunction(task.progress_callback):
                        await task.progress_callback(task)
                    else:
                        task.progress_callback(task)
                except Exception as e:
                    self.logger.error(f"Error in progress callback: {e}")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""

        task = self.tasks.get(task_id)
        if not task:
            return None

        return {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "description": task.description,
            "status": task.status.value,
            "progress_percentage": task.total_progress_percentage,
            "current_step": {
                "description": task.current_step.description,
                "progress": task.current_step.progress_percentage,
                "completed_items": task.current_step.completed_items,
                "total_items": task.current_step.total_items
            } if task.current_step else None,
            "estimated_time_remaining": task.estimated_total_time_remaining.total_seconds()
                                       if task.estimated_total_time_remaining else None,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error": task.error
        }

    def get_all_tasks_status(self) -> List[Dict[str, Any]]:
        """모든 작업 상태 조회"""

        return [
            self.get_task_status(task_id)
            for task_id in self.tasks.keys()
        ]

    def cancel_task(self, task_id: str) -> bool:
        """작업 취소"""

        task = self.tasks.get(task_id)
        if not task:
            return False

        if task.status == TaskStatus.RUNNING:
            # 실행 중인 태스크 취소
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()

            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()

            self.logger.info(f"Background task cancelled: {task_id}")
            return True

        elif task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()

            self.logger.info(f"Pending task cancelled: {task_id}")
            return True

        return False

    def update_step_progress(self, task_id: str, step_index: int, completed_items: int):
        """스텝 진행률 업데이트"""

        task = self.tasks.get(task_id)
        if not task or step_index >= len(task.steps):
            return

        step = task.steps[step_index]
        step.completed_items = min(completed_items, step.total_items)

        # 스텝 완료 시 다음 스텝으로 이동
        if step.is_completed and not step.completed_at:
            step.completed_at = datetime.now()

            # 다음 스텝 시작
            next_step_index = step_index + 1
            if next_step_index < len(task.steps):
                task.current_step_index = next_step_index
                task.steps[next_step_index].started_at = datetime.now()

    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""

        return {
            "running_tasks": len(self.running_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "total_tasks": len(self.tasks),
            "task_status_counts": {
                status.value: len([t for t in self.tasks.values() if t.status == status])
                for status in TaskStatus
            },
            "recently_completed": len(self.completed_tasks)
        }
