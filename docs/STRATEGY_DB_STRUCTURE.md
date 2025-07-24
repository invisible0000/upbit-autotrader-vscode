# DB 구조: 전략과 트리거 조합 저장 방식

## 📊 데이터베이스 스키마 구조

### 1. 개별 트리거 저장 (기존)
```sql
-- 개별 조건/트리거 테이블
CREATE TABLE trading_conditions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,                    -- "RSI 과매도 신호"
    variable_name TEXT NOT NULL,           -- "rsi_14"
    operator TEXT NOT NULL,                -- "<="
    target_value TEXT NOT NULL,            -- "30"
    category TEXT DEFAULT 'unknown',       -- "indicator"
    external_variable TEXT,                -- JSON: 외부 변수 참조
    created_at DATETIME,
    -- 기타 메타데이터...
);
```

### 2. 전략 저장 (신규 - 2단계 구조)

#### A. 메인 전략 테이블
```sql
CREATE TABLE component_strategy (
    id TEXT PRIMARY KEY,                   -- UUID
    name TEXT NOT NULL,                    -- "RSI + 볼린저 밴드 전략"
    description TEXT,                      -- 전략 설명
    triggers TEXT NOT NULL,                -- JSON: 전체 트리거 조합 구조
    conditions TEXT,                       -- JSON: 추가 조건들
    actions TEXT NOT NULL,                 -- JSON: 매수/매도 액션
    category TEXT DEFAULT 'user_created',
    difficulty TEXT DEFAULT 'intermediate',
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);
```

#### B. 전략 구성 요소 테이블 (세부 분해)
```sql
CREATE TABLE strategy_components (
    id TEXT PRIMARY KEY,                   -- UUID
    strategy_id TEXT NOT NULL,             -- 전략 ID 참조
    component_type TEXT NOT NULL,          -- 'entry_condition', 'exit_condition', 'risk_management'
    component_data TEXT NOT NULL,          -- JSON: 개별 트리거 데이터
    order_index INTEGER DEFAULT 0,        -- 실행 순서
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME,
    FOREIGN KEY(strategy_id) REFERENCES component_strategy(id)
);
```

## 🔄 저장 방식 예시

### 사용자가 만든 전략:
**"RSI 과매도 + 볼린저 하단 터치 매수 전략"**

### 1단계: component_strategy 테이블
```json
{
  "id": "strategy-uuid-123",
  "name": "RSI + 볼린저 밴드 전략",
  "description": "RSI 과매도 구간에서 볼린저 하단 터치 시 매수",
  "triggers": {
    "entry_conditions": [
      {
        "id": "condition-uuid-456",
        "name": "RSI 과매도",
        "variable_name": "rsi_14",
        "operator": "<=",
        "target_value": "30",
        "category": "indicator"
      },
      {
        "id": "condition-uuid-789", 
        "name": "볼린저 하단 터치",
        "variable_name": "bb_lower",
        "operator": "<=",
        "target_value": "current_price",
        "category": "indicator"
      }
    ],
    "exit_conditions": [
      {
        "id": "condition-uuid-101",
        "name": "RSI 과매수",
        "variable_name": "rsi_14",
        "operator": ">=", 
        "target_value": "70",
        "category": "indicator"
      }
    ],
    "entry_logic": "AND",  // 모든 진입 조건 만족
    "exit_logic": "OR"     // 하나라도 청산 조건 만족
  },
  "actions": {
    "buy_action": {
      "type": "market_buy",
      "conditions": "entry_conditions"
    },
    "sell_action": {
      "type": "market_sell",
      "conditions": "exit_conditions OR risk_management"
    },
    "risk_management": {
      "stop_loss": 3.0,      // 3% 손절
      "take_profit": 10.0,   // 10% 익절
      "position_size": 10.0, // 포지션 크기 10%
      "max_positions": 3     // 최대 3개 동시 포지션
    }
  }
}
```

### 2단계: strategy_components 테이블 (세부 분해)
```sql
-- 진입 조건 1
INSERT INTO strategy_components VALUES (
  'comp-uuid-001',
  'strategy-uuid-123',
  'entry_condition',
  '{"id": "condition-uuid-456", "name": "RSI 과매도", "variable_name": "rsi_14", "operator": "<=", "target_value": "30"}',
  0,  -- 첫 번째 조건
  1,
  '2025-07-23T22:24:14.592500'
);

-- 진입 조건 2  
INSERT INTO strategy_components VALUES (
  'comp-uuid-002',
  'strategy-uuid-123',
  'entry_condition',
  '{"id": "condition-uuid-789", "name": "볼린저 하단 터치", "variable_name": "bb_lower", "operator": "<=", "target_value": "current_price"}',
  1,  -- 두 번째 조건
  1,
  '2025-07-23T22:24:14.592500'
);

-- 청산 조건
INSERT INTO strategy_components VALUES (
  'comp-uuid-003',
  'strategy-uuid-123',
  'exit_condition',
  '{"id": "condition-uuid-101", "name": "RSI 과매수", "variable_name": "rsi_14", "operator": ">=", "target_value": "70"}',
  0,  -- 첫 번째 청산 조건
  1,
  '2025-07-23T22:24:14.592500'
);

-- 리스크 관리
INSERT INTO strategy_components VALUES (
  'comp-uuid-004',
  'strategy-uuid-123',
  'risk_management',
  '{"stop_loss": 3.0, "take_profit": 10.0, "position_size": 10.0, "max_positions": 3}',
  999,  -- 마지막 순서
  1,
  '2025-07-23T22:24:14.592500'
);
```

## 🎯 핵심 설계 특징

### 1. **이중 저장 구조**
- **메인 테이블**: 전체 전략을 JSON으로 통합 저장 (빠른 조회)
- **컴포넌트 테이블**: 개별 조건들을 분해해서 저장 (세밀한 분석)

### 2. **트리거 재사용성**
- 기존 `trading_conditions`의 트리거들을 **참조**해서 조합
- 트리거 자체는 독립적으로 관리
- 전략은 트리거들의 **조합 설정**만 저장

### 3. **논리 연산 지원**
```json
{
  "entry_logic": "AND",  // 모든 진입 조건 만족
  "exit_logic": "OR"     // 하나라도 청산 조건 만족
}
```

### 4. **확장 가능한 구조**
- 새로운 조건 타입 쉽게 추가 가능
- 복합 로직 (중첩 AND/OR) 지원 준비
- 외부 변수 참조 지원

## 🔍 조회 방식

### 전략 실행 시:
1. `component_strategy`에서 전략 기본 정보 조회
2. `triggers` JSON에서 조합 로직 파악
3. `strategy_components`에서 개별 조건 상세 정보 조회
4. 실시간 데이터와 비교하여 조건 평가

### 분석 시:
- 개별 조건별 성과 분석
- 조건 조합 효과 분석
- 전략 최적화를 위한 데이터 수집

이런 구조로 **트리거의 재사용성**과 **전략의 복잡성**을 모두 지원하면서도 **성능**을 보장할 수 있습니다.
