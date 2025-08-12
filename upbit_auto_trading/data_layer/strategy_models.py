#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
전략 조합 및 백테스트 관련 데이터 모델 확장

역할 기반 전략 시스템을 위한 새로운 데이터 모델들을 정의합니다.
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import (
    Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Text, JSON,
    Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum

Base = declarative_base()

class ConflictResolutionTypeEnum(str, Enum):
    """충돌 해결 방식"""
    CONSERVATIVE = "conservative"
    PRIORITY = "priority"
    MERGE = "merge"

class StrategyTypeEnum(str, Enum):
    """전략 타입"""
    ENTRY = "entry"
    MANAGEMENT = "management"

class BacktestStatusEnum(str, Enum):
    """백테스트 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# ===== 전략 조합 관련 테이블 =====

class StrategyDefinition(Base):
    """전략 정의 테이블 (역할 기반 전략)"""
    __tablename__ = 'strategy_definitions'
    
    id = Column(String(50), primary_key=True)  # 예: 'rsi_entry', 'averaging_down'
    name = Column(String(100), nullable=False)  # 예: 'RSI 과매수/과매도'
    description = Column(Text, nullable=True)
    strategy_type = Column(String(20), nullable=False)  # 'entry' or 'management'
    class_name = Column(String(100), nullable=False)  # 예: 'RSIEntry'
    default_parameters = Column(JSON, nullable=False)  # 기본 매개변수
    parameter_schema = Column(JSON, nullable=False)  # 매개변수 스키마 (유효성 검사용)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    strategy_configs = relationship("StrategyConfig", back_populates="strategy_definition")
    
    __table_args__ = (
        CheckConstraint(
            strategy_type.in_(['entry', 'management']),
            name='check_strategy_type'
        ),
        Index('idx_strategy_type', strategy_type),
    )
    
    def __repr__(self):
        return f"<StrategyDefinition(id='{self.id}', name='{self.name}', type='{self.strategy_type}')>"

class StrategyCombination(Base):
    """전략 조합 테이블"""
    __tablename__ = 'strategy_combinations'
    
    combination_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 진입 전략 (1개)
    entry_strategy_id = Column(String(50), ForeignKey('strategy_configs.config_id'), nullable=False)
    
    # 충돌 해결 방식
    conflict_resolution = Column(String(20), nullable=False, default='conservative')
    
    # 메타데이터
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50), nullable=True)  # 사용자 ID (향후 확장)
    
    # 관계
    entry_strategy = relationship("StrategyConfig", foreign_keys=[entry_strategy_id])
    management_strategies = relationship("CombinationManagementStrategy", back_populates="combination")
    backtest_results = relationship("BacktestResult", back_populates="combination")
    
    __table_args__ = (
        CheckConstraint(
            conflict_resolution.in_(['conservative', 'priority', 'merge']),
            name='check_conflict_resolution'
        ),
        Index('idx_combination_name', name),
        Index('idx_created_at', created_at),
    )
    
    def __repr__(self):
        return f"<StrategyCombination(id='{self.combination_id}', name='{self.name}')>"

class StrategyConfig(Base):
    """전략 설정 테이블 (매개변수와 함께)"""
    __tablename__ = 'strategy_configs'
    
    config_id = Column(String(50), primary_key=True)
    strategy_definition_id = Column(String(50), ForeignKey('strategy_definitions.id'), nullable=False)
    strategy_name = Column(String(100), nullable=False)  # 사용자 정의 이름
    parameters = Column(JSON, nullable=False)  # 실제 매개변수 값
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    strategy_definition = relationship("StrategyDefinition", back_populates="strategy_configs")
    combination_management_strategies = relationship("CombinationManagementStrategy", back_populates="strategy_config")
    
    __table_args__ = (
        Index('idx_strategy_definition', strategy_definition_id),
        Index('idx_strategy_name', strategy_name),
    )
    
    def __repr__(self):
        return f"<StrategyConfig(id='{self.config_id}', name='{self.strategy_name}')>"

class CombinationManagementStrategy(Base):
    """조합의 관리 전략들 (Many-to-Many 관계)"""
    __tablename__ = 'combination_management_strategies'
    
    id = Column(Integer, primary_key=True)
    combination_id = Column(String(50), ForeignKey('strategy_combinations.combination_id'), nullable=False)
    strategy_config_id = Column(String(50), ForeignKey('strategy_configs.config_id'), nullable=False)
    priority = Column(Integer, nullable=False, default=1)  # 우선순위 (1이 가장 높음)
    
    # 관계
    combination = relationship("StrategyCombination", back_populates="management_strategies")
    strategy_config = relationship("StrategyConfig", back_populates="combination_management_strategies")
    
    __table_args__ = (
        UniqueConstraint('combination_id', 'strategy_config_id', name='uq_combination_strategy'),
        Index('idx_combination_priority', combination_id, priority),
    )
    
    def __repr__(self):
        return f"<CombinationManagementStrategy(combination='{self.combination_id}', priority={self.priority})>"

# ===== 백테스트 관련 테이블 =====

class BacktestResult(Base):
    """백테스트 결과 테이블"""
    __tablename__ = 'backtest_results'
    
    result_id = Column(String(50), primary_key=True)
    combination_id = Column(String(50), ForeignKey('strategy_combinations.combination_id'), nullable=False)
    
    # 백테스트 설정
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)  # '1h', '4h', '1d' 등
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    
    # 수수료 및 슬리피지 설정
    trading_fee_rate = Column(Float, nullable=False, default=0.0005)  # 0.05%
    slippage_rate = Column(Float, nullable=False, default=0.001)     # 0.1%
    
    # 리스크 관리 설정
    risk_settings = Column(JSON, nullable=False)
    
    # 성과 지표
    total_return = Column(Float, nullable=True)        # 총 수익률 (%)
    total_trades = Column(Integer, nullable=True)      # 총 거래 수
    winning_trades = Column(Integer, nullable=True)    # 수익 거래 수
    losing_trades = Column(Integer, nullable=True)     # 손실 거래 수
    win_rate = Column(Float, nullable=True)            # 승률 (%)
    sharpe_ratio = Column(Float, nullable=True)        # 샤프 비율
    max_drawdown = Column(Float, nullable=True)        # 최대 낙폭 (%)
    
    # 전략별 기여도
    entry_contribution = Column(JSON, nullable=True)      # 진입 전략 기여도
    management_contribution = Column(JSON, nullable=True)  # 관리 전략 기여도
    
    # 실행 정보
    status = Column(String(20), nullable=False, default='pending')
    backtest_start = Column(DateTime, nullable=True)
    backtest_end = Column(DateTime, nullable=True)
    data_points = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 관계
    combination = relationship("StrategyCombination", back_populates="backtest_results")
    trade_logs = relationship("TradeLog", back_populates="backtest_result")
    position_logs = relationship("PositionLog", back_populates="backtest_result")
    
    __table_args__ = (
        CheckConstraint(
            status.in_(['pending', 'running', 'completed', 'failed', 'cancelled']),
            name='check_backtest_status'
        ),
        Index('idx_combination_symbol', combination_id, symbol),
        Index('idx_date_range', start_date, end_date),
        Index('idx_status_created', status, created_at),
    )
    
    def __repr__(self):
        return f"<BacktestResult(id='{self.result_id}', combination='{self.combination_id}', symbol='{self.symbol}')>"

class TradeLog(Base):
    """거래 로그 테이블"""
    __tablename__ = 'trade_logs'
    
    id = Column(Integer, primary_key=True)
    backtest_result_id = Column(String(50), ForeignKey('backtest_results.result_id'), nullable=False)
    
    timestamp = Column(DateTime, nullable=False)
    action = Column(String(20), nullable=False)        # 'ENTER', 'EXIT', 'ADD_BUY', 'ADD_SELL'
    direction = Column(String(10), nullable=False)     # 'BUY', 'SELL'
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    
    # 손익 정보 (EXIT 액션에만 적용)
    pnl_percent = Column(Float, nullable=True)         # 손익률 (%)
    pnl_amount = Column(Float, nullable=True)          # 손익 금액
    
    # 전략 정보
    strategy_name = Column(String(100), nullable=True)
    reason = Column(String(200), nullable=True)        # 거래 사유
    
    # 리스크 관리 정보
    stop_price = Column(Float, nullable=True)          # 스탑 가격
    risk_percent = Column(Float, nullable=True)        # 리스크 비율
    holding_time = Column(Float, nullable=True)        # 보유 시간 (시간 단위)
    
    # 관계
    backtest_result = relationship("BacktestResult", back_populates="trade_logs")
    
    __table_args__ = (
        CheckConstraint(
            action.in_(['ENTER', 'EXIT', 'ADD_BUY', 'ADD_SELL', 'UPDATE_STOP']),
            name='check_trade_action'
        ),
        CheckConstraint(
            direction.in_(['BUY', 'SELL']),
            name='check_trade_direction'
        ),
        Index('idx_backtest_timestamp', backtest_result_id, timestamp),
        Index('idx_action_direction', action, direction),
    )
    
    def __repr__(self):
        return f"<TradeLog(backtest='{self.backtest_result_id}', action='{self.action}', timestamp='{self.timestamp}')>"

class PositionLog(Base):
    """포지션 로그 테이블"""
    __tablename__ = 'position_logs'
    
    id = Column(Integer, primary_key=True)
    backtest_result_id = Column(String(50), ForeignKey('backtest_results.result_id'), nullable=False)
    
    timestamp = Column(DateTime, nullable=False)
    direction = Column(String(10), nullable=False)     # 'BUY', 'SELL'
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    stop_price = Column(Float, nullable=True)
    
    # 손익 정보
    unrealized_pnl_percent = Column(Float, nullable=False)  # 미실현 손익률
    unrealized_pnl_amount = Column(Float, nullable=False)   # 미실현 손익 금액
    
    # 관리 전략 이력
    management_actions = Column(JSON, nullable=True)        # 관리 액션 이력
    
    # 관계
    backtest_result = relationship("BacktestResult", back_populates="position_logs")
    
    __table_args__ = (
        CheckConstraint(
            direction.in_(['BUY', 'SELL']),
            name='check_position_direction'
        ),
        Index('idx_backtest_timestamp', backtest_result_id, timestamp),
    )
    
    def __repr__(self):
        return f"<PositionLog(backtest='{self.backtest_result_id}', timestamp='{self.timestamp}')>"

# ===== 매개변수 최적화 관련 테이블 =====

class OptimizationJob(Base):
    """매개변수 최적화 작업 테이블"""
    __tablename__ = 'optimization_jobs'
    
    job_id = Column(String(50), primary_key=True)
    combination_id = Column(String(50), ForeignKey('strategy_combinations.combination_id'), nullable=False)
    
    # 최적화 설정
    algorithm = Column(String(20), nullable=False)     # 'GA', 'PSO', 'RANDOM'
    parameter_ranges = Column(JSON, nullable=False)    # 매개변수 범위 정의
    optimization_target = Column(String(50), nullable=False)  # 'fitness_score', 'sharpe_ratio', 'total_return'
    
    # 알고리즘 설정
    population_size = Column(Integer, nullable=True)   # GA/PSO 개체 수
    generations = Column(Integer, nullable=True)       # GA 세대 수
    iterations = Column(Integer, nullable=True)        # PSO 반복 수
    
    # 실행 정보
    status = Column(String(20), nullable=False, default='pending')
    progress = Column(Float, nullable=False, default=0.0)  # 진행률 (0.0 ~ 1.0)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 결과 정보
    best_parameters = Column(JSON, nullable=True)      # 최적 매개변수
    best_fitness = Column(Float, nullable=True)        # 최적 적합도 점수
    convergence_data = Column(JSON, nullable=True)     # 수렴 데이터
    
    # 관계
    combination = relationship("StrategyCombination")
    optimization_results = relationship("OptimizationResult", back_populates="job")
    
    __table_args__ = (
        CheckConstraint(
            algorithm.in_(['GA', 'PSO', 'RANDOM', 'GRID']),
            name='check_algorithm'
        ),
        CheckConstraint(
            status.in_(['pending', 'running', 'completed', 'failed', 'cancelled']),
            name='check_optimization_status'
        ),
        CheckConstraint(
            optimization_target.in_(['fitness_score', 'sharpe_ratio', 'total_return', 'win_rate']),
            name='check_optimization_target'
        ),
        Index('idx_combination_status', combination_id, status),
        Index('idx_created_at', created_at),
    )
    
    def __repr__(self):
        return f"<OptimizationJob(id='{self.job_id}', algorithm='{self.algorithm}', status='{self.status}')>"

class OptimizationResult(Base):
    """최적화 결과 테이블 (각 세대/반복의 결과)"""
    __tablename__ = 'optimization_results'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(50), ForeignKey('optimization_jobs.job_id'), nullable=False)
    
    generation = Column(Integer, nullable=False)       # 세대/반복 번호
    individual_id = Column(Integer, nullable=False)    # 개체 번호
    
    parameters = Column(JSON, nullable=False)          # 매개변수 조합
    fitness_score = Column(Float, nullable=False)      # 적합도 점수
    
    # 성과 지표
    total_return = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 관계
    job = relationship("OptimizationJob", back_populates="optimization_results")
    
    __table_args__ = (
        Index('idx_job_generation', job_id, generation),
        Index('idx_fitness_score', fitness_score.desc()),
    )
    
    def __repr__(self):
        return f"<OptimizationResult(job='{self.job_id}', gen={self.generation}, fitness={self.fitness_score:.2f})>"

# ===== 실시간 거래 관련 테이블 =====

class LiveTradingSession(Base):
    """실시간 거래 세션 테이블"""
    __tablename__ = 'live_trading_sessions'
    
    session_id = Column(String(50), primary_key=True)
    combination_id = Column(String(50), ForeignKey('strategy_combinations.combination_id'), nullable=False)
    
    # 거래 설정
    symbol = Column(String(20), nullable=False)
    allocated_capital = Column(Float, nullable=False)
    risk_settings = Column(JSON, nullable=False)
    
    # 세션 정보
    status = Column(String(20), nullable=False, default='active')
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)
    
    # 성과 추적
    current_capital = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False, default=0.0)
    total_trades = Column(Integer, nullable=False, default=0)
    
    # 관계
    combination = relationship("StrategyCombination")
    live_trades = relationship("LiveTrade", back_populates="session")
    
    __table_args__ = (
        CheckConstraint(
            status.in_(['active', 'paused', 'stopped', 'error']),
            name='check_session_status'
        ),
        Index('idx_symbol_status', symbol, status),
        Index('idx_started_at', started_at),
    )
    
    def __repr__(self):
        return f"<LiveTradingSession(id='{self.session_id}', symbol='{self.symbol}', status='{self.status}')>"

class LiveTrade(Base):
    """실시간 거래 기록 테이블"""
    __tablename__ = 'live_trades'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), ForeignKey('live_trading_sessions.session_id'), nullable=False)
    
    # 거래 정보
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    action = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    
    # 거래소 정보
    exchange_order_id = Column(String(100), nullable=True)
    exchange_trade_id = Column(String(100), nullable=True)
    fee = Column(Float, nullable=True)
    
    # 전략 정보
    strategy_name = Column(String(100), nullable=True)
    reason = Column(String(200), nullable=True)
    
    # 손익 정보 (청산 시)
    pnl_percent = Column(Float, nullable=True)
    pnl_amount = Column(Float, nullable=True)
    
    # 관계
    session = relationship("LiveTradingSession", back_populates="live_trades")
    
    __table_args__ = (
        CheckConstraint(
            action.in_(['ENTER', 'EXIT', 'ADD_BUY', 'ADD_SELL', 'UPDATE_STOP']),
            name='check_live_trade_action'
        ),
        CheckConstraint(
            direction.in_(['BUY', 'SELL']),
            name='check_live_trade_direction'
        ),
        Index('idx_session_timestamp', session_id, timestamp),
        Index('idx_exchange_order', exchange_order_id),
    )
    
    def __repr__(self):
        return f"<LiveTrade(session='{self.session_id}', action='{self.action}', timestamp='{self.timestamp}')>"
