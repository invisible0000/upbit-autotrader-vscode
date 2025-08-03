# 🏗️ Clean Architecture 시스템 개요

> **목적**: 5계층 Clean Architecture 핵심 구조 이해  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 📊 5계층 아키텍처 구조

```
┌─────────────────────────────────────────────┐
│            🎨 Presentation                  │ ← UI만 담당 (Passive View)
│        Views │ Presenters │ Controllers     │
├─────────────────────────────────────────────┤
│            ⚙️ Application                   │ ← Use Case 조율
│      Services │ Commands │ Queries          │
├─────────────────────────────────────────────┤
│             💎 Domain                       │ ← 비즈니스 핵심 (중심)
│      Entities │ Value Objects │ Events      │
├─────────────────────────────────────────────┤
│            🔌 Infrastructure                │ ← 외부 연동
│    Repositories │ APIs │ Database           │
├─────────────────────────────────────────────┤
│             🛠️ Shared                       │ ← 공통 유틸리티
│       Common │ Extensions │ Helpers         │
└─────────────────────────────────────────────┘
```

**🎯 의존성 흐름**: `Presentation → Application → Domain ← Infrastructure`

## 🚨 핵심 원칙

### 1. Domain 중심 설계
- **모든 계층이 Domain을 참조**
- Domain은 다른 계층을 참조하지 않음
- 비즈니스 규칙은 Domain에만 존재

### 2. 계층별 단일 책임
```python
# ✅ 올바른 계층 분리
class StrategyPresenter:        # Presentation: UI 표시만
    def show_strategy(self, dto): pass

class StrategyService:          # Application: Use Case 조율
    def create_strategy(self, cmd): pass

class Strategy:                 # Domain: 비즈니스 규칙
    def add_rule(self, rule): pass

class StrategyRepository:       # Infrastructure: 데이터 저장
    def save(self, strategy): pass
```

## 🎯 계층별 핵심 역할

### 🎨 Presentation Layer
**책임**: 사용자 입력/출력만 처리
```python
class TriggerBuilderPresenter:
    def on_create_trigger_clicked(self):
        # 1. 입력 수집
        data = self.view.get_form_data()
        # 2. Application 계층 호출
        result = self.trigger_service.create_trigger(data)
        # 3. 결과 표시
        self.view.show_result(result)
```

### ⚙️ Application Layer
**책임**: Use Case 실행, 트랜잭션 관리
```python
class TriggerService:
    def create_trigger(self, command):
        # 1. 검증
        self._validate(command)
        # 2. Domain 객체 생성
        trigger = Trigger.create(command.variable, command.operator)
        # 3. 저장
        self.trigger_repo.save(trigger)
        # 4. 이벤트 발행
        self.events.publish(TriggerCreated(trigger.id))
```

### 💎 Domain Layer (핵심)
**책임**: 순수한 비즈니스 로직
```python
class Strategy:
    def add_trigger(self, trigger):
        # 비즈니스 규칙 검증
        if not self._is_compatible(trigger):
            raise IncompatibleTriggerError()
        
        self.triggers.append(trigger)
        self._events.append(TriggerAdded(self.id, trigger.id))
```

### 🔌 Infrastructure Layer
**책임**: 외부 시스템 연동
```python
class SqliteTriggerRepository:
    def save(self, trigger: Trigger):
        # Domain 객체 → DB 저장
        data = trigger.to_dict()
        self.db.execute("INSERT INTO triggers ...", data)
```

## 📁 실제 폴더 구조

```
upbit_auto_trading/
├── presentation/          # 🎨 UI 계층
│   ├── views/            # PyQt6 View
│   └── presenters/       # MVP Presenter
├── application/          # ⚙️ App 계층
│   ├── services/         # Use Case 서비스
│   └── commands/         # Command/Query
├── domain/              # 💎 Domain 계층 (핵심)
│   ├── entities/        # Strategy, Trigger, Position
│   ├── value_objects/   # Money, Price, StrategyId
│   └── events/          # Domain Events
├── infrastructure/      # 🔌 Infrastructure 계층
│   ├── repositories/    # DB 접근 구현
│   └── api_clients/     # 외부 API
└── shared/             # 🛠️ 공통 유틸리티
```

## 🔄 핵심 패턴

### CQRS (Command/Query 분리)
```python
# Command: 상태 변경
class CreateStrategyCommand:
    def __init__(self, name, rules):
        self.name = name
        self.rules = rules

# Query: 데이터 조회
class GetStrategyListQuery:
    def __init__(self, user_id):
        self.user_id = user_id
```

### Repository Pattern
```python
# 인터페이스 (Domain)
class StrategyRepository(ABC):
    def save(self, strategy: Strategy): pass
    def find_by_id(self, id: StrategyId): pass

# 구현 (Infrastructure)
class SqliteStrategyRepository(StrategyRepository):
    def save(self, strategy: Strategy):
        # SQLite 저장 구현
```

### Domain Events
```python
class StrategyCreated(DomainEvent):
    def __init__(self, strategy_id):
        self.strategy_id = strategy_id
        self.occurred_at = datetime.now()

# 이벤트 처리
class StrategyEventHandler:
    def handle(self, event: StrategyCreated):
        # 전략 생성 후 처리 로직
```

## 🚀 개발 워크플로

### 새 기능 추가 순서
1. **Domain**: 비즈니스 규칙 정의
2. **Application**: Use Case 구현  
3. **Infrastructure**: 저장/조회 구현
4. **Presentation**: UI 구현

### 기존 기능 수정 영향 범위
- **Domain 변경** → 모든 계층 확인 필요
- **Application 변경** → Presentation 확인
- **Infrastructure 변경** → 인터페이스 유지 시 영향 없음
- **Presentation 변경** → 다른 계층 영향 없음

## 📚 관련 문서

- [계층별 상세 역할](02_LAYER_RESPONSIBILITIES.md)
- [데이터 흐름 가이드](03_DATA_FLOW.md)
- [기능 개발 워크플로](04_FEATURE_DEVELOPMENT.md)

---
**💡 핵심**: "Domain이 중심이 되고, 모든 계층이 Domain을 바라보는 구조입니다!"
