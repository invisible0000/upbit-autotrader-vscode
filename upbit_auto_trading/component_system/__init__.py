"""
컴포넌트 기반 전략 시스템
Component-Based Strategy System

이 시스템은 기존의 고정된 전략 클래스 방식을 완전히 대체합니다.
사용자는 이제 레고 블록처럼 컴포넌트를 조합하여 무한한 전략 조합을 만들 수 있습니다.

주요 컴포넌트 타입:
- Triggers: 전략 실행의 시작점 (가격 변화, 지표 신호, 시간 기반 등)
- Actions: 실제 거래 행동 (매수, 매도, 포지션 관리 등)  
- Conditions: 추가 검증 조건 (리스크 관리, 잔고 확인 등)

예시 전략:
- 물타기(피라미딩): PriceChangeTrigger + AddBuyCountCondition + BuyAction
- RSI 역추세: RSITrigger + BalanceCondition + BuyAction
- 이동평균 교차: MovingAverageCrossTrigger + TimeCondition + SellAction
"""

# 기본 컴포넌트
from .base import (
    ComponentType,
    ComponentResult, 
    ExecutionContext,
    ComponentBase,
    TriggerComponent,
    ActionComponent, 
    ConditionComponent,
    StrategyRule
)

# 트리거 컴포넌트들
from .triggers.price_triggers import (
    PriceChangeTrigger, PriceChangeConfig,
    PriceBreakoutTrigger, PriceBreakoutConfig,
    PriceCrossoverTrigger, PriceCrossoverConfig
)

# 액션 컴포넌트들  
from .actions.trading_actions import (
    BuyAction, BuyActionConfig,
    SellAction, SellActionConfig,
    PositionManagementAction, PositionManagementConfig
)

# 조건 컴포넌트들
from .conditions.trading_conditions import (
    ProfitLossCondition, ProfitLossConditionConfig,
    PositionSizeCondition, PositionSizeConditionConfig,
    AddBuyCountCondition, AddBuyCountConditionConfig,
    TimeCondition, TimeConditionConfig,
    BalanceCondition, BalanceConditionConfig,
    TechnicalIndicatorCondition, TechnicalIndicatorConditionConfig
)

# 완성된 전략 예시
from .strategies.pyramiding_example import (
    PyramidingStrategy,
    create_simple_pyramiding_strategy,
    create_advanced_pyramiding_strategy
)

__version__ = "1.0.0"

# 컴포넌트 카탈로그 - UI에서 드래그앤드롭용
COMPONENT_CATALOG = {
    "triggers": {
        "price": [
            {
                "class": PriceChangeTrigger,
                "config_class": PriceChangeConfig,
                "name": "가격 변화 트리거",
                "description": "지정된 기준 가격에서 특정 % 변화 시 트리거",
                "use_cases": ["물타기", "손절매", "분할매수"],
                "icon": "📈"
            },
            {
                "class": PriceBreakoutTrigger,
                "config_class": PriceBreakoutConfig,
                "name": "가격 돌파 트리거", 
                "description": "지지선/저항선 돌파 시 트리거",
                "use_cases": ["브레이크아웃", "추세추종"],
                "icon": "🚀"
            },
            {
                "class": PriceCrossoverTrigger,
                "config_class": PriceCrossoverConfig,
                "name": "가격 교차 트리거",
                "description": "두 가격선의 교차 시 트리거",
                "use_cases": ["이동평균 교차", "황금십자", "데드크로스"],
                "icon": "✕"
            }
        ]
    },
    
    "actions": {
        "trading": [
            {
                "class": BuyAction,
                "config_class": BuyActionConfig,
                "name": "매수 액션",
                "description": "다양한 방식의 매수 실행",
                "use_cases": ["신규매수", "추가매수", "물타기"],
                "icon": "💰"
            },
            {
                "class": SellAction,
                "config_class": SellActionConfig,
                "name": "매도 액션",
                "description": "전체 또는 부분 매도 실행", 
                "use_cases": ["익절", "손절", "부분매도"],
                "icon": "💸"
            },
            {
                "class": PositionManagementAction,
                "config_class": PositionManagementConfig,
                "name": "포지션 관리 액션",
                "description": "손절가, 익절가 설정 및 리밸런싱",
                "use_cases": ["트레일링스탑", "리밸런싱"],
                "icon": "⚖️"
            }
        ]
    },
    
    "conditions": {
        "risk_management": [
            {
                "class": AddBuyCountCondition,
                "config_class": AddBuyCountConditionConfig,
                "name": "물타기 횟수 조건",
                "description": "추가 매수 횟수 제한",
                "use_cases": ["물타기 제한", "리스크 관리"],
                "icon": "🔢"
            },
            {
                "class": BalanceCondition,
                "config_class": BalanceConditionConfig,
                "name": "잔고 조건",
                "description": "사용 가능한 잔고 확인",
                "use_cases": ["매수 제한", "자금 관리"],
                "icon": "💳"
            },
            {
                "class": PositionSizeCondition,
                "config_class": PositionSizeConditionConfig,
                "name": "포지션 크기 조건",
                "description": "현재 포지션 크기 제한",
                "use_cases": ["최대투자금액", "포지션사이징"],
                "icon": "📏"
            }
        ],
        "profit_loss": [
            {
                "class": ProfitLossCondition,
                "config_class": ProfitLossConditionConfig,
                "name": "수익률 조건",
                "description": "현재 포지션의 수익률 확인",
                "use_cases": ["익절조건", "손절조건"],
                "icon": "📊"
            }
        ],
        "technical": [
            {
                "class": TechnicalIndicatorCondition,
                "config_class": TechnicalIndicatorConditionConfig,
                "name": "기술적 지표 조건",
                "description": "RSI, MACD 등 기술적 지표 확인",
                "use_cases": ["과매수/과매도", "추세확인"],
                "icon": "📉"
            }
        ],
        "timing": [
            {
                "class": TimeCondition,
                "config_class": TimeConditionConfig,
                "name": "시간 조건",
                "description": "시간 기반 조건 확인",
                "use_cases": ["장중시간", "홀딩시간", "쿨다운"],
                "icon": "⏰"
            }
        ]
    }
}

# 사전 정의된 전략 템플릿들
STRATEGY_TEMPLATES = {
    "pyramiding_simple": {
        "name": "간단 물타기 전략",
        "description": "3% 하락마다 추가매수, 최대 3회, 5% 익절",
        "factory": create_simple_pyramiding_strategy,
        "difficulty": "초급",
        "risk_level": "중간",
        "icon": "🔺"
    },
    "pyramiding_advanced": {
        "name": "고급 물타기 전략", 
        "description": "2.5% 하락마다 추가매수, 최대 5회, 7% 익절",
        "factory": create_advanced_pyramiding_strategy,
        "difficulty": "고급",
        "risk_level": "높음",
        "icon": "🔺🔺"
    }
}


def get_component_by_type(component_type: str) -> list:
    """타입별 컴포넌트 목록 조회"""
    return COMPONENT_CATALOG.get(component_type, {})


def get_all_triggers() -> list:
    """모든 트리거 컴포넌트 조회"""
    triggers = []
    for category in COMPONENT_CATALOG.get("triggers", {}).values():
        triggers.extend(category)
    return triggers


def get_all_actions() -> list:
    """모든 액션 컴포넌트 조회"""
    actions = []
    for category in COMPONENT_CATALOG.get("actions", {}).values():
        actions.extend(category)
    return actions


def get_all_conditions() -> list:
    """모든 조건 컴포넌트 조회"""
    conditions = []
    for category in COMPONENT_CATALOG.get("conditions", {}).values():
        conditions.extend(category)
    return conditions


def create_strategy_from_template(template_name: str, **kwargs):
    """템플릿에서 전략 생성"""
    template = STRATEGY_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"알 수 없는 템플릿: {template_name}")
    
    factory = template["factory"]
    return factory(**kwargs)


__all__ = [
    # 기본 클래스들
    'ComponentType', 'ComponentResult', 'ExecutionContext',
    'ComponentBase', 'TriggerComponent', 'ActionComponent', 'ConditionComponent',
    'StrategyRule',
    
    # 트리거들
    'PriceChangeTrigger', 'PriceChangeConfig',
    'PriceBreakoutTrigger', 'PriceBreakoutConfig', 
    'PriceCrossoverTrigger', 'PriceCrossoverConfig',
    
    # 액션들
    'BuyAction', 'BuyActionConfig',
    'SellAction', 'SellActionConfig',
    'PositionManagementAction', 'PositionManagementConfig',
    
    # 조건들
    'ProfitLossCondition', 'ProfitLossConditionConfig',
    'PositionSizeCondition', 'PositionSizeConditionConfig',
    'AddBuyCountCondition', 'AddBuyCountConditionConfig',
    'TimeCondition', 'TimeConditionConfig',
    'BalanceCondition', 'BalanceConditionConfig',
    'TechnicalIndicatorCondition', 'TechnicalIndicatorConditionConfig',
    
    # 전략 예시들
    'PyramidingStrategy',
    'create_simple_pyramiding_strategy',
    'create_advanced_pyramiding_strategy',
    
    # 유틸리티 함수들
    'get_component_by_type',
    'get_all_triggers',
    'get_all_actions', 
    'get_all_conditions',
    'create_strategy_from_template',
    
    # 상수들
    'COMPONENT_CATALOG',
    'STRATEGY_TEMPLATES'
]
