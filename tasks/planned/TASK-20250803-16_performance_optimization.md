# TASK-20250803-16

## Title
Performance Optimization - Clean Architecture 성능 최적화 및 모니터링

## Objective (목표)
Clean Architecture 구현으로 인한 계층 간 오버헤드를 최소화하고, 백테스팅 성능을 기존 수준(1년 분봉 5분 내)으로 유지하면서 시스템 전반의 성능을 최적화합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 5: 통합 테스트 및 최적화 (2주)" > "5.2 성능 최적화 (1주)"

## Pre-requisites (선행 조건)
- `TASK-20250803-15`: 시스템 통합 테스트 완료
- Clean Architecture 전 계층 구현 완료
- 성능 벤치마크 기준 데이터 수집 완료

## Detailed Steps (상세 실행 절차)

### 1. **[분석]** 성능 병목점 식별
- [ ] `tools/performance_profiler.py` 생성:
```python
import cProfile
import pstats
import time
from functools import wraps
from typing import Dict, List
import psutil
import memory_profiler

class PerformanceProfiler:
    """성능 프로파일링 도구"""
    
    def __init__(self):
        self._results: Dict[str, Dict] = {}
    
    def profile_method(self, method_name: str):
        """메소드 성능 프로파일링 데코레이터"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss
                
                # CPU 프로파일링
                pr = cProfile.Profile()
                pr.enable()
                
                result = func(*args, **kwargs)
                
                pr.disable()
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss
                
                # 결과 저장
                self._results[method_name] = {
                    "execution_time": end_time - start_time,
                    "memory_delta": (end_memory - start_memory) / 1024 / 1024,  # MB
                    "cpu_stats": pstats.Stats(pr)
                }
                
                return result
            return wrapper
        return decorator
    
    def analyze_backtest_performance(self, strategy_id: str) -> Dict:
        """백테스팅 성능 분석"""
        return self._profile_backtest_workflow(strategy_id)
```

- [ ] 핵심 성능 지표 측정:
```python
class PerformanceBenchmark:
    """성능 벤치마크 측정"""
    
    PERFORMANCE_TARGETS = {
        "strategy_creation": 0.1,      # 100ms 이하
        "trigger_validation": 0.05,    # 50ms 이하
        "backtest_1year": 300.0,       # 5분 이하
        "ui_response": 0.1,            # 100ms 이하
        "memory_usage": 500.0          # 500MB 이하
    }
    
    def measure_strategy_creation_performance(self) -> float:
        """전략 생성 성능 측정"""
        
    def measure_backtest_performance(self) -> Dict[str, float]:
        """백테스팅 성능 측정"""
        
    def measure_ui_responsiveness(self) -> Dict[str, float]:
        """UI 응답성 측정"""
```

### 2. **[최적화]** Repository 계층 성능 개선
- [ ] 데이터베이스 연결 풀링:
```python
# 파일: infrastructure/database/connection_pool.py
import sqlite3
from threading import Lock
from typing import Dict, List
from contextlib import contextmanager

class DatabaseConnectionPool:
    """SQLite 연결 풀 관리"""
    
    def __init__(self, db_paths: Dict[str, str], pool_size: int = 10):
        self._pools: Dict[str, List[sqlite3.Connection]] = {}
        self._locks: Dict[str, Lock] = {}
        self._db_paths = db_paths
        self._pool_size = pool_size
        self._initialize_pools()
    
    def _initialize_pools(self):
        """연결 풀 초기화"""
        for db_name, db_path in self._db_paths.items():
            self._pools[db_name] = []
            self._locks[db_name] = Lock()
            
            # WAL 모드 활성화로 읽기 성능 향상
            for _ in range(self._pool_size):
                conn = sqlite3.connect(db_path, check_same_thread=False)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=memory")
                self._pools[db_name].append(conn)
    
    @contextmanager
    def get_connection(self, db_name: str):
        """연결 풀에서 연결 획득"""
        with self._locks[db_name]:
            if self._pools[db_name]:
                conn = self._pools[db_name].pop()
            else:
                # 풀이 비어있으면 새 연결 생성
                conn = sqlite3.connect(self._db_paths[db_name])
        
        try:
            yield conn
        finally:
            with self._locks[db_name]:
                if len(self._pools[db_name]) < self._pool_size:
                    self._pools[db_name].append(conn)
                else:
                    conn.close()
```

- [ ] 배치 처리 최적화:
```python
# 파일: infrastructure/repositories/optimized_strategy_repository.py
class OptimizedStrategyRepository(StrategyRepository):
    """성능 최적화된 전략 Repository"""
    
    def save_batch(self, strategies: List[Strategy]) -> None:
        """배치 저장으로 성능 향상"""
        with self._connection_pool.get_connection('strategies') as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                # 전략 메인 데이터 배치 삽입
                strategy_data = [(s.strategy_id.value, s.name, s.created_at) 
                               for s in strategies]
                conn.executemany(
                    "INSERT INTO strategies (id, name, created_at) VALUES (?, ?, ?)",
                    strategy_data
                )
                
                # 트리거 데이터 배치 삽입
                trigger_data = []
                for strategy in strategies:
                    for trigger in strategy.get_all_triggers():
                        trigger_data.append(trigger.to_database_params())
                
                conn.executemany(
                    "INSERT INTO strategy_triggers (strategy_id, trigger_id, ...) VALUES (?, ?, ...)",
                    trigger_data
                )
                
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
    
    def find_strategies_optimized(self, query: StrategyQuery) -> List[Strategy]:
        """최적화된 전략 조회"""
        # 인덱스 활용한 쿼리 최적화
        # Lazy loading으로 메모리 사용량 최소화
```

### 3. **[최적화]** Application 계층 성능 개선
- [ ] 캐싱 시스템 구현:
```python
# 파일: application/caching/strategy_cache.py
from functools import lru_cache
import asyncio
from typing import Optional, Dict, Any

class StrategyCache:
    """전략 관련 데이터 캐싱"""
    
    def __init__(self, ttl_seconds: int = 300):  # 5분 TTL
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
    
    @lru_cache(maxsize=1000)
    def get_trading_variables(self) -> List[TradingVariable]:
        """매매 변수 캐싱 (자주 변경되지 않는 데이터)"""
        return self._settings_repo.get_trading_variables()
    
    async def get_strategy_with_cache(self, strategy_id: str) -> Optional[Strategy]:
        """전략 데이터 캐시된 조회"""
        cache_key = f"strategy:{strategy_id}"
        
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self._ttl:
                return cache_entry['data']
        
        # 캐시 미스 시 Repository에서 조회
        strategy = await self._strategy_repo.find_by_id(strategy_id)
        self._cache[cache_key] = {
            'data': strategy,
            'timestamp': time.time()
        }
        
        return strategy
```

- [ ] 비동기 처리 최적화:
```python
# 파일: application/services/async_backtest_service.py
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncBacktestService:
    """비동기 백테스팅 서비스"""
    
    def __init__(self, thread_pool_size: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=thread_pool_size)
    
    async def run_backtest_async(self, command: BacktestCommand) -> BacktestResult:
        """백테스팅 비동기 실행"""
        # CPU 집약적 작업을 별도 스레드에서 실행
        loop = asyncio.get_event_loop()
        
        # 데이터 로딩을 병렬로 처리
        market_data_task = loop.run_in_executor(
            self._executor, 
            self._load_market_data, 
            command.symbol, command.start_date, command.end_date
        )
        
        strategy_task = loop.run_in_executor(
            self._executor,
            self._load_strategy,
            command.strategy_id
        )
        
        market_data, strategy = await asyncio.gather(market_data_task, strategy_task)
        
        # 백테스팅 실행
        result = await loop.run_in_executor(
            self._executor,
            self._execute_backtest,
            strategy, market_data
        )
        
        return result
```

### 4. **[최적화]** 메모리 사용량 최적화
- [ ] 메모리 효율적인 데이터 처리:
```python
# 파일: infrastructure/data_processing/memory_efficient_processor.py
import pandas as pd
from typing import Iterator, Chunk

class MemoryEfficientDataProcessor:
    """메모리 효율적인 데이터 처리"""
    
    def __init__(self, chunk_size: int = 10000):
        self._chunk_size = chunk_size
    
    def process_large_dataset(self, data_source: str) -> Iterator[pd.DataFrame]:
        """대용량 데이터를 청크 단위로 처리"""
        for chunk in pd.read_csv(data_source, chunksize=self._chunk_size):
            # 메모리 사용량 최소화를 위한 처리
            chunk = chunk.dropna()
            chunk = self._optimize_dtypes(chunk)
            yield chunk
    
    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 타입 최적화로 메모리 사용량 감소"""
        for col in df.columns:
            if df[col].dtype == 'int64':
                if df[col].min() >= 0 and df[col].max() <= 255:
                    df[col] = df[col].astype('uint8')
                elif df[col].min() >= -128 and df[col].max() <= 127:
                    df[col] = df[col].astype('int8')
        return df
```

- [ ] 객체 생명주기 관리:
```python
# 파일: shared/memory_management/object_pool.py
from typing import TypeVar, Generic, List, Callable
import weakref

T = TypeVar('T')

class ObjectPool(Generic[T]):
    """객체 풀로 메모리 할당 최적화"""
    
    def __init__(self, factory: Callable[[], T], max_size: int = 100):
        self._factory = factory
        self._pool: List[T] = []
        self._max_size = max_size
    
    def acquire(self) -> T:
        """객체 획득"""
        if self._pool:
            return self._pool.pop()
        return self._factory()
    
    def release(self, obj: T) -> None:
        """객체 반환"""
        if len(self._pool) < self._max_size:
            # 객체 상태 초기화
            if hasattr(obj, 'reset'):
                obj.reset()
            self._pool.append(obj)

# 사용 예시
trigger_pool = ObjectPool(lambda: Trigger.create_empty(), max_size=50)
```

### 5. **[최적화]** UI 성능 개선
- [ ] 지연 로딩 및 가상화:
```python
# 파일: presentation/desktop/components/virtualized_list.py
from PyQt6.QtWidgets import QAbstractItemView, QStyledItemDelegate
from PyQt6.QtCore import QAbstractItemModel, QModelIndex

class VirtualizedStrategyListModel(QAbstractItemModel):
    """가상화된 전략 목록 모델"""
    
    def __init__(self, strategy_service: StrategyApplicationService):
        super().__init__()
        self._strategy_service = strategy_service
        self._cache: Dict[int, StrategyDto] = {}
        self._total_count = 0
    
    def rowCount(self, parent=QModelIndex()) -> int:
        if self._total_count == 0:
            self._total_count = self._strategy_service.get_strategy_count()
        return self._total_count
    
    def data(self, index: QModelIndex, role: int):
        """지연 로딩으로 필요한 데이터만 조회"""
        row = index.row()
        
        if row not in self._cache:
            # 현재 보이는 범위의 데이터만 로드
            start_idx = max(0, row - 10)
            end_idx = min(self._total_count, row + 10)
            
            strategies = self._strategy_service.get_strategies_range(start_idx, end_idx)
            for i, strategy in enumerate(strategies):
                self._cache[start_idx + i] = strategy
        
        return self._cache.get(row)
```

- [ ] 차트 렌더링 최적화:
```python
# 파일: presentation/desktop/components/optimized_chart.py
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

class OptimizedChartWidget(FigureCanvasQTAgg):
    """최적화된 차트 위젯"""
    
    def __init__(self):
        self.figure = plt.figure(figsize=(8, 6))
        super().__init__(self.figure)
        
        # 렌더링 최적화 설정
        self.figure.set_facecolor('white')
        self.setStyleSheet("background-color: white;")
        
        # 애니메이션 비활성화로 성능 향상
        plt.ioff()
    
    def update_chart_optimized(self, data: ChartData):
        """최적화된 차트 업데이트"""
        # 데이터 다운샘플링으로 렌더링 부하 감소
        if len(data.timestamps) > 1000:
            step = len(data.timestamps) // 1000
            data = data.downsample(step)
        
        # 부분 업데이트로 전체 재렌더링 방지
        if hasattr(self, '_last_update_time'):
            time_diff = time.time() - self._last_update_time
            if time_diff < 0.1:  # 100ms 내 중복 업데이트 방지
                return
        
        self._render_chart(data)
        self._last_update_time = time.time()
```

### 6. **[모니터링]** 성능 모니터링 시스템
- [ ] 실시간 성능 모니터:
```python
# 파일: shared/monitoring/performance_monitor.py
import time
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class PerformanceMetrics:
    """성능 지표 데이터"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    active_threads: int
    response_times: Dict[str, float]

class PerformanceMonitor:
    """실시간 성능 모니터링"""
    
    def __init__(self, sampling_interval: float = 1.0):
        self._sampling_interval = sampling_interval
        self._metrics_history: List[PerformanceMetrics] = []
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def start_monitoring(self):
        """모니터링 시작"""
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.start()
    
    def _monitor_loop(self):
        """모니터링 루프"""
        while self._monitoring:
            metrics = self._collect_metrics()
            self._metrics_history.append(metrics)
            
            # 성능 임계치 체크
            if self._check_performance_thresholds(metrics):
                self._trigger_performance_alert(metrics)
            
            time.sleep(self._sampling_interval)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        if not self._metrics_history:
            return {}
        
        recent_metrics = self._metrics_history[-60:]  # 최근 1분
        
        return {
            "avg_cpu_usage": sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
            "avg_memory_usage": sum(m.memory_usage for m in recent_metrics) / len(recent_metrics),
            "max_response_time": max(max(m.response_times.values()) for m in recent_metrics),
            "performance_score": self._calculate_performance_score(recent_metrics)
        }
```

### 7. **[검증]** 성능 개선 효과 측정
- [ ] 성능 비교 테스트:
```python
# 파일: tests/performance/test_optimization_results.py
class OptimizationEffectivenessTest:
    """최적화 효과 검증 테스트"""
    
    def test_strategy_creation_performance_improvement(self):
        """전략 생성 성능 개선 검증"""
        # Before: 기존 구현 성능 측정
        old_time = self._measure_old_strategy_creation()
        
        # After: 최적화된 구현 성능 측정
        new_time = self._measure_new_strategy_creation()
        
        # 개선율 검증 (최소 20% 개선 목표)
        improvement = (old_time - new_time) / old_time
        assert improvement >= 0.20, f"성능 개선 부족: {improvement:.2%}"
    
    def test_backtest_memory_optimization(self):
        """백테스팅 메모리 사용량 최적화 검증"""
        # 1년 백테스팅 메모리 사용량 측정
        initial_memory = psutil.Process().memory_info().rss
        
        self._run_optimized_backtest()
        
        peak_memory = psutil.Process().memory_info().rss
        memory_usage = (peak_memory - initial_memory) / 1024 / 1024  # MB
        
        # 메모리 사용량 500MB 이하 검증
        assert memory_usage < 500, f"메모리 사용량 초과: {memory_usage:.1f}MB"
```

## Verification Criteria (완료 검증 조건)

### **[성능 목표 달성]**
- [ ] 전략 생성 시간: 100ms 이하
- [ ] 백테스팅 성능: 1년 분봉 5분 내 유지
- [ ] UI 응답성: 100ms 이하
- [ ] 메모리 사용량: 500MB 이하

### **[시스템 안정성]**
- [ ] 장시간 실행 시 메모리 누수 없음
- [ ] 동시 요청 처리 시 성능 저하 20% 이하
- [ ] 피크 시간대 CPU 사용률 80% 이하

### **[최적화 효과]**
- [ ] 기존 대비 응답 시간 20% 이상 개선
- [ ] 메모리 효율성 30% 이상 개선
- [ ] 데이터베이스 쿼리 성능 40% 이상 개선

## Notes (주의사항)
- 최적화 작업 전후 반드시 성능 벤치마크 실행
- 메모리 프로파일링으로 누수 지점 정확히 파악
- UI 최적화 시 사용자 경험 저하 없도록 주의
