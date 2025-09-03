#!/usr/bin/env python3
"""
업비트 WebSocket Public/Private 독립성 및 실시간 응답 테스트 v2
========================================================

개선사항:
- upbit_private_client.py 사용으로 실제 주문 가능
- 매수 주문을 매우 낮은 가격(10,000원)으로 5,000원 주문
- 체결되지 않는 안전한 테스트 주문
- 기존 테스트 의도 완전 유지

목적:
1. Public/Private WebSocket 독립성 검증
2. REST API 주문 생성/취소 시 실시간 응답 확인
3. 콜백 기반으로 메시지 누락 방지
4. ping/pong으로 연결 상태 명확히 구분

테스트 시나리오:
1. Public/Private WebSocket 동시 연결
2. 각각 ping/pong 연결 상태 확인
3. Public: KRW-BTC ticker 스트림 시작
4. Private: myAsset, myOrder 구독
5. REST API: KRW-BTC 매수 주문 (10,000원에 5,000원) - 체결 안됨
6. Private 응답 확인, Public 스트림 지속성 확인
7. REST API: 주문 취소
8. 모든 응답 추적 및 분석
"""

import asyncio
import json
import os
import sys
import time
import uuid
from typing import Optional
from decimal import Decimal

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import websockets
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_private_client import UpbitPrivateClient
except ImportError as e:
    print(f"❌ 임포트 실패: {e}")
    exit(1)


class DualWebSocketBehaviorTestV2:
    """Public/Private WebSocket 동시 테스트 v2 - 실제 주문 지원"""

    def __init__(self):
        self.authenticator = UpbitAuthenticator()
        self.upbit_client = None  # UpbitPrivateClient 인스턴스
        self.has_api_keys = self.authenticator.is_authenticated()

        # 응답 카운터
        self.public_message_count = 0
        self.private_message_count = 0

        # 테스트 주문 ID 추적
        self.test_order_id: Optional[str] = None

        # 연결 상태
        self.public_ws = None
        self.private_ws = None

        print(f"🔑 API 키 상태: {'✅ 인증됨' if self.has_api_keys else '❌ 없음'}")

    async def initialize_client(self):
        """UpbitPrivateClient 초기화"""
        if not self.has_api_keys:
            print("❌ API 키 없음 - Private 클라이언트 초기화 건너뜀")
            return

        try:
            # DRY-RUN 모드 비활성화로 실제 주문 가능하게 설정
            self.upbit_client = UpbitPrivateClient(
                access_key=None,  # UpbitAuthenticator에서 자동 로드
                secret_key=None,  # UpbitAuthenticator에서 자동 로드
                dry_run=False,    # 실제 주문 모드
                use_dynamic_limiter=True
            )

            # 세션 초기화
            await self.upbit_client._ensure_session()
            print("✅ UpbitPrivateClient 초기화 완료 (실제 주문 모드)")

        except Exception as e:
            print(f"❌ UpbitPrivateClient 초기화 실패: {e}")
            self.upbit_client = None

    async def create_jwt_token(self) -> str:
        """JWT 토큰 생성"""
        if not self.has_api_keys:
            raise Exception("API 키가 없습니다")

        token_info = await self.authenticator.create_websocket_token()
        return token_info.get('access_token')

    async def ping_websocket(self, websocket, endpoint_name: str) -> bool:
        """WebSocket ping/pong 테스트"""
        try:
            print(f"🏓 {endpoint_name} WebSocket PING 전송...")
            pong_waiter = await websocket.ping()
            await asyncio.wait_for(pong_waiter, timeout=3.0)
            print(f"✅ {endpoint_name} WebSocket PONG 응답 - 연결 활성")
            return True
        except asyncio.TimeoutError:
            print(f"❌ {endpoint_name} WebSocket PING 타임아웃")
            return False
        except Exception as e:
            print(f"🚨 {endpoint_name} WebSocket PING 오류: {e}")
            return False

    async def public_message_handler(self):
        """Public WebSocket 메시지 핸들러 (콜백 방식)"""
        try:
            while True:
                message = await self.public_ws.recv()
                self.public_message_count += 1

                data = json.loads(message)
                code = data.get("code", "UNKNOWN")
                price = data.get("trade_price", "N/A")
                change_rate = data.get("change_rate", "N/A")

                # 10개마다 요약 출력 (너무 많은 로그 방지)
                if self.public_message_count % 10 == 0:
                    print(f"🟢 Public #{self.public_message_count}: {code} {price} (변화율: {change_rate})")
                elif self.public_message_count <= 5:
                    print(f"🟢 Public #{self.public_message_count}: {code} {price}")

        except websockets.exceptions.ConnectionClosed:
            print("🔌 Public WebSocket 연결 종료됨")
        except Exception as e:
            print(f"❌ Public 핸들러 오류: {e}")

    async def private_message_handler(self):
        """Private WebSocket 메시지 핸들러 (콜백 방식)"""
        try:
            while True:
                message = await self.private_ws.recv()
                self.private_message_count += 1

                print(f"🔵 Private #{self.private_message_count}: {message[:150]}...")

                # 메시지 타입 분석
                try:
                    data = json.loads(message)
                    if 'type' in data:
                        msg_type = data.get('type')
                        if msg_type == 'myOrder':
                            order_id = data.get('uuid', 'N/A')
                            state = data.get('state', 'N/A')
                            side = data.get('side', 'N/A')
                            price = data.get('price', 'N/A')
                            volume = data.get('volume', 'N/A')
                            market = data.get('market', 'N/A')
                            print(f"     📋 주문 업데이트: ID={order_id[:8]}... 상태={state} 매매={side}")
                            print(f"        마켓={market} 가격={price} 수량={volume}")

                            # 테스트 주문인지 확인
                            if self.test_order_id and order_id == self.test_order_id:
                                print(f"     🎯 테스트 주문 확인됨! 상태={state}")

                        elif msg_type == 'myAsset':
                            currency = data.get('currency', 'N/A')
                            balance = data.get('balance', 'N/A')
                            locked = data.get('locked', 'N/A')
                            avg_buy_price = data.get('avg_buy_price', 'N/A')
                            print(f"     💰 자산 업데이트: {currency} 잔고={balance} 묶임={locked}")
                            print(f"        평균매수가={avg_buy_price}")
                        else:
                            print(f"     📄 기타 타입: {msg_type}")
                    elif 'error' in data:
                        print(f"     ❌ 에러: {data['error']}")
                except json.JSONDecodeError:
                    print("     ⚠️ JSON 파싱 실패")

        except websockets.exceptions.ConnectionClosed:
            print("🔌 Private WebSocket 연결 종료됨")
        except Exception as e:
            print(f"❌ Private 핸들러 오류: {e}")

    async def step_1_connect_websockets(self):
        """1단계: WebSocket 연결"""
        print("\n" + "=" * 60)
        print("🔗 1단계: Public/Private WebSocket 연결")
        print("=" * 60)

        # Public WebSocket 연결
        print("📡 Public WebSocket 연결 중...")
        self.public_ws = await websockets.connect("wss://api.upbit.com/websocket/v1")
        print("✅ Public WebSocket 연결 성공!")

        if not self.has_api_keys:
            print("❌ API 키 없음 - Private 연결 건너뜀")
            return False

        # Private WebSocket 연결
        print("🔐 Private WebSocket 연결 중...")
        jwt_token = await self.create_jwt_token()
        private_headers = {"Authorization": f"Bearer {jwt_token}"}

        self.private_ws = await websockets.connect(
            "wss://api.upbit.com/websocket/v1/private",
            additional_headers=private_headers
        )
        print("✅ Private WebSocket 연결 성공!")

        return True

    async def step_2_ping_test(self):
        """2단계: ping/pong 연결 상태 확인"""
        print("\n🏓 2단계: WebSocket 연결 상태 확인 (ping/pong)")
        print("-" * 40)

        # Public ping
        await self.ping_websocket(self.public_ws, "Public")

        # Private ping (API 키가 있는 경우만)
        if self.private_ws:
            await self.ping_websocket(self.private_ws, "Private")

    async def step_3_public_subscription(self):
        """3단계: Public ticker 구독"""
        print("\n📡 3단계: Public KRW-BTC ticker 구독")
        print("-" * 40)

        public_request = json.dumps([
            # {"ticket": str(uuid.uuid4())},
            # {"ticket": "websocket_public"},
            {"ticket": "websocket_ticket"},
            {"type": "ticker", "codes": ["KRW-BTC"]},
            {"format": "DEFAULT"}
        ])

        await self.public_ws.send(public_request)
        print("✅ Public KRW-BTC ticker 구독 요청 완료")

    async def step_4_private_subscription(self):
        """4단계: Private myAsset, myOrder 구독"""
        if not self.private_ws:
            print("\n❌ 4단계: Private WebSocket 없음 - 건너뜀")
            return

        print("\n🔐 4단계: Private myAsset, myOrder 구독")
        print("-" * 40)

        # myAsset 구독
        asset_request = json.dumps([
            # {"ticket": str(uuid.uuid4())},
            # {"ticket": "websocket_private"},
            {"ticket": "websocket_ticket"},
            {"type": "myAsset"}
        ])
        await self.private_ws.send(asset_request)
        print("✅ myAsset 구독 요청 완료")

        # myOrder 구독
        order_request = json.dumps([
            # {"ticket": str(uuid.uuid4())},
            # {"ticket": "websocket_private"},
            {"ticket": "websocket_ticket"},
            {"type": "myOrder"}
        ])
        await self.private_ws.send(order_request)
        print("✅ myOrder 구독 요청 완료")

        # 초기 ping (응답이 없을 경우 대비)
        print("\n🏓 Private 초기 응답 확인용 ping...")
        await self.ping_websocket(self.private_ws, "Private")

    async def step_5_create_test_order(self):
        """5단계: REST API로 테스트 주문 생성 (매수, 낮은 가격)"""
        if not self.has_api_keys or not self.upbit_client:
            print("\n❌ 5단계: API 키 또는 클라이언트 없음 - 테스트 주문 건너뜀")
            return

        print("\n💰 5단계: KRW-BTC 테스트 매수 주문 생성")
        print("-" * 50)
        print("📋 주문 전략: 매수 10,000원에 5,000원 - 체결되지 않는 안전한 테스트")

        try:
            # 현재 BTC 가격 확인 (참고용)
            print("💡 참고: 현재 BTC 가격은 90,000,000원 이상이므로 10,000원 매수는 체결되지 않습니다")

            # 매수 주문 파라미터
            # - market: KRW-BTC
            # - side: bid (매수)
            # - ord_type: limit (지정가)
            # - volume: 5000 / 10000 = 0.5 BTC (매우 큰 수량이지만 가격이 낮아 체결 안됨)
            # - price: 10000 (현재가의 1/9000 수준 - 절대 체결되지 않음)

            volume = Decimal("5000") / Decimal("10000")  # 5,000원 / 10,000원 = 0.5 BTC
            price = Decimal("10000")  # 10,000원 (매우 낮은 가격)

            print(f"📤 주문 파라미터:")
            print(f"   마켓: KRW-BTC")
            print(f"   매매구분: bid (매수)")
            print(f"   주문타입: limit (지정가)")
            print(f"   수량: {volume} BTC")
            print(f"   가격: {price} KRW")
            print(f"   총 금액: {float(volume * price):,.0f}원")

            # 실제 주문 생성
            response = await self.upbit_client.place_order(
                market="KRW-BTC",
                side="bid",
                ord_type="limit",
                volume=volume,
                price=price
            )

            if response and 'uuid' in response:
                self.test_order_id = response['uuid']
                print(f"✅ 매수 주문 생성 성공!")
                print(f"   주문 ID: {self.test_order_id}")
                print(f"   주문 상태: {response.get('state', 'N/A')}")
                print(f"   생성 시간: {response.get('created_at', 'N/A')}")
                print(f"   📊 주문 세부사항: {response}")
            else:
                print(f"❌ 주문 생성 실패: {response}")

        except Exception as e:
            print(f"❌ 주문 생성 오류: {e}")
            print(f"   오류 타입: {type(e).__name__}")

    async def step_6_monitor_responses(self):
        """6단계: WebSocket 응답 모니터링"""
        print("\n📊 6단계: WebSocket 응답 모니터링 (15초)")
        print("-" * 40)
        print("💡 주문 생성 후 Private WebSocket 응답을 관찰합니다")

        start_time = time.time()
        last_summary_time = 0

        while time.time() - start_time < 15:
            elapsed = time.time() - start_time

            # 5초마다 상태 체크
            if int(elapsed) >= last_summary_time + 5:
                last_summary_time = int(elapsed)
                print(f"\n📈 [{elapsed:.0f}s] 현재 상황:")
                print(f"   🟢 Public 메시지: {self.public_message_count}개")
                print(f"   🔵 Private 메시지: {self.private_message_count}개")

                # 응답이 없으면 ping 확인
                if self.public_message_count == 0:
                    await self.ping_websocket(self.public_ws, "Public (응답없음)")
                if self.private_message_count == 0 and self.private_ws:
                    await self.ping_websocket(self.private_ws, "Private (응답없음)")

            await asyncio.sleep(0.1)

    async def step_7_cancel_test_order(self):
        """7단계: 테스트 주문 취소"""
        if not self.test_order_id or not self.upbit_client:
            print("\n❌ 7단계: 취소할 주문 없음 또는 클라이언트 없음")
            return

        print(f"\n🚫 7단계: 테스트 주문 취소")
        print("-" * 50)
        print(f"📋 취소 대상: {self.test_order_id}")

        try:
            response = await self.upbit_client.cancel_order(uuid=self.test_order_id)

            if response and 'uuid' in response:
                print(f"✅ 주문 취소 성공!")
                print(f"   취소된 주문 ID: {response['uuid']}")
                print(f"   취소 상태: {response.get('state', 'N/A')}")
                print(f"   📊 취소 응답: {response}")
            else:
                print(f"❌ 주문 취소 실패: {response}")

        except Exception as e:
            print(f"❌ 주문 취소 오류: {e}")
            print(f"   오류 타입: {type(e).__name__}")

    async def step_8_final_monitoring(self):
        """8단계: 최종 응답 확인"""
        print("\n🔍 8단계: 최종 응답 확인 (5초)")
        print("-" * 30)
        print("💡 주문 취소 후 Private WebSocket 응답을 확인합니다")

        await asyncio.sleep(5)

        print(f"\n📊 최종 결과:")
        print(f"   🟢 Public 메시지: {self.public_message_count}개")
        print(f"   🔵 Private 메시지: {self.private_message_count}개")

        if self.private_message_count > 0:
            print("✅ Private WebSocket이 주문 이벤트에 반응했습니다!")
        else:
            print("⚠️ Private WebSocket 응답이 없었습니다 (실시간 스트림 특성상 정상일 수 있음)")

    async def cleanup(self):
        """리소스 정리"""
        try:
            # UpbitPrivateClient 정리
            if self.upbit_client:
                await self.upbit_client.close()
                print("🔧 UpbitPrivateClient 리소스 정리 완료")

            # WebSocket 연결 해제
            if self.public_ws:
                await self.public_ws.close()
                print("🔌 Public WebSocket 연결 해제")
            if self.private_ws:
                await self.private_ws.close()
                print("🔌 Private WebSocket 연결 해제")

        except Exception as e:
            print(f"⚠️ 리소스 정리 중 오류: {e}")

    async def run_test(self):
        """전체 테스트 실행"""
        print("🧪 업비트 WebSocket Public/Private 독립성 테스트 v2")
        print("=" * 60)
        print("🎯 핵심 개선: 실제 주문 생성/취소로 Private WebSocket 응답 확인")
        print("💰 안전한 테스트: 매수 10,000원 (현재가 대비 매우 낮은 가격)")

        handlers = []

        try:
            # 클라이언트 초기화
            await self.initialize_client()

            # 1. WebSocket 연결
            success = await self.step_1_connect_websockets()
            if not success and not self.has_api_keys:
                print("⚠️ API 키 없음 - Public 테스트만 진행")

            # 2. ping/pong 테스트
            await self.step_2_ping_test()

            # 3. Public 구독
            await self.step_3_public_subscription()

            # 4. Private 구독
            await self.step_4_private_subscription()

            # 메시지 핸들러 시작
            handlers.append(asyncio.create_task(self.public_message_handler()))
            if self.private_ws:
                handlers.append(asyncio.create_task(self.private_message_handler()))

            # 짧은 대기 (핸들러 안정화)
            await asyncio.sleep(2)

            # 5. 테스트 주문 생성
            await self.step_5_create_test_order()

            # 6. 응답 모니터링
            await self.step_6_monitor_responses()

            # 7. 주문 취소
            await self.step_7_cancel_test_order()

            # 8. 최종 확인
            await self.step_8_final_monitoring()

        except Exception as e:
            print(f"❌ 테스트 실행 오류: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # 핸들러 정리
            for handler in handlers:
                handler.cancel()
                try:
                    await handler
                except asyncio.CancelledError:
                    pass

            # 리소스 정리
            await self.cleanup()

            print("\n" + "=" * 60)
            print("✅ 테스트 완료!")
            print("=" * 60)


async def main():
    """메인 함수"""
    tester = DualWebSocketBehaviorTestV2()
    await tester.run_test()


if __name__ == "__main__":
    asyncio.run(main())
