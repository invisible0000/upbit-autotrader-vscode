#!/usr/bin/env python3
"""테스트 파일들의 send() → send_notification() 수정 스크립트"""

import os
import re

def fix_test_files():
    """테스트 파일들에서 send() 메서드를 send_notification()으로 수정"""

    test_files = [
        "tests/application/event_handlers/test_strategy_event_handlers.py",
        "tests/application/event_handlers/test_backtest_event_handlers.py",
        "tests/application/event_handlers/test_event_handler_registry.py"
    ]

    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"❌ 파일 없음: {file_path}")
            continue

        print(f"🔧 수정 중: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. service.send = AsyncMock() → service.send_notification = AsyncMock()
        content = re.sub(
            r'(\s+)service\.send = AsyncMock\(\)',
            r'\1service.send_notification = AsyncMock()',
            content
        )

        # 2. notification_service.send = AsyncMock() → notification_service.send_notification = AsyncMock()
        content = re.sub(
            r'(\s+)notification_service\.send = AsyncMock\(\)',
            r'\1notification_service.send_notification = AsyncMock()',
            content
        )

        # 3. mock_notification_service.send.assert_called_once() → mock_notification_service.send_notification.assert_called_once()
        content = re.sub(
            r'mock_notification_service\.send\.assert_called_once\(\)',
            r'mock_notification_service.send_notification.assert_called_once()',
            content
        )

        # 4. notification_service.send.assert_called_once() → notification_service.send_notification.assert_called_once()
        content = re.sub(
            r'notification_service\.send\.assert_called_once\(\)',
            r'notification_service.send_notification.assert_called_once()',
            content
        )

        # 5. mock_notification_service.send.call_args → mock_notification_service.send_notification.call_args
        content = re.sub(
            r'mock_notification_service\.send\.call_args',
            r'mock_notification_service.send_notification.call_args',
            content
        )

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 수정 완료: {file_path}")

if __name__ == "__main__":
    fix_test_files()
    print("🎉 모든 테스트 파일 수정 완료!")
