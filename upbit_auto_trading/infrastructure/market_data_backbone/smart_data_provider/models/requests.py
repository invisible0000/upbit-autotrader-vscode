"""
요청 모델 정의
Smart Data Provider의 요청 구조를 정의합니다.
"""
from dataclasses import dataclass
from typing import Optional, List
from .priority import Priority


@dataclass(frozen=True)
class DataRequest:
    """데이터 요청"""
    request_type: str  # "candles", "ticker", "orderbook", "trades"
    symbol: str
    priority: Priority = Priority.NORMAL

    # 캔들 관련
    timeframe: Optional[str] = None
    count: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    # 다중 심볼
    symbols: Optional[List[str]] = None

    # 기타
    params: Optional[dict] = None

    def __post_init__(self):
        """요청 유효성 검증"""
        if self.request_type == "candles" and not self.timeframe:
            raise ValueError("캔들 요청시 timeframe은 필수입니다")

        if self.request_type in ["tickers"] and not self.symbols:
            raise ValueError("다중 티커 요청시 symbols는 필수입니다")
