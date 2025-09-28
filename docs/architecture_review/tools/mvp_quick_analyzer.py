#!/usr/bin/env python3
"""
MVP 패턴 빠른 분석기 - Architecture Review System v1.0

업비트 자동매매 시스템의 MVP(Model-View-Presenter) 패턴 준수성을
빠르게 분석하는 도구입니다.

Usage:
    python mvp_quick_analyzer.py --component settings_screen
    python mvp_quick_analyzer.py --scan-all-ui
    python mvp_quick_analyzer.py --violations-only
"""

import os
import re
import glob
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from enum import Enum

class ViolationType(Enum):
    """위반 사항 유형"""
    VIEW_BUSINESS_LOGIC = "VIEW_BUSINESS_LOGIC"     # View에 비즈니스 로직 포함
    VIEW_INFRASTRUCTURE = "VIEW_INFRASTRUCTURE"     # View에서 Infrastructure 접근
    PRESENTER_UI_DIRECT = "PRESENTER_UI_DIRECT"     # Presenter에서 UI 직접 조작
    MISSING_INTERFACE = "MISSING_INTERFACE"         # 인터페이스 미사용
    LAYER_VIOLATION = "LAYER_VIOLATION"             # 계층 위반
    CIRCULAR_DEPENDENCY = "CIRCULAR_DEPENDENCY"     # 순환 의존성

class Severity(Enum):
    """심각도"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class Violation:
    """위반 사항"""
    file_path: str
    line_number: int
    violation_type: ViolationType
    severity: Severity
    description: str
    code_snippet: str
    suggestion: str

class MVPQuickAnalyzer:
    """MVP 패턴 빠른 분석기"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.ui_base_path = self.project_root / "upbit_auto_trading" / "ui" / "desktop"
        self.violations: List[Violation] = []

        # 패턴 정의
        self.view_violation_patterns = {
            # View에서 비즈니스 로직 수행 패턴
            r'class.*View.*:.*\n.*def.*validate': ViolationType.VIEW_BUSINESS_LOGIC,
            r'class.*View.*:.*\n.*def.*save_to_': ViolationType.VIEW_INFRASTRUCTURE,
            r'class.*View.*:.*\n.*def.*load_from_': ViolationType.VIEW_INFRASTRUCTURE,

            # Infrastructure 레이어 직접 접근
            r'from.*infrastructure.*import': ViolationType.VIEW_INFRASTRUCTURE,
            r'import sqlite3': ViolationType.VIEW_INFRASTRUCTURE,
            r'import requests': ViolationType.VIEW_INFRASTRUCTURE,

            # Application/Domain 서비스 직접 호출
            r'\.save\(\)': ViolationType.VIEW_BUSINESS_LOGIC,
            r'\.delete\(\)': ViolationType.VIEW_BUSINESS_LOGIC,
            r'\.update\(\)': ViolationType.VIEW_BUSINESS_LOGIC,
        }

        self.presenter_violation_patterns = {
            # Presenter에서 UI 위젯 직접 조작
            r'\.setText\(': ViolationType.PRESENTER_UI_DIRECT,
            r'\.setEnabled\(': ViolationType.PRESENTER_UI_DIRECT,
            r'\.setVisible\(': ViolationType.PRESENTER_UI_DIRECT,
            r'\.show\(\)': ViolationType.PRESENTER_UI_DIRECT,
            r'\.hide\(\)': ViolationType.PRESENTER_UI_DIRECT,

            # Infrastructure 직접 접근
            r'from.*infrastructure.*import': ViolationType.LAYER_VIOLATION,
            r'sqlite3\.': ViolationType.LAYER_VIOLATION,
            r'requests\.': ViolationType.LAYER_VIOLATION,
        }

    def analyze_component(self, component_name: str) -> List[Violation]:
        """특정 컴포넌트 분석"""
        component_path = self.ui_base_path / "screens" / component_name
        if not component_path.exists():
            print(f"❌ 컴포넌트 경로가 존재하지 않습니다: {component_path}")
            return []

        print(f"🔍 {component_name} 컴포넌트 분석 시작...")

        # Python 파일 수집
        py_files = list(component_path.rglob("*.py"))
        print(f"📁 분석 대상 파일: {len(py_files)}개")

        for py_file in py_files:
            self._analyze_file(py_file)

        return self.violations

    def analyze_all_ui(self) -> List[Violation]:
        """전체 UI 컴포넌트 분석"""
        print("🔍 전체 UI 컴포넌트 스캔 시작...")

        ui_files = list(self.ui_base_path.rglob("*.py"))
        print(f"📁 분석 대상 파일: {len(ui_files)}개")

        for py_file in ui_files:
            self._analyze_file(py_file)

        return self.violations

    def _analyze_file(self, file_path: Path):
        """개별 파일 분석"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # 파일 유형 판단
            is_view = self._is_view_file(file_path, content)
            is_presenter = self._is_presenter_file(file_path, content)

            if is_view:
                self._analyze_view_violations(file_path, content, lines)
            elif is_presenter:
                self._analyze_presenter_violations(file_path, content, lines)

        except Exception as e:
            print(f"⚠️ 파일 분석 중 오류 발생: {file_path} - {e}")

    def _is_view_file(self, file_path: Path, content: str) -> bool:
        """View 파일 여부 판단"""
        indicators = [
            'QWidget', 'QDialog', 'QMainWindow',
            'class.*View', 'class.*Screen', 'class.*Dialog'
        ]
        return any(re.search(pattern, content) for pattern in indicators)

    def _is_presenter_file(self, file_path: Path, content: str) -> bool:
        """Presenter 파일 여부 판단"""
        indicators = [
            'class.*Presenter', 'presenter', 'Presenter'
        ]
        return any(re.search(pattern, content) for pattern in indicators)

    def _analyze_view_violations(self, file_path: Path, content: str, lines: List[str]):
        """View 파일 위반 사항 분석"""
        for pattern, violation_type in self.view_violation_patterns.items():
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1

                violation = Violation(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num,
                    violation_type=violation_type,
                    severity=self._get_severity(violation_type),
                    description=self._get_description(violation_type, match.group()),
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else "",
                    suggestion=self._get_suggestion(violation_type)
                )
                self.violations.append(violation)

    def _analyze_presenter_violations(self, file_path: Path, content: str, lines: List[str]):
        """Presenter 파일 위반 사항 분석"""
        for pattern, violation_type in self.presenter_violation_patterns.items():
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1

                violation = Violation(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num,
                    violation_type=violation_type,
                    severity=self._get_severity(violation_type),
                    description=self._get_description(violation_type, match.group()),
                    code_snippet=lines[line_num - 1] if line_num <= len(lines) else "",
                    suggestion=self._get_suggestion(violation_type)
                )
                self.violations.append(violation)

    def _get_severity(self, violation_type: ViolationType) -> Severity:
        """위반 유형별 심각도 결정"""
        severity_map = {
            ViolationType.VIEW_INFRASTRUCTURE: Severity.CRITICAL,
            ViolationType.LAYER_VIOLATION: Severity.CRITICAL,
            ViolationType.CIRCULAR_DEPENDENCY: Severity.CRITICAL,
            ViolationType.VIEW_BUSINESS_LOGIC: Severity.HIGH,
            ViolationType.PRESENTER_UI_DIRECT: Severity.HIGH,
            ViolationType.MISSING_INTERFACE: Severity.MEDIUM,
        }
        return severity_map.get(violation_type, Severity.LOW)

    def _get_description(self, violation_type: ViolationType, matched_text: str) -> str:
        """위반 유형별 설명"""
        descriptions = {
            ViolationType.VIEW_BUSINESS_LOGIC: f"View에서 비즈니스 로직 수행: {matched_text}",
            ViolationType.VIEW_INFRASTRUCTURE: f"View에서 Infrastructure 직접 접근: {matched_text}",
            ViolationType.PRESENTER_UI_DIRECT: f"Presenter에서 UI 직접 조작: {matched_text}",
            ViolationType.LAYER_VIOLATION: f"계층 경계 위반: {matched_text}",
            ViolationType.MISSING_INTERFACE: f"인터페이스 미사용: {matched_text}",
            ViolationType.CIRCULAR_DEPENDENCY: f"순환 의존성: {matched_text}",
        }
        return descriptions.get(violation_type, f"알 수 없는 위반: {matched_text}")

    def _get_suggestion(self, violation_type: ViolationType) -> str:
        """위반 유형별 개선 제안"""
        suggestions = {
            ViolationType.VIEW_BUSINESS_LOGIC: "비즈니스 로직을 Presenter로 이동하고 시그널로 통신하세요",
            ViolationType.VIEW_INFRASTRUCTURE: "Infrastructure 접근을 Application Service로 위임하세요",
            ViolationType.PRESENTER_UI_DIRECT: "View 인터페이스 메서드를 통해 UI를 조작하세요",
            ViolationType.LAYER_VIOLATION: "올바른 계층 순서를 따라 의존성을 설정하세요",
            ViolationType.MISSING_INTERFACE: "추상화된 인터페이스를 정의하고 사용하세요",
            ViolationType.CIRCULAR_DEPENDENCY: "의존성 방향을 재설계하여 순환 참조를 제거하세요",
        }
        return suggestions.get(violation_type, "아키텍처 가이드를 참조하여 수정하세요")

    def generate_report(self, output_path: str = None) -> str:
        """분석 보고서 생성"""
        if not self.violations:
            return "🎉 위반 사항이 발견되지 않았습니다!"

        # 심각도별 분류
        critical = [v for v in self.violations if v.severity == Severity.CRITICAL]
        high = [v for v in self.violations if v.severity == Severity.HIGH]
        medium = [v for v in self.violations if v.severity == Severity.MEDIUM]
        low = [v for v in self.violations if v.severity == Severity.LOW]

        report = []
        report.append("# 🚨 MVP 패턴 분석 보고서")
        report.append("")
        report.append(f"**분석 일시**: {self._get_timestamp()}")
        report.append(f"**총 위반 수**: {len(self.violations)}건")
        report.append("")

        report.append("## 📊 심각도별 위반 현황")
        report.append("")
        report.append(f"- 🚨 **Critical**: {len(critical)}건 (즉시 해결 필요)")
        report.append(f"- ⚠️ **High**: {len(high)}건 (단기 해결 필요)")
        report.append(f"- 📋 **Medium**: {len(medium)}건 (중기 해결 대상)")
        report.append(f"- 📝 **Low**: {len(low)}건 (장기 개선 대상)")
        report.append("")

        # 위반 사항별 상세 정보
        for severity, violations, icon in [
            (Severity.CRITICAL, critical, "🚨"),
            (Severity.HIGH, high, "⚠️"),
            (Severity.MEDIUM, medium, "📋"),
            (Severity.LOW, low, "📝")
        ]:
            if violations:
                report.append(f"## {icon} {severity.value} 위반 사항")
                report.append("")

                for i, violation in enumerate(violations, 1):
                    report.append(f"### {i}. {violation.description}")
                    report.append("")
                    report.append(f"**📍 위치**: `{violation.file_path}:{violation.line_number}`")
                    report.append("")
                    report.append("**🔍 문제 코드**:")
                    report.append("```python")
                    report.append(violation.code_snippet)
                    report.append("```")
                    report.append("")
                    report.append(f"**💡 개선 방안**: {violation.suggestion}")
                    report.append("")
                    report.append("---")
                    report.append("")

        # 다음 단계 제안
        report.append("## 🎯 다음 단계")
        report.append("")
        if critical:
            report.append("1. **즉시 해결**: Critical 위반 사항부터 우선 해결")
        if high:
            report.append("2. **단기 계획**: High 위반 사항 해결 태스크 생성")
        if medium or low:
            report.append("3. **장기 계획**: Medium/Low 위반 사항 개선 로드맵 수립")

        report.append("")
        report.append("## 📋 위반 사항 등록")
        report.append("")
        report.append("발견된 위반 사항을 다음 위치에 등록하세요:")
        report.append("- `docs/architecture_review/violation_registry/active_violations.md`")
        report.append("- 템플릿: `docs/architecture_review/violation_registry/templates/violation_report_template.md`")

        report_content = "\n".join(report)

        # 파일 저장 (옵션)
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"📄 보고서가 저장되었습니다: {output_path}")

        return report_content

    def _get_timestamp(self) -> str:
        """현재 타임스탬프"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="MVP 패턴 빠른 분석기")
    parser.add_argument("--component", help="분석할 컴포넌트명 (예: settings_screen)")
    parser.add_argument("--scan-all-ui", action="store_true", help="전체 UI 컴포넌트 스캔")
    parser.add_argument("--violations-only", action="store_true", help="위반 사항만 표시")
    parser.add_argument("--output", help="보고서 저장 파일 경로")

    args = parser.parse_args()

    analyzer = MVPQuickAnalyzer()

    # 분석 실행
    if args.component:
        violations = analyzer.analyze_component(args.component)
    elif args.scan_all_ui:
        violations = analyzer.analyze_all_ui()
    else:
        # 기본: settings_screen 분석
        violations = analyzer.analyze_component("settings_screen")

    # 결과 출력
    if args.violations_only:
        # 위반 사항만 간단히 출력
        for v in violations:
            print(f"{v.severity.value}: {v.file_path}:{v.line_number} - {v.description}")
    else:
        # 전체 보고서 출력
        report = analyzer.generate_report(args.output)
        print(report)

    print(f"\n✅ 분석 완료: 총 {len(violations)}건의 위반 사항 발견")

if __name__ == "__main__":
    main()
