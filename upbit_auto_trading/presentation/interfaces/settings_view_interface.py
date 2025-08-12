# settings_view_interface.py
"""Settings View Interface for MVP Pattern"""

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from PyQt6.QtCore import pyqtSignal

@runtime_checkable
class ISettingsView(Protocol):
    """Settings View Interface for MVP Pattern

    View는 순수하게 UI 표시/입력 수집만 담당
    모든 비즈니스 로직은 SettingsPresenter에서 처리
    """

    # 시그널 정의 (View → Presenter 통신)
    settings_changed: pyqtSignal = pyqtSignal()
    theme_changed: pyqtSignal = pyqtSignal(str)  # theme_value
    api_status_changed: pyqtSignal = pyqtSignal(bool)  # connected
    db_status_changed: pyqtSignal = pyqtSignal(bool)   # connected
    save_all_requested: pyqtSignal = pyqtSignal()

    @abstractmethod
    def setup_ui(self) -> None:
        """UI 컴포넌트 설정 (순수 UI 로직만)"""
        pass

    @abstractmethod
    def connect_view_signals(self) -> None:
        """View 내부 시그널 연결 (Presenter와 연결은 별도)"""
        pass

    @abstractmethod
    def show_loading_state(self, loading: bool) -> None:
        """로딩 상태 표시/숨김"""
        pass

    @abstractmethod
    def show_save_success_message(self) -> None:
        """저장 성공 메시지 표시"""
        pass

    @abstractmethod
    def show_save_error_message(self, error: str) -> None:
        """저장 실패 메시지 표시"""
        pass

    @abstractmethod
    def show_status_message(self, message: str, success: bool = True) -> None:
        """상태 메시지 표시"""
        pass

    @abstractmethod
    def get_current_tab_index(self) -> int:
        """현재 선택된 탭 인덱스"""
        pass

    @abstractmethod
    def set_current_tab_index(self, index: int) -> None:
        """특정 탭으로 이동"""
        pass

class ISettingsSubView(Protocol):
    """설정 하위 탭 View Interface"""

    @abstractmethod
    def load_settings_to_ui(self) -> None:
        """설정값을 UI에 표시"""
        pass

    @abstractmethod
    def save_settings_from_ui(self) -> bool:
        """UI에서 설정값을 저장, 성공 여부 반환"""
        pass

    @abstractmethod
    def validate_settings(self) -> tuple[bool, str]:
        """설정값 유효성 검사, (성공여부, 오류메시지) 반환"""
        pass
