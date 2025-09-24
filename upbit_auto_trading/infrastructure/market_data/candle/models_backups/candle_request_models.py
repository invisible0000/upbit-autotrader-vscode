"""
📝 Candle Request Models
캔들 데이터 요청/응답 관련 모델들

Created: 2025-09-22
Purpose: API 요청, 분석 결과, 시간 청크 등 요청 관련 데이터 구조
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from enum import Enum

# TYPE_CHECKING을 사용하여 순환 import 방지
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .candle_core_models import CandleData, OverlapStatus


class RequestType(Enum):
    """요청 타입 분류 - 시간 정렬 및 OverlapAnalyzer 최적화용"""
    COUNT_ONLY = "count_only"      # count만, to=None (첫 청크 OverlapAnalyzer 건너뜀)
    TO_COUNT = "to_count"          # to + count (to만 정렬, OverlapAnalyzer 사용)
    TO_END = "to_end"              # to + end (to만 정렬, OverlapAnalyzer 사용)
    END_ONLY = "end_only"          # end만, COUNT_ONLY처럼 동작 (동적 count 계산)


@dataclass
class CandleChunk:
    """200개 청크 처리 단위"""
    symbol: str
    timeframe: str
    start_time: datetime
    count: int
    chunk_index: int              # 청크 순서 (0부터 시작)

    def __post_init__(self):
        """청크 데이터 검증"""
        # ============================================
        # 🔍 VALIDATION ZONE - 성능 최적화시 제거 가능
        # ============================================
        if self.count <= 0 or self.count > 200:
            raise ValueError(f"청크 크기는 1-200 사이여야 합니다: {self.count}")
        if self.chunk_index < 0:
            raise ValueError(f"청크 인덱스는 0 이상이어야 합니다: {self.chunk_index}")
        # ============================================
        # 🔍 END VALIDATION ZONE
        # ============================================


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
    status: 'OverlapStatus'

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
        # 실제 import를 메서드 내에서 수행하여 순환 import 방지
        from .candle_core_models import OverlapStatus

        # ============================================
        # 🔍 VALIDATION ZONE - 성능 최적화시 제거 가능
        # ============================================
        # 완전 겹침: API 요청 없음
        if self.status == OverlapStatus.COMPLETE_OVERLAP:
            if self.api_start is not None or self.api_end is not None:
                raise ValueError("COMPLETE_OVERLAP에서는 API 요청이 없어야 합니다")

        # 겹침 없음: DB 조회 없음
        if self.status == OverlapStatus.NO_OVERLAP:
            if self.db_start is not None or self.db_end is not None:
                raise ValueError("NO_OVERLAP에서는 DB 조회가 없어야 합니다")
        # ============================================
        # 🔍 END VALIDATION ZONE
        # ============================================


@dataclass
class TimeChunk:
    """시간 기반 청크 (TimeUtils 연동용)"""
    start_time: datetime
    end_time: datetime
    expected_count: int           # 예상 캔들 개수

    def __post_init__(self):
        """시간 청크 검증"""
        if self.start_time >= self.end_time:
            raise ValueError("시작 시간이 종료 시간보다 늦습니다")
        if self.expected_count <= 0:
            raise ValueError(f"예상 캔들 개수는 1 이상이어야 합니다: {self.expected_count}")


@dataclass
class CollectionResult:
    """단일 청크 수집 결과"""
    chunk: CandleChunk
    collected_candles: List['CandleData']
    data_source: str              # "db", "api", "mixed"
    api_requests_made: int        # 실제 API 요청 횟수
    collection_time_ms: float    # 수집 소요 시간

    def __post_init__(self):
        """수집 결과 검증"""
        if self.api_requests_made < 0:
            raise ValueError(f"API 요청 횟수는 0 이상이어야 합니다: {self.api_requests_made}")
        if self.collection_time_ms < 0:
            raise ValueError(f"수집 시간은 0 이상이어야 합니다: {self.collection_time_ms}")


@dataclass(frozen=True)
class RequestInfo:
    """
    요청 정보 모델 - 사전 계산된 안전한 시간 정렬 지원
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
        # TimeUtils를 지연 import하여 순환 import 방지
        from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils

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
            aligned_to = TimeUtils.align_to_candle_boundary(self.to, self.timeframe)
        else:  # COUNT_ONLY, END_ONLY
            # 요청 시점 기준
            aligned_to = TimeUtils.align_to_candle_boundary(self.request_at, self.timeframe)
        object.__setattr__(self, 'aligned_to', aligned_to)

        # 2. aligned_end 계산 (모든 요청 타입에서 항상 존재)
        if request_type in [RequestType.TO_END, RequestType.END_ONLY]:
            # 사용자 제공 end 시간 기준
            aligned_end = TimeUtils.align_to_candle_boundary(self.end, self.timeframe)
        else:  # COUNT_ONLY, TO_COUNT
            # aligned_to에서 count-1틱 뒤로 계산
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
