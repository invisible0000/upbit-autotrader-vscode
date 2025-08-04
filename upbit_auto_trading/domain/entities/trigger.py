#!/usr/bin/env python3
"""
트리거 도메인 엔티티 (Trigger Domain Entity)
====================================================

트리거는 매매 신호 생성을 위한 조건을 표현하는 도메인 엔티티입니다.
기존 trigger_builder 시스템의 조건 생성 로직을 순수한 도메인 모델로 추상화합니다.

Design Principles:
- DDD Entity: 고유 식별자(TriggerId)를 가진 도메인 엔티티
- Business Logic Encapsulation: 조건 평가, 호환성 검증, 표현 로직 캡슐화
- Immutability: 생성 후 변경 불가능한 구조로 안정성 보장
- Domain Events: 트리거 생성, 평가 완료 등의 도메인 이벤트 발생

Value Objects Used:
- TriggerId: 트리거 고유 식별자
- ComparisonOperator: 비교 연산자
- TriggerType: 트리거 유형 (진입/관리/청산)
- TradingVariable: 트레이딩 변수 정보
"""

from dataclasses import dataclass, field
from typing import Union, Dict, Any, List, TYPE_CHECKING
from enum import Enum
from datetime import datetime

# Domain imports
from ..value_objects.trigger_id import TriggerId
from ..value_objects.comparison_operator import ComparisonOperator
from ..exceptions.domain_exceptions import IncompatibleTriggerError

if TYPE_CHECKING:
    from typing import Any as MarketData  # 실제 구현에서는 MarketData 클래스로 교체


class TriggerType(Enum):
    """트리거 유형 분류"""
    ENTRY = "entry"         # 진입 트리거 (포지션 없을 때 신호 생성)
    MANAGEMENT = "management"  # 관리 트리거 (활성 포지션 관리)
    EXIT = "exit"           # 청산 트리거 (포지션 종료)
    
    def get_display_name(self) -> str:
        """표시용 한글 이름 반환"""
        display_names = {
            self.ENTRY: "진입",
            self.MANAGEMENT: "관리",
            self.EXIT: "청산"
        }
        return display_names[self]
    
    def requires_position(self) -> bool:
        """포지션이 필요한 트리거 타입인지 확인"""
        return self in [self.MANAGEMENT, self.EXIT]


@dataclass(frozen=True)
class TradingVariable:
    """트레이딩 변수 값 객체 - 기존 variable_definitions.py 시스템을 도메인 모델로 추상화"""
    variable_id: str
    display_name: str
    purpose_category: str    # trend, momentum, volatility, volume, price
    chart_category: str      # overlay, subplot
    comparison_group: str    # price_comparable, percentage_comparable, zero_centered
    
    def __post_init__(self):
        """변수 유효성 검증"""
        if not self.variable_id or len(self.variable_id) < 1:
            raise ValueError("변수 ID는 최소 1자 이상이어야 합니다")
        
        if not self.display_name:
            raise ValueError("표시 이름은 필수입니다")
        
        # 카테고리 유효성 검증
        valid_purpose_categories = {'trend', 'momentum', 'volatility', 'volume', 'price'}
        if self.purpose_category not in valid_purpose_categories:
            raise ValueError(f"잘못된 목적 카테고리: {self.purpose_category}")
        
        valid_chart_categories = {'overlay', 'subplot'}
        if self.chart_category not in valid_chart_categories:
            raise ValueError(f"잘못된 차트 카테고리: {self.chart_category}")
        
        valid_comparison_groups = {'price_comparable', 'percentage_comparable', 'zero_centered', 'volume_comparable'}
        if self.comparison_group not in valid_comparison_groups:
            raise ValueError(f"잘못된 비교 그룹: {self.comparison_group}")
    
    def is_compatible_with(self, other: 'TradingVariable') -> bool:
        """다른 변수와의 호환성 확인 - 기존 CompatibilityValidator 로직 통합"""
        # 같은 comparison_group = 직접 비교 가능
        return self.comparison_group == other.comparison_group
    
    def get_compatibility_score(self, other: 'TradingVariable') -> float:
        """호환성 점수 (0.0~1.0) - 기존 시스템의 신뢰도 점수 개념"""
        if self.is_compatible_with(other):
            return 1.0
        
        # 부분 호환성 검사 (정규화 가능한 조합)
        partial_compatible_pairs = [
            ('price_comparable', 'percentage_comparable'),  # 가격 vs 백분율 (정규화 가능)
            ('percentage_comparable', 'zero_centered')      # 백분율 vs 0중심 (일부 가능)
        ]
        
        current_pair = (self.comparison_group, other.comparison_group)
        reverse_pair = (other.comparison_group, self.comparison_group)
        
        if current_pair in partial_compatible_pairs or reverse_pair in partial_compatible_pairs:
            return 0.5  # 부분 호환 (경고와 함께 허용)
        
        return 0.0  # 완전 비호환


@dataclass
class TriggerEvaluationResult:
    """트리거 평가 결과"""
    trigger_id: TriggerId
    is_triggered: bool
    evaluation_time: datetime
    market_data_snapshot: Dict[str, Any] = field(default_factory=dict)
    evaluation_details: str = ""
    
    @classmethod
    def create_success(cls, trigger_id: TriggerId, details: str = "") -> 'TriggerEvaluationResult':
        """성공 결과 생성"""
        return cls(
            trigger_id=trigger_id,
            is_triggered=True,
            evaluation_time=datetime.now(),
            evaluation_details=details
        )
    
    @classmethod
    def create_failure(cls, trigger_id: TriggerId, details: str = "") -> 'TriggerEvaluationResult':
        """실패 결과 생성"""
        return cls(
            trigger_id=trigger_id,
            is_triggered=False,
            evaluation_time=datetime.now(),
            evaluation_details=details
        )


@dataclass
class Trigger:
    """
    트리거 도메인 엔티티
    
    트리거는 매매 신호를 생성하기 위한 조건을 표현합니다.
    기존 trigger_builder 시스템의 복잡한 로직을 순수한 도메인 모델로 추상화했습니다.
    
    Business Rules:
    1. 트리거는 생성 후 변경할 수 없습니다 (불변성)
    2. 진입 트리거는 포지션이 없을 때만 동작
    3. 관리/청산 트리거는 활성 포지션이 있을 때만 동작
    4. 변수 간 호환성 검증을 통과해야 유효한 트리거
    """
    trigger_id: TriggerId
    trigger_type: TriggerType
    variable: TradingVariable
    operator: ComparisonOperator
    target_value: Union[float, TradingVariable]  # 고정값 또는 다른 변수와 비교
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    # 도메인 이벤트 추적
    _domain_events: List[Dict[str, Any]] = field(default_factory=list, init=False)
    
    def __post_init__(self):
        """트리거 생성 시 비즈니스 규칙 검증"""
        self._validate_trigger_configuration()
        self._emit_domain_event("trigger_created", {
            "trigger_id": str(self.trigger_id),
            "trigger_type": self.trigger_type.value,
            "variable_id": self.variable.variable_id
        })
    
    def _validate_trigger_configuration(self):
        """트리거 설정 유효성 검증"""
        # 외부 변수와 비교하는 경우 호환성 검증
        if isinstance(self.target_value, TradingVariable):
            if not self.variable.is_compatible_with(self.target_value):
                compatibility_score = self.variable.get_compatibility_score(self.target_value)
                if compatibility_score == 0.0:
                    raise IncompatibleTriggerError(
                        f"변수 '{self.variable.display_name}'과 '{self.target_value.display_name}'는 "
                        f"호환되지 않습니다 (그룹: {self.variable.comparison_group} vs {self.target_value.comparison_group})"
                    )
        
        # 파라미터 기본값 설정
        if not self.parameters:
            self.parameters = self._get_default_parameters()
    
    def _get_default_parameters(self) -> Dict[str, Any]:
        """변수 타입에 따른 기본 파라미터 반환"""
        defaults = {
            "RSI": {"period": 14},
            "SMA": {"period": 20},
            "EMA": {"period": 20},
            "MACD": {"fast": 12, "slow": 26, "signal": 9},
            "BB": {"period": 20, "std_dev": 2.0},
            "STOCH": {"k_period": 14, "d_period": 3}
        }
        return defaults.get(self.variable.variable_id, {})
    
    def evaluate(self, market_data: 'MarketData') -> TriggerEvaluationResult:
        """
        트리거 조건 평가 (EvaluationService 위임)
        
        실제 시장 데이터를 받아 트리거 조건이 만족되는지 평가합니다.
        TriggerEvaluationService로 위임하여 실제 평가 로직을 수행합니다.
        """
        try:
            # 순환 참조 방지를 위한 지연 import
            from ..services.trigger_evaluation_service import TriggerEvaluationService
            
            # TriggerEvaluationService 사용하여 평가
            evaluation_service = TriggerEvaluationService()
            evaluation_result = evaluation_service.evaluate_trigger(self, market_data)
            
            # EvaluationResult를 TriggerEvaluationResult로 변환
            if evaluation_result.status.value == "success":
                result = TriggerEvaluationResult.create_success(
                    self.trigger_id,
                    evaluation_result.message or f"평가 완료: {self.to_human_readable()}"
                )
                is_triggered = evaluation_result.result
            else:
                result = TriggerEvaluationResult.create_failure(
                    self.trigger_id,
                    evaluation_result.message or "평가 실패"
                )
                is_triggered = False
            
            # 도메인 이벤트 발생
            self._emit_domain_event("trigger_evaluated", {
                "trigger_id": str(self.trigger_id),
                "is_triggered": is_triggered,
                "evaluation_time": result.evaluation_time.isoformat(),
                "service_result": {
                    "status": evaluation_result.status.value,
                    "current_value": evaluation_result.current_value,
                    "target_value": evaluation_result.target_value,
                    "operator": evaluation_result.operator
                }
            })
            
            return result
            
        except ImportError as e:
            # TriggerEvaluationService를 사용할 수 없는 경우 fallback
            error_result = TriggerEvaluationResult.create_failure(
                self.trigger_id,
                f"평가 서비스 로드 실패: {str(e)}"
            )
            
            self._emit_domain_event("trigger_evaluation_service_unavailable", {
                "trigger_id": str(self.trigger_id),
                "error": str(e)
            })
            
            return error_result
            
        except Exception as e:
            error_result = TriggerEvaluationResult.create_failure(
                self.trigger_id,
                f"평가 실패: {str(e)}"
            )
            
            self._emit_domain_event("trigger_evaluation_failed", {
                "trigger_id": str(self.trigger_id),
                "error": str(e)
            })
            
            return error_result
    
    def to_human_readable(self) -> str:
        """사람이 읽기 쉬운 형태로 조건 표현"""
        if isinstance(self.target_value, TradingVariable):
            # 변수 간 비교
            return f"{self.variable.display_name} {self.operator.get_display_name()} {self.target_value.display_name}"
        else:
            # 고정값과 비교
            return f"{self.variable.display_name} {self.operator.get_display_name()} {self.target_value}"
    
    def get_technical_expression(self) -> str:
        """기술적 표현식 반환 (코드/공식 형태)"""
        param_str = ""
        if self.parameters:
            param_list = [f"{k}={v}" for k, v in self.parameters.items()]
            param_str = f"({', '.join(param_list)})"
        
        variable_expr = f"{self.variable.variable_id}{param_str}"
        
        if isinstance(self.target_value, TradingVariable):
            target_expr = f"{self.target_value.variable_id}"
        else:
            target_expr = str(self.target_value)
        
        return f"{variable_expr} {self.operator.value} {target_expr}"
    
    def get_compatibility_info(self) -> Dict[str, Any]:
        """호환성 정보 반환"""
        if isinstance(self.target_value, TradingVariable):
            compatibility_score = self.variable.get_compatibility_score(self.target_value)
            return {
                "has_external_variable": True,
                "is_compatible": self.variable.is_compatible_with(self.target_value),
                "compatibility_score": compatibility_score,
                "base_group": self.variable.comparison_group,
                "target_group": self.target_value.comparison_group
            }
        else:
            return {
                "has_external_variable": False,
                "is_compatible": True,
                "compatibility_score": 1.0,
                "base_group": self.variable.comparison_group,
                "target_group": "fixed_value"
            }
    
    def deactivate(self):
        """트리거 비활성화"""
        if self.is_active:
            object.__setattr__(self, 'is_active', False)  # frozen dataclass 우회
            self._emit_domain_event("trigger_deactivated", {
                "trigger_id": str(self.trigger_id),
                "deactivated_at": datetime.now().isoformat()
            })
    
    def activate(self):
        """트리거 활성화"""
        if not self.is_active:
            object.__setattr__(self, 'is_active', True)  # frozen dataclass 우회
            self._emit_domain_event("trigger_activated", {
                "trigger_id": str(self.trigger_id),
                "activated_at": datetime.now().isoformat()
            })
    
    def _emit_domain_event(self, event_type: str, event_data: Dict[str, Any]):
        """도메인 이벤트 발생"""
        event = {
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.now(),
            "aggregate_id": str(self.trigger_id)
        }
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List[Dict[str, Any]]:
        """발생한 도메인 이벤트 목록 반환"""
        return self._domain_events.copy()
    
    def clear_domain_events(self):
        """도메인 이벤트 목록 초기화"""
        self._domain_events.clear()
    
    def __eq__(self, other):
        """트리거 동등성 비교 - ID 기반"""
        if not isinstance(other, Trigger):
            return False
        return self.trigger_id == other.trigger_id
    
    def __hash__(self):
        """해시 값 - ID 기반"""
        return hash(self.trigger_id)
    
    def __str__(self):
        """문자열 표현"""
        return f"Trigger({self.trigger_id.value}: {self.to_human_readable()})"
    
    def __repr__(self):
        """개발자용 표현"""
        return (f"Trigger(id={self.trigger_id.value}, type={self.trigger_type.value}, "
                f"variable={self.variable.variable_id}, operator={self.operator.value}, "
                f"target={self.target_value}, active={self.is_active})")


# 팩토리 함수들
def create_rsi_entry_trigger() -> Trigger:
    """RSI 과매도 진입 트리거 생성 - 기본 7규칙 전략용"""
    rsi_variable = TradingVariable(
        variable_id="RSI",
        display_name="RSI 지표",
        purpose_category="momentum",
        chart_category="subplot", 
        comparison_group="percentage_comparable"
    )
    
    return Trigger(
        trigger_id=TriggerId.generate_entry_trigger("RSI_OVERSOLD"),
        trigger_type=TriggerType.ENTRY,
        variable=rsi_variable,
        operator=ComparisonOperator.LESS_THAN,
        target_value=30.0,
        parameters={"period": 14}
    )


def create_sma_crossover_trigger() -> Trigger:
    """이동평균 교차 트리거 생성 예시"""
    close_variable = TradingVariable(
        variable_id="Close",
        display_name="종가",
        purpose_category="price",
        chart_category="overlay",
        comparison_group="price_comparable"
    )
    
    sma_variable = TradingVariable(
        variable_id="SMA", 
        display_name="단순이동평균",
        purpose_category="trend",
        chart_category="overlay",
        comparison_group="price_comparable"
    )
    
    return Trigger(
        trigger_id=TriggerId.generate_entry_trigger("PRICE_ABOVE_SMA"),
        trigger_type=TriggerType.ENTRY,
        variable=close_variable,
        operator=ComparisonOperator.GREATER_THAN,
        target_value=sma_variable,
        parameters={"sma_period": 20}
    )
