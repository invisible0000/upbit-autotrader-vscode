#!/usr/bin/env python3
"""
🚀 Super DB Table Reference Code Analyzer v5.0
===============================================

📋 **주요 기능**:
- 정확한 데이터베이스 테이블 참조 분석 (False Positive 제거)
- 복합 테이블명의 부분 매치 방지 (예: backup_info의 'info'가 logger.info와 매치되지 않음)
- SQL 컨텍스트 기반 검증으로 실제 DB 연산만 탐지
- 사람용 상세 보고서 + 머신용 JSON 분리 생성

🎯 **사용법 가이드**:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 1. **기본 사용법 (모든 테이블 분석)**:
   python super_db_table_reference_code_analyzer.py

📖 2. **특정 테이블들만 분석** (권장):
   python super_db_table_reference_code_analyzer.py --tables backup_info execution_history
   python super_db_table_reference_code_analyzer.py --tables strategies system_settings

📖 3. **다른 데이터베이스 파일 분석**:
   python super_db_table_reference_code_analyzer.py --database "path/to/your.sqlite3"

📖 4. **출력 파일명 커스터마이징**:
   python super_db_table_reference_code_analyzer.py --output-suffix "migration_check"
   → 결과: db_table_reference_codes_migration_check.log

📖 5. **완전한 예시**:
   python super_db_table_reference_code_analyzer.py \
     --database "data/settings.sqlite3" \
     --tables app_settings strategies trading_conditions \
     --output-suffix "critical_tables"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 **참조 유형 설명**:
- **SQL컨텍스트**: 실제 데이터베이스 쿼리 (SELECT, INSERT, UPDATE, DELETE 등)
- **문자열**: 설정 파일이나 리스트에서 테이블명 언급
- **함수/클래스**: 테이블명이 포함된 함수명이나 클래스명

📊 **출력 파일 설명**:
- **db_table_reference_codes.log**: 사람이 읽기 쉬운 상세 보고서
- **db_table_reference_codes_details.json**: 프로그램 처리용 구조화된 데이터

🎯 **DB 마이그레이션 활용법**:
1. 스키마 변경 전: 위험 테이블들을 --tables로 지정하여 영향도 분석
2. 보고서 확인: 어떤 파일들이 수정되어야 하는지 파악
3. 테스트 계획: 영향받는 파일들을 우선적으로 테스트

💡 **팁**: 테이블명을 정확히 모르면 먼저 모든 테이블을 분석한 후, 
        위험도가 높은 테이블들만 골라서 재분석하세요!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import re
import sqlite3
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse

class SuperDBTableReferenceAnalyzer:
    def __init__(self, project_root: str, db_path: str, output_dir: str = "tools", target_folder: str = None):
        self.project_root = Path(project_root).resolve()
        self.db_path = Path(db_path).resolve()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.target_folder = target_folder  # 특정 폴더 분석 지원
        
        # 정확한 검색 패턴들 (false positive 방지)
        self.search_patterns = {
            'sql_operations_read': [
                r'SELECT\s+.*\s+FROM\s+{table}\b',
                r'PRAGMA\s+.*{table}.*',
                r'EXPLAIN\s+.*{table}.*',
            ],
            'sql_operations_write': [
                r'INSERT\s+INTO\s+{table}\b',
                r'UPDATE\s+{table}\s+SET',
                r'DELETE\s+FROM\s+{table}\b',
                r'CREATE\s+TABLE\s+{table}\b',
                r'DROP\s+TABLE\s+{table}\b',
                r'ALTER\s+TABLE\s+{table}\b',
            ],
            'quoted_strings': [
                r'["\']' + '{table}' + r'["\']',  # 정확한 문자열 매치
            ],
            'class_table_names': [
                r'class\s+.*{table}.*\(',
                r'def\s+.*{table}.*\(',
            ]
        }
        
        # SQL 컨텍스트 키워드
        self.sql_keywords = {
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
            'FROM', 'INTO', 'TABLE', 'JOIN', 'WHERE', 'SET'
        }
        
        print("🚀 Super DB Table Reference Analyzer v5.0 초기화")
        print(f"📁 프로젝트 루트: {self.project_root}")
        print(f"🗄️ 데이터베이스: {self.db_path}")
        print(f"📤 출력 디렉토리: {self.output_dir}")
        if self.target_folder:
            print(f"🎯 타겟 폴더: {self.target_folder}")

    def get_table_names(self) -> List[str]:
        """데이터베이스에서 모든 테이블명 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                print(f"📊 발견된 테이블: {len(tables)}개")
                for i, table in enumerate(sorted(tables), 1):
                    print(f"   {i:2d}. {table}")
                return tables
        except Exception as e:
            print(f"❌ 데이터베이스 연결 오류: {e}")
            return []

    def get_python_files(self) -> List[Path]:
        """프로젝트 내 모든 Python 파일 목록 조회 (폴더 필터링 지원)"""
        python_files = []
        
        exclude_dirs = {
            '__pycache__', '.git', '.vscode', 'node_modules',
            'venv', 'env', '.pytest_cache', 'logs', 'tests',
            '.venv', 'dist', 'build', 'tools'
        }
        
        # 타겟 폴더가 지정된 경우 해당 폴더만 검색
        if self.target_folder:
            search_root = self.project_root / self.target_folder
            if not search_root.exists():
                print(f"⚠️ 타겟 폴더가 존재하지 않습니다: {search_root}")
                return []
            print(f"🎯 특정 폴더 검색: {search_root}")
        else:
            search_root = self.project_root
        
        for root, dirs, files in os.walk(search_root):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        print(f"📝 Python 파일: {len(python_files)}개 발견")
        return python_files

    def is_sql_context(self, line: str, table_name: str) -> bool:
        """라인이 SQL 컨텍스트에서 테이블을 참조하는지 확인"""
        line_upper = line.upper()
        
        # SQL 키워드가 포함된 라인인지 확인
        has_sql_keyword = any(keyword in line_upper for keyword in self.sql_keywords)
        
        # 테이블명이 정확히 매치되는지 확인 (단어 경계 사용)
        table_pattern = r'\b' + re.escape(table_name) + r'\b'
        has_table_name = bool(re.search(table_pattern, line, re.IGNORECASE))
        
        return has_sql_keyword and has_table_name

    def search_precise_references(self, file_path: Path, table_name: str) -> List[Dict]:
        """정확한 테이블 참조만 검색 (읽기/쓰기 구분)"""
        references = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # 1. SQL 컨텍스트 검사
                if self.is_sql_context(line_stripped, table_name):
                    # 읽기/쓰기 구분
                    operation_type = self.classify_sql_operation(line_stripped)
                    references.append({
                        'line_number': line_num,
                        'line_content': line_stripped,
                        'match_type': f'sql_context_{operation_type}',
                        'table_name': table_name,
                        'operation_type': operation_type
                    })
                    continue
                
                # 2. 정확한 패턴 매치
                for category, patterns in self.search_patterns.items():
                    for pattern_template in patterns:
                        pattern = pattern_template.format(table=table_name)
                        
                        if re.search(pattern, line, re.IGNORECASE):
                            # 읽기/쓰기 분류
                            if 'read' in category:
                                operation_type = 'read'
                            elif 'write' in category:
                                operation_type = 'write'
                            else:
                                operation_type = 'reference'
                                
                            references.append({
                                'line_number': line_num,
                                'line_content': line_stripped,
                                'match_type': f'{category}_pattern',
                                'table_name': table_name,
                                'pattern': pattern,
                                'operation_type': operation_type
                            })
                            break  # 한 라인에서 중복 매치 방지
                    
        except Exception as e:
            print(f"⚠️ 파일 읽기 오류 {file_path}: {e}")
            
        return references

    def classify_sql_operation(self, line: str) -> str:
        """SQL 라인을 읽기/쓰기로 분류"""
        line_upper = line.upper()
        
        read_keywords = ['SELECT', 'PRAGMA', 'EXPLAIN', 'DESCRIBE', 'SHOW']
        write_keywords = ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        
        for keyword in write_keywords:
            if keyword in line_upper:
                return 'write'
        
        for keyword in read_keywords:
            if keyword in line_upper:
                return 'read'
        
        return 'unknown'

    def analyze_table_references(self, suspect_tables: List[str] = None) -> Dict:
        """정확한 테이블 참조 분석"""
        
        # 분석할 테이블 결정
        all_tables = self.get_table_names()
        if suspect_tables:
            tables_to_analyze = [t for t in suspect_tables if t in all_tables]
            missing_tables = [t for t in suspect_tables if t not in all_tables]
            if missing_tables:
                print(f"⚠️ 데이터베이스에 없는 테이블: {missing_tables}")
            print(f"🎯 선택적 분석: {len(tables_to_analyze)}개 테이블")
        else:
            tables_to_analyze = all_tables
            print(f"🔍 전체 분석: {len(tables_to_analyze)}개 테이블")
        
        python_files = self.get_python_files()
        results = {
            'analysis_info': {
                'total_tables': len(all_tables),
                'analyzed_tables': len(tables_to_analyze),
                'total_files': len(python_files),
                'suspect_tables': suspect_tables or [],
                'analyzer_version': 'Super_v5.0_precise'
            },
            'table_references': {},
            'summary': {}
        }
        
        total_references = 0
        
        for table in tables_to_analyze:
            print(f"\n🔍 테이블 '{table}' 분석 중...")
            table_refs = defaultdict(list)
            table_total = 0
            
            for file_path in python_files:
                file_refs = self.search_precise_references(file_path, table)
                
                if file_refs:
                    rel_path = str(file_path.relative_to(self.project_root))
                    table_refs[rel_path] = file_refs
                    table_total += len(file_refs)
            
            if table_refs:
                results['table_references'][table] = dict(table_refs)
                results['summary'][table] = {
                    'total_references': table_total,
                    'affected_files': len(table_refs),
                    'avg_refs_per_file': round(table_total / len(table_refs), 2)
                }
                total_references += table_total
                print(f"   📊 {table_total}개 참조 in {len(table_refs)}개 파일")
            else:
                print(f"   ✅ '{table}' - 참조 없음")
        
        results['analysis_info']['total_references_found'] = total_references
        return results

    def generate_summary_report(self, results: Dict) -> str:
        """요약 보고서 생성 - 상세 파일 정보 포함"""
        report_lines = []
        
        # 헤더
        report_lines.extend([
            "=" * 80,
            "🚀 Super DB Table Reference Code Analysis Report v5.0",
            "=" * 80,
            "",
            "📋 **사용된 명령어 예시**:",
            "   python super_db_table_reference_code_analyzer.py --tables backup_info execution_history",
            ""
        ])
        
        # 분석 정보
        info = results['analysis_info']
        report_lines.extend([
            "📊 분석 정보:",
            f"   • 총 테이블 수: {info['total_tables']}개",
            f"   • 분석된 테이블: {info['analyzed_tables']}개",
            f"   • 스캔한 파일: {info['total_files']}개",
            f"   • 발견된 참조: {info['total_references_found']}개",
            ""
        ])
        
        # 분석 대상 테이블 (있는 경우)
        if info['suspect_tables']:
            report_lines.extend([
                "🎯 분석 대상 테이블:",
                *[f"   • {table}" for table in info['suspect_tables']],
                ""
            ])
        
        # 테이블별 상세 분석
        table_references = results.get('table_references', {})
        summary = results['summary']
        
        if summary:
            report_lines.extend([
                "📊 테이블별 상세 참조 분석:",
                "=" * 50,
                ""
            ])
            
            # 참조 수 기준 정렬
            sorted_tables = sorted(summary.items(),
                                 key=lambda x: x[1]['total_references'],
                                 reverse=True)
            
            for table, stats in sorted_tables:
                # 테이블 요약 정보
                report_lines.extend([
                    f"🗄️ **{table}** ({stats['total_references']}개 참조, {stats['affected_files']}개 파일)",
                    ""
                ])
                
                # 파일별 상세 정보
                if table in table_references:
                    file_refs = table_references[table]
                    
                    for file_path, refs in file_refs.items():
                        # 파일별 참조 유형 분석 (읽기/쓰기 구분 포함)
                        match_types = {}
                        operation_stats = {'read': 0, 'write': 0, 'reference': 0, 'unknown': 0}
                        line_numbers = []
                        
                        for ref in refs:
                            match_type = ref.get('match_type', 'unknown')
                            operation_type = ref.get('operation_type', 'unknown')
                            line_numbers.append(ref.get('line_number', 0))
                            
                            if match_type not in match_types:
                                match_types[match_type] = 0
                            match_types[match_type] += 1
                            operation_stats[operation_type] += 1
                        
                        # 매치 유형을 사람이 읽기 쉽게 변환
                        readable_types = []
                        for match_type, count in match_types.items():
                            if 'sql_context' in match_type:
                                readable_types.append(f"SQL컨텍스트({count})")
                            elif 'quoted_strings' in match_type:
                                readable_types.append(f"문자열({count})")
                            elif 'class_table_names' in match_type:
                                readable_types.append(f"함수/클래스({count})")
                            elif 'sql_operations' in match_type:
                                readable_types.append(f"SQL명령({count})")
                            else:
                                readable_types.append(f"{match_type}({count})")
                        
                        # 읽기/쓰기 통계 추가
                        operation_summary = []
                        if operation_stats['read'] > 0:
                            operation_summary.append(f"읽기:{operation_stats['read']}")
                        if operation_stats['write'] > 0:
                            operation_summary.append(f"쓰기:{operation_stats['write']}")
                        if operation_stats['reference'] > 0:
                            operation_summary.append(f"참조:{operation_stats['reference']}")
                        
                        types_str = ", ".join(readable_types)
                        lines_str = f"라인: {', '.join(map(str, sorted(line_numbers)))}"
                        ops_str = f" [{'/'.join(operation_summary)}]" if operation_summary else ""
                        
                        report_lines.append(
                            f"   📄 {file_path} ({len(refs)}개) - {types_str}{ops_str} | {lines_str}"
                        )
                    
                    report_lines.append("")  # 테이블 간 구분선
                
        else:
            report_lines.append("✅ 분석된 테이블에서 참조가 발견되지 않았습니다.")
        
        # 사용법 가이드 및 도구 정보
        report_lines.extend([
            "",
            "=" * 80,
            "🛠️ 도구 정보 및 사용법:",
            f"   • 버전: {info.get('analyzer_version', 'Super_v5.0_precise')}",
            "   • 검색 패턴: SQL 컨텍스트, 정확한 문자열 매치, 함수/클래스명 매치",
            "   • False Positive 방지: 복합 테이블명 부분 매치 제거",
            "",
            "🎯 **다음번 사용 예시**:",
            "   # 특정 테이블들만 분석:",
            f"   python super_db_table_reference_code_analyzer.py --tables {' '.join(info['suspect_tables'][:3]) if info['suspect_tables'] else 'table1 table2'}",
            "",
            "   # 다른 데이터베이스 분석:",
            "   python super_db_table_reference_code_analyzer.py --database \"path/to/other.sqlite3\"",
            "",
            "   # 출력 파일명 변경:",
            "   python super_db_table_reference_code_analyzer.py --output-suffix \"my_analysis\"",
            "",
            "💡 **DB 마이그레이션 활용**:",
            "   1. 스키마 변경 전: 위험 테이블들을 지정하여 영향도 사전 분석",
            "   2. 테스트 계획: 영향받는 파일들을 우선적으로 테스트 대상에 포함",
            "   3. 코드 수정: 각 파일의 참조 유형을 보고 적절한 수정 방법 결정",
            "",
            "🚀 **이 도구는 DB 마이그레이션 유틸리티의 핵심 컴포넌트입니다!**"
        ])
        
        return "\n".join(report_lines)

    def save_results(self, results: Dict, output_suffix: str = ""):
        """결과를 여러 형식으로 저장"""
        
        timestamp = ""
        if output_suffix:
            timestamp = f"_{output_suffix}"
        
        # 1. 사람용 상세 보고서 (텍스트)
        summary_file = self.output_dir / f"db_table_reference_codes{timestamp}.log"
        summary_report = self.generate_summary_report(results)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_report)
        
        # 2. 머신용 상세 결과 (JSON)
        details_file = self.output_dir / f"db_table_reference_codes_details{timestamp}.json"
        with open(details_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Super 분석 결과 저장 완료:")
        print(f"   📄 사람용 상세 보고서: {summary_file}")
        print(f"   🤖 머신용 JSON 데이터: {details_file}")
        
        return summary_file, details_file


def main():
    parser = argparse.ArgumentParser(
        description='🚀 Super DB Table Reference Code Analyzer v5.0',
        epilog='''
사용 예시:
  python super_db_table_reference_code_analyzer.py
  python super_db_table_reference_code_analyzer.py --tables backup_info execution_history
  python super_db_table_reference_code_analyzer.py --database "other.sqlite3" --output-suffix "migration"
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--project', default='.',
                        help='프로젝트 루트 디렉토리 (기본값: 현재 디렉토리)')
    parser.add_argument('--database', default='data/settings.sqlite3',
                        help='분석할 데이터베이스 파일 경로')
    parser.add_argument('--tables', nargs='*',
                        help='분석할 특정 테이블들 (공백으로 구분, 없으면 전체 분석)')
    parser.add_argument('--output-suffix', default='',
                        help='출력 파일명에 추가할 접미사')
    parser.add_argument('--folder', default=None,
                        help='특정 폴더만 분석 (예: upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder)')
    
    args = parser.parse_args()
    
    print("🚀 Super DB Table Reference Code Analyzer v5.1 시작")
    print("=" * 60)
    print("💡 이 도구는 정확한 DB 테이블 참조 분석을 수행합니다.")
    print("   False Positive를 제거하여 실제 참조만 정확히 탐지합니다.")
    if args.folder:
        print(f"🎯 폴더 제한 분석: {args.folder}")
    print("")
    
    # 분석기 초기화
    analyzer = SuperDBTableReferenceAnalyzer(
        project_root=args.project,
        db_path=args.database,
        output_dir="tools",
        target_folder=args.folder
    )
    
    # 분석 실행
    results = analyzer.analyze_table_references(suspect_tables=args.tables)
    
    # 결과 저장
    analyzer.save_results(results, output_suffix=args.output_suffix)
    
    print("\n✅ Super 분석 완료!")
    print("\n📋 **다음 단계**:")
    if args.tables:
        print(f"   1. db_table_reference_codes.log 파일을 열어서 '{', '.join(args.tables)}' 테이블의 영향도 확인")
    else:
        print("   1. db_table_reference_codes.log 파일을 열어서 위험도가 높은 테이블들 식별")
        print("   2. 위험 테이블들을 --tables 옵션으로 재분석 권장")
    print("   3. 영향받는 파일들을 우선적으로 테스트 및 수정")
    print("   4. DB 마이그레이션 전에 백업 필수!")


if __name__ == "__main__":
    main()
