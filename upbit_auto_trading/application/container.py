"""
Application Service Container - 의존성 주입 컨테이너

Application Service들의 의존성을 관리하고 인스턴스를 제공합니다.
Singleton 패턴으로 구현하여 하나의 서비스 인스턴스만 존재하도록 보장합니다.
"""

from typing import Optional

from upbit_auto_trading.application.services.strategy_application_service import StrategyApplicationService
from upbit_auto_trading.application.services.trigger_application_service import TriggerApplicationService
from upbit_auto_trading.application.services.backtest_application_service import BacktestApplicationService


class ApplicationServiceContainer:
    """Application Service들의 의존성 주입 컨테이너

    Repository Container를 받아서 필요한 Application Service들을 생성하고 관리합니다.
    """

    def __init__(self, repository_container):
        """컨테이너 초기화

        Args:
            repository_container: Repository들을 제공하는 컨테이너
        """
        self._repo_container = repository_container
        self._services = {}

    def get_strategy_service(self) -> StrategyApplicationService:
        """전략 Application Service 조회

        Returns:
            StrategyApplicationService: 전략 관리 서비스
        """
        if "strategy" not in self._services:
            self._services["strategy"] = StrategyApplicationService(
                self._repo_container.get_strategy_repository(),
                self._repo_container.get_compatibility_service()
            )
        return self._services["strategy"]

    def get_trigger_service(self) -> TriggerApplicationService:
        """트리거 Application Service 조회

        Returns:
            TriggerApplicationService: 트리거 관리 서비스
        """
        if "trigger" not in self._services:
            self._services["trigger"] = TriggerApplicationService(
                self._repo_container.get_trigger_repository(),
                self._repo_container.get_strategy_repository(),
                self._repo_container.get_settings_repository(),
                self._repo_container.get_compatibility_service()
            )
        return self._services["trigger"]

    def get_backtest_service(self) -> BacktestApplicationService:
        """백테스팅 Application Service 조회

        Returns:
            BacktestApplicationService: 백테스팅 관리 서비스
        """
        if "backtest" not in self._services:
            self._services["backtest"] = BacktestApplicationService(
                self._repo_container.get_strategy_repository(),
                self._repo_container.get_backtest_repository(),
                self._repo_container.get_market_data_repository()
            )
        return self._services["backtest"]

    def clear_cache(self) -> None:
        """서비스 캐시 초기화

        테스트나 재설정이 필요할 때 사용합니다.
        """
        self._services.clear()


# 전역 컨테이너 인스턴스 (필요 시 사용)
_global_container: Optional[ApplicationServiceContainer] = None


def get_application_container() -> Optional[ApplicationServiceContainer]:
    """전역 Application Service Container 조회

    Returns:
        ApplicationServiceContainer: 전역 컨테이너 (없으면 None)
    """
    return _global_container


def set_application_container(container: ApplicationServiceContainer) -> None:
    """전역 Application Service Container 설정

    Args:
        container: 설정할 컨테이너
    """
    global _global_container
    _global_container = container
