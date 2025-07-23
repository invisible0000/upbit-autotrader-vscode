"""
매매 전략 관리 화면 - 새로운 컴포넌트 기반 전략 관리
- 전략 메이커 탭 (컴포넌트 기반)
- 백테스팅 탭
- 전략 분석 탭
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QHBoxLayout,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

# 통합 조건 관리 시스템 import
from .integrated_condition_manager import IntegratedConditionManager

class StrategyManagementScreen(QWidget):
    """컴포넌트 기반 전략 관리 화면"""
    
    # 백테스팅 요청 시그널
    backtest_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 매매 전략 관리")
        
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        
        # 탭들 생성
        self.strategy_maker_tab = self.create_strategy_maker_tab()
        self.backtest_tab = self.create_backtest_tab()
        self.analysis_tab = self.create_analysis_tab()
        
        # 탭 추가
        self.tab_widget.addTab(self.strategy_maker_tab, "🎯 전략 메이커")
        self.tab_widget.addTab(self.backtest_tab, "📊 백테스팅")
        self.tab_widget.addTab(self.analysis_tab, "📈 전략 분석")
        
        layout.addWidget(self.tab_widget)
        
        print("✅ 새로운 매매전략 관리 화면 초기화 완료")
    
    def create_strategy_maker_tab(self):
        """전략 메이커 탭 생성"""
        try:
            # 통합 조건 관리자를 탭으로 임베드
            condition_manager = IntegratedConditionManager()
            return condition_manager
        except Exception as e:
            print(f"❌ 통합 조건 관리자 로딩 실패: {e}")
            # 대체 위젯 생성
            fallback_widget = QWidget()
            layout = QVBoxLayout(fallback_widget)
            layout.addWidget(QLabel(f"통합 조건 관리자 로딩 실패: {e}"))
            return fallback_widget
    
    def create_backtest_tab(self):
        """백테스팅 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("백테스팅 기능")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        # TODO: 백테스팅 UI 구현
        info_label = QLabel("추후 백테스팅 기능이 여기에 구현됩니다.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_label)
        
        return widget
    
    def create_analysis_tab(self):
        """전략 분석 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("전략 분석 기능")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        # TODO: 전략 분석 UI 구현
        info_label = QLabel("추후 전략 분석 기능이 여기에 구현됩니다.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_label)
        
        return widget
    
    def refresh_all_data(self):
        """모든 데이터 새로고침"""
        try:
            print("🔄 전략 관리 데이터 새로고침 중...")
            # TODO: 각 탭의 데이터 새로고침 구현
            QMessageBox.information(self, "새로고침", "데이터가 새로고침되었습니다.")
        except Exception as e:
            print(f"❌ 데이터 새로고침 실패: {e}")
            QMessageBox.warning(self, "오류", f"데이터 새로고침 중 오류가 발생했습니다:\n{e}")
