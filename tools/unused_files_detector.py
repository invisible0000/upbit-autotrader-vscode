#!/usr/bin/env python3
"""
Unused Files Detector - 미사용 파일 탐지 도구
==============================================

upbit_auto_trading 폴더 내에서 참조되지 않는 파일들을 탐지하는 도구

기능:
1. Python 파일들의 import 관계 분석
2. 참조되지 않는 파일 식별
3. 인터페이스 파일 중 구현체가 없는 파일 식별
4. 안전한 제거 후보 추천
"""

import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FileInfo:
    """파일 정보 데이터 클래스"""
    path: str
    size: int
    layer: str  # Domain, Application, Infrastructure, Presentation
    file_type: str  # interface, implementation, test, example, etc.
    imports: List[str]
    imported_by: List[str]
    is_referenced: bool
    risk_level: str  # safe, medium, dangerous
    recommendation: str


class UnusedFilesDetector:
    """미사용 파일 탐지기"""

    def __init__(self, root_path: str = "upbit_auto_trading"):
        self.root_path = Path(root_path)
        self.files_info: Dict[str, FileInfo] = {}
        self.import_graph: Dict[str, Set[str]] = {}
        self.reverse_import_graph: Dict[str, Set[str]] = {}

        # DDD Layer 패턴 정의
        self.layer_patterns = {
            "Domain": [r"domain/", r"entities/", r"value_objects/"],
            "Application": [r"application/", r"use_cases/", r"services/"],
            "Infrastructure": [r"infrastructure/", r"repositories/", r"external/"],
            "Presentation": [r"ui/", r"screens/", r"widgets/", r"presenters/"]
        }

        # 파일 타입 패턴 정의
        self.file_type_patterns = {
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

    def detect_layer(self, file_path: str) -> str:
        """파일의 DDD Layer 탐지"""
        try:
            rel_path = str(Path(file_path).relative_to(self.root_path))
        except ValueError:
            rel_path = file_path

        for layer, patterns in self.layer_patterns.items():
            for pattern in patterns:
                if re.search(pattern, rel_path):
                    return layer

        return "Unknown"

    def detect_file_type(self, file_path: str) -> str:
        """파일 타입 탐지"""
        try:
            rel_path = str(Path(file_path).relative_to(self.root_path))
        except ValueError:
            rel_path = file_path

        for file_type, patterns in self.file_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, rel_path):
                    return file_type

        return "implementation"

    def extract_imports(self, file_path: Path) -> List[str]:
        """파일에서 import 구문 추출"""
        imports = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 정규식으로 import 추출 (단순하지만 안정적)
            import_patterns = [
                r'from\s+(upbit_auto_trading[\w\.]*)\s+import',
                r'import\s+(upbit_auto_trading[\w\.]*)'
            ]

            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                imports.extend(matches)

        except Exception as e:
            print(f"⚠️ 파일 읽기 실패: {file_path} - {e}")

        return imports

    def scan_files(self) -> None:
        """모든 Python 파일 스캔"""
        print("🔍 Python 파일 스캔 시작...")

        for py_file in self.root_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            # 상대 경로 계산
            try:
                rel_path = str(py_file.relative_to(Path.cwd()))
            except ValueError:
                rel_path = str(py_file)

            # 파일 정보 수집
            imports = self.extract_imports(py_file)
            layer = self.detect_layer(str(py_file))
            file_type = self.detect_file_type(str(py_file))

            self.files_info[rel_path] = FileInfo(
                path=rel_path,
                size=py_file.stat().st_size,
                layer=layer,
                file_type=file_type,
                imports=imports,
                imported_by=[],
                is_referenced=False,
                risk_level="unknown",
                recommendation=""
            )

        print(f"✅ {len(self.files_info)}개 파일 스캔 완료")

    def analyze_references(self) -> None:
        """참조 관계 분석"""
        print("🔗 참조 관계 분석 중...")

        # 모든 파일을 검사하여 다른 파일들을 참조하는지 확인
        for file_path, file_info in self.files_info.items():
            for other_path in self.files_info.keys():
                if file_path == other_path:
                    continue

                # 파일 내용에서 다른 파일 참조 검사
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 다른 파일의 모듈명이 import 되는지 확인
                    other_module = other_path.replace('\\', '.').replace('/', '.').replace('.py', '')
                    if other_module in content:
                        self.files_info[other_path].imported_by.append(file_path)
                        self.files_info[other_path].is_referenced = True

                except Exception:
                    continue

            # 특별한 파일들은 항상 참조된 것으로 간주
            special_files = [
                "__init__.py",
                "main.py",
                "run_desktop_ui.py",
                "setup.py",
                "config.py"
            ]

            if any(special in file_path for special in special_files):
                file_info.is_referenced = True

        print("✅ 참조 관계 분석 완료")

    def assess_risk_and_recommendations(self) -> None:
        """위험도 평가 및 권장사항 생성"""
        print("⚖️ 위험도 평가 중...")

        for file_path, file_info in self.files_info.items():
            # 위험도 평가 로직
            risk_score = 0
            recommendations = []

            # 1. 참조되지 않는 파일
            if not file_info.is_referenced:
                risk_score -= 2
                recommendations.append("참조되지 않음")

            # 2. 파일 타입별 위험도
            if file_info.file_type in ["backup", "example", "test"]:
                risk_score -= 3
                recommendations.append(f"{file_info.file_type} 파일")
            elif file_info.file_type == "interface" and not file_info.is_referenced:
                risk_score -= 2
                recommendations.append("미사용 인터페이스")

            # 3. Layer 위치별 위험도
            if file_info.layer == "Presentation":
                risk_score -= 1  # UI는 상대적으로 안전
            elif file_info.layer == "Domain":
                risk_score += 3  # Domain은 매우 중요

            # 4. 파일 크기
            if file_info.size < 1000:  # 1KB 미만
                risk_score -= 1
                recommendations.append("작은 파일")

            # 5. 특수 파일 체크
            special_patterns = [
                "__init__", "main", "run_", "setup", "config"
            ]
            if any(pattern in file_path for pattern in special_patterns):
                risk_score += 5
                recommendations.append("시스템 핵심 파일")

            # 위험도 결정
            if risk_score <= -4:
                file_info.risk_level = "safe"
                file_info.recommendation = "안전한 제거 후보: " + ", ".join(recommendations)
            elif risk_score <= -1:
                file_info.risk_level = "medium"
                file_info.recommendation = "검토 후 제거 가능: " + ", ".join(recommendations)
            else:
                file_info.risk_level = "dangerous"
                file_info.recommendation = "제거 위험 - 유지 필요: " + ", ".join(recommendations)

        print("✅ 위험도 평가 완료")

    def generate_report(self) -> Dict:
        """분석 보고서 생성"""
        report = {
            "analysis_date": datetime.now().isoformat(),
            "total_files": len(self.files_info),
            "summary": {
                "safe_to_remove": 0,
                "review_needed": 0,
                "keep_files": 0,
                "unreferenced_files": 0
            },
            "by_layer": {},
            "by_type": {},
            "recommendations": {
                "safe_removal_candidates": [],
                "review_candidates": [],
                "keep_files": []
            }
        }

        # 통계 수집
        for file_info in self.files_info.values():
            if file_info.risk_level == "safe":
                report["summary"]["safe_to_remove"] += 1
                report["recommendations"]["safe_removal_candidates"].append(
                    asdict(file_info)
                )
            elif file_info.risk_level == "medium":
                report["summary"]["review_needed"] += 1
                report["recommendations"]["review_candidates"].append(
                    asdict(file_info)
                )
            else:
                report["summary"]["keep_files"] += 1
                report["recommendations"]["keep_files"].append(
                    asdict(file_info)
                )

            if not file_info.is_referenced:
                report["summary"]["unreferenced_files"] += 1

            # Layer별 통계
            if file_info.layer not in report["by_layer"]:
                report["by_layer"][file_info.layer] = {"total": 0, "unreferenced": 0}

            report["by_layer"][file_info.layer]["total"] += 1
            if not file_info.is_referenced:
                report["by_layer"][file_info.layer]["unreferenced"] += 1

            # 타입별 통계
            if file_info.file_type not in report["by_type"]:
                report["by_type"][file_info.file_type] = {"total": 0, "unreferenced": 0}

            report["by_type"][file_info.file_type]["total"] += 1
            if not file_info.is_referenced:
                report["by_type"][file_info.file_type]["unreferenced"] += 1

        return report

    def run_analysis(self) -> Dict:
        """전체 분석 실행"""
        print("🚀 미사용 파일 분석 시작...")

        self.scan_files()
        self.analyze_references()
        self.assess_risk_and_recommendations()

        report = self.generate_report()

        print("✅ 분석 완료!")
        return report


def main():
    """메인 실행 함수"""
    detector = UnusedFilesDetector()
    report = detector.run_analysis()

    # 보고서 저장
    with open("unused_files_analysis.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 요약 출력
    print("\n" + "="*50)
    print("📊 분석 결과 요약")
    print("="*50)
    print(f"📁 총 파일 수: {report['total_files']}")
    print(f"🗑️  안전한 제거 후보: {report['summary']['safe_to_remove']}")
    print(f"⚠️  검토 필요: {report['summary']['review_needed']}")
    print(f"🔒 유지 필요: {report['summary']['keep_files']}")
    print(f"❓ 참조되지 않는 파일: {report['summary']['unreferenced_files']}")

    print("\n📋 Layer별 현황:")
    for layer, stats in report['by_layer'].items():
        print(f"  {layer}: {stats['total']}개 (미참조: {stats['unreferenced']}개)")

    print("\n📋 타입별 현황:")
    for file_type, stats in report['by_type'].items():
        print(f"  {file_type}: {stats['total']}개 (미참조: {stats['unreferenced']}개)")

    print(f"\n💾 상세 보고서: unused_files_analysis.json")

    # 안전한 제거 후보 상위 10개 출력
    safe_candidates = report["recommendations"]["safe_removal_candidates"]
    if safe_candidates:
        print(f"\n🗑️  안전한 제거 후보 (상위 {min(10, len(safe_candidates))}개):")
        for i, candidate in enumerate(safe_candidates[:10], 1):
            print(f"  {i}. {candidate['path']}")
            print(f"     타입: {candidate['file_type']}, 크기: {candidate['size']}B")
            print(f"     이유: {candidate['recommendation']}")


if __name__ == "__main__":
    main()
