"""
업비트 WebSocket 티켓 독립성 테스트 - 심플 버전

핵심 질문:
티켓1에 KRW-BTC 실시간 스트림이 있을 때,
티켓2에 KRW-BTC 스냅샷 요청하면 어떻게 될까?

테스트 시나리오:
1. 티켓1: KRW-BTC, KRW-ETH is_only_realtime=True (10초 대기)
2. 티켓2: KRW-BTC is_only_snapshot=True (10초 대기)

예상 결과:
A) 티켓 독립적: 티켓2는 스냅샷 1개만 받고 침묵
B) 심볼 기반 통합: 티켓2도 KRW-BTC 실시간 스트림 받기 시작
"""

import asyncio
import json
import websockets
import time


async def simple_ticket_test():
    """연속 20초 실험 - 10초 시점에 스냅샷 요청 끼어들기"""
    print("🧪 업비트 WebSocket 티켓 독립성 테스트 - 연속 20초 실험")
    print("=" * 60)
    print("📋 실험 계획:")
    print("   0-20초: 티켓1 KRW-BTC, KRW-ETH 실시간 스트림")
    print("   10초 시점: 티켓2 KRW-BTC 스냅샷 요청 끼어들기!")
    print("=" * 60)

    # WebSocket 연결
    websocket = await websockets.connect("wss://api.upbit.com/websocket/v1")
    print("✅ 업비트 WebSocket 연결 완료\n")

    message_count = 0
    snapshot_sent = False

    try:
        # 실험 시작: 티켓1 실시간 스트림 설정
        print("� 실험 시작: 티켓1 실시간 스트림")
        message1 = [
            {"ticket": "ticket_realtime_001"},
            {
                "type": "ticker",
                "codes": ["KRW-BTC", "KRW-ETH"],
                "is_only_realtime": True
            },
            {"format": "DEFAULT"}
        ]
        await websocket.send(json.dumps(message1))
        print("   ✅ 티켓1: KRW-BTC, KRW-ETH 실시간 스트림 시작")

        # 20초 연속 실험
        print("\n🔍 20초 연속 메시지 관찰 시작...\n")
        start_time = time.time()

        while time.time() - start_time < 20:
            current_time = time.time() - start_time

            # 10초 시점에 스냅샷 요청 끼어들기!
            if current_time >= 10 and not snapshot_sent:
                # 간단하게 한 줄로 표시
                print(f"🔥 [{current_time:.1f}s] 티켓2 스냅샷 요청 끼어들기!!")
                message2 = [
                    {"ticket": "ticket_snapshot_002"},
                    {
                        "type": "ticker",
                        "codes": ["KRW-BTC"],
                        "is_only_snapshot": True
                    },
                    {"format": "DEFAULT"}
                ]
                await websocket.send(json.dumps(message2))
                snapshot_sent = True

            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                data = json.loads(message)

                message_count += 1

                # 핵심 정보만 추출
                code = data.get("code", "UNKNOWN")
                price = data.get("trade_price", "NONE")
                stream_type = data.get("stream_type", "UNKNOWN")

                # 10초 전후로 구분해서 표시 (범위를 좁혀서)
                time_marker = "📍" if 9.8 <= current_time <= 10.2 else "⚡"

                print(f"{time_marker} [{current_time:.1f}s] #{message_count}: {code} {stream_type} {price}")

            except asyncio.TimeoutError:
                # 타임아웃 시에는 ping을 보내서 연결 상태 확인
                if current_time >= 10.5 and int(current_time * 10) % 20 == 0:  # 10.5초부터 2초마다
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

        # 간단한 결론
        print("\n🎯 결론:")
        if snapshot_sent:
            print("✅ 10초 시점에 스냅샷 요청 성공적으로 끼어들기")
            print("📊 실험 결과를 통해 티켓 독립성을 확인할 수 있음")
        else:
            print("⚠️ 스냅샷 요청이 전송되지 않음")

    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")

    finally:
        await websocket.close()
        print("\n🔌 WebSocket 연결 해제")

    print("\n🏁 테스트 완료")
    print("\n💡 이제 결과를 분석해보세요:")
    print("   - 10초 전후로 KRW-BTC 메시지 패턴이 바뀌었나요?")
    print("   - 스냅샷 요청 후 실시간 메시지가 증가했나요?")
    print("   - 티켓이 독립적인지 통합적인지 확인할 수 있어요!")


if __name__ == "__main__":
    asyncio.run(simple_ticket_test())
