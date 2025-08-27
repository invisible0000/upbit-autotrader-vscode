#!/usr/bin/env python3
"""
간단한 업비트 WebSocket 구독 해제 테스트
"""

import asyncio
import websockets
import json


async def simple_test():
    """간단한 구독 해제 테스트"""
    uri = "wss://api.upbit.com/websocket/v1"

    print(f"🔌 연결 시도: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ 연결 성공!")

            # 1. 구독
            subscribe_msg = [
                {"ticket": "test123"},
                {"type": "ticker", "codes": ["KRW-BTC"]},
                {"format": "DEFAULT"}
            ]
            print(f"📤 구독: {json.dumps(subscribe_msg)}")
            await websocket.send(json.dumps(subscribe_msg))

            # 2. 잠시 메시지 수신
            print("📥 3초간 메시지 수신...")
            count = 0
            start = asyncio.get_event_loop().time()

            while asyncio.get_event_loop().time() - start < 3:
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    count += 1
                    if count <= 2:
                        data = json.loads(msg)
                        print(f"  수신 {count}: {data.get('code', 'N/A')}")
                except asyncio.TimeoutError:
                    continue

            print(f"📊 3초간 {count}개 메시지 수신")

            # 3. 구독 해제 (빈 codes)
            unsubscribe_msg = [
                {"ticket": "test123"},
                {"type": "ticker", "codes": []},
                {"format": "DEFAULT"}
            ]
            print(f"📤 구독해제: {json.dumps(unsubscribe_msg)}")

            try:
                await websocket.send(json.dumps(unsubscribe_msg))
                print("✅ 구독해제 메시지 전송 완료")

                # 4. 해제 후 메시지 확인 (2초)
                print("📥 해제 후 2초간 메시지 확인...")
                after_count = 0
                start = asyncio.get_event_loop().time()

                while asyncio.get_event_loop().time() - start < 2:
                    try:
                        msg = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                        after_count += 1
                        if after_count <= 2:
                            data = json.loads(msg)
                            print(f"  해제후 {after_count}: {data.get('code', 'N/A')}")
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed as e:
                        print(f"🔌 연결 종료됨: {e}")
                        break

                print(f"📊 해제 후 {after_count}개 메시지 수신")

                if after_count == 0:
                    print("✅ 구독 해제 성공 - 메시지 차단됨")
                else:
                    print("❌ 구독 해제 실패 - 메시지 계속 수신")

            except websockets.exceptions.ConnectionClosed as e:
                print(f"🔌 구독 해제 요청 후 연결이 즉시 종료됨: {e}")
                print("✅ 업비트 서버가 빈 구독 요청으로 연결을 종료함")

    except Exception as e:
        print(f"❌ 오류: {e}")


if __name__ == "__main__":
    print("🧪 간단한 업비트 WebSocket 테스트")
    print("=" * 40)
    asyncio.run(simple_test())
