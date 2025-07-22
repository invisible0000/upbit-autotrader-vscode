"""
종합 전략 엔진 - GUI 없는 실전 버전
Comprehensive Strategy Engine - Production Version without GUI

7가지 핵심 전략을 모두 조합하여 실제 백테스팅과 실행이 가능한 시스템
"""

import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import time

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TriggerType(Enum):
    """트리거 타입"""
    RSI = "rsi"
    PRICE_CHANGE = "price_change"
    PROFIT_RATE = "profit_rate" 
    TRAILING_STOP = "trailing_stop"
    RAPID_CHANGE = "rapid_change"
    TIME_RANGE = "time_range"
    VOLUME = "volume"
    MACD = "macd"
    BOLLINGER = "bollinger"
    MOVING_AVERAGE = "moving_average"

class ActionType(Enum):
    """액션 타입"""
    BUY = "buy"
    SELL = "sell"
    PARTIAL_SELL = "partial_sell"

class TriggerRelation(Enum):
    """트리거 관계"""
    AND = "and"
    OR = "or"
    SEQUENCE = "sequence"

@dataclass
class TriggerConfig:
    """트리거 설정"""
    trigger_type: TriggerType
    params: Dict[str, Any]
    description: str

@dataclass
class RuleConfig:
    """규칙 설정"""
    rule_id: str
    name: str
    activation_state: str  # READY, ACTIVE
    priority: int
    triggers: List[TriggerConfig]
    trigger_relation: TriggerRelation
    action_type: ActionType
    action_params: Dict[str, Any]
    conditions: List[Dict[str, Any]]
    
@dataclass
class StrategyConfig:
    """전략 설정"""
    strategy_id: str
    name: str
    description: str
    rules: List[RuleConfig]
    
@dataclass
class MarketData:
    """시장 데이터"""
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    
@dataclass
class Position:
    """포지션 정보"""
    symbol: str
    entry_price: float
    quantity: float
    entry_time: datetime
    current_price: float
    unrealized_pnl: float
    highest_price: float  # 트레일링 스탑용

@dataclass
class TradeResult:
    """거래 결과"""
    timestamp: datetime
    action: str
    price: float
    quantity: float
    pnl: float
    balance: float
    rule_id: str
    trigger_description: str

class TechnicalIndicators:
    """기술적 지표 계산"""
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> float:
        """RSI 계산"""
        if len(prices) < period + 1:
            return 50.0
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """MACD 계산"""
        if len(prices) < slow:
            return 0.0, 0.0, 0.0
            
        # EMA 계산
        def ema(data, period):
            multiplier = 2 / (period + 1)
            ema_values = [data[0]]
            for price in data[1:]:
                ema_values.append((price * multiplier) + (ema_values[-1] * (1 - multiplier)))
            return ema_values[-1]
        
        fast_ema = ema(prices, fast)
        slow_ema = ema(prices, slow)
        macd_line = fast_ema - slow_ema
        
        # 시그널 라인은 단순화 (실제로는 MACD의 EMA)
        signal_line = macd_line * 0.8  # 근사값
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
        """볼린저 밴드 계산"""
        if len(prices) < period:
            avg = sum(prices) / len(prices)
            return avg, avg * 0.95, avg * 1.05
            
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / period
        variance = sum((price - sma) ** 2 for price in recent_prices) / period
        std = variance ** 0.5
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return sma, upper_band, lower_band
    
    @staticmethod
    def moving_average(prices: List[float], period: int) -> float:
        """이동평균 계산"""
        if len(prices) < period:
            return sum(prices) / len(prices)
        return sum(prices[-period:]) / period

class TriggerEvaluator:
    """트리거 평가기"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def evaluate_trigger(self, trigger: TriggerConfig, market_data: List[MarketData], 
                        position: Optional[Position], current_time: datetime) -> bool:
        """트리거 평가"""
        
        if not market_data:
            return False
            
        current_price = market_data[-1].close_price
        prices = [data.close_price for data in market_data]
        
        try:
            if trigger.trigger_type == TriggerType.RSI:
                rsi = self.indicators.rsi(prices, trigger.params.get('period', 14))
                threshold = trigger.params.get('threshold', 30)
                condition = trigger.params.get('condition', '<=')
                
                if condition == '<=':
                    return rsi <= threshold
                elif condition == '>=':
                    return rsi >= threshold
                elif condition == '<':
                    return rsi < threshold
                elif condition == '>':
                    return rsi > threshold
                    
            elif trigger.trigger_type == TriggerType.PRICE_CHANGE:
                if len(prices) < 2:
                    return False
                    
                base_price = prices[-2]  # 전 가격 기준
                change_percent = ((current_price - base_price) / base_price) * 100
                target_change = trigger.params.get('change_percent', 5.0)
                condition = trigger.params.get('condition', '>=')
                
                if condition == '>=':
                    return change_percent >= target_change
                elif condition == '<=':
                    return change_percent <= target_change
                    
            elif trigger.trigger_type == TriggerType.PROFIT_RATE:
                if not position:
                    return False
                    
                profit_rate = ((current_price - position.entry_price) / position.entry_price) * 100
                target_rate = trigger.params.get('rate', 5.0)
                condition = trigger.params.get('condition', '>=')
                
                if condition == '>=':
                    return profit_rate >= target_rate
                elif condition == '<=':
                    return profit_rate <= target_rate
                    
            elif trigger.trigger_type == TriggerType.TRAILING_STOP:
                if not position:
                    return False
                    
                trail_percent = trigger.params.get('trail_percent', 3.0)
                # 최고가 대비 하락률 계산
                drop_percent = ((position.highest_price - current_price) / position.highest_price) * 100
                return drop_percent >= trail_percent
                
            elif trigger.trigger_type == TriggerType.RAPID_CHANGE:
                time_window = trigger.params.get('time_window', 5)
                change_threshold = trigger.params.get('change_percent', -10.0)
                
                if len(prices) < time_window:
                    return False
                    
                old_price = prices[-time_window]
                change_percent = ((current_price - old_price) / old_price) * 100
                return change_percent <= change_threshold
                
            elif trigger.trigger_type == TriggerType.TIME_RANGE:
                start_time = trigger.params.get('start_time', '09:30')
                end_time = trigger.params.get('end_time', '15:00')
                
                current_time_str = current_time.strftime('%H:%M')
                return start_time <= current_time_str <= end_time
                
            elif trigger.trigger_type == TriggerType.VOLUME:
                if len(market_data) < 2:
                    return False
                    
                current_volume = market_data[-1].volume
                avg_volume = sum([data.volume for data in market_data[-20:]]) / min(20, len(market_data))
                multiplier = trigger.params.get('multiplier', 2.0)
                
                return current_volume >= avg_volume * multiplier
                
            elif trigger.trigger_type == TriggerType.MACD:
                macd_line, signal_line, histogram = self.indicators.macd(prices)
                signal_type = trigger.params.get('signal_type', 'golden_cross')
                
                if signal_type == 'golden_cross':
                    return macd_line > signal_line and histogram > 0
                elif signal_type == 'dead_cross':
                    return macd_line < signal_line and histogram < 0
                elif signal_type == 'histogram_positive':
                    return histogram > 0
                elif signal_type == 'histogram_negative':
                    return histogram < 0
                    
        except Exception as e:
            logger.warning(f"트리거 평가 오류: {e}")
            return False
            
        return False
    
    def evaluate_multiple_triggers(self, triggers: List[TriggerConfig], relation: TriggerRelation,
                                 market_data: List[MarketData], position: Optional[Position], 
                                 current_time: datetime) -> bool:
        """다중 트리거 평가"""
        
        if not triggers:
            return False
            
        results = []
        for trigger in triggers:
            result = self.evaluate_trigger(trigger, market_data, position, current_time)
            results.append(result)
            logger.debug(f"트리거 {trigger.description}: {result}")
        
        if relation == TriggerRelation.AND:
            return all(results)
        elif relation == TriggerRelation.OR:
            return any(results)
        elif relation == TriggerRelation.SEQUENCE:
            # 순차적 만족 (간단히 AND로 처리)
            return all(results)
            
        return False

class StrategyEngine:
    """전략 실행 엔진"""
    
    def __init__(self, initial_balance: float = 1000000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position: Optional[Position] = None
        self.trade_history: List[TradeResult] = []
        self.trigger_evaluator = TriggerEvaluator()
        self.execution_counts = {}  # 규칙별 실행 횟수
        
    def execute_strategy(self, strategy: StrategyConfig, market_data: List[MarketData]) -> List[TradeResult]:
        """전략 실행"""
        logger.info(f"전략 실행 시작: {strategy.name}")
        
        for i, data in enumerate(market_data):
            current_time = data.timestamp
            current_data = market_data[:i+1]  # 현재까지의 데이터
            
            # 포지션 업데이트
            if self.position:
                self.position.current_price = data.close_price
                self.position.unrealized_pnl = (data.close_price - self.position.entry_price) * self.position.quantity
                # 최고가 업데이트 (트레일링 스탑용)
                if data.close_price > self.position.highest_price:
                    self.position.highest_price = data.close_price
            
            # 규칙별로 평가 및 실행
            active_rules = self._get_active_rules(strategy.rules)
            
            for rule in sorted(active_rules, key=lambda r: r.priority):
                if self._should_execute_rule(rule, current_data, current_time):
                    self._execute_rule(rule, data, current_time)
        
        logger.info(f"전략 실행 완료. 총 거래: {len(self.trade_history)}")
        return self.trade_history
    
    def _get_active_rules(self, rules: List[RuleConfig]) -> List[RuleConfig]:
        """현재 활성화된 규칙들 반환"""
        if self.position is None:
            return [rule for rule in rules if rule.activation_state == "READY"]
        else:
            return [rule for rule in rules if rule.activation_state == "ACTIVE"]
    
    def _should_execute_rule(self, rule: RuleConfig, market_data: List[MarketData], 
                           current_time: datetime) -> bool:
        """규칙 실행 여부 판단"""
        
        # 트리거 평가
        trigger_result = self.trigger_evaluator.evaluate_multiple_triggers(
            rule.triggers, rule.trigger_relation, market_data, self.position, current_time
        )
        
        if not trigger_result:
            return False
        
        # 조건 확인
        for condition in rule.conditions:
            if not self._check_condition(condition, rule):
                return False
        
        return True
    
    def _check_condition(self, condition: Dict[str, Any], rule: RuleConfig) -> bool:
        """조건 확인"""
        condition_type = condition.get('type', '')
        
        if condition_type == 'balance_check':
            min_balance = condition.get('min_balance', 0)
            return self.balance >= min_balance
            
        elif condition_type == 'execution_count':
            max_count = condition.get('max_count', 999)
            current_count = self.execution_counts.get(rule.rule_id, 0)
            return current_count < max_count
            
        elif condition_type == 'position_check':
            required_position = condition.get('required_position', False)
            return (self.position is not None) == required_position
        
        return True
    
    def _execute_rule(self, rule: RuleConfig, market_data: MarketData, current_time: datetime):
        """규칙 실행"""
        
        current_price = market_data.close_price
        
        try:
            if rule.action_type == ActionType.BUY:
                self._execute_buy(rule, current_price, current_time)
                
            elif rule.action_type == ActionType.SELL:
                self._execute_sell(rule, current_price, current_time, 100.0)
                
            elif rule.action_type == ActionType.PARTIAL_SELL:
                sell_percent = rule.action_params.get('amount_percent', 50.0)
                self._execute_sell(rule, current_price, current_time, sell_percent)
            
            # 실행 횟수 업데이트
            self.execution_counts[rule.rule_id] = self.execution_counts.get(rule.rule_id, 0) + 1
            
        except Exception as e:
            logger.error(f"규칙 실행 오류 {rule.rule_id}: {e}")
    
    def _execute_buy(self, rule: RuleConfig, price: float, timestamp: datetime):
        """매수 실행"""
        if self.position is not None:
            # 이미 포지션이 있으면 추가 매수
            amount_percent = rule.action_params.get('amount_percent', 20.0)
            buy_amount = self.balance * (amount_percent / 100.0)
            
            if buy_amount < price:  # 최소 1주도 못 사는 경우
                return
                
            quantity = buy_amount / price
            
            # 기존 포지션과 합산
            total_cost = (self.position.entry_price * self.position.quantity) + buy_amount
            total_quantity = self.position.quantity + quantity
            new_avg_price = total_cost / total_quantity
            
            self.position.entry_price = new_avg_price
            self.position.quantity = total_quantity
            self.balance -= buy_amount
            
        else:
            # 신규 매수
            amount_percent = rule.action_params.get('amount_percent', 20.0)
            buy_amount = self.balance * (amount_percent / 100.0)
            
            if buy_amount < price:
                return
                
            quantity = buy_amount / price
            
            self.position = Position(
                symbol="TEST",
                entry_price=price,
                quantity=quantity,
                entry_time=timestamp,
                current_price=price,
                unrealized_pnl=0.0,
                highest_price=price
            )
            
            self.balance -= buy_amount
        
        # 거래 기록
        trade = TradeResult(
            timestamp=timestamp,
            action="BUY",
            price=price,
            quantity=quantity,
            pnl=0.0,
            balance=self.balance,
            rule_id=rule.rule_id,
            trigger_description=", ".join([t.description for t in rule.triggers])
        )
        
        self.trade_history.append(trade)
        logger.info(f"매수 실행: {rule.rule_id} - {price:.2f} x {quantity:.4f}")
    
    def _execute_sell(self, rule: RuleConfig, price: float, timestamp: datetime, sell_percent: float):
        """매도 실행"""
        if self.position is None:
            return
        
        sell_quantity = self.position.quantity * (sell_percent / 100.0)
        sell_amount = sell_quantity * price
        
        # PnL 계산
        entry_cost = sell_quantity * self.position.entry_price
        pnl = sell_amount - entry_cost
        
        self.balance += sell_amount
        
        if sell_percent >= 100.0:
            # 전량 매도
            self.position = None
        else:
            # 부분 매도
            self.position.quantity -= sell_quantity
        
        # 거래 기록
        trade = TradeResult(
            timestamp=timestamp,
            action="SELL",
            price=price,
            quantity=sell_quantity,
            pnl=pnl,
            balance=self.balance,
            rule_id=rule.rule_id,
            trigger_description=", ".join([t.description for t in rule.triggers])
        )
        
        self.trade_history.append(trade)
        logger.info(f"매도 실행: {rule.rule_id} - {price:.2f} x {sell_quantity:.4f} (PnL: {pnl:.2f})")

class ComprehensiveStrategyBuilder:
    """종합 전략 빌더"""
    
    @staticmethod
    def create_comprehensive_strategy() -> StrategyConfig:
        """7가지 전략이 통합된 종합 전략 생성"""
        
        rules = []
        
        # 1. RSI 하방진입 전략
        rules.append(RuleConfig(
            rule_id="rsi_entry",
            name="RSI 하방진입",
            activation_state="READY",
            priority=10,
            triggers=[
                TriggerConfig(
                    trigger_type=TriggerType.RSI,
                    params={'threshold': 30, 'condition': '<=', 'period': 14},
                    description="RSI <= 30"
                )
            ],
            trigger_relation=TriggerRelation.AND,
            action_type=ActionType.BUY,
            action_params={'amount_percent': 20.0},
            conditions=[
                {'type': 'balance_check', 'min_balance': 100000},
                {'type': 'position_check', 'required_position': False}
            ]
        ))
        
        # 2. 수익실현 단계매도 - 5% 익절
        rules.append(RuleConfig(
            rule_id="profit_5_sell",
            name="5% 익절",
            activation_state="ACTIVE",
            priority=5,
            triggers=[
                TriggerConfig(
                    trigger_type=TriggerType.PROFIT_RATE,
                    params={'rate': 5.0, 'condition': '>='},
                    description="5% 수익"
                )
            ],
            trigger_relation=TriggerRelation.AND,
            action_type=ActionType.PARTIAL_SELL,
            action_params={'amount_percent': 25.0},
            conditions=[]
        ))
        
        # 3. 수익실현 단계매도 - 10% 익절
        rules.append(RuleConfig(
            rule_id="profit_10_sell",
            name="10% 익절",
            activation_state="ACTIVE",
            priority=5,
            triggers=[
                TriggerConfig(
                    trigger_type=TriggerType.PROFIT_RATE,
                    params={'rate': 10.0, 'condition': '>='},
                    description="10% 수익"
                )
            ],
            trigger_relation=TriggerRelation.AND,
            action_type=ActionType.PARTIAL_SELL,
            action_params={'amount_percent': 50.0},
            conditions=[]
        ))
        
        # 4. 불타기 전략 - 5% 하락시 추가 매수
        rules.append(RuleConfig(
            rule_id="dca_5_percent",
            name="5% 하락 불타기",
            activation_state="ACTIVE",
            priority=8,
            triggers=[
                TriggerConfig(
                    trigger_type=TriggerType.PROFIT_RATE,
                    params={'rate': -5.0, 'condition': '<='},
                    description="5% 손실"
                )
            ],
            trigger_relation=TriggerRelation.AND,
            action_type=ActionType.BUY,
            action_params={'amount_percent': 30.0},
            conditions=[
                {'type': 'execution_count', 'max_count': 3},
                {'type': 'balance_check', 'min_balance': 100000}
            ]
        ))
        
        # 5. 트레일링 스탑 - 3% 하락시 매도
        rules.append(RuleConfig(
            rule_id="trailing_stop_3",
            name="3% 트레일링 스탑",
            activation_state="ACTIVE",
            priority=1,  # 최고 우선순위
            triggers=[
                TriggerConfig(
                    trigger_type=TriggerType.TRAILING_STOP,
                    params={'trail_percent': 3.0},
                    description="최고가 대비 3% 하락"
                )
            ],
            trigger_relation=TriggerRelation.AND,
            action_type=ActionType.SELL,
            action_params={'amount_percent': 100.0},
            conditions=[]
        ))
        
        # 6. 급락 대응 - 10% 급락시 손절
        rules.append(RuleConfig(
            rule_id="crash_detection",
            name="급락 감지 손절",
            activation_state="ACTIVE",
            priority=0,  # 최고 우선순위
            triggers=[
                TriggerConfig(
                    trigger_type=TriggerType.RAPID_CHANGE,
                    params={'time_window': 5, 'change_percent': -10.0},
                    description="5분간 10% 급락"
                )
            ],
            trigger_relation=TriggerRelation.AND,
            action_type=ActionType.SELL,
            action_params={'amount_percent': 100.0},
            conditions=[]
        ))
        
        # 7. 시간대 매매 + RSI 조합
        rules.append(RuleConfig(
            rule_id="time_rsi_entry",
            name="시간대 RSI 매수",
            activation_state="READY",
            priority=10,
            triggers=[
                TriggerConfig(
                    trigger_type=TriggerType.TIME_RANGE,
                    params={'start_time': '09:30', 'end_time': '15:00'},
                    description="장중 시간"
                ),
                TriggerConfig(
                    trigger_type=TriggerType.RSI,
                    params={'threshold': 35, 'condition': '<=', 'period': 14},
                    description="RSI <= 35"
                )
            ],
            trigger_relation=TriggerRelation.AND,  # 둘 다 만족해야 함
            action_type=ActionType.BUY,
            action_params={'amount_percent': 15.0},
            conditions=[
                {'type': 'balance_check', 'min_balance': 50000},
                {'type': 'position_check', 'required_position': False}
            ]
        ))
        
        # 8. 거래량 + RSI 조합 전략
        rules.append(RuleConfig(
            rule_id="volume_rsi_entry",
            name="거래량 RSI 매수",
            activation_state="READY",
            priority=9,
            triggers=[
                TriggerConfig(
                    trigger_type=TriggerType.VOLUME,
                    params={'multiplier': 2.0},
                    description="거래량 2배"
                ),
                TriggerConfig(
                    trigger_type=TriggerType.RSI,
                    params={'threshold': 25, 'condition': '<=', 'period': 14},
                    description="RSI <= 25"
                )
            ],
            trigger_relation=TriggerRelation.AND,
            action_type=ActionType.BUY,
            action_params={'amount_percent': 25.0},
            conditions=[
                {'type': 'balance_check', 'min_balance': 100000}
            ]
        ))
        
        return StrategyConfig(
            strategy_id="comprehensive_v1",
            name="종합 전략 V1 - 7가지 전략 통합",
            description="RSI진입, 단계매도, 불타기, 트레일링스탑, 급락대응, 시간대매매, 거래량 확인을 모두 포함한 종합 전략",
            rules=rules
        )

class MockDataGenerator:
    """모의 데이터 생성기"""
    
    @staticmethod
    def generate_market_data(days: int = 30, start_price: float = 50000.0) -> List[MarketData]:
        """시장 데이터 생성"""
        data = []
        current_price = start_price
        base_time = datetime.now() - timedelta(days=days)
        
        for day in range(days):
            for minute in range(0, 1440, 5):  # 5분봉
                timestamp = base_time + timedelta(days=day, minutes=minute)
                
                # 랜덤 가격 변동 (더 현실적으로)
                change_percent = np.random.normal(0, 0.5)  # 평균 0, 표준편차 0.5%
                
                # 가끔 큰 변동 추가
                if np.random.random() < 0.02:  # 2% 확률
                    change_percent += np.random.choice([-5, -3, 3, 5]) * np.random.random()
                
                price_change = current_price * (change_percent / 100)
                new_price = max(current_price + price_change, 1000)  # 최소 1000원
                
                # OHLC 생성
                high = new_price * (1 + abs(np.random.normal(0, 0.2)) / 100)
                low = new_price * (1 - abs(np.random.normal(0, 0.2)) / 100)
                open_price = current_price
                close_price = new_price
                
                # 거래량 생성 (가격 변동과 상관관계)
                base_volume = 1000000
                volume_multiplier = 1 + abs(change_percent) / 2  # 변동성에 따라 거래량 증가
                volume = int(base_volume * volume_multiplier * np.random.uniform(0.5, 2.0))
                
                data.append(MarketData(
                    timestamp=timestamp,
                    open_price=open_price,
                    high_price=high,
                    low_price=low,
                    close_price=close_price,
                    volume=volume
                ))
                
                current_price = new_price
        
        return data

class BacktestReporter:
    """백테스트 결과 분석 및 리포트"""
    
    @staticmethod
    def generate_report(engine: StrategyEngine, market_data: List[MarketData]) -> Dict[str, Any]:
        """백테스트 결과 리포트 생성"""
        
        if not engine.trade_history:
            return {
                'error': '거래 내역이 없습니다',
                'total_trades': 0,
                'final_balance': engine.balance,
                'total_return_percent': 0.0
            }
        
        # 기본 통계
        total_trades = len(engine.trade_history)
        buy_trades = [t for t in engine.trade_history if t.action == 'BUY']
        sell_trades = [t for t in engine.trade_history if t.action == 'SELL']
        
        final_balance = engine.balance
        if engine.position:
            # 미실현 손익 포함
            final_price = market_data[-1].close_price
            unrealized_value = engine.position.quantity * final_price
            final_balance += unrealized_value
        
        total_return = ((final_balance - engine.initial_balance) / engine.initial_balance) * 100
        
        # PnL 분석
        realized_pnl = sum([t.pnl for t in sell_trades])
        winning_trades = [t for t in sell_trades if t.pnl > 0]
        losing_trades = [t for t in sell_trades if t.pnl < 0]
        
        win_rate = (len(winning_trades) / len(sell_trades)) * 100 if sell_trades else 0
        
        # 규칙별 실행 횟수
        rule_stats = {}
        for trade in engine.trade_history:
            rule_id = trade.rule_id
            if rule_id not in rule_stats:
                rule_stats[rule_id] = {'buy_count': 0, 'sell_count': 0, 'total_pnl': 0.0}
            
            if trade.action == 'BUY':
                rule_stats[rule_id]['buy_count'] += 1
            else:
                rule_stats[rule_id]['sell_count'] += 1
                rule_stats[rule_id]['total_pnl'] += trade.pnl
        
        report = {
            'strategy_name': '종합 전략 V1',
            'backtest_period': f"{market_data[0].timestamp} ~ {market_data[-1].timestamp}",
            'initial_balance': engine.initial_balance,
            'final_balance': final_balance,
            'total_return_percent': total_return,
            'total_trades': total_trades,
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'realized_pnl': realized_pnl,
            'win_rate_percent': win_rate,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'rule_statistics': rule_stats,
            'current_position': {
                'has_position': engine.position is not None,
                'quantity': engine.position.quantity if engine.position else 0,
                'entry_price': engine.position.entry_price if engine.position else 0,
                'unrealized_pnl': engine.position.unrealized_pnl if engine.position else 0,
            }
        }
        
        return report

def main():
    """메인 실행 함수"""
    print("🚀 종합 전략 엔진 시작!")
    print("=" * 60)
    
    # 1. 전략 생성
    print("📋 종합 전략 생성 중...")
    strategy = ComprehensiveStrategyBuilder.create_comprehensive_strategy()
    print(f"✅ 전략 생성 완료: {strategy.name}")
    print(f"   📊 총 {len(strategy.rules)}개 규칙 포함")
    
    for rule in strategy.rules:
        triggers_desc = " + ".join([t.description for t in rule.triggers])
        print(f"   - {rule.name}: {triggers_desc}")
    
    # 2. 모의 데이터 생성  
    print("\n📈 시장 데이터 생성 중...")
    market_data = MockDataGenerator.generate_market_data(days=30, start_price=50000)
    print(f"✅ {len(market_data)}개 데이터 포인트 생성 (30일간)")
    print(f"   💰 시작가: {market_data[0].close_price:,.0f}원")
    print(f"   💰 종료가: {market_data[-1].close_price:,.0f}원")
    price_change = ((market_data[-1].close_price - market_data[0].close_price) / market_data[0].close_price) * 100
    print(f"   📊 가격 변동: {price_change:+.2f}%")
    
    # 3. 백테스트 실행
    print("\n🎯 백테스트 실행 중...")
    engine = StrategyEngine(initial_balance=1000000.0)
    
    start_time = time.time()
    trades = engine.execute_strategy(strategy, market_data)
    end_time = time.time()
    
    print(f"✅ 백테스트 완료! (실행시간: {end_time - start_time:.2f}초)")
    
    # 4. 결과 분석
    print("\n📊 백테스트 결과 분석...")
    report = BacktestReporter.generate_report(engine, market_data)
    
    print("=" * 60)
    print("🎊 **백테스트 결과 요약**")
    print("=" * 60)
    print(f"📈 전략명: {report['strategy_name']}")
    print(f"⏰ 기간: {report['backtest_period']}")
    print(f"💰 초기 자본: {report['initial_balance']:,}원")
    print(f"💰 최종 자본: {report['final_balance']:,.0f}원")
    print(f"📊 총 수익률: {report['total_return_percent']:+.2f}%")
    print(f"🔄 총 거래 횟수: {report['total_trades']}회")
    print(f"📈 매수 거래: {report['buy_trades']}회")
    print(f"📉 매도 거래: {report['sell_trades']}회")
    print(f"💵 실현 손익: {report['realized_pnl']:+,.0f}원")
    print(f"🎯 승률: {report['win_rate_percent']:.1f}%")
    print(f"✅ 성공 거래: {report['winning_trades']}회")
    print(f"❌ 실패 거래: {report['losing_trades']}회")
    
    if report['current_position']['has_position']:
        print(f"\n📍 현재 포지션:")
        print(f"   수량: {report['current_position']['quantity']:.4f}")
        print(f"   진입가: {report['current_position']['entry_price']:,.0f}원")
        print(f"   미실현 손익: {report['current_position']['unrealized_pnl']:+,.0f}원")
    
    print("\n📈 규칙별 실행 통계:")
    print("-" * 60)
    for rule_id, stats in report['rule_statistics'].items():
        print(f"🎯 {rule_id}:")
        print(f"   매수: {stats['buy_count']}회, 매도: {stats['sell_count']}회")
        print(f"   손익: {stats['total_pnl']:+,.0f}원")
    
    # 5. 거래 히스토리 출력 (최근 10개만)
    if trades:
        print("\n📋 최근 거래 내역 (최근 10개):")
        print("-" * 80)
        for trade in trades[-10:]:
            print(f"{trade.timestamp.strftime('%m/%d %H:%M')} | "
                  f"{trade.action:4s} | "
                  f"{trade.price:8,.0f}원 | "
                  f"수량:{trade.quantity:7.4f} | "
                  f"손익:{trade.pnl:+8,.0f}원 | "
                  f"{trade.rule_id}")
    
    print("\n" + "=" * 60)
    print("🎉 종합 전략 백테스트 완료!")
    
    # 성과 평가
    if report['total_return_percent'] > 0:
        print("🎊 축하합니다! 수익을 달성했습니다!")
    else:
        print("😔 손실이 발생했습니다. 전략을 재검토해보세요.")
    
    print(f"📊 최종 수익률: {report['total_return_percent']:+.2f}%")
    
if __name__ == "__main__":
    main()
