# 🎯 WebSocket v6.0 설계 원칙 및 아키텍처

## 🏗️ **핵심 설계 원칙**

### 1. **Single Source of Truth (단일 진실 공급원)**
- 전체 애플리케이션에서 **하나의 WebSocket 연결**만 업비트 서버와 통신
- 모든 구독 상태는 **GlobalWebSocketManager**에서 중앙 관리
- 데이터 중복 요청 방지 및 업비트 API 효율성 극대화

### 2. **Graceful Degradation (우아한 성능 저하)**
- API 키 없어도 **Public 기능 완전 동작**
- Private 기능 불가 시 **REST API 폴링으로 자동 대체**
- 연결 끊김 시에도 **사용자 경험 중단 없음**

### 3. **Zero Configuration (제로 설정)**
- 기본 설정만으로 **즉시 사용 가능**
- 복잡한 WebSocket 설정을 **내부적으로 자동 최적화**
- 개발자는 비즈니스 로직에만 집중

### 4. **Fail-Safe Design (안전 장치 설계)**
- 컴포넌트 비정상 종료 시 **자동 구독 정리**
- Rate Limit 초과 시 **지수 백오프 자동 적용**
- 메모리 누수 방지를 위한 **WeakRef 기반 자동 관리**

## 🏛️ **아키텍처 설계**

### **계층별 책임 분리**

```
┌─────────────────────────────────────────────────────────────┐
│                  Subsystem Layer                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Chart       │ │ OrderMonitor│ │ MarketDataAnalyzer     │ │
│  │ Component   │ │ Component   │ │ Component              │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Proxy Layer                                │
│           WebSocketClientProxy                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ • subscribe_ticker()     • is_public_available()       │ │
│  │ • subscribe_orderbook()  • is_private_available()      │ │
│  │ • get_snapshot()         • automatic_cleanup()         │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Global Management Layer                      │
│              GlobalWebSocketManager                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ • Subscription State Manager                           │ │
│  │ • Data Routing Engine                                  │ │
│  │ • Connection Manager                                   │ │
│  │ • Automatic Recovery System                            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                WebSocket Client Layer                       │
│  ┌─────────────────────┐       ┌─────────────────────────┐  │
│  │ UpbitWebSocketPublic│       │ UpbitWebSocketPrivate   │  │
│  │ Client              │       │ Client                  │  │
│  │ • No API Key Needed │       │ • JWT Authentication   │  │
│  │ • Market Data       │       │ • Order/Asset Data     │  │
│  │ • Always Available  │       │ • Conditional Available│  │
│  └─────────────────────┘       └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Upbit WebSocket API                       │
│                    wss://api.upbit.com                      │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 **데이터 흐름 아키텍처**

### **구독 요청 흐름**
```
[Subsystem]
    → [WebSocketClientProxy]
    → [GlobalWebSocketManager]
    → [SubscriptionStateManager]
    → [실제 WebSocket Client]
    → [Upbit API]
```

### **데이터 수신 흐름**
```
[Upbit API]
    → [실제 WebSocket Client]
    → [DataRoutingEngine]
    → [콜백 라우터]
    → [각 Subsystem 콜백]
```

## 🧩 **핵심 컴포넌트 설계**

### **1. GlobalWebSocketManager**
```python
class GlobalWebSocketManager:
    """전역 WebSocket 관리자 - Singleton 패턴"""

    # 핵심 설계 결정:
    # - 애플리케이션당 단 1개 인스턴스
    # - Public/Private 클라이언트 통합 관리
    # - 베이스 연결 상시 유지 (24/7)
    # - 자동 장애 복구 및 상태 복원
    # - upbit_auth.py와 rate_limiter.py 중앙 집중 사용
```### **2. WebSocketClientProxy**
```python
class WebSocketClientProxy:
    """서브시스템용 WebSocket 프록시"""

    # 핵심 설계 결정:
    # - 서브시스템별 독립적인 인터페이스 제공
    # - GlobalWebSocketManager로 모든 요청 위임
    # - WeakRef 기반 자동 생명주기 관리
    # - 오류 격리 및 복구
    # - upbit_auth.py 임포트 불필요 (전역 관리자가 JWT 제공)
```### **3. SubscriptionStateManager**
```python
class SubscriptionStateManager:
    """전역 구독 상태 관리자"""

    # 핵심 설계 결정:
    # - 모든 클라이언트의 구독 요구사항 통합
    # - 업비트 덮어쓰기 방식에 최적화
    # - 스냅샷 요청 시 기존 실시간 포함
    # - 중복 구독 자동 최적화
```

### **4. DataRoutingEngine**
```python
class DataRoutingEngine:
    """데이터 라우팅 및 분배 엔진"""

    # 핵심 설계 결정:
    # - 수신 데이터를 관련 모든 콜백에 멀티캐스트
    # - 콜백 실행 오류 격리
    # - 성능 최적화를 위한 비동기 분배
    # - 메모리 효율적인 데이터 복사
```

## 🔒 **보안 설계**

### **API 키 관리**
- **전역 인증**: `upbit_auth.py`의 UpbitAuthenticator를 전역 관리자에서만 사용
- **클라이언트 분리**: 개별 클라이언트는 JWT 토큰만 받아서 사용 (upbit_auth 임포트 불필요)
- **자동 만료**: JWT 토큰 자동 갱신 (Private 클라이언트)
- **권한 최소화**: 필요한 권한만 요청

### **에러 정보 보호**
- API 키가 로그에 노출되지 않도록 마스킹 처리
- 민감한 정보는 디버그 로그에서도 제외
- 에러 메시지에서 시스템 내부 정보 숨김

## ⚡ **성능 설계**

### **메모리 최적화**
```python
# WeakRef 기반 자동 정리
import weakref

class WebSocketClientProxy:
    def __init__(self, client_id: str):
        # 객체 소멸 시 자동 정리 콜백 등록
        weakref.finalize(self, self._cleanup_subscriptions)
```

### **네트워크 최적화**
```python
# 구독 요청 통합 최적화
def optimize_subscription_request(self, new_symbols: Set[str],
                                current_symbols: Set[str]) -> List[str]:
    """기존 실시간 + 새 요청을 통합하여 최적화된 구독 생성"""
    return list(current_symbols | new_symbols)
```

### **CPU 최적화**
```python
# 비동기 데이터 분배로 블로킹 방지
async def distribute_data(self, data: dict):
    """모든 콜백을 병렬 실행하여 성능 최적화"""
    tasks = [callback(data) for callback in self.callbacks]
    await asyncio.gather(*tasks, return_exceptions=True)
```

## 🛡️ **장애 복구 설계**

### **연결 장애 대응**
1. **자동 감지**: 5초마다 연결 상태 체크
2. **즉시 복구**: 연결 끊김 감지 시 1초 내 재연결 시도
3. **상태 복원**: 재연결 후 모든 구독 상태 자동 복원
4. **알림 시스템**: 장애 발생/복구 시 관련 컴포넌트에 알림

### **Rate Limit 대응**
1. **지수 백오프**: 429 오류 시 대기 시간 점진적 증가
2. **동적 조절**: Rate Limit 패턴 학습하여 요청 간격 자동 조절
3. **우선순위 큐**: 중요한 요청부터 우선 처리
4. **폴백 전략**: WebSocket 불가 시 REST API로 자동 대체

### **메모리 누수 방지**
1. **WeakRef 활용**: 참조 순환 방지
2. **주기적 정리**: 사용하지 않는 구독 자동 해제
3. **메모리 모니터링**: 임계값 초과 시 자동 최적화
4. **강제 GC**: 필요 시 가비지 컬렉션 수동 트리거

## 📊 **모니터링 및 관찰 가능성**

### **메트릭 수집**
```python
# 실시간 성능 지표
metrics = {
    'active_connections': int,
    'total_subscriptions': int,
    'messages_per_second': float,
    'average_latency_ms': float,
    'error_rate_percent': float,
    'memory_usage_mb': float
}
```

### **헬스체크 엔드포인트**
```python
async def health_check() -> dict:
    """시스템 건강성 종합 검사"""
    return {
        'status': 'healthy|degraded|critical',
        'uptime_seconds': float,
        'last_message_timestamp': datetime,
        'connection_quality': 'excellent|good|poor',
        'active_subscriptions': int
    }
```

## 🔧 **확장성 설계**

### **새로운 데이터 타입 추가**
```python
# 플러그인 방식으로 새 데이터 타입 지원
class CustomDataTypeHandler:
    def can_handle(self, data_type: str) -> bool:
        return data_type.startswith('custom_')

    async def process_data(self, data: dict) -> dict:
        # 커스텀 데이터 처리 로직
        return processed_data

# 핸들러 등록
global_manager.register_data_handler(CustomDataTypeHandler())
```

### **다중 거래소 지원 준비**
```python
# 추상 인터페이스로 다른 거래소 확장 가능
class AbstractWebSocketManager(ABC):
    @abstractmethod
    async def subscribe_ticker(self, symbols: List[str]) -> str:
        pass

    @abstractmethod
    async def subscribe_orderbook(self, symbols: List[str]) -> str:
        pass

# 업비트 구현체
class UpbitWebSocketManager(AbstractWebSocketManager):
    # 업비트 전용 구현
    pass

# 향후 바이낸스 등 추가 가능
class BinanceWebSocketManager(AbstractWebSocketManager):
    # 바이낸스 전용 구현
    pass
```

## 🎯 **품질 보증**

### **테스트 전략**
1. **단위 테스트**: 각 컴포넌트별 독립 테스트 (90% 커버리지)
2. **통합 테스트**: 실제 업비트 API와 연동 테스트
3. **부하 테스트**: 100개 심볼 동시 구독 안정성 검증
4. **장애 테스트**: 네트워크 단절, Rate Limit 등 시나리오 테스트

### **코드 품질**
1. **타입 힌트**: 모든 public 메서드에 완전한 타입 어노테이션
2. **문서화**: Docstring 100% 작성
3. **린팅**: mypy, flake8 검사 통과
4. **포맷팅**: black 자동 포맷팅 적용

---

**"Simple is better than complex. Complex is better than complicated."** - The Zen of Python
