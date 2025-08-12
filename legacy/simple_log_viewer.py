"""
간단한 로그 뷰어 - 안전한 실시간 로그 표시
============================================

무한 루프 없는 안전한 로그 캡처 및 표시 시스템
- 파일 기반 로그 읽기 (stdout/stderr 캡처 없음)
- 단순한 폴링 방식
- UI 안전성 우선

DDD Infrastructure Layer: 외부 로깅 시스템과의 안전한 연동
"""

import os
import time
import threading
from pathlib import Path
from typing import Optional, Callable, List
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import get_logging_service


class SimpleLogViewer:
    """간단하고 안전한 로그 뷰어 - 파일 기반"""

    def __init__(self):
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._log_handlers: List[Callable[[str], None]] = []

        # 로그 파일 경로
        self._log_file_path: Optional[Path] = None
        self._last_position = 0

        # 폴링 설정
        self._poll_interval = 0.5  # 500ms 간격

        # 안전장치
        self._max_lines_per_update = 50  # 한 번에 최대 50줄

    def start(self) -> bool:
        """로그 뷰어 시작"""
        if self._is_running:
            return True

        try:
            # 로깅 서비스에서 세션 파일 경로 가져오기
            logging_service = get_logging_service()
            self._log_file_path = logging_service.get_current_session_file_path()

            if not self._log_file_path or not self._log_file_path.exists():
                return False

            # 기존 로그 로드
            self._load_existing_logs()

            # 폴링 스레드 시작
            self._is_running = True
            self._thread = threading.Thread(
                target=self._polling_worker,
                daemon=True,
                name="SimpleLogViewer"
            )
            self._thread.start()

            return True

        except Exception:
            return False

    def stop(self) -> None:
        """로그 뷰어 중단"""
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def add_log_handler(self, handler: Callable[[str], None]) -> None:
        """로그 핸들러 추가"""
        if handler not in self._log_handlers:
            self._log_handlers.append(handler)

    def remove_log_handler(self, handler: Callable[[str], None]) -> None:
        """로그 핸들러 제거"""
        if handler in self._log_handlers:
            self._log_handlers.remove(handler)

    def _load_existing_logs(self) -> None:
        """기존 로그 파일 내용 로드"""
        try:
            if not self._log_file_path or not self._log_file_path.exists():
                return

            with open(self._log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 최대 100줄만 로드 (초기 로딩 성능 고려)
            if len(lines) > 100:
                lines = lines[-100:]

            if lines:
                # 핸들러들에게 전달
                content = ''.join(lines).rstrip()
                for handler in self._log_handlers:
                    try:
                        handler(content)
                    except Exception:
                        pass  # 핸들러 에러 무시

            # 현재 파일 위치 설정
            self._last_position = self._log_file_path.stat().st_size

        except Exception:
            pass  # 로드 실패 무시

    def _polling_worker(self) -> None:
        """파일 폴링 워커 스레드"""
        while self._is_running:
            try:
                self._check_file_updates()
                time.sleep(self._poll_interval)
            except Exception:
                # 모든 예외 무시하여 안정성 보장
                time.sleep(self._poll_interval)

    def _check_file_updates(self) -> None:
        """파일 업데이트 확인 및 처리"""
        try:
            if not self._log_file_path or not self._log_file_path.exists():
                return

            current_size = self._log_file_path.stat().st_size

            # 파일이 커진 경우에만 처리
            if current_size > self._last_position:
                with open(self._log_file_path, 'r', encoding='utf-8') as f:
                    f.seek(self._last_position)
                    new_content = f.read()

                if new_content.strip():
                    # 줄 단위로 분리
                    new_lines = new_content.rstrip().split('\n')

                    # 최대 줄 수 제한
                    if len(new_lines) > self._max_lines_per_update:
                        new_lines = new_lines[-self._max_lines_per_update:]

                    if new_lines and new_lines != ['']:
                        # 핸들러들에게 전달
                        content = '\n'.join(new_lines)
                        for handler in self._log_handlers:
                            try:
                                handler(content)
                            except Exception:
                                pass  # 핸들러 에러 무시

                self._last_position = current_size

        except Exception:
            pass  # 모든 예외 무시

    def get_status(self) -> dict:
        """현재 상태 반환"""
        return {
            'is_running': self._is_running,
            'log_file': str(self._log_file_path) if self._log_file_path else None,
            'file_size': self._last_position,
            'handlers_count': len(self._log_handlers)
        }
