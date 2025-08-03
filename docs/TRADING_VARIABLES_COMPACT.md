# 🎯 트레이딩 변수 관리 시스템 (간결판)

## 📋 개요

트레이딩 지표 변수의 **호환성 관리**와 **체계적 분류**를 위한 DB 기반 관리 시스템입니다.

## 🎯 핵심 목표

1. **호환성 문제 해결**: SMA ↔ EMA 같은 지표 간 비교 가능성 자동 판단
2. **3중 카테고리 시스템**: purpose, chart, comparison 분류로 UI 최적화
3. **확장성**: 새 지표 추가 시 자동 분류 및 호환성 검증

## 🗄️ 핵심 DB 스키마

### 변수 메인 테이블
```sql
CREATE TABLE trading_variables (
    variable_id TEXT PRIMARY KEY,           -- 'SMA', 'RSI', 'MACD'
    display_name_ko TEXT NOT NULL,          -- '단순이동평균'
    purpose_category TEXT NOT NULL,         -- 'trend', 'momentum', 'volatility'
    chart_category TEXT NOT NULL,           -- 'overlay', 'subplot'
    comparison_group TEXT NOT NULL,         -- 'price_comparable', 'percentage_comparable'
    is_active BOOLEAN DEFAULT 1,
    description TEXT,
    source TEXT DEFAULT 'built-in'
);
```

### 파라미터 정의 테이블
```sql
CREATE TABLE variable_parameters (
    parameter_id INTEGER PRIMARY KEY,
    variable_id TEXT NOT NULL,
    parameter_name TEXT NOT NULL,           -- 'period', 'source'
    parameter_type TEXT NOT NULL,           -- 'integer', 'float', 'enum'
    default_value TEXT,
    min_value REAL,
    max_value REAL,
    enum_options TEXT,                      -- JSON 형태
    is_required BOOLEAN DEFAULT 1,
    display_name_ko TEXT NOT NULL,
    help_text TEXT
);
```

## 🔗 호환성 분류 체계

### Purpose Category (목적별)
```python
PURPOSE_CATEGORIES = {
    "trend": {
        "name_ko": "추세 지표",
        "variables": ["SMA", "EMA", "MACD"],
        "icon": "📈"
    },
    "momentum": {
        "name_ko": "모멘텀 지표", 
        "variables": ["RSI", "Stochastic"],
        "icon": "🚀"
    },
    "volatility": {
        "name_ko": "변동성 지표",
        "variables": ["Bollinger_Bands", "ATR"],
        "icon": "📊"
    }
}
```

### Chart Category (차트 표시)
```python
CHART_CATEGORIES = {
    "overlay": "가격 차트 위 오버레이",     # SMA, EMA, Bollinger
    "subplot": "별도 서브플롯"              # RSI, MACD, Stochastic
}
```

### Comparison Group (비교 가능성)
```python
COMPARISON_GROUPS = {
    "price_comparable": "가격과 직접 비교 가능",        # SMA, EMA, Close
    "percentage_comparable": "백분율 기준 비교",       # RSI, Stochastic  
    "zero_centered": "0 중심 지표"                    # MACD, Williams %R
}
```

## 🧩 호환성 검증 로직

### 기본 규칙
```python
class CompatibilityChecker:
    def check_compatibility(self, var1, var2):
        # 1. 같은 comparison_group = 직접 비교 가능
        if var1.comparison_group == var2.comparison_group:
            return "compatible"
        
        # 2. price_comparable vs percentage_comparable = 경고
        if self._needs_normalization(var1, var2):
            return "warning"
        
        # 3. 완전히 다른 스케일 = 비교 불가
        return "incompatible"
```

### 허용되는 조합 예시
```python
# ✅ 호환 가능
"SMA(20) > EMA(10)"      # 둘 다 price_comparable
"RSI > 70"               # percentage_comparable vs 고정값
"Close > SMA(20)"        # 정규화를 통한 비교

# ⚠️ 경고 (정규화 필요)
"Close > RSI"            # price vs percentage (자동 정규화)

# ❌ 비교 불가
"RSI > MACD"             # percentage vs zero_centered
```

## 💻 구현 클래스 구조

### 변수 관리자
```python
class TradingVariableManager:
    def __init__(self, db_path):
        self.db = DatabaseManager(db_path)
    
    def get_variables_by_category(self, purpose=None, chart=None):
        """카테고리별 변수 조회"""
        pass
    
    def check_compatibility(self, var1_id, var2_id):
        """두 변수 간 호환성 확인"""
        pass
    
    def add_new_variable(self, variable_def):
        """새 변수 추가 (자동 분류)"""
        pass
```

### 지표 분류기
```python
class IndicatorClassifier:
    def auto_classify(self, indicator_name, formula, output_range):
        """지표 특성 기반 자동 분류"""
        
        # Purpose 분류
        if "moving_average" in formula.lower():
            purpose = "trend"
        elif "rsi" in indicator_name.lower():
            purpose = "momentum"
        
        # Chart 분류
        if output_range == "price_level":
            chart = "overlay"
        else:
            chart = "subplot"
        
        # Comparison 분류
        if output_range == (0, 100):
            comparison = "percentage_comparable"
        elif "price" in output_range:
            comparison = "price_comparable"
        else:
            comparison = "zero_centered"
```

## 🧪 테스트 시나리오

### 호환성 테스트
```python
def test_compatibility_checking():
    manager = TradingVariableManager()
    
    # 같은 그룹 = 호환
    assert manager.check_compatibility("SMA", "EMA") == "compatible"
    
    # 다른 그룹 = 경고
    assert manager.check_compatibility("Close", "RSI") == "warning"
    
    # 비호환
    assert manager.check_compatibility("RSI", "MACD") == "incompatible"
```

### UI 통합 테스트
```python
def test_ui_integration():
    # 트리거 빌더에서 호환성 검증
    builder = TriggerBuilder()
    
    # 호환 가능한 조건 생성
    condition = builder.create_condition("SMA(20)", ">", "EMA(10)")
    assert condition.is_valid()
    
    # 비호환 조건은 에러
    with pytest.raises(IncompatibleVariableError):
        builder.create_condition("RSI", ">", "MACD")
```

## 📊 초기 데이터 세트

### 기본 지표 목록
```python
INITIAL_VARIABLES = [
    # 추세 지표 (price_comparable, overlay)
    {"id": "SMA", "name": "단순이동평균", "purpose": "trend", "chart": "overlay", "comparison": "price_comparable"},
    {"id": "EMA", "name": "지수이동평균", "purpose": "trend", "chart": "overlay", "comparison": "price_comparable"},
    
    # 모멘텀 지표 (percentage_comparable, subplot)
    {"id": "RSI", "name": "상대강도지수", "purpose": "momentum", "chart": "subplot", "comparison": "percentage_comparable"},
    {"id": "Stochastic", "name": "스토캐스틱", "purpose": "momentum", "chart": "subplot", "comparison": "percentage_comparable"},
    
    # 변동성 지표
    {"id": "BB_Upper", "name": "볼린저밴드상단", "purpose": "volatility", "chart": "overlay", "comparison": "price_comparable"},
    {"id": "BB_Lower", "name": "볼린저밴드하단", "purpose": "volatility", "chart": "overlay", "comparison": "price_comparable"},
    
    # 특수 지표 (zero_centered)
    {"id": "MACD", "name": "MACD", "purpose": "trend", "chart": "subplot", "comparison": "zero_centered"},
]
```

## 🚀 실행 방법

### 초기 설정
```python
# 1. DB 초기화
python -m upbit_auto_trading.utils.trading_variables.init_db

# 2. 기본 변수 로드
python -m upbit_auto_trading.utils.trading_variables.load_defaults

# 3. 호환성 테스트
python -m pytest tests/test_trading_variables.py
```

### CLI 도구 사용
```bash
# 변수 목록 조회
python tools/trading_variables_cli.py list --purpose=trend

# 호환성 확인
python tools/trading_variables_cli.py check SMA EMA

# 새 변수 추가
python tools/trading_variables_cli.py add --name="Custom_MA" --purpose=trend
```

## 📚 관련 문서

- [트리거 빌더 가이드](TRIGGER_BUILDER_GUIDE.md)
- [DB 스키마](DB_SCHEMA.md)
- [호환성 검증 상세](VARIABLE_COMPATIBILITY.md)
