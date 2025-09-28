"""
설정 화면 - MVP 패턴 + Infrastructure Layer v4.0 통합

DDD 아키텍처와 MVP 패턴을 적용한 설정 관리 UI입니다.
View는 순수하게 UI 표시만 담당하고, 모든 비즈니스 로직은 Presenter에서 처리합니다.
Infrastructure Layer Enhanced Logging v4.0 시스템과 완전히 통합되었습니다.

Phase 2 마이그레이션 적용:
- API 설정: api_settings/ 폴더 구조 (DDD + MVP 패턴)
- Database 설정: database_settings/ 폴더 구조 (Phase 1 완료)
- Environment 프로파일: environment_profile/ 폴더 구조 (TASK 4.3 완료)
"""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

# Dependency Injection
from dependency_injector.wiring import Provide, inject

# Infrastructure Layer Enhanced Logging v4.0
from upbit_auto_trading.infrastructure.logging import create_component_logger

class SettingsScreen(QWidget):
    """Settings Screen - MVP 패턴 View 구현

    ISettingsView 인터페이스를 구현하여 순수한 UI 역할만 담당합니다.
    모든 비즈니스 로직은 SettingsPresenter에서 처리됩니다.
    """

    # ISettingsView 시그널 구현
    settings_changed = pyqtSignal()
    theme_changed = pyqtSignal(str)  # theme_value
    api_status_changed = pyqtSignal(bool)  # connected
    db_status_changed = pyqtSignal(bool)   # connected
    save_all_requested = pyqtSignal()

    @inject
    def __init__(
        self,
        parent=None,
        settings_service=Provide["settings_service"],
        api_key_service=Provide["api_key_service"]
    ):
        """SettingsScreen 초기화 - @inject 패턴으로 DI 적용

        Args:
            parent: 부모 위젯
            settings_service: Application Service (@inject로 주입)
            api_key_service: API 키 서비스 (@inject로 주입)
        """
        super().__init__(parent)
        self.settings_service = settings_service
        self._api_key_service = api_key_service

        # Infrastructure Layer Enhanced Logging v4.0 초기화
        self.logger = create_component_logger("SettingsScreen")
        self.logger.info("🔧 SettingsScreen (MVP View + Infrastructure v4.0) 초기화 시작")

        # Infrastructure Layer 의존성 주입 확인
        self.app_context = None
        self.logger.debug("🔧 Application Context 확인 중...")

        # 메인 SettingsPresenter 초기화 (MVP 패턴)
        self._init_main_presenter()

        # 하위 위젯들 초기화
        self._init_sub_widgets()

        # UI 설정 (순수 UI 로직만)
        self.setup_ui()

        # View 내부 시그널 연결
        self.connect_view_signals()

        # Infrastructure Layer 통합 초기화
        self._init_infrastructure_integration()

        self.logger.info("✅ SettingsScreen (MVP View + Infrastructure v4.0) 초기화 완료")

    def _init_main_presenter(self):
        """메인 SettingsPresenter 초기화 (MVP 패턴)"""
        try:
            # Fail-Fast 패턴: 필수 의존성 검증
            if not self.settings_service:
                error_msg = "SettingsService가 주입되지 않았습니다. DI Container 설정을 확인하세요."
                self.logger.error(f"❌ 의존성 주입 실패: {error_msg}")
                self.show_status_message(error_msg, False)
                self.main_presenter = None
                return

            from upbit_auto_trading.presentation.presenters.settings_presenter import SettingsPresenter

            # 메인 Presenter 생성 및 연결
            self.main_presenter = SettingsPresenter(
                view=self,
                settings_service=self.settings_service
            )

            self.logger.info("✅ 메인 SettingsPresenter 연결 완료")

            # 초기 설정 로드
            try:
                self.main_presenter.load_initial_settings()
            except Exception as load_error:
                error_msg = f"초기 설정 로드 중 오류 발생: {str(load_error)}"
                self.logger.warning(f"⚠️ {error_msg}")
                self.show_status_message(error_msg, False)

        except Exception as e:
            error_msg = f"메인 SettingsPresenter 초기화 실패: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            self.show_status_message(error_msg, False)
            self.main_presenter = None

    def _init_infrastructure_integration(self):
        """Infrastructure Layer v4.0와의 통합 초기화"""
        self.logger.info("🔧 Infrastructure Layer 통합 초기화 시작")

        try:
            # 설정 화면 초기화 완료 (레거시 briefing/dashboard 시스템 제거됨)
            self.logger.info("✅ 설정 화면 초기화 완료")

        except Exception as e:
            self.logger.error(f"❌ 설정 화면 초기화 실패: {e}")

        self.logger.info("✅ Infrastructure Layer 통합 초기화 완료")

    def _init_sub_widgets(self):
        """하위 설정 위젯들 초기화 - Lazy Loading 적용 (첫 탭만 초기화)"""
        self.logger.debug("🔧 하위 설정 위젯들 lazy loading 초기화 시작")

        # 위젯 참조 초기화 (lazy loading용)
        self.api_key_manager = None
        self.database_settings = None
        self.environment_profile = None
        self.notification_settings = None
        self.ui_settings = None
        self.logging_management = None

        # Presenter 참조 초기화
        self.api_settings_presenter = None
        self.environment_profile_presenter = None
        self.logging_management_presenter = None

        # Fail-Fast 패턴: ApiKeyService 의존성 검증
        if self._api_key_service:
            self.logger.info(f"✅ ApiKeyService @inject 성공: {type(self._api_key_service).__name__}")
        else:
            error_msg = "ApiKeyService가 주입되지 않았습니다. API 키 관리 기능이 제한될 수 있습니다."
            self.logger.warning(f"⚠️ {error_msg}")
            # 사용자에게 경고하되 치명적이지 않으므로 계속 진행
            self.show_status_message(error_msg, False)

        # 첫 번째 탭(UI 설정)만 즉시 초기화
        self._initialize_ui_settings()

        self.logger.info("✅ 하위 설정 위젯들 lazy loading 초기화 완료 (첫 탭만 로드)")

    def _initialize_ui_settings(self):
        """UI 설정 위젯 초기화 (첫 탭 - 즉시 로드)"""
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.ui_settings import UISettingsView
            self.ui_settings = UISettingsView(self)
            self.logger.debug("🎨 UI 설정 위젯 즉시 초기화 완료")
        except Exception as e:
            self.logger.error(f"❌ UI 설정 위젯 초기화 실패: {e}")
            self.ui_settings = self._create_fallback_widget("UI 설정")

    def _initialize_api_settings(self):
        """API 설정 위젯 lazy 초기화"""
        if self.api_key_manager is not None:
            return  # 이미 초기화됨

        try:
            from upbit_auto_trading.ui.desktop.screens.settings.api_settings import ApiSettingsView
            from upbit_auto_trading.ui.desktop.screens.settings.api_settings.presenters.api_settings_presenter import (
                ApiSettingsPresenter
            )

            self.api_key_manager = ApiSettingsView(self)
            self.api_settings_presenter = ApiSettingsPresenter(self.api_key_manager)
            self.api_key_manager.set_presenter(self.api_settings_presenter)
            self.logger.info("✅ API 설정 위젯 lazy 초기화 완료")
        except Exception as e:
            import traceback
            self.logger.error(f"❌ API 설정 위젯 lazy 초기화 실패: {e}")
            self.logger.error(f"상세 오류: {traceback.format_exc()}")
            self.api_key_manager = self._create_fallback_widget("API 키 관리")
            self.logger.warning("⚠️ API 키 관리 폴백 위젯으로 대체")

    def _initialize_database_settings(self):
        """데이터베이스 설정 위젯 lazy 초기화"""
        if self.database_settings is not None:
            return  # 이미 초기화됨

        try:
            from upbit_auto_trading.ui.desktop.screens.settings.database_settings import DatabaseSettingsView
            from upbit_auto_trading.ui.desktop.screens.settings.database_settings.presenters import (
                database_settings_presenter
            )

            self.database_settings = DatabaseSettingsView(self)

            # DatabaseSettingsPresenter 연결 (MVP 패턴)
            try:
                self.database_settings_presenter = database_settings_presenter.DatabaseSettingsPresenter(
                    self.database_settings
                )
                if hasattr(self.database_settings, 'set_presenter'):
                    self.database_settings.set_presenter(self.database_settings_presenter)
                    self.logger.debug("✅ DatabaseSettingsPresenter 연결 완료")
                else:
                    self.database_settings.presenter = self.database_settings_presenter
                    self.logger.debug("✅ DatabaseSettingsPresenter 직접 할당 완료")
            except Exception as presenter_error:
                self.logger.warning(f"⚠️ DatabaseSettingsPresenter 연결 실패: {presenter_error}")

            self.logger.debug("💾 데이터베이스 설정 위젯 lazy 초기화 완료")
        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 설정 위젯 lazy 초기화 실패: {e}")
            self.database_settings = self._create_fallback_widget("데이터베이스 설정")

    def _initialize_environment_profile(self):
        """환경 프로파일 위젯 lazy 초기화 - 정지된 기능"""
        if self.environment_profile is not None:
            return  # 이미 초기화됨

        self.logger.warning("🚫 프로파일 기능 정지 - 간단한 안내 위젯으로 대체")
        self.environment_profile = self._create_disabled_profile_widget()

    def _initialize_logging_management(self):
        """로깅 관리 위젯 lazy 초기화"""
        if self.logging_management is not None:
            return  # 이미 초기화됨

        try:
            from upbit_auto_trading.ui.desktop.screens.settings.logging_management import LoggingManagementView
            # 긴 임포트를 여러 줄로 분할
            from upbit_auto_trading.ui.desktop.screens.settings.logging_management.presenters import (
                logging_management_presenter
            )

            self.logging_management = LoggingManagementView()
            self.logging_management_presenter = logging_management_presenter.LoggingManagementPresenter(
                self.logging_management
            )
            self.logger.debug("📝 로깅 관리 위젯 lazy 초기화 완료")
        except Exception as e:
            self.logger.error(f"❌ 로깅 관리 위젯 lazy 초기화 실패: {e}")
            self.logging_management = self._create_fallback_widget("로깅 관리")

    def _initialize_notification_settings(self):
        """알림 설정 위젯 lazy 초기화"""
        if self.notification_settings is not None:
            return  # 이미 초기화됨

        try:
            from upbit_auto_trading.ui.desktop.screens.settings.notification_settings import NotificationSettingsView
            self.notification_settings = NotificationSettingsView(self)
            self.logger.debug("🔔 알림 설정 위젯 lazy 초기화 완료")
        except Exception as e:
            self.logger.error(f"❌ 알림 설정 위젯 lazy 초기화 실패: {e}")
            self.notification_settings = self._create_fallback_widget("알림 설정")

    def _create_fallback_widget(self, name: str):
        """향상된 폴백 위젯 생성 - 복구 가이드 포함"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 오류 제목
        title = QLabel(f"⚠️ {name} 로드 실패")
        title.setObjectName("error-title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # 복구 안내
        guide = QLabel("""이 기능을 로드하는 중 오류가 발생했습니다.

다음 방법으로 해결을 시도해보세요:
1. 애플리케이션을 재시작해보세요
2. 로그를 확인하여 구체적인 오류를 파악하세요
3. 문제가 지속되면 개발팀에 문의하세요""")
        guide.setObjectName("error-guide")
        guide.setAlignment(Qt.AlignmentFlag.AlignCenter)
        guide.setWordWrap(True)
        layout.addWidget(guide)

        # 스페이서
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)

        return widget

    def _create_disabled_profile_widget(self):
        """정지된 프로파일 기능 안내 위젯"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 제목
        title = QLabel("⚠️ 프로파일 기능 정지")
        title.setObjectName("disabled-feature-title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # 설명
        desc = QLabel("""이 기능은 현재 정지되었습니다.

config/ 폴더 기반으로 재구현될 예정입니다.
자세한 내용은 docs/PROFILE_FEATURE_DISABLED_NOTICE.md를 참조하세요.""")
        desc.setObjectName("disabled-feature-description")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 스페이서
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)

        return widget

    def setup_ui(self) -> None:
        """UI 컴포넌트 설정 (순수 UI 로직만)"""
        self.logger.debug("🎨 UI 컴포넌트 설정 시작")

        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        self.logger.debug("📐 메인 레이아웃 생성 완료")

        # 제목
        title_label = QLabel("설정")
        title_label.setObjectName("settings-title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        main_layout.addWidget(title_label)
        self.logger.debug("🏷️ 제목 레이블 생성 완료")

        # 설명
        description_label = QLabel("애플리케이션 설정을 관리합니다.")
        description_label.setObjectName("settings-description")
        description_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(description_label)
        self.logger.debug("📄 설명 레이블 생성 완료")

        # 구분선
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #cccccc;")
        main_layout.addWidget(line)
        self.logger.debug("📏 구분선 생성 완료")

        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("settings-tab-widget")
        self.logger.debug("📂 탭 위젯 생성 시작")

        # 탭 추가 (위젯은 lazy loading으로 나중에 생성)
        self.tab_widget.addTab(QWidget(), "UI 설정")      # index 0
        self.tab_widget.addTab(QWidget(), "API 키")       # index 1
        self.tab_widget.addTab(QWidget(), "데이터베이스")   # index 2
        self.tab_widget.addTab(QWidget(), "프로파일")     # index 3
        self.tab_widget.addTab(QWidget(), "로깅 관리")     # index 4
        self.tab_widget.addTab(QWidget(), "알림")         # index 5

        # 첫 번째 탭에 실제 UI 설정 위젯 배치
        if self.ui_settings:
            self.tab_widget.removeTab(0)
            self.tab_widget.insertTab(0, self.ui_settings, "UI 설정")
            self.tab_widget.setCurrentIndex(0)

        main_layout.addWidget(self.tab_widget)
        self.logger.info(f"📂 탭 위젯 완성: {self.tab_widget.count()}개 탭 (lazy loading)")

        # 탭 변경 시그널 연결 - lazy loading
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.logger.debug("🔄 탭 변경 시그널 연결 완료 (lazy loading)")

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        # 공간 추가
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        button_layout.addItem(spacer)

        main_layout.addLayout(button_layout)
        self.logger.info("✅ UI 컴포넌트 설정 완료 (lazy loading 지원)")

        # 초기화 완료 플래그 설정
        self._initial_tab_setup_done = True
        self.logger.debug("🚀 초기 탭 설정 완료 - lazy loading 활성화")

    def connect_view_signals(self) -> None:
        """View 내부 시그널 연결 (Presenter와 연결은 별도)"""
        # 하위 위젯들의 시그널을 상위로 중계
        try:
            # UI Settings의 시그널을 상위로 중계 (향후 구현 예정)
            self.logger.info("✅ UI Settings 시그널 연결 준비 완료 (직접 MVP 구조)")

            # API Key Manager의 상태 변경 시그널을 상위로 중계
            if self.api_key_manager is not None:
                try:
                    from upbit_auto_trading.ui.desktop.screens.settings.api_settings import ApiSettingsView
                    if isinstance(self.api_key_manager, ApiSettingsView):
                        self.api_key_manager.api_status_changed.connect(self._on_api_settings_status_changed)
                        self.logger.info("✅ ApiSettingsView api_status_changed 시그널 중계 연결 완료")
                    else:
                        self.logger.info(f"ℹ️ API 키 관리자 타입: {type(self.api_key_manager).__name__} (폴백 위젯 또는 대체 구현)")
                        # 폴백 위젯이라도 시그널이 있으면 연결 시도
                        if hasattr(self.api_key_manager, 'api_status_changed'):
                            self.api_key_manager.api_status_changed.connect(self._on_api_settings_status_changed)
                            self.logger.info("✅ 폴백 위젯 api_status_changed 시그널 연결 완료")
                except Exception as e:
                    self.logger.warning(f"⚠️ API 키 관리자 시그널 연결 실패: {e}")
            else:
                self.logger.warning("⚠️ API 키 관리자가 초기화되지 않음")

        except Exception as e:
            self.logger.error(f"❌ 하위 위젯 시그널 중계 연결 실패: {e}")

    def _on_ui_settings_theme_changed(self, theme_value: str):
        """UISettingsManager에서 테마 변경 시그널을 받아서 Presenter로 전달"""
        self.logger.info(f"🔄 UISettingsManager에서 테마 변경 시그널 수신: {theme_value}")

        # MVP 패턴: Presenter를 통해 비즈니스 로직 처리
        if hasattr(self, 'main_presenter') and self.main_presenter:
            self.main_presenter.handle_theme_changed(theme_value)

        # View 계층 시그널 중계 (상위 컴포넌트용)
        self.theme_changed.emit(theme_value)

    def _on_ui_settings_settings_changed(self):
        """UISettingsManager에서 설정 변경 시그널을 받아서 Presenter로 전달"""
        self.logger.debug("🔄 UISettingsManager에서 설정 변경 시그널 수신")

        # MVP 패턴: Presenter를 통해 비즈니스 로직 처리
        if hasattr(self, 'main_presenter') and self.main_presenter:
            self.main_presenter.handle_settings_changed()

        # View 계층 시그널 중계 (상위 컴포넌트용)
        self.settings_changed.emit()

    def _on_api_settings_status_changed(self, connected: bool):
        """ApiSettingsView에서 API 상태 변경 시그널을 받아서 Presenter로 전달"""
        self.logger.info(f"🔄 ApiSettingsView에서 API 상태 변경 시그널 수신: {'연결됨' if connected else '연결 끊김'}")

        # MVP 패턴: Presenter를 통해 비즈니스 로직 처리
        if hasattr(self, 'main_presenter') and self.main_presenter:
            self.main_presenter.handle_api_status_changed(connected)

        # View 계층 시그널 중계 (상위 컴포넌트용)
        self.api_status_changed.emit(connected)

    # ISettingsView 인터페이스 구현 메서드들

    def show_loading_state(self, loading: bool) -> None:
        """로딩 상태 표시/숨김 (배치 저장 방식에서는 각 탭에서 자체 관리)"""
        # 배치 저장 방식에서는 각 탭의 저장 버튼에서 자체적으로 로딩 상태 관리
        self.logger.debug(f"📊 로딩 상태 변경: {loading}")

    def show_save_success_message(self) -> None:
        """저장 성공 메시지 표시"""
        QMessageBox.information(self, "저장 완료", "모든 설정이 성공적으로 저장되었습니다.")

    def show_save_error_message(self, error: str) -> None:
        """저장 실패 메시지 표시"""
        QMessageBox.warning(self, "저장 실패", f"설정 저장 중 오류가 발생했습니다:\n{error}")

    def show_status_message(self, message: str, success: bool = True) -> None:
        """상태 메시지 표시"""
        if success:
            # 성공 메시지는 임시로 제목 표시 (실제로는 상태바 등에 표시)
            print(f"✅ {message}")
        else:
            # 실패 메시지는 경고창으로 표시
            QMessageBox.warning(self, "알림", message)

    def get_current_tab_index(self) -> int:
        """현재 선택된 탭 인덱스"""
        return self.tab_widget.currentIndex()

    def set_current_tab_index(self, index: int) -> None:
        """특정 탭으로 이동"""
        if 0 <= index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(index)

    def _on_tab_changed(self, index: int) -> None:
        """탭 변경 시 lazy loading 및 자동 새로고침 - 재귀 방지"""
        try:
            # 재귀 호출 방지 플래그 확인
            if getattr(self, '_tab_changing', False):
                return

            tab_names = ["UI 설정", "API 키", "데이터베이스", "프로파일", "로깅 관리", "알림"]
            tab_name = tab_names[index] if 0 <= index < len(tab_names) else f"탭 {index}"

            self.logger.debug(f"🔄 탭 변경 감지: {tab_name} (인덱스: {index})")

            # 초기화 시에는 처리 건너뛰기
            if not hasattr(self, '_initial_tab_setup_done'):
                self.logger.debug("🚀 초기 탭 설정 중 - 처리 건너뛰기")
                return

            # 재귀 호출 방지 플래그 설정
            self._tab_changing = True

            try:
                # 각 탭별 lazy loading 및 자동 새로고침
                if index == 0:  # UI 설정 탭 (이미 로드됨)
                    if self.ui_settings and hasattr(self.ui_settings, 'load_settings'):
                        try:
                            self.ui_settings.load_settings()  # type: ignore
                            self.logger.debug("✅ UI 설정 새로고침 완료")
                        except Exception as e:
                            self.logger.warning(f"⚠️ UI 설정 새로고침 실패: {e}")

                elif index == 1:  # API 키 탭
                    self._initialize_api_settings()
                    if self.api_key_manager and hasattr(self.api_key_manager, 'load_settings'):
                        # 시그널 일시 차단하고 탭 위젯 교체
                        self.tab_widget.currentChanged.disconnect()
                        try:
                            self.tab_widget.removeTab(1)
                            self.tab_widget.insertTab(1, self.api_key_manager, "API 키")
                            self.tab_widget.setCurrentIndex(1)
                        finally:
                            self.tab_widget.currentChanged.connect(self._on_tab_changed)

                        try:
                            self.api_key_manager.load_settings()  # type: ignore
                            self.logger.debug("✅ API 키 lazy 로드 및 새로고침 완료")
                        except Exception as e:
                            self.logger.warning(f"⚠️ API 키 새로고침 실패: {e}")

                elif index == 2:  # 데이터베이스 탭
                    self._initialize_database_settings()
                    if self.database_settings:
                        # 시그널 일시 차단하고 탭 위젯 교체
                        self.tab_widget.currentChanged.disconnect()
                        try:
                            self.tab_widget.removeTab(2)
                            self.tab_widget.insertTab(2, self.database_settings, "데이터베이스")
                            self.tab_widget.setCurrentIndex(2)
                        finally:
                            self.tab_widget.currentChanged.connect(self._on_tab_changed)

                        # 캐싱으로 성능 최적화 (5분 이내 재조회 방지)
                        current_time = time.time()
                        last_refresh = getattr(self, '_db_last_refresh_time', 0)
                        if current_time - last_refresh > 300:
                            try:
                                presenter = getattr(self.database_settings, 'presenter', None)
                                if presenter and hasattr(presenter, 'refresh_status'):
                                    presenter.refresh_status()
                                    self._db_last_refresh_time = current_time
                                    self.logger.debug("✅ 데이터베이스 lazy 로드 및 새로고침 완료")
                                else:
                                    self.logger.debug("✅ 데이터베이스 lazy 로드 완료 (새로고침 스킵)")
                            except Exception as e:
                                self.logger.warning(f"⚠️ 데이터베이스 새로고침 실패: {e}")
                        else:
                            self.logger.debug("⏭️ 데이터베이스 캐시 사용 (5분 이내)")

                elif index == 3:  # 프로파일 탭 (정지된 기능)
                    self._initialize_environment_profile()
                    if self.environment_profile:
                        # 시그널 일시 차단하고 탭 위젯 교체
                        self.tab_widget.currentChanged.disconnect()
                        try:
                            self.tab_widget.removeTab(3)
                            self.tab_widget.insertTab(3, self.environment_profile, "프로파일")
                            self.tab_widget.setCurrentIndex(3)
                        finally:
                            self.tab_widget.currentChanged.connect(self._on_tab_changed)
                        self.logger.debug("✅ 프로파일 탭 lazy 로드 완료 (정지된 기능)")

                elif index == 4:  # 로깅 관리 탭
                    self._initialize_logging_management()
                    if self.logging_management:
                        # 시그널 일시 차단하고 탭 위젯 교체
                        self.tab_widget.currentChanged.disconnect()
                        try:
                            self.tab_widget.removeTab(4)
                            self.tab_widget.insertTab(4, self.logging_management, "로깅 관리")
                            self.tab_widget.setCurrentIndex(4)
                        finally:
                            self.tab_widget.currentChanged.connect(self._on_tab_changed)

                        # 캐싱으로 성능 최적화 (1분 이내 재조회 방지)
                        current_time = time.time()
                        last_refresh = getattr(self, '_logging_last_refresh_time', 0)
                        if current_time - last_refresh > 60:
                            try:
                                presenter = getattr(self, 'logging_management_presenter', None)
                                if presenter and hasattr(presenter, 'refresh'):
                                    presenter.refresh()
                                    self._logging_last_refresh_time = current_time
                                    self.logger.debug("✅ 로깅 관리 lazy 로드 및 새로고침 완료")
                                else:
                                    self.logger.debug("✅ 로깅 관리 lazy 로드 완료 (새로고침 스킵)")
                            except Exception as e:
                                self.logger.warning(f"⚠️ 로깅 관리 새로고침 실패: {e}")
                        else:
                            self.logger.debug("⏭️ 로깅 관리 캐시 사용 (1분 이내)")

                elif index == 5:  # 알림 탭
                    self._initialize_notification_settings()
                    if self.notification_settings:
                        # 시그널 일시 차단하고 탭 위젯 교체
                        self.tab_widget.currentChanged.disconnect()
                        try:
                            self.tab_widget.removeTab(5)
                            self.tab_widget.insertTab(5, self.notification_settings, "알림")
                            self.tab_widget.setCurrentIndex(5)
                        finally:
                            self.tab_widget.currentChanged.connect(self._on_tab_changed)

                        # 캐싱으로 성능 최적화 (5분 이내 재조회 방지)
                        current_time = time.time()
                        last_refresh = getattr(self, '_notification_last_refresh_time', 0)
                        if current_time - last_refresh > 300:
                            try:
                                if hasattr(self.notification_settings, 'load_settings'):
                                    self.notification_settings.load_settings()  # type: ignore
                                    self._notification_last_refresh_time = current_time
                                    self.logger.debug("✅ 알림 설정 lazy 로드 및 새로고침 완료")
                                else:
                                    self.logger.debug("✅ 알림 설정 lazy 로드 완료 (새로고침 스킵)")
                            except Exception as e:
                                self.logger.warning(f"⚠️ 알림 설정 새로고침 실패: {e}")
                        else:
                            self.logger.debug("⏭️ 알림 설정 캐시 사용 (5분 이내)")

                self.logger.info(f"✅ {tab_name} 탭 lazy loading 및 새로고침 완료")

            finally:
                # 재귀 호출 방지 플래그 해제
                self._tab_changing = False

        except Exception as e:
            # 재귀 호출 방지 플래그 해제
            self._tab_changing = False
            self.logger.warning(f"⚠️ 탭 변경 시 lazy loading 실패: {e}")    # MVP 패턴 준수 - Presenter를 통한 처리

    def save_all_settings(self):
        """모든 설정 저장 - Presenter를 통해 처리"""
        if hasattr(self, 'main_presenter') and self.main_presenter:
            self.main_presenter.handle_save_all_settings()
        else:
            # 폴백: 직접 시그널 발생
            self.save_all_requested.emit()

    def load_settings(self):
        """설정 로드 - 재귀 방지된 View 레벨 처리"""
        # 🚨 재귀 방지: Presenter.load_initial_settings()를 호출하지 않음
        # View 레벨에서 각 탭의 설정만 새로고침
        try:
            current_tab_index = self.get_current_tab_index()
            tab_names = ["UI 설정", "API 키", "데이터베이스", "프로파일", "로깅 관리", "알림"]
            current_tab_name = tab_names[current_tab_index] if 0 <= current_tab_index < len(tab_names) else "알 수 없음"

            self.logger.debug(f"📋 설정 로드 (View 레벨) - 현재 탭: {current_tab_name}")

            # 현재 활성화된 탭의 설정만 새로고침 (재귀 없는 안전한 방식)
            self._refresh_current_tab_safely()

        except Exception as e:
            self.logger.warning(f"⚠️ 설정 로드 중 오류: {e}")

    def _refresh_current_tab_safely(self):
        """현재 탭을 안전하게 새로고침 (재귀 없음)"""
        current_index = self.get_current_tab_index()

        # 각 탭별로 안전한 새로고침 (Presenter 호출 없이)
        if current_index == 0 and self.ui_settings:  # UI 설정
            self.logger.debug("🔄 UI 설정 탭 안전한 새로고침")
        elif current_index == 1 and self.api_key_manager:  # API 키
            self.logger.debug("🔄 API 키 탭 안전한 새로고침")
        elif current_index == 2 and self.database_settings:  # 데이터베이스
            self.logger.debug("� 데이터베이스 탭 안전한 새로고침")
        # 기타 탭들...
        else:
            self.logger.debug(f"🔄 탭 {current_index} 안전한 새로고침")
