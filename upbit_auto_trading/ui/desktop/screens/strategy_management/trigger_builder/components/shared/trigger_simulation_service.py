"""
통합 트리거 시뮬레이션 서비스
trigger_builder_screen.py의 계산 로직을 분리하여 컴포넌트 기반으로 재구성
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
import numpy as np
import pandas as pd

# 기존 컴포넌트들 import
try:
    from .trigger_calculator import TriggerCalculator
    COMPONENTS_AVAILABLE = True
    print("✅ TriggerCalculator 로드 성공")
except ImportError as e:
    print(f"❌ TriggerCalculator 로드 실패: {e}")
    COMPONENTS_AVAILABLE = False
    
    # 최소한의 폴백 - 실제 계산 없이 에러만 반환
    class TriggerCalculator:
        def __init__(self):
            print("⚠️ 폴백 TriggerCalculator 사용중 - 실제 계산 불가")
        
        def calculate_sma(self, prices, period):
            raise ImportError("TriggerCalculator 컴포넌트를 불러올 수 없습니다")
        
        def calculate_ema(self, prices, period):
            raise ImportError("TriggerCalculator 컴포넌트를 불러올 수 없습니다")
        
        def calculate_rsi(self, prices, period):
            raise ImportError("TriggerCalculator 컴포넌트를 불러올 수 없습니다")
        
        def calculate_macd(self, prices):
            raise ImportError("TriggerCalculator 컴포넌트를 불러올 수 없습니다")
        
        def calculate_trigger_points(self, data, op, target):
            raise ImportError("TriggerCalculator 컴포넌트를 불러올 수 없습니다")
        
        def calculate_cross_trigger_points(self, base, ext, op):
            raise ImportError("TriggerCalculator 컴포넌트를 불러올 수 없습니다")


@dataclass
class TriggerSimulationRequest:
    """트리거 시뮬레이션 요청 데이터"""
    condition: Dict[str, Any]
    scenario: str
    data_source: str = "virtual"
    data_limit: int = 100


@dataclass
class TriggerSimulationResult:
    """트리거 시뮬레이션 결과 데이터"""
    success: bool
    scenario: str
    trigger_points: List[int]
    price_data: List[float]
    base_variable_data: Optional[List[float]]
    external_variable_data: Optional[List[float]]
    variable_info: Dict[str, Any]
    external_variable_info: Optional[Dict[str, Any]]
    condition_name: str
    current_value: float
    target_value: Any
    result_text: str
    data_source: str
    error_message: Optional[str] = None


class TriggerSimulationService:
    """통합 트리거 시뮬레이션 서비스"""
    
    def __init__(self):
        """초기화"""
        self.trigger_calculator = TriggerCalculator()
        self.logger = logging.getLogger(__name__)
    
    def run_simulation(self, request: TriggerSimulationRequest) -> TriggerSimulationResult:
        """트리거 시뮬레이션 실행"""
        try:
            print(f"🚀 트리거 시뮬레이션 시작: {request.scenario}")
            
            # 1. 시장 데이터 로드
            market_data = self._load_market_data(request.data_source, request.data_limit, request.scenario)
            if not market_data:
                return self._create_error_result(request, "시장 데이터 로드 실패")
            
            # 2. 조건 분석
            condition_info = self._analyze_condition(request.condition)
            if not condition_info['valid']:
                return self._create_error_result(request, condition_info['error'])
            
            # 3. 변수 계산
            variable_data = self._calculate_variables(
                market_data,
                condition_info['variable_name'],
                condition_info['base_parameters'],
                condition_info['external_variable'],
                condition_info['external_parameters']
            )
            
            # 4. 트리거 포인트 계산
            trigger_points = self._calculate_trigger_points(
                variable_data['base_data'],
                variable_data['external_data'],
                condition_info['operator'],
                condition_info['target_value']
            )
            
            # 5. 결과 생성
            result = TriggerSimulationResult(
                success=True,
                scenario=request.scenario,
                trigger_points=trigger_points,
                price_data=market_data,
                base_variable_data=variable_data['base_data'],
                external_variable_data=variable_data['external_data'],
                variable_info=variable_data['variable_info'],
                external_variable_info=variable_data['external_variable_info'],
                condition_name=condition_info['condition_name'],
                current_value=variable_data['current_value'],
                target_value=condition_info['target_value'],
                result_text=self._generate_result_text(trigger_points, condition_info),
                data_source=request.data_source
            )
            
            print(f"✅ 시뮬레이션 완료: {len(trigger_points)}개 트리거")
            return result
            
        except Exception as e:
            print(f"❌ 시뮬레이션 실행 오류: {e}")
            return self._create_error_result(request, str(e))
    
    def _load_market_data(self, data_source: str, limit: int, scenario: str) -> Optional[List[float]]:
        """시장 데이터 로드"""
        try:
            return self._generate_scenario_data(scenario, limit)
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            return None
    
    def _generate_scenario_data(self, scenario: str, limit: int) -> List[float]:
        """시나리오별 가상 데이터 생성"""
        base_price = 50000
        np.random.seed(42)
        
        if scenario == "상승 추세":
            trend = np.linspace(0, 10000, limit)
            noise = np.random.normal(0, 500, limit)
            prices = base_price + trend + noise
            
        elif scenario == "하락 추세":
            trend = np.linspace(0, -8000, limit)
            noise = np.random.normal(0, 500, limit)
            prices = base_price + trend + noise
            
        elif scenario == "급등":
            split_point = int(limit * 0.7)
            trend1 = np.linspace(0, 2000, split_point)
            trend2 = np.linspace(2000, 15000, limit - split_point)
            trend = np.concatenate([trend1, trend2])
            noise = np.random.normal(0, 300, limit)
            prices = base_price + trend + noise
            
        elif scenario == "급락":
            split_point = int(limit * 0.7)
            trend1 = np.linspace(0, -1000, split_point)
            trend2 = np.linspace(-1000, -12000, limit - split_point)
            trend = np.concatenate([trend1, trend2])
            noise = np.random.normal(0, 400, limit)
            prices = base_price + trend + noise
            
        elif scenario == "횡보":
            noise = np.random.normal(0, 800, limit)
            prices = base_price + noise
            
        elif scenario == "이동평균 교차":
            trend = np.concatenate([
                np.linspace(0, -3000, 40),
                np.linspace(-3000, -2000, 20),
                np.linspace(-2000, 5000, 40)
            ])
            noise = np.random.normal(0, 400, limit)
            prices = base_price + trend + noise
            
        else:
            noise = np.random.normal(0, 1000, limit)
            prices = base_price + noise
        
        return [max(price, 10000) for price in prices]
    
    def _analyze_condition(self, condition: Dict[str, Any]) -> Dict[str, Any]:
        """조건 분석"""
        try:
            variable_name = condition.get('variable_name', 'Unknown')
            operator = condition.get('operator', '>')
            target_value = condition.get('target_value', 0)
            external_variable = condition.get('external_variable')
            
            base_parameters = condition.get('variable_params', {})
            external_parameters = external_variable.get('parameters', {}) if external_variable else {}
            
            if external_variable:
                condition_name = f"{variable_name} {operator} {external_variable.get('variable_name', 'External')}"
            else:
                condition_name = f"{variable_name} {operator} {target_value}"
            
            return {
                'valid': True,
                'variable_name': variable_name,
                'operator': operator,
                'target_value': target_value,
                'external_variable': external_variable,
                'base_parameters': base_parameters,
                'external_parameters': external_parameters,
                'condition_name': condition_name,
                'error': None
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"조건 분석 실패: {e}"
            }
    
    def _calculate_variables(self, price_data: List[float], variable_name: str,
                           base_parameters: Dict, external_variable: Optional[Dict],
                           external_parameters: Dict) -> Dict[str, Any]:
        """변수 계산"""
        try:
            base_data = self._calculate_variable_data(variable_name, price_data, base_parameters)
            variable_info = self._get_variable_chart_info(variable_name)
            
            external_data = None
            external_variable_info = None
            if external_variable and external_variable.get('variable_name'):
                external_data = self._calculate_variable_data(
                    external_variable['variable_name'], price_data, external_parameters
                )
                external_variable_info = self._get_variable_chart_info(external_variable['variable_name'])
            
            current_value = base_data[-1] if base_data else 0
            
            print(f"✅ 변수 계산 완료:")
            print(f"   기본변수: {variable_name} (range: {min(base_data):.2f} ~ {max(base_data):.2f})")
            if external_data:
                ext_name = external_variable['variable_name']
                print(f"   외부변수: {ext_name} (range: {min(external_data):.2f} ~ {max(external_data):.2f})")
            
            return {
                'base_data': base_data,
                'external_data': external_data,
                'variable_info': variable_info,
                'external_variable_info': external_variable_info,
                'current_value': current_value
            }
            
        except Exception as e:
            print(f"❌ 변수 계산 실패: {e}")
            raise
    
    def _calculate_variable_data(self, variable_name: str, price_data: List[float],
                               parameters: Dict) -> List[float]:
        """개별 변수 데이터 계산"""
        variable_id = self._map_ui_text_to_variable_id(variable_name)
        
        if variable_id == 'SMA':
            period = self._extract_period_from_parameters(parameters, variable_name, default=20)
            return self.trigger_calculator.calculate_sma(price_data, period)
            
        elif variable_id == 'EMA':
            period = self._extract_period_from_parameters(parameters, variable_name, default=12)
            return self.trigger_calculator.calculate_ema(price_data, period)
            
        elif variable_id == 'RSI':
            period = self._extract_period_from_parameters(parameters, variable_name, default=14)
            return self.trigger_calculator.calculate_rsi(price_data, period)
            
        elif variable_id == 'MACD':
            return self.trigger_calculator.calculate_macd(price_data)
            
        elif variable_id == 'PRICE':
            return price_data
            
        else:
            print(f"⚠️ 알 수 없는 변수: {variable_name} -> {variable_id}")
            return price_data
    
    def _extract_period_from_parameters(self, parameters: Dict, variable_name: str, default: int) -> int:
        """파라미터에서 period 추출"""
        if parameters and isinstance(parameters, dict) and 'period' in parameters:
            return int(parameters['period'])
        
        import re
        match = re.search(r'\((\d+)\)', variable_name)
        if match:
            return int(match.group(1))
        
        return default
    
    def _map_ui_text_to_variable_id(self, variable_name: str) -> str:
        """UI 텍스트를 변수 ID로 매핑"""
        name_upper = variable_name.upper()
        
        if 'SMA' in name_upper or '단순이동평균' in variable_name:
            return 'SMA'
        elif 'EMA' in name_upper or '지수이동평균' in variable_name:
            return 'EMA'
        elif 'RSI' in name_upper:
            return 'RSI'
        elif 'MACD' in name_upper:
            return 'MACD'
        elif '현재가' in variable_name or 'PRICE' in name_upper:
            return 'PRICE'
        elif '거래량' in variable_name or 'VOLUME' in name_upper:
            return 'VOLUME'
        else:
            return 'PRICE'
    
    def _get_variable_chart_info(self, variable_name: str) -> Dict[str, Any]:
        """변수 차트 정보 가져오기"""
        variable_id = self._map_ui_text_to_variable_id(variable_name)
        if variable_id == 'RSI':
            return {'variable_id': 'RSI', 'category': 'oscillator', 'display_type': 'line',
                   'scale_min': 0, 'scale_max': 100}
        elif variable_id == 'MACD':
            return {'variable_id': 'MACD', 'category': 'momentum', 'display_type': 'line'}
        else:
            return {'variable_id': variable_id, 'category': 'price_overlay', 'display_type': 'line'}
    
    def _calculate_trigger_points(self, base_data: List[float], external_data: Optional[List[float]],
                                operator: str, target_value: Any) -> List[int]:
        """트리거 포인트 계산"""
        if external_data:
            return self.trigger_calculator.calculate_cross_trigger_points(
                base_data, external_data, operator
            )
        else:
            return self.trigger_calculator.calculate_trigger_points(
                base_data, operator, target_value
            )
    
    def _generate_result_text(self, trigger_points: List[int], condition_info: Dict) -> str:
        """결과 텍스트 생성"""
        trigger_count = len(trigger_points)
        condition_name = condition_info['condition_name']
        
        if trigger_count > 0:
            return f"✅ {condition_name} 조건 충족 ({trigger_count}회)"
        else:
            return f"❌ {condition_name} 조건 불충족"
    
    def _create_error_result(self, request: TriggerSimulationRequest, error_message: str) -> TriggerSimulationResult:
        """오류 결과 생성"""
        return TriggerSimulationResult(
            success=False,
            scenario=request.scenario,
            trigger_points=[],
            price_data=[],
            base_variable_data=None,
            external_variable_data=None,
            variable_info={},
            external_variable_info=None,
            condition_name="Error",
            current_value=0,
            target_value=0,
            result_text=f"❌ 시뮬레이션 실패: {error_message}",
            data_source=request.data_source,
            error_message=error_message
        )


# 전역 서비스 인스턴스
_trigger_simulation_service = None


def get_trigger_simulation_service() -> TriggerSimulationService:
    """트리거 시뮬레이션 서비스 싱글톤 반환"""
    global _trigger_simulation_service
    if _trigger_simulation_service is None:
        _trigger_simulation_service = TriggerSimulationService()
    return _trigger_simulation_service
