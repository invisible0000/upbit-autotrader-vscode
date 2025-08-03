#!/usr/bin/env python3
"""
관리 규칙 도메인 엔티티 (ManagementRule Domain Entity)
===========================================================

관리 규칙은 활성 포지션에 대한 리스크 관리와 수익 최적화를 위한 도메인 엔티티입니다.
기존 전략 시스템의 관리 전략 로직을 순수한 도메인 모델로 추상화합니다.

Design Principles:
- DDD Entity: 고유 식별자를 가진 포지션 관리 전용 엔티티
- Business Logic Encapsulation: 물타기, 불타기, 손절/익절 등 모든 관리 로직 캡슐화
- Position State Awareness: 현재 포지션 상태에 따른 조건부 실행
- Domain Events: 관리 규칙 실행 및 포지션 변경 이벤트 발생

Management Types:
- PYRAMID_BUYING: 물타기 (하락 시 추가 매수)
- SCALE_IN_BUYING: 불타기 (상승 시 추가 매수)
- TRAILING_STOP: 트레일링 스탑 (수익 보호용 후행 손절)
- FIXED_STOP_TAKE: 고정 손절/익절 (고정된 목표 수익률)
- TIME_BASED_EXIT: 시간 기반 청산 (최대 보유 시간 제한)
- PARTIAL_TAKE_PROFIT: 부분 익절 (단계별 수익 실현)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime, timedelta
from decimal import Decimal

# Domain imports
from ..value_objects.signal_type import SignalType
from ..exceptions.domain_exceptions import DomainException


class InvalidManagementRuleError(DomainException):
    """잘못된 관리 규칙 설정 예외"""
    pass


class IncompatiblePositionStateError(DomainException):
    """호환되지 않는 포지션 상태 예외"""
    pass


class ManagementType(Enum):
    """관리 전략 유형 분류"""
    PYRAMID_BUYING = "pyramid_buying"        # 물타기 (하락 시 추가 매수)
    SCALE_IN_BUYING = "scale_in_buying"      # 불타기 (상승 시 추가 매수)
    TRAILING_STOP = "trailing_stop"          # 트레일링 스탑 (후행 손절)
    FIXED_STOP_TAKE = "fixed_stop_take"      # 고정 손절/익절
    TIME_BASED_EXIT = "time_based_exit"      # 시간 기반 청산
    PARTIAL_TAKE_PROFIT = "partial_take_profit"  # 부분 익절
    
    def get_display_name(self) -> str:
        """표시용 한글 이름"""
        display_names = {
            self.PYRAMID_BUYING: "물타기",
            self.SCALE_IN_BUYING: "불타기",
            self.TRAILING_STOP: "트레일링 스탑",
            self.FIXED_STOP_TAKE: "고정 손절/익절",
            self.TIME_BASED_EXIT: "시간 기반 청산",
            self.PARTIAL_TAKE_PROFIT: "부분 익절"
        }
        return display_names[self]
    
    def get_description(self) -> str:
        """상세 설명"""
        descriptions = {
            self.PYRAMID_BUYING: "하락 시 평단가를 낮추기 위해 추가 매수합니다",
            self.SCALE_IN_BUYING: "상승 시 수익을 극대화하기 위해 추가 매수합니다",
            self.TRAILING_STOP: "최고점에서 일정 비율 하락 시 손절하여 수익을 보호합니다",
            self.FIXED_STOP_TAKE: "고정된 손절선과 익절선으로 리스크를 관리합니다",
            self.TIME_BASED_EXIT: "최대 보유 시간 초과 시 강제로 청산합니다",
            self.PARTIAL_TAKE_PROFIT: "단계별로 일부 물량을 매도하여 수익을 확정합니다"
        }
        return descriptions[self]
    
    def requires_position(self) -> bool:
        """포지션이 필요한 관리 타입인지 확인"""
        return True  # 모든 관리 규칙은 포지션이 있어야 실행됨
    
    def allowed_signals(self) -> List[SignalType]:
        """허용되는 신호 타입들"""
        signal_mapping = {
            self.PYRAMID_BUYING: [SignalType.ADD_BUY, SignalType.CLOSE_POSITION],
            self.SCALE_IN_BUYING: [SignalType.ADD_BUY, SignalType.CLOSE_POSITION],
            self.TRAILING_STOP: [SignalType.CLOSE_POSITION, SignalType.UPDATE_STOP],
            self.FIXED_STOP_TAKE: [SignalType.CLOSE_POSITION],
            self.TIME_BASED_EXIT: [SignalType.CLOSE_POSITION],
            self.PARTIAL_TAKE_PROFIT: [SignalType.ADD_SELL, SignalType.CLOSE_POSITION]
        }
        return signal_mapping[self]


@dataclass(frozen=True)
class PositionState:
    """포지션 상태 값 객체"""
    symbol: str                             # 거래 종목
    avg_price: Decimal                      # 평균 단가
    quantity: Decimal                       # 보유 수량
    current_price: Decimal                  # 현재 가격
    entry_time: datetime                    # 진입 시간
    highest_price: Optional[Decimal] = None  # 최고가 (트레일링 스탑용)
    
    def __post_init__(self):
        """포지션 상태 유효성 검증"""
        if not self.symbol:
            raise ValueError("거래 종목은 필수입니다")
        
        if self.avg_price <= 0:
            raise ValueError("평균 단가는 0보다 커야 합니다")
        
        if self.quantity <= 0:
            raise ValueError("보유 수량은 0보다 커야 합니다")
        
        if self.current_price <= 0:
            raise ValueError("현재 가격은 0보다 커야 합니다")
    
    def get_profit_rate(self) -> Decimal:
        """수익률 계산 (% 단위)"""
        return ((self.current_price - self.avg_price) / self.avg_price) * 100
    
    def get_profit_amount(self) -> Decimal:
        """수익 금액 계산"""
        return (self.current_price - self.avg_price) * self.quantity
    
    def is_profitable(self) -> bool:
        """수익 상태인지 확인"""
        return self.current_price > self.avg_price
    
    def is_loss(self) -> bool:
        """손실 상태인지 확인"""
        return self.current_price < self.avg_price
    
    def get_holding_time(self) -> timedelta:
        """보유 시간 계산"""
        return datetime.now() - self.entry_time


@dataclass(frozen=True)
class ManagementExecutionResult:
    """관리 규칙 실행 결과"""
    signal: SignalType
    executed: bool
    reason: str
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def success(cls, signal: SignalType, reason: str, **kwargs) -> "ManagementExecutionResult":
        """성공 결과 생성"""
        return cls(signal=signal, executed=True, reason=reason, additional_data=kwargs)
    
    @classmethod
    def hold(cls, reason: str) -> "ManagementExecutionResult":
        """대기 결과 생성"""
        return cls(signal=SignalType.HOLD, executed=False, reason=reason)
    
    @classmethod
    def failure(cls, reason: str) -> "ManagementExecutionResult":
        """실패 결과 생성"""
        return cls(signal=SignalType.HOLD, executed=False, reason=f"실행 실패: {reason}")


@dataclass
class ManagementRule:
    """
    관리 규칙 도메인 엔티티
    
    활성 포지션에 대한 리스크 관리와 수익 최적화를 담당하는 도메인 엔티티:
    - 고유 식별자와 메타데이터
    - 관리 전략 타입과 설정
    - 포지션 상태 기반 실행 로직
    - 도메인 이벤트 관리
    """
    
    rule_id: str
    management_type: ManagementType
    parameters: Dict[str, Any]
    priority: int = 1
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    last_executed_at: Optional[datetime] = None
    execution_count: int = 0
    
    # 내부 상태 (도메인 이벤트 추적용)
    _domain_events: List[Dict[str, Any]] = field(default_factory=list, init=False, repr=False)
    
    def __post_init__(self):
        """생성 후 유효성 검증"""
        if not self.rule_id:
            raise InvalidManagementRuleError("관리 규칙 ID는 필수입니다")
        
        if self.priority < 1:
            raise InvalidManagementRuleError("우선순위는 1 이상이어야 합니다")
        
        # 관리 타입별 필수 파라미터 검증
        self._validate_parameters()
        
        # 도메인 이벤트 기록
        self._record_domain_event("management_rule_created", {
            "rule_id": self.rule_id,
            "management_type": self.management_type.value,
            "parameters": self.parameters
        })
    
    def _validate_parameters(self) -> None:
        """관리 타입별 필수 파라미터 검증"""
        required_params = {
            ManagementType.PYRAMID_BUYING: ["trigger_drop_rate", "max_additions"],
            ManagementType.SCALE_IN_BUYING: ["trigger_profit_rate", "max_additions"],
            ManagementType.TRAILING_STOP: ["trail_distance", "activation_profit"],
            ManagementType.FIXED_STOP_TAKE: ["stop_loss_rate", "take_profit_rate"],
            ManagementType.TIME_BASED_EXIT: ["max_holding_hours"],
            ManagementType.PARTIAL_TAKE_PROFIT: ["profit_levels", "sell_ratios"]
        }
        
        required = required_params.get(self.management_type, [])
        missing = [param for param in required if param not in self.parameters]
        
        if missing:
            raise InvalidManagementRuleError(
                f"{self.management_type.get_display_name()} 타입에 필요한 파라미터가 누락되었습니다: {missing}"
            )
    
    def execute(self, position_state: PositionState) -> ManagementExecutionResult:
        """관리 규칙 실행"""
        if not self.is_active:
            return ManagementExecutionResult.hold("규칙이 비활성화되어 있습니다")
        
        try:
            # 관리 타입별 실행 로직 위임
            if self.management_type == ManagementType.PYRAMID_BUYING:
                result = self._execute_pyramid_buying(position_state)
            elif self.management_type == ManagementType.SCALE_IN_BUYING:
                result = self._execute_scale_in_buying(position_state)
            elif self.management_type == ManagementType.TRAILING_STOP:
                result = self._execute_trailing_stop(position_state)
            elif self.management_type == ManagementType.FIXED_STOP_TAKE:
                result = self._execute_fixed_stop_take(position_state)
            elif self.management_type == ManagementType.TIME_BASED_EXIT:
                result = self._execute_time_based_exit(position_state)
            elif self.management_type == ManagementType.PARTIAL_TAKE_PROFIT:
                result = self._execute_partial_take_profit(position_state)
            else:
                return ManagementExecutionResult.failure(f"지원하지 않는 관리 타입: {self.management_type}")
            
            # 실행 기록 업데이트
            if result.executed:
                self.execution_count += 1
                self.last_executed_at = datetime.now()
                self._record_domain_event("management_rule_executed", {
                    "rule_id": self.rule_id,
                    "signal": result.signal.value,
                    "position_symbol": position_state.symbol,
                    "execution_count": self.execution_count
                })
            
            return result
            
        except Exception as e:
            error_msg = f"관리 규칙 실행 중 오류: {str(e)}"
            self._record_domain_event("management_rule_error", {
                "rule_id": self.rule_id,
                "error": error_msg,
                "position_symbol": position_state.symbol
            })
            return ManagementExecutionResult.failure(error_msg)
    
    def _execute_pyramid_buying(self, position: PositionState) -> ManagementExecutionResult:
        """물타기 실행 로직"""
        trigger_drop_rate = self.parameters["trigger_drop_rate"]
        max_additions = self.parameters["max_additions"]
        
        loss_rate = abs(position.get_profit_rate())
        
        # 절대 손절선 체크 (있다면)
        if "absolute_stop_loss" in self.parameters:
            if loss_rate >= self.parameters["absolute_stop_loss"]:
                return ManagementExecutionResult.success(
                    SignalType.CLOSE_POSITION,
                    f"절대 손절선 도달 (손실률: {loss_rate:.2f}%)"
                )
        
        # 추가 매수 횟수 체크
        if self.execution_count >= max_additions:
            return ManagementExecutionResult.hold(f"최대 물타기 횟수 도달 ({max_additions}회)")
        
        # 물타기 조건 확인
        required_drop = trigger_drop_rate * (self.execution_count + 1)
        if position.is_loss() and loss_rate >= required_drop:
            return ManagementExecutionResult.success(
                SignalType.ADD_BUY,
                f"물타기 조건 충족 (손실률: {loss_rate:.2f}%, 기준: {required_drop:.2f}%)",
                addition_count=self.execution_count + 1
            )
        
        return ManagementExecutionResult.hold("물타기 조건 미충족")
    
    def _execute_scale_in_buying(self, position: PositionState) -> ManagementExecutionResult:
        """불타기 실행 로직"""
        trigger_profit_rate = self.parameters["trigger_profit_rate"]
        max_additions = self.parameters["max_additions"]
        
        profit_rate = position.get_profit_rate()
        
        # 목표 수익률 달성 시 청산 (있다면)
        if "profit_target" in self.parameters:
            if profit_rate >= self.parameters["profit_target"]:
                return ManagementExecutionResult.success(
                    SignalType.CLOSE_POSITION,
                    f"목표 수익률 달성 (수익률: {profit_rate:.2f}%)"
                )
        
        # 추가 매수 횟수 체크
        if self.execution_count >= max_additions:
            return ManagementExecutionResult.hold(f"최대 불타기 횟수 도달 ({max_additions}회)")
        
        # 불타기 조건 확인
        required_profit = trigger_profit_rate * (self.execution_count + 1)
        if position.is_profitable() and profit_rate >= required_profit:
            return ManagementExecutionResult.success(
                SignalType.ADD_BUY,
                f"불타기 조건 충족 (수익률: {profit_rate:.2f}%, 기준: {required_profit:.2f}%)",
                addition_count=self.execution_count + 1
            )
        
        return ManagementExecutionResult.hold("불타기 조건 미충족")
    
    def _execute_trailing_stop(self, position: PositionState) -> ManagementExecutionResult:
        """트레일링 스탑 실행 로직"""
        trail_distance = self.parameters["trail_distance"]
        activation_profit = self.parameters["activation_profit"]
        
        profit_rate = position.get_profit_rate()
        
        # 트레일링 스탑 활성화 확인
        if profit_rate < activation_profit:
            return ManagementExecutionResult.hold(f"트레일링 스탑 미활성화 (수익률: {profit_rate:.2f}%)")
        
        # 최고가 기록 업데이트 (실제로는 별도 서비스에서 관리)
        highest_price = position.highest_price or position.current_price
        if position.current_price > highest_price:
            highest_price = position.current_price
        
        # 트레일링 스탑 가격 계산
        trail_distance_decimal = Decimal(str(trail_distance))
        stop_price = highest_price * (Decimal("1") - trail_distance_decimal / Decimal("100"))
        
        if position.current_price <= stop_price:
            return ManagementExecutionResult.success(
                SignalType.CLOSE_POSITION,
                f"트레일링 스탑 발동 (현재가: {position.current_price}, 손절가: {stop_price})",
                stop_price=float(stop_price),
                highest_price=float(highest_price)
            )
        
        return ManagementExecutionResult.hold("트레일링 스탑 조건 미충족")
    
    def _execute_fixed_stop_take(self, position: PositionState) -> ManagementExecutionResult:
        """고정 손절/익절 실행 로직"""
        stop_loss_rate = self.parameters["stop_loss_rate"]
        take_profit_rate = self.parameters["take_profit_rate"]
        
        profit_rate = position.get_profit_rate()
        
        # 손절선 체크
        if profit_rate <= -stop_loss_rate:
            return ManagementExecutionResult.success(
                SignalType.CLOSE_POSITION,
                f"손절선 도달 (손실률: {abs(profit_rate):.2f}%)"
            )
        
        # 익절선 체크
        if profit_rate >= take_profit_rate:
            return ManagementExecutionResult.success(
                SignalType.CLOSE_POSITION,
                f"익절선 도달 (수익률: {profit_rate:.2f}%)"
            )
        
        return ManagementExecutionResult.hold("손절/익절 조건 미충족")
    
    def _execute_time_based_exit(self, position: PositionState) -> ManagementExecutionResult:
        """시간 기반 청산 실행 로직"""
        max_holding_hours = self.parameters["max_holding_hours"]
        
        holding_time = position.get_holding_time()
        holding_hours = holding_time.total_seconds() / 3600
        
        if holding_hours >= max_holding_hours:
            return ManagementExecutionResult.success(
                SignalType.CLOSE_POSITION,
                f"최대 보유 시간 초과 (보유: {holding_hours:.1f}시간, 제한: {max_holding_hours}시간)",
                holding_hours=holding_hours
            )
        
        return ManagementExecutionResult.hold(f"보유 시간 미달 ({holding_hours:.1f}/{max_holding_hours}시간)")
    
    def _execute_partial_take_profit(self, position: PositionState) -> ManagementExecutionResult:
        """부분 익절 실행 로직"""
        profit_levels = self.parameters["profit_levels"]
        sell_ratios = self.parameters["sell_ratios"]
        
        profit_rate = position.get_profit_rate()
        
        # 실행된 레벨 추적 (실제로는 별도 상태 관리 필요)
        executed_levels = self.parameters.get("executed_levels", set())
        
        for i, level in enumerate(profit_levels):
            if profit_rate >= level and i not in executed_levels:
                # 마지막 레벨이면 전체 청산
                if i == len(profit_levels) - 1:
                    return ManagementExecutionResult.success(
                        SignalType.CLOSE_POSITION,
                        f"최종 익절 레벨 도달 (수익률: {profit_rate:.2f}%)",
                        level=i + 1,
                        total_levels=len(profit_levels)
                    )
                else:
                    return ManagementExecutionResult.success(
                        SignalType.ADD_SELL,
                        f"부분 익절 레벨 {i + 1} 도달 (수익률: {profit_rate:.2f}%)",
                        sell_ratio=sell_ratios[i],
                        level=i + 1
                    )
        
        return ManagementExecutionResult.hold("부분 익절 조건 미충족")
    
    def activate(self) -> None:
        """관리 규칙 활성화"""
        if not self.is_active:
            self.is_active = True
            self.updated_at = datetime.now()
            self._record_domain_event("management_rule_activated", {
                "rule_id": self.rule_id
            })
    
    def deactivate(self) -> None:
        """관리 규칙 비활성화"""
        if self.is_active:
            self.is_active = False
            self.updated_at = datetime.now()
            self._record_domain_event("management_rule_deactivated", {
                "rule_id": self.rule_id
            })
    
    def update_parameters(self, new_parameters: Dict[str, Any]) -> None:
        """파라미터 업데이트"""
        old_parameters = self.parameters.copy()
        self.parameters.update(new_parameters)
        self.updated_at = datetime.now()
        
        # 업데이트 후 유효성 재검증
        try:
            self._validate_parameters()
        except InvalidManagementRuleError:
            # 롤백
            self.parameters = old_parameters
            raise
        
        self._record_domain_event("management_rule_updated", {
            "rule_id": self.rule_id,
            "old_parameters": old_parameters,
            "new_parameters": self.parameters
        })
    
    def get_status_summary(self) -> Dict[str, Any]:
        """관리 규칙 상태 요약"""
        return {
            "rule_id": self.rule_id,
            "management_type": self.management_type.get_display_name(),
            "is_active": self.is_active,
            "priority": self.priority,
            "execution_count": self.execution_count,
            "last_executed": self.last_executed_at.isoformat() if self.last_executed_at else None,
            "parameters": self.parameters
        }
    
    def _record_domain_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """도메인 이벤트 기록"""
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "aggregate_id": self.rule_id,
            "event_data": event_data
        }
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List[Dict[str, Any]]:
        """도메인 이벤트 목록 반환"""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """도메인 이벤트 초기화"""
        self._domain_events.clear()


# 팩토리 함수들
def create_pyramid_buying_rule(rule_id: str, trigger_drop_rate: float = 5.0, 
                             max_additions: int = 5, absolute_stop_loss: float = 15.0) -> ManagementRule:
    """물타기 관리 규칙 생성"""
    parameters = {
        "trigger_drop_rate": trigger_drop_rate,
        "max_additions": max_additions,
        "absolute_stop_loss": absolute_stop_loss
    }
    
    return ManagementRule(
        rule_id=rule_id,
        management_type=ManagementType.PYRAMID_BUYING,
        parameters=parameters
    )


def create_scale_in_buying_rule(rule_id: str, trigger_profit_rate: float = 3.0,
                               max_additions: int = 3, profit_target: float = 20.0) -> ManagementRule:
    """불타기 관리 규칙 생성"""
    parameters = {
        "trigger_profit_rate": trigger_profit_rate,
        "max_additions": max_additions,
        "profit_target": profit_target
    }
    
    return ManagementRule(
        rule_id=rule_id,
        management_type=ManagementType.SCALE_IN_BUYING,
        parameters=parameters
    )


def create_trailing_stop_rule(rule_id: str, trail_distance: float = 5.0,
                             activation_profit: float = 2.0) -> ManagementRule:
    """트레일링 스탑 관리 규칙 생성"""
    parameters = {
        "trail_distance": trail_distance,
        "activation_profit": activation_profit
    }
    
    return ManagementRule(
        rule_id=rule_id,
        management_type=ManagementType.TRAILING_STOP,
        parameters=parameters
    )


def create_fixed_stop_take_rule(rule_id: str, stop_loss_rate: float = 5.0,
                               take_profit_rate: float = 10.0) -> ManagementRule:
    """고정 손절/익절 관리 규칙 생성"""
    parameters = {
        "stop_loss_rate": stop_loss_rate,
        "take_profit_rate": take_profit_rate
    }
    
    return ManagementRule(
        rule_id=rule_id,
        management_type=ManagementType.FIXED_STOP_TAKE,
        parameters=parameters
    )
