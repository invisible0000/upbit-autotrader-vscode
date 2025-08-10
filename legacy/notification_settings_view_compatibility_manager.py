"""
알림 설정 매니저 - Phase 4 DDD+MVP 구현

이 모듈은 기존 notification_settings_view.py를 대체하는 완전한 DDD+MVP 구현체입니다.
settings_screen.py와의 호환성을 유지하면서 깨끗한 아키텍처를 제공합니다.
"""

from typing import Dict, Any
from PyQt6.QtCore import pyqtSignal

# Infrastructure Layer Enhanced Logging v4.0
from upbit_auto_trading.infrastructure.logging import create_component_logger

# DDD+MVP Components
from .notification_settings.views.notification_settings_view import NotificationSettingsView


class NotificationSettings(NotificationSettingsView):
    """
    알림 설정 매니저 - settings_screen.py 호환성 유지

    이 클래스는 기존 NotificationSettings 클래스의 인터페이스를 유지하면서
    내부적으로는 완전한 DDD+MVP 구조를 사용합니다.
    """

    # 기존 시그널 호환성 유지
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        """초기화 - 기존 인터페이스 호환성 유지"""
        super().__init__(parent)
        self.setObjectName("widget-notification-settings")

        # Infrastructure Layer Enhanced Logging v4.0
        self.logger = create_component_logger("NotificationSettings")
        self.logger.info("🔔 NotificationSettings (DDD+MVP) 초기화")

        # MVP View의 시그널을 기존 시그널로 연결
        super().settings_changed.connect(self.settings_changed.emit)

        self._report_compatibility_status()
        self.logger.info("✅ NotificationSettings (DDD+MVP) 초기화 완료")

    def _report_compatibility_status(self):
        """호환성 상태 보고"""
        try:
            from upbit_auto_trading.infrastructure.logging.briefing.status_tracker import SystemStatusTracker
            tracker = SystemStatusTracker()
            tracker.update_component_status(
                "NotificationSettings",
                "OK",
                "DDD+MVP 구조 적용 완료",
                compatibility_mode="direct_inheritance",
                architecture="DDD+MVP"
            )
            self.logger.info("📊 SystemStatusTracker에 호환성 상태 보고 완료")
        except Exception as e:
            self.logger.warning(f"⚠️ SystemStatusTracker 연동 실패: {e}")

    # 기존 인터페이스 메서드들 - MVP View로 위임
    def load_settings(self):
        """설정 로드 - 기존 인터페이스 호환성"""
        self.logger.info("📥 알림 설정 로드 (호환성 메서드)")
        return super().load_settings()

    def save_settings(self):
        """설정 저장 - 기존 인터페이스 호환성"""
        self.logger.info("💾 알림 설정 저장 (호환성 메서드)")
        return super().save_settings()

    def get_settings(self) -> Dict[str, Any]:
        """설정 반환 - 기존 인터페이스 호환성"""
        return super().get_settings()

    # 추가 호환성 메서드들
    @property
    def settings(self) -> Dict[str, Any]:
        """설정 프로퍼티 - 기존 코드 호환성"""
        return self.get_settings()

    def _update_ui_from_settings(self):
        """UI 업데이트 - 기존 메서드명 호환성"""
        # MVP에서는 Presenter가 자동으로 처리하므로 별도 동작 불필요
        self.logger.debug("🔄 UI 업데이트 (MVP에서 자동 처리됨)")

    def _update_settings_from_ui(self):
        """설정 업데이트 - 기존 메서드명 호환성"""
        # MVP에서는 위젯이 자동으로 Presenter에 알리므로 별도 동작 불필요
        self.logger.debug("🔄 설정 업데이트 (MVP에서 자동 처리됨)")

    def _on_settings_changed(self):
        """설정 변경 처리 - 기존 메서드명 호환성"""
        # MVP View에서 이미 처리되므로 시그널만 발생
        self.settings_changed.emit()
        self.logger.debug("📤 설정 변경 시그널 발생 (호환성 메서드)")
