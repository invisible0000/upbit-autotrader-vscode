# 🔄 데이터 흐름 및 요청 처리

> **목적**: 사용자 요청부터 응답까지의 완전한 데이터 흐름 이해  
> **대상**: 개발자, 디버깅 담당자  
> **예상 읽기 시간**: 12분

## 📊 전체 데이터 흐름 개요

```
[사용자] → [View] → [Presenter] → [Service] → [Domain] → [Repository]
    ↑         ↑         ↑          ↑         ↑          ↓
    ←---------←---------←----------←---------←----- [Database]
```

## 🎯 구체적 예시: "새 조건 생성" 흐름

### 1. 사용자 액션 (Presentation Layer)
```python
# TriggerBuilderView.py
def on_create_condition_clicked(self):
    """사용자가 조건 생성 버튼 클릭"""
    # Step 1: 입력 데이터 수집
    form_data = {
        'variable_id': self.variable_combo.currentData(),  # "RSI"
        'operator': self.operator_combo.currentText(),     # ">"
        'target_value': self.target_value_input.text(),    # "70"
        'parameters': self._get_parameter_values()         # {"period": 14}
    }
    
    # Step 2: 기본 검증 (UI 레벨)
    if not self._validate_form(form_data):
        self.show_error_message("입력값을 확인하세요")
        return
    
    # Step 3: Presenter에게 위임
    self.presenter.handle_create_condition(form_data)
```

### 2. 프레젠테이션 로직 (Presentation Layer)
```python
# TriggerBuilderPresenter.py
def handle_create_condition(self, form_data):
    """사용자 입력을 Application 계층으로 전달"""
    # Step 4: DTO 변환
    command = CreateConditionCommand(
        variable_id=VariableId(form_data['variable_id']),
        operator=form_data['operator'],
        target_value=form_data['target_value'],
        parameters=form_data['parameters']
    )
    
    # Step 5: Application Service 호출
    try:
        result = self.condition_service.create_condition(command)
        
        if result.success:
            # Step 6a: 성공 시 UI 업데이트
            self.view.show_success_message("조건이 생성되었습니다")
            self.view.add_condition_to_list(result.data.condition)
            self.view.clear_form()
        else:
            # Step 6b: 실패 시 에러 표시
            self.view.show_error_message(result.error)
            
    except Exception as e:
        self.view.show_error_message(f"예상치 못한 오류: {str(e)}")
```

### 3. 비즈니스 로직 조율 (Application Layer)
```python
# ConditionCreationService.py
def create_condition(self, command: CreateConditionCommand):
    """조건 생성 유스케이스"""
    try:
        # Step 7: 필요한 데이터 조회 (Infrastructure 위임)
        variable = self.variable_repo.find_by_id(command.variable_id)
        if not variable:
            return Result.fail("존재하지 않는 변수입니다")
        
        # Step 8: 비즈니스 규칙 적용 (Domain 위임)
        condition = TradingCondition.create(
            variable=variable,
            operator=command.operator,
            target_value=command.target_value,
            parameters=command.parameters
        )
        
        # Step 9: 트랜잭션 시작
        with self.unit_of_work.transaction():
            # Step 10: 저장 (Infrastructure 위임)
            saved_condition = self.condition_repo.save(condition)
            
            # Step 11: 도메인 이벤트 처리
            for event in condition.get_uncommitted_events():
                self.event_publisher.publish(event)
            
            condition.mark_events_as_committed()
        
        # Step 12: 성공 결과 반환
        return Result.ok(CreateConditionResult(saved_condition))
        
    except DomainException as e:
        return Result.fail(f"비즈니스 규칙 위반: {e.message}")
    except InfrastructureException as e:
        return Result.fail(f"시스템 오류: {e.message}")
```

### 4. 도메인 로직 실행 (Domain Layer)
```python
# TradingCondition.py (Domain Entity)
@classmethod
def create(cls, variable, operator, target_value, parameters):
    """조건 생성 - 핵심 비즈니스 로직"""
    # Step 13: 비즈니스 규칙 검증
    
    # 13a: 연산자 유효성 검사
    if not cls._is_valid_operator(operator):
        raise InvalidOperatorError(f"지원하지 않는 연산자: {operator}")
    
    # 13b: 변수-값 호환성 검사
    if not variable.is_compatible_with_value(target_value):
        raise IncompatibleValueError(
            f"변수 '{variable.name}'와 값 '{target_value}'는 호환되지 않습니다"
        )
    
    # 13c: 파라미터 유효성 검사
    validated_params = variable.validate_parameters(parameters)
    
    # Step 14: 도메인 객체 생성
    condition_id = ConditionId.generate()
    condition = cls(
        id=condition_id,
        variable=variable,
        operator=operator,
        target_value=TargetValue(target_value),
        parameters=validated_params,
        created_at=datetime.utcnow()
    )
    
    # Step 15: 도메인 이벤트 발생
    condition._add_event(
        ConditionCreatedEvent(
            condition_id=condition_id,
            variable_id=variable.id,
            operator=operator,
            target_value=target_value
        )
    )
    
    return condition

def _is_valid_operator(operator):
    """연산자 검증 로직"""
    valid_operators = ['>', '>=', '<', '<=', '==', '!=', '~=']
    return operator in valid_operators
```

### 5. 데이터 저장 (Infrastructure Layer)
```python
# SQLiteConditionRepository.py
def save(self, condition: TradingCondition):
    """조건을 데이터베이스에 저장"""
    # Step 16: Domain 객체 → DB 스키마 변환
    condition_data = {
        'id': condition.id.value,
        'variable_id': condition.variable.id.value,
        'operator': condition.operator,
        'target_value': str(condition.target_value.value),
        'parameters': json.dumps(condition.parameters.to_dict()),
        'created_at': condition.created_at.isoformat(),
        'is_active': True
    }
    
    # Step 17: SQL 실행
    query = """
    INSERT INTO trading_conditions 
    (id, variable_id, operator, target_value, parameters, created_at, is_active)
    VALUES (:id, :variable_id, :operator, :target_value, :parameters, :created_at, :is_active)
    """
    
    try:
        self.db.execute(query, condition_data)
        
        # Step 18: 저장된 데이터 반환용 조회
        return self.find_by_id(condition.id)
        
    except sqlite3.Error as e:
        raise DatabaseError(f"조건 저장 실패: {str(e)}")
```

## 🔄 이벤트 기반 사이드 이펙트

### 도메인 이벤트 처리 흐름
```python
# ConditionCreatedEventHandler.py (Application Layer)
def handle(self, event: ConditionCreatedEvent):
    """조건 생성 이벤트 처리"""
    # Step 19: 관련 시스템 업데이트
    
    # 19a: 호환성 캐시 무효화
    self.compatibility_cache.invalidate_for_variable(event.variable_id)
    
    # 19b: UI 알림 발송
    self.notification_service.send_notification(
        NotificationDto(
            type="success",
            message=f"조건 '{event.condition_id}'가 생성되었습니다",
            timestamp=event.occurred_at
        )
    )
    
    # 19c: 분석 데이터 수집
    self.analytics_service.track_event(
        "condition_created",
        {"variable_id": event.variable_id, "operator": event.operator}
    )
```

## 📊 조회 요청 흐름 (CQRS)

### 조건 목록 조회 예시
```python
# 1. View → Presenter
def on_view_initialized(self):
    self.presenter.load_condition_list()

# 2. Presenter → Query Handler
def load_condition_list(self):
    query = GetConditionListQuery(user_id=self.current_user.id)
    result = self.condition_query_handler.handle(query)
    self.view.display_conditions(result.conditions)

# 3. Query Handler → Repository
def handle(self, query: GetConditionListQuery):
    conditions = self.condition_repo.find_by_user_id(query.user_id)
    return GetConditionListResult([
        ConditionDto.from_domain(condition) 
        for condition in conditions
    ])
```

## 🔍 에러 처리 흐름

### 계층별 에러 전파
```python
# Domain Layer
class TradingCondition:
    def create(self, ...):
        if invalid_rule:
            raise DomainException("비즈니스 규칙 위반")

# Application Layer  
class ConditionService:
    def create_condition(self, command):
        try:
            return TradingCondition.create(...)
        except DomainException as e:
            return Result.fail(e.message)

# Presentation Layer
class Presenter:
    def handle_create_condition(self, form_data):
        result = self.service.create_condition(command)
        if not result.success:
            self.view.show_error_message(result.error)
```

## 🚀 성능 최적화 포인트

### 1. 지연 로딩 (Lazy Loading)
```python
# Repository에서 연관 객체 지연 로딩
def find_by_id(self, condition_id):
    condition = self._load_basic_condition(condition_id)
    condition.variable = LazyProxy(lambda: self._load_variable(condition.variable_id))
    return condition
```

### 2. 캐싱 전략
```python
# Application Layer에서 자주 사용되는 데이터 캐싱
@cached(ttl=300)  # 5분 캐시
def get_variable_compatibility_matrix(self):
    return self.variable_repo.get_all_compatibility_data()
```

### 3. 배치 처리
```python
# 여러 조건을 한 번에 처리
def create_multiple_conditions(self, commands):
    with self.unit_of_work.transaction():
        for command in commands:
            condition = TradingCondition.create(...)
            self.condition_repo.save(condition)
```

## 🔍 다음 단계

- **[기능 추가 가이드](04_FEATURE_DEVELOPMENT.md)**: 새 기능 개발 워크플로
- **[디버깅 가이드](15_DEBUGGING_GUIDE.md)**: 데이터 흐름 추적 방법
- **[성능 최적화](10_PERFORMANCE_OPTIMIZATION.md)**: 병목점 해결

---
**💡 핵심**: "데이터 흐름을 이해하면 디버깅과 기능 확장이 훨씬 쉬워집니다!"
