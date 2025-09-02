#!/usr/bin/env python3
"""
업비트 WebSocket API 동작 검증 데모
====================================

목적:
1. Public vs Private 엔드포인트 연결 테스트
2. Private 연결에서 Public 데이터 요청 가능 여부 확인
3. 인증 헤더 설정 방식 검증
4. JWT 토큰 검증 (실제 upbit_auth.py 사용)
"""

import asyncio
import json
import os
import sys
import time
import uuid
from typing import Optional, Dict, Any

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    print("❌ websockets 라이브러리가 설치되지 않았습니다.")
    print("pip install websockets 로 설치해주세요.")
    WEBSOCKETS_AVAILABLE = False
    exit(1)

# 실제 upbit_auth.py 임포트
try:
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator, AuthenticationError
    UPBIT_AUTH_AVAILABLE = True
except ImportError as e:
    print(f"❌ upbit_auth.py 임포트 실패: {e}")
    UPBIT_AUTH_AVAILABLE = False
    exit(1)


class UpbitWebSocketDemo:
    """업비트 WebSocket API 검증 데모 (실제 UpbitAuthenticator 사용)"""

    # 업비트 WebSocket 엔드포인트
    PUBLIC_URL = "wss://api.upbit.com/websocket/v1"
    PRIVATE_URL = "wss://api.upbit.com/websocket/v1/private"

    def __init__(self):
        # 실제 UpbitAuthenticator 사용
        self.authenticator = UpbitAuthenticator()
        self.has_api_keys = self.authenticator.is_authenticated()

    async def create_jwt_token(self) -> Optional[str]:
        """업비트 JWT 토큰 생성 (실제 UpbitAuthenticator 사용)"""
        if not self.has_api_keys:
            return None

        try:
            token_info = await self.authenticator.create_websocket_token()
            return token_info.get('access_token')

        except Exception as e:
            print(f"❌ JWT 토큰 생성 실패: {e}")
            return None

    def create_ticker_request(self) -> str:
        """KRW-BTC 현재가 요청 메시지 생성"""
        return json.dumps([
            {"ticket": str(uuid.uuid4())},
            {"type": "ticker", "codes": ["KRW-BTC"]},
            {"format": "DEFAULT"}
        ])

    def create_myasset_request(self) -> str:
        """내 자산 요청 메시지 생성 (Private 전용)"""
        return json.dumps([
            {"ticket": str(uuid.uuid4())},
            {"type": "myAsset"}
        ])

    async def test_public_connection(self):
        """Public 엔드포인트 연결 테스트"""
        print("\n" + "="*60)
        print("🔍 테스트 1: Public 엔드포인트 연결")
        print(f"URL: {self.PUBLIC_URL}")
        print("="*60)

        try:
            async with websockets.connect(self.PUBLIC_URL) as websocket:
                print("✅ Public 연결 성공!")

                # KRW-BTC 현재가 요청
                request = self.create_ticker_request()
                print(f"📤 요청: {request}")

                await websocket.send(request)

                # 응답 수신 (최대 5초 대기)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"📥 응답: {response[:200]}...")
                    print("✅ Public 데이터 수신 성공!")

                except asyncio.TimeoutError:
                    print("⚠️ 응답 타임아웃")

        except Exception as e:
            print(f"❌ Public 연결 실패: {e}")

    async def test_private_connection_no_auth(self):
        """Private 엔드포인트 인증 없이 연결 테스트"""
        print("\n" + "="*60)
        print("🔍 테스트 2: Private 엔드포인트 (인증 없음)")
        print(f"URL: {self.PRIVATE_URL}")
        print("="*60)

        try:
            async with websockets.connect(self.PRIVATE_URL) as websocket:
                print("✅ Private 연결 성공! (인증 없음)")

                # Public 데이터 요청 가능한지 테스트
                request = self.create_ticker_request()
                print(f"📤 Public 데이터 요청: {request}")

                await websocket.send(request)

                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"📥 응답: {response[:200]}...")
                    print("✅ Private 엔드포인트에서 Public 데이터 수신 성공!")

                except asyncio.TimeoutError:
                    print("⚠️ 응답 타임아웃")

        except Exception as e:
            print(f"❌ Private 연결 실패 (인증 없음): {e}")

    async def test_private_connection_with_auth(self):
        """Private 엔드포인트 JWT 인증과 함께 연결 테스트"""
        print("\n" + "="*60)
        print("🔍 테스트 3: Private 엔드포인트 (JWT 인증)")
        print(f"URL: {self.PRIVATE_URL}")

        if not self.has_api_keys:
            print("⚠️ API 키가 설정되지 않음 - 테스트 건너뛰기")
            print("DB 또는 환경변수에 API 키 설정 필요")
            return

        print(f"✅ API 키 감지됨 (UpbitAuthenticator)")
        print("="*60)

        # JWT 토큰 생성
        jwt_token = await self.create_jwt_token()
        if not jwt_token:
            print("❌ JWT 토큰 생성 실패")
            return

        print(f"🔐 JWT 토큰: {jwt_token[:50]}...")        # 인증 헤더 설정
        headers = {"Authorization": f"Bearer {jwt_token}"}

        try:
            # additional_headers vs extra_headers 호환성 테스트
            websocket = None
            connection_method = None

            try:
                websocket = await websockets.connect(
                    self.PRIVATE_URL,
                    additional_headers=headers
                )
                connection_method = "additional_headers"
            except TypeError:
                try:
                    websocket = await websockets.connect(
                        self.PRIVATE_URL,
                        extra_headers=headers
                    )
                    connection_method = "extra_headers"
                except Exception as e2:
                    print(f"❌ 헤더 설정 방식 모두 실패: {e2}")
                    return

            print(f"✅ Private 연결 성공! (헤더 방식: {connection_method})")

            async with websocket:
                # 1. Public 데이터 요청
                print("\n--- Public 데이터 요청 테스트 ---")
                request = self.create_ticker_request()
                print(f"📤 Public 요청: {request}")

                await websocket.send(request)

                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"📥 Public 응답: {response[:200]}...")
                    print("✅ Private 연결에서 Public 데이터 수신 성공!")

                except asyncio.TimeoutError:
                    print("⚠️ Public 데이터 응답 타임아웃")

                # 2. Private 데이터 요청
                print("\n--- Private 데이터 요청 테스트 ---")
                private_request = self.create_myasset_request()
                print(f"📤 Private 요청: {private_request}")

                await websocket.send(private_request)

                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"📥 Private 응답: {response[:200]}...")
                    print("✅ Private 데이터 수신 성공!")

                except asyncio.TimeoutError:
                    print("⚠️ Private 데이터 응답 타임아웃")

        except Exception as e:
            print(f"❌ Private 연결 실패 (JWT 인증): {e}")

    async def test_websockets_library_info(self):
        """websockets 라이브러리 정보 확인"""
        print("\n" + "="*60)
        print("🔍 라이브러리 정보")
        print("="*60)

        print(f"websockets 버전: {getattr(websockets, '__version__', 'Unknown')}")
        print(f"UpbitAuthenticator: {self.authenticator.__class__.__name__}")
        print(f"API 키 상태: {'✅ 인증됨' if self.has_api_keys else '❌ 미설정'}")

        # connect 함수의 시그니처 확인
        import inspect
        sig = inspect.signature(websockets.connect)
        params = list(sig.parameters.keys())
        print(f"websockets.connect 파라미터: {params}")

    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 업비트 WebSocket API 검증 데모 시작")
        print(f"⏰ 시작 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        await self.test_websockets_library_info()
        await self.test_public_connection()
        await self.test_private_connection_no_auth()
        await self.test_private_connection_with_auth()

        print("\n" + "="*60)
        print("✅ 모든 테스트 완료!")
        print("="*60)


async def main():
    """메인 실행 함수"""
    demo = UpbitWebSocketDemo()
    await demo.run_all_tests()


if __name__ == "__main__":
    if not WEBSOCKETS_AVAILABLE or not UPBIT_AUTH_AVAILABLE:
        exit(1)

    asyncio.run(main())
