"""
Environment Variables Management Widget

환경변수 관리를 위한 전용 UI 위젯입니다.
시스템 전체의 환경변수를 체계적으로 관리하고 편집할 수 있습니다.

Features:
- 로깅 환경변수 관리 (실제 구현)
- 거래 환경변수 관리 (미구현 - UI만)
- API 환경변수 관리 (미구현 - UI만)
- 시스템 환경변수 관리 (미구현 - UI만)
- MVP 패턴 완전 적용

Architecture:
- View: EnvironmentVariablesWidget (현재 파일)
- Presenter: EnvironmentVariablesPresenter (향후 생성)
- Model: Environment Variable DTOs (향후 생성)
"""

import os
from typing import Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QFormLayout, QLineEdit,
    QComboBox, QCheckBox, QScrollArea, QFrame,
    QTabWidget, QSpinBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger


class EnvironmentVariablesWidget(QWidget):
    """
    환경변수 관리 위젯

    시스템 전체의 환경변수를 카테고리별로 관리합니다.
    MVP 패턴을 적용하여 View 역할만 담당합니다.
    """

    # MVP 시그널 정의
    env_var_changed = pyqtSignal(str, str)  # (key, value)
    apply_changes_requested = pyqtSignal()
    reset_to_defaults_requested = pyqtSignal()
    export_config_requested = pyqtSignal()
    import_config_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EnvironmentVariablesWidget")

        # 로깅 초기화
        self._logger = create_component_logger("EnvironmentVariablesWidget")
        self._logger.info("🌍 환경변수 관리 위젯 초기화 시작")

        # 환경변수 데이터 저장소
        self._env_vars = {}
        self._original_env_vars = {}  # 변경 감지용

        self._setup_ui()
        self._connect_signals()
        self._load_current_environment_variables()

        self._logger.info("✅ 환경변수 관리 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 제목 및 설명
        self._create_header_section(layout)

        # 탭 위젯으로 카테고리별 관리
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("env-vars-tab-widget")

        # 1. 로깅 환경변수 탭 (실제 구현)
        self.tab_widget.addTab(self._create_logging_tab(), "📊 로깅 설정")

        # 2. 거래 환경변수 탭 (미구현)
        self.tab_widget.addTab(self._create_trading_tab(), "💰 거래 설정")

        # 3. API 환경변수 탭 (미구현)
        self.tab_widget.addTab(self._create_api_tab(), "🔗 API 설정")

        # 4. 시스템 환경변수 탭 (미구현)
        self.tab_widget.addTab(self._create_system_tab(), "⚙️ 시스템 설정")

        layout.addWidget(self.tab_widget)

        # 액션 버튼들
        self._create_action_buttons(layout)

    def _create_header_section(self, parent_layout):
        """헤더 섹션 생성"""
        header_frame = QFrame()
        header_frame.setObjectName("env-vars-header")
        header_layout = QVBoxLayout(header_frame)

        # 제목
        title_label = QLabel("🌍 환경변수 관리")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        # 설명
        desc_label = QLabel(
            "시스템 전체의 환경변수를 카테고리별로 관리합니다.\n"
            "변경사항은 '적용' 버튼을 눌러야 실제로 반영됩니다."
        )
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #666; font-size: 12px;")
        desc_label.setWordWrap(True)
        header_layout.addWidget(desc_label)

        parent_layout.addWidget(header_frame)

    def _create_logging_tab(self):
        """로깅 환경변수 탭 - 실제 구현"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # 로깅 컨텍스트 그룹
        self._create_logging_context_group(content_layout)

        # 로깅 레벨 그룹
        self._create_logging_level_group(content_layout)

        # 로깅 출력 제어 그룹
        self._create_logging_output_group(content_layout)

        # LLM 및 고급 기능 그룹
        self._create_logging_advanced_group(content_layout)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        return widget

    def _create_logging_context_group(self, parent_layout):
        """로깅 컨텍스트 설정 그룹"""
        group = QGroupBox("🎯 로깅 컨텍스트")
        group.setObjectName("env-vars-group")
        form_layout = QFormLayout(group)

        # UPBIT_LOG_CONTEXT
        self.log_context_combo = QComboBox()
        self.log_context_combo.addItems([
            "development", "testing", "production", "debugging"
        ])
        self.log_context_combo.setCurrentText(
            os.getenv('UPBIT_LOG_CONTEXT', 'development')
        )
        form_layout.addRow("로그 컨텍스트 (UPBIT_LOG_CONTEXT):", self.log_context_combo)

        # UPBIT_LOG_SCOPE
        self.log_scope_combo = QComboBox()
        self.log_scope_combo.addItems([
            "silent", "minimal", "normal", "verbose", "debug_all"
        ])
        self.log_scope_combo.setCurrentText(
            os.getenv('UPBIT_LOG_SCOPE', 'normal')
        )
        form_layout.addRow("로그 스코프 (UPBIT_LOG_SCOPE):", self.log_scope_combo)

        parent_layout.addWidget(group)

    def _create_logging_level_group(self, parent_layout):
        """로깅 레벨 설정 그룹"""
        group = QGroupBox("📊 로깅 레벨")
        group.setObjectName("env-vars-group")
        form_layout = QFormLayout(group)

        # UPBIT_LOG_LEVEL
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems([
            "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        ])
        self.log_level_combo.setCurrentText(
            os.getenv('UPBIT_LOG_LEVEL', 'INFO')
        )
        form_layout.addRow("로그 레벨 (UPBIT_LOG_LEVEL):", self.log_level_combo)

        # UPBIT_COMPONENT_FOCUS
        self.component_focus_edit = QLineEdit()
        self.component_focus_edit.setText(
            os.getenv('UPBIT_COMPONENT_FOCUS', '')
        )
        self.component_focus_edit.setPlaceholderText("예: TradingEngine,RSI_Strategy")
        form_layout.addRow("컴포넌트 포커스 (UPBIT_COMPONENT_FOCUS):", self.component_focus_edit)

        parent_layout.addWidget(group)

    def _create_logging_output_group(self, parent_layout):
        """로깅 출력 제어 그룹"""
        group = QGroupBox("📺 출력 제어")
        group.setObjectName("env-vars-group")
        form_layout = QFormLayout(group)

        # UPBIT_CONSOLE_OUTPUT
        self.console_output_check = QCheckBox("콘솔 출력 활성화")
        self.console_output_check.setChecked(
            os.getenv('UPBIT_CONSOLE_OUTPUT', 'true').lower() == 'true'
        )
        form_layout.addRow("UPBIT_CONSOLE_OUTPUT:", self.console_output_check)

        # UPBIT_FEATURE_DEVELOPMENT
        self.feature_dev_edit = QLineEdit()
        self.feature_dev_edit.setText(
            os.getenv('UPBIT_FEATURE_DEVELOPMENT', '')
        )
        self.feature_dev_edit.setPlaceholderText("예: TriggerBuilder")
        form_layout.addRow("기능 개발 모드 (UPBIT_FEATURE_DEVELOPMENT):", self.feature_dev_edit)

        parent_layout.addWidget(group)

    def _create_logging_advanced_group(self, parent_layout):
        """LLM 및 고급 로깅 기능 그룹"""
        group = QGroupBox("🤖 LLM 및 고급 기능")
        group.setObjectName("env-vars-group")
        form_layout = QFormLayout(group)

        # UPBIT_LLM_BRIEFING_ENABLED
        self.llm_briefing_check = QCheckBox("LLM 브리핑 활성화")
        self.llm_briefing_check.setChecked(
            os.getenv('UPBIT_LLM_BRIEFING_ENABLED', 'true').lower() == 'true'
        )
        form_layout.addRow("UPBIT_LLM_BRIEFING_ENABLED:", self.llm_briefing_check)

        # UPBIT_AUTO_DIAGNOSIS
        self.auto_diagnosis_check = QCheckBox("자동 진단 활성화")
        self.auto_diagnosis_check.setChecked(
            os.getenv('UPBIT_AUTO_DIAGNOSIS', 'true').lower() == 'true'
        )
        form_layout.addRow("UPBIT_AUTO_DIAGNOSIS:", self.auto_diagnosis_check)

        # UPBIT_PERFORMANCE_MONITORING
        self.performance_monitoring_check = QCheckBox("성능 모니터링 활성화")
        self.performance_monitoring_check.setChecked(
            os.getenv('UPBIT_PERFORMANCE_MONITORING', 'true').lower() == 'true'
        )
        form_layout.addRow("UPBIT_PERFORMANCE_MONITORING:", self.performance_monitoring_check)

        # UPBIT_BRIEFING_UPDATE_INTERVAL
        self.briefing_interval_spin = QSpinBox()
        self.briefing_interval_spin.setRange(1, 60)
        self.briefing_interval_spin.setValue(
            int(os.getenv('UPBIT_BRIEFING_UPDATE_INTERVAL', '5'))
        )
        self.briefing_interval_spin.setSuffix(" 분")
        form_layout.addRow("브리핑 업데이트 간격:", self.briefing_interval_spin)

        parent_layout.addWidget(group)

    def _create_trading_tab(self):
        """거래 환경변수 탭 - 미구현"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # 미구현 안내
        self._create_not_implemented_notice(
            layout,
            "💰 거래 환경변수 관리",
            [
                "TRADING_MODE (paper/live)",
                "MAX_POSITION_SIZE_KRW",
                "RISK_MANAGEMENT_ENABLED",
                "STOP_LOSS_PERCENTAGE",
                "TAKE_PROFIT_PERCENTAGE"
            ]
        )

        return widget

    def _create_api_tab(self):
        """API 환경변수 탭 - 미구현"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # 미구현 안내
        self._create_not_implemented_notice(
            layout,
            "🔗 API 환경변수 관리",
            [
                "UPBIT_ACCESS_KEY_DEV",
                "UPBIT_SECRET_KEY_DEV",
                "UPBIT_ACCESS_KEY_PROD",
                "UPBIT_SECRET_KEY_PROD",
                "API_REQUESTS_PER_SECOND",
                "API_TIMEOUT_SECONDS",
                "API_MAX_RETRIES"
            ]
        )

        return widget

    def _create_system_tab(self):
        """시스템 환경변수 탭 - 미구현"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # 미구현 안내
        self._create_not_implemented_notice(
            layout,
            "⚙️ 시스템 환경변수 관리",
            [
                "BACKUP_ENABLED",
                "BACKUP_RETENTION_DAYS",
                "BACKUP_COMPRESSION_ENABLED",
                "DB_CONNECTION_POOL_SIZE",
                "MEMORY_OPTIMIZATION_ENABLED",
                "THREAD_POOL_SIZE"
            ]
        )

        return widget

    def _create_not_implemented_notice(self, parent_layout, title, env_vars):
        """미구현 섹션 안내 생성"""
        # 제목
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        parent_layout.addWidget(title_label)

        # 상태 표시
        status_frame = QFrame()
        status_frame.setObjectName("not-implemented-frame")
        status_frame.setStyleSheet("""
            QFrame#not-implemented-frame {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 20px;
                margin: 10px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)

        # 미구현 안내
        notice_label = QLabel("🚧 미구현 섹션")
        notice_font = QFont()
        notice_font.setBold(True)
        notice_label.setFont(notice_font)
        notice_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(notice_label)

        desc_label = QLabel(
            "이 섹션은 향후 구현 예정입니다.\n"
            "현재는 UI 구조만 준비되어 있습니다."
        )
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #856404; margin: 10px;")
        status_layout.addWidget(desc_label)

        # 예정 환경변수 목록
        vars_label = QLabel("관리 예정 환경변수:")
        vars_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        status_layout.addWidget(vars_label)

        vars_list = QLabel("\n".join([f"• {var}" for var in env_vars]))
        vars_list.setStyleSheet("color: #666; margin: 5px 0 0 20px;")
        vars_list.setWordWrap(True)
        status_layout.addWidget(vars_list)

        parent_layout.addWidget(status_frame)
        parent_layout.addStretch()

    def _create_action_buttons(self, parent_layout):
        """액션 버튼들 생성"""
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 10, 0, 0)

        # 적용 버튼
        self.apply_button = QPushButton("✅ 변경사항 적용")
        self.apply_button.setObjectName("primary-button")
        self.apply_button.setMinimumHeight(35)

        # 초기화 버튼
        self.reset_button = QPushButton("🔄 기본값으로 초기화")
        self.reset_button.setObjectName("secondary-button")
        self.reset_button.setMinimumHeight(35)

        # 내보내기/가져오기 버튼
        self.export_button = QPushButton("📤 설정 내보내기")
        self.export_button.setObjectName("secondary-button")
        self.export_button.setMinimumHeight(35)

        self.import_button = QPushButton("📥 설정 가져오기")
        self.import_button.setObjectName("secondary-button")
        self.import_button.setMinimumHeight(35)

        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.import_button)

        parent_layout.addWidget(button_frame)

    def _connect_signals(self):
        """시그널 연결"""
        # 로깅 설정 변경 감지
        self.log_context_combo.currentTextChanged.connect(
            lambda: self._on_env_var_changed('UPBIT_LOG_CONTEXT', self.log_context_combo.currentText())
        )
        self.log_scope_combo.currentTextChanged.connect(
            lambda: self._on_env_var_changed('UPBIT_LOG_SCOPE', self.log_scope_combo.currentText())
        )
        self.log_level_combo.currentTextChanged.connect(
            lambda: self._on_env_var_changed('UPBIT_LOG_LEVEL', self.log_level_combo.currentText())
        )
        self.component_focus_edit.textChanged.connect(
            lambda: self._on_env_var_changed('UPBIT_COMPONENT_FOCUS', self.component_focus_edit.text())
        )
        self.console_output_check.toggled.connect(
            lambda checked: self._on_env_var_changed('UPBIT_CONSOLE_OUTPUT', 'true' if checked else 'false')
        )
        self.feature_dev_edit.textChanged.connect(
            lambda: self._on_env_var_changed('UPBIT_FEATURE_DEVELOPMENT', self.feature_dev_edit.text())
        )

        # LLM 및 고급 기능
        self.llm_briefing_check.toggled.connect(
            lambda checked: self._on_env_var_changed('UPBIT_LLM_BRIEFING_ENABLED', 'true' if checked else 'false')
        )
        self.auto_diagnosis_check.toggled.connect(
            lambda checked: self._on_env_var_changed('UPBIT_AUTO_DIAGNOSIS', 'true' if checked else 'false')
        )
        self.performance_monitoring_check.toggled.connect(
            lambda checked: self._on_env_var_changed('UPBIT_PERFORMANCE_MONITORING', 'true' if checked else 'false')
        )
        self.briefing_interval_spin.valueChanged.connect(
            lambda value: self._on_env_var_changed('UPBIT_BRIEFING_UPDATE_INTERVAL', str(value))
        )

        # 액션 버튼들
        self.apply_button.clicked.connect(self._on_apply_changes)
        self.reset_button.clicked.connect(self._on_reset_to_defaults)
        self.export_button.clicked.connect(self._on_export_config)
        self.import_button.clicked.connect(self._on_import_config)

    def _load_current_environment_variables(self):
        """현재 환경변수 로드"""
        self._logger.info("🔄 현재 환경변수 로드 중...")

        # 로깅 관련 환경변수들
        logging_vars = [
            'UPBIT_LOG_CONTEXT', 'UPBIT_LOG_SCOPE', 'UPBIT_LOG_LEVEL',
            'UPBIT_COMPONENT_FOCUS', 'UPBIT_CONSOLE_OUTPUT', 'UPBIT_FEATURE_DEVELOPMENT',
            'UPBIT_LLM_BRIEFING_ENABLED', 'UPBIT_AUTO_DIAGNOSIS', 'UPBIT_PERFORMANCE_MONITORING',
            'UPBIT_BRIEFING_UPDATE_INTERVAL'
        ]

        for var in logging_vars:
            value = os.getenv(var, '')
            self._env_vars[var] = value
            self._original_env_vars[var] = value

        self._logger.info(f"✅ {len(logging_vars)}개 환경변수 로드 완료")

    def _on_env_var_changed(self, key: str, value: str):
        """환경변수 변경 처리"""
        self._env_vars[key] = value
        self.env_var_changed.emit(key, value)

        # 변경 여부 확인 및 적용 버튼 상태 업데이트
        has_changes = any(
            self._env_vars.get(k, '') != self._original_env_vars.get(k, '')
            for k in self._env_vars
        )
        self.apply_button.setEnabled(has_changes)

    def _on_apply_changes(self):
        """변경사항 적용"""
        self._logger.info("💾 환경변수 변경사항 적용 시작")

        try:
            # 실제 환경변수 설정
            for key, value in self._env_vars.items():
                if value:  # 빈 값이 아닌 경우만
                    os.environ[key] = value
                    self._logger.debug(f"✅ {key} = {value}")
                elif key in os.environ:
                    # 빈 값으로 설정된 경우 환경변수 제거
                    del os.environ[key]
                    self._logger.debug(f"🗑️ {key} 제거됨")

            # 원본 데이터 업데이트
            self._original_env_vars = self._env_vars.copy()
            self.apply_button.setEnabled(False)

            # 성공 메시지
            QMessageBox.information(
                self,
                "환경변수 적용 완료",
                "환경변수 변경사항이 성공적으로 적용되었습니다.\n"
                "일부 변경사항은 애플리케이션 재시작 후 완전히 적용됩니다."
            )

            self.apply_changes_requested.emit()
            self._logger.info("✅ 환경변수 변경사항 적용 완료")

        except Exception as e:
            self._logger.error(f"❌ 환경변수 적용 실패: {e}")
            QMessageBox.critical(
                self,
                "환경변수 적용 실패",
                f"환경변수 적용 중 오류가 발생했습니다:\n{str(e)}"
            )

    def _on_reset_to_defaults(self):
        """기본값으로 초기화"""
        reply = QMessageBox.question(
            self,
            "기본값으로 초기화",
            "모든 환경변수를 기본값으로 초기화하시겠습니까?\n"
            "현재 설정이 모두 손실됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._reset_to_default_values()
            self.reset_to_defaults_requested.emit()

    def _reset_to_default_values(self):
        """기본값으로 리셋"""
        # 로깅 관련 기본값
        defaults = {
            'UPBIT_LOG_CONTEXT': 'development',
            'UPBIT_LOG_SCOPE': 'normal',
            'UPBIT_LOG_LEVEL': 'INFO',
            'UPBIT_COMPONENT_FOCUS': '',
            'UPBIT_CONSOLE_OUTPUT': 'true',
            'UPBIT_FEATURE_DEVELOPMENT': '',
            'UPBIT_LLM_BRIEFING_ENABLED': 'true',
            'UPBIT_AUTO_DIAGNOSIS': 'true',
            'UPBIT_PERFORMANCE_MONITORING': 'true',
            'UPBIT_BRIEFING_UPDATE_INTERVAL': '5'
        }

        # UI 업데이트
        self.log_context_combo.setCurrentText(defaults['UPBIT_LOG_CONTEXT'])
        self.log_scope_combo.setCurrentText(defaults['UPBIT_LOG_SCOPE'])
        self.log_level_combo.setCurrentText(defaults['UPBIT_LOG_LEVEL'])
        self.component_focus_edit.setText(defaults['UPBIT_COMPONENT_FOCUS'])
        self.console_output_check.setChecked(defaults['UPBIT_CONSOLE_OUTPUT'] == 'true')
        self.feature_dev_edit.setText(defaults['UPBIT_FEATURE_DEVELOPMENT'])
        self.llm_briefing_check.setChecked(defaults['UPBIT_LLM_BRIEFING_ENABLED'] == 'true')
        self.auto_diagnosis_check.setChecked(defaults['UPBIT_AUTO_DIAGNOSIS'] == 'true')
        self.performance_monitoring_check.setChecked(defaults['UPBIT_PERFORMANCE_MONITORING'] == 'true')
        self.briefing_interval_spin.setValue(int(defaults['UPBIT_BRIEFING_UPDATE_INTERVAL']))

        self._logger.info("🔄 환경변수를 기본값으로 초기화 완료")

    def _on_export_config(self):
        """설정 내보내기 - 미구현"""
        QMessageBox.information(
            self,
            "기능 준비중",
            "설정 내보내기 기능은 준비중입니다.\n향후 업데이트에서 제공될 예정입니다."
        )
        self.export_config_requested.emit()

    def _on_import_config(self):
        """설정 가져오기 - 미구현"""
        QMessageBox.information(
            self,
            "기능 준비중",
            "설정 가져오기 기능은 준비중입니다.\n향후 업데이트에서 제공될 예정입니다."
        )
        self.import_config_requested.emit()

    # === MVP View 인터페이스 메서드들 ===

    def get_current_env_vars(self) -> Dict[str, str]:
        """현재 환경변수 값들 반환"""
        return self._env_vars.copy()

    def set_env_var(self, key: str, value: str) -> None:
        """환경변수 값 설정"""
        self._env_vars[key] = value
        # TODO: UI 위젯 업데이트 로직 추가

    def show_validation_result(self, is_valid: bool, message: str) -> None:
        """유효성 검사 결과 표시"""
        if is_valid:
            QMessageBox.information(self, "검증 완료", message)
        else:
            QMessageBox.warning(self, "검증 실패", message)

    def show_error_message(self, title: str, message: str) -> None:
        """오류 메시지 표시"""
        QMessageBox.critical(self, title, message)

    def show_success_message(self, title: str, message: str) -> None:
        """성공 메시지 표시"""
        QMessageBox.information(self, title, message)
