"""
API 키 유틸리티 - 테스트용 API 키 로드
암호화된 키와 .env 파일에서 API 키를 안전하게 로드
"""

import json
from pathlib import Path
from typing import Tuple, Optional
from cryptography.fernet import Fernet


class ApiKeyLoader:
    """테스트용 API 키 로더"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.secure_dir = self.project_root / "config" / "secure"
        self.env_file = self.project_root / ".env"
        print(f"🔍 프로젝트 루트: {self.project_root}")
        print(f"🔍 .env 파일 경로: {self.env_file}")
        print(f"🔍 보안 디렉토리: {self.secure_dir}")

    def load_from_env(self) -> Tuple[Optional[str], Optional[str]]:
        """
        .env 파일에서 API 키 로드

        Returns:
            tuple: (access_key, secret_key) 또는 (None, None)
        """
        try:
            if not self.env_file.exists():
                return None, None

            access_key = None
            secret_key = None

            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('UPBIT_ACCESS_KEY='):
                        access_key = line.split('=', 1)[1]
                    elif line.startswith('UPBIT_SECRET_KEY='):
                        secret_key = line.split('=', 1)[1]

            return access_key, secret_key

        except Exception as e:
            print(f"⚠️ .env 파일에서 API 키 로드 실패: {e}")
            return None, None

    def load_from_encrypted(self) -> Tuple[Optional[str], Optional[str]]:
        """
        암호화된 파일에서 API 키 로드

        Returns:
            tuple: (access_key, secret_key) 또는 (None, None)
        """
        try:
            encryption_key_path = self.secure_dir / "encryption_key.key"
            api_credentials_path = self.secure_dir / "api_credentials.json"

            if not encryption_key_path.exists() or not api_credentials_path.exists():
                return None, None

            # 암호화 키 로드
            with open(encryption_key_path, "rb") as f:
                encryption_key = f.read()

            fernet = Fernet(encryption_key)

            # 암호화된 API 키 로드
            with open(api_credentials_path, "r", encoding='utf-8') as f:
                settings = json.load(f)

            access_key = None
            secret_key = None

            if "access_key" in settings:
                access_key = fernet.decrypt(settings["access_key"].encode('utf-8')).decode('utf-8')
            if "secret_key" in settings:
                secret_key = fernet.decrypt(settings["secret_key"].encode('utf-8')).decode('utf-8')

            return access_key, secret_key

        except Exception as e:
            print(f"⚠️ 암호화된 파일에서 API 키 로드 실패: {e}")
            return None, None

    def get_api_keys(self) -> Tuple[Optional[str], Optional[str]]:
        """
        API 키 로드 - 우선순위: .env > 암호화 파일

        Returns:
            tuple: (access_key, secret_key) 또는 (None, None)
        """
        # 1순위: .env 파일 (개발용)
        access_key, secret_key = self.load_from_env()
        if access_key and secret_key:
            print("✅ .env 파일에서 API 키 로드 성공")
            return access_key, secret_key

        # 2순위: 암호화된 파일 (보안용)
        access_key, secret_key = self.load_from_encrypted()
        if access_key and secret_key:
            print("✅ 암호화된 파일에서 API 키 로드 성공")
            return access_key, secret_key

        print("❌ 사용 가능한 API 키를 찾을 수 없습니다")
        return None, None


# 테스트용 전역 함수
def get_test_api_keys() -> Tuple[Optional[str], Optional[str]]:
    """테스트에서 사용할 API 키 조회"""
    loader = ApiKeyLoader()
    return loader.get_api_keys()


if __name__ == "__main__":
    # 테스트 실행
    loader = ApiKeyLoader()

    print("🔍 API 키 로드 테스트")
    print("=" * 50)

    # .env 파일 테스트
    env_access, env_secret = loader.load_from_env()
    print(f"📄 .env 파일: {'✅ 성공' if env_access and env_secret else '❌ 실패'}")
    if env_access:
        print(f"   Access Key: {env_access[:10]}...{env_access[-4:]}")

    # 암호화 파일 테스트
    enc_access, enc_secret = loader.load_from_encrypted()
    print(f"🔐 암호화 파일: {'✅ 성공' if enc_access and enc_secret else '❌ 실패'}")
    if enc_access:
        print(f"   Access Key: {enc_access[:10]}...{enc_access[-4:]}")

    # 통합 로드 테스트
    final_access, final_secret = loader.get_api_keys()
    print(f"🎯 최종 선택: {'✅ 성공' if final_access and final_secret else '❌ 실패'}")
