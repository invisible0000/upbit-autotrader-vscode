# 전략 실행 엔진 아키텍처 (Strategy Execution Engine Architecture)

## 📋 개요

전략이 실제로 **백테스트**와 **실전 매매**에서 실행되는 완전한 생명 주기와 상태 관리 체계를 정의합니다. 단일 전략부터 복합 조합 전략까지 모든 실행 플로우를 통합 관리합니다.

---

## 🔄 **전략 실행 생명 주기 (Strategy Execution Lifecycle)**

### **🎯 기본 실행 플로우**

```
1. 대기 상태 (WAITING)
   ├── 포지션 없음 (No Position)
   ├── 시장 데이터 수신 및 분석
   └── 진입 조건 감시
   
2. 진입 단계 (ENTRY_PHASE)
   ├── 진입 신호 발생 (Entry Signal Generated)
   ├── 매수 시도 (Buy Attempt)
   ├── 매수 성공 확인 (Buy Confirmation)
   └── 포지션 생성 (Position Created)
   
3. 관리 단계 (MANAGEMENT_PHASE)
   ├── 포지션 보유 중 (Position Holding)
   ├── 시가 감시 (Price Monitoring)
   ├── 진입가 대비 비율 계산 (P&L Tracking)
   ├── 특정 지표 추적 (Indicator Monitoring)
   └── 관리 조건 평가 (Management Conditions)
   
4. 청산 단계 (EXIT_PHASE)
   ├── 청산 신호 발생 (Exit Signal Generated)
   ├── 매도 시도 (Sell Attempt)
   ├── 매도 성공 확인 (Sell Confirmation)
   └── 포지션 종료 (Position Closed)
   
5. 완료 상태 (COMPLETED)
   ├── 수익/손실 확정 (P&L Finalized)
   ├── 성과 기록 (Performance Logging)
   └── 대기 상태로 복귀 (Return to WAITING)
```

---

## 🎭 **전략 상태 관리 시스템 (Strategy State Management)**

### **📊 상태 열거형 정의**

```python
from enum import Enum

class StrategyState(Enum):
    """전략 실행 상태"""
    WAITING = "WAITING"                    # 대기 중 (포지션 없음)
    ENTRY_SIGNAL = "ENTRY_SIGNAL"          # 진입 신호 발생
    ENTRY_PENDING = "ENTRY_PENDING"        # 매수 주문 대기
    POSITION_ACTIVE = "POSITION_ACTIVE"    # 포지션 보유 중
    EXIT_SIGNAL = "EXIT_SIGNAL"           # 청산 신호 발생
    EXIT_PENDING = "EXIT_PENDING"         # 매도 주문 대기
    COMPLETED = "COMPLETED"               # 완료 (수익/손실 확정)
    ERROR = "ERROR"                       # 오류 상태
    PAUSED = "PAUSED"                     # 일시 정지

class PositionType(Enum):
    """포지션 타입"""
    NONE = "NONE"          # 포지션 없음
    LONG = "LONG"          # 매수 포지션
    SHORT = "SHORT"        # 매도 포지션 (선물용)

class SignalType(Enum):
    """신호 타입 (확장된 버전)"""
    # 진입 신호
    BUY = "BUY"                    # 매수 신호
    SELL = "SELL"                  # 매도 신호
    BUY_SELL = "BUY_SELL"          # 양방향 신호
    
    # 관리 신호
    ADD_BUY = "ADD_BUY"            # 추가 매수 (피라미딩)
    PARTIAL_EXIT = "PARTIAL_EXIT"   # 부분 청산
    STOP_LOSS = "STOP_LOSS"        # 손절
    TAKE_PROFIT = "TAKE_PROFIT"    # 익절
    TRAILING = "TRAILING"          # 트레일링 스탑
    TIME_EXIT = "TIME_EXIT"        # 시간 기반 청산
    VOLATILITY = "VOLATILITY"      # 변동성 기반 관리
    
    # 필터 신호
    VOLUME_FILTER = "VOLUME_FILTER"
    VOLATILITY_FILTER = "VOLATILITY_FILTER"
```

### **🏗️ 전략 실행 컨텍스트 (Strategy Execution Context)**

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

@dataclass
class Position:
    """포지션 정보"""
    symbol: str
    position_type: PositionType
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    
    # 피라미딩 관련
    add_buy_count: int = 0
    average_price: float = 0.0
    total_invested: float = 0.0

@dataclass
class StrategyExecutionContext:
    """전략 실행 컨텍스트"""
    # 기본 정보
    strategy_id: str
    strategy_name: str
    symbol: str
    timeframe: str
    
    # 상태 정보
    current_state: StrategyState
    position: Optional[Position]
    
    # 실행 기록
    entry_signals: List[Dict[str, Any]]
    exit_signals: List[Dict[str, Any]]
    trade_history: List[Dict[str, Any]]
    
    # 성과 정보
    total_trades: int = 0
    winning_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    
    # 설정
    max_position_size: float = 1000000  # 최대 포지션 크기
    risk_per_trade: float = 0.02        # 거래당 리스크 (2%)
    
    def update_state(self, new_state: StrategyState, reason: str = ""):
        """상태 업데이트"""
        self.current_state = new_state
        # 로깅 로직 추가
        
    def has_position(self) -> bool:
        """포지션 보유 여부"""
        return self.position is not None and self.position.position_type != PositionType.NONE
    
    def can_enter(self) -> bool:
        """진입 가능 여부"""
        return self.current_state == StrategyState.WAITING and not self.has_position()
    
    def can_exit(self) -> bool:
        """청산 가능 여부"""
        return self.current_state == StrategyState.POSITION_ACTIVE and self.has_position()
```

---

## 🎪 **조합 전략 실행 엔진 (Combination Strategy Execution Engine)**

### **🔧 조합 전략 조정자 (Combination Coordinator)**

```python
class CombinationStrategyExecutor:
    """조합 전략 실행 엔진"""
    
    def __init__(self, combination_config: Dict[str, Any]):
        self.combination_id = combination_config["combination_id"]
        self.combination_name = combination_config["combination_name"]
        
        # 전략 그룹별 분류
        self.entry_strategies = self._load_strategies(combination_config["entry_strategies"])
        self.management_strategies = self._load_strategies(combination_config["management_strategies"])
        self.exit_strategies = self._load_strategies(combination_config["exit_strategies"])
        self.filter_strategies = self._load_strategies(combination_config.get("filter_strategies", []))
        
        # 실행 컨텍스트
        self.context = StrategyExecutionContext(
            strategy_id=self.combination_id,
            strategy_name=self.combination_name,
            symbol=combination_config["symbol"],
            timeframe=combination_config["timeframe"],
            current_state=StrategyState.WAITING,
            position=None,
            entry_signals=[],
            exit_signals=[],
            trade_history=[]
        )
        
    def execute_cycle(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """전략 실행 사이클"""
        execution_result = {
            "timestamp": market_data["timestamp"],
            "state": self.context.current_state.value,
            "signals": [],
            "actions": [],
            "position": self.context.position
        }
        
        try:
            if self.context.current_state == StrategyState.WAITING:
                # 진입 신호 평가
                entry_result = self._evaluate_entry_signals(market_data)
                if entry_result["should_enter"]:
                    self._execute_entry(entry_result)
                    execution_result["actions"].append("ENTRY_EXECUTED")
                    
            elif self.context.current_state == StrategyState.POSITION_ACTIVE:
                # 관리 신호 평가
                management_result = self._evaluate_management_signals(market_data)
                if management_result["actions"]:
                    self._execute_management_actions(management_result)
                    execution_result["actions"].extend(management_result["actions"])
                
                # 청산 신호 평가
                exit_result = self._evaluate_exit_signals(market_data)
                if exit_result["should_exit"]:
                    self._execute_exit(exit_result)
                    execution_result["actions"].append("EXIT_EXECUTED")
                    
        except Exception as e:
            self.context.update_state(StrategyState.ERROR, f"Execution error: {str(e)}")
            execution_result["error"] = str(e)
            
        return execution_result
    
    def _evaluate_entry_signals(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """진입 신호 평가"""
        entry_result = {
            "should_enter": False,
            "signals": [],
            "confidence": 0.0,
            "entry_price": market_data["close"],
            "position_size": 0.0
        }
        
        # 1단계: 필터 전략 적용
        if not self._check_filters(market_data):
            return entry_result
        
        # 2단계: 진입 전략들 평가
        primary_signals = []
        confirmation_signals = []
        
        for strategy in self.entry_strategies:
            signal = strategy.generate_signal(market_data)
            if signal:
                if strategy.trigger_mode == "PRIMARY":
                    primary_signals.append(signal)
                elif strategy.trigger_mode == "CONFIRMATION":
                    confirmation_signals.append(signal)
        
        # 3단계: 진입 조건 조합 로직
        if primary_signals:
            # 주 전략 신호가 있으면 확인 전략 검토
            total_confidence = sum(s.confidence * s.weight for s in primary_signals)
            
            if confirmation_signals:
                # 확인 전략도 만족하면 신뢰도 증가
                confirmation_boost = sum(s.confidence * s.weight for s in confirmation_signals) * 0.3
                total_confidence += confirmation_boost
            
            # 최종 진입 결정
            if total_confidence >= 0.6:  # 60% 이상 신뢰도
                entry_result["should_enter"] = True
                entry_result["confidence"] = min(total_confidence, 1.0)
                entry_result["signals"] = primary_signals + confirmation_signals
                entry_result["position_size"] = self._calculate_position_size(market_data, total_confidence)
        
        return entry_result
    
    def _evaluate_management_signals(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """관리 신호 평가 (피라미딩, 부분 청산 등)"""
        management_result = {
            "actions": [],
            "signals": []
        }
        
        for strategy in self.management_strategies:
            signal = strategy.generate_signal(market_data, self.context.position)
            if signal:
                if signal.signal_type == SignalType.ADD_BUY:
                    # 피라미딩 로직
                    if self._can_add_position():
                        management_result["actions"].append({
                            "action": "ADD_BUY",
                            "amount": signal.additional_data.get("add_amount", 100000),
                            "reason": signal.reason
                        })
                
                elif signal.signal_type == SignalType.PARTIAL_EXIT:
                    # 부분 청산 로직
                    management_result["actions"].append({
                        "action": "PARTIAL_EXIT",
                        "ratio": signal.additional_data.get("exit_ratio", 0.3),
                        "reason": signal.reason
                    })
                
                management_result["signals"].append(signal)
        
        return management_result
    
    def _evaluate_exit_signals(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """청산 신호 평가"""
        exit_result = {
            "should_exit": False,
            "signals": [],
            "exit_type": None,
            "urgency": "NORMAL"
        }
        
        for strategy in self.exit_strategies:
            signal = strategy.generate_signal(market_data, self.context.position)
            if signal:
                exit_result["signals"].append(signal)
                
                # 긴급 청산 신호 (손절 등)
                if signal.signal_type in [SignalType.STOP_LOSS]:
                    exit_result["should_exit"] = True
                    exit_result["exit_type"] = "STOP_LOSS"
                    exit_result["urgency"] = "URGENT"
                    break
                
                # 일반 청산 신호
                elif signal.confidence >= 0.7:
                    exit_result["should_exit"] = True
                    exit_result["exit_type"] = signal.signal_type.value
        
        return exit_result
```

---

## 📊 **백테스트 실행 플로우 (Backtest Execution Flow)**

### **🔄 백테스트 엔진 통합**

```python
class BacktestExecutionEngine:
    """백테스트 실행 엔진"""
    
    def __init__(self, strategy_config: Dict[str, Any], backtest_config: Dict[str, Any]):
        self.strategy_executor = CombinationStrategyExecutor(strategy_config)
        self.backtest_config = backtest_config
        self.market_data_loader = MarketDataLoader()
        self.execution_log = []
        
    def run_backtest(self) -> Dict[str, Any]:
        """백테스트 실행"""
        print(f"🚀 백테스트 시작: {self.strategy_executor.combination_name}")
        
        # 시장 데이터 로드
        market_data = self.market_data_loader.load_data(
            symbol=self.backtest_config["symbol"],
            start_date=self.backtest_config["start_date"],
            end_date=self.backtest_config["end_date"],
            timeframe=self.backtest_config["timeframe"]
        )
        
        # 시뮬레이션 실행
        for i, data_point in enumerate(market_data):
            # 전략 실행 사이클
            execution_result = self.strategy_executor.execute_cycle(data_point)
            self.execution_log.append(execution_result)
            
            # 진행 상황 출력
            if i % 1000 == 0:
                progress = (i / len(market_data)) * 100
                current_state = self.strategy_executor.context.current_state.value
                print(f"📊 진행률: {progress:.1f}% | 상태: {current_state}")
        
        # 결과 분석
        performance_metrics = self._calculate_performance_metrics()
        
        print(f"✅ 백테스트 완료!")
        print(f"📈 총 거래: {performance_metrics['total_trades']}회")
        print(f"💰 최종 수익률: {performance_metrics['total_return']:.2f}%")
        print(f"📉 최대 낙폭: {performance_metrics['max_drawdown']:.2f}%")
        
        return {
            "execution_log": self.execution_log,
            "performance_metrics": performance_metrics,
            "strategy_config": self.strategy_executor.combination_id
        }
```

---

## 🔧 **실전 매매 실행 플로우 (Live Trading Execution Flow)**

### **⚡ 실시간 실행 엔진**

```python
class LiveTradingEngine:
    """실시간 매매 실행 엔진"""
    
    def __init__(self, strategy_config: Dict[str, Any], api_credentials: Dict[str, Any]):
        self.strategy_executor = CombinationStrategyExecutor(strategy_config)
        self.upbit_api = UpbitAPI(api_credentials)
        self.is_running = False
        
    async def start_trading(self):
        """실시간 매매 시작"""
        print(f"🔴 실전 매매 시작: {self.strategy_executor.combination_name}")
        self.is_running = True
        
        while self.is_running:
            try:
                # 실시간 시장 데이터 수신
                market_data = await self.upbit_api.get_current_market_data(
                    symbol=self.strategy_executor.context.symbol
                )
                
                # 전략 실행
                execution_result = self.strategy_executor.execute_cycle(market_data)
                
                # 실제 주문 실행
                if execution_result["actions"]:
                    await self._execute_real_orders(execution_result["actions"])
                
                # 상태 모니터링
                await self._monitor_and_log(execution_result)
                
                # 다음 사이클까지 대기
                await asyncio.sleep(self._get_cycle_interval())
                
            except Exception as e:
                print(f"❌ 실행 오류: {str(e)}")
                await self._handle_execution_error(e)
    
    async def _execute_real_orders(self, actions: List[Dict[str, Any]]):
        """실제 주문 실행"""
        for action in actions:
            if action["action"] == "ENTRY_EXECUTED":
                # 매수 주문
                order_result = await self.upbit_api.place_buy_order(
                    symbol=self.strategy_executor.context.symbol,
                    amount=action["amount"]
                )
                print(f"💰 매수 주문 실행: {order_result}")
                
            elif action["action"] == "EXIT_EXECUTED":
                # 매도 주문
                order_result = await self.upbit_api.place_sell_order(
                    symbol=self.strategy_executor.context.symbol,
                    quantity=action["quantity"]
                )
                print(f"💸 매도 주문 실행: {order_result}")
```

---

## 📚 **문서 업데이트 체크리스트**

### **✅ 반영 완료된 내용**
1. ✅ 전략 역할 분류 (ENTRY, SCALE_IN, SCALE_OUT, EXIT, MANAGEMENT, FILTER)
2. ✅ 신호 타입 확장 (ADD_BUY, PARTIAL_EXIT 등)
3. ✅ 완전한 실행 생명 주기 정의
4. ✅ 조합 전략 실행 로직 명세

### **🔄 업데이트 예정 문서들**
1. **STRATEGY_ARCHITECTURE_OVERVIEW.md** → 실행 엔진 아키텍처 추가
2. **STRATEGY_COMBINATION_GUIDE.md** → 실제 조합 실행 로직 추가
3. **BUILT_IN_STRATEGY_LIBRARY.md** → 새로운 역할/신호 타입 반영 ✅
4. **백테스트 엔진 문서** → 새로운 실행 플로우 반영

---

## 🎯 **핵심 답변 요약**

### **📋 조합 전략 진입 조건 처리**
- **PRIMARY 전략**: 독립적으로 신호 생성
- **CONFIRMATION 전략**: PRIMARY 신호를 검증/강화
- **가중 평균**: 각 전략의 신뢰도와 가중치를 조합하여 최종 결정

### **🛡️ 조합 전략 매도 조건 처리**
- **병렬 평가**: 모든 EXIT/MANAGEMENT 전략을 동시 감시
- **우선순위**: STOP_LOSS > TRAILING > TAKE_PROFIT 순으로 처리
- **즉시 실행**: 긴급 신호(손절)는 다른 조건 무시하고 즉시 실행

### **⚡ 개별 감시 vs 조합 감시**
- **통합 감시**: 하나의 실행 엔진이 모든 전략을 조율
- **상태 기반**: 현재 포지션 상태에 따라 적절한 전략 그룹만 활성화
- **효율성**: 중복 계산 방지 및 일관된 의사결정

이제 완전한 실행 아키텍처가 문서화되었습니다! 🚀
