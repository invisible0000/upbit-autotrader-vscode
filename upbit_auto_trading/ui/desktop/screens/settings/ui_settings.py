"""
UI 설정 모듈

이 모듈은 UI 관련 설정 기능을 구현합니다.
- 테마 설정
- 창 크기/위치 설정
- 언어 설정
- 애니메이션 설정
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QComboBox, QSpinBox, QFormLayout,
    QSlider, QGridLayout
)


class UISettings(QWidget):
    """UI 설정 위젯 클래스 (Infrastructure Layer 기반)"""

    # 설정 변경 시그널
    settings_changed = pyqtSignal()
    theme_changed = pyqtSignal(str)  # 테마 변경 즉시 반영용

    def __init__(self, parent=None, settings_service=None):
        """초기화

        Args:
            parent: 부모 위젯
            settings_service: SettingsService 인스턴스
        """
        super().__init__(parent)
        self.setObjectName("widget-ui-settings")

        # SettingsService 저장
        self.settings_service = settings_service

        # UI 설정
        self._setup_ui()

        # 초기 설정 로드
        self._load_settings()

    def _setup_ui(self):
        """UI 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 테마 설정 그룹
        theme_group = QGroupBox("테마 설정")
        theme_layout = QFormLayout(theme_group)

        # 테마 선택
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("라이트 테마", "light")
        self.theme_combo.addItem("다크 테마", "dark")
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_layout.addRow("테마:", self.theme_combo)

        main_layout.addWidget(theme_group)

        # 창 설정 그룹
        window_group = QGroupBox("창 설정")
        window_layout = QFormLayout(window_group)

        # 창 크기 설정
        window_size_layout = QHBoxLayout()

        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 3840)
        self.window_width_spin.setSuffix(" px")
        self.window_width_spin.valueChanged.connect(self._on_settings_changed)

        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 2160)
        self.window_height_spin.setSuffix(" px")
        self.window_height_spin.valueChanged.connect(self._on_settings_changed)

        window_size_layout.addWidget(QLabel("너비:"))
        window_size_layout.addWidget(self.window_width_spin)
        window_size_layout.addWidget(QLabel("높이:"))
        window_size_layout.addWidget(self.window_height_spin)
        window_size_layout.addStretch()

        window_layout.addRow("기본 창 크기:", window_size_layout)

        # 창 상태 저장 설정
        self.save_window_state_checkbox = QCheckBox("창 크기/위치 자동 저장")
        self.save_window_state_checkbox.stateChanged.connect(self._on_settings_changed)
        window_layout.addRow("", self.save_window_state_checkbox)

        main_layout.addWidget(window_group)

        # 애니메이션 설정 그룹
        animation_group = QGroupBox("애니메이션 및 효과")
        animation_layout = QFormLayout(animation_group)

        # 애니메이션 활성화
        self.animation_enabled_checkbox = QCheckBox("UI 애니메이션 활성화")
        self.animation_enabled_checkbox.stateChanged.connect(self._on_settings_changed)
        animation_layout.addRow("", self.animation_enabled_checkbox)

        # 부드러운 스크롤링
        self.smooth_scrolling_checkbox = QCheckBox("부드러운 스크롤링")
        self.smooth_scrolling_checkbox.stateChanged.connect(self._on_settings_changed)
        animation_layout.addRow("", self.smooth_scrolling_checkbox)

        main_layout.addWidget(animation_group)

        # 차트 설정 그룹
        chart_group = QGroupBox("차트 설정")
        chart_layout = QFormLayout(chart_group)

        # 차트 스타일
        self.chart_style_combo = QComboBox()
        self.chart_style_combo.addItem("캔들스틱", "candlestick")
        self.chart_style_combo.addItem("라인", "line")
        self.chart_style_combo.addItem("바", "bar")
        self.chart_style_combo.currentTextChanged.connect(self._on_settings_changed)
        chart_layout.addRow("차트 스타일:", self.chart_style_combo)

        # 차트 업데이트 간격
        self.chart_update_spin = QSpinBox()
        self.chart_update_spin.setRange(1, 60)
        self.chart_update_spin.setSuffix(" 초")
        self.chart_update_spin.valueChanged.connect(self._on_settings_changed)
        chart_layout.addRow("업데이트 간격:", self.chart_update_spin)

        main_layout.addWidget(chart_group)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 기본값 복원 버튼
        self.reset_button = QPushButton("기본값으로 복원")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self.reset_button)

        # 즉시 적용 버튼
        self.apply_button = QPushButton("즉시 적용")
        self.apply_button.clicked.connect(self._apply_settings)
        button_layout.addWidget(self.apply_button)

        main_layout.addLayout(button_layout)
        main_layout.addStretch()

    def _on_theme_changed(self):
        """테마 변경 처리"""
        theme_value = self.theme_combo.currentData()
        if theme_value:
            # 즉시 테마 변경 시그널 발생
            self.theme_changed.emit(theme_value)
            self._on_settings_changed()

    def _on_settings_changed(self):
        """설정 변경 처리"""
        self.settings_changed.emit()

    def _load_settings(self):
        """설정 로드 (SettingsService 기반)"""
        if not self.settings_service:
            # SettingsService가 없으면 기본값 사용
            self._set_default_values()
            return

        try:
            # UI 설정 로드
            ui_config = self.settings_service.get_ui_config()

            # 테마 설정
            theme_index = self.theme_combo.findData(ui_config.theme)
            if theme_index >= 0:
                self.theme_combo.setCurrentIndex(theme_index)

            # 창 크기 설정
            self.window_width_spin.setValue(ui_config.window_width)
            self.window_height_spin.setValue(ui_config.window_height)

            # 창 상태 저장 설정
            self.save_window_state_checkbox.setChecked(ui_config.save_window_state)

            # 애니메이션 설정
            self.animation_enabled_checkbox.setChecked(ui_config.animation_enabled)
            self.smooth_scrolling_checkbox.setChecked(ui_config.smooth_scrolling)

            # 차트 설정
            chart_style_index = self.chart_style_combo.findData(ui_config.chart_style)
            if chart_style_index >= 0:
                self.chart_style_combo.setCurrentIndex(chart_style_index)

            self.chart_update_spin.setValue(ui_config.chart_update_interval_seconds)

        except Exception as e:
            print(f"⚠️ UI 설정 로드 실패: {e}")
            self._set_default_values()

    def _set_default_values(self):
        """기본값 설정"""
        self.theme_combo.setCurrentIndex(0)  # light
        self.window_width_spin.setValue(1600)
        self.window_height_spin.setValue(1000)
        self.save_window_state_checkbox.setChecked(True)
        self.animation_enabled_checkbox.setChecked(True)
        self.smooth_scrolling_checkbox.setChecked(True)
        self.chart_style_combo.setCurrentIndex(0)  # candlestick
        self.chart_update_spin.setValue(1)

    def _apply_settings(self):
        """설정 즉시 적용"""
        if not self.settings_service:
            return

        try:
            # UI 설정 업데이트
            self.settings_service.update_ui_setting("theme", self.theme_combo.currentData())
            self.settings_service.update_ui_setting("window_width", self.window_width_spin.value())
            self.settings_service.update_ui_setting("window_height", self.window_height_spin.value())
            self.settings_service.update_ui_setting("save_window_state", self.save_window_state_checkbox.isChecked())
            self.settings_service.update_ui_setting("animation_enabled", self.animation_enabled_checkbox.isChecked())
            self.settings_service.update_ui_setting("smooth_scrolling", self.smooth_scrolling_checkbox.isChecked())
            self.settings_service.update_ui_setting("chart_style", self.chart_style_combo.currentData())
            self.settings_service.update_ui_setting("chart_update_interval_seconds", self.chart_update_spin.value())

            print("✅ UI 설정 적용 완료")
            self.settings_changed.emit()

        except Exception as e:
            print(f"❌ UI 설정 적용 실패: {e}")

    def _reset_to_defaults(self):
        """기본값으로 복원"""
        if self.settings_service:
            try:
                self.settings_service.reset_to_defaults("ui")
                print("✅ UI 설정 기본값 복원 완료")
            except Exception as e:
                print(f"❌ UI 설정 기본값 복원 실패: {e}")

        # UI 업데이트
        self._load_settings()
        self.settings_changed.emit()

    def save_settings(self):
        """설정 저장 (외부 호출용)"""
        self._apply_settings()

    def load_settings(self):
        """설정 로드 (외부 호출용)"""
        self._load_settings()
