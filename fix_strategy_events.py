#!/usr/bin/env python3
"""
strategy.py의 이벤트 클래스명을 수정하는 스크립트
"""

# 파일 읽기
with open('upbit_auto_trading/domain/entities/strategy.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 이벤트 클래스명 변환
replacements = {
    'StrategyCreatedEvent': 'StrategyCreated',
    'StrategyModifiedEvent': 'StrategyUpdated',
    'StrategyActivatedEvent': 'StrategyActivated',
    'StrategyDeactivatedEvent': 'StrategyDeactivated',
    'StrategyDeletedEvent': 'StrategyDeleted'
}

print("🔧 이벤트 클래스명 수정 중...")
for old_name, new_name in replacements.items():
    if old_name in content:
        print(f"  {old_name} → {new_name}")
        content = content.replace(old_name, new_name)

# 파일 쓰기
with open('upbit_auto_trading/domain/entities/strategy.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ strategy.py 이벤트 클래스명 수정 완료")
