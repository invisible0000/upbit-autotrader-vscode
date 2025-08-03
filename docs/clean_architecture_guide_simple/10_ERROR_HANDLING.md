# 🚨 에러 처리 가이드

> **목적**: Clean Architecture에서 체계적인 에러 처리 및 복구 전략  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 🎯 에러 처리 철학

### 계층별 에러 처리 책임
```
🎨 Presentation  → 사용자 친화적 에러 메시지
⚙️ Application   → 유스케이스 실패 처리 및 복구
💎 Domain        → 비즈니스 규칙 위반 감지
🔌 Infrastructure → 외부 의존성 에러 변환
```

### 핵심 원칙
- **실패 빠르게**: 문제 발생 시 즉시 감지
- **명확한 메시지**: 문제 원인과 해결 방법 제시
- **복구 전략**: 가능한 경우 자동 복구 수행

## 💎 Domain Layer 에러 처리

### 도메인 예외 기본 클래스
```python
class DomainException(Exception):
    """도메인 계층 기본 예외"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> dict:
        return {
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }
```

### 구체적 도메인 예외들
```python
class BusinessRuleViolationException(DomainException):
    """비즈니스 규칙 위반 예외"""
    def __init__(self, rule_name: str, violation_details: str):
        super().__init__(
            message=f"비즈니스 규칙 위반: {rule_name}",
            error_code="BUSINESS_RULE_VIOLATION",
            details={"rule": rule_name, "violation": violation_details}
        )

class InvalidStrategyException(DomainException):
    """잘못된 전략 예외"""
    def __init__(self, strategy_id: str, reason: str):
        super().__init__(
            message=f"잘못된 전략 설정: {reason}",
            error_code="INVALID_STRATEGY",
            details={"strategy_id": strategy_id, "reason": reason}
        )

class IncompatibleVariableException(DomainException):
    """변수 호환성 위반 예외"""
    def __init__(self, var1: str, var2: str):
        super().__init__(
            message=f"호환되지 않는 변수 조합: {var1}과 {var2}",
            error_code="INCOMPATIBLE_VARIABLES",
            details={"variable1": var1, "variable2": var2}
        )
```

### Entity에서 에러 처리
```python
class Strategy:
    """전략 Entity - 비즈니스 규칙 검증"""
    def add_rule(self, rule: TradingRule):
        """규칙 추가 with 검증"""
        # 1. 비즈니스 규칙 검증
        if len(self.rules) >= 10:
            raise BusinessRuleViolationException(
                rule_name="최대_규칙_제한",
                violation_details=f"현재 {len(self.rules)}개, 최대 10개까지 허용"
            )
            
        # 2. 호환성 검증
        if not self._is_compatible_rule(rule):
            raise IncompatibleVariableException(
                var1=self.rules[-1].variable_id if self.rules else "none",
                var2=rule.variable_id
            )
            
        # 3. 성공 시 규칙 추가
        self.rules.append(rule)
        
    def _is_compatible_rule(self, rule: TradingRule) -> bool:
        """규칙 호환성 검사"""
        if not self.rules:
            return True
            
        # 복잡한 호환성 로직...
        return True
```

## ⚙️ Application Layer 에러 처리

### Application 예외 클래스
```python
class ApplicationException(Exception):
    """Application 계층 예외"""
    def __init__(self, message: str, inner_exception: Exception = None):
        super().__init__(message)
        self.message = message
        self.inner_exception = inner_exception
        
class UseCaseException(ApplicationException):
    """유스케이스 실행 실패"""
    pass
    
class ValidationException(ApplicationException):
    """입력 데이터 검증 실패"""
    def __init__(self, field_name: str, validation_message: str):
        super().__init__(f"검증 실패: {field_name} - {validation_message}")
        self.field_name = field_name
        self.validation_message = validation_message
```

### Service에서 에러 처리 및 변환
```python
class StrategyService:
    """전략 서비스 - 에러 처리 및 변환"""
    def __init__(self, strategy_repo, logger):
        self.strategy_repo = strategy_repo
        self.logger = logger
        
    def create_strategy(self, command: CreateStrategyCommand) -> Result[str]:
        """전략 생성 with 에러 처리"""
        try:
            # 1. 입력 검증
            self._validate_command(command)
            
            # 2. 도메인 로직 실행
            strategy = Strategy(command.name)
            for rule_data in command.rules:
                rule = TradingRule.from_dict(rule_data)
                strategy.add_rule(rule)  # DomainException 발생 가능
                
            # 3. 영속화
            strategy_id = self.strategy_repo.save(strategy)
            
            self.logger.info(f"✅ 전략 생성 성공: {strategy_id}")
            return Result.success(strategy_id)
            
        except DomainException as e:
            # 도메인 예외 → Application 예외로 변환
            self.logger.warning(f"⚠️ 전략 생성 실패: {e.message}")
            return Result.failure(
                UseCaseException(f"전략 생성 실패: {e.message}", e)
            )
            
        except Exception as e:
            # 예상치 못한 예외
            self.logger.error(f"❌ 전략 생성 중 예상치 못한 오류: {e}")
            return Result.failure(
                UseCaseException("시스템 오류가 발생했습니다", e)
            )
            
    def _validate_command(self, command: CreateStrategyCommand):
        """입력 명령 검증"""
        if not command.name or len(command.name.strip()) == 0:
            raise ValidationException("name", "전략 이름은 필수입니다")
            
        if len(command.name) > 50:
            raise ValidationException("name", "전략 이름은 50자 이하로 입력하세요")
            
        if not command.rules or len(command.rules) == 0:
            raise ValidationException("rules", "최소 1개 이상의 규칙이 필요합니다")
```

### Result 패턴으로 에러 처리
```python
from typing import Generic, TypeVar, Union
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Result(Generic[T]):
    """성공/실패 결과를 나타내는 클래스"""
    is_success: bool
    value: T = None
    error: Exception = None
    
    @classmethod
    def success(cls, value: T) -> 'Result[T]':
        return cls(is_success=True, value=value)
        
    @classmethod
    def failure(cls, error: Exception) -> 'Result[T]':
        return cls(is_success=False, error=error)
        
    def map(self, func) -> 'Result':
        """성공 시에만 함수 적용"""
        if self.is_success:
            try:
                return Result.success(func(self.value))
            except Exception as e:
                return Result.failure(e)
        return self
        
    def or_else(self, default_value: T) -> T:
        """실패 시 기본값 반환"""
        return self.value if self.is_success else default_value

# 사용 예시
def handle_strategy_creation():
    result = strategy_service.create_strategy(command)
    
    if result.is_success:
        strategy_id = result.value
        print(f"전략 생성 성공: {strategy_id}")
    else:
        error_message = result.error.message
        print(f"전략 생성 실패: {error_message}")
```

## 🔌 Infrastructure Layer 에러 처리

### Infrastructure 예외 클래스
```python
class InfrastructureException(Exception):
    """Infrastructure 계층 예외"""
    pass
    
class DatabaseException(InfrastructureException):
    """데이터베이스 관련 예외"""
    pass
    
class NetworkException(InfrastructureException):
    """네트워크 관련 예외"""
    pass
```

### Repository 에러 처리
```python
class SqliteStrategyRepository:
    """SQLite 전략 리포지토리 - 에러 처리"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def save(self, strategy: Strategy) -> str:
        """전략 저장 with 에러 처리"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 전략 저장
                cursor.execute(
                    "INSERT INTO strategies (id, name, created_at) VALUES (?, ?, ?)",
                    (strategy.id, strategy.name, datetime.utcnow())
                )
                
                # 규칙들 저장
                for rule in strategy.rules:
                    cursor.execute(
                        "INSERT INTO strategy_rules (strategy_id, rule_data) VALUES (?, ?)",
                        (strategy.id, rule.to_json())
                    )
                    
                conn.commit()
                return strategy.id
                
        except sqlite3.IntegrityError as e:
            raise DatabaseException(f"전략 저장 실패: 중복된 ID {strategy.id}")
            
        except sqlite3.OperationalError as e:
            raise DatabaseException(f"데이터베이스 연결 실패: {e}")
            
        except Exception as e:
            raise DatabaseException(f"알 수 없는 데이터베이스 오류: {e}")
            
    def get_by_id(self, strategy_id: str) -> Strategy:
        """전략 조회 with 에러 처리"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 전략 조회
                cursor.execute(
                    "SELECT * FROM strategies WHERE id = ?", (strategy_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    raise DatabaseException(f"전략을 찾을 수 없습니다: {strategy_id}")
                    
                strategy = Strategy(row['name'])
                strategy.id = row['id']
                
                # 규칙들 조회
                cursor.execute(
                    "SELECT rule_data FROM strategy_rules WHERE strategy_id = ?",
                    (strategy_id,)
                )
                for rule_row in cursor.fetchall():
                    rule = TradingRule.from_json(rule_row['rule_data'])
                    strategy.rules.append(rule)
                    
                return strategy
                
        except sqlite3.Error as e:
            raise DatabaseException(f"전략 조회 실패: {e}")
```

### API 클라이언트 에러 처리
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class UpbitApiClient:
    """업비트 API 클라이언트 - 에러 처리 및 재시도"""
    def __init__(self):
        self.session = requests.Session()
        self._setup_retry_strategy()
        
    def _setup_retry_strategy(self):
        """재시도 전략 설정"""
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def get_market_data(self, symbol: str) -> MarketData:
        """시장 데이터 조회 with 에러 처리"""
        try:
            url = f"https://api.upbit.com/v1/ticker?markets={symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 404:
                raise NetworkException(f"존재하지 않는 심볼: {symbol}")
            elif response.status_code == 429:
                raise NetworkException("API 호출 한도 초과")
            elif response.status_code >= 400:
                raise NetworkException(f"API 오류: {response.status_code}")
                
            data = response.json()
            return MarketData.from_api_response(data[0])
            
        except requests.exceptions.Timeout:
            raise NetworkException("API 응답 시간 초과")
        except requests.exceptions.ConnectionError:
            raise NetworkException("네트워크 연결 실패")
        except requests.exceptions.RequestException as e:
            raise NetworkException(f"API 요청 실패: {e}")
```

## 🎨 Presentation Layer 에러 처리

### Presenter 에러 처리
```python
class StrategyBuilderPresenter:
    """전략 빌더 Presenter - 사용자 친화적 에러 처리"""
    def __init__(self, view, strategy_service):
        self.view = view
        self.strategy_service = strategy_service
        
    def create_strategy(self, strategy_data: dict):
        """전략 생성 - 에러를 사용자 메시지로 변환"""
        try:
            # 입력 데이터 변환
            command = CreateStrategyCommand.from_dict(strategy_data)
            
            # 서비스 호출
            result = self.strategy_service.create_strategy(command)
            
            if result.is_success:
                self.view.show_success_message("전략이 성공적으로 생성되었습니다!")
                self.view.refresh_strategy_list()
            else:
                self._handle_service_error(result.error)
                
        except Exception as e:
            self.view.show_error_message("예상치 못한 오류가 발생했습니다")
            print(f"Presenter 오류: {e}")  # 개발자용 로그
            
    def _handle_service_error(self, error: Exception):
        """서비스 에러를 사용자 메시지로 변환"""
        if isinstance(error, ValidationException):
            self.view.show_validation_error(error.field_name, error.validation_message)
            
        elif isinstance(error, UseCaseException):
            if "비즈니스 규칙 위반" in str(error):
                self.view.show_warning_message("입력하신 설정에 문제가 있습니다. 규칙을 확인해주세요.")
            elif "호환되지 않는 변수" in str(error):
                self.view.show_warning_message("선택하신 변수들은 함께 사용할 수 없습니다.")
            else:
                self.view.show_error_message("전략 생성에 실패했습니다.")
                
        else:
            self.view.show_error_message("시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
```

### UI 에러 표시
```python
class StrategyBuilderView(QWidget):
    """전략 빌더 View - 에러 UI 표시"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def show_success_message(self, message: str):
        """성공 메시지 표시"""
        QMessageBox.information(self, "성공", message)
        
    def show_error_message(self, message: str):
        """에러 메시지 표시"""
        QMessageBox.critical(self, "오류", message)
        
    def show_warning_message(self, message: str):
        """경고 메시지 표시"""
        QMessageBox.warning(self, "주의", message)
        
    def show_validation_error(self, field_name: str, error_message: str):
        """필드별 검증 에러 표시"""
        # 해당 필드에 빨간 테두리 표시
        field_widget = self.findChild(QWidget, field_name)
        if field_widget:
            field_widget.setStyleSheet("border: 2px solid red;")
            
        # 툴팁으로 에러 메시지 표시
        field_widget.setToolTip(error_message)
        
        # 에러 라벨 업데이트
        error_label = self.findChild(QLabel, f"{field_name}_error")
        if error_label:
            error_label.setText(error_message)
            error_label.setStyleSheet("color: red;")
```

## 🔄 전역 에러 처리

### 전역 에러 핸들러
```python
class GlobalErrorHandler:
    """전역 에러 처리기"""
    def __init__(self, logger):
        self.logger = logger
        
    def handle_unhandled_exception(self, exc_type, exc_value, exc_traceback):
        """처리되지 않은 예외 처리"""
        if issubclass(exc_type, KeyboardInterrupt):
            # 사용자가 의도적으로 종료
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        error_msg = f"처리되지 않은 예외: {exc_type.__name__}: {exc_value}"
        self.logger.critical(error_msg, exc_info=(exc_type, exc_value, exc_traceback))
        
        # 사용자에게 친화적 메시지 표시
        QMessageBox.critical(
            None, 
            "시스템 오류", 
            "예상치 못한 오류가 발생했습니다.\n프로그램을 재시작해주세요."
        )

# 전역 에러 핸들러 설정
error_handler = GlobalErrorHandler(logger)
sys.excepthook = error_handler.handle_unhandled_exception
```

### 에러 복구 전략
```python
class ErrorRecoveryManager:
    """에러 복구 관리자"""
    def __init__(self):
        self.recovery_strategies = {}
        
    def register_recovery_strategy(self, error_type: type, strategy: callable):
        """복구 전략 등록"""
        self.recovery_strategies[error_type] = strategy
        
    def attempt_recovery(self, error: Exception) -> bool:
        """에러 복구 시도"""
        error_type = type(error)
        
        if error_type in self.recovery_strategies:
            try:
                self.recovery_strategies[error_type](error)
                return True
            except Exception as recovery_error:
                print(f"복구 실패: {recovery_error}")
                
        return False

# 복구 전략 등록 예시
def recover_from_database_error(error: DatabaseException):
    """데이터베이스 에러 복구"""
    # 데이터베이스 재연결 시도
    pass

def recover_from_network_error(error: NetworkException):
    """네트워크 에러 복구"""
    # 캐시된 데이터 사용
    pass

recovery_manager = ErrorRecoveryManager()
recovery_manager.register_recovery_strategy(DatabaseException, recover_from_database_error)
recovery_manager.register_recovery_strategy(NetworkException, recover_from_network_error)
```

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): 전체 아키텍처와 에러 처리 위치
- [계층별 책임](02_LAYER_RESPONSIBILITIES.md): 각 계층의 에러 처리 책임
- [문제 해결](06_TROUBLESHOOTING.md): 일반적인 에러 해결 방법
- [성능 최적화](09_PERFORMANCE_OPTIMIZATION.md): 에러 처리 성능 고려사항

---
**💡 핵심**: "에러는 숨기지 말고 적절한 계층에서 변환하여 사용자에게 유용한 정보를 제공하세요!"
