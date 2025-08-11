"""
Real-time Log Viewer Widget
===========================

실시간 로그 표시 위젯
Infrastructure Layer 로깅 시스템과 연동하여 실시간 로그 표시

Features:
- 실시간 로그 스트림 표시
- 로그 레벨별 색상 구분
- 자동 스크롤 및 수동 스크롤 지원
- 로그 필터링 (레벨별, 컴포넌트별)
- 로그 클리어 및 저장 기능
"""

import logging
import weakref
import os
import re
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QCheckBox, QLabel, QFrame
)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt, QFileSystemWatcher
from PyQt6.QtGui import QTextCursor, QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger


class LogEntry:
    """로그 엔트리 데이터 클래스"""
    def __init__(self, level: str, component: str, message: str, timestamp: str):
        self.level = level
        self.component = component
        self.message = message
        self.timestamp = timestamp


class LogViewerWidget(QWidget):
    """
    실시간 로그 뷰어 위젯

    Infrastructure 로깅 시스템의 출력을 실시간으로 표시
    Thread-Safe 설계로 안정성 보장
    """

    # Thread-Safe 시그널 정의
    log_entry_received = pyqtSignal(object)  # LogEntry 객체 전송

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("LogViewerWidget")

        # Infrastructure 로깅 초기화
        self._logger = create_component_logger("LogViewerWidget")

        # 로그 필터 상태
        self._show_debug = True
        self._show_info = True
        self._show_warning = True
        self._show_error = True
        self._component_filter = ""
        self._auto_scroll = True
        self._max_lines = 1000  # 최대 라인 수

        # Thread-Safe 로그 핸들러
        self._log_handler = None

        # 파일 기반 로그 읽기 (추가)
        self._file_watcher = None
        self._current_log_file = None
        self._last_read_position = 0
        self._file_update_timer = None

        # 모니터링 상태 관리
        self._is_monitoring = False
        self._monitoring_started = False

        self._setup_ui()
        self._connect_signals()

        # 로그 소스는 탭 활성화 시에만 설정
        self._logger.info("🔗 로그 뷰어 초기화 완료 (지연 로딩 모드)")

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 제목
        title_label = QLabel("📺 실시간 로그")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 필터 컨트롤
        self._create_filter_controls(layout)

        # 로그 표시 영역
        self._create_log_display(layout)

        # 액션 버튼
        self._create_action_buttons(layout)

    def _create_filter_controls(self, parent_layout: QVBoxLayout):
        """필터 컨트롤 생성"""
        filter_frame = QFrame()
        filter_frame.setObjectName("log-filter-frame")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(4, 4, 4, 4)
        filter_layout.setSpacing(8)

        # 레벨 필터 체크박스
        self.debug_check = QCheckBox("DEBUG")
        self.debug_check.setChecked(self._show_debug)
        self.debug_check.setStyleSheet("color: #666;")

        self.info_check = QCheckBox("INFO")
        self.info_check.setChecked(self._show_info)
        self.info_check.setStyleSheet("color: #2196F3;")

        self.warning_check = QCheckBox("WARNING")
        self.warning_check.setChecked(self._show_warning)
        self.warning_check.setStyleSheet("color: #FF9800;")

        self.error_check = QCheckBox("ERROR")
        self.error_check.setChecked(self._show_error)
        self.error_check.setStyleSheet("color: #F44336;")

        filter_layout.addWidget(QLabel("레벨:"))
        filter_layout.addWidget(self.debug_check)
        filter_layout.addWidget(self.info_check)
        filter_layout.addWidget(self.warning_check)
        filter_layout.addWidget(self.error_check)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        filter_layout.addWidget(line)

        # 자동 스크롤
        self.auto_scroll_check = QCheckBox("자동 스크롤")
        self.auto_scroll_check.setChecked(self._auto_scroll)
        filter_layout.addWidget(self.auto_scroll_check)

        filter_layout.addStretch()

        parent_layout.addWidget(filter_frame)

    def _create_log_display(self, parent_layout: QVBoxLayout):
        """로그 표시 영역"""
        self.log_text = QTextEdit()
        self.log_text.setObjectName("log-display")
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        self.log_text.setMaximumHeight(300)

        # 폰트 설정 (모노스페이스)
        font = QFont("Consolas", 9)
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.log_text.setFont(font)

        # 스타일 설정
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 8px;
            }
        """)

        parent_layout.addWidget(self.log_text)

    def _create_action_buttons(self, parent_layout: QVBoxLayout):
        """액션 버튼들"""
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 4, 0, 0)

        # 클리어 버튼
        self.clear_btn = QPushButton("🗑️ 클리어")
        self.clear_btn.setObjectName("secondary-button")
        self.clear_btn.setMaximumWidth(80)

        # 저장 버튼
        self.save_btn = QPushButton("💾 저장")
        self.save_btn.setObjectName("secondary-button")
        self.save_btn.setMaximumWidth(80)

        # 테스트 로그 버튼 (개발용)
        self.test_log_btn = QPushButton("🧪 테스트")
        self.test_log_btn.setObjectName("accent-button")
        self.test_log_btn.setMaximumWidth(80)
        self.test_log_btn.setToolTip("테스트용 로그를 추가합니다")

        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.test_log_btn)
        button_layout.addStretch()

        parent_layout.addWidget(button_frame)

    def _connect_signals(self):
        """시그널 연결"""
        # Thread-Safe 로그 엔트리 처리
        self.log_entry_received.connect(self._handle_log_entry)

        # 필터 변경
        self.debug_check.toggled.connect(lambda checked: setattr(self, '_show_debug', checked))
        self.info_check.toggled.connect(lambda checked: setattr(self, '_show_info', checked))
        self.warning_check.toggled.connect(lambda checked: setattr(self, '_show_warning', checked))
        self.error_check.toggled.connect(lambda checked: setattr(self, '_show_error', checked))

        # 자동 스크롤
        self.auto_scroll_check.toggled.connect(lambda checked: setattr(self, '_auto_scroll', checked))

        # 액션 버튼
        self.clear_btn.clicked.connect(self._clear_logs)
        self.save_btn.clicked.connect(self._save_logs)
        self.test_log_btn.clicked.connect(self.add_test_log)

    def _handle_log_entry(self, log_entry: LogEntry):
        """Thread-Safe 로그 엔트리 처리 (UI 스레드에서 실행)"""
        self.add_log_entry(log_entry.level, log_entry.component, log_entry.message)

    def _setup_log_sources(self):
        """로그 소스 설정 - Infrastructure 핸들러 + 파일 읽기"""
        try:
            # 1. Infrastructure 핸들러 연결 (기존 방식)
            self._setup_infrastructure_handler()

            # 2. 파일 기반 로그 읽기 (새로운 방식)
            self._setup_file_watcher()

        except Exception as e:
            self._logger.error(f"❌ 로그 소스 설정 실패: {e}")

    def _setup_infrastructure_handler(self):
        """Infrastructure 핸들러 설정 (기존 방식)"""
        try:
            # Thread-Safe 핸들러 생성 (Weak Reference 사용)
            self._log_handler = ThreadSafeLogViewerHandler(self)
            self._log_handler.setLevel(logging.DEBUG)

            # Infrastructure 로깅에 연결 - 모든 upbit.* 로거를 캐치
            upbit_logger = logging.getLogger('upbit')
            upbit_logger.addHandler(self._log_handler)

            # 전파 활성화로 변경하여 하위 로거들의 로그도 캐치
            upbit_logger.propagate = True

            # 루트 로거에도 추가하여 다른 로거들도 캐치 (선택적)
            root_logger = logging.getLogger()
            if self._log_handler not in root_logger.handlers:
                root_logger.addHandler(self._log_handler)

            self._logger.info("🔗 Infrastructure 핸들러 연결 완료")

        except Exception as e:
            self._logger.error(f"❌ Infrastructure 핸들러 설정 실패: {e}")

    def _setup_file_watcher(self):
        """파일 기반 로그 읽기 설정"""
        try:
            # 현재 세션 로그 파일 찾기
            self._current_log_file = self._find_current_session_log()

            if self._current_log_file and os.path.exists(self._current_log_file):
                self._logger.info(f"📁 세션 로그 파일 발견: {self._current_log_file}")

                # 파일 시스템 와처 설정
                self._file_watcher = QFileSystemWatcher()
                self._file_watcher.addPath(self._current_log_file)
                self._file_watcher.fileChanged.connect(self._on_log_file_changed)

                # 타이머로 주기적 체크 (파일 시스템 와처 백업)
                self._file_update_timer = QTimer()
                self._file_update_timer.timeout.connect(self._read_new_log_entries)
                self._file_update_timer.start(1000)  # 1초마다 체크

                # 기존 로그 내용 로드
                self._read_existing_log_content()

                self._logger.info("🔗 파일 기반 로그 읽기 설정 완료")
            else:
                self._logger.warning("⚠️ 세션 로그 파일을 찾을 수 없음")

        except Exception as e:
            self._logger.error(f"❌ 파일 와처 설정 실패: {e}")

    def _find_current_session_log(self) -> Optional[str]:
        """현재 세션 로그 파일 찾기"""
        try:
            logs_dir = Path("logs")
            if not logs_dir.exists():
                return None

            # session_YYYYMMDD_HHMMSS_PID*.log 패턴으로 찾기
            session_files = list(logs_dir.glob("session_*_PID*.log"))

            if session_files:
                # 가장 최신 파일 반환 (수정 시간 기준)
                latest_file = max(session_files, key=lambda f: f.stat().st_mtime)
                return str(latest_file)

        except Exception as e:
            self._logger.error(f"❌ 세션 로그 파일 찾기 실패: {e}")

        return None

    def _on_log_file_changed(self, path: str):
        """파일 변경 이벤트 처리"""
        self._read_new_log_entries()

    def _read_existing_log_content(self):
        """기존 로그 내용 읽기 (초기 로드)"""
        try:
            if not self._current_log_file or not os.path.exists(self._current_log_file):
                return

            with open(self._current_log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()

                # 헤더 스킵 (SESSION START 부분)
                log_lines = [line for line in lines if ' - upbit.' in line]

                # 최근 50줄만 표시 (초기 로드)
                recent_lines = log_lines[-50:] if len(log_lines) > 50 else log_lines

                for line in recent_lines:
                    self._parse_and_add_log_line(line)

                # 현재 읽은 위치 저장
                self._last_read_position = len(content)

                self._logger.info(f"📖 기존 로그 {len(recent_lines)}줄 로드 완료")

        except Exception as e:
            self._logger.error(f"❌ 기존 로그 읽기 실패: {e}")

    def _read_new_log_entries(self):
        """새로운 로그 엔트리 읽기"""
        try:
            if not self._current_log_file or not os.path.exists(self._current_log_file):
                return

            with open(self._current_log_file, 'r', encoding='utf-8') as f:
                # 마지막 읽은 위치부터 읽기
                f.seek(self._last_read_position)
                new_content = f.read()

                if new_content.strip():
                    lines = new_content.splitlines()

                    for line in lines:
                        if ' - upbit.' in line:  # Infrastructure 로그만 필터링
                            self._parse_and_add_log_line(line)

                    # 읽은 위치 업데이트
                    self._last_read_position = f.tell()

        except Exception as e:
            # 파일 읽기 에러는 조용히 무시 (파일이 쓰여지는 중일 수 있음)
            pass

    def _parse_and_add_log_line(self, line: str):
        """로그 라인 파싱 후 추가"""
        try:
            # 로그 라인 형식: "2025-08-10 17:41:00 - upbit.ComponentName - LEVEL - message"
            import re

            pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - upbit\.([^-]+) - (\w+) - (.+)'
            match = re.match(pattern, line.strip())

            if match:
                timestamp, component, level, message = match.groups()

                # Infrastructure 로깅 형식과 동일하게 처리
                self.add_log_entry(level.strip(), component.strip(), message.strip())

        except Exception as e:
            # 파싱 에러는 무시하고 원본 라인 표시
            self.add_log_entry("INFO", "FileReader", line.strip())

    def _setup_log_handler(self):
        """Thread-Safe 로그 핸들러 설정 (DEPRECATED - _setup_log_sources로 통합)"""
        pass

    def _update_logs(self):
        """제거됨 - Timer 기반 폴링 대신 Event-driven 방식 사용"""
        pass

    def add_test_log(self):
        """테스트용 로그 추가 (개발/디버깅용)"""
        from datetime import datetime
        import random

        test_messages = [
            ("INFO", "TradingEngine", "🚀 거래 엔진 시작됨"),
            ("DEBUG", "MarketData", "📊 시장 데이터 업데이트"),
            ("WARNING", "APIClient", "⚠️ API 요청 지연"),
            ("ERROR", "DatabaseService", "❌ 데이터베이스 연결 실패"),
            ("INFO", "UserInterface", "✅ UI 초기화 완료")
        ]

        level, component, message = random.choice(test_messages)
        self.add_log_entry(level, component, message)
        self._logger.debug(f"테스트 로그 추가: {level} - {message}")

    def add_log_entry(self, level: str, component: str, message: str):
        """로그 엔트리 추가"""
        # 필터 검사
        if not self._should_show_log(level):
            return

        # 색상 결정
        color = self._get_level_color(level)

        # 타임스탬프 추가
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 포맷팅
        formatted_entry = f"[{timestamp}] [{level:>7}] [{component:>15}] {message}"

        # 텍스트 추가
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 색상 적용
        cursor.insertHtml(f'<span style="color: {color};">{formatted_entry}</span><br>')

        # 자동 스크롤
        if self._auto_scroll:
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )

        # 최대 라인 수 제한
        self._limit_lines()

    def _should_show_log(self, level: str) -> bool:
        """로그 표시 여부 결정"""
        level_map = {
            'DEBUG': self._show_debug,
            'INFO': self._show_info,
            'WARNING': self._show_warning,
            'ERROR': self._show_error,
            'CRITICAL': self._show_error
        }
        return level_map.get(level, True)

    def _get_level_color(self, level: str) -> str:
        """로그 레벨별 색상 반환"""
        colors = {
            'DEBUG': '#666666',
            'INFO': '#2196F3',
            'WARNING': '#FF9800',
            'ERROR': '#F44336',
            'CRITICAL': '#D32F2F'
        }
        return colors.get(level, '#d4d4d4')

    def _limit_lines(self):
        """최대 라인 수 제한"""
        if self.log_text.document().lineCount() > self._max_lines:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down,
                               QTextCursor.MoveMode.KeepAnchor, 100)
            cursor.removeSelectedText()

    def _clear_logs(self):
        """로그 클리어"""
        self.log_text.clear()
        self._logger.info("📺 로그 뷰어 클리어됨")

    def _save_logs(self):
        """로그 저장 (미구현)"""
        self._logger.info("💾 로그 저장 기능 준비중")

    def cleanup(self):
        """리소스 정리 (위젯 삭제 시 호출)"""
        try:
            # Infrastructure 핸들러 정리
            if self._log_handler:
                # 로거에서 핸들러 제거
                upbit_logger = logging.getLogger('upbit')
                if self._log_handler in upbit_logger.handlers:
                    upbit_logger.removeHandler(self._log_handler)

                # 루트 로거에서도 제거
                root_logger = logging.getLogger()
                if self._log_handler in root_logger.handlers:
                    root_logger.removeHandler(self._log_handler)

                # 핸들러 정리
                self._log_handler.close()
                self._log_handler = None

            # 파일 와처 정리
            if self._file_watcher:
                self._file_watcher.fileChanged.disconnect()
                if self._current_log_file:
                    self._file_watcher.removePath(self._current_log_file)
                self._file_watcher = None

            # 타이머 정리
            if self._file_update_timer:
                self._file_update_timer.stop()
                self._file_update_timer.timeout.disconnect()
                self._file_update_timer = None

            self._logger.info("🧹 로그 뷰어 리소스 정리 완료")

        except Exception as e:
            self._logger.error(f"❌ 리소스 정리 실패: {e}")

    def closeEvent(self, a0):
        """위젯 종료 시 리소스 정리"""
        self.cleanup()
        super().closeEvent(a0)

    # === 탭 활성화 기반 모니터링 제어 ===

    def start_monitoring(self):
        """로그 모니터링 시작 (탭 활성화 시 호출)"""
        if not self._is_monitoring:
            self._logger.info("🔍 로그 뷰어 모니터링 시작...")

            try:
                # 로그 소스 연결
                self._setup_log_sources()

                # 상태 업데이트
                self._is_monitoring = True
                self._monitoring_started = True

                # 사용자에게 상태 표시
                self.add_log_entry("INFO", "LogViewer", "📡 실시간 로그 모니터링 시작됨")

                self._logger.info("✅ 로그 뷰어 모니터링 시작 완료")

            except Exception as e:
                self._logger.error(f"❌ 로그 모니터링 시작 실패: {e}")
                self.add_log_entry("ERROR", "LogViewer", f"모니터링 시작 실패: {e}")

    def stop_monitoring(self):
        """로그 모니터링 중지 (탭 비활성화 시 호출)"""
        if self._is_monitoring:
            self._logger.info("🛑 로그 뷰어 모니터링 중지...")

            try:
                # 리소스 정리
                self._cleanup_log_sources()

                # 상태 업데이트
                self._is_monitoring = False

                # 사용자에게 상태 표시
                self.add_log_entry("INFO", "LogViewer", "📴 실시간 로그 모니터링 중지됨")

                self._logger.info("✅ 로그 뷰어 모니터링 중지 완료")

            except Exception as e:
                self._logger.error(f"❌ 로그 모니터링 중지 실패: {e}")

    def _cleanup_log_sources(self):
        """로그 소스 정리 (내부 메서드)"""
        try:
            # Infrastructure 핸들러 정리
            if self._log_handler:
                upbit_logger = logging.getLogger('upbit')
                if self._log_handler in upbit_logger.handlers:
                    upbit_logger.removeHandler(self._log_handler)

                root_logger = logging.getLogger()
                if self._log_handler in root_logger.handlers:
                    root_logger.removeHandler(self._log_handler)

                self._log_handler.close()
                self._log_handler = None

            # 파일 와처 정리
            if self._file_watcher:
                self._file_watcher.fileChanged.disconnect()
                if self._current_log_file:
                    self._file_watcher.removePath(self._current_log_file)
                self._file_watcher = None

            # 타이머 정리
            if self._file_update_timer:
                self._file_update_timer.stop()
                self._file_update_timer.timeout.disconnect()
                self._file_update_timer = None

        except Exception as e:
            self._logger.error(f"❌ 로그 소스 정리 실패: {e}")

    def is_monitoring(self) -> bool:
        """모니터링 상태 반환"""
        return self._is_monitoring


class ThreadSafeLogViewerHandler(logging.Handler):
    """
    Thread-Safe 로그 뷰어 핸들러

    Weak Reference와 시그널-슬롯을 사용하여 Thread Safety 보장
    """

    def __init__(self, log_viewer: LogViewerWidget):
        super().__init__()
        # Weak Reference로 순환 참조 방지
        self._log_viewer_ref = weakref.ref(log_viewer)

    def emit(self, record):
        """Thread-Safe 로그 레코드 처리"""
        try:
            # Weak Reference 확인
            log_viewer = self._log_viewer_ref()
            if log_viewer is None:
                return  # 위젯이 삭제됨

            # 컴포넌트 이름 추출
            if hasattr(record, 'name') and record.name.startswith('upbit.'):
                component = record.name.replace('upbit.', '')
            else:
                component = record.name

            # 메시지 포맷팅
            message = record.getMessage()

            # 예외 정보가 있다면 추가
            if record.exc_info:
                import traceback
                message += '\n' + ''.join(traceback.format_exception(*record.exc_info))

            # 타임스탬프 생성
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 밀리초 포함

            # LogEntry 객체 생성
            log_entry = LogEntry(
                level=record.levelname,
                component=component,
                message=message,
                timestamp=timestamp
            )

            # Thread-Safe 시그널 발송 (Qt가 자동으로 UI 스레드로 전달)
            log_viewer.log_entry_received.emit(log_entry)

        except Exception:
            # 로깅 에러는 무시 (무한 루프 방지)
            pass


class LogViewerHandler(logging.Handler):
    """
    DEPRECATED: 기존 핸들러 (호환성 유지)
    ThreadSafeLogViewerHandler를 사용하세요
    """

    def __init__(self, log_viewer: LogViewerWidget):
        super().__init__()
        self.log_viewer = log_viewer

    def emit(self, record):
        """로그 레코드 처리"""
        try:
            # 컴포넌트 이름 추출 (더 정확하게)
            if hasattr(record, 'name') and record.name.startswith('upbit.'):
                component = record.name.replace('upbit.', '')
            else:
                component = record.name

            # 메시지 포맷팅
            message = record.getMessage()

            # 예외 정보가 있다면 추가
            if record.exc_info:
                import traceback
                message += '\n' + ''.join(traceback.format_exception(*record.exc_info))

            # 로그 뷰어에 직접 추가 (UI 스레드에서 호출됨)
            self.log_viewer.add_log_entry(
                record.levelname,
                component,
                message
            )

        except Exception:
            # 로깅 에러는 무시 (무한 루프 방지)
            pass
