"""
YAML Editor with Advanced Validation
====================================

고급 YAML 검증 기능이 탑재된 편집기 위젯
실시간 오류 감지, 툴팁 표시, 구조 검증 등을 제공

Features:
- 실시간 YAML 구문 검증
- 오류 라인 하이라이트 및 툴팁
- 구조적 검증 (키 중복, 들여쓰기 등)
- 상세한 오류 메시지
- 자동 수정 제안
"""

from typing import List, Dict, Optional, Tuple, Any
import yaml
from PyQt6.QtWidgets import (
    QPlainTextEdit, QWidget, QToolTip
)
from PyQt6.QtCore import pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor

from upbit_auto_trading.infrastructure.logging import create_component_logger


logger = create_component_logger("YamlEditorWithValidation")


class ValidationResult:
    """검증 결과를 담는 데이터 클래스"""

    def __init__(self, is_valid: bool = True, errors: Optional[List[Dict[str, Any]]] = None,
                 warnings: Optional[List[Dict[str, Any]]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def get_error_count(self) -> int:
        return len(self.errors)

    def get_warning_count(self) -> int:
        return len(self.warnings)


class YamlEditorWithValidation(QPlainTextEdit):
    """
    고급 검증 기능이 탑재된 YAML 편집기

    실시간으로 YAML 내용을 검증하고 오류를 시각적으로 표시합니다.
    """

    # 시그널 정의
    validation_completed = pyqtSignal(ValidationResult)  # 검증 완료
    error_hovered = pyqtSignal(str, int)                 # 오류 라인 호버
    fix_suggested = pyqtSignal(str, int, str)            # 수정 제안

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("YamlEditorWithValidation")

        logger.info("🔍 고급 YAML 검증 편집기 초기화 시작")

        # 검증 상태
        self._current_validation: Optional[ValidationResult] = None
        self._error_lines: Dict[int, Dict[str, Any]] = {}  # 라인번호 -> 오류정보
        self._warning_lines: Dict[int, Dict[str, Any]] = {}  # 라인번호 -> 경고정보

        # 검증 타이머 (실시간 검증용)
        self._validation_timer = QTimer()
        self._validation_timer.setSingleShot(True)
        self._validation_timer.timeout.connect(self._perform_validation)

        # 툴팁 타이머 (현재 비활성화)
        self._tooltip_timer = QTimer()
        self._tooltip_timer.setSingleShot(True)
        # self._tooltip_timer.timeout.connect(self._show_error_tooltip)
        self._last_hover_position = QPoint()

        # 오류 포맷 설정
        self._setup_error_formats()

        # 이벤트 연결
        self._connect_events()

        logger.info("✅ 고급 YAML 검증 편집기 초기화 완료")

    def _setup_error_formats(self) -> None:
        """오류 표시용 텍스트 포맷 설정"""
        # 오류 라인 포맷
        self.error_format = QTextCharFormat()
        self.error_format.setBackground(QColor("#FFEBEE"))  # 연한 빨강 배경
        self.error_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        self.error_format.setUnderlineColor(QColor("#F44336"))  # 빨강 밑줄

        # 경고 라인 포맷
        self.warning_format = QTextCharFormat()
        self.warning_format.setBackground(QColor("#FFF8E1"))  # 연한 노랑 배경
        self.warning_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        self.warning_format.setUnderlineColor(QColor("#FF9800"))  # 주황 밑줄

    def _connect_events(self) -> None:
        """이벤트 시그널 연결"""
        # 텍스트 변경 시 검증 예약
        self.textChanged.connect(self._schedule_validation)

        # 마우스 이벤트는 mouseMoveEvent에서 처리

    def _schedule_validation(self) -> None:
        """검증 작업 예약 (500ms 지연)"""
        self._validation_timer.stop()
        self._validation_timer.start(500)

    def _perform_validation(self) -> None:
        """실제 검증 수행"""
        content = self.toPlainText()

        if not content.strip():
            # 빈 내용은 유효한 것으로 처리
            result = ValidationResult(is_valid=True)
            self._update_validation_result(result)
            return

        # 검증 실행
        result = self._validate_content(content)
        self._update_validation_result(result)

        logger.debug(f"YAML 검증 완료: 오류 {result.get_error_count()}개, 경고 {result.get_warning_count()}개")

    def _validate_content(self, content: str) -> ValidationResult:
        """
        YAML 내용 종합 검증

        Args:
            content: 검증할 YAML 내용

        Returns:
            검증 결과
        """
        errors = []
        warnings = []

        try:
            # 1. 기본 YAML 구문 검증
            yaml.safe_load(content)

            # 2. 구조적 검증 수행
            structural_errors, structural_warnings = self._validate_structure(content)
            errors.extend(structural_errors)
            warnings.extend(structural_warnings)

            # 3. 스타일 검증 수행
            style_warnings = self._validate_style(content)
            warnings.extend(style_warnings)

        except yaml.YAMLError as e:
            # YAML 파싱 오류
            error_info = self._parse_yaml_error(e, content)
            errors.append(error_info)

        except Exception as e:
            # 기타 오류
            errors.append({
                'line': 0,
                'column': 0,
                'message': f"검증 오류: {str(e)}",
                'type': 'validation_error'
            })

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    def _parse_yaml_error(self, error: yaml.YAMLError, content: str) -> Dict[str, Any]:
        """YAML 오류 정보 파싱"""
        error_info = {
            'line': 0,
            'column': 0,
            'message': str(error),
            'type': 'syntax_error'
        }

        # 오류 위치 정보 추출 (안전한 접근)
        try:
            problem_mark = getattr(error, 'problem_mark', None)
            if problem_mark:
                error_info['line'] = getattr(problem_mark, 'line', 0)
                error_info['column'] = getattr(problem_mark, 'column', 0)
        except (AttributeError, TypeError):
            pass

        # 구체적인 오류 메시지 생성 (안전한 접근)
        try:
            problem = getattr(error, 'problem', None)
            if problem:
                error_info['message'] = str(problem)
        except (AttributeError, TypeError):
            pass        # 상황별 메시지 개선
        msg = error_info['message'].lower()
        if 'could not find expected' in msg:
            error_info['message'] = "구문 오류: 예상되는 문자를 찾을 수 없습니다"
            error_info['suggestion'] = "들여쓰기나 구두점을 확인해보세요"
        elif 'mapping values are not allowed' in msg:
            error_info['message'] = "매핑 값 오류: 잘못된 키-값 구조입니다"
            error_info['suggestion'] = "콜론(:) 사용법을 확인해보세요"
        elif 'found duplicate key' in msg:
            error_info['message'] = "중복 키 오류: 같은 키가 중복됩니다"
            error_info['suggestion'] = "중복된 키를 제거하거나 이름을 변경하세요"

        return error_info

    def _validate_structure(self, content: str) -> Tuple[List[Dict], List[Dict]]:
        """구조적 검증 수행"""
        errors = []
        warnings = []
        lines = content.split('\n')

        # 키 중복 검사
        seen_keys = set()
        for line_no, line in enumerate(lines):
            stripped = line.strip()
            if ':' in stripped and not stripped.startswith('#'):
                key = stripped.split(':')[0].strip()
                if key in seen_keys:
                    errors.append({
                        'line': line_no,
                        'column': 0,
                        'message': f"중복된 키: '{key}'",
                        'type': 'duplicate_key',
                        'suggestion': f"키 '{key}'가 이미 존재합니다. 다른 이름을 사용하세요."
                    })
                seen_keys.add(key)

        # 들여쓰기 일관성 검사
        indentation_errors = self._check_indentation(lines)
        errors.extend(indentation_errors)

        return errors, warnings

    def _check_indentation(self, lines: List[str]) -> List[Dict]:
        """들여쓰기 일관성 검사"""
        errors = []
        indent_stack = [0]  # 들여쓰기 레벨 스택

        for line_no, line in enumerate(lines):
            if not line.strip() or line.strip().startswith('#'):
                continue

            # 현재 라인의 들여쓰기 계산
            indent = len(line) - len(line.lstrip())

            # 들여쓰기 검증 로직
            if indent > indent_stack[-1]:
                # 들여쓰기 증가
                indent_stack.append(indent)
            elif indent < indent_stack[-1]:
                # 들여쓰기 감소
                while indent_stack and indent < indent_stack[-1]:
                    indent_stack.pop()

                if not indent_stack or indent != indent_stack[-1]:
                    errors.append({
                        'line': line_no,
                        'column': 0,
                        'message': f"잘못된 들여쓰기 (현재: {indent})",
                        'type': 'indentation_error',
                        'suggestion': "들여쓰기를 이전 레벨과 맞춰주세요"
                    })

        return errors

    def _validate_style(self, content: str) -> List[Dict]:
        """스타일 검증 (경고)"""
        warnings = []
        lines = content.split('\n')

        for line_no, line in enumerate(lines):
            # 탭 문자 사용 경고
            if '\t' in line:
                warnings.append({
                    'line': line_no,
                    'column': line.find('\t'),
                    'message': "탭 문자 대신 스페이스를 사용하세요",
                    'type': 'style_warning',
                    'suggestion': "YAML에서는 스페이스 들여쓰기를 권장합니다"
                })

            # 줄 끝 공백 경고
            if line.endswith(' ') or line.endswith('\t'):
                warnings.append({
                    'line': line_no,
                    'column': len(line.rstrip()),
                    'message': "줄 끝 공백이 있습니다",
                    'type': 'style_warning',
                    'suggestion': "줄 끝의 불필요한 공백을 제거하세요"
                })

        return warnings

    def _update_validation_result(self, result: ValidationResult) -> None:
        """검증 결과로 UI 업데이트"""
        self._current_validation = result

        # 이전 오류 표시 제거
        self._clear_error_highlights()

        # 오류 라인 정보 업데이트
        self._error_lines.clear()
        self._warning_lines.clear()

        # 오류 하이라이트 적용
        for error in result.errors:
            line_no = error.get('line', 0)
            self._error_lines[line_no] = error
            self._highlight_line(line_no, self.error_format)

        # 경고 하이라이트 적용
        for warning in result.warnings:
            line_no = warning.get('line', 0)
            self._warning_lines[line_no] = warning
            self._highlight_line(line_no, self.warning_format)

        # 검증 완료 시그널 발송
        self.validation_completed.emit(result)

    def _highlight_line(self, line_number: int, format_obj: QTextCharFormat) -> None:
        """특정 라인 하이라이트"""
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        # 해당 라인으로 이동
        for _ in range(line_number):
            cursor.movePosition(QTextCursor.MoveOperation.Down)

        # 라인 전체 선택 및 포맷 적용
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        cursor.mergeCharFormat(format_obj)

    def _clear_error_highlights(self) -> None:
        """모든 오류 하이라이트 제거"""
        cursor = QTextCursor(self.document())
        cursor.select(QTextCursor.SelectionType.Document)

        # 기본 포맷으로 초기화
        default_format = QTextCharFormat()
        cursor.setCharFormat(default_format)

    def mouseMoveEvent(self, e) -> None:
        """마우스 이동 이벤트 (툴팁 기능 비활성화)"""
        super().mouseMoveEvent(e)
        # 현재는 마우스 이벤트 처리를 생략    def _show_error_tooltip(self) -> None:
        """오류 툴팁 표시"""
        cursor = self.cursorForPosition(self.mapFromGlobal(self._last_hover_position))
        line_number = cursor.blockNumber()

        tooltip_text = ""

        # 오류 메시지 수집
        if line_number in self._error_lines:
            error = self._error_lines[line_number]
            tooltip_text += f"🔴 오류: {error['message']}"
            if 'suggestion' in error:
                tooltip_text += f"\\n💡 제안: {error['suggestion']}"

        # 경고 메시지 수집
        if line_number in self._warning_lines:
            if tooltip_text:
                tooltip_text += "\\n\\n"
            warning = self._warning_lines[line_number]
            tooltip_text += f"🟡 경고: {warning['message']}"
            if 'suggestion' in warning:
                tooltip_text += f"\\n💡 제안: {warning['suggestion']}"

        # 툴팁 표시
        if tooltip_text:
            QToolTip.showText(self._last_hover_position, tooltip_text, self)

    def get_validation_result(self) -> Optional[ValidationResult]:
        """현재 검증 결과 반환"""
        return self._current_validation

    def force_validation(self) -> None:
        """즉시 검증 수행"""
        self._validation_timer.stop()
        self._perform_validation()

    def get_error_summary(self) -> str:
        """오류 요약 문자열 반환"""
        if not self._current_validation:
            return "검증되지 않음"

        if self._current_validation.is_valid:
            warning_count = self._current_validation.get_warning_count()
            if warning_count > 0:
                return f"✅ 유효 (경고 {warning_count}개)"
            return "✅ 유효"

        error_count = self._current_validation.get_error_count()
        warning_count = self._current_validation.get_warning_count()

        parts = [f"❌ 오류 {error_count}개"]
        if warning_count > 0:
            parts.append(f"경고 {warning_count}개")

        return ", ".join(parts)
