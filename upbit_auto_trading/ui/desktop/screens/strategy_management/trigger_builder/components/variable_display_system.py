"""
변수 카테고리 및 차트 표현 시스템

변수의 성격에 따른 차트 표현 방식을 정의하고 관리하는 시스템
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


class VariableCategory(Enum):
    """변수 카테고리 정의"""
    # 시가 차트에 함께 표시되는 지표들
    PRICE_OVERLAY = "price_overlay"  # 시가차트 오버레이 (이동평균, 볼린저밴드, 현재가 등)
    
    # 별도 서브플롯이 필요한 지표들  
    OSCILLATOR = "oscillator"        # 오실레이터 (RSI, 스토캐스틱, %K, %D 등)
    MOMENTUM = "momentum"            # 모멘텀 지표 (MACD, ROC 등)
    VOLUME = "volume"                # 거래량 관련 지표
    
    # 특수 카테고리
    CURRENCY = "currency"            # 통화 단위 (원화, USD 등)
    PERCENTAGE = "percentage"        # 퍼센트 단위 (0-100%)
    CUSTOM = "custom"                # 사용자 정의


class ChartDisplayType(Enum):
    """차트 표시 방식"""
    MAIN_CHART_LINE = "main_line"           # 메인 차트에 선으로 표시
    MAIN_CHART_BAND = "main_band"           # 메인 차트에 밴드로 표시  
    MAIN_CHART_LEVEL = "main_level"         # 메인 차트에 수평선으로 표시
    SUBPLOT_LINE = "subplot_line"           # 서브플롯에 선으로 표시
    SUBPLOT_HISTOGRAM = "subplot_histogram" # 서브플롯에 히스토그램으로 표시
    SUBPLOT_LEVEL = "subplot_level"         # 서브플롯에 수평선으로 표시


@dataclass
class VariableDisplayConfig:
    """변수 표시 설정"""
    category: VariableCategory
    display_type: ChartDisplayType
    scale_min: Optional[float] = None  # 최소 스케일 (예: RSI는 0)
    scale_max: Optional[float] = None  # 최대 스케일 (예: RSI는 100)
    unit: str = ""                     # 단위 (원, %, 등)
    color: str = "#007bff"            # 기본 색상
    subplot_height_ratio: float = 0.3  # 서브플롯 높이 비율
    allow_external_vars: List[VariableCategory] = None  # 허용되는 외부변수 카테고리
    
    def __post_init__(self):
        if self.allow_external_vars is None:
            self.allow_external_vars = []


class VariableRegistry:
    """변수 등록 및 관리 시스템"""
    
    def __init__(self):
        self._registry: Dict[str, VariableDisplayConfig] = {}
        self._initialize_default_variables()
    
    def _initialize_default_variables(self):
        """기본 변수들을 등록"""
        
        # 시가 차트 오버레이 변수들
        self.register_variable("현재가", VariableDisplayConfig(
            category=VariableCategory.PRICE_OVERLAY,
            display_type=ChartDisplayType.MAIN_CHART_LEVEL,
            unit="원",
            color="#1f77b4",
            allow_external_vars=[VariableCategory.PRICE_OVERLAY, VariableCategory.CURRENCY]
        ))
        
        self.register_variable("이동평균", VariableDisplayConfig(
            category=VariableCategory.PRICE_OVERLAY,
            display_type=ChartDisplayType.MAIN_CHART_LINE,
            unit="원",
            color="#ff7f0e",
            allow_external_vars=[VariableCategory.PRICE_OVERLAY]
        ))
        
        self.register_variable("볼린저밴드", VariableDisplayConfig(
            category=VariableCategory.PRICE_OVERLAY,
            display_type=ChartDisplayType.MAIN_CHART_BAND,
            unit="원", 
            color="#2ca02c",
            allow_external_vars=[VariableCategory.PRICE_OVERLAY]
        ))
        
        # 오실레이터 변수들
        self.register_variable("RSI", VariableDisplayConfig(
            category=VariableCategory.OSCILLATOR,
            display_type=ChartDisplayType.SUBPLOT_LINE,
            scale_min=0,
            scale_max=100,
            unit="%",
            color="#d62728",
            subplot_height_ratio=0.25,
            allow_external_vars=[VariableCategory.OSCILLATOR, VariableCategory.PERCENTAGE]
        ))
        
        self.register_variable("스토캐스틱", VariableDisplayConfig(
            category=VariableCategory.OSCILLATOR,
            display_type=ChartDisplayType.SUBPLOT_LINE,
            scale_min=0,
            scale_max=100,
            unit="%",
            color="#ff69b4",
            subplot_height_ratio=0.25,
            allow_external_vars=[VariableCategory.OSCILLATOR, VariableCategory.PERCENTAGE]
        ))
        
        # 모멘텀 지표들
        self.register_variable("MACD", VariableDisplayConfig(
            category=VariableCategory.MOMENTUM,
            display_type=ChartDisplayType.SUBPLOT_LINE,
            unit="",
            color="#9467bd",
            subplot_height_ratio=0.3,
            allow_external_vars=[VariableCategory.MOMENTUM]
        ))
    
    def register_variable(self, variable_name: str, config: VariableDisplayConfig):
        """변수 등록"""
        self._registry[variable_name] = config
    
    def get_variable_config(self, variable_name: str) -> Optional[VariableDisplayConfig]:
        """변수 설정 조회"""
        return self._registry.get(variable_name)
    
    def is_compatible_external_variable(self, base_variable: str, external_variable: str) -> bool:
        """외부변수 호환성 검사"""
        base_config = self.get_variable_config(base_variable)
        external_config = self.get_variable_config(external_variable)
        
        if not base_config or not external_config:
            return False
        
        return external_config.category in base_config.allow_external_vars
    
    def get_chart_layout_info(self, variables: List[str]) -> Dict[str, Any]:
        """차트 레이아웃 정보 생성"""
        main_chart_vars = []
        subplots = []
        
        for var_name in variables:
            config = self.get_variable_config(var_name)
            if not config:
                continue
            
            if config.category == VariableCategory.PRICE_OVERLAY:
                main_chart_vars.append({
                    "name": var_name,
                    "config": config
                })
            else:
                subplots.append({
                    "name": var_name,
                    "config": config
                })
        
        return {
            "main_chart_variables": main_chart_vars,
            "subplots": subplots,
            "total_height_ratios": self._calculate_height_ratios(subplots)
        }
    
    def _calculate_height_ratios(self, subplots: List[Dict]) -> List[float]:
        """차트 높이 비율 계산"""
        if not subplots:
            return [1.0]  # 메인 차트만
        
        main_ratio = 0.6  # 메인 차트 60%
        remaining = 0.4   # 서브플롯들 40%
        
        total_subplot_ratio = sum(subplot["config"].subplot_height_ratio for subplot in subplots)
        if total_subplot_ratio == 0:
            return [1.0]
        
        ratios = [main_ratio]
        for subplot in subplots:
            subplot_ratio = (subplot["config"].subplot_height_ratio / total_subplot_ratio) * remaining
            ratios.append(subplot_ratio)
        
        return ratios


# 전역 변수 레지스트리
_variable_registry = None

def get_variable_registry() -> VariableRegistry:
    """변수 레지스트리 싱글톤 반환"""
    global _variable_registry
    if _variable_registry is None:
        _variable_registry = VariableRegistry()
    return _variable_registry
