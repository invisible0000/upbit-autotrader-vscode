"""
알림 센터 모듈

이 모듈은 알림 센터 화면을 구현합니다.
- 알림 목록 표시
- 알림 필터링
- 알림 관리 (읽음 표시, 삭제 등)
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSplitter, QToolBar, QStatusBar, QMenu
)
from PyQt6.QtGui import QIcon, QAction

from upbit_auto_trading.domain.models.notification import NotificationType
from .notification_list import NotificationList
from .notification_filter import NotificationFilter


class NotificationCenter(QMainWindow):
    """알림 센터 메인 윈도우"""

    # 알림 관련 시그널
    notification_read = pyqtSignal(int)  # 알림 읽음 (알림 ID)
    notification_deleted = pyqtSignal(int)  # 알림 삭제 (알림 ID)
    settings_changed = pyqtSignal(dict)  # 설정 변경 (설정 딕셔너리)

    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("notification-center")
        self.setWindowTitle("알림 센터")
        self.resize(800, 600)

        # 설정
        self.settings = {
            'enable_price_alerts': True,
            'enable_trade_alerts': True,
            'enable_system_alerts': True,
            'notification_sound': True,
            'desktop_notifications': True
        }

        # UI 설정
        self._setup_ui()

        # 시그널 연결
        self._connect_signals()

        # 초기 데이터 로드
        self._load_settings()

    def _setup_ui(self):
        """UI 설정"""
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 스플리터 (필터 + 알림 목록)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("notification-splitter")

        # 필터 패널
        self.notification_filter = NotificationFilter()
        splitter.addWidget(self.notification_filter)

        # 알림 목록 패널
        self.notification_list = NotificationList()
        splitter.addWidget(self.notification_list)

        # 스플리터 비율 설정
        splitter.setSizes([200, 600])  # 필터:알림 = 1:3 비율

        main_layout.addWidget(splitter)

        # 툴바 설정
        self._setup_toolbar()

        # 상태바 설정
        self._setup_statusbar()

    def _setup_toolbar(self):
        """툴바 설정"""
        toolbar = QToolBar("알림 센터 툴바")
        toolbar.setObjectName("notification-toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # 새로고침 액션
        refresh_action = QAction("새로고침", self)
        refresh_action.setObjectName("action-refresh")
        refresh_action.triggered.connect(self._on_refresh)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        # 모두 읽음 표시 액션
        mark_all_read_action = QAction("모두 읽음 표시", self)
        mark_all_read_action.setObjectName("action-mark-all-read")
        mark_all_read_action.triggered.connect(self._on_mark_all_read)
        toolbar.addAction(mark_all_read_action)

        # 모두 삭제 액션
        clear_all_action = QAction("모두 삭제", self)
        clear_all_action.setObjectName("action-clear-all")
        clear_all_action.triggered.connect(self._on_clear_all)
        toolbar.addAction(clear_all_action)

        toolbar.addSeparator()

        # 설정 액션
        settings_action = QAction("알림 설정", self)
        settings_action.setObjectName("action-settings")
        settings_action.triggered.connect(self._on_open_settings)
        toolbar.addAction(settings_action)

    def _setup_statusbar(self):
        """상태바 설정"""
        statusbar = QStatusBar()
        statusbar.setObjectName("notification-statusbar")
        self.setStatusBar(statusbar)

        # 알림 개수 표시 레이블
        self.status_label = QLabel()
        self.status_label.setObjectName("status-label")
        statusbar.addWidget(self.status_label)

        # 상태 업데이트
        self._update_status()

    def _connect_signals(self):
        """시그널 연결"""
        # 필터 변경 시그널
        self.notification_filter.filter_changed.connect(self._on_filter_changed)

        # 알림 작업 시그널
        self.notification_list.notification_read.connect(self._on_notification_read)
        self.notification_list.notification_deleted.connect(self._on_notification_deleted)

    def _load_settings(self):
        """설정 로드"""
        # 실제 구현에서는 설정 파일이나 데이터베이스에서 로드
        # 여기서는 기본값 사용
        pass

    def _update_status(self):
        """상태바 업데이트"""
        total_count = self.notification_list.get_notification_count()
        unread_count = self.notification_list.get_unread_count()

        status_text = f"총 {total_count}개 알림"
        if unread_count > 0:
            status_text += f" (읽지 않음: {unread_count}개)"

        self.status_label.setText(status_text)

    def _on_refresh(self):
        """새로고침 버튼 클릭 처리"""
        self.notification_list.load_notifications()
        self._update_status()

    def _on_mark_all_read(self):
        """모두 읽음 표시 버튼 클릭 처리"""
        self.notification_list.mark_all_as_read()
        self._update_status()

    def _on_clear_all(self):
        """모두 삭제 버튼 클릭 처리"""
        self.notification_list.clear_all_notifications()
        self._update_status()

    def _on_open_settings(self):
        """설정 버튼 클릭 처리"""
        # 실제 구현에서는 설정 대화상자 표시
        # 여기서는 간단히 상태바에 메시지 표시
        self.statusBar().showMessage("알림 설정 화면은 설정 메뉴에서 접근할 수 있습니다.", 3000)

    def _on_filter_changed(self, filters: dict):
        """필터 변경 처리"""
        # 필터 적용
        self.notification_list.filter_notifications(
            notification_type=filters['type'],
            only_unread=filters['read_status'] is False
        )

        # 상태 업데이트
        self._update_status()

    def _on_notification_read(self, notification_id: int):
        """알림 읽음 처리"""
        # 상태 업데이트
        self._update_status()

        # 시그널 발생
        self.notification_read.emit(notification_id)

    def _on_notification_deleted(self, notification_id: int):
        """알림 삭제 처리"""
        # 상태 업데이트
        self._update_status()

        # 시그널 발생
        self.notification_deleted.emit(notification_id)

    def update_settings(self, settings: Dict[str, Any]):
        """설정 업데이트"""
        self.settings.update(settings)
        self.settings_changed.emit(self.settings)

    def is_price_alert_enabled(self) -> bool:
        """가격 알림 활성화 여부 반환"""
        return self.settings.get('enable_price_alerts', True)

    def is_trade_alert_enabled(self) -> bool:
        """거래 알림 활성화 여부 반환"""
        return self.settings.get('enable_trade_alerts', True)

    def is_system_alert_enabled(self) -> bool:
        """시스템 알림 활성화 여부 반환"""
        return self.settings.get('enable_system_alerts', True)

    def add_notification(self, notification):
        """새 알림 추가"""
        # 알림 유형에 따른 활성화 여부 확인
        if notification.type == NotificationType.PRICE_ALERT and not self.is_price_alert_enabled():
            return
        elif notification.type == NotificationType.TRADE_ALERT and not self.is_trade_alert_enabled():
            return
        elif notification.type == NotificationType.SYSTEM_ALERT and not self.is_system_alert_enabled():
            return

        # 알림 목록에 추가
        self.notification_list.notifications.append(notification)
        self.notification_list._update_notification_widgets()

        # 상태 업데이트
        self._update_status()
