"""
대시보드 화면 모듈

이 모듈은 대시보드 화면을 구현합니다.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer

# 위젯 임포트
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.portfolio_summary_widget import PortfolioSummaryWidget
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.active_positions_widget import ActivePositionsWidget
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.market_overview_widget import MarketOverviewWidget


class DashboardScreen(QWidget):
    """
    대시보드 화면 클래스
    
    시스템 상태, 포트폴리오 성과, 활성 거래 등을 표시하는 화면입니다.
    """
    
    def __init__(self, parent=None):
        """
        초기화
        
        Args:
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(parent)
        self.setObjectName("dashboard-screen")
        
        # UI 설정
        self._setup_ui()
        
        # 타이머 설정 (5초마다 데이터 갱신)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_all_widgets)
        self.refresh_timer.start(5000)  # 5초마다 갱신
    
    def _setup_ui(self):
        """UI 설정"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 제목
        title_label = QLabel("대시보드")
        title_label.setObjectName("dashboard-title")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # 스크롤 영역 내부 위젯
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)
        
        # 상단 위젯 영역 (포트폴리오 요약)
        self.portfolio_summary_widget = PortfolioSummaryWidget()
        scroll_layout.addWidget(self.portfolio_summary_widget)
        
        # 중간 위젯 영역 (활성 거래 목록)
        self.active_positions_widget = ActivePositionsWidget()
        scroll_layout.addWidget(self.active_positions_widget)
        
        # 하단 위젯 영역 (시장 개요)
        self.market_overview_widget = MarketOverviewWidget()
        scroll_layout.addWidget(self.market_overview_widget)
        
        # 여백 추가
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_layout.addWidget(spacer)
        
        # 스크롤 영역 설정
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # 새로고침 버튼
        refresh_button = QPushButton("새로고침")
        refresh_button.setObjectName("dashboard-refresh-button")
        refresh_button.clicked.connect(self.refresh_all_widgets)
        main_layout.addWidget(refresh_button, alignment=Qt.AlignmentFlag.AlignRight)
    
    def refresh_all_widgets(self):
        """모든 위젯 새로고침"""
        try:
            self.portfolio_summary_widget.refresh_data()
            self.active_positions_widget.refresh_data()
            self.market_overview_widget.refresh_data()
        except Exception as e:
            print(f"대시보드 새로고침 중 오류 발생: {e}")
    
    def showEvent(self, event):
        """
        화면이 표시될 때 호출되는 이벤트 핸들러
        
        Args:
            event: 이벤트 객체
        """
        # 화면이 표시될 때 데이터 새로고침
        self.refresh_all_widgets()
        super().showEvent(event)
    
    def hideEvent(self, event):
        """
        화면이 숨겨질 때 호출되는 이벤트 핸들러
        
        Args:
            event: 이벤트 객체
        """
        # 화면이 숨겨질 때 타이머 중지
        self.refresh_timer.stop()
        super().hideEvent(event)