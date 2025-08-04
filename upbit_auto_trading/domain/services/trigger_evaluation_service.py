"""
Domain Service for Trigger Evaluation

트리거 조건 평가를 담당하는 도메인 서비스
기존 business_logic 계층의 신호 생성 로직을 도메인 서비스로 추상화
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from upbit_auto_trading.domain.entities.trigger import Trigger, TradingVariable


class EvaluationStatus(Enum):
    """평가 상태"""
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class MarketData:
    """
    시장 데이터 Value Object
    
    기존 DataFrame 기반 데이터를 단일 시점 데이터로 추상화
    Infrastructure 계층에서 실제 데이터 소스와 연동
    """
    symbol: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    
    # 기술적 지표 (Infrastructure에서 계산된 값)
    indicators: Dict[str, float] = field(default_factory=dict)
    
    # 추가 메타데이터
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_indicator_value(self, variable_id: str, parameters: Dict[str, Any] = None) -> Optional[float]:
        """
        지표값 조회
        
        Infrastructure 계층에서 계산된 지표값을 조회
        파라미터를 포함한 지표 키 생성
        """
        if not parameters:
            # 기본 지표명으로 조회
            return self.indicators.get(variable_id)
        
        # 파라미터를 포함한 지표 키 생성 (예: RSI_14, SMA_20)
        param_str = "_".join(str(v) for v in parameters.values())
        indicator_key = f"{variable_id}_{param_str}"
        
        return self.indicators.get(indicator_key) or self.indicators.get(variable_id)
    
    def get_price_value(self, price_type: str) -> float:
        """가격 데이터 조회"""
        price_map = {
            "Open": self.open_price,
            "High": self.high_price,
            "Low": self.low_price,
            "Close": self.close_price,
            "Volume": self.volume
        }
        return price_map.get(price_type, self.close_price)


@dataclass(frozen=True)
class EvaluationResult:
    """
    트리거 평가 결과 Value Object
    
    단일 트리거의 평가 결과를 표현
    기존 시스템의 신호 생성 결과와 호환
    """
    trigger_id: str
    status: EvaluationStatus
    result: bool
    current_value: float
    target_value: float
    operator: str
    message: str
    timestamp: datetime
    
    # 추가 메타데이터
    variable_info: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    error_details: Optional[str] = None
    
    @classmethod
    def create_success(cls, trigger_id: str, result: bool, current_value: float,
                       target_value: float, operator: str, message: str,
                       timestamp: datetime, **kwargs) -> 'EvaluationResult':
        """성공 결과 생성"""
        return cls(
            trigger_id=trigger_id,
            status=EvaluationStatus.SUCCESS,
            result=result,
            current_value=current_value,
            target_value=target_value,
            operator=operator,
            message=message,
            timestamp=timestamp,
            **kwargs
        )
    
    @classmethod
    def create_error(cls, trigger_id: str, error_message: str,
                     timestamp: datetime, **kwargs) -> 'EvaluationResult':
        """오류 결과 생성"""
        return cls(
            trigger_id=trigger_id,
            status=EvaluationStatus.ERROR,
            result=False,
            current_value=0.0,
            target_value=0.0,
            operator="",
            message=f"평가 오류: {error_message}",
            timestamp=timestamp,
            error_details=error_message,
            **kwargs
        )


class TriggerEvaluationService:
    """
    Domain Service: 트리거 조건 평가
    
    책임:
    - 단일 트리거 조건 평가
    - 복수 트리거 일괄 평가
    - 변수값 계산 및 비교 연산 수행
    - 기존 business_logic 시스템과의 브릿지 역할
    """
    
    def __init__(self):
        self._variable_calculators = self._init_variable_calculators()
    
    def evaluate_trigger(self, trigger: Trigger, market_data: MarketData) -> EvaluationResult:
        """
        단일 트리거 조건 평가
        
        기존 StrategyInterface.generate_signals() 로직을 단일 트리거로 분해
        """
        start_time = datetime.now()
        
        try:
            # 비활성 트리거는 건너뛰기
            if not trigger.is_active:
                return EvaluationResult(
                    trigger_id=str(trigger.trigger_id),
                    status=EvaluationStatus.SKIPPED,
                    result=False,
                    current_value=0.0,
                    target_value=0.0,
                    operator=trigger.operator.value,
                    message="비활성 트리거",
                    timestamp=start_time
                )
            
            # 1. 현재 변수값 계산
            current_value = self._calculate_variable_value(trigger.variable, market_data)
            
            # 2. 대상값 계산 (고정값 또는 다른 변수값)
            target_value = self._calculate_target_value(trigger.target_value, market_data)
            
            # 3. 비교 연산 수행 (기존 ComparisonOperator.evaluate 활용)
            comparison_result = trigger.operator.evaluate(current_value, target_value)
            
            # 4. 결과 메시지 생성
            message = self._generate_result_message(
                trigger.variable.display_name, current_value, 
                trigger.operator.value, target_value, comparison_result
            )
            
            # 5. 실행 시간 계산
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return EvaluationResult.create_success(
                trigger_id=str(trigger.trigger_id),
                result=comparison_result,
                current_value=current_value,
                target_value=target_value,
                operator=trigger.operator.value,
                message=message,
                timestamp=market_data.timestamp,
                variable_info={
                    "variable_id": trigger.variable.variable_id,
                    "display_name": trigger.variable.display_name,
                    "comparison_group": trigger.variable.comparison_group,
                    "parameters": trigger.parameters
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return EvaluationResult.create_error(
                trigger_id=str(trigger.trigger_id),
                error_message=str(e),
                timestamp=market_data.timestamp,
                execution_time_ms=execution_time
            )
    
    def evaluate_multiple_triggers(self, triggers: List[Trigger], 
                                  market_data: MarketData) -> List[EvaluationResult]:
        """
        복수 트리거 일괄 평가
        
        기존 전략의 여러 조건을 동시에 평가
        """
        results = []
        
        for trigger in triggers:
            try:
                result = self.evaluate_trigger(trigger, market_data)
                results.append(result)
            except Exception as e:
                # 개별 트리거 평가 실패 시에도 계속 진행
                error_result = EvaluationResult.create_error(
                    trigger_id=str(trigger.trigger_id),
                    error_message=f"일괄 평가 중 오류: {str(e)}",
                    timestamp=market_data.timestamp
                )
                results.append(error_result)
        
        return results
    
    def _calculate_variable_value(self, variable: TradingVariable, market_data: MarketData) -> float:
        """
        변수값 계산
        
        기존 business_logic의 지표 계산 로직을 도메인 서비스로 추상화
        실제 지표 계산은 Infrastructure 계층에서 수행된 결과를 사용
        """
        variable_id = variable.variable_id
        
        # 1. 기본 가격 데이터 (OHLCV)
        if variable_id in ["Open", "High", "Low", "Close", "Volume"]:
            return market_data.get_price_value(variable_id)
        
        # 2. 기술적 지표 (Infrastructure에서 계산된 값 조회)
        # 변수의 parameters를 사용하여 지표 조회
        calculator = self._variable_calculators.get(variable_id)
        if calculator:
            return calculator(variable, market_data)
        
        # 3. 기본 지표 조회 시도
        indicator_value = market_data.get_indicator_value(variable_id, variable.parameters)
        if indicator_value is not None:
            return indicator_value
        
        # 4. 변수를 찾을 수 없는 경우
        raise ValueError(f"알 수 없는 변수: {variable_id}")
    
    def _calculate_target_value(self, target: Union[float, TradingVariable], 
                               market_data: MarketData) -> float:
        """대상값 계산 (고정값 또는 변수값)"""
        if isinstance(target, (int, float)):
            return float(target)
        elif isinstance(target, TradingVariable):
            return self._calculate_variable_value(target, market_data)
        else:
            try:
                return float(target)
            except (ValueError, TypeError):
                raise ValueError(f"잘못된 대상값 타입: {type(target)}")
    
    def _generate_result_message(self, variable_name: str, current_value: float,
                                operator: str, target_value: float, result: bool) -> str:
        """결과 메시지 생성"""
        status_icon = "✅" if result else "❌"
        return f"{status_icon} {variable_name}: {current_value:.4f} {operator} {target_value:.4f}"
    
    def _init_variable_calculators(self) -> Dict[str, callable]:
        """
        변수별 계산기 초기화
        
        기존 business_logic의 지표 계산 로직과 브릿지
        Infrastructure 계층에서 실제 계산이 이루어진 후 결과 조회
        """
        return {
            # RSI 계산기
            "RSI": self._calculate_rsi,
            "RSI_INDICATOR": self._calculate_rsi,
            
            # 이동평균 계산기
            "SMA": self._calculate_sma,
            "EMA": self._calculate_ema,
            
            # MACD 계산기
            "MACD": self._calculate_macd,
            "MACD_SIGNAL": self._calculate_macd_signal,
            "MACD_HISTOGRAM": self._calculate_macd_histogram,
            
            # 볼린저 밴드 계산기
            "BB_UPPER": self._calculate_bb_upper,
            "BB_MIDDLE": self._calculate_bb_middle,
            "BB_LOWER": self._calculate_bb_lower,
            
            # 스토캐스틱 계산기
            "STOCH_K": self._calculate_stoch_k,
            "STOCH_D": self._calculate_stoch_d,
        }
    
    def _calculate_rsi(self, variable: TradingVariable, market_data: MarketData) -> float:
        """RSI 계산 (Infrastructure 계층 연동)"""
        period = variable.parameters.get("period", 14)
        
        # Infrastructure에서 계산된 RSI 값 조회 시도
        rsi_value = market_data.get_indicator_value("RSI", {"period": period})
        
        if rsi_value is not None:
            return rsi_value
        
        # 임시 구현: 실제로는 Infrastructure 계층에서 ta-lib 사용
        # 기존 business_logic과 호환성을 위한 기본값 반환
        return 50.0  # 중립값
    
    def _calculate_sma(self, variable: TradingVariable, market_data: MarketData) -> float:
        """단순 이동평균 계산"""
        period = variable.parameters.get("period", 20)
        sma_value = market_data.get_indicator_value("SMA", {"period": period})
        return sma_value if sma_value is not None else market_data.close_price
    
    def _calculate_ema(self, variable: TradingVariable, market_data: MarketData) -> float:
        """지수 이동평균 계산"""
        period = variable.parameters.get("period", 20)
        ema_value = market_data.get_indicator_value("EMA", {"period": period})
        return ema_value if ema_value is not None else market_data.close_price
    
    def _calculate_macd(self, variable: TradingVariable, market_data: MarketData) -> float:
        """MACD 라인 계산"""
        fast = variable.parameters.get("fast", 12)
        slow = variable.parameters.get("slow", 26)
        macd_value = market_data.get_indicator_value("MACD", {"fast": fast, "slow": slow})
        return macd_value if macd_value is not None else 0.0
    
    def _calculate_macd_signal(self, variable: TradingVariable, market_data: MarketData) -> float:
        """MACD 신호선 계산"""
        signal = variable.parameters.get("signal", 9)
        signal_value = market_data.get_indicator_value("MACD_SIGNAL", {"signal": signal})
        return signal_value if signal_value is not None else 0.0
    
    def _calculate_macd_histogram(self, variable: TradingVariable, market_data: MarketData) -> float:
        """MACD 히스토그램 계산"""
        histogram_value = market_data.get_indicator_value("MACD_HISTOGRAM")
        return histogram_value if histogram_value is not None else 0.0
    
    def _calculate_bb_upper(self, variable: TradingVariable, market_data: MarketData) -> float:
        """볼린저 밴드 상단 계산"""
        period = variable.parameters.get("period", 20)
        std_dev = variable.parameters.get("std_dev", 2.0)
        bb_upper = market_data.get_indicator_value("BB_UPPER", {"period": period, "std_dev": std_dev})
        return bb_upper if bb_upper is not None else market_data.close_price * 1.02
    
    def _calculate_bb_middle(self, variable: TradingVariable, market_data: MarketData) -> float:
        """볼린저 밴드 중간선 계산"""
        period = variable.parameters.get("period", 20)
        bb_middle = market_data.get_indicator_value("BB_MIDDLE", {"period": period})
        return bb_middle if bb_middle is not None else market_data.close_price
    
    def _calculate_bb_lower(self, variable: TradingVariable, market_data: MarketData) -> float:
        """볼린저 밴드 하단 계산"""
        period = variable.parameters.get("period", 20)
        std_dev = variable.parameters.get("std_dev", 2.0)
        bb_lower = market_data.get_indicator_value("BB_LOWER", {"period": period, "std_dev": std_dev})
        return bb_lower if bb_lower is not None else market_data.close_price * 0.98
    
    def _calculate_stoch_k(self, variable: TradingVariable, market_data: MarketData) -> float:
        """스토캐스틱 %K 계산"""
        k_period = variable.parameters.get("k_period", 14)
        stoch_k = market_data.get_indicator_value("STOCH_K", {"k_period": k_period})
        return stoch_k if stoch_k is not None else 50.0
    
    def _calculate_stoch_d(self, variable: TradingVariable, market_data: MarketData) -> float:
        """스토캐스틱 %D 계산"""
        d_period = variable.parameters.get("d_period", 3)
        stoch_d = market_data.get_indicator_value("STOCH_D", {"d_period": d_period})
        return stoch_d if stoch_d is not None else 50.0
