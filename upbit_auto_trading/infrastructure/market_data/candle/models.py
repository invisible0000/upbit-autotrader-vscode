"""
📝 CandleDataProvider Infrastructure - Data Models
캔들 데이터 처리를 위한 Infrastructure Layer 데이터 모델 통합

Created: 2025-01-08
Purpose: Infrastructure Service 간 데이터 교환용 모델 정의
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


# === Enum 모델 ===

class OverlapStatus(Enum):
    """겹침 분석 상태"""
    NO_OVERLAP = "no_overlap"      # 겹침 없음 → 전체 API 요청 필요
    HAS_OVERLAP = "has_overlap"    # 겹침 있음 → 일부 DB, 일부 API


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

        # 편의성 필드 설정
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
        if self.success and not self.candles:
            raise ValueError("성공 응답인데 캔들 데이터가 없습니다")
        if not self.success and self.error_message is None:
            raise ValueError("실패 응답인데 에러 메시지가 없습니다")
        if self.total_count != len(self.candles):
            raise ValueError(f"총 개수({self.total_count})와 실제 캔들 개수({len(self.candles)})가 다릅니다")


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
        if self.count <= 0 or self.count > 200:
            raise ValueError(f"청크 크기는 1-200 사이여야 합니다: {self.count}")
        if self.chunk_index < 0:
            raise ValueError(f"청크 인덱스는 0 이상이어야 합니다: {self.chunk_index}")


# === 분석 결과 모델 ===

@dataclass
class OverlapResult:
    """겹침 분석 결과 (API 요청 최적화용)"""
    status: OverlapStatus
    connected_end: Optional[datetime]  # 연속된 데이터의 끝점 (이 시점까지는 DB 조회 가능)

    def __post_init__(self):
        """분석 결과 검증"""
        if self.status == OverlapStatus.HAS_OVERLAP and self.connected_end is None:
            raise ValueError("겹침이 있는데 연속 데이터 끝점이 없습니다")


@dataclass
class DataRange:
    """기존 DB 데이터 범위"""
    start_time: datetime
    end_time: datetime
    candle_count: int
    is_continuous: bool           # 연속된 데이터인지 여부

    def __post_init__(self):
        """데이터 범위 검증"""
        if self.start_time >= self.end_time:
            raise ValueError("시작 시간이 종료 시간보다 늦습니다")
        if self.candle_count <= 0:
            raise ValueError(f"캔들 개수는 1 이상이어야 합니다: {self.candle_count}")


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
