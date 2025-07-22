#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
컴포넌트 시스템 기본 클래스들

모든 컴포넌트가 상속받아야 하는 기본 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# 순환 import 방지
if TYPE_CHECKING:
    from .position_management import PositionTag, PositionManager


class ComponentType(Enum):
    """컴포넌트 타입"""
    TRIGGER = "TRIGGER"
    ACTION = "ACTION"
    CONDITION = "CONDITION"
    CALCULATOR = "CALCULATOR"


@dataclass
class ComponentResult:
    """컴포넌트 실행 결과"""
    success: bool
    value: Any = None
    reason: str = ""
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExecutionContext:
    """
    실행 컨텍스트 - 전략 실행 상태 정보
    태그 기반 포지션 시스템과 연결됨
    """
    # 기본 정보
    symbol: str = ""
    strategy_id: str = ""
    position_tag: str = "AUTO"  # AUTO, MANUAL, HYBRID, LOCKED
    
    # 포지션 매니저 참조 (실제 구현에서는 dependency injection)
    position_manager: Optional[Any] = None
    
    # 레거시 호환성을 위한 속성들 (동적 계산)
    current_price: float = 0.0
    max_position_size: float = 1000000
    risk_per_trade: float = 0.02
    
    # 상태 정보
    last_signal_time: Optional[datetime] = None
    custom_variables: Optional[Dict[str, Any]] = None
    
    @property
    def has_position(self) -> bool:
        """포지션 보유 여부 (동적 계산)"""
        if not self.position_manager:
            return False
        from .position_management import PositionTag
        tag = PositionTag(self.position_tag)
        position = self.position_manager.get_position(self.symbol, tag)
        return position is not None and position.total_quantity > 0
    
    @property
    def position_size(self) -> float:
        """포지션 크기 (동적 계산)"""
        if not self.position_manager:
            return 0.0
        from .position_management import PositionTag
        tag = PositionTag(self.position_tag)
        position = self.position_manager.get_position(self.symbol, tag)
        return float(position.total_quantity) if position else 0.0
    
    @property
    def average_price(self) -> float:
        """평균 매수가 (동적 계산)"""
        if not self.position_manager:
            return 0.0
        from .position_management import PositionTag
        tag = PositionTag(self.position_tag)
        position = self.position_manager.get_position(self.symbol, tag)
        return float(position.average_price) if position else 0.0
    
    @property
    def entry_price(self) -> float:
        """최초 진입가 (첫 번째 매수가)"""
        if not self.position_manager:
            return 0.0
        from .position_management import PositionTag
        tag = PositionTag(self.position_tag)
        position = self.position_manager.get_position(self.symbol, tag)
        if position and position.entries:
            return float(position.entries[0].price)
        return 0.0
    
    @property
    def total_invested(self) -> float:
        """총 투자금액 (동적 계산)"""
        if not self.position_manager:
            return 0.0
        from .position_management import PositionTag
        tag = PositionTag(self.position_tag)
        position = self.position_manager.get_position(self.symbol, tag)
        return float(position.total_amount) if position else 0.0
    
    @property
    def add_buy_count(self) -> int:
        """추가 매수 횟수 (매수 기록 개수 - 1)"""
        if not self.position_manager:
            return 0
        from .position_management import PositionTag
        tag = PositionTag(self.position_tag)
        position = self.position_manager.get_position(self.symbol, tag)
        return len(position.entries) - 1 if position and position.entries else 0
    
    @property
    def entry_time(self) -> Optional[datetime]:
        """최초 진입 시간"""
        if not self.position_manager:
            return None
        from .position_management import PositionTag
        tag = PositionTag(self.position_tag)
        position = self.position_manager.get_position(self.symbol, tag)
        if position and position.entries:
            return position.entries[0].timestamp
        return None
    
    @property 
    def unrealized_pnl(self) -> float:
        """미실현 손익"""
        if not self.has_position or self.current_price <= 0:
            return 0.0
        return (self.current_price - self.average_price) * self.position_size
    
    @property
    def realized_pnl(self) -> float:
        """실현 손익 (단순화 - 실제로는 매도 기록 필요)"""
        return self.get_variable('realized_pnl', 0.0)
    
    def __post_init__(self):
        if self.custom_variables is None:
            self.custom_variables = {}
    
    def update_position(self, size: float, price: float, timestamp: Optional[datetime] = None):
        """포지션 정보 업데이트 (태그 기반 시스템에서는 position_manager 사용)"""
        if self.position_manager:
            from .position_management import PositionTag
            from decimal import Decimal
            
            tag = PositionTag(self.position_tag)
            success = self.position_manager.add_buy_entry(
                symbol=self.symbol,
                tag=tag,
                quantity=Decimal(str(size)),
                price=Decimal(str(price)),
                strategy_id=self.strategy_id,
                notes=f"자동매매 - {self.strategy_id}"
            )
            if not success:
                print(f"포지션 업데이트 실패: {self.symbol} {tag}")
    
    def close_position(self, price: float, timestamp: Optional[datetime] = None):
        """포지션 청산 (태그 기반 시스템에서는 position_manager 사용)"""
        if self.position_manager:
            from .position_management import PositionTag
            from decimal import Decimal
            
            tag = PositionTag(self.position_tag)
            
            # 실현 손익 계산
            if self.has_position:
                pnl = (price - self.average_price) * self.position_size
                current_realized_pnl = self.get_variable('realized_pnl', 0.0)
                self.set_variable('realized_pnl', current_realized_pnl + pnl)
            
            # 포지션 청산
            success = self.position_manager.close_position(
                symbol=self.symbol,
                tag=tag,
                sell_price=Decimal(str(price))
            )
            if not success:
                print(f"포지션 청산 실패: {self.symbol} {tag}")
    
    def add_buy_entry(self, quantity: float, price: float, timestamp: Optional[datetime] = None):
        """매수 엔트리 추가"""
        if self.position_manager:
            from .position_management import PositionTag
            from decimal import Decimal
            
            tag = PositionTag(self.position_tag)
            success = self.position_manager.add_buy_entry(
                symbol=self.symbol,
                tag=tag,
                quantity=Decimal(str(quantity)),
                price=Decimal(str(price)),
                strategy_id=self.strategy_id,
                notes=f"자동매매 - {self.strategy_id}"
            )
            
            if success:
                # add_buy_count 증가
                current_count = self.get_variable('add_buy_count', 0)
                self.set_variable('add_buy_count', current_count + 1)
            
            return success
        return False
    
    def partial_sell(self, quantity: float, price: float, timestamp: Optional[datetime] = None):
        """부분 매도"""
        if self.position_manager:
            from .position_management import PositionTag
            from decimal import Decimal
            
            tag = PositionTag(self.position_tag)
            
            # 실현 손익 계산
            profit = (price - self.average_price) * quantity
            current_realized_pnl = self.get_variable('realized_pnl', 0.0)
            self.set_variable('realized_pnl', current_realized_pnl + profit)
            
            # 부분 매도 실행 (실제로는 position_manager의 메서드 필요)
            # 임시로 직접 포지션 수정
            current_position = self.position_manager.get_position(self.symbol, tag)
            if current_position and current_position.total_quantity >= Decimal(str(quantity)):
                # 여기서는 단순화된 버전으로 처리
                return True
            
        return False
    
    def get_profit_loss_percent(self) -> float:
        """수익률 계산"""
        if not self.has_position or self.average_price == 0:
            return 0.0
        return (self.current_price - self.average_price) / self.average_price
    
    def get_position(self) -> Optional[Dict[str, Any]]:
        """현재 포지션 정보 반환"""
        if not self.has_position:
            return None
        
        return {
            'position_size': self.position_size,
            'entry_price': self.entry_price,
            'avg_buy_price': self.average_price,
            'current_price': self.current_price,
            'entry_time': self.entry_time,
            'add_buy_count': self.add_buy_count,
            'total_invested': self.total_invested,
            'unrealized_pnl': self.unrealized_pnl,
            'profit_loss_percent': self.get_profit_loss_percent()
        }
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """커스텀 변수 안전 조회"""
        if self.custom_variables is None:
            self.custom_variables = {}
        return self.custom_variables.get(key, default)
    
    def set_variable(self, key: str, value: Any):
        """커스텀 변수 안전 설정"""
        if self.custom_variables is None:
            self.custom_variables = {}
        self.custom_variables[key] = value


class ComponentBase(ABC):
    """모든 컴포넌트의 기본 클래스"""
    
    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        self.parameters = parameters or {}
        self.component_type = ComponentType.TRIGGER  # 하위 클래스에서 오버라이드
        self.component_id = self.__class__.__name__
        self.name = self.__class__.__name__
        self.enabled = True
        self.description = ""
    
    @abstractmethod
    def execute(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """컴포넌트 실행 - 하위 클래스에서 구현 필요"""
        pass
    
    def validate_parameters(self) -> bool:
        """파라미터 유효성 검증"""
        return True
    
    def get_required_parameters(self) -> list:
        """필수 파라미터 목록 반환"""
        return []
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """파라미터 값 가져오기"""
        return self.parameters.get(key, default)


class TriggerComponent(ComponentBase):
    """트리거 컴포넌트 기본 클래스"""
    
    def __init__(self, 
                 component_id: Optional[str] = None, 
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 parameters: Optional[Dict[str, Any]] = None):
        super().__init__(parameters)
        self.component_type = ComponentType.TRIGGER
        if component_id:
            self.component_id = component_id
        if name:
            self.name = name
        if description:
            self.description = description
    
    @abstractmethod
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """트리거 조건 평가"""
        pass
    
    def execute(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """TriggerComponent는 evaluate 메서드 사용"""
        return self.evaluate(market_data, context)


class ActionComponent(ComponentBase):
    """액션 컴포넌트 기본 클래스"""
    
    def __init__(self, 
                 component_id: Optional[str] = None, 
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 parameters: Optional[Dict[str, Any]] = None):
        super().__init__(parameters)
        self.component_type = ComponentType.ACTION
        if component_id:
            self.component_id = component_id
        if name:
            self.name = name
        if description:
            self.description = description
    
    @abstractmethod
    def execute(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """액션 실행"""
        pass


class ConditionComponent(ComponentBase):
    """조건 컴포넌트 기본 클래스"""
    
    def __init__(self, 
                 component_id: Optional[str] = None, 
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 parameters: Optional[Dict[str, Any]] = None):
        super().__init__(parameters)
        self.component_type = ComponentType.CONDITION
        if component_id:
            self.component_id = component_id
        if name:
            self.name = name
        if description:
            self.description = description
    
    @abstractmethod
    def check(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """조건 확인"""
        pass
    
    def execute(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """ConditionComponent는 check 메서드 사용"""
        return self.check(market_data, context)


class CalculatorComponent(ComponentBase):
    """계산 컴포넌트 기본 클래스"""
    
    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        super().__init__(parameters)
        self.component_type = ComponentType.CALCULATOR
    
    @abstractmethod
    def calculate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """값 계산"""
        pass
    
    def execute(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """CalculatorComponent는 calculate 메서드 사용"""
        return self.calculate(market_data, context)


@dataclass
class StrategyRule:
    """전략 규칙 - 트리거 + 조건들 + 액션의 조합"""
    rule_id: str
    description: str
    trigger: TriggerComponent
    conditions: Optional[List['ConditionComponent']] = None
    action: Optional[ActionComponent] = None
    enabled: bool = True
    priority: int = 0  # 우선순위 (낮을수록 먼저 실행)
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = []
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> bool:
        """규칙 평가"""
        if not self.enabled:
            return False
        
        # 1. 트리거 조건 확인
        trigger_result = self.trigger.evaluate(market_data, context)
        if not trigger_result.success:
            return False
        
        # 2. 추가 조건들 확인
        if self.conditions:
            for condition in self.conditions:
                condition_result = condition.check(market_data, context)
                if not condition_result.success:
                    return False
        
        return True
    
    def execute_action(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """액션 실행"""
        if self.action:
            return self.action.execute(market_data, context)
        else:
            return ComponentResult(success=False, reason="No action defined")
