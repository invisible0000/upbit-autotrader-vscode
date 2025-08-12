"""
간단한 로깅 관리 시스템 - 통합 인터페이스
====================================

SimpleLogViewer와 SafeConsoleCapture를 통합하여
간단하고 안전한 로깅 관리 시스템 제공

주요 특징:
- 무한 루프 없는 안전한 구현
- 로그 파일 뷰어와 콘솔 캡처 분리
- 단순한 인터페이스

DDD Infrastructure Layer: 통합 로깅 관리
"""

from typing import Callable, Optional, Dict, Any

from .simple_log_viewer import SimpleLogViewer
from .safe_console_capture import SafeConsoleCapture


class SimpleLoggingManager:
    """간단한 로깅 관리 시스템 - 통합 인터페이스"""

    def __init__(self):
        self._log_viewer = SimpleLogViewer()
        self._console_capture = SafeConsoleCapture()
        self._is_active = False

    def start(self) -> bool:
        """로깅 관리 시작"""
        if self._is_active:
            return True

        try:
            # 로그 뷰어 시작
            log_started = self._log_viewer.start()

            # 콘솔 캡처 시작
            console_started = self._console_capture.start_capture()

            # 적어도 하나는 성공해야 함
            if log_started or console_started:
                self._is_active = True
                return True
            else:
                return False

        except Exception:
            return False

    def stop(self) -> None:
        """로깅 관리 중단"""
        if not self._is_active:
            return

        try:
            self._log_viewer.stop()
            self._console_capture.stop_capture()
            self._is_active = False
        except Exception:
            pass  # 중단 에러 무시

    def add_log_handler(self, handler: Callable[[str], None]) -> None:
        """로그 파일 핸들러 추가"""
        self._log_viewer.add_log_handler(handler)

    def add_console_handler(self, handler: Callable[[str], None]) -> None:
        """콘솔 출력 핸들러 추가"""
        self._console_capture.add_console_handler(handler)

    def remove_log_handler(self, handler: Callable[[str], None]) -> None:
        """로그 파일 핸들러 제거"""
        self._log_viewer.remove_log_handler(handler)

    def remove_console_handler(self, handler: Callable[[str], None]) -> None:
        """콘솔 출력 핸들러 제거"""
        self._console_capture.remove_console_handler(handler)

    def get_status(self) -> Dict[str, Any]:
        """전체 상태 반환"""
        log_status = self._log_viewer.get_status()
        console_status = self._console_capture.get_status()

        return {
            'is_active': self._is_active,
            'log_viewer': log_status,
            'console_capture': console_status
        }

    @property
    def is_active(self) -> bool:
        """활성 상태 확인"""
        return self._is_active
