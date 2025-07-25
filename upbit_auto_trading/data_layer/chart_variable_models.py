#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
차트 변수 카테고리 모델 정의

변수의 차트 표현 방식과 카테고리를 정의하는 데이터 모델입니다.
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
    SUBPLOT_HISTOGRAM = "subplot_histogram"  # 서브플롯에 히스토그램으로 표시
    SUBPLOT_LEVEL = "subplot_level"         # 서브플롯에 수평선으로 표시


class ChartVariable(Base):
    """차트 변수 정의 테이블"""
    __tablename__ = 'chart_variables'
    
    id = Column(Integer, primary_key=True)
    variable_id = Column(String(50), nullable=False, unique=True, index=True)  # 변수 식별자
    variable_name = Column(String(100), nullable=False)  # 변수 표시명
    description = Column(Text, nullable=True)  # 변수 설명
    
    # 카테고리 정보
    category = Column(SQLEnum(VariableCategory), nullable=False, index=True)
    display_type = Column(SQLEnum(ChartDisplayType), nullable=False)
    
    # 스케일 정보
    scale_min = Column(Float, nullable=True)  # 최소 스케일 (예: RSI는 0)
    scale_max = Column(Float, nullable=True)  # 최대 스케일 (예: RSI는 100)
    unit = Column(String(20), nullable=False, default="")  # 단위 (원, %, 등)
    
    # 표시 설정
    default_color = Column(String(20), nullable=False, default="#007bff")  # 기본 색상
    subplot_height_ratio = Column(Float, nullable=False, default=0.3)  # 서브플롯 높이 비율
    
    # 호환성 설정
    compatible_categories = Column(JSON, nullable=True)  # 허용되는 외부변수 카테고리들
    
    # 메타데이터
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return (f"<ChartVariable(variable_id='{self.variable_id}', "
                f"name='{self.variable_name}', category='{self.category.value}')>")


class VariableCompatibilityRule(Base):
    """변수 호환성 규칙 테이블"""
    __tablename__ = 'variable_compatibility_rules'
    
    id = Column(Integer, primary_key=True)
    base_variable_id = Column(String(50), ForeignKey('chart_variables.variable_id'), nullable=False)
    compatible_category = Column(SQLEnum(VariableCategory), nullable=False)
    compatibility_reason = Column(Text, nullable=True)  # 호환성 이유 설명
    
    # 제약 조건
    min_value_constraint = Column(Float, nullable=True)  # 최소값 제약
    max_value_constraint = Column(Float, nullable=True)  # 최대값 제약
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 관계
    base_variable = relationship("ChartVariable", foreign_keys=[base_variable_id])
    
    def __repr__(self):
        return f"<VariableCompatibilityRule(base='{self.base_variable_id}', compatible='{self.compatible_category.value}')>"


class ChartLayoutTemplate(Base):
    """차트 레이아웃 템플릿 테이블"""
    __tablename__ = 'chart_layout_templates'
    
    id = Column(Integer, primary_key=True)
    template_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # 레이아웃 설정
    main_chart_height_ratio = Column(Float, nullable=False, default=0.6)  # 메인 차트 높이 비율
    subplot_configurations = Column(JSON, nullable=False)  # 서브플롯 설정들
    
    # 색상 팔레트
    color_palette = Column(JSON, nullable=True)  # 색상 팔레트 정의
    
    # 메타데이터
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChartLayoutTemplate(name='{self.template_name}', is_default={self.is_default})>"


class VariableUsageLog(Base):
    """변수 사용 로그 테이블"""
    __tablename__ = 'variable_usage_logs'
    
    id = Column(Integer, primary_key=True)
    variable_id = Column(String(50), ForeignKey('chart_variables.variable_id'), nullable=False)
    condition_id = Column(Integer, nullable=True)  # trading_conditions 테이블의 ID
    
    # 사용 컨텍스트
    usage_context = Column(String(50), nullable=False)  # 'trigger_builder', 'chart_view', 'backtest' 등
    chart_display_info = Column(JSON, nullable=True)  # 실제 차트 표시 정보
    
    # 성능 데이터
    render_time_ms = Column(Integer, nullable=True)  # 렌더링 시간 (밀리초)
    user_feedback = Column(String(20), nullable=True)  # 'helpful', 'confusing', 'irrelevant'
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 관계
    variable = relationship("ChartVariable", foreign_keys=[variable_id])
    
    def __repr__(self):
        return f"<VariableUsageLog(variable_id='{self.variable_id}', context='{self.usage_context}')>"
