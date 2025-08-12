"""
배치 로그 업데이트 시스템
=====================

Phase 2: Performance Optimization
UI 응답성 향상을 위한 배치 로그 업데이트 시스템입니다.

주요 기능:
- 로그 메시지 배치 처리로 UI 성능 최적화
- 적응형 배치 크기 (로그 양에 따라 자동 조절)
- 메모리 사용량 제어
- UI 블로킹 방지
"""

from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from typing import List, Callable, Optional
from datetime import datetime
import threading

class BatchedLogUpdater(QObject):
    """성능 최적화를 위한 배치 로그 업데이트

    Phase 2 성능 최적화 컴포넌트:
    - UI 스레드에서 안전한 배치 처리
    - 적응형 배치 크기 및 간격 조절
    - 메모리 사용량 모니터링 및 제어
    """

    # PyQt 시그널
    logs_ready = pyqtSignal(list)  # 배치 로그 준비 완료

    def __init__(self, update_callback: Optional[Callable[[List[str]], None]] = None, parent=None):
        """BatchedLogUpdater 초기화

        Args:
            update_callback: 로그 업데이트 콜백 함수
            parent: 부모 QObject
        """
        super().__init__(parent)

        # 콜백 설정
        self.update_callback = update_callback
        if update_callback:
            self.logs_ready.connect(lambda logs: update_callback(logs))

        # 배치 설정 (최적화됨)
        self._log_buffer: List[str] = []
        self._max_buffer_size = 100     # 더 큰 버퍼 (100개)
        self._min_buffer_size = 20      # 최소 크기 증가
        self._max_buffer_limit = 500    # 최대 크기 대폭 증가
        self._update_interval_ms = 100  # 업데이트 간격 단축 (100ms)

        # 성능 모니터링
        self._total_logs_processed = 0
        self._last_flush_time = datetime.now()
        self._adaptive_enabled = True

        # 타이머 설정
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._flush_buffer)
        self._update_timer.start(self._update_interval_ms)

        # 스레드 안전성
        self._lock = threading.RLock()

        print(f"✅ BatchedLogUpdater 초기화: 간격={self._update_interval_ms}ms, 버퍼={self._max_buffer_size}")

    def add_log_entry(self, log_entry: str) -> None:
        """로그 엔트리 추가

        Args:
            log_entry: 추가할 로그 메시지
        """
        with self._lock:
            self._log_buffer.append(log_entry)

            # 버퍼 가득 차면 즉시 플러시
            if len(self._log_buffer) >= self._max_buffer_size:
                self._flush_buffer()

    def add_multiple_log_entries(self, log_entries: List[str]) -> None:
        """여러 로그 엔트리 일괄 추가

        Args:
            log_entries: 추가할 로그 메시지 리스트
        """
        if not log_entries:
            return

        with self._lock:
            self._log_buffer.extend(log_entries)

            # 버퍼 크기 초과 시 즉시 플러시
            if len(self._log_buffer) >= self._max_buffer_size:
                self._flush_buffer()

    def flush_immediately(self) -> None:
        """즉시 버퍼 플러시 (강제)"""
        self._flush_buffer()

    def set_batch_size(self, size: int) -> None:
        """배치 크기 설정

        Args:
            size: 새 배치 크기
        """
        if self._min_buffer_size <= size <= self._max_buffer_limit:
            with self._lock:
                self._max_buffer_size = size
                print(f"🔧 배치 크기 변경: {size}")

    def set_update_interval(self, interval_ms: int) -> None:
        """업데이트 간격 설정

        Args:
            interval_ms: 새 업데이트 간격 (밀리초)
        """
        if 50 <= interval_ms <= 1000:  # 50ms ~ 1초 범위
            self._update_interval_ms = interval_ms
            self._update_timer.setInterval(interval_ms)
            print(f"🔧 업데이트 간격 변경: {interval_ms}ms")

    def enable_adaptive_batching(self, enabled: bool = True) -> None:
        """적응형 배치 처리 활성화/비활성화

        Args:
            enabled: 적응형 처리 활성화 여부
        """
        self._adaptive_enabled = enabled
        if enabled:
            print("🧠 적응형 배치 처리 활성화")
        else:
            print("🔒 고정 배치 처리 모드")

    def get_buffer_status(self) -> dict:
        """현재 버퍼 상태 조회

        Returns:
            dict: 버퍼 상태 정보
        """
        with self._lock:
            return {
                'buffer_size': len(self._log_buffer),
                'max_buffer_size': self._max_buffer_size,
                'total_processed': self._total_logs_processed,
                'update_interval': self._update_interval_ms,
                'adaptive_enabled': self._adaptive_enabled
            }

    def _flush_buffer(self) -> None:
        """버퍼 플러시 (내부 메서드)"""
        with self._lock:
            if not self._log_buffer:
                return

            # 로그 복사 및 버퍼 클리어
            logs_to_update = self._log_buffer.copy()
            self._log_buffer.clear()

            # 통계 업데이트
            self._total_logs_processed += len(logs_to_update)
            current_time = datetime.now()

            # 적응형 배치 크기 조절
            if self._adaptive_enabled:
                self._adjust_batch_size(len(logs_to_update), current_time)

            self._last_flush_time = current_time

        # 시그널 발생 (UI 스레드에서 처리됨)
        self.logs_ready.emit(logs_to_update)

    def _adjust_batch_size(self, flushed_count: int, current_time: datetime) -> None:
        """적응형 배치 크기 조절

        Args:
            flushed_count: 방금 플러시된 로그 수
            current_time: 현재 시간
        """
        time_diff = (current_time - self._last_flush_time).total_seconds()

        # 로그 유입 속도 계산
        if time_diff > 0:
            logs_per_second = flushed_count / time_diff

            # 높은 로그 유입 시 배치 크기 증가
            if logs_per_second > 50 and self._max_buffer_size < self._max_buffer_limit:
                self._max_buffer_size = min(self._max_buffer_size + 5, self._max_buffer_limit)

            # 낮은 로그 유입 시 배치 크기 감소
            elif logs_per_second < 10 and self._max_buffer_size > self._min_buffer_size:
                self._max_buffer_size = max(self._max_buffer_size - 2, self._min_buffer_size)

    def clear_buffer(self) -> None:
        """버퍼 클리어 (로그 손실)"""
        with self._lock:
            cleared_count = len(self._log_buffer)
            self._log_buffer.clear()
            if cleared_count > 0:
                print(f"🗑️ 버퍼 클리어: {cleared_count}개 로그 삭제")

    def pause_updates(self) -> None:
        """업데이트 일시 중지"""
        self._update_timer.stop()
        print("⏸️ 배치 업데이트 일시 중지")

    def resume_updates(self) -> None:
        """업데이트 재개"""
        self._update_timer.start(self._update_interval_ms)
        print("▶️ 배치 업데이트 재개")

    def get_performance_stats(self) -> dict:
        """성능 통계 조회

        Returns:
            dict: 성능 통계 정보
        """
        status = self.get_buffer_status()
        return {
            **status,
            'logs_per_minute': self._total_logs_processed / max(1,
                (datetime.now() - self._last_flush_time).total_seconds() / 60),
            'last_flush_time': self._last_flush_time.strftime('%H:%M:%S')
        }

    def __del__(self):
        """소멸자: 리소스 정리"""
        try:
            if hasattr(self, '_update_timer'):
                self._update_timer.stop()
            # 남은 로그 플러시
            if hasattr(self, '_log_buffer') and self._log_buffer:
                self.flush_immediately()
        except Exception:
            pass
