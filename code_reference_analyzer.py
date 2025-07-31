#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
코드 참조 분석 도구
위험도가 높은 테이블들을 참조하는 Python 파일들을 찾아서 영향도를 분석합니다.

Usage:
    python code_reference_analyzer.py
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict


class CodeReferenceAnalyzer:
    """코드 참조 분석 클래스"""
    
    def __init__(self, project_root: str = "upbit_auto_trading"):
        self.project_root = Path(project_root)
        self.results = {}
        self.log_file = None
        
        # 위험도별 테이블 분류 (실제 DB 분석 결과 기반)
        self.critical_tables_with_data = {
            'strategies', 'strategy_components', 'system_settings'
        }
        
        self.critical_tables_structure_needed = {
            'app_settings', 'strategy_conditions', 'strategy_execution'
        }
        
        self.important_tables_with_data = {
            'chart_layout_templates', 'chart_variables', 'trading_conditions'
        }
        
        self.important_tables_no_data = {
            'backup_info', 'execution_history'
        }
        
        # 모든 위험 테이블들 (TV 시스템 제외)
        self.all_risk_tables = (
            self.critical_tables_with_data | 
            self.critical_tables_structure_needed |
            self.important_tables_with_data |
            self.important_tables_no_data
        )
        
        # 검색 패턴들
        self.search_patterns = {
            'table_name': r'\b{table}\b',                    # 테이블명 직접 참조
            'sql_select': r'SELECT.*FROM\s+{table}\b',       # SELECT 쿼리
            'sql_insert': r'INSERT\s+INTO\s+{table}\b',      # INSERT 쿼리
            'sql_update': r'UPDATE\s+{table}\s+SET',         # UPDATE 쿼리
            'sql_delete': r'DELETE\s+FROM\s+{table}\b',      # DELETE 쿼리
            'create_table': r'CREATE\s+TABLE.*{table}\b',    # CREATE TABLE
            'string_literal': r'["\'{table}\"\']\s*[,)]',   # 문자열 리터럴
        }
        
    def setup_logging(self, log_file: str = "tools/code_reference_analysis.log"):
        """로깅 설정"""
        self.log_file = log_file
        # 로그 파일 초기화
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("코드 참조 분석 로그\n")
            f.write("="*80 + "\n")
    
    def log_and_print(self, message: str):
        """콘솔 출력과 파일 로깅을 동시에"""
        print(message)
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(message + "\n")
    
    def get_python_files(self) -> List[Path]:
        """프로젝트 내 모든 Python 파일 목록 조회"""
        python_files = []
        
        # 제외할 디렉토리들
        exclude_dirs = {
            '__pycache__', '.git', '.vscode', 'node_modules',
            'venv', 'env', '.pytest_cache', 'logs', 'tests',
            '.venv', 'dist', 'build', 'tools'
        }
        
        for root, dirs, files in os.walk(self.project_root):
            # 제외 디렉토리 필터링
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
                    
        return python_files
    
    def search_table_references(self, file_path: Path, table_name: str) -> Dict[str, List[Dict]]:
        """특정 파일에서 테이블 참조 검색 - 함수/메서드명 추출 포함"""
        references = defaultdict(list)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            for pattern_name, pattern_template in self.search_patterns.items():
                # 테이블명을 패턴에 삽입
                pattern = pattern_template.format(table=table_name)
                
                # 케이스 무시하고 검색
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    # 매치된 위치의 라인 번호 찾기
                    line_start = content.rfind('\n', 0, match.start()) + 1
                    line_num = content[:match.start()].count('\n') + 1
                    line_end = content.find('\n', match.end())
                    if line_end == -1:
                        line_end = len(content)
                    
                    matched_line = content[line_start:line_end].strip()
                    
                    # 함수/메서드명 추출
                    function_name = self.extract_function_name(content, match.start())
                    
                    references[pattern_name].append({
                        'line_number': line_num,
                        'matched_text': match.group(),
                        'full_line': matched_line,
                        'function_name': function_name,
                        'table_accessed': table_name,
                        'start_pos': match.start(),
                        'end_pos': match.end()
                    })
                    
        except Exception as e:
            print(f"⚠️ 파일 읽기 오류 {file_path}: {e}")
            
        return dict(references)
    
    def extract_function_name(self, content: str, position: int) -> str:
        """참조 위치에서 해당하는 함수/메서드명을 추출"""
        try:
            # 현재 위치에서 역방향으로 함수 정의를 찾기
            lines_before = content[:position].split('\n')
            
            for i in range(len(lines_before) - 1, -1, -1):
                line = lines_before[i].strip()
                
                # 함수/메서드 정의 패턴 매칭
                func_patterns = [
                    r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',  # def function_name(
                    r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',  # class ClassName(
                    r'async\s+def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',  # async def function_name(
                ]
                
                for pattern in func_patterns:
                    match = re.search(pattern, line)
                    if match:
                        return match.group(1)
                
                # 들여쓰기가 0이 되면 모듈 레벨 (함수 밖)
                if line and not line.startswith(' ') and not line.startswith('\t'):
                    keywords = ['def ', 'class ', 'async def ', '#', 'import ', 'from ']
                    if not any(line.startswith(keyword) for keyword in keywords):
                        break
            
            return "<module_level>"
            
        except Exception:
            return "<unknown>"
    
    def analyze_table_usage(self, table_name: str) -> Dict[str, any]:
        """특정 테이블의 사용 현황 분석"""
        self.log_and_print(f"\n🔍 '{table_name}' 테이블 참조 분석 중...")
        
        python_files = self.get_python_files()
        table_usage = {
            'table_name': table_name,
            'total_files_checked': len(python_files),
            'files_with_references': {},
            'total_references': 0,
            'reference_summary': defaultdict(int)
        }
        
        for file_path in python_files:
            references = self.search_table_references(file_path, table_name)
            
            if references:
                rel_path = file_path.relative_to(self.project_root)
                table_usage['files_with_references'][str(rel_path)] = references
                
                # 참조 통계 업데이트
                for pattern_name, matches in references.items():
                    count = len(matches)
                    table_usage['reference_summary'][pattern_name] += count
                    table_usage['total_references'] += count
        
        return table_usage
    
    def categorize_risk_level(self, table_name: str) -> str:
        """테이블의 위험도 레벨 반환"""
        if table_name in self.critical_tables_with_data:
            return "🔴 CRITICAL (데이터 있음)"
        elif table_name in self.critical_tables_structure_needed:
            return "🟠 CRITICAL (구조 필요)"
        elif table_name in self.important_tables_with_data:
            return "🟡 IMPORTANT (데이터 있음)"
        elif table_name in self.important_tables_no_data:
            return "🟨 IMPORTANT (데이터 없음)"
        else:
            return "⚪ UNKNOWN"
    
    def generate_human_friendly_report(self, all_results: Dict[str, Dict]) -> None:
        """사람이 읽기 좋은 간결한 보고서 생성"""
        self.log_and_print("\n" + "=" * 80)
        self.log_and_print("📊 코드 참조 분석 보고서 (사람용)")
        self.log_and_print("=" * 80)
        
        # 위험도별 정렬
        sorted_tables = sorted(
            all_results.items(),
            key=lambda x: (
                len(x[1]['files_with_references']),  # 참조 파일 수
                x[1]['total_references']             # 총 참조 수
            ),
            reverse=True
        )
        
        for table_name, usage_data in sorted_tables:
            risk_level = self.categorize_risk_level(table_name)
            files_count = len(usage_data['files_with_references'])
            ref_count = usage_data['total_references']
            
            self.log_and_print(f"\n{risk_level}")
            self.log_and_print(f"📦 테이블: {table_name}")
            self.log_and_print(f"📁 참조 파일 수: {files_count}개")
            self.log_and_print(f"🔗 총 참조 수: {ref_count}개")
            
            if files_count > 0:
                self.log_and_print("📋 참조 파일 목록:")
                
                # 파일별로 함수/메서드 정보 수집
                for file_path, references in usage_data['files_with_references'].items():
                    total_refs_in_file = sum(len(matches) for matches in references.values())
                    
                    # 함수/메서드별 정리
                    function_table_map = {}
                    for pattern_name, matches in references.items():
                        for match in matches:
                            func_name = match.get('function_name', '<unknown>')
                            table_accessed = match.get('table_accessed', table_name)
                            
                            if func_name not in function_table_map:
                                function_table_map[func_name] = set()
                            function_table_map[func_name].add(table_accessed)
                    
                    # 파일 경로와 총 참조 수 표시
                    self.log_and_print(f"  📄 {file_path} ({total_refs_in_file}개 참조)")
                    
                    # 함수별 참조 테이블 표시 (중복 제거)
                    for func_name, tables in function_table_map.items():
                        tables_str = ", ".join(sorted(tables))
                        self.log_and_print(f"     ↳ {func_name} → {tables_str}")
            
            self.log_and_print("-" * 60)
        
        # 전체 요약
        total_risk_files = set()
        total_risk_refs = 0
        
        for table_name, usage_data in all_results.items():
            if table_name in self.all_risk_tables:
                total_risk_files.update(usage_data['files_with_references'].keys())
                total_risk_refs += usage_data['total_references']
        
        self.log_and_print("\n📋 **전체 영향도 요약**:")
        self.log_and_print(f"  🔴 위험 테이블 수: {len(self.all_risk_tables)}개")
        self.log_and_print(f"  📁 영향받는 파일 수: {len(total_risk_files)}개")
        self.log_and_print(f"  🔗 총 위험 참조 수: {total_risk_refs}개")
        
        self.log_and_print("\n🚨 **가장 위험한 테이블 TOP 3**:")
        top3 = sorted_tables[:3]
        for i, (table_name, usage_data) in enumerate(top3, 1):
            risk = self.categorize_risk_level(table_name)
            files = len(usage_data['files_with_references'])
            refs = usage_data['total_references']
            self.log_and_print(f"  {i}. {table_name}: {files}개 파일, {refs}개 참조 {risk}")
        
    def save_llm_friendly_results(self, all_results: Dict[str, Dict], output_file: str) -> None:
        """LLM이 읽기 좋은 구조화된 JSON 저장"""
        try:
            # LLM 친화적 구조로 변환
            llm_data = {
                'analysis_metadata': {
                    'analysis_type': 'code_reference_analysis',
                    'project_root': str(self.project_root),
                    'total_risk_tables': len(self.all_risk_tables),
                    'python_files_total': len(self.get_python_files()),
                    'risk_categories': {
                        'critical_with_data': list(self.critical_tables_with_data),
                        'critical_structure_needed': list(self.critical_tables_structure_needed),
                        'important_with_data': list(self.important_tables_with_data),
                        'important_no_data': list(self.important_tables_no_data),
                    }
                },
                'reference_analysis': {}
            }
            
            # 각 테이블별로 LLM이 이해하기 쉬운 구조로 변환
            for table_name, usage_data in all_results.items():
                file_function_map = {}
                
                for file_path, references in usage_data.get('files_with_references', {}).items():
                    function_references = {}
                    
                    # 함수별로 참조 정보 정리
                    for pattern_name, matches in references.items():
                        for match in matches:
                            func_name = match.get('function_name', '<unknown>')
                            
                            if func_name not in function_references:
                                function_references[func_name] = {
                                    'tables_accessed': set(),
                                    'reference_count': 0,
                                    'reference_types': set()
                                }
                            
                            function_references[func_name]['tables_accessed'].add(
                                match.get('table_accessed', table_name)
                            )
                            function_references[func_name]['reference_count'] += 1
                            function_references[func_name]['reference_types'].add(pattern_name)
                    
                    # Set을 list로 변환 (JSON 직렬화를 위해)
                    for func_name, func_data in function_references.items():
                        func_data['tables_accessed'] = list(func_data['tables_accessed'])
                        func_data['reference_types'] = list(func_data['reference_types'])
                    
                    if function_references:
                        file_function_map[file_path] = function_references
                
                llm_data['reference_analysis'][table_name] = {
                    'risk_level': self.categorize_risk_level(table_name),
                    'total_files_with_references': len(usage_data.get('files_with_references', {})),
                    'total_references': usage_data.get('total_references', 0),
                    'file_function_mapping': file_function_map
                }
            
            # JSON 파일로 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(llm_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 LLM 친화적 분석 결과 저장: {output_file}")
            print("🤖 구조: 파일 → 함수/메서드 → 참조 테이블 매핑")
            
        except Exception as e:
            print(f"❌ LLM 친화적 결과 저장 실패: {e}")
    
    def generate_impact_report(self, all_results: Dict[str, Dict]) -> None:
        """기존 영향도 분석 보고서 생성 (호환성 유지)"""
        # 사람 친화적 보고서 생성
        self.generate_human_friendly_report(all_results)
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """전체 위험 테이블들에 대한 코드 참조 분석 실행"""
        self.log_and_print("🔍 위험 테이블들의 코드 참조 전면 분석 시작...")
        self.log_and_print(f"📊 분석 대상: {len(self.all_risk_tables)}개 위험 테이블")
        self.log_and_print(f"📁 검색 경로: {self.project_root}")
        self.log_and_print("=" * 80)
        
        all_results = {}
        
        # 각 위험 테이블별로 분석
        for table_name in sorted(self.all_risk_tables):
            usage_data = self.analyze_table_usage(table_name)
            all_results[table_name] = usage_data
            
            # 간단한 진행 상황 표시
            files_with_refs = len(usage_data['files_with_references'])
            total_refs = usage_data['total_references']
            self.log_and_print(f"  ✅ {table_name}: {files_with_refs}개 파일, {total_refs}개 참조")
        
        # 영향도 보고서 생성
        self.generate_impact_report(all_results)
        
        return all_results


def main():
    """메인 실행 함수"""
    print("🔍 개선된 코드 참조 분석 도구 v3.0")
    print("� 사람용 로그 + 🤖 LLM용 JSON 분리 생성")
    print("=" * 60)
    
    # 분석기 생성 및 로깅 설정
    analyzer = CodeReferenceAnalyzer("upbit_auto_trading")
    analyzer.setup_logging("tools/code_reference_analysis_human.log")
    
    # 분석 실행
    all_results = analyzer.run_full_analysis()
    
    # 결과 저장 (두 가지 형태)
    analyzer.save_llm_friendly_results(all_results, "tools/code_reference_analysis_llm.json")
    
    analyzer.log_and_print("\n" + "=" * 80)
    analyzer.log_and_print("✅ 개선된 코드 참조 분석 완료!")
    analyzer.log_and_print("🎯 생성된 파일:")
    analyzer.log_and_print("  📝 사람용 로그: tools/code_reference_analysis_human.log")
    analyzer.log_and_print("     → 파일별 함수/메서드 → 테이블 매핑 표시")
    analyzer.log_and_print("  🤖 LLM용 JSON: tools/code_reference_analysis_llm.json")
    analyzer.log_and_print("     → 구조화된 파일-함수-테이블 관계 데이터")
    analyzer.log_and_print("\n� 사용 방법:")
    analyzer.log_and_print("  📖 사람이 읽을 때: .log 파일 확인")
    analyzer.log_and_print("  🤖 LLM 분석용: .json 파일을 GPT-4o 등에 제공")
    analyzer.log_and_print("=" * 80)


if __name__ == "__main__":
    main()
