#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
미니차트 변수 카테고리 모델 정의

트리거 빌더의 4-요소 단순화 미니차트에 특화된 변수 관리 모델입니다.
Price/Volume + iVal + fVal/eVal + Trg 의 4가지 요소로 단순화된 차트 시스템을 지원합니다.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Text, JSON,
    Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum

Base = declarative_base()


class MiniChartCategory(Enum):
    """미니차트 변수 카테고리 정의 - 4요소 단순화"""
    # 기본 요소들
    PRICE_VOLUME = "price_volume"    # 가격/거래량 (파란색 라인)
    INDICATOR = "indicator"          # 지표값 iVal (녹색 라인) - SMA, EMA, RSI 등
    COMPARISON = "comparison"        # 비교값 fVal/eVal (주황색) - 고정값 또는 외부변수
    TRIGGER = "trigger"              # 트리거 마커 Trg (빨간 삼각형)


class MiniChartScaleType(Enum):
    """미니차트 스케일 타입 정의"""
    # 스케일 기반 분류
    PRICE_SCALE = "price_scale"      # 가격 스케일 (수만원~수십만원)
    PERCENTAGE_100 = "percentage_100" # 0-100% 스케일 (RSI, 스토캐스틱, %K, %D)
    PERCENTAGE_200 = "percentage_200" # 0-200% 스케일 (일부 오실레이터)
    VOLUME_SCALE = "volume_scale"    # 거래량 스케일 (수십만~수백만)
    NORMALIZED = "normalized"        # 정규화 스케일 (-1 ~ +1, -100 ~ +100 등)
    UNBOUNDED = "unbounded"          # 무제한 스케일 (MACD, ROC 등)


class MiniChartDisplayMode(Enum):
    """미니차트 표시 모드"""
    OVERLAY = "overlay"              # 메인 차트에 오버레이 (이동평균 등)
    SUBPLOT = "subplot"              # 별도 서브플롯 (RSI, MACD 등)
    VOLUME_BAR = "volume_bar"        # 거래량 바 차트
    MARKER_ONLY = "marker_only"      # 마커만 표시 (트리거 포인트)


class MiniChartVariable(Base):
    """미니차트 변수 정의 테이블"""
    __tablename__ = 'minichart_variables'
    
    id = Column(Integer, primary_key=True)
    variable_id = Column(String(50), nullable=False, unique=True, index=True)  # 변수 식별자
    variable_name = Column(String(100), nullable=False)  # 변수 표시명 (한글/영어)
    english_name = Column(String(50), nullable=False)   # 영어 약어 (iVal, fVal 등)
    description = Column(Text, nullable=True)  # 변수 설명
    
    # 카테고리 정보
    category = Column(SQLEnum(MiniChartCategory), nullable=False, index=True)
    scale_type = Column(SQLEnum(MiniChartScaleType), nullable=False, index=True)
    display_mode = Column(SQLEnum(MiniChartDisplayMode), nullable=False)
    
    # 스케일 정보 (미니차트 최적화)
    scale_min = Column(Float, nullable=True)  # 최소 스케일
    scale_max = Column(Float, nullable=True)  # 최대 스케일
    auto_scale = Column(Boolean, nullable=False, default=True)  # 자동 스케일 조정 여부
    
    # 표시 설정 (4요소 색상 체계)
    primary_color = Column(String(20), nullable=False, default="#007bff")   # 기본 색상
    secondary_color = Column(String(20), nullable=True)  # 보조 색상 (밴드 등)
    alpha = Column(Float, nullable=False, default=0.8)  # 투명도
    line_width = Column(Float, nullable=False, default=1.5)  # 라인 굵기
    
    # 미니차트 특화 설정
    subplot_height_ratio = Column(Float, nullable=False, default=0.3)  # 서브플롯 높이 비율
    show_grid = Column(Boolean, nullable=False, default=True)  # 그리드 표시
    show_legend = Column(Boolean, nullable=False, default=True)  # 범례 표시
    
    # 계산 파라미터 지원
    default_parameters = Column(JSON, nullable=True)  # 기본 파라미터 (period=14 등)
    parameter_constraints = Column(JSON, nullable=True)  # 파라미터 제약조건
    
    # 호환성 설정
    compatible_scale_types = Column(JSON, nullable=True)  # 호환 가능한 스케일 타입들
    comparison_compatible = Column(Boolean, nullable=False, default=True)  # 비교 가능 여부
    
    # 성능 최적화
    cache_calculation = Column(Boolean, nullable=False, default=True)  # 계산 결과 캐싱
    fast_rendering = Column(Boolean, nullable=False, default=True)  # 고속 렌더링 모드
    
    # 메타데이터
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=100)  # 표시 우선순위
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return (f"<MiniChartVariable(variable_id='{self.variable_id}', "
                f"name='{self.variable_name}', category='{self.category.value}', "
                f"scale_type='{self.scale_type.value}')>")


class MiniChartScaleGroup(Base):
    """미니차트 스케일 그룹 관리 테이블"""
    __tablename__ = 'minichart_scale_groups'
    
    id = Column(Integer, primary_key=True)
    group_name = Column(String(50), nullable=False, unique=True)  # 그룹명
    scale_type = Column(SQLEnum(MiniChartScaleType), nullable=False)
    description = Column(Text, nullable=True)
    
    # 스케일 설정
    min_value = Column(Float, nullable=False)
    max_value = Column(Float, nullable=False)
    default_step = Column(Float, nullable=True)  # 기본 단계
    
    # 표시 설정
    tick_format = Column(String(20), nullable=False, default="{:.1f}")  # 눈금 포맷
    unit_symbol = Column(String(10), nullable=False, default="")  # 단위 기호
    
    # 레퍼런스 라인들 (RSI의 30, 70 라인 등)
    reference_lines = Column(JSON, nullable=True)  # [{"value": 70, "label": "과매수", "color": "red"}]
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MiniChartScaleGroup(name='{self.group_name}', range={self.min_value}-{self.max_value})>"


class MiniChartCompatibilityRule(Base):
    """미니차트 변수 호환성 규칙 테이블"""
    __tablename__ = 'minichart_compatibility_rules'
    
    id = Column(Integer, primary_key=True)
    base_variable_id = Column(String(50), ForeignKey('minichart_variables.variable_id'), nullable=False)
    compatible_variable_id = Column(String(50), ForeignKey('minichart_variables.variable_id'), nullable=False)
    
    # 호환성 정보
    compatibility_type = Column(String(20), nullable=False)  # 'cross_compare', 'overlay', 'correlation'
    compatibility_score = Column(Float, nullable=False, default=1.0)  # 호환성 점수 (0.0-1.0)
    compatibility_reason = Column(Text, nullable=True)  # 호환성 이유
    
    # 표시 제약조건
    requires_scale_normalization = Column(Boolean, nullable=False, default=False)  # 스케일 정규화 필요
    max_display_variables = Column(Integer, nullable=False, default=2)  # 최대 동시 표시 변수 수
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 관계
    base_variable = relationship("MiniChartVariable", foreign_keys=[base_variable_id])
    compatible_variable = relationship("MiniChartVariable", foreign_keys=[compatible_variable_id])
    
    def __repr__(self):
        return (f"<MiniChartCompatibilityRule(base='{self.base_variable_id}', "
                f"compatible='{self.compatible_variable_id}', type='{self.compatibility_type}')>")


class MiniChartPreset(Base):
    """미니차트 프리셋 테이블"""
    __tablename__ = 'minichart_presets'
    
    id = Column(Integer, primary_key=True)
    preset_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # 프리셋 구성
    variable_configuration = Column(JSON, nullable=False)  # 변수 설정 정보
    layout_configuration = Column(JSON, nullable=False)   # 레이아웃 설정
    color_scheme = Column(JSON, nullable=True)            # 색상 스키마
    
    # 사용 정보
    usage_context = Column(String(50), nullable=False)    # 'trigger_builder', 'quick_analysis' 등
    is_default = Column(Boolean, nullable=False, default=False)
    user_rating = Column(Float, nullable=True)            # 사용자 평점
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MiniChartPreset(name='{self.preset_name}', context='{self.usage_context}')>"


# 미니차트 변수 초기 데이터 정의
MINICHART_INITIAL_VARIABLES = [
    # Price/Volume 카테고리
    {
        'variable_id': 'PRICE',
        'variable_name': '현재가',
        'english_name': 'Price',
        'category': MiniChartCategory.PRICE_VOLUME,
        'scale_type': MiniChartScaleType.PRICE_SCALE,
        'display_mode': MiniChartDisplayMode.OVERLAY,
        'primary_color': '#007bff',  # 파란색
        'scale_min': None,
        'scale_max': None,
        'auto_scale': True
    },
    {
        'variable_id': 'VOLUME',
        'variable_name': '거래량',
        'english_name': 'Volume',
        'category': MiniChartCategory.PRICE_VOLUME,
        'scale_type': MiniChartScaleType.VOLUME_SCALE,
        'display_mode': MiniChartDisplayMode.VOLUME_BAR,
        'primary_color': '#6c757d',  # 회색
        'scale_min': 0,
        'scale_max': None,
        'auto_scale': True
    },
    
    # Indicator 카테고리 (iVal)
    {
        'variable_id': 'SMA',
        'variable_name': '단순이동평균',
        'english_name': 'iVal',
        'category': MiniChartCategory.INDICATOR,
        'scale_type': MiniChartScaleType.PRICE_SCALE,
        'display_mode': MiniChartDisplayMode.OVERLAY,
        'primary_color': '#28a745',  # 녹색
        'default_parameters': {'period': 20}
    },
    {
        'variable_id': 'EMA',
        'variable_name': '지수이동평균',
        'english_name': 'iVal',
        'category': MiniChartCategory.INDICATOR,
        'scale_type': MiniChartScaleType.PRICE_SCALE,
        'display_mode': MiniChartDisplayMode.OVERLAY,
        'primary_color': '#28a745',  # 녹색
        'default_parameters': {'period': 12}
    },
    {
        'variable_id': 'RSI',
        'variable_name': 'RSI 지표',
        'english_name': 'iVal',
        'category': MiniChartCategory.INDICATOR,
        'scale_type': MiniChartScaleType.PERCENTAGE_100,
        'display_mode': MiniChartDisplayMode.SUBPLOT,
        'primary_color': '#28a745',  # 녹색
        'scale_min': 0.0,
        'scale_max': 100.0,
        'auto_scale': False,
        'default_parameters': {'period': 14}
    },
    {
        'variable_id': 'STOCHASTIC',
        'variable_name': '스토캐스틱',
        'english_name': 'iVal',
        'category': MiniChartCategory.INDICATOR,
        'scale_type': MiniChartScaleType.PERCENTAGE_100,
        'display_mode': MiniChartDisplayMode.SUBPLOT,
        'primary_color': '#28a745',  # 녹색
        'scale_min': 0.0,
        'scale_max': 100.0,
        'auto_scale': False,
        'default_parameters': {'k_period': 14, 'd_period': 3}
    },
    {
        'variable_id': 'MACD',
        'variable_name': 'MACD',
        'english_name': 'iVal',
        'category': MiniChartCategory.INDICATOR,
        'scale_type': MiniChartScaleType.UNBOUNDED,
        'display_mode': MiniChartDisplayMode.SUBPLOT,
        'primary_color': '#28a745',  # 녹색
        'default_parameters': {'fast': 12, 'slow': 26, 'signal': 9}
    }
]

# 스케일 그룹 초기 데이터
MINICHART_SCALE_GROUPS = [
    {
        'group_name': 'percentage_100',
        'scale_type': MiniChartScaleType.PERCENTAGE_100,
        'min_value': 0.0,
        'max_value': 100.0,
        'tick_format': '{:.0f}',
        'unit_symbol': '%',
        'reference_lines': [
            {'value': 30, 'label': 'OS(30)', 'color': '#dc3545', 'linestyle': '--'},
            {'value': 50, 'label': 'Mid(50)', 'color': '#6c757d', 'linestyle': '-'},
            {'value': 70, 'label': 'OB(70)', 'color': '#dc3545', 'linestyle': '--'}
        ]
    },
    {
        'group_name': 'price_scale',
        'scale_type': MiniChartScaleType.PRICE_SCALE,
        'min_value': 0.0,
        'max_value': 200000000.0,  # 2억원
        'tick_format': '{:,.0f}',
        'unit_symbol': '원',
        'reference_lines': []
    },
    {
        'group_name': 'volume_scale',
        'scale_type': MiniChartScaleType.VOLUME_SCALE,
        'min_value': 0.0,
        'max_value': 10000000.0,  # 1천만
        'tick_format': '{:,.0f}',
        'unit_symbol': '',
        'reference_lines': []
    }
]
