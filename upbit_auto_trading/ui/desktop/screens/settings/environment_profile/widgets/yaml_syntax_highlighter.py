"""
YAML Syntax Highlighter
=======================

YAML 파일용 구문 강조 시스템
PyQt6 QSyntaxHighlighter 기반으로 구현

Features:
- YAML 키-값 구문 강조
- 주석 강조
- 문자열 값 강조
- 들여쓰기 시각화
- 테마 시스템 연동 (다크/라이트)
- 오류 라인 강조
"""

import re
from typing import List, Tuple, Optional
from PyQt6.QtGui import (
    QSyntaxHighlighter, QTextDocument, QTextCharFormat,
    QFont, QColor
)

# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)
from upbit_auto_trading.ui.desktop.common.theme_notifier import ThemeNotifier
logger = create_component_logger("YamlSyntaxHighlighter")

class YamlSyntaxHighlighter(QSyntaxHighlighter):
    """
    YAML 구문 강조 클래스

    테마 변경에 자동으로 반응하여 색상을 업데이트합니다.
    """

    def __init__(self, parent: Optional[QTextDocument] = None):
        super().__init__(parent)

        # 테마 변경 알림 시스템 연결
        self.theme_notifier = ThemeNotifier()
        self.theme_notifier.theme_changed.connect(self._on_theme_changed)

        # 강조 규칙 저장
        self.highlighting_rules: List[Tuple[re.Pattern, QTextCharFormat]] = []

        # 문자 포맷 초기화
        self._init_formats()

        # 강조 규칙 설정
        self._setup_highlighting_rules()

        logger.debug("YAML 구문 강조기 초기화 완료")

    def _init_formats(self) -> None:
        """문자 포맷 객체들 초기화"""
        # 키 (key) 포맷
        self.key_format = QTextCharFormat()
        self.key_format.setFontWeight(QFont.Weight.Bold)

        # 값 (value) 포맷
        self.value_format = QTextCharFormat()

        # 문자열 값 포맷 (따옴표로 둘러싸인)
        self.string_format = QTextCharFormat()

        # 주석 포맷
        self.comment_format = QTextCharFormat()
        self.comment_format.setFontItalic(True)

        # 숫자 포맷
        self.number_format = QTextCharFormat()

        # 불린 값 포맷
        self.boolean_format = QTextCharFormat()
        self.boolean_format.setFontWeight(QFont.Weight.Bold)

        # 널 값 포맷
        self.null_format = QTextCharFormat()
        self.null_format.setFontItalic(True)

        # 구분자 포맷 (콜론, 하이픈)
        self.separator_format = QTextCharFormat()
        self.separator_format.setFontWeight(QFont.Weight.Bold)

        # 오류 포맷
        self.error_format = QTextCharFormat()
        self.error_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)

        # 테마에 따른 색상 설정
        self._update_colors_for_theme()

    def _update_colors_for_theme(self) -> None:
        """현재 테마에 맞는 색상으로 업데이트"""
        is_dark = self.theme_notifier.is_dark_theme()

        if is_dark:
            # 다크 테마 색상
            self.key_format.setForeground(QColor("#89CFF0"))      # 라이트 블루
            self.value_format.setForeground(QColor("#F0F0F0"))    # 밝은 회색
            self.string_format.setForeground(QColor("#90EE90"))   # 라이트 그린
            self.comment_format.setForeground(QColor("#808080"))  # 회색
            self.number_format.setForeground(QColor("#FFB347"))   # 오렌지
            self.boolean_format.setForeground(QColor("#DDA0DD"))  # 플럼
            self.null_format.setForeground(QColor("#A0A0A0"))     # 회색
            self.separator_format.setForeground(QColor("#FFFF00"))  # 노란색
            self.error_format.setUnderlineColor(QColor("#FF6B6B"))  # 빨간색
        else:
            # 라이트 테마 색상
            self.key_format.setForeground(QColor("#0066CC"))      # 블루
            self.value_format.setForeground(QColor("#333333"))    # 다크 그레이
            self.string_format.setForeground(QColor("#008000"))   # 그린
            self.comment_format.setForeground(QColor("#666666"))  # 회색
            self.number_format.setForeground(QColor("#FF6600"))   # 오렌지
            self.boolean_format.setForeground(QColor("#8B008B"))  # 다크 마젠타
            self.null_format.setForeground(QColor("#999999"))     # 회색
            self.separator_format.setForeground(QColor("#B8860B"))  # 다크 골든로드
            self.error_format.setUnderlineColor(QColor("#CC0000"))  # 빨간색

        logger.debug(f"테마 색상 업데이트 완료 (다크: {is_dark})")

    def _setup_highlighting_rules(self) -> None:
        """고급 구문 강조 규칙 설정"""
        self.highlighting_rules.clear()

        # 1. 주석 (# 으로 시작하는 라인)
        comment_pattern = re.compile(r'#.*$', re.MULTILINE)
        self.highlighting_rules.append((comment_pattern, self.comment_format))

        # 2. YAML 키 (줄 시작부터 콜론까지, 들여쓰기 포함)
        key_pattern = re.compile(r'^(\s*)([^:\s#]+)(?=\s*:)', re.MULTILINE)
        self.highlighting_rules.append((key_pattern, self.key_format))

        # 3. 문자열 값 (따옴표로 둘러싸인) - 개선된 패턴
        string_single_pattern = re.compile(r"'(?:[^'\\]|\\.)*'")  # 이스케이프 문자 지원
        string_double_pattern = re.compile(r'"(?:[^"\\]|\\.)*"')  # 이스케이프 문자 지원
        self.highlighting_rules.append((string_single_pattern, self.string_format))
        self.highlighting_rules.append((string_double_pattern, self.string_format))

        # 4. 숫자 값 (정수, 소수, 과학표기법)
        number_pattern = re.compile(r'\b-?(?:\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)\b')
        self.highlighting_rules.append((number_pattern, self.number_format))

        # 5. 불린 값 (YAML 표준)
        boolean_pattern = re.compile(r'\b(true|false|True|False|TRUE|FALSE|yes|no|Yes|No|YES|NO|on|off|On|Off|ON|OFF)\b')
        self.highlighting_rules.append((boolean_pattern, self.boolean_format))

        # 6. 널 값 (YAML 표준)
        null_pattern = re.compile(r'\b(null|Null|NULL|~)\b')
        self.highlighting_rules.append((null_pattern, self.null_format))

        # 7. YAML 특수 구문
        # 7a. 문서 시작/끝 구분자
        doc_separator_pattern = re.compile(r'^(---|\.\.\.)\s*$', re.MULTILINE)
        self.highlighting_rules.append((doc_separator_pattern, self.separator_format))

        # 7b. 배열 항목 (-로 시작)
        array_pattern = re.compile(r'^(\s*)(-)\s+')
        self.highlighting_rules.append((array_pattern, self.separator_format))

        # 7c. 콜론 구분자
        colon_pattern = re.compile(r':(?=\s|$)')
        self.highlighting_rules.append((colon_pattern, self.separator_format))

        # 8. YAML 참조 및 앵커 (고급 기능)
        anchor_pattern = re.compile(r'&\w+')  # 앵커 정의
        reference_pattern = re.compile(r'\*\w+')  # 참조
        self.highlighting_rules.append((anchor_pattern, self.key_format))  # 키와 같은 색상
        self.highlighting_rules.append((reference_pattern, self.key_format))

        # 9. 멀티라인 문자열 표시자
        multiline_pattern = re.compile(r'[|>][-+]?\d*\s*$')
        self.highlighting_rules.append((multiline_pattern, self.separator_format))

        logger.debug(f"고급 구문 강조 규칙 설정 완료: {len(self.highlighting_rules)}개 규칙")

    def highlightBlock(self, text):
        """
        텍스트 블록에 고급 구문 강조 적용

        Args:
            text: 강조할 텍스트 라인
        """
        # 기본 강조 규칙 적용
        for pattern, char_format in self.highlighting_rules:
            # 주석 규칙은 특별 처리 (전체 라인)
            if pattern.pattern == r'#.*$':
                match = pattern.search(text)
                if match:
                    start, end = match.span()
                    self.setFormat(start, end - start, char_format)

            # 키 패턴은 그룹 2만 강조 (들여쓰기 제외)
            elif pattern.pattern == r'^(\s*)([^:\s#]+)(?=\s*:)':
                match = pattern.search(text)
                if match:
                    # 그룹 2 (키 부분)만 강조
                    key_start = match.start(2)
                    key_end = match.end(2)
                    self.setFormat(key_start, key_end - key_start, char_format)

            # 배열 항목 패턴 (- 기호만 강조)
            elif pattern.pattern == r'^(\s*)(-)\s+':
                match = pattern.search(text)
                if match:
                    # 그룹 2 (- 기호)만 강조
                    dash_start = match.start(2)
                    dash_end = match.end(2)
                    self.setFormat(dash_start, dash_end - dash_start, char_format)

            # 문서 구분자 패턴 (전체 매치)
            elif pattern.pattern == r'^(---|\.\.\.)\s*$':
                match = pattern.search(text)
                if match:
                    start, end = match.span()
                    self.setFormat(start, end - start, char_format)

            # 나머지 패턴들 (일반 처리)
            else:
                for match in pattern.finditer(text):
                    start, end = match.span()
                    self.setFormat(start, end - start, char_format)

        # 현재 라인 강조 (선택적)
        if text:  # None 체크
            self._highlight_current_line_if_needed(text)

    def _highlight_current_line_if_needed(self, text: str) -> None:
        """현재 편집 중인 라인 미묘하게 강조 (선택적 기능)"""
        # 이 기능은 현재 비활성화 - 필요시 구현
        pass

    def highlight_error_line(self, line_number: int) -> None:
        """
        특정 라인을 오류로 강조

        Args:
            line_number: 오류 라인 번호 (0 기준)
        """
        doc = self.document()
        if not doc:
            return

        block = doc.findBlockByLineNumber(line_number)
        if block.isValid():
            # 전체 라인에 오류 강조 적용
            self.setFormat(0, block.length(), self.error_format)
            logger.debug(f"라인 {line_number}에 오류 강조 적용")

    def clear_error_highlights(self) -> None:
        """모든 오류 강조 제거"""
        if self.document():
            self.rehighlight()
            # 🔥 로깅 최적화: 과도한 DEBUG 메시지 제거
            # logger.debug("모든 오류 강조 제거")  # 제거됨 - 너무 빈번하게 호출

    def _on_theme_changed(self, is_dark: bool) -> None:
        """
        테마 변경 이벤트 핸들러

        Args:
            is_dark: 다크 테마 여부
        """
        logger.info(f"테마 변경 감지: {'다크' if is_dark else '라이트'} 테마")
        self._update_colors_for_theme()
        self.rehighlight()  # 전체 문서 다시 강조

    def get_highlighting_info(self) -> dict:
        """구문 강조 정보 반환 (디버깅용)"""
        return {
            'rules_count': len(self.highlighting_rules),
            'is_dark_theme': self.theme_notifier.is_dark_theme(),
            'formats': {
                'key': self.key_format.foreground().color().name(),
                'value': self.value_format.foreground().color().name(),
                'string': self.string_format.foreground().color().name(),
                'comment': self.comment_format.foreground().color().name(),
                'number': self.number_format.foreground().color().name(),
                'boolean': self.boolean_format.foreground().color().name(),
                'null': self.null_format.foreground().color().name(),
                'separator': self.separator_format.foreground().color().name()
            }
        }
