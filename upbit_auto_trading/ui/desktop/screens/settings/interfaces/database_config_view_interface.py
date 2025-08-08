"""
Database Configuration View Interface

MVP 패턴에서 View 계층의 인터페이스를 정의합니다.
Presenter가 View와 통신할 때 사용하는 표준 메서드들을 제공합니다.

Design Principles:
- Interface Segregation: 필요한 메서드만 노출
- Dependency Inversion: Presenter가 구체 클래스가 아닌 인터페이스에 의존
- Single Responsibility: UI 표시와 사용자 입력 처리만 담당
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class IDatabaseConfigView(ABC):
    """
    데이터베이스 설정 View 인터페이스

    Presenter가 View와 통신할 때 사용하는 표준 메서드들을 정의합니다.
    """

    # === 데이터 표시 ===

    @abstractmethod
    def update_configuration_display(self, config: Dict[str, Any]) -> None:
        """
        설정 데이터를 UI에 표시

        Args:
            config: 표시할 설정 데이터
        """
        pass

    @abstractmethod
    def update_status_display(self, status: Dict[str, Any]) -> None:
        """
        상태 정보를 UI에 표시

        Args:
            status: 표시할 상태 데이터
        """
        pass

    @abstractmethod
    def update_backup_list(self, backups: List[Dict[str, Any]]) -> None:
        """
        백업 목록을 UI에 표시

        Args:
            backups: 백업 목록 데이터
        """
        pass

    # === 진행상황 표시 ===

    @abstractmethod
    def show_progress(self, message: str) -> None:
        """
        진행상황 표시

        Args:
            message: 진행상황 메시지
        """
        pass

    @abstractmethod
    def hide_progress(self) -> None:
        """진행상황 숨기기"""
        pass

    @abstractmethod
    def update_progress(self, percentage: int, message: str = "") -> None:
        """
        진행률 업데이트

        Args:
            percentage: 진행률 (0-100)
            message: 진행상황 메시지
        """
        pass

    # === 메시지 표시 ===

    @abstractmethod
    def show_success_message(self, title: str, message: str) -> None:
        """
        성공 메시지 표시

        Args:
            title: 메시지 제목
            message: 메시지 내용
        """
        pass

    @abstractmethod
    def show_error_message(self, title: str, message: str) -> None:
        """
        에러 메시지 표시

        Args:
            title: 메시지 제목
            message: 메시지 내용
        """
        pass

    @abstractmethod
    def show_warning_message(self, title: str, message: str) -> None:
        """
        경고 메시지 표시

        Args:
            title: 메시지 제목
            message: 메시지 내용
        """
        pass

    @abstractmethod
    def show_info_message(self, title: str, message: str) -> None:
        """
        정보 메시지 표시

        Args:
            title: 메시지 제목
            message: 메시지 내용
        """
        pass

    @abstractmethod
    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """
        확인 대화상자 표시

        Args:
            title: 대화상자 제목
            message: 확인 메시지

        Returns:
            사용자가 확인을 선택했는지 여부
        """
        pass

    # === 데이터 입력 ===

    @abstractmethod
    def get_current_form_data(self) -> Dict[str, Any]:
        """
        현재 폼의 데이터 반환

        Returns:
            폼 데이터 딕셔너리
        """
        pass

    @abstractmethod
    def clear_form(self) -> None:
        """폼 데이터 초기화"""
        pass

    @abstractmethod
    def set_form_data(self, data: Dict[str, Any]) -> None:
        """
        폼에 데이터 설정

        Args:
            data: 설정할 데이터
        """
        pass

    # === UI 상태 제어 ===

    @abstractmethod
    def enable_controls(self, enabled: bool = True) -> None:
        """
        UI 컨트롤 활성화/비활성화

        Args:
            enabled: 활성화 여부
        """
        pass

    @abstractmethod
    def set_read_only(self, read_only: bool = True) -> None:
        """
        읽기 전용 모드 설정

        Args:
            read_only: 읽기 전용 여부
        """
        pass

    @abstractmethod
    def refresh_display(self) -> None:
        """화면 새로고침"""
        pass

    # === 파일 선택 ===

    @abstractmethod
    def show_file_selector(self, title: str, file_filter: str = "") -> str:
        """
        파일 선택 대화상자 표시

        Args:
            title: 대화상자 제목
            file_filter: 파일 필터 (예: "*.sqlite3")

        Returns:
            선택된 파일 경로 (취소 시 빈 문자열)
        """
        pass

    @abstractmethod
    def show_directory_selector(self, title: str) -> str:
        """
        디렉토리 선택 대화상자 표시

        Args:
            title: 대화상자 제목

        Returns:
            선택된 디렉토리 경로 (취소 시 빈 문자열)
        """
        pass


class IDatabaseConfigViewEvents(ABC):
    """
    데이터베이스 설정 View 이벤트 인터페이스

    View에서 발생하는 이벤트를 Presenter에게 전달하기 위한 인터페이스입니다.
    """

    # === 설정 관리 이벤트 ===

    @abstractmethod
    def on_load_configuration_requested(self) -> None:
        """설정 로드 요청"""
        pass

    @abstractmethod
    def on_save_configuration_requested(self, config_data: Dict[str, Any]) -> None:
        """
        설정 저장 요청

        Args:
            config_data: 저장할 설정 데이터
        """
        pass

    @abstractmethod
    def on_reset_configuration_requested(self) -> None:
        """설정 초기화 요청"""
        pass

    # === 프로필 관리 이벤트 ===

    @abstractmethod
    def on_switch_profile_requested(self, database_type: str, new_path: str) -> None:
        """
        프로필 전환 요청

        Args:
            database_type: 데이터베이스 타입
            new_path: 새로운 파일 경로
        """
        pass

    @abstractmethod
    def on_create_profile_requested(self, profile_data: Dict[str, Any]) -> None:
        """
        프로필 생성 요청

        Args:
            profile_data: 프로필 데이터
        """
        pass

    @abstractmethod
    def on_delete_profile_requested(self, profile_id: str) -> None:
        """
        프로필 삭제 요청

        Args:
            profile_id: 삭제할 프로필 ID
        """
        pass

    # === 백업 관리 이벤트 ===

    @abstractmethod
    def on_create_backup_requested(self, database_type: str) -> None:
        """
        백업 생성 요청

        Args:
            database_type: 백업할 데이터베이스 타입
        """
        pass

    @abstractmethod
    def on_restore_backup_requested(self, backup_id: str) -> None:
        """
        백업 복원 요청

        Args:
            backup_id: 복원할 백업 ID
        """
        pass

    @abstractmethod
    def on_delete_backup_requested(self, backup_id: str) -> None:
        """
        백업 삭제 요청

        Args:
            backup_id: 삭제할 백업 ID
        """
        pass

    @abstractmethod
    def on_list_backups_requested(self, database_type: str = None) -> None:
        """
        백업 목록 조회 요청

        Args:
            database_type: 특정 데이터베이스 타입 (None이면 전체)
        """
        pass

    # === 검증 및 상태 이벤트 ===

    @abstractmethod
    def on_validate_database_requested(self, database_type: str) -> None:
        """
        데이터베이스 검증 요청

        Args:
            database_type: 검증할 데이터베이스 타입
        """
        pass

    @abstractmethod
    def on_refresh_status_requested(self) -> None:
        """상태 새로고침 요청"""
        pass

    @abstractmethod
    def on_test_connection_requested(self, database_type: str) -> None:
        """
        연결 테스트 요청

        Args:
            database_type: 테스트할 데이터베이스 타입
        """
        pass
