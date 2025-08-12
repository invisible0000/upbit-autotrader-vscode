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
from typing import List, Callable, Optional, Dict, Any
from datetime import datetime
from queue import Queue, Empty

from upbit_auto_trading.infrastructure.logging import get_logging_service


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
        self._is_capturing = False
        self._lock = threading.RLock()

        # 배치 업데이트를 위한 큐 시스템
        self._log_queue = Queue(maxsize=max_buffer_size)
        self._batch_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Infrastructure 로깅 서비스 연동
        self._logging_service = None
        self._capture_handler: Optional[logging.Handler] = None

        # 성능 모니터링
        self._total_logs_captured = 0
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

                # Infrastructure 로깅 시스템의 루트 로거에 핸들러 추가
                root_logger = logging.getLogger('upbit_auto_trading')
                root_logger.addHandler(self._capture_handler)

                # 배치 처리 스레드 시작
                self._start_batch_processor()

                self._is_capturing = True
                self._start_time = datetime.now()

                print(f"✅ LogStreamCapture 시작됨 - {self._start_time.strftime('%H:%M:%S')}")
                return True

            except Exception as e:
                print(f"❌ LogStreamCapture 시작 실패: {e}")
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

                # 핸들러 제거
                if self._capture_handler:
                    root_logger = logging.getLogger('upbit_auto_trading')
                    root_logger.removeHandler(self._capture_handler)
                    self._capture_handler = None

                self._is_capturing = False

                duration = datetime.now() - self._start_time
                print(f"🛑 LogStreamCapture 중단됨 - {duration.total_seconds():.1f}초 동안 {self._total_logs_captured}개 로그 캡처")

            except Exception as e:
                print(f"⚠️ LogStreamCapture 중단 중 오류: {e}")

    def add_handler(self, handler: Callable[[str], None]) -> None:
        """로그 메시지 핸들러 추가

        Args:
            handler: 로그 메시지를 처리할 콜백 함수
        """
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)
                print(f"📝 LogStreamCapture 핸들러 추가됨 (총 {len(self._handlers)}개)")

    def remove_handler(self, handler: Callable[[str], None]) -> None:
        """로그 메시지 핸들러 제거

        Args:
            handler: 제거할 핸들러 함수
        """
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)
                print(f"🗑️ LogStreamCapture 핸들러 제거됨 (총 {len(self._handlers)}개)")

    def get_capture_stats(self) -> Dict[str, Any]:
        """캡처 통계 정보 반환

        Returns:
            Dict[str, Any]: 캡처 통계 (로그 수, 시간, 상태 등)
        """
        duration = datetime.now() - self._start_time
        return {
            'is_capturing': self._is_capturing,
            'total_logs': self._total_logs_captured,
            'duration_seconds': duration.total_seconds(),
            'handlers_count': len(self._handlers),
            'queue_size': self._log_queue.qsize() if hasattr(self._log_queue, 'qsize') else 0
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
        batch_size = 10  # 한 번에 처리할 로그 수
        timeout = 0.1    # 배치 대기 시간 (100ms)

        while not self._stop_event.is_set():
            try:
                # 큐에서 로그 수집
                try:
                    log_entry = self._log_queue.get(timeout=timeout)
                    batch_logs.append(log_entry)
                except Empty:
                    # 타임아웃 시 현재 배치 처리
                    pass

                # 배치 크기에 도달하거나 타임아웃 시 처리
                if len(batch_logs) >= batch_size or (batch_logs and self._log_queue.empty()):
                    self._process_batch(batch_logs)
                    batch_logs.clear()

            except Exception as e:
                print(f"⚠️ 배치 프로세서 오류 (복구 중): {e}")
                # 에러 발생 시 현재 배치 처리하고 계속
                if batch_logs:
                    self._process_batch(batch_logs)
                    batch_logs.clear()

        # 종료 시 남은 배치 처리
        if batch_logs:
            self._process_batch(batch_logs)

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
            except Exception as e:
                print(f"⚠️ 로그 핸들러 오류: {e}")

    def __del__(self):
        """소멸자: 리소스 정리"""
        try:
            self.stop_capture()
        except:
            pass
