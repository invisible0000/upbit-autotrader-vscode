"""
Infrastructure Layer - Dependency Injection System
===================================================

Clean Architecture + dependency-injector 기반 DI 시스템

주요 구성요소:
- ExternalDependencyContainer: Infrastructure Layer 외부 의존성 전담
- @inject 데코레이터: 생성자 주입 패턴
- Configuration Provider: 환경별 설정 관리

사용 예시:
    >>> from upbit_auto_trading.infrastructure.dependency_injection import ExternalDependencyContainer
    >>> container = ExternalDependencyContainer()
    >>>
    >>> # @inject 데코레이터 사용
    >>> @inject
    >>> def __init__(self, service: MyService = Provide[ExternalDependencyContainer.my_service]):
    >>>     self._service = service
"""

from .external_dependency_container import (
    ExternalDependencyContainer,
    create_external_dependency_container,
    wire_external_dependency_modules,
    validate_external_dependency_container,
    get_external_dependency_container,
    set_external_dependency_container,
    reset_external_dependency_container,
    get_global_container  # Legacy 호환성
)

from .di_lifecycle_manager import (
    DILifecycleManager,
    DILifecycleManagerError,
    get_di_lifecycle_manager,
    set_di_lifecycle_manager,
    reset_di_lifecycle_manager,
    is_di_lifecycle_manager_initialized,
    # Legacy compatibility
    ApplicationContext,
    ApplicationContextError,
    get_application_context,
    set_application_context,
    reset_application_context,
    is_application_context_initialized
)

__all__ = [
    # External Dependency Container (New)
    'ExternalDependencyContainer',
    'create_external_dependency_container',
    'wire_external_dependency_modules',
    'validate_external_dependency_container',
    'get_external_dependency_container',
    'set_external_dependency_container',
    'reset_external_dependency_container',
    # Legacy Compatibility
    'get_global_container',
    # DI Lifecycle Manager (New)
    'DILifecycleManager',
    'DILifecycleManagerError',
    'get_di_lifecycle_manager',
    'set_di_lifecycle_manager',
    'reset_di_lifecycle_manager',
    'is_di_lifecycle_manager_initialized',
    # Legacy Context Aliases
    'ApplicationContext',
    'ApplicationContextError',
    'get_application_context',
    'set_application_context',
    'reset_application_context',
    'is_application_context_initialized'
]

__version__ = '1.0.0'
