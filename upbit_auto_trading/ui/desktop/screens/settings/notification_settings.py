"""
알림 설정 모듈

이 모듈은 알림 설정 기능을 구현합니다.
- 가격 알림 설정
- 거래 알림 설정
- 시스템 알림 설정
"""

import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QCheckBox, QPushButton, QMessageBox,
    QGroupBox, QComboBox, QSpinBox, QTimeEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTime


class NotificationSettings(QWidget):
    """알림 설정 위젯 클래스"""
    
    # 설정 변경 시그널
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("widget-notification-settings")
        
        # UI 설정
        self._setup_ui()
        
        # 시그널 연결
        self._connect_signals()
    
    def _setup_ui(self):
        """UI 설정"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 알림 활성화 그룹
        enable_group = QGroupBox("알림 활성화")
        enable_layout = QVBoxLayout(enable_group)
        
        # 가격 알림 체크박스
        self.enable_price_alerts_checkbox = QCheckBox("가격 알림")
        self.enable_price_alerts_checkbox.setObjectName("checkbox-enable-price-alerts")
        enable_layout.addWidget(self.enable_price_alerts_checkbox)
        
        # 거래 알림 체크박스
        self.enable_trade_alerts_checkbox = QCheckBox("거래 알림")
        self.enable_trade_alerts_checkbox.setObjectName("checkbox-enable-trade-alerts")
        enable_layout.addWidget(self.enable_trade_alerts_checkbox)
        
        # 시스템 알림 체크박스
        self.enable_system_alerts_checkbox = QCheckBox("시스템 알림")
        self.enable_system_alerts_checkbox.setObjectName("checkbox-enable-system-alerts")
        enable_layout.addWidget(self.enable_system_alerts_checkbox)
        
        # 알림 활성화 설명
        enable_info = QLabel("* 각 알림 유형을 개별적으로 활성화/비활성화할 수 있습니다.")
        enable_info.setObjectName("label-enable-info")
        enable_info.setStyleSheet("color: #666666; font-size: 10px;")
        enable_layout.addWidget(enable_info)
        
        # 가격 알림 그룹
        price_group = QGroupBox("가격 알림 설정")
        price_layout = QVBoxLayout(price_group)
        
        # 폼 레이아웃
        price_form_layout = QFormLayout()
        price_form_layout.setContentsMargins(0, 10, 0, 10)
        price_form_layout.setSpacing(10)
        
        # 가격 변동 임계값 입력
        self.price_threshold_input = QSpinBox()
        self.price_threshold_input.setObjectName("input-price-threshold")
        self.price_threshold_input.setRange(1, 100)
        self.price_threshold_input.setValue(5)
        self.price_threshold_input.setSuffix(" %")
        price_form_layout.addRow("가격 변동 임계값:", self.price_threshold_input)
        
        # 가격 알림 주기 선택
        self.price_interval_combo = QComboBox()
        self.price_interval_combo.setObjectName("combo-price-interval")
        self.price_interval_combo.addItems(["1분", "5분", "15분", "30분", "1시간"])
        self.price_interval_combo.setCurrentIndex(1)  # 기본값: 5분
        price_form_layout.addRow("알림 주기:", self.price_interval_combo)
        
        price_layout.addLayout(price_form_layout)
        
        # 가격 알림 설명
        price_info = QLabel("* 설정한 임계값 이상으로 가격이 변동하면 알림이 발생합니다.\n* 알림 주기는 가격 변동을 확인하는 간격입니다.")
        price_info.setObjectName("label-price-info")
        price_info.setStyleSheet("color: #666666; font-size: 10px;")
        price_layout.addWidget(price_info)
        
        # 거래 알림 그룹
        trade_group = QGroupBox("거래 알림 설정")
        trade_layout = QVBoxLayout(trade_group)
        
        # 주문 체결 알림 체크박스
        self.enable_order_executed_checkbox = QCheckBox("주문 체결 알림")
        self.enable_order_executed_checkbox.setObjectName("checkbox-enable-order-executed")
        self.enable_order_executed_checkbox.setChecked(True)
        trade_layout.addWidget(self.enable_order_executed_checkbox)
        
        # 수익/손실 알림 체크박스
        self.enable_profit_loss_checkbox = QCheckBox("수익/손실 알림")
        self.enable_profit_loss_checkbox.setObjectName("checkbox-enable-profit-loss")
        self.enable_profit_loss_checkbox.setChecked(True)
        trade_layout.addWidget(self.enable_profit_loss_checkbox)
        
        # 포지션 변경 알림 체크박스
        self.enable_position_change_checkbox = QCheckBox("포지션 변경 알림")
        self.enable_position_change_checkbox.setObjectName("checkbox-enable-position-change")
        self.enable_position_change_checkbox.setChecked(True)
        trade_layout.addWidget(self.enable_position_change_checkbox)
        
        # 거래 알림 설명
        trade_info = QLabel("* 주문 체결, 수익/손실 발생, 포지션 변경 시 알림이 발생합니다.")
        trade_info.setObjectName("label-trade-info")
        trade_info.setStyleSheet("color: #666666; font-size: 10px;")
        trade_layout.addWidget(trade_info)
        
        # 시스템 알림 그룹
        system_group = QGroupBox("시스템 알림 설정")
        system_layout = QVBoxLayout(system_group)
        
        # 오류 알림 체크박스
        self.enable_error_alerts_checkbox = QCheckBox("오류 알림")
        self.enable_error_alerts_checkbox.setObjectName("checkbox-enable-error-alerts")
        self.enable_error_alerts_checkbox.setChecked(True)
        system_layout.addWidget(self.enable_error_alerts_checkbox)
        
        # 시스템 상태 알림 체크박스
        self.enable_system_status_checkbox = QCheckBox("시스템 상태 알림")
        self.enable_system_status_checkbox.setObjectName("checkbox-enable-system-status")
        self.enable_system_status_checkbox.setChecked(True)
        system_layout.addWidget(self.enable_system_status_checkbox)
        
        # 일일 요약 알림 체크박스 및 시간 설정
        daily_summary_layout = QHBoxLayout()
        
        self.enable_daily_summary_checkbox = QCheckBox("일일 요약 알림")
        self.enable_daily_summary_checkbox.setObjectName("checkbox-enable-daily-summary")
        self.enable_daily_summary_checkbox.setChecked(True)
        daily_summary_layout.addWidget(self.enable_daily_summary_checkbox)
        
        self.daily_summary_time = QTimeEdit()
        self.daily_summary_time.setObjectName("time-daily-summary")
        self.daily_summary_time.setTime(QTime(20, 0))  # 기본값: 저녁 8시
        self.daily_summary_time.setDisplayFormat("HH:mm")
        daily_summary_layout.addWidget(self.daily_summary_time)
        
        system_layout.addLayout(daily_summary_layout)
        
        # 시스템 알림 설명
        system_info = QLabel("* 오류 발생, 시스템 상태 변경 시 알림이 발생합니다.\n* 일일 요약 알림은 설정한 시간에 하루 동안의 거래 요약을 제공합니다.")
        system_info.setObjectName("label-system-info")
        system_info.setStyleSheet("color: #666666; font-size: 10px;")
        system_layout.addWidget(system_info)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)
        
        # 저장 버튼
        self.save_button = QPushButton("저장")
        self.save_button.setObjectName("button-save-notification-settings")
        button_layout.addWidget(self.save_button)
        
        # 초기화 버튼
        self.reset_button = QPushButton("초기화")
        self.reset_button.setObjectName("button-reset-notification-settings")
        button_layout.addWidget(self.reset_button)
        
        # 레이아웃 추가
        main_layout.addWidget(enable_group)
        main_layout.addWidget(price_group)
        main_layout.addWidget(trade_group)
        main_layout.addWidget(system_group)
        main_layout.addLayout(button_layout)
        main_layout.addStretch(1)
    
    def _connect_signals(self):
        """시그널 연결"""
        # 가격 알림 체크박스 변경 시 가격 알림 설정 그룹 활성화/비활성화
        self.enable_price_alerts_checkbox.stateChanged.connect(self._update_price_group_state)
        
        # 거래 알림 체크박스 변경 시 거래 알림 설정 그룹 활성화/비활성화
        self.enable_trade_alerts_checkbox.stateChanged.connect(self._update_trade_group_state)
        
        # 시스템 알림 체크박스 변경 시 시스템 알림 설정 그룹 활성화/비활성화
        self.enable_system_alerts_checkbox.stateChanged.connect(self._update_system_group_state)
        
        # 저장 버튼 클릭 시 설정 저장
        self.save_button.clicked.connect(self.save_settings)
        
        # 초기화 버튼 클릭 시 설정 초기화
        self.reset_button.clicked.connect(self._reset_settings)
    
    def _update_price_group_state(self, state):
        """가격 알림 설정 그룹 활성화/비활성화"""
        # 부모 위젯 찾기
        price_group = self.findChild(QGroupBox, "price-group")
        if price_group:
            price_group.setEnabled(state == Qt.CheckState.Checked.value)
    
    def _update_trade_group_state(self, state):
        """거래 알림 설정 그룹 활성화/비활성화"""
        # 부모 위젯 찾기
        trade_group = self.findChild(QGroupBox, "trade-group")
        if trade_group:
            trade_group.setEnabled(state == Qt.CheckState.Checked.value)
    
    def _update_system_group_state(self, state):
        """시스템 알림 설정 그룹 활성화/비활성화"""
        # 부모 위젯 찾기
        system_group = self.findChild(QGroupBox, "system-group")
        if system_group:
            system_group.setEnabled(state == Qt.CheckState.Checked.value)
    
    def _reset_settings(self):
        """설정 초기화"""
        # 알림 활성화 설정 초기화
        self.enable_price_alerts_checkbox.setChecked(True)
        self.enable_trade_alerts_checkbox.setChecked(True)
        self.enable_system_alerts_checkbox.setChecked(True)
        
        # 가격 알림 설정 초기화
        self.price_threshold_input.setValue(5)
        self.price_interval_combo.setCurrentIndex(1)  # 5분
        
        # 거래 알림 설정 초기화
        self.enable_order_executed_checkbox.setChecked(True)
        self.enable_profit_loss_checkbox.setChecked(True)
        self.enable_position_change_checkbox.setChecked(True)
        
        # 시스템 알림 설정 초기화
        self.enable_error_alerts_checkbox.setChecked(True)
        self.enable_system_status_checkbox.setChecked(True)
        self.enable_daily_summary_checkbox.setChecked(True)
        self.daily_summary_time.setTime(QTime(20, 0))  # 저녁 8시
    
    def load_settings(self):
        """설정 로드"""
        try:
            # 설정 파일 경로
            settings_dir = os.path.join(os.path.expanduser("~"), ".upbit_auto_trading")
            settings_path = os.path.join(settings_dir, "notification_settings.json")
            
            # 설정 파일이 없으면 기본 설정 사용
            if not os.path.exists(settings_path):
                self._reset_settings()
                return
            
            # 설정 파일 로드
            with open(settings_path, "r") as f:
                settings = json.load(f)
            
            # 알림 활성화 설정 적용
            if "enable_price_alerts" in settings:
                self.enable_price_alerts_checkbox.setChecked(settings["enable_price_alerts"])
            
            if "enable_trade_alerts" in settings:
                self.enable_trade_alerts_checkbox.setChecked(settings["enable_trade_alerts"])
            
            if "enable_system_alerts" in settings:
                self.enable_system_alerts_checkbox.setChecked(settings["enable_system_alerts"])
            
            # 가격 알림 설정 적용
            if "price_threshold" in settings:
                self.price_threshold_input.setValue(settings["price_threshold"])
            
            if "price_interval" in settings:
                index = self.price_interval_combo.findText(settings["price_interval"])
                if index >= 0:
                    self.price_interval_combo.setCurrentIndex(index)
            
            # 거래 알림 설정 적용
            if "enable_order_executed" in settings:
                self.enable_order_executed_checkbox.setChecked(settings["enable_order_executed"])
            
            if "enable_profit_loss" in settings:
                self.enable_profit_loss_checkbox.setChecked(settings["enable_profit_loss"])
            
            if "enable_position_change" in settings:
                self.enable_position_change_checkbox.setChecked(settings["enable_position_change"])
            
            # 시스템 알림 설정 적용
            if "enable_error_alerts" in settings:
                self.enable_error_alerts_checkbox.setChecked(settings["enable_error_alerts"])
            
            if "enable_system_status" in settings:
                self.enable_system_status_checkbox.setChecked(settings["enable_system_status"])
            
            if "enable_daily_summary" in settings:
                self.enable_daily_summary_checkbox.setChecked(settings["enable_daily_summary"])
            
            if "daily_summary_time" in settings:
                time_parts = settings["daily_summary_time"].split(":")
                if len(time_parts) == 2:
                    self.daily_summary_time.setTime(QTime(int(time_parts[0]), int(time_parts[1])))
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "설정 로드 오류",
                f"알림 설정을 로드하는 중 오류가 발생했습니다:\n{str(e)}"
            )
            
            # 오류 발생 시 기본 설정 사용
            self._reset_settings()
    
    def save_settings(self):
        """설정 저장"""
        try:
            # 설정 파일 경로
            settings_dir = os.path.join(os.path.expanduser("~"), ".upbit_auto_trading")
            settings_path = os.path.join(settings_dir, "notification_settings.json")
            
            # 디렉토리가 없으면 생성
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
            
            # 설정 저장
            settings = {
                # 알림 활성화 설정
                "enable_price_alerts": self.enable_price_alerts_checkbox.isChecked(),
                "enable_trade_alerts": self.enable_trade_alerts_checkbox.isChecked(),
                "enable_system_alerts": self.enable_system_alerts_checkbox.isChecked(),
                
                # 가격 알림 설정
                "price_threshold": self.price_threshold_input.value(),
                "price_interval": self.price_interval_combo.currentText(),
                
                # 거래 알림 설정
                "enable_order_executed": self.enable_order_executed_checkbox.isChecked(),
                "enable_profit_loss": self.enable_profit_loss_checkbox.isChecked(),
                "enable_position_change": self.enable_position_change_checkbox.isChecked(),
                
                # 시스템 알림 설정
                "enable_error_alerts": self.enable_error_alerts_checkbox.isChecked(),
                "enable_system_status": self.enable_system_status_checkbox.isChecked(),
                "enable_daily_summary": self.enable_daily_summary_checkbox.isChecked(),
                "daily_summary_time": self.daily_summary_time.time().toString("HH:mm")
            }
            
            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=4)
            
            QMessageBox.information(
                self,
                "저장 완료",
                "알림 설정이 저장되었습니다."
            )
            
            # 설정 변경 시그널 발생
            self.settings_changed.emit()
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "저장 오류",
                f"알림 설정을 저장하는 중 오류가 발생했습니다:\n{str(e)}"
            )