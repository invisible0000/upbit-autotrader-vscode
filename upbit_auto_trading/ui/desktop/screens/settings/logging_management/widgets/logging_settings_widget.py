"""
로깅 설정 위젯

좌측 패널에 위치하는 로깅 설정 컨트롤들을 담당합니다.
- 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- 콘솔 출력 토글
- 로그 스코프 설정 (silent, minimal, normal, verbose, debug_all)
- 파일 로깅 설정
- 컴포넌트 집중 설정
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QCheckBox, QLineEdit, QGroupBox,
    QFormLayout, QSpinBox, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger

# 컴포넌트 선택 다이얼로그 (안전한 import)
try:
    from ..dialogs import ComponentSelectorDialog, DIALOGS_AVAILABLE
except ImportError:
    ComponentSelectorDialog = None
    DIALOGS_AVAILABLE = False


class LoggingSettingsWidget(QWidget):
    """로깅 설정 위젯 - 좌측 패널"""

    # 시그널 정의
    log_level_changed = pyqtSignal(str)         # 로그 레벨 변경
    console_output_changed = pyqtSignal(str)    # 콘솔 출력 변경
    log_scope_changed = pyqtSignal(str)         # 로그 스코프 변경
    context_changed = pyqtSignal(str)           # 실행 환경 변경
    component_focus_changed = pyqtSignal(str)   # 컴포넌트 집중 변경
    file_logging_changed = pyqtSignal(bool)     # 파일 로깅 토글
    file_log_level_changed = pyqtSignal(str)    # 파일 로그 레벨 변경
    file_path_changed = pyqtSignal(str)         # 파일 경로 변경
    performance_monitoring_changed = pyqtSignal(bool)  # 성능 모니터링 변경
    apply_settings = pyqtSignal()               # 설정 적용
    reset_settings = pyqtSignal()               # 설정 초기화

    def __init__(self, parent=None):
        """초기화"""
        super().__init__(parent)
        self.setObjectName("logging-settings-widget")

        # 로깅
        self.logger = create_component_logger("LoggingSettingsWidget")
        self.logger.info("🔧 로깅 설정 위젯 초기화 시작")

        # 내부 상태
        self._is_loading = False

        # UI 구성
        self._setup_ui()
        self._connect_signals()

        self.logger.info("✅ 로깅 설정 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 1. 기본 로깅 설정
        basic_group = self._create_basic_logging_group()
        layout.addWidget(basic_group)

        # 2. 고급 설정
        advanced_group = self._create_advanced_settings_group()
        layout.addWidget(advanced_group)

        # 3. 파일 로깅 설정
        file_group = self._create_file_logging_group()
        layout.addWidget(file_group)

        # 4. 액션 버튼
        action_layout = self._create_action_buttons()
        layout.addLayout(action_layout)

        # 스트레치 추가 (위젯을 상단에 고정)
        layout.addStretch()

    def _create_basic_logging_group(self) -> QGroupBox:
        """기본 로깅 설정 그룹 생성"""
        group = QGroupBox("기본 로깅 설정")
        layout = QFormLayout(group)

        # 실행 환경 선택
        self.context_combo = QComboBox()
        self.context_combo.addItems([
            "development - 개발 환경",
            "production - 운영 환경",
            "testing - 테스트 환경",
            "staging - 스테이징 환경",
            "debug - 디버그 환경",
            "demo - 데모 환경"
        ])
        self.context_combo.setCurrentText("development - 개발 환경")
        layout.addRow("실행 환경:", self.context_combo)

        # 로그 레벨 선택
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems([
            "DEBUG - 상세 디버그 정보",
            "INFO - 일반 정보",
            "WARNING - 경고",
            "ERROR - 오류",
            "CRITICAL - 치명적 오류"
        ])
        self.log_level_combo.setCurrentText("INFO - 일반 정보")
        layout.addRow("로그 레벨:", self.log_level_combo)

        # 콘솔 출력 설정
        self.console_output_combo = QComboBox()
        self.console_output_combo.addItems([
            "true - 항상 출력",
            "false - 출력 안함",
            "auto - 오류시만"
        ])
        self.console_output_combo.setCurrentText("false - 출력 안함")
        layout.addRow("콘솔 출력:", self.console_output_combo)

        # 로그 스코프 선택
        self.log_scope_combo = QComboBox()
        self.log_scope_combo.addItems([
            "silent - 최소 출력",
            "minimal - 핵심만",
            "normal - 일반",
            "verbose - 상세",
            "debug_all - 모든 디버그"
        ])
        self.log_scope_combo.setCurrentText("normal - 일반")
        layout.addRow("로그 범위:", self.log_scope_combo)

        return group

    def _create_advanced_settings_group(self) -> QGroupBox:
        """고급 설정 그룹 생성"""
        group = QGroupBox("고급 설정")
        layout = QVBoxLayout(group)

        # 컴포넌트 집중 설정 영역
        focus_frame = QFrame()
        focus_layout = QFormLayout(focus_frame)

        # 선택된 컴포넌트 표시용 입력 필드
        self.component_focus_edit = QLineEdit()
        self.component_focus_edit.setText("")  # 초기에는 빈 값
        self.component_focus_edit.setPlaceholderText("선택된 컴포넌트가 여기에 표시됩니다")

        # 버튼 레이아웃
        button_layout = QHBoxLayout()

        # 컴포넌트 선택 버튼
        if DIALOGS_AVAILABLE:
            select_button = QPushButton("컴포넌트 선택...")
            select_button.clicked.connect(self._on_select_component)
            select_button.setToolTip("프로젝트의 컴포넌트를 탐색하여 선택합니다")
        else:
            # 다이얼로그 사용 불가 시 폴백
            select_button = QPushButton("수동 입력")
            select_button.setEnabled(False)
            select_button.setToolTip("컴포넌트 선택 다이얼로그를 사용할 수 없습니다. 직접 입력해주세요.")

        # 지우기 버튼
        clear_button = QPushButton("지우기")
        clear_button.clicked.connect(self._on_clear_component_focus)
        clear_button.setToolTip("컴포넌트 포커스를 해제합니다")

        button_layout.addWidget(select_button)
        button_layout.addWidget(clear_button)
        button_layout.addStretch()

        # 레이아웃 구성
        focus_layout.addRow("컴포넌트 집중:", self.component_focus_edit)

        # 컴포넌트 버튼과 헬프 버튼을 함께 배치
        button_help_layout = QHBoxLayout()
        button_help_layout.addLayout(button_layout)

        # 컴포넌트 집중 헬프 버튼
        component_help_button = QPushButton("?")
        component_help_button.setFixedSize(20, 20)
        component_help_button.setStyleSheet("""
            QPushButton {
                padding: 0px;
                margin: 0px;
                border: 1px solid gray;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: lightblue;
            }
        """)
        component_help_button.setToolTip("컴포넌트 집중 기능에 대한 상세 설명을 보려면 클릭하세요")
        component_help_button.clicked.connect(self._on_component_focus_help)

        # 우측 정렬을 위해 addStretch()를 먼저 하고 버튼 추가
        button_help_layout.addStretch()
        button_help_layout.addWidget(component_help_button)

        focus_layout.addRow("", button_help_layout)

        layout.addWidget(focus_frame)

        # 성능 모니터링 설정
        performance_frame = QFrame()
        performance_layout = QFormLayout(performance_frame)

        self.performance_monitoring_checkbox = QCheckBox("성능 모니터링 활성화")
        self.performance_monitoring_checkbox.setChecked(False)
        self.performance_monitoring_checkbox.setToolTip("Infrastructure Layer의 성능 메트릭 수집을 활성화합니다")

        # 성능 모니터링과 헬프 버튼을 함께 배치
        perf_layout = QHBoxLayout()
        perf_layout.addWidget(self.performance_monitoring_checkbox)

        # 성능 모니터링 헬프 버튼
        perf_help_button = QPushButton("?")
        perf_help_button.setFixedSize(20, 20)
        perf_help_button.setStyleSheet("""
            QPushButton {
                padding: 0px;
                margin: 0px;
                border: 1px solid gray;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: lightblue;
            }
        """)
        perf_help_button.setToolTip("성능 모니터링 기능에 대한 상세 설명을 보려면 클릭하세요")
        perf_help_button.clicked.connect(self._on_performance_monitoring_help)

        # 우측 정렬을 위해 addStretch()를 먼저 하고 버튼 추가
        perf_layout.addStretch()
        perf_layout.addWidget(perf_help_button)

        performance_layout.addRow("성능 감시:", perf_layout)

        layout.addWidget(performance_frame)

        return group

    def _create_file_logging_group(self) -> QGroupBox:
        """파일 로깅 설정 그룹 생성"""
        group = QGroupBox("파일 로깅 설정")
        layout = QFormLayout(group)

        # 파일 로깅 활성화
        self.file_logging_checkbox = QCheckBox("파일에 로그 저장")
        self.file_logging_checkbox.setChecked(True)
        layout.addRow("파일 저장:", self.file_logging_checkbox)

        # 파일 로깅 레벨
        self.file_log_level_combo = QComboBox()
        self.file_log_level_combo.addItems([
            "DEBUG - 상세 디버그 정보",
            "INFO - 일반 정보",
            "WARNING - 경고",
            "ERROR - 오류",
            "CRITICAL - 치명적 오류"
        ])
        self.file_log_level_combo.setCurrentText("DEBUG - 상세 디버그 정보")
        layout.addRow("파일 로그 레벨:", self.file_log_level_combo)

        # 파일 경로와 헬프 버튼
        file_path_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setText("logs")
        self.file_path_edit.setEnabled(True)  # 파일 로깅이 활성화되면 편집 가능
        file_path_layout.addWidget(self.file_path_edit)

        # 파일 경로 헬프 버튼
        file_path_help_button = QPushButton("?")
        file_path_help_button.setFixedSize(20, 20)
        file_path_help_button.setStyleSheet("""
            QPushButton {
                padding: 0px;
                margin: 0px;
                border: 1px solid gray;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: lightblue;
            }
        """)
        file_path_help_button.setToolTip("파일 로깅 경로 설정에 대한 상세 설명을 보려면 클릭하세요")
        file_path_help_button.clicked.connect(self._on_file_path_help)
        file_path_layout.addWidget(file_path_help_button)

        layout.addRow("저장 경로:", file_path_layout)

        # 최대 파일 크기
        self.max_size_spinbox = QSpinBox()
        self.max_size_spinbox.setRange(1, 100)
        self.max_size_spinbox.setValue(10)
        self.max_size_spinbox.setSuffix(" MB")
        layout.addRow("최대 크기:", self.max_size_spinbox)

        # 백업 파일 개수
        self.backup_count_spinbox = QSpinBox()
        self.backup_count_spinbox.setRange(0, 20)
        self.backup_count_spinbox.setValue(5)
        self.backup_count_spinbox.setSuffix(" 개")
        layout.addRow("백업 개수:", self.backup_count_spinbox)

        return group

    def _create_action_buttons(self) -> QHBoxLayout:
        """액션 버튼 레이아웃 생성"""
        layout = QHBoxLayout()

        # 설정 적용 버튼
        self.apply_button = QPushButton("설정 적용")
        self.apply_button.setObjectName("button-primary")
        layout.addWidget(self.apply_button)

        # 기본값 복원 버튼
        self.reset_button = QPushButton("기본값 복원")
        self.reset_button.setObjectName("button-secondary")
        layout.addWidget(self.reset_button)

        return layout

    def _connect_signals(self):
        """시그널 연결"""
        # 컨트롤 변경 시그널
        self.context_combo.currentTextChanged.connect(self._on_context_changed)
        self.log_level_combo.currentTextChanged.connect(self._on_log_level_changed)
        self.console_output_combo.currentTextChanged.connect(self._on_console_output_changed)
        self.log_scope_combo.currentTextChanged.connect(self._on_log_scope_changed)
        self.component_focus_edit.textChanged.connect(self._on_component_focus_changed)
        self.file_logging_checkbox.toggled.connect(self._on_file_logging_changed)
        self.file_log_level_combo.currentTextChanged.connect(self._on_file_log_level_changed)
        self.file_path_edit.textChanged.connect(self._on_file_path_changed)
        self.performance_monitoring_checkbox.toggled.connect(self._on_performance_monitoring_changed)

        # 액션 버튼
        self.apply_button.clicked.connect(self._on_apply_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)

        # 파일 로깅 토글에 따른 입력 필드 활성화/비활성화
        self.file_logging_checkbox.toggled.connect(self.file_path_edit.setEnabled)
        self.file_logging_checkbox.toggled.connect(self.max_size_spinbox.setEnabled)
        self.file_logging_checkbox.toggled.connect(self.backup_count_spinbox.setEnabled)

    # ===== 이벤트 핸들러 =====

    def _on_context_changed(self, text: str):
        """실행 환경 변경 처리"""
        if self._is_loading:
            return
        context = text.split(" - ")[0]  # "development - 개발 환경" -> "development"
        self.context_changed.emit(context)

    def _on_log_level_changed(self, text: str):
        """로그 레벨 변경 처리"""
        if self._is_loading:
            return
        level = text.split(" - ")[0]  # "INFO - 일반 정보" -> "INFO"
        self.log_level_changed.emit(level)

    def _on_console_output_changed(self, text: str):
        """콘솔 출력 변경 처리"""
        if self._is_loading:
            return
        # "true - 항상 출력" -> "true"
        output_mode = text.split(" - ")[0]
        self.console_output_changed.emit(output_mode)

    def _on_log_scope_changed(self, text: str):
        """로그 스코프 변경 처리"""
        if self._is_loading:
            return
        scope = text.split(" - ")[0]  # "normal - 일반" -> "normal"
        self.log_scope_changed.emit(scope)

    def _on_component_focus_changed(self, text: str):
        """컴포넌트 집중 변경 처리"""
        if self._is_loading:
            return
        self.component_focus_changed.emit(text)

    def _on_file_logging_changed(self, checked: bool):
        """파일 로깅 토글 변경 처리"""
        if self._is_loading:
            return
        self.file_logging_changed.emit(checked)

    def _on_file_path_changed(self, text: str):
        """파일 경로 변경 처리"""
        if self._is_loading:
            return
        self.file_path_changed.emit(text)

    def _on_file_log_level_changed(self, text: str):
        """파일 로그 레벨 변경 처리"""
        if self._is_loading:
            return
        # "DEBUG - 상세 디버그 정보" -> "DEBUG"
        log_level = text.split(" - ")[0]
        self.file_log_level_changed.emit(log_level)

    def _on_performance_monitoring_changed(self, checked: bool):
        """성능 모니터링 변경 처리"""
        if self._is_loading:
            return
        self.performance_monitoring_changed.emit(checked)

    def _on_apply_clicked(self):
        """설정 적용 버튼 클릭"""
        self.apply_settings.emit()

    def _on_reset_clicked(self):
        """기본값 복원 버튼 클릭"""
        self.reset_settings.emit()

    # ===== 공개 인터페이스 =====

    def get_context(self) -> str:
        """현재 실행 환경 반환"""
        text = self.context_combo.currentText()
        return text.split(" - ")[0]

    def set_context(self, context: str):
        """실행 환경 설정"""
        self._is_loading = True
        try:
            for i in range(self.context_combo.count()):
                item_text = self.context_combo.itemText(i)
                if item_text.startswith(context):
                    self.context_combo.setCurrentIndex(i)
                    break
        finally:
            self._is_loading = False

    def get_log_level(self) -> str:
        """현재 로그 레벨 반환"""
        text = self.log_level_combo.currentText()
        return text.split(" - ")[0]

    def set_log_level(self, level: str):
        """로그 레벨 설정"""
        self._is_loading = True
        try:
            for i in range(self.log_level_combo.count()):
                item_text = self.log_level_combo.itemText(i)
                if item_text.startswith(level):
                    self.log_level_combo.setCurrentIndex(i)
                    break
        finally:
            self._is_loading = False

    def get_console_output(self) -> str:
        """콘솔 출력 설정 반환"""
        text = self.console_output_combo.currentText()
        return text.split(" - ")[0]  # "true - 항상 출력" -> "true"

    def set_console_output(self, value: str):
        """콘솔 출력 설정"""
        self._is_loading = True
        try:
            mapping = {
                "true": "true - 항상 출력",
                "false": "false - 출력 안함",
                "auto": "auto - 오류시만"
            }
            display_text = mapping.get(str(value).lower(), "false - 출력 안함")
            self.console_output_combo.setCurrentText(display_text)
        finally:
            self._is_loading = False

    def get_log_scope(self) -> str:
        """로그 스코프 반환"""
        text = self.log_scope_combo.currentText()
        return text.split(" - ")[0]

    def set_log_scope(self, scope: str):
        """로그 스코프 설정"""
        self._is_loading = True
        try:
            for i in range(self.log_scope_combo.count()):
                item_text = self.log_scope_combo.itemText(i)
                if item_text.startswith(scope):
                    self.log_scope_combo.setCurrentIndex(i)
                    break
        finally:
            self._is_loading = False

    def get_component_focus(self) -> str:
        """컴포넌트 집중 설정 반환"""
        return self.component_focus_edit.text()

    def set_component_focus(self, component: str):
        """컴포넌트 집중 설정"""
        self._is_loading = True
        try:
            self.component_focus_edit.setText(component)
        finally:
            self._is_loading = False

    def get_file_log_level(self) -> str:
        """파일 로그 레벨 반환"""
        text = self.file_log_level_combo.currentText()
        return text.split(" - ")[0]  # "DEBUG - 상세 디버그 정보" -> "DEBUG"

    def set_file_log_level(self, level: str):
        """파일 로그 레벨 설정"""
        self._is_loading = True
        try:
            mapping = {
                "DEBUG": "DEBUG - 상세 디버그 정보",
                "INFO": "INFO - 일반 정보",
                "WARNING": "WARNING - 경고",
                "ERROR": "ERROR - 오류",
                "CRITICAL": "CRITICAL - 치명적 오류"
            }
            display_text = mapping.get(level.upper(), "DEBUG - 상세 디버그 정보")
            self.file_log_level_combo.setCurrentText(display_text)
        finally:
            self._is_loading = False

    def get_performance_monitoring(self) -> bool:
        """성능 모니터링 설정 반환"""
        return self.performance_monitoring_checkbox.isChecked()

    def set_performance_monitoring(self, enabled: bool):
        """성능 모니터링 설정"""
        self._is_loading = True
        try:
            self.performance_monitoring_checkbox.setChecked(enabled)
        finally:
            self._is_loading = False

    def get_file_logging_settings(self) -> dict:
        """파일 로깅 설정 반환"""
        return {
            'enabled': self.file_logging_checkbox.isChecked(),
            'path': self.file_path_edit.text(),
            'level': self.get_file_log_level(),
            'max_size_mb': self.max_size_spinbox.value(),
            'backup_count': self.backup_count_spinbox.value()
        }

    def set_file_logging_settings(self, settings: dict):
        """파일 로깅 설정"""
        self._is_loading = True
        try:
            self.file_logging_checkbox.setChecked(settings.get('enabled', True))
            self.file_path_edit.setText(settings.get('path', 'logs/upbit_auto_trading.log'))
            self.set_file_log_level(settings.get('level', 'DEBUG'))
            self.max_size_spinbox.setValue(settings.get('max_size_mb', 10))
            self.backup_count_spinbox.setValue(settings.get('backup_count', 5))
        finally:
            self._is_loading = False

    def reset_to_defaults(self):
        """모든 설정을 기본값으로 복원"""
        self._is_loading = True
        try:
            self.set_context("development")
            self.set_log_level("INFO")
            self.set_console_output("false")
            self.set_log_scope("normal")
            self.set_component_focus("")
            self.set_file_logging_settings({
                'enabled': True,
                'path': 'logs',
                'level': 'DEBUG',
                'max_size_mb': 10,
                'backup_count': 5
            })
            self.set_performance_monitoring(False)
        finally:
            self._is_loading = False

    def update_from_settings(self, settings: dict):
        """설정 딕셔너리로부터 UI 업데이트 (Presenter에서 호출)

        Args:
            settings: 로깅 설정 딕셔너리
        """
        self._is_loading = True
        try:
            # 기본 로깅 설정
            if 'context' in settings:
                self.set_context(settings['context'])
            if 'level' in settings:
                self.set_log_level(settings['level'])
            if 'console_output' in settings:
                # boolean 값도 호환성을 위해 지원
                console_value = settings['console_output']
                if isinstance(console_value, bool):
                    console_value = "true" if console_value else "false"
                self.set_console_output(str(console_value))
            if 'scope' in settings:
                self.set_log_scope(settings['scope'])
            if 'component_focus' in settings:
                self.set_component_focus(settings['component_focus'])

            # 파일 로깅 설정
            if 'file_logging' in settings:
                self.set_file_logging_settings(settings['file_logging'])

            # 고급 설정 (advanced 섹션)
            if 'advanced' in settings:
                advanced = settings['advanced']
                if 'performance_monitoring' in advanced:
                    self.set_performance_monitoring(advanced['performance_monitoring'])

        finally:
            self._is_loading = False

    def get_current_settings(self) -> dict:
        """현재 설정값들을 딕셔너리로 반환 (MVP Presenter 인터페이스)

        Phase 5.1 MVP 패턴을 위한 메서드

        Returns:
            dict: 현재 설정 딕셔너리
        """
        return {
            'context': self.get_context(),
            'level': self.get_log_level(),
            'console_output': self.get_console_output(),
            'scope': self.get_log_scope(),
            'component_focus': self.get_component_focus(),
            'file_logging': self.get_file_logging_settings(),
            'advanced': {
                'performance_monitoring': self.get_performance_monitoring()
            }
        }

    def _on_select_component(self):
        """컴포넌트 선택 다이얼로그 열기"""
        if not DIALOGS_AVAILABLE or ComponentSelectorDialog is None:
            self.logger.warning("컴포넌트 선택 다이얼로그를 사용할 수 없습니다")
            return

        try:
            dialog = ComponentSelectorDialog(self)
            dialog.setWindowTitle("컴포넌트 선택")

            if dialog.exec() == dialog.DialogCode.Accepted:
                result = dialog.get_selected_component()
                if result and result[0]:  # 튜플의 첫 번째 값(이름) 확인
                    selected_component = result[0]  # 컴포넌트 이름만 사용
                    self.logger.info(f"컴포넌트 선택됨: {selected_component}")
                    self.component_focus_edit.setText(selected_component)
                    # 변경 이벤트 강제 발생
                    self._on_component_focus_changed(selected_component)
                else:
                    self.logger.debug("컴포넌트가 선택되지 않았습니다")

        except Exception as e:
            self.logger.error(f"컴포넌트 선택 다이얼로그 오류: {e}")
            # 폴백: 사용자에게 수동 입력을 안내
            self.component_focus_edit.setFocus()
            self.component_focus_edit.selectAll()

    def _on_clear_component_focus(self):
        """컴포넌트 포커스 지우기"""
        self.logger.debug("컴포넌트 포커스 지우기")
        self.component_focus_edit.clear()
        self._on_component_focus_changed("")

    def _on_component_focus_help(self):
        """컴포넌트 집중 도움말 표시"""
        QMessageBox.information(
            self,
            "컴포넌트 집중 기능",
            "특정 컴포넌트의 로그만 필터링하여 표시합니다.\n\n"
            "기능:\n"
            "• 프로젝트 내 실제 컴포넌트를 탐색하여 선택\n"
            "• 직접 컴포넌트명 입력 가능\n"
            "• DDD 4계층 아키텍처 기반 분류\n"
            "• 검색 및 필터링 지원\n\n"
            "사용법:\n"
            "1. '컴포넌트 선택...' 버튼으로 탐색 후 선택\n"
            "2. 또는 직접 컴포넌트명 입력\n"
            "3. '지우기' 버튼으로 필터 해제"
        )

    def _on_performance_monitoring_help(self):
        """성능 모니터링 도움말 표시"""
        QMessageBox.information(
            self,
            "성능 모니터링 기능",
            "Infrastructure Layer의 성능 메트릭을 실시간으로 수집합니다.\n\n"
            "수집 데이터:\n"
            "• 메모리 사용량\n"
            "• 처리 시간\n"
            "• CPU 사용률\n"
            "• I/O 작업 통계\n\n"
            "주의사항:\n"
            "• 활성화 시 약간의 성능 오버헤드 발생\n"
            "• 개발/디버깅 환경에서 권장\n"
            "• 운영 환경에서는 신중히 사용"
        )

    def _on_file_path_help(self):
        """파일 경로 도움말 표시"""
        QMessageBox.information(
            self,
            "파일 로깅 경로 설정",
            "로그 파일이 저장될 경로를 설정합니다.\n\n"
            "파일명 자동화 시스템:\n"
            "• session_[날짜]_[시간]_PID[프로세스ID].log 형식으로 자동 생성\n"
            "• 예: session_20250812_143058_PID12345.log\n\n"
            "백업 시스템:\n"
            "• application.log로 자동 병합됨\n"
            "• 설정된 백업 개수만큼 순환 보관\n"
            "• 최대 크기 초과 시 자동 로테이션\n\n"
            "권장 설정:\n"
            "• 폴더: logs/ (상대 경로)\n"
            "• 절대 경로도 지원됨\n"
            "• 존재하지 않는 폴더는 자동 생성"
        )
