"""
API 키 서비스 구현

보안 강화된 API 키 관리를 위한 Infrastructure Layer 서비스
🔄 DDD Infrastructure Layer paths 적용
"""
import base64
import gc
import json
import sqlite3
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any
from cryptography.fernet import Fernet

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.configuration import paths


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

        # DDD Infrastructure Layer 경로 관리자 사용
        self.paths = paths

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

    # ===== DB 기반 암호화 키 관리 메서드들 =====

    def _save_encryption_key_to_db(self, key_data: bytes) -> bool:
        """
        암호화 키를 settings.sqlite3 DB에 저장

        Args:
            key_data (bytes): 저장할 암호화 키 데이터 (32바이트)

        Returns:
            bool: 저장 성공 여부

        Raises:
            sqlite3.Error: DB 작업 실패 시
            ValueError: 잘못된 키 데이터 시
        """
        if not key_data or not isinstance(key_data, bytes):
            raise ValueError("암호화 키 데이터가 올바르지 않습니다")

        try:
            # DB 경로 얻기
            db_path = self.paths.get_db_path('settings')
            self.logger.debug(f"🔗 DB 경로: {db_path}")

            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()

                # 암호화 키 저장 (기존 키 교체)
                cursor.execute("""
                    INSERT OR REPLACE INTO secure_keys (key_type, key_value)
                    VALUES (?, ?)
                """, ("encryption", key_data))

                conn.commit()
                self.logger.info("✅ 암호화 키 DB 저장 완료")
                return True

        except sqlite3.Error as e:
            self.logger.error(f"❌ DB 키 저장 실패: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ 키 저장 중 예상치 못한 오류: {e}")
            raise

    def _load_encryption_key_from_db(self) -> Optional[bytes]:
        """
        settings.sqlite3 DB에서 암호화 키 로드

        Returns:
            Optional[bytes]: 암호화 키 데이터 (없으면 None)

        Raises:
            sqlite3.Error: DB 작업 실패 시
        """
        try:
            # DB 경로 얻기
            db_path = self.paths.get_db_path('settings')

            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()

                # 암호화 키 조회
                cursor.execute("""
                    SELECT key_value FROM secure_keys
                    WHERE key_type = ?
                """, ("encryption",))

                result = cursor.fetchone()

                if result:
                    self.logger.debug("✅ DB에서 암호화 키 로드 완료")
                    return result[0]
                else:
                    self.logger.debug("🔑 DB에 암호화 키 없음")
                    return None

        except sqlite3.Error as e:
            self.logger.error(f"❌ DB 키 로드 실패: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ 키 로드 중 예상치 못한 오류: {e}")
            raise

    def _delete_encryption_key_from_db(self) -> bool:
        """
        settings.sqlite3 DB에서 암호화 키 삭제

        Returns:
            bool: 삭제 성공 여부 (없어도 True)
        """
        try:
            # DB 경로 얻기
            db_path = self.paths.get_db_path('settings')

            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()

                # 암호화 키 삭제
                cursor.execute("""
                    DELETE FROM secure_keys WHERE key_type = ?
                """, ("encryption",))

                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    self.logger.info(f"✅ DB에서 암호화 키 삭제 완료 ({deleted_count}개)")
                else:
                    self.logger.debug("🔑 DB에 삭제할 암호화 키 없음")

                return True

        except sqlite3.Error as e:
            self.logger.error(f"❌ DB 키 삭제 실패: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ 키 삭제 중 예상치 못한 오류: {e}")
            return False

    def _encryption_key_exists_in_db(self) -> bool:
        """
        DB에 암호화 키가 존재하는지 확인

        Returns:
            bool: 암호화 키 존재 여부
        """
        try:
            key_data = self._load_encryption_key_from_db()
            return key_data is not None
        except Exception:
            return False

    # ===== Task 1.3: 상황별 스마트 삭제 로직 =====

    def delete_api_keys_smart(self, confirm_deletion_callback=None) -> str:
        """
        상황별 명확한 삭제 로직

        Args:
            confirm_deletion_callback: 삭제 확인 콜백 함수 (UI용)

        Returns:
            str: 삭제 결과 메시지
        """
        try:
            deletion_message, deletion_details = self._get_deletion_message()

            if deletion_message == "삭제할 인증 정보가 없습니다.":
                self.logger.info("✅ 삭제할 인증 정보 없음")
                return deletion_message

            # 사용자 확인 (콜백이 제공된 경우)
            if confirm_deletion_callback:
                confirmed = confirm_deletion_callback(deletion_message, deletion_details)
                if not confirmed:
                    self.logger.info("🚫 사용자가 삭제를 취소함")
                    return "삭제가 취소되었습니다."

            # 삭제 실행
            result = self._execute_deletion()
            self.logger.info(f"✅ 스마트 삭제 완료: {result}")
            return result

        except Exception as e:
            self.logger.error(f"❌ 스마트 삭제 중 오류: {e}")
            return f"삭제 중 오류가 발생했습니다: {str(e)}"

    def _get_deletion_message(self) -> tuple[str, str]:
        """
        삭제 상황별 메시지 생성 (재사용 가능)

        Returns:
            tuple[str, str]: (deletion_message, deletion_details)
        """
        has_db_key = self._encryption_key_exists_in_db()
        has_credentials_file = self._credentials_file_exists()

        if has_db_key and has_credentials_file:
            message = "암호화 키(DB)와 자격증명 파일을 모두 삭제하시겠습니까?"
            details = "삭제 후에는 API 키를 다시 입력해야 합니다."
        elif has_db_key and not has_credentials_file:
            message = "암호화 키(DB)만 존재합니다. 삭제하시겠습니까?"
            details = "자격증명 파일은 이미 없는 상태입니다."
        elif not has_db_key and has_credentials_file:
            message = "자격증명 파일만 존재합니다. 삭제하시겠습니까?"
            details = "암호화 키는 이미 없는 상태입니다."
        else:
            message = "삭제할 인증 정보가 없습니다."
            details = ""

        return message, details

    def _get_save_confirmation_message(self) -> tuple[str, str]:
        """
        저장 확인용 메시지 생성 (UX 개선)

        Returns:
            tuple[str, str]: (save_message, save_details)
        """
        has_db_key = self._encryption_key_exists_in_db()
        has_credentials_file = self._credentials_file_exists()

        if has_db_key and has_credentials_file:
            message = "기존 API 키를 새로운 키로 교체하시겠습니까?"
            details = "기존 암호화 키와 자격증명이 모두 새로운 것으로 교체됩니다."
        elif has_db_key and not has_credentials_file:
            message = "기존 암호화 키를 새로운 키로 교체하시겠습니까?"
            details = "DB의 암호화 키가 새로운 것으로 교체됩니다."
        elif not has_db_key and has_credentials_file:
            message = "기존 자격증명을 새로운 API 키로 교체하시겠습니까?"
            details = "자격증명 파일이 새로운 것으로 교체됩니다."
        else:
            message = "새로운 API 키를 저장하시겠습니까?"
            details = "새로운 암호화 키와 자격증명이 생성됩니다."

        return message, details

    def _execute_deletion(self) -> str:
        """
        실제 삭제 실행

        Returns:
            str: 삭제 완료 메시지
        """
        has_db_key = self._encryption_key_exists_in_db()
        has_credentials_file = self._credentials_file_exists()

        deleted_items = []

        # DB 키 삭제
        if has_db_key:
            success = self._delete_encryption_key_from_db()
            if success:
                deleted_items.append("암호화 키(DB)")
                self.logger.debug("✅ DB 암호화 키 삭제 완료")

        # 자격증명 파일 삭제
        if has_credentials_file:
            success = self._delete_credentials_file()
            if success:
                deleted_items.append("자격증명 파일")
                self.logger.debug("✅ 자격증명 파일 삭제 완료")

        # 메모리 정리
        self.encryption_key = None
        self.fernet = None
        gc.collect()

        if deleted_items:
            return f"삭제 완료: {', '.join(deleted_items)}"
        else:
            return "삭제할 항목이 없었습니다."

    def _credentials_file_exists(self) -> bool:
        """
        자격증명 파일 존재 여부 확인

        Returns:
            bool: 자격증명 파일 존재 여부
        """
        try:
            return self.paths.API_CREDENTIALS_FILE.exists()
        except Exception:
            return False

    def _delete_credentials_file(self) -> bool:
        """
        자격증명 파일 삭제

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            if self.paths.API_CREDENTIALS_FILE.exists():
                self.paths.API_CREDENTIALS_FILE.unlink()
                self.logger.debug("✅ 자격증명 파일 삭제 완료")
                return True
            else:
                self.logger.debug("🔑 삭제할 자격증명 파일 없음")
                return True  # 없어도 성공으로 처리
        except Exception as e:
            self.logger.error(f"❌ 자격증명 파일 삭제 실패: {e}")
            return False

    # ===== Task 1.4: 깔끔한 재생성 로직 (코드 재사용) =====

    def save_api_keys_clean(self, access_key: str, secret_key: str, confirm_deletion_callback=None) -> tuple[bool, str]:
        """
        깔끔한 재생성: 스마트 삭제 기능 재사용

        Args:
            access_key (str): 업비트 Access Key
            secret_key (str): 업비트 Secret Key
            confirm_deletion_callback: 삭제 확인 콜백 함수 (UI용)

        Returns:
            tuple[bool, str]: (성공 여부, 결과 메시지)
        """
        try:
            self.logger.info("🔄 깔끔한 API 키 재생성 시작")

            # 1. 기존 인증정보 존재 시 스마트 삭제 로직 호출
            if self._has_any_existing_credentials():
                # 저장용 메시지 생성 (UX 개선)
                save_message, save_details = self._get_save_confirmation_message()

                # 사용자 확인 (콜백이 제공된 경우)
                if confirm_deletion_callback:
                    confirmed = confirm_deletion_callback(save_message, save_details)
                    if not confirmed:
                        self.logger.info("🚫 사용자가 저장을 취소함")
                        return False, "저장이 취소되었습니다."

                # 기존 데이터 삭제 (스마트 삭제 로직 재사용)
                deletion_result = self._execute_deletion()
                self.logger.info(f"🗑️ 기존 데이터 삭제: {deletion_result}")

            # 2. 새 키 생성 및 저장
            success, save_message = self._create_and_save_new_credentials(access_key, secret_key)

            if success:
                self.logger.info("✅ 깔끔한 재생성 완료")
                return True, save_message
            else:
                self.logger.error(f"❌ 새 키 저장 실패: {save_message}")
                return False, save_message

        except Exception as e:
            self.logger.error(f"❌ 깔끔한 재생성 중 오류: {e}")
            return False, f"재생성 중 오류가 발생했습니다: {str(e)}"

    def _has_any_existing_credentials(self) -> bool:
        """
        기존 인증정보 존재 여부 확인

        Returns:
            bool: DB 키 또는 자격증명 파일 중 하나라도 존재하면 True
        """
        return (self._encryption_key_exists_in_db()
                or self._credentials_file_exists())

    def _create_and_save_new_credentials(self, access_key: str, secret_key: str) -> tuple[bool, str]:
        """
        새로운 암호화 키 생성 및 자격증명 저장

        Args:
            access_key (str): 업비트 Access Key
            secret_key (str): 업비트 Secret Key

        Returns:
            tuple[bool, str]: (성공 여부, 결과 메시지)
        """
        try:
            self.logger.info("🔑 새로운 암호화 키 생성 및 자격증명 저장 시작")

            # 새 암호화 키 생성
            import os
            import base64
            raw_key = os.urandom(32)  # 32바이트 원시 키
            new_encryption_key = base64.urlsafe_b64encode(raw_key)  # URL-safe Base64 인코딩

            # DB에 암호화 키 저장
            if not self._save_encryption_key_to_db(new_encryption_key):
                return False, "암호화 키 DB 저장에 실패했습니다."

            # 메모리에 새 키 로드
            self.encryption_key = new_encryption_key
            self.fernet = Fernet(self.encryption_key)

            # API 키 저장 (기존 save_api_keys 로직 활용)
            save_success = self.save_api_keys(access_key, secret_key)

            if save_success:
                return True, "새로운 API 키가 저장되었습니다."
            else:
                # 실패 시 DB 키도 정리
                self._delete_encryption_key_from_db()
                return False, "API 키 저장에 실패했습니다."

        except Exception as e:
            self.logger.error(f"❌ 새 자격증명 생성 중 오류: {e}")
            # 에러 시 정리
            try:
                self._delete_encryption_key_from_db()
            except Exception:
                pass
            return False, f"새 자격증명 생성 중 오류: {str(e)}"

    # ========================================
    # Task 2.1: 기본 마이그레이션 시스템 (새로운 접근)
    # ========================================

    def _detect_legacy_encryption_file(self) -> bool:
        """
        Task 2.1.1: 레거시 암호화 키 파일 감지

        새로운 접근 방법:
        - 파일 존재 여부만 체크하는 단순한 감지 로직
        - 복잡한 파일 읽기나 검증은 다음 단계에서 처리
        - 에러 시 안전하게 False 반환 (마이그레이션 불필요로 간주)

        Returns:
            bool: 레거시 파일 존재 여부
        """
        try:
            # 레거시 암호화 키 파일 경로: config/secure/encryption_key.key
            legacy_key_path = self.paths.SECURE_DIR / "encryption_key.key"

            self.logger.debug(f"🔍 레거시 파일 감지: {legacy_key_path}")

            # 단순한 파일 존재 여부만 체크
            exists = legacy_key_path.exists()

            if exists:
                self.logger.info(f"📁 레거시 암호화 키 파일 발견: {legacy_key_path}")
            else:
                self.logger.debug(f"📁 레거시 암호화 키 파일 없음: {legacy_key_path}")

            return exists

        except Exception as e:
            # 모든 에러는 False 반환 (안전한 처리)
            self.logger.debug(f"⚠️ 레거시 파일 감지 중 오류 (안전하게 False 반환): {e}")
            return False

    def _read_file_key_safely(self) -> bytes | None:
        """
        Task 2.1.2: 레거시 암호화 키 파일 안전 읽기

        새로운 접근 방법:
        - 정상적인 레거시 파일에서 키 데이터를 안전하게 읽기
        - 손상된 파일이나 예외 상황에서 None 반환
        - 바이너리 데이터를 그대로 반환 (복호화나 검증은 다음 단계)

        Returns:
            bytes | None: 성공 시 키 데이터, 실패 시 None
        """
        try:
            # 레거시 암호화 키 파일 경로
            legacy_key_path = self.paths.SECURE_DIR / "encryption_key.key"

            self.logger.debug(f"🔍 레거시 파일 읽기: {legacy_key_path}")

            # 파일 존재 여부 확인
            if not legacy_key_path.exists():
                self.logger.debug(f"📁 레거시 파일 없음: {legacy_key_path}")
                return None

            # 파일 크기 확인 (레거시 암호화 키 기본 검증)
            file_size = legacy_key_path.stat().st_size

            # 레거시 암호화 키 크기 검증
            # - Base64 인코딩된 32바이트 키: 정확히 44바이트
            # - 일부 시스템에서 줄바꿈 추가 가능: 44~46바이트
            if file_size == 0:
                self.logger.warning(f"⚠️ 빈 레거시 파일: {legacy_key_path}")
                return None

            if file_size < 32 or file_size > 64:  # 32~64바이트 범위 (여유있게)
                self.logger.warning(f"⚠️ 비정상적인 레거시 키 파일 크기 ({file_size}바이트, 예상: 44바이트): {legacy_key_path}")
                return None

            # 파일 읽기
            key_data = legacy_key_path.read_bytes()

            self.logger.info(f"✅ 레거시 파일 읽기 성공: {len(key_data)}바이트")
            return key_data

        except PermissionError as e:
            # 권한 오류는 마이그레이션 불가로 간주
            self.logger.debug(f"🔒 레거시 파일 접근 권한 없음 (안전하게 None 반환): {e}")
            return None

        except OSError as e:
            # 파일 시스템 오류
            self.logger.debug(f"💾 레거시 파일 읽기 오류 (안전하게 None 반환): {e}")
            return None

        except Exception as e:
            # 기타 모든 예외는 안전하게 None 반환
            self.logger.debug(f"⚠️ 레거시 파일 읽기 중 예상치 못한 오류 (안전하게 None 반환): {e}")
            return None

    def _migrate_file_key_to_db_simple(self) -> bool:
        """
        Task 2.1.3: 3단계 기본 마이그레이션 플로우

        새로운 접근 방법:
        - 기존 구현된 메서드들을 조합하여 안전한 마이그레이션
        - 실패 시 원본 파일 보존 (사용자 수동 처리 가능)
        - DB에 이미 키가 있으면 마이그레이션 스킵

        3단계 플로우:
        1. 파일감지 (Task 2.1.1)
        2. 파일읽기 (Task 2.1.2)
        3. DB저장 (Task 1.2)
        4. 파일삭제 (새로운 단계)

        Returns:
            bool: 마이그레이션 성공 여부 (스킵도 성공으로 간주)
        """
        try:
            self.logger.info("🔄 레거시 파일 → DB 마이그레이션 시작")

            # 0단계: DB에 이미 암호화 키가 있는지 확인
            if self._encryption_key_exists_in_db():
                self.logger.info("✅ DB에 이미 암호화 키 존재 - 마이그레이션 스킵")
                return True  # 스킵도 성공으로 간주

            # 1단계: 레거시 파일 감지 (Task 2.1.1 활용)
            if not self._detect_legacy_encryption_file():
                self.logger.info("✅ 레거시 파일 없음 - 마이그레이션 불필요")
                return True  # 마이그레이션 불필요도 성공으로 간주

            # 2단계: 레거시 파일 안전 읽기 (Task 2.1.2 활용)
            legacy_key_data = self._read_file_key_safely()
            if legacy_key_data is None:
                self.logger.warning("⚠️ 레거시 파일 읽기 실패 - 원본 파일 보존")
                return False  # 읽기 실패는 마이그레이션 실패

            # Base64 디코딩 (레거시 키는 Base64로 저장됨)
            try:
                decoded_key = base64.b64decode(legacy_key_data.decode('utf-8').strip())
                self.logger.debug(f"🔑 레거시 키 디코딩: {len(decoded_key)}바이트")
            except Exception as e:
                self.logger.warning(f"⚠️ 레거시 키 Base64 디코딩 실패: {e} - 원본 파일 보존")
                return False

            # 3단계: DB에 암호화 키 저장 (Task 1.2 활용)
            if not self._save_encryption_key_to_db(decoded_key):
                self.logger.error("❌ DB 저장 실패 - 원본 파일 보존")
                return False  # DB 저장 실패

            # 4단계: 레거시 파일 삭제 (마이그레이션 완료)
            legacy_key_path = self.paths.SECURE_DIR / "encryption_key.key"
            try:
                legacy_key_path.unlink()
                self.logger.info(f"✅ 레거시 파일 삭제 완료: {legacy_key_path}")
            except Exception as e:
                self.logger.warning(f"⚠️ 레거시 파일 삭제 실패 (수동 삭제 필요): {e}")
                # 삭제 실패해도 마이그레이션은 성공으로 간주 (DB 저장은 완료됨)

            self.logger.info("🎉 레거시 파일 → DB 마이그레이션 완료")
            return True

        except Exception as e:
            # 예상치 못한 오류 시 안전한 실패
            self.logger.error(f"❌ 마이그레이션 중 예상치 못한 오류: {e}")
            return False
