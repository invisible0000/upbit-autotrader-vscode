"""
알림 방법 설정 위젯

이 모듈은 알림 방법 설정을 담당하는 위젯입니다.
- 소리 알림
- 데스크톱 알림
- 이메일 알림
"""

from typing import Dict, Any
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QGroupBox, QLabel

# Infrastructure Layer Enhanced Logging v4.0
# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)

class NotificationMethodsWidget(QWidget):
    """알림 방법 설정 위젯"""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("widget-notification-methods")

        self.logger = create_component_logger("NotificationMethodsWidget")
        self.logger.debug("📢 NotificationMethodsWidget 초기화")

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 알림 방법 그룹
        group = QGroupBox("알림 방법")
        group.setObjectName("group-notification-methods")
        group_layout = QVBoxLayout(group)

        # 소리 알림 체크박스
        self.notification_sound_checkbox = QCheckBox("소리 알림")
        self.notification_sound_checkbox.setObjectName("checkbox-notification-sound")
        group_layout.addWidget(self.notification_sound_checkbox)

        # 데스크톱 알림 체크박스
        self.desktop_notifications_checkbox = QCheckBox("데스크톱 알림")
        self.desktop_notifications_checkbox.setObjectName("checkbox-desktop-notifications")
        group_layout.addWidget(self.desktop_notifications_checkbox)

        # 이메일 알림 체크박스
        self.email_notifications_checkbox = QCheckBox("이메일 알림")
        self.email_notifications_checkbox.setObjectName("checkbox-email-notifications")
        group_layout.addWidget(self.email_notifications_checkbox)

        # 이메일 주소 입력 폼
        email_layout = QHBoxLayout()
        email_label = QLabel("이메일 주소:")
        email_label.setObjectName("label-email")
        self.email_status_label = QLabel("이메일 설정은 향후 업데이트에서 지원될 예정입니다.")
        self.email_status_label.setObjectName("label-email-status")
        self.email_status_label.setEnabled(False)
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_status_label, 1)
        group_layout.addLayout(email_layout)

        layout.addWidget(group)

    def _connect_signals(self):
        """시그널 연결"""
        self.notification_sound_checkbox.stateChanged.connect(self._on_setting_changed)
        self.desktop_notifications_checkbox.stateChanged.connect(self._on_setting_changed)
        self.email_notifications_checkbox.stateChanged.connect(self._on_setting_changed)

    def _on_setting_changed(self):
        """설정 변경 시 호출"""
        settings = self._collect_settings()
        self.logger.debug(f"🔧 알림 방법 설정 변경: {settings}")
        self.settings_changed.emit(settings)

        # 이메일 알림 상태에 따른 UI 업데이트
        self._update_email_ui()

    def _collect_settings(self) -> Dict[str, Any]:
        """현재 위젯 설정 수집"""
        return {
            'notification_sound': self.notification_sound_checkbox.isChecked(),
            'desktop_notifications': self.desktop_notifications_checkbox.isChecked(),
            'email_notifications': self.email_notifications_checkbox.isChecked()
        }

    def _update_email_ui(self):
        """이메일 알림 UI 상태 업데이트"""
        email_enabled = self.email_notifications_checkbox.isChecked()
        if email_enabled:
            self.email_status_label.setText("이메일 알림이 활성화되었습니다. (향후 업데이트에서 상세 설정 지원)")
            self.email_status_label.setStyleSheet("color: orange;")
        else:
            self.email_status_label.setText("이메일 설정은 향후 업데이트에서 지원될 예정입니다.")
            self.email_status_label.setStyleSheet("")

    def update_from_settings(self, settings: Dict[str, Any]):
        """설정에서 UI 업데이트"""
        # 시그널 일시 차단
        self.notification_sound_checkbox.blockSignals(True)
        self.desktop_notifications_checkbox.blockSignals(True)
        self.email_notifications_checkbox.blockSignals(True)

        # 값 설정
        self.notification_sound_checkbox.setChecked(settings.get('notification_sound', True))
        self.desktop_notifications_checkbox.setChecked(settings.get('desktop_notifications', True))
        self.email_notifications_checkbox.setChecked(settings.get('email_notifications', False))

        # 시그널 차단 해제
        self.notification_sound_checkbox.blockSignals(False)
        self.desktop_notifications_checkbox.blockSignals(False)
        self.email_notifications_checkbox.blockSignals(False)

        # 이메일 UI 업데이트
        self._update_email_ui()

        self.logger.debug("📥 알림 방법 설정 UI 업데이트 완료")
