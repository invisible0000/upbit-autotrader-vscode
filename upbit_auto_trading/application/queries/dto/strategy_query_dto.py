"""
전략 관련 Query DTO 정의
CQRS 패턴의 Query 측면을 담당하는 데이터 전송 객체들
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class StrategySortField(Enum):
    """전략 정렬 필드"""
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"
    PERFORMANCE = "performance"

class SortDirection(Enum):
    """정렬 방향"""
    ASC = "asc"
    DESC = "desc"

@dataclass
class StrategyListQuery:
    """전략 목록 조회 쿼리"""
    page: int = 1
    page_size: int = 20
    status_filter: Optional[str] = None  # ACTIVE, INACTIVE, DELETED
    tag_filter: Optional[List[str]] = None
    name_search: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    sort_field: StrategySortField = StrategySortField.CREATED_AT
    sort_direction: SortDirection = SortDirection.DESC
    include_deleted: bool = False

@dataclass
class StrategyListItem:
    """전략 목록 아이템 응답 DTO"""
    strategy_id: str
    name: str
    status: str
    tags: List[str]
    entry_triggers_count: int
    exit_triggers_count: int
    last_backtest_date: Optional[datetime]
    last_backtest_performance: Optional[float]
    created_at: datetime
    updated_at: datetime

@dataclass
class StrategyListResponse:
    """전략 목록 응답 DTO"""
    items: List[StrategyListItem]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool

@dataclass
class StrategyDetailQuery:
    """전략 상세 조회 쿼리"""
    strategy_id: str
    include_triggers: bool = True
    include_backtest_history: bool = True
    include_performance_metrics: bool = True

@dataclass
class StrategyDetailResponse:
    """전략 상세 응답 DTO"""
    strategy_id: str
    name: str
    description: Optional[str]
    status: str
    tags: List[str]
    triggers: List[Dict[str, Any]]
    backtest_history: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
