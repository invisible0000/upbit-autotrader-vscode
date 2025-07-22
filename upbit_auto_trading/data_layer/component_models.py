"""
컴포넌트 기반 전략 모델
Component-based Strategy Models

새로운 아토믹 컴포넌트 시스템을 위한 데이터베이스 모델들
"""

from sqlalchemy import Column, String, Text, JSON, DateTime, Integer, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from .models import Base

class ComponentStrategy(Base):
    """컴포넌트 기반 전략 모델"""
    __tablename__ = 'component_strategy'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 컴포넌트 구성 정보
    triggers = Column(JSON, nullable=False)  # 트리거 컴포넌트들
    conditions = Column(JSON, nullable=True)  # 조건 컴포넌트들
    actions = Column(JSON, nullable=False)  # 액션 컴포넌트들
    
    # 메타데이터
    tags = Column(JSON, nullable=True)  # 태그들
    category = Column(String(50), nullable=True)  # 카테고리
    difficulty = Column(String(20), nullable=True, default='beginner')  # 난이도
    
    # 상태 정보
    is_active = Column(Boolean, nullable=False, default=True)
    is_template = Column(Boolean, nullable=False, default=False)
    
    # 성능 정보 (백테스트 결과 등)
    performance_metrics = Column(JSON, nullable=True)
    
    # 시간 정보
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    executions = relationship("StrategyExecution", back_populates="strategy")
    
    def __repr__(self):
        return f"<ComponentStrategy(id='{self.id}', name='{self.name}', active={self.is_active})>"

class StrategyExecution(Base):
    """전략 실행 기록 모델"""
    __tablename__ = 'strategy_execution'
    
    id = Column(String(50), primary_key=True)
    strategy_id = Column(String(50), ForeignKey('component_strategy.id'), nullable=False)
    
    # 실행 정보
    symbol = Column(String(20), nullable=False)
    trigger_type = Column(String(50), nullable=False)  # 실행된 트리거 타입
    action_type = Column(String(50), nullable=False)  # 실행된 액션 타입
    
    # 시장 상황
    market_data = Column(JSON, nullable=True)  # 실행 시점의 시장 데이터
    
    # 실행 결과
    result = Column(String(20), nullable=False)  # SUCCESS, FAILED, SKIPPED
    result_details = Column(JSON, nullable=True)  # 상세 결과
    
    # 포지션 태그 관련
    position_tag = Column(String(20), nullable=True)  # AUTO, MANUAL, HYBRID, LOCKED
    
    # 시간 정보
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 관계
    strategy = relationship("ComponentStrategy", back_populates="executions")
    
    def __repr__(self):
        return f"<StrategyExecution(id='{self.id}', strategy='{self.strategy_id}', result='{self.result}')>"

class StrategyTemplate(Base):
    """전략 템플릿 모델"""
    __tablename__ = 'strategy_template'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 템플릿 구성
    template_data = Column(JSON, nullable=False)  # 전략 구성 템플릿
    
    # 분류 정보
    category = Column(String(50), nullable=False)
    difficulty = Column(String(20), nullable=False, default='beginner')
    tags = Column(JSON, nullable=True)
    
    # 사용 통계
    usage_count = Column(Integer, nullable=False, default=0)
    
    # 시간 정보
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<StrategyTemplate(id='{self.id}', name='{self.name}', category='{self.category}')>"

class ComponentConfiguration(Base):
    """컴포넌트 설정 모델"""
    __tablename__ = 'component_configuration'
    
    id = Column(String(50), primary_key=True)
    strategy_id = Column(String(50), ForeignKey('component_strategy.id'), nullable=False)
    
    # 컴포넌트 정보
    component_type = Column(String(50), nullable=False)  # trigger, condition, action
    component_name = Column(String(50), nullable=False)  # 컴포넌트 이름
    
    # 설정 데이터
    configuration = Column(JSON, nullable=False)  # 컴포넌트별 설정
    
    # 우선순위 및 활성화
    priority = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # 시간 정보
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    strategy = relationship("ComponentStrategy")
    
    def __repr__(self):
        return f"<ComponentConfiguration(id='{self.id}', type='{self.component_type}', name='{self.component_name}')>"
