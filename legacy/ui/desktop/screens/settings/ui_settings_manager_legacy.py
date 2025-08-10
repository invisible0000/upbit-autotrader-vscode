"""
UI 설정 호환성 어댑터

이 모듈은 기존 UISettings 클래스 인터페이스를 유지하면서
새로운 DDD+MVP 구조로 구현을 위임하는 어댑터입니다.

기존 import 경로:
from upbit_auto_trading.ui.desktop.screens.settings.ui_settings_view import UISettings

새로운 구조:
- View: ui_settings/views/ui_settings_view.py
- Presenter: ui_settings/presenters/ui_settings_presenter.py
- Widgets: ui_settings/widgets/
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget

# Infrastructure Layer Enhanced Logging v4.0
from upbit_auto_trading.infrastructure.logging import create_component_logger

# 새로운 MVP 구조 import
from . import UISettingsManager


class UISettings(QWidget):
    """
    UI 설정 위젯 클래스 - 호환성 어댑터

    기존 UISettings 클래스와 동일한 인터페이스를 제공하면서
    내부적으로는 새로운 DDD+MVP 구조를 사용합니다.

    ✅ Phase 3 완료: DDD+MVP 패턴 적용
    - Presenter: UI 설정 비즈니스 로직
    - View: UI 컴포넌트 조합
    - Widgets: 테마/창/애니메이션/차트 위젯 분리
    """

    # 기존 시그널 호환성 유지
    settings_changed = pyqtSignal()
    theme_changed = pyqtSignal(str)

    def __init__(self, parent=None, settings_service=None):
        """초기화 - Infrastructure Layer v4.0 통합

        Args:
            parent: 부모 위젯
            settings_service: SettingsService 인스턴스
        """
        super().__init__(parent)
        self.setObjectName("widget-ui-settings")

        # Infrastructure Layer Enhanced Logging v4.0 초기화
        self.logger = create_component_logger("UISettings")
        self.logger.info("🎨 UI 설정 위젯 초기화 시작 (DDD+MVP 어댑터)")

        # 새로운 MVP 매니저 생성
        self._manager = UISettingsManager(self, settings_service)

        # 기존 호환성을 위한 참조
        self.settings_service = settings_service

        # MVP View를 현재 위젯에 임베드
        self._embed_mvp_view()

        # 시그널 연결
        self._connect_signals()

        # Infrastructure Layer 연동 상태 확인
        self._check_infrastructure_integration()

        self.logger.info("✅ UI 설정 위젯 초기화 완료 (DDD+MVP 구조)")

    def _embed_mvp_view(self):
        """MVP View를 현재 위젯에 임베드"""
        from PyQt6.QtWidgets import QVBoxLayout

        # 레이아웃 설정
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # MVP View 추가
        mvp_view = self._manager.get_widget()
        layout.addWidget(mvp_view)

    def _connect_signals(self):
        """기존 시그널과 새로운 MVP 시그널 연결"""
        # MVP Presenter의 시그널을 기존 시그널로 연결
        self._manager._presenter.theme_changed.connect(self.theme_changed.emit)
        self._manager._presenter.settings_applied.connect(self.settings_changed.emit)

        # View의 시그널도 연결
        self._manager._view.apply_requested.connect(self.settings_changed.emit)

    def _check_infrastructure_integration(self):
        """Infrastructure Layer v4.0 연동 상태 확인"""
        try:
            # SystemStatusTracker 상태 보고
            from upbit_auto_trading.infrastructure.logging.briefing.status_tracker import SystemStatusTracker
            tracker = SystemStatusTracker()
            tracker.update_component_status(
                "UISettings",
                "OK",
                "UI 설정 위젯 로드됨 (DDD+MVP)",
                widget_type="settings_tab",
                features_count=4,
                architecture="DDD+MVP"
            )
            self.logger.info("📊 SystemStatusTracker에 UI 설정 상태 보고 완료")
        except Exception as e:
            self.logger.warning(f"⚠️ SystemStatusTracker 연동 실패: {e}")

    # ===========================================
    # 기존 호환성 유지를 위한 메서드들
    # ===========================================

    def _load_settings(self):
        """설정 로드 (기존 호환성 유지)"""
        self._manager.load_settings()

    def load_settings(self):
        """설정 로드 (외부 호출용)"""
        self._manager.load_settings()

    def save_settings(self):
        """설정 저장 (외부 호출용)"""
        self._manager.save_settings()

    def save_all_settings(self):
        """모든 설정 저장 (전체 저장용)"""
        self._manager.save_settings()

    def _apply_all_settings_batch(self):
        """모든 설정 배치 저장 (기존 호환성 유지)"""
        self._manager.save_settings()

    def _apply_all_settings(self):
        """모든 설정 적용 (기존 호환성 유지용)"""
        self._manager.save_settings()

    def _apply_settings(self):
        """설정 적용 (기존 호환성 유지)"""
        self._manager.save_settings()

    def _reset_to_defaults(self):
        """기본값으로 복원"""
        if self._manager._presenter:
            self._manager._presenter.reset_to_defaults()

    # 기존 메서드들 (더 이상 사용하지 않지만 호환성 유지)
    def _setup_ui(self):
        """UI 설정 (더 이상 사용안함 - MVP View가 처리)"""
        pass

    def _on_theme_changed_batch(self):
        """테마 변경 처리 (더 이상 사용안함)"""
        pass

    def _on_setting_changed_batch(self):
        """기타 설정 변경 처리 (더 이상 사용안함)"""
        pass

    def _update_unsaved_changes_state(self):
        """저장하지 않은 변경사항 상태 업데이트 (더 이상 사용안함)"""
        pass

    def _apply_other_settings(self):
        """기타 설정 저장 (기존 호환성 유지용)"""
        self._manager.save_settings()

    def _disconnect_change_signals(self):
        """변경 감지 시그널 연결 해제 (더 이상 사용안함)"""
        pass

    def _connect_change_signals(self):
        """변경 감지 시그널 연결 (더 이상 사용안함)"""
        pass

    def _set_default_values(self):
        """기본값 설정 (더 이상 사용안함)"""
        pass

    def _on_theme_changed(self):
        """테마 변경 처리 (기존 호환성 유지)"""
        pass

    def _on_settings_changed(self):
        """설정 변경 처리 (기존 호환성 유지)"""
        pass
