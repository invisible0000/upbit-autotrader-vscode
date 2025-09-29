"""
실시간 로깅 관리 탭 - MVP Passive View
====================================

DDD Presentation Layer - PyQt6 UI (표시만, Passive View)
3-위젯 아키텍처로 구성된 로깅 관리 인터페이스

주요 특징:
- MVP 패턴 Passive View (순수 UI 관심사만)
- 3-위젯 구조: 좌측 설정 | 우측 상단 로그뷰어 | 우측 하단 콘솔뷰어
- Config 파일 기반 설정 시스템 (환경변수 시스템 완전 대체)
- 전역 스타일 관리 시스템 준수
- 실시간 설정 반영 및 UI 프리징 방지
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt, pyqtSignal

# 3개 위젯 컴포넌트 임포트
from .widgets.logging_settings_widget import LoggingSettingsWidget
from .widgets.log_viewer_widget import LogViewerWidget
from .widgets.console_viewer_widget import ConsoleViewerWidget
from .presenters.logging_management_presenter import LoggingManagementPresenter

# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)


class LoggingManagementView(QWidget):
    """실시간 로깅 관리 탭 - MVP Passive View with 3-Widget Architecture"""

    # MVP 패턴: Presenter로 전달할 시그널들
    settings_changed = pyqtSignal(dict)  # 설정 변경 시그널
    apply_settings_requested = pyqtSignal()  # 설정 적용 요청
    reset_settings_requested = pyqtSignal()  # 설정 리셋 요청

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logging-management-view")

        # Infrastructure 로깅
        self.logger = create_component_logger("LoggingManagementView")
        self.logger.info("🎛️ 로깅 관리 뷰 초기화 시작")

        # MVP 패턴: Presenter 생성 및 연결
        self.presenter = LoggingManagementPresenter()
        self.presenter.set_view(self)

        self._setup_ui()
        self._connect_signals()
        self._connect_presenter_signals()

        self.logger.info("✅ 로깅 관리 뷰 초기화 완료 - 3-위젯 아키텍처")

    def _setup_ui(self):
        """3-위젯 아키텍처 UI 레이아웃 구성"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 메인 수평 스플리터 (좌측:우측 = 1:2)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)  # 위젯 완전 숨김 방지

        # 좌측: 로깅 설정 위젯
        self.logging_settings_widget = LoggingSettingsWidget()
        self.logging_settings_widget.setMinimumWidth(280)  # 최소 폭 보장
        # 최대 폭 제한 제거하여 윈도우 크기에 비례하도록 함

        # 우측: 수직 스플리터 (상단:하단 = 2:1)
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.right_splitter.setChildrenCollapsible(False)

        # 우측 상단: 로그 뷰어 위젯
        self.log_viewer_widget = LogViewerWidget()
        self.log_viewer_widget.setMinimumHeight(200)  # 최소 높이 보장

        # 우측 하단: 콘솔 뷰어 위젯
        self.console_viewer_widget = ConsoleViewerWidget()
        self.console_viewer_widget.setMinimumHeight(150)  # 최소 높이 보장

        # 우측 스플리터에 위젯 추가 (상단:하단 = 2:1)
        self.right_splitter.addWidget(self.log_viewer_widget)
        self.right_splitter.addWidget(self.console_viewer_widget)
        self.right_splitter.setSizes([400, 200])  # 2:1 비율 (600 기준)
        self.right_splitter.setStretchFactor(0, 2)  # 로그 뷰어가 더 많은 공간
        self.right_splitter.setStretchFactor(1, 1)  # 콘솔 뷰어

        # 메인 스플리터에 추가 (좌측:우측 = 1:2.5 → 더 유연한 비율)
        self.main_splitter.addWidget(self.logging_settings_widget)
        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setSizes([280, 700])  # 기본 크기: 280px + 700px = 980px
        self.main_splitter.setStretchFactor(0, 1)  # 설정 위젯: 비례 확장
        self.main_splitter.setStretchFactor(1, 3)  # 뷰어 영역: 3배 더 확장

        layout.addWidget(self.main_splitter)
        self.setLayout(layout)

        self.logger.debug("🎛️ 3-위젯 레이아웃 구성 완료: 1:3(유연한 수평) × 2:1(수직)")

    def _connect_signals(self):
        """위젯 간 시그널 연결 - MVP 패턴 준수"""

        # 로깅 설정 위젯 → 메인 뷰 (Presenter로 전달)
        self.logging_settings_widget.apply_settings.connect(self.apply_settings_requested.emit)
        self.logging_settings_widget.reset_settings.connect(self.reset_settings_requested.emit)

        # 개별 설정 변경 시그널들을 dict로 변환하여 전달
        self.logging_settings_widget.context_changed.connect(
            lambda value: self.settings_changed.emit({"context": value})
        )
        self.logging_settings_widget.log_level_changed.connect(
            lambda value: self.settings_changed.emit({"log_level": value})
        )
        self.logging_settings_widget.console_output_changed.connect(
            lambda value: self.settings_changed.emit({"console_output": value})
        )
        self.logging_settings_widget.log_scope_changed.connect(
            lambda value: self.settings_changed.emit({"log_scope": value})
        )
        self.logging_settings_widget.component_focus_changed.connect(
            lambda value: self.settings_changed.emit({"component_focus": value})
        )
        self.logging_settings_widget.file_logging_changed.connect(
            lambda value: self.settings_changed.emit({"file_logging_enabled": value})
        )
        self.logging_settings_widget.file_path_changed.connect(
            lambda value: self.settings_changed.emit({"file_path": value})
        )
        self.logging_settings_widget.file_log_level_changed.connect(
            lambda value: self.settings_changed.emit({"file_log_level": value})
        )
        self.logging_settings_widget.performance_monitoring_changed.connect(
            lambda value: self.settings_changed.emit({"performance_monitoring": value})
        )

        # UX 개선 시그널 연결
        self.logging_settings_widget.reload_requested.connect(
            lambda: self.presenter.load_current_config()
        )

        self.logger.debug("🔗 위젯 간 시그널 연결 완료 - MVP 패턴")

    def _connect_presenter_signals(self):
        """프레젠터와의 시그널 연결 - Phase 5.1 실시간 로그 스트리밍"""
        # Presenter → View 시그널 연결
        self.presenter.config_loaded.connect(self.update_settings_display)
        self.presenter.log_content_updated.connect(self.append_log_message)
        self.presenter.console_output_updated.connect(self.append_console_output)

        # View → Presenter 시그널 연결
        self.apply_settings_requested.connect(
            lambda: self.presenter.save_config(self.get_current_settings())
        )
        self.reset_settings_requested.connect(self.presenter.reset_to_defaults)

        # 초기 설정 로드
        self.presenter.load_current_config()

        # Phase 5.2: 실시간 모니터링 시작 (초기 로그 로딩 포함)
        self.presenter.start_real_time_monitoring()

        self.logger.debug("🔗 프레젠터 시그널 연결 완료 - 실시간 로그 스트리밍 활성화")

    # ===== MVP Passive View 인터페이스 =====
    # Presenter에서 호출할 메서드들

    def update_settings_display(self, settings: dict):
        """설정 값들을 UI에 반영 (Presenter → View)"""
        self.logger.debug(f"🔄 설정 표시 업데이트: {settings}")
        self.logging_settings_widget.update_from_settings(settings)

    def get_current_settings(self) -> dict:
        """현재 UI 설정 값들 반환 (View → Presenter)"""
        return self.logging_settings_widget.get_current_settings()

    def append_log_message(self, message: str):
        """로그 메시지 추가 (Presenter → View)"""
        self.log_viewer_widget.append_log_message(message)

    def append_console_output(self, output: str, is_error: bool = False):
        """콘솔 출력 추가 (Presenter → View)"""
        self.console_viewer_widget.append_console_output(output, is_error)  # type: ignore[attr-defined]

    def clear_log_viewer(self):
        """로그 뷰어 클리어 (Presenter → View)"""
        self.log_viewer_widget.clear_log_viewer()

    def clear_console_viewer(self):
        """콘솔 뷰어 클리어 (Presenter → View)"""
        self.console_viewer_widget.clear_console_viewer()  # type: ignore[attr-defined]
        # Presenter의 버퍼도 초기화
        try:
            self.presenter.clear_console_buffer()
        except Exception:
            pass

    def show_status_message(self, message: str, level: str = "info"):
        """상태 메시지 표시 (Presenter → View)"""
        # 상태바가 있다면 여기서 처리, 현재는 로그로 대체
        if level == "error":
            self.logger.error(f"❌ {message}")
        elif level == "warning":
            self.logger.warning(f"⚠️ {message}")
        else:
            self.logger.info(f"ℹ️ {message}")

    def get_splitter_sizes(self) -> tuple:
        """스플리터 크기 반환 (상태 저장용)"""
        main_sizes = self.main_splitter.sizes()
        right_sizes = self.right_splitter.sizes()
        return (main_sizes, right_sizes)

    def set_splitter_sizes(self, main_sizes: list, right_sizes: list):
        """스플리터 크기 설정 (상태 복원용)"""
        if main_sizes:
            self.main_splitter.setSizes(main_sizes)
        if right_sizes:
            self.right_splitter.setSizes(right_sizes)
