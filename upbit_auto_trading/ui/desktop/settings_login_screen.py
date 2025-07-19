from PyQt6.QtWidgets import QVBoxLayout, QWidget
from .common.components import StyledLineEdit, PrimaryButton, StyledComboBox, StyledCheckBox

class SettingsLoginScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.api_key_input = StyledLineEdit("API키 입력")
        self.save_button = PrimaryButton("API키 저장")
        self.test_button = PrimaryButton("API키 테스트")
        self.db_combo = StyledComboBox(items=["SQLite", "PostgreSQL"])
        self.alert_check = StyledCheckBox("알림 설정")
        self.theme_combo = StyledComboBox(items=["Light", "Dark"])
        layout.addWidget(self.api_key_input)
        layout.addWidget(self.save_button)
        layout.addWidget(self.test_button)
        layout.addWidget(self.db_combo)
        layout.addWidget(self.alert_check)
        layout.addWidget(self.theme_combo)

        # 샘플 데이터
        self.api_key = ""
        self.db_type = "SQLite"
        self.alert_enabled = True
        self.theme = "Light"
        self.is_loading = False
        self.load_settings()

        # 이벤트 연결
        self.save_button.clicked.connect(self.save_api_key)
        self.test_button.clicked.connect(self.test_api_key)
        self.db_combo.currentIndexChanged.connect(self.change_db)
        self.alert_check.stateChanged.connect(self.toggle_alert)
        self.theme_combo.currentIndexChanged.connect(self.change_theme)

        # 최초 데이터 fetch
        self.fetch_settings()
    def load_settings(self):
        if self.is_loading:
            print("[테스트] 설정 데이터 로딩 중...")
            return
        print(f"[테스트] 현재 설정: API키={self.api_key}, DB={self.db_type}, 알림={self.alert_enabled}, 테마={self.theme}")

    def fetch_settings(self):
        self.is_loading = True
        self.load_settings()
        import time
        time.sleep(0.2)
        self.api_key = "TESTKEY"
        self.db_type = "SQLite"
        self.alert_enabled = True
        self.theme = "Light"
        self.is_loading = False
        self.load_settings()

    def save_all_settings(self):
        try:
            with open("settings.csv", "w", encoding="utf-8") as f:
                f.write(f"API키,{self.api_key}\nDB,{self.db_type}\n알림,{self.alert_enabled}\n테마,{self.theme}\n")
            print("[테스트] settings.csv 파일로 설정 저장 완료")
        except Exception as e:
            print(f"[에러] 설정 저장 실패: {e}")

    def save_api_key(self):
        self.api_key = self.api_key_input.text()
        print(f"[테스트] API키 저장: {self.api_key}")

    def test_api_key(self):
        print(f"[테스트] API키 테스트: {self.api_key_input.text()}")

    def change_db(self, idx):
        self.db_type = self.db_combo.currentText()
        print(f"[테스트] DB 변경: {self.db_type}")

    def toggle_alert(self, state):
        self.alert_enabled = bool(state)
        print(f"[테스트] 알림 설정: {self.alert_enabled}")

    def change_theme(self, idx):
        self.theme = self.theme_combo.currentText()
        print(f"[테스트] 테마 변경: {self.theme}")
