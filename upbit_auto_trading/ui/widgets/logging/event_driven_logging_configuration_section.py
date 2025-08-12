"""
Event-Driven 로깅 구성 섹션
기존 Thread-Safe 패턴을 Event-Driven Architecture로 전환
"""

import asyncio
import os
from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QSpinBox, QCheckBox, QLineEdit, QLabel,
    QPushButton, QGroupBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import QTimer, pyqtSignal, pyqtSlot

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.config.config_manager import ConfigManager
from upbit_auto_trading.infrastructure.events.logging_events import (
    LogConfigurationChangedEvent, EnvironmentVariableChangedEvent
)
from upbit_auto_trading.infrastructure.events.event_system_initializer import EventSystemInitializer
from upbit_auto_trading.infrastructure.events.bus.event_bus_interface import IEventBus
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

class EventDrivenLoggingConfigurationSection(QWidget):
    """Event-Driven Architecture 기반 로깅 구성 섹션"""

    # PyQt6 신호들
    configuration_changed = pyqtSignal(str, dict)  # 구성 변경 신호
    environment_changed = pyqtSignal(str, str, str)  # 환경변수 변경 신호

    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.logger = create_component_logger("EventDrivenLoggingConfigurationSection")

        # Event System
        self.event_bus: Optional[IEventBus] = None
        self.domain_publisher = None
        self._event_subscription_ids: List[str] = []

        # 현재 설정 캐시
        self.current_config = {}
        self.current_env_vars = {}

        # UI 컴포넌트 생성
        self._init_ui()

        # 신호 연결
        self._connect_signals()

        # 초기 설정 로드
        self._load_current_configuration()

        # Event System 설정
        self._setup_event_system()

        self.logger.info("Event-Driven 로깅 구성 섹션 초기화 완료")

    def _init_ui(self):
        """UI 컴포넌트 초기화"""
        layout = QVBoxLayout(self)

        # 기본 로깅 설정 그룹
        basic_group = self._create_basic_logging_group()
        layout.addWidget(basic_group)

        # 핸들러 설정 그룹
        handlers_group = self._create_handlers_group()
        layout.addWidget(handlers_group)

        # 환경 변수 설정 그룹
        env_group = self._create_environment_variables_group()
        layout.addWidget(env_group)

        # 동작 버튼들
        actions_group = self._create_actions_group()
        layout.addWidget(actions_group)

        layout.addStretch()

    def _create_basic_logging_group(self) -> QGroupBox:
        """기본 로깅 설정 그룹"""
        group = QGroupBox("기본 로깅 설정")
        layout = QFormLayout(group)

        # 기본 로그 레벨
        self.default_level_combo = QComboBox()
        self.default_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        layout.addRow("기본 로그 레벨:", self.default_level_combo)

        # 로그 포맷
        self.log_format_combo = QComboBox()
        self.log_format_combo.addItems([
            "간단한 형식",
            "상세한 형식",
            "JSON 형식",
            "사용자 정의"
        ])
        layout.addRow("로그 포맷:", self.log_format_combo)

        # 사용자 정의 포맷 (선택적)
        self.custom_format_edit = QLineEdit()
        self.custom_format_edit.setPlaceholderText("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.custom_format_edit.setEnabled(False)
        layout.addRow("사용자 정의 포맷:", self.custom_format_edit)

        # 날짜 포맷
        self.date_format_edit = QLineEdit()
        self.date_format_edit.setPlaceholderText("%Y-%m-%d %H:%M:%S")
        layout.addRow("날짜 포맷:", self.date_format_edit)

        return group

    def _create_handlers_group(self) -> QGroupBox:
        """핸들러 설정 그룹"""
        group = QGroupBox("로그 핸들러 설정")
        layout = QVBoxLayout(group)

        # 콘솔 핸들러
        console_layout = QHBoxLayout()
        self.console_enabled = QCheckBox("콘솔 출력 활성화")
        self.console_level_combo = QComboBox()
        self.console_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        console_layout.addWidget(self.console_enabled)
        console_layout.addWidget(QLabel("레벨:"))
        console_layout.addWidget(self.console_level_combo)
        console_layout.addStretch()
        layout.addLayout(console_layout)

        # 파일 핸들러
        file_layout = QHBoxLayout()
        self.file_enabled = QCheckBox("파일 출력 활성화")
        self.file_level_combo = QComboBox()
        self.file_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        file_layout.addWidget(self.file_enabled)
        file_layout.addWidget(QLabel("레벨:"))
        file_layout.addWidget(self.file_level_combo)
        file_layout.addStretch()
        layout.addLayout(file_layout)

        # 파일 경로 설정
        file_path_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("logs/application.log")
        self.file_browse_button = QPushButton("찾아보기")
        file_path_layout.addWidget(QLabel("파일 경로:"))
        file_path_layout.addWidget(self.file_path_edit, 1)
        file_path_layout.addWidget(self.file_browse_button)
        layout.addLayout(file_path_layout)

        # 파일 회전 설정
        rotation_layout = QHBoxLayout()
        self.max_file_size = QSpinBox()
        self.max_file_size.setMinimum(1)
        self.max_file_size.setMaximum(1000)
        self.max_file_size.setValue(10)
        self.max_file_size.setSuffix(" MB")

        self.backup_count = QSpinBox()
        self.backup_count.setMinimum(1)
        self.backup_count.setMaximum(100)
        self.backup_count.setValue(5)

        rotation_layout.addWidget(QLabel("최대 파일 크기:"))
        rotation_layout.addWidget(self.max_file_size)
        rotation_layout.addWidget(QLabel("백업 파일 수:"))
        rotation_layout.addWidget(self.backup_count)
        rotation_layout.addStretch()
        layout.addLayout(rotation_layout)

        # 세션 핸들러 (Event-Driven)
        session_layout = QHBoxLayout()
        self.session_enabled = QCheckBox("세션 이벤트 핸들러 활성화")
        self.session_level_combo = QComboBox()
        self.session_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        session_layout.addWidget(self.session_enabled)
        session_layout.addWidget(QLabel("레벨:"))
        session_layout.addWidget(self.session_level_combo)
        session_layout.addStretch()
        layout.addLayout(session_layout)

        return group

    def _create_environment_variables_group(self) -> QGroupBox:
        """환경 변수 설정 그룹"""
        group = QGroupBox("환경 변수")
        layout = QVBoxLayout(group)

        # LOG_LEVEL
        log_level_layout = QHBoxLayout()
        log_level_layout.addWidget(QLabel("LOG_LEVEL:"))
        self.env_log_level_combo = QComboBox()
        self.env_log_level_combo.addItems(["", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_level_layout.addWidget(self.env_log_level_combo)
        log_level_layout.addStretch()
        layout.addLayout(log_level_layout)

        # LOG_FORMAT
        log_format_layout = QHBoxLayout()
        log_format_layout.addWidget(QLabel("LOG_FORMAT:"))
        self.env_log_format_edit = QLineEdit()
        self.env_log_format_edit.setPlaceholderText("환경변수에서 로그 포맷 지정...")
        log_format_layout.addWidget(self.env_log_format_edit, 1)
        layout.addLayout(log_format_layout)

        # LOG_FILE
        log_file_layout = QHBoxLayout()
        log_file_layout.addWidget(QLabel("LOG_FILE:"))
        self.env_log_file_edit = QLineEdit()
        self.env_log_file_edit.setPlaceholderText("환경변수에서 로그 파일 경로 지정...")
        log_file_layout.addWidget(self.env_log_file_edit, 1)
        layout.addLayout(log_file_layout)

        # PYTHONPATH (개발 환경)
        pythonpath_layout = QHBoxLayout()
        pythonpath_layout.addWidget(QLabel("PYTHONPATH:"))
        self.env_pythonpath_edit = QLineEdit()
        self.env_pythonpath_edit.setPlaceholderText("추가 Python 경로...")
        pythonpath_layout.addWidget(self.env_pythonpath_edit, 1)
        layout.addLayout(pythonpath_layout)

        return group

    def _create_actions_group(self) -> QGroupBox:
        """동작 버튼 그룹"""
        group = QGroupBox("동작")
        layout = QHBoxLayout(group)

        # 설정 적용 버튼
        self.apply_button = QPushButton("설정 적용")
        self.apply_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        layout.addWidget(self.apply_button)

        # 설정 재로드 버튼
        self.reload_button = QPushButton("설정 재로드")
        layout.addWidget(self.reload_button)

        # 기본값 복원 버튼
        self.reset_button = QPushButton("기본값 복원")
        layout.addWidget(self.reset_button)

        # 설정 내보내기 버튼
        self.export_button = QPushButton("설정 내보내기")
        layout.addWidget(self.export_button)

        layout.addStretch()

        return group

    def _connect_signals(self):
        """신호 연결"""
        # 내부 신호
        self.configuration_changed.connect(self._on_configuration_changed)
        self.environment_changed.connect(self._on_environment_changed)

        # 기본 설정 변경
        self.default_level_combo.currentTextChanged.connect(
            lambda value: self._emit_config_changed("logging.default_level", value)
        )
        self.log_format_combo.currentTextChanged.connect(self._on_log_format_changed)
        self.custom_format_edit.textChanged.connect(
            lambda value: self._emit_config_changed("logging.custom_format", value)
        )
        self.date_format_edit.textChanged.connect(
            lambda value: self._emit_config_changed("logging.date_format", value)
        )

        # 핸들러 설정 변경
        self.console_enabled.toggled.connect(
            lambda value: self._emit_config_changed("logging.console.enabled", value)
        )
        self.console_level_combo.currentTextChanged.connect(
            lambda value: self._emit_config_changed("logging.console.level", value)
        )
        self.file_enabled.toggled.connect(
            lambda value: self._emit_config_changed("logging.file.enabled", value)
        )
        self.file_level_combo.currentTextChanged.connect(
            lambda value: self._emit_config_changed("logging.file.level", value)
        )
        self.file_path_edit.textChanged.connect(
            lambda value: self._emit_config_changed("logging.file.path", value)
        )
        self.max_file_size.valueChanged.connect(
            lambda value: self._emit_config_changed("logging.file.max_size_mb", value)
        )
        self.backup_count.valueChanged.connect(
            lambda value: self._emit_config_changed("logging.file.backup_count", value)
        )
        self.session_enabled.toggled.connect(
            lambda value: self._emit_config_changed("logging.session.enabled", value)
        )
        self.session_level_combo.currentTextChanged.connect(
            lambda value: self._emit_config_changed("logging.session.level", value)
        )

        # 환경 변수 변경
        self.env_log_level_combo.currentTextChanged.connect(
            lambda value: self._emit_env_changed("LOG_LEVEL", value)
        )
        self.env_log_format_edit.textChanged.connect(
            lambda value: self._emit_env_changed("LOG_FORMAT", value)
        )
        self.env_log_file_edit.textChanged.connect(
            lambda value: self._emit_env_changed("LOG_FILE", value)
        )
        self.env_pythonpath_edit.textChanged.connect(
            lambda value: self._emit_env_changed("PYTHONPATH", value)
        )

        # 동작 버튼
        self.file_browse_button.clicked.connect(self._browse_log_file)
        self.apply_button.clicked.connect(self._apply_configuration)
        self.reload_button.clicked.connect(self._reload_configuration)
        self.reset_button.clicked.connect(self._reset_to_defaults)
        self.export_button.clicked.connect(self._export_configuration)

    def _setup_event_system(self):
        """Event System 비동기 초기화"""
        QTimer.singleShot(0, self._async_setup_event_system)

    def _async_setup_event_system(self):
        """비동기 Event System 설정"""
        try:
            # Event System 초기화
            self.event_bus, self.domain_publisher = EventSystemInitializer.create_simple_event_system(
                self.db_manager
            )

            # 이벤트 구독
            self._subscribe_to_events()

            # Event Bus 시작
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.event_bus.start())

            self.logger.info("Event System 초기화 완료")

        except Exception as e:
            self.logger.error(f"Event System 초기화 실패: {e}")

    def _subscribe_to_events(self):
        """이벤트 구독"""
        if not self.event_bus:
            return

        try:
            # 로깅 구성 변경 이벤트 구독
            subscription_id = self.event_bus.subscribe(
                event_type="logging.configuration_changed",
                handler=self._handle_configuration_changed_event,
                priority=1
            )
            self._event_subscription_ids.append(subscription_id)

            # 환경 변수 변경 이벤트 구독
            subscription_id = self.event_bus.subscribe(
                event_type="environment.variable_changed",
                handler=self._handle_environment_changed_event,
                priority=1
            )
            self._event_subscription_ids.append(subscription_id)

            self.logger.info(f"이벤트 구독 완료: {len(self._event_subscription_ids)}개 구독")

        except Exception as e:
            self.logger.error(f"이벤트 구독 실패: {e}")

    def _handle_configuration_changed_event(self, event_data: Dict[str, Any]) -> None:
        """구성 변경 이벤트 처리"""
        try:
            data = event_data.get('data', {})
            section = data.get('configuration_section', '')
            config_changes = {
                'old_value': data.get('old_value'),
                'new_value': data.get('new_value'),
                'config_path': data.get('config_path', '')
            }

            # UI 스레드로 신호 전송
            self.configuration_changed.emit(section, config_changes)

        except Exception as e:
            self.logger.error(f"구성 변경 이벤트 처리 실패: {e}")

    def _handle_environment_changed_event(self, event_data: Dict[str, Any]) -> None:
        """환경 변수 변경 이벤트 처리"""
        try:
            data = event_data.get('data', {})
            var_name = data.get('variable_name', '')
            old_value = data.get('old_value', '')
            new_value = data.get('new_value', '')

            # UI 스레드로 신호 전송
            self.environment_changed.emit(var_name, old_value, new_value)

        except Exception as e:
            self.logger.error(f"환경 변수 변경 이벤트 처리 실패: {e}")

    def _load_current_configuration(self):
        """현재 구성 로드"""
        try:
            # ConfigManager에서 로깅 설정 로드
            logging_config = self.config_manager.get_config_section('logging')
            self.current_config = logging_config.copy()

            # UI 컴포넌트에 설정 반영
            self._update_ui_from_config(logging_config)

            # 환경 변수 로드
            env_vars = {
                'LOG_LEVEL': os.environ.get('LOG_LEVEL', ''),
                'LOG_FORMAT': os.environ.get('LOG_FORMAT', ''),
                'LOG_FILE': os.environ.get('LOG_FILE', ''),
                'PYTHONPATH': os.environ.get('PYTHONPATH', '')
            }
            self.current_env_vars = env_vars.copy()

            # UI 컴포넌트에 환경 변수 반영
            self._update_ui_from_env_vars(env_vars)

            self.logger.info("현재 구성 로드 완료")

        except Exception as e:
            self.logger.error(f"구성 로드 실패: {e}")

    def _update_ui_from_config(self, config: Dict[str, Any]):
        """구성에서 UI 업데이트"""
        # 기본 설정
        self.default_level_combo.setCurrentText(config.get('level', 'INFO'))

        format_type = config.get('format_type', 'detailed')
        format_mapping = {
            'simple': '간단한 형식',
            'detailed': '상세한 형식',
            'json': 'JSON 형식',
            'custom': '사용자 정의'
        }
        self.log_format_combo.setCurrentText(format_mapping.get(format_type, '상세한 형식'))

        if format_type == 'custom':
            self.custom_format_edit.setEnabled(True)
            self.custom_format_edit.setText(config.get('custom_format', ''))

        self.date_format_edit.setText(config.get('date_format', '%Y-%m-%d %H:%M:%S'))

        # 핸들러 설정
        handlers = config.get('handlers', {})

        # 콘솔 핸들러
        console = handlers.get('console', {})
        self.console_enabled.setChecked(console.get('enabled', True))
        self.console_level_combo.setCurrentText(console.get('level', 'INFO'))

        # 파일 핸들러
        file_handler = handlers.get('file', {})
        self.file_enabled.setChecked(file_handler.get('enabled', False))
        self.file_level_combo.setCurrentText(file_handler.get('level', 'INFO'))
        self.file_path_edit.setText(file_handler.get('path', 'logs/application.log'))
        self.max_file_size.setValue(file_handler.get('max_size_mb', 10))
        self.backup_count.setValue(file_handler.get('backup_count', 5))

        # 세션 핸들러
        session = handlers.get('session', {})
        self.session_enabled.setChecked(session.get('enabled', False))
        self.session_level_combo.setCurrentText(session.get('level', 'INFO'))

    def _update_ui_from_env_vars(self, env_vars: Dict[str, str]):
        """환경 변수에서 UI 업데이트"""
        self.env_log_level_combo.setCurrentText(env_vars.get('LOG_LEVEL', ''))
        self.env_log_format_edit.setText(env_vars.get('LOG_FORMAT', ''))
        self.env_log_file_edit.setText(env_vars.get('LOG_FILE', ''))
        self.env_pythonpath_edit.setText(env_vars.get('PYTHONPATH', ''))

    def _on_log_format_changed(self, format_text: str):
        """로그 포맷 변경 처리"""
        format_mapping = {
            '간단한 형식': 'simple',
            '상세한 형식': 'detailed',
            'JSON 형식': 'json',
            '사용자 정의': 'custom'
        }

        format_type = format_mapping.get(format_text, 'detailed')
        self.custom_format_edit.setEnabled(format_type == 'custom')

        self._emit_config_changed("logging.format_type", format_type)

    def _emit_config_changed(self, config_path: str, new_value: Any):
        """구성 변경 이벤트 발행"""
        try:
            if self.event_bus:
                # 이전 값 찾기
                old_value = self._get_config_value(config_path)

                if old_value != new_value:
                    event = LogConfigurationChangedEvent(
                        configuration_section=config_path.split('.')[0],
                        old_value=old_value,
                        new_value=new_value,
                        config_path=config_path
                    )

                    # 이벤트 발행
                    asyncio.create_task(self.event_bus.publish(event.to_dict()))

        except Exception as e:
            self.logger.error(f"구성 변경 이벤트 발행 실패: {e}")

    def _emit_env_changed(self, var_name: str, new_value: str):
        """환경 변수 변경 이벤트 발행"""
        try:
            if self.event_bus:
                old_value = self.current_env_vars.get(var_name)

                if old_value != new_value:
                    event = EnvironmentVariableChangedEvent(
                        variable_name=var_name,
                        old_value=old_value,
                        new_value=new_value if new_value else None
                    )

                    # 이벤트 발행
                    asyncio.create_task(self.event_bus.publish(event.to_dict()))

                    # 캐시 업데이트
                    self.current_env_vars[var_name] = new_value

        except Exception as e:
            self.logger.error(f"환경 변수 변경 이벤트 발행 실패: {e}")

    def _get_config_value(self, config_path: str) -> Any:
        """구성 경로에서 현재 값 가져오기"""
        try:
            keys = config_path.split('.')
            value = self.current_config
            for key in keys[1:]:  # 'logging' 제외
                value = value.get(key, {})
            return value
        except:
            return None

    @pyqtSlot(str, dict)
    def _on_configuration_changed(self, section: str, changes: Dict[str, Any]):
        """구성 변경 처리 (UI 스레드)"""
        self.logger.info(f"구성 변경 감지: {section} -> {changes}")
        # TODO: UI 상태 업데이트 또는 알림 표시

    @pyqtSlot(str, str, str)
    def _on_environment_changed(self, var_name: str, old_value: str, new_value: str):
        """환경 변수 변경 처리 (UI 스레드)"""
        self.logger.info(f"환경 변수 변경 감지: {var_name} = '{new_value}'")
        # TODO: UI 상태 업데이트 또는 알림 표시

    def _browse_log_file(self):
        """로그 파일 경로 찾아보기"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "로그 파일 경로 선택",
            self.file_path_edit.text() or "logs/application.log",
            "로그 파일 (*.log);;모든 파일 (*.*)"
        )

        if file_path:
            self.file_path_edit.setText(file_path)

    def _apply_configuration(self):
        """설정 적용"""
        try:
            # 현재 UI 상태를 구성으로 변환
            new_config = self._collect_ui_configuration()

            # ConfigManager를 통해 설정 업데이트
            self.config_manager.update_config_section('logging', new_config)

            # 환경 변수 적용
            env_vars = self._collect_ui_environment_variables()
            for var_name, value in env_vars.items():
                if value:
                    os.environ[var_name] = value
                elif var_name in os.environ:
                    del os.environ[var_name]

            # Infrastructure Layer에 변경사항 전파
            self._apply_dynamic_logging_changes(new_config)

            QMessageBox.information(self, "설정 적용", "로깅 설정이 성공적으로 적용되었습니다.")
            self.logger.info("로깅 설정 적용 완료")

        except Exception as e:
            error_msg = f"설정 적용 실패: {e}"
            QMessageBox.critical(self, "오류", error_msg)
            self.logger.error(error_msg)

    def _collect_ui_configuration(self) -> Dict[str, Any]:
        """UI에서 구성 수집"""
        format_mapping = {
            '간단한 형식': 'simple',
            '상세한 형식': 'detailed',
            'JSON 형식': 'json',
            '사용자 정의': 'custom'
        }

        config = {
            'level': self.default_level_combo.currentText(),
            'format_type': format_mapping.get(self.log_format_combo.currentText(), 'detailed'),
            'date_format': self.date_format_edit.text() or '%Y-%m-%d %H:%M:%S',
            'handlers': {
                'console': {
                    'enabled': self.console_enabled.isChecked(),
                    'level': self.console_level_combo.currentText()
                },
                'file': {
                    'enabled': self.file_enabled.isChecked(),
                    'level': self.file_level_combo.currentText(),
                    'path': self.file_path_edit.text() or 'logs/application.log',
                    'max_size_mb': self.max_file_size.value(),
                    'backup_count': self.backup_count.value()
                },
                'session': {
                    'enabled': self.session_enabled.isChecked(),
                    'level': self.session_level_combo.currentText()
                }
            }
        }

        if config['format_type'] == 'custom':
            config['custom_format'] = self.custom_format_edit.text()

        return config

    def _collect_ui_environment_variables(self) -> Dict[str, str]:
        """UI에서 환경 변수 수집"""
        return {
            'LOG_LEVEL': self.env_log_level_combo.currentText(),
            'LOG_FORMAT': self.env_log_format_edit.text(),
            'LOG_FILE': self.env_log_file_edit.text(),
            'PYTHONPATH': self.env_pythonpath_edit.text()
        }

    def _apply_dynamic_logging_changes(self, new_config: Dict[str, Any]):
        """동적 로깅 변경사항 적용"""
        try:
            # Infrastructure Layer의 로깅 시스템에 변경사항 전파
            from upbit_auto_trading.infrastructure.logging import get_logging_system
            logging_system = get_logging_system()

            if hasattr(logging_system, 'update_configuration'):
                logging_system.update_configuration(new_config)
                self.logger.info("Infrastructure Layer 로깅 구성 업데이트 완료")

        except Exception as e:
            self.logger.error(f"동적 로깅 변경사항 적용 실패: {e}")

    def _reload_configuration(self):
        """설정 재로드"""
        try:
            self._load_current_configuration()
            QMessageBox.information(self, "설정 재로드", "설정이 다시 로드되었습니다.")
            self.logger.info("설정 재로드 완료")

        except Exception as e:
            error_msg = f"설정 재로드 실패: {e}"
            QMessageBox.critical(self, "오류", error_msg)
            self.logger.error(error_msg)

    def _reset_to_defaults(self):
        """기본값 복원"""
        try:
            # 기본 설정으로 복원
            default_config = {
                'level': 'INFO',
                'format_type': 'detailed',
                'date_format': '%Y-%m-%d %H:%M:%S',
                'handlers': {
                    'console': {'enabled': True, 'level': 'INFO'},
                    'file': {'enabled': False, 'level': 'INFO', 'path': 'logs/application.log', 'max_size_mb': 10, 'backup_count': 5},
                    'session': {'enabled': False, 'level': 'INFO'}
                }
            }

            self._update_ui_from_config(default_config)

            # 환경 변수 클리어
            env_vars = {'LOG_LEVEL': '', 'LOG_FORMAT': '', 'LOG_FILE': '', 'PYTHONPATH': ''}
            self._update_ui_from_env_vars(env_vars)

            QMessageBox.information(self, "기본값 복원", "설정이 기본값으로 복원되었습니다.")
            self.logger.info("기본값 복원 완료")

        except Exception as e:
            error_msg = f"기본값 복원 실패: {e}"
            QMessageBox.critical(self, "오류", error_msg)
            self.logger.error(error_msg)

    def _export_configuration(self):
        """설정 내보내기"""
        try:
            config = self._collect_ui_configuration()

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "로깅 설정 내보내기",
                "logging_config.yaml",
                "YAML 파일 (*.yaml *.yml);;JSON 파일 (*.json);;모든 파일 (*.*)"
            )

            if file_path:
                import yaml
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump({'logging': config}, f, allow_unicode=True, default_flow_style=False)

                QMessageBox.information(self, "내보내기 완료", f"설정이 {file_path}에 저장되었습니다.")
                self.logger.info(f"설정 내보내기 완료: {file_path}")

        except Exception as e:
            error_msg = f"설정 내보내기 실패: {e}"
            QMessageBox.critical(self, "오류", error_msg)
            self.logger.error(error_msg)

    def closeEvent(self, event):
        """위젯 종료 시 정리"""
        try:
            # 이벤트 구독 해제
            if self.event_bus and self._event_subscription_ids:
                for subscription_id in self._event_subscription_ids:
                    asyncio.create_task(self.event_bus.unsubscribe(subscription_id))

            self.logger.info("Event-Driven 로깅 구성 섹션 정리 완료")

        except Exception as e:
            self.logger.error(f"위젯 정리 실패: {e}")

        super().closeEvent(event)
