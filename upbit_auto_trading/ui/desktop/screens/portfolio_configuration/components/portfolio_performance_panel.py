"""
포트폴리오 성과 패널 컴포넌트
- 예상 성과 지표 표시
- 백테스트 실행
- 실시간 거래 시작
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QGroupBox, QProgressBar, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class PortfolioPerformancePanel(QWidget):
    """포트폴리오 성과 패널"""
    
    # 시그널 정의
    backtest_requested = pyqtSignal(dict)  # 백테스트 요청
    live_trading_requested = pyqtSignal(dict)  # 실시간 거래 요청
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = None
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 제목
        title_label = QLabel("📈 성과 분석")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057;")
        layout.addWidget(title_label)
        
        # 기대 성과 지표
        metrics_group = QGroupBox("기대 성과 지표")
        metrics_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        metrics_layout = QVBoxLayout(metrics_group)
        
        # 기대 수익률
        self.return_label = QLabel("기대 수익률: --")
        self.return_label.setStyleSheet("font-size: 14px; color: #28a745; font-weight: bold;")
        metrics_layout.addWidget(self.return_label)
        
        # 예상 변동성
        self.volatility_label = QLabel("예상 변동성: --")
        self.volatility_label.setStyleSheet("font-size: 14px; color: #dc3545;")
        metrics_layout.addWidget(self.volatility_label)
        
        # 샤프 지수
        self.sharpe_label = QLabel("샤프 지수: --")
        self.sharpe_label.setStyleSheet("font-size: 14px; color: #007bff;")
        metrics_layout.addWidget(self.sharpe_label)
        
        # 최대 낙폭 (MDD)
        self.mdd_label = QLabel("최대 낙폭: --")
        self.mdd_label.setStyleSheet("font-size: 14px; color: #6c757d;")
        metrics_layout.addWidget(self.mdd_label)
        
        layout.addWidget(metrics_group)
        
        # 포트폴리오 요약
        summary_group = QGroupBox("포트폴리오 요약")
        summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        summary_layout = QVBoxLayout(summary_group)
        
        self.asset_count_label = QLabel("자산 개수: 0개")
        self.asset_count_label.setStyleSheet("font-size: 12px; color: #495057;")
        summary_layout.addWidget(self.asset_count_label)
        
        self.total_weight_label = QLabel("총 비중: 0%")
        self.total_weight_label.setStyleSheet("font-size: 12px; color: #495057;")
        summary_layout.addWidget(self.total_weight_label)
        
        self.risk_level_label = QLabel("위험 수준: --")
        self.risk_level_label.setStyleSheet("font-size: 12px; color: #495057;")
        summary_layout.addWidget(self.risk_level_label)
        
        layout.addWidget(summary_group)
        
        # 자산별 기여도
        contribution_group = QGroupBox("자산별 기여도")
        contribution_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        contribution_layout = QVBoxLayout(contribution_group)
        
        self.contribution_table = QTableWidget()
        self.contribution_table.setColumnCount(3)
        self.contribution_table.setHorizontalHeaderLabels(["자산", "비중", "기여도"])
        
        self.contribution_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                gridline-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #e9ecef;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #dee2e6;
                font-size: 11px;
            }
        """)
        
        # 테이블 크기 조정
        header = self.contribution_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            self.contribution_table.setColumnWidth(1, 60)
            self.contribution_table.setColumnWidth(2, 80)
        
        self.contribution_table.setMaximumHeight(150)
        contribution_layout.addWidget(self.contribution_table)
        
        layout.addWidget(contribution_group)
        
        # 액션 버튼들
        actions_group = QGroupBox("실행")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        actions_layout = QVBoxLayout(actions_group)
        
        # 백테스트 버튼
        self.backtest_btn = QPushButton("🔍 포트폴리오 백테스트")
        self.backtest_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.backtest_btn.clicked.connect(self.request_backtest)
        self.backtest_btn.setEnabled(False)
        actions_layout.addWidget(self.backtest_btn)
        
        # 실시간 거래 버튼
        self.live_trading_btn = QPushButton("🚀 실시간 거래 시작")
        self.live_trading_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.live_trading_btn.clicked.connect(self.request_live_trading)
        self.live_trading_btn.setEnabled(False)
        actions_layout.addWidget(self.live_trading_btn)
        
        layout.addWidget(actions_group)
        
        # 스페이서
        layout.addStretch()
    
    def update_performance(self, portfolio_data):
        """성과 지표 업데이트"""
        self.current_data = portfolio_data
        
        if not portfolio_data or not portfolio_data.get('assets'):
            self.clear_performance()
            return
        
        assets = portfolio_data['assets']
        total_weight = portfolio_data.get('total_weight', 0)
        
        # 기대 수익률 계산
        weighted_return = sum(
            asset['weight'] * asset['expected_return'] / 100 
            for asset in assets
        )
        
        # 예상 변동성 계산 (간단한 근사치)
        volatility = sum(
            (asset['weight'] / 100) * (asset['expected_return'] * 0.8)
            for asset in assets
        )
        
        # 샤프 지수 계산 (무위험 수익률 3% 가정)
        risk_free_rate = 3.0
        sharpe_ratio = (weighted_return - risk_free_rate) / max(volatility, 1) if volatility > 0 else 0
        
        # 최대 낙폭 (임시 계산)
        mdd = volatility * 0.6
        
        # UI 업데이트
        self.return_label.setText(f"기대 수익률: {weighted_return:.2f}%")
        self.volatility_label.setText(f"예상 변동성: {volatility:.2f}%")
        self.sharpe_label.setText(f"샤프 지수: {sharpe_ratio:.3f}")
        self.mdd_label.setText(f"최대 낙폭: -{mdd:.2f}%")
        
        # 포트폴리오 요약
        self.asset_count_label.setText(f"자산 개수: {len(assets)}개")
        self.total_weight_label.setText(f"총 비중: {total_weight:.1f}%")
        
        # 위험 수준 결정
        if volatility < 10:
            risk_level = "낮음"
            risk_color = "#28a745"
        elif volatility < 20:
            risk_level = "보통"
            risk_color = "#ffc107"
        else:
            risk_level = "높음"
            risk_color = "#dc3545"
        
        self.risk_level_label.setText(f"위험 수준: {risk_level}")
        self.risk_level_label.setStyleSheet(f"font-size: 12px; color: {risk_color}; font-weight: bold;")
        
        # 자산별 기여도 테이블 업데이트
        self.update_contribution_table(assets, weighted_return)
        
        # 버튼 활성화
        valid_portfolio = total_weight >= 95.0  # 95% 이상이면 유효한 포트폴리오로 간주
        self.backtest_btn.setEnabled(valid_portfolio)
        self.live_trading_btn.setEnabled(valid_portfolio and total_weight == 100.0)
    
    def update_contribution_table(self, assets, total_return):
        """자산별 기여도 테이블 업데이트"""
        self.contribution_table.setRowCount(len(assets))
        
        for row, asset in enumerate(assets):
            # 자산명
            asset_item = QTableWidgetItem(asset['coin'].split('-')[0])
            self.contribution_table.setItem(row, 0, asset_item)
            
            # 비중
            weight_item = QTableWidgetItem(f"{asset['weight']:.1f}%")
            weight_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.contribution_table.setItem(row, 1, weight_item)
            
            # 기여도
            contribution = (asset['weight'] / 100) * asset['expected_return']
            contribution_item = QTableWidgetItem(f"{contribution:.2f}%")
            contribution_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.contribution_table.setItem(row, 2, contribution_item)
    
    def clear_performance(self):
        """성과 지표 초기화"""
        self.return_label.setText("기대 수익률: --")
        self.volatility_label.setText("예상 변동성: --")
        self.sharpe_label.setText("샤프 지수: --")
        self.mdd_label.setText("최대 낙폭: --")
        
        self.asset_count_label.setText("자산 개수: 0개")
        self.total_weight_label.setText("총 비중: 0%")
        self.risk_level_label.setText("위험 수준: --")
        self.risk_level_label.setStyleSheet("font-size: 12px; color: #495057;")
        
        self.contribution_table.setRowCount(0)
        
        self.backtest_btn.setEnabled(False)
        self.live_trading_btn.setEnabled(False)
    
    def request_backtest(self):
        """백테스트 요청"""
        if not self.current_data:
            return
        
        reply = QMessageBox.question(
            self,
            "백테스트 실행",
            f"현재 포트폴리오로 백테스트를 실행하시겠습니까?\n\n"
            f"포트폴리오: {self.current_data['portfolio']['name']}\n"
            f"자산 개수: {len(self.current_data['assets'])}개\n"
            f"총 비중: {self.current_data['total_weight']:.1f}%",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.backtest_requested.emit(self.current_data)
    
    def request_live_trading(self):
        """실시간 거래 요청"""
        if not self.current_data:
            return
        
        # 경고 메시지
        warning_msg = f"""⚠️ 실시간 거래 시작 안내

포트폴리오: {self.current_data['portfolio']['name']}
자산 개수: {len(self.current_data['assets'])}개
총 비중: {self.current_data['total_weight']:.1f}%

실시간 거래를 시작하면 실제 자본이 사용됩니다.
시장 상황에 따라 손실이 발생할 수 있습니다.

정말로 실시간 거래를 시작하시겠습니까?"""
        
        reply = QMessageBox.critical(
            self,
            "실시간 거래 시작",
            warning_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 재확인
            confirm_msg = "이 작업은 되돌릴 수 없습니다.\n마지막으로 한 번 더 확인해주세요."
            
            final_reply = QMessageBox.question(
                self,
                "최종 확인",
                confirm_msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if final_reply == QMessageBox.StandardButton.Yes:
                self.live_trading_requested.emit(self.current_data)
