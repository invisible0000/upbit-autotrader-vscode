"""
DDD 의존성 위반 분석 도구
Domain 계층의 Infrastructure 의존성을 구체적으로 분석합니다.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class ViolationCase:
    """의존성 위반 사례"""
    file_path: str
    line_number: int
    violation_type: str
    code_snippet: str
    impact_level: str
    fix_suggestion: str

class DomainPurityAnalyzer:
    """Domain 계층 순수성 분석기"""

    def __init__(self):
        self.domain_path = Path("upbit_auto_trading/domain")
        self.violations = []

    def analyze_all(self) -> Dict[str, List[ViolationCase]]:
        """전체 Domain 계층 분석"""
        results = {
            'infrastructure_imports': [],
            'direct_db_access': [],
            'external_dependencies': [],
            'logging_violations': []
        }

        for py_file in self.domain_path.rglob("*.py"):
            file_violations = self._analyze_file(py_file)
            for category, violations in file_violations.items():
                results[category].extend(violations)

        return results

    def _analyze_file(self, file_path: Path) -> Dict[str, List[ViolationCase]]:
        """개별 파일 분석"""
        violations = {
            'infrastructure_imports': [],
            'direct_db_access': [],
            'external_dependencies': [],
            'logging_violations': []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_no, line in enumerate(lines, 1):
                # Infrastructure import 검사
                if self._is_infrastructure_import(line):
                    violations['infrastructure_imports'].append(
                        ViolationCase(
                            file_path=str(file_path),
                            line_number=line_no,
                            violation_type="Infrastructure Import",
                            code_snippet=line.strip(),
                            impact_level="HIGH",
                            fix_suggestion="Domain Events 또는 Repository 인터페이스 사용"
                        )
                    )

                # 직접 DB 접근 검사
                if self._is_direct_db_access(line):
                    violations['direct_db_access'].append(
                        ViolationCase(
                            file_path=str(file_path),
                            line_number=line_no,
                            violation_type="Direct DB Access",
                            code_snippet=line.strip(),
                            impact_level="CRITICAL",
                            fix_suggestion="Repository 패턴으로 추상화"
                        )
                    )

                # 외부 의존성 검사
                if self._is_external_dependency(line):
                    violations['external_dependencies'].append(
                        ViolationCase(
                            file_path=str(file_path),
                            line_number=line_no,
                            violation_type="External Dependency",
                            code_snippet=line.strip(),
                            impact_level="MEDIUM",
                            fix_suggestion="의존성 역전(DI) 적용"
                        )
                    )

                # 로깅 위반 검사
                if self._is_logging_violation(line):
                    violations['logging_violations'].append(
                        ViolationCase(
                            file_path=str(file_path),
                            line_number=line_no,
                            violation_type="Infrastructure Logging",
                            code_snippet=line.strip(),
                            impact_level="HIGH",
                            fix_suggestion="Domain Logger (Events 기반) 사용"
                        )
                    )

        except Exception:
            pass

        return violations

    def _is_infrastructure_import(self, line: str) -> bool:
        """Infrastructure import 검사"""
        patterns = [
            r'from upbit_auto_trading\.infrastructure',
            r'import upbit_auto_trading\.infrastructure'
        ]
        return any(re.search(pattern, line) for pattern in patterns)

    def _is_direct_db_access(self, line: str) -> bool:
        """직접 DB 접근 검사"""
        patterns = [
            r'import sqlite3',
            r'sqlite3\.',
            r'\.connect\(',
            r'\.execute\(',
            r'\.cursor\('
        ]
        return any(re.search(pattern, line) for pattern in patterns)

    def _is_external_dependency(self, line: str) -> bool:
        """외부 의존성 검사"""
        patterns = [
            r'import requests',
            r'import urllib',
            r'import json',
            r'import yaml',
            r'from PyQt6'
        ]
        return any(re.search(pattern, line) for pattern in patterns)

    def _is_logging_violation(self, line: str) -> bool:
        """로깅 위반 검사"""
        patterns = [
            r'create_component_logger',
            r'self\.logger\.',
            r'logger\.',
            r'print\('
        ]
        return any(re.search(pattern, line) for pattern in patterns)

    def generate_report(self) -> str:
        """분석 리포트 생성"""
        results = self.analyze_all()
        report = []

        report.append("# DDD Domain 계층 의존성 위반 분석 리포트")
        report.append("=" * 60)

        total_violations = sum(len(violations) for violations in results.values())
        report.append(f"📊 총 위반 사항: {total_violations}개")
        report.append("")

        for category, violations in results.items():
            if violations:
                report.append(f"## {category.replace('_', ' ').title()}: {len(violations)}개")
                report.append("")

                for violation in violations[:5]:  # 상위 5개만 표시
                    report.append(f"### 📍 {violation.file_path}:{violation.line_number}")
                    report.append(f"**유형**: {violation.violation_type}")
                    report.append(f"**영향도**: {violation.impact_level}")
                    report.append(f"**코드**: `{violation.code_snippet}`")
                    report.append(f"**해결방안**: {violation.fix_suggestion}")
                    report.append("")

                if len(violations) > 5:
                    report.append(f"... 외 {len(violations) - 5}개 사례")
                    report.append("")

        # 우선순위 제안
        report.append("## 🎯 수정 우선순위")
        critical_count = sum(1 for violations in results.values()
                           for v in violations if v.impact_level == "CRITICAL")
        high_count = sum(1 for violations in results.values()
                        for v in violations if v.impact_level == "HIGH")

        report.append(f"1. **CRITICAL ({critical_count}개)**: 직접 DB 접근 → Repository 패턴")
        report.append(f"2. **HIGH ({high_count}개)**: Infrastructure 의존성 → Domain Events")
        report.append("")

        return "\n".join(report)

def main():
    """메인 실행"""
    analyzer = DomainPurityAnalyzer()
    report = analyzer.generate_report()
    print(report)

    # 파일로 저장
    output_path = Path("tasks/analysis_domain_purity_violations.md")
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n📄 상세 리포트 저장됨: {output_path}")

if __name__ == "__main__":
    main()
