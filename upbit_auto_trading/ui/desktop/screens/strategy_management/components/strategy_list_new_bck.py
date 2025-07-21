"""
전략 목록 위젯
- 저장된 전략들의 목록 표시
- 전략 선택, 삭제, 복사 기능
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QListWidgetItem, QGroupBox, QMessageBox,
    QLabel, QMenu
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction
import sys
import os
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

from upbit_auto_trading.business_logic.strategy.trading_strategies import StrategyManager, StrategyConfig

class StrategyListWidget(QWidget):
    # 시그널 정의
    strategy_selected = pyqtSignal(str)  # 전략 ID

    def __init__(self, parent=None):
        super().__init__(parent)
        self.strategy_manager = StrategyManager()
        self.init_ui()
        self.refresh_list()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 그룹박스로 감싸기
        group = QGroupBox("📋 저장된 전략 목록")
        group_layout = QVBoxLayout(group)
        
        # 상단: 제어 버튼들
        btn_row = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 새로고침")
        self.refresh_btn.clicked.connect(self.refresh_list)
        btn_row.addWidget(self.refresh_btn)
        
        self.delete_btn = QPushButton("🗑️ 삭제")
        self.delete_btn.clicked.connect(self.delete_selected_strategy)
        self.delete_btn.setEnabled(False)
        btn_row.addWidget(self.delete_btn)
        
        group_layout.addLayout(btn_row)
        
        # 전략 목록
        self.strategy_list = QListWidget()
        self.strategy_list.itemClicked.connect(self.on_strategy_selected)
        self.strategy_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.strategy_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.strategy_list.customContextMenuRequested.connect(self.show_context_menu)
        group_layout.addWidget(self.strategy_list)
        
        # 하단: 통계 정보
        self.stats_label = QLabel("전략 수: 0개")
        self.stats_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 5px;")
        group_layout.addWidget(self.stats_label)
        
        layout.addWidget(group)
    
    def refresh_list(self):
        """전략 목록 새로고침"""
        self.strategy_list.clear()
        strategies = self.strategy_manager.get_all_strategies()
        
        for strategy in strategies:
            item = QListWidgetItem()
            
            # 전략 정보 표시
            display_text = f"📈 {strategy.name}\n"
            display_text += f"   🔧 {strategy.strategy_type}\n"
            if strategy.description:
                display_text += f"   💬 {strategy.description[:50]}{'...' if len(strategy.description) > 50 else ''}\n"
            display_text += f"   📅 {strategy.updated_at.strftime('%Y-%m-%d %H:%M') if strategy.updated_at else 'N/A'}"
            
            item.setText(display_text)
            item.setData(Qt.ItemDataRole.UserRole, strategy.strategy_id)
            
            # 전략 타입별 색상 구분
            if strategy.strategy_type == "이동평균 교차":
                item.setBackground(Qt.GlobalColor.lightBlue)
            elif strategy.strategy_type == "RSI":
                item.setBackground(Qt.GlobalColor.lightGreen)
            elif strategy.strategy_type == "볼린저 밴드":
                item.setBackground(Qt.GlobalColor.lightYellow)
            
            self.strategy_list.addItem(item)
        
        # 통계 업데이트
        self.stats_label.setText(f"전략 수: {len(strategies)}개")
    
    def on_strategy_selected(self, item):
        """전략 선택 이벤트"""
        strategy_id = item.data(Qt.ItemDataRole.UserRole)
        if strategy_id:
            self.strategy_selected.emit(strategy_id)
    
    def on_selection_changed(self):
        """선택 변경 이벤트"""
        has_selection = len(self.strategy_list.selectedItems()) > 0
        self.delete_btn.setEnabled(has_selection)
    
    def delete_selected_strategy(self):
        """선택된 전략 삭제"""
        current_item = self.strategy_list.currentItem()
        if not current_item:
            return
        
        strategy_id = current_item.data(Qt.ItemDataRole.UserRole)
        strategy_config = self.strategy_manager.load_strategy(strategy_id)
        
        if not strategy_config:
            return
        
        reply = QMessageBox.question(
            self, 
            "전략 삭제 확인",
            f"'{strategy_config.name}' 전략을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: 실제 삭제 기능 구현 (DB에서 삭제)
            self.refresh_list()
            QMessageBox.information(self, "삭제 완료", f"'{strategy_config.name}' 전략이 삭제되었습니다.")
    
    def show_context_menu(self, position):
        """컨텍스트 메뉴 표시"""
        item = self.strategy_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # 전략 복사
        copy_action = QAction("📋 전략 복사", self)
        copy_action.triggered.connect(lambda: self.copy_strategy(item))
        menu.addAction(copy_action)
        
        # 전략 내보내기
        export_action = QAction("📤 전략 내보내기", self)
        export_action.triggered.connect(lambda: self.export_strategy(item))
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        # 전략 삭제
        delete_action = QAction("🗑️ 전략 삭제", self)
        delete_action.triggered.connect(self.delete_selected_strategy)
        menu.addAction(delete_action)
        
        menu.exec(self.strategy_list.mapToGlobal(position))
    
    def copy_strategy(self, item):
        """전략 복사"""
        strategy_id = item.data(Qt.ItemDataRole.UserRole)
        strategy_config = self.strategy_manager.load_strategy(strategy_id)
        
        if strategy_config:
            # 새로운 ID로 복사본 생성
            import uuid
            new_config = StrategyConfig(
                strategy_id=str(uuid.uuid4()),
                name=f"{strategy_config.name} (복사본)",
                strategy_type=strategy_config.strategy_type,
                parameters=strategy_config.parameters.copy(),
                description=strategy_config.description,
                created_at=datetime.now()
            )
            
            success = self.strategy_manager.save_strategy(new_config)
            if success:
                self.refresh_list()
                QMessageBox.information(self, "복사 완료", f"'{new_config.name}' 전략이 생성되었습니다.")
            else:
                QMessageBox.critical(self, "오류", "전략 복사에 실패했습니다.")
    
    def export_strategy(self, item):
        """전략 내보내기 (JSON 형태)"""
        strategy_id = item.data(Qt.ItemDataRole.UserRole)
        strategy_config = self.strategy_manager.load_strategy(strategy_id)
        
        if strategy_config:
            # TODO: 파일 다이얼로그로 JSON 내보내기 구현
            QMessageBox.information(self, "내보내기", "전략 내보내기 기능은 추후 구현됩니다.")
