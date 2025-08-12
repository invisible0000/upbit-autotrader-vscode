"""
전략 이벤트 핸들러 구현
Strategy와 Trigger 도메인 이벤트를 처리하여 알림, 로깅, 캐시 무효화 등의 부수 효과를 처리합니다.
"""

from typing import Type

from ..notifications.notification_service import NotificationService, Notification, NotificationType, NotificationChannel
from .base_event_handler import BaseEventHandler
from ...domain.events.strategy_events import StrategyCreated, StrategyUpdated
from ...domain.events.trigger_events import TriggerCreated

class StrategyCreatedHandler(BaseEventHandler[StrategyCreated]):
    """전략 생성 이벤트 핸들러"""

    def __init__(self, notification_service: NotificationService):
        """
        핸들러 초기화

        Args:
            notification_service: 알림 서비스
        """
        super().__init__()
        self._notification_service = notification_service

    async def handle(self, event: StrategyCreated) -> None:
        """
        전략 생성 이벤트 처리

        Args:
            event: 전략 생성 이벤트
        """
        # 전략 생성 성공 알림
        notification = Notification(
            title="전략 생성 완료",
            message=f"'{event.strategy_name}' 전략이 성공적으로 생성되었습니다.",
            notification_type=NotificationType.SUCCESS,
            channels=[
                NotificationChannel.UI_TOAST,
                NotificationChannel.UI_STATUS_BAR,
                NotificationChannel.LOG_FILE
            ],
            metadata={
                "strategy_id": event.strategy_id,
                "strategy_name": event.strategy_name,
                "strategy_type": event.strategy_type,
                "created_by": event.created_by,
                "event_type": event.event_type
            }
        )

        try:
            await self._notification_service.send_notification(notification)
        except Exception as e:
            self._logger.warning(f"알림 전송 실패 (계속 진행): {e}")

        # 전략 목록 캐시 무효화 (향후 캐시 시스템과 연동)
        self._logger.info(f"전략 목록 캐시 무효화 필요: strategy_id={event.strategy_id}")

    def get_event_type(self) -> Type[StrategyCreated]:
        """
        처리할 이벤트 타입 반환

        Returns:
            이벤트 타입 클래스
        """
        return StrategyCreated

class StrategyUpdatedHandler(BaseEventHandler[StrategyUpdated]):
    """전략 수정 이벤트 핸들러"""

    def __init__(self, notification_service: NotificationService):
        """
        핸들러 초기화

        Args:
            notification_service: 알림 서비스
        """
        super().__init__()
        self._notification_service = notification_service

    async def handle(self, event: StrategyUpdated) -> None:
        """
        전략 수정 이벤트 처리

        Args:
            event: 전략 수정 이벤트
        """
        # 수정된 필드 정보 생성
        updated_fields_text = ", ".join(event.updated_fields.keys()) if event.updated_fields else "일반 수정"

        # 전략 수정 성공 알림
        notification = Notification(
            title="전략 수정 완료",
            message=f"'{event.strategy_name}' 전략이 수정되었습니다. (수정 항목: {updated_fields_text})",
            notification_type=NotificationType.INFO,
            channels=[
                NotificationChannel.UI_TOAST,
                NotificationChannel.UI_STATUS_BAR,
                NotificationChannel.LOG_FILE
            ],
            metadata={
                "strategy_id": event.strategy_id,
                "strategy_name": event.strategy_name,
                "updated_fields": event.updated_fields,
                "previous_version": event.previous_version,
                "new_version": event.new_version,
                "event_type": event.event_type
            }
        )

        await self._notification_service.send_notification(notification)

        # 전략 상세정보 캐시 무효화 (향후 캐시 시스템과 연동)
        self._logger.info(f"전략 상세정보 캐시 무효화 필요: strategy_id={event.strategy_id}")

    def get_event_type(self) -> Type[StrategyUpdated]:
        """
        처리할 이벤트 타입 반환

        Returns:
            이벤트 타입 클래스
        """
        return StrategyUpdated

class TriggerCreatedHandler(BaseEventHandler[TriggerCreated]):
    """트리거 생성 이벤트 핸들러"""

    def __init__(self, notification_service: NotificationService):
        """
        핸들러 초기화

        Args:
            notification_service: 알림 서비스
        """
        super().__init__()
        self._notification_service = notification_service

    async def handle(self, event: TriggerCreated) -> None:
        """
        트리거 생성 이벤트 처리

        Args:
            event: 트리거 생성 이벤트
        """
        # 조건 개수 계산
        conditions_count = len(event.trigger_conditions)

        # 트리거 생성 알림
        notification = Notification(
            title="트리거 생성 완료",
            message=f"'{event.trigger_name}' 트리거가 생성되었습니다. (조건 {conditions_count}개, {event.logic_operator} 연산)",
            notification_type=NotificationType.SUCCESS,
            channels=[
                NotificationChannel.UI_TOAST,
                NotificationChannel.LOG_FILE
            ],
            metadata={
                "trigger_id": event.trigger_id,
                "trigger_name": event.trigger_name,
                "strategy_id": event.strategy_id,
                "conditions_count": conditions_count,
                "logic_operator": event.logic_operator,
                "created_by": event.created_by,
                "event_type": event.event_type
            }
        )

        await self._notification_service.send_notification(notification)

        # 트리거 목록 캐시 무효화 (향후 캐시 시스템과 연동)
        self._logger.info(f"트리거 목록 캐시 무효화 필요: trigger_id={event.trigger_id}, strategy_id={event.strategy_id}")

    def get_event_type(self) -> Type[TriggerCreated]:
        """
        처리할 이벤트 타입 반환

        Returns:
            이벤트 타입 클래스
        """
        return TriggerCreated
