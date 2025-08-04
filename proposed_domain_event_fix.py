from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


@dataclass(frozen=True)
class DomainEvent(ABC):
    """모든 도메인 이벤트의 기본 클래스 - 재설계"""

    # 📝 주의: 기본값이 있는 필드들을 먼저 정의하면
    # 자식 클래스에서 기본값 없는 필드 추가 불가능

    # 해결책: mixin 패턴이나 다른 방식 필요

    @property
    def event_id(self) -> str:
        """이벤트 ID (프로퍼티로 변경)"""
        if not hasattr(self, '_event_id'):
            object.__setattr__(self, '_event_id', str(uuid.uuid4()))
        return self._event_id

    @property
    def occurred_at(self) -> datetime:
        """발생 시간 (프로퍼티로 변경)"""
        if not hasattr(self, '_occurred_at'):
            object.__setattr__(self, '_occurred_at', datetime.now())
        return self._occurred_at

    @property
    def version(self) -> int:
        """이벤트 버전"""
        return 1

    @property
    def correlation_id(self) -> Optional[str]:
        """상관관계 ID"""
        return getattr(self, '_correlation_id', self.event_id)

    @property
    def causation_id(self) -> Optional[str]:
        """인과관계 ID"""
        return getattr(self, '_causation_id', None)

    @property
    def metadata(self) -> Dict[str, Any]:
        """메타데이터"""
        if not hasattr(self, '_metadata'):
            object.__setattr__(self, '_metadata', {})
        return self._metadata

    def __post_init__(self):
        """이벤트 생성 후 초기화"""
        # 지연 초기화를 위해 프로퍼티 접근
        _ = self.event_id
        _ = self.occurred_at
        _ = self.metadata

    @property
    def event_type(self) -> str:
        """이벤트 타입 반환 (클래스명 기반)"""
        return self.__class__.__name__

    def add_metadata(self, key: str, value: Any) -> None:
        """메타데이터 추가"""
        self.metadata[key] = value

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
        # 기본적으로 dataclass의 모든 필드를 반환 (기본 필드 제외)
        excluded_fields = {"_event_id", "_occurred_at", "_correlation_id", "_causation_id", "_metadata"}
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_') or key not in excluded_fields
        }
