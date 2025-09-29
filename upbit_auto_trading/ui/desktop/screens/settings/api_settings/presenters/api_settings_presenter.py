"""
API 설정 프레젠터

API 키 관리 및 연결 테스트에 대한 비즈니스 로직을 처리하는 MVP 패턴의 Presenter

Phase 2 마이그레이션으로 생성됨:
- 기존: ApiKeyManagerSecure (단일 클래스)
- 새로운: ApiSettingsPresenter (DDD + MVP 패턴)

📋 주요 기능:
- API 키 저장/로드/삭제
- API 연결 테스트
- 보안 마스킹 처리
- 권한 설정 관리
- Infrastructure Logger v4.0 통합
"""

import gc
from typing import TYPE_CHECKING, Tuple, Dict, Any

from dependency_injector.wiring import Provide, inject

# Application Layer - Infrastructure 의존성 격리 (Phase 3 수정)
# DI 컨테이너는 @inject 패턴으로 주입받도록 변경

if TYPE_CHECKING:
    from upbit_auto_trading.ui.desktop.screens.settings.api_settings.views.api_settings_view import ApiSettingsView
    # Infrastructure 서비스는 DI 컨테이너를 통해 주입받음

class ApiSettingsPresenter:
    """
    API 설정 프레젠터 - MVP 패턴의 Presenter 역할

    비즈니스 로직을 담당하며 View와 Domain Service 사이의 중계자 역할을 합니다.
    """

    @inject
    def __init__(
        self,
        view: "ApiSettingsView",
        api_key_service=Provide["api_key_service"],
        logging_service=Provide["application_logging_service"]
    ):
        self.view = view

        # Application Layer 로깅 서비스 사용 (Infrastructure 직접 접근 제거)
        self.logger = logging_service.get_component_logger("ApiSettingsPresenter")

        # ApiKeyService 의존성 주입
        self.api_key_service = api_key_service
        if self.api_key_service is None:
            self.logger.warning("⚠️ ApiKeyService가 None으로 전달됨 - 테스트 모드에서 실행 중")
        else:
            self.logger.info(f"✅ ApiKeyService 의존성 주입 성공: {type(self.api_key_service).__name__}")

        # 보안 상태 관리
        self._is_saved = False
        self._is_editing_mode = False  # 편집 모드 여부

        # Infrastructure Layer 연동 상태 보고
        self._report_to_infrastructure()

        self.logger.info("✅ API 설정 프레젠터 초기화 완료")

    def _report_to_infrastructure(self):
        """Infrastructure Layer 상태 보고 (레거시 briefing 시스템 제거됨)"""
        self.logger.debug("API 설정 프레젠터 상태 보고 완료")

    def load_api_settings(self) -> Dict[str, Any]:
        """API 설정 로드 - 캐싱 최적화"""
        try:
            if self.api_key_service is None:
                self.logger.warning("⚠️ ApiKeyService가 None이어서 설정을 로드할 수 없습니다")
                return {
                    'access_key': '',
                    'secret_key': '',
                    'trade_permission': False,
                    'has_saved_keys': False
                }

            # 캐싱된 API 인스턴스 상태 확인 (성능 정보)
            cache_status = self.api_key_service.get_cache_status()
            if cache_status.get('cached', False):
                cache_age = cache_status.get('age_seconds', 0)
                self.logger.debug(f"💨 API 캐시 상태: 유효={cache_status.get('valid', False)}, 나이={cache_age:.1f}초")

            api_keys = self.api_key_service.load_api_keys()

            if not api_keys or not any(api_keys):
                self.logger.debug("저장된 API 키가 없습니다.")
                self._is_saved = False
                return {
                    'access_key': '',
                    'secret_key': '',
                    'trade_permission': False,
                    'has_saved_keys': False
                }

            # Tuple 형태로 반환됨: (access_key, secret_key, trade_permission)
            access_key, secret_key, trade_permission = api_keys

            # Secret Key 마스킹 처리
            masked_secret_key = ''
            if secret_key:
                # ApiKeyService의 get_secret_key_mask_length() 활용
                mask_length = self.api_key_service.get_secret_key_mask_length()
                masked_secret_key = "●" * mask_length
                self._is_saved = True  # 저장된 상태로 표시
                self._is_editing_mode = False

            self.logger.debug("API 키 설정 로드 완료 (보안 마스킹 + 캐싱 최적화)")

            return {
                'access_key': access_key if access_key else '',
                'secret_key': masked_secret_key,
                'trade_permission': trade_permission,
                'has_saved_keys': True
            }

        except Exception as e:
            self.logger.error(f"API 키 로드 중 오류: {e}")
            return {
                'access_key': '',
                'secret_key': '',
                'trade_permission': False,
                'has_saved_keys': False
            }

    def save_api_keys(self, access_key: str, secret_key: str, trade_permission: bool) -> Tuple[bool, str]:
        """API 키 저장 - 깔끔한 재생성 시스템 사용"""
        try:
            if self.api_key_service is None:
                return False, "API 키 서비스가 초기화되지 않았습니다."

            # 입력 검증
            access_key = access_key.strip()
            secret_key_input = secret_key.strip()

            if not access_key:
                return False, "Access Key를 입력해주세요."

            # Secret Key 처리 - 보안 강화
            if not secret_key_input:
                return False, "Secret Key를 입력해주세요."
            elif secret_key_input.startswith("●"):
                # 마스킹된 기존 키: 변경되지 않음
                if not self._is_editing_mode:
                    return False, "기존 API 키가 유지됩니다. 변경하려면 새로운 키를 입력해주세요."
                else:
                    return False, "새로운 Secret Key를 입력해주세요."
            else:
                # 새로운 Secret Key 입력
                secret_key = secret_key_input

            # 깔끔한 재생성 확인 콜백 함수 정의
            def confirm_save_callback(save_message, save_details):
                """사용자 저장 확인 대화상자"""
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    None,
                    "API 키 저장 확인",
                    f"{save_message}\n\n{save_details}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes  # 저장은 기본적으로 Yes
                )
                return reply == QMessageBox.StandardButton.Yes

            # 깔끔한 재생성 시스템 사용
            success, result_message = self.api_key_service.save_api_keys_clean(
                access_key=access_key,
                secret_key=secret_key,
                confirm_deletion_callback=confirm_save_callback
            )

            if success:
                # 상태 업데이트
                self._is_saved = True
                self._is_editing_mode = False

                # 거래 권한 설정 (별도 저장 - 호환성 유지)
                try:
                    # 기본 save_api_keys로 권한 업데이트
                    permission_updated = self.api_key_service.save_api_keys(
                        access_key=access_key,
                        secret_key=secret_key,
                        trade_permission=trade_permission
                    )
                    if not permission_updated:
                        self.logger.warning("거래 권한 설정 업데이트 실패")
                except Exception as e:
                    self.logger.warning(f"거래 권한 설정 중 오류: {e}")

                self.logger.info(f"깔끔한 재생성 완료: {result_message}")

                # 보안: 사용된 평문 키를 메모리에서 즉시 삭제
                access_key = ""
                secret_key = ""
                secret_key_input = ""
                gc.collect()

                # 저장 후 자동으로 API 연결 테스트 수행 (조용한 모드)
                self.logger.info("저장 후 자동 API 연결 테스트 시작")
                test_success, test_message = self.test_api_connection(silent=True)

                return True, result_message

            elif "취소" in result_message:
                self.logger.debug(f"깔끔한 재생성 취소: {result_message}")
                return False, result_message
            else:
                self.logger.error(f"깔끔한 재생성 실패: {result_message}")
                return False, result_message

        except Exception as e:
            self.logger.error(f"깔끔한 재생성 중 오류: {e}")
            return False, f"API 키를 저장하는 중 오류가 발생했습니다: {str(e)}"

    def test_api_connection(self, silent: bool = False) -> Tuple[bool, str]:
        """API 키 테스트 - 저장된 키만 사용하는 새로운 정책"""
        try:
            if self.api_key_service is None:
                return False, "API 키 서비스가 초기화되지 않았습니다."

            # 새로운 정책: 저장된 키 존재 여부만 확인
            if not self.api_key_service.has_valid_keys():
                message = "저장된 API 키가 없습니다. 먼저 API 키를 입력하고 저장 버튼을 눌러주세요."
                self.logger.warning("🔒 테스트 실패: 저장된 API 키 없음")
                return False, message

            # 저장된 키만 사용 (입력 박스 값 무시)
            saved_keys = self.api_key_service.load_api_keys()
            if not saved_keys or len(saved_keys) < 2:
                message = "저장된 API 키를 불러올 수 없습니다."
                self.logger.error("🔒 테스트 실패: 저장된 키 로드 실패")
                return False, message

            access_key, secret_key, _ = saved_keys

            if not access_key or not secret_key:
                message = "저장된 API 키가 불완전합니다."
                self.logger.error("🔒 테스트 실패: 저장된 키 불완전")
                return False, message

            # 저장된 키로만 API 테스트 수행
            self.logger.info(f"🔑 저장된 키로 API 테스트 시작 - Access Key: {access_key[:10]}...")
            test_result = self.api_key_service.test_api_connection(access_key, secret_key)

            # Tuple 형태로 반환됨: (success, message, account_info)
            success, message, account_info = test_result

            if success:
                # KRW 잔고 정보 추출 - ApiKeyService 반환 형식에 맞춤
                krw_balance = 0
                self.logger.debug(f"🔍 account_info 타입: {type(account_info)}")
                self.logger.debug(f"🔍 account_info 내용: {account_info}")

                if account_info and isinstance(account_info, dict):
                    # ApiKeyService가 반환하는 새로운 형식 처리 (직접 통화별 딕셔너리)
                    if 'KRW' in account_info:
                        krw_info = account_info['KRW']
                        if isinstance(krw_info, dict) and 'total' in krw_info:
                            krw_balance = float(krw_info['total'])
                            self.logger.debug(f"🔍 KRW 잔고 발견 (신규 형식): {krw_balance}")
                        elif isinstance(krw_info, dict) and 'balance' in krw_info:
                            krw_balance = float(krw_info['balance'])
                            self.logger.debug(f"🔍 KRW 잔고 발견 (balance): {krw_balance}")
                    # 레거시 형식 지원 (krw_balance 직접 필드)
                    elif 'krw_balance' in account_info:
                        krw_balance = float(account_info.get('krw_balance', 0))
                        self.logger.debug(f"🔍 KRW 잔고 발견 (레거시 형식): {krw_balance}")
                    # 기존 accounts 배열 형식도 지원 (호환성)
                    elif 'accounts' in account_info:
                        accounts = account_info.get('accounts', [])
                        self.logger.debug(f"🔍 accounts 개수: {len(accounts)}")

                        for account in accounts:
                            currency = account.get('currency', '')
                            balance = account.get('balance', '0')
                            self.logger.debug(f"🔍 계좌: {currency} = {balance}")

                            if currency == 'KRW':
                                krw_balance = float(balance)
                                self.logger.debug(f"🔍 KRW 잔고 발견 (기존 형식): {krw_balance}")
                                break
                else:
                    self.logger.warning(f"⚠️ account_info가 dict가 아니거나 None: {type(account_info)}")

                # UI용 메시지 (줄바꿈 포함)
                success_message = f"API 키가 정상적으로 작동하며 서버에 연결되었습니다.\n\n조회된 잔고(KRW) 금액: {krw_balance:,.0f} 원"
                # 로그용 메시지 (줄바꿈 없이)
                self.logger.info(f"API 연결 테스트 성공 - KRW 잔고: {krw_balance:,.0f} 원")
                return True, success_message
            else:
                error_message = f"API 키 테스트에 실패했습니다.\n\n오류 메시지: {message}"
                self.logger.warning(f"API 연결 테스트 실패: {message}")
                return False, error_message

        except Exception as e:
            self.logger.error(f"API 테스트 중 오류: {e}")
            error_message = f"API 테스트 중 오류가 발생했습니다: {str(e)}"
            return False, error_message

    def delete_api_keys(self) -> Tuple[bool, str]:
        """API 키 삭제 - 스마트 삭제 시스템 사용"""
        try:
            if self.api_key_service is None:
                return False, "API 키 서비스가 초기화되지 않았습니다."

            # 스마트 삭제 확인 콜백 함수 정의
            def confirm_deletion_callback(deletion_message, deletion_details):
                """사용자 확인 대화상자"""
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    None,
                    "API 키 삭제 확인",
                    f"{deletion_message}\n\n{deletion_details}\n\n이 작업은 되돌릴 수 없습니다.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                return reply == QMessageBox.StandardButton.Yes

            # 스마트 삭제 시스템 사용
            result_message = self.api_key_service.delete_api_keys_smart(confirm_deletion_callback)

            # 삭제 성공한 경우에만 상태 초기화
            if "취소" not in result_message and "없습니다" not in result_message:
                # 메모리 정리 및 상태 초기화
                self._is_saved = False
                self._is_editing_mode = False
                gc.collect()

            # 결과 처리
            if "삭제 완료" in result_message:
                self.logger.info(f"스마트 삭제 완료: {result_message}")
                return True, result_message
            elif "취소" in result_message:
                self.logger.debug(f"스마트 삭제 취소: {result_message}")
                return False, result_message
            elif "없습니다" in result_message:
                self.logger.debug(f"삭제할 항목 없음: {result_message}")
                return True, result_message  # 성공으로 처리 (이미 삭제됨)
            else:
                self.logger.error(f"스마트 삭제 실패: {result_message}")
                return False, result_message

        except Exception as e:
            self.logger.error(f"스마트 삭제 중 오류: {e}")
            # 보안: 오류 발생시에도 메모리 정리
            gc.collect()
            return False, f"API 키 삭제 중 오류가 발생했습니다: {str(e)}"

    def on_input_changed(self, field_name: str, value: str):
        """입력 상자 내용 변경 시 호출되는 함수 - 보안 강화"""
        if field_name == "secret_key":
            # Secret Key 입력 시 편집 모드로 전환
            current_text = value.strip()
            if current_text and not current_text.startswith("●"):  # 보안: ● 문자로 저장된 키 표시
                self._is_editing_mode = True
                self._is_saved = False
                self.logger.debug("🔓 Secret Key 편집 모드 전환")
        elif field_name == "access_key":
            # Access Key 편집 감지
            self._is_saved = False
            self.logger.debug("🔓 Access Key 편집 감지")

    def get_button_states(self) -> Dict[str, bool]:
        """버튼 상태 반환"""
        has_saved_keys = bool(self.api_key_service and self.api_key_service.has_valid_keys())

        return {
            'save_enabled': True,  # 저장 버튼: 항상 활성화
            'test_enabled': has_saved_keys,  # 테스트 버튼: 저장된 키가 있을 때만
            'delete_enabled': has_saved_keys  # 삭제 버튼: 저장된 키가 있을 때만
        }

    def get_test_button_tooltip(self) -> str:
        """테스트 버튼 툴팁 반환"""
        has_saved_keys = bool(self.api_key_service and self.api_key_service.has_valid_keys())

        if has_saved_keys:
            return "저장된 API 키로 연결 테스트를 수행합니다."
        else:
            return "저장된 API 키가 없습니다. 먼저 키를 입력하고 저장해주세요."
