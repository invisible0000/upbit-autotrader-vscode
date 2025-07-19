"""
백테스트 결과 표시 위젯
- 핵심 성과 지표 표시
- 자산 변화 차트
- 상세 거래 내역
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QFrame,
    QProgressBar
)
from PyQt6.QtCore import Qt

class BacktestResultsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 1. 핵심 성과 지표
        metrics_frame = QFrame()
        metrics_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        metrics_layout = QHBoxLayout(metrics_frame)
        
        # 총수익률
        profit_layout = QVBoxLayout()
        profit_layout.addWidget(QLabel("총수익률"))
        self.profit_label = QLabel("0.0%")
        self.profit_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        profit_layout.addWidget(self.profit_label)
        metrics_layout.addLayout(profit_layout)
        
        # 승률
        winrate_layout = QVBoxLayout()
        winrate_layout.addWidget(QLabel("승률"))
        self.winrate_label = QLabel("0.0%")
        self.winrate_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        winrate_layout.addWidget(self.winrate_label)
        metrics_layout.addLayout(winrate_layout)
        
        # 최대 손실폭
        drawdown_layout = QVBoxLayout()
        drawdown_layout.addWidget(QLabel("최대 손실폭"))
        self.drawdown_label = QLabel("0.0%")
        self.drawdown_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        drawdown_layout.addWidget(self.drawdown_label)
        metrics_layout.addLayout(drawdown_layout)
        
        layout.addWidget(metrics_frame)
        
        # 2. 차트 영역 (실제 차트는 추후 구현)
        chart_frame = QFrame()
        chart_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        chart_frame.setMinimumHeight(300)
        chart_layout = QVBoxLayout(chart_frame)
        
        self.chart_label = QLabel("자산 변화 차트")
        self.chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_layout.addWidget(self.chart_label)
        
        layout.addWidget(chart_frame)
        
        # 3. 거래 내역 테이블
        self.trade_table = QTableWidget(0, 6)  # 초기 행은 0개, 열은 6개
        self.trade_table.setHorizontalHeaderLabels([
            "거래 시각", "종류", "코인", "가격", "수량", "수익률"
        ])
        layout.addWidget(self.trade_table)
        
        # 4. 로딩 바
        self.loading_bar = QProgressBar()
        self.loading_bar.setVisible(False)
        layout.addWidget(self.loading_bar)
    
    def clear_results(self):
        """결과 초기화"""
        self.profit_label.setText("0.0%")
        self.winrate_label.setText("0.0%")
        self.drawdown_label.setText("0.0%")
        self.trade_table.setRowCount(0)
    
    def show_loading(self, show: bool):
        """로딩 표시/숨김"""
        self.loading_bar.setVisible(show)
        if show:
            self.loading_bar.setRange(0, 0)  # 불확정 진행바
        else:
            self.loading_bar.setRange(0, 100)
    
    def update_results(self, results: dict):
        """백테스트 결과 업데이트
        
        Args:
            results (dict): {
                'total_profit': float,  # 총수익률
                'win_rate': float,      # 승률
                'max_drawdown': float,  # 최대 손실폭
                'trades': list          # 거래 내역 리스트
            }
        """
        # 1. 성과 지표 업데이트
        self.profit_label.setText(f"{results['total_profit']:.1f}%")
        self.winrate_label.setText(f"{results['win_rate']:.1f}%")
        self.drawdown_label.setText(f"{results['max_drawdown']:.1f}%")
        
        # 성과에 따른 색상 설정
        self.profit_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: %s" % 
            ("green" if results['total_profit'] > 0 else "red")
        )
        
        # 2. 거래 내역 테이블 업데이트
        self.trade_table.setRowCount(0)
        for trade in results.get('trades', []):
            row = self.trade_table.rowCount()
            self.trade_table.insertRow(row)
            
            self.trade_table.setItem(row, 0, QTableWidgetItem(trade['time']))
            self.trade_table.setItem(row, 1, QTableWidgetItem(trade['type']))
            self.trade_table.setItem(row, 2, QTableWidgetItem(trade['coin']))
            self.trade_table.setItem(row, 3, QTableWidgetItem(f"{trade['price']:,}"))
            self.trade_table.setItem(row, 4, QTableWidgetItem(f"{trade['amount']:.4f}"))
            
            profit_item = QTableWidgetItem(f"{trade.get('profit', 0):.1f}%")
            if 'profit' in trade:
                profit_item.setForeground(
                    Qt.GlobalColor.green if trade['profit'] > 0 else Qt.GlobalColor.red
                )
            self.trade_table.setItem(row, 5, profit_item)
        
        # 3. TODO: 차트 업데이트
        # self.update_chart(results.get('equity_curve', []))
