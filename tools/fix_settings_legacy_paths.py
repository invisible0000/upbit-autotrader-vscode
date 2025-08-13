"""
설정 화면 레거시 경로 제거 스크립트
모든 설정 탭에서 DatabasePathService, db_path_service, infrastructure_paths 제거
"""

import re
from pathlib import Path


def fix_database_settings_presenter():
    """database_settings_presenter.py 파일 수정"""
    file_path = Path("upbit_auto_trading/ui/desktop/screens/settings/presenters/database_settings_presenter.py")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 주요 교체 패턴들
    replacements = [
        # DatabaseInfoWorker 클래스의 생성자 수정
        (r'def __init__\(self, db_path_service, get_detailed_status_func\):',
         'def __init__(self, path_service, get_detailed_status_func):'),

        # DatabaseInfoWorker 클래스의 속성 수정
        (r'self\.db_path_service = db_path_service',
         'self.path_service = path_service'),

        # DatabaseSettingsPresenter에서 Worker 생성 시 수정
        (r'DatabaseInfoWorker\(\s*self\.db_path_service,',
         'DatabaseInfoWorker(\n            self.path_service,'),

        # 타입 힌트 수정 (Path를 str로 변환)
        (r'def _get_detailed_database_status\(self, paths: Dict\[str, str\]\)',
         'def _get_detailed_database_status(self, paths: Dict[str, str])'),
    ]

    # 교체 실행
    for pattern, replacement in replacements:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            print(f"✅ 교체: {pattern[:50]}...")

    # Path 타입 문제 해결 - str() 변환 추가
    path_conversion_pattern = r"(paths\.get\([^)]+\))"
    def convert_path_to_str(match):
        return f"str({match.group(1)})"

    content = re.sub(path_conversion_pattern, convert_path_to_str, content)
    print("✅ Path to str 변환 완료")

    # 파일 업데이트
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 파일 업데이트 완료: {file_path}")
        return True
    else:
        print(f"⚪ 변경사항 없음: {file_path}")
        return False


def scan_all_settings_files():
    """모든 설정 화면 파일 스캔"""
    settings_dir = Path("upbit_auto_trading/ui/desktop/screens/settings")

    files_with_legacy = []

    for py_file in settings_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            legacy_patterns = [
                'DatabasePathService',
                'db_path_service',
                'infrastructure_paths',
                'from .+paths import',
                '\.paths\.'
            ]

            for pattern in legacy_patterns:
                if re.search(pattern, content):
                    files_with_legacy.append((py_file, pattern))
                    break

        except Exception as e:
            print(f"❌ 파일 읽기 실패: {py_file} - {e}")

    return files_with_legacy


def main():
    """메인 실행 함수"""
    print("🔍 설정 화면 레거시 경로 검사 시작...")

    # 1. 전체 스캔
    legacy_files = scan_all_settings_files()

    if legacy_files:
        print(f"🎯 레거시 패턴 발견: {len(legacy_files)}개 파일")
        for file_path, pattern in legacy_files:
            print(f"   📁 {file_path.relative_to(Path('upbit_auto_trading/ui/desktop/screens/settings'))} - {pattern}")
    else:
        print("✅ 레거시 패턴이 없는 것으로 보입니다")
        return

    # 2. database_settings_presenter.py 수정
    print("\n🔧 database_settings_presenter.py 수정 중...")
    if fix_database_settings_presenter():
        print("✅ database_settings_presenter.py 수정 완료")

    # 3. 재검사
    print("\n🔍 재검사 중...")
    remaining_files = scan_all_settings_files()

    if remaining_files:
        print(f"⚠️ 남은 레거시 패턴: {len(remaining_files)}개")
        for file_path, pattern in remaining_files:
            print(f"   📁 {file_path.relative_to(Path('upbit_auto_trading/ui/desktop/screens/settings'))} - {pattern}")
    else:
        print("🎉 모든 레거시 패턴 제거 완료!")


if __name__ == "__main__":
    main()
