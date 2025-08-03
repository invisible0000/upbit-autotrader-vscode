# 📋 TASK-20250802-16: 조건 관리 서비스 구현

## 🎯 **작업 개요**
condition_builder.py의 조건 생성 및 관리 로직을 business_logic으로 분리하여 확장 가능한 조건 관리 시스템을 구현합니다.

## 📊 **현재 상황**

### **분리 대상 파일들**
```python
# components/core/condition_builder.py (342줄)
├── build_condition_from_ui() → 조건 객체 생성
├── generate_execution_code() → 실행 코드 생성
├── _generate_python_code() → Python 코드 생성
├── _generate_pine_script_code() → Pine Script 생성
└── _generate_auto_name() → 자동 이름 생성

# components/core/condition_validator.py
├── validate_condition() → 조건 검증
├── check_variable_compatibility() → 변수 호환성 검사
└── validate_parameters() → 파라미터 검증

# components/core/variable_definitions.py
├── get_variable_definition() → 변수 정의 조회
├── get_all_variables() → 전체 변수 목록
└── get_compatible_variables() → 호환 변수 조회
```

### **조건 관리 워크플로우**
```python
# 현재 조건 생성 플로우
UI Input → ConditionBuilder → Validation → Storage → Execution Code
├── 1. UI에서 조건 데이터 입력
├── 2. ConditionBuilder로 조건 객체 생성  
├── 3. ConditionValidator로 검증
├── 4. ConditionStorage에 저장
└── 5. ExecutionCodeGenerator로 실행 코드 생성
```

## 🏗️ **구현 목표**

### **새로운 서비스 구조**
```
business_logic/conditions/
├── builders/
│   ├── __init__.py
│   ├── condition_factory.py                # 조건 객체 팩토리
│   └── execution_code_generator.py         # 실행 코드 생성기
├── validators/
│   ├── __init__.py
│   ├── condition_compatibility_checker.py  # 호환성 검증
│   └── parameter_validator.py              # 파라미터 검증
├── models/
│   ├── __init__.py
│   ├── condition_model.py                  # 조건 모델
│   ├── variable_definition_model.py        # 변수 정의 모델
│   └── execution_context_model.py          # 실행 컨텍스트 모델
└── services/
    ├── __init__.py
    ├── condition_orchestration_service.py  # 메인 조건 관리 서비스
    ├── condition_crud_service.py           # 조건 CRUD 서비스
    └── variable_definition_service.py      # 변수 정의 서비스
```

### **ConditionOrchestrationService 클래스 설계**
```python
class ConditionOrchestrationService:
    """조건 관리 오케스트레이션 서비스 - 전체 조건 워크플로우 관리"""
    
    def __init__(self):
        """서비스 컴포넌트들 초기화"""
        self._condition_factory = ConditionFactory()
        self._compatibility_checker = ConditionCompatibilityChecker()
        self._parameter_validator = ParameterValidator()
        self._code_generator = ExecutionCodeGenerator()
        self._crud_service = ConditionCrudService()
    
    def create_condition_from_ui(self, ui_data: Dict[str, Any]) -> ConditionCreationResult:
        """UI 데이터로부터 완전한 조건 생성 및 검증"""
        
    def validate_condition(self, condition: ConditionModel) -> ValidationResult:
        """조건 완전성 검증"""
        
    def generate_execution_code(self, condition: ConditionModel, 
                              language: str = "python") -> CodeGenerationResult:
        """조건 실행 코드 생성"""
        
    def save_condition(self, condition: ConditionModel) -> SaveResult:
        """조건 저장 (검증 포함)"""
        
    def update_condition(self, condition_id: str, updates: Dict[str, Any]) -> UpdateResult:
        """조건 업데이트"""
```

## 📋 **상세 작업 내용**

### **1. 모델 클래스 구현 (2시간)**
```python
# business_logic/conditions/models/condition_model.py
"""
조건 관련 모델 클래스들
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime

class ConditionCategory(Enum):
    """조건 카테고리"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    CUSTOM = "custom"
    COMPOSITE = "composite"

class ComparisonType(Enum):
    """비교 타입"""
    FIXED_VALUE = "fixed"
    VARIABLE_COMPARISON = "variable"
    CROSS_SIGNAL = "cross"
    TREND_ANALYSIS = "trend"

@dataclass
class VariableInfo:
    """변수 정보"""
    variable_id: str
    variable_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    display_name: Optional[str] = None

@dataclass
class ConditionModel:
    """조건 모델"""
    # 기본 정보
    condition_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: ConditionCategory = ConditionCategory.CUSTOM
    
    # 조건 구성 요소
    variable_info: Optional[VariableInfo] = None
    operator: str = ">"
    comparison_type: ComparisonType = ComparisonType.FIXED_VALUE
    target_value: Any = ""
    external_variable: Optional[VariableInfo] = None
    
    # 추가 설정
    trend_direction: str = "static"
    tolerance_settings: Dict[str, Any] = field(default_factory=dict)
    
    # 메타데이터
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    is_active: bool = True
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "condition_id": self.condition_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "variable_info": self.variable_info.__dict__ if self.variable_info else None,
            "operator": self.operator,
            "comparison_type": self.comparison_type.value,
            "target_value": self.target_value,
            "external_variable": self.external_variable.__dict__ if self.external_variable else None,
            "trend_direction": self.trend_direction,
            "tolerance_settings": self.tolerance_settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "is_active": self.is_active,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConditionModel':
        """딕셔너리로부터 객체 생성"""
        # 복잡한 변환 로직 구현...
        pass

@dataclass
class ValidationResult:
    """검증 결과"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

@dataclass
class ConditionCreationResult:
    """조건 생성 결과"""
    success: bool
    condition: Optional[ConditionModel] = None
    validation_result: Optional[ValidationResult] = None
    error_message: Optional[str] = None

@dataclass
class CodeGenerationResult:
    """코드 생성 결과"""
    success: bool
    code: str = ""
    language: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
```

### **2. 조건 팩토리 구현 (2시간)**
```python
# business_logic/conditions/builders/condition_factory.py
"""
조건 객체 팩토리
UI 데이터로부터 조건 객체를 생성
"""

from typing import Dict, Any, Optional
import logging
from ..models.condition_model import (
    ConditionModel, VariableInfo, ConditionCategory, 
    ComparisonType, ConditionCreationResult, ValidationResult
)

class ConditionFactory:
    """조건 객체 팩토리"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 카테고리 매핑
        self._category_mapping = {
            "technical": ConditionCategory.TECHNICAL,
            "fundamental": ConditionCategory.FUNDAMENTAL, 
            "custom": ConditionCategory.CUSTOM,
            "composite": ConditionCategory.COMPOSITE
        }
        
        # 비교 타입 매핑
        self._comparison_type_mapping = {
            "fixed": ComparisonType.FIXED_VALUE,
            "variable": ComparisonType.VARIABLE_COMPARISON,
            "cross": ComparisonType.CROSS_SIGNAL,
            "trend": ComparisonType.TREND_ANALYSIS
        }
    
    def create_from_ui_data(self, ui_data: Dict[str, Any]) -> ConditionCreationResult:
        """
        UI 데이터로부터 조건 객체 생성
        기존 build_condition_from_ui() 메서드를 대체
        
        Args:
            ui_data: UI에서 전달된 조건 데이터
            
        Returns:
            ConditionCreationResult: 생성 결과 및 검증 정보
        """
        try:
            self.logger.debug(f"조건 객체 생성 시작: {ui_data.get('name', 'Unnamed')}")
            
            # 기본 정보 추출
            condition = ConditionModel(
                name=ui_data.get("name", "").strip(),
                description=ui_data.get("description", "").strip(),
                category=self._parse_category(ui_data.get("category", "custom")),
                operator=ui_data.get("operator", ">"),
                comparison_type=self._parse_comparison_type(ui_data.get("comparison_type", "fixed")),
                target_value=ui_data.get("target_value", ""),
                trend_direction=ui_data.get("trend_direction", "static")
            )
            
            # 변수 정보 설정
            if ui_data.get("variable_id"):
                condition.variable_info = VariableInfo(
                    variable_id=ui_data["variable_id"],
                    variable_name=ui_data.get("variable_name", ""),
                    parameters=ui_data.get("variable_params", {}),
                    display_name=ui_data.get("variable_display_name")
                )
            
            # 외부 변수 설정 (변수 간 비교시)
            if ui_data.get("external_variable"):
                ext_var = ui_data["external_variable"]
                condition.external_variable = VariableInfo(
                    variable_id=ext_var.get("variable_id", ""),
                    variable_name=ext_var.get("variable_name", ""),
                    parameters=ext_var.get("parameters", {}),
                    display_name=ext_var.get("display_name")
                )
            
            # 허용 오차 설정
            if ui_data.get("tolerance_settings"):
                condition.tolerance_settings = ui_data["tolerance_settings"]
            
            # 태그 설정
            if ui_data.get("tags"):
                condition.tags = ui_data["tags"] if isinstance(ui_data["tags"], list) else [ui_data["tags"]]
            
            # 자동 이름 생성 (필요시)
            if not condition.name:
                condition.name = self._generate_auto_name(condition)
            
            # 기본 검증 수행
            validation_result = self._perform_basic_validation(condition)
            
            success = validation_result.is_valid or len(validation_result.errors) == 0
            
            self.logger.debug(f"조건 객체 생성 완료: {condition.name} (성공: {success})")
            
            return ConditionCreationResult(
                success=success,
                condition=condition,
                validation_result=validation_result
            )
            
        except Exception as e:
            self.logger.error(f"조건 객체 생성 오류: {str(e)}")
            return ConditionCreationResult(
                success=False,
                error_message=str(e)
            )
    
    def _parse_category(self, category_str: str) -> ConditionCategory:
        """카테고리 문자열을 열거형으로 변환"""
        return self._category_mapping.get(category_str.lower(), ConditionCategory.CUSTOM)
    
    def _parse_comparison_type(self, type_str: str) -> ComparisonType:
        """비교 타입 문자열을 열거형으로 변환"""
        return self._comparison_type_mapping.get(type_str.lower(), ComparisonType.FIXED_VALUE)
    
    def _generate_auto_name(self, condition: ConditionModel) -> str:
        """
        조건의 자동 이름 생성
        기존 _generate_auto_name() 메서드를 개선
        """
        if not condition.variable_info:
            return f"조건_{condition.condition_id[:8]}"
        
        var_name = condition.variable_info.variable_name or condition.variable_info.variable_id
        operator = condition.operator
        
        if condition.comparison_type == ComparisonType.FIXED_VALUE:
            target = str(condition.target_value)
            return f"{var_name} {operator} {target}"
        elif condition.comparison_type == ComparisonType.VARIABLE_COMPARISON:
            if condition.external_variable:
                ext_name = condition.external_variable.variable_name or condition.external_variable.variable_id
                return f"{var_name} {operator} {ext_name}"
        elif condition.comparison_type == ComparisonType.CROSS_SIGNAL:
            if condition.external_variable:
                ext_name = condition.external_variable.variable_name or condition.external_variable.variable_id
                return f"{var_name} cross {ext_name}"
        elif condition.comparison_type == ComparisonType.TREND_ANALYSIS:
            direction = condition.trend_direction
            return f"{var_name} trend {direction}"
        
        return f"{var_name} 조건"
    
    def _perform_basic_validation(self, condition: ConditionModel) -> ValidationResult:
        """기본 검증 수행"""
        errors = []
        warnings = []
        suggestions = []
        
        # 필수 필드 검증
        if not condition.name:
            errors.append("조건 이름이 필요합니다")
        
        if not condition.variable_info:
            errors.append("기준 변수가 설정되지 않았습니다")
        
        if not condition.operator:
            errors.append("비교 연산자가 설정되지 않았습니다")
        
        # 비교 타입별 검증
        if condition.comparison_type == ComparisonType.FIXED_VALUE:
            if condition.target_value == "" or condition.target_value is None:
                errors.append("비교할 고정값이 설정되지 않았습니다")
        elif condition.comparison_type == ComparisonType.VARIABLE_COMPARISON:
            if not condition.external_variable:
                errors.append("비교할 외부 변수가 설정되지 않았습니다")
        
        # 경고 및 제안
        if len(condition.name) > 50:
            warnings.append("조건 이름이 너무 깁니다 (50자 이하 권장)")
        
        if not condition.description:
            suggestions.append("조건에 대한 설명을 추가하면 관리가 용이합니다")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def create_template_condition(self, template_type: str) -> ConditionModel:
        """템플릿 조건 생성"""
        templates = {
            "rsi_oversold": {
                "name": "RSI 과매도 조건",
                "description": "RSI가 30 이하로 하락할 때",
                "variable_id": "RSI",
                "variable_name": "RSI",
                "operator": "<=",
                "target_value": 30,
                "category": "technical"
            },
            "sma_cross": {
                "name": "SMA 골든 크로스",
                "description": "5일 이평선이 20일 이평선을 상향 돌파",
                "variable_id": "SMA",
                "variable_name": "SMA_5",
                "comparison_type": "cross",
                "operator": "cross_above",
                "external_variable": {
                    "variable_id": "SMA",
                    "variable_name": "SMA_20",
                    "parameters": {"period": 20}
                },
                "category": "technical"
            }
        }
        
        if template_type in templates:
            return self.create_from_ui_data(templates[template_type]).condition
        else:
            raise ValueError(f"지원하지 않는 템플릿 타입: {template_type}")
```

### **3. 실행 코드 생성기 구현 (2시간)**
```python
# business_logic/conditions/builders/execution_code_generator.py
"""
조건 실행 코드 생성기
Python, Pine Script 등 다양한 언어로 조건 실행 코드 생성
"""

from typing import Dict, Any, Optional
import logging
from ..models.condition_model import ConditionModel, ComparisonType, CodeGenerationResult

class ExecutionCodeGenerator:
    """실행 코드 생성기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._code_generators = {
            "python": self._generate_python_code,
            "pine_script": self._generate_pine_script_code,
            "pseudocode": self._generate_pseudocode
        }
    
    def generate_code(self, condition: ConditionModel, language: str = "python", 
                     options: Dict[str, Any] = None) -> CodeGenerationResult:
        """
        조건 실행 코드 생성
        기존 generate_execution_code() 메서드를 대체
        
        Args:
            condition: 조건 모델
            language: 생성할 언어 (python, pine_script, pseudocode)
            options: 생성 옵션
            
        Returns:
            CodeGenerationResult: 생성된 코드 및 메타데이터
        """
        try:
            self.logger.debug(f"코드 생성 시작: {condition.name} ({language})")
            
            if language not in self._code_generators:
                return CodeGenerationResult(
                    success=False,
                    error_message=f"지원하지 않는 언어: {language}"
                )
            
            # 언어별 코드 생성
            generator = self._code_generators[language]
            code, metadata = generator(condition, options or {})
            
            self.logger.debug(f"코드 생성 완료: {len(code)} 문자")
            
            return CodeGenerationResult(
                success=True,
                code=code,
                language=language,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"코드 생성 오류: {str(e)}")
            return CodeGenerationResult(
                success=False,
                language=language,
                error_message=str(e)
            )
    
    def _generate_python_code(self, condition: ConditionModel, 
                            options: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Python 실행 코드 생성"""
        if not condition.variable_info:
            raise ValueError("변수 정보가 없습니다")
        
        var_name = condition.variable_info.variable_id
        var_params = condition.variable_info.parameters
        
        # 변수 계산 코드 생성
        calc_code = self._generate_variable_calculation_code(var_name, var_params)
        
        # 조건 체크 코드 생성
        if condition.comparison_type == ComparisonType.FIXED_VALUE:
            condition_code = self._generate_fixed_value_condition(condition)
        elif condition.comparison_type == ComparisonType.VARIABLE_COMPARISON:
            condition_code = self._generate_variable_comparison_condition(condition)
        elif condition.comparison_type == ComparisonType.CROSS_SIGNAL:
            condition_code = self._generate_cross_signal_condition(condition)
        else:
            condition_code = self._generate_trend_condition(condition)
        
        # 전체 함수 생성
        function_name = f"check_{condition.name.replace(' ', '_').lower()}"
        
        code = f'''def {function_name}(price_data, current_index=None):
    """
    조건: {condition.name}
    설명: {condition.description}
    """
    try:
        # 변수 계산
{calc_code}
        
        # 조건 체크
{condition_code}
        
        return result
    except Exception as e:
        logging.error(f"조건 체크 오류: {{e}}")
        return False
'''
        
        metadata = {
            "function_name": function_name,
            "condition_id": condition.condition_id,
            "dependencies": [var_name],
            "parameters": var_params
        }
        
        return code, metadata
    
    def _generate_variable_calculation_code(self, var_name: str, 
                                          parameters: Dict[str, Any]) -> str:
        """변수 계산 코드 생성"""
        if var_name == "SMA":
            period = parameters.get("period", 20)
            return f"        sma_values = calculate_sma(price_data, {period})"
        elif var_name == "EMA":
            period = parameters.get("period", 20)
            return f"        ema_values = calculate_ema(price_data, {period})"
        elif var_name == "RSI":
            period = parameters.get("period", 14)
            return f"        rsi_values = calculate_rsi(price_data, {period})"
        elif var_name == "MACD":
            fast = parameters.get("fast", 12)
            slow = parameters.get("slow", 26)
            signal = parameters.get("signal", 9)
            return f"        macd_values = calculate_macd(price_data, {fast}, {slow}, {signal})"
        else:
            return f"        {var_name.lower()}_values = calculate_{var_name.lower()}(price_data, **{parameters})"
    
    def _generate_fixed_value_condition(self, condition: ConditionModel) -> str:
        """고정값 비교 조건 코드 생성"""
        var_name = condition.variable_info.variable_id.lower()
        operator = condition.operator
        target = condition.target_value
        
        return f'''        if current_index is None:
            current_index = len({var_name}_values) - 1
        
        if current_index < 0 or current_index >= len({var_name}_values):
            return False
        
        current_value = {var_name}_values[current_index]
        result = current_value {operator} {target}'''
    
    def _generate_variable_comparison_condition(self, condition: ConditionModel) -> str:
        """변수 간 비교 조건 코드 생성"""
        base_var = condition.variable_info.variable_id.lower()
        ext_var = condition.external_variable.variable_id.lower()
        operator = condition.operator
        
        # 외부 변수 계산 코드 추가 필요
        ext_calc_code = self._generate_variable_calculation_code(
            condition.external_variable.variable_id, 
            condition.external_variable.parameters
        )
        
        return f'''        # 외부 변수 계산
{ext_calc_code}
        
        if current_index is None:
            current_index = len({base_var}_values) - 1
        
        if current_index < 0 or current_index >= min(len({base_var}_values), len({ext_var}_values)):
            return False
        
        base_value = {base_var}_values[current_index]
        ext_value = {ext_var}_values[current_index]
        result = base_value {operator} ext_value'''
    
    def _generate_cross_signal_condition(self, condition: ConditionModel) -> str:
        """크로스 신호 조건 코드 생성"""
        base_var = condition.variable_info.variable_id.lower()
        ext_var = condition.external_variable.variable_id.lower()
        operator = condition.operator
        
        if operator == "cross_above":
            cross_logic = f"prev_base <= prev_ext and curr_base > curr_ext"
        elif operator == "cross_below":
            cross_logic = f"prev_base >= prev_ext and curr_base < curr_ext"
        else:
            cross_logic = f"# Custom cross logic for {operator}"
        
        return f'''        if current_index is None:
            current_index = len({base_var}_values) - 1
        
        if current_index < 1 or current_index >= min(len({base_var}_values), len({ext_var}_values)):
            return False
        
        prev_base = {base_var}_values[current_index - 1]
        curr_base = {base_var}_values[current_index]
        prev_ext = {ext_var}_values[current_index - 1]
        curr_ext = {ext_var}_values[current_index]
        
        result = {cross_logic}'''
    
    def _generate_pine_script_code(self, condition: ConditionModel, 
                                 options: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Pine Script 코드 생성"""
        var_name = condition.variable_info.variable_id
        
        if var_name == "SMA":
            period = condition.variable_info.parameters.get("period", 20)
            pine_code = f"sma_value = ta.sma(close, {period})"
        elif var_name == "RSI":
            period = condition.variable_info.parameters.get("period", 14)
            pine_code = f"rsi_value = ta.rsi(close, {period})"
        else:
            pine_code = f"// Custom indicator: {var_name}"
        
        if condition.comparison_type == ComparisonType.FIXED_VALUE:
            condition_check = f"condition_met = {var_name.lower()}_value {condition.operator} {condition.target_value}"
        else:
            condition_check = "// Complex condition logic needed"
        
        code = f'''// 조건: {condition.name}
// 설명: {condition.description}

//@version=5
indicator("{condition.name}", overlay=true)

// 변수 계산
{pine_code}

// 조건 체크
{condition_check}

// 시각화
plotshape(condition_met, title="Signal", location=location.belowbar, color=color.green, style=shape.triangleup)
'''
        
        metadata = {
            "version": 5,
            "overlay": True,
            "condition_id": condition.condition_id
        }
        
        return code, metadata
    
    def _generate_pseudocode(self, condition: ConditionModel, 
                           options: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """의사코드 생성"""
        code = f'''조건: {condition.name}
설명: {condition.description}

절차:
1. {condition.variable_info.variable_name} 계산
2. 현재값이 {condition.operator} {condition.target_value}인지 확인
3. 조건 만족시 True, 불만족시 False 반환

예시:
만약 ({condition.variable_info.variable_name} {condition.operator} {condition.target_value}) 이면
    신호 발생
그렇지 않으면
    대기
'''
        
        metadata = {"type": "pseudocode", "language": "korean"}
        return code, metadata
```

## ✅ **완료 기준**

### **구현 완료 체크리스트**
- [ ] 조건 모델 클래스 구현 완료
- [ ] 조건 팩토리 구현 완료
- [ ] 실행 코드 생성기 구현 완료
- [ ] 조건 검증 및 호환성 체커 구현
- [ ] 조건 CRUD 서비스 구현
- [ ] 단위 테스트 90% 이상 커버리지

### **품질 기준**
- [ ] 기존 condition_builder.py 기능 100% 호환성
- [ ] Python, Pine Script 코드 생성 지원
- [ ] 타입 안전성 및 에러 처리
- [ ] 확장 가능한 아키텍처

### **검증 명령어**
```powershell
# 단위 테스트 실행
pytest tests/unit/conditions/ -v

# 통합 테스트 실행
pytest tests/integration/test_condition_management.py -v
```

## 🔗 **연관 작업**
- **이전**: TASK-20250802-15 (트리거 빌더 UI 어댑터 구현)
- **다음**: TASK-20250802-17 (미니차트 시각화 서비스 구현)
- **관련**: TASK-20250802-18 (전체 통합 테스트)

## 📊 **예상 소요 시간**
- **총 소요 시간**: 8시간
- **우선순위**: HIGH
- **복잡도**: MEDIUM-HIGH
- **리스크**: LOW

---
**작성일**: 2025년 8월 2일  
**담당자**: GitHub Copilot  
**문서 타입**: 서비스 구현 작업
