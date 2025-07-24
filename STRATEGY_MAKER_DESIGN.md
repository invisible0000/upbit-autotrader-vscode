# 전략 메이커 시스템 설계 문서

## 📊 전체 아키텍처 개요

### 핵심 개념
**전략 = 매수 조건 + 매도 조건 + 리스크 관리**

```
트리거 (개별 조건) → 전략 (조건 조합) → 실거래 시스템
```

## 🗃️ 데이터베이스 스키마

### 1. 기존 트리거 시스템 (완성됨)
```sql
-- 개별 조건/트리거 저장
CREATE TABLE trading_conditions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    variable_name TEXT NOT NULL,
    operator TEXT NOT NULL,
    target_value TEXT NOT NULL,
    category TEXT DEFAULT 'unknown',
    created_at DATETIME,
    -- 추가 메타데이터...
);
```

### 2. 새로운 전략 시스템 (신규 구현)
```sql
-- 메인 전략 테이블
CREATE TABLE component_strategy (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,                    -- 전략명
    description TEXT,                      -- 전략 설명
    triggers TEXT NOT NULL,                -- JSON: 진입/청산 조건들
    conditions TEXT,                       -- JSON: 추가 조건들
    actions TEXT NOT NULL,                 -- JSON: 매수/매도 액션
    category TEXT DEFAULT 'user_created',  -- 전략 카테고리
    difficulty TEXT DEFAULT 'intermediate', -- 난이도
    is_active BOOLEAN DEFAULT 1,           -- 활성 상태
    is_template BOOLEAN DEFAULT 0,         -- 템플릿 여부
    performance_metrics TEXT,              -- JSON: 성과 지표
    created_at DATETIME,
    updated_at DATETIME
);

-- 전략 구성 요소 (트리거별 상세)
CREATE TABLE strategy_components (
    id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    component_type TEXT NOT NULL,          -- 'entry_condition', 'exit_condition', 'risk_management'
    component_data TEXT NOT NULL,          -- JSON: 트리거 데이터
    order_index INTEGER DEFAULT 0,        -- 순서
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME,
    FOREIGN KEY(strategy_id) REFERENCES component_strategy(id)
);

-- 전략 실행 기록
CREATE TABLE strategy_execution (
    id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    symbol TEXT NOT NULL,                  -- 거래 심볼
    trigger_type TEXT NOT NULL,            -- 'entry' or 'exit'
    action_type TEXT NOT NULL,             -- 'buy' or 'sell'
    market_data TEXT,                      -- JSON: 시장 데이터
    result TEXT NOT NULL,                  -- 'success', 'failed', 'pending'
    result_details TEXT,                   -- 상세 결과
    position_tag TEXT,                     -- 포지션 태그
    executed_at DATETIME,
    FOREIGN KEY(strategy_id) REFERENCES component_strategy(id)
);
```

## 🏗️ 전략 구조 예시

### 예시 전략: "RSI 역전 + 볼린저 밴드"
```json
{
    "name": "RSI 역전 + 볼린저 밴드 전략",
    "description": "RSI 과매도 구간에서 볼린저 하단 터치 시 매수",
    "triggers": {
        "entry_conditions": [
            {
                "id": "rsi_condition_123",
                "name": "RSI 과매도",
                "variable_name": "rsi_14",
                "operator": "<=",
                "target_value": "30"
            },
            {
                "id": "bb_condition_456", 
                "name": "볼린저 하단 터치",
                "variable_name": "bb_lower",
                "operator": "<=",
                "target_value": "current_price"
            }
        ],
        "exit_conditions": [
            {
                "id": "rsi_exit_789",
                "name": "RSI 과매수",
                "variable_name": "rsi_14", 
                "operator": ">=",
                "target_value": "70"
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
            "take_profit": 10.0,    // 10% 익절
            "position_size": 10.0,  // 포지션 크기 10%
            "max_positions": 3      // 최대 3개 동시 포지션
        }
    }
}
```

## 🔄 워크플로우

### 1단계: 트리거 선택 (좌측 영역)
- 기존 트리거 빌더에서 생성한 조건들 표시
- 검색 및 필터링 기능
- 드래그 앤 드롭으로 전략에 추가

### 2단계: 전략 구성 (중앙 영역)
- **진입 조건 탭**: 매수 신호 조건들
- **청산 조건 탭**: 매도 신호 조건들
- **조합 로직**: AND/OR/사용자 정의
- **전략 미리보기**: 실시간 전략 구조 표시

### 3단계: 리스크 관리 & 검증 (우측 영역)
- **리스크 설정**: 손절/익절/포지션 사이징
- **검증 기능**: 
  - 구문 검증
  - 빠른 시뮬레이션
  - 히스토리컬 백테스트

## 💡 핵심 설계 특징

### 1. 컴포넌트 재사용성
- 개별 트리거들을 다양한 전략에서 재사용
- 검증된 조건들의 조합으로 안정성 확보

### 2. 점진적 복잡성
- 간단한 단일 조건 → 복합 조건 → 전략
- 초보자도 쉽게 시작할 수 있는 구조

### 3. 실시간 검증
- 전략 구성 중 실시간 구문 검증
- 시뮬레이션을 통한 사전 테스트

### 4. 확장 가능한 구조
- 새로운 조건 타입 쉽게 추가 가능
- 플러그인 방식의 리스크 관리 모듈

## 🚀 구현 우선순위

### Phase 1: 기본 전략 구성 (완료)
- [x] 전략 메이커 UI 구조
- [x] 트리거 선택 및 조합 기능
- [x] 기본 리스크 관리 설정

### Phase 2: 검증 및 시뮬레이션
- [ ] 전략 구문 검증 엔진
- [ ] 빠른 시뮬레이션 (가상 데이터)
- [ ] 히스토리컬 백테스팅 연동

### Phase 3: 실거래 연동
- [ ] 전략 → 실거래 시스템 브릿지
- [ ] 실시간 포지션 관리
- [ ] 리스크 모니터링

### Phase 4: 고급 기능
- [ ] 전략 템플릿 시스템
- [ ] 성과 분석 및 최적화
- [ ] 소셜 트레이딩 (전략 공유)

## 🔗 시스템 연동점

### 기존 시스템과의 통합
1. **트리거 빌더** → 전략 메이커 (조건 공유)
2. **전략 메이커** → 백테스팅 (전략 검증)
3. **전략 메이커** → 실거래 시스템 (전략 배포)
4. **실거래 시스템** → 전략 분석 (성과 피드백)

### 데이터 흐름
```
Conditions DB → Strategy Maker → Component Strategy DB → Trading Engine
     ↓                ↓                    ↓                    ↓
Trigger Builder → Strategy Preview → Backtest Engine → Real Trading
```

이 설계를 통해 안정적이고 확장 가능한 전략 시스템을 구축할 수 있습니다.
