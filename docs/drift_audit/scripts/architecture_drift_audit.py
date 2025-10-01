"""Architecture & Policy Drift Audit (Minimal v0.1)

목적:
- DDD 레이어 규칙 위반(금지 import) 기본 스캔
- print() 직접 호출 검사 (로깅 정책 위반 후보)
- 결과를 표준 JSON 구조로 출력 (stdout)

사용 예 (PowerShell):
    python docs/drift_audit/scripts/architecture_drift_audit.py --root . --output docs/drift_audit/reports/latest.json

제한:
- 정적 문자열 패턴 기반 (AST 미사용 - 후속 버전 확장 예정)
- 심볼 해석 미수행, 단순 경로/텍스트 기반

향후 확장 포인트:
- AST 파싱으로 default argument (dry_run=True) 검증
- Domain 레이어 외부 의존성 transitive import 탐지
- Drift Score 계산 통합
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Iterable

# 금지 패턴 정의
FORBIDDEN_IN_DOMAIN = [
    re.compile(r"^\s*import\s+sqlite3"),
    re.compile(r"^\s*import\s+requests"),
    re.compile(r"^\s*from\s+requests"),
    re.compile(r"^\s*from\s+PyQt6"),
    re.compile(r"^\s*import\s+PyQt6"),
]

PRINT_PATTERN = re.compile(r"(^|[^a-zA-Z0-9_])print\(")  # naive


@dataclass
class Finding:
    file: str
    line_no: int
    severity: str
    category: str
    pattern: str
    line: str
    rule: str


@dataclass
class AuditResult:
    generated_at: str
    root: str
    findings: List[Finding]
    summary: Dict[str, Any]
    version: str = "0.1.0"
    kind: str = "architecture_drift_audit"

    def to_json(self) -> str:
        return json.dumps(
            {
                "generated_at": self.generated_at,
                "root": self.root,
                "version": self.version,
                "kind": self.kind,
                "summary": self.summary,
                "findings": [asdict(f) for f in self.findings],
            },
            ensure_ascii=False,
            indent=2,
        )


def iter_python_files(root: str) -> Iterable[str]:
    for dirpath, _, filenames in os.walk(root):
        if ".venv" in dirpath or "__pycache__" in dirpath:
            continue
        for fn in filenames:
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def scan_domain_forbidden(domain_root: str) -> List[Finding]:
    findings: List[Finding] = []
    for file_path in iter_python_files(domain_root):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f, start=1):
                for regex in FORBIDDEN_IN_DOMAIN:
                    if regex.search(line):
                        findings.append(
                            Finding(
                                file=file_path,
                                line_no=idx,
                                severity="High",
                                category="forbidden_import",
                                pattern=regex.pattern,
                                line=line.rstrip(),
                                rule="domain_no_external_dependency",
                            )
                        )
    return findings


def scan_print_calls(root: str) -> List[Finding]:
    findings: List[Finding] = []
    for file_path in iter_python_files(root):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f, start=1):
                if "print(" in line and "create_component_logger" not in line:
                    findings.append(
                        Finding(
                            file=file_path,
                            line_no=idx,
                            severity="Medium",
                            category="print_usage",
                            pattern="print(",
                            line=line.rstrip(),
                            rule="no_direct_print",
                        )
                    )
    return findings


def summarize(findings: List[Finding]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "total": len(findings),
        "by_category": {},
        "by_severity": {},
    }
    for f in findings:
        summary["by_category"].setdefault(f.category, 0)
        summary["by_category"][f.category] += 1
        summary["by_severity"].setdefault(f.severity, 0)
        summary["by_severity"][f.severity] += 1
    return summary


def run_audit(root: str) -> AuditResult:
    domain_root = os.path.join(root, "upbit_auto_trading", "domain")
    findings: List[Finding] = []
    if os.path.isdir(domain_root):
        findings.extend(scan_domain_forbidden(domain_root))
    else:
        print(f"[WARN] domain root not found: {domain_root}", file=sys.stderr)

    findings.extend(scan_print_calls(os.path.join(root, "upbit_auto_trading")))

    return AuditResult(
        generated_at=datetime.now(timezone.utc).isoformat(),
        root=os.path.abspath(root),
        findings=findings,
        summary=summarize(findings),
    )


def main():
    parser = argparse.ArgumentParser(description="Architecture & Policy Drift Audit")
    parser.add_argument("--root", default=".", help="리포지토리 루트 경로")
    parser.add_argument("--output", help="JSON 출력 경로 (지정 안 하면 stdout)")
    args = parser.parse_args()

    result = run_audit(args.root)
    output_json = result.to_json()

    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(args.output)
    else:
        print(output_json)


if __name__ == "__main__":  # pragma: no cover
    main()
