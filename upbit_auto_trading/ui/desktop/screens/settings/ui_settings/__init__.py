"""
UI 설정 모듈

이 모듈은 UI 설정 관련 컴포넌트들을 제공합니다.
"""

from .views import UISettingsView
from .presenters import UISettingsPresenter
from .widgets import (
    ThemeSelectorWidget, WindowSettingsWidget,
    AnimationSettingsWidget, ChartSettingsWidget
)

__all__ = [
    'UISettingsView',
    'UISettingsPresenter',
    'ThemeSelectorWidget',
    'WindowSettingsWidget',
    'AnimationSettingsWidget',
    'ChartSettingsWidget',
    'UISettingsManager'  # 호환성 어댑터
]


class UISettingsManager:
    """
    UI 설정 매니저 - 호환성 어댑터

    기존 코드와의 호환성을 위한 어댑터 클래스입니다.
    내부적으로는 새로운 MVP 구조를 사용하지만
    기존 인터페이스를 그대로 제공합니다.
    """

    def __init__(self, parent=None, settings_service=None):
        """초기화

        Args:
            parent: 부모 위젯
            settings_service: 설정 서비스 인스턴스
        """
        # MVP 컴포넌트 생성
        self._presenter = UISettingsPresenter(settings_service)
        self._view = UISettingsView(parent)

        # MVP 연결
        self._view.set_presenter(self._presenter)

        # 기존 호환성을 위한 참조
        self.widget = self._view

    def get_widget(self):
        """위젯 반환 (기존 호환성)"""
        return self._view

    def load_settings(self):
        """설정 로드"""
        self._view.load_settings()

    def save_settings(self):
        """설정 저장"""
        self._view.save_settings()

    # 기존 코드 호환성을 위한 속성들
    @property
    def settings_changed(self):
        return self._view.settings_changed

    @property
    def theme_changed(self):
        return self._presenter.theme_changed
