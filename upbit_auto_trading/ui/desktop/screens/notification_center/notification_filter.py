"""
알림 필터 모듈

이 모듈은 알림 필터 기능을 구현합니다.
- 알림 유형별 필터링
- 읽음/읽지 않음 상태별 필터링
- 날짜별 필터링
"""

from typing import Optional, Callable
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QGroupBox, QRadioButton, QButtonGroup
)

from upbit_auto_trading.domain.models.notification import NotificationType

class NotificationFilter(QWidget):
    """알림 필터 위젯"""

    # 필터 변경 시그널
    filter_changed = pyqtSignal(dict)  # 필터 설정 (딕셔너리)

    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("notification-filter")

        # 필터 상태
        self.current_filters = {
            'type': None,  # 알림 유형
            'read_status': None,  # 읽음 상태
            'time_range': None,  # 시간 범위
        }

        # UI 설정
        self._setup_ui()

    def _setup_ui(self):
        """UI 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # 필터 제목
        title_label = QLabel("알림 필터")
        title_label.setObjectName("filter-title")
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(12)
        title_label.setFont(font)
        main_layout.addWidget(title_label)

        # 알림 유형 필터
        type_group = QGroupBox("알림 유형")
        type_group.setObjectName("filter-type-group")
        type_layout = QVBoxLayout(type_group)

        # 모든 알림 라디오 버튼
        self.radio_all = QRadioButton("모든 알림")
        self.radio_all.setObjectName("radio-all")
        self.radio_all.setChecked(True)
        type_layout.addWidget(self.radio_all)

        # 가격 알림 라디오 버튼
        self.radio_price = QRadioButton("가격 알림")
        self.radio_price.setObjectName("radio-price")
        type_layout.addWidget(self.radio_price)

        # 거래 알림 라디오 버튼
        self.radio_trade = QRadioButton("거래 알림")
        self.radio_trade.setObjectName("radio-trade")
        type_layout.addWidget(self.radio_trade)

        # 시스템 알림 라디오 버튼
        self.radio_system = QRadioButton("시스템 알림")
        self.radio_system.setObjectName("radio-system")
        type_layout.addWidget(self.radio_system)

        # 라디오 버튼 그룹 설정
        self.type_button_group = QButtonGroup(self)
        self.type_button_group.addButton(self.radio_all, 0)
        self.type_button_group.addButton(self.radio_price, 1)
        self.type_button_group.addButton(self.radio_trade, 2)
        self.type_button_group.addButton(self.radio_system, 3)
        self.type_button_group.buttonClicked.connect(self._on_type_filter_changed)

        main_layout.addWidget(type_group)

        # 읽음 상태 필터
        status_group = QGroupBox("읽음 상태")
        status_group.setObjectName("filter-status-group")
        status_layout = QVBoxLayout(status_group)

        # 모든 알림 라디오 버튼
        self.radio_status_all = QRadioButton("모든 알림")
        self.radio_status_all.setObjectName("radio-status-all")
        self.radio_status_all.setChecked(True)
        status_layout.addWidget(self.radio_status_all)

        # 읽지 않은 알림 라디오 버튼
        self.radio_unread = QRadioButton("읽지 않은 알림")
        self.radio_unread.setObjectName("radio-unread")
        status_layout.addWidget(self.radio_unread)

        # 읽은 알림 라디오 버튼
        self.radio_read = QRadioButton("읽은 알림")
        self.radio_read.setObjectName("radio-read")
        status_layout.addWidget(self.radio_read)

        # 라디오 버튼 그룹 설정
        self.status_button_group = QButtonGroup(self)
        self.status_button_group.addButton(self.radio_status_all, 0)
        self.status_button_group.addButton(self.radio_unread, 1)
        self.status_button_group.addButton(self.radio_read, 2)
        self.status_button_group.buttonClicked.connect(self._on_status_filter_changed)

        main_layout.addWidget(status_group)

        # 시간 범위 필터
        time_group = QGroupBox("시간 범위")
        time_group.setObjectName("filter-time-group")
        time_layout = QVBoxLayout(time_group)

        # 모든 기간 라디오 버튼
        self.radio_time_all = QRadioButton("모든 기간")
        self.radio_time_all.setObjectName("radio-time-all")
        self.radio_time_all.setChecked(True)
        time_layout.addWidget(self.radio_time_all)

        # 오늘 라디오 버튼
        self.radio_today = QRadioButton("오늘")
        self.radio_today.setObjectName("radio-today")
        time_layout.addWidget(self.radio_today)

        # 지난 7일 라디오 버튼
        self.radio_week = QRadioButton("지난 7일")
        self.radio_week.setObjectName("radio-week")
        time_layout.addWidget(self.radio_week)

        # 지난 30일 라디오 버튼
        self.radio_month = QRadioButton("지난 30일")
        self.radio_month.setObjectName("radio-month")
        time_layout.addWidget(self.radio_month)

        # 라디오 버튼 그룹 설정
        self.time_button_group = QButtonGroup(self)
        self.time_button_group.addButton(self.radio_time_all, 0)
        self.time_button_group.addButton(self.radio_today, 1)
        self.time_button_group.addButton(self.radio_week, 2)
        self.time_button_group.addButton(self.radio_month, 3)
        self.time_button_group.buttonClicked.connect(self._on_time_filter_changed)

        main_layout.addWidget(time_group)

        # 필터 초기화 버튼
        reset_button = QPushButton("필터 초기화")
        reset_button.setObjectName("btn-reset-filter")
        reset_button.clicked.connect(self.reset_filters)
        main_layout.addWidget(reset_button)

        # 빈 공간 추가
        main_layout.addStretch(1)

    def _on_type_filter_changed(self, button):
        """알림 유형 필터 변경 처리"""
        button_id = self.type_button_group.id(button)

        if button_id == 0:  # 모든 알림
            self.current_filters['type'] = None
        elif button_id == 1:  # 가격 알림
            self.current_filters['type'] = NotificationType.PRICE_ALERT
        elif button_id == 2:  # 거래 알림
            self.current_filters['type'] = NotificationType.TRADE_ALERT
        elif button_id == 3:  # 시스템 알림
            self.current_filters['type'] = NotificationType.SYSTEM_ALERT

        self.filter_changed.emit(self.current_filters)

    def _on_status_filter_changed(self, button):
        """읽음 상태 필터 변경 처리"""
        button_id = self.status_button_group.id(button)

        if button_id == 0:  # 모든 알림
            self.current_filters['read_status'] = None
        elif button_id == 1:  # 읽지 않은 알림
            self.current_filters['read_status'] = False
        elif button_id == 2:  # 읽은 알림
            self.current_filters['read_status'] = True

        self.filter_changed.emit(self.current_filters)

    def _on_time_filter_changed(self, button):
        """시간 범위 필터 변경 처리"""
        button_id = self.time_button_group.id(button)
        now = datetime.now()

        if button_id == 0:  # 모든 기간
            self.current_filters['time_range'] = None
        elif button_id == 1:  # 오늘
            today_start = datetime(now.year, now.month, now.day)
            self.current_filters['time_range'] = today_start
        elif button_id == 2:  # 지난 7일
            week_ago = now - timedelta(days=7)
            self.current_filters['time_range'] = week_ago
        elif button_id == 3:  # 지난 30일
            month_ago = now - timedelta(days=30)
            self.current_filters['time_range'] = month_ago

        self.filter_changed.emit(self.current_filters)

    def reset_filters(self):
        """모든 필터 초기화"""
        # 필터 상태 초기화
        self.current_filters = {
            'type': None,
            'read_status': None,
            'time_range': None,
        }

        # UI 상태 초기화
        self.radio_all.setChecked(True)
        self.radio_status_all.setChecked(True)
        self.radio_time_all.setChecked(True)

        # 필터 변경 시그널 발생
        self.filter_changed.emit(self.current_filters)

    def filter_by_type(self, notification_type: Optional[NotificationType]):
        """알림 유형으로 필터링"""
        if notification_type is None:
            self.radio_all.setChecked(True)
        elif notification_type == NotificationType.PRICE_ALERT:
            self.radio_price.setChecked(True)
        elif notification_type == NotificationType.TRADE_ALERT:
            self.radio_trade.setChecked(True)
        elif notification_type == NotificationType.SYSTEM_ALERT:
            self.radio_system.setChecked(True)

        self.current_filters['type'] = notification_type

        # 테스트를 위한 디버그 출력
        print(f"필터 유형 변경: {notification_type}")

        # 필터 변경 시그널 발생
        self.filter_changed.emit(self.current_filters)

    def filter_by_read_status(self, is_read: Optional[bool]):
        """읽음 상태로 필터링"""
        if is_read is None:
            self.radio_status_all.setChecked(True)
        elif is_read is False:
            self.radio_unread.setChecked(True)
        elif is_read is True:
            self.radio_read.setChecked(True)

        self.current_filters['read_status'] = is_read
        self.filter_changed.emit(self.current_filters)

    def filter_by_time_range(self, time_range: Optional[datetime]):
        """시간 범위로 필터링"""
        now = datetime.now()

        if time_range is None:
            self.radio_time_all.setChecked(True)
        elif time_range.date() == now.date():
            self.radio_today.setChecked(True)
        elif (now - time_range).days <= 7:
            self.radio_week.setChecked(True)
        elif (now - time_range).days <= 30:
            self.radio_month.setChecked(True)
        else:
            # 범위를 벗어나는 경우 모든 기간으로 설정
            self.radio_time_all.setChecked(True)
            time_range = None

        self.current_filters['time_range'] = time_range
        self.filter_changed.emit(self.current_filters)

    def get_current_filters(self) -> dict:
        """현재 필터 설정 반환"""
        return self.current_filters.copy()
