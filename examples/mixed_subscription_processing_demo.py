"""
여러 타입이 섞인 WebSocket 구독 요청 처리 데모

🎯 목적: 업비트 WebSocket에서 여러 데이터 타입을 하나의 티켓으로 동시 구독하는 방법 시연
- TICKER + TRADE + ORDERBOOK + CANDLE을 단일 티켓으로 처리
- 실제 WebSocket 메시지 구조 확인
- 통합 구독 시스템의 내부 동작 원리 이해
"""

import asyncio
import json

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_public_client import (
    UpbitWebSocketPublicClient,
    WebSocketDataType,
    UnifiedSubscription
)


def show_mixed_subscription_message_structure():
    """혼합 타입 구독 메시지 구조 시연"""
    print("🔍 여러 타입이 섞인 구독 메시지 구조 분석")
    print("=" * 60)

    # 통합 구독 객체 생성
    ticket = "mixed-demo-12345678"
    unified_sub = UnifiedSubscription(ticket)

    # 1. TICKER 타입 추가
    unified_sub.add_subscription_type("ticker", ["KRW-BTC", "KRW-ETH"])
    print("1️⃣ TICKER 타입 추가:")
    print("   심볼: KRW-BTC, KRW-ETH")

    # 2. TRADE 타입 추가
    unified_sub.add_subscription_type("trade", ["KRW-BTC", "KRW-ETH"])
    print("2️⃣ TRADE 타입 추가:")
    print("   심볼: KRW-BTC, KRW-ETH")

    # 3. ORDERBOOK 타입 추가
    unified_sub.add_subscription_type("orderbook", ["KRW-BTC"])
    print("3️⃣ ORDERBOOK 타입 추가:")
    print("   심볼: KRW-BTC")

    # 4. CANDLE 타입 추가 (5분봉)
    unified_sub.add_subscription_type("candle", ["KRW-BTC"], **{"unit": "5m"})
    print("4️⃣ CANDLE 타입 추가:")
    print("   심볼: KRW-BTC, 단위: 5분봉")    # 5. 최종 통합 메시지 구조 확인
    message = unified_sub.get_subscription_message()

    print("\n📦 최종 통합 구독 메시지:")
    print(json.dumps(message, indent=2, ensure_ascii=False))

    print("\n✨ 핵심 포인트:")
    print("   - 단일 티켓으로 4가지 타입 동시 구독")
    print("   - 타입별 개별 설정 가능 (심볼, 파라미터)")
    print("   - 업비트가 하나의 연결로 모든 데이터 전송")

    return message


async def demo_realtime_mixed_subscription():
    """실시간 혼합 구독 데모"""
    print("\n🚀 실시간 혼합 구독 데모 시작")
    print("=" * 60)

    client = UpbitWebSocketPublicClient()

    # 메시지 수신 카운터
    message_counters = {
        "ticker": 0,
        "trade": 0,
        "orderbook": 0,
        "candle": 0
    }

    def handle_ticker(message):
        message_counters["ticker"] += 1
        if message_counters["ticker"] <= 3:  # 처음 3개만 출력
            print(f"📊 TICKER: {message.market} - 현재가: {message.data.get('trade_price', 'N/A')}원")

    def handle_trade(message):
        message_counters["trade"] += 1
        if message_counters["trade"] <= 3:
            print(f"💰 TRADE: {message.market} - 체결가: {message.data.get('trade_price', 'N/A')}원")

    def handle_orderbook(message):
        message_counters["orderbook"] += 1
        if message_counters["orderbook"] <= 2:
            orderbook_units = message.data.get('orderbook_units', [{}])
            bid_price = orderbook_units[0].get('bid_price', 'N/A') if orderbook_units else 'N/A'
            print(f"📋 ORDERBOOK: {message.market} - 매수1호가: {bid_price}원")

    def handle_candle(message):
        message_counters["candle"] += 1
        if message_counters["candle"] <= 1:
            print(f"🕐 CANDLE: {message.market} - 종가: {message.data.get('trade_price', 'N/A')}원")

    # 핸들러 등록
    client.add_message_handler(WebSocketDataType.TICKER, handle_ticker)
    client.add_message_handler(WebSocketDataType.TRADE, handle_trade)
    client.add_message_handler(WebSocketDataType.ORDERBOOK, handle_orderbook)
    client.add_message_handler(WebSocketDataType.CANDLE, handle_candle)

    try:
        # 연결
        print("🔗 WebSocket 연결 중...")
        if not await client.connect():
            print("❌ 연결 실패")
            return

        # 혼합 구독 순차 실행 (내부적으로 단일 티켓 사용)
        symbols = ["KRW-BTC", "KRW-ETH"]

        print("\n📡 혼합 구독 시작...")
        print("   ⚠️  내부적으로 모든 타입이 동일한 티켓 사용!")

        # 각 구독이 동일한 티켓에 추가됨
        await client.subscribe_ticker(symbols)
        await client.subscribe_trade(symbols)
        await client.subscribe_orderbook(["KRW-BTC"])  # 호가는 1개만
        await client.subscribe_candle(["KRW-BTC"], "5")  # 5분봉 1개만

        # 티켓 상태 확인
        print("\n🎫 티켓 사용 현황:")
        stats = client.get_ticket_statistics()
        print(f"   활성 티켓 수: {stats['active_tickets']}")
        print(f"   티켓 효율성: {stats['reuse_efficiency']:.1f}%")

        # 구독 정보 확인
        subscriptions = client.get_subscriptions()
        print(f"\n📊 구독된 타입: {len(subscriptions)}개")
        for data_type, info in subscriptions.items():
            symbol_count = len(info.get('symbols', []))
            print(f"   {data_type}: {symbol_count}개 심볼")

        # 10초 동안 메시지 수신
        print("\n⏱️  10초 동안 혼합 메시지 수신 중...")
        await asyncio.sleep(10)

        # 최종 통계
        print("\n📈 수신 메시지 통계:")
        total_messages = sum(message_counters.values())
        for msg_type, count in message_counters.items():
            percentage = (count / total_messages * 100) if total_messages > 0 else 0
            print(f"   {msg_type.upper()}: {count}개 ({percentage:.1f}%)")

        print(f"\n🏆 총 {total_messages}개 메시지를 단일 티켓으로 수신!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        await client.disconnect()
        print("✅ 연결 종료")


async def demo_ticket_optimization_comparison():
    """티켓 최적화 비교 데모"""
    print("\n🔄 티켓 최적화 비교 분석")
    print("=" * 60)

    # 기존 방식 시뮬레이션 (개별 티켓)
    print("📊 기존 방식 (개별 티켓):")
    traditional_tickets = {
        "ticker_ticket_001": ["ticker"],
        "trade_ticket_002": ["trade"],
        "orderbook_ticket_003": ["orderbook"],
        "candle_ticket_004": ["candle"]
    }

    for ticket, types in traditional_tickets.items():
        print(f"   {ticket}: {types[0]} 전용")

    print(f"   총 필요 티켓: {len(traditional_tickets)}개")

    # 통합 방식 시뮬레이션
    print("\n🚀 통합 방식 (단일 티켓):")
    unified_ticket = {
        "unified_ticket_001": ["ticker", "trade", "orderbook", "candle"]
    }

    for ticket, types in unified_ticket.items():
        print(f"   {ticket}: {', '.join(types)} 통합")

    print(f"   총 필요 티켓: {len(unified_ticket)}개")

    # 효율성 계산
    efficiency = ((len(traditional_tickets) - len(unified_ticket)) / len(traditional_tickets)) * 100
    print(f"\n⚡ 효율성 개선: {efficiency:.0f}% 절약!")
    print(f"   절약된 티켓: {len(traditional_tickets) - len(unified_ticket)}개")

    # 업비트 제한과 비교
    upbit_limit = 5
    print(f"\n📏 업비트 제한 ({upbit_limit}티켓) 대비:")
    traditional_usage = (len(traditional_tickets) / upbit_limit) * 100
    unified_usage = (len(unified_ticket) / upbit_limit) * 100

    print(f"   기존 방식: {traditional_usage:.0f}% 사용")
    print(f"   통합 방식: {unified_usage:.0f}% 사용")
    remaining_tickets = upbit_limit - len(unified_ticket)
    remaining_percentage = (remaining_tickets / upbit_limit) * 100
    print(f"   여유 공간: {remaining_tickets}티켓 ({remaining_percentage:.0f}%)")


def analyze_subscription_message_details():
    """구독 메시지 상세 분석"""
    print("\n🔬 혼합 구독 메시지 상세 분석")
    print("=" * 60)

    # 실제 업비트 WebSocket 메시지 구조 재현
    ticket = "analysis-demo"
    unified_sub = UnifiedSubscription(ticket)

    # 복잡한 혼합 구독 구성
    unified_sub.add_subscription_type("ticker", ["KRW-BTC", "KRW-ETH", "KRW-XRP"])
    unified_sub.add_subscription_type("trade", ["KRW-BTC", "KRW-ETH"])
    unified_sub.add_subscription_type("orderbook", ["KRW-BTC"])
    unified_sub.add_subscription_type("candle", ["KRW-BTC"], unit="1m")

    message = unified_sub.get_subscription_message()

    print("📋 메시지 구성 요소:")
    for i, part in enumerate(message):
        print(f"   {i + 1}. {json.dumps(part, ensure_ascii=False)}")

        if "ticket" in part:
            print("      → 티켓 식별자")
        elif "type" in part:
            data_type = part["type"]
            codes = part.get("codes", [])
            print(f"      → {data_type.upper()} 타입, {len(codes)}개 심볼")
            if "unit" in part:
                print(f"      → 추가 파라미터: unit={part['unit']}")
        elif "format" in part:
            print("      → 응답 형식 지정")

    print("\n📊 구독 통계:")
    print(f"   총 타입 수: {len(unified_sub.types)}")
    print(f"   총 심볼 수: {len(unified_sub.symbols)}")
    print(f"   메시지 크기: {len(json.dumps(message))} bytes")

    # 각 타입별 상세 정보
    print("\n📈 타입별 상세:")
    for data_type, config in unified_sub.types.items():
        symbols = config.get("codes", [])
        extra_params = {k: v for k, v in config.items() if k != "codes"}
        print(f"   {data_type.upper()}:")
        print(f"     심볼: {', '.join(symbols)}")
        if extra_params:
            print(f"     파라미터: {extra_params}")


async def main():
    """메인 데모 실행"""
    print("🎯 여러 타입 섞인 WebSocket 구독 요청 처리 데모")
    print("=" * 70)

    # 1. 메시지 구조 분석
    show_mixed_subscription_message_structure()

    # 2. 상세 분석
    analyze_subscription_message_details()

    # 3. 티켓 최적화 비교
    await demo_ticket_optimization_comparison()

    # 4. 실시간 테스트 자동 실행
    print("\n🚀 실시간 혼합 구독 테스트 자동 실행")
    await demo_realtime_mixed_subscription()

    print("\n🎉 모든 데모 완료!")
    print("\n💡 핵심 요약:")
    print("   ✅ 하나의 티켓으로 여러 타입 동시 구독 가능")
    print("   ✅ 각 타입마다 개별 심볼 및 파라미터 설정 가능")
    print("   ✅ 75% 티켓 효율성 향상")
    print("   ✅ 업비트 5티켓 제한 내에서 최대 활용")


if __name__ == "__main__":
    asyncio.run(main())
