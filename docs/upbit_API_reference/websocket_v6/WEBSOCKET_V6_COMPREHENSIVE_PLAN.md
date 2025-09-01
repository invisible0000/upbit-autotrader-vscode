# 🚀 WebSocket v6.0 종합 기획 문서

## 1. 개요 (Overview)

### 1.1. 목표
- **안정성, 확장성, 사용성**을 모두 갖춘 업비트 WebSocket v6 시스템 구축.
- 복잡한 비동기 데이터 스트림을 개발자가 쉽고 안전하게 사용할 수 있는 최상위 수준의 API 제공.

### 1.2. 핵심 문제 정의
- **업비트 WebSocket의 구독 덮어쓰기(Overwrite) 정책**: 새로운 구독 요청 시 기존 구독이 예고 없이 중단되는 문제.
- **복잡한 GUI 환경에서의 구독 충돌**: 다수의 독립적인 UI 컴포넌트(차트, 호가창, 실시간 잔고 등)가 동시에 WebSocket 구독을 시도하며 발생하는 데이터 스트림 충돌 및 유실.

### 1.3. 해결 전략
- **중앙 집중식 전역 관리 아키텍처 도입**:
  - **`GlobalWebSocketManager`**: 애플리케이션 전체에서 단 하나의 인스턴스만 존재(싱글톤)하며, 업비트와의 모든 WebSocket 연결(Public/Private)과 구독 상태를 중앙에서 관리.
  - **`WebSocketClientProxy`**: 각 컴포넌트에 제공되는 경량 프록시 객체. 컴포넌트는 이 프록시를 통해 전역 관리자에게 구독을 요청하며, 복잡한 내부 동작으로부터 완벽히 격리됨.
- **단일 진실 공급원 (Single Source of Truth)**: 모든 구독 정보는 `GlobalWebSocketManager`에만 존재하며, 이를 통해 구독 상태의 불일치를 원천적으로 차단.

---

## 2. 주요 설계 원칙 (Core Design Principles)

1.  **Single Source of Truth (단일 진실 공급원)**
    - 전체 애플리케이션에서 단 하나의 Public 연결과 단 하나의 Private 연결만 유지.
    - 모든 구독 상태는 `GlobalWebSocketManager`에서 중앙 관리하여 중복과 충돌을 방지.

2.  **Graceful Degradation (우아한 성능 저하)**
    - API 키가 없거나 Private 연결에 실패해도, Public 기능은 완벽하게 동작.
    - Private 기능 사용 불가 시, 관련 기능은 자동으로 REST API 폴링으로 전환되거나 비활성화.

3.  **Zero Configuration (제로 설정)**
    - 개발자는 `WebSocketClientProxy("my_component")`와 같이 간단한 선언만으로 즉시 WebSocket 사용 가능.
    - 연결, 재연결, 구독 최적화 등 복잡한 설정은 시스템이 자동으로 처리.

4.  **Fail-Safe Design (안전 장치 설계)**
    - 컴포넌트 비정상 종료 또는 가비지 컬렉션 시, 관련 구독은 자동으로 정리되어 메모리 누수 방지.
    - Rate Limit 초과, 네트워크 단절 등 예외 상황 발생 시 지수 백오프(Exponential Backoff)를 적용한 자동 복구 메커니즘 동작.

5.  **Developer Experience (개발자 경험 최우선)**
    - 직관적인 API, 상세한 문서, 풍부한 예제 코드를 제공하여 학습 곡선을 최소화.
    - 콜백에서의 실수를 방지하기 위한 타입 안정성(Type Safety) 강화.

---

## 3. 아키텍처 (Architecture)

### 3.1. 계층형 아키텍처
```
┌─────────────────────────────────────────────────────────────┐
│                  Subsystem Layer (Application Components)   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ ChartWidget │ │ OrderMonitor│ │ BalanceViewer          │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │ (Requests via Proxy)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Proxy Layer                                │
│           WebSocketClientProxy                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ • subscribe_ticker()     • is_private_available()      │ │
│  │ • get_snapshot()         • Automatic Resource Cleanup  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │ (Delegates to Global Manager)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Global Management Layer                      │
│              GlobalWebSocketManager (Singleton)             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ • Subscription State Manager   • Data Routing Engine    │ │
│  │ • Connection & Recovery        • FanoutHub (Back-pressure)│
│  │ • Global Rate Limiter          • Idempotency Guard      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │ (Manages physical connections)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                WebSocket Client Layer                       │
│  ┌─────────────────────┐       ┌─────────────────────────┐  │
│  │ UpbitWebSocketPublic│       │ UpbitWebSocketPrivate   │  │
│  └─────────────────────┘       └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Upbit WebSocket API                       │
└─────────────────────────────────────────────────────────────┘
```

### 3.2. 핵심 컴포넌트 (Core Components)

- **`GlobalWebSocketManager`**: 아키텍처의 심장. 싱글톤으로 존재하며 다음을 책임진다.
  - **연결 관리**: Public/Private WebSocket 연결의 생명주기(연결, 유지, 종료) 관리.
  - **상태 관리**: 모든 컴포넌트의 구독 요구사항을 통합하여 최적화된 단일 구독 상태 유지.
  - **데이터 라우팅**: 수신된 데이터를 구독을 요청한 모든 `Proxy`의 콜백으로 분배.
  - **장애 복구**: 연결 단절 시 자동 재연결 및 구독 상태 복원.

- **`WebSocketClientProxy`**: 각 서브시스템(컴포넌트)에 제공되는 인터페이스.
  - 모든 요청을 `GlobalWebSocketManager`에 위임.
  - `WeakRef`와 명시적 `cleanup()` 메서드를 통해 객체 소멸 시 관련 구독을 자동으로 정리하여 리소스 누수 방지.

- **`SubscriptionStateManager`**: `GlobalWebSocketManager` 내부에 존재.
  - 여러 컴포넌트의 구독 요청(e.g., A는 BTC, B는 ETH)을 취합하여 최종 구독 목록(BTC, ETH)을 원자적으로(atomically) 계산.

- **`DataRoutingEngine` & `FanoutHub`**: 데이터 분배 및 백프레셔 관리.
  - 수신된 데이터를 모든 구독자에게 비동기적으로 멀티캐스팅.
  - **(제안 수용)** `FanoutHub`를 통해 구독자별 `asyncio.Queue` (Bounded Queue)를 두어 백프레셔(Back-pressure) 관리. 특정 콜백이 느려도 전체 시스템에 영향을 주지 않음.
  - 큐가 가득 찰 경우, 오래된 데이터를 버리거나(`drop_oldest`) 최신 데이터로 덮어쓰는(`coalesce-by-symbol`) 정책 적용.

- **`GlobalRateLimiter`**: (제안 수용) REST, WebSocket을 아우르는 전역 레이트 리밋 관리.
  - 공유된 토큰 버킷(Token Bucket) 알고리즘을 사용하여 모든 종류의 API 요청 속도를 중앙에서 조절.

---

## 4. 주요 기능 및 정책 (Key Features & Policies)

### 4.1. 구독 관리 (Subscription Management)
- **통합 구독**: 여러 컴포넌트의 요청을 실시간으로 병합하여 업비트에는 단일 구독 요청만 전송.
- **자동 정리**: `WebSocketClientProxy` 객체 소멸 시, `WeakRef`와 명시적 `cleanup()`을 통해 해당 컴포넌트가 요청한 구독을 전역 상태에서 자동으로 제거하고, 필요시 전체 구독 목록을 갱신.
- **원자적 업데이트**: 구독 추가/제거 시, `SubscriptionStateManager`는 내부 잠금(lock) 또는 직렬화된 태스크 큐를 통해 구독 상태를 원자적으로 변경하여 경쟁 조건(Race Condition) 방지.

### 4.2. 데이터 처리 및 분배 (Data Handling & Distribution)
- **타입 안정성 (Type Safety)**: (제안 수용) 콜백으로 전달되는 `data`는 단순 `dict`가 아닌, `dataclasses`로 정의된 `Typed Event` (e.g., `TickerEvent`, `OrderbookEvent`) 객체를 사용하여 개발자의 실수를 줄이고 코드 가독성 향상.
- **GUI 스레드 안정성**: (제안 수용) `asyncio` 이벤트 루프에서 실행되는 콜백이 PyQt 등 GUI의 메인 스레드에 안전하게 접근할 수 있도록 `qasync` 라이브러리 또는 `PyQt Signal/Slot`을 이용한 브릿지(Bridge) 패턴을 공식적으로 가이드하고 예제 제공.

### 4.3. 안정성 및 장애 복구 (Stability & Fault Tolerance)
- **자동 재연결 및 상태 복원**: 연결 끊김 감지 시, 지수 백오프(1s, 2s, 4s...) 전략에 따라 자동으로 재연결 시도. 성공 시, 이전에 유지하던 모든 구독 상태를 즉시 복원.
- **멱등성(Idempotency) 보장**: (제안 수용) 재연결 과정에서 발생할 수 있는 데이터 중복 및 순서 꼬임 문제를 방지하기 위해 `epoch`(세대) 개념 도입. 재연결 시마다 `epoch`을 증가시키고, 콜백에서는 현재 `epoch`과 다른 과거의 데이터는 무시.
- **Private 채널 JWT 관리**: (제안 수용) Private 채널의 JWT(JSON Web Token)는 만료 시간(e.g., 10분)의 80%가 경과하기 전에 비동기적으로 선제 갱신. 갱신 실패 시, 해당 기능을 REST API 폴링으로 우아하게 전환.

### 4.4. API 및 사용성 (API & Usability)
- `WebSocketClientProxy`를 통해 `subscribe_ticker`, `get_orderbook_snapshot`, `unsubscribe_all` 등 직관적인 비동기 메서드 제공.
- `async with WebSocketClientProxy(...) as ws:` 구문을 지원하여, `with` 블록을 벗어날 때 모든 구독이 자동으로 정리되도록 보장.
- `client_id`의 충돌을 방지하기 위한 네이밍 컨벤션(`"<모듈명>_<인스턴스ID>"`)을 문서에 명시.

### 4.5. 관찰 가능성 (Observability)
- `get_performance_metrics()`: 초당 메시지 수, 평균 지연 시간, 메모리 사용량 등 핵심 성능 지표 제공.
- `health_check()`: 시스템의 전반적인 건강 상태(healthy, degraded, critical)와 업타임(uptime) 제공.
- **(제안 수용)** `lag_ms`(데이터 발생-수신 지연), `queue_depth`(백프레셔 큐 깊이), `drop_rate`(데이터 폐기율) 등 더 상세한 디버깅용 지표 추가.

---

## 5. 구현 계획 (Implementation Plan)

- **Phase 1: 코어 아키텍처 구축 (1주)**
  - `GlobalWebSocketManager` 및 `WebSocketClientProxy`의 기본 구조와 싱글톤/프록시 패턴 구현.
  - Public/Private 연결 관리 및 자동 재연결/상태 복원 로직 구현.

- **Phase 2: 구독 및 데이터 라우팅 엔진 고도화 (1.5주)**
  - `SubscriptionStateManager`의 원자적 구독 병합/관리 로직 구현.
  - `DataRoutingEngine` 및 백프레셔 관리를 위한 `FanoutHub` 구현.
  - `Typed Event` 데이터클래스 정의 및 콜백에 적용.

- **Phase 3: 안정성 강화 (1주)**
  - 재연결 시 `epoch` 기반 멱등성 처리 로직 추가.
  - Private 채널 JWT 자동 갱신 및 폴백 로직 구현.
  - `GlobalRateLimiter` 구현 및 REST/WebSocket 클라이언트에 통합.

- **Phase 4: 통합 및 테스트 (1.5주)**
  - GUI 스레드 브릿지(e.g., `qasync`) 구현 및 테스트.
  - Mock WebSocket 서버 구축 및 이를 활용한 통합/장애 시나리오 테스트 자동화.
  - 기존 UI 컴포넌트들을 `WebSocketClientProxy`를 사용하도록 점진적으로 리팩터링.

---

## 6. 테스트 전략 (Testing Strategy)

- **단위 테스트**: 각 컴포넌트(`GlobalWebSocketManager`, `FanoutHub` 등)의 핵심 로직을 격리하여 90% 이상의 커버리지 목표로 테스트.
- **통합 테스트 (Mock 서버 활용)**: (제안 수용) 실제 업비트 API 대신, 자체 제작한 Mock WebSocket 서버를 사용하여 다음과 같은 시나리오를 안정적이고 반복적으로 테스트.
  - **정상 시나리오**: 연결, 구독, 데이터 수신, 구독 해제, 정상 종료.
  - **장애 시나리오**: 의도적인 연결 끊김 후 자동 재연결 및 구독 복원 검증.
  - **에러 시나리오**: 업비트의 429(Rate Limit) 에러 응답 시 지수 백오프 동작 검증.
  - **데이터 이상 시나리오**: 비정상 포맷 데이터 수신 시 해당 콜백의 오류가 다른 콜백에 영향을 주지 않는지 격리 테스트.
- **부하 테스트**: 100개 이상의 심볼 동시 구독 및 초당 수백 건의 메시지 수신 상황에서 CPU/메모리 사용량, 데이터 처리 지연 시간(latency) 측정.
- **카오스 테스트**: (제안 수용) 네트워크 지연, 패킷 손실, 메시지 순서 뒤바뀜 등을 의도적으로 발생시켜 극한 상황에서의 시스템 안정성 검증.

---

## 7. 부록: 고려된 설계 결정 (Appendix: Design Decisions)

- **`WeakRef` 자동 정리 vs 명시적 `cleanup`**: `WeakRef`는 개발자 편의성을 위한 보조 수단으로 활용하되, 안정적인 리소스 해제를 위해 `async with` 구문과 명시적인 `cleanup()`/`shutdown()` 호출을 기본으로 권장.
- **스냅샷과 실시간 데이터 동기화**: 스냅샷 요청 직후 들어오는 실시간 데이터와의 순서 보장을 위해, 스냅샷 데이터에 포함된 타임스탬프 또는 시퀀스 번호를 기준으로 이전 데이터를 무시하는 규칙을 `DataRoutingEngine`에 적용.
