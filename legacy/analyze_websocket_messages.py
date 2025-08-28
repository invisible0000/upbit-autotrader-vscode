"""
업비트 WebSocket 초기 메시지 분석 스크립트

🎯 목적:
- 연결 시 수신되는 모든 메시지 로깅
- "Connected!" 메시지 존재 여부 확인
- 상태 메시지 패턴 분석
"""

import asyncio
import websockets
import json
import time


class WebSocketMessageAnalyzer:
    """WebSocket 초기 메시지 분석기"""

    def __init__(self):
        self.connection_messages = []
        self.connection_start_time = None
        self.websocket = None

    async def analyze_connection_messages(self, duration: int = 15):
        """연결 후 일정 시간동안 메시지 분석"""
        print("🔍 업비트 WebSocket 초기 메시지 분석 시작...")
        print(f"   📊 분석 시간: {duration}초")
        print("   🎯 'Connected!' 메시지 탐지")
        print("   📝 모든 초기 메시지 기록")
        print()

        try:
            # WebSocket 연결
            print("🔗 WebSocket 연결 시도...")
            self.connection_start_time = time.time()

            self.websocket = await websockets.connect(
                "wss://api.upbit.com/websocket/v1",
                ping_interval=30,
                ping_timeout=10
            )

            print(f"✅ WebSocket 연결 완료! ({time.time() - self.connection_start_time:.3f}초)")
            print("📥 메시지 수신 대기 중...")
            print("-" * 60)

            # 메시지 수신 루프
            start_time = time.time()
            message_count = 0

            try:
                while (time.time() - start_time) < duration:
                    try:
                        # 1초 타임아웃으로 메시지 수신 시도
                        message = await asyncio.wait_for(
                            self.websocket.recv(), timeout=1.0
                        )

                        message_count += 1
                        elapsed = time.time() - self.connection_start_time

                        # 메시지 파싱 시도
                        try:
                            if isinstance(message, str):
                                # JSON 파싱 시도
                                try:
                                    data = json.loads(message)
                                    print(f"[{elapsed:6.3f}s] #{message_count:2d} JSON: {data}")
                                except json.JSONDecodeError:
                                    # 일반 텍스트 메시지
                                    print(f"[{elapsed:6.3f}s] #{message_count:2d} TEXT: '{message}'")

                                    # "Connected!" 메시지 특별 처리
                                    if "Connected" in message:
                                        print(f"🎉 'Connected!' 메시지 발견! (연결 후 {elapsed:.3f}초)")
                            else:
                                # 바이너리 메시지
                                print(f"[{elapsed:6.3f}s] #{message_count:2d} BINARY: {len(message)} bytes")

                        except Exception as parse_error:
                            print(f"[{elapsed:6.3f}s] #{message_count:2d} PARSE_ERROR: {parse_error}")

                        # 메시지 저장
                        self.connection_messages.append({
                            'timestamp': elapsed,
                            'message': message,
                            'message_number': message_count
                        })

                    except asyncio.TimeoutError:
                        # 1초 동안 메시지가 없으면 계속
                        pass

            except Exception as recv_error:
                print(f"❌ 메시지 수신 오류: {recv_error}")

            print("-" * 60)
            print(f"📊 분석 완료! 총 {message_count}개 메시지 수신")

            # 결과 분석
            await self.analyze_results()

        except Exception as e:
            print(f"❌ 연결 실패: {e}")

        finally:
            if self.websocket:
                await self.websocket.close()
                print("🔌 WebSocket 연결 해제 완료")

    async def analyze_results(self):
        """수신된 메시지 분석 결과 출력"""
        print("\n" + "="*60)
        print("📋 메시지 분석 결과")
        print("="*60)

        if not self.connection_messages:
            print("❌ 수신된 메시지가 없습니다.")
            return

        # 메시지 타입별 분류
        json_messages = []
        text_messages = []
        binary_messages = []
        connected_messages = []

        for msg_info in self.connection_messages:
            message = msg_info['message']

            if isinstance(message, str):
                try:
                    json.loads(message)
                    json_messages.append(msg_info)
                except:
                    text_messages.append(msg_info)
                    if "Connected" in message:
                        connected_messages.append(msg_info)
            else:
                binary_messages.append(msg_info)

        print(f"📊 메시지 통계:")
        print(f"   🔢 총 메시지: {len(self.connection_messages)}개")
        print(f"   📄 JSON 메시지: {len(json_messages)}개")
        print(f"   📝 텍스트 메시지: {len(text_messages)}개")
        print(f"   📦 바이너리 메시지: {len(binary_messages)}개")
        print(f"   🎯 'Connected' 포함: {len(connected_messages)}개")
        print()

        if connected_messages:
            print("🎉 'Connected!' 메시지 발견!")
            for msg_info in connected_messages:
                print(f"   ⏰ 연결 후 {msg_info['timestamp']:.3f}초에 수신")
                print(f"   📝 내용: '{msg_info['message']}'")
            print()
            print("💡 추천: 'Connected!' 메시지를 연결 완료 신호로 활용 가능!")
        else:
            print("❌ 'Connected!' 메시지를 찾을 수 없습니다.")

        # 첫 5개 메시지 상세 출력
        print("\n📝 첫 5개 메시지 상세:")
        for i, msg_info in enumerate(self.connection_messages[:5]):
            print(f"   {i+1}. [{msg_info['timestamp']:.3f}s] {msg_info['message']}")

        if len(self.connection_messages) > 5:
            print(f"   ... 및 {len(self.connection_messages) - 5}개 추가 메시지")

        print("="*60)

async def main():
    """메인 실행 함수"""
    analyzer = WebSocketMessageAnalyzer()

    try:
        await analyzer.analyze_connection_messages(duration=15)
    except KeyboardInterrupt:
        print("\n⏹️ 분석이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    print("🔍 업비트 WebSocket 초기 메시지 분석기")
    print("   - 연결 후 15초간 모든 메시지 기록")
    print("   - 'Connected!' 메시지 탐지")
    print("   - Ctrl+C로 중단 가능")
    print()

    asyncio.run(main())
