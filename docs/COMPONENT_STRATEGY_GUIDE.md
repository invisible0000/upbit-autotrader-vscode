# 컴포넌트 전략 시스템 가이드

## 📋 개요

**컴포넌트 전략 시스템**은 아토믹 컴포넌트(트리거, 액션)를 자유롭게 조합하여 무한한 전략 생성이 가능한 차세대 아키텍처입니다. 기존 고정 전략 클래스의 한계를 극복하고 사용자 친화적인 드래그&드롭 인터페이스를 제공합니다.

---

## 🧩 컴포넌트 아키텍처

### 🎯 **아토믹 컴포넌트 구조**

```
Strategy Instance         🎪 전략 인스턴스 (완전한 거래 로직)
    ↑
Component Combination     🔗 컴포넌트 조합 (트리거 + 액션)
    ↑
Atomic Components        ⚛️ 아토믹 컴포넌트 (최소 기능 단위)
    ↑
Market Data              📊 시장 데이터 (가격, 지표, 거래량)
```

### 🔧 **컴포넌트 유형**

#### 1️⃣ **트리거 컴포넌트 (Trigger Components)**
시장 상황을 감지하고 전략 실행 조건을 판단하는 컴포넌트

| 카테고리 | 컴포넌트 | 설명 |
|---------|---------|------|
| **Price** | PriceChangeTrigger | 가격 변동율 감지 |
| | PriceBreakoutTrigger | 가격 범위 돌파 |
| | PriceCrossoverTrigger | 가격 기준선 교차 |
| **Indicator** | RSITrigger | RSI 과매수/과매도 |
| | MACDTrigger | MACD 시그널 |
| | BollingerBandTrigger | 볼린저 밴드 터치 |
| | MovingAverageCrossTrigger | 이동평균 교차 |
| **Time** | PeriodicTrigger | 주기적 실행 |
| | ScheduledTrigger | 특정 시간 실행 |
| | DelayTrigger | 지연 후 실행 |
| **Volume** | VolumeSurgeTrigger | 거래량 급증 |
| | VolumeDropTrigger | 거래량 급락 |
| | RelativeVolumeTrigger | 상대적 거래량 |
| | VolumeBreakoutTrigger | 거래량 돌파 |

#### 2️⃣ **액션 컴포넌트 (Action Components)**
트리거 발생 시 실제 거래 행동을 수행하는 컴포넌트

| 액션 | 설명 | 파라미터 |
|------|------|----------|
| **MarketBuyAction** | 시장가 매수 | amount_percent, max_amount |
| **MarketSellAction** | 시장가 매도 | amount_percent, min_amount |
| **PositionCloseAction** | 포지션 청산 | close_percent, position_tag |

---

## 🏷️ 태그 기반 포지션 관리

### 포지션 태그 시스템
전략 간 충돌을 방지하고 안전한 거래를 보장하는 핵심 메커니즘

```python
class PositionTag(Enum):
    AUTO = "AUTO"       # 자동 전략이 생성한 포지션
    MANUAL = "MANUAL"   # 수동으로 생성한 포지션  
    HYBRID = "HYBRID"   # 혼합 관리 포지션
    LOCKED = "LOCKED"   # 잠금된 포지션
```

### 액세스 제어 매트릭스

| 포지션 태그 | 자동 전략 | 수동 조작 | 설명 |
|------------|----------|----------|------|
| **AUTO** | ✅ 허용 | ❌ 금지 | 자동 전략 전용 |
| **MANUAL** | ❌ 금지 | ✅ 허용 | 수동 조작 전용 |
| **HYBRID** | ✅ 허용 | ✅ 허용 | 혼합 관리 |
| **LOCKED** | ❌ 금지 | ❌ 금지 | 완전 잠금 |

### 충돌 방지 예시
```python
def execute_action(self, action: BaseAction, position: TaggedPosition):
    # 태그 기반 액세스 제어
    if position.tag == PositionTag.AUTO and action.source == "MANUAL":
        raise PositionAccessDenied("AUTO 포지션은 수동 조작할 수 없습니다")
    
    if position.tag == PositionTag.LOCKED:
        raise PositionAccessDenied("LOCKED 포지션은 어떤 조작도 불가합니다")
    
    # 안전한 액션 실행
    return action.execute(position)
```

---

## 🎨 전략 메이커 UI

### 드래그&드롭 인터페이스
사용자가 시각적으로 전략을 구성할 수 있는 직관적 인터페이스

```
┌─────────────┬─────────────────────┬─────────────┐
│ 컴포넌트    │     전략 캔버스       │   설정 패널  │
│   팔레트    │                     │            │
│            │  ┌─[트리거]─→[액션]─┐  │  ┌─설정─┐  │
│ 📊 Price   │  │                │  │  │ RSI  │  │
│ 📈 Indicator│  └─[트리거]─→[액션]─┘  │  │ 30   │  │
│ ⏰ Time     │                     │  └──────┘  │
│ 📊 Volume   │                     │            │
│ 🛒 Actions  │                     │            │
└─────────────┴─────────────────────┴─────────────┘
```

### 전략 구성 플로우
1. **컴포넌트 선택**: 팔레트에서 원하는 트리거/액션 선택
2. **캔버스 배치**: 드래그&드롭으로 캔버스에 배치
3. **연결 생성**: 트리거와 액션 간 논리적 연결
4. **설정 조정**: 우측 패널에서 상세 파라미터 설정
5. **전략 저장**: 완성된 전략을 데이터베이스에 저장

---

## 💾 데이터 모델

### ComponentStrategy 스키마
```python
class ComponentStrategy:
    id: str                    # 고유 식별자
    name: str                  # 전략 이름
    description: str           # 전략 설명
    triggers: List[Dict]       # 트리거 컴포넌트 목록
    conditions: List[Dict]     # 조건 컴포넌트 목록 (향후 확장)
    actions: List[Dict]        # 액션 컴포넌트 목록
    tags: List[str]           # 전략 태그
    category: str             # 카테고리
    difficulty: str           # 난이도
    is_active: bool           # 활성화 상태
    performance_metrics: Dict  # 성과 지표
    created_at: datetime      # 생성 시간
    updated_at: datetime      # 수정 시간
```

### 전략 데이터 예시
```json
{
  "id": "strategy_001",
  "name": "RSI 과매도 매수 전략",
  "description": "RSI가 30 이하로 떨어질 때 시장가 매수",
  "triggers": [
    {
      "type": "rsi",
      "config": {
        "threshold": 30,
        "period": 14,
        "direction": "below"
      }
    }
  ],
  "actions": [
    {
      "type": "market_buy",
      "config": {
        "amount_percent": 10,
        "position_tag": "AUTO"
      }
    }
  ],
  "tags": ["technical", "reversal"],
  "category": "mean_reversion",
  "difficulty": "beginner"
}
```

---

## 🚀 전략 실행 엔진

### 이벤트 기반 실행
```python
class ComponentExecutionEngine:
    def on_market_data(self, market_data: MarketData):
        for strategy in self.active_strategies:
            # 모든 트리거 검사
            for trigger in strategy.triggers:
                if trigger.evaluate(market_data):
                    # 트리거 발생 시 액션 실행
                    self.execute_actions(strategy.actions, market_data)
    
    def execute_actions(self, actions: List[Action], market_data: MarketData):
        for action in actions:
            # 포지션 태그 검사
            if self.check_position_access(action):
                result = action.execute(market_data)
                self.log_execution(action, result)
```

### 실행 기록 추적
```python
class StrategyExecution:
    id: str                   # 실행 기록 ID
    strategy_id: str          # 전략 ID
    trigger_type: str         # 발생한 트리거
    action_type: str          # 실행된 액션
    market_data: Dict         # 실행 시점 시장 데이터
    result: str              # 실행 결과 (SUCCESS/FAILED/SKIPPED)
    result_details: Dict      # 상세 결과
    position_tag: str        # 포지션 태그
    executed_at: datetime    # 실행 시간
```

---

## 📊 템플릿 시스템

### 사전 정의된 전략 템플릿
사용자가 쉽게 시작할 수 있도록 검증된 전략 패턴 제공

```python
STRATEGY_TEMPLATES = {
    "rsi_reversal": {
        "name": "RSI 반전 전략",
        "description": "RSI 과매도/과매수 구간에서 반전 매매",
        "category": "reversal",
        "difficulty": "beginner",
        "template_data": {
            "triggers": [
                {
                    "type": "rsi",
                    "config": {"threshold": 30, "period": 14}
                }
            ],
            "actions": [
                {
                    "type": "market_buy",
                    "config": {"amount_percent": 10}
                }
            ]
        }
    },
    "macd_momentum": {
        "name": "MACD 모멘텀 전략", 
        "description": "MACD 골든크로스/데드크로스 추세 매매",
        "category": "momentum",
        "difficulty": "intermediate",
        "template_data": {
            "triggers": [
                {
                    "type": "macd",
                    "config": {"fast_period": 12, "slow_period": 26}
                }
            ],
            "actions": [
                {
                    "type": "market_buy",
                    "config": {"amount_percent": 15}
                }
            ]
        }
    }
}
```

### 템플릿 사용 플로우
1. **템플릿 선택**: 사전 정의된 템플릿 중 선택
2. **파라미터 조정**: 기본 설정을 사용자 환경에 맞게 수정
3. **전략 생성**: 템플릿 기반으로 새 전략 인스턴스 생성
4. **커스터마이징**: 추가 컴포넌트 조합으로 고도화

---

## 🔍 확장성 설계

### 새 컴포넌트 추가
```python
# 1. 새 트리거 정의
class CustomPatternTrigger(BaseTrigger):
    def __init__(self, config: Dict):
        self.pattern_type = config.get('pattern_type')
        self.confidence_threshold = config.get('confidence', 0.8)
    
    def evaluate(self, market_data: MarketData) -> bool:
        pattern_confidence = self.detect_pattern(market_data)
        return pattern_confidence >= self.confidence_threshold

# 2. 메타데이터 등록
TRIGGER_METADATA['custom_pattern'] = {
    'display_name': '패턴 인식 트리거',
    'category': 'advanced',
    'description': 'AI 기반 차트 패턴 감지',
    'difficulty': 'advanced'
}

# 3. 클래스 등록
TRIGGER_CLASSES['custom_pattern'] = CustomPatternTrigger
```

### 플러그인 구조
```python
class ComponentPlugin:
    def register(self):
        # 새 컴포넌트 등록
        pass
    
    def get_metadata(self) -> Dict:
        # 메타데이터 반환
        pass
    
    def get_config_schema(self) -> Dict:
        # 설정 스키마 반환
        pass
```

---

## 📈 성능 및 모니터링

### 전략 성과 추적
```python
class StrategyPerformanceTracker:
    def track_execution(self, strategy_id: str, result: ExecutionResult):
        # 실행 성공률 추적
        self.update_success_rate(strategy_id, result.success)
        
        # 수익률 계산
        if result.trade_completed:
            self.update_profitability(strategy_id, result.pnl)
        
        # 위험 지표 업데이트
        self.update_risk_metrics(strategy_id, result)
```

### 성과 지표
- **실행 성공률**: 트리거 발생 대비 성공적 실행 비율
- **수익률**: 전략별 수익성 분석
- **샤프 비율**: 위험 대비 수익률
- **최대 낙폭**: 최대 손실 구간
- **승률**: 수익 거래 대비 손실 거래 비율

---

## 🛡️ 리스크 관리

### 포지션 한도 관리
```python
class PositionLimitManager:
    def check_limits(self, action: MarketBuyAction, current_positions: List[Position]):
        total_exposure = sum(p.value for p in current_positions)
        new_exposure = action.calculate_exposure()
        
        if total_exposure + new_exposure > self.max_exposure:
            raise ExposureLimitExceeded("포지션 한도 초과")
```

### 동시 실행 제어
```python
class ConcurrencyController:
    def __init__(self):
        self.executing_strategies = set()
    
    def execute_if_not_busy(self, strategy_id: str, action: BaseAction):
        if strategy_id in self.executing_strategies:
            return ExecutionResult.SKIPPED("전략 실행 중")
        
        self.executing_strategies.add(strategy_id)
        try:
            return action.execute()
        finally:
            self.executing_strategies.remove(strategy_id)
```

---

## 📋 개발 로드맵

### Phase 1: 현재 완료 ✅
- [x] 아토믹 컴포넌트 시스템 (14 트리거 + 3 액션)
- [x] 전략 메이커 UI (드래그&드롭)
- [x] 태그 기반 포지션 관리
- [x] 컴포넌트 전략 매니저
- [x] 데이터베이스 모델 분리

### Phase 2: 진행 중 🚧
- [ ] 백테스팅 엔진 통합
- [ ] 전략 성과 분석 대시보드
- [ ] 템플릿 시스템 확장
- [ ] 실시간 실행 엔진

### Phase 3: 계획 📋
- [ ] 조건 컴포넌트 (Condition Components)
- [ ] 고급 트리거 (패턴 인식, 감정 분석)
- [ ] 머신러닝 통합
- [ ] 포트폴리오 레벨 최적화

---

## 🔧 개발자 가이드

### 새 컴포넌트 개발 체크리스트
1. **[ ] 기본 클래스 상속** (BaseTrigger/BaseAction)
2. **[ ] Config 클래스 정의** (설정 검증)
3. **[ ] evaluate/execute 메서드 구현** (핵심 로직)
4. **[ ] 메타데이터 등록** (UI 표시 정보)
5. **[ ] 단위 테스트 작성** (기능 검증)
6. **[ ] 통합 테스트** (실제 데이터 테스트)
7. **[ ] 문서화** (사용법 가이드)

### 코드 예시
```python
# 새 트리거 구현 예시
class VolumeWeightedPriceTrigger(BaseTrigger):
    """거래량 가중 평균 가격 기반 트리거"""
    
    def __init__(self, config: VWAPTriggerConfig):
        super().__init__(config)
        self.period = config.period
        self.threshold = config.threshold
    
    def evaluate(self, market_data: MarketData) -> bool:
        vwap = self.calculate_vwap(market_data, self.period)
        current_price = market_data.current_price
        
        deviation = (current_price - vwap) / vwap * 100
        return abs(deviation) >= self.threshold
    
    def calculate_vwap(self, market_data: MarketData, period: int) -> float:
        # VWAP 계산 로직
        pass
```

---

**⚠️ 중요**: 이 시스템은 기존 고정 전략 아키텍처를 완전히 대체하는 차세대 설계입니다. 모든 새로운 전략 개발은 이 컴포넌트 시스템을 기반으로 진행됩니다.
