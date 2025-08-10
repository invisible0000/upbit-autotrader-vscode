"""
Real-time Log Viewer Widget
===========================

실시간 로그 표시 위젯
Infrastructure Layer 로깅 시스템과 연동하여 실시간 로그 표시

Features:
- 실시간 로그 스트림 표시
- 로그 레벨별 색상 구분
- 자동 스크롤 및 수동 스크롤 지원
- 로그 필터링 (레벨별, 컴포넌트별)
- 로그 클리어 및 저장 기능
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QCheckBox, QComboBox, QLabel, QFrame, QSplitter
)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QTextCursor, QFont, QColor

from upbit_auto_trading.infrastructure.logging import create_component_logger


class LogViewerWidget(QWidget):
    """
    실시간 로그 뷰어 위젯

    Infrastructure 로깅 시스템의 출력을 실시간으로 표시
    """

    # 시그널 정의
    log_entry_received = pyqtSignal(str, str, str)  # (level, component, message)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("LogViewerWidget")

        # Infrastructure 로깅 초기화
        self._logger = create_component_logger("LogViewerWidget")

        # 로그 필터 상태
        self._show_debug = True
        self._show_info = True
        self._show_warning = True
        self._show_error = True
        self._component_filter = ""
        self._auto_scroll = True
        self._max_lines = 1000  # 최대 라인 수

        self._setup_ui()
        self._setup_log_handler()
        self._connect_signals()

        # 주기적 로그 업데이트
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_logs)
        self._update_timer.start(500)  # 500ms 마다 업데이트

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 제목
        title_label = QLabel("📺 실시간 로그")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 필터 컨트롤
        self._create_filter_controls(layout)

        # 로그 표시 영역
        self._create_log_display(layout)

        # 액션 버튼
        self._create_action_buttons(layout)

    def _create_filter_controls(self, parent_layout: QVBoxLayout):
        """필터 컨트롤 생성"""
        filter_frame = QFrame()
        filter_frame.setObjectName("log-filter-frame")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(4, 4, 4, 4)
        filter_layout.setSpacing(8)

        # 레벨 필터 체크박스
        self.debug_check = QCheckBox("DEBUG")
        self.debug_check.setChecked(self._show_debug)
        self.debug_check.setStyleSheet("color: #666;")

        self.info_check = QCheckBox("INFO")
        self.info_check.setChecked(self._show_info)
        self.info_check.setStyleSheet("color: #2196F3;")

        self.warning_check = QCheckBox("WARNING")
        self.warning_check.setChecked(self._show_warning)
        self.warning_check.setStyleSheet("color: #FF9800;")

        self.error_check = QCheckBox("ERROR")
        self.error_check.setChecked(self._show_error)
        self.error_check.setStyleSheet("color: #F44336;")

        filter_layout.addWidget(QLabel("레벨:"))
        filter_layout.addWidget(self.debug_check)
        filter_layout.addWidget(self.info_check)
        filter_layout.addWidget(self.warning_check)
        filter_layout.addWidget(self.error_check)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        filter_layout.addWidget(line)

        # 자동 스크롤
        self.auto_scroll_check = QCheckBox("자동 스크롤")
        self.auto_scroll_check.setChecked(self._auto_scroll)
        filter_layout.addWidget(self.auto_scroll_check)

        filter_layout.addStretch()

        parent_layout.addWidget(filter_frame)

    def _create_log_display(self, parent_layout: QVBoxLayout):
        """로그 표시 영역"""
        self.log_text = QTextEdit()
        self.log_text.setObjectName("log-display")
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        self.log_text.setMaximumHeight(300)

        # 폰트 설정 (모노스페이스)
        font = QFont("Consolas", 9)
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.log_text.setFont(font)

        # 스타일 설정
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 8px;
            }
        """)

        parent_layout.addWidget(self.log_text)

    def _create_action_buttons(self, parent_layout: QVBoxLayout):
        """액션 버튼들"""
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 4, 0, 0)

        # 클리어 버튼
        self.clear_btn = QPushButton("🗑️ 클리어")
        self.clear_btn.setObjectName("secondary-button")
        self.clear_btn.setMaximumWidth(80)

        # 저장 버튼
        self.save_btn = QPushButton("💾 저장")
        self.save_btn.setObjectName("secondary-button")
        self.save_btn.setMaximumWidth(80)

        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()

        parent_layout.addWidget(button_frame)

    def _setup_log_handler(self):
        """로그 핸들러 설정"""
        # Python 로깅 시스템에 커스텀 핸들러 추가
        self._log_handler = LogViewerHandler(self)
        self._log_handler.setLevel(logging.DEBUG)

        # Infrastructure 로깅에 연결
        # 실제로는 Infrastructure 로깅 서비스의 핸들러에 연결해야 함
        root_logger = logging.getLogger('upbit_auto_trading')
        root_logger.addHandler(self._log_handler)

    def _connect_signals(self):
        """시그널 연결"""
        # 필터 변경
        self.debug_check.toggled.connect(lambda checked: setattr(self, '_show_debug', checked))
        self.info_check.toggled.connect(lambda checked: setattr(self, '_show_info', checked))
        self.warning_check.toggled.connect(lambda checked: setattr(self, '_show_warning', checked))
        self.error_check.toggled.connect(lambda checked: setattr(self, '_show_error', checked))

        # 자동 스크롤
        self.auto_scroll_check.toggled.connect(lambda checked: setattr(self, '_auto_scroll', checked))

        # 액션 버튼
        self.clear_btn.clicked.connect(self._clear_logs)
        self.save_btn.clicked.connect(self._save_logs)

    def _update_logs(self):
        """로그 업데이트 (주기적 호출)"""
        # 실제로는 Infrastructure 로깅 서비스에서 새 로그를 가져와야 함
        pass

    def add_log_entry(self, level: str, component: str, message: str):
        """로그 엔트리 추가"""
        # 필터 검사
        if not self._should_show_log(level):
            return

        # 색상 결정
        color = self._get_level_color(level)

        # 타임스탬프 추가
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 포맷팅
        formatted_entry = f"[{timestamp}] [{level:>7}] [{component:>15}] {message}"

        # 텍스트 추가
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 색상 적용
        cursor.insertHtml(f'<span style="color: {color};">{formatted_entry}</span><br>')

        # 자동 스크롤
        if self._auto_scroll:
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )

        # 최대 라인 수 제한
        self._limit_lines()

    def _should_show_log(self, level: str) -> bool:
        """로그 표시 여부 결정"""
        level_map = {
            'DEBUG': self._show_debug,
            'INFO': self._show_info,
            'WARNING': self._show_warning,
            'ERROR': self._show_error,
            'CRITICAL': self._show_error
        }
        return level_map.get(level, True)

    def _get_level_color(self, level: str) -> str:
        """로그 레벨별 색상 반환"""
        colors = {
            'DEBUG': '#666666',
            'INFO': '#2196F3',
            'WARNING': '#FF9800',
            'ERROR': '#F44336',
            'CRITICAL': '#D32F2F'
        }
        return colors.get(level, '#d4d4d4')

    def _limit_lines(self):
        """최대 라인 수 제한"""
        if self.log_text.document().lineCount() > self._max_lines:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down,
                               QTextCursor.MoveMode.KeepAnchor, 100)
            cursor.removeSelectedText()

    def _clear_logs(self):
        """로그 클리어"""
        self.log_text.clear()
        self._logger.info("📺 로그 뷰어 클리어됨")

    def _save_logs(self):
        """로그 저장 (미구현)"""
        self._logger.info("💾 로그 저장 기능 준비중")


class LogViewerHandler(logging.Handler):
    """
    LogViewerWidget을 위한 커스텀 로깅 핸들러
    """

    def __init__(self, log_viewer: LogViewerWidget):
        super().__init__()
        self.log_viewer = log_viewer

    def emit(self, record):
        """로그 레코드 처리"""
        try:
            # 컴포넌트 이름 추출
            component = getattr(record, 'component', record.name)

            # 로그 뷰어에 추가
            self.log_viewer.add_log_entry(
                record.levelname,
                component,
                record.getMessage()
            )
        except Exception:
            # 로깅 에러는 무시 (무한 루프 방지)
            pass
