"""
전략 조합 탭 컴포넌트 - 고도화된 UI 구현

2x2 그리드 레이아웃:
┌─────────────────┬─────────────────┐
│ 전략 선택 영역    │ 조합 설정 영역    │
│ (진입/관리전략)   │ (충돌해결/우선순위)│
├─────────────────┼─────────────────┤
│ 미리보기 영역     │ 제어 영역        │
│ (조합 시각화)     │ (저장/백테스트)  │
└─────────────────┴─────────────────┘
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QComboBox, QPushButton, QListWidget, QListWidgetItem,
    QTextEdit, QSpinBox, QSlider, QCheckBox, QMessageBox,
    QProgressBar, QFrame, QScrollArea, QSplitter, QTabWidget,
    QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QMimeData
from PyQt6.QtGui import QFont, QPixmap, QIcon, QDrag, QPainter

from upbit_auto_trading.ui.desktop.common.components import (
    StyledTableWidget, PrimaryButton, SecondaryButton, DangerButton
)
from upbit_auto_trading.data_layer.combination_manager import CombinationManager
from upbit_auto_trading.business_logic.strategy.strategy_manager import get_strategy_manager

import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class DraggableStrategyItem(QListWidgetItem):
    """드래그 가능한 전략 아이템"""
    
    def __init__(self, strategy_data: Dict[str, Any]):
        super().__init__()
        self.strategy_data = strategy_data
        
        # 아이템 표시 설정
        strategy_type = strategy_data.get('strategy_type', 'unknown')
        name = strategy_data.get('name', 'Unknown')
        
        # 전략 타입별 아이콘
        if 'entry' in strategy_type.lower() or 'rsi' in strategy_type.lower():
            icon = "📈"
        elif any(kw in strategy_type.lower() for kw in ['stop', 'trail', 'exit', 'management']):
            icon = "🛡️"
        else:
            icon = "⚙️"
            
        self.setText(f"{icon} {name}")
        self.setToolTip(f"타입: {strategy_type}\n설명: {strategy_data.get('description', 'N/A')}")

class DropZone(QListWidget):
    """드롭 존 위젯"""
    
    strategy_dropped = pyqtSignal(dict)
    strategy_removed = pyqtSignal(str)
    
    def __init__(self, zone_type: str, parent=None):
        super().__init__(parent)
        self.zone_type = zone_type  # 'entry' 또는 'management'
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        
        # 스타일 설정
        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #cccccc;
                border-radius: 8px;
                background-color: #f9f9f9;
                min-height: 100px;
                padding: 10px;
            }
            QListWidget:hover {
                border-color: #4CAF50;
                background-color: #f0f8f0;
            }
        """)
        
        # 플레이스홀더 텍스트
        if zone_type == 'entry':
            self.placeholder = "진입 전략을 여기에 드래그하세요\n(최대 1개)"
        else:
            self.placeholder = "관리 전략을 여기에 드래그하세요\n(다중 선택 가능)"
        
        self.update_placeholder()
    
    def update_placeholder(self):
        """플레이스홀더 업데이트"""
        if self.count() == 0:
            item = QListWidgetItem(self.placeholder)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.addItem(item)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        try:
            strategy_json = event.mimeData().text()
            strategy_data = json.loads(strategy_json)
            
            # 진입 전략은 최대 1개만
            if self.zone_type == 'entry':
                if self.count() > 0:
                    # 기존 아이템 제거 (플레이스홀더 아님)
                    for i in range(self.count()):
                        item = self.item(i)
                        if hasattr(item, 'strategy_data'):
                            self.takeItem(i)
                            break
                    self.clear()
            else:
                # 관리 전략은 플레이스홀더만 제거
                if self.count() > 0 and not hasattr(self.item(0), 'strategy_data'):
                    self.clear()
            
            # 새 아이템 추가
            new_item = DraggableStrategyItem(strategy_data)
            new_item.strategy_data = strategy_data
            self.addItem(new_item)
            
            self.strategy_dropped.emit(strategy_data)
            event.acceptProposedAction()
            
        except Exception as e:
            print(f"드롭 처리 오류: {e}")
    
    def removeStrategy(self, strategy_id: str):
        """전략 제거"""
        for i in range(self.count()):
            item = self.item(i)
            if hasattr(item, 'strategy_data') and item.strategy_data.get('id') == strategy_id:
                self.takeItem(i)
                self.strategy_removed.emit(strategy_id)
                break
        
        self.update_placeholder()

class StrategyCombinationTab(QWidget):
    """전략 조합 탭 - 2x2 그리드 레이아웃"""
    
    combination_created = pyqtSignal(str)  # 조합 생성됨
    combination_updated = pyqtSignal(str)  # 조합 업데이트됨
    combination_deleted = pyqtSignal(str)  # 조합 삭제됨
    backtest_requested = pyqtSignal(str)   # 백테스트 요청
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 매니저 초기화
        self.combination_manager = CombinationManager()
        self.strategy_manager = get_strategy_manager()
        
        # 현재 조합 상태
        self.current_combination = {
            'entry_strategy': None,
            'management_strategies': [],
            'conflict_resolution': 'priority',  # 'priority', 'weighted', 'voting'
            'validation_status': 'PENDING'
        }
        
        self.init_ui()
        self.load_initial_data()
        
        # 실시간 검증 타이머
        self.validation_timer = QTimer()
        self.validation_timer.timeout.connect(self.validate_current_combination)
        self.validation_timer.setSingleShot(True)
    
    def init_ui(self):
        """UI 초기화 - 2x2 그리드 레이아웃"""
        layout = QVBoxLayout(self)
        
        # 제목
        title_label = QLabel("🔗 전략 조합 관리")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; padding: 10px;")
        layout.addWidget(title_label)
        
        # 메인 그리드 생성
        main_grid = QGridLayout()
        main_grid.setSpacing(10)
        
        # 1. 전략 선택 영역 (좌상단)
        strategy_selection_widget = self.create_strategy_selection_area()
        main_grid.addWidget(strategy_selection_widget, 0, 0)
        
        # 2. 조합 설정 영역 (우상단)
        combination_config_widget = self.create_combination_config_area()
        main_grid.addWidget(combination_config_widget, 0, 1)
        
        # 3. 미리보기 영역 (좌하단)
        preview_widget = self.create_preview_area()
        main_grid.addWidget(preview_widget, 1, 0)
        
        # 4. 제어 영역 (우하단)
        control_widget = self.create_control_area()
        main_grid.addWidget(control_widget, 1, 1)
        
        # 그리드를 메인 레이아웃에 추가
        grid_widget = QWidget()
        grid_widget.setLayout(main_grid)
        layout.addWidget(grid_widget)
        
        # 하단 상태 표시
        self.status_bar = self.create_status_bar()
        layout.addWidget(self.status_bar)
    
    def create_strategy_selection_area(self):
        """전략 선택 영역 생성 (좌상단)"""
        group = QGroupBox("📋 사용 가능한 전략")
        layout = QVBoxLayout(group)
        
        # 전략 목록 (드래그 가능)
        self.strategy_list = QListWidget()
        self.strategy_list.setDragDropMode(QListWidget.DragDropMode.DragOnly)
        self.strategy_list.setDefaultDropAction(Qt.DropAction.CopyAction)
        layout.addWidget(self.strategy_list)
        
        # 전략 타입 필터
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("필터:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["전체", "진입 전략", "관리 전략"])
        self.filter_combo.currentTextChanged.connect(self.filter_strategies)
        filter_layout.addWidget(self.filter_combo)
        
        filter_layout.addStretch()
        
        refresh_btn = SecondaryButton("🔄")
        refresh_btn.setMaximumWidth(40)
        refresh_btn.clicked.connect(self.load_strategies)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        return group
    
    def create_combination_config_area(self):
        """조합 설정 영역 생성 (우상단)"""
        group = QGroupBox("⚙️ 조합 설정")
        layout = QVBoxLayout(group)
        
        # 선택된 전략 표시
        # 진입 전략 드롭존
        layout.addWidget(QLabel("📈 진입 전략:"))
        self.entry_drop_zone = DropZone('entry')
        self.entry_drop_zone.strategy_dropped.connect(self.on_entry_strategy_added)
        self.entry_drop_zone.strategy_removed.connect(self.on_strategy_removed)
        layout.addWidget(self.entry_drop_zone)
        
        # 관리 전략 드롭존
        layout.addWidget(QLabel("🛡️ 관리 전략:"))
        self.management_drop_zone = DropZone('management')
        self.management_drop_zone.strategy_dropped.connect(self.on_management_strategy_added)
        self.management_drop_zone.strategy_removed.connect(self.on_strategy_removed)
        layout.addWidget(self.management_drop_zone)
        
        # 충돌 해결 방식
        layout.addWidget(QLabel("🔧 충돌 해결 방식:"))
        self.conflict_combo = QComboBox()
        self.conflict_combo.addItems([
            "우선순위 기반", 
            "가중치 평균", 
            "투표 방식"
        ])
        self.conflict_combo.currentTextChanged.connect(self.on_conflict_resolution_changed)
        layout.addWidget(self.conflict_combo)
        
        return group
    
    def create_preview_area(self):
        """미리보기 영역 생성 (좌하단)"""
        group = QGroupBox("👁️ 조합 미리보기")
        layout = QVBoxLayout(group)
        
        # 조합 시각화
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                background-color: #fafafa;
                font-family: 'Courier New', monospace;
            }
        """)
        layout.addWidget(self.preview_text)
        
        # 검증 상태 표시
        validation_layout = QHBoxLayout()
        self.validation_icon = QLabel("⏳")
        self.validation_text = QLabel("검증 대기 중...")
        validation_layout.addWidget(self.validation_icon)
        validation_layout.addWidget(self.validation_text)
        validation_layout.addStretch()
        
        layout.addLayout(validation_layout)
        
        return group
    
    def create_control_area(self):
        """제어 영역 생성 (우하단)"""
        group = QGroupBox("🎮 제어 패널")
        layout = QVBoxLayout(group)
        
        # 조합 이름 입력
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("조합 이름:"))
        self.combination_name_input = QComboBox()
        self.combination_name_input.setEditable(True)
        self.combination_name_input.setPlaceholderText("새 조합 이름 입력...")
        name_layout.addWidget(self.combination_name_input)
        layout.addLayout(name_layout)
        
        # 버튼들
        button_layout = QVBoxLayout()
        
        # 저장/불러오기
        save_load_layout = QHBoxLayout()
        self.save_btn = PrimaryButton("💾 저장")
        self.save_btn.clicked.connect(self.save_combination)
        self.save_btn.setEnabled(False)
        
        self.load_btn = SecondaryButton("📁 불러오기")
        self.load_btn.clicked.connect(self.load_combination)
        
        save_load_layout.addWidget(self.save_btn)
        save_load_layout.addWidget(self.load_btn)
        button_layout.addLayout(save_load_layout)
        
        # 백테스트/클리어
        test_clear_layout = QHBoxLayout()
        self.backtest_btn = PrimaryButton("🧪 백테스트")
        self.backtest_btn.clicked.connect(self.request_backtest)
        self.backtest_btn.setEnabled(False)
        
        self.clear_btn = DangerButton("🗑️ 클리어")
        self.clear_btn.clicked.connect(self.clear_combination)
        
        test_clear_layout.addWidget(self.backtest_btn)
        test_clear_layout.addWidget(self.clear_btn)
        button_layout.addLayout(test_clear_layout)
        
        layout.addLayout(button_layout)
        
        # 저장된 조합 목록
        layout.addWidget(QLabel("📚 저장된 조합:"))
        self.saved_combinations_list = QListWidget()
        self.saved_combinations_list.setMaximumHeight(100)
        self.saved_combinations_list.itemClicked.connect(self.on_saved_combination_selected)
        layout.addWidget(self.saved_combinations_list)
        
        return group
    
    def create_status_bar(self):
        """상태 표시 바 생성"""
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border-top: 1px solid #ddd;
                padding: 5px;
            }
        """)
        layout = QHBoxLayout(status_frame)
        
        self.status_label = QLabel("📊 상태: 준비됨")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 실시간 통계
        self.stats_label = QLabel("진입: 0개, 관리: 0개")
        layout.addWidget(self.stats_label)
        
        return status_frame
    
    def load_initial_data(self):
        """초기 데이터 로딩"""
        self.load_strategies()
        self.load_saved_combinations()
        self.update_preview()
    
    def load_strategies(self):
        """전략 목록 로딩"""
        try:
            self.strategy_list.clear()
            
            # 전략 매니저에서 전략 목록 가져오기
            strategies = self.strategy_manager.get_strategy_list()
            
            for strategy in strategies:
                item = DraggableStrategyItem(strategy)
                self.strategy_list.addItem(item)
            
            # 드래그 시작 이벤트 설정
            self.strategy_list.startDrag = self.start_drag
            
            print(f"✅ 전략 {len(strategies)}개 로딩 완료")
            
        except Exception as e:
            print(f"❌ 전략 로딩 오류: {e}")
    
    def start_drag(self, supported_actions):
        """드래그 시작"""
        current_item = self.strategy_list.currentItem()
        if current_item and hasattr(current_item, 'strategy_data'):
            drag = QDrag(self.strategy_list)
            mime_data = QMimeData()
            
            # 전략 데이터를 JSON으로 전송
            strategy_json = json.dumps(current_item.strategy_data)
            mime_data.setText(strategy_json)
            drag.setMimeData(mime_data)
            
            # 드래그 실행
            drag.exec(Qt.DropAction.CopyAction)
    
    def filter_strategies(self, filter_text: str):
        """전략 필터링"""
        for i in range(self.strategy_list.count()):
            item = self.strategy_list.item(i)
            if hasattr(item, 'strategy_data'):
                strategy_type = item.strategy_data.get('strategy_type', '').lower()
                
                if filter_text == "전체":
                    item.setHidden(False)
                elif filter_text == "진입 전략":
                    item.setHidden(not ('entry' in strategy_type or 'rsi' in strategy_type))
                elif filter_text == "관리 전략":
                    item.setHidden(not any(kw in strategy_type for kw in ['stop', 'trail', 'exit', 'management']))
    
    def on_entry_strategy_added(self, strategy_data: Dict[str, Any]):
        """진입 전략 추가됨"""
        self.current_combination['entry_strategy'] = strategy_data
        self.update_preview()
        self.start_validation_timer()
    
    def on_management_strategy_added(self, strategy_data: Dict[str, Any]):
        """관리 전략 추가됨"""
        if strategy_data not in self.current_combination['management_strategies']:
            self.current_combination['management_strategies'].append(strategy_data)
        self.update_preview()
        self.start_validation_timer()
    
    def on_strategy_removed(self, strategy_id: str):
        """전략 제거됨"""
        # 진입 전략 확인
        if (self.current_combination['entry_strategy'] and 
            self.current_combination['entry_strategy'].get('id') == strategy_id):
            self.current_combination['entry_strategy'] = None
        
        # 관리 전략에서 제거
        self.current_combination['management_strategies'] = [
            s for s in self.current_combination['management_strategies'] 
            if s.get('id') != strategy_id
        ]
        
        self.update_preview()
        self.start_validation_timer()
    
    def on_conflict_resolution_changed(self, resolution_text: str):
        """충돌 해결 방식 변경"""
        resolution_map = {
            "우선순위 기반": "priority",
            "가중치 평균": "weighted", 
            "투표 방식": "voting"
        }
        self.current_combination['conflict_resolution'] = resolution_map.get(resolution_text, 'priority')
        self.update_preview()
    
    def start_validation_timer(self):
        """검증 타이머 시작 (디바운싱)"""
        self.validation_timer.stop()
        self.validation_timer.start(500)  # 500ms 후 검증
    
    def validate_current_combination(self):
        """현재 조합 검증"""
        try:
            if not self.current_combination['entry_strategy']:
                self.update_validation_status("PENDING", "진입 전략을 선택해주세요")
                return
            
            # CombinationManager로 검증
            entry_id = self.current_combination['entry_strategy'].get('id')
            mgmt_ids = [s.get('id') for s in self.current_combination['management_strategies']]
            
            result = self.combination_manager.validate_combination(entry_id, mgmt_ids)
            
            if result['is_valid']:
                self.update_validation_status("VALID", "유효한 조합입니다")
                self.save_btn.setEnabled(True)
                self.backtest_btn.setEnabled(True)
            else:
                self.update_validation_status("INVALID", f"오류: {result.get('error', '알 수 없는 오류')}")
                self.save_btn.setEnabled(False)
                self.backtest_btn.setEnabled(False)
                
        except Exception as e:
            self.update_validation_status("ERROR", f"검증 오류: {str(e)}")
            self.save_btn.setEnabled(False)
            self.backtest_btn.setEnabled(False)
    
    def update_validation_status(self, status: str, message: str):
        """검증 상태 업데이트"""
        self.current_combination['validation_status'] = status
        
        status_icons = {
            "PENDING": "⏳",
            "VALID": "✅", 
            "INVALID": "❌",
            "ERROR": "⚠️"
        }
        
        status_colors = {
            "PENDING": "#ff9800",
            "VALID": "#4caf50",
            "INVALID": "#f44336", 
            "ERROR": "#ff5722"
        }
        
        icon = status_icons.get(status, "❓")
        color = status_colors.get(status, "#000")
        
        self.validation_icon.setText(icon)
        self.validation_text.setText(message)
        self.validation_text.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def update_preview(self):
        """미리보기 업데이트"""
        preview_text = "🔗 전략 조합 구성\n"
        preview_text += "=" * 40 + "\n\n"
        
        # 진입 전략
        if self.current_combination['entry_strategy']:
            entry = self.current_combination['entry_strategy']
            preview_text += f"📈 진입 전략: {entry.get('name', 'N/A')}\n"
            preview_text += f"   타입: {entry.get('strategy_type', 'N/A')}\n"
            preview_text += f"   설명: {entry.get('description', 'N/A')}\n\n"
        else:
            preview_text += "📈 진입 전략: 선택되지 않음\n\n"
        
        # 관리 전략들
        if self.current_combination['management_strategies']:
            preview_text += f"🛡️ 관리 전략 ({len(self.current_combination['management_strategies'])}개):\n"
            for i, mgmt in enumerate(self.current_combination['management_strategies'], 1):
                preview_text += f"   {i}. {mgmt.get('name', 'N/A')}\n"
                preview_text += f"      타입: {mgmt.get('strategy_type', 'N/A')}\n"
        else:
            preview_text += "🛡️ 관리 전략: 없음\n"
        
        preview_text += "\n" + "=" * 40 + "\n"
        preview_text += f"⚙️ 충돌 해결: {self.current_combination['conflict_resolution']}\n"
        preview_text += f"📊 상태: {self.current_combination['validation_status']}"
        
        self.preview_text.setPlainText(preview_text)
        
        # 통계 업데이트
        entry_count = 1 if self.current_combination['entry_strategy'] else 0
        mgmt_count = len(self.current_combination['management_strategies'])
        self.stats_label.setText(f"진입: {entry_count}개, 관리: {mgmt_count}개")
    
    def save_combination(self):
        """조합 저장"""
        try:
            combination_name = self.combination_name_input.currentText().strip()
            if not combination_name:
                QMessageBox.warning(self, "경고", "조합 이름을 입력해주세요.")
                return
            
            if not self.current_combination['entry_strategy']:
                QMessageBox.warning(self, "경고", "진입 전략을 선택해주세요.")
                return
            
            # CombinationManager로 저장
            entry_id = self.current_combination['entry_strategy'].get('id')
            mgmt_ids = [s.get('id') for s in self.current_combination['management_strategies']]
            
            result = self.combination_manager.create_combination(
                name=combination_name,
                entry_strategy_id=entry_id,
                management_strategy_ids=mgmt_ids,
                conflict_resolution=self.current_combination['conflict_resolution']
            )
            
            if result['success']:
                QMessageBox.information(self, "저장 완료", f"조합 '{combination_name}'이 저장되었습니다.")
                self.load_saved_combinations()
                self.combination_created.emit(combination_name)
            else:
                QMessageBox.critical(self, "저장 실패", f"저장에 실패했습니다: {result.get('error', '알 수 없는 오류')}")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 중 오류가 발생했습니다: {str(e)}")
    
    def load_combination(self):
        """선택된 조합 불러오기"""
        current_item = self.saved_combinations_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "경고", "불러올 조합을 선택해주세요.")
            return
        
        try:
            combination_name = current_item.text().split(' - ')[0]  # 이름 부분만 추출
            
            # CombinationManager에서 조합 상세 정보 가져오기
            combinations = self.combination_manager.list_combinations()
            selected_combination = None
            
            for combo in combinations:
                if combo['name'] == combination_name:
                    selected_combination = combo
                    break
            
            if not selected_combination:
                QMessageBox.warning(self, "오류", "선택된 조합을 찾을 수 없습니다.")
                return
            
            # 현재 조합 클리어
            self.clear_combination()
            
            # 조합 데이터 로드
            details = self.combination_manager.get_combination_details(selected_combination['id'])
            
            if details['success']:
                combo_data = details['combination']
                
                # 진입 전략 설정
                entry_strategy = combo_data['entry_strategy']
                if entry_strategy:
                    self.current_combination['entry_strategy'] = entry_strategy
                    item = DraggableStrategyItem(entry_strategy)
                    item.strategy_data = entry_strategy
                    self.entry_drop_zone.clear()
                    self.entry_drop_zone.addItem(item)
                
                # 관리 전략들 설정
                for mgmt_strategy in combo_data['management_strategies']:
                    self.current_combination['management_strategies'].append(mgmt_strategy)
                    item = DraggableStrategyItem(mgmt_strategy)
                    item.strategy_data = mgmt_strategy
                    if self.management_drop_zone.count() > 0 and not hasattr(self.management_drop_zone.item(0), 'strategy_data'):
                        self.management_drop_zone.clear()
                    self.management_drop_zone.addItem(item)
                
                # 충돌 해결 방식 설정
                conflict_resolution = combo_data.get('conflict_resolution', 'priority')
                self.current_combination['conflict_resolution'] = conflict_resolution
                
                resolution_map = {
                    'priority': "우선순위 기반",
                    'weighted': "가중치 평균",
                    'voting': "투표 방식"
                }
                self.conflict_combo.setCurrentText(resolution_map.get(conflict_resolution, "우선순위 기반"))
                
                # 조합 이름 설정
                self.combination_name_input.setCurrentText(combination_name)
                
                # 미리보기 및 검증 업데이트
                self.update_preview()
                self.start_validation_timer()
                
                QMessageBox.information(self, "불러오기 완료", f"조합 '{combination_name}'을 불러왔습니다.")
                
            else:
                QMessageBox.critical(self, "오류", f"조합 불러오기 실패: {details.get('error', '알 수 없는 오류')}")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"불러오기 중 오류가 발생했습니다: {str(e)}")
    
    def clear_combination(self):
        """현재 조합 클리어"""
        self.current_combination = {
            'entry_strategy': None,
            'management_strategies': [],
            'conflict_resolution': 'priority',
            'validation_status': 'PENDING'
        }
        
        # UI 클리어
        self.entry_drop_zone.clear()
        self.entry_drop_zone.update_placeholder()
        
        self.management_drop_zone.clear()
        self.management_drop_zone.update_placeholder()
        
        self.combination_name_input.setCurrentText("")
        self.conflict_combo.setCurrentIndex(0)
        
        # 상태 리셋
        self.update_preview()
        self.update_validation_status("PENDING", "조합을 구성해주세요")
        self.save_btn.setEnabled(False)
        self.backtest_btn.setEnabled(False)
    
    def load_saved_combinations(self):
        """저장된 조합 목록 로딩"""
        try:
            self.saved_combinations_list.clear()
            
            combinations = self.combination_manager.list_combinations()
            
            for combo in combinations:
                # 응답 데이터 구조 확인
                if isinstance(combo, dict):
                    combo_id = combo.get('combination_id') or combo.get('id', 'unknown')
                    combo_name = combo.get('name', 'Unknown')
                    entry_name = combo.get('entry_strategy_name', 'Unknown')
                    mgmt_count = combo.get('management_count', 0)
                    created_date = combo.get('created_at', 'Unknown')
                else:
                    # 다른 형식의 응답 처리
                    print(f"예상과 다른 조합 데이터 형식: {type(combo)} - {combo}")
                    continue
                
                # 날짜 포맷팅
                if created_date != 'Unknown':
                    try:
                        from datetime import datetime
                        if isinstance(created_date, str):
                            date_obj = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                        else:
                            date_obj = created_date
                        formatted_date = date_obj.strftime('%m-%d')
                    except:
                        formatted_date = str(created_date)[:10]
                else:
                    formatted_date = 'Unknown'
                
                item_text = f"{combo_name} - {entry_name} + {mgmt_count}개 관리 ({formatted_date})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, combo_id)
                self.saved_combinations_list.addItem(item)
                
                # 콤보박스에도 추가 (이름만)
                if self.combination_name_input.findText(combo_name) == -1:
                    self.combination_name_input.addItem(combo_name)
            
            print(f"✅ 저장된 조합 {len(combinations)}개 로딩 완료")
            
        except Exception as e:
            print(f"❌ 저장된 조합 로딩 오류: {e}")
            # 오류 상세 정보 출력
            combinations = self.combination_manager.list_combinations()
            if combinations:
                print(f"   첫 번째 조합 데이터 구조: {type(combinations[0])} - {combinations[0]}")
    
    def on_saved_combination_selected(self, item):
        """저장된 조합 선택"""
        # 더블클릭으로 자동 로드하지 않고, 불러오기 버튼을 명시적으로 클릭하도록 유도
        combination_name = item.text().split(' - ')[0]
        self.combination_name_input.setCurrentText(combination_name)
    
    def request_backtest(self):
        """백테스트 요청"""
        if not self.current_combination['entry_strategy']:
            QMessageBox.warning(self, "경고", "백테스트할 조합을 구성해주세요.")
            return
        
        # 조합 ID가 있는지 확인 (저장된 조합인지)
        combination_name = self.combination_name_input.currentText().strip()
        if not combination_name:
            QMessageBox.warning(self, "경고", "조합을 먼저 저장해주세요.")
            return
        
        reply = QMessageBox.question(
            self, "백테스트 실행", 
            f"'{combination_name}' 조합으로 백테스트를 실행하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.backtest_requested.emit(combination_name)
            QMessageBox.information(self, "백테스트 시작", "백테스트가 시작되었습니다.\n백테스팅 탭에서 결과를 확인하세요.")
