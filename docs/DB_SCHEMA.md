# 🗄️ 데이터베이스 스키마 명세서

## 📋 개요

업비트 자동매매 시스템은 **3-DB 아키텍처**를 사용하여 구조 정의, 전략 인스턴스, 시장 데이터를 분리 관리합니다.

## 🏗️ 데이터베이스 아키텍처

### 1. `settings.sqlite3` - 구조 정의
- **목적**: 시스템 구조와 메타데이터 관리
- **내용**: 변수 정의, 파라미터 스키마, 카테고리 분류
- **특징**: 읽기 전용, 업데이트 시에만 변경

### 2. `strategies.sqlite3` - 전략 인스턴스  
- **목적**: 사용자 생성 전략과 조건 저장
- **내용**: 전략 조합, 백테스팅 결과, 실행 기록
- **특징**: 읽기/쓰기, 사용자별 개인화

### 3. `market_data.sqlite3` - 시장 데이터
- **목적**: 실시간/과거 시장 데이터 캐시
- **내용**: 가격 데이터, 기술적 지표, 거래량
- **특징**: 대용량, 자동 정리, 공유 가능

## 📊 Settings.sqlite3 스키마

### 트레이딩 변수 메인 테이블
```sql
CREATE TABLE tv_trading_variables (
    variable_id TEXT PRIMARY KEY,           -- 'SMA', 'RSI', 'MACD'
    display_name_ko TEXT NOT NULL,          -- '단순이동평균', 'RSI 지표'
    display_name_en TEXT,                   -- 'Simple Moving Average'
    purpose_category TEXT NOT NULL,         -- 'trend', 'momentum', 'volatility'
    chart_category TEXT NOT NULL,           -- 'overlay', 'subplot'
    comparison_group TEXT NOT NULL,         -- 'price_comparable', 'percentage_comparable'
    parameter_required BOOLEAN DEFAULT 0,   -- 파라미터 필요 여부
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,                       -- 지표 설명
    source TEXT DEFAULT 'built-in'          -- 'built-in', 'tradingview', 'custom'
);
```

### 변수 파라미터 정의 테이블
```sql
CREATE TABLE tv_variable_parameters (
    parameter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL,              -- 외래키: tv_trading_variables.variable_id
    parameter_name TEXT NOT NULL,           -- 'period', 'source', 'multiplier'
    parameter_type TEXT NOT NULL,           -- 'integer', 'float', 'string', 'boolean', 'enum'
    default_value TEXT,                     -- 기본값
    min_value TEXT,                         -- 최소값 (숫자 타입용)
    max_value TEXT,                         -- 최대값 (숫자 타입용)
    enum_values TEXT,                       -- JSON 형태의 선택 옵션
    is_required BOOLEAN DEFAULT 1,          -- 필수 파라미터 여부
    display_name_ko TEXT NOT NULL,          -- '기간', '데이터 소스'
    display_name_en TEXT,                   -- 'Period', 'Data Source'
    description TEXT,                       -- 파라미터 설명
    display_order INTEGER DEFAULT 0,        -- 표시 순서
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id) ON DELETE CASCADE
);
```

### 카테고리 관리 테이블
```sql
CREATE TABLE tv_indicator_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_type TEXT NOT NULL,            -- 'purpose', 'chart', 'comparison'
    category_key TEXT NOT NULL,             -- 'trend', 'overlay', 'price_comparable'
    category_name_ko TEXT NOT NULL,         -- '추세 지표', '오버레이'
    category_name_en TEXT NOT NULL,         -- 'Trend Indicators', 'Overlay'
    description TEXT,                       -- 카테고리 설명
    icon TEXT,                              -- UI 아이콘 ('📈', '🔗')
    color_code TEXT,                        -- 색상 코드 (#FF5733)
    display_order INTEGER DEFAULT 0,        -- 표시 순서
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 시스템 설정 테이블
```sql
CREATE TABLE cfg_app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 📈 Strategies.sqlite3 스키마

### 전략 메인 테이블
```sql
CREATE TABLE strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- 전략 이름
    description TEXT,                       -- 전략 설명
    strategy_type TEXT NOT NULL,            -- 'entry', 'management', 'combined'
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    use_count INTEGER DEFAULT 0,
    tags TEXT,                              -- JSON 형태 태그
    risk_level INTEGER DEFAULT 3,           -- 1(낮음) ~ 5(높음)
    expected_return REAL,                   -- 예상 수익률
    max_drawdown REAL                       -- 최대 손실률
);
```

### 전략 조건 테이블
```sql
CREATE TABLE strategy_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL,
    condition_name TEXT NOT NULL,           -- 조건 이름
    variable_id TEXT NOT NULL,              -- 기본 변수 ID
    variable_params TEXT,                   -- JSON: 변수 파라미터
    operator TEXT NOT NULL,                 -- '>', '>=', '<', '<=', '~=', '!='
    target_value TEXT,                      -- 비교값 (고정값 모드)
    external_variable TEXT,                 -- JSON: 외부변수 정보
    trend_direction TEXT DEFAULT 'both',    -- 'rising', 'falling', 'both'
    comparison_type TEXT DEFAULT 'fixed',   -- 'fixed', 'external'
    condition_group INTEGER DEFAULT 1,      -- 조건 그룹 (AND/OR 구분)
    logical_operator TEXT DEFAULT 'AND',    -- 'AND', 'OR'
    weight REAL DEFAULT 1.0,               -- 조건 가중치
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
);
```

### 백테스팅 결과 테이블
```sql
CREATE TABLE backtest_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,                   -- 'KRW-BTC'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_return REAL,                      -- 총 수익률 (%)
    annual_return REAL,                     -- 연간 수익률 (%)
    max_drawdown REAL,                      -- 최대 손실폭 (%)
    sharpe_ratio REAL,                      -- 샤프 비율
    win_rate REAL,                          -- 승률 (%)
    total_trades INTEGER,                   -- 총 거래 수
    avg_holding_time REAL,                  -- 평균 보유 시간 (시간)
    profit_factor REAL,                     -- 수익 팩터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
);
```

### 실행 기록 테이블
```sql
CREATE TABLE execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,                   -- 'BUY', 'SELL', 'HOLD'
    price REAL,                            -- 실행 가격
    quantity REAL,                         -- 거래량
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    order_id TEXT,                         -- 거래소 주문 ID
    status TEXT DEFAULT 'pending',          -- 'pending', 'completed', 'failed'
    error_message TEXT,                     -- 오류 메시지
    
    FOREIGN KEY (strategy_id) REFERENCES strategies(id)
);
```

## 📊 Market_data.sqlite3 스키마

### 가격 데이터 테이블
```sql
CREATE TABLE price_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,                   -- 'KRW-BTC'
    timestamp TIMESTAMP NOT NULL,
    timeframe TEXT NOT NULL,                -- '1m', '5m', '1h', '1d'
    open_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    close_price REAL NOT NULL,
    volume REAL NOT NULL,
    trade_value REAL,                       -- 거래대금
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, timestamp, timeframe)
);

-- 성능 최적화 인덱스
CREATE INDEX idx_price_data_symbol_time ON price_data(symbol, timestamp);
CREATE INDEX idx_price_data_timeframe ON price_data(timeframe, timestamp);
```

### 기술적 지표 캐시 테이블
```sql
CREATE TABLE indicator_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    timeframe TEXT NOT NULL,
    indicator_name TEXT NOT NULL,           -- 'SMA_20', 'RSI_14'
    indicator_params TEXT,                  -- JSON: 파라미터
    value REAL,                            -- 지표 값
    additional_data TEXT,                   -- JSON: 추가 데이터 (MACD의 경우)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, timestamp, timeframe, indicator_name, indicator_params)
);

-- 지표 캐시 인덱스
CREATE INDEX idx_indicator_cache_lookup ON indicator_cache(symbol, indicator_name, timestamp);
```

### 시장 정보 테이블
```sql
CREATE TABLE market_info (
    symbol TEXT PRIMARY KEY,               -- 'KRW-BTC'
    korean_name TEXT,                      -- '비트코인'
    english_name TEXT,                     -- 'Bitcoin'
    market_warning TEXT,                   -- 'NONE', 'CAUTION'
    is_active BOOLEAN DEFAULT 1,
    tick_size REAL,                        -- 최소 호가 단위
    min_order_amount REAL,                 -- 최소 주문 금액
    max_order_amount REAL,                 -- 최대 주문 금액
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 데이터베이스 관리

### 성능 최적화
```sql
-- 정기적 데이터 정리 (30일 이상 된 분봉 데이터)
DELETE FROM price_data 
WHERE timeframe = '1m' 
AND timestamp < date('now', '-30 days');

-- 지표 캐시 정리 (7일 이상 된 캐시)
DELETE FROM indicator_cache 
WHERE created_at < date('now', '-7 days');

-- 인덱스 재구성
REINDEX;
VACUUM;
```

### 백업 전략
```python
# 데이터베이스 백업 스케줄
{
    "settings.sqlite3": "주간 백업",      # 구조 변경 시에만
    "strategies.sqlite3": "일일 백업",    # 사용자 데이터 보호
    "market_data.sqlite3": "백업 제외"    # 재생성 가능
}
```

## 📚 관련 문서

- [트리거 빌더 가이드](TRIGGER_BUILDER_GUIDE.md)
- [전략 명세서](STRATEGY_SPECIFICATIONS.md)
- [데이터베이스 마이그레이션](DB_MIGRATION_GUIDE.md)
