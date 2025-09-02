#!/usr/bin/env python3
"""
업비트 Private WebSocket 세부 테스트
===================================

목적: myAsset 요청 실패 원인 파악
1. Private 연결 후 장시간 대기
2. 다양한 Private 데이터 요청 테스트
3. 에러 메시지 상세 분석
"""

import asyncio
import json
import os
import sys
import time
import uuid

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import websockets
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator
except ImportError as e:
    print(f"❌ 임포트 실패: {e}")
    exit(1)


class PrivateWebSocketDetailTest:
    """Private WebSocket 상세 테스트"""

    PRIVATE_URL = "wss://api.upbit.com/websocket/v1/private"

    def __init__(self):
        self.authenticator = UpbitAuthenticator()
        self.has_api_keys = self.authenticator.is_authenticated()

    async def create_jwt_token(self) -> str:
        """JWT 토큰 생성"""
        if not self.has_api_keys:
            raise Exception("API 키가 없습니다")

        token_info = await self.authenticator.create_websocket_token()
        return token_info.get('access_token')

    async def test_private_connection_detail(self):
        """Private 연결 상세 테스트"""
        print("🔍 Private WebSocket 상세 분석")
        print("="*60)

        if not self.has_api_keys:
            print("❌ API 키가 없어서 테스트를 건너뜁니다")
            return

        # JWT 토큰 생성
        jwt_token = await self.create_jwt_token()
        headers = {"Authorization": f"Bearer {jwt_token}"}

        try:
            async with websockets.connect(
                self.PRIVATE_URL,
                additional_headers=headers
            ) as websocket:
                print("✅ Private WebSocket 연결 성공!")

                # 1. 연결 후 초기 상태 확인 (5초 대기)
                print("\n--- 1단계: 연결 후 초기 메시지 대기 (5초) ---")
                try:
                    initial_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"📥 초기 메시지: {initial_msg}")
                except asyncio.TimeoutError:
                    print("⏰ 초기 메시지 없음 (정상)")

                # 2. myOrder 요청 (myAsset 대신 - 주문 데이터가 더 확실)
                print("\n--- 2단계: myOrder 요청 ---")
                request = json.dumps([
                    {"ticket": str(uuid.uuid4())},
                    {"type": "myOrder"}
                ])
                print(f"📤 요청: {request}")

                await websocket.send(request)
                print("✅ 요청 전송 완료")

                # 응답 대기 - 지속적인 polling 방식 (30초)
                print("⏳ 응답 대기 중... (30초간 지속적 모니터링)")
                start_wait = time.time()
                message_count = 0

                while time.time() - start_wait < 30:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                        message_count += 1

                        # 현재 시간 표시
                        elapsed = time.time() - start_wait
                        print(f"📥 [{elapsed:.1f}s] 메시지 #{message_count}: {response[:200]}...")

                        # JSON 파싱 시도
                        try:
                            parsed = json.loads(response)
                            if 'error' in parsed:
                                print(f"❌ 서버 에러: {parsed['error']}")
                            elif 'type' in parsed:
                                print(f"✅ 데이터 타입: {parsed.get('type')} - 수신 성공!")
                            else:
                                print("✅ myOrder 데이터 수신 성공!")
                        except json.JSONDecodeError:
                            print(f"⚠️ JSON 파싱 실패, Raw 응답 길이: {len(response)} bytes")

                    except asyncio.TimeoutError:
                        # 5초마다 상태 확인 메시지
                        if int(time.time() - start_wait) % 5 == 0:
                            elapsed = time.time() - start_wait
                            print(f"🔍 [{elapsed:.1f}s] 메시지 대기 중... (받은 메시지: {message_count}개)")
                        continue

                if message_count == 0:
                    print("⚠️ 30초 동안 메시지를 받지 못했습니다 - 매도 주문이 없거나 응답 방식 문제")
                else:
                    print(f"✅ 총 {message_count}개의 메시지를 받았습니다")

                # 3. 연결 상태 확인
                print("\n--- 3단계: 연결 상태 확인 ---")
                print(f"연결 상태: {websocket.state}")
                print(f"연결 활성 여부: {websocket.state.name}")

                # 4. 추가 메시지 대기 (연결이 살아있는지 확인)
                print("\n--- 4단계: 추가 메시지 대기 (5초) ---")
                try:
                    additional_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"📥 추가 메시지: {additional_msg}")
                except asyncio.TimeoutError:
                    print("⏰ 추가 메시지 없음")
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"🔌 연결 종료됨: {e}")

                # 5. 다른 Private 데이터 타입 테스트
                if websocket.state.name in ['OPEN', 'CONNECTING']:
                    print("\n--- 5단계: myTrade 요청 테스트 ---")
                    trade_request = json.dumps([
                        {"ticket": str(uuid.uuid4())},
                        {"type": "myTrade"}
                    ])
                    print(f"📤 myTrade 요청: {trade_request}")

                    try:
                        await websocket.send(trade_request)
                        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        print(f"📥 myTrade 응답: {response}")
                    except Exception as e:
                        print(f"❌ myTrade 요청 실패: {e}")
                else:
                    print("\n--- 5단계: 연결이 종료되어 추가 테스트 건너뜀 ---")

        except Exception as e:
            print(f"❌ Private 연결 실패: {e}")

    async def test_connection_timing(self):
        """연결 타이밍 테스트"""
        print("\n🕐 연결 타이밍 분석")
        print("="*60)

        if not self.has_api_keys:
            return

        jwt_token = await self.create_jwt_token()
        headers = {"Authorization": f"Bearer {jwt_token}"}

        start_time = time.time()

        try:
            async with websockets.connect(
                self.PRIVATE_URL,
                additional_headers=headers
            ) as websocket:
                connect_time = time.time() - start_time
                print(f"⏱️ 연결 시간: {connect_time:.3f}초")

                # 즉시 요청
                request = json.dumps([
                    {"ticket": str(uuid.uuid4())},
                    {"type": "myAsset"}
                ])

                send_start = time.time()
                await websocket.send(request)
                send_time = time.time() - send_start
                print(f"⏱️ 요청 전송 시간: {send_time:.3f}초")

                # 응답 시간 측정
                response_start = time.time()
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    response_time = time.time() - response_start
                    print(f"⏱️ 응답 시간: {response_time:.3f}초")
                    print(f"📥 응답 내용: {response[:100]}...")
                except asyncio.TimeoutError:
                    response_time = time.time() - response_start
                    print(f"⏱️ 응답 타임아웃: {response_time:.3f}초")

        except Exception as e:
            connect_time = time.time() - start_time
            print(f"❌ 연결 실패: {e} (시간: {connect_time:.3f}초)")

    async def test_dual_websocket_connections(self):
        """두 개의 WebSocket 동시 연결 테스트 - 매도 주문 상태 확인"""
        print("\n🔗 Public + Private WebSocket 동시 연결 테스트 (실제 주문 확인)")
        print("=" * 60)

        if not self.has_api_keys:
            print("❌ API 키가 없어서 Private 연결 테스트를 건너뜁니다")
            return

        # JWT 토큰 생성
        jwt_token = await self.create_jwt_token()
        private_headers = {"Authorization": f"Bearer {jwt_token}"}

        try:
            # 두 개의 WebSocket 동시 연결
            public_url = "wss://api.upbit.com/websocket/v1"
            private_url = "wss://api.upbit.com/websocket/v1/private"

            async with websockets.connect(public_url) as public_ws, \
                       websockets.connect(private_url,
                                          additional_headers=private_headers) as private_ws:

                print("✅ Public + Private WebSocket 동시 연결 성공!")

                # Public WebSocket에 ticker 요청
                public_request = json.dumps([
                    {"ticket": str(uuid.uuid4())},
                    {"type": "ticker", "codes": ["KRW-BTC"]},
                    {"format": "DEFAULT"}
                ])

                # Private WebSocket에 myOrder 요청
                private_request = json.dumps([
                    {"ticket": str(uuid.uuid4())},
                    {"type": "myOrder"}
                ])

                print("\n📤 Public에 ticker 요청...")
                await public_ws.send(public_request)

                print("📤 Private에 myOrder 요청...")
                await private_ws.send(private_request)

                # 두 WebSocket을 30초간 지속적으로 모니터링
                print("\n⏳ 두 WebSocket 30초간 지속 모니터링...")

                start_time = time.time()
                public_count = 0
                private_count = 0

                while time.time() - start_time < 30:
                    elapsed = time.time() - start_time

                    # Public WebSocket 체크
                    try:
                        public_response = await asyncio.wait_for(public_ws.recv(), timeout=0.1)
                        public_count += 1
                        data = json.loads(public_response)
                        price = data.get('trade_price', 'N/A')
                        print(f"🟢 [{elapsed:.1f}s] Public #{public_count}: BTC {price}")
                    except asyncio.TimeoutError:
                        pass
                    except Exception as e:
                        print(f"❌ Public 오류: {e}")

                    # Private WebSocket 체크
                    try:
                        private_response = await asyncio.wait_for(private_ws.recv(), timeout=0.1)
                        private_count += 1
                        print(f"🔵 [{elapsed:.1f}s] Private #{private_count}: {private_response[:150]}...")

                        # 주문 데이터 파싱
                        try:
                            order_data = json.loads(private_response)
                            if 'error' in order_data:
                                print(f"     ❌ 에러: {order_data['error']}")
                            elif 'type' in order_data:
                                order_type = order_data.get('type')
                                order_id = order_data.get('uuid', 'N/A')
                                state = order_data.get('state', 'N/A')
                                print(f"     ✅ 주문: {order_type} ID:{order_id[:8]}... 상태:{state}")
                        except Exception:
                            pass

                    except asyncio.TimeoutError:
                        pass
                    except Exception as e:
                        print(f"❌ Private 오류: {e}")

                    # 10초마다 상태 요약
                    if int(elapsed) > 0 and int(elapsed) % 10 == 0 and int(elapsed * 10) % 10 == 0:
                        print(f"📊 [{elapsed:.0f}s] 요약: Public {public_count}개, Private {private_count}개 메시지")

                print("\n📊 30초 최종 결과:")
                print(f"  🟢 Public: {public_count}개 메시지 (ticker 데이터)")
                print(f"  🔵 Private: {private_count}개 메시지 (주문 데이터)")

                if private_count == 0:
                    print("\n🤔 Private 메시지가 없는 이유:")
                    print("  1. 매도 주문이 없거나")
                    print("  2. 주문 상태 변화가 없거나")
                    print("  3. myOrder는 실시간 스트림이라 초기 스냅샷이 없을 수 있음")
                    print("  → myTrade나 myAsset으로도 테스트해보세요")
                else:
                    print("✅ Private WebSocket이 정상 작동하고 있습니다!")

        except Exception as e:
            print(f"❌ 동시 연결 테스트 실패: {e}")

    async def _wait_for_response(self, websocket, ws_type: str) -> str:
        """WebSocket 응답 대기 헬퍼"""
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            return f"응답 수신 ({len(response)} bytes)"
        except asyncio.TimeoutError:
            return "타임아웃 (실시간 스트림 특성상 정상)"


async def main():
    """메인 테스트 실행"""
    print("🧪 업비트 Private WebSocket 세부 분석 시작\n")

    tester = PrivateWebSocketDetailTest()

    await tester.test_private_connection_detail()
    await tester.test_connection_timing()
    await tester.test_dual_websocket_connections()

    print("\n" + "=" * 60)
    print("✅ 모든 세부 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
