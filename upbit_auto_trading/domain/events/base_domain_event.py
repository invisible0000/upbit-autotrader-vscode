from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DomainEvent(ABC):
    """
    모든 도메인 이벤트의 기본 클래스

    dataclass 기반으로 설계하여 자식 클래스와 일관성 유지:
    - 공통 메타데이터는 field(init=False)로 자동 생성
    - 자식 클래스에서 __post_init__에서 초기화 가능
    """

    # 메타데이터는 자동 생성되므로 __init__에서 제외
    _event_id: str = field(init=False)
    _occurred_at: datetime = field(init=False)
    _version: int = field(init=False, default=1)
    _correlation_id: Optional[str] = field(init=False, default=None)
    _causation_id: Optional[str] = field(init=False, default=None)
    _metadata: Dict[str, Any] = field(init=False, default_factory=dict)

    def __post_init__(self):
        """메타데이터 자동 초기화"""
        object.__setattr__(self, '_event_id', str(uuid.uuid4()))
        object.__setattr__(self, '_occurred_at', datetime.now())

    @property
    def event_id(self) -> str:
        return self._event_id

    @property
    def occurred_at(self) -> datetime:
        return self._occurred_at

    @property
    def version(self) -> int:
        return self._version

    @property
    def correlation_id(self) -> Optional[str]:
        return self._correlation_id

    @property
    def causation_id(self) -> Optional[str]:
        return self._causation_id

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    @property
    @abstractmethod
    def event_type(self) -> str:
        """이벤트 타입 (하위 클래스에서 구현)"""
        pass

    @property
    @abstractmethod
    def aggregate_id(self) -> str:
        """관련된 Aggregate Root ID (하위 클래스에서 구현)"""
        pass

    def add_metadata(self, key: str, value: Any) -> None:
        """메타데이터 추가"""
        self._metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """이벤트를 딕셔너리로 변환 (직렬화용)"""
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
        """이벤트별 고유 데이터 반환 (하위 클래스에서 구현)"""
        # 기본적으로 모든 public 필드를 반환 (메타데이터 제외)
        excluded = {"_event_id", "_occurred_at", "_version", "_correlation_id", "_causation_id", "_metadata"}
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_') or key not in excluded
        }
