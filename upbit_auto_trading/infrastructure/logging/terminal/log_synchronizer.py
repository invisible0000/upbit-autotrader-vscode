"""
Log Synchronizer - 로그 동기화 시스템
===================================

터미널 출력과 LLM 로그 시스템을 동기화하는 중앙 관리 시스템
실시간 데이터 흐름과 일관성 보장
"""

import threading
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, field

from .terminal_capturer import TerminalCapturer, get_terminal_capturer
from .output_parser import TerminalOutputParser, ParsedOutput, OutputType, create_terminal_output_parser

@dataclass
class SyncState:
    """동기화 상태 정보"""
    last_sync_time: datetime = field(default_factory=datetime.now)
    total_synced: int = 0
    pending_items: int = 0
    sync_errors: int = 0
    is_running: bool = False
    last_error: Optional[str] = None

@dataclass
class SyncConfig:
    """동기화 설정"""
    sync_interval: float = 1.0  # 동기화 간격 (초)
    batch_size: int = 100  # 배치 처리 크기
    max_buffer_size: int = 1000  # 최대 버퍼 크기
    enable_file_output: bool = True  # 파일 출력 활성화
    llm_log_file: Optional[str] = None  # LLM 로그 파일 경로
    auto_cleanup: bool = True  # 자동 정리 활성화
    cleanup_interval_hours: int = 24  # 정리 간격 (시간)

class LogSynchronizer:
    """
    로그 동기화 중앙 관리 시스템

    터미널 출력을 실시간으로 파싱하고 LLM 로그 시스템과 동기화
    """

    def __init__(self, config: Optional[SyncConfig] = None):
        """동기화 시스템 초기화"""
        self.config = config or SyncConfig()
        self.state = SyncState()

        # 핵심 컴포넌트 초기화
        self.terminal_capturer = get_terminal_capturer()
        self.output_parser = create_terminal_output_parser()

        # 동기화 버퍼
        self.sync_buffer: deque = deque(maxlen=self.config.max_buffer_size)
        self.processed_items: List[ParsedOutput] = []

        # 스레딩 관리
        self._sync_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # 콜백 시스템
        self.event_callbacks: Dict[str, List[Callable]] = {
            'on_llm_report': [],
            'on_error': [],
            'on_warning': [],
            'on_performance': [],
            'on_status_change': []
        }

        # LLM 로그 파일 설정
        if self.config.llm_log_file:
            self.llm_log_path = Path(self.config.llm_log_file)
            self.llm_log_path.parent.mkdir(parents=True, exist_ok=True)

    def start(self) -> bool:
        """동기화 시작"""
        if self.state.is_running:
            return False

        try:
            # 터미널 캡쳐 시작
            self.terminal_capturer.start_capture()

            # 동기화 스레드 시작
            self._stop_event.clear()
            self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self._sync_thread.start()

            self.state.is_running = True
            self._trigger_callbacks('on_status_change', {'status': 'started'})

            return True

        except Exception as e:
            self.state.last_error = str(e)
            self.state.sync_errors += 1
            self._trigger_callbacks('on_error', {'error': str(e), 'context': 'start'})
            return False

    def stop(self) -> bool:
        """동기화 중지"""
        if not self.state.is_running:
            return False

        try:
            # 스레드 종료 신호
            self._stop_event.set()

            # 스레드 종료 대기
            if self._sync_thread and self._sync_thread.is_alive():
                self._sync_thread.join(timeout=5.0)

            # 터미널 캡쳐 중지
            self.terminal_capturer.stop_capture()

            # 마지막 동기화 실행
            self._process_pending_items()

            self.state.is_running = False
            self._trigger_callbacks('on_status_change', {'status': 'stopped'})

            return True

        except Exception as e:
            self.state.last_error = str(e)
            self.state.sync_errors += 1
            self._trigger_callbacks('on_error', {'error': str(e), 'context': 'stop'})
            return False

    def _sync_loop(self) -> None:
        """동기화 메인 루프"""
        while not self._stop_event.is_set():
            try:
                # 터미널 출력 수집
                terminal_lines = self.terminal_capturer.get_output()

                if terminal_lines:
                    # 출력 파싱
                    parsed_outputs = self.output_parser.parse_output(terminal_lines)

                    # 버퍼에 추가
                    with self._lock:
                        for output in parsed_outputs:
                            if len(self.sync_buffer) >= self.config.max_buffer_size:
                                # 버퍼 오버플로우 시 오래된 항목 제거
                                self.sync_buffer.popleft()
                            self.sync_buffer.append(output)

                    # 배치 처리
                    if len(self.sync_buffer) >= self.config.batch_size:
                        self._process_pending_items()

                # 마지막 동기화 시간 업데이트
                self.state.last_sync_time = datetime.now()

                # 다음 동기화까지 대기
                time.sleep(self.config.sync_interval)

            except Exception as e:
                self.state.last_error = str(e)
                self.state.sync_errors += 1
                self._trigger_callbacks('on_error', {'error': str(e), 'context': 'sync_loop'})
                time.sleep(self.config.sync_interval)  # 에러 시에도 잠시 대기

    def _process_pending_items(self) -> None:
        """대기 중인 항목들 처리"""
        items_to_process = []

        # 버퍼에서 항목들 추출
        with self._lock:
            while self.sync_buffer and len(items_to_process) < self.config.batch_size:
                items_to_process.append(self.sync_buffer.popleft())

        if not items_to_process:
            return

        # 각 항목 처리
        for item in items_to_process:
            try:
                self._process_single_item(item)
                self.state.total_synced += 1

            except Exception as e:
                self.state.sync_errors += 1
                self._trigger_callbacks('on_error', {
                    'error': str(e),
                    'context': 'process_item',
                    'item': item.raw_line[:100]
                })

        # 처리된 항목들 저장
        self.processed_items.extend(items_to_process)

        # 자동 정리
        if self.config.auto_cleanup:
            self._cleanup_old_items()

    def _process_single_item(self, item: ParsedOutput) -> None:
        """단일 항목 처리"""
        # 타입별 콜백 실행
        if item.type == OutputType.LLM_REPORT:
            self._trigger_callbacks('on_llm_report', {'item': item})
        elif item.type == OutputType.ERROR:
            self._trigger_callbacks('on_error', {'item': item})
        elif item.type == OutputType.WARNING:
            self._trigger_callbacks('on_warning', {'item': item})
        elif item.type == OutputType.PERFORMANCE:
            self._trigger_callbacks('on_performance', {'item': item})

        # LLM 로그 파일에 기록
        if self.config.enable_file_output and hasattr(self, 'llm_log_path'):
            self._write_to_llm_log(item)

    def _write_to_llm_log(self, item: ParsedOutput) -> None:
        """LLM 로그 파일에 기록"""
        try:
            log_entry = self._format_llm_log_entry(item)

            with open(self.llm_log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')

        except Exception as e:
            # 파일 쓰기 실패는 조용히 처리 (무한 루프 방지)
            pass

    def _format_llm_log_entry(self, item: ParsedOutput) -> str:
        """LLM 로그 엔트리 포맷팅"""
        timestamp_str = item.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        if item.type == OutputType.LLM_REPORT:
            # LLM 보고서는 원본 형태 유지
            return f"[{timestamp_str}] {item.raw_line}"
        else:
            # 다른 타입들은 LLM 친화적 형태로 변환
            component = item.component or "Unknown"
            message = item.message or item.raw_line

            return f"[{timestamp_str}] 🤖 LLM_SYNC: Type={item.type.value}, Component={component}, Message={message[:200]}"

    def _cleanup_old_items(self) -> None:
        """오래된 항목들 정리"""
        if not self.processed_items:
            return

        cutoff_time = datetime.now() - timedelta(hours=self.config.cleanup_interval_hours)

        # 오래된 항목들 필터링
        old_count = len(self.processed_items)
        self.processed_items = [
            item for item in self.processed_items
            if item.timestamp > cutoff_time
        ]

        cleaned_count = old_count - len(self.processed_items)
        if cleaned_count > 0:
            self._trigger_callbacks('on_status_change', {
                'status': 'cleanup',
                'cleaned_items': cleaned_count
            })

    def register_callback(self, event_type: str, callback: Callable) -> bool:
        """콜백 등록"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
            return True
        return False

    def _trigger_callbacks(self, event_type: str, data: Dict[str, Any]) -> None:
        """콜백 실행"""
        for callback in self.event_callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                # 콜백 실행 실패는 조용히 처리
                pass

    def get_sync_state(self) -> SyncState:
        """현재 동기화 상태 반환"""
        self.state.pending_items = len(self.sync_buffer)
        return self.state

    def get_recent_items(self, count: int = 50,
                        output_types: Optional[List[OutputType]] = None) -> List[ParsedOutput]:
        """최근 항목들 반환"""
        items = self.processed_items[-count:] if count > 0 else self.processed_items

        if output_types:
            items = [item for item in items if item.type in output_types]

        return sorted(items, key=lambda x: x.timestamp, reverse=True)

    def get_parsing_stats(self) -> Dict[str, Any]:
        """파싱 통계 반환"""
        return self.output_parser.get_parsing_stats()

    def clear_processed_items(self) -> int:
        """처리된 항목들 정리"""
        count = len(self.processed_items)
        self.processed_items.clear()
        self.output_parser.clear_stats()
        return count

    def force_sync(self) -> bool:
        """강제 동기화 실행"""
        try:
            self._process_pending_items()
            return True
        except Exception as e:
            self.state.last_error = str(e)
            self.state.sync_errors += 1
            return False

# 전역 인스턴스 관리
_global_synchronizer: Optional[LogSynchronizer] = None
_sync_lock = threading.Lock()

def get_log_synchronizer(config: Optional[SyncConfig] = None) -> LogSynchronizer:
    """전역 로그 동기화 인스턴스 반환"""
    global _global_synchronizer

    with _sync_lock:
        if _global_synchronizer is None:
            _global_synchronizer = LogSynchronizer(config)
        return _global_synchronizer

def create_log_synchronizer(config: Optional[SyncConfig] = None) -> LogSynchronizer:
    """새로운 로그 동기화 인스턴스 생성"""
    return LogSynchronizer(config)
