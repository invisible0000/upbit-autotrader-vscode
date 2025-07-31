#!/usr/bin/env python3
"""
🚀 Unified Variable Definitions 코드 생성기 v2.0
===============================================

DB 데이터 + data_info 통합으로 완전한 variable_definitions.py 생성
하드코딩 제거 및 DB 중심 아키텍처 구현

주요 개선사항:
- DB에서 도움말 텍스트 로드
- DB에서 플레이스홀더 텍스트 로드  
- DB에서 지표 라이브러리 정보 로드
- 완전한 자동화 (data_info 의존성 제거)

작성일: 2025-07-30
버전: 2.0 (Unified)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import sqlite3


class UnifiedVariableDefinitionsGenerator:
    """통합 variable_definitions.py 파일 생성기 (DB 완전 통합)"""
    
    def __init__(self, db_path: str):
        """
        초기화
        
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self.db_data = {}
        self.help_texts = {}
        self.placeholder_texts = {}
        self.indicator_library = {}
        self.stats = {}
        
        # DB에서 모든 데이터 로드
        self._load_all_data()
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """DB 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _load_all_data(self):
        """DB에서 모든 필요한 데이터 로드"""
        with self._get_db_connection() as conn:
            self._load_indicators_data(conn)
            self._load_help_texts(conn)
            self._load_placeholder_texts(conn)
            self._load_indicator_library(conn)
            self._generate_stats()
    
    def _load_indicators_data(self, conn: sqlite3.Connection):
        """지표 데이터 로드"""
        self.db_data = {
            "indicators": {},
            "categories": {},
            "chart_categories": {}
        }
        
        # 지표 및 파라미터 로드
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                tv.variable_id,
                tv.display_name_ko,
                tv.display_name_en,
                tv.purpose_category,
                tv.chart_category,
                tv.description,
                tv.is_active
            FROM tv_trading_variables tv
            WHERE tv.is_active = 1
            ORDER BY tv.purpose_category, tv.variable_id
        """)
        
        indicators = {}
        for row in cursor.fetchall():
            variable_id = row['variable_id']
            indicators[variable_id] = {
                'display_name_ko': row['display_name_ko'],
                'display_name_en': row['display_name_en'], 
                'purpose_category': row['purpose_category'],
                'chart_category': row['chart_category'],
                'description': row['description'],
                'parameters': {}
            }
        
        # 파라미터 로드
        cursor.execute("""
            SELECT 
                variable_id,
                parameter_name,
                parameter_type,
                default_value,
                min_value,
                max_value,
                enum_values,
                display_name_ko,
                description
            FROM tv_variable_parameters
            ORDER BY variable_id, display_order
        """)
        
        for row in cursor.fetchall():
            variable_id = row['variable_id']
            if variable_id in indicators:
                param_name = row['parameter_name']
                indicators[variable_id]['parameters'][param_name] = {
                    'type': row['parameter_type'],
                    'default': row['default_value'],
                    'min': row['min_value'],
                    'max': row['max_value'],
                    'options': json.loads(row['enum_values']) if row['enum_values'] else None,
                    'label': row['display_name_ko'],
                    'help': row['description']
                }
        
        self.db_data['indicators'] = indicators
        
        # 카테고리 로드
        cursor.execute("SELECT category_id, category_name FROM tv_indicator_categories WHERE is_active = 1")
        categories = {}
        for row in cursor.fetchall():
            categories[row['category_id']] = row['category_name']
        self.db_data['categories'] = categories
        
        # 차트 카테고리 매핑 생성
        chart_categories = {}
        for variable_id, indicator in indicators.items():
            chart_categories[variable_id] = indicator['chart_category']
        self.db_data['chart_categories'] = chart_categories
    
    def _load_help_texts(self, conn: sqlite3.Connection):
        """도움말 텍스트 로드"""
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT help_key, help_text, variable_id, parameter_name
                FROM tv_help_texts
                WHERE language_code = 'ko'
                ORDER BY help_key
            """)
            
            for row in cursor.fetchall():
                key = row['help_key']
                text = row['help_text']
                variable_id = row['variable_id']
                parameter_name = row['parameter_name']
                
                # 계층적 구조로 저장
                if variable_id and parameter_name:
                    # 특정 지표의 특정 파라미터
                    if variable_id not in self.help_texts:
                        self.help_texts[variable_id] = {}
                    self.help_texts[variable_id][parameter_name] = text
                elif variable_id:
                    # 특정 지표 전체
                    if variable_id not in self.help_texts:
                        self.help_texts[variable_id] = {}
                    self.help_texts[variable_id]['_general'] = text
                else:
                    # 전역 도움말
                    self.help_texts[key] = text
                    
        except sqlite3.OperationalError:
            # 테이블이 없으면 빈 딕셔너리
            self.help_texts = {}
    
    def _load_placeholder_texts(self, conn: sqlite3.Connection):
        """플레이스홀더 텍스트 로드"""
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    variable_id,
                    placeholder_type,
                    placeholder_text,
                    scenario_order
                FROM tv_placeholder_texts
                WHERE language_code = 'ko'
                ORDER BY variable_id, placeholder_type, scenario_order
            """)
            
            for row in cursor.fetchall():
                variable_id = row['variable_id']
                placeholder_type = row['placeholder_type']
                text = row['placeholder_text']
                
                if variable_id not in self.placeholder_texts:
                    self.placeholder_texts[variable_id] = {}
                
                if placeholder_type == 'scenario':
                    # 시나리오는 리스트로 저장
                    if 'usage_scenarios' not in self.placeholder_texts[variable_id]:
                        self.placeholder_texts[variable_id]['usage_scenarios'] = []
                    self.placeholder_texts[variable_id]['usage_scenarios'].append(text)
                else:
                    # 기본 플레이스홀더들
                    self.placeholder_texts[variable_id][placeholder_type] = text
                    
        except sqlite3.OperationalError:
            self.placeholder_texts = {}
    
    def _load_indicator_library(self, conn: sqlite3.Connection):
        """지표 라이브러리 정보 로드"""
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    variable_id,
                    content_type,
                    content_ko,
                    reference_links,
                    examples
                FROM tv_indicator_library
                ORDER BY variable_id, content_order
            """)
            
            for row in cursor.fetchall():
                variable_id = row['variable_id']
                content_type = row['content_type']
                content = row['content_ko']
                
                if variable_id not in self.indicator_library:
                    self.indicator_library[variable_id] = {}
                
                self.indicator_library[variable_id][content_type] = content
                
                # 참고 링크 및 예시 추가
                if row['reference_links']:
                    try:
                        links = json.loads(row['reference_links'])
                        self.indicator_library[variable_id]['reference_links'] = links
                    except:
                        pass
                
                if row['examples']:
                    try:
                        examples = json.loads(row['examples'])
                        self.indicator_library[variable_id]['examples'] = examples
                    except:
                        pass
                        
        except sqlite3.OperationalError:
            self.indicator_library = {}
    
    def _generate_stats(self):
        """통계 정보 생성"""
        indicators = self.db_data.get('indicators', {})
        total_indicators = len(indicators)
        total_parameters = sum(len(ind.get('parameters', {})) for ind in indicators.values())
        
        # 카테고리별 통계
        category_stats = {}
        for indicator in indicators.values():
            category = indicator.get('purpose_category', 'unknown')
            category_stats[category] = category_stats.get(category, 0) + 1
        
        self.stats = {
            'total_indicators': total_indicators,
            'total_parameters': total_parameters,
            'categories': category_stats,
            'generation_time': datetime.now().isoformat()
        }
    
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
            self._generate_utility_methods(),
            self._generate_compatibility_methods()
        ]
        
        return '\n\n'.join(sections)
    
    def _generate_header(self) -> str:
        """파일 헤더 생성"""
        stats = self.stats
        indicators_count = stats.get('total_indicators', 0)
        parameters_count = stats.get('total_parameters', 0)
        generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f'''#!/usr/bin/env python3
"""
변수 정의 모듈 (VariableDefinitions) - Enhanced DB 중심 자동 생성 v2.0
====================================================================

⚠️  **이 파일은 향상된 시스템으로 자동 생성됩니다. 직접 편집하지 마세요!**

🎯 **Enhanced DB 중심 워크플로우 v2.0**:
1. data_info YAML → DB 마이그레이션 (고급 마이그레이션 도구)
2. DB에서 모든 데이터 통합 관리 (하드코딩 제거)
3. GUI의 Enhanced DB → Code 동기화 탭에서 동기화 실행
4. 완전 자동화된 variable_definitions.py 생성

🔄 **마지막 동기화**: {generation_time}
📊 **지표 통계**: 활성 {indicators_count}개 / 총 파라미터 {parameters_count}개
🗄️ **데이터 소스**: 
  ✅ tv_trading_variables: 지표 메타데이터
  ✅ tv_variable_parameters: 파라미터 정의
  ✅ tv_help_texts: 도움말 텍스트 ({len(self.help_texts)}개)
  ✅ tv_placeholder_texts: 플레이스홀더 ({len(self.placeholder_texts)}개)
  ✅ tv_indicator_library: 지표 라이브러리 ({len(self.indicator_library)}개)

🚀 **v2.0 개선사항**: 완전한 DB 통합, 하드코딩 제거, data_info 의존성 해결
"""

from typing import Dict, Any, List, Optional'''
    
    def _generate_imports(self) -> str:
        """import 섹션 생성"""
        return '''# 호환성 검증기 import (shared 폴더)
try:
    from ..shared.compatibility_validator import CompatibilityValidator
    COMPATIBILITY_VALIDATOR_AVAILABLE = True
    print("✅ 통합 호환성 검증기 로드 성공")
except ImportError as e:
    print(f"⚠️ 통합 호환성 검증기 로드 실패: {e}")
    COMPATIBILITY_VALIDATOR_AVAILABLE = False'''
    
    def _generate_class_declaration(self) -> str:
        """클래스 선언 생성"""
        return '''class VariableDefinitions:
    """트레이딩 변수들의 파라미터 정의를 관리하는 클래스 (Enhanced DB 중심 자동 생성 v2.0)"""'''
    
    def _generate_chart_categories(self) -> str:
        """차트 카테고리 매핑 생성"""
        chart_categories = self.db_data.get('chart_categories', {})
        
        categories_dict = {}
        for variable_id, category in chart_categories.items():
            # 지표 설명 추가
            indicator = self.db_data['indicators'].get(variable_id, {})
            description = indicator.get('display_name_ko', variable_id)
            categories_dict[variable_id] = f'"{category}",  # {description}'
        
        # 정렬
        sorted_items = sorted(categories_dict.items())
        
        lines = ['    # 📊 차트 카테고리 매핑 (Enhanced DB 중심)']
        lines.append('    CHART_CATEGORIES = {')
        
        for variable_id, line in sorted_items:
            lines.append(f'        "{variable_id}": {line}')
        
        lines.append('    }')
        
        return '\n'.join(lines)
    
    def _generate_parameters_method(self) -> str:
        """get_variable_parameters 메서드 생성"""
        indicators = self.db_data.get('indicators', {})
        
        lines = [
            '    @staticmethod',
            '    def get_variable_parameters(variable_id: str) -> Dict[str, Any]:',
            '        """지표별 파라미터 정보 반환 (Enhanced DB 기반)"""',
            '        parameters = {'
        ]
        
        for variable_id, indicator in sorted(indicators.items()):
            if not indicator.get('parameters'):
                continue
                
            lines.append(f'            "{variable_id}": {{')
            
            for param_name, param_info in indicator['parameters'].items():
                param_dict = self._format_parameter_dict(param_info)
                lines.append(f'                "{param_name}": {param_dict},')
            
            lines.append('            },')
        
        lines.extend([
            '        }',
            '        return parameters.get(variable_id, {})'
        ])
        
        return '\n'.join(lines)
    
    def _format_parameter_dict(self, param_info: Dict[str, Any]) -> str:
        """파라미터 딕셔너리 포맷팅"""
        parts = []
        
        # 기본 속성들
        if param_info.get('type'):
            parts.append(f'"type": "{param_info["type"]}"')
        if param_info.get('default'):
            parts.append(f'"default": {repr(param_info["default"])}')
        if param_info.get('label'):
            parts.append(f'"label": "{param_info["label"]}"')
        if param_info.get('min'):
            parts.append(f'"min": {param_info["min"]}')
        if param_info.get('max'):
            parts.append(f'"max": {param_info["max"]}')
        if param_info.get('help'):
            parts.append(f'"help": "{param_info["help"]}"')
        if param_info.get('options'):
            options_str = json.dumps(param_info['options'], ensure_ascii=False)
            parts.append(f'"options": {options_str}')
        
        return '{' + ', '.join(parts) + '}'
    
    def _generate_descriptions_method(self) -> str:
        """get_variable_descriptions 메서드 생성"""
        indicators = self.db_data.get('indicators', {})
        
        lines = [
            '    @staticmethod',
            '    def get_variable_descriptions() -> Dict[str, str]:',
            '        """변수별 설명 반환 (Enhanced DB 기반)"""',
            '        return {'
        ]
        
        for variable_id, indicator in sorted(indicators.items()):
            description = indicator.get('description', '')
            if description:
                lines.append(f'            "{variable_id}": "{description}",')
        
        lines.extend([
            '        }'
        ])
        
        return '\n'.join(lines)
    
    def _generate_category_method(self) -> str:
        """get_category_variables 메서드 생성"""
        indicators = self.db_data.get('indicators', {})
        
        # 카테고리별로 그룹화
        categories = {}
        for variable_id, indicator in indicators.items():
            category = indicator.get('purpose_category', 'unknown')
            display_name = indicator.get('display_name_ko', variable_id)
            
            if category not in categories:
                categories[category] = []
            categories[category].append((variable_id, display_name))
        
        lines = [
            '    @staticmethod',
            '    def get_category_variables() -> Dict[str, List[tuple]]:',
            '        """카테고리별 변수 목록 반환 (Enhanced DB 기반)"""',
            '        return {'
        ]
        
        for category, items in sorted(categories.items()):
            lines.append(f'            "{category}": [')
            for variable_id, display_name in sorted(items):
                lines.append(f'                ("{variable_id}", "{display_name}"),')
            lines.append('            ],')
        
        lines.extend([
            '        }'
        ])
        
        return '\n'.join(lines)
    
    def _generate_placeholders_method(self) -> str:
        """get_variable_placeholders 메서드 생성"""
        lines = [
            '    @staticmethod',
            '    def get_variable_placeholders() -> Dict[str, Dict[str, str]]:',
            '        """지표별 사용 예시 및 플레이스홀더 (Enhanced DB 기반)"""',
            '        placeholders = {'
        ]
        
        for variable_id, placeholder_data in sorted(self.placeholder_texts.items()):
            lines.append(f'            "{variable_id}": {{')
            
            # 기본 플레이스홀더들
            for key in ['target', 'name', 'description']:
                if key in placeholder_data:
                    value = placeholder_data[key].replace('"', '\\"')
                    lines.append(f'                "{key}": "{value}",')
            
            # 사용 시나리오들을 basic_usage와 advanced_usage로 변환
            scenarios = placeholder_data.get('usage_scenarios', [])
            if scenarios:
                if len(scenarios) >= 1:
                    basic = scenarios[0].replace('"', '\\"')
                    lines.append(f'                "basic_usage": "{basic}",')
                if len(scenarios) >= 2:
                    advanced = scenarios[1].replace('"', '\\"')
                    lines.append(f'                "advanced_usage": "{advanced}",')
            
            lines.append('            },')
        
        lines.extend([
            '        }',
            '        return placeholders'
        ])
        
        return '\n'.join(lines)
    
    def _generate_help_text_method(self) -> str:
        """get_variable_help_text 메서드 생성"""
        lines = [
            '    @staticmethod',
            '    def get_variable_help_text(variable_id: str, parameter_name: str = None) -> str:',
            '        """지표별 상세 도움말 텍스트 (Enhanced DB 기반)"""'
        ]
        
        if not self.help_texts:
            lines.extend([
                '        # 도움말 데이터가 없음',
                '        return ""'
            ])
            return '\n'.join(lines)
        
        lines.extend([
            '        help_data = {',
        ])
        
        # 지표별 도움말 데이터 생성
        for variable_id, help_info in sorted(self.help_texts.items()):
            if isinstance(help_info, dict):
                lines.append(f'            "{variable_id}": {{')
                for param_key, help_text in help_info.items():
                    escaped_text = help_text.replace('"', '\\"').replace('\n', '\\n')
                    lines.append(f'                "{param_key}": "{escaped_text}",')
                lines.append('            },')
        
        lines.extend([
            '        }',
            '',
            '        if variable_id in help_data:',
            '            var_help = help_data[variable_id]',
            '            if parameter_name and parameter_name in var_help:',
            '                return var_help[parameter_name]',
            '            elif "_general" in var_help:',
            '                return var_help["_general"]',
            '',
            '        return ""'
        ])
        
        return '\n'.join(lines)
    
    def _generate_utility_methods(self) -> str:
        """유틸리티 메서드들 생성"""
        return '''    @classmethod
    def get_chart_category(cls, variable_id: str) -> str:
        """지표의 차트 카테고리 반환 (Enhanced DB 기반)"""
        return cls.CHART_CATEGORIES.get(variable_id, "subplot")
    
    @classmethod
    def is_overlay_indicator(cls, variable_id: str) -> bool:
        """오버레이 지표 여부 확인 (Enhanced DB 기반)"""
        return cls.get_chart_category(variable_id) == "overlay"
    
    @staticmethod
    def get_variable_category(variable_id: str) -> str:
        """지표의 목적 카테고리 반환 (Enhanced DB 기반)"""
        categories = VariableDefinitions.get_category_variables()
        for category, variables in categories.items():
            for var_id, _ in variables:
                if var_id == variable_id:
                    return category
        return "unknown"'''
    
    def _generate_compatibility_methods(self) -> str:
        """호환성 관련 메서드들 생성"""
        return '''    @staticmethod
    def check_variable_compatibility(var1_id: str, var2_id: str) -> tuple[bool, str]:
        """두 지표 간 호환성 체크 (Enhanced DB 기반)"""
        # 기본 호환성 로직
        cat1 = VariableDefinitions.get_variable_category(var1_id)
        cat2 = VariableDefinitions.get_variable_category(var2_id)
        
        # 동일 카테고리는 호환 가능
        if cat1 == cat2:
            return True, "동일 카테고리 지표로 호환 가능"
        
        # 가격 관련 지표들은 서로 호환 가능
        price_categories = {'price', 'trend', 'volatility'}
        if cat1 in price_categories and cat2 in price_categories:
            return True, "가격 관련 지표들로 호환 가능"
        
        return False, f"서로 다른 카테고리 ({cat1} vs {cat2})로 호환되지 않음"
    
    @staticmethod
    def get_available_indicators() -> Dict[str, Any]:
        """사용 가능한 모든 지표 정보 반환 (Enhanced DB 기반)"""
        categories = VariableDefinitions.get_category_variables()
        descriptions = VariableDefinitions.get_variable_descriptions()
        
        result = {}
        for category, variables in categories.items():
            result[category] = []
            for var_id, display_name in variables:
                result[category].append({
                    'id': var_id,
                    'name': display_name,
                    'description': descriptions.get(var_id, ''),
                    'chart_category': VariableDefinitions.get_chart_category(var_id),
                    'parameters': VariableDefinitions.get_variable_parameters(var_id)
                })
        
        return result
    
    @staticmethod
    def get_indicator_metadata(variable_id: str) -> Dict[str, Any]:
        """특정 지표의 메타데이터 반환 (Enhanced DB 기반)"""
        descriptions = VariableDefinitions.get_variable_descriptions()
        
        return {
            'id': variable_id,
            'category': VariableDefinitions.get_variable_category(variable_id),
            'chart_category': VariableDefinitions.get_chart_category(variable_id),
            'description': descriptions.get(variable_id, ''),
            'parameters': VariableDefinitions.get_variable_parameters(variable_id),
            'is_overlay': VariableDefinitions.is_overlay_indicator(variable_id)
        }'''


def generate_enhanced_variable_definitions(db_path: str, output_path: str = None) -> str:
    """
    향상된 variable_definitions.py 파일 생성
    
    Args:
        db_path: 데이터베이스 파일 경로
        output_path: 출력 파일 경로 (None이면 내용만 반환)
    
    Returns:
        생성된 파일 내용
    """
    generator = UnifiedVariableDefinitionsGenerator(db_path)
    content = generator.generate_file_content()
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Enhanced variable_definitions.py 생성 완료: {output_path}")
    
    return content


def main():
    """테스트 실행"""
    import sys
    from pathlib import Path
    
    if len(sys.argv) < 2:
        print("사용법: python unified_code_generator.py <db_path> [output_path]")
        return
    
    db_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(db_path).exists():
        print(f"❌ DB 파일을 찾을 수 없습니다: {db_path}")
        return
    
    print(f"🚀 Enhanced Variable Definitions 생성 시작...")
    print(f"📄 DB 경로: {db_path}")
    
    try:
        content = generate_enhanced_variable_definitions(db_path, output_path)
        
        if not output_path:
            print("\n" + "="*60)
            print("📋 생성된 내용 미리보기 (처음 1000자):")
            print("="*60)
            print(content[:1000])
            if len(content) > 1000:
                print("... (생략)")
        
        print(f"\n✅ 처리 완료! (총 {len(content):,}자)")
        
    except Exception as e:
        print(f"❌ 생성 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
