"""
테마 서비스 구현

Configuration Management와 StyleManager를 연결하여
Infrastructure Layer 기반 테마 관리를 제공합니다.
"""
from typing import Protocol
from PyQt6.QtCore import QObject, pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.services.settings_service import ISettingsService
from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager, Theme


class IThemeService(Protocol):
    """테마 서비스 인터페이스 (Protocol 사용으로 메타클래스 충돌 해결)"""

    def get_current_theme(self) -> str:
        """현재 테마 반환"""
        ...

    def set_theme(self, theme: str) -> bool:
        """테마 설정 및 즉시 적용"""
        ...

    def toggle_theme(self) -> str:
        """테마 전환 및 즉시 적용"""
        ...

    def apply_current_theme(self) -> bool:
        """현재 설정된 테마 적용"""
        ...

    def connect_theme_changed(self, callback) -> bool:
        """테마 변경 시그널 연결"""
        ...


class ThemeService(QObject):
    """테마 서비스 구현체 (Infrastructure Layer 기반)"""

    # 테마 변경 시그널
    theme_changed = pyqtSignal(str)  # 테마명 (light/dark)

    def __init__(self, settings_service: ISettingsService, style_manager: StyleManager):
        super().__init__()
        self.settings_service = settings_service
        self.style_manager = style_manager
        self.logger = create_component_logger("ThemeService")

        # 초기 테마 로드 및 적용
        self._load_and_apply_theme()

    def _load_and_apply_theme(self):
        """설정에서 테마 로드하고 StyleManager에 적용"""
        try:
            ui_config = self.settings_service.get_ui_config()
            theme_name = ui_config.theme

            # StyleManager에 테마 적용
            if theme_name == "dark":
                self.style_manager.set_theme(Theme.DARK)
            else:
                self.style_manager.set_theme(Theme.LIGHT)

            self.logger.info(f"✅ ThemeService: 설정에서 테마 로드 및 적용 완료 - {theme_name}")

        except Exception as e:
            self.logger.warning(f"⚠️ ThemeService: 테마 로드 실패, 기본 테마 사용 - {e}")
            self.style_manager.set_theme(Theme.LIGHT)

    def get_current_theme(self) -> str:
        """현재 테마 반환"""
        return self.style_manager.current_theme.value

    def set_theme(self, theme: str) -> bool:
        """테마 설정 및 즉시 적용"""
        try:
            # StyleManager에 테마 적용
            if theme == "dark":
                self.style_manager.set_theme(Theme.DARK)
            else:
                self.style_manager.set_theme(Theme.LIGHT)

            # SettingsService에 저장
            self.settings_service.update_ui_setting("theme", theme)

            # 테마 변경 시그널 발생
            self.theme_changed.emit(theme)

            # theme_notifier에도 알림
            self._notify_theme_changed()

            self.logger.info(f"✅ ThemeService: 테마 변경 및 저장 완료 - {theme}")
            return True

        except Exception as e:
            self.logger.error(f"❌ ThemeService: 테마 설정 실패 - {e}")
            return False

    def toggle_theme(self) -> str:
        """테마 전환 및 즉시 적용"""
        current_theme = self.get_current_theme()
        new_theme = "dark" if current_theme == "light" else "light"

        if self.set_theme(new_theme):
            return new_theme
        else:
            return current_theme

    def apply_current_theme(self) -> bool:
        """현재 설정된 테마 적용"""
        try:
            self.style_manager.apply_theme()
            self._notify_theme_changed()
            self.logger.info(f"✅ ThemeService: 현재 테마 재적용 완료 - {self.get_current_theme()}")
            return True
        except Exception as e:
            self.logger.error(f"❌ ThemeService: 테마 재적용 실패 - {e}")
            return False

    def connect_theme_changed(self, callback) -> bool:
        """테마 변경 시그널 연결"""
        try:
            self.theme_changed.connect(callback)
            return True
        except Exception as e:
            self.logger.error(f"❌ ThemeService: 시그널 연결 실패 - {e}")
            return False

    def _notify_theme_changed(self):
        """기존 theme_notifier 시스템에 테마 변경 알림"""
        try:
            from upbit_auto_trading.ui.desktop.common.theme_notifier import get_theme_notifier
            theme_notifier = get_theme_notifier()
            theme_notifier.notify_theme_changed()
            self.logger.info("✅ ThemeService: theme_notifier에 테마 변경 알림 완료")
        except Exception as e:
            self.logger.warning(f"⚠️ ThemeService: theme_notifier 알림 실패 - {e}")


class MockThemeService:
    """Mock 테마 서비스 (테스트용) - 메타클래스 충돌 없음"""

    def __init__(self):
        self._current_theme = "light"
        self.logger = create_component_logger("MockThemeService")

    def get_current_theme(self) -> str:
        return self._current_theme

    def set_theme(self, theme: str) -> bool:
        self._current_theme = theme
        self.logger.info(f"🧪 MockThemeService: 테마 설정 - {theme}")
        return True

    def toggle_theme(self) -> str:
        self._current_theme = "dark" if self._current_theme == "light" else "light"
        self.logger.info(f"🧪 MockThemeService: 테마 전환 - {self._current_theme}")
        return self._current_theme

    def apply_current_theme(self) -> bool:
        self.logger.info(f"🧪 MockThemeService: 테마 적용 - {self._current_theme}")
        return True

    def connect_theme_changed(self, callback) -> bool:
        self.logger.info("🧪 MockThemeService: 시그널 연결")
        return True
