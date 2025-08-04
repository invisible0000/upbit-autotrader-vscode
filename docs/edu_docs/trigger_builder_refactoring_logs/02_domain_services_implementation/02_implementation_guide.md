# 🔧 도메인 서비스 구현 가이드

> **목적**: 도메인 서비스 구현의 실용적 가이드  
> **대상**: 실무 개발자  
> **갱신**: 2025-08-04

## 🎯 구현 체크리스트

### 기본 설정
- [ ] `domain/services/` 폴더 생성
- [ ] `__init__.py`에 서비스 export
- [ ] `domain/value_objects/` 폴더에 결과 객체 준비

### 서비스 구현
- [ ] **무상태 클래스**: 인스턴스 변수 없음
- [ ] **명확한 메서드명**: 동사 + 명사 조합
- [ ] **Value Object 반환**: 원시 타입 대신 도메인 객체
- [ ] **예외 처리**: 비즈니스 예외와 기술 예외 구분

## 🛠️ 핵심 구현 패턴

### 패턴 1: 호환성 검증 서비스
```python
class StrategyCompatibilityService:
    """매매 변수 호환성 검증 전문 서비스"""
    
    def check_variable_compatibility(self, 
                                   existing_vars: List[TradingVariable],
                                   new_var: TradingVariable) -> CompatibilityResult:
        """
        3단계 호환성 검증:
        1. 직접 호환성 (같은 comparison_group)
        2. 정규화 호환성 (price ↔ percentage)  
        3. 완전 비호환
        """
        
        # 1. 직접 호환성 검사
        if self._is_directly_compatible(existing_vars, new_var):
            return CompatibilityResult.compatible()
        
        # 2. 정규화 가능성 검사
        if self._can_be_normalized(existing_vars, new_var):
            return CompatibilityResult.warning(
                "정규화를 통해 비교 가능합니다",
                recommended_action="normalize"
            )
        
        # 3. 완전 비호환
        return CompatibilityResult.incompatible(
            "호환되지 않는 변수 조합입니다"
        )
    
    def _is_directly_compatible(self, existing_vars, new_var) -> bool:
        """같은 comparison_group인지 확인"""
        if not existing_vars:
            return True
        
        return all(
            var.comparison_group == new_var.comparison_group 
            for var in existing_vars
        )
    
    def _can_be_normalized(self, existing_vars, new_var) -> bool:
        """정규화 가능한 조합인지 확인"""
        normalization_pairs = [
            ("price_comparable", "percentage_comparable"),
            ("percentage_comparable", "price_comparable")
        ]
        
        for existing_var in existing_vars:
            pair = (existing_var.comparison_group, new_var.comparison_group)
            if pair in normalization_pairs:
                return True
        
        return False
```

### 패턴 2: 평가 서비스 (어댑터 활용)
```python
class TriggerEvaluationService:
    """트리거 조건 평가 서비스"""
    
    def evaluate_trigger(self, 
                        trigger: Trigger, 
                        market_data: MarketData) -> EvaluationResult:
        """
        기존 시스템과 호환성 유지하면서 새로운 도메인 모델 지원
        """
        try:
            # 기존 DataFrame 기반 로직 재활용
            df_data = self._convert_to_dataframe(market_data)
            legacy_result = trigger.evaluate(df_data)
            
            # 새로운 도메인 모델로 변환
            return self._convert_to_domain_result(legacy_result)
            
        except Exception as e:
            return EvaluationResult.error(f"평가 실패: {e}")
    
    def _convert_to_dataframe(self, market_data: MarketData) -> pd.DataFrame:
        """MarketData를 DataFrame으로 변환"""
        data = {
            'close': [market_data.close],
            'volume': [market_data.volume],
            **market_data.indicators
        }
        
        df = pd.DataFrame(data, index=[market_data.timestamp])
        df.attrs['symbol'] = market_data.symbol
        return df
    
    def _convert_to_domain_result(self, legacy_result) -> EvaluationResult:
        """기존 결과를 도메인 모델로 변환"""
        if hasattr(legacy_result, 'success') and legacy_result.success:
            return EvaluationResult.success(
                result=legacy_result.result,
                value=legacy_result.actual_value,
                target_value=legacy_result.target_value
            )
        else:
            return EvaluationResult.failure(
                message=getattr(legacy_result, 'message', '평가 실패')
            )
```

### 패턴 3: Strategy 패턴 서비스
```python
class NormalizationService:
    """정규화 알고리즘 서비스"""
    
    def __init__(self):
        self._strategies = {
            NormalizationMethod.MIN_MAX: self._min_max_normalize,
            NormalizationMethod.Z_SCORE: self._z_score_normalize,
            NormalizationMethod.ROBUST: self._robust_normalize
        }
    
    def normalize(self, 
                 data: List[float], 
                 method: NormalizationMethod) -> NormalizationResult:
        """데이터 정규화 실행"""
        
        if not data:
            return NormalizationResult.error("빈 데이터")
        
        if len(data) < 2:
            return NormalizationResult.error("최소 2개 데이터 필요")
        
        strategy_func = self._strategies.get(method)
        if not strategy_func:
            return NormalizationResult.error(f"지원하지 않는 방법: {method}")
        
        try:
            normalized_data = strategy_func(data)
            confidence = self._calculate_confidence(data, normalized_data)
            
            return NormalizationResult.success(
                normalized_data=normalized_data,
                method=method,
                confidence=confidence
            )
        except Exception as e:
            return NormalizationResult.error(f"정규화 실패: {e}")
    
    def _min_max_normalize(self, data: List[float]) -> List[float]:
        """Min-Max 정규화: (x - min) / (max - min)"""
        min_val, max_val = min(data), max(data)
        if min_val == max_val:
            return [0.5] * len(data)  # 모든 값이 같으면 중간값
        
        return [(x - min_val) / (max_val - min_val) for x in data]
    
    def _z_score_normalize(self, data: List[float]) -> List[float]:
        """Z-Score 정규화: (x - mean) / std"""
        mean_val = sum(data) / len(data)
        variance = sum((x - mean_val) ** 2 for x in data) / len(data)
        std_val = variance ** 0.5
        
        if std_val == 0:
            return [0.0] * len(data)  # 표준편차가 0이면 모두 평균
        
        return [(x - mean_val) / std_val for x in data]
    
    def _calculate_confidence(self, original, normalized) -> float:
        """정규화 품질 점수 계산"""
        if len(original) < 10:
            return 0.7  # 데이터 부족
        
        # 분포 유지도 검사
        original_range = max(original) - min(original)
        if original_range == 0:
            return 0.5  # 모든 값이 같음
        
        return min(0.95, 0.8 + (len(original) / 1000) * 0.15)
```

## 📊 Value Objects 구현

### CompatibilityResult
```python
@dataclass(frozen=True)
class CompatibilityResult:
    """호환성 검증 결과"""
    level: CompatibilityLevel
    message: str
    recommended_action: Optional[str] = None
    
    @classmethod
    def compatible(cls) -> 'CompatibilityResult':
        return cls(CompatibilityLevel.COMPATIBLE, "호환 가능")
    
    @classmethod
    def warning(cls, message: str, action: str = None) -> 'CompatibilityResult':
        return cls(CompatibilityLevel.WARNING, message, action)
    
    @classmethod
    def incompatible(cls, message: str) -> 'CompatibilityResult':
        return cls(CompatibilityLevel.INCOMPATIBLE, message)
    
    @property
    def is_usable(self) -> bool:
        """사용 가능한 수준인지 확인"""
        return self.level in [CompatibilityLevel.COMPATIBLE, CompatibilityLevel.WARNING]
```

### EvaluationResult
```python
@dataclass(frozen=True)
class EvaluationResult:
    """트리거 평가 결과"""
    status: EvaluationStatus
    result: Optional[bool] = None
    value: Optional[float] = None
    target_value: Optional[float] = None
    message: str = ""
    
    @classmethod
    def success(cls, result: bool, value: float, target_value: float) -> 'EvaluationResult':
        return cls(EvaluationStatus.SUCCESS, result, value, target_value)
    
    @classmethod
    def failure(cls, message: str) -> 'EvaluationResult':
        return cls(EvaluationStatus.FAILURE, message=message)
    
    @classmethod
    def error(cls, message: str) -> 'EvaluationResult':
        return cls(EvaluationStatus.ERROR, message=message)
```

## 🧪 테스트 구현 가이드

### 기본 테스트 구조
```python
class TestStrategyCompatibilityService:
    """호환성 서비스 테스트"""
    
    def setup_method(self):
        """각 테스트 전 실행"""
        self.service = StrategyCompatibilityService()
        
        # 테스트용 변수들
        self.rsi = TradingVariable("RSI", "RSI", "momentum", "subplot", "percentage_comparable")
        self.stochastic = TradingVariable("Stochastic", "스토캐스틱", "momentum", "subplot", "percentage_comparable")
        self.close_price = TradingVariable("Close", "종가", "price", "overlay", "price_comparable")
        self.macd = TradingVariable("MACD", "MACD", "momentum", "subplot", "zero_centered")
    
    def test_compatible_variables_same_group(self):
        """같은 그룹 변수들의 호환성 테스트"""
        result = self.service.check_variable_compatibility([self.rsi], self.stochastic)
        
        assert result.level == CompatibilityLevel.COMPATIBLE
        assert result.is_usable
        assert "호환 가능" in result.message
    
    def test_normalization_warning(self):
        """정규화 경고 상황 테스트"""
        result = self.service.check_variable_compatibility([self.close_price], self.rsi)
        
        assert result.level == CompatibilityLevel.WARNING
        assert result.is_usable
        assert "정규화" in result.message
        assert result.recommended_action == "normalize"
    
    def test_incompatible_variables(self):
        """비호환 변수 테스트"""
        result = self.service.check_variable_compatibility([self.rsi], self.macd)
        
        assert result.level == CompatibilityLevel.INCOMPATIBLE
        assert not result.is_usable
        assert "호환되지 않는" in result.message
```

## 🔧 엔티티-서비스 통합

### Strategy 엔티티 확장
```python
class Strategy:
    """전략 엔티티에 서비스 연동"""
    
    def check_trigger_compatibility(self, new_trigger: Trigger) -> CompatibilityResult:
        """새 트리거 추가 시 호환성 검증"""
        try:
            # 지연 import로 순환 참조 방지
            from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService
            
            service = StrategyCompatibilityService()
            existing_variables = self._extract_variables_from_triggers()
            new_variables = new_trigger.get_variables()
            
            for new_var in new_variables:
                result = service.check_variable_compatibility(existing_variables, new_var)
                if result.level == CompatibilityLevel.INCOMPATIBLE:
                    return result
            
            return CompatibilityResult.compatible()
            
        except ImportError:
            # 서비스를 사용할 수 없으면 기본 동작
            return CompatibilityResult.compatible()
    
    def _extract_variables_from_triggers(self) -> List[TradingVariable]:
        """기존 트리거들에서 변수 추출"""
        variables = []
        for trigger in self.triggers:
            variables.extend(trigger.get_variables())
        return variables
```

## 📚 실무 팁

### 성능 최적화
- **캐싱**: 반복 계산 결과 캐시
- **지연 계산**: 필요할 때만 복잡한 계산 수행
- **배치 처리**: 여러 항목을 한 번에 처리

### 에러 처리
- **비즈니스 예외**: 도메인 규칙 위반
- **기술적 예외**: 시스템 오류
- **명확한 메시지**: 사용자가 이해할 수 있는 설명

### 확장성 고려
- **인터페이스 분리**: 구현과 인터페이스 분리
- **플러그인 패턴**: 새로운 알고리즘 추가 용이
- **설정 외부화**: 하드코딩된 값 피하기

---

**🎯 핵심**: 도메인 서비스는 "비즈니스 로직의 전문가"입니다. 단순하고 명확하게 유지하세요!

**🔍 다음 단계**: [문제해결 가이드](./03_troubleshooting_guide.md)에서 자주 발생하는 문제들을 확인하세요.
