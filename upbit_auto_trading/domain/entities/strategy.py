"""
전략 도메인 엔티티 (Strategy)

매매 전략의 핵심 비즈니스 로직을 캡슐화한 도메인 엔티티입니다.
기존 StrategyCombination과 StrategyConfig 모델을 통합하여 도메인 엔티티로 변환한 것입니다.

전략은 다음 요소들로 구성됩니다:
- 전략 식별자와 기본 정보
- 진입 전략 설정 (필수, 1개)
- 관리 전략 설정들 (선택, 여러개)
- 충돌 해결 방식
- 도메인 이벤트 발생 및 관리
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..value_objects.strategy_id import StrategyId
from ..value_objects.strategy_config import StrategyConfig
from ..value_objects.conflict_resolution import ConflictResolution
from ..exceptions.domain_exceptions import DomainException

# 새로운 도메인 이벤트 시스템 import
from ..events.strategy_events import (
    StrategyCreated,
    StrategyUpdated,
    StrategyActivated,
    StrategyDeactivated,
    StrategyDeleted
)
from ..events.base_domain_event import DomainEvent

class InvalidStrategyConfigurationError(DomainException):
    """잘못된 전략 설정 예외"""
    pass

class IncompatibleStrategyError(DomainException):
    """호환되지 않는 전략 예외"""
    pass

@dataclass
class Strategy:
    """
    전략 도메인 엔티티

    매매 전략의 완전한 정의를 포함하는 도메인 엔티티:
    - 고유 식별자와 메타데이터
    - 진입 전략 (필수 1개)
    - 관리 전략들 (선택 다수)
    - 충돌 해결 방식
    - 도메인 이벤트 관리
    """

    strategy_id: StrategyId
    name: str
    description: Optional[str] = None
    entry_strategy_config: Optional[StrategyConfig] = None
    management_strategy_configs: List[StrategyConfig] = field(default_factory=list)
    conflict_resolution: ConflictResolution = ConflictResolution.CONSERVATIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    is_active: bool = True

    # 도메인 이벤트 (새로운 이벤트 시스템)
    _domain_events: List[DomainEvent] = field(default_factory=list, init=False)

    def __post_init__(self):
        """생성 후 유효성 검증 및 초기화"""
        self._validate_strategy_configuration()
        # 새로운 도메인 이벤트 시스템으로 전략 생성 이벤트 발행
        creation_event = StrategyCreated(
            strategy_id=self.strategy_id.value,
            strategy_name=self.name,
            strategy_type="entry",  # 기본값 사용
            created_by=self.created_by,        # 선택사항
            strategy_config={       # 전략 설정을 딕셔너리로 구성
                "entry_strategy_config": self.entry_strategy_config.config_id if self.entry_strategy_config else None,
                "management_strategy_count": len(self.management_strategy_configs),
                "conflict_resolution": self.conflict_resolution.value
            }
        )
        self._domain_events.append(creation_event)

    def _validate_strategy_configuration(self):
        """전략 설정 유효성 검증"""
        if not self.name.strip():
            raise InvalidStrategyConfigurationError("전략 이름은 필수입니다")

        # 진입 전략은 선택사항으로 변경 (유연성 확보)
        if self.entry_strategy_config and not self._is_entry_strategy(self.entry_strategy_config):
            raise InvalidStrategyConfigurationError("진입 전략 설정이 올바르지 않습니다")

        # 관리 전략들 검증
        for mgmt_config in self.management_strategy_configs:
            if not self._is_management_strategy(mgmt_config):
                raise InvalidStrategyConfigurationError(f"관리 전략 {mgmt_config.config_id}가 올바르지 않습니다")

    def _is_entry_strategy(self, config: StrategyConfig) -> bool:
        """진입 전략인지 확인 (간단한 ID 기반 판단)"""
        # 실제로는 StrategyDefinition에서 role을 확인해야 함
        return "entry" in config.strategy_definition_id.lower()

    def _is_management_strategy(self, config: StrategyConfig) -> bool:
        """관리 전략인지 확인"""
        # 실제로는 StrategyDefinition에서 role을 확인해야 함
        return "management" in config.strategy_definition_id.lower() or "mgmt" in config.strategy_definition_id.lower()

    def add_management_strategy(self, config: StrategyConfig) -> None:
        """관리 전략 추가"""
        if not self._is_management_strategy(config):
            raise IncompatibleStrategyError(f"'{config.strategy_definition_id}'는 관리 전략이 아닙니다")

        # 중복 방지
        if any(existing.config_id == config.config_id for existing in self.management_strategy_configs):
            raise InvalidStrategyConfigurationError(f"관리 전략 '{config.config_id}'가 이미 존재합니다")

        old_count = len(self.management_strategy_configs)
        self.management_strategy_configs.append(config)
        self.updated_at = datetime.now()

        # 새로운 도메인 이벤트 발행
        modification_event = StrategyUpdated(
            strategy_id=self.strategy_id.value,
            strategy_name=self.name,
            updated_fields={
                "management_strategy_count": {
                    "old": old_count,
                    "new": len(self.management_strategy_configs)
                },
                "added_config_id": config.config_id,
                "added_strategy_name": config.strategy_name,
                "added_strategy_definition_id": config.strategy_definition_id
            }
        )
        self._domain_events.append(modification_event)

    def remove_management_strategy(self, config_id: str) -> bool:
        """관리 전략 제거"""
        for i, config in enumerate(self.management_strategy_configs):
            if config.config_id == config_id:
                removed_config = self.management_strategy_configs.pop(i)
                self.updated_at = datetime.now()

                # 새로운 도메인 이벤트 발행
                modification_event = StrategyUpdated(
                    strategy_id=self.strategy_id.value,
                    strategy_name=self.name,
                    updated_fields={
                        "removed_config_id": removed_config.config_id,
                        "removed_config_name": removed_config.strategy_name,
                        "remaining_count": len(self.management_strategy_configs)
                    }
                )
                self._domain_events.append(modification_event)
                return True
        return False

    def set_entry_strategy(self, config: StrategyConfig) -> None:
        """진입 전략 설정"""
        if not self._is_entry_strategy(config):
            raise IncompatibleStrategyError(f"'{config.strategy_definition_id}'는 진입 전략이 아닙니다")

        old_entry = self.entry_strategy_config
        self.entry_strategy_config = config
        self.updated_at = datetime.now()

        # 새로운 도메인 이벤트 발행
        modification_event = StrategyUpdated(
            strategy_id=self.strategy_id.value,
            strategy_name=self.name,
            updated_fields={
                "entry_strategy_changed": {
                    "old_config_id": old_entry.config_id if old_entry else "none",
                    "new_config_id": config.config_id,
                    "old_strategy_name": old_entry.strategy_name if old_entry else None,
                    "new_strategy_name": config.strategy_name
                }
            }
        )
        self._domain_events.append(modification_event)

    def get_all_strategy_configs(self) -> List[StrategyConfig]:
        """모든 전략 설정 반환"""
        configs = []
        if self.entry_strategy_config:
            configs.append(self.entry_strategy_config)
        configs.extend(self.management_strategy_configs)
        return configs

    def get_management_strategies_by_priority(self) -> List[StrategyConfig]:
        """우선순위순으로 정렬된 관리 전략들 반환"""
        return sorted(self.management_strategy_configs, key=lambda config: config.priority)

    def is_fully_configured(self) -> bool:
        """완전히 설정된 전략인지 확인"""
        return (
            self.entry_strategy_config is not None
            and self.entry_strategy_config.is_enabled()
            and len(self.management_strategy_configs) > 0
        )

    def is_ready_for_execution(self) -> bool:
        """실행 준비가 완료된 전략인지 확인"""
        return (
            self.is_active
            and self.is_fully_configured()
            and all(config.is_enabled() for config in self.get_all_strategy_configs())
        )

    def activate(self) -> None:
        """전략 활성화"""
        if not self.is_active:
            self.is_active = True
            self.updated_at = datetime.now()
            # 새로운 도메인 이벤트 발행
            activation_event = StrategyActivated(
                strategy_id=self.strategy_id.value,
                strategy_name=self.name,
                activated_by="system",
                activation_reason="user_request"
            )
            self._domain_events.append(activation_event)

    def deactivate(self) -> None:
        """전략 비활성화"""
        if self.is_active:
            self.is_active = False
            self.updated_at = datetime.now()
            # 새로운 도메인 이벤트 발행
            deactivation_event = StrategyDeactivated(
                strategy_id=self.strategy_id.value,
                strategy_name=self.name,
                deactivated_by="system",
                deactivation_reason="user_request"
            )
            self._domain_events.append(deactivation_event)

    def update_metadata(self, name: Optional[str] = None, description: Optional[str] = None) -> None:
        """메타데이터 업데이트"""
        changed = False

        if name and name != self.name:
            old_name = self.name
            self.name = name
            changed = True
            # 새로운 도메인 이벤트 발행
            modification_event = StrategyUpdated(
                strategy_id=self.strategy_id.value,
                strategy_name=name,  # 새로운 이름
                updated_fields={
                    "strategy_renamed": {
                        "old_name": old_name,
                        "new_name": name
                    }
                }
            )
            self._domain_events.append(modification_event)

        if description and description != self.description:
            self.description = description
            changed = True

        if changed:
            self.updated_at = datetime.now()

    def resolve_management_conflicts(self, signals: List[str]) -> str:
        """관리 전략 충돌 해결"""
        if len(signals) <= 1:
            return signals[0] if signals else "HOLD"

        resolved_signal = self.conflict_resolution.resolve_signals(signals)

        # 새로운 도메인 이벤트 발행
        modification_event = StrategyUpdated(
            strategy_id=self.strategy_id.value,
            strategy_name=self.name,
            updated_fields={
                "conflict_resolved": {
                    "conflicting_signals": signals,
                    "resolved_signal": resolved_signal,
                    "resolution_method": self.conflict_resolution.value
                }
            }
        )
        self._domain_events.append(modification_event)

        return resolved_signal

    def get_strategy_summary(self) -> Dict[str, Any]:
        """전략 요약 정보"""
        return {
            "strategy_id": str(self.strategy_id),
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "is_fully_configured": self.is_fully_configured(),
            "is_ready_for_execution": self.is_ready_for_execution(),
            "entry_strategy": self.entry_strategy_config.strategy_name if self.entry_strategy_config else None,
            "management_strategy_count": len(self.management_strategy_configs),
            "conflict_resolution": self.conflict_resolution.get_display_name(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def get_domain_events(self) -> List[DomainEvent]:
        """도메인 이벤트 반환 (복사본)"""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """도메인 이벤트 초기화 (이벤트 처리 후 호출)"""
        self._domain_events.clear()

    def has_pending_events(self) -> bool:
        """처리되지 않은 도메인 이벤트가 있는지 확인"""
        return len(self._domain_events) > 0

    def mark_for_deletion(self, deleted_by: Optional[str] = None,
                          deletion_reason: Optional[str] = None) -> None:
        """전략 삭제 표시 및 이벤트 발행"""
        # 전략 삭제 이벤트 발행
        deletion_event = StrategyDeleted(
            strategy_id=self.strategy_id.value,
            strategy_name=self.name,
            deleted_by=deleted_by or "system",
            deletion_reason=deletion_reason or "user_request"
        )
        self._domain_events.append(deletion_event)

        # 전략 비활성화
        if self.is_active:
            self.deactivate()

    @classmethod
    def create_new(cls, strategy_id: StrategyId, name: str,
                   description: Optional[str] = None,
                   created_by: Optional[str] = None) -> "Strategy":
        """새 전략 생성 (팩토리 메서드) - 도메인 이벤트 포함"""
        strategy = cls(
            strategy_id=strategy_id,
            name=name,
            description=description or f"{name} - 새로 생성된 전략",
            created_by=created_by or "system",
            conflict_resolution=ConflictResolution.CONSERVATIVE,
            is_active=False  # 완전히 구성될 때까지 비활성화
        )
        return strategy

    @classmethod
    def create_empty_strategy(cls, strategy_id: StrategyId, name: str) -> "Strategy":
        """빈 전략 생성 (점진적 구성용)"""
        return cls(
            strategy_id=strategy_id,
            name=name,
            description=f"{name} - 점진적으로 구성될 전략",
            conflict_resolution=ConflictResolution.CONSERVATIVE,
            is_active=False  # 완전히 구성될 때까지 비활성화
        )

    def check_trigger_compatibility(self, trigger) -> bool:
        """
        트리거 호환성 검증 (CompatibilityService 위임)

        Args:
            trigger: 검증할 트리거 객체

        Returns:
            bool: 호환성 여부
        """
        # 순환 참조 방지를 위한 지연 import
        from ..services.strategy_compatibility_service import StrategyCompatibilityService

        try:
            # 임시 Mock Repository 클래스
            class MockRepository:
                def get_trading_variables(self):
                    return []

                def get_compatibility_rules(self):
                    return {"default": "compatible"}

                def is_variable_compatible_with(self, variable_id1: str, variable_id2: str) -> bool:
                    return True

            # 임시로 Mock Repository 사용 (실제 구현에서는 DI Container에서 주입)
            compatibility_service = StrategyCompatibilityService(settings_repository=MockRepository())

            # 기존 전략의 변수 ID들 수집 (임시 구현)
            existing_variable_ids = []
            if self.entry_strategy_config:
                # StrategyConfig에서 변수 정보 추출 (실제 구현에서는 더 정교하게)
                existing_variable_ids.extend(self._extract_variable_ids_from_config(self.entry_strategy_config))

            for mgmt_config in self.management_strategy_configs:
                existing_variable_ids.extend(self._extract_variable_ids_from_config(mgmt_config))

            # 새 트리거의 변수 ID 추출
            if hasattr(trigger, 'variable') and hasattr(trigger.variable, 'variable_id'):
                new_variable_id = trigger.variable.variable_id

                # 호환성 검증
                if existing_variable_ids:
                    result = compatibility_service.validate_variable_compatibility(
                        existing_variable_ids + [new_variable_id]
                    )
                    return result.level in ["COMPATIBLE", "WARNING"]
                else:
                    # 첫 번째 트리거인 경우 항상 호환
                    return True

            return True  # 변수 정보가 없으면 기본적으로 호환으로 간주

        except Exception as e:
            # 호환성 검증 실패 시 새로운 도메인 이벤트 발행
            error_event = StrategyUpdated(
                strategy_id=self.strategy_id.value,
                strategy_name=self.name,
                updated_fields={
                    "trigger_compatibility_check_failed": {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "trigger_info": str(trigger) if trigger else "None"
                    }
                }
            )
            self._domain_events.append(error_event)
            return False

    def _extract_variable_ids_from_config(self, config: StrategyConfig) -> List[str]:
        """
        StrategyConfig에서 변수 ID 추출 (임시 구현)

        실제 구현에서는 StrategyConfig의 구조에 따라 적절히 구현
        """
        # 임시 구현 - StrategyConfig의 실제 구조에 맞게 수정 필요
        variable_ids = []

        if hasattr(config, 'parameters') and config.parameters:
            # parameters에서 변수 관련 정보 추출
            for key, value in config.parameters.items():
                if key.endswith('_variable_id') or 'variable' in key.lower():
                    if isinstance(value, str):
                        variable_ids.append(value)

        return variable_ids

    @classmethod
    def create_basic_strategy(cls, strategy_id: StrategyId, name: str,
                              entry_config: StrategyConfig) -> "Strategy":
        """기본 전략 생성 (진입 전략만)"""
        strategy = cls(
            strategy_id=strategy_id,
            name=name,
            entry_strategy_config=entry_config,
            conflict_resolution=ConflictResolution.CONSERVATIVE
        )
        return strategy
