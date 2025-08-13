#!/usr/bin/env python3
"""
LLM_REPORT 제거 스크립트
모든 _log_llm_report 호출을 제거합니다.
"""

import re
import sys
from pathlib import Path


def remove_llm_reports_from_file(file_path):
    """파일에서 _log_llm_report 호출을 제거합니다."""
    try:
        # 파일 내용 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        original_lines = lines[:]
        new_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # _log_llm_report 호출을 찾음
            if '_log_llm_report' in line:
                # 현재 라인과 다음 라인들을 검사하여 완전한 호출을 찾음
                call_lines = [line]
                j = i + 1

                # 괄호가 완전히 닫힐 때까지 라인 수집
                open_parens = line.count('(') - line.count(')')
                while j < len(lines) and open_parens > 0:
                    next_line = lines[j]
                    call_lines.append(next_line)
                    open_parens += next_line.count('(') - next_line.count(')')
                    j += 1

                # 호출 전체를 건너뜀
                i = j
                continue
            else:
                new_lines.append(line)
                i += 1

        # 연속된 빈 줄 정리 (3개 이상의 연속 빈 줄을 2개로 제한)
        cleaned_lines = []
        empty_count = 0

        for line in new_lines:
            if line.strip() == '':
                empty_count += 1
                if empty_count <= 2:
                    cleaned_lines.append(line)
            else:
                empty_count = 0
                cleaned_lines.append(line)

        # 변경사항이 있으면 파일 저장
        if cleaned_lines != original_lines:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)
            print(f"✅ {file_path}: LLM 보고 제거 완료")
            return True
        else:
            print(f"ℹ️ {file_path}: 변경사항 없음")
            return False

    except Exception as e:
        print(f"❌ {file_path}: 처리 실패 - {e}")
        return False


def main():
    """메인 함수"""
    base_path = Path("upbit_auto_trading")

    if not base_path.exists():
        print("❌ upbit_auto_trading 디렉토리를 찾을 수 없습니다.")
        sys.exit(1)

    # 모든 Python 파일 찾기
    python_files = list(base_path.rglob("*.py"))

    print(f"🔍 총 {len(python_files)}개의 Python 파일을 검사합니다...")

    changed_files = 0
    total_files = 0

    for file_path in python_files:
        total_files += 1
        if remove_llm_reports_from_file(file_path):
            changed_files += 1

    print("\n📊 처리 완료:")
    print(f"   - 총 파일 수: {total_files}")
    print(f"   - 변경된 파일: {changed_files}")
    print(f"   - 변경되지 않은 파일: {total_files - changed_files}")


if __name__ == "__main__":
    main()
