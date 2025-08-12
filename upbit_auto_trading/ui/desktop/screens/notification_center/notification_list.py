"""
알림 목록 모듈

이 모듈은 알림 목록 화면을 구현합니다.
- 알림 목록 표시
- 알림 읽음 표시
- 알림 삭제
"""

import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QMenu
)
from PyQt6.QtGui import QIcon, QAction, QColor, QPalette

from upbit_auto_trading.domain.models.notification import Notification, NotificationType

class NotificationItem(QFrame):
    """알림 항목 위젯"""

    # 알림 작업 시그널
    mark_as_read_signal = pyqtSignal(int)  # 읽음 표시 (알림 ID)
    delete_signal = pyqtSignal(int)  # 삭제 (알림 ID)

    def __init__(self, notification: Notification, parent=None):
        """초기화"""
        super().__init__(parent)
        self.notification = notification
        self.setObjectName(f"notification-item-{notification.id}")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(80)

        # 읽음 상태에 따른 스타일 설정
        self._update_style()

        # 레이아웃 설정
        self._setup_ui()

    def _setup_ui(self):
        """UI 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # 상단 레이아웃 (제목 + 시간)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        # 알림 유형에 따른 아이콘 설정
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        if self.notification.type == NotificationType.PRICE_ALERT:
            icon_label.setText("💰")  # 가격 알림 아이콘
        elif self.notification.type == NotificationType.TRADE_ALERT:
            icon_label.setText("🔄")  # 거래 알림 아이콘
        elif self.notification.type == NotificationType.SYSTEM_ALERT:
            icon_label.setText("⚙️")  # 시스템 알림 아이콘
        top_layout.addWidget(icon_label)

        # 제목
        title_label = QLabel(self.notification.title)
        title_label.setObjectName("notification-title")
        font = title_label.font()
        font.setBold(True)
        title_label.setFont(font)
        top_layout.addWidget(title_label, 1)

        # 시간
        time_label = QLabel(self.notification.get_formatted_time())
        time_label.setObjectName("notification-time")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(time_label)

        main_layout.addLayout(top_layout)

        # 메시지
        message_label = QLabel(self.notification.message)
        message_label.setObjectName("notification-message")
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)

        # 하단 레이아웃 (관련 코인 + 작업 버튼)
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        # 관련 코인 정보
        if self.notification.related_symbol:
            symbol_label = QLabel(self.notification.related_symbol)
            symbol_label.setObjectName("notification-symbol")
            bottom_layout.addWidget(symbol_label)

        # 빈 공간
        bottom_layout.addStretch(1)

        # 작업 버튼
        if not self.notification.is_read:
            read_button = QPushButton("읽음")
            read_button.setObjectName("btn-mark-read")
            read_button.setFixedSize(60, 24)
            read_button.clicked.connect(self._on_mark_as_read)
            bottom_layout.addWidget(read_button)

        delete_button = QPushButton("삭제")
        delete_button.setObjectName("btn-delete")
        delete_button.setFixedSize(60, 24)
        delete_button.clicked.connect(self._on_delete)
        bottom_layout.addWidget(delete_button)

        main_layout.addLayout(bottom_layout)

    def _update_style(self):
        """읽음 상태에 따른 스타일 업데이트"""
        if not self.notification.is_read:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 120, 215, 0.1);
                    border: 1px solid rgba(0, 120, 215, 0.3);
                    border-radius: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(200, 200, 200, 0.1);
                    border: 1px solid rgba(200, 200, 200, 0.3);
                    border-radius: 5px;
                }
            """)

    def _on_mark_as_read(self):
        """읽음 표시 버튼 클릭 처리"""
        self.mark_as_read_signal.emit(self.notification.id)

    def _on_delete(self):
        """삭제 버튼 클릭 처리"""
        self.delete_signal.emit(self.notification.id)

    def update_notification(self, notification: Notification):
        """알림 정보 업데이트"""
        self.notification = notification
        self._update_style()
        # UI 요소 업데이트 필요 (재구성)
        # 간단한 구현을 위해 위젯을 다시 생성하는 방식으로 처리
        # 실제 구현에서는 각 위젯의 내용만 업데이트하는 것이 효율적
        self.deleteLater()
        self.__init__(notification, self.parent())

class NotificationList(QScrollArea):
    """알림 목록 위젯"""

    # 알림 작업 시그널
    notification_read = pyqtSignal(int)  # 알림 읽음 (알림 ID)
    notification_deleted = pyqtSignal(int)  # 알림 삭제 (알림 ID)

    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("notification-list")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 내부 위젯 및 레이아웃 설정
        self.container = QWidget()
        self.container.setObjectName("notification-container")
        self.setWidget(self.container)

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.layout.addStretch(1)  # 항목이 위에서부터 채워지도록 빈 공간 추가

        # 알림 목록
        self.notifications: List[Notification] = []
        self.notification_widgets: List[NotificationItem] = []

        # 초기 알림 로드
        self.load_notifications()

    def load_notifications(self) -> List[Notification]:
        """알림 목록 로드"""
        # 실제 구현에서는 데이터베이스나 파일에서 알림을 로드
        # 여기서는 테스트를 위한 더미 데이터 반환

        # 기존 알림 위젯 제거
        for widget in self.notification_widgets:
            widget.deleteLater()
        self.notification_widgets.clear()

        # 더미 데이터 생성 (실제 구현에서는 DB에서 로드)
        self.notifications = [
            Notification(
                id=1,
                type=NotificationType.PRICE_ALERT,
                title="가격 알림",
                message="BTC 가격이 50,000,000원을 초과했습니다.",
                timestamp=datetime.now(),
                is_read=False,
                related_symbol="KRW-BTC"
            ),
            Notification(
                id=2,
                type=NotificationType.TRADE_ALERT,
                title="거래 알림",
                message="BTC 매수 주문이 체결되었습니다.",
                timestamp=datetime.now(),
                is_read=True,
                related_symbol="KRW-BTC"
            ),
            Notification(
                id=3,
                type=NotificationType.SYSTEM_ALERT,
                title="시스템 알림",
                message="데이터베이스 연결이 복구되었습니다.",
                timestamp=datetime.now(),
                is_read=False,
                related_symbol=None
            )
        ]

        # 알림 위젯 생성 및 추가
        self._update_notification_widgets()

        return self.notifications

    def _update_notification_widgets(self):
        """알림 위젯 업데이트"""
        # 기존 위젯 제거
        for widget in self.notification_widgets:
            self.layout.removeWidget(widget)
            widget.deleteLater()
        self.notification_widgets.clear()

        # 새 위젯 생성 및 추가
        for notification in self.notifications:
            item = NotificationItem(notification)
            item.mark_as_read_signal.connect(self.mark_as_read)
            item.delete_signal.connect(self.delete_notification)

            # 레이아웃의 마지막 항목(stretch) 앞에 위젯 추가
            self.layout.insertWidget(self.layout.count() - 1, item)
            self.notification_widgets.append(item)

    def filter_notifications(self, notification_type: Optional[NotificationType] = None,
                            only_unread: bool = False):
        """알림 필터링"""
        # 원본 알림 목록 백업 (테스트용)
        original_notifications = self.notifications.copy()
        filtered = original_notifications

        # 유형 필터링
        if notification_type is not None:
            filtered = [n for n in filtered if n.type == notification_type]
            print(f"유형 필터링 후 알림 개수: {len(filtered)}")

        # 읽지 않은 알림만 필터링
        if only_unread:
            filtered = [n for n in filtered if not n.is_read]
            print(f"읽지 않은 알림 필터링 후 알림 개수: {len(filtered)}")

        # 필터링된 알림으로 위젯 업데이트
        self.notifications = filtered
        self._update_notification_widgets()

    def mark_as_read(self, notification_id: int):
        """알림을 읽음으로 표시"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.is_read = True
                self._update_notification_widgets()
                self.notification_read.emit(notification_id)
                break

        # 테스트를 위한 디버그 출력
        print(f"알림 {notification_id}를 읽음으로 표시합니다. 현재 상태: {notification.is_read}")

    def mark_all_as_read(self):
        """모든 알림을 읽음으로 표시"""
        for notification in self.notifications:
            notification.is_read = True
        self._update_notification_widgets()

    def delete_notification(self, notification_id: int):
        """알림 삭제"""
        for i, notification in enumerate(self.notifications):
            if notification.id == notification_id:
                del self.notifications[i]
                self._update_notification_widgets()
                self.notification_deleted.emit(notification_id)
                break

    def clear_all_notifications(self):
        """모든 알림 삭제"""
        self.notifications.clear()
        self._update_notification_widgets()

    def get_notification_count(self) -> int:
        """알림 개수 반환"""
        return len(self.notifications)

    def get_unread_count(self) -> int:
        """읽지 않은 알림 개수 반환"""
        return sum(1 for n in self.notifications if not n.is_read)

    def get_notification(self, index: int) -> Optional[Notification]:
        """인덱스로 알림 조회"""
        if 0 <= index < len(self.notifications):
            return self.notifications[index]
        return None
