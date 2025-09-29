"""
로그 뷰어 위젯

우측 상단에 위치하는 로그 메시지 표시 영역입니다.
- 실시간 로그 메시지 표시
- 자동 스크롤 기능
- 로그 구문 강조 (하이라이트)
- 폰트 크기 조절
- 로그 내용 복사
"""

from datetime import datetime
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QCheckBox, QLabel, QSpinBox, QLineEdit, QComboBox
)
from PyQt6.QtGui import QFont, QTextCursor, QTextDocument

# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)
from .log_syntax_highlighter import LogSyntaxHighlighter


class LogViewerWidget(QWidget):
    """로그 뷰어 위젯 - 우측 상단"""

    # 시그널 정의
    clear_logs = pyqtSignal()                   # 로그 지우기
    save_logs = pyqtSignal()                    # 로그 저장
    auto_scroll_changed = pyqtSignal(bool)      # 자동 스크롤 토글

    def __init__(self, parent=None, logging_service=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("log-viewer-widget")
        # 로깅
        if logging_service:
            self.logger = logging_service.get_component_logger("LogViewerWidget")
        else:
            raise ValueError("LogViewerWidget에 logging_service가 주입되지 않았습니다")
        self.logger.info("📄 로그 뷰어 위젯 초기화 시작")

        # 내부 상태
        self._auto_scroll = True
        self._max_lines = 1000  # 최대 로그 라인 수
        self._current_lines = 0
        self._font_size = 12  # 기본 폰트 크기 (12px로 변경)
        self._buffer_lines = []  # (line, level)
        self._text_filter = ""
        self._level_filter = "all"  # all|debug|info|warning|error|critical

        # UI 구성
        self._setup_ui()
        self._connect_signals()

        # 로그 구문 강조기 설정
        self._setup_syntax_highlighter()

        self.logger.info("✅ 로그 뷰어 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 상단 컨트롤 패널
        control_layout = self._create_control_panel()
        layout.addLayout(control_layout)

        # 로그 표시 영역
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setObjectName("log-text-display")
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setFont(QFont("Consolas", self._font_size))  # 고정폭 폰트
        self.log_text_edit.setPlaceholderText("로그 메시지가 여기에 표시됩니다...")
        layout.addWidget(self.log_text_edit)

        # 하단 상태 표시
        self.status_label = QLabel("로그 준비됨 - 0개 메시지")
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.status_label)

    def _create_control_panel(self) -> QHBoxLayout:
        """상단 컨트롤 패널 생성"""
        layout = QHBoxLayout()

        # 제목
        title_label = QLabel("📄 로그 뷰어")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)

        # 스페이서
        layout.addStretch()

        # 레벨 필터 콤보박스 (전체/ERROR/DEBUG/INFO/WARNING)
        self.level_filter_combo = QComboBox()
        self.level_filter_combo.addItems(["전체", "ERROR", "WARNING", "DEBUG", "INFO"])
        self.level_filter_combo.setToolTip("로그 레벨 필터")
        layout.addWidget(self.level_filter_combo)

        # 텍스트 필터
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("텍스트 필터... (대소문자 구분 없음)")
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.setFixedWidth(200)
        layout.addWidget(self.filter_edit)

        # 폰트 크기 조절
        font_label = QLabel("폰트:")
        layout.addWidget(font_label)

        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(6, 20)
        self.font_size_spinbox.setValue(self._font_size)
        self.font_size_spinbox.setToolTip("로그 텍스트 폰트 크기")
        layout.addWidget(self.font_size_spinbox)

        # 자동 스크롤 체크박스
        self.auto_scroll_checkbox = QCheckBox("자동 스크롤")
        self.auto_scroll_checkbox.setChecked(True)
        layout.addWidget(self.auto_scroll_checkbox)

        # 로그 지우기 버튼
        self.clear_button = QPushButton("지우기")
        self.clear_button.setObjectName("button-small")
        layout.addWidget(self.clear_button)

        # 로그 저장 버튼
        self.save_button = QPushButton("저장")
        self.save_button.setObjectName("button-small")
        layout.addWidget(self.save_button)

        return layout

    def _connect_signals(self):
        """시그널 연결"""
        self.auto_scroll_checkbox.toggled.connect(self._on_auto_scroll_changed)
        self.clear_button.clicked.connect(self._on_clear_clicked)
        self.save_button.clicked.connect(self._on_save_clicked)

        # 폰트 크기 변경
        self.font_size_spinbox.valueChanged.connect(self._on_font_size_changed)
        # 필터 변경
        self.filter_edit.textChanged.connect(self._on_filter_text_changed)
        self.level_filter_combo.currentTextChanged.connect(self._on_level_filter_changed)

    def _setup_syntax_highlighter(self):
        """로그 구문 강조기 설정"""
        try:
            self.syntax_highlighter = LogSyntaxHighlighter(self.log_text_edit.document())
            self.logger.debug("✅ 로그 구문 강조기 설정 완료")
        except Exception as e:
            self.logger.error(f"❌ 로그 구문 강조기 설정 실패: {e}")

    # ===== 이벤트 핸들러 =====

    def _on_auto_scroll_changed(self, checked: bool):
        """자동 스크롤 토글 변경"""
        self._auto_scroll = checked
        self.auto_scroll_changed.emit(checked)

    def _on_clear_clicked(self):
        """로그 지우기 버튼 클릭"""
        self.clear_logs.emit()
        self._clear_logs()

    def _on_save_clicked(self):
        """로그 저장 버튼 클릭"""
        self.save_logs.emit()

    def _on_font_size_changed(self, size: int):
        """폰트 크기 변경 핸들러"""
        self._font_size = size
        font = QFont("Consolas", size)
        self.log_text_edit.setFont(font)
        self.logger.debug(f"폰트 크기 변경: {size}px")

    # ===== 공개 인터페이스 =====

    def append_log_message(self, log_message: str):
        """로그 메시지 추가 (MVP Presenter 인터페이스)

        Phase 5.1 실시간 로그 스트리밍을 위한 메서드

        Args:
            log_message: 추가할 로그 메시지
        """
        # 대량 문자열이 들어올 수 있으므로 줄 단위로 처리
        if '\n' in log_message:
            for line in log_message.splitlines():
                self.append_log(line)
        else:
            self.append_log(log_message)

    def append_log(self, log_message: str):
        """로그 메시지 추가

        Args:
            log_message: 추가할 로그 메시지
        """
        if not log_message.strip():
            return

        # 최대 라인 수 체크
        if self._current_lines >= self._max_lines:
            self._remove_old_lines()

        # 타임스탬프가 없으면 추가 (파일 포맷과 중복 방지)
        if not log_message.startswith('['):
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {log_message}"

        # 레벨 추출 및 버퍼 저장
        level = self._extract_level(log_message)
        self._buffer_lines.append((log_message, level))
        if len(self._buffer_lines) > self._max_lines:
            overflow = len(self._buffer_lines) - self._max_lines
            if overflow > 0:
                self._buffer_lines = self._buffer_lines[overflow:]

        # 필터 통과 시만 화면에 추가
        if self._should_display(log_message, level):
            cursor = self.log_text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(log_message + "\n")

            self._current_lines += 1
            if self._auto_scroll:
                self._scroll_to_bottom()
            self._update_status()

    def append_logs(self, log_messages: list):
        """여러 로그 메시지 일괄 추가

        Args:
            log_messages: 로그 메시지 리스트
        """
        for message in log_messages:
            if '\n' in message:
                for line in message.splitlines():
                    self.append_log(line)
            else:
                self.append_log(message)

    def clear_log_viewer(self):
        """로그 뷰어 클리어 (MVP Presenter 인터페이스)

        Phase 5.1 MVP 패턴을 위한 메서드
        """
        self._clear_logs()
        self._buffer_lines.clear()

    def _clear_logs(self):
        """로그 내용 지우기"""
        self.log_text_edit.clear()
        self._current_lines = 0
        self._update_status()

    def _scroll_to_bottom(self):
        """스크롤을 맨 아래로 이동"""
        scrollbar = self.log_text_edit.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scrollbar.maximum())

    def _remove_old_lines(self):
        """오래된 로그 라인 제거 (최대 라인 수 유지)"""
        lines_to_remove = self._current_lines - self._max_lines + 100  # 100줄 여유

        cursor = self.log_text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        for _ in range(lines_to_remove):
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # 개행 문자 제거

        self._current_lines -= lines_to_remove

    def _update_status(self):
        """상태 레이블 업데이트"""
        self.status_label.setText(f"로그 활성 - {self._current_lines:,}개 메시지")

    def _extract_level(self, message: str) -> str:
        """로그 메시지에서 레벨 추출"""
        up = message.upper()

        # 브라켓 형태 우선 검색: [DEBUG], [INFO], [WARNING], [ERROR], [CRITICAL]
        for lv in ("CRITICAL", "ERROR", "WARNING", "DEBUG", "INFO"):  # 우선순위 순
            if f"[{lv}]" in up:
                return lv.lower()

        # 브라켓 없이 레벨 키워드 검색 (- upbit.Component - LEVEL - 형태)
        for lv in ("CRITICAL", "ERROR", "WARNING", "DEBUG", "INFO"):
            if f" - {lv} - " in up:
                return lv.lower()

        # 단독 키워드 검색 (공백 경계)
        import re
        for lv in ("CRITICAL", "ERROR", "WARNING", "DEBUG", "INFO"):
            if re.search(rf'\b{lv}\b', up):
                return lv.lower()

        return "info"  # 기본값

    def _should_display(self, message: str, level: str) -> bool:
        # 레벨 필터
        if self._level_filter != "all" and level != self._level_filter:
            return False
        # 텍스트 필터 (대소문자 무시)
        if self._text_filter and self._text_filter.lower() not in message.lower():
            return False
        return True

    def _rebuild_display(self):
        # 버퍼에서 다시 그리기
        self.log_text_edit.clear()
        self._current_lines = 0
        for msg, lv in self._buffer_lines:
            if self._should_display(msg, lv):
                cursor = self.log_text_edit.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertText(msg + "\n")
                self._current_lines += 1
        if self._auto_scroll:
            self._scroll_to_bottom()
        self._update_status()

    def _on_filter_text_changed(self, text: str):
        self._text_filter = text.strip()
        self._rebuild_display()

    def _on_level_filter_changed(self, text: str):
        """레벨 필터 변경 핸들러"""
        # 제공되는 옵션만 매핑: 전체/ERROR/WARNING/DEBUG/INFO
        mapping = {
            "전체": "all",
            "ERROR": "error",
            "WARNING": "warning",
            "DEBUG": "debug",
            "INFO": "info",
        }
        self._level_filter = mapping.get(text.strip(), "all")
        self._rebuild_display()

    def get_log_content(self) -> str:
        """현재 로그 내용 반환

        Returns:
            str: 현재 표시된 모든 로그 내용
        """
        return self.log_text_edit.toPlainText()

    def set_auto_scroll(self, enabled: bool):
        """자동 스크롤 설정

        Args:
            enabled: 자동 스크롤 활성화 여부
        """
        self._auto_scroll = enabled
        self.auto_scroll_checkbox.setChecked(enabled)

    def get_auto_scroll(self) -> bool:
        """자동 스크롤 설정 반환

        Returns:
            bool: 자동 스크롤 활성화 여부
        """
        return self._auto_scroll

    def set_max_lines(self, max_lines: int):
        """최대 로그 라인 수 설정

        Args:
            max_lines: 최대 라인 수
        """
        self._max_lines = max_lines

    def get_line_count(self) -> int:
        """현재 로그 라인 수 반환

        Returns:
            int: 현재 표시된 로그 라인 수
        """
        return self._current_lines

    def scroll_to_top(self):
        """스크롤을 맨 위로 이동"""
        scrollbar = self.log_text_edit.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(0)

    def scroll_to_bottom(self):
        """스크롤을 맨 아래로 이동 (공개 메서드)"""
        self._scroll_to_bottom()

    def find_text(self, text: str, case_sensitive: bool = False) -> bool:
        """텍스트 검색

        Args:
            text: 검색할 텍스트
            case_sensitive: 대소문자 구분 여부

        Returns:
            bool: 검색 성공 여부
        """
        if case_sensitive:
            flags = QTextDocument.FindFlag.FindCaseSensitively
        else:
            flags = QTextDocument.FindFlag(0)
        return self.log_text_edit.find(text, flags)
