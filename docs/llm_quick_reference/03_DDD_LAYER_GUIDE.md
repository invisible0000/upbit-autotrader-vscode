# 🏗️ DDD 계층 구조 + Event-Driven + 금지사항 가이드
*최종 업데이트: 2025년 8월 10일*

## ⚡ 아키텍처 전략: Hybrid Pattern

### 🎯 핵심 아키텍처 조합
- **DDD + MVP**: 설정, 단순 UI (85% 영역)
- **Event-Driven**: 거래, 전략, 시스템 상태 (15% 핵심 영역)

#### � 자동 검증 명령어
```powershell
# Domain Layer에 외부 의존성 있는지 확인 (결과 없어야 정상)
grep -r "import sqlite3" upbit_auto_trading/domain/
grep -r "import requests" upbit_auto_trading/domain/
grep -r "from PyQt6" upbit_auto_trading/domain/

# Presenter에 SQLite 직접 사용 있는지 확인 (결과 없어야 정상)
grep -r "import sqlite3" upbit_auto_trading/ui/
grep -r "sqlite3.connect" upbit_auto_trading/presentation/

# print 문 사용 확인 (결과 없어야 정상 - Infrastructure 로깅 사용 필수)
grep -r "print(" upbit_auto_trading/ --exclude-dir=tests --exclude-dir=tools

# 호환성 alias 사용 확인 (결과 없어야 정상)
grep -r "import.*as.*View" upbit_auto_trading/ui/
grep -r "__all__.*alias" upbit_auto_trading/

# Event-Driven과 MVP 혼용 확인 (결과 분석 필요)
grep -r "event_bus.*connect\|connect.*event_bus" upbit_auto_trading/ui/
grep -r "pyqtSignal.*Event.*Bus\|Event.*Bus.*pyqtSignal" upbit_auto_trading/
```칙)
```
🎨 Presentation → ⚙️ Application → 💎 Domain ← 🔧 Infrastructure
     ↓              ↓              ↑           ↑
   View/MVP      Use Cases      Business    Repository
                                 Logic       Impl
     ↓              ↓              ↑           ↑
  Event Bus ←── Event Handlers ←── Domain ←── Event Storage
```

**핵심**: Domain이 중심이며, 다른 계층을 참조하지 않음

---

## 📁 계층별 위치 + 역할 + 금지사항

### 🎨 Presentation Layer
**📂 위치**: `upbit_auto_trading/ui/desktop/`, `upbit_auto_trading/presentation/`
- **✅ 역할**: UI 표시, 사용자 입력 수집, View 업데이트
- **✅ 허용**: Use Case 호출, View Interface 구현, MVP 패턴
- **✅ 적용된 패턴**: Settings MVP 100% 완성 (ApiSettingsView, DatabaseSettingsView, NotificationSettingsView, UISettingsView)
- **❌ 금지**: SQLite 직접 사용, 파일시스템 접근, 비즈니스 로직, print 문 사용
- **🔧 로깅**: Infrastructure logging `create_component_logger()` 필수 사용

### ⚙️ Application Layer
**📂 위치**: `upbit_auto_trading/application/`
- **✅ 역할**: Use Case 조율, DTO 변환, 트랜잭션 관리
- **✅ 허용**: Domain Service + Repository Interface만
- **❌ 금지**: SQLite, HTTP, 구체적 기술 스택, UI 참조, print 문 사용
- **🔧 로깅**: Infrastructure logging `create_component_logger()` 필수 사용

### 💎 Domain Layer
**📂 위치**: `upbit_auto_trading/domain/`
- **✅ 역할**: 순수 비즈니스 로직, Entity, Value Object, Domain Service
- **✅ 허용**: 자체 Entity, Value Object, Service, Repository Interface만
- **❌ 금지**: 다른 계층 import 절대 금지, SQLite, HTTP, UI, print 문 사용
- **🔧 로깅**: Infrastructure logging `create_component_logger()` 필수 사용

### 🔧 Infrastructure Layer
**📂 위치**: `upbit_auto_trading/infrastructure/`
- **✅ 역할**: 외부 시스템 연동, Repository 구현, DB 접근, Event Bus 구현
- **✅ 허용**: SQLite, API, 파일시스템, Domain Entity 변환, Event 발행/구독
- **✅ 완성된 시스템**: 로깅 시스템 (create_component_logger), Repository Container, Event-Driven Bus
- **❌ 금지**: Domain 로직 포함, UI 로직, print 문 사용
- **🔧 로깅**: Infrastructure logging `create_component_logger()` 필수 사용
- **📦 Event System**: Event Bus, Domain Event Publisher, Event Storage 제공

### 🎭 Event-Driven Layer (Infrastructure 하위)
**📂 위치**: `upbit_auto_trading/infrastructure/events/`
- **✅ 역할**: 시스템 간 비동기 통신, 이벤트 중재, 상태 전파
- **✅ 허용**: Event Bus, Event Handlers, Domain Event 처리
- **✅ 적용 영역**: 거래 실행, 전략 생명주기, 시스템 상태 변경, 실시간 모니터링
- **❌ 금지**: 단순 UI 상호작용, 로컬 컴포넌트 통신에 사용
- **🔧 주요 컴포넌트**: EventBusInterface, InMemoryEventBus, DomainEventPublisher

---

## 🚨 자주 위반하는 패턴들 (즉시 차단!)

### ❌ 절대 금지된 코드

#### 1. Presenter에서 SQLite 직접 사용 (계층 위반!)
```python
# ❌ 절대 금지!
class BadPresenter:
    def method(self):
        import sqlite3  # 금지!
        conn = sqlite3.connect("db.sqlite3")
        cursor = conn.execute("SELECT * FROM strategies")

        print("데이터 로드 중...")  # 금지! Infrastructure 로깅 사용 필수
```

#### 2. Domain에서 다른 계층 import (의존성 위반!)
```python
# ❌ 절대 금지!
from upbit_auto_trading.infrastructure.database import SomeRepo  # 금지!
from upbit_auto_trading.ui.desktop import SomeWidget  # 금지!

def domain_method():
    print("처리 중...")  # 금지! Infrastructure 로깅 사용 필수
```

#### 3. Application에서 UI 직접 조작 (책임 위반!)
```python
# ❌ 절대 금지!
class BadUseCase:
    def execute(self):
        widget.setText("완료")  # UI 직접 조작 금지!
        print("작업 완료")  # 금지! Infrastructure 로깅 사용 필수
```

#### 4. 호환성 alias 사용 (투명성 위반!)
```python
# ❌ 절대 금지!
from upbit_auto_trading.ui.desktop.screens.settings import ApiSettingsView as ApiSettings  # alias 금지!
# __init__.py에서 alias 제공도 금지!
```

#### 5. Event-Driven과 MVP 혼용 (아키텍처 혼란!)
```python
# ❌ 절대 금지!
class BadPresenter:
    def method(self):
        # PyQt Signal과 Event Bus를 동시에 사용
        self.widget.clicked.connect(self.handle_click)  # MVP 패턴
        self.event_bus.publish(ClickEvent())  # Event-Driven 패턴
        # 한 컨텍스트에서 두 패턴 혼용 금지!
```

### ✅ 올바른 코드 패턴

#### 1. Event-Driven 영역: 거래/전략/시스템 상태
```python
# ✅ 올바른 패턴 (거래 시스템)
from upbit_auto_trading.infrastructure.events.event_system_initializer import EventSystemInitializer

class TradingEventHandler:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.logger = create_component_logger("TradingEventHandler")

    async def handle_market_data(self, event_data):
        self.logger.info("시장 데이터 수신")
        # 전략 평가 이벤트 발행
        strategy_event = StrategyEvaluationEvent(market_data=event_data)
        await self.event_bus.publish(strategy_event.to_dict())
```

#### 2. MVP 영역: 설정/단순 UI
```python
# ✅ 올바른 패턴 (설정 화면)
from upbit_auto_trading.infrastructure.logging import create_component_logger

class GoodPresenter:
    def __init__(self, use_case):
        self.use_case = use_case
        self.logger = create_component_logger("GoodPresenter")

    def method(self):
        self.logger.info("작업 시작")
        result = self.use_case.execute(request_dto)
        self.view.update_display(result)
        self.logger.info("작업 완료")
```

#### 2. Domain은 순수 로직만 + Infrastructure 로깅
```python
# ✅ 올바른 패턴
from upbit_auto_trading.infrastructure.logging import create_component_logger

class GoodDomainService:
    def __init__(self, repo: AbstractRepo):  # 인터페이스만
        self.repo = repo
        self.logger = create_component_logger("GoodDomainService")

    def validate_strategy(self, strategy):
        self.logger.debug("전략 검증 시작")
        # 순수 비즈니스 로직만
        is_valid = strategy.is_valid()
        self.logger.info(f"전략 검증 결과: {is_valid}")
        return is_valid
```

#### 3. Hybrid Architecture 브릿지 패턴
```python
# ✅ 올바른 패턴 (MVP와 Event-Driven 연결)
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.ui.desktop.screens.settings.api_settings import ApiSettingsView  # 직접 import
from upbit_auto_trading.ui.desktop.screens.settings.database_settings import DatabaseSettingsView

class MVPToEventBridge:
    """MVP 패턴과 Event-Driven 패턴을 연결하는 브릿지"""
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.logger = create_component_logger("MVPToEventBridge")

    async def notify_critical_system_change(self, change_data):
        """중요한 시스템 변경사항만 이벤트로 전파"""
        self.logger.info("시스템 변경사항 이벤트 발행")
        event = SystemStateChangedEvent(change_data)
        await self.event_bus.publish(event.to_dict())

class GoodRepository(IStrategyRepository):  # Interface 구현
    def __init__(self):
        self.logger = create_component_logger("GoodRepository")

    def save(self, strategy: Strategy):
        self.logger.info("전략 저장 시작")
        # Domain Entity → Database 변환
        record = self._to_database_record(strategy)
        # SQLite 저장 (Infrastructure만 허용)
        self.db.save(record)
        self.logger.info("전략 저장 완료")
```

---

## 🔍 계층 위반 즉시 체크 방법

### 🔧 자동 검증 명령어
```powershell
# Domain Layer에 외부 의존성 있는지 확인 (결과 없어야 정상)
grep -r "import sqlite3" upbit_auto_trading/domain/
grep -r "import requests" upbit_auto_trading/domain/
grep -r "from PyQt6" upbit_auto_trading/domain/

# Presenter에 SQLite 직접 사용 있는지 확인 (결과 없어야 정상)
grep -r "import sqlite3" upbit_auto_trading/ui/
grep -r "sqlite3.connect" upbit_auto_trading/presentation/

# print 문 사용 확인 (결과 없어야 정상 - Infrastructure 로깅 사용 필수)
grep -r "print(" upbit_auto_trading/ --exclude-dir=tests --exclude-dir=tools

# 호환성 alias 사용 확인 (결과 없어야 정상)
grep -r "import.*as.*View" upbit_auto_trading/ui/
grep -r "__all__.*alias" upbit_auto_trading/
```

### 📋 파일별 점검 체크리스트
#### Domain Layer 파일 점검
- [ ] `import` 문에 infrastructure, ui, application 없음
- [ ] SQLite, HTTP, 파일시스템 관련 코드 없음
- [ ] 순수 비즈니스 로직만 포함
- [ ] `print` 문 없음 (Infrastructure 로깅 사용)

#### Presenter 파일 점검 (MVP 영역)
- [ ] Use Case 호출만 있음
- [ ] SQLite 직접 접근 없음
- [ ] 복잡한 비즈니스 계산 없음
- [ ] `print` 문 없음 (Infrastructure 로깅 사용)
- [ ] 직접 import 사용 (호환성 alias 금지)
- [ ] Event Bus 사용 없음 (MVP 패턴 유지)

#### Event Handler 파일 점검 (Event-Driven 영역)
- [ ] 거래/전략/시스템 상태 관련 이벤트만 처리
- [ ] PyQt Signal/Slot 사용 없음
- [ ] 비동기 처리 패턴 사용
- [ ] Event Bus 인터페이스 의존

#### Use Case 파일 점검
- [ ] Domain Service + Repository Interface만 의존
- [ ] UI 위젯 직접 조작 없음
- [ ] 구체적 기술 스택 참조 없음
- [ ] `print` 문 없음 (Infrastructure 로깅 사용)
- [ ] 필요 시 도메인 이벤트 발행

---

## 🛠️ 올바른 개발 순서 (Bottom-Up + Hybrid)

### 1단계: Domain Layer 먼저
```python
# 1. Entity, Value Object 정의
class Strategy(Entity):
    def validate(self) -> bool:
        # 비즈니스 로직

# 2. Repository Interface 정의
class IStrategyRepository(ABC):
    def save(self, strategy: Strategy) -> None:
        pass

# 3. Domain Events 정의 (필요시)
class StrategyCreatedEvent(DomainEvent):
    strategy_id: str
    created_at: datetime
```

### 2단계: Infrastructure Layer
```python
# 4. Repository 구현체
class SqliteStrategyRepository(IStrategyRepository):
    def save(self, strategy: Strategy) -> None:
        # SQLite 저장 로직

# 5. Event System 설정 (Event-Driven 영역만)
class TradingEventBus:
    def __init__(self):
        self.event_bus = EventSystemInitializer.create_simple_event_system()
```

### 3단계: Application Layer
```python
# 6. Use Case 구현
class CreateStrategyUseCase:
    def __init__(self, repo: IStrategyRepository):
        self.repo = repo

    def execute(self, request: CreateStrategyDto) -> ResponseDto:
        # Domain Entity 생성 + Repository 호출
        # 필요시 도메인 이벤트 발행
```

### 4단계: Presentation Layer (패턴 선택)
```python
# 7a. MVP 패턴 (설정/단순 UI)
class StrategyPresenter:
    def __init__(self, use_case: CreateStrategyUseCase):
        self.use_case = use_case

    def create_strategy(self):
        result = self.use_case.execute(dto)
        self.view.show_result(result)

# 7b. Event-Driven 패턴 (거래/전략/시스템 상태)
class TradingEventHandler:
    def __init__(self, event_bus):
        self.event_bus = event_bus

    async def handle_strategy_signal(self, event_data):
        # 전략 신호 처리 및 다른 시스템에 전파
```

---

## 🎯 핵심 원칙 요약

### ✅ 허용되는 의존성
- **Presentation** → Application (Use Case 호출)
- **Application** → Domain (Service, Repository Interface)
- **Infrastructure** → Domain (Entity 변환, Interface 구현)
- **Event System** → Domain (Domain Event 처리)

### ❌ 금지되는 의존성
- **Domain** → 다른 모든 계층 (절대 금지!)
- **Presentation** → Infrastructure (Repository 직접 사용 금지)
- **Application** → Infrastructure (구체 구현 의존 금지)
- **MVP와 Event-Driven 혼용** (한 컨텍스트에서 두 패턴 동시 사용 금지)

### 🎭 아키텍처 패턴 선택 가이드
- **Event-Driven 사용**: 거래 실행, 전략 생명주기, 시스템 상태 변경, 실시간 모니터링
- **MVP 사용**: 설정 관리, 단순 UI, 정적 데이터 관리
- **브릿지 패턴**: MVP에서 중요한 변경사항만 이벤트로 전파

### 💡 계층 위반 시 해결책
1. **Domain 위반** → 해당 로직을 적절한 계층으로 이동
2. **Presenter 위반** → Use Case 생성 후 위임
3. **Use Case 위반** → Repository Interface로 추상화
4. **아키텍처 혼용** → 명확한 패턴 선택 후 일관성 유지

---

**🔥 기억할 것**:
1. Domain Layer가 다른 계층을 import하고 있는지 먼저 확인!
2. 거래/전략/시스템 상태는 Event-Driven, 설정/UI는 MVP!
3. 한 컨텍스트에서 두 아키텍처 패턴 혼용 금지!

**⚡ 빠른 검증**: `python run_desktop_ui.py` 실행해서 오류 없으면 계층 구조 정상!
