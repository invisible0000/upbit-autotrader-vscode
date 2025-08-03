# ⚡ 성능 최적화 가이드

> **목적**: Clean Architecture에서 성능 병목점 해결 및 최적화  
> **대상**: 개발자, 성능 엔지니어  
> **예상 읽기 시간**: 16분

## 🎯 성능 최적화 전략

### 📊 계층별 성능 포인트
```
Domain Layer      ← 비즈니스 로직 최적화 (알고리즘, 메모리)
Application Layer ← 유스케이스 흐름 최적화 (캐싱, 배치)
Infrastructure    ← I/O 최적화 (DB, API, 파일)
Presentation      ← UI 응답성 최적화 (비동기, 렌더링)
```

## 💎 Domain Layer 최적화

### 1. 비즈니스 로직 최적화
```python
# domain/entities/trading_condition.py
class TradingCondition:
    """최적화된 거래 조건"""
    
    def __init__(self):
        # ✅ 계산 결과 캐싱
        self._evaluation_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 60  # 60초 TTL
    
    def evaluate(self, market_data: MarketData) -> bool:
        """조건 평가 - 캐싱 적용"""
        
        # 캐시 키 생성 (데이터 해시 기반)
        cache_key = self._generate_cache_key(market_data)
        current_time = datetime.utcnow()
        
        # 캐시 확인
        if (cache_key in self._evaluation_cache and 
            self._cache_timestamp and
            (current_time - self._cache_timestamp).seconds < self._cache_ttl):
            return self._evaluation_cache[cache_key]
        
        # 실제 계산 수행
        result = self._perform_evaluation(market_data)
        
        # 캐시 저장
        self._evaluation_cache[cache_key] = result
        self._cache_timestamp = current_time
        
        return result
    
    def _generate_cache_key(self, market_data: MarketData) -> str:
        """캐시 키 생성"""
        # 중요한 데이터만 해싱하여 키 생성
        key_data = f"{market_data.symbol}_{market_data.timestamp}_{market_data.close_price}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _perform_evaluation(self, market_data: MarketData) -> bool:
        """실제 조건 평가 로직"""
        # 비즈니스 로직 구현
        pass

# domain/services/indicator_calculation_service.py
class IndicatorCalculationService:
    """지표 계산 서비스 - 메모리 최적화"""
    
    def __init__(self):
        # ✅ 순환 버퍼로 메모리 사용량 제한
        self._price_buffer = collections.deque(maxlen=1000)
        self._indicator_cache = LRUCache(maxsize=100)
    
    def calculate_sma(self, prices: List[float], period: int) -> float:
        """SMA 계산 - 최적화 버전"""
        
        # 캐시 확인
        cache_key = f"sma_{period}_{hash(tuple(prices[-period:]))}"
        if cache_key in self._indicator_cache:
            return self._indicator_cache[cache_key]
        
        # 효율적인 계산 (numpy 활용)
        if len(prices) < period:
            return None
        
        # ✅ numpy로 벡터화 연산
        import numpy as np
        result = np.mean(prices[-period:])
        
        # 캐시 저장
        self._indicator_cache[cache_key] = result
        return result
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """RSI 계산 - 메모리 효율적 버전"""
        if len(prices) < period + 1:
            return None
        
        # ✅ 증분 계산으로 전체 재계산 방지
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return None
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
```

### 2. 메모리 관리 최적화
```python
# domain/common/memory_manager.py
class DomainMemoryManager:
    """도메인 객체 메모리 관리"""
    
    def __init__(self):
        self._object_pools = {}
        self._weak_references = weakref.WeakSet()
    
    def get_pooled_object(self, object_type: type, *args, **kwargs):
        """객체 풀에서 재사용 가능한 객체 가져오기"""
        pool_key = object_type.__name__
        
        if pool_key not in self._object_pools:
            self._object_pools[pool_key] = []
        
        pool = self._object_pools[pool_key]
        
        # 풀에서 사용 가능한 객체 찾기
        for obj in pool:
            if obj.is_reusable():
                obj.reset(*args, **kwargs)
                return obj
        
        # 새 객체 생성
        new_obj = object_type(*args, **kwargs)
        pool.append(new_obj)
        self._weak_references.add(new_obj)
        
        return new_obj
    
    def cleanup_unused_objects(self):
        """사용하지 않는 객체 정리"""
        for pool in self._object_pools.values():
            pool[:] = [obj for obj in pool if obj.is_in_use()]
```

## ⚙️ Application Layer 최적화

### 1. 서비스 레벨 캐싱
```python
# application/services/condition_query_service.py
class ConditionQueryService:
    """조건 조회 서비스 - 캐싱 최적화"""
    
    def __init__(self, condition_repo, cache_manager):
        self.condition_repo = condition_repo
        self.cache = cache_manager
    
    @cached(ttl=300)  # 5분 캐시
    def get_active_conditions(self) -> List[ConditionDto]:
        """활성 조건 목록 조회 - 캐싱 적용"""
        conditions = self.condition_repo.find_all_active()
        return [ConditionDto.from_domain(c) for c in conditions]
    
    @cached(ttl=60, key_generator=lambda self, variable_id: f"compat_{variable_id}")
    def get_compatible_variables(self, variable_id: str) -> List[VariableDto]:
        """호환 변수 목록 - 변수별 캐싱"""
        variables = self.condition_repo.find_compatible_variables(variable_id)
        return [VariableDto.from_domain(v) for v in variables]
    
    def invalidate_condition_cache(self, condition_id: str = None):
        """조건 캐시 무효화"""
        if condition_id:
            self.cache.delete(f"condition_{condition_id}")
        else:
            self.cache.delete_pattern("condition_*")

# application/common/cache_manager.py
class CacheManager:
    """애플리케이션 레벨 캐시 관리"""
    
    def __init__(self):
        self._cache = {}
        self._ttl_data = {}
        self._cleanup_interval = 300  # 5분마다 정리
        self._last_cleanup = datetime.utcnow()
    
    def get(self, key: str):
        """캐시에서 값 가져오기"""
        self._cleanup_if_needed()
        
        if key in self._cache:
            ttl_info = self._ttl_data.get(key)
            if ttl_info and datetime.utcnow() > ttl_info['expires_at']:
                self.delete(key)
                return None
            return self._cache[key]
        return None
    
    def set(self, key: str, value, ttl: int = None):
        """캐시에 값 저장"""
        self._cache[key] = value
        
        if ttl:
            self._ttl_data[key] = {
                'expires_at': datetime.utcnow() + timedelta(seconds=ttl)
            }
    
    def delete(self, key: str):
        """캐시에서 값 삭제"""
        self._cache.pop(key, None)
        self._ttl_data.pop(key, None)
    
    def delete_pattern(self, pattern: str):
        """패턴 매칭으로 캐시 삭제"""
        import re
        regex = re.compile(pattern.replace('*', '.*'))
        
        keys_to_delete = [
            key for key in self._cache.keys() 
            if regex.match(key)
        ]
        
        for key in keys_to_delete:
            self.delete(key)
    
    def _cleanup_if_needed(self):
        """만료된 캐시 항목 정리"""
        now = datetime.utcnow()
        if (now - self._last_cleanup).seconds > self._cleanup_interval:
            self._cleanup_expired_items()
            self._last_cleanup = now
    
    def _cleanup_expired_items(self):
        """만료된 항목 정리"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, ttl_info in self._ttl_data.items()
            if now > ttl_info['expires_at']
        ]
        
        for key in expired_keys:
            self.delete(key)
```

### 2. 배치 처리 최적화
```python
# application/services/batch_condition_service.py
class BatchConditionService:
    """배치 조건 처리 서비스"""
    
    def __init__(self, condition_repo, event_publisher):
        self.condition_repo = condition_repo
        self.event_publisher = event_publisher
        self.batch_size = 100
    
    def process_conditions_batch(self, market_data: MarketData):
        """조건들을 배치로 처리"""
        
        # ✅ 페이징으로 메모리 사용량 제한
        offset = 0
        total_processed = 0
        
        while True:
            # 배치 단위로 조건 조회
            conditions = self.condition_repo.find_active_conditions_paginated(
                offset=offset, 
                limit=self.batch_size
            )
            
            if not conditions:
                break
            
            # ✅ 병렬 처리로 성능 향상
            evaluation_results = self._evaluate_conditions_parallel(
                conditions, market_data
            )
            
            # ✅ 배치로 이벤트 발행
            events = []
            for condition, result in evaluation_results:
                if result:
                    events.append(ConditionActivatedEvent(condition.id))
            
            if events:
                self.event_publisher.publish_batch(events)
            
            total_processed += len(conditions)
            offset += self.batch_size
            
            # 메모리 정리
            del conditions, evaluation_results, events
            gc.collect()
        
        return total_processed
    
    def _evaluate_conditions_parallel(self, conditions, market_data):
        """조건들을 병렬로 평가"""
        import concurrent.futures
        
        def evaluate_single(condition):
            try:
                result = condition.evaluate(market_data)
                return (condition, result)
            except Exception as e:
                logger.error(f"조건 평가 실패: {condition.id}, 오류: {str(e)}")
                return (condition, False)
        
        # ✅ ThreadPoolExecutor로 병렬 처리
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(evaluate_single, condition) for condition in conditions]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        return results
```

## 🔌 Infrastructure Layer 최적화

### 1. 데이터베이스 최적화
```python
# infrastructure/repositories/optimized_condition_repository.py
class OptimizedConditionRepository:
    """최적화된 조건 Repository"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._setup_connection_optimizations()
    
    def _setup_connection_optimizations(self):
        """DB 연결 최적화 설정"""
        # ✅ WAL 모드로 읽기 성능 향상
        self.db.execute("PRAGMA journal_mode=WAL")
        
        # ✅ 메모리 캐시 크기 증가
        self.db.execute("PRAGMA cache_size=10000")  # 10MB
        
        # ✅ 동기화 모드 최적화 (안전성 vs 성능)
        self.db.execute("PRAGMA synchronous=NORMAL")
        
        # ✅ 임시 저장소를 메모리로
        self.db.execute("PRAGMA temp_store=MEMORY")
    
    def find_active_conditions_batch(self, symbol: str, limit: int = 1000):
        """활성 조건 배치 조회 - 최적화된 쿼리"""
        
        # ✅ 인덱스 활용 및 필요한 컬럼만 조회
        query = """
        SELECT c.id, c.variable_id, c.operator, c.target_value, c.parameters,
               v.name as variable_name, v.comparison_group
        FROM trading_conditions c
        INNER JOIN trading_variables v ON c.variable_id = v.id
        WHERE c.is_active = 1 AND c.symbol = ?
        ORDER BY c.priority DESC, c.created_at ASC
        LIMIT ?
        """
        
        return self.db.fetchall(query, (symbol, limit))
    
    def bulk_insert_conditions(self, conditions: List[TradingCondition]):
        """조건 일괄 삽입 - 트랜잭션 최적화"""
        
        # ✅ 단일 트랜잭션으로 배치 삽입
        query = """
        INSERT INTO trading_conditions 
        (id, variable_id, operator, target_value, parameters, created_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        condition_data = [
            (
                condition.id.value,
                condition.variable.id.value,
                condition.operator,
                str(condition.target_value),
                json.dumps(condition.parameters.to_dict()),
                condition.created_at.isoformat(),
                True
            )
            for condition in conditions
        ]
        
        with self.db.transaction():
            self.db.executemany(query, condition_data)
    
    def find_conditions_with_prepared_statement(self, variable_ids: List[str]):
        """준비된 문장으로 조건 조회"""
        
        # ✅ IN 절 최적화
        placeholders = ','.join(['?' for _ in variable_ids])
        query = f"""
        SELECT * FROM trading_conditions 
        WHERE variable_id IN ({placeholders}) AND is_active = 1
        """
        
        return self.db.fetchall(query, variable_ids)

# infrastructure/database/connection_pool.py
class SQLiteConnectionPool:
    """SQLite 연결 풀"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool = queue.Queue(maxsize=pool_size)
        self._create_connections()
    
    def _create_connections(self):
        """연결 풀 생성"""
        for _ in range(self.pool_size):
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            conn.row_factory = sqlite3.Row
            self._pool.put(conn)
    
    @contextmanager
    def get_connection(self):
        """연결 가져오기"""
        conn = self._pool.get(timeout=10)
        try:
            yield conn
        finally:
            self._pool.put(conn)
```

### 2. API 클라이언트 최적화
```python
# infrastructure/api_clients/optimized_upbit_client.py
class OptimizedUpbitClient:
    """최적화된 업비트 API 클라이언트"""
    
    def __init__(self):
        # ✅ 연결 풀링으로 연결 재사용
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3
        )
        self.session.mount('https://', adapter)
        
        # ✅ 응답 캐시
        self._response_cache = TTLCache(maxsize=1000, ttl=60)
        
        # ✅ Rate limiting
        self._rate_limiter = RateLimiter(max_calls=10, period=1)
    
    @cached_property
    def _session_with_retries(self):
        """재시도 로직이 있는 세션"""
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        return self.session
    
    async def get_candle_data_async(self, symbol: str, timeframe: str):
        """비동기 캔들 데이터 조회"""
        
        # 캐시 확인
        cache_key = f"{symbol}_{timeframe}"
        if cache_key in self._response_cache:
            return self._response_cache[cache_key]
        
        # Rate limiting 적용
        with self._rate_limiter:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.upbit.com/v1/candles/{timeframe}"
                params = {"market": symbol, "count": 200}
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    # 캐시 저장
                    self._response_cache[cache_key] = data
                    return data
    
    def get_multiple_symbols_data(self, symbols: List[str], timeframe: str):
        """여러 심볼 데이터 동시 조회"""
        
        async def fetch_all():
            tasks = [
                self.get_candle_data_async(symbol, timeframe)
                for symbol in symbols
            ]
            return await asyncio.gather(*tasks)
        
        return asyncio.run(fetch_all())
```

## 🎨 Presentation Layer 최적화

### 1. UI 응답성 최적화
```python
# presentation/views/optimized_condition_list_view.py
class OptimizedConditionListView(QWidget):
    """최적화된 조건 목록 View"""
    
    def __init__(self):
        super().__init__()
        self.condition_model = ConditionTableModel()
        self.proxy_model = QSortFilterProxyModel()
        
        # ✅ 가상화된 테이블로 메모리 절약
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.proxy_model.setSourceModel(self.condition_model)
        
        # ✅ 지연 로딩 설정
        self.table_view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table_view.verticalScrollBar().valueChanged.connect(self._on_scroll)
        
        self._current_page = 0
        self._page_size = 50
        self._loading = False
    
    def _on_scroll(self, value):
        """스크롤 시 지연 로딩"""
        scrollbar = self.table_view.verticalScrollBar()
        
        # 스크롤이 하단 90%에 도달하면 추가 로딩
        if (value >= scrollbar.maximum() * 0.9 and 
            not self._loading and 
            self.condition_model.can_fetch_more()):
            
            self._loading = True
            self._load_more_conditions()
    
    def _load_more_conditions(self):
        """추가 조건 로딩 - 백그라운드 스레드"""
        
        def load_conditions():
            """백그라운드에서 조건 로딩"""
            try:
                offset = self._current_page * self._page_size
                conditions = self.presenter.load_conditions_paginated(
                    offset=offset, 
                    limit=self._page_size
                )
                return conditions
            except Exception as e:
                logger.error(f"조건 로딩 실패: {str(e)}")
                return []
        
        # ✅ QThread로 백그라운드 로딩
        self.loader_thread = ConditionLoaderThread(load_conditions)
        self.loader_thread.conditions_loaded.connect(self._on_conditions_loaded)
        self.loader_thread.start()
    
    def _on_conditions_loaded(self, conditions):
        """조건 로딩 완료 처리"""
        self.condition_model.append_conditions(conditions)
        self._current_page += 1
        self._loading = False

class ConditionLoaderThread(QThread):
    """조건 로딩 백그라운드 스레드"""
    conditions_loaded = pyqtSignal(list)
    
    def __init__(self, load_function):
        super().__init__()
        self.load_function = load_function
    
    def run(self):
        """백그라운드에서 실행"""
        conditions = self.load_function()
        self.conditions_loaded.emit(conditions)
```

### 2. 차트 렌더링 최적화
```python
# presentation/widgets/optimized_chart_widget.py
class OptimizedChartWidget(QWidget):
    """최적화된 차트 위젯"""
    
    def __init__(self):
        super().__init__()
        # ✅ OpenGL 가속 활성화
        self.setOpenGLEnabled(True)
        
        # ✅ 데이터 다운샘플링
        self.max_data_points = 1000
        self._last_render_time = 0
        self._render_interval = 16  # 60 FPS
        
        # ✅ 렌더링 캐시
        self._render_cache = {}
        self._cache_key = None
    
    def update_chart_data(self, data: List[dict]):
        """차트 데이터 업데이트 - 최적화"""
        
        # ✅ 다운샘플링으로 데이터 포인트 제한
        if len(data) > self.max_data_points:
            step = len(data) // self.max_data_points
            data = data[::step]
        
        # ✅ 캐시 키 생성
        new_cache_key = self._generate_cache_key(data)
        if new_cache_key == self._cache_key:
            return  # 데이터 변경 없음
        
        self._cache_key = new_cache_key
        
        # ✅ 프레임 레이트 제한
        current_time = time.time() * 1000
        if current_time - self._last_render_time < self._render_interval:
            return
        
        self._render_chart(data)
        self._last_render_time = current_time
    
    def _render_chart(self, data):
        """실제 차트 렌더링"""
        # 차트 라이브러리별 최적화된 렌더링 로직
        pass
    
    def _generate_cache_key(self, data):
        """캐시 키 생성"""
        if not data:
            return None
        
        # 첫번째, 마지막, 중간값으로 간단한 해시 생성
        key_points = [
            data[0]['timestamp'],
            data[-1]['timestamp'],
            len(data)
        ]
        return hash(tuple(key_points))
```

## 📊 성능 모니터링

### 성능 메트릭 수집
```python
# shared/monitoring/performance_monitor.py
class PerformanceMonitor:
    """성능 모니터링"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    @contextmanager
    def measure(self, operation_name: str):
        """작업 성능 측정"""
        start_time = time.perf_counter()
        memory_before = psutil.Process().memory_info().rss
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            memory_after = psutil.Process().memory_info().rss
            
            duration = end_time - start_time
            memory_used = memory_after - memory_before
            
            self._record_metric(operation_name, duration, memory_used)
    
    def _record_metric(self, operation: str, duration: float, memory: int):
        """메트릭 기록"""
        if operation not in self.metrics:
            self.metrics[operation] = {
                'count': 0,
                'total_duration': 0,
                'max_duration': 0,
                'total_memory': 0,
                'max_memory': 0
            }
        
        metric = self.metrics[operation]
        metric['count'] += 1
        metric['total_duration'] += duration
        metric['max_duration'] = max(metric['max_duration'], duration)
        metric['total_memory'] += memory
        metric['max_memory'] = max(metric['max_memory'], memory)
    
    def get_performance_report(self) -> dict:
        """성능 리포트 생성"""
        report = {}
        for operation, metric in self.metrics.items():
            if metric['count'] > 0:
                report[operation] = {
                    'avg_duration': metric['total_duration'] / metric['count'],
                    'max_duration': metric['max_duration'],
                    'avg_memory_mb': metric['total_memory'] / metric['count'] / 1024 / 1024,
                    'max_memory_mb': metric['max_memory'] / 1024 / 1024,
                    'call_count': metric['count']
                }
        return report

# 사용 예시
performance_monitor = PerformanceMonitor()

with performance_monitor.measure("condition_evaluation"):
    result = condition.evaluate(market_data)
```

## 🔍 다음 단계

- **[에러 처리](11_ERROR_HANDLING.md)**: 성능 최적화와 안정성 균형
- **[디버깅 가이드](15_DEBUGGING_GUIDE.md)**: 성능 이슈 진단 방법
- **[테스팅 전략](16_TESTING_STRATEGY.md)**: 성능 테스트 구현

---
**💡 핵심**: "Clean Architecture에서는 각 계층별로 적절한 최적화 전략을 적용하여 전체 시스템 성능을 향상시킵니다!"
