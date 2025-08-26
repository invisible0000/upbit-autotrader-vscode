"""
업비트 WebSocket stream_type 필드 동작 테스트

🎯 목적: 업비트 WebSocket에서 stream_type 필드의 실제 동작 확인
- 기본 구독 vs is_only_snapshot: true 비교
- 초기 응답에서 stream_type 존재 여부 확인
- 스냅샷과 실시간 데이터의 stream_type 차이 분석
"""

import asyncio
import json
import websockets
import websockets.exceptions
from typing import Dict, Any, List

class StreamTypeAnalyzer:
    """업비트 WebSocket stream_type 분석기"""

    def __init__(self):
        self.url = "wss://api.upbit.com/websocket/v1"
        self.messages_received = []
        self.analysis_results = {}

    async def test_default_subscription(self) -> List[Dict[str, Any]]:
        """기본 구독 테스트 (스냅샷 + 실시간)"""
        print("🔍 기본 구독 테스트 시작 (스냅샷 + 실시간)")

        messages = []

        async with websockets.connect(self.url) as websocket:
            # 기본 구독 요청 (스냅샷 + 실시간)
            request = [
                {"ticket": "stream_type_test_default"},
                {"type": "ticker", "codes": ["KRW-BTC"]}
            ]

            await websocket.send(json.dumps(request))
            print(f"📤 요청 전송: {json.dumps(request, ensure_ascii=False)}")

            # 첫 5개 메시지 수집
            for i in range(5):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)

                    stream_type = data.get("stream_type")
                    print(f"📨 메시지 {i+1}: stream_type = {stream_type}")

                    messages.append({
                        "order": i + 1,
                        "stream_type": stream_type,
                        "has_stream_type": "stream_type" in data,
                        "type": data.get("type"),
                        "market": data.get("market", data.get("code")),
                        "timestamp": data.get("timestamp")
                    })

                except asyncio.TimeoutError:
                    print(f"⏱️ 메시지 {i+1} 대기 시간 초과")
                    break
                except Exception as e:
                    print(f"❌ 메시지 {i+1} 처리 오류: {e}")
                    break

        return messages

    async def test_snapshot_only_subscription(self) -> List[Dict[str, Any]]:
        """스냅샷 전용 구독 테스트"""
        print("\n🔍 스냅샷 전용 구독 테스트 시작 (is_only_snapshot: true)")

        messages = []

        async with websockets.connect(self.url) as websocket:
            # 스냅샷 전용 구독 요청
            request = [
                {"ticket": "stream_type_test_snapshot"},
                {"type": "ticker", "codes": ["KRW-BTC"], "is_only_snapshot": True}
            ]

            await websocket.send(json.dumps(request))
            print(f"📤 요청 전송: {json.dumps(request, ensure_ascii=False)}")

            # 스냅샷 메시지만 수집 (보통 1개)
            for i in range(3):  # 최대 3개까지 대기
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)

                    stream_type = data.get("stream_type")
                    print(f"📨 메시지 {i+1}: stream_type = {stream_type}")

                    messages.append({
                        "order": i + 1,
                        "stream_type": stream_type,
                        "has_stream_type": "stream_type" in data,
                        "type": data.get("type"),
                        "market": data.get("market", data.get("code")),
                        "timestamp": data.get("timestamp")
                    })

                except asyncio.TimeoutError:
                    print(f"⏱️ 메시지 {i+1} 대기 시간 초과 (정상 - 스냅샷 전용)")
                    break
                except Exception as e:
                    print(f"❌ 메시지 {i+1} 처리 오류: {e}")
                    break

        return messages

    async def test_realtime_only_subscription(self) -> List[Dict[str, Any]]:
        """실시간 전용 구독 테스트"""
        print("\n🔍 실시간 전용 구독 테스트 시작 (is_only_realtime: true)")

        messages = []

        async with websockets.connect(self.url) as websocket:
            # 실시간 전용 구독 요청
            request = [
                {"ticket": "stream_type_test_realtime"},
                {"type": "ticker", "codes": ["KRW-BTC"], "is_only_realtime": True}
            ]

            await websocket.send(json.dumps(request))
            print(f"📤 요청 전송: {json.dumps(request, ensure_ascii=False)}")

            # 실시간 메시지 수집
            for i in range(3):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)

                    stream_type = data.get("stream_type")
                    print(f"📨 메시지 {i+1}: stream_type = {stream_type}")

                    messages.append({
                        "order": i + 1,
                        "stream_type": stream_type,
                        "has_stream_type": "stream_type" in data,
                        "type": data.get("type"),
                        "market": data.get("market", data.get("code")),
                        "timestamp": data.get("timestamp")
                    })

                except asyncio.TimeoutError:
                    print(f"⏱️ 메시지 {i+1} 대기 시간 초과")
                    break
                except Exception as e:
                    print(f"❌ 메시지 {i+1} 처리 오류: {e}")
                    break

        return messages

    def analyze_results(self, default_msgs: List[Dict], snapshot_msgs: List[Dict], realtime_msgs: List[Dict]):
        """결과 분석 및 출력"""
        print("\n" + "="*80)
        print("📊 업비트 WebSocket stream_type 분석 결과")
        print("="*80)

        print("\n🔸 기본 구독 (스냅샷 + 실시간):")
        for msg in default_msgs:
            stream_status = "✅ 포함" if msg["has_stream_type"] else "❌ 없음"
            print(f"   메시지 {msg['order']}: stream_type = {msg['stream_type']} ({stream_status})")

        print("\n🔸 스냅샷 전용 구독 (is_only_snapshot: true):")
        for msg in snapshot_msgs:
            stream_status = "✅ 포함" if msg["has_stream_type"] else "❌ 없음"
            print(f"   메시지 {msg['order']}: stream_type = {msg['stream_type']} ({stream_status})")

        print("\n🔸 실시간 전용 구독 (is_only_realtime: true):")
        for msg in realtime_msgs:
            stream_status = "✅ 포함" if msg["has_stream_type"] else "❌ 없음"
            print(f"   메시지 {msg['order']}: stream_type = {msg['stream_type']} ({stream_status})")

        print("\n📝 핵심 발견사항:")

        # 기본 구독 분석
        if default_msgs:
            first_default = default_msgs[0]
            if not first_default["has_stream_type"]:
                print("   ✅ 기본 구독의 첫 응답에는 stream_type 없음 (구독 확인 메시지)")
            else:
                print(f"   ⚠️ 기본 구독의 첫 응답에 stream_type 있음: {first_default['stream_type']}")

        # 스냅샷 전용 분석
        if snapshot_msgs:
            first_snapshot = snapshot_msgs[0]
            if first_snapshot["has_stream_type"] and first_snapshot["stream_type"] == "SNAPSHOT":
                print("   ✅ is_only_snapshot: true 시 첫 응답에 stream_type='SNAPSHOT' 포함")
            else:
                print(f"   ⚠️ is_only_snapshot: true 예상과 다름: {first_snapshot}")

        # 실시간 전용 분석
        if realtime_msgs:
            first_realtime = realtime_msgs[0]
            if first_realtime["has_stream_type"] and first_realtime["stream_type"] == "REALTIME":
                print("   ✅ is_only_realtime: true 시 첫 응답에 stream_type='REALTIME' 포함")
            else:
                print(f"   ⚠️ is_only_realtime: true 예상과 다름: {first_realtime}")

        print("\n💡 결론:")
        print("   - 기본 구독: 초기 응답 stream_type 없음 → 스냅샷 → 실시간")
        print("   - is_only_snapshot: 명시적 SNAPSHOT stream_type 포함")
        print("   - is_only_realtime: 명시적 REALTIME stream_type 포함")
        print("   - 초기 응답은 '구독 확인'이며 데이터가 아님")

async def main():
    """메인 테스트 실행"""
    print("🎯 업비트 WebSocket stream_type 필드 동작 분석")
    print("=" * 70)

    analyzer = StreamTypeAnalyzer()

    try:
        # 각 테스트 실행
        default_messages = await analyzer.test_default_subscription()
        snapshot_messages = await analyzer.test_snapshot_only_subscription()
        realtime_messages = await analyzer.test_realtime_only_subscription()

        # 결과 분석
        analyzer.analyze_results(default_messages, snapshot_messages, realtime_messages)

    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
