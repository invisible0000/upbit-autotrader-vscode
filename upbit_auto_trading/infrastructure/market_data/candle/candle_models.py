"""
📝 CandleDataProvider Infrastructure - Data Models
캔들 데이터 처리를 위한 Infrastructure Layer 데이터 모델 통합

Created: 2025-01-08
Purpose: Infrastructure Service 간 데이터 교환용 모델 정의

🔍 VALIDATION POLICY:
- 현재: 업비트 데이터 무결성 검증 활성화
- 향후: 업비트 데이터 안정성 확인 시 "🔍 VALIDATION ZONE" 블록 제거로 성능 최적화
- 검증 제거 시 예상 성능 향상: 캔들 1000개 처리 시간 30-50% 단축
- 검증 블록 위치: 각 @dataclass의 __post_init__ 메서드 내 표시됨
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any


# === Enum 모델 ===

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


# === 도메인 모델 ===

@dataclass
class CandleData:
    """캔들 데이터 도메인 모델 (업비트 API 완전 호환)"""
    # === 업비트 API 응답 필드 (1:1 매칭) ===
    market: str                                    # 페어 코드 (KRW-BTC)
    candle_date_time_utc: str                     # UTC 시간 문자열
    candle_date_time_kst: str                     # KST 시간 문자열
    opening_price: Optional[float]                # 시가 (빈 캔들에서는 None)
    high_price: Optional[float]                   # 고가 (빈 캔들에서는 None)
    low_price: Optional[float]                    # 저가 (빈 캔들에서는 None)
    trade_price: Optional[float]                  # 종가 (빈 캔들에서는 None)
    timestamp: int                                # 마지막 틱 타임스탬프 (ms)
    candle_acc_trade_price: Optional[float]       # 누적 거래 금액 (빈 캔들에서는 None)
    candle_acc_trade_volume: Optional[float]      # 누적 거래량 (빈 캔들에서는 None)

    # === 타임프레임별 고유 필드 (Optional) ===
    unit: Optional[int] = None                    # 초봉/분봉: 캔들 단위
    prev_closing_price: Optional[float] = None    # 일봉: 전일 종가
    change_price: Optional[float] = None          # 일봉: 가격 변화
    change_rate: Optional[float] = None           # 일봉: 변화율
    first_day_of_period: Optional[str] = None     # 주봉~연봉: 집계 시작일
    converted_trade_price: Optional[float] = None  # 일봉: 환산 종가 (선택적)

    # === 빈 캔들 처리 필드 ===
    blank_copy_from_utc: Optional[str] = None  # 빈 캔들 식별용 (참조 캔들의 UTC 시간)

    # === 편의성 필드 (호환성) ===
    symbol: str = ""                     # market에서 추출
    timeframe: str = ""                  # 별도 지정

    def __post_init__(self):
        """데이터 검증 및 변환"""
        # ============================================
        # 🔍 VALIDATION ZONE - 성능 최적화시 제거 가능
        # ============================================
        # 빈 캔들 허용: blank_copy_from_utc가 있으면 가격/거래량 검증 건너뛰기
        if self.blank_copy_from_utc is not None:
            # 빈 캔들: 검증 생략 (NULL 값 허용)
            pass
        else:
            # 일반 캔들: 기본 가격 검증
            prices = [self.opening_price, self.high_price, self.low_price, self.trade_price]
            if any(p is None or p <= 0 for p in prices):
                raise ValueError("모든 가격은 0보다 커야 합니다")
            if self.candle_acc_trade_volume is not None and self.candle_acc_trade_volume < 0:
                raise ValueError("거래량은 0 이상이어야 합니다")
            if self.high_price < max(self.opening_price, self.trade_price, self.low_price):
                raise ValueError("고가는 시가/종가/저가보다 높아야 합니다")
            if self.low_price > min(self.opening_price, self.trade_price, self.high_price):
                raise ValueError("저가는 시가/종가/고가보다 낮아야 합니다")
        # ============================================
        # 🔍 END VALIDATION ZONE
        # ============================================

        # 편의성 필드 설정 (유지 필요)
        if not self.symbol and self.market:
            self.symbol = self.market

    @classmethod
    def from_upbit_api(cls, api_data: dict, timeframe: str) -> 'CandleData':
        """업비트 API 응답에서 CandleData 생성"""
        return cls(
            # 공통 필드
            market=api_data["market"],
            candle_date_time_utc=api_data["candle_date_time_utc"],
            candle_date_time_kst=api_data["candle_date_time_kst"],
            opening_price=api_data.get("opening_price"),      # 빈 캔들 고려 None 허용
            high_price=api_data.get("high_price"),           # 빈 캔들 고려 None 허용
            low_price=api_data.get("low_price"),             # 빈 캔들 고려 None 허용
            trade_price=api_data.get("trade_price"),         # 빈 캔들 고려 None 허용
            timestamp=api_data["timestamp"],
            candle_acc_trade_price=api_data.get("candle_acc_trade_price"),   # 빈 캔들 고려 None 허용
            candle_acc_trade_volume=api_data.get("candle_acc_trade_volume"),  # 빈 캔들 고려 None 허용

            # 타임프레임별 선택적 필드
            unit=api_data.get("unit"),
            prev_closing_price=api_data.get("prev_closing_price"),
            change_price=api_data.get("change_price"),
            change_rate=api_data.get("change_rate"),
            first_day_of_period=api_data.get("first_day_of_period"),
            converted_trade_price=api_data.get("converted_trade_price"),

            # 빈 캔들 처리 필드
            blank_copy_from_utc=api_data.get("blank_copy_from_utc"),

            # 편의성 필드
            symbol=api_data["market"],
            timeframe=timeframe
        )

    @classmethod
    def create_empty_candle(
        cls,
        target_time: datetime,
        reference_utc: str,
        timeframe: str,
        market: str,
        timestamp_ms: int
    ) -> 'CandleData':
        """
        빈 캔들 생성 (EmptyCandleDetector 전용)

        빈 캔들 특징:
        - 가격: 참조 캔들의 종가로 고정 (시가=고가=저가=종가=0.0, 실제값은 Dict에서 설정)
        - 거래량/거래대금: 0
        - timestamp: 정확한 밀리초 단위 (SqliteCandleRepository 호환)

        Args:
            target_time: 빈 캔들의 시간
            reference_utc: 참조 캔들의 UTC 시간 (추적용)
            timeframe: 타임프레임
            market: 마켓 코드 (예: 'KRW-BTC')
            timestamp_ms: 정확한 Unix timestamp (밀리초)

        Returns:
            CandleData: 빈 캔들 객체
        """
        return cls(
            # === 업비트 API 공통 필드 ===
            market=market,
            candle_date_time_utc=target_time.strftime('%Y-%m-%dT%H:%M:%S'),  # UTC 형식 (timezone 정보 없음)
            candle_date_time_kst=cls._utc_to_kst_string(target_time),
            opening_price=0.0,      # 빈 캔들: 기본값 (실제값은 Dict에서 설정)
            high_price=0.0,
            low_price=0.0,
            trade_price=0.0,
            timestamp=timestamp_ms,  # 🚀 정확한 timestamp (SqliteCandleRepository 호환)
            candle_acc_trade_price=0.0,   # 빈 캔들: 거래 없음
            candle_acc_trade_volume=0.0,

            # === 편의성 필드 ===
            symbol=market,
            timeframe=timeframe
        )

    @staticmethod
    def _utc_to_kst_string(utc_time: datetime) -> str:
        """UTC datetime을 KST 시간 문자열로 변환 (빈 캔들 생성용)"""
        from datetime import timedelta

        # KST = UTC + 9시간
        kst_time = utc_time + timedelta(hours=9)
        return kst_time.strftime('%Y-%m-%dT%H:%M:%S')

    def to_db_dict(self) -> dict:
        """DB 저장용 딕셔너리 변환 (공통 필드만, Repository 스키마와 통일)"""
        return {
            # 업비트 API 공통 필드 (Repository 스키마와 1:1 매칭)
            "market": self.market,
            "candle_date_time_utc": self.candle_date_time_utc,
            "candle_date_time_kst": self.candle_date_time_kst,
            "opening_price": self.opening_price,
            "high_price": self.high_price,
            "low_price": self.low_price,
            "trade_price": self.trade_price,
            "timestamp": self.timestamp,
            "candle_acc_trade_price": self.candle_acc_trade_price,
            "candle_acc_trade_volume": self.candle_acc_trade_volume,
            "blank_copy_from_utc": self.blank_copy_from_utc,
        }


# === 요청/응답 모델 ===

@dataclass
class CandleDataResponse:
    """서브시스템 최종 응답 모델"""
    success: bool
    candles: List[CandleData]
    total_count: int
    data_source: str              # "cache", "db", "api", "mixed"
    response_time_ms: float
    error_message: Optional[str] = None

    def __post_init__(self):
        """응답 데이터 검증"""
        # ============================================
        # 🔍 VALIDATION ZONE - 성능 최적화시 제거 가능
        # ============================================
        if self.success and not self.candles:
            raise ValueError("성공 응답인데 캔들 데이터가 없습니다")
        if not self.success and self.error_message is None:
            raise ValueError("실패 응답인데 에러 메시지가 없습니다")
        if self.total_count != len(self.candles):
            raise ValueError(f"총 개수({self.total_count})와 실제 캔들 개수({len(self.candles)})가 다릅니다")
        # ============================================
        # 🔍 END VALIDATION ZONE
        # ============================================


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


# === 분석 결과 모델 ===

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

    # 하위 호환성 유지
    connected_end: Optional[datetime] = None  # deprecated: partial_end 사용 권장

    def __post_init__(self):
        """분석 결과 검증 - v5.0 로직"""
        # 하위 호환성: connected_end가 있으면 partial_end에 복사 (유지 필요)
        if self.connected_end is not None and self.partial_end is None:
            object.__setattr__(self, 'partial_end', self.connected_end)

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


# === 시간 관련 모델 ===

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


# === 수집 결과 모델 ===

@dataclass
class CollectionResult:
    """단일 청크 수집 결과"""
    chunk: CandleChunk
    collected_candles: List[CandleData]
    data_source: str              # "db", "api", "mixed"
    api_requests_made: int        # 실제 API 요청 횟수
    collection_time_ms: float    # 수집 소요 시간

    def __post_init__(self):
        """수집 결과 검증"""
        if self.api_requests_made < 0:
            raise ValueError(f"API 요청 횟수는 0 이상이어야 합니다: {self.api_requests_made}")
        if self.collection_time_ms < 0:
            raise ValueError(f"수집 시간은 0 이상이어야 합니다: {self.collection_time_ms}")


# === 캐시 관련 모델 ===

@dataclass
class CacheKey:
    """캐시 키 구조화"""
    symbol: str
    timeframe: str
    start_time: datetime
    count: int

    def __post_init__(self):
        """캐시 키 검증"""
        if not self.symbol:
            raise ValueError("심볼은 필수입니다")
        if not self.timeframe:
            raise ValueError("타임프레임은 필수입니다")
        if self.count <= 0:
            raise ValueError(f"개수는 1 이상이어야 합니다: {self.count}")

    def to_string(self) -> str:
        """캐시 키를 문자열로 변환"""
        return f"candles_{self.symbol}_{self.timeframe}_{self.start_time.isoformat()}_{self.count}"


@dataclass
class CacheEntry:
    """캐시 엔트리 (데이터 + 메타데이터)"""
    key: CacheKey
    candles: List[CandleData]
    created_at: datetime
    ttl_seconds: int
    data_size_bytes: int

    def __post_init__(self):
        """캐시 엔트리 검증"""
        if self.ttl_seconds <= 0:
            raise ValueError(f"TTL은 1 이상이어야 합니다: {self.ttl_seconds}")
        if self.data_size_bytes < 0:
            raise ValueError(f"데이터 크기는 0 이상이어야 합니다: {self.data_size_bytes}")
        if len(self.candles) != self.key.count:
            raise ValueError(f"캔들 개수({len(self.candles)})와 키 개수({self.key.count})가 다릅니다")

    def is_expired(self, current_time: datetime) -> bool:
        """캐시 만료 여부 확인"""
        elapsed_seconds = (current_time - self.created_at).total_seconds()
        return elapsed_seconds > self.ttl_seconds

    def get_remaining_ttl(self, current_time: datetime) -> int:
        """남은 TTL 초 반환"""
        elapsed_seconds = (current_time - self.created_at).total_seconds()
        remaining = self.ttl_seconds - elapsed_seconds
        return max(0, int(remaining))


@dataclass
class CacheStats:
    """캐시 통계 정보"""
    total_entries: int
    total_memory_bytes: int
    hit_count: int
    miss_count: int
    eviction_count: int
    expired_count: int

    def __post_init__(self):
        """통계 검증"""
        if any(count < 0 for count in [self.total_entries, self.total_memory_bytes,
                                       self.hit_count, self.miss_count,
                                       self.eviction_count, self.expired_count]):
            raise ValueError("모든 통계 값은 0 이상이어야 합니다")

    def get_hit_rate(self) -> float:
        """캐시 히트율 계산"""
        total_requests = self.hit_count + self.miss_count
        if total_requests == 0:
            return 0.0
        return self.hit_count / total_requests

    def get_memory_mb(self) -> float:
        """메모리 사용량 MB 반환"""
        return self.total_memory_bytes / (1024 * 1024)


# === CandleDataProvider v4.0 전용 모델 ===

@dataclass
class CollectionState:
    """캔들 수집 상태 관리 - CandleDataProvider v4.0"""
    request_id: str
    symbol: str
    timeframe: str
    total_requested: int
    total_collected: int = 0
    completed_chunks: List['ChunkInfo'] = None
    current_chunk: Optional['ChunkInfo'] = None
    last_candle_time: Optional[str] = None  # 마지막 수집된 캔들 시간 (연속성용)
    estimated_total_chunks: int = 0
    estimated_completion_time: Optional[datetime] = None
    start_time: datetime = None
    is_completed: bool = False
    error_message: Optional[str] = None

    # 남은 시간 추적 필드들
    last_update_time: datetime = None
    avg_chunk_duration: float = 0.0  # 평균 청크 처리 시간 (초)
    remaining_chunks: int = 0  # 남은 청크 수
    estimated_remaining_seconds: float = 0.0  # 실시간 계산된 남은 시간

    def __post_init__(self):
        """기본값 설정"""
        from datetime import datetime, timezone

        if self.completed_chunks is None:
            self.completed_chunks = []
        if self.start_time is None:
            self.start_time = datetime.now(timezone.utc)
        if self.last_update_time is None:
            self.last_update_time = datetime.now(timezone.utc)


@dataclass
class CollectionPlan:
    """수집 계획 (최소 정보만) - CandleDataProvider v4.0"""
    total_count: int
    estimated_chunks: int
    estimated_duration_seconds: float
    first_chunk_params: Dict[str, Any]  # 첫 번째 청크 요청 파라미터

    def __post_init__(self):
        """계획 정보 검증"""
        if self.total_count <= 0:
            raise ValueError(f"총 개수는 1 이상이어야 합니다: {self.total_count}")
        if self.estimated_chunks <= 0:
            raise ValueError(f"예상 청크 수는 1 이상이어야 합니다: {self.estimated_chunks}")
        if self.estimated_duration_seconds < 0:
            raise ValueError(f"예상 소요시간은 0 이상이어야 합니다: {self.estimated_duration_seconds}")


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

    # === 선택적 파라미터 ===
    count: Optional[int] = None           # 요청 캔들 개수 (정규화 과정에서 계산됨)
    to: Optional[datetime] = None         # 시작점 - 최신 캔들 시간
    end: Optional[datetime] = None        # 종료점 - 가장 과거 캔들 시간

    def __post_init__(self):
        """간략화된 요청 정보 검증"""
        # ============================================
        # 🔍 VALIDATION ZONE - 성능 최적화시 제거 가능
        # ============================================

        # 1. 기본 파라미터 검증
        if not self.symbol:
            raise ValueError("심볼은 필수입니다")
        if not self.timeframe:
            raise ValueError("타임프레임은 필수입니다")

        # 2. count 범위 검증 (최소값만 체크)
        if self.count is not None and self.count < 1:
            raise ValueError(f"count는 1 이상이어야 합니다: {self.count}")

        # 3. 시간 순서 검증 (to > end 이어야 함)
        if self.to is not None and self.end is not None and self.to <= self.end:
            raise ValueError("to는 end보다 이전 시점이어야 합니다")

        # 4. count와 end 동시 사용 방지
        if self.count is not None and self.end is not None:
            raise ValueError("count와 end는 동시에 사용할 수 없습니다. count 또는 to+end 조합만 사용 가능합니다")

        # 5. 최소 파라미터 조합 확인
        # 허용되는 조합: count만, count+to, to+end, end만
        has_count = self.count is not None
        has_to = self.to is not None
        has_end = self.end is not None

        valid_combinations = [
            has_count and not has_end,  # count만 또는 count+to
            has_to and has_end and not has_count,  # to+end
            has_end and not has_count and not has_to  # end만
        ]

        if not any(valid_combinations):
            raise ValueError("count 또는 to+end 또는 end만 사용 가능합니다")

        # ============================================
        # 🔍 END VALIDATION ZONE
        # ============================================


@dataclass(frozen=False)  # 실시간 조정을 위해 mutable
class ChunkInfo:
    """
    CandleDataProvider v6.1 개별 청크 정보 - Overlap 최적화 지원

    실시간 시간 조정이 가능한 개별 청크 메타정보.
    이전 청크 결과에 따라 동적으로 시간 범위 조정.
    temp_chunk 생성 제거로 성능 최적화.
    """
    # === 청크 식별 정보 ===
    chunk_id: str                         # 청크 고유 식별자
    chunk_index: int                      # 청크 순서 (0부터 시작)
    symbol: str                           # 거래 심볼
    timeframe: str                        # 타임프레임

    # === 청크 파라미터 (실시간 조정 가능) ===
    count: int                            # 이 청크에서 요청할 캔들 개수
    to: Optional[datetime] = None         # 이 청크의 마지막 캔들 시간
    end: Optional[datetime] = None        # 이 청크의 종료 시간

    # === 🆕 Overlap 최적화 필드들 ===
    overlap_status: Optional['OverlapStatus'] = None    # 겹침 분석 결과
    api_count: Optional[int] = None                     # 실제 API 호출 개수 (부분 겹침 시)
    api_start: Optional[datetime] = None                # API 호출 시작점 (부분 겹침 시)
    api_end: Optional[datetime] = None                  # API 호출 종료점 (부분 겹침 시)

    # === 처리 상태 정보 ===
    status: str = "pending"               # pending, processing, completed, failed
    created_at: Optional[datetime] = None  # 청크 생성 시간

    # === 연결 정보 ===
    previous_chunk_id: Optional[str] = None   # 이전 청크 ID
    next_chunk_id: Optional[str] = None       # 다음 청크 ID

    def __post_init__(self):
        """청크 정보 검증 및 기본값 설정"""
        # created_at 기본값 설정
        if self.created_at is None:
            object.__setattr__(self, 'created_at', datetime.now(timezone.utc))

        # ============================================
        # 🔍 VALIDATION ZONE - 성능 최적화시 제거 가능
        # ============================================
        if not self.chunk_id:
            raise ValueError("청크 ID는 필수입니다")
        if self.chunk_index < 0:
            raise ValueError(f"청크 인덱스는 0 이상이어야 합니다: {self.chunk_index}")
        if self.count < 1 or self.count > 200:
            raise ValueError(f"청크 count는 1~200 범위여야 합니다: {self.count}")
        if self.status not in ["pending", "processing", "completed", "failed"]:
            raise ValueError(f"잘못된 상태값: {self.status}")
        # ============================================
        # 🔍 END VALIDATION ZONE
        # ============================================

    def adjust_times(self, new_to: Optional[datetime] = None, new_end: Optional[datetime] = None) -> None:
        """실시간 시간 조정 (이전 청크 결과 반영)"""
        if new_to is not None:
            self.to = new_to
        if new_end is not None:
            self.end = new_end

    def mark_processing(self) -> None:
        """처리 중 상태로 변경"""
        self.status = "processing"

    def mark_completed(self) -> None:
        """완료 상태로 변경"""
        self.status = "completed"

    def mark_failed(self) -> None:
        """실패 상태로 변경"""
        self.status = "failed"

    def is_pending(self) -> bool:
        """대기 중 상태 확인"""
        return self.status == "pending"

    def is_completed(self) -> bool:
        """완료 상태 확인"""
        return self.status == "completed"

    # === 🆕 Overlap 최적화 메서드들 ===

    def set_overlap_info(self, overlap_result: 'OverlapResult', api_count: Optional[int] = None) -> None:
        """겹침 분석 결과를 ChunkInfo에 설정 (temp_chunk 생성 제거)"""
        self.overlap_status = overlap_result.status
        self.api_start = overlap_result.api_start
        self.api_end = overlap_result.api_end

        # API 개수 설정 (부분 겹침 시)
        if api_count is not None:
            self.api_count = api_count
        elif overlap_result.api_start and overlap_result.api_end:
            # API 개수 자동 계산
            from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils
            self.api_count = TimeUtils.calculate_expected_count(
                overlap_result.api_start, overlap_result.api_end, self.timeframe
            )

    def has_overlap_info(self) -> bool:
        """겹침 분석 정보 보유 여부 확인"""
        return self.overlap_status is not None

    def needs_api_call(self) -> bool:
        """API 호출 필요 여부 확인"""
        if not self.has_overlap_info():
            return True  # 겹침 분석 없으면 API 호출 필요

        from upbit_auto_trading.infrastructure.market_data.candle.candle_models import OverlapStatus
        return self.overlap_status != OverlapStatus.COMPLETE_OVERLAP

    def needs_partial_api_call(self) -> bool:
        """부분 API 호출 필요 여부 확인"""
        if not self.has_overlap_info():
            return False

        from upbit_auto_trading.infrastructure.market_data.candle.candle_models import OverlapStatus
        return self.overlap_status in [OverlapStatus.PARTIAL_START, OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS]

    def get_api_params(self) -> tuple[int, Optional[datetime]]:
        """API 호출 파라미터 반환 (count, to)"""
        if self.needs_partial_api_call() and self.api_count and self.api_start:
            # 부분 겹침: overlap 정보 사용
            return self.api_count, self.api_start
        else:
            # 전체 호출: 기본 정보 사용
            return self.count, self.to

    @classmethod
    def create_chunk(cls, chunk_index: int, symbol: str, timeframe: str, count: int,
                     to: Optional[datetime] = None, end: Optional[datetime] = None) -> 'ChunkInfo':
        """새 청크 생성 헬퍼"""
        chunk_id = f"{symbol}_{timeframe}_{chunk_index:03d}"
        return cls(
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            to=to,
            end=end
        )


@dataclass
class ProcessingStats:
    """
    CandleDataProvider v4.0 처리 통계

    전체 처리 과정의 성능 및 상태 정보.
    """
    # === 기본 정보 ===
    total_chunks_planned: int             # 계획된 총 청크 수
    processing_start_time: datetime       # 처리 시작 시간
    chunks_completed: int = 0             # 완료된 청크 수
    chunks_failed: int = 0                # 실패한 청크 수

    # === 시간 정보 ===
    processing_end_time: Optional[datetime] = None  # 처리 완료 시간

    # === API 통계 ===
    total_api_requests: int = 0           # 총 API 요청 수
    api_request_time_ms: float = 0.0      # 총 API 요청 시간

    # === 캐시 통계 ===
    cache_hits: int = 0                   # 캐시 히트 수
    cache_misses: int = 0                 # 캐시 미스 수

    # === 데이터 통계 ===
    total_candles_collected: int = 0      # 수집된 총 캔들 수

    def __post_init__(self):
        """통계 검증"""
        if self.total_chunks_planned <= 0:
            raise ValueError(f"계획된 총 청크 수는 1 이상이어야 합니다: {self.total_chunks_planned}")
        if any(count < 0 for count in [self.chunks_completed, self.chunks_failed,
                                       self.total_api_requests, self.cache_hits,
                                       self.cache_misses, self.total_candles_collected]):
            raise ValueError("모든 통계 값은 0 이상이어야 합니다")

    def get_completion_rate(self) -> float:
        """완료율 계산 (0.0 ~ 1.0)"""
        if self.total_chunks_planned == 0:
            return 0.0
        return self.chunks_completed / self.total_chunks_planned

    def get_cache_hit_rate(self) -> float:
        """캐시 히트율 계산 (0.0 ~ 1.0)"""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return self.cache_hits / total_cache_requests

    def get_average_api_time_ms(self) -> float:
        """평균 API 요청 시간 (ms)"""
        if self.total_api_requests == 0:
            return 0.0
        return self.api_request_time_ms / self.total_api_requests

    def get_total_processing_time_ms(self) -> float:
        """총 처리 시간 (ms)"""
        if self.processing_end_time is None:
            end_time = datetime.now()
        else:
            end_time = self.processing_end_time

        delta = end_time - self.processing_start_time
        return delta.total_seconds() * 1000

    def mark_completed(self) -> None:
        """처리 완료 마킹"""
        self.processing_end_time = datetime.now()


# === 유틸리티 함수 ===

def create_success_response(
    candles: List[CandleData],
    data_source: str,
    response_time_ms: float
) -> CandleDataResponse:
    """성공 응답 생성 헬퍼"""
    return CandleDataResponse(
        success=True,
        candles=candles,
        total_count=len(candles),
        data_source=data_source,
        response_time_ms=response_time_ms
    )


def create_error_response(
    error_message: str,
    response_time_ms: float
) -> CandleDataResponse:
    """에러 응답 생성 헬퍼"""
    return CandleDataResponse(
        success=False,
        candles=[],
        total_count=0,
        data_source="error",
        response_time_ms=response_time_ms,
        error_message=error_message
    )
