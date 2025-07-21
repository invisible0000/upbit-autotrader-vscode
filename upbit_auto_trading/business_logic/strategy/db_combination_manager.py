#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DB 기반 전략 조합 관리자

전략 조합을 데이터베이스에서 관리하는 클래스입니다.
"""

import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from upbit_auto_trading.data_layer.storage.database_manager import DatabaseManager
from upbit_auto_trading.data_layer.models import StrategyCombination, CombinationManagementStrategy, Strategy
from .strategy_combination import StrategyCombination as StrategyCombinationData, StrategyConfig


class DBCombinationManager:
    """DB 기반 전략 조합 관리자"""
    
    def __init__(self, db_manager: DatabaseManager):
        """초기화
        
        Args:
            db_manager: 데이터베이스 매니저
        """
        self.db_manager = db_manager
    
    def create_combination(self, name: str, description: str,
                          entry_strategy_id: str,
                          management_strategy_configs: Optional[List[Dict[str, Any]]] = None) -> bool:
        """새 전략 조합 생성
        
        Args:
            name: 조합 이름
            description: 조합 설명
            entry_strategy_id: 진입 전략 ID
            management_strategy_configs: 관리 전략 설정 리스트
                [{"strategy_id": str, "priority": int, "weight": float}, ...]
                
        Returns:
            성공 여부
        """
        try:
            session = self.db_manager.get_session()
            
            try:
                # 중복 이름 체크
                existing = session.query(StrategyCombination).filter_by(name=name).first()
                if existing:
                    print(f"❌ 조합 이름 중복: {name}")
                    return False
                
                # 진입 전략 존재 확인
                entry_strategy = session.query(Strategy).filter_by(id=entry_strategy_id).first()
                if not entry_strategy:
                    print(f"❌ 진입 전략을 찾을 수 없음: {entry_strategy_id}")
                    return False
                
                # 새 조합 생성
                combination_id = str(uuid.uuid4())
                new_combination = StrategyCombination(
                    id=combination_id,
                    name=name,
                    description=description,
                    entry_strategy_id=entry_strategy_id,
                    execution_order='parallel',
                    conflict_resolution='conservative',
                    is_active=True
                )
                
                session.add(new_combination)
                session.flush()  # ID 생성을 위해 flush
                
                # 관리 전략들 추가
                if management_strategy_configs:
                    for config in management_strategy_configs:
                        strategy_id = config["strategy_id"]
                        priority = config.get("priority", 1)
                        weight = config.get("weight", 1.0)
                        
                        # 관리 전략 존재 확인
                        mgmt_strategy = session.query(Strategy).filter_by(id=strategy_id).first()
                        if not mgmt_strategy:
                            print(f"⚠️ 관리 전략을 찾을 수 없음: {strategy_id}")
                            continue
                        
                        combination_mgmt = CombinationManagementStrategy(
                            combination_id=combination_id,
                            strategy_id=strategy_id,
                            priority=priority,
                            weight=weight,
                            is_active=True
                        )
                        session.add(combination_mgmt)
                
                session.commit()
                print(f"✅ 전략 조합 생성 완료: {name} (ID: {combination_id})")
                return True
                
            except Exception as e:
                session.rollback()
                print(f"❌ 전략 조합 생성 실패: {e}")
                return False
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ DB 연결 실패: {e}")
            return False
    
    def get_all_combinations(self) -> List[Dict[str, Any]]:
        """모든 전략 조합 조회
        
        Returns:
            조합 정보 리스트
        """
        try:
            session = self.db_manager.get_session()
            
            try:
                combinations = session.query(StrategyCombination).all()
                result = []
                
                for combo in combinations:
                    # 진입 전략 정보
                    entry_strategy_info = {
                        "id": combo.entry_strategy.id,
                        "name": combo.entry_strategy.name,
                        "description": combo.entry_strategy.description
                    }
                    
                    # 관리 전략들 정보
                    mgmt_strategies_info = []
                    for mgmt in combo.management_strategies:
                        if mgmt.is_active:
                            mgmt_strategies_info.append({
                                "id": mgmt.strategy.id,
                                "name": mgmt.strategy.name,
                                "description": mgmt.strategy.description,
                                "priority": mgmt.priority,
                                "weight": mgmt.weight
                            })
                    
                    # 조합 구성 요약 생성
                    mgmt_count = len(mgmt_strategies_info)
                    summary = f"진입: {entry_strategy_info['name']}, 관리: {mgmt_count}개"
                    
                    result.append({
                        "id": combo.id,
                        "name": combo.name,
                        "description": combo.description,
                        "summary": summary,
                        "entry_strategy": entry_strategy_info,
                        "management_strategies": mgmt_strategies_info,
                        "execution_order": combo.execution_order,
                        "conflict_resolution": combo.conflict_resolution,
                        "is_active": combo.is_active,
                        "created_at": combo.created_at,
                        "updated_at": combo.updated_at
                    })
                
                print(f"✅ 전략 조합 {len(result)}개 조회 완료")
                return result
                
            except Exception as e:
                print(f"❌ 전략 조합 조회 실패: {e}")
                return []
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ DB 연결 실패: {e}")
            return []
    
    def get_combination_by_id(self, combination_id: str) -> Optional[Dict[str, Any]]:
        """ID로 전략 조합 조회
        
        Args:
            combination_id: 조합 ID
            
        Returns:
            조합 정보 또는 None
        """
        try:
            session = self.db_manager.get_session()
            
            try:
                combo = session.query(StrategyCombination).filter_by(id=combination_id).first()
                if not combo:
                    return None
                
                # 진입 전략 정보
                entry_strategy_info = {
                    "id": combo.entry_strategy.id,
                    "name": combo.entry_strategy.name,
                    "description": combo.entry_strategy.description
                }
                
                # 관리 전략들 정보
                mgmt_strategies_info = []
                for mgmt in combo.management_strategies:
                    if mgmt.is_active:
                        mgmt_strategies_info.append({
                            "id": mgmt.strategy.id,
                            "name": mgmt.strategy.name,
                            "description": mgmt.strategy.description,
                            "priority": mgmt.priority,
                            "weight": mgmt.weight
                        })
                
                return {
                    "id": combo.id,
                    "name": combo.name,
                    "description": combo.description,
                    "entry_strategy": entry_strategy_info,
                    "management_strategies": mgmt_strategies_info,
                    "execution_order": combo.execution_order,
                    "conflict_resolution": combo.conflict_resolution,
                    "is_active": combo.is_active,
                    "created_at": combo.created_at,
                    "updated_at": combo.updated_at
                }
                
            except Exception as e:
                print(f"❌ 전략 조합 조회 실패: {e}")
                return None
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ DB 연결 실패: {e}")
            return None
    
    def update_combination(self, combination_id: str, updates: Dict[str, Any]) -> bool:
        """전략 조합 업데이트
        
        Args:
            combination_id: 조합 ID
            updates: 업데이트할 필드들
            
        Returns:
            성공 여부
        """
        try:
            session = self.db_manager.get_session()
            
            try:
                combo = session.query(StrategyCombination).filter_by(id=combination_id).first()
                if not combo:
                    print(f"❌ 조합을 찾을 수 없음: {combination_id}")
                    return False
                
                # 업데이트 가능한 필드들
                updateable_fields = ['name', 'description', 'execution_order', 'conflict_resolution', 'is_active']
                
                for field, value in updates.items():
                    if field in updateable_fields:
                        setattr(combo, field, value)
                
                combo.updated_at = datetime.utcnow()
                session.commit()
                
                print(f"✅ 전략 조합 업데이트 완료: {combination_id}")
                return True
                
            except Exception as e:
                session.rollback()
                print(f"❌ 전략 조합 업데이트 실패: {e}")
                return False
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ DB 연결 실패: {e}")
            return False
    
    def delete_combination(self, combination_id: str) -> bool:
        """전략 조합 삭제
        
        Args:
            combination_id: 조합 ID
            
        Returns:
            성공 여부
        """
        try:
            session = self.db_manager.get_session()
            
            try:
                # 관련된 관리 전략들 먼저 삭제
                session.query(CombinationManagementStrategy).filter_by(
                    combination_id=combination_id
                ).delete()
                
                # 조합 삭제
                combo = session.query(StrategyCombination).filter_by(id=combination_id).first()
                if combo:
                    session.delete(combo)
                    session.commit()
                    print(f"✅ 전략 조합 삭제 완료: {combination_id}")
                    return True
                else:
                    print(f"⚠️ 조합을 찾을 수 없음: {combination_id}")
                    return False
                
            except Exception as e:
                session.rollback()
                print(f"❌ 전략 조합 삭제 실패: {e}")
                return False
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ DB 연결 실패: {e}")
            return False
    
    def get_sample_combinations(self) -> List[Dict[str, Any]]:
        """샘플 조합 생성 (테스트/데모용)
        
        Returns:
            샘플 조합 리스트
        """
        return [
            {
                "id": "sample_combo_1",
                "name": "RSI + 물타기 조합",
                "description": "RSI 과매수/과매도 진입 + 물타기 관리",
                "summary": "진입: RSI 과매수/과매도, 관리: 1개",
                "entry_strategy": {
                    "id": "rsi_entry",
                    "name": "RSI 과매수/과매도",
                    "description": "RSI 30/70 돌파 신호"
                },
                "management_strategies": [{
                    "id": "averaging_down",
                    "name": "물타기",
                    "description": "하락 시 추가 매수",
                    "priority": 1,
                    "weight": 1.0
                }],
                "execution_order": "parallel",
                "conflict_resolution": "conservative",
                "is_active": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "id": "sample_combo_2", 
                "name": "이동평균 + 멀티 관리",
                "description": "이동평균 교차 진입 + 복합 관리 전략",
                "summary": "진입: 이동평균 교차, 관리: 2개",
                "entry_strategy": {
                    "id": "ma_cross_entry",
                    "name": "이동평균 교차",
                    "description": "골든크로스/데드크로스 신호"
                },
                "management_strategies": [
                    {
                        "id": "trailing_stop",
                        "name": "트레일링 스탑",
                        "description": "동적 손절가 조정",
                        "priority": 1,
                        "weight": 1.0
                    },
                    {
                        "id": "fixed_target",
                        "name": "고정 익절/손절",
                        "description": "고정 % 도달 시 청산",
                        "priority": 2,
                        "weight": 0.8
                    }
                ],
                "execution_order": "parallel",
                "conflict_resolution": "conservative",
                "is_active": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]


def get_db_combination_manager(db_manager: DatabaseManager = None) -> DBCombinationManager:
    """DB 조합 매니저 팩토리 함수
    
    Args:
        db_manager: 데이터베이스 매니저 (None이면 기본 매니저 사용)
        
    Returns:
        DB 조합 매니저 인스턴스
    """
    if db_manager is None:
        from upbit_auto_trading.data_layer.storage.database_manager import get_database_manager
        db_manager = get_database_manager()
    
    return DBCombinationManager(db_manager)
