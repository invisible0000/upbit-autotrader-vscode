# 전략 조합 시스템 설계 및 관리 가이드

## 📋 개요

**⚠️ 주의: 이 문서는 레거시 시스템 문서입니다.**

**현재 활성 시스템**: 원자적 전략 빌더 (`ui_prototypes/`)  
**참조 문서**: `ui_prototypes/basic_7_rule_strategy_guide.md`  
**개발 로드맵**: `STRATEGY_BUILDER_ROADMAP.md`

---

## 🚀 **현재 시스템: 원자적 전략 빌더 (Phase 1 완료)**

### 🧩 **새로운 아키텍처: Variable → Condition → Action → Rule → Strategy**

원자적 전략 빌더는 전략 조합을 더 직관적이고 유연하게 구현합니다:

1. **Variable**: RSI, 가격, 볼륨 등 기본 데이터
2. **Condition**: Variable에 대한 논리적 판단 (`rsi < 20`)
3. **Action**: 실제 거래 행동 (`market_buy 5%`)
4. **Rule**: Condition + Action 조합 ("RSI < 20이면 5% 매수")
5. **Strategy**: 여러 Rule의 집합 (완전한 매매 전략)

### 📖 **실제 사용 예제**

7규칙 기본 전략을 통해 완전한 매매 시스템을 5분 내에 구현할 수 있습니다.
자세한 내용은 `ui_prototypes/basic_7_rule_strategy_guide.md`를 참조하세요.

---

## 📚 **레거시 시스템 문서 (참고용)**

**전략 조합(Strategy Combination)**은 개별 전략들을 논리적으로 결합하여 완전한 트레이딩 시스템을 구성하는 고급 아키텍처입니다. 단순한 전략 나열이 아닌, 지능적인 조합 규칙과 상호작용 메커니즘을 포함합니다.

---

## 🏗️ 조합 아키텍처 (Combination Architecture)

### 🎯 **조합 계층 구조**

```
Portfolio Level           📊 포트폴리오 (다중 조합 관리)
    ↑
Combination Level         🎪 전략 조합 (단일 트레이딩 시스템)
    ↑
Strategy Level           🧩 개별 전략 (최소 실행 단위)
    ↑
Indicator Level          📈 기술적 지표 (데이터 소스)
```

### 🔧 **조합 컴포넌트**

#### 1. **조합 메타데이터 (Combination Metadata)**
```python
combination_schema = {
    "combination_id": "combo_001",
    "combination_name": "RSI + MACD 스윙 트레이딩",
    "description": "RSI 과매도 구간에서 MACD 골든크로스 확인 후 매수",
    "version": "1.2.0",
    "author": "strategy_team",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T15:45:00Z",
    "is_active": True,
    "risk_category": "MEDIUM",
    "target_instruments": ["KRW-BTC", "KRW-ETH"],
    "timeframes": ["1h", "4h"]
}
```

#### 2. **전략 구성 (Strategy Composition)**
```python
strategy_composition = {
    "entry_strategies": [
        {
            "strategy_id": "rsi_oversold",
            "weight": 0.6,
            "trigger_mode": "PRIMARY",
            "dependencies": []
        },
        {
            "strategy_id": "macd_golden_cross",
            "weight": 0.4,
            "trigger_mode": "CONFIRMATION",
            "dependencies": ["rsi_oversold"]
        }
    ],
    "exit_strategies": [
        {
            "strategy_id": "trailing_stop_5pct",
            "weight": 1.0,
            "trigger_mode": "GUARDIAN",
            "dependencies": []
        },
        {
            "strategy_id": "rsi_overbought_exit",
            "weight": 0.8,
            "trigger_mode": "PROFIT_TAKING",
            "dependencies": []
        }
    ]
}
```

---

## ⚙️ 조합 규칙 엔진 (Combination Rules Engine)

### 🎭 **트리거 모드 (Trigger Modes)**

#### 📍 **PRIMARY (주 전략)**
- **역할**: 독립적으로 신호 생성 가능
- **특징**: 다른 전략에 의존하지 않음
- **활용**: 주요 진입/청산 신호 담당

```python
class PrimaryTrigger:
    def __init__(self, strategy, weight=1.0):
        self.strategy = strategy
        self.weight = weight
        self.can_trigger_alone = True
    
    def evaluate(self, market_data):
        signal = self.strategy.generate_signal(market_data)
        if signal:
            signal.confidence *= self.weight
        return signal
```

#### 🔍 **CONFIRMATION (확인 전략)**
- **역할**: 다른 전략의 신호를 확인/검증
- **특징**: 의존 전략이 활성화된 후에만 작동
- **활용**: 거짓 신호 필터링, 신호 강화

```python
class ConfirmationTrigger:
    def __init__(self, strategy, dependencies, weight=1.0):
        self.strategy = strategy
        self.dependencies = dependencies
        self.weight = weight
        self.requires_confirmation = True
    
    def evaluate(self, market_data, dependency_signals):
        # 의존 전략들이 모두 활성화되었는지 확인
        if not all(dep.is_active for dep in dependency_signals):
            return None
            
        signal = self.strategy.generate_signal(market_data)
        if signal:
            signal.confidence *= self.weight
        return signal
```

---

## 🔄 **실제 조합 실행 플로우 (Combination Execution Flow)**

### **🎯 조합 전략 실행 생명주기**

```python
class CombinationExecutionFlow:
    """조합 전략 실행 플로우"""
    
    def __init__(self, combination_config):
        self.state = "WAITING"  # WAITING → ENTRY → POSITION → EXIT → COMPLETED
        self.position = None
        self.entry_strategies = combination_config["entry_strategies"]
        self.management_strategies = combination_config["management_strategies"]
        self.exit_strategies = combination_config["exit_strategies"]
    
    def execute_cycle(self, market_data):
        """매 사이클마다 실행되는 핵심 로직"""
        
        if self.state == "WAITING":
            # 📊 진입 조건 평가
            entry_decision = self._evaluate_entry_combination(market_data)
            if entry_decision["should_enter"]:
                self._execute_entry(entry_decision)
                self.state = "POSITION"
                
        elif self.state == "POSITION":
            # 🛡️ 관리 조건 평가 (피라미딩, 부분청산 등)
            management_actions = self._evaluate_management_combination(market_data)
            if management_actions:
                self._execute_management(management_actions)
            
            # 🚪 청산 조건 평가
            exit_decision = self._evaluate_exit_combination(market_data)
            if exit_decision["should_exit"]:
                self._execute_exit(exit_decision)
                self.state = "COMPLETED"
    
    def _evaluate_entry_combination(self, market_data):
        """진입 조건 조합 평가"""
        # 1단계: 모든 진입 전략 신호 수집
        entry_signals = []
        for strategy in self.entry_strategies:
            signal = strategy.generate_signal(market_data)
            if signal:
                entry_signals.append({
                    "strategy_id": strategy.id,
                    "signal": signal,
                    "weight": strategy.weight,
                    "trigger_mode": strategy.trigger_mode
                })
        
        # 2단계: 조합 규칙 적용
        primary_signals = [s for s in entry_signals if s["trigger_mode"] == "PRIMARY"]
        confirmation_signals = [s for s in entry_signals if s["trigger_mode"] == "CONFIRMATION"]
        
        # 3단계: 최종 결정
        decision = {"should_enter": False, "confidence": 0.0, "reasoning": []}
        
        if primary_signals:
            # PRIMARY 신호가 있으면 기본 신뢰도 계산
            primary_confidence = sum(s["signal"].confidence * s["weight"] for s in primary_signals)
            decision["confidence"] = primary_confidence
            decision["reasoning"].append(f"Primary signals: {len(primary_signals)}")
            
            # CONFIRMATION 신호로 신뢰도 증폭
            if confirmation_signals:
                confirmation_boost = sum(s["signal"].confidence * s["weight"] for s in confirmation_signals) * 0.3
                decision["confidence"] += confirmation_boost
                decision["reasoning"].append(f"Confirmation boost: +{confirmation_boost:.2f}")
            
            # 최종 진입 결정 (60% 이상 신뢰도)
            if decision["confidence"] >= 0.6:
                decision["should_enter"] = True
                decision["reasoning"].append(f"Entry approved: {decision['confidence']:.2f} >= 0.6")
        
        return decision
    
    def _evaluate_management_combination(self, market_data):
        """관리 조건 조합 평가"""
        actions = []
        
        for strategy in self.management_strategies:
            signal = strategy.generate_signal(market_data, self.position)
            if signal:
                if signal.signal_type == "ADD_BUY":
                    # 피라미딩 검증
                    if self._validate_add_buy(signal):
                        actions.append({
                            "type": "ADD_BUY",
                            "amount": signal.additional_data["add_amount"],
                            "strategy": strategy.id,
                            "reason": signal.reason
                        })
                
                elif signal.signal_type == "PARTIAL_EXIT":
                    # 부분 청산 검증
                    if self._validate_partial_exit(signal):
                        actions.append({
                            "type": "PARTIAL_EXIT",
                            "ratio": signal.additional_data["exit_ratio"],
                            "strategy": strategy.id,
                            "reason": signal.reason
                        })
        
        return actions
    
    def _evaluate_exit_combination(self, market_data):
        """청산 조건 조합 평가"""
        exit_signals = []
        
        for strategy in self.exit_strategies:
            signal = strategy.generate_signal(market_data, self.position)
            if signal:
                exit_signals.append({
                    "strategy_id": strategy.id,
                    "signal": signal,
                    "priority": self._get_exit_priority(signal.signal_type),
                    "urgency": signal.additional_data.get("urgency", "NORMAL")
                })
        
        # 우선순위 정렬 (STOP_LOSS > TRAILING > TAKE_PROFIT)
        exit_signals.sort(key=lambda x: x["priority"])
        
        decision = {"should_exit": False, "exit_type": None, "reasoning": []}
        
        if exit_signals:
            # 가장 높은 우선순위 신호 채택
            top_signal = exit_signals[0]
            
            if top_signal["urgency"] == "URGENT":
                # 긴급 청산 (손절 등)
                decision["should_exit"] = True
                decision["exit_type"] = "URGENT"
                decision["reasoning"].append(f"Urgent exit: {top_signal['signal'].signal_type}")
            
            elif top_signal["signal"].confidence >= 0.7:
                # 일반 청산
                decision["should_exit"] = True
                decision["exit_type"] = "NORMAL"
                decision["reasoning"].append(f"Normal exit: {top_signal['signal'].signal_type}")
        
        return decision
```

### **🎪 개별 감시 vs 조합 감시 전략**

#### **통합 감시 시스템 (Unified Monitoring System)**

```python
class UnifiedMonitoringSystem:
    """통합 감시 시스템 - 모든 전략을 하나의 엔진에서 조율"""
    
    def __init__(self, combination_config):
        self.all_strategies = self._categorize_strategies(combination_config)
        self.current_state = "NO_POSITION"
        self.position_context = None
        
    def monitor_cycle(self, market_data):
        """통합 감시 사이클"""
        monitoring_result = {
            "timestamp": market_data["timestamp"],
            "active_strategies": [],
            "signals_generated": [],
            "actions_taken": []
        }
        
        # 현재 상태에 따라 활성화할 전략 그룹 결정
        active_strategy_groups = self._get_active_strategy_groups()
        
        for group_name, strategies in active_strategy_groups.items():
            group_signals = []
            
            for strategy in strategies:
                # 개별 전략 실행 (중복 계산 방지)
                signal = self._execute_strategy_with_cache(strategy, market_data)
                if signal:
                    group_signals.append(signal)
            
            # 그룹별 조합 로직 적용
            group_decision = self._apply_group_combination_logic(group_name, group_signals)
            
            if group_decision["action_required"]:
                monitoring_result["actions_taken"].append(group_decision)
                self._update_system_state(group_decision)
        
        return monitoring_result
    
    def _get_active_strategy_groups(self):
        """현재 상태에 따른 활성 전략 그룹 반환"""
        active_groups = {}
        
        if self.current_state == "NO_POSITION":
            # 포지션 없음 → 진입 전략만 활성화
            active_groups["entry"] = self.all_strategies["entry"]
            active_groups["filters"] = self.all_strategies["filters"]
            
        elif self.current_state == "POSITION_ACTIVE":
            # 포지션 보유 → 관리/청산 전략 활성화
            active_groups["management"] = self.all_strategies["management"]  
            active_groups["exit"] = self.all_strategies["exit"]
            
        return active_groups
    
    def _apply_group_combination_logic(self, group_name, signals):
        """그룹별 조합 로직 적용"""
        if group_name == "entry":
            return self._combine_entry_signals(signals)
        elif group_name == "management":
            return self._combine_management_signals(signals)
        elif group_name == "exit":
            return self._combine_exit_signals(signals)
        else:
            return {"action_required": False}
    
    def _combine_entry_signals(self, signals):
        """진입 신호 조합 로직"""
        # PRIMARY + CONFIRMATION 조합
        primary_signals = [s for s in signals if s.trigger_mode == "PRIMARY"]
        confirmation_signals = [s for s in signals if s.trigger_mode == "CONFIRMATION"]
        
        if primary_signals:
            total_confidence = sum(s.confidence * s.weight for s in primary_signals)
            if confirmation_signals:
                total_confidence += sum(s.confidence * s.weight for s in confirmation_signals) * 0.3
            
            if total_confidence >= 0.6:
                return {
                    "action_required": True,
                    "action_type": "ENTER_POSITION",
                    "confidence": total_confidence,
                    "contributing_signals": len(signals)
                }
        
        return {"action_required": False}
    
    def _combine_exit_signals(self, signals):
        """청산 신호 조합 로직"""
        # 우선순위 기반 조합 (STOP_LOSS > TRAILING > TAKE_PROFIT)
        if not signals:
            return {"action_required": False}
        
        # 긴급 신호 우선 처리
        urgent_signals = [s for s in signals if s.additional_data.get("urgency") == "URGENT"]
        if urgent_signals:
            return {
                "action_required": True,
                "action_type": "EXIT_POSITION",
                "exit_mode": "URGENT",
                "signal_source": urgent_signals[0].strategy_id
            }
        
        # 일반 신호 평가
        high_confidence_signals = [s for s in signals if s.confidence >= 0.7]
        if high_confidence_signals:
            return {
                "action_required": True,
                "action_type": "EXIT_POSITION", 
                "exit_mode": "NORMAL",
                "signal_source": high_confidence_signals[0].strategy_id
            }
        
        return {"action_required": False}
```

---

## 🚀 **백테스트 통합 실행 예제**

### **📊 완전한 백테스트 시나리오**

```python
# 조합 전략 설정
combination_config = {
    "combination_id": "rsi_macd_trailing_combo",
    "combination_name": "RSI + MACD + 트레일링 스탑 조합",
    "symbol": "KRW-BTC",
    "timeframe": "1h",
    
    "entry_strategies": [
        {
            "strategy_id": "rsi_oversold",
            "trigger_mode": "PRIMARY",
            "weight": 0.6,
            "parameters": {"rsi_period": 14, "oversold_threshold": 30}
        },
        {
            "strategy_id": "macd_golden_cross",
            "trigger_mode": "CONFIRMATION", 
            "weight": 0.4,
            "parameters": {"fast_period": 12, "slow_period": 26}
        }
    ],
    
    "management_strategies": [
        {
            "strategy_id": "upward_pyramiding",
            "weight": 1.0,
            "parameters": {
                "add_trigger_percent": 0.05,
                "add_amount": 100000,
                "max_add_count": 3
            }
        }
    ],
    
    "exit_strategies": [
        {
            "strategy_id": "trailing_stop",
            "weight": 1.0,
            "parameters": {"trail_percent": 0.03, "activation_percent": 0.02}
        },
        {
            "strategy_id": "fixed_stop_loss",
            "weight": 1.0,
            "parameters": {"stop_loss_percent": 0.05}
        }
    ]
}

# 백테스트 실행
def run_complete_backtest():
    # 1. 조합 전략 실행 엔진 초기화
    combo_executor = CombinationExecutionFlow(combination_config)
    
    # 2. 시장 데이터 로드
    market_data = load_market_data("KRW-BTC", "2024-01-01", "2024-06-01", "1h")
    
    # 3. 시뮬레이션 실행
    execution_log = []
    
    for data_point in market_data:
        # 매 시간마다 전략 실행
        cycle_result = combo_executor.execute_cycle(data_point)
        execution_log.append(cycle_result)
        
        # 상태 변화 로깅
        if cycle_result.get("state_changed"):
            print(f"⚡ 상태 변화: {cycle_result['old_state']} → {cycle_result['new_state']}")
            
        # 거래 실행 로깅  
        if cycle_result.get("trade_executed"):
            trade = cycle_result["trade_executed"]
            print(f"💰 거래 실행: {trade['type']} | 가격: {trade['price']} | 수량: {trade['quantity']}")
    
    # 4. 성과 분석
    performance = analyze_performance(execution_log)
    
    print(f"""
    🎯 백테스트 결과:
    📈 총 거래 횟수: {performance['total_trades']}
    💰 총 수익률: {performance['total_return']:.2f}%
    📉 최대 낙폭: {performance['max_drawdown']:.2f}%
    🎪 조합 효과: {performance['combination_benefit']:.2f}%
    """)
    
    return execution_log, performance

# 백테스트 실행
if __name__ == "__main__":
    log, perf = run_complete_backtest()
```
            # 의존 신호들과 결합하여 최종 신호 강도 계산
            combined_confidence = self.combine_with_dependencies(
                signal.confidence, dependency_signals
            )
            signal.confidence = combined_confidence * self.weight
        return signal
```

#### 🛡️ **GUARDIAN (보호 전략)**
- **역할**: 지속적인 리스크 모니터링
- **특징**: 항상 활성화 상태, 다른 신호보다 우선
- **활용**: 손절, 긴급 청산

```python
class GuardianTrigger:
    def __init__(self, strategy, priority=1):
        self.strategy = strategy
        self.priority = priority  # 낮을수록 높은 우선순위
        self.always_active = True
    
    def evaluate(self, market_data, current_position):
        if not current_position:
            return None
            
        signal = self.strategy.generate_signal(market_data)
        if signal and signal.action in ["SELL", "STOP_LOSS"]:
            signal.priority = self.priority
            signal.override_other_signals = True
        return signal
```

### 🔗 **조합 로직 패턴**

#### 1. **AND 조합 (All-Required)**
```python
class ANDCombination:
    """모든 전략이 동시에 신호를 발생시켜야 실행"""
    
    def combine_signals(self, signals):
        if not all(signal.is_active for signal in signals):
            return None
        
        # 가장 약한 신호의 강도를 기준으로 조합
        min_confidence = min(signal.confidence for signal in signals)
        combined_signal = Signal(
            action=signals[0].action,
            confidence=min_confidence,
            timestamp=signals[0].timestamp
        )
        return combined_signal
```

#### 2. **OR 조합 (Any-Sufficient)**
```python
class ORCombination:
    """임의의 전략이 신호를 발생시키면 실행"""
    
    def combine_signals(self, signals):
        active_signals = [s for s in signals if s.is_active]
        if not active_signals:
            return None
        
        # 가장 강한 신호를 선택
        strongest_signal = max(active_signals, key=lambda s: s.confidence)
        return strongest_signal
```

#### 3. **WEIGHTED 조합 (Weighted Average)**
```python
class WeightedCombination:
    """가중평균으로 신호 강도 계산"""
    
    def __init__(self, strategy_weights):
        self.strategy_weights = strategy_weights
    
    def combine_signals(self, signals):
        weighted_sum = 0
        total_weight = 0
        
        for signal in signals:
            if signal.is_active:
                weight = self.strategy_weights.get(signal.strategy_id, 1.0)
                weighted_sum += signal.confidence * weight
                total_weight += weight
        
        if total_weight == 0:
            return None
        
        combined_confidence = weighted_sum / total_weight
        return Signal(
            action=signals[0].action,  # 주 전략의 액션 사용
            confidence=combined_confidence,
            timestamp=signals[0].timestamp
        )
```

---

## 🕐 실행 순서 및 우선순위 (Execution Order & Priority)

### 📊 **실행 파이프라인**

```
1. 데이터 수집
   ↓
2. 개별 전략 신호 생성
   ↓
3. 의존성 해결 (Dependency Resolution)
   ↓
4. 조합 규칙 적용
   ↓
5. 우선순위 정렬
   ↓
6. 신호 검증 및 필터링
   ↓
7. 최종 실행 신호 출력
```

### ⚡ **우선순위 체계**

#### **Level 1: EMERGENCY (긴급)**
- **우선순위**: 1-10
- **대상**: 손절, 시스템 보호 신호
- **특징**: 다른 모든 신호를 오버라이드

```python
emergency_strategies = [
    {"strategy": "emergency_stop_loss", "priority": 1},
    {"strategy": "margin_call_protection", "priority": 2},
    {"strategy": "system_failure_exit", "priority": 3}
]
```

#### **Level 2: MANAGEMENT (관리)**
- **우선순위**: 11-50
- **대상**: 일반적인 위험 관리 신호
- **특징**: 진입 신호보다 우선하지만 긴급 신호에는 후순위

```python
management_strategies = [
    {"strategy": "trailing_stop", "priority": 15},
    {"strategy": "profit_taking", "priority": 20},
    {"strategy": "position_sizing", "priority": 25}
]
```

#### **Level 3: ENTRY (진입)**
- **우선순위**: 51-100
- **대상**: 새로운 포지션 생성 신호
- **특징**: 가장 낮은 우선순위

```python
entry_strategies = [
    {"strategy": "primary_entry", "priority": 60},
    {"strategy": "confirmation_entry", "priority": 70},
    {"strategy": "opportunity_entry", "priority": 80}
]
```

---

## 🎪 조합 타입별 구현 패턴

### 🏹 **진입 조합 패턴**

#### **1. 다단계 확인 패턴 (Multi-Stage Confirmation)**
```python
entry_combination = {
    "name": "다단계 RSI-MACD 진입",
    "pattern": "STAGED_CONFIRMATION",
    "stages": [
        {
            "stage": 1,
            "strategy": "rsi_oversold",
            "threshold": 0.6,
            "timeout": "1h"
        },
        {
            "stage": 2,
            "strategy": "macd_golden_cross",
            "threshold": 0.7,
            "timeout": "30m",
            "requires": [1]
        },
        {
            "stage": 3,
            "strategy": "volume_surge",
            "threshold": 0.5,
            "timeout": "15m",
            "requires": [1, 2]
        }
    ],
    "execution": {
        "min_stages": 2,
        "max_wait_time": "2h"
    }
}
```

#### **2. 대기 패턴 (Waiting Pattern)**
```python
waiting_combination = {
    "name": "타이밍 대기 조합",
    "pattern": "WAIT_AND_CONFIRM",
    "primary_signal": "bollinger_band_squeeze",
    "waiting_conditions": [
        {
            "condition": "volatility_breakout",
            "timeout": "4h"
        },
        {
            "condition": "volume_confirmation",
            "timeout": "1h"
        }
    ],
    "execution_window": "30m"
}
```

### 🛡️ **위험 관리 조합 패턴**

#### **1. 계층적 손절 패턴**
```python
risk_management_combination = {
    "name": "다층 리스크 관리",
    "pattern": "LAYERED_PROTECTION",
    "layers": [
        {
            "layer": "hard_stop",
            "strategy": "fixed_stop_loss",
            "threshold": 0.05,  # 5% 손실
            "priority": 1
        },
        {
            "layer": "soft_stop", 
            "strategy": "trailing_stop",
            "threshold": 0.03,  # 3% 트레일링
            "priority": 10
        },
        {
            "layer": "smart_exit",
            "strategy": "rsi_divergence_exit",
            "threshold": 0.7,
            "priority": 20
        }
    ]
}
```

#### **2. 적응형 포지션 사이징**
```python
position_sizing_combination = {
    "name": "동적 포지션 관리",
    "pattern": "ADAPTIVE_SIZING",
    "base_size": 0.1,  # 기본 10%
    "modifiers": [
        {
            "factor": "volatility",
            "strategy": "atr_based_sizing",
            "multiplier": -0.5  # 변동성 높으면 크기 감소
        },
        {
            "factor": "confidence",
            "strategy": "signal_strength_sizing", 
            "multiplier": 0.3   # 신뢰도 높으면 크기 증가
        },
        {
            "factor": "market_regime",
            "strategy": "trend_based_sizing",
            "multiplier": 0.2   # 트렌드 강하면 크기 증가
        }
    ],
    "limits": {
        "min_size": 0.01,   # 최소 1%
        "max_size": 0.25    # 최대 25%
    }
}
```

---

## 📊 상태 관리 및 동기화 (State Management)

### 🔄 **조합 상태 머신**

```python
class CombinationStateMachine:
    """조합의 생명주기를 관리하는 상태 머신"""
    
    states = [
        "INITIALIZED",    # 초기화됨
        "WAITING",        # 신호 대기 중
        "TRIGGERED",      # 신호 발생됨
        "EXECUTING",      # 실행 중
        "MANAGING",       # 포지션 관리 중
        "COMPLETED",      # 완료됨
        "FAILED"          # 실패함
    ]
    
    def __init__(self, combination_config):
        self.config = combination_config
        self.current_state = "INITIALIZED"
        self.state_history = []
        self.context = {}
    
    def transition_to(self, new_state, reason=None):
        """상태 전환"""
        old_state = self.current_state
        self.current_state = new_state
        
        self.state_history.append({
            "from": old_state,
            "to": new_state,
            "timestamp": datetime.now(),
            "reason": reason
        })
        
        # 상태별 액션 실행
        self._execute_state_action(new_state)
    
    def _execute_state_action(self, state):
        """상태별 액션 실행"""
        actions = {
            "WAITING": self._start_signal_monitoring,
            "TRIGGERED": self._prepare_execution,
            "EXECUTING": self._execute_trade,
            "MANAGING": self._start_position_management,
            "COMPLETED": self._cleanup_resources
        }
        
        action = actions.get(state)
        if action:
            action()
```

### 📝 **컨텍스트 공유 메커니즘**

```python
class CombinationContext:
    """조합 내 전략 간 정보 공유를 위한 컨텍스트"""
    
    def __init__(self):
        self.shared_data = {}
        self.signals_history = []
        self.execution_log = []
        self.performance_metrics = {}
    
    def set_shared_data(self, key, value, strategy_id=None):
        """공유 데이터 설정"""
        self.shared_data[key] = {
            "value": value,
            "timestamp": datetime.now(),
            "source_strategy": strategy_id
        }
    
    def get_shared_data(self, key, default=None):
        """공유 데이터 조회"""
        data = self.shared_data.get(key, {})
        return data.get("value", default)
    
    def log_signal(self, signal):
        """신호 이력 기록"""
        self.signals_history.append({
            "signal": signal,
            "timestamp": datetime.now()
        })
    
    def log_execution(self, execution_result):
        """실행 결과 기록"""
        self.execution_log.append({
            "result": execution_result,
            "timestamp": datetime.now()
        })
```

---

## 🔬 성능 측정 및 최적화

### 📈 **조합 성능 메트릭**

```python
combination_metrics = {
    "profitability": {
        "total_return": 0.15,      # 15% 수익률
        "sharpe_ratio": 1.8,       # 샤프 비율
        "max_drawdown": 0.08,      # 최대 손실
        "win_rate": 0.65           # 승률 65%
    },
    "efficiency": {
        "signal_accuracy": 0.72,   # 신호 정확도
        "execution_speed": 1.2,    # 평균 실행 시간 (초)
        "resource_usage": 0.3,     # CPU/메모리 사용률
        "false_signal_rate": 0.15  # 거짓 신호 비율
    },
    "robustness": {
        "market_adaptability": 0.8,    # 시장 적응성
        "parameter_sensitivity": 0.2,  # 파라미터 민감도
        "stress_test_score": 0.9       # 스트레스 테스트 점수
    }
}
```

### 🎯 **최적화 전략**

#### **1. 파라미터 최적화**
```python
class CombinationOptimizer:
    def __init__(self, combination):
        self.combination = combination
        self.optimization_history = []
    
    def optimize_weights(self, market_data, target_metric="sharpe_ratio"):
        """전략 가중치 최적화"""
        from scipy.optimize import minimize
        
        def objective(weights):
            # 가중치 설정
            self.combination.set_strategy_weights(weights)
            
            # 백테스트 실행
            results = self.backtest(market_data)
            
            # 목표 메트릭 반환 (최대화를 위해 음수)
            return -results[target_metric]
        
        # 제약 조건: 가중치 합 = 1, 모든 가중치 >= 0
        constraints = [
            {"type": "eq", "fun": lambda w: sum(w) - 1},
            {"type": "ineq", "fun": lambda w: w}
        ]
        
        result = minimize(
            objective, 
            x0=self.combination.get_initial_weights(),
            constraints=constraints,
            method="SLSQP"
        )
        
        return result.x
```

#### **2. 동적 적응 최적화**
```python
class AdaptiveOptimizer:
    def __init__(self, combination, adaptation_interval="1d"):
        self.combination = combination
        self.adaptation_interval = adaptation_interval
        self.performance_window = 30  # 30일 성능 윈도우
    
    def adaptive_rebalance(self, current_performance):
        """성능 기반 동적 리밸런싱"""
        
        # 최근 성능 분석
        recent_performance = self.analyze_recent_performance()
        
        # 시장 체제 감지
        market_regime = self.detect_market_regime()
        
        # 전략별 기여도 분석
        strategy_contributions = self.analyze_strategy_contributions()
        
        # 새로운 가중치 계산
        new_weights = self.calculate_adaptive_weights(
            recent_performance, 
            market_regime, 
            strategy_contributions
        )
        
        # 가중치 업데이트
        self.combination.update_strategy_weights(new_weights)
        
        return new_weights
```

---

## 🚀 고급 기능 및 확장성

### 🤖 **머신러닝 기반 조합**

```python
class MLEnhancedCombination:
    """머신러닝으로 강화된 전략 조합"""
    
    def __init__(self, base_combination):
        self.base_combination = base_combination
        self.ml_model = None
        self.feature_extractor = FeatureExtractor()
    
    def train_ml_layer(self, historical_data, target_returns):
        """ML 레이어 훈련"""
        
        # 특성 추출
        features = self.feature_extractor.extract_features(
            historical_data, 
            self.base_combination.get_strategy_signals()
        )
        
        # 모델 훈련
        from sklearn.ensemble import RandomForestRegressor
        
        self.ml_model = RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )
        
        self.ml_model.fit(features, target_returns)
    
    def generate_enhanced_signal(self, market_data):
        """ML로 강화된 신호 생성"""
        
        # 기본 조합 신호
        base_signal = self.base_combination.generate_signal(market_data)
        
        if not base_signal or not self.ml_model:
            return base_signal
        
        # ML 특성 추출
        features = self.feature_extractor.extract_current_features(market_data)
        
        # ML 예측
        ml_confidence = self.ml_model.predict([features])[0]
        
        # 신호 강화
        enhanced_signal = base_signal.copy()
        enhanced_signal.confidence = (
            base_signal.confidence * 0.7 + 
            ml_confidence * 0.3
        )
        
        return enhanced_signal
```

### 🌐 **분산 실행 아키텍처**

```python
class DistributedCombination:
    """분산 환경에서 실행되는 전략 조합"""
    
    def __init__(self, combination_config, node_count=4):
        self.config = combination_config
        self.node_count = node_count
        self.strategy_allocation = self._allocate_strategies_to_nodes()
    
    def _allocate_strategies_to_nodes(self):
        """전략을 노드에 할당"""
        strategies = self.config["strategies"]
        allocation = {}
        
        for i, strategy in enumerate(strategies):
            node_id = i % self.node_count
            if node_id not in allocation:
                allocation[node_id] = []
            allocation[node_id].append(strategy)
        
        return allocation
    
    async def execute_distributed_signals(self, market_data):
        """분산 신호 실행"""
        import asyncio
        
        # 각 노드에서 병렬 실행
        tasks = []
        for node_id, strategies in self.strategy_allocation.items():
            task = self._execute_node_strategies(node_id, strategies, market_data)
            tasks.append(task)
        
        # 모든 노드 결과 수집
        node_results = await asyncio.gather(*tasks)
        
        # 결과 조합
        combined_signal = self._combine_distributed_results(node_results)
        
        return combined_signal
```

---

## 📚 조합 라이브러리 및 템플릿

### 📖 **사전 정의된 조합 템플�트**

```python
COMBINATION_TEMPLATES = {
    "trend_following": {
        "name": "트렌드 추종 조합",
        "description": "강한 트렌드에서 수익을 추구하는 조합",
        "strategies": [
            {"type": "moving_average_cross", "role": "entry", "weight": 0.5},
            {"type": "macd_trend", "role": "confirmation", "weight": 0.3},
            {"type": "trailing_stop", "role": "exit", "weight": 1.0}
        ],
        "suitable_market": "TRENDING",
        "risk_level": "MEDIUM"
    },
    
    "mean_reversion": {
        "name": "평균 회귀 조합", 
        "description": "과매수/과매도 구간에서 반전을 노리는 조합",
        "strategies": [
            {"type": "rsi_reversal", "role": "entry", "weight": 0.6},
            {"type": "bollinger_bounce", "role": "confirmation", "weight": 0.4},
            {"type": "fixed_profit_target", "role": "exit", "weight": 1.0}
        ],
        "suitable_market": "SIDEWAYS",
        "risk_level": "HIGH"
    },
    
    "breakout": {
        "name": "돌파 전략 조합",
        "description": "박스권 돌파를 포착하는 조합",
        "strategies": [
            {"type": "volatility_breakout", "role": "entry", "weight": 0.7},
            {"type": "volume_confirmation", "role": "confirmation", "weight": 0.3},
            {"type": "volatility_stop", "role": "exit", "weight": 1.0}
        ],
        "suitable_market": "VOLATILE",
        "risk_level": "HIGH"
    }
}
```

### 🏭 **조합 빌더 유틸리티**

```python
class CombinationBuilder:
    """전략 조합을 쉽게 구성할 수 있는 빌더"""
    
    def __init__(self):
        self.combination = {
            "entry_strategies": [],
            "exit_strategies": [],
            "filters": [],
            "rules": {}
        }
    
    def add_entry_strategy(self, strategy_type, weight=1.0, trigger_mode="PRIMARY"):
        """진입 전략 추가"""
        self.combination["entry_strategies"].append({
            "strategy_type": strategy_type,
            "weight": weight,
            "trigger_mode": trigger_mode
        })
        return self
    
    def add_exit_strategy(self, strategy_type, weight=1.0, trigger_mode="GUARDIAN"):
        """청산 전략 추가"""
        self.combination["exit_strategies"].append({
            "strategy_type": strategy_type,
            "weight": weight,
            "trigger_mode": trigger_mode
        })
        return self
    
    def set_combination_rule(self, rule_type, parameters):
        """조합 규칙 설정"""
        self.combination["rules"][rule_type] = parameters
        return self
    
    def build(self):
        """최종 조합 객체 생성"""
        return StrategyCombination(self.combination)

# 사용 예시
combination = (CombinationBuilder()
    .add_entry_strategy("rsi_reversal", weight=0.6, trigger_mode="PRIMARY")
    .add_entry_strategy("macd_cross", weight=0.4, trigger_mode="CONFIRMATION")
    .add_exit_strategy("trailing_stop", weight=1.0, trigger_mode="GUARDIAN")
    .set_combination_rule("entry_logic", {"type": "AND", "timeout": "2h"})
    .build())
```

---

> **🎯 핵심 원칙**: "전략 조합은 단순한 전략의 합이 아니라, 시너지를 창출하는 지능적인 시스템이어야 합니다."
