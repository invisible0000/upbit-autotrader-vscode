# 🛠️ Application Layer 도메인 이벤트 통합 - 구현 가이드

> **대상**: 주니어 개발자, DDD 입문자
> **목적**: Step-by-step 구현 방법과 Best Practice 제공
> **전제조건**: Python 3.8+, pytest, 기본적인 OOP 지식

## 🎯 구현 목표

### 최종 결과물
- **Application Service**: Use Case 중심의 비즈니스 로직 구현
- **Mock 기반 테스트**: 완전히 격리된 단위 테스트
- **도메인 이벤트 통합**: 타입 안전한 이벤트 시스템
- **타입 안전성**: Pylance 정적 분석 통과

## 📁 폴더 구조

```
upbit_auto_trading/
├── application/
│   ├── services/
│   │   └── strategy_application_service.py  # 핵심 구현
│   ├── commands/
│   │   └── strategy_commands.py             # Command 패턴
│   ├── dto/
│   │   └── strategy_dto.py                  # Data Transfer Object
│   └── interfaces/
│       └── dependency_container.py          # DI Container
├── domain/
│   ├── entities/
│   │   └── strategy.py                      # 도메인 엔티티 (수정 대상)
│   └── events/
│       └── strategy_events.py               # 도메인 이벤트
└── tests/
    └── application/
        └── services/
            └── test_strategy_application_service.py  # 단위 테스트
```

## 🔧 Step 1: Application Service 구현

### 1.1 기본 클래스 구조
```python
# application/services/strategy_application_service.py
from typing import List, Optional
from ..commands.strategy_commands import CreateStrategyCommand, UpdateStrategyCommand
from ..dto.strategy_dto import StrategyDto
from ...domain.entities.strategy import Strategy
from ...domain.value_objects.strategy_id import StrategyId

class StrategyApplicationService:
    """전략 관리 Application Service - Use Case 구현"""

    def __init__(self, strategy_repository, domain_event_publisher):
        self._strategy_repository = strategy_repository
        self._domain_event_publisher = domain_event_publisher
```

### 1.2 Use Case 메서드 구현 패턴
```python
def create_strategy(self, command: CreateStrategyCommand) -> StrategyDto:
    """전략 생성 Use Case"""

    # 1. 입력 검증
    if not command.name or not command.name.strip():
        raise ValueError("전략 이름은 필수입니다")

    # 2. 도메인 객체 생성
    strategy_id = StrategyId.generate_default()
    strategy = Strategy.create_new(
        strategy_id=strategy_id,
        name=command.name,
        description=command.description,
        created_by=command.created_by
    )

    # 3. 비즈니스 규칙 검증
    # (필요시 도메인 서비스 호출)

    # 4. Repository에 저장
    saved_strategy = self._strategy_repository.save(strategy)

    # 5. 도메인 이벤트 발행
    domain_events = saved_strategy.get_domain_events()
    for event in domain_events:
        self._domain_event_publisher.publish(event)
    saved_strategy.clear_domain_events()

    # 6. DTO로 변환하여 반환
    return StrategyDto.from_entity(saved_strategy)
```

### 1.3 핵심 패턴 요약
```python
# Application Service의 책임
# 1. 입력 검증 (Command 객체 검증)
# 2. 도메인 객체 조율 (Orchestration)
# 3. Repository 호출 (영속성)
# 4. 도메인 이벤트 발행 (Event Publishing)
# 5. DTO 변환 (Presentation Layer 호환)
```

## 🧪 Step 2: Mock 기반 단위 테스트

### 2.1 테스트 클래스 기본 구조
```python
# tests/application/services/test_strategy_application_service.py
import pytest
from unittest.mock import Mock, patch
from upbit_auto_trading.application.services.strategy_application_service import StrategyApplicationService
from upbit_auto_trading.application.commands.strategy_commands import CreateStrategyCommand

class TestStrategyApplicationService:
    """StrategyApplicationService 단위 테스트"""

    def setup_method(self):
        """각 테스트 전에 실행되는 설정"""
        # Mock Repository 생성
        self.mock_repository = Mock()
        self.mock_event_publisher = Mock()

        # 테스트 대상 서비스 생성
        self.service = StrategyApplicationService(
            strategy_repository=self.mock_repository,
            domain_event_publisher=self.mock_event_publisher
        )
```

### 2.2 Mock 객체 완전 설정 패턴
```python
def create_mock_strategy(self):
    """완전히 설정된 Mock Strategy 객체 생성"""
    mock_strategy = Mock(spec=Strategy)

    # 🔥 핵심: 모든 사용될 속성을 명시적으로 설정
    mock_strategy.strategy_id = Mock()
    mock_strategy.strategy_id.value = "test-strategy-001"
    mock_strategy.name = "테스트 전략"
    mock_strategy.description = "테스트용 전략"
    mock_strategy.created_by = "test_user"
    mock_strategy.tags = ["test", "sample"]
    mock_strategy.status = "ACTIVE"

    # 📝 중요: 컬렉션 속성들도 설정
    mock_strategy.entry_triggers = []
    mock_strategy.exit_triggers = []

    # 🎯 핵심: 메서드 반환값 설정
    mock_strategy.get_domain_events.return_value = []
    mock_strategy.clear_domain_events.return_value = None

    return mock_strategy
```

### 2.3 테스트 메서드 작성 패턴
```python
def test_create_strategy_success(self):
    """전략 생성 성공 테스트"""

    # Arrange (준비)
    command = CreateStrategyCommand(
        name="새로운 전략",
        description="테스트 전략입니다",
        created_by="test_user"
    )

    mock_strategy = self.create_mock_strategy()
    self.mock_repository.save.return_value = mock_strategy

    # Act (실행)
    with patch('upbit_auto_trading.domain.value_objects.strategy_id.StrategyId.generate_default') as mock_generate:
        mock_strategy_id = Mock()
        mock_strategy_id.value = "generated-id-001"
        mock_generate.return_value = mock_strategy_id

        result = self.service.create_strategy(command)

    # Assert (검증)
    assert result is not None
    assert result.name == "테스트 전략"
    self.mock_repository.save.assert_called_once()
    mock_strategy.get_domain_events.assert_called_once()
    mock_strategy.clear_domain_events.assert_called_once()
```

## 🎭 Step 3: 도메인 이벤트 오류 해결

### 3.1 오류 진단 방법
```bash
# Pylance 오류 확인
1. VS Code에서 Problems 패널 열기 (Ctrl+Shift+M)
2. 해당 파일의 오류 목록 확인
3. 각 오류의 원인 분석

# 일반적인 오류 패턴
- "매개 변수 'parameter_name'에 대한 인수가 없습니다"
- "이름이 'old_parameter'인 매개 변수가 없습니다"
- "형식 'Type1'을 'Type2'에 할당할 수 없습니다"
```

### 3.2 도메인 이벤트 생성자 분석
```python
# 🔍 단계 1: 이벤트 클래스 생성자 확인
# domain/events/strategy_events.py 파일 열기

class StrategyCreated(DomainEvent):
    def __init__(self, strategy_id: str, strategy_name: str,
                 strategy_type: str, created_by: Optional[str] = None,
                 strategy_config: Optional[Dict] = None):
        # 실제 매개변수 확인

class StrategyUpdated(DomainEvent):
    def __init__(self, strategy_id: str, strategy_name: str,
                 updated_fields: Dict[str, Any],
                 previous_version: Optional[str] = None):
        # 새로운 매개변수 구조 확인
```

### 3.3 수정 패턴
```python
# ❌ 수정 전: 잘못된 매개변수
StrategyUpdated(
    strategy_id=self.strategy_id,           # StrategyId 객체
    modification_type="strategy_renamed",   # 존재하지 않는 매개변수
    old_value=old_name,                     # 존재하지 않는 매개변수
    new_value=name                          # 존재하지 않는 매개변수
)

# ✅ 수정 후: 올바른 매개변수
StrategyUpdated(
    strategy_id=self.strategy_id.value,     # 문자열로 변환
    strategy_name=name,                     # 새로운 이름
    updated_fields={                        # 딕셔너리 구조
        "strategy_renamed": {
            "old_name": old_name,
            "new_name": name
        }
    }
)
```

### 3.4 일관된 수정 접근법
```python
# 수정 작업 체크리스트
□ 1. 이벤트 클래스 생성자 매개변수 확인
□ 2. strategy_id.value로 문자열 변환
□ 3. updated_fields 딕셔너리 구조 사용
□ 4. 불필요한 매개변수 제거
□ 5. Pylance 오류 재확인
```

## 🔧 Step 4: 타입 안전성 확보

### 4.1 Value Object 올바른 사용법
```python
# ❌ 잘못된 사용: 객체를 문자열이 필요한 곳에 직접 사용
strategy_id = StrategyId("test-id")
event = StrategyCreated(strategy_id=strategy_id)  # 타입 오류!

# ✅ 올바른 사용: .value 속성으로 문자열 추출
strategy_id = StrategyId("test-id")
event = StrategyCreated(strategy_id=strategy_id.value)  # 타입 안전!
```

### 4.2 Optional 매개변수 처리
```python
# ✅ 선택적 매개변수는 명시적으로 처리
StrategyCreated(
    strategy_id=self.strategy_id.value,
    strategy_name=self.name,
    strategy_type="entry",
    created_by=self.created_by,        # Optional[str] - None 가능
    strategy_config={                  # Optional[Dict] - 딕셔너리 제공
        "entry_strategy": self.entry_strategy_config.config_id if self.entry_strategy_config else None
    }
)
```

### 4.3 타입 힌트 활용
```python
# 모든 메서드에 타입 힌트 추가
def create_strategy(self, command: CreateStrategyCommand) -> StrategyDto:
    """명확한 타입 정보로 IDE 지원 향상"""
    pass

def update_metadata(self, name: Optional[str] = None,
                   description: Optional[str] = None) -> None:
    """Optional 타입으로 선택적 매개변수 명시"""
    pass
```

## 🧪 Step 5: 테스트 실행 및 검증

### 5.1 테스트 실행 명령어
```bash
# 특정 테스트 파일 실행
python -m pytest tests/application/services/test_strategy_application_service.py -v

# 모든 Application 테스트 실행
python -m pytest tests/application/ -v

# 커버리지와 함께 실행
python -m pytest tests/application/ --cov=upbit_auto_trading.application --cov-report=html
```

### 5.2 테스트 성공 기준
```bash
# 예상 출력
tests/application/services/test_strategy_application_service.py::TestStrategyApplicationService::test_create_strategy_success PASSED
tests/application/services/test_strategy_application_service.py::TestStrategyApplicationService::test_get_strategy_by_id_success PASSED
...
======================= 9 passed in 0.15s =======================
```

### 5.3 오류 해결 체크리스트
```markdown
□ 모든 테스트 통과 (pytest)
□ Pylance 오류 0개 (VS Code Problems 패널)
□ 타입 힌트 누락 없음
□ Mock 객체 완전 설정
□ 도메인 이벤트 발행 검증
```

## 📚 Best Practices

### 1. 점진적 개발
```python
# 한 번에 하나씩 구현하고 테스트
1. Application Service 메서드 1개 구현
2. 해당 메서드 테스트 작성
3. 테스트 통과 확인
4. 다음 메서드로 진행
```

### 2. Mock 설정 완전성
```python
# Mock 객체는 과하게 설정하는 것이 부족한 것보다 낫다
mock_strategy.every_possible_attribute = "default_value"
mock_strategy.every_method.return_value = expected_return
```

### 3. 오류 메시지 활용
```python
# Pylance 오류 메시지에서 정확한 정보 추출
# "매개 변수 'strategy_name'에 대한 인수가 없습니다"
# → strategy_name 매개변수가 필요함을 의미
```

## 🎯 완료 확인 방법

### 최종 검증 체크리스트
```bash
# 1. 테스트 실행
python -m pytest tests/application/services/test_strategy_application_service.py -v
# 결과: 9 passed

# 2. 타입 검사
# VS Code에서 Problems 패널 확인
# 결과: 0 errors

# 3. 실제 동작 확인
python run_desktop_ui.py
# 결과: 애플리케이션 정상 실행
```

---

**💡 성공의 핵심**: "각 단계마다 검증하고, Mock 설정은 완전하게, 타입 오류는 즉시 해결하세요!"

**🚨 주의사항**: "Mock 객체의 불완전한 설정이 가장 흔한 실수입니다. 모든 사용될 속성을 명시적으로 설정하세요."
