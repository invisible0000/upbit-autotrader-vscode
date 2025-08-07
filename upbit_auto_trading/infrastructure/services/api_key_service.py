"""
API 키 서비스 구현

보안 강화된 API 키 관리를 위한 Infrastructure Layer 서비스
"""
import gc
import json
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any
from cryptography.fernet import Fernet

from upbit_auto_trading.infrastructure.logging import create_component_logger
from config.simple_paths import SimplePaths


class IApiKeyService(ABC):
    """API 키 서비스 인터페이스"""

    @abstractmethod
    def save_api_keys(self, access_key: str, secret_key: str, trade_permission: bool = False) -> bool:
        """API 키 암호화 저장"""
        pass

    @abstractmethod
    def load_api_keys(self) -> Tuple[Optional[str], Optional[str], bool]:
        """API 키 복호화 로드 - (access_key, secret_key, trade_permission)"""
        pass

    @abstractmethod
    def test_api_connection(self, access_key: str, secret_key: str) -> Tuple[bool, str, Dict[str, Any]]:
        """API 연결 테스트 - (success, message, account_info)"""
        pass

    @abstractmethod
    def delete_api_keys(self) -> bool:
        """API 키 및 암호화 키 삭제"""
        pass

    @abstractmethod
    def has_valid_keys(self) -> bool:
        """유효한 API 키 존재 여부 확인"""
        pass

    @abstractmethod
    def get_secret_key_mask_length(self) -> int:
        """저장된 Secret Key의 마스킹 길이 반환"""
        pass


class ApiKeyService(IApiKeyService):
    """API 키 서비스 구현체 - Infrastructure Layer"""

    def __init__(self):
        """ApiKeyService 초기화"""
        self.logger = create_component_logger("ApiKeyService")
        self.logger.info("🔐 ApiKeyService Infrastructure Layer 초기화 시작")

        # 경로 관리자 초기화
        self.paths = SimplePaths()

        # 보안 컴포넌트 설정 - 프로그램 시작 시에는 키 생성하지 않음
        self._try_load_existing_encryption_key()

        self.logger.info("✅ ApiKeyService Infrastructure Layer 초기화 완료")

    def _try_load_existing_encryption_key(self):
        """
        기존 암호화 키가 있으면 로드, 없으면 로드하지 않음

        새로운 정책:
        - 프로그램 시작 시에는 암호화 키를 생성하지 않음
        - 저장 시에만 필요에 따라 암호화 키 생성
        - 자격증명과 암호화 키의 일관성 보장
        """
        try:
            # 보안 디렉토리 확보
            encryption_key_path = self.paths.SECURE_DIR / "encryption_key.key"
            self.logger.debug(f"🔑 암호화 키 경로: {encryption_key_path}")

            # 보안 디렉토리가 없으면 생성 (파일은 생성하지 않음)
            if not self.paths.SECURE_DIR.exists():
                self.logger.debug(f"🔐 보안 디렉토리 생성: {self.paths.SECURE_DIR}")
                self.paths.SECURE_DIR.mkdir(parents=True, exist_ok=True)

            # 기존 암호화 키가 있으면 로드
            if encryption_key_path.exists():
                self.logger.debug(f"🔑 기존 암호화 키 로드 중: {encryption_key_path}")
                with open(encryption_key_path, "rb") as key_file:
                    self.encryption_key = key_file.read()
                self.fernet = Fernet(self.encryption_key)
                self.logger.debug(f"✅ 암호화 키 로드 완료: {encryption_key_path}")
            else:
                # 암호화 키가 없으면 초기화하지 않음
                self.logger.debug("🔑 암호화 키 없음 - 저장 시 생성될 예정")
                self.encryption_key = None
                self.fernet = None

        except Exception as e:
            self.logger.error(f"암호화 키 로드 중 오류: {e}")
            self.encryption_key = None
            self.fernet = None

    def _create_new_encryption_key(self):
        """
        새로운 암호화 키 생성 및 저장

        정책:
        - 저장 버튼 클릭 시에만 호출
        - 기존 자격증명이 있으면 먼저 삭제
        - 새 키로 새로운 자격증명 생성
        """
        try:
            encryption_key_path = self.paths.SECURE_DIR / "encryption_key.key"

            # 새 암호화 키 생성
            key = Fernet.generate_key()
            self.logger.info(f"🔑 새 암호화 키 생성 중: {encryption_key_path}")

            # 파일로 저장
            with open(encryption_key_path, "wb") as key_file:
                key_file.write(key)

            # 메모리에 로드
            self.encryption_key = key
            self.fernet = Fernet(self.encryption_key)

            self.logger.info("✅ 새로운 암호화 키가 생성되고 로드되었습니다.")

        except Exception as e:
            self.logger.error(f"새 암호화 키 생성 중 오류: {e}")
            raise

    def _setup_encryption_key(self):
        """
        암호화 키 설정 및 생성 - 보안 경로 사용

        보안 고려사항:
        - 암호화 키를 config/secure/에 저장 (데이터 백업에서 제외)
        - API 키와 암호화 키를 분리된 위치에 저장
        """
        try:
            # 보안 디렉토리 확보
            encryption_key_path = self.paths.SECURE_DIR / "encryption_key.key"
            self.logger.debug(f"🔑 암호화 키 경로: {encryption_key_path}")

            # 보안 디렉토리가 존재하는지 확인하고 생성
            if not self.paths.SECURE_DIR.exists():
                self.logger.info(f"🔐 보안 디렉토리 생성: {self.paths.SECURE_DIR}")
                self.paths.SECURE_DIR.mkdir(parents=True, exist_ok=True)

            # 암호화 키 생성 또는 로드
            if not encryption_key_path.exists():
                key = Fernet.generate_key()
                self.logger.info(f"🔑 새 암호화 키 생성 중: {encryption_key_path}")
                with open(encryption_key_path, "wb") as key_file:
                    key_file.write(key)
                self.logger.info("✅ 새로운 암호화 키가 생성되었습니다.")
            else:
                self.logger.debug(f"🔑 기존 암호화 키 로드 중: {encryption_key_path}")

            with open(encryption_key_path, "rb") as key_file:
                self.encryption_key = key_file.read()
            self.fernet = Fernet(self.encryption_key)

            self.logger.debug(f"✅ 암호화 키 로드 완료: {encryption_key_path}")

        except Exception as e:
            self.logger.error(f"암호화 키 설정 중 오류: {e}")
            raise

    def save_api_keys(self, access_key: str, secret_key: str, trade_permission: bool = False) -> bool:
        """API 키 암호화 저장

        Args:
            access_key: 업비트 Access Key
            secret_key: 업비트 Secret Key
            trade_permission: 거래 권한 여부

        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 입력 검증
            if not access_key or not secret_key:
                self.logger.warning("Access Key 또는 Secret Key가 비어있음")
                return False

            # 암호화 키가 없으면 새로 생성 (저장 시에만 생성)
            if self.fernet is None or self.encryption_key is None:
                self.logger.info("🔑 저장을 위한 새 암호화 키 생성 중...")
                self._create_new_encryption_key()

            # 보안 경로에 저장
            api_keys_path = self.paths.API_CREDENTIALS_FILE

            # 키 암호화
            encrypted_access_key = self.fernet.encrypt(access_key.encode()).decode()
            encrypted_secret_key = self.fernet.encrypt(secret_key.encode()).decode()

            # 설정 저장
            settings = {
                "access_key": encrypted_access_key,
                "secret_key": encrypted_secret_key,
                "trade_permission": trade_permission
            }

            # UTF-8 인코딩으로 파일 저장
            with open(api_keys_path, "w", encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            # 보안: 사용된 평문 키를 메모리에서 즉시 삭제
            access_key = ""
            secret_key = ""
            encrypted_access_key = ""
            encrypted_secret_key = ""
            gc.collect()

            self.logger.info("API 키 저장 완료 (Infrastructure Layer)")
            return True

        except Exception as e:
            self.logger.error(f"API 키 저장 중 오류: {e}")
            # 보안: 오류 발생시에도 메모리 정리
            access_key = ""
            secret_key = ""
            gc.collect()
            return False

    def load_api_keys(self) -> Tuple[Optional[str], Optional[str], bool]:
        """API 키 복호화 로드

        Returns:
            Tuple[Optional[str], Optional[str], bool]: (access_key, secret_key, trade_permission)
        """
        try:
            api_keys_path = self.paths.API_CREDENTIALS_FILE

            if not api_keys_path.exists():
                self.logger.debug("API 키 파일이 존재하지 않습니다.")
                return None, None, False

            # 암호화 키가 없으면 복호화 불가
            if self.fernet is None:
                self.logger.error("암호화 키가 없어서 API 키를 복호화할 수 없습니다.")
                return None, None, False

            # UTF-8 인코딩으로 파일 읽기
            with open(api_keys_path, "r", encoding='utf-8') as f:
                settings = json.load(f)

            access_key = None
            secret_key = None
            trade_permission = settings.get("trade_permission", False)

            if "access_key" in settings:
                access_key = self.fernet.decrypt(settings["access_key"].encode('utf-8')).decode('utf-8')
            if "secret_key" in settings:
                secret_key = self.fernet.decrypt(settings["secret_key"].encode('utf-8')).decode('utf-8')

            self.logger.debug("API 키 로드 완료 (Infrastructure Layer)")
            return access_key, secret_key, trade_permission

        except Exception as e:
            self.logger.error(f"API 키 로드 중 오류: {e}")
            return None, None, False

    def test_api_connection(self, access_key: str, secret_key: str) -> Tuple[bool, str, Dict[str, Any]]:
        """API 연결 테스트

        Args:
            access_key: 업비트 Access Key
            secret_key: 업비트 Secret Key

        Returns:
            Tuple[bool, str, Dict[str, Any]]: (success, message, account_info)
        """
        try:
            if not access_key or not secret_key:
                return False, "Access Key 또는 Secret Key가 비어있습니다.", {}

            # API 연결 테스트
            from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
            api = UpbitAPI(access_key, secret_key)
            accounts = api.get_account()

            # 보안: API 호출 후 민감한 데이터를 메모리에서 즉시 삭제
            access_key = ""
            secret_key = ""
            gc.collect()

            if accounts:
                krw_balance = 0
                for acc in accounts:
                    if acc.get('currency') == 'KRW':
                        krw_balance = float(acc.get('balance', 0))
                        break

                account_info = {
                    "krw_balance": krw_balance,
                    "account_count": len(accounts)
                }

                message = f"API 키가 정상적으로 작동하며 서버에 연결되었습니다.\n조회된 잔고(KRW): {krw_balance:,.0f} 원"
                self.logger.info(f"API 연결 테스트 성공 - KRW 잔고: {krw_balance:,.0f} 원")
                return True, message, account_info
            else:
                message = "API 키가 유효하지 않거나 계좌 정보 조회에 실패했습니다.\nAPI 키 권한(계좌 조회) 설정을 확인해주세요."
                self.logger.warning("API 연결 테스트 실패 - 계좌 정보 조회 실패")
                return False, message, {}

        except Exception as e:
            # 보안: 사용 후 민감한 데이터를 메모리에서 즉시 삭제
            access_key = ""
            secret_key = ""
            gc.collect()

            self.logger.error(f"API 테스트 중 오류: {e}")
            return False, f"API 테스트 중 오류가 발생했습니다:\n{str(e)}", {}

    def delete_api_keys(self) -> bool:
        """API 키 및 암호화 키 삭제

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            api_keys_path = self.paths.API_CREDENTIALS_FILE
            encryption_key_path = self.paths.SECURE_DIR / "encryption_key.key"

            deleted = False

            # API 키 파일 삭제
            if api_keys_path.exists():
                api_keys_path.unlink()
                deleted = True
                self.logger.debug("API 키 파일 삭제 완료")

            # 암호화 키 파일 삭제
            if encryption_key_path.exists():
                encryption_key_path.unlink()
                deleted = True
                self.logger.debug("암호화 키 파일 삭제 완료")

            # 메모리 정리
            gc.collect()

            if deleted:
                self.logger.info("API 키 삭제 완료 (Infrastructure Layer)")
            else:
                self.logger.info("삭제할 API 키가 존재하지 않습니다.")

            return True

        except Exception as e:
            self.logger.error(f"API 키 삭제 중 오류: {e}")
            # 보안: 오류 발생시에도 메모리 정리
            gc.collect()
            return False

    def has_valid_keys(self) -> bool:
        """유효한 API 키 존재 여부 확인

        Returns:
            bool: 유효한 키 존재 여부
        """
        try:
            api_keys_path = self.paths.API_CREDENTIALS_FILE
            return api_keys_path.exists()
        except Exception:
            return False

    def get_secret_key_mask_length(self) -> int:
        """저장된 Secret Key의 마스킹 길이 반환

        Returns:
            int: 마스킹 길이 (기본값: 72자)
        """
        try:
            access_key, secret_key, _ = self.load_api_keys()
            if secret_key:
                length = len(secret_key)
                # 보안: 즉시 평문 삭제
                secret_key = ""
                gc.collect()
                return length
            else:
                return 72  # 업비트 표준 Secret Key 길이
        except Exception:
            return 72  # 기본값
