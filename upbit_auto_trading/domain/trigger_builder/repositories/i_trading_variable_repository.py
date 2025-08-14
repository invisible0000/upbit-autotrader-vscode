"""
TradingVariable Repository Interface
- 도메인 계층의 Repository 인터페이스
- 외부 의존성 없는 순수한 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from upbit_auto_trading.domain.trigger_builder.entities.trading_variable import TradingVariable
from upbit_auto_trading.domain.trigger_builder.enums import VariableCategory, ComparisonGroup


class ITradingVariableRepository(ABC):
    """TradingVariable Repository 인터페이스"""

    @abstractmethod
    async def get_by_id(self, variable_id: str) -> Optional[TradingVariable]:
        """변수 ID로 조회"""
        pass

    @abstractmethod
    async def get_all_active(self) -> List[TradingVariable]:
        """활성화된 모든 변수 조회"""
        pass

    @abstractmethod
    async def get_by_category(self, category: VariableCategory) -> List[TradingVariable]:
        """카테고리별 변수 조회"""
        pass

    @abstractmethod
    async def get_by_comparison_group(self, group: ComparisonGroup) -> List[TradingVariable]:
        """비교 그룹별 변수 조회"""
        pass

    @abstractmethod
    async def search_by_name(self, search_term: str, language: str = "ko") -> List[TradingVariable]:
        """이름으로 변수 검색"""
        pass

    @abstractmethod
    async def create(self, variable: TradingVariable) -> TradingVariable:
        """변수 생성"""
        pass

    @abstractmethod
    async def update(self, variable: TradingVariable) -> TradingVariable:
        """변수 수정"""
        pass

    @abstractmethod
    async def delete(self, variable_id: str) -> bool:
        """변수 삭제"""
        pass

    @abstractmethod
    async def get_compatible_variables(self, variable_id: str) -> List[TradingVariable]:
        """호환 가능한 변수들 조회"""
        pass

    @abstractmethod
    async def bulk_create(self, variables: List[TradingVariable]) -> List[TradingVariable]:
        """변수 일괄 생성"""
        pass

    @abstractmethod
    async def get_variables_with_parameters(self) -> List[TradingVariable]:
        """파라미터가 있는 변수들 조회"""
        pass

    @abstractmethod
    async def get_meta_variables(self) -> List[TradingVariable]:
        """메타 변수들 조회 (META_ 접두사)"""
        pass

    @abstractmethod
    async def get_dynamic_management_variables(self) -> List[TradingVariable]:
        """동적 관리 변수들 조회"""
        pass

    @abstractmethod
    async def get_change_detection_variables(self) -> List[TradingVariable]:
        """변화 감지 변수들 조회"""
        pass

    @abstractmethod
    async def get_external_trackable_variables(self) -> List[TradingVariable]:
        """외부 추적 가능한 변수들 조회 (external_variable 파라미터 타입에서 사용)"""
        pass

    @abstractmethod
    async def load_from_yaml_config(self) -> List[TradingVariable]:
        """YAML 설정파일에서 변수들 로드"""
        pass
