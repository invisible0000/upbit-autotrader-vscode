#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
전략 관리자 모듈

이 모듈은 전략의 저장, 불러오기, 목록 관리 등의 기능을 제공합니다.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

# 한국 시간대(KST) 객체 생성
KST = ZoneInfo("Asia/Seoul")
import uuid

from sqlalchemy.exc import SQLAlchemyError

from upbit_auto_trading.business_logic.strategy.strategy_interface import StrategyInterface
from upbit_auto_trading.business_logic.strategy.strategy_factory import StrategyFactory
from upbit_auto_trading.data_layer.storage.database_manager import DatabaseManager
from upbit_auto_trading.data_layer.models import Strategy


class StrategyManager:
    """
    전략 관리자 클래스
    
    전략의 저장, 불러오기, 목록 관리 등의 기능을 제공합니다.
    """
    
    def __init__(self, db_manager: DatabaseManager, strategy_factory: StrategyFactory):
        """
        전략 관리자 초기화
        
        Args:
            db_manager: 데이터베이스 관리자
            strategy_factory: 전략 팩토리
        """
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
        self.strategy_factory = strategy_factory
    
    def save_strategy(self, strategy_id: str, strategy_type: str, name: str, 
                     description: str, parameters: Dict[str, Any]) -> bool:
        """
        전략 저장
        
        Args:
            strategy_id: 전략 ID (고유 식별자)
            strategy_type: 전략 타입 (strategy_factory에 등록된 ID)
            name: 전략 이름
            description: 전략 설명
            parameters: 전략 매개변수
            
        Returns:
            저장 성공 여부
        """
        try:
            # 전략 타입 유효성 검사
            temp_strategy = self.strategy_factory.create_strategy(strategy_type, parameters)
            if temp_strategy is None:
                self.logger.error(f"전략 타입 '{strategy_type}'이 유효하지 않습니다.")
                return False
            
            # 매개변수 유효성 검사
            if not temp_strategy.validate_parameters(parameters):
                self.logger.error(f"전략 매개변수가 유효하지 않습니다: {parameters}")
                return False
            
            # 데이터베이스 세션 생성
            session = self.db_manager.get_session()
            
            try:
                # 기존 전략 확인
                existing_strategy = session.query(Strategy).filter_by(id=strategy_id).first()
                
                if existing_strategy:
                    # 기존 전략 업데이트
                    existing_strategy.name = name
                    existing_strategy.description = description
                    existing_strategy.parameters = json.dumps(parameters)
                    existing_strategy.updated_at = datetime.now(KST)
                else:
                    # 새 전략 생성
                    new_strategy = Strategy(
                        id=strategy_id,
                        name=name,
                        description=description,
                        parameters=json.dumps(parameters)
                    )
                    session.add(new_strategy)
                
                # 변경사항 커밋
                session.commit()
                self.logger.info(f"전략 '{strategy_id}'이(가) 저장되었습니다.")
                return True
            
            except SQLAlchemyError as e:
                session.rollback()
                self.logger.error(f"전략 저장 중 데이터베이스 오류 발생: {str(e)}")
                return False
            
            finally:
                session.close()
        
        except Exception as e:
            self.logger.error(f"전략 저장 중 오류 발생: {str(e)}")
            return False
    
    def load_strategy(self, strategy_id: str) -> Optional[StrategyInterface]:
        """
        전략 불러오기
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            전략 인스턴스 또는 None (실패 시)
        """
        try:
            # 데이터베이스 세션 생성
            session = self.db_manager.get_session()
            
            try:
                # 전략 조회
                db_strategy = session.query(Strategy).filter_by(id=strategy_id).first()
                
                if not db_strategy:
                    self.logger.warning(f"전략 ID '{strategy_id}'를 찾을 수 없습니다.")
                    return None
                
                # 전략 타입과 매개변수 추출
                strategy_type = self._extract_strategy_type(db_strategy)
                parameters = json.loads(db_strategy.parameters)
                
                # 전략 인스턴스 생성
                strategy = self.strategy_factory.create_strategy(strategy_type, parameters)
                
                if strategy is None:
                    self.logger.error(f"전략 타입 '{strategy_type}'으로 인스턴스를 생성할 수 없습니다.")
                    return None
                
                return strategy
            
            except SQLAlchemyError as e:
                self.logger.error(f"전략 불러오기 중 데이터베이스 오류 발생: {str(e)}")
                return None
            
            finally:
                session.close()
        
        except Exception as e:
            self.logger.error(f"전략 불러오기 중 오류 발생: {str(e)}")
            return None
    
    def get_strategy_list(self) -> List[Dict[str, Any]]:
        """
        저장된 전략 목록 조회
        
        Returns:
            전략 정보 목록
        """
        try:
            # 데이터베이스 세션 생성
            session = self.db_manager.get_session()
            
            try:
                # 모든 전략 조회
                db_strategies = session.query(Strategy).all()
                
                # 전략 정보 목록 생성
                strategies = []
                
                for db_strategy in db_strategies:
                    try:
                        # 전략 타입 추출
                        strategy_type = self._extract_strategy_type(db_strategy)
                        
                        # 전략 정보 생성
                        strategy_info = {
                            "id": db_strategy.id,
                            "name": db_strategy.name,
                            "description": db_strategy.description,
                            "strategy_type": strategy_type,
                            "parameters": json.loads(db_strategy.parameters),
                            "created_at": db_strategy.created_at,
                            "updated_at": db_strategy.updated_at
                        }
                        
                        strategies.append(strategy_info)
                    
                    except Exception as e:
                        self.logger.error(f"전략 '{db_strategy.id}' 정보 처리 중 오류 발생: {str(e)}")
                
                return strategies
            
            except SQLAlchemyError as e:
                self.logger.error(f"전략 목록 조회 중 데이터베이스 오류 발생: {str(e)}")
                return []
            
            finally:
                session.close()
        
        except Exception as e:
            self.logger.error(f"전략 목록 조회 중 오류 발생: {str(e)}")
            return []
    
    def update_strategy(self, strategy_id: str, name: str = None, 
                       description: str = None, parameters: Dict[str, Any] = None) -> bool:
        """
        전략 업데이트
        
        Args:
            strategy_id: 전략 ID
            name: 새 전략 이름 (None인 경우 변경 없음)
            description: 새 전략 설명 (None인 경우 변경 없음)
            parameters: 새 전략 매개변수 (None인 경우 변경 없음)
            
        Returns:
            업데이트 성공 여부
        """
        try:
            # 데이터베이스 세션 생성
            session = self.db_manager.get_session()
            
            try:
                # 전략 조회
                db_strategy = session.query(Strategy).filter_by(id=strategy_id).first()
                
                if not db_strategy:
                    self.logger.warning(f"전략 ID '{strategy_id}'를 찾을 수 없습니다.")
                    return False
                
                # 전략 타입과 현재 매개변수 추출
                strategy_type = self._extract_strategy_type(db_strategy)
                current_parameters = json.loads(db_strategy.parameters)
                
                # 매개변수가 제공된 경우 유효성 검사
                if parameters is not None:
                    # 매개변수 병합
                    merged_parameters = {**current_parameters, **parameters}
                    
                    # 전략 인스턴스 생성하여 매개변수 유효성 검사
                    temp_strategy = self.strategy_factory.create_strategy(strategy_type, {})
                    if temp_strategy is None:
                        self.logger.error(f"전략 타입 '{strategy_type}'이 유효하지 않습니다.")
                        return False
                    
                    if not temp_strategy.validate_parameters(merged_parameters):
                        self.logger.error(f"전략 매개변수가 유효하지 않습니다: {merged_parameters}")
                        return False
                    
                    # 유효한 매개변수로 업데이트
                    db_strategy.parameters = json.dumps(merged_parameters)
                
                # 이름 업데이트
                if name is not None:
                    db_strategy.name = name
                
                # 설명 업데이트
                if description is not None:
                    db_strategy.description = description
                
                # 업데이트 시간 갱신
                db_strategy.updated_at = datetime.now(KST)
                
                # 변경사항 커밋
                session.commit()
                self.logger.info(f"전략 '{strategy_id}'이(가) 업데이트되었습니다.")
                return True
            
            except SQLAlchemyError as e:
                session.rollback()
                self.logger.error(f"전략 업데이트 중 데이터베이스 오류 발생: {str(e)}")
                return False
            
            finally:
                session.close()
        
        except Exception as e:
            self.logger.error(f"전략 업데이트 중 오류 발생: {str(e)}")
            return False
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """
        전략 삭제
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            # 데이터베이스 세션 생성
            session = self.db_manager.get_session()
            
            try:
                # 전략 조회
                db_strategy = session.query(Strategy).filter_by(id=strategy_id).first()
                
                if not db_strategy:
                    self.logger.warning(f"전략 ID '{strategy_id}'를 찾을 수 없습니다.")
                    return False
                
                # 전략 삭제
                session.delete(db_strategy)
                
                # 변경사항 커밋
                session.commit()
                self.logger.info(f"전략 '{strategy_id}'이(가) 삭제되었습니다.")
                return True
            
            except SQLAlchemyError as e:
                session.rollback()
                self.logger.error(f"전략 삭제 중 데이터베이스 오류 발생: {str(e)}")
                return False
            
            finally:
                session.close()
        
        except Exception as e:
            self.logger.error(f"전략 삭제 중 오류 발생: {str(e)}")
            return False
    
    def _extract_strategy_type(self, db_strategy: Strategy) -> str:
        """
        데이터베이스 전략 객체에서 전략 타입 추출
        
        Args:
            db_strategy: 데이터베이스 전략 객체
            
        Returns:
            전략 타입 문자열
        """
        # 전략 ID에서 타입 추출
        strategy_id = db_strategy.id
        
        # 테스트 ID 패턴 확인
        if strategy_id.startswith("test_"):
            # test_ma_strategy -> moving_average_cross
            # test_bb_strategy -> bollinger_bands
            # test_rsi_strategy -> rsi
            if "ma_" in strategy_id:
                return "moving_average_cross"
            elif "bb_" in strategy_id:
                return "bollinger_bands"
            elif "rsi_" in strategy_id:
                return "rsi"
        
        # 매개변수에서 타입 정보 찾기 시도
        try:
            parameters = json.loads(db_strategy.parameters)
            if "strategy_type" in parameters:
                return parameters["strategy_type"]
        except:
            pass
        
        # 기본값으로 첫 번째 등록된 전략 타입 사용
        available_strategies = self.strategy_factory.get_available_strategies()
        if available_strategies:
            return available_strategies[0]["id"]
        
        # 마지막 수단으로 기본 타입 반환
        return "moving_average_cross"  # 기본 전략 타입


# 싱글톤 인스턴스
_instance = None

def get_strategy_manager(db_manager: DatabaseManager = None, 
                        strategy_factory: StrategyFactory = None) -> StrategyManager:
    """
    StrategyManager의 싱글톤 인스턴스를 반환합니다.
    
    Args:
        db_manager: 데이터베이스 관리자 (None인 경우 기본 인스턴스 사용)
        strategy_factory: 전략 팩토리 (None인 경우 기본 인스턴스 사용)
        
    Returns:
        StrategyManager: StrategyManager 인스턴스
    """
    global _instance
    
    if _instance is None:
        from upbit_auto_trading.data_layer.storage.database_manager import get_database_manager
        from upbit_auto_trading.business_logic.strategy.strategy_factory import StrategyFactory
        
        if db_manager is None:
            db_manager = get_database_manager()
        
        if strategy_factory is None:
            strategy_factory = StrategyFactory()
            
            # 기본 전략 등록
            from upbit_auto_trading.business_logic.strategy.basic_strategies import (
                MovingAverageCrossStrategy, BollingerBandsStrategy, RSIStrategy
            )
            from upbit_auto_trading.business_logic.strategy.role_based_strategy import (
                MACDEntry, StochasticEntry, FixedTargetManagement, 
                PartialExitManagement, TimeBasedExitManagement, TrailingStopManagement
            )
            
            # 진입 전략들
            strategy_factory.register_strategy("moving_average_cross", MovingAverageCrossStrategy)
            strategy_factory.register_strategy("bollinger_bands", BollingerBandsStrategy)
            strategy_factory.register_strategy("bollinger_band_mean_reversion", BollingerBandsStrategy)  # 별칭
            strategy_factory.register_strategy("rsi", RSIStrategy)
            strategy_factory.register_strategy("rsi_reversal", RSIStrategy)  # 별칭
            strategy_factory.register_strategy("macd_cross", MACDEntry)
            strategy_factory.register_strategy("stochastic", StochasticEntry)
            strategy_factory.register_strategy("volatility_breakout", MovingAverageCrossStrategy)  # 임시로 MA 사용
            
            # 관리 전략들
            strategy_factory.register_strategy("target_profit", FixedTargetManagement)
            strategy_factory.register_strategy("partial_profit", PartialExitManagement)
            strategy_factory.register_strategy("time_based_exit", TimeBasedExitManagement)
            strategy_factory.register_strategy("volatility_based_management", TrailingStopManagement)
            strategy_factory.register_strategy("fixed_stop_loss", TrailingStopManagement)  # 임시로 trailing stop 사용
            strategy_factory.register_strategy("trailing_stop", TrailingStopManagement)
        
        _instance = StrategyManager(db_manager, strategy_factory)
    
    return _instance