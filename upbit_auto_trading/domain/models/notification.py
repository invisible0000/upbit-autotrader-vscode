"""
Domain Layer - Notification Models
==================================

DDD(Domain Driven Design) 원칙에 따른 알림 도메인 모델
UI Layer에서 Domain Layer로 이동됨 (2025.08.10)

핵심 도메인 개념:
- Notification: 알림 도메인 엔터티
- NotificationType: 알림 유형 값 객체
- NotificationManager: 알림 도메인 서비스

이전 위치: upbit_auto_trading.ui.desktop.models.notification
현재 위치: upbit_auto_trading.domain.models.notification
"""

from enum import Enum, auto
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class NotificationType(Enum):
    """알림 유형 열거형 (Value Object)"""
    PRICE_ALERT = auto()  # 가격 알림
    TRADE_ALERT = auto()  # 거래 알림
    SYSTEM_ALERT = auto()  # 시스템 알림

@dataclass
class Notification:
    """알림 도메인 엔터티 (Domain Entity)"""
    id: int  # 알림 고유 ID
    type: NotificationType  # 알림 유형
    title: str  # 알림 제목
    message: str  # 알림 메시지
    timestamp: datetime  # 알림 발생 시간
    is_read: bool = False  # 읽음 상태
    related_symbol: Optional[str] = None  # 관련 코인 심볼 (없을 수 있음)

    def __post_init__(self):
        """초기화 후 처리"""
        # timestamp가 문자열로 전달된 경우 datetime으로 변환
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

    def to_dict(self) -> dict:
        """알림을 딕셔너리로 변환"""
        return {
            'id': self.id,
            'type': self.type.name,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read,
            'related_symbol': self.related_symbol
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Notification':
        """딕셔너리에서 알림 객체 생성"""
        return cls(
            id=data['id'],
            type=NotificationType[data['type']],
            title=data['title'],
            message=data['message'],
            timestamp=data['timestamp'],
            is_read=data['is_read'],
            related_symbol=data.get('related_symbol')
        )

    def get_formatted_time(self) -> str:
        """알림 시간을 포맷팅하여 반환"""
        now = datetime.now()
        delta = now - self.timestamp

        if delta.days > 0:
            return f"{delta.days}일 전"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600}시간 전"
        elif delta.seconds >= 60:
            return f"{delta.seconds // 60}분 전"
        else:
            return "방금 전"

class NotificationManager:
    """알림 도메인 서비스 (Domain Service)"""

    def __init__(self):
        """초기화"""
        self._notifications = []
        self._next_id = 1

    def add_notification(self, notification_type: NotificationType, title: str, message: str,
                         related_symbol: Optional[str] = None) -> Notification:
        """새 알림 추가"""
        notification = Notification(
            id=self._next_id,
            type=notification_type,
            title=title,
            message=message,
            timestamp=datetime.now(),
            is_read=False,
            related_symbol=related_symbol
        )
        self._notifications.append(notification)
        self._next_id += 1
        return notification

    def get_notifications(self, limit: Optional[int] = None,
                          notification_type: Optional[NotificationType] = None,
                          only_unread: bool = False) -> list[Notification]:
        """알림 목록 조회"""
        filtered = self._notifications

        # 유형 필터링
        if notification_type is not None:
            filtered = [n for n in filtered if n.type == notification_type]

        # 읽지 않은 알림만 필터링
        if only_unread:
            filtered = [n for n in filtered if not n.is_read]

        # 최신순 정렬
        filtered.sort(key=lambda n: n.timestamp, reverse=True)

        # 개수 제한
        if limit is not None:
            filtered = filtered[:limit]

        return filtered

    def mark_as_read(self, notification_id: int) -> bool:
        """알림을 읽음으로 표시"""
        for notification in self._notifications:
            if notification.id == notification_id:
                notification.is_read = True
                return True
        return False

    def mark_all_as_read(self) -> int:
        """모든 알림을 읽음으로 표시"""
        count = 0
        for notification in self._notifications:
            if not notification.is_read:
                notification.is_read = True
                count += 1
        return count

    def delete_notification(self, notification_id: int) -> bool:
        """알림 삭제"""
        for i, notification in enumerate(self._notifications):
            if notification.id == notification_id:
                del self._notifications[i]
                return True
        return False

    def clear_all_notifications(self) -> int:
        """모든 알림 삭제"""
        count = len(self._notifications)
        self._notifications.clear()
        return count

    def get_unread_count(self) -> int:
        """읽지 않은 알림 개수 반환"""
        return sum(1 for n in self._notifications if not n.is_read)
