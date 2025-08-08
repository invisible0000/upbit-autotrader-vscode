"""
데이터베이스 설정 View 인터페이스

MVP 패턴의 View 인터페이스입니다.
메타클래스 충돌 없이 깔끔하게 구현했습니다.
"""

from typing import Protocol, Dict
from PyQt6.QtCore import pyqtSignal


class IDatabaseTabView(Protocol):
    """데이터베이스 탭 View 인터페이스"""

    # 시그널들
    settings_changed: pyqtSignal
    db_status_changed: pyqtSignal

    def display_database_info(self, info: Dict[str, str]) -> None:
        """데이터베이스 정보 표시"""
        ...

    def display_status(self, status: Dict) -> None:
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
