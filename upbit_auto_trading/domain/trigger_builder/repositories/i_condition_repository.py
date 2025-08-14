"""
Condition Repository Interface
- 조건 저장/조회를 위한 Repository 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from upbit_auto_trading.domain.trigger_builder.entities.condition import Condition
from upbit_auto_trading.domain.trigger_builder.enums import ConditionStatus


class IConditionRepository(ABC):
    """Condition Repository 인터페이스"""

    @abstractmethod
    async def get_by_id(self, condition_id: str) -> Optional[Condition]:
        """조건 ID로 조회"""
        pass

    @abstractmethod
    async def get_all_by_status(self, status: ConditionStatus) -> List[Condition]:
        """상태별 조건 조회"""
        pass

    @abstractmethod
    async def get_by_variable_id(self, variable_id: str) -> List[Condition]:
        """변수 ID로 조건들 조회"""
        pass

    @abstractmethod
    async def create(self, condition: Condition) -> Condition:
        """조건 생성"""
        pass

    @abstractmethod
    async def update(self, condition: Condition) -> Condition:
        """조건 수정"""
        pass

    @abstractmethod
    async def delete(self, condition_id: str) -> bool:
        """조건 삭제"""
        pass

    @abstractmethod
    async def search_by_description(self, search_term: str) -> List[Condition]:
        """설명으로 조건 검색"""
        pass

    @abstractmethod
    async def get_recent_conditions(self, limit: int = 10) -> List[Condition]:
        """최근 생성된 조건들 조회"""
        pass

    @abstractmethod
    async def bulk_create(self, conditions: List[Condition]) -> List[Condition]:
        """조건 일괄 생성"""
        pass

    @abstractmethod
    async def update_status(self, condition_id: str, status: ConditionStatus) -> bool:
        """조건 상태 업데이트"""
        pass
