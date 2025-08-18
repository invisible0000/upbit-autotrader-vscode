# PLAN_캐시시스템v1

**목적**: 지능형 마켓 데이터 캐싱 시스템 1차 구현 계획
**우선순위**: 🔥 최고 (매매 변수 계산기 의존성)
**구현 기간**: 2주 (Phase 1-2)
**예상 효과**: API 호출 80% 감소, 응답시간 90% 단축

---

## 🎯 **핵심 목표 및 가치 (1-20줄: 즉시 파악)**

### **해결할 핵심 문제**
- ❌ **API Rate Limit 충돌**: 업비트 API 한계로 실시간 계산 지연
- ❌ **중복 데이터 요청**: 동일 자산 여러 변수에서 반복 호출
- ❌ **실시간 계산 불가**: 과거 데이터 부족으로 통계 계산 실패
- ❌ **200개 한계 비효율**: 필요한 14개만 요청, 186개 낭비

### **1차 구현 핵심 가치**
- ✅ **지능형 배치 로딩**: 200개 한계 최대 활용
- ✅ **메모리-DB 하이브리드**: 1ms 캐시 + 10ms DB + 1000ms API
- ✅ **선행 적재 시스템**: 요청 패턴 분석으로 사전 준비
- ✅ **실시간 가상 캔들**: 진행중 타임프레임 실시간 추적

### **1차 성공 기준**
- API 호출 감소: 현재 2,400회/일 → 480회/일 (80% 감소)
- 계산기 응답: 현재 150ms → 15ms (90% 단축)
- 캐시 히트율: 메모리 90% + DB 95% 달성

---

## 🏗️ **1차 시스템 아키텍처 (21-50줄: 맥락 완성)**

### **핵심 구성요소 4개**
```python
1. MarketDataRouter (데이터 요청 라우터)
   - 모든 계산기의 데이터 요청 중앙 집중
   - 캐시 우선 확인 → DB 조회 → API 호출 순서
   - 배치 요청 통합 및 스케줄링

2. HybridCache (하이브리드 캐시)
   - 메모리: deque(maxlen=200) 초고속 접근
   - DB: market_data.sqlite3 영구 저장
   - 실시간: VirtualCandle 진행중 타임프레임

3. IntelligentPreloader (지능형 선행 로더)
   - 전략 분석으로 필요 데이터 예측
   - 200개 한계 활용한 대량 선행 적재
   - 사용 패턴 학습 및 최적화

4. APIOptimizer (API 효율성 엔진)
   - Rate Limit 안전 관리 (초당 10회)
   - 동일 요청 통합 배치 처리
   - 백오프 재시도 전략
```

### **데이터 플로우 설계**
```
계산기 요청 → MarketDataRouter → HybridCache 확인
                                      ↓ (캐시 미스)
                                 DB Cache 조회
                                      ↓ (DB 미스)
                                 APIOptimizer → 업비트 API
                                      ↓
                                 200개 받아서 캐시 업데이트
                                      ↓
                                 요청된 데이터 반환
```

### **1차 구현 범위 제한**
- **지원 심볼**: KRW-BTC만 (확장성 고려 설계)
- **지원 타임프레임**: 1m, 5m, 15m, 1h, 1d
- **캐시 크기**: 메모리 200개, DB 무제한
- **실시간 업데이트**: WebSocket 연동 제외 (2차에서 구현)

---

## 💾 **하이브리드 캐시 상세 설계 (51-100줄: 상세 분석)**

### **3계층 캐시 전략**
```python
class MarketDataCache:
    def __init__(self):
        # L1 캐시: 메모리 (1ms 응답)
        self.memory_cache: Dict[str, deque] = {}
        # Key: "KRW-BTC_1d", Value: deque(maxlen=200)

        # L2 캐시: SQLite DB (10ms 응답)
        self.db_cache = market_data.sqlite3

        # L3 캐시: 실시간 가상 캔들
        self.virtual_candles: Dict[str, VirtualCandle] = {}

    def get_data(self, symbol: str, timeframe: str, count: int) -> List[CandleData]:
        cache_key = f"{symbol}_{timeframe}"

        # L1: 메모리 캐시 우선 확인
        if cache_key in self.memory_cache:
            memory_data = list(self.memory_cache[cache_key])
            if len(memory_data) >= count:
                self.metrics.record_cache_hit('memory')
                return memory_data[-count:]

        # L2: DB 캐시 확인
        db_data = self.load_from_db(symbol, timeframe, count)
        if len(db_data) >= count:
            self.update_memory_cache(cache_key, db_data)
            self.metrics.record_cache_hit('db')
            return db_data[-count:]

        # L3: API 호출 (200개 대량 로딩)
        api_data = self.fetch_from_api(symbol, timeframe, 200)
        self.save_to_db(symbol, timeframe, api_data)
        self.update_memory_cache(cache_key, api_data)
        self.metrics.record_cache_miss('api')
        return api_data[-count:]
```

### **메모리 캐시 최적화**
```python
class MemoryCacheManager:
    def __init__(self, max_symbols: int = 10):
        self.max_memory_usage = 100 * 1024 * 1024  # 100MB 제한
        self.cache_data = {}
        self.access_times = {}  # LRU 관리

    def evict_if_needed(self):
        """메모리 부족시 LRU 기준 제거"""
        current_usage = self.calculate_memory_usage()
        if current_usage > self.max_memory_usage:
            oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            del self.cache_data[oldest_key]
            del self.access_times[oldest_key]

    def update_cache(self, key: str, data: List[CandleData]):
        """캐시 업데이트 및 LRU 갱신"""
        self.evict_if_needed()
        self.cache_data[key] = deque(data, maxlen=200)
        self.access_times[key] = time.time()
```

### **DB 캐시 인덱스 최적화**
```sql
-- 기존 market_data.sqlite3 테이블 최적화
CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_timestamp
ON candles(symbol, timeframe, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_timestamp_recent
ON candles(timestamp DESC)
WHERE timestamp > datetime('now', '-30 days');

-- 캐시 메타데이터 테이블 추가
CREATE TABLE IF NOT EXISTS cache_metadata (
    cache_key TEXT PRIMARY KEY,
    last_updated TIMESTAMP,
    data_count INTEGER,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ⚡ **지능형 선행 로더 구현 (101-150줄: 실행 방법)**

### **전략 분석 기반 예측 로딩**
```python
class IntelligentPreloader:
    def __init__(self, market_data_router: MarketDataRouter):
        self.router = market_data_router
        self.strategy_analyzer = StrategyAnalyzer()
        self.usage_pattern_learner = UsagePatternLearner()

    async def analyze_and_preload(self, strategy_id: str):
        """전략 분석하여 필요 데이터 선행 적재"""

        # 1. 전략 설정 분석
        strategy_config = await self.load_strategy_config(strategy_id)
        required_data = self.strategy_analyzer.analyze_requirements(strategy_config)

        # 2. 필요 데이터 패턴 파악
        data_requirements = {
            "KRW-BTC": {
                "1d": max([
                    required_data.get('ATR_period', 0),      # ATR 20일
                    required_data.get('RSI_period', 0),      # RSI 14일
                    required_data.get('HIGH_period', 0),     # HIGH_PRICE 60일
                    required_data.get('VOLUME_period', 0)    # VOLUME 30일
                ]) + 50  # 추가 마진
            }
        }

        # 3. 대량 선행 적재 실행
        for symbol, timeframes in data_requirements.items():
            for timeframe, period in timeframes.items():
                # 200개 한계 활용하여 대량 적재
                await self.router.preload_data(symbol, timeframe, 200)

        # 4. 사용 패턴 학습 업데이트
        self.usage_pattern_learner.update_pattern(strategy_id, required_data)
```

### **사용 패턴 학습 및 최적화**
```python
class UsagePatternLearner:
    def __init__(self):
        self.pattern_db = {}  # 패턴 저장소
        self.request_history = deque(maxlen=1000)  # 최근 1000개 요청 기록

    def learn_request_patterns(self):
        """요청 패턴 분석 및 학습"""

        # 시간대별 요청 패턴 분석
        hourly_patterns = self.analyze_hourly_requests()

        # 심볼-타임프레임 조합 빈도 분석
        combination_frequency = self.analyze_combination_frequency()

        # 연속 요청 패턴 분석 (A 요청 후 B 요청 확률)
        sequence_patterns = self.analyze_sequence_patterns()

        return {
            'hourly': hourly_patterns,
            'combinations': combination_frequency,
            'sequences': sequence_patterns
        }

    def predict_next_requests(self, current_request: DataRequest) -> List[DataRequest]:
        """현재 요청 기반 다음 요청 예측"""
        predictions = []

        # 시퀀스 패턴 기반 예측
        if current_request.symbol in self.sequence_patterns:
            next_likely = self.sequence_patterns[current_request.symbol]
            predictions.extend(next_likely[:3])  # 상위 3개만

        return predictions
```

### **API 효율성 최적화 엔진**
```python
class APIOptimizationEngine:
    def __init__(self):
        self.rate_limiter = RateLimiter(
            calls_per_second=10,
            calls_per_minute=600,
            calls_per_hour=6000
        )
        self.batch_scheduler = BatchScheduler()
        self.request_queue = asyncio.Queue()

    async def optimize_batch_requests(self, requests: List[DataRequest]) -> Dict[str, List[CandleData]]:
        """여러 요청을 효율적으로 배치 처리"""

        # 1. 동일 symbol+timeframe 요청 통합
        grouped_requests = self.group_by_symbol_timeframe(requests)

        # 2. 최대 필요 개수로 통합 (200개 한계 활용)
        optimized_requests = []
        for group_key, group_requests in grouped_requests.items():
            max_count = max(req.count for req in group_requests)
            optimized_requests.append(DataRequest(
                symbol=group_requests[0].symbol,
                timeframe=group_requests[0].timeframe,
                count=min(max_count, 200)  # 200개 한계
            ))

        # 3. Rate Limit 준수하여 순차 실행
        results = {}
        for request in optimized_requests:
            await self.rate_limiter.acquire()
            api_result = await self.call_upbit_api(request)
            results[f"{request.symbol}_{request.timeframe}"] = api_result

        return results
```

---

## 🎯 **1차 구현 로드맵 및 검증 (151-200줄: 연결과 관리)**

### **Phase 1: 기본 캐시 시스템 (1주차)**
```yaml
Day 1-2: MarketDataRouter 기본 구현
- 데이터 요청 라우팅 로직
- 캐시 우선순위 처리
- 기본 메모리 캐시 구현

Day 3-4: HybridCache 구현
- 3계층 캐시 구조 완성
- SQLite DB 연동 및 인덱스 최적화
- LRU 메모리 관리

Day 5-7: 기본 통합 테스트
- 계산기와 연동 테스트
- 성능 벤치마크 측정
- 기본 캐시 효율성 검증
```

### **Phase 2: 지능형 최적화 (2주차)**
```yaml
Day 8-10: IntelligentPreloader 구현
- 전략 분석 엔진
- 사용 패턴 학습 시스템
- 선행 적재 스케줄러

Day 11-12: APIOptimizer 완성
- 배치 요청 최적화
- Rate Limit 관리
- 백오프 재시도 전략

Day 13-14: 통합 최적화 및 검증
- 전체 시스템 통합 테스트
- 성능 목표 달성 검증
- 문서화 및 모니터링 구축
```

### **성능 검증 기준**
```yaml
정량적 목표:
- API 호출 감소: 2,400회/일 → 480회/일 (80% 감소)
- 응답시간 단축: 150ms → 15ms (90% 단축)
- 캐시 히트율: 메모리 90% + DB 95%
- 메모리 사용량: 100MB 이하 유지

정성적 목표:
- 매매 변수 계산기 즉시 응답
- 실시간 계산 지연 없음
- 시스템 안정성 99.9% 유지
- 확장성 확보 (다른 심볼 추가 용이)
```

### **2차 확장 계획 (1개월 후)**
```yaml
실시간 WebSocket 연동:
- 업비트 ticker, orderbook 실시간 구독
- VirtualCandle 실시간 업데이트
- 진행중 타임프레임 즉시 반영

다중 심볼 지원:
- KRW-ETH, KRW-XRP 등 확장
- 심볼별 독립 캐시 관리
- 메모리 사용량 최적화

고급 예측 알고리즘:
- 머신러닝 기반 요청 예측
- 시장 상황별 적응형 캐싱
- 자동 캐시 크기 조정
```

### **관련 문서 및 다음 단계**
```yaml
필수 참조:
- NOW_백본시스템현황.md - 현재 Infrastructure 상태
- NOW_핵심백본5개.md - Database, Repositories 연동
- RULE_문서작성표준.md - 구현 문서 작성 규칙

구현 후 작성 예정:
- STAT_캐시성능측정.md - 1차 구현 성능 결과
- GUIDE_캐시시스템사용법.md - 개발자 사용 가이드
- PLAN_실시간연동v2.md - 2차 WebSocket 확장 계획
```

**1차 목표**: 매매 변수 계산기의 **즉시 응답 지원**으로 실시간 트레이딩 기반 완성 🚀
