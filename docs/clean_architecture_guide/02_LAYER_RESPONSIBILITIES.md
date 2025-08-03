# 🎭 계층별 책임과 경계

> **목적**: 각 계층의 명확한 역할과 경계 정의  
> **대상**: 개발자, 아키텍처 검토자  
> **예상 읽기 시간**: 15분

## 📋 계층별 핵심 책임

### 🎨 Presentation Layer - "사용자와의 소통"

#### ✅ 담당 업무
- **사용자 입력 수집**: 폼 데이터, 버튼 클릭, 드래그앤드롭
- **데이터 표시**: 차트, 테이블, 다이얼로그, 알림
- **UI 상태 관리**: 버튼 활성화/비활성화, 로딩 스피너
- **입력 검증**: 형식 검증, 필수 필드 체크

#### ❌ 하지 말아야 할 것
- 비즈니스 로직 구현 (계산, 검증 등)
- 직접적인 데이터베이스 접근
- 외부 API 호출
- 복잡한 상태 변경 로직

#### 💡 실제 예시
```python
class TriggerBuilderView(QWidget):
    """트리거 빌더 UI - Presentation 계층"""
    
    def __init__(self):
        super().__init__()
        self.presenter = None  # Presenter가 주입됨
        
    def on_create_condition_clicked(self):
        # ✅ 입력 데이터 수집
        form_data = {
            'variable_id': self.variable_combo.currentData(),
            'operator': self.operator_combo.currentText(),
            'target_value': self.target_value_input.text()
        }
        
        # ✅ 기본 검증만 수행
        if not form_data['target_value']:
            self.show_error("목표값을 입력하세요")
            return
            
        # ✅ Presenter에게 위임
        self.presenter.create_condition(form_data)
        
    def update_condition_list(self, conditions):
        # ✅ 데이터 표시만 담당
        self.condition_list.clear()
        for condition in conditions:
            self.condition_list.addItem(condition.display_name)
```

### ⚙️ Application Layer - "비즈니스 흐름 조율"

#### ✅ 담당 업무
- **유스케이스 구현**: "전략 생성", "백테스트 실행"
- **트랜잭션 관리**: 여러 Repository 작업 조율
- **이벤트 발행**: Domain Event를 다른 컨텍스트로 전파
- **권한 검사**: 사용자 권한 확인

#### ❌ 하지 말아야 할 것
- UI 직접 조작
- 비즈니스 규칙 정의 (Domain 계층 역할)
- 데이터 저장 로직 구현 (Infrastructure 역할)
- 복잡한 계산 로직 (Domain Service 역할)

#### 💡 실제 예시
```python
class ConditionCreationService:
    """조건 생성 서비스 - Application 계층"""
    
    def __init__(self, condition_repo, variable_repo, event_publisher):
        self.condition_repo = condition_repo
        self.variable_repo = variable_repo
        self.event_publisher = event_publisher
        
    def create_condition(self, command: CreateConditionCommand):
        # ✅ 유스케이스 흐름 조율
        
        # 1. 필요한 데이터 조회 (Infrastructure 위임)
        variable = self.variable_repo.find_by_id(command.variable_id)
        
        # 2. 비즈니스 규칙 적용 (Domain 위임)
        condition = TradingCondition.create(
            variable, command.operator, command.target_value
        )
        
        # 3. 저장 (Infrastructure 위임)
        self.condition_repo.save(condition)
        
        # 4. 이벤트 발행 (Infrastructure 위임)
        self.event_publisher.publish(
            ConditionCreatedEvent(condition.id, condition.variable_id)
        )
        
        return CreateConditionResult(condition.id)
```

### 💎 Domain Layer - "핵심 비즈니스 규칙"

#### ✅ 담당 업무
- **비즈니스 규칙 정의**: "RSI는 0-100 범위만 가능"
- **도메인 로직**: 복잡한 계산, 검증, 상태 변경
- **불변식 보장**: 객체의 일관성 유지
- **도메인 이벤트**: 중요한 비즈니스 사건 정의

#### ❌ 하지 말아야 할 것
- 외부 시스템 의존성 (DB, API, UI 등)
- 기술적 구현 세부사항
- 프레임워크별 코드
- 사용자 인터페이스 관련 로직

#### 💡 실제 예시
```python
class TradingCondition:
    """거래 조건 도메인 엔티티 - Domain 계층"""
    
    def __init__(self, condition_id, variable, operator, target_value):
        self.id = condition_id
        self.variable = variable
        self.operator = operator
        self.target_value = target_value
        self._events = []
        
    @classmethod
    def create(cls, variable, operator, target_value):
        # ✅ 비즈니스 규칙 검증
        if not cls._is_valid_operator(operator):
            raise InvalidOperatorError(f"지원하지 않는 연산자: {operator}")
            
        if not cls._is_compatible_value(variable, target_value):
            raise IncompatibleValueError(
                f"{variable.name}와 {target_value}는 호환되지 않습니다"
            )
        
        condition_id = ConditionId.generate()
        condition = cls(condition_id, variable, operator, target_value)
        
        # ✅ 도메인 이벤트 발생
        condition._events.append(
            ConditionCreatedEvent(condition_id, variable.id)
        )
        
        return condition
        
    def evaluate(self, market_data):
        # ✅ 핵심 비즈니스 로직
        variable_value = self.variable.calculate(market_data)
        return self._apply_operator(variable_value, self.target_value)
        
    @staticmethod
    def _is_valid_operator(operator):
        return operator in ['>', '>=', '<', '<=', '==', '!=', '~=']
        
    @staticmethod
    def _is_compatible_value(variable, target_value):
        # 변수 타입과 목표값 호환성 검증
        if variable.value_type == 'percentage':
            return 0 <= float(target_value) <= 100
        return True
```

### 🔌 Infrastructure Layer - "기술적 구현"

#### ✅ 담당 업무
- **데이터 저장/조회**: Database Repository 구현
- **외부 API 연동**: 업비트 API, 알림 서비스
- **이벤트 저장소**: Domain Event 영속화
- **설정 관리**: 환경별 설정 로딩

#### ❌ 하지 말아야 할 것
- 비즈니스 로직 구현
- UI 직접 조작
- Domain 객체 구조 변경
- 비즈니스 검증 로직

#### 💡 실제 예시
```python
class SQLiteConditionRepository:
    """조건 저장소 구현 - Infrastructure 계층"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    def save(self, condition: TradingCondition):
        # ✅ Domain 객체 → DB 변환
        query = """
        INSERT INTO trading_conditions 
        (id, variable_id, operator, target_value, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        
        self.db.execute(query, (
            condition.id.value,
            condition.variable.id.value,
            condition.operator,
            str(condition.target_value),
            datetime.utcnow()
        ))
        
    def find_by_id(self, condition_id: ConditionId) -> TradingCondition:
        # ✅ DB → Domain 객체 변환
        query = "SELECT * FROM trading_conditions WHERE id = ?"
        row = self.db.fetch_one(query, (condition_id.value,))
        
        if not row:
            raise ConditionNotFoundError(condition_id)
            
        # Variable 정보도 조회
        variable = self._load_variable(row['variable_id'])
        
        return TradingCondition(
            ConditionId(row['id']),
            variable,
            row['operator'],
            row['target_value']
        )
```

### 🛠️ Shared Layer - "공통 도구"

#### ✅ 담당 업무
- **공통 유틸리티**: Result, Maybe, Either 등
- **확장 메서드**: 자주 사용하는 도우미 함수
- **공통 예외**: 시스템 전체에서 사용하는 예외
- **기본 인터페이스**: 모든 계층에서 사용하는 기본 타입

#### 💡 실제 예시
```python
class Result(Generic[T]):
    """결과 래퍼 클래스 - Shared 계층"""
    
    def __init__(self, success: bool, data: T = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error
        
    @classmethod
    def ok(cls, data: T) -> 'Result[T]':
        return cls(True, data=data)
        
    @classmethod
    def fail(cls, error: str) -> 'Result[T]':
        return cls(False, error=error)
        
    def map(self, func) -> 'Result':
        if self.success:
            try:
                return Result.ok(func(self.data))
            except Exception as e:
                return Result.fail(str(e))
        return self
```

## 🚫 계층 간 의존성 규칙

### ✅ 허용되는 의존성
```
Presentation → Application → Domain
Infrastructure → Domain
Shared ← 모든 계층
```

### ❌ 금지되는 의존성
```
Domain → Infrastructure (절대 금지!)
Domain → Application (절대 금지!)
Domain → Presentation (절대 금지!)
Application → Presentation (바람직하지 않음)
```

## 🎯 계층별 테스트 전략

### Presentation Layer
- **UI 테스트**: PyQt6 QTest 프레임워크
- **모킹**: Application 계층 모킹
- **검증**: 사용자 상호작용, 데이터 표시

### Application Layer
- **유닛 테스트**: 각 Service 클래스
- **모킹**: Infrastructure 계층 모킹
- **검증**: 비즈니스 흐름, 이벤트 발행

### Domain Layer
- **순수 유닛 테스트**: 외부 의존성 없음
- **검증**: 비즈니스 규칙, 도메인 로직

### Infrastructure Layer
- **통합 테스트**: 실제 DB/API 연동
- **컨테이너 테스트**: TestContainers 활용

## 🔍 다음 단계

- **[데이터 흐름](03_DATA_FLOW.md)**: 실제 요청 처리 과정
- **[기능 추가 가이드](04_FEATURE_DEVELOPMENT.md)**: 개발 워크플로
- **[UI 개발 가이드](05_UI_DEVELOPMENT.md)**: MVP 패턴 구현

---
**💡 핵심**: "각 계층은 명확한 책임을 가지며, 의존성 방향을 준수해야 합니다!"
