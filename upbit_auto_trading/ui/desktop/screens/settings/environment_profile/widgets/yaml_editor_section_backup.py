"""
High-Performance YAML Editor Section
=====================================

PyQt6 모범 사례를 적용한 고성능 YAML 편집기
- Debounced Content Processing
- Optimized Syntax Highlighting
- Efficient Signal Management
- Background Validation
"""

from typing import Optional, Dict, Any, Set
import yaml
import re
from threading import Lock
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QFrame, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QObject
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor, QTextDocument, QTextBlock

from upbit_auto_trading.infrastructure.logging import create_component_logger

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
        self._format_cache = {}  # 형식 캐싱

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

        self.error_format = QTextCharFormat()
        self.error_format.setBackground(QColor("#ffcccc"))
        self.error_format.setForeground(QColor("#cc0000"))

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

    def highlightBlock(self, text: str):
        """
        최적화된 블록 하이라이팅
        - 패턴 매칭 최소화
        - 중복 계산 방지
        """
        if not text.strip():  # 빈 줄은 건너뛰기
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
            key_end = key_start + len(key)
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
        # 문자열 (따옴표로 감싸진)
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
        """헤더 영역 설정"""
        header_frame = QFrame()
        header_frame.setObjectName("yaml_editor_header")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # 제목 레이블
        self.title_label = QLabel("YAML 편집기")
        self.title_label.setObjectName("yaml_editor_title")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # 편집 모드 버튼
        self.edit_mode_button = QPushButton("편집 시작")
        self.edit_mode_button.setObjectName("yaml_edit_mode_button")
        header_layout.addWidget(self.edit_mode_button)

        parent_layout.addWidget(header_frame)

    def _setup_editor(self, parent_layout):
        """편집기 영역 설정"""
        # 텍스트 편집기
        self.text_editor = QPlainTextEdit()
        self.text_editor.setObjectName("yaml_text_editor")

        # 폰트 설정
        font = QFont("Consolas", 10)
        font.setFixedPitch(True)
        self.text_editor.setFont(font)

        # 최적화된 신택스 하이라이터 적용
        self.syntax_highlighter = OptimizedYamlSyntaxHighlighter(self.text_editor.document())

        # 편집기 최적화 설정
        self.text_editor.setMaximumBlockCount(10000)  # 성능을 위한 블록 제한
        self.text_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)

        parent_layout.addWidget(self.text_editor)

    def _setup_footer(self, parent_layout):
        """푸터 영역 설정"""
        footer_frame = QFrame()
        footer_frame.setObjectName("yaml_editor_footer")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(0, 0, 0, 0)

        # 상태 레이블
        self.status_label = QLabel("읽기 전용 모드")
        self.status_label.setObjectName("yaml_editor_status")
        footer_layout.addWidget(self.status_label)

        footer_layout.addStretch()

        # 취소 버튼
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setObjectName("yaml_cancel_button")
        footer_layout.addWidget(self.cancel_button)

        # 저장 버튼
        self.save_button = QPushButton("저장")
        self.save_button.setObjectName("yaml_save_button")
        footer_layout.addWidget(self.save_button)

        parent_layout.addWidget(footer_frame)

    def _connect_signals(self):
        """시그널 연결"""
        # 편집 모드 관련
        self.edit_mode_button.clicked.connect(self._on_edit_mode_requested)
        self.cancel_button.clicked.connect(self._on_cancel_requested)
        self.save_button.clicked.connect(self._on_save_requested)

        # 텍스트 변경 처리 (최적화된 방식)
        self.text_editor.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        """텍스트 변경 처리 - 디바운싱 적용"""
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
        self.save_requested.emit(current_content, self._current_filename)

    def set_content(self, content: str, filename: str = ""):
        """
        컨텐츠 설정 - 프로그래밍적 변경으로 처리
        텍스트 변경 시그널이 발생하지 않도록 함
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
        """편집 모드 설정"""
        self._is_edit_mode = enabled
        self.text_editor.setReadOnly(not enabled)
        self._update_ui_state()

        if enabled:
            logger.info("✏️ 편집 모드 활성화")
        else:
            logger.info("👁️ 읽기 전용 모드 활성화")

    def set_built_in_profile(self, is_built_in: bool):
        """빌트인 프로파일 여부 설정"""
        self._is_built_in_profile = is_built_in
        self._update_ui_state()

    def _update_ui_state(self):
        """UI 상태 업데이트"""
        if self._is_built_in_profile:
            self.edit_mode_button.setText("편집 제한")
            self.edit_mode_button.setEnabled(False)
            self.status_label.setText("빌트인 프로파일 (편집 불가)")
        elif self._is_edit_mode:
            self.edit_mode_button.setText("편집 중")
            self.edit_mode_button.setEnabled(False)
            self.cancel_button.setVisible(True)
            self.save_button.setVisible(True)
            self.status_label.setText("편집 모드")
        else:
            self.edit_mode_button.setText("편집 시작")
            self.edit_mode_button.setEnabled(True)
            self.cancel_button.setVisible(False)
            self.save_button.setVisible(False)
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


class YamlEditorSection(QWidget):
    """
    YAML 편집기 섹션 위젯

    좌우 분할 레이아웃의 우측(2/3 영역)을 담당하여
    선택된 프로파일의 YAML 내용을 직접 편집할 수 있게 합니다.
    """

    # 시그널 정의
    edit_mode_requested = pyqtSignal()                     # 편집 모드 전환 요청
    save_requested = pyqtSignal(str, str)                  # 저장 요청 (content, filename)
    cancel_requested = pyqtSignal()                        # 편집 취소 요청
    content_changed = pyqtSignal(str)                      # 내용 변경 알림
    validation_error = pyqtSignal(str, int)                # 검증 오류 (message, line_number)
    validation_success = pyqtSignal()                      # 검증 성공

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("YamlEditorSection")

        # Infrastructure 로깅 초기화
        logger.info("🔧 YAML 편집기 섹션 초기화 시작")

        # 상태 관리
        self._is_editing = False
        self._has_changes = False
        self._current_filename = ""
        self._original_content = ""
        self._current_profile_name: Optional[str] = None

        # 기본 프로파일 (편집 금지)
        self._built_in_profiles = {'development', 'production', 'testing'}

        # 자동 저장 타이머
        self._auto_save_timer = QTimer()
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._auto_save)

        # 🔥 디바운싱 타이머 추가 (과도한 이벤트 방지)
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._debounced_content_changed)

        # 🔥 프로그래밍 변경 추적 (사용자 입력과 구분)
        self._programmatic_change = False

        # UI 구성
        self._setup_ui()
        self._setup_editor()
        self._connect_signals()

        # 초기 상태 설정
        self._set_read_only_mode()

        logger.info("✅ YAML 편집기 섹션 초기화 완료")

    def _setup_ui(self) -> None:
        """UI 구성요소 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 상단 헤더 영역
        self._create_header_section(layout)

        # 편집기 영역 (메인)
        self._create_editor_section(layout)

        # 하단 액션 버튼 영역
        self._create_action_section(layout)

    def _create_header_section(self, parent_layout: QVBoxLayout) -> None:
        """상단 헤더 섹션 생성"""
        header_frame = QFrame()
        header_frame.setObjectName("yaml_editor_header")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)

        # 파일명 표시
        self.filename_label = QLabel("프로파일을 선택하세요")
        self.filename_label.setObjectName("filename_label")
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        self.filename_label.setFont(font)

        # 상태 표시 레이블
        self.status_label = QLabel("읽기 전용")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        header_layout.addWidget(self.filename_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)

        parent_layout.addWidget(header_frame)

    def _create_editor_section(self, parent_layout: QVBoxLayout) -> None:
        """편집기 섹션 생성 (향후 고급 기능 추가 예정)"""
        # 기본 YAML 편집기 위젯 (점진적 개선)
        self.text_editor = QPlainTextEdit()
        self.text_editor.setObjectName("yaml_text_editor")

        # 편집기를 프레임으로 감싸기
        editor_frame = QFrame()
        editor_frame.setObjectName("yaml_editor_frame")
        editor_layout = QVBoxLayout(editor_frame)
        editor_layout.setContentsMargins(5, 5, 5, 5)
        editor_layout.addWidget(self.text_editor)

        parent_layout.addWidget(editor_frame, 1)  # 확장 가능

    def _create_action_section(self, parent_layout: QVBoxLayout) -> None:
        """하단 액션 버튼 섹션 생성"""
        action_frame = QFrame()
        action_frame.setObjectName("yaml_editor_actions")
        action_layout = QHBoxLayout(action_frame)
        action_layout.setContentsMargins(10, 5, 10, 5)

        # 편집 시작 버튼
        self.edit_button = QPushButton("편집 시작")
        self.edit_button.setObjectName("yaml_edit_button")

        # 저장 버튼
        self.save_button = QPushButton("저장")
        self.save_button.setObjectName("yaml_save_button")
        self.save_button.setVisible(False)

        # 취소 버튼
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setObjectName("yaml_cancel_button")
        self.cancel_button.setVisible(False)

        # 검증 상태 레이블
        self.validation_label = QLabel("")
        self.validation_label.setObjectName("validation_status_label")

        action_layout.addWidget(self.edit_button)
        action_layout.addWidget(self.save_button)
        action_layout.addWidget(self.cancel_button)
        action_layout.addStretch()
        action_layout.addWidget(self.validation_label)

        parent_layout.addWidget(action_frame)

    def _setup_editor(self) -> None:
        """편집기 설정"""
        # 폰트 설정 (모노스페이스)
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_editor.setFont(font)

        # 탭 설정 (2 스페이스)
        self.text_editor.setTabStopDistance(20)  # 약 2 character width

        # 라인 번호는 향후 추가 가능
        self.text_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # YAML 구문 강조 적용
        self.syntax_highlighter = YamlSyntaxHighlighter(self.text_editor.document())

    def _connect_signals(self) -> None:
        """시그널 연결"""
        # 버튼 시그널
        self.edit_button.clicked.connect(self._on_edit_requested)
        self.save_button.clicked.connect(self._on_save_requested)
        self.cancel_button.clicked.connect(self._on_cancel_requested)

        # 편집기 시그널
        self.text_editor.textChanged.connect(self._on_content_changed)

    def load_file_content(self, filename: str, content: str) -> None:
        """
        파일 내용을 편집기에 로드

        Args:
            filename: 파일명
            content: 파일 내용
        """
        try:
            self._current_filename = filename
            self._original_content = content

            # 🔥 프로그래밍 변경 플래그 설정 (사용자 입력이 아님을 표시)
            self._programmatic_change = True

            # 편집기에 내용 설정
            self.text_editor.setPlainText(content)

            # 🔥 프로그래밍 변경 플래그 해제
            self._programmatic_change = False

            # 헤더 업데이트
            self.filename_label.setText(f"📄 {filename}")

            # 변경사항 플래그 초기화
            self._has_changes = False

            # 읽기 전용 모드로 설정
            self._set_read_only_mode()

            logger.info(f"파일 내용 로드 완료: {filename}")

        except Exception as e:
            self._programmatic_change = False  # 예외 시에도 플래그 해제
            logger.error(f"파일 내용 로드 실패: {e}")
            self._show_error_message("파일 로드 오류", f"파일을 로드할 수 없습니다: {e}")

    def set_content(self, content: str, filename: str = "unnamed") -> None:
        """
        편집기에 내용만 설정 (간단한 버전)

        Args:
            content: 설정할 내용
            filename: 표시할 파일명 (선택적)
        """
        try:
            # 🔥 프로그래밍 변경 플래그 설정
            self._programmatic_change = True

            # 편집기에 내용 설정
            self.text_editor.setPlainText(content)

            # 🔥 프로그래밍 변경 플래그 해제
            self._programmatic_change = False

            # 헤더 업데이트 (파일명이 제공된 경우)
            if hasattr(self, 'filename_label') and filename != "unnamed":
                self.filename_label.setText(f"📄 {filename}")

            # 현재 파일명 업데이트
            if filename != "unnamed":
                self._current_filename = filename

            logger.debug(f"편집기 내용 설정 완료: {len(content)} 문자")

        except Exception as e:
            self._programmatic_change = False  # 예외 시에도 플래그 해제
            logger.error(f"편집기 내용 설정 실패: {e}")
            self._show_error_message("내용 설정 오류", f"내용을 설정할 수 없습니다: {e}")

    def _set_read_only_mode(self) -> None:
        """읽기 전용 모드 설정"""
        self._is_editing = False
        self.text_editor.setReadOnly(True)

        # 버튼 상태 변경
        self.edit_button.setVisible(True)
        self.save_button.setVisible(False)
        self.cancel_button.setVisible(False)

        # 상태 레이블 업데이트
        self.status_label.setText("읽기 전용")
        self.status_label.setObjectName("status_readonly")

        logger.debug("읽기 전용 모드로 전환")

    def _set_edit_mode(self) -> None:
        """편집 모드 설정"""
        self._is_editing = True
        self.text_editor.setReadOnly(False)

        # 버튼 상태 변경
        self.edit_button.setVisible(False)
        self.save_button.setVisible(True)
        self.cancel_button.setVisible(True)

        # 상태 레이블 업데이트
        self.status_label.setText("편집 중")
        self.status_label.setObjectName("status_editing")

        # 편집기에 포커스
        self.text_editor.setFocus()

        logger.debug("편집 모드로 전환")

    def _on_edit_requested(self) -> None:
        """편집 시작 요청 처리"""
        if not self._current_filename:
            self._show_error_message("편집 오류", "편집할 파일이 선택되지 않았습니다.")
            return

        # 🚨 기본 프로파일 편집 방지 (중요한 보호 로직)
        if self._is_built_in_profile():
            self._show_error_message(
                "편집 제한",
                f"기본 환경 프로파일 '{self._current_profile_name}'은 안전을 위해 편집할 수 없습니다.\n\n"
                "기본 프로파일은 시스템 설정 파일이므로 외부 텍스트 에디터를 사용하여 수정하세요."
            )
            return

        self._set_edit_mode()
        self.edit_mode_requested.emit()

        logger.info(f"편집 모드 시작: {self._current_filename}")

    def _on_save_requested(self) -> None:
        """저장 요청 처리"""
        if not self._is_editing:
            return

        current_content = self.text_editor.toPlainText()

        # YAML 검증
        if not self._validate_yaml_content(current_content):
            self._show_error_message("저장 오류", "YAML 형식에 오류가 있습니다. 수정 후 다시 시도해주세요.")
            return

        # 저장 요청 시그널 발송
        self.save_requested.emit(current_content, self._current_filename)

        logger.info(f"저장 요청: {self._current_filename}")

    def _on_cancel_requested(self) -> None:
        """편집 취소 요청 처리"""
        if self._has_changes:
            # 변경사항이 있으면 확인 대화상자 표시
            reply = QMessageBox.question(
                self,
                "편집 취소",
                "변경사항이 있습니다. 정말 취소하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        # 원본 내용으로 복원
        self.text_editor.setPlainText(self._original_content)
        self._has_changes = False

        # 읽기 전용 모드로 전환
        self._set_read_only_mode()

        # 취소 요청 시그널 발송
        self.cancel_requested.emit()

        logger.info(f"편집 취소: {self._current_filename}")

    def _on_content_changed(self) -> None:
        """내용 변경 이벤트 처리"""
        if not self._is_editing:
            return

        current_content = self.text_editor.toPlainText()
        self._has_changes = (current_content != self._original_content)

        # 내용 변경 시그널 발송
        self.content_changed.emit(current_content)

        # 자동 저장 타이머 재시작 (3초 후)
        self._auto_save_timer.stop()
        self._auto_save_timer.start(3000)

        # 실시간 검증
        self._validate_yaml_content(current_content)

    def _auto_save(self) -> None:
        """자동 저장 실행"""
        if self._is_editing and self._has_changes:
            current_content = self.text_editor.toPlainText()

            # 자동 저장은 검증 오류가 있어도 실행 (temp 파일로)
            self.content_changed.emit(current_content)
            logger.debug("자동 저장 실행")

    def _validate_yaml_content(self, content: str) -> bool:
        """
        YAML 내용 검증

        Args:
            content: 검증할 YAML 내용

        Returns:
            검증 성공 여부
        """
        try:
            yaml.safe_load(content)

            # 검증 성공
            self.validation_label.setText("✅ 유효한 YAML")
            self.validation_label.setObjectName("validation_success")
            self.validation_success.emit()

            # 오류 강조 제거
            self.syntax_highlighter.clear_error_highlights()

            return True

        except yaml.YAMLError as e:
            # 검증 실패
            error_msg = str(e)
            line_number = getattr(e, 'problem_mark', None)

            if line_number:
                line_no = line_number.line
                self.validation_label.setText(f"❌ YAML 오류 (라인 {line_no + 1})")
                self.validation_error.emit(error_msg, line_no)

                # 오류 라인 강조
                self.syntax_highlighter.highlight_error_line(line_no)
            else:
                self.validation_label.setText("❌ YAML 형식 오류")
                self.validation_error.emit(error_msg, -1)

            self.validation_label.setObjectName("validation_error")

            return False

        except Exception as e:
            # 🔥 로깅 최적화: 반복적인 YAML 검증 오류 메시지 최소화
            error_msg = str(e)
            if "maximum recursion depth exceeded" in error_msg:
                # 순환 참조 오류는 한 번만 로그에 기록
                if not hasattr(self, '_recursion_error_logged'):
                    logger.warning(f"YAML 순환 참조 감지: {e}")
                    self._recursion_error_logged = True
            else:
                logger.error(f"YAML 검증 중 오류: {e}")

            self.validation_label.setText("❌ 검증 오류")
            self.validation_label.setObjectName("validation_error")
            return False

    def _show_error_message(self, title: str, message: str) -> None:
        """오류 메시지 표시"""
        QMessageBox.warning(self, title, message)

    def save_completed(self) -> None:
        """저장 완료 처리"""
        # 원본 내용 업데이트
        self._original_content = self.text_editor.toPlainText()
        self._has_changes = False

        # 읽기 전용 모드로 전환
        self._set_read_only_mode()

        logger.info(f"저장 완료: {self._current_filename}")

    def _on_yaml_structure_changed(self) -> None:
        """YAML 구조 변경 감지 처리"""
        if not self._is_editing:
            return

        current_content = self.text_editor.toPlainText()

        # 고급 실시간 검증 수행
        self._advanced_yaml_validation(current_content)

        logger.debug("YAML 구조 변경 감지됨")

    def _advanced_yaml_validation(self, content: str) -> None:
        """
        고급 YAML 검증 시스템

        기본 구문 검증 + 의미적 검증 + 컨텍스트 도움말 제공
        """
        # 1. 기본 구문 검증
        basic_valid = self._validate_yaml_content(content)

        if not basic_valid:
            return

        # 2. 환경 프로파일 구조 검증
        self._validate_profile_structure(content)

        # 3. 컨텍스트 도움말 업데이트
        self._update_context_help()

    def _validate_profile_structure(self, content: str) -> None:
        """환경 프로파일 구조 검증"""
        try:
            yaml_data = yaml.safe_load(content)

            if not isinstance(yaml_data, dict):
                self._show_structure_warning("프로파일은 YAML 객체여야 합니다")
                return

            # 환경 프로파일 필수 키 검증
            required_keys = ['api', 'database', 'logging']
            missing_keys = [key for key in required_keys if key not in yaml_data]

            if missing_keys:
                self._show_structure_warning(f"필수 키 누락: {', '.join(missing_keys)}")
                return

            # 구조 검증 성공
            self.validation_label.setText("✅ 유효한 환경 프로파일")

        except Exception as e:
            logger.debug(f"구조 검증 중 오류 (무시됨): {e}")

    def _show_structure_warning(self, message: str) -> None:
        """구조 경고 표시"""
        self.validation_label.setText(f"⚠️ {message}")
        self.validation_label.setObjectName("validation_warning")

    def _update_context_help(self) -> None:
        """커서 위치에 따른 컨텍스트 도움말 업데이트"""
        if not hasattr(self, '_context_help_enabled') or not self._context_help_enabled:
            return

        cursor = self.text_editor.textCursor()
        current_line = cursor.block().text()

        # 간단한 컨텍스트 도움말
        help_text = self._get_context_help_for_line(current_line)
        if help_text:
            self.text_editor.setToolTip(help_text)

    def _get_context_help_for_line(self, line: str) -> str:
        """라인별 컨텍스트 도움말 생성"""
        line_stripped = line.strip()

        if 'api:' in line_stripped:
            return "API 설정 섹션: key, secret, base_url 등을 설정합니다"
        elif 'database:' in line_stripped:
            return "데이터베이스 설정 섹션: 연결 정보와 백업 설정을 관리합니다"
        elif 'logging:' in line_stripped:
            return "로깅 설정 섹션: 로그 레벨과 출력 형식을 제어합니다"
        elif 'key:' in line_stripped:
            return "API 키: 업비트 API 접근을 위한 공개 키"
        elif 'secret:' in line_stripped:
            return "API 시크릿: 업비트 API 접근을 위한 비밀 키 (보안 주의)"
        elif 'level:' in line_stripped:
            return "로그 레벨: DEBUG, INFO, WARNING, ERROR, CRITICAL 중 선택"

        return ""

    def enable_context_help(self, enabled: bool = True) -> None:
        """컨텍스트 도움말 활성화/비활성화"""
        self._context_help_enabled = enabled
        if not enabled:
            self.text_editor.setToolTip("")

    def get_editor_info(self) -> Dict[str, Any]:
        """편집기 정보 반환 (디버깅용)"""
        return {
            'filename': self._current_filename,
            'is_editing': self._is_editing,
            'has_changes': self._has_changes,
            'content_length': len(self.text_editor.toPlainText()),
            'advanced_features': {
                'line_numbers': getattr(self.text_editor, '_show_line_numbers', False),
                'auto_indent': getattr(self.text_editor, '_auto_indent_enabled', False),
                'context_help': getattr(self, '_context_help_enabled', False)
            }
        }

    # ============================================================================
    # 🔒 프로파일 보호 및 관리 메서드 (Task 5.3.1 요구사항)
    # ============================================================================

    def set_current_profile(self, profile_name: str) -> None:
        """현재 프로파일 설정 (편집 권한 제어용)

        Args:
            profile_name: 프로파일명 (development, production, testing, 또는 커스텀)
        """
        self._current_profile_name = profile_name

        # 기본 프로파일인 경우 편집 버튼 상태 업데이트
        if self._is_built_in_profile():
            self._update_edit_button_for_built_in_profile()
        else:
            self._restore_edit_button_for_custom_profile()

        logger.debug(f"현재 프로파일 설정: {profile_name} (기본 프로파일: {self._is_built_in_profile()})")

    def _is_built_in_profile(self) -> bool:
        """현재 프로파일이 기본 프로파일인지 확인

        Returns:
            bool: 기본 프로파일(development, production, testing)이면 True
        """
        return self._current_profile_name in self._built_in_profiles

    def _update_edit_button_for_built_in_profile(self) -> None:
        """기본 프로파일용 편집 버튼 상태 업데이트"""
        if hasattr(self, 'edit_button'):
            self.edit_button.setText("편집 제한 (기본 프로파일)")
            self.edit_button.setEnabled(False)
            self.edit_button.setToolTip(
                f"기본 환경 프로파일 '{self._current_profile_name}'은 시스템 보호를 위해 "
                "내부 편집이 제한됩니다. 외부 텍스트 에디터를 사용하세요."
            )

    def _restore_edit_button_for_custom_profile(self) -> None:
        """커스텀 프로파일용 편집 버튼 상태 복원"""
        if hasattr(self, 'edit_button'):
            self.edit_button.setText("편집 시작")
            self.edit_button.setEnabled(True)
            self.edit_button.setToolTip("YAML 파일을 편집 모드로 전환합니다")
