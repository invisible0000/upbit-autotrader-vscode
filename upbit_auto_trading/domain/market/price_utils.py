"""
업비트 원화 마켓 호가 단위 처리 유틸리티

업비트 공식 예제 기반의 호가 단위 계산 및 가격 정규화 함수들
"""

from decimal import Decimal, getcontext, ROUND_DOWN
from typing import Union

# Decimal 정밀도 설정
getcontext().prec = 16


def get_tick_size(price: Decimal) -> Decimal:
    """
    업비트 원화 마켓 호가 단위 반환

    Args:
        price: 가격 (Decimal)

    Returns:
        Decimal: 해당 가격대의 호가 단위

    Raises:
        ValueError: price가 0 이하인 경우
    """
    if price <= 0:
        raise ValueError("price must be > 0")

    if price < Decimal("0.00001"):
        return Decimal("1e-8")

    decade = int(price.log10().to_integral_value(rounding=ROUND_DOWN))

    if decade < 3:
        return Decimal(10) ** (decade - 2)

    if decade >= 6:
        return Decimal("1000")

    base = Decimal(10) ** (decade - 3)
    leading = price / (Decimal(10) ** decade)
    step = Decimal("5") if leading >= Decimal("5") else Decimal("1")
    return min(base * step, Decimal("1000"))


def round_price_by_tick_size(price: Union[int, float, Decimal]) -> Decimal:
    """
    price가 호가 단위에 맞지 않는 경우 호가 단위에 맞게 내림

    Args:
        price: 정규화할 가격

    Returns:
        Decimal: 호가 단위에 맞게 내림된 가격
    """
    price_decimal = Decimal(str(price))
    tick = get_tick_size(price_decimal)
    return (price_decimal // tick) * tick


def format_krw_price(price: Union[int, float, Decimal]) -> str:
    """
    KRW 가격을 읽기 쉬운 형태로 포맷팅

    Args:
        price: 가격

    Returns:
        str: 포맷된 가격 문자열 (예: "159,476,000원")
    """
    return f"{int(price):,}원"


def calculate_safe_order_price(market_price: Union[int, float, Decimal],
                               discount_rate: float = 0.95) -> Decimal:
    """
    시장가 기준으로 안전한 주문가를 계산 (호가 단위 적용)

    Args:
        market_price: 시장 기준가
        discount_rate: 할인율 (기본값: 0.95 = 5% 할인)

    Returns:
        Decimal: 호가 단위에 맞게 조정된 안전한 주문가
    """
    market_decimal = Decimal(str(market_price))
    discounted_price = market_decimal * Decimal(str(discount_rate))
    return round_price_by_tick_size(discounted_price)


def adjust_volume_for_krw_integer(price: Union[int, float, Decimal],
                                  target_krw: int) -> Decimal:
    """
    업비트 원화 정수 규칙에 맞는 수량 계산

    업비트에서는 가격 × 수량 = 정수원 결과가 나와야 합니다.
    이 함수는 목표 원화 금액에 맞는 정확한 수량을 계산합니다.

    Args:
        price: 주문 가격 (원)
        target_krw: 목표 원화 금액 (원)

    Returns:
        Decimal: 정수원 결과를 보장하는 조정된 수량

    Example:
        >>> adjust_volume_for_krw_integer(159394000, 5000)
        Decimal('0.00003137')  # 159394000 * 0.00003137 ≈ 5000원
    """
    price_decimal = Decimal(str(price))

    # 기본 수량 계산
    base_volume = Decimal(str(target_krw)) / price_decimal
    base_volume = base_volume.quantize(Decimal('0.00000001'))  # 8자리 정밀도

    # 실제 원화 결과 확인
    actual_krw = int(base_volume * price_decimal)

    # 목표 금액보다 부족하면 1 사토시씩 추가하여 조정
    while actual_krw < target_krw:
        base_volume += Decimal('0.00000001')
        actual_krw = int(base_volume * price_decimal)

        # 무한 루프 방지 (최대 100 사토시까지만 조정)
        if base_volume > (Decimal(str(target_krw)) / price_decimal) + Decimal('0.00001000'):
            break

    return base_volume


def validate_krw_order(price: Union[int, float, Decimal],
                       volume: Union[float, Decimal]) -> dict:
    """
    업비트 원화 주문 유효성 검증

    Args:
        price: 주문 가격 (원)
        volume: 주문 수량 (BTC)

    Returns:
        dict: {
            'is_valid': bool,
            'total_krw': int,
            'issues': List[str]
        }
    """
    price_decimal = Decimal(str(price))
    volume_decimal = Decimal(str(volume))
    issues = []

    # 가격이 정수인지 확인
    if price_decimal % 1 != 0:
        issues.append(f"가격은 정수여야 합니다: {price_decimal}")

    # 총 원화 금액 계산
    total_krw = int(price_decimal * volume_decimal)

    # 최소 주문 금액 확인 (5,000원)
    if total_krw < 5000:
        issues.append(f"최소 주문 금액 미달: {total_krw:,}원 < 5,000원")

    # 수량 정밀도 확인 (8자리)
    exponent = volume_decimal.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -8:
        issues.append("수량 정밀도 초과: 최대 8자리까지 허용")

    return {
        'is_valid': len(issues) == 0,
        'total_krw': total_krw,
        'issues': issues
    }


if __name__ == "__main__":
    # 테스트 케이스
    test_prices = [159476000, 151502200, 100000000, 50000000]

    print("🔧 업비트 호가 단위 테스트")
    print("=" * 50)

    for price in test_prices:
        tick = get_tick_size(Decimal(str(price)))
        rounded = round_price_by_tick_size(price)

        print(f"가격: {format_krw_price(price)}")
        print(f"호가단위: {tick}원")
        print(f"조정가격: {format_krw_price(rounded)}")
        print(f"조정차이: {price - int(rounded):,}원")
        print("-" * 30)
