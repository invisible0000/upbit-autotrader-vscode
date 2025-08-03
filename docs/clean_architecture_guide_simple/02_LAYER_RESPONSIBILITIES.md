# 🎭 계층별 책임과 경계

> **목적**: 각 계층의 명확한 역할 정의  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 📋 계층별 핵심 책임 요약

| 계층 | 핵심 책임 | 금지 사항 |
|------|----------|----------|
| 🎨 Presentation | UI 표시/입력 | 비즈니스 로직, DB 접근 |
| ⚙️ Application | Use Case 조율 | UI 조작, 비즈니스 규칙 정의 |
| 💎 Domain | 비즈니스 규칙 | 외부 의존성 참조 |
| 🔌 Infrastructure | 외부 연동 | 비즈니스 로직 |
| 🛠️ Shared | 공통 유틸 | 계층별 특화 로직 |

## 🎨 Presentation Layer

### ✅ 담당 업무
- **입력 수집**: 폼 데이터, 버튼 클릭
- **화면 표시**: 차트, 테이블, 다이얼로그
- **UI 상태**: 버튼 활성화, 로딩 표시
- **기본 검증**: 필수 필드, 형식 확인

### 💡 올바른 구현
```python
class TriggerBuilderView(QWidget):
    def on_create_clicked(self):
        # ✅ 입력 수집
        data = self.collect_form_data()
        
        # ✅ 기본 검증
        if not data['target_value']:
            self.show_error("값을 입력하세요")
            return
            
        # ✅ Presenter에 위임
        self.presenter.create_trigger(data)
        
    def display_triggers(self, triggers):
        # ✅ 단순 표시
        self.trigger_list.clear()
        for trigger in triggers:
            self.trigger_list.addItem(trigger.name)
```

## ⚙️ Application Layer

### ✅ 담당 업무
- **Use Case 실행**: "전략 생성", "백테스트"
- **트랜잭션 관리**: 여러 작업 조율
- **이벤트 발행**: Domain Event 전파
- **인증/권한**: 사용자 권한 확인

### 💡 올바른 구현
```python
class TriggerService:
    def create_trigger(self, command):
        # ✅ Use Case 흐름 조율
        
        # 1. 검증 (Application 레벨)
        if not self._user_can_create_trigger(command.user_id):
            raise UnauthorizedError()
            
        # 2. Domain 객체 생성
        trigger = Trigger.create(
            command.variable_id,
            command.operator,
            command.target_value
        )
        
        # 3. 저장 (Infrastructure 위임)
        self.trigger_repo.save(trigger)
        
        # 4. 이벤트 발행
        self.event_publisher.publish(TriggerCreated(trigger.id))
        
        return TriggerDto.from_entity(trigger)
```

## 💎 Domain Layer (핵심)

### ✅ 담당 업무
- **비즈니스 규칙**: 전략 검증, 호환성 체크
- **도메인 모델**: Entity, Value Object
- **도메인 이벤트**: 중요 비즈니스 사건
- **도메인 서비스**: 복잡한 비즈니스 로직

### 🚨 중요 제약
- **다른 계층 참조 금지**: 순수한 비즈니스 로직만
- **외부 의존성 없음**: DB, API 등 참조 불가

### 💡 올바른 구현
```python
class Trigger:
    """트리거 도메인 엔티티"""
    
    def __init__(self, trigger_id, variable, operator, target_value):
        self.id = trigger_id
        self.variable = variable
        self.operator = operator
        self.target_value = target_value
        self._events = []
        
    @classmethod
    def create(cls, variable_id, operator, target_value):
        # ✅ 비즈니스 규칙 검증
        if not cls._is_valid_operator(operator):
            raise InvalidOperatorError(f"지원하지 않는 연산자: {operator}")
            
        trigger_id = TriggerId.generate()
        trigger = cls(trigger_id, variable_id, operator, target_value)
        
        # ✅ 도메인 이벤트 추가
        trigger._events.append(TriggerCreated(trigger_id))
        return trigger
        
    def evaluate(self, market_data):
        # ✅ 순수 비즈니스 로직
        variable_value = market_data.get_value(self.variable)
        return self._apply_operator(variable_value, self.target_value)
```

## 🔌 Infrastructure Layer

### ✅ 담당 업무
- **데이터 저장**: Repository 구현
- **외부 API**: 업비트 API 클라이언트
- **이벤트 저장**: Event Store 구현
- **설정 관리**: DB 연결, 환경 변수

### 💡 올바른 구현
```python
class SqliteTriggerRepository(TriggerRepository):
    """Repository 구현체"""
    
    def save(self, trigger: Trigger):
        # ✅ Domain 객체 → DB 변환
        data = {
            'id': trigger.id.value,
            'variable_id': trigger.variable.value,
            'operator': trigger.operator,
            'target_value': str(trigger.target_value),
            'created_at': datetime.utcnow()
        }
        
        self.db.execute(
            "INSERT INTO triggers (id, variable_id, operator, target_value, created_at) "
            "VALUES (:id, :variable_id, :operator, :target_value, :created_at)",
            data
        )
        
    def find_by_id(self, trigger_id: TriggerId) -> Trigger:
        # ✅ DB → Domain 객체 변환
        row = self.db.fetchone(
            "SELECT * FROM triggers WHERE id = ?",
            (trigger_id.value,)
        )
        
        if not row:
            raise TriggerNotFoundError(trigger_id)
            
        return Trigger(
            TriggerId(row['id']),
            VariableId(row['variable_id']),
            row['operator'],
            row['target_value']
        )
```

## 🛠️ Shared Layer

### ✅ 담당 업무
- **공통 유틸리티**: 날짜, 문자열 처리
- **공통 예외**: 기본 예외 클래스
- **확장 메서드**: 편의 기능
- **헬퍼 함수**: 범용 기능

### 💡 올바른 구현
```python
class Result:
    """공통 결과 객체"""
    
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

class Money:
    """공통 금액 값 객체"""
    
    def __init__(self, amount: Decimal, currency: str = "KRW"):
        if amount < 0:
            raise ValueError("금액은 0 이상이어야 합니다")
        self.amount = amount
        self.currency = currency
```

## 🚨 경계 위반 예시와 해결

### ❌ 자주 하는 실수들

#### UI에서 비즈니스 로직 수행
```python
# ❌ 잘못된 예시
class StrategyView(QWidget):
    def save_strategy(self):
        # UI에서 직접 비즈니스 로직 수행
        if len(self.strategy.rules) > 5:  # 비즈니스 규칙
            self.show_error("규칙은 5개까지만 가능합니다")
```

#### Domain에서 외부 의존성 참조
```python
# ❌ 잘못된 예시
class Strategy:
    def save(self):
        # Domain에서 직접 DB 접근
        conn = sqlite3.connect("strategies.db")  # 절대 금지!
```

### ✅ 올바른 해결책

#### Presenter 패턴 적용
```python
# ✅ 올바른 분리
class StrategyPresenter:
    def save_strategy(self):
        # Application Service에 위임
        result = self.strategy_service.save_strategy(self.current_strategy)
        if result.success:
            self.view.show_success_message()
        else:
            self.view.show_error(result.error)
```

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): 전체 아키텍처 구조
- [데이터 흐름](03_DATA_FLOW.md): 계층 간 데이터 흐름
- [기능 개발](04_FEATURE_DEVELOPMENT.md): 실제 개발 가이드

---
**💡 핵심**: "각 계층은 자신의 책임만 수행하고, 다른 계층에 의존하지 않습니다!"
