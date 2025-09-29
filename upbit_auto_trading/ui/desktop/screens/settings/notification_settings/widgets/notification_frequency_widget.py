"""
알림 빈도 설정 위젯

이 모듈은 알림 빈도 설정을 담당하는 위젯입니다.
- 즉시 알림
- 시간별 요약
- 일별 요약
"""

from typing import Dict, Any
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QGroupBox, QFormLayout

# Infrastructure Layer Enhanced Logging v4.0
# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)

class NotificationFrequencyWidget(QWidget):
    """알림 빈도 설정 위젯"""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None, logging_service=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("widget-notification-frequency")

        if logging_service:
            self.logger = logging_service.get_component_logger("NotificationFrequencyWidget")
        else:
            raise ValueError("NotificationFrequencyWidget에 logging_service가 주입되지 않았습니다")
        self.logger.debug("⏰ NotificationFrequencyWidget 초기화")

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 알림 빈도 그룹
        group = QGroupBox("알림 빈도")
        group.setObjectName("group-notification-frequency")
        group_layout = QFormLayout(group)

        # 알림 빈도 콤보박스
        self.frequency_combo = QComboBox()
        self.frequency_combo.setObjectName("combo-frequency")
        self.frequency_combo.addItem("즉시 알림", "immediate")
        self.frequency_combo.addItem("시간별 요약", "hourly")
        self.frequency_combo.addItem("일별 요약", "daily")

        group_layout.addRow("알림 빈도:", self.frequency_combo)

        layout.addWidget(group)

    def _connect_signals(self):
        """시그널 연결"""
        self.frequency_combo.currentIndexChanged.connect(self._on_setting_changed)

    def _on_setting_changed(self):
        """설정 변경 시 호출"""
        settings = self._collect_settings()
        self.logger.debug(f"🔧 알림 빈도 설정 변경: {settings}")
        self.settings_changed.emit(settings)

    def _collect_settings(self) -> Dict[str, Any]:
        """현재 위젯 설정 수집"""
        return {
            'notification_frequency': self.frequency_combo.currentData()
        }

    def update_from_settings(self, settings: Dict[str, Any]):
        """설정에서 UI 업데이트"""
        # 시그널 일시 차단
        self.frequency_combo.blockSignals(True)

        # 값 설정
        frequency = settings.get('notification_frequency', 'immediate')
        index = self.frequency_combo.findData(frequency)
        if index >= 0:
            self.frequency_combo.setCurrentIndex(index)

        # 시그널 차단 해제
        self.frequency_combo.blockSignals(False)

        self.logger.debug("📥 알림 빈도 설정 UI 업데이트 완료")
