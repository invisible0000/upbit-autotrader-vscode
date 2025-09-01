"""
API 키 로딩 디버깅 테스트
"""

import asyncio
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_private_client import UpbitPrivateClient


async def test_api_key_loading():
    """API 키 로딩 과정 디버깅"""
    print("🔧 API 키 로딩 테스트 시작")

    # 1. 직접 키 없이 클라이언트 생성 (ApiKeyService에서 로드 시도)
    print("\n1. ApiKeyService에서 키 로드 시도...")
    client = UpbitPrivateClient()

    # 2. 인증 상태 확인
    print(f"   인증 상태: {client.is_authenticated()}")
    print(f"   DRY-RUN 모드: {client.is_dry_run_enabled()}")

    # 3. 클라이언트 정보 출력
    print(f"   클라이언트 정보: {repr(client)}")

    await client.close()
    print("\n✅ 테스트 완료")


if __name__ == "__main__":
    asyncio.run(test_api_key_loading())
