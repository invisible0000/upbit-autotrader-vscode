# d:\projects\upbit-autotrader-vscode\upbit_auto_trading\infrastructure\market_data_backbone\smart_router\models\canonical_candle.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class CanonicalCandle:
    """
    표준화된 캔들 데이터 모델입니다.
    """
    symbol: str  # 예: 'KRW-BTC'
    candle_date_time_utc: str # UTC 날짜 시간 문자열, 예: '2023-01-01T00:00:00Z'
    candle_date_time_kst: str # KST 날짜 시간 문자열
    opening_price: float # 시가
    high_price: float # 고가
    low_price: float # 저가
    closing_price: float # 종가
    trade_price: float # 캔들 기간 동안의 체결 가격 합계
    trade_volume: float # 캔들 기간 동안의 체결량 합계
    timestamp: int # 유닉스 타임스탬프 (밀리초)
    unit: Optional[int] = None # 캔들 단위 (예: 1, 3, 5, 15, 30, 60, 240, 1440)
    # 필요한 기타 관련 필드를 추가합니다.
