# 📋 스마트 라우팅 시스템 단순화 설계안

## 🎯 **문제 진단**

### 현재 복잡성
```python
# 현재: 복잡한 설정이 필요
request = RoutingRequest(
    symbols=["KRW-BTC"],
    data_type=DataType.TICKER,
    timeframe=TimeFrame.MINUTE_1,
    # ... 10개 이상의 매개변수
)
context = RoutingContext(
    usage_context=UsageContext.REAL_TIME_TRADING,
    network_policy=NetworkPolicy.BALANCED,
    # ... 복잡한 설정
)
response = await engine.route_data_request(request, context)
```

### 사용자 기대
```python
# 기대: 단순한 호출
data = await smart_router.get_ticker("KRW-BTC")
# 또는
data = await smart_router.get_candles("KRW-BTC", interval="1m", count=100)
```

---

## 🚀 **단순화 설계안**

### **1. 단순 인터페이스 계층 추가**

```python
class SimpleSmartRouter:
    """사용자 친화적 스마트 라우팅 인터페이스"""

    def __init__(self):
        self._engine = AdaptiveRoutingEngine()
        self._auto_context = AutoContextBuilder()

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """티커 데이터 조회 - 자동 최적화"""
        context = self._auto_context.build_for_ticker(symbol)
        request = RoutingRequest.create_ticker_request([symbol])
        response = await self._engine.route_data_request(request, context)
        return response.data.get(symbol, {})

    async def get_candles(self, symbol: str, interval: str = "1m",
                         count: int = 100) -> List[Dict[str, Any]]:
        """캔들 데이터 조회 - 자동 최적화"""
        context = self._auto_context.build_for_candles(symbol, interval, count)
        request = RoutingRequest.create_candle_request([symbol], interval, count)
        response = await self._engine.route_data_request(request, context)
        return response.data.get(symbol, [])

    async def subscribe_realtime(self, symbol: str,
                               callback: Callable) -> str:
        """실시간 구독 - 자동 채널 선택"""
        # WebSocket 우선, REST 폴백
        return await self._setup_subscription(symbol, callback)
```

### **2. 자동 컨텍스트 빌더**

```python
class AutoContextBuilder:
    """사용 패턴 기반 자동 컨텍스트 생성"""

    def __init__(self):
        self._usage_tracker = UsagePatternTracker()

    def build_for_ticker(self, symbol: str) -> RoutingContext:
        """티커 요청용 컨텍스트 자동 생성"""
        recent_pattern = self._usage_tracker.get_recent_pattern(symbol)

        if recent_pattern.is_high_frequency():
            usage_context = UsageContext.REAL_TIME_TRADING
        elif recent_pattern.is_monitoring():
            usage_context = UsageContext.MARKET_MONITORING
        else:
            usage_context = UsageContext.GENERAL_QUERY

        return RoutingContext(
            usage_context=usage_context,
            network_policy=NetworkPolicy.BALANCED,
            priority=Priority.NORMAL,
            timeout_seconds=5.0
        )

    def build_for_candles(self, symbol: str, interval: str,
                         count: int) -> RoutingContext:
        """캔들 요청용 컨텍스트 자동 생성"""
        if count > 200:
            usage_context = UsageContext.RESEARCH_ANALYSIS
        elif interval in ["1m", "5m"] and count <= 50:
            usage_context = UsageContext.REAL_TIME_TRADING
        else:
            usage_context = UsageContext.GENERAL_QUERY

        return RoutingContext(
            usage_context=usage_context,
            network_policy=NetworkPolicy.EFFICIENCY_FIRST,
            priority=Priority.NORMAL,
            timeout_seconds=10.0
        )
```

### **3. 사용 패턴 추적기**

```python
class UsagePatternTracker:
    """요청 패턴 학습 및 예측"""

    def __init__(self):
        self._patterns: Dict[str, SymbolPattern] = {}

    def track_request(self, symbol: str, request_type: str):
        """요청 패턴 기록"""
        if symbol not in self._patterns:
            self._patterns[symbol] = SymbolPattern(symbol)
        self._patterns[symbol].add_request(request_type)

    def get_recent_pattern(self, symbol: str) -> SymbolPattern:
        """최근 패턴 조회"""
        return self._patterns.get(symbol, SymbolPattern(symbol))

@dataclass
class SymbolPattern:
    symbol: str
    request_history: List[Tuple[datetime, str]] = field(default_factory=list)

    def add_request(self, request_type: str):
        self.request_history.append((datetime.now(), request_type))
        # 최근 100개만 유지
        if len(self.request_history) > 100:
            self.request_history = self.request_history[-100:]

    def is_high_frequency(self) -> bool:
        """고빈도 요청 패턴 여부"""
        if len(self.request_history) < 5:
            return False

        recent_5 = self.request_history[-5:]
        time_span = (recent_5[-1][0] - recent_5[0][0]).total_seconds()
        return time_span < 10.0  # 10초 내 5회 요청

    def is_monitoring(self) -> bool:
        """모니터링 패턴 여부"""
        if len(self.request_history) < 3:
            return False

        # 일정한 간격의 요청 패턴
        intervals = []
        for i in range(1, min(6, len(self.request_history))):
            delta = (self.request_history[-i][0] -
                    self.request_history[-i-1][0]).total_seconds()
            intervals.append(delta)

        if not intervals:
            return False

        avg_interval = sum(intervals) / len(intervals)
        return 30 <= avg_interval <= 300  # 30초~5분 간격
```

---

## 🎯 **통합 전략**

### **Phase 1: 래퍼 계층 추가**
- 기존 `AdaptiveRoutingEngine` 유지
- `SimpleSmartRouter` 래퍼 추가
- 점진적 마이그레이션 지원

### **Phase 2: 실제 시스템 통합**
```python
# 차트 뷰어 통합
class ChartDataService:
    def __init__(self):
        self.router = SimpleSmartRouter()

    async def load_chart_data(self, symbol: str, timeframe: str):
        # 기존: 복잡한 API 호출
        # candles = await upbit_client.get_candles(symbol, interval, count)

        # 개선: 스마트 라우팅 활용
        candles = await self.router.get_candles(symbol, timeframe, 200)
        return self._convert_to_chart_format(candles)

# 백테스팅 통합
class BacktestDataProvider:
    def __init__(self):
        self.router = SimpleSmartRouter()

    async def fetch_historical_data(self, symbol: str, start_date: datetime, end_date: datetime):
        # 자동으로 적절한 Tier 선택 (COLD_REST for 대용량 과거 데이터)
        return await self.router.get_candles_range(symbol, start_date, end_date)
```

### **Phase 3: 성능 최적화**
- 패턴 학습 정확도 향상
- 캐시 계층 통합
- Rate Limiting 중앙화

---

## 📊 **성공 기준**

### **사용성 개선**
- [ ] API 호출 복잡도 90% 감소
- [ ] 설정 매개변수 10개 → 2개 이하
- [ ] 학습 없이 즉시 사용 가능

### **성능 유지**
- [ ] 기존 AdaptiveRoutingEngine 성능 100% 유지
- [ ] 오버헤드 < 1ms
- [ ] 메모리 사용량 증가 < 10MB

### **실제 통합**
- [ ] 차트 뷰어 통합 완료
- [ ] 백테스팅 시스템 통합
- [ ] 실거래 시스템 통합 (Phase 4)

---

## 🔧 **구현 우선순위**

1. **즉시 (1시간)**: `SimpleSmartRouter` 기본 구현
2. **단기 (4시간)**: `AutoContextBuilder` 및 패턴 추적
3. **중기 (1일)**: 차트 뷰어 통합 테스트
4. **장기 (1주)**: 전체 시스템 통합 및 최적화

---

**핵심 철학**: "복잡한 내부, 단순한 외부 - 사용자는 쉽게, 시스템은 똑똑하게"
