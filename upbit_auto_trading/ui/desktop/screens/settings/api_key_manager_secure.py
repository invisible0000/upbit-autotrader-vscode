"""
API 키 관리자 - 보안 강화 버전 (Infrastructure Layer v4.0 통합)
- tuple 반환 타입 처리 수정
- 암호화 키 유지 문제 해결
- UI 그대로 유지
"""
import gc
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QFormLayout, QLineEdit, QCheckBox, QPushButton,
                             QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt

# Infrastructure Layer Enhanced Logging v4.0
from upbit_auto_trading.infrastructure.logging import create_component_logger


class ApiKeyManagerSecure(QWidget):
    """
    보안 강화된 API 키 관리자 - Infrastructure Layer v4.0 통합

    주요 보안 기능:
    1. config/secure/ 폴더를 사용하여 데이터 백업에서 제외
    2. 암호화 키와 API 키를 분리된 위치에 저장
    3. 메모리 보안 및 즉시 정리
    4. Infrastructure Layer Enhanced Logging v4.0 연동
    5. tuple 반환 타입 올바른 처리
    """
    settings_changed = pyqtSignal()
    api_status_changed = pyqtSignal(bool)

    def __init__(self, parent=None, api_key_service=None):
        super().__init__(parent)
        self.setObjectName("widget-api-key-manager-secure")

        # Infrastructure Layer Enhanced Logging v4.0 초기화
        self.logger = create_component_logger("ApiKeyManagerSecure")
        self.logger.info("🔐 API 키 관리자 Infrastructure Layer 통합 초기화 시작")

        # ApiKeyService 의존성 주입
        self.api_key_service = api_key_service
        if self.api_key_service is None:
            self.logger.error("❌ ApiKeyService가 None으로 전달됨 - 의존성 주입 실패")
        else:
            self.logger.info(f"✅ ApiKeyService 의존성 주입 성공: {type(self.api_key_service).__name__}")

        # 보안 상태 관리
        self._is_saved = False
        self._is_editing_mode = False  # 편집 모드 여부

        # Infrastructure Layer 연동 상태 보고
        self._report_to_infrastructure()

        # UI 설정 (기존과 동일)
        self._setup_ui()
        self._connect_signals()

        # 기존 설정 로드
        self.load_settings()

        self.logger.info("✅ API 키 관리자 Infrastructure Layer 통합 완료")

    def _report_to_infrastructure(self):
        """Infrastructure Layer v4.0에 상태 보고"""
        try:
            from upbit_auto_trading.infrastructure.logging.briefing.status_tracker import SystemStatusTracker
            tracker = SystemStatusTracker()
            tracker.update_component_status(
                "ApiKeyManagerSecure",
                "OK",
                "API 키 관리자 로드됨",
                widget_type="security_settings",
                encryption_enabled=True
            )
            self.logger.info("📊 SystemStatusTracker에 API 키 관리자 상태 보고 완료")
        except Exception as e:
            self.logger.warning(f"⚠️ SystemStatusTracker 연동 실패: {e}")

    def _setup_ui(self):
        """UI 설정 - 기존과 동일"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # API 키 입력 그룹
        api_key_group = QGroupBox("업비트 API 키 (보안 저장)")
        api_key_layout = QVBoxLayout(api_key_group)

        # 폼 레이아웃
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 10, 0, 10)
        form_layout.setSpacing(10)

        # Access Key 입력
        self.access_key_input = QLineEdit()
        self.access_key_input.setObjectName("input-access-key")
        self.access_key_input.setPlaceholderText("Access Key를 입력하세요")
        form_layout.addRow("Access Key:", self.access_key_input)

        # Secret Key 입력 - 보안 강화된 설정
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setObjectName("input-secret-key")
        self.secret_key_input.setPlaceholderText("Secret Key를 입력하세요")
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)

        # 보안 입력 힌트 적용 (PyQt6 표준)
        hints = (Qt.InputMethodHint.ImhHiddenText
                 | Qt.InputMethodHint.ImhSensitiveData
                 | Qt.InputMethodHint.ImhNoPredictiveText)
        self.secret_key_input.setInputMethodHints(hints)
        form_layout.addRow("Secret Key:", self.secret_key_input)

        # 키 표시 체크박스
        self.show_keys_checkbox = QCheckBox("키 표시")
        self.show_keys_checkbox.setObjectName("checkbox-show-keys")
        form_layout.addRow("", self.show_keys_checkbox)

        api_key_layout.addLayout(form_layout)

        # API 권한 설정 그룹
        permissions_group = QGroupBox("API 권한 설정")
        permissions_layout = QVBoxLayout(permissions_group)

        # 거래 권한 체크박스
        self.trade_permission_checkbox = QCheckBox("거래 권한 (매수/매도)")
        self.trade_permission_checkbox.setObjectName("checkbox-trade-permission")
        permissions_layout.addWidget(self.trade_permission_checkbox)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        # 저장 버튼
        self.save_button = QPushButton("저장")
        self.save_button.setObjectName("button-save-api-keys")
        button_layout.addWidget(self.save_button)

        # 테스트 버튼
        self.test_button = QPushButton("테스트")
        self.test_button.setObjectName("button-test-api-keys")
        self.test_button.setToolTip("저장된 API 키로 연결 테스트를 수행합니다.\n(입력 박스 값이 아닌 저장된 키만 사용)")
        button_layout.addWidget(self.test_button)

        # 삭제 버튼
        self.delete_button = QPushButton("삭제")
        self.delete_button.setObjectName("button-delete-api-keys")
        button_layout.addWidget(self.delete_button)

        # 레이아웃 조립
        self.main_layout.addWidget(api_key_group)
        self.main_layout.addWidget(permissions_group)
        self.main_layout.addLayout(button_layout)
        self.main_layout.addStretch(1)

    def _connect_signals(self):
        """시그널 연결 - 기존과 동일"""
        self.show_keys_checkbox.stateChanged.connect(self._toggle_key_visibility)
        self.save_button.clicked.connect(self.save_api_keys)
        self.test_button.clicked.connect(self.test_api_keys)
        self.delete_button.clicked.connect(self.delete_api_keys)

        # 입력 상자 편집 감지 (보안 정책용)
        self.access_key_input.textChanged.connect(self._on_input_changed)
        self.secret_key_input.textChanged.connect(self._on_input_changed)

    def _on_input_changed(self):
        """입력 상자 내용 변경 시 호출되는 함수 - 보안 강화"""
        sender = self.sender()

        if sender == self.secret_key_input:
            # Secret Key 입력 시 편집 모드로 전환
            current_text = self.secret_key_input.text().strip()
            if current_text and not current_text.startswith("●"):  # 보안: ● 문자로 저장된 키 표시
                self._is_editing_mode = True
                self._is_saved = False
                self.logger.debug("🔓 Secret Key 편집 모드 전환")
        elif sender == self.access_key_input:
            # Access Key 편집 감지
            self._is_saved = False
            self.logger.debug("🔓 Access Key 편집 감지")

    def _toggle_key_visibility(self, state):
        """키 표시/숨김 토글 - UI 전용 기능 (보안 강화)"""
        if state == Qt.CheckState.Checked.value:
            # 키 표시: 현재 입력 중인 텍스트만 보여줌
            self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.logger.debug("🔓 Secret Key 표시 모드 활성화 (편집 중 텍스트만)")
        else:
            # 키 숨김: 표준 암호 모드
            self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.logger.debug("🔒 Secret Key 숨김 모드 활성화")

    def load_settings(self):
        """설정 파일에서 API 키 로드 - 캐싱 최적화 (Task 2.3 통합)"""
        try:
            if self.api_key_service is None:
                self.logger.warning("⚠️ ApiKeyService가 None이어서 설정을 로드할 수 없습니다")
                return

            # Task 2.3: 캐싱된 API 인스턴스 상태 확인 (성능 정보)
            cache_status = self.api_key_service.get_cache_status()
            if cache_status.get('cached', False):
                cache_age = cache_status.get('age_seconds', 0)
                self.logger.debug(f"💨 API 캐시 상태: 유효={cache_status.get('valid', False)}, 나이={cache_age:.1f}초")

            api_keys = self.api_key_service.load_api_keys()

            if not api_keys or not any(api_keys):
                self.logger.debug("저장된 API 키가 없습니다.")
                self._update_button_states(has_saved_keys=False)
                return

            # Tuple 형태로 반환됨: (access_key, secret_key, trade_permission)
            access_key, secret_key, trade_permission = api_keys

            # Access Key 로드
            if access_key:
                self.access_key_input.setText(access_key)

            # Secret Key 로드 - 보안: 마스킹 처리
            if secret_key:
                # ApiKeyService의 get_secret_key_mask_length() 활용
                mask_length = self.api_key_service.get_secret_key_mask_length()
                self.secret_key_input.setText("●" * mask_length)
                self._is_saved = True  # 저장된 상태로 표시
                self._is_editing_mode = False

            # Trade Permission 설정
            self.trade_permission_checkbox.setChecked(trade_permission)

            # 버튼 상태 업데이트
            self._update_button_states(has_saved_keys=True)

            self.logger.debug("API 키 설정 로드 완료 (보안 마스킹 + 캐싱 최적화)")

        except Exception as e:
            self.logger.error(f"API 키 로드 중 오류: {e}")
            self._update_button_states(has_saved_keys=False)
            QMessageBox.warning(
                self,
                "로드 오류",
                f"API 키 설정을 읽는 중 오류가 발생했습니다:\n{str(e)}"
            )

    def _update_button_states(self, has_saved_keys: bool):
        """버튼 상태 업데이트 - 새로운 정책 반영

        Args:
            has_saved_keys (bool): 저장된 키 존재 여부
        """
        # 테스트 버튼: 저장된 키가 있을 때만 활성화
        self.test_button.setEnabled(has_saved_keys)

        # 삭제 버튼: 저장된 키가 있을 때만 활성화
        self.delete_button.setEnabled(has_saved_keys)

        # 저장 버튼: 항상 활성화 (새로운 키 입력용)
        self.save_button.setEnabled(True)

        if has_saved_keys:
            self.test_button.setToolTip("저장된 API 키로 연결 테스트를 수행합니다.")
        else:
            self.test_button.setToolTip("저장된 API 키가 없습니다. 먼저 키를 입력하고 저장해주세요.")

        self.logger.debug(f"🔘 버튼 상태 업데이트: 테스트={has_saved_keys}, 삭제={has_saved_keys}")

    def save_settings(self):
        """외부 호출용 저장 함수"""
        self.save_api_keys()

    def save_api_keys(self):
        """API 키 저장 - 깔끔한 재생성 시스템 사용 (Task 1.4 통합)"""
        try:
            if self.api_key_service is None:
                QMessageBox.warning(self, "서비스 오류", "API 키 서비스가 초기화되지 않았습니다.")
                return

            access_key = self.access_key_input.text().strip()
            secret_key_input = self.secret_key_input.text().strip()

            # 입력 검증
            if not access_key:
                QMessageBox.warning(self, "입력 오류", "Access Key를 입력해주세요.")
                return

            # Secret Key 처리 - 보안 강화
            if not secret_key_input:
                QMessageBox.warning(self, "입력 오류", "Secret Key를 입력해주세요.")
                return
            elif secret_key_input.startswith("●"):
                # 마스킹된 기존 키: 변경되지 않음
                if not self._is_editing_mode:
                    QMessageBox.information(self, "알림", "기존 API 키가 유지됩니다. 변경하려면 새로운 키를 입력해주세요.")
                    self.logger.info("기존 Secret Key 유지 (변경 없음)")
                    return
                else:
                    QMessageBox.warning(self, "입력 오류", "새로운 Secret Key를 입력해주세요.")
                    return
            else:
                # 새로운 Secret Key 입력
                secret_key = secret_key_input

            # 깔끔한 재생성 확인 콜백 함수 정의
            def confirm_save_callback(save_message, save_details):
                """사용자 저장 확인 대화상자"""
                reply = QMessageBox.question(
                    self,
                    "API 키 저장 확인",
                    f"{save_message}\n\n{save_details}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes  # 저장은 기본적으로 Yes
                )
                return reply == QMessageBox.StandardButton.Yes

            # Task 1.4 깔끔한 재생성 시스템 사용
            success, result_message = self.api_key_service.save_api_keys_clean(
                access_key=access_key,
                secret_key=secret_key,
                confirm_deletion_callback=confirm_save_callback
            )

            if success:
                # UI 업데이트: Secret Key를 실제 길이에 맞춰 마스킹 표시로 변경
                self.secret_key_input.setText("●" * len(secret_key))
                self._is_saved = True
                self._is_editing_mode = False

                # 거래 권한 설정 (별도 저장 - 호환성 유지)
                try:
                    # 기본 save_api_keys로 권한 업데이트
                    permission_updated = self.api_key_service.save_api_keys(
                        access_key=access_key,
                        secret_key=secret_key,
                        trade_permission=self.trade_permission_checkbox.isChecked()
                    )
                    if not permission_updated:
                        self.logger.warning("거래 권한 설정 업데이트 실패")
                except Exception as e:
                    self.logger.warning(f"거래 권한 설정 중 오류: {e}")

                QMessageBox.information(self, "저장 완료", result_message)
                self.logger.info(f"깔끔한 재생성 완료: {result_message}")

                # 보안: 사용된 평문 키를 메모리에서 즉시 삭제
                access_key = ""
                secret_key = ""
                secret_key_input = ""
                gc.collect()

                # 버튼 상태 업데이트 (저장 완료 후)
                self._update_button_states(has_saved_keys=True)

                self.settings_changed.emit()

                # 저장 후 자동으로 API 연결 테스트 수행 (조용한 모드)
                self.logger.info("저장 후 자동 API 연결 테스트 시작")
                self.test_api_keys(silent=True)

            elif "취소" in result_message:
                self.logger.debug(f"깔끔한 재생성 취소: {result_message}")
                # 취소는 메시지 표시 안함 (사용자가 이미 알고 있음)
            else:
                QMessageBox.warning(self, "저장 실패", result_message)
                self.logger.error(f"깔끔한 재생성 실패: {result_message}")

        except Exception as e:
            self.logger.error(f"깔끔한 재생성 중 오류: {e}")
            QMessageBox.warning(
                self,
                "저장 오류",
                f"API 키를 저장하는 중 오류가 발생했습니다:\n{str(e)}"
            )

    def test_api_keys(self, silent=False):
        """API 키 테스트 - 저장된 키만 사용하는 새로운 정책

        새로운 보안 정책:
        1. 테스트 버튼은 저장된 인증 정보만 사용
        2. 입력 박스의 값은 절대 사용하지 않음
        3. 저장된 정보가 없으면 테스트 불가
        4. 입력 박스는 표시용도만

        Args:
            silent (bool): True인 경우 성공/실패 메시지 팝업을 표시하지 않음
        """
        try:
            if self.api_key_service is None:
                if not silent:
                    QMessageBox.warning(self, "서비스 오류", "API 키 서비스가 초기화되지 않았습니다.")
                self.api_status_changed.emit(False)
                return

            # 🔒 새로운 정책: 저장된 키 존재 여부만 확인
            if not self.api_key_service.has_valid_keys():
                if not silent:
                    QMessageBox.warning(self, "테스트 불가",
                        "저장된 API 키가 없습니다.\n\n"
                        "먼저 API 키를 입력하고 저장 버튼을 눌러주세요.")
                self.logger.warning("🔒 테스트 실패: 저장된 API 키 없음")
                self.api_status_changed.emit(False)
                return

            # 저장된 키만 사용 (입력 박스 값 무시)
            saved_keys = self.api_key_service.load_api_keys()
            if not saved_keys or len(saved_keys) < 2:
                if not silent:
                    QMessageBox.warning(self, "키 오류", "저장된 API 키를 불러올 수 없습니다.")
                self.logger.error("🔒 테스트 실패: 저장된 키 로드 실패")
                self.api_status_changed.emit(False)
                return

            access_key, secret_key, _ = saved_keys

            if not access_key or not secret_key:
                if not silent:
                    QMessageBox.warning(self, "키 오류", "저장된 API 키가 불완전합니다.")
                self.logger.error("🔒 테스트 실패: 저장된 키 불완전")
                self.api_status_changed.emit(False)
                return

            # 저장된 키로만 API 테스트 수행
            self.logger.info(f"� 저장된 키로 API 테스트 시작 - Access Key: {access_key[:10]}...")
            test_result = self.api_key_service.test_api_connection(access_key, secret_key)            # Tuple 형태로 반환됨: (success, message, account_info)
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

                if not silent:
                    QMessageBox.information(
                        self,
                        "테스트 성공",
                        f"API 키가 정상적으로 작동하며 서버에 연결되었습니다.\n\n조회된 잔고(KRW) 금액: {krw_balance:,.0f} 원"
                    )
                self.logger.info(f"API 연결 테스트 성공 - KRW 잔고: {krw_balance:,.0f} 원")
                self.api_status_changed.emit(True)
            else:
                if not silent:
                    QMessageBox.warning(
                        self,
                        "테스트 실패",
                        f"API 키 테스트에 실패했습니다.\n\n오류 메시지: {message}"
                    )
                self.logger.warning(f"API 연결 테스트 실패: {message}")
                self.api_status_changed.emit(False)

        except Exception as e:
            self.logger.error(f"API 테스트 중 오류: {e}")
            if not silent:
                QMessageBox.warning(
                    self,
                    "API 호출 오류",
                    f"API 테스트 중 오류가 발생했습니다:\n{str(e)}"
                )
            self.api_status_changed.emit(False)

    def delete_api_keys(self):
        """API 키 삭제 - 스마트 삭제 시스템 사용 (Task 1.3 통합)"""
        try:
            if self.api_key_service is None:
                QMessageBox.warning(self, "서비스 오류", "API 키 서비스가 초기화되지 않았습니다.")
                return

            # 스마트 삭제 확인 콜백 함수 정의
            def confirm_deletion_callback(deletion_message, deletion_details):
                """사용자 확인 대화상자"""
                reply = QMessageBox.question(
                    self,
                    "API 키 삭제 확인",
                    f"{deletion_message}\n\n{deletion_details}\n\n이 작업은 되돌릴 수 없습니다.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                return reply == QMessageBox.StandardButton.Yes

            # Task 1.3 스마트 삭제 시스템 사용
            result_message = self.api_key_service.delete_api_keys_smart(confirm_deletion_callback)

            # UI 초기화 (삭제 성공한 경우에만)
            if "취소" not in result_message and "없습니다" not in result_message:
                self.access_key_input.clear()
                self.secret_key_input.clear()
                self.trade_permission_checkbox.setChecked(False)

                # 메모리 정리 및 상태 초기화
                self._is_saved = False
                self._is_editing_mode = False
                gc.collect()

                # 버튼 상태 업데이트 (삭제 완료 후)
                self._update_button_states(has_saved_keys=False)

                self.api_status_changed.emit(False)
                self.settings_changed.emit()

            # 결과 메시지 표시
            if "삭제 완료" in result_message:
                QMessageBox.information(self, "삭제 완료", result_message)
                self.logger.info(f"스마트 삭제 완료: {result_message}")
            elif "취소" in result_message:
                self.logger.debug(f"스마트 삭제 취소: {result_message}")
                # 취소는 메시지 표시 안함 (사용자가 이미 알고 있음)
            elif "없습니다" in result_message:
                QMessageBox.information(self, "알림", result_message)
                self.logger.debug(f"삭제할 항목 없음: {result_message}")
            else:
                QMessageBox.warning(self, "삭제 오류", result_message)
                self.logger.error(f"스마트 삭제 실패: {result_message}")

        except Exception as e:
            self.logger.error(f"스마트 삭제 중 오류: {e}")
            QMessageBox.warning(
                self,
                "삭제 오류",
                f"API 키 삭제 중 오류가 발생했습니다:\n{str(e)}"
            )
            # 보안: 오류 발생시에도 메모리 정리
            gc.collect()
