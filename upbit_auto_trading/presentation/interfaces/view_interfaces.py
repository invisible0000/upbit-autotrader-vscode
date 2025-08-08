"""
View 인터페이스 정의 - MVP 패턴

UI 컴포넌트들이 구현해야 하는 View 인터페이스를 정의합니다.
Presenter는 이 인터페이스를 통해서만 View와 상호작용하여
UI 기술과 무관한 비즈니스 로직을 구현할 수 있습니다.

Note: Protocol을 사용하여 PyQt6와의 메타클래스 충돌을 방지합니다.
"""

from typing import List, Dict, Any, Protocol


class IStrategyMakerView(Protocol):
    """전략 메이커 View 인터페이스

    전략 생성 및 편집 UI의 표준 인터페이스입니다.
    실제 UI 기술(PyQt6, tkinter 등)과 무관하게 비즈니스 로직을 처리할 수 있도록 합니다.
    """

    def display_strategy_list(self, strategies: List[Dict[str, Any]]) -> None:
        """전략 목록 표시"""
        ...

    def display_validation_errors(self, errors: List[str]) -> None:
        """검증 오류 표시"""
        ...

    def display_success_message(self, message: str) -> None:
        """성공 메시지 표시"""
        ...

    def display_error_message(self, message: str) -> None:
        """오류 메시지 표시"""
        ...

    def clear_form(self) -> None:
        """폼 초기화"""
        ...

    def get_strategy_form_data(self) -> Dict[str, Any]:
        """폼에서 전략 데이터 수집"""
        ...

    def set_strategy_form_data(self, strategy_data: Dict[str, Any]) -> None:
        """폼에 전략 데이터 설정"""
        ...

    def show_loading(self, message: str = "처리 중...") -> None:
        """로딩 상태 표시"""
        ...

    def hide_loading(self) -> None:
        """로딩 상태 숨김"""
        ...


class ITriggerBuilderView(Protocol):
    """트리거 빌더 View 인터페이스"""

    def display_variables(self, variables: List[Dict[str, Any]]) -> None:
        """변수 목록 표시"""
        ...

    def display_compatibility_warning(self, message: str) -> None:
        """호환성 경고 표시"""
        ...

    def update_condition_preview(self, preview: str) -> None:
        """조건 미리보기 업데이트"""
        ...

    def get_trigger_form_data(self) -> Dict[str, Any]:
        """트리거 폼 데이터 수집"""
        ...

    def clear_trigger_form(self) -> None:
        """트리거 폼 초기화"""
        ...


class IBacktestView(Protocol):
    """백테스팅 View 인터페이스"""

    def display_backtest_results(self, results: Dict[str, Any]) -> None:
        """백테스팅 결과 표시"""
        ...

    def update_progress(self, progress: int, message: str = "") -> None:
        """진행률 업데이트"""
        ...

    def display_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """성과 지표 표시"""
        ...

    def show_trade_history(self, trades: List[Dict[str, Any]]) -> None:
        """거래 이력 표시"""
        ...


class ISettingsView(Protocol):
    """설정 View 인터페이스"""

    def display_current_settings(self, settings: Dict[str, Any]) -> None:
        """현재 설정 표시"""
        ...

    def get_settings_data(self) -> Dict[str, Any]:
        """설정 데이터 수집"""
        ...

    def display_settings_saved_message(self) -> None:
        """설정 저장 완료 메시지 표시"""
        ...

    def display_settings_error(self, error: str) -> None:
        """설정 오류 메시지 표시"""
        ...


class ILiveTradingView(Protocol):
    """실시간 거래 View 인터페이스"""

    def display_current_positions(self, positions: List[Dict[str, Any]]) -> None:
        """현재 포지션 표시"""
        ...

    def display_trade_signals(self, signals: List[Dict[str, Any]]) -> None:
        """거래 신호 표시"""
        ...

    def update_pnl(self, pnl_data: Dict[str, Any]) -> None:
        """손익 정보 업데이트"""
        ...

    def display_market_data(self, market_data: Dict[str, Any]) -> None:
        """시장 데이터 표시"""
        ...

    def show_trading_status(self, status: str, is_active: bool) -> None:
        """거래 상태 표시"""
        ...
