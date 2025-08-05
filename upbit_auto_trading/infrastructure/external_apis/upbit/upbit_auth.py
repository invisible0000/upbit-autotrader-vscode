import jwt  # type: ignore
import hashlib
import uuid
from urllib.parse import urlencode
from typing import Dict, Optional
import os
import logging

from upbit_auto_trading.infrastructure.external_apis.common.api_client_base import (
    AuthenticationError
)


class UpbitAuthenticator:
    """Upbit API 인증 처리 - 기존 _get_auth_header 로직 기반"""

    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Args:
            access_key: Upbit API Access Key (None이면 환경변수에서 로드)
            secret_key: Upbit API Secret Key (None이면 환경변수에서 로드)
        """
        self._access_key = access_key or os.getenv('UPBIT_ACCESS_KEY')
        self._secret_key = secret_key or os.getenv('UPBIT_SECRET_KEY')
        self._logger = logging.getLogger(__name__)

        if not self._access_key or not self._secret_key:
            self._logger.warning("Upbit API 키가 설정되지 않았습니다. 공개 API만 사용 가능합니다.")

    def is_authenticated(self) -> bool:
        """인증 정보 설정 여부 확인"""
        return bool(self._access_key and self._secret_key)

    def create_jwt_token(self, query_params: Optional[Dict] = None,
                         request_body: Optional[Dict] = None) -> str:
        """JWT 토큰 생성 - 기존 _get_auth_header 로직 기반"""
        if not self.is_authenticated():
            raise AuthenticationError("API 키가 설정되지 않았습니다")

        payload = {
            'access_key': self._access_key,
            'nonce': str(uuid.uuid4())
        }

        # 쿼리 파라미터 해시 추가 (기존 로직 보존)
        if query_params:
            query_string = urlencode(query_params, doseq=True).encode()
            m = hashlib.sha512()
            m.update(query_string)
            payload['query_hash'] = m.hexdigest()
            payload['query_hash_alg'] = 'SHA512'

        # 요청 본문 해시 추가 (POST/DELETE 요청용)
        if request_body:
            import json
            body_string = json.dumps(request_body, separators=(',', ':')).encode()
            m = hashlib.sha512()
            m.update(body_string)
            payload['query_hash'] = m.hexdigest()
            payload['query_hash_alg'] = 'SHA512'

        try:
            # 기존 jwt.encode 호출 방식 보존
            token = jwt.encode(payload, self._secret_key, algorithm='HS256')
            return f'Bearer {token}'
        except Exception as e:
            self._logger.error(f"JWT 토큰 생성 실패: {e}")
            raise AuthenticationError(f"JWT 토큰 생성 실패: {e}")

    def get_public_headers(self) -> Dict[str, str]:
        """공개 API용 헤더"""
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def get_private_headers(self, query_params: Optional[Dict] = None,
                            request_body: Optional[Dict] = None) -> Dict[str, str]:
        """인증 API용 헤더"""
        headers = self.get_public_headers()

        if self.is_authenticated():
            headers['Authorization'] = self.create_jwt_token(query_params, request_body)

        return headers
