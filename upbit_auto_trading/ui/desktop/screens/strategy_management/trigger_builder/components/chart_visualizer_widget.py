"""
차트 시각화 위젯 (임시 구현)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal
from upbit_auto_trading.ui.desktop.components.styled_components import StyledGroupBox


class ChartVisualizerWidget(StyledGroupBox):
    """차트 시각화 위젯"""
    
    def __init__(self, parent=None):
        super().__init__("📈 차트 시각화", parent)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 차트 플레이스홀더
        self.chart_label = QLabel("차트가 여기에 표시됩니다.")
        self.chart_label.setStyleSheet("""
            QLabel {
                border: 1px dashed #ccc;
                padding: 20px;
                text-align: center;
                color: #666;
                background-color: #f9f9f9;
            }
        """)
        
        layout.addWidget(self.chart_label)
        self.setLayout(layout)
    
    def update_data_source(self, data_source_info):
        """데이터 소스 업데이트"""
        source = data_source_info.get('source', 'Unknown')
        self.chart_label.setText(f"데이터 소스: {source}\n차트 업데이트 중...")
    
    def update_simulation_result(self, result):
        """시뮬레이션 결과로 차트 업데이트"""
        trigger_name = result.get('trigger_name', 'Unknown')
        signal_count = result.get('signal_count', 0)
        self.chart_label.setText(f"시뮬레이션 결과\n트리거: {trigger_name}\n신호: {signal_count}회")
    
    def clear_chart(self):
        """차트 초기화"""
        self.chart_label.setText("차트가 여기에 표시됩니다.")
