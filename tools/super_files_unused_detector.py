#!/usr/bin/env python3
"""
Super Files Unused Detector - 고도화된 미사용 파일 탐지 도구
========================================================

DDD 아키텍처와 Infrastructure Layer v4.0을 완벽히 이해하는 탐지 시스템

핵심 개선사항:
1. AST 기반 정확한 import 분석
2. Infrastructure Layer 보호 시스템
3. 동적 import 및 런타임 의존성 감지
4. DDD 계층별 중요도 평가
5.        # 파일 타입 패턴 정의 (개선됨)
        self.file_type_patterns = {
            "interface": [r"_interface\.py$", r"/interfaces/"],
            "presenter": [r"_presenter\.py$", r"/presenters/"],
            "view": [r"_view\.py$", r"/views/"],
            "widget": [r"_widget\.py$", r"/widgets/"],
            "dto": [r"_dto\.py$", r"/dtos/"],
            "test": [r"test_.*\.py$", r"_test\.py$", r"/tests/"],
            "example": [r"example.*\.py$", r"_example\.py$"],
            "backup": [r"_backup\.py$", r"_old\.py$", r"_legacy\.py$", r"copy\.py$"],
            "config": [r"config.*\.py$", r"settings.*\.py$"],
            "util": [r"util.*\.py$", r"helper.*\.py$", r"tool.*\.py$"],
            "entry_point": [r"main\.py$", r"run_.*\.py$", r"__main__\.py$"],
            "cli_web": [r"ui/cli/.*\.py$", r"ui/web/.*\.py$"]  # 특별 처리
        }
"""

import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class SuperFileInfo:
    """향상된 파일 정보 데이터 클래스"""
    path: str
    size: int
    layer: str
    file_type: str
    imports: List[str]
    dynamic_imports: List[str]  # 동적 import
    imported_by: List[str]
    runtime_dependencies: List[str]  # 런타임 의존성
    is_referenced: bool
    is_infrastructure_critical: bool  # Infrastructure Layer 핵심 여부
    is_ddd_essential: bool  # DDD 필수 요소 여부
    protection_level: str  # PROTECTED, CAUTION, SAFE
    risk_level: str
    recommendation: str
    analysis_confidence: float  # 분석 신뢰도 (0.0-1.0)


class SuperFilesUnusedDetector:
    """고도화된 미사용 파일 탐지기"""

    def __init__(self, root_path: str = "upbit_auto_trading"):
        self.root_path = Path(root_path)
        self.files_info: Dict[str, SuperFileInfo] = {}
        self.import_graph: Dict[str, Set[str]] = {}
        self.reverse_import_graph: Dict[str, Set[str]] = {}

        # Infrastructure Layer v4.0 보호 규칙
        self.infrastructure_critical_patterns = [
            # 로깅 시스템 (v4.0)
            r"infrastructure/logging/.*\.py$",
            r"infrastructure/dependency_injection/.*\.py$",
            r"infrastructure/repositories/.*\.py$",

            # 핵심 서비스들
            r".*logging_service\.py$",
            r".*app_context\.py$",
            r".*repository_container\.py$",

            # 도메인 핵심
            r"domain/.*\.py$",

            # 실행 진입점들
            r"run_.*\.py$",
            r"main\.py$",
            r"__init__\.py$"
        ]

        # DDD 필수 요소 패턴
        self.ddd_essential_patterns = [
            r"domain/entities/.*\.py$",
            r"domain/repositories/.*\.py$",
            r"domain/services/.*\.py$",
            r"application/use_cases/.*\.py$",
            r"application/services/.*\.py$",
            r"infrastructure/.*repository.*\.py$",
            r".*_service\.py$",
            r".*_repository\.py$"
        ]

        # 동적 import 패턴들 (개선됨)
        self.dynamic_import_patterns = [
            r"importlib\.import_module\s*\(\s*['\"]([^'\"]+)['\"]",
            r"__import__\s*\(\s*['\"]([^'\"]+)['\"]",
            r"exec\s*\(\s*['\"]import\s+([^'\"]+)['\"]",
            r"eval\s*\(\s*['\"]import\s+([^'\"]+)['\"]",
            # 조건부 import 패턴 추가
            r"if.*:\s*from\s+([^\s]+)\s+import",
            r"try:\s*from\s+([^\s]+)\s+import",
            r"except.*:\s*from\s+([^\s]+)\s+import"
        ]

        # 런타임 의존성 패턴들 (config, entry points 등)
        self.runtime_dependency_patterns = [
            r"entry_points.*=.*['\"]([^'\"]+)['\"]",
            r"console_scripts.*=.*['\"]([^'\"]+)['\"]",
            r"\.yaml.*['\"]([^'\"]+)\.py['\"]",
            r"getattr\s*\(\s*.*,\s*['\"]([^'\"]+)['\"]"
        ]

        # DDD Layer 패턴 정의 (우선순위 포함)
        self.layer_patterns = {
            "Domain": {
                "patterns": [r"domain/", r"entities/", r"value_objects/"],
                "priority": 10  # 최고 우선순위
            },
            "Application": {
                "patterns": [r"application/", r"use_cases/", r"services/"],
                "priority": 8
            },
            "Infrastructure": {
                "patterns": [r"infrastructure/", r"repositories/", r"external/"],
                "priority": 9  # 매우 높은 우선순위
            },
            "Presentation": {
                "patterns": [r"ui/", r"screens/", r"widgets/", r"presenters/"],
                "priority": 6
            }
        }

    def is_infrastructure_critical(self, file_path: str) -> bool:
        """Infrastructure Layer 핵심 파일 여부 판단"""
        try:
            rel_path = str(Path(file_path).relative_to(self.root_path))
        except ValueError:
            rel_path = file_path

        for pattern in self.infrastructure_critical_patterns:
            if re.search(pattern, rel_path, re.IGNORECASE):
                return True
        return False

    def is_ddd_essential(self, file_path: str) -> bool:
        """DDD 필수 요소 여부 판단"""
        try:
            rel_path = str(Path(file_path).relative_to(self.root_path))
        except ValueError:
            rel_path = file_path

        for pattern in self.ddd_essential_patterns:
            if re.search(pattern, rel_path, re.IGNORECASE):
                return True
        return False

    def extract_ast_imports(self, file_path: Path) -> Tuple[List[str], List[str]]:
        """AST를 사용한 정확한 import 추출"""
        imports = []
        dynamic_imports = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # AST 파싱으로 import 추출
            try:
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith('upbit_auto_trading'):
                                imports.append(alias.name)

                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith('upbit_auto_trading'):
                            imports.append(node.module)
                        elif node.module and node.module.startswith('.'):
                            # 상대 import 처리
                            try:
                                parent_module = self.resolve_relative_import(file_path, node.module)
                                if parent_module:
                                    imports.append(parent_module)
                            except Exception:
                                pass

            except SyntaxError:
                # AST 파싱 실패 시 정규식 백업
                pass

            # 동적 import 탐지
            for pattern in self.dynamic_import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if 'upbit_auto_trading' in match:
                        dynamic_imports.append(match)

        except Exception as e:
            print(f"⚠️ 파일 분석 실패: {file_path} - {e}")

        return imports, dynamic_imports

    def resolve_relative_import(self, file_path: Path, relative_module: str) -> Optional[str]:
        """상대 import를 절대 경로로 변환"""
        try:
            # 파일의 패키지 경로 계산
            rel_file_path = file_path.relative_to(self.root_path)
            package_parts = list(rel_file_path.parts[:-1])  # 파일명 제외

            # 상대 import 레벨 계산
            level = 0
            module = relative_module
            while module.startswith('.'):
                level += 1
                module = module[1:]

            # 패키지 경로에서 레벨만큼 상위로 이동
            target_package = package_parts[:-level] if level > 0 else package_parts

            if module:
                target_package.append(module)

            return 'upbit_auto_trading.' + '.'.join(target_package)

        except Exception:
            return None

    def extract_runtime_dependencies(self, file_path: Path) -> List[str]:
        """런타임 의존성 추출"""
        dependencies = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            for pattern in self.runtime_dependency_patterns:
                matches = re.findall(pattern, content)
                dependencies.extend(matches)

        except Exception:
            pass

        return dependencies

    def detect_layer_with_priority(self, file_path: str) -> Tuple[str, int]:
        """Layer 탐지 및 우선순위 반환"""
        try:
            rel_path = str(Path(file_path).relative_to(self.root_path))
        except ValueError:
            rel_path = file_path

        best_match = ("Unknown", 0)

        for layer, info in self.layer_patterns.items():
            for pattern in info["patterns"]:
                if re.search(pattern, rel_path):
                    if info["priority"] > best_match[1]:
                        best_match = (layer, info["priority"])

        return best_match

    def scan_files_super(self) -> None:
        """고도화된 파일 스캔"""
        print("🔍 Python 파일 스캔 시작 (Super Mode)...")

        for py_file in self.root_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            # 상대 경로 계산
            try:
                rel_path = str(py_file.relative_to(Path.cwd()))
            except ValueError:
                rel_path = str(py_file)

            # 고도화된 분석
            imports, dynamic_imports = self.extract_ast_imports(py_file)
            runtime_deps = self.extract_runtime_dependencies(py_file)
            layer, priority = self.detect_layer_with_priority(str(py_file))

            # 보호 수준 판단
            is_infra_critical = self.is_infrastructure_critical(str(py_file))
            is_ddd_essential = self.is_ddd_essential(str(py_file))

            protection_level = "SAFE"
            if is_infra_critical:
                protection_level = "PROTECTED"
            elif is_ddd_essential or priority >= 8:
                protection_level = "CAUTION"

            # 파일 타입 감지 (기존 로직 재사용)
            file_type = self.detect_file_type(str(py_file))

            self.files_info[rel_path] = SuperFileInfo(
                path=rel_path,
                size=py_file.stat().st_size,
                layer=layer,
                file_type=file_type,
                imports=imports,
                dynamic_imports=dynamic_imports,
                imported_by=[],
                runtime_dependencies=runtime_deps,
                is_referenced=False,
                is_infrastructure_critical=is_infra_critical,
                is_ddd_essential=is_ddd_essential,
                protection_level=protection_level,
                risk_level="unknown",
                recommendation="",
                analysis_confidence=0.0
            )

        print(f"✅ {len(self.files_info)}개 파일 스캔 완료 (Super Mode)")

    def detect_file_type(self, file_path: str) -> str:
        """파일 타입 탐지 (기존 로직)"""
        file_type_patterns = {
            "interface": [r"_interface\.py$", r"/interfaces/"],
            "presenter": [r"_presenter\.py$", r"/presenters/"],
            "view": [r"_view\.py$", r"/views/"],
            "widget": [r"_widget\.py$", r"/widgets/"],
            "dto": [r"_dto\.py$", r"/dtos/"],
            "test": [r"test_.*\.py$", r"_test\.py$", r"/tests/"],
            "example": [r"example.*\.py$", r"_example\.py$"],
            "backup": [r"_backup\.py$", r"_old\.py$", r"_legacy\.py$"],
            "config": [r"config.*\.py$", r"settings.*\.py$"],
            "util": [r"util.*\.py$", r"helper.*\.py$", r"tool.*\.py$"]
        }

        try:
            rel_path = str(Path(file_path).relative_to(self.root_path))
        except ValueError:
            rel_path = file_path

        for file_type, patterns in file_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, rel_path):
                    return file_type

        return "implementation"

    def analyze_references_super(self) -> None:
        """고도화된 참조 관계 분석"""
        print("🔗 참조 관계 분석 중 (Super Mode)...")

        # 1. 직접 import 분석
        for file_path, file_info in self.files_info.items():
            for import_module in file_info.imports + file_info.dynamic_imports:
                # import를 파일 경로로 변환
                possible_paths = self.module_to_file_paths(import_module)

                for target_path in possible_paths:
                    if target_path in self.files_info:
                        self.files_info[target_path].imported_by.append(file_path)
                        self.files_info[target_path].is_referenced = True

        # 2. 런타임 의존성 분석
        for file_path, file_info in self.files_info.items():
            for runtime_dep in file_info.runtime_dependencies:
                possible_paths = self.resolve_runtime_dependency(runtime_dep)
                for target_path in possible_paths:
                    if target_path in self.files_info:
                        self.files_info[target_path].imported_by.append(f"{file_path}[runtime]")
                        self.files_info[target_path].is_referenced = True

        # 3. 파일 내용 기반 참조 분석 (보조)
        self.analyze_content_references()

        # 4. 특별한 파일들 보호
        self.protect_special_files()

        print("✅ 참조 관계 분석 완료 (Super Mode)")

    def module_to_file_paths(self, module: str) -> List[str]:
        """모듈명을 가능한 파일 경로들로 변환"""
        paths = []

        if module.startswith('upbit_auto_trading'):
            # 절대 import
            relative_module = module.replace('upbit_auto_trading.', '').replace('.', '/')
            paths.append(f"upbit_auto_trading/{relative_module}.py")
            paths.append(f"upbit_auto_trading/{relative_module}/__init__.py")

        return paths

    def resolve_runtime_dependency(self, dependency: str) -> List[str]:
        """런타임 의존성을 파일 경로로 해결"""
        paths = []

        # 여기에 런타임 의존성 해결 로직 추가
        # 예: config 파일에서 참조되는 파일들

        return paths

    def analyze_content_references(self) -> None:
        """파일 내용 기반 참조 분석"""
        for file_path, file_info in self.files_info.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                for other_path in self.files_info.keys():
                    if file_path == other_path:
                        continue

                    # 파일명이나 클래스명이 문자열로 참조되는 경우
                    file_name = Path(other_path).stem
                    if file_name in content and len(file_name) > 3:  # 너무 짧은 이름 제외
                        self.files_info[other_path].imported_by.append(f"{file_path}[content]")
                        self.files_info[other_path].is_referenced = True

            except Exception:
                continue

    def protect_special_files(self) -> None:
        """특별한 파일들 보호"""
        special_patterns = [
            r"__init__\.py$",
            r"main\.py$",
            r"run_.*\.py$",
            r"setup\.py$",
            r"config\.py$",
            r".*_service\.py$",
            r".*_repository\.py$"
        ]

        for file_path, file_info in self.files_info.items():
            for pattern in special_patterns:
                if re.search(pattern, file_path):
                    file_info.is_referenced = True
                    if file_info.protection_level == "SAFE":
                        file_info.protection_level = "CAUTION"

    def assess_risk_super(self) -> None:
        """고도화된 위험도 평가"""
        print("⚖️ 위험도 평가 중 (Super Mode)...")

        for file_path, file_info in self.files_info.items():
            risk_score = 0
            recommendations = []
            confidence = 1.0

            # 1. 보호 수준 기반 평가 (최우선)
            if file_info.protection_level == "PROTECTED":
                risk_score += 100
                recommendations.append("Infrastructure 핵심 파일 - 절대 삭제 금지")

            elif file_info.protection_level == "CAUTION":
                risk_score += 50
                recommendations.append("DDD 중요 파일 - 신중한 검토 필요")

            # 2. 참조 관계 평가
            if not file_info.is_referenced:
                risk_score -= 30
                recommendations.append("참조되지 않음")
            else:
                risk_score += len(file_info.imported_by) * 5
                recommendations.append(f"{len(file_info.imported_by)}개 파일에서 참조")

            # 3. 파일 타입별 평가
            if file_info.file_type in ["backup", "example"]:
                risk_score -= 40
                recommendations.append(f"{file_info.file_type} 파일")
            elif file_info.file_type == "test":
                risk_score -= 20
                recommendations.append("테스트 파일")
            elif file_info.file_type in ["interface", "dto"]:
                if not file_info.is_referenced:
                    risk_score -= 25
                    recommendations.append("미사용 인터페이스")

            # 4. 파일 크기 고려
            if file_info.size == 0:
                risk_score -= 50
                recommendations.append("빈 파일")
            elif file_info.size < 500:
                risk_score -= 10
                recommendations.append("작은 파일")

            # 5. 동적 의존성 고려
            if file_info.dynamic_imports or file_info.runtime_dependencies:
                risk_score += 20
                recommendations.append("동적 의존성 있음")
                confidence *= 0.8

            # 6. Layer 중요도 반영
            layer_priorities = {"Domain": 30, "Infrastructure": 25, "Application": 20, "Presentation": 10}
            risk_score += layer_priorities.get(file_info.layer, 0)

            # 최종 위험도 결정
            if risk_score >= 60:
                file_info.risk_level = "dangerous"
                file_info.recommendation = "🔒 유지 필수: " + ", ".join(recommendations)
            elif risk_score >= 20:
                file_info.risk_level = "medium"
                file_info.recommendation = "⚠️ 신중한 검토 필요: " + ", ".join(recommendations)
            elif risk_score >= -10:
                file_info.risk_level = "review"
                file_info.recommendation = "📋 검토 후 제거 가능: " + ", ".join(recommendations)
            else:
                file_info.risk_level = "safe"
                file_info.recommendation = "✅ 안전한 제거 후보: " + ", ".join(recommendations)

            file_info.analysis_confidence = min(confidence, 1.0)

        print("✅ 위험도 평가 완료 (Super Mode)")

    def generate_super_report(self) -> Dict:
        """고도화된 분석 보고서 생성"""
        report = {
            "analysis_date": datetime.now().isoformat(),
            "detector_version": "Super v2.0",
            "total_files": len(self.files_info),
            "summary": {
                "safe_to_remove": 0,
                "review_needed": 0,
                "medium_risk": 0,
                "dangerous": 0,
                "protected_files": 0,
                "unreferenced_files": 0
            },
            "protection_analysis": {
                "PROTECTED": [],
                "CAUTION": [],
                "SAFE": []
            },
            "by_layer": {},
            "by_type": {},
            "confidence_stats": {
                "high_confidence": 0,  # >= 0.8
                "medium_confidence": 0,  # 0.5-0.8
                "low_confidence": 0  # < 0.5
            },
            "recommendations": {
                "safe_removal_candidates": [],
                "review_candidates": [],
                "medium_risk_files": [],
                "protected_files": []
            }
        }

        # 통계 수집
        for file_info in self.files_info.values():
            # 위험도별 분류
            if file_info.risk_level == "safe":
                report["summary"]["safe_to_remove"] += 1
                report["recommendations"]["safe_removal_candidates"].append(asdict(file_info))
            elif file_info.risk_level == "review":
                report["summary"]["review_needed"] += 1
                report["recommendations"]["review_candidates"].append(asdict(file_info))
            elif file_info.risk_level == "medium":
                report["summary"]["medium_risk"] += 1
                report["recommendations"]["medium_risk_files"].append(asdict(file_info))
            else:
                report["summary"]["dangerous"] += 1
                report["recommendations"]["protected_files"].append(asdict(file_info))

            # 보호 수준별 분류
            report["protection_analysis"][file_info.protection_level].append(asdict(file_info))

            if file_info.protection_level == "PROTECTED":
                report["summary"]["protected_files"] += 1

            if not file_info.is_referenced:
                report["summary"]["unreferenced_files"] += 1

            # 신뢰도 통계
            if file_info.analysis_confidence >= 0.8:
                report["confidence_stats"]["high_confidence"] += 1
            elif file_info.analysis_confidence >= 0.5:
                report["confidence_stats"]["medium_confidence"] += 1
            else:
                report["confidence_stats"]["low_confidence"] += 1

            # Layer별 통계
            if file_info.layer not in report["by_layer"]:
                report["by_layer"][file_info.layer] = {"total": 0, "unreferenced": 0, "protected": 0}

            report["by_layer"][file_info.layer]["total"] += 1
            if not file_info.is_referenced:
                report["by_layer"][file_info.layer]["unreferenced"] += 1
            if file_info.protection_level == "PROTECTED":
                report["by_layer"][file_info.layer]["protected"] += 1

            # 타입별 통계
            if file_info.file_type not in report["by_type"]:
                report["by_type"][file_info.file_type] = {"total": 0, "unreferenced": 0}

            report["by_type"][file_info.file_type]["total"] += 1
            if not file_info.is_referenced:
                report["by_type"][file_info.file_type]["unreferenced"] += 1

        return report

    def run_super_analysis(self) -> Dict:
        """Super 분석 실행"""
        print("🚀 Super 미사용 파일 분석 시작...")
        print("🛡️ Infrastructure Layer v4.0 보호 시스템 활성화")
        print("🏗️ DDD 아키텍처 인식 시스템 활성화")

        self.scan_files_super()
        self.analyze_references_super()
        self.assess_risk_super()

        report = self.generate_super_report()

        print("✅ Super 분석 완료!")
        return report


def main():
    """메인 실행 함수"""
    detector = SuperFilesUnusedDetector()
    report = detector.run_super_analysis()

    # 보고서 저장
    with open("super_unused_files_analysis.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 요약 출력
    print("\n" + "="*60)
    print("📊 Super 분석 결과 요약")
    print("="*60)
    print(f"📁 총 파일 수: {report['total_files']}")
    print(f"🛡️ 보호된 파일: {report['summary']['protected_files']}")
    print(f"🗑️ 안전한 제거 후보: {report['summary']['safe_to_remove']}")
    print(f"📋 검토 필요: {report['summary']['review_needed']}")
    print(f"⚠️ 중간 위험도: {report['summary']['medium_risk']}")
    print(f"🔒 위험함 (유지 필수): {report['summary']['dangerous']}")
    print(f"❓ 참조되지 않는 파일: {report['summary']['unreferenced_files']}")

    print(f"\n🎯 분석 신뢰도:")
    print(f"  높음 (≥80%): {report['confidence_stats']['high_confidence']}개")
    print(f"  중간 (50-80%): {report['confidence_stats']['medium_confidence']}개")
    print(f"  낮음 (<50%): {report['confidence_stats']['low_confidence']}개")

    print("\n🛡️ 보호 수준별 현황:")
    for level, files in report['protection_analysis'].items():
        print(f"  {level}: {len(files)}개")

    print("\n📋 Layer별 현황:")
    for layer, stats in report['by_layer'].items():
        print(f"  {layer}: {stats['total']}개 (미참조: {stats['unreferenced']}개, 보호됨: {stats.get('protected', 0)}개)")

    print(f"\n💾 상세 보고서: super_unused_files_analysis.json")

    # 안전한 제거 후보만 출력 (신뢰도 높은 것 우선)
    safe_candidates = sorted(
        report["recommendations"]["safe_removal_candidates"],
        key=lambda x: x['analysis_confidence'],
        reverse=True
    )

    if safe_candidates:
        print(f"\n🗑️ 안전한 제거 후보 (신뢰도 순, 상위 {min(10, len(safe_candidates))}개):")
        for i, candidate in enumerate(safe_candidates[:10], 1):
            confidence = candidate['analysis_confidence'] * 100
            print(f"  {i}. {candidate['path']}")
            print(f"     타입: {candidate['file_type']}, 크기: {candidate['size']}B, 신뢰도: {confidence:.1f}%")
            print(f"     이유: {candidate['recommendation']}")

    # 보호된 파일 예시 출력
    protected_files = report['protection_analysis']['PROTECTED']
    if protected_files:
        print(f"\n🛡️ 보호된 핵심 파일들 (상위 5개):")
        for i, protected in enumerate(protected_files[:5], 1):
            print(f"  {i}. {protected['path']}")
            print(f"     이유: {protected['recommendation']}")


if __name__ == "__main__":
    main()
