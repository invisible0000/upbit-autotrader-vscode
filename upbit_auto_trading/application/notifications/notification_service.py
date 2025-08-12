"""
Application Layer Notification 시스템

도메인 이벤트 처리의 부수 효과로 발생하는 다양한 형태의 알림을 통합 관리합니다.
UI 토스트, 상태 표시줄, 로그 파일, 시스템 알림 등 다양한 채널을 지원합니다.
"""

from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import uuid
import logging

class NotificationType(Enum):
    """알림 타입 분류"""
    SUCCESS = "success"    # 성공적 완료 (전략 생성, 백테스팅 성공 등)
    WARNING = "warning"    # 주의 필요 (성능 저하, 일부 실패 등)
    ERROR = "error"        # 오류 발생 (백테스팅 실패, 시스템 오류 등)
    INFO = "info"          # 일반 정보 (진행 상황, 상태 변경 등)

class NotificationChannel(Enum):
    """알림 전송 채널"""
    UI_TOAST = "ui_toast"                    # UI 토스트 메시지
    UI_STATUS_BAR = "ui_status_bar"          # UI 상태 표시줄
    LOG_FILE = "log_file"                    # 로그 파일 기록
    SYSTEM_NOTIFICATION = "system_notification"  # OS 시스템 알림

@dataclass
class Notification:
    """알림 메시지 데이터

    Args:
        id: 고유 식별자
        title: 알림 제목
        message: 알림 내용
        notification_type: 알림 타입 (성공/경고/오류/정보)
        channels: 전송할 채널 목록
        timestamp: 생성 시간
        metadata: 추가 메타데이터 (이벤트 ID, 관련 객체 정보 등)
        auto_dismiss_seconds: 자동 닫기 시간 (None이면 수동으로만 닫기)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    message: str = ""
    notification_type: NotificationType = NotificationType.INFO
    channels: List[NotificationChannel] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    auto_dismiss_seconds: Optional[int] = None

class NotificationService:
    """알림 관리 서비스

    다양한 채널을 통해 알림을 전송하고, 알림 히스토리를 관리합니다.
    각 채널별로 구독자를 등록할 수 있으며, 비동기로 알림을 전송합니다.
    """

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._subscribers: Dict[NotificationChannel, List[Callable]] = {}
        self._notification_history: List[Notification] = []
        self._max_history_size = 1000

    def subscribe(self, channel: NotificationChannel, callback: Callable) -> None:
        """채널별 알림 구독자 등록

        Args:
            channel: 구독할 알림 채널
            callback: 알림 수신 시 호출될 콜백 함수
                     sync/async 함수 모두 지원
        """
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(callback)

        self._logger.debug(f"알림 구독자 등록: {channel.value}")

    def unsubscribe(self, channel: NotificationChannel, callback: Callable) -> None:
        """구독 해제

        Args:
            channel: 구독 해제할 채널
            callback: 해제할 콜백 함수
        """
        if channel in self._subscribers:
            try:
                self._subscribers[channel].remove(callback)
                self._logger.debug(f"알림 구독자 해제: {channel.value}")
            except ValueError:
                self._logger.warning(f"구독자를 찾을 수 없음: {channel.value}")

    async def send_notification(self, notification: Notification) -> None:
        """알림 발송

        Args:
            notification: 발송할 알림 데이터

        Note:
            - 히스토리에 저장 후 모든 채널의 구독자들에게 병렬 전송
            - 개별 구독자 전송 실패는 전체 시스템에 영향을 주지 않음
        """
        # 히스토리에 추가
        self._add_to_history(notification)

        # 각 채널의 구독자들에게 알림 전송
        tasks = []
        for channel in notification.channels:
            if channel in self._subscribers:
                for callback in self._subscribers[channel]:
                    tasks.append(self._send_to_subscriber(callback, notification))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 실패한 전송 건수 로깅
            failed_count = sum(1 for result in results if isinstance(result, Exception))
            if failed_count > 0:
                self._logger.warning(f"알림 전송 일부 실패: {failed_count}/{len(tasks)}건")

        self._logger.info(f"알림 발송 완료: {notification.title} ({len(notification.channels)}개 채널)")

    async def _send_to_subscriber(self, callback: Callable, notification: Notification) -> None:
        """개별 구독자에게 알림 전송

        Args:
            callback: 호출할 콜백 함수
            notification: 전송할 알림

        Note:
            동기/비동기 콜백 모두 지원하며, 예외 발생 시 격리 처리
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(notification)
            else:
                callback(notification)
        except Exception as e:
            # 알림 전송 실패는 전체 시스템에 영향주지 않도록 처리
            self._logger.error(f"⚠️ 알림 전송 실패: {e}")

    def _add_to_history(self, notification: Notification) -> None:
        """알림 히스토리에 추가

        Args:
            notification: 히스토리에 추가할 알림
        """
        self._notification_history.append(notification)

        # 히스토리 크기 제한
        if len(self._notification_history) > self._max_history_size:
            removed_count = len(self._notification_history) - self._max_history_size
            self._notification_history = self._notification_history[-self._max_history_size:]
            self._logger.debug(f"알림 히스토리 정리: {removed_count}개 제거")

    def get_recent_notifications(self, limit: int = 50) -> List[Notification]:
        """최근 알림 목록 조회

        Args:
            limit: 조회할 최대 알림 수

        Returns:
            List[Notification]: 최근 알림 목록 (최신순)
        """
        return self._notification_history[-limit:]

    def get_notifications_by_type(self, notification_type: NotificationType,
                                  limit: int = 50) -> List[Notification]:
        """타입별 알림 목록 조회

        Args:
            notification_type: 조회할 알림 타입
            limit: 조회할 최대 알림 수

        Returns:
            List[Notification]: 해당 타입의 알림 목록
        """
        filtered = [n for n in self._notification_history
                    if n.notification_type == notification_type]
        return filtered[-limit:]

    def clear_notifications(self) -> None:
        """알림 히스토리 초기화"""
        cleared_count = len(self._notification_history)
        self._notification_history.clear()
        self._logger.info(f"알림 히스토리 초기화: {cleared_count}개 알림 삭제")

    def get_subscriber_count(self) -> Dict[str, int]:
        """채널별 구독자 수 조회

        Returns:
            Dict[str, int]: 채널명과 구독자 수 매핑
        """
        return {
            channel.value: len(callbacks)
            for channel, callbacks in self._subscribers.items()
        }

    def create_notification(self, title: str, message: str,
                            notification_type: NotificationType = NotificationType.INFO,
                            channels: Optional[List[NotificationChannel]] = None,
                            metadata: Optional[Dict[str, Any]] = None,
                            auto_dismiss_seconds: Optional[int] = None) -> Notification:
        """알림 생성 헬퍼 메소드

        Args:
            title: 알림 제목
            message: 알림 내용
            notification_type: 알림 타입
            channels: 전송 채널 목록 (기본값: UI_TOAST)
            metadata: 추가 메타데이터
            auto_dismiss_seconds: 자동 닫기 시간

        Returns:
            Notification: 생성된 알림 객체
        """
        if channels is None:
            channels = [NotificationChannel.UI_TOAST]

        return Notification(
            title=title,
            message=message,
            notification_type=notification_type,
            channels=channels,
            metadata=metadata or {},
            auto_dismiss_seconds=auto_dismiss_seconds
        )
