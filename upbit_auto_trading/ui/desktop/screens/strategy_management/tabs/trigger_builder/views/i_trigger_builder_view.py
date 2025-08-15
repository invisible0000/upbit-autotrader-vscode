"""
트리거 빌더 View Interface - MVP 패턴
"""

from abc import ABC, abstractmethod
from upbit_auto_trading.application.dto.trigger_builder.trading_variable_dto import (
    TradingVariableListDTO,
    TradingVariableDetailDTO
)


class ITriggerBuilderView(ABC):
    """트리거 빌더 메인 View 인터페이스"""

    @abstractmethod
    def display_variables(self, variables_dto: TradingVariableListDTO) -> None:
        """변수 목록을 UI에 표시"""
        pass

    @abstractmethod
    def show_variable_details(self, details_dto: TradingVariableDetailDTO) -> None:
        """변수 상세 정보를 UI에 표시"""
        pass

    @abstractmethod
    def show_external_variable_details(self, details_dto: TradingVariableDetailDTO) -> None:
        """외부 변수 상세 정보를 UI에 표시"""
        pass

    @abstractmethod
    def update_compatibility_status(self, is_compatible: bool, message: str) -> None:
        """호환성 검증 결과를 UI에 표시"""
        pass

    @abstractmethod
    def show_error_message(self, message: str) -> None:
        """에러 메시지를 UI에 표시"""
        pass

    @abstractmethod
    def show_success_message(self, message: str) -> None:
        """성공 메시지를 UI에 표시"""
        pass

    @abstractmethod
    def enable_simulation_controls(self, enabled: bool) -> None:
        """시뮬레이션 컨트롤 활성화/비활성화"""
        pass

    @abstractmethod
    def update_simulation_progress(self, progress: int) -> None:
        """시뮬레이션 진행률 업데이트"""
        pass

    @abstractmethod
    def run_simulation(self, scenario_type: str) -> None:
        """시뮬레이션 실행"""
        pass

    @abstractmethod
    def update_data_source(self, source_type: str) -> None:
        """데이터 소스 변경"""
        pass
