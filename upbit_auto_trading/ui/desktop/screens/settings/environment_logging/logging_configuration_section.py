"""
Logging Configuration Section
=============================

로깅 설정 관리 섹션 (우측 4)
Infrastructure Layer v4.0 로깅 시스템과 완전 연동

Features:
- 로깅 레벨 설정 (DEBUG/INFO/WARNING/ERROR)
- 로깅 컨텍스트 설정 (development/testing/production)
- 로깅 스코프 설정 (minimal/normal/verbose)
- 환경변수 연동 (UPBIT_LOG_*)
- 실시간 설정 적용
"""

import os
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QFormLayout,
    QComboBox, QCheckBox, QLineEdit, QSpinBox, QPushButton,
    QGroupBox, QScrollArea, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger


class LoggingConfigurationSection(QWidget):
    """
    로깅 설정 관리 섹션

    Infrastructure Layer v4.0 로깅 시스템과 연동하여
    실시간 로깅 설정 관리
    """

    # 시그널 정의
    logging_config_changed = pyqtSignal(str, str)  # (key, value)
    apply_logging_config_requested = pyqtSignal(dict)  # 설정 적용 요청
    reset_logging_config_requested = pyqtSignal()  # 초기화 요청

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("LoggingConfigurationSection")

        # Infrastructure 로깅 초기화
        self._logger = create_component_logger("LoggingConfigurationSection")
        self._logger.info("📊 로깅 설정 섹션 초기화 시작")

        # 내부 상태
        self._current_environment = "Development"
        self._config_values = {}
        self._original_values = {}

        self._setup_ui()
        self._connect_signals()
        self._load_current_config()

        self._logger.info("✅ 로깅 설정 섹션 초기화 완료")

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 섹션 제목
        self._create_section_header(layout)

        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(12)

        # 로깅 설정 그룹들
        self._create_basic_logging_group(content_layout)
        self._create_context_scope_group(content_layout)
        self._create_advanced_logging_group(content_layout)

        # 액션 버튼
        self._create_action_buttons(content_layout)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

    def _create_section_header(self, parent_layout: QVBoxLayout):
        """섹션 헤더 생성"""
        header_frame = QFrame()
        header_frame.setObjectName("section-header")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 8, 8, 8)

        # 제목
        title_label = QLabel("📊 로깅 설정")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(title_label)

        # 설명
        desc_label = QLabel("Infrastructure Layer v4.0 로깅 시스템 설정")
        desc_label.setStyleSheet("color: #666; font-size: 10px; margin-bottom: 4px;")
        header_layout.addWidget(desc_label)

        parent_layout.addWidget(header_frame)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #ddd;")
        parent_layout.addWidget(line)

    def _create_basic_logging_group(self, parent_layout: QVBoxLayout):
        """기본 로깅 설정 그룹"""
        group = QGroupBox("🎯 기본 설정")
        group.setObjectName("logging-basic-group")
        form_layout = QFormLayout(group)
        form_layout.setSpacing(8)

        # 로그 레벨
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText(os.getenv('UPBIT_LOG_LEVEL', 'INFO'))
        form_layout.addRow("로그 레벨:", self.log_level_combo)

        # 콘솔 출력
        self.console_output_check = QCheckBox("콘솔 출력 활성화")
        self.console_output_check.setChecked(
            os.getenv('UPBIT_CONSOLE_OUTPUT', 'true').lower() == 'true'
        )
        form_layout.addRow("UPBIT_CONSOLE_OUTPUT:", self.console_output_check)

        parent_layout.addWidget(group)

    def _create_context_scope_group(self, parent_layout: QVBoxLayout):
        """컨텍스트 및 스코프 설정 그룹"""
        group = QGroupBox("🔧 컨텍스트 & 스코프")
        group.setObjectName("logging-context-group")
        form_layout = QFormLayout(group)
        form_layout.setSpacing(8)

        # 로그 컨텍스트
        self.log_context_combo = QComboBox()
        self.log_context_combo.addItems([
            "development", "testing", "production", "debugging"
        ])
        self.log_context_combo.setCurrentText(
            os.getenv('UPBIT_LOG_CONTEXT', 'development')
        )
        form_layout.addRow("컨텍스트:", self.log_context_combo)

        # 로그 스코프
        self.log_scope_combo = QComboBox()
        self.log_scope_combo.addItems([
            "silent", "minimal", "normal", "verbose", "debug_all"
        ])
        self.log_scope_combo.setCurrentText(
            os.getenv('UPBIT_LOG_SCOPE', 'normal')
        )
        form_layout.addRow("스코프:", self.log_scope_combo)

        # 컴포넌트 포커스
        self.component_focus_edit = QLineEdit()
        self.component_focus_edit.setText(
            os.getenv('UPBIT_COMPONENT_FOCUS', '')
        )
        self.component_focus_edit.setPlaceholderText("예: TradingEngine")
        form_layout.addRow("컴포넌트 포커스:", self.component_focus_edit)

        parent_layout.addWidget(group)

    def _create_advanced_logging_group(self, parent_layout: QVBoxLayout):
        """고급 로깅 설정 그룹"""
        group = QGroupBox("🤖 고급 기능")
        group.setObjectName("logging-advanced-group")
        form_layout = QFormLayout(group)
        form_layout.setSpacing(8)

        # LLM 브리핑
        self.llm_briefing_check = QCheckBox("LLM 브리핑 활성화")
        self.llm_briefing_check.setChecked(
            os.getenv('UPBIT_LLM_BRIEFING_ENABLED', 'true').lower() == 'true'
        )
        form_layout.addRow("LLM 브리핑:", self.llm_briefing_check)

        # 기능 개발 모드
        self.feature_dev_edit = QLineEdit()
        self.feature_dev_edit.setText(
            os.getenv('UPBIT_FEATURE_DEVELOPMENT', '')
        )
        self.feature_dev_edit.setPlaceholderText("예: TriggerBuilder")
        form_layout.addRow("개발 모드:", self.feature_dev_edit)

        # 성능 모니터링
        self.performance_monitoring_check = QCheckBox("성능 모니터링 활성화")
        self.performance_monitoring_check.setChecked(
            os.getenv('UPBIT_PERFORMANCE_MONITORING', 'true').lower() == 'true'
        )
        form_layout.addRow("성능 모니터링:", self.performance_monitoring_check)

        # 브리핑 간격
        self.briefing_interval_spin = QSpinBox()
        self.briefing_interval_spin.setRange(1, 60)
        self.briefing_interval_spin.setValue(
            int(os.getenv('UPBIT_BRIEFING_UPDATE_INTERVAL', '5'))
        )
        self.briefing_interval_spin.setSuffix(" 분")
        form_layout.addRow("브리핑 간격:", self.briefing_interval_spin)

        parent_layout.addWidget(group)

    def _create_action_buttons(self, parent_layout: QVBoxLayout):
        """액션 버튼들"""
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 8, 0, 0)

        # 적용 버튼
        self.apply_btn = QPushButton("✅ 적용")
        self.apply_btn.setObjectName("primary-button")
        self.apply_btn.setMinimumHeight(32)
        self.apply_btn.setEnabled(False)  # 변경사항 있을 때만 활성화

        # 초기화 버튼
        self.reset_btn = QPushButton("🔄 초기화")
        self.reset_btn.setObjectName("secondary-button")
        self.reset_btn.setMinimumHeight(32)

        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()

        parent_layout.addWidget(button_frame)

    def _connect_signals(self):
        """시그널 연결"""
        # 설정 변경 감지
        self.log_level_combo.currentTextChanged.connect(
            lambda text: self._on_config_changed('UPBIT_LOG_LEVEL', text)
        )
        self.console_output_check.toggled.connect(
            lambda checked: self._on_config_changed('UPBIT_CONSOLE_OUTPUT', 'true' if checked else 'false')
        )
        self.log_context_combo.currentTextChanged.connect(
            lambda text: self._on_config_changed('UPBIT_LOG_CONTEXT', text)
        )
        self.log_scope_combo.currentTextChanged.connect(
            lambda text: self._on_config_changed('UPBIT_LOG_SCOPE', text)
        )
        self.component_focus_edit.textChanged.connect(
            lambda text: self._on_config_changed('UPBIT_COMPONENT_FOCUS', text)
        )
        self.llm_briefing_check.toggled.connect(
            lambda checked: self._on_config_changed('UPBIT_LLM_BRIEFING_ENABLED', 'true' if checked else 'false')
        )
        self.feature_dev_edit.textChanged.connect(
            lambda text: self._on_config_changed('UPBIT_FEATURE_DEVELOPMENT', text)
        )
        self.performance_monitoring_check.toggled.connect(
            lambda checked: self._on_config_changed('UPBIT_PERFORMANCE_MONITORING', 'true' if checked else 'false')
        )
        self.briefing_interval_spin.valueChanged.connect(
            lambda value: self._on_config_changed('UPBIT_BRIEFING_UPDATE_INTERVAL', str(value))
        )

        # 액션 버튼
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        self.reset_btn.clicked.connect(self._on_reset_clicked)

    def _load_current_config(self):
        """현재 설정 로드"""
        self._logger.info("🔄 현재 로깅 설정 로드 중...")

        logging_env_vars = [
            'UPBIT_LOG_LEVEL', 'UPBIT_CONSOLE_OUTPUT', 'UPBIT_LOG_CONTEXT',
            'UPBIT_LOG_SCOPE', 'UPBIT_COMPONENT_FOCUS', 'UPBIT_LLM_BRIEFING_ENABLED',
            'UPBIT_FEATURE_DEVELOPMENT', 'UPBIT_PERFORMANCE_MONITORING',
            'UPBIT_BRIEFING_UPDATE_INTERVAL'
        ]

        for var in logging_env_vars:
            value = os.getenv(var, '')
            self._config_values[var] = value
            self._original_values[var] = value

        self._logger.info(f"✅ {len(logging_env_vars)}개 로깅 설정 로드 완료")

    def _on_config_changed(self, key: str, value: str):
        """설정 변경 처리"""
        self._config_values[key] = value
        self.logging_config_changed.emit(key, value)

        # 변경 여부 확인 및 적용 버튼 상태 업데이트
        has_changes = any(
            self._config_values.get(k, '') != self._original_values.get(k, '')
            for k in self._config_values
        )
        self.apply_btn.setEnabled(has_changes)

        self._logger.debug(f"🔧 로깅 설정 변경: {key} = {value}")

    def _on_apply_clicked(self):
        """적용 버튼 클릭 처리"""
        self._logger.info("💾 로깅 설정 적용 시작")

        try:
            # 환경변수 설정
            for key, value in self._config_values.items():
                if value:  # 빈 값이 아닌 경우만
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]

            # 원본 값 업데이트
            self._original_values = self._config_values.copy()
            self.apply_btn.setEnabled(False)

            # 성공 알림
            QMessageBox.information(
                self,
                "로깅 설정 적용 완료",
                "로깅 설정이 성공적으로 적용되었습니다.\n"
                "일부 변경사항은 재시작 후 완전히 적용됩니다."
            )

            # 상위로 전파
            self.apply_logging_config_requested.emit(self._config_values.copy())

            self._logger.info("✅ 로깅 설정 적용 완료")

        except Exception as e:
            self._logger.error(f"❌ 로깅 설정 적용 실패: {e}")
            QMessageBox.critical(
                self,
                "로깅 설정 적용 실패",
                f"로깅 설정 적용 중 오류가 발생했습니다:\n{str(e)}"
            )

    def _on_reset_clicked(self):
        """초기화 버튼 클릭 처리"""
        reply = QMessageBox.question(
            self,
            "로깅 설정 초기화",
            "로깅 설정을 기본값으로 초기화하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._reset_to_defaults()
            self.reset_logging_config_requested.emit()

    def _reset_to_defaults(self):
        """기본값으로 초기화"""
        defaults = {
            'UPBIT_LOG_LEVEL': 'INFO',
            'UPBIT_CONSOLE_OUTPUT': 'true',
            'UPBIT_LOG_CONTEXT': 'development',
            'UPBIT_LOG_SCOPE': 'normal',
            'UPBIT_COMPONENT_FOCUS': '',
            'UPBIT_LLM_BRIEFING_ENABLED': 'true',
            'UPBIT_FEATURE_DEVELOPMENT': '',
            'UPBIT_PERFORMANCE_MONITORING': 'true',
            'UPBIT_BRIEFING_UPDATE_INTERVAL': '5'
        }

        # UI 업데이트
        self.log_level_combo.setCurrentText(defaults['UPBIT_LOG_LEVEL'])
        self.console_output_check.setChecked(defaults['UPBIT_CONSOLE_OUTPUT'] == 'true')
        self.log_context_combo.setCurrentText(defaults['UPBIT_LOG_CONTEXT'])
        self.log_scope_combo.setCurrentText(defaults['UPBIT_LOG_SCOPE'])
        self.component_focus_edit.setText(defaults['UPBIT_COMPONENT_FOCUS'])
        self.llm_briefing_check.setChecked(defaults['UPBIT_LLM_BRIEFING_ENABLED'] == 'true')
        self.feature_dev_edit.setText(defaults['UPBIT_FEATURE_DEVELOPMENT'])
        self.performance_monitoring_check.setChecked(defaults['UPBIT_PERFORMANCE_MONITORING'] == 'true')
        self.briefing_interval_spin.setValue(int(defaults['UPBIT_BRIEFING_UPDATE_INTERVAL']))

        self._logger.info("🔄 로깅 설정을 기본값으로 초기화 완료")

    # === 외부 API ===

    def on_environment_changed(self, environment_name: str):
        """환경 변경 시 처리"""
        self._current_environment = environment_name
        self._logger.info(f"🌍 환경 변경: {environment_name}")

        # 환경별 기본값 적용 (필요시)
        if environment_name == "Production":
            self.log_level_combo.setCurrentText("WARNING")
            self.log_scope_combo.setCurrentText("minimal")
        elif environment_name == "Development":
            self.log_level_combo.setCurrentText("DEBUG")
            self.log_scope_combo.setCurrentText("verbose")
        elif environment_name == "Testing":
            self.log_level_combo.setCurrentText("INFO")
            self.log_scope_combo.setCurrentText("normal")

    def update_config(self, config: dict):
        """설정 업데이트"""
        for key, value in config.items():
            if key in self._config_values:
                self._config_values[key] = value
                # TODO: UI 위젯 업데이트 로직 추가

        self._logger.debug(f"🔧 로깅 설정 업데이트: {len(config)} 항목")

    def get_current_config(self) -> dict:
        """현재 설정 반환"""
        return self._config_values.copy()

    def enable_widgets(self, enabled: bool):
        """위젯 활성화/비활성화"""
        self.log_level_combo.setEnabled(enabled)
        self.console_output_check.setEnabled(enabled)
        self.log_context_combo.setEnabled(enabled)
        self.log_scope_combo.setEnabled(enabled)
        self.component_focus_edit.setEnabled(enabled)
        self.llm_briefing_check.setEnabled(enabled)
        self.feature_dev_edit.setEnabled(enabled)
        self.performance_monitoring_check.setEnabled(enabled)
        self.briefing_interval_spin.setEnabled(enabled)
        self.apply_btn.setEnabled(enabled and self.apply_btn.isEnabled())
        self.reset_btn.setEnabled(enabled)
