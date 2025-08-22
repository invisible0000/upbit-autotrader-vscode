"""
우선순위별 큐 관리 및 부하 제어 시스템

다양한 우선순위의 요청을 효율적으로 관리하고
시스템 부하를 제어합니다.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import heapq

from upbit_auto_trading.infrastructure.logging import create_component_logger


logger = create_component_logger("PriorityQueueManager")


class Priority(Enum):
    """요청 우선순위"""
    CRITICAL = 1    # 실거래봇 (< 50ms)
    HIGH = 2        # 실시간 모니터링 (< 100ms)
    NORMAL = 3      # 차트뷰어 (< 500ms)
    LOW = 4         # 백테스터 (백그라운드)


@dataclass
class PriorityRequest:
    """우선순위 요청"""
    id: str
    priority: Priority
    request_data: Dict[str, Any]
    callback: Callable
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    timeout_seconds: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3

    def __lt__(self, other):
        """우선순위 비교 (heapq용)"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        # 같은 우선순위면 생성 시간으로 정렬 (FIFO)
        return self.created_at < other.created_at

    @property
    def is_expired(self) -> bool:
        """타임아웃 여부 확인"""
        if self.timeout_seconds is None:
            return False

        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.timeout_seconds

    @property
    def can_retry(self) -> bool:
        """재시도 가능 여부"""
        return self.retry_count < self.max_retries


@dataclass
class QueueStats:
    """큐 통계"""
    total_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    retry_requests: int = 0
    average_wait_time_ms: float = 0.0
    average_processing_time_ms: float = 0.0
    queue_lengths_by_priority: Dict[Priority, int] = field(default_factory=dict)
    throughput_per_minute: float = 0.0


class LoadController:
    """부하 제어기"""

    def __init__(self, max_concurrent_requests: int = 10):
        self.max_concurrent_requests = max_concurrent_requests
        self.current_load = 0
        self.rate_limits: Dict[str, float] = {
            "api_calls_per_second": 10.0,
            "requests_per_minute": 600.0
        }
        self.recent_requests: List[datetime] = []
        self.logger = logger

    def can_process_request(self, priority: Priority) -> bool:
        """요청 처리 가능 여부 확인"""

        # 동시 처리 한도 확인
        if self.current_load >= self.max_concurrent_requests:
            # CRITICAL 우선순위는 항상 처리 허용
            if priority != Priority.CRITICAL:
                return False

        # Rate limit 확인
        now = datetime.now()

        # 1초 내 요청 수 확인
        recent_1s = [req for req in self.recent_requests if (now - req).total_seconds() <= 1.0]
        if len(recent_1s) >= self.rate_limits["api_calls_per_second"]:
            if priority != Priority.CRITICAL:
                return False

        # 1분 내 요청 수 확인
        recent_1m = [req for req in self.recent_requests if (now - req).total_seconds() <= 60.0]
        if len(recent_1m) >= self.rate_limits["requests_per_minute"]:
            if priority != Priority.CRITICAL:
                return False

        return True

    def acquire_slot(self, priority: Priority) -> bool:
        """처리 슬롯 획득"""
        if self.can_process_request(priority):
            self.current_load += 1
            self.recent_requests.append(datetime.now())

            # 오래된 요청 기록 정리 (메모리 절약)
            cutoff = datetime.now() - timedelta(minutes=2)
            self.recent_requests = [req for req in self.recent_requests if req > cutoff]

            return True
        return False

    def release_slot(self):
        """처리 슬롯 해제"""
        if self.current_load > 0:
            self.current_load -= 1

    def get_load_info(self) -> Dict[str, Any]:
        """현재 부하 정보"""
        now = datetime.now()
        recent_1s = len([req for req in self.recent_requests if (now - req).total_seconds() <= 1.0])
        recent_1m = len([req for req in self.recent_requests if (now - req).total_seconds() <= 60.0])

        return {
            "current_concurrent_load": self.current_load,
            "max_concurrent_requests": self.max_concurrent_requests,
            "requests_last_second": recent_1s,
            "requests_last_minute": recent_1m,
            "utilization_percentage": (self.current_load / self.max_concurrent_requests) * 100
        }


class PriorityQueueManager:
    """우선순위 큐 관리자"""

    def __init__(self, max_concurrent_requests: int = 10):
        self.priority_queues: Dict[Priority, List[PriorityRequest]] = {
            priority: [] for priority in Priority
        }
        self.load_controller = LoadController(max_concurrent_requests)
        self.processing_requests: Dict[str, PriorityRequest] = {}
        self.completed_requests: List[PriorityRequest] = []
        self.stats = QueueStats()
        self.logger = logger

        # 비동기 처리를 위한 이벤트 루프
        self._processing_task: Optional[asyncio.Task] = None
        self._shutdown = False

        # 통계 수집을 위한 시간 추적
        self._last_stats_update = datetime.now()

    async def start(self):
        """큐 매니저 시작"""
        if self._processing_task is None:
            self._processing_task = asyncio.create_task(self._process_queue_loop())
            self.logger.info("Priority queue manager started")

    async def stop(self):
        """큐 매니저 종료"""
        self._shutdown = True
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            self._processing_task = None
        self.logger.info("Priority queue manager stopped")

    async def submit_request(
        self,
        request_id: str,
        priority: Priority,
        request_data: Dict[str, Any],
        callback: Callable,
        timeout_seconds: Optional[float] = None
    ) -> bool:
        """요청 제출"""

        # 타임아웃 기본값 설정
        if timeout_seconds is None:
            timeout_defaults = {
                Priority.CRITICAL: 5.0,
                Priority.HIGH: 10.0,
                Priority.NORMAL: 30.0,
                Priority.LOW: 120.0
            }
            timeout_seconds = timeout_defaults.get(priority, 30.0)

        request = PriorityRequest(
            id=request_id,
            priority=priority,
            request_data=request_data,
            callback=callback,
            timeout_seconds=timeout_seconds
        )

        # 우선순위 큐에 추가
        heapq.heappush(self.priority_queues[priority], request)

        self.stats.total_requests += 1

        self.logger.debug(
            f"Request submitted to {priority.name} queue",
            extra={
                "request_id": request_id,
                "queue_length": len(self.priority_queues[priority]),
                "timeout_seconds": timeout_seconds
            }
        )

        return True

    async def _process_queue_loop(self):
        """큐 처리 메인 루프"""

        while not self._shutdown:
            try:
                # 만료된 요청 정리
                await self._cleanup_expired_requests()

                # 처리 가능한 요청 찾기
                next_request = self._get_next_processable_request()

                if next_request:
                    # 비동기로 요청 처리
                    asyncio.create_task(self._process_request(next_request))
                else:
                    # 처리할 요청이 없으면 잠시 대기
                    await asyncio.sleep(0.01)  # 10ms 대기

                # 주기적으로 통계 업데이트
                await self._update_stats_if_needed()

            except Exception as e:
                self.logger.error(f"Error in queue processing loop: {e}")
                await asyncio.sleep(0.1)  # 오류 시 잠시 대기

    def _get_next_processable_request(self) -> Optional[PriorityRequest]:
        """처리 가능한 다음 요청 찾기"""

        # 우선순위 순서로 확인 (CRITICAL -> HIGH -> NORMAL -> LOW)
        for priority in Priority:
            queue = self.priority_queues[priority]

            if queue and self.load_controller.can_process_request(priority):
                # 가장 우선순위가 높은 요청 반환
                return heapq.heappop(queue)

        return None

    async def _process_request(self, request: PriorityRequest):
        """개별 요청 처리"""

        # 부하 제어 슬롯 획득
        if not self.load_controller.acquire_slot(request.priority):
            # 슬롯 획득 실패 시 큐에 다시 추가
            heapq.heappush(self.priority_queues[request.priority], request)
            return

        request.started_at = datetime.now()
        self.processing_requests[request.id] = request

        try:
            # 콜백 함수 실행
            if asyncio.iscoroutinefunction(request.callback):
                result = await request.callback(request.request_data)
            else:
                result = request.callback(request.request_data)

            # 성공 처리
            self.stats.completed_requests += 1
            self._record_request_completion(request, success=True)

        except Exception as e:
            self.logger.error(
                f"Request processing failed: {e}",
                extra={"request_id": request.id, "priority": request.priority.name}
            )

            # 재시도 가능한 경우 큐에 다시 추가
            if request.can_retry:
                request.retry_count += 1
                heapq.heappush(self.priority_queues[request.priority], request)
                self.stats.retry_requests += 1
            else:
                self.stats.failed_requests += 1
                self._record_request_completion(request, success=False)

        finally:
            # 슬롯 해제 및 처리 목록에서 제거
            self.load_controller.release_slot()
            if request.id in self.processing_requests:
                del self.processing_requests[request.id]

    async def _cleanup_expired_requests(self):
        """만료된 요청 정리"""

        for priority in Priority:
            queue = self.priority_queues[priority]
            valid_requests = []

            while queue:
                request = heapq.heappop(queue)
                if request.is_expired:
                    self.stats.timeout_requests += 1
                    self._record_request_completion(request, success=False)

                    self.logger.warning(
                        f"Request expired: {request.id}",
                        extra={"priority": priority.name, "age_seconds":
                               (datetime.now() - request.created_at).total_seconds()}
                    )
                else:
                    valid_requests.append(request)

            # 유효한 요청들로 큐 재구성
            for request in valid_requests:
                heapq.heappush(queue, request)

    def _record_request_completion(self, request: PriorityRequest, success: bool):
        """요청 완료 기록"""
        self.completed_requests.append(request)

        # 완료된 요청 기록 제한 (메모리 절약)
        if len(self.completed_requests) > 1000:
            self.completed_requests = self.completed_requests[-500:]

    async def _update_stats_if_needed(self):
        """필요시 통계 업데이트"""
        now = datetime.now()
        if (now - self._last_stats_update).total_seconds() >= 60:  # 1분마다 업데이트
            self._update_stats()
            self._last_stats_update = now

    def _update_stats(self):
        """통계 업데이트"""

        # 큐 길이 업데이트
        self.stats.queue_lengths_by_priority = {
            priority: len(queue) for priority, queue in self.priority_queues.items()
        }

        # 최근 완료된 요청들로 평균 시간 계산
        if self.completed_requests:
            recent_completed = [
                req for req in self.completed_requests
                if req.started_at and (datetime.now() - req.started_at).total_seconds() <= 300  # 5분 이내
            ]

            if recent_completed:
                wait_times = [
                    (req.started_at - req.created_at).total_seconds() * 1000
                    for req in recent_completed if req.started_at
                ]

                if wait_times:
                    self.stats.average_wait_time_ms = sum(wait_times) / len(wait_times)

                # 처리량 계산 (분당 요청 수)
                minute_ago = datetime.now() - timedelta(minutes=1)
                recent_minute = [
                    req for req in recent_completed
                    if req.started_at and req.started_at > minute_ago
                ]
                self.stats.throughput_per_minute = len(recent_minute)

    def get_queue_status(self) -> Dict[str, Any]:
        """큐 상태 조회"""

        return {
            "queue_lengths": {
                priority.name: len(queue)
                for priority, queue in self.priority_queues.items()
            },
            "processing_requests": len(self.processing_requests),
            "load_info": self.load_controller.get_load_info(),
            "stats": {
                "total_requests": self.stats.total_requests,
                "completed_requests": self.stats.completed_requests,
                "failed_requests": self.stats.failed_requests,
                "timeout_requests": self.stats.timeout_requests,
                "retry_requests": self.stats.retry_requests,
                "average_wait_time_ms": self.stats.average_wait_time_ms,
                "throughput_per_minute": self.stats.throughput_per_minute
            }
        }
