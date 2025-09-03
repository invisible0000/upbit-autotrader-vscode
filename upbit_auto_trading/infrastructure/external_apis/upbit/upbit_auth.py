import jwt  # type: ignore
import hashlib
import uuid
from urllib.parse import urlencode
from typing import Dict, Optional, Any
import os
import logging


class AuthenticationError(Exception):
    """인증 관련 오류"""
    pass


class UpbitAuthenticator:
    """Upbit API 인증 처리 - ApiKeyService 연동"""

    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Args:
            access_key: Upbit API Access Key (직접 제공된 경우)
            secret_key: Upbit API Secret Key (직접 제공된 경우)
        """
        self._access_key = access_key
        self._secret_key = secret_key
        self._logger = logging.getLogger(__name__)

        # ApiKeyService에서 키를 로드 시도 (직접 키가 제공되지 않은 경우)
        if not self._access_key or not self._secret_key:
            self._load_keys_from_service()

    def _load_keys_from_service(self):
        """ApiKeyService에서 API 키 로드"""
        try:
            self._logger.debug("🔄 ApiKeyService에서 API 키 로드 시도 중...")

            from upbit_auto_trading.infrastructure.services.api_key_service import ApiKeyService
            from upbit_auto_trading.infrastructure.repositories.sqlite_secure_keys_repository import SqliteSecureKeysRepository
            from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

            # DatabaseManager와 Repository 인스턴스 생성
            db_paths = {
                'settings': 'data/settings.sqlite3',
                'strategies': 'data/strategies.sqlite3',
                'market_data': 'data/market_data.sqlite3'
            }
            db_manager = DatabaseManager(db_paths)
            repository = SqliteSecureKeysRepository(db_manager)
            api_key_service = ApiKeyService(repository)

            self._logger.debug("🔧 ApiKeyService 인스턴스 생성 완료")

            # 저장된 키 로드
            access_key, secret_key, trade_permission = api_key_service.load_api_keys()
            access_status = '존재' if access_key else '없음'
            secret_status = '존재' if secret_key else '없음'
            self._logger.debug(f"🔍 로드된 키 상태: access_key={access_status}, secret_key={secret_status}")

            if access_key and secret_key:
                self._access_key = access_key
                self._secret_key = secret_key
                self._logger.info("✅ ApiKeyService에서 Upbit API 키 로드 성공")
            else:
                self._logger.warning("⚠️ ApiKeyService에서 유효한 API 키를 찾을 수 없습니다")

        except Exception as e:
            self._logger.error(f"❌ ApiKeyService에서 키 로드 실패: {e}")
            self._logger.debug(f"❌ 상세 오류: {str(e)}", exc_info=True)
            # 환경변수 fallback (기존 동작 유지)
            self._access_key = self._access_key or os.getenv('UPBIT_ACCESS_KEY')
            self._secret_key = self._secret_key or os.getenv('UPBIT_SECRET_KEY')

        if not self._access_key or not self._secret_key:
            self._logger.info("ℹ️ Upbit API 키가 설정되지 않았습니다. 공개 API만 사용 가능합니다.")

    def is_authenticated(self) -> bool:
        """인증 정보 설정 여부 확인"""
        return bool(self._access_key and self._secret_key)

    def create_jwt_token(self, query_params: Optional[Dict] = None,
                         request_body: Optional[Dict] = None) -> str:
        """JWT 토큰 생성 - 업비트 공식 예제 방식"""
        if not self.is_authenticated():
            raise AuthenticationError("API 키가 설정되지 않았습니다")

        # 강제 콘솔 출력으로 JWT 요청 추적
        self._logger.debug("JWT 생성 요청:")
        self._logger.debug(f"   query_params: {query_params}")
        self._logger.debug(f"   request_body: {request_body}")

        payload = {
            'access_key': self._access_key,
            'nonce': str(uuid.uuid4())
        }

        # 쿼리스트링 생성 및 해시 추가
        query_string_data = {}

        # GET 요청의 쿼리 파라미터
        if query_params:
            query_string_data.update(query_params)

        # POST 요청의 body 데이터 (업비트 공식 방식: body를 query_string으로 처리)
        if request_body:
            query_string_data.update(request_body)

        # 쿼리스트링이 있으면 해시 생성
        if query_string_data:
            # 업비트 JWT 검증 이슈 해결: []를 URL 인코딩하지 않고 직접 구성
            query_string = urlencode(query_string_data, doseq=True)

            # []가 %5B%5D로 인코딩된 경우 원래대로 복원
            query_string = query_string.replace('%5B%5D', '[]')
            query_string = query_string.encode()

            # JWT 검증을 위한 URL 인코딩에서 []를 제외하고 처리
            self._logger.debug("JWT Debug - 요청 분석:")
            self._logger.debug(f"   query_string_data: {query_string_data}")
            self._logger.debug(f"   encoded query_string: {query_string.decode('utf-8')}")

            m = hashlib.sha512()
            m.update(query_string)
            payload['query_hash'] = m.hexdigest()
            payload['query_hash_alg'] = 'SHA512'

            # JWT 해시 값 로깅
            self._logger.debug(f"   query_hash: {payload['query_hash'][:32]}...")

        else:
            # 쿼리 파라미터가 없는 경우
            self._logger.debug("JWT Debug - 쿼리 파라미터 없음")

        try:
            # 타입 안전성 확인
            if not self._secret_key:
                raise AuthenticationError("Secret key is None")

            # JWT 토큰 생성 (업비트 공식 권장: HS512 알고리즘)
            token = jwt.encode(payload, self._secret_key, algorithm='HS512')
            return token  # Bearer 접두사 제거 (헤더에서 추가)
        except Exception as e:
            self._logger.error(f"JWT 토큰 생성 실패: {e}")
            raise AuthenticationError(f"JWT 토큰 생성 실패: {e}")

    async def create_websocket_token(self) -> Dict[str, Any]:
        """WebSocket 연결용 JWT 토큰 생성"""
        if not self.is_authenticated():
            raise AuthenticationError("API 키가 설정되지 않았습니다")

        try:
            # WebSocket용 JWT 토큰 생성 (REST API와 동일한 방식)
            access_token = self.create_jwt_token()

            # WebSocket JWT 토큰은 일반적으로 1시간 수명
            expires_in = 3600  # 1시간 (3600초)

            self._logger.debug("WebSocket JWT 토큰 생성 완료")

            return {
                'access_token': access_token,
                'expires_in': expires_in,
                'token_type': 'Bearer'
            }

        except Exception as e:
            self._logger.error(f"WebSocket JWT 토큰 생성 실패: {e}")
            raise AuthenticationError(f"WebSocket JWT 토큰 생성 실패: {e}")

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
            token = self.create_jwt_token(query_params, request_body)
            headers['Authorization'] = f'Bearer {token}'

        return headers
