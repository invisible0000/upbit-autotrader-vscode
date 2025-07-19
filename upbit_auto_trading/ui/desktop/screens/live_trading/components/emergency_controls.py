"""
긴급 제어 패널 컴포넌트
- 전체 전략 긴급 중지
- 시스템 상태 표시
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, 
    QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette

class EmergencyControls(QWidget):
    """긴급 제어 패널"""
    
    # 시그널 정의
    emergency_stop_all = pyqtSignal()
    strategy_stopped = pyqtSignal(str)  # strategy_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_timer()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 프레임으로 감싸기
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        
        frame_layout = QHBoxLayout(frame)
        
        # 1. 시스템 상태 표시
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("시스템 상태: 정상")
        self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        self.active_count_label = QLabel("활성 전략: 0개")
        self.active_count_label.setStyleSheet("color: #495057;")
        status_layout.addWidget(self.active_count_label)
        
        frame_layout.addLayout(status_layout)
        
        # 2. 스페이서
        frame_layout.addStretch()
        
        # 3. 현재 시간 표시
        self.time_label = QLabel("--:--:--")
        self.time_label.setStyleSheet("color: #6c757d; font-size: 14px;")
        frame_layout.addWidget(self.time_label)
        
        # 4. 긴급 정지 버튼
        self.emergency_button = QPushButton("🚨 긴급 전체 정지")
        self.emergency_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        self.emergency_button.clicked.connect(self.on_emergency_stop)
        frame_layout.addWidget(self.emergency_button)
        
        layout.addWidget(frame)
        
        # 높이 제한
        self.setMaximumHeight(80)
    
    def setup_timer(self):
        """타이머 설정 - 실시간 업데이트"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1000)  # 1초마다 업데이트
    
    def update_display(self):
        """디스플레이 업데이트"""
        from datetime import datetime
        
        # 현재 시간 업데이트
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)
        
        # TODO: 실제 활성 전략 수 조회
        # active_count = get_active_strategies_count()
        active_count = 0  # 임시
        self.active_count_label.setText(f"활성 전략: {active_count}개")
        
        # 시스템 상태 업데이트
        if active_count > 0:
            self.status_label.setText("시스템 상태: 거래 중")
            self.status_label.setStyleSheet("color: #007bff; font-weight: bold;")
        else:
            self.status_label.setText("시스템 상태: 대기")
            self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
    
    def on_emergency_stop(self):
        """긴급 정지 버튼 클릭 핸들러"""
        # 확인 대화상자
        reply = QMessageBox.question(
            self,
            "긴급 전체 정지",
            "⚠️ 모든 활성 전략을 즉시 중지하시겠습니까?\n\n"
            "이 작업은 되돌릴 수 없으며, 현재 진행 중인 모든 거래가 중단됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.emergency_stop_all.emit()
            self.show_stop_confirmation()
    
    def show_stop_confirmation(self):
        """정지 확인 메시지"""
        QMessageBox.information(
            self,
            "긴급 정지 완료",
            "✅ 모든 활성 전략이 중지되었습니다."
        )
    
    def update_active_count(self, count):
        """활성 전략 수 업데이트"""
        self.active_count_label.setText(f"활성 전략: {count}개")
