#!/usr/bin/env python3
"""
업비트 WebSocket 빈 구독 메시지 안전성 테스트

목적: 빈 구독 메시지가 업비트 서버에서 어떻게 처리되는지 확인
위험: 서버 오류 응답 또는 연결 끊김 가능성 검증
"""

import asyncio
import json
import time
import traceback
import websockets
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TestResult:
    """테스트 결과 저장"""
    test_name: str
    success: bool
    response_received: bool
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    connection_maintained: bool = True
    response_time: Optional[float] = None


class EmptySubscriptionTester:
    """빈 구독 메시지 안전성 테스트"""

    def __init__(self):
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.upbit_ws_url = "wss://api.upbit.com/websocket/v1"
        self.test_results = []

    async def connect_websocket(self) -> bool:
        """WebSocket 연결"""
        try:
            print("🔌 업비트 WebSocket 연결 중...")
            self.websocket = await websockets.connect(self.upbit_ws_url)
            print("✅ WebSocket 연결 완료")
            return True
        except Exception as e:
            print(f"❌ WebSocket 연결 실패: {e}")
            return False

    async def send_and_check_subscription_list(
        self, initial_message: list, test_name: str
    ) -> tuple[TestResult, Optional[Dict[str, Any]]]:
        """메시지 전송 후 LIST_SUBSCRIPTIONS로 구독 상태 확인"""
        # 1. 초기 메시지 전송
        initial_result = await self.send_message_and_wait_response(initial_message, test_name)

        if not initial_result.connection_maintained:
            return initial_result, None

        # WebSocket 연결 확인
        if not self.websocket:
            return initial_result, None

        # 2. LIST_SUBSCRIPTIONS 요청
        await asyncio.sleep(0.5)  # 구독 처리 대기
        list_message = [
            {"ticket": "public"},
            {"method": "LIST_SUBSCRIPTIONS"}
        ]

        print("📋 LIST_SUBSCRIPTIONS 확인:")
        print(f"   전송: {json.dumps(list_message)}")

        try:
            await self.websocket.send(json.dumps(list_message))

            # LIST_SUBSCRIPTIONS 응답만 대기 (ticker 메시지 무시)
            for _ in range(5):  # 최대 5번 시도
                try:
                    response = await asyncio.wait_for(self.websocket.recv(), timeout=3.0)
                    response_data = json.loads(response)

                    # LIST_SUBSCRIPTIONS 응답인지 확인
                    if response_data.get("method") == "LIST_SUBSCRIPTIONS":
                        print("✅ LIST_SUBSCRIPTIONS 응답:")
                        print(f"   {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                        return initial_result, response_data
                    else:
                        # ticker 메시지 등은 무시
                        print(f"   🎯 기타 메시지 무시: {response_data.get('type', 'unknown')}")
                        continue

                except asyncio.TimeoutError:
                    print("   ⏰ LIST_SUBSCRIPTIONS 응답 타임아웃")
                    break

        except Exception as e:
            print(f"   ❌ LIST_SUBSCRIPTIONS 오류: {e}")

        return initial_result, None

    async def send_message_and_wait_response(self, message: list, test_name: str, timeout: float = 5.0) -> TestResult:
        """메시지 전송 및 응답 대기"""
        if not self.websocket:
            return TestResult(
                test_name=test_name,
                success=False,
                response_received=False,
                error_message="WebSocket 연결 없음"
            )

        try:
            # 메시지 전송
            message_json = json.dumps(message)
            print(f"\n📤 {test_name}")
            print(f"   전송: {message_json}")

            start_time = time.time()
            await self.websocket.send(message_json)

            # 응답 대기
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
                response_time = time.time() - start_time
                response_data = json.loads(response)

                print(f"✅ 응답 수신 ({response_time:.3f}초):")
                print(f"   응답: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

                # 에러 응답 확인
                is_error = (
                    "error" in response_data
                    or "code" in response_data
                    or response_data.get("status") == "error"
                )

                return TestResult(
                    test_name=test_name,
                    success=not is_error,
                    response_received=True,
                    response_data=response_data,
                    response_time=response_time,
                    connection_maintained=True
                )

            except asyncio.TimeoutError:
                print(f"⏰ 응답 타임아웃 ({timeout}초)")
                return TestResult(
                    test_name=test_name,
                    success=True,  # 타임아웃은 에러가 아님
                    response_received=False,
                    connection_maintained=True
                )

        except websockets.exceptions.ConnectionClosed:
            print("❌ WebSocket 연결이 서버에 의해 끊어짐")
            return TestResult(
                test_name=test_name,
                success=False,
                response_received=False,
                error_message="연결 끊어짐",
                connection_maintained=False
            )
        except Exception as e:
            print(f"❌ 메시지 전송 오류: {e}")
            return TestResult(
                test_name=test_name,
                success=False,
                response_received=False,
                error_message=str(e)
            )

    async def test_empty_subscription_messages(self):
        """다양한 빈 구독 메시지 테스트"""
        test_cases = [
            {
                "name": "현재 시스템 빈 구독 (ticket + format)",
                "message": [
                    {"ticket": "public"},
                    {"format": "DEFAULT"}
                ]
            },
            {
                "name": "완전 빈 구독 (ticket만)",
                "message": [
                    {"ticket": "public"}
                ]
            },
            {
                "name": "빈 codes 배열",
                "message": [
                    {"ticket": "public"},
                    {"type": "ticker", "codes": []},
                    {"format": "DEFAULT"}
                ]
            },
            # 🧪 연결 끊김 조건 정밀 분석
            {
                "name": "잘못된 타입 - invalid_type",
                "message": [
                    {"ticket": "public"},
                    {"type": "invalid_type", "codes": ["KRW-BTC"]},
                    {"format": "DEFAULT"}
                ]
            },
            {
                "name": "잘못된 타입 - wrong_type",
                "message": [
                    {"ticket": "public"},
                    {"type": "wrong_type", "codes": ["KRW-BTC"]},
                    {"format": "DEFAULT"}
                ]
            },
            {
                "name": "잘못된 타입 - 빈 문자열",
                "message": [
                    {"ticket": "public"},
                    {"type": "", "codes": ["KRW-BTC"]},
                    {"format": "DEFAULT"}
                ]
            },
            {
                "name": "잘못된 타입 - 숫자",
                "message": [
                    {"ticket": "public"},
                    {"type": 123, "codes": ["KRW-BTC"]},
                    {"format": "DEFAULT"}
                ]
            },
            {
                "name": "타입 필드 없음",
                "message": [
                    {"ticket": "public"},
                    {"codes": ["KRW-BTC"]},
                    {"format": "DEFAULT"}
                ]
            },
            {
                "name": "잘못된 codes - 문자열",
                "message": [
                    {"ticket": "public"},
                    {"type": "ticker", "codes": "KRW-BTC"},
                    {"format": "DEFAULT"}
                ]
            },
            {
                "name": "잘못된 심볼",
                "message": [
                    {"ticket": "public"},
                    {"type": "ticker", "codes": ["INVALID-SYMBOL"]},
                    {"format": "DEFAULT"}
                ]
            },
            {
                "name": "정상 구독 (비교용)",
                "message": [
                    {"ticket": "public"},
                    {"type": "ticker", "codes": ["KRW-BTC"]},
                    {"format": "DEFAULT"}
                ]
            }
        ]

        for test_case in test_cases:
            # 각 테스트 전 연결 상태 확인
            if not self.websocket:
                print("\n🔄 WebSocket 재연결 필요")
                if not await self.connect_websocket():
                    print("❌ 재연결 실패, 테스트 중단")
                    break

            # 특별 처리: "완전 빈 구독 (ticket만)" 케이스는 LIST_SUBSCRIPTIONS 체크
            if "완전 빈 구독 (ticket만)" in test_case["name"]:
                result, list_response = await self.send_and_check_subscription_list(
                    test_case["message"],
                    test_case["name"]
                )
                # LIST_SUBSCRIPTIONS 응답을 결과에 저장
                if list_response:
                    result.response_data = list_response
                    result.response_received = True
            else:
                result = await self.send_message_and_wait_response(
                    test_case["message"],
                    test_case["name"]
                )

            self.test_results.append(result)

            # 연결이 끊어진 경우 재연결
            if not result.connection_maintained:
                print("🔄 연결 끊어짐, 재연결 시도...")
                await asyncio.sleep(1)
                if not await self.connect_websocket():
                    print("❌ 재연결 실패")
                    break
            else:
                # 다음 테스트 전 잠시 대기
                await asyncio.sleep(1)

    def analyze_results(self):
        """테스트 결과 분석"""
        print("\n" + "=" * 80)
        print("📊 빈 구독 메시지 안전성 분석 결과")
        print("=" * 80)

        for result in self.test_results:
            print(f"\n🧪 {result.test_name}")
            print(f"   성공: {'✅' if result.success else '❌'}")
            print(f"   응답: {'✅' if result.response_received else '⏰'}")
            print(f"   연결: {'✅' if result.connection_maintained else '❌'}")

            if result.response_time:
                print(f"   응답시간: {result.response_time:.3f}초")

            if result.error_message:
                print(f"   오류: {result.error_message}")

            # LIST_SUBSCRIPTIONS 응답 분석
            if result.response_data and result.response_data.get("method") == "LIST_SUBSCRIPTIONS":
                subscriptions = result.response_data.get("result", [])
                print(f"   📋 구독 리스트: {len(subscriptions)}개")
                if subscriptions:
                    for sub in subscriptions:
                        codes = sub.get("codes", [])
                        print(f"      - {sub.get('type', 'unknown')}: {codes}")

        print("\n" + "=" * 50)
        print("🔍 핵심 발견사항:")

        # 빈 구독 메시지 안전성 평가
        empty_subscription_result = next(
            (r for r in self.test_results if "현재 시스템 빈 구독" in r.test_name),
            None
        )

        if empty_subscription_result:
            if empty_subscription_result.success and empty_subscription_result.connection_maintained:
                print("  ✅ 현재 빈 구독 메시지는 안전함")
                print("  📊 서버가 정상적으로 처리하거나 무시함")
            else:
                print("  ⚠️ 현재 빈 구독 메시지가 위험할 수 있음")
                if not empty_subscription_result.connection_maintained:
                    print("  🚨 서버가 연결을 끊었음 - 빈 구독 로직 수정 필요")

        # 빈 구독 후 LIST_SUBSCRIPTIONS 결과 분석
        ticket_only_result = next(
            (r for r in self.test_results if "완전 빈 구독 (ticket만)" in r.test_name),
            None
        )

        if ticket_only_result and ticket_only_result.response_data:
            list_data = ticket_only_result.response_data
            subscriptions = list_data.get("result", [])
            print("\n  🎫 티켓만 전송 후 서버 인식:")
            if not subscriptions:
                print("    📋 구독 리스트: 비어있음 (서버가 빈 구독으로 인식하지 않음)")
            else:
                print(f"    📋 구독 리스트: {len(subscriptions)}개 등록됨")
                for sub in subscriptions:
                    codes = sub.get("codes", [])
                    print(f"       - {sub.get('type', 'unknown')}: {codes}")
                print("    ⚠️ 예상치 못한 구독 등록 - 빈 구독 로직 재검토 필요")

        # 연결 안정성 평가
        connection_breaks = sum(1 for r in self.test_results if not r.connection_maintained)
        if connection_breaks > 0:
            print(f"  ⚠️ {connection_breaks}개 테스트에서 연결 끊어짐")
            print("  🔧 빈 구독 대신 기본 구독 또는 무연결 상태 유지 권장")
        else:
            print("  ✅ 모든 테스트에서 연결 유지됨")

        print("\n💡 권장사항:")
        if empty_subscription_result and empty_subscription_result.success:
            print("  🎯 현재 빈 구독 로직 유지 가능")
        else:
            print("  🛠️ 빈 구독 대신 다음 대안 고려:")
            print("     1. 기본 심볼(KRW-BTC) 구독")
            print("     2. 빈 구독 로직 완전 제거")
            print("     3. 연결만 유지하고 구독하지 않음")

    async def run_safety_test(self):
        """전체 안전성 테스트 실행"""
        try:
            print("🚀 업비트 WebSocket 빈 구독 안전성 테스트")
            print("=" * 80)
            print("🎯 목적: 빈 구독 메시지의 서버 응답 및 연결 안정성 확인")
            print("⚠️  주의: 일부 테스트에서 연결이 끊어질 수 있습니다")
            print("=" * 80)

            # WebSocket 연결
            if not await self.connect_websocket():
                print("❌ 초기 연결 실패")
                return

            # 빈 구독 메시지 테스트
            await self.test_empty_subscription_messages()

            # 결과 분석
            self.analyze_results()

        except Exception as e:
            print(f"❌ 테스트 실행 오류: {e}")
            traceback.print_exc()
        finally:
            if self.websocket:
                await self.websocket.close()
                print("\n🔌 WebSocket 연결 종료")


async def main():
    """메인 실행 함수"""
    tester = EmptySubscriptionTester()
    await tester.run_safety_test()


if __name__ == "__main__":
    asyncio.run(main())
