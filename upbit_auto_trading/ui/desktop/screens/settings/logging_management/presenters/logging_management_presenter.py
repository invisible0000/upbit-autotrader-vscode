"""
로깅 관리 프레젠터 (DDD/MVP 패턴)

단순화된 버전:
- Infrastructure 로깅 시스템의 실시간 로그 파일 읽기만 담당
- 로그 저장/내보내기 기능 제거
- Config 파일 기반 설정 관리
"""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget
from pathlib import Path
from typing import Optional, Dict, Any

from upbit_auto_trading.infrastructure.logging.config.logging_config_manager import LoggingConfigManager
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.logging.terminal.terminal_capturer import (
    get_global_terminal_capturer,
    start_global_terminal_capture,
    stop_global_terminal_capture,
)


class LoggingManagementPresenter(QObject):
    """로깅 관리 프레젠터 (MVP 패턴) - 단순화 버전"""

    # 시그널 정의
    config_loaded = pyqtSignal(dict)
    config_saved = pyqtSignal()
    log_content_updated = pyqtSignal(str)
    console_output_updated = pyqtSignal(str, bool)  # (content, is_error)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

        # Infrastructure 로깅 시스템
        self.logger = create_component_logger("LoggingManagementPresenter")
        self.config_manager = LoggingConfigManager()

        # View 참조 (MVP 패턴)
        self.view = None

        # 실시간 로그 모니터링
        self.log_refresh_timer = QTimer()
        self.log_refresh_timer.timeout.connect(self._refresh_log_content)
        self.log_refresh_timer.setInterval(1000)  # 1초마다 갱신

        # 실시간 콘솔 모니터링
        self.console_refresh_timer = QTimer()
        self.console_refresh_timer.timeout.connect(self._refresh_console_output)
        self.console_refresh_timer.setInterval(500)  # 0.5초 간격

        # 콘솔 캡처러
        self._console_started = False
        self._last_console_len = 0  # 유지하되 사용하지 않음 (호환)
        self._last_console_anchor = None  # 마지막으로 보낸 마지막 라인 값

        # 로그 파일 상태 추적
        self._last_log_size = 0
        self._current_log_file = None

        self.logger.info("로깅 관리 프레젠터 초기화 완료")

    def set_view(self, view: QWidget) -> None:
        """View 설정 (MVP 패턴)"""
        self.view = view
        self.logger.debug(f"View 설정됨: {type(view).__name__}")

    def load_current_config(self) -> None:
        """현재 로깅 설정을 로드하여 View에 전달"""
        try:
            config = self.config_manager.get_current_config()
            self.logger.debug(f"로깅 설정 로드됨: {len(config)} 항목")
            self.config_loaded.emit(config)
        except Exception as e:
            self.logger.error(f"❌ 로깅 설정 로드 실패: {e}")
            self.config_loaded.emit({})

    def save_config(self, config: Dict[str, Any]) -> None:
        """로깅 설정을 Config 파일에 저장"""
        try:
            self.config_manager.update_logging_config(config, save_to_file=True)
            self.logger.info("✅ 로깅 설정 저장 완료")
            self.config_saved.emit()
        except Exception as e:
            self.logger.error(f"❌ 로깅 설정 저장 실패: {e}")

    def reset_to_defaults(self) -> None:
        """기본 설정으로 복원 (UI에서 확인 완료 후 호출됨)"""
        try:
            self.config_manager.reset_to_defaults(save_to_file=True)
            self.logger.info("✅ 기본 설정으로 복원 완료")
            self.load_current_config()  # UI에 새 설정 반영
        except Exception as e:
            self.logger.error(f"❌ 기본 설정 복원 실패: {e}")

    def start_real_time_monitoring(self) -> None:
        """실시간 로그 모니터링 시작"""
        try:
            self._update_current_log_file()
            if self._current_log_file and self._current_log_file.exists():
                self._last_log_size = self._current_log_file.stat().st_size
                self.log_refresh_timer.start()
                self.logger.info(f"📊 실시간 로그 모니터링 시작: {self._current_log_file}")
            else:
                self.logger.warning("⚠️  활성 로그 파일을 찾을 수 없음")

            # 콘솔 캡처 시작 및 폴링
            if not self._console_started:
                start_global_terminal_capture()
                self._console_started = True
                self.logger.info("💻 콘솔 캡처 시작")
            self.console_refresh_timer.start()
        except Exception as e:
            self.logger.error(f"❌ 실시간 모니터링 시작 실패: {e}")

    def stop_real_time_monitoring(self) -> None:
        """실시간 로그 모니터링 중지"""
        if self.log_refresh_timer.isActive():
            self.log_refresh_timer.stop()
            self.logger.info("📊 실시간 로그 모니터링 중지")
        if self.console_refresh_timer.isActive():
            self.console_refresh_timer.stop()
            self.logger.info("💻 콘솔 모니터링 중지")
        if self._console_started:
            stop_global_terminal_capture()
            self._console_started = False
        self._last_console_len = 0

    def _update_current_log_file(self) -> None:
        """현재 활성 로그 파일 경로 업데이트"""
        try:
            logs_dir = Path("logs")
            if not logs_dir.exists():
                return

            log_files = list(logs_dir.glob("*.log"))
            if log_files:
                self._current_log_file = max(log_files, key=lambda f: f.stat().st_mtime)
                self.logger.debug(f"현재 로그 파일: {self._current_log_file}")
        except Exception as e:
            self.logger.error(f"❌ 로그 파일 경로 업데이트 실패: {e}")

    def _refresh_log_content(self) -> None:
        """로그 내용 새로고침 (실시간 모니터링)"""
        try:
            if not self._current_log_file or not self._current_log_file.exists():
                return

            current_size = self._current_log_file.stat().st_size
            if current_size <= self._last_log_size:
                return

            with open(self._current_log_file, 'r', encoding='utf-8') as f:
                f.seek(self._last_log_size)
                new_content = f.read()

            if new_content.strip():
                self.log_content_updated.emit(new_content)
                self._last_log_size = current_size
        except Exception as e:
            self.logger.error(f"❌ 로그 내용 새로고침 실패: {e}")

    def get_full_log_content(self) -> str:
        """전체 로그 내용 가져오기"""
        try:
            if not self._current_log_file or not self._current_log_file.exists():
                return "로그 파일을 찾을 수 없습니다."

            with open(self._current_log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            self.logger.debug(f"전체 로그 내용 로드: {len(content)} 문자")
            return content
        except Exception as e:
            self.logger.error(f"❌ 전체 로그 내용 로드 실패: {e}")
            return f"로그 읽기 오류: {str(e)}"

    def refresh_log_viewer(self) -> None:
        """로그 뷰어 수동 새로고침"""
        try:
            self._update_current_log_file()
            full_content = self.get_full_log_content()
            self.log_content_updated.emit(full_content)
            self.logger.debug("로그 뷰어 수동 새로고침 완료")
        except Exception as e:
            self.logger.error(f"❌ 로그 뷰어 새로고침 실패: {e}")

    def cleanup(self) -> None:
        """리소스 정리"""
        self.stop_real_time_monitoring()
        self.logger.info("로깅 관리 프레젠터 리소스 정리 완료")

    # ===== 내부: 콘솔 폴링 =====

    def _refresh_console_output(self) -> None:
        try:
            capturer = get_global_terminal_capturer()
            # 최근 라인을 넉넉히 읽어와 앵커 검색 (버퍼 밀림에도 견고)
            recent = capturer.get_recent_output(lines=200)
            if not recent:
                return

            # 앵커(마지막으로 전송한 마지막 라인)를 기준으로 새 라인만 추출
            new_lines = []
            if self._last_console_anchor is None:
                new_lines = recent
            else:
                try:
                    idx = recent.index(self._last_console_anchor)
                    new_lines = recent[idx + 1:]
                except ValueError:
                    # 앵커가 최근 윈도우에서 밀려난 경우, 최근 라인 전체를 전송
                    new_lines = recent

            for line in new_lines:
                # stderr 여부는 태그로 판정
                lowered = line.lower()
                is_error = "[stderr]" in lowered
                self.console_output_updated.emit(line, is_error)
            if recent:
                self._last_console_anchor = recent[-1]
            self._last_console_len = len(recent)
        except Exception as e:
            self.logger.error(f"❌ 콘솔 출력 갱신 실패: {e}")

    # 외부 호출: 콘솔 버퍼 초기화
    def clear_console_buffer(self) -> None:
        try:
            capturer = get_global_terminal_capturer()
            capturer.clear_buffer()
            self._last_console_len = 0
            self._last_console_anchor = None
        except Exception as e:
            self.logger.error(f"❌ 콘솔 버퍼 초기화 실패: {e}")
