#!/usr/bin/env python3
"""
간단한 DB → variable_definitions.py 동기화 시스템
==============================================

🎯 **목적**: 복잡한 trading_variables 시스템 대신 단순한 2단계 접근
1. DB 직접 편집 (LLM 에이전트 또는 수동)
2. 자동으로 variable_definitions.py 생성

🔧 **사용법**:
    python sync_db_to_code.py
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class DBToCodeSynchronizer:
    """DB 내용을 variable_definitions.py로 동기화하는 단순한 도구"""
    
    def __init__(self, db_path: str = "upbit_auto_trading/data/settings.sqlite3"):
        self.db_path = db_path
        self.script_dir = Path(__file__).parent  # 스크립트가 있는 폴더
        self.variable_definitions_path = self._generate_safe_filename()
    
    def _generate_safe_filename(self) -> str:
        """안전한 파일명 생성 (기존 파일 덮어쓰기 방지)"""
        base_name = "variable_definitions_new"
        
        # 기본 파일명 시도
        basic_path = self.script_dir / f"{base_name}.py"
        if not basic_path.exists():
            return str(basic_path)
        
        # 기존 파일이 있으면 날짜시간 suffix 추가
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_path = self.script_dir / f"{base_name}_{timestamp}.py"
        return str(timestamped_path)
    
    def sync_all(self) -> bool:
        """DB → variable_definitions.py 전체 동기화"""
        try:
            print("🔄 DB → variable_definitions.py 동기화 시작...")
            print(f"📁 스크립트 위치: {self.script_dir}")
            print(f"🎯 생성될 파일: {self.variable_definitions_path}")
            print(f"💾 DB 경로: {self.db_path}")
            
            # 1. DB에서 모든 지표 정보 읽기
            indicators = self._load_indicators_from_db()
            print(f"📊 DB에서 {len(indicators)}개 지표 로드됨")
            
            # 2. variable_definitions.py 파일 생성
            self._generate_variable_definitions_file(indicators)
            print(f"✅ variable_definitions.py 생성 완료: {Path(self.variable_definitions_path).name}")
            
            # 3. 검증 보고서 생성
            report = self._generate_sync_report(indicators)
            print("\n📋 동기화 보고서:")
            print(report)
            
            return True
            
        except Exception as e:
            print(f"❌ 동기화 실패: {e}")
            return False
    
    def _load_indicators_from_db(self) -> Dict[str, Any]:
        """DB에서 모든 지표 정보 로드"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        indicators = {}
        
        # 지표 기본 정보 로드
        cursor.execute("""
            SELECT variable_id, display_name_ko, display_name_en, 
                   purpose_category, chart_category, comparison_group, description
            FROM tv_trading_variables 
            WHERE is_active = 1
            ORDER BY variable_id
        """)
        
        for row in cursor.fetchall():
            indicator_id = row["variable_id"]
            indicators[indicator_id] = {
                "display_name_ko": row["display_name_ko"] or "",
                "display_name_en": row["display_name_en"] or "",
                "purpose_category": row["purpose_category"] or "momentum",
                "chart_category": row["chart_category"] or "subplot",
                "comparison_group": row["comparison_group"] or "percentage_comparable",
                "description": row["description"] or f"{row['display_name_ko']} 지표",
                "parameters": {}
            }
        
        # 각 지표의 파라미터 정보 로드
        for indicator_id in indicators.keys():
            cursor.execute("""
                SELECT parameter_name, parameter_type, default_value,
                       min_value, max_value, enum_values, display_name_ko, description
                FROM tv_variable_parameters
                WHERE variable_id = ? 
                ORDER BY display_order
            """, (indicator_id,))
            
            parameters = {}
            for param_row in cursor.fetchall():
                param_name = param_row["parameter_name"]
                param_info = {
                    "label": param_row["display_name_ko"] or param_name,
                    "type": self._convert_param_type(param_row["parameter_type"]),
                    "default": self._convert_default_value(param_row["default_value"], param_row["parameter_type"]),
                    "help": param_row["description"] or f"{param_row['display_name_ko']} 설정"
                }
                
                # 숫자형 파라미터의 범위 추가
                if param_row["parameter_type"] in ["integer", "float"]:
                    if param_row["min_value"]:
                        try:
                            param_info["min"] = int(param_row["min_value"]) if param_row["parameter_type"] == "integer" else float(param_row["min_value"])
                        except:
                            pass
                    if param_row["max_value"]:
                        try:
                            param_info["max"] = int(param_row["max_value"]) if param_row["parameter_type"] == "integer" else float(param_row["max_value"])
                        except:
                            pass
                
                # enum 타입의 옵션 추가
                if param_row["parameter_type"] == "enum" and param_row["enum_values"]:
                    try:
                        param_info["options"] = json.loads(param_row["enum_values"])
                    except:
                        param_info["options"] = ["옵션1", "옵션2"]
                
                parameters[param_name] = param_info
            
            indicators[indicator_id]["parameters"] = parameters
        
        conn.close()
        return indicators
    
    def _convert_param_type(self, db_type: str) -> str:
        """DB 파라미터 타입을 variable_definitions.py 형식으로 변환"""
        type_mapping = {
            "integer": "int",
            "float": "float", 
            "string": "str",
            "boolean": "bool",
            "enum": "enum"
        }
        return type_mapping.get(db_type, "str")
    
    def _convert_default_value(self, default_str: str, param_type: str):
        """DB 기본값을 적절한 Python 타입으로 변환"""
        if not default_str:
            return None
        
        try:
            if param_type == "integer":
                return int(default_str)
            elif param_type == "float":
                return float(default_str)
            elif param_type == "boolean":
                return default_str.lower() in ["true", "1", "yes"]
            else:
                return default_str
        except:
            return default_str
    
    def _generate_variable_definitions_file(self, indicators: Dict[str, Any]):
        """variable_definitions.py 파일 전체 생성"""
        
        # 파일 헤더
        header = '''#!/usr/bin/env python3
"""
변수 정의 모듈 (VariableDefinitions) - DB 동기화 자동 생성
==================================================

⚠️  **이 파일은 자동 생성됩니다. 직접 편집하지 마세요!**
📝 **편집하려면**: data/app_settings.sqlite3의 tv_trading_variables 테이블을 수정 후 sync_db_to_code.py 실행

🔄 **마지막 동기화**: {datetime}
📊 **총 지표 수**: {total_indicators}개

🎯 **새로운 지표 추가 워크플로우**:
1. tv_trading_variables 테이블에 지표 추가
2. tv_variable_parameters 테이블에 파라미터 추가
3. python sync_db_to_code.py 실행하여 이 파일 자동 생성
"""

from typing import Dict, Any

# 호환성 검증기 import (shared 폴더)
try:
    from ..shared.compatibility_validator import CompatibilityValidator
    COMPATIBILITY_VALIDATOR_AVAILABLE = True
    print("✅ 통합 호환성 검증기 로드 성공 (trigger_builder/components)")
except ImportError as e:
    print(f"⚠️ 통합 호환성 검증기 로드 실패: {{e}}")
    COMPATIBILITY_VALIDATOR_AVAILABLE = False


class VariableDefinitions:
    """트레이딩 변수들의 파라미터 정의를 관리하는 클래스 (DB 동기화)"""
    
'''.format(
    datetime=self._get_current_datetime(),
    total_indicators=len(indicators)
)
        
        # CHART_CATEGORIES 생성
        chart_categories = self._generate_chart_categories(indicators)
        
        # get_variable_parameters 메서드 생성
        parameters_method = self._generate_parameters_method(indicators)
        
        # get_variable_descriptions 메서드 생성
        descriptions_method = self._generate_descriptions_method(indicators)
        
        # get_category_variables 메서드 생성
        category_method = self._generate_category_method(indicators)
        
        # 클래스 메서드들 생성
        class_methods = '''
    @classmethod
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
            "custom": []
        }
'''
        
        # 전체 파일 내용 조합
        full_content = header + chart_categories + parameters_method + descriptions_method + category_method + class_methods
        
        # 파일 저장
        with open(self.variable_definitions_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
    
    def _generate_chart_categories(self, indicators: Dict[str, Any]) -> str:
        """CHART_CATEGORIES 딕셔너리 생성"""
        lines = ["    # 📊 차트 카테고리 매핑 (DB 동기화)"]
        lines.append("    CHART_CATEGORIES = {")
        
        for indicator_id, info in sorted(indicators.items()):
            chart_cat = info["chart_category"]
            lines.append(f'        "{indicator_id}": "{chart_cat}",')
        
        lines.append("    }")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_parameters_method(self, indicators: Dict[str, Any]) -> str:
        """get_variable_parameters 메서드 생성"""
        lines = ["    @staticmethod"]
        lines.append("    def get_variable_parameters(var_id: str) -> Dict[str, Any]:")
        lines.append('        """변수별 파라미터 정의 반환 (DB 동기화)"""')
        lines.append("        params = {")
        
        for indicator_id, info in sorted(indicators.items()):
            if info["parameters"]:
                lines.append(f'            "{indicator_id}": {{')
                
                for param_name, param_info in info["parameters"].items():
                    lines.append(f'                "{param_name}": {{')
                    for key, value in param_info.items():
                        if isinstance(value, str):
                            value = value.replace('"', '\\"')  # 이스케이프 처리
                            lines.append(f'                    "{key}": "{value}",')
                        elif isinstance(value, list):
                            lines.append(f'                    "{key}": {value},')
                        else:
                            lines.append(f'                    "{key}": {value},')
                    lines.append("                },")
                
                lines.append("            },")
        
        lines.append("        }")
        lines.append("")
        lines.append("        return params.get(var_id, {})")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_descriptions_method(self, indicators: Dict[str, Any]) -> str:
        """get_variable_descriptions 메서드 생성"""
        lines = ["    @staticmethod"]
        lines.append("    def get_variable_descriptions() -> Dict[str, str]:")
        lines.append('        """변수별 설명 반환 (DB 동기화)"""')
        lines.append("        return {")
        
        for indicator_id, info in sorted(indicators.items()):
            description = info["description"] or f"{info['display_name_ko']} 지표"
            # 따옴표 이스케이프
            description = description.replace('"', '\\"')
            lines.append(f'            "{indicator_id}": "{description}",')
        
        lines.append("        }")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_category_method(self, indicators: Dict[str, Any]) -> str:
        """get_category_variables 메서드 생성"""
        # 카테고리별로 지표 그룹화
        categories = {}
        for indicator_id, info in indicators.items():
            category = info["purpose_category"]
            if category not in categories:
                categories[category] = []
            categories[category].append((indicator_id, info["display_name_ko"]))
        
        lines = ["    @staticmethod"]
        lines.append("    def get_category_variables() -> Dict[str, list]:")
        lines.append('        """카테고리별 변수 목록 반환 (DB 동기화)"""')
        lines.append("        return {")
        
        for category, indicators_list in sorted(categories.items()):
            lines.append(f'            "{category}": [')
            for indicator_id, display_name in sorted(indicators_list):
                lines.append(f'                ("{indicator_id}", "{display_name}"),')
            lines.append("            ],")
        
        lines.append("        }")
        lines.append("")
        
        return "\n".join(lines)
    
    def _get_current_datetime(self) -> str:
        """현재 시간 문자열 반환"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _generate_sync_report(self, indicators: Dict[str, Any]) -> str:
        """동기화 보고서 생성"""
        total_indicators = len(indicators)
        
        # 카테고리별 통계
        categories = {}
        chart_positions = {}
        
        for info in indicators.values():
            category = info["purpose_category"]
            chart_pos = info["chart_category"]
            
            categories[category] = categories.get(category, 0) + 1
            chart_positions[chart_pos] = chart_positions.get(chart_pos, 0) + 1
        
        report_lines = [
            f"총 지표 수: {total_indicators}개",
            "",
            "📊 카테고리별 분포:",
        ]
        
        for category, count in sorted(categories.items()):
            report_lines.append(f"  - {category}: {count}개")
        
        report_lines.extend([
            "",
            "🎨 차트 위치별 분포:",
        ])
        
        for position, count in sorted(chart_positions.items()):
            report_lines.append(f"  - {position}: {count}개")
        
        return "\n".join(report_lines)


def main():
    """메인 실행 함수"""
    print("🔄 DB → variable_definitions.py 동기화 도구")
    print("=" * 50)
    
    synchronizer = DBToCodeSynchronizer()
    success = synchronizer.sync_all()
    
    if success:
        filename = Path(synchronizer.variable_definitions_path).name
        full_path = synchronizer.variable_definitions_path
        
        print("\n✅ 동기화 완료!")
        print(f"📁 생성된 파일: {filename}")
        print(f"🎯 전체 경로: {full_path}")
        print("\n🔍 다음 단계:")
        print(f"1. {filename} 파일 내용 확인")
        print("2. 기존 variable_definitions.py와 비교")
        print("3. 문제없으면 기존 파일 백업 후 교체")
        print("4. python run_desktop_ui.py로 테스트")
        print("5. 정상 동작 확인 후 git commit")
        
        print("\n⚠️  주의사항:")
        print("- 기존 variable_definitions.py 파일들은 자동으로 변경되지 않습니다")
        print("- 수동으로 검토 후 안전하게 교체하세요")
        
    else:
        print("\n❌ 동기화 실패! 로그를 확인해주세요.")


if __name__ == "__main__":
    main()
