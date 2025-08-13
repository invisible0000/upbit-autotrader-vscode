#!/usr/bin/env python3
"""
레거시 패턴 및 하드코딩 탐지 도구

개발 중 레거시 패턴 사용을 방지하고 DDD 원칙 준수를 강제하는 도구입니다.
"""

import re
from pathlib import Path
from typing import List
from dataclasses import dataclass
from enum import Enum


class ViolationType(Enum):
    """위반 유형"""
    HARDCODED_PATH = "hardcoded_path"
    DEPRECATED_IMPORT = "deprecated_import"
    LAYER_VIOLATION = "layer_violation"
    PRINT_USAGE = "print_usage"
    HARDCODED_CONFIG = "hardcoded_config"
    LEGACY_PATTERN = "legacy_pattern"


@dataclass
class Violation:
    """위반 사항"""
    file_path: str
    line_number: int
    violation_type: ViolationType
    message: str
    code_snippet: str
    severity: str = "ERROR"


class LegacyDetector:
    """레거시 패턴 탐지기"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.violations: List[Violation] = []
        self.scanned_files = 0
        self.total_files = 0

        # 탐지 패턴 정의
        self.hardcoded_patterns = [
            r'Path\(__file__\)\.parents\[\d+\]',  # __file__ 기반 경로
            r'["\']data[/\\].*\.sqlite3["\']',     # 하드코딩된 DB 경로
            r'["\']config[/\\]',                   # 하드코딩된 config 경로
            r'["\']logs[/\\]',                     # 하드코딩된 logs 경로
            r'["\'][a-zA-Z_]+\.sqlite3["\']',      # 하드코딩된 DB 파일명
        ]

        self.deprecated_imports = [
            'from .paths import',
            'from upbit_auto_trading.infrastructure.configuration.paths',
            'import sqlite3',   # Domain에서 사용 금지
            'import requests',  # Domain에서 사용 금지
            'from PyQt6',       # Domain에서 사용 금지
        ]

        self.layer_violations = {
            'domain': [
                'sqlite3', 'requests', 'PyQt6', 'tkinter',
                'infrastructure', 'presentation'
            ],
            'presentation': [
                'sqlite3', 'sqlalchemy', 'requests'
            ]
        }

    def detect_all_violations(self) -> List[Violation]:
        """모든 위반 사항 탐지 - DDD 기반 설정 화면 영역 집중"""
        self.violations = []

        # 현재 개발 중인 DDD 기반 영역만 검사
        ddd_areas = [
            "upbit_auto_trading/domain/database_configuration",
            "upbit_auto_trading/infrastructure/configuration",
            "upbit_auto_trading/infrastructure/persistence",
            "upbit_auto_trading/infrastructure/services/api_key_service.py",
            "upbit_auto_trading/ui/desktop/screens/settings",
        ]

        py_files = []
        for area in ddd_areas:
            area_path = self.project_root / area
            if area_path.exists():
                if area_path.is_file():
                    py_files.append(area_path)
                else:
                    py_files.extend(list(area_path.rglob("*.py")))

        py_files = [f for f in py_files if not self._should_skip_file(f)]
        self.total_files = len(py_files)

        print(f"🔍 {self.total_files}개 파일 검사 시작...")

        for py_file in py_files:
            self.scanned_files += 1

            # 진행률 표시 (10% 단위)
            progress = (self.scanned_files / self.total_files) * 100
            if self.scanned_files % max(1, self.total_files // 10) == 0:
                print(f"   📂 진행률: {progress:.0f}% ({self.scanned_files}/{self.total_files})")

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()

                # 각종 위반 패턴 검사
                self._detect_hardcoded_paths(py_file, lines)
                self._detect_deprecated_imports(py_file, lines)
                self._detect_layer_violations(py_file, lines)
                self._detect_print_usage(py_file, lines)
                self._detect_legacy_patterns(py_file, lines)

            except Exception as e:
                print(f"⚠️ 파일 검사 실패: {py_file} - {e}")

        print(f"✅ 검사 완료: {self.scanned_files}개 파일, {len(self.violations)}개 위반사항 발견")
        return self.violations

    def _should_skip_file(self, file_path: Path) -> bool:
        """파일 스킵 여부 판단"""
        skip_dirs = {
            '__pycache__', '.git', 'venv', '.venv', 'node_modules',
            'tests', 'legacy', '.pytest_cache', 'dist', 'build',
            'upbit_auto_trading.egg-info'
        }        # 스킵할 디렉토리에 포함되어 있는지 확인
        return any(part in skip_dirs for part in file_path.parts)

    def _detect_hardcoded_paths(self, file_path: Path, lines: List[str]):
        """하드코딩된 경로 탐지"""
        for i, line in enumerate(lines, 1):
            for pattern in self.hardcoded_patterns:
                if re.search(pattern, line):
                    self.violations.append(Violation(
                        file_path=str(file_path),
                        line_number=i,
                        violation_type=ViolationType.HARDCODED_PATH,
                        message=f"하드코딩된 경로 발견: {pattern}",
                        code_snippet=line.strip(),
                        severity="ERROR"
                    ))

    def _detect_deprecated_imports(self, file_path: Path, lines: List[str]):
        """Deprecated import 탐지"""
        for i, line in enumerate(lines, 1):
            for deprecated in self.deprecated_imports:
                if deprecated in line and not line.strip().startswith('#'):
                    self.violations.append(Violation(
                        file_path=str(file_path),
                        line_number=i,
                        violation_type=ViolationType.DEPRECATED_IMPORT,
                        message=f"Deprecated import 사용: {deprecated}",
                        code_snippet=line.strip(),
                        severity="ERROR"
                    ))

    def _detect_layer_violations(self, file_path: Path, lines: List[str]):
        """DDD 계층 위반 탐지"""
        layer = self._get_layer_from_path(file_path)
        if not layer:
            return

        forbidden_imports = self.layer_violations.get(layer, [])

        for i, line in enumerate(lines, 1):
            if line.strip().startswith('import ') or 'from ' in line:
                for forbidden in forbidden_imports:
                    if forbidden in line and not line.strip().startswith('#'):
                        self.violations.append(Violation(
                            file_path=str(file_path),
                            line_number=i,
                            violation_type=ViolationType.LAYER_VIOLATION,
                            message=f"{layer.upper()} 계층에서 {forbidden} 사용 금지",
                            code_snippet=line.strip(),
                            severity="ERROR"
                        ))

    def _detect_print_usage(self, file_path: Path, lines: List[str]):
        """print() 사용 탐지 (Infrastructure 로깅 사용해야 함)"""
        for i, line in enumerate(lines, 1):
            if re.search(r'\bprint\s*\(', line) and not line.strip().startswith('#'):
                self.violations.append(Violation(
                    file_path=str(file_path),
                    line_number=i,
                    violation_type=ViolationType.PRINT_USAGE,
                    message="print() 대신 Infrastructure 로깅 사용",
                    code_snippet=line.strip(),
                    severity="WARNING"
                ))

    def _detect_legacy_patterns(self, file_path: Path, lines: List[str]):
        """기타 레거시 패턴 탐지"""
        legacy_patterns = [
            (r'\.legacy\b', "레거시 모듈 사용"),
            (r'simple_paths', "simple_paths 대신 DatabasePathService 사용"),
            (r'config\.yaml.*database', "하드코딩된 설정 파일 경로"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, message in legacy_patterns:
                if re.search(pattern, line) and not line.strip().startswith('#'):
                    self.violations.append(Violation(
                        file_path=str(file_path),
                        line_number=i,
                        violation_type=ViolationType.LEGACY_PATTERN,
                        message=message,
                        code_snippet=line.strip(),
                        severity="WARNING"
                    ))

    def _get_layer_from_path(self, file_path: Path) -> str:
        """파일 경로에서 DDD 계층 추출"""
        path_parts = file_path.parts

        if 'domain' in path_parts:
            return 'domain'
        elif 'infrastructure' in path_parts:
            return 'infrastructure'
        elif 'presentation' in path_parts or 'ui' in path_parts:
            return 'presentation'

        return ''

    def generate_report(self) -> str:
        """위반 사항 보고서 생성"""
        if not self.violations:
            return "🎉 레거시 패턴 및 위반 사항이 발견되지 않았습니다!"

        report = []
        report.append("=" * 60)
        report.append("🚨 레거시 패턴 및 DDD 위반 사항 탐지 보고서")
        report.append("=" * 60)
        report.append(f"총 {len(self.violations)}개의 위반 사항 발견\n")

        # 심각도별 그룹화
        errors = [v for v in self.violations if v.severity == "ERROR"]
        warnings = [v for v in self.violations if v.severity == "WARNING"]

        if errors:
            report.append(f"❌ ERROR: {len(errors)}개")
            for violation in errors:
                report.append(self._format_violation(violation))

        if warnings:
            report.append(f"⚠️ WARNING: {len(warnings)}개")
            for violation in warnings:
                report.append(self._format_violation(violation))

        report.append("\n" + "=" * 60)
        report.append("💡 해결 방법:")
        report.append("1. DatabasePathService 사용하여 경로 관리")
        report.append("2. Infrastructure 로깅 시스템 사용")
        report.append("3. DDD 계층 분리 원칙 준수")
        report.append("4. 하드코딩 대신 설정 파일 사용")

        return "\n".join(report)

    def _format_violation(self, violation: Violation) -> str:
        """위반 사항 포맷팅"""
        return (
            f"\n📍 {violation.file_path}:{violation.line_number}\n"
            f"   유형: {violation.violation_type.value}\n"
            f"   메시지: {violation.message}\n"
            f"   코드: {violation.code_snippet}"
        )


def main():
    """메인 실행 함수"""
    import sys

    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    detector = LegacyDetector(project_root)

    print("�️ DDD 및 레거시 패턴 검사 도구")
    print("=" * 50)
    violations = detector.detect_all_violations()

    print("\n" + "=" * 50)
    report = detector.generate_report()
    print(report)

    # 위반 사항이 있으면 종료 코드 1 반환 (CI/CD에서 활용)
    return 1 if any(v.severity == "ERROR" for v in violations) else 0


if __name__ == "__main__":
    exit(main())
