#!/usr/bin/env python3
"""
Super 파일 의존성 상세 분석기
특정 파일의 의존성을 깊이 있게 분석하여 실제 사용 여부를 정확히 판단

사용법:
python tools/super_file_dependency_analyzer.py <파일경로>
python tools/super_file_dependency_analyzer.py upbit_auto_trading/application/queries/query_container.py
"""

import ast
import re
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, asdict
import sys

@dataclass
class DependencyInfo:
    """의존성 정보"""
    file_path: str
    import_type: str  # direct, dynamic, string_reference, reflection
    context: str      # 발견된 컨텍스트
    line_number: int
    confidence: float # 실제 사용될 가능성 (0.0-1.0)

@dataclass
class FileAnalysisResult:
    """파일 분석 결과"""
    target_file: str
    file_size: int
    total_lines: int

    # 참조 분석
    imported_by: List[DependencyInfo]
    imports_from: List[str]

    # 코드 분석
    class_definitions: List[str]
    function_definitions: List[str]
    constants: List[str]

    # DDD 분석
    ddd_patterns: List[str]
    architecture_role: str

    # 사용 가능성 평가
    usage_probability: float
    risk_assessment: str
    recommendation: str

    # 상세 증거
    evidence_for_usage: List[str]
    evidence_against_usage: List[str]

class SuperFileDependencyAnalyzer:
    """고도화된 파일 의존성 분석기"""

    def __init__(self, root_path: str = "upbit_auto_trading"):
        self.root_path = Path(root_path)
        self.all_python_files = list(self.root_path.rglob("*.py"))

        # DDD 패턴 정의 (Raw string으로 수정)
        self.ddd_patterns = {
            "entity": [r"class.*Entity", r"@dataclass", r"class.*\(.*Entity\)"],
            "value_object": [r"class.*ValueObject", r"@dataclass.*frozen=True"],
            "repository": [r"class.*Repository", r"def.*save\(", r"def.*find"],
            "service": [r"class.*Service", r"def.*execute\(", r"def.*handle\("],
            "use_case": [r"class.*UseCase", r"def.*execute\("],
            "dto": [r"class.*DTO", r"class.*Request", r"class.*Response"],
            "query": [r"class.*Query", r"def.*query\(", r"SELECT.*FROM"],
            "container": [r"class.*Container", r"def.*register\(", r"@inject"],
            "interface": [r"class.*Interface", r"from.*abc.*import", r"@abstractmethod"]
        }

        # 의존성 주입 패턴
        self.di_patterns = [
            r"@inject",
            r"container\.resolve",
            r"container\.get",
            r"\.register\(",
            r"dependency_injection",
            r"DI\.",
            r"Inject\[",
            r"get_container\(\)"
        ]

        # 동적 로딩 패턴
        self.dynamic_patterns = [
            r"importlib\.import_module",
            r"__import__\(",
            r"exec\(",
            r"eval\(",
            r"getattr\(",
            r"hasattr\(",
            r"\.load_module",
            r"ModuleType"
        ]

    def analyze_file(self, target_file: str) -> FileAnalysisResult:
        """파일 상세 분석"""
        target_path = Path(target_file)
        if not target_path.exists():
            target_path = self.root_path / target_file

        if not target_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {target_file}")

        print(f"🔍 파일 분석 시작: {target_path}")

        # 기본 정보
        file_size = target_path.stat().st_size
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            total_lines = len(lines)

        # AST 분석
        try:
            tree = ast.parse(content)
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            imports = self._extract_imports(tree)
        except SyntaxError:
            classes, functions, imports = [], [], []

        # 상수 추출
        constants = self._extract_constants(content)

        # 참조 분석
        imported_by = self._find_who_imports(target_path)

        # DDD 패턴 분석
        ddd_patterns = self._analyze_ddd_patterns(content)
        architecture_role = self._determine_architecture_role(target_path, content, classes, functions)

        # 사용 가능성 평가
        evidence_for, evidence_against = self._collect_evidence(target_path, content, imported_by)
        usage_probability = self._calculate_usage_probability(evidence_for, evidence_against, imported_by)
        risk_assessment = self._assess_risk(usage_probability, architecture_role, ddd_patterns)
        recommendation = self._generate_recommendation(usage_probability, risk_assessment, architecture_role)

        return FileAnalysisResult(
            target_file=str(target_path),
            file_size=file_size,
            total_lines=total_lines,
            imported_by=imported_by,
            imports_from=imports,
            class_definitions=classes,
            function_definitions=functions,
            constants=constants,
            ddd_patterns=ddd_patterns,
            architecture_role=architecture_role,
            usage_probability=usage_probability,
            risk_assessment=risk_assessment,
            recommendation=recommendation,
            evidence_for_usage=evidence_for,
            evidence_against_usage=evidence_against
        )

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """AST에서 import 추출"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    def _extract_constants(self, content: str) -> List[str]:
        """상수 정의 추출"""
        constants = []
        for line in content.split('\n'):
            line = line.strip()
            if re.match(r'^[A-Z_][A-Z0-9_]*\s*=', line):
                constants.append(line.split('=')[0].strip())
        return constants

    def _find_who_imports(self, target_path: Path) -> List[DependencyInfo]:
        """누가 이 파일을 import하는지 찾기"""
        imported_by = []

        try:
            rel_target = target_path.relative_to(Path.cwd())
            target_module = str(rel_target).replace('/', '.').replace('\\', '.').replace('.py', '')
        except ValueError:
            target_module = str(target_path).replace('.py', '')

        target_name = target_path.stem

        for py_file in self.all_python_files:
            if py_file == target_path:
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                # 다양한 import 패턴 검색
                patterns_to_check = [
                    (f"from.*{target_module}.*import", "direct_import"),
                    (f"import.*{target_module}", "direct_import"),
                    (f"from.*{target_name}.*import", "partial_import"),
                    (f'"{target_module}"', "string_reference"),
                    (f"'{target_module}'", "string_reference"),
                    (f"{target_name}", "name_reference")
                ]

                for i, line in enumerate(lines, 1):
                    for pattern, import_type in patterns_to_check:
                        if re.search(pattern, line, re.IGNORECASE):
                            confidence = self._calculate_import_confidence(line, import_type)

                            imported_by.append(DependencyInfo(
                                file_path=str(py_file),
                                import_type=import_type,
                                context=line.strip(),
                                line_number=i,
                                confidence=confidence
                            ))
            except (UnicodeDecodeError, PermissionError):
                continue

        return imported_by

    def _calculate_import_confidence(self, line: str, import_type: str) -> float:
        """import 신뢰도 계산"""
        if import_type == "direct_import":
            return 0.9
        elif import_type == "partial_import":
            return 0.8
        elif import_type == "string_reference":
            if "import" in line or "module" in line:
                return 0.7
            return 0.3
        elif import_type == "name_reference":
            if line.strip().startswith("#"):
                return 0.1
            return 0.4
        return 0.5

    def _analyze_ddd_patterns(self, content: str) -> List[str]:
        """DDD 패턴 분석"""
        found_patterns = []

        for pattern_name, patterns in self.ddd_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                    found_patterns.append(pattern_name)
                    break

        return found_patterns

    def _determine_architecture_role(self, file_path: Path, content: str, classes: List[str], functions: List[str]) -> str:
        """아키텍처에서의 역할 판단"""
        path_str = str(file_path)

        # 경로 기반 판단
        if "domain" in path_str:
            if "entities" in path_str:
                return "Domain Entity"
            elif "services" in path_str:
                return "Domain Service"
            elif "repositories" in path_str:
                return "Domain Repository"
            elif "value_objects" in path_str:
                return "Value Object"
            return "Domain Layer"
        elif "application" in path_str:
            if "use_cases" in path_str:
                return "Use Case"
            elif "services" in path_str:
                return "Application Service"
            elif "queries" in path_str:
                return "Query Handler"
            return "Application Layer"
        elif "infrastructure" in path_str:
            return "Infrastructure Layer"
        elif "ui" in path_str or "presentation" in path_str:
            return "Presentation Layer"
        elif "business_logic" in path_str:
            return "Business Logic"

        # 내용 기반 판단
        if any("Repository" in cls for cls in classes):
            return "Repository Pattern"
        elif any("Service" in cls for cls in classes):
            return "Service Pattern"
        elif any("UseCase" in cls for cls in classes):
            return "Use Case Pattern"
        elif any("Container" in cls for cls in classes):
            return "Dependency Container"
        elif any("Query" in cls for cls in classes):
            return "Query Pattern"

        return "General Implementation"

    def _collect_evidence(self, target_path: Path, content: str, imported_by: List[DependencyInfo]) -> Tuple[List[str], List[str]]:
        """사용/미사용 증거 수집"""
        evidence_for = []
        evidence_against = []

        # 사용 증거
        high_confidence_imports = [dep for dep in imported_by if dep.confidence >= 0.7]
        if high_confidence_imports:
            evidence_for.append(f"고신뢰도 import {len(high_confidence_imports)}개 발견")

        # DI 패턴 검색
        di_matches = sum(1 for pattern in self.di_patterns if re.search(pattern, content))
        if di_matches > 0:
            evidence_for.append(f"의존성 주입 패턴 {di_matches}개 발견")

        # 동적 로딩 패턴
        dynamic_matches = sum(1 for pattern in self.dynamic_patterns if re.search(pattern, content))
        if dynamic_matches > 0:
            evidence_for.append(f"동적 로딩 패턴 {dynamic_matches}개 발견")

        # 클래스/함수 존재
        if re.search(r"class\s+\w+", content):
            evidence_for.append("클래스 정의 존재")
        if re.search(r"def\s+\w+", content):
            evidence_for.append("함수 정의 존재")

        # 미사용 증거
        if len(imported_by) == 0:
            evidence_against.append("어떤 파일에서도 직접 import되지 않음")

        low_confidence_only = all(dep.confidence < 0.5 for dep in imported_by)
        if low_confidence_only and imported_by:
            evidence_against.append("모든 참조가 낮은 신뢰도")

        if target_path.stat().st_size == 0:
            evidence_against.append("빈 파일")

        # TODO 코멘트나 미완성 코드
        if re.search(r"#\s*TODO", content, re.IGNORECASE):
            evidence_against.append("TODO 주석 포함 (미완성 코드)")

        if re.search(r"pass\s*$", content, re.MULTILINE):
            evidence_against.append("pass 문만 있는 함수/클래스 존재")

        return evidence_for, evidence_against

    def _calculate_usage_probability(self, evidence_for: List[str], evidence_against: List[str], imported_by: List[DependencyInfo]) -> float:
        """사용 가능성 확률 계산"""
        score = 0.5  # 기본 점수

        # 증거 기반 점수 조정
        score += len(evidence_for) * 0.1
        score -= len(evidence_against) * 0.15

        # import 신뢰도 기반 조정
        if imported_by:
            avg_confidence = sum(dep.confidence for dep in imported_by) / len(imported_by)
            score += (avg_confidence - 0.5) * 0.4

        # 범위 제한
        return max(0.0, min(1.0, score))

    def _assess_risk(self, usage_probability: float, architecture_role: str, ddd_patterns: List[str]) -> str:
        """위험도 평가"""
        if usage_probability >= 0.8:
            return "🔴 HIGH RISK - 삭제 위험"
        elif usage_probability >= 0.6:
            return "🟡 MEDIUM RISK - 신중한 검토 필요"
        elif usage_probability >= 0.4:
            return "🟠 LOW-MEDIUM RISK - 추가 조사 권장"
        elif usage_probability >= 0.2:
            return "🟢 LOW RISK - 삭제 후보"
        else:
            return "✅ VERY LOW RISK - 안전한 삭제 후보"

    def _generate_recommendation(self, usage_probability: float, risk_assessment: str, architecture_role: str) -> str:
        """권장사항 생성"""
        if usage_probability >= 0.8:
            return f"❌ 삭제 금지 - {architecture_role}으로 중요한 역할 수행 가능성 높음"
        elif usage_probability >= 0.6:
            return f"⚠️ 신중한 검토 필요 - 실제 런타임 테스트 권장"
        elif usage_probability >= 0.4:
            return f"🔍 추가 조사 필요 - DI나 동적 로딩으로 사용될 가능성 있음"
        elif usage_probability >= 0.2:
            return f"📋 삭제 고려 가능 - 백업 후 제거 테스트"
        else:
            return f"✅ 안전한 삭제 - 미사용 확률 높음"

    def print_analysis_result(self, result: FileAnalysisResult):
        """분석 결과 출력"""
        print(f"\n{'='*80}")
        print(f"📋 파일 상세 분석 결과")
        print(f"{'='*80}")

        print(f"📁 파일: {result.target_file}")
        print(f"📏 크기: {result.file_size:,}B ({result.total_lines}줄)")
        print(f"🏗️ 아키텍처 역할: {result.architecture_role}")
        print(f"🎯 DDD 패턴: {', '.join(result.ddd_patterns) if result.ddd_patterns else '없음'}")

        print(f"\n📊 사용 가능성 평가:")
        print(f"  확률: {result.usage_probability:.1%}")
        print(f"  위험도: {result.risk_assessment}")
        print(f"  권장사항: {result.recommendation}")

        if result.imported_by:
            print(f"\n🔗 참조하는 파일들 ({len(result.imported_by)}개):")
            for dep in sorted(result.imported_by, key=lambda x: x.confidence, reverse=True)[:10]:
                print(f"  • {dep.file_path}:{dep.line_number}")
                print(f"    타입: {dep.import_type}, 신뢰도: {dep.confidence:.1%}")
                print(f"    컨텍스트: {dep.context}")
        else:
            print(f"\n🔗 참조하는 파일: 없음")

        if result.imports_from:
            print(f"\n📦 import하는 모듈들:")
            for imp in result.imports_from[:10]:
                print(f"  • {imp}")

        if result.class_definitions:
            print(f"\n🏛️ 클래스 정의 ({len(result.class_definitions)}개):")
            for cls in result.class_definitions[:5]:
                print(f"  • {cls}")

        if result.function_definitions:
            print(f"\n⚙️ 함수 정의 ({len(result.function_definitions)}개):")
            for func in result.function_definitions[:5]:
                print(f"  • {func}")

        if result.evidence_for_usage:
            print(f"\n✅ 사용 증거:")
            for evidence in result.evidence_for_usage:
                print(f"  • {evidence}")

        if result.evidence_against_usage:
            print(f"\n❌ 미사용 증거:")
            for evidence in result.evidence_against_usage:
                print(f"  • {evidence}")

        print(f"\n{'='*80}")

def main():
    if len(sys.argv) != 2:
        print("사용법: python tools/super_file_dependency_analyzer.py <파일경로>")
        print("예시: python tools/super_file_dependency_analyzer.py upbit_auto_trading/application/queries/query_container.py")
        sys.exit(1)

    target_file = sys.argv[1]
    analyzer = SuperFileDependencyAnalyzer()

    try:
        result = analyzer.analyze_file(target_file)
        analyzer.print_analysis_result(result)

        # JSON 보고서 저장
        json_output = f"super_file_analysis_{Path(target_file).stem}.json"
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, ensure_ascii=False, indent=2)
        print(f"\n💾 상세 보고서 저장: {json_output}")

    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
