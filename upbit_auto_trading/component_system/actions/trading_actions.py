"""
거래 액션 컴포넌트들 - 실제 매수/매도/포지션 관리를 담당
물타기 전략의 핵심이 되는 액션들
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal
from ..base import ActionComponent, ComponentResult, ExecutionContext


@dataclass
class BuyActionConfig:
    """매수 액션 설정"""
    amount_type: str = "fixed_amount"  # fixed_amount, percent_of_balance, position_ratio
    amount_value: float = 100000  # 매수 금액 (원)
    price_type: str = "market"  # market, limit, current
    limit_price_offset: float = 0  # 지정가 오프셋 (%)
    validate_balance: bool = True  # 잔고 확인 여부


class BuyAction(ActionComponent):
    """
    매수 액션 - 물타기 전략의 핵심
    다양한 매수 방식 지원 (고정 금액, 잔고 비율, 포지션 비율 등)
    """
    
    def __init__(self, config: BuyActionConfig):
        super().__init__(
            component_id=f"buy_{config.amount_type}_{config.amount_value}",
            name=f"매수 액션 ({config.amount_type})",
            description=f"{config.amount_type} 방식으로 {config.amount_value} 매수"
        )
        self.config = config
        self.last_execution_time: Optional[str] = None
    
    def execute(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """매수 액션 실행"""
        try:
            # 매수 금액 계산
            buy_amount = self._calculate_buy_amount(market_data, context)
            if buy_amount <= 0:
                return ComponentResult(False, "매수 금액이 0 이하")
            
            # 매수 가격 결정
            buy_price = self._determine_buy_price(market_data)
            if buy_price <= 0:
                return ComponentResult(False, "유효하지 않은 매수 가격")
            
            # 매수 수량 계산
            buy_quantity = buy_amount / buy_price
            
            # 잔고 확인 (옵션)
            if self.config.validate_balance:
                balance_check = self._validate_balance(buy_amount, context)
                if not balance_check:
                    return ComponentResult(False, "잔고 부족")
            
            # 실제 매수 실행 (시뮬레이션에서는 컨텍스트 업데이트)
            success = self._execute_buy_order(buy_quantity, buy_price, market_data, context)
            
            if success:
                self.last_execution_time = market_data.get('timestamp')
                
                return ComponentResult(
                    True,
                    f"매수 실행: {buy_quantity:.6f} @ {buy_price:,.0f} (총 {buy_amount:,.0f}원)",
                    metadata={
                        'action_type': 'buy',
                        'quantity': buy_quantity,
                        'price': buy_price,
                        'amount': buy_amount,
                        'amount_type': self.config.amount_type,
                        'price_type': self.config.price_type
                    }
                )
            else:
                return ComponentResult(False, "매수 주문 실패")
                
        except Exception as e:
            return ComponentResult(False, f"매수 액션 오류: {str(e)}")
    
    def _calculate_buy_amount(self, market_data: Dict[str, Any], context: ExecutionContext) -> float:
        """매수 금액 계산"""
        if self.config.amount_type == "fixed_amount":
            return self.config.amount_value
            
        elif self.config.amount_type == "percent_of_balance":
            # 잔고의 일정 비율
            available_balance = context.get_variable('available_balance', 1000000)
            return available_balance * (self.config.amount_value / 100)
            
        elif self.config.amount_type == "position_ratio":
            # 기존 포지션 대비 비율
            if not context.has_position:
                return self.config.amount_value  # 첫 매수는 고정 금액
            return context.total_invested * (self.config.amount_value / 100)
            
        elif self.config.amount_type == "add_buy_amount":
            # 물타기 횟수에 따른 누진적 매수
            base_amount = self.config.amount_value
            multiplier = 1 + (context.add_buy_count * 0.5)  # 50%씩 증가
            return base_amount * multiplier
            
        return self.config.amount_value
    
    def _determine_buy_price(self, market_data: Dict[str, Any]) -> float:
        """매수 가격 결정"""
        current_price = market_data.get('current_price', 0)
        
        if self.config.price_type == "market":
            return current_price
            
        elif self.config.price_type == "current":
            return current_price
            
        elif self.config.price_type == "limit":
            # 지정가 + 오프셋
            offset_amount = current_price * (self.config.limit_price_offset / 100)
            return current_price + offset_amount
            
        return current_price
    
    def _validate_balance(self, required_amount: float, context: ExecutionContext) -> bool:
        """잔고 확인"""
        available_balance = context.get_variable('available_balance', 1000000)
        return available_balance >= required_amount
    
    def _execute_buy_order(self, quantity: float, price: float, market_data: Dict[str, Any], context: ExecutionContext) -> bool:
        """매수 주문 실행 (시뮬레이션)"""
        try:
            # 실제 거래소 연결 시 여기서 API 호출
            # 시뮬레이션에서는 컨텍스트 업데이트
            
            timestamp = market_data.get('timestamp')
            success = context.add_buy_entry(quantity, price, timestamp)
            if not success:
                return False
            
            # 잔고 차감
            total_cost = quantity * price
            current_balance = context.get_variable('available_balance', 1000000)
            context.set_variable('available_balance', current_balance - total_cost)
            
            return True
            
        except Exception as e:
            print(f"매수 주문 실행 오류: {e}")
            return False


@dataclass
class SellActionConfig:
    """매도 액션 설정"""
    sell_type: str = "full_position"  # full_position, partial_percent, partial_amount
    sell_value: float = 100  # 매도 비율(%) 또는 수량
    price_type: str = "market"  # market, limit, current
    limit_price_offset: float = 0  # 지정가 오프셋 (%)


class SellAction(ActionComponent):
    """
    매도 액션 - 포지션 청산 또는 부분 매도
    """
    
    def __init__(self, config: SellActionConfig):
        super().__init__(
            component_id=f"sell_{config.sell_type}_{config.sell_value}",
            name=f"매도 액션 ({config.sell_type})",
            description=f"{config.sell_type} 방식으로 {config.sell_value} 매도"
        )
        self.config = config
        self.last_execution_time: Optional[str] = None
    
    def execute(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """매도 액션 실행"""
        try:
            if not context.has_position:
                return ComponentResult(False, "매도할 포지션이 없음")
            
            # 매도 수량 계산
            sell_quantity = self._calculate_sell_quantity(context)
            if sell_quantity <= 0:
                return ComponentResult(False, "매도 수량이 0 이하")
            
            # 매도 가격 결정
            sell_price = self._determine_sell_price(market_data)
            if sell_price <= 0:
                return ComponentResult(False, "유효하지 않은 매도 가격")
            
            # 실제 매도 실행
            success = self._execute_sell_order(sell_quantity, sell_price, market_data, context)
            
            if success:
                self.last_execution_time = market_data.get('timestamp')
                
                total_amount = sell_quantity * sell_price
                
                return ComponentResult(
                    True,
                    f"매도 실행: {sell_quantity:.6f} @ {sell_price:,.0f} (총 {total_amount:,.0f}원)",
                    metadata={
                        'action_type': 'sell',
                        'quantity': sell_quantity,
                        'price': sell_price,
                        'amount': total_amount,
                        'sell_type': self.config.sell_type,
                        'price_type': self.config.price_type
                    }
                )
            else:
                return ComponentResult(False, "매도 주문 실패")
                
        except Exception as e:
            return ComponentResult(False, f"매도 액션 오류: {str(e)}")
    
    def _calculate_sell_quantity(self, context: ExecutionContext) -> float:
        """매도 수량 계산"""
        if self.config.sell_type == "full_position":
            return context.position_size
            
        elif self.config.sell_type == "partial_percent":
            return context.position_size * (self.config.sell_value / 100)
            
        elif self.config.sell_type == "partial_amount":
            # 특정 수량만 매도
            return min(self.config.sell_value, context.position_size)
            
        return context.position_size
    
    def _determine_sell_price(self, market_data: Dict[str, Any]) -> float:
        """매도 가격 결정"""
        current_price = market_data.get('current_price', 0)
        
        if self.config.price_type == "market":
            return current_price
            
        elif self.config.price_type == "current":
            return current_price
            
        elif self.config.price_type == "limit":
            # 지정가 + 오프셋
            offset_amount = current_price * (self.config.limit_price_offset / 100)
            return current_price + offset_amount
            
        return current_price
    
    def _execute_sell_order(self, quantity: float, price: float, market_data: Dict[str, Any], context: ExecutionContext) -> bool:
        """매도 주문 실행 (시뮬레이션)"""
        try:
            # 실제 거래소 연결 시 여기서 API 호출
            # 시뮬레이션에서는 컨텍스트 업데이트
            
            total_amount = quantity * price
            
            if self.config.sell_type == "full_position":
                # 전체 포지션 청산
                context.close_position(price, market_data.get('timestamp'))
            else:
                # 부분 매도
                success = context.partial_sell(quantity, price, market_data.get('timestamp'))
                if not success:
                    return False
            
            # 잔고 증가
            current_balance = context.get_variable('available_balance', 0)
            context.set_variable('available_balance', current_balance + total_amount)
            
            return True
            
        except Exception as e:
            print(f"매도 주문 실행 오류: {e}")
            return False


@dataclass
class PositionManagementConfig:
    """포지션 관리 액션 설정"""
    action_type: str = "update_stop_loss"  # update_stop_loss, update_take_profit, rebalance
    target_value: float = 0  # 목표 값 (가격 또는 비율)
    trailing: bool = False  # 트레일링 여부


class PositionManagementAction(ActionComponent):
    """
    포지션 관리 액션 - 손절/익절 설정, 리밸런싱 등
    """
    
    def __init__(self, config: PositionManagementConfig):
        super().__init__(
            component_id=f"position_mgmt_{config.action_type}",
            name=f"포지션 관리 ({config.action_type})",
            description=f"{config.action_type} 실행"
        )
        self.config = config
        self.last_execution_time: Optional[str] = None
    
    def execute(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """포지션 관리 액션 실행"""
        try:
            if not context.has_position:
                return ComponentResult(False, "관리할 포지션이 없음")
            
            if self.config.action_type == "update_stop_loss":
                return self._update_stop_loss(market_data, context)
                
            elif self.config.action_type == "update_take_profit":
                return self._update_take_profit(market_data, context)
                
            elif self.config.action_type == "rebalance":
                return self._rebalance_position(market_data, context)
            
            return ComponentResult(False, f"알 수 없는 액션 타입: {self.config.action_type}")
            
        except Exception as e:
            return ComponentResult(False, f"포지션 관리 액션 오류: {str(e)}")
    
    def _update_stop_loss(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """손절가 업데이트"""
        current_price = market_data.get('current_price', 0)
        
        if self.config.trailing:
            # 트레일링 스탑
            new_stop_loss = current_price * (1 - self.config.target_value / 100)
            old_stop_loss = context.get_variable('stop_loss_price', 0)
            
            if new_stop_loss > old_stop_loss:  # 손절가 상향 조정만
                context.set_variable('stop_loss_price', new_stop_loss)
                return ComponentResult(
                    True,
                    f"트레일링 스탑 업데이트: {new_stop_loss:,.0f}",
                    metadata={'new_stop_loss': new_stop_loss, 'old_stop_loss': old_stop_loss}
                )
        else:
            # 고정 손절가
            stop_loss_price = context.average_price * (1 - self.config.target_value / 100)
            context.set_variable('stop_loss_price', stop_loss_price)
            return ComponentResult(
                True,
                f"손절가 설정: {stop_loss_price:,.0f}",
                metadata={'stop_loss_price': stop_loss_price}
            )
        
        return ComponentResult(False, "손절가 업데이트 없음")
    
    def _update_take_profit(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """익절가 업데이트"""
        take_profit_price = context.average_price * (1 + self.config.target_value / 100)
        context.set_variable('take_profit_price', take_profit_price)
        
        return ComponentResult(
            True,
            f"익절가 설정: {take_profit_price:,.0f}",
            metadata={'take_profit_price': take_profit_price}
        )
    
    def _rebalance_position(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """포지션 리밸런싱"""
        # 리밸런싱 로직 구현 (예: 목표 포지션 크기로 조정)
        target_position_value = self.config.target_value
        current_position_value = context.position_size * context.current_price
        
        return ComponentResult(
            True,
            f"리밸런싱 완료: 현재 {current_position_value:,.0f} → 목표 {target_position_value:,.0f}",
            metadata={
                'current_value': current_position_value,
                'target_value': target_position_value
            }
        )


@dataclass
class StopLossConfig:
    """손절매 액션 설정"""
    stop_loss_type: str = "percentage"  # percentage, fixed_price, trailing
    stop_loss_value: float = -5.0  # 손절 기준 (% 또는 절대 가격)
    trailing_distance: float = 2.0  # 트레일링 스탑 거리 (%)
    immediate_execution: bool = True  # 즉시 실행 여부


class StopLossAction(ActionComponent):
    """
    손절매 액션 - 리스크 관리를 위한 자동 매도
    """
    
    def __init__(self, config: StopLossConfig):
        super().__init__(
            component_id=f"stop_loss_{config.stop_loss_type}_{config.stop_loss_value}",
            name=f"손절매 액션 ({config.stop_loss_type})",
            description=f"{config.stop_loss_value}% 손절매"
        )
        self.config = config
        self.trailing_high_price: Optional[float] = None
    
    def execute(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """손절매 실행"""
        try:
            current_price = context.current_price
            if not current_price or context.position_size <= 0:
                return ComponentResult(False, "포지션이 없음")
            
            # 손절 기준 계산
            if self.config.stop_loss_type == "percentage":
                stop_price = context.average_price * (1 + self.config.stop_loss_value / 100)
            elif self.config.stop_loss_type == "fixed_price":
                stop_price = self.config.stop_loss_value
            elif self.config.stop_loss_type == "trailing":
                stop_price = self._calculate_trailing_stop(current_price)
            else:
                return ComponentResult(False, f"지원하지 않는 손절 타입: {self.config.stop_loss_type}")
            
            # 손절 조건 확인
            if current_price <= stop_price:
                if self.config.immediate_execution:
                    # 즉시 매도 실행
                    return self._execute_stop_loss_sell(current_price, context)
                else:
                    # 손절 신호만 발생
                    return ComponentResult(
                        True,
                        f"손절 신호 발생: 현재가 {current_price:,.0f} <= 손절가 {stop_price:,.0f}",
                        metadata={
                            'signal_type': 'stop_loss',
                            'current_price': current_price,
                            'stop_price': stop_price
                        }
                    )
            
            return ComponentResult(False, f"손절 조건 미충족: 현재가 {current_price:,.0f} > 손절가 {stop_price:,.0f}")
            
        except Exception as e:
            return ComponentResult(False, f"손절매 액션 오류: {str(e)}")
    
    def _calculate_trailing_stop(self, current_price: float) -> float:
        """트레일링 스탑 계산"""
        if self.trailing_high_price is None:
            self.trailing_high_price = current_price
        
        # 신고가 갱신
        if current_price > self.trailing_high_price:
            self.trailing_high_price = current_price
        
        # 트레일링 스탑 가격 계산
        trailing_stop = self.trailing_high_price * (1 - self.config.trailing_distance / 100)
        return trailing_stop
    
    def _execute_stop_loss_sell(self, current_price: float, context: ExecutionContext) -> ComponentResult:
        """손절매 매도 실행"""
        sell_amount = context.position_size
        
        # 태그가 있는 포지션에서만 매도
        if hasattr(context, 'position_tag') and context.position_tag == 'AUTO':
            # 실제 매도 API 호출 (여기서는 시뮬레이션)
            sell_value = sell_amount * current_price
            
            # 컨텍스트 업데이트 - 전체 포지션 청산
            context.close_position(current_price)
            
            return ComponentResult(
                True,
                f"손절매 매도 완료: {sell_amount:.8f} 코인, {sell_value:,.0f}원",
                metadata={
                    'action_type': 'stop_loss_sell',
                    'sell_amount': sell_amount,
                    'sell_price': current_price,
                    'sell_value': sell_value
                }
            )
        else:
            return ComponentResult(False, "AUTO 태그 포지션이 아님")


@dataclass
class TakeProfitConfig:
    """익절매 액션 설정"""
    profit_type: str = "percentage"  # percentage, fixed_price, rr_ratio
    profit_value: float = 10.0  # 익절 기준 (% 또는 절대 가격)
    partial_take: bool = False  # 부분 익절 여부
    partial_ratio: float = 0.5  # 부분 익절 비율 (0.0 ~ 1.0)
    immediate_execution: bool = True  # 즉시 실행 여부


class TakeProfitAction(ActionComponent):
    """
    익절매 액션 - 수익 실현을 위한 자동 매도
    """
    
    def __init__(self, config: TakeProfitConfig):
        super().__init__(
            component_id=f"take_profit_{config.profit_type}_{config.profit_value}",
            name=f"익절매 액션 ({config.profit_type})",
            description=f"{config.profit_value}% 익절매"
        )
        self.config = config
    
    def execute(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """익절매 실행"""
        try:
            current_price = context.current_price
            if not current_price or context.position_size <= 0:
                return ComponentResult(False, "포지션이 없음")
            
            # 익절 기준 계산
            if self.config.profit_type == "percentage":
                take_profit_price = context.average_price * (1 + self.config.profit_value / 100)
            elif self.config.profit_type == "fixed_price":
                take_profit_price = self.config.profit_value
            elif self.config.profit_type == "rr_ratio":
                # 리스크 리워드 비율 기반
                stop_loss_distance = abs(context.average_price - context.get_variable('stop_loss_price', context.average_price))
                take_profit_price = context.average_price + (stop_loss_distance * self.config.profit_value)
            else:
                return ComponentResult(False, f"지원하지 않는 익절 타입: {self.config.profit_type}")
            
            # 익절 조건 확인
            if current_price >= take_profit_price:
                if self.config.immediate_execution:
                    # 즉시 매도 실행
                    return self._execute_take_profit_sell(current_price, context)
                else:
                    # 익절 신호만 발생
                    return ComponentResult(
                        True,
                        f"익절 신호 발생: 현재가 {current_price:,.0f} >= 익절가 {take_profit_price:,.0f}",
                        metadata={
                            'signal_type': 'take_profit',
                            'current_price': current_price,
                            'take_profit_price': take_profit_price
                        }
                    )
            
            return ComponentResult(False, f"익절 조건 미충족: 현재가 {current_price:,.0f} < 익절가 {take_profit_price:,.0f}")
            
        except Exception as e:
            return ComponentResult(False, f"익절매 액션 오류: {str(e)}")
    
    def _execute_take_profit_sell(self, current_price: float, context: ExecutionContext) -> ComponentResult:
        """익절매 매도 실행"""
        if self.config.partial_take:
            # 부분 익절
            sell_amount = context.position_size * self.config.partial_ratio
            remaining_amount = context.position_size - sell_amount
        else:
            # 전체 익절
            sell_amount = context.position_size
            remaining_amount = 0
        
        # 태그가 있는 포지션에서만 매도
        if hasattr(context, 'position_tag') and context.position_tag == 'AUTO':
            # 실제 매도 API 호출 (여기서는 시뮬레이션)
            sell_value = sell_amount * current_price
            
            # 컨텍스트 업데이트
            if self.config.partial_take:
                # 부분 익절
                success = context.partial_sell(sell_amount, current_price)
                if not success:
                    return ComponentResult(False, "부분 익절 실패")
            else:
                # 전체 익절
                context.close_position(current_price)
            
            action_type = "partial_take_profit" if self.config.partial_take else "full_take_profit"
            
            return ComponentResult(
                True,
                f"익절매 매도 완료: {sell_amount:.8f} 코인, {sell_value:,.0f}원",
                metadata={
                    'action_type': action_type,
                    'sell_amount': sell_amount,
                    'sell_price': current_price,
                    'sell_value': sell_value,
                    'remaining_amount': remaining_amount
                }
            )
        else:
            return ComponentResult(False, "AUTO 태그 포지션이 아님")
