"""
Infrastructure Layer - Logging System
=====================================

Clean Architecture 기반 로깅 시스템
환경별 지능형 필터링, LLM 에이전트 통합, 성능 최적화 지원

핵심 기능:
- Smart Context-aware Filtering: 환경별/기능별 지능형 로그 필터링
- Dual File Logging: 메인 로그 + 세션별 로그 관리
- Environment Variable Control: 실시간 로그 레벨 제어
- LLM Agent Integration: 구조화된 에러 보고 및 브리핑
- Terminal Capture: 실시간 터미널 출력 캡처 및 동기화
- Performance Optimization: 비동기 처리 및 메모리 최적화

사용 예시:
    >>> from upbit_auto_trading.infrastructure.logging import get_logging_service
    >>> logging_service = get_logging_service()
    >>> logger = logging_service.get_logger("MyComponent")
    >>> logger.info("Infrastructure Layer 로깅")
"""

from .interfaces.logging_interface import ILoggingService, LogContext, LogScope
from .services.logging_service import (
    LoggingService, get_logging_service, create_logging_service,
    create_component_logger, set_logging_context, set_logging_scope
)

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

__all__ = [
    'ILoggingService',
    'LoggingService',
    'LogContext',
    'LogScope',
    'get_logging_service',
    'create_logging_service',
    'create_component_logger',
    'set_logging_context',
    'set_logging_scope'
]

__version__ = '2.0.0'
