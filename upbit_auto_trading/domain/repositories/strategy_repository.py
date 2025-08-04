"""
전략 Repository 인터페이스

전략 도메인 엔티티의 영속화를 위한 Repository 인터페이스를 정의합니다.
strategies.sqlite3 데이터베이스와의 데이터 접근을 추상화하며,
기존 StrategyStorage 클래스의 기능을 Repository 패턴으로 재구성합니다.

Author: Repository 인터페이스 정의 Task
Created: 2025-08-04
"""

from abc import abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from upbit_auto_trading.domain.entities.strategy import Strategy
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
from upbit_auto_trading.domain.repositories.base_repository import BaseRepository


class StrategyRepository(BaseRepository[Strategy, StrategyId]):
    """
    전략 데이터 접근을 위한 Repository 인터페이스
    
    DDD 패턴에 따라 Strategy 도메인 엔티티의 영속화를 추상화합니다.
    strategies.sqlite3 데이터베이스의 strategies, strategy_conditions 테이블과
    매핑되며, 기존 StrategyStorage 클래스의 기능을 Repository 패턴으로 재구성합니다.
    
    기존 호환성:
        - StrategyStorage.save_strategy() → save()
        - StrategyStorage.get_strategy() → find_by_id()
        - component_strategy 테이블과의 JSON 기반 데이터 저장 방식 지원
    """
    
    # BaseRepository 기본 메서드들 (상속)
    @abstractmethod
    def save(self, entity: Strategy) -> None:
        """
        전략을 strategies.sqlite3에 저장합니다.
        
        strategies 테이블과 strategy_conditions 테이블에 트랜잭션으로 저장하며,
        기존 StrategyStorage.save_strategy() 메서드와 호환되도록 구현됩니다.
        
        Args:
            entity: 저장할 Strategy 도메인 엔티티
            
        Raises:
            RepositoryError: 저장 실패 시
            ValidationError: 전략 데이터 검증 실패 시
        """
        pass
    
    @abstractmethod
    def find_by_id(self, entity_id: StrategyId) -> Optional[Strategy]:
        """
        전략 ID로 전략을 조회합니다.
        
        strategies 테이블과 strategy_conditions 테이블을 JOIN하여
        완전한 Strategy 엔티티를 재구성합니다.
        
        Args:
            entity_id: 조회할 전략의 고유 식별자
            
        Returns:
            Optional[Strategy]: 조회된 전략 엔티티, 없으면 None
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[Strategy]:
        """
        모든 전략을 조회합니다.
        
        Returns:
            List[Strategy]: 모든 전략 엔티티 목록
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: StrategyId) -> bool:
        """
        전략을 삭제합니다.
        
        관련 strategy_conditions도 CASCADE로 함께 삭제됩니다.
        
        Args:
            entity_id: 삭제할 전략의 고유 식별자
            
        Returns:
            bool: 삭제 성공 여부
        """
        pass
    
    @abstractmethod
    def exists(self, entity_id: StrategyId) -> bool:
        """
        전략 존재 여부를 확인합니다.
        
        Args:
            entity_id: 확인할 전략의 고유 식별자
            
        Returns:
            bool: 존재 여부
        """
        pass
    
    # 전략 특화 메서드들 (비즈니스 요구사항)
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Strategy]:
        """
        전략 이름으로 전략을 조회합니다.
        
        전략 이름은 고유하므로 단일 결과를 반환합니다.
        
        Args:
            name: 전략 이름
            
        Returns:
            Optional[Strategy]: 해당 이름의 전략, 없으면 None
        """
        pass
    
    @abstractmethod
    def find_by_tags(self, tags: List[str]) -> List[Strategy]:
        """
        태그로 전략을 검색합니다.
        
        strategies 테이블의 tags 컬럼(JSON 형태)에서 
        지정된 태그들을 포함하는 전략들을 조회합니다.
        
        Args:
            tags: 검색할 태그 목록
            
        Returns:
            List[Strategy]: 해당 태그를 포함하는 전략들
        """
        pass
    
    @abstractmethod
    def find_active_strategies(self) -> List[Strategy]:
        """
        활성화된 전략들만 조회합니다.
        
        is_active = 1인 전략들만 반환합니다.
        
        Returns:
            List[Strategy]: 활성화된 전략 목록
        """
        pass
    
    @abstractmethod
    def find_strategies_created_after(self, date: datetime) -> List[Strategy]:
        """
        특정 날짜 이후에 생성된 전략들을 조회합니다.
        
        created_at 컬럼을 기준으로 필터링합니다.
        
        Args:
            date: 기준 날짜
            
        Returns:
            List[Strategy]: 기준 날짜 이후 생성된 전략들
        """
        pass
    
    @abstractmethod
    def find_strategies_by_risk_level(self, min_risk: int, max_risk: int) -> List[Strategy]:
        """
        리스크 레벨 범위로 전략을 조회합니다.
        
        Args:
            min_risk: 최소 리스크 레벨 (1-5)
            max_risk: 최대 리스크 레벨 (1-5)
            
        Returns:
            List[Strategy]: 해당 리스크 범위의 전략들
        """
        pass
    
    @abstractmethod
    def find_strategies_by_performance_range(self, min_return: float, max_return: float) -> List[Strategy]:
        """
        예상 수익률 범위로 전략을 조회합니다.
        
        Args:
            min_return: 최소 예상 수익률
            max_return: 최대 예상 수익률
            
        Returns:
            List[Strategy]: 해당 수익률 범위의 전략들
        """
        pass
    
    # 전략 메타데이터 관리 메서드들
    @abstractmethod
    def update_strategy_metadata(self, strategy_id: StrategyId, metadata: Dict[str, Any]) -> bool:
        """
        전략 메타데이터를 업데이트합니다.
        
        name, description, tags, risk_level, expected_return 등의 
        메타데이터만 업데이트하며, 전략 조건은 변경하지 않습니다.
        
        Args:
            strategy_id: 업데이트할 전략의 ID
            metadata: 업데이트할 메타데이터 딕셔너리
                     예: {"name": "새 이름", "description": "새 설명", "tags": ["태그1", "태그2"]}
            
        Returns:
            bool: 업데이트 성공 여부
        """
        pass
    
    @abstractmethod
    def increment_use_count(self, strategy_id: StrategyId) -> None:
        """
        전략 사용 횟수를 1 증가시킵니다.
        
        백테스팅이나 실제 거래에서 전략이 사용될 때마다 호출됩니다.
        
        Args:
            strategy_id: 사용 횟수를 증가시킬 전략의 ID
        """
        pass
    
    @abstractmethod
    def update_last_used_at(self, strategy_id: StrategyId, timestamp: datetime) -> None:
        """
        마지막 사용 시간을 업데이트합니다.
        
        Args:
            strategy_id: 업데이트할 전략의 ID
            timestamp: 마지막 사용 시간
        """
        pass
    
    @abstractmethod
    def get_strategy_usage_statistics(self, strategy_id: StrategyId) -> Dict[str, Any]:
        """
        전략의 사용 통계를 조회합니다.
        
        Args:
            strategy_id: 통계를 조회할 전략의 ID
            
        Returns:
            Dict[str, Any]: 사용 통계 정보
                          {"use_count": 10, "last_used_at": datetime, "created_at": datetime}
        """
        pass
    
    @abstractmethod
    def get_popular_strategies(self, limit: int = 10) -> List[Strategy]:
        """
        사용 횟수가 많은 인기 전략들을 조회합니다.
        
        Args:
            limit: 조회할 전략 수
            
        Returns:
            List[Strategy]: 사용 횟수 내림차순으로 정렬된 전략 목록
        """
        pass
    
    @abstractmethod
    def search_strategies(self, query: str) -> List[Strategy]:
        """
        전략 이름이나 설명에서 키워드를 검색합니다.
        
        Args:
            query: 검색할 키워드
            
        Returns:
            List[Strategy]: 검색 결과 전략 목록
        """
        pass
