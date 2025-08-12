"""
로그 캡처 시스템
===============

Infrastructure Layer - 로깅 시스템 통합
무한 루프 방지를 위한 안전한 로그 캡처 구현

주요 기능:
- 세션 로그 파일 실시간 읽기
- 배치 처리로 성능 최적화
- 안전한 에러 처리
"""

import threading
import time
from pathlib import Path
from typing import List, Callable, Optional
from datetime import datetime
from queue import Queue, Empty

from upbit_auto_trading.infrastructure.logging import get_logging_service


class LogCapture:
    """안전한 로그 파일 캡처 시스템"""

    def __init__(self, max_buffer_size: int = 1000):
        """LogCapture 초기화

        Args:
            max_buffer_size: 최대 버퍼 크기
        """
        self._handlers: List[Callable[[str], None]] = []
        self._is_capturing = False
        self._lock = threading.RLock()

        # 로그 큐 (논블로킹)
        self._log_queue = Queue(maxsize=max_buffer_size)
        self._processor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 로그 파일 추적
        self._log_file_path: Optional[Path] = None
        self._last_file_position = 0
        self._file_monitor_thread: Optional[threading.Thread] = None

        # 통계
        self._total_logs = 0
        self._start_time = datetime.now()

    def start_capture(self) -> bool:
        """로그 캡처 시작

        Returns:
            bool: 시작 성공 여부
        """
        with self._lock:
            if self._is_capturing:
                return True

            try:
                # 로깅 서비스에서 파일 경로 가져오기
                logging_service = get_logging_service()
                self._log_file_path = logging_service.get_current_session_file_path()

                if not self._log_file_path or not self._log_file_path.exists():
                    return False

                # 기존 로그 내용 로드
                self._load_existing_logs()

                # 처리 스레드 시작
                self._start_processor_thread()

                # 파일 모니터링 시작
                self._start_file_monitor()

                self._is_capturing = True
                return True

            except Exception:
                return False

    def stop_capture(self) -> None:
        """로그 캡처 중단"""
        with self._lock:
            if not self._is_capturing:
                return

            try:
                # 스레드 중단
                self._stop_event.set()

                if self._processor_thread and self._processor_thread.is_alive():
                    self._processor_thread.join(timeout=2.0)

                if self._file_monitor_thread and self._file_monitor_thread.is_alive():
                    self._file_monitor_thread.join(timeout=2.0)

                self._is_capturing = False

            except Exception:
                pass

    def add_handler(self, handler: Callable[[str], None]) -> None:
        """로그 핸들러 추가

        Args:
            handler: 로그 처리 콜백 함수
        """
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)

    def remove_handler(self, handler: Callable[[str], None]) -> None:
        """로그 핸들러 제거

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
            'total_logs': self._total_logs,
            'duration_seconds': duration.total_seconds(),
            'handlers_count': len(self._handlers),
            'queue_size': self._log_queue.qsize() if hasattr(self._log_queue, 'qsize') else 0
        }

    def _load_existing_logs(self) -> None:
        """기존 로그 파일 내용 로드"""
        try:
            if not self._log_file_path or not self._log_file_path.exists():
                return

            with open(self._log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 최대 1000줄로 제한
            if len(lines) > 1000:
                lines = lines[-1000:]

            # 핸들러에 전달
            if lines:
                log_content = ''.join(lines).rstrip()
                self._notify_handlers(log_content)

            # 파일 위치 설정
            self._last_file_position = self._log_file_path.stat().st_size

        except Exception:
            pass

    def _start_processor_thread(self) -> None:
        """로그 처리 스레드 시작"""
        self._stop_event.clear()
        self._processor_thread = threading.Thread(
            target=self._process_logs,
            name="LogCapture-Processor",
            daemon=True
        )
        self._processor_thread.start()

    def _start_file_monitor(self) -> None:
        """파일 모니터링 스레드 시작"""
        self._file_monitor_thread = threading.Thread(
            target=self._monitor_file,
            name="LogCapture-FileMonitor",
            daemon=True
        )
        self._file_monitor_thread.start()

    def _process_logs(self) -> None:
        """로그 처리 루프"""
        batch_logs = []
        batch_size = 10
        timeout = 0.1

        while not self._stop_event.is_set():
            try:
                # 큐에서 로그 수집
                try:
                    log_entry = self._log_queue.get(timeout=timeout)
                    batch_logs.append(log_entry)
                except Empty:
                    pass

                # 배치 처리 조건
                if (len(batch_logs) >= batch_size or
                    (batch_logs and self._log_queue.empty())):

                    if batch_logs:
                        combined_logs = '\n'.join(batch_logs)
                        self._notify_handlers(combined_logs)
                        self._total_logs += len(batch_logs)
                        batch_logs.clear()

            except Exception:
                # 에러 발생 시 현재 배치 처리하고 계속
                if batch_logs:
                    combined_logs = '\n'.join(batch_logs)
                    self._notify_handlers(combined_logs)
                    batch_logs.clear()

        # 종료 시 남은 배치 처리
        if batch_logs:
            combined_logs = '\n'.join(batch_logs)
            self._notify_handlers(combined_logs)

    def _monitor_file(self) -> None:
        """파일 변경 모니터링"""
        while not self._stop_event.is_set():
            try:
                if not self._log_file_path or not self._log_file_path.exists():
                    time.sleep(1)
                    continue

                current_size = self._log_file_path.stat().st_size

                # 파일이 커졌으면 새 내용 읽기
                if current_size > self._last_file_position:
                    with open(self._log_file_path, 'r', encoding='utf-8') as f:
                        f.seek(self._last_file_position)
                        new_content = f.read()

                    if new_content.strip():
                        # 줄 단위로 분리
                        new_lines = new_content.strip().split('\n')

                        # 큐에 추가
                        for line in new_lines:
                            if line.strip():
                                try:
                                    self._log_queue.put_nowait(line.strip())
                                except Exception:
                                    break  # 큐가 가득 차면 무시

                    self._last_file_position = current_size

                time.sleep(0.1)  # 100ms 간격

            except Exception:
                time.sleep(1)

    def _notify_handlers(self, log_content: str) -> None:
        """핸들러에 로그 전달

        Args:
            log_content: 로그 내용
        """
        if not log_content.strip():
            return

        with self._lock:
            handlers_copy = self._handlers.copy()

        for handler in handlers_copy:
            try:
                handler(log_content)
            except Exception:
                pass  # 핸들러 에러 무시

    def __del__(self):
        """소멸자: 리소스 정리"""
        try:
            self.stop_capture()
        except Exception:
            pass
