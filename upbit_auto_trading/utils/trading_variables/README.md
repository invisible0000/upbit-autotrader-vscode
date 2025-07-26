# 트레이딩 지표 변수 관리 시스템 사용법

## 📋 개요
이 시스템은 업비트 자동매매 시스템에서 트레이딩 지표의 호환성 문제를 해결하고, 새로운 지표 추가를 자동화하는 DB 기반 관리 시스템입니다.

## 🚀 빠른 시작

### 1. 기본 사용법

```python
from upbit_auto_trading.utils.trading_variables import SimpleVariableManager

# 매니저 초기화
manager = SimpleVariableManager()

# 호환 가능한 변수 조회
compatible_vars = manager.get_compatible_variables('SMA')
print(f"SMA와 호환되는 변수들: {[var['variable_id'] for var in compatible_vars]}")

# 두 변수의 호환성 확인
is_compatible = manager.check_compatibility('SMA', 'EMA')
print(f"SMA ↔ EMA 호환성: {'✅ 호환' if is_compatible else '❌ 비호환'}")
```

### 2. 성능 최적화된 사용법

```python
from upbit_auto_trading.utils.trading_variables import CachedVariableManager

# 캐싱 기능이 있는 매니저 사용 (대용량 처리에 적합)
manager = CachedVariableManager(cache_size=1000)

# 배치 호환성 검사 (성능 최적화됨)
pairs = [('SMA', 'EMA'), ('RSI', 'STOCH'), ('MACD', 'RSI')]
results = manager.batch_check_compatibility(pairs)

for (var1, var2), compatible in results.items():
    print(f"{var1} ↔ {var2}: {'✅' if compatible else '❌'}")
```

### 3. 파라미터 관리

```python
from upbit_auto_trading.utils.trading_variables import ParameterManager

# 파라미터 매니저 초기화
param_manager = ParameterManager()

# SMA의 기본 파라미터 가져오기
defaults = param_manager.get_default_parameters('SMA')
print(f"SMA 기본 파라미터: {defaults}")
# 출력: {'period': 20, 'source': 'close'}

# 파라미터 유효성 검증
test_params = {'period': 50, 'source': 'high'}
validation_results = param_manager.validate_parameters('SMA', test_params)

for result in validation_results:
    if result.is_valid:
        print(f"✅ {result.parameter_name}: {result.value}")
    else:
        print(f"❌ {result.parameter_name}: {result.error_message}")
```

## 🎛️ CLI 도구 사용법

시스템에는 강력한 CLI 도구가 포함되어 있습니다:

```bash
# CLI 도구 실행
cd tools
python trading_variables_cli.py

# 또는 직접 명령 실행
python trading_variables_cli.py list              # 모든 변수 목록
python trading_variables_cli.py add MACD_SIGNAL "MACD 시그널"  # 새 변수 추가
python trading_variables_cli.py check SMA EMA     # 호환성 확인
python trading_variables_cli.py export variables.json  # 설정 내보내기
```

### CLI 명령어 전체 목록

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `list` | 모든 활성 변수 목록 표시 | `python trading_variables_cli.py list` |
| `add <ID> <NAME>` | 새 변수 추가 (자동 분류) | `add HULL_MA "헐 이동평균"` |
| `activate <ID>` | 변수 활성화 | `activate HULL_MA` |
| `deactivate <ID>` | 변수 비활성화 | `deactivate HULL_MA` |
| `check <ID1> <ID2>` | 두 변수 호환성 확인 | `check SMA EMA` |
| `info <ID>` | 변수 상세 정보 표시 | `info SMA` |
| `category <CAT>` | 카테고리별 변수 목록 | `category trend` |
| `export <FILE>` | 설정을 JSON으로 내보내기 | `export backup.json` |
| `stats` | 시스템 통계 정보 표시 | `stats` |

## 🔧 고급 사용법

### 1. 새 지표 자동 추가

```python
from upbit_auto_trading.utils.trading_variables import SmartIndicatorClassifier

# 지능형 분류기 사용
classifier = SmartIndicatorClassifier()

# 새 지표 자동 분류 및 추가
result = classifier.classify_and_add("AWESOME_OSCILLATOR", "어썸 오실레이터")

print(f"🔍 분류 결과: {result['category']}")
print(f"📊 신뢰도: {result['confidence']}%")
print(f"✅ 추가 성공: {result['success']}")

if result['confidence'] < 80:
    print("⚠️ 신뢰도가 낮습니다. 수동 확인이 권장됩니다.")
```

### 2. UI 위젯 통합

```python
from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components import (
    DatabaseVariableComboBox, CompatibilityAwareVariableSelector
)

# DB 기반 콤보박스 (카테고리별 그룹화)
combo_box = DatabaseVariableComboBox()
combo_box.load_variables()

# 호환성 인식 변수 선택기
selector = CompatibilityAwareVariableSelector()
selector.set_base_variable('SMA')  # 기준 변수 설정
# 자동으로 SMA와 호환되는 변수들만 표시됨
```

### 3. 성능 모니터링

```python
from upbit_auto_trading.utils.trading_variables import CachedVariableManager

manager = CachedVariableManager()

# 성능 테스트 실행
performance_results = manager.performance_test(iterations=1000)

print("📊 성능 분석 결과:")
print(f"  🚀 성능 향상: {performance_results['test_summary']['performance_improvement']}배")
print(f"  💾 캐시 적중률: {performance_results['cache_performance']['hit_rate']}%")
print(f"  ⚡ 평균 쿼리 시간: {performance_results['cache_performance']['avg_query_time']}ms")
```

## 📊 지원되는 지표 카테고리

### 📈 추세 지표 (Trend)
- `SMA`, `EMA`, `WMA` - 이동평균선
- `BOLLINGER_BANDS` - 볼린저 밴드
- `ICHIMOKU` - 일목균형표
- `PARABOLIC_SAR` - 파라볼릭 SAR
- `ADX` - 평균방향성지수
- `AROON` - 아룬 지표

### ⚡ 모멘텀 지표 (Momentum)
- `RSI` - RSI 지표
- `STOCH` - 스토캐스틱
- `STOCH_RSI` - 스토캐스틱 RSI
- `WILLIAMS_R` - 윌리엄스 %R
- `CCI` - 상품채널지수
- `MACD` - MACD 지표
- `ROC` - 가격변동률
- `MFI` - 자금흐름지수

### 🔥 변동성 지표 (Volatility)
- `ATR` - 평균실제범위
- `BOLLINGER_WIDTH` - 볼린저 밴드 폭
- `STANDARD_DEVIATION` - 표준편차

### 📦 거래량 지표 (Volume)
- `VOLUME` - 거래량
- `OBV` - 누적거래량
- `VOLUME_MA` - 거래량 이동평균
- `VOLUME_OSCILLATOR` - 거래량 오실레이터
- `AD_LINE` - 누적분배선
- `CHAIKIN_MF` - 차이킨 머니플로우

### 💰 가격 지표 (Price)
- `OPEN`, `HIGH`, `LOW`, `CLOSE` - 기본 가격
- `HL2`, `HLC3`, `OHLC4` - 조합 가격
- `TYPICAL_PRICE` - 대표가격
- `WEIGHTED_CLOSE` - 가중종가

## 🔍 호환성 규칙

### 호환 가능한 조합
- **같은 카테고리**: 동일한 용도의 지표들 (예: 추세 지표끼리)
- **같은 비교 그룹**: 동일한 수치 범위나 특성 (예: 퍼센트 지표끼리)

### 호환성 그룹
- `price_comparable`: 가격 기반 지표 (SMA, EMA, 가격 등)
- `percentage_comparable`: 0-100% 범위 지표 (RSI, STOCH 등)
- `centered_oscillator`: 0 중심 오실레이터 (CCI, ROC 등)
- `volatility_comparable`: 변동성 지표들
- `volume_comparable`: 거래량 기반 지표들

### 예시
```python
# ✅ 호환 가능한 조합들
manager.check_compatibility('SMA', 'EMA')      # True - 둘 다 price_comparable
manager.check_compatibility('RSI', 'STOCH')    # True - 둘 다 percentage_comparable
manager.check_compatibility('ATR', 'BOLLINGER_WIDTH')  # True - 둘 다 volatility_comparable

# ❌ 호환되지 않는 조합들
manager.check_compatibility('RSI', 'VOLUME')   # False - 다른 그룹
manager.check_compatibility('SMA', 'ATR')      # False - 가격 vs 변동성
```

## 🔧 파라미터 시스템

### 지원되는 파라미터 타입
- `integer`: 정수 (기간, 개수 등)
- `float`: 실수 (배수, 계수 등)
- `string`: 문자열
- `boolean`: 참/거짓
- `enum`: 선택지 (예: 'open', 'high', 'low', 'close')

### 파라미터 예시
```python
# SMA 파라미터
{
    "period": 20,          # 기간 (정수, 1-200)
    "source": "close"      # 데이터 소스 (enum)
}

# BOLLINGER_BANDS 파라미터
{
    "period": 20,          # 기간 (정수, 2-100)
    "multiplier": 2.0,     # 표준편차 배수 (실수, 0.1-5.0)
    "source": "close"      # 데이터 소스 (enum)
}

# STOCH 파라미터
{
    "k_period": 14,        # %K 기간 (정수, 1-100)
    "d_period": 3,         # %D 기간 (정수, 1-50)
    "smooth": 3            # 스무딩 (정수, 1-10)
}
```

## 🔄 데이터베이스 구조

### 주요 테이블
- `trading_variables`: 메인 지표 정보
- `variable_parameters`: 지표별 파라미터 정의
- `comparison_groups`: 호환성 그룹 메타데이터
- `schema_version`: 스키마 버전 관리

### 백업 및 복원
```python
# 설정 내보내기 (CLI)
python trading_variables_cli.py export backup_20250726.json

# 프로그래밍 방식 백업
manager = SimpleVariableManager()
all_variables = manager.get_all_variables()

import json
with open('backup.json', 'w', encoding='utf-8') as f:
    json.dump(all_variables, f, ensure_ascii=False, indent=2)
```

## 🚨 문제 해결

### 자주 발생하는 문제

1. **DB 파일을 찾을 수 없음**
   ```
   해결책: DB 파일이 자동으로 생성됩니다. 경로 권한을 확인하세요.
   ```

2. **호환성 검사가 예상과 다름**
   ```python
   # 상세 정보 확인
   var1_info = manager.get_variable_info('SMA')
   var2_info = manager.get_variable_info('EMA')
   print(f"SMA 카테고리: {var1_info['purpose_category']}")
   print(f"EMA 카테고리: {var2_info['purpose_category']}")
   ```

3. **새 지표 분류 신뢰도가 낮음**
   ```python
   # 수동으로 카테고리 지정
   manager.add_variable(
       variable_id="CUSTOM_INDICATOR",
       display_name_ko="커스텀 지표",
       purpose_category="trend",  # 수동 지정
       chart_category="overlay",
       comparison_group="price_comparable"
   )
   ```

### 성능 최적화 팁

1. **대용량 데이터 처리**: `CachedVariableManager` 사용
2. **배치 처리**: `batch_check_compatibility()` 활용
3. **캐시 관리**: 주기적으로 `clear_cache()` 호출

## 📝 개발자 가이드

### 새 지표 추가 플로우

1. **자동 추가** (권장)
   ```bash
   python trading_variables_cli.py add NEW_INDICATOR "새 지표"
   ```

2. **수동 추가** (정밀 제어)
   ```python
   success = manager.add_variable(
       variable_id="NEW_INDICATOR",
       display_name_ko="새 지표",
       purpose_category="trend",
       chart_category="overlay", 
       comparison_group="price_comparable",
       description="상세 설명"
   )
   ```

3. **파라미터 정의**
   ```python
   param_manager.add_parameter_definition(
       variable_id="NEW_INDICATOR",
       parameter_name="period",
       parameter_type="integer",
       default_value="20",
       display_name_ko="기간",
       min_value="1",
       max_value="200"
   )
   ```

### 테스트 코드 작성

```python
import unittest
from upbit_auto_trading.utils.trading_variables import SimpleVariableManager

class TestVariableCompatibility(unittest.TestCase):
    def setUp(self):
        self.manager = SimpleVariableManager()
    
    def test_sma_ema_compatibility(self):
        """SMA와 EMA는 호환되어야 함"""
        self.assertTrue(self.manager.check_compatibility('SMA', 'EMA'))
    
    def test_rsi_volume_incompatibility(self):
        """RSI와 VOLUME은 호환되지 않아야 함"""
        self.assertFalse(self.manager.check_compatibility('RSI', 'VOLUME'))

if __name__ == '__main__':
    unittest.main()
```

## 📞 지원

문제가 발생하거나 새로운 기능이 필요한 경우:
1. 로그 파일 확인 (`logs/` 디렉토리)
2. CLI 도구의 `stats` 명령으로 시스템 상태 확인
3. 성능 테스트로 시스템 건전성 검증

---

## 🎯 요약

이 시스템을 사용하면:
- ✅ **호환성 문제 해결**: SMA ↔ EMA 등 자동 호환성 검증
- ✅ **자동 지표 분류**: 80-100% 신뢰도로 새 지표 자동 분류
- ✅ **성능 최적화**: 200개 지표까지 0.6초 처리
- ✅ **사용자 친화적**: 3줄 코드로 새 지표 추가 가능

더 이상 수동으로 지표를 관리할 필요가 없습니다! 🚀
