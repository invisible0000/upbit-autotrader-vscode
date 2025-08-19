# MarketDataBackbone V2 - 핵심 아키텍처 (AI 최적화 문서 1/3)

## 🎯 **현재 상태 요약**
```yaml
Phase 상태: Phase 2.1 완료 (81/81 테스트 통과)
다음 단계: Phase 2.2 실제 API 연동 (3-4일)
긴급 이슈: 800라인 초과 파일 2개 (분리 필요)
```

## 🏗️ **아키텍처 핵심**

### **3계층 분리 구조**
```
MarketDataBackbone V2
├── 데이터 수집 (Collection Layer)
│   ├── SmartChannelRouter: REST/WebSocket 지능 선택
│   ├── RateLimiter: API 호출 제한 관리
│   └── ErrorHandler: 실패 시 자동 복구
├── 데이터 통합 (Unification Layer)
│   ├── FieldMapper: 다양한 API → 표준 형식
│   ├── DataValidator: 데이터 무결성 검증
│   └── CacheManager: 성능 최적화 캐시
└── 데이터 제공 (Service Layer)
    ├── QueryOptimizer: 요청 최적화
    ├── DataProvider: 포지션별 맞춤 제공
    └── PerformanceMonitor: 실시간 성능 감시
```

### **핵심 클래스 구조**
```python
# 1. 통합 API (현재 476라인 → 분리 예정)
class UnifiedMarketDataAPI:
    """모든 마켓 데이터 요청의 단일 진입점"""

    async def get_candles(self, symbol: str, timeframe: str,
                         count: int = 200) -> List[CandleData]:
        """캔들 데이터 수집 (REST/WebSocket 자동 선택)"""

    async def get_orderbook(self, symbol: str) -> OrderbookData:
        """호가 데이터 수집 (WebSocket 우선)"""

    async def get_tickers(self, symbols: List[str]) -> List[TickerData]:
        """현재가 데이터 수집 (최적 채널 선택)"""

# 2. 데이터 통합기 (현재 492라인 → 분리 예정)
class DataUnifier:
    """다양한 소스 데이터를 표준 형식으로 통합"""

    def unify_candle_data(self, raw_data: dict, source: str) -> CandleData:
        """캔들 데이터 표준화"""

    def unify_orderbook_data(self, raw_data: dict, source: str) -> OrderbookData:
        """호가 데이터 표준화"""

# 3. 백본 조정자 (현재 347라인 - 안전)
class MarketDataBackbone:
    """전체 시스템 조정 및 외부 인터페이스"""

    def __init__(self):
        self.unified_api = UnifiedMarketDataAPI()
        self.data_unifier = DataUnifier()
        self.cache_manager = CacheManager()
```

## 📊 **데이터 플로우**

### **요청 처리 과정**
```
1. 요청 접수: MarketDataBackbone.get_candles()
2. 캐시 확인: CacheManager에서 기존 데이터 검색
3. 채널 선택: SmartChannelRouter가 최적 채널 결정
4. 데이터 수집: REST API 또는 WebSocket 호출
5. 데이터 통합: FieldMapper로 표준 형식 변환
6. 유효성 검증: DataValidator로 품질 확인
7. 캐시 저장: 향후 요청 최적화를 위해 저장
8. 결과 반환: 표준 DTO 형식으로 반환
```

### **실시간 업데이트 플로우**
```
1. WebSocket 연결: 시작 시 자동 연결
2. 구독 관리: 필요한 심볼만 선택적 구독
3. 데이터 수신: 실시간 스트림 처리
4. 즉시 통합: 수신 즉시 표준 형식 변환
5. 캐시 업데이트: 기존 데이터 즉시 갱신
6. 이벤트 발행: 구독자들에게 변경 알림
```

## 🚨 **긴급 해결 필요 이슈**

### **800라인 초과 파일 분리**
```yaml
대상 파일:
  - unified_market_data_api.py: 476라인 (위험)
  - data_unifier.py: 492라인 (위험)

분리 계획:
  unified_market_data_api.py →
    - api_client.py (200라인)
    - websocket_client.py (200라인)
    - coordinator.py (76라인)

  data_unifier.py →
    - field_mapper.py (200라인)
    - data_validator.py (200라인)
    - cache_manager.py (92라인)
```

## 🧪 **검증된 기능 (81개 테스트 통과)**

### **Phase 1 기반 기능 (62개 테스트)**
- REST API 기본 호출 및 에러 처리
- WebSocket 연결 및 실시간 데이터 수신
- 다중 타임프레임 데이터 수집
- 캐시 시스템 및 TTL 관리
- 데이터 유효성 검증

### **Phase 2.1 통합 기능 (19개 테스트)**
- SmartChannelRouter 지능형 채널 선택
- FieldMapper 다양한 API 형식 통합
- ErrorUnifier 통합 에러 처리
- PerformanceMonitor 성능 감시

### **전략적 최적화 (7개 시나리오)**
- ROI 기반 데이터 수집 전략
- 포지션별 맞춤 데이터 제공
- 실시간 vs 히스토리 최적 균형

## 🎯 **다음 단계: Phase 2.2**

### **실제 API 연동 (3-4일 예상)**
```python
# 개발 순서
1. 긴급 파일 분리 (1일)
   - 800라인 초과 파일 강제 분리
   - 테스트 마이그레이션

2. 실제 업비트 API 연동 (2일)
   - 업비트 REST API 클라이언트 연결
   - 업비트 WebSocket 클라이언트 연결
   - 실제 데이터로 통합 테스트

3. 성능 최적화 (1일)
   - 실제 데이터 기반 성능 튜닝
   - 캐시 전략 최적화
   - 메모리 사용량 최적화
```

## 🔍 **개발 가이드라인**

### **코드 품질 기준**
- 각 파일 200라인 이하 유지
- 테스트 커버리지 80% 이상
- 명확한 인터페이스 정의
- DDD 아키텍처 준수

### **성능 기준**
- 캔들 200개 로딩: 100ms 이내
- 실시간 업데이트: 50ms 이내
- 메모리 사용: 200MB 이하
- API 호출: Rate Limit 90% 이하

---
*AI 최적화 문서 1/3 - 다음: 02_IMPLEMENTATION_GUIDE.md*
