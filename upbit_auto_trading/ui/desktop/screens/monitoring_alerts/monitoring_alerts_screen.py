"""
모니터링 및 알림 화면 메인 모듈
- 실시간 시장 모니터링
- 알림 설정 및 관리
- 알림 기록 조회
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget
from .components.real_time_monitor import RealTimeMonitorWidget
from .components.alert_settings_panel import AlertSettingsPanel
from .components.alert_history_panel import AlertHistoryPanel

class MonitoringAlertsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("모니터링 및 알림")
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 탭 위젯 생성
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 10px 20px;
                margin-right: 2px;
                font-size: 14px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #007bff;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
        """)
        
        # 실시간 모니터링 탭
        self.monitor_widget = RealTimeMonitorWidget()
        tab_widget.addTab(self.monitor_widget, "📊 실시간 모니터링")
        
        # 알림 설정 탭
        self.alert_settings_panel = AlertSettingsPanel()
        tab_widget.addTab(self.alert_settings_panel, "🔔 알림 설정")
        
        # 알림 기록 탭
        self.alert_history_panel = AlertHistoryPanel()
        tab_widget.addTab(self.alert_history_panel, "📋 알림 기록")
        
        layout.addWidget(tab_widget)
        
        # 시그널/슬롯 연결
        self.connect_signals()
    
    def connect_signals(self):
        """시그널/슬롯 연결"""
        # 알림 설정에서 새 알림이 생성되면 기록에 추가
        self.alert_settings_panel.alert_created.connect(
            self.alert_history_panel.add_alert_record
        )
        
        # 실시간 모니터에서 알림 조건 확인
        self.monitor_widget.price_changed.connect(
            self.alert_settings_panel.check_price_alerts
        )
