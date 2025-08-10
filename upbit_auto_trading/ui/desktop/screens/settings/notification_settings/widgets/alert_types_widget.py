"""
알림 유형 설정 위젯

이 모듈은 알림 유형 활성화/비활성화 설정을 담당하는 위젯입니다.
- 가격 알림
- 거래 알림
- 시스템 알림
"""

from typing import Dict, Any
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QGroupBox, QLabel

# Infrastructure Layer Enhanced Logging v4.0
from upbit_auto_trading.infrastructure.logging import create_component_logger


class AlertTypesWidget(QWidget):
    """알림 유형 설정 위젯"""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("widget-alert-types")

        self.logger = create_component_logger("AlertTypesWidget")
        self.logger.debug("🚨 AlertTypesWidget 초기화")

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 알림 활성화 그룹
        group = QGroupBox("알림 유형")
        group.setObjectName("group-alert-types")
        group_layout = QVBoxLayout(group)

        # 가격 알림 체크박스
        self.enable_price_alerts_checkbox = QCheckBox("가격 알림")
        self.enable_price_alerts_checkbox.setObjectName("checkbox-enable-price-alerts")
        group_layout.addWidget(self.enable_price_alerts_checkbox)

        # 거래 알림 체크박스
        self.enable_trade_alerts_checkbox = QCheckBox("거래 알림")
        self.enable_trade_alerts_checkbox.setObjectName("checkbox-enable-trade-alerts")
        group_layout.addWidget(self.enable_trade_alerts_checkbox)

        # 시스템 알림 체크박스
        self.enable_system_alerts_checkbox = QCheckBox("시스템 알림")
        self.enable_system_alerts_checkbox.setObjectName("checkbox-enable-system-alerts")
        group_layout.addWidget(self.enable_system_alerts_checkbox)

        # 설명 라벨
        info_label = QLabel("* 각 알림 유형을 개별적으로 활성화/비활성화할 수 있습니다.")
        info_label.setObjectName("label-alert-types-info")
        group_layout.addWidget(info_label)

        layout.addWidget(group)

    def _connect_signals(self):
        """시그널 연결"""
        self.enable_price_alerts_checkbox.stateChanged.connect(self._on_setting_changed)
        self.enable_trade_alerts_checkbox.stateChanged.connect(self._on_setting_changed)
        self.enable_system_alerts_checkbox.stateChanged.connect(self._on_setting_changed)

    def _on_setting_changed(self):
        """설정 변경 시 호출"""
        settings = self._collect_settings()
        self.logger.debug(f"🔧 알림 유형 설정 변경: {settings}")
        self.settings_changed.emit(settings)

    def _collect_settings(self) -> Dict[str, Any]:
        """현재 위젯 설정 수집"""
        return {
            'enable_price_alerts': self.enable_price_alerts_checkbox.isChecked(),
            'enable_trade_alerts': self.enable_trade_alerts_checkbox.isChecked(),
            'enable_system_alerts': self.enable_system_alerts_checkbox.isChecked()
        }

    def update_from_settings(self, settings: Dict[str, Any]):
        """설정에서 UI 업데이트"""
        # 시그널 일시 차단
        self.enable_price_alerts_checkbox.blockSignals(True)
        self.enable_trade_alerts_checkbox.blockSignals(True)
        self.enable_system_alerts_checkbox.blockSignals(True)

        # 값 설정
        self.enable_price_alerts_checkbox.setChecked(settings.get('enable_price_alerts', True))
        self.enable_trade_alerts_checkbox.setChecked(settings.get('enable_trade_alerts', True))
        self.enable_system_alerts_checkbox.setChecked(settings.get('enable_system_alerts', True))

        # 시그널 차단 해제
        self.enable_price_alerts_checkbox.blockSignals(False)
        self.enable_trade_alerts_checkbox.blockSignals(False)
        self.enable_system_alerts_checkbox.blockSignals(False)

        self.logger.debug("📥 알림 유형 설정 UI 업데이트 완료")
