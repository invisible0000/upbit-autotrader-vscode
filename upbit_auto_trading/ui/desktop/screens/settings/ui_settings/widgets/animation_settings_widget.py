"""
애니메이션 설정 위젯

이 모듈은 애니메이션 관련 설정 UI 컴포넌트를 구현합니다.
- UI 애니메이션 활성화
- 부드러운 스크롤링 설정
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QCheckBox, QGroupBox, QFormLayout
)

from upbit_auto_trading.infrastructure.logging import create_component_logger


class AnimationSettingsWidget(QWidget):
    """애니메이션 설정 위젯"""

    # 시그널
    settings_changed = pyqtSignal()  # 설정 변경 시그널

    def __init__(self, parent=None):
        """초기화

        Args:
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.setObjectName("widget-animation-settings")

        # 로깅 설정
        self.logger = create_component_logger("AnimationSettingsWidget")
        self.logger.info("🎭 애니메이션 설정 위젯 초기화 시작")

        # 내부 상태
        self._is_loading = False

        # UI 설정
        self._setup_ui()

        self.logger.info("✅ 애니메이션 설정 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 애니메이션 설정 그룹
        animation_group = QGroupBox("애니메이션 및 효과")
        animation_layout = QFormLayout(animation_group)

        # 애니메이션 활성화
        self.animation_enabled_checkbox = QCheckBox("UI 애니메이션 활성화")
        self.animation_enabled_checkbox.stateChanged.connect(self._on_setting_changed)
        animation_layout.addRow("", self.animation_enabled_checkbox)

        # 부드러운 스크롤링
        self.smooth_scrolling_checkbox = QCheckBox("부드러운 스크롤링")
        self.smooth_scrolling_checkbox.stateChanged.connect(self._on_setting_changed)
        animation_layout.addRow("", self.smooth_scrolling_checkbox)

        layout.addWidget(animation_group)

    def _on_setting_changed(self):
        """설정 변경 처리"""
        if not self._is_loading:
            self.logger.debug("🎭 애니메이션 설정 변경됨")
            self.settings_changed.emit()

    def get_animation_enabled(self) -> bool:
        """애니메이션 활성화 상태 반환"""
        return self.animation_enabled_checkbox.isChecked()

    def get_smooth_scrolling(self) -> bool:
        """부드러운 스크롤링 상태 반환"""
        return self.smooth_scrolling_checkbox.isChecked()

    def set_animation_enabled(self, enabled: bool):
        """애니메이션 활성화 설정

        Args:
            enabled: 활성화 여부
        """
        self._is_loading = True
        try:
            self.animation_enabled_checkbox.setChecked(enabled)
            self.logger.debug(f"🎭 애니메이션 활성화 설정됨: {enabled}")
        finally:
            self._is_loading = False

    def set_smooth_scrolling(self, enabled: bool):
        """부드러운 스크롤링 설정

        Args:
            enabled: 활성화 여부
        """
        self._is_loading = True
        try:
            self.smooth_scrolling_checkbox.setChecked(enabled)
            self.logger.debug(f"🎭 부드러운 스크롤링 설정됨: {enabled}")
        finally:
            self._is_loading = False

    def reset_to_default(self):
        """기본값으로 재설정"""
        self.set_animation_enabled(True)
        self.set_smooth_scrolling(True)
