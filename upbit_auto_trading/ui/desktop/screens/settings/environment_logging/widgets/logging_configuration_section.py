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
        context_items = ["development", "testing", "production", "debugging"]
        self.log_context_combo.addItems(context_items)
        # 기본값 보장: 환경변수가 빈값이거나 잘못된 값이면 'development' 사용
        current_context = os.getenv('UPBIT_LOG_CONTEXT', 'development').strip()
        if not current_context or current_context not in context_items:
            current_context = 'development'
        self.log_context_combo.setCurrentText(current_context)
        # 빈 값 선택 방지: 변경 시 항상 유효한 값 보장
        self.log_context_combo.currentTextChanged.connect(self._validate_context_selection)
        form_layout.addRow("컨텍스트:", self.log_context_combo)

        # 로그 스코프
        self.log_scope_combo = QComboBox()
        scope_items = ["silent", "minimal", "normal", "verbose", "debug_all"]
        self.log_scope_combo.addItems(scope_items)
        # 기본값 보장: 환경변수가 빈값이거나 잘못된 값이면 'normal' 사용
        current_scope = os.getenv('UPBIT_LOG_SCOPE', 'normal').strip()
        if not current_scope or current_scope not in scope_items:
            current_scope = 'normal'
        self.log_scope_combo.setCurrentText(current_scope)
        # 빈 값 선택 방지: 변경 시 항상 유효한 값 보장
        self.log_scope_combo.currentTextChanged.connect(self._validate_scope_selection)
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
            lambda text: self._on_config_changed('UPBIT_LOG_CONTEXT', text) if text and text.strip() else None
        )
        self.log_scope_combo.currentTextChanged.connect(
            lambda text: self._on_config_changed('UPBIT_LOG_SCOPE', text) if text and text.strip() else None
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
        """현재 설정 로드 - 빈 값 원천 차단"""
        self._logger.info("🔄 현재 로깅 설정 로드 중...")

        logging_env_vars = [
            'UPBIT_LOG_LEVEL', 'UPBIT_CONSOLE_OUTPUT', 'UPBIT_LOG_CONTEXT',
            'UPBIT_LOG_SCOPE', 'UPBIT_COMPONENT_FOCUS', 'UPBIT_LLM_BRIEFING_ENABLED',
            'UPBIT_FEATURE_DEVELOPMENT', 'UPBIT_PERFORMANCE_MONITORING',
            'UPBIT_BRIEFING_UPDATE_INTERVAL'
        ]

        for var in logging_env_vars:
            value = os.getenv(var, '')

            # 중요한 로깅 설정들은 빈 값을 딕셔너리에 저장하지 않음
            if var in ['UPBIT_LOG_CONTEXT', 'UPBIT_LOG_SCOPE']:
                if value and value.strip():
                    self._config_values[var] = value
                    self._original_values[var] = value
                    self._logger.debug(f"🔍 {var} 로드됨: {value}")
                else:
                    # 빈 값은 딕셔너리에 저장하지 않음 (안전한 기본 상태)
                    self._logger.debug(f"🔍 {var} 빈 값 - 딕셔너리 저장 생략")
            else:
                # 다른 설정들은 기존 방식 유지
                self._config_values[var] = value
                self._original_values[var] = value

        self._logger.info(f"✅ {len(logging_env_vars)}개 로깅 설정 로드 완료")

    def _on_config_changed(self, key: str, value: str):
        """설정 변경 처리 - 빈 값 원천 차단 및 딕셔너리 무결성 보장"""
        # 컨텍스트와 스코프는 빈 값 허용 안 함
        if key in ['UPBIT_LOG_CONTEXT', 'UPBIT_LOG_SCOPE']:
            if not value or not value.strip():
                self._logger.warning(f"⚠️ {key} 빈 값 감지 - 무시됨 (딕셔너리 저장 차단)")
                # 딕셔너리에서도 제거 (기존 빈 값 정리)
                if key in self._config_values:
                    del self._config_values[key]
                return  # 빈 값은 아예 처리하지 않음

        # 정상 값만 딕셔너리에 저장
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
        """적용 버튼 클릭 처리 - 실시간 동적 적용"""
        self._logger.info("💾 실시간 로깅 설정 적용 시작")

        try:
            # **터미널에 적용될 환경변수 명확히 출력**
            print("=" * 70)
            print("🔧 UI → Infrastructure 로깅 환경변수 실시간 적용")
            print("=" * 70)

            # 환경변수 설정
            applied_vars = {}
            for key, value in self._config_values.items():
                if value:  # 빈 값이 아닌 경우만
                    os.environ[key] = value
                    applied_vars[key] = value
                    print(f"✓ {key} = {value}")  # 적용된 값 출력
                elif key in os.environ:
                    del os.environ[key]
                    print(f"✗ {key} (삭제됨)")

            print("=" * 70)

            # **실시간 Infrastructure Layer 동적 적용**
            self._apply_dynamic_logging_changes()

            # Infrastructure 로깅 서비스 재초기화 시도
            try:
                from upbit_auto_trading.infrastructure.logging import create_component_logger
                test_logger = create_component_logger("LoggingConfigTest")
                test_logger.info("🧪 실시간 로깅 설정 적용 테스트")
                print("✅ Infrastructure 로깅 실시간 테스트 완료")
            except Exception as logging_error:
                print(f"⚠️ Infrastructure 로깅 테스트 실패: {logging_error}")

            # **적용된 환경변수 요약 출력**
            if applied_vars:
                print(f"📋 총 {len(applied_vars)}개 환경변수가 Infrastructure Layer에 적용되었습니다.")

            # 원본 값 업데이트
            self._original_values = self._config_values.copy()
            self.apply_btn.setEnabled(False)

            # 성공 알림
            QMessageBox.information(
                self,
                "실시간 로깅 설정 적용 완료",
                "로깅 설정이 실시간으로 적용되었습니다.\n"
                "새로운 로그부터 변경된 설정이 즉시 반영됩니다."
            )

            # 상위로 전파
            self.apply_logging_config_requested.emit(self._config_values.copy())

            self._logger.info("✅ 실시간 로깅 설정 적용 완료")

        except Exception as e:
            self._logger.error(f"❌ 로깅 설정 적용 실패: {e}")
            QMessageBox.critical(
                self,
                "로깅 설정 적용 실패",
                f"로깅 설정 적용 중 오류가 발생했습니다:\n{str(e)}"
            )

    def _apply_dynamic_logging_changes(self):
        """Infrastructure Layer에 실시간 동적 로깅 설정 적용"""
        try:
            # 로깅 서비스 가져오기
            from upbit_auto_trading.infrastructure.logging.services.logging_service import get_logging_service
            from upbit_auto_trading.infrastructure.logging.interfaces.logging_interface import LogContext, LogScope

            logging_service = get_logging_service()

            # 컨텍스트 동적 변경 적용
            if 'UPBIT_LOG_CONTEXT' in self._config_values:
                context_value = self._config_values['UPBIT_LOG_CONTEXT']
                # 2차 안전 검증: 빈 값 완전 차단
                if context_value and context_value.strip():
                    context = LogContext(context_value.lower())
                    logging_service.set_context(context)
                    self._logger.info(f"🔧 로그 컨텍스트 실시간 변경: {context.value}")
                else:
                    self._logger.warning(f"⚠️ 빈 컨텍스트 값 감지됨 - Infrastructure Layer 전달 차단: '{context_value}'")

            # 스코프 동적 변경 적용
            if 'UPBIT_LOG_SCOPE' in self._config_values:
                scope_value = self._config_values['UPBIT_LOG_SCOPE']
                # 2차 안전 검증: 빈 값 완전 차단
                if scope_value and scope_value.strip():
                    scope = LogScope(scope_value.lower())
                    logging_service.set_scope(scope)
                    self._logger.info(f"🔧 로그 스코프 실시간 변경: {scope.value}")
                else:
                    self._logger.warning(f"⚠️ 빈 스코프 값 감지됨 - Infrastructure Layer 전달 차단: '{scope_value}'")

            # 컴포넌트 포커스 실시간 적용
            if 'UPBIT_COMPONENT_FOCUS' in self._config_values:
                focus_component = self._config_values['UPBIT_COMPONENT_FOCUS'].strip()
                if focus_component:
                    self._logger.info(f"🎯 컴포넌트 포커스 실시간 설정: {focus_component}")
                    print(f"🎯 컴포넌트 포커스 실시간 설정: {focus_component}")
                else:
                    self._logger.info("🎯 컴포넌트 포커스 실시간 해제")
                    print("🎯 컴포넌트 포커스 실시간 해제")

            print("🚀 Infrastructure Layer 실시간 동적 설정 적용 완료")

        except Exception as e:
            self._logger.error(f"❌ Infrastructure Layer 실시간 설정 적용 실패: {e}")
            print(f"❌ Infrastructure Layer 실시간 설정 적용 실패: {e}")
            # 계속 진행 (환경변수는 이미 설정됨)

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

    def _validate_context_selection(self, text: str):
        """컨텍스트 선택 검증 - 빈 값 방지"""
        if not text or not text.strip():
            # 빈 값이 선택되면 강제로 기본값으로 복원
            self.log_context_combo.setCurrentText('development')
            self._logger.warning("⚠️ 컨텍스트 빈 값 감지 - 'development'로 복원")

    def _validate_scope_selection(self, text: str):
        """스코프 선택 검증 - 빈 값 방지"""
        if not text or not text.strip():
            # 빈 값이 선택되면 강제로 기본값으로 복원
            self.log_scope_combo.setCurrentText('normal')
            self._logger.warning("⚠️ 스코프 빈 값 감지 - 'normal'로 복원")

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
