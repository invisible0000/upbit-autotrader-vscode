# 🛠️ 전문가 리팩토링 블루프린트 종합

## 📋 분석 개요

본 문서는 `docs/upbit_trading_system_refactoring_blueprints` 폴더의 전문가 리팩토링 계획을 종합하여 실행 가능한 리팩토링 로드맵을 제시합니다.

**분석 범위**: refactoring_blueprints 폴더 내 5개 블루프린트 문서  
**현재 진행률**: 75% 완료 상태 (전문가 평가)  
**목표**: 단계별 리팩토링 실행 계획 수립

## 🎯 전문가 진단: 현재 시스템 성숙도

### ✅ 완성된 우수 구조 (유지)
- **3-Database 아키텍처**: 고정된 표준 구조
- **컴포넌트 시스템**: `component_system/` 완전 분리
- **계층별 기본 구조**: data_layer, business_logic, ui 폴더 분리
- **중앙 집중식 설정**: `config/database_paths.py` 경로 관리
- **글로벌 DB 매니저**: 싱글톤 패턴 연결 관리

### 🔧 리팩토링 필요 영역 (개선)
- **UI-Business Logic 분리**: 현재 75% → 목표 95%
- **Service Layer 구축**: 현재 30% → 목표 90%
- **Repository 패턴**: 현재 40% → 목표 90%
- **이벤트 시스템**: 현재 10% → 목표 80%

## 🏗️ 전문가 권장 리팩토링 아키텍처

### 1. 최종 목표 구조
```
📁 리팩토링 완료 후 구조:
upbit_auto_trading/
├── 🎨 presentation/           # UI 계층 (Passive View)
│   ├── desktop/              # PyQt6 UI (표시만 담당)
│   ├── presenters/           # MVP 패턴 Presenter
│   └── view_models/          # MVVM 패턴 ViewModel
├── 🚀 application/           # Application 계층 (Use Cases)
│   ├── services/             # 비즈니스 서비스
│   ├── dto/                  # 데이터 전송 객체
│   └── commands/             # Command 패턴
├── 🧠 domain/                # Domain 계층 (핵심 비즈니스)
│   ├── entities/             # 도메인 엔티티
│   ├── value_objects/        # 값 객체
│   ├── services/             # 도메인 서비스
│   ├── repositories/         # 추상 Repository
│   └── events/               # 도메인 이벤트
├── 🔧 infrastructure/        # Infrastructure 계층
│   ├── repositories/         # 구체 Repository 구현
│   ├── external_apis/        # 외부 API 클라이언트
│   ├── database/             # DB 접근 로직
│   └── messaging/            # 이벤트 버스
├── 📊 shared/                # 공유 계층
│   ├── utils/                # 공통 유틸리티
│   ├── config/               # 설정 관리
│   └── exceptions/           # 예외 정의
└── 📁 data/                  # 데이터 파일 (외부)
    ├── settings.sqlite3
    ├── strategies.sqlite3
    └── market_data.sqlite3
```

### 2. 계층별 리팩토링 전략

#### Presentation Layer (UI 계층)
**목표**: UI를 완전히 수동적(Passive)으로 만들기

```python
# ❌ 현재: UI에 비즈니스 로직 혼재
class StrategyMaker(QWidget):
    def save_strategy(self):
        # 검증 로직
        # DB 저장 로직
        # 비즈니스 규칙 적용

# ✅ 리팩토링 후: Passive View
class StrategyMakerView(QWidget):
    def __init__(self, presenter):
        self.presenter = presenter
        
    def on_save_clicked(self):
        strategy_data = self.collect_form_data()
        self.presenter.save_strategy(strategy_data)
        
    def display_validation_errors(self, errors):
        # 단순히 표시만 담당
        pass

class StrategyMakerPresenter:
    def __init__(self, view, strategy_service):
        self.view = view
        self.strategy_service = strategy_service
        
    def save_strategy(self, strategy_data):
        try:
            result = self.strategy_service.create_strategy(strategy_data)
            self.view.display_success_message()
        except ValidationError as e:
            self.view.display_validation_errors(e.errors)
```

#### Application Layer (서비스 계층)
**목표**: Use Case 중심의 Application Service 구축

```python
# 전략 관리 서비스
class StrategyApplicationService:
    def __init__(self, strategy_repo, trigger_repo, event_bus):
        self.strategy_repo = strategy_repo
        self.trigger_repo = trigger_repo
        self.event_bus = event_bus
        
    def create_strategy(self, command: CreateStrategyCommand) -> StrategyDto:
        # 1. 입력 검증
        self._validate_command(command)
        
        # 2. 도메인 객체 생성
        strategy = Strategy.create(
            name=command.name,
            entry_triggers=command.entry_triggers,
            exit_triggers=command.exit_triggers
        )
        
        # 3. 저장
        self.strategy_repo.save(strategy)
        
        # 4. 이벤트 발행
        self.event_bus.publish(StrategyCreated(strategy.id))
        
        # 5. DTO 반환
        return StrategyDto.from_entity(strategy)

# 트리거 관리 서비스
class TriggerApplicationService:
    def create_trigger(self, command: CreateTriggerCommand) -> TriggerDto:
        # Use Case 구현
        pass
        
    def validate_trigger_compatibility(self, trigger_id, variable_id) -> bool:
        # 호환성 검증 Use Case
        pass
```

#### Domain Layer (도메인 계층)
**목표**: Rich Domain Model 구축

```python
# 도메인 엔티티
class Strategy:
    def __init__(self, strategy_id, name, entry_triggers, exit_triggers):
        self.id = strategy_id
        self.name = name
        self.entry_triggers = entry_triggers
        self.exit_triggers = exit_triggers
        self.version = 1
        self.status = StrategyStatus.DRAFT
        
    @classmethod
    def create(cls, name, entry_triggers, exit_triggers):
        # 팩토리 메서드
        strategy_id = StrategyId.generate()
        strategy = cls(strategy_id, name, entry_triggers, exit_triggers)
        strategy._validate_business_rules()
        return strategy
        
    def add_trigger(self, trigger, trigger_type):
        # 비즈니스 규칙 검증
        if not self._can_add_trigger(trigger):
            raise DomainException("호환되지 않는 트리거입니다")
            
        if trigger_type == TriggerType.ENTRY:
            self.entry_triggers.append(trigger)
        else:
            self.exit_triggers.append(trigger)
            
        self.version += 1
        
    def evaluate_entry_signal(self, market_data) -> Signal:
        # 순수한 비즈니스 로직
        entry_results = [t.evaluate(market_data) for t in self.entry_triggers]
        return self._combine_signals(entry_results, self.entry_logic)

# 도메인 서비스
class StrategyCompatibilityService:
    def check_trigger_compatibility(self, strategy, new_trigger) -> bool:
        # 복잡한 호환성 검증 로직
        pass

# 값 객체
@dataclass(frozen=True)
class StrategyId:
    value: str
    
    @classmethod
    def generate(cls):
        return cls(str(uuid.uuid4()))
```

#### Infrastructure Layer (인프라 계층)
**목표**: 구체적인 기술 구현 분리

```python
# Repository 구현
class SqliteStrategyRepository(StrategyRepository):
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def save(self, strategy: Strategy):
        conn = self.db_manager.get_connection('strategies')
        # SQLite 저장 로직
        
    def find_by_id(self, strategy_id: StrategyId) -> Strategy:
        # SQLite 조회 로직
        pass
        
    def find_active_strategies(self) -> List[Strategy]:
        # Active 전략 조회
        pass

# 외부 API 클라이언트
class UpbitApiClient:
    def __init__(self, api_config):
        self.api_config = api_config
        
    def get_market_data(self, market, interval) -> MarketData:
        # Upbit API 호출
        pass
        
    def place_order(self, order_request) -> OrderResult:
        # 주문 실행
        pass

# 이벤트 버스 구현
class InMemoryEventBus(EventBus):
    def __init__(self):
        self.handlers = defaultdict(list)
        
    def subscribe(self, event_type, handler):
        self.handlers[event_type].append(handler)
        
    def publish(self, event: DomainEvent):
        for handler in self.handlers[type(event)]:
            handler.handle(event)
```

## 🚀 단계별 리팩토링 실행 계획

### Phase 1: Domain Layer 구축 (2주)
**목표**: 핵심 비즈니스 로직을 Domain 계층으로 추출

#### Week 1: 도메인 모델 설계
- [ ] Strategy, Trigger, Position 엔티티 설계
- [ ] 값 객체 정의 (StrategyId, TriggerId 등)
- [ ] 도메인 이벤트 설계
- [ ] 비즈니스 규칙 추출 및 정의

#### Week 2: 도메인 서비스 구현
- [ ] StrategyCompatibilityService 구현
- [ ] TriggerEvaluationService 구현
- [ ] PositionManagementService 구현
- [ ] 단위 테스트 작성

#### 성공 기준
- 모든 비즈니스 규칙이 Domain 객체에 포함
- UI와 완전히 독립적인 도메인 모델
- 90% 이상의 테스트 커버리지

### Phase 2: Application Layer 구축 (2주)
**목표**: Use Case 중심의 Application Service 구현

#### Week 1: Application Service 설계
- [ ] StrategyApplicationService 구현
- [ ] TriggerApplicationService 구현
- [ ] BacktestingApplicationService 구현
- [ ] Command/Query 객체 정의

#### Week 2: DTO 및 매핑 구현
- [ ] DTO 클래스 설계 및 구현
- [ ] Entity ↔ DTO 매핑 로직
- [ ] Application Service 테스트
- [ ] 트랜잭션 관리 구현

#### 성공 기준
- 모든 Use Case가 Service로 구현
- DTO를 통한 계층 간 데이터 전송
- 트랜잭션 일관성 보장

### Phase 3: Infrastructure Layer 리팩토링 (2주)
**목표**: Repository 패턴 완전 구현

#### Week 1: Repository 구현
- [ ] 모든 도메인별 Repository 구현
- [ ] Unit of Work 패턴 구현
- [ ] Database Migration 스크립트 작성
- [ ] 기존 데이터 마이그레이션

#### Week 2: 외부 연동 개선
- [ ] Upbit API Client 리팩토링
- [ ] 이벤트 버스 구현
- [ ] 설정 관리 개선
- [ ] Infrastructure 테스트

#### 성공 기준
- Repository를 통한 모든 데이터 접근
- 외부 API 의존성 완전 분리
- 이벤트 기반 느슨한 결합

### Phase 4: Presentation Layer 리팩토링 (3주)
**목표**: Passive View 패턴 적용

#### Week 1: Presenter 구현
- [ ] MVP 패턴 Presenter 구현
- [ ] UI에서 비즈니스 로직 제거
- [ ] View 인터페이스 정의
- [ ] Strategy Maker 리팩토링

#### Week 2: Trigger Builder 리팩토링
- [ ] Trigger Builder Presenter 구현
- [ ] 조건 생성 로직 Service로 이동
- [ ] 호환성 검증 로직 분리
- [ ] 실시간 검증 기능 개선

#### Week 3: 전체 UI 통합
- [ ] 모든 Screen Presenter 패턴 적용
- [ ] 이벤트 기반 UI 갱신
- [ ] 사용자 경험 개선
- [ ] UI 테스트 자동화

#### 성공 기준
- UI 코드에 비즈니스 로직 0%
- 모든 화면이 Presenter 패턴 적용
- 이벤트 기반 반응형 UI

## 🔧 리팩토링 핵심 패턴 적용

### 1. Clean Architecture 준수
```python
# 의존성 방향: UI → Application → Domain ← Infrastructure
# 모든 의존성이 Domain을 향해 흐름

class DependencyContainer:
    """의존성 주입 컨테이너"""
    def __init__(self):
        # Infrastructure
        self.db_manager = DatabaseManager()
        self.strategy_repo = SqliteStrategyRepository(self.db_manager)
        self.event_bus = InMemoryEventBus()
        
        # Application
        self.strategy_service = StrategyApplicationService(
            self.strategy_repo, self.event_bus
        )
        
        # Presentation
        self.strategy_presenter = StrategyMakerPresenter(
            self.strategy_service
        )
```

### 2. CQRS (Command Query Responsibility Segregation)
```python
# Command (변경 작업)
class CreateStrategyCommand:
    def __init__(self, name, entry_triggers, exit_triggers):
        self.name = name
        self.entry_triggers = entry_triggers
        self.exit_triggers = exit_triggers

# Query (조회 작업)
class GetStrategyQuery:
    def __init__(self, strategy_id):
        self.strategy_id = strategy_id

class StrategyQueryService:
    """조회 전용 서비스"""
    def get_strategy(self, query: GetStrategyQuery) -> StrategyDto:
        pass
        
    def get_all_strategies(self) -> List[StrategyDto]:
        pass
```

### 3. 이벤트 기반 아키텍처
```python
# 도메인 이벤트
class StrategyCreated(DomainEvent):
    def __init__(self, strategy_id):
        super().__init__()
        self.strategy_id = strategy_id

class PositionOpened(DomainEvent):
    def __init__(self, position_id, strategy_id, market):
        super().__init__()
        self.position_id = position_id
        self.strategy_id = strategy_id
        self.market = market

# 이벤트 핸들러
class StrategyEventHandler:
    def handle_strategy_created(self, event: StrategyCreated):
        # 전략 생성 시 알림 발송
        pass
        
    def handle_position_opened(self, event: PositionOpened):
        # 포지션 모니터링 시작
        pass
```

## 📊 리팩토링 성공 지표

### 정량적 지표
- **코드 복잡도**: 현재 평균 15 → 목표 8 이하
- **테스트 커버리지**: 현재 30% → 목표 80% 이상
- **UI 비즈니스 로직**: 현재 60% → 목표 5% 이하
- **순환 의존성**: 현재 8개 → 목표 0개

### 정성적 지표
- **가독성**: 새로운 개발자가 1주 내 이해 가능
- **확장성**: 새로운 전략 추가가 2시간 내 가능
- **테스트 용이성**: 모든 비즈니스 로직 단위 테스트 가능
- **유지보수성**: 변경 사항의 영향 범위 예측 가능

## 🎯 리팩토링 위험 관리

### 높은 위험 (주의)
- **데이터 손실**: 마이그레이션 중 전략/포지션 데이터 손실
- **기능 퇴화**: 리팩토링 중 기존 기능 동작 변경
- **성능 저하**: 계층 분리로 인한 성능 오버헤드

### 위험 완화 전략
- **점진적 마이그레이션**: Big Bang 방식 지양, 단계별 적용
- **기능 테스트**: 각 단계별 회귀 테스트 필수
- **성능 모니터링**: 리팩토링 전후 성능 벤치마크
- **롤백 계획**: 각 단계별 롤백 시나리오 준비

## 💡 전문가 권장사항

### 1. 점진적 리팩토링 (Strangler Fig Pattern)
- 새로운 기능은 새 아키텍처로 구현
- 기존 기능은 점진적으로 마이그레이션
- 기존 코드와 새 코드의 공존 기간 최소화

### 2. 테스트 주도 리팩토링
- 리팩토링 전 특성화 테스트(Characterization Test) 작성
- 각 계층별 단위 테스트 필수
- 통합 테스트로 계층 간 연동 검증

### 3. 문서화 및 지식 전파
- 아키텍처 결정 기록(ADR) 작성
- 개발자 가이드 문서 업데이트
- 코드 리뷰 문화 정착

---

**다음 문서**: [현재 중요 방침 종합](04_CURRENT_POLICY_SYNTHESIS.md)
