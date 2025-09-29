"""
테마 선택 위젯

이 모듈은 테마 선택 관련 UI 컴포넌트를 구현합니다.
- 라이트/다크 테마 선택
- 실시간 테마 변경 시그널
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QGroupBox, QFormLayout
)

# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)

class ThemeSelectorWidget(QWidget):
    """테마 선택 위젯"""

    # 시그널
    theme_changed = pyqtSignal(str)  # 테마 값 변경 시그널
    settings_changed = pyqtSignal()  # 일반 설정 변경 시그널

    def __init__(self, parent=None):
        """초기화

        Args:
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.setObjectName("widget-theme-selector")

        # 로깅 설정
        # Application Layer 로깅 서비스 사용 (임시 폴백)
        try:
            from upbit_auto_trading.application.services.logging_application_service import ApplicationLoggingService
            fallback_service = ApplicationLoggingService()
            self.logger = fallback_service.get_component_logger("ThemeSelectorWidget")
        except Exception:
            self.logger = None
        self.logger.info("🎨 테마 선택 위젯 초기화 시작")

        # 내부 상태
        self._current_theme = "light"
        self._is_loading = False

        # UI 설정
        self._setup_ui()

        self.logger.info("✅ 테마 선택 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 테마 설정 그룹
        theme_group = QGroupBox("테마 설정")
        theme_layout = QFormLayout(theme_group)

        # 테마 선택 콤보박스
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("라이트 테마", "light")
        self.theme_combo.addItem("다크 테마", "dark")
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)

        theme_layout.addRow("테마:", self.theme_combo)
        layout.addWidget(theme_group)

    def _on_theme_changed(self):
        """테마 변경 처리"""
        if self._is_loading:
            return

        theme_value = self.theme_combo.currentData()
        if theme_value and theme_value != self._current_theme:
            self._current_theme = theme_value
            self.logger.debug(f"🎨 테마 변경됨: {theme_value}")
            self.theme_changed.emit(theme_value)
            self.settings_changed.emit()

    def get_theme(self) -> str:
        """현재 선택된 테마 반환

        Returns:
            str: 현재 테마 ("light" 또는 "dark")
        """
        return self.theme_combo.currentData() or "light"

    def set_theme(self, theme: str):
        """테마 설정

        Args:
            theme: 설정할 테마 ("light" 또는 "dark")
        """
        self._is_loading = True
        try:
            index = self.theme_combo.findData(theme)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
                self._current_theme = theme
                self.logger.debug(f"🎨 테마 설정됨: {theme}")
            else:
                self.logger.warning(f"⚠️ 알 수 없는 테마: {theme}")
        finally:
            self._is_loading = False

    def reset_to_default(self):
        """기본값으로 재설정"""
        self.set_theme("light")
