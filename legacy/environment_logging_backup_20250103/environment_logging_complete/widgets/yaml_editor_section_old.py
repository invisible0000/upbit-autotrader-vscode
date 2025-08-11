"""
YAML Editor Section
==================

YAML 직접 편집을 위한 섹션 위젯 (우측 섹션 담당)
좌우 1:2 레이아웃의 우측에 위치하여 YAML 파일을 직접 편집

Features:
- 구문 강조가 적용된 YAML 편집기
- 실시간 YAML 검증
- 자동 저장 및 수동 저장
- 편집 모드 관리 (읽기 전용 ↔ 편집 모드)
- Temp 파일 기반 안전한 편집
- 변경사항 추적
"""

from typing import Optional, Dict, Any
import yaml
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QFrame, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .yaml_syntax_highlighter import YamlSyntaxHighlighter


logger = create_component_logger("YamlEditorSection")


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

        # 자동 저장 타이머
        self._auto_save_timer = QTimer()
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._auto_save)

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
        """편집기 섹션 생성"""
        # 편집기 위젯
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

            # 편집기에 내용 설정
            self.text_editor.setPlainText(content)

            # 헤더 업데이트
            self.filename_label.setText(f"📄 {filename}")

            # 변경사항 플래그 초기화
            self._has_changes = False

            # 읽기 전용 모드로 설정
            self._set_read_only_mode()

            logger.info(f"파일 내용 로드 완료: {filename}")

        except Exception as e:
            logger.error(f"파일 내용 로드 실패: {e}")
            self._show_error_message("파일 로드 오류", f"파일을 로드할 수 없습니다: {e}")

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

    def get_editor_info(self) -> Dict[str, Any]:
        """편집기 정보 반환 (디버깅용)"""
        return {
            'filename': self._current_filename,
            'is_editing': self._is_editing,
            'has_changes': self._has_changes,
            'content_length': len(self.text_editor.toPlainText()),
            'highlighter_info': self.syntax_highlighter.get_highlighting_info()
        }
