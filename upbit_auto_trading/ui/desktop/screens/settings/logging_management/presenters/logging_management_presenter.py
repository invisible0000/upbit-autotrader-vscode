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

# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정), get_logging_service
# Application Layer - Infrastructure 의존성 격리 (Phase 3 수정) # (
    get_global_terminal_capturer,
    start_global_terminal_capture,
    stop_global_terminal_capture,
)
# Application Layer - Infrastructure 의존성 격리 (Phase 3 수정) # (
    get_live_log_buffer,
    attach_live_log_handler,
    detach_live_log_handler,
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

        # ✅ LoggingService의 config_manager 사용 (중요!)
        logging_service = get_logging_service()
        self.config_manager = logging_service._config_manager

        self.logger.info(f"✅ LoggingService의 config_manager 사용 - 핸들러 수: {len(self.config_manager._change_handlers)}")

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

        # 라이브 로그 버퍼 시퀀스 추적 (인메모리 구독)
        self._live_last_seq = 0

        # 중복 로딩 방지 플래그
        self._monitoring_started = False

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
        if self._monitoring_started:
            self.logger.debug("실시간 모니터링이 이미 시작됨 - 중복 호출 방지")
            return

        try:
            self._update_current_log_file()
            if self._current_log_file and self._current_log_file.exists():
                self._last_log_size = self._current_log_file.stat().st_size
                # 1) 초기 하이드레이트: 현재 세션 시작점부터만 로드 (없으면 최근 N줄)
                self._hydrate_since_session_start_or_recent(lines=200)
                # 2) 실시간은 인메모리 버퍼를 폴링 (파일 폴링은 보조로 유지하거나 비활성화)
                self.log_refresh_timer.start()
                self.logger.info(f"📊 하이브리드 로그 모니터링 시작: 파일={self._current_log_file}")
            else:
                self.logger.warning("⚠️  활성 로그 파일을 찾을 수 없음")

            # 콘솔 캡처 시작 및 폴링
            if not self._console_started:
                start_global_terminal_capture()
                self._console_started = True
                self.logger.info("💻 콘솔 캡처 시작")
            self.console_refresh_timer.start()

            # 라이브 로그 핸들러 연결 및 시퀀스 초기화
            attach_live_log_handler()
            self._live_last_seq = get_live_log_buffer().last_seq()

            self._monitoring_started = True
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
        # 라이브 로그 핸들러 해제
        detach_live_log_handler()
        self._monitoring_started = False

    def _update_current_log_file(self) -> None:
        """현재 활성 로그 파일 경로 업데이트"""
        try:
            logs_dir = Path("logs")
            if not logs_dir.exists():
                return

            # 우선순위 1: 세션 로그 파일 패턴 session_YYYY-MM-DD_HH-MM-SS_PIDxxxx.log 중 최신
            session_logs = list(logs_dir.glob("session_*.log"))
            if session_logs:
                self._current_log_file = max(session_logs, key=lambda f: f.stat().st_mtime)
                self.logger.debug(f"현재 세션 로그 파일 선택: {self._current_log_file}")
                return

            # 우선순위 2: 일반 *.log 중 최신
            log_files = list(logs_dir.glob("*.log"))
            if log_files:
                self._current_log_file = max(log_files, key=lambda f: f.stat().st_mtime)
                self.logger.debug(f"현재 로그 파일(폴백) 선택: {self._current_log_file}")
        except Exception as e:
            self.logger.error(f"❌ 로그 파일 경로 업데이트 실패: {e}")

    def _refresh_log_content(self) -> None:
        """로그 내용 새로고침 (실시간 모니터링)"""
        try:
            # 1) 우선 인메모리 라이브 버퍼에서 신규 라인 드레인
            buf = get_live_log_buffer()
            lines, max_seq = buf.get_since(self._live_last_seq)
            if lines:
                self.log_content_updated.emit("\n".join(lines) + "\n")
                self._live_last_seq = max_seq
                return

            # 2) 보조: 파일 사이즈 증가분 tail (로테이션/외부 프로세스 대비)
            if self._current_log_file and self._current_log_file.exists():
                current_size = self._current_log_file.stat().st_size
                if current_size > self._last_log_size:
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
            # 파일 경로 최신화 시도 후 없으면 빈 문자열 반환 (뷰에서 환영 메시지 처리)
            if not self._current_log_file or not self._current_log_file.exists():
                self._update_current_log_file()
            if not self._current_log_file or not self._current_log_file.exists():
                return ""

            # 현재 세션 시작점부터만 반환 (없으면 전체가 아니라 최근 N줄)
            content = self._read_since_last_session_start(self._current_log_file)
            if content is None:
                content = self._read_recent_lines_text(self._current_log_file, lines=200)
            self.logger.debug(f"세션 기준 로그 내용 로드: {len(content)} 문자")
            return content or ""
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

    # ===== 내부: 파일 하이드레이트 =====
    def _hydrate_since_session_start_or_recent(self, lines: int = 200) -> None:
        """현재 세션 시작점부터 하이드레이트. 없으면 최근 N줄을 공급."""
        try:
            if not self._current_log_file or not self._current_log_file.exists():
                return
            # 세션 시작점 탐색
            session_text = self._read_since_last_session_start(self._current_log_file)
            if session_text:
                self.log_content_updated.emit(session_text if session_text.endswith("\n") else session_text + "\n")
                return

            # 폴백: 최근 N줄
            recent_text = self._read_recent_lines_text(self._current_log_file, lines=lines)
            if recent_text:
                self.log_content_updated.emit(recent_text if recent_text.endswith("\n") else recent_text + "\n")
        except Exception as e:
            self.logger.error(f"❌ 초기 로그 하이드레이트 실패: {e}")

    # ===== 내부: 파일 읽기 유틸 =====
    def _read_since_last_session_start(self, path: Path, max_bytes: int = 2 * 1024 * 1024) -> Optional[str]:
        """파일의 마지막 'SESSION START' 마커 이후 텍스트를 반환. 없으면 None.

        성능: 파일 끝에서 최대 max_bytes만 읽어서 검색.
        """
        try:
            size = path.stat().st_size
            with open(path, 'rb') as f:
                if size > max_bytes:
                    f.seek(size - max_bytes)
                data = f.read()
            text = data.decode('utf-8', errors='replace')
            idx = text.rfind('SESSION START')
            if idx != -1:
                return text[idx:]
            return None
        except Exception as e:
            self.logger.error(f"세션 시작 마커 검색 실패: {e}")
            return None

    def _read_recent_lines_text(self, path: Path, lines: int = 200) -> str:
        """파일 끝에서부터 최근 N줄을 읽어 텍스트로 반환."""
        try:
            with open(path, 'rb') as f:
                f.seek(0, 2)  # EOF
                size = f.tell()
                block = 4096
                data = b''
                pos = size
                want = lines
                while pos > 0 and want > 0:
                    read = block if pos >= block else pos
                    pos -= read
                    f.seek(pos)
                    data = f.read(read) + data
                    want = lines - data.count(b'\n')
                text = data.decode('utf-8', errors='replace')
            last_lines = text.splitlines()[-lines:]
            return "\n".join(last_lines)
        except Exception as e:
            self.logger.error(f"최근 라인 읽기 실패: {e}")
            return ""

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
