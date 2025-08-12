"""
실시간 로깅 관리 탭 - MVP Passive View
====================================

DDD Presentation Layer - PyQt6 UI (표시만, Passive View)
Infrastructure Layer 로깅 시스템과 통합된 실시간 로그 관리 UI

주요 특징:
- MVP 패턴 Passive View (순수 UI 관심사만)
- 3-위젯 구조: 좌측 설정 | 우측 상단 로그뷰어 | 우측 하단 콘솔뷰어
- Config 파일 기반 설정 시스템 (환경변수 시스템 대체)
- 전역 스타일 관리 시스템 준수
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt, pyqtSignal

# 3개 위젯 컴포넌트 임포트
from .widgets.logging_settings_widget import LoggingSettingsWidget
from .widgets.log_viewer_widget import LogViewerWidget
from .widgets.console_viewer_widget import ConsoleViewerWidget

class LoggingManagementView(QWidget):
    """실시간 로깅 관리 탭 - MVP Passive View with 3-Widget Architecture"""

    # 시그널 정의 (Presenter로 전달용)
    settings_changed = pyqtSignal(dict)  # 설정 변경 시그널
    apply_settings_requested = pyqtSignal()  # 설정 적용 요청
    reset_settings_requested = pyqtSignal()  # 설정 리셋 요청

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """3-위젯 아키텍처 UI 레이아웃 구성"""
        layout = QVBoxLayout()

        # 메인 수평 스플리터 (좌측:우측 = 1:2)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 좌측: 로깅 설정 위젯
        self.logging_settings_widget = LoggingSettingsWidget()

        # 우측: 수직 스플리터 (상단:하단 = 2:1)
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)

        # 우측 상단: 로그 뷰어 위젯
        self.log_viewer_widget = LogViewerWidget()

        # 우측 하단: 콘솔 뷰어 위젯
        self.console_viewer_widget = ConsoleViewerWidget()

        # 우측 스플리터에 위젯 추가
        self.right_splitter.addWidget(self.log_viewer_widget)
        self.right_splitter.addWidget(self.console_viewer_widget)
        self.right_splitter.setSizes([600, 300])  # 2:1 비율

        # 메인 스플리터에 추가
        self.main_splitter.addWidget(self.logging_settings_widget)
        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setSizes([300, 600])  # 1:2 비율

        layout.addWidget(self.main_splitter)
        self.setLayout(layout)

    def _connect_signals(self):
        """위젯 간 시그널 연결"""
        # 로깅 설정 위젯의 시그널을 메인 뷰로 릴레이
        self.logging_settings_widget.settings_changed.connect(self.settings_changed.emit)
        self.logging_settings_widget.apply_requested.connect(self.apply_settings_requested.emit)
        self.logging_settings_widget.reset_requested.connect(self.reset_settings_requested.emit)

    def _create_control_panel(self) -> QWidget:
        """환경변수 제어 패널 - Infrastructure 로깅 시스템 연동"""
        panel = QWidget()
        layout = QVBoxLayout()

        # 1. 로그 레벨 제어 그룹
        log_level_group = QGroupBox("로그 레벨 제어")
        log_level_layout = QVBoxLayout()

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("INFO")  # 기본값

        log_level_layout.addWidget(QLabel("UPBIT_LOG_LEVEL:"))
        log_level_layout.addWidget(self.log_level_combo)
        log_level_group.setLayout(log_level_layout)

        # 2. 출력 제어 그룹
        output_group = QGroupBox("출력 제어")
        output_layout = QVBoxLayout()

        self.console_output_checkbox = QCheckBox("콘솔 출력 활성화")
        self.console_output_checkbox.setChecked(True)  # 기본값

        output_layout.addWidget(self.console_output_checkbox)
        output_group.setLayout(output_layout)

        # 3. 로깅 스코프 그룹 (Infrastructure 로깅 시스템 v4.0)
        scope_group = QGroupBox("로깅 스코프")
        scope_layout = QVBoxLayout()

        self.log_scope_combo = QComboBox()
        self.log_scope_combo.addItems(["silent", "minimal", "normal", "verbose", "debug_all"])
        self.log_scope_combo.setCurrentText("normal")  # 기본값

        scope_layout.addWidget(QLabel("UPBIT_LOG_SCOPE:"))
        scope_layout.addWidget(self.log_scope_combo)
        scope_group.setLayout(scope_layout)

        # 4. 컴포넌트 집중 모드
        focus_group = QGroupBox("컴포넌트 집중")
        focus_layout = QVBoxLayout()

        self.component_focus_edit = QLineEdit()
        self.component_focus_edit.setPlaceholderText("컴포넌트명 입력 (비어두면 모든 컴포넌트)")

        focus_layout.addWidget(QLabel("UPBIT_COMPONENT_FOCUS:"))
        focus_layout.addWidget(self.component_focus_edit)
        focus_group.setLayout(focus_layout)

        # 5. 로깅 컨텍스트 그룹
        context_group = QGroupBox("로깅 컨텍스트")
        context_layout = QVBoxLayout()

        self.log_context_combo = QComboBox()
        self.log_context_combo.addItems(["development", "testing", "staging", "production"])
        self.log_context_combo.setCurrentText("development")  # 기본값

        context_layout.addWidget(QLabel("UPBIT_LOG_CONTEXT:"))
        context_layout.addWidget(self.log_context_combo)
        context_group.setLayout(context_layout)

        # 🆕 6. 파일 로깅 설정 그룹
        file_group = QGroupBox("파일 로깅 설정")
        file_layout = QVBoxLayout()

        # 파일 로깅 활성화
        self.file_logging_checkbox = QCheckBox("파일 로깅 활성화")
        self.file_logging_checkbox.setChecked(True)  # 기본값

        # 파일 경로
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setText("logs/upbit_auto_trading.log")
        self.file_path_edit.setPlaceholderText("로그 파일 경로")

        # 파일 로그 레벨
        self.file_level_combo = QComboBox()
        self.file_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.file_level_combo.setCurrentText("DEBUG")  # 기본값

        file_layout.addWidget(self.file_logging_checkbox)
        file_layout.addWidget(QLabel("파일 경로:"))
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(QLabel("파일 로그 레벨:"))
        file_layout.addWidget(self.file_level_combo)
        file_group.setLayout(file_layout)

        # 7. 제어 버튼
        button_layout = QHBoxLayout()
        self.apply_btn = QPushButton("설정 적용")
        self.reset_btn = QPushButton("기본값 복원")

        # 전역 스타일 적용을 위한 objectName 설정
        self.apply_btn.setObjectName("primary_button")
        self.reset_btn.setObjectName("secondary_button")

        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.reset_btn)

        # 레이아웃 조립
        layout.addWidget(log_level_group)
        layout.addWidget(output_group)
        layout.addWidget(scope_group)
        layout.addWidget(focus_group)
        layout.addWidget(context_group)  # 🆕 로깅 컨텍스트 그룹 추가
        layout.addWidget(file_group)  # 🆕 파일 로깅 설정 그룹 추가
        layout.addLayout(button_layout)
        layout.addStretch()  # 하단 여백

        panel.setLayout(layout)
        return panel

    def _create_log_viewer(self) -> QWidget:
        """로그 뷰어 패널 - 실시간 로그 표시"""
        viewer_widget = QWidget()
        layout = QVBoxLayout()

        # 툴바
        toolbar = QHBoxLayout()

        # 자동 스크롤 토글
        self.auto_scroll_checkbox = QCheckBox("자동 스크롤")
        self.auto_scroll_checkbox.setChecked(True)

        # 로그 필터 (Phase 2에서 구현)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("로그 필터링 (정규식 지원)")
        self.filter_edit.setEnabled(False)  # Phase 1에서는 비활성화

        # 제어 버튼
        self.clear_btn = QPushButton("로그 지우기")
        self.save_btn = QPushButton("로그 저장")

        # 전역 스타일 적용
        self.clear_btn.setObjectName("warning_button")
        self.save_btn.setObjectName("secondary_button")

        toolbar.addWidget(self.auto_scroll_checkbox)
        toolbar.addWidget(QLabel("필터:"))
        toolbar.addWidget(self.filter_edit)
        toolbar.addWidget(self.clear_btn)
        toolbar.addWidget(self.save_btn)
        toolbar.addStretch()

        # 메인 로그 뷰어 (세션 로그 파일 내용, 상단 2/3)
        self.log_text_edit = QPlainTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.log_text_edit.setMaximumBlockCount(1000)  # 1000줄 제한
        self.log_text_edit.setUndoRedoEnabled(False)  # 메모리 절약
        self.log_text_edit.setObjectName("log_viewer")

        # 콘솔 출력 뷰어 (터미널 콘솔 출력, 하단 1/3)
        self.console_text_edit = QPlainTextEdit()
        self.console_text_edit.setReadOnly(True)
        self.console_text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.console_text_edit.setMaximumBlockCount(1000)  # 1000줄 제한
        self.console_text_edit.setUndoRedoEnabled(False)  # 메모리 절약
        self.console_text_edit.setObjectName("console_viewer")
        self.console_text_edit.setPlaceholderText("콘솔 출력이 여기에 표시됩니다...")

        # 모노스페이스 폰트 설정 (두 뷰어 모두)
        font = QFont("Consolas", 9)
        if not font.exactMatch():
            font = QFont("Courier New", 9)  # 폴백 폰트
        font.setFixedPitch(True)

        # 두 뷰어 모두에 폰트 적용
        self.log_text_edit.setFont(font)
        self.console_text_edit.setFont(font)

        # 초기 메시지는 Presenter에서 설정됨 (하드코딩 제거)

        # 상태바
        status_layout = QHBoxLayout()
        self.log_count_label = QLabel("로그 개수: 0")
        self.filter_count_label = QLabel("필터링됨: 0")

        status_layout.addWidget(self.log_count_label)
        status_layout.addWidget(self.filter_count_label)
        status_layout.addStretch()

        # 로그 뷰어 영역 (상단 2/3 + 하단 1/3 splitter)
        log_splitter = QSplitter(Qt.Orientation.Vertical)

        # 세션 로그 파일 뷰어 영역
        log_file_widget = QWidget()
        log_file_layout = QVBoxLayout()
        log_file_layout.addWidget(QLabel("📄 세션 로그 파일"))
        log_file_layout.addWidget(self.log_text_edit)
        log_file_widget.setLayout(log_file_layout)

        # 콘솔 출력 뷰어 영역
        console_widget = QWidget()
        console_layout = QVBoxLayout()
        console_layout.addWidget(QLabel("💻 콘솔 출력"))
        console_layout.addWidget(self.console_text_edit)
        console_widget.setLayout(console_layout)

        # Splitter에 추가 (2:1 비율)
        log_splitter.addWidget(log_file_widget)
        log_splitter.addWidget(console_widget)
        log_splitter.setSizes([600, 300])  # 2:1 비율 (총 900 기준)
        log_splitter.setStretchFactor(0, 2)  # 상단 영역이 더 큰 비중
        log_splitter.setStretchFactor(1, 1)  # 하단 영역

        # 레이아웃 조립
        layout.addLayout(toolbar)
        layout.addWidget(log_splitter)
        layout.addLayout(status_layout)

        viewer_widget.setLayout(layout)
        return viewer_widget

    # ===== MVP Passive View 인터페이스 =====

    def append_log(self, log_text: str):
        """세션 로그 파일 내용 추가 (Presenter에서 호출)"""
        self.log_text_edit.appendPlainText(log_text)
        self._update_status()

    def append_console(self, console_text: str):
        """콘솔 출력 추가 (Presenter에서 호출)"""
        self.console_text_edit.appendPlainText(console_text)
        self._update_status()

    def append_log_batch(self, log_texts: list):
        """배치 로그 추가 (성능 최적화용)

        Args:
            log_texts: 추가할 로그 메시지 리스트
        """
        if not log_texts:
            return

        # 배치로 한번에 추가하여 UI 업데이트 최소화
        combined_text = '\n'.join(log_texts)
        self.log_text_edit.appendPlainText(combined_text)
        self._update_status()

    def clear_logs(self):
        """세션 로그 파일 뷰어 클리어 (Presenter에서 호출)"""
        self.log_text_edit.clear()
        self._update_status()

    def clear_console(self):
        """콘솔 출력 뷰어 클리어 (Presenter에서 호출)"""
        self.console_text_edit.clear()
        self._update_status()

    def clear_all(self):
        """모든 뷰어 클리어 (Presenter에서 호출)"""
        self.log_text_edit.clear()
        self.console_text_edit.clear()
        self._update_status()

    def get_log_level(self) -> str:
        """선택된 로그 레벨 반환"""
        return self.log_level_combo.currentText()

    def get_console_output_enabled(self) -> bool:
        """콘솔 출력 활성화 여부"""
        return self.console_output_checkbox.isChecked()

    def get_log_scope(self) -> str:
        """선택된 로그 스코프 반환"""
        return self.log_scope_combo.currentText()

    def get_component_focus(self) -> str:
        """컴포넌트 집중 모드 값 반환"""
        return self.component_focus_edit.text().strip()

    def get_log_context(self) -> str:
        """로깅 컨텍스트 값 반환"""
        return self.log_context_combo.currentText()

    def set_log_level(self, level: str):
        """로그 레벨 설정 (환경변수 동기화용)"""
        index = self.log_level_combo.findText(level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)

    def set_console_output_enabled(self, enabled: bool):
        """콘솔 출력 설정 (환경변수 동기화용)"""
        self.console_output_checkbox.setChecked(enabled)

    def set_log_scope(self, scope: str):
        """로그 스코프 설정 (환경변수 동기화용)"""
        index = self.log_scope_combo.findText(scope)
        if index >= 0:
            self.log_scope_combo.setCurrentIndex(index)

    def set_component_focus(self, component: str):
        """컴포넌트 집중 설정 (환경변수 동기화용)"""
        self.component_focus_edit.setText(component)

    def set_log_context(self, context: str):
        """로깅 컨텍스트 설정 (환경변수 동기화용)"""
        index = self.log_context_combo.findText(context)
        if index >= 0:
            self.log_context_combo.setCurrentIndex(index)

    # 🆕 파일 로깅 설정 getter/setter 메서드들
    def get_file_logging_enabled(self) -> bool:
        """파일 로깅 활성화 여부"""
        return self.file_logging_checkbox.isChecked()

    def get_file_path(self) -> str:
        """파일 경로 반환"""
        return self.file_path_edit.text().strip()

    def get_file_level(self) -> str:
        """파일 로그 레벨 반환"""
        return self.file_level_combo.currentText()

    def set_file_logging_enabled(self, enabled: bool):
        """파일 로깅 활성화 설정"""
        self.file_logging_checkbox.setChecked(enabled)

    def set_file_path(self, path: str):
        """파일 경로 설정"""
        self.file_path_edit.setText(path)

    def set_file_level(self, level: str):
        """파일 로그 레벨 설정"""
        index = self.file_level_combo.findText(level)
        if index >= 0:
            self.file_level_combo.setCurrentIndex(index)

    def _update_status(self):
        """상태바 업데이트"""
        # 세션 로그 파일 라인 수 계산
        log_content = self.log_text_edit.toPlainText()
        log_lines = len(log_content.split('\n')) if log_content.strip() else 0

        # 콘솔 출력 라인 수 계산
        console_content = self.console_text_edit.toPlainText()
        console_lines = len(console_content.split('\n')) if console_content.strip() else 0

        self.log_count_label.setText(f"로그: {log_lines}줄 | 콘솔: {console_lines}줄")

        # 필터링은 Phase 2에서 구현
        filter_text = self.filter_edit.text().strip()
        if filter_text:
            self.filter_count_label.setText("필터링됨: 활성")
        else:
            self.filter_count_label.setText("필터링됨: 비활성")
