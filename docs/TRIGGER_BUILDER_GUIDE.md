# 🎯 트리거 빌더 시스템 가이드

## 📋 개요

트리거 빌더는 **조건부 매매 신호 생성**을 위한 핵심 시스템입니다. 사용자가 드래그앤드롭으로 조건을 조합하여 매매 전략을 구축할 수 있습니다.

## 🏗️ 시스템 아키텍처

### 컴포넌트 구조
```
trigger_builder/
├── components/core/
│   ├── condition_builder.py      # 조건 생성 엔진
│   ├── condition_dialog.py       # 조건 생성 UI
│   ├── condition_validator.py    # 조건 검증
│   └── parameter_widgets.py      # 파라미터 UI
├── components/shared/
│   └── compatibility_validator.py # 호환성 검증
└── data/
    └── variable_definitions.py   # 변수 정의 관리
```

### UI 구조
```
트리거 빌더 탭
├── 📊 변수 팔레트        # 좌측: 사용 가능한 변수들
├── 🎯 조건 캔버스        # 중앙: 조건 조합 영역
├── ⚙️ 파라미터 패널      # 우측: 세부 설정
└── 🔍 미리보기 차트      # 하단: 실시간 결과
```

## 🧩 3중 카테고리 호환성 시스템

### 1. Purpose Category (목적별 분류)
- **`trend`**: 추세 지표 (SMA, EMA, MACD)
- **`momentum`**: 모멘텀 지표 (RSI, Stochastic)
- **`volatility`**: 변동성 지표 (Bollinger Bands, ATR)
- **`volume`**: 거래량 지표 (Volume, VWAP)
- **`price`**: 가격 지표 (Close, High, Low)

### 2. Chart Category (차트 표시 방식)
- **`overlay`**: 가격 차트 위 오버레이 (이동평균, 볼린저밴드)
- **`subplot`**: 별도 서브플롯 (RSI, MACD, Stochastic)

### 3. Comparison Group (비교 가능성)
- **`price_comparable`**: 가격과 직접 비교 가능 (이동평균, 볼린저밴드)
- **`percentage_comparable`**: 백분율 기준 비교 (RSI, Stochastic)
- **`zero_centered`**: 0 중심 지표 (MACD, Williams %R)

## 🔗 호환성 검증 규칙

### 기본 원칙
- **같은 comparison_group**: 직접 비교 가능
- **다른 comparison_group**: 비교 불가 (UI에서 경고)
- **price vs percentage**: 비교 시 정규화 필요

### 예외 사항
```python
# 허용되는 특수 조합
RSI > 70  # percentage_comparable
Close > SMA(20)  # price_comparable (정규화됨)

# 금지되는 조합  
RSI > Close  # Error: 비교 불가능
MACD > RSI   # Error: 서로 다른 스케일
```

## 🗄️ 데이터베이스 스키마

### 트레이딩 변수 테이블
```sql
CREATE TABLE trading_variables (
    variable_id TEXT PRIMARY KEY,           -- 'SMA', 'RSI', 'MACD'
    display_name_ko TEXT NOT NULL,          -- '단순이동평균'
    purpose_category TEXT NOT NULL,         -- 'trend', 'momentum'
    chart_category TEXT NOT NULL,           -- 'overlay', 'subplot'
    comparison_group TEXT NOT NULL,         -- 'price_comparable'
    is_active BOOLEAN DEFAULT 1,
    description TEXT,
    source TEXT DEFAULT 'built-in'
);
```

### 변수 파라미터 테이블
```sql
CREATE TABLE variable_parameters (
    parameter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL,              -- 외래키
    parameter_name TEXT NOT NULL,           -- 'period', 'source'
    parameter_type TEXT NOT NULL,           -- 'integer', 'float', 'enum'
    default_value TEXT,                     -- 기본값
    min_value REAL,                         -- 최소값
    max_value REAL,                         -- 최대값
    enum_options TEXT,                      -- JSON 형태 선택지
    is_required BOOLEAN DEFAULT 1,
    display_name_ko TEXT NOT NULL,
    help_text TEXT
);
```

### 조건 저장 테이블
```sql
CREATE TABLE trading_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    variable_id TEXT NOT NULL,
    variable_params TEXT,                   -- JSON: 파라미터
    operator TEXT NOT NULL,                 -- '>', '<', '~='
    target_value TEXT,                      -- 고정값
    external_variable TEXT,                 -- JSON: 외부변수
    comparison_type TEXT DEFAULT 'fixed',   -- 'fixed', 'external'
    is_active BOOLEAN DEFAULT 1
);
```

## 🎨 사용자 워크플로

### 1. 변수 선택
```
변수 팔레트에서 지표 선택
├── 📈 추세 지표 (SMA, EMA, MACD)
├── 🔄 모멘텀 지표 (RSI, Stochastic)
├── 📊 변동성 지표 (Bollinger Bands)
└── 💰 가격 지표 (Close, High, Low)
```

### 2. 파라미터 설정
```python
# 예시: RSI 설정
{
    "period": 14,           # 계산 기간
    "source": "close",      # 데이터 소스
    "overbought": 70,       # 과매수 기준
    "oversold": 30          # 과매도 기준
}
```

### 3. 조건 생성
```
RSI(14) > 70               # 과매수 조건
Close > SMA(20)            # 이평선 상향 돌파
MACD.signal_line > 0       # MACD 시그널 상승
```

### 4. 조건 조합
```
진입 조건: RSI < 30 AND Close > SMA(20)
관리 조건: RSI > 70 OR (Close < SMA(20) * 0.95)
```

## 🔧 개발 구현 사항

### 실시간 호환성 검증
```python
class CompatibilityValidator:
    def validate_condition(self, var1, var2, operator):
        # comparison_group 일치성 검사
        if var1.comparison_group != var2.comparison_group:
            raise IncompatibleVariableError()
        
        # 차트 카테고리 호환성 검사
        if not self._chart_compatible(var1, var2):
            return ValidationWarning()
```

### 동적 파라미터 UI 생성
```python
class ParameterWidgetFactory:
    def create_widget(self, param_def):
        if param_def.type == 'integer':
            return SpinBoxWidget(param_def.min_value, param_def.max_value)
        elif param_def.type == 'enum':
            return ComboBoxWidget(param_def.enum_options)
```

## 🧪 테스트 시나리오

### 단위 테스트
- 호환성 검증 로직
- 파라미터 유효성 검사
- 조건 직렬화/역직렬화

### 통합 테스트
- UI 상호작용 테스트
- 데이터베이스 연동 테스트
- 백테스팅 엔진 연동

## 📚 관련 문서

- [변수 호환성 상세](VARIABLE_COMPATIBILITY.md)
- [데이터베이스 스키마](DB_SCHEMA.md)
- [전략 메이커 연동](STRATEGY_MAKER_INTEGRATION.md)
