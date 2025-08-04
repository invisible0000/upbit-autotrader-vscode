"""
Base Application Service - 모든 Application Service의 기본 클래스
"""

from abc import ABC
from typing import TypeVar, Generic
from upbit_auto_trading.domain.events.domain_event_publisher import get_domain_event_publisher

T = TypeVar('T')


class BaseApplicationService(ABC, Generic[T]):
    """모든 Application Service의 기본 클래스

    Application Service는 Use Case를 구현하며, 다음 책임을 가집니다:
    1. Use Case 조정 (Domain Entity들 간의 협력)
    2. 트랜잭션 경계 관리
    3. 도메인 이벤트 발행
    4. 입력 데이터 검증 (Command 객체를 통해)
    """

    def __init__(self):
        self._event_publisher = get_domain_event_publisher()

    def _publish_domain_events(self, entity) -> None:
        """엔티티의 도메인 이벤트들을 발행

        Args:
            entity: 도메인 이벤트를 가진 엔티티
        """
        if hasattr(entity, 'get_domain_events'):
            events = entity.get_domain_events()
            for event in events:
                self._event_publisher.publish(event)
            entity.clear_domain_events()
