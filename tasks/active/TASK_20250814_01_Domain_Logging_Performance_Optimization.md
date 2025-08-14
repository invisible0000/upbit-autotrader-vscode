# TASK_20250814_01_Domain_Logging_Performance_Optimization.md

## 🚨 **긴급 성능 문제 발견!**

Domain Events 기반 로깅이 **272배 성능 저하**를 일으키고 있습니다.

### 📊 **성능 테스트 결과**
```
🔍 로깅 성능 비교 테스트 (10,000회 로깅)
📊 Domain Events 방식: 39.73ms
📊 단순 함수 호출: 0.15ms
📊 성능 차이: 272.1배 느림
📊 오버헤드: 39.58ms
```

## 🎯 **태스크 목표**
DDD 순수성을 유지하면서도 성능 오버헤드가 없는 로깅 시스템 구현

## ❌ **현재 문제: 과도한 성능 오버헤드**

### **1. 매 로그마다 복잡한 객체 생성**
```python
# 현재: 로그 한 번에 이것들이 모두 생성됨
@dataclass(frozen=True)
class DomainLogRequested(DomainEvent):
    component_name: str       # ✅ 필요
    log_level: str           # ✅ 필요
    message: str             # ✅ 필요
    context_data: Dict       # ✅ 필요
    _event_id: str          # ❌ 불필요 (UUID 생성 비용)
    _occurred_at: datetime  # ❌ 불필요 (datetime.now() 비용)

def __post_init__(self):
    object.__setattr__(self, '_event_id', str(uuid.uuid4()))     # 🐌 UUID 생성
    object.__setattr__(self, '_occurred_at', datetime.now())     # 🐌 시간 생성
    super().__post_init__()  # 🐌 부모 클래스 체인
```

### **2. 불필요한 메타데이터 오버헤드**
- **event_id**: 로깅에 UUID가 필요한가?
- **occurred_at**: Infrastructure에서 timestamp 추가하면 됨
- **aggregate_id**: 로깅에 집합 루트 개념이 필요한가?

### **3. Domain Events 남용**
- **로깅은 비즈니스 이벤트가 아님**: Domain Events는 도메인 중요 사건용
- **관찰 vs 비즈니스**: 로깅은 관찰 도구, 비즈니스 핵심이 아님

## ✅ **해결 방안: 순수성 + 성능 모두 달성**

### **Option 1: 최소한의 Domain Interface (권장)**

```python
# domain/logging.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class DomainLogger(ABC):
    """순수 Domain 로깅 인터페이스 - 성능 최적화"""

    @abstractmethod
    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        pass

    @abstractmethod
    def error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        pass

class NoOpLogger(DomainLogger):
    """기본 구현 - 아무것도 하지 않음"""
    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        pass
    def error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        pass

# 전역 인스턴스 (Infrastructure에서 주입)
_logger: DomainLogger = NoOpLogger()

def set_domain_logger(logger: DomainLogger) -> None:
    global _logger
    _logger = logger

def create_domain_logger(component_name: str) -> DomainLogger:
    """기존 API 호환성 유지"""
    return _logger  # 실제로는 같은 인스턴스 반환
```

### **Option 2: 초경량 이벤트 (대안)**

```python
# domain/events/logging_events.py
@dataclass(frozen=True)
class LogEvent:
    """초경량 로그 이벤트 - 메타데이터 최소화"""
    level: str
    message: str
    context: Optional[Dict[str, Any]] = None
    # event_id, occurred_at, aggregate_id 제거 → 성능 향상
```

## 📋 **작업 계획**

### **Phase 1: 성능 문제 정확한 분석** (30분)
- [-] 현재 Domain Events 로깅 상세 성능 프로파일링
- [ ] 각 구성 요소별 오버헤드 측정 (UUID, datetime, dataclass 생성)
- [ ] 실제 업무 로드에서 성능 영향 측정
- [ ] 메모리 사용량 분석

### **Phase 2: 순수성 유지하면서 성능 최적화** (45분)
- [ ] Option 1: 의존성 주입 기반 단순 인터페이스 구현
- [ ] Infrastructure 구현체 연결
- [ ] 기존 API 호환성 확보 (`create_domain_logger` 유지)
- [ ] DDD 순수성 검증 (Infrastructure 의존성 여전히 0개)

### **Phase 3: 성능 검증 및 마이그레이션** (45분)
- [ ] 새로운 구현 성능 테스트
- [ ] 기존 Domain Services 마이그레이션
- [ ] 전체 시스템 로깅 동작 확인
- [ ] 성능 개선 효과 측정

### **Phase 4: 문서 업데이트** (30분)
- [ ] `docs/architecture_patterns/logging/` 문서 업데이트
- [ ] 성능 최적화 근거 설명
- [ ] 새로운 아키텍처 설명

## 🔍 **핵심 인사이트**

### **로깅의 본질적 특성**
1. **고빈도 호출**: 로깅은 매우 자주 호출됨 → 성능 중요
2. **단순한 데이터**: 레벨 + 메시지 + 컨텍스트면 충분
3. **비즈니스 로직 아님**: Domain Events보다 단순한 추상화 적합

### **DDD와 성능의 균형**
- ✅ **순수성 유지**: Interface 기반 의존성 주입
- ✅ **성능 확보**: 불필요한 객체 생성 제거
- ✅ **API 호환성**: 기존 코드 변경 없음

## 📊 **예상 성능 개선**

### **Before (현재)**
```python
logger.info("메시지")
# → DomainLogRequested 객체 생성 (UUID + datetime + metadata)
# → Publisher.publish() 호출
# → Subscriber에서 Infrastructure Logger 호출
# 총 비용: ~4ms (10k 호출 시 39.73ms)
```

### **After (최적화)**
```python
logger.info("메시지")
# → 주입된 Infrastructure Logger 직접 호출
# 총 비용: ~0.015ms (10k 호출 시 0.15ms)
# 성능 향상: 272배 빨라짐
```

## ⚠️ **검토 사항**

### **1. DDD 순수성 vs 성능**
- 의존성 주입이 Domain Events보다 "덜 순수"한가?
- 성능을 위해 아키텍처 원칙을 타협해야 하는가?

### **2. 로깅의 위상**
- 로깅이 정말 Domain Events를 사용할 만큼 중요한가?
- 관찰 도구 vs 비즈니스 이벤트의 구분은?

### **3. 실용성**
- 272배 성능 차이가 실제로 문제가 되는가?
- 금융 시스템에서 로깅 성능이 얼마나 중요한가?

## 🎯 **성공 기준**

- [ ] 로깅 성능 **100배 이상 개선** (39ms → 0.4ms 이하)
- [ ] Domain Layer Infrastructure 의존성 **여전히 0개**
- [ ] 기존 `create_domain_logger` API **100% 호환성**
- [ ] 모든 로깅 기능 **정상 동작**
- [ ] DDD 순수성 원칙 **준수**

## 📝 **진행 마커 규칙**
- [ ]: 미완료 (미시작 상태)
- [-]: 진행 중 (현재 작업 중)
- [x]: 완료 (작업 완료)

---

**태스크 생성일**: 2025년 8월 14일
**예상 소요 시간**: 2.5시간
**우선순위**: High (성능 문제 해결 필요)
**타입**: 성능 최적화 + 아키텍처 개선
