# 📊 마켓 데이터 요구사항 관리 시스템 설계

## 🔍 **현재 시스템 분석**

### **기존 아키텍처 문제점**

#### **1. 이중 API 구현 (연동 안됨)**
```
🔄 데이터 레이어 (Legacy):
├── upbit_auto_trading/data_layer/collectors/upbit_api.py
├── 클래스: UpbitAPI (동기식)
├── 전체 시스템에서 사용중
└── 기본적인 Rate Limiting만 존재

🆕 인프라스트럭처 (DDD):
├── upbit_auto_trading/infrastructure/external_apis/upbit/
├── 클래스: UpbitClient (비동기)
├── 완전한 Rate Limiting, 재시도, 인증
└── 시스템에서 사용되지 않음 (미연동)
```

#### **2. 데이터 요구사항 관리 부재**
- **계산기 → DB → API 연쇄 반응**: 관리되지 않음
- **동시 다발적 요청**: 스케줄링 없음
- **데이터 의존성**: 명시되지 않음
- **배치 최적화**: 없음

#### **3. 현재 데이터 흐름**
```
ATR 계산기 요청 → MarketDataLoader → SQLite DB 확인 →
데이터 없음 → UpbitAPI 직접 호출 → 200개 캔들 제한
```

## 🎯 **제안하는 통합 아키텍처**

### **Phase 1: API 통합 (기존 → 신규)**

#### **1-1. 기존 UpbitAPI 마이그레이션**
```python
# 기존 코드 (data_layer/upbit_api.py)
api = UpbitAPI()
candles = api.get_candles('KRW-BTC', '1h', 100)

# 신규 코드 (infrastructure/external_apis)
async with UpbitClient() as client:
    candles = await client.get_candles_minutes('KRW-BTC', unit=60, count=100)
```

#### **1-2. 호환성 래퍼 제공**
```python
# 기존 시스템 호환용 동기식 래퍼
class UpbitAPIWrapper:
    def __init__(self):
        self._async_client = UpbitClient()

    def get_candles(self, symbol, timeframe, count):
        # 비동기를 동기로 래핑
        return asyncio.run(
            self._async_client.get_candles_minutes(symbol, unit, count)
        )
```

### **Phase 2: 데이터 요구사항 스케줄러**

#### **2-1. 계산기 데이터 요구사항 명세**
```python
class DataRequirement:
    symbol: str                    # 'KRW-BTC'
    timeframe: str                 # '1m', '5m', '1h', '1d'
    period_needed: int             # 필요한 과거 데이터 개수
    calculation_type: str          # 'ATR', 'RSI', 'MACD'
    urgency: int                   # 1(낮음) ~ 5(높음)
    cache_duration: timedelta      # 캐시 유효 기간

class ATRCalculator:
    def get_data_requirements(self, params) -> List[DataRequirement]:
        """이 계산기가 필요한 데이터 요구사항 반환"""
        base_req = DataRequirement(
            symbol=params['symbol'],
            timeframe=params['timeframe'],
            period_needed=params['period'] + 50,  # ATR 계산 + 통계용
            calculation_type='OHLCV',
            urgency=3,
            cache_duration=timedelta(minutes=5)
        )

        if params['calculation_method'] == 'previous':
            base_req.period_needed += params['calculation_period']

        return [base_req]
```

#### **2-2. 데이터 요구사항 스케줄러**
```python
class DataRequirementScheduler:
    """데이터 요구사항을 수집하고 최적화된 배치로 처리"""

    def __init__(self):
        self.pending_requirements: List[DataRequirement] = []
        self.cache_manager = DataCacheManager()
        self.api_client = UpbitClient()
        self.batch_timer = None

    def add_requirement(self, requirement: DataRequirement):
        """계산기로부터 데이터 요구사항 접수"""
        self.pending_requirements.append(requirement)
        self._schedule_batch_processing()

    def _schedule_batch_processing(self):
        """100ms 후 배치 처리 (중복 요청 병합용)"""
        if self.batch_timer:
            self.batch_timer.cancel()

        self.batch_timer = threading.Timer(0.1, self._process_batch)
        self.batch_timer.start()

    def _process_batch(self):
        """수집된 요구사항들을 최적화하여 처리"""
        if not self.pending_requirements:
            return

        # 1. 중복 제거 및 병합
        merged_reqs = self._merge_requirements(self.pending_requirements)

        # 2. 캐시에서 해결 가능한 것들 분리
        cache_hits, cache_misses = self._check_cache(merged_reqs)

        # 3. API 호출 최적화 (같은 심볼/타임프레임 묶기)
        api_batches = self._optimize_api_calls(cache_misses)

        # 4. 우선순위별 실행
        asyncio.create_task(self._execute_batches(api_batches))

        self.pending_requirements.clear()
```

#### **2-3. 데이터 캐시 매니저**
```python
class DataCacheManager:
    """DB + 메모리 2단계 캐싱"""

    def __init__(self):
        self.memory_cache = {}  # 최근 데이터 메모리 캐시
        self.db_cache = SQLiteCache()  # DB 영구 저장

    def get_data(self, requirement: DataRequirement) -> Optional[pd.DataFrame]:
        """캐시에서 데이터 조회 (메모리 → DB 순서)"""

        # 1. 메모리 캐시 확인
        cache_key = self._make_cache_key(requirement)
        if cache_key in self.memory_cache:
            data, expiry = self.memory_cache[cache_key]
            if datetime.now() < expiry:
                return data

        # 2. DB 캐시 확인
        db_data = self.db_cache.get_candles(
            requirement.symbol,
            requirement.timeframe,
            requirement.period_needed
        )

        if db_data is not None and len(db_data) >= requirement.period_needed:
            # 메모리 캐시에도 저장
            expiry = datetime.now() + requirement.cache_duration
            self.memory_cache[cache_key] = (db_data, expiry)
            return db_data

        return None

    def store_data(self, requirement: DataRequirement, data: pd.DataFrame):
        """데이터를 2단계 캐시에 저장"""
        cache_key = self._make_cache_key(requirement)
        expiry = datetime.now() + requirement.cache_duration

        # 메모리 캐시
        self.memory_cache[cache_key] = (data, expiry)

        # DB 캐시 (비동기로)
        asyncio.create_task(self.db_cache.store_candles(data))
```

### **Phase 3: 통합 데이터 서비스**

#### **3-1. 계산기-스케줄러 연동**
```python
class EnhancedCalculatorBase:
    """모든 계산기의 기본 클래스"""

    def __init__(self):
        self.data_scheduler = DataRequirementScheduler()

    async def calculate_with_auto_data(self, params: dict) -> float:
        """데이터 자동 확보 후 계산"""

        # 1. 데이터 요구사항 생성
        requirements = self.get_data_requirements(params)

        # 2. 스케줄러에 요청
        data_futures = []
        for req in requirements:
            future = self.data_scheduler.request_data(req)
            data_futures.append(future)

        # 3. 모든 데이터 확보 대기
        data_list = await asyncio.gather(*data_futures)

        # 4. 계산 실행
        return self.calculate(data_list[0], params)

    @abstractmethod
    def get_data_requirements(self, params: dict) -> List[DataRequirement]:
        """구현 필수: 필요한 데이터 요구사항 정의"""
        pass

    @abstractmethod
    def calculate(self, data: pd.DataFrame, params: dict) -> float:
        """구현 필수: 실제 계산 로직"""
        pass
```

#### **3-2. ATR 계산기 구현 예시**
```python
class ATRCalculator(EnhancedCalculatorBase):
    def get_data_requirements(self, params: dict) -> List[DataRequirement]:
        period_needed = params['period'] + 10  # 기본 ATR 계산용

        # 확장 기능별 추가 데이터
        if params.get('calculation_method') == 'previous':
            period_needed += params.get('calculation_period', 5)
        elif params.get('calculation_method') in ['min', 'max', 'average']:
            period_needed += params.get('calculation_period', 5)

        return [DataRequirement(
            symbol=params['symbol'],
            timeframe=params['timeframe'],
            period_needed=period_needed,
            calculation_type='OHLCV',
            urgency=3,
            cache_duration=timedelta(minutes=5)
        )]

    def calculate(self, data: pd.DataFrame, params: dict) -> float:
        # 기본 ATR 계산
        atr_series = self._calculate_basic_atr(data, params['period'])

        # 확장 기능 적용
        method = params.get('calculation_method', 'basic')
        if method == 'basic':
            result = atr_series.iloc[-1]
        elif method == 'previous':
            periods_back = params.get('calculation_period', 5)
            result = atr_series.iloc[-(periods_back + 1)]
        elif method in ['min', 'max', 'average']:
            period = params.get('calculation_period', 5)
            recent_data = atr_series.tail(period)
            if method == 'min':
                result = recent_data.min()
            elif method == 'max':
                result = recent_data.max()
            else:  # average
                result = recent_data.mean()

        # 배율 적용
        multiplier = params.get('multiplier_percent', 100.0) / 100.0
        return result * multiplier
```

## 🚀 **구현 우선순위**

### **Phase 1: API 통합 (1-2주)**
- [ ] infrastructure/external_apis를 전체 시스템에 적용
- [ ] 기존 data_layer/upbit_api.py 호환성 래퍼 제공
- [ ] 점진적 마이그레이션

### **Phase 2: 기본 스케줄러 (2-3주)**
- [ ] DataRequirement 모델 정의
- [ ] DataRequirementScheduler 구현
- [ ] DataCacheManager 구현

### **Phase 3: 계산기 통합 (3-4주)**
- [ ] EnhancedCalculatorBase 정의
- [ ] ATRCalculator 첫 번째 구현
- [ ] 다른 계산기들 순차 적용

## ⚡ **즉시 해결 가능한 문제**

현재 ATR 확장 기능은 **Phase 1 완료 없이도 구현 가능**합니다:
1. 기존 data_layer/upbit_api.py 사용
2. 단순한 데이터 캐싱으로 시작
3. 향후 Phase 2, 3에서 점진적 업그레이드

---

**결론**: 현재 시스템의 이중 API 구조를 통합하고, 체계적인 데이터 요구사항 관리 시스템을 구축해야 합니다. 하지만 ATR 확장 기능은 기존 구조로도 충분히 구현 가능합니다.
