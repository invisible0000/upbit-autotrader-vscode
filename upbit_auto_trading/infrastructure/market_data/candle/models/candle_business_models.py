"""
📝 Candle Business Models
캔들 데이터 비즈니스 로직의 핵심 모델들 - "소스의 원천"
Created: 2025-09-23
Purpose: 청크 처리의 자연스러운 흐름을 위한 핵심 4개 모델만 통합
Architecture: 단일 소스 원칙 (Single Source of Truth)
핵심 모델:
1. RequestInfo: 요청/시작의 단일 소스
2. CollectionPlan: 계획의 단일 소스
3. ChunkInfo: 개별 처리의 단일 소스
4. OverlapRequest/Result: 분석 지원 모델
설계 원칙:
- RequestInfo + List[ChunkInfo] = 모든 비즈니스 로직의 완전한 소스
- 모니터링은 별도 계층에서 이 핵심 모델들을 참조하는 읽기 전용 뷰
- 복잡한 상태 관리 클래스들(CollectionState, InternalCollectionState 등) 제거
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from enum import Enum
# TimeUtils import 추가 (lazy import 제거를 위해)
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


# ============================================================================
# 🏁 Enum 모델 - 비즈니스 로직 지원
# ============================================================================
class OverlapStatus(Enum):
    """겹침 상태 - OverlapAnalyzer v5.0과 정확히 일치하는 5개 분류"""
    NO_OVERLAP = "no_overlap"                        # 1. 겹침 없음
    COMPLETE_OVERLAP = "complete_overlap"            # 2.1. 완전 겹침
    PARTIAL_START = "partial_start"                  # 2.2.1. 시작 겹침
    PARTIAL_MIDDLE_FRAGMENT = "partial_middle_fragment"    # 2.2.2.1. 중간 겹침 (파편)
    PARTIAL_MIDDLE_CONTINUOUS = "partial_middle_continuous"  # 2.2.2.2. 중간 겹침 (말단)


class ChunkStatus(Enum):
    """청크 처리 상태 - CandleDataProvider v4.0 호환"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# 🎯 RequestInfo - 요청/시작의 단일 소스
# ============================================================================
class RequestType(Enum):
    """요청 타입 분류 - 시간 정렬 및 OverlapAnalyzer 최적화용"""
    COUNT_ONLY = "count_only"      # count만, to=None (첫 청크 OverlapAnalyzer 건너뜀)
    TO_COUNT = "to_count"          # to + count (to만 정렬, OverlapAnalyzer 사용)
    TO_END = "to_end"              # to + end (to만 정렬, OverlapAnalyzer 사용)
    END_ONLY = "end_only"          # end만, COUNT_ONLY처럼 동작 (동적 count 계산)


@dataclass(frozen=True)
class RequestInfo:
    """
    요청 정보 모델 - 사전 계산된 안전한 시간 정렬 지원
    청크 처리의 시작점이자 모든 요청 파라미터의 단일 소스.
    사전 계산을 통해 성능과 일관성을 보장하는 핵심 비즈니스 모델.
    """

    # 필수 파라미터
    symbol: str
    timeframe: str

    # 선택적 파라미터 (원시 입력)
    count: Optional[int] = None
    to: Optional[datetime] = None
    end: Optional[datetime] = None

    # 요청 시점 기록
    request_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # 사전 계산된 필드들 (성능 + 일관성 보장, 항상 존재)
    aligned_to: datetime = field(init=False)
    aligned_end: datetime = field(init=False)
    expected_count: int = field(init=False)

    def __post_init__(self):
        """요청 정보 검증 및 사전 계산"""

        # 기본 파라미터 검증
        if not self.symbol:
            raise ValueError("symbol은 필수입니다")

        if not self.timeframe:
            raise ValueError("timeframe은 필수입니다")

        # count 범위 검증
        if self.count is not None and self.count < 1:
            raise ValueError("count는 1 이상이어야 합니다")

        # 시간 순서 검증 (to > end 이어야 함)
        if self.to is not None and self.end is not None and self.to <= self.end:
            raise ValueError("to 시점은 end 시점보다 미래여야 합니다")

        # count와 end 동시 사용 방지
        if self.count is not None and self.end is not None:
            raise ValueError("count와 end는 동시에 사용할 수 없습니다")

        # 최소 파라미터 조합 확인
        has_count = self.count is not None
        has_to = self.to is not None
        has_end = self.end is not None

        valid_combinations = [
            has_count and not has_end,  # count만 또는 to + count
            has_to and has_end and not has_count,  # to + end
            has_end and not has_count and not has_to  # end만
        ]

        if not any(valid_combinations):
            raise ValueError("유효하지 않은 파라미터 조합입니다")

        # 사전 계산 영역 - 성능 + 일관성 보장 (모든 요청 타입에서 항상 계산)
        request_type = self._get_request_type_internal()

        # 1. aligned_to 계산 (모든 요청 타입에서 항상 존재)
        if request_type in [RequestType.TO_COUNT, RequestType.TO_END]:
            # 사용자 제공 to 시간 기준
            if self.to is None:
                raise ValueError("TO_COUNT 또는 TO_END 요청에서 to 시간이 None일 수 없습니다")
            aligned_to = TimeUtils.align_to_candle_boundary(self.to, self.timeframe)

        else:  # COUNT_ONLY, END_ONLY
            # 요청 시점 기준
            aligned_to = TimeUtils.align_to_candle_boundary(self.request_at, self.timeframe)

        object.__setattr__(self, 'aligned_to', aligned_to)

        # 2. aligned_end 계산 (모든 요청 타입에서 항상 존재)
        if request_type in [RequestType.TO_END, RequestType.END_ONLY]:
            # 사용자 제공 end 시간 기준
            if self.end is None:
                raise ValueError("TO_END 또는 END_ONLY 요청에서 end 시간이 None일 수 없습니다")
            aligned_end = TimeUtils.align_to_candle_boundary(self.end, self.timeframe)

        else:  # COUNT_ONLY, TO_COUNT
            # aligned_to에서 count-1틱 뒤로 계산
            if self.count is None:
                raise ValueError("COUNT_ONLY 또는 TO_COUNT 요청에서 count가 None일 수 없습니다")
            aligned_end = TimeUtils.get_time_by_ticks(aligned_to, self.timeframe, -(self.count - 1))

        object.__setattr__(self, 'aligned_end', aligned_end)

        # 3. expected_count 계산 (모든 요청 타입에서 항상 존재)
        if request_type in [RequestType.COUNT_ONLY, RequestType.TO_COUNT]:
            # 사용자 제공 count
            expected_count = self.count

        else:  # TO_END, END_ONLY
            # 시간 차이로 계산
            expected_count = TimeUtils.calculate_expected_count(aligned_to, aligned_end, self.timeframe)

        object.__setattr__(self, 'expected_count', expected_count)

    def _get_request_type_internal(self) -> RequestType:
        """내부용 요청 타입 계산"""
        has_count = self.count is not None
        has_to = self.to is not None
        has_end = self.end is not None

        if has_count and not has_to and not has_end:
            return RequestType.COUNT_ONLY

        elif has_to and has_count and not has_end:
            return RequestType.TO_COUNT

        elif has_to and has_end and not has_count:
            return RequestType.TO_END

        elif has_end and not has_to and not has_count:
            return RequestType.END_ONLY

        else:
            raise ValueError(f"알 수 없는 요청 타입: count={has_count}, to={has_to}, end={has_end}")

    def get_request_type(self) -> RequestType:
        """요청 타입 자동 분류"""
        return self._get_request_type_internal()

    def should_align_time(self) -> bool:
        """시간 정렬 필요 여부 - TO_COUNT, TO_END만 true"""
        request_type = self.get_request_type()
        return request_type in [RequestType.TO_COUNT, RequestType.TO_END]

    def needs_current_time_fallback(self) -> bool:
        """현재 시간 폴백 필요 여부 - END_ONLY만 true"""
        return self.get_request_type() == RequestType.END_ONLY

    def should_skip_overlap_analysis_for_first_chunk(self) -> bool:
        """첫 청크 OverlapAnalyzer 건너뛸지 - COUNT_ONLY와 END_ONLY만 true"""
        request_type = self.get_request_type()
        return request_type in [RequestType.COUNT_ONLY, RequestType.END_ONLY]

    def get_aligned_to_time(self) -> datetime:
        """사전 계산된 정렬 시간 반환 (항상 존재 보장)"""
        return self.aligned_to

    def get_aligned_end_time(self) -> datetime:
        """사전 계산된 정렬 종료 시간 반환 (항상 존재 보장)"""
        return self.aligned_end

    def get_expected_count(self) -> int:
        """사전 계산된 예상 캔들 개수 반환 (항상 존재 보장)"""
        return self.expected_count

    def to_log_string(self) -> str:
        """사용자 인터페이스 로깅용 문자열 (원시 입력)"""
        request_type = self.get_request_type()
        return (f"RequestInfo[{request_type.value}]: {self.symbol} {self.timeframe}, "
                f"count={self.count}, to={self.to}, end={self.end}")

    def to_internal_log_string(self) -> str:
        """내부 처리 로깅용 문자열 (정규화된 계산값)"""
        request_type = self.get_request_type()
        return (f"RequestInfo[{request_type.value}]: {self.symbol} {self.timeframe}, "
                f"aligned_to={self.aligned_to}, aligned_end={self.aligned_end}, "
                f"expected_count={self.expected_count}")


# ============================================================================
# 🎯 CollectionPlan - 계획의 단일 소스
# ============================================================================
@dataclass
class CollectionPlan:
    """
    수집 계획 모델 - 최소 정보만
    RequestInfo를 기반으로 계산된 수집 계획의 단일 소스.
    청크 분할과 성능 예측을 위한 핵심 정보만 포함.
    """
    total_count: int                        # 총 수집할 캔들 개수
    estimated_chunks: int                   # 예상 청크 수
    estimated_duration_seconds: float      # 예상 소요 시간
    first_chunk_params: Dict[str, Any]      # 첫 번째 청크 요청 파라미터

    def __post_init__(self):
        """계획 정보 검증"""
        if self.total_count <= 0:
            raise ValueError(f"총 개수는 1 이상이어야 합니다: {self.total_count}")
        if self.estimated_chunks <= 0:
            raise ValueError(f"예상 청크 수는 1 이상이어야 합니다: {self.estimated_chunks}")
        if self.estimated_duration_seconds < 0:
            raise ValueError(f"예상 소요시간은 0 이상이어야 합니다: {self.estimated_duration_seconds}")


# ============================================================================
# 🎯 CollectionResult - 수집 결과 요약 (최소 필드)
# ============================================================================


@dataclass
class CollectionResult:
    """ChunkProcessor → CandleDataProvider 연동용 최소 결과 모델"""
    success: bool
    request_start_time: Optional[datetime]
    request_end_time: Optional[datetime]
    error: Optional[Exception] = None


# ============================================================================
# 🎯 ChunkInfo - 개별 처리의 단일 소스
# ============================================================================


@dataclass(frozen=False)  # 실시간 조정을 위해 mutable
class ChunkInfo:
    """
    개별 청크 정보 모델 - 전체 처리 단계 추적 지원
    청크 처리의 개별 단위이자 모든 처리 정보의 단일 소스.
    요청부터 완료까지의 전체 단계를 추적하여 완전한 정보 제공.
    추적 단계:
    1. 요청 단계: 오버랩 분석 결과 기반 API 요청 정보
    2. 응답 단계: 실제 API 응답으로부터 받은 캔들 정보
    3. 최종 단계: 빈 캔들 처리 완료 후 최종 결과 정보
    주요 기능:
    - 단계별 캔들 개수, 시작/종료 시간 추적
    - 전체 처리 과정 요약 정보 제공 (디버깅용)
    - 이전 청크 결과에 따른 동적 시간 범위 조정
    - 4단계 우선순위 시간 추적으로 완전성 보장
    """
    # === 청크 식별 정보 ===
    chunk_id: str                         # 청크 고유 식별자
    chunk_index: int                      # 청크 순서 (0부터 시작)
    symbol: str                           # 거래 심볼
    timeframe: str                        # 타임프레임

    # === 청크 파라미터 (실시간 조정 가능) ===
    count: int                            # 이 청크에서 요청할 캔들 개수
    to: Optional[datetime] = None         # 이 청크의 시작 캔들 시간
    end: Optional[datetime] = None        # 이 청크의 종료 시간

    # === 청크 처리 단계별 추적 필드들 ===
    overlap_status: Optional[OverlapStatus] = None           # 겹침 분석 결과
    chunk_status: ChunkStatus = ChunkStatus.PENDING          # 청크 처리 상태

    # === OverlapResult 통합 필드 (COMPLETE_OVERLAP 지원) ===
    # DB 기존 데이터 정보 (OverlapResult에서 추출)
    db_start: Optional[datetime] = None                     # DB 데이터 시작점
    db_end: Optional[datetime] = None                       # DB 데이터 종료점

    # 요청 단계 (오버랩 분석 결과)
    api_request_count: Optional[int] = None                 # 요청할 API 호출 개수 (부분 겹침 시)
    api_request_start: Optional[datetime] = None            # API 요청 시작점 (부분 겹침 시)
    api_request_end: Optional[datetime] = None              # API 요청 종료점 (부분 겹침 시)

    # API 호출 캐시 파라미터 (재사용)
    api_fetch_count: Optional[int] = None                      # 실제 API 호출에 사용할 count
    api_fetch_to: Optional[datetime] = None                    # 실제 API 호출에 사용할 to 값

    # 응답 단계 (실제 API 응답)
    api_response_count: Optional[int] = None                # 실제 받은 캔들 개수
    api_response_start: Optional[datetime] = None           # 응답 첫 캔들 시간
    api_response_end: Optional[datetime] = None             # 응답 마지막 캔들 시간

    # 최종 처리 단계 (빈 캔들 처리 후)
    final_candle_count: Optional[int] = None                # 최종 캔들 개수
    final_candle_start: Optional[datetime] = None           # 최종 첫 캔들 시간
    final_candle_end: Optional[datetime] = None             # 최종 마지막 캔들 시간

    # 계산된 캔들 수 캐시
    effective_candle_count: Optional[int] = None               # 중첩 반영 최종 캔들 수
    cumulative_candle_count: Optional[int] = None              # 이전 누적을 포함한 총합

    # === 처리 상태 정보 ===
    # status: str = "pending"  # 삭제: chunk_status로 대체
    created_at: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))
    processing_started_at: Optional[datetime] = None  # 처리 시작 시점
    completed_at: Optional[datetime] = None           # 처리 완료 시점

    def __post_init__(self):
        """청크 정보 검증 및 기본값 설정"""
        if not self.chunk_id:
            raise ValueError("청크 ID는 필수입니다")
        if self.chunk_index < 0:
            raise ValueError(f"청크 인덱스는 0 이상이어야 합니다: {self.chunk_index}")
        if self.count < 1 or self.count > 200:
            raise ValueError(f"청크 count는 1~200 범위여야 합니다: {self.count}")
        if not isinstance(self.chunk_status, ChunkStatus):
            raise ValueError(f"잘못된 상태값: {self.chunk_status}")
        self._update_api_fetch_params_from_overlap()

    def adjust_times(self, new_to: Optional[datetime] = None, new_end: Optional[datetime] = None) -> None:
        """실시간 시간 조정 (이전 청크 결과 반영) - UTC 타임존 정규화 적용"""
        if new_to is not None:
            self.to = TimeUtils.normalize_datetime_to_utc(new_to)
        if new_end is not None:
            self.end = TimeUtils.normalize_datetime_to_utc(new_end)
        self._update_api_fetch_params_from_overlap()

    def mark_processing(self) -> None:
        """처리 중 상태로 변경 및 시작 시간 기록"""
        self.chunk_status = ChunkStatus.PROCESSING
        self.processing_started_at = datetime.now(timezone.utc)

    def mark_completed(self) -> None:
        """완료 상태로 변경 및 완료 시간 기록"""
        self.chunk_status = ChunkStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self) -> None:
        """실패 상태로 변경 및 완료 시간 기록 (실패도 완료의 한 형태)"""
        self.chunk_status = ChunkStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)

    def get_processing_duration(self) -> Optional[float]:
        """처리 시간을 초 단위로 반환 (시작~완료 또는 현재 시점)"""
        if not self.processing_started_at:
            return None
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.processing_started_at).total_seconds()

    def is_pending(self) -> bool:
        """대기 중 상태 확인"""
        return self.chunk_status == ChunkStatus.PENDING

    def is_completed(self) -> bool:
        """완료 상태 확인"""
        return self.chunk_status == ChunkStatus.COMPLETED

    def get_effective_end_time(self) -> Optional[datetime]:
        """청크가 담당한 범위의 실제 종료 시각"""
        status = self.overlap_status
        if status == OverlapStatus.COMPLETE_OVERLAP:
            return self.end or self.db_end or self.final_candle_end or self.api_response_end

        if status == OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS:
            return self.db_end or self.final_candle_end or self.api_response_end or self.end

        if status in (OverlapStatus.PARTIAL_START, OverlapStatus.PARTIAL_MIDDLE_FRAGMENT):
            return self.api_response_end or self.final_candle_end or self.end or self.db_end

        if self.api_response_end:
            return self.api_response_end

        if self.final_candle_end:
            return self.final_candle_end

        if self.end:
            return self.end

        return self.db_end

    def get_time_source(self) -> str:
        """시간 정보 출처 반환 (디버깅용)"""
        status = self.overlap_status
        if status == OverlapStatus.COMPLETE_OVERLAP:
            return "planned"
        if status == OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS:
            return "db_overlap"
        if status in (OverlapStatus.PARTIAL_START, OverlapStatus.PARTIAL_MIDDLE_FRAGMENT):
            return "api_response"
        if self.api_response_end:
            return "api_response"
        if self.final_candle_end:
            return "final_processing"
        if self.end:
            return "planned"
        if self.db_end:
            return "db_overlap"
        return "none"

    def has_complete_time_info(self) -> bool:
        """완전한 시간 정보 보유 여부"""
        return self.get_effective_end_time() is not None

    def calculate_effective_candle_count(self) -> int:
        """중첩 상태를 반영한 실효 캔들 수"""
        if self.effective_candle_count is None:
            self.effective_candle_count = self._compute_effective_candle_count()
        return self.effective_candle_count

    def _compute_effective_candle_count(self) -> int:
        """중첩 결과와 응답 데이터를 토대로 실효 수량 계산"""

        # 첫 청크이고 겹침 분석을 안하였으면 final_candle_count 사용
        # final_candle_count이 None이면 API응답이 없었으므로 0
        if self.chunk_index == 0 and not self.has_overlap_info():
            return self.final_candle_count or 0

        status = self.overlap_status

        # 겹침 상태가 없거나 None이면 final_candle_count 사용
        if status is None or status == OverlapStatus.NO_OVERLAP:
            return self.final_candle_count or 0

        # 완전 겹침이면 chunkinfo 범위를 db에서 조회하므로 chunk.count와 동일
        if status == OverlapStatus.COMPLETE_OVERLAP:
            return self.count

        # 처음 겹침이면 처음은 db에 존재하므로 db_start ~ api_response_end
        if status == OverlapStatus.PARTIAL_START:
            if self.db_start and self.api_response_end:
                return TimeUtils.calculate_expected_count(self.db_start, self.api_response_end, self.timeframe)
            return self.final_candle_count or self.count

        if status == OverlapStatus.PARTIAL_MIDDLE_FRAGMENT:
            return self.final_candle_count or 0

        # 말단 겹침이면 처음은 API응답이고 끝은 db에 존재하므로 api_response_start ~ db_end
        if status == OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS:
            if self.to and self.db_end:
                return TimeUtils.calculate_expected_count(self.to, self.db_end, self.timeframe)
            return self.count

        # 안전망: 그 외에 final_candle_count이 있으면 그 값을 사용하고 없으면 0
        return self.final_candle_count or 0

    def update_cumulative_candle_count(self, previous_total: int) -> int:
        """누적 캔들 수를 갱신하고 반환"""
        effective = self.calculate_effective_candle_count()
        self.cumulative_candle_count = previous_total + effective
        return self.cumulative_candle_count

    # === Overlap 최적화 메서드들 ===
    def set_overlap_info(self, overlap_result: 'OverlapResult', api_count: Optional[int] = None) -> None:
        """중첩 분석 결과를 ChunkInfo에 반영"""
        from upbit_auto_trading.infrastructure.logging import create_component_logger

        logger = create_component_logger("ChunkInfo")

        self.overlap_status = overlap_result.status
        self.db_start = TimeUtils.normalize_datetime_to_utc(getattr(overlap_result, 'db_start', None))
        self.db_end = TimeUtils.normalize_datetime_to_utc(getattr(overlap_result, 'db_end', None))
        self.api_request_start = TimeUtils.normalize_datetime_to_utc(overlap_result.api_start)
        self.api_request_end = TimeUtils.normalize_datetime_to_utc(overlap_result.api_end)

        if api_count is not None:
            self.api_request_count = api_count

        elif overlap_result.api_start and overlap_result.api_end:
            self.api_request_count = TimeUtils.calculate_expected_count(
                overlap_result.api_start,
                overlap_result.api_end,
                self.timeframe
            )
        self.effective_candle_count = None
        self.cumulative_candle_count = None

        self._update_api_fetch_params_from_overlap()

        logger.debug(f"OverlapResult 반영 완료: {self.chunk_id}")
        logger.debug(f"  overlap_status: {self.overlap_status}")
        logger.debug(f"  db_range: {self.db_start} ~ {self.db_end}")
        logger.debug(f"  api_request_range: {self.api_request_start} ~ {self.api_request_end}")
        logger.debug(f"  effective_end: {self.get_effective_end_time()}")
        logger.debug(f"  time_source: {self.get_time_source()}")

    def has_overlap_info(self) -> bool:
        """겹침 분석 정보 보유 여부 확인"""
        return self.overlap_status is not None

    def needs_api_call(self) -> bool:
        """API 호출 필요 여부 확인"""
        if not self.has_overlap_info():
            return True  # 겹침 분석 없으면 API 호출 필요
        return self.overlap_status != OverlapStatus.COMPLETE_OVERLAP

    def needs_partial_api_call(self) -> bool:
        """부분 API 호출 필요 여부 확인"""
        if not self.has_overlap_info():
            return False
        return self.overlap_status in [
            OverlapStatus.PARTIAL_START,
            OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS
        ]

    def _update_api_fetch_params_from_overlap(self) -> None:
        """Overlap 상태에 따라 API 호출 파라미터 캐시를 동기화"""
        if not self.has_overlap_info():
            self.api_fetch_count = self.count
            self.api_fetch_to = self.to
            return

        status = self.overlap_status

        if status == OverlapStatus.COMPLETE_OVERLAP:
            self.api_fetch_count = 0
            self.api_fetch_to = None
            return

        if status in (OverlapStatus.PARTIAL_START, OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS):
            fetch_count = self.api_request_count
            if fetch_count is None and self.api_request_start and self.api_request_end:
                fetch_count = TimeUtils.calculate_expected_count(
                    self.api_request_start,
                    self.api_request_end,
                    self.timeframe
                )

            self.api_fetch_count = fetch_count if fetch_count is not None else self.count
            self.api_fetch_to = self.api_request_start if self.api_request_start is not None else self.to

            return
        self.api_fetch_count = self.count
        self.api_fetch_to = self.to

    def get_api_params(self) -> tuple[int, Optional[datetime]]:
        """API 호출 파라미터 반환 (count, to)"""
        if not self.has_overlap_info():
            return self.count, self.to

        if self.overlap_status == OverlapStatus.COMPLETE_OVERLAP:
            return 0, None

        self._update_api_fetch_params_from_overlap()

        fetch_count = (
            self.api_fetch_count
            if self.api_fetch_count is not None and self.api_fetch_count > 0
            else self.count
        )

        fetch_to = self.api_fetch_to if self.api_fetch_to is not None else self.to

        return fetch_count, fetch_to
    # === 단계별 정보 설정 메서드들 ===

    def set_api_response_info(self, candles: List[Dict[str, Any]]) -> None:
        """API 응답 메타데이터 저장"""
        if not candles:
            self.api_response_count = 0
            self.api_response_start = None
            self.api_response_end = None
            self.effective_candle_count = None
            self.cumulative_candle_count = None
            return

        self.api_response_count = len(candles)
        first_candle_time = candles[0]['candle_date_time_utc']
        last_candle_time = candles[-1]['candle_date_time_utc']

        try:
            start_dt = datetime.fromisoformat(first_candle_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(last_candle_time.replace('Z', '+00:00'))
            self.api_response_start = TimeUtils.normalize_datetime_to_utc(start_dt)
            self.api_response_end = TimeUtils.normalize_datetime_to_utc(end_dt)
        except Exception:
            self.api_response_start = None
            self.api_response_end = None

        self.effective_candle_count = None
        self.cumulative_candle_count = None

    def set_final_candle_info(self, candles: List[Dict[str, Any]]) -> None:
        """후처리된 캔들 정보 저장 (빈 캔들 보정 이후)"""
        if not candles:
            self.final_candle_count = 0
            self.final_candle_start = None
            self.final_candle_end = None
            self.effective_candle_count = None
            self.cumulative_candle_count = None
            return

        self.final_candle_count = len(candles)
        first_candle_time = candles[0]['candle_date_time_utc']
        last_candle_time = candles[-1]['candle_date_time_utc']

        try:
            start_dt = datetime.fromisoformat(first_candle_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(last_candle_time.replace('Z', '+00:00'))
            self.final_candle_start = TimeUtils.normalize_datetime_to_utc(start_dt)
            self.final_candle_end = TimeUtils.normalize_datetime_to_utc(end_dt)
        except Exception:
            self.final_candle_start = None
            self.final_candle_end = None

        self.effective_candle_count = None
        self.cumulative_candle_count = None

    @classmethod
    def create_chunk(cls, chunk_index: int, symbol: str, timeframe: str, count: int,
                     to: Optional[datetime] = None, end: Optional[datetime] = None) -> 'ChunkInfo':
        """새 청크 생성 헬퍼 - UTC 타임존 정규화 적용"""
        chunk_id = f"{symbol}_{timeframe}_{chunk_index:03d}"
        return cls(
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            to=TimeUtils.normalize_datetime_to_utc(to),
            end=TimeUtils.normalize_datetime_to_utc(end)
        )


# ============================================================================
# 🎯 OverlapRequest/Result - 분석 지원 모델
# ============================================================================

@dataclass(frozen=True)
class OverlapRequest:
    """겹침 분석 요청 - OverlapAnalyzer v5.0 호환"""
    symbol: str                    # 거래 심볼 (예: 'KRW-BTC')
    timeframe: str                 # 타임프레임 ('1m', '5m', '15m', etc.)
    target_start: datetime         # 요청 시작 시간
    target_end: datetime           # 요청 종료 시간
    target_count: int              # 요청 캔들 개수 (1~200)


@dataclass
class OverlapResult:
    """겹침 분석 결과 - OverlapAnalyzer v5.0 호환"""
    status: OverlapStatus

    # API 요청 범위 (필요시만)
    api_start: Optional[datetime] = None  # API 요청 시작점
    api_end: Optional[datetime] = None    # API 요청 종료점

    # DB 조회 범위 (필요시만)
    db_start: Optional[datetime] = None   # DB 조회 시작점
    db_end: Optional[datetime] = None     # DB 조회 종료점

    # 추가 정보
    partial_end: Optional[datetime] = None    # 연속 데이터의 끝점
    partial_start: Optional[datetime] = None  # 데이터 시작점 (중간 겹침용)

    def __post_init__(self):
        """분석 결과 검증 - v5.0 로직"""
        # 완전 겹침: API 요청 없음
        if self.status == OverlapStatus.COMPLETE_OVERLAP:
            if self.api_start is not None or self.api_end is not None:
                raise ValueError("COMPLETE_OVERLAP에서는 API 요청이 없어야 합니다")

        # 겹침 없음: DB 조회 없음
        if self.status == OverlapStatus.NO_OVERLAP:
            if self.db_start is not None or self.db_end is not None:
                raise ValueError("NO_OVERLAP에서는 DB 조회가 없어야 합니다")


# ============================================================================
# 🎯 헬퍼 함수들 - 단순한 완료 판단 로직
# ============================================================================
def should_complete_collection(request_info: RequestInfo, chunks: List[ChunkInfo]) -> bool:
    """수집 종료 여부를 판단"""
    if not chunks:
        return False

    completed_count = 0

    for chunk in reversed(chunks):
        if not chunk.is_completed():
            continue
        if chunk.cumulative_candle_count is not None:
            completed_count = chunk.cumulative_candle_count
            break
        completed_count += chunk.calculate_effective_candle_count()

    if completed_count >= request_info.expected_count:
        return True

    if request_info.end:
        last_chunk = chunks[-1]
        last_time = last_chunk.get_effective_end_time()
        if last_time and last_time <= request_info.end:
            return True
    return False


def create_collection_plan(
    request_info: RequestInfo,
    chunk_size: int = 200,
    api_rate_limit_rps: float = 10.0
) -> CollectionPlan:
    """
    RequestInfo 기반 수집 계획 생성
    Args:
        request_info: 요청 정보 (사전 계산된 값들 활용)
        chunk_size: 청크 크기 (기본 200)
        api_rate_limit_rps: API 레이트 리미트 (기본 10 RPS)
    Returns:
        CollectionPlan: 수집 계획
    """
    # RequestInfo의 사전 계산된 값들 활용
    total_count = request_info.get_expected_count()

    # 예상 청크 수 계산
    estimated_chunks = (total_count + chunk_size - 1) // chunk_size

    # 예상 완료 시간 계산
    estimated_duration_seconds = estimated_chunks / api_rate_limit_rps

    # 첫 번째 청크 파라미터 생성
    first_chunk_params = _create_first_chunk_params_by_type(request_info, chunk_size)
    return CollectionPlan(
        total_count=total_count,
        estimated_chunks=estimated_chunks,
        estimated_duration_seconds=estimated_duration_seconds,
        first_chunk_params=first_chunk_params
    )


def _create_first_chunk_params_by_type(request_info: RequestInfo, chunk_size: int) -> Dict[str, Any]:
    """요청 타입별 첫 번째 청크 파라미터 생성"""
    request_type = request_info.get_request_type()
    params: Dict[str, Any] = {"market": request_info.symbol}

    if request_type == RequestType.COUNT_ONLY:
        # COUNT_ONLY: to 파라미터 없이 count만 사용 (원시 count 사용)
        chunk_count = min(request_info.expected_count, chunk_size)
        params["count"] = chunk_count

    elif request_type == RequestType.TO_COUNT:
        # to + count: 사전 계산된 정렬 시간 사용 (원시 count 사용)
        chunk_count = min(request_info.expected_count, chunk_size)
        print(f"TO_COUNT 첫 청크 생성: count={chunk_count}, to={request_info.to}")  # debug
        aligned_to = request_info.get_aligned_to_time()
        print("debug: 이 출력이 없으면 aligned_to 계산 실패")  # debug

        # 진입점 보정 (사용자 시간 → 내부 시간 변환)
        first_chunk_start_time = TimeUtils.get_time_by_ticks(aligned_to, request_info.timeframe, -1)
        params["count"] = chunk_count
        params["to"] = first_chunk_start_time

    elif request_type == RequestType.TO_END:
        # to + end: 사전 계산된 정렬 시간 사용 (계산된 expected_count 사용)
        aligned_to = request_info.get_aligned_to_time()
        chunk_count = min(request_info.get_expected_count(), chunk_size)

        # 진입점 보정 (사용자 시간 → 내부 시간 변환)
        first_chunk_start_time = TimeUtils.get_time_by_ticks(aligned_to, request_info.timeframe, -1)
        params["count"] = chunk_count
        params["to"] = first_chunk_start_time

    elif request_type == RequestType.END_ONLY:
        # END_ONLY: COUNT_ONLY처럼 to 없이 count만 사용 (계산된 expected_count 사용)
        chunk_count = min(request_info.get_expected_count(), chunk_size)
        params["count"] = chunk_count
    return params
