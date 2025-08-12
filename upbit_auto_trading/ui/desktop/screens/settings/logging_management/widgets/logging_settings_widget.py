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
    QFormLayout, QSpinBox, QPushButton, QSpacerItem,
    QSizePolicy
)

from upbit_auto_trading.infrastructure.logging import create_component_logger


class LoggingSettingsWidget(QWidget):
    """로깅 설정 위젯 - 좌측 패널"""

    # 시그널 정의
    log_level_changed = pyqtSignal(str)         # 로그 레벨 변경
    console_output_changed = pyqtSignal(bool)   # 콘솔 출력 변경
    log_scope_changed = pyqtSignal(str)         # 로그 스코프 변경
    component_focus_changed = pyqtSignal(str)   # 컴포넌트 집중 변경
    file_logging_changed = pyqtSignal(bool)     # 파일 로깅 토글
    file_path_changed = pyqtSignal(str)         # 파일 경로 변경
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

        # 콘솔 출력 토글
        self.console_output_checkbox = QCheckBox("콘솔에 로그 출력")
        self.console_output_checkbox.setChecked(False)
        layout.addRow("출력 설정:", self.console_output_checkbox)

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
        layout = QFormLayout(group)

        # 컴포넌트 집중
        self.component_focus_edit = QLineEdit()
        self.component_focus_edit.setPlaceholderText("특정 컴포넌트명 입력 (예: TradingEngine)")
        layout.addRow("컴포넌트 집중:", self.component_focus_edit)

        # 설명 레이블
        desc_label = QLabel("특정 컴포넌트의 로그만 필터링하여 표시합니다.")
        desc_label.setStyleSheet("color: gray; font-size: 11px;")
        desc_label.setWordWrap(True)
        layout.addRow("", desc_label)

        return group

    def _create_file_logging_group(self) -> QGroupBox:
        """파일 로깅 설정 그룹 생성"""
        group = QGroupBox("파일 로깅 설정")
        layout = QFormLayout(group)

        # 파일 로깅 활성화
        self.file_logging_checkbox = QCheckBox("파일에 로그 저장")
        self.file_logging_checkbox.setChecked(True)
        layout.addRow("파일 저장:", self.file_logging_checkbox)

        # 파일 경로
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setText("logs/upbit_auto_trading.log")
        self.file_path_edit.setEnabled(True)  # 파일 로깅이 활성화되면 편집 가능
        layout.addRow("저장 경로:", self.file_path_edit)

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
        self.log_level_combo.currentTextChanged.connect(self._on_log_level_changed)
        self.console_output_checkbox.toggled.connect(self._on_console_output_changed)
        self.log_scope_combo.currentTextChanged.connect(self._on_log_scope_changed)
        self.component_focus_edit.textChanged.connect(self._on_component_focus_changed)
        self.file_logging_checkbox.toggled.connect(self._on_file_logging_changed)
        self.file_path_edit.textChanged.connect(self._on_file_path_changed)

        # 액션 버튼
        self.apply_button.clicked.connect(self._on_apply_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)

        # 파일 로깅 토글에 따른 입력 필드 활성화/비활성화
        self.file_logging_checkbox.toggled.connect(self.file_path_edit.setEnabled)
        self.file_logging_checkbox.toggled.connect(self.max_size_spinbox.setEnabled)
        self.file_logging_checkbox.toggled.connect(self.backup_count_spinbox.setEnabled)

    # ===== 이벤트 핸들러 =====

    def _on_log_level_changed(self, text: str):
        """로그 레벨 변경 처리"""
        if self._is_loading:
            return
        level = text.split(" - ")[0]  # "INFO - 일반 정보" -> "INFO"
        self.log_level_changed.emit(level)

    def _on_console_output_changed(self, checked: bool):
        """콘솔 출력 변경 처리"""
        if self._is_loading:
            return
        self.console_output_changed.emit(checked)

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

    def _on_apply_clicked(self):
        """설정 적용 버튼 클릭"""
        self.apply_settings.emit()

    def _on_reset_clicked(self):
        """기본값 복원 버튼 클릭"""
        self.reset_settings.emit()

    # ===== 공개 인터페이스 =====

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

    def get_console_output(self) -> bool:
        """콘솔 출력 설정 반환"""
        return self.console_output_checkbox.isChecked()

    def set_console_output(self, enabled: bool):
        """콘솔 출력 설정"""
        self._is_loading = True
        try:
            self.console_output_checkbox.setChecked(enabled)
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

    def get_file_logging_settings(self) -> dict:
        """파일 로깅 설정 반환"""
        return {
            'enabled': self.file_logging_checkbox.isChecked(),
            'path': self.file_path_edit.text(),
            'max_size_mb': self.max_size_spinbox.value(),
            'backup_count': self.backup_count_spinbox.value()
        }

    def set_file_logging_settings(self, settings: dict):
        """파일 로깅 설정"""
        self._is_loading = True
        try:
            self.file_logging_checkbox.setChecked(settings.get('enabled', True))
            self.file_path_edit.setText(settings.get('path', 'logs/upbit_auto_trading.log'))
            self.max_size_spinbox.setValue(settings.get('max_size_mb', 10))
            self.backup_count_spinbox.setValue(settings.get('backup_count', 5))
        finally:
            self._is_loading = False

    def reset_to_defaults(self):
        """모든 설정을 기본값으로 복원"""
        self._is_loading = True
        try:
            self.set_log_level("INFO")
            self.set_console_output(False)
            self.set_log_scope("normal")
            self.set_component_focus("")
            self.set_file_logging_settings({
                'enabled': True,
                'path': 'logs/upbit_auto_trading.log',
                'max_size_mb': 10,
                'backup_count': 5
            })
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
            if 'level' in settings:
                self.set_log_level(settings['level'])
            if 'console_output' in settings:
                self.set_console_output(settings['console_output'])
            if 'scope' in settings:
                self.set_log_scope(settings['scope'])
            if 'component_focus' in settings:
                self.set_component_focus(settings['component_focus'])

            # 파일 로깅 설정
            if 'file_logging' in settings:
                self.set_file_logging_settings(settings['file_logging'])

        finally:
            self._is_loading = False

    def get_current_settings(self) -> dict:
        """현재 설정값들을 딕셔너리로 반환 (MVP Presenter 인터페이스)

        Phase 5.1 MVP 패턴을 위한 메서드

        Returns:
            dict: 현재 설정 딕셔너리
        """
        return {
            'level': self.get_log_level(),
            'console_output': self.get_console_output(),
            'scope': self.get_log_scope(),
            'component_focus': self.get_component_focus(),
            'file_logging': self.get_file_logging_settings()
        }
