#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
미니차트 변수 서비스

트리거 빌더의 4-요소 단순화 미니차트를 위한 변수 관리 서비스입니다.
기존 chart_variable_service.py와 병행하여 미니차트에 특화된 기능을 제공합니다.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

try:
    from upbit_auto_trading.data_layer.minichart_variable_models import (
        MINICHART_INITIAL_VARIABLES, MINICHART_SCALE_GROUPS
    )
    MINICHART_MODELS_AVAILABLE = True
except ImportError:
    MINICHART_MODELS_AVAILABLE = False
    logging.warning("미니차트 모델을 가져올 수 없습니다. 폴백 모드로 동작합니다.")

@dataclass
class MiniChartVariableConfig:
    """미니차트 변수 설정"""
    variable_id: str
    variable_name: str
    english_name: str
    category: str  # MiniChartCategory.value
    scale_type: str  # MiniChartScaleType.value
    display_mode: str  # MiniChartDisplayMode.value
    
    # 스케일 정보
    scale_min: Optional[float] = None
    scale_max: Optional[float] = None
    auto_scale: bool = True
    
    # 색상 설정
    primary_color: str = "#007bff"
    secondary_color: Optional[str] = None
    alpha: float = 0.8
    line_width: float = 1.5
    
    # 표시 설정
    subplot_height_ratio: float = 0.3
    show_grid: bool = True
    show_legend: bool = True
    
    # 파라미터
    default_parameters: Dict[str, Any] = None
    parameter_constraints: Dict[str, Any] = None
    
    # 호환성
    compatible_scale_types: List[str] = None
    comparison_compatible: bool = True
    
    # 메타데이터
    is_active: bool = True
    priority: int = 100
    
    def __post_init__(self):
        if self.default_parameters is None:
            self.default_parameters = {}
        if self.parameter_constraints is None:
            self.parameter_constraints = {}
        if self.compatible_scale_types is None:
            self.compatible_scale_types = []

@dataclass
class MiniChartLayoutInfo:
    """미니차트 레이아웃 정보"""
    main_elements: List[Dict[str, Any]]  # Price/Volume, iVal 등
    comparison_elements: List[Dict[str, Any]]  # fVal/eVal
    trigger_markers: List[Dict[str, Any]]  # Trg
    color_scheme: Dict[str, str]
    scale_groups: Dict[str, Dict[str, Any]]

class MiniChartVariableService:
    """미니차트 변수 서비스 - 4요소 단순화 시스템"""
    
    def __init__(self):
        """미니차트 변수 서비스 초기화"""
        self._variable_cache: Dict[str, MiniChartVariableConfig] = {}
        self._scale_groups: Dict[str, Dict[str, Any]] = {}
        self._color_scheme = {
            'price': '#007bff',        # 파란색 - Price
            'volume': '#6c757d',       # 회색 - Volume
            'indicator': '#28a745',    # 녹색 - iVal
            'comparison': '#fd7e14',   # 주황색 - fVal/eVal
            'trigger': '#dc3545',      # 빨간색 - Trg
            'reference': '#6c757d'     # 회색 - 참조선
        }
        
        self._load_initial_data()
        logging.info("✅ 미니차트 변수 서비스 초기화 완료")
    
    def _load_initial_data(self):
        """초기 데이터 로드"""
        try:
            if MINICHART_MODELS_AVAILABLE:
                # 모델이 있으면 모델에서 로드
                self._load_from_models()
            else:
                # 모델이 없으면 하드코딩된 데이터 사용
                self._load_fallback_data()
        except Exception as e:
            logging.error(f"초기 데이터 로드 실패: {e}")
            self._load_fallback_data()
    
    def _load_from_models(self):
        """모델에서 데이터 로드"""
        # 변수 데이터 로드
        for var_data in MINICHART_INITIAL_VARIABLES:
            config = MiniChartVariableConfig(
                variable_id=var_data['variable_id'],
                variable_name=var_data['variable_name'],
                english_name=var_data['english_name'],
                category=var_data['category'].value,
                scale_type=var_data['scale_type'].value,
                display_mode=var_data['display_mode'].value,
                primary_color=var_data.get('primary_color', '#007bff'),
                scale_min=var_data.get('scale_min'),
                scale_max=var_data.get('scale_max'),
                auto_scale=var_data.get('auto_scale', True),
                default_parameters=var_data.get('default_parameters', {})
            )
            self._variable_cache[var_data['variable_id']] = config
        
        # 스케일 그룹 로드
        for group_data in MINICHART_SCALE_GROUPS:
            self._scale_groups[group_data['group_name']] = group_data
    
    def _load_fallback_data(self):
        """폴백 데이터 로드"""
        # 기본 변수들
        fallback_variables = [
            {
                'variable_id': 'SMA',
                'variable_name': '단순이동평균',
                'english_name': 'iVal',
                'category': 'indicator',
                'scale_type': 'price_scale',
                'display_mode': 'overlay',
                'primary_color': '#28a745',
                'default_parameters': {'period': 20}
            },
            {
                'variable_id': 'RSI',
                'variable_name': 'RSI 지표',
                'english_name': 'iVal',
                'category': 'indicator',
                'scale_type': 'percentage_100',
                'display_mode': 'subplot',
                'primary_color': '#28a745',
                'scale_min': 0.0,
                'scale_max': 100.0,
                'auto_scale': False,
                'default_parameters': {'period': 14}
            },
            {
                'variable_id': 'VOLUME',
                'variable_name': '거래량',
                'english_name': 'Volume',
                'category': 'price_volume',
                'scale_type': 'volume_scale',
                'display_mode': 'volume_bar',
                'primary_color': '#6c757d'
            }
        ]
        
        for var_data in fallback_variables:
            config = MiniChartVariableConfig(**var_data)
            self._variable_cache[var_data['variable_id']] = config
        
        # 기본 스케일 그룹
        self._scale_groups = {
            'percentage_100': {
                'group_name': 'percentage_100',
                'scale_type': 'percentage_100',
                'min_value': 0.0,
                'max_value': 100.0,
                'reference_lines': [
                    {'value': 30, 'label': 'OS(30)', 'color': '#dc3545'},
                    {'value': 70, 'label': 'OB(70)', 'color': '#dc3545'}
                ]
            }
        }
    
    def get_variable_config(self, variable_id: str) -> Optional[MiniChartVariableConfig]:
        """변수 설정 조회"""
        return self._variable_cache.get(variable_id)
    
    def get_variable_by_name(self, variable_name: str) -> Optional[MiniChartVariableConfig]:
        """변수명으로 설정 조회"""
        for config in self._variable_cache.values():
            if config.variable_name == variable_name:
                return config
        return None
    
    def get_variables_by_category(self, category: str) -> List[MiniChartVariableConfig]:
        """카테고리별 변수 목록 조회"""
        return [config for config in self._variable_cache.values() 
                if config.category == category and config.is_active]
    
    def get_variables_by_scale_type(self, scale_type: str) -> List[MiniChartVariableConfig]:
        """스케일 타입별 변수 목록 조회"""
        return [config for config in self._variable_cache.values() 
                if config.scale_type == scale_type and config.is_active]
    
    def get_scale_group(self, group_name: str) -> Optional[Dict[str, Any]]:
        """스케일 그룹 정보 조회"""
        return self._scale_groups.get(group_name)
    
    def get_color_scheme(self) -> Dict[str, str]:
        """4요소 색상 스키마 반환"""
        return self._color_scheme.copy()
    
    def get_display_colors(self, variable_config: MiniChartVariableConfig) -> Dict[str, str]:
        """변수별 표시 색상 반환"""
        category = variable_config.category
        
        if category == 'price_volume':
            return {
                'primary': self._color_scheme['price'],
                'secondary': self._color_scheme['volume']
            }
        elif category == 'indicator':
            return {
                'primary': self._color_scheme['indicator'],
                'secondary': variable_config.primary_color
            }
        elif category == 'comparison':
            return {
                'primary': self._color_scheme['comparison'],
                'secondary': variable_config.primary_color
            }
        elif category == 'trigger':
            return {
                'primary': self._color_scheme['trigger'],
                'secondary': variable_config.primary_color
            }
        else:
            return {
                'primary': variable_config.primary_color,
                'secondary': variable_config.secondary_color or variable_config.primary_color
            }
    
    def create_layout_info(self, base_variable_id: str, 
                          external_variable_id: Optional[str] = None,
                          fixed_value: Optional[float] = None,
                          trigger_points: Optional[List[int]] = None) -> MiniChartLayoutInfo:
        """4요소 레이아웃 정보 생성"""
        
        base_config = self.get_variable_config(base_variable_id)
        if not base_config:
            raise ValueError(f"알 수 없는 변수: {base_variable_id}")
        
        # 메인 요소들 (Price/Volume + iVal)
        main_elements = []
        
        # Price는 항상 포함 (subplot이 아닌 경우)
        if base_config.display_mode != 'subplot':
            main_elements.append({
                'type': 'price',
                'label': 'Price',
                'color': self._color_scheme['price'],
                'data_key': 'price_data'
            })
        
        # 기본 변수 (iVal)
        main_elements.append({
            'type': 'indicator',
            'label': base_config.english_name,
            'color': self._color_scheme['indicator'],
            'data_key': 'base_variable_data',
            'config': base_config
        })
        
        # 비교 요소들 (fVal/eVal)
        comparison_elements = []
        if external_variable_id:
            ext_config = self.get_variable_config(external_variable_id)
            if ext_config:
                comparison_elements.append({
                    'type': 'external_variable',
                    'label': 'eVal',
                    'color': self._color_scheme['comparison'],
                    'data_key': 'external_variable_data',
                    'config': ext_config
                })
        
        if fixed_value is not None:
            comparison_elements.append({
                'type': 'fixed_value',
                'label': 'fVal',
                'color': self._color_scheme['comparison'],
                'value': fixed_value,
                'linestyle': '--'
            })
        
        # 트리거 마커들 (Trg)
        trigger_markers = []
        if trigger_points:
            trigger_markers.append({
                'type': 'trigger_points',
                'label': 'Trg',
                'color': self._color_scheme['trigger'],
                'positions': trigger_points,
                'marker': 'v',
                'size': 50
            })
        
        # 스케일 그룹 정보
        scale_groups = {}
        scale_group = self.get_scale_group(base_config.scale_type)
        if scale_group:
            scale_groups[base_config.scale_type] = scale_group
        
        return MiniChartLayoutInfo(
            main_elements=main_elements,
            comparison_elements=comparison_elements,
            trigger_markers=trigger_markers,
            color_scheme=self._color_scheme,
            scale_groups=scale_groups
        )
    
    def is_compatible_for_comparison(self, base_variable_id: str, 
                                   compare_variable_id: str) -> Tuple[bool, str]:
        """변수 간 비교 호환성 확인"""
        base_config = self.get_variable_config(base_variable_id)
        compare_config = self.get_variable_config(compare_variable_id)
        
        if not base_config or not compare_config:
            return False, "변수를 찾을 수 없습니다"
        
        # 같은 스케일 타입이면 호환
        if base_config.scale_type == compare_config.scale_type:
            return True, "같은 스케일 타입"
        
        # 호환 가능한 스케일 타입 확인
        if compare_config.scale_type in base_config.compatible_scale_types:
            return True, "호환 가능한 스케일 타입"
        
        # 가격 스케일과 정규화 스케일은 조건부 호환
        if (base_config.scale_type == 'price_scale' and 
            compare_config.scale_type in ['normalized', 'unbounded']):
            return True, "가격 스케일과 정규화 스케일 호환"
        
        return False, f"호환되지 않는 스케일: {base_config.scale_type} vs {compare_config.scale_type}"
    
    def get_optimal_subplot_layout(self, variable_configs: List[MiniChartVariableConfig]) -> Dict[str, Any]:
        """최적의 서브플롯 레이아웃 계산"""
        overlay_count = sum(1 for config in variable_configs if config.display_mode == 'overlay')
        subplot_count = sum(1 for config in variable_configs if config.display_mode == 'subplot')
        
        if subplot_count == 0:
            # 서브플롯이 없으면 메인 차트만
            return {
                'layout_type': 'single',
                'main_height_ratio': 1.0,
                'subplot_ratios': []
            }
        elif subplot_count == 1:
            # 서브플롯 1개
            subplot_config = next(config for config in variable_configs if config.display_mode == 'subplot')
            return {
                'layout_type': 'main_subplot',
                'main_height_ratio': 0.7,
                'subplot_ratios': [subplot_config.subplot_height_ratio]
            }
        else:
            # 서브플롯 2개 이상 - 높이를 균등 분할
            subplot_configs = [config for config in variable_configs if config.display_mode == 'subplot']
            total_subplot_ratio = sum(config.subplot_height_ratio for config in subplot_configs)
            normalized_ratios = [config.subplot_height_ratio / total_subplot_ratio * 0.6 
                               for config in subplot_configs]
            
            return {
                'layout_type': 'multi_subplot',
                'main_height_ratio': 0.4,
                'subplot_ratios': normalized_ratios
            }

# 전역 서비스 인스턴스
_minichart_variable_service = None

def get_minichart_variable_service() -> MiniChartVariableService:
    """미니차트 변수 서비스 싱글톤 반환"""
    global _minichart_variable_service
    if _minichart_variable_service is None:
        _minichart_variable_service = MiniChartVariableService()
    return _minichart_variable_service
