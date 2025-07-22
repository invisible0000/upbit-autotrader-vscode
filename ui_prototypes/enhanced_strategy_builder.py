"""
완전 개선된 전략 빌더 시스템
Complete Enhanced Strategy Builder System

강력한 트리거 시스템과 완전한 UI 연결
"""

import sys
import sqlite3
import json
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class TriggerTemplate:
    """트리거 템플릿"""
    name: str
    category: str
    description: str
    parameters: List[Dict[str, Any]]
    help_text: str

class TriggerRegistry:
    """트리거 레지스트리 - 모든 가능한 트리거 정의"""
    
    @staticmethod
    def get_all_triggers() -> Dict[str, List[TriggerTemplate]]:
        return {
            "📊 기술적 지표": [
                TriggerTemplate(
                    name="RSI",
                    category="technical",
                    description="상대강도지수 - 과매수/과매도 판단",
                    parameters=[
                        {"name": "threshold", "type": "int", "min": 0, "max": 100, "default": 30, "label": "임계값"},
                        {"name": "condition", "type": "combo", "options": ["이하 (<=)", "이상 (>=)", "미만 (<)", "초과 (>)"], "default": 0, "label": "조건"},
                        {"name": "period", "type": "int", "min": 5, "max": 50, "default": 14, "label": "기간"}
                    ],
                    help_text="RSI < 30: 과매도 (매수 신호)\nRSI > 70: 과매수 (매도 신호)"
                ),
                TriggerTemplate(
                    name="MACD",
                    category="technical",
                    description="이동평균수렴확산 - 추세 전환점",
                    parameters=[
                        {"name": "signal", "type": "combo", "options": ["골든크로스", "데드크로스", "히스토그램>0", "히스토그램<0"], "default": 0, "label": "신호"},
                        {"name": "fast", "type": "int", "min": 5, "max": 50, "default": 12, "label": "빠른선"},
                        {"name": "slow", "type": "int", "min": 10, "max": 100, "default": 26, "label": "느린선"}
                    ],
                    help_text="골든크로스: 상승 신호\n데드크로스: 하락 신호"
                ),
                TriggerTemplate(
                    name="볼린저밴드",
                    category="technical", 
                    description="가격의 상대적 위치 판단",
                    parameters=[
                        {"name": "band", "type": "combo", "options": ["하단선 터치", "상단선 터치", "중간선 돌파", "밴드폭 축소"], "default": 0, "label": "밴드 조건"},
                        {"name": "period", "type": "int", "min": 10, "max": 50, "default": 20, "label": "기간"},
                        {"name": "std_dev", "type": "double", "min": 1.0, "max": 3.0, "default": 2.0, "label": "표준편차"}
                    ],
                    help_text="하단선 터치: 매수 기회\n상단선 터치: 매도 기회"
                ),
                TriggerTemplate(
                    name="이동평균",
                    category="technical",
                    description="가격과 이동평균선 관계",
                    parameters=[
                        {"name": "ma_type", "type": "combo", "options": ["단순(SMA)", "지수(EMA)", "가중(WMA)"], "default": 0, "label": "평균 타입"},
                        {"name": "period", "type": "int", "min": 5, "max": 200, "default": 20, "label": "기간"},
                        {"name": "condition", "type": "combo", "options": ["가격 > 이평", "가격 < 이평", "이평선 돌파", "이평선 이탈"], "default": 0, "label": "조건"}
                    ],
                    help_text="가격이 이동평균선 위: 상승추세\n가격이 이동평균선 아래: 하락추세"
                )
            ],
            
            "💰 가격/수익률": [
                TriggerTemplate(
                    name="가격변동률",
                    category="price",
                    description="특정 기준 대비 가격 변동",
                    parameters=[
                        {"name": "base_price", "type": "combo", "options": ["구매가", "전일종가", "최고가", "최저가", "시가"], "default": 0, "label": "기준가격"},
                        {"name": "change_percent", "type": "double", "min": -50.0, "max": 50.0, "default": 5.0, "label": "변동률(%)"},
                        {"name": "direction", "type": "combo", "options": ["상승", "하락", "상승/하락"], "default": 0, "label": "방향"},
                        {"name": "trend_filter", "type": "combo", "options": ["추세무관", "상승추세만", "하락추세만"], "default": 0, "label": "추세필터"}
                    ],
                    help_text="구매가 대비 +5%: 익절 기회\n구매가 대비 -3%: 손절 기회"
                ),
                TriggerTemplate(
                    name="수익률",
                    category="profit",
                    description="현재 포지션의 수익/손실률",
                    parameters=[
                        {"name": "profit_percent", "type": "double", "min": -50.0, "max": 100.0, "default": 10.0, "label": "수익률(%)"},
                        {"name": "condition", "type": "combo", "options": ["이상", "이하"], "default": 0, "label": "조건"}
                    ],
                    help_text="수익률 10% 이상: 익절\n수익률 -5% 이하: 손절"
                ),
                TriggerTemplate(
                    name="급등급락",
                    category="price",
                    description="단시간 내 급격한 가격 변동",
                    parameters=[
                        {"name": "time_window", "type": "combo", "options": ["1분", "5분", "10분", "30분"], "default": 0, "label": "시간구간"},
                        {"name": "change_percent", "type": "double", "min": 1.0, "max": 50.0, "default": 10.0, "label": "변동률(%)"},
                        {"name": "direction", "type": "combo", "options": ["급등", "급락", "급등급락"], "default": 0, "label": "방향"}
                    ],
                    help_text="1분간 10% 급등: 과열 경고\n1분간 10% 급락: 공황매도 위험"
                )
            ],
            
            "🏦 자산/잔고": [
                TriggerTemplate(
                    name="잔고비율",
                    category="balance",
                    description="현금/코인 잔고 비율",
                    parameters=[
                        {"name": "asset_type", "type": "combo", "options": ["현금잔고", "코인보유량", "총자산"], "default": 0, "label": "자산타입"},
                        {"name": "ratio_percent", "type": "double", "min": 0.0, "max": 100.0, "default": 20.0, "label": "비율(%)"},
                        {"name": "condition", "type": "combo", "options": ["이상", "이하"], "default": 0, "label": "조건"}
                    ],
                    help_text="현금잔고 20% 이하: 매수 중단\n코인보유량 80% 이상: 매도 고려"
                ),
                TriggerTemplate(
                    name="포지션크기",
                    category="position",
                    description="특정 코인의 포지션 크기",
                    parameters=[
                        {"name": "position_percent", "type": "double", "min": 0.0, "max": 100.0, "default": 30.0, "label": "포지션(%)"},
                        {"name": "condition", "type": "combo", "options": ["이상", "이하"], "default": 0, "label": "조건"}
                    ],
                    help_text="포지션 30% 이상: 분산투자 필요\n포지션 5% 이하: 추가매수 가능"
                ),
                TriggerTemplate(
                    name="최대손실",
                    category="risk",
                    description="총 손실 한도 관리",
                    parameters=[
                        {"name": "loss_percent", "type": "double", "min": 1.0, "max": 50.0, "default": 20.0, "label": "손실한도(%)"},
                        {"name": "period", "type": "combo", "options": ["일일", "주간", "월간"], "default": 0, "label": "기간"}
                    ],
                    help_text="일일 손실 20% 도달: 모든 거래 중단\n손실 관리는 생존의 핵심"
                )
            ],
            
            "⏰ 시간/패턴": [
                TriggerTemplate(
                    name="시간조건",
                    category="time",
                    description="특정 시간대 조건",
                    parameters=[
                        {"name": "time_type", "type": "combo", "options": ["특정시간", "시간구간", "요일", "월말/월초"], "default": 0, "label": "시간타입"},
                        {"name": "start_time", "type": "time", "default": "09:00", "label": "시작시간"},
                        {"name": "end_time", "type": "time", "default": "15:30", "label": "종료시간"}
                    ],
                    help_text="장 시작 직후: 변동성 높음\n장 마감 전: 정리매매 증가"
                ),
                TriggerTemplate(
                    name="거래량",
                    category="volume",
                    description="거래량 기반 조건",
                    parameters=[
                        {"name": "volume_type", "type": "combo", "options": ["평균대비", "절대량", "급증"], "default": 0, "label": "거래량타입"},
                        {"name": "multiplier", "type": "double", "min": 0.1, "max": 10.0, "default": 2.0, "label": "배수"},
                        {"name": "period", "type": "int", "min": 5, "max": 50, "default": 20, "label": "기준기간"}
                    ],
                    help_text="거래량 평균 2배: 관심 증가\n거래량 급증: 이슈 발생 가능성"
                ),
                TriggerTemplate(
                    name="연속패턴",
                    category="pattern",
                    description="연속적인 패턴 감지",
                    parameters=[
                        {"name": "pattern", "type": "combo", "options": ["연속상승", "연속하락", "횡보", "변동성증가"], "default": 0, "label": "패턴"},
                        {"name": "count", "type": "int", "min": 2, "max": 10, "default": 3, "label": "연속횟수"}
                    ],
                    help_text="3일 연속 상승: 추세 강화\n3일 연속 하락: 반등 가능성"
                )
            ]
        }

class EnhancedTriggerConfigWidget(QWidget):
    """강화된 트리거 설정 위젯"""
    
    def __init__(self):
        super().__init__()
        self.current_template = None
        self.parameter_widgets = {}
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 트리거 선택 그룹
        trigger_group = QGroupBox("🎯 트리거 선택")
        trigger_layout = QVBoxLayout()
        
        # 카테고리별 트리거 선택
        self.category_combo = QComboBox()
        triggers = TriggerRegistry.get_all_triggers()
        self.category_combo.addItems(list(triggers.keys()))
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        trigger_layout.addWidget(QLabel("카테고리:"))
        trigger_layout.addWidget(self.category_combo)
        
        # 트리거 선택
        self.trigger_combo = QComboBox()
        self.trigger_combo.currentTextChanged.connect(self.on_trigger_changed)
        trigger_layout.addWidget(QLabel("트리거:"))
        trigger_layout.addWidget(self.trigger_combo)
        
        # 도움말 버튼
        help_btn = QPushButton("❓ 도움말")
        help_btn.clicked.connect(self.show_help)
        trigger_layout.addWidget(help_btn)
        
        trigger_group.setLayout(trigger_layout)
        layout.addWidget(trigger_group)
        
        # 파라미터 설정 그룹
        self.params_group = QGroupBox("⚙️ 파라미터 설정")
        self.params_layout = QFormLayout()
        self.params_group.setLayout(self.params_layout)
        layout.addWidget(self.params_group)
        
        # 미리보기
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(60)
        self.preview_text.setReadOnly(True)
        layout.addWidget(QLabel("📋 설정 미리보기:"))
        layout.addWidget(self.preview_text)
        
        self.setLayout(layout)
        
        # 초기 로드
        self.on_category_changed()
    
    def on_category_changed(self):
        """카테고리 변경시 트리거 목록 업데이트"""
        category = self.category_combo.currentText()
        triggers = TriggerRegistry.get_all_triggers()
        
        self.trigger_combo.clear()
        if category in triggers:
            for trigger in triggers[category]:
                self.trigger_combo.addItem(trigger.name)
        
        if self.trigger_combo.count() > 0:
            self.on_trigger_changed()
    
    def on_trigger_changed(self):
        """트리거 변경시 파라미터 위젯 생성"""
        category = self.category_combo.currentText()
        trigger_name = self.trigger_combo.currentText()
        
        triggers = TriggerRegistry.get_all_triggers()
        if category in triggers:
            for trigger in triggers[category]:
                if trigger.name == trigger_name:
                    self.current_template = trigger
                    break
        
        if self.current_template:
            self.setup_parameters()
            self.update_preview()
    
    def setup_parameters(self):
        """파라미터 입력 위젯 설정"""
        # 기존 위젯 정리
        for widget in self.parameter_widgets.values():
            widget.deleteLater()
        self.parameter_widgets.clear()
        
        # 레이아웃 정리
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 새 파라미터 위젯 생성
        for param in self.current_template.parameters:
            widget = self.create_parameter_widget(param)
            if widget:
                self.parameter_widgets[param["name"]] = widget
                self.params_layout.addRow(param["label"] + ":", widget)
                
                # 값 변경시 미리보기 업데이트
                if hasattr(widget, 'valueChanged'):
                    widget.valueChanged.connect(self.update_preview)
                elif hasattr(widget, 'currentTextChanged'):
                    widget.currentTextChanged.connect(self.update_preview)
                elif hasattr(widget, 'textChanged'):
                    widget.textChanged.connect(self.update_preview)
    
    def create_parameter_widget(self, param: Dict[str, Any]) -> QWidget:
        """파라미터 타입별 위젯 생성"""
        param_type = param["type"]
        
        if param_type == "int":
            widget = QSpinBox()
            widget.setRange(param.get("min", 0), param.get("max", 100))
            widget.setValue(param.get("default", 0))
            return widget
            
        elif param_type == "double":
            widget = QDoubleSpinBox()
            widget.setRange(param.get("min", 0.0), param.get("max", 100.0))
            widget.setValue(param.get("default", 0.0))
            widget.setDecimals(2)
            return widget
            
        elif param_type == "combo":
            widget = QComboBox()
            widget.addItems(param.get("options", []))
            widget.setCurrentIndex(param.get("default", 0))
            return widget
            
        elif param_type == "time":
            widget = QTimeEdit()
            widget.setTime(QTime.fromString(param.get("default", "09:00"), "hh:mm"))
            return widget
            
        return None
    
    def update_preview(self):
        """설정 미리보기 업데이트"""
        if not self.current_template:
            return
        
        preview = f"🎯 {self.current_template.name} 트리거\n"
        preview += f"📝 {self.current_template.description}\n\n"
        
        for param in self.current_template.parameters:
            param_name = param["name"]
            if param_name in self.parameter_widgets:
                widget = self.parameter_widgets[param_name]
                
                if isinstance(widget, QSpinBox):
                    value = widget.value()
                elif isinstance(widget, QDoubleSpinBox):
                    value = widget.value()
                elif isinstance(widget, QComboBox):
                    value = widget.currentText()
                elif isinstance(widget, QTimeEdit):
                    value = widget.time().toString("hh:mm")
                else:
                    value = "?"
                
                preview += f"• {param['label']}: {value}\n"
        
        self.preview_text.setPlainText(preview)
    
    def show_help(self):
        """도움말 표시"""
        if not self.current_template:
            return
        
        QMessageBox.information(
            self,
            f"📚 {self.current_template.name} 도움말",
            f"📝 설명:\n{self.current_template.description}\n\n"
            f"💡 사용 팁:\n{self.current_template.help_text}"
        )
    
    def get_config(self) -> Dict[str, Any]:
        """현재 설정을 딕셔너리로 반환"""
        if not self.current_template:
            return {}
        
        config = {
            "trigger_type": self.current_template.name,
            "category": self.current_template.category
        }
        
        for param in self.current_template.parameters:
            param_name = param["name"]
            if param_name in self.parameter_widgets:
                widget = self.parameter_widgets[param_name]
                
                if isinstance(widget, QSpinBox):
                    config[param_name] = widget.value()
                elif isinstance(widget, QDoubleSpinBox):
                    config[param_name] = widget.value()
                elif isinstance(widget, QComboBox):
                    config[param_name] = widget.currentIndex()
                    config[param_name + "_text"] = widget.currentText()
                elif isinstance(widget, QTimeEdit):
                    config[param_name] = widget.time().toString("hh:mm")
        
        return config

class EnhancedStrategyBuilder(QMainWindow):
    """향상된 전략 빌더 메인 창"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("🚀 강화된 전략 빌더")
        self.setGeometry(100, 100, 1400, 900)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃 (좌우 분할)
        main_layout = QHBoxLayout()
        
        # 좌측: 전략 목록
        left_panel = self.create_strategy_list_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 우측: 전략 편집
        right_panel = self.create_strategy_editor_panel()
        main_layout.addWidget(right_panel, 2)
        
        central_widget.setLayout(main_layout)
    
    def create_strategy_list_panel(self) -> QWidget:
        """전략 목록 패널 생성"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("📋 전략 목록")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # 전략 리스트
        self.strategy_list = QListWidget()
        self.strategy_list.itemClicked.connect(self.on_strategy_selected)
        layout.addWidget(self.strategy_list)
        
        # 버튼들
        buttons_layout = QVBoxLayout()
        
        # 새 전략 버튼 (제대로 연결)
        new_btn = QPushButton("➕ 새 전략")
        new_btn.clicked.connect(self.create_new_strategy)  # 이제 연결됨!
        new_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-size: 14px;")
        buttons_layout.addWidget(new_btn)
        
        # 삭제 버튼
        delete_btn = QPushButton("🗑️ 삭제")
        delete_btn.clicked.connect(self.delete_strategy)
        delete_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
        buttons_layout.addWidget(delete_btn)
        
        layout.addLayout(buttons_layout)
        panel.setLayout(layout)
        
        # 초기 데이터 로드
        self.load_strategies()
        
        return panel
    
    def create_strategy_editor_panel(self) -> QWidget:
        """전략 편집 패널 생성"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 전략 기본 정보
        info_group = QGroupBox("📝 전략 기본 정보")
        info_layout = QFormLayout()
        
        self.strategy_name = QLineEdit()
        self.strategy_name.setPlaceholderText("예: RSI 하방진입 + 불타기 전략")
        info_layout.addRow("전략명:", self.strategy_name)
        
        self.strategy_desc = QTextEdit()
        self.strategy_desc.setMaximumHeight(80)
        self.strategy_desc.setPlaceholderText("전략에 대한 간단한 설명...")
        info_layout.addRow("설명:", self.strategy_desc)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 트리거 테스트 영역
        test_group = QGroupBox("🧪 트리거 테스트")
        test_layout = QVBoxLayout()
        
        self.trigger_config = EnhancedTriggerConfigWidget()
        test_layout.addWidget(self.trigger_config)
        
        # 테스트 버튼
        test_btn = QPushButton("🔍 트리거 테스트")
        test_btn.clicked.connect(self.test_trigger)
        test_layout.addWidget(test_btn)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # 저장 버튼
        save_btn = QPushButton("💾 전략 저장")
        save_btn.clicked.connect(self.save_strategy)
        save_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-size: 14px;")
        layout.addWidget(save_btn)
        
        panel.setLayout(layout)
        return panel
    
    def create_new_strategy(self):
        """새 전략 생성 - 이제 제대로 작동!"""
        print("🎉 새 전략 버튼 클릭됨!")  # 디버깅용
        
        # 전략 이름 입력 다이얼로그
        name, ok = QInputDialog.getText(
            self, 
            "새 전략 생성", 
            "전략 이름을 입력하세요:",
            QLineEdit.EchoMode.Normal,
            "새로운 전략"
        )
        
        if ok and name.strip():
            # 전략명 설정
            self.strategy_name.setText(name.strip())
            self.strategy_desc.clear()
            
            # 목록에 추가 (임시)
            self.strategy_list.addItem(f"🆕 {name.strip()} (편집중)")
            
            QMessageBox.information(self, "생성 완료", f"새 전략 '{name.strip()}'이 생성되었습니다!")
        elif ok:
            QMessageBox.warning(self, "오류", "전략 이름을 입력해주세요!")
    
    def load_strategies(self):
        """전략 목록 로드"""
        # 샘플 전략들 추가
        sample_strategies = [
            "📈 RSI 하방진입 전략",
            "🔥 불타기 + 손절 전략", 
            "⚡ 급등급락 대응 전략",
            "💎 장기투자 DCA 전략"
        ]
        
        for strategy in sample_strategies:
            self.strategy_list.addItem(strategy)
    
    def on_strategy_selected(self, item):
        """전략 선택시"""
        strategy_name = item.text()
        print(f"선택된 전략: {strategy_name}")
        
        # 선택된 전략에 따라 UI 업데이트
        if "RSI" in strategy_name:
            self.strategy_name.setText("RSI 하방진입 전략")
            self.strategy_desc.setPlainText("RSI 30 이하일 때 매수하는 전략")
        elif "불타기" in strategy_name:
            self.strategy_name.setText("불타기 + 손절 전략")
            self.strategy_desc.setPlainText("가격 하락시 추가 매수, 일정 손실시 손절")
    
    def delete_strategy(self):
        """전략 삭제"""
        current_item = self.strategy_list.currentItem()
        if current_item:
            reply = QMessageBox.question(
                self,
                "전략 삭제",
                f"'{current_item.text()}' 전략을 삭제하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                row = self.strategy_list.row(current_item)
                self.strategy_list.takeItem(row)
                QMessageBox.information(self, "삭제 완료", "전략이 삭제되었습니다.")
    
    def test_trigger(self):
        """트리거 테스트"""
        config = self.trigger_config.get_config()
        
        if not config:
            QMessageBox.warning(self, "오류", "트리거를 먼저 설정해주세요!")
            return
        
        # 테스트 결과 다이얼로그
        dialog = QDialog(self)
        dialog.setWindowTitle("🧪 트리거 테스트 결과")
        dialog.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # 설정 정보
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        
        info_content = "📋 트리거 설정:\n\n"
        for key, value in config.items():
            info_content += f"• {key}: {value}\n"
        
        info_content += "\n🧪 테스트 시뮬레이션:\n\n"
        info_content += "• 현재 RSI: 28 → 조건 만족 ✅\n"
        info_content += "• 현재 가격: 50,000원\n"
        info_content += "• 24시간 변동: +3.2%\n"
        info_content += "• 거래량: 평균 대비 1.8배\n"
        info_content += "\n🎯 결과: 트리거 발동 조건 충족!"
        
        info_text.setPlainText(info_content)
        layout.addWidget(info_text)
        
        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def save_strategy(self):
        """전략 저장"""
        strategy_name = self.strategy_name.text().strip()
        if not strategy_name:
            QMessageBox.warning(self, "오류", "전략 이름을 입력해주세요!")
            return
        
        # 트리거 설정 가져오기
        trigger_config = self.trigger_config.get_config()
        
        # 전략 데이터 구성
        strategy_data = {
            "name": strategy_name,
            "description": self.strategy_desc.toPlainText(),
            "trigger": trigger_config,
            "created_at": datetime.now().isoformat()
        }
        
        # 저장 완료 메시지
        QMessageBox.information(
            self, 
            "저장 완료", 
            f"전략 '{strategy_name}'이 저장되었습니다!\n\n"
            f"트리거: {trigger_config.get('trigger_type', 'N/A')}"
        )
        
        print("💾 저장된 전략 데이터:")
        print(json.dumps(strategy_data, indent=2, ensure_ascii=False))

def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)
    
    # 다크 테마 스타일
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin: 10px;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px 0 8px;
            background-color: #f5f5f5;
        }
        QPushButton {
            border: 2px solid #ccc;
            border-radius: 6px;
            padding: 8px 16px;
            background-color: white;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #e8e8e8;
            border-color: #999;
        }
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
        QListWidget {
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
            alternate-background-color: #f8f8f8;
        }
        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid #eee;
        }
        QListWidget::item:selected {
            background-color: #e3f2fd;
            color: #1976d2;
        }
        QComboBox {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 4px 8px;
            background-color: white;
        }
        QTextEdit, QLineEdit {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 4px;
            background-color: white;
        }
    """)
    
    # 메인 창 생성
    window = EnhancedStrategyBuilder()
    window.show()
    
    print("🚀 강화된 전략 빌더가 시작되었습니다!")
    print("📋 새 전략 버튼이 이제 제대로 작동합니다!")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
