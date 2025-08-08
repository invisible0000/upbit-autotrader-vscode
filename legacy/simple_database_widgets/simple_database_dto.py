"""
간단한 데이터베이스 설정 DTO

기본에 충실한 데이터 전송 객체입니다.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class SimpleDatabaseInfoDto:
    """데이터베이스 정보 DTO"""
    settings_db_path: str
    strategies_db_path: str
    market_data_db_path: str


@dataclass
class SimpleDatabaseStatusDto:
    """데이터베이스 상태 DTO"""
    settings_db_exists: bool
    strategies_db_exists: bool
    market_data_db_exists: bool
    status_message: str


@dataclass
class DatabaseValidationResultDto:
    """데이터베이스 검증 결과 DTO"""
    results: List[str]
    all_valid: bool
    error_count: int
