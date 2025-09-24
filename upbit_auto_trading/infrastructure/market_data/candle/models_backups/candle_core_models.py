"""
📝 Candle Core Models
캔들 데이터 핵심 모델 - 가장 자주 사용되는 기본 도메인 모델들

Created: 2025-09-22
Purpose: 핵심 캔들 데이터 구조와 기본 Enum 정의
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


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


# === 핵심 도메인 모델 ===

@dataclass
class CandleData:
    """캔들 데이터 도메인 모델 (업비트 API 완전 호환)"""
    # === 업비트 API 응답 필드 (1:1 매칭) ===
    market: str                                    # 페어 코드 (KRW-BTC)
    candle_date_time_utc: str                     # UTC 시간 문자열
    candle_date_time_kst: Optional[str]           # KST 시간 문자열 (빈 캔들에서는 None)
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
    empty_copy_from_utc: Optional[str] = None  # 빈 캔들 식별용 (참조 상태 문자열)

    # === 편의성 필드 (호환성) ===
    symbol: str = ""                     # market에서 추출
    timeframe: str = ""                  # 별도 지정

    def __post_init__(self):
        """데이터 검증 및 변환"""
        # ============================================
        # 🔍 VALIDATION ZONE - 성능 최적화시 제거 가능
        # ============================================
        # 빈 캔들 허용: empty_copy_from_utc가 있으면 가격/거래량 검증 건너뛰기
        if self.empty_copy_from_utc is not None:
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
            empty_copy_from_utc=api_data.get("empty_copy_from_utc"),

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
            # candle_date_time_kst=cls._utc_to_kst_string(target_time),
            candle_date_time_kst=None,  # 빈 캔들에서는 None (용량 절약)
            opening_price=None,         # 빈 캔들: None으로 변경 (시간과 관련없는 데이터)
            high_price=None,           # 빈 캔들: None으로 변경
            low_price=None,            # 빈 캔들: None으로 변경
            trade_price=None,          # 빈 캔들: None으로 변경
            timestamp=timestamp_ms,    # 🚀 정확한 timestamp (SqliteCandleRepository 호환)
            candle_acc_trade_price=None,   # 빈 캔들: None으로 변경 (거래 없음)
            candle_acc_trade_volume=None,  # 빈 캔들: None으로 변경 (거래 없음)

            # === 빈 캔들 처리 필드 ===
            empty_copy_from_utc=reference_utc,  # 빈 캔들 식별용 (검증 우회)

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
            "empty_copy_from_utc": self.empty_copy_from_utc,
        }


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
