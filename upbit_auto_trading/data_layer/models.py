#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터 모델 정의

시장 데이터, 전략, 백테스트 등의 데이터 모델을 정의합니다.
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class OHLCV(Base):
    """OHLCV 데이터 모델"""
    __tablename__ = 'ohlcv'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    timeframe = Column(String(10), nullable=False, index=True)
    
    def __repr__(self):
        return f"<OHLCV(symbol='{self.symbol}', timestamp='{self.timestamp}', timeframe='{self.timeframe}')>"

class OrderBook(Base):
    """호가 데이터 모델"""
    __tablename__ = 'orderbook'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    asks = Column(JSON, nullable=False)  # 매도 호가 목록 (JSON 형식)
    bids = Column(JSON, nullable=False)  # 매수 호가 목록 (JSON 형식)
    
    def __repr__(self):
        return f"<OrderBook(symbol='{self.symbol}', timestamp='{self.timestamp}')>"

class Trade(Base):
    """거래 데이터 모델"""
    __tablename__ = 'trade'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    side = Column(String(10), nullable=False)  # 'buy' 또는 'sell'
    order_id = Column(String(50), nullable=True)
    fee = Column(Float, nullable=True)
    
    # 백테스트 관계 (선택적)
    backtest_id = Column(String(50), ForeignKey('backtest.id'), nullable=True)
    backtest = relationship("Backtest", back_populates="trades")
    
    def __repr__(self):
        return f"<Trade(symbol='{self.symbol}', timestamp='{self.timestamp}', side='{self.side}')>"

class Strategy(Base):
    """전략 모델"""
    __tablename__ = 'strategy'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=False)  # 전략 매개변수 (JSON 형식)
    
    # 전략 성질들
    signal_type = Column(String(20), nullable=False, default='BUY_SELL')  # 신호 타입: BUY_SELL, STOP_LOSS, TRAILING, TAKE_PROFIT, PARTIAL_EXIT, TIME_EXIT, VOLATILITY, ADD_BUY
    role = Column(String(20), nullable=False, default='ENTRY')  # 역할: ENTRY, EXIT, SCALE_IN, SCALE_OUT, MANAGEMENT
    position_required = Column(Boolean, nullable=False, default=False)  # 포지션 보유 필요 여부
    market_phase = Column(String(20), nullable=True, default='ALL')  # 시장 환경: ALL, TREND, VOLATILE, SIDEWAYS
    risk_level = Column(String(20), nullable=True, default='MEDIUM')  # 위험도: LOW, MEDIUM, HIGH, VERY_HIGH
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    backtests = relationship("Backtest", back_populates="strategy")
    portfolio_coins = relationship("PortfolioCoin", back_populates="strategy")
    
    def __repr__(self):
        return f"<Strategy(id='{self.id}', name='{self.name}', role='{self.role}', signal_type='{self.signal_type}')>"

class Backtest(Base):
    """백테스트 모델"""
    __tablename__ = 'backtest'
    
    id = Column(String(50), primary_key=True)
    strategy_id = Column(String(50), ForeignKey('strategy.id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    portfolio_id = Column(String(50), ForeignKey('portfolio.id'), nullable=True)
    timeframe = Column(String(10), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    performance_metrics = Column(JSON, nullable=True)  # 성과 지표 (JSON 형식)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 관계
    strategy = relationship("Strategy", back_populates="backtests")
    portfolio = relationship("Portfolio", back_populates="backtests")
    trades = relationship("Trade", back_populates="backtest")
    
    def __repr__(self):
        return f"<Backtest(id='{self.id}', strategy_id='{self.strategy_id}', symbol='{self.symbol}')>"

class Portfolio(Base):
    """포트폴리오 모델"""
    __tablename__ = 'portfolio'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    coins = relationship("PortfolioCoin", back_populates="portfolio")
    backtests = relationship("Backtest", back_populates="portfolio")
    
    def __repr__(self):
        return f"<Portfolio(id='{self.id}', name='{self.name}')>"

class PortfolioCoin(Base):
    """포트폴리오 코인 모델"""
    __tablename__ = 'portfolio_coin'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(String(50), ForeignKey('portfolio.id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    strategy_id = Column(String(50), ForeignKey('strategy.id'), nullable=False)
    weight = Column(Float, nullable=False)
    
    # 관계
    portfolio = relationship("Portfolio", back_populates="coins")
    strategy = relationship("Strategy", back_populates="portfolio_coins")
    
    def __repr__(self):
        return f"<PortfolioCoin(portfolio_id='{self.portfolio_id}', symbol='{self.symbol}', weight={self.weight})>"

class TradingSession(Base):
    """거래 세션 모델"""
    __tablename__ = 'trading_session'
    
    id = Column(String(50), primary_key=True)
    strategy_id = Column(String(50), ForeignKey('strategy.id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)  # 'active', 'paused', 'stopped'
    amount = Column(Float, nullable=False)
    risk_params = Column(JSON, nullable=False)  # 위험 관리 설정 (JSON 형식)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<TradingSession(id='{self.id}', strategy_id='{self.strategy_id}', symbol='{self.symbol}', status='{self.status}')>"

class Notification(Base):
    """알림 모델"""
    __tablename__ = 'notification'
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)  # 'trade', 'price', 'system'
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    read = Column(Boolean, nullable=False, default=False)
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type='{self.type}', timestamp='{self.timestamp}')>"

class StrategyCombination(Base):
    """전략 조합 모델"""
    __tablename__ = 'strategy_combination'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    entry_strategy_id = Column(String(50), ForeignKey('strategy.id'), nullable=False)
    execution_order = Column(String(20), nullable=False, default='parallel')  # 'parallel', 'sequential'
    conflict_resolution = Column(String(20), nullable=False, default='conservative')  # 'conservative', 'aggressive'
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    entry_strategy = relationship("Strategy", foreign_keys=[entry_strategy_id])
    management_strategies = relationship("CombinationManagementStrategy", back_populates="combination")
    
    def __repr__(self):
        return f"<StrategyCombination(id='{self.id}', name='{self.name}', is_active={self.is_active})>"

class CombinationManagementStrategy(Base):
    """조합에 포함된 관리 전략 모델"""
    __tablename__ = 'combination_management_strategy'
    
    id = Column(Integer, primary_key=True)
    combination_id = Column(String(50), ForeignKey('strategy_combination.id'), nullable=False)
    strategy_id = Column(String(50), ForeignKey('strategy.id'), nullable=False)
    priority = Column(Integer, nullable=False, default=1)  # 우선순위 (1이 최고)
    weight = Column(Float, nullable=False, default=1.0)  # 가중치
    is_active = Column(Boolean, nullable=False, default=True)
    
    # 관계
    combination = relationship("StrategyCombination", back_populates="management_strategies")
    strategy = relationship("Strategy")
    
    def __repr__(self):
        return f"<CombinationManagementStrategy(combination_id='{self.combination_id}', strategy_id='{self.strategy_id}', priority={self.priority})>"