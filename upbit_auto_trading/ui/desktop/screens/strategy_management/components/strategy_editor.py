"""
전략 에디터 위젯
- 시각적 전략 편집 도구
- 전략 유형별 파라미터 설정
- 전략 저장/테스트 기능
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QComboBox, QSpinBox, QGroupBox, QLineEdit,
    QTextEdit, QDoubleSpinBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
import uuid
from datetime import datetime
import sys
import os

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

from upbit_auto_trading.business_logic.strategy.trading_strategies import (
    StrategyManager, StrategyConfig, initialize_default_strategies
)

class StrategyEditorWidget(QWidget):
    # 시그널 정의
    strategy_updated = pyqtSignal(str)  # 전략 ID
    strategy_saved = pyqtSignal(str)  # 전략 저장 완료
    strategy_test_requested = pyqtSignal(str)  # 백테스트 요청

    def __init__(self, parent=None):
        super().__init__(parent)
        self.strategy_manager = StrategyManager()
        self.current_strategy_id = None
        self.init_ui()
        self._load_default_strategies()
    
    def _load_default_strategies(self):
        """기본 전략이 없으면 초기화"""
        strategies = self.strategy_manager.get_all_strategies()
        if not strategies:
            initialize_default_strategies()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. 상단: 전략 기본 정보
        info_group = QGroupBox("📋 전략 기본 정보")
        info_layout = QVBoxLayout(info_group)
        
        # 전략 이름
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("전략 이름:"))
        self.strategy_name = QLineEdit()
        self.strategy_name.setPlaceholderText("예: 나만의 골든크로스 전략")
        name_row.addWidget(self.strategy_name)
        info_layout.addLayout(name_row)
        
        # 전략 유형 선택
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("전략 유형:"))
        self.strategy_type = QComboBox()
        self.strategy_type.addItems(["이동평균 교차", "RSI", "볼린저 밴드", "변동성 돌파"])
        self.strategy_type.currentTextChanged.connect(self.on_strategy_type_changed)
        type_row.addWidget(self.strategy_type)
        info_layout.addLayout(type_row)
        
        # 전략 설명
        desc_row = QVBoxLayout()
        desc_row.addWidget(QLabel("전략 설명:"))
        self.strategy_description = QTextEdit()
        self.strategy_description.setMaximumHeight(60)
        self.strategy_description.setPlaceholderText("전략에 대한 간단한 설명을 입력하세요...")
        desc_row.addWidget(self.strategy_description)
        info_layout.addLayout(desc_row)
        
        layout.addWidget(info_group)
        
        # 2. 중앙: 파라미터 설정 (동적으로 변경)
        self.params_group = QGroupBox("⚙️ 파라미터 설정")
        self.params_layout = QVBoxLayout(self.params_group)
        layout.addWidget(self.params_group)
        
        # 초기 파라미터 UI 생성
        self.create_parameter_ui()
        
        # 3. 하단: 액션 버튼
        btn_row = QHBoxLayout()
        
        self.new_btn = QPushButton("🆕 새 전략")
        self.new_btn.clicked.connect(self.new_strategy)
        
        self.save_btn = QPushButton("💾 전략 저장")
        self.save_btn.clicked.connect(self.save_strategy)
        
        self.test_btn = QPushButton("🧪 백테스트 실행")
        self.test_btn.clicked.connect(self.run_backtest_strategy)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        btn_row.addWidget(self.new_btn)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.test_btn)
        layout.addLayout(btn_row)
    
    def on_strategy_type_changed(self):
        """전략 유형 변경시 파라미터 UI 재생성"""
        self.create_parameter_ui()
    
    def create_parameter_ui(self):
        """선택된 전략 유형에 따른 파라미터 UI 생성"""
        # 기존 파라미터 UI 제거
        for i in reversed(range(self.params_layout.count())):
            item = self.params_layout.itemAt(i)
            if item:
                child = item.widget()
                if child:
                    child.setParent(None)
        
        strategy_type = self.strategy_type.currentText()
        
        if strategy_type == "이동평균 교차":
            self.create_ma_cross_ui()
        elif strategy_type == "RSI":
            self.create_rsi_ui()
        elif strategy_type == "볼린저 밴드":
            self.create_bollinger_ui()
        elif strategy_type == "변동성 돌파":
            self.create_volatility_ui()
    
    def create_ma_cross_ui(self):
        """이동평균 교차 전략 파라미터 UI"""
        ma_row = QHBoxLayout()
        ma_row.addWidget(QLabel("단기 이평:"))
        self.short_ma = QSpinBox()
        self.short_ma.setRange(1, 200)
        self.short_ma.setValue(5)
        self.short_ma.setSuffix("일")
        ma_row.addWidget(self.short_ma)
        
        ma_row.addWidget(QLabel("장기 이평:"))
        self.long_ma = QSpinBox()
        self.long_ma.setRange(1, 200)
        self.long_ma.setValue(20)
        self.long_ma.setSuffix("일")
        ma_row.addWidget(self.long_ma)
        
        self.params_layout.addLayout(ma_row)
        
        # 설명 추가
        desc_label = QLabel("💡 단기 이평이 장기 이평을 상향 돌파하면 매수, 하향 돌파하면 매도")
        desc_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 10px;")
        self.params_layout.addWidget(desc_label)
    
    def create_rsi_ui(self):
        """RSI 전략 파라미터 UI"""
        rsi_row1 = QHBoxLayout()
        rsi_row1.addWidget(QLabel("RSI 기간:"))
        self.rsi_period = QSpinBox()
        self.rsi_period.setRange(1, 100)
        self.rsi_period.setValue(14)
        self.rsi_period.setSuffix("일")
        rsi_row1.addWidget(self.rsi_period)
        self.params_layout.addLayout(rsi_row1)
        
        rsi_row2 = QHBoxLayout()
        rsi_row2.addWidget(QLabel("과매도 기준:"))
        self.rsi_low = QSpinBox()
        self.rsi_low.setRange(0, 50)
        self.rsi_low.setValue(30)
        rsi_row2.addWidget(self.rsi_low)
        
        rsi_row2.addWidget(QLabel("과매수 기준:"))
        self.rsi_high = QSpinBox()
        self.rsi_high.setRange(50, 100)
        self.rsi_high.setValue(70)
        rsi_row2.addWidget(self.rsi_high)
        self.params_layout.addLayout(rsi_row2)
        
        desc_label = QLabel("💡 RSI가 과매도 기준 이하로 떨어지면 매수, 과매수 기준 이상 오르면 매도")
        desc_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 10px;")
        self.params_layout.addWidget(desc_label)
    
    def create_bollinger_ui(self):
        """볼린저 밴드 전략 파라미터 UI"""
        bb_row1 = QHBoxLayout()
        bb_row1.addWidget(QLabel("기간:"))
        self.bb_period = QSpinBox()
        self.bb_period.setRange(1, 100)
        self.bb_period.setValue(20)
        self.bb_period.setSuffix("일")
        bb_row1.addWidget(self.bb_period)
        
        bb_row1.addWidget(QLabel("표준편차 배수:"))
        self.bb_std = QDoubleSpinBox()
        self.bb_std.setRange(0.1, 5.0)
        self.bb_std.setValue(2.0)
        self.bb_std.setSingleStep(0.1)
        bb_row1.addWidget(self.bb_std)
        self.params_layout.addLayout(bb_row1)
        
        desc_label = QLabel("💡 가격이 하단 밴드에 접촉하면 매수, 상단 밴드에 접촉하면 매도")
        desc_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 10px;")
        self.params_layout.addWidget(desc_label)
    
    def create_volatility_ui(self):
        """변동성 돌파 전략 파라미터 UI"""
        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("돌파 기간:"))
        self.vol_period = QSpinBox()
        self.vol_period.setRange(1, 100)
        self.vol_period.setValue(20)
        self.vol_period.setSuffix("일")
        vol_row.addWidget(self.vol_period)
        
        vol_row.addWidget(QLabel("돌파 비율:"))
        self.vol_ratio = QDoubleSpinBox()
        self.vol_ratio.setRange(0.1, 2.0)
        self.vol_ratio.setValue(0.5)
        self.vol_ratio.setSingleStep(0.1)
        self.vol_ratio.setSuffix("%")
        vol_row.addWidget(self.vol_ratio)
        self.params_layout.addLayout(vol_row)
        
        desc_label = QLabel("💡 전일 고가 + (고가-저가) × 돌파비율을 상향 돌파하면 매수")
        desc_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 10px;")
        self.params_layout.addWidget(desc_label)
    
    def get_current_parameters(self) -> dict:
        """현재 UI에서 설정된 파라미터 추출"""
        strategy_type = self.strategy_type.currentText()
        
        if strategy_type == "이동평균 교차":
            return {
                'short_period': self.short_ma.value(),
                'long_period': self.long_ma.value()
            }
        elif strategy_type == "RSI":
            return {
                'period': self.rsi_period.value(),
                'oversold': self.rsi_low.value(),
                'overbought': self.rsi_high.value()
            }
        elif strategy_type == "볼린저 밴드":
            return {
                'period': self.bb_period.value(),
                'std_multiplier': self.bb_std.value()
            }
        elif strategy_type == "변동성 돌파":
            return {
                'period': self.vol_period.value(),
                'ratio': self.vol_ratio.value() / 100
            }
        
        return {}
    
    def new_strategy(self):
        """새 전략 생성"""
        self.current_strategy_id = None
        self.strategy_name.clear()
        self.strategy_description.clear()
        self.strategy_type.setCurrentIndex(0)
        self.create_parameter_ui()
    
    def load_strategy(self, strategy_id: str):
        """전략 불러오기"""
        config = self.strategy_manager.load_strategy(strategy_id)
        if config:
            self.current_strategy_id = strategy_id
            self.strategy_name.setText(config.name)
            self.strategy_type.setCurrentText(config.strategy_type)
            self.strategy_description.setText(config.description or "")
            
            # 파라미터 UI 재생성 후 값 설정
            self.create_parameter_ui()
            self.set_parameters(config.parameters)
    
    def set_parameters(self, parameters: dict):
        """파라미터 값을 UI에 설정"""
        strategy_type = self.strategy_type.currentText()
        
        if strategy_type == "이동평균 교차":
            if hasattr(self, 'short_ma'):
                self.short_ma.setValue(parameters.get('short_period', 5))
            if hasattr(self, 'long_ma'):
                self.long_ma.setValue(parameters.get('long_period', 20))
        elif strategy_type == "RSI":
            if hasattr(self, 'rsi_period'):
                self.rsi_period.setValue(parameters.get('period', 14))
            if hasattr(self, 'rsi_low'):
                self.rsi_low.setValue(parameters.get('oversold', 30))
            if hasattr(self, 'rsi_high'):
                self.rsi_high.setValue(parameters.get('overbought', 70))
        elif strategy_type == "볼린저 밴드":
            if hasattr(self, 'bb_period'):
                self.bb_period.setValue(parameters.get('period', 20))
            if hasattr(self, 'bb_std'):
                self.bb_std.setValue(parameters.get('std_multiplier', 2.0))
    
    def save_strategy(self):
        """전략 저장"""
        name = self.strategy_name.text().strip()
        if not name:
            QMessageBox.warning(self, "경고", "전략 이름을 입력해주세요.")
            return
        
        # 전략 ID 생성 (새 전략인 경우)
        if not self.current_strategy_id:
            self.current_strategy_id = str(uuid.uuid4())
        
        config = StrategyConfig(
            strategy_id=self.current_strategy_id,
            name=name,
            strategy_type=self.strategy_type.currentText(),
            parameters=self.get_current_parameters(),
            description=self.strategy_description.toPlainText(),
            created_at=datetime.now()
        )
        
        success = self.strategy_manager.save_strategy(config)
        if success:
            QMessageBox.information(self, "성공", f"전략 '{name}'이 저장되었습니다.")
            self.strategy_saved.emit(self.current_strategy_id)  # strategy_saved 시그널 발송
        else:
            QMessageBox.critical(self, "오류", "전략 저장에 실패했습니다.")
    
    def create_new_strategy(self):
        """새 전략 생성"""
        self.current_strategy_id = None
        self.strategy_name.clear()
        self.strategy_description.clear()
        self.strategy_type.setCurrentIndex(0)
        self.create_parameter_ui()  # 올바른 메서드 이름으로 수정
        print("[DEBUG] 새 전략 생성 모드로 전환")
    
    def run_backtest_strategy(self):
        """백테스트 실행 (이름 변경으로 충돌 방지)"""
        if not self.current_strategy_id:
            # 임시 전략으로 백테스트
            temp_config = StrategyConfig(
                strategy_id="temp_" + str(uuid.uuid4()),
                name=self.strategy_name.text() or "임시 전략",
                strategy_type=self.strategy_type.currentText(),
                parameters=self.get_current_parameters(),
                description=self.strategy_description.toPlainText()
            )
            # 임시로 저장
            self.strategy_manager.save_strategy(temp_config)
            strategy_id = temp_config.strategy_id
        else:
            strategy_id = self.current_strategy_id
        
        # 백테스트 요청 시그널 발생
        self.strategy_test_requested.emit(strategy_id)
        QMessageBox.information(
            self, 
            "백테스트 실행", 
            "백테스팅 탭에서 해당 전략으로 백테스트가 실행됩니다."
        )
        # TODO: 현재 설정된 전략 정보를 DB에 저장
        print("[DEBUG] 전략 저장")
        self.strategy_updated.emit("current_strategy_id")
