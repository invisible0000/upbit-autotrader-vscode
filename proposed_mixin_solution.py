from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


class DomainEventMixin:
    """도메인 이벤트 공통 기능을 제공하는 Mixin"""

    def __post_init__(self):
        """이벤트 생성 후 공통 필드 초기화"""
        if not hasattr(self, '_event_id'):
            object.__setattr__(self, '_event_id', str(uuid.uuid4()))
        if not hasattr(self, '_occurred_at'):
            object.__setattr__(self, '_occurred_at', datetime.now())
        if not hasattr(self, '_version'):
            object.__setattr__(self, '_version', 1)
        if not hasattr(self, '_correlation_id'):
            object.__setattr__(self, '_correlation_id', self._event_id)
        if not hasattr(self, '_causation_id'):
            object.__setattr__(self, '_causation_id', None)
        if not hasattr(self, '_metadata'):
            object.__setattr__(self, '_metadata', {})

    @property
    def event_id(self) -> str:
        return getattr(self, '_event_id', str(uuid.uuid4()))

    @property
    def occurred_at(self) -> datetime:
        return getattr(self, '_occurred_at', datetime.now())

    @property
    def version(self) -> int:
        return getattr(self, '_version', 1)

    @property
    def correlation_id(self) -> Optional[str]:
        return getattr(self, '_correlation_id', self.event_id)

    @property
    def causation_id(self) -> Optional[str]:
        return getattr(self, '_causation_id', None)

    @property
    def metadata(self) -> Dict[str, Any]:
        return getattr(self, '_metadata', {})

    @property
    @abstractmethod
    def event_type(self) -> str:
        """이벤트 타입 (하위 클래스에서 구현)"""
        pass

    @property
    @abstractmethod
    def aggregate_id(self) -> str:
        """집계 ID (하위 클래스에서 구현)"""
        pass

    def add_metadata(self, key: str, value: Any) -> None:
        """메타데이터 추가"""
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """이벤트를 딕셔너리로 변환"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "version": self.version,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "metadata": self.metadata,
            "data": self._get_event_data()
        }

    def _get_event_data(self) -> Dict[str, Any]:
        """이벤트별 고유 데이터 반환"""
        excluded_fields = {"_event_id", "_occurred_at", "_version", "_correlation_id", "_causation_id", "_metadata"}
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_') or key not in excluded_fields
        }


# DomainEvent는 이제 추상 기본 클래스만 역할
class DomainEvent(DomainEventMixin, ABC):
    """도메인 이벤트 추상 기본 클래스"""
    pass


# 사용 예시
@dataclass(frozen=True)
class StrategyCreated(DomainEvent):
    """전략 생성 이벤트 - 필수 필드들을 자유롭게 정의 가능"""
    strategy_id: str          # 필수 필드 (기본값 없음)
    strategy_name: str        # 필수 필드 (기본값 없음)
    strategy_type: str = "entry"  # 기본값 있는 필드
    creator_id: Optional[str] = None  # 선택적 필드

    @property
    def event_type(self) -> str:
        return "strategy.created"

    @property
    def aggregate_id(self) -> str:
        return self.strategy_id
