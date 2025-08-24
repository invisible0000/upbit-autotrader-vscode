#!/usr/bin/env python
"""
업비트 API 키 설정 도구

20,000원 범위 내에서 실제 거래 테스트를 위한 API 키 설정
"""

import sys
import getpass
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from upbit_auto_trading.infrastructure.services.api_key_service import ApiKeyService
from upbit_auto_trading.infrastructure.configuration import get_path_service
from upbit_auto_trading.infrastructure.repositories.secure_keys_repository import SecureKeysRepository


def main():
    """API 키 설정 메인 함수"""
    print("🔐 업비트 API 키 설정 도구")
    print("=" * 50)
    print("20,000원 범위 내 실제 거래 테스트를 위한 API 키 설정")
    print()

    try:
        # Repository와 ApiKeyService 초기화
        repository = SecureKeysRepository()
        api_service = ApiKeyService(repository)

        # 기존 키 확인
        if api_service.has_valid_keys():
            print("🔍 기존 API 키 발견됨")
            choice = input("기존 키를 삭제하고 새로 설정하시겠습니까? (y/N): ").strip().lower()
            if choice == 'y':
                if api_service.delete_api_keys():
                    print("✅ 기존 키 삭제 완료")
                else:
                    print("❌ 기존 키 삭제 실패")
                    return
            else:
                print("기존 키를 유지합니다.")
                # 기존 키로 연결 테스트
                print("\n🔍 기존 키로 연결 테스트 중...")
                saved_keys = api_service.load_api_keys()
                if saved_keys and len(saved_keys) >= 2 and saved_keys[0] and saved_keys[1]:
                    access_key, secret_key, _ = saved_keys
                    success, message, account_info = api_service.test_api_connection(access_key, secret_key)
                    if success:
                        print(f"✅ {message}")
                        if 'total_krw' in account_info:
                            print(f"💰 KRW 잔고: {account_info['total_krw']:,.0f}원")
                    else:
                        print(f"❌ {message}")
                else:
                    print("❌ 저장된 키를 불러올 수 없습니다.")
                return

        # 새 API 키 입력
        print("\n📝 새 API 키 입력")
        print("업비트 마이페이지 > Open API 관리에서 발급받은 키를 입력하세요.")
        print("⚠️  보안을 위해 입력 시 화면에 표시되지 않습니다.")
        print()

        access_key = getpass.getpass("Access Key: ").strip()
        secret_key = getpass.getpass("Secret Key: ").strip()

        if not access_key or not secret_key:
            print("❌ API 키가 비어있습니다.")
            return

        # 거래 권한 확인
        print("\n🔐 거래 권한 설정")
        trade_permission = input("거래 권한을 허용하시겠습니까? (실제 주문 가능) (y/N): ").strip().lower() == 'y'

        # API 키 저장
        print("\n💾 API 키 저장 중...")
        if api_service.save_api_keys(access_key, secret_key, trade_permission):
            print("✅ API 키 저장 완료")

            # 연결 테스트
            print("\n🔍 API 연결 테스트 중...")
            success, message, account_info = api_service.test_api_connection(access_key, secret_key)

            if success:
                print(f"✅ {message}")
                if 'total_krw' in account_info:
                    krw_balance = account_info['total_krw']
                    print(f"💰 KRW 잔고: {krw_balance:,.0f}원")

                    if krw_balance >= 5000:
                        print("✅ 최소 주문 금액(5,000원) 이상 보유 - 실제 거래 테스트 가능")
                    else:
                        print("⚠️ 최소 주문 금액(5,000원) 미만 - 조회 테스트만 가능")

                print("\n🎉 API 키 설정 완료! 이제 실제 거래 테스트를 진행할 수 있습니다.")
                print("다음 명령어로 테스트를 실행하세요:")
                print("pytest tests\\external_apis\\upbit\\test_upbit_private_client\\"
                      "test_accounts.py::TestUpbitPrivateClientAccountsReal -v -s")

            else:
                print(f"❌ 연결 테스트 실패: {message}")
                print("API 키를 다시 확인해주세요.")
        else:
            print("❌ API 키 저장 실패")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
