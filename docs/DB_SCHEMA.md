# 🗄️ DDD 기반 데이터베이스 스키마 명세서

## 📋 개요

DDD 아키텍처 기반 업비트 자동매매 시스템은 **Domain-Driven 3-DB 아키텍처**를 사용하여 Domain Entity를 영속화합니다.

## 🏗️ DDD 기반 데이터베이스 아키텍처

### Infrastructure Layer의 Repository 구현

- **Domain Entity 매핑**: Aggregate Root를 데이터베이스 테이블로 매핑
- **Repository Pattern**: Domain Layer에서 정의한 Repository Interface 구현
- **Data Mapper**: Entity ↔ 데이터베이스 레코드 변환

### 1. `settings.sqlite3` - Domain Configuration

- **목적**: Domain Value Object와 Configuration Entity 저장
- **내용**: Trading Variable Entity, Parameter Value Object, Category Entity
- **특징**: Domain-driven 읽기 전용 구조

### 2. `strategies.sqlite3` - Strategy Aggregate

- **목적**: Strategy Aggregate Root와 관련 Entity 저장
- **내용**: Strategy Entity, Trading Rule Entity, Execution Record Entity
- **특징**: Domain Event 기반 읽기/쓰기

### 3. `market_data.sqlite3` - Market Data Aggregate

- **목적**: Market Data Entity와 Technical Indicator Value Object 저장
- **내용**: Price Entity, Volume Entity, Indicator Entity
- **특징**: Domain Service 기반 대용량 처리

## 📊 Settings.sqlite3 - Domain Configuration Schema

### Trading Variable Entity 매핑

```sql
-- Domain Entity: TradingVariable
CREATE TABLE tv_trading_variables (
    variable_id TEXT PRIMARY KEY,           -- VariableId Value Object
    display_name_ko TEXT NOT NULL,          -- DisplayName Value Object (Korean)
    display_name_en TEXT,                   -- DisplayName Value Object (English)
    purpose_category TEXT NOT NULL,         -- PurposeCategory Value Object
    chart_category TEXT NOT NULL,           -- ChartCategory Value Object
    comparison_group TEXT NOT NULL,         -- ComparisonGroup Value Object
    parameter_required BOOLEAN DEFAULT 0,   -- Domain Business Rule
    is_active BOOLEAN DEFAULT 1,           -- Entity State
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,                       -- Description Value Object
    source TEXT DEFAULT 'built-in'          -- Source Value Object
);
```

### Parameter Value Object 매핑

```sql
-- Domain Value Object: ParameterDefinition
CREATE TABLE tv_variable_parameters (
    parameter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL,              -- Aggregate Root Reference
    parameter_name TEXT NOT NULL,           -- ParameterName Value Object
    parameter_type TEXT NOT NULL,           -- ParameterType Value Object
    default_value TEXT,                     -- DefaultValue Value Object
    min_value TEXT,                         -- MinValue Value Object
    max_value TEXT,                         -- MaxValue Value Object
    enum_values TEXT,                       -- EnumOptions Value Object (JSON)
    is_required BOOLEAN DEFAULT 1,          -- RequiredFlag Business Rule
    display_name_ko TEXT NOT NULL,          -- DisplayName Value Object
    display_name_en TEXT,                   -- DisplayName Value Object
    description TEXT,                       -- Description Value Object
    display_order INTEGER DEFAULT 0,        -- DisplayOrder Value Object
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id) ON DELETE CASCADE
);
```

### Category Entity 매핑

```sql
-- Domain Entity: IndicatorCategory
CREATE TABLE tv_indicator_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_type TEXT NOT NULL,            -- CategoryType Value Object
    category_key TEXT NOT NULL,             -- CategoryKey Value Object
    category_name_ko TEXT NOT NULL,         -- CategoryName Value Object
    category_name_en TEXT NOT NULL,         -- CategoryName Value Object
    description TEXT,                       -- Description Value Object
    icon TEXT,                              -- Icon Value Object
    color_code TEXT,                        -- ColorCode Value Object
    display_order INTEGER DEFAULT 0,        -- DisplayOrder Value Object
    is_active BOOLEAN NOT NULL DEFAULT 1,  -- Entity State
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
