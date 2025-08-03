# ⚡ 성능 최적화 가이드

> **목적**: Clean Architecture에서 성능 병목점 해결 및 최적화  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 🎯 성능 최적화 개요

### 계층별 성능 포인트
```
🎨 Presentation  → UI 응답성 (렌더링, 이벤트 처리)
⚙️ Application   → 서비스 처리 속도 (배치, 캐싱)
💎 Domain        → 비즈니스 로직 효율성 (알고리즘)
🔌 Infrastructure → DB/API 접근 최적화 (쿼리, 네트워크)
```

### 성능 측정 기준
- **UI 응답성**: 사용자 입력 후 100ms 내 반응
- **백테스팅**: 1년 분봉 데이터 5분 내 처리
- **실시간 데이터**: 1초 내 시장 데이터 갱신
- **메모리 사용량**: 시스템 메모리의 30% 이하 점유

## 🎨 Presentation Layer 최적화

### UI 렌더링 최적화
```python
class OptimizedChartWidget(QWidget):
    """최적화된 차트 위젯"""
    def __init__(self):
        super().__init__()
        self._data_cache = {}
        self._render_timer = QTimer()
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._do_render)
        
    def update_data(self, new_data):
        """데이터 업데이트 - 렌더링 지연"""
        self._pending_data = new_data
        
        # 100ms 내 추가 업데이트가 있으면 렌더링 지연
        self._render_timer.start(100)
        
    def _do_render(self):
        """실제 렌더링 수행"""
        if hasattr(self, '_pending_data'):
            self._render_chart(self._pending_data)
            delattr(self, '_pending_data')

class LazyLoadingListWidget(QListWidget):
    """지연 로딩 리스트 위젯"""
    def __init__(self):
        super().__init__()
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self._loaded_items = set()
        
    def _on_scroll(self, value):
        """스크롤 시 보이는 항목만 로딩"""
        visible_range = self._get_visible_range()
        for index in visible_range:
            if index not in self._loaded_items:
                self._load_item(index)
                self._loaded_items.add(index)
```

### 이벤트 처리 최적화
```python
class OptimizedPresenter:
    """이벤트 배칭으로 성능 향상"""
    def __init__(self, view, service):
        self.view = view
        self.service = service
        self._event_batch = []
        self._batch_timer = QTimer()
        self._batch_timer.setSingleShot(True)
        self._batch_timer.timeout.connect(self._process_batch)
        
    def on_parameter_changed(self, param_name, value):
        """파라미터 변경 이벤트 배칭"""
        self._event_batch.append((param_name, value))
        
        # 50ms 내 추가 변경이 없으면 일괄 처리
        self._batch_timer.start(50)
        
    def _process_batch(self):
        """배치된 이벤트 일괄 처리"""
        if self._event_batch:
            self.service.update_parameters(dict(self._event_batch))
            self._event_batch.clear()
```

## ⚙️ Application Layer 최적화

### 서비스 레벨 캐싱
```python
from functools import lru_cache
from typing import Dict, Any
import hashlib

class CachedTriggerService:
    """트리거 서비스 캐싱"""
    def __init__(self, variable_repo, cache_size=128):
        self.variable_repo = variable_repo
        self._cache: Dict[str, Any] = {}
        self.cache_size = cache_size
        
    @lru_cache(maxsize=64)
    def get_compatible_variables(self, base_variable_id: str) -> List[str]:
        """호환 변수 목록 캐싱"""
        base_variable = self.variable_repo.get_by_id(base_variable_id)
        compatible = []
        
        for variable in self.variable_repo.get_all():
            if self._is_compatible(base_variable, variable):
                compatible.append(variable.id)
                
        return compatible
        
    def _cache_key(self, *args) -> str:
        """캐시 키 생성"""
        key_string = "|".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()
        
    def invalidate_cache(self, pattern: str = None):
        """캐시 무효화"""
        if pattern:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            self._cache.clear()
            self.get_compatible_variables.cache_clear()
```

### 배치 처리 패턴
```python
class BatchStrategyService:
    """전략 서비스 배치 처리"""
    def __init__(self, strategy_repo):
        self.strategy_repo = strategy_repo
        self._pending_saves: List[Strategy] = []
        self._save_timer = Timer(1.0, self._flush_saves)
        
    def save_strategy(self, strategy: Strategy):
        """전략 저장 배치 처리"""
        self._pending_saves.append(strategy)
        
        # 1초 후 또는 10개 누적되면 일괄 저장
        if len(self._pending_saves) >= 10:
            self._flush_saves()
        else:
            self._restart_timer()
            
    def _flush_saves(self):
        """배치 저장 실행"""
        if self._pending_saves:
            self.strategy_repo.save_batch(self._pending_saves)
            self._pending_saves.clear()
            
    def _restart_timer(self):
        """타이머 재시작"""
        if self._save_timer.is_alive():
            self._save_timer.cancel()
        self._save_timer = Timer(1.0, self._flush_saves)
        self._save_timer.start()
```

## 💎 Domain Layer 최적화

### 알고리즘 최적화
```python
class OptimizedStrategy:
    """최적화된 전략 Domain Logic"""
    def __init__(self):
        self._rule_cache = {}
        self._evaluation_cache = {}
        
    def evaluate_conditions(self, market_data: MarketData) -> bool:
        """조건 평가 최적화"""
        # 캐시 키 생성
        cache_key = f"{market_data.timestamp}_{market_data.symbol}"
        
        if cache_key in self._evaluation_cache:
            return self._evaluation_cache[cache_key]
            
        # 조건들을 빠른 것부터 평가 (Short-circuit)
        sorted_conditions = sorted(self.conditions, key=lambda c: c.complexity)
        
        result = True
        for condition in sorted_conditions:
            if not condition.evaluate(market_data):
                result = False
                break  # AND 조건에서 하나라도 False면 즉시 중단
                
        # 결과 캐싱
        self._evaluation_cache[cache_key] = result
        return result
        
    def optimize_rule_order(self):
        """규칙 실행 순서 최적화"""
        # 실행 시간이 짧은 규칙부터 배치
        self.rules.sort(key=lambda rule: rule.estimated_execution_time)
```

### 값 객체 최적화
```python
from dataclasses import dataclass
from functools import cached_property

@dataclass(frozen=True, slots=True)
class OptimizedMarketData:
    """최적화된 시장 데이터 값 객체"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    @cached_property
    def price_change(self) -> float:
        """가격 변화율 지연 계산"""
        return (self.close - self.open) / self.open * 100
        
    @cached_property
    def volatility(self) -> float:
        """변동성 지연 계산"""
        return (self.high - self.low) / self.close * 100
```

## 🔌 Infrastructure Layer 최적화

### 데이터베이스 최적화
```python
class OptimizedStrategyRepository:
    """최적화된 전략 리포지토리"""
    def __init__(self, db_connection):
        self.db = db_connection
        self._setup_connection_pool()
        
    def _setup_connection_pool(self):
        """커넥션 풀 설정"""
        self.db.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        self.db.execute("PRAGMA synchronous=NORMAL")  # 동기화 수준 조정
        self.db.execute("PRAGMA cache_size=-2000")    # 2MB 캐시
        self.db.execute("PRAGMA temp_store=MEMORY")   # 임시 데이터 메모리 저장
        
    def get_strategies_with_rules(self, limit: int = 100) -> List[Strategy]:
        """JOIN을 사용한 효율적 조회"""
        query = """
        SELECT s.*, r.id as rule_id, r.type, r.parameters
        FROM strategies s
        LEFT JOIN strategy_rules r ON s.id = r.strategy_id
        ORDER BY s.created_at DESC
        LIMIT ?
        """
        
        rows = self.db.execute(query, (limit,)).fetchall()
        return self._build_strategies_from_rows(rows)
        
    def save_batch(self, strategies: List[Strategy]):
        """배치 저장으로 성능 향상"""
        with self.db.transaction():
            for strategy in strategies:
                self._save_single_strategy(strategy)
                
    def _build_strategies_from_rows(self, rows) -> List[Strategy]:
        """쿼리 결과를 Strategy 객체로 효율적 변환"""
        strategies_dict = {}
        
        for row in rows:
            strategy_id = row['id']
            if strategy_id not in strategies_dict:
                strategy = Strategy(row['name'])
                strategy.id = strategy_id
                strategies_dict[strategy_id] = strategy
                
            if row['rule_id']:
                rule = TradingRule(row['type'], row['parameters'])
                strategies_dict[strategy_id].add_rule(rule)
                
        return list(strategies_dict.values())
```

### API 호출 최적화
```python
import asyncio
import aiohttp
from typing import List, Dict

class OptimizedMarketDataService:
    """최적화된 시장 데이터 서비스"""
    def __init__(self):
        self._session = None
        self._rate_limiter = asyncio.Semaphore(10)  # 동시 요청 제한
        
    async def get_multiple_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """여러 심볼 동시 조회"""
        if not self._session:
            self._session = aiohttp.ClientSession()
            
        tasks = []
        for symbol in symbols:
            task = self._get_single_market_data(symbol)
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            symbol: result for symbol, result in zip(symbols, results)
            if not isinstance(result, Exception)
        }
        
    async def _get_single_market_data(self, symbol: str) -> MarketData:
        """단일 심볼 조회 (레이트 리미터 적용)"""
        async with self._rate_limiter:
            url = f"https://api.upbit.com/v1/ticker?markets={symbol}"
            
            async with self._session.get(url) as response:
                data = await response.json()
                return MarketData.from_api_response(data[0])
```

## 📊 메모리 최적화

### 메모리 사용량 모니터링
```python
import psutil
import gc
from typing import Optional

class MemoryMonitor:
    """메모리 사용량 모니터링"""
    def __init__(self, warning_threshold=70, critical_threshold=85):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        
    def get_memory_usage(self) -> float:
        """현재 메모리 사용률 반환"""
        return psutil.virtual_memory().percent
        
    def check_memory_pressure(self) -> Optional[str]:
        """메모리 압박 상황 체크"""
        usage = self.get_memory_usage()
        
        if usage >= self.critical_threshold:
            return "critical"
        elif usage >= self.warning_threshold:
            return "warning"
        return None
        
    def trigger_cleanup(self):
        """메모리 정리 트리거"""
        # 가비지 컬렉션 강제 실행
        collected = gc.collect()
        print(f"🗑️ 가비지 컬렉션: {collected}개 객체 정리")
        
        # 캐시 정리
        self._clear_caches()
        
    def _clear_caches(self):
        """각종 캐시 정리"""
        # LRU 캐시 정리
        for obj in gc.get_objects():
            if hasattr(obj, 'cache_clear'):
                obj.cache_clear()
```

### 객체 풀링
```python
class MarketDataPool:
    """MarketData 객체 풀링"""
    def __init__(self, pool_size=100):
        self._pool: List[MarketData] = []
        self._pool_size = pool_size
        self._in_use: Set[MarketData] = set()
        
    def get_instance(self) -> MarketData:
        """풀에서 객체 가져오기"""
        if self._pool:
            instance = self._pool.pop()
        else:
            instance = MarketData.__new__(MarketData)
            
        self._in_use.add(instance)
        return instance
        
    def return_instance(self, instance: MarketData):
        """풀에 객체 반환"""
        if instance in self._in_use:
            self._in_use.remove(instance)
            
            if len(self._pool) < self._pool_size:
                instance._reset()  # 객체 초기화
                self._pool.append(instance)
```

## 🚀 프로파일링 및 측정

### 성능 프로파일러
```python
import time
import functools
from typing import Dict, List

class PerformanceProfiler:
    """성능 프로파일러"""
    def __init__(self):
        self.timings: Dict[str, List[float]] = {}
        
    def profile(self, name: str):
        """함수 실행 시간 측정 데코레이터"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    execution_time = time.perf_counter() - start_time
                    self.record_timing(name, execution_time)
            return wrapper
        return decorator
        
    def record_timing(self, name: str, execution_time: float):
        """실행 시간 기록"""
        if name not in self.timings:
            self.timings[name] = []
        self.timings[name].append(execution_time)
        
    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """통계 정보 반환"""
        stats = {}
        for name, times in self.timings.items():
            stats[name] = {
                'count': len(times),
                'total': sum(times),
                'average': sum(times) / len(times),
                'min': min(times),
                'max': max(times)
            }
        return stats

# 사용 예시
profiler = PerformanceProfiler()

@profiler.profile('strategy_evaluation')
def evaluate_strategy(strategy, market_data):
    return strategy.evaluate(market_data)
```

### 병목점 탐지
```python
class BottleneckDetector:
    """병목점 자동 탐지"""
    def __init__(self, threshold_ms=100):
        self.threshold_ms = threshold_ms
        self.slow_operations: List[Dict] = []
        
    def detect_slow_operation(self, operation_name: str, execution_time: float):
        """느린 작업 탐지"""
        if execution_time * 1000 > self.threshold_ms:
            self.slow_operations.append({
                'operation': operation_name,
                'time_ms': execution_time * 1000,
                'timestamp': datetime.now()
            })
            
            print(f"⚠️ 병목점 탐지: {operation_name} ({execution_time*1000:.1f}ms)")
            
    def get_top_bottlenecks(self, limit=10) -> List[Dict]:
        """주요 병목점 반환"""
        return sorted(
            self.slow_operations,
            key=lambda x: x['time_ms'],
            reverse=True
        )[:limit]
```

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): 전체 아키텍처와 성능 고려사항
- [이벤트 시스템](08_EVENT_SYSTEM.md): 이벤트 처리 성능 최적화
- [상태 관리](07_STATE_MANAGEMENT.md): 상태 캐싱과 성능
- [문제 해결](06_TROUBLESHOOTING.md): 성능 문제 디버깅

---
**💡 핵심**: "측정 없이는 최적화 없다! 프로파일링으로 실제 병목점을 찾아 해결하세요!"
