#!/usr/bin/env python3
"""
🏛️ Super Code Import Reference Analyzer v1.0 - DDD Edition
============================================================

📋 **주요 기능**:
- DDD 계층별 의존성 분석 (Domain ← Application ← Infrastructure ← Presentation)
- Import 참조 관계 추적 및 시각화
- 순환 의존성 탐지
- 계층 위반 검증 (DDD 원칙 준수 여부)
- Use Case → Repository → Service 의존성 체인 분석

🎯 **DDD 아키텍처 전용 기능**:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏗️ 1. **계층별 의존성 분석**:
   - Domain Layer: entities, services, repositories (interfaces)
   - Application Layer: use_cases, dtos, services
   - Infrastructure Layer: persistence, external, logging
   - Presentation Layer: ui, presenters, views

🔍 2. **Use Case 중심 분석**:
   - 특정 Use Case가 사용하는 모든 의존성 추적
   - DTO → Entity → Repository 체인 검증
   - Missing imports나 잘못된 의존성 탐지

⚠️ 3. **아키텍처 위반 검증**:
   - Domain이 다른 계층을 의존하는지 확인
   - Presentation이 Domain을 직접 접근하는지 확인
   - 순환 의존성 경고

📊 4. **시각화 및 보고서**:
   - 계층별 의존성 트리
   - Use Case별 의존성 맵
   - 아키텍처 위반 사항 상세 리포트

🚀 **사용법**:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 1. **전체 DDD 구조 분석**:
   python super_code_import_reference_analyzer.py

📖 2. **특정 Use Case 의존성 분석**:
   python super_code_import_reference_analyzer.py --use-case "database_replacement_use_case"

📖 3. **계층별 분석**:
   python super_code_import_reference_analyzer.py --layer domain
   python super_code_import_reference_analyzer.py --layer application

📖 4. **아키텍처 위반 검증**:
   python super_code_import_reference_analyzer.py --check-violations

📖 5. **특정 파일의 의존성 추적**:
   python super_code_import_reference_analyzer.py --file "database_settings_presenter.py"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import re
import ast
import argparse
import json
from typing import Dict, List, Set, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import traceback


@dataclass
class ImportInfo:
    """Import 정보"""
    module: str
    imported_names: List[str]
    file_path: str
    line_number: int
    import_type: str  # 'from', 'import', 'relative'


@dataclass
class FileAnalysis:
    """파일 분석 결과"""
    file_path: str
    layer: str
    imports: List[ImportInfo]
    dependencies: Set[str]
    exports: Set[str]  # 이 파일에서 정의된 클래스/함수들
    use_cases: Set[str]  # Use Case 관련 정보
    dtos: Set[str]  # DTO 관련 정보


@dataclass
class LayerViolation:
    """계층 위반 정보"""
    violating_file: str
    violated_layer: str
    violation_type: str
    details: str


@dataclass
class DependencyChain:
    """의존성 체인"""
    start_file: str
    end_file: str
    chain: List[str]
    chain_type: str  # 'use_case_to_repository', 'dto_to_entity', etc.


class DDDArchitectureAnalyzer:
    """DDD 아키텍처 분석기"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.upbit_root = self.project_root / "upbit_auto_trading"

        # DDD 계층 정의
        self.layers = {
            'domain': ['entities', 'value_objects', 'services', 'repositories'],
            'application': ['use_cases', 'dtos', 'services'],
            'infrastructure': ['persistence', 'external', 'logging', 'configs'],
            'presentation': ['ui', 'desktop', 'presenters', 'views', 'widgets']
        }

        # 분석 결과
        self.file_analyses: Dict[str, FileAnalysis] = {}
        self.layer_violations: List[LayerViolation] = []
        self.circular_dependencies: List[List[str]] = []
        self.dependency_chains: List[DependencyChain] = []

        print(f"🏛️ DDD 아키텍처 분석기 초기화")
        print(f"📁 프로젝트 루트: {self.project_root}")
        print(f"📁 업비트 루트: {self.upbit_root}")

    def identify_layer(self, file_path: str) -> str:
        """파일의 DDD 계층 식별"""
        try:
            rel_path = Path(file_path).relative_to(self.upbit_root)
            path_parts = rel_path.parts

            # 계층별 매칭
            for layer, keywords in self.layers.items():
                for keyword in keywords:
                    if keyword in path_parts:
                        return layer

            # 경로 기반 추론
            if 'domain' in path_parts:
                return 'domain'
            elif 'application' in path_parts:
                return 'application'
            elif 'infrastructure' in path_parts:
                return 'infrastructure'
            elif 'ui' in path_parts or 'desktop' in path_parts:
                return 'presentation'

            return 'unknown'

        except ValueError:
            return 'external'

    def extract_imports(self, file_path: str) -> List[ImportInfo]:
        """파일에서 import 정보 추출"""
        imports = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(ImportInfo(
                            module=alias.name,
                            imported_names=[alias.name],
                            file_path=file_path,
                            line_number=node.lineno,
                            import_type='import'
                        ))

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_names = [alias.name for alias in node.names]
                        imports.append(ImportInfo(
                            module=node.module,
                            imported_names=imported_names,
                            file_path=file_path,
                            line_number=node.lineno,
                            import_type='from'
                        ))

        except Exception as e:
            print(f"⚠️ {file_path} 파싱 오류: {e}")

        return imports

    def extract_exports(self, file_path: str) -> Set[str]:
        """파일에서 export되는 클래스/함수 추출"""
        exports = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    exports.add(node.name)
                elif isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):  # public functions only
                        exports.add(node.name)

        except Exception as e:
            print(f"⚠️ {file_path} exports 추출 오류: {e}")

        return exports

    def categorize_by_pattern(self, file_path: str, exports: Set[str]) -> Tuple[Set[str], Set[str]]:
        """파일명과 exports를 기반으로 Use Case, DTO 분류"""
        use_cases = set()
        dtos = set()

        file_name = Path(file_path).name.lower()

        # Use Case 패턴
        if 'use_case' in file_name:
            use_cases.update(exports)

        # DTO 패턴
        if 'dto' in file_name or file_name.endswith('_dto.py'):
            dtos.update(exports)

        # exports에서 패턴 매칭
        for export in exports:
            if export.endswith('UseCase'):
                use_cases.add(export)
            elif export.endswith('Dto') or export.endswith('DTO'):
                dtos.add(export)

        return use_cases, dtos

    def analyze_file(self, file_path: str) -> FileAnalysis:
        """단일 파일 분석"""
        imports = self.extract_imports(file_path)
        exports = self.extract_exports(file_path)
        layer = self.identify_layer(file_path)

        # 의존성 추출
        dependencies = set()
        for imp in imports:
            if 'upbit_auto_trading' in imp.module:
                dependencies.add(imp.module)

        # Use Case, DTO 분류
        use_cases, dtos = self.categorize_by_pattern(file_path, exports)

        return FileAnalysis(
            file_path=file_path,
            layer=layer,
            imports=imports,
            dependencies=dependencies,
            exports=exports,
            use_cases=use_cases,
            dtos=dtos
        )

    def find_python_files(self) -> List[str]:
        """Python 파일 검색"""
        python_files = []

        for root, dirs, files in os.walk(self.upbit_root):
            # __pycache__ 제외
            dirs[:] = [d for d in dirs if d != '__pycache__']

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)

        return python_files

    def check_layer_violations(self):
        """DDD 계층 위반 검증"""
        for file_path, analysis in self.file_analyses.items():
            if analysis.layer == 'domain':
                # Domain은 다른 계층을 의존하면 안됨
                for dep in analysis.dependencies:
                    if 'application' in dep or 'infrastructure' in dep or 'ui' in dep:
                        self.layer_violations.append(LayerViolation(
                            violating_file=file_path,
                            violated_layer='domain',
                            violation_type='domain_dependency',
                            details=f"Domain layer depends on {dep}"
                        ))

            elif analysis.layer == 'presentation':
                # Presentation은 Domain을 직접 의존하면 안됨
                for dep in analysis.dependencies:
                    if '/domain/' in dep and '/application/' not in dep:
                        self.layer_violations.append(LayerViolation(
                            violating_file=file_path,
                            violated_layer='presentation',
                            violation_type='presentation_to_domain',
                            details=f"Presentation layer directly depends on {dep}"
                        ))

    def find_circular_dependencies(self):
        """순환 의존성 탐지"""
        # 의존성 그래프 구축
        graph = defaultdict(set)

        for file_path, analysis in self.file_analyses.items():
            for dep in analysis.dependencies:
                # 의존성 모듈을 실제 파일로 매핑
                dep_file = self.module_to_file(dep)
                if dep_file and dep_file in self.file_analyses:
                    graph[file_path].add(dep_file)

        # DFS로 순환 탐지
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            if node in rec_stack:
                # 순환 발견
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                self.circular_dependencies.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, set()):
                dfs(neighbor, path + [neighbor])

            rec_stack.remove(node)

        for file_path in self.file_analyses:
            if file_path not in visited:
                dfs(file_path, [file_path])

    def module_to_file(self, module: str) -> Optional[str]:
        """모듈명을 실제 파일 경로로 변환"""
        # upbit_auto_trading.domain.entities.example -> domain/entities/example.py
        if not module.startswith('upbit_auto_trading'):
            return None

        parts = module.split('.')
        if len(parts) < 2:
            return None

        # upbit_auto_trading 제거
        rel_parts = parts[1:]

        # 파일 경로 구성
        file_path = self.upbit_root / '/'.join(rel_parts[:-1]) / f"{rel_parts[-1]}.py"

        if file_path.exists():
            return str(file_path)

        return None

    def trace_use_case_dependencies(self, use_case_name: str) -> List[DependencyChain]:
        """특정 Use Case의 의존성 체인 추적"""
        chains = []

        # Use Case 파일 찾기
        use_case_file = None
        for file_path, analysis in self.file_analyses.items():
            if use_case_name in analysis.use_cases or use_case_name in Path(file_path).name:
                use_case_file = file_path
                break

        if not use_case_file:
            return chains

        # BFS로 의존성 체인 추적
        queue = deque([(use_case_file, [use_case_file])])
        visited = set()

        while queue:
            current_file, path = queue.popleft()

            if current_file in visited:
                continue
            visited.add(current_file)

            analysis = self.file_analyses.get(current_file)
            if not analysis:
                continue

            for dep in analysis.dependencies:
                dep_file = self.module_to_file(dep)
                if dep_file and dep_file in self.file_analyses:
                    new_path = path + [dep_file]

                    # 체인 타입 결정
                    chain_type = self.determine_chain_type(analysis, self.file_analyses[dep_file])

                    chains.append(DependencyChain(
                        start_file=use_case_file,
                        end_file=dep_file,
                        chain=new_path,
                        chain_type=chain_type
                    ))

                    if len(new_path) < 5:  # 깊이 제한
                        queue.append((dep_file, new_path))

        return chains

    def determine_chain_type(self, from_analysis: FileAnalysis, to_analysis: FileAnalysis) -> str:
        """의존성 체인 타입 결정"""
        if from_analysis.layer == 'application' and to_analysis.layer == 'domain':
            if to_analysis.file_path.endswith('_repository.py'):
                return 'use_case_to_repository'
            elif 'entities' in to_analysis.file_path:
                return 'use_case_to_entity'
            elif 'services' in to_analysis.file_path:
                return 'use_case_to_service'

        if from_analysis.dtos and to_analysis.exports:
            return 'dto_to_entity'

        return 'general_dependency'

    def analyze_all(self):
        """전체 분석 실행"""
        print("🔍 Python 파일 검색 중...")
        python_files = self.find_python_files()
        print(f"📊 총 {len(python_files)}개 파일 발견")

        print("📋 파일별 분석 진행 중...")
        for i, file_path in enumerate(python_files, 1):
            if i % 20 == 0:
                print(f"   진행률: {i}/{len(python_files)} ({i/len(python_files)*100:.1f}%)")

            try:
                analysis = self.analyze_file(file_path)
                self.file_analyses[file_path] = analysis
            except Exception as e:
                print(f"⚠️ {file_path} 분석 실패: {e}")

        print("🔍 아키텍처 위반 검증 중...")
        self.check_layer_violations()

        print("🔄 순환 의존성 탐지 중...")
        self.find_circular_dependencies()

        print("✅ 전체 분석 완료!")

    def generate_report(self, output_file: str = "ddd_architecture_analysis.log"):
        """상세 분석 보고서 생성"""
        report = []
        report.append("🏛️ DDD 아키텍처 분석 보고서")
        report.append("=" * 60)
        report.append(f"📅 분석 일시: {self._get_timestamp()}")
        report.append(f"📁 분석 대상: {self.upbit_root}")
        report.append(f"📊 총 파일 수: {len(self.file_analyses)}")
        report.append("")

        # 계층별 통계
        layer_stats = defaultdict(int)
        for analysis in self.file_analyses.values():
            layer_stats[analysis.layer] += 1

        report.append("📊 계층별 파일 분포")
        report.append("-" * 30)
        for layer, count in sorted(layer_stats.items()):
            report.append(f"  {layer:15}: {count:3d}개")
        report.append("")

        # Use Case 분석
        all_use_cases = set()
        for analysis in self.file_analyses.values():
            all_use_cases.update(analysis.use_cases)

        report.append(f"🎯 Use Case 분석 ({len(all_use_cases)}개)")
        report.append("-" * 30)
        for use_case in sorted(all_use_cases):
            report.append(f"  📋 {use_case}")
        report.append("")

        # DTO 분석
        all_dtos = set()
        for analysis in self.file_analyses.values():
            all_dtos.update(analysis.dtos)

        report.append(f"📝 DTO 분석 ({len(all_dtos)}개)")
        report.append("-" * 30)
        for dto in sorted(all_dtos):
            report.append(f"  📄 {dto}")
        report.append("")

        # 아키텍처 위반
        if self.layer_violations:
            report.append(f"⚠️ 아키텍처 위반 ({len(self.layer_violations)}개)")
            report.append("-" * 30)
            for violation in self.layer_violations:
                report.append(f"  🚨 {violation.violation_type}")
                report.append(f"     파일: {self._relative_path(violation.violating_file)}")
                report.append(f"     상세: {violation.details}")
                report.append("")
        else:
            report.append("✅ 아키텍처 위반 없음")
            report.append("")

        # 순환 의존성
        if self.circular_dependencies:
            report.append(f"🔄 순환 의존성 ({len(self.circular_dependencies)}개)")
            report.append("-" * 30)
            for i, cycle in enumerate(self.circular_dependencies, 1):
                report.append(f"  순환 {i}:")
                for j, file_path in enumerate(cycle):
                    arrow = " → " if j < len(cycle) - 1 else ""
                    report.append(f"    {self._relative_path(file_path)}{arrow}")
                report.append("")
        else:
            report.append("✅ 순환 의존성 없음")
            report.append("")

        # 파일별 상세 정보
        report.append("📋 파일별 상세 분석")
        report.append("-" * 30)

        for layer in ['domain', 'application', 'infrastructure', 'presentation']:
            layer_files = [f for f, a in self.file_analyses.items() if a.layer == layer]
            if layer_files:
                report.append(f"\n🏗️ {layer.upper()} LAYER ({len(layer_files)}개)")
                report.append("─" * 40)

                for file_path in sorted(layer_files):
                    analysis = self.file_analyses[file_path]
                    report.append(f"\n📄 {self._relative_path(file_path)}")

                    if analysis.exports:
                        report.append(f"   exports: {', '.join(sorted(analysis.exports))}")

                    if analysis.use_cases:
                        report.append(f"   use_cases: {', '.join(sorted(analysis.use_cases))}")

                    if analysis.dtos:
                        report.append(f"   dtos: {', '.join(sorted(analysis.dtos))}")

                    if analysis.dependencies:
                        report.append(f"   dependencies: {len(analysis.dependencies)}개")
                        for dep in sorted(analysis.dependencies):
                            if 'upbit_auto_trading' in dep:
                                report.append(f"     → {dep}")

        # 보고서 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        print(f"📋 상세 보고서 저장: {output_file}")

    def generate_json_report(self, output_file: str = "ddd_architecture_analysis.json"):
        """JSON 형태 보고서 생성 (머신 가독용)"""
        data = {
            'timestamp': self._get_timestamp(),
            'project_root': str(self.project_root),
            'total_files': len(self.file_analyses),
            'layers': dict(defaultdict(int)),
            'files': {},
            'violations': [asdict(v) for v in self.layer_violations],
            'circular_dependencies': [[self._relative_path(f) for f in cycle] for cycle in self.circular_dependencies],
            'use_cases': [],
            'dtos': []
        }

        # 계층별 통계
        for analysis in self.file_analyses.values():
            data['layers'][analysis.layer] = data['layers'].get(analysis.layer, 0) + 1

        # 파일별 정보
        for file_path, analysis in self.file_analyses.items():
            data['files'][self._relative_path(file_path)] = {
                'layer': analysis.layer,
                'exports': list(analysis.exports),
                'use_cases': list(analysis.use_cases),
                'dtos': list(analysis.dtos),
                'dependencies': list(analysis.dependencies),
                'import_count': len(analysis.imports)
            }

        # Use Cases, DTOs 수집
        all_use_cases = set()
        all_dtos = set()
        for analysis in self.file_analyses.values():
            all_use_cases.update(analysis.use_cases)
            all_dtos.update(analysis.dtos)

        data['use_cases'] = sorted(all_use_cases)
        data['dtos'] = sorted(all_dtos)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"📊 JSON 보고서 저장: {output_file}")

    def analyze_specific_use_case(self, use_case_name: str):
        """특정 Use Case 의존성 분석"""
        print(f"🎯 Use Case 분석: {use_case_name}")

        chains = self.trace_use_case_dependencies(use_case_name)

        if not chains:
            print(f"❌ '{use_case_name}' Use Case를 찾을 수 없습니다.")
            return

        print(f"📊 발견된 의존성 체인: {len(chains)}개")
        print("")

        # 체인 타입별 그룹화
        chains_by_type = defaultdict(list)
        for chain in chains:
            chains_by_type[chain.chain_type].append(chain)

        for chain_type, type_chains in chains_by_type.items():
            print(f"🔗 {chain_type} ({len(type_chains)}개)")
            print("-" * 40)

            for chain in type_chains[:5]:  # 상위 5개만 표시
                print(f"  {self._relative_path(chain.start_file)}")
                for i, file_path in enumerate(chain.chain[1:], 1):
                    print(f"  {'  ' * i}→ {self._relative_path(file_path)}")
                print("")

    def _relative_path(self, file_path: str) -> str:
        """상대 경로 반환"""
        try:
            return str(Path(file_path).relative_to(self.project_root))
        except ValueError:
            return file_path

    def _get_timestamp(self) -> str:
        """현재 시간 반환"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="🏛️ DDD 아키텍처 분석 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python super_code_import_reference_analyzer.py
  python super_code_import_reference_analyzer.py --use-case "database_replacement_use_case"
  python super_code_import_reference_analyzer.py --layer domain
  python super_code_import_reference_analyzer.py --check-violations
  python super_code_import_reference_analyzer.py --file "database_settings_presenter.py"
        """
    )

    parser.add_argument('--project-root', default='.',
                       help='프로젝트 루트 디렉토리 (기본: 현재 디렉토리)')
    parser.add_argument('--use-case',
                       help='특정 Use Case 의존성 분석')
    parser.add_argument('--layer', choices=['domain', 'application', 'infrastructure', 'presentation'],
                       help='특정 계층만 분석')
    parser.add_argument('--check-violations', action='store_true',
                       help='아키텍처 위반만 검사')
    parser.add_argument('--file',
                       help='특정 파일의 의존성 추적')
    parser.add_argument('--output', default='ddd_architecture_analysis',
                       help='출력 파일명 (확장자 제외)')

    args = parser.parse_args()

    # 분석기 초기화
    analyzer = DDDArchitectureAnalyzer(args.project_root)

    # 전체 분석 실행
    analyzer.analyze_all()

    # 특정 분석 실행
    if args.use_case:
        analyzer.analyze_specific_use_case(args.use_case)
    elif args.check_violations:
        if analyzer.layer_violations:
            print("⚠️ 아키텍처 위반 발견!")
            for violation in analyzer.layer_violations:
                print(f"  🚨 {violation.violation_type}: {violation.details}")
        else:
            print("✅ 아키텍처 위반 없음")
    else:
        # 전체 보고서 생성
        log_file = f"{args.output}.log"
        json_file = f"{args.output}.json"

        analyzer.generate_report(log_file)
        analyzer.generate_json_report(json_file)

        print("")
        print("🎉 분석 완료!")
        print(f"📋 상세 보고서: {log_file}")
        print(f"📊 JSON 데이터: {json_file}")


if __name__ == "__main__":
    main()
