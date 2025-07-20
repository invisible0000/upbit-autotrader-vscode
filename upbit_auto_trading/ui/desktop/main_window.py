"""
메인 윈도우 모듈
"""
import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QMessageBox, QApplication, QLabel
)
from PyQt6.QtCore import Qt, QSettings, QSize, QPoint
from PyQt6.QtGui import QIcon, QAction

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
                from upbit_auto_trading.ui.desktop.screens.strategy_management.strategy_management_screen import StrategyManagementScreen
                screen = StrategyManagementScreen()
                
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