"""
Comprehensive Migration Script - DatabasePathService를 Factory 패턴으로 완전 교체
"""

import re
from pathlib import Path
import os


def replace_database_path_service(file_path: str) -> bool:
    """DatabasePathService 사용을 Factory 패턴으로 교체"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Import 교체
    import_replacements = [
        # DatabasePathService import 제거하고 get_path_service import 추가
        (r'from upbit_auto_trading\.domain\.database_configuration\.services\.database_path_service import[^\n]*\n',
         ''),
        (r'from upbit_auto_trading\.infrastructure\.configuration import[^\n]*',
         lambda m: m.group(0) + '\nfrom upbit_auto_trading.infrastructure.configuration import get_path_service'
         if 'get_path_service' not in m.group(0) else m.group(0)),
    ]

    # Usage 교체
    usage_replacements = [
        # Constructor에서 DatabasePathService() -> get_path_service()
        (r'self\.db_path_service = DatabasePathService\(\)',
         'self.path_service = get_path_service()'),

        # Method 호출 교체
        (r'self\.db_path_service\.get_all_paths\(\)',
         'self._get_all_database_paths()'),  # Helper method로 래핑

        (r'self\.db_path_service\.get_current_path\(([^)]+)\)',
         r'self.path_service.get_database_path(\1)'),

        (r'self\.db_path_service\.change_database_path\(([^,]+),\s*([^)]+)\)',
         r'self.path_service.change_database_location(\1, \2)'),
    ]

    # Import 교체 실행
    for pattern, replacement in import_replacements:
        if callable(replacement):
            content = re.sub(pattern, replacement, content)
        else:
            content = re.sub(pattern, replacement, content)

    # Usage 교체 실행
    for pattern, replacement in usage_replacements:
        content = re.sub(pattern, replacement, content)

    # Helper method 추가 (필요한 경우)
    if '_get_all_database_paths()' in content and 'def _get_all_database_paths(' not in content:
        # Class 정의 찾아서 helper method 추가
        class_pattern = r'(class [^:]+:.*?\n)'
        def add_helper_method(match):
            return match.group(1) + '''
    def _get_all_database_paths(self):
        """모든 데이터베이스 경로를 반환하는 헬퍼 메서드"""
        return {
            'settings': self.path_service.get_database_path('settings'),
            'strategies': self.path_service.get_database_path('strategies'),
            'market_data': self.path_service.get_database_path('market_data')
        }
'''
        content = re.sub(class_pattern, add_helper_method, content, flags=re.DOTALL)

    # 파일 업데이트
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ DatabasePathService 교체 완료: {file_path}")
        return True
    else:
        print(f"⚪ 변경사항 없음: {file_path}")
        return False


def main():
    """주요 파일들 일괄 교체"""

    # 교체할 파일들 찾기
    files_to_process = []

    for root, dirs, files in os.walk("upbit_auto_trading"):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'DatabasePathService' in content or 'db_path_service' in content:
                        files_to_process.append(file_path)

    print(f"🎯 DatabasePathService 사용 파일: {len(files_to_process)}개")

    # 교체 실행
    updated_count = 0
    for file_path in files_to_process:
        try:
            if replace_database_path_service(file_path):
                updated_count += 1
        except Exception as e:
            print(f"❌ 교체 실패: {file_path} - {e}")

    print(f"\n🎉 교체 완료: {updated_count}/{len(files_to_process)} 파일")


if __name__ == "__main__":
    main()
