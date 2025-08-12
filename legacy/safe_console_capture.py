"""
간단한 콘솔 출력 캡처 - 안전한 stdout/stderr 모니터링
================================================

무한 루프 없는 안전한 콘솔 출력 캡처 시스템
- print() 문들을 안전하게 캡처
- 재귀 호출 완전 차단
- 큐 기반 비동기 처리

DDD Infrastructure Layer: 콘솔 출력 안전 캡처
"""

import sys
import threading
import time
from queue import Queue, Empty
from typing import Optional, Callable, List, TextIO
from datetime import datetime


class SafeConsoleCapture:
    """안전한 콘솔 출력 캡처 - 무한 루프 방지"""

    def __init__(self):
        self._is_capturing = False
        self._console_handlers: List[Callable[[str], None]] = []

        # 원본 stdout/stderr 저장
        self._original_stdout: Optional[TextIO] = None
        self._original_stderr: Optional[TextIO] = None

        # 캡처 래퍼
        self._stdout_wrapper: Optional['OutputWrapper'] = None
        self._stderr_wrapper: Optional['OutputWrapper'] = None

        # 큐 기반 처리
        self._output_queue = Queue(maxsize=200)
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start_capture(self) -> bool:
        """콘솔 캡처 시작"""
        if self._is_capturing:
            return True

        try:
            # 원본 저장
            self._original_stdout = sys.stdout
            self._original_stderr = sys.stderr

            # 래퍼 생성
            self._stdout_wrapper = OutputWrapper(
                self._original_stdout,
                self._output_queue,
                "STDOUT"
            )
            self._stderr_wrapper = OutputWrapper(
                self._original_stderr,
                self._output_queue,
                "STDERR"
            )

            # sys.stdout/stderr 교체
            sys.stdout = self._stdout_wrapper
            sys.stderr = self._stderr_wrapper

            # 워커 스레드 시작
            self._stop_event.clear()
            self._worker_thread = threading.Thread(
                target=self._process_output_queue,
                daemon=True,
                name="ConsoleCapture"
            )
            self._worker_thread.start()

            self._is_capturing = True
            return True

        except Exception:
            self._restore_console()
            return False

    def stop_capture(self) -> None:
        """콘솔 캡처 중단"""
        if not self._is_capturing:
            return

        try:
            # 워커 스레드 중단
            self._stop_event.set()
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=2.0)

            # 콘솔 복원
            self._restore_console()

            self._is_capturing = False

        except Exception:
            pass  # 중단 중 에러 무시

    def add_console_handler(self, handler: Callable[[str], None]) -> None:
        """콘솔 출력 핸들러 추가"""
        if handler not in self._console_handlers:
            self._console_handlers.append(handler)

    def remove_console_handler(self, handler: Callable[[str], None]) -> None:
        """콘솔 출력 핸들러 제거"""
        if handler in self._console_handlers:
            self._console_handlers.remove(handler)

    def _restore_console(self) -> None:
        """원본 콘솔 복원"""
        try:
            if self._original_stdout:
                sys.stdout = self._original_stdout
            if self._original_stderr:
                sys.stderr = self._original_stderr
        except Exception:
            pass

    def _process_output_queue(self) -> None:
        """출력 큐 처리 워커"""
        batch = []
        batch_size = 10
        timeout = 0.1

        while not self._stop_event.is_set():
            try:
                # 큐에서 출력 수집
                try:
                    output_item = self._output_queue.get(timeout=timeout)
                    batch.append(output_item)
                except Empty:
                    pass

                # 배치 처리 조건
                if len(batch) >= batch_size or (batch and self._output_queue.empty()):
                    self._process_batch(batch)
                    batch.clear()

            except Exception:
                # 예외 발생 시 현재 배치 처리하고 계속
                if batch:
                    self._process_batch(batch)
                    batch.clear()
                time.sleep(0.1)

        # 종료 시 남은 배치 처리
        if batch:
            self._process_batch(batch)

    def _process_batch(self, batch: List[str]) -> None:
        """배치 출력 처리"""
        if not batch:
            return

        try:
            # 배치를 결합하여 핸들러에 전달
            combined_output = '\n'.join(batch)

            for handler in self._console_handlers:
                try:
                    handler(combined_output)
                except Exception:
                    pass  # 핸들러 에러 무시

        except Exception:
            pass  # 배치 처리 에러 무시

    def get_status(self) -> dict:
        """캡처 상태 반환"""
        return {
            'is_capturing': self._is_capturing,
            'queue_size': self._output_queue.qsize() if hasattr(self._output_queue, 'qsize') else 0,
            'handlers_count': len(self._console_handlers)
        }


class OutputWrapper:
    """안전한 출력 래퍼 - 무한 루프 완전 차단"""

    def __init__(self, original_stream: TextIO, queue: Queue, stream_type: str):
        self._original = original_stream
        self._queue = queue
        self._stream_type = stream_type
        self._in_write = False  # 재귀 방지 플래그

    def write(self, text: str):
        """출력 가로채기 - 강력한 재귀 방지"""
        # 재귀 호출 완전 차단
        if self._in_write:
            # 원본 출력만 수행
            try:
                self._original.write(text)
                self._original.flush()
            except Exception:
                pass
            return

        self._in_write = True
        try:
            # 원본 출력 먼저 (안정성 우선)
            try:
                self._original.write(text)
                self._original.flush()
            except Exception:
                pass

            # 큐에 추가 (조건부)
            if text.strip() and len(text.strip()) > 0:
                try:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    formatted = f"[{timestamp}] {self._stream_type}: {text.strip()}"

                    # 논블로킹 큐 추가
                    if not self._queue.full():
                        self._queue.put_nowait(formatted)

                except Exception:
                    pass  # 큐 에러 무시

        except Exception:
            pass  # 모든 예외 무시
        finally:
            self._in_write = False

    def flush(self):
        """flush 메서드"""
        if not self._in_write:
            try:
                self._original.flush()
            except Exception:
                pass

    def __getattr__(self, name):
        """다른 메서드들은 원본으로 위임"""
        return getattr(self._original, name)
