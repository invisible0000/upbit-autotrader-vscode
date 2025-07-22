"""
7개 핵심 규칙 템플릿 시스템
Core Strategy Rule Templates

기획 문서의 7개 핵심 규칙을 기존 컴포넌트 시스템의 조합으로 구현한 템플릿
사용자는 이 템플릿들을 기반으로 파라미터만 조정하여 전략을 구성할 수 있습니다.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from ..component_system import *

# 7개 핵심 규칙 템플릿 정의
CORE_STRATEGY_TEMPLATES = {
    "rsi_oversold_entry": {
        "name": "RSI 과매도 진입",
        "role": "ENTRY", 
        "description": "RSI 지표가 지정된 값 이하로 떨어지면 최초 진입합니다",
        "activation_state": "READY",
        "icon": "📈",
        "color": "#e74c3c",
        "components": {
            "trigger": {
                "type": "RSITrigger",
                "default_config": {
                    "period": 14,
                    "threshold": 20,
                    "direction": "below"
                },
                "config_schema": {
                    "period": {"type": "int", "min": 5, "max": 50, "label": "RSI 기간"},
                    "threshold": {"type": "int", "min": 10, "max": 40, "label": "과매도 임계값"},
                    "direction": {"type": "select", "options": ["below"], "label": "방향"}
                }
            },
            "conditions": [
                {
                    "type": "PositionStateCondition", 
                    "default_config": {"required_state": "READY"},
                    "config_schema": {
                        "required_state": {"type": "select", "options": ["READY"], "label": "필요 포지션 상태"}
                    }
                }
            ],
            "action": {
                "type": "BuyAction",
                "default_config": {
                    "amount_percent": 10,
                    "position_tag": "AUTO"
                },
                "config_schema": {
                    "amount_percent": {"type": "int", "min": 1, "max": 100, "label": "매수 비율(%)"},
                    "position_tag": {"type": "string", "default": "AUTO", "label": "포지션 태그"}
                }
            }
        }
    },
    
    "profit_scale_in": {
        "name": "수익 시 불타기",
        "role": "SCALE_IN",
        "description": "수익률이 지정된 값에 도달할 때마다 정해진 횟수만큼 추가 매수합니다",
        "activation_state": "ACTIVE", 
        "icon": "🔥",
        "color": "#f39c12",
        "components": {
            "trigger": {
                "type": "ProfitLossTrigger",
                "default_config": {
                    "profit_threshold": 5.0,
                    "direction": "above"
                },
                "config_schema": {
                    "profit_threshold": {"type": "float", "min": 1.0, "max": 20.0, "label": "수익률 임계값(%)"},
                    "direction": {"type": "select", "options": ["above"], "label": "방향"}
                }
            },
            "conditions": [
                {
                    "type": "ExecutionCountCondition",
                    "default_config": {
                        "target_rule_id": "profit_scale_in",
                        "less_than": 3
                    },
                    "config_schema": {
                        "target_rule_id": {"type": "string", "default": "profit_scale_in", "label": "대상 규칙 ID"},
                        "less_than": {"type": "int", "min": 1, "max": 10, "label": "최대 실행 횟수"}
                    }
                },
                {
                    "type": "ContextCondition",
                    "default_config": {
                        "check_flag": "is_pyramiding_paused",
                        "is_value": False
                    },
                    "config_schema": {
                        "check_flag": {"type": "string", "default": "is_pyramiding_paused", "label": "확인할 플래그"},
                        "is_value": {"type": "bool", "default": False, "label": "기대값"}
                    }
                }
            ],
            "action": {
                "type": "BuyAction",
                "default_config": {
                    "amount": 100000,
                    "position_tag": "AUTO"
                },
                "config_schema": {
                    "amount": {"type": "int", "min": 10000, "max": 1000000, "label": "추가 매수 금액"},
                    "position_tag": {"type": "string", "default": "AUTO", "label": "포지션 태그"}
                }
            }
        }
    },
    
    "planned_exit": {
        "name": "계획된 익절",
        "role": "EXIT",
        "description": "불타기가 계획된 횟수를 모두 채운 후, 다음 수익 신호에 전량 매도합니다",
        "activation_state": "ACTIVE",
        "icon": "💰", 
        "color": "#27ae60",
        "components": {
            "trigger": {
                "type": "ProfitLossTrigger",
                "default_config": {
                    "profit_threshold": 5.0,
                    "direction": "above"
                },
                "config_schema": {
                    "profit_threshold": {"type": "float", "min": 1.0, "max": 20.0, "label": "수익률 임계값(%)"},
                    "direction": {"type": "select", "options": ["above"], "label": "방향"}
                }
            },
            "conditions": [
                {
                    "type": "ExecutionCountCondition",
                    "default_config": {
                        "target_rule_id": "profit_scale_in", 
                        "equal_to": 3
                    },
                    "config_schema": {
                        "target_rule_id": {"type": "string", "default": "profit_scale_in", "label": "대상 규칙 ID"},
                        "equal_to": {"type": "int", "min": 1, "max": 10, "label": "필요 실행 횟수"}
                    }
                }
            ],
            "action": {
                "type": "SellAction",
                "default_config": {
                    "sell_type": "full_position"
                },
                "config_schema": {
                    "sell_type": {"type": "select", "options": ["full_position"], "label": "매도 유형"}
                }
            }
        }
    },
    
    "trailing_stop": {
        "name": "트레일링 스탑",
        "role": "EXIT",
        "description": "지정된 수익률 도달 후, 고점 대비 일정 비율 하락 시 전량 매도합니다",
        "activation_state": "ACTIVE",
        "icon": "📉",
        "color": "#e67e22",
        "components": {
            "trigger": {
                "type": "TrailingStopTrigger",
                "default_config": {
                    "activation_profit": 10.0,
                    "trailing_percent": 3.0
                },
                "config_schema": {
                    "activation_profit": {"type": "float", "min": 5.0, "max": 50.0, "label": "활성화 수익률(%)"},
                    "trailing_percent": {"type": "float", "min": 1.0, "max": 10.0, "label": "트레일링 비율(%)"}
                }
            },
            "conditions": [],
            "action": {
                "type": "SellAction",
                "default_config": {
                    "sell_type": "full_position"
                },
                "config_schema": {
                    "sell_type": {"type": "select", "options": ["full_position"], "label": "매도 유형"}
                }
            }
        }
    },
    
    "loss_averaging": {
        "name": "하락 시 물타기",
        "role": "SCALE_IN",
        "description": "평단가 대비 지정된 비율만큼 하락 시, 정해진 횟수만큼 추가 매수합니다",
        "activation_state": "ACTIVE",
        "icon": "⬇️",
        "color": "#9b59b6",
        "components": {
            "trigger": {
                "type": "PriceChangeTrigger", 
                "default_config": {
                    "price_change_percent": -5.0,
                    "reference": "average_price",
                    "direction": "below"
                },
                "config_schema": {
                    "price_change_percent": {"type": "float", "min": -20.0, "max": -1.0, "label": "하락률 임계값(%)"},
                    "reference": {"type": "select", "options": ["average_price"], "label": "기준 가격"},
                    "direction": {"type": "select", "options": ["below"], "label": "방향"}
                }
            },
            "conditions": [
                {
                    "type": "ExecutionCountCondition",
                    "default_config": {
                        "target_rule_id": "loss_averaging",
                        "less_than": 2
                    },
                    "config_schema": {
                        "target_rule_id": {"type": "string", "default": "loss_averaging", "label": "대상 규칙 ID"}, 
                        "less_than": {"type": "int", "min": 1, "max": 5, "label": "최대 실행 횟수"}
                    }
                }
            ],
            "action": {
                "type": "BuyAction",
                "default_config": {
                    "amount": 100000,
                    "position_tag": "AUTO"
                },
                "config_schema": {
                    "amount": {"type": "int", "min": 10000, "max": 1000000, "label": "추가 매수 금액"},
                    "position_tag": {"type": "string", "default": "AUTO", "label": "포지션 태그"}
                }
            }
        }
    },
    
    "crash_detection": {
        "name": "급락 감지",
        "role": "EMERGENCY_EXIT",
        "description": "단일 감시 주기 내에 가격이 폭락하면, 다른 모든 규칙을 무시하고 즉시 전량 매도합니다",
        "activation_state": "ACTIVE",
        "icon": "🚨",
        "color": "#c0392b",
        "priority": 0,  # 최고 우선순위
        "components": {
            "trigger": {
                "type": "RapidPriceDropTrigger",
                "default_config": {
                    "drop_threshold": -10.0,
                    "time_window_minutes": 5
                },
                "config_schema": {
                    "drop_threshold": {"type": "float", "min": -20.0, "max": -5.0, "label": "급락 임계값(%)"},
                    "time_window_minutes": {"type": "int", "min": 1, "max": 30, "label": "감시 시간(분)"}
                }
            },
            "conditions": [],
            "action": {
                "type": "SellAction",
                "default_config": {
                    "sell_type": "emergency_exit"
                },
                "config_schema": {
                    "sell_type": {"type": "select", "options": ["emergency_exit"], "label": "매도 유형"}
                }
            }
        }
    },
    
    "spike_hold": {
        "name": "급등 홀드",
        "role": "MANAGEMENT",
        "description": "단기간에 가격이 급등하면, 불타기 규칙을 일시 정지시켜 추격 매수의 위험을 막습니다",
        "activation_state": "ACTIVE",
        "icon": "🔒",
        "color": "#34495e",
        "priority": 1,  # 높은 우선순위
        "components": {
            "trigger": {
                "type": "RapidPriceSpikeTrigger",
                "default_config": {
                    "spike_threshold": 15.0,
                    "time_window_minutes": 5
                },
                "config_schema": {
                    "spike_threshold": {"type": "float", "min": 10.0, "max": 30.0, "label": "급등 임계값(%)"},
                    "time_window_minutes": {"type": "int", "min": 1, "max": 30, "label": "감시 시간(분)"}
                }
            },
            "conditions": [],
            "action": {
                "type": "ContextManagementAction",
                "default_config": {
                    "set_flag": "is_pyramiding_paused",
                    "value": True,
                    "duration_minutes": 30
                },
                "config_schema": {
                    "set_flag": {"type": "string", "default": "is_pyramiding_paused", "label": "설정할 플래그"},
                    "value": {"type": "bool", "default": True, "label": "설정값"},
                    "duration_minutes": {"type": "int", "min": 10, "max": 120, "label": "홀드 시간(분)"}
                }
            }
        }
    }
}


@dataclass
class ComponentTemplate:
    """컴포넌트 템플릿 정의"""
    type: str
    default_config: Dict[str, Any] 
    config_schema: Dict[str, Dict[str, Any]]


@dataclass  
class RuleTemplate:
    """규칙 템플릿 정의"""
    name: str
    role: str
    description: str
    activation_state: str
    icon: str
    color: str
    priority: int
    trigger: ComponentTemplate
    conditions: List[ComponentTemplate]
    action: ComponentTemplate
    
    @classmethod
    def from_dict(cls, template_id: str, data: Dict[str, Any]) -> 'RuleTemplate':
        """딕셔너리에서 RuleTemplate 생성"""
        components = data['components']
        
        # 트리거 템플릿 생성
        trigger_data = components['trigger']
        trigger = ComponentTemplate(
            type=trigger_data['type'],
            default_config=trigger_data['default_config'],
            config_schema=trigger_data['config_schema']
        )
        
        # 조건 템플릿들 생성
        conditions = []
        for cond_data in components.get('conditions', []):
            condition = ComponentTemplate(
                type=cond_data['type'],
                default_config=cond_data['default_config'],
                config_schema=cond_data['config_schema']
            )
            conditions.append(condition)
        
        # 액션 템플릿 생성
        action_data = components['action']
        action = ComponentTemplate(
            type=action_data['type'],
            default_config=action_data['default_config'],
            config_schema=action_data['config_schema']
        )
        
        return cls(
            name=data['name'],
            role=data['role'],
            description=data['description'], 
            activation_state=data['activation_state'],
            icon=data['icon'],
            color=data['color'],
            priority=data.get('priority', 10),
            trigger=trigger,
            conditions=conditions,
            action=action
        )


def get_rule_template(template_id: str) -> RuleTemplate:
    """규칙 템플릿 조회"""
    if template_id not in CORE_STRATEGY_TEMPLATES:
        raise ValueError(f"Unknown template: {template_id}")
    
    template_data = CORE_STRATEGY_TEMPLATES[template_id]
    return RuleTemplate.from_dict(template_id, template_data)


def list_rule_templates() -> Dict[str, Dict[str, Any]]:
    """모든 규칙 템플릿 목록 반환"""
    return {
        template_id: {
            'name': data['name'],
            'role': data['role'], 
            'description': data['description'],
            'icon': data['icon'],
            'color': data['color']
        }
        for template_id, data in CORE_STRATEGY_TEMPLATES.items()
    }


def create_strategy_rule_from_template(template_id: str, rule_id: str, custom_config: Dict[str, Any] = None) -> StrategyRule:
    """템플릿으로부터 실제 StrategyRule 생성"""
    template = get_rule_template(template_id)
    
    # 기본 설정에 사용자 커스텀 설정 적용
    trigger_config = template.trigger.default_config.copy()
    if custom_config and 'trigger' in custom_config:
        trigger_config.update(custom_config['trigger'])
    
    conditions_config = []
    for i, cond_template in enumerate(template.conditions):
        cond_config = cond_template.default_config.copy()
        if custom_config and 'conditions' in custom_config and i < len(custom_config['conditions']):
            cond_config.update(custom_config['conditions'][i])
        conditions_config.append(cond_config)
    
    action_config = template.action.default_config.copy()
    if custom_config and 'action' in custom_config:
        action_config.update(custom_config['action'])
    
    # StrategyRule 생성 (실제 컴포넌트 인스턴스 생성은 별도 팩토리에서)
    return StrategyRule(
        rule_id=rule_id,
        priority=template.priority,
        activation_state=template.activation_state,
        trigger_type=template.trigger.type,
        trigger_config=trigger_config,
        action_type=template.action.type,
        action_config=action_config,
        conditions=[
            {
                'type': template.conditions[i].type,
                'config': conditions_config[i]
            } for i in range(len(template.conditions))
        ]
    )
