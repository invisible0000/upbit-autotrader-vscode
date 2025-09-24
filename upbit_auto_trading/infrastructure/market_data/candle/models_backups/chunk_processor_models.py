"""
📋 ChunkProcessor v2.0 전용 데이터 모델

Created: 2025-09-23
Purpose: ChunkProcessor v2.0의 Legacy 로직 보존과 독립적 사용을 위한 데이터 모델들
Features: CollectionProgress (UI), CollectionResult (완료결과), InternalCollectionState (내부상태)
Architecture: DDD Infrastructure 계층, Immutable 데이터 구조
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Callable, Optional, Dict, Any, List

# 기존 모델들 import
from .candle_collection_models import ChunkInfo
from .candle_request_models import RequestInfo


@dataclass(frozen=True)
class CollectionProgress:
    """
    수집 진행 상황 (UI Progress Callback용)

    실시간으로 UI에 진행 상황을 보고하기 위한 불변 데이터 구조.
    Progress Callback에서 메모리 누수 없이 안전하게 사용할 수 있도록 설계.
    """
    # 기본 정보
    symbol: str
    timeframe: str
    request_id: str

    # 진행 상황
    current_chunk: int
    total_chunks: int
    collected_candles: int
    requested_candles: int

    # 시간 정보
    elapsed_seconds: float
    estimated_remaining_seconds: float
    estimated_completion_time: datetime

    # 상태
    current_status: str  # "analyzing", "fetching", "processing", "storing"
    last_chunk_info: Optional[str] = None  # "수집: 200개 (overlap: NO_OVERLAP)"

    @property
    def progress_percentage(self) -> float:
        """진행률 퍼센트 (0.0 ~ 100.0)"""
        if self.requested_candles <= 0:
            return 0.0
        return (self.collected_candles / self.requested_candles) * 100.0

    def to_summary_string(self) -> str:
        """요약 문자열 반환 (UI 표시용)"""
        return (f"{self.symbol} {self.timeframe} | "
                f"청크: {self.current_chunk}/{self.total_chunks} | "
                f"캔들: {self.collected_candles:,}/{self.requested_candles:,} "
                f"({self.progress_percentage:.1f}%) | "
                f"상태: {self.current_status}")


@dataclass(frozen=True)
class CollectionResult:
    """
    전체 수집 완료 결과

    ChunkProcessor v2.0의 execute_full_collection() 메서드 결과.
    Legacy 호환성과 성능 메트릭을 포함한 완전한 수집 결과 정보.
    """
    success: bool
    collected_count: int
    requested_count: int
    processing_time_seconds: float

    # 오류 정보
    error: Optional[Exception] = None
    error_chunk_id: Optional[str] = None

    # 메타데이터
    chunks_processed: int = 0
    api_calls_made: int = 0
    overlap_optimizations: int = 0
    empty_candles_filled: int = 0

    # 수집 범위 정보 (CandleDataProvider DB 조회용)
    collected_start_time: Optional[datetime] = None
    collected_end_time: Optional[datetime] = None

    # 추가 정보
    completion_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """성공률 (0.0 ~ 1.0)"""
        if self.requested_count <= 0:
            return 0.0
        return self.collected_count / self.requested_count

    @property
    def collection_rate_per_second(self) -> float:
        """초당 수집률"""
        if self.processing_time_seconds <= 0:
            return 0.0
        return self.collected_count / self.processing_time_seconds

    def is_successful(self) -> bool:
        """수집 성공 여부"""
        return self.success and self.error is None

    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 정보"""
        return {
            "processing_time_seconds": self.processing_time_seconds,
            "collection_rate_per_second": self.collection_rate_per_second,
            "success_rate": self.success_rate,
            "api_calls_made": self.api_calls_made,
            "overlap_optimizations": self.overlap_optimizations,
            "empty_candles_filled": self.empty_candles_filled,
            "chunks_processed": self.chunks_processed
        }

    def to_log_string(self) -> str:
        """로그용 요약 문자열"""
        if self.success:
            return (f"수집 완료: {self.collected_count:,}/{self.requested_count:,}개 "
                    f"({self.success_rate:.1%}) in {self.processing_time_seconds:.1f}s "
                    f"[{self.chunks_processed}청크, API {self.api_calls_made}회]")
        else:
            return (f"수집 실패: {self.collected_count:,}/{self.requested_count:,}개 "
                    f"처리 후 오류 - {self.error}")


@dataclass
class InternalCollectionState:
    """
    ChunkProcessor v2.0 내부 전용 상태

    CandleDataProvider의 CollectionState와 분리된 독립적 상태 관리.
    ChunkProcessor가 독립적으로 사용될 때의 내부 상태 추적.
    """
    # 기본 정보
    request_info: RequestInfo
    symbol: str
    timeframe: str

    # 수집 계획
    total_requested: int
    estimated_total_chunks: int

    # 진행 상태
    current_chunk: Optional[ChunkInfo] = None
    completed_chunks: List[ChunkInfo] = field(default_factory=list)
    total_collected: int = 0

    # 시간 정보
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_update_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # 완료 상태
    is_completed: bool = False
    reached_upbit_data_end: bool = False

    # 성능 메트릭
    api_calls_made: int = 0
    overlap_optimizations: int = 0
    empty_candles_filled: int = 0

    @property
    def elapsed_seconds(self) -> float:
        """경과 시간 (초)"""
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()

    @property
    def progress_percentage(self) -> float:
        """진행률 퍼센트"""
        if self.total_requested <= 0:
            return 0.0
        return (self.total_collected / self.total_requested) * 100.0

    @property
    def avg_chunk_duration(self) -> float:
        """평균 청크 처리 시간 (초)"""
        if not self.completed_chunks:
            return 0.0
        return self.elapsed_seconds / len(self.completed_chunks)

    @property
    def estimated_remaining_seconds(self) -> float:
        """예상 남은 시간 (초)"""
        remaining_chunks = self.estimated_total_chunks - len(self.completed_chunks)
        if remaining_chunks <= 0 or self.avg_chunk_duration <= 0:
            return 0.0
        return remaining_chunks * self.avg_chunk_duration

    @property
    def estimated_completion_time(self) -> datetime:
        """예상 완료 시간"""
        return datetime.now(timezone.utc) + timedelta(seconds=self.estimated_remaining_seconds)

    def add_completed_chunk(self, chunk_info: ChunkInfo, saved_count: int) -> None:
        """완료된 청크 추가"""
        self.completed_chunks.append(chunk_info)
        self.total_collected += saved_count
        self.last_update_time = datetime.now(timezone.utc)

    def mark_api_call(self) -> None:
        """API 호출 기록"""
        self.api_calls_made += 1

    def mark_overlap_optimization(self) -> None:
        """겹침 최적화 기록"""
        self.overlap_optimizations += 1

    def mark_empty_candles_filled(self, count: int) -> None:
        """빈 캔들 채우기 기록"""
        self.empty_candles_filled += count

    def get_last_effective_time_datetime(self) -> Optional[datetime]:
        """마지막 유효 시간 (ChunkInfo 기반)"""
        if not self.completed_chunks:
            return None
        return self.completed_chunks[-1].get_effective_end_time()

    def should_complete(self) -> bool:
        """완료 여부 판단 - 로깅 포함"""
        from upbit_auto_trading.infrastructure.logging import create_component_logger
        logger = create_component_logger("InternalCollectionState")

        # 요청 개수 달성
        if self.total_collected >= self.total_requested:
            logger.debug(f"🎯 수집 완료: 개수 달성 ({self.total_collected}/{self.total_requested})")
            return True

        # 업비트 데이터 끝 도달
        if self.reached_upbit_data_end:
            logger.debug("🎯 수집 완료: 업비트 데이터 끝 도달")
            return True

        # 시간 기반 완료 (end 조건)
        if hasattr(self.request_info, 'end') and self.request_info.end:
            last_time = self.get_last_effective_time_datetime()
            if last_time and last_time <= self.request_info.end:
                logger.debug(f"🎯 수집 완료: 시간 도달 ({last_time} <= {self.request_info.end})")
                return True

        return False

    def get_last_time_source(self) -> str:
        """마지막 시간 출처 반환"""
        if not self.completed_chunks:
            return "none"
        return self.completed_chunks[-1].get_time_source()


# Progress Callback 타입 정의
ProgressCallback = Callable[[CollectionProgress], None]


# 팩토리 함수들

def create_success_collection_result(
    collected_count: int,
    requested_count: int,
    processing_time_seconds: float,
    chunks_processed: int = 0,
    api_calls_made: int = 0,
    overlap_optimizations: int = 0,
    empty_candles_filled: int = 0,
    collected_start_time: Optional[datetime] = None,
    collected_end_time: Optional[datetime] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> CollectionResult:
    """성공적인 수집 결과 생성"""
    return CollectionResult(
        success=True,
        collected_count=collected_count,
        requested_count=requested_count,
        processing_time_seconds=processing_time_seconds,
        chunks_processed=chunks_processed,
        api_calls_made=api_calls_made,
        overlap_optimizations=overlap_optimizations,
        empty_candles_filled=empty_candles_filled,
        collected_start_time=collected_start_time,
        collected_end_time=collected_end_time,
        metadata=metadata or {}
    )


def create_error_collection_result(
    error: Exception,
    collected_count: int = 0,
    requested_count: int = 0,
    processing_time_seconds: float = 0.0,
    error_chunk_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> CollectionResult:
    """오류 발생 수집 결과 생성"""
    return CollectionResult(
        success=False,
        collected_count=collected_count,
        requested_count=requested_count,
        processing_time_seconds=processing_time_seconds,
        error=error,
        error_chunk_id=error_chunk_id,
        metadata=metadata or {}
    )


def create_collection_progress(
    state: InternalCollectionState,
    current_status: str,
    last_chunk_info: Optional[str] = None
) -> CollectionProgress:
    """내부 상태로부터 Progress 객체 생성"""
    return CollectionProgress(
        symbol=state.symbol,
        timeframe=state.timeframe,
        request_id=f"{state.symbol}_{state.timeframe}",
        current_chunk=len(state.completed_chunks) + 1,
        total_chunks=state.estimated_total_chunks,
        collected_candles=state.total_collected,
        requested_candles=state.total_requested,
        elapsed_seconds=state.elapsed_seconds,
        estimated_remaining_seconds=state.estimated_remaining_seconds,
        estimated_completion_time=state.estimated_completion_time,
        current_status=current_status,
        last_chunk_info=last_chunk_info
    )
