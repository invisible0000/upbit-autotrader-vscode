"""
웹소켓 일반 요청 간섭 테스트
=========================

목적:
- KRW-ETH 실시간 스트림 중에
- 10초 시점에 KRW-BTC 일반 요청(is_only_snapshot 없음)을 끼워넣어서
- KRW-ETH 메시지가 멈추는지 확인

예상 결과:
- 만약 일반 요청도 기존 스트림을 방해한다면 → 업비트 웹소켓 설계 문제
- 만약 스냅샷만 방해한다면 → is_only_snapshot 처리 이슈
"""

import asyncio
import json
import websockets
import time

async def test_regular_request_interference():
    uri = "wss://api.upbit.com/websocket/v1"

    async with websockets.connect(uri) as websocket:
        print("🚀 웹소켓 연결 성공!")

        # 1단계: KRW-ETH 실시간 스트림 시작
        print("📡 KRW-ETH 실시간 스트림 시작...")
        message1 = [
            {"ticket": "ticket_eth_realtime_001"},
            {
                "type": "ticker",
                "codes": ["KRW-ETH"]
                # is_only_snapshot 없음 → 실시간 스트림
            },
            {"format": "DEFAULT"}
        ]
        await websocket.send(json.dumps(message1))
        print("   ✅ 티켓1: KRW-ETH 실시간 구독 완료\n")

        # 2단계: 20초 동안 모니터링
        start_time = time.time()
        message_count = 0
        regular_request_sent = False

        print("🔍 20초 모니터링 시작 (10초 시점에 KRW-BTC 일반 요청 끼어들기)")
        print("=" * 60)

        while time.time() - start_time < 20:
            current_time = time.time() - start_time

            # 10초 시점에 KRW-BTC 일반 요청 끼어들기!
            if current_time >= 10 and not regular_request_sent:
                print(f"🔥 [{current_time:.1f}s] 티켓2 일반 요청 끼어들기!! (is_only_snapshot 없음)")
                message2 = [
                    {"ticket": "ticket_btc_regular_002"},
                    {
                        "type": "ticker",
                        "codes": ["KRW-BTC"]
                        # is_only_snapshot 없음 → 일반 요청 (실시간?)
                    },
                    {"format": "DEFAULT"}
                ]
                await websocket.send(json.dumps(message2))
                regular_request_sent = True

            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                data = json.loads(message)

                message_count += 1

                # 핵심 정보만 추출
                code = data.get("code", "UNKNOWN")
                price = data.get("trade_price", "NONE")
                stream_type = data.get("stream_type", "UNKNOWN")

                # 10초 전후로 구분해서 표시
                time_marker = "📍" if 9.8 <= current_time <= 10.2 else "⚡"

                # 심볼별로 구분해서 표시
                symbol_marker = "🟢" if code == "KRW-ETH" else "🔵" if code == "KRW-BTC" else "❓"

                print(f"{time_marker}{symbol_marker} [{current_time:.1f}s] #{message_count}: {code} {stream_type} {price}")

            except asyncio.TimeoutError:
                # 연결 상태 확인을 위한 ping
                if current_time >= 10.5 and int(current_time * 10) % 20 == 0:  # 2초마다
                    try:
                        print(f"🏓 [{current_time:.1f}s] PING 전송 중...")
                        pong_waiter = await websocket.ping()
                        await asyncio.wait_for(pong_waiter, timeout=1.0)
                        print(f"✅ [{current_time:.1f}s] PONG 응답 받음 - 연결 살아있음")
                    except asyncio.TimeoutError:
                        print(f"❌ [{current_time:.1f}s] PING 응답 없음 - 연결 문제?")
                    except Exception as e:
                        print(f"🚨 [{current_time:.1f}s] PING 오류: {e}")

                continue

        print(f"\n🏁 20초 실험 완료: 총 {message_count}개 메시지 수신")
        print("=" * 60)

        if message_count == 0:
            print("🚨 심각: 메시지를 전혀 받지 못했습니다!")
        elif regular_request_sent:
            print("🔍 결론:")
            print("   - 일반 요청도 기존 스트림을 방해하는지 확인 필요")
            print("   - 마지막 메시지 시간과 끼어들기 시간 비교 분석")

if __name__ == "__main__":
    print("🧪 웹소켓 일반 요청 간섭 테스트")
    print("================================")
    print("목적: is_only_snapshot 없는 일반 요청이 기존 스트림을 방해하는지 확인")
    print()

    asyncio.run(test_regular_request_interference())
