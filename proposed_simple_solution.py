from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


class DomainEvent(ABC):
    """도메인 이벤트 기본 클래스 - 일반 클래스로 변경"""

    def __init__(self):
        self._event_id = str(uuid.uuid4())
        self._occurred_at = datetime.now()
        self._version = 1
        self._correlation_id = self._event_id
        self._causation_id = None
        self._metadata = {}

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
        """이벤트 타입"""
        pass

    @property
    @abstractmethod
    def aggregate_id(self) -> str:
        """집계 ID"""
        pass

    def add_metadata(self, key: str, value: Any) -> None:
        """메타데이터 추가"""
        self._metadata[key] = value

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
        """이벤트별 고유 데이터 반환 (하위 클래스에서 오버라이드)"""
        return {}


# 사용 예시
@dataclass(frozen=True)
class StrategyCreated(DomainEvent):
    """전략 생성 이벤트"""
    strategy_id: str          # 필수 필드
    strategy_name: str        # 필수 필드
    strategy_type: str = "entry"  # 기본값 있는 필드
    creator_id: Optional[str] = None

    def __post_init__(self):
        # DomainEvent 초기화 호출
        super().__init__()

    @property
    def event_type(self) -> str:
        return "strategy.created"

    @property
    def aggregate_id(self) -> str:
        return self.strategy_id

    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "strategy_type": self.strategy_type,
            "creator_id": self.creator_id
        }
