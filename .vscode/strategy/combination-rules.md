# 🔗 전략 조합 규칙

> **참조**: `.vscode/project-specs.md`의 전략 시스템 핵심 섹션

## 🎯 조합 규칙 개요

**기본 구조**: 1개 진입 전략(필수) + 0~N개 관리 전략(선택)  
**최대 관리 전략**: 5개까지 조합 허용  
**충돌 해결**: 3가지 방식 지원 (priority/conservative/merge)  
**실행 순서**: parallel/sequential 선택 가능

## ✅ 유효한 조합 패턴

### 1. 기본 조합 (진입 + 1개 관리)
```python
# 예시: RSI 진입 + 트레일링 스탑
combination = {
    "name": "RSI 진입 + 트레일링 스탑",
    "entry_strategy": {
        "type": "rsi",
        "parameters": {"period": 14, "oversold": 30, "overbought": 70}
    },
    "management_strategies": [
        {
            "type": "trailing_stop",
            "parameters": {"trail_distance": 0.05, "activation_profit": 0.02},
            "priority": 1
        }
    ],
    "conflict_resolution": "priority",
    "execution_order": "parallel"
}
```

### 2. 복합 리스크 관리 조합
```python
# 예시: 이평교차 진입 + 물타기 + 고정손절 + 부분익절
combination = {
    "name": "이평교차 + 복합 리스크 관리",
    "entry_strategy": {
        "type": "moving_average_crossover",
        "parameters": {"short_period": 20, "long_period": 50, "ma_type": "EMA"}
    },
    "management_strategies": [
        {
            "type": "pyramid_buying",
            "parameters": {"trigger_drop_rate": 0.05, "max_additions": 3},
            "priority": 3  # 높은 우선순위
        },
        {
            "type": "fixed_exit",
            "parameters": {"stop_loss_rate": 0.10, "take_profit_rate": 0.15},
            "priority": 2
        },
        {
            "type": "partial_closing",
            "parameters": {"profit_levels": [0.05, 0.10], "closing_ratios": [0.5, 0.5]},
            "priority": 1
        }
    ],
    "conflict_resolution": "conservative",
    "execution_order": "parallel"
}
```

### 3. 최대 활용 조합 (5개 관리 전략)
```python
# 예시: 볼린저밴드 진입 + 모든 관리 전략
combination = {
    "name": "볼린저밴드 + 전면 관리",
    "entry_strategy": {
        "type": "bollinger_bands",
        "parameters": {"period": 20, "std_dev": 2.0, "strategy_type": "reversal"}
    },
    "management_strategies": [
        {"type": "pyramid_buying", "priority": 5},
        {"type": "trailing_stop", "priority": 4},
        {"type": "fixed_exit", "priority": 3},
        {"type": "partial_closing", "priority": 2},
        {"type": "time_based_closing", "priority": 1}
    ],
    "conflict_resolution": "merge",
    "execution_order": "sequential"
}
```

## 🚫 금지된 조합 패턴

### 1. 진입 전략 없음
```python
# ❌ 잘못된 조합 - 진입 전략 누락
invalid_combination = {
    "entry_strategy": None,  # 필수 항목 누락
    "management_strategies": [...]
}
```

### 2. 관리 전략 과다
```python
# ❌ 잘못된 조합 - 관리 전략 6개 이상
invalid_combination = {
    "management_strategies": [
        # 6개 이상의 관리 전략 - 복잡성 과다
    ]
}
```

### 3. 상충되는 관리 전략
```python
# ⚠️ 주의 필요 - 상충 가능한 조합
conflicting_combination = {
    "management_strategies": [
        {
            "type": "fixed_exit",
            "parameters": {"take_profit_rate": 0.10}  # 10% 익절
        },
        {
            "type": "partial_closing", 
            "parameters": {"profit_levels": [0.15]}   # 15% 부분 익절
        }
        # 익절 기준이 상충할 수 있음
    ]
}
```

## ⚖️ 충돌 해결 방식

### 1. Priority (우선순위) 방식
```python
class PriorityResolver:
    """우선순위 기반 충돌 해결"""
    
    def resolve(self, signals: List[Tuple[str, str, int]]) -> str:
        """높은 우선순위 전략의 신호 채택"""
        if not signals:
            return 'HOLD'
            
        # 우선순위로 정렬 (높은 숫자가 우선)
        sorted_signals = sorted(signals, key=lambda x: x[2], reverse=True)
        return sorted_signals[0][1]

# 사용 예시
signals = [
    ("trailing_stop", "CLOSE_POSITION", 4),
    ("pyramid_buying", "ADD_BUY", 3),
    ("fixed_exit", "HOLD", 2)
]
# 결과: "CLOSE_POSITION" (우선순위 4가 가장 높음)
```

### 2. Conservative (보수적) 방식
```python
class ConservativeResolver:
    """보수적 충돌 해결"""
    
    SIGNAL_PRIORITY = {
        'CLOSE_POSITION': 10,    # 청산이 최우선
        'UPDATE_STOP': 8,        # 손절선 업데이트
        'PARTIAL_CLOSE': 6,      # 부분 청산
        'HOLD': 4,               # 보유
        'ADD_BUY': 2,            # 추가 매수 (가장 보수적)
        'ADD_SELL': 2            # 추가 매도
    }
    
    def resolve(self, signals: List[Tuple[str, str, int]]) -> str:
        """보수적 우선순위로 해결"""
        if not signals:
            return 'HOLD'
            
        # 보수적 우선순위로 정렬
        sorted_signals = sorted(
            signals, 
            key=lambda x: self.SIGNAL_PRIORITY.get(x[1], 0), 
            reverse=True
        )
        return sorted_signals[0][1]

# 사용 예시
signals = [
    ("pyramid_buying", "ADD_BUY", 5),
    ("trailing_stop", "HOLD", 3),
    ("fixed_exit", "CLOSE_POSITION", 1)
]
# 결과: "CLOSE_POSITION" (보수적 우선순위가 가장 높음)
```

### 3. Merge (병합) 방식
```python
class MergeResolver:
    """신호 병합 해결"""
    
    def resolve(self, signals: List[Tuple[str, str, int]]) -> str:
        """신호들을 논리적으로 병합"""
        if not signals:
            return 'HOLD'
            
        signal_counts = {}
        for _, signal, priority in signals:
            if signal not in signal_counts:
                signal_counts[signal] = []
            signal_counts[signal].append(priority)
            
        # 청산 신호가 있으면 무조건 청산
        if 'CLOSE_POSITION' in signal_counts:
            return 'CLOSE_POSITION'
            
        # ADD_BUY 신호 병합 (수량 조정)
        if 'ADD_BUY' in signal_counts:
            buy_count = len(signal_counts['ADD_BUY'])
            avg_priority = sum(signal_counts['ADD_BUY']) / buy_count
            
            if buy_count > 1:
                # 다중 매수 신호를 하나로 병합
                return f'ADD_BUY:MERGED:{buy_count}:{avg_priority}'
            else:
                return 'ADD_BUY'
                
        # 기타 신호는 가장 빈번한 것 선택
        most_common_signal = max(signal_counts.keys(), key=lambda k: len(signal_counts[k]))
        return most_common_signal
```

## 🔄 실행 순서 관리

### 1. Parallel (병렬) 실행
```python
class ParallelExecutor:
    """병렬 전략 실행기"""
    
    def execute_strategies(self, position: PositionState, data: pd.DataFrame) -> List[str]:
        """모든 관리 전략을 동시에 실행"""
        signals = []
        
        for strategy in self.management_strategies:
            try:
                signal = strategy.generate_signal(position, data)
                if signal != 'HOLD':
                    signals.append((strategy.name, signal, strategy.priority))
            except Exception as e:
                logging.error(f"전략 {strategy.name} 실행 오류: {e}")
                
        return signals
```

### 2. Sequential (순차) 실행
```python
class SequentialExecutor:
    """순차 전략 실행기"""
    
    def execute_strategies(self, position: PositionState, data: pd.DataFrame) -> List[str]:
        """우선순위 순서로 전략 실행"""
        # 우선순위로 정렬
        sorted_strategies = sorted(
            self.management_strategies, 
            key=lambda s: s.priority, 
            reverse=True
        )
        
        signals = []
        current_position = position.copy()
        
        for strategy in sorted_strategies:
            try:
                signal = strategy.generate_signal(current_position, data)
                if signal != 'HOLD':
                    signals.append((strategy.name, signal, strategy.priority))
                    
                    # 신호에 따라 포지션 상태 업데이트
                    current_position = self._update_position_state(current_position, signal)
                    
            except Exception as e:
                logging.error(f"전략 {strategy.name} 실행 오류: {e}")
                
        return signals
```

## 🎛️ 조합 검증 규칙

### 1. 구조 검증
```python
class CombinationValidator:
    """전략 조합 검증기"""
    
    def validate_structure(self, combination: Dict) -> Tuple[bool, List[str]]:
        """조합 구조 검증"""
        errors = []
        
        # 필수 진입 전략 체크
        if not combination.get('entry_strategy'):
            errors.append("진입 전략이 필요합니다")
            
        # 관리 전략 개수 체크
        mgmt_strategies = combination.get('management_strategies', [])
        if len(mgmt_strategies) > 5:
            errors.append("관리 전략은 최대 5개까지 가능합니다")
            
        # 우선순위 중복 체크
        priorities = [s.get('priority', 0) for s in mgmt_strategies]
        if len(priorities) != len(set(priorities)):
            errors.append("관리 전략 우선순위가 중복됩니다")
            
        return len(errors) == 0, errors
```

### 2. 로직 검증
```python
    def validate_logic(self, combination: Dict) -> Tuple[bool, List[str]]:
        """조합 로직 검증"""
        warnings = []
        
        mgmt_strategies = combination.get('management_strategies', [])
        strategy_types = [s.get('type') for s in mgmt_strategies]
        
        # 상충 전략 체크
        if 'pyramid_buying' in strategy_types and 'scale_in_buying' in strategy_types:
            warnings.append("물타기와 불타기 전략이 동시에 있으면 상충할 수 있습니다")
            
        # 중복 기능 체크
        exit_strategies = {'fixed_exit', 'partial_closing', 'time_based_closing'}
        exit_count = len([s for s in strategy_types if s in exit_strategies])
        if exit_count > 2:
            warnings.append("너무 많은 청산 전략이 있어 혼란을 야기할 수 있습니다")
            
        return True, warnings  # 경고는 있어도 차단하지 않음
```

## 📊 조합 성과 측정

### 1. 개별 기여도 추적
```python
class CombinationPerformanceTracker:
    """조합 성과 추적기"""
    
    def track_strategy_contributions(self, trade_history: List[Trade]) -> Dict:
        """각 전략의 기여도 추적"""
        contributions = {}
        
        for trade in trade_history:
            # 진입 전략 기여도
            entry_contribution = trade.entry_profit
            entry_strategy = trade.entry_strategy_name
            
            if entry_strategy not in contributions:
                contributions[entry_strategy] = {
                    'profit': 0, 'trades': 0, 'type': 'entry'
                }
            contributions[entry_strategy]['profit'] += entry_contribution
            contributions[entry_strategy]['trades'] += 1
            
            # 관리 전략 기여도
            for mgmt_action in trade.management_actions:
                mgmt_strategy = mgmt_action['strategy_name']
                mgmt_profit = mgmt_action['profit_impact']
                
                if mgmt_strategy not in contributions:
                    contributions[mgmt_strategy] = {
                        'profit': 0, 'trades': 0, 'type': 'management'
                    }
                contributions[mgmt_strategy]['profit'] += mgmt_profit
                contributions[mgmt_strategy]['trades'] += 1
                
        return contributions
```

### 2. 조합 효율성 분석
```python
    def analyze_combination_efficiency(self, combination_results: Dict) -> Dict:
        """조합 효율성 분석"""
        total_profit = sum(c['profit'] for c in combination_results.values())
        total_trades = sum(c['trades'] for c in combination_results.values())
        
        analysis = {
            'total_profit': total_profit,
            'total_trades': total_trades,
            'average_profit_per_trade': total_profit / total_trades if total_trades > 0 else 0,
            'strategy_efficiency': {}
        }
        
        for strategy_name, result in combination_results.items():
            efficiency = result['profit'] / result['trades'] if result['trades'] > 0 else 0
            contribution_ratio = result['profit'] / total_profit if total_profit != 0 else 0
            
            analysis['strategy_efficiency'][strategy_name] = {
                'profit_per_trade': efficiency,
                'contribution_percentage': contribution_ratio * 100
            }
            
        return analysis
```

## 🧪 조합 테스트 케이스

### 1. 기본 조합 테스트
```python
def test_basic_combination():
    """기본 진입+관리 조합 테스트"""
    combination = {
        "entry_strategy": {"type": "rsi", "parameters": {"period": 14}},
        "management_strategies": [
            {"type": "trailing_stop", "priority": 1}
        ]
    }
    
    validator = CombinationValidator()
    is_valid, errors = validator.validate_structure(combination)
    assert is_valid, f"기본 조합이 유효하지 않음: {errors}"
```

### 2. 복잡한 조합 테스트
```python
def test_complex_combination():
    """복잡한 다중 관리 전략 조합 테스트"""
    combination = {
        "entry_strategy": {"type": "moving_average_crossover"},
        "management_strategies": [
            {"type": "pyramid_buying", "priority": 3},
            {"type": "trailing_stop", "priority": 2},
            {"type": "partial_closing", "priority": 1}
        ],
        "conflict_resolution": "conservative"
    }
    
    # 충돌 상황 시뮬레이션
    signals = [
        ("pyramid_buying", "ADD_BUY", 3),
        ("trailing_stop", "CLOSE_POSITION", 2),
        ("partial_closing", "PARTIAL_CLOSE", 1)
    ]
    
    resolver = ConservativeResolver()
    result = resolver.resolve(signals)
    assert result == "CLOSE_POSITION", "보수적 해결에서 청산이 우선되어야 함"
```

이 조합 규칙은 전략 시스템의 핵심 아키텍처를 정의하며, 복잡한 다중 전략 환경에서도 일관되고 예측 가능한 동작을 보장합니다.
