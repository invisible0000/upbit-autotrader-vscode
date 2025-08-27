#!/usr/bin/env python3
"""
매크로 스타일 중복 필터 실행 예제
- 최고 성능의 중복 필터링
- 클로저를 활용한 상태 관리
- 실제 웹소켓 데이터 시뮬레이션
"""

import time
import random
from typing import Any, Callable


def create_ticker_filter(window_seconds: float = 0.2) -> Callable[[str, Any], bool]:
    """
    현재가 중복 필터 생성 (매크로 스타일)

    Args:
        window_seconds: 중복 판정 시간 윈도우

    Returns:
        filter_func: (symbol, price) -> bool 함수
    """
    # 클로저로 상태 보관
    last_states = {}

    def should_process_ticker(symbol: str, price: Any) -> bool:
        """현재가 처리 여부 판정"""
        current_time = time.time()

        # 이전 상태 확인
        if symbol in last_states:
            last_price, last_time = last_states[symbol]
            # 시간 윈도우 내 같은 가격이면 스킵
            if (current_time - last_time <= window_seconds and
                last_price == price):
                return False

        # 새 상태 저장
        last_states[symbol] = (price, current_time)
        return True

    return should_process_ticker


def create_trade_filter(window_seconds: float = 0.1) -> Callable[[str, Any], bool]:
    """
    체결 중복 필터 생성 (매크로 스타일)

    Args:
        window_seconds: 중복 판정 시간 윈도우

    Returns:
        filter_func: (symbol, seq_id) -> bool 함수
    """
    last_states = {}

    def should_process_trade(symbol: str, seq_id: Any) -> bool:
        """체결 처리 여부 판정"""
        current_time = time.time()

        if symbol in last_states:
            last_seq_id, last_time = last_states[symbol]
            if (current_time - last_time <= window_seconds and
                last_seq_id == seq_id):
                return False

        last_states[symbol] = (seq_id, current_time)
        return True

    return should_process_trade


def simulate_websocket_data():
    """웹소켓 데이터 시뮬레이션"""
    symbols = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']

    while True:
        # 현재가 데이터
        yield {
            'type': 'ticker',
            'symbol': random.choice(symbols),
            'price': round(50000000 + random.randint(-1000000, 1000000), -3),
            'timestamp': time.time()
        }

        # 체결 데이터
        yield {
            'type': 'trade',
            'symbol': random.choice(symbols),
            'seq_id': random.randint(1000000, 9999999),
            'price': round(50000000 + random.randint(-1000000, 1000000), -3),
            'volume': round(random.uniform(0.1, 10.0), 4),
            'timestamp': time.time()
        }


def run_performance_test():
    """매크로 스타일 필터 성능 테스트"""
    print("=" * 60)
    print("매크로 스타일 중복 필터 성능 테스트")
    print("=" * 60)

    # 필터 생성
    ticker_filter = create_ticker_filter(window_seconds=0.2)
    trade_filter = create_trade_filter(window_seconds=0.1)

    # 테스트 데이터 생성 (중복이 많이 발생하도록)
    test_messages = []
    symbols = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
    base_time = time.time()

    print("테스트 데이터 생성 중...")

    # 기본 메시지들 생성
    for i in range(5000):
        # 현재가 메시지
        ticker_msg = {
            'type': 'ticker',
            'symbol': random.choice(symbols),
            'price': round(50000000 + random.randint(-500000, 500000), -3),
            'timestamp': base_time + i * 0.001
        }
        test_messages.append(ticker_msg)

        # 체결 메시지
        trade_msg = {
            'type': 'trade',
            'symbol': random.choice(symbols),
            'seq_id': random.randint(1000000, 1005000),  # 범위를 좁혀서 중복 유발
            'timestamp': base_time + i * 0.001
        }
        test_messages.append(trade_msg)

        # 의도적 중복 생성 (매 10번째마다)
        if i % 10 == 0 and i > 0:
            # 이전 ticker 메시지 복사 (동일한 시간대)
            dup_ticker = test_messages[-2].copy()
            dup_ticker['timestamp'] = base_time + i * 0.001 + 0.05  # 0.05초 후
            test_messages.append(dup_ticker)

            # 이전 trade 메시지 복사
            dup_trade = test_messages[-2].copy()
            dup_trade['timestamp'] = base_time + i * 0.001 + 0.05
            test_messages.append(dup_trade)

    print(f"총 {len(test_messages)}개 메시지 생성 (중복 포함)")

    # 성능 테스트 실행
    ticker_processed = 0
    ticker_filtered = 0
    trade_processed = 0
    trade_filtered = 0

    start_time = time.time()

    for message in test_messages:
        if message['type'] == 'ticker':
            if ticker_filter(message['symbol'], message['price']):
                ticker_processed += 1
            else:
                ticker_filtered += 1

        elif message['type'] == 'trade':
            if trade_filter(message['symbol'], message['seq_id']):
                trade_processed += 1
            else:
                trade_filtered += 1

    end_time = time.time()

    # 결과 출력
    duration = end_time - start_time
    total_messages = len(test_messages)
    messages_per_second = total_messages / duration if duration > 0 else 0

    print(f"\n테스트 결과:")
    print(f"  처리 시간: {duration:.4f}초")
    print(f"  처리 속도: {messages_per_second:,.0f} 메시지/초")
    print(f"  메시지당 평균 처리 시간: {duration/total_messages*1000:.3f}ms")

    print(f"\n현재가 필터:")
    print(f"  처리됨: {ticker_processed:,}")
    print(f"  필터됨: {ticker_filtered:,}")
    print(f"  필터율: {ticker_filtered/(ticker_processed+ticker_filtered)*100:.1f}%")

    print(f"\n체결 필터:")
    print(f"  처리됨: {trade_processed:,}")
    print(f"  필터됨: {trade_filtered:,}")
    print(f"  필터율: {trade_filtered/(trade_processed+trade_filtered)*100:.1f}%")


def run_real_time_demo():
    """실시간 필터링 데모"""
    print("\n" + "=" * 60)
    print("실시간 매크로 필터 데모 (5초간)")
    print("=" * 60)

    # 필터 생성
    ticker_filter = create_ticker_filter(window_seconds=0.2)
    trade_filter = create_trade_filter(window_seconds=0.1)

    # 통계
    stats = {
        'ticker_processed': 0,
        'ticker_filtered': 0,
        'trade_processed': 0,
        'trade_filtered': 0
    }

    # 중복이 발생하도록 고정된 값들 사용
    symbols = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
    fixed_prices = [50000000, 50100000, 49900000]
    fixed_seq_ids = [1000001, 1000002, 1000003]

    start_time = time.time()
    message_count = 0

    print("실시간 데이터 처리 중...")
    print(f"{'시간':<8} {'타입':<8} {'심볼':<10} {'값':<12} {'결과':<8}")
    print("-" * 50)

    try:
        while time.time() - start_time < 5:  # 5초간 실행
            message_count += 1
            current_time = time.time() - start_time

            # 중복이 발생하도록 의도적으로 설계 - 같은 심볼을 연속 사용
            if message_count % 2 == 1:  # 홀수번째는 ticker
                # 중복 테스트: 처음 몇 개는 같은 심볼+가격으로
                if message_count <= 5:
                    symbol = 'KRW-BTC'
                    price = 50000000  # 같은 가격
                else:
                    symbol = symbols[(message_count // 2) % 3]
                    price = fixed_prices[(message_count // 2) % 3]

                should_process = ticker_filter(symbol, price)
                if should_process:
                    stats['ticker_processed'] += 1
                    result = "처리"
                else:
                    stats['ticker_filtered'] += 1
                    result = "필터"

                print(f"{current_time:6.2f}s {'ticker':<8} {symbol:<10} {price:>10,} {result:<8}")

            else:  # 짝수번째는 trade
                # 중복 테스트: 처음 몇 개는 같은 심볼+seq_id로
                if message_count <= 6:
                    symbol = 'KRW-BTC'
                    seq_id = 1000001  # 같은 seq_id
                else:
                    symbol = symbols[(message_count // 2) % 3]
                    seq_id = fixed_seq_ids[(message_count // 2) % 3]

                should_process = trade_filter(symbol, seq_id)
                if should_process:
                    stats['trade_processed'] += 1
                    result = "처리"
                else:
                    stats['trade_filtered'] += 1
                    result = "필터"

                print(f"{current_time:6.2f}s {'trade':<8} {symbol:<10} {seq_id:>10} {result:<8}")

            # 실제 웹소켓 속도 시뮬레이션 (초당 5회)
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n사용자가 중단했습니다.")

    # 최종 통계
    print(f"\n최종 통계:")
    print(f"  총 메시지: {message_count}")
    print(f"  현재가 처리/필터: {stats['ticker_processed']}/{stats['ticker_filtered']}")
    print(f"  체결 처리/필터: {stats['trade_processed']}/{stats['trade_filtered']}")

    total_processed = stats['ticker_processed'] + stats['trade_processed']
    total_filtered = stats['ticker_filtered'] + stats['trade_filtered']

    if total_processed + total_filtered > 0:
        filter_rate = total_filtered / (total_processed + total_filtered) * 100
        print(f"  전체 필터율: {filter_rate:.1f}%")


def main():
    """메인 실행 함수 - 자동으로 순차 실행"""
    print("매크로 스타일 중복 필터 예제")
    print("자동으로 성능 테스트 → 실시간 데모 순서로 실행합니다.\n")

    # 1단계: 성능 테스트
    run_performance_test()

    # 2단계: 실시간 데모 (바로 실행)
    run_real_time_demo()

    print("\n모든 테스트 완료!")


if __name__ == "__main__":
    main()
