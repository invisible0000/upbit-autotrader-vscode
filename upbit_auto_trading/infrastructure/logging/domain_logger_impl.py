"""
Infrastructure Layer - Domain Logger Implementation
=================================================

Domain Logger 인터페이스의 Infrastructure 구현체
Infrastructure 로깅 시스템과 Domain 로깅을 연결하는 어댑터

핵심 기능:
1. Domain Logger 인터페이스 구현
2. Infrastructure 로깅 시스템으로 위임
3. 성능 최적화: 직접 위임으로 오버헤드 최소화
"""

from typing import Optional, Dict, Any
from upbit_auto_trading.domain.logging import DomainLogger
from upbit_auto_trading.infrastructure.logging import create_component_logger


class InfrastructureDomainLogger(DomainLogger):
    """
    Infrastructure 기반 Domain Logger 구현체

    Domain Logger 인터페이스를 Infrastructure 로깅 시스템으로 위임하는 어댑터
    성능 최적화를 위해 직접 위임 방식 사용
    """

    def __init__(self, component_name: str = "DomainLogger"):
        """
        Infrastructure 로거 초기화

        Args:
            component_name: 로거 컴포넌트 이름
        """
        self._infrastructure_logger = create_component_logger(component_name)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Debug 레벨 로깅 - Infrastructure로 직접 위임"""
        if context:
            self._infrastructure_logger.debug(f"{message} | Context: {context}")
        else:
            self._infrastructure_logger.debug(message)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Info 레벨 로깅 - Infrastructure로 직접 위임"""
        if context:
            self._infrastructure_logger.info(f"{message} | Context: {context}")
        else:
            self._infrastructure_logger.info(message)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Warning 레벨 로깅 - Infrastructure로 직접 위임"""
        if context:
            self._infrastructure_logger.warning(f"{message} | Context: {context}")
        else:
            self._infrastructure_logger.warning(message)

    def error(self, message: str, context: Optional[Dict[str, Any]] = None,
              exception_info: Optional[str] = None) -> None:
        """Error 레벨 로깅 - Infrastructure로 직접 위임"""
        error_message = message
        if context:
            error_message += f" | Context: {context}"
        if exception_info:
            error_message += f" | Exception: {exception_info}"

        self._infrastructure_logger.error(error_message)

    def critical(self, message: str, context: Optional[Dict[str, Any]] = None,
                 exception_info: Optional[str] = None) -> None:
        """Critical 레벨 로깅 - Infrastructure로 직접 위임"""
        critical_message = message
        if context:
            critical_message += f" | Context: {context}"
        if exception_info:
            critical_message += f" | Exception: {exception_info}"

        self._infrastructure_logger.critical(critical_message)


def create_infrastructure_domain_logger() -> InfrastructureDomainLogger:
    """
    Infrastructure Domain Logger 생성

    Returns:
        InfrastructureDomainLogger: Infrastructure 기반 Domain Logger 구현체
    """
    return InfrastructureDomainLogger("DomainServices")
