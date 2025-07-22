"""
조건 컴포넌트들 - 트리거 이후 추가 검증을 담당
물타기 전략에서 중요한 리스크 관리 조건들
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal
from ..base import ConditionComponent, ComponentResult, ExecutionContext


@dataclass
class ProfitLossConditionConfig:
    """수익률 조건 설정"""
    condition_type: str = "profit_above"  # profit_above, loss_below, profit_between
    target_percent: float = 5.0  # 목표 수익률 (%)
    max_percent: Optional[float] = None  # 최대 수익률 (between 타입용)


class ProfitLossCondition(ConditionComponent):
    """
    수익률 조건 - 현재 포지션의 수익률 확인
    물타기 전략에서 익절 조건으로 자주 사용
    """
    
    def __init__(self, config: ProfitLossConditionConfig):
        super().__init__(
            component_id=f"pnl_{config.condition_type}_{config.target_percent}",
            name=f"수익률 조건 ({config.condition_type})",
            description=f"{config.condition_type}: {config.target_percent}%"
        )
        self.config = config
    
    def check(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """수익률 조건 확인"""
        try:
            if not context.has_position:
                return ComponentResult(False, "포지션이 없어 수익률 계산 불가")
            
            current_pnl_percent = context.get_profit_loss_percent() * 100
            
            if self.config.condition_type == "profit_above":
                condition_met = current_pnl_percent >= self.config.target_percent
                message = f"수익률 {current_pnl_percent:.2f}% {'≥' if condition_met else '<'} {self.config.target_percent}%"
                
            elif self.config.condition_type == "loss_below":
                condition_met = current_pnl_percent <= -abs(self.config.target_percent)
                message = f"손실 {current_pnl_percent:.2f}% {'≤' if condition_met else '>'} -{abs(self.config.target_percent)}%"
                
            elif self.config.condition_type == "profit_between":
                min_percent = self.config.target_percent
                max_percent = self.config.max_percent or (self.config.target_percent + 10)
                condition_met = min_percent <= current_pnl_percent <= max_percent
                message = f"수익률 {current_pnl_percent:.2f}% {'between' if condition_met else 'not between'} {min_percent}%~{max_percent}%"
                
            else:
                return ComponentResult(False, f"알 수 없는 조건 타입: {self.config.condition_type}")
            
            return ComponentResult(
                condition_met,
                message,
                metadata={
                    'condition_type': 'profit_loss',
                    'current_pnl_percent': current_pnl_percent,
                    'target_percent': self.config.target_percent,
                    'condition_met': condition_met
                }
            )
            
        except Exception as e:
            return ComponentResult(False, f"수익률 조건 확인 오류: {str(e)}")


@dataclass
class PositionSizeConditionConfig:
    """포지션 크기 조건 설정"""
    condition_type: str = "max_position"  # max_position, min_position, exact_position
    target_value: float = 1000000  # 목표 값 (원)
    value_type: str = "amount"  # amount (금액), quantity (수량)


class PositionSizeCondition(ConditionComponent):
    """
    포지션 크기 조건 - 현재 포지션 크기 확인
    물타기에서 최대 투자금액 제한으로 자주 사용
    """
    
    def __init__(self, config: PositionSizeConditionConfig):
        super().__init__(
            component_id=f"position_size_{config.condition_type}_{config.target_value}",
            name=f"포지션 크기 조건 ({config.condition_type})",
            description=f"{config.condition_type}: {config.target_value} {config.value_type}"
        )
        self.config = config
    
    def check(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """포지션 크기 조건 확인"""
        try:
            if self.config.value_type == "amount":
                current_value = context.total_invested
                unit = "원"
            else:  # quantity
                current_value = context.position_size
                unit = "개"
            
            if self.config.condition_type == "max_position":
                condition_met = current_value <= self.config.target_value
                message = f"포지션 크기 {current_value:,.0f}{unit} {'≤' if condition_met else '>'} {self.config.target_value:,.0f}{unit}"
                
            elif self.config.condition_type == "min_position":
                condition_met = current_value >= self.config.target_value
                message = f"포지션 크기 {current_value:,.0f}{unit} {'≥' if condition_met else '<'} {self.config.target_value:,.0f}{unit}"
                
            elif self.config.condition_type == "exact_position":
                tolerance = self.config.target_value * 0.05  # 5% 허용 오차
                condition_met = abs(current_value - self.config.target_value) <= tolerance
                message = f"포지션 크기 {current_value:,.0f}{unit} {'≈' if condition_met else '≠'} {self.config.target_value:,.0f}{unit}"
                
            else:
                return ComponentResult(False, f"알 수 없는 조건 타입: {self.config.condition_type}")
            
            return ComponentResult(
                condition_met,
                message,
                metadata={
                    'condition_type': 'position_size',
                    'current_value': current_value,
                    'target_value': self.config.target_value,
                    'value_type': self.config.value_type,
                    'condition_met': condition_met
                }
            )
            
        except Exception as e:
            return ComponentResult(False, f"포지션 크기 조건 확인 오류: {str(e)}")


@dataclass
class AddBuyCountConditionConfig:
    """물타기 횟수 조건 설정"""
    condition_type: str = "max_count"  # max_count, min_count, exact_count
    target_count: int = 3  # 목표 횟수


class AddBuyCountCondition(ConditionComponent):
    """
    물타기 횟수 조건 - 추가 매수 횟수 제한
    물타기 전략의 핵심 리스크 관리 조건
    """
    
    def __init__(self, config: AddBuyCountConditionConfig):
        super().__init__(
            component_id=f"add_buy_count_{config.condition_type}_{config.target_count}",
            name=f"물타기 횟수 조건 ({config.condition_type})",
            description=f"{config.condition_type}: {config.target_count}회"
        )
        self.config = config
    
    def check(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """물타기 횟수 조건 확인"""
        try:
            current_count = context.add_buy_count
            
            if self.config.condition_type == "max_count":
                condition_met = current_count < self.config.target_count  # 아직 최대에 도달하지 않음
                message = f"물타기 횟수 {current_count}회 {'<' if condition_met else '≥'} 최대 {self.config.target_count}회"
                
            elif self.config.condition_type == "min_count":
                condition_met = current_count >= self.config.target_count
                message = f"물타기 횟수 {current_count}회 {'≥' if condition_met else '<'} 최소 {self.config.target_count}회"
                
            elif self.config.condition_type == "exact_count":
                condition_met = current_count == self.config.target_count
                message = f"물타기 횟수 {current_count}회 {'==' if condition_met else '!='} 정확히 {self.config.target_count}회"
                
            else:
                return ComponentResult(False, f"알 수 없는 조건 타입: {self.config.condition_type}")
            
            return ComponentResult(
                condition_met,
                message,
                metadata={
                    'condition_type': 'add_buy_count',
                    'current_count': current_count,
                    'target_count': self.config.target_count,
                    'condition_met': condition_met
                }
            )
            
        except Exception as e:
            return ComponentResult(False, f"물타기 횟수 조건 확인 오류: {str(e)}")


@dataclass
class TimeConditionConfig:
    """시간 조건 설정"""
    condition_type: str = "position_hold_time"  # position_hold_time, market_hours, cooldown
    target_minutes: int = 60  # 목표 시간 (분)
    comparison: str = "more_than"  # more_than, less_than, exactly


class TimeCondition(ConditionComponent):
    """
    시간 조건 - 시간 기반 조건 확인
    포지션 보유 시간, 마켓 시간, 쿨다운 등
    """
    
    def __init__(self, config: TimeConditionConfig):
        super().__init__(
            component_id=f"time_{config.condition_type}_{config.target_minutes}",
            name=f"시간 조건 ({config.condition_type})",
            description=f"{config.condition_type}: {config.comparison} {config.target_minutes}분"
        )
        self.config = config
    
    def check(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """시간 조건 확인"""
        try:
            from datetime import datetime, timedelta
            
            current_time = datetime.now()
            
            if self.config.condition_type == "position_hold_time":
                if not context.has_position or not context.entry_time:
                    return ComponentResult(False, "포지션이 없거나 진입 시간 정보 없음")
                
                hold_duration = current_time - context.entry_time
                hold_minutes = hold_duration.total_seconds() / 60
                
                if self.config.comparison == "more_than":
                    condition_met = hold_minutes > self.config.target_minutes
                    operator = ">"
                elif self.config.comparison == "less_than":
                    condition_met = hold_minutes < self.config.target_minutes
                    operator = "<"
                else:  # exactly
                    tolerance = 5  # 5분 허용 오차
                    condition_met = abs(hold_minutes - self.config.target_minutes) <= tolerance
                    operator = "≈"
                
                message = f"포지션 보유시간 {hold_minutes:.1f}분 {operator} {self.config.target_minutes}분"
                
                return ComponentResult(
                    condition_met,
                    message,
                    metadata={
                        'condition_type': 'time',
                        'hold_minutes': hold_minutes,
                        'target_minutes': self.config.target_minutes,
                        'condition_met': condition_met
                    }
                )
                
            elif self.config.condition_type == "market_hours":
                # 한국 시장 시간 체크 (9:00 ~ 15:30)
                market_open = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
                market_close = current_time.replace(hour=15, minute=30, second=0, microsecond=0)
                
                is_market_hours = market_open <= current_time <= market_close
                weekday = current_time.weekday()  # 0=월요일, 6=일요일
                is_weekday = weekday < 5
                
                condition_met = is_market_hours and is_weekday
                message = f"시장시간 {'O' if condition_met else 'X'} (현재: {current_time.strftime('%H:%M')})"
                
                return ComponentResult(
                    condition_met,
                    message,
                    metadata={
                        'condition_type': 'market_hours',
                        'is_market_hours': is_market_hours,
                        'is_weekday': is_weekday,
                        'condition_met': condition_met
                    }
                )
                
            elif self.config.condition_type == "cooldown":
                # 마지막 거래 이후 쿨다운 시간 체크
                last_signal_time = context.last_signal_time
                if not last_signal_time:
                    return ComponentResult(True, "첫 거래 - 쿨다운 조건 통과")
                
                cooldown_duration = current_time - last_signal_time
                cooldown_minutes = cooldown_duration.total_seconds() / 60
                
                condition_met = cooldown_minutes >= self.config.target_minutes
                message = f"쿨다운 {cooldown_minutes:.1f}분 {'≥' if condition_met else '<'} 필요 {self.config.target_minutes}분"
                
                return ComponentResult(
                    condition_met,
                    message,
                    metadata={
                        'condition_type': 'cooldown',
                        'cooldown_minutes': cooldown_minutes,
                        'target_minutes': self.config.target_minutes,
                        'condition_met': condition_met
                    }
                )
                
            return ComponentResult(False, f"알 수 없는 시간 조건 타입: {self.config.condition_type}")
            
        except Exception as e:
            return ComponentResult(False, f"시간 조건 확인 오류: {str(e)}")


@dataclass
class BalanceConditionConfig:
    """잔고 조건 설정"""
    condition_type: str = "min_balance"  # min_balance, max_balance, balance_ratio
    target_amount: float = 100000  # 목표 금액 (원)
    ratio: Optional[float] = None  # 비율 (%) - balance_ratio 타입용


class BalanceCondition(ConditionComponent):
    """
    잔고 조건 - 사용 가능한 잔고 확인
    물타기에서 더 이상 매수할 수 없는 상황을 방지
    """
    
    def __init__(self, config: BalanceConditionConfig):
        super().__init__(
            component_id=f"balance_{config.condition_type}_{config.target_amount}",
            name=f"잔고 조건 ({config.condition_type})",
            description=f"{config.condition_type}: {config.target_amount:,.0f}원"
        )
        self.config = config
    
    def check(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """잔고 조건 확인"""
        try:
            available_balance = context.get_variable('available_balance', 1000000)
            
            if self.config.condition_type == "min_balance":
                condition_met = available_balance >= self.config.target_amount
                message = f"잔고 {available_balance:,.0f}원 {'≥' if condition_met else '<'} 최소 {self.config.target_amount:,.0f}원"
                
            elif self.config.condition_type == "max_balance":
                condition_met = available_balance <= self.config.target_amount
                message = f"잔고 {available_balance:,.0f}원 {'≤' if condition_met else '>'} 최대 {self.config.target_amount:,.0f}원"
                
            elif self.config.condition_type == "balance_ratio":
                # 전체 자본 대비 사용 가능한 잔고 비율
                total_capital = available_balance + context.total_invested
                current_ratio = (available_balance / total_capital * 100) if total_capital > 0 else 0
                target_ratio = self.config.ratio or 20  # 기본 20%
                
                condition_met = current_ratio >= target_ratio
                message = f"잔고 비율 {current_ratio:.1f}% {'≥' if condition_met else '<'} 목표 {target_ratio}%"
                
            else:
                return ComponentResult(False, f"알 수 없는 조건 타입: {self.config.condition_type}")
            
            return ComponentResult(
                condition_met,
                message,
                metadata={
                    'condition_type': 'balance',
                    'available_balance': available_balance,
                    'target_amount': self.config.target_amount,
                    'condition_met': condition_met
                }
            )
            
        except Exception as e:
            return ComponentResult(False, f"잔고 조건 확인 오류: {str(e)}")


@dataclass
class TechnicalIndicatorConditionConfig:
    """기술적 지표 조건 설정"""
    indicator_type: str = "rsi"  # rsi, macd, bollinger, volume
    condition_type: str = "above"  # above, below, between, cross_above, cross_below
    target_value: float = 70  # 목표 값
    secondary_value: Optional[float] = None  # 두 번째 값 (between, cross 타입용)


class TechnicalIndicatorCondition(ConditionComponent):
    """
    기술적 지표 조건 - RSI, MACD, 볼린저밴드 등
    물타기에서 과매도/과매수 상황 판단에 사용
    """
    
    def __init__(self, config: TechnicalIndicatorConditionConfig):
        super().__init__(
            component_id=f"indicator_{config.indicator_type}_{config.condition_type}_{config.target_value}",
            name=f"기술적 지표 조건 ({config.indicator_type} {config.condition_type})",
            description=f"{config.indicator_type} {config.condition_type} {config.target_value}"
        )
        self.config = config
    
    def check(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """기술적 지표 조건 확인"""
        try:
            indicator_value = self._get_indicator_value(market_data)
            if indicator_value is None:
                return ComponentResult(False, f"{self.config.indicator_type} 지표 데이터 없음")
            
            if self.config.condition_type == "above":
                condition_met = indicator_value > self.config.target_value
                message = f"{self.config.indicator_type.upper()} {indicator_value:.2f} {'>' if condition_met else '≤'} {self.config.target_value}"
                
            elif self.config.condition_type == "below":
                condition_met = indicator_value < self.config.target_value
                message = f"{self.config.indicator_type.upper()} {indicator_value:.2f} {'<' if condition_met else '≥'} {self.config.target_value}"
                
            elif self.config.condition_type == "between":
                min_val = self.config.target_value
                max_val = self.config.secondary_value or (self.config.target_value + 10)
                condition_met = min_val <= indicator_value <= max_val
                message = f"{self.config.indicator_type.upper()} {indicator_value:.2f} {'between' if condition_met else 'not between'} {min_val}~{max_val}"
                
            else:
                return ComponentResult(False, f"지원하지 않는 조건 타입: {self.config.condition_type}")
            
            return ComponentResult(
                condition_met,
                message,
                metadata={
                    'condition_type': 'technical_indicator',
                    'indicator_type': self.config.indicator_type,
                    'indicator_value': indicator_value,
                    'target_value': self.config.target_value,
                    'condition_met': condition_met
                }
            )
            
        except Exception as e:
            return ComponentResult(False, f"기술적 지표 조건 확인 오류: {str(e)}")
    
    def _get_indicator_value(self, market_data: Dict[str, Any]) -> Optional[float]:
        """지표 값 가져오기"""
        if self.config.indicator_type == "rsi":
            return market_data.get('rsi')
        elif self.config.indicator_type == "macd":
            return market_data.get('macd')
        elif self.config.indicator_type == "bollinger":
            # 볼린저밴드 %B 값
            return market_data.get('bb_percent')
        elif self.config.indicator_type == "volume":
            return market_data.get('volume_ratio')  # 평균 대비 거래량 비율
        
        return None
