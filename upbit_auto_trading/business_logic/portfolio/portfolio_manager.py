#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
포트폴리오 관리자 모듈

포트폴리오 생성, 관리, 코인 추가/제거 등의 기능을 제공합니다.
"""

import uuid
from typing import Dict, List, Optional, Union
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from upbit_auto_trading.data_layer.models import Portfolio, PortfolioCoin, Strategy

class PortfolioManager:
    """포트폴리오 관리자 클래스"""

    def __init__(self, session: Session):
        """
        포트폴리오 관리자 초기화
        
        Args:
            session: SQLAlchemy 세션
        """
        self.session = session

    def create_portfolio(self, name: str, description: Optional[str] = None) -> str:
        """
        새 포트폴리오 생성
        
        Args:
            name: 포트폴리오 이름
            description: 포트폴리오 설명 (선택적)
            
        Returns:
            생성된 포트폴리오 ID
        """
        try:
            # 고유 ID 생성
            portfolio_id = str(uuid.uuid4())
            
            # 포트폴리오 객체 생성
            portfolio = Portfolio(
                id=portfolio_id,
                name=name,
                description=description
            )
            
            # 데이터베이스에 저장
            self.session.add(portfolio)
            self.session.commit()
            
            return portfolio_id
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ValueError(f"포트폴리오 생성 중 오류 발생: {str(e)}")

    def add_coin_to_portfolio(self, portfolio_id: str, symbol: str, strategy_id: str, weight: float) -> bool:
        """
        포트폴리오에 코인 추가
        
        Args:
            portfolio_id: 포트폴리오 ID
            symbol: 코인 심볼 (예: 'KRW-BTC')
            strategy_id: 전략 ID
            weight: 가중치 (0.0 ~ 1.0)
            
        Returns:
            성공 여부
        """
        try:
            # 포트폴리오 존재 여부 확인
            portfolio = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
            if not portfolio:
                raise ValueError(f"ID가 {portfolio_id}인 포트폴리오를 찾을 수 없습니다.")
            
            # 전략 존재 여부 확인
            strategy = self.session.query(Strategy).filter_by(id=strategy_id).first()
            if not strategy:
                raise ValueError(f"ID가 {strategy_id}인 전략을 찾을 수 없습니다.")
            
            # 가중치 유효성 검사
            if weight < 0.0 or weight > 1.0:
                raise ValueError("가중치는 0.0에서 1.0 사이의 값이어야 합니다.")
            
            # 이미 존재하는 코인인지 확인
            existing_coin = self.session.query(PortfolioCoin).filter_by(
                portfolio_id=portfolio_id, symbol=symbol
            ).first()
            
            if existing_coin:
                # 이미 존재하는 경우 업데이트
                existing_coin.strategy_id = strategy_id
                existing_coin.weight = weight
            else:
                # 새 코인 추가
                portfolio_coin = PortfolioCoin(
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    strategy_id=strategy_id,
                    weight=weight
                )
                self.session.add(portfolio_coin)
            
            # 포트폴리오 업데이트 시간 갱신
            portfolio.updated_at = datetime.utcnow()
            
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ValueError(f"코인 추가 중 오류 발생: {str(e)}")

    def remove_coin_from_portfolio(self, portfolio_id: str, symbol: str) -> bool:
        """
        포트폴리오에서 코인 제거
        
        Args:
            portfolio_id: 포트폴리오 ID
            symbol: 코인 심볼 (예: 'KRW-BTC')
            
        Returns:
            성공 여부
        """
        try:
            # 포트폴리오 존재 여부 확인
            portfolio = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
            if not portfolio:
                raise ValueError(f"ID가 {portfolio_id}인 포트폴리오를 찾을 수 없습니다.")
            
            # 코인 찾기
            portfolio_coin = self.session.query(PortfolioCoin).filter_by(
                portfolio_id=portfolio_id, symbol=symbol
            ).first()
            
            if not portfolio_coin:
                raise ValueError(f"포트폴리오에서 {symbol} 코인을 찾을 수 없습니다.")
            
            # 코인 제거
            self.session.delete(portfolio_coin)
            
            # 포트폴리오 업데이트 시간 갱신
            portfolio.updated_at = datetime.utcnow()
            
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ValueError(f"코인 제거 중 오류 발생: {str(e)}")

    def update_portfolio(self, portfolio_id: str, name: Optional[str] = None, 
                         description: Optional[str] = None) -> bool:
        """
        포트폴리오 정보 업데이트
        
        Args:
            portfolio_id: 포트폴리오 ID
            name: 새 포트폴리오 이름 (선택적)
            description: 새 포트폴리오 설명 (선택적)
            
        Returns:
            성공 여부
        """
        try:
            # 포트폴리오 존재 여부 확인
            portfolio = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
            if not portfolio:
                raise ValueError(f"ID가 {portfolio_id}인 포트폴리오를 찾을 수 없습니다.")
            
            # 정보 업데이트
            if name is not None:
                portfolio.name = name
            
            if description is not None:
                portfolio.description = description
            
            # 업데이트 시간 갱신
            portfolio.updated_at = datetime.utcnow()
            
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ValueError(f"포트폴리오 업데이트 중 오류 발생: {str(e)}")

    def update_coin_weight(self, portfolio_id: str, symbol: str, weight: float) -> bool:
        """
        포트폴리오 내 코인 가중치 업데이트
        
        Args:
            portfolio_id: 포트폴리오 ID
            symbol: 코인 심볼 (예: 'KRW-BTC')
            weight: 새 가중치 (0.0 ~ 1.0)
            
        Returns:
            성공 여부
        """
        try:
            # 포트폴리오 존재 여부 확인
            portfolio = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
            if not portfolio:
                raise ValueError(f"ID가 {portfolio_id}인 포트폴리오를 찾을 수 없습니다.")
            
            # 가중치 유효성 검사
            if weight < 0.0 or weight > 1.0:
                raise ValueError("가중치는 0.0에서 1.0 사이의 값이어야 합니다.")
            
            # 코인 찾기
            portfolio_coin = self.session.query(PortfolioCoin).filter_by(
                portfolio_id=portfolio_id, symbol=symbol
            ).first()
            
            if not portfolio_coin:
                raise ValueError(f"포트폴리오에서 {symbol} 코인을 찾을 수 없습니다.")
            
            # 가중치 업데이트
            portfolio_coin.weight = weight
            
            # 포트폴리오 업데이트 시간 갱신
            portfolio.updated_at = datetime.utcnow()
            
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ValueError(f"코인 가중치 업데이트 중 오류 발생: {str(e)}")

    def get_portfolio(self, portfolio_id: str) -> Dict:
        """
        포트폴리오 정보 조회
        
        Args:
            portfolio_id: 포트폴리오 ID
            
        Returns:
            포트폴리오 정보 딕셔너리
        """
        try:
            # 포트폴리오 조회
            portfolio = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
            if not portfolio:
                raise ValueError(f"ID가 {portfolio_id}인 포트폴리오를 찾을 수 없습니다.")
            
            # 포트폴리오 정보 구성
            portfolio_data = {
                "id": portfolio.id,
                "name": portfolio.name,
                "description": portfolio.description,
                "created_at": portfolio.created_at.isoformat(),
                "updated_at": portfolio.updated_at.isoformat(),
                "coins": []
            }
            
            # 코인 정보 추가
            for coin in portfolio.coins:
                coin_data = {
                    "symbol": coin.symbol,
                    "strategy_id": coin.strategy_id,
                    "weight": coin.weight
                }
                portfolio_data["coins"].append(coin_data)
            
            return portfolio_data
        except SQLAlchemyError as e:
            raise ValueError(f"포트폴리오 조회 중 오류 발생: {str(e)}")

    def get_all_portfolios(self) -> List[Dict]:
        """
        모든 포트폴리오 조회
        
        Returns:
            포트폴리오 정보 딕셔너리 리스트
        """
        try:
            # 모든 포트폴리오 조회
            portfolios = self.session.query(Portfolio).all()
            
            # 포트폴리오 정보 리스트 구성
            portfolio_list = []
            for portfolio in portfolios:
                portfolio_data = {
                    "id": portfolio.id,
                    "name": portfolio.name,
                    "description": portfolio.description,
                    "created_at": portfolio.created_at.isoformat(),
                    "updated_at": portfolio.updated_at.isoformat(),
                    "coin_count": len(portfolio.coins)
                }
                portfolio_list.append(portfolio_data)
            
            return portfolio_list
        except SQLAlchemyError as e:
            raise ValueError(f"포트폴리오 목록 조회 중 오류 발생: {str(e)}")

    def delete_portfolio(self, portfolio_id: str) -> bool:
        """
        포트폴리오 삭제
        
        Args:
            portfolio_id: 포트폴리오 ID
            
        Returns:
            성공 여부
        """
        try:
            # 포트폴리오 존재 여부 확인
            portfolio = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
            if not portfolio:
                raise ValueError(f"ID가 {portfolio_id}인 포트폴리오를 찾을 수 없습니다.")
            
            # 연결된 코인 삭제
            self.session.query(PortfolioCoin).filter_by(portfolio_id=portfolio_id).delete()
            
            # 포트폴리오 삭제
            self.session.delete(portfolio)
            
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ValueError(f"포트폴리오 삭제 중 오류 발생: {str(e)}")

    def validate_portfolio_weights(self, portfolio_id: str) -> bool:
        """
        포트폴리오 가중치 합이 1.0인지 검증
        
        Args:
            portfolio_id: 포트폴리오 ID
            
        Returns:
            가중치 합이 1.0이면 True, 아니면 False
        """
        try:
            # 포트폴리오 존재 여부 확인
            portfolio = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
            if not portfolio:
                raise ValueError(f"ID가 {portfolio_id}인 포트폴리오를 찾을 수 없습니다.")
            
            # 코인이 없는 경우
            if not portfolio.coins:
                return True
            
            # 가중치 합계 계산
            total_weight = sum(coin.weight for coin in portfolio.coins)
            
            # 부동 소수점 오차를 고려하여 비교 (0.001 오차 허용)
            return abs(total_weight - 1.0) < 0.001
        except SQLAlchemyError as e:
            raise ValueError(f"포트폴리오 가중치 검증 중 오류 발생: {str(e)}")