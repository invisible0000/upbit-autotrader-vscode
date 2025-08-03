# TASK-20250803-06

## Title
Query 패턴 및 CQRS 구현 (읽기 전용 쿼리 최적화)

## Objective (목표)
Command와 Query 책임을 분리하는 CQRS(Command Query Responsibility Segregation) 패턴을 구현합니다. 복잡한 읽기 쿼리들을 전용 Query Service로 분리하여 성능을 최적화하고, UI에서 필요한 다양한 조회 요구사항을 효율적으로 처리합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 2: Application Layer 구축 (2주)" > "2.2 Query Service 및 CQRS 패턴 (3일)"

## Pre-requisites (선행 조건)
- `TASK-20250803-05`: Application Service 구현 완료

## Detailed Steps (상세 실행 절차)

### 1. **[분석]** 현재 UI의 복잡한 읽기 요구사항 식별
- [ ] 전략 목록 필터링 (상태별, 태그별, 날짜별)
- [ ] 트리거 조건별 검색 및 정렬
- [ ] 백테스팅 결과 통계 및 비교
- [ ] 대시보드용 요약 정보 (성과 지표, 활성 전략 수 등)

### 2. **[폴더 구조 생성]** Query Layer 구조
- [ ] `upbit_auto_trading/application/queries/` 폴더 생성
- [ ] `upbit_auto_trading/application/queries/dto/` 폴더 생성
- [ ] `upbit_auto_trading/application/queries/handlers/` 폴더 생성

### 3. **[새 코드 작성]** Query DTO 정의
- [ ] `upbit_auto_trading/application/queries/dto/strategy_query_dto.py` 생성:
```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class StrategySortField(Enum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"
    PERFORMANCE = "performance"

class SortDirection(Enum):
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
```

- [ ] `upbit_auto_trading/application/queries/dto/dashboard_query_dto.py` 생성:
```python
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime

@dataclass
class DashboardQuery:
    """대시보드 조회 쿼리"""
    date_range_days: int = 30
    include_performance_charts: bool = True
    include_trigger_stats: bool = True

@dataclass
class PerformanceMetric:
    """성과 지표"""
    metric_name: str
    current_value: float
    previous_value: Optional[float]
    change_percentage: Optional[float]
    trend: str  # UP, DOWN, STABLE

@dataclass
class TriggerStatistic:
    """트리거 통계"""
    variable_type: str
    total_count: int
    active_count: int
    success_rate: float
    avg_execution_time_ms: float

@dataclass
class DashboardResponse:
    """대시보드 응답 DTO"""
    summary_stats: Dict[str, Any]
    performance_metrics: List[PerformanceMetric]
    trigger_statistics: List[TriggerStatistic]
    active_strategies_count: int
    recent_backtest_results: List[Dict[str, Any]]
    system_health: Dict[str, Any]
    generated_at: datetime
```

### 4. **[새 코드 작성]** 기본 Query Handler 추상 클래스
- [ ] `upbit_auto_trading/application/queries/handlers/base_query_handler.py` 생성:
```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any

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
```

### 5. **[새 코드 작성]** 전략 Query Handler 구현
- [ ] `upbit_auto_trading/application/queries/handlers/strategy_query_handler.py` 생성:
```python
from typing import List, Optional, Dict, Any
import logging

from upbit_auto_trading.application.queries.handlers.base_query_handler import BaseQueryHandler
from upbit_auto_trading.application.queries.dto.strategy_query_dto import (
    StrategyListQuery, StrategyListResponse, StrategyListItem,
    StrategyDetailQuery, StrategyDetailResponse
)
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
from upbit_auto_trading.domain.repositories.trigger_repository import TriggerRepository
from upbit_auto_trading.domain.repositories.backtest_repository import BacktestRepository

class StrategyListQueryHandler(BaseQueryHandler[StrategyListQuery, StrategyListResponse]):
    """전략 목록 조회 Query Handler"""
    
    def __init__(self, strategy_repository: StrategyRepository,
                 backtest_repository: BacktestRepository):
        self._strategy_repository = strategy_repository
        self._backtest_repository = backtest_repository
        self._logger = logging.getLogger(__name__)
    
    def handle(self, query: StrategyListQuery) -> StrategyListResponse:
        """전략 목록 조회 처리"""
        self.validate_query(query)
        
        # 1. 전략 목록 조회 (필터링 및 정렬 포함)
        strategies = self._strategy_repository.find_with_filters(
            status=query.status_filter,
            tags=query.tag_filter,
            name_pattern=query.name_search,
            created_after=query.created_after,
            created_before=query.created_before,
            include_deleted=query.include_deleted,
            sort_field=query.sort_field.value,
            sort_direction=query.sort_direction.value,
            limit=query.page_size,
            offset=(query.page - 1) * query.page_size
        )
        
        # 2. 총 개수 조회
        total_count = self._strategy_repository.count_with_filters(
            status=query.status_filter,
            tags=query.tag_filter,
            name_pattern=query.name_search,
            created_after=query.created_after,
            created_before=query.created_before,
            include_deleted=query.include_deleted
        )
        
        # 3. 응답 DTO 생성
        items = []
        for strategy in strategies:
            # 최근 백테스트 정보 조회
            last_backtest = self._backtest_repository.find_latest_by_strategy(
                strategy.strategy_id
            )
            
            item = StrategyListItem(
                strategy_id=strategy.strategy_id.value,
                name=strategy.name,
                status=strategy.status.value,
                tags=strategy.tags or [],
                entry_triggers_count=len(strategy.entry_triggers),
                exit_triggers_count=len(strategy.exit_triggers),
                last_backtest_date=last_backtest.completed_at if last_backtest else None,
                last_backtest_performance=last_backtest.total_return if last_backtest else None,
                created_at=strategy.created_at,
                updated_at=strategy.updated_at
            )
            items.append(item)
        
        return StrategyListResponse(
            items=items,
            total_count=total_count,
            page=query.page,
            page_size=query.page_size,
            has_next=(query.page * query.page_size) < total_count,
            has_previous=query.page > 1
        )
    
    def validate_query(self, query: StrategyListQuery) -> None:
        """쿼리 유효성 검증"""
        if query.page < 1:
            raise ValueError("페이지 번호는 1 이상이어야 합니다")
        if query.page_size < 1 or query.page_size > 100:
            raise ValueError("페이지 크기는 1-100 사이여야 합니다")

class StrategyDetailQueryHandler(BaseQueryHandler[StrategyDetailQuery, StrategyDetailResponse]):
    """전략 상세 조회 Query Handler"""
    
    def __init__(self, strategy_repository: StrategyRepository,
                 trigger_repository: TriggerRepository,
                 backtest_repository: BacktestRepository):
        self._strategy_repository = strategy_repository
        self._trigger_repository = trigger_repository
        self._backtest_repository = backtest_repository
        self._logger = logging.getLogger(__name__)
    
    def handle(self, query: StrategyDetailQuery) -> StrategyDetailResponse:
        """전략 상세 조회 처리"""
        from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
        
        # 1. 전략 기본 정보 조회
        strategy = self._strategy_repository.find_by_id(StrategyId(query.strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {query.strategy_id}")
        
        # 2. 트리거 정보 조회 (옵션)
        triggers = []
        if query.include_triggers:
            strategy_triggers = self._trigger_repository.find_by_strategy_id(
                strategy.strategy_id
            )
            triggers = [
                {
                    "trigger_id": t.trigger_id.value,
                    "trigger_name": t.trigger_name,
                    "variable_id": t.variable.variable_id,
                    "operator": t.operator.value,
                    "target_value": t.target_value,
                    "trigger_type": t.trigger_type.value,
                    "is_active": t.is_active
                }
                for t in strategy_triggers
            ]
        
        # 3. 백테스트 히스토리 조회 (옵션)
        backtest_history = []
        if query.include_backtest_history:
            backtests = self._backtest_repository.find_by_strategy_id(
                strategy.strategy_id, limit=10
            )
            backtest_history = [
                {
                    "backtest_id": bt.backtest_id,
                    "completed_at": bt.completed_at,
                    "total_return": bt.total_return,
                    "max_drawdown": bt.max_drawdown,
                    "sharpe_ratio": bt.sharpe_ratio,
                    "total_trades": bt.total_trades
                }
                for bt in backtests
            ]
        
        # 4. 성과 지표 계산 (옵션)
        performance_metrics = {}
        if query.include_performance_metrics:
            performance_metrics = self._calculate_performance_metrics(
                strategy.strategy_id
            )
        
        return StrategyDetailResponse(
            strategy_id=strategy.strategy_id.value,
            name=strategy.name,
            description=strategy.description,
            status=strategy.status.value,
            tags=strategy.tags or [],
            triggers=triggers,
            backtest_history=backtest_history,
            performance_metrics=performance_metrics,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at
        )
    
    def _calculate_performance_metrics(self, strategy_id) -> Dict[str, Any]:
        """성과 지표 계산"""
        backtests = self._backtest_repository.find_by_strategy_id(strategy_id)
        
        if not backtests:
            return {"status": "no_data"}
        
        returns = [bt.total_return for bt in backtests if bt.total_return is not None]
        drawdowns = [bt.max_drawdown for bt in backtests if bt.max_drawdown is not None]
        
        return {
            "avg_return": sum(returns) / len(returns) if returns else 0,
            "max_return": max(returns) if returns else 0,
            "min_return": min(returns) if returns else 0,
            "avg_drawdown": sum(drawdowns) / len(drawdowns) if drawdowns else 0,
            "max_drawdown": max(drawdowns) if drawdowns else 0,
            "total_backtests": len(backtests),
            "profitable_backtests": len([r for r in returns if r > 0])
        }
```

### 6. **[새 코드 작성]** 대시보드 Query Handler 구현
- [ ] `upbit_auto_trading/application/queries/handlers/dashboard_query_handler.py` 생성:
```python
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from upbit_auto_trading.application.queries.handlers.base_query_handler import BaseQueryHandler
from upbit_auto_trading.application.queries.dto.dashboard_query_dto import (
    DashboardQuery, DashboardResponse, PerformanceMetric, TriggerStatistic
)
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
from upbit_auto_trading.domain.repositories.trigger_repository import TriggerRepository
from upbit_auto_trading.domain.repositories.backtest_repository import BacktestRepository

class DashboardQueryHandler(BaseQueryHandler[DashboardQuery, DashboardResponse]):
    """대시보드 조회 Query Handler"""
    
    def __init__(self, strategy_repository: StrategyRepository,
                 trigger_repository: TriggerRepository,
                 backtest_repository: BacktestRepository):
        self._strategy_repository = strategy_repository
        self._trigger_repository = trigger_repository
        self._backtest_repository = backtest_repository
        self._logger = logging.getLogger(__name__)
    
    def handle(self, query: DashboardQuery) -> DashboardResponse:
        """대시보드 조회 처리"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=query.date_range_days)
        
        # 1. 요약 통계 생성
        summary_stats = self._generate_summary_stats(start_date, end_date)
        
        # 2. 성과 지표 계산
        performance_metrics = []
        if query.include_performance_charts:
            performance_metrics = self._calculate_performance_metrics(start_date, end_date)
        
        # 3. 트리거 통계 생성
        trigger_statistics = []
        if query.include_trigger_stats:
            trigger_statistics = self._generate_trigger_statistics(start_date, end_date)
        
        # 4. 활성 전략 수 계산
        active_strategies_count = self._strategy_repository.count_active_strategies()
        
        # 5. 최근 백테스트 결과 조회
        recent_backtest_results = self._get_recent_backtest_results(limit=5)
        
        # 6. 시스템 상태 체크
        system_health = self._check_system_health()
        
        return DashboardResponse(
            summary_stats=summary_stats,
            performance_metrics=performance_metrics,
            trigger_statistics=trigger_statistics,
            active_strategies_count=active_strategies_count,
            recent_backtest_results=recent_backtest_results,
            system_health=system_health,
            generated_at=datetime.now()
        )
    
    def _generate_summary_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """요약 통계 생성"""
        total_strategies = self._strategy_repository.count_all_strategies()
        active_strategies = self._strategy_repository.count_active_strategies()
        total_triggers = self._trigger_repository.count_all_triggers()
        
        period_backtests = self._backtest_repository.count_backtests_in_period(
            start_date, end_date
        )
        
        return {
            "total_strategies": total_strategies,
            "active_strategies": active_strategies,
            "inactive_strategies": total_strategies - active_strategies,
            "total_triggers": total_triggers,
            "period_backtests": period_backtests,
            "strategy_utilization_rate": (active_strategies / total_strategies * 100) if total_strategies > 0 else 0
        }
    
    def _calculate_performance_metrics(self, start_date: datetime, end_date: datetime) -> List[PerformanceMetric]:
        """성과 지표 계산"""
        # 현재 기간 데이터
        current_backtests = self._backtest_repository.find_completed_in_period(
            start_date, end_date
        )
        
        # 이전 기간 데이터 (비교용)
        prev_start = start_date - timedelta(days=(end_date - start_date).days)
        prev_end = start_date
        previous_backtests = self._backtest_repository.find_completed_in_period(
            prev_start, prev_end
        )
        
        metrics = []
        
        # 평균 수익률
        current_avg_return = self._calculate_avg_return(current_backtests)
        previous_avg_return = self._calculate_avg_return(previous_backtests)
        
        metrics.append(PerformanceMetric(
            metric_name="평균 수익률",
            current_value=current_avg_return,
            previous_value=previous_avg_return,
            change_percentage=self._calculate_change_percentage(current_avg_return, previous_avg_return),
            trend=self._determine_trend(current_avg_return, previous_avg_return)
        ))
        
        # 평균 샤프 비율
        current_avg_sharpe = self._calculate_avg_sharpe(current_backtests)
        previous_avg_sharpe = self._calculate_avg_sharpe(previous_backtests)
        
        metrics.append(PerformanceMetric(
            metric_name="평균 샤프 비율",
            current_value=current_avg_sharpe,
            previous_value=previous_avg_sharpe,
            change_percentage=self._calculate_change_percentage(current_avg_sharpe, previous_avg_sharpe),
            trend=self._determine_trend(current_avg_sharpe, previous_avg_sharpe)
        ))
        
        return metrics
    
    def _generate_trigger_statistics(self, start_date: datetime, end_date: datetime) -> List[TriggerStatistic]:
        """트리거 통계 생성"""
        trigger_stats = self._trigger_repository.get_trigger_statistics_by_variable_type(
            start_date, end_date
        )
        
        statistics = []
        for stat in trigger_stats:
            statistics.append(TriggerStatistic(
                variable_type=stat["variable_type"],
                total_count=stat["total_count"],
                active_count=stat["active_count"],
                success_rate=stat["success_rate"],
                avg_execution_time_ms=stat["avg_execution_time_ms"]
            ))
        
        return statistics
    
    def _get_recent_backtest_results(self, limit: int = 5) -> List[Dict[str, Any]]:
        """최근 백테스트 결과 조회"""
        recent_backtests = self._backtest_repository.find_recent_completed(limit)
        
        results = []
        for backtest in recent_backtests:
            strategy = self._strategy_repository.find_by_id(backtest.strategy_id)
            results.append({
                "backtest_id": backtest.backtest_id,
                "strategy_name": strategy.name if strategy else "Unknown",
                "completed_at": backtest.completed_at,
                "total_return": backtest.total_return,
                "max_drawdown": backtest.max_drawdown,
                "sharpe_ratio": backtest.sharpe_ratio
            })
        
        return results
    
    def _check_system_health(self) -> Dict[str, Any]:
        """시스템 상태 체크"""
        # 기본적인 시스템 상태 지표들
        return {
            "database_status": "healthy",  # 실제로는 DB 연결 체크
            "memory_usage_percentage": 45.2,  # 실제로는 시스템 메모리 사용률
            "active_connections": 12,  # 실제로는 활성 연결 수
            "last_error_count": 0,  # 최근 24시간 에러 수
            "uptime_hours": 72.5  # 시스템 가동 시간
        }
    
    def _calculate_avg_return(self, backtests: List) -> float:
        """평균 수익률 계산"""
        returns = [bt.total_return for bt in backtests if bt.total_return is not None]
        return sum(returns) / len(returns) if returns else 0.0
    
    def _calculate_avg_sharpe(self, backtests: List) -> float:
        """평균 샤프 비율 계산"""
        sharpes = [bt.sharpe_ratio for bt in backtests if bt.sharpe_ratio is not None]
        return sum(sharpes) / len(sharpes) if sharpes else 0.0
    
    def _calculate_change_percentage(self, current: float, previous: float) -> Optional[float]:
        """변화율 계산"""
        if previous == 0:
            return None
        return ((current - previous) / previous) * 100
    
    def _determine_trend(self, current: float, previous: float) -> str:
        """트렌드 결정"""
        if previous == 0:
            return "STABLE"
        
        change = ((current - previous) / previous) * 100
        if change > 5:
            return "UP"
        elif change < -5:
            return "DOWN"
        else:
            return "STABLE"
```

### 7. **[새 코드 작성]** Query Dispatcher 구현
- [ ] `upbit_auto_trading/application/queries/query_dispatcher.py` 생성:
```python
from typing import TypeVar, Generic, Dict, Type, Any
import logging

from upbit_auto_trading.application.queries.handlers.base_query_handler import BaseQueryHandler

Q = TypeVar('Q')
R = TypeVar('R')

class QueryDispatcher:
    """Query와 Handler를 매핑하여 실행하는 디스패처"""
    
    def __init__(self):
        self._handlers: Dict[Type, BaseQueryHandler] = {}
        self._logger = logging.getLogger(__name__)
    
    def register_handler(self, query_type: Type[Q], handler: BaseQueryHandler[Q, R]) -> None:
        """Query Handler 등록"""
        self._handlers[query_type] = handler
        self._logger.debug(f"Query Handler 등록: {query_type.__name__} -> {handler.__class__.__name__}")
    
    def dispatch(self, query: Q) -> R:
        """Query 실행"""
        query_type = type(query)
        
        if query_type not in self._handlers:
            raise ValueError(f"등록되지 않은 Query 타입입니다: {query_type.__name__}")
        
        handler = self._handlers[query_type]
        
        try:
            self._logger.debug(f"Query 실행: {query_type.__name__}")
            result = handler.handle(query)
            self._logger.debug(f"Query 실행 완료: {query_type.__name__}")
            return result
        except Exception as e:
            self._logger.error(f"Query 실행 실패: {query_type.__name__} - {str(e)}")
            raise
    
    def get_registered_handlers(self) -> Dict[str, str]:
        """등록된 핸들러 목록 반환"""
        return {
            query_type.__name__: handler.__class__.__name__
            for query_type, handler in self._handlers.items()
        }
```

### 8. **[새 코드 작성]** Query Service Facade 구현
- [ ] `upbit_auto_trading/application/queries/query_service.py` 생성:
```python
from typing import List, Optional
import logging

from upbit_auto_trading.application.queries.query_dispatcher import QueryDispatcher
from upbit_auto_trading.application.queries.dto.strategy_query_dto import (
    StrategyListQuery, StrategyListResponse, StrategyDetailQuery, StrategyDetailResponse
)
from upbit_auto_trading.application.queries.dto.dashboard_query_dto import (
    DashboardQuery, DashboardResponse
)

class QueryService:
    """Query 실행을 위한 Facade 클래스"""
    
    def __init__(self, dispatcher: QueryDispatcher):
        self._dispatcher = dispatcher
        self._logger = logging.getLogger(__name__)
    
    # 전략 관련 쿼리
    def get_strategy_list(self, query: StrategyListQuery) -> StrategyListResponse:
        """전략 목록 조회"""
        return self._dispatcher.dispatch(query)
    
    def get_strategy_detail(self, strategy_id: str, 
                          include_triggers: bool = True,
                          include_backtest_history: bool = True,
                          include_performance_metrics: bool = True) -> StrategyDetailResponse:
        """전략 상세 조회"""
        query = StrategyDetailQuery(
            strategy_id=strategy_id,
            include_triggers=include_triggers,
            include_backtest_history=include_backtest_history,
            include_performance_metrics=include_performance_metrics
        )
        return self._dispatcher.dispatch(query)
    
    # 대시보드 관련 쿼리
    def get_dashboard_data(self, date_range_days: int = 30,
                          include_performance_charts: bool = True,
                          include_trigger_stats: bool = True) -> DashboardResponse:
        """대시보드 데이터 조회"""
        query = DashboardQuery(
            date_range_days=date_range_days,
            include_performance_charts=include_performance_charts,
            include_trigger_stats=include_trigger_stats
        )
        return self._dispatcher.dispatch(query)
    
    # 검색 및 필터링 편의 메서드
    def search_strategies_by_name(self, name_pattern: str, limit: int = 10) -> StrategyListResponse:
        """이름으로 전략 검색"""
        query = StrategyListQuery(
            name_search=name_pattern,
            page_size=limit,
            sort_field=StrategySortField.NAME
        )
        return self._dispatcher.dispatch(query)
    
    def get_active_strategies(self, page: int = 1, page_size: int = 20) -> StrategyListResponse:
        """활성 전략 목록 조회"""
        query = StrategyListQuery(
            status_filter="ACTIVE",
            page=page,
            page_size=page_size,
            sort_field=StrategySortField.UPDATED_AT
        )
        return self._dispatcher.dispatch(query)
    
    def get_strategies_by_tags(self, tags: List[str], page: int = 1, page_size: int = 20) -> StrategyListResponse:
        """태그별 전략 조회"""
        query = StrategyListQuery(
            tag_filter=tags,
            page=page,
            page_size=page_size
        )
        return self._dispatcher.dispatch(query)
```

### 9. **[테스트 코드 작성]** Query Handler 테스트
- [ ] `tests/application/queries/` 폴더 생성
- [ ] `tests/application/queries/test_strategy_query_handler.py` 생성:
```python
import pytest
from unittest.mock import Mock
from datetime import datetime

from upbit_auto_trading.application.queries.handlers.strategy_query_handler import StrategyListQueryHandler
from upbit_auto_trading.application.queries.dto.strategy_query_dto import StrategyListQuery, StrategySortField

class TestStrategyListQueryHandler:
    def setup_method(self):
        self.strategy_repository = Mock()
        self.backtest_repository = Mock()
        self.handler = StrategyListQueryHandler(
            self.strategy_repository,
            self.backtest_repository
        )
    
    def test_handle_strategy_list_query(self):
        # Given
        query = StrategyListQuery(
            page=1,
            page_size=10,
            sort_field=StrategySortField.CREATED_AT
        )
        
        mock_strategies = [Mock()]
        mock_strategies[0].strategy_id.value = "TEST_001"
        mock_strategies[0].name = "테스트 전략"
        mock_strategies[0].status.value = "ACTIVE"
        mock_strategies[0].tags = ["test"]
        mock_strategies[0].entry_triggers = []
        mock_strategies[0].exit_triggers = []
        mock_strategies[0].created_at = datetime.now()
        mock_strategies[0].updated_at = datetime.now()
        
        self.strategy_repository.find_with_filters.return_value = mock_strategies
        self.strategy_repository.count_with_filters.return_value = 1
        self.backtest_repository.find_latest_by_strategy.return_value = None
        
        # When
        result = self.handler.handle(query)
        
        # Then
        assert len(result.items) == 1
        assert result.items[0].name == "테스트 전략"
        assert result.total_count == 1
    
    def test_validate_query_invalid_page(self):
        # Given
        query = StrategyListQuery(page=0)
        
        # When & Then
        with pytest.raises(ValueError, match="페이지 번호는 1 이상이어야 합니다"):
            self.handler.validate_query(query)
```

### 10. **[통합]** Query Service Container 구성
- [ ] `upbit_auto_trading/application/queries/query_container.py` 생성:
```python
from upbit_auto_trading.application.queries.query_dispatcher import QueryDispatcher
from upbit_auto_trading.application.queries.query_service import QueryService
from upbit_auto_trading.application.queries.handlers.strategy_query_handler import (
    StrategyListQueryHandler, StrategyDetailQueryHandler
)
from upbit_auto_trading.application.queries.handlers.dashboard_query_handler import DashboardQueryHandler
from upbit_auto_trading.application.queries.dto.strategy_query_dto import (
    StrategyListQuery, StrategyDetailQuery
)
from upbit_auto_trading.application.queries.dto.dashboard_query_dto import DashboardQuery

class QueryServiceContainer:
    """Query Service들의 의존성 주입 컨테이너"""
    
    def __init__(self, repository_container):
        self._repo_container = repository_container
        self._dispatcher = None
        self._query_service = None
    
    def get_query_service(self) -> QueryService:
        """Query Service 반환"""
        if self._query_service is None:
            self._query_service = QueryService(self.get_dispatcher())
        return self._query_service
    
    def get_dispatcher(self) -> QueryDispatcher:
        """Query Dispatcher 반환"""
        if self._dispatcher is None:
            self._dispatcher = self._create_dispatcher()
        return self._dispatcher
    
    def _create_dispatcher(self) -> QueryDispatcher:
        """Query Dispatcher 생성 및 핸들러 등록"""
        dispatcher = QueryDispatcher()
        
        # Strategy Query Handlers 등록
        strategy_list_handler = StrategyListQueryHandler(
            self._repo_container.get_strategy_repository(),
            self._repo_container.get_backtest_repository()
        )
        dispatcher.register_handler(StrategyListQuery, strategy_list_handler)
        
        strategy_detail_handler = StrategyDetailQueryHandler(
            self._repo_container.get_strategy_repository(),
            self._repo_container.get_trigger_repository(),
            self._repo_container.get_backtest_repository()
        )
        dispatcher.register_handler(StrategyDetailQuery, strategy_detail_handler)
        
        # Dashboard Query Handler 등록
        dashboard_handler = DashboardQueryHandler(
            self._repo_container.get_strategy_repository(),
            self._repo_container.get_trigger_repository(),
            self._repo_container.get_backtest_repository()
        )
        dispatcher.register_handler(DashboardQuery, dashboard_handler)
        
        return dispatcher
```

## Verification Criteria (완료 검증 조건)

### **[Query Handler 검증]** 모든 Query Handler 구현 확인
- [ ] `pytest tests/application/queries/ -v` 실행하여 모든 테스트 통과
- [ ] 각 Query Handler의 성능이 적절한지 확인 (복잡한 쿼리 1초 이내)

### **[CQRS 분리 검증]** Command와 Query 책임 분리 확인
- [ ] Python REPL에서 Query Service 테스트:
```python
from upbit_auto_trading.application.queries.query_service import QueryService
from upbit_auto_trading.application.queries.dto.strategy_query_dto import StrategyListQuery

# Query Service 생성 (실제로는 Container에서)
query_service = QueryService(dispatcher)

# 전략 목록 조회 테스트
query = StrategyListQuery(page=1, page_size=5)
result = query_service.get_strategy_list(query)

print(f"조회된 전략 수: {len(result.items)}")
print("✅ CQRS Query 검증 완료")
```

### **[성능 검증]** Query 응답 시간 확인
- [ ] 대용량 데이터 상황에서 Query 성능 테스트
- [ ] 페이징 처리가 올바르게 동작하는지 확인

### **[통합 검증]** Query Dispatcher와 Service 연동 확인
- [ ] QueryServiceContainer를 통한 전체 Query 플로우 테스트

## Notes (주의사항)
- Query는 데이터 변경 없이 읽기 전용으로만 동작해야 함
- Repository에 복잡한 필터링 메서드 추가 필요 (Infrastructure Layer에서 구현)
- 성능 최적화를 위해 캐싱 전략 고려 (향후 Infrastructure Layer에서)
- Query DTO는 UI 요구사항에 최적화된 구조로 설계
