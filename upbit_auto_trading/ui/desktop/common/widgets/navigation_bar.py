"""
네비게이션 바 위젯 모듈
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, 
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QIcon, QFont

class NavigationButton(QPushButton):
    """
    네비게이션 버튼 클래스
    
    네비게이션 바에 사용되는 버튼 위젯입니다.
    """
    
    def __init__(self, text, icon_path=None, parent=None):
        """
        초기화
        
        Args:
            text (str): 버튼 텍스트
            icon_path (str, optional): 아이콘 경로
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(parent)
        self.setText(text)
        
        if icon_path:
            self.setIcon(QIcon(icon_path))
        
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setMinimumHeight(50)
        self.setIconSize(QSize(24, 24))
        
        # 스타일은 QSS 파일에서 관리하므로 인라인 스타일 제거

class NavigationBar(QWidget):
    """
    네비게이션 바 위젯
    
    애플리케이션의 주요 화면 간 이동을 위한 네비게이션 바입니다.
    """
    
    # 화면 전환 시그널
    screen_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        초기화
        
        Args:
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(parent)
        self.setObjectName("nav-main")  # 화면 명세서의 요소 ID 활용
        self.setMinimumWidth(200)
        self.setMaximumWidth(250)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 로고 및 타이틀
        title_label = QLabel("업비트 자동매매 시스템")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setMinimumHeight(60)
        title_label.setStyleSheet("background-color: #2c3e50; color: white;")
        
        layout.addWidget(title_label)
        
        # 네비게이션 버튼
        self.btn_dashboard = NavigationButton("대시보드")
        self.btn_chart = NavigationButton("차트 뷰")
        self.btn_screener = NavigationButton("종목 스크리닝")
        self.btn_strategy = NavigationButton("매매 전략 관리")
        self.btn_backtest = NavigationButton("백테스팅")
        self.btn_trading = NavigationButton("실시간 거래")
        self.btn_portfolio = NavigationButton("포트폴리오 구성")
        self.btn_monitoring = NavigationButton("모니터링 및 알림")
        self.btn_settings = NavigationButton("설정")
        
        # 버튼 클릭 이벤트 연결
        self.btn_dashboard.clicked.connect(lambda: self.screen_changed.emit("dashboard"))
        self.btn_chart.clicked.connect(lambda: self.screen_changed.emit("chart_view"))
        self.btn_screener.clicked.connect(lambda: self.screen_changed.emit("screener"))
        self.btn_strategy.clicked.connect(lambda: self.screen_changed.emit("strategy"))
        self.btn_backtest.clicked.connect(lambda: self.screen_changed.emit("backtest"))
        self.btn_trading.clicked.connect(lambda: self.screen_changed.emit("trading"))
        self.btn_portfolio.clicked.connect(lambda: self.screen_changed.emit("portfolio"))
        self.btn_monitoring.clicked.connect(lambda: self.screen_changed.emit("monitoring"))
        self.btn_settings.clicked.connect(lambda: self.screen_changed.emit("settings"))
        
        # 버튼 추가
        layout.addWidget(self.btn_dashboard)
        layout.addWidget(self.btn_chart)
        layout.addWidget(self.btn_screener)
        layout.addWidget(self.btn_strategy)
        layout.addWidget(self.btn_backtest)
        layout.addWidget(self.btn_trading)
        layout.addWidget(self.btn_portfolio)
        layout.addWidget(self.btn_monitoring)
        
        # 여백 추가
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)
        
        # 설정 버튼은 하단에 배치
        layout.addWidget(self.btn_settings)
        
        # 기본적으로 대시보드 선택
        self.btn_dashboard.setChecked(True)
    
    def set_active_screen(self, screen_name):
        """
        활성 화면 설정
        
        Args:
            screen_name (str): 화면 이름
        """
        # 모든 버튼 선택 해제
        for button in self.findChildren(NavigationButton):
            button.setChecked(False)
        
        # 해당 화면 버튼 선택
        if screen_name == "dashboard":
            self.btn_dashboard.setChecked(True)
        elif screen_name == "chart_view":
            self.btn_chart.setChecked(True)
        elif screen_name == "screener":
            self.btn_screener.setChecked(True)
        elif screen_name == "strategy":
            self.btn_strategy.setChecked(True)
        elif screen_name == "backtest":
            self.btn_backtest.setChecked(True)
        elif screen_name == "trading":
            self.btn_trading.setChecked(True)
        elif screen_name == "portfolio":
            self.btn_portfolio.setChecked(True)
        elif screen_name == "monitoring":
            self.btn_monitoring.setChecked(True)
        elif screen_name == "settings":
            self.btn_settings.setChecked(True)