"""
Strategy 및 Trigger 엔티티 매핑

Domain Layer의 Strategy와 Trigger 엔티티를 데이터베이스 레코드로 변환하고,
데이터베이스 레코드를 다시 엔티티로 변환하는 매퍼 클래스들입니다.

주요 기능:
- 타입 안전한 변환
- JSON 데이터 직렬화/역직렬화
- 파라미터 튜플 생성 (SQL 쿼리용)
- 엔티티 재구성 (연관된 트리거들과 함께)

Note: Mock 구현으로 Domain Entity 클래스들이 구현된 후 실제 import로 교체 예정
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import logging


# Mock 클래스들 - Domain Layer 구현 완료 후 실제 클래스로 교체
class MockStrategyId:
    def __init__(self, value: Union[str, int]):
        self.value = str(value)


class MockTriggerId:
    def __init__(self, value: Union[str, int]):
        self.value = str(value)


class MockStrategy:
    """Mock Strategy Entity - Domain Layer 완성 후 실제 Strategy로 교체"""
    
    def __init__(self, strategy_id, name, description=None, status='ACTIVE',
                 entry_triggers=None, exit_triggers=None, management_triggers=None,
                 tags=None, created_at=None, updated_at=None, created_by='system',
                 version=1):
        self.strategy_id = strategy_id
        self.name = name
        self.description = description
        self.status = status
        self.entry_triggers = entry_triggers or []
        self.exit_triggers = exit_triggers or []
        self.management_triggers = management_triggers or []
        self.tags = tags or []
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.created_by = created_by
        self.version = version
    
    def get_all_triggers(self):
        """모든 트리거 반환"""
        return (self.entry_triggers + self.exit_triggers + 
                self.management_triggers)


class MockTrigger:
    """Mock Trigger Entity - Domain Layer 완성 후 실제 Trigger로 교체"""
    
    def __init__(self, trigger_id, trigger_name, strategy_id, variable,
                 operator, target_value, trigger_type='ENTRY', is_active=True,
                 weight=1.0, description=None, created_at=None):
        self.trigger_id = trigger_id
        self.trigger_name = trigger_name
        self.strategy_id = strategy_id
        self.variable = variable
        self.operator = operator
        self.target_value = target_value
        self.trigger_type = trigger_type
        self.is_active = is_active
        self.weight = weight
        self.description = description
        self.created_at = created_at or datetime.now()


class MockTradingVariable:
    """Mock TradingVariable Value Object"""
    
    def __init__(self, variable_id: str, parameters: Dict = None):
        self.variable_id = variable_id
        self.parameters = parameters or {}


class StrategyMapper:
    """Strategy 엔티티와 데이터베이스 레코드 간 매핑"""

    @staticmethod
    def to_entity(strategy_row: Dict[str, Any], 
                  triggers: Optional[List[Any]] = None) -> MockStrategy:
        """데이터베이스 레코드를 Strategy 엔티티로 변환"""
        if triggers is None:
            triggers = []

        # 트리거를 타입별로 분류
        entry_triggers = [t for t in triggers if 
                         getattr(t, 'trigger_type', 'ENTRY') == 'ENTRY']
        exit_triggers = [t for t in triggers if 
                        getattr(t, 'trigger_type', 'ENTRY') == 'EXIT']
        management_triggers = [t for t in triggers if 
                              getattr(t, 'trigger_type', 'ENTRY') == 'MANAGEMENT']

        return MockStrategy(
            strategy_id=MockStrategyId(strategy_row['id']),
            name=strategy_row['name'],
            description=strategy_row.get('description'),
            status=strategy_row.get('status', 'ACTIVE'),
            entry_triggers=entry_triggers,
            exit_triggers=exit_triggers,
            management_triggers=management_triggers,
            tags=(strategy_row.get('tags', '').split(',') 
                 if strategy_row.get('tags') else []),
            created_at=(datetime.fromisoformat(strategy_row['created_at']) 
                       if strategy_row.get('created_at') else datetime.now()),
            updated_at=(datetime.fromisoformat(strategy_row['updated_at']) 
                       if strategy_row.get('updated_at') else datetime.now()),
            created_by=strategy_row.get('created_by', 'system'),
            version=strategy_row.get('version', 1)
        )

    @staticmethod
    def to_database_record(strategy: MockStrategy) -> Dict[str, Any]:
        """Strategy 엔티티를 데이터베이스 레코드로 변환"""
        return {
            'id': strategy.strategy_id.value,
            'name': strategy.name,
            'description': strategy.description,
            'status': strategy.status,
            'tags': ','.join(strategy.tags) if strategy.tags else '',
            'created_at': strategy.created_at.isoformat(),
            'updated_at': strategy.updated_at.isoformat(),
            'created_by': strategy.created_by,
            'version': strategy.version
        }

    @staticmethod
    def to_insert_params(strategy: MockStrategy) -> tuple:
        """INSERT 쿼리용 파라미터 튜플로 변환"""
        record = StrategyMapper.to_database_record(strategy)
        return (
            record['id'],
            record['name'],
            record['description'],
            record['status'],
            record['tags'],
            record['created_at'],
            record['updated_at'],
            record['created_by'],
            record['version']
        )

    @staticmethod
    def to_update_params(strategy: MockStrategy) -> tuple:
        """UPDATE 쿼리용 파라미터 튜플로 변환"""
        record = StrategyMapper.to_database_record(strategy)
        return (
            record['name'],
            record['description'],
            record['status'],
            record['tags'],
            record['updated_at'],
            record['version'],
            record['id']  # WHERE 조건용
        )


class TriggerMapper:
    """Trigger 엔티티와 데이터베이스 레코드 간 매핑"""

    @staticmethod
    def to_entity(trigger_row: Dict[str, Any]) -> MockTrigger:
        """데이터베이스 레코드를 Trigger 엔티티로 변환"""
        
        # 변수 정보 파싱 (JSON 또는 별도 테이블에서 로드)
        variable_params = {}
        if trigger_row.get('variable_params'):
            try:
                variable_params = json.loads(trigger_row['variable_params'])
            except (json.JSONDecodeError, TypeError):
                variable_params = {}

        trading_variable = MockTradingVariable(
            variable_id=trigger_row['variable_id'],
            parameters=variable_params
        )

        return MockTrigger(
            trigger_id=MockTriggerId(trigger_row['id']),
            trigger_name=trigger_row['trigger_name'],
            strategy_id=MockStrategyId(trigger_row['strategy_id']),
            variable=trading_variable,
            operator=trigger_row['operator'],
            target_value=trigger_row['target_value'],
            trigger_type=trigger_row.get('trigger_type', 'ENTRY'),
            is_active=bool(trigger_row.get('is_active', True)),
            weight=float(trigger_row.get('weight', 1.0)),
            description=trigger_row.get('description'),
            created_at=(datetime.fromisoformat(trigger_row['created_at']) 
                       if trigger_row.get('created_at') else datetime.now())
        )

    @staticmethod
    def to_database_record(trigger: MockTrigger) -> Dict[str, Any]:
        """Trigger 엔티티를 데이터베이스 레코드로 변환"""
        
        return {
            'id': trigger.trigger_id.value,
            'trigger_name': trigger.trigger_name,
            'strategy_id': trigger.strategy_id.value,
            'variable_id': trigger.variable.variable_id,
            'variable_params': (json.dumps(trigger.variable.parameters) 
                              if trigger.variable.parameters else '{}'),
            'operator': trigger.operator,
            'target_value': trigger.target_value,
            'trigger_type': trigger.trigger_type,
            'is_active': trigger.is_active,
            'weight': trigger.weight,
            'description': trigger.description,
            'created_at': trigger.created_at.isoformat()
        }

    @staticmethod
    def to_insert_params(trigger: MockTrigger) -> tuple:
        """INSERT 쿼리용 파라미터 튜플로 변환"""
        record = TriggerMapper.to_database_record(trigger)
        return (
            record['id'],
            record['trigger_name'],
            record['strategy_id'],
            record['variable_id'],
            record['variable_params'],
            record['operator'],
            record['target_value'],
            record['trigger_type'],
            record['is_active'],
            record['weight'],
            record['description'],
            record['created_at']
        )

    @staticmethod
    def to_update_params(trigger: MockTrigger) -> tuple:
        """UPDATE 쿼리용 파라미터 튜플로 변환"""
        record = TriggerMapper.to_database_record(trigger)
        return (
            record['trigger_name'],
            record['variable_id'],
            record['variable_params'],
            record['operator'],
            record['target_value'],
            record['trigger_type'],
            record['is_active'],
            record['weight'],
            record['description'],
            record['id']  # WHERE 조건용
        )


class TradingVariableMapper:
    """TradingVariable Value Object 매핑 (Settings DB용)"""

    @staticmethod
    def to_entity(variable_row: Dict[str, Any]) -> MockTradingVariable:
        """데이터베이스 레코드를 TradingVariable로 변환"""
        return MockTradingVariable(
            variable_id=variable_row['variable_id'],
            parameters={}  # 파라미터는 별도 테이블에서 로드
        )

    @staticmethod
    def to_database_record(variable: MockTradingVariable) -> Dict[str, Any]:
        """TradingVariable을 데이터베이스 레코드로 변환"""
        return {
            'variable_id': variable.variable_id,
            'parameters': json.dumps(variable.parameters)
        }

    @staticmethod
    def load_parameters_for_variable(
        variable_id: str, 
        parameter_rows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """변수의 파라미터들을 딕셔너리로 변환"""
        parameters = {}
        for param_row in parameter_rows:
            param_name = param_row['parameter_name']
            param_value = param_row.get('value', param_row.get('default_value'))
            
            # 타입에 따른 값 변환
            param_type = param_row.get('parameter_type', 'string')
            if param_type == 'integer':
                try:
                    param_value = int(param_value) if param_value else 0
                except (ValueError, TypeError):
                    param_value = 0
            elif param_type == 'float':
                try:
                    param_value = float(param_value) if param_value else 0.0
                except (ValueError, TypeError):
                    param_value = 0.0
            elif param_type == 'boolean':
                param_value = bool(param_value) if param_value else False
            
            parameters[param_name] = param_value
        
        return parameters


# 로깅 설정
logger = logging.getLogger(__name__)
            if trigger_type == 'ENTRY':
                entry_triggers.append(trigger)
            elif trigger_type == 'EXIT':
                exit_triggers.append(trigger)
            elif trigger_type == 'MANAGEMENT':
                management_triggers.append(trigger)

        # 날짜 변환 처리
        created_at_str = strategy_row.get('created_at')
        updated_at_str = strategy_row.get('updated_at')
        created_at = (datetime.fromisoformat(created_at_str)
                      if created_at_str else datetime.now())
        updated_at = (datetime.fromisoformat(updated_at_str)
                      if updated_at_str else datetime.now())        # Strategy 엔티티 생성 (Mock)
        strategy_data = {
            'strategy_id': strategy_row['id'],
            'name': strategy_row['name'],
            'description': strategy_row.get('description'),
            'status': strategy_row.get('status', 'ACTIVE'),
            'entry_triggers': entry_triggers,
            'exit_triggers': exit_triggers,
            'management_triggers': management_triggers,
            'tags': strategy_row.get('tags', '').split(',') if strategy_row.get('tags') else [],
            'created_at': created_at,
            'updated_at': updated_at,
            'created_by': strategy_row.get('created_by', 'system'),
            'version': strategy_row.get('version', 1)
        }

        return strategy_data  # TODO: 실제 Strategy 엔티티 반환

    @staticmethod
    def to_database_record(strategy) -> Dict[str, Any]:
        """Strategy 엔티티를 데이터베이스 레코드로 변환"""
        # TODO: 실제 Strategy 엔티티 속성으로 교체

        # Mock 구현 - strategy가 dict라고 가정
        if isinstance(strategy, dict):
            strategy_id = strategy.get('strategy_id')
            name = strategy.get('name')
            description = strategy.get('description')
            status = strategy.get('status', 'ACTIVE')
            tags = strategy.get('tags', [])
            created_at = strategy.get('created_at', datetime.now())
            updated_at = strategy.get('updated_at', datetime.now())
            created_by = strategy.get('created_by', 'system')
            version = strategy.get('version', 1)
        else:
            # 실제 엔티티 객체 처리
            strategy_id = getattr(strategy, 'strategy_id', None)
            strategy_id = getattr(strategy_id, 'value', strategy_id) if strategy_id else None
            name = getattr(strategy, 'name', None)
            description = getattr(strategy, 'description', None)
            status = getattr(strategy, 'status', 'ACTIVE')
            status = getattr(status, 'value', status) if hasattr(status, 'value') else status
            tags = getattr(strategy, 'tags', [])
            created_at = getattr(strategy, 'created_at', datetime.now())
            updated_at = getattr(strategy, 'updated_at', datetime.now())
            created_by = getattr(strategy, 'created_by', 'system')
            version = getattr(strategy, 'version', 1)

        return {
            'id': strategy_id,
            'name': name,
            'description': description,
            'status': status,
            'tags': ','.join(tags) if tags else '',
            'created_at': created_at.isoformat() if isinstance(created_at, datetime) else str(created_at),
            'updated_at': updated_at.isoformat() if isinstance(updated_at, datetime) else str(updated_at),
            'created_by': created_by,
            'version': version
        }

    @staticmethod
    def to_insert_params(strategy) -> tuple:
        """INSERT 쿼리용 파라미터 튜플로 변환"""
        record = StrategyMapper.to_database_record(strategy)
        return (
            record['id'],
            record['name'],
            record['description'],
            record['status'],
            record['tags'],
            record['created_at'],
            record['updated_at'],
            record['created_by'],
            record['version']
        )

    @staticmethod
    def to_update_params(strategy) -> tuple:
        """UPDATE 쿼리용 파라미터 튜플로 변환"""
        record = StrategyMapper.to_database_record(strategy)
        return (
            record['name'],
            record['description'],
            record['status'],
            record['tags'],
            record['updated_at'],
            record['version'],
            record['id']  # WHERE 조건용
        )


class TriggerMapper:
    """Trigger 엔티티와 데이터베이스 레코드 간 매핑"""

    @staticmethod
    def to_entity(trigger_row: Dict[str, Any]):
        """데이터베이스 레코드를 Trigger 엔티티로 변환"""
        # TODO: Domain Entity 구현 완료 후 실제 로직으로 교체

        # 변수 파라미터 파싱
        variable_params = {}
        if trigger_row.get('variable_params'):
            try:
                variable_params = json.loads(trigger_row['variable_params'])
            except json.JSONDecodeError:
                logging.warning(f"잘못된 JSON 형식의 변수 파라미터: {trigger_row.get('variable_params')}")
                variable_params = {}

        # TradingVariable 생성 (Mock)
        trading_variable = {
            'variable_id': trigger_row['variable_id'],
            'parameters': variable_params
        }

        # 날짜 변환 처리
        created_at_str = trigger_row.get('created_at')
        created_at = (datetime.fromisoformat(created_at_str)
                      if created_at_str else datetime.now())

        # Trigger 엔티티 생성 (Mock)
        trigger_data = {
            'trigger_id': trigger_row['id'],
            'trigger_name': trigger_row['trigger_name'],
            'strategy_id': trigger_row['strategy_id'],
            'variable': trading_variable,
            'operator': trigger_row['operator'],
            'target_value': trigger_row['target_value'],
            'trigger_type': trigger_row['trigger_type'],
            'is_active': bool(trigger_row.get('is_active', True)),
            'weight': float(trigger_row.get('weight', 1.0)),
            'description': trigger_row.get('description'),
            'created_at': created_at
        }

        return trigger_data  # TODO: 실제 Trigger 엔티티 반환

    @staticmethod
    def to_database_record(trigger) -> Dict[str, Any]:
        """Trigger 엔티티를 데이터베이스 레코드로 변환"""
        # TODO: 실제 Trigger 엔티티 속성으로 교체

        # Mock 구현 - trigger가 dict라고 가정
        if isinstance(trigger, dict):
            trigger_id = trigger.get('trigger_id')
            trigger_name = trigger.get('trigger_name')
            strategy_id = trigger.get('strategy_id')
            variable = trigger.get('variable', {})
            variable_id = (variable.get('variable_id') if isinstance(variable, dict)
                           else getattr(variable, 'variable_id', None))
            variable_params = (variable.get('parameters', {}) if isinstance(variable, dict)
                               else getattr(variable, 'parameters', {}))
            operator = trigger.get('operator')
            target_value = trigger.get('target_value')
            trigger_type = trigger.get('trigger_type')
            is_active = trigger.get('is_active', True)
            weight = trigger.get('weight', 1.0)
            description = trigger.get('description')
            created_at = trigger.get('created_at', datetime.now())
        else:
            # 실제 엔티티 객체 처리
            trigger_id = getattr(trigger, 'trigger_id', None)
            trigger_id = getattr(trigger_id, 'value', trigger_id) if trigger_id else None
            trigger_name = getattr(trigger, 'trigger_name', None)
            strategy_id = getattr(trigger, 'strategy_id', None)
            strategy_id = getattr(strategy_id, 'value', strategy_id) if strategy_id else None

            variable = getattr(trigger, 'variable', None)
            variable_id = getattr(variable, 'variable_id', None) if variable else None
            variable_params = getattr(variable, 'parameters', {}) if variable else {}

            operator = getattr(trigger, 'operator', None)
            operator = getattr(operator, 'value', operator) if hasattr(operator, 'value') else operator
            target_value = getattr(trigger, 'target_value', None)
            trigger_type = getattr(trigger, 'trigger_type', None)
            trigger_type = getattr(trigger_type, 'value', trigger_type) if hasattr(trigger_type, 'value') else trigger_type
            is_active = getattr(trigger, 'is_active', True)
            weight = getattr(trigger, 'weight', 1.0)
            description = getattr(trigger, 'description', None)
            created_at = getattr(trigger, 'created_at', datetime.now())

        return {
            'id': trigger_id,
            'trigger_name': trigger_name,
            'strategy_id': strategy_id,
            'variable_id': variable_id,
            'variable_params': json.dumps(variable_params) if variable_params else '{}',
            'operator': operator,
            'target_value': target_value,
            'trigger_type': trigger_type,
            'is_active': is_active,
            'weight': weight,
            'description': description,
            'created_at': created_at.isoformat() if isinstance(created_at, datetime) else str(created_at)
        }

    @staticmethod
    def to_insert_params(trigger) -> tuple:
        """INSERT 쿼리용 파라미터 튜플로 변환"""
        record = TriggerMapper.to_database_record(trigger)
        return (
            record['id'],
            record['trigger_name'],
            record['strategy_id'],
            record['variable_id'],
            record['variable_params'],
            record['operator'],
            record['target_value'],
            record['trigger_type'],
            record['is_active'],
            record['weight'],
            record['description'],
            record['created_at']
        )

    @staticmethod
    def to_update_params(trigger) -> tuple:
        """UPDATE 쿼리용 파라미터 튜플로 변환"""
        record = TriggerMapper.to_database_record(trigger)
        return (
            record['trigger_name'],
            record['variable_id'],
            record['variable_params'],
            record['operator'],
            record['target_value'],
            record['trigger_type'],
            record['is_active'],
            record['weight'],
            record['description'],
            record['id']  # WHERE 조건용
        )


class TradingVariableMapper:
    """TradingVariable 매핑 (Settings DB 읽기 전용)"""

    @staticmethod
    def to_entity(variable_row: Dict[str, Any],
                  parameters: Optional[List[Dict[str, Any]]] = None):
        """데이터베이스 레코드를 TradingVariable로 변환"""
        if parameters is None:
            parameters = []

        # TODO: 실제 TradingVariable 엔티티로 교체
        variable_data = {
            'variable_id': variable_row['variable_id'],
            'display_name_ko': variable_row['display_name_ko'],
            'display_name_en': variable_row.get('display_name_en'),
            'purpose_category': variable_row['purpose_category'],
            'chart_category': variable_row['chart_category'],
            'comparison_group': variable_row['comparison_group'],
            'parameters': parameters,
            'description': variable_row.get('description'),
            'source': variable_row.get('source', 'built-in'),
            'is_active': bool(variable_row.get('is_active', True))
        }

        return variable_data  # TODO: 실제 TradingVariable 엔티티 반환

    @staticmethod
    def parse_parameter_string(param_string: str) -> Dict[str, Any]:
        """파라미터 문자열을 딕셔너리로 파싱"""
        try:
            # 파라미터가 JSON 형태라면
            return json.loads(param_string)
        except json.JSONDecodeError:
            # 구분자로 분리된 형태라면
            parts = param_string.split(':')
            if len(parts) >= 8:
                param = {
                    'parameter_name': parts[0],
                    'parameter_type': parts[1],
                    'default_value': parts[2] if parts[2] else None,
                    'min_value': parts[3] if parts[3] else None,
                    'max_value': parts[4] if parts[4] else None,
                    'enum_values': parts[5] if parts[5] else None,
                    'is_required': bool(int(parts[6])) if parts[6].isdigit() else True,
                    'display_name_ko': parts[7] if len(parts) > 7 else parts[0]
                }

                # enum_values JSON 파싱
                if param['enum_values']:
                    try:
                        param['enum_values'] = json.loads(param['enum_values'])
                    except json.JSONDecodeError:
                        pass

                return param

        return {}
