"""
테스트용 로깅 유틸리티
======================

pytest와 커스텀 LoggingService 통합을 위한 헬퍼 함수들
"""

import pytest
import logging
from typing import List, Dict, Any
from unittest.mock import Mock, patch

@pytest.fixture
def log_capture():
    """로그 캡처 픽스처 - 표준 logging과 연동"""
    # 캡처된 로그 저장소
    captured_logs = []

    # 커스텀 핸들러로 로그 캡처
    class TestLogHandler(logging.Handler):
        def emit(self, record):
            captured_logs.append({
                'level': record.levelname,
                'name': record.name,
                'message': record.getMessage(),
                'full_record': record
            })

    # upbit.* 로거들에 테스트 핸들러 추가
    test_handler = TestLogHandler()
    test_handler.setLevel(logging.DEBUG)

    # 기존 upbit 로거와 하위 로거들 모두 처리
    upbit_logger = logging.getLogger('upbit')

    # 백업: 기존 핸들러와 propagate 설정
    original_handlers = upbit_logger.handlers.copy()
    original_propagate = upbit_logger.propagate
    original_level = upbit_logger.level

    # 테스트용 설정 적용
    upbit_logger.addHandler(test_handler)
    upbit_logger.setLevel(logging.DEBUG)
    upbit_logger.propagate = True  # 상위로 전파 허용

    # 하위 로거들도 모두 처리 (OverlapAnalyzer, SqliteCandleRepository 등)
    specific_loggers = []
    for logger_name in ['upbit.OverlapAnalyzer', 'upbit.SqliteCandleRepository', 'upbit.UpbitApi']:
        specific_logger = logging.getLogger(logger_name)
        specific_original_handlers = specific_logger.handlers.copy()
        specific_original_propagate = specific_logger.propagate
        specific_original_level = specific_logger.level

        specific_loggers.append((
            specific_logger, specific_original_handlers,
            specific_original_propagate, specific_original_level
        ))

        specific_logger.addHandler(test_handler)
        specific_logger.setLevel(logging.DEBUG)
        specific_logger.propagate = True

    yield captured_logs

    # 정리: 모든 변경사항 복원
    upbit_logger.handlers = original_handlers
    upbit_logger.propagate = original_propagate
    upbit_logger.setLevel(original_level)

    for logger, handlers, propagate, level in specific_loggers:
        logger.handlers = handlers
        logger.propagate = propagate
        logger.setLevel(level)

    test_handler.close()


def find_log_patterns(captured_logs: List[Dict], patterns: List[str]) -> Dict[str, bool]:
    """캡처된 로그에서 패턴 찾기"""
    results = {}
    for pattern in patterns:
        results[pattern] = any(
            pattern in log['message']
            for log in captured_logs
        )
    return results


def print_captured_logs(captured_logs: List[Dict], title: str = "캡처된 로그"):
    """캡처된 로그 출력 (디버깅용)"""
    print(f"\n{'=' * 50}")
    print(f"{title} ({len(captured_logs)}개)")
    print(f"{'=' * 50}")

    for i, log in enumerate(captured_logs, 1):
        print(f"{i:2d}. [{log['level']}] {log['name']} | {log['message']}")

    print(f"{'=' * 50}")


@pytest.fixture
def enhanced_log_capture(log_capture):
    """향상된 로그 캡처 - 패턴 검색 기능 포함"""
    class LogCapture:
        def __init__(self, logs):
            self.logs = logs

        def find_patterns(self, patterns: List[str]) -> Dict[str, bool]:
            return find_log_patterns(self.logs, patterns)

        def contains(self, pattern: str) -> bool:
            return any(pattern in log['message'] for log in self.logs)

        def debug_print(self, title: str = "캡처된 로그"):
            print_captured_logs(self.logs, title)

        def get_messages(self) -> List[str]:
            return [log['message'] for log in self.logs]

        def filter_by_component(self, component: str) -> List[Dict]:
            return [log for log in self.logs if component in log['name']]

    return LogCapture(log_capture)
