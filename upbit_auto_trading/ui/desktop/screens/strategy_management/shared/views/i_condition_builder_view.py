"""
컨디션 빌더 View Interface - MVP 패턴의 View 계층
"""
from abc import ABC, abstractmethod
from upbit_auto_trading.application.dto.trigger_builder.trading_variable_dto import (
    TradingVariableListDTO,
    TradingVariableDetailDTO
)


class IConditionBuilderView(ABC):
    """컨디션 빌더 View Interface - MVP 패턴"""

    @abstractmethod
    def display_variables(self, variables_dto: TradingVariableListDTO) -> None:
        """변수 목록을 UI에 표시"""
        pass

    @abstractmethod
    def show_variable_details(self, details_dto: TradingVariableDetailDTO) -> None:
        """선택된 변수의 상세 정보 표시"""
        pass

    @abstractmethod
    def show_external_variable_details(self, details_dto: TradingVariableDetailDTO) -> None:
        """선택된 외부 변수의 상세 정보 표시"""
        pass

    @abstractmethod
    def update_compatibility_status(self, is_compatible: bool, message: str, detail: str = "") -> None:
        """변수 호환성 검증 결과 표시"""
        pass

    @abstractmethod
    def get_current_condition(self) -> dict:
        """현재 설정된 조건 반환"""
        pass

    @abstractmethod
    def reset_condition(self) -> None:
        """조건 설정 초기화"""
        pass

    @abstractmethod
    def set_loading_state(self, is_loading: bool) -> None:
        """로딩 상태 표시/숨김"""
        pass
