# TASK_20250814_01_Pure_Domain_Logging_Simplification.md

## 🎯 태스크 목표
Domain Layer 로깅 시스템을 진정한 순수성과 단순함으로 재설계

## 📊 문제 분석: 현재 구현이 과도한 이유

### ❌ **현재 문제점들**

#### 1. **과도한 복잡성**
```python
# 현재: 5개의 Domain Events + 복잡한 Publisher + Subscriber
DomainLogRequested, DomainComponentInitialized, DomainOperationStarted,
DomainOperationCompleted, DomainErrorOccurred

# 문제: 단순한 로깅을 위해 너무 많은 이벤트 타입
```

#### 2. **Domain Events의 남용**
```python
# 현재: 로깅마다 이벤트 객체 생성
def info(self, message: str, context_data: Optional[Dict[str, Any]] = None) -> None:
    self._log(LogLevel.INFO, message, context_data)  # 이벤트 생성 오버헤드

# 문제: 로깅은 비즈니스 이벤트가 아니라 관찰 도구
```

#### 3. **불필요한 메타데이터**
```python
# 현재: 로깅 이벤트에 과도한 메타데이터
@dataclass(frozen=True)
class DomainLogRequested(DomainEvent):
    component_name: str
    log_level: LogLevel
    message: str
    context_data: Optional[Dict[str, Any]] = None
    exception_info: Optional[str] = None
    # + 부모 클래스의 event_id, occurred_at, aggregate_id...

# 문제: 단순한 로그 메시지를 위해 8개 이상의 필드
```

#### 4. **DDD 개념 혼동**
```python
# 현재: 로깅을 Domain Event로 취급
# 문제: 로깅은 Domain의 핵심 비즈니스가 아니라 부수적 관찰
```

## 🎯 **진정한 순수 로깅의 원칙**

### ✅ **Core Principle 1: 로깅은 비즈니스가 아니다**
- 로깅은 Domain의 핵심 관심사가 아님
- 로깅은 관찰/디버깅 도구일 뿐
- Domain Events는 비즈니스 의미가 있는 사건에만 사용

### ✅ **Core Principle 2: 최소한의 인터페이스**
- Domain에서는 단순한 로깅 인터페이스만 제공
- 복잡한 이벤트 시스템 불필요
- "로그를 남긴다"는 행위만 추상화

### ✅ **Core Principle 3: Zero Overhead Principle**
- 로깅 때문에 Domain 성능 저하 없어야 함
- 객체 생성 최소화
- 단순한 함수 호출 수준

## 🏗️ **제안하는 순수 로깅 아키텍처**

### **Phase 1: Minimal Pure Logging Interface**

```python
# domain/logging.py (극도로 단순화)
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class DomainLogger(ABC):
    """순수 Domain 로깅 인터페이스 - 최소한만"""

    @abstractmethod
    def log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """단일 로깅 메서드"""
        pass

class NoOpLogger(DomainLogger):
    """아무것도 하지 않는 로거 (기본값)"""

    def log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        pass  # 아무것도 하지 않음

# 전역 로거 인스턴스 (Infrastructure에서 주입)
_domain_logger: DomainLogger = NoOpLogger()

def set_domain_logger(logger: DomainLogger) -> None:
    """Infrastructure에서 실제 로거 주입"""
    global _domain_logger
    _domain_logger = logger

def log_info(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Domain에서 사용하는 단순 함수"""
    _domain_logger.log("INFO", message, context)

def log_error(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Domain에서 사용하는 단순 함수"""
    _domain_logger.log("ERROR", message, context)
```

### **Phase 2: Infrastructure Implementation**

```python
# infrastructure/logging/domain_logger_impl.py
class InfrastructureDomainLogger(DomainLogger):
    """Infrastructure에서 Domain Logger 구현"""

    def __init__(self, component_logger):
        self.infrastructure_logger = component_logger

    def log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """단순하게 Infrastructure Logger에 전달"""
        if level == "INFO":
            self.infrastructure_logger.info(message)
        elif level == "ERROR":
            self.infrastructure_logger.error(message)
        # 필요한 레벨만 간단히 처리
```

### **Phase 3: Simple Integration**

```python
# run_desktop_ui.py (애플리케이션 시작점)
def setup_domain_logging():
    """Domain에 단순 로거 주입"""
    from upbit_auto_trading.infrastructure.logging import create_component_logger
    from upbit_auto_trading.infrastructure.logging.domain_logger_impl import InfrastructureDomainLogger
    from upbit_auto_trading.domain.logging import set_domain_logger

    # Infrastructure Logger 생성
    infra_logger = create_component_logger("Domain")

    # Domain에 주입
    domain_logger = InfrastructureDomainLogger(infra_logger)
    set_domain_logger(domain_logger)
```

## 📋 **작업 계획**

### **Phase 1: 현재 분석 및 단순화 설계** (30분)
- [-] 현재 Domain Events 로깅 복잡도 분석
- [ ] 진정한 필수 기능만 식별
- [ ] 최소한의 순수 인터페이스 설계
- [ ] 성능 오버헤드 분석

### **Phase 2: 순수 로깅 인터페이스 구현** (45분)
- [ ] `domain/logging.py` 단순화
- [ ] NoOp 기본 구현 (Infrastructure 없이도 동작)
- [ ] 의존성 주입 메커니즘
- [ ] 기존 Domain Events 로깅과 비교

### **Phase 3: Infrastructure 구현** (30분)
- [ ] Infrastructure에서 순수 인터페이스 구현
- [ ] 기존 create_component_logger와 연결
- [ ] 애플리케이션 시작점에서 주입 설정

### **Phase 4: 마이그레이션 및 검증** (45분)
- [ ] 기존 Domain Services 마이그레이션
- [ ] 성능 비교 (이벤트 기반 vs 직접 호출)
- [ ] DDD 순수성 검증
- [ ] 실제 동작 테스트

## 🔍 **예상 결과**

### **Before (현재 - 과도한 복잡성)**
```python
# Domain Service에서 로깅
logger = create_domain_logger("StrategyService")
logger.info("매매 신호 생성")
# → DomainLogRequested 이벤트 생성 → Publisher → Subscriber → Infrastructure Logger
```

### **After (순수 단순함)**
```python
# Domain Service에서 로깅
from upbit_auto_trading.domain.logging import log_info
log_info("매매 신호 생성")
# → 직접 Infrastructure Logger 호출 (의존성 주입으로 순수성 유지)
```

### **핵심 개선점**
- ✅ **성능**: 이벤트 객체 생성 오버헤드 제거
- ✅ **단순성**: 5개 이벤트 타입 → 1개 인터페이스
- ✅ **순수성**: Infrastructure 의존성 여전히 0개 (의존성 주입)
- ✅ **가독성**: 복잡한 이벤트 시스템 → 단순한 함수 호출

## ⚠️ **검토 포인트**

### **1. 현재 구현이 정말 과도한가?**
- Domain Events를 로깅에 사용하는 것이 적절한가?
- 5개 이벤트 타입이 필요한가?
- 성능 오버헤드는 얼마나 되는가?

### **2. 의존성 주입 vs Domain Events**
- 의존성 주입이 Domain Events보다 순수한가?
- 어떤 방식이 더 DDD 원칙에 부합하는가?
- 테스트 용이성은 어떻게 달라지는가?

### **3. 실용성 vs 순수성**
- 현재 구현으로도 충분한가?
- 단순화가 정말 필요한가?
- 추가 복잡성의 가치가 있는가?

## 🎯 **성공 기준**

- [ ] Domain Layer Infrastructure 의존성 여전히 0개
- [ ] 로깅 성능 개선 (객체 생성 오버헤드 감소)
- [ ] 코드 복잡도 감소 (파일 수, 클래스 수 감소)
- [ ] 기존 로깅 기능성 100% 유지
- [ ] DDD 순수성 원칙 준수

## 📝 **진행 마커 규칙**
- [ ]: 미완료 (미시작 상태)
- [-]: 진행 중 (현재 작업 중)
- [x]: 완료 (작업 완료)

---

**태스크 생성일**: 2025년 8월 14일
**예상 소요 시간**: 2.5시간
**우선순위**: Medium (현재 시스템도 완전히 동작하므로)
**타입**: 아키텍처 개선 (성능 + 단순성)
