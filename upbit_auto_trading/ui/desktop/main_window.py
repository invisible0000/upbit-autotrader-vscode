"""
메인 윈도우 모듈
"""
import traceback
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel
)
from PyQt6.QtCore import Qt

# Dependency Injection
from dependency_injector.wiring import Provide, inject

# Application Layer 서비스 - MVP 패턴으로 Presenter에서 처리

# Presenter Layer - DI Container를 통해 주입받음

# 공통 위젯 임포트
from upbit_auto_trading.ui.desktop.common.widgets.status_bar import StatusBar
from upbit_auto_trading.ui.desktop.common.widgets.navigation_bar import NavigationBar

# 화면 임포트 (임시로 더미 클래스 사용)


def create_placeholder_screen(name):
    """임시 화면 생성"""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    label = QLabel(f"{name} 화면 (개발 중)")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label)
    return widget


try:
    from upbit_auto_trading.ui.desktop.screens.dashboard.dashboard_screen import DashboardScreen
except ImportError:
    def DashboardScreen():
        return create_placeholder_screen("대시보드")


try:
    from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen
except ImportError:
    def ChartViewScreen():
        return create_placeholder_screen("차트 뷰")


try:
    from upbit_auto_trading.ui.desktop.screens.settings.settings_screen import SettingsScreen
except ImportError:
    def SettingsScreen():
        return create_placeholder_screen("설정")


try:
    from upbit_auto_trading.ui.desktop.screens.notification_center.notification_center import NotificationCenter
except ImportError:
    def NotificationCenter():
        return create_placeholder_screen("알림 센터")


try:
    from upbit_auto_trading.ui.desktop.screens.asset_screener.asset_screener_screen import AssetScreenerScreen
except ImportError:
    def AssetScreenerScreen():
        return create_placeholder_screen("종목 스크리닝")


try:
    from upbit_auto_trading.ui.desktop.screens.strategy_management.strategy_management_screen import StrategyManagementScreen
except ImportError:
    def StrategyManagementScreen():
        return create_placeholder_screen("매매 전략 관리")


try:
    from upbit_auto_trading.ui.desktop.screens.backtesting.backtesting_screen import BacktestingScreen
except ImportError:
    def BacktestingScreen():
        return create_placeholder_screen("백테스팅")


try:
    from upbit_auto_trading.ui.desktop.screens.live_trading.live_trading_screen import LiveTradingScreen
except ImportError:
    def LiveTradingScreen():
        return create_placeholder_screen("실시간 거래")


try:
    from upbit_auto_trading.ui.desktop.screens.portfolio_configuration.portfolio_configuration_screen import (
        PortfolioConfigurationScreen
    )
except ImportError:
    def PortfolioConfigurationScreen():
        return create_placeholder_screen("포트폴리오 구성")


try:
    from upbit_auto_trading.ui.desktop.screens.monitoring_alerts.monitoring_alerts_screen import MonitoringAlertsScreen
except ImportError:
    def MonitoringAlertsScreen():
        return create_placeholder_screen("모니터링 & 알림")


class MainWindow(QMainWindow):
    """
    메인 윈도우 클래스

    애플리케이션의 메인 윈도우입니다.
    """

    def __init__(self):
        """초기화 - @inject 패턴으로 서비스 주입

        Args:
            settings_service: 설정 서비스
            theme_service: 테마 서비스
            style_manager: 스타일 매니저
            navigation_service: 네비게이션 서비스
            api_key_service: API 키 서비스
        """
        super().__init__()

        # DILifecycleManager를 통해 서비스 가져오기
        from upbit_auto_trading.infrastructure.dependency_injection import get_di_lifecycle_manager

        di_manager = get_di_lifecycle_manager()
        external_container = di_manager.get_external_container()

        # 서비스들 초기화
        self.api_key_service = external_container.api_key_service()
        self.settings_service = external_container.settings_service()
        self.theme_service = external_container.theme_service()
        self.style_manager = external_container.style_manager()

        # Navigation은 직접 생성
        from upbit_auto_trading.ui.desktop.common.widgets.navigation_bar import NavigationBar
        self.nav_bar = NavigationBar()

        # Presenter는 External Container에서 가져오기 (MVP 패턴)
        try:
            # External Dependency Container에서 MainWindowPresenter 가져오기
            self.presenter = external_container.main_window_presenter()
        except AttributeError as e:
            # Golden Rules: 에러 숨김 금지 - 명시적으로 문제 상황 알림
            raise RuntimeError(
                f"MainWindowPresenter Provider가 External Dependency Container에 등록되지 않았습니다. "
                f"original error: {e}. "
                f"External Dependency Container에 main_window_presenter Provider를 추가하거나 "
                f"MVP 패턴 의존성을 올바르게 구성해야 합니다."
            ) from e

        # IL 스마트 로깅 초기화 (먼저 초기화) - Fail-Fast 패턴
        try:
            from upbit_auto_trading.infrastructure.logging import create_component_logger
            self.logger = create_component_logger("MainWindow")
            self.logger.info("🎯 MainWindow IL 스마트 로깅 초기화 완료")
        except Exception as e:
            # 로깅은 핵심 Infrastructure이므로 실패시 명시적 에러 발생
            raise RuntimeError(f"MainWindow 필수 로깅 시스템 초기화 실패: {e}") from e

        # 서비스 주입 검증 및 초기화 (@inject 패턴 사용)
        # 핵심 서비스 주입 검증 - Fail-Fast 패턴
        if not self.settings_service:
            raise RuntimeError("SettingsService 주입 실패: MainWindow 핵심 의존성")
        self._log_info(f"✅ SettingsService 주입 성공: {type(self.settings_service).__name__}")

        if self.theme_service:
            self._log_info("✅ ThemeService 주입 성공")
            # 테마 변경 시그널 연결
            try:
                self.theme_service.connect_theme_changed(self._on_theme_changed_from_service)
                self._log_info("✅ 테마 변경 시그널 연결 성공")
            except Exception as e:
                self._log_error(f"❌ 테마 시그널 연결 실패: {e} (테마 자동 전환 비활성화)")
        else:
            self._log_warning("⚠️ ThemeService가 주입되지 않음")

        # StyleManager 주입 검증 - Fail-Fast 패턴
        if not self.style_manager:
            raise RuntimeError("StyleManager 주입 실패: UI 스타일링 필수 의존성")
        self._log_info("✅ StyleManager 주입 성공")

        # NavigationBar 주입 검증 (대체 가능)
        if self.nav_bar:
            self._log_info("✅ NavigationBar 주입 성공")
        else:
            self._log_warning("⚠️ NavigationBar 주입 실패 - 폴백 생성 예정")

        # DatabaseHealthService는 Presenter에서 처리

        # 화면 캐시 (지연 로딩용)
        self._screen_cache = {}
        self._screen_widgets: Dict[str, QWidget | None] = {}

        self.setWindowTitle("업비트 자동매매 시스템")
        self.setMinimumSize(1280, 720)  # 요구사항 문서의 최소 해상도 요구사항 적용

        # Application Service들은 Presenter를 통해 처리 (MVP 패턴)

        # MainWindowPresenter 연결 - MVP 패턴 핵심
        if self.presenter:
            self._setup_presenter_connections()
            self._log_info("✅ MVP 패턴 Presenter 연결 완료")
        else:
            self._log_info("⚠️ MainWindowPresenter 없이 동작 (단순화 모드)")

        # UI 설정
        self._setup_ui()

        # 저장된 테마 로드
        self._load_theme()

        self.style_manager.apply_theme()

        # WebSocket v6 초기화 (UI 로드 완료 후)
        self._initialize_websocket_async()

    def _log_info(self, message: str) -> None:
        """IL 스마트 로깅 - INFO 레벨"""
        if self.logger:
            self.logger.info(message)
        else:
            print(f"INFO: {message}")

    def _log_warning(self, message: str) -> None:
        """IL 스마트 로깅 - WARNING 레벨"""
        if self.logger:
            self.logger.warning(message)
        else:
            print(f"WARNING: {message}")

    def _log_error(self, message: str) -> None:
        """IL 스마트 로깅 - ERROR 레벨"""
        if self.logger:
            self.logger.error(message)
        else:
            print(f"ERROR: {message}")

    def _log_debug(self, message: str) -> None:
        """IL 스마트 로깅 - DEBUG 레벨"""
        if self.logger:
            self.logger.debug(message)
        else:
            print(f"DEBUG: {message}")

    def _setup_ui(self):
        """UI 설정"""
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃 설정
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 네비게이션 바 시그널 연결
        if self.nav_bar:
            self.nav_bar.screen_changed.connect(self._change_screen)
        else:
            # 폴백: 기존 방식으로 NavigationBar 생성
            self.nav_bar = NavigationBar()
            self.nav_bar.screen_changed.connect(self._change_screen)
            self._log_warning("⚠️ NavigationBar 폴백 생성 (DI 주입 실패)")

        # 콘텐츠 영역 설정
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 스택 위젯 설정 (화면 전환용)
        self.stack_widget = QStackedWidget()

        # 화면 추가
        self._add_screens()

        # 레이아웃에 위젯 추가
        content_layout.addWidget(self.stack_widget)

        main_layout.addWidget(self.nav_bar)
        main_layout.addWidget(content_widget)

        # 상태 바 설정 - 기본 StatusBar만 설정
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)
        self._log_info("✅ StatusBar 기본 설정 완료")

        # 메뉴 바 설정 (Presenter를 통한 MVP 패턴)
        menu_dependencies = self._get_menu_dependencies()
        self.presenter.handle_menu_setup(self, menu_dependencies)

        # 저장된 창 상태 로드 (Presenter를 통한 MVP 패턴)
        self.presenter.handle_window_state_load(self, self.settings_service)

    def _initialize_websocket_async(self):
        """WebSocket v6 Application Service 비동기 초기화 - QAsync TaskManager 사용"""
        from PyQt6.QtCore import QTimer

        def start_websocket_init():
            """WebSocket 초기화를 비동기적으로 시작 - AppKernel TaskManager 활용"""
            try:
                # AppKernel에서 TaskManager 가져오기
                from upbit_auto_trading.infrastructure.runtime.app_kernel import get_kernel
                kernel = get_kernel()

                if kernel:
                    # TaskManager를 통한 안전한 태스크 생성
                    kernel.create_task(
                        self._perform_websocket_initialization(),
                        name="websocket_initialization",
                        component="MainWindow"
                    )
                    self._log_info("🔄 TaskManager를 통한 WebSocket v6 초기화 태스크 생성 완료")
                else:
                    self._log_warning("⚠️ AppKernel을 사용할 수 없음 - WebSocket 초기화 연기")
                    # 100ms 후 재시도
                    QTimer.singleShot(100, start_websocket_init)

            except Exception as e:
                self._log_error(f"❌ TaskManager WebSocket 초기화 태스크 생성 실패: {e}")
                # 폴백: 100ms 후 재시도
                QTimer.singleShot(100, start_websocket_init)

        # 100ms 후에 WebSocket 초기화 시작 (UI 로드 완료 후)
        QTimer.singleShot(100, start_websocket_init)

    async def _perform_websocket_initialization(self):
        """실제 WebSocket 초기화 수행 - LoopGuard 적용"""
        # LoopGuard로 이벤트 루프 안전성 확보
        from upbit_auto_trading.infrastructure.runtime.loop_guard import ensure_main_loop
        ensure_main_loop(where="MainWindow._perform_websocket_initialization", component="MainWindow")

        try:
            self._log_info("🚀 WebSocket v6 Application Service 초기화 시작 (LoopGuard 적용)")

            from upbit_auto_trading.application.services.websocket_application_service import (
                get_websocket_service,
                WebSocketServiceConfig
            )

            # API 키 확인 (WebSocket Private 연결 결정)
            api_key_available = False
            try:
                if self.api_key_service:
                    access_key, secret_key, _ = self.api_key_service.load_api_keys()
                    api_key_available = bool(access_key and secret_key)
                    self._log_info(f"🔑 API 키 상태: {'사용 가능' if api_key_available else '없음'}")
            except Exception as api_check_error:
                self._log_warning(f"⚠️ API 키 확인 실패: {api_check_error}")

            # WebSocket v6 서비스 설정
            websocket_config = WebSocketServiceConfig(
                auto_start_on_init=True,
                enable_public_connection=True,
                enable_private_connection=api_key_available,  # API 키가 있을 때만 Private 연결
                reconnect_on_failure=True,
                health_check_interval=30.0
            )

            self._log_info(f"🌐 WebSocket 연결 설정 - Public: ✅, Private: {'✅' if api_key_available else '❌'}")

            # WebSocket v6 서비스 초기화 및 시작
            websocket_service = await get_websocket_service(websocket_config)

            # MainWindow에 서비스 저장 (필요시 사용)
            self.websocket_service = websocket_service

            self._log_info("✅ WebSocket v6 Application Service 초기화 완료")

        except Exception as e:
            self._log_error(f"❌ WebSocket v6 초기화 실패: {e.__class__.__name__}: {e}")
            self._log_warning("⚠️ WebSocket 없이 계속 진행 (실시간 데이터 수신 불가)")
            # WebSocket은 선택적 기능이므로 실패해도 애플리케이션 계속 실행

    # Legacy 창 상태 로드 메서드가 제거되었습니다. WindowStateService에서 처리됩니다.

    # Legacy 메뉴 바 설정 메서드가 제거되었습니다. MenuService에서 처리됩니다.

    def _add_screens(self):
        """화면 추가 (Presenter를 통한 MVP 패턴)"""
        if not self.presenter:
            # Presenter가 없으면 명시적 에러 발생 - Golden Rules: 에러 숨김 금지
            raise RuntimeError(
                "MainWindowPresenter가 None입니다. "
                "External Dependency Container에 main_window_presenter Provider가 구현되지 않았거나 "
                "MVP 패턴 의존성 주입이 실패했습니다."
            )

        success = self.presenter.handle_screen_initialization(self.stack_widget, self._screen_widgets)
        if not success:
            # 폴백: 대시보드 화면만 간단히 추가
            dashboard_screen = DashboardScreen()
            self.stack_widget.addWidget(dashboard_screen)
            self._screen_widgets = {'대시보드': dashboard_screen}
            self._log_warning("⚠️ 폴백으로 대시보드 화면만 추가")

    def _add_placeholder_screens(self, screens):
        """임시 화면 추가"""
        # 각 화면에 대한 임시 위젯 생성

        for screen_name in screens:
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)

            label = QLabel(f"{screen_name} 화면 (구현 예정)")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)

            self.stack_widget.addWidget(placeholder)

    def _change_screen(self, screen_name):
        """화면 전환 (Presenter를 통한 MVP 패턴)"""
        dependencies = self._prepare_screen_dependencies()
        success = self.presenter.handle_screen_change(
            screen_name, self.stack_widget, self._screen_widgets, dependencies
        )
        if not success:
            self._log_warning(f"⚠️ 화면 전환 실패: {screen_name}")

    def _prepare_screen_dependencies(self):
        """화면 의존성 준비 (@inject 패턴 사용으로 mvp_container 제거됨)"""
        # Application Logging Service 준비 (Phase 6 기능 테스트를 위해 추가)
        try:
            from upbit_auto_trading.infrastructure.dependency_injection import get_external_dependency_container
            external_container = get_external_dependency_container()
            application_logging_service = external_container.application_logging_service()
        except Exception:
            # 폴백: 직접 생성
            from upbit_auto_trading.application.services.logging_application_service import ApplicationLoggingService
            application_logging_service = ApplicationLoggingService()

        # MVP Container 준비
        try:
            from upbit_auto_trading.presentation.mvp_container import get_mvp_container
            mvp_container = get_mvp_container()
        except Exception:
            mvp_container = None

        return {
            'settings_service': self.settings_service,
            'application_logging_service': application_logging_service,
            'mvp_container': mvp_container,
            'parent': self,
            'backtest_callback': self._on_backtest_requested,
            'settings_changed_callback': self._on_settings_changed_from_screen,
            'theme_changed_callback': self._on_theme_changed_from_ui_settings,
            'api_status_changed_callback': getattr(self, '_on_api_status_changed', None)
        }

    def _get_menu_dependencies(self):
        """메뉴 서비스에 필요한 의존성 반환"""
        return {
            'change_screen_callback': self._change_screen,
            'toggle_theme_callback': self._toggle_theme_via_service,
            'reset_window_size_callback': self._reset_window_size_via_presenter,
            'reset_window_size_medium_callback': self._reset_window_size_medium_via_presenter,
            'theme_service': self.theme_service,
            'style_manager': self.style_manager,
            'nav_bar': self.nav_bar
        }

    def _setup_presenter_connections(self):
        """MainWindowPresenter와 UI 간 시그널-슬롯 연결 - MVP 패턴 강화"""
        if hasattr(self, 'presenter'):
            # 기존 시그널 연결
            self.presenter.theme_update_requested.connect(self._on_theme_update_requested)
            self.presenter.status_update_requested.connect(self._on_status_update_requested)

            # 새로운 시그널 연결
            self.presenter.screen_change_requested.connect(self._on_screen_change_requested)
            self.presenter.window_title_update_requested.connect(self.setWindowTitle)
            self.presenter.navigation_update_requested.connect(self._on_navigation_update_requested)
            self.presenter.error_message_requested.connect(self._on_error_message_requested)

            self._log_debug("✅ MainWindowPresenter 시그널-슬롯 연결 완료 (MVP 패턴 강화)")

    def _on_theme_update_requested(self, theme_name: str):
        """Presenter에서 테마 업데이트 요청 시 처리"""
        try:
            self._log_debug(f"Presenter로부터 테마 업데이트 요청: {theme_name}")
            self._log_info(f"✅ Presenter 테마 업데이트 완료: {theme_name}")

        except Exception as e:
            self._log_error(f"❌ Presenter 테마 업데이트 실패: {e}")

    def _on_status_update_requested(self, status_type: str, status_value: str):
        """Presenter에서 상태 업데이트 요청 시 처리"""
        try:
            self._log_debug(f"Presenter로부터 상태 업데이트 요청: {status_type} = {status_value}")
            # StatusBar가 있으면 업데이트
            if hasattr(self, 'status_bar') and self.status_bar:
                # StatusBar의 메서드가 있으면 호출 (구현에 따라)
                pass  # 실제 StatusBar 업데이트 로직은 StatusBar 구현에 따라 결정
            self._log_debug(f"✅ Presenter 상태 업데이트 완료: {status_type}")

        except Exception as e:
            self._log_error(f"❌ Presenter 상태 업데이트 실패: {e}")

    def _on_screen_change_requested(self, screen_name: str):
        """Presenter에서 화면 전환 요청 시 처리 - View는 단순 실행만"""
        try:
            self._change_screen(screen_name)
            self._log_debug(f"✅ 화면 전환 요청 처리 완료: {screen_name}")
        except Exception as e:
            self._log_error(f"❌ 화면 전환 요청 처리 실패: {e}")

    def _on_navigation_update_requested(self):
        """Presenter에서 네비게이션 업데이트 요청 시 처리"""
        try:
            if hasattr(self, 'nav_bar') and self.nav_bar:
                self.nav_bar.update()
                self.nav_bar.repaint()
            self._log_debug("✅ 네비게이션 바 업데이트 완료")
        except Exception as e:
            self._log_error(f"❌ 네비게이션 바 업데이트 실패: {e}")

    def _on_error_message_requested(self, title: str, message: str):
        """Presenter에서 에러 메시지 표시 요청 시 처리"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.exec()
            self._log_debug(f"✅ 에러 메시지 표시 완료: {title}")
        except Exception as e:
            self._log_error(f"❌ 에러 메시지 표시 실패: {e}")

    def _toggle_theme_via_service(self):
        """MenuService를 통한 테마 전환 - MVP 패턴으로 Presenter를 통해 처리"""
        if hasattr(self, 'presenter') and self.presenter:
            self.presenter.handle_theme_toggle(
                self.theme_service,
                self.style_manager,
                self.nav_bar
            )
        else:
            self._log_error("MainWindowPresenter가 초기화되지 않음")

    def _reset_window_size_via_presenter(self):
        """창크기 초기화 - MVP 패턴으로 Presenter를 통해 처리"""
        if hasattr(self, 'presenter') and self.presenter:
            self.presenter.handle_reset_window_size(self)
        else:
            self._log_error("MainWindowPresenter가 초기화되지 않음")

    def _reset_window_size_medium_via_presenter(self):
        """창크기 초기화(중간) - MVP 패턴으로 Presenter를 통해 처리"""
        if hasattr(self, 'presenter') and self.presenter:
            self.presenter.handle_reset_window_size_medium(self)
        else:
            self._log_error("MainWindowPresenter가 초기화되지 않음")

    def _load_screen_lazy(self, screen_name):
        """지연 로딩으로 화면 생성 - 간단한 플레이스홀더로 대체"""
        screen = None
        try:
            from upbit_auto_trading.ui.desktop.common.widgets.placeholder import create_placeholder_screen
            screen = create_placeholder_screen(screen_name)
            if screen is not None:
                self.stack_widget.addWidget(screen)
                self._screen_widgets[screen_name] = screen
                self._log_info(f"{screen_name} 화면 로딩 완료 (플레이스홀더)")
        except Exception as e:
            self._log_error(f"{screen_name} 화면 로딩 실패: {e}")
            if screen is not None:
                self._screen_widgets[screen_name] = screen

    def _on_theme_changed_from_service(self, theme_name: str):
        """ThemeService에서 테마 변경 시그널을 받았을 때 처리"""
        self._log_info(f"ThemeService에서 테마 변경 시그널 수신: {theme_name}")

        # 네비게이션 바 스타일 강제 업데이트
        if hasattr(self, 'nav_bar') and self.nav_bar:
            self.nav_bar.update()
            self.nav_bar.repaint()

        # 전역 테마 변경 알림 발송 (기존 컴포넌트와의 호환성)
        try:
            from upbit_auto_trading.ui.desktop.common.theme_notifier import get_theme_notifier
            theme_notifier = get_theme_notifier()
            theme_notifier.notify_theme_changed()
            self._log_info("기존 theme_notifier를 통한 알림 발송 완료")
        except Exception as e:
            self._log_warning(f"기존 테마 변경 알림 실패: {e}")

    def _on_settings_changed_from_screen(self):
        """설정 화면에서 설정 변경 시그널을 받았을 때 처리"""
        self._log_info("설정 변경 시그널 수신")
        self._load_theme()
        if hasattr(self, 'nav_bar'):
            self.nav_bar.update()

    def _on_theme_changed_from_ui_settings(self, theme_name: str):
        """UI 설정에서 테마 변경 시그널을 받았을 때 처리"""
        self._log_info(f"UI 설정에서 테마 변경: {theme_name}")
        if self.theme_service:
            try:
                self.theme_service.set_theme(theme_name)
            except Exception as e:
                self._log_warning(f"테마 적용 실패: {e}")
        if hasattr(self, 'nav_bar'):
            self.nav_bar.update()

    def _load_theme(self):
        """저장된 테마 로드 - ThemeService에서 처리"""
        if self.theme_service:
            try:
                self.theme_service.apply_current_theme()
                current_theme = self.theme_service.get_current_theme()
                self._log_info(f"ThemeService를 통한 테마 로드 완료: {current_theme}")
            except Exception as e:
                self._log_warning(f"ThemeService 테마 로드 실패: {e}")
        else:
            self._log_warning("ThemeService 없음 - 기본 테마 사용")

    def _update_all_widgets(self):
        """모든 위젯 업데이트"""
        try:
            if hasattr(self, 'nav_bar'):
                self.nav_bar.update()
            if hasattr(self, 'stack_widget'):
                current_widget = self.stack_widget.currentWidget()
                if current_widget:
                    current_widget.update()
        except Exception as e:
            self._log_error(f"위젯 업데이트 오류: {e}")

    def showEvent(self, a0):
        """윈도우 표시 이벤트 처리"""
        super().showEvent(a0)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._update_all_widgets)

    def _save_settings(self):
        """설정 저장 - Presenter를 통한 MVP 패턴"""
        success = self.presenter.handle_window_state_save(self, self.settings_service)
        if not success:
            self._log_warning("⚠️ 창 상태 저장 실패")

    def closeEvent(self, a0):
        """
        윈도우 종료 이벤트 처리

        Args:
            a0: 종료 이벤트
        """
        # 설정 저장
        self._save_settings()

        # 이벤트 수락
        if a0:
            a0.accept()

    def _on_backtest_requested(self, strategy_id):
        """매매전략 관리에서 백테스팅 요청 시 처리"""
        try:
            self._log_info(f"백테스팅 요청 수신: 전략 ID = {strategy_id}")
            self._change_screen("backtest")
        except Exception as e:
            self._log_error(f"백테스팅 화면 전환 실패: {e}")
            traceback.print_exc()

    # ======================================================================
    # Legacy 메서드들이 제거되었습니다.
    # 상태바 관련 로직은 StatusBar 위젯에서 자율적으로 처리됩니다.
    # 해당 기능들은 MainWindowPresenter에서 처리됩니다.
    # ======================================================================
