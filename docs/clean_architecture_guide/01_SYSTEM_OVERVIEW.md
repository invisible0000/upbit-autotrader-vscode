# 🏗️ Clean Architecture 시스템 개요

> **목적**: 5계층 Clean Architecture 전체 구조 이해  
> **독자**: 개발자, LLM 에이전트  
> **예상 읽기 시간**: 10분

## 📊 아키텍처 다이어그램

```
┌─────────────────────────────────────────────┐
│                Presentation                 │ ← PyQt6 UI, MVP 패턴
│     Views  │  Presenters  │  Controllers    │
├─────────────────────────────────────────────┤
│                Application                  │ ← 비즈니스 로직 조율
│   Services │ Query Handlers │ Event Handlers│
├─────────────────────────────────────────────┤
│                  Domain                     │ ← 핵심 비즈니스 규칙 (중심)
│   Entities │  Value Objects │ Domain Events │
├─────────────────────────────────────────────┤
│               Infrastructure                │ ← 외부 시스템 연동
│ Repositories │ API Clients │ Event Storage │
├─────────────────────────────────────────────┤
│                  Shared                     │ ← 공통 유틸리티
│   Common   │   Extensions   │   Helpers    │
└─────────────────────────────────────────────┘
```

## 🎯 계층별 핵심 역할

### 🎨 Presentation Layer (UI 계층)
```python
# 예시: 전략 관리 Presenter
class StrategyManagementPresenter:
    def __init__(self, view, strategy_service):
        self.view = view
        self.strategy_service = strategy_service  # Application 계층
        
    def on_create_strategy_clicked(self):
        # 사용자 입력 → Application 계층으로 전달
        strategy_data = self.view.get_strategy_form_data()
        result = self.strategy_service.create_strategy(strategy_data)
        self.view.update_strategy_list(result.strategies)
```

### ⚙️ Application Layer (애플리케이션 계층)
```python
# 예시: 전략 생성 서비스
class StrategyCreationService:
    def __init__(self, strategy_repo, event_publisher):
        self.strategy_repo = strategy_repo      # Infrastructure
        self.event_publisher = event_publisher  # Infrastructure
        
    def create_strategy(self, command: CreateStrategyCommand):
        # 1. Domain 객체 생성
        strategy = Strategy.create(command.name, command.rules)
        
        # 2. 저장 (Infrastructure 위임)
        self.strategy_repo.save(strategy)
        
        # 3. 이벤트 발행
        self.event_publisher.publish(StrategyCreatedEvent(strategy.id))
        
        return CreateStrategyResult(strategy.id)
```

### 💎 Domain Layer (도메인 계층) - 핵심
```python
# 예시: 전략 도메인 엔티티
class Strategy:
    def __init__(self, strategy_id, name, entry_rules, management_rules):
        self.id = strategy_id
        self.name = name
        self.entry_rules = entry_rules
        self.management_rules = management_rules
        self._events = []
        
    def add_management_rule(self, rule: ManagementRule):
        if len(self.management_rules) >= 5:
            raise TooManyManagementRulesError()
        
        self.management_rules.append(rule)
        self._events.append(ManagementRuleAddedEvent(self.id, rule.id))
```

### 🔌 Infrastructure Layer (인프라 계층)
```python
# 예시: SQLite 전략 리포지토리
class SQLiteStrategyRepository:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def save(self, strategy: Strategy):
        # Domain 객체 → 데이터베이스 변환
        query = "INSERT INTO strategies (id, name, rules) VALUES (?, ?, ?)"
        self.db.execute(query, (strategy.id, strategy.name, 
                               json.dumps(strategy.to_dict())))
        
    def find_by_id(self, strategy_id: StrategyId) -> Strategy:
        # 데이터베이스 → Domain 객체 변환
        row = self.db.fetch_one("SELECT * FROM strategies WHERE id = ?", 
                               (strategy_id.value,))
        return Strategy.from_dict(row)
```

### 🛠️ Shared Layer (공유 계층)
```python
# 예시: 공통 유틸리티
class Result:
    def __init__(self, success: bool, data=None, error=None):
        self.success = success
        self.data = data
        self.error = error
        
    @classmethod
    def success_with(cls, data):
        return cls(True, data=data)
        
    @classmethod
    def failure_with(cls, error):
        return cls(False, error=error)
```

## 🔄 데이터 흐름 예시

### 1. 사용자 액션 → 시스템 응답
```
1. [UI] 사용자가 "전략 생성" 버튼 클릭
   ↓
2. [Presenter] 입력 데이터 수집 및 검증
   ↓
3. [Application] 비즈니스 로직 실행
   ↓
4. [Domain] 전략 객체 생성 및 규칙 검증
   ↓
5. [Infrastructure] 데이터베이스 저장
   ↓
6. [Application] 이벤트 발행
   ↓
7. [Presenter] UI 업데이트
```

### 2. 의존성 방향 (중요!)
```
Presentation ──→ Application ──→ Domain
     ↓                             ↑
Infrastructure ←─────────────────────┘
     ↓
   Shared
```
**핵심**: Domain이 중심이며, 다른 계층을 참조하지 않음!

## 📁 실제 파일 구조

```
upbit_auto_trading/
├── presentation/           # UI 계층
│   ├── views/             # PyQt6 UI 클래스
│   ├── presenters/        # MVP 패턴 Presenter
│   └── controllers/       # 사용자 입력 처리
├── application/           # 애플리케이션 계층  
│   ├── services/          # 비즈니스 로직 조율
│   ├── queries/           # 조회 처리
│   └── events/            # 이벤트 핸들러
├── domain/               # 도메인 계층 (핵심)
│   ├── entities/         # 핵심 비즈니스 객체
│   ├── value_objects/    # 값 객체
│   ├── services/         # 도메인 서비스
│   └── events/           # 도메인 이벤트
├── infrastructure/       # 인프라 계층
│   ├── repositories/     # 데이터 접근 구현
│   ├── api_clients/      # 외부 API 클라이언트
│   ├── database/         # DB 연결 및 설정
│   └── events/           # 이벤트 저장소
└── shared/              # 공통 유틸리티
    ├── common/          # 공통 클래스
    ├── extensions/      # 확장 메서드
    └── helpers/         # 헬퍼 함수
```

## 🎯 핵심 개념 요약

### Domain-Driven Design (DDD)
- **Entity**: 고유 식별자를 가진 객체 (Strategy, Position)
- **Value Object**: 값으로만 식별되는 객체 (Money, Price)
- **Domain Service**: 여러 Entity에 걸친 비즈니스 로직
- **Repository**: 도메인 객체 저장/조회 인터페이스

### CQRS (Command Query Responsibility Segregation)
- **Command**: 시스템 상태 변경 (CreateStrategy, UpdatePosition)
- **Query**: 데이터 조회 (GetStrategyList, GetBacktestResults)
- **분리 이유**: 읽기/쓰기 최적화, 복잡도 감소

### Event-Driven Architecture
- **Domain Event**: 비즈니스 중요 사건 (StrategyCreated, PositionClosed)
- **Event Handler**: 이벤트 발생 시 실행되는 로직
- **Event Bus**: 이벤트 발행/구독 중계

## 🚀 개발자를 위한 실용 가이드

### 새로운 기능 개발 시 순서
1. **Domain**: 비즈니스 규칙 정의
2. **Application**: 유스케이스 구현
3. **Infrastructure**: 데이터 저장/조회 구현
4. **Presentation**: UI 구현

### 기존 기능 수정 시 영향 범위
- **Domain 변경**: 모든 계층 영향 (신중히 결정)
- **Application 변경**: Presentation + Infrastructure 확인
- **Infrastructure 변경**: Application 인터페이스 유지 시 영향 없음
- **Presentation 변경**: 다른 계층 영향 없음

## 🔍 다음 단계

- **[계층별 책임](02_LAYER_RESPONSIBILITIES.md)**: 각 계층의 상세 역할
- **[데이터 흐름](03_DATA_FLOW.md)**: 실제 요청 처리 과정
- **[기능 추가 가이드](04_FEATURE_DEVELOPMENT.md)**: 실무 개발 워크플로

---
**💡 핵심**: "Clean Architecture는 비즈니스 로직(Domain)을 중심으로 모든 것이 설계되는 아키텍처입니다!"
