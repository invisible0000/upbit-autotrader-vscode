"""
알림 설정 View - MVP 패턴 구현

이 모듈은 알림 설정의 View 레이어를 담당합니다.
DDD 아키텍처에서 Presentation Layer 역할을 수행합니다.
"""

from typing import Dict, Any
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout

# Infrastructure Layer Enhanced Logging v4.0
from upbit_auto_trading.infrastructure.logging import create_component_logger

# Widgets
from ..widgets.alert_types_widget import AlertTypesWidget
from ..widgets.notification_methods_widget import NotificationMethodsWidget
from ..widgets.notification_frequency_widget import NotificationFrequencyWidget
from ..widgets.quiet_hours_widget import QuietHoursWidget

# Presenter
from ..presenters.notification_settings_presenter import NotificationSettingsPresenter

class NotificationSettingsView(QWidget):
    """알림 설정 View - MVP 패턴 Presentation Layer"""

    # 외부 시그널
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("widget-notification-settings")

        # Infrastructure Layer Enhanced Logging v4.0
        self.logger = create_component_logger("NotificationSettingsView")
        self.logger.info("🔔 NotificationSettingsView 초기화 시작")

        # Presenter 생성 (MVP 패턴)
        self.presenter = NotificationSettingsPresenter()

        # 위젯 초기화
        self._init_widgets()
        self._setup_ui()
        self._connect_signals()

        # 초기 데이터 로드
        self.presenter.load_settings()

        self._report_to_infrastructure()
        self.logger.info("✅ NotificationSettingsView 초기화 완료")

    def _report_to_infrastructure(self):
        """Infrastructure Layer 상태 보고 (레거시 briefing 시스템 제거됨)"""
        self.logger.debug("알림 설정 View 상태 보고 완료")

    def _init_widgets(self):
        """위젯 초기화"""
        self.alert_types_widget = AlertTypesWidget()
        self.notification_methods_widget = NotificationMethodsWidget()
        self.notification_frequency_widget = NotificationFrequencyWidget()
        self.quiet_hours_widget = QuietHoursWidget()

        self.logger.debug("🎛️ 알림 설정 위젯들 초기화 완료")

    def _setup_ui(self):
        """UI 레이아웃 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 위젯 추가
        main_layout.addWidget(self.alert_types_widget)
        main_layout.addWidget(self.notification_methods_widget)
        main_layout.addWidget(self.notification_frequency_widget)
        main_layout.addWidget(self.quiet_hours_widget)

        # 빈 공간 추가
        main_layout.addStretch(1)

        self.logger.debug("🎨 알림 설정 UI 레이아웃 설정 완료")

    def _connect_signals(self):
        """시그널 연결"""
        # Presenter 시그널 연결
        self.presenter.settings_updated.connect(self._on_settings_updated)
        self.presenter.settings_changed.connect(self._on_settings_changed)

        # 위젯 시그널 연결
        self.alert_types_widget.settings_changed.connect(self._on_widget_settings_changed)
        self.notification_methods_widget.settings_changed.connect(self._on_widget_settings_changed)
        self.notification_frequency_widget.settings_changed.connect(self._on_widget_settings_changed)
        self.quiet_hours_widget.settings_changed.connect(self._on_widget_settings_changed)

        self.logger.debug("🔗 알림 설정 시그널 연결 완료")

    def _on_settings_updated(self, settings: Dict[str, Any]):
        """Presenter에서 설정 업데이트 시 호출"""
        self.logger.debug("📥 Presenter로부터 설정 업데이트 수신")

        # 각 위젯에 설정 전달
        self.alert_types_widget.update_from_settings(settings)
        self.notification_methods_widget.update_from_settings(settings)
        self.notification_frequency_widget.update_from_settings(settings)
        self.quiet_hours_widget.update_from_settings(settings)

    def _on_settings_changed(self):
        """설정 변경 시 외부에 알림"""
        self.logger.debug("📤 설정 변경 시그널 발생")
        self.settings_changed.emit()

    def _on_widget_settings_changed(self, widget_settings: Dict[str, Any]):
        """위젯에서 설정 변경 시 호출"""
        self.logger.debug(f"🔧 위젯 설정 변경: {list(widget_settings.keys())}")

        # Presenter에 변경사항 전달
        self.presenter.update_multiple_settings(widget_settings)

    # Public Interface
    def load_settings(self):
        """설정 로드"""
        self.logger.info("📥 알림 설정 로드 요청")
        return self.presenter.load_settings()

    def save_settings(self):
        """설정 저장"""
        self.logger.info("💾 알림 설정 저장 요청")
        return self.presenter.save_settings()

    def get_settings(self) -> Dict[str, Any]:
        """현재 설정 반환"""
        return self.presenter.get_current_settings()

    def reset_to_defaults(self):
        """기본값으로 재설정"""
        self.logger.info("🔄 알림 설정 기본값 재설정 요청")
        self.presenter.reset_to_defaults()

    def validate_settings(self) -> bool:
        """설정 유효성 검증"""
        return self.presenter.validate_settings()

    def get_active_notification_types(self) -> list:
        """활성화된 알림 유형 목록"""
        return self.presenter.get_active_notification_types()

    def get_active_notification_methods(self) -> list:
        """활성화된 알림 방법 목록"""
        return self.presenter.get_active_notification_methods()
