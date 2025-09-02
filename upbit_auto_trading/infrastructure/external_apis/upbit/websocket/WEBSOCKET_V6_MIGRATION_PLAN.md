# WebSocket v6 핵심 기능 점진적 이식 계획

## 📋 개요

현재 시스템의 기본적인 WebSocket 연결 관리를 `websocket_v6_backup20250902_150200`의 고급 기능들로 점진적으로 업그레이드하는 마이그레이션 계획입니다.

### 🎯 목표
- 안정적이고 확장 가능한 WebSocket 시스템 구축
- 프로덕션 환경에서 연결 지속성 보장
- 메모리 누수 방지 및 자동 정리 시스템 구축
- 고성능 데이터 처리 및 라우팅 시스템 구현

### 📊 현재 상태 분석

| 기능 영역 | 현재 구현도 | 목표 구현도 | 우선순위 |
|-----------|-------------|-------------|----------|
| **연결 관리** | 60% | 95% | 🔥 높음 |
| **구독 관리** | 40% | 90% | 🔥 높음 |
| **데이터 라우팅** | 20% | 85% | 🟡 중간 |
| **모니터링** | 30% | 90% | 🟡 중간 |
| **자동 정리** | 50% | 95% | 🔥 높음 |
| **타입 안전성** | 70% | 90% | 🟢 낮음 |
| **Rate Limiting** | 60% | 85% | 🟡 중간 |

---

## 🚀 Phase 1: GlobalWebSocketManager 핵심 구조 이식 (1-2주)

### 🎯 목표
기본적인 WebSocketManager를 완전한 GlobalWebSocketManager로 업그레이드

### 📋 작업 목록

#### **1.1 핵심 타입 시스템 이식**
- [ ] `types.py` 파일 이식 및 통합
  - `WebSocketType`, `ConnectionState`, `GlobalManagerState` 등
  - `BaseWebSocketEvent`, `TradeEvent`, `MyOrderEvent` 등
  - `SubscriptionSpec`, `ComponentSubscription` 등
- [ ] `exceptions.py` 파일 이식
  - `SubscriptionError`, `RecoveryError` 등
- [ ] 기존 타입 시스템과 호환성 확보

#### **1.2 ConnectionMetrics 시스템 구축**
```python
@dataclass
class ConnectionMetrics:
    """연결별 상세 메트릭스"""
    connection_type: WebSocketType
    is_connected: bool = False
    connect_time: Optional[float] = None
    last_message_time: Optional[float] = None
    message_count: int = 0
    error_count: int = 0
    reconnect_count: int = 0
    bytes_received: int = 0
    current_subscriptions: int = 0

    @property
    def uptime_seconds(self) -> float: ...
    @property
    def messages_per_second(self) -> float: ...
    @property
    def error_rate(self) -> float: ...
    @property
    def health_score(self) -> float: ...
```

#### **1.3 EpochManager 구현**
```python
class EpochManager:
    """재연결 시 데이터 순서 보장"""

    async def increment_epoch(self, connection_type: WebSocketType) -> int: ...
    def get_current_epoch(self, connection_type: WebSocketType) -> int: ...
    def is_current_epoch(self, connection_type: WebSocketType, epoch: int) -> bool: ...
```

#### **1.4 GlobalWebSocketManager 기본 구조**
- [ ] 싱글톤 패턴 구현 (AsyncLock 기반)
- [ ] WeakRef 기반 컴포넌트 관리
- [ ] 기본적인 연결 생명주기 관리
- [ ] 구독 관리 위임 구조

### 🧪 테스트 계획
- [ ] 기존 기능 무중단 동작 확인
- [ ] 새로운 타입 시스템 검증
- [ ] ConnectionMetrics 정확성 테스트
- [ ] 메모리 누수 테스트

### 📈 예상 효과
- **연결 관리**: 60% → 80%
- **타입 안전성**: 70% → 85%
- **모니터링**: 30% → 60%

---

## 🔄 Phase 2: SubscriptionStateManager 및 자동 정리 시스템 (1-2주)

### 🎯 목표
구독 상태의 중앙 집중식 관리 및 자동 정리 시스템 구축

### 📋 작업 목록

#### **2.1 SubscriptionStateManager 이식**
```python
class SubscriptionStateManager:
    """구독 상태 중앙 관리"""

    async def register_component_subscriptions(
        self,
        component_id: str,
        subscriptions: List[SubscriptionSpec]
    ) -> ComponentSubscription: ...

    async def unregister_component(self, component_id: str) -> None: ...

    def get_active_subscriptions(self) -> Dict[str, ComponentSubscription]: ...

    async def optimize_subscription_requests(self) -> List[Dict[str, Any]]: ...
```

#### **2.2 WeakRef 기반 자동 정리 시스템**
```python
class GlobalWebSocketManager:
    def __init__(self):
        # WeakRef 컴포넌트 관리
        self._components: Dict[str, weakref.ref] = {}

    async def register_component(
        self,
        component_id: str,
        component_instance: Any,
        subscriptions: List[SubscriptionSpec],
        callback: Callable[[BaseWebSocketEvent], None]
    ) -> ComponentSubscription:
        # WeakRef 콜백으로 자동 정리 설정
        weak_ref = weakref.ref(
            component_instance,
            lambda ref: asyncio.create_task(self._cleanup_component(component_id))
        )
        self._components[component_id] = weak_ref
```

#### **2.3 백그라운드 모니터링 시스템**
```python
def _start_background_tasks(self):
    """백그라운드 태스크 시작"""
    self._health_monitor_task = asyncio.create_task(self._health_monitor_task())
    self._cleanup_monitor_task = asyncio.create_task(self._cleanup_monitor_task())

async def _health_monitor_task(self) -> None:
    """30초마다 연결 상태 및 WeakRef 정리"""
    while True:
        try:
            await asyncio.sleep(30.0)
            await self._check_connection_health()
            await self._cleanup_dead_references()
        except Exception as e:
            self.logger.error(f"헬스 모니터링 오류: {e}")

async def _cleanup_monitor_task(self) -> None:
    """1분마다 죽은 참조 자동 정리"""
    while True:
        await asyncio.sleep(60.0)
        await self._cleanup_dead_components()
```

### 🧪 테스트 계획
- [ ] 컴포넌트 자동 정리 검증
- [ ] WeakRef 콜백 동작 확인
- [ ] 메모리 누수 방지 테스트
- [ ] 구독 최적화 효과 측정

### 📈 예상 효과
- **구독 관리**: 40% → 80%
- **자동 정리**: 50% → 90%
- **메모리 효율성**: 크게 개선

---

## 📊 Phase 3: DataRoutingEngine 및 고급 모니터링 (1-2주)

### 🎯 목표
효율적인 데이터 분배 시스템 및 실시간 성능 모니터링 구축

### 📋 작업 목록

#### **3.1 DataRoutingEngine 구현**
```python
class DataRoutingEngine:
    """중앙집중식 데이터 라우팅"""

    def __init__(self):
        self._routes: Dict[Tuple[str, DataType], List[Callable]] = {}
        self._performance_stats: Dict[str, Any] = {}

    async def route_event(self, event: BaseWebSocketEvent) -> None:
        """이벤트를 적절한 콜백들로 라우팅"""

    def register_route(
        self,
        symbol: str,
        data_type: DataType,
        callback: Callable,
        component_id: str
    ) -> None: ...

    def unregister_routes(self, component_id: str) -> None: ...

    def get_routing_statistics(self) -> Dict[str, Any]: ...
```

#### **3.2 고급 성능 모니터링**
```python
async def _metrics_collector_task(self) -> None:
    """10초마다 성능 메트릭스 자동 업데이트"""
    while True:
        await asyncio.sleep(10.0)

        # 연결별 메트릭스 업데이트
        for connection_type, metrics in self._connection_metrics.items():
            await self._update_connection_metrics(connection_type, metrics)

        # 전역 성능 지표 계산
        await self._calculate_global_performance()

async def get_performance_metrics(self) -> PerformanceMetrics:
    """실시간 성능 지표 반환"""
    return PerformanceMetrics(
        total_subscriptions=len(self._subscription_manager.get_active_subscriptions()),
        messages_processed=sum(m.message_count for m in self._connection_metrics.values()),
        average_latency=self._calculate_average_latency(),
        error_rate=self._calculate_error_rate(),
        memory_usage=self._get_memory_usage(),
        uptime_seconds=time.time() - self._start_time
    )
```

#### **3.3 연결 독립성 모니터링**
```python
class ConnectionIndependenceMonitor:
    """연결 간 독립성 모니터링"""

    def monitor_cross_connection_impact(self) -> Dict[str, Any]: ...
    def detect_connection_interference(self) -> List[str]: ...
    def ensure_connection_isolation(self) -> None: ...
```

### 🧪 테스트 계획
- [ ] 데이터 라우팅 정확성 검증
- [ ] 성능 지표 측정 정확도 확인
- [ ] 다중 구독 시나리오 테스트
- [ ] 부하 테스트 (1000+ 구독)

### 📈 예상 효과
- **데이터 라우팅**: 20% → 80%
- **모니터링**: 60% → 85%
- **성능 최적화**: 크게 개선

---

## 🔮 Phase 4: DataPoolManager 및 v6.1 고급 기능 (선택적, 2-3주)

### 🎯 목표
Pull 모델 기반 데이터 관리 시스템 구축 (차세대 아키텍처)

### 📋 작업 목록

#### **4.1 DataPoolManager 핵심 구조**
```python
class DataPoolManager:
    """중앙집중식 데이터 풀 관리"""

    def __init__(self):
        self._data_pools: Dict[str, Dict[DataType, Any]] = {}  # symbol -> data_type -> latest_data
        self._client_interests: Dict[str, Set[Tuple[str, DataType]]] = {}
        self._data_history: Dict[str, deque] = {}  # 선택적 히스토리

    async def register_client_interest(
        self,
        client_id: str,
        symbols: List[str],
        data_types: List[DataType]
    ) -> bool: ...

    def get_latest_data(
        self,
        symbol: str,
        data_type: DataType
    ) -> Optional[BaseWebSocketEvent]: ...

    def get_multiple_data(
        self,
        requests: List[Tuple[str, DataType]]
    ) -> Dict[Tuple[str, DataType], BaseWebSocketEvent]: ...
```

#### **4.2 SimpleWebSocketClient v6.1**
```python
class SimpleWebSocketClient:
    """Pull 모델 기반 간소화된 클라이언트"""

    def __init__(self, client_id: str):
        self.client_id = client_id
        self._data_pool_manager = None

    async def register_interests(
        self,
        symbols: List[str],
        data_types: List[DataType]
    ) -> bool:
        """관심사 등록 (구독 대신)"""

    def get_ticker(self, symbol: str) -> Optional[TickerEvent]:
        """최신 현재가 데이터 조회"""

    def get_orderbook(self, symbol: str) -> Optional[OrderbookEvent]:
        """최신 호가창 데이터 조회"""

    def get_multiple_tickers(self, symbols: List[str]) -> Dict[str, TickerEvent]:
        """다중 현재가 데이터 조회"""
```

#### **4.3 SIMPLE 포맷 지원**
```python
class SimpleFormatConverter:
    """SIMPLE 포맷 변환 (대역폭 최적화)"""

    @staticmethod
    def convert_to_simple_format(data: Dict[str, Any]) -> Dict[str, Any]: ...

    @staticmethod
    def convert_from_simple_format(simple_data: Dict[str, Any]) -> Dict[str, Any]: ...

    @staticmethod
    def is_simple_format_beneficial(data_size: int) -> bool: ...
```

### 🧪 테스트 계획
- [ ] Pull 모델 성능 비교 (vs 콜백 모델)
- [ ] 메모리 사용량 최적화 확인
- [ ] 대역폭 절약 효과 측정
- [ ] 동시성 테스트 (다중 클라이언트)

### 📈 예상 효과
- **개발자 경험**: 크게 향상 (콜백 지옥 제거)
- **메모리 효율성**: 추가 최적화
- **코드 복잡도**: 크게 감소

---

## 📅 구현 일정

### **Week 1-2: Phase 1 - 핵심 구조**
- [ ] 월: 타입 시스템 이식
- [ ] 화: ConnectionMetrics 구현
- [ ] 수: EpochManager 구현
- [ ] 목: GlobalWebSocketManager 기본 구조
- [ ] 금: 통합 테스트 및 버그 수정

### **Week 3-4: Phase 2 - 구독 관리**
- [ ] 월: SubscriptionStateManager 이식
- [ ] 화: WeakRef 자동 정리 시스템
- [ ] 수: 백그라운드 모니터링 구현
- [ ] 목: Application Service 통합
- [ ] 금: 메모리 누수 테스트

### **Week 5-6: Phase 3 - 데이터 라우팅**
- [ ] 월: DataRoutingEngine 구현
- [ ] 화: 고급 성능 모니터링
- [ ] 수: 연결 독립성 모니터링
- [ ] 목: 부하 테스트 및 최적화
- [ ] 금: 프로덕션 준비

### **Week 7-9: Phase 4 - 고급 기능 (선택적)**
- [ ] Week 7: DataPoolManager 구현
- [ ] Week 8: SimpleWebSocketClient v6.1
- [ ] Week 9: SIMPLE 포맷 지원 및 최종 최적화

---

## ⚠️ 위험 요소 및 대응 방안

### **위험 요소**
1. **기존 코드 호환성 파괴**
   - 대응: 점진적 마이그레이션 및 하위 호환성 유지

2. **메모리 사용량 증가**
   - 대응: 성능 모니터링 및 최적화

3. **복잡도 증가**
   - 대응: 상세한 문서화 및 테스트 커버리지 확보

4. **개발 일정 지연**
   - 대응: Phase별 독립적 구현 및 우선순위 조정

### **품질 보증**
- [ ] 각 Phase별 독립적 테스트
- [ ] 기존 기능 회귀 테스트
- [ ] 성능 벤치마크 비교
- [ ] 메모리 프로파일링
- [ ] 코드 리뷰 및 문서화

---

## 🎯 성공 지표

### **정량적 지표**
- **연결 안정성**: 99.9% 이상 유지
- **메모리 누수**: 0건
- **응답 지연시간**: 10ms 이하
- **동시 구독 처리**: 1000+ 개

### **정성적 지표**
- **개발자 경험**: 콜백 복잡도 50% 감소
- **유지보수성**: 코드 모듈화 및 테스트 가능성 향상
- **확장성**: 새로운 데이터 타입 추가 용이성

---

## 📚 참고 자료

- **백업 시스템**: `upbit_auto_trading/infrastructure/external_apis/upbit/websocket_v6_backup20250902_150200/`
- **아키텍처 가이드**: `websocket_v6_backup20250902_150200/ARCHITECTURE_GUIDE.md`
- **현재 시스템**: `upbit_auto_trading/infrastructure/external_apis/upbit/websocket_v6/`
- **Application Service**: `upbit_auto_trading/application/services/websocket_application_service.py`

---

## 📝 추가 고려사항

### **프로덕션 배포 전략**
1. **Blue-Green 배포**: 기존 시스템과 새 시스템 병렬 운영
2. **단계적 트래픽 전환**: 10% → 50% → 100%
3. **롤백 계획**: 문제 발생 시 즉시 이전 버전 복구

### **모니터링 및 알림**
1. **실시간 대시보드**: WebSocket 연결 상태 및 성능 지표
2. **알림 시스템**: 연결 끊김, 에러율 증가 시 자동 알림
3. **로그 분석**: 구조화된 로그를 통한 문제 분석

### **문서화 계획**
1. **API 문서**: 새로운 인터페이스 상세 설명
2. **마이그레이션 가이드**: 기존 코드 업그레이드 방법
3. **트러블슈팅 가이드**: 일반적인 문제 및 해결 방법

이 계획을 통해 현재의 기본적인 WebSocket 시스템을 **안정적이고 확장 가능한 엔터프라이즈급 시스템**으로 발전시킬 수 있습니다.
