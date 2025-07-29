"""
매매 전략 관리 화면 - 새로운 컴포넌트 기반 전략 관리
- 트리거 빌더 탭 (조건 생성 및 관리)
- 전략 메이커 탭 (실제 매매 전략 생성)
- 백테스팅 탭
- 전략 분석 탭
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QHBoxLayout,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from upbit_auto_trading.utils.debug_logger import get_logger

# 리팩토링된 트리거 빌더 시스템 import
try:
    from .trigger_builder.trigger_builder_screen import TriggerBuilderScreen
    TRIGGER_BUILDER_AVAILABLE = True
except ImportError:
    TRIGGER_BUILDER_AVAILABLE = False
    # 폴백: 기존 통합 조건 관리 시스템
    try:
        from .integrated_condition_manager import IntegratedConditionManager
    except ImportError:
        IntegratedConditionManager = None


class StrategyManagementScreen(QWidget):
    """컴포넌트 기반 전략 관리 화면"""
    
    # 백테스팅 요청 시그널
    backtest_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 매매 전략 관리")
        self.logger = get_logger("StrategyManagement")
        
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        
        # 탭들 생성
        self.trigger_builder_tab = self.create_trigger_builder_tab()
        self.strategy_maker_tab = self.create_strategy_maker_tab()
        self.backtest_tab = self.create_backtest_tab()
        self.analysis_tab = self.create_analysis_tab()
        
        # 탭 추가
        self.tab_widget.addTab(self.trigger_builder_tab, "🎯 트리거 빌더")
        self.tab_widget.addTab(self.strategy_maker_tab, "⚙️ 전략 메이커")
        self.tab_widget.addTab(self.backtest_tab, "📊 백테스팅")
        self.tab_widget.addTab(self.analysis_tab, "📈 전략 분석")
        
        layout.addWidget(self.tab_widget)
        
        self.logger.debug("매매전략 관리 화면 초기화 완료 (4개 탭)")
    
    def create_trigger_builder_tab(self):
        """트리거 빌더 탭 생성 - 리팩토링된 컴포넌트 기반"""
        try:
            if TRIGGER_BUILDER_AVAILABLE:
                return TriggerBuilderScreen()
            else:
                if IntegratedConditionManager:
                    return IntegratedConditionManager()
                else:
                    raise ImportError("트리거 빌더 컴포넌트들을 찾을 수 없습니다")
        except Exception as e:
            self.logger.error(f"트리거 빌더 탭 생성 실패: {e}")
            return self.create_fallback_screen("트리거 빌더 로딩 실패")
    
    def create_strategy_maker_tab(self):
        """전략 메이커 탭 생성 - 실제 매매 전략 생성"""
        try:
            from .components.strategy_maker import StrategyMaker
            return StrategyMaker()
        except Exception as e:
            self.logger.error(f"전략 메이커 탭 생성 실패: {e}")
            return self.create_fallback_screen("전략 메이커 로딩 실패")
            
            # 설명
            desc_label = QLabel("""
            � 전략 메이커는 트리거들을 조합하여 완전한 매매 전략을 생성하는 도구입니다.
            
            🔧 주요 기능:
            • 트리거 조합을 통한 진입/청산 조건 설정
            • 리스크 관리 설정 (손절, 익절, 포지션 사이징)
            • 전략 시뮬레이션 및 검증
            • 실거래 연동 준비
            """)
            desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            desc_label.setStyleSheet("""
                font-size: 12px;
                color: #34495e;
                background-color: #f8f9fa;
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
                padding: 20px;
                margin: 10px;
                line-height: 1.6;
            """)
            return self.create_fallback_screen("전략 메이커 로딩 실패")
    
    def create_backtest_tab(self):
        """백테스팅 탭 생성"""
        return self.create_fallback_screen("백테스팅 (개발 예정)")
    
    def create_analysis_tab(self):
        """전략 분석 탭 생성"""
        return self.create_fallback_screen("전략 분석 (개발 예정)")
    
    def create_fallback_screen(self, title):
        """폴백 화면 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        error_label = QLabel(f"� {title}\n\n개발 진행 중입니다.")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
                padding: 20px;
                background-color: #f8f9fa;
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
            }
        """)
        layout.addWidget(error_label)
        
        return widget
        """)
        layout.addWidget(desc_label)
        
        # 개발 상태 알림
        status_label = QLabel("🚧 백테스팅 엔진 개발 중입니다. 전략 메이커에서 전략을 먼저 생성해주세요.")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet("""
            color: #2980b9;
            font-style: italic;
            font-size: 13px;
            padding: 15px;
            background-color: #ebf3fd;
            border: 1px solid #3498db;
            border-radius: 6px;
            margin: 10px;
        """)
        layout.addWidget(status_label)
        
        layout.addStretch()
        
        return widget
    
    def create_analysis_tab(self):
        """전략 분석 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 헤더
        header_label = QLabel("📈 전략 분석")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 20px;
            background-color: #eaf2f8;
            border-radius: 8px;
            margin: 10px;
        """)
        layout.addWidget(header_label)
        
        # 설명
        desc_label = QLabel("""
        📊 전략 분석은 백테스팅 결과를 심층 분석하고 최적화하는 도구입니다.
        
        🔧 주요 기능:
        • 상세 성과 분석 리포트 생성
        • 전략 파라미터 최적화
        • 위험 요소 식별 및 개선 제안
        • 실거래 적용 시뮬레이션
        • 포트폴리오 다각화 분석
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: #34495e;
            background-color: #f8f9fa;
            border: 2px dashed #1abc9c;
            border-radius: 8px;
            padding: 20px;
            margin: 10px;
            line-height: 1.6;
        """)
        layout.addWidget(desc_label)
        
        # 개발 상태 알림
        status_label = QLabel("🚧 전략 분석 도구 개발 중입니다. 백테스팅 결과가 준비되면 활성화됩니다.")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet("""
            color: #16a085;
            font-style: italic;
            font-size: 13px;
            padding: 15px;
            background-color: #e8f6f3;
            border: 1px solid #1abc9c;
            border-radius: 6px;
            margin: 10px;
        """)
        layout.addWidget(status_label)
        
        layout.addStretch()
        
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
