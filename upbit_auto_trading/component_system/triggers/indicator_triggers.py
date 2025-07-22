"""
기술적 지표 기반 트리거 컴포넌트들
Technical Indicator Based Trigger Components

RSI, MACD, 볼린저밴드 등 기술적 지표를 기반으로 한 트리거들
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from ..base import TriggerComponent, ComponentResult, ExecutionContext


@dataclass
class RSITriggerConfig:
    """RSI 트리거 설정"""
    threshold_type: str = "oversold"  # oversold, overbought, crossover
    threshold_value: float = 30  # RSI 임계값
    period: int = 14  # RSI 계산 기간


class RSITrigger(TriggerComponent):
    """
    RSI 트리거 - 과매수/과매도 상황 감지
    """
    
    def __init__(self, config: RSITriggerConfig):
        super().__init__(
            component_id=f"rsi_{config.threshold_type}_{config.threshold_value}",
            name=f"RSI {config.threshold_type} 트리거",
            description=f"RSI {config.threshold_value} {config.threshold_type} 시 실행"
        )
        self.config = config
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """RSI 조건을 확인하여 트리거 여부 결정"""
        try:
            rsi_value = market_data.get('rsi', 0)
            if rsi_value <= 0:
                return ComponentResult(False, "RSI 데이터 없음")
            
            if self.config.threshold_type == "oversold":
                triggered = rsi_value <= self.config.threshold_value
                message = f"RSI {rsi_value:.1f} {'≤' if triggered else '>'} {self.config.threshold_value} (과매도)"
            elif self.config.threshold_type == "overbought":
                triggered = rsi_value >= self.config.threshold_value
                message = f"RSI {rsi_value:.1f} {'≥' if triggered else '<'} {self.config.threshold_value} (과매수)"
            else:
                return ComponentResult(False, f"지원하지 않는 RSI 트리거 타입: {self.config.threshold_type}")
            
            return ComponentResult(
                triggered,
                message,
                metadata={
                    'trigger_type': 'rsi',
                    'rsi_value': rsi_value,
                    'threshold': self.config.threshold_value,
                    'threshold_type': self.config.threshold_type
                }
            )
            
        except Exception as e:
            return ComponentResult(False, f"RSI 트리거 오류: {str(e)}")


@dataclass
class MACDTriggerConfig:
    """MACD 트리거 설정"""
    signal_type: str = "golden_cross"  # golden_cross, death_cross, divergence
    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9


class MACDTrigger(TriggerComponent):
    """
    MACD 트리거 - MACD 라인과 시그널 라인의 교차 감지
    """
    
    def __init__(self, config: MACDTriggerConfig):
        super().__init__(
            component_id=f"macd_{config.signal_type}",
            name=f"MACD {config.signal_type} 트리거",
            description=f"MACD {config.signal_type} 시 실행"
        )
        self.config = config
        self.previous_macd: Optional[float] = None
        self.previous_signal: Optional[float] = None
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """MACD 교차를 감지하여 트리거 여부 결정"""
        try:
            macd_line = market_data.get('macd_line', 0)
            signal_line = market_data.get('macd_signal', 0)
            
            if macd_line == 0 or signal_line == 0:
                return ComponentResult(False, "MACD 데이터 없음")
            
            # 이전 값이 없으면 현재 값 저장 후 대기
            if self.previous_macd is None or self.previous_signal is None:
                self.previous_macd = macd_line
                self.previous_signal = signal_line
                return ComponentResult(False, "MACD 교차 확인을 위한 이전 데이터 수집 중")
            
            # 교차 감지
            if self.config.signal_type == "golden_cross":
                # 이전: MACD < Signal → 현재: MACD > Signal
                triggered = (self.previous_macd <= self.previous_signal) and (macd_line > signal_line)
                message = f"MACD 골든크로스: {macd_line:.4f} > {signal_line:.4f}"
            elif self.config.signal_type == "death_cross":
                # 이전: MACD > Signal → 현재: MACD < Signal  
                triggered = (self.previous_macd >= self.previous_signal) and (macd_line < signal_line)
                message = f"MACD 데드크로스: {macd_line:.4f} < {signal_line:.4f}"
            else:
                return ComponentResult(False, f"지원하지 않는 MACD 신호 타입: {self.config.signal_type}")
            
            # 이전 값 업데이트
            self.previous_macd = macd_line
            self.previous_signal = signal_line
            
            return ComponentResult(
                triggered,
                message,
                metadata={
                    'trigger_type': 'macd',
                    'macd_line': macd_line,
                    'signal_line': signal_line,
                    'signal_type': self.config.signal_type
                }
            )
            
        except Exception as e:
            return ComponentResult(False, f"MACD 트리거 오류: {str(e)}")


@dataclass
class BollingerBandTriggerConfig:
    """볼린저밴드 트리거 설정"""
    band_type: str = "lower"  # upper, lower, squeeze
    touch_type: str = "touch"  # touch, break, bounce
    period: int = 20
    std_dev: float = 2.0


class BollingerBandTrigger(TriggerComponent):
    """
    볼린저밴드 트리거 - 상/하단 밴드 터치/돌파 감지
    """
    
    def __init__(self, config: BollingerBandTriggerConfig):
        super().__init__(
            component_id=f"bb_{config.band_type}_{config.touch_type}",
            name=f"볼린저밴드 {config.band_type} {config.touch_type} 트리거",
            description=f"볼린저밴드 {config.band_type} 밴드 {config.touch_type} 시 실행"
        )
        self.config = config
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """볼린저밴드 조건을 확인하여 트리거 여부 결정"""
        try:
            current_price = market_data.get('current_price', 0)
            bb_upper = market_data.get('bb_upper', 0)
            bb_lower = market_data.get('bb_lower', 0)
            bb_middle = market_data.get('bb_middle', 0)
            
            if not all([current_price, bb_upper, bb_lower, bb_middle]):
                return ComponentResult(False, "볼린저밴드 데이터 없음")
            
            if self.config.band_type == "lower":
                if self.config.touch_type == "touch":
                    triggered = current_price <= bb_lower
                    message = f"하단밴드 터치: {current_price:,.0f} ≤ {bb_lower:,.0f}"
                elif self.config.touch_type == "break":
                    triggered = current_price < bb_lower
                    message = f"하단밴드 돌파: {current_price:,.0f} < {bb_lower:,.0f}"
                else:
                    return ComponentResult(False, f"지원하지 않는 터치 타입: {self.config.touch_type}")
                    
            elif self.config.band_type == "upper":
                if self.config.touch_type == "touch":
                    triggered = current_price >= bb_upper
                    message = f"상단밴드 터치: {current_price:,.0f} ≥ {bb_upper:,.0f}"
                elif self.config.touch_type == "break":
                    triggered = current_price > bb_upper
                    message = f"상단밴드 돌파: {current_price:,.0f} > {bb_upper:,.0f}"
                else:
                    return ComponentResult(False, f"지원하지 않는 터치 타입: {self.config.touch_type}")
            else:
                return ComponentResult(False, f"지원하지 않는 밴드 타입: {self.config.band_type}")
            
            return ComponentResult(
                triggered,
                message,
                metadata={
                    'trigger_type': 'bollinger_band',
                    'current_price': current_price,
                    'bb_upper': bb_upper,
                    'bb_lower': bb_lower,
                    'bb_middle': bb_middle,
                    'band_type': self.config.band_type,
                    'touch_type': self.config.touch_type
                }
            )
            
        except Exception as e:
            return ComponentResult(False, f"볼린저밴드 트리거 오류: {str(e)}")


@dataclass
class MovingAverageCrossConfig:
    """이동평균 교차 트리거 설정"""
    fast_period: int = 5
    slow_period: int = 20
    cross_direction: str = "golden"  # golden, death, any


class MovingAverageCrossTrigger(TriggerComponent):
    """
    이동평균 교차 트리거 - 단기/장기 이동평균 교차 감지
    """
    
    def __init__(self, config: MovingAverageCrossConfig):
        super().__init__(
            component_id=f"ma_cross_{config.fast_period}_{config.slow_period}_{config.cross_direction}",
            name=f"이동평균 교차 ({config.fast_period}/{config.slow_period}) {config.cross_direction}",
            description=f"MA{config.fast_period}과 MA{config.slow_period}의 {config.cross_direction} 교차 시 실행"
        )
        self.config = config
        self.previous_fast_ma: Optional[float] = None
        self.previous_slow_ma: Optional[float] = None
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """이동평균 교차를 감지하여 트리거 여부 결정"""
        try:
            fast_ma = market_data.get(f'ma_{self.config.fast_period}', 0)
            slow_ma = market_data.get(f'ma_{self.config.slow_period}', 0)
            
            if not fast_ma or not slow_ma:
                return ComponentResult(False, f"이동평균 데이터 없음 (MA{self.config.fast_period}, MA{self.config.slow_period})")
            
            # 이전 값이 없으면 현재 값 저장 후 대기
            if self.previous_fast_ma is None or self.previous_slow_ma is None:
                self.previous_fast_ma = fast_ma
                self.previous_slow_ma = slow_ma
                return ComponentResult(False, "이동평균 교차 확인을 위한 이전 데이터 수집 중")
            
            # 교차 감지
            golden_cross = (self.previous_fast_ma <= self.previous_slow_ma) and (fast_ma > slow_ma)
            death_cross = (self.previous_fast_ma >= self.previous_slow_ma) and (fast_ma < slow_ma)
            
            triggered = False
            cross_type = ""
            
            if self.config.cross_direction == "golden" and golden_cross:
                triggered = True
                cross_type = "골든크로스"
            elif self.config.cross_direction == "death" and death_cross:
                triggered = True
                cross_type = "데드크로스"
            elif self.config.cross_direction == "any" and (golden_cross or death_cross):
                triggered = True
                cross_type = "골든크로스" if golden_cross else "데드크로스"
            
            # 이전 값 업데이트
            self.previous_fast_ma = fast_ma
            self.previous_slow_ma = slow_ma
            
            message = f"MA{self.config.fast_period}({fast_ma:,.0f}) vs MA{self.config.slow_period}({slow_ma:,.0f})"
            if triggered:
                message += f" - {cross_type} 발생!"
            
            return ComponentResult(
                triggered,
                message,
                metadata={
                    'trigger_type': 'moving_average_cross',
                    'fast_ma': fast_ma,
                    'slow_ma': slow_ma,
                    'fast_period': self.config.fast_period,
                    'slow_period': self.config.slow_period,
                    'cross_type': cross_type if triggered else None
                }
            )
            
        except Exception as e:
            return ComponentResult(False, f"이동평균 교차 트리거 오류: {str(e)}")
