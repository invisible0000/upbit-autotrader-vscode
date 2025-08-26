"""
통합 티켓 관리 시스템 데모
전체 시스템이 티켓 관리를 쉽게 활용하는 방법 시연
"""

import asyncio

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_public_client import UpbitWebSocketPublicClient
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.websocket_subscription_manager import (
    WebSocketSubscriptionManager, SubscriptionType
)


async def demo_unified_ticket_management():
    """통합 티켓 관리 시스템 데모"""

    # 1. 기본 WebSocket 클라이언트 생성 (티켓 관리 허브)
    print("🚀 통합 티켓 관리 시스템 초기화...")
    client = UpbitWebSocketPublicClient()

    # 2. 상위 구독 매니저 생성 (단순화된 인터페이스)
    manager = WebSocketSubscriptionManager(
        websocket_client=client,
        max_subscription_types=4
    )

    # 3. 연결
    print("🔗 WebSocket 연결 중...")
    if not await client.connect():
        print("❌ 연결 실패")
        return

    # 4. 다양한 구독 시나리오 테스트
    print("\n🎯 시나리오 1: 기본 구독 (자동 티켓 관리)")

    # 티켓을 신경 쓰지 않고 단순 구독
    symbols_batch1 = ["KRW-BTC", "KRW-ETH", "KRW-ADA"]

    # TICKER 구독 (내부적으로 티켓 1개 사용)
    success1 = await manager.subscribe_symbols(symbols_batch1, SubscriptionType.TICKER)
    print(f"✅ TICKER 구독: {success1}")

    # TRADE 구독 (기존 티켓에 타입 추가 또는 새 티켓)
    success2 = await manager.subscribe_symbols(symbols_batch1, SubscriptionType.TRADE)
    print(f"✅ TRADE 구독: {success2}")

    # ORDERBOOK 구독 (통합 구독 효율성 극대화)
    success3 = await manager.subscribe_symbols(symbols_batch1, SubscriptionType.ORDERBOOK)
    print(f"✅ ORDERBOOK 구독: {success3}")

    # 5. 티켓 상태 확인
    print("\n📊 티켓 사용 현황:")
    ticket_stats = client.get_ticket_statistics()
    print(f"   총 티켓 수: {ticket_stats['total_tickets']}")
    print(f"   활성 티켓: {ticket_stats['active_tickets']}")
    print(f"   재사용 효율: {ticket_stats['reuse_efficiency']:.1f}%")

    # 구독 정보도 확인
    subscriptions = client.get_subscriptions()
    print(f"   구독 타입 수: {len(subscriptions)}개")

    # 6. 대량 구독 테스트 (티켓 한계 테스트)
    print("\n🎯 시나리오 2: 대량 구독 (5-티켓 한계 자동 관리)")

    # 많은 심볼로 다양한 타입 구독
    large_symbols = [f"KRW-{coin}" for coin in ["BTC", "ETH", "XRP", "ADA", "DOT", "LINK", "LTC", "BCH", "EOS", "TRX"]]

    # 캔들 구독 (새로운 타입)
    success4 = await manager.subscribe_symbols(large_symbols, SubscriptionType.CANDLE)
    print(f"✅ CANDLE 구독 (10개 심볼): {success4}")

    # 7. 최종 티켓 효율성 확인
    print("\n🏆 최종 티켓 효율성 보고:")
    final_stats = client.get_ticket_statistics()
    final_subscriptions = client.get_subscriptions()

    active_tickets = max(final_stats['active_tickets'], 1)  # 0으로 나누기 방지

    print(f"   사용된 티켓: {final_stats['active_tickets']}/5 (최대)")
    print("   구독된 타입: 4개 (TICKER, TRADE, ORDERBOOK, CANDLE)")
    print(f"   총 구독 심볼: {len(large_symbols)}개")
    print(f"   티켓당 평균 타입: {len(final_subscriptions) / active_tickets:.1f}개")

    # 계산된 효율성
    traditional_tickets = 4  # 각 타입마다 1티켓씩
    unified_tickets = max(final_stats['active_tickets'], 1)
    efficiency = ((traditional_tickets - unified_tickets) / traditional_tickets) * 100

    print("\n⚡ 효율성 개선:")
    print(f"   기존 방식: {traditional_tickets}티켓 필요")
    print(f"   통합 방식: {unified_tickets}티켓 사용")
    print(f"   개선율: {efficiency:.1f}% 절약!")

    # 실제 WebSocket 메시지 확인
    print("\n📈 실제 구독 상태:")
    for data_type, sub_info in final_subscriptions.items():
        symbol_count = len(sub_info.get('symbols', []))
        print(f"   {data_type}: {symbol_count}개 심볼")    # 8. 실시간 데이터 수신 테스트 (짧은 시간)
    print("\n📡 실시간 데이터 수신 테스트 (5초)...")

    # 간단한 메시지 카운터
    message_count = 0

    def count_messages(message):
        nonlocal message_count
        message_count += 1

    # 메시지 핸들러 등록
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_public_client import WebSocketDataType
    client.add_message_handler(WebSocketDataType.TICKER, count_messages)

    # 5초 대기
    await asyncio.sleep(5)

    print(f"✅ 5초간 수신된 메시지: {message_count}개")
    print(f"   초당 평균: {message_count / 5:.1f}msg/s")    # 9. 정리
    print("\n🧹 연결 정리 중...")
    await client.disconnect()
    print("✅ 데모 완료!")


async def demo_smart_router_integration():
    """Smart Router와의 통합 시연"""
    print("\n🔗 Smart Router 통합 데모")

    # Smart Router는 내부적으로 통합 티켓 시스템을 활용
    # 개발자는 변경 사항을 인지할 필요 없음

    client = UpbitWebSocketPublicClient()
    manager = WebSocketSubscriptionManager(client)

    await client.connect()

    # Smart Router 스타일 배치 구독
    symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]

    print("📦 배치 구독 요청...")
    success = await manager.request_batch_subscription(
        symbols=symbols,
        subscription_type=SubscriptionType.TICKER,
        priority=5  # 무시됨 (기본 API가 관리)
    )

    print(f"✅ 배치 구독 성공: {success}")

    # 구독 처리 가능 여부 확인
    can_handle = manager.can_handle_subscription(
        symbols=["KRW-DOT", "KRW-LINK"],
        subscription_type=SubscriptionType.TRADE
    )
    print(f"📋 추가 구독 가능: {can_handle}")

    # 현재 구독 통계
    current_count = manager.get_current_subscription_count()
    max_count = manager.get_max_subscription_count()
    print(f"📊 구독 현황: {current_count}/{max_count} 타입")

    await client.disconnect()
    print("✅ Smart Router 통합 데모 완료")


if __name__ == "__main__":
    print("🎯 업비트 통합 티켓 관리 시스템 데모")
    print("=" * 50)

    # 메인 데모 실행
    asyncio.run(demo_unified_ticket_management())

    # Smart Router 통합 데모
    asyncio.run(demo_smart_router_integration())

    print("\n🏆 모든 데모 완료!")
    print("   전체 시스템이 티켓 관리를 쉽고 효율적으로 활용할 수 있습니다.")
