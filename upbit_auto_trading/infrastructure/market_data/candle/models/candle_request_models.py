"""
📝 Candle Request Models
캔들 데이터 요청/응답 관련 모델들

Created: 2025-09-22
Purpose: API 요청, 분석 결과, 시간 청크 등 요청 관련 데이터 구조
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Any, Dict

# TYPE_CHECKING을 사용하여 순환 import 방지
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .candle_core_models import CandleData, OverlapStatus


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
    CandleDataProvider v4.1 간략화된 요청 정보 모델

    업비트 API 파라미터 조합을 단순하게 표현:
    - 모든 요청은 최종적으로 to + end 형태로 정규화됨
    """
    # === 필수 파라미터 ===
    symbol: str                           # 거래 심볼 (예: 'KRW-BTC')
    timeframe: str                        # 타임프레임 ('1m', '5m', '1h' 등)
    count: int                            # 요청 캔들 개수 (1~200)

    # === API 파라미터 (정규화됨) ===
    to: Optional[str] = None              # 마지막 캔들 시각 (ISO format UTC)
    end: Optional[str] = None             # 종료 시점 (ISO format UTC)

    def __post_init__(self):
        """요청 정보 검증"""
        if self.count <= 0 or self.count > 200:
            raise ValueError(f"요청 개수는 1-200 사이여야 합니다: {self.count}")

        # to와 end는 둘 중 하나만 설정 가능
        if self.to is not None and self.end is not None:
            raise ValueError("to와 end는 동시에 설정할 수 없습니다")

    def to_api_params(self) -> Dict[str, Any]:
        """업비트 API 요청 파라미터로 변환"""
        params = {
            "market": self.symbol,
            "count": self.count
        }

        if self.to is not None:
            params["to"] = self.to
        elif self.end is not None:
            params["to"] = self.end

        return params

    def get_description(self) -> str:
        """요청 정보 설명 문자열"""
        base = f"{self.symbol} {self.timeframe} {self.count}개"
        if self.to:
            return f"{base} (to: {self.to})"
        elif self.end:
            return f"{base} (end: {self.end})"
        else:
            return f"{base} (최신)"
