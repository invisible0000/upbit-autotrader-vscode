"""
Trigger Application Service - 트리거 관리 Application Service

트리거 관련 Use Case들을 구현합니다:
- 트리거 생성, 수정, 삭제, 조회
- 트리거 호환성 검증
- 전략별 트리거 관리
"""

from typing import List, Optional
import logging

from upbit_auto_trading.application.services.base_application_service import BaseApplicationService
from upbit_auto_trading.application.dto.trigger_dto import TriggerDto, CreateTriggerDto
from upbit_auto_trading.domain.entities.trigger import Trigger, TradingVariable
from upbit_auto_trading.domain.value_objects.trigger_id import TriggerId
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
from upbit_auto_trading.domain.repositories.trigger_repository import TriggerRepository
from upbit_auto_trading.domain.repositories.settings_repository import SettingsRepository
from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService


class TriggerApplicationService(BaseApplicationService[Trigger]):
    """트리거 관리 Application Service

    UI의 트리거 빌더에서 수행되던 비즈니스 로직을 중앙 집중화합니다.
    """

    def __init__(self, trigger_repository: TriggerRepository,
                 strategy_repository: StrategyRepository,
                 settings_repository: SettingsRepository,
                 compatibility_service: StrategyCompatibilityService):
        super().__init__()
        self._trigger_repository = trigger_repository
        self._strategy_repository = strategy_repository
        self._settings_repository = settings_repository
        self._compatibility_service = compatibility_service
        self._logger = logging.getLogger(__name__)

    def create_trigger(self, dto: CreateTriggerDto) -> TriggerDto:
        """새 트리거 생성

        Args:
            dto: 트리거 생성 요청 DTO

        Returns:
            TriggerDto: 생성된 트리거 정보

        Raises:
            ValueError: 검증 실패 시
        """
        # 1. 전략 존재 여부 확인
        strategy = self._strategy_repository.find_by_id(StrategyId(dto.strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {dto.strategy_id}")

        # 2. 트레이딩 변수 조회
        variable_def = self._settings_repository.get_trading_variable(dto.variable_id)
        if not variable_def:
            raise ValueError(f"존재하지 않는 트레이딩 변수입니다: {dto.variable_id}")

        # 3. 트레이딩 변수 생성
        trading_variable = TradingVariable(
            variable_id=variable_def["variable_id"],
            display_name=variable_def.get("display_name_ko", dto.variable_id),
            purpose_category=variable_def.get("purpose_category", "unknown"),
            chart_category=variable_def.get("chart_category", "price"),
            comparison_group=variable_def.get("comparison_group", "default"),
            parameters=dto.variable_params
        )

        # 4. 트리거 엔티티 생성
        trigger_id = TriggerId.generate()
        trigger = Trigger(
            trigger_id=trigger_id,
            trigger_type=dto.trigger_type,
            variable=trading_variable,
            operator=dto.operator,
            target_value=dto.target_value
        )

        # 5. 트리거 이름 설정
        if dto.trigger_name:
            trigger.trigger_name = dto.trigger_name

        # 6. 호환성 검증
        if not self._compatibility_service.can_add_trigger_to_strategy(strategy, trigger):
            reason = self._compatibility_service.get_incompatibility_reason(strategy, trigger)
            raise ValueError(f"트리거가 전략과 호환되지 않습니다: {reason}")

        # 7. 전략에 트리거 추가
        strategy.add_trigger(trigger)

        # 8. 저장 및 이벤트 발행
        self._trigger_repository.save(trigger)
        self._strategy_repository.save(strategy)
        self._publish_domain_events(trigger)
        self._publish_domain_events(strategy)

        self._logger.info(f"트리거 생성 완료: {trigger.trigger_name} (ID: {trigger.trigger_id.value})")

        return TriggerDto.from_entity(trigger)

    def get_triggers_by_strategy(self, strategy_id: str) -> List[TriggerDto]:
        """전략별 트리거 조회

        Args:
            strategy_id: 전략 ID

        Returns:
            List[TriggerDto]: 트리거 목록
        """
        triggers = self._trigger_repository.find_by_strategy_id(StrategyId(strategy_id))
        return [TriggerDto.from_entity(trigger) for trigger in triggers]

    def get_trigger(self, trigger_id: str) -> Optional[TriggerDto]:
        """단일 트리거 조회

        Args:
            trigger_id: 트리거 ID

        Returns:
            TriggerDto: 트리거 정보 (없으면 None)
        """
        trigger = self._trigger_repository.find_by_id(TriggerId(trigger_id))
        return TriggerDto.from_entity(trigger) if trigger else None

    def delete_trigger(self, trigger_id: str) -> bool:
        """트리거 삭제

        Args:
            trigger_id: 트리거 ID

        Returns:
            bool: 삭제 성공 여부

        Raises:
            ValueError: 트리거 없음
        """
        # 1. 트리거 조회
        trigger = self._trigger_repository.find_by_id(TriggerId(trigger_id))
        if not trigger:
            raise ValueError(f"존재하지 않는 트리거입니다: {trigger_id}")

        # 2. 전략에서 트리거 제거
        if hasattr(trigger, 'strategy_id') and trigger.strategy_id:
            strategy = self._strategy_repository.find_by_id(trigger.strategy_id)
            if strategy:
                strategy.remove_trigger(trigger.trigger_id)
                self._strategy_repository.save(strategy)
                self._publish_domain_events(strategy)

        # 3. 트리거 삭제
        self._trigger_repository.delete(trigger.trigger_id)

        self._logger.info(f"트리거 삭제 완료: {getattr(trigger, 'trigger_name', 'Unknown')} (ID: {trigger.trigger_id.value})")

        return True

    def validate_trigger_compatibility(self, strategy_id: str, trigger_data: dict) -> dict:
        """트리거 호환성 검증

        실제 생성 전에 트리거가 전략과 호환되는지 미리 검증합니다.

        Args:
            strategy_id: 전략 ID
            trigger_data: 트리거 데이터 (variable_id, operator, target_value 등)

        Returns:
            dict: 호환성 검증 결과
                - compatible: bool (호환 여부)
                - reason: str (호환되지 않는 이유)
                - suggestions: List[str] (개선 제안들)
        """
        strategy = self._strategy_repository.find_by_id(StrategyId(strategy_id))
        if not strategy:
            return {"compatible": False, "reason": "존재하지 않는 전략입니다", "suggestions": []}

        # 임시 트리거 생성하여 호환성 검증
        variable_def = self._settings_repository.get_trading_variable(trigger_data["variable_id"])
        if not variable_def:
            return {"compatible": False, "reason": "존재하지 않는 트레이딩 변수입니다", "suggestions": []}

        try:
            trading_variable = TradingVariable(
                variable_id=variable_def["variable_id"],
                display_name=variable_def.get("display_name_ko", trigger_data["variable_id"]),
                purpose_category=variable_def.get("purpose_category", "unknown"),
                chart_category=variable_def.get("chart_category", "price"),
                comparison_group=variable_def.get("comparison_group", "default"),
                parameters=trigger_data.get("variable_params", {})
            )

            temp_trigger = Trigger(
                trigger_id=TriggerId.generate(),
                trigger_type=trigger_data["trigger_type"],
                variable=trading_variable,
                operator=trigger_data["operator"],
                target_value=trigger_data["target_value"]
            )

            compatible = self._compatibility_service.can_add_trigger_to_strategy(strategy, temp_trigger)
            reason = "" if compatible else self._compatibility_service.get_incompatibility_reason(strategy, temp_trigger)
            suggestions = self._compatibility_service.get_compatibility_suggestions(strategy, temp_trigger)

            return {
                "compatible": compatible,
                "reason": reason,
                "suggestions": suggestions
            }

        except Exception as e:
            return {
                "compatible": False,
                "reason": f"트리거 검증 중 오류 발생: {str(e)}",
                "suggestions": []
            }
