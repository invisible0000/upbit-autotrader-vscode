"""
통합 전략 메이커 UI
Unified Strategy Maker UI

7개 핵심 규칙 템플릿 + 자유 컴포넌트 조합 방식
템플릿 기반 빠른 구성과 컴포넌트 레벨 세밀 조정 모두 지원
"""
import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QScrollArea, QLabel, QPushButton, QFrame, QButtonGroup,
    QTabWidget, QTextEdit, QTreeWidget, QTreeWidgetItem, QListWidget,
    QListWidgetItem, QGroupBox, QFormLayout, QLineEdit, QSpinBox, 
    QDoubleSpinBox, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal, QSize
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QFont, QColor, QIcon, QDrag
from typing import Dict, Any, List, Optional

# 템플릿 시스템 import 시도
try:
    from upbit_auto_trading.component_system.core_rule_templates import (
        CORE_STRATEGY_TEMPLATES, 
        get_rule_template,
        list_rule_templates
    )
    TEMPLATES_AVAILABLE = True
except ImportError:
    print("템플릿 시스템을 찾을 수 없습니다. 기본 템플릿으로 실행합니다.")
    TEMPLATES_AVAILABLE = False
    # 기본 템플릿 (간소화)
    CORE_STRATEGY_TEMPLATES = {
        "rsi_oversold_entry": {
            "name": "RSI 과매도 진입",
            "role": "ENTRY", 
            "description": "RSI 지표가 지정된 값 이하로 떨어지면 최초 진입합니다",
            "activation_state": "READY",
            "icon": "📈",
            "color": "#e74c3c"
        },
        "profit_scale_in": {
            "name": "수익 시 불타기",
            "role": "SCALE_IN",
            "description": "수익률이 지정된 값에 도달할 때마다 정해진 횟수만큼 추가 매수합니다",
            "activation_state": "ACTIVE", 
            "icon": "🔥",
            "color": "#f39c12"
        }
    }


class UnifiedStrategyMaker(QMainWindow):
    """통합 전략 메이커 메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.current_strategy = {
            "strategy_id": "",
            "strategy_name": "새 전략",
            "type": "hybrid",  # template 또는 component 또는 hybrid
            "rules": []
        }
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle("통합 전략 메이커 - Template + Component Based")
        self.setGeometry(100, 100, 1600, 1000)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 좌측 패널 (템플릿 + 컴포넌트)
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout()
        
        # 전략 메타데이터
        self.strategy_meta_panel = self.create_strategy_meta_panel()
        left_layout.addWidget(self.strategy_meta_panel)
        
        # 모드 선택 탭
        self.mode_tabs = QTabWidget()
        
        # 탭 1: 템플릿 모드
        self.template_tab = self.create_template_tab()
        self.mode_tabs.addTab(self.template_tab, "🎯 규칙 템플릿")
        
        # 탭 2: 컴포넌트 모드  
        self.component_tab = self.create_component_tab()
        self.mode_tabs.addTab(self.component_tab, "🧩 컴포넌트")
        
        left_layout.addWidget(self.mode_tabs)
        left_panel.setLayout(left_layout)
        main_layout.addWidget(left_panel)
        
        # 중앙 영역 (구성된 전략)
        center_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 선택된 규칙/컴포넌트 목록
        self.strategy_view_panel = self.create_strategy_view_panel()
        center_splitter.addWidget(self.strategy_view_panel)
        
        # 상세 설정 패널
        self.detail_config_panel = self.create_detail_config_panel()
        center_splitter.addWidget(self.detail_config_panel)
        
        center_splitter.setSizes([400, 500])
        main_layout.addWidget(center_splitter)
        
        # 우측 패널 (JSON 미리보기 + 저장/로드)
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        right_panel.setMaximumWidth(450)
        right_layout = QVBoxLayout()
        
        # JSON 미리보기
        self.json_preview_panel = self.create_json_preview_panel()
        right_layout.addWidget(self.json_preview_panel)
        
        right_panel.setLayout(right_layout)
        main_layout.addWidget(right_panel)
        
        # 초기 JSON 업데이트
        self.update_json_preview()
    
    def create_strategy_meta_panel(self):
        """전략 메타데이터 패널"""
        group = QGroupBox("전략 정보")
        layout = QFormLayout()
        
        self.strategy_name_edit = QLineEdit()
        self.strategy_name_edit.setText("새 전략")
        layout.addRow("전략 이름:", self.strategy_name_edit)
        
        self.strategy_id_edit = QLineEdit()
        self.strategy_id_edit.setPlaceholderText("자동 생성됨")
        layout.addRow("전략 ID:", self.strategy_id_edit)
        
        # 전략 유형
        self.strategy_type_combo = QComboBox()
        self.strategy_type_combo.addItems(["hybrid", "template", "component"])
        layout.addRow("전략 유형:", self.strategy_type_combo)
        
        group.setLayout(layout)
        return group
    
    def create_template_tab(self):
        """템플릿 기반 규칙 선택 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 안내 라벨
        info_label = QLabel("💡 검증된 7개 핵심 규칙을 빠르게 조합하세요")
        info_label.setStyleSheet("color: #2c3e50; font-weight: bold; padding: 8px;")
        layout.addWidget(info_label)
        
        # 템플릿 목록
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        for template_id, template_info in CORE_STRATEGY_TEMPLATES.items():
            template_button = TemplateRuleButton(template_id, template_info)
            template_button.rule_selected.connect(self.add_template_rule)
            scroll_layout.addWidget(template_button)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        tab.setLayout(layout)
        return tab
    
    def create_component_tab(self):
        """컴포넌트 기반 자유 조합 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 안내 라벨
        info_label = QLabel("🔧 트리거, 조건, 액션을 자유롭게 조합하세요")
        info_label.setStyleSheet("color: #2c3e50; font-weight: bold; padding: 8px;")
        layout.addWidget(info_label)
        
        # 컴포넌트 카테고리
        component_tabs = QTabWidget()
        
        categories = {
            "트리거": ["RSI", "가격변동", "지표교차", "시간"],
            "조건": ["잔고", "실행횟수", "시간", "리스크"],
            "액션": ["매수", "매도", "포지션관리"]
        }
        
        for category, components in categories.items():
            cat_tab = QWidget()
            cat_layout = QVBoxLayout()
            
            for component in components:
                comp_button = ComponentButton(component, category)
                comp_button.component_selected.connect(self.add_component)
                cat_layout.addWidget(comp_button)
            
            cat_layout.addStretch()
            cat_tab.setLayout(cat_layout)
            component_tabs.addTab(cat_tab, category)
        
        layout.addWidget(component_tabs)
        tab.setLayout(layout)
        return tab
    
    def create_strategy_view_panel(self):
        """구성된 전략 보기 패널"""
        group = QGroupBox("구성된 전략 요소")
        layout = QVBoxLayout()
        
        # 모드별 정보 표시
        self.strategy_info_label = QLabel("전략을 구성해보세요")
        self.strategy_info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(self.strategy_info_label)
        
        # 규칙/컴포넌트 목록
        self.strategy_items_list = QListWidget()
        self.strategy_items_list.itemClicked.connect(self.item_selected)
        layout.addWidget(self.strategy_items_list)
        
        # 제어 버튼들
        button_layout = QHBoxLayout()
        
        self.edit_item_btn = QPushButton("편집")
        self.edit_item_btn.clicked.connect(self.edit_selected_item)
        button_layout.addWidget(self.edit_item_btn)
        
        self.remove_item_btn = QPushButton("제거") 
        self.remove_item_btn.clicked.connect(self.remove_selected_item)
        button_layout.addWidget(self.remove_item_btn)
        
        self.clear_all_btn = QPushButton("모두 제거")
        self.clear_all_btn.clicked.connect(self.clear_all_items)
        button_layout.addWidget(self.clear_all_btn)
        
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group
    
    def create_detail_config_panel(self):
        """상세 설정 패널"""
        group = QGroupBox("상세 설정")
        layout = QVBoxLayout()
        
        self.config_scroll = QScrollArea()
        self.config_widget = QWidget()
        self.config_layout = QFormLayout()
        
        # 기본 메시지
        self.config_layout.addRow(QLabel("항목을 선택하여 설정을 변경하세요"))
        
        self.config_widget.setLayout(self.config_layout)
        self.config_scroll.setWidget(self.config_widget)
        self.config_scroll.setWidgetResizable(True)
        
        layout.addWidget(self.config_scroll)
        group.setLayout(layout)
        return group
    
    def create_json_preview_panel(self):
        """JSON 미리보기 패널"""
        group = QGroupBox("전략 JSON 미리보기")
        layout = QVBoxLayout()
        
        # 제어 버튼들
        button_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("📁 불러오기")
        self.load_btn.clicked.connect(self.load_strategy)
        button_layout.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("💾 저장")
        self.save_btn.clicked.connect(self.save_strategy)
        button_layout.addWidget(self.save_btn)
        
        self.copy_btn = QPushButton("📋 복사")
        self.copy_btn.clicked.connect(self.copy_json)
        button_layout.addWidget(self.copy_btn)
        
        layout.addLayout(button_layout)
        
        # 전략 통계
        self.strategy_stats = QLabel("규칙: 0개 | 컴포넌트: 0개")
        self.strategy_stats.setStyleSheet("color: #7f8c8d; padding: 5px;")
        layout.addWidget(self.strategy_stats)
        
        # JSON 텍스트 영역
        self.json_preview = QTextEdit()
        self.json_preview.setFont(QFont("Consolas", 10))
        layout.addWidget(self.json_preview)
        
        group.setLayout(layout)
        return group
    
    def setup_connections(self):
        """시그널 연결"""
        self.strategy_name_edit.textChanged.connect(self.update_strategy_meta)
        self.strategy_id_edit.textChanged.connect(self.update_strategy_meta)
        self.strategy_type_combo.currentTextChanged.connect(self.update_strategy_meta)
    
    def add_template_rule(self, template_id: str):
        """템플릿 규칙 추가"""
        template_info = CORE_STRATEGY_TEMPLATES[template_id]
        
        rule_data = {
            "type": "template_rule",
            "template_id": template_id,
            "rule_id": f"{template_id}_{len(self.current_strategy['rules']) + 1}",
            "name": template_info["name"],
            "role": template_info["role"],
            "activation_state": template_info["activation_state"],
            "icon": template_info["icon"],
            "color": template_info["color"],
            "config": {}  # 기본값은 템플릿에서 가져옴
        }
        
        self.current_strategy["rules"].append(rule_data)
        self.update_strategy_view()
        self.update_json_preview()
    
    def add_component(self, component_name: str, category: str):
        """개별 컴포넌트 추가"""
        component_data = {
            "type": "component",
            "component_name": component_name,
            "category": category,
            "config": {}
        }
        
        self.current_strategy["rules"].append(component_data)
        self.update_strategy_view()
        self.update_json_preview()
    
    def update_strategy_view(self):
        """전략 뷰 업데이트"""
        self.strategy_items_list.clear()
        
        rule_count = 0
        component_count = 0
        
        for i, item in enumerate(self.current_strategy["rules"]):
            if item["type"] == "template_rule":
                rule_count += 1
                item_text = f"{item['icon']} {item['name']} ({item['role']})"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.ItemDataRole.UserRole, i)
                
                # 색상 설정
                color = QColor(item["color"])
                list_item.setBackground(color.lighter(180))
                
                self.strategy_items_list.addItem(list_item)
                
            elif item["type"] == "component":
                component_count += 1
                item_text = f"🧩 {item['component_name']} ({item['category']})"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.ItemDataRole.UserRole, i)
                
                self.strategy_items_list.addItem(list_item)
        
        # 통계 업데이트
        self.strategy_stats.setText(f"규칙: {rule_count}개 | 컴포넌트: {component_count}개")
        
        # 정보 라벨 업데이트
        total_items = rule_count + component_count
        if total_items == 0:
            self.strategy_info_label.setText("전략을 구성해보세요")
        else:
            self.strategy_info_label.setText(f"총 {total_items}개 요소로 구성된 {self.current_strategy['type']} 전략")
    
    def item_selected(self, item):
        """항목 선택 시 상세 설정 표시"""
        item_index = item.data(Qt.ItemDataRole.UserRole)
        item_data = self.current_strategy["rules"][item_index]
        
        self.show_item_config(item_data, item_index)
    
    def show_item_config(self, item_data: dict, item_index: int):
        """항목 설정 표시"""
        # 기존 위젯 제거
        while self.config_layout.count():
            child = self.config_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if item_data["type"] == "template_rule":
            # 템플릿 규칙 설정
            title_label = QLabel(f"🎯 {item_data['name']} 설정")
            title_label.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
            self.config_layout.addRow(title_label)
            
            desc_label = QLabel(CORE_STRATEGY_TEMPLATES[item_data['template_id']]["description"])
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
            self.config_layout.addRow(desc_label)
            
            # TODO: 템플릿별 설정 필드 생성
            self.config_layout.addRow(QLabel("템플릿 기반 설정 (구현 예정)"))
            
        elif item_data["type"] == "component":
            # 개별 컴포넌트 설정
            title_label = QLabel(f"🧩 {item_data['component_name']} 설정")
            title_label.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
            self.config_layout.addRow(title_label)
            
            self.config_layout.addRow(QLabel("컴포넌트 설정 (구현 예정)"))
    
    def edit_selected_item(self):
        """선택된 항목 편집"""
        # TODO: 상세 편집 다이얼로그
        pass
    
    def remove_selected_item(self):
        """선택된 항목 제거"""
        current_item = self.strategy_items_list.currentItem()
        if current_item:
            item_index = current_item.data(Qt.ItemDataRole.UserRole)
            del self.current_strategy["rules"][item_index]
            self.update_strategy_view()
            self.update_json_preview()
    
    def clear_all_items(self):
        """모든 항목 제거"""
        self.current_strategy["rules"] = []
        self.update_strategy_view()
        self.update_json_preview()
    
    def update_strategy_meta(self):
        """전략 메타데이터 업데이트"""
        self.current_strategy["strategy_name"] = self.strategy_name_edit.text()
        self.current_strategy["strategy_id"] = self.strategy_id_edit.text()
        self.current_strategy["type"] = self.strategy_type_combo.currentText()
        self.update_json_preview()
    
    def update_json_preview(self):
        """JSON 미리보기 업데이트"""
        json_str = json.dumps(self.current_strategy, indent=2, ensure_ascii=False)
        self.json_preview.setPlainText(json_str)
    
    def load_strategy(self):
        """전략 불러오기"""
        # TODO: 파일 다이얼로그 구현
        print("전략 불러오기 (구현 예정)")
    
    def save_strategy(self):
        """전략 저장"""
        # TODO: 파일 다이얼로그 구현
        print("전략 저장 (구현 예정)")
    
    def copy_json(self):
        """JSON 클립보드 복사"""
        QApplication.clipboard().setText(self.json_preview.toPlainText())
        print("JSON이 클립보드에 복사되었습니다.")


class TemplateRuleButton(QPushButton):
    """템플릿 규칙 선택 버튼"""
    
    rule_selected = pyqtSignal(str)
    
    def __init__(self, template_id: str, template_info: dict):
        super().__init__()
        self.template_id = template_id
        self.template_info = template_info
        
        self.setText(f"{template_info['icon']} {template_info['name']}")
        self.setMinimumHeight(70)
        self.setToolTip(template_info['description'])
        
        # 스타일 설정
        color = template_info['color']
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 2px solid {color};
                color: white;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
                text-align: left;
                padding: 10px;
                margin: 2px;
            }}
            QPushButton:hover {{
                background-color: {QColor(color).lighter(120).name()};
                transform: scale(1.02);
            }}
            QPushButton:pressed {{
                background-color: {QColor(color).darker(120).name()};
            }}
        """)
        
        self.clicked.connect(lambda: self.rule_selected.emit(self.template_id))


class ComponentButton(QPushButton):
    """개별 컴포넌트 선택 버튼"""
    
    component_selected = pyqtSignal(str, str)
    
    def __init__(self, component_name: str, category: str):
        super().__init__()
        self.component_name = component_name
        self.category = category
        
        # 카테고리별 아이콘
        icons = {
            "트리거": "⚡",
            "조건": "🔍", 
            "액션": "🎯"
        }
        
        self.setText(f"{icons.get(category, '🔧')} {component_name}")
        self.setMinimumHeight(50)
        self.setToolTip(f"{category} 컴포넌트: {component_name}")
        
        # 카테고리별 색상
        colors = {
            "트리거": "#3498db",
            "조건": "#f39c12",
            "액션": "#27ae60"
        }
        
        color = colors.get(category, "#95a5a6")
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 1px solid {color};
                color: white;
                border-radius: 8px;
                font-size: 11px;
                font-weight: bold;
                text-align: center;
                padding: 8px;
                margin: 1px;
            }}
            QPushButton:hover {{
                background-color: {QColor(color).lighter(120).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(color).darker(120).name()};
            }}
        """)
        
        self.clicked.connect(lambda: self.component_selected.emit(self.component_name, self.category))


def main():
    app = QApplication(sys.argv)
    
    # 한글 폰트 설정
    font = QFont("맑은 고딕", 9)
    app.setFont(font)
    
    window = UnifiedStrategyMaker()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
