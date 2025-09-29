"""
창 설정 위젯

이 모듈은 창 관련 설정 UI 컴포넌트를 구현합니다.
- 창 크기 설정
- 창 위치 저장 설정
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QCheckBox, QGroupBox, QFormLayout
)

# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)

class WindowSettingsWidget(QWidget):
    """창 설정 위젯"""

    # 시그널
    settings_changed = pyqtSignal()  # 설정 변경 시그널

    def __init__(self, parent=None):
        """초기화

        Args:
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.setObjectName("widget-window-settings")

        # 로깅 설정
        self.logger = create_component_logger("WindowSettingsWidget")
        self.logger.info("🪟 창 설정 위젯 초기화 시작")

        # 내부 상태
        self._is_loading = False

        # UI 설정
        self._setup_ui()

        self.logger.info("✅ 창 설정 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 창 설정 그룹
        window_group = QGroupBox("창 설정")
        window_layout = QFormLayout(window_group)

        # 창 크기 설정
        window_size_layout = QHBoxLayout()

        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 3840)
        self.window_width_spin.setSuffix(" px")
        self.window_width_spin.valueChanged.connect(self._on_setting_changed)

        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 2160)
        self.window_height_spin.setSuffix(" px")
        self.window_height_spin.valueChanged.connect(self._on_setting_changed)

        window_size_layout.addWidget(QLabel("너비:"))
        window_size_layout.addWidget(self.window_width_spin)
        window_size_layout.addWidget(QLabel("높이:"))
        window_size_layout.addWidget(self.window_height_spin)
        window_size_layout.addStretch()

        window_layout.addRow("기본 창 크기:", window_size_layout)

        # 창 상태 저장 설정
        self.save_window_state_checkbox = QCheckBox("창 크기/위치 자동 저장")
        self.save_window_state_checkbox.stateChanged.connect(self._on_setting_changed)
        window_layout.addRow("", self.save_window_state_checkbox)

        layout.addWidget(window_group)

    def _on_setting_changed(self):
        """설정 변경 처리"""
        if not self._is_loading:
            self.logger.debug("🪟 창 설정 변경됨")
            self.settings_changed.emit()

    def get_window_width(self) -> int:
        """창 너비 반환"""
        return self.window_width_spin.value()

    def get_window_height(self) -> int:
        """창 높이 반환"""
        return self.window_height_spin.value()

    def get_save_window_state(self) -> bool:
        """창 상태 저장 설정 반환"""
        return self.save_window_state_checkbox.isChecked()

    def set_window_size(self, width: int, height: int):
        """창 크기 설정

        Args:
            width: 창 너비
            height: 창 높이
        """
        self._is_loading = True
        try:
            self.window_width_spin.setValue(width)
            self.window_height_spin.setValue(height)
            self.logger.debug(f"🪟 창 크기 설정됨: {width}x{height}")
        finally:
            self._is_loading = False

    def set_save_window_state(self, save: bool):
        """창 상태 저장 설정

        Args:
            save: 저장 여부
        """
        self._is_loading = True
        try:
            self.save_window_state_checkbox.setChecked(save)
            self.logger.debug(f"🪟 창 상태 저장 설정됨: {save}")
        finally:
            self._is_loading = False

    def reset_to_default(self):
        """기본값으로 재설정"""
        self.set_window_size(1600, 1000)
        self.set_save_window_state(True)
