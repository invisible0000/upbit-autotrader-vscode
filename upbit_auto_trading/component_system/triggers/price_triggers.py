"""
가격 변화 기반 트리거 컴포넌트들
물타기(피라미딩) 전략의 핵심이 되는 가격 변화 감지 트리거들
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal
from ..base import TriggerComponent, ComponentResult, ExecutionContext


@dataclass 
class PriceChangeConfig:
    """가격 변화 트리거 설정"""
    change_percent: float  # 변화율 (예: -3.0은 3% 하락)
    reference_type: str = "purchase_price"  # purchase_price, market_price, previous_close
    direction: str = "down"  # down, up, any
    reset_on_trigger: bool = True  # 트리거 후 기준점 리셋


class PriceChangeTrigger(TriggerComponent):
    """
    가격 변화 트리거 - 물타기 전략의 핵심
    
    지정된 기준 가격에서 특정 % 변화 시 트리거
    예: 매수가 대비 3% 하락 시 추가 매수
    """
    
    def __init__(self, config: PriceChangeConfig):
        super().__init__(
            component_id=f"price_change_{config.direction}_{config.change_percent}",
            name=f"가격 {config.direction} {abs(config.change_percent)}% 트리거",
            description=f"{config.reference_type}에서 {config.direction} {abs(config.change_percent)}% 변화 시 실행"
        )
        self.config = config
        self.reference_price: Optional[Decimal] = None
        self.last_trigger_time: Optional[str] = None
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """가격 변화를 감지하여 트리거 여부 결정"""
        try:
            current_price = Decimal(str(market_data.get('current_price', 0)))
            if current_price <= 0:
                return ComponentResult(False, "현재 가격 정보 없음")
            
            # 기준 가격 설정
            reference_price = self._get_reference_price(market_data, context)
            if reference_price is None:
                return ComponentResult(False, "기준 가격을 찾을 수 없음")
            
            # 변화율 계산
            change_percent = float((current_price - reference_price) / reference_price * 100)
            
            # 트리거 조건 확인
            should_trigger = self._check_trigger_condition(change_percent)
            
            if should_trigger:
                # 기준점 리셋 (설정 시)
                if self.config.reset_on_trigger:
                    self.reference_price = current_price
                
                self.last_trigger_time = market_data.get('timestamp')
                
                return ComponentResult(
                    True, 
                    f"가격 변화 트리거: {change_percent:.2f}% (기준: {reference_price}, 현재: {current_price})",
                    metadata={
                        'trigger_type': 'price_change',
                        'change_percent': change_percent,
                        'reference_price': float(reference_price),
                        'current_price': float(current_price),
                        'direction': self.config.direction
                    }
                )
            
            return ComponentResult(False, f"변화율 {change_percent:.2f}%는 트리거 조건 미만")
            
        except Exception as e:
            return ComponentResult(False, f"가격 변화 트리거 오류: {str(e)}")
    
    def _get_reference_price(self, market_data: Dict[str, Any], context: ExecutionContext) -> Optional[Decimal]:
        """기준 가격 가져오기"""
        if self.reference_price is not None:
            return self.reference_price
            
        if self.config.reference_type == "purchase_price":
            # 포지션의 평균 매수가
            position = context.get_position()
            if position and position.get('avg_buy_price'):
                price = Decimal(str(position['avg_buy_price']))
                self.reference_price = price
                return price
                
        elif self.config.reference_type == "market_price":
            # 현재 시장가를 기준으로 설정
            current_price = market_data.get('current_price')
            if current_price:
                price = Decimal(str(current_price))
                self.reference_price = price
                return price
                
        elif self.config.reference_type == "previous_close":
            # 전일 종가
            prev_close = market_data.get('previous_close')
            if prev_close:
                price = Decimal(str(prev_close))
                self.reference_price = price
                return price
        
        return None
    
    def _check_trigger_condition(self, change_percent: float) -> bool:
        """트리거 조건 확인"""
        target_percent = self.config.change_percent
        
        if self.config.direction == "down":
            return change_percent <= target_percent
        elif self.config.direction == "up":
            return change_percent >= target_percent
        elif self.config.direction == "any":
            return abs(change_percent) >= abs(target_percent)
        
        return False
    
    def reset(self):
        """트리거 상태 리셋"""
        self.reference_price = None
        self.last_trigger_time = None


@dataclass
class PriceBreakoutConfig:
    """가격 돌파 트리거 설정"""
    resistance_level: float  # 저항선 가격
    support_level: float    # 지지선 가격
    breakout_type: str = "resistance"  # resistance, support, any
    volume_confirmation: bool = False  # 거래량 확인 필요 여부
    min_volume_ratio: float = 1.5  # 최소 거래량 비율


class PriceBreakoutTrigger(TriggerComponent):
    """
    가격 돌파 트리거
    지지선/저항선 돌파 시 트리거
    """
    
    def __init__(self, config: PriceBreakoutConfig):
        super().__init__(
            component_id=f"price_breakout_{config.breakout_type}",
            name=f"가격 돌파 트리거 ({config.breakout_type})",
            description=f"{config.breakout_type} 돌파 시 실행"
        )
        self.config = config
        self.last_trigger_time: Optional[str] = None
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """가격 돌파를 감지하여 트리거 여부 결정"""
        try:
            current_price = float(market_data.get('current_price', 0))
            if current_price <= 0:
                return ComponentResult(False, "현재 가격 정보 없음")
            
            # 돌파 확인
            breakout_detected = False
            breakout_message = ""
            
            if self.config.breakout_type == "resistance":
                if current_price > self.config.resistance_level:
                    breakout_detected = True
                    breakout_message = f"저항선 {self.config.resistance_level} 돌파"
                    
            elif self.config.breakout_type == "support":
                if current_price < self.config.support_level:
                    breakout_detected = True
                    breakout_message = f"지지선 {self.config.support_level} 하향 돌파"
                    
            elif self.config.breakout_type == "any":
                if current_price > self.config.resistance_level:
                    breakout_detected = True
                    breakout_message = f"저항선 {self.config.resistance_level} 돌파"
                elif current_price < self.config.support_level:
                    breakout_detected = True
                    breakout_message = f"지지선 {self.config.support_level} 하향 돌파"
            
            if not breakout_detected:
                return ComponentResult(False, "돌파 조건 미충족")
            
            # 거래량 확인 (옵션)
            if self.config.volume_confirmation:
                volume_confirmed = self._check_volume_confirmation(market_data)
                if not volume_confirmed:
                    return ComponentResult(False, f"{breakout_message} but 거래량 미확인")
            
            self.last_trigger_time = market_data.get('timestamp')
            
            return ComponentResult(
                True,
                breakout_message,
                metadata={
                    'trigger_type': 'price_breakout',
                    'breakout_type': self.config.breakout_type,
                    'current_price': current_price,
                    'resistance_level': self.config.resistance_level,
                    'support_level': self.config.support_level
                }
            )
            
        except Exception as e:
            return ComponentResult(False, f"가격 돌파 트리거 오류: {str(e)}")
    
    def _check_volume_confirmation(self, market_data: Dict[str, Any]) -> bool:
        """거래량 확인"""
        current_volume = market_data.get('volume', 0)
        avg_volume = market_data.get('avg_volume_20', 0)
        
        if avg_volume <= 0:
            return True  # 데이터 없으면 통과
            
        volume_ratio = current_volume / avg_volume
        return volume_ratio >= self.config.min_volume_ratio


@dataclass
class PriceCrossoverConfig:
    """가격 교차 트리거 설정"""
    price_line_1: str  # "current_price", "ma_5", "ma_20" 등
    price_line_2: str  # 비교할 가격선
    cross_direction: str = "golden"  # golden(상향교차), death(하향교차), any


class PriceCrossoverTrigger(TriggerComponent):
    """
    가격 교차 트리거
    두 가격선의 교차 시 트리거 (예: 현재가와 이동평균선 교차)
    """
    
    def __init__(self, config: PriceCrossoverConfig):
        super().__init__(
            component_id=f"price_crossover_{config.price_line_1}_{config.price_line_2}",
            name=f"가격 교차 트리거 ({config.cross_direction})",
            description=f"{config.price_line_1}과 {config.price_line_2}의 {config.cross_direction} 교차 시 실행"
        )
        self.config = config
        self.previous_values: Dict[str, float] = {}
        self.last_trigger_time: Optional[str] = None
    
    def evaluate(self, market_data: Dict[str, Any], context: ExecutionContext) -> ComponentResult:
        """가격 교차를 감지하여 트리거 여부 결정"""
        try:
            # 현재 값들 가져오기
            current_value_1 = self._get_price_value(self.config.price_line_1, market_data)
            current_value_2 = self._get_price_value(self.config.price_line_2, market_data)
            
            if current_value_1 is None or current_value_2 is None:
                return ComponentResult(False, "가격 데이터 불충분")
            
            # 이전 값이 없으면 현재 값 저장 후 대기
            prev_key_1 = f"prev_{self.config.price_line_1}"
            prev_key_2 = f"prev_{self.config.price_line_2}"
            
            if prev_key_1 not in self.previous_values or prev_key_2 not in self.previous_values:
                self.previous_values[prev_key_1] = current_value_1
                self.previous_values[prev_key_2] = current_value_2
                return ComponentResult(False, "교차 확인을 위한 이전 데이터 수집 중")
            
            # 교차 검사
            previous_value_1 = self.previous_values[prev_key_1]
            previous_value_2 = self.previous_values[prev_key_2]
            
            crossover_detected = self._detect_crossover(
                previous_value_1, current_value_1,
                previous_value_2, current_value_2
            )
            
            # 이전 값 업데이트
            self.previous_values[prev_key_1] = current_value_1
            self.previous_values[prev_key_2] = current_value_2
            
            if crossover_detected:
                self.last_trigger_time = market_data.get('timestamp')
                
                cross_type = "상향교차" if current_value_1 > current_value_2 else "하향교차"
                
                return ComponentResult(
                    True,
                    f"가격 교차 감지: {self.config.price_line_1}({current_value_1:.2f}) {cross_type} {self.config.price_line_2}({current_value_2:.2f})",
                    metadata={
                        'trigger_type': 'price_crossover',
                        'cross_direction': cross_type,
                        'value_1': current_value_1,
                        'value_2': current_value_2,
                        'price_line_1': self.config.price_line_1,
                        'price_line_2': self.config.price_line_2
                    }
                )
            
            return ComponentResult(False, "교차 미발생")
            
        except Exception as e:
            return ComponentResult(False, f"가격 교차 트리거 오류: {str(e)}")
    
    def _get_price_value(self, price_line: str, market_data: Dict[str, Any]) -> Optional[float]:
        """가격선 값 가져오기"""
        if price_line == "current_price":
            return market_data.get('current_price')
        elif price_line.startswith("ma_"):
            # 이동평균선 (예: ma_5, ma_20)
            period = price_line.split("_")[1]
            return market_data.get(f'ma_{period}')
        elif price_line in market_data:
            return market_data.get(price_line)
        
        return None
    
    def _detect_crossover(self, prev_1: float, curr_1: float, prev_2: float, curr_2: float) -> bool:
        """교차 감지"""
        # 이전: line1이 line2 아래 → 현재: line1이 line2 위 = 상향교차
        golden_cross = (prev_1 <= prev_2) and (curr_1 > curr_2)
        
        # 이전: line1이 line2 위 → 현재: line1이 line2 아래 = 하향교차
        death_cross = (prev_1 >= prev_2) and (curr_1 < curr_2)
        
        if self.config.cross_direction == "golden":
            return golden_cross
        elif self.config.cross_direction == "death":
            return death_cross
        elif self.config.cross_direction == "any":
            return golden_cross or death_cross
            
        return False
    
    def reset(self):
        """트리거 상태 리셋"""
        self.previous_values.clear()
        self.last_trigger_time = None
