# 🚀 **통합 마켓 데이터 백본 시스템 V2.0 - 전문가 권고 반영 아키텍처**

> **사용자 요구사항**: "REST API와 WebSocket을 매번 구분해서 쓰지 말고, 하나의 내부 API처럼 통합하여 개발자는 단일 인터페이스로 호출하면 시스템이 알아서 최적화해서 데이터를 제공하는 시스템"
> **전문가 권고**: SmartChannelRouter를 통한 지능적 채널 라우팅 및 데이터 구조 통일

## **🎯 설계 목표 (전문가 권고 반영)**

### **1. 개발자 경험 단순화**
```python
# 기존 방식 (복잡)
rest_client = UpbitClient()
websocket_client = UpbitWebSocketClient()

if need_realtime:
    data = await websocket_client.subscribe_ticker(["KRW-BTC"])
else:
    data = await rest_client.get_tickers(["KRW-BTC"])

# 새로운 방식 (전문가 권고: UnifiedMarketDataAPI)
unified_api = UnifiedMarketDataAPI()
data = await unified_api.get_ticker("KRW-BTC")  # SmartChannelRouter가 최적 채널 자동 선택
```

### **2. 전문가 권고사항 적용**
- **SmartChannelRouter**: 요청 빈도/실시간성 감지 → 자동 채널 전환
- **데이터 구조 통일**: REST "market" ↔ WebSocket "code" 필드명 매핑
- **통합 에러 처리**: HTTP 429 ↔ WebSocket INVALID_AUTH 동일 예외로 처리
- **하이브리드 최적화**: "초기 REST + 이후 WebSocket 지속 업데이트" 패턴

## **🏗️ 아키텍처 설계 (전문가 권고 반영)**

### **전체 시스템 구조**
```
┌─────────────────────────────────────────────────────────────────────┐
│                        Application Layer                            │
│  (Chart Viewer, Trading Engine, Strategy Manager, etc.)            │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ 통합 API
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   UnifiedMarketDataAPI                              │
│                    (전문가 권고: 투명한 통합 인터페이스)                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │SmartChannelRouter│  │  Data Unifier   │  │ Session Manager │      │
│  │- 빈도 감지      │  │- 필드명 통일     │  │- 연결 관리      │      │
│  │- 채널 자동 선택  │  │- 포맷 표준화     │  │- 재연결 로직    │      │
│  │- 폴백 처리      │  │- 에러 통합      │  │- 라이프사이클    │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
└───────────┬─────────────────────┬─────────────────────┬─────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
  │  REST Channel   │    │WebSocket Channel│    │  Error Recovery │
  │   (REST API)    │    │  (WebSocket)    │    │     System      │
  │                 │    │                 │    │                 │
  │ - Rate Limit    │    │ - Connection    │    │ - Health Check  │
  │ - Retry Logic   │    │ - Reconnection  │    │ - Fallback      │
  │ - Caching       │    │ - Subscription  │    │ - Circuit Break │
  └─────────────────┘    └─────────────────┘    └─────────────────┘
            │                     │                     │
            └─────────┬─────────────┘                     │
                      ▼                                   ▼
            ┌─────────────────┐                ┌─────────────────┐
            │   Upbit APIs    │                │   Monitoring    │
            │                 │                │                 │
            │ - REST API      │                │ - Metrics       │
            │ - WebSocket     │                │ - Alerting      │
            └─────────────────┘                └─────────────────┘
```

## **🔧 핵심 컴포넌트 설계**

### **1. MarketDataBackbone (Public Interface)**
```python
class MarketDataBackbone:
    """
    통합 마켓 데이터 백본 - 단일 진입점

    개발자는 이 클래스만 사용하면 됨
    내부적으로 REST API와 WebSocket을 최적화하여 활용
    """

    async def get_ticker(self, symbol: str,
                        realtime: bool = False,
                        priority: Priority = Priority.NORMAL) -> TickerData:
        """현재가 조회 - 시스템이 자동 최적화"""

    async def get_candles(self, symbol: str,
                         timeframe: str,
                         count: int,
                         strategy: DataStrategy = DataStrategy.AUTO) -> List[CandleData]:
        """캔들 데이터 조회 - 최적 채널 선택"""

    async def subscribe_realtime(self, symbol: str,
                               data_types: List[DataType],
                               callback: Callable) -> SubscriptionId:
        """실시간 구독 - WebSocket 자동 관리"""

    async def get_orderbook(self, symbol: str,
                           levels: int = 15) -> OrderbookData:
        """호가창 조회 - 실시간/스냅샷 자동 선택"""
```

### **2. Request Router (지능적 채널 선택)**
```python
class RequestRouter:
    """
    요청 특성 분석 후 최적 채널 선택

    - 대량 과거 데이터 → REST API
    - 실시간 데이터 → WebSocket
    - 호가창/현재가 → WebSocket 우선, 실패시 REST
    - 성능 모니터링 기반 동적 조정
    """

    def analyze_request(self, request: DataRequest) -> ChannelDecision:
        """요청 분석 후 최적 채널 결정"""

    def get_performance_metrics(self) -> Dict[str, PerformanceMetric]:
        """각 채널 성능 지표"""

    def update_routing_strategy(self, metrics: PerformanceMetric):
        """성능 기반 라우팅 전략 업데이트"""
```

### **3. Data Unifier (포맷 통합 엔진)**
```python
class DataUnifier:
    """
    REST API와 WebSocket의 서로 다른 포맷을
    하나의 일관된 형식으로 통합

    - 필드명 표준화 (trade_price vs tp)
    - 데이터 타입 통일 (문자열 → Decimal)
    - 타임스탬프 표준화 (UTC)
    - 검증 및 정제
    """

    def unify_ticker_data(self, raw_data: Dict, source: DataSource) -> TickerData:
        """현재가 데이터 통합"""

    def unify_candle_data(self, raw_data: List[Dict], source: DataSource) -> List[CandleData]:
        """캔들 데이터 통합"""

    def unify_orderbook_data(self, raw_data: Dict, source: DataSource) -> OrderbookData:
        """호가창 데이터 통합"""
```

### **4. Session Manager (연결 라이프사이클 관리)**
```python
class SessionManager:
    """
    WebSocket 연결을 프로그램 전체 생명주기 동안 관리

    - 시작시 연결, 종료시 정리
    - 120초 타임아웃 방지 (PING)
    - 자동 재연결
    - 구독 상태 복원
    """

    async def initialize(self):
        """프로그램 시작시 WebSocket 연결"""

    async def maintain_connections(self):
        """연결 유지 (백그라운드)"""

    async def handle_disconnection(self, connection: WebSocketConnection):
        """연결 끊김 처리 및 재연결"""
```

## **📊 데이터 통합 스펙**

### **표준화된 데이터 모델**
```python
@dataclass(frozen=True)
class UnifiedTickerData:
    """통합 현재가 데이터"""
    symbol: str
    current_price: Decimal
    change_rate: Decimal  # 변화율 (%)
    change_amount: Decimal  # 변화액
    volume_24h: Decimal
    high_24h: Decimal
    low_24h: Decimal
    prev_closing_price: Decimal
    timestamp: datetime
    source: DataSource  # REST 또는 WebSocket

@dataclass(frozen=True)
class UnifiedCandleData:
    """통합 캔들 데이터"""
    symbol: str
    timeframe: str
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    timestamp: datetime
    source: DataSource

@dataclass(frozen=True)
class UnifiedOrderbookData:
    """통합 호가창 데이터"""
    symbol: str
    asks: List[OrderbookUnit]  # 매도호가
    bids: List[OrderbookUnit]  # 매수호가
    total_ask_size: Decimal
    total_bid_size: Decimal
    spread_percent: Decimal
    timestamp: datetime
    source: DataSource
```

### **포맷 변환 맵핑**
```python
FIELD_MAPPING = {
    "REST_API": {
        "trade_price": "current_price",
        "signed_change_rate": "change_rate",
        "signed_change_price": "change_amount",
        "acc_trade_volume_24h": "volume_24h",
        # ... 전체 맵핑
    },
    "WEBSOCKET_DEFAULT": {
        "trade_price": "current_price",
        "signed_change_rate": "change_rate",
        # ... 전체 맵핑
    },
    "WEBSOCKET_SIMPLE": {
        "tp": "current_price",
        "scr": "change_rate",
        "scp": "change_amount",
        # ... 축약어 맵핑
    }
}
```

## **⚡ 성능 최적화 전략**

### **1. 지능적 채널 선택 로직**
```python
def choose_channel(request: DataRequest) -> ChannelDecision:
    """
    요청 특성 분석 후 최적 채널 선택
    """

    # 1. 실시간 요구사항 체크
    if request.requires_realtime:
        return ChannelDecision.WEBSOCKET_PREFERRED

    # 2. 데이터 볼륨 체크
    if request.count > 200:  # 대량 데이터
        return ChannelDecision.REST_API_PREFERRED

    # 3. 호가창/현재가는 WebSocket 우선
    if request.data_type in [DataType.TICKER, DataType.ORDERBOOK]:
        return ChannelDecision.WEBSOCKET_PREFERRED

    # 4. 성능 히스토리 기반 선택
    rest_latency = get_average_latency(Channel.REST_API)
    ws_latency = get_average_latency(Channel.WEBSOCKET)

    if rest_latency < ws_latency * 1.5:  # REST가 충분히 빠르면
        return ChannelDecision.REST_API_PREFERRED
    else:
        return ChannelDecision.WEBSOCKET_PREFERRED
```

### **2. 캐싱 및 중복 제거**
```python
class IntelligentCache:
    """
    지능적 캐싱 시스템

    - 같은 요청 중복 제거
    - TTL 기반 캐시 무효화
    - 실시간 데이터는 캐시하지 않음
    """

    def get_cached_data(self, request: DataRequest) -> Optional[Any]:
        """캐시된 데이터 조회"""

    def cache_data(self, request: DataRequest, data: Any, ttl: int):
        """데이터 캐싱"""

    def invalidate_cache(self, symbol: str, data_type: DataType):
        """캐시 무효화"""
```

### **3. 연결 풀링 및 재사용**
```python
class ConnectionPool:
    """
    WebSocket 연결 풀 관리

    - 심볼별 연결 재사용
    - 유휴 연결 정리
    - 부하 분산
    """

    def get_connection(self, symbol: str) -> WebSocketConnection:
        """연결 획득 (재사용 또는 신규 생성)"""

    def release_connection(self, connection: WebSocketConnection):
        """연결 반환"""

    def cleanup_idle_connections(self):
        """유휴 연결 정리"""
```

## **🛡️ 장애 복구 시스템**

### **1. Circuit Breaker 패턴**
```python
class CircuitBreaker:
    """
    회로 차단기 패턴으로 장애 전파 방지

    - 연속 실패시 일시적 차단
    - 점진적 복구
    - 다른 채널로 자동 전환
    """

    def call(self, func: Callable, *args, **kwargs):
        """보호된 함수 호출"""

    def handle_failure(self, exception: Exception):
        """실패 처리"""

    def attempt_recovery(self):
        """복구 시도"""
```

### **2. Health Check & Monitoring**
```python
class HealthMonitor:
    """
    각 채널 상태 모니터링

    - 응답 시간 측정
    - 성공률 추적
    - 에러 패턴 분석
    """

    def check_rest_api_health(self) -> HealthStatus:
        """REST API 상태 체크"""

    def check_websocket_health(self) -> HealthStatus:
        """WebSocket 상태 체크"""

    def get_performance_report(self) -> PerformanceReport:
        """성능 리포트 생성"""
```

## **🔄 단계별 구현 계획**

### **Phase 1: 핵심 인프라 (2주)**
- [ ] 기본 MarketDataBackbone 클래스
- [ ] 간단한 Request Router
- [ ] 기본 Data Unifier (ticker, candle만)
- [ ] WebSocket Session Manager

### **Phase 2: 지능적 최적화 (2주)**
- [ ] 성능 기반 채널 선택
- [ ] 캐싱 시스템
- [ ] 연결 풀링
- [ ] 기본 장애 복구

### **Phase 3: 고급 기능 (2주)**
- [ ] Circuit Breaker
- [ ] Health Monitoring
- [ ] 실시간 구독 관리
- [ ] 전체 데이터 타입 지원

### **Phase 4: 프로덕션 준비 (1주)**
- [ ] 성능 테스트
- [ ] 스트레스 테스트
- [ ] 문서화
- [ ] 기존 시스템 통합

## **🎯 성공 지표**

### **개발자 경험**
- **API 단순화**: 기존 2개 클라이언트 → 1개 백본
- **코드 감소**: 채널 선택 로직 50% 감소
- **에러 처리**: 자동 복구로 안정성 99.9%

### **성능 향상**
- **응답 시간**: WebSocket 활용으로 50% 개선
- **대역폭**: 중복 요청 제거로 30% 절약
- **안정성**: 자동 장애 복구로 가용성 99.9%

### **운영 효율성**
- **모니터링**: 통합 메트릭으로 운영 복잡도 감소
- **확장성**: 새로운 데이터 소스 쉽게 추가
- **유지보수**: 단일 백본으로 유지보수 비용 감소

---

이것이 **진짜 프로덕션급 통합 백본 시스템**의 설계입니다. 단순한 래퍼가 아닌, 업비트 API의 복잡성을 완전히 추상화하고 개발자에게는 단일하고 일관된 인터페이스를 제공하는 시스템입니다.

**핵심은 "개발자는 더 이상 REST와 WebSocket을 구분해서 생각할 필요가 없다"는 것입니다.**
