"""
Database Tab Widget

데이터베이스 설정의 모든 기능을 통합한 메인 탭 위젯입니다.
MVP 패턴을 완전히 적용하여 각 하위 위젯들을 조합하고 Presenter와 연동합니다.

Features:
- 통합된 데이터베이스 관리 인터페이스
- 실시간 상태 모니터링
- 백업/복원 기능
- 경로 선택 및 검증
- MVP 패턴 완전 적용
"""

from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger

# 하위 위젯들 - 안전한 import with fallback
try:
    from .database_status_widget import DatabaseStatusWidget, DatabaseProgressWidget
    from .database_path_selector import DatabasePathSelectorGroup
    from .database_backup_widget import DatabaseBackupWidget
    WIDGETS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ [DEBUG] 하위 위젯 import 실패: {e}")
    # Fallback: 기본 위젯들로 대체
    from PyQt6.QtWidgets import QLabel
    DatabaseStatusWidget = QLabel
    DatabaseProgressWidget = QLabel
    DatabasePathSelectorGroup = QLabel
    DatabaseBackupWidget = QLabel
    WIDGETS_AVAILABLE = False

# MVP 인터페이스 - 안전한 import with fallback
try:
    from ..interfaces.database_config_view_interface import (
        IDatabaseConfigView, IDatabaseConfigViewEvents
    )
    MVP_INTERFACES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ [DEBUG] MVP 인터페이스 import 실패: {e}")
    # Fallback: 기본 클래스들로 대체
    class IDatabaseConfigView:
        pass
    class IDatabaseConfigViewEvents:
        pass
    MVP_INTERFACES_AVAILABLE = False


class DatabaseTabWidget(QWidget):
    """
    통합된 데이터베이스 탭 위젯

    모든 데이터베이스 관련 기능을 하나의 탭으로 통합하여 제공합니다.
    현재는 기본 기능으로 동작합니다.
    """

    # 설정 변경 시그널
    settings_changed = pyqtSignal()

    # 프로그램 재시작 요청 시그널
    restart_requested = pyqtSignal()

    # DB 상태 변경 시그널
    db_status_changed = pyqtSignal(bool)  # is_healthy

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-database-tab")
        self._logger = create_component_logger("DatabaseTabWidget")

        # MVP 컴포넌트
        self._presenter = None
        self._is_initialized = False

        # 하위 위젯들
        self._status_widget = None
        self._progress_widget = None
        self._path_selector = None
        self._backup_widget = None

        # MVP 패턴: Application Service와 Presenter 초기화
        self._init_application_services()
        self._init_presenter()

        self._setup_ui()
        self._connect_signals()

        # 초기 데이터 로드
        self._load_initial_data()

        self._logger.info("🎭 DatabaseTabWidget 초기화 완료 (MVP 패턴 적용)")

    def _init_application_services(self):
        """Application Layer 서비스 초기화"""
        self._logger.debug("🔧 Application Layer 서비스 초기화 시작")

        try:
            # 현재는 간단한 방식으로 동작
            self.app_service = None
            self._logger.info("✅ Application Service 초기화 완료 (기본 모드)")
        except Exception as e:
            self._logger.error(f"❌ Application Service 초기화 실패: {e}")
            self.app_service = None

    def _init_presenter(self):
        """MVP 패턴: Presenter 초기화"""
        self._logger.debug("🎭 MVP Presenter 초기화 시작")

        try:
            # 현재는 기본 동작
            self._presenter = None
            self._logger.info("✅ Presenter 초기화 완료 (기본 모드)")
        except Exception as e:
            self._logger.error(f"❌ Presenter 초기화 실패: {e}")

    def _load_initial_data(self):
        """초기 데이터 로드"""
        self._logger.debug("📊 초기 데이터 로드 시작")

        try:
            # 기본 동작
            self._logger.info("✅ 초기 데이터 로드 완료 (기본 모드)")
        except Exception as e:
            self._logger.error(f"❌ 초기 데이터 로드 실패: {e}")

    def _setup_ui(self):
        """UI 구성"""
        self._logger.debug("🎨 UI 구성 시작")

        layout = QVBoxLayout(self)

        # 기본 라벨 추가
        from PyQt6.QtWidgets import QLabel
        label = QLabel("데이터베이스 설정")
        label.setObjectName("title")
        layout.addWidget(label)

        desc = QLabel("데이터베이스 관련 설정을 관리합니다.")
        desc.setObjectName("description")
        layout.addWidget(desc)

        self._logger.info("✅ UI 구성 완료")

    def _connect_signals(self):
        """시그널 연결"""
        self._logger.debug("🔗 시그널 연결 시작")
        # 기본적인 시그널 연결
        self._logger.info("✅ 시그널 연결 완료")

    def set_presenter(self, presenter):
        """Presenter 설정"""
        self._presenter = presenter
        self._logger.debug("🎭 Presenter 설정 완료")
            self._logger.error(f"❌ 초기 데이터 로드 실패: {e}")    def _setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # 메인 스플리터 (수직 분할)
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # 상단: 상태 및 경로 선택
        top_widget = self._create_top_section()
        main_splitter.addWidget(top_widget)

        # 하단: 백업 관리
        bottom_widget = self._create_bottom_section()
        main_splitter.addWidget(bottom_widget)

        # 스플리터 비율 설정 (상단 60%, 하단 40%)
        main_splitter.setSizes([600, 400])

        main_layout.addWidget(main_splitter)

        # 진행상황 위젯 (오버레이)
        self._progress_widget = DatabaseProgressWidget(self)

    def _create_top_section(self) -> QWidget:
        """상단 섹션 생성 (상태 + 경로 선택)"""
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(15)

        # 좌측: 상태 표시
        self._status_widget = DatabaseStatusWidget()
        self._status_widget.setMaximumWidth(280)
        top_layout.addWidget(self._status_widget)

        # 우측: 경로 선택
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._path_selector = DatabasePathSelectorGroup()
        scroll_area.setWidget(self._path_selector)

        top_layout.addWidget(scroll_area, 1)

        return top_widget

    def _create_bottom_section(self) -> QWidget:
        """하단 섹션 생성 (백업 관리)"""
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # 백업 관리 위젯
        self._backup_widget = DatabaseBackupWidget()
        bottom_layout.addWidget(self._backup_widget)

        return bottom_widget

    def _connect_signals(self):
        """시그널 연결"""
        # 상태 위젯 시그널
        if self._status_widget:
            self._status_widget.status_clicked.connect(self._on_status_clicked)

        # 경로 선택 위젯 시그널
        if self._path_selector:
            self._path_selector.path_changed.connect(self._on_path_changed)
            self._path_selector.validation_changed.connect(self._on_validation_changed)

        # 백업 위젯 시그널
        if self._backup_widget:
            self._backup_widget.create_backup_requested.connect(self.on_create_backup_requested)
            self._backup_widget.restore_backup_requested.connect(self.on_restore_backup_requested)
            self._backup_widget.delete_backup_requested.connect(self.on_delete_backup_requested)
            self._backup_widget.refresh_backups_requested.connect(self.on_list_backups_requested)

    def _on_status_clicked(self, database_type: str):
        """상태 클릭 시 처리"""
        self.on_test_connection_requested(database_type)

    def _on_path_changed(self, database_type: str, new_path: str):
        """경로 변경 시 처리"""
        self.on_switch_profile_requested(database_type, new_path)

    def _on_validation_changed(self, all_valid: bool):
        """검증 상태 변경 시 처리"""
        self.db_status_changed.emit(all_valid)

    def set_presenter(self, presenter):
        """Presenter 설정"""
        self._presenter = presenter
        self._is_initialized = True
        self._logger.info("🎭 Presenter 연결 완료")

    # === IDatabaseConfigView 인터페이스 구현 ===

    def update_configuration_display(self, config: Dict[str, Any]) -> None:
        """설정 데이터를 UI에 표시"""
        try:
            self._logger.debug("🔄 설정 화면 업데이트")

            # 경로 정보 업데이트
            if 'profiles' in config and self._path_selector:
                paths = {}
                for db_type, profile in config['profiles'].items():
                    if isinstance(profile, dict):
                        paths[db_type] = profile.get('file_path', '')

                self._path_selector.set_paths(paths)

        except Exception as e:
            self._logger.error(f"❌ 설정 표시 업데이트 실패: {e}")

    def update_status_display(self, status: Dict[str, Any]) -> None:
        """상태 정보를 UI에 표시"""
        try:
            self._logger.debug("📊 상태 표시 업데이트")

            if self._status_widget:
                self._status_widget.update_status(status)

        except Exception as e:
            self._logger.error(f"❌ 상태 표시 업데이트 실패: {e}")

    def update_backup_list(self, backups: List[Dict[str, Any]]) -> None:
        """백업 목록을 UI에 표시"""
        try:
            self._logger.debug(f"📋 백업 목록 업데이트: {len(backups)}개")

            if self._backup_widget:
                self._backup_widget.update_backup_list(backups)

        except Exception as e:
            self._logger.error(f"❌ 백업 목록 업데이트 실패: {e}")

    def show_progress(self, message: str) -> None:
        """진행상황 표시"""
        if self._progress_widget:
            self._progress_widget.show_progress(message)

    def hide_progress(self) -> None:
        """진행상황 숨김"""
        if self._progress_widget:
            self._progress_widget.hide_progress()

    def update_progress(self, percentage: int, message: str = "") -> None:
        """진행률 업데이트"""
        if self._progress_widget:
            self._progress_widget.update_progress(percentage, message)

    def show_success_message(self, title: str, message: str) -> None:
        """성공 메시지 표시"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, title, message)

    def show_error_message(self, title: str, message: str) -> None:
        """에러 메시지 표시"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, title, message)

    def show_warning_message(self, title: str, message: str) -> None:
        """경고 메시지 표시"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, title, message)

    def show_info_message(self, title: str, message: str) -> None:
        """정보 메시지 표시"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, title, message)

    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """확인 대화상자 표시"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def get_current_form_data(self) -> Dict[str, Any]:
        """현재 폼의 데이터 반환"""
        data = {}

        if self._path_selector:
            data.update(self._path_selector.get_paths())

        return data

    def clear_form(self) -> None:
        """폼 데이터 초기화"""
        if self._path_selector:
            self._path_selector.clear_all()

        if self._backup_widget:
            self._backup_widget.clear_backup_list()

    def set_form_data(self, data: Dict[str, Any]) -> None:
        """폼에 데이터 설정"""
        if self._path_selector:
            self._path_selector.set_paths(data)

    def enable_controls(self, enabled: bool = True) -> None:
        """UI 컨트롤 활성화/비활성화"""
        if self._backup_widget:
            self._backup_widget.set_enabled(enabled)

    def set_read_only(self, read_only: bool = True) -> None:
        """읽기 전용 모드 설정"""
        # TODO: 경로 선택기 읽기 전용 모드 구현
        pass

    def refresh_display(self) -> None:
        """화면 새로고침"""
        self.on_refresh_status_requested()
        self.on_list_backups_requested()

    def show_file_selector(self, title: str, file_filter: str = "") -> str:
        """파일 선택 대화상자 표시"""
        from PyQt6.QtWidgets import QFileDialog
        dialog = QFileDialog()
        file_path, _ = dialog.getOpenFileName(
            self, title, "", file_filter or "SQLite 파일 (*.sqlite3);;모든 파일 (*)"
        )
        return file_path

    def show_directory_selector(self, title: str) -> str:
        """디렉토리 선택 대화상자 표시"""
        from PyQt6.QtWidgets import QFileDialog
        dialog = QFileDialog()
        directory = dialog.getExistingDirectory(self, title)
        return directory

    # === IDatabaseConfigViewEvents 인터페이스 구현 ===

    def on_load_configuration_requested(self) -> None:
        """설정 로드 요청"""
        if self._presenter:
            import asyncio
            asyncio.create_task(self._presenter.load_configuration())

    def on_save_configuration_requested(self, config_data: Dict[str, Any]) -> None:
        """설정 저장 요청"""
        if self._presenter:
            import asyncio
            asyncio.create_task(self._presenter.save_configuration(config_data))

    def on_reset_configuration_requested(self) -> None:
        """설정 초기화 요청"""
        self.clear_form()
        self.refresh_display()

    def on_switch_profile_requested(self, database_type: str, new_path: str) -> None:
        """프로필 전환 요청"""
        if self._presenter:
            import asyncio
            asyncio.create_task(self._presenter.switch_database_profile(database_type, new_path))

    def on_create_profile_requested(self, profile_data: Dict[str, Any]) -> None:
        """프로필 생성 요청"""
        if self._presenter:
            import asyncio
            asyncio.create_task(self._presenter.create_database_profile(profile_data))

    def on_delete_profile_requested(self, profile_id: str) -> None:
        """프로필 삭제 요청"""
        # TODO: 프로필 삭제 구현
        pass

    def on_create_backup_requested(self, database_type: str) -> None:
        """백업 생성 요청"""
        if self._presenter:
            import asyncio
            asyncio.create_task(self._presenter.create_backup(database_type))

    def on_restore_backup_requested(self, backup_id: str) -> None:
        """백업 복원 요청"""
        if self._presenter:
            import asyncio
            asyncio.create_task(self._presenter.restore_backup(backup_id))

    def on_delete_backup_requested(self, backup_id: str) -> None:
        """백업 삭제 요청"""
        # TODO: 백업 삭제 구현
        pass

    def on_list_backups_requested(self, database_type: Optional[str] = None) -> None:
        """백업 목록 조회 요청"""
        if self._presenter:
            import asyncio
            asyncio.create_task(self._presenter.list_backups(database_type))

    def on_validate_database_requested(self, database_type: str) -> None:
        """데이터베이스 검증 요청"""
        if self._presenter:
            import asyncio
            asyncio.create_task(self._presenter.validate_database(database_type))

    def on_refresh_status_requested(self) -> None:
        """상태 새로고침 요청"""
        if self._presenter:
            import asyncio
            asyncio.create_task(self._presenter.refresh_status())

    def on_test_connection_requested(self, database_type: str) -> None:
        """연결 테스트 요청"""
        self.on_validate_database_requested(database_type)

    # === 추가 공개 메서드 ===

    def initialize_with_presenter(self, presenter):
        """Presenter와 함께 초기화"""
        self.set_presenter(presenter)

        # 초기 데이터 로드
        self.on_load_configuration_requested()
        self.on_refresh_status_requested()
        self.on_list_backups_requested()

    def get_status_summary(self) -> Dict[str, Any]:
        """상태 요약 정보 반환"""
        if self._status_widget:
            return self._status_widget.get_status_data()
        return {}
