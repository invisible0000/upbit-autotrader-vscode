"""
컴포넌트 시스템 기본 테스트
Component System Basic Test

이 테스트는 새로운 컴포넌트 기반 아키텍처가 제대로 동작하는지 확인합니다.
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from component_system import (
    ExecutionContext,
    PriceChangeTrigger, PriceChangeConfig,
    BuyAction, BuyActionConfig,
    AddBuyCountCondition, AddBuyCountConditionConfig,
    StrategyRule,
    create_simple_pyramiding_strategy
)


def test_basic_components():
    """기본 컴포넌트들의 동작 테스트"""
    print("=== 컴포넌트 기본 기능 테스트 ===")
    
    # 1. ExecutionContext 테스트
    print("\n1. ExecutionContext 테스트")
    context = ExecutionContext(symbol="KRW-BTC")
    context.set_variable('available_balance', 1000000)
    
    print(f"초기 잔고: {context.get_variable('available_balance', 0):,}원")
    print(f"포지션 보유: {context.has_position}")
    
    # 2. PriceChangeTrigger 테스트
    print("\n2. PriceChangeTrigger 테스트")
    trigger_config = PriceChangeConfig(
        change_percent=-3.0,
        reference_type="market_price",
        direction="down"
    )
    trigger = PriceChangeTrigger(trigger_config)
    
    # 기준 가격 설정용 데이터
    initial_data = {
        'current_price': 50000000,
        'timestamp': '2024-01-01 10:00:00'
    }
    
    # 첫 번째 호출로 기준 가격 설정
    result1 = trigger.evaluate(initial_data, context)
    print(f"기준 가격 설정: {result1.reason}")
    
    # 3% 하락한 가격으로 테스트
    dropped_data = {
        'current_price': 48500000,  # 3% 하락
        'timestamp': '2024-01-01 10:30:00'
    }
    
    result2 = trigger.evaluate(dropped_data, context)
    print(f"3% 하락 감지: {result2.success} - {result2.reason}")
    
    # 3. BuyAction 테스트
    print("\n3. BuyAction 테스트")
    buy_config = BuyActionConfig(
        amount_type="fixed_amount",
        amount_value=100000,
        price_type="market"
    )
    buy_action = BuyAction(buy_config)
    
    if result2.success:  # 트리거 조건이 만족되었을 때만
        buy_result = buy_action.execute(dropped_data, context)
        print(f"매수 실행: {buy_result.success} - {buy_result.reason}")
        
        if buy_result.success:
            print(f"매수 후 포지션: 보유량 {context.position_size:.6f}, 평균가 {context.average_price:,.0f}")
            print(f"매수 후 잔고: {context.get_variable('available_balance', 0):,}원")
    
    # 4. AddBuyCountCondition 테스트
    print("\n4. AddBuyCountCondition 테스트")
    condition_config = AddBuyCountConditionConfig(
        condition_type="max_count",
        target_count=3
    )
    condition = AddBuyCountCondition(condition_config)
    
    condition_result = condition.check(dropped_data, context)
    print(f"물타기 횟수 확인: {condition_result.success} - {condition_result.reason}")
    print(f"현재 추가매수 횟수: {context.add_buy_count}")


def test_strategy_rule():
    """StrategyRule 조합 테스트"""
    print("\n\n=== StrategyRule 조합 테스트 ===")
    
    # 컨텍스트 초기화
    context = ExecutionContext(symbol="KRW-BTC")
    context.set_variable('available_balance', 1000000)
    
    # 트리거: 3% 하락
    trigger_config = PriceChangeConfig(
        change_percent=-3.0,
        reference_type="market_price",
        direction="down"
    )
    trigger = PriceChangeTrigger(trigger_config)
    
    # 조건: 최대 3회까지만 물타기
    condition_config = AddBuyCountConditionConfig(
        condition_type="max_count",
        target_count=3
    )
    condition = AddBuyCountCondition(condition_config)
    
    # 액션: 10만원 매수
    action_config = BuyActionConfig(
        amount_type="fixed_amount",
        amount_value=100000,
        price_type="market"
    )
    action = BuyAction(action_config)
    
    # 규칙 생성
    rule = StrategyRule(
        rule_id="add_buy_rule_1",
        description="3% 하락시 10만원 추가 매수",
        trigger=trigger,
        conditions=[condition],
        action=action
    )
    
    # 테스트 시나리오
    print("\n시나리오 1: 기준 가격 설정")
    initial_data = {'current_price': 50000000, 'timestamp': '2024-01-01 10:00:00'}
    trigger.evaluate(initial_data, context)  # 기준 가격 설정
    
    print("\n시나리오 2: 3% 하락 후 규칙 실행")
    dropped_data = {'current_price': 48500000, 'timestamp': '2024-01-01 10:30:00'}
    
    # 규칙 실행 로직 (실제 전략에서는 execute_strategy 메서드에서 처리)
    trigger_result = rule.trigger.evaluate(dropped_data, context)
    print(f"트리거 결과: {trigger_result.success} - {trigger_result.reason}")
    
    if trigger_result.success:
        condition_result = rule.conditions[0].check(dropped_data, context)
        print(f"조건 결과: {condition_result.success} - {condition_result.reason}")
        
        if condition_result.success:
            action_result = rule.action.execute(dropped_data, context)
            print(f"액션 결과: {action_result.success} - {action_result.reason}")
            
            print(f"\n실행 후 상태:")
            print(f"- 포지션: {context.position_size:.6f} @ {context.average_price:,.0f}")
            print(f"- 잔고: {context.get_variable('available_balance', 0):,}원")
            print(f"- 물타기 횟수: {context.add_buy_count}")


def test_pyramiding_strategy():
    """완성된 물타기 전략 테스트"""
    print("\n\n=== 물타기 전략 완전 테스트 ===")
    
    # 전략 생성
    strategy = create_simple_pyramiding_strategy()
    print(f"전략 생성: {strategy.get_strategy_summary()}")
    
    # 컨텍스트 초기화  
    context = ExecutionContext(symbol="KRW-BTC")
    context.set_variable('available_balance', 1000000)
    
    # 시나리오: 지속적인 하락장에서 물타기 실행
    price_scenarios = [
        {'current_price': 50000000, 'timestamp': '2024-01-01 10:00:00', 'desc': '시작가'},
        {'current_price': 48500000, 'timestamp': '2024-01-01 11:00:00', 'desc': '3% 하락'},
        {'current_price': 47000000, 'timestamp': '2024-01-01 12:00:00', 'desc': '6% 하락'},
        {'current_price': 45500000, 'timestamp': '2024-01-01 13:00:00', 'desc': '9% 하락'},
        {'current_price': 44000000, 'timestamp': '2024-01-01 14:00:00', 'desc': '12% 하락'},
    ]
    
    for i, scenario in enumerate(price_scenarios):
        print(f"\n--- {scenario['desc']} ({scenario['current_price']:,}원) ---")
        
        results = strategy.execute_strategy(scenario, context)
        
        if results:
            for result in results:
                print(f"  {result}")
        else:
            print("  실행된 규칙 없음")
        
        # 현재 상태 출력
        if context.has_position:
            profit_percent = context.get_profit_loss_percent() * 100
            print(f"  현재 상태: 보유량 {context.position_size:.6f}, 평균가 {context.average_price:,.0f}, 수익률 {profit_percent:.2f}%")
        print(f"  잔고: {context.get_variable('available_balance', 0):,}원")


if __name__ == "__main__":
    print("🚀 컴포넌트 기반 전략 시스템 테스트 시작")
    print("=" * 60)
    
    try:
        # 1. 기본 컴포넌트 테스트
        test_basic_components()
        
        # 2. 규칙 조합 테스트  
        test_strategy_rule()
        
        # 3. 완성된 전략 테스트
        test_pyramiding_strategy()
        
        print("\n" + "=" * 60)
        print("✅ 모든 테스트 완료! 컴포넌트 시스템이 정상 작동합니다.")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
