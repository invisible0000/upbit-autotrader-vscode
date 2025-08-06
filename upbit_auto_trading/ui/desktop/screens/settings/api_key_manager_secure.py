"""
API 키 관리자 - 보안 강화 버전 (Infrastructure Layer v4.0 통합)
"""
import gc
import json
from cryptography.fernet import Fernet
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QFormLayout, QLineEdit, QCheckBox, QPushButton,
                             QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt

# Infrastructure Layer Enhanced Logging v4.0
from upbit_auto_trading.infrastructure.logging import create_component_logger
from config.simple_paths import SimplePaths


class ApiKeyManagerSecure(QWidget):
    """
    보안 강화된 API 키 관리자 - Infrastructure Layer v4.0 통합

    주요 보안 기능:
    1. config/secure/ 폴더를 사용하여 데이터 백업에서 제외
    2. 암호화 키와 API 키를 분리된 위치에 저장
    3. 메모리 보안 및 즉시 정리
    4. Infrastructure Layer Enhanced Logging v4.0 연동
    """
    settings_changed = pyqtSignal()
    api_status_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-api-key-manager-secure")

        # Infrastructure Layer Enhanced Logging v4.0 초기화
        self.logger = create_component_logger("ApiKeyManagerSecure")
        self.logger.info("🔐 API 키 관리자 초기화 시작")

        # 보안 상태 관리
        self._actual_secret_key = ""
        self._is_saved = False

        # 경로 관리자 초기화
        self.paths = SimplePaths()

        # Infrastructure Layer 연동 상태 보고
        self._report_to_infrastructure()

        # 보안 컴포넌트 설정
        self._setup_encryption_key()
        self._setup_ui()
        self._connect_signals()

        # 기존 설정 로드
        self.load_settings()

        self.logger.info("✅ API 키 관리자 초기화 완료")

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

            # 암호화 키 생성 또는 로드
            if not encryption_key_path.exists():
                key = Fernet.generate_key()
                with open(encryption_key_path, "wb") as key_file:
                    key_file.write(key)
                self.logger.info("새로운 암호화 키가 생성되었습니다.")

            with open(encryption_key_path, "rb") as key_file:
                self.encryption_key = key_file.read()
            self.fernet = Fernet(self.encryption_key)

            self.logger.debug(f"암호화 키 로드 완료: {encryption_key_path}")

        except Exception as e:
            self.logger.error(f"암호화 키 설정 중 오류: {e}")
            raise

    def _setup_ui(self):
        """UI 설정"""
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

        # Secret Key 입력
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setObjectName("input-secret-key")
        self.secret_key_input.setPlaceholderText("Secret Key를 입력하세요")
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
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
        """시그널 연결"""
        self.show_keys_checkbox.stateChanged.connect(self._toggle_key_visibility)
        self.save_button.clicked.connect(self.save_api_keys)
        self.test_button.clicked.connect(self.test_api_keys)
        self.delete_button.clicked.connect(self.delete_api_keys)

        # 입력 상자 편집 감지 (보안 정책용)
        self.access_key_input.textChanged.connect(self._on_input_changed)
        self.secret_key_input.textChanged.connect(self._on_input_changed)

    def _on_input_changed(self):
        """입력 상자 내용 변경 시 호출되는 함수"""
        if hasattr(self, '_is_saved') and self._is_saved:
            sender = self.sender()

            if sender == self.secret_key_input:
                current_text = self.secret_key_input.text()
                if current_text and not current_text.startswith("*"):
                    self._is_saved = False
                    self.logger.debug("🔓 새로운 Secret Key 입력 감지 - 편집 모드로 전환")
            elif sender == self.access_key_input:
                self._is_saved = False
                self.logger.debug("🔓 Access Key 편집 감지 - 편집 모드로 전환")

    def _toggle_key_visibility(self, state):
        """키 표시/숨김 토글"""
        if state == Qt.CheckState.Checked.value:
            # 키 표시 상태일 때 실제 secret key 보여주기
            if hasattr(self, '_actual_secret_key') and self._actual_secret_key:
                self.secret_key_input.setText(self._actual_secret_key)
            self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            # 키 숨김 상태일 때 * 문자로 변경
            if hasattr(self, '_actual_secret_key') and self._actual_secret_key:
                self.secret_key_input.setText("*" * len(self._actual_secret_key))
            self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _secure_get_decrypted_keys(self):
        """
        보안 기능: 암호화된 키 파일에서 복호화하여 반환

        Returns:
            tuple: (access_key, secret_key) 또는 (None, None)
        """
        try:
            api_keys_path = self.paths.API_CREDENTIALS_FILE

            if not api_keys_path.exists():
                return None, None

            # UTF-8 인코딩으로 파일 읽기
            with open(api_keys_path, "r", encoding='utf-8') as f:
                settings = json.load(f)

            access_key = None
            secret_key = None

            if "access_key" in settings:
                access_key = self.fernet.decrypt(settings["access_key"].encode('utf-8')).decode('utf-8')
            if "secret_key" in settings:
                secret_key = self.fernet.decrypt(settings["secret_key"].encode('utf-8')).decode('utf-8')

            return access_key, secret_key

        except Exception as e:
            self.logger.error(f"API 키 복호화 중 오류: {e}")
            QMessageBox.warning(
                self,
                "복호화 오류",
                f"API 키 설정을 읽는 중 오류가 발생했습니다:\n{str(e)}"
            )
            return None, None

    def load_settings(self):
        """설정 파일에서 API 키 로드"""
        try:
            api_keys_path = self.paths.API_CREDENTIALS_FILE

            if not api_keys_path.exists():
                self.logger.debug("API 키 파일이 존재하지 않습니다.")
                return

            # UTF-8 인코딩으로 파일 읽기
            with open(api_keys_path, "r", encoding='utf-8') as f:
                settings = json.load(f)

            if "access_key" in settings:
                access_key = self.fernet.decrypt(settings["access_key"].encode()).decode()
                self.access_key_input.setText(access_key)

            if "secret_key" in settings:
                secret_key = self.fernet.decrypt(settings["secret_key"].encode()).decode()
                # 보안: 실제 키를 메모리에 보관하고 UI에는 * 표시
                self._actual_secret_key = secret_key
                self.secret_key_input.setText("*" * len(secret_key))
                self._is_saved = True  # 로드된 상태는 저장된 상태로 간주

            if "trade_permission" in settings:
                self.trade_permission_checkbox.setChecked(settings["trade_permission"])

            self.logger.debug("API 키 설정 로드 완료")

        except Exception as e:
            self.logger.error(f"API 키 로드 중 오류: {e}")
            QMessageBox.warning(
                self,
                "로드 오류",
                f"API 키 설정을 읽는 중 오류가 발생했습니다:\n{str(e)}"
            )

    def save_settings(self):
        """외부 호출용 저장 함수"""
        self.save_api_keys()

    def save_api_keys(self):
        """API 키 저장 - 보안 경로 사용"""
        try:
            access_key = self.access_key_input.text().strip()
            secret_key_input = self.secret_key_input.text().strip()

            # Secret key가 *로 표시된 경우 실제 저장된 값을 사용
            if secret_key_input.startswith("*") and hasattr(self, '_actual_secret_key'):
                secret_key = self._actual_secret_key
            else:
                secret_key = secret_key_input
                # 🔒 보안: 새 키 저장 시에만 _actual_secret_key 업데이트
                self._actual_secret_key = secret_key

            # 입력 검증
            if not access_key or not secret_key:
                QMessageBox.warning(self, "입력 오류", "Access Key와 Secret Key를 모두 입력해주세요.")
                return

            # 보안 경로에 저장
            api_keys_path = self.paths.API_CREDENTIALS_FILE

            # 키 암호화
            encrypted_access_key = self.fernet.encrypt(access_key.encode()).decode()
            encrypted_secret_key = self.fernet.encrypt(secret_key.encode()).decode()

            # 설정 저장
            settings = {
                "access_key": encrypted_access_key,
                "secret_key": encrypted_secret_key,
                "trade_permission": self.trade_permission_checkbox.isChecked()
            }

            # UTF-8 인코딩으로 파일 저장
            with open(api_keys_path, "w", encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            # UI 업데이트: Secret Key를 * 표시로 변경
            if not secret_key_input.startswith("*"):
                self.secret_key_input.setText("*" * len(secret_key))
                self._is_saved = True

            QMessageBox.information(
                self,
                "저장 완료",
                f"API 키가 안전하게 저장되었습니다.\n저장 위치: {api_keys_path.parent}"
            )

            # 보안: 사용된 평문 키를 메모리에서 즉시 삭제
            access_key = ""
            secret_key = ""
            gc.collect()

            self.settings_changed.emit()
            self.logger.info("API 키 저장 완료")

            # 저장 후 자동으로 API 연결 테스트 수행 (조용한 모드)
            self.logger.info("저장 후 자동 API 연결 테스트 시작")
            self.test_api_keys(silent=True)

        except Exception as e:
            self.logger.error(f"API 키 저장 중 오류: {e}")
            QMessageBox.warning(
                self,
                "저장 오류",
                f"API 키를 저장하는 중 오류가 발생했습니다:\n{str(e)}"
            )

    def test_api_keys(self, silent=False):
        """API 키 테스트

        Args:
            silent (bool): True인 경우 성공/실패 메시지 팝업을 표시하지 않음
        """
        # 보안 강화: 저장된 키를 임시 로드하여 테스트
        access_key, secret_key = self._secure_get_decrypted_keys()

        # UI에서 새로 입력된 키가 있는지 확인
        access_key_input = self.access_key_input.text().strip()
        secret_key_input = self.secret_key_input.text().strip()

        # 새로 입력된 키가 있으면 우선 사용
        if access_key_input and not access_key_input.startswith("*"):
            access_key = access_key_input
        if secret_key_input and not secret_key_input.startswith("*"):
            secret_key = secret_key_input
        elif secret_key_input.startswith("*") and hasattr(self, '_actual_secret_key') and self._actual_secret_key:
            secret_key = self._actual_secret_key

        # 입력 검증
        if not access_key or not secret_key:
            if not silent:
                QMessageBox.warning(self, "입력 오류", "Access Key와 Secret Key를 모두 입력해주세요.")
            self.logger.warning("API 테스트 실패 - Access Key 또는 Secret Key가 비어있음")
            self.api_status_changed.emit(False)
            return

        try:
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
                        "API 키가 유효하지 않거나 계좌 정보 조회에 실패했습니다.\nAPI 키 권한(계좌 조회) 설정을 확인해주세요."
                    )

                self.logger.warning("API 연결 테스트 실패 - 계좌 정보 조회 실패")
                self.api_status_changed.emit(False)

        except Exception as api_e:
            # 보안: 사용 후 민감한 데이터를 메모리에서 즉시 삭제
            access_key = ""
            secret_key = ""
            gc.collect()

            self.logger.error(f"API 테스트 중 오류: {api_e}")

            if not silent:
                QMessageBox.warning(
                    self,
                    "API 호출 오류",
                    f"API 테스트 중 오류가 발생했습니다:\n{str(api_e)}"
                )

            self.api_status_changed.emit(False)

    def delete_api_keys(self):
        """API 키 및 암호화 키 삭제"""
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

            # UI 초기화
            self.access_key_input.clear()
            self.secret_key_input.clear()
            self.trade_permission_checkbox.setChecked(False)

            # 메모리 정리 및 상태 초기화
            self._actual_secret_key = ""
            self._is_saved = False
            gc.collect()

            # 결과 메시지
            if deleted:
                QMessageBox.information(self, "삭제 완료", "API 키와 암호화 키가 안전하게 삭제되었습니다.")
            else:
                QMessageBox.information(self, "알림", "삭제할 API 키 또는 암호화 키가 존재하지 않습니다.")

            self.api_status_changed.emit(False)
            self.settings_changed.emit()
            self.logger.info("API 키 삭제 완료")

        except Exception as e:
            self.logger.error(f"API 키 삭제 중 오류: {e}")
            QMessageBox.warning(
                self,
                "삭제 오류",
                f"API 키 삭제 중 오류가 발생했습니다:\n{str(e)}"
            )
            # 보안: 오류 발생시에도 메모리 정리
            self._actual_secret_key = ""
            gc.collect()
