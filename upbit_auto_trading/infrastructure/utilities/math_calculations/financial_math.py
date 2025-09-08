# 수학 계산 유틸리티 - Infrastructure Layer
from decimal import Decimal
from typing import List, Optional, Union

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("MathCalculationsUtils")


def safe_decimal(value: Union[str, int, float, Decimal], precision: int = 8) -> Decimal:
    """안전한 Decimal 변환 (자동매매용 정밀도 보장)"""
    try:
        return Decimal(str(value)).quantize(Decimal('0.' + '0' * precision))
    except Exception as e:
        logger.error(f"Decimal 변환 실패 {value}: {e}")
        return Decimal('0')


def percentage_change(old_value: Union[Decimal, float], new_value: Union[Decimal, float]) -> Decimal:
    """퍼센트 변화율 계산"""
    old_decimal = safe_decimal(old_value)
    new_decimal = safe_decimal(new_value)

    if old_decimal == 0:
        return Decimal('0')

    return ((new_decimal - old_decimal) / old_decimal) * 100


def round_to_tick_size(value: Union[Decimal, float], tick_size: Union[Decimal, float]) -> Decimal:
    """틱 사이즈에 맞춰 반올림 (업비트 호가 단위)"""
    value_decimal = safe_decimal(value)
    tick_decimal = safe_decimal(tick_size)

    if tick_decimal == 0:
        return value_decimal

    # 틱 단위로 내림 처리
    return (value_decimal // tick_decimal) * tick_decimal


def calculate_order_amount(price: Union[Decimal, float], quantity: Union[Decimal, float],
                           fee_rate: Union[Decimal, float] = Decimal('0.0005')) -> dict:
    """주문 금액 계산 (수수료 포함)"""
    price_decimal = safe_decimal(price)
    quantity_decimal = safe_decimal(quantity)
    fee_decimal = safe_decimal(fee_rate)

    gross_amount = price_decimal * quantity_decimal
    fee_amount = gross_amount * fee_decimal
    net_amount = gross_amount + fee_amount

    return {
        'gross_amount': gross_amount,
        'fee_amount': fee_amount,
        'net_amount': net_amount,
        'effective_price': net_amount / quantity_decimal if quantity_decimal > 0 else Decimal('0')
    }


def calculate_rsi(prices: List[Union[Decimal, float]], period: int = 14) -> Optional[Decimal]:
    """RSI (Relative Strength Index) 계산"""
    if len(prices) < period + 1:
        return None

    # 가격 변화 계산
    price_changes = []
    for i in range(1, len(prices)):
        change = safe_decimal(prices[i]) - safe_decimal(prices[i - 1])
        price_changes.append(change)

    if len(price_changes) < period:
        return None

    # 상승/하락 분리
    gains = [change if change > 0 else Decimal('0') for change in price_changes[-period:]]
    losses = [-change if change < 0 else Decimal('0') for change in price_changes[-period:]]

    # 평균 계산
    avg_gain = sum(gains) / len(gains)
    avg_loss = sum(losses) / len(losses)

    if avg_loss == 0:
        return Decimal('100')

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return safe_decimal(rsi, 2)


def calculate_moving_average(values: List[Union[Decimal, float]], period: int) -> Optional[Decimal]:
    """이동평균 계산"""
    if len(values) < period:
        return None

    recent_values = values[-period:]
    total = sum(safe_decimal(v) for v in recent_values)

    return total / period


def calculate_volatility(prices: List[Union[Decimal, float]], period: int = 20) -> Optional[Decimal]:
    """변동성 계산 (표준편차)"""
    if len(prices) < period:
        return None

    recent_prices = [safe_decimal(p) for p in prices[-period:]]
    mean_price = sum(recent_prices) / len(recent_prices)

    # 분산 계산
    variance = sum((price - mean_price) ** 2 for price in recent_prices) / len(recent_prices)

    # 표준편차 (변동성)
    volatility = variance.sqrt()

    return safe_decimal(volatility, 4)


def is_within_tolerance(value1: Union[Decimal, float], value2: Union[Decimal, float],
                       tolerance_percent: Union[Decimal, float] = Decimal('0.01')) -> bool:
    """허용 오차 범위 내 비교"""
    val1 = safe_decimal(value1)
    val2 = safe_decimal(value2)
    tolerance = safe_decimal(tolerance_percent)

    if val1 == 0 and val2 == 0:
        return True

    if val1 == 0 or val2 == 0:
        return False

    diff_percent = abs((val1 - val2) / val1) * 100
    return diff_percent <= tolerance


def calculate_position_size(account_balance: Union[Decimal, float],
                           risk_percent: Union[Decimal, float],
                           entry_price: Union[Decimal, float],
                           stop_loss_price: Union[Decimal, float]) -> Decimal:
    """포지션 크기 계산 (리스크 관리)"""
    balance = safe_decimal(account_balance)
    risk = safe_decimal(risk_percent) / 100
    entry = safe_decimal(entry_price)
    stop_loss = safe_decimal(stop_loss_price)

    if entry == 0 or stop_loss == 0:
        return Decimal('0')

    # 리스크 금액
    risk_amount = balance * risk

    # 손실 폭
    loss_per_unit = abs(entry - stop_loss)

    if loss_per_unit == 0:
        return Decimal('0')

    # 포지션 크기
    position_size = risk_amount / loss_per_unit

    return safe_decimal(position_size, 6)


def normalize_to_range(value: Union[Decimal, float], min_val: Union[Decimal, float],
                      max_val: Union[Decimal, float]) -> Decimal:
    """값을 0-1 범위로 정규화"""
    val = safe_decimal(value)
    min_decimal = safe_decimal(min_val)
    max_decimal = safe_decimal(max_val)

    if max_decimal == min_decimal:
        return Decimal('0.5')

    normalized = (val - min_decimal) / (max_decimal - min_decimal)

    # 0-1 범위로 클램핑
    return max(Decimal('0'), min(Decimal('1'), normalized))
