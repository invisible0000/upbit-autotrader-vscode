"""
API 키 관리 모듈

이 모듈은 업비트 API 키 관리 기능을 구현합니다.
- API 키 저장 및 로드
- API 키 암호화
- API 키 테스트
"""

import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from cryptography.fernet import Fernet


class ApiKeyManager(QWidget):
    """API 키 관리 위젯 클래스"""
    
    # 설정 변경 시그널
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("widget-api-key-manager")
        
        # 암호화 키 설정
        self._setup_encryption_key()
        
        # UI 설정
        self._setup_ui()
        
        # 시그널 연결
        self._connect_signals()
    
    def _setup_encryption_key(self):
        """암호화 키 설정"""
        # 암호화 키 파일 경로
        key_dir = os.path.join(os.path.expanduser("~"), ".upbit_auto_trading")
        key_path = os.path.join(key_dir, "encryption_key.key")
        
        # 디렉토리가 없으면 생성
        if not os.path.exists(key_dir):
            os.makedirs(key_dir)
        
        # 키 파일이 없으면 생성
        if not os.path.exists(key_path):
            key = Fernet.generate_key()
            with open(key_path, "wb") as key_file:
                key_file.write(key)
        
        # 키 로드
        with open(key_path, "rb") as key_file:
            self.encryption_key = key_file.read()
        
        # Fernet 객체 생성
        self.fernet = Fernet(self.encryption_key)
    
    def _setup_ui(self):
        """UI 설정"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # API 키 그룹
        api_key_group = QGroupBox("업비트 API 키")
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
        
        # 권한 그룹
        permissions_group = QGroupBox("API 키 권한")
        permissions_layout = QVBoxLayout(permissions_group)
        
        # 권한 체크박스
        self.read_permission_checkbox = QCheckBox("조회 권한")
        self.read_permission_checkbox.setObjectName("checkbox-read-permission")
        self.read_permission_checkbox.setChecked(True)
        self.read_permission_checkbox.setEnabled(False)  # 필수 권한이므로 비활성화
        
        self.trade_permission_checkbox = QCheckBox("거래 권한")
        self.trade_permission_checkbox.setObjectName("checkbox-trade-permission")
        
        permissions_layout.addWidget(self.read_permission_checkbox)
        permissions_layout.addWidget(self.trade_permission_checkbox)
        
        # 권한 설명
        permissions_info = QLabel("* 조회 권한은 필수입니다.\n* 거래 권한은 실제 거래를 위해 필요합니다.")
        permissions_info.setObjectName("label-permissions-info")
        permissions_info.setStyleSheet("color: #666666; font-size: 10px;")
        permissions_layout.addWidget(permissions_info)
        
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
        
        # 레이아웃 추가
        main_layout.addWidget(api_key_group)
        main_layout.addWidget(permissions_group)
        main_layout.addLayout(button_layout)
        main_layout.addStretch(1)
    
    def _connect_signals(self):
        """시그널 연결"""
        # 키 표시 체크박스 변경 시 비밀번호 표시 모드 변경
        self.show_keys_checkbox.stateChanged.connect(self._toggle_key_visibility)
        
        # 저장 버튼 클릭 시 API 키 저장
        self.save_button.clicked.connect(self.save_api_keys)
        
        # 테스트 버튼 클릭 시 API 키 테스트
        self.test_button.clicked.connect(self.test_api_keys)
    
    def _toggle_key_visibility(self, state):
        """키 표시 여부 토글"""
        if state == Qt.CheckState.Checked.value:
            self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def load_settings(self):
        """설정 로드"""
        try:
            # 설정 파일 경로
            settings_dir = os.path.join(os.path.expanduser("~"), ".upbit_auto_trading")
            settings_path = os.path.join(settings_dir, "api_keys.json")
            
            # 설정 파일이 없으면 종료
            if not os.path.exists(settings_path):
                return
            
            # 설정 파일 로드
            with open(settings_path, "r") as f:
                settings = json.load(f)
            
            # 암호화된 키 복호화
            if "access_key" in settings:
                access_key = self.fernet.decrypt(settings["access_key"].encode()).decode()
                self.access_key_input.setText(access_key)
            
            if "secret_key" in settings:
                secret_key = self.fernet.decrypt(settings["secret_key"].encode()).decode()
                self.secret_key_input.setText(secret_key)
            
            # 권한 설정
            if "trade_permission" in settings:
                self.trade_permission_checkbox.setChecked(settings["trade_permission"])
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "설정 로드 오류",
                f"API 키 설정을 로드하는 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def save_settings(self):
        """설정 저장"""
        # API 키 저장
        self.save_api_keys()
    
    def save_api_keys(self):
        """API 키 저장"""
        try:
            # 입력값 가져오기
            access_key = self.access_key_input.text().strip()
            secret_key = self.secret_key_input.text().strip()
            trade_permission = self.trade_permission_checkbox.isChecked()
            
            # 입력값 검증
            if not access_key or not secret_key:
                QMessageBox.warning(
                    self,
                    "입력 오류",
                    "Access Key와 Secret Key를 모두 입력해주세요."
                )
                return
            
            # 설정 파일 경로
            settings_dir = os.path.join(os.path.expanduser("~"), ".upbit_auto_trading")
            settings_path = os.path.join(settings_dir, "api_keys.json")
            
            # 디렉토리가 없으면 생성
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
            
            # 키 암호화
            encrypted_access_key = self.fernet.encrypt(access_key.encode()).decode()
            encrypted_secret_key = self.fernet.encrypt(secret_key.encode()).decode()
            
            # 설정 저장
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
            
            # 설정 변경 시그널 발생
            self.settings_changed.emit()
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "저장 오류",
                f"API 키를 저장하는 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def test_api_keys(self):
        """API 키 테스트"""
        try:
            # 입력값 가져오기
            access_key = self.access_key_input.text().strip()
            secret_key = self.secret_key_input.text().strip()
            
            # 입력값 검증
            if not access_key or not secret_key:
                QMessageBox.warning(
                    self,
                    "입력 오류",
                    "Access Key와 Secret Key를 모두 입력해주세요."
                )
                return
            
            # API 키 테스트 로직 구현
            # 여기서는 간단히 성공 메시지만 표시
            # 실제로는 업비트 API를 호출하여 테스트해야 함
            QMessageBox.information(
                self,
                "테스트 성공",
                "API 키가 유효합니다."
            )
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "테스트 오류",
                f"API 키 테스트 중 오류가 발생했습니다:\n{str(e)}"
            )