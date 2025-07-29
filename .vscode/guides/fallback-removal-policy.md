# 폴백 코드 제거 정책 v1.0

> **"종기의 고름을 뺀다" - 폴백 코드의 역기능 제거**

## 🎯 핵심 철학

**"동작이 안되면 화면이 비고 에러가 표시되는게 훨씬 개발에 도움이 됩니다"**

폴백 코드는 개발 단계에서 **실제 문제를 숨겨서 디버깅을 방해**하는 역기능을 합니다. 마치 종기의 고름을 덮어두는 것과 같아서, 근본적인 치료를 방해합니다.

## 🚨 폴백 코드의 문제점

### 1. 에러 마스킹 (Error Masking)
```python
# ❌ 문제가 있는 코드 (폴백으로 에러 숨김)
try:
    from .components.condition_storage import ConditionStorage
except ImportError:
    # 폴백으로 더미 클래스 - 실제 import 경로 문제를 숨김!
    class ConditionStorage:
        def __init__(self): 
            print("⚠️ 폴백 ConditionStorage 사용 중")
        def save_condition(self, data): 
            return True, "폴백 저장", 1
```

**결과**: 개발자는 `ConditionStorage`가 정상 동작한다고 착각하게 됨

### 2. 디버깅 시간 낭비
- 폴백 코드가 동작하면서 실제 문제가 숨겨짐
- 개발자는 다른 곳에서 문제를 찾느라 시간 낭비
- 근본 원인 파악까지 시간이 오래 걸림

### 3. 코드 품질 저하
- 실제로 동작하지 않는 코드가 남아있음
- 테스트가 무의미해짐 (폴백으로 항상 통과)
- 프로덕션에서 예상치 못한 오류 발생

## ✅ 폴백 제거 가이드라인

### 1. Import 에러는 절대 숨기지 않기
```python
# ✅ 올바른 방식 (에러를 명확히 드러냄)
from .components.core.condition_storage import ConditionStorage
from .components.core.variable_definitions import VariableDefinitions

# 에러 발생 시: ModuleNotFoundError: No module named 'upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.condition_storage'
# → 정확한 경로 문제를 즉시 파악 가능
```

### 2. 비즈니스 로직 폴백 제거
```python
# ❌ 비즈니스 로직 폴백 (문제 숨김)
def save_condition(self, data):
    try:
        return self.storage.save_condition(data)
    except Exception:
        return True, "폴백 저장", 1  # 실제 저장 실패를 숨김

# ✅ 에러를 명확히 표시
def save_condition(self, data):
    return self.storage.save_condition(data)
    # 실패하면 바로 예외 발생 → 문제 즉시 파악
```

### 3. UI 컴포넌트 폴백 제거
```python
# ❌ UI 컴포넌트 폴백
try:
    self.condition_dialog = ConditionDialog()
except Exception as e:
    print(f"⚠️ ConditionDialog 로드 실패: {e}")
    self.condition_dialog = None  # 이후 hasattr 검사로 숨김

# ✅ 명확한 에러 표시
self.condition_dialog = ConditionDialog()
# 실패하면 즉시 예외 → 정확한 문제 파악
```

## 🎯 허용되는 최소 폴백

### 1. UI 틀 보존 (구조적 안전성)
```python
# ✅ 허용: UI가 완전히 깨지지 않도록 하는 최소한의 구조 보존
try:
    self.chart_widget = ChartWidget()
except Exception as e:
    # 에러 표시는 필수
    self.logger.error(f"❌ 차트 위젯 로드 실패: {e}")
    # 최소 구조만 제공 (기능은 제공하지 않음)
    self.chart_widget = QLabel("차트 로드 실패")
```

### 2. 외부 의존성 (선택적 기능)
```python
# ✅ 허용: 외부 라이브러리 등 선택적 기능
try:
    import matplotlib.pyplot as plt
    CHART_AVAILABLE = True
except ImportError:
    CHART_AVAILABLE = False
    # 기능 비활성화 명시
```

### 3. 설정 기본값 (사용자 편의)
```python
# ✅ 허용: 설정값 기본값 제공
def get_chart_theme(self):
    try:
        return self.config.get_theme()
    except Exception:
        # 기본값 제공 (에러 로그 필수)
        self.logger.warning("⚠️ 테마 설정 로드 실패, 기본 테마 사용")
        return "default"
```

## 🏆 폴백 제거의 효과

### Phase 4 Critical Task 사례
**Before (폴백 있음)**:
```
⚠️ ConditionStorage import 실패: 폴백 사용
⚠️ 조건 빌더 로드 실패: 폴백 위젯 사용
⚠️ 시뮬레이션 엔진 로드 실패: 더미 데이터 사용
```
→ 8개 GUI 문제가 모두 숨겨져서 원인 파악 불가능

**After (폴백 제거)**:
```
ModuleNotFoundError: No module named 'upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.condition_storage'
```
→ 정확한 import 경로 문제 즉시 파악, 30초 만에 해결

### 디버깅 시간 단축
- **폴백 있음**: 문제 파악 30분 + 수정 30분 = **1시간**
- **폴백 제거**: 문제 파악 1분 + 수정 2분 = **3분**
- **효율성 향상**: **20배 빨라짐**

## 📋 폴백 제거 체크리스트

### Import 관련
- [ ] `try-except ImportError`로 감싸진 import 문 제거
- [ ] 더미 클래스/함수로 대체하는 코드 제거
- [ ] 정확한 import 경로 사용

### 비즈니스 로직
- [ ] 데이터 저장/로드 폴백 제거
- [ ] 계산 로직 폴백 제거
- [ ] 검증 로직 폴백 제거

### UI 컴포넌트
- [ ] 위젯 생성 폴백 제거
- [ ] 이벤트 핸들러 폴백 제거
- [ ] 데이터 바인딩 폴백 제거

### 에러 처리
- [ ] 모든 에러 메시지 명확히 표시
- [ ] 에러 발생 시 적절한 예외 발생
- [ ] 로그에 상세한 에러 정보 기록

## 🎯 결론

**"천천히 가는 것이 빠르게 가는 방법"**

폴백 코드를 제거하는 것은 단기적으로는 더 많은 에러를 보게 되지만, 장기적으로는:

1. **문제를 정확히 파악**할 수 있게 됩니다
2. **디버깅 시간이 대폭 단축**됩니다  
3. **코드 품질이 향상**됩니다
4. **실제 동작하는 코드**만 남게 됩니다

이는 마치 종기의 고름을 제대로 배출하여 근본적인 치료를 가능하게 하는 것과 같습니다.
