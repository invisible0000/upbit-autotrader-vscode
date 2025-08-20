"""
거래 심볼 도메인 모델

거래소 독립적인 심볼 표현을 제공합니다.
업비트의 "KRW-BTC" 형태를 완전히 추상화합니다.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TradingSymbol:
    """거래 심볼 도메인 객체

    거래소별 심볼 형태의 차이를 추상화하여
    통일된 형태로 심볼을 표현합니다.
    """

    base_currency: str  # 기준 통화 (예: BTC, ETH)
    quote_currency: str  # 견적 통화 (예: KRW, USDT)

    def __post_init__(self):
        """초기화 후 검증"""
        if not self.base_currency or not self.quote_currency:
            raise ValueError("기준 통화와 견적 통화는 필수입니다")

        # 대문자로 정규화
        object.__setattr__(self, 'base_currency', self.base_currency.upper())
        object.__setattr__(self, 'quote_currency', self.quote_currency.upper())

    @classmethod
    def from_upbit_symbol(cls, upbit_symbol: str) -> 'TradingSymbol':
        """업비트 심볼 형태에서 생성

        Args:
            upbit_symbol: "KRW-BTC" 형태의 업비트 심볼

        Returns:
            TradingSymbol 객체

        Example:
            >>> symbol = TradingSymbol.from_upbit_symbol("KRW-BTC")
            >>> symbol.base_currency
            'BTC'
            >>> symbol.quote_currency
            'KRW'
        """
        if '-' not in upbit_symbol:
            raise ValueError(f"올바르지 않은 업비트 심볼 형태: {upbit_symbol}")

        quote, base = upbit_symbol.split('-', 1)
        return cls(base_currency=base, quote_currency=quote)

    @classmethod
    def from_standard_symbol(cls, base: str, quote: str) -> 'TradingSymbol':
        """표준 형태에서 생성

        Args:
            base: 기준 통화 (BTC, ETH 등)
            quote: 견적 통화 (KRW, USDT 등)

        Returns:
            TradingSymbol 객체
        """
        return cls(base_currency=base, quote_currency=quote)

    def to_upbit_symbol(self) -> str:
        """업비트 심볼 형태로 변환

        Returns:
            "KRW-BTC" 형태의 업비트 심볼
        """
        return f"{self.quote_currency}-{self.base_currency}"

    def to_standard_symbol(self) -> str:
        """표준 심볼 형태로 변환

        Returns:
            "BTCKRW" 형태의 표준 심볼
        """
        return f"{self.base_currency}{self.quote_currency}"

    def __str__(self) -> str:
        """문자열 표현"""
        return f"{self.base_currency}/{self.quote_currency}"

    def __repr__(self) -> str:
        """디버그 표현"""
        return f"TradingSymbol(base='{self.base_currency}', quote='{self.quote_currency}')"


# 자주 사용되는 심볼들을 상수로 정의
class CommonSymbols:
    """자주 사용되는 심볼들"""

    # KRW 마켓
    BTC_KRW = TradingSymbol("BTC", "KRW")
    ETH_KRW = TradingSymbol("ETH", "KRW")
    XRP_KRW = TradingSymbol("XRP", "KRW")
    ADA_KRW = TradingSymbol("ADA", "KRW")
    DOT_KRW = TradingSymbol("DOT", "KRW")

    # BTC 마켓
    ETH_BTC = TradingSymbol("ETH", "BTC")
    XRP_BTC = TradingSymbol("XRP", "BTC")
    ADA_BTC = TradingSymbol("ADA", "BTC")

    # USDT 마켓 (향후 확장용)
    BTC_USDT = TradingSymbol("BTC", "USDT")
    ETH_USDT = TradingSymbol("ETH", "USDT")
