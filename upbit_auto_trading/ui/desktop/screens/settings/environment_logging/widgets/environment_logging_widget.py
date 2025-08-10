"""
Event-Driven Environment Logging Widget
=======================================

Event-Driven Architecture로 전환된 환경 프로파일과 로깅 설정, 로그 뷰어 통합 위젯
3열 1:1:1 분할 레이아웃으로 사용성 최적화

Features:
- Environment Profile Management (left 33%)
- Event-Driven Logging Configuration (center 33%)
- Real-time Event-Driven Log Viewer (right 33%)
- Event-driven environment switching
- Infrastructure Layer v4.0 + Event System integration
- MVP Pattern implementation with Event-Driven Architecture
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QSplitter, QVBoxLayout,
    QLabel, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .environment_profile_section import EnvironmentProfileSection


class EnvironmentLoggingWidget(QWidget):
    """
    환경&로깅 통합 설정 위젯

    3열 1:1:1 분할로 환경 프로파일, 로깅 설정, 로그 뷰어를 동시 관리
    MVP 패턴을 적용하여 View 역할만 담당
    """

    # MVP 시그널 정의
    environment_switch_requested = pyqtSignal(str)  # 환경 전환 요청
    logging_config_changed = pyqtSignal(str, str)   # 로깅 설정 변경 (key, value)
    environment_logging_sync_requested = pyqtSignal(str)  # 환경-로깅 동기화

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("EnvironmentLoggingWidget")

        # Infrastructure 로깅 초기화
        self._logger = create_component_logger("EnvironmentLoggingWidget")
        self._logger.info("🌍 환경&로깅 통합 위젯 초기화 시작")

        # 내부 상태
        self._current_environment = "Development"

        self._setup_ui()
        self._connect_signals()

        self._logger.info("✅ 환경&로깅 통합 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 구성 - 3열 1:1:1 분할 레이아웃"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 헤더 (선택적)
        self._create_header_section(layout)

        # 메인 분할 레이아웃
        self._create_main_splitter(layout)

    def _create_header_section(self, parent_layout: QVBoxLayout):
        """헤더 섹션 (제목 및 설명)"""
        header_frame = QFrame()
        header_frame.setObjectName("environment-logging-header")
        header_frame.setMaximumHeight(60)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 8, 16, 8)

        # 제목
        title_label = QLabel("🌍 환경 & 로깅 설정")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(title_label)

        # 설명
        desc_label = QLabel("환경 프로파일, 로깅 설정, 실시간 로그를 통합 관리합니다")
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        header_layout.addWidget(desc_label)

        parent_layout.addWidget(header_frame)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setObjectName("header-separator")
        parent_layout.addWidget(line)

    def _create_main_splitter(self, parent_layout: QVBoxLayout):
        """메인 분할 레이아웃 (1:1:1 3열 비율)"""
        # QSplitter 생성
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setObjectName("main-environment-logging-splitter")

        # 좌측: 환경 프로파일 섹션 (33%)
        self.environment_section = EnvironmentProfileSection()
        self.environment_section.setObjectName("environment-profile-section")

        # 중앙: 로깅 설정 섹션 (33%)
        from .logging_configuration_section import LoggingConfigurationSection
        self.logging_section = LoggingConfigurationSection()
        self.logging_section.setObjectName("logging-configuration-section")

        # 우측: 실시간 로그 뷰어 (33%) - 필요 시 시작
        from .log_viewer_widget import LogViewerWidget
        self.log_viewer_section = LogViewerWidget()
        self.log_viewer_section.setObjectName("log-viewer-section")

        # 로그 뷰어는 처음에는 비활성화 상태로 시작
        self._log_viewer_activated = False

        # 스플리터에 추가
        self.main_splitter.addWidget(self.environment_section)
        self.main_splitter.addWidget(self.logging_section)
        self.main_splitter.addWidget(self.log_viewer_section)

        # 1:1:1 비율 설정
        self.main_splitter.setSizes([333, 333, 334])  # 상대 비율

        # 최소 크기 설정
        self.main_splitter.setChildrenCollapsible(False)
        self.environment_section.setMinimumWidth(250)
        self.logging_section.setMinimumWidth(250)
        self.log_viewer_section.setMinimumWidth(250)

        # 스플리터 핸들 스타일링
        self.main_splitter.setHandleWidth(3)
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #ddd;
                border: 1px solid #ccc;
            }
            QSplitter::handle:hover {
                background-color: #4CAF50;
            }
        """)

        parent_layout.addWidget(self.main_splitter)

    def _connect_signals(self):
        """시그널 연결"""
        # 환경 프로파일 섹션 시그널
        self.environment_section.environment_switch_requested.connect(
            self._on_environment_switch_requested
        )

        # 로깅 설정 섹션 시그널
        self.logging_section.logging_config_changed.connect(
            self._on_logging_config_changed
        )

        # 환경 변경 시 로깅 설정 동기화
        self.environment_section.environment_switch_requested.connect(
            self._on_environment_logging_sync_needed
        )

        # 로그 뷰어에 로그 엔트리 전달 (향후 구현)
        # self.logging_section과 self.log_viewer_section 간 연동

    def _on_environment_switch_requested(self, environment_name: str):
        """환경 전환 요청 처리"""
        self._logger.info(f"🔄 환경 전환 요청: {self._current_environment} → {environment_name}")

        # 현재 환경 업데이트
        self._current_environment = environment_name

        # 상위로 전파
        self.environment_switch_requested.emit(environment_name)

        # 로깅 섹션에 환경 변경 알림
        self.logging_section.on_environment_changed(environment_name)

    def _on_logging_config_changed(self, key: str, value: str):
        """로깅 설정 변경 처리"""
        self._logger.debug(f"🔧 로깅 설정 변경: {key} = {value}")

        # 상위로 전파
        self.logging_config_changed.emit(key, value)

    def _on_environment_logging_sync_needed(self, environment_name: str):
        """환경-로깅 동기화 요청"""
        self._logger.info(f"🔄 환경-로깅 동기화: {environment_name}")

        # 상위로 전파 (Presenter에서 처리)
        self.environment_logging_sync_requested.emit(environment_name)

    # === MVP View 인터페이스 ===

    def set_current_environment(self, environment_name: str):
        """현재 환경 설정"""
        self._current_environment = environment_name

        # 환경 섹션 업데이트
        self.environment_section.set_current_environment(environment_name)

        # 로깅 섹션 업데이트
        self.logging_section.on_environment_changed(environment_name)

        self._logger.info(f"📊 현재 환경 설정: {environment_name}")

    def update_logging_config(self, config: dict):
        """로깅 설정 업데이트"""
        self.logging_section.update_config(config)
        self._logger.debug(f"🔧 로깅 설정 업데이트: {len(config)} 항목")

    def show_environment_switch_success(self, environment_name: str):
        """환경 전환 성공 표시"""
        self.environment_section.show_environment_switch_success(environment_name)

    def show_environment_switch_error(self, error_message: str):
        """환경 전환 실패 표시"""
        self.environment_section.show_environment_switch_error(error_message)

    def get_current_environment(self) -> str:
        """현재 환경 반환"""
        return self._current_environment

    def get_logging_config(self) -> dict:
        """현재 로깅 설정 반환"""
        return self.logging_section.get_current_config()

    def enable_widgets(self, enabled: bool):
        """위젯 활성화/비활성화"""
        self.environment_section.enable_widgets(enabled)
        self.logging_section.enable_widgets(enabled)
        # 로그 뷰어는 항상 활성화 상태 유지

    def get_splitter_sizes(self) -> list:
        """스플리터 크기 반환"""
        return self.main_splitter.sizes()

    def set_splitter_sizes(self, sizes: list):
        """스플리터 크기 설정"""
        self.main_splitter.setSizes(sizes)

    def activate_log_viewer(self):
        """로그 뷰어 활성화 (탭이 표시될 때 호출)"""
        if not self._log_viewer_activated:
            self._logger.info("🔍 로그 뷰어 활성화 시작...")

            # 로그 뷰어에 활성화 신호 전송
            if hasattr(self.log_viewer_section, 'start_monitoring'):
                self.log_viewer_section.start_monitoring()

            self._log_viewer_activated = True
            self._logger.info("✅ 로그 뷰어 활성화 완료")

    def deactivate_log_viewer(self):
        """로그 뷰어 비활성화 (탭이 숨겨질 때 호출)"""
        if self._log_viewer_activated:
            self._logger.info("🛑 로그 뷰어 비활성화...")

            # 로그 뷰어에 비활성화 신호 전송
            if hasattr(self.log_viewer_section, 'stop_monitoring'):
                self.log_viewer_section.stop_monitoring()

            self._log_viewer_activated = False
            self._logger.info("✅ 로그 뷰어 비활성화 완료")
