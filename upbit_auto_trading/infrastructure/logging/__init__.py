"""
Infrastructure Layer - Integrated Logging System
===============================================

Clean Architecture 기반 통합 로깅 시스템
기존 upbit_auto_trading/logging의 핵심 개념을 Infrastructure Layer로 통합

핵심 기능:
- Smart Context-aware Filtering: 환경별/기능별 지능형 로그 필터링
- Dual File Logging: 메인 로그 + 세션별 로그 관리
- Environment Variable Control: 실시간 로그 레벨 제어
- Component-based Logger: 컴포넌트별 독립 로거 관리
- DI Container Integration: 의존성 주입 완전 지원

사용 예시:
    >>> from upbit_auto_trading.infrastructure.logging import get_logging_service
    >>> logging_service = get_logging_service()
    >>> logger = logging_service.get_logger("MyComponent")
    >>> logger.info("Infrastructure Layer 통합 로깅")
"""

from .interfaces.logging_interface import ILoggingService, LogContext, LogScope
from .services.smart_logging_service import SmartLoggingService
from .configuration.logging_config import LoggingConfig

# 전역 로깅 서비스 인스턴스 (싱글톤)
_logging_service_instance: ILoggingService = None


def get_logging_service() -> ILoggingService:
    """
    통합 로깅 서비스 조회 (싱글톤)

    Returns:
        ILoggingService: 통합 로깅 서비스 인스턴스
    """
    global _logging_service_instance
    if _logging_service_instance is None:
        _logging_service_instance = SmartLoggingService()
    return _logging_service_instance


def create_component_logger(component_name: str):
    """
    컴포넌트별 로거 생성 (편의 함수)

    Args:
        component_name: 컴포넌트 이름

    Returns:
        Logger: 컴포넌트 전용 로거
    """
    service = get_logging_service()
    return service.get_logger(component_name)


def set_logging_context(context: LogContext) -> None:
    """
    로깅 컨텍스트 설정 (편의 함수)

    Args:
        context: 로그 컨텍스트 (development, testing, production 등)
    """
    service = get_logging_service()
    service.set_context(context)


def set_logging_scope(scope: LogScope) -> None:
    """
    로깅 스코프 설정 (편의 함수)

    Args:
        scope: 로그 스코프 (silent, minimal, normal, verbose, debug_all)
    """
    service = get_logging_service()
    service.set_scope(scope)


# 하위 호환성을 위한 기존 패턴 지원
def get_integrated_logger(component_name: str):
    """
    기존 get_integrated_logger 호환 함수

    Args:
        component_name: 컴포넌트 이름

    Returns:
        Logger: 통합 로거
    """
    return create_component_logger(component_name)


__all__ = [
    'ILoggingService',
    'SmartLoggingService',
    'LoggingConfig',
    'LogContext',
    'LogScope',
    'get_logging_service',
    'create_component_logger',
    'set_logging_context',
    'set_logging_scope',
    'get_integrated_logger'  # 호환성
]

__version__ = '1.0.0'
