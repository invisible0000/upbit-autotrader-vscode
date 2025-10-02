"""
방해 금지 시간 설정 위젯

이 모듈은 방해 금지 시간 설정을 담당하는 위젯입니다.
- 방해 금지 시간 활성화/비활성화
- 시작 시간 설정
- 종료 시간 설정
"""

from typing import Dict, Any
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QGroupBox,
    QLabel, QSpinBox
)

# Infrastructure Layer Enhanced Logging v4.0
# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)

class QuietHoursWidget(QWidget):
    """방해 금지 시간 설정 위젯"""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None, logging_service=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("widget-quiet-hours")

        if logging_service:
            self.logger = logging_service.get_component_logger("QuietHoursWidget")
        else:
            raise ValueError("QuietHoursWidget에 logging_service가 주입되지 않았습니다")
        self.logger.debug("🔇 QuietHoursWidget 초기화")

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 방해 금지 시간 그룹
        group = QGroupBox("방해 금지 시간")
        group.setObjectName("group-quiet-hours")
        group_layout = QVBoxLayout(group)

        # 방해 금지 시간 활성화 체크박스
        self.quiet_hours_checkbox = QCheckBox("방해 금지 시간 활성화")
        self.quiet_hours_checkbox.setObjectName("checkbox-quiet-hours")
        group_layout.addWidget(self.quiet_hours_checkbox)

        # 시작 및 종료 시간 설정
        time_layout = QHBoxLayout()

        # 시작 시간
        start_layout = QHBoxLayout()
        start_label = QLabel("시작 시간:")
        start_label.setObjectName("label-start-time")
        self.start_hour_spin = QSpinBox()
        self.start_hour_spin.setObjectName("spin-start-hour")
        self.start_hour_spin.setRange(0, 23)
        self.start_hour_spin.setSuffix("시")
        self.start_hour_spin.setValue(22)  # 기본값: 22시
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_hour_spin)
        time_layout.addLayout(start_layout)

        # 종료 시간
        end_layout = QHBoxLayout()
        end_label = QLabel("종료 시간:")
        end_label.setObjectName("label-end-time")
        self.end_hour_spin = QSpinBox()
        self.end_hour_spin.setObjectName("spin-end-hour")
        self.end_hour_spin.setRange(0, 23)
        self.end_hour_spin.setSuffix("시")
        self.end_hour_spin.setValue(8)  # 기본값: 8시
        end_layout.addWidget(end_label)
        end_layout.addWidget(self.end_hour_spin)
        time_layout.addLayout(end_layout)

        group_layout.addLayout(time_layout)

        # 방해 금지 시간 설명
        info_label = QLabel("* 방해 금지 시간 동안에는 알림이 표시되지 않습니다.")
        info_label.setObjectName("label-quiet-hours-info")
        group_layout.addWidget(info_label)

        layout.addWidget(group)

        # 초기 상태 설정
        self._update_time_controls_state()

    def _connect_signals(self):
        """시그널 연결"""
        self.quiet_hours_checkbox.stateChanged.connect(self._on_setting_changed)
        self.start_hour_spin.valueChanged.connect(self._on_setting_changed)
        self.end_hour_spin.valueChanged.connect(self._on_setting_changed)

        # 체크박스 상태에 따른 시간 컨트롤 활성화/비활성화
        self.quiet_hours_checkbox.stateChanged.connect(self._update_time_controls_state)

    def _on_setting_changed(self):
        """설정 변경 시 호출"""
        settings = self._collect_settings()
        self.logger.debug(f"🔧 방해 금지 시간 설정 변경: {settings}")
        self.settings_changed.emit(settings)

    def _collect_settings(self) -> Dict[str, Any]:
        """현재 위젯 설정 수집"""
        return {
            'quiet_hours_enabled': self.quiet_hours_checkbox.isChecked(),
            'quiet_hours_start': self.start_hour_spin.value(),
            'quiet_hours_end': self.end_hour_spin.value()
        }

    def _update_time_controls_state(self):
        """방해 금지 시간 활성화 상태에 따라 시간 컨트롤 상태 업데이트"""
        enabled = self.quiet_hours_checkbox.isChecked()
        self.start_hour_spin.setEnabled(enabled)
        self.end_hour_spin.setEnabled(enabled)

    def update_from_settings(self, settings: Dict[str, Any]):
        """설정에서 UI 업데이트"""
        # 시그널 일시 차단
        self.quiet_hours_checkbox.blockSignals(True)
        self.start_hour_spin.blockSignals(True)
        self.end_hour_spin.blockSignals(True)

        # 값 설정
        self.quiet_hours_checkbox.setChecked(settings.get('quiet_hours_enabled', False))
        self.start_hour_spin.setValue(settings.get('quiet_hours_start', 22))
        self.end_hour_spin.setValue(settings.get('quiet_hours_end', 8))

        # 시그널 차단 해제
        self.quiet_hours_checkbox.blockSignals(False)
        self.start_hour_spin.blockSignals(False)
        self.end_hour_spin.blockSignals(False)

        # 시간 컨트롤 상태 업데이트
        self._update_time_controls_state()

        self.logger.debug("📥 방해 금지 시간 설정 UI 업데이트 완료")
