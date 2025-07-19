"""
전략 상세 정보 표시 위젯
- 선택된 전략의 상세 정보
- 백테스팅 결과 및 성과 지표
- 실시간 적용 상태
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt

class StrategyDetailsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. 전략 기본 정보 영역
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        info_layout = QVBoxLayout(info_frame)
        
        self.strategy_name = QLabel("전략명: -")
        self.strategy_type = QLabel("전략 유형: -")
        self.created_date = QLabel("생성일: -")
        self.last_modified = QLabel("최종 수정일: -")
        
        info_layout.addWidget(self.strategy_name)
        info_layout.addWidget(self.strategy_type)
        info_layout.addWidget(self.created_date)
        info_layout.addWidget(self.last_modified)
        
        layout.addWidget(info_frame)
        
        # 2. 백테스팅 결과 테이블
        self.result_table = QTableWidget(5, 2)
        self.result_table.setHorizontalHeaderLabels(["지표", "값"])
        self.result_table.verticalHeader().setVisible(False)
        
        # 성과 지표 행 설정
        metrics = [
            ("승률", "0%"),
            ("손익비", "0.0"),
            ("최대 손실폭", "0%"),
            ("평균 보유기간", "0일"),
            ("샤프 비율", "0.0")
        ]
        
        for row, (metric, value) in enumerate(metrics):
            self.result_table.setItem(row, 0, QTableWidgetItem(metric))
            self.result_table.setItem(row, 1, QTableWidgetItem(value))
        
        layout.addWidget(self.result_table)
        
        # 3. 실시간 적용 상태 및 버튼
        status_layout = QHBoxLayout()
        self.status_label = QLabel("실시간 적용: 비활성")
        self.toggle_btn = QPushButton("활성화")
        self.toggle_btn.clicked.connect(self.toggle_live_trading)
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.toggle_btn)
        
        layout.addLayout(status_layout)
        
        # 여백을 아래쪽으로
        layout.addStretch(1)
    
    def load_strategy(self, strategy_id):
        """전략 정보 로드"""
        print(f"[DEBUG] 전략 상세정보 로드: {strategy_id}")
        # TODO: DB에서 전략 정보를 조회하여 UI 업데이트
        
        # 테스트용 더미 데이터
        if strategy_id != "new":
            self.strategy_name.setText("전략명: 골든크로스 전략")
            self.strategy_type.setText("전략 유형: 이동평균")
            self.created_date.setText("생성일: 2025-07-19")
            self.last_modified.setText("최종 수정일: 2025-07-19")
            
            # 성과 지표 업데이트
            metrics = [
                ("승률", "67.5%"),
                ("손익비", "2.1"),
                ("최대 손실폭", "-12.3%"),
                ("평균 보유기간", "3.5일"),
                ("샤프 비율", "1.2")
            ]
            
            for row, (metric, value) in enumerate(metrics):
                self.result_table.setItem(row, 1, QTableWidgetItem(value))
        else:
            # 새 전략인 경우 초기화
            self.strategy_name.setText("전략명: 새 전략")
            self.strategy_type.setText("전략 유형: -")
            self.created_date.setText("생성일: -")
            self.last_modified.setText("최종 수정일: -")
            
            for row in range(5):
                self.result_table.setItem(row, 1, QTableWidgetItem("0"))
    
    def toggle_live_trading(self):
        """실시간 거래 활성화/비활성화 토글"""
        current_status = self.status_label.text()
        if "비활성" in current_status:
            self.status_label.setText("실시간 적용: 활성")
            self.toggle_btn.setText("비활성화")
            print("[DEBUG] 실시간 거래 활성화")
        else:
            self.status_label.setText("실시간 적용: 비활성")
            self.toggle_btn.setText("활성화")
            print("[DEBUG] 실시간 거래 비활성화")
