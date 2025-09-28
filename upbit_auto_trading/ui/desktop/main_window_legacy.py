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

# Application Layer 서비스
from upbit_auto_trading.application.services.database_health_service import DatabaseHealthService
from upbit_auto_trading.application.services.screen_manager_service import ScreenManagerService
from upbit_auto_trading.application.services.window_state_service import WindowStateService
from upbit_auto_trading.application.services.menu_service import MenuService

# Presenter Layer
from upbit_auto_trading.ui.desktop.presenters.main_window_presenter import MainWindowPresenter

# 공통 위젯 임포트
from upbit_auto_trading.ui.desktop.common.widgets.status_bar import StatusBar
from upbit_auto_trading.ui.desktop.common.widgets.navigation_bar import NavigationBar
from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager

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

    @inject
    @inject
    def __init__(
        self,
        settings_service=Provide["settings_service"],
        theme_service=Provide["theme_service"],
        style_manager=Provide["style_manager"],
        navigation_service=Provide["navigation_service"],
        api_key_service=Provide["api_key_service"]
    ):
        """초기화 - @inject 패턴으로 서비스 주입

        Args:
            settings_service: 설정 서비스
            theme_service: 테마 서비스
            style_manager: 스타일 매니저
            navigation_service: 네비게이션 서비스
            api_key_service: API 키 서비스
        """
        super().__init__()

        # 주입받은 API 키 서비스 저장
        self.api_key_service = api_key_service

        # 주입받은 서비스들 저장
        self.settings_service = settings_service
        self.theme_service = theme_service
        self.style_manager = style_manager
        self.nav_bar = navigation_service

        # IL 스마트 로깅 초기화 (먼저 초기화)
        self.logger = None
        try:
            from upbit_auto_trading.infrastructure.logging import create_component_logger
            self.logger = create_component_logger("MainWindow")
            self.logger.info("🎯 MainWindow IL 스마트 로깅 초기화 완료")
        except Exception as e:
            # 폴백: print로 출력하되 로거는 None 유지
            print(f"⚠️ IL 스마트 로깅 초기화 실패, print 폴백: {e}")

        # 서비스 주입 검증 및 초기화 (@inject 패턴 사용)
        if self.settings_service:
            self._log_info(f"✅ SettingsService 주입 성공: {type(self.settings_service).__name__}")
        else:
            self._log_warning("⚠️ SettingsService가 주입되지 않음")

        if self.theme_service:
            self._log_info("✅ ThemeService 주입 성공")
            # 테마 변경 시그널 연결
            try:
                self.theme_service.connect_theme_changed(self._on_theme_changed_from_service)
            except Exception as e:
                self._log_warning(f"⚠️ 테마 변경 시그널 연결 실패: {e}")
        else:
            self._log_warning("⚠️ ThemeService가 주입되지 않음")

        if self.style_manager:
            self._log_info("✅ StyleManager 주입 성공")
        else:
            self._log_warning("⚠️ StyleManager가 주입되지 않음")

        if self.nav_bar:
            self._log_info("✅ NavigationBar 주입 성공")
        else:
            self._log_warning("⚠️ NavigationBar가 주입되지 않음")

        # DatabaseHealthService 초기화 (최소 구현)
        self.db_health_service = None
        try:
            # DatabaseHealthService 생성 (최소 구현)
            self.db_health_service = DatabaseHealthService()
            self._log_info("✅ DatabaseHealthService 초기화 완료 (최소 구현)")

        except Exception as e:
            self._log_warning(f"⚠️ DatabaseHealthService 초기화 실패: {e}")

        # 화면 캐시 (지연 로딩용)
        self._screen_cache = {}
        self._screen_widgets: Dict[str, QWidget | None] = {}

        self.setWindowTitle("업비트 자동매매 시스템")
        self.setMinimumSize(1280, 720)  # 요구사항 문서의 최소 해상도 요구사항 적용

        # ScreenManagerService 초기화 (DDD/MVP 패턴)
        self.screen_manager = ScreenManagerService()
        self._log_info("✅ ScreenManagerService 초기화 완료")

        # WindowStateService 초기화 (DDD/MVP 패턴)
        self.window_state_service = WindowStateService()
        self._log_info("✅ WindowStateService 초기화 완료")

        # MenuService 초기화 (DDD/MVP 패턴)
        self.menu_service = MenuService()
        self._log_info("✅ MenuService 초기화 완료")

        # MainWindowPresenter 초기화 (DDD/MVP 패턴)
        presenter_services = self._get_presenter_dependencies()
        self.presenter = MainWindowPresenter(presenter_services)
        self._setup_presenter_connections()
        self._log_info("✅ MainWindowPresenter 초기화 완료")

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

        # 상태 바 설정 - 자율적 상태바로 간소화
        db_service = getattr(self, 'db_health_service', None)
        self.status_bar = StatusBar(database_health_service=db_service)
        self.setStatusBar(self.status_bar)
        self._log_info("✅ 자율적 StatusBar 초기화 완료")

        # 메뉴 바 설정 (MenuService 사용)
        menu_dependencies = self._get_menu_dependencies()
        self.menu_service.setup_menu_bar(self, menu_dependencies)

        # 저장된 창 상태 로드 (WindowStateService 사용)
        self.window_state_service.load_window_state(self, self.settings_service)

    def _initialize_websocket_async(self):
        """WebSocket v6 Application Service 비동기 초기화"""
        import asyncio

        # QTimer를 사용해서 이벤트 루프가 준비된 후 WebSocket 초기화
        from PyQt6.QtCore import QTimer

        def start_websocket_init():
            """WebSocket 초기화를 비동기적으로 시작"""
            try:
                # 현재 이벤트 루프 확인
                try:
                    asyncio.get_running_loop()
                    # 비동기 초기화 태스크 생성
                    asyncio.create_task(self._perform_websocket_initialization())
                    self._log_info("🔄 WebSocket v6 초기화 태스크 생성 완료")
                except RuntimeError:
                    self._log_warning("⚠️ 이벤트 루프가 실행되지 않음 - WebSocket 초기화 연기")
                    # 100ms 후 재시도
                    QTimer.singleShot(100, start_websocket_init)

            except Exception as e:
                self._log_error(f"❌ WebSocket 초기화 태스크 생성 실패: {e}")

        # 100ms 후에 WebSocket 초기화 시작 (UI 로드 완료 후)
        QTimer.singleShot(100, start_websocket_init)

    async def _perform_websocket_initialization(self):
        """실제 WebSocket 초기화 수행"""
        try:
            self._log_info("🚀 WebSocket v6 Application Service 초기화 시작")

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
            self._log_error(f"❌ WebSocket v6 Application Service 초기화 실패: {e}")
            # WebSocket 실패는 치명적이지 않으므로 계속 진행
            self._log_warning("⚠️ WebSocket v6 없이 계속 진행합니다")

    # Legacy 창 상태 로드 메서드가 제거되었습니다. WindowStateService에서 처리됩니다.

    # Legacy 메뉴 바 설정 메서드가 제거되었습니다. MenuService에서 처리됩니다.

    def _add_screens(self):
        """화면 추가 (ScreenManagerService 사용)"""
        try:
            self.screen_manager.initialize_screens(self.stack_widget, self._screen_widgets)
            self._log_info("ScreenManagerService를 통한 화면 초기화 완료")
        except Exception as e:
            self._log_error(f"ScreenManagerService 화면 초기화 실패: {e}")
            # 대시보드 화면만 간단히 추가
            dashboard_screen = DashboardScreen()
            self.stack_widget.addWidget(dashboard_screen)
            self._screen_widgets = {'대시보드': dashboard_screen}

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
        """화면 전환 (ScreenManagerService 사용)"""
        try:
            # 의존성 준비
            dependencies = self._prepare_screen_dependencies()

            # ScreenManagerService를 통한 화면 전환
            success = self.screen_manager.change_screen(
                screen_name,
                self.stack_widget,
                self._screen_widgets,
                dependencies
            )

            if not success:
                self._log_warning(f"ScreenManagerService 화면 전환 실패: {screen_name}")

        except Exception as e:
            self._log_error(f"ScreenManagerService 화면 전환 중 오류: {e}")

    def _prepare_screen_dependencies(self):
        """화면 의존성 준비 (@inject 패턴 사용으로 mvp_container 제거됨)"""
        return {
            'settings_service': self.settings_service,
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
            'window_state_service': self.window_state_service,
            'theme_service': self.theme_service,
            'style_manager': self.style_manager,
            'nav_bar': self.nav_bar
        }

    def _get_presenter_dependencies(self):
        """MainWindowPresenter에 필요한 의존성 반환"""
        return {
            'theme_service': self.theme_service,
            'database_health_service': self.db_health_service,
            'navigation_bar': self.nav_bar if hasattr(self, 'nav_bar') else None
        }

    def _setup_presenter_connections(self):
        """MainWindowPresenter와 UI 간 시그널-슬롯 연결"""
        if hasattr(self, 'presenter'):
            # 테마 업데이트 요청 시그널 연결
            self.presenter.theme_update_requested.connect(self._on_theme_update_requested)

            # 상태 업데이트 요청 시그널 연결
            self.presenter.status_update_requested.connect(self._on_status_update_requested)

            self._log_debug("✅ MainWindowPresenter 시그널-슬롯 연결 완료")

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
            self._log_debug(f"✅ Presenter 상태 업데이트 완료: {status_type}")

        except Exception as e:
            self._log_error(f"❌ Presenter 상태 업데이트 실패: {e}")

    def _toggle_theme_via_service(self):
        """MenuService를 통한 테마 전환"""
        self.menu_service.toggle_theme(
            self.theme_service,
            self.style_manager,
            self.nav_bar
        )

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
        """설정 저장 - WindowStateService로 위임"""
        try:
            self.window_state_service.save_window_state(self, self.settings_service)
        except Exception as e:
            self._log_error(f"설정 저장 실패: {e}")

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
            import traceback
            traceback.print_exc()

    # ======================================================================
    # Legacy 메서드들이 제거되었습니다.
    # 상태바 관련 로직은 StatusBar 위젯에서 자율적으로 처리됩니다.
    # 해당 기능들은 MainWindowPresenter에서 처리됩니다.
    # ======================================================================
