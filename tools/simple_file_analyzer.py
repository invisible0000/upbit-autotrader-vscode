#!/usr/bin/env python3
"""
Super 파일 의존성 간단 분석기
특정 파일의 의존성을 간단히 분석

사용법:
python tools/simple_file_analyzer.py <파일경로>
"""

import ast
import re
from pathlib import Path
from typing import List
import sys

class SimpleFileAnalyzer:
    """간단한 파일 분석기"""

    def __init__(self, root_path: str = "upbit_auto_trading"):
        self.root_path = Path(root_path)
        self.all_python_files = list(self.root_path.rglob("*.py"))

    def analyze_file(self, target_file: str):
        """파일 분석"""
        target_path = Path(target_file)
        if not target_path.exists():
            target_path = self.root_path / target_file

        if not target_path.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {target_file}")
            return

        print(f"🔍 파일 분석: {target_path}")
        print(f"{'='*60}")

        # 기본 정보
        file_size = target_path.stat().st_size
        print(f"📏 파일 크기: {file_size:,}B")

        if file_size == 0:
            print("📋 빈 파일입니다")
            self._analyze_empty_file_usage(target_path)
            return

        # 내용 분석
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                print(f"📏 총 줄 수: {len(lines)}")
        except Exception as e:
            print(f"❌ 파일 읽기 실패: {e}")
            return

        # AST 분석
        try:
            tree = ast.parse(content)
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

            if classes:
                print(f"🏛️ 클래스: {', '.join(classes)}")
            if functions:
                print(f"⚙️ 함수: {', '.join(functions)}")

        except SyntaxError:
            print("⚠️ Python 문법 오류 - AST 분석 불가")

        # 참조 분석
        self._find_references(target_path)

        # 아키텍처 역할 분석
        self._analyze_architecture_role(target_path, content if file_size > 0 else "")

    def _analyze_empty_file_usage(self, target_path: Path):
        """빈 파일 사용 분석"""
        print(f"\n📋 빈 파일 분석:")

        # 경로 기반 역할 추정
        path_str = str(target_path)
        if "value_objects" in path_str:
            print("  🎯 Value Object 영역 - DDD 패턴")
        if "domain" in path_str:
            print("  🏗️ Domain Layer")
        if "settings" in path_str:
            print("  ⚙️ 설정 관련")
        if "health_check" in path_str:
            print("  🏥 헬스 체크 관련")

        # 참조 확인
        references = self._find_simple_references(target_path)
        if not references:
            print("  ❌ 어떤 파일에서도 참조되지 않음")
            print("  ✅ 안전한 삭제 후보")
        else:
            print(f"  🔗 {len(references)}개 파일에서 참조됨")
            for ref in references[:5]:
                print(f"    • {ref}")

    def _find_references(self, target_path: Path):
        """참조 찾기"""
        try:
            rel_target = target_path.relative_to(Path.cwd())
            target_module = str(rel_target).replace('/', '.').replace('\\', '.').replace('.py', '')
        except ValueError:
            target_module = str(target_path).replace('.py', '')

        target_name = target_path.stem
        references = []

        print(f"\n🔍 참조 분석:")
        print(f"  모듈명: {target_module}")
        print(f"  파일명: {target_name}")

        for py_file in self.all_python_files:
            if py_file == target_path:
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 간단한 참조 패턴 검색
                if target_module in content or target_name in content:
                    # 더 정확한 검증
                    if self._is_actual_reference(content, target_module, target_name):
                        references.append(str(py_file))

            except (UnicodeDecodeError, PermissionError):
                continue

        if references:
            print(f"  🔗 {len(references)}개 파일에서 참조:")
            for ref in references[:10]:
                print(f"    • {ref}")
        else:
            print("  ❌ 어떤 파일에서도 참조되지 않음")

        return references

    def _find_simple_references(self, target_path: Path):
        """빈 파일용 간단한 참조 찾기"""
        target_name = target_path.stem
        references = []

        for py_file in self.all_python_files:
            if py_file == target_path:
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if target_name in content:
                    references.append(str(py_file))

            except (UnicodeDecodeError, PermissionError):
                continue

        return references

    def _is_actual_reference(self, content: str, target_module: str, target_name: str) -> bool:
        """실제 참조인지 확인"""
        # import 문 확인
        import_patterns = [
            f"from.*{target_module}.*import",
            f"import.*{target_module}",
            f"from.*{target_name}.*import"
        ]

        for pattern in import_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        # 문자열 참조 확인
        if f'"{target_module}"' in content or f"'{target_module}'" in content:
            return True

        return False

    def _analyze_architecture_role(self, target_path: Path, content: str):
        """아키텍처 역할 분석"""
        print(f"\n🏗️ 아키텍처 분석:")

        path_str = str(target_path)

        # 경로 기반 분석
        if "domain" in path_str:
            if "entities" in path_str:
                print("  🎯 Domain Entity")
            elif "value_objects" in path_str:
                print("  💎 Value Object")
            elif "services" in path_str:
                print("  🔧 Domain Service")
            elif "repositories" in path_str:
                print("  📦 Domain Repository")
            else:
                print("  🏗️ Domain Layer")
        elif "application" in path_str:
            print("  📋 Application Layer")
        elif "infrastructure" in path_str:
            print("  🔌 Infrastructure Layer")
        elif "ui" in path_str:
            print("  🖥️ Presentation Layer")

        # 내용 기반 분석
        if content:
            if "@dataclass" in content:
                print("  📊 Data Class 패턴")
            if "class.*Repository" in content:
                print("  📦 Repository 패턴")
            if "class.*Service" in content:
                print("  🔧 Service 패턴")

def main():
    if len(sys.argv) != 2:
        print("사용법: python tools/simple_file_analyzer.py <파일경로>")
        print("예시: python tools/simple_file_analyzer.py upbit_auto_trading/domain/settings/value_objects/health_check_result.py")
        sys.exit(1)

    target_file = sys.argv[1]
    analyzer = SimpleFileAnalyzer()
    analyzer.analyze_file(target_file)

if __name__ == "__main__":
    main()
