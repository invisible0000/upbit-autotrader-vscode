"""
Strategy Application Service - 전략 관리 Application Service

전략 관련 Use Case들을 구현합니다:
- 전략 생성, 수정, 삭제, 조회
- 전략 활성화/비활성화
- 도메인 이벤트 발행 관리
"""

from typing import List, Optional
import logging

from upbit_auto_trading.application.services.base_application_service import BaseApplicationService
from upbit_auto_trading.application.dto.strategy_dto import StrategyDto
from upbit_auto_trading.application.commands.strategy_commands import (
    CreateStrategyCommand, UpdateStrategyCommand, DeleteStrategyCommand
)
from upbit_auto_trading.domain.entities.strategy import Strategy
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService


class StrategyApplicationService(BaseApplicationService[Strategy]):
    """전략 관리 Application Service

    UI에 흩어진 전략 관리 로직을 중앙 집중화하여 관리합니다.
    """

    def __init__(self, strategy_repository: StrategyRepository,
                 compatibility_service: StrategyCompatibilityService):
        super().__init__()
        self._strategy_repository = strategy_repository
        self._compatibility_service = compatibility_service
        self._logger = logging.getLogger(__name__)

    def create_strategy(self, command: CreateStrategyCommand) -> StrategyDto:
        """새 전략 생성

        Args:
            command: 전략 생성 명령

        Returns:
            StrategyDto: 생성된 전략 정보

        Raises:
            ValueError: 검증 실패 시
        """
        # 1. 명령 유효성 검증
        validation_errors = command.validate()
        if validation_errors:
            raise ValueError(f"전략 생성 실패: {', '.join(validation_errors)}")

        # 2. 중복 이름 검증
        existing_strategy = self._strategy_repository.find_by_name(command.name)
        if existing_strategy:
            raise ValueError(f"이미 존재하는 전략 이름입니다: {command.name}")

        # 3. 도메인 엔티티 생성
        strategy_id = StrategyId.generate_default()
        strategy = Strategy.create_new(
            strategy_id=strategy_id,
            name=command.name,
            description=command.description,
            created_by=command.created_by
        )

        # 4. 메타데이터 설정 (tags는 별도 처리 필요)
        if command.tags:
            # 태그는 현재 Strategy 엔티티에서 직접 지원하지 않으므로 추후 확장
            pass

        # 5. 저장 및 이벤트 발행
        self._strategy_repository.save(strategy)
        self._publish_domain_events(strategy)

        self._logger.info(f"전략 생성 완료: {strategy.name} (ID: {strategy.strategy_id.value})")

        return StrategyDto.from_entity(strategy)

    def get_strategy(self, strategy_id: str) -> Optional[StrategyDto]:
        """전략 조회

        Args:
            strategy_id: 전략 ID

        Returns:
            StrategyDto: 전략 정보 (없으면 None)
        """
        strategy = self._strategy_repository.find_by_id(StrategyId(strategy_id))
        return StrategyDto.from_entity(strategy) if strategy else None

    def get_all_strategies(self) -> List[StrategyDto]:
        """모든 전략 조회

        Returns:
            List[StrategyDto]: 전략 목록
        """
        strategies = self._strategy_repository.find_all()
        return [StrategyDto.from_entity(strategy) for strategy in strategies]

    def update_strategy(self, command: UpdateStrategyCommand) -> StrategyDto:
        """전략 수정

        Args:
            command: 전략 수정 명령

        Returns:
            StrategyDto: 수정된 전략 정보

        Raises:
            ValueError: 검증 실패 또는 전략 없음
        """
        # 1. 명령 유효성 검증
        validation_errors = command.validate()
        if validation_errors:
            raise ValueError(f"전략 수정 실패: {', '.join(validation_errors)}")

        # 2. 기존 전략 조회
        strategy = self._strategy_repository.find_by_id(StrategyId(command.strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {command.strategy_id}")

        # 3. 수정 사항 적용
        update_needed = False
        new_name = None
        new_description = None

        if command.name and command.name != strategy.name:
            # 중복 이름 검증
            existing_strategy = self._strategy_repository.find_by_name(command.name)
            if existing_strategy and existing_strategy.strategy_id != strategy.strategy_id:
                raise ValueError(f"이미 존재하는 전략 이름입니다: {command.name}")
            new_name = command.name
            update_needed = True

        if command.description is not None:
            new_description = command.description
            update_needed = True

        if update_needed:
            strategy.update_metadata(name=new_name, description=new_description)

        if command.tags is not None:
            # 태그는 현재 Strategy 엔티티에서 직접 지원하지 않으므로 추후 확장
            pass

        # 4. 저장 및 이벤트 발행
        self._strategy_repository.save(strategy)
        self._publish_domain_events(strategy)

        self._logger.info(f"전략 수정 완료: {strategy.name} (ID: {strategy.strategy_id.value})")

        return StrategyDto.from_entity(strategy)

    def delete_strategy(self, command: DeleteStrategyCommand) -> bool:
        """전략 삭제

        Args:
            command: 전략 삭제 명령

        Returns:
            bool: 삭제 성공 여부

        Raises:
            ValueError: 검증 실패 또는 전략 없음
        """
        # 1. 명령 유효성 검증
        validation_errors = command.validate()
        if validation_errors:
            raise ValueError(f"전략 삭제 실패: {', '.join(validation_errors)}")

        # 2. 기존 전략 조회
        strategy = self._strategy_repository.find_by_id(StrategyId(command.strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {command.strategy_id}")

        # 3. 삭제 처리
        if command.soft_delete:
            strategy.mark_for_deletion(
                deleted_by="system",
                deletion_reason="user_request"
            )
            self._strategy_repository.save(strategy)
        else:
            self._strategy_repository.delete(strategy.strategy_id)

        # 4. 이벤트 발행
        self._publish_domain_events(strategy)

        self._logger.info(f"전략 삭제 완료: {strategy.name} (ID: {strategy.strategy_id.value})")

        return True

    def activate_strategy(self, strategy_id: str) -> StrategyDto:
        """전략 활성화

        Args:
            strategy_id: 전략 ID

        Returns:
            StrategyDto: 활성화된 전략 정보

        Raises:
            ValueError: 전략 없음
        """
        strategy = self._strategy_repository.find_by_id(StrategyId(strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {strategy_id}")

        strategy.activate()
        self._strategy_repository.save(strategy)
        self._publish_domain_events(strategy)

        return StrategyDto.from_entity(strategy)

    def deactivate_strategy(self, strategy_id: str, reason: str = "user_requested") -> StrategyDto:
        """전략 비활성화

        Args:
            strategy_id: 전략 ID
            reason: 비활성화 이유

        Returns:
            StrategyDto: 비활성화된 전략 정보

        Raises:
            ValueError: 전략 없음
        """
        strategy = self._strategy_repository.find_by_id(StrategyId(strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {strategy_id}")

        strategy.deactivate()
        self._strategy_repository.save(strategy)
        self._publish_domain_events(strategy)

        return StrategyDto.from_entity(strategy)
