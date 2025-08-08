"""
Database Configuration Repository Interface

데이터베이스 구성 정보를 저장하고 조회하는 Repository 인터페이스입니다.
DDD의 Repository 패턴을 따라 도메인 로직과 데이터 접근을 분리합니다.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from upbit_auto_trading.domain.database_configuration.entities.database_configuration import DatabaseConfiguration


class IDatabaseConfigurationRepository(ABC):
    """데이터베이스 구성 Repository 인터페이스"""

    @abstractmethod
    def save(self, configuration: DatabaseConfiguration) -> None:
        """데이터베이스 구성 저장"""
        pass

    @abstractmethod
    def get_by_type(self, database_type: str) -> Optional[DatabaseConfiguration]:
        """타입별 데이터베이스 구성 조회"""
        pass

    @abstractmethod
    def get_all(self) -> List[DatabaseConfiguration]:
        """모든 데이터베이스 구성 조회"""
        pass

    @abstractmethod
    def delete(self, database_type: str) -> bool:
        """데이터베이스 구성 삭제"""
        pass

    @abstractmethod
    def exists(self, database_type: str) -> bool:
        """데이터베이스 구성 존재 여부 확인"""
        pass
