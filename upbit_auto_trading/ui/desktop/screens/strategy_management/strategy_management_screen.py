"""
매매 전략 관리 화면 - 3탭 구조
- 진입 전략 관리 탭
- 관리 전략 관리 탭  
- 전략 조합 탭
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QSplitter, QGroupBox,
    QFormLayout, QDateEdit, QComboBox, QTableWidgetItem,
    QInputDialog, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QIcon, QAction

from upbit_auto_trading.ui.desktop.common.components import (
    StyledTableWidget, PrimaryButton, SecondaryButton, DangerButton
)
from upbit_auto_trading.business_logic.strategy.strategy_manager import get_strategy_manager

# 컴포넌트 import
from .components.entry_strategy_tab import EntryStrategyTab
from .components.management_strategy_tab import ManagementStrategyTab
from .components.strategy_combination_tab import StrategyCombinationTab
from .components.parameter_editor_dialog import ParameterEditorDialog

import uuid
from datetime import datetime
from typing import Dict, Any

class StrategyManagementScreen(QWidget):
    """역할 기반 전략 관리 화면 - 진입/관리/조합 3탭 구조"""
    
    # 백테스팅 요청 시그널
    backtest_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 매매 전략 관리")
        
        # 필수 매니저들 초기화
        self.strategy_manager = get_strategy_manager()
        print("✅ 실제 DB 연동 StrategyManager 초기화 완료")
        
        self.init_ui()
        # 초기 데이터는 탭 생성 후 로딩
        self.load_initial_data()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 툴바 생성
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        
        # 3개 탭 생성
        self.entry_tab = self.create_entry_strategy_tab()
        self.management_tab = self.create_management_strategy_tab()
        self.combination_tab = self.create_strategy_combination_tab()
        
        # 탭 추가
        self.tab_widget.addTab(self.entry_tab, "📈 진입 전략")
        self.tab_widget.addTab(self.management_tab, "🛡️ 관리 전략")
        self.tab_widget.addTab(self.combination_tab, "🔗 전략 조합")
        
        layout.addWidget(self.tab_widget)
        
        print("✅ 매매전략 관리 화면 초기화 완료")
    
    def create_toolbar(self):
        """툴바 생성"""
        toolbar_widget = QWidget()
        layout = QHBoxLayout(toolbar_widget)
        
        # 제목
        title_label = QLabel("📊 매매 전략 관리")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 새로고침 버튼
        refresh_button = SecondaryButton("🔄 새로고침")
        refresh_button.clicked.connect(self.refresh_all_data)
        layout.addWidget(refresh_button)
        
        return toolbar_widget
    
    def create_entry_strategy_tab(self):
        """진입 전략 탭 생성 - 컴포넌트 사용"""
        self.entry_tab = EntryStrategyTab(self.strategy_manager, self)
        
        # 시그널 연결
        self.entry_tab.strategy_created.connect(self._on_entry_strategy_created)
        self.entry_tab.strategy_updated.connect(self._on_entry_strategy_updated)
        self.entry_tab.strategy_deleted.connect(self._on_entry_strategy_deleted)
        self.entry_tab.backtest_requested.connect(self._on_entry_backtest_requested)
        
        return self.entry_tab
        
    def create_management_strategy_tab(self):
        """관리 전략 탭 생성 - 컴포넌트 사용"""
        self.management_tab = ManagementStrategyTab(self.strategy_manager, self)
        
        # 시그널 연결
        self.management_tab.strategy_created.connect(self._on_management_strategy_created)
        self.management_tab.strategy_updated.connect(self._on_management_strategy_updated)
        self.management_tab.strategy_deleted.connect(self._on_management_strategy_deleted)
        self.management_tab.backtest_requested.connect(self._on_management_backtest_requested)
        
        return self.management_tab
        
    def create_strategy_combination_tab(self):
        """전략 조합 탭 생성 - 새로운 고도화된 컴포넌트 사용"""
        self.combination_tab = StrategyCombinationTab(self)
        
        # 시그널 연결
        self.combination_tab.combination_created.connect(self._on_combination_created)
        self.combination_tab.combination_updated.connect(self._on_combination_updated)
        self.combination_tab.combination_deleted.connect(self._on_combination_deleted)
        self.combination_tab.backtest_requested.connect(self._on_combination_backtest_requested)
        
        return self.combination_tab
    
    def load_combination_data(self):
        """조합 데이터 로딩 - 더 이상 사용되지 않음 (새 컴포넌트에서 자체 처리)"""
        pass
    
    def on_mgmt_table_clicked(self, row, col):
        """관리 전략 테이블 클릭 처리 - 더 이상 사용되지 않음"""
        pass
    
    def preview_combination(self):
        """조합 미리보기 - 더 이상 사용되지 않음"""
        pass
    
    def save_combination(self):
        """조합 저장 - 더 이상 사용되지 않음"""
        pass
    
    def load_initial_data(self):
        """초기 데이터 로딩"""
        # 탭이 초기화된 후 데이터 로딩
        print("✅ 매매전략 관리 화면 로딩 완료")
    
    def refresh_all_data(self):
        """모든 데이터 새로고침"""
        print("[UI] 🔄 전략 데이터 새로고침")
        
        try:
            # 진입 전략 탭 새로고침
            if hasattr(self, 'entry_tab'):
                self.entry_tab.load_strategies()
                print("   ✅ 진입 전략 새로고침 완료")
            
            # 관리 전략 탭 새로고침
            if hasattr(self, 'management_tab'):
                self.management_tab.load_strategies()
                print("   ✅ 관리 전략 새로고침 완료")
            
            # 전략 조합 탭 새로고침
            if hasattr(self, 'combination_tab'):
                self.combination_tab.load_strategies()
                self.combination_tab.load_saved_combinations()
                print("   ✅ 전략 조합 새로고침 완료")
            
            QMessageBox.information(self, "새로고침", "모든 데이터가 새로고침되었습니다.")
            
        except Exception as e:
            print(f"   ❌ 새로고침 중 오류: {e}")
            QMessageBox.critical(self, "오류", f"새로고침 중 오류가 발생했습니다:\n{str(e)}")
    
    # ===== 진입 전략 시그널 핸들러 =====
    def _on_entry_strategy_created(self, strategy_name: str):
        """진입 전략 생성 시그널 핸들러"""
        print(f"[Main] 📈 진입 전략 생성됨: {strategy_name}")
    
    def _on_entry_strategy_updated(self, strategy_name: str):
        """진입 전략 수정 시그널 핸들러"""
        print(f"[Main] ✏️ 진입 전략 수정됨: {strategy_name}")
    
    def _on_entry_strategy_deleted(self, strategy_name: str):
        """진입 전략 삭제 시그널 핸들러"""
        print(f"[Main] 🗑️ 진입 전략 삭제됨: {strategy_name}")
    
    def _on_entry_backtest_requested(self, strategy_id: str):
        """진입 전략 백테스트 요청 시그널 핸들러"""
        print(f"[Main] 🧪 진입 전략 백테스트 요청: {strategy_id}")
        # 백테스트 탭으로 전환하거나 백테스트 실행
        self.tab_widget.setCurrentIndex(2)  # 조합 탭으로 전환
    
    # ===== 관리 전략 시그널 핸들러 =====
    def _on_management_strategy_created(self, strategy_name: str):
        """관리 전략 생성 시그널 핸들러"""
        print(f"[Main] 🛡️ 관리 전략 생성됨: {strategy_name}")
    
    def _on_management_strategy_updated(self, strategy_name: str):
        """관리 전략 수정 시그널 핸들러"""
        print(f"[Main] ✏️ 관리 전략 수정됨: {strategy_name}")
    
    def _on_management_strategy_deleted(self, strategy_name: str):
        """관리 전략 삭제 시그널 핸들러"""
        print(f"[Main] 🗑️ 관리 전략 삭제됨: {strategy_name}")
    
    def _on_management_backtest_requested(self, strategy_id: str):
        """관리 전략 백테스트 요청 시그널 핸들러"""
        print(f"[Main] 🧪 관리 전략 백테스트 요청: {strategy_id}")
        # 백테스트 탭으로 전환하거나 백테스트 실행
        self.tab_widget.setCurrentIndex(2)  # 조합 탭으로 전환
    
    # ===== 전략 조합 시그널 핸들러 =====
    def _on_combination_created(self, combination_name: str):
        """전략 조합 생성 시그널 핸들러"""
        print(f"[Main] 🔗 전략 조합 생성됨: {combination_name}")
        # 새로고침이나 알림 처리
    
    def _on_combination_updated(self, combination_name: str):
        """전략 조합 수정 시그널 핸들러"""
        print(f"[Main] ✏️ 전략 조합 수정됨: {combination_name}")
        
    def _on_combination_deleted(self, combination_name: str):
        """전략 조합 삭제 시그널 핸들러"""
        print(f"[Main] 🗑️ 전략 조합 삭제됨: {combination_name}")
    
    def _on_combination_backtest_requested(self, combination_name: str):
        """전략 조합 백테스트 요청 시그널 핸들러"""
        print(f"[Main] 🧪 전략 조합 백테스트 요청: {combination_name}")
        # 상위 신호로 전파 (메인 윈도우나 백테스팅 화면으로)
        self.backtest_requested.emit(combination_name)
