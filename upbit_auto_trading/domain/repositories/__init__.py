"""
Repository 인터페이스 패키지

이 패키지는 도메인 계층과 데이터 접근 계층 간의 추상화를 제공하는
Repository 패턴의 인터페이스들을 정의합니다.

각 Repository 인터페이스는 특정 도메인 엔티티나 데이터 영역에 대한
데이터 접근 방법을 추상화하며, 구체적인 구현은 Infrastructure Layer에서
제공됩니다.

사용 예시:
    from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
    from upbit_auto_trading.domain.repositories.settings_repository import SettingsRepository
    
주요 Repository 인터페이스:
    - BaseRepository: 모든 Repository의 기본 인터페이스
    - StrategyRepository: 전략 데이터 접근 인터페이스
    - TriggerRepository: 트리거 데이터 접근 인터페이스  
    - SettingsRepository: 설정 데이터 접근 인터페이스 (읽기 전용)
    - MarketDataRepository: 시장 데이터 접근 인터페이스
    - BacktestRepository: 백테스팅 결과 데이터 접근 인터페이스
    - RepositoryFactory: Repository 생성을 위한 추상 팩토리
"""

# 향후 Repository 인터페이스들의 편리한 import를 위한 __all__ 정의
# 실제 구현 파일들이 생성되면 주석을 해제하여 사용

# from .base_repository import BaseRepository
# from .strategy_repository import StrategyRepository
# from .trigger_repository import TriggerRepository
# from .settings_repository import SettingsRepository
# from .market_data_repository import MarketDataRepository
# from .backtest_repository import BacktestRepository
# from .repository_factory import RepositoryFactory

# __all__ = [
#     'BaseRepository',
#     'StrategyRepository', 
#     'TriggerRepository',
#     'SettingsRepository',
#     'MarketDataRepository',
#     'BacktestRepository',
#     'RepositoryFactory',
# ]
