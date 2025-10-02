"""
Application Layer - Clean Architecture의 Application Layer

이 레이어는 Use Case들을 구현하며, UI 레이어와 Domain 레이어 사이의 조정자 역할을 합니다.
Application Service들은 도메인 엔티티들을 조율하여 비즈니스 Use Case를 실행합니다.

주요 구성요소:
- services/: Application Service 클래스들 (Use Case 구현)
- dto/: Data Transfer Objects (계층 간 데이터 전송)
- commands/: Command 패턴 구현체들 (입력 데이터 검증)

DDD 원칙:
- Application Service는 Domain Layer에 의존하되, Infrastructure Layer는 모르도록 구현
- 모든 도메인 이벤트는 Application Service에서 발행
- DTO를 통해 UI Layer와의 결합도를 최소화
"""

# Import 순서를 조정하고 오류 방지
try:
    from .services.strategy_application_service import StrategyApplicationService
except ImportError:
    StrategyApplicationService = None

try:
    from .services.trigger_application_service import TriggerApplicationService
except ImportError:
    TriggerApplicationService = None

try:
    from .services.backtest_application_service import BacktestApplicationService
except ImportError:
    BacktestApplicationService = None

try:
    from .application_service_container import (
        ApplicationServiceContainer,
        get_application_container,
        set_application_container
    )
except ImportError:
    ApplicationServiceContainer = None
    get_application_container = None
    set_application_container = None

__all__ = [
    'StrategyApplicationService',
    'TriggerApplicationService',
    'BacktestApplicationService',
    'ApplicationServiceContainer',
    'get_application_container',
    'set_application_container'
]
