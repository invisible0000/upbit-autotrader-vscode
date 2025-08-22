# d:\projects\upbit-autotrader-vscode\upbit_auto_trading\infrastructure\market_data_backbone\smart_router\models\canonical_ticker.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class CanonicalTicker:
    """
    표준화된 티커 데이터 모델입니다.
    """
    symbol: str  # 예: 'KRW-BTC'
    trade_price: float # 체결 가격
    trade_volume: float # 체결량
    change: str # 변화 상태: 'RISE'(상승), 'FALL'(하락), 'EVEN'(보합)
    change_price: float # 변화액
    signed_change_price: float # 부호 있는 변화액
    change_rate: float # 변화율
    signed_change_rate: float # 부호 있는 변화율
    ask_bid: str # 매수/매도 구분: 'ASK'(매도), 'BID'(매수)
    high_price: float # 고가
    low_price: float # 저가
    trade_timestamp: int # 체결 타임스탬프 (Unix milliseconds)
    acc_trade_price_24h: float # 24시간 누적 거래대금
    acc_trade_volume_24h: float # 24시간 누적 거래량
    # REST 및 WS에서 필요한 기타 관련 필드를 추가합니다.
