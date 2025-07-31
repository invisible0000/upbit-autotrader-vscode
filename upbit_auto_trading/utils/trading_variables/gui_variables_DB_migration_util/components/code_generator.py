#!/usr/bin/env python3
"""
Variable Definitions 코드 생성기
================================

DB 데이터를 기반으로 variable_definitions.py 파일을 생성하는 전용 모듈

주요 기능:
- DB 데이터 → Python 코드 변환
- data_info 정보 통합 (향후 DB 마이그레이션 예정)
- 코드 템플릿 관리
- 안전한 파일 생성

작성일: 2025-07-30
"""

from typing import Dict, Any, List
from datetime import datetime
import os
import json


class VariableDefinitionsGenerator:
    """variable_definitions.py 파일 생성기"""
    
    def __init__(self, db_data: Dict[str, Any], data_info: Dict[str, Any] = None):
        """
        초기화
        
        Args:
            db_data: DB에서 가져온 지표 데이터
            data_info: data_info 폴더의 YAML 데이터 (선택사항)
        """
        self.db_data = db_data
        self.data_info = data_info or {}
        self.indicators = db_data.get("indicators", {})
        self.categories = db_data.get("categories", {})
        self.chart_categories = db_data.get("chart_categories", {})
        self.stats = db_data.get("stats", {})
    
    def generate_file_content(self) -> str:
        """전체 파일 내용 생성"""
        sections = [
            self._generate_header(),
            self._generate_imports(),
            self._generate_class_declaration(),
            self._generate_chart_categories(),
            self._generate_parameters_method(),
            self._generate_descriptions_method(),
            self._generate_category_method(),
            self._generate_placeholders_method(),
            self._generate_help_text_method(),
            self._generate_utility_methods()
        ]
        
        return "\n".join(sections)
    
    def save_to_file(self, file_path: str) -> bool:
        """파일로 저장"""
        try:
            content = self.generate_file_content()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ 파일 저장 실패: {e}")
            return False
    
    def _generate_header(self) -> str:
        """파일 헤더 생성"""
        total_indicators = self.stats.get("active_indicators", len(self.indicators))
        total_parameters = self.stats.get("total_parameters", 0)
        
        # data_info 상태 확인
        data_info_status = ""
        if self.data_info:
            indicator_lib = self.data_info.get('indicator_library', {})
            help_texts = self.data_info.get('help_texts', {})
            placeholders = self.data_info.get('placeholder_texts', {})
            
            data_info_status = f"""
📋 **data_info 상태**:
  ✅ indicator_library: {len(indicator_lib.get('indicators', {}))}개 정의
  ✅ help_texts: {len(help_texts.get('parameter_help_texts', {}))}개 도움말
  ✅ placeholders: {len(placeholders.get('indicators', {}))}개 예시"""
        else:
            data_info_status = """
📋 **data_info 상태**: ❌ 로드되지 않음 (DB 전용 모드)"""
        
        return f'''#!/usr/bin/env python3
"""
변수 정의 모듈 (VariableDefinitions) - DB 중심 자동 생성
====================================================

⚠️  **이 파일은 자동 생성됩니다. 직접 편집하지 마세요!**

🎯 **DB 중심 워크플로우**:
1. tv_trading_variables, tv_variable_parameters 테이블 수정
2. GUI의 DB → Code 동기화 탭에서 동기화 실행
3. 생성된 파일 검토 및 배포

🔄 **마지막 동기화**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
📊 **지표 통계**: 활성 {total_indicators}개 / 총 파라미터 {total_parameters}개{data_info_status}

🚀 **향후 계획**: data_info → DB 마이그레이션으로 완전한 DB 중심화
"""'''
    
    def _generate_imports(self) -> str:
        """import 문 생성"""
        return '''
from typing import Dict, Any, List, Optional

# 호환성 검증기 import (shared 폴더)
try:
    from ..shared.compatibility_validator import CompatibilityValidator
    COMPATIBILITY_VALIDATOR_AVAILABLE = True
    print("✅ 통합 호환성 검증기 로드 성공")
except ImportError as e:
    print(f"⚠️ 통합 호환성 검증기 로드 실패: {e}")
    COMPATIBILITY_VALIDATOR_AVAILABLE = False
'''
    
    def _generate_class_declaration(self) -> str:
        """클래스 선언부 생성"""
        return '''

class VariableDefinitions:
    """트레이딩 변수들의 파라미터 정의를 관리하는 클래스 (DB 중심 자동 생성)"""
'''
    
    def _generate_chart_categories(self) -> str:
        """CHART_CATEGORIES 딕셔너리 생성"""
        lines = ["    # 📊 차트 카테고리 매핑 (DB 중심)"]
        lines.append("    CHART_CATEGORIES = {")
        
        for indicator_id in sorted(self.chart_categories.keys()):
            chart_category = self.chart_categories[indicator_id]
            display_name = self.indicators.get(indicator_id, {}).get("display_name_ko", indicator_id)
            lines.append(f'        "{indicator_id}": "{chart_category}",  # {display_name}')
        
        lines.append("    }")
        lines.append("")
        return "\n".join(lines)
    
    def _generate_parameters_method(self) -> str:
        """get_variable_parameters 메서드 생성"""
        lines = ["    @staticmethod"]
        lines.append("    def get_variable_parameters(variable_id: str) -> Dict[str, Any]:")
        lines.append('        """지표별 파라미터 정보 반환 (DB 기반)"""')
        lines.append("        parameters = {")
        
        for indicator_id in sorted(self.indicators.keys()):
            info = self.indicators[indicator_id]
            if not info.get("parameters"):
                continue
                
            lines.append(f'            "{indicator_id}": {{')
            
            # 파라미터들을 display_order로 정렬
            params = info["parameters"]
            sorted_params = sorted(params.items(), key=lambda x: x[1].get("display_order", 0))
            
            for param_name, param_info in sorted_params:
                param_dict_parts = []
                
                # 기본 정보
                param_dict_parts.append(f'"type": "{param_info.get("type", "str")}"')
                
                default_val = param_info.get("default")
                if isinstance(default_val, str):
                    param_dict_parts.append(f'"default": "{default_val}"')
                else:
                    param_dict_parts.append(f'"default": {default_val}')
                
                param_dict_parts.append(f'"label": "{param_info.get("label", param_name)}"')
                
                # 범위 정보
                if "min" in param_info:
                    param_dict_parts.append(f'"min": {param_info["min"]}')
                if "max" in param_info:
                    param_dict_parts.append(f'"max": {param_info["max"]}')
                
                # enum 옵션
                if "options" in param_info:
                    options_str = json.dumps(param_info["options"], ensure_ascii=False)
                    param_dict_parts.append(f'"options": {options_str}')
                
                # 도움말
                help_text = param_info.get("description", f"{param_name} 설정")
                param_dict_parts.append(f'"help": "{help_text}"')
                
                param_dict_str = "{" + ", ".join(param_dict_parts) + "}"
                lines.append(f'                "{param_name}": {param_dict_str},')
            
            lines.append("            },")
        
        lines.append("        }")
        lines.append("        return parameters.get(variable_id, {})")
        lines.append("")
        return "\n".join(lines)
    
    def _generate_descriptions_method(self) -> str:
        """get_variable_descriptions 메서드 생성"""
        lines = ["    @staticmethod"]
        lines.append("    def get_variable_descriptions() -> Dict[str, str]:")
        lines.append('        """변수별 설명 반환 (DB 기반)"""')
        lines.append("        return {")
        
        for indicator_id in sorted(self.indicators.keys()):
            info = self.indicators[indicator_id]
            description = info.get("description", f"{info.get('display_name_ko', indicator_id)} 지표")
            # 따옴표 이스케이프
            description = description.replace('"', '\\"').replace('\n', ' ')
            lines.append(f'            "{indicator_id}": "{description}",')
        
        lines.append("        }")
        lines.append("")
        return "\n".join(lines)
    
    def _generate_category_method(self) -> str:
        """get_category_variables 메서드 생성"""
        lines = ["    @staticmethod"]
        lines.append("    def get_category_variables() -> Dict[str, List[tuple]]:")
        lines.append('        """카테고리별 변수 목록 반환 (DB 기반)"""')
        lines.append("        return {")
        
        for category in sorted(self.categories.keys()):
            indicators_list = self.categories[category]
            lines.append(f'            "{category}": [')
            
            for indicator_id, display_name in sorted(indicators_list):
                lines.append(f'                ("{indicator_id}", "{display_name}"),')
            
            lines.append("            ],")
        
        lines.append("        }")
        lines.append("")
        return "\n".join(lines)
    
    def _generate_placeholders_method(self) -> str:
        """get_variable_placeholders 메서드 생성"""
        lines = ["    @staticmethod"]
        lines.append("    def get_variable_placeholders() -> Dict[str, Dict[str, str]]:")
        lines.append('        """지표별 사용 예시 및 플레이스홀더"""')
        lines.append("        placeholders = {")
        
        for indicator_id in sorted(self.indicators.keys()):
            info = self.indicators[indicator_id]
            display_name = info.get("display_name_ko", indicator_id)
            
            # data_info에서 플레이스홀더 정보 가져오기
            data_info_placeholders = {}
            if (self.data_info and 
                indicator_id in self.data_info.get('placeholder_texts', {}).get('indicators', {})):
                data_info_placeholders = self.data_info['placeholder_texts']['indicators'][indicator_id]
            
            lines.append(f'            "{indicator_id}": {{')
            lines.append(f'                "basic_usage": "{data_info_placeholders.get("basic_usage", f"{display_name} 기본 설정으로 매매 신호 생성")}",')
            lines.append(f'                "advanced_usage": "{data_info_placeholders.get("advanced_usage", f"{display_name} 고급 설정으로 정밀한 분석")}",')
            
            # 시나리오 정보가 있다면 추가
            if 'scenarios' in data_info_placeholders:
                lines.append('                "scenarios": {')
                for scenario_name, scenario_desc in data_info_placeholders['scenarios'].items():
                    lines.append(f'                    "{scenario_name}": "{scenario_desc}",')
                lines.append('                },')
            
            lines.append("            },")
        
        lines.append("        }")
        lines.append("        return placeholders")
        lines.append("")
        return "\n".join(lines)
    
    def _generate_help_text_method(self) -> str:
        """get_variable_help_text 메서드 생성"""
        lines = ["    @staticmethod"]
        lines.append("    def get_variable_help_text(variable_id: str, parameter_name: str = None) -> str:")
        lines.append('        """지표별 상세 도움말 텍스트"""')
        lines.append("        help_texts = {")
        
        for indicator_id in sorted(self.indicators.keys()):
            info = self.indicators[indicator_id]
            lines.append(f'            "{indicator_id}": {{')
            lines.append(f'                "overview": "{info.get("description", f"{info.get("display_name_ko", indicator_id)} 지표")}",')
            
            # data_info에서 추가 정보 가져오기
            if (self.data_info and 
                indicator_id in self.data_info.get('indicator_library', {}).get('indicators', {})):
                lib_info = self.data_info['indicator_library']['indicators'][indicator_id]
                
                if 'interpretation' in lib_info:
                    interp = lib_info['interpretation']
                    lines.append('                "interpretation": {')
                    for key, value in interp.items():
                        lines.append(f'                    "{key}": "{value}",')
                    lines.append('                },')
                
                if 'trading_signals' in lib_info:
                    signals = lib_info['trading_signals']
                    signals_str = ' | '.join(signals) if isinstance(signals, list) else str(signals)
                    lines.append(f'                "trading_signals": "{signals_str}",')
            
            # 파라미터 도움말
            if info.get("parameters"):
                lines.append('                "parameters": {')
                for param_name, param_info in info["parameters"].items():
                    help_text = param_info.get("description", f"{param_name} 설정")
                    lines.append(f'                    "{param_name}": "{help_text}",')
                lines.append('                },')
            
            lines.append("            },")
        
        lines.append("        }")
        lines.append("")
        lines.append("        if variable_id not in help_texts:")
        lines.append('            return f"지표 {variable_id}에 대한 도움말이 준비되지 않았습니다."')
        lines.append("")
        lines.append("        var_help = help_texts[variable_id]")
        lines.append("        if parameter_name:")
        lines.append('            return var_help.get("parameters", {}).get(parameter_name, f"파라미터 {parameter_name}에 대한 도움말이 없습니다.")')
        lines.append("        else:")
        lines.append('            return var_help.get("overview", "도움말이 없습니다.")')
        lines.append("")
        return "\n".join(lines)
    
    def _generate_utility_methods(self) -> str:
        """유틸리티 메서드들 생성"""
        return '''    @classmethod
    def get_chart_category(cls, variable_id: str) -> str:
        """변수 ID의 차트 카테고리 반환 (overlay or subplot)"""
        return cls.CHART_CATEGORIES.get(variable_id, "subplot")
    
    @classmethod
    def is_overlay_indicator(cls, variable_id: str) -> bool:
        """오버레이 지표인지 확인"""
        return cls.get_chart_category(variable_id) == "overlay"
    
    @staticmethod
    def get_variable_category(variable_id: str) -> str:
        """변수 ID로부터 카테고리 찾기"""
        category_variables = VariableDefinitions.get_category_variables()
        
        for category, variables in category_variables.items():
            for var_id, var_name in variables:
                if var_id == variable_id:
                    return category
        
        return "custom"  # 기본값
    
    @staticmethod
    def check_variable_compatibility(var1_id: str, var2_id: str) -> tuple[bool, str]:
        """변수 간 호환성 검증 (통합 호환성 검증기 사용)"""
        try:
            if COMPATIBILITY_VALIDATOR_AVAILABLE:
                validator = CompatibilityValidator()
                is_compatible, score, reason = validator.validate_compatibility(var1_id, var2_id)
                reason_str = str(reason) if isinstance(reason, dict) else reason
                return is_compatible, reason_str
            else:
                # 폴백: 기본 카테고리 기반 검증
                cat1 = VariableDefinitions.get_variable_category(var1_id)
                cat2 = VariableDefinitions.get_variable_category(var2_id)
                
                if cat1 == cat2:
                    return True, f"같은 카테고리: {cat1}"
                else:
                    return False, f"다른 카테고리: {cat1} vs {cat2}"
            
        except Exception as e:
            print(f"⚠️ 호환성 검증 실패, 기본 방식 사용: {e}")
            
            # 폴백: 기본 카테고리 기반 검증
            cat1 = VariableDefinitions.get_variable_category(var1_id)
            cat2 = VariableDefinitions.get_variable_category(var2_id)
            
            if cat1 == cat2:
                return True, f"같은 카테고리: {cat1}"
            else:
                return False, f"다른 카테고리: {cat1} vs {cat2}"
    
    @staticmethod
    def get_available_indicators() -> Dict[str, Any]:
        """사용 가능한 모든 지표 목록 반환"""
        category_vars = VariableDefinitions.get_category_variables()
        all_indicators = []
        for variables in category_vars.values():
            all_indicators.extend([var_id for var_id, _ in variables])
        
        return {
            "core": all_indicators,
            "custom": [],
            "categories": list(category_vars.keys()),
            "total_count": len(all_indicators)
        }
    
    @staticmethod
    def get_indicator_metadata(variable_id: str) -> Dict[str, Any]:
        """지표의 메타데이터 정보 반환"""
        parameters = VariableDefinitions.get_variable_parameters(variable_id)
        descriptions = VariableDefinitions.get_variable_descriptions()
        category = VariableDefinitions.get_variable_category(variable_id)
        chart_category = VariableDefinitions.CHART_CATEGORIES.get(variable_id, "subplot")
        
        return {
            "variable_id": variable_id,
            "description": descriptions.get(variable_id, "설명 없음"),
            "category": category,
            "chart_category": chart_category,
            "parameters": parameters,
            "parameter_count": len(parameters),
            "has_help": bool(VariableDefinitions.get_variable_help_text(variable_id)),
        }
'''


# ===== 편의 함수들 =====

def generate_variable_definitions_file(db_data: Dict[str, Any], 
                                      output_path: str, 
                                      data_info: Dict[str, Any] = None) -> bool:
    """variable_definitions.py 파일 생성 편의 함수"""
    generator = VariableDefinitionsGenerator(db_data, data_info)
    return generator.save_to_file(output_path)

def create_safe_filename(base_dir: str, base_name: str = "variable_definitions_new") -> str:
    """안전한 파일명 생성 (항상 타임스탬프 포함)"""
    # 항상 타임스탬프가 포함된 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(base_dir, f"{base_name}_{timestamp}.py")
