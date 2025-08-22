# 📋 TASK_20250822_07: Smart Data Provider 개발

## 🎯 태스크 목표
- **주요 목표**: 마켓 데이터가 DB에 잘 보관되어 효율적으로 제공되는 통합 시스템 구축
- **완료 기준**:
  - ✅ 4개 통합 API 제공 (캔들/티커/호가/체결)
  - ✅ SQLite 캔들 자동 캐시 + 메모리 실시간 캐시
  - ✅ 대용량 요청 자동 분할 처리
  - ✅ 우선순위 기반 처리 (실거래 우선)
  - ✅ Smart Router V2.0 완전 활용

## 📊 현재 상황 분석 (2025-08-22 기준)

### ✅ **기반 시스템 현황**
- **Smart Router V2.0** ✅ 완료 - 채널 선택, API 호출, 장애 복구
- **SQLite 스키마** ✅ 준비 - market_data.sqlite3 구조 완성
- **기본 클라이언트** ✅ 완료 - UpbitPublicClient, UpbitWebSocketClient

### 🎯 **Smart Data Provider 역할 정의**

#### **핵심 책임**
- **단일 진입점**: 모든 클라이언트가 하나의 API로 마켓 데이터 접근
- **자동 캐시**: SQLite (캔들) + 메모리 (실시간) 이중 캐시 시스템
- **스마트 분할**: 대용량 요청을 자동으로 적절한 크기로 분할
- **우선순위 처리**: 실거래 > 차트뷰어 > 백테스터 순 처리
- **투명한 최적화**: 내부 복잡성을 클라이언트에서 완전히 숨김

#### **클라이언트별 사용 시나리오**
```
🖥️ 차트뷰어
요청: await provider.get_candles("KRW-BTC", "1m", count=1000, priority=NORMAL)
처리: SQLite 캐시 확인 → 부족한 부분만 Smart Router 요청 → 자동 병합
응답: 1000개 캔들 데이터 (< 2초, 캐시 히트시 < 100ms)

🔍 스크리너
요청: await provider.get_tickers(KRW_symbols, priority=HIGH)
처리: 메모리 캐시 확인 → 최신 데이터 Smart Router 요청 → 빠른 응답
응답: 189개 KRW 마켓 티커 (< 500ms)

📈 백테스터
요청: await provider.get_candles("KRW-BTC", "1m", start="2024-01-01", priority=LOW)
처리: SQLite 우선 조회 → 부족한 부분만 백그라운드 수집 → 점진적 제공
응답: 3개월 데이터 (SQLite 히트시 즉시, API 수집시 진행률 추적)

🤖 실거래봇
요청: await provider.get_tickers(["KRW-BTC"], priority=CRITICAL)
처리: 메모리 캐시 우선 → 1초 이내 데이터면 즉시 반환 → 없으면 최우선 처리
응답: 현재가 데이터 (< 50ms)
```

## 🛠️ Smart Data Provider 아키텍처 설계

### 🏗️ **2계층 통합 구조**

```
📱 클라이언트 (차트뷰어, 백테스터, 실거래봇)
    ↓ 단일 API 호출
🧠 Layer 2: Smart Data Provider
    ├─ 요청 분석 및 우선순위 처리
    ├─ 캐시 확인 (SQLite + 메모리)
    ├─ 자동 분할 (대용량 요청)
    ├─ 응답 병합 및 형식 통일
    └─ 성능 모니터링
    ↓
💾 Layer 1: Storage & Routing
    ├─ Smart Router V2.0 (기존 완성)
    ├─ SQLite 캔들 스토리지
    ├─ 메모리 실시간 캐시 (TTL)
    └─ Rate Limit 관리
    ↓
🌐 업비트 API (REST/WebSocket)
```

### 📊 **핵심 API 인터페이스 설계**

```python
class SmartDataProvider:
    """통합 마켓 데이터 제공자 - 모든 복잡성을 내부에서 처리"""

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        priority: Priority = Priority.NORMAL
    ) -> DataResponse:
        """캔들 데이터 조회 - SQLite 캐시 우선, 자동 분할 처리"""

    async def get_tickers(
        self,
        symbols: List[str],
        priority: Priority = Priority.NORMAL
    ) -> DataResponse:
        """현재가 조회 - 메모리 캐시 우선, Smart Router 폴백"""

    async def get_orderbook(
        self,
        symbols: List[str],
        priority: Priority = Priority.NORMAL
    ) -> DataResponse:
        """호가 조회 - 실시간 메모리 캐시 + WebSocket 연동"""

    async def get_trades(
        self,
        symbol: str,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        priority: Priority = Priority.NORMAL
    ) -> DataResponse:
        """체결 조회 - 실시간 + 히스토리 데이터 통합"""

# 우선순위 열거형
class Priority(Enum):
    CRITICAL = 1    # 실거래봇 (< 50ms)
    HIGH = 2        # 실시간 모니터링 (< 100ms)
    NORMAL = 3      # 차트뷰어 (< 500ms)
    LOW = 4         # 백테스터 (백그라운드)

# 통합 응답 구조
@dataclass
class DataResponse:
    success: bool
    data: List[Dict[str, Any]]
    metadata: ResponseMetadata
    error: Optional[str] = None

@dataclass
class ResponseMetadata:
    priority_used: Priority
    cache_hit: bool
    cache_type: str  # "sqlite", "memory", "api"
    response_time_ms: float
    data_count: int
    split_requests: int  # 분할된 요청 수
    source: str  # "smart_router", "cache", "hybrid"
```

## 🗺️ 체계적 작업 계획 (10일)

### Phase 1: 핵심 구조 설계 (3일)
- [ ] 1.1 SmartDataProvider 메인 클래스 구현
- [ ] 1.2 Priority 기반 요청 처리 시스템
- [ ] 1.3 4개 기본 API 인터페이스 구현
- [ ] 1.4 Smart Router V2.0 연동 어댑터

### Phase 2: 스토리지 시스템 통합 (4일)
- [ ] 2.1 SQLite 캔들 캐시 시스템 구현
- [ ] 2.2 메모리 실시간 캐시 (티커/호가/체결) 구현
- [ ] 2.3 캐시 조정자 - 적중률 최적화 및 TTL 관리
- [ ] 2.4 스토리지 성능 모니터링 및 통계

### Phase 3: 자동화 기능 (2일)
- [ ] 3.1 대용량 요청 자동 분할 시스템
- [ ] 3.2 분할된 응답 자동 병합 시스템
- [ ] 3.3 우선순위별 큐 관리 및 부하 제어
- [ ] 3.4 백그라운드 진행률 추적 시스템

### Phase 4: 통합 테스트 및 최적화 (1일)
- [ ] 4.1 클라이언트별 시나리오 테스트
- [ ] 4.2 성능 벤치마크 및 캐시 효율성 검증
- [ ] 4.3 기존 시스템 호환성 어댑터
- [ ] 4.4 모니터링 대시보드 및 경고 시스템

## 🛠️ 단순화된 파일 구조

```
smart_data_provider/                   # 통합 데이터 제공자
├── __init__.py
├── core/                              # 핵심 구현
│   ├── __init__.py
│   ├── smart_data_provider.py         # 메인 제공자 클래스
│   ├── request_processor.py           # 요청 처리 및 우선순위
│   ├── response_builder.py            # 응답 구조 생성
│   └── performance_monitor.py         # 성능 모니터링
├── cache/                             # 캐시 시스템
│   ├── __init__.py
│   ├── sqlite_candle_cache.py         # SQLite 캔들 저장소
│   ├── memory_realtime_cache.py       # 메모리 실시간 캐시
│   ├── cache_coordinator.py           # 캐시 조정자
│   └── cache_statistics.py            # 캐시 통계 및 최적화
├── processing/                        # 요청 처리
│   ├── __init__.py
│   ├── request_splitter.py            # 대용량 요청 분할
│   ├── response_merger.py             # 응답 병합
│   ├── priority_queue.py              # 우선순위 큐 관리
│   └── background_processor.py        # 백그라운드 처리
├── adapters/                          # 외부 연동
│   ├── __init__.py
│   ├── smart_router_adapter.py        # Smart Router V2.0 연동
│   ├── legacy_client_adapter.py       # 기존 클라이언트 호환
│   └── database_adapter.py            # SQLite 연동
├── models/                            # 데이터 모델
│   ├── __init__.py
│   ├── requests.py                    # 요청 모델
│   ├── responses.py                   # 응답 모델
│   ├── priority.py                    # 우선순위 열거형
│   └── cache_models.py                # 캐시 데이터 모델
└── utils/                             # 유틸리티
    ├── __init__.py
    ├── time_utils.py                  # 시간 처리 유틸
    ├── validation.py                  # 요청 검증
    └── metrics.py                     # 성능 지표 수집
```

## 🎯 핵심 구현 전략

### 1. **기존 자산 100% 활용**
```python
class SmartDataProvider:
    def __init__(self):
        # 기존 완성된 시스템 활용
        self.smart_router = get_smart_router()  # Smart Router V2.0
        self.db_manager = DatabaseManager()     # 기존 DB 매니저

        # 새로 추가되는 캐시 시스템
        self.candle_cache = SQLiteCandleCache()
        self.realtime_cache = MemoryRealtimeCache(ttl=60)
        self.priority_queue = PriorityQueue()
```

### 2. **스마트 캐시 전략**
```python
async def get_candles(self, symbol: str, timeframe: str, count: int):
    # 1. SQLite 캐시 확인
    cached = await self.candle_cache.get(symbol, timeframe, count)
    if cached.is_complete():
        return self._build_response(cached.data, cache_hit=True, cache_type="sqlite")

    # 2. 부족한 부분만 Smart Router로 요청
    missing_ranges = cached.get_missing_ranges(count)
    if missing_ranges:
        for range_req in missing_ranges:
            fresh_data = await self.smart_router.get_candles(symbol, timeframe, range_req)
            await self.candle_cache.store(fresh_data)

    # 3. 완전한 데이터 반환
    complete_data = await self.candle_cache.get(symbol, timeframe, count)
    return self._build_response(complete_data, cache_hit="hybrid", cache_type="sqlite+api")
```

### 3. **자동 분할 및 병합**
```python
async def _handle_large_request(self, symbol: str, timeframe: str, count: int):
    if count <= 200:  # 업비트 API 한계
        return await self._single_request(symbol, timeframe, count)

    # 자동 분할 (200개씩)
    chunks = self.splitter.split_candle_request(symbol, timeframe, count)
    logger.info(f"대용량 요청 분할: {count}개 → {len(chunks)}개 청크")

    # 병렬 처리
    tasks = [self._process_chunk(chunk) for chunk in chunks]
    chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

    # 자동 병합
    merged_result = self.merger.merge_candle_results(chunk_results)
    return self._build_response(merged_result, split_requests=len(chunks))
```

### 4. **우선순위 기반 처리**
```python
async def _process_with_priority(self, request: DataRequest):
    if request.priority == Priority.CRITICAL:
        # 실거래봇: 즉시 처리, 캐시 우선
        return await self._critical_path(request)

    elif request.priority == Priority.LOW:
        # 백테스터: 백그라운드 큐에 등록
        return await self._background_queue.add(request)

    else:
        # 일반: 표준 경로
        return await self._standard_path(request)
```

## 🔗 우선순위별 처리 흐름 상세

### **CRITICAL 경로 (실거래봇)**
```
🤖 실거래봇 요청
    ↓ priority=CRITICAL 확인
🧠 Smart Data Provider
    ├─ 메모리 캐시 확인 (< 1초 데이터면 즉시 반환)
    ├─ 캐시 없으면 Smart Router 최우선 처리
    └─ 응답 시간 < 50ms 보장
    ↓
🤖 실거래봇 (즉시 매매 신호 판단)
```

### **NORMAL 경로 (차트뷰어)**
```
🖥️ 차트뷰어 요청 (1000개 캔들)
    ↓ 대용량 요청 감지
🧠 Smart Data Provider
    ├─ SQLite 캐시 확인 (기존 데이터 최대한 활용)
    ├─ 부족한 부분만 자동 분할 (5번의 200개 요청)
    ├─ Smart Router 병렬 처리
    ├─ SQLite 자동 저장
    └─ 완전한 데이터 병합하여 응답
    ↓
🖥️ 차트뷰어 (< 2초 내 1000개 캔들 렌더링)
```

### **LOW 경로 (백테스터)**
```
📈 백테스터 요청 (3개월 데이터)
    ↓ priority=LOW 확인
🧠 Smart Data Provider
    ├─ SQLite 우선 조회 (기존 데이터 최대한 활용)
    ├─ 부족한 구간 식별 및 백그라운드 큐 등록
    ├─ 시스템 부하 확인 후 순차 처리
    ├─ 진행률 추적 및 피드백
    └─ 완료된 구간부터 점진적 제공
    ↓
📈 백테스터 (완료된 구간부터 순차 시뮬레이션)
```

## 🎯 성공 기준

### 기능적 성공 기준
- ✅ **4개 API**: 캔들/티커/호가/체결 API 완벽 동작
- ✅ **자동 캐시**: SQLite + 메모리 이중 캐시로 95% 이상 적중률
- ✅ **자동 분할**: 대용량 요청 자동 처리, 클라이언트 인식 불가
- ✅ **우선순위**: CRITICAL < 50ms, LOW는 백그라운드 처리

### 성능적 성공 기준
- ✅ **캐시 적중률**: SQLite 90% 이상, 메모리 80% 이상
- ✅ **응답 시간**: CRITICAL < 50ms, NORMAL < 500ms
- ✅ **처리량**: 동시 100개 요청 처리 가능
- ✅ **메모리 효율성**: 실시간 캐시 100MB 이하 유지

### 운영적 성공 기준
- ✅ **API 호출 절약**: 기존 대비 70% 이상 API 호출 감소
- ✅ **DB 효율성**: SQLite 캔들 데이터 중복률 5% 이하
- ✅ **장애 대응**: Smart Router 장애 시 자동 폴백
- ✅ **모니터링**: 실시간 성능 지표 및 캐시 통계

## 💡 작업 시 주의사항

### Smart Router V2.0 연동 원칙
- **완전 활용**: 기존 33개 테스트 통과한 안정적 시스템 그대로 사용
- **어댑터 패턴**: SmartRouterAdapter로 인터페이스 통일
- **성능 보장**: Smart Router의 채널 선택 로직 100% 활용
- **장애 대응**: Smart Router의 폴백 메커니즘 그대로 상속

### 캐시 시스템 원칙
- **SQLite 우선**: 캔들 데이터는 반드시 SQLite에 영구 저장
- **메모리 보조**: 실시간 데이터만 메모리 캐시 (TTL 관리)
- **스마트 갱신**: 오래된 캐시는 백그라운드에서 자동 갱신
- **용량 관리**: SQLite 자동 정리, 메모리 LRU 정책

### 성능 최적화 원칙
- **분할 최적화**: 업비트 API 제한(200개)에 맞춘 자동 분할
- **병렬 처리**: asyncio.gather로 동시 요청 최대화
- **우선순위 보장**: 실거래 요청은 절대 지연 없음
- **진행률 피드백**: 대용량 요청시 실시간 진행 상황 제공

## 🚀 즉시 시작할 작업

### 1. 기존 시스템 인터페이스 분석
```powershell
# Smart Router V2.0 API 확인
Get-ChildItem upbit_auto_trading\infrastructure\market_data_backbone\smart_routing -Include "*.py" -Recurse

# 기존 클라이언트 사용 패턴 분석
python -c "
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.main_system_adapter import get_market_data_adapter
adapter = get_market_data_adapter()
print('현재 어댑터 상태:', adapter.get_performance_summary())
"
```

### 2. SQLite 캐시 테이블 설계
```sql
-- 캔들 캐시 테이블 (market_data.sqlite3)
CREATE TABLE candle_cache (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    open_price DECIMAL(20,8),
    high_price DECIMAL(20,8),
    low_price DECIMAL(20,8),
    close_price DECIMAL(20,8),
    volume DECIMAL(20,8),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, timeframe, timestamp)
);

CREATE INDEX idx_candle_cache_lookup ON candle_cache(symbol, timeframe, timestamp);
```

### 3. 메모리 캐시 구조 설계
```python
# 실시간 데이터 메모리 캐시
class MemoryRealtimeCache:
    def __init__(self, ttl: int = 60):
        self.ticker_cache = TTLCache(maxsize=500, ttl=ttl)      # 현재가
        self.orderbook_cache = TTLCache(maxsize=200, ttl=10)    # 호가 (짧은 TTL)
        self.trades_cache = TTLCache(maxsize=100, ttl=30)       # 체결
```

## 📋 관련 문서 및 리소스

### 핵심 참고 자료
- **Smart Router V2.0**: `upbit_auto_trading/infrastructure/market_data_backbone/smart_routing/`
- **기존 어댑터**: `smart_routing/main_system_adapter.py`
- **DB 스키마**: `data_info/upbit_autotrading_schema_market_data.sql`

### 설계 참고 문서
- **기존 시스템 분석**: `docs/업비트 마켓 데이터 통합 API 구현 평가 및 방안.md`
- **Smart Router 기획**: `docs/UPBIT_SMART_ROUTER_V2_PLAN.md`

## 🔄 태스크 연관성

### 기반 태스크
- **Smart Router V2.0**: ✅ 완료 (33개 테스트 통과)
- **DB 스키마**: ✅ 완료 (SQLite 구조 준비)

### 후속 태스크
- **클라이언트 마이그레이션**: 기존 시스템을 Smart Data Provider로 전환
- **성능 튜닝**: 운영 환경에서의 캐시 최적화

---

## 📊 **예상 소요 시간**

### 🔥 **단계별 작업 일정**
1. **Phase 1 - 핵심 구조**: 3일
2. **Phase 2 - 스토리지 통합**: 4일
3. **Phase 3 - 자동화 기능**: 2일
4. **Phase 4 - 통합 테스트**: 1일

### 📈 **총 예상 소요 시간**: 10일

---

**시작 조건**: Smart Router V2.0 완료, SQLite 스키마 준비
**핵심 가치**: DB 효율적 보관 + 자동 캐시 + 투명한 복잡성 + Smart Router 활용
**성공 지표**: 캐시 적중률 + API 호출 절약 + 응답 속도 + 시스템 안정성

**🎯 최종 목표**: 마켓 데이터가 DB에 잘 보관되어 모든 클라이언트에게 효율적으로 제공되는 완벽한 통합 시스템!

**🌟 원래 목표 달성**: 이 태스크 완료 시 DB 기반 효율적 마켓 데이터 제공 시스템 완성!
