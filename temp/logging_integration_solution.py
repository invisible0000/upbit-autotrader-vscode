"""
현재 커스텀 로깅 시스템과 pytest caplog 통합 솔루션
==========================================================

문제: 커스텀 LoggingService가 표준 Python logging과 분리되어 pytest caplog가 캡처 못함
해결: 테스트 모드에서 로그 캡처 기능을 LoggingService에 추가
"""

import logging
import threading
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class LogRecord:
    """테스트용 로그 레코드"""
    timestamp: datetime
    level: str
    component: str
    message: str

class TestLogCapture:
    """테스트용 로그 캡처"""
    def __init__(self):
        self.records: List[LogRecord] = []
        self._lock = threading.Lock()

    def capture_log(self, level: str, component: str, message: str):
        """로그 캡처"""
        with self._lock:
            record = LogRecord(
                timestamp=datetime.now(),
                level=level,
                component=component,
                message=message
            )
            self.records.append(record)

    def get_records(self, level: Optional[str] = None, component: Optional[str] = None) -> List[LogRecord]:
        """조건에 맞는 로그 레코드 반환"""
        with self._lock:
            filtered = self.records
            if level:
                filtered = [r for r in filtered if r.level == level]
            if component:
                filtered = [r for r in filtered if r.component == component]
            return filtered

    def clear(self):
        """캡처된 로그 클리어"""
        with self._lock:
            self.records.clear()

    def contains_pattern(self, pattern: str) -> bool:
        """특정 패턴이 로그에 포함되어 있는지 확인"""
        with self._lock:
            for record in self.records:
                if pattern in record.message:
                    return True
            return False

    def find_patterns(self, patterns: List[str]) -> Dict[str, bool]:
        """여러 패턴을 찾아서 결과 반환"""
        results = {}
        with self._lock:
            for pattern in patterns:
                results[pattern] = any(pattern in record.message for record in self.records)
        return results

# LoggingService에 추가할 메소드들
class LoggingServiceTestMixin:
    """LoggingService에 추가할 테스트 기능"""

    def __init__(self):
        self._test_capture: Optional[TestLogCapture] = None
        self._test_mode = False

    def enable_test_mode(self) -> TestLogCapture:
        """테스트 모드 활성화 및 캡처 객체 반환"""
        self._test_mode = True
        self._test_capture = TestLogCapture()
        return self._test_capture

    def disable_test_mode(self):
        """테스트 모드 비활성화"""
        self._test_mode = False
        if self._test_capture:
            self._test_capture.clear()
        self._test_capture = None

    def _capture_test_log(self, level: str, component: str, message: str):
        """테스트 모드에서 로그 캡처"""
        if self._test_mode and self._test_capture:
            self._test_capture.capture_log(level, component, message)

# 방안 1: LoggingService 수정 예시
"""
기존 LoggingService._create_logger 메소드에 추가:

def _create_logger(self, component_name: str) -> logging.Logger:
    logger = logging.getLogger(f"upbit.{component_name}")
    # ... 기존 코드 ...

    # 테스트 모드용 핸들러 추가
    if self._test_mode and self._test_capture:
        test_handler = TestModeHandler(self._test_capture, component_name)
        logger.addHandler(test_handler)

    return logger

class TestModeHandler(logging.Handler):
    def __init__(self, capture: TestLogCapture, component: str):
        super().__init__()
        self.capture = capture
        self.component = component

    def emit(self, record):
        self.capture.capture_log(
            level=record.levelname,
            component=self.component,
            message=record.getMessage()
        )
"""

# 방안 2: 테스트에서 직접 표준 logging 설정
def setup_test_logging_bridge():
    """테스트용 로깅 브리지 설정"""
    import logging

    # 표준 logging에서 upbit.* 로거들을 pytest가 캡처할 수 있도록 설정
    upbit_logger = logging.getLogger('upbit')
    upbit_logger.setLevel(logging.DEBUG)
    upbit_logger.propagate = True

    # 루트 로거 설정
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.DEBUG)

# 방안 3: Context Manager를 이용한 임시 로그 캡처
class TemporaryLogCapture:
    """임시 로그 캡처 컨텍스트"""
    def __init__(self, logging_service):
        self.logging_service = logging_service
        self.captured_logs = []
        self.original_handlers = {}

    def __enter__(self):
        # 기존 핸들러 백업하고 캡처 핸들러 추가
        for component_name, logger in self.logging_service._loggers.items():
            self.original_handlers[component_name] = logger.handlers.copy()

            # 캡처 핸들러 추가
            capture_handler = ListHandler(self.captured_logs)
            logger.addHandler(capture_handler)

        return self.captured_logs

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 핸들러 복원
        for component_name, logger in self.logging_service._loggers.items():
            logger.handlers = self.original_handlers.get(component_name, [])

class ListHandler(logging.Handler):
    """리스트에 로그를 저장하는 핸들러"""
    def __init__(self, log_list):
        super().__init__()
        self.log_list = log_list

    def emit(self, record):
        self.log_list.append(record)

print("✅ 로깅 통합 솔루션 준비 완료")
print("권장 방안: LoggingService에 테스트 모드 추가")
