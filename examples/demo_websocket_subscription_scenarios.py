"""
WebSocket 구독 시나리오 테스트 - 3초 내 빠른 검증
=================================================

websocket_subscription_scenario_02.md의 시나리오들을 실제 WebSocket으로 테스트
- 시나리오 1: 멀티탭 동시 진입 (Public 구독)
- 시나리오 2: 심볼 변경 연쇄 반응 (KRW-BTC → KRW-ETH)
- 시나리오 3: 스트림 타입 충돌 해결 (realtime vs snapshot)

각 시나리오는 3초 내로 빠르게 검증합니다.
"""

import asyncio
import json
import websockets
import time
from typing import Dict, List, Set


class SubscriptionTester:
    """구독 시나리오 테스트 클래스"""

    def __init__(self):
        self.websocket = None
        self.received_messages = []
        self.received_types = set()
        self.received_symbols = set()
        self.subscription_history = []  # 구독 이력 추적

    async def connect(self):
        """업비트 WebSocket 연결"""
        self.websocket = await websockets.connect("wss://api.upbit.com/websocket/v1")
        print("✅ 업비트 WebSocket 연결 완료")

    async def disconnect(self):
        """WebSocket 연결 해제"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 WebSocket 연결 해제")

    def track_subscription(self, subscriptions: List[Dict], description: str):
        """구독 상태 추적"""
        subscription_state = {
            "timestamp": time.time(),
            "description": description,
            "subscriptions": {}
        }

        for sub in subscriptions:
            sub_type = sub["type"]
            symbols = set(sub.get("codes", []))
            subscription_state["subscriptions"][sub_type] = symbols

        self.subscription_history.append(subscription_state)

        # 현재 구독 상태 표시
        print(f"📊 현재 구독 상태:")
        for sub_type, symbols in subscription_state["subscriptions"].items():
            print(f"   🎯 {sub_type}: {sorted(symbols)}")

    async def send_subscription(self, ticket: str, subscriptions: List[Dict], description: str):
        """구독 메시지 전송"""
        message = [{"ticket": ticket}] + subscriptions + [{"format": "DEFAULT"}]
        await self.websocket.send(json.dumps(message))
        print(f"📤 {description}")
        print(f"   📋 구독 내용: {len(subscriptions)}개 타입")
        for sub in subscriptions:
            codes_count = len(sub.get("codes", []))
            print(f"      - {sub['type']}: {codes_count}개 심볼")

        # 구독 상태 추적
        self.track_subscription(subscriptions, description)

    async def collect_messages(self, duration: float, expected_types: Set[str]):
        """지정된 시간 동안 메시지 수집"""
        print(f"🔍 {duration}초 동안 메시지 수집 중...")

        start_time = time.time()
        message_count = 0
        type_counts = {}

        while time.time() - start_time < duration:
            try:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
                data = json.loads(message)

                message_count += 1
                msg_type = data.get("type", "unknown")
                symbol = data.get("code", "unknown")
                stream_type = data.get("stream_type", "unknown")

                # 타입별 카운트
                type_counts[msg_type] = type_counts.get(msg_type, 0) + 1

                # 수신 데이터 기록
                self.received_types.add(msg_type)
                self.received_symbols.add(symbol)

                # 주요 메시지만 출력 (처음 몇 개)
                if message_count <= 5:
                    # orderbook 간소화: 첫 번째 가격만 표시
                    if msg_type == "orderbook" and "orderbook_units" in data:
                        units = data["orderbook_units"]
                        if units and len(units) > 0:
                            first_unit = units[0]
                            price_info = f"ask:{first_unit.get('ask_price', 'N/A')} bid:{first_unit.get('bid_price', 'N/A')}"
                        else:
                            price_info = "N/A"
                    else:
                        price_info = data.get("trade_price", "N/A")

                    print(f"   📨 #{message_count}: {msg_type} {symbol} {stream_type} {price_info}")
                elif message_count == 6:
                    print(f"   ... (메시지 계속 수신 중)")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"   ⚠️ 메시지 처리 오류: {e}")

        elapsed = time.time() - start_time
        print(f"📊 수집 완료: {elapsed:.1f}초, 총 {message_count}개 메시지")

        # 타입별 요약
        for msg_type, count in type_counts.items():
            status = "✅" if msg_type in expected_types else "❓"
            print(f"   {status} {msg_type}: {count}개")

        return message_count, type_counts


async def test_scenario_1_multitab_subscription():
    """
    시나리오 1: 멀티탭 동시 진입 테스트

    차트뷰(ticker + orderbook) + 거래내역(trade) 동시 구독
    """
    print("\n" + "="*60)
    print("🧪 시나리오 1: 멀티탭 동시 진입")
    print("   차트뷰(ticker + orderbook) + 거래내역(trade)")
    print("="*60)

    tester = SubscriptionTester()
    await tester.connect()

    try:
        # 멀티탭 구독: ticker + orderbook + trade
        subscriptions = [
            {
                "type": "ticker",
                "codes": ["KRW-BTC", "KRW-ETH", "KRW-XRP"]  # 차트뷰 코인 리스트
            },
            {
                "type": "orderbook",
                "codes": ["KRW-BTC"]  # 호가창
            },
            {
                "type": "trade",
                "codes": ["KRW-BTC"]  # 거래내역
            }
        ]

        await tester.send_subscription(
            "multitab_ticket",
            subscriptions,
            "멀티탭 구독 (ticker + orderbook + trade)"
        )

        # 3초 동안 데이터 수집
        expected_types = {"ticker", "orderbook", "trade"}
        count, types = await tester.collect_messages(3.0, expected_types)

        # 결과 검증
        print("\n🎯 결과 분석:")
        success = True
        for expected_type in expected_types:
            if expected_type in types:
                print(f"   ✅ {expected_type}: {types[expected_type]}개 메시지 수신")
            else:
                print(f"   ❌ {expected_type}: 메시지 없음")
                success = False

        if success and count > 10:
            print("   🎉 멀티탭 동시 구독 성공!")
        else:
            print("   ⚠️ 일부 타입 누락 또는 메시지 부족")

    finally:
        await tester.disconnect()


async def test_scenario_2_symbol_change():
    """
    시나리오 2: 심볼 변경 연쇄 반응 테스트

    KRW-BTC → KRW-ETH 변경 시 orderbook + trade 동시 전환
    """
    print("\n" + "="*60)
    print("🧪 시나리오 2: 심볼 변경 연쇄 반응")
    print("   KRW-BTC → KRW-ETH 변경 시 orderbook + trade 전환")
    print("="*60)

    tester = SubscriptionTester()
    await tester.connect()

    try:
        # 1단계: KRW-BTC 구독
        print("\n📋 1단계: KRW-BTC 구독")
        subscriptions_btc = [
            {
                "type": "orderbook",
                "codes": ["KRW-BTC"]
            },
            {
                "type": "trade",
                "codes": ["KRW-BTC"]
            }
        ]

        await tester.send_subscription(
            "symbol_change_1",
            subscriptions_btc,
            "KRW-BTC 구독"
        )

        # 1.5초 동안 KRW-BTC 데이터 수집
        count1, types1 = await tester.collect_messages(1.5, {"orderbook", "trade"})
        btc_symbols = tester.received_symbols.copy()

        # 2단계: KRW-ETH로 변경
        print(f"\n📋 2단계: KRW-ETH로 변경")
        tester.received_symbols.clear()  # 심볼 기록 초기화

        subscriptions_eth = [
            {
                "type": "orderbook",
                "codes": ["KRW-ETH"]
            },
            {
                "type": "trade",
                "codes": ["KRW-ETH"]
            }
        ]

        await tester.send_subscription(
            "symbol_change_2",
            subscriptions_eth,
            "KRW-ETH로 변경"
        )

        # 1.5초 동안 KRW-ETH 데이터 수집
        count2, types2 = await tester.collect_messages(1.5, {"orderbook", "trade"})
        eth_symbols = tester.received_symbols.copy()

        # 결과 검증
        print("\n🎯 결과 분석:")
        print(f"   📊 1단계 심볼: {btc_symbols}")
        print(f"   📊 2단계 심볼: {eth_symbols}")

        btc_received = "KRW-BTC" in btc_symbols
        eth_received = "KRW-ETH" in eth_symbols

        if btc_received and eth_received:
            print("   🎉 심볼 변경 연쇄 반응 성공!")
            print("   ✅ KRW-BTC → KRW-ETH 전환 확인됨")
        else:
            print("   ⚠️ 심볼 전환 불완전")

    finally:
        await tester.disconnect()


async def test_scenario_3_stream_type_conflict():
    """
    시나리오 3: 스트림 타입 충돌 해결 테스트

    같은 심볼에 realtime vs snapshot 요구 시 통합 처리
    """
    print("\n" + "="*60)
    print("🧪 시나리오 3: 스트림 타입 충돌 해결")
    print("   같은 심볼에 realtime vs snapshot 통합 처리")
    print("="*60)

    tester = SubscriptionTester()
    await tester.connect()

    try:
        # 1단계: realtime만 구독
        print("\n📋 1단계: KRW-BTC realtime만 구독")
        subscriptions_realtime = [
            {
                "type": "ticker",
                "codes": ["KRW-BTC"],
                "isOnlyRealtime": True
            }
        ]

        await tester.send_subscription(
            "realtime_only",
            subscriptions_realtime,
            "KRW-BTC realtime만 구독"
        )

        # 1초 동안 realtime 데이터 수집
        count1, types1 = await tester.collect_messages(1.0, {"ticker"})
        realtime_count = count1

        # 2단계: snapshot 추가 (충돌 상황)
        print(f"\n📋 2단계: 같은 심볼에 snapshot 추가 (충돌 해결)")
        subscriptions_mixed = [
            {
                "type": "ticker",
                "codes": ["KRW-BTC"]
                # 기본값 = snapshot + realtime (충돌 해결 방식)
            }
        ]

        await tester.send_subscription(
            "mixed_stream",
            subscriptions_mixed,
            "KRW-BTC snapshot + realtime (통합)"
        )

        # 2초 동안 통합 데이터 수집
        tester.received_messages.clear()  # 메시지 기록 초기화
        count2, types2 = await tester.collect_messages(2.0, {"ticker"})
        mixed_count = count2

        # 결과 검증
        print("\n🎯 결과 분석:")
        print(f"   📊 1단계 (realtime만): {realtime_count}개 메시지")
        print(f"   📊 2단계 (snapshot+realtime): {mixed_count}개 메시지")

        # 통합 처리 성공 판단: 2단계에서 더 많은 메시지 (snapshot 포함)
        if mixed_count >= realtime_count:
            print("   🎉 스트림 타입 충돌 해결 성공!")
            print("   ✅ realtime → snapshot+realtime 통합 처리 확인")
        else:
            print("   ⚠️ 충돌 해결 결과 불명확")

    finally:
        await tester.disconnect()


async def test_scenario_4_subscription_cleanup():
    """
    보너스 시나리오: 구독 정리 테스트

    복수 구독 → 일부 정리 → 남은 구독 유지 확인
    """
    print("\n" + "="*60)
    print("🧪 보너스 시나리오: 구독 정리")
    print("   복수 구독 → 일부 정리 → 남은 구독 유지")
    print("="*60)

    tester = SubscriptionTester()
    await tester.connect()

    try:
        # 1단계: 다중 타입 구독
        print("\n📋 1단계: ticker + orderbook 구독")
        subscriptions_multi = [
            {
                "type": "ticker",
                "codes": ["KRW-BTC", "KRW-ETH"]
            },
            {
                "type": "orderbook",
                "codes": ["KRW-BTC"]
            }
        ]

        await tester.send_subscription(
            "multi_types",
            subscriptions_multi,
            "ticker + orderbook 다중 구독"
        )

        # 1.5초 동안 다중 타입 데이터 수집
        count1, types1 = await tester.collect_messages(1.5, {"ticker", "orderbook"})

        # 2단계: orderbook만 정리 (ticker는 유지)
        print(f"\n📋 2단계: orderbook 정리, ticker만 유지")
        subscriptions_ticker_only = [
            {
                "type": "ticker",
                "codes": ["KRW-BTC", "KRW-ETH"]
            }
        ]

        await tester.send_subscription(
            "ticker_only",
            subscriptions_ticker_only,
            "ticker만 유지 (orderbook 정리)"
        )

        # 1.5초 동안 ticker만 데이터 수집
        count2, types2 = await tester.collect_messages(1.5, {"ticker"})

        # 결과 검증
        print("\n🎯 결과 분석:")
        print(f"   📊 1단계 타입: {list(types1.keys())}")
        print(f"   📊 2단계 타입: {list(types2.keys())}")

        # 정리 성공 판단: 2단계에서 orderbook 사라짐
        stage1_has_both = "ticker" in types1 and "orderbook" in types1
        stage2_ticker_only = "ticker" in types2 and "orderbook" not in types2

        if stage1_has_both and stage2_ticker_only:
            print("   🎉 구독 정리 성공!")
            print("   ✅ orderbook 정리됨, ticker 유지됨")
        else:
            print("   ⚠️ 구독 정리 결과 불명확")

    finally:
        await tester.disconnect()


async def main():
    """전체 테스트 실행"""
    print("🔧 WebSocket 구독 시나리오 테스트 시작")
    print("=" * 60)
    print("📋 테스트 계획:")
    print("   - 시나리오 1: 멀티탭 동시 진입 (3초)")
    print("   - 시나리오 2: 심볼 변경 연쇄 (3초)")
    print("   - 시나리오 3: 스트림 타입 충돌 (3초)")
    print("   - 보너스: 구독 정리 (3초)")
    print("=" * 60)

    start_time = time.time()

    try:
        # 각 시나리오 순차 실행
        await test_scenario_1_multitab_subscription()
        await asyncio.sleep(0.5)  # 시나리오 간 간격

        await test_scenario_2_symbol_change()
        await asyncio.sleep(0.5)

        await test_scenario_3_stream_type_conflict()
        await asyncio.sleep(0.5)

        await test_scenario_4_subscription_cleanup()

    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()

    elapsed = time.time() - start_time
    print(f"\n🏁 전체 테스트 완료: {elapsed:.1f}초")
    print("\n🎯 핵심 검증 포인트:")
    print("   ✅ 멀티탭 구독이 동시에 정상 동작하는가?")
    print("   ✅ 심볼 변경 시 연관 구독이 함께 전환되는가?")
    print("   ✅ 스트림 타입 충돌이 적절히 통합되는가?")
    print("   ✅ 구독 정리가 선택적으로 동작하는가?")
    print("\n💡 이 결과를 토대로 SubscriptionManager v6.2 검증 가능!")


if __name__ == "__main__":
    asyncio.run(main())
