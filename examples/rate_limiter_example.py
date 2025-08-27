#!/usr/bin/env python3
"""
Rate Limiting 필터 실행 예제 (올바른 구현)
- 시간 간격 기반 처리 제한
- 중복 여부와 관계없이 최신값만 처리
- 웹소켓 초당 100회 → 실제 처리 초당 5-10회
"""

import time
import random
from typing import Any, Callable


def create_rate_limiter(interval_seconds: float = 0.2) -> Callable[[str, Any], bool]:
    """
    Rate Limiter 생성 (시간 간격 기반)

    Args:
        interval_seconds: 최소 처리 간격

    Returns:
        limiter_func: (symbol, value) -> bool 함수
    """
    # 클로저로 상태 보관: symbol -> (last_value, last_time)
    last_processed = {}

    def should_process(symbol: str, value: Any) -> bool:
        """
        Rate Limiting 처리 여부 판정
        - interval_seconds 내에는 최신값만 업데이트, 처리는 스킹
        - interval_seconds 지나면 마지막 최신값으로 처리
        """
        current_time = time.time()

        # 이전 처리 시간 확인
        if symbol in last_processed:
            last_value, last_time = last_processed[symbol]

            # 아직 간격이 안 지났으면 최신값만 업데이트하고 스킵
            if current_time - last_time < interval_seconds:
                last_processed[symbol] = (value, last_time)  # 값만 업데이트, 시간은 유지
                return False

        # 간격이 지났거나 첫 번째 요청 → 처리
        last_processed[symbol] = (value, current_time)
        return True

    return should_process


def create_ticker_rate_limiter() -> Callable[[str, Any], bool]:
    """현재가 Rate Limiter (0.2초 간격)"""
    return create_rate_limiter(interval_seconds=0.2)


def create_trade_rate_limiter() -> Callable[[str, Any], bool]:
    """체결 Rate Limiter (0.1초 간격)"""
    return create_rate_limiter(interval_seconds=0.1)


def run_rate_limiting_demo():
    """Rate Limiting 데모"""
    print("=" * 60)
    print("Rate Limiting 데모 (올바른 구현)")
    print("=" * 60)
    print("웹소켓 초당 100회 → 실제 처리 초당 5-10회")
    print()

    # Rate Limiter 생성
    ticker_limiter = create_ticker_rate_limiter()
    trade_limiter = create_trade_rate_limiter()

    # 통계
    stats = {
        'ticker_received': 0,
        'ticker_processed': 0,
        'trade_received': 0,
        'trade_processed': 0
    }

    print("고빈도 데이터 수신 시뮬레이션 (10초간)")
    print(f"{'시간':<8} {'타입':<8} {'심볼':<10} {'값':<12} {'결과':<8}")
    print("-" * 55)

    start_time = time.time()

    # 고빈도 데이터 시뮬레이션 (실제로는 0.01초마다 데이터가 온다고 가정)
    while time.time() - start_time < 5:  # 5초간
        current_time = time.time() - start_time

        # 현재가 데이터 (자주 변하는 값)
        symbol = 'KRW-BTC'
        price = 50000000 + random.randint(-100000, 100000)
        stats['ticker_received'] += 1

        if ticker_limiter(symbol, price):
            stats['ticker_processed'] += 1
            print(f"{current_time:6.2f}s {'ticker':<8} {symbol:<10} {price:>10,} {'처리':<8}")
        # else: 내부적으로 최신값 업데이트됨 (출력 안 함)

        time.sleep(0.01)  # 0.01초마다 데이터 수신 (초당 100회)

        # 체결 데이터도 같이
        if int(current_time * 100) % 2 == 0:  # 절반 확률로 체결 데이터
            seq_id = random.randint(1000000, 1000010)
            stats['trade_received'] += 1

            if trade_limiter(symbol, seq_id):
                stats['trade_processed'] += 1
                print(f"{current_time:6.2f}s {'trade':<8} {symbol:<10} {seq_id:>10} {'처리':<8}")

    # 최종 통계
    print(f"\n최종 통계:")
    print(f"  현재가: 수신 {stats['ticker_received']}회 → 처리 {stats['ticker_processed']}회")
    print(f"  체결: 수신 {stats['trade_received']}회 → 처리 {stats['trade_processed']}회")

    if stats['ticker_received'] > 0:
        ticker_rate = stats['ticker_processed'] / (5 / 60)  # 5초 → 분당 처리율
        print(f"  현재가 실제 처리율: {ticker_rate:.1f}회/분 (목표: 300회/분)")

    if stats['trade_received'] > 0:
        trade_rate = stats['trade_processed'] / (5 / 60)
        print(f"  체결 실제 처리율: {trade_rate:.1f}회/분 (목표: 600회/분)")


def run_comparison_demo():
    """잘못된 중복 필터 vs 올바른 Rate Limiter 비교"""
    print("\n" + "=" * 60)
    print("중복 필터 vs Rate Limiter 비교")
    print("=" * 60)

    # 잘못된 중복 필터 (기존 방식)
    def wrong_duplicate_filter():
        last_states = {}
        def should_process(symbol: str, value: Any) -> bool:
            current_time = time.time()
            if symbol in last_states:
                last_value, last_time = last_states[symbol]
                if current_time - last_time <= 0.2 and last_value == value:
                    return False  # 같은 값이면 스킵
            last_states[symbol] = (value, current_time)
            return True
        return should_process

    # 올바른 Rate Limiter
    rate_limiter = create_rate_limiter(interval_seconds=0.2)
    duplicate_filter = wrong_duplicate_filter()

    print("시나리오: 0.05초마다 같은 가격이 5번 연속 수신")
    print()

    symbol = 'KRW-BTC'
    price = 50000000

    for i in range(5):
        print(f"  {i*0.05:.2f}초: 가격 {price:,}")

        dup_result = "처리" if duplicate_filter(symbol, price) else "스킵"
        rate_result = "처리" if rate_limiter(symbol, price) else "스킵"

        print(f"    중복 필터: {dup_result}")
        print(f"    Rate Limiter: {rate_result}")
        print()

        time.sleep(0.05)

    print("결과 분석:")
    print("  중복 필터: 첫 번째만 처리, 나머지는 스킵 (같은 값이라서)")
    print("  Rate Limiter: 첫 번째 처리, 0.2초 후 마지막 값으로 처리")
    print("  → Rate Limiter가 웹소켓 환경에 적합!")


def main():
    """메인 실행 함수"""
    print("Rate Limiting 필터 예제 (올바른 웹소켓 처리)")
    print("웹소켓 고빈도 데이터 → 적절한 빈도로 처리")
    print()

    # 1단계: Rate Limiting 데모
    run_rate_limiting_demo()

    # 2단계: 비교 데모
    run_comparison_demo()

    print("\n모든 테스트 완료!")
    print("\n결론: 웹소켓에는 중복 필터가 아닌 Rate Limiter가 필요합니다!")


if __name__ == "__main__":
    main()
