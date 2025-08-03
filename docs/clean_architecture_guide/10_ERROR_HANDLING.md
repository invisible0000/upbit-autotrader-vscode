# 🚨 에러 처리 가이드

> **목적**: Clean Architecture에서 체계적인 에러 처리 및 복구 전략  
> **대상**: 개발자, QA 엔지니어  
> **예상 읽기 시간**: 15분

## 🎯 에러 처리 철학

### 🔄 계층별 에러 처리 전략
```
Domain Layer      ← 비즈니스 규칙 위반 (DomainException)
Application Layer ← 유스케이스 실패 (ApplicationException)  
Infrastructure    ← 외부 의존성 오류 (InfrastructureException)
Presentation      ← 사용자 인터페이스 오류 (PresentationException)
```

### 핵심 원칙
- **실패 빠르게**: 문제 발생 시 즉시 감지 및 보고
- **계층별 책임**: 각 계층에서 적절한 수준의 에러 처리
- **사용자 친화적**: 기술적 에러를 사용자가 이해할 수 있는 메시지로 변환

## 💎 Domain Layer 에러 처리

### 1. 도메인 예외 정의
```python
# domain/exceptions/domain_exceptions.py
class DomainException(Exception):
    """도메인 계층 기본 예외"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class BusinessRuleViolationException(DomainException):
    """비즈니스 규칙 위반 예외"""
    
    def __init__(self, rule_name: str, violation_details: str):
        super().__init__(
            message=f"비즈니스 규칙 위반: {rule_name}",
            error_code="BUSINESS_RULE_VIOLATION",
            details={"rule": rule_name, "violation": violation_details}
        )

class InvalidTradingConditionException(DomainException):
    """잘못된 거래 조건 예외"""
    
    def __init__(self, condition_id: str, reason: str):
        super().__init__(
            message=f"잘못된 거래 조건: {condition_id}",
            error_code="INVALID_TRADING_CONDITION",
            details={"condition_id": condition_id, "reason": reason}
        )

class IncompatibleVariableException(DomainException):
    """호환되지 않는 변수 조합 예외"""
    
    def __init__(self, var1: str, var2: str, reason: str):
        super().__init__(
            message=f"변수 '{var1}'과 '{var2}'는 호환되지 않습니다: {reason}",
            error_code="INCOMPATIBLE_VARIABLES",
            details={"variable1": var1, "variable2": var2, "reason": reason}
        )

# domain/entities/trading_condition.py
class TradingCondition:
    """거래 조건 - 에러 처리 적용"""
    
    def __init__(self, variable: TradingVariable, operator: str, target_value: any):
        # ✅ 생성 시점에서 유효성 검증
        self._validate_construction(variable, operator, target_value)
        
        self.variable = variable
        self.operator = operator
        self.target_value = target_value
    
    def _validate_construction(self, variable: TradingVariable, operator: str, target_value: any):
        """생성 시점 유효성 검증"""
        
        # 변수 유효성 검사
        if not variable or not variable.is_active:
            raise InvalidTradingConditionException(
                condition_id="new",
                reason=f"비활성 변수: {variable.id if variable else 'None'}"
            )
        
        # 연산자 유효성 검사
        valid_operators = ['>', '>=', '<', '<=', '==', '!=', '~=']
        if operator not in valid_operators:
            raise InvalidTradingConditionException(
                condition_id="new",
                reason=f"지원하지 않는 연산자: {operator}"
            )
        
        # 대상값 유효성 검사
        if target_value is None:
            raise InvalidTradingConditionException(
                condition_id="new",
                reason="대상값이 None입니다"
            )
    
    def evaluate(self, market_data: MarketData) -> bool:
        """조건 평가 - 에러 처리 포함"""
        try:
            # 시장 데이터 유효성 검사
            if not market_data or not market_data.is_valid():
                raise InvalidTradingConditionException(
                    condition_id=str(self.id),
                    reason="유효하지 않은 시장 데이터"
                )
            
            # 변수값 계산
            variable_value = self._calculate_variable_value(market_data)
            
            # 조건 평가
            return self._perform_comparison(variable_value, self.target_value)
            
        except DomainException:
            # 도메인 예외는 그대로 전파
            raise
        except Exception as e:
            # 예상치 못한 예외는 도메인 예외로 변환
            raise InvalidTradingConditionException(
                condition_id=str(self.id),
                reason=f"조건 평가 중 오류: {str(e)}"
            ) from e
    
    def _calculate_variable_value(self, market_data: MarketData) -> float:
        """변수값 계산 - 에러 처리"""
        try:
            return self.variable.calculate_value(market_data)
        except Exception as e:
            raise InvalidTradingConditionException(
                condition_id=str(self.id),
                reason=f"변수값 계산 실패: {str(e)}"
            ) from e
    
    def _perform_comparison(self, value1: float, value2: float) -> bool:
        """비교 연산 - 에러 처리"""
        try:
            if self.operator == '>':
                return value1 > value2
            elif self.operator == '>=':
                return value1 >= value2
            elif self.operator == '<':
                return value1 < value2
            elif self.operator == '<=':
                return value1 <= value2
            elif self.operator == '==':
                return abs(value1 - value2) < 1e-10  # 부동소수점 비교
            elif self.operator == '!=':
                return abs(value1 - value2) >= 1e-10
            elif self.operator == '~=':
                return abs(value1 - value2) < (value2 * 0.01)  # 1% 오차 허용
            else:
                raise InvalidTradingConditionException(
                    condition_id=str(self.id),
                    reason=f"지원하지 않는 연산자: {self.operator}"
                )
        except (TypeError, ValueError) as e:
            raise InvalidTradingConditionException(
                condition_id=str(self.id),
                reason=f"비교 연산 실패: {str(e)}"
            ) from e
```

### 2. 도메인 서비스 에러 처리
```python
# domain/services/compatibility_validation_service.py
class CompatibilityValidationService:
    """호환성 검증 서비스 - 에러 처리 적용"""
    
    def validate_variable_compatibility(
        self, 
        var1: TradingVariable, 
        var2: TradingVariable
    ) -> CompatibilityResult:
        """변수 호환성 검증"""
        
        try:
            # 입력 유효성 검사
            if not var1 or not var2:
                raise IncompatibleVariableException(
                    var1=str(var1.id) if var1 else "None",
                    var2=str(var2.id) if var2 else "None", 
                    reason="변수가 None입니다"
                )
            
            # 동일 변수 검사
            if var1.id == var2.id:
                return CompatibilityResult.create_warning(
                    "동일한 변수입니다", 
                    "SAME_VARIABLE"
                )
            
            # comparison_group 호환성 검사
            if var1.comparison_group != var2.comparison_group:
                # 완전 비호환 케이스
                incompatible_groups = [
                    ("percentage_comparable", "zero_centered"),
                    ("volume_based", "percentage_comparable"),
                ]
                
                current_pair = (var1.comparison_group, var2.comparison_group)
                if current_pair in incompatible_groups or current_pair[::-1] in incompatible_groups:
                    raise IncompatibleVariableException(
                        var1=str(var1.id),
                        var2=str(var2.id),
                        reason=f"비교 불가능한 그룹: {var1.comparison_group} vs {var2.comparison_group}"
                    )
                
                # 경고 케이스 (정규화 필요)
                return CompatibilityResult.create_warning(
                    "정규화가 필요한 조합입니다",
                    "NORMALIZATION_REQUIRED"
                )
            
            # 호환 가능
            return CompatibilityResult.create_compatible()
            
        except DomainException:
            raise
        except Exception as e:
            raise IncompatibleVariableException(
                var1=str(var1.id) if var1 else "Unknown",
                var2=str(var2.id) if var2 else "Unknown",
                reason=f"호환성 검증 중 오류: {str(e)}"
            ) from e

class CompatibilityResult:
    """호환성 검증 결과"""
    
    def __init__(self, status: str, message: str, code: str = None):
        self.status = status  # 'compatible', 'warning', 'incompatible'
        self.message = message
        self.code = code
    
    @classmethod
    def create_compatible(cls):
        return cls("compatible", "호환 가능")
    
    @classmethod  
    def create_warning(cls, message: str, code: str):
        return cls("warning", message, code)
    
    @classmethod
    def create_incompatible(cls, message: str, code: str):
        return cls("incompatible", message, code)
```

## ⚙️ Application Layer 에러 처리

### 1. 애플리케이션 예외 정의
```python
# application/exceptions/application_exceptions.py
class ApplicationException(Exception):
    """애플리케이션 계층 기본 예외"""
    
    def __init__(self, message: str, error_code: str = None, inner_exception: Exception = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.inner_exception = inner_exception
        self.timestamp = datetime.utcnow()

class ConditionNotFoundError(ApplicationException):
    """조건 없음 예외"""
    
    def __init__(self, condition_id: str):
        super().__init__(
            message=f"조건을 찾을 수 없습니다: {condition_id}",
            error_code="CONDITION_NOT_FOUND"
        )
        self.condition_id = condition_id

class InvalidUseCaseParameterError(ApplicationException):
    """잘못된 유스케이스 파라미터 예외"""
    
    def __init__(self, parameter_name: str, parameter_value: any, reason: str):
        super().__init__(
            message=f"잘못된 파라미터 '{parameter_name}': {reason}",
            error_code="INVALID_PARAMETER"
        )
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value
        self.reason = reason

class UseCaseExecutionError(ApplicationException):
    """유스케이스 실행 실패 예외"""
    
    def __init__(self, use_case_name: str, reason: str, inner_exception: Exception = None):
        super().__init__(
            message=f"유스케이스 '{use_case_name}' 실행 실패: {reason}",
            error_code="USE_CASE_EXECUTION_ERROR",
            inner_exception=inner_exception
        )
        self.use_case_name = use_case_name
```

### 2. 유스케이스 에러 처리
```python
# application/use_cases/create_condition_use_case.py
class CreateConditionUseCase:
    """조건 생성 유스케이스 - 에러 처리 적용"""
    
    def __init__(self, condition_repo, variable_repo, validation_service, event_publisher):
        self.condition_repo = condition_repo
        self.variable_repo = variable_repo
        self.validation_service = validation_service
        self.event_publisher = event_publisher
    
    def execute(self, command: CreateConditionCommand) -> CreateConditionResult:
        """조건 생성 실행 - 포괄적 에러 처리"""
        
        try:
            # 1. 입력 검증
            self._validate_command(command)
            
            # 2. 변수 조회
            variable = self._get_variable(command.variable_id)
            
            # 3. 호환성 검증 (외부 변수가 있는 경우)
            if command.external_variable_id:
                external_variable = self._get_variable(command.external_variable_id)
                self._validate_compatibility(variable, external_variable)
            
            # 4. 도메인 객체 생성
            condition = self._create_condition(command, variable)
            
            # 5. 저장
            saved_condition = self._save_condition(condition)
            
            # 6. 이벤트 발행
            self._publish_event(saved_condition)
            
            return CreateConditionResult.success(saved_condition.id)
            
        except DomainException as e:
            # 도메인 예외는 비즈니스 로직 오류로 처리
            logger.warning(f"도메인 규칙 위반: {str(e)}")
            return CreateConditionResult.failure(
                error_code=e.error_code,
                error_message=e.message,
                user_message="입력하신 조건에 문제가 있습니다. 설정을 확인해주세요."
            )
            
        except ApplicationException as e:
            # 애플리케이션 예외는 그대로 전파
            logger.error(f"조건 생성 실패: {str(e)}")
            raise
            
        except Exception as e:
            # 예상치 못한 예외는 애플리케이션 예외로 감싸서 전파
            logger.error(f"조건 생성 중 예상치 못한 오류: {str(e)}", exc_info=True)
            raise UseCaseExecutionError(
                use_case_name="CreateCondition",
                reason=str(e),
                inner_exception=e
            ) from e
    
    def _validate_command(self, command: CreateConditionCommand):
        """명령 유효성 검증"""
        if not command:
            raise InvalidUseCaseParameterError(
                parameter_name="command",
                parameter_value=None,
                reason="명령이 None입니다"
            )
        
        if not command.variable_id:
            raise InvalidUseCaseParameterError(
                parameter_name="variable_id",
                parameter_value=command.variable_id,
                reason="변수 ID가 필요합니다"
            )
        
        if not command.operator:
            raise InvalidUseCaseParameterError(
                parameter_name="operator",
                parameter_value=command.operator,
                reason="연산자가 필요합니다"
            )
    
    def _get_variable(self, variable_id: str) -> TradingVariable:
        """변수 조회 - 에러 처리"""
        try:
            variable = self.variable_repo.find_by_id(VariableId(variable_id))
            if not variable:
                raise ConditionNotFoundError(f"변수 '{variable_id}'를 찾을 수 없습니다")
            return variable
        except Exception as e:
            if isinstance(e, ApplicationException):
                raise
            raise UseCaseExecutionError(
                use_case_name="CreateCondition",
                reason=f"변수 조회 실패: {str(e)}",
                inner_exception=e
            ) from e
    
    def _validate_compatibility(self, var1: TradingVariable, var2: TradingVariable):
        """호환성 검증 - 에러 처리"""
        try:
            result = self.validation_service.validate_variable_compatibility(var1, var2)
            if result.status == "incompatible":
                raise InvalidUseCaseParameterError(
                    parameter_name="external_variable_id",
                    parameter_value=var2.id.value,
                    reason=result.message
                )
        except DomainException:
            raise
        except Exception as e:
            raise UseCaseExecutionError(
                use_case_name="CreateCondition",
                reason=f"호환성 검증 실패: {str(e)}",
                inner_exception=e
            ) from e
    
    def _create_condition(self, command: CreateConditionCommand, variable: TradingVariable) -> TradingCondition:
        """조건 생성 - 에러 처리"""
        try:
            return TradingCondition(
                variable=variable,
                operator=command.operator,
                target_value=command.target_value
            )
        except DomainException:
            raise
        except Exception as e:
            raise UseCaseExecutionError(
                use_case_name="CreateCondition",
                reason=f"조건 객체 생성 실패: {str(e)}",
                inner_exception=e
            ) from e
    
    def _save_condition(self, condition: TradingCondition) -> TradingCondition:
        """조건 저장 - 에러 처리"""
        try:
            return self.condition_repo.save(condition)
        except Exception as e:
            raise UseCaseExecutionError(
                use_case_name="CreateCondition", 
                reason=f"조건 저장 실패: {str(e)}",
                inner_exception=e
            ) from e
    
    def _publish_event(self, condition: TradingCondition):
        """이벤트 발행 - 에러 처리"""
        try:
            event = ConditionCreatedEvent(condition.id)
            self.event_publisher.publish(event)
        except Exception as e:
            # 이벤트 발행 실패는 로그만 남기고 계속 진행
            logger.warning(f"조건 생성 이벤트 발행 실패: {str(e)}")

class CreateConditionResult:
    """조건 생성 결과"""
    
    def __init__(self, success: bool, condition_id: str = None, 
                 error_code: str = None, error_message: str = None, 
                 user_message: str = None):
        self.success = success
        self.condition_id = condition_id
        self.error_code = error_code
        self.error_message = error_message
        self.user_message = user_message
    
    @classmethod
    def success(cls, condition_id: str):
        return cls(success=True, condition_id=condition_id)
    
    @classmethod
    def failure(cls, error_code: str, error_message: str, user_message: str = None):
        return cls(
            success=False,
            error_code=error_code,
            error_message=error_message,
            user_message=user_message or error_message
        )
```

## 🔌 Infrastructure Layer 에러 처리

### 1. 인프라 예외 정의
```python
# infrastructure/exceptions/infrastructure_exceptions.py
class InfrastructureException(Exception):
    """인프라 계층 기본 예외"""
    
    def __init__(self, message: str, error_code: str = None, retryable: bool = False):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.retryable = retryable
        self.timestamp = datetime.utcnow()

class DatabaseConnectionError(InfrastructureException):
    """데이터베이스 연결 오류"""
    
    def __init__(self, connection_string: str, inner_exception: Exception = None):
        super().__init__(
            message=f"데이터베이스 연결 실패: {connection_string}",
            error_code="DB_CONNECTION_ERROR",
            retryable=True
        )
        self.connection_string = connection_string
        self.inner_exception = inner_exception

class ExternalApiError(InfrastructureException):
    """외부 API 오류"""
    
    def __init__(self, api_name: str, status_code: int, response_text: str):
        super().__init__(
            message=f"{api_name} API 오류 (HTTP {status_code}): {response_text}",
            error_code="EXTERNAL_API_ERROR",
            retryable=status_code in [429, 500, 502, 503, 504]  # 재시도 가능한 상태 코드
        )
        self.api_name = api_name
        self.status_code = status_code
        self.response_text = response_text
```

### 2. Repository 에러 처리
```python
# infrastructure/repositories/sqlite_condition_repository.py
class SQLiteConditionRepository:
    """SQLite 조건 Repository - 에러 처리 적용"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def find_by_id(self, condition_id: ConditionId) -> Optional[TradingCondition]:
        """ID로 조건 조회 - 에러 처리"""
        
        try:
            query = """
            SELECT c.*, v.name as variable_name, v.comparison_group
            FROM trading_conditions c
            INNER JOIN trading_variables v ON c.variable_id = v.id
            WHERE c.id = ? AND c.is_active = 1
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (condition_id.value,))
                row = cursor.fetchone()
                
                if row:
                    return self._map_to_domain(row)
                return None
                
        except sqlite3.Error as e:
            logger.error(f"조건 조회 DB 오류: {str(e)}")
            raise DatabaseConnectionError(
                connection_string=self.db.connection_string,
                inner_exception=e
            ) from e
        except Exception as e:
            logger.error(f"조건 조회 중 예상치 못한 오류: {str(e)}")
            raise InfrastructureException(
                message=f"조건 조회 실패: {str(e)}",
                error_code="CONDITION_QUERY_ERROR"
            ) from e
    
    def save(self, condition: TradingCondition) -> TradingCondition:
        """조건 저장 - 트랜잭션 및 에러 처리"""
        
        try:
            with self.db.transaction():
                # 기존 조건 확인
                existing = self._check_existing_condition(condition)
                
                if existing:
                    return self._update_condition(condition)
                else:
                    return self._insert_condition(condition)
                    
        except sqlite3.IntegrityError as e:
            logger.error(f"조건 저장 무결성 오류: {str(e)}")
            raise InfrastructureException(
                message="중복된 조건이거나 필수 정보가 누락되었습니다",
                error_code="DATA_INTEGRITY_ERROR"
            ) from e
        except sqlite3.Error as e:
            logger.error(f"조건 저장 DB 오류: {str(e)}")
            raise DatabaseConnectionError(
                connection_string=self.db.connection_string,
                inner_exception=e
            ) from e
        except Exception as e:
            logger.error(f"조건 저장 중 예상치 못한 오류: {str(e)}")
            raise InfrastructureException(
                message=f"조건 저장 실패: {str(e)}",
                error_code="CONDITION_SAVE_ERROR"
            ) from e
    
    def _insert_condition(self, condition: TradingCondition) -> TradingCondition:
        """조건 삽입 - 세부 에러 처리"""
        
        query = """
        INSERT INTO trading_conditions 
        (id, variable_id, operator, target_value, parameters, created_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with self.db.cursor() as cursor:
                cursor.execute(query, (
                    condition.id.value,
                    condition.variable.id.value,
                    condition.operator,
                    str(condition.target_value),
                    json.dumps(condition.parameters.to_dict()) if condition.parameters else '{}',
                    condition.created_at.isoformat(),
                    True
                ))
                
                if cursor.rowcount == 0:
                    raise InfrastructureException(
                        message="조건 삽입 실패: 행이 삽입되지 않았습니다",
                        error_code="INSERT_FAILED"
                    )
                
                return condition
                
        except sqlite3.Error as e:
            logger.error(f"조건 삽입 SQL 오류: {str(e)}")
            raise DatabaseConnectionError(
                connection_string=self.db.connection_string,
                inner_exception=e
            ) from e
```

## 🎨 Presentation Layer 에러 처리

### 1. UI 에러 처리
```python
# presentation/presenters/condition_presenter.py
class ConditionPresenter:
    """조건 Presenter - 에러 처리 적용"""
    
    def __init__(self, create_condition_use_case, view):
        self.create_condition_use_case = create_condition_use_case
        self.view = view
    
    def create_condition(self, variable_id: str, operator: str, target_value: str):
        """조건 생성 - UI 에러 처리"""
        
        try:
            # 입력값 기본 검증
            if not variable_id or not operator or not target_value:
                self.view.show_validation_error("모든 필드를 입력해주세요.")
                return
            
            # 대상값 타입 변환
            try:
                parsed_target_value = self._parse_target_value(target_value)
            except ValueError as e:
                self.view.show_validation_error(f"올바른 숫자를 입력해주세요: {target_value}")
                return
            
            # 유스케이스 실행
            command = CreateConditionCommand(
                variable_id=variable_id,
                operator=operator,
                target_value=parsed_target_value
            )
            
            result = self.create_condition_use_case.execute(command)
            
            if result.success:
                self.view.show_success_message("조건이 성공적으로 생성되었습니다.")
                self.view.refresh_condition_list()
            else:
                # 사용자 친화적 메시지 표시
                self.view.show_business_error(result.user_message)
                
        except ApplicationException as e:
            # 애플리케이션 레벨 오류
            logger.error(f"조건 생성 애플리케이션 오류: {str(e)}")
            self.view.show_application_error("조건 생성 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.")
            
        except InfrastructureException as e:
            # 인프라 레벨 오류
            logger.error(f"조건 생성 인프라 오류: {str(e)}")
            
            if e.retryable:
                self.view.show_retryable_error(
                    "일시적인 문제가 발생했습니다. 다시 시도하시겠습니까?",
                    retry_action=lambda: self.create_condition(variable_id, operator, target_value)
                )
            else:
                self.view.show_system_error("시스템 오류가 발생했습니다. 관리자에게 문의해주세요.")
                
        except Exception as e:
            # 예상치 못한 오류
            logger.error(f"조건 생성 중 예상치 못한 오류: {str(e)}", exc_info=True)
            self.view.show_system_error("예상치 못한 오류가 발생했습니다. 관리자에게 문의해주세요.")
    
    def _parse_target_value(self, target_value: str) -> float:
        """대상값 파싱 - 타입 변환 에러 처리"""
        try:
            # 쉼표 제거 및 공백 정리
            cleaned_value = target_value.replace(',', '').strip()
            return float(cleaned_value)
        except ValueError:
            raise ValueError(f"숫자로 변환할 수 없는 값: {target_value}")

# presentation/views/condition_view.py
class ConditionView:
    """조건 View - 에러 메시지 표시"""
    
    def show_validation_error(self, message: str):
        """유효성 검사 오류 표시"""
        QMessageBox.warning(self, "입력 오류", message)
    
    def show_business_error(self, message: str):
        """비즈니스 규칙 오류 표시"""
        QMessageBox.information(self, "알림", message)
    
    def show_application_error(self, message: str):
        """애플리케이션 오류 표시"""
        QMessageBox.warning(self, "오류", message)
    
    def show_retryable_error(self, message: str, retry_action):
        """재시도 가능한 오류 표시"""
        reply = QMessageBox.question(
            self, 
            "일시적 오류", 
            message,
            QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Retry:
            retry_action()
    
    def show_system_error(self, message: str):
        """시스템 오류 표시"""
        QMessageBox.critical(self, "시스템 오류", message)
    
    def show_success_message(self, message: str):
        """성공 메시지 표시"""
        QMessageBox.information(self, "성공", message)
```

## 📊 에러 모니터링

### 에러 수집 및 분석
```python
# shared/monitoring/error_monitor.py
class ErrorMonitor:
    """에러 모니터링 및 수집"""
    
    def __init__(self):
        self.error_stats = defaultdict(int)
        self.error_details = []
    
    def record_error(self, exception: Exception, context: dict = None):
        """에러 기록"""
        error_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'exception_type': type(exception).__name__,
            'message': str(exception),
            'context': context or {},
            'stack_trace': traceback.format_exc()
        }
        
        self.error_details.append(error_info)
        self.error_stats[error_info['exception_type']] += 1
        
        # 심각한 오류는 즉시 알림
        if self._is_critical_error(exception):
            self._send_critical_alert(error_info)
    
    def _is_critical_error(self, exception: Exception) -> bool:
        """심각한 오류 판단"""
        critical_types = [
            'DatabaseConnectionError',
            'SystemExit',
            'MemoryError'
        ]
        return type(exception).__name__ in critical_types
    
    def get_error_summary(self) -> dict:
        """에러 요약 통계"""
        return {
            'total_errors': len(self.error_details),
            'error_types': dict(self.error_stats),
            'recent_errors': self.error_details[-10:]  # 최근 10개
        }
```

## 🔍 다음 단계

- **[트레일링 스탑 구현](12_TRAILING_STOP_IMPLEMENTATION.md)**: 실제 구현 시 에러 처리 적용
- **[디버깅 가이드](15_DEBUGGING_GUIDE.md)**: 에러 진단 및 해결 방법
- **[모니터링 전략](17_MONITORING_STRATEGY.md)**: 프로덕션 에러 모니터링

---
**💡 핵심**: "각 계층에서 적절한 수준의 에러 처리를 통해 시스템의 안정성과 사용자 경험을 보장합니다!"
