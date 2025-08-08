"""
View 인터페이스 정의 - MVP 패턴

UI 컴포넌트들이 구현해야 하는 View 인터페이스를 정의합니다.
Presenter는 이 인터페이스를 통해서만 View와 상호작용하여
UI 기술과 무관한 비즈니스 로직을 구현할 수 있습니다.
"""

from typing import List, Dict, Any, Protocol


class IStrategyMakerView(Protocol):
    """전략 메이커 View 인터페이스

    전략 생성 및 편집 UI의 표준 인터페이스입니다.
    실제 UI 기술(PyQt6, tkinter 등)과 무관하게 비즈니스 로직을 처리할 수 있도록 합니다.

    Note: Protocol을 사용하여 PyQt6와의 메타클래스 충돌을 방지합니다.
    """

    def display_strategy_list(self, strategies: List[Dict[str, Any]]) -> None:
        """전략 목록 표시

        Args:
            strategies: 전략 목록 데이터
        """
        ...

    def display_validation_errors(self, errors: List[str]) -> None:
        """검증 오류 표시

        Args:
            errors: 오류 메시지 목록
        """
        ...

    def display_success_message(self, message: str) -> None:
        """성공 메시지 표시

        Args:
            message: 성공 메시지
        """
        ...

    def display_error_message(self, message: str) -> None:
        """오류 메시지 표시

        Args:
            message: 오류 메시지
        """
        pass

    @abstractmethod
    def clear_form(self) -> None:
        """폼 초기화"""
        pass

    @abstractmethod
    def get_strategy_form_data(self) -> Dict[str, Any]:
        """폼에서 전략 데이터 수집

        Returns:
            Dict[str, Any]: 전략 폼 데이터
        """
        pass

    @abstractmethod
    def set_strategy_form_data(self, strategy_data: Dict[str, Any]) -> None:
        """폼에 전략 데이터 설정

        Args:
            strategy_data: 설정할 전략 데이터
        """
        pass

    @abstractmethod
    def show_loading(self, message: str = "처리 중...") -> None:
        """로딩 상태 표시

        Args:
            message: 로딩 메시지
        """
        pass

    @abstractmethod
    def hide_loading(self) -> None:
        """로딩 상태 숨김"""
        pass


class ITriggerBuilderView(ABC):
    """트리거 빌더 View 인터페이스

    트리거 및 조건 생성 UI의 표준 인터페이스입니다.
    """

    @abstractmethod
    def display_variables(self, variables: List[Dict[str, Any]]) -> None:
        """변수 목록 표시

        Args:
            variables: 사용 가능한 변수 목록
        """
        pass

    @abstractmethod
    def display_compatibility_warning(self, message: str) -> None:
        """호환성 경고 표시

        Args:
            message: 경고 메시지
        """
        pass

    @abstractmethod
    def update_condition_preview(self, preview: str) -> None:
        """조건 미리보기 업데이트

        Args:
            preview: 조건 미리보기 텍스트
        """
        pass

    @abstractmethod
    def get_trigger_form_data(self) -> Dict[str, Any]:
        """트리거 폼 데이터 수집

        Returns:
            Dict[str, Any]: 트리거 폼 데이터
        """
        pass

    @abstractmethod
    def clear_trigger_form(self) -> None:
        """트리거 폼 초기화"""
        pass


class IBacktestView(ABC):
    """백테스팅 View 인터페이스

    백테스팅 실행 및 결과 표시 UI의 표준 인터페이스입니다.
    """

    @abstractmethod
    def display_backtest_results(self, results: Dict[str, Any]) -> None:
        """백테스팅 결과 표시

        Args:
            results: 백테스팅 결과 데이터
        """
        pass

    @abstractmethod
    def update_backtest_progress(self, progress: int, message: str) -> None:
        """백테스팅 진행률 업데이트

        Args:
            progress: 진행률 (0-100)
            message: 진행 상태 메시지
        """
        pass

    @abstractmethod
    def get_backtest_parameters(self) -> Dict[str, Any]:
        """백테스팅 파라미터 수집

        Returns:
            Dict[str, Any]: 백테스팅 파라미터
        """
        pass

    @abstractmethod
    def enable_backtest_controls(self, enabled: bool) -> None:
        """백테스팅 컨트롤 활성화/비활성화

        Args:
            enabled: 활성화 여부
        """
        pass


class ISettingsView(ABC):
    """설정 View 인터페이스

    애플리케이션 설정 UI의 표준 인터페이스입니다.
    """

    @abstractmethod
    def display_settings(self, settings: Dict[str, Any]) -> None:
        """설정 값 표시

        Args:
            settings: 설정 데이터
        """
        pass

    @abstractmethod
    def get_settings_data(self) -> Dict[str, Any]:
        """설정 데이터 수집

        Returns:
            Dict[str, Any]: 현재 설정 데이터
        """
        pass

    @abstractmethod
    def apply_theme_settings(self, theme: str) -> None:
        """테마 설정 즉시 적용

        Args:
            theme: 적용할 테마 이름
        """
        pass


class ILiveTradingView(ABC):
    """실시간 거래 View 인터페이스

    실시간 거래 모니터링 및 제어 UI의 표준 인터페이스입니다.
    """

    @abstractmethod
    def display_active_strategies(self, strategies: List[Dict[str, Any]]) -> None:
        """활성 전략 목록 표시

        Args:
            strategies: 활성 전략 목록
        """
        pass

    @abstractmethod
    def update_strategy_status(self, strategy_id: str, status: Dict[str, Any]) -> None:
        """전략 상태 업데이트

        Args:
            strategy_id: 전략 ID
            status: 업데이트할 상태 정보
        """
        pass

    @abstractmethod
    def display_market_data(self, market_data: Dict[str, Any]) -> None:
        """시장 데이터 표시

        Args:
            market_data: 시장 데이터
        """
        pass

    @abstractmethod
    def show_emergency_stop_confirmation(self) -> bool:
        """긴급 정지 확인 다이얼로그 표시

        Returns:
            bool: 사용자 확인 여부
        """
        pass
