# 🚨 도메인 서비스 문제해결 가이드

> **목적**: 도메인 서비스 구현 시 자주 발생하는 문제와 해결책  
> **대상**: 실무 개발자  
> **갱신**: 2025-08-04

## 🔥 자주 발생하는 문제들

### 문제 1: 순환 참조 (Circular Import)
**증상**: `ImportError: cannot import name 'StrategyCompatibilityService'`

**원인**: 엔티티와 서비스가 서로를 import
```python
# ❌ 문제 상황
# strategy.py
from domain.services.strategy_compatibility_service import StrategyCompatibilityService

# strategy_compatibility_service.py  
from domain.entities.strategy import Strategy  # 순환 참조!
```

**해결책**: 지연 import 사용
```python
# ✅ 해결 방법
class Strategy:
    def check_trigger_compatibility(self, new_trigger):
        try:
            # 메서드 내부에서 import
            from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService
            
            service = StrategyCompatibilityService()
            return service.check_compatibility(self.triggers, new_trigger)
        except ImportError:
            # 서비스 없으면 기본 동작
            return CompatibilityResult.compatible()
```

**예방법**:
- 엔티티는 서비스를 import하되, 서비스는 엔티티를 직접 import하지 않기
- 인터페이스나 추상 클래스 활용
- 의존성 주입 패턴 사용

### 문제 2: 테스트에서 Mock 실패
**증상**: `AttributeError: Mock object has no attribute 'level'`

**원인**: Value Object의 속성을 Mock이 제대로 흉내내지 못함
```python
# ❌ 문제 코드
def test_compatibility_check(self, mock_service):
    mock_service.check_variable_compatibility.return_value = Mock()
    # Mock 객체에는 .level 속성이 없음
```

**해결책**: 실제 Value Object 사용
```python
# ✅ 해결 방법
def test_compatibility_check(self):
    with patch('domain.services.strategy_compatibility_service.StrategyCompatibilityService') as MockService:
        mock_instance = MockService.return_value
        
        # 실제 Value Object 반환
        mock_instance.check_variable_compatibility.return_value = CompatibilityResult.compatible()
        
        strategy = Strategy(StrategyId("TEST"), "테스트")
        result = strategy.check_trigger_compatibility(test_trigger)
        
        assert result.level == CompatibilityLevel.COMPATIBLE
```

**예방법**:
- Mock 대신 실제 Value Object 사용
- 테스트용 팩토리 메서드 제공
- Builder 패턴으로 테스트 데이터 생성

### 문제 3: 서비스에 상태 추가하려는 유혹
**증상**: 성능을 위해 캐시를 서비스에 추가하고 싶음

**잘못된 접근**:
```python
# ❌ 상태를 가진 서비스 (잘못된 설계)
class StrategyCompatibilityService:
    def __init__(self):
        self._cache = {}  # 상태!
        
    def check_compatibility(self, vars1, var2):
        key = (tuple(vars1), var2)
        if key in self._cache:
            return self._cache[key]
        # ...
```

**올바른 해결책**:
```python
# ✅ 무상태 서비스 + 외부 캐시
class StrategyCompatibilityService:
    def __init__(self, cache_provider=None):
        self._cache_provider = cache_provider  # 외부 의존성
        
    def check_compatibility(self, vars1, var2):
        if self._cache_provider:
            cached = self._cache_provider.get(vars1, var2)
            if cached:
                return cached
        
        result = self._perform_compatibility_check(vars1, var2)
        
        if self._cache_provider:
            self._cache_provider.set(vars1, var2, result)
            
        return result
```

**예방법**:
- 캐시는 Infrastructure Layer에서 관리
- 도메인 서비스는 항상 무상태로 유지
- 의존성 주입으로 외부 서비스 활용

### 문제 4: DataFrame과 도메인 모델 변환 오류
**증상**: `KeyError: 'indicators'` 또는 `AttributeError: 'DataFrame' object has no attribute 'symbol'`

**원인**: DataFrame과 MarketData 간 데이터 구조 불일치
```python
# ❌ 문제 상황
def convert_to_market_data(self, df):
    return MarketData(
        symbol=df.symbol,  # DataFrame에 symbol 속성 없음!
        indicators=df.indicators  # 이것도 없음!
    )
```

**해결책**: 안전한 변환 로직
```python
# ✅ 해결 방법
def convert_to_market_data(self, df: pd.DataFrame) -> MarketData:
    """안전한 DataFrame → MarketData 변환"""
    
    # 속성에서 메타데이터 추출
    symbol = df.attrs.get('symbol', 'UNKNOWN')
    
    # 기본 데이터 추출
    close = df['close'].iloc[-1] if 'close' in df.columns else 0.0
    volume = df['volume'].iloc[-1] if 'volume' in df.columns else 0.0
    timestamp = df.index[-1] if len(df.index) > 0 else datetime.now()
    
    # 지표 데이터 추출 (안전하게)
    indicators = {}
    for col in df.columns:
        if col not in ['open', 'high', 'low', 'close', 'volume']:
            try:
                indicators[col] = float(df[col].iloc[-1])
            except (ValueError, IndexError):
                indicators[col] = 0.0
    
    return MarketData(
        symbol=symbol,
        timestamp=timestamp,
        close=close,
        volume=volume,
        indicators=indicators
    )
```

**예방법**:
- 변환 시 항상 기본값 제공
- try-catch로 안전하게 처리
- 변환 로직을 별도 어댑터 클래스로 분리

### 문제 5: 테스트 데이터 부족
**증상**: 테스트에서 실제 변수나 지표 데이터가 필요한데 준비가 어려움

**해결책**: 테스트 팩토리 패턴
```python
# ✅ 테스트 데이터 팩토리
class TestDataFactory:
    """테스트용 데이터 생성 팩토리"""
    
    @staticmethod
    def create_rsi_variable() -> TradingVariable:
        return TradingVariable(
            variable_id="RSI",
            display_name_ko="RSI",
            purpose_category="momentum",
            chart_category="subplot",
            comparison_group="percentage_comparable"
        )
    
    @staticmethod
    def create_close_price_variable() -> TradingVariable:
        return TradingVariable(
            variable_id="Close",
            display_name_ko="종가",
            purpose_category="price",
            chart_category="overlay",
            comparison_group="price_comparable"
        )
    
    @staticmethod
    def create_market_data_with_rsi(rsi_value: float = 50.0) -> MarketData:
        return MarketData(
            symbol="KRW-BTC",
            timestamp=datetime.now(),
            close=50000.0,
            volume=1000.0,
            indicators={"RSI": rsi_value, "MACD": 0.1}
        )
    
    @staticmethod
    def create_test_strategy() -> Strategy:
        strategy = Strategy(StrategyId("TEST"), "테스트 전략")
        # 기본 트리거 추가
        return strategy

# 테스트에서 사용
def test_compatibility_with_factory():
    rsi = TestDataFactory.create_rsi_variable()
    close = TestDataFactory.create_close_price_variable()
    
    service = StrategyCompatibilityService()
    result = service.check_variable_compatibility([close], rsi)
    
    assert result.level == CompatibilityLevel.WARNING
```

## 🔧 성능 문제 해결

### 문제: 호환성 검증이 느림
**증상**: UI에서 변수 선택 시 응답 지연

**분석**: 매번 모든 규칙을 다시 계산
```python
# ❌ 비효율적인 코드
def check_compatibility(self, existing_vars, new_var):
    # 매번 전체 규칙을 다시 로드하고 계산
    rules = self._load_all_compatibility_rules()  # 느림!
    return self._evaluate_rules(rules, existing_vars, new_var)
```

**해결책**: 규칙 캐싱과 인덱싱
```python
# ✅ 최적화된 코드
class StrategyCompatibilityService:
    def __init__(self):
        self._compatibility_matrix = self._build_compatibility_matrix()
    
    def _build_compatibility_matrix(self) -> Dict[Tuple[str, str], CompatibilityLevel]:
        """호환성 매트릭스를 미리 구성"""
        matrix = {}
        
        groups = ["price_comparable", "percentage_comparable", "zero_centered", 
                 "volume_comparable", "boolean_comparable", "custom_comparable"]
        
        for group1 in groups:
            for group2 in groups:
                if group1 == group2:
                    matrix[(group1, group2)] = CompatibilityLevel.COMPATIBLE
                elif (group1, group2) in [("price_comparable", "percentage_comparable"),
                                        ("percentage_comparable", "price_comparable")]:
                    matrix[(group1, group2)] = CompatibilityLevel.WARNING
                else:
                    matrix[(group1, group2)] = CompatibilityLevel.INCOMPATIBLE
        
        return matrix
    
    def check_variable_compatibility(self, existing_vars, new_var):
        """O(1) 시간 복잡도로 호환성 확인"""
        if not existing_vars:
            return CompatibilityResult.compatible()
        
        for existing_var in existing_vars:
            key = (existing_var.comparison_group, new_var.comparison_group)
            level = self._compatibility_matrix.get(key, CompatibilityLevel.INCOMPATIBLE)
            
            if level == CompatibilityLevel.INCOMPATIBLE:
                return CompatibilityResult.incompatible("호환되지 않는 조합")
            elif level == CompatibilityLevel.WARNING:
                return CompatibilityResult.warning("정규화 필요")
        
        return CompatibilityResult.compatible()
```

## 🧪 테스트 문제 해결

### 문제: 테스트가 다른 테스트에 영향
**증상**: 개별 테스트는 통과하지만 전체 실행 시 실패

**원인**: 전역 상태나 싱글톤 패턴
```python
# ❌ 문제 코드
class StrategyCompatibilityService:
    _instance = None
    _cache = {}  # 전역 캐시!
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**해결책**: 테스트별 독립적인 인스턴스
```python
# ✅ 해결 방법
class TestStrategyCompatibilityService:
    def setup_method(self):
        """각 테스트마다 새로운 인스턴스"""
        self.service = StrategyCompatibilityService()
        
    def teardown_method(self):
        """테스트 후 정리"""
        # 필요시 전역 상태 초기화
        pass
```

## 📊 디버깅 도구

### 로깅 활용
```python
class StrategyCompatibilityService:
    def __init__(self):
        from upbit_auto_trading.logging import get_integrated_logger
        self.logger = get_integrated_logger("StrategyCompatibilityService")
    
    def check_variable_compatibility(self, existing_vars, new_var):
        self.logger.debug(f"호환성 검사: {[v.variable_id for v in existing_vars]} + {new_var.variable_id}")
        
        result = self._perform_check(existing_vars, new_var)
        
        self.logger.info(f"호환성 결과: {result.level.value} - {result.message}")
        return result
```

### 검증 헬퍼
```python
def validate_compatibility_result(result: CompatibilityResult) -> None:
    """호환성 결과 검증 헬퍼"""
    assert isinstance(result, CompatibilityResult)
    assert isinstance(result.level, CompatibilityLevel)
    assert isinstance(result.message, str)
    assert len(result.message) > 0
    
    if result.level == CompatibilityLevel.WARNING:
        assert result.recommended_action is not None
```

## 🎯 베스트 프랙티스

### 에러 메시지 개선
```python
# ✅ 명확한 에러 메시지
def check_variable_compatibility(self, existing_vars, new_var):
    if not new_var:
        return CompatibilityResult.error("새 변수가 지정되지 않았습니다")
    
    if not hasattr(new_var, 'comparison_group'):
        return CompatibilityResult.error(f"변수 '{new_var.variable_id}'에 comparison_group이 없습니다")
    
    # 구체적인 변수명과 이유 포함
    for existing_var in existing_vars:
        if existing_var.comparison_group != new_var.comparison_group:
            return CompatibilityResult.incompatible(
                f"'{existing_var.variable_id}'({existing_var.comparison_group})와 "
                f"'{new_var.variable_id}'({new_var.comparison_group})는 호환되지 않습니다"
            )
```

### 방어적 프로그래밍
```python
def normalize(self, data: List[float], method: NormalizationMethod) -> NormalizationResult:
    """방어적 검증을 포함한 정규화"""
    
    # 입력 검증
    if not isinstance(data, list):
        return NormalizationResult.error("데이터는 리스트여야 합니다")
    
    if not all(isinstance(x, (int, float)) for x in data):
        return NormalizationResult.error("모든 데이터는 숫자여야 합니다")
    
    if len(data) < 2:
        return NormalizationResult.error("최소 2개의 데이터가 필요합니다")
    
    # 실제 처리
    try:
        result = self._perform_normalization(data, method)
        return NormalizationResult.success(result)
    except Exception as e:
        return NormalizationResult.error(f"정규화 중 오류 발생: {e}")
```

---

**🎯 핵심**: 문제는 예방이 최고의 해결책입니다. 방어적 프로그래밍과 명확한 에러 메시지로 디버깅 시간을 줄이세요!

**📚 추가 학습**: [실무 경험](./01_domain_service_work_experience.md)과 [구현 가이드](./02_implementation_guide.md)를 다시 읽어보세요.
