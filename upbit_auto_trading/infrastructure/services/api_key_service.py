"""
API 키 서비스 구현

보안 강화된 API 키 관리를 위한 Infrastructure Layer 서비스
🔄 DDD Infrastructure Layer Repository Pattern 적용
✅ Task 1.3, 1.4 핵심 기능 집중
"""
import base64
import gc
import json
import os
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any
from cryptography.fernet import Fernet

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.configuration import get_path_service
from upbit_auto_trading.domain.repositories.secure_keys_repository import SecureKeysRepository
from upbit_auto_trading.infrastructure.monitoring.simple_failure_monitor import mark_api_success, mark_api_failure

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

    def __init__(self, secure_keys_repository: SecureKeysRepository):
        """ApiKeyService 초기화 - DDD Repository 패턴 적용

        Args:
            secure_keys_repository (SecureKeysRepository): 보안 키 저장소 Repository
        """
        self.logger = create_component_logger("ApiKeyService")
        self.logger.info("🔐 ApiKeyService Infrastructure Layer 초기화 시작")

        # DDD Repository 주입
        self.secure_keys_repo = secure_keys_repository

        # Factory 패턴으로 Path Service 사용
        self.path_service = get_path_service()

        # 보안 컴포넌트 설정 - 프로그램 시작 시에는 키 생성하지 않음
        self._try_load_existing_encryption_key()

        # TTL 캐싱 시스템 초기화 (Task 2.3)
        self._api_cache = None  # 캐싱된 API 인스턴스
        self._cache_timestamp = None  # 캐시 생성 시간
        self._cache_ttl_seconds = 300  # TTL: 5분 (300초)
        self._cached_keys_hash = None  # 캐시된 키의 해시값 (변경 감지용)

        self.logger.info("✅ ApiKeyService Infrastructure Layer 초기화 완료")
        self.logger.debug("🕒 TTL 캐싱 시스템 초기화 완료 (TTL: 5분)")

    def _try_load_existing_encryption_key(self):
        """
        기존 암호화 키가 있으면 로드 (DB 우선, 파일 폴백)

        새로운 정책:
        - DB에서 암호화 키 우선 검색
        - 프로그램 시작 시에는 암호화 키를 생성하지 않음
        - 저장 시에만 필요에 따라 암호화 키 생성
        - 자격증명과 암호화 키의 일관성 보장
        """
        try:
            # 1. DB에서 암호화 키 먼저 검색
            db_key = self._load_encryption_key_from_db()
            if db_key is not None:
                self.encryption_key = db_key
                self.fernet = Fernet(self.encryption_key)
                self.logger.debug("✅ DB에서 암호화 키 로드 완료")
                return

            # 2. 보안 디렉토리 확보 (폴백용)
            encryption_key_path = self.path_service.get_directory_path("config") / "secure" / "encryption_key.key"
            self.logger.debug(f"🔑 암호화 키 경로: {encryption_key_path}")

            # 보안 디렉토리가 없으면 생성 (파일은 생성하지 않음)
            if not self.path_service.get_directory_path("config") / "secure".exists():
                self.logger.debug(f"🔐 보안 디렉토리 생성: {self.path_service.get_directory_path("config") / "secure"}")
                self.path_service.get_directory_path("config") / "secure".mkdir(parents=True, exist_ok=True)

            # 3. 레거시 파일 키 로드 (폴백)
            if encryption_key_path.exists():
                self.logger.debug(f"🔑 레거시 파일 키 로드 중: {encryption_key_path}")
                with open(encryption_key_path, "rb") as key_file:
                    self.encryption_key = key_file.read()
                self.fernet = Fernet(self.encryption_key)
                self.logger.debug(f"✅ 레거시 파일 키 로드 완료: {encryption_key_path}")
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
            encryption_key_path = self.path_service.get_directory_path("config") / "secure" / "encryption_key.key"

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
            encryption_key_path = self.path_service.get_directory_path("config") / "secure" / "encryption_key.key"
            self.logger.debug(f"🔑 암호화 키 경로: {encryption_key_path}")

            # 보안 디렉토리가 존재하는지 확인하고 생성
            if not self.path_service.get_directory_path("config") / "secure".exists():
                self.logger.info(f"🔐 보안 디렉토리 생성: {self.path_service.get_directory_path("config") / "secure"}")
                self.path_service.get_directory_path("config") / "secure".mkdir(parents=True, exist_ok=True)

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
            api_keys_path = self.path_service.get_directory_path("config") / "secure" / "api_credentials.json"

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
            api_keys_path = self.path_service.get_directory_path("config") / "secure" / "api_credentials.json"

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
        """API 연결 테스트 - 실제 업비트 API 호출

        Args:
            access_key: 업비트 Access Key
            secret_key: 업비트 Secret Key

        Returns:
            Tuple[bool, str, Dict[str, Any]]: (success, message, account_info)
        """
        client = None
        loop = None

        try:
            from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_private_client import UpbitPrivateClient

            self.logger.info("🔍 실제 업비트 API 연결 테스트 시작")

            # UpbitPrivateClient 직접 사용 (4-client 구조)
            client = UpbitPrivateClient(access_key=access_key, secret_key=secret_key)

            # PyQt 환경에서도 실제 API 호출 수행 (20,000원 테스트를 위해)
            try:
                # 현재 실행 중인 이벤트 루프가 있는지 확인
                import asyncio
                loop = asyncio.get_running_loop()

                # PyQt 환경에서도 실제 API 호출 수행
                self.logger.info("🔍 PyQt 환경에서 실제 API 호출 시작")

                # 새로운 스레드에서 비동기 작업 실행
                def run_async_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        async def test_connection():
                            async with client:
                                return await client.get_accounts()  # Dict 형식 사용
                        return new_loop.run_until_complete(test_connection())
                    finally:
                        new_loop.close()

                # 스레드에서 실행
                import threading
                result_container = []
                error_container = []

                def thread_worker():
                    try:
                        result = run_async_in_thread()
                        result_container.append(result)
                    except Exception as e:
                        error_container.append(e)

                thread = threading.Thread(target=thread_worker)
                thread.start()
                thread.join(timeout=10)  # 10초 타임아웃

                if error_container:
                    raise error_container[0]

                if result_container:
                    accounts = result_container[0]
                    # 계좌 정보 처리 (Dict 형식)
                    account_info = {}
                    total_krw = 0.0

                    if isinstance(accounts, dict):
                        # 새로운 Dict 형식 처리: {currency: account_data}
                        for currency, account in accounts.items():
                            balance = float(account.get('balance', 0))
                            locked = float(account.get('locked', 0))

                            if currency == 'KRW':
                                total_krw = balance + locked

                            account_info[currency] = {
                                'balance': balance,
                                'locked': locked,
                                'total': balance + locked
                            }

                        self.logger.info(f"✅ API 연결 테스트 성공 - KRW 잔고: {total_krw:,.0f}원")
                        return True, f"연결 성공\nKRW 잔고: {total_krw:,.0f}원", {
                            'KRW': account_info.get('KRW', {'balance': 0, 'locked': 0, 'total': 0}),
                            'accounts': account_info,
                            'total_krw': total_krw,
                            'currencies_count': len(account_info)
                        }
                    else:
                        return False, "계좌 정보 형식 오류", {}
                else:
                    raise TimeoutError("API 호출 타임아웃")

            except RuntimeError:
                # 실행 중인 루프가 없는 경우 (비PyQt 환경)
                import asyncio

                async def test_connection():
                    async with client:
                        return await client.get_accounts()  # Dict 형식 사용

                accounts = asyncio.run(test_connection())

                # 계좌 정보 처리 (Dict 형식)
                account_info = {}
                total_krw = 0.0

                if isinstance(accounts, dict):
                    # 새로운 Dict 형식 처리: {currency: account_data}
                    for currency, account in accounts.items():
                        balance = float(account.get('balance', 0))
                        locked = float(account.get('locked', 0))

                        if currency == 'KRW':
                            total_krw = balance + locked

                        account_info[currency] = {
                            'balance': balance,
                            'locked': locked,
                            'total': balance + locked
                        }

                    self.logger.info("✅ API 연결 테스트 성공")
                    return True, "연결 성공", {
                        'accounts': account_info,
                        'total_krw': total_krw,
                        'currencies_count': len(account_info)
                    }
                else:
                    return False, "계좌 정보 형식 오류", {}

        except Exception as e:
            mark_api_failure()  # API 실패 기록
            error_msg = f"API 연결 실패: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return False, error_msg, {}

        finally:
            # 명시적 클라이언트 정리 (컨텍스트 매니저가 실패한 경우를 위한 백업)
            if client:
                try:
                    if loop and not loop.is_closed():
                        loop.run_until_complete(client.close())
                except Exception as cleanup_error:
                    self.logger.debug(f"클라이언트 정리 중 오류 (무시 가능): {cleanup_error}")

    def delete_api_keys(self) -> bool:
        """API 키 및 암호화 키 삭제

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            api_keys_path = self.path_service.get_directory_path("config") / "secure" / "api_credentials.json"
            encryption_key_path = self.path_service.get_directory_path("config") / "secure" / "encryption_key.key"

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
            api_keys_path = self.path_service.get_directory_path("config") / "secure" / "api_credentials.json"
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

    # ===== DB 기반 암호화 키 관리 메서드들 (DDD Repository 패턴) =====

    def _save_encryption_key_to_db(self, key_data: bytes) -> bool:
        """
        암호화 키를 settings.sqlite3 DB에 저장 (Repository 패턴)

        Args:
            key_data (bytes): 저장할 암호화 키 데이터 (32바이트)

        Returns:
            bool: 저장 성공 여부
        """
        if not key_data or not isinstance(key_data, bytes):
            raise ValueError("암호화 키 데이터가 올바르지 않습니다")

        try:
            success = self.secure_keys_repo.save_key("encryption", key_data)
            if success:
                self.logger.info("✅ 암호화 키 DB 저장 완료 (Repository)")
            return success

        except Exception as e:
            self.logger.error(f"❌ DB 키 저장 실패 (Repository): {e}")
            raise

    def _load_encryption_key_from_db(self) -> Optional[bytes]:
        """
        settings.sqlite3 DB에서 암호화 키 로드 (Repository 패턴)

        Returns:
            Optional[bytes]: 암호화 키 데이터 (없으면 None)
        """
        try:
            key_data = self.secure_keys_repo.load_key("encryption")

            if key_data:
                self.logger.debug("✅ DB에서 암호화 키 로드 완료 (Repository)")
            else:
                self.logger.debug("🔑 DB에 암호화 키 없음 (Repository)")

            return key_data

        except Exception as e:
            self.logger.error(f"❌ DB 키 로드 실패 (Repository): {e}")
            raise

    def _delete_encryption_key_from_db(self) -> bool:
        """
        settings.sqlite3 DB에서 암호화 키 삭제 (Repository 패턴)

        Returns:
            bool: 삭제 성공 여부 (없어도 True)
        """
        try:
            success = self.secure_keys_repo.delete_key("encryption")

            if success:
                self.logger.info("✅ DB에서 암호화 키 삭제 완료 (Repository)")

            return success

        except Exception as e:
            self.logger.error(f"❌ DB 키 삭제 실패 (Repository): {e}")
            return False

    def _encryption_key_exists_in_db(self) -> bool:
        """
        DB에 암호화 키가 존재하는지 확인 (Repository 패턴)

        Returns:
            bool: 암호화 키 존재 여부
        """
        try:
            return self.secure_keys_repo.key_exists("encryption")
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

            # TTL 캐시 무효화 (Task 2.3)
            self.invalidate_api_cache()

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
            return self.path_service.get_directory_path("config") / "secure" / "api_credentials.json".exists()
        except Exception:
            return False

    def _delete_credentials_file(self) -> bool:
        """
        자격증명 파일 삭제

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            if self.path_service.get_directory_path("config") / "secure" / "api_credentials.json".exists():
                self.path_service.get_directory_path("config") / "secure" / "api_credentials.json".unlink()
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
                # TTL 캐시 무효화 (Task 2.3)
                self.invalidate_api_cache()
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

    # ===== Task 1.3: 상황별 스마트 삭제 로직 =====

    # ===== Task 2.3: TTL 기반 API 인스턴스 캐싱 =====

    def get_cached_api_instance(self):
        """
        TTL 기반 캐싱된 API 인스턴스 반환 (5분 TTL)

        성능 최적화를 위한 API 인스턴스 캐싱:
        - TTL: 5분 (보안-성능 균형점)
        - 키 변경 감지: 자동 캐시 무효화
        - 80% 성능 향상 목표

        Returns:
            Optional[UpbitClient]: 캐싱된 API 인스턴스 (유효한 경우)
            None: 캐시 없음/만료/키 변경됨

        Infrastructure Layer 패턴:
        - Repository를 통한 키 로드
        - Infrastructure 로깅 활용
        - DDD 경계 준수
        """
        try:
            self.logger.debug("🔍 캐싱된 API 인스턴스 요청")

            # 1. 캐시 유효성 검사
            if not self._is_cache_valid():
                self.logger.debug("🔄 캐시 없음/만료 - 새 인스턴스 생성 필요")
                return None

            # 2. 유효한 캐시 반환
            if self._api_cache is not None:
                self.logger.debug("✅ 유효한 캐시 발견 - 반환")
                return self._api_cache

            self.logger.debug("❓ 캐시 상태 불명 - None 반환")
            return None

        except Exception as e:
            self.logger.error(f"❌ 캐싱된 API 인스턴스 조회 실패: {e}")
            return None

    def cache_api_instance(self):
        """
        현재 API 키로 새 인스턴스를 생성하고 캐싱

        캐싱 프로세스:
        1. 현재 API 키 로드 (복호화)
        2. UpbitClient 인스턴스 생성
        3. TTL과 키 해시값 설정
        4. 캐시 저장

        Returns:
            Optional[UpbitClient]: 새로 생성되고 캐싱된 API 인스턴스
            None: 키 없음/오류
        """
        try:
            self.logger.debug("🔧 새 API 인스턴스 생성 및 캐싱 시작")

            # 1. 현재 API 키 로드
            access_key, secret_key, trade_permission = self.load_api_keys()

            if not access_key or not secret_key:
                self.logger.warning("⚠️ API 키 없음 - 캐싱 불가")
                return None

            # 2. UpbitPrivateClient 인스턴스 생성 (DDD Infrastructure Layer)
            from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_private_client import UpbitPrivateClient
            api_instance = UpbitPrivateClient(access_key, secret_key)

            # 3. 캐시 메타데이터 설정
            import time
            import hashlib

            current_time = time.time()
            keys_string = f"{access_key}:{secret_key}"
            keys_hash = hashlib.sha256(keys_string.encode()).hexdigest()[:16]

            # 4. 캐시 저장
            self._api_cache = api_instance
            self._cache_timestamp = current_time
            self._cached_keys_hash = keys_hash

            self.logger.info(f"✅ API 인스턴스 캐싱 완료 (TTL: {self._cache_ttl_seconds}초)")
            self.logger.debug(f"🔑 키 해시: {keys_hash}")

            return api_instance

        except Exception as e:
            self.logger.error(f"❌ API 인스턴스 캐싱 실패: {e}")
            return None

    def invalidate_api_cache(self) -> None:
        """
        API 캐시 수동 무효화

        호출 시점:
        - 새로운 API 키 저장 시
        - API 키 삭제 시
        - 수동 캐시 정리 시

        Infrastructure Layer 패턴:
        - 메모리 정리
        - 가비지 컬렉션 유도
        - 로깅을 통한 추적
        """
        try:
            self.logger.debug("🧹 API 캐시 수동 무효화 시작")

            # 캐시 존재 여부 확인
            cache_existed = self._api_cache is not None

            # 캐시 정리
            self._api_cache = None
            self._cache_timestamp = None
            self._cached_keys_hash = None

            # 메모리 정리 (선택적)
            if cache_existed:
                gc.collect()
                self.logger.info("✅ API 캐시 무효화 완료")
            else:
                self.logger.debug("ℹ️ 무효화할 캐시가 없음")

        except Exception as e:
            self.logger.error(f"❌ API 캐시 무효화 실패: {e}")

    def _is_cache_valid(self) -> bool:
        """
        캐시 유효성 검사 (TTL + 키 변경 감지)

        유효성 조건:
        1. 캐시 인스턴스 존재
        2. TTL 미만료 (5분)
        3. 키 변경 없음 (해시 비교)

        Returns:
            bool: 캐시 유효 여부
        """
        try:
            # 1. 캐시 존재 확인
            if self._api_cache is None or self._cache_timestamp is None:
                self.logger.debug("ℹ️ 캐시 없음 (정상)")
                return False

            # 2. TTL 확인 (5분)
            import time
            current_time = time.time()
            cache_age = current_time - self._cache_timestamp

            if cache_age > self._cache_ttl_seconds:
                self.logger.debug(f"⏰ TTL 만료 ({cache_age:.1f}초 > {self._cache_ttl_seconds}초)")
                return False

            # 3. 키 변경 감지
            try:
                access_key, secret_key, _ = self.load_api_keys()
                if access_key and secret_key:
                    import hashlib
                    keys_string = f"{access_key}:{secret_key}"
                    current_keys_hash = hashlib.sha256(keys_string.encode()).hexdigest()[:16]

                    if current_keys_hash != self._cached_keys_hash:
                        self.logger.debug("🔑 API 키 변경 감지 - 캐시 무효화")
                        return False
                else:
                    self.logger.debug("❌ 현재 키 로드 실패 - 캐시 무효화")
                    return False

            except Exception as key_check_error:
                self.logger.warning(f"⚠️ 키 변경 감지 실패: {key_check_error}")
                return False

            # 4. 모든 조건 통과
            self.logger.debug(f"✅ 캐시 유효 (남은 시간: {self._cache_ttl_seconds - cache_age:.1f}초)")
            return True

        except Exception as e:
            self.logger.error(f"❌ 캐시 유효성 검사 실패: {e}")
            return False

    def get_or_create_api_instance(self):
        """
        캐시된 API 인스턴스 반환 또는 새로 생성

        고수준 편의 메서드:
        1. 캐시 확인 → 있으면 반환
        2. 캐시 없음 → 새로 생성하고 캐싱

        Returns:
            Optional[UpbitClient]: API 인스턴스 (캐시됨 또는 새로 생성됨)
            None: 키 없음/오류

        사용 예시:
            api = service.get_or_create_api_instance()
            if api:
                accounts = api.get_accounts()
        """
        try:
            # 1. 캐시 확인
            cached_api = self.get_cached_api_instance()
            if cached_api is not None:
                self.logger.debug("💨 캐시에서 API 인스턴스 반환")
                return cached_api

            # 2. 새로 생성
            self.logger.debug("🔧 새 API 인스턴스 생성")
            new_api = self.cache_api_instance()
            return new_api

        except Exception as e:
            self.logger.error(f"❌ API 인스턴스 가져오기/생성 실패: {e}")
            return None

    def clear_cache(self) -> None:
        """
        캐시 완전 정리 (테스트/디버깅용)

        invalidate_api_cache()의 별칭 메서드
        테스트 코드에서 명확한 의도 표현용
        """
        self.invalidate_api_cache()

    def get_cache_status(self) -> dict:
        """
        캐시 상태 정보 반환 (디버깅/모니터링용)

        Returns:
            dict: 캐시 상태 정보
            - cached: 캐시 존재 여부
            - valid: 캐시 유효 여부
            - age_seconds: 캐시 나이 (초)
            - ttl_seconds: TTL 설정값
            - keys_hash: 키 해시값 (마스킹됨)
        """
        try:
            import time

            status = {
                'cached': self._api_cache is not None,
                'valid': self._is_cache_valid(),
                'age_seconds': None,
                'ttl_seconds': self._cache_ttl_seconds,
                'keys_hash': None
            }

            if self._cache_timestamp is not None:
                status['age_seconds'] = time.time() - self._cache_timestamp

            if self._cached_keys_hash is not None:
                # 키 해시 마스킹 (보안)
                status['keys_hash'] = f"{self._cached_keys_hash[:4]}****{self._cached_keys_hash[-4:]}"

            return status

        except Exception as e:
            self.logger.error(f"❌ 캐시 상태 조회 실패: {e}")
            return {'error': str(e)}

    # ===== Task 1.3: 상황별 스마트 삭제 로직 =====
