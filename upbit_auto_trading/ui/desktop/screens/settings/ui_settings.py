"""
UI 설정 모듈 - Infrastructure Layer v4.0 통합

이 모듈은 UI 관련 설정 기능을 구현합니다.
- 테마 설정
- 창 크기/위치 설정
- 언어 설정
- 애니메이션 설정
- Infrastructure Layer v4.0 Enhanced Logging 연동
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QComboBox, QSpinBox, QFormLayout,
    QSlider, QGridLayout
)

# Infrastructure Layer Enhanced Logging v4.0
from upbit_auto_trading.infrastructure.logging import create_component_logger


class UISettings(QWidget):
    """UI 설정 위젯 클래스 (Infrastructure Layer v4.0 통합)"""

    # 설정 변경 시그널
    settings_changed = pyqtSignal()
    theme_changed = pyqtSignal(str)  # 테마 변경 시그널 (배치 저장 방식)

    def __init__(self, parent=None, settings_service=None):
        """초기화 - Infrastructure Layer v4.0 통합

        Args:
            parent: 부모 위젯
            settings_service: SettingsService 인스턴스
        """
        super().__init__(parent)
        self.setObjectName("widget-ui-settings")

        # Infrastructure Layer Enhanced Logging v4.0 초기화
        self.logger = create_component_logger("UISettings")
        self.logger.info("🎨 UI 설정 위젯 초기화 시작")

        # SettingsService 저장
        self.settings_service = settings_service

        # 배치 저장을 위한 내부 상태 관리
        self._pending_changes = {}
        self._has_unsaved_changes = False

        # SettingsService 의존성 확인
        if self.settings_service is None:
            self.logger.error("❌ SettingsService가 None으로 전달됨 - 의존성 주입 실패")
        else:
            self.logger.info(f"✅ SettingsService 의존성 주입 성공: {type(self.settings_service).__name__}")

        # Infrastructure Layer 연동 상태 확인
        self._check_infrastructure_integration()

        # UI 설정
        self._setup_ui()

        # 초기 설정 로드
        self._load_settings()

        self.logger.info("✅ UI 설정 위젯 초기화 완료")

    def _check_infrastructure_integration(self):
        """Infrastructure Layer v4.0 연동 상태 확인"""
        try:
            # SystemStatusTracker 상태 보고
            from upbit_auto_trading.infrastructure.logging.briefing.status_tracker import SystemStatusTracker
            tracker = SystemStatusTracker()
            tracker.update_component_status(
                "UISettings",
                "OK",
                "UI 설정 위젯 로드됨",
                widget_type="settings_tab",
                features_count=4
            )
            self.logger.info("📊 SystemStatusTracker에 UI 설정 상태 보고 완료")
        except Exception as e:
            self.logger.warning(f"⚠️ SystemStatusTracker 연동 실패: {e}")

    def _setup_ui(self):
        """UI 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 테마 설정 그룹 (배치 저장 방식)
        theme_group = QGroupBox("테마 설정")
        theme_layout = QFormLayout(theme_group)

        # 테마 선택
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("라이트 테마", "light")
        self.theme_combo.addItem("다크 테마", "dark")
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed_batch)
        theme_layout.addRow("테마:", self.theme_combo)

        main_layout.addWidget(theme_group)

        # 창 설정 그룹
        window_group = QGroupBox("창 설정 (미구현)")
        window_layout = QFormLayout(window_group)

        # 창 크기 설정
        window_size_layout = QHBoxLayout()

        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 3840)
        self.window_width_spin.setSuffix(" px")
        self.window_width_spin.valueChanged.connect(self._on_setting_changed_batch)

        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 2160)
        self.window_height_spin.setSuffix(" px")
        self.window_height_spin.valueChanged.connect(self._on_setting_changed_batch)

        window_size_layout.addWidget(QLabel("너비:"))
        window_size_layout.addWidget(self.window_width_spin)
        window_size_layout.addWidget(QLabel("높이:"))
        window_size_layout.addWidget(self.window_height_spin)
        window_size_layout.addStretch()

        window_layout.addRow("기본 창 크기:", window_size_layout)

        # 창 상태 저장 설정
        self.save_window_state_checkbox = QCheckBox("창 크기/위치 자동 저장")
        self.save_window_state_checkbox.stateChanged.connect(self._on_setting_changed_batch)
        window_layout.addRow("", self.save_window_state_checkbox)

        main_layout.addWidget(window_group)

        # 애니메이션 설정 그룹
        animation_group = QGroupBox("애니메이션 및 효과 (미구현)")
        animation_layout = QFormLayout(animation_group)

        # 애니메이션 활성화
        self.animation_enabled_checkbox = QCheckBox("UI 애니메이션 활성화")
        self.animation_enabled_checkbox.stateChanged.connect(self._on_setting_changed_batch)
        animation_layout.addRow("", self.animation_enabled_checkbox)

        # 부드러운 스크롤링
        self.smooth_scrolling_checkbox = QCheckBox("부드러운 스크롤링")
        self.smooth_scrolling_checkbox.stateChanged.connect(self._on_setting_changed_batch)
        animation_layout.addRow("", self.smooth_scrolling_checkbox)

        main_layout.addWidget(animation_group)

        # 차트 설정 그룹
        chart_group = QGroupBox("차트 설정 (미구현)")
        chart_layout = QFormLayout(chart_group)

        # 차트 스타일
        self.chart_style_combo = QComboBox()
        self.chart_style_combo.addItem("캔들스틱", "candlestick")
        self.chart_style_combo.addItem("라인", "line")
        self.chart_style_combo.addItem("바", "bar")
        self.chart_style_combo.currentTextChanged.connect(self._on_setting_changed_batch)
        chart_layout.addRow("차트 스타일:", self.chart_style_combo)

        # 차트 업데이트 간격
        self.chart_update_spin = QSpinBox()
        self.chart_update_spin.setRange(1, 60)
        self.chart_update_spin.setSuffix(" 초")
        self.chart_update_spin.valueChanged.connect(self._on_setting_changed_batch)
        chart_layout.addRow("업데이트 간격:", self.chart_update_spin)

        main_layout.addWidget(chart_group)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 기본값 복원 버튼
        self.reset_button = QPushButton("기본값으로 복원")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self.reset_button)

        # 설정 저장 버튼 (배치 저장 방식)
        self.apply_button = QPushButton("설정 저장")
        self.apply_button.clicked.connect(self._apply_all_settings_batch)
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

    def _on_theme_changed_batch(self):
        """테마 변경 처리 (배치 저장 방식)"""
        theme_value = self.theme_combo.currentData()
        if theme_value:
            self.logger.debug(f"🎨 테마 변경 대기 중: {theme_value}")
            self._pending_changes["theme"] = theme_value
            self._update_unsaved_changes_state()

    def _on_setting_changed_batch(self):
        """기타 설정 변경 처리 (배치 저장 방식)"""
        self.logger.debug("🔧 설정 변경 감지됨 - 배치 저장 대기")

        # 현재 설정값들을 pending_changes에 저장
        self._pending_changes.update({
            "window_width": self.window_width_spin.value(),
            "window_height": self.window_height_spin.value(),
            "save_window_state": self.save_window_state_checkbox.isChecked(),
            "animation_enabled": self.animation_enabled_checkbox.isChecked(),
            "smooth_scrolling": self.smooth_scrolling_checkbox.isChecked(),
            "chart_style": self.chart_style_combo.currentData(),
            "chart_update_interval_seconds": self.chart_update_spin.value()
        })

        self._update_unsaved_changes_state()

    def _update_unsaved_changes_state(self):
        """저장하지 않은 변경사항 상태 업데이트"""
        has_changes = bool(self._pending_changes)

        if has_changes != self._has_unsaved_changes:
            self._has_unsaved_changes = has_changes
            self.apply_button.setEnabled(has_changes)

            if has_changes:
                self.apply_button.setText("설정 저장")
                self.logger.debug("🔄 저장하지 않은 변경사항 발견 - 저장 버튼 활성화")
            else:
                self.apply_button.setText("설정 저장")
                self.logger.debug("✅ 모든 변경사항 저장됨 - 저장 버튼 비활성화")

    def _apply_all_settings_batch(self):
        """모든 설정 배치 저장"""
        if not self.settings_service:
            self.logger.warning("⚠️ SettingsService가 없어 설정 저장 불가")
            return

        if not self._pending_changes:
            self.logger.info("📝 저장할 변경사항이 없습니다")
            return

        try:
            self.logger.info("🔧 배치 설정 저장 시작")

            # 저장 버튼 상태 변경
            self.apply_button.setText("저장 중...")
            self.apply_button.setEnabled(False)

            # 모든 변경사항 적용
            for key, value in self._pending_changes.items():
                self.settings_service.update_ui_setting(key, value)
                self.logger.debug(f"💾 {key} = {value}")

            # 테마 변경이 있으면 시그널 발생
            if "theme" in self._pending_changes:
                theme_value = self._pending_changes["theme"]
                self.theme_changed.emit(theme_value)
                self.logger.info(f"🎨 테마 변경 시그널 발생: {theme_value}")

            # 변경사항 초기화
            self._pending_changes.clear()
            self._update_unsaved_changes_state()

            self.logger.info("✅ 배치 설정 저장 완료")
            self.settings_changed.emit()

        except Exception as e:
            self.logger.error(f"❌ 배치 설정 저장 실패: {e}")
        finally:
            # 저장 버튼 상태 복원
            self._update_unsaved_changes_state()

    def _apply_other_settings(self):
        """기타 설정 저장 (배치 방식으로 변경됨 - 호환성 유지용)"""
        # 새로운 배치 저장 방식으로 위임
        self._apply_all_settings_batch()

    def _load_settings(self):
        """설정 로드 (SettingsService 기반)"""
        if not self.settings_service:
            # SettingsService가 없으면 기본값 사용
            self._set_default_values()
            return

        try:
            # UI 설정 로드
            ui_config = self.settings_service.get_ui_config()

            # 시그널 연결 해제하여 로딩 중 불필요한 변경 감지 방지
            self._disconnect_change_signals()

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

            self.chart_update_spin.setValue(int(ui_config.chart_update_interval_seconds))

            # 시그널 연결 재설정
            self._connect_change_signals()

            # 변경사항 초기화 (로딩된 값들은 저장된 상태)
            self._pending_changes.clear()
            self._update_unsaved_changes_state()

        except Exception as e:
            self.logger.error(f"⚠️ UI 설정 로드 실패: {e}")
            self._set_default_values()

    def _disconnect_change_signals(self):
        """변경 감지 시그널 연결 해제"""
        try:
            self.theme_combo.currentIndexChanged.disconnect()
        except TypeError:
            pass  # 이미 연결이 해제된 경우

        try:
            self.window_width_spin.valueChanged.disconnect()
        except TypeError:
            pass

        try:
            self.window_height_spin.valueChanged.disconnect()
        except TypeError:
            pass

        try:
            self.save_window_state_checkbox.stateChanged.disconnect()
        except TypeError:
            pass

        try:
            self.animation_enabled_checkbox.stateChanged.disconnect()
        except TypeError:
            pass

        try:
            self.smooth_scrolling_checkbox.stateChanged.disconnect()
        except TypeError:
            pass

        try:
            self.chart_style_combo.currentTextChanged.disconnect()
        except TypeError:
            pass

        try:
            self.chart_update_spin.valueChanged.disconnect()
        except TypeError:
            pass

    def _connect_change_signals(self):
        """변경 감지 시그널 연결"""
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed_batch)
        self.window_width_spin.valueChanged.connect(self._on_setting_changed_batch)
        self.window_height_spin.valueChanged.connect(self._on_setting_changed_batch)
        self.save_window_state_checkbox.stateChanged.connect(self._on_setting_changed_batch)
        self.animation_enabled_checkbox.stateChanged.connect(self._on_setting_changed_batch)
        self.smooth_scrolling_checkbox.stateChanged.connect(self._on_setting_changed_batch)
        self.chart_style_combo.currentTextChanged.connect(self._on_setting_changed_batch)
        self.chart_update_spin.valueChanged.connect(self._on_setting_changed_batch)

    def _set_default_values(self):
        """기본값 설정"""
        # 시그널 연결 해제하여 기본값 설정 중 변경 감지 방지
        self._disconnect_change_signals()

        self.theme_combo.setCurrentIndex(0)  # light
        self.window_width_spin.setValue(1600)
        self.window_height_spin.setValue(1000)
        self.save_window_state_checkbox.setChecked(True)
        self.animation_enabled_checkbox.setChecked(True)
        self.smooth_scrolling_checkbox.setChecked(True)
        self.chart_style_combo.setCurrentIndex(0)  # candlestick
        self.chart_update_spin.setValue(1)

        # 시그널 연결 재설정
        self._connect_change_signals()

        # 변경사항 초기화
        self._pending_changes.clear()
        self._update_unsaved_changes_state()

    def _apply_all_settings(self):
        """모든 설정 적용 (기존 호환성 유지용)"""
        # 새로운 배치 저장 방식으로 위임
        self._apply_all_settings_batch()

    def _apply_settings(self):
        """설정 적용 (기존 호환성 유지)"""
        # 새로운 배치 저장 방식으로 위임
        self._apply_all_settings_batch()

    def _reset_to_defaults(self):
        """기본값으로 복원 - UI 표시만 변경 (저장하지 않음)"""
        try:
            self.logger.info("🔄 기본값으로 복원 시작 (UI 표시만)")

            # 1. 시그널을 유지한 상태에서 UI 값만 변경
            # PyQt6는 프로그래밍적 변경도 자동으로 시그널 발생시킴
            self.theme_combo.setCurrentIndex(0)  # light
            self.window_width_spin.setValue(1600)
            self.window_height_spin.setValue(1000)
            self.save_window_state_checkbox.setChecked(True)
            self.animation_enabled_checkbox.setChecked(True)
            self.smooth_scrolling_checkbox.setChecked(True)
            self.chart_style_combo.setCurrentIndex(0)  # candlestick
            self.chart_update_spin.setValue(1)

            # 2. 위의 UI 변경으로 인해 시그널이 자동 발생하여
            #    _on_theme_changed_batch()와 _on_setting_changed_batch()가 호출됨
            #    따라서 '설정 저장' 버튼이 자동으로 활성화됨

            self.logger.info("✅ 기본값으로 UI 복원 완료 (저장은 사용자가 결정)")

        except Exception as e:
            self.logger.error(f"❌ 기본값 복원 실패: {e}")

        self.settings_changed.emit()

    def save_settings(self):
        """설정 저장 (외부 호출용 - 배치 저장 방식)"""
        self._apply_all_settings_batch()

    def save_all_settings(self):
        """모든 설정 저장 (전체 저장용)"""
        self._apply_all_settings_batch()

    def load_settings(self):
        """설정 로드 (외부 호출용)"""
        self._load_settings()

    # 호환성 유지를 위한 기존 메서드들
    def _on_theme_changed(self):
        """테마 변경 처리 (기존 호환성 유지)"""
        # 새로운 배치 방식으로 위임
        self._on_theme_changed_batch()

    def _on_settings_changed(self):
        """설정 변경 처리 (기존 호환성 유지)"""
        # 새로운 배치 방식으로 위임
        self._on_setting_changed_batch()
