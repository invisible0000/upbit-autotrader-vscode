#!/usr/bin/env python3
"""
🔍 Super Legacy Detector v2.0
최고급 레거시 패턴 및 DDD 위반 탐지 도구

Features:
- 🎯 DDD 레이어별 집중 검사
- 📊 위험도 기반 우선순위
- 🔧 사용자 맞춤 필터링
- 📈 진행률 표시 및 성능 최적화
- 💡 실시간 해결 방법 제안
"""

import argparse
import re
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum, IntEnum
from concurrent.futures import ThreadPoolExecutor
import json


class SeverityLevel(IntEnum):
    """위험도 레벨 (숫자가 높을수록 위험)"""
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class ViolationType(Enum):
    """위반 유형"""
    HARDCODED_PATH = "hardcoded_path"
    DEPRECATED_IMPORT = "deprecated_import"
    LAYER_VIOLATION = "layer_violation"
    PRINT_USAGE = "print_usage"
    HARDCODED_CONFIG = "hardcoded_config"
    LEGACY_PATTERN = "legacy_pattern"
    DOMAIN_PURITY = "domain_purity"
    CIRCULAR_IMPORT = "circular_import"


@dataclass
class Violation:
    """위반 사항"""
    file_path: str
    line_number: int
    violation_type: ViolationType
    severity: SeverityLevel
    message: str
    code_snippet: str
    solution_hint: str = ""
    category: str = ""


class DddLayer(Enum):
    """DDD 계층"""
    DOMAIN = "domain"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"
    PRESENTATION = "presentation"


class SuperLegacyDetector:
    """최고급 레거시 패턴 탐지기"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.violations: List[Violation] = []

        # DDD 레이어별 검사 경로
        self.ddd_layer_paths = {
            DddLayer.DOMAIN: "upbit_auto_trading/domain",
            DddLayer.APPLICATION: "upbit_auto_trading/application",
            DddLayer.INFRASTRUCTURE: "upbit_auto_trading/infrastructure",
            DddLayer.PRESENTATION: "upbit_auto_trading/ui",
        }

        # 위험도 기반 탐지 패턴
        self.detection_rules = self._initialize_detection_rules()

        # 성능 최적화
        self.thread_pool_size = 4
        self.max_file_size = 1024 * 1024  # 1MB 제한

    def _initialize_detection_rules(self) -> Dict[ViolationType, Dict]:
        """탐지 규칙 초기화"""
        return {
            ViolationType.DOMAIN_PURITY: {
                'patterns': [
                    (r'from upbit_auto_trading\.infrastructure', SeverityLevel.CRITICAL),
                    (r'import sqlite3', SeverityLevel.CRITICAL),
                    (r'import requests', SeverityLevel.CRITICAL),
                    (r'from PyQt6', SeverityLevel.CRITICAL),
                ],
                'applicable_layers': [DddLayer.DOMAIN],
                'solution': "Domain 계층은 외부 의존성 없이 순수해야 합니다. Repository 인터페이스를 사용하세요."
            },

            ViolationType.HARDCODED_PATH: {
                'patterns': [
                    (r'Path\(__file__\)\.parents\[\d+\]', SeverityLevel.HIGH),
                    (r'["\']data[/\\].*\.sqlite3["\']', SeverityLevel.HIGH),
                    (r'["\'][a-zA-Z_]+\.sqlite3["\']', SeverityLevel.MEDIUM),
                    (r'["\']config[/\\]', SeverityLevel.MEDIUM),
                    (r'["\']logs[/\\]', SeverityLevel.LOW),
                ],
                'applicable_layers': [DddLayer.INFRASTRUCTURE, DddLayer.APPLICATION],
                'solution': "DatabasePathService 또는 설정 파일을 사용하여 경로를 관리하세요."
            },

            ViolationType.DEPRECATED_IMPORT: {
                'patterns': [
                    (r'from \.paths import', SeverityLevel.CRITICAL),
                    (r'from upbit_auto_trading\.infrastructure\.configuration\.paths', SeverityLevel.CRITICAL),
                    (r'import simple_paths', SeverityLevel.HIGH),
                ],
                'applicable_layers': [DddLayer.INFRASTRUCTURE, DddLayer.APPLICATION],
                'solution': "새로운 DDD 기반 DatabasePathService를 사용하세요."
            },

            ViolationType.LAYER_VIOLATION: {
                'patterns': [
                    (r'from upbit_auto_trading\.ui.*import', SeverityLevel.HIGH),  # Domain에서 UI import
                    (r'import tkinter', SeverityLevel.MEDIUM),
                ],
                'applicable_layers': [DddLayer.DOMAIN, DddLayer.APPLICATION],
                'solution': "DDD 계층 분리를 준수하세요. 상위 계층에서 하위 계층만 참조 가능합니다."
            },

            ViolationType.PRINT_USAGE: {
                'patterns': [
                    (r'\bprint\s*\(', SeverityLevel.LOW),
                ],
                'applicable_layers': [DddLayer.INFRASTRUCTURE, DddLayer.APPLICATION, DddLayer.DOMAIN],
                'solution': "Infrastructure 로깅 시스템(create_component_logger)을 사용하세요."
            },

            ViolationType.LEGACY_PATTERN: {
                'patterns': [
                    (r'\.legacy\b', SeverityLevel.MEDIUM),
                    (r'simple_paths', SeverityLevel.HIGH),
                    (r'config\.yaml.*database', SeverityLevel.LOW),
                ],
                'applicable_layers': list(DddLayer),
                'solution': "최신 DDD 패턴으로 리팩터링하세요."
            }
        }

    def scan(self,
             target_paths: Optional[List[str]] = None,
             layers: Optional[List[DddLayer]] = None,
             max_violations: int = 20,
             min_severity: SeverityLevel = SeverityLevel.HIGH,
             include_solutions: bool = True) -> List[Violation]:
        """
        레거시 패턴 스캔

        Args:
            target_paths: 특정 경로들 (None이면 DDD 레이어 경로)
            layers: 검사할 DDD 레이어들
            max_violations: 최대 위반사항 수
            min_severity: 최소 위험도
            include_solutions: 해결 방법 포함 여부
        """
        start_time = time.time()
        print("🔍 Super Legacy Detector v2.0 시작")
        print(f"📊 설정: 최대 {max_violations}개, 최소 위험도 {min_severity.name}")
        print("=" * 60)

        # 검사 대상 파일 수집
        target_files = self._collect_target_files(target_paths, layers)

        if not target_files:
            print("❌ 검사할 파일이 없습니다.")
            return []

        print(f"📁 {len(target_files)}개 파일 검사 시작...")

        # 병렬 처리로 성능 최적화
        self.violations = []
        with ThreadPoolExecutor(max_workers=self.thread_pool_size) as executor:
            futures = [executor.submit(self._scan_file, file_path) for file_path in target_files]

            completed = 0
            for future in futures:
                try:
                    future.result(timeout=5)  # 5초 타임아웃
                except Exception as e:
                    print(f"⚠️ 파일 스캔 실패: {e}")

                completed += 1
                if completed % max(1, len(target_files) // 10) == 0:
                    progress = (completed / len(target_files)) * 100
                    print(f"   📈 진행률: {progress:.0f}% ({completed}/{len(target_files)})")

        # 위험도 기반 정렬 및 필터링
        filtered_violations = [
            v for v in self.violations
            if v.severity >= min_severity
        ]

        # 위험도순 정렬 (CRITICAL -> HIGH -> MEDIUM -> LOW)
        filtered_violations.sort(key=lambda x: (-x.severity.value, x.file_path, x.line_number))

        # 최대 개수 제한
        result = filtered_violations[:max_violations]

        elapsed = time.time() - start_time
        print(f"✅ 검사 완료: {elapsed:.2f}초, {len(result)}개 위반사항 발견")

        return result

    def _collect_target_files(self, target_paths: Optional[List[str]], layers: Optional[List[DddLayer]]) -> List[Path]:
        """검사 대상 파일 수집"""
        target_files = []

        if target_paths:
            # 사용자 지정 경로
            for path_str in target_paths:
                path = self.project_root / path_str
                if path.is_file() and path.suffix == '.py':
                    target_files.append(path)
                elif path.is_dir():
                    target_files.extend(path.rglob("*.py"))
        else:
            # DDD 레이어 기반 검사
            layers = layers or [DddLayer.DOMAIN, DddLayer.INFRASTRUCTURE]  # 기본: 핵심 레이어만

            for layer in layers:
                layer_path = self.project_root / self.ddd_layer_paths[layer]
                if layer_path.exists():
                    target_files.extend(layer_path.rglob("*.py"))

        # 필터링: 제외할 파일들
        filtered_files = []
        skip_patterns = {
            '__pycache__', '.git', 'venv', '.venv', 'node_modules',
            'tests', 'legacy', '.pytest_cache', 'dist', 'build',
            'egg-info'
        }

        for file_path in target_files:
            # 크기 제한
            if file_path.stat().st_size > self.max_file_size:
                continue

            # 패턴 제외
            if any(pattern in str(file_path) for pattern in skip_patterns):
                continue

            filtered_files.append(file_path)

        return filtered_files

    def _scan_file(self, file_path: Path) -> None:
        """단일 파일 스캔"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()

            # 현재 파일의 DDD 레이어 감지
            current_layer = self._detect_layer(file_path)

            # 각 탐지 규칙 적용
            for violation_type, rule_config in self.detection_rules.items():
                if current_layer not in rule_config['applicable_layers']:
                    continue

                for pattern, severity in rule_config['patterns']:
                    self._check_pattern(file_path, lines, pattern, violation_type, severity, rule_config['solution'])

        except Exception as e:
            # 파일 읽기 실패는 조용히 넘어감
            pass

    def _check_pattern(self, file_path: Path, lines: List[str], pattern: str,
                      violation_type: ViolationType, severity: SeverityLevel, solution: str) -> None:
        """패턴 검사"""
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith('#'):  # 주석 무시
                continue

            if re.search(pattern, line):
                violation = Violation(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num,
                    violation_type=violation_type,
                    severity=severity,
                    message=self._generate_message(violation_type, pattern),
                    code_snippet=line.strip()[:100],  # 100자 제한
                    solution_hint=solution,
                    category=self._detect_layer(file_path).value
                )
                self.violations.append(violation)

    def _detect_layer(self, file_path: Path) -> DddLayer:
        """파일 경로에서 DDD 레이어 감지"""
        path_str = str(file_path)

        if '/domain/' in path_str or '\\domain\\' in path_str:
            return DddLayer.DOMAIN
        elif '/infrastructure/' in path_str or '\\infrastructure\\' in path_str:
            return DddLayer.INFRASTRUCTURE
        elif '/ui/' in path_str or '\\ui\\' in path_str:
            return DddLayer.PRESENTATION
        else:
            return DddLayer.APPLICATION

    def _generate_message(self, violation_type: ViolationType, pattern: str) -> str:
        """위반 메시지 생성"""
        messages = {
            ViolationType.DOMAIN_PURITY: f"🚨 Domain 순수성 위반: {pattern}",
            ViolationType.HARDCODED_PATH: f"📁 하드코딩된 경로: {pattern}",
            ViolationType.DEPRECATED_IMPORT: f"🔄 Deprecated import: {pattern}",
            ViolationType.LAYER_VIOLATION: f"🏗️ DDD 계층 위반: {pattern}",
            ViolationType.PRINT_USAGE: "📝 print() 사용 (로깅 시스템 사용 권장)",
            ViolationType.LEGACY_PATTERN: f"🔧 레거시 패턴: {pattern}",
        }
        return messages.get(violation_type, f"위반: {pattern}")

    def generate_report(self, violations: List[Violation], format_type: str = "console") -> str:
        """보고서 생성"""
        if not violations:
            return "🎉 위반사항이 발견되지 않았습니다!"

        if format_type == "json":
            return self._generate_json_report(violations)
        else:
            return self._generate_console_report(violations)

    def _generate_console_report(self, violations: List[Violation]) -> str:
        """콘솔 보고서 생성"""
        report = []
        report.append("🚨 Super Legacy Detector 보고서")
        report.append("=" * 60)
        report.append(f"총 {len(violations)}개 위반사항 발견\n")

        # 위험도별 그룹화
        by_severity = {}
        for violation in violations:
            severity = violation.severity
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(violation)

        # 위험도별 출력 (높은 것부터)
        severity_icons = {
            SeverityLevel.CRITICAL: "🔥",
            SeverityLevel.HIGH: "❌",
            SeverityLevel.MEDIUM: "⚠️",
            SeverityLevel.LOW: "💡",
        }

        for severity in sorted(by_severity.keys(), reverse=True):
            violations_list = by_severity[severity]
            icon = severity_icons.get(severity, "📌")
            report.append(f"{icon} {severity.name}: {len(violations_list)}개")

            for violation in violations_list:
                report.append(f"\n📍 {violation.file_path}:{violation.line_number}")
                report.append(f"   유형: {violation.violation_type.value}")
                report.append(f"   메시지: {violation.message}")
                report.append(f"   코드: {violation.code_snippet}")
                if violation.solution_hint:
                    report.append(f"   💡 해결: {violation.solution_hint}")

        # 요약 통계
        report.append("\n" + "=" * 60)
        report.append("📊 통계 요약:")
        report.append(f"   🎯 DDD Domain 위반: {sum(1 for v in violations if v.category == 'domain')}개")
        report.append(f"   🏗️ Infrastructure 문제: {sum(1 for v in violations if v.category == 'infrastructure')}개")
        report.append(f"   🖥️ Presentation 문제: {sum(1 for v in violations if v.category == 'presentation')}개")

        return "\n".join(report)

    def _generate_json_report(self, violations: List[Violation]) -> str:
        """JSON 보고서 생성"""
        data = {
            "summary": {
                "total_violations": len(violations),
                "by_severity": {},
                "by_category": {}
            },
            "violations": []
        }

        for violation in violations:
            # 요약 데이터
            severity_name = violation.severity.name
            data["summary"]["by_severity"][severity_name] = data["summary"]["by_severity"].get(severity_name, 0) + 1
            data["summary"]["by_category"][violation.category] = data["summary"]["by_category"].get(violation.category, 0) + 1

            # 상세 데이터
            data["violations"].append({
                "file": violation.file_path,
                "line": violation.line_number,
                "type": violation.violation_type.value,
                "severity": violation.severity.name,
                "message": violation.message,
                "code": violation.code_snippet,
                "solution": violation.solution_hint,
                "category": violation.category
            })

        return json.dumps(data, indent=2, ensure_ascii=False)


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="🔍 Super Legacy Detector v2.0 - 최고급 레거시 패턴 탐지",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "paths", nargs="*", default=None,
        help="검사할 경로들 (기본: DDD 핵심 레이어)"
    )

    parser.add_argument(
        "--layers", "-l", nargs="+",
        choices=["domain", "infrastructure", "presentation", "application"],
        help="검사할 DDD 레이어들"
    )

    parser.add_argument(
        "--max", "-m", type=int, default=20,
        help="최대 위반사항 수 (기본: 20)"
    )

    parser.add_argument(
        "--severity", "-s",
        choices=["info", "low", "medium", "high", "critical"],
        default="high",
        help="최소 위험도 (기본: high)"
    )

    parser.add_argument(
        "--format", "-f",
        choices=["console", "json"],
        default="console",
        help="출력 형식 (기본: console)"
    )

    parser.add_argument(
        "--project-root", "-r", default=".",
        help="프로젝트 루트 경로 (기본: 현재 디렉토리)"
    )

    args = parser.parse_args()

    # 파라미터 변환
    severity_map = {
        "info": SeverityLevel.INFO,
        "low": SeverityLevel.LOW,
        "medium": SeverityLevel.MEDIUM,
        "high": SeverityLevel.HIGH,
        "critical": SeverityLevel.CRITICAL
    }

    layer_map = {
        "domain": DddLayer.DOMAIN,
        "infrastructure": DddLayer.INFRASTRUCTURE,
        "presentation": DddLayer.PRESENTATION,
        "application": DddLayer.APPLICATION
    }

    # 스캔 실행
    detector = SuperLegacyDetector(args.project_root)

    layers = [layer_map[l] for l in args.layers] if args.layers else None
    violations = detector.scan(
        target_paths=args.paths,
        layers=layers,
        max_violations=args.max,
        min_severity=severity_map[args.severity]
    )

    # 보고서 출력
    report = detector.generate_report(violations, args.format)
    print("\n" + report)

    # 종료 코드: CRITICAL 또는 HIGH 위반이 있으면 1
    critical_or_high = any(v.severity >= SeverityLevel.HIGH for v in violations)
    return 1 if critical_or_high else 0


if __name__ == "__main__":
    exit(main())
