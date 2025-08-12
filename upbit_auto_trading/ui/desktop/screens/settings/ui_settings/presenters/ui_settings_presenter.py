"""
UI 설정 Presenter

이 모듈은 UI 설정 화면의 MVP 패턴 Presenter를 구현합니다.
- View와 Application Layer 간 중재
- 설정 변경 로직 조율
- 상태 관리 및 검증
"""

from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger

class UISettingsPresenter(QObject):
    """UI 설정 Presenter - MVP 패턴"""

    # 시그널
    theme_changed = pyqtSignal(str)  # 테마 변경 알림
    settings_applied = pyqtSignal()  # 설정 적용 완료 알림

    def __init__(self, settings_service=None):
        """초기화

        Args:
            settings_service: 설정 서비스 인스턴스
        """
        super().__init__()

        # 로깅 설정
        self.logger = create_component_logger("UISettingsPresenter")
        self.logger.info("🎯 UI 설정 Presenter 초기화 시작")

        # 서비스 의존성
        self.settings_service = settings_service

        # 내부 상태
        self._view = None
        self._pending_changes: Dict[str, Any] = {}
        self._has_unsaved_changes = False

        # 의존성 검증
        if self.settings_service is None:
            self.logger.warning("⚠️ SettingsService가 None으로 전달됨")
        else:
            self.logger.info(f"✅ SettingsService 의존성 주입 성공: {type(self.settings_service).__name__}")

        self.logger.info("✅ UI 설정 Presenter 초기화 완료")

    def set_view(self, view):
        """View 설정 및 연결

        Args:
            view: UI 설정 View 인스턴스
        """
        self._view = view
        self.logger.info("🔗 View 연결됨")

        # View의 위젯들과 연결
        if hasattr(self._view, 'theme_widget'):
            self._view.theme_widget.theme_changed.connect(self._on_theme_changed)
            self._view.theme_widget.settings_changed.connect(self._on_setting_changed)

        if hasattr(self._view, 'window_widget'):
            self._view.window_widget.settings_changed.connect(self._on_setting_changed)

        if hasattr(self._view, 'animation_widget'):
            self._view.animation_widget.settings_changed.connect(self._on_setting_changed)

        if hasattr(self._view, 'chart_widget'):
            self._view.chart_widget.settings_changed.connect(self._on_setting_changed)

    def load_settings(self):
        """설정 로드 및 View에 적용"""
        if not self.settings_service:
            self.logger.warning("⚠️ SettingsService가 없어 기본값 사용")
            self._load_default_settings()
            return

        try:
            self.logger.info("📥 UI 설정 로드 시작")

            # UI 설정 로드
            ui_config = self.settings_service.get_ui_config()

            if self._view:
                # 테마 설정
                if hasattr(self._view, 'theme_widget'):
                    self._view.theme_widget.set_theme(ui_config.theme)

                # 창 설정
                if hasattr(self._view, 'window_widget'):
                    self._view.window_widget.set_window_size(
                        ui_config.window_width,
                        ui_config.window_height
                    )
                    self._view.window_widget.set_save_window_state(ui_config.save_window_state)

                # 애니메이션 설정
                if hasattr(self._view, 'animation_widget'):
                    self._view.animation_widget.set_animation_enabled(ui_config.animation_enabled)
                    self._view.animation_widget.set_smooth_scrolling(ui_config.smooth_scrolling)

                # 차트 설정
                if hasattr(self._view, 'chart_widget'):
                    self._view.chart_widget.set_chart_style(ui_config.chart_style)
                    self._view.chart_widget.set_chart_update_interval(
                        int(ui_config.chart_update_interval_seconds)
                    )

            # 변경사항 초기화
            self._pending_changes.clear()
            self._update_unsaved_state(False)

            self.logger.info("✅ UI 설정 로드 완료")

        except Exception as e:
            self.logger.error(f"❌ UI 설정 로드 실패: {e}")
            self._load_default_settings()

    def _load_default_settings(self):
        """기본 설정 로드"""
        self.logger.info("📄 기본 설정 적용")

        if self._view:
            if hasattr(self._view, 'theme_widget'):
                self._view.theme_widget.reset_to_default()
            if hasattr(self._view, 'window_widget'):
                self._view.window_widget.reset_to_default()
            if hasattr(self._view, 'animation_widget'):
                self._view.animation_widget.reset_to_default()
            if hasattr(self._view, 'chart_widget'):
                self._view.chart_widget.reset_to_default()

        self._pending_changes.clear()
        self._update_unsaved_state(False)

    def _on_theme_changed(self, theme: str):
        """테마 변경 처리

        Args:
            theme: 변경된 테마 값
        """
        self.logger.debug(f"🎨 테마 변경 요청: {theme}")
        self._pending_changes["theme"] = theme
        self._update_unsaved_state(True)

    def _on_setting_changed(self):
        """일반 설정 변경 처리"""
        self.logger.debug("🔧 설정 변경 감지됨")

        if self._view:
            # 모든 현재 설정값을 pending_changes에 수집
            self._collect_current_settings()
            self._update_unsaved_state(True)

    def _collect_current_settings(self):
        """현재 View의 모든 설정값 수집"""
        if not self._view:
            return

        try:
            # 테마 설정 (기본값 복원 시 필요)
            if hasattr(self._view, 'theme_widget'):
                current_theme = self._view.theme_widget.get_theme()
                self._pending_changes["theme"] = current_theme

            # 창 설정
            if hasattr(self._view, 'window_widget'):
                self._pending_changes.update({
                    "window_width": self._view.window_widget.get_window_width(),
                    "window_height": self._view.window_widget.get_window_height(),
                    "save_window_state": self._view.window_widget.get_save_window_state()
                })

            # 애니메이션 설정
            if hasattr(self._view, 'animation_widget'):
                self._pending_changes.update({
                    "animation_enabled": self._view.animation_widget.get_animation_enabled(),
                    "smooth_scrolling": self._view.animation_widget.get_smooth_scrolling()
                })

            # 차트 설정
            if hasattr(self._view, 'chart_widget'):
                self._pending_changes.update({
                    "chart_style": self._view.chart_widget.get_chart_style(),
                    "chart_update_interval_seconds": self._view.chart_widget.get_chart_update_interval()
                })

        except Exception as e:
            self.logger.error(f"❌ 설정값 수집 실패: {e}")

    def apply_all_settings(self):
        """모든 변경사항 적용"""
        if not self.settings_service:
            self.logger.warning("⚠️ SettingsService가 없어 설정 저장 불가")
            return

        if not self._pending_changes:
            self.logger.info("📝 저장할 변경사항이 없습니다")
            return

        try:
            self.logger.info("💾 설정 저장 시작")

            # View 상태 업데이트
            if self._view:
                self._view.set_apply_button_state(False, "저장 중...")

            # 모든 변경사항 적용
            for key, value in self._pending_changes.items():
                self.settings_service.update_ui_setting(key, value)
                self.logger.debug(f"💾 저장됨: {key} = {value}")

            # 테마 변경이 있으면 시그널 발생
            if "theme" in self._pending_changes:
                theme_value = self._pending_changes["theme"]
                self.theme_changed.emit(theme_value)
                self.logger.info(f"🎨 테마 변경 시그널 발생: {theme_value}")

            # 변경사항 초기화
            self._pending_changes.clear()
            self._update_unsaved_state(False)

            # 완료 시그널 발생
            self.settings_applied.emit()

            self.logger.info("✅ 설정 저장 완료")

        except Exception as e:
            self.logger.error(f"❌ 설정 저장 실패: {e}")
        finally:
            # View 상태 복원
            if self._view:
                self._view.set_apply_button_state(self._has_unsaved_changes, "설정 저장")

    def reset_to_defaults(self):
        """기본값으로 재설정"""
        self.logger.info("🔄 기본값으로 재설정")

        if self._view:
            if hasattr(self._view, 'theme_widget'):
                self._view.theme_widget.reset_to_default()
            if hasattr(self._view, 'window_widget'):
                self._view.window_widget.reset_to_default()
            if hasattr(self._view, 'animation_widget'):
                self._view.animation_widget.reset_to_default()
            if hasattr(self._view, 'chart_widget'):
                self._view.chart_widget.reset_to_default()

        # 변경사항이 발생하므로 업데이트
        self._collect_current_settings()
        self._update_unsaved_state(True)

    def _update_unsaved_state(self, has_changes: bool):
        """저장하지 않은 변경사항 상태 업데이트

        Args:
            has_changes: 변경사항 존재 여부
        """
        if has_changes != self._has_unsaved_changes:
            self._has_unsaved_changes = has_changes

            if self._view:
                self._view.set_apply_button_state(has_changes, "설정 저장")

            if has_changes:
                self.logger.debug("🔄 저장하지 않은 변경사항 발견")
            else:
                self.logger.debug("✅ 모든 변경사항 저장됨")

    def has_unsaved_changes(self) -> bool:
        """저장하지 않은 변경사항 존재 여부

        Returns:
            bool: 변경사항 존재 여부
        """
        return self._has_unsaved_changes
