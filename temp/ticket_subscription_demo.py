"""
구독-티켓 관계 데모
"""
import asyncio
import sys
import os

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.subscription_manager import (
    SubscriptionManager, DataRequest, Subscription, TicketPoolType
)

async def demo_ticket_subscription_relationship():
    manager = SubscriptionManager(public_pool_size=3, private_pool_size=2)

    print('🎯 구독-티켓 관계 데모')
    print('=' * 50)

    # 1. 여러 구독이 하나의 기본 티켓 공유
    print('📋 1단계: 기본 티켓으로 여러 구독 생성')

    # 기본 티켓 생성
    default_ticket = manager.ticket_manager.get_default_ticket(TicketPoolType.PUBLIC)
    print(f'  기본 Public 티켓: {default_ticket}')

    # 구독 객체들 생성 (실제 WebSocket 전송 없이)
    sub1 = Subscription('sub_0001_test1', default_ticket, TicketPoolType.PUBLIC)
    sub1.add_request(DataRequest('ticker', ['KRW-BTC']))

    sub2 = Subscription('sub_0002_test2', default_ticket, TicketPoolType.PUBLIC)
    sub2.add_request(DataRequest('trade', ['KRW-ETH']))

    sub3 = Subscription('sub_0003_test3', default_ticket, TicketPoolType.PUBLIC)
    sub3.add_request(DataRequest('orderbook', ['KRW-XRP']))

    print(f'  구독 1: {sub1.subscription_id} → 티켓: {sub1.ticket_id} (BTC 현재가)')
    print(f'  구독 2: {sub2.subscription_id} → 티켓: {sub2.ticket_id} (ETH 체결)')
    print(f'  구독 3: {sub3.subscription_id} → 티켓: {sub3.ticket_id} (XRP 호가)')
    print(f'  ✅ 구독 3개가 모두 같은 티켓 {default_ticket} 공유!')

    print()
    print('📋 2단계: 전용 티켓으로 분리')

    # 전용 티켓 생성
    trading_ticket = manager.ticket_manager.create_dedicated_ticket(TicketPoolType.PUBLIC, 'high_priority')
    print(f'  전용 트레이딩 티켓: {trading_ticket}')

    # 전용 티켓 사용 구독
    premium_sub = Subscription('sub_0004_premium', trading_ticket, TicketPoolType.PUBLIC)
    premium_sub.add_request(DataRequest('trade', ['KRW-BTC']))

    print(f'  프리미엄 구독: {premium_sub.subscription_id} → 전용 티켓: {premium_sub.ticket_id}')
    print(f'  ✅ 중요한 트레이딩은 전용 티켓으로 격리!')

    print()
    print('📊 3단계: 티켓 사용률 분석')
    stats = manager.ticket_manager.get_stats()
    public_util = stats["public_pool"]["utilization_percent"]
    total_tickets = stats["total_tickets"]
    max_tickets = stats["max_total_tickets"]

    print(f'  Public 티켓 사용률: {public_util:.1f}%')
    print(f'  전체 티켓 수: {total_tickets}/{max_tickets}')

    available_tickets = manager.ticket_manager.get_available_tickets()
    public_count = len(available_tickets["public"])
    print(f'  사용 가능한 Public 티켓: {public_count}개')

    for ticket_id, info in available_tickets["public"].items():
        purpose = info["purpose"]
        request_count = info["request_count"]
        print(f'    - {ticket_id}: {purpose} (요청 {request_count}개)')

    print()
    print('� 4단계: 가상 구독의 비동기 메시지 집합 시뮬레이션')

    # 가상의 메시지 스트림 시뮬레이션
    incoming_messages = [
        {"type": "ticker", "code": "KRW-BTC", "trade_price": 95000000, "stream_ticket": default_ticket},
        {"type": "trade", "code": "KRW-ETH", "trade_price": 4200000, "stream_ticket": default_ticket},
        {"type": "orderbook", "code": "KRW-XRP", "total_ask_size": 1000, "stream_ticket": default_ticket},
        {"type": "trade", "code": "KRW-BTC", "trade_price": 95100000, "stream_ticket": trading_ticket},
        {"type": "ticker", "code": "KRW-BTC", "trade_price": 95050000, "stream_ticket": default_ticket},
    ]

    print(f'  🌊 물리적 스트림: {len(set(msg["stream_ticket"] for msg in incoming_messages))}개 티켓')
    print(f'  📦 논리적 집합: {len([sub1, sub2, sub3, premium_sub])}개 가상 구독')
    print()
    print('  메시지 라우팅 시뮬레이션:')

    # 각 구독이 어떤 메시지를 받을지 시뮬레이션
    all_subscriptions = [
        (sub1, "BTC 현재가 모니터링"),
        (sub2, "ETH 체결 분석"),
        (sub3, "XRP 호가 추적"),
        (premium_sub, "BTC 고성능 트레이딩")
    ]

    for i, message in enumerate(incoming_messages, 1):
        print(f'    메시지 {i}: {message["type"]} {message["code"]} (티켓: {message["stream_ticket"][-6:]})')

        # 각 구독이 이 메시지를 처리할지 확인
        for subscription, purpose in all_subscriptions:
            would_handle = subscription.handles_message(message["type"], message["code"])
            if would_handle:
                print(f'      ↳ 🎯 {subscription.subscription_id} ({purpose}) 처리!')

    print()
    print('💡 가상 구독 = 제한 극복 + 비동기 메시지 집합의 핵심:')
    print('   ┌─ 물리적 제약: 업비트 WebSocket 연결 최대 5개')
    print('   ├─ 가상화 계층: 구독 = 논리적 메시지 필터 + 콜백 집합')
    print('   ├─ 비동기 라우팅: 하나의 스트림 → 여러 구독으로 분배')
    print('   └─ 무제한 확장: 5개 티켓으로 수백개 구독 처리 가능!')
    print()
    print('🏗️ 아키텍처 비유:')
    print('   티켓 = 아파트 단지의 수도관 (물리적 인프라)')
    print('   구독 = 각 세대의 수도꼭지 (논리적 사용 지점)')
    print('   메시지 = 흐르는 물 (데이터 스트림)')
    print('   → 하나의 수도관으로 모든 세대에 물 공급! 💧')

if __name__ == "__main__":
    asyncio.run(demo_ticket_subscription_relationship())
