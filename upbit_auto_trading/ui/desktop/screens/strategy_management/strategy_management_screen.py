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
        """전략 조합 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 조합 전략 설명
        description = QLabel("🔗 전략 조합: 1개 진입 전략 + 0~N개 관리 전략을 조합하여 완성된 매매 시스템을 구성합니다")
        description.setStyleSheet("font-weight: bold; color: #4CAF50; padding: 10px; background: #E8F5E8; border-radius: 5px;")
        layout.addWidget(description)
        
        # 조합 선택 섹션
        combination_group = QGroupBox("전략 조합 구성")
        combination_layout = QVBoxLayout(combination_group)
        
        # 진입 전략 선택
        entry_layout = QHBoxLayout()
        entry_layout.addWidget(QLabel("📈 진입 전략:"))
        self.entry_combo = QComboBox()
        self.entry_combo.addItem("전략을 선택하세요...")
        entry_layout.addWidget(self.entry_combo)
        combination_layout.addLayout(entry_layout)
        
        # 관리 전략 선택 (다중 선택)
        mgmt_label = QLabel("🛡️ 관리 전략 (다중 선택 가능):")
        combination_layout.addWidget(mgmt_label)
        
        # 관리 전략 테이블
        self.mgmt_table = StyledTableWidget(rows=5, columns=3)
        self.mgmt_table.setHorizontalHeaderLabels(["선택", "전략명", "설명"])
        self.mgmt_table.setColumnWidth(0, 60)
        self.mgmt_table.setColumnWidth(1, 200)
        self.mgmt_table.setColumnWidth(2, 300)
        self.mgmt_table.setMaximumHeight(200)
        combination_layout.addWidget(self.mgmt_table)
        
        # 조합 버튼들
        button_layout = QHBoxLayout()
        preview_btn = SecondaryButton("👁️ 미리보기")
        preview_btn.clicked.connect(self.preview_combination)
        save_btn = PrimaryButton("💾 조합 저장")
        save_btn.clicked.connect(self.save_combination)
        
        button_layout.addWidget(preview_btn)
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        combination_layout.addLayout(button_layout)
        
        layout.addWidget(combination_group)
        
        # 저장된 조합 목록
        saved_group = QGroupBox("저장된 전략 조합")
        saved_layout = QVBoxLayout(saved_group)
        
        self.saved_combinations_table = StyledTableWidget(rows=3, columns=4)
        self.saved_combinations_table.setHorizontalHeaderLabels(["조합명", "진입전략", "관리전략", "생성일"])
        self.saved_combinations_table.setColumnWidth(0, 150)
        self.saved_combinations_table.setColumnWidth(1, 150)
        self.saved_combinations_table.setColumnWidth(2, 200)
        self.saved_combinations_table.setColumnWidth(3, 100)
        saved_layout.addWidget(self.saved_combinations_table)
        
        layout.addWidget(saved_group)
        
        # 초기 데이터 로딩
        self.load_combination_data()
        
        return tab
    
    def load_combination_data(self):
        """조합 데이터 로딩"""
        try:
            # 진입 전략 콤보박스 채우기
            entry_strategies = self.strategy_manager.get_strategy_list()
            entry_list = [s for s in entry_strategies if not any(mgmt in s.get("strategy_type", "").lower() 
                         for mgmt in ["stop", "management", "trail", "profit", "exit"])]
            
            self.entry_combo.clear()
            self.entry_combo.addItem("전략을 선택하세요...")
            for strategy in entry_list:
                self.entry_combo.addItem(strategy.get("name", ""), strategy.get("id"))
            
            # 관리 전략 테이블 채우기
            mgmt_strategies = [s for s in entry_strategies if any(mgmt in s.get("strategy_type", "").lower() 
                              for mgmt in ["stop", "management", "trail", "profit", "exit"])]
            
            self.mgmt_table.setRowCount(len(mgmt_strategies))
            for i, strategy in enumerate(mgmt_strategies):
                # 체크박스 (텍스트로 구현)
                check_item = QTableWidgetItem("☐")
                check_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.mgmt_table.setItem(i, 0, check_item)
                
                # 전략명
                name_item = QTableWidgetItem(strategy.get("name", ""))
                name_item.setData(Qt.ItemDataRole.UserRole, strategy.get("id"))
                self.mgmt_table.setItem(i, 1, name_item)
                
                # 설명
                desc_item = QTableWidgetItem(strategy.get("description", ""))
                self.mgmt_table.setItem(i, 2, desc_item)
            
            # 테이블 클릭 이벤트 연결
            self.mgmt_table.cellClicked.connect(self.on_mgmt_table_clicked)
            
        except Exception as e:
            print(f"조합 데이터 로딩 오류: {e}")
    
    def on_mgmt_table_clicked(self, row, col):
        """관리 전략 테이블 클릭 처리"""
        if col == 0:  # 체크박스 열
            item = self.mgmt_table.item(row, 0)
            if item:
                current_text = item.text()
                new_text = "☑" if current_text == "☐" else "☐"
                item.setText(new_text)
    
    def preview_combination(self):
        """조합 미리보기"""
        entry_strategy = self.entry_combo.currentText()
        if entry_strategy == "전략을 선택하세요...":
            QMessageBox.warning(self, "경고", "진입 전략을 선택해주세요.")
            return
        
        # 선택된 관리 전략들
        selected_mgmt = []
        for i in range(self.mgmt_table.rowCount()):
            check_item = self.mgmt_table.item(i, 0)
            name_item = self.mgmt_table.item(i, 1)
            if check_item and name_item and check_item.text() == "☑":
                selected_mgmt.append(name_item.text())
        
        preview_text = f"📊 전략 조합 미리보기\n\n"
        preview_text += f"📈 진입 전략: {entry_strategy}\n"
        preview_text += f"🛡️ 관리 전략: {', '.join(selected_mgmt) if selected_mgmt else '없음'}\n\n"
        preview_text += f"💡 이 조합은 {entry_strategy} 신호로 진입하고,\n"
        if selected_mgmt:
            preview_text += f"   {len(selected_mgmt)}개의 관리 전략이 포지션을 관리합니다."
        else:
            preview_text += f"   별도 관리 전략 없이 수동으로 관리합니다."
        
        QMessageBox.information(self, "조합 미리보기", preview_text)
    
    def save_combination(self):
        """조합 저장"""
        entry_strategy = self.entry_combo.currentText()
        if entry_strategy == "전략을 선택하세요...":
            QMessageBox.warning(self, "경고", "진입 전략을 선택해주세요.")
            return
        
        # 조합명 입력
        combination_name, ok = QInputDialog.getText(
            self, "조합 저장", "전략 조합 이름을 입력하세요:",
            text=f"{entry_strategy} 조합"
        )
        
        if ok and combination_name:
            # 테이블에 추가
            current_rows = self.saved_combinations_table.rowCount()
            self.saved_combinations_table.setRowCount(current_rows + 1)
            
            self.saved_combinations_table.setItem(current_rows, 0, QTableWidgetItem(combination_name))
            self.saved_combinations_table.setItem(current_rows, 1, QTableWidgetItem(entry_strategy))
            
            # 선택된 관리 전략들
            selected_mgmt = []
            for i in range(self.mgmt_table.rowCount()):
                check_item = self.mgmt_table.item(i, 0)
                name_item = self.mgmt_table.item(i, 1)
                if check_item and name_item and check_item.text() == "☑":
                    selected_mgmt.append(name_item.text())
            
            self.saved_combinations_table.setItem(current_rows, 2, QTableWidgetItem(', '.join(selected_mgmt) if selected_mgmt else '없음'))
            self.saved_combinations_table.setItem(current_rows, 3, QTableWidgetItem(datetime.now().strftime("%m/%d")))
            
            QMessageBox.information(self, "저장 완료", f"전략 조합 '{combination_name}'이 저장되었습니다.")
    
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
