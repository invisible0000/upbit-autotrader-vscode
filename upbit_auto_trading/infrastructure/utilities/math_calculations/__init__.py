# Math Calculations Utilities
"""
수학적 계산 유틸리티 (금융/자동매매 특화)

기능:
- Decimal 안전 변환 (정밀도 보장)
- 퍼센트 변화율 계산
- 틱 사이즈 반올림
- 주문 금액/수수료 계산
- 기술적 지표 (RSI, 이동평균, 변동성)
- 포지션 크기 계산 (리스크 관리)
- 정규화 및 허용 오차 비교
"""

from .financial_math import (
    safe_decimal,
    percentage_change,
    round_to_tick_size,
    calculate_order_amount,
    calculate_rsi,
    calculate_moving_average,
    calculate_volatility,
    is_within_tolerance,
    calculate_position_size,
    normalize_to_range
)

__all__ = [
    'safe_decimal',
    'percentage_change',
    'round_to_tick_size',
    'calculate_order_amount',
    'calculate_rsi',
    'calculate_moving_average',
    'calculate_volatility',
    'is_within_tolerance',
    'calculate_position_size',
    'normalize_to_range'
]
