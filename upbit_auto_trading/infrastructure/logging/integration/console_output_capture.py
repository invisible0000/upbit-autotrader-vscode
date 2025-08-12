"""
콘솔 출력 캡처 시스템
===================

Infrastructure Layer - stdout/stderr 캡처
안전한 콘솔 출력 가로채기 및 UI 전달

주요 기능:
- stdout/stderr 안전 캡처
- 무한 루프 방지
- 배치 처리 최적화
"""

import sys
import threading
from typing import List, Callable, Optional, TextIO
from datetime import datetime
from queue import Queue, Empty


class ConsoleOutputCapture:
    """안전한 콘솔 출력 캡처 시스템"""

    def __init__(self, max_buffer_size: int = 500):
        """ConsoleOutputCapture 초기화

        Args:
            max_buffer_size: 최대 버퍼 크기
        """
        self._handlers: List[Callable[[str], None]] = []
        self._is_capturing = False
        self._lock = threading.RLock()

        # 콘솔 큐
        self._console_queue = Queue(maxsize=max_buffer_size)
        self._processor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 원본 stdout/stderr 저장
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._capture_wrapper: Optional['_CaptureWrapper'] = None

        # 통계
        self._total_captures = 0
        self._start_time = datetime.now()

    def start_capture(self) -> bool:
        """콘솔 캡처 시작

        Returns:
            bool: 시작 성공 여부
        """
        with self._lock:
            if self._is_capturing:
                return True

            try:
                # 캡처 래퍼 생성
                self._capture_wrapper = _CaptureWrapper(
                    self._original_stdout,
                    self._console_queue
                )

                # stdout/stderr 교체
                sys.stdout = self._capture_wrapper
                sys.stderr = self._capture_wrapper

                # 처리 스레드 시작
                self._start_processor_thread()

                self._is_capturing = True
                return True

            except Exception:
                self._restore_original_outputs()
                return False

    def stop_capture(self) -> None:
        """콘솔 캡처 중단"""
        with self._lock:
            if not self._is_capturing:
                return

            try:
                # 원본 출력 복원
                self._restore_original_outputs()

                # 처리 스레드 중단
                self._stop_event.set()
                if self._processor_thread and self._processor_thread.is_alive():
                    self._processor_thread.join(timeout=2.0)

                self._is_capturing = False

            except Exception:
                pass

    def add_handler(self, handler: Callable[[str], None]) -> None:
        """콘솔 출력 핸들러 추가

        Args:
            handler: 콘솔 출력 처리 콜백 함수
        """
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)

    def remove_handler(self, handler: Callable[[str], None]) -> None:
        """콘솔 출력 핸들러 제거

        Args:
            handler: 제거할 핸들러
        """
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)

    def get_stats(self) -> dict:
        """캡처 통계 반환

        Returns:
            dict: 통계 정보
        """
        duration = datetime.now() - self._start_time
        return {
            'is_capturing': self._is_capturing,
            'total_captures': self._total_captures,
            'duration_seconds': duration.total_seconds(),
            'handlers_count': len(self._handlers),
            'queue_size': self._console_queue.qsize() if hasattr(self._console_queue, 'qsize') else 0
        }

    def _restore_original_outputs(self) -> None:
        """원본 출력 복원"""
        try:
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr
            self._capture_wrapper = None
        except Exception:
            pass

    def _start_processor_thread(self) -> None:
        """콘솔 처리 스레드 시작"""
        self._stop_event.clear()
        self._processor_thread = threading.Thread(
            target=self._process_console_output,
            name="ConsoleCapture-Processor",
            daemon=True
        )
        self._processor_thread.start()

    def _process_console_output(self) -> None:
        """콘솔 출력 처리 루프"""
        batch_console = []
        batch_size = 5
        timeout = 0.1

        while not self._stop_event.is_set():
            try:
                # 큐에서 콘솔 출력 수집
                try:
                    console_entry = self._console_queue.get(timeout=timeout)
                    batch_console.append(console_entry)
                except Empty:
                    pass

                # 배치 처리 조건
                if (len(batch_console) >= batch_size or
                    (batch_console and self._console_queue.empty())):

                    if batch_console:
                        combined_console = '\n'.join(batch_console)
                        self._notify_handlers(combined_console)
                        self._total_captures += len(batch_console)
                        batch_console.clear()

            except Exception:
                # 에러 발생 시 현재 배치 처리하고 계속
                if batch_console:
                    combined_console = '\n'.join(batch_console)
                    self._notify_handlers(combined_console)
                    batch_console.clear()

        # 종료 시 남은 배치 처리
        if batch_console:
            combined_console = '\n'.join(batch_console)
            self._notify_handlers(combined_console)

    def _notify_handlers(self, console_content: str) -> None:
        """핸들러에 콘솔 출력 전달

        Args:
            console_content: 콘솔 출력 내용
        """
        if not console_content.strip():
            return

        with self._lock:
            handlers_copy = self._handlers.copy()

        for handler in handlers_copy:
            try:
                handler(console_content)
            except Exception:
                pass  # 핸들러 에러 무시

    def __del__(self):
        """소멸자: 리소스 정리"""
        try:
            self.stop_capture()
        except Exception:
            pass


class _CaptureWrapper:
    """stdout/stderr 캡처 래퍼 - 무한 루프 방지"""

    def __init__(self, original_output: TextIO, console_queue: Queue):
        """래퍼 초기화

        Args:
            original_output: 원본 출력 스트림
            console_queue: 콘솔 큐
        """
        self._original_output = original_output
        self._console_queue = console_queue
        self._is_writing = False  # 재귀 방지
        self._recursion_depth = 0
        self._max_recursion_depth = 2

    def _is_handler_output(self, text: str) -> bool:
        """핸들러 출력인지 감지하여 순환 방지

        Args:
            text: 검사할 텍스트

        Returns:
            bool: 핸들러 출력이면 True
        """
        # 정밀한 핸들러 출력 패턴들 (무한 루프 방지용)
        handler_patterns = [
            "📨 HANDLER_CALLED",    # 정확한 디버깅 메시지만 차단
            "📨 RECEIVED:",         # 수신 메시지 재귀 방지
            "� MANAGER_DEBUG:",    # 매니저 디버그 메시지만 차단
            "Presenter 통계:",      # 통계 출력 재귀 방지
            "🔍 TRACE",            # 트레이싱 메시지
            "TRACE [",             # 트레이싱 패턴
            "� args:",            # 메서드 트레이싱
            "📤 result:",          # 메서드 결과
        ]

        # 정밀 매칭: 전체 텍스트에서 패턴 검사
        for pattern in handler_patterns:
            if pattern in text:
                return True

        # 추가: 반복 패턴 감지 (무한 루프 패턴)
        if "💻 CONSOLE:" in text and text.count("💻 CONSOLE:") > 3:
            return True  # 한 메시지에 여러 번 반복되면 루프로 간주

        return False

    def write(self, text: str) -> None:
        """write 메서드 - 안전한 캡처"""
        # 강화된 재귀 방지
        if (self._is_writing or
            self._recursion_depth > self._max_recursion_depth or
            not hasattr(self, '_original_output')):

            # 원본 출력만 수행
            try:
                self._original_output.write(text)
                self._original_output.flush()
            except Exception:
                pass
            return

        try:
            self._is_writing = True
            self._recursion_depth += 1

            # 원본 출력 먼저 수행 (안정성 우선)
            try:
                self._original_output.write(text)
                self._original_output.flush()
            except Exception:
                pass

            # 큐에 추가 (조건부) - 순환 방지 강화
            if (text.strip() and
                len(text.strip()) > 0 and
                self._recursion_depth <= 1 and
                hasattr(self, '_console_queue') and
                not self._is_handler_output(text)):  # 핸들러 출력 감지

                try:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    # 터미널 디버깅 메시지도 캡처하도록 개선
                    formatted_text = f"[{timestamp}] CONSOLE: {text.strip()}"

                    # 논블로킹 큐 추가
                    if not self._console_queue.full():
                        self._console_queue.put_nowait(formatted_text)

                except Exception:
                    pass

        except Exception:
            pass
        finally:
            self._recursion_depth = max(0, self._recursion_depth - 1)
            self._is_writing = False

    def flush(self) -> None:
        """flush 메서드"""
        if not self._is_writing and self._recursion_depth == 0:
            try:
                self._original_output.flush()
            except Exception:
                pass
