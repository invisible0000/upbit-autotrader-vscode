# 🚨 DDD 기반 에러 처리 및 폴백 제거 정책

## 🎯 핵심 철학

**"종기의 고름을 뺀다" - Domain Layer에서 발생하는 에러를 숨기지 말고 명확히 드러내라**

### DDD 계층별 에러 처리 원칙
- **Domain Layer**: Business Rule 위반 시 명확한 Domain Exception 발생
- **Application Layer**: Use Case 실패 시 구체적인 Application Exception 전파
- **Infrastructure Layer**: 외부 의존성 실패 시 Infrastructure Exception으로 래핑
- **Presentation Layer**: 사용자 친화적 에러 메시지로 변환

## ❌ 금지되는 DDD 폴백 패턴

### 1. Domain Service Import 에러 숨기기
```python
# ❌ 절대 금지 - Domain Service 로드 실패 숨김
try:
    from domain.services.strategy_validation_service import StrategyValidationService
except ImportError:
    class StrategyValidationService:  # 더미 Domain Service
        def validate_strategy(self, strategy):
            return ValidationResult.success()  # 검증 실패 숨김

# ✅ 올바른 방식 - Domain Layer 에러 즉시 노출
from domain.services.strategy_validation_service import StrategyValidationService
# 실패하면 즉시 ModuleNotFoundError → Domain Layer 구조 문제 파악
```

### 2. Business Logic 폴백
```python
# ❌ Domain Rule 위반 숨김
class StrategyEntity:
    def add_rule(self, rule: TradingRule) -> None:
        try:
            self._validate_rule_compatibility(rule)
            self._rules.append(rule)
        except DomainRuleViolationError:
            pass  # 호환성 문제 무시하고 추가 - 위험!

# ✅ Domain Exception 명확히 전파
class StrategyEntity:
    def add_rule(self, rule: TradingRule) -> None:
        self._validate_rule_compatibility(rule)  # 실패 시 즉시 Exception
        self._rules.append(rule)
```

### 3. Repository 폴백
```python
# ❌ Infrastructure 실패 숨김
class StrategyRepository:
    def save(self, strategy: Strategy) -> StrategyId:
        try:
            return self._db_repository.save(strategy)
        except DatabaseError:
            return StrategyId.generate()  # 저장 실패했는데 성공한 것처럼 행동

# ✅ Infrastructure Exception 전파
class StrategyRepository:
    def save(self, strategy: Strategy) -> StrategyId:
        try:
            return self._db_repository.save(strategy)
        except DatabaseError as e:
            raise RepositoryError(f"Strategy 저장 실패: {e}") from e
```

## ✅ 허용되는 최소 예외 처리

### 1. UI 구조 보존 (최소한의 안전성)
```python
# ✅ 허용: UI가 완전히 깨지지 않도록 최소 구조만 제공
try:
    self.chart_widget = ChartWidget()
except Exception as e:
    self.logger.error(f"❌ 차트 위젯 로드 실패: {e}")
    # 기능은 없지만 UI 구조는 유지
    self.chart_widget = QLabel("차트 로드 실패 - 로그 확인 요망")
```

### 2. 외부 의존성 (선택적 기능)
```python
# ✅ 허용: 외부 라이브러리 등 선택적 기능
try:
    import matplotlib.pyplot as plt
    CHART_AVAILABLE = True
except ImportError:
    CHART_AVAILABLE = False
    # 기능 자체를 비활성화하고 사용자에게 알림
```

### 3. 네트워크/파일 접근 (외부 리소스)
```python
# ✅ 허용: 네트워크나 파일 등 외부 요인
try:
    data = self.api_client.fetch_market_data()
except ConnectionError as e:
    self.logger.warning(f"⚠️ 시장 데이터 로드 실패: {e}")
    # 명확한 에러 상태 표시
    raise APIConnectionError("업비트 API 연결 실패") from e
```

## 🔧 올바른 에러 처리 패턴

### 1. 명확한 에러 메시지
```python
class ValidationError(Exception):
    """검증 실패 시 발생하는 예외"""
    pass

def validate_strategy_config(config):
    if not config.get('entry_strategy'):
        raise ValidationError("진입 전략이 설정되지 않았습니다")
    
    if not config.get('management_strategies'):
        raise ValidationError("관리 전략이 하나도 설정되지 않았습니다")
```

### 2. 계층적 에러 처리
```python
# 하위 레벨: 구체적 에러
def save_to_database(data):
    try:
        self.db.execute(query, params)
    except sqlite3.Error as e:
        raise DatabaseError(f"전략 저장 실패: {e}") from e

# 상위 레벨: 사용자 친화적 에러
def save_strategy(strategy_data):
    try:
        save_to_database(strategy_data)
    except DatabaseError as e:
        self.show_error_dialog("전략 저장에 실패했습니다", str(e))
        raise  # 상위로 전파
```

### 3. 로깅과 함께하는 에러 처리
```python
def load_trading_variables():
    try:
        variables = self.db.fetch_all_variables()
        self.logger.info(f"✅ 트레이딩 변수 {len(variables)}개 로드 완료")
        return variables
    except Exception as e:
        self.logger.error(f"❌ 트레이딩 변수 로드 실패: {e}")
        raise TradingVariableError("변수 정의를 불러올 수 없습니다") from e
```

## 🧪 에러 상황 테스트

### 개발 중 확인사항
- [ ] **Import 에러**: 잘못된 경로로 import 시 즉시 실패하는가?
- [ ] **DB 연결 실패**: 데이터베이스 없을 때 명확한 에러 메시지 표시하는가?
- [ ] **파라미터 오류**: 잘못된 파라미터 전달 시 구체적인 검증 메시지 제공하는가?
- [ ] **UI 컴포넌트 오류**: 필수 UI 요소 로드 실패 시 즉시 표시되는가?

### 테스트 케이스 예시
```python
def test_no_fallback_behavior():
    """폴백 코드 없이 정확한 에러 발생 테스트"""
    
    # 잘못된 DB 경로
    with pytest.raises(DatabaseError):
        manager = DatabaseManager("nonexistent.db")
    
    # 잘못된 변수 ID
    with pytest.raises(ValidationError):
        validator.check_variable_compatibility("INVALID_VAR", "RSI")
    
    # 필수 파라미터 누락
    with pytest.raises(ValueError):
        strategy = RSIStrategy()  # period 파라미터 없음
```

## 🚀 디버깅 효율성

### Before (폴백 코드 있을 때)
1. 문제 발생 → 폴백으로 숨겨짐
2. 개발자는 다른 곳에서 문제 찾음
3. 시간 낭비 후 우연히 폴백 코드 발견
4. 실제 문제 파악까지 오랜 시간 소요

### After (폴백 제거 후)
1. 문제 발생 → 즉시 명확한 에러 메시지
2. 에러 메시지에서 정확한 위치와 원인 파악
3. 직접적인 문제 해결
4. 개발 시간 대폭 단축

## 📚 관련 문서

- [개발 체크리스트](DEV_CHECKLIST.md): 에러 처리 검증 항목
- [개발 가이드](DEVELOPMENT_GUIDE_COMPACT.md): 코딩 표준과 예외 처리
- [로깅 시스템](LOGGING_SYSTEM.md): 에러 로깅 패턴

---
**💡 핵심**: "문제를 숨기지 말고 빠르게 해결하자!"
