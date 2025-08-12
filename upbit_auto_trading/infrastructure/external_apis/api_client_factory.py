from typing import Optional
import os

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_client import UpbitClient

class ApiClientFactory:
    """API 클라이언트 팩토리"""

    @staticmethod
    def create_upbit_client(access_key: Optional[str] = None,
                            secret_key: Optional[str] = None) -> UpbitClient:
        """Upbit 클라이언트 생성"""
        # 환경변수에서 API 키 로드 (파라미터가 없을 경우)
        if access_key is None:
            access_key = os.getenv('UPBIT_ACCESS_KEY')
        if secret_key is None:
            secret_key = os.getenv('UPBIT_SECRET_KEY')

        return UpbitClient(access_key, secret_key)

    @staticmethod
    def create_public_only_client() -> UpbitClient:
        """공개 API 전용 클라이언트 생성"""
        return UpbitClient()
