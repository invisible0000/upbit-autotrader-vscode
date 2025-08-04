"""
도메인 이벤트 시스템 - 기본 클래스
Domain-Driven Design을 기반으로 한 이벤트 기반 아키텍처 구현
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Callable
import uuid
from upbit_auto_trading.logging import get_integrated_logger

# 새로운 분리된 DomainEventPublisher를 import
from .domain_event_publisher import (
    DomainEventPublisher,
    get_domain_event_publisher,
    reset_domain_event_publisher
)

# dataclass 기반 DomainEvent를 기본으로 사용
from .base_domain_event import DomainEvent

logger = get_integrated_logger("DomainEvent")


# 편의 함수들 (하위 호환성 유지)
def publish_domain_event(event: DomainEvent) -> None:
    """
    도메인 이벤트 발행 편의 함수

    Args:
        event: 발행할 도메인 이벤트
    """
    publisher = get_domain_event_publisher()
    publisher.publish(event)


def subscribe_to_domain_event(event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
    """
    도메인 이벤트 구독 편의 함수

    Args:
        event_type: 구독할 이벤트 타입
        handler: 이벤트 처리 함수
    """
    publisher = get_domain_event_publisher()
    publisher.subscribe(event_type, handler)
