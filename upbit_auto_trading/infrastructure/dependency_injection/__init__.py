"""
Infrastructure Layer - Dependency Injection System
===================================================

Clean Architecture 기반 의존성 주입 컨테이너와 서비스 생명주기 관리

주요 구성요소:
- DIContainer: 의존성 주입 컨테이너 (Singleton, Transient, Scoped 지원)
- LifetimeScope: 서비스 생명주기 열거형
- ServiceRegistration: 서비스 등록 정보 관리

사용 예시:
    >>> from upbit_auto_trading.infrastructure.dependency_injection import DIContainer
    >>> container = DIContainer()
    >>> container.register_singleton(IMarketDataService, UpbitMarketDataService)
    >>> service = container.resolve(IMarketDataService)
"""

from .container import DIContainer, LifetimeScope, ServiceRegistration

__all__ = [
    'DIContainer',
    'LifetimeScope',
    'ServiceRegistration'
]

__version__ = '1.0.0'
