# 🔧 Application Layer 도메인 이벤트 통합 - 문제해결 가이드

> **대상**: 실무에서 막힌 개발자
> **목적**: 자주 발생하는 문제의 빠른 해결책 제공
> **사용법**: 문제 증상으로 검색 후 해결책 적용

## 🚨 긴급 문제 해결 (Quick Fix)

### 문제 1: 테스트 실행 시 AttributeError
```bash
# 증상
AttributeError: 'Mock' object has no attribute 'strategy_id'

# 원인
Mock 객체에 필요한 속성이 설정되지 않음

# 해결책 (2분)
mock_strategy = Mock(spec=Strategy)
mock_strategy.strategy_id = Mock()
mock_strategy.strategy_id.value = "test-id"
mock_strategy.name = "Test Strategy"
# 모든 사용될 속성 추가 설정
```

### 문제 2: Pylance 타입 오류 대량 발생
```bash
# 증상
42개의 "매개 변수에 대한 인수가 없습니다" 오류

# 원인
도메인 이벤트 생성자 매개변수 불일치

# 해결책 (10분)
1. 이벤트 클래스 생성자 확인
2. strategy_id.value로 변경
3. updated_fields 딕셔너리 구조 사용
```

### 문제 3: Import 순환 참조 오류
```bash
# 증상
ImportError: cannot import name 'Strategy' from partially initialized module

# 원인
Application과 Domain 계층 간 순환 참조

# 해결책 (5분)
# 지연 import 사용
def method_with_domain_dependency(self):
    from ...domain.entities.strategy import Strategy
    # 메서드 내에서만 import
```

## 🔍 문제별 상세 해결책

### 🧪 테스트 관련 문제

#### 문제 A: Mock 객체 설정 불완전
```python
# ❌ 문제 코드
mock_strategy = Mock()
self.mock_repository.save.return_value = mock_strategy
result = self.service.create_strategy(command)  # AttributeError!

# ✅ 해결 코드
def create_complete_mock_strategy(self):
    mock_strategy = Mock(spec=Strategy)

    # 모든 속성 명시적 설정
    mock_strategy.strategy_id = Mock()
    mock_strategy.strategy_id.value = "test-strategy-001"
    mock_strategy.name = "테스트 전략"
    mock_strategy.description = "테스트용"
    mock_strategy.created_by = "test_user"
    mock_strategy.tags = ["test"]
    mock_strategy.status = "ACTIVE"
    mock_strategy.entry_triggers = []
    mock_strategy.exit_triggers = []

    # 메서드 반환값 설정
    mock_strategy.get_domain_events.return_value = []
    mock_strategy.clear_domain_events.return_value = None

    return mock_strategy
```

#### 문제 B: patch 사용 오류
```python
# ❌ 문제 코드
@patch('strategy_id.StrategyId.generate_default')  # 잘못된 경로
def test_create_strategy(self, mock_generate):
    pass

# ✅ 해결 코드
@patch('upbit_auto_trading.domain.value_objects.strategy_id.StrategyId.generate_default')
def test_create_strategy(self, mock_generate):
    mock_strategy_id = Mock()
    mock_strategy_id.value = "generated-id"
    mock_generate.return_value = mock_strategy_id
    # 테스트 로직
```

#### 문제 C: pytest fixture 충돌
```python
# ❌ 문제 코드
def setup_method(self):
    self.service = StrategyApplicationService()  # 의존성 없음

# ✅ 해결 코드
def setup_method(self):
    # Mock 의존성 생성
    self.mock_repository = Mock()
    self.mock_event_publisher = Mock()

    # 서비스 인스턴스 생성
    self.service = StrategyApplicationService(
        strategy_repository=self.mock_repository,
        domain_event_publisher=self.mock_event_publisher
    )
```

### 🎭 도메인 이벤트 관련 문제

#### 문제 D: 매개변수 이름 불일치
```python
# ❌ 문제 코드
StrategyUpdated(
    strategy_id=self.strategy_id,
    modification_type="renamed",      # 존재하지 않는 매개변수
    old_value=old_name,              # 존재하지 않는 매개변수
    new_value=new_name               # 존재하지 않는 매개변수
)

# ✅ 해결 코드
StrategyUpdated(
    strategy_id=self.strategy_id.value,
    strategy_name=new_name,
    updated_fields={
        "strategy_renamed": {
            "old_name": old_name,
            "new_name": new_name
        }
    }
)
```

#### 문제 E: Value Object 타입 오류
```python
# ❌ 문제 코드
event = StrategyCreated(strategy_id=self.strategy_id)  # StrategyId 객체

# ✅ 해결 코드
event = StrategyCreated(strategy_id=self.strategy_id.value)  # str 타입
```

#### 문제 F: 도메인 이벤트 발행 누락
```python
# ❌ 문제 코드
def create_strategy(self, command):
    strategy = Strategy.create_new(...)
    saved_strategy = self._repository.save(strategy)
    return StrategyDto.from_entity(saved_strategy)  # 이벤트 발행 누락!

# ✅ 해결 코드
def create_strategy(self, command):
    strategy = Strategy.create_new(...)
    saved_strategy = self._repository.save(strategy)

    # 도메인 이벤트 발행
    domain_events = saved_strategy.get_domain_events()
    for event in domain_events:
        self._domain_event_publisher.publish(event)
    saved_strategy.clear_domain_events()

    return StrategyDto.from_entity(saved_strategy)
```

### 🏗️ 아키텍처 관련 문제

#### 문제 G: 계층 의존성 위반
```python
# ❌ 문제 코드 (Presentation에서 Domain 직접 접근)
class StrategyWidget:
    def save_strategy(self):
        strategy = Strategy.create_new(...)  # 계층 위반!

# ✅ 해결 코드 (Application Service 사용)
class StrategyWidget:
    def __init__(self, app_service: StrategyApplicationService):
        self._app_service = app_service

    def save_strategy(self):
        command = CreateStrategyCommand(...)
        result = self._app_service.create_strategy(command)
```

#### 문제 H: DI Container 설정 오류
```python
# ❌ 문제 코드
container = DependencyContainer()
service = container.get(StrategyApplicationService)  # 등록 안됨!

# ✅ 해결 코드
container = DependencyContainer()
# 의존성 등록
container.register(IStrategyRepository, SqliteStrategyRepository)
container.register(IDomainEventPublisher, InMemoryEventPublisher)
container.register(StrategyApplicationService, StrategyApplicationService)

# 서비스 해결
service = container.get(StrategyApplicationService)
```

## 🛠️ 디버깅 도구와 기법

### 1. Pylance 오류 분석
```bash
# VS Code에서 Problems 패널 열기
Ctrl + Shift + M

# 오류 메시지 해석
"매개 변수 'strategy_name'에 대한 인수가 없습니다"
→ strategy_name 매개변수가 필요함

"형식 'StrategyId'을 'str'에 할당할 수 없습니다"
→ .value 속성 사용하여 문자열 변환 필요
```

### 2. 테스트 디버깅
```python
# pytest 상세 출력
python -m pytest tests/application/ -v -s

# 특정 테스트만 실행
python -m pytest tests/application/services/test_strategy_application_service.py::TestStrategyApplicationService::test_create_strategy_success -v

# 실패 시 즉시 중단
python -m pytest tests/application/ -x
```

### 3. Mock 객체 검증
```python
# Mock 호출 확인
assert self.mock_repository.save.called
assert self.mock_repository.save.call_count == 1

# Mock 호출 인자 확인
args, kwargs = self.mock_repository.save.call_args
assert isinstance(args[0], Strategy)

# Mock 설정 확인
print(mock_strategy.__dict__)  # 설정된 속성 확인
```

## 🚨 응급처치 스크립트

### 스크립트 1: Mock 속성 자동 생성
```python
def auto_configure_mock_strategy():
    """Mock Strategy 객체 자동 설정"""
    mock_strategy = Mock(spec=Strategy)

    # 기본 속성들
    attributes = [
        'strategy_id', 'name', 'description', 'created_by',
        'tags', 'status', 'entry_triggers', 'exit_triggers'
    ]

    for attr in attributes:
        if attr == 'strategy_id':
            mock_id = Mock()
            mock_id.value = f"test-{attr}"
            setattr(mock_strategy, attr, mock_id)
        elif attr in ['entry_triggers', 'exit_triggers', 'tags']:
            setattr(mock_strategy, attr, [])
        else:
            setattr(mock_strategy, attr, f"test_{attr}")

    # 메서드 설정
    mock_strategy.get_domain_events.return_value = []
    mock_strategy.clear_domain_events.return_value = None

    return mock_strategy
```

### 스크립트 2: 도메인 이벤트 매개변수 검증
```python
def validate_domain_event_parameters():
    """도메인 이벤트 매개변수 검증"""
    from upbit_auto_trading.domain.events.strategy_events import StrategyCreated, StrategyUpdated

    # StrategyCreated 매개변수 확인
    import inspect
    created_sig = inspect.signature(StrategyCreated.__init__)
    print("StrategyCreated 매개변수:", list(created_sig.parameters.keys()))

    # StrategyUpdated 매개변수 확인
    updated_sig = inspect.signature(StrategyUpdated.__init__)
    print("StrategyUpdated 매개변수:", list(updated_sig.parameters.keys()))
```

### 스크립트 3: 전체 오류 검사
```python
def check_all_errors():
    """프로젝트 전체 오류 검사"""
    import subprocess

    # pytest 실행
    test_result = subprocess.run(['python', '-m', 'pytest', 'tests/application/', '-v'],
                                capture_output=True, text=True)
    print("테스트 결과:")
    print(test_result.stdout)

    # mypy 타입 검사 (선택사항)
    mypy_result = subprocess.run(['mypy', 'upbit_auto_trading/'],
                                capture_output=True, text=True)
    print("타입 검사 결과:")
    print(mypy_result.stdout)
```

## 📋 문제해결 체크리스트

### 테스트 문제 해결 순서
```markdown
□ 1. Mock 객체 모든 속성 설정 확인
□ 2. patch 데코레이터 경로 정확성 확인
□ 3. 테스트 메서드 이름 test_ 접두사 확인
□ 4. assertion 구문 정확성 확인
□ 5. pytest 실행 명령어 정확성 확인
```

### 도메인 이벤트 문제 해결 순서
```markdown
□ 1. 이벤트 클래스 생성자 매개변수 확인
□ 2. strategy_id.value 문자열 변환 적용
□ 3. updated_fields 딕셔너리 구조 사용
□ 4. 선택적 매개변수 None 허용 확인
□ 5. Pylance Problems 패널 오류 0개 확인
```

### 아키텍처 문제 해결 순서
```markdown
□ 1. 계층 간 의존성 방향 올바른지 확인
□ 2. DI Container 의존성 등록 완료 확인
□ 3. 인터페이스를 통한 추상화 사용 확인
□ 4. 순환 참조 발생하지 않는지 확인
□ 5. Application Service 책임 범위 적절한지 확인
```

## 🎯 예방법과 모범 사례

### 1. 테스트 우선 개발
```python
# 구현하기 전에 테스트부터 작성
def test_create_strategy_success(self):
    # Given
    command = CreateStrategyCommand(name="테스트")

    # When
    result = self.service.create_strategy(command)

    # Then
    assert result is not None
    # 이 시점에서 구현 시작
```

### 2. 점진적 Mock 설정
```python
# 기본 Mock부터 시작해서 점진적으로 확장
mock_strategy = Mock(spec=Strategy)
# 테스트 실행 후 AttributeError 발생 시
mock_strategy.strategy_id = Mock()
# 또 다른 오류 발생 시
mock_strategy.strategy_id.value = "test-id"
# 반복하여 완전한 Mock 완성
```

### 3. 타입 힌트 활용
```python
# 모든 메서드에 명확한 타입 힌트
def create_strategy(self, command: CreateStrategyCommand) -> StrategyDto:
    # IDE가 타입 검사를 자동으로 수행
    pass
```

---

**🚨 긴급상황**: "모든 테스트가 실패한다면 Mock 설정부터 다시 확인하세요!"

**💡 예방의 핵심**: "타입 힌트를 활용하면 대부분의 문제를 컴파일 타임에 발견할 수 있습니다!"

**🎯 문제해결 원칙**: "작은 단위로 나누어 해결하고, 각 단계마다 검증하세요!"
