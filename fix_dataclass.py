#!/usr/bin/env python3
"""
trigger_events.py의 모든 dataclass에 kw_only=True 추가
"""

# 파일 읽기
with open('upbit_auto_trading/domain/events/trigger_events.py', 'r', encoding='utf-8') as f:
    content = f.read()

# @dataclass(frozen=True)를 @dataclass(frozen=True, kw_only=True)로 변경
content = content.replace('@dataclass(frozen=True)', '@dataclass(frozen=True, kw_only=True)')

# 파일 쓰기
with open('upbit_auto_trading/domain/events/trigger_events.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ trigger_events.py dataclass에 kw_only=True 추가 완료")
