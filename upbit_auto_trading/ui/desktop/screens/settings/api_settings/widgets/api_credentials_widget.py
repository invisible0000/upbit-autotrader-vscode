"""
API 자격증명 위젯

API 키 입력 및 마스킹 처리를 담당하는 위젯

Phase 2 마이그레이션으로 생성됨:
- 기존: ApiKeyManagerSecure의 API 키 입력 부분
- 새로운: 독립적인 위젯으로 분리
"""

from typing import Tuple
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit,
                             QCheckBox, QGroupBox)
from PyQt6.QtCore import pyqtSignal, Qt

# Application Layer - Infrastructure 의존성 격리
from upbit_auto_trading.application.services.logging_application_service import IPresentationLogger

class ApiCredentialsWidget(QWidget):
    """
    API 자격증명 입력 위젯

    Access Key와 Secret Key 입력을 처리하며,
    보안 마스킹과 키 표시 기능을 제공합니다.
    """

    # 시그널 정의
    credentials_changed = pyqtSignal(str, str)  # access_key, secret_key
    input_changed = pyqtSignal(str, str)  # field_name, value

    def __init__(self, parent=None, logging_service: IPresentationLogger = None):
        """API 자격증명 위젯 초기화

        Args:
            parent: 부모 위젯
            logging_service: Application Layer 로깅 서비스
        """
        super().__init__(parent)
        self.setObjectName("widget-api-credentials")

        # 로깅 설정 - DI 패턴 적용
        if logging_service:
            self.logger = logging_service.get_component_logger("ApiCredentialsWidget")
        else:
            raise ValueError("ApiCredentialsWidget에 logging_service가 주입되지 않았습니다")

        # 상태 관리
        self._is_editing_mode = False

        self._setup_ui()
        self._connect_signals()

        self.logger.info("✅ API 자격증명 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 설정"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
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
        self.main_layout.addWidget(api_key_group)

    def _connect_signals(self):
        """시그널 연결"""
        self.show_keys_checkbox.stateChanged.connect(self._toggle_key_visibility)
        self.access_key_input.textChanged.connect(self._on_access_key_changed)
        self.secret_key_input.textChanged.connect(self._on_secret_key_changed)

    def _toggle_key_visibility(self, state):
        """키 표시/숨김 토글"""
        if state == Qt.CheckState.Checked.value:
            # 키 표시: 현재 입력 중인 텍스트만 보여줌
            self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.logger.debug("🔓 Secret Key 표시 모드 활성화 (편집 중 텍스트만)")
        else:
            # 키 숨김: 표준 암호 모드
            self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.logger.debug("🔒 Secret Key 숨김 모드 활성화")

    def _on_access_key_changed(self):
        """Access Key 변경 시 처리"""
        self.input_changed.emit("access_key", self.access_key_input.text())
        self._emit_credentials_changed()

    def _on_secret_key_changed(self):
        """Secret Key 변경 시 처리"""
        current_text = self.secret_key_input.text().strip()
        if current_text and not current_text.startswith("●"):
            self._is_editing_mode = True
            self.logger.debug("🔓 Secret Key 편집 모드 전환")

        self.input_changed.emit("secret_key", current_text)
        self._emit_credentials_changed()

    def _emit_credentials_changed(self):
        """자격증명 변경 시그널 발생"""
        access_key = self.access_key_input.text().strip()
        secret_key = self.secret_key_input.text().strip()
        self.credentials_changed.emit(access_key, secret_key)

    def set_credentials(self, access_key: str, secret_key: str):
        """자격증명 설정"""
        self.access_key_input.setText(access_key)
        self.secret_key_input.setText(secret_key)

        # 마스킹된 키인지 확인
        if secret_key.startswith("●"):
            self._is_editing_mode = False
        else:
            self._is_editing_mode = True

        self.logger.debug("API 자격증명 설정 완료")

    def get_credentials(self) -> Tuple[str, str]:
        """현재 자격증명 반환"""
        return (
            self.access_key_input.text().strip(),
            self.secret_key_input.text().strip()
        )

    def clear_credentials(self):
        """자격증명 지우기"""
        self.access_key_input.clear()
        self.secret_key_input.clear()
        self._is_editing_mode = False
        self.logger.debug("API 자격증명 지움 완료")

    def is_editing_mode(self) -> bool:
        """편집 모드 여부 반환"""
        return self._is_editing_mode
