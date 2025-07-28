# 🛡️ 관리 전략 상세 명세

> **참조**: `.vscode/project-specs.md`의 전략 시스템 핵심 섹션

## 🎯 관리 전략 개요

**역할**: 활성 포지션의 리스크 관리 및 수익 극대화  
**활성화 조건**: `position_state == "position_management"`  
**출력 신호**: `ADD_BUY`, `ADD_SELL`, `CLOSE_POSITION`, `UPDATE_STOP`, `HOLD`  
**구현 목표**: 6개 관리 전략 완전 구현

## 1️⃣ 물타기 전략 (Pyramid Buying - Averaging Down)

### 전략 로직
```python
from dataclasses import dataclass
from typing import List

@dataclass
class PyramidBuyConfig:
    trigger_drop_rate: float = 0.05    # 추가 매수 트리거 하락률 (5%)
    max_additions: int = 5             # 최대 추가 매수 횟수
    addition_ratio: float = 1.0        # 추가 매수 수량 비율 (기본 수량 대비)
    absolute_stop_loss: float = 0.15   # 절대 손절선 (15%)

class PyramidBuyingStrategy(ManagementStrategy):
    """물타기 관리 전략"""
    
    def __init__(self, config: PyramidBuyConfig):
        self.config = config
        self.addition_count = 0
        self.total_cost = 0
        self.total_quantity = 0
        
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        """물타기 신호 생성"""
        current_price = data['close'].iloc[-1]
        
        # 절대 손절선 체크
        loss_rate = (position.entry_price - current_price) / position.entry_price
        if loss_rate >= self.config.absolute_stop_loss:
            return 'CLOSE_POSITION'
            
        # 추가 매수 조건 체크
        if (self.addition_count < self.config.max_additions and
            loss_rate >= self.config.trigger_drop_rate * (self.addition_count + 1)):
            
            self.addition_count += 1
            return 'ADD_BUY'
            
        return 'HOLD'
        
    def calculate_average_price(self, position: PositionState, add_price: float, add_quantity: float):
        """평균 단가 계산"""
        total_cost = (position.entry_price * position.quantity) + (add_price * add_quantity)
        total_quantity = position.quantity + add_quantity
        return total_cost / total_quantity
```

### UI 파라미터 설정
```python
def setup_pyramid_buying_ui(self):
    """물타기 전략 UI"""
    layout = QVBoxLayout()
    
    # 트리거 설정
    trigger_group = QGroupBox("추가 매수 조건")
    trigger_layout = QFormLayout(trigger_group)
    
    self.drop_rate_spin = QDoubleSpinBox()
    self.drop_rate_spin.setRange(0.01, 0.20)
    self.drop_rate_spin.setValue(0.05)
    self.drop_rate_spin.setSuffix(" %")
    trigger_layout.addRow("하락률 기준:", self.drop_rate_spin)
    
    self.max_additions_spin = QSpinBox()
    self.max_additions_spin.setRange(1, 5)
    self.max_additions_spin.setValue(3)
    trigger_layout.addRow("최대 횟수:", self.max_additions_spin)
    
    # 수량 설정
    quantity_group = QGroupBox("추가 매수 수량")
    quantity_layout = QFormLayout(quantity_group)
    
    self.addition_ratio_spin = QDoubleSpinBox()
    self.addition_ratio_spin.setRange(0.5, 2.0)
    self.addition_ratio_spin.setValue(1.0)
    quantity_layout.addRow("수량 비율:", self.addition_ratio_spin)
    
    # 손절 설정
    stop_group = QGroupBox("절대 손절선")
    stop_layout = QFormLayout(stop_group)
    
    self.stop_loss_spin = QDoubleSpinBox()
    self.stop_loss_spin.setRange(0.05, 0.30)
    self.stop_loss_spin.setValue(0.15)
    self.stop_loss_spin.setSuffix(" %")
    stop_layout.addRow("손절 기준:", self.stop_loss_spin)
    
    layout.addWidget(trigger_group)
    layout.addWidget(quantity_group)
    layout.addWidget(stop_group)
```

## 2️⃣ 불타기 전략 (Scale-in Buying - Momentum Adding)

### 전략 로직
```python
@dataclass
class ScaleInBuyConfig:
    trigger_rise_rate: float = 0.03   # 추가 매수 트리거 상승률 (3%)
    max_additions: int = 3            # 최대 추가 매수 횟수
    quantity_reduction: float = 0.7   # 수량 감소 비율 (피라미드)
    breakeven_protection: bool = True # 손익분기점 보호

class ScaleInBuyingStrategy(ManagementStrategy):
    """불타기 관리 전략"""
    
    def __init__(self, config: ScaleInBuyConfig):
        self.config = config
        self.addition_count = 0
        self.last_add_price = None
        
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        """불타기 신호 생성"""
        current_price = data['close'].iloc[-1]
        
        # 손익분기점 보호
        if (self.config.breakeven_protection and 
            current_price <= position.entry_price and 
            self.addition_count > 0):
            return 'CLOSE_POSITION'
            
        # 추가 매수 조건
        base_price = self.last_add_price or position.entry_price
        rise_rate = (current_price - base_price) / base_price
        
        if (self.addition_count < self.config.max_additions and
            rise_rate >= self.config.trigger_rise_rate):
            
            self.addition_count += 1
            self.last_add_price = current_price
            return 'ADD_BUY'
            
        return 'HOLD'
        
    def calculate_addition_quantity(self, base_quantity: float) -> float:
        """추가 매수 수량 계산 (피라미드 형태)"""
        reduction_factor = self.config.quantity_reduction ** self.addition_count
        return base_quantity * reduction_factor
```

## 3️⃣ 트레일링 스탑 전략 (Trailing Stop)

### 전략 로직
```python
@dataclass
class TrailingStopConfig:
    trail_distance: float = 0.05      # 추적 거리 (5%)
    activation_profit: float = 0.02   # 활성화 최소 수익률 (2%)
    stop_method: str = 'percentage'   # 'percentage' or 'atr'
    atr_period: int = 14             # ATR 기간 (ATR 방식 사용시)
    atr_multiplier: float = 2.0      # ATR 배수

class TrailingStopStrategy(ManagementStrategy):
    """트레일링 스탑 관리 전략"""
    
    def __init__(self, config: TrailingStopConfig):
        self.config = config
        self.highest_price = None
        self.stop_price = None
        self.is_activated = False
        
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        """트레일링 스탑 신호 생성"""
        current_price = data['close'].iloc[-1]
        
        # 최고가 갱신
        if self.highest_price is None or current_price > self.highest_price:
            self.highest_price = current_price
            
        # 트레일링 스탑 활성화 조건
        profit_rate = (current_price - position.entry_price) / position.entry_price
        if not self.is_activated and profit_rate >= self.config.activation_profit:
            self.is_activated = True
            
        # 트레일링 스탑 실행
        if self.is_activated:
            if self.config.stop_method == 'percentage':
                self.stop_price = self.highest_price * (1 - self.config.trail_distance)
            else:  # ATR 방식
                atr = self._calculate_atr(data)
                self.stop_price = self.highest_price - (atr * self.config.atr_multiplier)
                
            if current_price <= self.stop_price:
                return 'CLOSE_POSITION'
                
        return 'HOLD'
        
    def _calculate_atr(self, data: pd.DataFrame) -> float:
        """ATR(Average True Range) 계산"""
        if len(data) < self.config.atr_period:
            return 0
            
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(self.config.atr_period).mean()
        
        return atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0
```

## 4️⃣ 고정 익절/손절 전략 (Fixed Take Profit/Stop Loss)

### 전략 로직
```python
@dataclass
class FixedExitConfig:
    take_profit_rate: float = 0.10    # 익절 목표 (10%)
    stop_loss_rate: float = 0.05      # 손절 기준 (5%)
    use_partial_exit: bool = False    # 부분 익절 사용 여부
    partial_exit_rate: float = 0.50   # 부분 익절 시 청산 비율

class FixedTakeProfitStopLossStrategy(ManagementStrategy):
    """고정 익절/손절 관리 전략"""
    
    def __init__(self, config: FixedExitConfig):
        self.config = config
        self.partial_exit_executed = False
        
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        """고정 익절/손절 신호 생성"""
        current_price = data['close'].iloc[-1]
        
        # 수익률 계산
        if position.side == 'long':
            profit_rate = (current_price - position.entry_price) / position.entry_price
            loss_rate = (position.entry_price - current_price) / position.entry_price
        else:  # short
            profit_rate = (position.entry_price - current_price) / position.entry_price
            loss_rate = (current_price - position.entry_price) / position.entry_price
            
        # 손절 체크
        if loss_rate >= self.config.stop_loss_rate:
            return 'CLOSE_POSITION'
            
        # 익절 체크
        if profit_rate >= self.config.take_profit_rate:
            if self.config.use_partial_exit and not self.partial_exit_executed:
                self.partial_exit_executed = True
                return f'PARTIAL_CLOSE:{self.config.partial_exit_rate}'
            else:
                return 'CLOSE_POSITION'
                
        return 'HOLD'
```

## 5️⃣ 부분 청산 전략 (Partial Closing)

### 전략 로직
```python
@dataclass
class PartialClosingConfig:
    profit_levels: List[float]        # 익절 단계 [5%, 10%, 15%]
    closing_ratios: List[float]       # 청산 비율 [30%, 30%, 40%]
    trailing_after_partial: bool     # 부분 청산 후 트레일링 적용

class PartialClosingStrategy(ManagementStrategy):
    """부분 청산 관리 전략"""
    
    def __init__(self, config: PartialClosingConfig):
        self.config = config
        self.executed_levels = set()
        self.remaining_quantity_ratio = 1.0
        
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        """부분 청산 신호 생성"""
        current_price = data['close'].iloc[-1]
        profit_rate = (current_price - position.entry_price) / position.entry_price
        
        # 각 익절 단계 체크
        for i, (level, ratio) in enumerate(zip(self.config.profit_levels, self.config.closing_ratios)):
            if (i not in self.executed_levels and 
                profit_rate >= level):
                
                self.executed_levels.add(i)
                self.remaining_quantity_ratio -= ratio
                
                if self.remaining_quantity_ratio <= 0:
                    return 'CLOSE_POSITION'
                else:
                    return f'PARTIAL_CLOSE:{ratio}'
                    
        # 부분 청산 후 트레일링 스탑 적용
        if (self.config.trailing_after_partial and 
            len(self.executed_levels) > 0 and
            self.remaining_quantity_ratio > 0):
            
            # 간단한 트레일링 로직 (5% 하락 시 청산)
            if profit_rate < max(self.config.profit_levels) * 0.8:
                return 'CLOSE_POSITION'
                
        return 'HOLD'
```

## 6️⃣ 시간 기반 청산 전략 (Time-based Closing)

### 전략 로직
```python
@dataclass
class TimeBasedClosingConfig:
    max_holding_hours: int = 24       # 최대 보유 시간 (시간)
    force_close_on_loss: bool = True  # 손실시에도 강제 청산
    close_before_market_end: bool = True # 장 마감 전 청산
    market_close_buffer_hours: int = 1   # 장 마감 전 청산 여유시간

class TimeBasedClosingStrategy(ManagementStrategy):
    """시간 기반 청산 관리 전략"""
    
    def __init__(self, config: TimeBasedClosingConfig):
        self.config = config
        
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        """시간 기반 청산 신호 생성"""
        current_time = data.index[-1]
        holding_hours = (current_time - position.entry_time).total_seconds() / 3600
        
        # 최대 보유 시간 초과
        if holding_hours >= self.config.max_holding_hours:
            current_price = data['close'].iloc[-1]
            profit_rate = (current_price - position.entry_price) / position.entry_price
            
            if self.config.force_close_on_loss or profit_rate >= 0:
                return 'CLOSE_POSITION'
                
        # 장 마감 전 청산 (한국 시간 기준)
        if self.config.close_before_market_end:
            if self._is_near_market_close(current_time):
                return 'CLOSE_POSITION'
                
        return 'HOLD'
        
    def _is_near_market_close(self, current_time) -> bool:
        """장 마감 시간 근접 여부 체크"""
        # 암호화폐는 24시간이므로 특별한 마감시간 없음
        # 필요시 특정 시간대 설정 가능
        hour = current_time.hour
        
        # 예: 매일 특정 시간(예: 오전 6시)에 청산
        if hour == (6 - self.config.market_close_buffer_hours):
            return True
            
        return False
```

## 🔗 충돌 해결 시스템

### 다중 관리 전략 조율
```python
from enum import Enum

class ConflictResolutionMethod(Enum):
    PRIORITY = "priority"        # 우선순위 기반
    CONSERVATIVE = "conservative" # 보수적 처리
    MERGE = "merge"             # 신호 병합

class ManagementSignalResolver:
    """관리 전략 신호 충돌 해결"""
    
    def __init__(self, resolution_method: ConflictResolutionMethod):
        self.resolution_method = resolution_method
        
    def resolve_signals(self, signals: List[Tuple[str, str, int]]) -> str:
        """
        신호 충돌 해결
        signals: [(strategy_name, signal, priority), ...]
        """
        if not signals:
            return 'HOLD'
            
        if len(signals) == 1:
            return signals[0][1]
            
        if self.resolution_method == ConflictResolutionMethod.PRIORITY:
            return self._resolve_by_priority(signals)
        elif self.resolution_method == ConflictResolutionMethod.CONSERVATIVE:
            return self._resolve_conservative(signals)
        else:  # MERGE
            return self._resolve_by_merge(signals)
            
    def _resolve_by_priority(self, signals: List[Tuple[str, str, int]]) -> str:
        """우선순위 기반 해결"""
        sorted_signals = sorted(signals, key=lambda x: x[2], reverse=True)
        return sorted_signals[0][1]
        
    def _resolve_conservative(self, signals: List[Tuple[str, str, int]]) -> str:
        """보수적 해결 (CLOSE_POSITION > HOLD > 기타)"""
        signal_priority = {
            'CLOSE_POSITION': 3,
            'HOLD': 2,
            'ADD_BUY': 1,
            'ADD_SELL': 1,
            'UPDATE_STOP': 1
        }
        
        sorted_signals = sorted(signals, key=lambda x: signal_priority.get(x[1], 0), reverse=True)
        return sorted_signals[0][1]
        
    def _resolve_by_merge(self, signals: List[Tuple[str, str, int]]) -> str:
        """신호 병합 해결"""
        # 단순 구현: ADD_BUY 신호들의 수량 합산 등
        add_buy_count = sum(1 for _, signal, _ in signals if signal == 'ADD_BUY')
        close_count = sum(1 for _, signal, _ in signals if signal == 'CLOSE_POSITION')
        
        if close_count > 0:
            return 'CLOSE_POSITION'
        elif add_buy_count > 1:
            return f'ADD_BUY:{add_buy_count}'  # 배수 매수
        else:
            return signals[0][1]
```

## 🎨 관리 전략 탭 UI 구현

### 전략 설정 및 조합 인터페이스
```python
class ManagementStrategyTab(QWidget):
    """관리 전략 탭"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.strategies = {
            'pyramid_buying': PyramidBuyingStrategy,
            'scale_in_buying': ScaleInBuyingStrategy, 
            'trailing_stop': TrailingStopStrategy,
            'fixed_exit': FixedTakeProfitStopLossStrategy,
            'partial_closing': PartialClosingStrategy,
            'time_based_closing': TimeBasedClosingStrategy
        }
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        
        # 상단: 전략 선택 체크박스들
        selection_group = QGroupBox("관리 전략 선택 (다중 선택 가능)")
        selection_layout = QGridLayout(selection_group)
        
        self.strategy_checkboxes = {}
        strategy_items = [
            ("pyramid_buying", "🔻 물타기", "하락 시 평균단가 낮추기"),
            ("scale_in_buying", "🔺 불타기", "상승 시 수익 극대화"),
            ("trailing_stop", "🏃 트레일링 스탑", "수익 보호 추적 손절"),
            ("fixed_exit", "⚖️ 고정 익절/손절", "명확한 목표 수익/손실"),
            ("partial_closing", "📊 부분 청산", "단계별 수익 실현"),
            ("time_based_closing", "⏰ 시간 청산", "보유시간 제한 관리")
        ]
        
        for i, (key, name, desc) in enumerate(strategy_items):
            checkbox = QCheckBox(name)
            checkbox.setToolTip(desc)
            self.strategy_checkboxes[key] = checkbox
            
            row, col = i // 2, i % 2
            selection_layout.addWidget(checkbox, row, col)
            
        # 하단: 선택된 전략별 파라미터 설정
        self.parameter_tabs = QTabWidget()
        
        # 충돌 해결 설정
        conflict_group = QGroupBox("충돌 해결 방식")
        conflict_layout = QHBoxLayout(conflict_group)
        
        self.conflict_combo = StyledComboBox()
        self.conflict_combo.addItems([
            "우선순위 기반",
            "보수적 처리", 
            "신호 병합"
        ])
        conflict_layout.addWidget(QLabel("해결 방식:"))
        conflict_layout.addWidget(self.conflict_combo)
        
        layout.addWidget(selection_group)
        layout.addWidget(conflict_group)
        layout.addWidget(self.parameter_tabs)
        
        # 시그널 연결
        for checkbox in self.strategy_checkboxes.values():
            checkbox.toggled.connect(self.on_strategy_toggled)
```

## 📊 성능 추적 및 분석

### 관리 전략 기여도 측정
```python
class ManagementStrategyAnalyzer:
    """관리 전략 성과 분석"""
    
    def analyze_contribution(self, trades: List[Trade], strategies: List[ManagementStrategy]):
        """각 관리 전략의 기여도 분석"""
        results = {}
        
        for strategy in strategies:
            contribution = self._calculate_strategy_contribution(trades, strategy)
            results[strategy.__class__.__name__] = contribution
            
        return results
        
    def _calculate_strategy_contribution(self, trades: List[Trade], strategy: ManagementStrategy):
        """개별 전략 기여도 계산"""
        strategy_trades = [t for t in trades if strategy.__class__.__name__ in t.strategy_tags]
        
        if not strategy_trades:
            return {
                'profit_contribution': 0,
                'trades_affected': 0,
                'average_impact': 0
            }
            
        total_profit_impact = sum(t.profit_from_management for t in strategy_trades)
        
        return {
            'profit_contribution': total_profit_impact,
            'trades_affected': len(strategy_trades),
            'average_impact': total_profit_impact / len(strategy_trades),
            'success_rate': len([t for t in strategy_trades if t.profit_from_management > 0]) / len(strategy_trades)
        }
```

## 🧪 테스트 케이스

### 관리 전략 단위 테스트
```python
class TestManagementStrategies(unittest.TestCase):
    
    def setUp(self):
        """테스트 포지션 및 데이터 설정"""
        self.test_position = PositionState(
            entry_price=100.0,
            current_price=100.0,
            quantity=1.0,
            side='long',
            entry_time=datetime.now(),
            management_history=[]
        )
        
        # 가격 하락 시나리오 데이터
        self.declining_data = pd.DataFrame({
            'close': [100, 98, 95, 92, 90, 85],
            'high': [101, 99, 96, 93, 91, 86],
            'low': [99, 97, 94, 91, 89, 84]
        })
        
    def test_pyramid_buying_strategy(self):
        """물타기 전략 테스트"""
        config = PyramidBuyConfig(trigger_drop_rate=0.05, max_additions=3)
        strategy = PyramidBuyingStrategy(config)
        
        # 5% 하락 시 ADD_BUY 신호
        self.test_position.current_price = 95.0
        signal = strategy.generate_signal(self.test_position, self.declining_data[2:3])
        self.assertEqual(signal, 'ADD_BUY')
        
        # 절대 손절선 도달 시 CLOSE_POSITION
        config_stop = PyramidBuyConfig(absolute_stop_loss=0.10)
        strategy_stop = PyramidBuyingStrategy(config_stop)
        self.test_position.current_price = 85.0
        signal = strategy_stop.generate_signal(self.test_position, self.declining_data[-1:])
        self.assertEqual(signal, 'CLOSE_POSITION')
        
    def test_trailing_stop_strategy(self):
        """트레일링 스탑 전략 테스트"""
        config = TrailingStopConfig(trail_distance=0.05, activation_profit=0.02)
        strategy = TrailingStopStrategy(config)
        
        # 수익 실현 전에는 HOLD
        self.test_position.current_price = 101.0
        rising_data = pd.DataFrame({'close': [101], 'high': [102], 'low': [100]})
        signal = strategy.generate_signal(self.test_position, rising_data)
        self.assertEqual(signal, 'HOLD')
        
        # 트레일링 스탑 활성화 후 하락 시 CLOSE_POSITION
        self.test_position.current_price = 105.0
        strategy.highest_price = 105.0
        strategy.is_activated = True
        
        self.test_position.current_price = 98.0  # 5% 이상 하락
        declining_data = pd.DataFrame({'close': [98], 'high': [99], 'low': [97]})
        signal = strategy.generate_signal(self.test_position, declining_data)
        self.assertEqual(signal, 'CLOSE_POSITION')
```

이 관리 전략 명세는 포지션 관리의 핵심 기능들을 완전히 구현하며, 리스크 관리와 수익 극대화를 위한 체계적인 접근법을 제공합니다.
