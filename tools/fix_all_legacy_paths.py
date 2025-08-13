"""
전체 프로젝트에서 레거시 경로 패턴 제거 스크립트
DatabasePathService, db_path_service, infrastructure_paths 완전 제거
"""

import re
from pathlib import Path
from typing import List, Tuple


class LegacyPathFixer:
    def __init__(self):
        self.fixed_files = []
        self.errors = []

    def get_python_files(self) -> List[Path]:
        """Python 파일들 찾기"""
        python_files = []
        for pattern in ["**/*.py"]:
            python_files.extend(Path(".").glob(pattern))
        return [f for f in python_files if not str(f).startswith("venv")]

    def get_replacement_patterns(self) -> List[Tuple[str, str]]:
        """교체 패턴 정의"""
        return [
            # Import 문 교체
            (r'from upbit_auto_trading\.infrastructure\.configuration\.database_path_service import DatabasePathService',
             'from upbit_auto_trading.infrastructure.configuration import PathServiceFactory'),

            # 인스턴스 생성 교체
            (r'DatabasePathService\(\)',
             'PathServiceFactory.get_path_service()'),

            (r'DatabasePathService\([^)]*\)',
             'PathServiceFactory.get_path_service()'),

            # 변수명 교체
            (r'db_path_service = DatabasePathService\([^)]*\)',
             'path_service = PathServiceFactory.get_path_service()'),

            (r'self\.db_path_service = DatabasePathService\([^)]*\)',
             'self.path_service = PathServiceFactory.get_path_service()'),

            # 메서드 호출 교체
            (r'db_path_service\.([a-zA-Z_]+)',
             r'path_service.\1'),

            (r'self\.db_path_service\.([a-zA-Z_]+)',
             r'self.path_service.\1'),

            # 매개변수 교체
            (r'def __init__\(self, db_path_service([^)]*)\):',
             r'def __init__(self, path_service\1):'),

            # 일부 import에서 잘못된 들여쓰기 수정
            (r'\s+from upbit_auto_trading\.infrastructure\.persistence\.database_configuration_repository_impl import \(\s*FileSystemDatabaseConfigurationRepository\s*\)',
             ''),

            # 빈 repository 코드 제거
            (r'repository = FileSystemDatabaseConfigurationRepository\(\)\s*',
             ''),

            # 댓글의 DatabasePathService 교체
            (r'# DatabasePathService',
             '# PathServiceFactory'),

            (r'DatabasePathService 인스턴스',
             'PathServiceFactory 인스턴스'),
        ]

    def fix_file(self, file_path: Path) -> bool:
        """개별 파일 수정"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # 교체 패턴 적용
            for pattern, replacement in self.get_replacement_patterns():
                new_content = re.sub(pattern, content, flags=re.MULTILINE)
                if new_content != content:
                    content = new_content
                    print(f"  ✅ {file_path}: {pattern[:30]}...")

            # 변경사항이 있으면 파일 저장
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.fixed_files.append(str(file_path))
                return True

            return False

        except Exception as e:
            self.errors.append(f"{file_path}: {e}")
            return False

    def run(self):
        """전체 수정 실행"""
        print("🔧 전체 프로젝트 레거시 경로 패턴 제거 시작...")

        python_files = self.get_python_files()
        print(f"📁 검색된 Python 파일: {len(python_files)}개")

        for file_path in python_files:
            if "test" in str(file_path) or "__pycache__" in str(file_path):
                continue

            print(f"🔍 검사: {file_path}")
            self.fix_file(file_path)

        # 결과 출력
        print(f"\n✅ 수정 완료: {len(self.fixed_files)}개 파일")
        for file in self.fixed_files:
            print(f"  📄 {file}")

        if self.errors:
            print(f"\n❌ 오류 발생: {len(self.errors)}개")
            for error in self.errors:
                print(f"  ⚠️ {error}")


if __name__ == "__main__":
    fixer = LegacyPathFixer()
    fixer.run()
