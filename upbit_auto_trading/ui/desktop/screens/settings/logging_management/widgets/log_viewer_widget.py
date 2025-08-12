"""
로그 뷰어 위젯

우측 상단에 위치하는 로그 메시지 표시 영역입니다.
- 실시간 로그 메시지 표시
- 자동 스크롤 기능
- 로그 필터링
- 로그 내용 저장
"""

from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QCheckBox, QLabel, QGroupBox
)
from PyQt6.QtGui import QFont, QTextCursor

from upbit_auto_trading.infrastructure.logging import create_component_logger


class LogViewerWidget(QWidget):
    """로그 뷰어 위젯 - 우측 상단"""

    # 시그널 정의
    clear_logs = pyqtSignal()                   # 로그 지우기
    save_logs = pyqtSignal()                    # 로그 저장
    auto_scroll_changed = pyqtSignal(bool)      # 자동 스크롤 토글

    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("log-viewer-widget")

        # 로깅
        self.logger = create_component_logger("LogViewerWidget")
        self.logger.info("📄 로그 뷰어 위젯 초기화 시작")

        # 내부 상태
        self._auto_scroll = True
        self._max_lines = 1000  # 최대 로그 라인 수
        self._current_lines = 0

        # UI 구성
        self._setup_ui()
        self._connect_signals()

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
        self.log_text_edit.setFont(QFont("Consolas", 9))  # 고정폭 폰트
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

    # ===== 공개 인터페이스 =====

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

        # 타임스탬프가 없으면 추가
        if not log_message.startswith('['):
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {log_message}"

        # 로그 추가
        cursor = self.log_text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(log_message + "\n")

        self._current_lines += 1

        # 자동 스크롤
        if self._auto_scroll:
            self._scroll_to_bottom()

        # 상태 업데이트
        self._update_status()

    def append_logs(self, log_messages: list):
        """여러 로그 메시지 일괄 추가

        Args:
            log_messages: 로그 메시지 리스트
        """
        for message in log_messages:
            self.append_log(message)

    def _clear_logs(self):
        """로그 내용 지우기"""
        self.log_text_edit.clear()
        self._current_lines = 0
        self._update_status()

    def _scroll_to_bottom(self):
        """스크롤을 맨 아래로 이동"""
        scrollbar = self.log_text_edit.verticalScrollBar()
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
        flags = QTextCursor.FindFlag(0)
        if case_sensitive:
            flags |= QTextCursor.FindFlag.FindCaseSensitively

        return self.log_text_edit.find(text, flags)
