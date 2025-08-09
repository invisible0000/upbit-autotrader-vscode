"""
설정 화면 - MVP 패턴 + Infrastructure Layer v4.0 통합

DDD 아키텍처와 MVP 패턴을 적용한 설정 관리 UI입니다.
View는 순수하게 UI 표시만        try:
            # 실제 설정 위젯들 import 및 생성
            from upbit_auto_trading.ui.desktop.screens.settings.api_key_settings_view import ApiKeyManagerSecure
            from upbit_auto_trading.ui.desktop.screens.settings.database_settings_view import DatabaseSettingsView
            from upbit_auto_trading.ui.desktop.screens.settings.notification_settings_view import NotificationSettings
            from upbit_auto_trading.ui.desktop.screens.settings.ui_settings_view import UISettings

            self.logger.info("📦 설정 위젯 모듈들 import 성공 (DDD Database Widget 적용)")든 비즈니스 로직은 Presenter에서 처리합니다.
Infrastructure Layer Enhanced Logging v4.0 시스템과 완전히 통합되었습니다.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

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

    def __init__(self, settings_service=None, parent=None):
        """SettingsScreen 초기화 - Infrastructure Layer v4.0 통합

        Args:
            settings_service: Application Service (MVP Container에서 주입)
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.settings_service = settings_service

        # Infrastructure Layer Enhanced Logging v4.0 초기화
        self.logger = create_component_logger("SettingsScreen")
        self.logger.info("🔧 SettingsScreen (MVP View + Infrastructure v4.0) 초기화 시작")

        # Infrastructure Layer 의존성 주입 확인
        self.app_context = None
        self.logger.debug("🔧 Application Context 확인 중...")

        # 하위 위젯들 초기화
        self._init_sub_widgets()

        # UI 설정 (순수 UI 로직만)
        self.setup_ui()

        # View 내부 시그널 연결
        self.connect_view_signals()

        # Infrastructure Layer 통합 초기화
        self._init_infrastructure_integration()

        self.logger.info("✅ SettingsScreen (MVP View + Infrastructure v4.0) 초기화 완료")

    def _init_infrastructure_integration(self):
        """Infrastructure Layer v4.0와의 통합 초기화"""
        self.logger.info("🔧 Infrastructure Layer 통합 초기화 시작")

        try:
            # SystemStatusTracker로 컴포넌트 상태 보고
            try:
                from upbit_auto_trading.infrastructure.logging.briefing.status_tracker import SystemStatusTracker
                tracker = SystemStatusTracker()
                tracker.update_component_status(
                    "SettingsScreen",
                    "OK",
                    "설정 화면 초기화 완료",
                    tabs_count=4,
                    widgets_loaded=True
                )
                self.logger.info("📊 SystemStatusTracker에 상태 보고 완료")
            except ImportError as e:
                self.logger.debug(f"📊 SystemStatusTracker 모듈 없음: {e}")
            # DashboardService로 실시간 대시보드 업데이트 (선택적)
            try:
                from upbit_auto_trading.infrastructure.logging.dashboard.dashboard_service import DashboardService
                dashboard_service = DashboardService()
                dashboard_data = dashboard_service.update_dashboard([
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - SettingsScreen - INFO - 설정 화면 초기화 완료"
                ])
                self.logger.info("📊 DashboardService 업데이트 완료")
                self.logger.debug(f"📈 시스템 상태: {dashboard_data.system_health}")
            except ImportError as e:
                self.logger.debug(f"📊 DashboardService 모듈 없음: {e}")
            except Exception as e:
                self.logger.warning(f"⚠️ DashboardService 업데이트 실패: {e}")

        except Exception as e:
            self.logger.error(f"❌ Infrastructure Layer 통합 초기화 실패: {e}")

        self.logger.info("✅ Infrastructure Layer 통합 초기화 완료")

    def _init_sub_widgets(self):
        """하위 설정 위젯들 초기화"""
        self.logger.debug("🔧 하위 설정 위젯들 초기화 시작")

        try:
            # 실제 설정 위젯들 import 및 생성
            from upbit_auto_trading.ui.desktop.screens.settings.api_key_settings_view import ApiKeyManagerSecure
            from upbit_auto_trading.ui.desktop.screens.settings.database_settings_view import DatabaseSettingsView
            from upbit_auto_trading.ui.desktop.screens.settings.notification_settings_view import NotificationSettings
            from upbit_auto_trading.ui.desktop.screens.settings.ui_settings_view import UISettings

            self.logger.info("📦 설정 위젯 모듈들 import 성공 (DDD Database Widget 적용)")

            # DI 컨테이너에서 ApiKeyService 가져오기
            api_key_service = None
            try:
                # MainWindow에서 DI Container 가져오기 (getattr 사용으로 안전하게)
                main_window = self.parent()
                self.logger.debug(f"🔍 현재 parent: {type(main_window).__name__ if main_window else 'None'}")
                self.logger.debug(f"🔍 현재 parent 주소: {id(main_window) if main_window else 'None'}")

                # parent 체인을 따라 MainWindow 찾기 (상세 로깅)
                search_count = 0
                original_parent = main_window
                while main_window and not hasattr(main_window, 'di_container') and search_count < 5:
                    self.logger.debug(f"🔍 부모 탐색 중 [{search_count}]: {type(main_window).__name__} (id: {id(main_window)})")
                    main_window = main_window.parent()
                    search_count += 1

                self.logger.debug(f"🔍 최종 main_window: {type(main_window).__name__ if main_window else 'None'}")
                success_msg = '성공' if main_window and hasattr(main_window, 'di_container') else '실패'
                self.logger.debug(f"🔍 부모 탐색 결과: {search_count}번 탐색 후 {success_msg}")

                if main_window and hasattr(main_window, 'di_container'):
                    di_container = getattr(main_window, 'di_container', None)
                    self.logger.debug(f"🔍 DI Container 발견: {type(di_container).__name__ if di_container else 'None'}")

                    if di_container:
                        from upbit_auto_trading.infrastructure.services.api_key_service import IApiKeyService
                        api_key_service = di_container.resolve(IApiKeyService)
                        self.logger.info(f"✅ ApiKeyService 주입 성공: {type(api_key_service).__name__}")
                    else:
                        self.logger.warning("⚠️ DI Container가 None입니다")
                else:
                    self.logger.warning("⚠️ MainWindow의 DI Container를 찾을 수 없음")
                    # 디버깅: 부모 체인 전체 출력
                    parent_chain = []
                    current = original_parent
                    depth = 0
                    while current and depth < 10:
                        has_di = hasattr(current, 'di_container')
                        parent_info = f"[{depth}] {type(current).__name__} (id: {id(current)}, hasattr di_container: {has_di})"
                        parent_chain.append(parent_info)
                        current = current.parent()
                        depth += 1
                    self.logger.debug(f"🔍 부모 체인 상세: {' -> '.join(parent_chain) if parent_chain else 'Empty'}")
            except Exception as e:
                self.logger.error(f"❌ ApiKeyService 해결 중 오류: {e}")
                import traceback
                self.logger.error(f"❌ 스택 트레이스: {traceback.format_exc()}")

            # 실제 위젯 인스턴스 생성 (Infrastructure Layer 기반)
            self.api_key_manager = ApiKeyManagerSecure(self, api_key_service=api_key_service)
            self.logger.debug("🔑 API 키 관리자 생성 완료")

            # 데이터베이스 설정 View 사용 (MVP 패턴 이미 적용됨)
            self.database_settings = DatabaseSettingsView(self)
            self.logger.debug("💾 데이터베이스 설정 생성 완료 (DatabaseSettingsView - MVP 적용)")

            self.notification_settings = NotificationSettings(self)
            self.logger.debug("🔔 알림 설정 생성 완료")

            # UISettings에 SettingsService 의존성 주입
            if self.settings_service is None:
                self.logger.error("❌ SettingsScreen에서 SettingsService가 None - MainWindow에서 주입 실패")
            else:
                self.logger.info(f"✅ SettingsScreen에서 SettingsService 확인됨: {type(self.settings_service).__name__}")

            self.ui_settings = UISettings(self, settings_service=self.settings_service)
            self.logger.debug("🎨 UI 설정 생성 완료 (SettingsService 주입)")

            self.logger.info("✅ 모든 실제 설정 위젯들 생성 완료 (Infrastructure Layer 연동)")

        except Exception as e:
            self.logger.error(f"❌ 설정 위젯 생성 실패: {e}")
            self.logger.warning("⚠️ 더미 위젯으로 폴백")

            # 폴백: 간단한 더미 위젯들로 대체
            self.api_key_manager = QWidget()
            self.database_settings = QWidget()
            self.notification_settings = QWidget()
            self.ui_settings = QWidget()

            # 각 위젯에 임시 레이블 추가
            widgets_info = [
                (self.api_key_manager, "API 키 관리"),
                (self.database_settings, "데이터베이스 설정"),
                (self.notification_settings, "알림 설정"),
                (self.ui_settings, "UI 설정")
            ]

            for widget, name in widgets_info:
                layout = QVBoxLayout(widget)
                label = QLabel(f"{name} (개발 중)")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(label)
                self.logger.debug(f"📝 {name} 위젯 생성 완료")

        self.logger.info("✅ 하위 설정 위젯들 초기화 완료")

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

        # UI 설정 탭 (첫 번째 탭으로 배치)
        self.tab_widget.addTab(self.ui_settings, "UI 설정")
        self.logger.debug("📋 UI 설정 탭 추가 완료")

        # API 키 탭
        self.tab_widget.addTab(self.api_key_manager, "API 키")
        self.logger.debug("🔑 API 키 탭 추가 완료")

        # 데이터베이스 탭
        self.tab_widget.addTab(self.database_settings, "데이터베이스")
        self.logger.debug("💾 데이터베이스 탭 추가 완료")

        # 알림 탭
        self.tab_widget.addTab(self.notification_settings, "알림")
        self.logger.debug("🔔 알림 탭 추가 완료")

        main_layout.addWidget(self.tab_widget)
        self.logger.info(f"📂 탭 위젯 완성: {self.tab_widget.count()}개 탭")

        # 탭 변경 시그널 연결 - 자동 새로고침
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.logger.debug("🔄 탭 변경 시그널 연결 완료")

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        # 공간 추가
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        button_layout.addItem(spacer)

        # 저장 버튼 제거 (UISettings에서 자체 처리하므로 불필요)
        # 참고: 배치 저장 방식으로 변경됨에 따라 각 탭에서 자체 저장 버튼 관리
        self.logger.debug("💾 설정 화면 하단 저장 버튼 제거 (탭별 자체 관리)")

        main_layout.addLayout(button_layout)
        self.logger.info("✅ UI 컴포넌트 설정 완료")

    def connect_view_signals(self) -> None:
        """View 내부 시그널 연결 (Presenter와 연결은 별도)"""
        # 하위 위젯들의 시그널을 상위로 중계
        try:
            # UI Settings의 테마 변경 시그널을 상위로 중계
            from upbit_auto_trading.ui.desktop.screens.settings.ui_settings_view import UISettings
            if isinstance(self.ui_settings, UISettings):
                self.ui_settings.theme_changed.connect(self._on_ui_settings_theme_changed)
                self.logger.info("✅ UISettings theme_changed 시그널 중계 연결 완료")

                self.ui_settings.settings_changed.connect(self._on_ui_settings_settings_changed)
                self.logger.info("✅ UISettings settings_changed 시그널 중계 연결 완료")
            else:
                self.logger.warning("⚠️ UISettings가 UISettings 타입이 아닙니다 (폴백 위젯 사용 중)")

            # API Key Manager의 상태 변경 시그널을 상위로 중계
            from upbit_auto_trading.ui.desktop.screens.settings.api_key_settings_view import ApiKeyManagerSecure
            if isinstance(self.api_key_manager, ApiKeyManagerSecure):
                self.api_key_manager.api_status_changed.connect(self._on_api_key_manager_status_changed)
                self.logger.info("✅ ApiKeyManagerSecure api_status_changed 시그널 중계 연결 완료")
            else:
                self.logger.warning("⚠️ ApiKeyManagerSecure가 올바른 타입이 아닙니다 (폴백 위젯 사용 중)")

        except Exception as e:
            self.logger.error(f"❌ 하위 위젯 시그널 중계 연결 실패: {e}")

    def _on_ui_settings_theme_changed(self, theme_value: str):
        """UISettings에서 테마 변경 시그널을 받아서 상위로 중계"""
        self.logger.info(f"🔄 UISettings에서 테마 변경 시그널 수신하여 중계: {theme_value}")
        self.theme_changed.emit(theme_value)

    def _on_ui_settings_settings_changed(self):
        """UISettings에서 설정 변경 시그널을 받아서 상위로 중계"""
        self.logger.debug("🔄 UISettings에서 설정 변경 시그널 수신하여 중계")
        self.settings_changed.emit()

    def _on_api_key_manager_status_changed(self, connected: bool):
        """ApiKeyManagerSecure에서 API 상태 변경 시그널을 받아서 상위로 중계"""
        self.logger.info(f"🔄 ApiKeyManagerSecure에서 API 상태 변경 시그널 수신하여 중계: {'연결됨' if connected else '연결 끊김'}")
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
        """탭 변경 시 자동 새로고침 - UX 편의 기능"""
        try:
            tab_names = ["UI 설정", "API 키", "데이터베이스", "알림"]
            tab_name = tab_names[index] if 0 <= index < len(tab_names) else f"탭 {index}"

            self.logger.debug(f"🔄 탭 변경 감지: {tab_name} (인덱스: {index})")

            # 각 탭별 자동 새로고침 처리
            if index == 0:  # UI 설정 탭
                self.logger.debug("🎨 UI 설정 탭 선택 - 자동 새로고침 시작")
                ui_settings = getattr(self, 'ui_settings', None)
                if ui_settings and hasattr(ui_settings, 'load_settings'):
                    try:
                        ui_settings.load_settings()
                        self.logger.debug("✅ UI 설정 상태 자동 새로고침 완료")
                    except Exception as e:
                        self.logger.warning(f"⚠️ UI 설정 새로고침 실패: {e}")

            elif index == 1:  # API 키 탭
                self.logger.debug("🔑 API 키 탭 선택 - 자동 새로고침 시작")
                api_key_manager = getattr(self, 'api_key_manager', None)
                if api_key_manager and hasattr(api_key_manager, 'load_settings'):
                    try:
                        api_key_manager.load_settings()
                        self.logger.debug("✅ API 키 상태 자동 새로고침 완료")
                    except Exception as e:
                        self.logger.warning(f"⚠️ API 키 새로고침 실패: {e}")

            elif index == 2:  # 데이터베이스 탭
                self.logger.debug("� 데이터베이스 탭 선택 - 자동 새로고침 시작")
                if hasattr(self, 'database_settings'):
                    try:
                        # Presenter를 통한 새로고침 (MVP 패턴)
                        presenter = getattr(self.database_settings, 'presenter', None)
                        if presenter and hasattr(presenter, 'refresh_status'):
                            presenter.refresh_status()
                            self.logger.debug("✅ 데이터베이스 상태 자동 새로고침 완료 (Presenter)")
                        # View 직접 새로고침 (폴백)
                        elif hasattr(self.database_settings, 'refresh_display'):
                            getattr(self.database_settings, 'refresh_display')()
                            self.logger.debug("✅ 데이터베이스 상태 자동 새로고침 완료 (View)")
                    except Exception as e:
                        self.logger.warning(f"⚠️ 데이터베이스 새로고침 실패: {e}")

            elif index == 3:  # 알림 탭
                self.logger.debug("🔔 알림 탭 선택 - 자동 새로고침 시작")
                notification_settings = getattr(self, 'notification_settings', None)
                if notification_settings and hasattr(notification_settings, 'load_settings'):
                    try:
                        getattr(notification_settings, 'load_settings')()
                        self.logger.debug("✅ 알림 설정 자동 새로고침 완료")
                    except Exception as e:
                        self.logger.warning(f"⚠️ 알림 설정 새로고침 실패: {e}")

            self.logger.info(f"✅ {tab_name} 탭 자동 새로고침 처리 완료")

        except Exception as e:
            self.logger.warning(f"⚠️ 탭 변경 시 자동 새로고침 실패: {e}")

    # 기존 호환성을 위한 메서드들 (Presenter가 호출)

    def save_all_settings(self):
        """모든 설정 저장 - save_all_requested 시그널 발생"""
        self.save_all_requested.emit()

    def load_settings(self):
        """설정 로드 - 간단한 버전에서는 아무것도 하지 않음"""
        print("📋 설정 로드 (간단한 버전)")
