#!/usr/bin/env python3
"""
🔍 Super Import Tracker v1.0 - DDD Debug Edition
================================================

📋 **주요 기능**:
- 특정 클래스/모듈의 import 위치 추적
- Import 오류 디버깅 지원
- 리팩토링 영향도 분석
- 실시간 의존성 검색

🎯 **실시간 디버깅 전용 기능**:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 1. **특정 클래스 추적**:
   - 클래스가 어디서 정의되고 어디서 사용되는지 확인
   - Import 경로 검증
   - Missing import 탐지

🐛 2. **Import 오류 디버깅**:
   - 실패한 import 구문 분석
   - 순환 import 탐지
   - 경로 오류 진단

🔄 3. **리팩토링 지원**:
   - 파일 이동 시 영향받는 import 목록
   - 클래스명 변경 시 수정 필요한 파일들
   - 안전한 리팩토링 가이드

⚡ 4. **빠른 검색**:
   - 키워드 기반 빠른 검색
   - 정규식 패턴 지원
   - 결과 필터링

🚀 **사용법**:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 1. **특정 클래스 추적**:
   python super_import_tracker.py --class "DatabaseSettingsPresenter"
   python super_import_tracker.py --class "SystemSafetyRequestDto"

📖 2. **모듈 import 추적**:
   python super_import_tracker.py --module "database_settings_presenter"
   python super_import_tracker.py --module "system_safety_check_use_case"

📖 3. **패턴 검색**:
   python super_import_tracker.py --pattern ".*SettingsPresenter"
   python super_import_tracker.py --pattern ".*UseCase$"

📖 4. **Import 오류 디버깅**:
   python super_import_tracker.py --debug-import "upbit_auto_trading.ui.desktop.screens.settings.presenters.database_settings_presenter"

📖 5. **빠른 키워드 검색**:
   python super_import_tracker.py --search "DatabaseSettings"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import re
import ast
import argparse
import json
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict
import importlib.util
import traceback


@dataclass
class ImportMatch:
    """Import 매칭 정보"""
    file_path: str
    line_number: int
    import_statement: str
    import_type: str  # 'from', 'import', 'attribute'
    context: str  # 주변 라인들


@dataclass
class ClassDefinition:
    """클래스 정의 정보"""
    class_name: str
    file_path: str
    line_number: int
    parent_classes: List[str]
    methods: List[str]


@dataclass
class ImportAnalysis:
    """Import 분석 결과"""
    target: str
    search_type: str
    definitions: List[ClassDefinition]
    imports: List[ImportMatch]
    potential_issues: List[str]
    suggestions: List[str]


class SuperImportTracker:
    """슈퍼 Import 추적기 - 실시간 디버깅 전용"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.upbit_root = self.project_root / "upbit_auto_trading"

        # 캐시
        self.python_files: List[str] = []
        self.file_cache: Dict[str, str] = {}

        print(f"🔍 Super Import Tracker 초기화")
        print(f"📁 프로젝트 루트: {self.project_root}")
        print(f"📁 업비트 루트: {self.upbit_root}")

    def find_python_files(self) -> List[str]:
        """Python 파일 검색 (캐시 사용)"""
        if self.python_files:
            return self.python_files

        python_files = []
        for root, dirs, files in os.walk(self.upbit_root):
            # __pycache__ 제외
            dirs[:] = [d for d in dirs if d != '__pycache__']

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)

        self.python_files = python_files
        print(f"📊 총 {len(python_files)}개 Python 파일 발견")
        return python_files

    def get_file_content(self, file_path: str) -> str:
        """파일 내용 가져오기 (캐시 사용)"""
        if file_path not in self.file_cache:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.file_cache[file_path] = f.read()
            except Exception as e:
                print(f"⚠️ {file_path} 읽기 오류: {e}")
                self.file_cache[file_path] = ""

        return self.file_cache[file_path]

    def find_class_definitions(self, class_name: str) -> List[ClassDefinition]:
        """클래스 정의 찾기"""
        definitions = []

        for file_path in self.find_python_files():
            content = self.get_file_content(file_path)
            if not content:
                continue

            try:
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        # 부모 클래스 추출
                        parent_classes = []
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                parent_classes.append(base.id)
                            elif isinstance(base, ast.Attribute):
                                parent_classes.append(f"{base.value.id}.{base.attr}")

                        # 메서드 추출
                        methods = []
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                methods.append(item.name)

                        definitions.append(ClassDefinition(
                            class_name=class_name,
                            file_path=file_path,
                            line_number=node.lineno,
                            parent_classes=parent_classes,
                            methods=methods
                        ))

            except Exception as e:
                # 파싱 오류 무시 (이미 다른 도구에서 보고됨)
                continue

        return definitions

    def find_imports(self, target: str, search_type: str = "class") -> List[ImportMatch]:
        """Import 구문 찾기"""
        imports = []

        # 검색 패턴 준비
        if search_type == "class":
            patterns = [
                rf"from\s+[\w.]+\s+import\s+.*\b{target}\b",
                rf"import\s+.*\b{target}\b",
                rf"\b{target}\b\s*\(",  # 클래스 인스턴스화
                rf":\s*{target}\b",     # 타입 힌트
            ]
        elif search_type == "module":
            patterns = [
                rf"from\s+.*\b{target}\b\s+import",
                rf"import\s+.*\b{target}\b",
            ]
        else:  # pattern
            patterns = [target]

        for file_path in self.find_python_files():
            content = self.get_file_content(file_path)
            if not content:
                continue

            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # 컨텍스트 추출 (앞뒤 2줄)
                        start = max(0, line_num - 3)
                        end = min(len(lines), line_num + 2)
                        context_lines = lines[start:end]
                        context = '\n'.join(f"{start + i + 1:3}: {ctx_line}"
                                          for i, ctx_line in enumerate(context_lines))

                        import_type = "unknown"
                        if "from" in line and "import" in line:
                            import_type = "from"
                        elif "import" in line:
                            import_type = "import"
                        elif "(" in line:
                            import_type = "instantiation"
                        elif ":" in line:
                            import_type = "type_hint"

                        imports.append(ImportMatch(
                            file_path=file_path,
                            line_number=line_num,
                            import_statement=line.strip(),
                            import_type=import_type,
                            context=context
                        ))

        return imports

    def debug_import_statement(self, module_path: str) -> List[str]:
        """Import 구문 디버깅"""
        issues = []

        try:
            # 모듈 경로 분석
            if module_path.startswith('upbit_auto_trading'):
                # 상대 경로로 변환
                parts = module_path.split('.')
                rel_path = '/'.join(parts[1:]) + '.py'
                file_path = self.upbit_root / rel_path

                if not file_path.exists():
                    issues.append(f"❌ 파일이 존재하지 않음: {file_path}")
                else:
                    # 파일 구문 검사
                    content = self.get_file_content(str(file_path))
                    try:
                        ast.parse(content)
                        issues.append(f"✅ 파일 구문 정상: {file_path}")
                    except SyntaxError as e:
                        issues.append(f"❌ 구문 오류: {file_path}:{e.lineno} - {e.msg}")

                    # __init__.py 확인
                    init_file = file_path.parent / '__init__.py'
                    if init_file.exists():
                        issues.append(f"✅ __init__.py 존재: {init_file}")
                    else:
                        issues.append(f"⚠️ __init__.py 없음: {init_file}")

            # 실제 import 시도
            try:
                spec = importlib.util.find_spec(module_path)
                if spec is None:
                    issues.append(f"❌ 모듈 스펙을 찾을 수 없음: {module_path}")
                else:
                    issues.append(f"✅ 모듈 스펙 발견: {spec.origin}")
            except Exception as e:
                issues.append(f"❌ import 실패: {module_path} - {str(e)}")

        except Exception as e:
            issues.append(f"❌ 디버깅 중 오류: {str(e)}")

        return issues

    def analyze_target(self, target: str, search_type: str = "class") -> ImportAnalysis:
        """대상 분석"""
        print(f"🔍 분석 시작: {target} ({search_type})")

        # 정의 찾기
        definitions = []
        if search_type == "class":
            definitions = self.find_class_definitions(target)

        # Import 찾기
        imports = self.find_imports(target, search_type)

        # 잠재적 이슈 분석
        issues = []
        suggestions = []

        if search_type == "class" and not definitions:
            issues.append(f"❌ '{target}' 클래스 정의를 찾을 수 없음")
            suggestions.append(f"💡 클래스명 철자 확인 또는 파일 검색 범위 확대")

        if not imports:
            issues.append(f"⚠️ '{target}' 사용처를 찾을 수 없음")
            suggestions.append(f"💡 사용되지 않는 클래스이거나 검색 패턴 조정 필요")

        # 순환 import 간단 체크
        if definitions and imports:
            def_files = {d.file_path for d in definitions}
            import_files = {i.file_path for i in imports}

            for def_file in def_files:
                def_content = self.get_file_content(def_file)
                for import_file in import_files:
                    import_module = self.file_to_module(import_file)
                    if import_module and import_module in def_content:
                        issues.append(f"⚠️ 잠재적 순환 import: {def_file} ↔ {import_file}")

        return ImportAnalysis(
            target=target,
            search_type=search_type,
            definitions=definitions,
            imports=imports,
            potential_issues=issues,
            suggestions=suggestions
        )

    def file_to_module(self, file_path: str) -> Optional[str]:
        """파일 경로를 모듈명으로 변환"""
        try:
            rel_path = Path(file_path).relative_to(self.upbit_root)
            parts = list(rel_path.parts)
            if parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]  # .py 제거
            return 'upbit_auto_trading.' + '.'.join(parts)
        except ValueError:
            return None

    def generate_report(self, analysis: ImportAnalysis, output_file: Optional[str] = None):
        """분석 보고서 생성"""
        report = []
        report.append(f"🔍 Import 분석 보고서: {analysis.target}")
        report.append("=" * 60)
        report.append(f"📅 분석 일시: {self._get_timestamp()}")
        report.append(f"🎯 검색 타입: {analysis.search_type}")
        report.append("")

        # 정의 정보
        if analysis.definitions:
            report.append(f"📍 클래스 정의 ({len(analysis.definitions)}개)")
            report.append("-" * 30)
            for definition in analysis.definitions:
                report.append(f"  📄 {self._relative_path(definition.file_path)}:{definition.line_number}")
                if definition.parent_classes:
                    report.append(f"     상속: {', '.join(definition.parent_classes)}")
                if definition.methods:
                    methods = ', '.join(definition.methods[:5])
                    if len(definition.methods) > 5:
                        methods += f" ... (총 {len(definition.methods)}개)"
                    report.append(f"     메서드: {methods}")
                report.append("")

        # Import 정보
        if analysis.imports:
            report.append(f"📥 Import 사용처 ({len(analysis.imports)}개)")
            report.append("-" * 30)

            # 타입별 그룹화
            by_type = defaultdict(list)
            for imp in analysis.imports:
                by_type[imp.import_type].append(imp)

            for import_type, type_imports in by_type.items():
                report.append(f"\n🔹 {import_type} ({len(type_imports)}개)")
                report.append("  " + "─" * 40)

                for imp in type_imports[:10]:  # 상위 10개만
                    report.append(f"  📄 {self._relative_path(imp.file_path)}:{imp.line_number}")
                    report.append(f"     {imp.import_statement}")
                    if len(type_imports) > 10 and imp == type_imports[9]:
                        report.append(f"     ... (총 {len(type_imports)}개, 나머지 생략)")
                        break
                    report.append("")

        # 잠재적 이슈
        if analysis.potential_issues:
            report.append(f"⚠️ 잠재적 이슈 ({len(analysis.potential_issues)}개)")
            report.append("-" * 30)
            for issue in analysis.potential_issues:
                report.append(f"  {issue}")
            report.append("")

        # 제안사항
        if analysis.suggestions:
            report.append(f"💡 제안사항 ({len(analysis.suggestions)}개)")
            report.append("-" * 30)
            for suggestion in analysis.suggestions:
                report.append(f"  {suggestion}")
            report.append("")

        # 상세 컨텍스트 (처음 5개만)
        if analysis.imports:
            report.append("📝 상세 컨텍스트 (상위 5개)")
            report.append("-" * 30)
            for i, imp in enumerate(analysis.imports[:5], 1):
                report.append(f"\n{i}. {self._relative_path(imp.file_path)}:{imp.line_number}")
                report.append(f"   타입: {imp.import_type}")
                report.append(f"   컨텍스트:")
                for ctx_line in imp.context.split('\n'):
                    report.append(f"   {ctx_line}")

        # 출력
        report_text = '\n'.join(report)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"📋 보고서 저장: {output_file}")
        else:
            print("\n" + report_text)

    def quick_search(self, keyword: str):
        """빠른 키워드 검색"""
        print(f"🔍 빠른 검색: '{keyword}'")

        matches = []
        for file_path in self.find_python_files():
            content = self.get_file_content(file_path)
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                if keyword.lower() in line.lower():
                    matches.append({
                        'file': self._relative_path(file_path),
                        'line': line_num,
                        'content': line.strip()
                    })

        # 결과 출력
        if matches:
            print(f"📊 '{keyword}' 검색 결과: {len(matches)}개")
            print("-" * 40)

            # 파일별 그룹화
            by_file = defaultdict(list)
            for match in matches:
                by_file[match['file']].append(match)

            for file_path, file_matches in list(by_file.items())[:10]:  # 상위 10개 파일
                print(f"\n📄 {file_path} ({len(file_matches)}개)")
                for match in file_matches[:3]:  # 파일당 상위 3개
                    print(f"  {match['line']:3}: {match['content']}")
                if len(file_matches) > 3:
                    print(f"  ... (총 {len(file_matches)}개)")
        else:
            print(f"❌ '{keyword}' 검색 결과 없음")

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
        description="🔍 Super Import Tracker - 실시간 Import 디버깅 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python super_import_tracker.py --class "DatabaseSettingsPresenter"
  python super_import_tracker.py --module "database_settings_presenter"
  python super_import_tracker.py --pattern ".*UseCase$"
  python super_import_tracker.py --debug-import "upbit_auto_trading.ui.desktop.screens.settings.presenters.database_settings_presenter"
  python super_import_tracker.py --search "DatabaseSettings"
        """
    )

    parser.add_argument('--project-root', default='.',
                       help='프로젝트 루트 디렉토리 (기본: 현재 디렉토리)')

    # 검색 옵션들 (상호 배타적)
    search_group = parser.add_mutually_exclusive_group(required=True)
    search_group.add_argument('--class', dest='class_name',
                             help='특정 클래스명 추적')
    search_group.add_argument('--module', dest='module_name',
                             help='특정 모듈명 추적')
    search_group.add_argument('--pattern', dest='pattern',
                             help='정규식 패턴 검색')
    search_group.add_argument('--debug-import', dest='debug_import',
                             help='Import 구문 디버깅')
    search_group.add_argument('--search', dest='keyword',
                             help='키워드 빠른 검색')

    parser.add_argument('--output',
                       help='출력 파일명 (지정하지 않으면 콘솔 출력)')

    args = parser.parse_args()

    # 추적기 초기화
    tracker = SuperImportTracker(args.project_root)

    # 작업 실행
    if args.class_name:
        analysis = tracker.analyze_target(args.class_name, "class")
        tracker.generate_report(analysis, args.output)

    elif args.module_name:
        analysis = tracker.analyze_target(args.module_name, "module")
        tracker.generate_report(analysis, args.output)

    elif args.pattern:
        analysis = tracker.analyze_target(args.pattern, "pattern")
        tracker.generate_report(analysis, args.output)

    elif args.debug_import:
        print(f"🐛 Import 디버깅: {args.debug_import}")
        issues = tracker.debug_import_statement(args.debug_import)
        print("\n디버깅 결과:")
        print("-" * 40)
        for issue in issues:
            print(f"  {issue}")

    elif args.keyword:
        tracker.quick_search(args.keyword)

    print("\n🎉 분석 완료!")


if __name__ == "__main__":
    main()
