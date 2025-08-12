"""
로깅 관리 통합 시스템
===================

Infrastructure Layer - 로그 캡처와 콘솔 출력 통합 관리
무한 루프 방지를 위한 안전한 통합 시스템

주요 기능:
- 로그 파일 캡처와 콘솔 출력 캡처 통합
- 안전한 시작/중단 관리
- 통합 통계 제공
"""

from typing import Callable, Optional, Dict, Any
from datetime import datetime

from .log_capture import LogCapture
from .console_output_capture import ConsoleOutputCapture


class LoggingManager:
    """로깅 시스템 통합 관리자"""

    def __init__(self):
        """LoggingManager 초기화"""
        self._log_capture: Optional[LogCapture] = None
        self._console_capture: Optional[ConsoleOutputCapture] = None
        self._is_active = False
        self._start_time = datetime.now()

        # 핸들러 대기열 (캡처 시작 전에 등록된 핸들러들)
        self._pending_log_handlers = []
        self._pending_console_handlers = []

    def start_logging(self) -> bool:
        """통합 로깅 시작

        Returns:
            bool: 시작 성공 여부
        """
        if self._is_active:
            return True

        try:
            # 로그 캡처 시작
            self._log_capture = LogCapture(max_buffer_size=1000)
            log_started = self._log_capture.start_capture()

            # 대기 중인 로그 핸들러 등록
            for handler in self._pending_log_handlers:
                self._log_capture.add_handler(handler)

            # 콘솔 캡처 시작
            self._console_capture = ConsoleOutputCapture(max_buffer_size=500)
            console_started = self._console_capture.start_capture()

            # 대기 중인 콘솔 핸들러 등록
            for handler in self._pending_console_handlers:
                self._console_capture.add_handler(handler)

            # 둘 중 하나라도 성공하면 활성화
            if log_started or console_started:
                self._is_active = True
                self._start_time = datetime.now()
                return True
            else:
                self._cleanup_failed_start()
                return False

        except Exception:
            self._cleanup_failed_start()
            return False

    def stop_logging(self) -> None:
        """통합 로깅 중단"""
        if not self._is_active:
            return

        try:
            # 로그 캡처 중단
            if self._log_capture:
                self._log_capture.stop_capture()
                self._log_capture = None

            # 콘솔 캡처 중단
            if self._console_capture:
                self._console_capture.stop_capture()
                self._console_capture = None

            self._is_active = False

        except Exception:
            pass

    def add_log_handler(self, handler: Callable[[str], None]) -> None:
        """로그 핸들러 추가

        Args:
            handler: 로그 처리 콜백 함수
        """
        if self._log_capture:
            self._log_capture.add_handler(handler)
        else:
            # 캡처가 시작되기 전이면 대기열에 추가
            if handler not in self._pending_log_handlers:
                self._pending_log_handlers.append(handler)

    def add_console_handler(self, handler: Callable[[str], None]) -> None:
        """콘솔 출력 핸들러 추가

        Args:
            handler: 콘솔 출력 처리 콜백 함수
        """
        if self._console_capture:
            self._console_capture.add_handler(handler)
        else:
            # 캡처가 시작되기 전이면 대기열에 추가
            if handler not in self._pending_console_handlers:
                self._pending_console_handlers.append(handler)

    def remove_log_handler(self, handler: Callable[[str], None]) -> None:
        """로그 핸들러 제거

        Args:
            handler: 제거할 핸들러
        """
        if self._log_capture:
            self._log_capture.remove_handler(handler)

        # 대기열에서도 제거
        if handler in self._pending_log_handlers:
            self._pending_log_handlers.remove(handler)

    def remove_console_handler(self, handler: Callable[[str], None]) -> None:
        """콘솔 출력 핸들러 제거

        Args:
            handler: 제거할 핸들러
        """
        if self._console_capture:
            self._console_capture.remove_handler(handler)

        # 대기열에서도 제거
        if handler in self._pending_console_handlers:
            self._pending_console_handlers.remove(handler)

    def get_stats(self) -> Dict[str, Any]:
        """통합 통계 반환

        Returns:
            dict: 통합 통계 정보
        """
        duration = datetime.now() - self._start_time

        # 개별 통계 수집
        log_stats = self._log_capture.get_stats() if self._log_capture else {}
        console_stats = self._console_capture.get_stats() if self._console_capture else {}

        return {
            'is_active': self._is_active,
            'duration_seconds': duration.total_seconds(),
            'log_capture': {
                'is_capturing': log_stats.get('is_capturing', False),
                'total_logs': log_stats.get('total_logs', 0),
                'handlers_count': log_stats.get('handlers_count', 0),
                'queue_size': log_stats.get('queue_size', 0)
            },
            'console_capture': {
                'is_capturing': console_stats.get('is_capturing', False),
                'total_captures': console_stats.get('total_captures', 0),
                'handlers_count': console_stats.get('handlers_count', 0),
                'queue_size': console_stats.get('queue_size', 0)
            }
        }

    def is_active(self) -> bool:
        """활성화 상태 확인

        Returns:
            bool: 활성화 여부
        """
        return self._is_active

    def _cleanup_failed_start(self) -> None:
        """시작 실패 시 정리"""
        try:
            if self._log_capture:
                self._log_capture.stop_capture()
                self._log_capture = None

            if self._console_capture:
                self._console_capture.stop_capture()
                self._console_capture = None

            self._is_active = False

        except Exception:
            pass

    def __del__(self):
        """소멸자: 리소스 정리"""
        try:
            self.stop_logging()
        except Exception:
            pass


# 전역 인스턴스 (싱글톤 패턴)
_global_logging_manager: Optional[LoggingManager] = None


def get_logging_manager() -> LoggingManager:
    """전역 로깅 매니저 인스턴스 반환

    Returns:
        LoggingManager: 로깅 매니저 인스턴스
    """
    global _global_logging_manager
    if _global_logging_manager is None:
        _global_logging_manager = LoggingManager()
    return _global_logging_manager
