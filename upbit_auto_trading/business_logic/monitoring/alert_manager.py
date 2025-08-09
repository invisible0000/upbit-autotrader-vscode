"""
알림 관리자 모듈

이 모듈은 알림 생성 및 관리 기능을 제공합니다.
- 알림 생성
- 알림 목록 관리
- 알림 상태 관리
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from upbit_auto_trading.domain.models.notification import Notification, NotificationType


class AlertManager:
    """알림 관리자 클래스"""

    def __init__(self):
        """초기화"""
        self._notifications = []
        self._next_id = 1
        self._notification_handlers = []

    def add_notification(self, notification_type: NotificationType, title: str, message: str,
                         related_symbol: Optional[str] = None) -> Notification:
        """새 알림 추가

        Args:
            notification_type: 알림 유형
            title: 알림 제목
            message: 알림 메시지
            related_symbol: 관련 코인 심볼 (없을 수 있음)

        Returns:
            Notification: 생성된 알림 객체
        """
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

        # 알림 핸들러 호출
        for handler in self._notification_handlers:
            handler(notification)

        return notification

    def register_notification_handler(self, handler):
        """알림 핸들러 등록

        Args:
            handler: 알림 발생 시 호출할 콜백 함수
        """
        if handler not in self._notification_handlers:
            self._notification_handlers.append(handler)

    def unregister_notification_handler(self, handler):
        """알림 핸들러 등록 해제

        Args:
            handler: 등록 해제할 콜백 함수
        """
        if handler in self._notification_handlers:
            self._notification_handlers.remove(handler)

    def get_notifications(self, limit: Optional[int] = None,
                          notification_type: Optional[NotificationType] = None,
                          only_unread: bool = False) -> List[Notification]:
        """알림 목록 조회

        Args:
            limit: 최대 알림 개수 (None이면 모든 알림)
            notification_type: 알림 유형 필터 (None이면 모든 유형)
            only_unread: 읽지 않은 알림만 조회할지 여부

        Returns:
            List[Notification]: 알림 목록
        """
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
        """알림을 읽음으로 표시

        Args:
            notification_id: 알림 ID

        Returns:
            bool: 성공 여부
        """
        for notification in self._notifications:
            if notification.id == notification_id:
                notification.is_read = True
                return True
        return False

    def mark_all_as_read(self) -> int:
        """모든 알림을 읽음으로 표시

        Returns:
            int: 읽음으로 표시된 알림 개수
        """
        count = 0
        for notification in self._notifications:
            if not notification.is_read:
                notification.is_read = True
                count += 1
        return count

    def delete_notification(self, notification_id: int) -> bool:
        """알림 삭제

        Args:
            notification_id: 알림 ID

        Returns:
            bool: 성공 여부
        """
        for i, notification in enumerate(self._notifications):
            if notification.id == notification_id:
                del self._notifications[i]
                return True
        return False

    def clear_all_notifications(self) -> int:
        """모든 알림 삭제

        Returns:
            int: 삭제된 알림 개수
        """
        count = len(self._notifications)
        self._notifications.clear()
        return count

    def get_unread_count(self) -> int:
        """읽지 않은 알림 개수 반환

        Returns:
            int: 읽지 않은 알림 개수
        """
        return sum(1 for n in self._notifications if not n.is_read)

    def save_notifications(self, file_path: str) -> bool:
        """알림 목록 저장

        Args:
            file_path: 저장할 파일 경로

        Returns:
            bool: 성공 여부
        """
        try:
            # 디렉토리 생성
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 알림 목록을 딕셔너리 목록으로 변환
            notifications_data = [n.to_dict() for n in self._notifications]

            # JSON 파일로 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "next_id": self._next_id,
                    "notifications": notifications_data
                }, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"알림 목록 저장 중 오류 발생: {e}")
            return False

    def load_notifications(self, file_path: str) -> bool:
        """알림 목록 로드

        Args:
            file_path: 로드할 파일 경로

        Returns:
            bool: 성공 여부
        """
        try:
            if not os.path.exists(file_path):
                return False

            # JSON 파일에서 로드
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 알림 목록 설정
            self._next_id = data.get("next_id", 1)
            self._notifications = [Notification.from_dict(n) for n in data.get("notifications", [])]

            return True
        except Exception as e:
            print(f"알림 목록 로드 중 오류 발생: {e}")
            return False
