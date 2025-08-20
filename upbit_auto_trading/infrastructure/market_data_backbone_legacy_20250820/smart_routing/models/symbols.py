"""
거래소 독립적 심볼 관리

이 모듈은 다양한 거래소의 심볼 표기법을 통일된 형태로 관리합니다.
업비트의 "KRW-BTC" 형태를 표준으로 하되, 다른 거래소 확장 시에도
쉽게 변환할 수 있도록 설계되었습니다.
"""

from dataclasses import dataclass
from typing import Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass(frozen=True)
class TradingSymbol:
    """거래소 독립적 거래 심볼"""

    base_currency: str      # 기준 통화 (예: BTC, ETH)
    quote_currency: str     # 견적 통화 (예: KRW, USDT)
    exchange: str = "upbit"  # 거래소 (기본값: upbit)

    def __post_init__(self):
        """초기화 후 검증"""
        if not self.base_currency or not self.quote_currency:
            raise ValueError("base_currency와 quote_currency는 필수입니다")

        # 대문자로 정규화
        object.__setattr__(self, 'base_currency', self.base_currency.upper())
        object.__setattr__(self, 'quote_currency', self.quote_currency.upper())
        object.__setattr__(self, 'exchange', self.exchange.lower())

    @classmethod
    def from_upbit_format(cls, symbol: str) -> 'TradingSymbol':
        """업비트 형식에서 TradingSymbol 생성 (예: KRW-BTC)"""
        if not symbol or '-' not in symbol:
            raise ValueError(f"잘못된 업비트 심볼 형식: {symbol}")

        parts = symbol.split('-')
        if len(parts) != 2:
            raise ValueError(f"업비트 심볼은 'QUOTE-BASE' 형식이어야 합니다: {symbol}")

        quote_currency, base_currency = parts
        return cls(
            base_currency=base_currency,
            quote_currency=quote_currency,
            exchange="upbit"
        )

    @classmethod
    def from_binance_format(cls, symbol: str) -> 'TradingSymbol':
        """바이낸스 형식에서 TradingSymbol 생성 (예: BTCUSDT)"""
        # 향후 바이낸스 지원 시 구현
        # 현재는 업비트 전용이므로 placeholder
        raise NotImplementedError("바이낸스 형식은 아직 지원되지 않습니다")

    def to_upbit_format(self) -> str:
        """업비트 형식으로 변환 (KRW-BTC)"""
        return f"{self.quote_currency}-{self.base_currency}"

    def to_binance_format(self) -> str:
        """바이낸스 형식으로 변환 (BTCUSDT)"""
        # 향후 바이낸스 지원 시 구현
        return f"{self.base_currency}{self.quote_currency}"

    def to_exchange_format(self, exchange: Optional[str] = None) -> str:
        """지정된 거래소 형식으로 변환"""
        target_exchange = exchange or self.exchange

        if target_exchange == "upbit":
            return self.to_upbit_format()
        elif target_exchange == "binance":
            return self.to_binance_format()
        else:
            raise ValueError(f"지원되지 않는 거래소: {target_exchange}")

    def is_krw_pair(self) -> bool:
        """KRW 페어인지 확인"""
        return self.quote_currency == "KRW"

    def is_usdt_pair(self) -> bool:
        """USDT 페어인지 확인"""
        return self.quote_currency == "USDT"

    def is_btc_pair(self) -> bool:
        """BTC 페어인지 확인"""
        return self.quote_currency == "BTC"

    def __str__(self) -> str:
        """문자열 표현 (업비트 형식)"""
        return self.to_upbit_format()

    def __repr__(self) -> str:
        """개발자용 표현"""
        return f"TradingSymbol('{self.base_currency}', '{self.quote_currency}', '{self.exchange}')"


class SymbolValidator:
    """심볼 유효성 검증 클래스"""

    # 업비트 지원 원화 마켓
    UPBIT_KRW_MARKETS = {
        "BTC", "ETH", "ADA", "XRP", "DOT", "LINK", "LTC", "BCH",
        "ETC", "OMG", "CVC", "DKA", "EOS", "BSV", "TRX", "QTUM",
        "BTG", "IOTA", "POWR", "ICX", "STEEM", "NEO", "MTL", "LRC",
        # 더 많은 심볼들... (실제로는 API에서 동적으로 가져와야 함)
    }

    def __init__(self):
        self._logger = create_component_logger("SymbolValidator")

    def validate_upbit_symbol(self, symbol: TradingSymbol) -> bool:
        """업비트 심볼 유효성 검증"""
        if symbol.exchange != "upbit":
            return True  # 다른 거래소는 일단 통과

        if symbol.is_krw_pair():
            # KRW 마켓 검증
            is_valid = symbol.base_currency in self.UPBIT_KRW_MARKETS
            if not is_valid:
                self._logger.warning(f"지원되지 않는 KRW 마켓: {symbol}")
            return is_valid

        # BTC, USDT 마켓은 별도 검증 로직 필요
        return True

    def suggest_similar_symbols(self, invalid_symbol: str) -> list[str]:
        """비슷한 심볼 제안"""
        # 간단한 유사도 기반 제안 (향후 개선 가능)
        suggestions = []
        for market in self.UPBIT_KRW_MARKETS:
            if market.lower() in invalid_symbol.lower():
                suggestions.append(f"KRW-{market}")
        return suggestions[:5]  # 최대 5개


# 편의 함수들
def create_krw_symbol(base_currency: str) -> TradingSymbol:
    """KRW 페어 심볼 생성"""
    return TradingSymbol(base_currency=base_currency, quote_currency="KRW")


def create_usdt_symbol(base_currency: str) -> TradingSymbol:
    """USDT 페어 심볼 생성"""
    return TradingSymbol(base_currency=base_currency, quote_currency="USDT")


def parse_symbol(symbol_str: str, exchange: str = "upbit") -> TradingSymbol:
    """문자열에서 심볼 파싱"""
    if exchange == "upbit":
        return TradingSymbol.from_upbit_format(symbol_str)
    else:
        raise ValueError(f"지원되지 않는 거래소: {exchange}")


# 상수
POPULAR_KRW_SYMBOLS = [
    create_krw_symbol("BTC"),
    create_krw_symbol("ETH"),
    create_krw_symbol("ADA"),
    create_krw_symbol("XRP"),
    create_krw_symbol("DOT"),
]
