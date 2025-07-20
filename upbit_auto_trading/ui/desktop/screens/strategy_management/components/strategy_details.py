"""
전략 상세 정보 표시 위젯
- 선택된 전략의 상세 정보
- 백테스팅 결과 및 성과 지표
- 실시간 적용 상태
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QTableWidget, QTableWidgetItem,
    QGroupBox, QTextEdit, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt
import sys
import os

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

from upbit_auto_trading.business_logic.strategy.trading_strategies import StrategyManager

class StrategyDetailsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.strategy_manager = StrategyManager()
        self.current_strategy_id = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 스플리터로 상하 분할
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 상단: 전략 기본 정보
        info_group = QGroupBox("📊 전략 정보")
        info_layout = QVBoxLayout(info_group)
        
        # 전략 기본 정보
        self.strategy_name = QLabel("📝 전략명: 선택된 전략이 없습니다")
        self.strategy_type = QLabel("🔧 전략 유형: -")
        self.created_date = QLabel("📅 생성일: -")
        self.last_modified = QLabel("🔄 최종 수정일: -")
        
        for label in [self.strategy_name, self.strategy_type, self.created_date, self.last_modified]:
            label.setStyleSheet("font-size: 12px; margin: 2px 0;")
            info_layout.addWidget(label)
        
        # 전략 설명
        self.description_label = QLabel("📄 전략 설명:")
        self.description_text = QTextEdit()
        self.description_text.setMaximumHeight(80)
        self.description_text.setReadOnly(True)
        info_layout.addWidget(self.description_label)
        info_layout.addWidget(self.description_text)
        
        splitter.addWidget(info_group)
        
        # 하단: 성과 지표 및 컨트롤
        performance_group = QGroupBox("📈 성과 지표")
        performance_layout = QVBoxLayout(performance_group)
        
        # 성과 지표 테이블
        self.result_table = QTableWidget(6, 2)
        self.result_table.setHorizontalHeaderLabels(["지표", "값"])
        
        # 테이블 설정
        header = self.result_table.horizontalHeader()
        if header:
            header.setStretchLastSection(True)
        
        vertical_header = self.result_table.verticalHeader()
        if vertical_header:
            vertical_header.setVisible(False)
        
        # 성과 지표 초기값
        metrics = [
            ("총 수익률", "0%"),
            ("승률", "0%"),
            ("손익비", "0.0"),
            ("최대 손실폭", "0%"),
            ("평균 보유기간", "0일"),
            ("샤프 비율", "0.0")
        ]
        
        for row, (metric, value) in enumerate(metrics):
            self.result_table.setItem(row, 0, QTableWidgetItem(metric))
            self.result_table.setItem(row, 1, QTableWidgetItem(value))
        
        performance_layout.addWidget(self.result_table)
        
        # 실시간 적용 컨트롤
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        self.status_label = QLabel("🔴 실시간 적용: 비활성")
        self.toggle_btn = QPushButton("▶️ 활성화")
        self.toggle_btn.clicked.connect(self.toggle_live_trading)
        self.toggle_btn.setEnabled(False)
        
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.toggle_btn)
        
        performance_layout.addWidget(control_frame)
        
        splitter.addWidget(performance_group)
        layout.addWidget(splitter)
    
    def load_strategy(self, strategy_id):
        """전략 정보 로드"""
        self.current_strategy_id = strategy_id
        
        if strategy_id == "new" or not strategy_id:
            self.clear_display()
            return
        
        # DB에서 전략 정보 조회
        strategy_config = self.strategy_manager.load_strategy(strategy_id)
        
        if strategy_config:
            self.strategy_name.setText(f"📝 전략명: {strategy_config.name}")
            self.strategy_type.setText(f"🔧 전략 유형: {strategy_config.strategy_type}")
            self.created_date.setText(f"📅 생성일: {strategy_config.created_at.strftime('%Y-%m-%d %H:%M') if strategy_config.created_at else 'N/A'}")
            self.last_modified.setText(f"🔄 최종 수정일: {strategy_config.updated_at.strftime('%Y-%m-%d %H:%M') if strategy_config.updated_at else 'N/A'}")
            
            # 전략 설명
            self.description_text.setText(strategy_config.description or "설명이 없습니다.")
            
            # 파라미터 표시 (성과 지표 대신)
            self.display_strategy_parameters(strategy_config)
            
            # 버튼 활성화
            self.toggle_btn.setEnabled(True)
        else:
            self.clear_display()
    
    def display_strategy_parameters(self, strategy_config):
        """전략 파라미터 표시"""
        parameters = strategy_config.parameters
        
        # 전략 타입별 파라미터 표시
        if strategy_config.strategy_type == "이동평균 교차":
            params = [
                ("짧은 이동평균", f"{parameters.get('short_period', 5)}일"),
                ("긴 이동평균", f"{parameters.get('long_period', 20)}일"),
                ("이동평균 타입", parameters.get('ma_type', 'SMA')),
                ("진입 신호", "골든크로스"),
                ("청산 신호", "데드크로스"),
                ("상태", "설정 완료")
            ]
        elif strategy_config.strategy_type == "RSI":
            params = [
                ("RSI 기간", f"{parameters.get('period', 14)}일"),
                ("과매도 기준", f"{parameters.get('oversold_threshold', 30)}"),
                ("과매수 기준", f"{parameters.get('overbought_threshold', 70)}"),
                ("RSI 스무딩", parameters.get('smoothing', 'EMA')),
                ("진입 조건", f"RSI < {parameters.get('oversold_threshold', 30)}"),
                ("상태", "설정 완료")
            ]
        elif strategy_config.strategy_type == "볼린저 밴드":
            params = [
                ("기간", f"{parameters.get('period', 20)}일"),
                ("표준편차", f"{parameters.get('std_dev', 2.0)}"),
                ("기준선", parameters.get('basis', 'SMA')),
                ("진입 조건", "하단선 터치"),
                ("청산 조건", "중심선 회귀"),
                ("상태", "설정 완료")
            ]
        else:
            params = [
                ("전략 타입", strategy_config.strategy_type),
                ("파라미터 수", str(len(parameters))),
                ("상태", "설정 완료"),
                ("", ""),
                ("", ""),
                ("", "")
            ]
        
        # 테이블에 파라미터 표시
        for row, (param_name, param_value) in enumerate(params):
            if row < self.result_table.rowCount():
                self.result_table.setItem(row, 0, QTableWidgetItem(param_name))
                self.result_table.setItem(row, 1, QTableWidgetItem(str(param_value)))
    
    def clear_display(self):
        """화면 초기화"""
        self.strategy_name.setText("📝 전략명: 선택된 전략이 없습니다")
        self.strategy_type.setText("🔧 전략 유형: -")
        self.created_date.setText("📅 생성일: -")
        self.last_modified.setText("🔄 최종 수정일: -")
        self.description_text.setText("전략을 선택하여 상세 정보를 확인하세요.")
        
        # 테이블 초기화
        for row in range(self.result_table.rowCount()):
            self.result_table.setItem(row, 0, QTableWidgetItem(""))
            self.result_table.setItem(row, 1, QTableWidgetItem(""))
        
        self.toggle_btn.setEnabled(False)
    
    def toggle_live_trading(self):
        """실시간 거래 활성화/비활성화 토글"""
        if not self.current_strategy_id:
            return
        
        current_status = self.status_label.text()
        if "비활성" in current_status:
            self.status_label.setText("🟢 실시간 적용: 활성")
            self.toggle_btn.setText("⏸️ 비활성화")
            print(f"[DEBUG] 전략 {self.current_strategy_id} 실시간 거래 활성화")
        else:
            self.status_label.setText("🔴 실시간 적용: 비활성")
            self.toggle_btn.setText("▶️ 활성화")
            print(f"[DEBUG] 전략 {self.current_strategy_id} 실시간 거래 비활성화")
