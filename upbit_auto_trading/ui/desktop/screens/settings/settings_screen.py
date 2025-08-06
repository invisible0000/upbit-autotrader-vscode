"""
설정 화면 모듈

이 모듈은 애플리케이션의 설정 화면을 구현합니다.
- API 키 관리
- 데이터베이스 설정
- 알림 설정
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from .api_key_manager_secure import ApiKeyManagerSecure as ApiKeyManager
from .database_settings import DatabaseSettings
from .notification_settings import NotificationSettings


class SettingsScreen(QWidget):
    """설정 화면 클래스"""

    # 설정 변경 시그널
    settings_changed = pyqtSignal()
    api_status_changed = pyqtSignal(bool)  # API 상태 변경 시그널 추가
    db_status_changed = pyqtSignal(bool)   # DB 상태 변경 시그널 추가

    def __init__(self, parent=None, settings_service=None):
        """초기화

        Args:
            parent: 부모 위젯
            settings_service: SettingsService 인스턴스 (DI Container에서 주입)
        """
        super().__init__(parent)
        self.setObjectName("screen-settings")

        # SettingsService 저장 (Infrastructure Layer 통합)
        self.settings_service = settings_service

        # 위젯 생성
        self.api_key_manager = ApiKeyManager()
        self.database_settings = DatabaseSettings()
        self.notification_settings = NotificationSettings()

        # UI 설정 위젯 생성 (Infrastructure Layer 기반)
        self.ui_settings = None
        try:
            from .ui_settings import UISettings
            self.ui_settings = UISettings(settings_service=self.settings_service)
        except Exception as e:
            print(f"⚠️ UI 설정 위젯 생성 실패: {e}")
            # settings_service가 없어도 기본 UI 설정 탭은 보이도록 함
            from .ui_settings import UISettings
            self.ui_settings = UISettings(settings_service=None)

        # UI 설정
        self._setup_ui()

        # 시그널 연결
        self._connect_signals()

        # 설정 로드
        self._load_settings()

    def _setup_ui(self):
        """UI 설정"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # 제목
        title_label = QLabel("설정")
        title_label.setObjectName("settings-title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        main_layout.addWidget(title_label)

        # 설명
        description_label = QLabel("애플리케이션 설정을 관리합니다.")
        description_label.setObjectName("settings-description")
        description_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(description_label)

        # 구분선
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #cccccc;")
        main_layout.addWidget(line)

        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("settings-tab-widget")

        # UI 설정 탭 (Infrastructure Layer 기반 - 첫 번째 탭으로 배치)
        if self.ui_settings:
            self.tab_widget.addTab(self.ui_settings, "UI 설정")

        # API 키 탭
        self.tab_widget.addTab(self.api_key_manager, "API 키")

        # 데이터베이스 탭
        self.tab_widget.addTab(self.database_settings, "데이터베이스")

        # 알림 탭
        self.tab_widget.addTab(self.notification_settings, "알림")

        main_layout.addWidget(self.tab_widget)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        # 공간 추가
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        button_layout.addItem(spacer)

        # 저장 버튼
        self.save_all_button = QPushButton("모든 설정 저장")
        self.save_all_button.setObjectName("settings-save-all-button")
        self.save_all_button.setMinimumWidth(150)
        button_layout.addWidget(self.save_all_button)

        main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """시그널 연결"""
        # 저장 버튼 클릭 시 모든 설정 저장
        self.save_all_button.clicked.connect(self.save_all_settings)

        # UI 설정 위젯 시그널 연결 (Infrastructure Layer 기반)
        if self.ui_settings:
            self.ui_settings.settings_changed.connect(self._on_settings_changed)
            # 테마 변경 즉시 반영 (상위 MainWindow로 전달)
            self.ui_settings.theme_changed.connect(self._on_theme_immediately_changed)

        # 각 설정 위젯의 설정 변경 시그널 연결
        self.api_key_manager.settings_changed.connect(self._on_settings_changed)
        self.api_key_manager.api_status_changed.connect(self._on_api_status_changed)  # API 상태 시그널 연결
        self.database_settings.settings_changed.connect(self._on_settings_changed)
        self.database_settings.db_status_changed.connect(self._on_db_status_changed)  # DB 상태 시그널 연결
        self.notification_settings.settings_changed.connect(self._on_settings_changed)

    def _load_settings(self):
        """설정 로드"""
        # UI 설정 로드 (Infrastructure Layer 기반)
        if self.ui_settings:
            self.ui_settings.load_settings()

        # 각 설정 위젯의 설정 로드
        self.api_key_manager.load_settings()
        self.database_settings.load_settings()
        self.notification_settings.load_settings()

    def save_all_settings(self):
        """모든 설정 저장"""
        # UI 설정 저장 (Infrastructure Layer 기반)
        if self.ui_settings:
            self.ui_settings.save_settings()

        # 각 설정 위젯의 설정 저장
        self.api_key_manager.save_settings()
        self.database_settings.save_settings()
        self.notification_settings.save_settings()

        # 설정 변경 시그널 발생
        self.settings_changed.emit()

    def _on_settings_changed(self):
        """설정 변경 시 호출되는 메서드"""
        # 설정 변경 시그널 발생
        self.settings_changed.emit()

    def _on_theme_immediately_changed(self, theme_value):
        """테마 즉시 변경 처리 (Infrastructure Layer 기반)"""
        # 상위 MainWindow에 테마 변경 즉시 반영 요청
        # 설정 저장과 별도로 즉시 적용
        if self.settings_service:
            try:
                self.settings_service.update_ui_setting("theme", theme_value)
                print(f"✅ 테마 즉시 변경: {theme_value}")
                # 설정 변경 시그널 발생하여 MainWindow에서 테마 즉시 적용
                self.settings_changed.emit()
            except Exception as e:
                print(f"❌ 테마 즉시 변경 실패: {e}")

    def _on_api_status_changed(self, connected):
        """API 연결 상태 변경 시 호출되는 메서드"""
        # API 상태 변경 시그널을 상위로 전달
        self.api_status_changed.emit(connected)

    def _on_db_status_changed(self, connected):
        """DB 연결 상태 변경 시 호출되는 메서드"""
        # DB 상태 변경 시그널을 상위로 전달
        self.db_status_changed.emit(connected)
