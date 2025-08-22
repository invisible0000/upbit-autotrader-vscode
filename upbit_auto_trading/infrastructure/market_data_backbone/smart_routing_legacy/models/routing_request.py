"""
라우팅 요청 모델

시장 데이터 요청을 위한 표준화된 요청 모델입니다.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DataType(Enum):
    """데이터 타입"""
    CANDLE = "candle"
    TICKER = "ticker"
    ORDERBOOK = "orderbook"
    TRADE = "trade"


class TimeFrame(Enum):
    """시간 프레임"""
    MINUTES_1 = "1m"
    MINUTES_3 = "3m"
    MINUTES_5 = "5m"
    MINUTES_15 = "15m"
    MINUTES_30 = "30m"
    HOURS_1 = "1h"
    HOURS_4 = "4h"
    DAYS_1 = "1d"
    WEEKS_1 = "1w"
    MONTHS_1 = "1M"


@dataclass(frozen=True)
class RoutingRequest:
    """라우팅 요청

    시장 데이터 요청을 위한 표준화된 모델입니다.
    """
    symbols: List[str]
    data_type: DataType
    timeframe: Optional[TimeFrame] = None
    request_id: str = ""
    requested_at: Optional[datetime] = None

    # 캔들 데이터 관련
    count: Optional[int] = None  # 요청할 데이터 개수
    to_date: Optional[str] = None  # 마지막 캔들 시각 (ISO 8601 UTC)

    # 실시간 요청 관련
    is_realtime: bool = False
    update_interval_ms: Optional[int] = None

    # 메타데이터
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """후처리"""
        if self.requested_at is None:
            object.__setattr__(self, 'requested_at', datetime.now())

        if not self.request_id:
            # 요청 ID 자동 생성 (timestamp + symbols hash)
            if self.requested_at is not None:
                timestamp = int(self.requested_at.timestamp() * 1000)
                symbols_hash = hash(tuple(sorted(self.symbols)))
                request_id = f"req_{timestamp}_{abs(symbols_hash) % 10000:04d}"
                object.__setattr__(self, 'request_id', request_id)

    @property
    def is_single_symbol(self) -> bool:
        """단일 심볼 요청 여부"""
        return len(self.symbols) == 1

    @property
    def is_bulk_request(self) -> bool:
        """대량 요청 여부 (20개 이상)"""
        return len(self.symbols) >= 20

    @property
    def requires_timeframe(self) -> bool:
        """시간 프레임 필요 여부"""
        return self.data_type == DataType.CANDLE

    @property
    def batch_friendly(self) -> bool:
        """배치 처리 적합 여부"""
        # 티커/오더북 타입이고 실시간이 아닌 경우 배치 적합
        return (
            self.data_type in [DataType.TICKER, DataType.ORDERBOOK]
            and not self.is_realtime
        )

    @property
    def estimated_response_size_kb(self) -> float:
        """예상 응답 크기 (KB)"""
        # 데이터 타입별 평균 크기 추정
        base_sizes = {
            DataType.TICKER: 0.5,      # ~500 bytes per symbol
            DataType.ORDERBOOK: 2.0,   # ~2KB per symbol
            DataType.TRADE: 1.0,       # ~1KB per symbol
            DataType.CANDLE: 0.1       # ~100 bytes per candle
        }

        base_size = base_sizes.get(self.data_type, 1.0)
        symbol_count = len(self.symbols)

        if self.data_type == DataType.CANDLE and self.count:
            return base_size * symbol_count * self.count

        return base_size * symbol_count

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'request_id': self.request_id,
            'symbols': self.symbols,
            'data_type': self.data_type.value,
            'timeframe': self.timeframe.value if self.timeframe else None,
            'count': self.count,
            'to_date': self.to_date,
            'is_realtime': self.is_realtime,
            'update_interval_ms': self.update_interval_ms,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'metadata': self.metadata,
            'is_single_symbol': self.is_single_symbol,
            'is_bulk_request': self.is_bulk_request,
            'batch_friendly': self.batch_friendly,
            'estimated_response_size_kb': self.estimated_response_size_kb
        }

    @classmethod
    def create_ticker_request(
        cls,
        symbols: List[str],
        is_realtime: bool = False
    ) -> 'RoutingRequest':
        """티커 요청 생성"""
        return cls(
            symbols=symbols,
            data_type=DataType.TICKER,
            is_realtime=is_realtime
        )

    @classmethod
    def create_candle_request(
        cls,
        symbols: List[str],
        timeframe: TimeFrame,
        count: int = 200,
        to_date: Optional[str] = None
    ) -> 'RoutingRequest':
        """캔들 요청 생성"""
        return cls(
            symbols=symbols,
            data_type=DataType.CANDLE,
            timeframe=timeframe,
            count=count,
            to_date=to_date
        )

    @classmethod
    def create_orderbook_request(
        cls,
        symbols: List[str],
        is_realtime: bool = False
    ) -> 'RoutingRequest':
        """오더북 요청 생성"""
        return cls(
            symbols=symbols,
            data_type=DataType.ORDERBOOK,
            is_realtime=is_realtime
        )
