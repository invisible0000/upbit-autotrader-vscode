"""
Infrastructure 로깅 실시간 캡처 시스템
====================================

Phase 2: Infrastructure Integration
Infrastructure 로깅 시스템에서 실시간으로 로그를 캡처하여
로깅 관리 탭으로 전달하는 시스템입니다.

DDD 아키텍처:
- Infrastructure Layer: 로깅 시스템과의 직접 연동
- Application Layer: UI Presenter로 데이터 전달
- Presentation Layer: 사용자에게 실시간 로그 표시

주요 기능:
- 실시간 로그 스트림 캡처
- 환경변수 기반 필터링
- 배치 업데이트 최적화
- 메모리 사용량 제어
"""

import logging
import threading
import os
import time
import sys
from typing import List, Callable, Optional, Dict, Any, TextIO
from queue import Queue, Empty
from pathlib import Path

from upbit_auto_trading.infrastructure.logging import get_logging_service


class ConsoleCapture:
    """터미널 stdout/stderr 캡처 클래스 - 무한 루프 방지 강화"""

    def __init__(self, console_queue: Queue):
        self._console_queue = console_queue
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._is_writing = False  # 재귀 호출 방지 플래그
        self._recursion_depth = 0  # 추가 재귀 방지
        self._max_recursion_depth = 3  # 최대 재귀 깊이

    def write(self, text: str):
        """stdout/stderr write 가로채기 - 안전한 재귀 방지"""
        # 강화된 재귀 방지 체크
        if self._is_writing or self._recursion_depth > self._max_recursion_depth:
            # 원본 출력만 수행하고 즉시 반환
            try:
                self._original_stdout.write(text)
                self._original_stdout.flush()
            except Exception:
                pass  # 출력 실패도 무시하여 안정성 보장
            return

        try:
            self._is_writing = True
            self._recursion_depth += 1

            # 원본 출력 먼저 수행 (안정성 우선)
            try:
                self._original_stdout.write(text)
                self._original_stdout.flush()
            except Exception:
                pass  # 원본 출력 실패 무시

            # 콘솔 캐처링은 필수 조건에서만 수행
            if (text.strip() and
                    len(text.strip()) > 0 and
                    self._recursion_depth <= 1 and  # 첫 번째 레벨에서만
                    hasattr(self, '_console_queue')):

                try:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    formatted_text = f"[{timestamp}] CONSOLE: {text.strip()}"

                    # 논블로킹 큐 추가 (타임아웃 없음)
                    if not self._console_queue.full():
                        self._console_queue.put_nowait(formatted_text)
                    # 큐가 가득 찬 경우 무시 (에러 없음)

                except Exception:
                    pass  # 모든 큐 관련 에러 무시

        except Exception:
            pass  # 모든 예외 무시하여 시스템 안정성 보장
        finally:
            self._recursion_depth = max(0, self._recursion_depth - 1)
            self._is_writing = False

    def flush(self):
        """flush 메서드 (호환성) - 안전한 처리"""
        # 재귀 상태에서는 flush 수행하지 않음
        if not self._is_writing and self._recursion_depth == 0:
            try:
                self._original_stdout.flush()
            except Exception:
                pass  # flush 실패도 무시



class LogStreamCapture:
    """Infrastructure 로깅 시스템에서 실시간 로그 캡처

    Phase 2 핵심 컴포넌트:
    - Infrastructure 로깅 서비스와 직접 연동
    - 실시간 로그 메시지를 UI Presenter로 전달
    - 환경변수 기반 스마트 필터링 지원
    """

    def __init__(self, max_buffer_size: int = 1000):
        """LogStreamCapture 초기화

        Args:
            max_buffer_size: 메모리 사용량 제어를 위한 최대 버퍼 크기
        """
        self._handlers: List[Callable[[str], None]] = []
        self._console_handlers: List[Callable[[str], None]] = []
        self._is_capturing = False
        self._lock = threading.RLock()

        # 배치 업데이트를 위한 큐 시스템
        self._log_queue = Queue(maxsize=max_buffer_size)
        self._console_queue = Queue(maxsize=max_buffer_size)
        self._batch_thread: Optional[threading.Thread] = None
        self._file_tail_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Infrastructure 로깅 서비스 연동
        self._logging_service = None
        self._capture_handler: Optional[logging.Handler] = None

        # 로그 파일 실시간 추적
        self._log_file_path: Optional[Path] = None
        self._last_file_position = 0

        # Console stdout/stderr 캡처
        self._console_capture: Optional[ConsoleCapture] = None
        self._original_stdout = None
        self._original_stderr = None

        # 성능 모니터링
        self._total_logs_captured = 0
        self._total_console_captured = 0
        self._start_time = datetime.now()

    def start_capture(self) -> bool:
        """실시간 로그 캡처 시작

        Returns:
            bool: 캡처 시작 성공 여부
        """
        with self._lock:
            if self._is_capturing:
                return True

            try:
                # Infrastructure 로깅 서비스 연결
                self._logging_service = get_logging_service()

                # 커스텀 핸들러 생성 및 추가
                self._capture_handler = self._create_capture_handler()

                # Infrastructure 로깅 시스템의 모든 로거에 핸들러 추가
                # Infrastructure 로거들은 propagate=False이므로 개별 등록 필요

                # 1. 기존 로거들에 핸들러 추가
                existing_loggers = [name for name in logging.Logger.manager.loggerDict
                                  if name.startswith('upbit.')]
                for logger_name in existing_loggers:
                    logger = logging.getLogger(logger_name)
                    if self._capture_handler not in logger.handlers:
                        logger.addHandler(self._capture_handler)

                # 2. 새로 생성되는 로거들을 위해 upbit 루트에도 추가
                upbit_logger = logging.getLogger('upbit')
                upbit_logger.addHandler(self._capture_handler)

                # 3. Infrastructure 로깅 서비스에서 새 로거 생성 시 자동 등록을 위한 훅
                # self._hook_logger_creation()  # 일단 주석 처리

                # 배치 처리 스레드 시작
                self._start_batch_processor()

                # 로그 파일 실시간 추적 시작
                self._start_file_tail()

                # Console stdout/stderr 캡처 시작
                self._start_console_capture()

                self._is_capturing = True
                self._start_time = datetime.now()

                # print(f"✅ LogStreamCapture 시작됨 - {self._start_time.strftime('%H:%M:%S')}")
                # print(f"📊 등록된 로거 수: {len(existing_loggers) + 1}")
                # print(f"📄 세션 로그 파일 추적 시작")
                return True

            except Exception as e:
                # print(f"❌ LogStreamCapture 시작 실패: {e}")
                return False

    def stop_capture(self) -> None:
        """실시간 로그 캡처 중단"""
        with self._lock:
            if not self._is_capturing:
                return

            try:
                # 배치 처리 중단
                self._stop_event.set()
                if self._batch_thread and self._batch_thread.is_alive():
                    self._batch_thread.join(timeout=2.0)

                # 파일 추적 스레드 중단
                if self._file_tail_thread and self._file_tail_thread.is_alive():
                    self._file_tail_thread.join(timeout=2.0)

                # 핸들러 제거
                if self._capture_handler:
                    root_logger = logging.getLogger('upbit_auto_trading')
                    root_logger.removeHandler(self._capture_handler)
                    self._capture_handler = None

                # Console 캡처 중단
                self._stop_console_capture()

                self._is_capturing = False

                duration = datetime.now() - self._start_time
                # print(f"🛑 LogStreamCapture 중단됨 - {duration.total_seconds():.1f}초 동안 {self._total_logs_captured}개 로그 캡처")

            except Exception as e:
                # print(f"⚠️ LogStreamCapture 중단 중 오류: {e}")
                pass

    def add_handler(self, handler: Callable[[str], None]) -> None:
        """세션 로그 파일 메시지 핸들러 추가

        Args:
            handler: 로그 메시지를 처리할 콜백 함수
        """
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)
                # print(f"📝 LogStreamCapture 핸들러 추가됨 (총 {len(self._handlers)}개)")

    def add_console_handler(self, handler: Callable[[str], None]) -> None:
        """콘솔 출력 핸들러 추가

        Args:
            handler: 콘솔 출력을 처리할 콜백 함수
        """
        with self._lock:
            if handler not in self._console_handlers:
                self._console_handlers.append(handler)
                # print(f"💻 콘솔 핸들러 추가됨 (총 {len(self._console_handlers)}개)")

    def remove_handler(self, handler: Callable[[str], None]) -> None:
        """세션 로그 파일 핸들러 제거

        Args:
            handler: 제거할 핸들러 함수
        """
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)
                # print(f"🗑️ LogStreamCapture 핸들러 제거됨 (총 {len(self._handlers)}개)")

    def get_capture_stats(self) -> Dict[str, Any]:
        """캡처 통계 정보 반환

        Returns:
            Dict[str, Any]: 캡처 통계 (로그 수, 시간, 상태 등)
        """
        duration = datetime.now() - self._start_time
        return {
            'is_capturing': self._is_capturing,
            'total_logs': self._total_logs_captured,
            'total_console': self._total_console_captured,
            'duration_seconds': duration.total_seconds(),
            'handlers_count': len(self._handlers),
            'console_handlers_count': len(self._console_handlers),
            'log_queue_size': self._log_queue.qsize() if hasattr(self._log_queue, 'qsize') else 0,
            'console_queue_size': self._console_queue.qsize() if hasattr(self._console_queue, 'qsize') else 0
        }

    def _create_capture_handler(self) -> logging.Handler:
        """실시간 캡처용 로깅 핸들러 생성

        Returns:
            logging.Handler: 실시간 캡처 핸들러
        """
        class RealTimeHandler(logging.Handler):
            """실시간 로그 캡처 핸들러"""

            def __init__(self, callback: Callable[[str], None]):
                super().__init__()
                self.callback = callback

                # Infrastructure 로깅 시스템 포맷터와 동일하게 설정
                formatter = logging.Formatter(
                    '%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                self.setFormatter(formatter)

            def emit(self, record: logging.LogRecord) -> None:
                """로그 레코드를 처리하여 UI로 전달"""
                try:
                    # 환경변수 기반 필터링 (Phase 2 스마트 필터링)
                    if not self._should_capture_log(record):
                        return

                    # 로그 메시지 포맷팅
                    log_entry = self.format(record)

                    # 큐에 추가 (비동기 처리)
                    self.callback(log_entry)

                except Exception:
                    # 로깅 중 에러는 무시 (로깅 시스템 안정성 유지)
                    pass

            def _should_capture_log(self, record: logging.LogRecord) -> bool:
                """환경변수 기반 로그 필터링 결정

                Args:
                    record: 로그 레코드

                Returns:
                    bool: 캡처할지 여부
                """
                import os

                # UPBIT_LOG_LEVEL 환경변수 확인
                env_level = os.getenv('UPBIT_LOG_LEVEL', 'INFO').upper()
                level_priority = {
                    'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50
                }

                min_level = level_priority.get(env_level, 20)  # 기본값: INFO
                return record.levelno >= min_level

        return RealTimeHandler(self._emit_to_queue)

    def _emit_to_queue(self, log_entry: str) -> None:
        """로그 엔트리를 큐에 추가 (배치 처리용)

        Args:
            log_entry: 포맷된 로그 메시지
        """
        try:
            # 큐가 가득 찬 경우 오래된 로그 제거
            if self._log_queue.full():
                try:
                    self._log_queue.get_nowait()  # 오래된 로그 제거
                except Empty:
                    pass

            self._log_queue.put_nowait(log_entry)
            self._total_logs_captured += 1

        except Exception:
            # 큐 에러는 무시 (로깅 시스템 안정성 유지)
            pass

    def _start_batch_processor(self) -> None:
        """배치 처리 스레드 시작"""
        self._stop_event.clear()
        self._batch_thread = threading.Thread(
            target=self._batch_processor,
            name="LogStreamCapture-BatchProcessor",
            daemon=True
        )
        self._batch_thread.start()

    def _batch_processor(self) -> None:
        """배치 로그 처리 루프

        성능 최적화를 위해 로그를 배치로 모아서 UI에 전달합니다.
        """
        batch_logs = []
        batch_console = []
        batch_size = 10  # 한 번에 처리할 로그 수
        timeout = 0.1    # 배치 대기 시간 (100ms)

        while not self._stop_event.is_set():
            try:
                # 로그 큐에서 수집
                try:
                    log_entry = self._log_queue.get(timeout=timeout)
                    batch_logs.append(log_entry)
                except Empty:
                    pass

                # 콘솔 큐에서 수집
                try:
                    console_entry = self._console_queue.get_nowait()
                    batch_console.append(console_entry)
                    self._total_console_captured += 1
                except Empty:
                    pass

                # 배치 처리 조건 확인
                should_process = (
                    len(batch_logs) >= batch_size or
                    len(batch_console) >= batch_size or
                    (batch_logs and self._log_queue.empty()) or
                    (batch_console and self._console_queue.empty())
                )

                if should_process:
                    if batch_logs:
                        self._process_batch(batch_logs)
                        batch_logs.clear()
                    if batch_console:
                        self._process_console_batch(batch_console)
                        batch_console.clear()

            except Exception as e:
                # 에러 발생 시 현재 배치 처리하고 계속
                # 에러 정보는 무시하여 무한루프 방지
                if batch_logs:
                    self._process_batch(batch_logs)
                    batch_logs.clear()
                if batch_console:
                    self._process_console_batch(batch_console)
                    batch_console.clear()

        # 종료 시 남은 배치 처리
        if batch_logs:
            self._process_batch(batch_logs)
        if batch_console:
            self._process_console_batch(batch_console)

    def _process_batch(self, batch_logs: List[str]) -> None:
        """배치 로그를 모든 핸들러에 전달

        Args:
            batch_logs: 처리할 로그 배치
        """
        if not batch_logs:
            return

        with self._lock:
            handlers_copy = self._handlers.copy()

        # 모든 핸들러에 배치 전달
        for handler in handlers_copy:
            try:
                # 배치를 한 번에 전달 (성능 최적화)
                combined_logs = '\n'.join(batch_logs)
                handler(combined_logs)
            except Exception:
                pass  # 로그 핸들러 오류 무시

    def _process_console_batch(self, batch_console: List[str]) -> None:
        """배치 콘솔 출력을 모든 콘솔 핸들러에 전달

        Args:
            batch_console: 처리할 콘솔 출력 배치
        """
        if not batch_console:
            return

        with self._lock:
            console_handlers_copy = self._console_handlers.copy()

        # 모든 콘솔 핸들러에 배치 전달
        for handler in console_handlers_copy:
            try:
                # 배치를 한 번에 전달 (성능 최적화)
                combined_console = '\n'.join(batch_console)
                handler(combined_console)
            except Exception:
                pass  # 콘솔 핸들러 오류 무시

    def _start_file_tail(self) -> None:
        """로그 파일 실시간 추적 시작"""
        try:
            # Infrastructure 로깅 서비스에서 현재 세션 파일 경로 가져오기
            if self._logging_service:
                self._log_file_path = self._logging_service.get_current_session_file_path()

            if self._log_file_path and self._log_file_path.exists():
                # 현재 파일 크기부터 시작 (기존 내용은 한 번에 로드)
                self._last_file_position = 0

                # 기존 파일 내용 한 번에 로드
                self._load_existing_log_content()

                # 파일 추적 스레드 시작
                self._file_tail_thread = threading.Thread(
                    target=self._file_tail_worker,
                    daemon=True,
                    name="LogFileTailThread"
                )
                self._file_tail_thread.start()
                # print(f"📄 로그 파일 추적 시작: {self._log_file_path}")
            else:
                # print("⚠️ 세션 로그 파일을 찾을 수 없음")
                pass

        except Exception:
            # print(f"❌ 로그 파일 추적 시작 실패: {e}")  # 무한루프 방지를 위해 주석처리
            pass

    def _start_console_capture(self) -> None:
        """Console stdout/stderr 캡처 시작"""
        try:
            if not self._console_capture:
                # 원본 저장
                self._original_stdout = sys.stdout
                self._original_stderr = sys.stderr

                # Console capture 객체 생성
                self._console_capture = ConsoleCapture(self._console_queue)

                # stdout/stderr 교체
                sys.stdout = self._console_capture
                sys.stderr = self._console_capture

                # print("✅ Console stdout/stderr 캡처 시작")  # 무한루프 방지를 위해 주석처리
        except Exception:
            # print(f"❌ Console 캡처 시작 실패: {e}")  # 무한루프 방지를 위해 주석처리
            pass

    def _stop_console_capture(self) -> None:
        """Console stdout/stderr 캡처 중단"""
        try:
            if self._original_stdout and self._original_stderr:
                # 원본 복원
                sys.stdout = self._original_stdout
                sys.stderr = self._original_stderr

                self._console_capture = None
                self._original_stdout = None
                self._original_stderr = None

                # print("✅ Console stdout/stderr 캡처 중단")  # 무한루프 방지를 위해 주석처리
        except Exception:
            # print(f"❌ Console 캡처 중단 실패: {e}")  # 무한루프 방지를 위해 주석처리
            pass

    def _load_existing_log_content(self) -> None:
        """기존 로그 파일 내용을 한 번에 로드 (최대 1000줄)"""
        try:
            if not self._log_file_path or not self._log_file_path.exists():
                return

            with open(self._log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 최대 1000줄로 제한
            if len(lines) > 1000:
                lines = lines[-1000:]

            # 배치로 전달
            if lines:
                # 줄바꿈 제거하고 전달 (빈 줄 필터링 제거)
                log_lines = [line.rstrip('\n\r') for line in lines]
                for handler in self._handlers:
                    try:
                        combined_logs = '\n'.join(log_lines)
                        handler(combined_logs)
                    except Exception:
                        pass  # 기존 로그 로드 핸들러 오류 무시

                # print(f"📄 기존 로그 {len(log_lines)}줄 로드 완료 (원본: {len(lines)}줄)")  # 무한루프 방지

            # 현재 파일 위치 설정
            self._last_file_position = self._log_file_path.stat().st_size

        except Exception as e:
            print(f"❌ 기존 로그 내용 로드 실패: {e}")

    def _file_tail_worker(self) -> None:
        """로그 파일 실시간 추적 워커 스레드"""
        try:
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
                            # 줄 단위로 분리 (빈 줄 필터링 제거)
                            new_lines = new_content.split('\n')
                            # 마지막 줄이 빈 문자열이면 제거 (split 특성상)
                            if new_lines and not new_lines[-1]:
                                new_lines = new_lines[:-1]

                            if new_lines:
                                # 큐에 추가 (기존 실시간 로그와 동일한 방식)
                                for line in new_lines:
                                    try:
                                        self._log_queue.put(line, timeout=0.1)
                                    except Exception:
                                        break  # 큐가 가득 차면 무시

                        self._last_file_position = current_size

                    time.sleep(0.1)  # 100ms 간격으로 확인

                except Exception as e:
                    print(f"⚠️ 파일 추적 중 오류: {e}")
                    time.sleep(1)

        except Exception as e:
            print(f"❌ 파일 추적 워커 오류: {e}")

    def __del__(self):
        """소멸자: 리소스 정리"""
        try:
            self.stop_capture()
        except Exception:
            pass
