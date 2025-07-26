"""
트레이딩 지표 파라미터 관리 시스템

지표별 파라미터 정의, 유효성 검증, 기본값 관리를 담당하는 클래스입니다.
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParameterDefinition:
    """파라미터 정의 클래스"""
    parameter_id: int
    variable_id: str
    parameter_name: str
    parameter_type: str  # 'integer', 'float', 'string', 'boolean', 'enum'
    default_value: str
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    enum_values: Optional[List[str]] = None
    is_required: bool = True
    display_name_ko: str = ""
    display_name_en: str = ""
    description: str = ""
    display_order: int = 0

    def __post_init__(self):
        """enum_values가 JSON 문자열인 경우 파싱"""
        if self.enum_values and isinstance(self.enum_values, str):
            try:
                self.enum_values = json.loads(self.enum_values)
            except (json.JSONDecodeError, TypeError):
                self.enum_values = []


@dataclass
class ParameterValue:
    """파라미터 값 클래스"""
    parameter_name: str
    value: Any
    is_valid: bool = True
    error_message: str = ""


class ParameterManager:
    """트레이딩 지표 파라미터 관리 클래스"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Args:
            db_path: SQLite 데이터베이스 파일 경로. None이면 자동으로 설정
        """
        if db_path is None:
            # 현재 모듈과 같은 디렉토리에 DB 파일 생성
            current_dir = Path(__file__).parent
            db_path = current_dir / "trading_variables.db"
        
        self.db_path = str(db_path)
        self._init_database()
    
    def _init_database(self):
        """데이터베이스 초기화 및 스키마 생성"""
        schema_file = Path(__file__).parent / "schema.sql"
        
        if not schema_file.exists():
            raise FileNotFoundError(f"스키마 파일을 찾을 수 없습니다: {schema_file}")
        
        with sqlite3.connect(self.db_path) as conn:
            # 스키마 파일 실행
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                conn.executescript(schema_sql)
            conn.commit()
    
    def get_parameter_definitions(self, variable_id: str) -> List[ParameterDefinition]:
        """
        지정된 지표의 모든 파라미터 정의를 가져옵니다.
        
        Args:
            variable_id: 지표 ID (예: 'SMA', 'RSI')
            
        Returns:
            파라미터 정의 리스트 (display_order 순으로 정렬)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM variable_parameters
                WHERE variable_id = ?
                ORDER BY display_order ASC, parameter_name ASC
            """, (variable_id,))
            
            definitions = []
            for row in cursor.fetchall():
                definitions.append(ParameterDefinition(
                    parameter_id=row['parameter_id'],
                    variable_id=row['variable_id'],
                    parameter_name=row['parameter_name'],
                    parameter_type=row['parameter_type'],
                    default_value=row['default_value'],
                    min_value=row['min_value'],
                    max_value=row['max_value'],
                    enum_values=row['enum_values'],
                    is_required=bool(row['is_required']),
                    display_name_ko=row['display_name_ko'],
                    display_name_en=row['display_name_en'],
                    description=row['description'],
                    display_order=row['display_order']
                ))
            
            return definitions
    
    def get_default_parameters(self, variable_id: str) -> Dict[str, Any]:
        """
        지정된 지표의 기본 파라미터 값들을 가져옵니다.
        
        Args:
            variable_id: 지표 ID
            
        Returns:
            파라미터명 -> 기본값 딕셔너리
        """
        definitions = self.get_parameter_definitions(variable_id)
        defaults = {}
        
        for defn in definitions:
            defaults[defn.parameter_name] = self._parse_value(
                defn.default_value, defn.parameter_type
            )
        
        return defaults
    
    def validate_parameters(self, variable_id: str, parameters: Dict[str, Any]) -> List[ParameterValue]:
        """
        파라미터 값들의 유효성을 검증합니다.
        
        Args:
            variable_id: 지표 ID
            parameters: 검증할 파라미터 딕셔너리
            
        Returns:
            검증 결과 리스트
        """
        definitions = {defn.parameter_name: defn for defn in self.get_parameter_definitions(variable_id)}
        results = []
        
        # 필수 파라미터 확인
        for param_name, defn in definitions.items():
            if defn.is_required and param_name not in parameters:
                results.append(ParameterValue(
                    parameter_name=param_name,
                    value=None,
                    is_valid=False,
                    error_message=f"필수 파라미터 '{param_name}'이 누락되었습니다."
                ))
                continue
            
            if param_name in parameters:
                value = parameters[param_name]
                validation_result = self._validate_single_parameter(defn, value)
                results.append(validation_result)
        
        # 정의되지 않은 파라미터 확인
        for param_name in parameters:
            if param_name not in definitions:
                results.append(ParameterValue(
                    parameter_name=param_name,
                    value=parameters[param_name],
                    is_valid=False,
                    error_message=f"정의되지 않은 파라미터 '{param_name}'입니다."
                ))
        
        return results
    
    def _validate_single_parameter(self, definition: ParameterDefinition, value: Any) -> ParameterValue:
        """단일 파라미터 유효성 검증"""
        param_name = definition.parameter_name
        param_type = definition.parameter_type
        
        try:
            # 타입 변환 및 검증
            if param_type == 'integer':
                value = int(value)
                if definition.min_value and value < int(definition.min_value):
                    return ParameterValue(param_name, value, False, 
                                        f"값이 최소값 {definition.min_value}보다 작습니다.")
                if definition.max_value and value > int(definition.max_value):
                    return ParameterValue(param_name, value, False, 
                                        f"값이 최대값 {definition.max_value}보다 큽니다.")
            
            elif param_type == 'float':
                value = float(value)
                if definition.min_value and value < float(definition.min_value):
                    return ParameterValue(param_name, value, False, 
                                        f"값이 최소값 {definition.min_value}보다 작습니다.")
                if definition.max_value and value > float(definition.max_value):
                    return ParameterValue(param_name, value, False, 
                                        f"값이 최대값 {definition.max_value}보다 큽니다.")
            
            elif param_type == 'boolean':
                if isinstance(value, str):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    value = bool(value)
            
            elif param_type == 'enum':
                value = str(value)
                if definition.enum_values and value not in definition.enum_values:
                    return ParameterValue(param_name, value, False, 
                                        f"허용되지 않는 값입니다. 가능한 값: {definition.enum_values}")
            
            elif param_type == 'string':
                value = str(value)
            
            else:
                return ParameterValue(param_name, value, False, 
                                    f"알 수 없는 파라미터 타입: {param_type}")
            
            return ParameterValue(param_name, value, True)
            
        except (ValueError, TypeError) as e:
            return ParameterValue(param_name, value, False, 
                                f"타입 변환 오류: {str(e)}")
    
    def _parse_value(self, value_str: str, param_type: str) -> Any:
        """문자열 값을 적절한 타입으로 변환"""
        if value_str is None:
            return None
        
        if param_type == 'integer':
            return int(value_str)
        elif param_type == 'float':
            return float(value_str)
        elif param_type == 'boolean':
            return value_str.lower() in ('true', '1', 'yes', 'on')
        else:  # string, enum
            return value_str
    
    def add_parameter_definition(self, variable_id: str, parameter_name: str, 
                               parameter_type: str, default_value: str,
                               display_name_ko: str, **kwargs) -> bool:
        """
        새로운 파라미터 정의를 추가합니다.
        
        Args:
            variable_id: 지표 ID
            parameter_name: 파라미터명
            parameter_type: 파라미터 타입
            default_value: 기본값
            display_name_ko: 한국어 표시명
            **kwargs: 기타 옵션들
            
        Returns:
            성공 여부
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO variable_parameters 
                    (variable_id, parameter_name, parameter_type, default_value,
                     min_value, max_value, enum_values, is_required,
                     display_name_ko, display_name_en, description, display_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    variable_id, parameter_name, parameter_type, default_value,
                    kwargs.get('min_value'), kwargs.get('max_value'),
                    json.dumps(kwargs.get('enum_values')) if kwargs.get('enum_values') else None,
                    kwargs.get('is_required', True),
                    display_name_ko, kwargs.get('display_name_en', ''),
                    kwargs.get('description', ''), kwargs.get('display_order', 0)
                ))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"파라미터 정의 추가 실패: {e}")
            return False
    
    def get_supported_variable_ids(self) -> List[str]:
        """파라미터가 정의된 지표 ID들을 가져옵니다."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT variable_id FROM variable_parameters ORDER BY variable_id")
            return [row[0] for row in cursor.fetchall()]
    
    def get_parameter_summary(self, variable_id: str) -> Dict[str, Any]:
        """지표의 파라미터 요약 정보를 가져옵니다."""
        definitions = self.get_parameter_definitions(variable_id)
        
        return {
            'variable_id': variable_id,
            'parameter_count': len(definitions),
            'required_parameters': [d.parameter_name for d in definitions if d.is_required],
            'optional_parameters': [d.parameter_name for d in definitions if not d.is_required],
            'parameter_types': {d.parameter_name: d.parameter_type for d in definitions},
            'default_values': {d.parameter_name: self._parse_value(d.default_value, d.parameter_type) 
                             for d in definitions}
        }


def main():
    """CLI 테스트"""
    manager = ParameterManager()
    
    print("🔧 파라미터 관리 시스템 테스트")
    print("=" * 50)
    
    # 지원되는 지표들 확인
    supported_vars = manager.get_supported_variable_ids()
    print(f"📋 파라미터가 정의된 지표들: {supported_vars}")
    print()
    
    # SMA 파라미터 테스트
    print("📈 SMA 파라미터 정의:")
    sma_definitions = manager.get_parameter_definitions('SMA')
    for defn in sma_definitions:
        print(f"  - {defn.parameter_name} ({defn.parameter_type}): "
              f"기본값={defn.default_value}, 필수={defn.is_required}")
    
    print("\n📈 SMA 기본 파라미터:")
    sma_defaults = manager.get_default_parameters('SMA')
    print(f"  {sma_defaults}")
    
    # 파라미터 검증 테스트
    print("\n✅ 파라미터 검증 테스트:")
    test_params = {'period': 20, 'source': 'close'}
    validation_results = manager.validate_parameters('SMA', test_params)
    
    all_valid = all(result.is_valid for result in validation_results)
    print(f"  테스트 파라미터: {test_params}")
    print(f"  검증 결과: {'✅ 성공' if all_valid else '❌ 실패'}")
    
    for result in validation_results:
        if not result.is_valid:
            print(f"    - {result.parameter_name}: {result.error_message}")
    
    # 잘못된 파라미터 테스트
    print("\n❌ 잘못된 파라미터 테스트:")
    bad_params = {'period': -5, 'source': 'invalid', 'unknown': 'test'}
    bad_results = manager.validate_parameters('SMA', bad_params)
    
    print(f"  테스트 파라미터: {bad_params}")
    for result in bad_results:
        if not result.is_valid:
            print(f"    - {result.parameter_name}: {result.error_message}")


if __name__ == "__main__":
    main()
