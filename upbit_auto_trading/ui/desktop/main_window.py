"""
메인 윈도우 모듈
"""
import sys
import os
import json
import sqlite3
import gc
import traceback
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QMessageBox, QApplication, QLabel
)
from PyQt6.QtCore import Qt, QSettings, QSize, QPoint
from PyQt6.QtGui import QIcon, QAction

# Infrastructure Layer 서비스 인터페이스
from upbit_auto_trading.infrastructure.services.api_key_service import IApiKeyService

# Application Layer 서비스
from upbit_auto_trading.application.services.database_health_service import DatabaseHealthService

# 공통 위젯 임포트
from upbit_auto_trading.ui.desktop.common.widgets.status_bar import StatusBar
from upbit_auto_trading.ui.desktop.common.widgets.navigation_bar import NavigationBar
from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager, Theme

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
    DashboardScreen = lambda: create_placeholder_screen("대시보드")

try:
    from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen
except ImportError:
    ChartViewScreen = lambda: create_placeholder_screen("차트 뷰")

try:
    from upbit_auto_trading.ui.desktop.screens.settings.settings_screen import SettingsScreen
except ImportError:
    SettingsScreen = lambda: create_placeholder_screen("설정")

try:
    from upbit_auto_trading.ui.desktop.screens.notification_center.notification_center import NotificationCenter
except ImportError:
    NotificationCenter = lambda: create_placeholder_screen("알림 센터")

try:
    from upbit_auto_trading.ui.desktop.screens.asset_screener.asset_screener_screen import AssetScreenerScreen
except ImportError:
    AssetScreenerScreen = lambda: create_placeholder_screen("종목 스크리닝")

try:
    from upbit_auto_trading.ui.desktop.screens.strategy_management.strategy_management_screen import StrategyManagementScreen
except ImportError:
    StrategyManagementScreen = lambda: create_placeholder_screen("매매 전략 관리")

try:
    from upbit_auto_trading.ui.desktop.screens.backtesting.backtesting_screen import BacktestingScreen
except ImportError:
    BacktestingScreen = lambda: create_placeholder_screen("백테스팅")

try:
    from upbit_auto_trading.ui.desktop.screens.live_trading.live_trading_screen import LiveTradingScreen
except ImportError:
    LiveTradingScreen = lambda: create_placeholder_screen("실시간 거래")

try:
    from upbit_auto_trading.ui.desktop.screens.portfolio_configuration.portfolio_configuration_screen import PortfolioConfigurationScreen
except ImportError:
    PortfolioConfigurationScreen = lambda: create_placeholder_screen("포트폴리오 구성")

try:
    from upbit_auto_trading.ui.desktop.screens.monitoring_alerts.monitoring_alerts_screen import MonitoringAlertsScreen
except ImportError:
    MonitoringAlertsScreen = lambda: create_placeholder_screen("모니터링 & 알림")

class MainWindow(QMainWindow):
    """
    메인 윈도우 클래스

    애플리케이션의 메인 윈도우입니다.
    """

    def __init__(self, di_container=None):
        """초기화

        Args:
            di_container: DI Container (옵션). None이면 기존 방식으로 동작
        """
        super().__init__()

        # DI Container 저장
        self.di_container = di_container

        # IL 스마트 로깅 초기화 (먼저 초기화)
        self.logger = None
        try:
            from upbit_auto_trading.infrastructure.logging import create_component_logger
            self.logger = create_component_logger("MainWindow")
            self.logger.info("🎯 MainWindow IL 스마트 로깅 초기화 완료")
        except Exception as e:
            # 폴백: print로 출력하되 로거는 None 유지
            print(f"⚠️ IL 스마트 로깅 초기화 실패, print 폴백: {e}")

        # MVP Container 초기화 (TASK-13: MVP 패턴 적용)
        self.mvp_container = None
        try:
            from upbit_auto_trading.presentation.mvp_container import initialize_mvp_system
            from upbit_auto_trading.application.container import get_application_container

            app_container = get_application_container()
            if app_container:
                self.mvp_container = initialize_mvp_system(app_container)
                self._log_info("✅ MVP 시스템 초기화 완료")
            else:
                self._log_warning("⚠️ Application Container를 찾을 수 없음")
        except Exception as e:
            self._log_warning(f"⚠️ MVP 시스템 초기화 실패: {e}")

        # SettingsService 주입 (DI Container 기반 또는 기존 방식)
        self._log_info("🔧 SettingsService 주입 시작...")
        self.settings_service = None
        if self.di_container:
            self._log_info("🔧 DI Container 존재 확인 완료")
            try:
                from upbit_auto_trading.infrastructure.services.settings_service import ISettingsService
                self._log_info("🔧 ISettingsService import 성공")

                # DI Container에 등록되어 있는지 확인
                is_registered = self.di_container.is_registered(ISettingsService)
                self._log_info(f"🔧 ISettingsService 등록 상태: {is_registered}")

                # DI Container 자체 확인
                container_type = type(self.di_container).__name__
                self._log_info(f"🔧 DI Container 타입: {container_type}")

                # resolve 시도 전 로그
                self._log_info("🔧 SettingsService resolve 시도 중...")
                self.settings_service = self.di_container.resolve(ISettingsService)

                if self.settings_service is not None:
                    self._log_info(f"✅ SettingsService DI 주입 성공: {type(self.settings_service).__name__}")
                else:
                    self._log_error("❌ SettingsService resolve 결과가 None")

            except Exception as e:
                self._log_error(f"❌ SettingsService DI 주입 실패: {e}")
                self._log_error(f"❌ Exception 타입: {type(e).__name__}")
                # 예외 스택 트레이스 로그
                self._log_debug(f"📊 SettingsService 주입 실패 상세: {traceback.format_exc()}")
        else:
            self._log_warning("⚠️ DI Container가 None - SettingsService 주입 불가")

        # ThemeService 주입 (Infrastructure Layer 기반)
        self.theme_service = None
        if self.di_container:
            try:
                from upbit_auto_trading.infrastructure.services.theme_service import IThemeService
                self.theme_service = self.di_container.resolve(IThemeService)
                self._log_info("✅ ThemeService DI 주입 성공")
                # 테마 변경 시그널 연결
                self.theme_service.connect_theme_changed(self._on_theme_changed_from_service)

            except Exception as e:
                self._log_warning(f"⚠️ ThemeService DI 주입 실패, 기존 방식 사용: {e}")

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
        self._screen_widgets = {}

        self.setWindowTitle("업비트 자동매매 시스템")
        self.setMinimumSize(1280, 720)  # 요구사항 문서의 최소 해상도 요구사항 적용

        # 설정 로드
        self._load_settings()

        # UI 설정
        self._setup_ui()

        # 스타일 적용 (DI Container 기반 또는 기존 방식)
        if self.di_container:
            # DI Container에서 StyleManager 주입
            try:
                self.style_manager = self.di_container.resolve(StyleManager)
                self._log_info("✅ StyleManager DI 주입 성공")
            except Exception as e:
                self._log_warning(f"⚠️ StyleManager DI 주입 실패, 기존 방식 사용: {e}")
                self.style_manager = StyleManager()
        else:
            # 기존 방식 (호환성 유지)
            self.style_manager = StyleManager()
            self._log_debug("StyleManager 기존 방식으로 생성 (DI Container 없음)")

        # 저장된 테마 로드
        self._load_theme()

        self.style_manager.apply_theme()

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

        # 네비게이션 바 설정 (DI Container 기반 또는 기존 방식)
        if self.di_container:
            try:
                self.nav_bar = self.di_container.resolve(NavigationBar)
                self._log_info("✅ NavigationBar DI 주입 성공")

            except Exception as e:
                self._log_warning(f"⚠️ NavigationBar DI 주입 실패, 기존 방식 사용: {e}")

                self.nav_bar = NavigationBar()
        else:
            self.nav_bar = NavigationBar()
            self._log_debug("NavigationBar 기존 방식으로 생성 (DI Container 없음)")
        self.nav_bar.screen_changed.connect(self._change_screen)

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

        # 상태 바 설정 (DI Container 기반 또는 기존 방식)
        if self.di_container:
            try:
                self.status_bar = self.di_container.resolve(StatusBar)
                self._log_info("StatusBar DI 주입 성공")

            except Exception as e:
                self._log_warning(f"StatusBar DI 주입 실패, 기존 방식 사용: {e}")
                self.status_bar = StatusBar()
        else:
            self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        # API 새로고침 시그널 연결
        self.status_bar.api_refresh_requested.connect(self._on_api_refresh_requested)

        # 초기 API 연결 상태 확인
        self._check_initial_api_status()

        # 초기 DB 연결 상태 확인
        self._check_initial_db_status()

        # 메뉴 바 설정
        self._setup_menu_bar()

        # 저장된 창 상태 로드 (설정 서비스 기반)
        self._load_window_state()

    def _load_window_state(self):
        """저장된 창 크기/위치 로드 (SettingsService 우선, 실패 시 QSettings 폴백)"""
        if self.settings_service:
            try:
                window_state = self.settings_service.load_window_state()
                if window_state:
                    # 창 크기 설정
                    if 'width' in window_state and 'height' in window_state:
                        self.resize(window_state['width'], window_state['height'])
                        self._log_info(f"SettingsService에서 창 크기 로드: {window_state['width']}x{window_state['height']}")

                    # 창 위치 설정
                    if 'x' in window_state and 'y' in window_state:
                        self.move(window_state['x'], window_state['y'])
                        self._log_info(f"SettingsService에서 창 위치 로드: ({window_state['x']}, {window_state['y']})")

                    # 최대화 상태 설정
                    if window_state.get('maximized', False):
                        self.showMaximized()
                        self._log_info("SettingsService에서 창 최대화 상태 로드")

                    return
                else:
                    self._log_info("SettingsService에 저장된 창 상태 없음, 기본값 사용")
            except Exception as e:
                self._log_warning(f"SettingsService 창 상태 로드 실패, QSettings 사용: {e}")

        # 폴백: QSettings 사용
        try:
            settings = QSettings("UpbitAutoTrading", "MainWindow")

            # 창 크기 복원
            size = settings.value("size")
            if size:
                self.resize(size)
                self._log_info(f"QSettings에서 창 크기 로드: {size.width()}x{size.height()}")

            # 창 위치 복원
            position = settings.value("position")
            if position:
                self.move(position)
                self._log_info(f"QSettings에서 창 위치 로드: ({position.x()}, {position.y()})")

        except Exception as e:
            self._log_warning(f"QSettings 창 상태 로드 실패, 기본값 사용: {e}")
            # 기본 창 크기/위치 설정
            self.resize(1600, 1000)

    def _setup_menu_bar(self):
        """메뉴 바 설정"""
        # 파일 메뉴
        file_menu = self.menuBar().addMenu("파일")

        # 설정 액션
        settings_action = QAction("설정", self)
        settings_action.triggered.connect(lambda: self._change_screen("settings"))
        file_menu.addAction(settings_action)

        # 종료 액션
        exit_action = QAction("종료", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 보기 메뉴
        view_menu = self.menuBar().addMenu("보기")

        # 테마 전환 액션
        theme_action = QAction("테마 전환", self)
        theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(theme_action)

        # 구분선 추가
        view_menu.addSeparator()

        # 창 크기 초기화 액션
        reset_size_action = QAction("창 크기 초기화", self)
        reset_size_action.triggered.connect(self._reset_window_size)
        view_menu.addAction(reset_size_action)

        # 창 크기 초기화 (중간) 액션 추가
        reset_size_medium_action = QAction("창 크기 초기화(중간)", self)
        reset_size_medium_action.triggered.connect(self._reset_window_size_medium)
        view_menu.addAction(reset_size_medium_action)

        # 도움말 메뉴
        help_menu = self.menuBar().addMenu("도움말")

        # 정보 액션
        about_action = QAction("정보", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _add_screens(self):
        """화면 추가 (지연 로딩 방식)"""
        # 대시보드 화면만 먼저 로드 (기본 화면)
        dashboard_screen = DashboardScreen()
        self.stack_widget.addWidget(dashboard_screen)
        self._screen_widgets['대시보드'] = dashboard_screen

        # 나머지 화면들은 지연 로딩을 위해 None으로 초기화
        self._screen_widgets['차트 뷰'] = None
        self._screen_widgets['종목 스크리닝'] = None
        self._screen_widgets['매매전략 관리'] = None
        self._screen_widgets['백테스팅'] = None
        self._screen_widgets['실시간 거래'] = None
        self._screen_widgets['포트폴리오 구성'] = None
        self._screen_widgets['모니터링/알림'] = None
        self._screen_widgets['설정'] = None

        self._log_info("대시보드 화면만 초기화 완료, 나머지는 지연 로딩됩니다")

    def _add_placeholder_screens(self, screens):
        """임시 화면 추가"""
        # 각 화면에 대한 임시 위젯 생성

        for screen_name in screens:
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)

            from PyQt6.QtWidgets import QLabel
            label = QLabel(f"{screen_name} 화면 (구현 예정)")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)

            self.stack_widget.addWidget(placeholder)

    def _change_screen(self, screen_name):
        """
        화면 전환 (지연 로딩 방식)

        Args:
            screen_name (str): 화면 이름
        """
        self._log_info(f"화면 전환 요청: {screen_name}")

        # 현재 활성 화면에서 차트뷰인 경우 업데이트 일시정지
        current_widget = self.stack_widget.currentWidget()
        if current_widget:
            # 차트뷰 화면인지 확인하고 일시정지
            try:
                if hasattr(current_widget, 'pause_chart_updates'):
                    current_widget.pause_chart_updates()
            except Exception as e:
                self._log_warning(f"이전 화면 일시정지 중 오류: {e}")

        # 화면 이름 매핑
        screen_mapping = {
            "dashboard": "대시보드",
            "chart_view": "차트 뷰",
            "screener": "종목 스크리닝",
            "strategy": "매매전략 관리",
            "backtest": "백테스팅",
            "trading": "실시간 거래",
            "portfolio": "포트폴리오 구성",
            "monitoring": "모니터링/알림",
            "settings": "설정"
        }

        mapped_name = screen_mapping.get(screen_name, screen_name)

        # 해당 화면이 이미 로드되었는지 확인
        if self._screen_widgets.get(mapped_name) is None:
            self._log_info(f"{mapped_name} 화면 지연 로딩 중...")

            self._load_screen_lazy(mapped_name)

        # 화면 전환
        widget = self._screen_widgets.get(mapped_name)
        if widget:
            index = self.stack_widget.indexOf(widget)
            if index >= 0:
                self.stack_widget.setCurrentIndex(index)
                self._log_info(f"{mapped_name} 화면으로 전환 완료")

                # 차트뷰 화면으로 전환한 경우 업데이트 재개
                try:
                    if hasattr(widget, 'resume_chart_updates'):
                        widget.resume_chart_updates()
                except Exception as e:
                    self._log_warning(f"차트뷰 업데이트 재개 중 오류: {e}")

            else:
                self._log_error(f"{mapped_name} 화면을 스택에서 찾을 수 없습니다")

        else:
            self._log_error(f"{mapped_name} 화면 로딩 실패")

    def _load_screen_lazy(self, screen_name):
        """지연 로딩으로 화면 생성"""
        try:
            if screen_name == "차트 뷰":
                self._log_info("차트뷰 화면 로딩 중...")

                from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen
                screen = ChartViewScreen()

            elif screen_name == "종목 스크리닝":
                from upbit_auto_trading.ui.desktop.screens.asset_screener.asset_screener_screen import AssetScreenerScreen
                screen = AssetScreenerScreen()

            elif screen_name == "매매전략 관리":
                # 기존 탭 구조 유지하면서 전략 메이커 탭에만 MVP 패턴 적용 (TASK-13)
                from upbit_auto_trading.ui.desktop.screens.strategy_management.strategy_management_screen import StrategyManagementScreen
                screen = StrategyManagementScreen()

                # MVP Container를 전략 관리 화면에 전달 (전략 메이커 탭에서 사용)
                if self.mvp_container and hasattr(screen, 'set_mvp_container'):
                    screen.set_mvp_container(self.mvp_container)
                    self._log_info("✅ 기존 탭 구조 유지하며 MVP Container 주입 완료")

                else:
                    self._log_info("기존 전략 관리 화면 사용 (탭 구조 유지)")

                # 백테스팅 요청 시그널 연결 (시그널이 있는 경우)
                if hasattr(screen, 'backtest_requested'):
                    screen.backtest_requested.connect(self._on_backtest_requested)
                else:
                    self._log_warning("StrategyManagementScreen에 backtest_requested 시그널이 없습니다")

            elif screen_name == "백테스팅":
                from upbit_auto_trading.ui.desktop.screens.backtesting.backtesting_screen import BacktestingScreen
                screen = BacktestingScreen()

            elif screen_name == "실시간 거래":
                from upbit_auto_trading.ui.desktop.screens.live_trading.live_trading_screen import LiveTradingScreen
                screen = LiveTradingScreen()

            elif screen_name == "포트폴리오 구성":
                from upbit_auto_trading.ui.desktop.screens.portfolio_configuration.portfolio_configuration_screen import PortfolioConfigurationScreen
                screen = PortfolioConfigurationScreen()

            elif screen_name == "모니터링/알림":
                from upbit_auto_trading.ui.desktop.screens.monitoring_alerts.monitoring_alerts_screen import MonitoringAlertsScreen
                screen = MonitoringAlertsScreen()

            elif screen_name == "설정":
                # MVP 패턴 적용 (TASK-13: Settings MVP 구현)
                if self.mvp_container:
                    try:
                        # MVP Container를 통해 Settings Presenter와 View 생성
                        # SettingsService를 직접 전달, parent도 전달
                        settings_view, settings_presenter = self.mvp_container.create_settings_mvp(
                            settings_service=self.settings_service,
                            parent=self
                        )
                        screen = settings_view  # View가 실제 QWidget

                        # 참고: parent는 이미 MVP Container에서 설정됨
                        # screen.setParent(self)  # 불필요

                        # Presenter 초기 설정 로드
                        settings_presenter.load_initial_settings()

                        self._log_info("✅ Settings MVP 패턴 생성 완료")

                    except Exception as e:
                        self._log_error(f"❌ Settings MVP 생성 실패: {e}")
                        # 폴백: 기존 방식
                        from upbit_auto_trading.ui.desktop.screens.settings.settings_screen import SettingsScreen
                        screen = SettingsScreen(settings_service=self.settings_service, parent=self)
                        self._log_warning("⚠️ Settings 기존 방식으로 폴백")
                else:
                    # MVP Container가 없으면 기존 방식
                    from upbit_auto_trading.ui.desktop.screens.settings.settings_screen import SettingsScreen
                    screen = SettingsScreen(settings_service=self.settings_service, parent=self)
                    self._log_info("SettingsScreen에 SettingsService 주입 완료 (기존 방식)")

                # 설정 변경 시그널 연결 (테마 변경 즉시 반영)
                if hasattr(screen, 'settings_changed'):
                    screen.settings_changed.connect(self._on_settings_changed_from_screen)
                    self._log_info("SettingsScreen settings_changed 시그널 연결 완료")
                else:
                    self._log_warning("SettingsScreen에 settings_changed 시그널이 없습니다")

                # 테마 변경 시그널 연결 (즉시 반영용)
                if hasattr(screen, 'theme_changed'):
                    screen.theme_changed.connect(self._on_theme_changed_from_ui_settings)
                    self._log_info("SettingsScreen theme_changed 시그널 연결 완료")
                else:
                    self._log_warning("SettingsScreen에 theme_changed 시그널이 없습니다")

                # API 상태 변경 시그널 연결
                if hasattr(screen, 'api_status_changed'):
                    screen.api_status_changed.connect(self._on_api_status_changed)
                else:
                    self._log_warning("SettingsScreen에 api_status_changed 시그널이 없습니다")

                # DB 상태 변경 시그널 연결
                if hasattr(screen, 'db_status_changed'):
                    screen.db_status_changed.connect(self._on_db_status_changed)
                else:
                    self._log_warning("SettingsScreen에 db_status_changed 시그널이 없습니다")

            else:
                self._log_error(f"알 수 없는 화면: {screen_name}")

                return

            # 스택에 추가하고 캐시에 저장
            self.stack_widget.addWidget(screen)
            self._screen_widgets[screen_name] = screen
            self._log_info(f"{screen_name} 화면 로딩 완료")

        except Exception as e:
            self._log_error(f"{screen_name} 화면 로딩 실패: {e}")
            import traceback
            traceback.print_exc()

            # 오류 발생 시 플레이스홀더 화면 생성
            from upbit_auto_trading.ui.desktop.common.widgets.placeholder import create_placeholder_screen
            screen = create_placeholder_screen(f"{screen_name} (로딩 실패)")
            self.stack_widget.addWidget(screen)
            self._screen_widgets[screen_name] = screen

    def _toggle_theme(self):
        """테마 전환 (ThemeService 우선, 실패 시 기존 방식)"""
        if self.theme_service:
            try:
                # ThemeService를 통한 테마 전환
                new_theme = self.theme_service.toggle_theme()
                self._log_info(f"ThemeService를 통한 테마 전환 완료: {new_theme}")

                # 네비게이션 바 스타일 강제 업데이트
                self.nav_bar.update()
                self.nav_bar.repaint()
                return
            except Exception as e:
                self._log_warning(f"ThemeService 테마 전환 실패, 기존 방식 사용: {e}")

        # 기존 방식 (폴백)
        self.style_manager.toggle_theme()
        # 네비게이션 바 스타일 강제 업데이트
        self.nav_bar.update()
        self.nav_bar.repaint()
        # 테마 상태 저장
        self._save_theme()

        # 전역 테마 변경 알림 발송
        try:
            from upbit_auto_trading.ui.desktop.common.theme_notifier import get_theme_notifier
            theme_notifier = get_theme_notifier()
            theme_notifier.notify_theme_changed()
        except Exception as e:
            self._log_warning(f"테마 변경 알림 실패: {e}")

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
        """설정 화면에서 설정 변경 시그널을 받았을 때 처리 (테마 변경 등)"""
        self._log_info("설정 화면에서 설정 변경 시그널 수신")

        # 테마가 변경되었을 수 있으므로 다시 로드
        self._load_theme()

        # 네비게이션 바 스타일 강제 업데이트
        if hasattr(self, 'nav_bar') and self.nav_bar:
            self.nav_bar.update()
            self.nav_bar.repaint()

        # 전역 테마 변경 알림 발송 (기존 컴포넌트와의 호환성)
        try:
            from upbit_auto_trading.ui.desktop.common.theme_notifier import get_theme_notifier
            theme_notifier = get_theme_notifier()
            theme_notifier.notify_theme_changed()
            self._log_info("설정 변경으로 인한 테마 알림 발송 완료")
        except Exception as e:
            self._log_warning(f"설정 변경 테마 알림 실패: {e}")

    def _on_theme_changed_from_ui_settings(self, theme_name: str):
        """UI 설정에서 테마 변경 시그널을 받았을 때 처리"""
        self._log_info(f"🎨 UI 설정에서 테마 변경 시그널 수신: {theme_name}")

        # ThemeService 상태 확인
        if self.theme_service:
            self._log_info(f"✅ ThemeService 사용 가능: {type(self.theme_service).__name__}")
            try:
                current_theme = self.theme_service.get_current_theme()
                self._log_info(f"🔍 현재 테마: {current_theme} → 변경 요청: {theme_name}")

                success = self.theme_service.set_theme(theme_name)
                if success:
                    new_theme = self.theme_service.get_current_theme()
                    self._log_info(f"✅ ThemeService를 통한 테마 적용 완료: {new_theme}")

                else:
                    self._log_warning(f"❌ ThemeService 테마 적용 실패: {theme_name}")

            except Exception as e:
                self._log_warning(f"❌ ThemeService 테마 적용 중 오류: {e}")
        else:
            # ThemeService가 없으면 기존 방식으로 폴백
            self._log_warning("⚠️ ThemeService가 None - 기존 방식으로 테마 적용")

            self._load_theme()

        # 네비게이션 바 스타일 강제 업데이트
        if hasattr(self, 'nav_bar') and self.nav_bar:
            self.nav_bar.update()
            self.nav_bar.repaint()
            self._log_info("🔄 네비게이션 바 스타일 강제 업데이트 완료")

        # 메인 윈도우 전체 업데이트
        self.update()
        self.repaint()
        self._log_info("🔄 메인 윈도우 전체 업데이트 완료")
        if hasattr(self, 'nav_bar') and self.nav_bar:
            self.nav_bar.update()
            self.nav_bar.repaint()

    def _load_theme(self):
        """저장된 테마 로드 (ThemeService 우선, 실패 시 기존 방식)"""
        if self.theme_service:
            try:
                # ThemeService를 통한 현재 테마 적용
                self.theme_service.apply_current_theme()
                current_theme = self.theme_service.get_current_theme()
                self._log_info(f"ThemeService를 통한 테마 로드 완료: {current_theme}")

                return
            except Exception as e:
                self._log_warning(f"ThemeService 테마 로드 실패, 기존 방식 사용: {e}")

        # 기존 방식 (폴백)
        theme_name = "light"  # 기본값

        if self.settings_service:
            try:
                # SettingsService를 통한 UI 설정 로드
                ui_config = self.settings_service.get_ui_config()
                theme_name = ui_config.theme
                self._log_info(f"SettingsService에서 테마 로드: {theme_name}")

            except Exception as e:
                self._log_warning(f"SettingsService 테마 로드 실패, ConfigLoader 시도: {e}")

                # ConfigLoader 폴백 시도
                if self.di_container:
                    try:
                        from upbit_auto_trading.infrastructure.config.loaders.config_loader import ConfigLoader
                        config_loader = self.di_container.resolve(ConfigLoader)
                        config = config_loader.get_config()
                        theme_name = config.ui.theme
                        self._log_info(f"ConfigLoader에서 테마 로드: {theme_name}")

                    except Exception as e2:
                        self._log_warning(f"ConfigLoader 테마 로드 실패, QSettings 사용: {e2}")
                        settings = QSettings("UpbitAutoTrading", "MainWindow")
                        theme_name = settings.value("theme", "light")
                else:
                    # QSettings 폴백
                    settings = QSettings("UpbitAutoTrading", "MainWindow")
                    theme_name = settings.value("theme", "light")
        else:
            # 기존 방식 (호환성 유지)
            settings = QSettings("UpbitAutoTrading", "MainWindow")
            theme_name = settings.value("theme", "light")

        # Theme 열거형으로 변환 및 적용
        try:
            from upbit_auto_trading.ui.desktop.common.styles.style_manager import Theme
            if theme_name == "dark":
                self.style_manager.set_theme(Theme.DARK)
            else:
                self.style_manager.set_theme(Theme.LIGHT)
        except Exception as e:
            self._log_warning(f"테마 적용 실패: {e}")

    def _save_theme(self):
        """현재 테마 저장 (SettingsService 우선, 실패 시 QSettings 폴백)"""
        if self.settings_service:
            try:
                theme_name = self.style_manager.current_theme.value
                self.settings_service.update_ui_setting("theme", theme_name)
                self._log_info(f"SettingsService에 테마 저장: {theme_name}")

                return
            except Exception as e:
                self._log_warning(f"SettingsService 테마 저장 실패, QSettings 사용: {e}")

        # 폴백: QSettings 사용
        settings = QSettings("UpbitAutoTrading", "MainWindow")
        try:
            theme_name = self.style_manager.current_theme.value
            settings.setValue("theme", theme_name)
        except Exception as e:
            # 오류 발생 시 기본값 저장
            self._log_warning(f"테마 저장 오류, 기본값 저장: {e}")
            settings.setValue("theme", "light")

    def _reset_window_size(self):
        """창 크기 초기화"""
        # 현재 위치 저장
        current_pos = self.pos()

        # 기본 크기로 초기화 (위치는 현재 위치 유지)
        self.resize(1280, 720)

        # 모든 스플리터와 차트들을 다시 업데이트
        self._update_all_widgets()

    def _reset_window_size_medium(self):
        """창 크기 초기화 (중간 크기)"""
        # 현재 위치 저장
        current_pos = self.pos()

        # 중간 크기로 초기화 (첨부 이미지의 해상도)
        self.resize(1600, 1000)

        # 모든 스플리터와 차트들을 다시 업데이트
        self._update_all_widgets()

        self._log_info("창 크기를 중간 크기(1600x1000)로 초기화했습니다")

    def _update_all_widgets(self):
        """모든 위젯 업데이트 (IL 스마트 로깅 적용)"""
        # stack_widget이 초기화되지 않은 경우 안전하게 처리
        if not hasattr(self, 'stack_widget') or self.stack_widget is None:
            self._log_debug("stack_widget이 아직 초기화되지 않아 위젯 업데이트를 건너뜁니다")

            return

        try:
            # 현재 화면의 모든 위젯들을 업데이트
            current_widget = self.stack_widget.currentWidget()
            if current_widget:
                current_widget.update()
                current_widget.repaint()

                # 모든 자식 위젯들 업데이트 (특히 차트 위젯들)
                for child in current_widget.findChildren(QWidget):
                    child.update()
                    child.repaint()

                    # 스플리터가 있다면 크기 재조정
                    try:
                        from PyQt6.QtWidgets import QSplitter
                        if isinstance(child, QSplitter):
                            child.refresh()
                    except Exception as e:
                        self._log_debug(f"스플리터 업데이트 중 오류: {e}")

                # 레이아웃 강제 업데이트
                layout = current_widget.layout()
                if layout:
                    layout.update()
                    layout.activate()

                self._log_debug("모든 위젯 업데이트 완료")

            else:
                self._log_debug("현재 위젯이 없어 업데이트를 건너뜁니다")

        except Exception as e:
            self._log_error(f"위젯 업데이트 중 오류 발생: {e}")
            import traceback
            self._log_debug(f"위젯 업데이트 오류 상세: {traceback.format_exc()}")

    def showEvent(self, a0):
        """
        윈도우 표시 이벤트 처리

        Args:
            a0: 표시 이벤트
        """
        super().showEvent(a0)

        # 위젯들이 제대로 표시되도록 지연 후 여러 번 업데이트
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._update_all_widgets)
        QTimer.singleShot(300, self._update_all_widgets)
        QTimer.singleShot(500, self._update_all_widgets)

    def resizeEvent(self, a0):
        """
        윈도우 리사이즈 이벤트 처리

        Args:
            a0: 리사이즈 이벤트
        """
        super().resizeEvent(a0)

        # 리사이즈 후 위젯들 업데이트
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self._update_all_widgets)

    def _show_about_dialog(self):
        """정보 대화상자 표시"""
        QMessageBox.about(
            self,
            "업비트 자동매매 시스템",
            "업비트 자동매매 시스템 v1.0.0\n\n"
            "업비트 API를 활용한 암호화폐 자동 거래 시스템입니다.\n"
            "© 2025 업비트 자동매매 시스템"
        )

    def _load_settings(self):
        """설정 로드 (SettingsService 우선, 실패 시 QSettings 폴백)"""
        if self.settings_service:
            try:
                # SettingsService를 통한 창 상태 로드
                window_state = self.settings_service.load_window_state()
                if window_state:
                    # 창 크기 및 위치 복원
                    self.resize(window_state.get("width", 1280), window_state.get("height", 720))
                    if window_state.get("x") is not None and window_state.get("y") is not None:
                        self.move(window_state["x"], window_state["y"])
                    if window_state.get("maximized", False):
                        self.showMaximized()
                    self._log_info("SettingsService를 통한 창 상태 로드 완료")

                    return
                else:
                    self._log_info("저장된 창 상태가 없어 기본값 사용")

            except Exception as e:
                self._log_warning(f"SettingsService 창 상태 로드 실패, QSettings 사용: {e}")

        # 폴백: QSettings 사용
        settings = QSettings("UpbitAutoTrading", "MainWindow")
        size = settings.value("size", QSize(1280, 720))
        position = settings.value("position", QPoint(100, 100))
        self.resize(size)
        self.move(position)

    def _save_settings(self):
        """설정 저장 (SettingsService 우선, 실패 시 QSettings 폴백)"""
        if self.settings_service:
            try:
                # SettingsService를 통한 창 상태 저장
                self.settings_service.save_window_state(
                    x=self.pos().x(),
                    y=self.pos().y(),
                    width=self.size().width(),
                    height=self.size().height(),
                    maximized=self.isMaximized()
                )
                self._log_info("SettingsService를 통한 창 상태 저장 완료")

                return
            except Exception as e:
                self._log_warning(f"SettingsService 창 상태 저장 실패, QSettings 사용: {e}")

        # 폴백: QSettings 사용
        settings = QSettings("UpbitAutoTrading", "MainWindow")
        settings.setValue("size", self.size())
        settings.setValue("position", self.pos())

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

            # 백테스팅 화면으로 전환
            self._change_screen("backtest")

            # 백테스팅 화면에 전략 ID 전달
            backtest_screen = self._screen_widgets.get("백테스팅")
            if backtest_screen:
                # 백테스팅 설정 패널에 전략 ID 설정
                if hasattr(backtest_screen, 'setup_panel'):
                    setup_panel = backtest_screen.setup_panel

                    # 전략 목록 새로고침
                    if hasattr(setup_panel, 'refresh_strategy_list'):
                        setup_panel.refresh_strategy_list()

                    # 해당 전략 선택
                    if hasattr(setup_panel, 'strategy_selector'):
                        for i in range(setup_panel.strategy_selector.count()):
                            if setup_panel.strategy_selector.itemData(i) == strategy_id:
                                setup_panel.strategy_selector.setCurrentIndex(i)
                                break

                self._log_info(f"백테스팅 화면에 전략 ID 설정 완료: {strategy_id}")

            else:
                self._log_error("백테스팅 화면을 찾을 수 없습니다")

        except Exception as e:
            self._log_error(f"백테스팅 요청 처리 실패: {e}")
            import traceback
            traceback.print_exc()

    def _on_api_status_changed(self, connected):
        """API 연결 상태 변경 시 호출되는 메서드"""
        try:
            # 상태바의 API 연결 상태 업데이트
            if hasattr(self, 'status_bar'):
                self.status_bar.set_api_status(connected)
                self._log_info(f"API 연결 상태 업데이트: {'연결됨' if connected else '연결 끊김'}")

            else:
                self._log_warning("상태바를 찾을 수 없습니다")

        except Exception as e:
            self._log_error(f"API 상태 업데이트 실패: {e}")

    def _on_api_refresh_requested(self):
        """API 상태 새로고침 요청 처리"""
        try:
            self._log_info("사용자가 API 상태 새로고침을 요청했습니다")

            # 상태바에 확인 중 표시
            if hasattr(self, 'status_bar'):
                self.status_bar.set_api_status(None)  # 확인 중 상태

            # 백그라운드에서 API 연결 테스트 수행
            self._perform_background_api_test()

        except Exception as e:
            self._log_error(f"API 새로고침 요청 처리 실패: {e}")

    def _perform_background_api_test(self):
        """백그라운드에서 API 연결 테스트 수행"""
        try:
            self._log_info("사용자 요청으로 API 연결 상태 확인 중...")

            # DI Container가 있는 경우 API 키 서비스를 통한 실제 연결 테스트
            if self.di_container:
                try:
                    api_service = self.di_container.resolve(IApiKeyService)
                    if api_service:
                        # 실제 API 연결 테스트 수행
                        try:
                            # API 키 로드
                            api_keys = api_service.load_api_keys()

                            if not api_keys or not any(api_keys):
                                # API 키가 없음
                                if hasattr(self, 'status_bar'):
                                    self.status_bar.set_api_status(False)
                                self._log_warning("API 키가 설정되지 않았습니다")

                                from upbit_auto_trading.infrastructure.monitoring import mark_api_failure
                                mark_api_failure()
                                return

                            # API 키가 있으면 실제 통신 테스트
                            access_key, secret_key, _ = api_keys
                            if not access_key or not secret_key:
                                # 키가 불완전함
                                if hasattr(self, 'status_bar'):
                                    self.status_bar.set_api_status(False)
                                self._log_warning("API 키 정보가 불완전합니다")

                                from upbit_auto_trading.infrastructure.monitoring import mark_api_failure
                                mark_api_failure()
                                return

                            # test_api_connection 메서드 사용 (올바른 메서드명)
                            success, message, account_info = api_service.test_api_connection(access_key, secret_key)

                            # 상태바 업데이트
                            if hasattr(self, 'status_bar'):
                                self.status_bar.set_api_status(success)

                            # 모니터링에 결과 기록
                            from upbit_auto_trading.infrastructure.monitoring import mark_api_success, mark_api_failure
                            if success:
                                mark_api_success()
                                self._log_info(f"✅ API 연결 테스트 성공: {message}")
                            else:
                                mark_api_failure()
                                self._log_warning(f"❌ API 연결 테스트 실패: {message}")
                            return

                        except Exception as e:
                            # API 테스트 중 예외 발생
                            self._log_error(f"API 연결 테스트 중 오류: {e}")

                            # 실패 상태로 설정
                            if hasattr(self, 'status_bar'):
                                self.status_bar.set_api_status(False)

                            # 모니터링에 실패 기록
                            from upbit_auto_trading.infrastructure.monitoring import mark_api_failure
                            mark_api_failure()
                            return

                    else:
                        self._log_warning("DI Container에서 API 키 서비스를 resolve할 수 없습니다")

                except Exception as e:
                    self._log_error(f"DI Container를 통한 API 서비스 resolve 실패: {e}")            # 폴백: 직접 ApiKeyService 생성하여 테스트
            self._log_info("DI Container 실패, 직접 API 키 서비스 생성으로 폴백")
            try:
                from upbit_auto_trading.infrastructure.services.api_key_service import ApiKeyService
                from upbit_auto_trading.infrastructure.repositories.sqlite_secure_keys_repository import SqliteSecureKeysRepository
                from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
                from upbit_auto_trading.infrastructure.configuration import PathServiceFactory

                # DDD 서비스를 통한 설정 DB 경로 가져오기
                path_service = PathServiceFactory.get_path_service()
                current_paths = db_path_service.get_all_paths()
                settings_db_path = current_paths.get('settings', 'd:/projects/upbit-autotrader-vscode/data/settings.sqlite3')

                # DatabaseManager 생성 후 Repository 주입으로 ApiKeyService 생성
                db_manager = DatabaseManager({"settings": settings_db_path})
                repo = SqliteSecureKeysRepository(db_manager)
                api_key_service = ApiKeyService(repo)

                # API 키 로드 및 테스트
                api_keys = api_key_service.load_api_keys()

                if not api_keys or not any(api_keys):
                    # API 키가 없음
                    if hasattr(self, 'status_bar'):
                        self.status_bar.set_api_status(False)
                    self._log_warning("API 키가 설정되지 않았습니다")

                    from upbit_auto_trading.infrastructure.monitoring import mark_api_failure
                    mark_api_failure()
                    return

                # API 키가 있으면 실제 통신 테스트
                access_key, secret_key, _ = api_keys
                if not access_key or not secret_key:
                    # 키가 불완전함
                    if hasattr(self, 'status_bar'):
                        self.status_bar.set_api_status(False)
                    self._log_warning("API 키 정보가 불완전합니다")

                    from upbit_auto_trading.infrastructure.monitoring import mark_api_failure
                    mark_api_failure()
                    return

                # 실제 API 테스트
                success, message, account_info = api_key_service.test_api_connection(access_key, secret_key)

                # 상태바 업데이트
                if hasattr(self, 'status_bar'):
                    self.status_bar.set_api_status(success)

                # 모니터링에 결과 기록
                from upbit_auto_trading.infrastructure.monitoring import mark_api_success, mark_api_failure
                if success:
                    mark_api_success()
                    self._log_info(f"✅ API 연결 테스트 성공: {message}")
                else:
                    mark_api_failure()
                    self._log_warning(f"❌ API 연결 테스트 실패: {message}")

            except Exception as e:
                # 폴백도 실패
                self._log_error(f"폴백 API 테스트도 실패: {e}")

                # 실패 상태로 설정
                if hasattr(self, 'status_bar'):
                    self.status_bar.set_api_status(False)

                # 모니터링에 실패 기록
                from upbit_auto_trading.infrastructure.monitoring import mark_api_failure
                mark_api_failure()

        except Exception as e:
            self._log_error(f"백그라운드 API 테스트 실패: {e}")

            # 예외 발생 시 연결 끊김 상태로 설정
            if hasattr(self, 'status_bar'):
                self.status_bar.set_api_status(False)

            # 모니터링에 실패 기록
            from upbit_auto_trading.infrastructure.monitoring import mark_api_failure
            mark_api_failure()

    def _on_db_status_changed(self, connected):
        """DB 연결 상태 변경 시 호출되는 메서드"""
        try:
            # 상태바의 DB 연결 상태 업데이트
            if hasattr(self, 'status_bar'):
                self.status_bar.set_db_status(connected)
                self._log_info(f"DB 연결 상태 업데이트: {'연결됨' if connected else '연결 끊김'}")

            else:
                self._log_warning("상태바를 찾을 수 없습니다")

        except Exception as e:
            self._log_error(f"DB 상태 업데이트 실패: {e}")

    def _check_initial_db_status(self):
        """애플리케이션 시작 시 DB 연결 상태 확인 - DatabaseHealthService 활용"""
        try:
            if self.db_health_service:
                # 새로운 DatabaseHealthService 사용
                self._log_info("🔍 DatabaseHealthService를 통한 DB 건강 검사 시작")

                # 비동기 호출을 동기적으로 처리 (startup 시점이므로 안전)
                import asyncio

                # 기존 이벤트 루프가 있는지 확인
                try:
                    loop = asyncio.get_running_loop()
                    # 이미 실행 중인 루프가 있으면 태스크로 스케줄링
                    task = loop.create_task(self._async_check_db_health())
                    self._log_info("📅 기존 이벤트 루프에 DB 건강 검사 태스크 스케줄링")
                except RuntimeError:
                    # 실행 중인 루프가 없으면 새로 실행
                    db_is_healthy = asyncio.run(self.db_health_service.check_startup_health())
                    self._update_db_status_display(db_is_healthy)

            else:
                # 폴백: 기존 방식 사용
                self._log_warning("⚠️ DatabaseHealthService 없음, 기존 방식으로 DB 상태 확인")
                self._check_db_status_legacy()

        except Exception as e:
            self._log_error(f"❌ DB 상태 확인 실패: {e}")
            # 오류 발생 시 연결 끊김으로 설정
            if hasattr(self, 'status_bar'):
                self.status_bar.set_db_status(False)

    async def _async_check_db_health(self):
        """비동기 DB 건강 검사"""
        try:
            db_is_healthy = await self.db_health_service.check_startup_health()
            self._update_db_status_display(db_is_healthy)
        except Exception as e:
            self._log_error(f"❌ 비동기 DB 건강 검사 실패: {e}")
            self._update_db_status_display(False)

    def _update_db_status_display(self, is_healthy: bool):
        """DB 상태를 StatusBar에 반영"""
        try:
            if hasattr(self, 'status_bar'):
                self.status_bar.set_db_status(is_healthy)
                status_text = "연결됨" if is_healthy else "고장남"
                self._log_info(f"📊 DB 상태 업데이트: {status_text}")

            else:
                self._log_warning("⚠️ StatusBar 없음 - DB 상태 표시 불가")
        except Exception as e:
            self._log_error(f"❌ DB 상태 표시 실패: {e}")

    def _check_db_status_legacy(self):
        """애플리케이션 시작 시 DB 연결 상태 확인 - DDD 서비스 활용"""
        try:
            # DDD 서비스를 통한 DB 경로 가져오기
            path_service = PathServiceFactory.get_path_service()
            current_paths = path_service.get_all_database_paths()

            from pathlib import Path
            db_path = Path(current_paths.get('settings', 'd:/projects/upbit-autotrader-vscode/data/settings.sqlite3'))

            db_connected = False
            show_warning = False
            warning_message = ""

            # DB 파일 존재 여부 확인
            if not db_path.exists():
                warning_message = f"DB 파일이 존재하지 않습니다.\n경로: {db_path}\n\n새로 설치했거나 파일이 손상되었을 수 있습니다."
                show_warning = True
                self._log_error(f"DB 파일 없음: {db_path.name}")

            else:
                try:
                    # 실제 DB 연결 테스트
                    with sqlite3.connect(str(db_path)) as conn:
                        cursor = conn.cursor()
                        # 간단한 쿼리로 연결 확인
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                        result = cursor.fetchone()

                        if result:
                            db_connected = True
                            self._log_info(f"DB 연결 성공: {db_path.name}")

                        else:
                            warning_message = f"DB 파일이 비어있거나 손상되었습니다.\n경로: {db_path}\n\n데이터베이스를 다시 초기화해야 할 수 있습니다."
                            show_warning = True
                            self._log_warning(f"DB가 비어있음: {db_path.name}")

                except Exception as e:
                    warning_message = f"DB 연결에 실패했습니다.\n경로: {db_path}\n오류: {str(e)}\n\n데이터베이스 파일이 손상되었을 수 있습니다."
                    show_warning = True
                    self._log_error(f"DB 연결 실패: {str(e)}")
                    db_connected = False

            # 상태바 DB 상태 설정
            if hasattr(self, 'status_bar'):
                self.status_bar.set_db_status(db_connected)
                self._log_info(f"초기 DB 상태: {'연결됨' if db_connected else '연결 끊김'}")

            # DB 문제가 있는 경우 콘솔에만 로그 출력 (알림 비활성화)
            if show_warning:
                self._log_warning(f"DB 상태 경고: {warning_message}")

                # 사용자 알림은 표시하지 않음 (조용한 체크)

        except Exception as e:
            self._log_error(f"초기 DB 상태 확인 실패: {e}")
            # 오류 발생 시 연결 끊김으로 설정
            if hasattr(self, 'status_bar'):
                self.status_bar.set_db_status(False)

    def _check_initial_api_status(self):
        """애플리케이션 시작 시 API 키 존재 여부 및 연결 상태 확인 - DDD 서비스 활용"""
        try:
            # ApiKeyService를 통한 통합된 API 키 상태 확인
            from upbit_auto_trading.infrastructure.services.api_key_service import ApiKeyService
            from upbit_auto_trading.infrastructure.repositories.sqlite_secure_keys_repository import SqliteSecureKeysRepository
            from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

            # DDD 서비스를 통한 설정 DB 경로 가져오기
            path_service = PathServiceFactory.get_path_service()
            current_paths = path_service.get_all_database_paths()
            settings_db_path = current_paths.get('settings', 'd:/projects/upbit-autotrader-vscode/data/settings.sqlite3')

            # DatabaseManager 생성 후 Repository 주입으로 ApiKeyService 생성
            db_manager = DatabaseManager({"settings": settings_db_path})
            repo = SqliteSecureKeysRepository(db_manager)
            api_key_service = ApiKeyService(repo)

            # API 키 로드 시도
            api_keys = api_key_service.load_api_keys()

            if not api_keys or not any(api_keys):
                # API 키가 없거나 로드 실패
                if hasattr(self, 'status_bar'):
                    self.status_bar.set_api_status(False)
                self._log_warning("API 키 파일이 없습니다. 설정에서 API 키를 등록해주세요")

                return

            # API 키가 있으면 실제 통신 테스트
            access_key, secret_key, _ = api_keys
            if not access_key or not secret_key:
                # 로드는 되었지만 키가 비어있음
                if hasattr(self, 'status_bar'):
                    self.status_bar.set_api_status(False)
                self._log_warning("API 키 정보가 불완전합니다")

                return

            self._log_info("API 키 파일 발견 - 연결 테스트 중...")

            # ApiKeyService를 통한 통합된 API 테스트
            success, message, account_info = api_key_service.test_api_connection(access_key, secret_key)

            if success:
                # API 통신 성공
                if hasattr(self, 'status_bar'):
                    self.status_bar.set_api_status(True)
                self._log_info("API 연결 테스트 성공 - 정상 연결됨")

            else:
                # API 통신 실패
                if hasattr(self, 'status_bar'):
                    self.status_bar.set_api_status(False)
                self._log_error(f"API 연결 테스트 실패: {message}")

        except Exception as e:
            # 전체적인 오류
            if hasattr(self, 'status_bar'):
                self.status_bar.set_api_status(False)
            self._log_error(f"API 상태 확인 중 오류: {str(e)}")
            # 조용한 테스트이므로 사용자에게 팝업은 표시하지 않음
            self._log_error(f"초기 API 상태 확인 실패: {e}")
            # 오류 발생 시 연결 끊김으로 설정
            if hasattr(self, 'status_bar'):
                self.status_bar.set_api_status(False)
