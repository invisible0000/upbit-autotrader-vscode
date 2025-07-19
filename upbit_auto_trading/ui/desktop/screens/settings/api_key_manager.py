
import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit, QCheckBox, QLabel,
    QHBoxLayout, QPushButton, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from cryptography.fernet import Fernet

class ApiKeyManager(QWidget):
    """API 키 관리 위젯 클래스"""
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-api-key-manager")
        self._setup_encryption_key()
        self._setup_ui()
        self._connect_signals()

    def _setup_encryption_key(self):
        # data 폴더에 키 저장
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..')
        data_dir = os.path.join(base_dir, 'data')
        key_dir = os.path.join(data_dir, "settings")
        key_path = os.path.join(key_dir, "encryption_key.key")
        if not os.path.exists(key_dir):
            os.makedirs(key_dir)
        if not os.path.exists(key_path):
            key = Fernet.generate_key()
            with open(key_path, "wb") as key_file:
                key_file.write(key)
        with open(key_path, "rb") as key_file:
            self.encryption_key = key_file.read()
        self.fernet = Fernet(self.encryption_key)

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        api_key_group = QGroupBox("업비트 API 키")
        api_key_layout = QVBoxLayout(api_key_group)
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 10, 0, 10)
        form_layout.setSpacing(10)
        self.access_key_input = QLineEdit()
        self.access_key_input.setObjectName("input-access-key")
        self.access_key_input.setPlaceholderText("Access Key를 입력하세요")
        form_layout.addRow("Access Key:", self.access_key_input)
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setObjectName("input-secret-key")
        self.secret_key_input.setPlaceholderText("Secret Key를 입력하세요")
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Secret Key:", self.secret_key_input)
        self.show_keys_checkbox = QCheckBox("키 표시")
        self.show_keys_checkbox.setObjectName("checkbox-show-keys")
        form_layout.addRow("", self.show_keys_checkbox)
        api_key_layout.addLayout(form_layout)
        permissions_group = QGroupBox("API 키 권한")
        permissions_layout = QVBoxLayout(permissions_group)
        self.read_permission_checkbox = QCheckBox("조회 권한")
        self.read_permission_checkbox.setObjectName("checkbox-read-permission")
        self.read_permission_checkbox.setChecked(True)
        self.read_permission_checkbox.setEnabled(False)
        self.trade_permission_checkbox = QCheckBox("거래 권한")
        self.trade_permission_checkbox.setObjectName("checkbox-trade-permission")
        permissions_layout.addWidget(self.read_permission_checkbox)
        permissions_layout.addWidget(self.trade_permission_checkbox)
        permissions_info = QLabel("* 조회 권한은 필수입니다.\n* 거래 권한은 실제 거래를 위해 필요합니다.")
        permissions_info.setObjectName("label-permissions-info")
        permissions_info.setStyleSheet("color: #666666; font-size: 10px;")
        permissions_layout.addWidget(permissions_info)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)
        self.save_button = QPushButton("저장")
        self.save_button.setObjectName("button-save-api-keys")
        button_layout.addWidget(self.save_button)
        self.test_button = QPushButton("테스트")
        self.test_button.setObjectName("button-test-api-keys")
        button_layout.addWidget(self.test_button)
        self.delete_button = QPushButton("삭제")
        self.delete_button.setObjectName("button-delete-api-keys")
        button_layout.addWidget(self.delete_button)
        self.main_layout.addWidget(api_key_group)
        self.main_layout.addWidget(permissions_group)
        self.main_layout.addLayout(button_layout)
        self.main_layout.addStretch(1)

    def _connect_signals(self):
        self.show_keys_checkbox.stateChanged.connect(self._toggle_key_visibility)
        self.save_button.clicked.connect(self.save_api_keys)
        self.test_button.clicked.connect(self.test_api_keys)
        self.delete_button.clicked.connect(self.delete_api_keys)
    def delete_api_keys(self):
        try:
            base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..')
            data_dir = os.path.join(base_dir, 'data')
            settings_dir = os.path.join(data_dir, "settings")
            settings_path = os.path.join(settings_dir, "api_keys.json")
            key_path = os.path.join(settings_dir, "encryption_key.key")
            deleted = False
            if os.path.exists(settings_path):
                os.remove(settings_path)
                deleted = True
            if os.path.exists(key_path):
                os.remove(key_path)
                deleted = True
            self.access_key_input.clear()
            self.secret_key_input.clear()
            self.trade_permission_checkbox.setChecked(False)
            if deleted:
                QMessageBox.information(self, "삭제 완료", "API 키와 암호화 키가 삭제되었습니다.")
            else:
                QMessageBox.information(self, "삭제", "삭제할 API 키 또는 암호화 키 파일이 없습니다.")
            self.settings_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "삭제 오류", f"API 키 삭제 중 오류가 발생했습니다:\n{str(e)}")

    def _toggle_key_visibility(self, state):
        if state == Qt.CheckState.Checked.value:
            self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def load_settings(self):
        try:
            base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..')
            data_dir = os.path.join(base_dir, 'data')
            settings_dir = os.path.join(data_dir, "settings")
            settings_path = os.path.join(settings_dir, "api_keys.json")
            if not os.path.exists(settings_path):
                return
            with open(settings_path, "r") as f:
                settings = json.load(f)
            if "access_key" in settings:
                access_key = self.fernet.decrypt(settings["access_key"].encode()).decode()
                self.access_key_input.setText(access_key)
            if "secret_key" in settings:
                secret_key = self.fernet.decrypt(settings["secret_key"].encode()).decode()
                self.secret_key_input.setText(secret_key)
            if "trade_permission" in settings:
                self.trade_permission_checkbox.setChecked(settings["trade_permission"])
        except Exception as e:
            QMessageBox.warning(
                self,
                "설정 로드 오류",
                f"API 키 설정을 로드하는 중 오류가 발생했습니다:\n{str(e)}"
            )

    def save_settings(self):
        self.save_api_keys()

    def save_api_keys(self):
        try:
            access_key = self.access_key_input.text().strip()
            secret_key = self.secret_key_input.text().strip()
            trade_permission = self.trade_permission_checkbox.isChecked()
            if not access_key or not secret_key:
                QMessageBox.warning(
                    self,
                    "입력 오류",
                    "Access Key와 Secret Key를 모두 입력해주세요."
                )
                return
            base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..')
            data_dir = os.path.join(base_dir, 'data')
            settings_dir = os.path.join(data_dir, "settings")
            settings_path = os.path.join(settings_dir, "api_keys.json")
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
            encrypted_access_key = self.fernet.encrypt(access_key.encode()).decode()
            encrypted_secret_key = self.fernet.encrypt(secret_key.encode()).decode()
            settings = {
                "access_key": encrypted_access_key,
                "secret_key": encrypted_secret_key,
                "trade_permission": trade_permission
            }
            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=4)
            QMessageBox.information(
                self,
                "저장 완료",
                "API 키가 저장되었습니다."
            )
            self.settings_changed.emit()
        except Exception as e:
            QMessageBox.warning(
                self,
                "저장 오류",
                f"API 키를 저장하는 중 오류가 발생했습니다:\n{str(e)}"
            )

    def test_api_keys(self):
        access_key = self.access_key_input.text().strip()
        secret_key = self.secret_key_input.text().strip()
        if not access_key or not secret_key:
            QMessageBox.warning(self, "입력 오류", "Access Key와 Secret Key를 모두 입력해주세요.")
            return
        try:
            from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
            api = UpbitAPI(access_key, secret_key)
            accounts = api.get_account()
            if accounts:
                krw_balance = 0
                for acc in accounts:
                    if acc.get('currency') == 'KRW':
                        krw_balance = float(acc.get('balance', 0))
                        break
                QMessageBox.information(
                    self,
                    "테스트 성공",
                    f"API 키가 유효하며 서버에 정상적으로 연결되었습니다.\n\n조회된 원화(KRW) 잔고: {krw_balance:,.0f} 원"
                )
            else:
                QMessageBox.warning(
                    self,
                    "테스트 실패",
                    "API 키가 유효하지 않거나, 계좌 정보 조회에 실패했습니다.\nAPI 키의 권한(계좌 조회) 설정을 확인해주세요."
                )
        except Exception as api_e:
            QMessageBox.warning(
                self,
                "API 호출 오류",
                f"API 키 테스트 중 오류가 발생했습니다:\n{str(api_e)}"
            )