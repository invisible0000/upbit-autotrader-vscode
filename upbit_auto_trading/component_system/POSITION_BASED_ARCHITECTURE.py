"""
포지션 기반 전략 관리 시스템 설계
Position-Based Strategy Management System Design

현재 컴포넌트 시스템의 문제점과 해결방안
===============================================

문제점 1: 전략 vs 포지션 관리
- 현재: 전략이 포지션을 소유하는 구조
- 문제: 하나의 코인에 여러 전략이 동시에 적용될 때 충돌
- 해결: 포지션이 전략들을 관리하는 구조로 전환

문제점 2: 수동 개입 시 기준가 문제  
- 현재: 초기 구매가만 기준으로 사용
- 문제: 수동 매수/매도 후 평단가 변경 시 전략 로직 오작동
- 해결: 동적 기준가 계산 시스템 도입

문제점 3: 다중 포지션 관리
- 현재: 하나의 코인에 하나의 포지션만 가정
- 문제: 서로 다른 자본 규모의 독립적 포지션 관리 불가
- 해결: 포지션 그룹(Portfolio) 개념 도입

새로운 아키텍처 제안
===================

1. PositionManager (포지션 관리자)
   - 하나의 코인에 대한 모든 포지션들을 관리
   - 전략들을 포지션에 연결/해제
   - 수동 개입 시 자동으로 기준가 재계산

2. Position (개별 포지션)
   - 독립적인 자본과 전략을 가짐
   - 자체적인 ExecutionContext 보유
   - 전략 컴포넌트들을 동적으로 추가/제거 가능

3. ReferencePrice (기준가 시스템)
   - 포지션 상태에 따라 동적으로 기준가 계산
   - 수동 개입 감지 및 자동 조정
   - 여러 기준가 타입 지원 (초기가, 평단가, 최고가, 최저가 등)

4. PortfolioManager (포트폴리오 관리자)
   - 여러 코인의 PositionManager들을 통합 관리
   - 전체 자본 배분 및 리스크 관리
   - 포지션 간 상호작용 제어
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from decimal import Decimal
import uuid

from ..base import ExecutionContext, StrategyRule, ComponentResult


class PositionStatus(Enum):
    """포지션 상태"""
    EMPTY = "empty"           # 포지션 없음
    ACTIVE = "active"         # 활성 포지션
    PARTIAL = "partial"       # 부분 매도 상태
    CLOSED = "closed"         # 청산 완료
    SUSPENDED = "suspended"   # 일시 중단


class ReferenceType(Enum):
    """기준가 타입"""
    INITIAL_PRICE = "initial_price"       # 최초 매수가
    AVERAGE_PRICE = "average_price"       # 평균 매수가 (평단가)
    LAST_BUY_PRICE = "last_buy_price"     # 마지막 매수가
    HIGHEST_PRICE = "highest_price"       # 보유 중 최고가
    LOWEST_PRICE = "lowest_price"         # 보유 중 최저가
    MANUAL_PRICE = "manual_price"         # 수동 설정 가격


@dataclass
class ReferencePrice:
    """동적 기준가 시스템"""
    reference_type: ReferenceType
    base_price: Decimal
    last_updated: datetime
    auto_update: bool = True
    manual_override: Optional[Decimal] = None
    
    def get_current_reference(self, position_data: Dict[str, Any]) -> Decimal:
        """현재 기준가 반환"""
        if self.manual_override:
            return self.manual_override
            
        if self.reference_type == ReferenceType.INITIAL_PRICE:
            return Decimal(str(position_data.get('initial_price', self.base_price)))
            
        elif self.reference_type == ReferenceType.AVERAGE_PRICE:
            return Decimal(str(position_data.get('average_price', self.base_price)))
            
        elif self.reference_type == ReferenceType.LAST_BUY_PRICE:
            return Decimal(str(position_data.get('last_buy_price', self.base_price)))
            
        elif self.reference_type == ReferenceType.HIGHEST_PRICE:
            return Decimal(str(position_data.get('highest_price', self.base_price)))
            
        elif self.reference_type == ReferenceType.LOWEST_PRICE:
            return Decimal(str(position_data.get('lowest_price', self.base_price)))
            
        return self.base_price
    
    def update_reference(self, new_price: Decimal, update_type: str = "auto"):
        """기준가 업데이트"""
        if not self.auto_update and update_type == "auto":
            return
            
        if update_type == "manual":
            self.manual_override = new_price
        else:
            self.base_price = new_price
            
        self.last_updated = datetime.now()


@dataclass
class Position:
    """개별 포지션 - 독립적인 자본과 전략을 가짐"""
    position_id: str
    symbol: str
    name: str
    
    # 포지션 기본 정보
    status: PositionStatus = PositionStatus.EMPTY
    allocated_capital: Decimal = Decimal('0')  # 할당된 자본
    available_balance: Decimal = Decimal('0')  # 사용 가능한 잔고
    
    # 보유 정보
    quantity: Decimal = Decimal('0')
    initial_price: Optional[Decimal] = None    # 최초 매수가
    average_price: Optional[Decimal] = None    # 평균 매수가
    last_buy_price: Optional[Decimal] = None   # 마지막 매수가
    highest_price: Optional[Decimal] = None    # 보유 중 최고가
    lowest_price: Optional[Decimal] = None     # 보유 중 최저가
    
    # 거래 기록
    buy_count: int = 0
    sell_count: int = 0
    total_invested: Decimal = Decimal('0')
    realized_pnl: Decimal = Decimal('0')
    
    # 시간 정보
    created_at: datetime = field(default_factory=datetime.now)
    first_buy_at: Optional[datetime] = None
    last_trade_at: Optional[datetime] = None
    
    # 기준가 시스템
    reference_prices: Dict[str, ReferencePrice] = field(default_factory=dict)
    
    # 전략 관리
    active_strategies: List[StrategyRule] = field(default_factory=list)
    execution_context: Optional[ExecutionContext] = None
    
    # 메타데이터
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    auto_trade: bool = True
    
    def __post_init__(self):
        """초기화 후 처리"""
        if not self.execution_context:
            self.execution_context = ExecutionContext(
                symbol=self.symbol,
                max_position_size=float(self.allocated_capital)
            )
            self.execution_context.set_variable('allocated_capital', float(self.allocated_capital))
            self.execution_context.set_variable('available_balance', float(self.available_balance))
    
    def add_strategy(self, strategy_rule: StrategyRule) -> bool:
        """전략 추가"""
        # 중복 확인
        for existing_rule in self.active_strategies:
            if existing_rule.rule_id == strategy_rule.rule_id:
                return False
        
        self.active_strategies.append(strategy_rule)
        return True
    
    def remove_strategy(self, rule_id: str) -> bool:
        """전략 제거"""
        for i, rule in enumerate(self.active_strategies):
            if rule.rule_id == rule_id:
                del self.active_strategies[i]
                return True
        return False
    
    def execute_buy(self, quantity: Decimal, price: Decimal, trade_type: str = "auto") -> ComponentResult:
        """매수 실행"""
        try:
            cost = quantity * price
            
            # 잔고 확인
            if cost > self.available_balance:
                return ComponentResult(False, f"잔고 부족: 필요 {cost}, 보유 {self.available_balance}")
            
            # 첫 매수인지 확인
            is_first_buy = self.quantity == 0
            
            if is_first_buy:
                # 첫 매수
                self.initial_price = price
                self.average_price = price
                self.highest_price = price
                self.lowest_price = price
                self.first_buy_at = datetime.now()
                self.status = PositionStatus.ACTIVE
            else:
                # 추가 매수 - 평단가 계산
                old_total_cost = self.quantity * self.average_price
                new_total_cost = old_total_cost + cost
                new_total_quantity = self.quantity + quantity
                self.average_price = new_total_cost / new_total_quantity
                
                # 최고가/최저가 업데이트
                if price > self.highest_price:
                    self.highest_price = price
                if price < self.lowest_price:
                    self.lowest_price = price
            
            # 포지션 업데이트
            self.quantity += quantity
            self.last_buy_price = price
            self.buy_count += 1
            self.total_invested += cost
            self.available_balance -= cost
            self.last_trade_at = datetime.now()
            
            # ExecutionContext 동기화
            self._sync_execution_context()
            
            # 기준가 업데이트
            self._update_reference_prices("buy", price)
            
            return ComponentResult(
                True,
                f"매수 완료: {quantity} @ {price} ({trade_type})",
                metadata={
                    'trade_type': trade_type,
                    'quantity': float(quantity),
                    'price': float(price),
                    'cost': float(cost),
                    'new_average_price': float(self.average_price),
                    'new_quantity': float(self.quantity)
                }
            )
            
        except Exception as e:
            return ComponentResult(False, f"매수 실행 오류: {str(e)}")
    
    def execute_sell(self, quantity: Decimal, price: Decimal, trade_type: str = "auto") -> ComponentResult:
        """매도 실행"""
        try:
            if quantity > self.quantity:
                return ComponentResult(False, f"매도 수량 초과: 요청 {quantity}, 보유 {self.quantity}")
            
            proceeds = quantity * price
            cost_basis = quantity * self.average_price
            profit = proceeds - cost_basis
            
            # 포지션 업데이트
            self.quantity -= quantity
            self.sell_count += 1
            self.realized_pnl += profit
            self.available_balance += proceeds
            self.last_trade_at = datetime.now()
            
            # 전체 청산 여부 확인
            if self.quantity == 0:
                self.status = PositionStatus.CLOSED
            elif self.quantity < self.total_invested / self.average_price * Decimal('0.1'):
                self.status = PositionStatus.PARTIAL
            
            # ExecutionContext 동기화
            self._sync_execution_context()
            
            # 기준가 업데이트
            self._update_reference_prices("sell", price)
            
            return ComponentResult(
                True,
                f"매도 완료: {quantity} @ {price} ({trade_type})",
                metadata={
                    'trade_type': trade_type,
                    'quantity': float(quantity),
                    'price': float(price),
                    'proceeds': float(proceeds),
                    'profit': float(profit),
                    'remaining_quantity': float(self.quantity)
                }
            )
            
        except Exception as e:
            return ComponentResult(False, f"매도 실행 오류: {str(e)}")
    
    def manual_intervention(self, action: str, quantity: Decimal, price: Decimal, notes: str = "") -> ComponentResult:
        """수동 개입 처리"""
        self.notes += f"\n[{datetime.now()}] 수동 {action}: {notes}"
        
        if action == "buy":
            result = self.execute_buy(quantity, price, "manual")
        elif action == "sell":
            result = self.execute_sell(quantity, price, "manual")
        else:
            return ComponentResult(False, f"알 수 없는 액션: {action}")
        
        if result.success:
            # 수동 개입 후 기준가 재계산
            self._recalculate_reference_prices_after_manual_intervention()
        
        return result
    
    def set_reference_price(self, name: str, reference_type: ReferenceType, price: Optional[Decimal] = None):
        """기준가 설정"""
        if price is None:
            if reference_type == ReferenceType.AVERAGE_PRICE:
                price = self.average_price or Decimal('0')
            elif reference_type == ReferenceType.INITIAL_PRICE:
                price = self.initial_price or Decimal('0')
            else:
                price = Decimal('0')
        
        self.reference_prices[name] = ReferencePrice(
            reference_type=reference_type,
            base_price=price,
            last_updated=datetime.now()
        )
    
    def get_reference_price(self, name: str) -> Optional[Decimal]:
        """기준가 조회"""
        ref_price = self.reference_prices.get(name)
        if not ref_price:
            return None
        
        position_data = {
            'initial_price': self.initial_price,
            'average_price': self.average_price,
            'last_buy_price': self.last_buy_price,
            'highest_price': self.highest_price,
            'lowest_price': self.lowest_price
        }
        
        return ref_price.get_current_reference(position_data)
    
    def _sync_execution_context(self):
        """ExecutionContext와 동기화"""
        if not self.execution_context:
            return
        
        self.execution_context.has_position = self.quantity > 0
        self.execution_context.position_size = float(self.quantity)
        self.execution_context.entry_price = float(self.initial_price or 0)
        self.execution_context.average_price = float(self.average_price or 0)
        self.execution_context.entry_time = self.first_buy_at
        self.execution_context.add_buy_count = self.buy_count - 1  # 첫 매수 제외
        self.execution_context.total_invested = float(self.total_invested)
        self.execution_context.realized_pnl = float(self.realized_pnl)
        self.execution_context.set_variable('available_balance', float(self.available_balance))
    
    def _update_reference_prices(self, action: str, price: Decimal):
        """거래 후 기준가 업데이트"""
        for ref_price in self.reference_prices.values():
            if action == "buy" and ref_price.reference_type == ReferenceType.AVERAGE_PRICE:
                ref_price.update_reference(self.average_price)
            elif action == "buy" and ref_price.reference_type == ReferenceType.LAST_BUY_PRICE:
                ref_price.update_reference(price)
    
    def _recalculate_reference_prices_after_manual_intervention(self):
        """수동 개입 후 기준가 재계산"""
        # 모든 기준가를 현재 포지션 상태에 맞게 재계산
        for name, ref_price in self.reference_prices.items():
            if ref_price.reference_type == ReferenceType.AVERAGE_PRICE:
                ref_price.update_reference(self.average_price, "manual")
            elif ref_price.reference_type == ReferenceType.INITIAL_PRICE:
                # 초기가는 수동 개입 시에도 유지
                pass
    
    def get_position_summary(self) -> Dict[str, Any]:
        """포지션 요약 정보"""
        return {
            'position_id': self.position_id,
            'symbol': self.symbol,
            'name': self.name,
            'status': self.status.value,
            'quantity': float(self.quantity),
            'average_price': float(self.average_price or 0),
            'total_invested': float(self.total_invested),
            'available_balance': float(self.available_balance),
            'buy_count': self.buy_count,
            'sell_count': self.sell_count,
            'realized_pnl': float(self.realized_pnl),
            'active_strategies': len(self.active_strategies),
            'reference_prices': {name: float(self.get_reference_price(name) or 0) 
                               for name in self.reference_prices.keys()}
        }


class PositionManager:
    """포지션 관리자 - 하나의 코인에 대한 모든 포지션들을 관리"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.positions: Dict[str, Position] = {}
        self.active_position_ids: List[str] = []
        self.created_at = datetime.now()
    
    def create_position(self, 
                       name: str, 
                       allocated_capital: float,
                       position_id: Optional[str] = None) -> str:
        """새 포지션 생성"""
        if position_id is None:
            position_id = f"{self.symbol}_{len(self.positions) + 1}_{uuid.uuid4().hex[:8]}"
        
        position = Position(
            position_id=position_id,
            symbol=self.symbol,
            name=name,
            allocated_capital=Decimal(str(allocated_capital)),
            available_balance=Decimal(str(allocated_capital))
        )
        
        # 기본 기준가 설정
        position.set_reference_price("purchase_price", ReferenceType.AVERAGE_PRICE)
        position.set_reference_price("initial_price", ReferenceType.INITIAL_PRICE)
        
        self.positions[position_id] = position
        self.active_position_ids.append(position_id)
        
        return position_id
    
    def get_position(self, position_id: str) -> Optional[Position]:
        """포지션 조회"""
        return self.positions.get(position_id)
    
    def execute_trade_on_position(self, 
                                position_id: str, 
                                action: str, 
                                quantity: float, 
                                price: float,
                                trade_type: str = "auto") -> ComponentResult:
        """특정 포지션에서 거래 실행"""
        position = self.get_position(position_id)
        if not position:
            return ComponentResult(False, f"포지션을 찾을 수 없음: {position_id}")
        
        quantity_decimal = Decimal(str(quantity))
        price_decimal = Decimal(str(price))
        
        if action == "buy":
            return position.execute_buy(quantity_decimal, price_decimal, trade_type)
        elif action == "sell":
            return position.execute_sell(quantity_decimal, price_decimal, trade_type)
        else:
            return ComponentResult(False, f"알 수 없는 거래 액션: {action}")
    
    def execute_strategies_on_position(self, 
                                     position_id: str, 
                                     market_data: Dict[str, Any]) -> List[ComponentResult]:
        """특정 포지션의 전략들 실행"""
        position = self.get_position(position_id)
        if not position or not position.auto_trade:
            return []
        
        results = []
        
        # 현재 시장가로 ExecutionContext 업데이트
        if position.execution_context:
            position.execution_context.current_price = market_data.get('current_price', 0)
        
        # 활성화된 전략들 실행
        for strategy_rule in position.active_strategies:
            if not strategy_rule.enabled:
                continue
            
            try:
                # 1. 트리거 확인
                if strategy_rule.trigger:
                    trigger_result = strategy_rule.trigger.evaluate(market_data, position.execution_context)
                    if not trigger_result.success:
                        continue
                
                # 2. 조건들 확인
                if strategy_rule.conditions:
                    all_conditions_met = True
                    for condition in strategy_rule.conditions:
                        condition_result = condition.check(market_data, position.execution_context)
                        if not condition_result.success:
                            all_conditions_met = False
                            break
                    
                    if not all_conditions_met:
                        continue
                
                # 3. 액션 실행
                if strategy_rule.action:
                    action_result = strategy_rule.action.execute(market_data, position.execution_context)
                    results.append(action_result)
                    
                    # 실행 성공 시 포지션 상태 동기화
                    if action_result.success:
                        self._sync_position_from_context(position)
                
            except Exception as e:
                error_result = ComponentResult(False, f"전략 실행 오류 [{strategy_rule.rule_id}]: {str(e)}")
                results.append(error_result)
        
        return results
    
    def _sync_position_from_context(self, position: Position):
        """ExecutionContext에서 포지션으로 상태 동기화"""
        if not position.execution_context:
            return
        
        ctx = position.execution_context
        
        # 기본적인 동기화는 이미 각 액션에서 처리되므로
        # 여기서는 추가적인 메타데이터만 업데이트
        position.available_balance = Decimal(str(ctx.get_variable('available_balance', 0)))
    
    def get_total_portfolio_value(self, current_prices: Dict[str, float]) -> Dict[str, float]:
        """전체 포트폴리오 가치 계산"""
        current_price = current_prices.get(self.symbol, 0)
        
        total_invested = 0
        total_current_value = 0
        total_realized_pnl = 0
        
        for position in self.positions.values():
            total_invested += float(position.total_invested)
            total_current_value += float(position.quantity) * current_price
            total_realized_pnl += float(position.realized_pnl)
        
        unrealized_pnl = total_current_value - total_invested
        total_pnl = total_realized_pnl + unrealized_pnl
        
        return {
            'total_invested': total_invested,
            'total_current_value': total_current_value,
            'unrealized_pnl': unrealized_pnl,
            'realized_pnl': total_realized_pnl,
            'total_pnl': total_pnl,
            'roi_percent': (total_pnl / total_invested * 100) if total_invested > 0 else 0
        }
    
    def get_all_positions_summary(self) -> List[Dict[str, Any]]:
        """모든 포지션 요약"""
        return [position.get_position_summary() for position in self.positions.values()]


def create_example_multi_position_setup():
    """다중 포지션 예시 설정"""
    # BTC 포지션 매니저 생성
    btc_manager = PositionManager("KRW-BTC")
    
    # 포지션 1: 보수적 물타기 (500만원)
    conservative_id = btc_manager.create_position("보수적 물타기", 5000000)
    conservative_pos = btc_manager.get_position(conservative_id)
    
    # 포지션 2: 공격적 물타기 (1000만원)  
    aggressive_id = btc_manager.create_position("공격적 물타기", 10000000)
    aggressive_pos = btc_manager.get_position(aggressive_id)
    
    # 포지션 3: 실험적 전략 (200만원)
    experimental_id = btc_manager.create_position("실험적 전략", 2000000)
    experimental_pos = btc_manager.get_position(experimental_id)
    
    print(f"생성된 포지션들:")
    print(f"1. 보수적 물타기: {conservative_id}")
    print(f"2. 공격적 물타기: {aggressive_id}")
    print(f"3. 실험적 전략: {experimental_id}")
    
    return btc_manager, {
        'conservative': conservative_id,
        'aggressive': aggressive_id,
        'experimental': experimental_id
    }


if __name__ == "__main__":
    # 예시 실행
    manager, position_ids = create_example_multi_position_setup()
    
    # 각 포지션에 서로 다른 매수 실행
    manager.execute_trade_on_position(position_ids['conservative'], "buy", 0.01, 50000000)
    manager.execute_trade_on_position(position_ids['aggressive'], "buy", 0.05, 50000000)
    
    # 포트폴리오 요약
    portfolio_value = manager.get_total_portfolio_value({"KRW-BTC": 48000000})
    print(f"\n포트폴리오 현황: {portfolio_value}")
    
    positions_summary = manager.get_all_positions_summary()
    for pos_summary in positions_summary:
        print(f"\n포지션: {pos_summary}")
