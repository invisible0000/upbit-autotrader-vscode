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

# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)
from upbit_auto_trading.ui.desktop.common.theme_notifier import ThemeNotifier




class LogSyntaxHighlighter(QSyntaxHighlighter):
    """
    로그 구문 강조 클래스

    Infrastructure 로깅 시스템의 로그 포맷에 최적화:
    [TIMESTAMP] [LEVEL] [COMPONENT] MESSAGE
    """

    def __init__(self, parent: Optional[QTextDocument] = None, logging_service=None):
        super().__init__(parent)

        # 로깅 서비스 (선택적 - DDD 계층 준수)
        self.logger = logging_service

        # 테마 변경 알림 시스템 연결
        self.theme_notifier = ThemeNotifier()
        self.theme_notifier.theme_changed.connect(self._on_theme_changed)

        # 강조 규칙 저장
        self.highlighting_rules: List[Tuple[re.Pattern, QTextCharFormat]] = []

        # 문자 포맷 초기화
        self._init_formats()

        # 강조 규칙 설정
        self._setup_highlighting_rules()

        if self.logger:
            self.logger.debug("로그 구문 강조기 초기화 완료")

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
            self.timestamp_format.setForeground(QColor("#34D399"))    # 연한 초록 (타임스탬프)

            # 로그 레벨별 색상 (다크 테마)
            self.debug_format.setForeground(QColor("#FBBF24"))        # 노랑 (DEBUG)
            self.info_format.setForeground(QColor("#10B981"))         # 초록 (INFO)
            self.warning_format.setForeground(QColor("#F59E0B"))      # 앰버 (WARNING)
            self.error_format.setForeground(QColor("#EF4444"))        # 레드 (ERROR)
            self.critical_format.setForeground(QColor("#DC2626"))     # 진한 레드 (CRITICAL)
            self.critical_format.setFontWeight(QFont.Weight.Bold)

            self.component_format.setForeground(QColor("#60A5FA"))    # 파란 계열 (컴포넌트/로거)

            # 특별 메시지 색상
            self.success_format.setForeground(QColor("#98FB98"))      # 연두색
            self.failure_format.setForeground(QColor("#FF6B6B"))      # 라이트 레드
            self.warning_symbol_format.setForeground(QColor("#FFD700"))  # 골드
            self.info_symbol_format.setForeground(QColor("#87CEEB"))     # 스카이 블루

            self.bracket_format.setForeground(QColor("#D3D3D3"))      # 밝은 회색
            self.path_format.setForeground(QColor("#DDA0DD"))         # 플럼

        else:
            # 라이트 테마 색상
            self.timestamp_format.setForeground(QColor("#059669"))    # 초록 (타임스탬프)

            # 로그 레벨별 색상 (라이트 테마)
            self.debug_format.setForeground(QColor("#D97706"))        # 앰버/노랑 (DEBUG)
            self.info_format.setForeground(QColor("#16A34A"))         # 초록 (INFO)
            self.warning_format.setForeground(QColor("#F59E0B"))      # 앰버 (WARNING)
            self.error_format.setForeground(QColor("#DC2626"))        # 레드 (ERROR)
            self.critical_format.setForeground(QColor("#B91C1C"))     # 진한 레드 (CRITICAL)
            self.critical_format.setFontWeight(QFont.Weight.Bold)

            self.component_format.setForeground(QColor("#2563EB"))    # 파란 계열 (컴포넌트/로거)

            # 특별 메시지 색상
            self.success_format.setForeground(QColor("#228B22"))      # 포레스트 그린
            self.failure_format.setForeground(QColor("#DC143C"))      # 크림슨
            self.warning_symbol_format.setForeground(QColor("#FF8C00"))  # 다크 오렌지
            self.info_symbol_format.setForeground(QColor("#0066CC"))     # 블루

            self.bracket_format.setForeground(QColor("#666666"))      # 회색
            self.path_format.setForeground(QColor("#8B008B"))         # 다크 마젠타

        if self.logger:
            self.logger.debug(f"로그 하이라이터 테마 색상 업데이트 완료 (다크: {is_dark})")

    def _setup_highlighting_rules(self) -> None:
        """로그 구문 강조 규칙 설정"""
        self.highlighting_rules.clear()

        # 1. 타임스탬프 패턴 (다양한 형태 지원)
        timestamp_patterns = [
            # [YYYY-MM-DD HH:MM:SS], [YYYY-MM-DD HH:MM:SS,mmm], [YYYY-MM-DD HH:MM:SS.mmm]
            re.compile(r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:[\.,]\d{3})?\]'),
            # [HH:MM:SS], [HH:MM:SS,mmm], [HH:MM:SS.mmm]
            re.compile(r'\[\d{2}:\d{2}:\d{2}(?:[\.,]\d{3})?\]'),
            # YYYY-MM-DD HH:MM:SS(,mmm|.mmm)? (브라켓 없이)
            re.compile(r'\b\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:[\.,]\d{3})?\b'),
            # HH:MM:SS(,mmm|.mmm)? (브라켓 없이)
            re.compile(r'\b\d{2}:\d{2}:\d{2}(?:[\.,]\d{3})?\b'),
        ]
        for tp in timestamp_patterns:
            self.highlighting_rules.append((tp, self.timestamp_format))

        # 2. 로그 레벨 패턴 (브라켓 및 일반 토큰 모두 지원)
        level_specs = [
            (r'\[DEBUG\]', self.debug_format),
            (r'\bDEBUG\b', self.debug_format),
            (r'\[INFO\]', self.info_format),
            (r'\bINFO\b', self.info_format),
            (r'\[WARNING\]', self.warning_format),
            (r'\bWARNING\b', self.warning_format),
            (r'\[ERROR\]', self.error_format),
            (r'\bERROR\b', self.error_format),
            (r'\[CRITICAL\]', self.critical_format),
            (r'\bCRITICAL\b', self.critical_format),
        ]
        for patt, fmt in level_specs:
            self.highlighting_rules.append((re.compile(patt, re.IGNORECASE), fmt))

        # 3. 컴포넌트/로거명 패턴
        # - 대괄호로 둘러싼 컴포넌트 [Component]
        component_bracket_pattern = re.compile(
            r'\[(?!DEBUG|INFO|WARNING|ERROR|CRITICAL)([A-Za-z_][A-Za-z0-9_]*)\]'
        )
        self.highlighting_rules.append(
            (component_bracket_pattern, self.component_format)
        )
        # - 점 표기 로거명 upbit.SomeScreen (공백 또는 하이픈 전까지)
        dotted_logger_pattern = re.compile(
            r'\b(?:upbit|uvicorn|werkzeug|root)(?:\.[A-Za-z0-9_]+)+\b'
        )
        self.highlighting_rules.append(
            (dotted_logger_pattern, self.component_format)
        )

        # 4. 특별 메시지 이모지/기호 패턴
        success_pattern = re.compile(r'✅[^✅❌⚠️📊]*')
        failure_pattern = re.compile(r'❌[^✅❌⚠️📊]*')
        warning_symbol_pattern = re.compile(r'⚠️[^✅❌⚠️📊]*')
        info_symbol_pattern = re.compile(r'📊[^✅❌⚠️📊]*')

        # 4-b. STDOUT/STDERR 태그 패턴 (콘솔/로그 공통)
        stdout_tag = re.compile(r'\[STDOUT\]', re.IGNORECASE)
        stderr_tag = re.compile(r'\[STDERR\]', re.IGNORECASE)
        self.highlighting_rules.append((stdout_tag, self.info_format))
        self.highlighting_rules.append((stderr_tag, self.error_format))

        self.highlighting_rules.append((success_pattern, self.success_format))
        self.highlighting_rules.append((failure_pattern, self.failure_format))
        self.highlighting_rules.append(
            (warning_symbol_pattern, self.warning_symbol_format)
        )
        self.highlighting_rules.append(
            (info_symbol_pattern, self.info_symbol_format)
        )

        # 5. 파일 경로 패턴
        # 예: /path/to/file.py, C:\path\to\file.py
        path_pattern = re.compile(
            r'(?:[A-Za-z]:\\|/)(?:[\w\s.-][\\\\/])*[\w\s.-]+\.[\w]+'
        )
        self.highlighting_rules.append((path_pattern, self.path_format))

        # 6. 대괄호 구조 (일반)
        bracket_pattern = re.compile(r'[\[\]]')
        self.highlighting_rules.append((bracket_pattern, self.bracket_format))

        # 7. 중요한 키워드 강조 (한글과 영문을 분리해 경계 처리 개선)
        korean_keywords = [
            '시작됨', '시작중', '시작완료', '초기화완료', '초기화됨', '로딩완료',
            '완료됨', '처리완료', '생성완료', '연결완료', '설정완료',
            '실패함', '실패됨', '처리실패', '연결실패', '로드실패',
            '성공함', '성공됨', '처리성공', '연결성공', '생성성공',
            '에러발생', '오류발생',
            '경고발생', '주의사항',
            '초기화중', '종료중', '연결중', '해제중', '로드중', '저장중',
        ]
        english_keywords = [
            'started', 'starting', 'complete', 'completed', 'finished',
            'failed', 'failure', 'success', 'successful', 'error', 'warning',
            'initialized', 'initializing', 'loading', 'loaded', 'saving', 'saved'
        ]

        # 한글 키워드는 2글자 이상이고 앞뒤가 한글/영문/숫자/언더스코어가 아닌 경우만
        for keyword in korean_keywords:
            if len(keyword) >= 2:  # 2글자 이상만 매칭
                pattern = re.compile(
                    rf'(?<![가-힣A-Za-z0-9_]){re.escape(keyword)}(?![가-힣A-Za-z0-9_])'
                )
                if any(word in keyword for word in ['실패', '에러', '오류']):
                    fmt = self.failure_format
                elif any(word in keyword for word in ['성공', '완료']):
                    fmt = self.success_format
                elif any(word in keyword for word in ['경고', '주의']):
                    fmt = self.warning_symbol_format
                else:
                    fmt = self.info_format
                self.highlighting_rules.append((pattern, fmt))

        # 영문 키워드는 \\b 경계 사용
        for keyword in english_keywords:
            pattern = re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
            if keyword in ['failed', 'fail', 'error']:
                fmt = self.failure_format
            elif keyword in ['success', 'completed', 'complete']:
                fmt = self.success_format
            elif keyword in ['warning']:
                fmt = self.warning_symbol_format
            else:
                fmt = self.info_format
            self.highlighting_rules.append((pattern, fmt))

        if self.logger:
            self.logger.debug(
                f"로그 구문 강조 규칙 설정 완료: {len(self.highlighting_rules)}개 규칙"
            )

    def highlightBlock(self, text: Optional[str]) -> None:
        """
        텍스트 블록에 로그 구문 강조 적용

        Args:
            text: 강조할 로그 텍스트 라인 (None 가능)
        """
        if not text:
            return
        # 모든 강조 규칙 적용
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
        # 현재 블록 전체에 살짝 배경 적용 (가독성 높임)
        color = QColor(255, 0, 0, 30)  # 투명한 빨간 배경
        fmt = QTextCharFormat()
        fmt.setBackground(color)
        self.setFormat(0, len(text), fmt)

    def _on_theme_changed(self, is_dark: bool) -> None:
        """
        테마 변경 이벤트 핸들러

        Args:
            is_dark: 다크 테마 여부
        """
        if self.logger:
            self.logger.info(f"로그 하이라이터 테마 변경 감지: {'다크' if is_dark else '라이트'} 테마")
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
