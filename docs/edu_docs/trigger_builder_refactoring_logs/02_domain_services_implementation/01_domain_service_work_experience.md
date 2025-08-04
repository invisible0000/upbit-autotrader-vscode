# 🛠️ 도메인 서비스 구현 실무 경험

> **목적**: TASK-20250803-02 실제 구현 과정과 경험 공유  
> **대상**: 중급 개발자, DDD 실무자  
> **갱신**: 2025-08-04

## 📊 프로젝트 개요

### 구현 목표
- UI에 분산된 호환성 검증 로직을 도메인 서비스로 중앙화
- 기존 트리거 평가 시스템과 새로운 도메인 모델 통합
- DDD 아키텍처 완성: 엔티티 → 서비스 위임 패턴

### 최종 성과
- **도메인 서비스**: 3개 구현 (호환성, 평가, 정규화)
- **단위 테스트**: 63개 (100% 통과)
- **구현 시간**: 3일 (설계 1일, 구현 1일, 테스트 1일)

## 🎯 핵심 구현 결정들

### 결정 1: 호환성 서비스 설계
```python
# 문제: UI에 분산된 호환성 검증 로직
# 기존: compatibility_validator.py (752줄) - UI + DB 결합

# 해결: 순수 도메인 서비스
class StrategyCompatibilityService:
    def check_variable_compatibility(self, existing_vars, new_var):
        # 3단계 호환성 검증
        # 1. 같은 그룹 → COMPATIBLE
        # 2. 정규화 가능 → WARNING  
        # 3. 완전 비호환 → INCOMPATIBLE
```

**왜 이렇게 했는가?**
- UI 계층에 752줄의 복잡한 검증 로직이 DB와 강결합
- 비즈니스 규칙이 여러 UI 컴포넌트에 중복 분산
- 테스트하기 어려운 구조

**결과**:
- 310줄의 순수 도메인 서비스로 압축
- 21개 단위 테스트로 완전 검증
- UI에서 간단한 서비스 호출로 변경

### 결정 2: 기존 시스템과의 통합 방식
```python
# 문제: DataFrame 기반 기존 시스템 vs 새로운 도메인 모델

# 해결: 어댑터 패턴 활용
class TriggerEvaluationService:
    def evaluate_trigger(self, trigger: Trigger, market_data: MarketData):
        try:
            # 기존 로직 재활용
            df_data = market_data.to_dataframe()
            legacy_result = trigger.evaluate(df_data)
            
            # 새로운 도메인 모델로 변환
            return EvaluationResult.from_legacy(legacy_result)
        except Exception as e:
            return EvaluationResult.error(f"평가 실패: {e}")
```

**왜 이렇게 했는가?**
- 기존 `Trigger.evaluate()` 메서드가 잘 작동함
- 전체 시스템을 한 번에 바꾸기에는 리스크 큼
- 점진적 마이그레이션 필요

**결과**:
- 기존 시스템 동작 100% 유지
- 새로운 도메인 모델 점진적 도입
- 12개 테스트로 호환성 검증

### 결정 3: Strategy 패턴으로 정규화 구현
```python
# 문제: 다양한 정규화 알고리즘 지원 필요

# 해결: Strategy 패턴
class NormalizationService:
    def __init__(self):
        self._strategies = {
            NormalizationMethod.MIN_MAX: MinMaxStrategy(),
            NormalizationMethod.Z_SCORE: ZScoreStrategy(),
            NormalizationMethod.ROBUST: RobustStrategy()
        }
    
    def normalize(self, data, method):
        strategy = self._strategies[method]
        return strategy.normalize(data)
```

**왜 이렇게 했는가?**
- MinMax, Z-Score, Robust 등 다양한 정규화 방법 필요
- 향후 새로운 정규화 방법 추가 예정
- 각 알고리즘의 독립적 테스트 필요

**결과**:
- 확장 가능한 정규화 시스템
- 23개 테스트로 각 알고리즘 검증
- 신뢰도 점수 계산 기능 추가

## 🔧 실무 구현 과정

### Phase 1: 분석 및 설계 (1일)
```
1. 기존 코드 분석
   - compatibility_validator.py (752줄) 분석
   - 핵심 비즈니스 규칙 추출
   - UI와 DB 결합도 파악

2. 도메인 모델 설계
   - CompatibilityResult Value Object
   - TradingVariable 엔티티 활용 방안
   - 서비스 간 협력 구조 설계

3. 마이그레이션 전략 수립
   - 기존 시스템 호환성 유지
   - 점진적 전환 계획
```

### Phase 2: 핵심 구현 (1일)
```
1. 호환성 서비스 구현
   - StrategyCompatibilityService (310줄)
   - ComparisonGroupRules Value Object
   - 3단계 호환성 검증 로직

2. 트리거 평가 서비스 구현
   - TriggerEvaluationService (331줄)
   - MarketData/EvaluationResult Value Objects
   - BusinessLogicAdapter (289줄)

3. 정규화 서비스 구현
   - NormalizationService (400+ 줄)
   - Strategy 패턴 적용
   - 3가지 정규화 알고리즘
```

### Phase 3: 테스트 및 통합 (1일)
```
1. 단위 테스트 구현
   - 호환성 서비스: 21개 테스트
   - 트리거 평가: 12개 테스트
   - 정규화 서비스: 23개 테스트

2. 엔티티-서비스 통합
   - Strategy.check_trigger_compatibility() 추가
   - Trigger.evaluate() 서비스 위임
   - 7개 통합 테스트

3. 전체 검증
   - 63개 테스트 100% 통과
   - 기존 시스템 호환성 확인
```

## 💡 핵심 학습 포인트

### 성공 요인
1. **기존 코드 분석 우선**: 새로 만들기 전에 기존 로직 완전 이해
2. **점진적 마이그레이션**: 어댑터 패턴으로 호환성 유지
3. **Value Object 활용**: 복잡한 데이터를 명확한 타입으로 관리
4. **테스트 주도 개발**: 도메인 서비스는 테스트하기 쉬움

### 피해야 할 실수들
1. **과도한 서비스화**: 모든 로직을 서비스로 만들려는 욕구
2. **상태 관리**: 도메인 서비스에 인스턴스 변수 추가
3. **기술적 관심사**: DB나 UI 로직을 서비스에 포함
4. **의존성 과다**: 너무 많은 다른 서비스에 의존

## 🚨 해결한 실제 문제들

### 문제 1: 호환성 검증 로직 분산
**상황**: RSI + 가격 조합 시 사용자 혼란, UI 곳곳에 중복 검증 로직

**해결**:
```python
# Before: UI에 분산된 로직
if variable.comparison_group == "percentage_comparable":
    # 여러 UI 컴포넌트에 중복

# After: 중앙화된 서비스
result = compatibility_service.check_variable_compatibility(existing, new)
if result.level == CompatibilityLevel.WARNING:
    show_normalization_dialog(result.message)
```

### 문제 2: DataFrame vs 도메인 모델 충돌
**상황**: 기존 DataFrame 기반 시스템과 새로운 도메인 모델 불일치

**해결**:
```python
# 어댑터 패턴으로 브릿지
class BusinessLogicAdapter:
    def dataframe_to_market_data(self, df: pd.DataFrame) -> MarketData:
        return MarketData(
            symbol=df.attrs.get('symbol', 'UNKNOWN'),
            timestamp=df.index[-1],
            close=df['close'].iloc[-1],
            indicators=self._extract_indicators(df)
        )
```

### 문제 3: 테스트 복잡성
**상황**: UI와 결합된 로직은 테스트하기 어려움

**해결**:
```python
# 순수 도메인 서비스는 테스트 용이
def test_compatible_variables_same_group():
    service = StrategyCompatibilityService()
    rsi = TradingVariable("RSI", "momentum", "percentage_comparable")
    stochastic = TradingVariable("Stochastic", "momentum", "percentage_comparable")
    
    result = service.check_variable_compatibility([rsi], stochastic)
    assert result.level == CompatibilityLevel.COMPATIBLE
```

## 📈 비즈니스 가치

### 사용자 경험 개선
- **혼란 해소**: 변수 조합 시 명확한 안내
- **실시간 검증**: UI에서 즉시 호환성 확인
- **일관성**: 모든 곳에서 동일한 검증 규칙

### 개발 생산성 향상
- **코드 재사용**: 63개 테스트로 검증된 안정적 서비스
- **유지보수성**: 중앙화된 비즈니스 로직
- **확장성**: 새로운 변수나 규칙 추가 용이

### 시스템 품질 향상
- **안정성**: 100% 테스트 커버리지
- **성능**: 중복 계산 제거
- **일관성**: 도메인 규칙의 단일 소스

---

**🎯 핵심 메시지**: 도메인 서비스는 복잡한 비즈니스 로직을 단순화하고 중앙화하는 강력한 도구입니다!

**🔍 다음 읽을 것**: [구현 가이드](./02_implementation_guide.md)에서 실제 코드 작성 방법을 확인하세요.
