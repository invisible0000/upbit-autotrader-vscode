"""
메인 윈도우 모듈
"""
import sys
import os
import json
import sqlite3
import gc
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QMessageBox, QApplication, QLabel
)
from PyQt6.QtCore import Qt, QSettings, QSize, QPoint
from PyQt6.QtGui import QIcon, QAction

# simple_paths 시스템 import
from config.simple_paths import SimplePaths

# 공통 위젯 임포트
try:
    from upbit_auto_trading.ui.desktop.common.widgets.navigation_bar import NavigationBar
except ImportError:
    # 임시로 더미 클래스 사용
    class NavigationBar(QWidget):
        from PyQt6.QtCore import pyqtSignal
        screen_changed = pyqtSignal(str)
        def set_current_screen(self, name): pass

try:
    from upbit_auto_trading.ui.desktop.common.widgets.status_bar import StatusBar
except ImportError:
    # 임시로 더미 클래스 사용
    class StatusBar(QWidget):
        def update_current_screen(self, name): pass

try:
    from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager, Theme
except ImportError:
    # 임시로 더미 클래스 사용
    class StyleManager:
        def apply_theme(self): pass
        def get_current_theme(self): return "light"
        def set_theme(self, theme): pass
        def toggle_theme(self): pass
        @property
        def current_theme(self):
            class DummyTheme:
                value = "light"
            return DummyTheme()
    class Theme:
        LIGHT = "light"
        DARK = "dark"

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
    
    def __init__(self):
        """초기화"""
        super().__init__()
        
        # 화면 캐시 (지연 로딩용)
        self._screen_cache = {}
        self._screen_widgets = {}
        
        self.setWindowTitle("업비트 자동매매 시스템")
        self.setMinimumSize(1280, 720)  # 요구사항 문서의 최소 해상도 요구사항 적용
        
        # 설정 로드
        self._load_settings()
        
        # UI 설정
        self._setup_ui()
        
        # 스타일 적용
        self.style_manager = StyleManager()
        
        # 저장된 테마 로드
        self._load_theme()
        
        self.style_manager.apply_theme()
    
    def _setup_ui(self):
        """UI 설정"""
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃 설정
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 네비게이션 바 설정
        self.nav_bar = NavigationBar()
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
        
        # 상태 바 설정
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)
        
        # 초기 API 연결 상태 확인
        self._check_initial_api_status()
        
        # 초기 DB 연결 상태 확인
        self._check_initial_db_status()
        
        # 메뉴 바 설정
        self._setup_menu_bar()
    
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
        
        print("🏠 대시보드 화면만 초기화 완료, 나머지는 지연 로딩됩니다.")
    
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
        print(f"🔄 화면 전환 요청: {screen_name}")
        
        # 현재 활성 화면에서 차트뷰인 경우 업데이트 일시정지
        current_widget = self.stack_widget.currentWidget()
        if current_widget:
            # 차트뷰 화면인지 확인하고 일시정지
            try:
                if hasattr(current_widget, 'pause_chart_updates'):
                    current_widget.pause_chart_updates()
            except Exception as e:
                print(f"⚠️ 이전 화면 일시정지 중 오류: {e}")
        
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
            print(f"📥 {mapped_name} 화면 지연 로딩 중...")
            self._load_screen_lazy(mapped_name)
        
        # 화면 전환
        widget = self._screen_widgets.get(mapped_name)
        if widget:
            index = self.stack_widget.indexOf(widget)
            if index >= 0:
                self.stack_widget.setCurrentIndex(index)
                print(f"✅ {mapped_name} 화면으로 전환 완료")
                
                # 차트뷰 화면으로 전환한 경우 업데이트 재개
                try:
                    if hasattr(widget, 'resume_chart_updates'):
                        widget.resume_chart_updates()
                except Exception as e:
                    print(f"⚠️ 차트뷰 업데이트 재개 중 오류: {e}")
                    
            else:
                print(f"❌ {mapped_name} 화면을 스택에서 찾을 수 없습니다")
        else:
            print(f"❌ {mapped_name} 화면 로딩 실패")
    
    def _load_screen_lazy(self, screen_name):
        """지연 로딩으로 화면 생성"""
        try:
            if screen_name == "차트 뷰":
                print("📊 차트뷰 화면 로딩 중...")
                from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen
                screen = ChartViewScreen()
                
            elif screen_name == "종목 스크리닝":
                from upbit_auto_trading.ui.desktop.screens.asset_screener.asset_screener_screen import AssetScreenerScreen
                screen = AssetScreenerScreen()
                
            elif screen_name == "매매전략 관리":
                # 컴포넌트 기반 전략 관리 화면 사용
                from upbit_auto_trading.ui.desktop.screens.strategy_management.strategy_management_screen import StrategyManagementScreen
                screen = StrategyManagementScreen()
                # 백테스팅 요청 시그널 연결 (시그널이 있는 경우)
                if hasattr(screen, 'backtest_requested'):
                    screen.backtest_requested.connect(self._on_backtest_requested)
                else:
                    print("⚠️ StrategyManagementScreen에 backtest_requested 시그널이 없습니다")
                
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
                from upbit_auto_trading.ui.desktop.screens.settings.settings_screen import SettingsScreen
                screen = SettingsScreen()
                # API 상태 변경 시그널 연결
                if hasattr(screen, 'api_status_changed'):
                    screen.api_status_changed.connect(self._on_api_status_changed)
                else:
                    print("⚠️ SettingsScreen에 api_status_changed 시그널이 없습니다")
                
                # DB 상태 변경 시그널 연결
                if hasattr(screen, 'db_status_changed'):
                    screen.db_status_changed.connect(self._on_db_status_changed)
                else:
                    print("⚠️ SettingsScreen에 db_status_changed 시그널이 없습니다")
                
            else:
                print(f"❌ 알 수 없는 화면: {screen_name}")
                return
            
            # 스택에 추가하고 캐시에 저장
            self.stack_widget.addWidget(screen)
            self._screen_widgets[screen_name] = screen
            print(f"✅ {screen_name} 화면 로딩 완료")
            
        except Exception as e:
            print(f"❌ {screen_name} 화면 로딩 실패: {e}")
            import traceback
            traceback.print_exc()
            
            # 오류 발생 시 플레이스홀더 화면 생성
            from upbit_auto_trading.ui.desktop.common.widgets.placeholder import create_placeholder_screen
            screen = create_placeholder_screen(f"{screen_name} (로딩 실패)")
            self.stack_widget.addWidget(screen)
            self._screen_widgets[screen_name] = screen
    
    def _toggle_theme(self):
        """테마 전환"""
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
            print(f"⚠️ 테마 변경 알림 실패: {e}")
    
    def _load_theme(self):
        """저장된 테마 로드"""
        settings = QSettings("UpbitAutoTrading", "MainWindow")
        theme_name = settings.value("theme", "light")
        
        # Theme 열거형으로 변환
        if theme_name == "dark":
            from upbit_auto_trading.ui.desktop.common.styles.style_manager import Theme
            self.style_manager.set_theme(Theme.DARK)
        else:
            from upbit_auto_trading.ui.desktop.common.styles.style_manager import Theme
            self.style_manager.set_theme(Theme.LIGHT)
    
    def _save_theme(self):
        """현재 테마 저장"""
        settings = QSettings("UpbitAutoTrading", "MainWindow")
        try:
            theme_name = self.style_manager.current_theme.value
            settings.setValue("theme", theme_name)
        except:
            # 오류 발생 시 기본값 저장
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
        
        print("🖥️ 창 크기를 중간 크기(1600x1000)로 초기화했습니다.")
    
    def _update_all_widgets(self):
        """모든 위젯 업데이트"""
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
                except:
                    pass
            
            # 레이아웃 강제 업데이트
            layout = current_widget.layout()
            if layout:
                layout.update()
                layout.activate()
    
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
        """설정 로드"""
        settings = QSettings("UpbitAutoTrading", "MainWindow")
        
        # 윈도우 크기 및 위치 로드
        size = settings.value("size", QSize(1280, 720))
        position = settings.value("position", QPoint(100, 100))
        
        self.resize(size)
        self.move(position)
    
    def _save_settings(self):
        """설정 저장"""
        settings = QSettings("UpbitAutoTrading", "MainWindow")
        
        # 윈도우 크기 및 위치 저장
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
            print(f"🔬 백테스팅 요청 수신: 전략 ID = {strategy_id}")
            
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
                
                print(f"✅ 백테스팅 화면에 전략 ID 설정 완료: {strategy_id}")
            else:
                print("❌ 백테스팅 화면을 찾을 수 없습니다")
                
        except Exception as e:
            print(f"❌ 백테스팅 요청 처리 실패: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_api_status_changed(self, connected):
        """API 연결 상태 변경 시 호출되는 메서드"""
        try:
            # 상태바의 API 연결 상태 업데이트
            if hasattr(self, 'status_bar'):
                self.status_bar.set_api_status(connected)
                print(f"📊 API 연결 상태 업데이트: {'연결됨' if connected else '연결 끊김'}")
            else:
                print("⚠️ 상태바를 찾을 수 없습니다")
        except Exception as e:
            print(f"❌ API 상태 업데이트 실패: {e}")
    
    def _on_db_status_changed(self, connected):
        """DB 연결 상태 변경 시 호출되는 메서드"""
        try:
            # 상태바의 DB 연결 상태 업데이트
            if hasattr(self, 'status_bar'):
                self.status_bar.set_db_status(connected)
                print(f"🗄️ DB 연결 상태 업데이트: {'연결됨' if connected else '연결 끊김'}")
            else:
                print("⚠️ 상태바를 찾을 수 없습니다")
        except Exception as e:
            print(f"❌ DB 상태 업데이트 실패: {e}")
    
    def _check_initial_db_status(self):
        """애플리케이션 시작 시 DB 연결 상태 확인"""
        try:
            # simple_paths 시스템 사용
            paths = SimplePaths()
            db_path = paths.SETTINGS_DB
            
            db_connected = False
            show_warning = False
            warning_message = ""
            
            # DB 파일 존재 여부 확인
            if not db_path.exists():
                warning_message = f"DB 파일이 존재하지 않습니다.\n경로: {db_path}\n\n새로 설치했거나 파일이 손상되었을 수 있습니다."
                show_warning = True
                print(f"❌ DB 파일 없음: {db_path.name}")
            else:
                try:
                    import sqlite3
                    # 실제 DB 연결 테스트
                    with sqlite3.connect(str(db_path)) as conn:
                        cursor = conn.cursor()
                        # 간단한 쿼리로 연결 확인
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                        result = cursor.fetchone()
                        
                        if result:
                            db_connected = True
                            print(f"✅ DB 연결 성공: {db_path.name}")
                        else:
                            warning_message = f"DB 파일이 비어있거나 손상되었습니다.\n경로: {db_path}\n\n데이터베이스를 다시 초기화해야 할 수 있습니다."
                            show_warning = True
                            print(f"❌ DB가 비어있음: {db_path.name}")
                            
                except Exception as e:
                    warning_message = f"DB 연결에 실패했습니다.\n경로: {db_path}\n오류: {str(e)}\n\n데이터베이스 파일이 손상되었을 수 있습니다."
                    show_warning = True
                    print(f"❌ DB 연결 실패: {str(e)}")
                    db_connected = False
            
            # 상태바 DB 상태 설정
            if hasattr(self, 'status_bar'):
                self.status_bar.set_db_status(db_connected)
                print(f"🗄️ 초기 DB 상태: {'연결됨' if db_connected else '연결 끊김'}")
            
            # DB 문제가 있는 경우 콘솔에만 로그 출력 (알림 비활성화)
            if show_warning:
                print(f"⚠️ DB 상태 경고: {warning_message}")
                # 사용자 알림은 표시하지 않음 (조용한 체크)
            
        except Exception as e:
            print(f"❌ 초기 DB 상태 확인 실패: {e}")
            # 오류 발생 시 연결 끊김으로 설정
            if hasattr(self, 'status_bar'):
                self.status_bar.set_db_status(False)
    
    def _check_initial_api_status(self):
        """애플리케이션 시작 시 API 키 존재 여부 및 연결 상태 확인"""
        try:
            # simple_paths 시스템 사용
            paths = SimplePaths()
            api_keys_path = paths.API_CREDENTIALS_FILE
            
            # API 키 파일 존재 여부 확인
            if not os.path.exists(api_keys_path):
                # API 키 파일이 없는 경우
                if hasattr(self, 'status_bar'):
                    self.status_bar.set_api_status(False)
                print("🔑 API 키 파일이 없습니다. 설정에서 API 키를 등록해주세요.")
                return
            
            # API 키가 있는 경우 실제 통신 테스트
            print("🔑 API 키 파일 발견 - 연결 테스트 중...")
            
            try:
                from cryptography.fernet import Fernet
                
                # 새로운 secure 위치에서 암호화 키 로드
                encryption_key_path = paths.SECURE_DIR / "encryption_key.key"
                
                if not os.path.exists(encryption_key_path):
                    print("❌ 암호화 키 파일이 없습니다")
                    if hasattr(self, 'status_bar'):
                        self.status_bar.set_api_status(False)
                    return
                
                with open(encryption_key_path, "rb") as key_file:
                    encryption_key = key_file.read()
                fernet = Fernet(encryption_key)
                
                # API 키 복호화
                with open(api_keys_path, "r", encoding='utf-8') as f:
                    settings = json.load(f)
                
                if "access_key" not in settings or "secret_key" not in settings:
                    print("❌ API 키 정보가 불완전합니다")
                    if hasattr(self, 'status_bar'):
                        self.status_bar.set_api_status(False)
                    return
                
                access_key = fernet.decrypt(settings["access_key"].encode()).decode()
                secret_key = fernet.decrypt(settings["secret_key"].encode()).decode()
                
                # 실제 API 통신 테스트
                from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
                api = UpbitAPI(access_key, secret_key)
                accounts = api.get_account()
                
                # 메모리에서 키 삭제
                access_key = ""
                secret_key = ""
                gc.collect()
                
                if accounts:
                    # API 통신 성공
                    if hasattr(self, 'status_bar'):
                        self.status_bar.set_api_status(True)
                    print("✅ API 연결 테스트 성공 - 정상 연결됨")
                else:
                    # API 응답이 없음
                    if hasattr(self, 'status_bar'):
                        self.status_bar.set_api_status(False)
                    print("❌ API 연결 테스트 실패 - 계좌 정보 조회 불가")
                    
            except Exception as api_e:
                # API 통신 오류
                if hasattr(self, 'status_bar'):
                    self.status_bar.set_api_status(False)
                print(f"❌ API 연결 테스트 실패: {str(api_e)}")
                # 조용한 테스트이므로 사용자에게 팝업은 표시하지 않음
            
        except Exception as e:
            print(f"❌ 초기 API 상태 확인 실패: {e}")
            # 오류 발생 시 연결 끊김으로 설정
            if hasattr(self, 'status_bar'):
                self.status_bar.set_api_status(False)
