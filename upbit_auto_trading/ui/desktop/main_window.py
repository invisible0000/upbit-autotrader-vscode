"""
메인 윈도우 모듈
"""
import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QSettings, QSize, QPoint
from PyQt6.QtGui import QIcon, QAction

# 공통 위젯 임포트
from upbit_auto_trading.ui.desktop.common.widgets.navigation_bar import NavigationBar
from upbit_auto_trading.ui.desktop.common.widgets.status_bar import StatusBar
from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager, Theme

# 화면 임포트 (나중에 구현 예정)
# from upbit_auto_trading.ui.desktop.screens.dashboard.dashboard_screen import DashboardScreen
# from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen


class MainWindow(QMainWindow):
    """
    메인 윈도우 클래스
    
    애플리케이션의 메인 윈도우입니다.
    """
    
    def __init__(self):
        """초기화"""
        super().__init__()
        
        self.setWindowTitle("업비트 자동매매 시스템")
        self.setMinimumSize(1280, 720)  # 요구사항 문서의 최소 해상도 요구사항 적용
        
        # 설정 로드
        self._load_settings()
        
        # UI 설정
        self._setup_ui()
        
        # 스타일 적용
        self.style_manager = StyleManager()
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
        
        # 화면 추가 (나중에 구현 예정)
        # self._add_screens()
        
        # 임시 화면 추가
        self._add_placeholder_screens()
        
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
        
        # 도움말 메뉴
        help_menu = self.menuBar().addMenu("도움말")
        
        # 정보 액션
        about_action = QAction("정보", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
    
    def _add_screens(self):
        """화면 추가 (나중에 구현 예정)"""
        # 대시보드 화면
        # dashboard_screen = DashboardScreen()
        # self.stack_widget.addWidget(dashboard_screen)
        
        # 차트 뷰 화면
        # chart_view_screen = ChartViewScreen()
        # self.stack_widget.addWidget(chart_view_screen)
        
        # 기타 화면들...
    
    def _add_placeholder_screens(self):
        """임시 화면 추가"""
        # 각 화면에 대한 임시 위젯 생성
        screens = [
            "대시보드", "차트 뷰", "종목 스크리닝", "매매 전략 관리",
            "백테스팅", "실시간 거래", "포트폴리오 구성", "모니터링 및 알림", "설정"
        ]
        
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
        화면 전환
        
        Args:
            screen_name (str): 화면 이름
        """
        # 네비게이션 바 활성 화면 설정
        self.nav_bar.set_active_screen(screen_name)
        
        # 스택 위젯 인덱스 설정
        if screen_name == "dashboard":
            self.stack_widget.setCurrentIndex(0)
        elif screen_name == "chart_view":
            self.stack_widget.setCurrentIndex(1)
        elif screen_name == "screener":
            self.stack_widget.setCurrentIndex(2)
        elif screen_name == "strategy":
            self.stack_widget.setCurrentIndex(3)
        elif screen_name == "backtest":
            self.stack_widget.setCurrentIndex(4)
        elif screen_name == "trading":
            self.stack_widget.setCurrentIndex(5)
        elif screen_name == "portfolio":
            self.stack_widget.setCurrentIndex(6)
        elif screen_name == "monitoring":
            self.stack_widget.setCurrentIndex(7)
        elif screen_name == "settings":
            self.stack_widget.setCurrentIndex(8)
    
    def _toggle_theme(self):
        """테마 전환"""
        self.style_manager.toggle_theme()
    
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
    
    def closeEvent(self, event):
        """
        윈도우 종료 이벤트 처리
        
        Args:
            event: 종료 이벤트
        """
        # 설정 저장
        self._save_settings()
        
        # 이벤트 수락
        event.accept()