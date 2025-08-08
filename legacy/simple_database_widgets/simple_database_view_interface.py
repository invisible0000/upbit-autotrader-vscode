"""
간단한 데이터베이스 뷰 인터페이스

기본에 충실하면서도 MVP 패턴을 적용한 데이터베이스 설정 뷰 인터페이스입니다.
메타클래스 충돌을 피하기 위해 단순한 Protocol을 사용합니다.
"""

from typing import Protocol, Dict, Any
from PyQt6.QtCore import pyqtSignal


class ISimpleDatabaseView(Protocol):
    """간단한 데이터베이스 뷰 인터페이스

    메타클래스 충돌 없이 MVP 패턴을 적용하기 위한 간단한 인터페이스입니다.
    """

    # 시그널들
    settings_changed: pyqtSignal
    db_status_changed: pyqtSignal

    def display_database_info(self, info: Dict[str, str]) -> None:
        """데이터베이스 정보 표시"""
        ...

    def display_status(self, status: Dict[str, bool]) -> None:
        """상태 정보 표시"""
        ...

    def show_progress(self, message: str, value: int = 0) -> None:
        """진행상황 표시"""
        ...

    def hide_progress(self) -> None:
        """진행상황 숨김"""
        ...

    def show_validation_result(self, results: list) -> None:
        """검증 결과 표시"""
        ...

    def show_error_message(self, title: str, message: str) -> None:
        """오류 메시지 표시"""
        ...

    def show_info_message(self, title: str, message: str) -> None:
        """정보 메시지 표시"""
        ...


class ISimpleDatabaseViewEvents(Protocol):
    """간단한 데이터베이스 뷰 이벤트 인터페이스"""

    def on_refresh_status_clicked(self) -> None:
        """상태 새로고침 클릭"""
        ...

    def on_validate_databases_clicked(self) -> None:
        """데이터베이스 검증 클릭"""
        ...

    def on_open_data_folder_clicked(self) -> None:
        """데이터 폴더 열기 클릭"""
        ...
