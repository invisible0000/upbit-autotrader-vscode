"""
7규칙 전략 예제: 스마트 평균회귀 시스템
- 원자적 구성요소를 활용한 완전한 매매 전략 예제
- 진입/청산/리스크관리를 7개 규칙으로 세분화
"""

from atomic_strategy_components import *

def create_seven_rule_strategy_example():
    """7규칙 전략 예제 생성"""
    
    builder = StrategyBuilder()
    
    # =================================================================
    # 1단계: 추가 변수 정의 (기본 외 필요한 변수들)
    # =================================================================
    
    # 볼륨 관련 변수
    volume_sma = Variable(
        id="indicator.volume_sma",
        name="거래량 평균",
        category=VariableCategory.VOLUME,
        parameters={"period": 20},
        return_type=ReturnType.SCALAR,
        description="20일 평균 거래량",
        ui_widget_type="slider",
        ui_constraints={"min": 5, "max": 50, "step": 1},
        ui_help_text="거래량 평균 계산 기간",
        ui_icon="📊"
    )
    builder.variables[volume_sma.id] = volume_sma
    
    # 현재 거래량
    current_volume = Variable(
        id="volume.current",
        name="현재 거래량",
        category=VariableCategory.VOLUME,
        parameters={},
        return_type=ReturnType.SCALAR,
        description="현재 캔들의 거래량",
        ui_widget_type="display",
        ui_help_text="실시간 거래량",
        ui_icon="📈"
    )
    builder.variables[current_volume.id] = current_volume
    
    # 수익률 관련
    profit_target = Variable(
        id="state.profit_target",
        name="목표 수익률",
        category=VariableCategory.STATE,
        parameters={"target_percent": 5.0},
        return_type=ReturnType.SCALAR,
        description="목표 수익률 (%)",
        ui_widget_type="slider",
        ui_constraints={"min": 1, "max": 20, "step": 0.5},
        ui_help_text="익절 목표 수익률",
        ui_icon="🎯"
    )
    builder.variables[profit_target.id] = profit_target
    
    # =================================================================
    # 2단계: 조건 생성 (기본 + 추가 조건들)
    # =================================================================
    
    # 거래량 조건
    volume_condition = builder.create_custom_condition(
        variable_id="volume.current",
        operator=Operator.GREATER,
        target="indicator.volume_sma",
        name="거래량 증가"
    )
    
    # 수익률 조건들
    profit_5_condition = builder.create_custom_condition(
        variable_id="state.profit_percent",
        operator=Operator.GREATER_EQUAL,
        target=5.0,
        name="5% 수익 달성"
    )
    
    profit_10_condition = builder.create_custom_condition(
        variable_id="state.profit_percent",
        operator=Operator.GREATER_EQUAL,
        target=10.0,
        name="10% 수익 달성"
    )
    
    loss_3_condition = builder.create_custom_condition(
        variable_id="state.profit_percent",
        operator=Operator.LESS_EQUAL,
        target=-3.0,
        name="3% 손실 발생"
    )
    
    loss_5_condition = builder.create_custom_condition(
        variable_id="state.profit_percent",
        operator=Operator.LESS_EQUAL,
        target=-5.0,
        name="5% 손실 발생"
    )
    
    # =================================================================
    # 3단계: 액션 생성 (다양한 매매 액션들)
    # =================================================================
    
    # 부분 매수 액션
    partial_buy = Action(
        id="action_buy_half_equity",
        name="절반 자금 매수",
        action_type=ActionType.BUY,
        quantity_rule=QuantityRule.PERCENT_EQUITY,
        quantity_parameter=0.5,
        description="가용 현금 50% 매수",
        ui_color="#4CAF50",
        ui_icon="💰"
    )
    builder.actions[partial_buy.id] = partial_buy
    
    # 부분 매도 액션들
    sell_quarter = Action(
        id="action_sell_quarter",
        name="25% 매도",
        action_type=ActionType.SELL,
        quantity_rule=QuantityRule.PERCENT_POSITION,
        quantity_parameter=0.25,
        description="보유 포지션 25% 매도",
        ui_color="#FF9800",
        ui_icon="💸"
    )
    builder.actions[sell_quarter.id] = sell_quarter
    
    # =================================================================
    # 4단계: 7개 규칙 생성
    # =================================================================
    
    print("🚀 7규칙 전략 생성 시작...")
    
    # 규칙 1: 진입 필터 (거래량 확인)
    rule1_id = builder.create_rule(
        name="거래량 필터",
        role=RuleRole.RISK_FILTER,
        condition_ids=[volume_condition],
        logic=LogicCombination.AND,
        action_id="action_buy_all_cash"  # 실제로는 필터 역할
    )
    print(f"✅ 규칙 1 생성: {builder.rules[rule1_id].name}")
    
    # 규칙 2: 메인 진입 (RSI + 볼린저밴드 AND)
    rule2_id = builder.create_rule(
        name="이중 과매도 진입",
        role=RuleRole.ENTRY,
        condition_ids=["cond_rsi_oversold", "cond_price_below_bb_lower"],
        logic=LogicCombination.AND,
        action_id="action_buy_all_cash"
    )
    print(f"✅ 규칙 2 생성: {builder.rules[rule2_id].name}")
    
    # 규칙 3: 1차 익절 (5% 수익 시 25% 매도)
    rule3_id = builder.create_rule(
        name="1차 익절",
        role=RuleRole.EXIT,
        condition_ids=[profit_5_condition],
        logic=LogicCombination.AND,
        action_id="action_sell_quarter"
    )
    print(f"✅ 규칙 3 생성: {builder.rules[rule3_id].name}")
    
    # 규칙 4: 2차 익절 (10% 수익 시 50% 매도)
    rule4_id = builder.create_rule(
        name="2차 익절",
        role=RuleRole.EXIT,
        condition_ids=[profit_10_condition],
        logic=LogicCombination.AND,
        action_id="action_sell_half"
    )
    print(f"✅ 규칙 4 생성: {builder.rules[rule4_id].name}")
    
    # 규칙 5: 1차 손절 (3% 손실 시 50% 매도)
    rule5_id = builder.create_rule(
        name="1차 손절",
        role=RuleRole.EXIT,
        condition_ids=[loss_3_condition],
        logic=LogicCombination.AND,
        action_id="action_sell_half"
    )
    print(f"✅ 규칙 5 생성: {builder.rules[rule5_id].name}")
    
    # 규칙 6: 2차 손절 (5% 손실 시 전량 청산)
    rule6_id = builder.create_rule(
        name="2차 손절 (전량 청산)",
        role=RuleRole.EXIT,
        condition_ids=[loss_5_condition],
        logic=LogicCombination.AND,
        action_id="action_exit_all"
    )
    print(f"✅ 규칙 6 생성: {builder.rules[rule6_id].name}")
    
    # 규칙 7: RSI 과매수 시 전량 청산
    rule7_id = builder.create_rule(
        name="과매수 청산",
        role=RuleRole.EXIT,
        condition_ids=["cond_rsi_overbought"],
        logic=LogicCombination.AND,
        action_id="action_exit_all"
    )
    print(f"✅ 규칙 7 생성: {builder.rules[rule7_id].name}")
    
    # =================================================================
    # 5단계: 전략 생성 및 검증
    # =================================================================
    
    all_rule_ids = [rule1_id, rule2_id, rule3_id, rule4_id, rule5_id, rule6_id, rule7_id]
    
    strategy_id = builder.create_strategy(
        name="7규칙 스마트 평균회귀 전략",
        rule_ids=all_rule_ids,
        description="""
        RSI + 볼린저밴드 기반 평균회귀 전략
        • 진입: RSI 과매도 + BB 하단 돌파 + 거래량 증가
        • 익절: 5% → 25% 매도, 10% → 50% 매도
        • 손절: 3% → 50% 매도, 5% → 전량 청산
        • 추가: RSI 과매수 시 전량 청산
        """
    )
    
    # 전략 검증
    validation = builder.validate_strategy(strategy_id)
    
    print("\n📋 7규칙 전략 검증 결과:")
    print(f"• 전략 ID: {strategy_id}")
    print(f"• 유효성: {'✅ 유효' if validation['is_valid'] else '❌ 무효'}")
    print(f"• 진입 규칙: {'있음' if validation['has_entry'] else '없음'}")
    print(f"• 청산 규칙: {'있음' if validation['has_exit'] else '없음'}")
    
    if validation["errors"]:
        print("❌ 오류:")
        for error in validation["errors"]:
            print(f"  - {error}")
    
    if validation["warnings"]:
        print("⚠️ 경고:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")
    
    # =================================================================
    # 6단계: 규칙별 상세 정보 출력
    # =================================================================
    
    print(f"\n🧬 전략 구성 상세 정보:")
    print(f"전략명: {builder.strategies[strategy_id].name}")
    print(f"총 규칙 수: {len(all_rule_ids)}개")
    print("=" * 60)
    
    for i, rule_id in enumerate(all_rule_ids, 1):
        rule = builder.rules[rule_id]
        print(f"\n📌 규칙 {i}: {rule.name}")
        print(f"   역할: {rule.role.value}")
        print(f"   조건: {rule.logic_combination.value} 조합")
        
        for j, condition_id in enumerate(rule.conditions):
            condition = builder.conditions[condition_id]
            prefix = "   └─" if j == len(rule.conditions) - 1 else "   ├─"
            print(f"{prefix} {condition.name}: {condition.description}")
        
        action = builder.actions[rule.action]
        print(f"   ➡️ 액션: {action.name} ({action.description})")
    
    return builder, strategy_id

# =================================================================
# 사용자 상호작용 시나리오 예제
# =================================================================

def demonstrate_ui_interaction_scenarios():
    """UI 상호작용 시나리오 시연"""
    
    print("\n" + "=" * 80)
    print("🎮 사용자 상호작용 시나리오 예제")
    print("=" * 80)
    
    print("""
    🎯 시나리오 1: RSI + 볼린저밴드 AND 조건 만들기
    
    1. 왼쪽 팔레트 → 🎯조건 탭 클릭
    2. "📉 RSI 과매도" 버튼 클릭 → 오른쪽 캔버스 "선택된 컴포넌트"에 추가
    3. "⬇️ 가격 < 볼린저 하단" 버튼 클릭 → 캔버스에 추가
    4. ⚡액션 탭에서 "💰 전량 매수" 클릭 → 캔버스에 추가
    5. 오른쪽 캔버스에서 "🔧 규칙 만들기" 버튼 클릭
    6. 팝업에서 규칙 이름: "이중 과매도 진입"
    7. 역할: "ENTRY" 선택
    8. 조건 조합: "AND (모든 조건 만족)" 선택
    9. OK 클릭 → 규칙 카드가 캔버스에 생성됨
    """)
    
    print("""
    🎯 시나리오 2: 커스텀 조건 생성 (가격 5% 상승)
    
    1. 🎯조건 탭 → "🔧 새 조건 만들기" 클릭
    2. 팝업에서:
       - 변수 선택: "현재 수익률(%)"
       - 연산자: ">="
       - 비교 대상: "고정값" → "5" 입력
       - 조건 이름: "5% 수익 달성"
    3. 실시간 미리보기: "📊 현재 수익률(%) >= 5"
    4. OK 클릭 → 새 조건이 생성되어 캔버스에 추가
    """)
    
    print("""
    🎯 시나리오 3: 변수 파라미터 조정
    
    1. 📊변수 탭 → "📈 RSI 지표" 클릭
    2. 파라미터 설정 팝업:
       - period 슬라이더: 14 → 21로 조정
       - 실시간 값 표시: "21" 
       - 도움말: "RSI 계산 기간 (일반적으로 14일)"
    3. OK 클릭 → RSI(21) 설정으로 조건 생성
    """)
    
    print("""
    🎯 시나리오 4: 전략 검증 및 저장
    
    1. 여러 규칙 생성 후 "✅ 전략 검증" 클릭
    2. 검증 결과 팝업:
       ✅ 전략이 유효합니다!
       • 진입 규칙: 있음 (2개)
       • 청산 규칙: 있음 (4개)
       
    3. "💾 전략 저장" 클릭
    4. 전략 이름 입력: "7규칙 스마트 평균회귀 전략"
    5. 설명 입력: "RSI + BB 기반 다단계 익절/손절 시스템"
    6. 저장 완료 → 상태바에 "저장됨: 7규칙 스마트 평균회귀 전략" 표시
    """)
    
    print("""
    🎯 시나리오 5: 규칙 카드 관리
    
    1. 생성된 규칙 카드에서:
       - 🚀 진입 규칙: 녹색 배경
       - 🛑 청산 규칙: 빨간색 배경  
       - 🛡️ 필터 규칙: 주황색 배경
       
    2. 각 카드 호버 시: 파란색 테두리 + 그림자 효과
    3. 카드 내 조건들: AND/OR 논리 표시
    4. 카드 우상단 ❌ 버튼으로 개별 규칙 삭제
    5. "🗑️ 캔버스 초기화"로 전체 초기화
    """)

if __name__ == "__main__":
    # 7규칙 전략 예제 실행
    builder, strategy_id = create_seven_rule_strategy_example()
    
    # UI 상호작용 시나리오 설명
    demonstrate_ui_interaction_scenarios()
    
    print(f"\n🎉 7규칙 전략 생성 완료!")
    print(f"전략 ID: {strategy_id}")
    print(f"UI에서 이 전략을 재현하려면 위의 시나리오를 따라하세요!")
