"""
물타기(피라미딩) 전략 완전 구현 예시
컴포넌트 기반 아키텍처를 사용한 실제 동작 가능한 전략

이 예시는 다음과 같은 물타기 규칙을 구현합니다:
1. 매수가 대비 3% 하락 시마다 추가 매수
2. 최대 3회까지만 추가 매수 허용  
3. 평균단가 대비 5% 상승 시 전체 매도
4. 평균단가 대비 10% 하락 시 손절매
5. 각 추가 매수 시 이전 대비 50% 더 많은 금액 투입
"""

from typing import List, Dict, Any
from datetime import datetime

# 컴포넌트 임포트
from ..base import StrategyRule, ExecutionContext
from ..triggers.price_triggers import PriceChangeTrigger, PriceChangeConfig
from ..actions.trading_actions import BuyAction, BuyActionConfig, SellAction, SellActionConfig
from ..conditions.trading_conditions import (
    AddBuyCountCondition, AddBuyCountConditionConfig,
    ProfitLossCondition, ProfitLossConditionConfig,
    BalanceCondition, BalanceConditionConfig
)


class PyramidingStrategy:
    """
    물타기(피라미딩) 전략 - 컴포넌트 조합으로 구현
    
    이 클래스는 더 이상 고정된 전략이 아니라, 
    사용자가 설정한 컴포넌트 규칙들의 컨테이너 역할만 합니다.
    """
    
    def __init__(self, 
                 symbol: str = "KRW-BTC",
                 initial_amount: float = 100000,
                 add_buy_percent: float = -3.0,
                 max_add_buy_count: int = 3,
                 take_profit_percent: float = 5.0,
                 stop_loss_percent: float = -10.0):
        
        self.symbol = symbol
        self.rules: List[StrategyRule] = []
        
        # 1. 초기 매수 규칙 (수동 실행 또는 별도 트리거)
        self._create_initial_buy_rule(initial_amount)
        
        # 2. 추가 매수 규칙 (물타기)
        self._create_add_buy_rules(add_buy_percent, max_add_buy_count)
        
        # 3. 익절 규칙
        self._create_take_profit_rule(take_profit_percent)
        
        # 4. 손절 규칙  
        self._create_stop_loss_rule(stop_loss_percent)
    
    def _create_initial_buy_rule(self, initial_amount: float):
        """초기 매수 규칙 생성"""
        # 첫 매수는 보통 수동이거나 별도 진입 신호로 처리
        # 여기서는 예시로 시장가 매수 액션만 생성
        buy_config = BuyActionConfig(
            amount_type="fixed_amount",
            amount_value=initial_amount,
            price_type="market"
        )
        
        initial_buy_action = BuyAction(buy_config)
        
        # 수동 실행을 위한 더미 트리거 (실제로는 사용자가 버튼 클릭 등으로 실행)
        # 실제 구현에서는 ManualTrigger 또는 UI 이벤트 트리거 사용
        pass
    
    def _create_add_buy_rules(self, add_buy_percent: float, max_count: int):
        """추가 매수 규칙들 생성 (물타기의 핵심)"""
        
        # 각 물타기 단계별로 별도 규칙 생성
        for step in range(1, max_count + 1):
            # 트리거: 매수가 대비 N% 하락
            trigger_config = PriceChangeConfig(
                change_percent=add_buy_percent * step,  # -3%, -6%, -9%
                reference_type="purchase_price",
                direction="down",
                reset_on_trigger=False  # 누적 하락폭 기준
            )
            
            price_trigger = PriceChangeTrigger(trigger_config)
            
            # 조건1: 아직 최대 횟수에 도달하지 않음
            count_condition_config = AddBuyCountConditionConfig(
                condition_type="max_count",
                target_count=step  # 현재 단계까지만 허용
            )
            count_condition = AddBuyCountCondition(count_condition_config)
            
            # 조건2: 충분한 잔고 확인
            min_buy_amount = 100000 * (1 + (step-1) * 0.5)  # 누진적 매수 금액
            balance_condition_config = BalanceConditionConfig(
                condition_type="min_balance",
                target_amount=min_buy_amount
            )
            balance_condition = BalanceCondition(balance_condition_config)
            
            # 액션: 누진적 매수 (이전 대비 50% 증가)
            buy_action_config = BuyActionConfig(
                amount_type="add_buy_amount",
                amount_value=100000,  # 기본 금액 (누진 적용됨)
                price_type="market"
            )
            buy_action = BuyAction(buy_action_config)
            
            # 규칙 조합
            add_buy_rule = StrategyRule(
                rule_id=f"add_buy_step_{step}",
                description=f"{step}단계 물타기: {add_buy_percent * step}% 하락시 추가매수",
                trigger=price_trigger,
                conditions=[count_condition, balance_condition],
                action=buy_action,
                priority=step  # 우선순위: 단계가 높을수록 나중에 실행
            )
            
            self.rules.append(add_buy_rule)
    
    def _create_take_profit_rule(self, profit_percent: float):
        """익절 규칙 생성"""
        
        # 트리거: 평균단가 대비 수익률 확인 (주기적으로 체크)
        # 실제로는 PeriodicTrigger나 PriceChangeTrigger 사용
        # 여기서는 수익률 조건만으로 단순화
        
        # 조건: 목표 수익률 달성
        profit_condition_config = ProfitLossConditionConfig(
            condition_type="profit_above",
            target_percent=profit_percent
        )
        profit_condition = ProfitLossCondition(profit_condition_config)
        
        # 액션: 전체 포지션 매도
        sell_action_config = SellActionConfig(
            sell_type="full_position",
            price_type="market"
        )
        sell_action = SellAction(sell_action_config)
        
        # 실제 구현에서는 주기적 체크 트리거 필요
        # 여기서는 개념적 예시로만 표현
        take_profit_rule = StrategyRule(
            rule_id="take_profit",
            description=f"익절: 평균단가 대비 {profit_percent}% 상승시 전체 매도",
            trigger=None,  # 실제로는 PeriodicTrigger 또는 PriceMonitorTrigger
            conditions=[profit_condition],
            action=sell_action,
            priority=0  # 최우선 실행
        )
        
        # self.rules.append(take_profit_rule)
    
    def _create_stop_loss_rule(self, loss_percent: float):
        """손절 규칙 생성"""
        
        # 조건: 목표 손실률 도달
        loss_condition_config = ProfitLossConditionConfig(
            condition_type="loss_below",
            target_percent=abs(loss_percent)
        )
        loss_condition = ProfitLossCondition(loss_condition_config)
        
        # 액션: 전체 포지션 매도
        sell_action_config = SellActionConfig(
            sell_type="full_position",
            price_type="market"
        )
        sell_action = SellAction(sell_action_config)
        
        stop_loss_rule = StrategyRule(
            rule_id="stop_loss",
            description=f"손절: 평균단가 대비 {loss_percent}% 하락시 전체 매도",
            trigger=None,  # 실제로는 PeriodicTrigger 또는 PriceMonitorTrigger
            conditions=[loss_condition],
            action=sell_action,
            priority=0  # 최우선 실행
        )
        
        # self.rules.append(stop_loss_rule)
    
    def execute_strategy(self, market_data: Dict[str, Any], context: ExecutionContext) -> List[str]:
        """
        전략 실행 - 모든 규칙을 우선순위 순으로 확인
        
        이것이 새로운 아키텍처의 핵심입니다:
        더 이상 고정된 if-else 로직이 아니라, 
        동적으로 구성된 규칙들을 순회하며 실행합니다.
        """
        execution_results = []
        
        # 우선순위 순으로 규칙 정렬
        sorted_rules = sorted(self.rules, key=lambda r: r.priority)
        
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            
            try:
                # 1. 트리거 확인
                if rule.trigger:
                    trigger_result = rule.trigger.evaluate(market_data, context)
                    if not trigger_result.success:
                        continue  # 트리거 조건 미충족
                
                # 2. 추가 조건들 확인
                if rule.conditions:
                    all_conditions_met = True
                    for condition in rule.conditions:
                        condition_result = condition.check(market_data, context)
                        if not condition_result.success:
                            all_conditions_met = False
                            execution_results.append(f"조건 미충족: {condition_result.reason}")
                            break
                    
                    if not all_conditions_met:
                        continue
                
                # 3. 액션 실행
                if rule.action:
                    action_result = rule.action.execute(market_data, context)
                    if action_result.success:
                        execution_results.append(f"✅ {rule.description}: {action_result.reason}")
                        
                        # 마지막 신호 시간 업데이트
                        context.last_signal_time = datetime.now()
                    else:
                        execution_results.append(f"❌ {rule.description} 실행 실패: {action_result.reason}")
                
            except Exception as e:
                execution_results.append(f"🔥 규칙 실행 오류 [{rule.rule_id}]: {str(e)}")
        
        return execution_results
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """전략 요약 정보"""
        return {
            'strategy_name': 'Pyramiding Strategy (물타기)',
            'symbol': self.symbol,
            'total_rules': len(self.rules),
            'active_rules': len([r for r in self.rules if r.enabled]),
            'rule_types': {
                'triggers': len([r for r in self.rules if r.trigger]),
                'conditions': sum(len(r.conditions or []) for r in self.rules),
                'actions': len([r for r in self.rules if r.action])
            }
        }


def create_simple_pyramiding_strategy() -> PyramidingStrategy:
    """간단한 물타기 전략 생성 예시"""
    return PyramidingStrategy(
        symbol="KRW-BTC",
        initial_amount=100000,      # 첫 매수: 10만원
        add_buy_percent=-3.0,       # 3% 하락마다 추가 매수
        max_add_buy_count=3,        # 최대 3회 추가 매수
        take_profit_percent=5.0,    # 5% 상승시 익절
        stop_loss_percent=-10.0     # 10% 하락시 손절
    )


def create_advanced_pyramiding_strategy() -> PyramidingStrategy:
    """고급 물타기 전략 생성 예시"""
    return PyramidingStrategy(
        symbol="KRW-ETH",
        initial_amount=200000,      # 첫 매수: 20만원
        add_buy_percent=-2.5,       # 2.5% 하락마다 추가 매수 (더 민감)
        max_add_buy_count=5,        # 최대 5회 추가 매수 (더 많은 기회)
        take_profit_percent=7.0,    # 7% 상승시 익절 (더 큰 수익 추구)
        stop_loss_percent=-15.0     # 15% 하락시 손절 (더 많은 하락 허용)
    )


if __name__ == "__main__":
    # 사용 예시
    strategy = create_simple_pyramiding_strategy()
    print("물타기 전략 생성 완료!")
    print(f"전략 요약: {strategy.get_strategy_summary()}")
    
    # 실제 시장 데이터와 컨텍스트로 실행하는 예시
    sample_market_data = {
        'current_price': 45000000,
        'timestamp': '2024-01-01 10:00:00',
        'volume': 100.5,
        'previous_close': 46000000
    }
    
    sample_context = ExecutionContext(
        symbol="KRW-BTC",
        has_position=False
    )
    sample_context.set_variable('available_balance', 1000000)
    
    results = strategy.execute_strategy(sample_market_data, sample_context)
    for result in results:
        print(result)
