"""
로그 구문 강조기 (Log Syntax Highlighter)
========================================

로그 파일용 구문 강조 시스템
PyQt6 QSyntaxHighlighter 기반으로 구현

Features:
- 로그 레벨별 색상 구분 (DEBUG, INFO, WARNING, ERROR)
- 타임스탬프 강조
- 컴포넌트명 강조
- 에러 메시지 강조
- 테마 시스템 연동 (다크/라이트)
"""

import re
from typing import List, Tuple, Optional
from PyQt6.QtGui import (
    QSyntaxHighlighter, QTextDocument, QTextCharFormat,
    QFont, QColor
)

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.ui.desktop.common.theme_notifier import ThemeNotifier

logger = create_component_logger("LogSyntaxHighlighter")


class LogSyntaxHighlighter(QSyntaxHighlighter):
    """
    로그 구문 강조 클래스

    Infrastructure 로깅 시스템의 로그 포맷에 최적화:
    [TIMESTAMP] [LEVEL] [COMPONENT] MESSAGE
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

        logger.debug("로그 구문 강조기 초기화 완료")

    def _init_formats(self) -> None:
        """문자 포맷 객체들 초기화"""
        # 타임스탬프 포맷
        self.timestamp_format = QTextCharFormat()

        # 로그 레벨별 포맷
        self.debug_format = QTextCharFormat()
        self.info_format = QTextCharFormat()
        self.warning_format = QTextCharFormat()
        self.error_format = QTextCharFormat()
        self.critical_format = QTextCharFormat()

        # 컴포넌트명 포맷
        self.component_format = QTextCharFormat()
        self.component_format.setFontWeight(QFont.Weight.Bold)

        # 특별 메시지 포맷
        self.success_format = QTextCharFormat()  # ✅ 성공 메시지
        self.failure_format = QTextCharFormat()  # ❌ 실패 메시지
        self.warning_symbol_format = QTextCharFormat()  # ⚠️  경고 메시지
        self.info_symbol_format = QTextCharFormat()  # 📊 정보 메시지

        # 대괄호 포맷 (구조 표시)
        self.bracket_format = QTextCharFormat()

        # 파일 경로 포맷
        self.path_format = QTextCharFormat()
        self.path_format.setFontItalic(True)

        # 테마에 따른 색상 설정
        self._update_colors_for_theme()

    def _update_colors_for_theme(self) -> None:
        """현재 테마에 맞는 색상으로 업데이트"""
        is_dark = self.theme_notifier.is_dark_theme()

        if is_dark:
            # 다크 테마 색상
            self.timestamp_format.setForeground(QColor("#B0B0B0"))    # 밝은 회색

            # 로그 레벨별 색상 (다크 테마)
            self.debug_format.setForeground(QColor("#A0A0A0"))        # 회색
            self.info_format.setForeground(QColor("#87CEEB"))         # 스카이 블루
            self.warning_format.setForeground(QColor("#FFD700"))      # 골드
            self.error_format.setForeground(QColor("#FF6B6B"))        # 라이트 레드
            self.critical_format.setForeground(QColor("#FF4444"))     # 레드
            self.critical_format.setFontWeight(QFont.Weight.Bold)

            self.component_format.setForeground(QColor("#90EE90"))    # 라이트 그린

            # 특별 메시지 색상
            self.success_format.setForeground(QColor("#98FB98"))      # 연두색
            self.failure_format.setForeground(QColor("#FF6B6B"))      # 라이트 레드
            self.warning_symbol_format.setForeground(QColor("#FFD700"))  # 골드
            self.info_symbol_format.setForeground(QColor("#87CEEB"))     # 스카이 블루

            self.bracket_format.setForeground(QColor("#D3D3D3"))      # 밝은 회색
            self.path_format.setForeground(QColor("#DDA0DD"))         # 플럼

        else:
            # 라이트 테마 색상
            self.timestamp_format.setForeground(QColor("#666666"))    # 회색

            # 로그 레벨별 색상 (라이트 테마)
            self.debug_format.setForeground(QColor("#808080"))        # 회색
            self.info_format.setForeground(QColor("#0066CC"))         # 블루
            self.warning_format.setForeground(QColor("#FF8C00"))      # 다크 오렌지
            self.error_format.setForeground(QColor("#DC143C"))        # 크림슨
            self.critical_format.setForeground(QColor("#B22222"))     # 파이어 브릭
            self.critical_format.setFontWeight(QFont.Weight.Bold)

            self.component_format.setForeground(QColor("#228B22"))    # 포레스트 그린

            # 특별 메시지 색상
            self.success_format.setForeground(QColor("#228B22"))      # 포레스트 그린
            self.failure_format.setForeground(QColor("#DC143C"))      # 크림슨
            self.warning_symbol_format.setForeground(QColor("#FF8C00"))  # 다크 오렌지
            self.info_symbol_format.setForeground(QColor("#0066CC"))     # 블루

            self.bracket_format.setForeground(QColor("#666666"))      # 회색
            self.path_format.setForeground(QColor("#8B008B"))         # 다크 마젠타

        logger.debug(f"로그 하이라이터 테마 색상 업데이트 완료 (다크: {is_dark})")

    def _setup_highlighting_rules(self) -> None:
        """로그 구문 강조 규칙 설정"""
        self.highlighting_rules.clear()

        # 1. 타임스탬프 패턴 (Infrastructure 로깅 시스템 형식)
        # 예: [2025-08-12 14:30:45,123]
        timestamp_pattern = re.compile(r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}\]')
        self.highlighting_rules.append((timestamp_pattern, self.timestamp_format))

        # 2. 로그 레벨 패턴
        debug_pattern = re.compile(r'\[DEBUG\]', re.IGNORECASE)
        info_pattern = re.compile(r'\[INFO\]', re.IGNORECASE)
        warning_pattern = re.compile(r'\[WARNING\]', re.IGNORECASE)
        error_pattern = re.compile(r'\[ERROR\]', re.IGNORECASE)
        critical_pattern = re.compile(r'\[CRITICAL\]', re.IGNORECASE)

        self.highlighting_rules.append((debug_pattern, self.debug_format))
        self.highlighting_rules.append((info_pattern, self.info_format))
        self.highlighting_rules.append((warning_pattern, self.warning_format))
        self.highlighting_rules.append((error_pattern, self.error_format))
        self.highlighting_rules.append((critical_pattern, self.critical_format))

        # 3. 컴포넌트명 패턴
        # 예: [ComponentName]
        component_pattern = re.compile(r'\[([A-Za-z_][A-Za-z0-9_]*)\]')
        self.highlighting_rules.append((component_pattern, self.component_format))

        # 4. 특별 메시지 이모지/기호 패턴
        success_pattern = re.compile(r'✅[^✅❌⚠️📊]*')
        failure_pattern = re.compile(r'❌[^✅❌⚠️📊]*')
        warning_symbol_pattern = re.compile(r'⚠️[^✅❌⚠️📊]*')
        info_symbol_pattern = re.compile(r'📊[^✅❌⚠️📊]*')

        self.highlighting_rules.append((success_pattern, self.success_format))
        self.highlighting_rules.append((failure_pattern, self.failure_format))
        self.highlighting_rules.append((warning_symbol_pattern, self.warning_symbol_format))
        self.highlighting_rules.append((info_symbol_pattern, self.info_symbol_format))

        # 5. 파일 경로 패턴
        # 예: /path/to/file.py, C:\path\to\file.py
        path_pattern = re.compile(r'(?:[A-Za-z]:\\|/)(?:[\w\s.-][\\\\/])*[\w\s.-]+\.[\w]+')
        self.highlighting_rules.append((path_pattern, self.path_format))

        # 6. 대괄호 구조 (일반)
        bracket_pattern = re.compile(r'[\[\]]')
        self.highlighting_rules.append((bracket_pattern, self.bracket_format))

        # 7. 중요한 키워드 강조
        important_keywords = [
            '시작', '완료', '실패', '성공', '에러', '경고',
            '초기화', '종료', '연결', '해제', '로드', '저장',
            'started', 'completed', 'failed', 'success', 'error', 'warning'
        ]

        for keyword in important_keywords:
            keyword_pattern = re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
            # 키워드별로 적절한 포맷 선택
            if keyword in ['실패', 'failed', '에러', 'error']:
                format_to_use = self.failure_format
            elif keyword in ['성공', 'success', '완료', 'completed']:
                format_to_use = self.success_format
            elif keyword in ['경고', 'warning']:
                format_to_use = self.warning_symbol_format
            else:
                format_to_use = self.info_format

            self.highlighting_rules.append((keyword_pattern, format_to_use))

        logger.debug(f"로그 구문 강조 규칙 설정 완료: {len(self.highlighting_rules)}개 규칙")

    def highlightBlock(self, text: Optional[str]) -> None:
        """
        텍스트 블록에 로그 구문 강조 적용

        Args:
            text: 강조할 로그 텍스트 라인 (None 가능)
        """
        if not text:
            return        # 모든 강조 규칙 적용
        for pattern, char_format in self.highlighting_rules:
            # 컴포넌트 패턴은 그룹 1만 강조 (대괄호 제외하고 컴포넌트명만)
            if pattern.pattern == r'\[([A-Za-z_][A-Za-z0-9_]*)\]':
                for match in pattern.finditer(text):
                    # 그룹 1 (컴포넌트명)만 강조
                    start = match.start(1)
                    end = match.end(1)
                    self.setFormat(start, end - start, char_format)
            else:
                # 일반 패턴들
                for match in pattern.finditer(text):
                    start, end = match.span()
                    self.setFormat(start, end - start, char_format)

        # 전체 라인이 에러 레벨이면 라인 전체를 약간 강조
        if re.search(r'\[ERROR\]|\[CRITICAL\]', text, re.IGNORECASE):
            self._highlight_error_line(text)

    def _highlight_error_line(self, text: str) -> None:
        """에러 라인 전체를 미묘하게 강조"""
        # 배경색 설정은 필요시 구현 (현재는 텍스트 색상만 사용)
        pass

    def _on_theme_changed(self, is_dark: bool) -> None:
        """
        테마 변경 이벤트 핸들러

        Args:
            is_dark: 다크 테마 여부
        """
        logger.info(f"로그 하이라이터 테마 변경 감지: {'다크' if is_dark else '라이트'} 테마")
        self._update_colors_for_theme()
        self.rehighlight()  # 전체 문서 다시 강조

    def get_highlighting_info(self) -> dict:
        """구문 강조 정보 반환 (디버깅용)"""
        return {
            'rules_count': len(self.highlighting_rules),
            'is_dark_theme': self.theme_notifier.is_dark_theme(),
            'log_levels_supported': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            'special_symbols_supported': ['✅', '❌', '⚠️', '📊'],
            'formats': {
                'timestamp': self.timestamp_format.foreground().color().name(),
                'debug': self.debug_format.foreground().color().name(),
                'info': self.info_format.foreground().color().name(),
                'warning': self.warning_format.foreground().color().name(),
                'error': self.error_format.foreground().color().name(),
                'critical': self.critical_format.foreground().color().name(),
                'component': self.component_format.foreground().color().name(),
                'success': self.success_format.foreground().color().name(),
                'failure': self.failure_format.foreground().color().name(),
            }
        }
