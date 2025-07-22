"""
원자적 전략 구성요소 데이터 모델
- Variable -> Condition -> Action -> Rule -> Strategy 위계 구조
- UI와 백엔드 로직 분리를 위한 표준화된 컴포넌트 정의
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import json

# =============================================================================
# 계층 1: 변수 (Variable) - "무엇을 볼 것인가?"
# =============================================================================

class VariableCategory(Enum):
    INDICATOR = "지표"
    PRICE = "가격"
    STATE = "상태"
    TIME = "시간"
    VOLUME = "거래량"

class ReturnType(Enum):
    SCALAR = "숫자"
    SERIES = "시계열"
    OBJECT = "객체"

@dataclass
class Variable:
    id: str                             # indicator.rsi, price.close
    name: str                          # "RSI 지표", "현재가"
    category: VariableCategory         # 지표, 가격, 상태, 시간
    parameters: Dict[str, Any]         # {"period": 14}
    return_type: ReturnType           # 숫자, 시계열, 객체
    description: str                  # "지정된 기간의 상대강도지수"
    
    # UI 관련 메타데이터
    ui_widget_type: str = "number"    # number, slider, dropdown
    ui_constraints: Dict[str, Any] = field(default_factory=dict)  # min, max, step
    ui_help_text: str = ""           # 사용자에게 보여줄 도움말
    ui_icon: str = "📊"              # UI에 표시할 아이콘

# =============================================================================
# 계층 2: 조건 (Condition) - "어떤 상황인가?"
# =============================================================================

class Operator(Enum):
    GREATER = ">"
    LESS = "<"
    EQUAL = "=="
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"
    IS_RISING = "is_rising"
    IS_FALLING = "is_falling"

@dataclass
class Condition:
    id: str                                    # cond_rsi_oversold
    name: str                                 # "RSI 과매도 진입"
    variable_a: str                           # indicator.rsi
    operator: Operator                        # <
    compare_target: Union[float, str]         # 30 또는 indicator.sma_20
    description: str                          # "RSI(14) 값이 30 미만인가?"
    
    # UI 관련
    ui_color: str = "#4CAF50"                # 조건 블록 색상
    ui_icon: str = "📊"                      # 조건 아이콘

# =============================================================================
# 계층 3: 액션 (Action) - "무엇을 할 것인가?"
# =============================================================================

class ActionType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    EXIT_ALL = "EXIT_ALL"

class QuantityRule(Enum):
    PERCENT_EQUITY = "PERCENT_EQUITY"        # 총자산 대비
    PERCENT_POSITION = "PERCENT_POSITION"    # 포지션 대비
    FIXED_AMOUNT = "FIXED_AMOUNT"           # 고정 금액
    FIXED_QUANTITY = "FIXED_QUANTITY"       # 고정 수량

@dataclass
class Action:
    id: str                                  # action_buy_full_equity
    name: str                               # "가용 현금 전량 매수"
    action_type: ActionType                 # BUY, SELL, EXIT_ALL
    quantity_rule: QuantityRule            # PERCENT_EQUITY
    quantity_parameter: float              # 1.0 (100%)
    description: str                       # "현재 가용 현금의 100%를 사용..."
    
    # UI 관련
    ui_color: str = "#2196F3"              # 액션 블록 색상
    ui_icon: str = "💰"                    # 액션 아이콘

# =============================================================================
# 계층 4: 규칙 (Rule) - "상황과 행동을 어떻게 묶을 것인가?"
# =============================================================================

class RuleRole(Enum):
    ENTRY = "ENTRY"                        # 진입
    EXIT = "EXIT"                          # 청산
    SCALE_IN = "SCALE_IN"                  # 추가 매수
    RISK_FILTER = "RISK_FILTER"           # 진입 필터

class LogicCombination(Enum):
    AND = "AND"
    OR = "OR"

@dataclass
class Rule:
    id: str                                # rule_oversold_entry
    name: str                             # "과매도 진입 규칙"
    role: RuleRole                        # ENTRY
    conditions: List[str]                 # ['cond_rsi_oversold', 'cond_bb_lower']
    logic_combination: LogicCombination   # AND
    action: str                           # action_buy_full_equity
    description: str                      # "만약 RSI가 과매도 상태이고..."
    
    # 우선순위 및 활성화 설정
    priority: int = 1                     # 규칙 우선순위 (낮을수록 높음)
    is_active: bool = True               # 규칙 활성화 여부

# =============================================================================
# 계층 5: 전략 (Strategy) - "규칙들을 어떻게 조합할 것인가?"
# =============================================================================

@dataclass
class Strategy:
    id: str                              # strat_mean_reversion_v1
    name: str                           # "평균 회귀 전략 v1.2"
    rules: List[str]                    # ['rule_oversold_entry', 'rule_take_profit']
    description: str                    # "과매도 구간에서 진입하여..."
    
    # 메타데이터
    created_at: str = ""                # 생성 시간
    version: str = "1.0"               # 전략 버전
    tags: List[str] = field(default_factory=list)  # ["역추세", "단기"]

# =============================================================================
# 기본 컴포넌트 라이브러리
# =============================================================================

class ComponentLibrary:
    """사전 정의된 컴포넌트들의 라이브러리"""
    
    @staticmethod
    def get_default_variables() -> List[Variable]:
        """기본 변수들 반환"""
        return [
            Variable(
                id="indicator.rsi",
                name="RSI 지표",
                category=VariableCategory.INDICATOR,
                parameters={"period": 14},
                return_type=ReturnType.SCALAR,
                description="상대강도지수 (0-100)",
                ui_widget_type="slider",
                ui_constraints={"min": 5, "max": 50, "step": 1},
                ui_help_text="RSI 계산 기간 (일반적으로 14일)",
                ui_icon="📈"
            ),
            Variable(
                id="indicator.bollinger_bands",
                name="볼린저 밴드",
                category=VariableCategory.INDICATOR,
                parameters={"period": 20, "std": 2},
                return_type=ReturnType.OBJECT,
                description="볼린저 밴드 (상단, 중간, 하단)",
                ui_widget_type="multi_slider",
                ui_constraints={
                    "period": {"min": 10, "max": 50, "step": 1},
                    "std": {"min": 1, "max": 3, "step": 0.1}
                },
                ui_help_text="기간과 표준편차 배수 설정",
                ui_icon="📊"
            ),
            Variable(
                id="price.close",
                name="현재가",
                category=VariableCategory.PRICE,
                parameters={},
                return_type=ReturnType.SCALAR,
                description="현재 종가",
                ui_widget_type="display",
                ui_help_text="실시간 종가",
                ui_icon="💰"
            ),
            Variable(
                id="state.profit_percent",
                name="현재 수익률(%)",
                category=VariableCategory.STATE,
                parameters={},
                return_type=ReturnType.SCALAR,
                description="현재 포지션의 수익률",
                ui_widget_type="display",
                ui_help_text="현재 보유 포지션의 수익률",
                ui_icon="📊"
            )
        ]
    
    @staticmethod
    def get_default_conditions() -> List[Condition]:
        """기본 조건들 반환"""
        return [
            Condition(
                id="cond_rsi_oversold",
                name="RSI 과매도",
                variable_a="indicator.rsi",
                operator=Operator.LESS,
                compare_target=30,
                description="RSI가 30 미만 (과매도 구간)",
                ui_color="#FF5722",
                ui_icon="📉"
            ),
            Condition(
                id="cond_rsi_overbought",
                name="RSI 과매수",
                variable_a="indicator.rsi",
                operator=Operator.GREATER,
                compare_target=70,
                description="RSI가 70 초과 (과매수 구간)",
                ui_color="#FF9800",
                ui_icon="📈"
            ),
            Condition(
                id="cond_price_below_bb_lower",
                name="가격 < 볼린저 하단",
                variable_a="price.close",
                operator=Operator.LESS,
                compare_target="indicator.bollinger_bands.lower",
                description="현재가가 볼린저밴드 하단 아래",
                ui_color="#9C27B0",
                ui_icon="⬇️"
            )
        ]
    
    @staticmethod
    def get_default_actions() -> List[Action]:
        """기본 액션들 반환"""
        return [
            Action(
                id="action_buy_all_cash",
                name="전량 매수",
                action_type=ActionType.BUY,
                quantity_rule=QuantityRule.PERCENT_EQUITY,
                quantity_parameter=1.0,
                description="가용 현금 100% 매수",
                ui_color="#4CAF50",
                ui_icon="💰"
            ),
            Action(
                id="action_sell_half",
                name="50% 매도",
                action_type=ActionType.SELL,
                quantity_rule=QuantityRule.PERCENT_POSITION,
                quantity_parameter=0.5,
                description="보유 포지션 50% 매도",
                ui_color="#FF5722",
                ui_icon="💸"
            ),
            Action(
                id="action_exit_all",
                name="전량 청산",
                action_type=ActionType.EXIT_ALL,
                quantity_rule=QuantityRule.PERCENT_POSITION,
                quantity_parameter=1.0,
                description="보유 포지션 전량 청산",
                ui_color="#F44336",
                ui_icon="🚫"
            )
        ]

# =============================================================================
# 전략 빌더 매니저
# =============================================================================

class StrategyBuilder:
    """전략 구성요소들을 조합하여 전략을 생성하는 매니저"""
    
    def __init__(self):
        self.variables = {v.id: v for v in ComponentLibrary.get_default_variables()}
        self.conditions = {c.id: c for c in ComponentLibrary.get_default_conditions()}
        self.actions = {a.id: a for a in ComponentLibrary.get_default_actions()}
        self.rules: Dict[str, Rule] = {}
        self.strategies: Dict[str, Strategy] = {}
    
    def create_custom_condition(self, variable_id: str, operator: Operator, 
                              target: Union[float, str], name: Optional[str] = None) -> str:
        """사용자 정의 조건 생성"""
        cond_id = f"cond_{variable_id.replace('.', '_')}_{operator.value}_{target}"
        
        variable_name = self.variables[variable_id].name
        if name is None:
            name = f"{variable_name} {operator.value} {target}"
        
        condition = Condition(
            id=cond_id,
            name=name,
            variable_a=variable_id,
            operator=operator,
            compare_target=target,
            description=f"{variable_name} {operator.value} {target}"
        )
        
        self.conditions[cond_id] = condition
        return cond_id
    
    def create_rule(self, name: str, role: RuleRole, condition_ids: List[str],
                   logic: LogicCombination, action_id: str) -> str:
        """규칙 생성"""
        rule_id = f"rule_{len(self.rules):04d}"
        
        rule = Rule(
            id=rule_id,
            name=name,
            role=role,
            conditions=condition_ids,
            logic_combination=logic,
            action=action_id,
            description=f"{name}: {logic.value} 조건으로 {action_id} 실행"
        )
        
        self.rules[rule_id] = rule
        return rule_id
    
    def create_strategy(self, name: str, rule_ids: List[str], 
                       description: str = "") -> str:
        """전략 생성"""
        strategy_id = f"strat_{len(self.strategies):04d}"
        
        strategy = Strategy(
            id=strategy_id,
            name=name,
            rules=rule_ids,
            description=description
        )
        
        self.strategies[strategy_id] = strategy
        return strategy_id
    
    def validate_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """전략 유효성 검증"""
        strategy = self.strategies[strategy_id]
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "has_entry": False,
            "has_exit": False
        }
        
        for rule_id in strategy.rules:
            rule = self.rules[rule_id]
            
            if rule.role == RuleRole.ENTRY:
                validation_result["has_entry"] = True
            elif rule.role == RuleRole.EXIT:
                validation_result["has_exit"] = True
        
        if not validation_result["has_entry"]:
            validation_result["errors"].append("진입 규칙이 없습니다")
            validation_result["is_valid"] = False
        
        if not validation_result["has_exit"]:
            validation_result["warnings"].append("청산 규칙이 없습니다")
        
        return validation_result

if __name__ == "__main__":
    # 테스트 코드
    builder = StrategyBuilder()
    
    # RSI 과매도 + 볼린저밴드 하단 돌파 조건 생성
    rsi_cond = "cond_rsi_oversold"
    bb_cond = "cond_price_below_bb_lower"
    
    # 진입 규칙 생성
    entry_rule = builder.create_rule(
        name="이중 과매도 진입",
        role=RuleRole.ENTRY,
        condition_ids=[rsi_cond, bb_cond],
        logic=LogicCombination.AND,
        action_id="action_buy_all_cash"
    )
    
    # 전략 생성
    strategy_id = builder.create_strategy(
        name="이중 과매도 전략",
        rule_ids=[entry_rule],
        description="RSI 과매도 + 볼린저밴드 하단 돌파 시 전량 매수"
    )
    
    # 검증
    validation = builder.validate_strategy(strategy_id)
    print(f"전략 검증 결과: {validation}")
