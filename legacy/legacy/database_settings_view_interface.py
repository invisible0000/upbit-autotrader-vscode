"""
데이터베이스 설정 View Interface

MVP 패턴의 View 계약을 정의합니다.
UI가 Presenter와 통신하는 방법을 명확히 규정합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import pyqtSignal

from upbit_auto_trading.application.dto.database_config_dto import (
    DatabaseProfileDto, DatabaseStatusDto, DatabaseHealthCheckDto
)


class IDatabaseSettingsView(ABC):
    """데이터베이스 설정 View 인터페이스"""

    # View 이벤트 시그널들 (UI에서 Presenter로)
    @abstractmethod
    def get_load_current_settings_signal(self) -> pyqtSignal:
        """현재 설정 로드 요청 시그널"""
        pass

    @abstractmethod
    def get_validate_database_signal(self) -> pyqtSignal:
        """데이터베이스 검증 요청 시그널"""
        pass

    @abstractmethod
    def get_apply_settings_signal(self) -> pyqtSignal:
        """설정 적용 요청 시그널"""
        pass

    @abstractmethod
    def get_browse_file_signal(self) -> pyqtSignal:
        """파일 찾아보기 요청 시그널"""
        pass

    @abstractmethod
    def get_reset_to_defaults_signal(self) -> pyqtSignal:
        """기본값으로 초기화 요청 시그널"""
        pass

    # View 업데이트 메서드들 (Presenter에서 View로)
    @abstractmethod
    def display_database_profiles(self, profiles: List[DatabaseProfileDto]) -> None:
        """데이터베이스 프로필 목록 표시"""
        pass

    @abstractmethod
    def display_database_status(self, status: DatabaseStatusDto) -> None:
        """데이터베이스 상태 표시"""
        pass

    @abstractmethod
    def display_health_check_result(self, health_check: DatabaseHealthCheckDto) -> None:
        """건강 검사 결과 표시"""
        pass

    @abstractmethod
    def update_file_path(self, database_type: str, file_path: str) -> None:
        """파일 경로 업데이트"""
        pass

    @abstractmethod
    def show_validation_progress(self, show: bool, message: str = "") -> None:
        """검증 진행 상황 표시"""
        pass

    @abstractmethod
    def show_success_message(self, message: str) -> None:
        """성공 메시지 표시"""
        pass

    @abstractmethod
    def show_error_message(self, message: str) -> None:
        """오류 메시지 표시"""
        pass

    @abstractmethod
    def show_warning_message(self, message: str) -> None:
        """경고 메시지 표시"""
        pass

    @abstractmethod
    def enable_apply_button(self, enabled: bool) -> None:
        """적용 버튼 활성화/비활성화"""
        pass

    @abstractmethod
    def get_current_file_paths(self) -> Dict[str, str]:
        """현재 입력된 파일 경로들 조회"""
        pass

    @abstractmethod
    def set_loading_state(self, loading: bool) -> None:
        """로딩 상태 설정"""
        pass


class DatabaseSettingsViewEvents:
    """View에서 발생하는 이벤트들"""

    def __init__(self):
        """이벤트 시그널 초기화"""
        from PyQt6.QtCore import QObject, pyqtSignal

        class ViewEventSignals(QObject):
            # 데이터 로드 관련
            load_current_settings_requested = pyqtSignal()
            refresh_status_requested = pyqtSignal()

            # 검증 관련
            validate_database_requested = pyqtSignal(str)  # database_type
            validate_all_databases_requested = pyqtSignal()

            # 설정 변경 관련
            apply_settings_requested = pyqtSignal(dict)  # file_paths
            reset_to_defaults_requested = pyqtSignal()

            # 파일 탐색 관련
            browse_file_requested = pyqtSignal(str)  # database_type

            # 백업 관련
            create_backup_requested = pyqtSignal(str)  # database_type
            restore_backup_requested = pyqtSignal(str, str)  # backup_id, database_type

            # 고급 기능
            export_configuration_requested = pyqtSignal()
            import_configuration_requested = pyqtSignal(str)  # file_path

        self.signals = ViewEventSignals()

    def get_signals(self):
        """이벤트 시그널 객체 반환"""
        return self.signals
