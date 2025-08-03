#!/usr/bin/env python3
"""
전략 팩토리 (Strategy Factory) - 도메인 엔티티
==============================================

전략 생성을 위한 팩토리 클래스
- 기본 7규칙 전략 생성
- 사전 정의된 전략 템플릿 제공
- 복잡한 전략 조합 자동화

Design Principles:
- Factory Pattern: 복잡한 전략 생성 로직 캡슐화
- Template Method: 전략 생성 단계 표준화
- Builder Pattern: 단계별 전략 구성 지원
"""

from typing import Dict, Any, List

from .strategy import Strategy
from .management_rule import (
    create_pyramid_buying_rule, 
    create_scale_in_buying_rule, 
    create_trailing_stop_rule, 
    create_fixed_stop_take_rule
)
from ..value_objects.strategy_id import StrategyId
from ..value_objects.strategy_config import StrategyConfig


class StrategyFactory:
    """
    전략 생성을 위한 팩토리 클래스
    
    복잡한 전략 조합을 쉽게 생성할 수 있도록 도와주는 팩토리.
    기본 7규칙 전략을 포함한 다양한 전략 템플릿 제공.
    """
    
    @staticmethod
    def create_basic_7_rule_strategy() -> Strategy:
        """
        기본 7규칙 전략 생성
        
        실제 구현된 엔티티 구조에 맞춰 단순화된 전략 생성:
        - Strategy 엔티티 기본 구조 활용
        - 기존 Value Objects 적극 활용
        - ManagementRule 팩토리 함수 활용
        
        Returns:
            Strategy: 완전히 구성된 기본 7규칙 전략
        """
        # 1. StrategyId Value Object 활용
        strategy_id = StrategyId("BASIC_7_RULE_001")
        
        # 2. StrategyConfig Value Object 활용
        strategy_config = StrategyConfig(
            config_id="basic_7_rule_config",
            strategy_definition_id="basic_7_rule_entry_strategy",
            strategy_name="기본 7규칙 전략",
            parameters={
                "description": "RSI 과매도 진입 + 불타기/물타기 + 트레일링 스탑",
                "risk_level": 3,
                "expected_return": 15.0,
                "max_drawdown": 12.0,
                "rules": [
                    "RSI 과매도 진입 (RSI < 30)",
                    "수익 시 불타기 (3% 수익마다 추가 매수, 최대 3회)",
                    "계획된 익절 (목표 수익률 20% 달성 시)",
                    "트레일링 스탑 (5% 후행, 2% 활성화)",
                    "하락 시 물타기 (5% 하락마다 추가 매수, 최대 5회)",
                    "급락 감지 (절대 손절 15%)",
                    "급등 감지 (불타기 중단을 위한 수익 보호)"
                ]
            }
        )        # 3. Strategy 엔티티 생성 (기존 구조 활용)
        strategy = Strategy(
            strategy_id=strategy_id,
            name="기본 7규칙 전략",
            description="RSI 과매도 진입 + 불타기/물타기 + 트레일링 스탑",
            entry_strategy_config=strategy_config
        )
        
        # 4. 관리 규칙들 생성 (테스트용으로 변수에 저장만)
        
        # 규칙 2: 수익 시 불타기 (Scale-in Buying)
        _ = create_scale_in_buying_rule(
            rule_id="basic_scale_in_rule",
            trigger_profit_rate=3.0,               # 3% 수익마다
            max_additions=3,                       # 최대 3회
            profit_target=20.0                     # 목표 20%
        )
        
        # 규칙 4: 트레일링 스탑
        _ = create_trailing_stop_rule(
            rule_id="basic_trailing_stop_rule",
            trail_distance=5.0,                    # 5% 후행 거리
            activation_profit=2.0                  # 2% 수익 시 활성화
        )
        
        # 규칙 5: 하락 시 물타기 (Pyramid Buying)
        _ = create_pyramid_buying_rule(
            rule_id="basic_pyramid_rule",
            trigger_drop_rate=5.0,                 # 5% 하락마다
            max_additions=5,                       # 최대 5회
            absolute_stop_loss=15.0                # 절대 손절 15%
        )
        
        # 규칙 6,7: 고정 손절/익절 (추가 안전장치)
        _ = create_fixed_stop_take_rule(
            rule_id="basic_fixed_stop_rule",
            stop_loss_rate=8.0,                    # 8% 손절
            take_profit_rate=25.0                  # 25% 익절 (보조)
        )
        
        return strategy
    
    @staticmethod
    def create_conservative_strategy() -> Strategy:
        """
        보수적 전략 생성
        
        - 안정적인 고정 손절/익절만 사용
        - 물타기/불타기 없음
        """
        strategy_id = StrategyId("CONSERVATIVE_001")
        strategy_config = StrategyConfig(
            config_id="conservative_config",
            strategy_definition_id="conservative_entry_strategy",
            strategy_name="보수적 전략",
            parameters={
                "description": "안정적인 고정 손절/익절 전략",
                "risk_level": 1,
                "expected_return": 8.0,
                "max_drawdown": 5.0
            }
        )
        
        strategy = Strategy(
            strategy_id=strategy_id,
            name="보수적 전략",
            description="안정적인 고정 손절/익절 전략",
            entry_strategy_config=strategy_config
        )
        
        # 보수적 고정 손절/익절
        _ = create_fixed_stop_take_rule(
            rule_id="conservative_stop_rule",
            stop_loss_rate=3.0,                    # 3% 손절
            take_profit_rate=8.0                   # 8% 익절
        )
        
        return strategy
    
    @staticmethod
    def create_aggressive_strategy() -> Strategy:
        """
        공격적 전략 생성
        
        - 적극적 불타기/물타기
        - 높은 목표 수익률
        """
        strategy_id = StrategyId("AGGRESSIVE_001")
        strategy_config = StrategyConfig(
            config_id="aggressive_config",
            strategy_definition_id="aggressive_entry_strategy",
            strategy_name="공격적 전략",
            parameters={
                "description": "높은 수익률을 추구하는 공격적 전략",
                "risk_level": 5,
                "expected_return": 25.0,
                "max_drawdown": 20.0
            }
        )
        
        strategy = Strategy(
            strategy_id=strategy_id,
            name="공격적 전략",
            description="높은 수익률을 추구하는 공격적 전략",
            entry_strategy_config=strategy_config
        )
        
        # 적극적 불타기
        _ = create_scale_in_buying_rule(
            rule_id="aggressive_scale_in_rule",
            trigger_profit_rate=2.0,               # 2% 수익마다
            max_additions=5,                       # 최대 5회
            profit_target=30.0                     # 목표 30%
        )
        
        # 적극적 물타기
        _ = create_pyramid_buying_rule(
            rule_id="aggressive_pyramid_rule",
            trigger_drop_rate=3.0,                 # 3% 하락마다
            max_additions=8,                       # 최대 8회
            absolute_stop_loss=25.0                # 절대 손절 25%
        )
        
        # 트레일링 스탑 (더 넓은 후행 거리)
        _ = create_trailing_stop_rule(
            rule_id="aggressive_trailing_rule",
            trail_distance=8.0,                    # 8% 후행 거리
            activation_profit=5.0                  # 5% 수익 시 활성화
        )
        
        return strategy
    
    @staticmethod
    def create_scalping_strategy() -> Strategy:
        """
        스캘핑 전략 생성
        
        - 빠른 진입/청산
        - 작은 수익률 목표
        """
        strategy_id = StrategyId("SCALPING_001")
        strategy_config = StrategyConfig(
            config_id="scalping_config",
            strategy_definition_id="scalping_entry_strategy",
            strategy_name="스캘핑 전략",
            parameters={
                "description": "빠른 매매를 통한 소액 수익 추구",
                "risk_level": 2,
                "expected_return": 5.0,
                "max_drawdown": 3.0
            }
        )
        
        strategy = Strategy(
            strategy_id=strategy_id,
            name="스캘핑 전략",
            description="빠른 매매를 통한 소액 수익 추구",
            entry_strategy_config=strategy_config
        )
        
        # 빠른 고정 손절/익절
        _ = create_fixed_stop_take_rule(
            rule_id="scalping_stop_rule",
            stop_loss_rate=2.0,                    # 2% 손절
            take_profit_rate=3.0                   # 3% 익절
        )
        
        return strategy
    
    @staticmethod
    def get_available_strategies() -> List[Dict[str, Any]]:
        """
        사용 가능한 전략 템플릿 목록 반환
        
        Returns:
            List[Dict]: 전략 템플릿 정보 목록
        """
        return [
            {
                "id": "BASIC_7_RULE_001",
                "name": "기본 7규칙 전략",
                "description": "RSI 과매도 진입 + 불타기/물타기 + 트레일링 스탑",
                "risk_level": 3,
                "expected_return": 15.0,
                "factory_method": "create_basic_7_rule_strategy"
            },
            {
                "id": "CONSERVATIVE_001",
                "name": "보수적 전략",
                "description": "안정적인 고정 손절/익절 전략",
                "risk_level": 1,
                "expected_return": 8.0,
                "factory_method": "create_conservative_strategy"
            },
            {
                "id": "AGGRESSIVE_001",
                "name": "공격적 전략",
                "description": "높은 수익률을 추구하는 공격적 전략",
                "risk_level": 5,
                "expected_return": 25.0,
                "factory_method": "create_aggressive_strategy"
            },
            {
                "id": "SCALPING_001",
                "name": "스캘핑 전략",
                "description": "빠른 매매를 통한 소액 수익 추구",
                "risk_level": 2,
                "expected_return": 5.0,
                "factory_method": "create_scalping_strategy"
            }
        ]


# 팩토리 함수들 (편의 함수)
def create_basic_7_rule_strategy() -> Strategy:
    """기본 7규칙 전략 생성 (편의 함수)"""
    return StrategyFactory.create_basic_7_rule_strategy()


def create_conservative_strategy() -> Strategy:
    """보수적 전략 생성 (편의 함수)"""
    return StrategyFactory.create_conservative_strategy()


def create_aggressive_strategy() -> Strategy:
    """공격적 전략 생성 (편의 함수)"""
    return StrategyFactory.create_aggressive_strategy()


def create_scalping_strategy() -> Strategy:
    """스캘핑 전략 생성 (편의 함수)"""
    return StrategyFactory.create_scalping_strategy()
