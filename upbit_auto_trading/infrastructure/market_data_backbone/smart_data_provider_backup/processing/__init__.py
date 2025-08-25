"""
Smart Data Provider Processing 모듈

대용량 요청 분할, 응답 병합, 우선순위 큐 관리, 백그라운드 처리 등
자동화 기능을 제공합니다.
"""

from .request_splitter import RequestSplitter, SplitRequest, SplitStrategy
from .response_merger import ResponseMerger, SplitResponse, MergedResponse
from .priority_queue import PriorityQueueManager, Priority, PriorityRequest
from .background_processor import BackgroundProcessor, BackgroundTask, TaskStatus, TaskType

__all__ = [
    "RequestSplitter",
    "SplitRequest",
    "SplitStrategy",
    "ResponseMerger",
    "SplitResponse",
    "MergedResponse",
    "PriorityQueueManager",
    "Priority",
    "PriorityRequest",
    "BackgroundProcessor",
    "BackgroundTask",
    "TaskStatus",
    "TaskType"
]
