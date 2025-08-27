"""
업비트 WebSocket is_only_snapshot 동작 검증 스크립트

이 스크립트는 업비트 WebSocket의 두 가지 모드를 검증합니다:
1. is_only_snapshot: true  → 스냅샷만 받고 realtime 데이터 없음
2. is_only_snapshot: false → 스냅샷 + realtime 데이터 스트림

기본 websocket 패키지 사용으로 언제든 독립적 검증 가능
"""

import asyncio
import websockets
import json
import uuid
import time
from datetime import datetime


class UpbitWebSocketTester:
    def __init__(self):
        self.uri = "wss://api.upbit.com/websocket/v1"
        self.websocket = None

    async def connect(self):
        """WebSocket 연결"""
        self.websocket = await websockets.connect(self.uri)
        print(f"✅ Connected to {self.uri}")

    async def disconnect(self):
        """WebSocket 연결 해제"""
        if self.websocket:
            await self.websocket.close()
            print("✅ Disconnected")

    async def send_request(self, data_type: str, symbols: list, is_only_snapshot: bool):
        """업비트 WebSocket 요청 전송"""
        ticket = str(uuid.uuid4())[:8]

        request = [
            {"ticket": ticket},
            {
                "type": data_type,
                "codes": symbols,
                "isOnlySnapshot": is_only_snapshot
            }
        ]

        await self.websocket.send(json.dumps(request))
        print(f"📤 Request sent - Type: {data_type}, Snapshot Only: {is_only_snapshot}")
        print(f"   Symbols: {symbols}")
        return ticket

    async def receive_messages(self, duration_seconds: int):
        """지정된 시간 동안 메시지 수신"""
        messages = []
        start_time = time.time()
        last_progress_time = start_time

        print(f"📥 Receiving messages for {duration_seconds} seconds...")
        print(f"   ⏰ 시작 시간: {datetime.fromtimestamp(start_time).strftime('%H:%M:%S.%f')[:-3]}")
        print("   ⏳ 대기 중... (스냅샷 모드라도 충분히 대기하여 확인)")

        try:
            while True:
                current_time = time.time()
                elapsed = current_time - start_time

                # 종료 조건 체크
                if elapsed >= duration_seconds:
                    print(f"   ⏰ {duration_seconds}초 완료 - 종료")
                    break

                # 1초마다 진행 상황 출력
                if current_time - last_progress_time >= 1.0:
                    remaining = duration_seconds - elapsed
                    print(f"   ⏱️  경과: {elapsed:.1f}초 / 남은시간: {remaining:.1f}초")
                    last_progress_time = current_time

                try:
                    # 0.5초 타임아웃으로 메시지 대기 (더 세밀한 체크)
                    if self.websocket:
                        message = await asyncio.wait_for(
                            self.websocket.recv(),
                            timeout=0.5
                        )
                    else:
                        break

                    # 바이너리 데이터 처리
                    if isinstance(message, bytes):
                        try:
                            decoded = message.decode('utf-8')
                            data = json.loads(decoded)

                            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                            elapsed_at_msg = time.time() - start_time
                            msg_type = data.get('type', 'unknown')
                            msg_code = data.get('code', 'N/A')
                            print(f"[{timestamp}] 📨 Message (경과: {elapsed_at_msg:.2f}초): "
                                  f"{msg_type} - {msg_code}")

                            messages.append({
                                'timestamp': timestamp,
                                'elapsed': elapsed_at_msg,
                                'data': data
                            })

                        except Exception as e:
                            print(f"❌ Failed to decode message: {e}")

                except asyncio.TimeoutError:
                    # 0.5초 타임아웃은 정상 - 계속 대기
                    continue

        except Exception as e:
            print(f"❌ Error receiving messages: {e}")

        end_time = time.time()
        actual_duration = end_time - start_time
        print(f"   ⏰ 종료 시간: {datetime.fromtimestamp(end_time).strftime('%H:%M:%S.%f')[:-3]}")
        print(f"   ⏱️  실제 대기 시간: {actual_duration:.2f}초 (목표: {duration_seconds}초)")
        print(f"📊 Total messages received: {len(messages)}")

        return messages


async def test_snapshot_only():
    """is_only_snapshot: true 테스트"""
    print("\n" + "=" * 60)
    print("🧪 TEST 1: is_only_snapshot = True")
    print("   Expected: 스냅샷 1개만 받고 realtime 데이터 없음")
    print("=" * 60)

    tester = UpbitWebSocketTester()
    await tester.connect()

    try:
        # 스냅샷 전용 요청
        await tester.send_request(
            data_type="ticker",
            symbols=["KRW-BTC"],
            is_only_snapshot=True
        )

        # 10초 동안 메시지 수신 (스냅샷 후 추가 메시지가 있는지 확인)
        messages = await tester.receive_messages(10)

        # 결과 분석
        print("\n📊 분석 결과:")
        print(f"   총 메시지 수: {len(messages)}")

        if len(messages) == 0:
            print("   ❌ 스냅샷 메시지도 받지 못함")
        elif len(messages) == 1:
            print("   ✅ 스냅샷 1개만 받음 (예상대로)")
            print(f"   📄 스냅샷 데이터: {messages[0]['data'].get('trade_price', 'N/A')}")
        else:
            print(f"   ⚠️  예상보다 많은 메시지 받음 ({len(messages)}개)")
            print("   📄 첫 번째: 스냅샷")
            print("   📄 나머지: realtime 데이터 (예상과 다름)")

        return len(messages)

    finally:
        await tester.disconnect()


async def test_realtime_with_snapshot():
    """is_only_snapshot: false 테스트"""
    print("\n" + "=" * 60)
    print("🧪 TEST 2: is_only_snapshot = False")
    print("   Expected: 스냅샷 1개 + realtime 데이터 스트림")
    print("=" * 60)

    tester = UpbitWebSocketTester()
    await tester.connect()

    try:
        # 리얼타임 구독 요청
        await tester.send_request(
            data_type="ticker",
            symbols=["KRW-BTC"],
            is_only_snapshot=False
        )

        # 5초 동안 메시지 수신
        messages = await tester.receive_messages(5)

        # 결과 분석
        print("\n📊 분석 결과:")
        print(f"   총 메시지 수: {len(messages)}")

        if len(messages) == 0:
            print("   ❌ 아무 메시지도 받지 못함")
        elif len(messages) == 1:
            print("   ⚠️  스냅샷만 받음 (realtime 없음)")
        else:
            print(f"   ✅ 스냅샷 + realtime 스트림 ({len(messages)}개)")
            print("   📄 첫 번째: 스냅샷")
            print(f"   📄 나머지: realtime 데이터 ({len(messages) - 1}개)")

            # 시간 간격 분석
            if len(messages) >= 2:
                first_time = messages[0]['timestamp']
                last_time = messages[-1]['timestamp']
                print(f"   ⏱️  스트림 기간: {first_time} ~ {last_time}")

        return len(messages)

    finally:
        await tester.disconnect()


async def test_comparison():
    """두 모드 비교 분석"""
    print("\n" + "=" * 60)
    print("🔍 ANALYSIS: 스냅샷 vs 리얼타임 모드 비교")
    print("   Expected: snapshot_count = 1, realtime_count > 1")
    print("=" * 60)

    # 테스트 실행
    snapshot_count = await test_snapshot_only()
    await asyncio.sleep(2)  # 잠시 대기
    realtime_count = await test_realtime_with_snapshot()

    # 비교 결과
    print("\n" + "=" * 60)
    print("📊 최종 비교 결과")
    print("=" * 60)
    print(f"is_only_snapshot = True:  {snapshot_count}개 메시지")
    print(f"is_only_snapshot = False: {realtime_count}개 메시지")

    if snapshot_count == 1 and realtime_count > 1:
        print("✅ 테스트 성공: is_only_snapshot 기능이 올바르게 동작함")
        print("   - snapshot 모드: 1개 메시지만")
        print("   - realtime 모드: 지속적 스트림")
    elif snapshot_count == 1 and realtime_count == 1:
        print("⚠️  is_only_snapshot = False도 1개만 받음")
        print("   - 가능한 원인: 시장 시간 외, 네트워크 이슈")
    elif snapshot_count > 1:
        print("❌ is_only_snapshot = True인데 여러 메시지 받음")
        print("   - 업비트 서버 이슈이거나 구현 문제")
    else:
        print("❌ 예상과 다른 결과")

    return snapshot_count, realtime_count


async def main():
    """메인 테스트 실행"""
    print("🚀 업비트 WebSocket is_only_snapshot 검증 시작")
    print(f"⏰ 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        snapshot_count, realtime_count = await test_comparison()

        print("\n📋 테스트 요약:")
        print(f"   • 스냅샷 전용: {snapshot_count}개")
        print(f"   • 리얼타임 포함: {realtime_count}개")
        print(f"   • 차이: {realtime_count - snapshot_count}개")

        # 결론
        if snapshot_count == 1 and realtime_count > snapshot_count:
            print("\n🎯 결론: is_only_snapshot 기능 정상 동작 확인")
            print("   - 스냅샷 모드에서는 realtime 데이터가 전송되지 않음")
            print("   - 리얼타임 모드에서는 스냅샷 후 지속적 업데이트")
        else:
            print("\n🤔 결론: 추가 확인 필요")
            print("   - 시장 시간, 네트워크 상태, 서버 상태 확인 권장")

    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")


if __name__ == "__main__":
    asyncio.run(main())
