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
            content = f.read()
            
        original_content = content
        
        # _log_llm_report 호출을 찾고 제거하는 패턴
        # 1. 단일 라인 호출
        pattern1 = re.compile(r'^\s*self\._log_llm_report\([^)]*\)\s*$', re.MULTILINE)
        
        # 2. 멀티라인 호출 (줄바꿈이 있는 경우)
        pattern2 = re.compile(r'^\s*self\._log_llm_report\([^)]*(?:\n[^)]*)*\)\s*$', re.MULTILINE | re.DOTALL)
        
        # 패턴 매칭 및 제거
        content = pattern1.sub('', content)
        content = pattern2.sub('', content)
        
        # 연속된 빈 줄 정리 (3개 이상의 연속 빈 줄을 2개로 제한)
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        # 변경사항이 있으면 파일 저장
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
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
    
    print(f"\n📊 처리 완료:")
    print(f"   - 총 파일 수: {total_files}")
    print(f"   - 변경된 파일: {changed_files}")
    print(f"   - 변경되지 않은 파일: {total_files - changed_files}")


if __name__ == "__main__":
    main()
