"""
UI 설정 View

이 모듈은 UI 설정 화면의 View 부분을 구현합니다.
- MVP 패턴의 View 역할
- 위젯 조합 및 레이아웃 관리
- Presenter와의 연동
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
)

# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)
from ..widgets import (
    ThemeSelectorWidget, WindowSettingsWidget,
    AnimationSettingsWidget, ChartSettingsWidget
)

class UISettingsView(QWidget):
    """UI 설정 View - MVP 패턴"""

    # 시그널
    apply_requested = pyqtSignal()  # 설정 적용 요청
    reset_requested = pyqtSignal()  # 기본값 복원 요청

    def __init__(self, parent=None, logging_service=None):
        """초기화

        Args:
            parent: 부모 위젯
            logging_service: Application Layer 로깅 서비스
        """
        super().__init__(parent)
        self.setObjectName("widget-ui-settings-view")

        # Application Layer 로깅 서비스 초기화
        if logging_service is not None:
            self.logger = logging_service
            self.logger.info("🎨 UI 설정 View 초기화 시작")
        else:
            # 폴백: 임시 로거
            try:
                from upbit_auto_trading.application.services.logging_application_service import ApplicationLoggingService
                fallback_service = ApplicationLoggingService()
                self.logger = fallback_service.get_component_logger("UISettingsView")
                self.logger.info("🎨 UI 설정 View 초기화 시작 (폴백 로거)")
            except Exception:
                self.logger = None

        # Presenter 참조
        self._presenter = None

        # UI 위젯들
        self.theme_widget = None
        self.window_widget = None
        self.animation_widget = None
        self.chart_widget = None

        # 버튼들
        self.apply_button = None
        self.reset_button = None

        # UI 설정
        self._setup_ui()

        if self.logger:
            self.logger.info("✅ UI 설정 View 초기화 완료")

    def _setup_ui(self):
        """UI 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 각 설정 위젯들 생성
        self.theme_widget = ThemeSelectorWidget()
        self.window_widget = WindowSettingsWidget()
        self.animation_widget = AnimationSettingsWidget()
        self.chart_widget = ChartSettingsWidget()

        # 위젯들을 레이아웃에 추가
        main_layout.addWidget(self.theme_widget)
        main_layout.addWidget(self.window_widget)
        main_layout.addWidget(self.animation_widget)
        main_layout.addWidget(self.chart_widget)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 기본값 복원 버튼
        self.reset_button = QPushButton("기본값으로 복원")
        self.reset_button.clicked.connect(self._on_reset_requested)
        button_layout.addWidget(self.reset_button)

        # 설정 저장 버튼
        self.apply_button = QPushButton("설정 저장")
        self.apply_button.clicked.connect(self._on_apply_requested)
        self.apply_button.setEnabled(False)  # 초기에는 비활성화
        button_layout.addWidget(self.apply_button)

        main_layout.addLayout(button_layout)

        # 하단 안내 메시지
        info_layout = QHBoxLayout()
        info_label = QLabel("💡 '기본값으로 복원'은 화면만 변경합니다. 실제 적용은 '설정 저장' 버튼을 클릭하세요")
        info_label.setStyleSheet("color: #666; font-size: 11px; padding: 10px;")
        info_layout.addWidget(info_label)
        main_layout.addLayout(info_layout)

        main_layout.addStretch()

    def set_presenter(self, presenter):
        """Presenter 설정

        Args:
            presenter: UI 설정 Presenter 인스턴스
        """
        self._presenter = presenter
        self.logger.info("🔗 Presenter 연결됨")

        # Presenter에 View 설정
        if self._presenter:
            self._presenter.set_view(self)

    def _on_apply_requested(self):
        """설정 적용 요청 처리"""
        self.logger.debug("💾 설정 적용 요청됨")
        self.apply_requested.emit()

        if self._presenter:
            self._presenter.apply_all_settings()

    def _on_reset_requested(self):
        """기본값 복원 요청 처리"""
        self.logger.debug("🔄 기본값 복원 요청됨")
        self.reset_requested.emit()

        if self._presenter:
            self._presenter.reset_to_defaults()

    def set_apply_button_state(self, enabled: bool, text: str = "설정 저장"):
        """적용 버튼 상태 설정

        Args:
            enabled: 버튼 활성화 여부
            text: 버튼 텍스트
        """
        if self.apply_button:
            self.apply_button.setEnabled(enabled)
            self.apply_button.setText(text)

    def load_settings(self):
        """설정 로드 (Presenter 위임)"""
        if self._presenter:
            self._presenter.load_settings()
        else:
            self.logger.warning("⚠️ Presenter가 없어 설정 로드 불가")

    # 기존 호환성을 위한 메서드들
    def save_settings(self):
        """설정 저장 (기존 호환성 유지)"""
        self._on_apply_requested()

    def save_all_settings(self):
        """모든 설정 저장 (기존 호환성 유지)"""
        self._on_apply_requested()

    def _reset_to_defaults(self):
        """기본값으로 복원 (기존 호환성 유지)"""
        self._on_reset_requested()

    # 시그널 지원 (기존 호환성)
    @property
    def settings_changed(self):
        """설정 변경 시그널 (기존 호환성)"""
        # 실제로는 각 위젯의 settings_changed 시그널을 조합
        return self.apply_requested

    @property
    def theme_changed(self):
        """테마 변경 시그널 (기존 호환성)"""
        if self.theme_widget:
            return self.theme_widget.theme_changed
        return None
