"""
수집 상태 관리 모델
Smart Data Provider V3.0의 스마트 캔들 콜렉터 기능을 위한 데이터 모델
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List
from decimal import Decimal


class CollectionStatus(Enum):
    """캔들 수집 상태"""
    COLLECTED = "COLLECTED"  # 정상 수집 완료
    EMPTY = "EMPTY"          # 거래가 없어서 빈 캔들
    PENDING = "PENDING"      # 아직 수집하지 않음
    FAILED = "FAILED"        # 수집 실패


@dataclass(frozen=True)
class CollectionStatusRecord:
    """수집 상태 레코드"""
    id: Optional[int]
    symbol: str
    timeframe: str
    target_time: datetime
    collection_status: CollectionStatus
    last_attempt_at: Optional[datetime] = None
    attempt_count: int = 0
    api_response_code: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create_pending(cls, symbol: str, timeframe: str, target_time: datetime) -> 'CollectionStatusRecord':
        """새로운 PENDING 상태 레코드 생성"""
        return cls(
            id=None,
            symbol=symbol,
            timeframe=timeframe,
            target_time=target_time,
            collection_status=CollectionStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def mark_collected(self, api_response_code: int = 200) -> 'CollectionStatusRecord':
        """수집 완료로 상태 변경"""
        return CollectionStatusRecord(
            id=self.id,
            symbol=self.symbol,
            timeframe=self.timeframe,
            target_time=self.target_time,
            collection_status=CollectionStatus.COLLECTED,
            last_attempt_at=datetime.now(),
            attempt_count=self.attempt_count + 1,
            api_response_code=api_response_code,
            created_at=self.created_at,
            updated_at=datetime.now()
        )

    def mark_empty(self, api_response_code: int = 200) -> 'CollectionStatusRecord':
        """빈 캔들로 상태 변경"""
        return CollectionStatusRecord(
            id=self.id,
            symbol=self.symbol,
            timeframe=self.timeframe,
            target_time=self.target_time,
            collection_status=CollectionStatus.EMPTY,
            last_attempt_at=datetime.now(),
            attempt_count=self.attempt_count + 1,
            api_response_code=api_response_code,
            created_at=self.created_at,
            updated_at=datetime.now()
        )

    def mark_failed(self, api_response_code: Optional[int] = None) -> 'CollectionStatusRecord':
        """수집 실패로 상태 변경"""
        return CollectionStatusRecord(
            id=self.id,
            symbol=self.symbol,
            timeframe=self.timeframe,
            target_time=self.target_time,
            collection_status=CollectionStatus.FAILED,
            last_attempt_at=datetime.now(),
            attempt_count=self.attempt_count + 1,
            api_response_code=api_response_code,
            created_at=self.created_at,
            updated_at=datetime.now()
        )


@dataclass(frozen=True)
class CandleWithStatus:
    """캔들 데이터와 수집 상태를 함께 담는 모델"""
    # 캔들 기본 정보
    market: str
    candle_date_time_utc: datetime
    candle_date_time_kst: datetime
    opening_price: Decimal
    high_price: Decimal
    low_price: Decimal
    trade_price: Decimal
    timestamp: int
    candle_acc_trade_price: Decimal
    candle_acc_trade_volume: Decimal
    unit: int

    # 수집 상태 정보
    is_empty: bool = False
    collection_status: CollectionStatus = CollectionStatus.COLLECTED

    @classmethod
    def create_empty(cls, market: str, target_time: datetime, last_price: Decimal) -> 'CandleWithStatus':
        """빈 캔들 생성 (마지막 가격으로 채움)"""
        return cls(
            market=market,
            candle_date_time_utc=target_time,
            candle_date_time_kst=target_time,  # 간단화, 실제로는 KST 변환 필요
            opening_price=last_price,
            high_price=last_price,
            low_price=last_price,
            trade_price=last_price,
            timestamp=int(target_time.timestamp() * 1000),
            candle_acc_trade_price=Decimal("0"),
            candle_acc_trade_volume=Decimal("0"),
            unit=1,
            is_empty=True,
            collection_status=CollectionStatus.EMPTY
        )


@dataclass(frozen=True)
class TimeRange:
    """시간 범위"""
    start_time: datetime
    end_time: datetime

    def generate_expected_times(self, timeframe: str) -> List[datetime]:
        """예상 캔들 시간 목록 생성"""
        from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.processing.time_utils import (
            generate_candle_times
        )
        return generate_candle_times(self.start_time, self.end_time, timeframe)


@dataclass(frozen=True)
class CollectionSummary:
    """수집 요약 정보"""
    symbol: str
    timeframe: str
    time_range: TimeRange
    total_expected: int
    collected_count: int
    empty_count: int
    pending_count: int
    failed_count: int

    @property
    def completion_rate(self) -> float:
        """수집 완료율 (%)"""
        if self.total_expected == 0:
            return 100.0
        return (self.collected_count + self.empty_count) / self.total_expected * 100

    @property
    def success_rate(self) -> float:
        """수집 성공률 (%) - 실패 제외"""
        if self.total_expected == 0:
            return 100.0
        total_attempted = self.total_expected - self.failed_count
        if total_attempted <= 0:
            return 0.0
        return (self.collected_count + self.empty_count) / total_attempted * 100
