"""
알림 설정 모듈

이 모듈은 알림 설정 기능을 구현합니다.
- 가격 알림 설정
- 거래 알림 설정
- 시스템 알림 설정
"""

import os
import json
from typing import Dict, Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QGroupBox, QComboBox, QSpinBox, QFormLayout
)


class NotificationSettings(QWidget):
    """알림 설정 위젯 클래스"""
    
    # 설정 변경 시그널
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("widget-notification-settings")
        
        # 설정 값
        self.settings = {
            'enable_price_alerts': True,
            'enable_trade_alerts': True,
            'enable_system_alerts': True,
            'notification_sound': True,
            'desktop_notifications': True,
            'email_notifications': False,
            'email_address': '',
            'notification_frequency': 'immediate',  # immediate, hourly, daily
            'quiet_hours_enabled': False,
            'quiet_hours_start': 22,  # 22:00
            'quiet_hours_end': 8,  # 08:00
        }
        
        # UI 설정
        self._setup_ui()
    
    def _setup_ui(self):
        """UI 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # 알림 활성화 그룹
        enable_group = QGroupBox("알림 활성화")
        enable_layout = QVBoxLayout(enable_group)
        
        # 가격 알림 체크박스
        self.enable_price_alerts_checkbox = QCheckBox("가격 알림")
        self.enable_price_alerts_checkbox.setObjectName("checkbox-enable-price-alerts")
        enable_layout.addWidget(self.enable_price_alerts_checkbox)
        
        # 거래 알림 체크박스
        self.enable_trade_alerts_checkbox = QCheckBox("거래 알림")
        self.enable_trade_alerts_checkbox.setObjectName("checkbox-enable-trade-alerts")
        enable_layout.addWidget(self.enable_trade_alerts_checkbox)
        
        # 시스템 알림 체크박스
        self.enable_system_alerts_checkbox = QCheckBox("시스템 알림")
        self.enable_system_alerts_checkbox.setObjectName("checkbox-enable-system-alerts")
        enable_layout.addWidget(self.enable_system_alerts_checkbox)
        
        # 알림 활성화 설명
        enable_info = QLabel("* 각 알림 유형을 개별적으로 활성화/비활성화할 수 있습니다.")
        enable_info.setObjectName("label-enable-info")
        enable_layout.addWidget(enable_info)
        
        main_layout.addWidget(enable_group)
        
        # 알림 방법 그룹
        method_group = QGroupBox("알림 방법")
        method_layout = QVBoxLayout(method_group)
        
        # 소리 알림 체크박스
        self.notification_sound_checkbox = QCheckBox("소리 알림")
        self.notification_sound_checkbox.setObjectName("checkbox-notification-sound")
        method_layout.addWidget(self.notification_sound_checkbox)
        
        # 데스크톱 알림 체크박스
        self.desktop_notifications_checkbox = QCheckBox("데스크톱 알림")
        self.desktop_notifications_checkbox.setObjectName("checkbox-desktop-notifications")
        method_layout.addWidget(self.desktop_notifications_checkbox)
        
        # 이메일 알림 체크박스
        self.email_notifications_checkbox = QCheckBox("이메일 알림")
        self.email_notifications_checkbox.setObjectName("checkbox-email-notifications")
        method_layout.addWidget(self.email_notifications_checkbox)
        
        # 이메일 주소 입력 폼
        email_layout = QHBoxLayout()
        email_label = QLabel("이메일 주소:")
        email_label.setObjectName("label-email")
        self.email_input = QLabel("이메일 설정은 향후 업데이트에서 지원될 예정입니다.")
        self.email_input.setObjectName("label-email-input")
        self.email_input.setEnabled(False)
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input, 1)
        method_layout.addLayout(email_layout)
        
        main_layout.addWidget(method_group)
        
        # 알림 빈도 그룹
        frequency_group = QGroupBox("알림 빈도")
        frequency_layout = QFormLayout(frequency_group)
        
        # 알림 빈도 콤보박스
        self.frequency_combo = QComboBox()
        self.frequency_combo.setObjectName("combo-frequency")
        self.frequency_combo.addItem("즉시 알림", "immediate")
        self.frequency_combo.addItem("시간별 요약", "hourly")
        self.frequency_combo.addItem("일별 요약", "daily")
        frequency_layout.addRow("알림 빈도:", self.frequency_combo)
        
        main_layout.addWidget(frequency_group)
        
        # 방해 금지 시간 그룹
        quiet_hours_group = QGroupBox("방해 금지 시간")
        quiet_hours_layout = QVBoxLayout(quiet_hours_group)
        
        # 방해 금지 시간 활성화 체크박스
        self.quiet_hours_checkbox = QCheckBox("방해 금지 시간 활성화")
        self.quiet_hours_checkbox.setObjectName("checkbox-quiet-hours")
        quiet_hours_layout.addWidget(self.quiet_hours_checkbox)
        
        # 시작 및 종료 시간 설정
        time_layout = QHBoxLayout()
        
        # 시작 시간
        start_layout = QHBoxLayout()
        start_label = QLabel("시작 시간:")
        self.start_hour_spin = QSpinBox()
        self.start_hour_spin.setObjectName("spin-start-hour")
        self.start_hour_spin.setRange(0, 23)
        self.start_hour_spin.setSuffix("시")
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_hour_spin)
        time_layout.addLayout(start_layout)
        
        # 종료 시간
        end_layout = QHBoxLayout()
        end_label = QLabel("종료 시간:")
        self.end_hour_spin = QSpinBox()
        self.end_hour_spin.setObjectName("spin-end-hour")
        self.end_hour_spin.setRange(0, 23)
        self.end_hour_spin.setSuffix("시")
        end_layout.addWidget(end_label)
        end_layout.addWidget(self.end_hour_spin)
        time_layout.addLayout(end_layout)
        
        quiet_hours_layout.addLayout(time_layout)
        
        # 방해 금지 시간 설명
        quiet_hours_info = QLabel("* 방해 금지 시간 동안에는 알림이 표시되지 않습니다.")
        quiet_hours_info.setObjectName("label-quiet-hours-info")
        quiet_hours_layout.addWidget(quiet_hours_info)
        
        main_layout.addWidget(quiet_hours_group)
        
        # 빈 공간 추가
        main_layout.addStretch(1)
        
        # 시그널 연결
        self._connect_signals()
        
        # 초기 값 설정
        self._update_ui_from_settings()
    
    def _connect_signals(self):
        """시그널 연결"""
        # 알림 활성화 체크박스
        self.enable_price_alerts_checkbox.stateChanged.connect(self._on_settings_changed)
        self.enable_trade_alerts_checkbox.stateChanged.connect(self._on_settings_changed)
        self.enable_system_alerts_checkbox.stateChanged.connect(self._on_settings_changed)
        
        # 알림 방법 체크박스
        self.notification_sound_checkbox.stateChanged.connect(self._on_settings_changed)
        self.desktop_notifications_checkbox.stateChanged.connect(self._on_settings_changed)
        self.email_notifications_checkbox.stateChanged.connect(self._on_settings_changed)
        
        # 알림 빈도 콤보박스
        self.frequency_combo.currentIndexChanged.connect(self._on_settings_changed)
        
        # 방해 금지 시간 설정
        self.quiet_hours_checkbox.stateChanged.connect(self._on_settings_changed)
        self.start_hour_spin.valueChanged.connect(self._on_settings_changed)
        self.end_hour_spin.valueChanged.connect(self._on_settings_changed)
    
    def _update_ui_from_settings(self):
        """설정 값으로 UI 업데이트"""
        # 알림 활성화 체크박스
        self.enable_price_alerts_checkbox.setChecked(self.settings['enable_price_alerts'])
        self.enable_trade_alerts_checkbox.setChecked(self.settings['enable_trade_alerts'])
        self.enable_system_alerts_checkbox.setChecked(self.settings['enable_system_alerts'])
        
        # 알림 방법 체크박스
        self.notification_sound_checkbox.setChecked(self.settings['notification_sound'])
        self.desktop_notifications_checkbox.setChecked(self.settings['desktop_notifications'])
        self.email_notifications_checkbox.setChecked(self.settings['email_notifications'])
        
        # 알림 빈도 콤보박스
        index = self.frequency_combo.findData(self.settings['notification_frequency'])
        if index >= 0:
            self.frequency_combo.setCurrentIndex(index)
        
        # 방해 금지 시간 설정
        self.quiet_hours_checkbox.setChecked(self.settings['quiet_hours_enabled'])
        self.start_hour_spin.setValue(self.settings['quiet_hours_start'])
        self.end_hour_spin.setValue(self.settings['quiet_hours_end'])
    
    def _update_settings_from_ui(self):
        """UI 값으로 설정 업데이트"""
        # 알림 활성화 체크박스
        self.settings['enable_price_alerts'] = self.enable_price_alerts_checkbox.isChecked()
        self.settings['enable_trade_alerts'] = self.enable_trade_alerts_checkbox.isChecked()
        self.settings['enable_system_alerts'] = self.enable_system_alerts_checkbox.isChecked()
        
        # 알림 방법 체크박스
        self.settings['notification_sound'] = self.notification_sound_checkbox.isChecked()
        self.settings['desktop_notifications'] = self.desktop_notifications_checkbox.isChecked()
        self.settings['email_notifications'] = self.email_notifications_checkbox.isChecked()
        
        # 알림 빈도 콤보박스
        self.settings['notification_frequency'] = self.frequency_combo.currentData()
        
        # 방해 금지 시간 설정
        self.settings['quiet_hours_enabled'] = self.quiet_hours_checkbox.isChecked()
        self.settings['quiet_hours_start'] = self.start_hour_spin.value()
        self.settings['quiet_hours_end'] = self.end_hour_spin.value()
    
    def _on_settings_changed(self):
        """설정 변경 처리"""
        self._update_settings_from_ui()
        self.settings_changed.emit()
    
    def load_settings(self):
        """설정 로드"""
        # 실제 구현에서는 설정 파일이나 데이터베이스에서 로드
        # 여기서는 기본값 사용
        self._update_ui_from_settings()
    
    def save_settings(self):
        """설정 저장"""
        # 실제 구현에서는 설정 파일이나 데이터베이스에 저장
        self._update_settings_from_ui()
        return True
    
    def get_settings(self) -> Dict[str, Any]:
        """설정 값 반환"""
        self._update_settings_from_ui()
        return self.settings.copy()