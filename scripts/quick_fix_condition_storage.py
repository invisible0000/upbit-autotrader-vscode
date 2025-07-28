#!/usr/bin/env python3
"""
condition_storage.py 빠른 수정 스크립트
전역 DB 매니저 사용을 위한 핵심 메소드들만 수정
"""

import re
import os

def quick_fix_condition_storage():
    """condition_storage.py의 sqlite3.connect 호출을 빠르게 수정"""
    
    file_path = "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/core/condition_storage.py"
    
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # sqlite3.connect(self.db_path) 패턴을 self._get_connection()으로 교체
    patterns = [
        (r'with sqlite3\.connect\(self\.db_path\) as conn:', 'conn = self._get_connection()\n        with conn:'),
        (r'sqlite3\.connect\(self\.db_path\)', 'self._get_connection()'),
    ]
    
    modified = False
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            modified = True
            print(f"✅ 패턴 수정: {pattern} → {replacement}")
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 파일 수정 완료: {file_path}")
    else:
        print(f"⚠️ 수정할 패턴을 찾지 못했습니다: {file_path}")

if __name__ == "__main__":
    quick_fix_condition_storage()
    print("🎉 빠른 수정 완료!")
