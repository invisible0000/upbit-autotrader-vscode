"""
High-Performance YAML Editor Section
=====================================

PyQt6 모범 사례를 적용한 고성능 YAML 편집기
- Debounced Content Processing
- Optimized Syntax Highlighting
- Efficient Signal Management
- Background Validation
"""

from typing import Optional
import yaml
from threading import Lock
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QFrame, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, QTimer, QObject, Qt
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QTextDocument

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("YamlEditorSection")


class OptimizedYamlSyntaxHighlighter(QSyntaxHighlighter):
    """
    PyQt6 모범 사례를 적용한 최적화된 YAML 신택스 하이라이터
    - Block State Management
    - Format Caching
    - Minimal Recalculation
    """

    def __init__(self, document: QTextDocument):
        super().__init__(document)
        self._setup_formats()
        self._compiled_patterns = self._compile_patterns()

    def _setup_formats(self):
        """텍스트 형식 설정 - 한 번만 계산"""
        self.key_format = QTextCharFormat()
        self.key_format.setForeground(QColor("#0066cc"))
        self.key_format.setFontWeight(700)

        self.value_format = QTextCharFormat()
        self.value_format.setForeground(QColor("#009900"))

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#888888"))
        self.comment_format.setFontItalic(True)

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#cc6600"))

        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#cc0066"))

        self.boolean_format = QTextCharFormat()
        self.boolean_format.setForeground(QColor("#0066cc"))
        self.boolean_format.setFontWeight(600)

    def _compile_patterns(self):
        """정규식 패턴 컴파일 - 한 번만 계산"""
        import re
        return {
            'key': re.compile(r'^(\s*)([a-zA-Z_][\w\s]*?)(\s*:\s*)'),
            'comment': re.compile(r'#.*$'),
            'string_quoted': re.compile(r'"[^"]*"'),
            'string_single': re.compile(r"'[^']*'"),
            'number': re.compile(r'\b\d+\.?\d*\b'),
            'boolean': re.compile(r'\b(true|false|True|False|yes|no|on|off)\b'),
            'list_item': re.compile(r'^(\s*)-\s+'),
        }

    def highlightBlock(self, text: str | None) -> None:
        """
        최적화된 블록 하이라이팅
        - 패턴 매칭 최소화
        - 중복 계산 방지
        """
        if text is None or not text.strip():  # None 체크 및 빈 줄은 건너뛰기
            return

        # 주석 처리 (우선순위 높음)
        comment_match = self._compiled_patterns['comment'].search(text)
        if comment_match:
            start, end = comment_match.span()
            self.setFormat(start, end - start, self.comment_format)
            text_to_process = text[:start]  # 주석 이후는 처리하지 않음
        else:
            text_to_process = text

        if not text_to_process.strip():
            return

        # 키: 값 패턴 처리
        key_match = self._compiled_patterns['key'].match(text_to_process)
        if key_match:
            indent, key, separator = key_match.groups()
            key_start = len(indent)
            self.setFormat(key_start, len(key), self.key_format)

            # 값 부분 처리
            value_start = key_match.end()
            if value_start < len(text_to_process):
                value_text = text_to_process[value_start:]
                self._highlight_value(value_text, value_start)
        else:
            # 리스트 아이템 처리
            list_match = self._compiled_patterns['list_item'].match(text_to_process)
            if list_match:
                value_start = list_match.end()
                if value_start < len(text_to_process):
                    value_text = text_to_process[value_start:]
                    self._highlight_value(value_text, value_start)

    def _highlight_value(self, value_text: str, offset: int):
        """값 부분 하이라이팅"""
        # 패턴별로 하이라이팅 적용
        for pattern, format_obj in [
            (self._compiled_patterns['string_quoted'], self.string_format),
            (self._compiled_patterns['string_single'], self.string_format),
            (self._compiled_patterns['boolean'], self.boolean_format),
            (self._compiled_patterns['number'], self.number_format),
        ]:
            for match in pattern.finditer(value_text):
                start, end = match.span()
                self.setFormat(offset + start, end - start, format_obj)


class DebouncedTextProcessor(QObject):
    """
    디바운싱을 적용한 텍스트 처리기
    - 연속된 변경을 그룹화하여 처리 횟수 최소화
    - Qt 공식 문서 권장사항 적용
    """

    content_processed = pyqtSignal(str)
    validation_completed = pyqtSignal(bool, str, int)  # success, message, line_no

    def __init__(self, debounce_delay: int = 300):
        super().__init__()
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._process_content)
        self._debounce_delay = debounce_delay
        self._pending_content = ""
        self._processing_lock = Lock()

    def request_processing(self, content: str):
        """처리 요청 - 디바운싱 적용"""
        with self._processing_lock:
            self._pending_content = content
            self._debounce_timer.stop()
            self._debounce_timer.start(self._debounce_delay)

    def _process_content(self):
        """실제 컨텐츠 처리"""
        content = self._pending_content
        if not content:
            return

        # 시그널 방출
        self.content_processed.emit(content)

        # YAML 검증 (백그라운드)
        try:
            yaml.safe_load(content)
            self.validation_completed.emit(True, "", 0)
        except yaml.YAMLError as e:
            line_no = getattr(e, 'problem_mark', None)
            line_number = line_no.line + 1 if line_no else 0
            error_msg = str(e).split('\n')[0]  # 첫 번째 줄만
            self.validation_completed.emit(False, error_msg, line_number)
        except Exception as e:
            self.validation_completed.emit(False, f"검증 오류: {str(e)}", 0)


class YamlEditorSection(QWidget):
    """
    고성능 YAML 편집기 섹션
    - Debounced Content Processing
    - Optimized Syntax Highlighting
    - Efficient Signal Management
    """

    # 시그널 정의
    edit_mode_requested = pyqtSignal()
    save_requested = pyqtSignal(str, str)  # content, filename
    cancel_requested = pyqtSignal()
    content_changed = pyqtSignal(str)
    validation_error = pyqtSignal(str, int)  # message, line_number
    validation_success = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("YamlEditorSection")

        # 상태 관리
        self._current_filename = ""
        self._is_edit_mode = False
        self._is_built_in_profile = False
        self._original_content = ""
        self._programmatic_change = False  # 프로그래밍적 변경 구분
        self._font_size = 12  # 기본 폰트 크기

        # 고성능 텍스트 프로세서 초기화
        self._text_processor = DebouncedTextProcessor(debounce_delay=300)
        self._text_processor.content_processed.connect(self._on_content_processed)
        self._text_processor.validation_completed.connect(self._on_validation_completed)

        self._setup_ui()
        self._connect_signals()

        logger.info("🚀 고성능 YAML 편집기 초기화 완료")

    def _setup_ui(self):
        """UI 구성 요소 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 헤더 구성
        self._setup_header(layout)

        # 편집기 구성
        self._setup_editor(layout)

        # 푸터 구성
        self._setup_footer(layout)

        # 초기 상태 설정
        self._update_ui_state()

    def _setup_header(self, parent_layout):
        """헤더 영역 설정 - 이슈 3 해결: 상태 레이블을 편집 버튼 왼쪽으로 이동"""
        header_frame = QFrame()
        header_frame.setObjectName("yaml_editor_header")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # 제목 레이블
        self.title_label = QLabel("YAML 편집기")
        self.title_label.setObjectName("yaml_editor_title")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # 폰트 크기 조절 컨트롤
        self._add_font_size_controls(header_layout)

        header_layout.addStretch()

        # 상태 레이블 (편집 버튼 왼쪽에 배치)
        self.status_label = QLabel("읽기 전용 모드")
        self.status_label.setObjectName("yaml_editor_status")
        header_layout.addWidget(self.status_label)

        # 편집 모드 버튼
        self.edit_mode_button = QPushButton("편집 시작")
        self.edit_mode_button.setObjectName("yaml_edit_mode_button")
        header_layout.addWidget(self.edit_mode_button)

        # 저장 버튼 (편집 시작 버튼 우측)
        self.save_button = QPushButton("저장")
        self.save_button.setObjectName("yaml_save_button")
        self.save_button.setEnabled(False)  # 기본적으로 비활성화
        header_layout.addWidget(self.save_button)

        # 취소 버튼 (저장 버튼 우측)
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setObjectName("yaml_cancel_button")
        self.cancel_button.setEnabled(False)  # 기본적으로 비활성화
        header_layout.addWidget(self.cancel_button)

        parent_layout.addWidget(header_frame)

    def _setup_editor(self, parent_layout):
        """편집기 영역 설정"""
        # 텍스트 편집기
        self.text_editor = QPlainTextEdit()
        self.text_editor.setObjectName("yaml_text_editor")

        # 최적화된 신택스 하이라이터 적용
        document = self.text_editor.document()
        if document is not None:
            self.syntax_highlighter = OptimizedYamlSyntaxHighlighter(document)
        else:
            self.syntax_highlighter = None

        # 편집기 최적화 설정 (PyQt6 성능 권장사항)
        self.text_editor.setMaximumBlockCount(10000)  # 성능을 위한 블록 제한
        self.text_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)

        # 초기 상태: 읽기 전용 설정 및 스타일 적용
        self.text_editor.setReadOnly(True)
        self._apply_editor_style()  # 일관된 초기 스타일 적용

        parent_layout.addWidget(self.text_editor)

    def _setup_footer(self, parent_layout):
        """푸터 영역 설정 - 버튼들이 헤더로 이동하여 여기서는 최소한만 유지"""
        # 푸터는 현재 불필요하므로 제거
        pass

    def _add_font_size_controls(self, header_layout: QHBoxLayout) -> None:
        """폰트 크기 조절 컨트롤 추가"""
        # 폰트 크기 라벨
        font_label = QLabel("폰트:")
        font_label.setObjectName("font_size_label")
        header_layout.addWidget(font_label)

        # 폰트 크기 감소 버튼
        self.font_decrease_btn = QPushButton("-")
        self.font_decrease_btn.setObjectName("font_size_button")
        self.font_decrease_btn.setFixedSize(24, 24)
        self.font_decrease_btn.clicked.connect(self._decrease_font_size)
        header_layout.addWidget(self.font_decrease_btn)

        # 폰트 크기 표시 라벨
        self.font_size_label = QLabel(str(self._font_size))
        self.font_size_label.setObjectName("font_size_display")
        self.font_size_label.setFixedWidth(30)
        self.font_size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.font_size_label)

        # 폰트 크기 증가 버튼
        self.font_increase_btn = QPushButton("+")
        self.font_increase_btn.setObjectName("font_size_button")
        self.font_increase_btn.setFixedSize(24, 24)
        self.font_increase_btn.clicked.connect(self._increase_font_size)
        header_layout.addWidget(self.font_increase_btn)

    def _increase_font_size(self) -> None:
        """폰트 크기 증가 (최대 40pt)"""
        if self._font_size < 40:
            self._font_size += 2
            self._update_font_size()

    def _decrease_font_size(self) -> None:
        """폰트 크기 감소 (최소 10pt)"""
        if self._font_size > 10:
            self._font_size -= 2
            self._update_font_size()

    def _update_font_size(self) -> None:
        """폰트 크기 업데이트"""
        self.font_size_label.setText(str(self._font_size))
        # 현재 편집기 스타일 다시 적용
        self._apply_editor_style()
        logger.debug(f"📏 폰트 크기 변경: {self._font_size}pt")

    def _connect_signals(self):
        """시그널 연결 - Qt 모범 사례 적용"""
        # 편집 모드 관련
        self.edit_mode_button.clicked.connect(self._on_edit_mode_requested)
        self.cancel_button.clicked.connect(self._on_cancel_requested)
        self.save_button.clicked.connect(self._on_save_requested)

        # 텍스트 변경 처리 (최적화된 방식)
        self.text_editor.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        """
        텍스트 변경 처리 - 디바운싱 적용
        Qt 공식 문서 권장: "defer using timer for better performance"
        """
        if self._programmatic_change:
            return  # 프로그래밍적 변경은 무시

        current_content = self.text_editor.toPlainText()

        # 디바운싱된 처리 요청
        self._text_processor.request_processing(current_content)

    def _on_content_processed(self, content: str):
        """디바운싱된 컨텐츠 처리"""
        if content != self._original_content:
            logger.debug(f"📝 내용 변경됨 ({len(content)} 문자)")
            self.content_changed.emit(content)

    def _on_validation_completed(self, success: bool, message: str, line_no: int):
        """YAML 검증 완료"""
        if success:
            logger.debug("✅ YAML 검증 성공")
            self.validation_success.emit()
        else:
            logger.warning(f"❌ YAML 검증 실패: {message} (line {line_no})")
            self.validation_error.emit(message, line_no)

    def _on_edit_mode_requested(self):
        """편집 모드 요청"""
        if self._is_built_in_profile:
            QMessageBox.warning(
                self, "편집 제한",
                "빠른 환경 프로파일(development, production, testing)은 편집할 수 없습니다."
            )
            return

        self.edit_mode_requested.emit()

    def _on_cancel_requested(self):
        """편집 취소 요청"""
        self.cancel_requested.emit()

    def _on_save_requested(self):
        """저장 요청"""
        if not self._current_filename:
            logger.warning("저장할 파일명이 없습니다")
            return

        current_content = self.text_editor.toPlainText()
        logger.info(f"💾 저장 요청: {self._current_filename}")
        self.save_requested.emit(current_content, self._current_filename)

    def set_content(self, content: str, filename: str = ""):
        """
        컨텐츠 설정 - 프로그래밍적 변경으로 처리
        textChanged 시그널이 발생하지 않도록 함
        """
        self._programmatic_change = True
        try:
            self._current_filename = filename
            self._original_content = content

            # 텍스트 설정
            self.text_editor.setPlainText(content)

            # UI 업데이트
            if filename:
                self.title_label.setText(f"YAML 편집기 - {filename}")
            else:
                self.title_label.setText("YAML 편집기")

            self._update_ui_state()
            logger.info(f"📄 컨텐츠 로드 완료: {filename} ({len(content)} 문자)")

        finally:
            self._programmatic_change = False

    def set_edit_mode(self, enabled: bool):
        """편집 모드 설정 - 원칙적 구현"""
        self._is_edit_mode = enabled
        self.text_editor.setReadOnly(not enabled)

        # 통일된 스타일 시스템 적용
        self._apply_editor_style()

        # 구문 강조기 강제 업데이트 (모든 모드에서 구문 강조 유지)
        if hasattr(self, 'syntax_highlighter') and self.syntax_highlighter:
            self.syntax_highlighter.rehighlight()

        self._update_ui_state()

        mode_name = "편집" if enabled else "읽기"
        logger.info(f"🎯 {mode_name} 모드 활성화 (구문 강조 유지)")

    def _apply_editor_style(self) -> None:
        """편집기 스타일 적용 - 폰트 크기와 모드에 따른 일관된 스타일"""
        # 기본 스타일: 모든 모드에서 동일한 폰트와 구문 강조
        base_style = f"""
            QPlainTextEdit {{
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: {self._font_size}pt;
                line-height: 1.4;
                border-radius: 4px;
                padding: 10px;
                selection-background-color: #3399ff;
            }}
        """

        if self._is_edit_mode:
            # 편집 모드: 어두운 배경 + 초록 테두리
            edit_style = base_style + """
                QPlainTextEdit {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 2px solid #4CAF50;
                }
                QPlainTextEdit:focus {
                    border: 2px solid #66BB6A;
                }
            """
            self.text_editor.setStyleSheet(edit_style)
        else:
            # 읽기 모드: 밝은 배경 + 회색 테두리 (구문 강조 유지)
            read_style = base_style + """
                QPlainTextEdit {
                    background-color: #fafafa;
                    color: #2d2d2d;
                    border: 1px solid #cccccc;
                }
                QPlainTextEdit:focus {
                    border: 1px solid #999999;
                }
            """
            self.text_editor.setStyleSheet(read_style)

    def set_built_in_profile(self, is_built_in: bool):
        """빌트인 프로파일 여부 설정"""
        self._is_built_in_profile = is_built_in
        self._update_ui_state()

    def _update_ui_state(self):
        """UI 상태 업데이트 - 새로운 버튼 배치에 맞게 수정"""
        if self._is_built_in_profile:
            self.edit_mode_button.setText("편집 제한")
            self.edit_mode_button.setEnabled(False)
            self.save_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.status_label.setText("빌트인 프로파일 (편집 불가)")
        elif self._is_edit_mode:
            self.edit_mode_button.setText("편집 중")
            self.edit_mode_button.setEnabled(False)
            self.save_button.setEnabled(True)  # 편집 모드에서 활성화
            self.cancel_button.setEnabled(True)  # 편집 모드에서 활성화
            self.status_label.setText("편집 모드")
        else:
            self.edit_mode_button.setText("편집 시작")
            self.edit_mode_button.setEnabled(True)
            self.save_button.setEnabled(False)  # 읽기 전용에서 비활성화
            self.cancel_button.setEnabled(False)  # 읽기 전용에서 비활성화
            self.status_label.setText("읽기 전용 모드")

    def get_content(self) -> str:
        """현재 컨텐츠 반환"""
        return self.text_editor.toPlainText()

    def is_modified(self) -> bool:
        """변경 여부 확인"""
        return self.get_content() != self._original_content

    def clear_content(self):
        """컨텐츠 클리어"""
        self.set_content("", "")

    def focus_editor(self):
        """편집기에 포커스"""
        self.text_editor.setFocus()

    def load_file_content(self, filename: str, content: str):
        """
        파일 내용 로드 - 기존 인터페이스 호환성 유지
        Args:
            filename: 파일명
            content: YAML 내용
        """
        self.set_content(content, filename)
        logger.info(f"📄 파일 로드 완료: {filename} ({len(content)} 문자)")

    def set_current_profile(self, profile_name: str):
        """
        현재 프로파일 설정 - 기존 인터페이스 호환성 유지
        빌트인 프로파일 보호를 위해 사용
        """
        built_in_profiles = ["development", "production", "testing"]
        self.set_built_in_profile(profile_name in built_in_profiles)
        logger.debug(f"🔒 프로파일 설정: {profile_name} (빌트인: {profile_name in built_in_profiles})")
