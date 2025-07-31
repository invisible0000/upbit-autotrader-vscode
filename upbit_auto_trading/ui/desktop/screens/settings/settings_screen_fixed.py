"""
설정 화면 모듈

이 모듈은 애플리케이션의 설정 화면을 구현합니다.
- API 키 관리
- 데이터베이스 설정
- 알림 설정
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QScrollArea, QHBoxLayout, QPushButton, 
    QFrame, QLabel, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt

from .api_key_manager import ApiKeyManager
from .database_settings import DatabaseSettings
from .notification_settings import NotificationSettings


class SettingsScreen(QWidget):
    """설정 화면 클래스"""
    
    # 설정 변경 시그널
    settings_changed = pyqtSignal()
    api_status_changed = pyqtSignal(bool)  # API 상태 변경 시그널 추가

    def __init__(self):
        super().__init__()
        self.setObjectName("screen-settings")
        
        # API 키 관리자 생성
        self.api_key_manager = ApiKeyManager()
        
        # 데이터베이스 설정 생성
        self.database_settings = DatabaseSettings()
        
        # 알림 설정 생성
        self.notification_settings = NotificationSettings()
        
        # 시그널 연결
        self._connect_signals()
        
        # UI 설정
        self._setup_ui()
        
        # 설정 로드
        self.load_all_settings()

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 제목 영역
        title_frame = QFrame()
        title_frame.setFixedHeight(60)
        title_frame.setStyleSheet("""
            QFrame {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                border: none;
            }
        """)
        
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(20, 0, 20, 0)
        
        # 제목 라벨
        title_label = QLabel("⚙️ 설정")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 저장 버튼
        save_button = QPushButton("모든 설정 저장")
        save_button.clicked.connect(self.save_all_settings)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        title_layout.addWidget(save_button)
        
        layout.addWidget(title_frame)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
        """)
        
        # 탭 추가
        self.tab_widget.addTab(self.api_key_manager, "API 키")
        self.tab_widget.addTab(self.database_settings, "데이터베이스")
        self.tab_widget.addTab(self.notification_settings, "알림")
        
        layout.addWidget(self.tab_widget)

    def _connect_signals(self):
        """시그널 연결"""
        try:
            # 각 설정 위젯의 설정 변경 시그널 연결
            self.api_key_manager.settings_changed.connect(self._on_settings_changed)
            self.api_key_manager.api_status_changed.connect(self._on_api_status_changed)  # API 상태 시그널 연결
            self.database_settings.settings_changed.connect(self._on_settings_changed)
            self.notification_settings.settings_changed.connect(self._on_settings_changed)
        except Exception as e:
            print(f"❌ 시그널 연결 실패: {e}")

    def load_all_settings(self):
        """모든 설정 로드"""
        # 각 설정 위젯의 설정 로드
        self.api_key_manager.load_settings()
        self.database_settings.load_settings()
        self.notification_settings.load_settings()
    
    def save_all_settings(self):
        """모든 설정 저장"""
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
        
    def _on_api_status_changed(self, connected):
        """API 연결 상태 변경 시 호출되는 메서드"""
        # API 상태 변경 시그널을 상위로 전달
        self.api_status_changed.emit(connected)
