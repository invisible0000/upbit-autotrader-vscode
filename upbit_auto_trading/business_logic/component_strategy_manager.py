"""
컴포넌트 기반 전략 매니저
Component-based Strategy Manager

새로운 아토믹 컴포넌트 시스템을 위한 전략 관리자
"""

import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..component_models import ComponentStrategy, StrategyExecution, StrategyTemplate, ComponentConfiguration
from ..storage.database_manager import DatabaseManager
from ...component_system import (
    TRIGGER_CLASSES, CONFIG_CLASSES, ACTION_CLASSES,
    get_trigger_class, get_config_class, get_action_class,
    TRIGGER_METADATA, ACTION_METADATA
)

logger = logging.getLogger(__name__)

class ComponentStrategyManager:
    """컴포넌트 기반 전략 매니저"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        초기화
        
        Args:
            db_manager: 데이터베이스 매니저
        """
        self.db_manager = db_manager
        self.logger = logger
    
    def create_strategy(self, name: str, description: str = None, 
                       triggers: List[Dict] = None, conditions: List[Dict] = None,
                       actions: List[Dict] = None, tags: List[str] = None,
                       category: str = None, difficulty: str = 'beginner') -> str:
        """
        새로운 컴포넌트 전략 생성
        
        Args:
            name: 전략 이름
            description: 전략 설명
            triggers: 트리거 컴포넌트 목록
            conditions: 조건 컴포넌트 목록  
            actions: 액션 컴포넌트 목록
            tags: 태그 목록
            category: 카테고리
            difficulty: 난이도
            
        Returns:
            str: 생성된 전략 ID
        """
        try:
            strategy_id = str(uuid.uuid4())
            
            # 컴포넌트 검증
            self._validate_components(triggers or [], conditions or [], actions or [])
            
            strategy = ComponentStrategy(
                id=strategy_id,
                name=name,
                description=description,
                triggers=json.dumps(triggers or []),
                conditions=json.dumps(conditions or []),
                actions=json.dumps(actions or []),
                tags=json.dumps(tags or []),
                category=category,
                difficulty=difficulty
            )
            
            with self.db_manager.session_scope() as session:
                session.add(strategy)
                session.commit()
                
                # 컴포넌트 설정들도 저장
                self._save_component_configurations(session, strategy_id, 
                                                  triggers or [], conditions or [], actions or [])
                
                self.logger.info(f"✅ 컴포넌트 전략 생성 완료: {name} (ID: {strategy_id})")
                return strategy_id
                
        except Exception as e:
            self.logger.error(f"❌ 컴포넌트 전략 생성 실패: {e}")
            raise
    
    def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        전략 조회
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            Dict[str, Any]: 전략 정보
        """
        try:
            with self.db_manager.session_scope() as session:
                strategy = session.query(ComponentStrategy).filter_by(id=strategy_id).first()
                
                if not strategy:
                    return None
                
                return self._strategy_to_dict(strategy)
                
        except Exception as e:
            self.logger.error(f"❌ 전략 조회 실패: {e}")
            return None
    
    def list_strategies(self, category: str = None, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        전략 목록 조회
        
        Args:
            category: 카테고리 필터
            active_only: 활성화된 전략만 조회
            
        Returns:
            List[Dict[str, Any]]: 전략 목록
        """
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(ComponentStrategy)
                
                if category:
                    query = query.filter_by(category=category)
                
                if active_only:
                    query = query.filter_by(is_active=True)
                
                strategies = query.all()
                return [self._strategy_to_dict(s) for s in strategies]
                
        except Exception as e:
            self.logger.error(f"❌ 전략 목록 조회 실패: {e}")
            return []
    
    def update_strategy(self, strategy_id: str, **kwargs) -> bool:
        """
        전략 업데이트
        
        Args:
            strategy_id: 전략 ID
            **kwargs: 업데이트할 필드들
            
        Returns:
            bool: 성공 여부
        """
        try:
            with self.db_manager.session_scope() as session:
                strategy = session.query(ComponentStrategy).filter_by(id=strategy_id).first()
                
                if not strategy:
                    self.logger.warning(f"전략을 찾을 수 없습니다: {strategy_id}")
                    return False
                
                # 업데이트 가능한 필드들
                updatable_fields = [
                    'name', 'description', 'triggers', 'conditions', 'actions', 
                    'tags', 'category', 'difficulty', 'is_active'
                ]
                
                for field, value in kwargs.items():
                    if field in updatable_fields:
                        if field in ['triggers', 'conditions', 'actions', 'tags']:
                            setattr(strategy, field, json.dumps(value))
                        else:
                            setattr(strategy, field, value)
                
                strategy.updated_at = datetime.utcnow()
                session.commit()
                
                self.logger.info(f"✅ 전략 업데이트 완료: {strategy_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 전략 업데이트 실패: {e}")
            return False
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """
        전략 삭제
        
        Args:
            strategy_id: 전략 ID
            
        Returns:
            bool: 성공 여부
        """
        try:
            with self.db_manager.session_scope() as session:
                strategy = session.query(ComponentStrategy).filter_by(id=strategy_id).first()
                
                if not strategy:
                    self.logger.warning(f"전략을 찾을 수 없습니다: {strategy_id}")
                    return False
                
                # 관련 데이터들도 삭제
                session.query(ComponentConfiguration).filter_by(strategy_id=strategy_id).delete()
                session.query(StrategyExecution).filter_by(strategy_id=strategy_id).delete()
                
                session.delete(strategy)
                session.commit()
                
                self.logger.info(f"✅ 전략 삭제 완료: {strategy_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 전략 삭제 실패: {e}")
            return False
    
    def create_from_template(self, template_id: str, name: str, **overrides) -> str:
        """
        템플릿으로부터 전략 생성
        
        Args:
            template_id: 템플릿 ID
            name: 새 전략 이름
            **overrides: 덮어쓸 설정들
            
        Returns:
            str: 생성된 전략 ID
        """
        try:
            template = self.get_template(template_id)
            if not template:
                raise ValueError(f"템플릿을 찾을 수 없습니다: {template_id}")
            
            template_data = json.loads(template['template_data'])
            
            # 기본값에 overrides 적용
            strategy_config = {
                'name': name,
                'description': template.get('description', ''),
                'triggers': template_data.get('triggers', []),
                'conditions': template_data.get('conditions', []),
                'actions': template_data.get('actions', []),
                'category': template.get('category'),
                'difficulty': template.get('difficulty', 'beginner'),
                **overrides
            }
            
            strategy_id = self.create_strategy(**strategy_config)
            
            # 템플릿 사용 횟수 증가
            self._increment_template_usage(template_id)
            
            return strategy_id
            
        except Exception as e:
            self.logger.error(f"❌ 템플릿으로부터 전략 생성 실패: {e}")
            raise
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """템플릿 조회"""
        try:
            with self.db_manager.session_scope() as session:
                template = session.query(StrategyTemplate).filter_by(id=template_id).first()
                
                if not template:
                    return None
                
                return {
                    'id': template.id,
                    'name': template.name,
                    'description': template.description,
                    'template_data': template.template_data,
                    'category': template.category,
                    'difficulty': template.difficulty,
                    'tags': json.loads(template.tags) if template.tags else [],
                    'usage_count': template.usage_count,
                    'created_at': template.created_at.isoformat() if template.created_at else None
                }
                
        except Exception as e:
            self.logger.error(f"❌ 템플릿 조회 실패: {e}")
            return None
    
    def list_templates(self, category: str = None) -> List[Dict[str, Any]]:
        """템플릿 목록 조회"""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(StrategyTemplate)
                
                if category:
                    query = query.filter_by(category=category)
                
                templates = query.all()
                return [
                    {
                        'id': t.id,
                        'name': t.name,
                        'description': t.description,
                        'category': t.category,
                        'difficulty': t.difficulty,
                        'usage_count': t.usage_count
                    }
                    for t in templates
                ]
                
        except Exception as e:
            self.logger.error(f"❌ 템플릿 목록 조회 실패: {e}")
            return []
    
    def _validate_components(self, triggers: List[Dict], conditions: List[Dict], actions: List[Dict]):
        """컴포넌트 검증"""
        # 최소 하나의 트리거와 액션이 필요
        if not triggers:
            raise ValueError("최소 하나의 트리거가 필요합니다")
        
        if not actions:
            raise ValueError("최소 하나의 액션이 필요합니다")
        
        # 트리거 검증
        for trigger in triggers:
            trigger_type = trigger.get('type')
            if not trigger_type or trigger_type not in TRIGGER_CLASSES:
                raise ValueError(f"유효하지 않은 트리거 타입: {trigger_type}")
        
        # 액션 검증
        for action in actions:
            action_type = action.get('type')
            if not action_type or action_type not in ACTION_CLASSES:
                raise ValueError(f"유효하지 않은 액션 타입: {action_type}")
    
    def _save_component_configurations(self, session: Session, strategy_id: str,
                                     triggers: List[Dict], conditions: List[Dict], actions: List[Dict]):
        """컴포넌트 설정들 저장"""
        # 기존 설정들 삭제
        session.query(ComponentConfiguration).filter_by(strategy_id=strategy_id).delete()
        
        # 트리거 설정들 저장
        for i, trigger in enumerate(triggers):
            config = ComponentConfiguration(
                id=str(uuid.uuid4()),
                strategy_id=strategy_id,
                component_type='trigger',
                component_name=trigger['type'],
                configuration=json.dumps(trigger.get('config', {})),
                priority=i + 1
            )
            session.add(config)
        
        # 조건 설정들 저장
        for i, condition in enumerate(conditions):
            config = ComponentConfiguration(
                id=str(uuid.uuid4()),
                strategy_id=strategy_id,
                component_type='condition',
                component_name=condition['type'],
                configuration=json.dumps(condition.get('config', {})),
                priority=i + 1
            )
            session.add(config)
        
        # 액션 설정들 저장
        for i, action in enumerate(actions):
            config = ComponentConfiguration(
                id=str(uuid.uuid4()),
                strategy_id=strategy_id,
                component_type='action',
                component_name=action['type'],
                configuration=json.dumps(action.get('config', {})),
                priority=i + 1
            )
            session.add(config)
    
    def _strategy_to_dict(self, strategy: ComponentStrategy) -> Dict[str, Any]:
        """전략 객체를 딕셔너리로 변환"""
        return {
            'id': strategy.id,
            'name': strategy.name,
            'description': strategy.description,
            'triggers': json.loads(strategy.triggers) if strategy.triggers else [],
            'conditions': json.loads(strategy.conditions) if strategy.conditions else [],
            'actions': json.loads(strategy.actions) if strategy.actions else [],
            'tags': json.loads(strategy.tags) if strategy.tags else [],
            'category': strategy.category,
            'difficulty': strategy.difficulty,
            'is_active': strategy.is_active,
            'is_template': strategy.is_template,
            'performance_metrics': json.loads(strategy.performance_metrics) if strategy.performance_metrics else {},
            'created_at': strategy.created_at.isoformat() if strategy.created_at else None,
            'updated_at': strategy.updated_at.isoformat() if strategy.updated_at else None
        }
    
    def _increment_template_usage(self, template_id: str):
        """템플릿 사용 횟수 증가"""
        try:
            with self.db_manager.session_scope() as session:
                template = session.query(StrategyTemplate).filter_by(id=template_id).first()
                if template:
                    template.usage_count += 1
                    session.commit()
        except Exception as e:
            self.logger.warning(f"템플릿 사용 횟수 업데이트 실패: {e}")

# 전역 인스턴스 (싱글톤 패턴)
_component_strategy_manager = None

def get_component_strategy_manager(db_manager: DatabaseManager = None) -> ComponentStrategyManager:
    """컴포넌트 전략 매니저 인스턴스 반환"""
    global _component_strategy_manager
    
    if _component_strategy_manager is None:
        if db_manager is None:
            from ..storage.database_manager import get_database_manager
            db_manager = get_database_manager()
        _component_strategy_manager = ComponentStrategyManager(db_manager)
    
    return _component_strategy_manager
