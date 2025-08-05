#!/usr/bin/env python3
"""
로깅 시스템 마이그레이션 스크립트

목적: 기존 `upbit_auto_trading.utils.debug_logger`를 새로운 `upbit_auto_trading.logging` 시스템으로 변환

변환 내용:
1. import 구문 변경:
   - 기존: from upbit_auto_trading.logging import get_integrated_logger
   - 신규: from upbit_auto_trading.logging import get_integrated_logger

2. logger 생성 구문 변경:
   - 기존: logger = get_integrated_logger("LoggingMigrationTool") 또는 get_logger("ComponentName")
   - 신규: logger = get_integrated_logger("ComponentName")

3. 추가 패턴들:
   - 기존: from upbit_auto_trading import logging as upbit_logging
   - 신규: from upbit_auto_trading import logging

안전성 보장:
- 실제 파일 수정 전에 백업 생성
- 변경 사항 미리보기 제공
- 실행 전 사용자 확인 요청
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Tuple, Dict
import datetime


class LoggingMigrationTool:
    """로깅 시스템 마이그레이션 도구"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.backup_dir = self.project_root / "backups" / f"logging_migration_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 변환 패턴 정의
        self.patterns = [
            # 패턴 1: from upbit_auto_trading.logging import get_integrated_logger
            {
                "name": "utils.debug_logger import",
                "search": r"from\s+upbit_auto_trading\.utils\.debug_logger\s+import\s+get_logger",
                "replace": "from upbit_auto_trading.logging import get_integrated_logger",
                "description": "기존 utils.debug_logger의 get_logger import를 새 logging 시스템으로 변경"
            },

            # 패턴 2: from upbit_auto_trading import logging as upbit_logging
            {
                "name": "utils import debug_logger",
                "search": r"from\s+upbit_auto_trading\.utils\s+import\s+debug_logger",
                "replace": "from upbit_auto_trading import logging as upbit_logging",
                "description": "utils 모듈의 debug_logger import를 logging 모듈로 변경"
            },

            # 패턴 3: logger = get_integrated_logger("LoggingMigrationTool")
            {
                "name": "get_logger with __name__",
                "search": r"logger\s*=\s*get_logger\s*\(\s*__name__\s*\)",
                "replace": lambda match, filename: f"logger = get_integrated_logger(\"{self._extract_component_name(filename)}\")",
                "description": "get_logger(__name__)를 파일명 기반 get_integrated_logger로 변경"
            },

            # 패턴 4: logger = get_integrated_logger("ComponentName")
            {
                "name": "get_logger with string",
                "search": r"logger\s*=\s*get_logger\s*\(\s*[\"']([^\"']+)[\"']\s*\)",
                "replace": r'logger = get_integrated_logger("\1")',
                "description": "get_logger(\"ComponentName\")를 get_integrated_logger로 변경"
            },

            # 패턴 5: debug_logger.get_logger() 형태
            {
                "name": "debug_logger.get_logger",
                "search": r"debug_logger\.get_logger\s*\(\s*([^)]+)\s*\)",
                "replace": r"upbit_logging.get_integrated_logger(\1)",
                "description": "debug_logger.get_logger() 호출을 새 시스템으로 변경"
            }
        ]

        # 처리할 파일 확장자
        self.file_extensions = ['.py']

        # 제외할 디렉토리
        self.exclude_dirs = {
            '__pycache__', '.git', '.pytest_cache', 'venv', 'env',
            'node_modules', '.vscode', 'backups', 'legacy'
        }

    def _extract_component_name(self, filepath: Path) -> str:
        """파일 경로에서 컴포넌트명 추출

        예: upbit_auto_trading/ui/desktop/main_window.py -> MainWindow
        """
        filename = filepath.stem

        # 파일명을 PascalCase로 변환
        # main_window -> MainWindow
        # api_key_manager -> ApiKeyManager
        words = filename.split('_')
        component_name = ''.join(word.capitalize() for word in words if word)

        return component_name

    def find_python_files(self) -> List[Path]:
        """프로젝트에서 Python 파일 찾기"""
        python_files = []

        for root, dirs, files in os.walk(self.project_root):
            # 제외 디렉토리 필터링
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                if any(file.endswith(ext) for ext in self.file_extensions):
                    filepath = Path(root) / file
                    python_files.append(filepath)

        return python_files

    def analyze_file(self, filepath: Path) -> Dict:
        """파일 분석하여 변경 필요한 부분 찾기"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # UTF-8로 읽기 실패 시 다른 인코딩 시도
            try:
                with open(filepath, 'r', encoding='cp949') as f:
                    content = f.read()
            except:
                return {"error": "인코딩 오류로 파일 읽기 실패"}
        except Exception as e:
            return {"error": f"파일 읽기 실패: {e}"}

        analysis = {
            "filepath": filepath,
            "original_content": content,
            "matches": [],
            "needs_change": False
        }

        # 각 패턴에 대해 검사
        for pattern in self.patterns:
            matches = list(re.finditer(pattern["search"], content, re.MULTILINE))

            if matches:
                analysis["needs_change"] = True
                for match in matches:
                    line_start = content.rfind('\n', 0, match.start()) + 1
                    line_end = content.find('\n', match.end())
                    if line_end == -1:
                        line_end = len(content)

                    line_number = content[:match.start()].count('\n') + 1
                    line_content = content[line_start:line_end]

                    # 대체 텍스트 생성
                    if callable(pattern["replace"]):
                        replacement = pattern["replace"](match, filepath)
                    else:
                        replacement = re.sub(pattern["search"], pattern["replace"], match.group(0))

                    analysis["matches"].append({
                        "pattern_name": pattern["name"],
                        "description": pattern["description"],
                        "line_number": line_number,
                        "original_text": match.group(0),
                        "replacement_text": replacement,
                        "line_content": line_content,
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    })

        return analysis

    def preview_changes(self, files_to_check: List[Path] = None) -> Dict:
        """변경 사항 미리보기"""
        if files_to_check is None:
            files_to_check = self.find_python_files()

        preview_result = {
            "total_files": len(files_to_check),
            "files_to_change": [],
            "files_with_errors": [],
            "summary": {}
        }

        pattern_counts = {pattern["name"]: 0 for pattern in self.patterns}

        print(f"🔍 {len(files_to_check)}개 Python 파일 분석 중...")

        for filepath in files_to_check:
            analysis = self.analyze_file(filepath)

            if "error" in analysis:
                preview_result["files_with_errors"].append({
                    "filepath": filepath,
                    "error": analysis["error"]
                })
                continue

            if analysis["needs_change"]:
                preview_result["files_to_change"].append(analysis)

                # 패턴별 카운트 업데이트
                for match in analysis["matches"]:
                    pattern_counts[match["pattern_name"]] += 1

        preview_result["summary"] = {
            "files_needing_change": len(preview_result["files_to_change"]),
            "files_with_errors": len(preview_result["files_with_errors"]),
            "pattern_counts": pattern_counts,
            "total_replacements": sum(pattern_counts.values())
        }

        return preview_result

    def create_backup(self, files_to_backup: List[Path]):
        """백업 생성"""
        print(f"💾 백업 생성 중: {self.backup_dir}")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        for filepath in files_to_backup:
            relative_path = filepath.relative_to(self.project_root)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(filepath, backup_path)

        print(f"✅ {len(files_to_backup)}개 파일 백업 완료")

    def apply_changes(self, preview_result: Dict, create_backup: bool = True) -> Dict:
        """변경 사항 적용"""
        if create_backup:
            files_to_backup = [analysis["filepath"] for analysis in preview_result["files_to_change"]]
            self.create_backup(files_to_backup)

        apply_result = {
            "successful_files": [],
            "failed_files": [],
            "total_replacements": 0
        }

        print(f"🔧 {len(preview_result['files_to_change'])}개 파일 변경 적용 중...")

        for analysis in preview_result["files_to_change"]:
            try:
                # 변경 사항을 뒤에서부터 적용 (위치가 변경되지 않도록)
                content = analysis["original_content"]
                matches = sorted(analysis["matches"], key=lambda x: x["start_pos"], reverse=True)

                for match in matches:
                    # 원본 텍스트를 대체 텍스트로 교체
                    content = (
                        content[:match["start_pos"]] +
                        match["replacement_text"] +
                        content[match["end_pos"]:]
                    )
                    apply_result["total_replacements"] += 1

                # 파일에 저장
                with open(analysis["filepath"], 'w', encoding='utf-8') as f:
                    f.write(content)

                apply_result["successful_files"].append(analysis["filepath"])

            except Exception as e:
                apply_result["failed_files"].append({
                    "filepath": analysis["filepath"],
                    "error": str(e)
                })

        return apply_result

    def print_preview_report(self, preview_result: Dict):
        """미리보기 결과 출력"""
        summary = preview_result["summary"]

        print("\n" + "="*60)
        print("📊 로깅 시스템 마이그레이션 미리보기 결과")
        print("="*60)

        print(f"📁 전체 Python 파일: {preview_result['total_files']}개")
        print(f"🔧 변경 필요 파일: {summary['files_needing_change']}개")
        print(f"❌ 오류 파일: {summary['files_with_errors']}개")
        print(f"🔄 총 교체 작업: {summary['total_replacements']}개")

        if summary["pattern_counts"]:
            print("\n📋 패턴별 발견 횟수:")
            for pattern_name, count in summary["pattern_counts"].items():
                if count > 0:
                    print(f"   • {pattern_name}: {count}개")

        if preview_result["files_with_errors"]:
            print(f"\n❌ 오류가 발생한 파일들:")
            for error_info in preview_result["files_with_errors"]:
                print(f"   • {error_info['filepath']}: {error_info['error']}")

        if preview_result["files_to_change"]:
            print(f"\n🔧 변경될 파일들:")
            for analysis in preview_result["files_to_change"][:10]:  # 처음 10개만 표시
                filepath = analysis["filepath"].relative_to(self.project_root)
                print(f"   • {filepath} ({len(analysis['matches'])}개 변경)")

                # 각 변경 사항의 미리보기
                for match in analysis["matches"][:3]:  # 처음 3개만 표시
                    print(f"     - 라인 {match['line_number']}: {match['description']}")
                    print(f"       이전: {match['original_text']}")
                    print(f"       이후: {match['replacement_text']}")

                if len(analysis["matches"]) > 3:
                    print(f"     ... 외 {len(analysis['matches']) - 3}개 더")

            if len(preview_result["files_to_change"]) > 10:
                print(f"   ... 외 {len(preview_result['files_to_change']) - 10}개 파일 더")


def main():
    """메인 실행 함수"""
    print("🚀 로깅 시스템 마이그레이션 도구 시작")
    print("=" * 50)

    # 마이그레이션 도구 초기화
    migration_tool = LoggingMigrationTool()

    # 변경 사항 미리보기
    print("🔍 프로젝트 분석 중...")
    preview_result = migration_tool.preview_changes()

    # 미리보기 결과 출력
    migration_tool.print_preview_report(preview_result)

    if preview_result["summary"]["files_needing_change"] == 0:
        print("\n✅ 변경이 필요한 파일이 없습니다.")
        return

    # 사용자 확인
    print("\n" + "="*60)
    print("⚠️  실제 파일 변경을 진행하시겠습니까?")
    print("   - 백업이 자동으로 생성됩니다")
    print("   - 변경 사항은 되돌릴 수 있습니다")

    while True:
        user_input = input("\n진행하시겠습니까? (y/n): ").lower().strip()
        if user_input in ['y', 'yes']:
            break
        elif user_input in ['n', 'no']:
            print("❌ 사용자에 의해 취소되었습니다.")
            return
        else:
            print("y 또는 n을 입력해주세요.")

    # 변경 사항 적용
    print("\n🔧 변경 사항 적용 중...")
    apply_result = migration_tool.apply_changes(preview_result)

    # 결과 출력
    print("\n" + "="*60)
    print("✅ 마이그레이션 완료!")
    print("="*60)
    print(f"✅ 성공한 파일: {len(apply_result['successful_files'])}개")
    print(f"❌ 실패한 파일: {len(apply_result['failed_files'])}개")
    print(f"🔄 총 교체 작업: {apply_result['total_replacements']}개")

    if apply_result["failed_files"]:
        print(f"\n❌ 실패한 파일들:")
        for fail_info in apply_result["failed_files"]:
            print(f"   • {fail_info['filepath']}: {fail_info['error']}")

    print(f"\n💾 백업 위치: {migration_tool.backup_dir}")
    print("\n🎉 로깅 시스템 마이그레이션이 완료되었습니다!")
    print("   이제 애플리케이션을 실행해서 정상 동작하는지 확인해보세요.")


if __name__ == "__main__":
    main()
