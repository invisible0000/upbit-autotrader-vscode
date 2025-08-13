"""
콘솔 뷰어 위젯

우측 하단에 위치하는 콘솔 출력 표시 영역입니다.
- 실시간 콘솔 출력 캡처
- 콘솔 내용 지우기
- stdout/stderr/system 출력 구분 및 필터링
"""

from datetime import datetime
import re
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QLineEdit, QComboBox
)
from PyQt6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor

from upbit_auto_trading.infrastructure.logging import create_component_logger


class ConsoleViewerWidget(QWidget):
    """콘솔 뷰어 위젯 - 우측 하단"""

    # 시그널 정의
    clear_console = pyqtSignal()  # 콘솔 지우기

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("console-viewer-widget")

        # 로깅
        self.logger = create_component_logger("ConsoleViewerWidget")
        self.logger.info("💻 콘솔 뷰어 위젯 초기화 시작")

        # 내부 상태
        self._max_lines = 1000  # 최대 콘솔 라인 수 (표시 기준) - 1000라인으로 증가
        self._current_lines = 0
        self._buffer_lines = []  # (message, type)
        self._text_filter = ""
        self._stream_filter = "all"  # all|error|warning|debug|info

        # 텍스트 포맷 설정
        self._setup_formats()

        # UI 구성 및 시그널
        self._setup_ui()
        self._connect_signals()

        self.logger.info("✅ 콘솔 뷰어 위젯 초기화 완료")

    def _setup_formats(self):
        """텍스트 포맷 설정"""
        # 일반 출력 (stdout) - 테마 기본 텍스트 색상 사용 (색상 미지정)
        self._stdout_format = QTextCharFormat()

        # 오류 출력 (stderr)
        self._stderr_format = QTextCharFormat()
        # 밝은/어두운 테마 모두에서 가독성 좋은 레드
        self._stderr_format.setForeground(QColor("#ff6b6b"))

        # 시스템 메시지
        self._system_format = QTextCharFormat()
        self._system_format.setForeground(QColor("#9aa0a6"))

        # 경량 하이라이트용 포맷
        self._tag_format = QTextCharFormat()  # [STDOUT]/[STDERR]/[SYSTEM]
        self._tag_format.setForeground(QColor("#10b981"))

        self._error_token_format = QTextCharFormat()  # ERROR
        self._error_token_format.setForeground(QColor("#ff6b6b"))

        self._warn_token_format = QTextCharFormat()  # WARN/WARNING
        self._warn_token_format.setForeground(QColor("#f59e0b"))

        self._info_token_format = QTextCharFormat()  # INFO
        self._info_token_format.setForeground(QColor("#4db6e5"))

        self._debug_token_format = QTextCharFormat()  # DEBUG
        self._debug_token_format.setForeground(QColor("#a78bfa"))

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 상단 컨트롤 패널
        control_layout = self._create_control_panel()
        layout.addLayout(control_layout)

        # 콘솔 표시 영역
        self.console_text_edit = QTextEdit()
        self.console_text_edit.setObjectName("console-text-display")
        self.console_text_edit.setReadOnly(True)
        self.console_text_edit.setFont(QFont("Consolas", 9))
        self.console_text_edit.setPlaceholderText("콘솔 출력이 여기에 표시됩니다...")

        # 스타일은 전역 QSS에서 관리 (개별 setStyleSheet 금지)
        layout.addWidget(self.console_text_edit)

        # 하단 상태 표시
        self.status_label = QLabel("콘솔 준비됨 - 0개 메시지")
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.status_label)

    def _create_control_panel(self) -> QHBoxLayout:
        """상단 컨트롤 패널 생성"""
        layout = QHBoxLayout()

        # 제목
        title_label = QLabel("💻 콘솔 뷰어")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)

        # 스페이서
        layout.addStretch()

        # 스트림 필터 콤보박스
        self.stream_filter_combo = QComboBox()
        self.stream_filter_combo.addItems(["전체", "ERROR", "WARNING", "DEBUG", "INFO"])
        self.stream_filter_combo.setToolTip("메시지 레벨 필터")
        layout.addWidget(self.stream_filter_combo)

        # 텍스트 필터
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("텍스트 필터... (대소문자 구분 없음)")
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.setFixedWidth(200)
        layout.addWidget(self.filter_edit)

        # 콘솔 지우기 버튼
        self.clear_button = QPushButton("지우기")
        self.clear_button.setObjectName("button-small")
        layout.addWidget(self.clear_button)

        return layout

    def _connect_signals(self):
        """시그널 연결"""
        self.clear_button.clicked.connect(self._on_clear_clicked)
        self.filter_edit.textChanged.connect(self._on_filter_text_changed)
        self.stream_filter_combo.currentTextChanged.connect(self._on_stream_filter_changed)

    # ===== 이벤트 핸들러 =====

    def _on_clear_clicked(self):
        """콘솔 지우기 버튼 클릭"""
        self.clear_console.emit()
        self._clear_console()
        # 로컬 버퍼도 동기화하여 초기화
        self._buffer_lines.clear()

    def _on_filter_text_changed(self, text: str):
        self._text_filter = text.strip()
        self._rebuild_display()

    def _on_stream_filter_changed(self, text: str):
        """스트림 필터 변경 핸들러"""
        mapping = {
            "전체": "all",
            "ERROR": "error",
            "WARNING": "warning",
            "DEBUG": "debug",
            "INFO": "info",
        }
        self._stream_filter = mapping.get(text, "all")
        self._rebuild_display()

    # ===== 공개 인터페이스 =====

    def append_console_output(self, output: str, is_error: bool = False):
        """콘솔 출력 추가 (MVP Presenter 인터페이스)"""
        lowered = output.lower()
        if "[system]" in lowered:
            message_type = "system"
        else:
            message_type = "stderr" if is_error else "stdout"
        self.append_console(output, message_type)

    def clear_console_viewer(self):
        """콘솔 뷰어 클리어 (MVP Presenter 인터페이스)"""
        self._clear_console()

    def append_console(self, message: str, message_type: str = "stdout"):
        """콘솔 메시지 추가"""
        if not message.strip():
            return

        # 버퍼에 먼저 적재 (최대 유지)
        self._buffer_lines.append((message, message_type))
        if len(self._buffer_lines) > self._max_lines:
            overflow = len(self._buffer_lines) - self._max_lines
            if overflow > 0:
                self._buffer_lines = self._buffer_lines[overflow:]

        # 타임스탬프가 없으면 추가
        if not message.startswith("["):
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = f"[{timestamp}] {message}"

        # 필터에 매칭되면 화면에 추가
        if self._should_display(message, message_type):
            self._append_line_to_view(message, message_type)
            self._current_lines += 1
            self._scroll_to_bottom()
            self._update_status()

    def append_stdout(self, message: str):
        self.append_console(message, "stdout")

    def append_stderr(self, message: str):
        self.append_console(message, "stderr")

    def append_system(self, message: str):
        self.append_console(message, "system")

    def _clear_console(self):
        """콘솔 내용 지우기"""
        self.console_text_edit.clear()
        self._current_lines = 0
        # 시스템 메시지 추가
        self.append_system("콘솔이 지워졌습니다.")
        self._update_status()

    # ===== 내부 유틸 =====

    def _append_line_to_view(self, message: str, message_type: str):
        # 기본 포맷 선택
        base_format = self._stdout_format
        if message_type == "stderr":
            base_format = self._stderr_format
        elif message_type == "system":
            base_format = self._system_format

        cursor = self.console_text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 경량 하이라이트 적용하여 삽입
        self._insert_with_highlights(cursor, message, base_format)
        cursor.insertText("\n")

    def _insert_with_highlights(self, cursor: QTextCursor, text: str, base_format: QTextCharFormat):
        """메시지 내 토큰을 간단히 하이라이트하며 삽입"""
        patterns = [
            (re.compile(r"\[STDERR\]", re.IGNORECASE), self._tag_format),
            (re.compile(r"\[STDOUT\]", re.IGNORECASE), self._tag_format),
            (re.compile(r"\[SYSTEM\]", re.IGNORECASE), self._tag_format),
            (re.compile(r"\bERROR\b", re.IGNORECASE), self._error_token_format),
            (re.compile(r"\bWARN(?:ING)?\b", re.IGNORECASE), self._warn_token_format),
            (re.compile(r"\bINFO\b", re.IGNORECASE), self._info_token_format),
            (re.compile(r"\bDEBUG\b", re.IGNORECASE), self._debug_token_format),
            (re.compile(r"[✅⚠️❌]"), self._warn_token_format),
        ]

        # 모든 매치 수집
        matches = []
        for regex, fmt in patterns:
            for m in regex.finditer(text):
                start, end = m.span()
                matches.append((start, end, fmt))
        # 시작 위치 기준 정렬 및 겹침 처리
        matches.sort(key=lambda x: x[0])

        pos = 0
        for start, end, fmt in matches:
            if end <= pos:
                continue  # 이미 지나간 또는 겹침 영역은 건너뛰기
            # 앞 부분 기본 포맷으로 삽입
            if start > pos:
                cursor.setCharFormat(base_format)
                cursor.insertText(text[pos:start])
            # 매치 부분 강조 포맷으로 삽입
            cursor.setCharFormat(fmt)
            cursor.insertText(text[start:end])
            pos = end

        # 남은 부분 삽입
        if pos < len(text):
            cursor.setCharFormat(base_format)
            cursor.insertText(text[pos:])

    def _should_display(self, message: str, message_type: str) -> bool:
        """메시지 표시 여부 결정"""
        # 레벨 필터 체크 (메시지 내용에서 레벨 추출)
        if self._stream_filter != "all":
            message_level = self._extract_log_level(message)
            if message_level != self._stream_filter:
                return False

        # 텍스트 필터 체크 (대소문자 무시)
        if self._text_filter:
            return self._text_filter.lower() in message.lower()
        return True

    def _extract_log_level(self, message: str) -> str:
        """메시지에서 로그 레벨 추출"""
        message_upper = message.upper()
        if "ERROR" in message_upper or "CRITICAL" in message_upper:
            return "error"
        elif "WARNING" in message_upper or "WARN" in message_upper:
            return "warning"
        elif "DEBUG" in message_upper:
            return "debug"
        elif "INFO" in message_upper:
            return "info"
        return "debug"  # 기본값은 debug

    def _rebuild_display(self):
        # 현재 뷰를 버퍼로부터 재구성
        self.console_text_edit.clear()
        self._current_lines = 0
        for message, mtype in self._buffer_lines:
            if self._should_display(message, mtype):
                self._append_line_to_view(message, mtype)
                self._current_lines += 1
        self._scroll_to_bottom()
        self._update_status()

    def _scroll_to_bottom(self):
        scrollbar = self.console_text_edit.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scrollbar.maximum())

    def _remove_old_lines(self):
        """오래된 콘솔 라인 제거 (최대 라인 수 유지)"""
        lines_to_remove = self._current_lines - self._max_lines + 50  # 50줄 여유
        if lines_to_remove <= 0:
            return
        cursor = self.console_text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(lines_to_remove):
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
        self._current_lines -= max(0, lines_to_remove)
        # 버퍼에서도 동일 수 만큼 제거 (앞쪽)
        if len(self._buffer_lines) > self._max_lines:
            overflow = len(self._buffer_lines) - self._max_lines
            if overflow > 0:
                self._buffer_lines = self._buffer_lines[overflow:]

    def _update_status(self):
        self.status_label.setText(f"콘솔 활성 - {self._current_lines:,}개 메시지")

    def get_console_content(self) -> str:
        return self.console_text_edit.toPlainText()

    def set_max_lines(self, max_lines: int):
        self._max_lines = max_lines

    def get_line_count(self) -> int:
        return self._current_lines

    def scroll_to_top(self):
        scrollbar = self.console_text_edit.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(0)

    def scroll_to_bottom(self):
        self._scroll_to_bottom()

    # set_theme는 전역 QSS 테마 시스템을 사용하므로 더 이상 필요하지 않습니다.
