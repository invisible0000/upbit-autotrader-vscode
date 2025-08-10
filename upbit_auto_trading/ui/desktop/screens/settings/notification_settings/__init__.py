"""
알림 설정 패키지 초기화

이 패키지는 DDD+MVP 패턴을 적용한 알림 설정 시스템입니다.
"""

from .views.notification_settings_view import NotificationSettingsView
from .presenters.notification_settings_presenter import NotificationSettingsPresenter

# 호환성 alias (settings_screen.py에서 사용)
NotificationSettings = NotificationSettingsView

__all__ = [
    'NotificationSettingsView',
    'NotificationSettingsPresenter',
    'NotificationSettings'
]
