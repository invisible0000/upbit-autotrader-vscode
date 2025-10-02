"""
알림 설정 패키지 초기화

이 패키지는 DDD+MVP 패턴을 적용한 알림 설정 시스템입니다.
"""

from .views.notification_settings_view import NotificationSettingsView
# Presenter는 presentation/presenters/settings/로 이동됨

__all__ = [
    'NotificationSettingsView'
]
