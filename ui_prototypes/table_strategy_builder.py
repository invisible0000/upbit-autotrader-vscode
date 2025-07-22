"""
테이블 기반 전략 빌더 UI
Table-Based Strategy Builder

사용자 친화적인 테이블 형태의 전략 구성 인터페이스
"""

import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from typing import Dict, List, Any, Optional
import json

class TriggerRelation(QWidget):
    """트리거 간 관계 설정 위젯"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        
        # AND/OR 선택
        self.relation_combo = QComboBox()
        self.relation_combo.addItems(["AND (모든 조건)", "OR (하나만 충족)"])
        
        # 우선순위 설정
        layout.addWidget(QLabel("트리거 관계:"))
        layout.addWidget(self.relation_combo)
        layout.addWidget(QLabel("우선순위:"))
        
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 100)
        self.priority_spin.setValue(10)
        layout.addWidget(self.priority_spin)
        
        self.setLayout(layout)
    
    def get_relation(self) -> Dict[str, Any]:
        return {
            "type": "AND" if self.relation_combo.currentIndex() == 0 else "OR",
            "priority": self.priority_spin.value()
        }

class TriggerConfigWidget(QWidget):
    """트리거 설정 위젯"""
    
    def __init__(self, trigger_type: str):
        super().__init__()
        self.trigger_type = trigger_type
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        if self.trigger_type == "RSI":
            # RSI 설정
            self.threshold_spin = QSpinBox()
            self.threshold_spin.setRange(0, 100)
            self.threshold_spin.setValue(30)
            layout.addRow("임계값:", self.threshold_spin)
            
            self.direction_combo = QComboBox()
            self.direction_combo.addItems(["이하 (<=)", "이상 (>=)", "미만 (<)", "초과 (>)"])
            layout.addRow("조건:", self.direction_combo)
            
            self.period_spin = QSpinBox()
            self.period_spin.setRange(5, 50)
            self.period_spin.setValue(14)
            layout.addRow("기간:", self.period_spin)
            
        elif self.trigger_type == "MACD":
            # MACD 설정
            self.signal_combo = QComboBox()
            self.signal_combo.addItems(["골든크로스", "데드크로스", "히스토그램 > 0", "히스토그램 < 0"])
            layout.addRow("신호:", self.signal_combo)
            
            self.fast_spin = QSpinBox()
            self.fast_spin.setRange(5, 50)
            self.fast_spin.setValue(12)
            layout.addRow("빠른선:", self.fast_spin)
            
            self.slow_spin = QSpinBox()
            self.slow_spin.setRange(10, 100)
            self.slow_spin.setValue(26)
            layout.addRow("느린선:", self.slow_spin)
            
        elif self.trigger_type == "가격변동":
            # 가격 변동 설정
            self.change_type = QComboBox()
            self.change_type.addItems(["구매가 대비", "전일 종가 대비", "최고가 대비", "최저가 대비"])
            layout.addRow("기준:", self.change_type)
            
            self.change_percent = QDoubleSpinBox()
            self.change_percent.setRange(-50.0, 50.0)
            self.change_percent.setValue(5.0)
            self.change_percent.setSuffix("%")
            layout.addRow("변동률:", self.change_percent)
            
            self.direction_combo = QComboBox()
            self.direction_combo.addItems(["상승", "하락", "상승/하락 모두"])
            layout.addRow("방향:", self.direction_combo)
        
        self.setLayout(layout)
    
    def get_config(self) -> Dict[str, Any]:
        if self.trigger_type == "RSI":
            direction_map = {0: "<=", 1: ">=", 2: "<", 3: ">"}
            return {
                "threshold": self.threshold_spin.value(),
                "direction": direction_map[self.direction_combo.currentIndex()],
                "period": self.period_spin.value()
            }
        elif self.trigger_type == "MACD":
            signal_map = {0: "golden_cross", 1: "dead_cross", 2: "histogram_positive", 3: "histogram_negative"}
            return {
                "signal": signal_map[self.signal_combo.currentIndex()],
                "fast_period": self.fast_spin.value(),
                "slow_period": self.slow_spin.value()
            }
        elif self.trigger_type == "가격변동":
            base_map = {0: "buy_price", 1: "prev_close", 2: "high_price", 3: "low_price"}
            direction_map = {0: "up", 1: "down", 2: "both"}
            return {
                "base_price": base_map[self.change_type.currentIndex()],
                "change_percent": self.change_percent.value(),
                "direction": direction_map[self.direction_combo.currentIndex()]
            }
        return {}

class ActionConfigWidget(QWidget):
    """액션 설정 위젯"""
    
    def __init__(self, action_type: str):
        super().__init__()
        self.action_type = action_type
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        if self.action_type == "매수":
            # 매수 설정
            self.amount_type = QComboBox()
            self.amount_type.addItems(["전량", "고정 금액", "비율", "매수 카운트 기준"])
            layout.addRow("금액 방식:", self.amount_type)
            
            self.amount_value = QDoubleSpinBox()
            self.amount_value.setRange(1.0, 100.0)
            self.amount_value.setValue(10.0)
            layout.addRow("금액/비율:", self.amount_value)
            
            self.max_count = QSpinBox()
            self.max_count.setRange(1, 10)
            self.max_count.setValue(3)
            layout.addRow("최대 매수 횟수:", self.max_count)
            
        elif self.action_type == "매도":
            # 매도 설정
            self.sell_type = QComboBox()
            self.sell_type.addItems(["전량", "일부 (고정)", "일부 (비율)", "단계적"])
            layout.addRow("매도 방식:", self.sell_type)
            
            self.sell_amount = QDoubleSpinBox()
            self.sell_amount.setRange(1.0, 100.0)
            self.sell_amount.setValue(100.0)
            layout.addRow("매도량 (%):", self.sell_amount)
        
        elif self.action_type == "감시":
            # 감시 설정
            self.watch_duration = QSpinBox()
            self.watch_duration.setRange(1, 3600)
            self.watch_duration.setValue(60)
            self.watch_duration.setSuffix("초")
            layout.addRow("감시 시간:", self.watch_duration)
            
            self.check_interval = QSpinBox()
            self.check_interval.setRange(1, 60)
            self.check_interval.setValue(5)
            self.check_interval.setSuffix("초")
            layout.addRow("체크 주기:", self.check_interval)
        
        self.setLayout(layout)
    
    def get_config(self) -> Dict[str, Any]:
        if self.action_type == "매수":
            amount_types = ["full", "fixed", "percent", "buy_count"]
            return {
                "amount_type": amount_types[self.amount_type.currentIndex()],
                "amount_value": self.amount_value.value(),
                "max_count": self.max_count.value()
            }
        elif self.action_type == "매도":
            sell_types = ["full", "fixed", "percent", "staged"]
            return {
                "sell_type": sell_types[self.sell_type.currentIndex()],
                "sell_amount": self.sell_amount.value()
            }
        elif self.action_type == "감시":
            return {
                "duration": self.watch_duration.value(),
                "interval": self.check_interval.value()
            }
        return {}

class StrategyRuleRow(QWidget):
    """전략 규칙 한 줄"""
    
    remove_requested = pyqtSignal(object)  # 삭제 요청 신호
    
    def __init__(self, rule_id: str = ""):
        super().__init__()
        self.rule_id = rule_id or f"rule_{id(self)}"
        self.trigger_configs = []
        self.action_config = None
        self.condition_configs = []
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        
        # 규칙 이름
        self.rule_name = QLineEdit()
        self.rule_name.setPlaceholderText("규칙 이름")
        self.rule_name.setText(self.rule_id)
        layout.addWidget(self.rule_name)
        
        # 포지션 상태
        self.position_state = QComboBox()
        self.position_state.addItems(["대기 (READY)", "활성 (ACTIVE)"])
        layout.addWidget(self.position_state)
        
        # 트리거 버튼
        self.triggers_btn = QPushButton("트리거 설정")
        self.triggers_btn.clicked.connect(self.setup_triggers)
        layout.addWidget(self.triggers_btn)
        
        # 액션 버튼
        self.action_btn = QPushButton("액션 설정")
        self.action_btn.clicked.connect(self.setup_action)
        layout.addWidget(self.action_btn)
        
        # 조건 버튼
        self.conditions_btn = QPushButton("조건 설정")
        self.conditions_btn.clicked.connect(self.setup_conditions)
        layout.addWidget(self.conditions_btn)
        
        # 삭제 버튼
        self.delete_btn = QPushButton("❌")
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        layout.addWidget(self.delete_btn)
        
        self.setLayout(layout)
        self.update_button_states()
    
    def setup_triggers(self):
        """트리거 설정 다이얼로그"""
        dialog = QDialog(self)
        dialog.setWindowTitle("트리거 설정")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # 현재 트리거 목록
        triggers_group = QGroupBox("현재 트리거들")
        triggers_layout = QVBoxLayout()
        
        self.trigger_list = QListWidget()
        self.update_trigger_list()
        triggers_layout.addWidget(self.trigger_list)
        
        # 트리거 추가 버튼들
        add_buttons_layout = QHBoxLayout()
        
        add_rsi_btn = QPushButton("+ RSI 트리거")
        add_rsi_btn.clicked.connect(lambda: self.add_trigger("RSI"))
        add_buttons_layout.addWidget(add_rsi_btn)
        
        add_macd_btn = QPushButton("+ MACD 트리거")  
        add_macd_btn.clicked.connect(lambda: self.add_trigger("MACD"))
        add_buttons_layout.addWidget(add_macd_btn)
        
        add_price_btn = QPushButton("+ 가격변동 트리거")
        add_price_btn.clicked.connect(lambda: self.add_trigger("가격변동"))
        add_buttons_layout.addWidget(add_price_btn)
        
        triggers_layout.addLayout(add_buttons_layout)
        
        # 트리거 관계 설정
        if len(self.trigger_configs) > 1:
            self.trigger_relation = TriggerRelation()
            triggers_layout.addWidget(self.trigger_relation)
        
        triggers_group.setLayout(triggers_layout)
        layout.addWidget(triggers_group)
        
        # 버튼
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_button_states()
    
    def add_trigger(self, trigger_type: str):
        """트리거 추가"""
        config_widget = TriggerConfigWidget(trigger_type)
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{trigger_type} 트리거 설정")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        layout.addWidget(config_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            trigger_config = {
                "type": trigger_type,
                "config": config_widget.get_config()
            }
            self.trigger_configs.append(trigger_config)
            self.update_trigger_list()
    
    def update_trigger_list(self):
        """트리거 목록 업데이트"""
        if hasattr(self, 'trigger_list'):
            self.trigger_list.clear()
            for i, trigger in enumerate(self.trigger_configs):
                item_text = f"{i+1}. {trigger['type']} - {trigger['config']}"
                self.trigger_list.addItem(item_text)
    
    def setup_action(self):
        """액션 설정 다이얼로그"""
        dialog = QDialog(self)
        dialog.setWindowTitle("액션 설정")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        # 액션 타입 선택
        action_type_group = QGroupBox("액션 타입")
        action_type_layout = QHBoxLayout()
        
        self.action_type_combo = QComboBox()
        self.action_type_combo.addItems(["매수", "매도", "감시"])
        action_type_layout.addWidget(self.action_type_combo)
        action_type_group.setLayout(action_type_layout)
        layout.addWidget(action_type_group)
        
        # 액션 설정
        self.action_config_widget = ActionConfigWidget("매수")
        layout.addWidget(self.action_config_widget)
        
        # 액션 타입 변경 시 설정 위젯 업데이트
        def update_action_config():
            layout.removeWidget(self.action_config_widget)
            self.action_config_widget.deleteLater()
            self.action_config_widget = ActionConfigWidget(self.action_type_combo.currentText())
            layout.insertWidget(-1, self.action_config_widget)
        
        self.action_type_combo.currentTextChanged.connect(update_action_config)
        
        # 버튼
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.action_config = {
                "type": self.action_type_combo.currentText(),
                "config": self.action_config_widget.get_config()
            }
            self.update_button_states()
    
    def setup_conditions(self):
        """조건 설정 다이얼로그"""
        dialog = QDialog(self)
        dialog.setWindowTitle("실행 조건 설정")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # 조건 목록
        conditions_group = QGroupBox("실행 조건들")
        conditions_layout = QVBoxLayout()
        
        # 잔고 확인
        self.balance_check = QCheckBox("잔고 확인 (매수 시에만)")
        self.balance_min = QSpinBox()
        self.balance_min.setRange(10000, 10000000)
        self.balance_min.setValue(100000)
        self.balance_min.setSuffix("원")
        
        balance_layout = QHBoxLayout()
        balance_layout.addWidget(self.balance_check)
        balance_layout.addWidget(QLabel("최소:"))
        balance_layout.addWidget(self.balance_min)
        conditions_layout.addLayout(balance_layout)
        
        # 실행 횟수 제한
        self.execution_limit = QCheckBox("실행 횟수 제한")
        self.max_executions = QSpinBox()
        self.max_executions.setRange(1, 100)
        self.max_executions.setValue(3)
        
        execution_layout = QHBoxLayout()
        execution_layout.addWidget(self.execution_limit)
        execution_layout.addWidget(QLabel("최대:"))
        execution_layout.addWidget(self.max_executions)
        execution_layout.addWidget(QLabel("회"))
        conditions_layout.addLayout(execution_layout)
        
        # 포지션 크기 제한
        self.position_limit = QCheckBox("포지션 크기 제한")
        self.max_position = QDoubleSpinBox()
        self.max_position.setRange(1.0, 100.0)
        self.max_position.setValue(20.0)
        self.max_position.setSuffix("%")
        
        position_layout = QHBoxLayout()
        position_layout.addWidget(self.position_limit)
        position_layout.addWidget(QLabel("최대:"))
        position_layout.addWidget(self.max_position)
        conditions_layout.addLayout(position_layout)
        
        conditions_group.setLayout(conditions_layout)
        layout.addWidget(conditions_group)
        
        # 버튼
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.condition_configs = []
            
            if self.balance_check.isChecked():
                self.condition_configs.append({
                    "type": "balance_check",
                    "min_balance": self.balance_min.value()
                })
            
            if self.execution_limit.isChecked():
                self.condition_configs.append({
                    "type": "execution_limit", 
                    "max_executions": self.max_executions.value()
                })
            
            if self.position_limit.isChecked():
                self.condition_configs.append({
                    "type": "position_limit",
                    "max_position_percent": self.max_position.value()
                })
            
            self.update_button_states()
    
    def update_button_states(self):
        """버튼 상태 업데이트"""
        # 트리거 버튼
        trigger_count = len(self.trigger_configs)
        if trigger_count == 0:
            self.triggers_btn.setText("트리거 설정 ❗")
            self.triggers_btn.setStyleSheet("background-color: #ffcccc;")
        else:
            self.triggers_btn.setText(f"트리거 설정 ({trigger_count})")
            self.triggers_btn.setStyleSheet("background-color: #ccffcc;")
        
        # 액션 버튼
        if self.action_config is None:
            self.action_btn.setText("액션 설정 ❗")
            self.action_btn.setStyleSheet("background-color: #ffcccc;")
        else:
            self.action_btn.setText(f"액션 설정 ({self.action_config['type']})")
            self.action_btn.setStyleSheet("background-color: #ccffcc;")
        
        # 조건 버튼
        condition_count = len(self.condition_configs)
        if condition_count == 0:
            self.conditions_btn.setText("조건 설정")
            self.conditions_btn.setStyleSheet("")
        else:
            self.conditions_btn.setText(f"조건 설정 ({condition_count})")
            self.conditions_btn.setStyleSheet("background-color: #ccffdd;")
    
    def to_dict(self) -> Dict[str, Any]:
        """규칙을 딕셔너리로 변환"""
        return {
            "rule_id": self.rule_name.text() or self.rule_id,
            "activation_state": "READY" if self.position_state.currentIndex() == 0 else "ACTIVE",
            "triggers": self.trigger_configs,
            "action": self.action_config,
            "conditions": self.condition_configs,
            "priority": 10
        }

class TableBasedStrategyBuilder(QMainWindow):
    """테이블 기반 전략 빌더 메인 창"""
    
    def __init__(self):
        super().__init__()
        self.rule_rows = []
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("📊 테이블 기반 전략 빌더")
        self.setGeometry(100, 100, 1200, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("🎯 전략 규칙 관리")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 전략 정보
        strategy_info_group = QGroupBox("전략 기본 정보")
        strategy_info_layout = QFormLayout()
        
        self.strategy_name = QLineEdit()
        self.strategy_name.setPlaceholderText("예: RSI 하방 + 불타기 + 트레일링 스탑")
        strategy_info_layout.addRow("전략 이름:", self.strategy_name)
        
        self.strategy_desc = QTextEdit()
        self.strategy_desc.setMaximumHeight(60)
        self.strategy_desc.setPlaceholderText("전략 설명을 간단히 입력하세요...")
        strategy_info_layout.addRow("설명:", self.strategy_desc)
        
        strategy_info_group.setLayout(strategy_info_layout)
        layout.addWidget(strategy_info_group)
        
        # 규칙 목록
        rules_group = QGroupBox("전략 규칙들")
        rules_layout = QVBoxLayout()
        
        # 헤더
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("규칙 이름"))
        header_layout.addWidget(QLabel("포지션 상태"))
        header_layout.addWidget(QLabel("트리거"))
        header_layout.addWidget(QLabel("액션"))
        header_layout.addWidget(QLabel("조건"))
        header_layout.addWidget(QLabel(""))
        rules_layout.addLayout(header_layout)
        
        # 규칙 목록 스크롤 영역
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.rules_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        rules_layout.addWidget(scroll_area)
        
        # 규칙 추가 버튼
        add_rule_btn = QPushButton("➕ 새 규칙 추가")
        add_rule_btn.clicked.connect(self.add_rule)
        add_rule_btn.setStyleSheet("font-size: 14px; padding: 10px; background-color: #4CAF50; color: white;")
        rules_layout.addWidget(add_rule_btn)
        
        rules_group.setLayout(rules_layout)
        layout.addWidget(rules_group)
        
        # 하단 버튼들
        buttons_layout = QHBoxLayout()
        
        # 전략 검증
        validate_btn = QPushButton("🔍 전략 검증")
        validate_btn.clicked.connect(self.validate_strategy)
        validate_btn.setStyleSheet("font-size: 14px; padding: 8px; background-color: #2196F3; color: white;")
        buttons_layout.addWidget(validate_btn)
        
        # JSON 보기
        show_json_btn = QPushButton("📋 JSON 보기")
        show_json_btn.clicked.connect(self.show_json)
        buttons_layout.addWidget(show_json_btn)
        
        # 저장
        save_btn = QPushButton("💾 전략 저장")
        save_btn.clicked.connect(self.save_strategy)
        save_btn.setStyleSheet("font-size: 14px; padding: 8px; background-color: #FF9800; color: white;")
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        
        central_widget.setLayout(layout)
        
        # 기본 규칙 하나 추가
        self.add_rule()
    
    def add_rule(self):
        """새 규칙 추가"""
        rule_row = StrategyRuleRow(f"rule_{len(self.rule_rows)+1}")
        rule_row.remove_requested.connect(self.remove_rule)
        
        self.rule_rows.append(rule_row)
        self.rules_layout.addWidget(rule_row)
    
    def remove_rule(self, rule_row):
        """규칙 삭제"""
        if len(self.rule_rows) > 1:  # 최소 하나는 유지
            self.rule_rows.remove(rule_row)
            self.rules_layout.removeWidget(rule_row)
            rule_row.deleteLater()
        else:
            QMessageBox.information(self, "알림", "최소 하나의 규칙은 필요합니다.")
    
    def validate_strategy(self):
        """전략 검증"""
        from advanced_strategy_validator import StrategyValidator
        
        strategy_data = self.get_strategy_data()
        validator = StrategyValidator()
        result = validator.validate_strategy(strategy_data)
        
        # 검증 결과 다이얼로그
        dialog = QDialog(self)
        dialog.setWindowTitle("🔍 전략 검증 결과")
        dialog.setModal(True)
        dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        # 검증 요약
        summary_text = f"""
        ✅ 실행 가능: {result.is_executable}
        📊 신뢰도: {result.confidence_score:.1f}%
        📝 완성도: {result.is_complete}
        """
        
        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet("font-size: 14px; background-color: #f0f0f0; padding: 10px; margin: 5px;")
        layout.addWidget(summary_label)
        
        # 이슈 목록
        issues_text = QTextEdit()
        issues_content = "📋 검증 이슈들:\n\n"
        
        for issue in result.issues:
            level_emoji = {"error": "❌", "warning": "⚠️", "critical": "🚨"}
            emoji = level_emoji.get(issue.level.value, "ℹ️")
            issues_content += f"{emoji} [{issue.level.value.upper()}] {issue.message}\n"
            issues_content += f"   💡 해결책: {issue.suggestion}\n\n"
        
        if not result.issues:
            issues_content += "🎉 모든 검증을 통과했습니다!"
        
        issues_text.setPlainText(issues_content)
        layout.addWidget(issues_text)
        
        # 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def show_json(self):
        """JSON 미리보기"""
        strategy_data = self.get_strategy_data()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📋 JSON 미리보기")
        dialog.setModal(True)
        dialog.resize(700, 500)
        
        layout = QVBoxLayout()
        
        json_text = QTextEdit()
        json_text.setPlainText(json.dumps(strategy_data, indent=2, ensure_ascii=False))
        json_text.setFont(QFont("Consolas", 10))
        layout.addWidget(json_text)
        
        # 복사 버튼
        copy_btn = QPushButton("📋 클립보드에 복사")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(json_text.toPlainText()))
        layout.addWidget(copy_btn)
        
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def save_strategy(self):
        """전략 저장"""
        strategy_data = self.get_strategy_data()
        
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "전략 저장", 
            f"{strategy_data.get('name', 'strategy')}.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(strategy_data, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "저장 완료", f"전략이 저장되었습니다:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "저장 실패", f"저장 중 오류가 발생했습니다:\n{e}")
    
    def get_strategy_data(self) -> Dict[str, Any]:
        """현재 전략 데이터 가져오기"""
        rules = []
        for rule_row in self.rule_rows:
            rule_data = rule_row.to_dict()
            if rule_data["triggers"] and rule_data["action"]:  # 완성된 규칙만 포함
                rules.append(rule_data)
        
        return {
            "strategy_id": f"strategy_{int(QDateTime.currentSecsSinceEpoch())}",
            "name": self.strategy_name.text() or "미명명 전략",
            "description": self.strategy_desc.toPlainText(),
            "created_at": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate),
            "rules": rules
        }

def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)
    
    # 스타일 설정
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin: 5px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QPushButton {
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 5px;
            background-color: white;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
    """)
    
    window = TableBasedStrategyBuilder()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
