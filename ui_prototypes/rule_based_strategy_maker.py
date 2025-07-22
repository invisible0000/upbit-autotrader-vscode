"""
규칙 기반 전략 메이커 UI
Rule-Based Strategy Maker UI

7개 핵심 규칙을 기반으로 한 전략 구성 인터페이스
"""
import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QScrollArea, QLabel, QPushButton, QFrame, QButtonGroup,
    QTabWidget, QTextEdit, QTreeWidget, QTreeWidgetItem, QListWidget,
    QListWidgetItem, QGroupBox, QFormLayout, QLineEdit, QSpinBox, 
    QDoubleSpinBox, QComboBox, QCheckBox, QSlider
)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal, QSize
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QFont, QColor, QIcon, QDrag
from typing import Dict, Any, List, Optional

# 7개 핵심 규칙 정의
CORE_RULES = {
    "rsi_oversold_entry": {
        "name": "RSI 과매도 진입",
        "role": "ENTRY",
        "description": "RSI 지표가 지정된 값 이하로 떨어지면 최초 진입합니다",
        "activation_state": "READY",
        "icon": "📈",
        "color": "#e74c3c",
        "config_fields": {
            "rsi_period": {"type": "int", "default": 14, "min": 5, "max": 50, "label": "RSI 기간"},
            "rsi_threshold": {"type": "int", "default": 20, "min": 10, "max": 40, "label": "과매도 임계값"},
            "amount_percent": {"type": "int", "default": 10, "min": 1, "max": 100, "label": "매수 비율(%)"}
        }
    },
    "profit_scale_in": {
        "name": "수익 시 불타기",
        "role": "SCALE_IN",
        "description": "수익률이 지정된 값에 도달할 때마다 정해진 횟수만큼 추가 매수합니다",
        "activation_state": "ACTIVE",
        "icon": "🔥",
        "color": "#f39c12",
        "config_fields": {
            "profit_threshold": {"type": "float", "default": 5.0, "min": 1.0, "max": 20.0, "label": "수익률 임계값(%)"},
            "max_executions": {"type": "int", "default": 3, "min": 1, "max": 10, "label": "최대 실행 횟수"},
            "amount": {"type": "int", "default": 100000, "min": 10000, "max": 1000000, "label": "추가 매수 금액"}
        }
    },
    "planned_exit": {
        "name": "계획된 익절",
        "role": "EXIT",
        "description": "불타기가 계획된 횟수를 모두 채운 후, 다음 수익 신호에 전량 매도합니다",
        "activation_state": "ACTIVE",
        "icon": "💰",
        "color": "#27ae60",
        "config_fields": {
            "target_rule_id": {"type": "string", "default": "profit_scale_in", "label": "대상 규칙 ID"},
            "required_executions": {"type": "int", "default": 3, "min": 1, "max": 10, "label": "필요 실행 횟수"}
        }
    },
    "trailing_stop": {
        "name": "트레일링 스탑",
        "role": "EXIT",
        "description": "지정된 수익률 도달 후, 고점 대비 일정 비율 하락 시 전량 매도합니다",
        "activation_state": "ACTIVE",
        "icon": "📉",
        "color": "#e67e22",
        "config_fields": {
            "activation_profit": {"type": "float", "default": 10.0, "min": 5.0, "max": 50.0, "label": "활성화 수익률(%)"},
            "trailing_percent": {"type": "float", "default": 3.0, "min": 1.0, "max": 10.0, "label": "트레일링 비율(%)"}
        }
    },
    "loss_averaging": {
        "name": "하락 시 물타기",
        "role": "SCALE_IN",
        "description": "평단가 대비 지정된 비율만큼 하락 시, 정해진 횟수만큼 추가 매수합니다",
        "activation_state": "ACTIVE",
        "icon": "⬇️",
        "color": "#9b59b6",
        "config_fields": {
            "loss_threshold": {"type": "float", "default": -5.0, "min": -20.0, "max": -1.0, "label": "하락률 임계값(%)"},
            "max_executions": {"type": "int", "default": 2, "min": 1, "max": 5, "label": "최대 실행 횟수"},
            "amount": {"type": "int", "default": 100000, "min": 10000, "max": 1000000, "label": "추가 매수 금액"}
        }
    },
    "crash_detection": {
        "name": "급락 감지",
        "role": "EXIT",
        "description": "단일 감시 주기 내에 가격이 폭락하면, 다른 모든 규칙을 무시하고 즉시 전량 매도합니다",
        "activation_state": "ACTIVE",
        "icon": "🚨",
        "color": "#c0392b",
        "config_fields": {
            "crash_threshold": {"type": "float", "default": -10.0, "min": -20.0, "max": -5.0, "label": "급락 임계값(%)"},
            "time_window": {"type": "int", "default": 5, "min": 1, "max": 30, "label": "감시 시간(분)"}
        }
    },
    "spike_hold": {
        "name": "급등 홀드",
        "role": "MANAGEMENT",
        "description": "단기간에 가격이 급등하면, 불타기 규칙을 일시 정지시켜 추격 매수의 위험을 막습니다",
        "activation_state": "ACTIVE",
        "icon": "🔒",
        "color": "#34495e",
        "config_fields": {
            "spike_threshold": {"type": "float", "default": 15.0, "min": 10.0, "max": 30.0, "label": "급등 임계값(%)"},
            "hold_duration": {"type": "int", "default": 30, "min": 10, "max": 120, "label": "홀드 시간(분)"}
        }
    }
}


class RuleBasedStrategyMaker(QMainWindow):
    """규칙 기반 전략 메이커 메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.current_strategy = {
            "strategy_id": "",
            "strategy_name": "새 전략",
            "rules": []
        }
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle("규칙 기반 전략 메이커 - Rule-Based Strategy Maker")
        self.setGeometry(100, 100, 1400, 900)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 좌측 패널 (규칙 팔레트)
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout()
        
        # 전략 메타데이터
        self.strategy_meta_panel = self.create_strategy_meta_panel()
        left_layout.addWidget(self.strategy_meta_panel)
        
        # 규칙 팔레트
        self.rule_palette = self.create_rule_palette()
        left_layout.addWidget(self.rule_palette)
        
        left_panel.setLayout(left_layout)
        main_layout.addWidget(left_panel)
        
        # 중앙 영역 (선택된 규칙들)
        center_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 선택된 규칙 목록
        self.selected_rules_panel = self.create_selected_rules_panel()
        center_splitter.addWidget(self.selected_rules_panel)
        
        # 규칙 설정 패널
        self.rule_config_panel = self.create_rule_config_panel()
        center_splitter.addWidget(self.rule_config_panel)
        
        center_splitter.setSizes([300, 400])
        main_layout.addWidget(center_splitter)
        
        # 우측 패널 (JSON 미리보기)
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        right_panel.setMaximumWidth(400)
        right_layout = QVBoxLayout()
        
        # JSON 미리보기
        self.json_preview_panel = self.create_json_preview_panel()
        right_layout.addWidget(self.json_preview_panel)
        
        right_panel.setLayout(right_layout)
        main_layout.addWidget(right_panel)
    
    def create_strategy_meta_panel(self):
        """전략 메타데이터 패널 생성"""
        group = QGroupBox("전략 정보")
        layout = QFormLayout()
        
        self.strategy_name_edit = QLineEdit()
        self.strategy_name_edit.setText("새 전략")
        layout.addRow("전략 이름:", self.strategy_name_edit)
        
        self.strategy_id_edit = QLineEdit()
        self.strategy_id_edit.setPlaceholderText("자동 생성됨")
        layout.addRow("전략 ID:", self.strategy_id_edit)
        
        group.setLayout(layout)
        return group
    
    def create_rule_palette(self):
        """규칙 팔레트 생성"""
        group = QGroupBox("7개 핵심 규칙")
        layout = QVBoxLayout()
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        for rule_id, rule_info in CORE_RULES.items():
            rule_button = RuleButton(rule_id, rule_info)
            rule_button.rule_selected.connect(self.add_rule_to_strategy)
            scroll_layout.addWidget(rule_button)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        group.setLayout(layout)
        return group
    
    def create_selected_rules_panel(self):
        """선택된 규칙 목록 패널"""
        group = QGroupBox("구성된 규칙 목록")
        layout = QVBoxLayout()
        
        self.selected_rules_list = QListWidget()
        self.selected_rules_list.itemClicked.connect(self.rule_selected)
        layout.addWidget(self.selected_rules_list)
        
        # 제어 버튼들
        button_layout = QHBoxLayout()
        
        self.remove_rule_btn = QPushButton("규칙 제거")
        self.remove_rule_btn.clicked.connect(self.remove_selected_rule)
        button_layout.addWidget(self.remove_rule_btn)
        
        self.clear_all_btn = QPushButton("모두 제거")
        self.clear_all_btn.clicked.connect(self.clear_all_rules)
        button_layout.addWidget(self.clear_all_btn)
        
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group
    
    def create_rule_config_panel(self):
        """규칙 설정 패널"""
        group = QGroupBox("규칙 설정")
        layout = QVBoxLayout()
        
        self.config_scroll = QScrollArea()
        self.config_widget = QWidget()
        self.config_layout = QFormLayout()
        
        # 기본 메시지
        self.config_layout.addRow(QLabel("규칙을 선택하여 설정을 변경하세요"))
        
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
        
        self.load_btn = QPushButton("불러오기")
        self.load_btn.clicked.connect(self.load_strategy)
        button_layout.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("저장")
        self.save_btn.clicked.connect(self.save_strategy)
        button_layout.addWidget(self.save_btn)
        
        self.copy_btn = QPushButton("복사")
        self.copy_btn.clicked.connect(self.copy_json)
        button_layout.addWidget(self.copy_btn)
        
        layout.addLayout(button_layout)
        
        # JSON 텍스트 영역
        self.json_preview = QTextEdit()
        self.json_preview.setFont(QFont("Consolas", 10))
        self.update_json_preview()
        layout.addWidget(self.json_preview)
        
        group.setLayout(layout)
        return group
    
    def setup_connections(self):
        """시그널 연결"""
        self.strategy_name_edit.textChanged.connect(self.update_strategy_meta)
        self.strategy_id_edit.textChanged.connect(self.update_strategy_meta)
    
    def add_rule_to_strategy(self, rule_id: str):
        """전략에 규칙 추가"""
        rule_info = CORE_RULES[rule_id]
        
        # 기본 설정값으로 규칙 생성
        rule_data = {
            "rule_id": rule_id,
            "name": rule_info["name"],
            "role": rule_info["role"],
            "activation_state": rule_info["activation_state"],
            "config": {}
        }
        
        # 기본값 설정
        for field_name, field_info in rule_info["config_fields"].items():
            rule_data["config"][field_name] = field_info["default"]
        
        self.current_strategy["rules"].append(rule_data)
        self.update_selected_rules_list()
        self.update_json_preview()
    
    def update_selected_rules_list(self):
        """선택된 규칙 목록 업데이트"""
        self.selected_rules_list.clear()
        
        for i, rule in enumerate(self.current_strategy["rules"]):
            rule_info = CORE_RULES[rule["rule_id"]]
            item_text = f"{i+1}. {rule['name']} ({rule['role']})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, i)  # 인덱스 저장
            
            # 색상 설정
            color = QColor(rule_info["color"])
            item.setBackground(color.lighter(180))
            
            self.selected_rules_list.addItem(item)
    
    def rule_selected(self, item):
        """규칙 선택 시 설정 패널 업데이트"""
        rule_index = item.data(Qt.ItemDataRole.UserRole)
        rule = self.current_strategy["rules"][rule_index]
        rule_info = CORE_RULES[rule["rule_id"]]
        
        self.show_rule_config(rule, rule_info, rule_index)
    
    def show_rule_config(self, rule: dict, rule_info: dict, rule_index: int):
        """규칙 설정 표시"""
        # 기존 위젯 제거
        while self.config_layout.count():
            child = self.config_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 규칙 정보 표시
        title_label = QLabel(f"🔧 {rule['name']} 설정")
        title_label.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
        self.config_layout.addRow(title_label)
        
        desc_label = QLabel(rule_info["description"])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        self.config_layout.addRow(desc_label)
        
        # 설정 필드들
        for field_name, field_info in rule_info["config_fields"].items():
            widget = self.create_config_widget(field_info, rule["config"][field_name])
            widget.setProperty("rule_index", rule_index)
            widget.setProperty("field_name", field_name)
            
            # 값 변경 시그널 연결
            if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                widget.valueChanged.connect(self.config_value_changed)
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.config_value_changed)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(self.config_value_changed)
            
            self.config_layout.addRow(field_info["label"] + ":", widget)
    
    def create_config_widget(self, field_info: dict, current_value):
        """설정 위젯 생성"""
        field_type = field_info["type"]
        
        if field_type == "int":
            widget = QSpinBox()
            widget.setMinimum(field_info.get("min", 0))
            widget.setMaximum(field_info.get("max", 999999))
            widget.setValue(current_value)
            return widget
        
        elif field_type == "float":
            widget = QDoubleSpinBox()
            widget.setMinimum(field_info.get("min", 0.0))
            widget.setMaximum(field_info.get("max", 999999.0))
            widget.setDecimals(1)
            widget.setValue(current_value)
            return widget
        
        elif field_type == "string":
            widget = QLineEdit()
            widget.setText(str(current_value))
            return widget
        
        else:
            widget = QLineEdit()
            widget.setText(str(current_value))
            return widget
    
    def config_value_changed(self):
        """설정값 변경 처리"""
        sender = self.sender()
        rule_index = sender.property("rule_index")
        field_name = sender.property("field_name")
        
        # 새 값 가져오기
        if isinstance(sender, QSpinBox) or isinstance(sender, QDoubleSpinBox):
            new_value = sender.value()
        elif isinstance(sender, QLineEdit):
            new_value = sender.text()
        elif isinstance(sender, QComboBox):
            new_value = sender.currentText()
        else:
            new_value = str(sender.text())
        
        # 전략 데이터 업데이트
        self.current_strategy["rules"][rule_index]["config"][field_name] = new_value
        self.update_json_preview()
    
    def remove_selected_rule(self):
        """선택된 규칙 제거"""
        current_item = self.selected_rules_list.currentItem()
        if current_item:
            rule_index = current_item.data(Qt.ItemDataRole.UserRole)
            del self.current_strategy["rules"][rule_index]
            self.update_selected_rules_list()
            self.update_json_preview()
            
            # 설정 패널 초기화
            while self.config_layout.count():
                child = self.config_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self.config_layout.addRow(QLabel("규칙을 선택하여 설정을 변경하세요"))
    
    def clear_all_rules(self):
        """모든 규칙 제거"""
        self.current_strategy["rules"] = []
        self.update_selected_rules_list()
        self.update_json_preview()
        
        # 설정 패널 초기화
        while self.config_layout.count():
            child = self.config_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.config_layout.addRow(QLabel("규칙을 선택하여 설정을 변경하세요"))
    
    def update_strategy_meta(self):
        """전략 메타데이터 업데이트"""
        self.current_strategy["strategy_name"] = self.strategy_name_edit.text()
        self.current_strategy["strategy_id"] = self.strategy_id_edit.text()
        self.update_json_preview()
    
    def update_json_preview(self):
        """JSON 미리보기 업데이트"""
        json_str = json.dumps(self.current_strategy, indent=2, ensure_ascii=False)
        self.json_preview.setPlainText(json_str)
    
    def load_strategy(self):
        """전략 불러오기"""
        # TODO: 파일 다이얼로그 구현
        pass
    
    def save_strategy(self):
        """전략 저장"""
        # TODO: 파일 다이얼로그 구현
        pass
    
    def copy_json(self):
        """JSON 클립보드 복사"""
        QApplication.clipboard().setText(self.json_preview.toPlainText())


class RuleButton(QPushButton):
    """규칙 선택 버튼"""
    
    rule_selected = pyqtSignal(str)
    
    def __init__(self, rule_id: str, rule_info: dict):
        super().__init__()
        self.rule_id = rule_id
        self.rule_info = rule_info
        
        self.setText(f"{rule_info['icon']} {rule_info['name']}")
        self.setMinimumHeight(60)
        self.setToolTip(rule_info['description'])
        
        # 스타일 설정
        color = rule_info['color']
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 2px solid {color};
                color: white;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                text-align: left;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {QColor(color).lighter(120).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(color).darker(120).name()};
            }}
        """)
        
        self.clicked.connect(lambda: self.rule_selected.emit(self.rule_id))


def main():
    app = QApplication(sys.argv)
    
    # 한글 폰트 설정
    font = QFont("맑은 고딕", 9)
    app.setFont(font)
    
    window = RuleBasedStrategyMaker()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
