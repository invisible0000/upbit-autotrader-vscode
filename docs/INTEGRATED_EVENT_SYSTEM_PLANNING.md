# 🎭 통합 이벤트 시스템 기획서: 실시간 금전거래 안정성을 위한 백그라운드 아키텍처

> **"금전거래 시스템에서 모든 동작은 예측 가능하고 추적 가능해야 한다"**

## 📋 문서 정보

- **문서 유형**: 백그라운드 시스템 초기 기획
- **작성일**: 2025년 8월 10일
- **목적**: Event-Driven + Queue 기반 안정성 확보
- **범위**: 실시간 거래 중단 없는 시스템 운영

---

## 🎯 핵심 문제 정의

### 현재 상황
```
❌ PyQt6 Thread-Safe 패턴 → 임시방편적 해결
❌ 직접적인 UI ↔ Infrastructure 연결 → 결합도 높음
❌ 로그 출력만 이벤트 기반 → 시스템 전체가 아님
```

### 목표 상황
```
✅ 모든 시스템 동작이 Event Queue로 관리
✅ 금전거래 중 안전한 설정 변경/로그 관리
✅ 예측 가능한 이벤트 순서와 실패 처리
```

---

## 🏗️ 통합 이벤트 시스템 아키텍처

### 1. **핵심 컴포넌트 구조**
```
┌─────────────────────────────────────────────────────┐
│                  Event Bus Manager                  │ ← 중앙 통제탑
│                 (Single Thread)                     │
└─────────────────────┬───────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Trading     │ │ Logging     │ │ Config      │
│ Event Queue │ │ Event Queue │ │ Event Queue │
│(High Prior.)│ │(Low Prior.) │ │(Medium Pri.)│
└─────────────┘ └─────────────┘ └─────────────┘
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Trading     │ │ Logging     │ │ Config      │
│ Worker      │ │ Worker      │ │ Worker      │
│ Thread      │ │ Thread      │ │ Thread      │
└─────────────┘ └─────────────┘ └─────────────┘
```

### 2. **우선순위 기반 이벤트 처리**
```python
class EventPriority(Enum):
    CRITICAL_TRADING = 1      # 거래 실행, 손절/익절
    HIGH_SAFETY = 2           # 거래 안전성 검증
    MEDIUM_CONFIG = 3         # 설정 변경, DB 업데이트
    LOW_LOGGING = 4           # 로그 출력, UI 업데이트
    LOWEST_CLEANUP = 5        # 리소스 정리, 백업
```

---

## 🎪 Event-Driven 실무 적용 계획

### 1. **거래 안전성 보장 이벤트**
```python
@dataclass
class TradingStateChangeEvent:
    event_type: str = "trading_state_change"
    old_state: TradingState
    new_state: TradingState
    timestamp: datetime
    can_interrupt: bool = False  # 거래 중단 가능 여부

# 거래 중일 때 설정 변경 요청 → 안전하게 대기/거부
@dataclass
class ConfigChangeRequestEvent:
    event_type: str = "config_change_request"
    config_type: str  # "database", "logging", "api"
    change_data: dict
    requester: str
    can_wait: bool = True  # 거래 완료까지 대기 가능 여부
```

### 2. **로그 시스템 이벤트 통합**
```python
@dataclass
class LogEntryEvent:
    event_type: str = "log_entry"
    level: str
    component: str
    message: str
    timestamp: datetime
    metadata: dict = field(default_factory=dict)

# 기존 PyQt6 Thread-Safe → Event Queue 방식으로 변경
class LogViewerEventHandler:
    async def handle_log_entry(self, event: LogEntryEvent):
        # UI 업데이트도 이벤트 큐를 통해 안전하게 처리
        ui_update_event = UIUpdateEvent(
            widget_id="log_viewer",
            action="add_log_entry",
            data=event
        )
        await EventBus.publish(ui_update_event)
```

### 3. **Database 프로필 전환 이벤트**
```python
@dataclass
class DatabaseProfileSwitchEvent:
    event_type: str = "database_profile_switch"
    old_profile_id: str
    new_profile_id: str
    requester: str
    force_switch: bool = False
    backup_before_switch: bool = True
```

---

## ⚡ 실시간 안정성 보장 메커니즘

### 1. **거래 상태 인식 이벤트 체인**
```
거래 시작 → TradingStartEvent
          ↓
       모든 설정 변경 요청 HOLD
          ↓
거래 완료 → TradingCompleteEvent
          ↓
       대기 중인 설정 변경 실행
```

### 2. **실패 안전 처리 (Fail-Safe)**
```python
class EventExecutionResult:
    success: bool
    error_message: Optional[str] = None
    rollback_required: bool = False
    retry_count: int = 0
    max_retries: int = 3

# 실패 시 자동 복구
async def handle_failed_event(event: BaseEvent, error: Exception):
    if event.retry_count < event.max_retries:
        # 재시도 큐에 추가
        await EventBus.schedule_retry(event, delay=event.retry_count * 2)
    else:
        # 수동 개입 필요 - 관리자 알림
        await EventBus.publish(CriticalFailureEvent(
            failed_event=event,
            error=str(error)
        ))
```

---

## 🔧 구현 로드맵 (현실적 접근)

### **Phase 1: Event Bus 핵심 (2주)**
- [ ] EventBus Manager 기본 구현
- [ ] Priority Queue 시스템
- [ ] Trading State 감지 시스템
- [ ] 기본 이벤트 타입 정의

### **Phase 2: 로깅 시스템 통합 (1주)**
- [ ] 기존 PyQt6 Thread-Safe → Event 방식 변경
- [ ] LogEntryEvent 처리 Worker
- [ ] UI 업데이트 이벤트 통합

### **Phase 3: Config 관리 통합 (1주)**
- [ ] Database 프로필 전환 이벤트
- [ ] 거래 중 안전성 검증
- [ ] 설정 변경 대기/실행 시스템

### **Phase 4: 확장 및 최적화 (1주)**
- [ ] 이벤트 모니터링 UI
- [ ] 성능 최적화
- [ ] 에러 복구 자동화

---

## 💡 DDD 방법론과의 연계

### **Domain Events 활용**
- 거래 도메인 이벤트 → Event Bus로 전파
- Cross-Boundary 통신을 이벤트로 통일
- Aggregate 간 느슨한 결합 유지

### **Infrastructure Layer 통합**
- Event Bus도 Infrastructure Layer의 핵심 서비스
- Repository, Logging, Config 모두 이벤트 기반 통합
- DI Container에서 Event Bus 주입 관리

---

## ⚠️ 주의사항 및 리스크

### **성능 고려사항**
- Event Queue 크기 제한 및 모니터링 필요
- 높은 빈도 이벤트 (가격 업데이트) 별도 최적화
- Memory Leak 방지위한 이벤트 라이프사이클 관리

### **디버깅 복잡성**
- 이벤트 체인 추적 시스템 필요
- 개발 모드에서 이벤트 플로우 시각화
- 프로덕션에서 이벤트 로그 별도 관리

---

## 🎯 결론

Event-Driven Architecture는 **복잡성을 추가하지만 안정성을 크게 향상**시킵니다.

특히 **실시간 금전거래 시스템**에서는 이 복잡성이 충분히 가치가 있습니다:
- 거래 중 안전한 설정 변경
- 예측 가능한 시스템 동작
- 실패 상황에서의 자동 복구

**현실적 접근**: Phase 1부터 단계적으로 구현하여 기존 시스템에 점진적 통합

---

**문서 작성자**: GitHub Copilot
**프로젝트**: 업비트 자동매매 Event-Driven Architecture
**작성일**: 2025년 8월 10일
**예상 구현 기간**: 4-5주
