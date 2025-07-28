#!/usr/bin/env python3
"""
condition_storage.py의 try/with 블록 들여쓰기 문제 수정
"""

import re

def fix_try_with_blocks():
    """try/with 블록의 들여쓰기 문제 수정"""
    file_path = "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/core/condition_storage.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 패턴: try: 다음 줄에 conn = self._get_connection() 그 다음 줄에 with conn:
        # 수정: try: 다음 줄에 conn = self._get_connection() 그리고 with conn:을 같은 들여쓰기로
        
        # 정규식 패턴
        pattern = r'(\s+try:\s*\n\s+conn = self\._get_connection\(\)\s*\n)(\s+)(with conn:)'
        replacement = r'\1            \3'
        
        content = re.sub(pattern, replacement, content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ try/with 블록 들여쓰기 수정 완료!")
        
    except Exception as e:
        print(f"❌ 수정 실패: {e}")

if __name__ == "__main__":
    fix_try_with_blocks()
