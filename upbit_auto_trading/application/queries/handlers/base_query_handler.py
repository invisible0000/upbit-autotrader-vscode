"""
기본 Query Handler 추상 클래스
모든 Query Handler가 상속받는 베이스 클래스
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

Q = TypeVar('Q')  # Query type
R = TypeVar('R')  # Response type


class BaseQueryHandler(ABC, Generic[Q, R]):
    """모든 Query Handler의 기본 클래스"""

    @abstractmethod
    def handle(self, query: Q) -> R:
        """쿼리 처리"""
        pass

    def validate_query(self, query: Q) -> None:
        """쿼리 유효성 검증"""
        pass
