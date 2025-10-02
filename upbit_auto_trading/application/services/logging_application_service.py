"""
Application Layer 로깅 서비스
Settings 컴포넌트의 Infrastructure 직접 접근 위반 해결을 위한 DI 패턴 적용
"""

from typing import Any, Protocol
from upbit_auto_trading.infrastructure.logging import create_component_logger


class IPresentationLogger(Protocol):
    """
    Presentation Layer가 사용할 로깅 인터페이스

    Infrastructure 계층으로부터 격리된 로깅 규약 정의
    """

    def debug(self, message: str, *args, **kwargs) -> None:
        """디버그 레벨 로그 출력"""
        ...

    def info(self, message: str, *args, **kwargs) -> None:
        """정보 레벨 로그 출력"""
        ...

    def warning(self, message: str, *args, **kwargs) -> None:
        """경고 레벨 로그 출력"""
        ...

    def error(self, message: str, *args, **kwargs) -> None:
        """에러 레벨 로그 출력"""
        ...

    def critical(self, message: str, *args, **kwargs) -> None:
        """심각한 에러 레벨 로그 출력"""
        ...


class PresentationLoggerAdapter:
    """
    Infrastructure 로거를 Presentation Layer 인터페이스로 감싸는 어댑터
    """

    def __init__(self, infrastructure_logger: Any, component_name: str):
        self._logger = infrastructure_logger
        self._component_name = component_name

    def debug(self, message: str, *args, **kwargs) -> None:
        """디버그 레벨 로그 출력"""
        self._logger.debug(f"[{self._component_name}] {message}", *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """정보 레벨 로그 출력"""
        self._logger.info(f"[{self._component_name}] {message}", *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """경고 레벨 로그 출력"""
        self._logger.warning(f"[{self._component_name}] {message}", *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """에러 레벨 로그 출력"""
        self._logger.error(f"[{self._component_name}] {message}", *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """심각한 에러 레벨 로그 출력"""
        self._logger.critical(f"[{self._component_name}] {message}", *args, **kwargs)

    def get_component_logger(self, component_name: str) -> 'PresentationLoggerAdapter':
        """하위 컴포넌트용 로거 생성 (Factory 패턴에서 필요)"""
        # Infrastructure 로거 재사용하여 새로운 어댑터 생성
        from upbit_auto_trading.infrastructure.logging import create_component_logger
        infrastructure_logger = create_component_logger(component_name)
        return PresentationLoggerAdapter(infrastructure_logger, component_name)


class ApplicationLoggingService:
    """
    Application Layer 로깅 서비스

    Infrastructure 로깅을 Application 계층에서 감싸서
    Presentation Layer가 Infrastructure에 직접 의존하지 않도록 격리
    """

    def __init__(self):
        """
        ApplicationLoggingService 초기화

        Infrastructure 로깅 팩토리를 내부적으로 사용하되,
        외부에는 Application Layer 인터페이스만 노출
        """
        self._component_loggers = {}
        self._service_logger = create_component_logger("ApplicationLoggingService")
        self._service_logger.info("ApplicationLoggingService 초기화 완료")

    def get_component_logger(self, component_name: str) -> IPresentationLogger:
        """
        컴포넌트별 로거 조회/생성

        Args:
            component_name: 컴포넌트 이름 (예: "SettingsView", "ApiSettingsPresenter")

        Returns:
            IPresentationLogger: Presentation Layer용 로거 인터페이스
        """
        if component_name not in self._component_loggers:
            # Infrastructure 로거 생성
            infrastructure_logger = create_component_logger(component_name)

            # Presentation Layer 어댑터로 감쌈
            presentation_logger = PresentationLoggerAdapter(infrastructure_logger, component_name)

            self._component_loggers[component_name] = presentation_logger
            self._service_logger.debug(f"새 컴포넌트 로거 생성: {component_name}")

        return self._component_loggers[component_name]

    def clear_cache(self) -> None:
        """
        캐시된 로거들 정리

        테스트나 특별한 경우에만 사용
        """
        cleared_count = len(self._component_loggers)
        self._component_loggers.clear()
        self._service_logger.info(f"로거 캐시 정리 완료: {cleared_count}개 로거")

    def get_cached_logger_count(self) -> int:
        """
        현재 캐시된 로거 개수 반환

        Returns:
            int: 캐시된 로거 개수
        """
        return len(self._component_loggers)

    def list_component_names(self) -> list[str]:
        """
        현재 등록된 컴포넌트 이름들 반환

        Returns:
            list[str]: 등록된 컴포넌트 이름 목록
        """
        return list(self._component_loggers.keys())


# =============================================================================
# Factory 함수 - DI 컨테이너에서 사용
# =============================================================================

def create_application_logging_service() -> ApplicationLoggingService:
    """
    ApplicationLoggingService 팩토리 함수

    DI 컨테이너에서 사용할 수 있도록 독립된 팩토리 함수 제공

    Returns:
        ApplicationLoggingService: 새로 생성된 로깅 서비스 인스턴스
    """
    return ApplicationLoggingService()
