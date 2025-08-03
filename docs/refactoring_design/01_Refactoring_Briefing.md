# 🚀 업비트 자동매매 시스템 리팩토링 계획 브리핑

## 📋 문서 개요

**작성일**: 2025년 8월 3일  
**문서 목적**: Clean Architecture 적용을 통한 대규모 시스템 리팩토링 총괄 계획서  
**대상 독자**: 프로젝트 오너, 개발팀, 아키텍트  
**실행 기준**: 본 문서의 모든 단계와 검증 방안은 즉시 실행 가능한 태스크로 변환됩니다.

---

## 🎯 리팩토링의 핵심 철학

### "정교한 매매 전략 없이는 모든 기능이 무의미하다"

이 깨달음이 프로젝트 전체 방향을 **'매매 전략 관리(Strategy Management)' 중심**으로 전환시켰습니다. 리팩토링의 모든 결정은 이 철학을 구현하는 데 최적화됩니다.

### 핵심 목표
1. **전략 중심 아키텍처**: 모든 컴포넌트가 매매 전략 실행을 위해 존재
2. **비즈니스 로직 순수성**: UI와 완전히 분리된 도메인 로직
3. **확장 가능한 구조**: 새로운 전략 추가가 2시간 내 완료
4. **신뢰할 수 있는 시스템**: 실제 자금 운용에 사용 가능한 안정성

---

## 🚨 현재 상황 진단

### 주요 문제점
- **UI 레이어 과부하**: 전체 기능의 60%가 UI에 집중
- **비즈니스 로직 분산**: 중요한 로직이 UI 컴포넌트에 혼재
- **테스트 불가능**: UI와 결합된 로직으로 인한 테스트 어려움
- **확장성 부족**: 새로운 전략 추가 시 UI 수정 필요

### 현재 강점 (유지해야 할 것들)
- **3-DB 아키텍처**: 이미 완성된 우수한 데이터 분리 구조
- **기본 7규칙 전략**: 검증 기준으로 활용할 완전한 전략 템플릿
- **컴포넌트 기반 UI**: PyQt6 기반의 모듈화된 UI 구조
- **스마트 로깅 시스템**: 개발과 디버깅에 최적화된 로깅

---

## 🏗️ 목표 아키텍처: 5-Layer Clean Architecture

```
📁 최종 목표 구조:
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
└── 📊 shared/                # 공유 계층
    ├── utils/                # 공통 유틸리티
    ├── config/               # 설정 관리
    └── exceptions/           # 예외 정의
```

### 계층별 책임 정의

#### 🎨 Presentation Layer (UI 계층)
**역할**: 순수한 표시와 사용자 입력 처리만 담당
- UI 컴포넌트 렌더링
- 사용자 이벤트 Presenter로 전달
- Presenter로부터 받은 데이터 표시

#### 🚀 Application Layer (애플리케이션 계층)
**역할**: Use Case 구현 및 외부 요청 조정
- 전략 생성, 수정, 삭제 Use Case
- 트리거 빌더 워크플로우 관리
- 백테스팅 실행 조정

#### 🧠 Domain Layer (도메인 계층)
**역할**: 핵심 비즈니스 규칙과 매매 로직
- 전략 호환성 검증
- 트리거 조건 평가
- 포지션 관리 규칙

#### 🔧 Infrastructure Layer (인프라 계층)
**역할**: 외부 시스템과의 연동
- 데이터베이스 접근
- Upbit API 통신
- 파일 시스템 관리

---

## 🚀 단계별 리팩토링 실행 계획

### Phase 1: Domain Layer 구축 (2주)
**목표**: 매매 전략의 핵심 비즈니스 로직을 순수한 도메인 모델로 구현

#### 1.1 도메인 엔티티 설계 (3일)

**구체적 작업**:
1. **전략 도메인 모델 구현**
   ```python
   # 파일: domain/entities/strategy.py
   @dataclass
   class Strategy:
       strategy_id: StrategyId
       name: str
       entry_triggers: List[Trigger]
       exit_triggers: List[Trigger]
       management_rules: List[ManagementRule]
       
       def add_trigger(self, trigger: Trigger) -> None:
           """트리거 추가 시 호환성 검증"""
           if not self._is_compatible_trigger(trigger):
               raise IncompatibleTriggerError()
   ```

2. **트리거 도메인 모델 구현**
   ```python
   # 파일: domain/entities/trigger.py
   @dataclass
   class Trigger:
       trigger_id: TriggerId
       variable: TradingVariable
       operator: ComparisonOperator
       target_value: Union[float, TradingVariable]
       
       def evaluate(self, market_data: MarketData) -> bool:
           """조건 평가 로직"""
   ```

3. **값 객체 정의**
   ```python
   # 파일: domain/value_objects/strategy_id.py
   @dataclass(frozen=True)
   class StrategyId:
       value: str
       
       def __post_init__(self):
           if not self.value or len(self.value) < 3:
               raise InvalidStrategyIdError()
   ```

**검증 방안**:
- **단위 테스트**: `test_domain_entities.py` 작성
  ```python
  def test_strategy_creation():
      # Given
      strategy_id = StrategyId("RSI_STRATEGY_001")
      rsi_trigger = create_rsi_trigger()
      
      # When
      strategy = Strategy(strategy_id, "RSI 전략", [rsi_trigger], [], [])
      
      # Then
      assert strategy.strategy_id.value == "RSI_STRATEGY_001"
      assert len(strategy.entry_triggers) == 1
  ```

- **비즈니스 규칙 테스트**: `test_strategy_business_rules.py` 작성
  ```python
  def test_incompatible_trigger_rejection():
      # Given
      strategy = create_basic_strategy()
      incompatible_trigger = create_incompatible_trigger()
      
      # When & Then
      with pytest.raises(IncompatibleTriggerError):
          strategy.add_trigger(incompatible_trigger)
  ```

#### 1.2 도메인 서비스 구현 (4일)

**구체적 작업**:
1. **전략 호환성 서비스**
   ```python
   # 파일: domain/services/strategy_compatibility_service.py
   class StrategyCompatibilityService:
       def check_trigger_compatibility(self, strategy: Strategy, trigger: Trigger) -> bool:
           """3중 카테고리 호환성 검증"""
           return self._check_comparison_group_compatibility(
               strategy.get_existing_variables(), trigger.variable
           )
   ```

2. **트리거 평가 서비스**
   ```python
   # 파일: domain/services/trigger_evaluation_service.py
   class TriggerEvaluationService:
       def evaluate_all_triggers(self, triggers: List[Trigger], 
                                market_data: MarketData) -> EvaluationResult:
           """모든 트리거 조건 평가"""
   ```

**검증 방안**:
- **호환성 검증 테스트**: 기본 7규칙 전략의 모든 조합 테스트
  ```python
  def test_7_rule_strategy_compatibility():
      # Given: 기본 7규칙 전략 구성 요소
      rsi_trigger = create_rsi_oversold_trigger()
      profit_management = create_profit_taking_rule()
      
      # When: 호환성 검증
      result = compatibility_service.check_compatibility(rsi_trigger, profit_management)
      
      # Then: 모든 조합이 호환되어야 함
      assert result.is_compatible
  ```

#### 1.3 Repository 인터페이스 정의 (3일)

**구체적 작업**:
1. **전략 Repository 추상화**
   ```python
   # 파일: domain/repositories/strategy_repository.py
   class StrategyRepository(ABC):
       @abstractmethod
       def save(self, strategy: Strategy) -> None:
           pass
           
       @abstractmethod
       def find_by_id(self, strategy_id: StrategyId) -> Optional[Strategy]:
           pass
   ```

2. **트리거 Repository 추상화**
   ```python
   # 파일: domain/repositories/trigger_repository.py
   class TriggerRepository(ABC):
       @abstractmethod
       def save_trigger(self, trigger: Trigger) -> None:
           pass
   ```

**검증 방안**:
- **인터페이스 테스트**: Mock을 사용한 Repository 동작 검증
  ```python
  def test_strategy_repository_interface():
      # Given
      mock_repo = Mock(spec=StrategyRepository)
      strategy = create_test_strategy()
      
      # When
      mock_repo.save(strategy)
      
      # Then
      mock_repo.save.assert_called_once_with(strategy)
  ```

#### 1.4 도메인 이벤트 시스템 (4일)

**구체적 작업**:
1. **도메인 이벤트 정의**
   ```python
   # 파일: domain/events/strategy_events.py
   @dataclass
   class StrategyCreated(DomainEvent):
       strategy_id: StrategyId
       created_at: datetime
       
   @dataclass
   class TriggerEvaluated(DomainEvent):
       trigger_id: TriggerId
       result: bool
       market_data_timestamp: datetime
   ```

2. **이벤트 발행 메커니즘**
   ```python
   # 파일: domain/entities/strategy.py (수정)
   class Strategy:
       def add_trigger(self, trigger: Trigger) -> None:
           # ... 비즈니스 로직 ...
           self._domain_events.append(TriggerAdded(self.strategy_id, trigger.trigger_id))
   ```

**검증 방안**:
- **이벤트 발행 테스트**:
  ```python
  def test_strategy_creation_event():
      # Given
      strategy_data = create_strategy_data()
      
      # When
      strategy = Strategy.create_new(strategy_data)
      
      # Then
      events = strategy.get_domain_events()
      assert len(events) == 1
      assert isinstance(events[0], StrategyCreated)
  ```

### **Phase 1 완료 검증 기준**

#### UI 검증 시나리오
현재 UI는 아직 연동되지 않으므로, 이 단계에서는 도메인 로직만 검증합니다.

#### 단위 테스트 검증
```bash
# 실행할 테스트 명령어
pytest tests/domain/ -v --cov=upbit_auto_trading/domain --cov-report=html

# 통과해야 할 테스트들
✅ test_strategy_creation_with_valid_data
✅ test_trigger_compatibility_validation  
✅ test_7_rule_strategy_complete_workflow
✅ test_domain_events_publishing
✅ test_repository_interface_compliance
```

#### 기능 검증 코드
```python
# 파일: tests/integration/test_phase1_integration.py
def test_phase1_complete_7_rule_strategy():
    """Phase 1 완료 후 기본 7규칙 전략이 완전히 구현되는지 검증"""
    # Given: 기본 7규칙 전략 구성 요소
    strategy_factory = StrategyFactory()
    
    # When: 7규칙 전략 생성
    strategy = strategy_factory.create_basic_7_rule_strategy()
    
    # Then: 모든 규칙이 올바르게 구성되어야 함
    assert len(strategy.entry_triggers) == 1  # RSI 과매도 진입
    assert len(strategy.exit_triggers) == 4   # 4가지 청산 규칙
    assert len(strategy.management_rules) == 2 # 불타기, 물타기
    
    # And: 모든 조합이 호환되어야 함
    compatibility_service = StrategyCompatibilityService()
    assert compatibility_service.validate_strategy(strategy)
```

---

### Phase 2: Application Layer 구축 (2주)
**목표**: Use Case 중심의 Application Service로 비즈니스 로직 조정

#### 2.1 Application Service 설계 (4일)

**구체적 작업**:
1. **전략 관리 서비스**
   ```python
   # 파일: application/services/strategy_application_service.py
   class StrategyApplicationService:
       def __init__(self, strategy_repo: StrategyRepository, 
                    compatibility_service: StrategyCompatibilityService,
                    event_bus: EventBus):
           self._strategy_repo = strategy_repo
           self._compatibility_service = compatibility_service
           self._event_bus = event_bus
       
       def create_strategy(self, command: CreateStrategyCommand) -> StrategyDto:
           """전략 생성 Use Case"""
           # 1. 입력 검증
           self._validate_create_command(command)
           
           # 2. 도메인 객체 생성
           strategy = Strategy.create_new(command.to_domain_data())
           
           # 3. 비즈니스 규칙 검증
           if not self._compatibility_service.validate_strategy(strategy):
               raise StrategyValidationError()
           
           # 4. 저장
           self._strategy_repo.save(strategy)
           
           # 5. 이벤트 발행
           self._event_bus.publish_all(strategy.get_domain_events())
           
           # 6. DTO 반환
           return StrategyDto.from_entity(strategy)
   ```

2. **트리거 관리 서비스**
   ```python
   # 파일: application/services/trigger_application_service.py
   class TriggerApplicationService:
       def create_trigger(self, command: CreateTriggerCommand) -> TriggerDto:
           """트리거 생성 Use Case"""
           
       def validate_trigger_compatibility(self, 
                                        strategy_id: str, 
                                        trigger_data: dict) -> ValidationResult:
           """실시간 호환성 검증 Use Case"""
   ```

**검증 방안**:
- **Use Case 테스트**:
  ```python
  def test_create_strategy_use_case():
      # Given
      service = StrategyApplicationService(mock_repo, mock_compatibility, mock_event_bus)
      command = CreateStrategyCommand("RSI 전략", rsi_trigger_data)
      
      # When
      result = service.create_strategy(command)
      
      # Then
      assert result.strategy_id is not None
      assert result.name == "RSI 전략"
      mock_repo.save.assert_called_once()
  ```

#### 2.2 Command/Query 패턴 구현 (3일)

**구체적 작업**:
1. **Command 객체 정의**
   ```python
   # 파일: application/commands/strategy_commands.py
   @dataclass
   class CreateStrategyCommand:
       name: str
       entry_triggers: List[Dict]
       exit_triggers: List[Dict]
       management_rules: List[Dict]
       
       def to_domain_data(self) -> StrategyCreationData:
           """도메인 생성 데이터로 변환"""
   ```

2. **Query 객체 정의**
   ```python
   # 파일: application/queries/strategy_queries.py
   @dataclass 
   class GetStrategyQuery:
       strategy_id: str
       
   @dataclass
   class SearchStrategiesQuery:
       name_pattern: Optional[str] = None
       tags: Optional[List[str]] = None
   ```

**검증 방안**:
- **Command 검증 테스트**:
  ```python
  def test_create_strategy_command_validation():
      # Given
      invalid_command = CreateStrategyCommand("", [], [], [])
      
      # When & Then
      with pytest.raises(ValidationError):
          invalid_command.validate()
  ```

#### 2.3 DTO 및 매핑 구현 (4일)

**구체적 작업**:
1. **전략 DTO 클래스**
   ```python
   # 파일: application/dto/strategy_dto.py
   @dataclass
   class StrategyDto:
       strategy_id: str
       name: str
       entry_triggers: List[TriggerDto]
       exit_triggers: List[TriggerDto]
       created_at: datetime
       
       @classmethod
       def from_entity(cls, strategy: Strategy) -> 'StrategyDto':
           """도메인 엔티티를 DTO로 변환"""
   ```

2. **트리거 DTO 클래스**
   ```python
   # 파일: application/dto/trigger_dto.py
   @dataclass
   class TriggerDto:
       trigger_id: str
       variable_name: str
       operator: str
       target_value: Union[float, str]
       
       def to_domain_entity(self) -> Trigger:
           """DTO를 도메인 엔티티로 변환"""
   ```

**검증 방안**:
- **매핑 정확성 테스트**:
  ```python
  def test_strategy_dto_mapping():
      # Given
      strategy = create_test_strategy()
      
      # When
      dto = StrategyDto.from_entity(strategy)
      reconstructed = dto.to_domain_entity()
      
      # Then
      assert reconstructed.strategy_id == strategy.strategy_id
      assert reconstructed.name == strategy.name
  ```

#### 2.4 이벤트 핸들러 구현 (3일)

**구체적 작업**:
1. **전략 이벤트 핸들러**
   ```python
   # 파일: application/event_handlers/strategy_event_handlers.py
   class StrategyEventHandler:
       def handle_strategy_created(self, event: StrategyCreated):
           """전략 생성 이벤트 처리"""
           self._send_notification(f"새 전략 생성됨: {event.strategy_id}")
           
       def handle_trigger_evaluated(self, event: TriggerEvaluated):
           """트리거 평가 이벤트 처리"""
           if event.result:
               self._log_trigger_activation(event)
   ```

**검증 방안**:
- **이벤트 핸들링 테스트**:
  ```python
  def test_strategy_created_event_handling():
      # Given
      handler = StrategyEventHandler()
      event = StrategyCreated(StrategyId("TEST_001"), datetime.now())
      
      # When
      handler.handle_strategy_created(event)
      
      # Then
      # 알림이 전송되었는지 검증
  ```

### **Phase 2 완료 검증 기준**

#### UI 검증 시나리오
이 단계에서도 아직 UI 연동은 없으므로 Application Layer 검증에 집중합니다.

#### 통합 테스트 검증
```bash
# 실행할 테스트 명령어
pytest tests/application/ -v --cov=upbit_auto_trading/application

# 통과해야 할 테스트들
✅ test_create_strategy_use_case_complete_flow
✅ test_trigger_compatibility_validation_use_case
✅ test_command_query_separation
✅ test_dto_mapping_accuracy
✅ test_event_handling_pipeline
```

#### 기능 검증 코드
```python
# 파일: tests/integration/test_phase2_integration.py
def test_phase2_complete_application_layer():
    """Phase 2 완료 후 Application Layer가 완전히 동작하는지 검증"""
    # Given: 의존성 주입 컨테이너 설정
    container = DependencyContainer()
    strategy_service = container.resolve(StrategyApplicationService)
    
    # When: 기본 7규칙 전략 생성 Use Case 실행
    command = CreateBasic7RuleStrategyCommand()
    result = strategy_service.create_strategy(command)
    
    # Then: 정확한 응답과 부수 효과 검증
    assert result.strategy_id is not None
    assert len(result.entry_triggers) == 1
    assert len(result.exit_triggers) == 4
    
    # And: 도메인 이벤트가 발행되었는지 검증
    events = mock_event_bus.published_events
    assert any(isinstance(e, StrategyCreated) for e in events)
```

---

### Phase 3: Infrastructure Layer 구현 (2주)
**목표**: Repository 패턴과 외부 시스템 연동 완성

#### 3.1 Repository 구현 (5일)

**구체적 작업**:
1. **SQLite 전략 Repository**
   ```python
   # 파일: infrastructure/repositories/sqlite_strategy_repository.py
   class SqliteStrategyRepository(StrategyRepository):
       def __init__(self, db_manager: DatabaseManager):
           self._db = db_manager
           
       def save(self, strategy: Strategy) -> None:
           """전략을 strategies.sqlite3에 저장"""
           with self._db.get_connection('strategies') as conn:
               # 전략 메인 데이터 저장
               conn.execute(
                   "INSERT INTO strategies (id, name, created_at) VALUES (?, ?, ?)",
                   (strategy.strategy_id.value, strategy.name, strategy.created_at)
               )
               
               # 트리거 데이터 저장
               for trigger in strategy.get_all_triggers():
                   conn.execute(
                       "INSERT INTO strategy_triggers (strategy_id, trigger_id, ...) VALUES (?, ?, ...)",
                       trigger.to_database_params()
                   )
   ```

2. **설정 Repository (읽기 전용)**
   ```python
   # 파일: infrastructure/repositories/settings_repository.py
   class SettingsRepository:
       def get_trading_variables(self) -> List[TradingVariable]:
           """settings.sqlite3에서 매매 변수 정의 로드"""
           
       def get_compatibility_rules(self) -> CompatibilityRules:
           """호환성 규칙 로드"""
   ```

**검증 방안**:
- **Repository 통합 테스트**:
  ```python
  def test_sqlite_strategy_repository_roundtrip():
      # Given
      repo = SqliteStrategyRepository(test_db_manager)
      strategy = create_test_strategy()
      
      # When
      repo.save(strategy)
      loaded_strategy = repo.find_by_id(strategy.strategy_id)
      
      # Then
      assert loaded_strategy is not None
      assert loaded_strategy.name == strategy.name
      assert len(loaded_strategy.entry_triggers) == len(strategy.entry_triggers)
  ```

#### 3.2 외부 API 클라이언트 (4일)

**구체적 작업**:
1. **Upbit API 클라이언트**
   ```python
   # 파일: infrastructure/external_apis/upbit_client.py
   class UpbitApiClient:
       def __init__(self, api_config: ApiConfig):
           self._config = api_config
           
       async def get_market_data(self, symbol: str, timeframe: str) -> MarketData:
           """시장 데이터 조회"""
           
       async def place_order(self, order_request: OrderRequest) -> OrderResult:
           """주문 실행"""
   ```

**검증 방안**:
- **API 클라이언트 테스트** (Mock 사용):
  ```python
  @pytest.mark.asyncio
  async def test_upbit_client_market_data():
      # Given
      mock_response = create_mock_market_data_response()
      client = UpbitApiClient(test_config)
      
      # When
      with patch('aiohttp.ClientSession.get') as mock_get:
          mock_get.return_value.__aenter__.return_value.json.return_value = mock_response
          result = await client.get_market_data("KRW-BTC", "1h")
      
      # Then
      assert result.symbol == "KRW-BTC"
      assert len(result.candles) > 0
  ```

#### 3.3 이벤트 버스 구현 (3일)

**구체적 작업**:
1. **인메모리 이벤트 버스**
   ```python
   # 파일: infrastructure/messaging/in_memory_event_bus.py
   class InMemoryEventBus(EventBus):
       def __init__(self):
           self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}
           
       def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler):
           """이벤트 핸들러 등록"""
           
       async def publish(self, event: DomainEvent):
           """이벤트 발행"""
   ```

**검증 방안**:
- **이벤트 버스 테스트**:
  ```python
  @pytest.mark.asyncio
  async def test_event_bus_publish_subscribe():
      # Given
      bus = InMemoryEventBus()
      handler = Mock()
      event = StrategyCreated(StrategyId("TEST"))
      
      # When
      bus.subscribe(StrategyCreated, handler)
      await bus.publish(event)
      
      # Then
      handler.handle.assert_called_once_with(event)
  ```

#### 3.4 설정 관리 개선 (2일)

**구체적 작업**:
1. **의존성 주입 컨테이너**
   ```python
   # 파일: infrastructure/config/dependency_container.py
   class DependencyContainer:
       def __init__(self):
           self._services = {}
           self._configure_dependencies()
           
       def resolve(self, service_type: Type[T]) -> T:
           """서비스 해결"""
   ```

### **Phase 3 완료 검증 기준**

#### 단위 테스트 검증
```bash
pytest tests/infrastructure/ -v --cov=upbit_auto_trading/infrastructure

# 통과해야 할 테스트들
✅ test_sqlite_repository_operations
✅ test_upbit_api_client_integration  
✅ test_event_bus_reliability
✅ test_dependency_injection_container
```

#### 통합 테스트 검증
```python
def test_phase3_complete_infrastructure():
    """Phase 3 완료 후 Infrastructure가 완전히 동작하는지 검증"""
    # Given: 실제 데이터베이스와 연동된 Repository
    container = DependencyContainer()
    strategy_service = container.resolve(StrategyApplicationService)
    
    # When: 전략 생성부터 저장까지 전체 플로우 실행
    command = CreateBasic7RuleStrategyCommand()
    result = strategy_service.create_strategy(command)
    
    # Then: 데이터베이스에 실제로 저장되었는지 검증
    saved_strategy = container.resolve(StrategyRepository).find_by_id(result.strategy_id)
    assert saved_strategy is not None
    
    # And: 설정 데이터가 올바르게 로드되는지 검증
    settings_repo = container.resolve(SettingsRepository)
    variables = settings_repo.get_trading_variables()
    assert len(variables) > 0
```

---

### Phase 4: Presentation Layer 리팩토링 (3주)
**목표**: MVP 패턴 적용으로 UI를 완전히 수동적(Passive)으로 만들기

#### 4.1 Presenter 구현 (1주)

**구체적 작업**:
1. **전략 메이커 Presenter**
   ```python
   # 파일: presentation/presenters/strategy_maker_presenter.py
   class StrategyMakerPresenter:
       def __init__(self, view: StrategyMakerView, 
                    strategy_service: StrategyApplicationService):
           self._view = view
           self._strategy_service = strategy_service
           self._setup_view_bindings()
           
       def on_save_strategy_clicked(self, strategy_data: dict):
           """전략 저장 버튼 클릭 처리"""
           try:
               command = CreateStrategyCommand.from_view_data(strategy_data)
               result = self._strategy_service.create_strategy(command)
               self._view.show_success_message(f"전략 '{result.name}' 저장 완료")
               self._view.clear_form()
           except ValidationError as e:
               self._view.show_validation_errors(e.errors)
           except Exception as e:
               self._view.show_error_message(f"저장 실패: {str(e)}")
   ```

2. **트리거 빌더 Presenter**
   ```python
   # 파일: presentation/presenters/trigger_builder_presenter.py
   class TriggerBuilderPresenter:
       def on_variable_selected(self, variable_name: str):
           """변수 선택 시 호환성 검증 및 UI 업데이트"""
           compatible_variables = self._trigger_service.get_compatible_variables(variable_name)
           self._view.update_variable_list(compatible_variables)
           
       def on_create_condition_clicked(self, condition_data: dict):
           """조건 생성 버튼 클릭 처리"""
           validation_result = self._trigger_service.validate_condition(condition_data)
           if validation_result.is_valid:
               self._view.add_condition_card(condition_data)
           else:
               self._view.show_validation_warnings(validation_result.warnings)
   ```

**검증 방안**:
- **Presenter 단위 테스트**:
  ```python
  def test_strategy_maker_presenter_save_success():
      # Given
      mock_view = Mock(spec=StrategyMakerView)
      mock_service = Mock(spec=StrategyApplicationService)
      presenter = StrategyMakerPresenter(mock_view, mock_service)
      
      strategy_data = {"name": "테스트 전략", "triggers": []}
      mock_service.create_strategy.return_value = StrategyDto("ID_001", "테스트 전략", [])
      
      # When
      presenter.on_save_strategy_clicked(strategy_data)
      
      # Then
      mock_view.show_success_message.assert_called_once()
      mock_view.clear_form.assert_called_once()
  ```

#### 4.2 View 리팩토링 (1주)

**구체적 작업**:
1. **Passive View로 전환**
   ```python
   # 파일: presentation/desktop/views/strategy_maker_view.py
   class StrategyMakerView(QWidget):
       def __init__(self, presenter: StrategyMakerPresenter):
           super().__init__()
           self._presenter = presenter
           self._setup_ui()
           
       def _setup_ui(self):
           """UI 구성 (표시만 담당)"""
           self._name_input = QLineEdit()
           self._save_button = QPushButton("저장")
           self._save_button.clicked.connect(self._on_save_clicked)
           
       def _on_save_clicked(self):
           """저장 버튼 클릭 시 Presenter에 위임"""
           strategy_data = self._collect_form_data()
           self._presenter.on_save_strategy_clicked(strategy_data)
           
       def show_success_message(self, message: str):
           """성공 메시지 표시 (Presenter에서 호출)"""
           QMessageBox.information(self, "성공", message)
           
       def show_validation_errors(self, errors: List[str]):
           """검증 오류 표시 (Presenter에서 호출)"""
           error_text = "\n".join(errors)
           QMessageBox.warning(self, "입력 오류", error_text)
   ```

**검증 방안**:
- **View 테스트** (PyQt6 테스트 프레임워크 사용):
  ```python
  def test_strategy_maker_view_user_interaction():
      # Given
      mock_presenter = Mock()
      view = StrategyMakerView(mock_presenter)
      
      # When
      view._name_input.setText("테스트 전략")
      QTest.mouseClick(view._save_button, Qt.LeftButton)
      
      # Then
      mock_presenter.on_save_strategy_clicked.assert_called_once()
  ```

#### 4.3 이벤트 기반 UI 갱신 (1주)

**구체적 작업**:
1. **실시간 차트 업데이트**
   ```python
   # 파일: presentation/desktop/components/mini_chart_component.py
   class MiniChartComponent(QWidget):
       def __init__(self, chart_presenter: ChartPresenter):
           super().__init__()
           self._presenter = chart_presenter
           self._presenter.data_updated.connect(self._on_data_updated)
           
       def _on_data_updated(self, chart_data: ChartData):
           """차트 데이터 업데이트 (Presenter에서 신호 발생)"""
           self._update_chart_display(chart_data)
   ```

2. **실시간 호환성 검증 UI**
   ```python
   # 파일: presentation/desktop/views/trigger_builder_view.py
   class TriggerBuilderView(QWidget):
       def _on_variable_changed(self):
           """변수 변경 시 실시간 호환성 검증"""
           selected_variable = self._variable_combo.currentText()
           self._presenter.on_variable_selected(selected_variable)
           
       def update_compatibility_status(self, is_compatible: bool, warnings: List[str]):
           """호환성 상태 UI 업데이트"""
           if is_compatible:
               self._status_label.setText("✅ 호환 가능")
               self._status_label.setStyleSheet("color: green;")
           else:
               self._status_label.setText("❌ 호환 불가")
               self._status_label.setStyleSheet("color: red;")
   ```

### **Phase 4 완료 검증 기준**

#### UI 검증 시나리오 (최종 통합 테스트)
이제 `run_desktop_ui.py`를 실행하여 전체 시스템을 검증할 수 있습니다.

**시나리오 1: 기본 7규칙 전략 생성**
```
1. `python run_desktop_ui.py` 실행
2. "전략 관리" 탭으로 이동
3. "새 전략 만들기" 버튼 클릭
4. 전략 이름: "기본 7규칙 테스트"
5. 트리거 빌더에서 다음 순서로 구성:
   - RSI(14) < 30 (진입 조건)
   - 수익률 > 5% (불타기 조건) 
   - 수익률 < -5% (물타기 조건)
   - 급락 감지 (비상 청산)
6. "저장" 버튼 클릭
7. 성공 메시지 확인: "전략 '기본 7규칙 테스트' 저장 완료"
8. 전략 목록에서 저장된 전략 확인
9. data/strategies.sqlite3 파일에 데이터 저장 확인
```

**시나리오 2: 호환성 검증**
```
1. 트리거 빌더에서 RSI 지표 선택
2. 비교 대상으로 MACD 선택 시도
3. 경고 메시지 확인: "RSI와 MACD는 호환되지 않습니다"
4. 비교 대상 선택란에서 MACD가 비활성화되어 있는지 확인
5. 호환 가능한 Stochastic 선택 시 정상 동작 확인
```

**시나리오 3: 실시간 시뮬레이션**
```
1. 생성된 전략 선택
2. "백테스팅" 버튼 클릭  
3. 시뮬레이션 진행 상황을 미니 차트에서 확인
4. 결과 리포트 생성 확인
5. 성능 지표 (수익률, 샤프비율 등) 표시 확인
```

#### 최종 통합 테스트
```python
# 파일: tests/integration/test_complete_system.py
def test_complete_7_rule_strategy_workflow():
    """전체 시스템에서 기본 7규칙 전략 워크플로우 테스트"""
    # Given: 완전히 구성된 시스템
    container = DependencyContainer()
    
    # When: UI 없이 전체 플로우 실행
    strategy_service = container.resolve(StrategyApplicationService)
    trigger_service = container.resolve(TriggerApplicationService)
    backtest_service = container.resolve(BacktestApplicationService)
    
    # 1. 전략 생성
    strategy_result = strategy_service.create_strategy(CreateBasic7RuleStrategyCommand())
    
    # 2. 백테스팅 실행
    backtest_result = backtest_service.run_backtest(
        strategy_result.strategy_id, 
        "KRW-BTC", 
        "2024-01-01", 
        "2024-12-31"
    )
    
    # Then: 모든 단계가 정상 동작
    assert strategy_result.strategy_id is not None
    assert backtest_result.total_return is not None
    assert backtest_result.max_drawdown is not None
    assert backtest_result.sharpe_ratio is not None
    
    # And: 7규칙이 모두 실행되었는지 검증
    execution_logs = backtest_result.execution_logs
    assert any("RSI 과매도 진입" in log.action for log in execution_logs)
    assert any("불타기" in log.action for log in execution_logs)
    assert any("물타기" in log.action for log in execution_logs)
```

#### 성능 검증
```bash
# 백테스팅 성능 테스트
pytest tests/performance/test_backtest_performance.py

# 확인해야 할 성능 지표
✅ 1년 분봉 데이터 백테스팅: 5분 내 완료
✅ UI 응답성: 모든 버튼 클릭 100ms 내 반응
✅ 메모리 사용량: 2GB 이하 유지
✅ 전략 저장: 1초 내 완료
```

---

## 🎯 리팩토링 성공 지표

### 정량적 지표
- **코드 복잡도**: 현재 평균 15 → 목표 8 이하
- **테스트 커버리지**: 현재 30% → 목표 80% 이상  
- **UI 비즈니스 로직**: 현재 60% → 목표 5% 이하
- **순환 의존성**: 현재 8개 → 목표 0개
- **백테스팅 성능**: 1년 분봉 데이터 5분 내 처리 유지

### 정성적 지표
- **가독성**: 새로운 개발자가 1주 내 코드 구조 이해 가능
- **확장성**: 새로운 전략 추가가 2시간 내 완료 가능
- **테스트 용이성**: 모든 비즈니스 로직이 단위 테스트 가능
- **유지보수성**: 변경 사항의 영향 범위가 명확히 예측 가능

---

## 🚨 위험 관리 및 롤백 계획

### 주요 위험 요소
1. **데이터 손실**: 마이그레이션 중 전략/포지션 데이터 손실
2. **기능 퇴화**: 리팩토링으로 인한 기존 기능 동작 변경
3. **성능 저하**: 계층 분리로 인한 오버헤드
4. **개발 지연**: 예상보다 복잡한 의존성 해결

### 위험 완화 전략
1. **점진적 마이그레이션**: 
   - Big Bang 방식 지양
   - 각 Phase별 독립적 검증
   - 기존 코드와 새 코드 공존 기간 최소화

2. **데이터 백업**:
   ```bash
   # 각 Phase 시작 전 필수 백업
   cp data/strategies.sqlite3 data/backups/strategies_phase1_backup.sqlite3
   cp data/settings.sqlite3 data/backups/settings_phase1_backup.sqlite3
   ```

3. **성능 모니터링**:
   - 각 Phase 완료 후 성능 벤치마크 실행
   - 성능 저하 10% 초과 시 최적화 작업 추가

4. **롤백 시나리오**:
   ```bash
   # Phase 실패 시 롤백 스크립트
   git checkout phase_backup_branch
   cp data/backups/* data/
   python scripts/verify_rollback.py
   ```

---

## 📚 팀 준비사항

### 필수 학습 자료
1. **Clean Architecture**: Uncle Bob의 Clean Architecture 개념
2. **MVP 패턴**: PyQt6에서의 MVP 패턴 구현
3. **Repository 패턴**: 데이터 접근 추상화
4. **Domain Driven Design**: 도메인 모델링 기법

### 개발 환경 설정
```bash
# 필수 도구 설치
pip install pytest pytest-cov pytest-mock
pip install mypy black isort
pip install sqlalchemy alembic  # 마이그레이션용

# 테스트 데이터베이스 설정
python scripts/setup_test_databases.py
```

### 코드 리뷰 체크리스트
- [ ] 모든 비즈니스 로직이 Domain Layer에 위치
- [ ] UI 컴포넌트에 비즈니스 로직 없음
- [ ] Repository 인터페이스를 통한 데이터 접근
- [ ] 단위 테스트 커버리지 80% 이상
- [ ] 순환 의존성 없음

---

## 🎉 리팩토링 완료 후 기대 효과

### 개발 생산성 향상
- **새 전략 개발**: 2시간 내 완료 (기존 1-2일)
- **버그 수정**: 영향 범위 명확화로 50% 시간 단축
- **테스트 작성**: 모든 로직이 테스트 가능해져 품질 향상

### 시스템 안정성 확보
- **실제 자금 운용 가능**: 충분한 테스트와 검증으로 신뢰성 확보
- **확장성**: 향후 새로운 거래소 추가 용이
- **유지보수성**: 코드 변경 시 예측 가능한 영향 범위

### 사용자 경험 개선
- **빠른 응답성**: UI와 비즈니스 로직 분리로 성능 최적화
- **직관적 인터페이스**: 명확한 책임 분리로 일관된 UX
- **안정적 동작**: 예외 상황 처리 개선으로 크래시 최소화

---

**💡 핵심 메시지**: "단계별 점진적 리팩토링을 통해 안전하고 확실한 아키텍처 개선을 달성한다!"

**🎯 최종 목표**: 실제 자금 운용이 가능한 수준의 안정적이고 확장 가능한 자동매매 시스템 완성

---

## 📞 다음 단계 Action Items

### 즉시 시작 (이번 주)
1. **팀 브리핑**: 본 문서 내용 전체 팀 검토
2. **개발 환경 준비**: 필수 도구 설치 및 테스트 DB 구성
3. **Phase 1 상세 계획**: Domain Layer 구축 태스크 세분화

### 1주 내 완료
1. **태스크 생성**: GitHub Issues로 각 Phase별 상세 태스크 생성
2. **담당자 배정**: 각 개발자별 역할과 책임 할당
3. **마일스톤 설정**: 각 Phase별 완료 기준과 일정 확정

### 지속적 모니터링
1. **주간 리뷰**: 매주 진행 상황과 이슈 점검
2. **품질 체크**: 코드 리뷰와 테스트 커버리지 모니터링
3. **성능 벤치마크**: 각 Phase별 성능 지표 측정 및 기록
