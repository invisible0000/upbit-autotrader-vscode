"""
응답 모델 정의
Smart Data Provider의 응답 구조를 정의합니다.
"""
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ResponseMetadata:
    """응답 메타데이터"""
    priority_used: Any  # Priority 타입 (순환 참조 방지)
    source: str  # "sqlite_cache", "memory_cache", "api", "hybrid", "error"
    response_time_ms: float
    cache_hit: bool = False
    records_count: Optional[int] = None
    split_requests: Optional[int] = None  # 분할된 요청 수
    api_calls_made: Optional[int] = None  # 실제 API 호출 수


@dataclass(frozen=True)
class DataResponse:
    """데이터 응답"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[ResponseMetadata] = None

    @property
    def is_cache_hit(self) -> bool:
        """캐시 히트 여부"""
        return self.metadata.cache_hit if self.metadata else False

    @property
    def response_time_ms(self) -> float:
        """응답 시간 (밀리초)"""
        return self.metadata.response_time_ms if self.metadata else 0.0

    @property
    def data_source(self) -> str:
        """데이터 소스"""
        return self.metadata.source if self.metadata else "unknown"
