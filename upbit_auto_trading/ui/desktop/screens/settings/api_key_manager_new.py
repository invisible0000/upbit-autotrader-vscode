import os
import json
import gc
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit, QCheckBox, QLabel,
    QHBoxLayout, QPushButton, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from cryptography.fernet import Fernet

class ApiKeyManager(QWidget):
    """API 키 관리자 위젯 - 보안 강화 버전"""
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-api-key-manager")
        self._actual_secret_key = ""  # 실제 secret key 보관용
        self._setup_encryption_key()
        self._setup_ui()
        self._connect_signals()

    def _setup_encryption_key(self):
        """암호화 키 설정 및 생성"""
        # data 디렉터리 설정
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..')
        data_dir = os.path.join(base_dir, 'data')
        key_dir = os.path.join(data_dir, "settings")
        key_path = os.path.join(key_dir, "encryption_key.key")
        
        # 디렉터리 생성
        if not os.path.exists(key_dir):
            os.makedirs(key_dir)
            
        # 암호화 키 생성 또는 로드
        if not os.path.exists(key_path):
            key = Fernet.generate_key()
            with open(key_path, "wb") as key_file:
                key_file.write(key)
                
        with open(key_path, "rb") as key_file:
            self.encryption_key = key_file.read()
        self.fernet = Fernet(self.encryption_key)

    def _setup_ui(self):
        """UI 설정"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # API 키 입력 그룹
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
        
        # API 권한 설정 그룹
        permissions_group = QGroupBox("API 권한 설정")
        permissions_layout = QVBoxLayout(permissions_group)
        
        # 조회 권한 (필수)
        self.read_permission_checkbox = QCheckBox("조회 권한")
        self.read_permission_checkbox.setObjectName("checkbox-read-permission")
        self.read_permission_checkbox.setChecked(True)
        self.read_permission_checkbox.setEnabled(False)
        
        # 거래 권한 (선택)
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

    def _secure_get_decrypted_keys(self):
        """
        보안 기능: 암호화된 키 파일에서 복호화하여 반환
        메모리 사용 후 즉시 정리하는 방식
        
        Returns:
            tuple: (access_key, secret_key) 또는 (None, None)
        """
        try:
            base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..')
            data_dir = os.path.join(base_dir, 'data')
            settings_dir = os.path.join(data_dir, "settings")
            settings_path = os.path.join(settings_dir, "api_keys.json")
            
            if not os.path.exists(settings_path):
                return None, None
                
            # UTF-8 인코딩으로 파일 읽기
            with open(settings_path, "r", encoding='utf-8') as f:
                settings = json.load(f)
            
            access_key = None
            secret_key = None
            
            if "access_key" in settings:
                access_key = self.fernet.decrypt(settings["access_key"].encode('utf-8')).decode('utf-8')
            if "secret_key" in settings:
                secret_key = self.fernet.decrypt(settings["secret_key"].encode('utf-8')).decode('utf-8')
                
            return access_key, secret_key
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "복호화 오류",
                f"API 키 설정을 읽는 중 오류가 발생했습니다:\n{str(e)}"
            )
            return None, None

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

    def load_settings(self):
        """설정 파일에서 API 키 로드"""
        try:
            base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..')
            data_dir = os.path.join(base_dir, 'data')
            settings_dir = os.path.join(data_dir, "settings")
            settings_path = os.path.join(settings_dir, "api_keys.json")
            
            if not os.path.exists(settings_path):
                return
                
            # UTF-8 인코딩으로 파일 읽기
            with open(settings_path, "r", encoding='utf-8') as f:
                settings = json.load(f)
                
            if "access_key" in settings:
                access_key = self.fernet.decrypt(settings["access_key"].encode()).decode()
                self.access_key_input.setText(access_key)
                
            if "secret_key" in settings:
                secret_key = self.fernet.decrypt(settings["secret_key"].encode()).decode()
                # Secret key는 보안상 ***로 표시
                self.secret_key_input.setText("*" * len(secret_key) if secret_key else "")
                # 실제 값은 내부변수로 보관 (보안용)
                self._actual_secret_key = secret_key
                
            if "trade_permission" in settings:
                self.trade_permission_checkbox.setChecked(settings["trade_permission"])
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "설정 로드 오류",
                f"API 키 설정을 불러오는 중 오류가 발생했습니다:\n{str(e)}"
            )

    def save_settings(self):
        """외부 호출용 저장 함수"""
        self.save_api_keys()

    def save_api_keys(self):
        """API 키 저장"""
        try:
            access_key = self.access_key_input.text().strip()
            secret_key_input = self.secret_key_input.text().strip()
            
            # Secret key가 *로 표시된 경우 실제 저장된 값을 사용
            if secret_key_input.startswith("*") and hasattr(self, '_actual_secret_key'):
                secret_key = self._actual_secret_key
            else:
                secret_key = secret_key_input
                self._actual_secret_key = secret_key  # 새로 입력된 경우 업데이트
            
            trade_permission = self.trade_permission_checkbox.isChecked()
            
            # 입력 검증
            if not access_key or not secret_key:
                QMessageBox.warning(
                    self,
                    "입력 오류",
                    "Access Key와 Secret Key를 모두 입력해주세요."
                )
                return
                
            # 파일 경로 설정
            base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..')
            data_dir = os.path.join(base_dir, 'data')
            settings_dir = os.path.join(data_dir, "settings")
            settings_path = os.path.join(settings_dir, "api_keys.json")
            
            # 디렉터리 생성
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
                
            # 암호화
            encrypted_access_key = self.fernet.encrypt(access_key.encode('utf-8')).decode('utf-8')
            encrypted_secret_key = self.fernet.encrypt(secret_key.encode('utf-8')).decode('utf-8')
            
            # 설정 딕셔너리
            settings = {
                "access_key": encrypted_access_key,
                "secret_key": encrypted_secret_key,
                "trade_permission": trade_permission
            }
            
            # UTF-8 인코딩으로 파일 저장
            with open(settings_path, "w", encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
                
            QMessageBox.information(
                self,
                "저장 완료",
                "API 키가 저장되었습니다."
            )
            
            # 보안: 사용된 평문 키를 메모리에서 즉시 삭제
            access_key = ""
            secret_key = ""
            gc.collect()
            
            self.settings_changed.emit()
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "저장 오류",
                f"API 키를 저장하는 중 오류가 발생했습니다:\n{str(e)}"
            )

    def test_api_keys(self):
        """API 키 테스트"""
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
            QMessageBox.warning(self, "입력 오류", "Access Key와 Secret Key를 모두 입력해주세요.")
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
                        
                QMessageBox.information(
                    self,
                    "테스트 성공",
                    f"API 키가 정상적으로 작동하며 서버에 연결되었습니다.\n\n조회된 잔고(KRW) 금액: {krw_balance:,.0f} 원"
                )
            else:
                QMessageBox.warning(
                    self,
                    "테스트 실패",
                    "API 키가 유효하지 않거나 계좌 정보 조회에 실패했습니다.\nAPI 키 권한(계좌 조회) 설정을 확인해주세요."
                )
                
        except Exception as api_e:
            # 보안: 사용 후 민감한 데이터를 메모리에서 즉시 삭제
            access_key = ""
            secret_key = ""
            gc.collect()
            
            QMessageBox.warning(
                self,
                "API 호출 오류",
                f"API 테스트 중 오류가 발생했습니다:\n{str(api_e)}"
            )

    def delete_api_keys(self):
        """API 키 및 암호화 키 삭제"""
        try:
            base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..')
            data_dir = os.path.join(base_dir, 'data')
            settings_dir = os.path.join(data_dir, "settings")
            settings_path = os.path.join(settings_dir, "api_keys.json")
            key_path = os.path.join(settings_dir, "encryption_key.key")
            
            deleted = False
            
            # API 키 파일 삭제
            if os.path.exists(settings_path):
                os.remove(settings_path)
                deleted = True
                
            # 암호화 키 파일 삭제
            if os.path.exists(key_path):
                os.remove(key_path)
                deleted = True
                
            # UI 초기화
            self.access_key_input.clear()
            self.secret_key_input.clear()
            self.trade_permission_checkbox.setChecked(False)
            
            # 메모리 정리
            self._actual_secret_key = ""
            gc.collect()
            
            # 결과 메시지
            if deleted:
                QMessageBox.information(self, "삭제 완료", "API 키와 암호화 키가 삭제되었습니다.")
            else:
                QMessageBox.information(self, "알림", "삭제할 API 키 또는 암호화 키가 존재하지 않습니다.")
                
            self.settings_changed.emit()
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "삭제 오류",
                f"API 키 삭제 중 오류가 발생했습니다:\n{str(e)}"
            )
            # 보안: 오류 발생시에도 메모리 정리
            self._actual_secret_key = ""
            gc.collect()
