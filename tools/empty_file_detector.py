#!/usr/bin/env python3
"""
빈 파일 검출기
Python 프로젝트에서 빈 파일들을 찾고 분석

사용법:
python tools/empty_file_detector.py [경로]
python tools/empty_file_detector.py upbit_auto_trading
python tools/empty_file_detector.py .  # 전체 프로젝트
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import re

class EmptyFileInfo:
    """빈 파일 정보"""
    def __init__(self, path: Path):
        self.path = path
        self.relative_path = self._get_relative_path(path)
        self.file_name = path.stem
        self.last_modified = datetime.fromtimestamp(path.stat().st_mtime)
        self.is_init_file = path.name == "__init__.py"
        self.references = 0
        self.reference_files = []
        self.directory_type = self._classify_directory()
        self.deletion_safety = "UNKNOWN"

    def _get_relative_path(self, path: Path) -> str:
        """상대 경로 반환"""
        try:
            return str(path.relative_to(Path.cwd()))
        except ValueError:
            return str(path)

    def _classify_directory(self) -> str:
        """디렉토리 타입 분류"""
        path_str = str(self.path)

        if "domain" in path_str:
            if "entities" in path_str:
                return "Domain Entity"
            elif "value_objects" in path_str:
                return "Value Object"
            elif "services" in path_str:
                return "Domain Service"
            elif "repositories" in path_str:
                return "Repository Interface"
            return "Domain Layer"
        elif "application" in path_str:
            if "dtos" in path_str:
                return "Application DTO"
            elif "services" in path_str:
                return "Application Service"
            return "Application Layer"
        elif "infrastructure" in path_str:
            return "Infrastructure Layer"
        elif "ui" in path_str:
            return "UI Layer"

        return "Unknown"

class EmptyFileDetector:
    """빈 파일 검출기"""

    def __init__(self, root_path: str = "upbit_auto_trading"):
        self.root_path = Path(root_path)
        self.empty_files: List[EmptyFileInfo] = []
        self.all_python_files: List[Path] = []

    def scan_empty_files(self) -> List[EmptyFileInfo]:
        """빈 파일 스캔"""
        print(f"🔍 빈 파일 스캔 시작: {self.root_path}")

        # 모든 Python 파일 수집
        self.all_python_files = list(self.root_path.rglob("*.py"))
        total_files = len(self.all_python_files)

        # 빈 파일 찾기
        for py_file in self.all_python_files:
            if py_file.stat().st_size == 0:
                empty_info = EmptyFileInfo(py_file)
                self.empty_files.append(empty_info)

        print(f"📊 스캔 완료: 전체 {total_files}개 중 빈 파일 {len(self.empty_files)}개 발견")

        # 참조 분석
        self._analyze_references()

        # 삭제 안전성 평가
        self._assess_deletion_safety()

        return self.empty_files

    def _analyze_references(self):
        """참조 분석"""
        print("🔗 참조 분석 중...")

        for empty_file in self.empty_files:
            if empty_file.is_init_file:
                # __init__.py는 별도 처리
                empty_file.references = -1  # 특별 표시
                continue

            file_name = empty_file.file_name

            # 다른 모든 파일에서 이 파일명 검색
            for py_file in self.all_python_files:
                if py_file == empty_file.path:
                    continue

                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 파일명이 포함된 경우 참조로 간주
                    if file_name in content:
                        # 정확한 참조인지 검증
                        if self._is_actual_reference(content, file_name):
                            empty_file.references += 1
                            empty_file.reference_files.append(str(py_file))

                except (UnicodeDecodeError, PermissionError):
                    continue

    def _is_actual_reference(self, content: str, file_name: str) -> bool:
        """실제 참조인지 확인"""
        # import 문에서 참조
        import_patterns = [
            rf"from.*{file_name}.*import",
            rf"import.*{file_name}",
            rf"from.*{file_name}",
        ]

        for pattern in import_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        # 문자열 참조
        if f'"{file_name}"' in content or f"'{file_name}'" in content:
            return True

        # 클래스명 또는 함수명으로 사용
        # 단어 경계를 확인하여 정확한 매칭
        if re.search(rf'\b{file_name}\b', content):
            return True

        return False

    def _assess_deletion_safety(self):
        """삭제 안전성 평가"""
        print("⚖️ 삭제 안전성 평가 중...")

        for empty_file in self.empty_files:
            if empty_file.is_init_file:
                # __init__.py는 패키지 구조에 중요하므로 신중
                empty_file.deletion_safety = "CAUTION"
            elif empty_file.references == 0:
                # 참조가 없으면 안전
                empty_file.deletion_safety = "SAFE"
            elif empty_file.references <= 2:
                # 적은 참조는 검토 필요
                empty_file.deletion_safety = "REVIEW"
            else:
                # 많은 참조는 위험
                empty_file.deletion_safety = "DANGEROUS"

    def print_analysis_report(self):
        """분석 보고서 출력"""
        print(f"\n{'='*80}")
        print(f"📋 빈 파일 분석 보고서")
        print(f"{'='*80}")

        # 요약
        total = len(self.empty_files)
        safe_count = len([f for f in self.empty_files if f.deletion_safety == "SAFE"])
        caution_count = len([f for f in self.empty_files if f.deletion_safety == "CAUTION"])
        review_count = len([f for f in self.empty_files if f.deletion_safety == "REVIEW"])
        dangerous_count = len([f for f in self.empty_files if f.deletion_safety == "DANGEROUS"])

        print(f"📊 요약:")
        print(f"  전체 빈 파일: {total}개")
        print(f"  ✅ 안전한 삭제: {safe_count}개")
        print(f"  ⚠️ 주의 필요: {caution_count}개")
        print(f"  📋 검토 필요: {review_count}개")
        print(f"  🚨 위험: {dangerous_count}개")

        # 타입별 분류
        print(f"\n📁 타입별 분류:")
        type_groups = {}
        for empty_file in self.empty_files:
            dir_type = empty_file.directory_type
            if dir_type not in type_groups:
                type_groups[dir_type] = []
            type_groups[dir_type].append(empty_file)

        for dir_type, files in sorted(type_groups.items()):
            print(f"  {dir_type}: {len(files)}개")

        # 안전한 삭제 후보
        safe_files = [f for f in self.empty_files if f.deletion_safety == "SAFE"]
        if safe_files:
            print(f"\n✅ 안전한 삭제 후보 ({len(safe_files)}개):")
            for file_info in safe_files:
                print(f"  📄 {file_info.relative_path}")
                print(f"     타입: {file_info.directory_type}")
                print(f"     수정일: {file_info.last_modified.strftime('%Y-%m-%d %H:%M')}")

        # 검토 필요 파일
        review_files = [f for f in self.empty_files if f.deletion_safety == "REVIEW"]
        if review_files:
            print(f"\n📋 검토 필요 파일 ({len(review_files)}개):")
            for file_info in review_files:
                print(f"  📄 {file_info.relative_path}")
                print(f"     타입: {file_info.directory_type}")
                print(f"     참조 횟수: {file_info.references}")
                if file_info.reference_files:
                    print(f"     참조 파일: {file_info.reference_files[0]}")

        # 위험 파일
        dangerous_files = [f for f in self.empty_files if f.deletion_safety == "DANGEROUS"]
        if dangerous_files:
            print(f"\n🚨 삭제 위험 파일 ({len(dangerous_files)}개):")
            for file_info in dangerous_files:
                print(f"  📄 {file_info.relative_path}")
                print(f"     타입: {file_info.directory_type}")
                print(f"     참조 횟수: {file_info.references}")

        # 시간 패턴 분석
        print(f"\n⏰ 생성 시간 패턴:")
        time_groups = {}
        for empty_file in self.empty_files:
            time_key = empty_file.last_modified.strftime('%Y-%m-%d %H:%M')
            if time_key not in time_groups:
                time_groups[time_key] = 0
            time_groups[time_key] += 1

        for time_key, count in sorted(time_groups.items()):
            if count > 1:  # 2개 이상인 경우만 표시
                print(f"  {time_key}: {count}개 파일")

    def generate_cleanup_commands(self):
        """레거시 폴더로 이동 명령어 생성"""
        safe_files = [f for f in self.empty_files if f.deletion_safety == "SAFE"]

        if not safe_files:
            print("\n💡 안전한 이동 후보가 없습니다.")
            return

        # 타임스탬프 생성
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        legacy_dir = f"legacy/empty_files_cleanup_{timestamp}"

        print("\n🛠️ 안전한 파일 레거시 이동 명령어:")
        print(f"# 레거시 폴더: {legacy_dir}")
        print(f"# PowerShell 명령어 (안전한 {len(safe_files)}개 파일)")

        # 레거시 폴더 생성 명령
        print("\n# 1. 레거시 폴더 생성")
        print(f'New-Item -ItemType Directory -Path "{legacy_dir}" -Force')

        # 개별 파일 이동 명령
        print("\n# 2. 개별 파일 이동:")
        for file_info in safe_files:
            rel_path = file_info.relative_path.replace('\\', '/')
            file_name = Path(rel_path).name
            target_path = f"{legacy_dir}/{file_name}"
            print(f'Move-Item "{rel_path}" "{target_path}" -Force  # {file_info.directory_type}')

        # 일괄 이동 명령
        print("\n# 3. 또는 일괄 이동:")
        safe_paths = [f'"{f.relative_path.replace(chr(92), "/")}"' for f in safe_files]
        paths_str = ", ".join(safe_paths)
        print(f'$legacyDir = "{legacy_dir}"')
        print("New-Item -ItemType Directory -Path $legacyDir -Force | Out-Null")
        print(f"$safeFiles = @({paths_str})")
        print("$safeFiles | ForEach-Object { ")
        print("    $fileName = Split-Path $_ -Leaf")
        print("    $targetPath = Join-Path $legacyDir $fileName")
        print("    Move-Item $_ $targetPath -Force")
        print("    Write-Host \"이동됨: $_ → $targetPath\" -ForegroundColor Green")
        print("}")

        # 확인 명령
        print("\n# 4. 이동 확인:")
        print(f'Get-ChildItem "{legacy_dir}" | Select-Object Name, Length, LastWriteTime')

    def move_safe_files_to_legacy(self):
        """실제로 안전한 파일들을 레거시 폴더로 이동"""
        safe_files = [f for f in self.empty_files if f.deletion_safety == "SAFE"]

        if not safe_files:
            print("\n💡 이동할 안전한 파일이 없습니다.")
            return False

        # 타임스탬프 생성
        from datetime import datetime
        import shutil

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        legacy_dir = Path(f"legacy/empty_files_cleanup_{timestamp}")

        try:
            # 레거시 폴더 생성
            legacy_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 레거시 폴더 생성: {legacy_dir}")

            # 파일 이동
            moved_count = 0
            for file_info in safe_files:
                source = Path(file_info.relative_path)
                target = legacy_dir / source.name

                if source.exists():
                    shutil.move(str(source), str(target))
                    print(f"✅ 이동: {source} → {target}")
                    moved_count += 1
                else:
                    print(f"⚠️ 파일 없음: {source}")

            print(f"\n🎉 완료: {moved_count}개 파일이 레거시 폴더로 이동되었습니다.")
            print(f"📂 레거시 위치: {legacy_dir}")

            return True

        except Exception as e:
            print(f"❌ 이동 중 오류 발생: {e}")
            return False

def main():
    target_path = sys.argv[1] if len(sys.argv) > 1 else "upbit_auto_trading"

    if not Path(target_path).exists():
        print(f"❌ 경로를 찾을 수 없습니다: {target_path}")
        sys.exit(1)

    detector = EmptyFileDetector(target_path)
    detector.scan_empty_files()
    detector.print_analysis_report()
    detector.generate_cleanup_commands()

    # 추가 옵션: 실제 이동 실행
    if len(sys.argv) > 2 and sys.argv[2] == "--execute":
        print("\n🚀 실제 파일 이동을 시작합니다...")
        if detector.move_safe_files_to_legacy():
            print("✅ 파일 이동이 완료되었습니다.")
        else:
            print("❌ 파일 이동에 실패했습니다.")


if __name__ == "__main__":
    main()
