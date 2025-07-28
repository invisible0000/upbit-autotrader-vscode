# 트리거 빌더 시스템 가이드

## 📋 개요

트리거 빌더는 전략 메이커의 핵심 구성요소로, 조건(Condition) 생성과 파라미터 설정을 통해 트리거를 구축하는 시스템입니다. 

## 🏗️ 아키텍처 구조

### 컴포넌트 기반 설계
```
trigger_builder/
├── components/
│   ├── core/                      # 핵심 로직 컴포넌트
│   │   ├── condition_builder.py   # 조건 생성 및 빌드
│   │   ├── condition_dialog.py    # 조건 생성 UI
│   │   ├── condition_storage.py   # 조건 저장/로드
│   │   ├── condition_validator.py # 조건 검증
│   │   ├── variable_definitions.py # 변수 정의 관리
│   │   └── parameter_widgets.py   # 파라미터 UI 위젯
│   ├── shared/                    # 공유 컴포넌트
│   │   └── compatibility_validator.py # 호환성 검증
│   └── data/                      # 데이터 관련
└── README.md                      # 컴포넌트 가이드
```

## 🗄️ 새로운 DB 스키마 구조

### 1. 통합 데이터베이스 (`data/app_settings.sqlite3`)

#### 핵심 테이블 구조
```sql
-- 트레이딩 변수 메인 테이블
CREATE TABLE trading_variables (
    variable_id TEXT PRIMARY KEY,           -- 'SMA', 'RSI', 'MACD'
    display_name_ko TEXT NOT NULL,          -- '단순이동평균', 'RSI 지표'
    display_name_en TEXT,                   -- 'Simple Moving Average'
    purpose_category TEXT NOT NULL,         -- 'trend', 'momentum', 'volatility', 'volume', 'price'
    chart_category TEXT NOT NULL,           -- 'overlay', 'subplot'
    comparison_group TEXT NOT NULL,         -- 'price_comparable', 'percentage_comparable'
    is_active BOOLEAN DEFAULT 1,            -- 활성화 상태
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,                       -- 지표 설명
    source TEXT DEFAULT 'built-in'          -- 'built-in', 'tradingview', 'custom'
);

-- 변수별 파라미터 정의 테이블
CREATE TABLE variable_parameters (
    parameter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL,              -- 외래키: trading_variables.variable_id
    parameter_name TEXT NOT NULL,           -- 'period', 'source', 'multiplier'
    parameter_type TEXT NOT NULL,           -- 'integer', 'float', 'string', 'boolean', 'enum'
    default_value TEXT,                     -- 기본값
    min_value REAL,                         -- 최소값 (숫자 타입용)
    max_value REAL,                         -- 최대값 (숫자 타입용)
    enum_options TEXT,                      -- JSON 형태의 선택 옵션
    is_required BOOLEAN NOT NULL DEFAULT 1, -- 필수 파라미터 여부
    display_name_ko TEXT NOT NULL,          -- '기간', '데이터 소스'
    display_name_en TEXT,                   -- 'Period', 'Data Source'
    help_text TEXT,                         -- 파라미터 도움말
    display_order INTEGER DEFAULT 0,        -- 표시 순서
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 트리거 조건 저장 테이블
CREATE TABLE trading_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- 조건 이름
    description TEXT,                       -- 조건 설명
    variable_id TEXT NOT NULL,              -- 기본 변수 ID
    variable_params TEXT,                   -- JSON: 변수 파라미터
    operator TEXT NOT NULL,                 -- '>', '>=', '<', '<=', '~=', '!='
    target_value TEXT,                      -- 비교값 (고정값 모드)
    external_variable TEXT,                 -- JSON: 외부변수 정보 (외부변수 모드)
    trend_direction TEXT DEFAULT 'both',    -- 'rising', 'falling', 'both'
    comparison_type TEXT DEFAULT 'fixed',   -- 'fixed', 'external'
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. 카테고리 관리 테이블
```sql
-- 변수 카테고리 정의
CREATE TABLE variable_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_type TEXT NOT NULL,            -- 'purpose', 'chart', 'comparison'
    category_key TEXT NOT NULL,             -- 'trend', 'overlay', 'price_comparable'
    category_name_ko TEXT NOT NULL,         -- '추세 지표', '오버레이'
    category_name_en TEXT NOT NULL,         -- 'Trend Indicators', 'Overlay'
    description TEXT,                       -- 카테고리 설명
    icon TEXT,                              -- UI 아이콘 ('📈', '🔗')
    display_order INTEGER DEFAULT 0,        -- 표시 순서
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎯 3중 카테고리 시스템

### 1. 용도 카테고리 (Purpose Category)
변수의 분석 목적에 따른 분류:

| 카테고리 | 설명 | 예시 |
|---------|------|------|
| `trend` | 📈 추세 지표 | SMA, EMA, TEMA, DEMA, WMA, HMA, VWMA |
| `momentum` | ⚡ 모멘텀 지표 | RSI, STOCHASTIC, %K, %D, CCI, ROC |
| `volatility` | 🔥 변동성 지표 | BOLLINGER_BAND, ATR, STDDEV |
| `volume` | 📦 거래량 지표 | VOLUME, VOLUME_SMA, VOLUME_WEIGHTED |
| `price` | 💰 가격 데이터 | CURRENT_PRICE, HIGH, LOW, OPEN, CLOSE |

### 2. 차트 카테고리 (Chart Category)
차트 표시 방식에 따른 분류:

| 카테고리 | 설명 | 특징 |
|---------|------|------|
| `overlay` | 🔗 오버레이 | 가격 차트 위에 직접 표시 (같은 스케일) |
| `subplot` | 📊 서브플롯 | 별도 영역에 표시 (독립적 스케일) |

### 3. 비교 그룹 (Comparison Group)
변수 간 비교 가능성에 따른 분류:

| 그룹 | 설명 | 호환 규칙 |
|------|------|-----------|
| `price_comparable` | 💱 가격 비교 가능 | 원화 단위, 가격 기반 지표들 |
| `percentage_comparable` | 📊 퍼센트 비교 가능 | 0-100% 범위의 오실레이터들 |
| `centered_oscillator` | ⚖️ 중심선 오실레이터 | 0을 중심으로 한 오실레이터들 |
| `volume_comparable` | 📦 거래량 비교 가능 | 거래량 기반 지표들 |
| `signal_conditional` | ⚡ 신호 조건부 | 특별한 조건에서만 비교 가능 |
| `unique_scale` | 🚫 비교 불가 | 독립적 스케일, 타 변수와 비교 불가 |

## 🔧 조건 생성 프로세스

### 1. 기본 조건 생성
```python
# 1단계: 변수 선택
variable_id = "RSI"
variable_params = {"period": 14, "source": "close"}

# 2단계: 비교 설정
operator = ">"
target_value = "70"  # 고정값 모드

# 3단계: 조건 정보
condition_name = "RSI 과매수 진입"
description = "RSI가 70을 초과할 때"
trend_direction = "rising"
```

### 2. 외부변수 조건 생성
```python
# 외부변수 모드
comparison_type = "external"
external_variable = {
    "variable_id": "STOCHASTIC",
    "variable_params": {"k_period": 14, "d_period": 3},
    "category": "momentum"
}

# 호환성 자동 검증
is_compatible = check_compatibility("RSI", "STOCHASTIC")
# Result: True (둘 다 momentum 카테고리, percentage_comparable 그룹)
```

## 🎨 파라미터 시스템

### 파라미터 타입 지원
```python
parameter_types = {
    "integer": {"min_value": 1, "max_value": 200, "default": 14},
    "float": {"min_value": 0.1, "max_value": 5.0, "default": 2.0},
    "enum": {"options": ["close", "open", "high", "low"], "default": "close"},
    "boolean": {"default": True},
    "string": {"pattern": r"^[A-Z_]+$", "default": "DEFAULT"}
}
```

### 동적 파라미터 위젯 생성
```python
class ParameterWidgetFactory:
    def create_parameter_widgets(self, variable_id: str, params: dict, layout):
        """변수별 파라미터에 맞는 UI 위젯 동적 생성"""
        for param_name, param_config in params.items():
            if param_config['type'] == 'integer':
                widget = self.create_integer_widget(param_config)
            elif param_config['type'] == 'enum':
                widget = self.create_enum_widget(param_config)
            # ... 타입별 위젯 생성
            layout.addWidget(widget)
```

## 🔍 호환성 검증 시스템

### 통합 호환성 검증기
```python
from .shared.compatibility_validator import check_compatibility

# 기본 사용법
is_compatible, reason = check_compatibility("RSI", "STOCHASTIC")
# Result: (True, "호환 (기본: 같은 카테고리: momentum, 고급: 완전 호환)")

# 상세 정보 포함
is_compatible, reason = check_compatibility("RSI", "MACD")
# Result: (False, "비호환 (기본: 다른 카테고리: momentum vs momentum, 고급: 비호환)")
```

### 3단계 검증 로직
1. **카테고리 검증**: purpose_category 일치 확인
2. **스케일 검증**: comparison_group 일치 확인  
3. **고급 검증**: VariableType, ScaleType 세부 분석

## 📊 실제 활용 예시

### 성공적인 조건 조합
```python
# ✅ RSI + 스토캐스틱 (같은 오실레이터)
condition_1 = {
    "base_variable": {"id": "RSI", "params": {"period": 14}},
    "external_variable": {"id": "STOCHASTIC", "params": {"k_period": 14}},
    "operator": ">",
    "comparison_type": "external"
}

# ✅ 현재가 + 이동평균 (같은 가격 단위)
condition_2 = {
    "base_variable": {"id": "CURRENT_PRICE", "params": {}},
    "external_variable": {"id": "SMA", "params": {"period": 20}},
    "operator": ">",
    "comparison_type": "external"
}
```

### 차단되는 조건 조합
```python
# ❌ RSI + MACD (스케일 불일치)
# RSI: 0-100% vs MACD: 무제한 범위

# ❌ 현재가 + 거래량 (단위 불일치)  
# 가격(원화) vs 거래량(개수)

# ❌ RSI + 거래량 (의미 불일치)
# 퍼센트 지표 vs 수량 지표
```

## 🚀 개발 워크플로우

### 1. 새로운 변수 추가
```sql
-- 1. 변수 정의 추가
INSERT INTO trading_variables VALUES (
    'NEW_INDICATOR', '새로운지표', 'New Indicator', 
    'momentum', 'subplot', 'percentage_comparable', 
    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 
    '새로운 모멘텀 지표', 'custom'
);

-- 2. 파라미터 정의 추가
INSERT INTO variable_parameters VALUES (
    NULL, 'NEW_INDICATOR', 'period', 'integer', '14', 
    1, 100, NULL, 1, '기간', 'Period', 
    '계산 기간', 1, CURRENT_TIMESTAMP
);
```

### 2. UI 자동 업데이트
- 변수 콤보박스에 자동 표시
- 파라미터 위젯 자동 생성
- 호환성 검증 자동 적용

### 3. 테스트 절차
```powershell
# 전체 시스템 테스트
python run_desktop_ui.py

# 트리거 빌더 → 조건 생성 → 파라미터 설정 → 저장 → 로드 검증
```

## 📈 확장성 고려사항

### 미래 개선 방향
1. **AI 기반 파라미터 최적화**: 과거 데이터 기반 자동 파라미터 추천
2. **조건 템플릿 시스템**: 자주 사용되는 조건 조합의 템플릿화
3. **백테스팅 연동**: 조건 생성 후 즉시 백테스팅 실행
4. **시각적 조건 빌더**: 드래그앤드롭 방식의 비주얼 조건 생성기

### 성능 최적화
- 데이터베이스 인덱스 최적화
- 조건 검증 로직 캐싱
- 대용량 파라미터 처리 최적화

---

## 📚 관련 문서

- **기술 세부사항**: `docs/TRADING_VARIABLES_DB_SCHEMA.md`
- **구현 계획**: `docs/TRADING_VARIABLES_IMPLEMENTATION_PLAN.md`
- **변수 호환성**: `.vscode/guides/variable-compatibility.md`
- **컴포넌트 가이드**: `trigger_builder/README.md`
