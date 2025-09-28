"""
Infrastructure Layer - Dependency Injection System
===================================================

Clean Architecture + dependency-injector 기반 DI 시스템

주요 구성요소:
- ApplicationContainer: DDD 계층별 Provider 구성
- @inject 데코레이터: 생성자 주입 패턴
- Configuration Provider: 환경별 설정 관리

사용 예시:
    >>> from upbit_auto_trading.infrastructure.dependency_injection import ApplicationContainer
    >>> container = ApplicationContainer()
    >>>
    >>> # @inject 데코레이터 사용
    >>> @inject
    >>> def __init__(self, service: MyService = Provide[ApplicationContainer.my_service]):
    >>>     self._service = service
"""

from .container import (
    ApplicationContainer,
    create_application_container,
    wire_container_modules,
    validate_container_registration,
    get_global_container,
    set_global_container,
    reset_global_container,
    LegacyDIContainerWrapper
)

from .app_context import (
    ApplicationContext,
    ApplicationContextError,
    get_application_context,
    set_application_context,
    reset_application_context,
    is_application_context_initialized
)

__all__ = [
    # Container
    'ApplicationContainer',
    'create_application_container',
    'wire_container_modules',
    'validate_container_registration',
    'get_global_container',
    'set_global_container',
    'reset_global_container',
    'LegacyDIContainerWrapper',
    # Context
    'ApplicationContext',
    'ApplicationContextError',
    'get_application_context',
    'set_application_context',
    'reset_application_context',
    'is_application_context_initialized'
]

__version__ = '1.0.0'
