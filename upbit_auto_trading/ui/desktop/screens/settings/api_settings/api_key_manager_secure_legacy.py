"""
API 설정 통합 컴포넌트

기존 ApiKeyManagerSecure와 호환되는 인터페이스를 제공하는 통합 클래스

Phase 2 마이그레이션으로 생성됨:
- 기존: ApiKeyManagerSecure (단일 클래스)
- 새로운: ApiSettingsView + ApiSettingsPresenter + Widgets (DDD + MVP 패턴)
- 호환성: 기존 인터페이스 유지
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .presenters.api_settings_presenter import ApiSettingsPresenter
from .views.api_settings_view import ApiSettingsView

class ApiKeyManagerSecure(QWidget):
    """
    API 키 관리자 - DDD + MVP 패턴 (Phase 2 마이그레이션)

    기존 ApiKeyManagerSecure와 완전히 동일한 인터페이스를 제공하면서,
    내부적으로는 새로운 DDD + MVP 구조를 사용합니다.

    이 클래스는 기존 코드와의 호환성을 보장하는 어댑터 역할을 합니다.
    """

    # 기존과 동일한 시그널
    settings_changed = pyqtSignal()
    api_status_changed = pyqtSignal(bool)

    def __init__(self, parent=None, api_key_service=None):
        super().__init__(parent)
        self.setObjectName("widget-api-key-manager-secure")

        self.logger = create_component_logger("ApiKeyManagerSecure")
        self.logger.info("🔄 API 키 관리자 Phase 2 마이그레이션 초기화 시작")

        # ApiKeyService 저장 (Presenter에 전달용)
        self.api_key_service = api_key_service

        self._setup_mvp_components()
        self._setup_ui()
        self._connect_signals()

        self.logger.info("✅ API 키 관리자 Phase 2 마이그레이션 완료")

    def _setup_mvp_components(self):
        """MVP 컴포넌트 초기화"""
        # View 생성
        self.view = ApiSettingsView(self, self.api_key_service)

        # Presenter 생성 및 연결
        self.presenter = ApiSettingsPresenter(self.view, self.api_key_service)
        self.view.set_presenter(self.presenter)

        self.logger.info("✅ MVP 컴포넌트 초기화 완료")

    def _setup_ui(self):
        """UI 설정 - View를 단순히 포함"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.view)

    def _connect_signals(self):
        """시그널 연결 - View의 시그널을 외부로 중계"""
        self.view.settings_changed.connect(self.settings_changed.emit)
        self.view.api_status_changed.connect(self.api_status_changed.emit)

    # === 기존 ApiKeyManagerSecure와 호환되는 인터페이스 ===

    def load_settings(self):
        """설정 로드 (기존 인터페이스 호환)"""
        if hasattr(self.view, 'load_settings'):
            self.view.load_settings()
        else:
            self.logger.warning("View에 load_settings 메서드가 없습니다")

    def save_settings(self):
        """설정 저장 (기존 인터페이스 호환)"""
        if hasattr(self.view, 'save_settings'):
            self.view.save_settings()
        else:
            self.logger.warning("View에 save_settings 메서드가 없습니다")

    def save_api_keys(self):
        """API 키 저장 (기존 인터페이스 호환)"""
        self.save_settings()

    def test_api_keys(self, silent=False):
        """API 키 테스트 (기존 인터페이스 호환)"""
        if self.presenter:
            try:
                success, message = self.presenter.test_api_connection(silent=silent)

                # View의 연결 위젯 업데이트
                if hasattr(self.view, 'connection_widget'):
                    self.view.connection_widget.update_connection_status(success, message)

                # silent 모드가 아니면 메시지 표시
                if not silent:
                    if success:
                        self.view.show_info_message("테스트 성공", message)
                    else:
                        self.view.show_error_message("테스트 실패", message)

                return success

            except Exception as e:
                self.logger.error(f"API 테스트 중 오류: {e}")
                if not silent:
                    self.view.show_error_message("테스트 오류", f"테스트 중 오류가 발생했습니다: {str(e)}")
                return False

        return False

    def delete_api_keys(self):
        """API 키 삭제 (기존 인터페이스 호환)"""
        if hasattr(self.view, '_on_delete_clicked'):
            self.view._on_delete_clicked()
        else:
            self.logger.warning("View에 삭제 메서드가 없습니다")

    # === Infrastructure Layer 연동 (기존 호환성) ===

    def _report_to_infrastructure(self):
        """Infrastructure Layer v4.0에 상태 보고 (기존 호환성)"""
        # Presenter에서 이미 처리되므로 패스
        pass

    def _update_button_states(self, has_saved_keys: bool):
        """버튼 상태 업데이트 (기존 호환성)"""
        # View에서 자동으로 처리되므로 패스
        pass

    # === 접근자 메서드 (필요시 확장) ===

    def get_view(self) -> ApiSettingsView:
        """View 인스턴스 반환"""
        return self.view

    def get_presenter(self) -> ApiSettingsPresenter:
        """Presenter 인스턴스 반환"""
        return self.presenter
