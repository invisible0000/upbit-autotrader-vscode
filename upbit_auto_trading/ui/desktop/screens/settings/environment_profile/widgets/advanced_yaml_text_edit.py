"""
Advanced YAML Text Editor
========================

고급 YAML 편집 기능을 제공하는 텍스트 에디터
QPlainTextEdit를 확장하여 IDE 수준의 편집 환경 제공

Features:
- 자동 들여쓰기 (YAML 구조 인식)
- 라인 넘버 표시 (선택적)
- 검색 및 바꾸기 (Ctrl+F, Ctrl+H)
- 괄호 매칭
- 현재 라인 강조
- 키보드 단축키
- 탭을 스페이스로 변환 (2스페이스)
"""

from typing import Optional
from PyQt6.QtGui import (
    QFont, QFontMetrics, QPainter, QColor, QTextCursor,
    QKeyEvent, QPaintEvent, QTextCharFormat
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtWidgets import (
    QPlainTextEdit, QWidget, QTextEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QCheckBox, QDialog
)
from PyQt6.QtGui import QTextDocument

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("AdvancedYamlTextEdit")


class LineNumberArea(QWidget):
    """라인 넘버 표시 영역"""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return self.editor.line_number_area_width()

    def paintEvent(self, a0: QPaintEvent):
        self.editor.line_number_area_paint_event(a0)


class SearchDialog(QDialog):
    """검색/바꾸기 다이얼로그"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("검색 및 바꾸기")
        self.setFixedSize(400, 200)
        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)

        # 검색어 입력
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("검색:"))
        self.search_edit = QLineEdit()
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # 바꿀 문자열 입력
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("바꾸기:"))
        self.replace_edit = QLineEdit()
        replace_layout.addWidget(self.replace_edit)
        layout.addLayout(replace_layout)

        # 옵션
        options_layout = QHBoxLayout()
        self.case_sensitive_cb = QCheckBox("대소문자 구분")
        self.whole_word_cb = QCheckBox("전체 단어")
        options_layout.addWidget(self.case_sensitive_cb)
        options_layout.addWidget(self.whole_word_cb)
        layout.addLayout(options_layout)

        # 버튼
        button_layout = QHBoxLayout()
        self.find_button = QPushButton("찾기")
        self.replace_button = QPushButton("바꾸기")
        self.replace_all_button = QPushButton("모두 바꾸기")
        self.close_button = QPushButton("닫기")

        button_layout.addWidget(self.find_button)
        button_layout.addWidget(self.replace_button)
        button_layout.addWidget(self.replace_all_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        # 이벤트 연결
        self.close_button.clicked.connect(self.close)


class AdvancedYamlTextEdit(QPlainTextEdit):
    """
    고급 YAML 편집기

    IDE 수준의 편집 기능을 제공하는 YAML 전용 텍스트 에디터
    """

    # 커스텀 시그널
    yaml_structure_changed = pyqtSignal()  # YAML 구조 변경 시

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # 설정 변수
        self._show_line_numbers = True
        self._auto_indent_enabled = True
        self._tab_size = 2
        self._highlight_current_line = True

        # 라인 넘버 영역
        self.line_number_area = LineNumberArea(self)

        # 검색 다이얼로그
        self.search_dialog: Optional[SearchDialog] = None

        # 기본 설정
        self._setup_editor()
        self._setup_signals()

        logger.debug("고급 YAML 텍스트 에디터 초기화 완료")

    def _setup_editor(self):
        """에디터 기본 설정"""
        # 폰트 설정 (모노스페이스)
        font = QFont("Consolas, Monaco, monospace")
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.setFont(font)

        # 탭 설정
        metrics = QFontMetrics(font)
        self.setTabStopDistance(metrics.horizontalAdvance(' ' * self._tab_size))

        # 기본 에디터 설정
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setObjectName("advanced_yaml_editor")

        # 라인 넘버 표시 설정
        if self._show_line_numbers:
            self._update_line_number_area_width()

        # 현재 라인 강조
        if self._highlight_current_line:
            self._highlight_current_line_display()

    def _setup_signals(self):
        """시그널 연결"""
        # 라인 넘버 업데이트
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line_display)

        # YAML 구조 변경 감지
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        """텍스트 변경 시 처리"""
        # YAML 구조 변경 감지 (들여쓰기 변화)
        self.yaml_structure_changed.emit()

    def keyPressEvent(self, event: QKeyEvent):
        """키보드 이벤트 처리"""
        # Ctrl+F: 검색
        if event.key() == Qt.Key.Key_F and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._show_search_dialog()
            return

        # Ctrl+H: 바꾸기
        if event.key() == Qt.Key.Key_H and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._show_search_dialog(replace_mode=True)
            return

        # Tab -> 스페이스 변환
        if event.key() == Qt.Key.Key_Tab:
            self._insert_spaces(self._tab_size)
            return

        # Enter: 자동 들여쓰기
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self._auto_indent_enabled:
                self._auto_indent()
                return

        # 기본 처리
        super().keyPressEvent(event)

    def _insert_spaces(self, count: int):
        """스페이스 삽입"""
        cursor = self.textCursor()
        cursor.insertText(' ' * count)

    def _auto_indent(self):
        """자동 들여쓰기"""
        cursor = self.textCursor()
        current_line = cursor.block().text()

        # 현재 라인의 들여쓰기 레벨 계산
        indent_level = 0
        for char in current_line:
            if char == ' ':
                indent_level += 1
            else:
                break

        # YAML 구조에 따른 들여쓰기 조정
        new_indent = self._calculate_yaml_indent(current_line, indent_level)

        # 새 라인 + 들여쓰기 삽입
        cursor.insertText('\n' + ' ' * new_indent)

    def _calculate_yaml_indent(self, line: str, current_indent: int) -> int:
        """YAML 구조에 따른 들여쓰기 계산"""
        line_stripped = line.strip()

        # 빈 라인이면 현재 들여쓰기 유지
        if not line_stripped:
            return current_indent

        # 키-값 쌍인 경우 (: 포함)
        if ':' in line_stripped and not line_stripped.startswith('-'):
            if line_stripped.endswith(':'):
                # 키만 있는 경우 -> 다음 레벨로 들여쓰기
                return current_indent + self._tab_size
            else:
                # 키:값 쌍인 경우 -> 같은 레벨 유지
                return current_indent

        # 배열 항목인 경우 (- 시작)
        if line_stripped.startswith('-'):
            # 배열 항목 내부로 들여쓰기
            return current_indent + self._tab_size

        # 기본적으로 현재 들여쓰기 유지
        return current_indent

    def _show_search_dialog(self, replace_mode: bool = False):
        """검색 다이얼로그 표시"""
        if not self.search_dialog:
            self.search_dialog = SearchDialog(self)
            self._connect_search_signals()

        # 선택된 텍스트를 검색어에 설정
        selected_text = self.textCursor().selectedText()
        if selected_text:
            self.search_dialog.search_edit.setText(selected_text)

        self.search_dialog.show()
        self.search_dialog.search_edit.setFocus()

    def _connect_search_signals(self):
        """검색 다이얼로그 시그널 연결"""
        if not self.search_dialog:
            return

        self.search_dialog.find_button.clicked.connect(self._find_text)
        self.search_dialog.replace_button.clicked.connect(self._replace_text)
        self.search_dialog.replace_all_button.clicked.connect(self._replace_all_text)

    def _find_text(self):
        """텍스트 찾기"""
        if not self.search_dialog:
            return

        search_text = self.search_dialog.search_edit.text()
        if not search_text:
            return

        # 검색 옵션 설정
        options = QTextDocument.FindFlag(0)
        if self.search_dialog.case_sensitive_cb.isChecked():
            options |= QTextDocument.FindFlag.FindCaseSensitively
        if self.search_dialog.whole_word_cb.isChecked():
            options |= QTextDocument.FindFlag.FindWholeWords

        # 텍스트 찾기
        found = self.find(search_text, options)
        if not found:
            # 처음부터 다시 검색
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)
            self.find(search_text, options)

    def _replace_text(self):
        """현재 선택된 텍스트 바꾸기"""
        if not self.search_dialog:
            return

        replace_text = self.search_dialog.replace_edit.text()
        cursor = self.textCursor()

        if cursor.hasSelection():
            cursor.insertText(replace_text)

        # 다음 찾기
        self._find_text()

    def _replace_all_text(self):
        """모든 텍스트 바꾸기"""
        if not self.search_dialog:
            return

        search_text = self.search_dialog.search_edit.text()
        replace_text = self.search_dialog.replace_edit.text()

        if not search_text:
            return

        # 처음부터 시작
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.setTextCursor(cursor)

        # 모든 항목 바꾸기
        count = 0
        while self.find(search_text):
            cursor = self.textCursor()
            cursor.insertText(replace_text)
            count += 1

        logger.info(f"총 {count}개 항목이 바뀌었습니다.")

    # 라인 넘버 관련 메서드들
    def line_number_area_width(self):
        """라인 넘버 영역 너비 계산"""
        if not self._show_line_numbers:
            return 0

        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1

        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def _update_line_number_area_width(self):
        """라인 넘버 영역 너비 업데이트"""
        if self._show_line_numbers:
            self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int):
        """라인 넘버 영역 업데이트"""
        if not self._show_line_numbers:
            return

        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()

    def resizeEvent(self, event):
        """크기 변경 이벤트"""
        super().resizeEvent(event)

        if self._show_line_numbers:
            cr = self.contentsRect()
            self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event: QPaintEvent):
        """라인 넘버 그리기"""
        if not self._show_line_numbers:
            return

        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(240, 240, 240))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(120, 120, 120))
                painter.drawText(0, int(top), self.line_number_area.width(),
                               self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def _highlight_current_line_display(self):
        """현재 라인 강조 표시"""
        if not self._highlight_current_line:
            return

        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(Qt.GlobalColor.yellow).lighter(160)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    # 설정 메서드들
    def set_line_numbers_visible(self, visible: bool):
        """라인 넘버 표시 설정"""
        self._show_line_numbers = visible
        if visible:
            self._update_line_number_area_width()
        else:
            self.setViewportMargins(0, 0, 0, 0)
        self.line_number_area.setVisible(visible)

    def set_auto_indent_enabled(self, enabled: bool):
        """자동 들여쓰기 활성화 설정"""
        self._auto_indent_enabled = enabled

    def set_tab_size(self, size: int):
        """탭 크기 설정"""
        self._tab_size = size
        metrics = QFontMetrics(self.font())
        self.setTabStopDistance(metrics.horizontalAdvance(' ' * size))

    def set_current_line_highlight(self, enabled: bool):
        """현재 라인 강조 설정"""
        self._highlight_current_line = enabled
        if enabled:
            self._highlight_current_line_display()
        else:
            self.setExtraSelections([])
