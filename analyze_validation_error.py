#!/usr/bin/env python3
"""
검증 오류 분석: parameter_type 검증 로직 찾기
"""

import os
from pathlib import Path

def find_validation_error():
    """parameter_type 검증 오류가 발생하는 코드 찾기"""

    print("=== PARAMETER_TYPE 검증 오류 분석 ===\n")

    # 1. 에러 메시지 검색
    search_patterns = [
        "boolean.*integer.*decimal.*string",
        "parameter_type.*중 하나여야",
        "VALIDATION_ERROR.*parameter_type",
        "{'boolean', 'integer', 'decimal', 'string'}"
    ]

    print("1. 에러 메시지 관련 파일 검색")

    for pattern in search_patterns:
        print(f"  🔍 패턴: {pattern}")
        find_files_with_pattern(pattern)
        print()

def find_files_with_pattern(pattern):
    """특정 패턴이 포함된 파일들 찾기"""

    # 검색할 디렉토리들
    search_dirs = [
        "upbit_auto_trading/infrastructure/repositories",
        "upbit_auto_trading/domain",
        "upbit_auto_trading/application"
    ]

    found_files = []

    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if any(keyword in content for keyword in pattern.split('.*')):
                                    found_files.append(file_path)
                                    print(f"    📄 발견: {file_path}")
                                    break
                        except:
                            continue

    return found_files

def analyze_specific_repository():
    """sqlite_trading_variable_repository.py 분석"""

    print("2. sqlite_trading_variable_repository.py 상세 분석")

    repo_file = "upbit_auto_trading/infrastructure/repositories/sqlite_trading_variable_repository.py"

    if not os.path.exists(repo_file):
        print(f"  ❌ 파일 없음: {repo_file}")
        return

    print(f"  📄 분석 대상: {repo_file}")

    try:
        with open(repo_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # validation 관련 코드 찾기
        validation_lines = []
        for i, line in enumerate(lines, 1):
            if any(keyword in line.lower() for keyword in
                   ['validation', 'boolean', 'integer', 'decimal', 'string', 'parameter_type']):
                validation_lines.append((i, line.strip()))

        print(f"  🔍 validation 관련 라인 {len(validation_lines)}개 발견:")
        for line_num, line_content in validation_lines[:10]:  # 처음 10개만
            print(f"    {line_num:3d}: {line_content}")

        if len(validation_lines) > 10:
            print(f"    ... (총 {len(validation_lines)}개)")

    except Exception as e:
        print(f"  ❌ 파일 읽기 오류: {e}")

def generate_fix_suggestions():
    """수정 제안 생성"""

    print("\n3. 수정 제안")

    print("  🎯 문제:")
    print("    - 리포지토리 검증 로직에 'enum' 타입이 허용되지 않음")
    print("    - 현재 허용: {'boolean', 'integer', 'decimal', 'string'}")
    print("    - 필요: {'boolean', 'integer', 'decimal', 'string', 'enum'}")

    print("\n  💡 해결 방안:")
    print("    1. 검증 로직에 'enum' 타입 추가")
    print("    2. 또는 'external_variable' 등 다른 커스텀 타입들도 고려")
    print("    3. UI에서 enum 타입 처리 로직 구현")

    print("\n  📋 예상 수정 위치:")
    print("    - sqlite_trading_variable_repository.py의 validation 로직")
    print("    - parameter_input_widget.py의 enum 타입 지원")
    print("    - domain model의 parameter_type 정의")

if __name__ == "__main__":
    find_validation_error()
    analyze_specific_repository()
    generate_fix_suggestions()
