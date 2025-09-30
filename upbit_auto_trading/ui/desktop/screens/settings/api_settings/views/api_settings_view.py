"""
API 설정 뷰

API 설정 탭의 메인 UI 컴포넌트

Phase 2 마이그레이션으로 생성됨:
- 기존: ApiKeyManagerSecure (단일 클래스)
- 새로운: ApiSettingsView (DDD + MVP 패턴)

MVP 패턴의 View 역할을 담당하며, UI 렌더링만 처리합니다.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QMessageBox)
from PyQt6.QtCore import pyqtSignal

# Application Layer - Infrastructure 의존성 격리
from upbit_auto_trading.application.services.logging_application_service import IPresentationLogger
from ..widgets.api_credentials_widget import ApiCredentialsWidget
from ..widgets.api_connection_widget import ApiConnectionWidget
from ..widgets.api_permissions_widget import ApiPermissionsWidget

class ApiSettingsView(QWidget):
    """
    API 설정 뷰 - MVP 패턴의 View 역할

    UI 렌더링과 사용자 상호작용을 담당하며,
    비즈니스 로직은 Presenter에게 위임합니다.
    """

    # 시그널 정의 (외부 중계용)
    settings_changed = pyqtSignal()
    api_status_changed = pyqtSignal(bool)

    def __init__(self, parent=None, api_key_service=None, logging_service=None):
        super().__init__(parent)
        self.setObjectName("widget-api-settings-view")

        # 로깅 설정 - DI 패턴 적용
        if logging_service:
            self.logger = logging_service.get_component_logger("ApiSettingsView")
        else:
            raise ValueError("ApiSettingsView에 logging_service가 주입되지 않았습니다")

        # Presenter는 외부에서 주입받도록 설계 (MVP 패턴)
        self.presenter = None

        # 위젯들 생성 (로깅 서비스 전달)
        # DI 패턴: 동일한 logging_service를 모든 위젯에 전달

        self.credentials_widget = ApiCredentialsWidget(self, logging_service=logging_service)
        self.connection_widget = ApiConnectionWidget(self, logging_service=logging_service)
        self.permissions_widget = ApiPermissionsWidget(self, logging_service=logging_service)

        self._setup_ui()
        self._connect_signals()

        if self.logger:
            self.logger.info("✅ API 설정 뷰 초기화 완료")

        # Presenter 초기화는 외부에서 set_presenter() 호출로 처리

    def set_presenter(self, presenter):
        """Presenter 설정 (MVP 패턴)"""
        from upbit_auto_trading.presentation.presenters.settings.api_settings_presenter import ApiSettingsPresenter
        if not isinstance(presenter, ApiSettingsPresenter):
            raise TypeError("ApiSettingsPresenter 타입이어야 합니다")

        self.presenter = presenter
        if self.logger:
            self.logger.info("✅ API 설정 Presenter 연결 완료")

        # 초기 설정 로드
        self._load_initial_settings()

    def _setup_ui(self):
        """UI 설정"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # 위젯들 배치
        self.main_layout.addWidget(self.credentials_widget)
        self.main_layout.addWidget(self.permissions_widget)
        self.main_layout.addWidget(self.connection_widget)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        # 저장 버튼
        self.save_button = QPushButton("저장")
        self.save_button.setObjectName("button-save-api-keys")
        button_layout.addWidget(self.save_button)

        # 삭제 버튼
        self.delete_button = QPushButton("삭제")
        self.delete_button.setObjectName("button-delete-api-keys")
        button_layout.addWidget(self.delete_button)

        self.main_layout.addLayout(button_layout)
        self.main_layout.addStretch(1)

    def _connect_signals(self):
        """시그널 연결"""
        # 위젯 간 시그널 연결
        self.credentials_widget.input_changed.connect(self._on_input_changed)
        self.connection_widget.test_requested.connect(self._on_test_requested)
        self.permissions_widget.permissions_changed.connect(self._on_permissions_changed)

        # 버튼 시그널 연결
        self.save_button.clicked.connect(self._on_save_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)

        # 외부 시그널 중계
        self.connection_widget.connection_status_changed.connect(self.api_status_changed.emit)

    def _load_initial_settings(self):
        """초기 설정 로드"""
        if not self.presenter:
            return

        try:
            # Presenter에서 설정 로드
            settings = self.presenter.load_api_settings()

            # UI에 반영
            self.credentials_widget.set_credentials(
                settings['access_key'],
                settings['secret_key']
            )
            self.permissions_widget.set_trade_permission(settings['trade_permission'])

            # 버튼 상태 업데이트
            self._update_button_states()

            # 📌 저장된 키가 있으면 자동으로 연결 상태 확인
            if settings.get('has_saved_keys', False):
                if self.logger:
                    self.logger.info("💡 저장된 API 키 발견 - 자동 연결 상태 확인 시작")
                try:
                    # 조용한 모드로 연결 테스트 수행
                    test_success, test_message = self.presenter.test_api_connection(silent=True)
                    self.connection_widget.update_connection_status(test_success, test_message)

                    if test_success:
                        # 로그용으로 줄바꿈 문자 제거
                        log_message = test_message.replace('\n', ' ').replace('  ', ' ')
                        if self.logger:
                            self.logger.info(f"✅ 초기 연결 상태 확인 성공: {log_message}")
                    else:
                        # 로그용으로 줄바꿈 문자 제거
                        log_message = test_message.replace('\n', ' ').replace('  ', ' ')
                        if self.logger:
                            self.logger.warning(f"⚠️ 초기 연결 상태 확인 실패: {log_message}")

                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ 초기 연결 상태 확인 중 오류: {e}")
                    # 연결 테스트 실패해도 설정 로드는 계속 진행
                    self.connection_widget.update_connection_status(False, "연결 상태를 확인할 수 없습니다")
            else:
                # 저장된 키가 없으면 미연결 상태로 표시
                self.connection_widget.clear_status()

            if self.logger:
                self.logger.debug("초기 설정 로드 완료")

        except Exception as e:
            if self.logger:
                self.logger.error(f"초기 설정 로드 실패: {e}")
            self.show_error_message("설정 로드 오류", f"설정을 불러오는 중 오류가 발생했습니다: {str(e)}")

    def _on_input_changed(self, field_name: str, value: str):
        """입력 변경 시 처리"""
        if self.presenter:
            self.presenter.on_input_changed(field_name, value)
            self._update_button_states()

    def _on_test_requested(self):
        """테스트 요청 시 처리"""
        if not self.presenter:
            return

        try:
            success, message = self.presenter.test_api_connection()
            self.connection_widget.update_connection_status(success, message)

            if not success:
                self.show_error_message("연결 테스트 실패", message)
            else:
                self.show_info_message("연결 테스트 성공", message)

        except Exception as e:
            self.logger.error(f"API 테스트 중 오류: {e}")
            self.connection_widget.update_connection_status(False, str(e))

    def _on_permissions_changed(self, trade_permission: bool):
        """권한 변경 시 처리"""
        # 권한은 저장 시에만 반영되므로 여기서는 로깅만
        self.logger.debug(f"권한 변경: 거래 권한={trade_permission}")
        self.settings_changed.emit()

    def _on_save_clicked(self):
        """저장 버튼 클릭 시 처리"""
        if not self.presenter:
            return

        try:
            # 현재 입력값 수집
            access_key, secret_key = self.credentials_widget.get_credentials()
            trade_permission = self.permissions_widget.get_trade_permission()

            # Presenter를 통해 저장
            success, message = self.presenter.save_api_keys(access_key, secret_key, trade_permission)

            if success:
                self.show_info_message("저장 완료", message)

                # UI 업데이트 (마스킹된 키로 표시)
                settings = self.presenter.load_api_settings()
                self.credentials_widget.set_credentials(
                    settings['access_key'],
                    settings['secret_key']
                )

                # 버튼 상태 업데이트
                self._update_button_states()

                # 외부 시그널 발생
                self.settings_changed.emit()

                # 저장 후 자동 테스트 (조용한 모드)
                test_success, test_message = self.presenter.test_api_connection(silent=True)
                self.connection_widget.update_connection_status(test_success, test_message)

            else:
                if "취소" not in message:
                    self.show_error_message("저장 실패", message)

        except Exception as e:
            if self.logger:
                self.logger.error(f"저장 중 오류: {e}")
            self.show_error_message("저장 오류", f"저장 중 오류가 발생했습니다: {str(e)}")

    def _on_delete_clicked(self):
        """삭제 버튼 클릭 시 처리"""
        if not self.presenter:
            return

        try:
            success, message = self.presenter.delete_api_keys()

            if success:
                # UI 초기화
                self.credentials_widget.clear_credentials()
                self.permissions_widget.clear_permissions()
                self.connection_widget.clear_status()

                # 버튼 상태 업데이트
                self._update_button_states()

                # 외부 시그널 발생
                self.settings_changed.emit()
                self.api_status_changed.emit(False)

                if "삭제 완료" in message:
                    self.show_info_message("삭제 완료", message)
                elif "없습니다" in message:
                    self.show_info_message("알림", message)
            else:
                if "취소" not in message:
                    self.show_error_message("삭제 실패", message)

        except Exception as e:
            if self.logger:
                self.logger.error(f"삭제 중 오류: {e}")
            self.show_error_message("삭제 오류", f"삭제 중 오류가 발생했습니다: {str(e)}")

    def _update_button_states(self):
        """버튼 상태 업데이트"""
        if not self.presenter:
            return

        try:
            button_states = self.presenter.get_button_states()

            # 버튼 활성화 상태 설정
            self.save_button.setEnabled(button_states['save_enabled'])
            self.delete_button.setEnabled(button_states['delete_enabled'])

            # 연결 위젯 버튼 상태 설정
            self.connection_widget.set_test_button_enabled(button_states['test_enabled'])
            self.connection_widget.set_test_button_tooltip(self.presenter.get_test_button_tooltip())

        except Exception as e:
            if self.logger:
                self.logger.warning(f"버튼 상태 업데이트 실패: {e}")

    def show_info_message(self, title: str, message: str):
        """정보 메시지 표시"""
        QMessageBox.information(self, title, message)

    def show_error_message(self, title: str, message: str):
        """에러 메시지 표시"""
        QMessageBox.warning(self, title, message)

    def save_settings(self):
        """외부 호출용 저장 함수 (호환성)"""
        self._on_save_clicked()

    def load_settings(self):
        """외부 호출용 로드 함수 (호환성)"""
        self._load_initial_settings()
