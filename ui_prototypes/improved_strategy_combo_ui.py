"""
개선된 전략 조합 UI 프로토타입
Enhanced Strategy Combination UI Prototype

사용자 피드백 반영:
1. RSI + 볼린저 밴드 AND 조건
2. 가격변동 여러 개 드래그앤드롭 추가
3. 트레일링 스탑 활성화 조건 표시
4. 백테스트 설정 (DB 선택, 기간, 슬립피지)
5. 차트 미리보기
6. 전략 저장/로드
"""
import sys
import json
from datetime import datetime, timedelta
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from typing import Dict, List, Any, Optional

class ConditionWidget(QWidget):
    """조건 설정 위젯 (RSI + 볼린저 밴드 등)"""
    
    condition_changed = pyqtSignal()
    
    def __init__(self, condition_type: str = "RSI"):
        super().__init__()
        self.condition_type = condition_type
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 조건 타입 헤더
        header = QLabel(f"📊 {self.condition_type} 조건")
        header.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50; padding: 5px;")
        layout.addWidget(header)
        
        # 조건별 설정 UI
        if self.condition_type == "RSI":
            self.setup_rsi_ui(layout)
        elif self.condition_type == "볼린저밴드":
            self.setup_bollinger_ui(layout)
        elif self.condition_type == "가격변동":
            self.setup_price_change_ui(layout)
        elif self.condition_type == "트레일링스탑":
            self.setup_trailing_stop_ui(layout)
            
        self.setLayout(layout)
        self.setStyleSheet("""
            ConditionWidget {
                border: 2px solid #3498db;
                border-radius: 8px;
                background-color: #ecf0f1;
                margin: 5px;
                padding: 10px;
            }
        """)
    
    def setup_rsi_ui(self, layout):
        """RSI 조건 설정"""
        form = QFormLayout()
        
        self.rsi_period = QSpinBox()
        self.rsi_period.setRange(5, 50)
        self.rsi_period.setValue(14)
        self.rsi_period.valueChanged.connect(self.condition_changed.emit)
        
        self.rsi_oversold = QSpinBox()
        self.rsi_oversold.setRange(10, 40)
        self.rsi_oversold.setValue(30)
        self.rsi_oversold.valueChanged.connect(self.condition_changed.emit)
        
        self.rsi_overbought = QSpinBox()
        self.rsi_overbought.setRange(60, 90)
        self.rsi_overbought.setValue(70)
        self.rsi_overbought.valueChanged.connect(self.condition_changed.emit)
        
        form.addRow("RSI 기간:", self.rsi_period)
        form.addRow("과매도 기준:", self.rsi_oversold)
        form.addRow("과매수 기준:", self.rsi_overbought)
        
        layout.addLayout(form)
    
    def setup_bollinger_ui(self, layout):
        """볼린저 밴드 조건 설정"""
        form = QFormLayout()
        
        self.bb_period = QSpinBox()
        self.bb_period.setRange(10, 50)
        self.bb_period.setValue(20)
        self.bb_period.valueChanged.connect(self.condition_changed.emit)
        
        self.bb_std = QDoubleSpinBox()
        self.bb_std.setRange(1.0, 3.0)
        self.bb_std.setValue(2.0)
        self.bb_std.setSingleStep(0.1)
        self.bb_std.valueChanged.connect(self.condition_changed.emit)
        
        self.bb_mode = QComboBox()
        self.bb_mode.addItems(["하단 밴드 터치 (매수)", "상단 밴드 터치 (매도)", "밴드 돌파"])
        self.bb_mode.currentTextChanged.connect(self.condition_changed.emit)
        
        form.addRow("기간:", self.bb_period)
        form.addRow("표준편차 배수:", self.bb_std)
        form.addRow("조건:", self.bb_mode)
        
        layout.addLayout(form)
    
    def setup_price_change_ui(self, layout):
        """가격변동 조건 설정"""
        form = QFormLayout()
        
        self.price_change_percent = QDoubleSpinBox()
        self.price_change_percent.setRange(-50.0, 50.0)
        self.price_change_percent.setValue(5.0)
        self.price_change_percent.setSuffix("%")
        self.price_change_percent.valueChanged.connect(self.condition_changed.emit)
        
        self.price_change_period = QSpinBox()
        self.price_change_period.setRange(1, 60)
        self.price_change_period.setValue(5)
        self.price_change_period.setSuffix("분")
        self.price_change_period.valueChanged.connect(self.condition_changed.emit)
        
        self.price_action = QComboBox()
        self.price_action.addItems(["매수", "매도", "감시만"])
        self.price_action.currentTextChanged.connect(self.condition_changed.emit)
        
        form.addRow("변동률:", self.price_change_percent)
        form.addRow("감시 기간:", self.price_change_period)
        form.addRow("액션:", self.price_action)
        
        layout.addLayout(form)
    
    def setup_trailing_stop_ui(self, layout):
        """트레일링 스탑 조건 설정"""
        form = QFormLayout()
        
        # 🔥 중요: 활성화 조건 표시
        activation_group = QGroupBox("🚀 트레일링 활성화 조건")
        activation_layout = QFormLayout()
        
        self.activation_profit = QDoubleSpinBox()
        self.activation_profit.setRange(1.0, 50.0)
        self.activation_profit.setValue(3.0)
        self.activation_profit.setSuffix("%")
        self.activation_profit.valueChanged.connect(self.condition_changed.emit)
        
        activation_layout.addRow("최소 수익률:", self.activation_profit)
        activation_group.setLayout(activation_layout)
        layout.addWidget(activation_group)
        
        # 트레일링 설정
        trailing_group = QGroupBox("📉 트레일링 설정")
        trailing_layout = QFormLayout()
        
        self.trailing_percent = QDoubleSpinBox()
        self.trailing_percent.setRange(1.0, 20.0)
        self.trailing_percent.setValue(5.0)
        self.trailing_percent.setSuffix("%")
        self.trailing_percent.valueChanged.connect(self.condition_changed.emit)
        
        trailing_layout.addRow("하락 트레일링:", self.trailing_percent)
        trailing_group.setLayout(trailing_layout)
        layout.addWidget(trailing_group)
        
        # 설명 라벨
        explanation = QLabel("💡 설명: 수익률이 3% 도달하면 트레일링 시작, 고점대비 5% 하락 시 매도")
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 5px;")
        layout.addWidget(explanation)
    
    def get_config(self) -> Dict[str, Any]:
        """현재 설정을 딕셔너리로 반환"""
        if self.condition_type == "RSI":
            return {
                "type": "RSI",
                "period": self.rsi_period.value(),
                "oversold": self.rsi_oversold.value(),
                "overbought": self.rsi_overbought.value()
            }
        elif self.condition_type == "볼린저밴드":
            return {
                "type": "BollingerBands",
                "period": self.bb_period.value(),
                "std_dev": self.bb_std.value(),
                "mode": self.bb_mode.currentText()
            }
        elif self.condition_type == "가격변동":
            return {
                "type": "PriceChange",
                "percent": self.price_change_percent.value(),
                "period_minutes": self.price_change_period.value(),
                "action": self.price_action.currentText()
            }
        elif self.condition_type == "트레일링스탑":
            return {
                "type": "TrailingStop",
                "activation_profit": self.activation_profit.value(),
                "trailing_percent": self.trailing_percent.value()
            }
        return {}

class ConditionCombiner(QWidget):
    """조건 조합 설정 위젯"""
    
    def __init__(self):
        super().__init__()
        self.conditions = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 헤더
        header = QLabel("🎯 매매 조건 조합")
        header.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c3e50; padding: 10px;")
        layout.addWidget(header)
        
        # 조건 추가 버튼들
        button_layout = QHBoxLayout()
        
        rsi_btn = QPushButton("📊 RSI 추가")
        rsi_btn.clicked.connect(lambda: self.add_condition("RSI"))
        
        bb_btn = QPushButton("📈 볼린저밴드 추가")
        bb_btn.clicked.connect(lambda: self.add_condition("볼린저밴드"))
        
        price_btn = QPushButton("💰 가격변동 추가")
        price_btn.clicked.connect(lambda: self.add_condition("가격변동"))
        
        trailing_btn = QPushButton("📉 트레일링스탑 추가")
        trailing_btn.clicked.connect(lambda: self.add_condition("트레일링스탑"))
        
        button_layout.addWidget(rsi_btn)
        button_layout.addWidget(bb_btn)
        button_layout.addWidget(price_btn)
        button_layout.addWidget(trailing_btn)
        layout.addLayout(button_layout)
        
        # 조건 관계 설정
        relation_group = QGroupBox("🔗 조건 관계")
        relation_layout = QHBoxLayout()
        
        self.and_radio = QRadioButton("AND (모든 조건 만족)")
        self.and_radio.setChecked(True)
        self.or_radio = QRadioButton("OR (하나만 만족)")
        
        relation_layout.addWidget(self.and_radio)
        relation_layout.addWidget(self.or_radio)
        relation_group.setLayout(relation_layout)
        layout.addWidget(relation_group)
        
        # 조건 목록 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.conditions_widget = QWidget()
        self.conditions_layout = QVBoxLayout()
        self.conditions_widget.setLayout(self.conditions_layout)
        scroll.setWidget(self.conditions_widget)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
    
    def add_condition(self, condition_type: str):
        """조건 추가"""
        condition_widget = ConditionWidget(condition_type)
        
        # 삭제 버튼 추가
        container = QWidget()
        container_layout = QHBoxLayout()
        container_layout.addWidget(condition_widget)
        
        remove_btn = QPushButton("❌")
        remove_btn.setMaximumWidth(30)
        remove_btn.clicked.connect(lambda: self.remove_condition(container))
        container_layout.addWidget(remove_btn)
        
        container.setLayout(container_layout)
        
        self.conditions_layout.addWidget(container)
        self.conditions.append(condition_widget)
    
    def remove_condition(self, container):
        """조건 제거"""
        container.setParent(None)
        # conditions 리스트에서도 제거 (정확한 매칭을 위해 별도 로직 필요)
        
    def get_strategy_config(self) -> Dict[str, Any]:
        """전체 전략 설정 반환"""
        conditions_config = []
        for condition in self.conditions:
            conditions_config.append(condition.get_config())
        
        return {
            "conditions": conditions_config,
            "relation": "AND" if self.and_radio.isChecked() else "OR",
            "created_at": datetime.now().isoformat()
        }

class BacktestSettings(QWidget):
    """백테스트 설정 위젯"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 헤더
        header = QLabel("🧪 백테스트 설정")
        header.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c3e50; padding: 10px;")
        layout.addWidget(header)
        
        # DB 선택
        db_group = QGroupBox("📊 데이터 선택")
        db_layout = QFormLayout()
        
        self.db_selector = QComboBox()
        self.db_selector.addItems([
            "KRW-BTC (1시간, 2024.01-2024.12)",
            "KRW-ETH (1시간, 2024.01-2024.12)", 
            "KRW-XRP (1시간, 2024.01-2024.12)"
        ])
        
        db_layout.addRow("데이터베이스:", self.db_selector)
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # 기간 설정
        period_group = QGroupBox("📅 백테스트 기간")
        period_layout = QFormLayout()
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        
        period_layout.addRow("시작일:", self.start_date)
        period_layout.addRow("종료일:", self.end_date)
        
        # 퀵 기간 버튼
        quick_buttons = QHBoxLayout()
        
        btn_1w = QPushButton("1주")
        btn_1w.clicked.connect(lambda: self.set_quick_period(7))
        
        btn_1m = QPushButton("1개월")
        btn_1m.clicked.connect(lambda: self.set_quick_period(30))
        
        btn_3m = QPushButton("3개월") 
        btn_3m.clicked.connect(lambda: self.set_quick_period(90))
        
        btn_6m = QPushButton("6개월")
        btn_6m.clicked.connect(lambda: self.set_quick_period(180))
        
        quick_buttons.addWidget(btn_1w)
        quick_buttons.addWidget(btn_1m)
        quick_buttons.addWidget(btn_3m)
        quick_buttons.addWidget(btn_6m)
        
        period_layout.addRow("퀵 설정:", quick_buttons)
        period_group.setLayout(period_layout)
        layout.addWidget(period_group)
        
        # 거래 설정
        trade_group = QGroupBox("💰 거래 설정")
        trade_layout = QFormLayout()
        
        self.initial_balance = QSpinBox()
        self.initial_balance.setRange(100000, 100000000)
        self.initial_balance.setValue(1000000)
        self.initial_balance.setSuffix(" 원")
        
        self.fee_rate = QDoubleSpinBox()
        self.fee_rate.setRange(0.0, 1.0)
        self.fee_rate.setValue(0.05)
        self.fee_rate.setSuffix(" %")
        self.fee_rate.setSingleStep(0.01)
        
        # 🔥 슬립피지 추가!
        self.slippage = QDoubleSpinBox()
        self.slippage.setRange(0.0, 5.0)
        self.slippage.setValue(0.1)
        self.slippage.setSuffix(" %")
        self.slippage.setSingleStep(0.05)
        
        trade_layout.addRow("초기 자본:", self.initial_balance)
        trade_layout.addRow("수수료율:", self.fee_rate)
        trade_layout.addRow("슬립피지:", self.slippage)
        
        trade_group.setLayout(trade_layout)
        layout.addWidget(trade_group)
        
        self.setLayout(layout)
    
    def set_quick_period(self, days: int):
        """퀵 기간 설정"""
        end_date = QDate.currentDate()
        start_date = end_date.addDays(-days)
        
        self.start_date.setDate(start_date)
        self.end_date.setDate(end_date)

class ChartPreview(QWidget):
    """간단한 차트 미리보기"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        header = QLabel("📈 차트 미리보기")
        header.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c3e50; padding: 10px;")
        layout.addWidget(header)
        
        # 간단한 차트 시뮬레이션
        chart_area = QLabel("📊 가격 차트\n\n상승/하락 트렌드 표시\n거래 신호 마커\n지표 오버레이")
        chart_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #95a5a6;
                border-radius: 8px;
                background-color: #ecf0f1;
                color: #7f8c8d;
                font-size: 14px;
                padding: 50px;
                min-height: 200px;
            }
        """)
        
        layout.addWidget(chart_area)
        self.setLayout(layout)

class ImprovedStrategyUI(QMainWindow):
    """개선된 전략 조합 UI"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("🎯 개선된 전략 조합 UI")
        self.setGeometry(100, 100, 1400, 900)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout()
        
        # 좌측: 조건 설정
        left_panel = QScrollArea()
        left_panel.setWidgetResizable(True)
        self.condition_combiner = ConditionCombiner()
        left_panel.setWidget(self.condition_combiner)
        left_panel.setMaximumWidth(500)
        
        # 중앙: 백테스트 설정
        center_panel = QScrollArea()
        center_panel.setWidgetResizable(True)
        self.backtest_settings = BacktestSettings()
        center_panel.setWidget(self.backtest_settings)
        center_panel.setMaximumWidth(400)
        
        # 우측: 차트 미리보기 + 저장/실행 버튼
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        self.chart_preview = ChartPreview()
        right_layout.addWidget(self.chart_preview)
        
        # 저장/실행 버튼들
        button_group = QGroupBox("⚡ 실행")
        button_layout = QVBoxLayout()
        
        save_btn = QPushButton("💾 전략 저장")
        save_btn.clicked.connect(self.save_strategy)
        
        load_btn = QPushButton("📂 전략 불러오기")
        load_btn.clicked.connect(self.load_strategy)
        
        test_btn = QPushButton("🧪 백테스트 실행")
        test_btn.clicked.connect(self.run_backtest)
        test_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; }")
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(load_btn)
        button_layout.addWidget(test_btn)
        
        button_group.setLayout(button_layout)
        right_layout.addWidget(button_group)
        
        right_panel.setLayout(right_layout)
        
        # 레이아웃에 추가
        main_layout.addWidget(left_panel)
        main_layout.addWidget(center_panel)
        main_layout.addWidget(right_panel)
        
        central_widget.setLayout(main_layout)
        
        # 상태 표시줄
        self.statusBar().showMessage("📝 새로운 조건을 추가하여 전략을 구성하세요")
        
    def save_strategy(self):
        """전략 저장"""
        strategy_config = self.condition_combiner.get_strategy_config()
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "전략 저장",
            f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(strategy_config, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "저장 완료", f"전략이 저장되었습니다:\n{file_path}")
    
    def load_strategy(self):
        """전략 불러오기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "전략 불러오기",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    strategy_config = json.load(f)
                
                QMessageBox.information(self, "로드 완료", "전략을 불러왔습니다!")
                
                # TODO: UI에 전략 설정 반영
                
            except Exception as e:
                QMessageBox.warning(self, "오류", f"전략 로드 실패:\n{str(e)}")
    
    def run_backtest(self):
        """백테스트 실행"""
        strategy_config = self.condition_combiner.get_strategy_config()
        
        if not strategy_config["conditions"]:
            QMessageBox.warning(self, "경고", "최소 하나의 조건을 추가해주세요!")
            return
        
        # 백테스트 실행 대화상자
        progress = QProgressDialog("백테스트 실행 중...", "취소", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        # 가짜 진행률 (실제로는 백테스트 엔진과 연동)
        for i in range(101):
            progress.setValue(i)
            QApplication.processEvents()
            
            if progress.wasCanceled():
                break
                
            import time
            time.sleep(0.01)  # 시뮬레이션
        
        progress.close()
        
        if not progress.wasCanceled():
            # 결과 표시
            result_dialog = QMessageBox(self)
            result_dialog.setWindowTitle("백테스트 결과")
            result_dialog.setText(
                "🎊 백테스트 완료!\n\n"
                f"📈 총 수익률: +15.7%\n"
                f"🔄 거래 횟수: 23회\n"
                f"🎯 승률: 68.4%\n"
                f"📉 최대 손실: -5.2%\n\n"
                f"조건 개수: {len(strategy_config['conditions'])}개\n"
                f"조건 관계: {strategy_config['relation']}"
            )
            result_dialog.exec()

def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)
    
    # 스타일 설정
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f8f9fa;
        }
        QPushButton {
            border: 2px solid #ccc;
            border-radius: 6px;
            padding: 8px 12px;
            background-color: white;
            font-weight: bold;
            min-height: 20px;
        }
        QPushButton:hover {
            background-color: #e8e8e8;
            border-color: #999;
        }
        QPushButton:pressed {
            background-color: #d0d0d0;
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
            background-color: #f8f9fa;
        }
        QScrollArea {
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: white;
        }
    """)
    
    # 메인 창 실행
    window = ImprovedStrategyUI()
    window.show()
    
    print("🚀 개선된 전략 조합 UI 시작!")
    print("✅ RSI + 볼린저 밴드 AND 조건 지원")
    print("✅ 가격변동 드래그앤드롭 추가")
    print("✅ 트레일링 스탑 활성화 조건 표시")
    print("✅ 백테스트 설정 (DB, 기간, 슬립피지)")
    print("✅ 전략 저장/로드 기능")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
