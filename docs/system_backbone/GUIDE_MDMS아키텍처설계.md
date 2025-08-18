# GUIDE_MDMS아키텍처설계

**목적**: Market Data Management System 계층화 아키텍처 설계 가이드
**적용**: 스크리너/매매전략/백테스팅 통합 데이터 관리
**분량**: 184줄 / 200줄 (92% 사용)

---

## 🎯 **핵심 설계 원칙 (1-20줄: 즉시 파악)**

### **MDMS 아키텍처 철학**
- **계층 분리**: 데이터 수집 ← 계산 엔진 ← 사용케이스 서비스
- **중복 제거**: 공통 계산 엔진으로 리소스 효율성
- **사용 패턴별 최적화**: 배치(스크리너) vs 실시간(매매)
- **느슨한 결합**: 이벤트 기반 통신

### **핵심 문제 해결**
- ✅ 계산 중복 방지 (ATR, RSI 등 공통 지표)
- ✅ 대량 처리 최적화 (120개 심볼 동시 스크리닝)
- ✅ 실시간 응답 보장 (매매 신호 즉시 생성)
- ✅ 확장성 확보 (새로운 사용케이스 추가 용이)

---

## 🏗️ **3계층 아키텍처 (21-50줄: 맥락)**

### **계층 1: 데이터 수집 & 저장**
```python
class MarketDataCollector:
    """순수 데이터 수집/저장 백본"""

    def __init__(self):
        self.api_client = UpbitAPIClient()
        self.storage = MarketDataStorage()
        self.cache_manager = DataCacheManager()

    async def collect_batch_data(self, symbols: List[str], timeframe: str, days: int):
        """대량 데이터 수집 (스크리너용)"""
        for symbol_batch in self.chunk_symbols(symbols, 10):
            await self.parallel_collect(symbol_batch, timeframe, days)

    async def collect_realtime_data(self, symbol: str, timeframe: str):
        """실시간 데이터 수집 (매매용)"""
        return await self.get_latest_candles(symbol, timeframe, 1)
```

### **계층 2: 계산 서비스 (공통)**
```python
class CalculationEngine:
    """모든 시스템이 공유하는 계산 엔진"""

    def __init__(self):
        self.calculation_cache = {}
        self.dependency_resolver = DependencyResolver()

    async def calculate_batch_indicators(self, symbols: List[str], indicators: List[str]):
        """배치 지표 계산 (중복 제거)"""
        required_calcs = self.dependency_resolver.resolve(indicators)

        for calc_type in self.get_calculation_order(required_calcs):
            batch_results = await self.batch_calculate(calc_type, symbols)
            self.calculation_cache.update(batch_results)

    async def calculate_realtime_indicator(self, symbol: str, indicator: str):
        """실시간 지표 계산 (캐시 활용)"""
        cache_key = f"{symbol}_{indicator}"
        if cache_key in self.calculation_cache:
            return self.update_incremental(cache_key)
        return await self.calculate_fresh(symbol, indicator)
```

### **계층 3: 사용 케이스별 서비스**
```python
class ScreenerOrchestrator:
    """스크리너 전용 배치 처리"""

    async def execute_screening(self, symbols: List[str], rules: List[str]):
        # 1. 데이터 사전 준비
        await self.data_collector.preload_symbols(symbols)

        # 2. 배치 계산 실행
        results = await self.calculation_engine.calculate_batch_indicators(
            symbols, self.extract_indicators(rules)
        )

        # 3. 규칙 적용 및 랭킹
        return self.apply_screening_rules(results, rules)

class StrategyCalculator:
    """매매 전략 실시간 처리"""

    async def get_signal(self, symbol: str, strategy_config: dict):
        # 실시간 데이터 확보
        latest_data = await self.data_collector.get_latest(symbol)

        # 즉시 계산
        signal = await self.calculation_engine.calculate_realtime_indicator(
            symbol, strategy_config['indicator']
        )

        return self.generate_trading_signal(signal, strategy_config)
```

---

## 🔄 **중복 제거 메커니즘 (51-100줄: 상세)**

### **의존성 해결 시스템**
```python
class DependencyResolver:
    def __init__(self):
        self.dependency_graph = {
            'RSI': ['SMA'],
            'MACD': ['EMA_12', 'EMA_26'],
            'BOLLINGER_BANDS': ['SMA', 'STDDEV'],
            'ATR': ['TR'],
            'STOCH': ['HIGHEST', 'LOWEST']
        }

    def resolve(self, indicators: List[str]) -> List[str]:
        """지표 의존성 해결 및 계산 순서 결정"""
        resolved = set()
        queue = indicators.copy()

        while queue:
            indicator = queue.pop(0)
            dependencies = self.dependency_graph.get(indicator, [])

            if all(dep in resolved for dep in dependencies):
                resolved.add(indicator)
            else:
                queue.extend([dep for dep in dependencies if dep not in resolved])
                queue.append(indicator)

        return list(resolved)
```

### **스마트 캐싱 전략**
```python
class SmartCalculationCache:
    def __init__(self):
        self.memory_cache = {}  # 최근 계산 결과
        self.incremental_cache = {}  # 증분 계산용

    def cache_batch_result(self, symbol: str, indicator: str, result: any):
        """배치 계산 결과 캐싱"""
        cache_key = f"{symbol}_{indicator}"
        self.memory_cache[cache_key] = {
            'result': result,
            'timestamp': datetime.now(),
            'type': 'batch'
        }

    def get_incremental_base(self, symbol: str, indicator: str):
        """증분 계산 기준점 반환"""
        cache_key = f"{symbol}_{indicator}"
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]['result']
        return None

    def update_incremental(self, symbol: str, indicator: str, new_data: any):
        """증분 업데이트"""
        base = self.get_incremental_base(symbol, indicator)
        if base:
            return self.calculate_incremental_update(base, new_data)
        return None
```

### **배치 최적화 알고리즘**
```python
class BatchOptimizer:
    def optimize_calculation_order(self, symbols: List[str], indicators: List[str]):
        """최적 계산 순서 결정"""

        # 1. 의존성 그래프 기반 순서
        dependency_order = self.dependency_resolver.resolve(indicators)

        # 2. 메모리 사용량 고려 청킹
        symbol_chunks = self.optimize_memory_usage(symbols)

        # 3. API Rate Limit 고려 스케줄링
        execution_plan = []
        for chunk in symbol_chunks:
            for indicator in dependency_order:
                execution_plan.append({
                    'symbols': chunk,
                    'indicator': indicator,
                    'priority': self.get_priority(indicator),
                    'estimated_time': self.estimate_calculation_time(len(chunk), indicator)
                })

        return sorted(execution_plan, key=lambda x: x['priority'])
```

---

## ⚡ **성능 최적화 전략 (101-150줄: 실행)**

### **병렬 처리 최적화**
```python
class ParallelCalculationManager:
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.task_queue = asyncio.Queue()

    async def process_batch_calculations(self, calculation_plan: List[dict]):
        """배치 계산 병렬 처리"""

        # 우선순위별 그룹화
        priority_groups = self.group_by_priority(calculation_plan)

        for priority, tasks in priority_groups.items():
            # 우선순위 그룹 내에서 병렬 실행
            await asyncio.gather(*[
                self.execute_calculation_task(task) for task in tasks
            ])

    async def execute_calculation_task(self, task: dict):
        """개별 계산 작업 실행"""
        async with self.semaphore:
            try:
                result = await self.calculate_indicator(
                    task['symbols'], task['indicator']
                )
                return {'task': task, 'result': result, 'status': 'success'}
            except Exception as e:
                return {'task': task, 'error': str(e), 'status': 'failed'}
```

### **메모리 효율성 관리**
```python
class MemoryManager:
    def __init__(self, max_memory_mb: int = 500):
        self.max_memory = max_memory_mb * 1024 * 1024
        self.current_usage = 0
        self.cache_priority = {}

    def optimize_symbol_chunking(self, symbols: List[str]) -> List[List[str]]:
        """메모리 사용량 기반 심볼 청킹"""
        estimated_memory_per_symbol = 2 * 1024 * 1024  # 2MB per symbol
        max_symbols_per_chunk = self.max_memory // estimated_memory_per_symbol

        chunks = []
        for i in range(0, len(symbols), max_symbols_per_chunk):
            chunks.append(symbols[i:i + max_symbols_per_chunk])

        return chunks

    def evict_if_needed(self):
        """메모리 부족시 캐시 제거"""
        if self.current_usage > self.max_memory * 0.8:  # 80% 임계점
            # LRU 기반 제거
            least_used = min(self.cache_priority.items(), key=lambda x: x[1])
            self.remove_from_cache(least_used[0])
```

### **실시간 최적화**
```python
class RealtimeOptimizer:
    def __init__(self):
        self.hot_cache = {}  # 자주 사용되는 심볼용 핫 캐시
        self.calculation_shortcuts = {}

    async def fast_signal_calculation(self, symbol: str, strategy: dict):
        """실시간 신호 계산 최적화"""

        # 1. 핫 캐시 확인
        if symbol in self.hot_cache:
            base_data = self.hot_cache[symbol]
            return await self.incremental_update(base_data, strategy)

        # 2. 계산 단축 경로 확인
        if strategy['type'] in self.calculation_shortcuts:
            shortcut = self.calculation_shortcuts[strategy['type']]
            return await shortcut(symbol, strategy)

        # 3. 일반 계산 경로
        return await self.full_calculation(symbol, strategy)

    def promote_to_hot_cache(self, symbol: str):
        """자주 사용되는 심볼을 핫 캐시로 승격"""
        if symbol not in self.hot_cache:
            self.hot_cache[symbol] = self.load_base_data(symbol)
```

---

## 🌐 **이벤트 기반 통신 (151-184줄: 연결)**

### **이벤트 버스 구현**
```python
class MDMSEventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.event_queue = asyncio.Queue()

    async def publish(self, event_type: str, data: dict):
        """비동기 이벤트 발행"""
        event = {'type': event_type, 'data': data, 'timestamp': datetime.now()}
        await self.event_queue.put(event)

    async def process_events(self):
        """이벤트 처리 루프"""
        while True:
            event = await self.event_queue.get()
            await self.dispatch_event(event)

    async def dispatch_event(self, event: dict):
        """이벤트 디스패치"""
        event_type = event['type']
        if event_type in self.subscribers:
            await asyncio.gather(*[
                subscriber.handle(event) for subscriber in self.subscribers[event_type]
            ])
```

### **시스템 간 연동 예시**
```python
# 데이터 수집 완료 이벤트
await event_bus.publish("market_data_collected", {
    "symbols": ["KRW-BTC", "KRW-ETH"],
    "timeframe": "1d",
    "count": 30
})

# 계산 엔진이 캐시 무효화
class CalculationEngine:
    async def handle_data_collected(self, event):
        symbols = event['data']['symbols']
        for symbol in symbols:
            await self.invalidate_cache(symbol)

# 스크리너가 재계산 트리거
class ScreenerOrchestrator:
    async def handle_data_collected(self, event):
        if self.is_screening_active():
            await self.trigger_recalculation(event['data']['symbols'])
```

### **확장성 보장**
```yaml
새로운 사용케이스 추가:
1. 새 서비스 클래스 생성 (예: BacktesterService)
2. 기존 CalculationEngine 재사용
3. 필요한 이벤트 구독
4. 특화된 최적화 로직 구현

시스템 독립성:
- 각 계층은 인터페이스로만 통신
- 이벤트 버스를 통한 느슨한 결합
- 개별 배포 및 스케일링 가능
```

**설계 목표**: **확장 가능하고 효율적인** MDMS 아키텍처로 모든 사용케이스 지원 🚀
