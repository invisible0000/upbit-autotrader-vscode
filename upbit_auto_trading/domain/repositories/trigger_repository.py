"""
트리거 Repository 인터페이스

트리거 도메인 엔티티의 영속화를 위한 Repository 인터페이스를 정의합니다.
strategies.sqlite3의 strategy_conditions 테이블과의 데이터 접근을 추상화하며,
기존 트리거 빌더 시스템의 조건 관리 기능을 Repository 패턴으로 재구성합니다.

Author: Repository 인터페이스 정의 Task
Created: 2025-08-04
"""

from abc import abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from upbit_auto_trading.domain.entities.trigger import Trigger, TriggerType
from upbit_auto_trading.domain.value_objects.trigger_id import TriggerId
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
from upbit_auto_trading.domain.repositories.base_repository import BaseRepository

class TriggerRepository(BaseRepository[Trigger, TriggerId]):
    """
    트리거 데이터 접근을 위한 Repository 인터페이스

    DDD 패턴에 따라 Trigger 도메인 엔티티의 영속화를 추상화합니다.
    strategies.sqlite3의 strategy_conditions 테이블과 매핑되며,
    기존 트리거 빌더 시스템의 조건 생성/관리 기능을 Repository 패턴으로 재구성합니다.

    특화 기능:
        - 전략별 트리거 관리 (일괄 저장/삭제)
        - 트리거 타입별 조회 (ENTRY, MANAGEMENT, EXIT)
        - 변수별 트리거 검색 및 통계
    """

    # BaseRepository 기본 메서드들 (상속) - 매개변수명 일치
    @abstractmethod
    def save(self, entity: Trigger) -> None:
        """
        트리거를 strategies.sqlite3의 strategy_conditions 테이블에 저장합니다.

        트리거의 조건 정보, 파라미터, 비교 연산자, 대상값 등을
        JSON 형태로 직렬화하여 저장합니다.

        도메인 이벤트 발행:
        저장 완료 후 트리거 엔티티의 도메인 이벤트를 자동으로 발행합니다.
        구현체에서는 저장 로직 완료 후 반드시 _publish_domain_events()를 호출해야 합니다.

        Args:
            entity: 저장할 Trigger 도메인 엔티티

        Raises:
            RepositoryError: 저장 실패 시
            ValidationError: 트리거 데이터 검증 실패 시
        """
        pass

    @abstractmethod
    def find_by_id(self, entity_id: TriggerId) -> Optional[Trigger]:
        """
        트리거 ID로 트리거를 조회합니다.

        strategy_conditions 테이블에서 조건 데이터를 조회하고
        Trigger 도메인 엔티티로 재구성합니다.

        Args:
            entity_id: 조회할 트리거의 고유 식별자

        Returns:
            Optional[Trigger]: 조회된 트리거 엔티티, 없으면 None
        """
        pass

    @abstractmethod
    def find_all(self) -> List[Trigger]:
        """
        모든 트리거를 조회합니다.

        Returns:
            List[Trigger]: 모든 트리거 엔티티 목록
        """
        pass

    @abstractmethod
    def delete(self, entity_id: TriggerId) -> bool:
        """
        트리거를 삭제합니다.

        Args:
            entity_id: 삭제할 트리거의 고유 식별자

        Returns:
            bool: 삭제 성공 여부
        """
        pass

    @abstractmethod
    def exists(self, entity_id: TriggerId) -> bool:
        """
        트리거 존재 여부를 확인합니다.

        Args:
            entity_id: 확인할 트리거의 고유 식별자

        Returns:
            bool: 존재 여부
        """
        pass

    # 트리거 특화 메서드들 (전략 관리)
    @abstractmethod
    def find_by_strategy_id(self, strategy_id: StrategyId) -> List[Trigger]:
        """
        특정 전략에 속한 모든 트리거를 조회합니다.

        전략 구성 시 해당 전략의 모든 진입/관리/청산 트리거를
        한 번에 조회하는데 사용됩니다.

        Args:
            strategy_id: 전략 고유 식별자

        Returns:
            List[Trigger]: 해당 전략의 모든 트리거 목록
        """
        pass

    @abstractmethod
    def find_by_trigger_type(self, trigger_type: TriggerType) -> List[Trigger]:
        """
        트리거 타입별로 트리거를 조회합니다.

        진입 전략 분석, 청산 전략 통계 등에 활용됩니다.

        Args:
            trigger_type: 트리거 타입 (TriggerType.ENTRY, MANAGEMENT, EXIT)

        Returns:
            List[Trigger]: 해당 타입의 모든 트리거 목록
        """
        pass

    @abstractmethod
    def find_by_variable_id(self, variable_id: str) -> List[Trigger]:
        """
        특정 매매 변수를 사용하는 트리거들을 조회합니다.

        특정 지표(예: RSI, MACD)를 사용하는 모든 트리거를 찾아
        변수 변경 영향도 분석이나 유사 전략 탐색에 활용됩니다.

        Args:
            variable_id: 매매 변수 식별자 (예: "indicator.rsi")

        Returns:
            List[Trigger]: 해당 변수를 사용하는 트리거 목록
        """
        pass

    @abstractmethod
    def find_by_strategy_and_type(self, strategy_id: StrategyId, trigger_type: TriggerType) -> List[Trigger]:
        """
        특정 전략의 특정 타입 트리거들을 조회합니다.

        예: 특정 전략의 진입 트리거만 조회하여 진입 조건 분석

        Args:
            strategy_id: 전략 고유 식별자
            trigger_type: 트리거 타입

        Returns:
            List[Trigger]: 해당 전략의 특정 타입 트리거 목록
        """
        pass

    # 배치 작업 메서드들 (성능 최적화)
    @abstractmethod
    def save_strategy_triggers(self, strategy_id: StrategyId, triggers: List[Trigger]) -> None:
        """
        전략에 속한 모든 트리거를 일괄 저장합니다.

        전략 생성/수정 시 모든 트리거를 트랜잭션으로 일괄 처리하여
        데이터 일관성을 보장하고 성능을 최적화합니다.

        Args:
            strategy_id: 전략 고유 식별자
            triggers: 저장할 트리거 목록

        Raises:
            RepositoryError: 일괄 저장 실패 시
        """
        pass

    @abstractmethod
    def delete_strategy_triggers(self, strategy_id: StrategyId) -> int:
        """
        전략의 모든 트리거를 삭제합니다.

        전략 삭제 시 관련된 모든 트리거를 일괄 삭제합니다.

        Args:
            strategy_id: 전략 고유 식별자

        Returns:
            int: 삭제된 트리거 개수
        """
        pass

    @abstractmethod
    def update_triggers_batch(self, trigger_updates: List[Dict[str, Any]]) -> int:
        """
        여러 트리거를 일괄 업데이트합니다.

        Args:
            trigger_updates: 업데이트 정보 목록
                           [{"trigger_id": id, "updates": {"field": value}}]

        Returns:
            int: 업데이트된 트리거 개수
        """
        pass

    # 통계 및 분석 메서드들
    @abstractmethod
    def count_triggers_by_strategy(self, strategy_id: StrategyId) -> Dict[TriggerType, int]:
        """
        전략별 트리거 타입별 개수를 조회합니다.

        전략 복잡도 분석이나 UI 표시용 통계에 활용됩니다.

        Args:
            strategy_id: 전략 고유 식별자

        Returns:
            Dict[TriggerType, int]: 타입별 트리거 개수
                                   {TriggerType.ENTRY: 1, TriggerType.EXIT: 3, ...}
        """
        pass

    @abstractmethod
    def get_trigger_statistics(self) -> Dict[str, Any]:
        """
        전체 트리거 통계 정보를 조회합니다.

        Returns:
            Dict[str, Any]: 트리거 통계 정보
                          {"total_triggers": 100, "by_type": {...}, "by_variable": {...}}
        """
        pass

    @abstractmethod
    def get_most_used_variables(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        가장 많이 사용되는 매매 변수들을 조회합니다.

        Args:
            limit: 조회할 변수 개수

        Returns:
            List[Dict[str, Any]]: 사용 빈도순 변수 목록
                                [{"variable_id": "indicator.rsi", "usage_count": 25}, ...]
        """
        pass

    # 검색 및 필터링 메서드들
    @abstractmethod
    def find_triggers_by_operator(self, operator: str) -> List[Trigger]:
        """
        특정 비교 연산자를 사용하는 트리거들을 조회합니다.

        Args:
            operator: 비교 연산자 (">", "<", ">=", "<=", "~=", "!=")

        Returns:
            List[Trigger]: 해당 연산자를 사용하는 트리거 목록
        """
        pass

    @abstractmethod
    def find_triggers_by_value_range(self, min_value: float, max_value: float) -> List[Trigger]:
        """
        특정 값 범위를 사용하는 트리거들을 조회합니다.

        Args:
            min_value: 최소값
            max_value: 최대값

        Returns:
            List[Trigger]: 해당 값 범위의 트리거 목록
        """
        pass

    @abstractmethod
    def search_triggers_by_description(self, keyword: str) -> List[Trigger]:
        """
        트리거 설명에서 키워드를 검색합니다.

        Args:
            keyword: 검색할 키워드

        Returns:
            List[Trigger]: 검색 결과 트리거 목록
        """
        pass

    # 호환성 검증 관련 메서드들
    @abstractmethod
    def validate_trigger_compatibility(self, trigger: Trigger, strategy_id: StrategyId) -> bool:
        """
        트리거가 기존 전략의 다른 트리거들과 호환되는지 검증합니다.

        Args:
            trigger: 검증할 트리거
            strategy_id: 대상 전략 ID

        Returns:
            bool: 호환성 여부
        """
        pass

    @abstractmethod
    def get_incompatible_triggers(self, trigger: Trigger) -> List[Trigger]:
        """
        주어진 트리거와 호환되지 않는 기존 트리거들을 조회합니다.

        Args:
            trigger: 기준 트리거

        Returns:
            List[Trigger]: 호환되지 않는 트리거 목록
        """
        pass
