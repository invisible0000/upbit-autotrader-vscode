"""
빠른 단일 연결 테스트
"""

import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.upbit_websocket_public_client import (  # noqa: E402
    UpbitWebSocketPublicV5
)


async def quick_test():
    """빠른 테스트"""
    print("🚀 빠른 연결 즉시 티커 요청 테스트 (강화된 디버깅)")

    received_data = None
    callback_called = False
    raw_messages = []

    def ticker_callback(data):
        nonlocal received_data, callback_called
        callback_called = True
        received_data = data
        print(f"🔔 콜백 호출됨! 데이터 타입: {type(data)}")

        if hasattr(data, 'payload') and data.payload:
            price = data.payload.get('trade_price', 'N/A')
            symbol = data.payload.get('code', 'N/A')
            print(f"   📊 티커 수신: {symbol} = {price:,}원")
        elif isinstance(data, dict):
            price = data.get('trade_price', data.get('tp', 'N/A'))
            symbol = data.get('code', data.get('cd', 'KRW-BTC'))
            print(f"   📊 딕셔너리 데이터: {symbol} = {price}원")
        else:
            print(f"   📊 원시 데이터: {data}")

    client = None
    try:
        # 1. 연결
        start_time = time.perf_counter()
        client = UpbitWebSocketPublicV5(max_tickets=3)  # 티켓 수 증가

        # 메시지 후킹으로 실제 수신 확인
        original_process_message = client._process_message

        async def debug_process_message(raw_message):
            print(f"📨 원시 메시지 수신: {raw_message[:100]}...")
            raw_messages.append(raw_message)
            return await original_process_message(raw_message)

        client._process_message = debug_process_message

        connect_start = time.perf_counter()
        await client.connect()
        connect_end = time.perf_counter()
        print(f"   ✅ 연결 완료: {connect_end - connect_start:.3f}초")

        # 2. 즉시 구독
        subscribe_start = time.perf_counter()
        subscription_id = await client.subscribe_ticker(
            ["KRW-BTC"],
            callback=ticker_callback,
            is_only_snapshot=True
        )
        subscribe_end = time.perf_counter()
        print(f"   ✅ 구독 완료: {subscribe_end - subscribe_start:.3f}초")
        print(f"   📋 구독 ID: {subscription_id}")

        # 3. 응답 대기 (더 자세한 모니터링)
        response_start = time.perf_counter()
        for i in range(100):  # 10초 대기
            if received_data:
                break
            if i % 10 == 0:  # 1초마다 상태 출력
                print(f"   ⏳ 대기 중... {i/10:.0f}초 (메시지:{len(raw_messages)}, 콜백:{callback_called})")
            await asyncio.sleep(0.1)

        response_end = time.perf_counter()

        # 결과 분석
        print(f"\n📊 결과 분석:")
        print(f"   원시 메시지 수신: {len(raw_messages)}개")
        print(f"   콜백 호출 여부: {callback_called}")
        print(f"   데이터 수신 여부: {received_data is not None}")

        if raw_messages:
            print(f"   첫 번째 메시지: {raw_messages[0][:200]}...")

        if received_data:
            print(f"   ✅ 응답 수신: {response_end - response_start:.3f}초")
            total_time = response_end - start_time
            print(f"   🏆 총 소요시간: {total_time:.3f}초")
            print("   💡 연결 즉시 데이터 요청 성공!")
        else:
            print("   ❌ 응답 타임아웃")
            if raw_messages:
                print("   ⚠️ 메시지는 수신되었지만 콜백 처리 실패")
            else:
                print("   ⚠️ 메시지 자체가 수신되지 않음")

    except Exception as e:
        print(f"   ❌ 오류: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass


if __name__ == "__main__":
    os.environ["UPBIT_CONSOLE_OUTPUT"] = "false"  # 로그 최소화
    asyncio.run(quick_test())
