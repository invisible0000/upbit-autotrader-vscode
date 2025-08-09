"""
빈 패키지 검출기

Python 패키지 구조에서 실질적으로 빈 폴더를 검출합니다.
- __init__.py만 있는 폴더
- __init__.py + __pycache__만 있는 폴더
- 모든 .py 파일이 빈 파일인 폴더
- 실제 기능 코드가 없는 폴더
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List
from datetime import datetime
import ast


@dataclass
class PackageInfo:
    """패키지 정보"""
    path: Path
    relative_path: str
    package_type: str
    total_files: int
    python_files: int
    empty_files: int
    meaningful_files: int
    has_init: bool
    init_content_lines: int
    folder_purpose: str
    deletion_safety: str
    subdirectories: List[str]
    file_list: List[str]


class EmptyPackageDetector:
    """빈 패키지 검출기"""

    def __init__(self, target_path: str):
        self.target_path = Path(target_path).resolve()
        self.empty_packages: List[PackageInfo] = []
        self.excluded_dirs = {
            '__pycache__', '.git', '.vscode', 'node_modules',
            '.pytest_cache', '.mypy_cache', 'logs', 'temp'
        }

    def is_meaningful_python_file(self, file_path: Path) -> bool:
        """의미있는 Python 파일인지 판단"""
        if not file_path.suffix == '.py':
            return False

        if file_path.stat().st_size == 0:
            return False

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # 주석과 빈 줄 제거
            meaningful_lines = []
            for line in content.splitlines():
                line = line.strip()
                if (line and not line.startswith('#') and
                        not line.startswith('"""') and
                        not line.startswith("'''")):
                    meaningful_lines.append(line)

            # docstring만 있는 파일 체크
            if len(meaningful_lines) <= 3:
                # 간단한 AST 파싱으로 실제 코드 확인
                try:
                    tree = ast.parse(content)
                    # import문, 클래스 정의, 함수 정의가 있으면 의미있는 파일
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef,
                                             ast.FunctionDef, ast.AsyncFunctionDef)):
                            return True
                    return False
                except Exception:
                    return len(meaningful_lines) > 1

            return len(meaningful_lines) > 3

        except Exception:
            return False

    def get_init_content_lines(self, init_path: Path) -> int:
        """__init__.py의 의미있는 코드 줄 수 계산"""
        if not init_path.exists():
            return 0

        try:
            content = init_path.read_text(encoding='utf-8', errors='ignore')
            meaningful_lines = 0

            for line in content.splitlines():
                line = line.strip()
                if (line and
                    not line.startswith('#') and
                    not line.startswith('"""') and
                    not line.startswith("'''") and
                    line != ''):
                    meaningful_lines += 1

            return meaningful_lines

        except Exception:
            return 0

    def classify_package_type(self, package_path: Path) -> str:
        """패키지 타입 분류"""
        relative_parts = package_path.relative_to(self.target_path).parts

        if 'domain' in relative_parts:
            if 'entities' in relative_parts:
                return "Domain Entity"
            elif 'services' in relative_parts:
                return "Domain Service"
            elif 'repositories' in relative_parts:
                return "Repository Interface"
            elif 'value_objects' in relative_parts:
                return "Value Object"
            elif 'aggregates' in relative_parts:
                return "Aggregate"
            else:
                return "Domain Layer"
        elif 'application' in relative_parts:
            if 'use_cases' in relative_parts:
                return "Use Case"
            elif 'dto' in relative_parts:
                return "Application DTO"
            elif 'services' in relative_parts:
                return "Application Service"
            else:
                return "Application Layer"
        elif 'infrastructure' in relative_parts:
            if 'repositories' in relative_parts:
                return "Repository Implementation"
            elif 'external' in relative_parts:
                return "External Service"
            else:
                return "Infrastructure Layer"
        elif 'ui' in relative_parts:
            return "Presentation Layer"
        elif 'tests' in relative_parts:
            return "Test Package"
        else:
            return "Root Package"

    def determine_folder_purpose(self, package_info: PackageInfo) -> str:
        """폴더 목적 판단"""
        if package_info.meaningful_files > 0:
            return "Active Package"
        elif package_info.has_init and package_info.init_content_lines > 5:
            return "Namespace Package"
        elif package_info.has_init and package_info.init_content_lines > 0:
            return "Import Package"
        elif package_info.has_init:
            return "Empty Package"
        elif package_info.total_files == 0:
            return "Empty Directory"
        else:
            return "Non-Python Directory"

    def assess_deletion_safety(self, package_info: PackageInfo) -> str:
        """삭제 안전성 평가"""
        if package_info.meaningful_files > 0:
            return "DANGEROUS"
        elif package_info.folder_purpose == "Namespace Package":
            return "REVIEW_NEEDED"
        elif package_info.folder_purpose == "Import Package":
            return "CAUTION"
        elif package_info.folder_purpose == "Empty Package":
            return "SAFE"
        elif package_info.folder_purpose == "Empty Directory":
            return "SAFE"
        else:
            return "CAUTION"

    def scan_empty_packages(self):
        """빈 패키지 스캔"""
        print(f"🔍 빈 패키지 스캔 시작: {self.target_path.name}")

        for package_path in self.target_path.rglob('*'):
            if not package_path.is_dir():
                continue

            # 제외 디렉토리 스킵
            if any(excluded in package_path.parts for excluded in self.excluded_dirs):
                continue

            # 파일 분석
            all_files = list(package_path.iterdir())
            python_files = [f for f in all_files if f.suffix == '.py']
            init_file = package_path / '__init__.py'

            empty_files = 0
            meaningful_files = 0

            for py_file in python_files:
                if self.is_meaningful_python_file(py_file):
                    meaningful_files += 1
                elif py_file.stat().st_size == 0:
                    empty_files += 1

            # 빈 패키지 후보 판단
            if (len(python_files) > 0 and meaningful_files == 0) or (init_file.exists() and meaningful_files == 0):
                package_info = PackageInfo(
                    path=package_path,
                    relative_path=str(package_path.relative_to(self.target_path.parent)),
                    package_type=self.classify_package_type(package_path),
                    total_files=len(all_files),
                    python_files=len(python_files),
                    empty_files=empty_files,
                    meaningful_files=meaningful_files,
                    has_init=init_file.exists(),
                    init_content_lines=self.get_init_content_lines(init_file),
                    folder_purpose="",
                    deletion_safety="",
                    subdirectories=[d.name for d in all_files if d.is_dir() and d.name not in self.excluded_dirs],
                    file_list=[f.name for f in all_files if f.is_file()]
                )

                package_info.folder_purpose = self.determine_folder_purpose(package_info)
                package_info.deletion_safety = self.assess_deletion_safety(package_info)

                self.empty_packages.append(package_info)

        print(f"📊 스캔 완료: {len(self.empty_packages)}개 빈 패키지 후보 발견")

    def print_analysis_report(self):
        """분석 보고서 출력"""
        if not self.empty_packages:
            print("\n✅ 빈 패키지가 발견되지 않았습니다.")
            return

        print("\n" + "=" * 80)
        print("📁 빈 패키지 분석 보고서")
        print("=" * 80)

        # 요약 통계
        safety_counts = {}
        purpose_counts = {}
        type_counts = {}

        for pkg in self.empty_packages:
            safety_counts[pkg.deletion_safety] = safety_counts.get(pkg.deletion_safety, 0) + 1
            purpose_counts[pkg.folder_purpose] = purpose_counts.get(pkg.folder_purpose, 0) + 1
            type_counts[pkg.package_type] = type_counts.get(pkg.package_type, 0) + 1

        print(f"📊 요약:")
        print(f"  전체 빈 패키지: {len(self.empty_packages)}개")
        for safety, count in safety_counts.items():
            safety_icon = {"SAFE": "✅", "CAUTION": "⚠️", "REVIEW_NEEDED": "📋", "DANGEROUS": "🚨"}.get(safety, "❓")
            print(f"  {safety_icon} {safety}: {count}개")

        print(f"\n📁 목적별 분류:")
        for purpose, count in purpose_counts.items():
            print(f"  {purpose}: {count}개")

        print(f"\n🏗️ 타입별 분류:")
        for pkg_type, count in type_counts.items():
            print(f"  {pkg_type}: {count}개")

        # 안전한 삭제 후보
        safe_packages = [pkg for pkg in self.empty_packages if pkg.deletion_safety == "SAFE"]
        if safe_packages:
            print(f"\n✅ 안전한 삭제 후보 ({len(safe_packages)}개):")
            for pkg in safe_packages:
                print(f"  📁 {pkg.relative_path}")
                print(f"     목적: {pkg.folder_purpose}")
                print(f"     파일: {pkg.total_files}개 (Python: {pkg.python_files}개)")
                if pkg.has_init:
                    print(f"     __init__.py: {pkg.init_content_lines}줄")

        # 위험한 패키지
        dangerous_packages = [pkg for pkg in self.empty_packages if pkg.deletion_safety == "DANGEROUS"]
        if dangerous_packages:
            print(f"\n🚨 삭제 위험 패키지 ({len(dangerous_packages)}개):")
            for pkg in dangerous_packages:
                print(f"  📁 {pkg.relative_path}")
                print(f"     의미있는 파일: {pkg.meaningful_files}개")

        # 검토 필요
        review_packages = [pkg for pkg in self.empty_packages if pkg.deletion_safety in ["CAUTION", "REVIEW_NEEDED"]]
        if review_packages:
            print(f"\n📋 검토 필요 ({len(review_packages)}개):")
            for pkg in review_packages:
                print(f"  📁 {pkg.relative_path}")
                print(f"     목적: {pkg.folder_purpose}")
                print(f"     타입: {pkg.package_type}")
                if pkg.subdirectories:
                    print(f"     하위 디렉토리: {', '.join(pkg.subdirectories)}")

    def generate_cleanup_commands(self):
        """정리 명령어 생성"""
        safe_packages = [pkg for pkg in self.empty_packages if pkg.deletion_safety == "SAFE"]

        if not safe_packages:
            print("\n💡 안전한 삭제 후보가 없습니다.")
            return

        # 타임스탬프 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        legacy_dir = f"legacy/empty_packages_cleanup_{timestamp}"

        print("\n🛠️ 안전한 패키지 레거시 이동 명령어:")
        print(f"# 레거시 폴더: {legacy_dir}")
        print(f"# PowerShell 명령어 (안전한 {len(safe_packages)}개 패키지)")

        # 레거시 폴더 생성
        print("\n# 1. 레거시 폴더 생성")
        print(f'New-Item -ItemType Directory -Path "{legacy_dir}" -Force')

        # 개별 폴더 이동
        print("\n# 2. 개별 패키지 이동:")
        for pkg in safe_packages:
            rel_path = pkg.relative_path.replace('\\', '/')
            folder_name = Path(rel_path).name
            target_path = f"{legacy_dir}/{folder_name}"
            print(f'Move-Item "{rel_path}" "{target_path}" -Force  # {pkg.folder_purpose}')

        # 확인 명령
        print("\n# 3. 이동 확인:")
        print(f'Get-ChildItem "{legacy_dir}" | Select-Object Name, LastWriteTime')


def main():
    target_path = sys.argv[1] if len(sys.argv) > 1 else "upbit_auto_trading"

    if not Path(target_path).exists():
        print(f"❌ 경로를 찾을 수 없습니다: {target_path}")
        sys.exit(1)

    detector = EmptyPackageDetector(target_path)
    detector.scan_empty_packages()
    detector.print_analysis_report()
    detector.generate_cleanup_commands()


if __name__ == "__main__":
    main()
