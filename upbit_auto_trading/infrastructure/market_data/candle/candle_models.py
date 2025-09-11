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
from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal


# === Enum 모델 ===

class OverlapStatus(Enum):
    """겹침 상태 - OverlapAnalyzer v5.0과 정확히 일치하는 5개 분류"""
    NO_OVERLAP = "no_overlap"                        # 1. 겹침 없음
    COMPLETE_OVERLAP = "complete_overlap"            # 2.1. 완전 겹침
    PARTIAL_START = "partial_start"                  # 2.2.1. 시작 겹침
    PARTIAL_MIDDLE_FRAGMENT = "partial_middle_fragment"    # 2.2.2.1. 중간 겹침 (파편)
    PARTIAL_MIDDLE_CONTINUOUS = "partial_middle_continuous"  # 2.2.2.2. 중간 겹침 (말단)


# === 도메인 모델 ===

@dataclass
class CandleData:
    """캔들 데이터 도메인 모델 (업비트 API 완전 호환)"""
    # === 업비트 API 응답 필드 (1:1 매칭) ===
    market: str                           # 페어 코드 (KRW-BTC)
    candle_date_time_utc: str            # UTC 시간 문자열
    candle_date_time_kst: str            # KST 시간 문자열
    opening_price: float                 # 시가
    high_price: float                    # 고가
    low_price: float                     # 저가
    trade_price: float                   # 종가
    timestamp: int                       # 마지막 틱 타임스탬프 (ms)
    candle_acc_trade_price: float        # 누적 거래 금액
    candle_acc_trade_volume: float       # 누적 거래량

    # === 타임프레임별 고유 필드 (Optional) ===
    unit: Optional[int] = None                    # 초봉/분봉: 캔들 단위
    prev_closing_price: Optional[float] = None    # 일봉: 전일 종가
    change_price: Optional[float] = None          # 일봉: 가격 변화
    change_rate: Optional[float] = None           # 일봉: 변화율
    first_day_of_period: Optional[str] = None     # 주봉~연봉: 집계 시작일
    converted_trade_price: Optional[float] = None  # 일봉: 환산 종가 (선택적)

    # === 편의성 필드 (호환성) ===
    symbol: str = ""                     # market에서 추출
    timeframe: str = ""                  # 별도 지정

    def __post_init__(self):
        """데이터 검증 및 변환"""
        # ============================================
        # 🔍 VALIDATION ZONE - 성능 최적화시 제거 가능
        # ============================================
        # 기본 가격 검증
        prices = [self.opening_price, self.high_price, self.low_price, self.trade_price]
        if any(p <= 0 for p in prices):
            raise ValueError("모든 가격은 0보다 커야 합니다")
        if self.candle_acc_trade_volume < 0:
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
            opening_price=api_data["opening_price"],
            high_price=api_data["high_price"],
            low_price=api_data["low_price"],
            trade_price=api_data["trade_price"],
            timestamp=api_data["timestamp"],
            candle_acc_trade_price=api_data["candle_acc_trade_price"],
            candle_acc_trade_volume=api_data["candle_acc_trade_volume"],

            # 타임프레임별 선택적 필드
            unit=api_data.get("unit"),
            prev_closing_price=api_data.get("prev_closing_price"),
            change_price=api_data.get("change_price"),
            change_rate=api_data.get("change_rate"),
            first_day_of_period=api_data.get("first_day_of_period"),
            converted_trade_price=api_data.get("converted_trade_price"),

            # 편의성 필드
            symbol=api_data["market"],
            timeframe=timeframe
        )

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

RequestType = Literal["count_only", "count_with_to", "to_with_end", "end_only"]


@dataclass(frozen=True)
class RequestInfo:
    """
    CandleDataProvider v4.0 요청 정보 표준화 모델

    4가지 업비트 API 파라미터 조합 완벽 지원:
    1. count_only: count만 사용 (최신 데이터부터)
    2. count_with_to: count + to 조합
    3. to_with_end: to + end 조합
    4. end_only: end만 사용 (특정 시점까지 최대 200개)
    """
    # === 필수 파라미터 ===
    symbol: str                           # 거래 심볼 (예: 'KRW-BTC')
    timeframe: str                        # 타임프레임 ('1m', '5m', '1h' 등)
    request_type: RequestType             # 요청 타입 분류

    # === 선택적 파라미터 (상호 배타적 조합) ===
    count: Optional[int] = None           # 요청 캔들 개수 (1~200)
    to: Optional[datetime] = None         # 마지막 캔들 시간 (이 시간까지)
    end: Optional[datetime] = None        # 종료 시간 (이 시간부터 과거로)

    def __post_init__(self):
        """요청 정보 검증 - 업비트 API 규칙 준수"""
        # ============================================
        # 🔍 VALIDATION ZONE - 성능 최적화시 제거 가능
        # ============================================

        # 1. 기본 파라미터 검증
        if not self.symbol:
            raise ValueError("심볼은 필수입니다")
        if not self.timeframe:
            raise ValueError("타임프레임은 필수입니다")

        # 2. count 범위 검증 (업비트 API 제한)
        if self.count is not None and (self.count < 1 or self.count > 200):
            raise ValueError(f"count는 1~200 범위여야 합니다: {self.count}")

        # 3. 요청 타입별 파라미터 조합 검증
        if self.request_type == "count_only":
            if self.count is None:
                raise ValueError("count_only 타입에는 count가 필수입니다")
            if self.to is not None or self.end is not None:
                raise ValueError("count_only 타입에는 to, end를 사용할 수 없습니다")

        elif self.request_type == "count_with_to":
            if self.count is None or self.to is None:
                raise ValueError("count_with_to 타입에는 count와 to가 필수입니다")
            if self.end is not None:
                raise ValueError("count_with_to 타입에는 end를 사용할 수 없습니다")

        elif self.request_type == "to_with_end":
            if self.to is None or self.end is None:
                raise ValueError("to_with_end 타입에는 to와 end가 필수입니다")
            if self.count is not None:
                raise ValueError("to_with_end 타입에는 count를 사용할 수 없습니다")
            if self.to <= self.end:
                raise ValueError("to_with_end 타입에서 to는 end보다 나중이어야 합니다")

        elif self.request_type == "end_only":
            if self.end is None:
                raise ValueError("end_only 타입에는 end가 필수입니다")
            if self.count is not None or self.to is not None:
                raise ValueError("end_only 타입에는 count, to를 사용할 수 없습니다")
        else:
            raise ValueError(f"지원하지 않는 요청 타입: {self.request_type}")

        # ============================================
        # 🔍 END VALIDATION ZONE
        # ============================================

    @classmethod
    def create_count_only(cls, symbol: str, timeframe: str, count: int) -> 'RequestInfo':
        """count만 사용하는 요청 생성 (최신 데이터부터)"""
        return cls(
            symbol=symbol,
            timeframe=timeframe,
            request_type="count_only",
            count=count
        )

    @classmethod
    def create_count_with_to(cls, symbol: str, timeframe: str, count: int, to: datetime) -> 'RequestInfo':
        """count + to 조합 요청 생성"""
        return cls(
            symbol=symbol,
            timeframe=timeframe,
            request_type="count_with_to",
            count=count,
            to=to
        )

    @classmethod
    def create_to_with_end(cls, symbol: str, timeframe: str, to: datetime, end: datetime) -> 'RequestInfo':
        """to + end 조합 요청 생성"""
        return cls(
            symbol=symbol,
            timeframe=timeframe,
            request_type="to_with_end",
            to=to,
            end=end
        )

    @classmethod
    def create_end_only(cls, symbol: str, timeframe: str, end: datetime) -> 'RequestInfo':
        """end만 사용하는 요청 생성 (특정 시점까지 최대 200개)"""
        return cls(
            symbol=symbol,
            timeframe=timeframe,
            request_type="end_only",
            end=end
        )


@dataclass(frozen=True)
class ChunkPlan:
    """
    CandleDataProvider v4.0 청크 분할 계획

    요청 정규화 후 생성되는 전체 청크 처리 계획.
    200개 단위 청크로 분할하여 순차 처리.
    """
    # === 전체 계획 정보 ===
    original_request: RequestInfo         # 원본 요청 정보 (불변 보존)
    total_chunks: int                     # 총 청크 개수
    total_expected_candles: int           # 총 예상 캔들 개수

    # === 청크 리스트 ===
    chunks: List['ChunkInfo']             # 개별 청크 정보 리스트

    # === 처리 메타정보 ===
    plan_created_at: datetime             # 계획 생성 시간
    estimated_completion_time: float      # 예상 완료 시간 (초)

    def __post_init__(self):
        """청크 계획 검증"""
        # ============================================
        # 🔍 VALIDATION ZONE - 성능 최적화시 제거 가능
        # ============================================
        if self.total_chunks <= 0:
            raise ValueError(f"총 청크 개수는 1 이상이어야 합니다: {self.total_chunks}")
        if self.total_expected_candles <= 0:
            raise ValueError(f"총 예상 캔들 개수는 1 이상이어야 합니다: {self.total_expected_candles}")
        if len(self.chunks) != self.total_chunks:
            raise ValueError(f"청크 리스트 길이({len(self.chunks)})와 총 청크 개수({self.total_chunks})가 다릅니다")
        if self.estimated_completion_time < 0:
            raise ValueError(f"예상 완료 시간은 0 이상이어야 합니다: {self.estimated_completion_time}")
        # ============================================
        # 🔍 END VALIDATION ZONE
        # ============================================

    def get_chunk_by_index(self, index: int) -> 'ChunkInfo':
        """인덱스로 청크 조회"""
        if index < 0 or index >= len(self.chunks):
            raise IndexError(f"청크 인덱스 범위 초과: {index}")
        return self.chunks[index]

    def get_total_estimated_candles(self) -> int:
        """모든 청크의 예상 캔들 개수 합계"""
        return sum(chunk.expected_candles for chunk in self.chunks)


@dataclass(frozen=False)  # 실시간 조정을 위해 mutable
class ChunkInfo:
    """
    CandleDataProvider v4.0 개별 청크 정보

    실시간 시간 조정이 가능한 개별 청크 메타정보.
    이전 청크 결과에 따라 동적으로 시간 범위 조정.
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

    # === 처리 상태 정보 ===
    status: str = "pending"               # pending, processing, completed, failed
    expected_candles: int = 200           # 예상 캔들 개수 (기본 200개)

    # === 연결 정보 ===
    previous_chunk_id: Optional[str] = None   # 이전 청크 ID
    next_chunk_id: Optional[str] = None       # 다음 청크 ID

    def __post_init__(self):
        """청크 정보 검증"""
        # ============================================
        # 🔍 VALIDATION ZONE - 성능 최적화시 제거 가능
        # ============================================
        if not self.chunk_id:
            raise ValueError("청크 ID는 필수입니다")
        if self.chunk_index < 0:
            raise ValueError(f"청크 인덱스는 0 이상이어야 합니다: {self.chunk_index}")
        if self.count < 1 or self.count > 200:
            raise ValueError(f"청크 count는 1~200 범위여야 합니다: {self.count}")
        if self.expected_candles < 1:
            raise ValueError(f"예상 캔들 개수는 1 이상이어야 합니다: {self.expected_candles}")
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
            end=end,
            expected_candles=count
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
