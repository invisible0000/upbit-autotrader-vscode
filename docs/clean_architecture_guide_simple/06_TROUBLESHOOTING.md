# 🔧 Clean Architecture 문제 해결 가이드

> **목적**: Clean Architecture 적용 시 자주 발생하는 문제와 해결법  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 🚨 자주 발생하는 문제들

### 1. 계층 경계 위반 문제

#### ❌ 문제: UI에서 직접 Repository 호출
```python
# 잘못된 예시
class StrategyView(QWidget):
    def save_strategy(self):
        # ❌ View에서 직접 DB 접근
        repo = SqliteStrategyRepository()
        repo.save(self.strategy)
```

#### ✅ 해결: Presenter 패턴 적용
```python
# 올바른 해결책
class StrategyView(QWidget):
    def save_strategy(self):
        # ✅ Presenter에 위임
        self.presenter.save_strategy()

class StrategyPresenter:
    def save_strategy(self):
        # ✅ Service 호출
        self.strategy_service.save_strategy(self.current_strategy)
```

### 2. Domain에서 외부 의존성 참조

#### ❌ 문제: Domain에서 외부 라이브러리 사용
```python
# 잘못된 예시
class Strategy:
    def send_notification(self):
        # ❌ Domain에서 외부 서비스 직접 호출
        import smtplib
        smtp = smtplib.SMTP('smtp.gmail.com')
        smtp.send_email(...)
```

#### ✅ 해결: Domain Event 패턴
```python
# 올바른 해결책
class Strategy:
    def activate(self):
        # ✅ Domain Event 발행
        self.add_event(StrategyActivated(self.id))

# Infrastructure에서 처리
class StrategyEventHandler:
    def handle(self, event: StrategyActivated):
        # ✅ 여기서 외부 서비스 호출
        self.notification_service.send_notification(...)
```

### 3. 순환 의존성 문제

#### ❌ 문제: 계층 간 순환 참조
```python
# 잘못된 예시
class StrategyService:
    def __init__(self, view):
        self.view = view  # ❌ Service가 View 참조

class StrategyView:
    def __init__(self, service):
        self.service = service  # ❌ View가 Service 참조
```

#### ✅ 해결: 의존성 역전 원칙
```python
# 올바른 해결책
class StrategyService:
    def __init__(self, event_publisher):
        self.event_publisher = event_publisher  # ✅ 인터페이스 의존

class StrategyPresenter:
    def __init__(self, view, service):
        self.view = view      # ✅ 단방향 의존
        self.service = service  # ✅ 단방향 의존
```

## 🔍 계층별 문제 진단법

### 🎨 Presentation Layer 문제

#### 증상 체크리스트
- [ ] View 클래스가 500줄 이상
- [ ] View에서 계산 로직 수행
- [ ] View에서 직접 DB/API 호출
- [ ] View에서 복잡한 비즈니스 규칙 적용

#### 해결 방법
```python
# ❌ 문제가 있는 View
class ComplexView(QWidget):
    def save_data(self):
        # ❌ 복잡한 로직이 View에 있음
        if self.calculate_profit() > 0.1:
            self.update_database()
            self.send_notification()

# ✅ 개선된 View
class SimpleView(QWidget):
    def save_data(self):
        # ✅ Presenter에 위임
        data = self.collect_form_data()
        self.presenter.save_data(data)
```

### ⚙️ Application Layer 문제

#### 증상 체크리스트
- [ ] Service에서 UI 조작
- [ ] Service가 Domain 규칙 정의
- [ ] Service에서 직접 DB 스키마 참조
- [ ] 하나의 Service가 너무 많은 책임

#### 해결 방법
```python
# ❌ 문제가 있는 Service
class OverloadedService:
    def create_strategy(self, data):
        # ❌ UI 조작
        self.view.show_loading()
        
        # ❌ Domain 규칙 정의
        if len(data.rules) > 5:
            raise TooManyRulesError()

# ✅ 개선된 Service
class FocusedService:
    def create_strategy(self, command):
        # ✅ Domain에 규칙 검증 위임
        strategy = Strategy.create(command.name, command.rules)
        
        # ✅ Repository에 저장 위임
        self.strategy_repo.save(strategy)
        
        # ✅ 이벤트 발행
        self.event_publisher.publish(StrategyCreated(strategy.id))
```

### 💎 Domain Layer 문제

#### 증상 체크리스트
- [ ] Domain 객체에 Infrastructure 참조
- [ ] Domain에서 외부 API 호출
- [ ] Domain 객체가 너무 단순함 (Anemic Model)
- [ ] 비즈니스 규칙이 Service에 흩어져 있음

#### 해결 방법
```python
# ❌ Anemic Domain Model
class Strategy:
    def __init__(self, name, rules):
        self.name = name
        self.rules = rules  # 단순 데이터만

# ✅ Rich Domain Model
class Strategy:
    def __init__(self, name, rules):
        self.name = name
        self.rules = rules
        
    def add_rule(self, rule):
        # ✅ 비즈니스 규칙 포함
        if len(self.rules) >= 5:
            raise TooManyRulesError()
        
        if not self._is_compatible_rule(rule):
            raise IncompatibleRuleError()
            
        self.rules.append(rule)
```

## 🔄 리팩토링 전략

### 단계별 개선 방법

#### Phase 1: Extract Service (Service 추출)
```python
# Before: UI에 비즈니스 로직
class StrategyView(QWidget):
    def create_strategy(self):
        # 복잡한 비즈니스 로직...

# After: Service로 추출
class StrategyService:
    def create_strategy(self, command):
        # 비즈니스 로직을 Service로 이동

class StrategyView(QWidget):
    def create_strategy(self):
        # Service 호출만
        self.presenter.create_strategy()
```

#### Phase 2: Extract Domain (Domain 추출)
```python
# Before: Service에 비즈니스 규칙
class StrategyService:
    def validate_strategy(self, strategy_data):
        if len(strategy_data.rules) > 5:
            return False

# After: Domain으로 이동
class Strategy:
    def add_rule(self, rule):
        if len(self.rules) >= 5:
            raise TooManyRulesError()
```

#### Phase 3: Apply Repository (Repository 적용)
```python
# Before: Service에서 직접 DB 접근
class StrategyService:
    def save(self, strategy):
        db.execute("INSERT INTO strategies...")

# After: Repository 패턴 적용
class StrategyService:
    def save(self, strategy):
        self.strategy_repo.save(strategy)
```

## 🧪 테스트 전략

### 계층별 테스트 방법

#### Domain Layer 테스트
```python
# ✅ 외부 의존성 없이 테스트 가능
def test_strategy_add_rule():
    # Given
    strategy = Strategy("test", [])
    rule = TradingRule("RSI > 70")
    
    # When
    strategy.add_rule(rule)
    
    # Then
    assert len(strategy.rules) == 1
    assert strategy.rules[0] == rule
```

#### Application Layer 테스트
```python
# ✅ Mock을 사용한 Service 테스트
def test_strategy_service_create():
    # Given
    mock_repo = Mock()
    service = StrategyService(mock_repo)
    command = CreateStrategyCommand("test", [])
    
    # When
    service.create_strategy(command)
    
    # Then
    mock_repo.save.assert_called_once()
```

#### Presentation Layer 테스트
```python
# ✅ View와 Presenter 분리 테스트
def test_presenter_create_strategy():
    # Given
    mock_view = Mock()
    mock_service = Mock()
    presenter = StrategyPresenter(mock_view, mock_service)
    
    # When
    presenter.create_strategy({"name": "test"})
    
    # Then
    mock_service.create_strategy.assert_called_once()
    mock_view.show_success.assert_called_once()
```

## 📊 성능 문제 해결

### 일반적인 성능 이슈

#### 1. N+1 쿼리 문제
```python
# ❌ 문제: 반복적 DB 호출
def get_strategies_with_rules():
    strategies = strategy_repo.find_all()
    for strategy in strategies:
        strategy.rules = rule_repo.find_by_strategy_id(strategy.id)  # N+1

# ✅ 해결: 배치 로딩
def get_strategies_with_rules():
    strategies = strategy_repo.find_all_with_rules()  # JOIN 쿼리
```

#### 2. 과도한 이벤트 발행
```python
# ❌ 문제: 모든 변경에 이벤트
class Strategy:
    def set_name(self, name):
        self.name = name
        self.add_event(StrategyNameChanged())  # 과도한 이벤트

# ✅ 해결: 중요한 이벤트만
class Strategy:
    def activate(self):
        self.status = StrategyStatus.ACTIVE
        self.add_event(StrategyActivated())  # 중요한 이벤트만
```

## 📚 참고 리소스

### 디버깅 도구
- **계층 의존성 체크**: 각 계층이 올바른 방향으로만 의존하는지 확인
- **순환 참조 탐지**: import 순환 참조 자동 검출
- **테스트 커버리지**: 각 계층별 테스트 커버리지 측정

### 코드 품질 지표
- **응집도**: 하나의 클래스가 하나의 책임만 가지는가?
- **결합도**: 계층 간 의존성이 최소화되어 있는가?
- **복잡도**: 각 메서드의 순환 복잡도가 10 이하인가?

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): 전체 아키텍처 구조
- [계층별 책임](02_LAYER_RESPONSIBILITIES.md): 각 계층의 명확한 역할
- [기능 개발](04_FEATURE_DEVELOPMENT.md): 올바른 개발 워크플로

---
**💡 핵심**: "문제가 발생하면 먼저 올바른 계층에서 작업하고 있는지 확인하세요!"
