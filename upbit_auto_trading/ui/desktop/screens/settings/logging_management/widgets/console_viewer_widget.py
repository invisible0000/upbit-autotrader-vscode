"""
콘솔 뷰어 위젯

우측 하단에 위치하는 콘솔 출력 표시 영역입니다.
- 실시간 콘솔 출력 캡처
- 콘솔 내용 지우기
- stdout/stderr 출력 구분 표시
"""

from datetime import datetime
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel
)
from PyQt6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor

from upbit_auto_trading.infrastructure.logging import create_component_logger


class ConsoleViewerWidget(QWidget):
    """콘솔 뷰어 위젯 - 우측 하단"""

    # 시그널 정의
    clear_console = pyqtSignal()                # 콘솔 지우기

    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("console-viewer-widget")

        # 로깅
        self.logger = create_component_logger("ConsoleViewerWidget")
        self.logger.info("💻 콘솔 뷰어 위젯 초기화 시작")

        # 내부 상태
        self._max_lines = 500  # 최대 콘솔 라인 수
        self._current_lines = 0

        # 텍스트 포맷 설정
        self._setup_formats()

        # UI 구성
        self._setup_ui()
        self._connect_signals()

        self.logger.info("✅ 콘솔 뷰어 위젯 초기화 완료")

    def _setup_formats(self):
        """텍스트 포맷 설정"""
        # 일반 출력 (stdout)
        self._stdout_format = QTextCharFormat()
        self._stdout_format.setForeground(QColor("#333333"))  # 검은색

        # 오류 출력 (stderr)
        self._stderr_format = QTextCharFormat()
        self._stderr_format.setForeground(QColor("#dc3545"))  # 빨간색

        # 시스템 메시지
        self._system_format = QTextCharFormat()
        self._system_format.setForeground(QColor("#6c757d"))  # 회색

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
        self.console_text_edit.setFont(QFont("Consolas", 9))  # 고정폭 폰트
        self.console_text_edit.setPlaceholderText("콘솔 출력이 여기에 표시됩니다...")

        # 콘솔 스타일 설정
        self.console_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #404040;
            }
        """)
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

        # 콘솔 지우기 버튼
        self.clear_button = QPushButton("지우기")
        self.clear_button.setObjectName("button-small")
        layout.addWidget(self.clear_button)

        return layout

    def _connect_signals(self):
        """시그널 연결"""
        self.clear_button.clicked.connect(self._on_clear_clicked)

    # ===== 이벤트 핸들러 =====

    def _on_clear_clicked(self):
        """콘솔 지우기 버튼 클릭"""
        self.clear_console.emit()
        self._clear_console()

    # ===== 공개 인터페이스 =====

    def append_console_output(self, output: str, is_error: bool = False):
        """콘솔 출력 추가 (MVP Presenter 인터페이스)

        Phase 5.1 MVP 패턴을 위한 메서드

        Args:
            output: 콘솔 출력 내용
            is_error: 에러 메시지 여부
        """
        message_type = "stderr" if is_error else "stdout"
        self.append_console(output, message_type)

    def clear_console_viewer(self):
        """콘솔 뷰어 클리어 (MVP Presenter 인터페이스)

        Phase 5.1 MVP 패턴을 위한 메서드
        """
        self._clear_console()

    def append_console(self, message: str, message_type: str = "stdout"):
        """콘솔 메시지 추가

        Args:
            message: 추가할 콘솔 메시지
            message_type: 메시지 타입 ("stdout", "stderr", "system")
        """
        if not message.strip():
            return

        # 최대 라인 수 체크
        if self._current_lines >= self._max_lines:
            self._remove_old_lines()

        # 타임스탬프가 없으면 추가
        if not message.startswith('['):
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = f"[{timestamp}] {message}"

        # 포맷 선택
        text_format = self._stdout_format
        if message_type == "stderr":
            text_format = self._stderr_format
        elif message_type == "system":
            text_format = self._system_format

        # 콘솔 출력 추가
        cursor = self.console_text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.setCharFormat(text_format)
        cursor.insertText(message + "\n")

        self._current_lines += 1

        # 자동 스크롤 (항상 맨 아래로)
        self._scroll_to_bottom()

        # 상태 업데이트
        self._update_status()

    def append_stdout(self, message: str):
        """표준 출력 메시지 추가

        Args:
            message: stdout 메시지
        """
        self.append_console(message, "stdout")

    def append_stderr(self, message: str):
        """표준 오류 메시지 추가

        Args:
            message: stderr 메시지
        """
        self.append_console(message, "stderr")

    def append_system(self, message: str):
        """시스템 메시지 추가

        Args:
            message: 시스템 메시지
        """
        self.append_console(message, "system")

    def _clear_console(self):
        """콘솔 내용 지우기"""
        self.console_text_edit.clear()
        self._current_lines = 0

        # 시스템 메시지 추가
        self.append_system("콘솔이 지워졌습니다.")

        self._update_status()

    def _scroll_to_bottom(self):
        """스크롤을 맨 아래로 이동"""
        scrollbar = self.console_text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _remove_old_lines(self):
        """오래된 콘솔 라인 제거 (최대 라인 수 유지)"""
        lines_to_remove = self._current_lines - self._max_lines + 50  # 50줄 여유

        cursor = self.console_text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        for _ in range(lines_to_remove):
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # 개행 문자 제거

        self._current_lines -= lines_to_remove

    def _update_status(self):
        """상태 레이블 업데이트"""
        self.status_label.setText(f"콘솔 활성 - {self._current_lines:,}개 메시지")

    def get_console_content(self) -> str:
        """현재 콘솔 내용 반환

        Returns:
            str: 현재 표시된 모든 콘솔 내용
        """
        return self.console_text_edit.toPlainText()

    def set_max_lines(self, max_lines: int):
        """최대 콘솔 라인 수 설정

        Args:
            max_lines: 최대 라인 수
        """
        self._max_lines = max_lines

    def get_line_count(self) -> int:
        """현재 콘솔 라인 수 반환

        Returns:
            int: 현재 표시된 콘솔 라인 수
        """
        return self._current_lines

    def scroll_to_top(self):
        """스크롤을 맨 위로 이동"""
        scrollbar = self.console_text_edit.verticalScrollBar()
        scrollbar.setValue(0)

    def scroll_to_bottom(self):
        """스크롤을 맨 아래로 이동 (공개 메서드)"""
        self._scroll_to_bottom()

    def set_theme(self, theme: str):
        """테마 설정

        Args:
            theme: "light" 또는 "dark"
        """
        if theme == "dark":
            self.console_text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #404040;
                }
            """)
            # 다크 테마 색상 설정
            self._stdout_format.setForeground(QColor("#ffffff"))
            self._stderr_format.setForeground(QColor("#ff6b6b"))
            self._system_format.setForeground(QColor("#8e8e93"))
        else:
            self.console_text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #d0d0d0;
                }
            """)
            # 라이트 테마 색상 설정
            self._stdout_format.setForeground(QColor("#333333"))
            self._stderr_format.setForeground(QColor("#dc3545"))
            self._system_format.setForeground(QColor("#6c757d"))
