"""
알림 설정 패널 컴포넌트
- 다양한 알림 유형 설정
- 알림 조건 및 전달 방식 설정
- 활성 알림 관리
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox,
    QPushButton, QCheckBox, QGroupBox, QFrame, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
import datetime

class AlertSettingsPanel(QWidget):
    """알림 설정 패널"""
    
    # 시그널 정의
    alert_created = pyqtSignal(dict)  # 새 알림 생성
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_alerts = []
        self.price_alerts = {}
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        
        # 왼쪽: 알림 설정
        left_panel = self.create_alert_settings_panel()
        layout.addWidget(left_panel, stretch=2)
        
        # 오른쪽: 활성 알림 목록
        right_panel = self.create_active_alerts_panel()
        layout.addWidget(right_panel, stretch=1)
    
    def create_alert_settings_panel(self):
        """알림 설정 패널 생성"""
        group = QGroupBox("🔔 새 알림 설정")
        group.setStyleSheet("""
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
        
        layout = QVBoxLayout(group)
        
        # 알림 유형 선택
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("알림 유형:"))
        
        self.alert_type_combo = QComboBox()
        self.alert_type_combo.addItems([
            "가격 알림", "기술적 지표 알림", "주문 체결 알림", 
            "거래량 알림", "시스템 상태 알림"
        ])
        self.alert_type_combo.currentTextChanged.connect(self.on_alert_type_changed)
        type_layout.addWidget(self.alert_type_combo)
        type_layout.addStretch()
        
        layout.addLayout(type_layout)
        
        # 동적 설정 영역
        self.dynamic_settings_frame = QFrame()
        self.dynamic_settings_frame.setFrameStyle(QFrame.Shape.Box)
        self.dynamic_settings_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #e9ecef;
                border-radius: 6px;
                background-color: #f8f9fa;
                padding: 15px;
            }
        """)
        
        self.dynamic_layout = QVBoxLayout(self.dynamic_settings_frame)
        layout.addWidget(self.dynamic_settings_frame)
        
        # 알림 전달 방식
        delivery_group = QGroupBox("알림 전달 방식")
        delivery_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        delivery_layout = QVBoxLayout(delivery_group)
        
        self.popup_check = QCheckBox("프로그램 내 팝업")
        self.popup_check.setChecked(True)
        delivery_layout.addWidget(self.popup_check)
        
        self.sound_check = QCheckBox("소리 알림")
        self.sound_check.setChecked(True)
        delivery_layout.addWidget(self.sound_check)
        
        self.email_check = QCheckBox("이메일 알림")
        delivery_layout.addWidget(self.email_check)
        
        layout.addWidget(delivery_group)
        
        # 저장 버튼
        self.save_alert_btn = QPushButton("💾 알림 저장")
        self.save_alert_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.save_alert_btn.clicked.connect(self.save_alert)
        layout.addWidget(self.save_alert_btn)
        
        # 초기 설정 로드
        self.on_alert_type_changed()
        
        return group
    
    def create_active_alerts_panel(self):
        """활성 알림 패널 생성"""
        group = QGroupBox("📋 활성 알림 목록")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # 활성 알림 테이블
        self.active_alerts_table = QTableWidget()
        self.active_alerts_table.setColumnCount(4)
        self.active_alerts_table.setHorizontalHeaderLabels([
            "유형", "조건", "상태", "액션"
        ])
        
        self.active_alerts_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                gridline-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #dee2e6;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        
        # 테이블 설정
        header = self.active_alerts_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)    # 유형
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 조건
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # 상태
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # 액션
            
            self.active_alerts_table.setColumnWidth(0, 80)
            self.active_alerts_table.setColumnWidth(2, 60)
            self.active_alerts_table.setColumnWidth(3, 60)
        
        layout.addWidget(self.active_alerts_table)
        
        # 일괄 관리 버튼
        buttons_layout = QHBoxLayout()
        
        enable_all_btn = QPushButton("전체 활성화")
        enable_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        enable_all_btn.clicked.connect(self.enable_all_alerts)
        buttons_layout.addWidget(enable_all_btn)
        
        disable_all_btn = QPushButton("전체 비활성화")
        disable_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        disable_all_btn.clicked.connect(self.disable_all_alerts)
        buttons_layout.addWidget(disable_all_btn)
        
        layout.addLayout(buttons_layout)
        
        # 초기 데이터 로드
        self.load_active_alerts()
        
        return group
    
    def on_alert_type_changed(self):
        """알림 유형 변경 시 동적 UI 업데이트"""
        # 기존 위젯들 제거
        for i in reversed(range(self.dynamic_layout.count())):
            child = self.dynamic_layout.itemAt(i)
            if child and child.widget():
                child.widget().setParent(None)
        
        alert_type = self.alert_type_combo.currentText()
        
        if alert_type == "가격 알림":
            self.create_price_alert_settings()
        elif alert_type == "기술적 지표 알림":
            self.create_indicator_alert_settings()
        elif alert_type == "주문 체결 알림":
            self.create_order_alert_settings()
        elif alert_type == "거래량 알림":
            self.create_volume_alert_settings()
        elif alert_type == "시스템 상태 알림":
            self.create_system_alert_settings()
    
    def create_price_alert_settings(self):
        """가격 알림 설정 UI"""
        form = QFormLayout()
        
        # 코인 선택
        self.price_coin_combo = QComboBox()
        self.price_coin_combo.addItems([
            "BTC-KRW", "ETH-KRW", "ADA-KRW", "DOT-KRW", "SOL-KRW"
        ])
        form.addRow("코인:", self.price_coin_combo)
        
        # 조건 선택
        self.price_condition_combo = QComboBox()
        self.price_condition_combo.addItems([
            "이상일 때", "이하일 때", "정확히 일치할 때"
        ])
        form.addRow("조건:", self.price_condition_combo)
        
        # 목표 가격
        self.target_price_input = QLineEdit()
        self.target_price_input.setPlaceholderText("예: 50000000")
        form.addRow("목표 가격 (KRW):", self.target_price_input)
        
        # 설명
        desc_label = QLabel("💡 설정한 코인이 목표 가격에 도달하면 알림을 받습니다.")
        desc_label.setStyleSheet("font-size: 12px; color: #6c757d; font-style: italic;")
        form.addRow(desc_label)
        
        self.dynamic_layout.addLayout(form)
    
    def create_indicator_alert_settings(self):
        """기술적 지표 알림 설정 UI"""
        form = QFormLayout()
        
        # 코인 선택
        self.indicator_coin_combo = QComboBox()
        self.indicator_coin_combo.addItems([
            "BTC-KRW", "ETH-KRW", "ADA-KRW", "DOT-KRW", "SOL-KRW"
        ])
        form.addRow("코인:", self.indicator_coin_combo)
        
        # 지표 선택
        self.indicator_type_combo = QComboBox()
        self.indicator_type_combo.addItems([
            "RSI", "MACD", "볼린저 밴드", "이동평균선", "스토캐스틱"
        ])
        form.addRow("지표:", self.indicator_type_combo)
        
        # 조건
        self.indicator_condition_combo = QComboBox()
        self.indicator_condition_combo.addItems([
            "이상일 때", "이하일 때", "크로스 오버", "크로스 언더"
        ])
        form.addRow("조건:", self.indicator_condition_combo)
        
        # 임계값
        self.threshold_input = QDoubleSpinBox()
        self.threshold_input.setRange(0, 100)
        self.threshold_input.setValue(70)
        form.addRow("임계값:", self.threshold_input)
        
        # 설명
        desc_label = QLabel("💡 기술적 지표가 설정된 조건을 만족하면 알림을 받습니다.")
        desc_label.setStyleSheet("font-size: 12px; color: #6c757d; font-style: italic;")
        form.addRow(desc_label)
        
        self.dynamic_layout.addLayout(form)
    
    def create_order_alert_settings(self):
        """주문 체결 알림 설정 UI"""
        form = QFormLayout()
        
        # 알림 대상
        self.order_target_combo = QComboBox()
        self.order_target_combo.addItems([
            "모든 주문", "매수 주문만", "매도 주문만", "특정 코인만"
        ])
        form.addRow("알림 대상:", self.order_target_combo)
        
        # 최소 체결 금액
        self.min_amount_input = QLineEdit()
        self.min_amount_input.setPlaceholderText("예: 100000 (10만원 이상)")
        form.addRow("최소 체결 금액:", self.min_amount_input)
        
        # 설명
        desc_label = QLabel("💡 주문이 체결되면 즉시 알림을 받습니다.")
        desc_label.setStyleSheet("font-size: 12px; color: #6c757d; font-style: italic;")
        form.addRow(desc_label)
        
        self.dynamic_layout.addLayout(form)
    
    def create_volume_alert_settings(self):
        """거래량 알림 설정 UI"""
        form = QFormLayout()
        
        # 코인 선택
        self.volume_coin_combo = QComboBox()
        self.volume_coin_combo.addItems([
            "BTC-KRW", "ETH-KRW", "ADA-KRW", "DOT-KRW", "SOL-KRW"
        ])
        form.addRow("코인:", self.volume_coin_combo)
        
        # 거래량 조건
        self.volume_condition_combo = QComboBox()
        self.volume_condition_combo.addItems([
            "평균 대비 2배 이상", "평균 대비 3배 이상", "절대값 이상"
        ])
        form.addRow("조건:", self.volume_condition_combo)
        
        # 기준 기간
        self.period_input = QSpinBox()
        self.period_input.setRange(1, 24)
        self.period_input.setValue(1)
        self.period_input.setSuffix("시간")
        form.addRow("기준 기간:", self.period_input)
        
        # 설명
        desc_label = QLabel("💡 거래량이 평소보다 급증하면 알림을 받습니다.")
        desc_label.setStyleSheet("font-size: 12px; color: #6c757d; font-style: italic;")
        form.addRow(desc_label)
        
        self.dynamic_layout.addLayout(form)
    
    def create_system_alert_settings(self):
        """시스템 상태 알림 설정 UI"""
        form = QFormLayout()
        
        # 알림 유형
        self.system_type_combo = QComboBox()
        self.system_type_combo.addItems([
            "연결 오류", "API 한도 초과", "전략 실행 오류", "잔고 부족"
        ])
        form.addRow("알림 유형:", self.system_type_combo)
        
        # 심각도
        self.severity_combo = QComboBox()
        self.severity_combo.addItems([
            "정보", "경고", "오류", "치명적"
        ])
        form.addRow("최소 심각도:", self.severity_combo)
        
        # 설명
        desc_label = QLabel("💡 시스템 오류나 중요한 상태 변화 시 알림을 받습니다.")
        desc_label.setStyleSheet("font-size: 12px; color: #6c757d; font-style: italic;")
        form.addRow(desc_label)
        
        self.dynamic_layout.addLayout(form)
    
    def save_alert(self):
        """알림 저장"""
        try:
            alert_type = self.alert_type_combo.currentText()
            
            alert_data = {
                "id": len(self.active_alerts) + 1,
                "type": alert_type,
                "created_time": datetime.datetime.now(),
                "enabled": True,
                "delivery_methods": {
                    "popup": self.popup_check.isChecked(),
                    "sound": self.sound_check.isChecked(),
                    "email": self.email_check.isChecked()
                }
            }
            
            if alert_type == "가격 알림":
                alert_data.update({
                    "coin": self.price_coin_combo.currentText(),
                    "condition": self.price_condition_combo.currentText(),
                    "target_price": float(self.target_price_input.text() or "0"),
                    "description": f"{self.price_coin_combo.currentText()} 가격이 {self.target_price_input.text()}원 {self.price_condition_combo.currentText()}"
                })
                
                # 가격 알림을 체크 리스트에 추가
                coin = alert_data["coin"]
                target_price = alert_data["target_price"]
                condition = alert_data["condition"]
                
                if coin not in self.price_alerts:
                    self.price_alerts[coin] = []
                
                self.price_alerts[coin].append({
                    "id": alert_data["id"],
                    "target_price": target_price,
                    "condition": condition,
                    "enabled": True
                })
                
            elif alert_type == "기술적 지표 알림":
                alert_data.update({
                    "coin": self.indicator_coin_combo.currentText(),
                    "indicator": self.indicator_type_combo.currentText(),
                    "condition": self.indicator_condition_combo.currentText(),
                    "threshold": self.threshold_input.value(),
                    "description": f"{self.indicator_coin_combo.currentText()} {self.indicator_type_combo.currentText()}이 {self.threshold_input.value()} {self.indicator_condition_combo.currentText()}"
                })
            
            # 기타 알림 유형들도 유사하게 처리...
            
            if not alert_data.get("description"):
                alert_data["description"] = f"{alert_type} 알림"
            
            # 유효성 검사
            if alert_type == "가격 알림" and alert_data["target_price"] <= 0:
                QMessageBox.warning(self, "입력 오류", "올바른 목표 가격을 입력해주세요.")
                return
            
            # 알림 저장
            self.active_alerts.append(alert_data)
            self.update_active_alerts_table()
            
            # 성공 메시지
            QMessageBox.information(
                self,
                "알림 저장 완료",
                f"{alert_data['description']} 알림이 설정되었습니다."
            )
            
            # 알림 생성 시그널 발송
            self.alert_created.emit(alert_data)
            
            # 입력 필드 초기화
            self.reset_form()
            
        except ValueError as e:
            QMessageBox.warning(self, "입력 오류", "올바른 숫자를 입력해주세요.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"알림 저장 중 오류가 발생했습니다: {str(e)}")
    
    def reset_form(self):
        """입력 폼 초기화"""
        alert_type = self.alert_type_combo.currentText()
        
        if alert_type == "가격 알림":
            self.target_price_input.clear()
        elif alert_type == "거래량 알림":
            self.period_input.setValue(1)
        # 기타 필드들도 초기화...
    
    def load_active_alerts(self):
        """활성 알림 목록 로드"""
        # 샘플 데이터
        sample_alerts = [
            {
                "id": 1,
                "type": "가격 알림",
                "description": "BTC-KRW 50,000,000원 이상",
                "enabled": True
            },
            {
                "id": 2,
                "type": "기술적 지표 알림",
                "description": "ETH-KRW RSI 70 이상",
                "enabled": True
            },
            {
                "id": 3,
                "type": "주문 체결 알림",
                "description": "모든 주문 체결 시",
                "enabled": False
            }
        ]
        
        self.active_alerts = sample_alerts
        self.update_active_alerts_table()
    
    def update_active_alerts_table(self):
        """활성 알림 테이블 업데이트"""
        self.active_alerts_table.setRowCount(len(self.active_alerts))
        
        for row, alert in enumerate(self.active_alerts):
            # 유형
            type_item = QTableWidgetItem(alert["type"])
            self.active_alerts_table.setItem(row, 0, type_item)
            
            # 조건
            desc_item = QTableWidgetItem(alert["description"])
            self.active_alerts_table.setItem(row, 1, desc_item)
            
            # 상태
            status = "활성" if alert["enabled"] else "비활성"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            color = "#28a745" if alert["enabled"] else "#6c757d"
            status_item.setForeground(QColor(color))
            self.active_alerts_table.setItem(row, 2, status_item)
            
            # 액션 버튼
            action_btn = QPushButton("삭제")
            action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            action_btn.clicked.connect(lambda checked, r=row: self.delete_alert(r))
            self.active_alerts_table.setCellWidget(row, 3, action_btn)
    
    def delete_alert(self, row):
        """알림 삭제"""
        if 0 <= row < len(self.active_alerts):
            alert = self.active_alerts[row]
            
            reply = QMessageBox.question(
                self,
                "알림 삭제",
                f"'{alert['description']}' 알림을 삭제하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.active_alerts.pop(row)
                self.update_active_alerts_table()
    
    def enable_all_alerts(self):
        """모든 알림 활성화"""
        for alert in self.active_alerts:
            alert["enabled"] = True
        self.update_active_alerts_table()
    
    def disable_all_alerts(self):
        """모든 알림 비활성화"""
        for alert in self.active_alerts:
            alert["enabled"] = False
        self.update_active_alerts_table()
    
    def check_price_alerts(self, coin, current_price):
        """가격 알림 조건 확인"""
        if coin in self.price_alerts:
            for alert in self.price_alerts[coin]:
                if not alert["enabled"]:
                    continue
                
                condition = alert["condition"]
                target_price = alert["target_price"]
                
                triggered = False
                if condition == "이상일 때" and current_price >= target_price:
                    triggered = True
                elif condition == "이하일 때" and current_price <= target_price:
                    triggered = True
                elif condition == "정확히 일치할 때" and abs(current_price - target_price) < (target_price * 0.001):
                    triggered = True
                
                if triggered:
                    self.trigger_alert(alert["id"], coin, current_price, target_price)
                    alert["enabled"] = False  # 한 번 발생한 알림은 비활성화
    
    def trigger_alert(self, alert_id, coin, current_price, target_price):
        """알림 발생"""
        # 알림 기록 생성
        alert_record = {
            "id": alert_id,
            "type": "가격 알림",
            "coin": coin,
            "message": f"{coin} 가격이 목표가 {target_price:,}원에 도달했습니다. (현재가: {current_price:,}원)",
            "timestamp": datetime.datetime.now(),
            "status": "발생"
        }
        
        # 팝업 알림 표시
        QMessageBox.information(
            self,
            "🔔 가격 알림",
            alert_record["message"]
        )
        
        # 알림 기록에 추가
        self.alert_created.emit(alert_record)
        
        print(f"[ALERT] {alert_record['message']}")
