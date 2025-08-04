#!/usr/bin/env python3
"""
안전한 super() 호출 제거 스크립트
strategy_events.py 파일에서 super().__post_init__() 호출을 제거합니다.
"""

import os

def fix_super_calls():
    """super().__post_init__() 호출을 안전하게 제거"""

    file_path = "upbit_auto_trading/domain/events/strategy_events.py"

    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 제거할 패턴들
    patterns_to_replace = [
        ('        super().__post_init__()', '        # super().__post_init__()  # 제거: 일반 클래스 DomainEvent에는 __post_init__가 없음'),
    ]

    # 변경 카운트
    changes_made = 0

    # 패턴 대체
    for old_pattern, new_pattern in patterns_to_replace:
        old_count = content.count(old_pattern)
        content = content.replace(old_pattern, new_pattern)
        new_count = content.count(old_pattern)
        changes_made += (old_count - new_count)

    # 파일 쓰기
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {changes_made}개의 super() 호출을 안전하게 제거했습니다.")
    print(f"📁 파일: {file_path}")

    return changes_made

if __name__ == "__main__":
    changes = fix_super_calls()
    if changes > 0:
        print("🎉 super() 호출 제거 완료!")
    else:
        print("ℹ️  더 이상 제거할 super() 호출이 없습니다.")
