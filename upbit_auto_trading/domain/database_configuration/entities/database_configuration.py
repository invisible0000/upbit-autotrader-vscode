"""
Database Configuration Entity

데이터베이스 구성 정보를 나타내는 도메인 엔터티입니다.
DDD의 Entity 패턴을 따라 식별자와 비즈니스 로직을 포함합니다.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from upbit_auto_trading.domain.database_configuration.value_objects.database_path import DatabasePath


@dataclass
class DatabaseConfiguration:
    """
    데이터베이스 구성 엔터티

    데이터베이스의 타입, 경로, 연결 상태 등을 관리합니다.
    """

    database_type: str  # settings, strategies, market_data
    database_path: DatabasePath
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_path: Optional[str] = None  # 원본 파일 경로

    def __post_init__(self):
        """초기화 후 처리"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def update_path(self, new_path: DatabasePath, source_path: Optional[str] = None) -> None:
        """경로 업데이트"""
        self.database_path = new_path
        self.source_path = source_path
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """활성화"""
        self.is_active = True
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """비활성화"""
        self.is_active = False
        self.updated_at = datetime.now()

    def get_path_string(self) -> str:
        """경로 문자열 반환"""
        return str(self.database_path.path)

    def exists(self) -> bool:
        """파일 존재 여부 확인"""
        return self.database_path.exists()

    def is_valid(self) -> bool:
        """구성 유효성 검사"""
        return (self.database_type in ['settings', 'strategies', 'market_data']
                and self.database_path.is_valid()
                and self.is_active)

    def get_identifier(self) -> str:
        """식별자 반환"""
        return self.database_type
