#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
전략 조합 관리자

전략 조합의 생성, 검증, 실행을 담당하는 핵심 클래스입니다.
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import uuid
import logging
from enum import Enum

from upbit_auto_trading.data_layer.models import Base
from upbit_auto_trading.data_layer.strategy_models import (
    StrategyDefinition, StrategyCombination, StrategyConfig, 
    CombinationManagementStrategy, ConflictResolutionTypeEnum
)
from upbit_auto_trading.data_layer.storage.database_manager import get_database_manager

logger = logging.getLogger(__name__)


class ValidationStatus(str, Enum):
    """전략 조합 검증 상태"""
    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"


class StrategyRole(str, Enum):
    """전략 역할"""
    ENTRY = "entry"
    EXIT = "exit"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"
    MANAGEMENT = "management"
    RISK_FILTER = "risk_filter"


class CombinationManager:
    """전략 조합 관리자 클래스"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
        
    def create_combination(
        self, 
        name: str,
        entry_strategy_config_id: str,
        management_strategy_configs: List[Dict[str, Any]],
        description: str = None,
        conflict_resolution: str = "conservative"
    ) -> StrategyCombination:
        """
        새로운 전략 조합을 생성합니다.
        
        Args:
            name: 조합 이름
            entry_strategy_config_id: 진입 전략 설정 ID
            management_strategy_configs: 관리 전략 설정 목록 [{"config_id": str, "priority": int}]
            description: 설명
            conflict_resolution: 충돌 해결 방식
            
        Returns:
            생성된 StrategyCombination 객체
        """
        logger.info(f"🎯 새로운 전략 조합 생성: {name}")
        
        try:
            with self.db_manager.get_session() as session:
                # 1. 진입 전략 검증
                entry_config = session.query(StrategyConfig).filter(
                    StrategyConfig.config_id == entry_strategy_config_id
                ).first()
                
                if not entry_config:
                    raise ValueError(f"진입 전략 설정을 찾을 수 없습니다: {entry_strategy_config_id}")
                
                # 2. 관리 전략들 검증
                management_configs = []
                for mgmt_config in management_strategy_configs:
                    config = session.query(StrategyConfig).filter(
                        StrategyConfig.config_id == mgmt_config["config_id"]
                    ).first()
                    
                    if not config:
                        raise ValueError(f"관리 전략 설정을 찾을 수 없습니다: {mgmt_config['config_id']}")
                    
                    management_configs.append({
                        "config": config,
                        "priority": mgmt_config.get("priority", 1)
                    })
                
                # 3. 조합 생성
                combination_id = str(uuid.uuid4())
                combination = StrategyCombination(
                    combination_id=combination_id,
                    name=name,
                    description=description,
                    entry_strategy_id=entry_strategy_config_id,
                    conflict_resolution=conflict_resolution
                )
                
                session.add(combination)
                session.flush()  # ID 생성을 위해
                
                # 4. 관리 전략 연결
                for mgmt_config in management_configs:
                    combo_mgmt = CombinationManagementStrategy(
                        combination_id=combination_id,
                        strategy_config_id=mgmt_config["config"].config_id,
                        priority=mgmt_config["priority"]
                    )
                    session.add(combo_mgmt)
                
                session.commit()
                
                # 생성된 조합 정보 반환을 위해 다시 조회
                created_combination = session.query(StrategyCombination).filter(
                    StrategyCombination.combination_id == combination_id
                ).first()
                
                logger.info(f"✅ 전략 조합 생성 완료: {combination_id}")
                return created_combination
                
        except Exception as e:
            logger.error(f"❌ 전략 조합 생성 실패: {e}")
            raise
    
    def validate_combination(self, combination_id: str) -> Dict[str, Any]:
        """
        전략 조합의 유효성을 검증합니다.
        
        Args:
            combination_id: 조합 ID
            
        Returns:
            검증 결과 딕셔너리
        """
        logger.info(f"🔍 전략 조합 검증: {combination_id}")
        
        validation_result = {
            "combination_id": combination_id,
            "status": ValidationStatus.VALID,
            "warnings": [],
            "errors": [],
            "details": {}
        }
        
        try:
            with self.db_manager.get_session() as session:
                # 1. 조합 존재 여부 확인
                combination = session.query(StrategyCombination).filter(
                    StrategyCombination.combination_id == combination_id
                ).first()
                
                if not combination:
                    validation_result["status"] = ValidationStatus.INVALID
                    validation_result["errors"].append("조합을 찾을 수 없습니다")
                    return validation_result
                
                # 2. 진입 전략 검증
                entry_strategy = session.query(StrategyConfig).filter(
                    StrategyConfig.config_id == combination.entry_strategy_id
                ).first()
                
                if not entry_strategy:
                    validation_result["status"] = ValidationStatus.INVALID
                    validation_result["errors"].append("진입 전략이 유효하지 않습니다")
                
                # 3. 관리 전략들 검증
                management_strategies = session.query(CombinationManagementStrategy).filter(
                    CombinationManagementStrategy.combination_id == combination_id
                ).order_by(CombinationManagementStrategy.priority).all()
                
                if not management_strategies:
                    validation_result["status"] = ValidationStatus.WARNING
                    validation_result["warnings"].append("관리 전략이 없습니다")
                
                # 4. 우선순위 중복 확인
                priorities = [ms.priority for ms in management_strategies]
                if len(priorities) != len(set(priorities)):
                    validation_result["status"] = ValidationStatus.WARNING
                    validation_result["warnings"].append("우선순위 중복이 있습니다")
                
                # 5. 전략 타입 검증
                entry_def = session.query(StrategyDefinition).filter(
                    StrategyDefinition.id == entry_strategy.strategy_definition_id
                ).first()
                
                if entry_def and entry_def.strategy_type != "entry":
                    validation_result["status"] = ValidationStatus.INVALID
                    validation_result["errors"].append("진입 전략의 타입이 올바르지 않습니다")
                
                # 6. 세부 정보 수집
                validation_result["details"] = {
                    "combination_name": combination.name,
                    "entry_strategy_name": entry_strategy.strategy_name if entry_strategy else None,
                    "management_strategy_count": len(management_strategies),
                    "conflict_resolution": combination.conflict_resolution,
                    "created_at": combination.created_at.isoformat()
                }
                
                logger.info(f"✅ 검증 완료: {validation_result['status']}")
                return validation_result
                
        except Exception as e:
            logger.error(f"❌ 검증 실패: {e}")
            validation_result["status"] = ValidationStatus.INVALID
            validation_result["errors"].append(f"검증 중 오류 발생: {str(e)}")
            return validation_result
    
    def get_combination_details(self, combination_id: str) -> Optional[Dict[str, Any]]:
        """
        전략 조합의 상세 정보를 조회합니다.
        
        Args:
            combination_id: 조합 ID
            
        Returns:
            조합 상세 정보 딕셔너리
        """
        try:
            with self.db_manager.get_session() as session:
                combination = session.query(StrategyCombination).filter(
                    StrategyCombination.combination_id == combination_id
                ).first()
                
                if not combination:
                    return None
                
                # 진입 전략 정보
                entry_strategy = session.query(StrategyConfig).filter(
                    StrategyConfig.config_id == combination.entry_strategy_id
                ).first()
                
                # 관리 전략들 정보
                management_strategies = session.query(CombinationManagementStrategy).filter(
                    CombinationManagementStrategy.combination_id == combination_id
                ).order_by(CombinationManagementStrategy.priority).all()
                
                mgmt_details = []
                for mgmt in management_strategies:
                    config = session.query(StrategyConfig).filter(
                        StrategyConfig.config_id == mgmt.strategy_config_id
                    ).first()
                    
                    if config:
                        mgmt_details.append({
                            "config_id": config.config_id,
                            "name": config.strategy_name,
                            "priority": mgmt.priority,
                            "parameters": config.parameters
                        })
                
                return {
                    "combination_id": combination.combination_id,
                    "name": combination.name,
                    "description": combination.description,
                    "conflict_resolution": combination.conflict_resolution,
                    "created_at": combination.created_at.isoformat(),
                    "updated_at": combination.updated_at.isoformat(),
                    "entry_strategy": {
                        "config_id": entry_strategy.config_id if entry_strategy else None,
                        "name": entry_strategy.strategy_name if entry_strategy else None,
                        "parameters": entry_strategy.parameters if entry_strategy else None
                    },
                    "management_strategies": mgmt_details
                }
                
        except Exception as e:
            logger.error(f"❌ 조합 상세 정보 조회 실패: {e}")
            return None
    
    def list_combinations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        전략 조합 목록을 조회합니다.
        
        Args:
            limit: 조회할 최대 개수
            
        Returns:
            조합 목록
        """
        try:
            with self.db_manager.get_session() as session:
                combinations = session.query(StrategyCombination).order_by(
                    StrategyCombination.created_at.desc()
                ).limit(limit).all()
                
                result = []
                for combo in combinations:
                    # 진입 전략 이름 조회
                    entry_strategy = session.query(StrategyConfig).filter(
                        StrategyConfig.config_id == combo.entry_strategy_id
                    ).first()
                    
                    # 관리 전략 개수 조회
                    mgmt_count = session.query(CombinationManagementStrategy).filter(
                        CombinationManagementStrategy.combination_id == combo.combination_id
                    ).count()
                    
                    result.append({
                        "combination_id": combo.combination_id,
                        "name": combo.name,
                        "description": combo.description,
                        "entry_strategy_name": entry_strategy.strategy_name if entry_strategy else "Unknown",
                        "management_strategy_count": mgmt_count,
                        "conflict_resolution": combo.conflict_resolution,
                        "created_at": combo.created_at.isoformat()
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"❌ 조합 목록 조회 실패: {e}")
            return []
    
    def delete_combination(self, combination_id: str) -> bool:
        """
        전략 조합을 삭제합니다.
        
        Args:
            combination_id: 조합 ID
            
        Returns:
            삭제 성공 여부
        """
        logger.info(f"🗑️ 전략 조합 삭제: {combination_id}")
        
        try:
            with self.db_manager.get_session() as session:
                # 1. 관리 전략 연결 삭제
                session.query(CombinationManagementStrategy).filter(
                    CombinationManagementStrategy.combination_id == combination_id
                ).delete()
                
                # 2. 조합 삭제
                deleted_count = session.query(StrategyCombination).filter(
                    StrategyCombination.combination_id == combination_id
                ).delete()
                
                session.commit()
                
                if deleted_count > 0:
                    logger.info(f"✅ 조합 삭제 완료: {combination_id}")
                    return True
                else:
                    logger.warning(f"⚠️ 삭제할 조합을 찾을 수 없음: {combination_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 조합 삭제 실패: {e}")
            return False


# 편의 함수들
def create_sample_strategy_definitions():
    """샘플 전략 정의들을 생성합니다."""
    sample_definitions = [
        {
            "id": "rsi_entry",
            "name": "RSI 과매수/과매도",
            "description": "RSI 30/70 기준 진입 전략",
            "strategy_type": "entry",
            "class_name": "RSIEntryStrategy",
            "default_parameters": {
                "rsi_period": 14,
                "oversold_threshold": 30,
                "overbought_threshold": 70
            },
            "parameter_schema": {
                "rsi_period": {"type": "integer", "min": 5, "max": 50},
                "oversold_threshold": {"type": "float", "min": 10, "max": 40},
                "overbought_threshold": {"type": "float", "min": 60, "max": 90}
            }
        },
        {
            "id": "fixed_stop_loss",
            "name": "고정 손절",
            "description": "고정 손절률 적용",
            "strategy_type": "management",
            "class_name": "FixedStopLossStrategy",
            "default_parameters": {
                "stop_loss_percent": 5.0
            },
            "parameter_schema": {
                "stop_loss_percent": {"type": "float", "min": 1.0, "max": 20.0}
            }
        },
        {
            "id": "trailing_stop",
            "name": "트레일링 스탑",
            "description": "수익 추적 손절",
            "strategy_type": "management", 
            "class_name": "TrailingStopStrategy",
            "default_parameters": {
                "trail_percent": 3.0,
                "activation_percent": 5.0
            },
            "parameter_schema": {
                "trail_percent": {"type": "float", "min": 1.0, "max": 10.0},
                "activation_percent": {"type": "float", "min": 2.0, "max": 15.0}
            }
        }
    ]
    
    db_manager = get_database_manager()
    
    try:
        with db_manager.get_session() as session:
            for def_data in sample_definitions:
                # 이미 존재하는지 확인
                existing = session.query(StrategyDefinition).filter(
                    StrategyDefinition.id == def_data["id"]
                ).first()
                
                if not existing:
                    strategy_def = StrategyDefinition(**def_data)
                    session.add(strategy_def)
                    logger.info(f"✅ 샘플 전략 정의 생성: {def_data['name']}")
            
            session.commit()
            logger.info("🎯 샘플 전략 정의 생성 완료")
            
    except Exception as e:
        logger.error(f"❌ 샘플 전략 정의 생성 실패: {e}")


def create_sample_strategy_configs():
    """샘플 전략 설정들을 생성합니다."""
    sample_configs = [
        {
            "config_id": "rsi_entry_config_001",
            "strategy_definition_id": "rsi_entry",
            "strategy_name": "RSI 진입 (기본)",
            "parameters": {
                "rsi_period": 14,
                "oversold_threshold": 30,
                "overbought_threshold": 70
            }
        },
        {
            "config_id": "fixed_stop_config_001", 
            "strategy_definition_id": "fixed_stop_loss",
            "strategy_name": "5% 고정 손절",
            "parameters": {
                "stop_loss_percent": 5.0
            }
        },
        {
            "config_id": "trailing_stop_config_001",
            "strategy_definition_id": "trailing_stop", 
            "strategy_name": "3% 트레일링 스탑",
            "parameters": {
                "trail_percent": 3.0,
                "activation_percent": 5.0
            }
        }
    ]
    
    db_manager = get_database_manager()
    
    try:
        with db_manager.get_session() as session:
            for config_data in sample_configs:
                # 이미 존재하는지 확인
                existing = session.query(StrategyConfig).filter(
                    StrategyConfig.config_id == config_data["config_id"]
                ).first()
                
                if not existing:
                    strategy_config = StrategyConfig(**config_data)
                    session.add(strategy_config)
                    logger.info(f"✅ 샘플 전략 설정 생성: {config_data['strategy_name']}")
            
            session.commit()
            logger.info("🎯 샘플 전략 설정 생성 완료")
            
    except Exception as e:
        logger.error(f"❌ 샘플 전략 설정 생성 실패: {e}")
