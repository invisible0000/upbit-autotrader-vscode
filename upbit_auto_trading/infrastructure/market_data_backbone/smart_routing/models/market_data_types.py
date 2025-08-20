"""
마켓 데이터 타입 도메인 모델

캔들, 티커, 호가창, 체결 데이터의 표준화된 형태를 정의합니다.
거래소별 데이터 형태의 차이를 완전히 추상화합니다.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class CandleData:
    """캔들(OHLCV) 데이터

    거래소 독립적인 캔들 데이터 표현
    """

    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal

    def __post_init__(self):
        """데이터 검증"""
        if self.high_price < max(self.open_price, self.close_price):
            raise ValueError("고가가 시가/종가보다 낮을 수 없습니다")
        if self.low_price > min(self.open_price, self.close_price):
            raise ValueError("저가가 시가/종가보다 높을 수 없습니다")
        if self.volume < 0:
            raise ValueError("거래량은 음수일 수 없습니다")


@dataclass(frozen=True)
class TickerData:
    """현재 시세 데이터

    거래소 독립적인 티커 데이터 표현
    """

    timestamp: datetime
    current_price: Decimal
    change_amount: Decimal  # 전일 대비 변화량
    change_rate: Decimal    # 전일 대비 변화율 (0.05 = 5%)
    volume_24h: Decimal     # 24시간 거래량
    high_24h: Decimal       # 24시간 최고가
    low_24h: Decimal        # 24시간 최저가
    opening_price: Decimal  # 당일 시가

    @property
    def is_price_up(self) -> bool:
        """가격 상승 여부"""
        return self.change_amount > 0

    @property
    def is_price_down(self) -> bool:
        """가격 하락 여부"""
        return self.change_amount < 0

    @property
    def change_percentage(self) -> Decimal:
        """변화율을 퍼센트로 반환 (5.0 = 5%)"""
        return self.change_rate * 100


@dataclass(frozen=True)
class OrderbookLevel:
    """호가창 단일 레벨

    매수/매도 호가의 가격과 수량
    """

    price: Decimal
    size: Decimal  # 수량

    def __post_init__(self):
        """데이터 검증"""
        if self.price <= 0:
            raise ValueError("가격은 양수여야 합니다")
        if self.size <= 0:
            raise ValueError("수량은 양수여야 합니다")


@dataclass(frozen=True)
class OrderbookData:
    """호가창 데이터

    거래소 독립적인 호가창 표현
    """

    timestamp: datetime
    bids: List[OrderbookLevel]  # 매수 호가 (가격 높은 순)
    asks: List[OrderbookLevel]  # 매도 호가 (가격 낮은 순)

    def __post_init__(self):
        """데이터 검증 및 정렬"""
        if not self.bids and not self.asks:
            raise ValueError("매수 또는 매도 호가가 있어야 합니다")

        # 매수 호가는 가격 높은 순으로 정렬되어야 함
        if len(self.bids) > 1:
            for i in range(len(self.bids) - 1):
                if self.bids[i].price < self.bids[i + 1].price:
                    raise ValueError("매수 호가는 가격 높은 순으로 정렬되어야 합니다")

        # 매도 호가는 가격 낮은 순으로 정렬되어야 함
        if len(self.asks) > 1:
            for i in range(len(self.asks) - 1):
                if self.asks[i].price > self.asks[i + 1].price:
                    raise ValueError("매도 호가는 가격 낮은 순으로 정렬되어야 합니다")

    @property
    def best_bid(self) -> Optional[OrderbookLevel]:
        """최고 매수 호가"""
        return self.bids[0] if self.bids else None

    @property
    def best_ask(self) -> Optional[OrderbookLevel]:
        """최저 매도 호가"""
        return self.asks[0] if self.asks else None

    @property
    def spread(self) -> Optional[Decimal]:
        """호가 스프레드"""
        if self.best_bid and self.best_ask:
            return self.best_ask.price - self.best_bid.price
        return None

    @property
    def mid_price(self) -> Optional[Decimal]:
        """중간 가격"""
        if self.best_bid and self.best_ask:
            return (self.best_bid.price + self.best_ask.price) / 2
        return None


@dataclass(frozen=True)
class TradeData:
    """체결 데이터

    거래소 독립적인 체결 내역 표현
    """

    timestamp: datetime
    price: Decimal
    size: Decimal  # 체결 수량
    side: str      # "buy" 또는 "sell" (체결 주도 방향)
    trade_id: Optional[str] = None  # 거래소별 체결 ID

    def __post_init__(self):
        """데이터 검증"""
        if self.price <= 0:
            raise ValueError("체결 가격은 양수여야 합니다")
        if self.size <= 0:
            raise ValueError("체결 수량은 양수여야 합니다")
        if self.side not in ("buy", "sell"):
            raise ValueError("체결 방향은 'buy' 또는 'sell'이어야 합니다")

    @property
    def is_buy(self) -> bool:
        """매수 체결 여부"""
        return self.side == "buy"

    @property
    def is_sell(self) -> bool:
        """매도 체결 여부"""
        return self.side == "sell"

    @property
    def notional_value(self) -> Decimal:
        """체결 금액 (가격 × 수량)"""
        return self.price * self.size
