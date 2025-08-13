"""
Terminal Capturer - 터미널 출력 캡처 시스템
==========================================

실시간으로 터미널 출력을 캡처하고 버퍼링하는 시스템
"""

import sys
import logging
from collections import deque
from typing import List, Optional, TextIO
from datetime import datetime
import threading


class TeeOutput:
    """
    출력을 두 곳으로 분기하는 클래스
    원본 출력을 유지하면서 동시에 버퍼에 저장
    """

    def __init__(self, original_stream: TextIO, buffer: deque, stream_name: str = "stdout"):
        self.original_stream = original_stream
        self.buffer = buffer
        self.lock = threading.Lock()
        self.stream_name = stream_name  # 'stdout' or 'stderr'

    def write(self, text: str) -> int:
        """텍스트를 원본 스트림과 버퍼에 동시 출력"""
        # 원본 스트림에 출력
        result = self.original_stream.write(text)

        # 버퍼에 저장 (스레드 안전)
        with self.lock:
            if text.strip():  # 빈 라인 제외
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                stream_tag = "STDERR" if self.stream_name.lower() == "stderr" else "STDOUT"
                self.buffer.append(f"[{timestamp}] [{stream_tag}] {text.rstrip()}")

        return result

    def flush(self):
        """원본 스트림 플러시"""
        if hasattr(self.original_stream, 'flush'):
            self.original_stream.flush()

    def __getattr__(self, name):
        """나머지 속성들은 원본 스트림으로 위임"""
        return getattr(self.original_stream, name)


class TerminalCapturer:
    """
    터미널 출력 실시간 캡처 시스템

    stdout, stderr을 모두 캡처하면서 원본 출력은 유지
    """

    def __init__(self, buffer_size: int = 1000):
        """
        Args:
            buffer_size: 버퍼에 저장할 최대 라인 수
        """
        self.buffer_size = buffer_size
        self.buffer = deque(maxlen=buffer_size)

        # 원본 스트림 저장
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # 캡처 상태
        self.is_capturing = False
        self.tee_stdout: Optional[TeeOutput] = None
        self.tee_stderr: Optional[TeeOutput] = None

        # 스레드 안전성
        self.lock = threading.Lock()

        # 로깅 핸들러 패칭 기록 (복원용)
        self._patched_handlers = []  # list[tuple[logging.Handler, TextIO]]
        self._orig_addHandler = None  # type: ignore[var-annotated]

    # 내부 유틸: 로깅 스트림 핸들러 재지정/복원
    def _iter_all_log_handlers(self):
        handlers = []
        try:
            # 루트 핸들러들
            handlers.extend(logging.getLogger().handlers)
            handlers.extend(logging.root.handlers)
            # 자식 로거들
            for logger in logging.Logger.manager.loggerDict.values():
                if isinstance(logger, logging.Logger):
                    handlers.extend(logger.handlers)
        except Exception:
            pass
        return handlers

    def _retarget_stream_handlers(self):
        """기존/신규 StreamHandler의 스트림을 Tee로 라우팅"""
        self._patched_handlers.clear()
        for h in self._iter_all_log_handlers():
            if isinstance(h, logging.StreamHandler):
                stream = getattr(h, 'stream', None)
                if stream in (self.original_stderr, getattr(sys, '__stderr__', None)):
                    self._patched_handlers.append((h, stream))
                    h.stream = sys.stderr  # Tee로 교체
                elif stream in (self.original_stdout, getattr(sys, '__stdout__', None)):
                    self._patched_handlers.append((h, stream))
                    h.stream = sys.stdout  # Tee로 교체

        # 이후 추가되는 핸들러도 자동 라우팅
        if self._orig_addHandler is None:
            self._orig_addHandler = logging.Logger.addHandler

            def _patched_addHandler(logger_self, h):  # type: ignore[no-redef]
                try:
                    if isinstance(h, logging.StreamHandler):
                        stream = getattr(h, 'stream', None)
                        if stream in (self.original_stdout, getattr(sys, '__stdout__', None)):
                            h.stream = sys.stdout
                        elif stream in (self.original_stderr, getattr(sys, '__stderr__', None)):
                            h.stream = sys.stderr
                except Exception:
                    pass
                return self._orig_addHandler(logger_self, h)  # type: ignore[misc]

            logging.Logger.addHandler = _patched_addHandler  # type: ignore[assignment]

    def _restore_stream_handlers(self):
        """패칭했던 StreamHandler 스트림을 원복"""
        for h, original in self._patched_handlers:
            try:
                h.stream = original
            except Exception:
                pass
        self._patched_handlers.clear()
        if self._orig_addHandler is not None:
            try:
                logging.Logger.addHandler = self._orig_addHandler  # type: ignore[assignment]
            except Exception:
                pass
            self._orig_addHandler = None

    def start_capture(self) -> None:
        """터미널 출력 캡처 시작"""
        with self.lock:
            if self.is_capturing:
                return

            # Tee 출력 객체 생성
            self.tee_stdout = TeeOutput(self.original_stdout, self.buffer, "stdout")
            self.tee_stderr = TeeOutput(self.original_stderr, self.buffer, "stderr")

            # 시스템 출력 스트림 교체
            sys.stdout = self.tee_stdout
            sys.stderr = self.tee_stderr

            self.is_capturing = True

            # 기존 로깅 StreamHandler들이 원본 스트림을 직접 참조 중이면 Tee로 재지정
            self._retarget_stream_handlers()

            # 캡처 시작 로그
            self.buffer.append(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] [SYSTEM] 🎯 터미널 캡처 시작"
            )

    def stop_capture(self) -> None:
        """터미널 출력 캡처 중지"""
        with self.lock:
            if not self.is_capturing:
                return

            # 캡처 중지 로그
            self.buffer.append(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] [SYSTEM] 🛑 터미널 캡처 중지"
            )

            # 로깅 핸들러 스트림 원복
            self._restore_stream_handlers()

            # 원본 스트림 복원
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr

            self.is_capturing = False
            self.tee_stdout = None
            self.tee_stderr = None

    def get_recent_output(self, lines: int = 50) -> List[str]:
        """최근 출력 라인 반환"""
        with self.lock:
            return list(self.buffer)[-lines:]

    def get_all_output(self) -> List[str]:
        """모든 캡처된 출력 반환"""
        with self.lock:
            return list(self.buffer)

    def clear_buffer(self) -> None:
        """버퍼 내용 삭제"""
        with self.lock:
            self.buffer.clear()
            self.buffer.append(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] [SYSTEM] 🗑️ 터미널 캡처 버퍼 클리어"
            )

    def get_buffer_stats(self) -> dict:
        """버퍼 통계 정보 반환"""
        with self.lock:
            return {
                "is_capturing": self.is_capturing,
                "buffer_size": len(self.buffer),
                "max_buffer_size": self.buffer_size,
                "buffer_usage": f"{len(self.buffer)}/{self.buffer_size}",
                "first_entry": self.buffer[0] if self.buffer else None,
                "last_entry": self.buffer[-1] if self.buffer else None,
            }

    def search_in_buffer(self, pattern: str, case_sensitive: bool = False) -> List[str]:
        """버퍼에서 패턴 검색"""
        with self.lock:
            if not case_sensitive:
                pattern = pattern.lower()
                return [line for line in self.buffer if pattern in line.lower()]
            else:
                return [line for line in self.buffer if pattern in line]

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.start_capture()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.stop_capture()

    def __del__(self):
        """소멸자 - 캡처 중지 보장"""
        if hasattr(self, 'is_capturing') and self.is_capturing:
            self.stop_capture()


# 전역 캡처 인스턴스 (싱글톤 패턴)
_global_capturer: Optional[TerminalCapturer] = None


def get_global_terminal_capturer() -> TerminalCapturer:
    """전역 터미널 캡처 인스턴스 반환"""
    global _global_capturer
    if _global_capturer is None:
        _global_capturer = TerminalCapturer()
    return _global_capturer


def start_global_terminal_capture() -> None:
    """전역 터미널 캡처 시작"""
    capturer = get_global_terminal_capturer()
    capturer.start_capture()


def stop_global_terminal_capture() -> None:
    """전역 터미널 캡처 중지"""
    capturer = get_global_terminal_capturer()
    capturer.stop_capture()


def get_recent_terminal_output(lines: int = 50) -> List[str]:
    """최근 터미널 출력 반환"""
    capturer = get_global_terminal_capturer()
    return capturer.get_recent_output(lines)


# Alias for compatibility
get_terminal_capturer = get_global_terminal_capturer
start_terminal_capture = start_global_terminal_capture
stop_terminal_capture = stop_global_terminal_capture
get_captured_output = get_recent_terminal_output
