"""
Repository 팩토리 인터페이스

DI 컨테이너와 호환되는 Abstract Factory 패턴을 통해
모든 Repository 인터페이스의 생성을 관리합니다.
"""

from abc import ABC, abstractmethod

from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
from upbit_auto_trading.domain.repositories.trigger_repository import TriggerRepository
from upbit_auto_trading.domain.repositories.settings_repository import SettingsRepository
from upbit_auto_trading.domain.repositories.market_data_repository import MarketDataRepository
from upbit_auto_trading.domain.repositories.backtest_repository import BacktestRepository

class RepositoryFactory(ABC):
    """
    Repository 생성을 위한 추상 팩토리 인터페이스
    
    Abstract Factory 패턴을 사용하여 모든 Repository 인스턴스의
    생성을 관리하고, 의존성 주입과 테스트 가능성을 제공합니다.
    
    구현체는 Infrastructure Layer에서 제공되며,
    SQLite, MySQL, PostgreSQL 등 다양한 데이터 소스를 지원할 수 있습니다.
    
    Example:
        >>> # Production에서 SQLite 팩토리 사용
        >>> factory = SqliteRepositoryFactory()
        >>> strategy_repo = factory.create_strategy_repository()
        >>>
        >>> # 테스트에서 In-Memory 팩토리 사용
        >>> test_factory = InMemoryRepositoryFactory()
        >>> test_strategy_repo = test_factory.create_strategy_repository()
    """

    @abstractmethod
    def create_strategy_repository(self) -> StrategyRepository:
        """
        전략 Repository 생성
        
        strategies.sqlite3의 전략 관련 테이블에 접근하는
        StrategyRepository 구현체를 생성합니다.
        
        Returns:
            StrategyRepository: 전략 데이터 접근 Repository
            
        Raises:
            RepositoryCreationError: Repository 생성 실패 시
        """
        pass

    @abstractmethod
    def create_trigger_repository(self) -> TriggerRepository:
        """
        트리거 Repository 생성
        
        strategies.sqlite3의 strategy_conditions 테이블에 접근하는
        TriggerRepository 구현체를 생성합니다.
        
        Returns:
            TriggerRepository: 트리거 데이터 접근 Repository
            
        Raises:
            RepositoryCreationError: Repository 생성 실패 시
        """
        pass

    @abstractmethod
    def create_settings_repository(self) -> SettingsRepository:
        """
        설정 Repository 생성 (읽기 전용)
        
        settings.sqlite3의 매매 변수, 파라미터, 카테고리 테이블에
        접근하는 SettingsRepository 구현체를 생성합니다.
        
        Note:
            이 Repository는 읽기 전용입니다.
            설정 데이터는 시스템 초기화 시에만 로드됩니다.
        
        Returns:
            SettingsRepository: 설정 데이터 접근 Repository
            
        Raises:
            RepositoryCreationError: Repository 생성 실패 시
        """
        pass

    @abstractmethod
    def create_market_data_repository(self) -> MarketDataRepository:
        """
        시장 데이터 Repository 생성
        
        market_data.sqlite3의 시장 데이터, 기술적 지표, 실시간 데이터
        테이블에 접근하는 MarketDataRepository 구현체를 생성합니다.
        
        Returns:
            MarketDataRepository: 시장 데이터 접근 Repository
            
        Raises:
            RepositoryCreationError: Repository 생성 실패 시
        """
        pass

    @abstractmethod
    def create_backtest_repository(self) -> BacktestRepository:
        """
        백테스팅 Repository 생성
        
        strategies.sqlite3의 시뮬레이션 및 백테스팅 결과 테이블에
        접근하는 BacktestRepository 구현체를 생성합니다.
        
        Returns:
            BacktestRepository: 백테스팅 데이터 접근 Repository
            
        Raises:
            RepositoryCreationError: Repository 생성 실패 시
        """
        pass

    # =====================================
    # 팩토리 설정 및 구성
    # =====================================

    @abstractmethod
    def configure_database_connections(self, config: dict) -> None:
        """
        데이터베이스 연결 설정
        
        Repository들이 사용할 데이터베이스 연결 정보를 설정합니다.
        
        Args:
            config: 데이터베이스 설정 딕셔너리
                   예: {
                       "settings_db_path": "data/settings.sqlite3",
                       "strategies_db_path": "data/strategies.sqlite3",
                       "market_data_db_path": "data/market_data.sqlite3",
                       "connection_pool_size": 10,
                       "timeout": 30
                   }
                   
        Raises:
            ConfigurationError: 설정 정보가 유효하지 않을 때
        """
        pass

    @abstractmethod
    def validate_database_schema(self) -> bool:
        """
        데이터베이스 스키마 유효성 검증
        
        모든 필요한 테이블과 인덱스가 올바르게 생성되어 있는지 확인합니다.
        
        Returns:
            bool: 스키마 유효성 여부
            
        Raises:
            SchemaValidationError: 스키마 검증 실패 시
        """
        pass

    @abstractmethod
    def get_database_health_status(self) -> dict:
        """
        데이터베이스 상태 정보 조회
        
        모든 데이터베이스의 연결 상태, 크기, 성능 지표 등을 조회합니다.
        
        Returns:
            dict: 데이터베이스별 상태 정보
                 예: {
                     "settings_db": {
                         "status": "connected",
                         "size_mb": 2.1,
                         "table_count": 5
                     },
                     "strategies_db": {
                         "status": "connected",
                         "size_mb": 15.7,
                         "table_count": 12
                     },
                     "market_data_db": {
                         "status": "connected",
                         "size_mb": 250.3,
                         "table_count": 8
                     }
                 }
        """
        pass

    # =====================================
    # 리소스 관리
    # =====================================

    @abstractmethod
    def create_all_repositories(self) -> dict:
        """
        모든 Repository 일괄 생성
        
        시스템 초기화 시 필요한 모든 Repository를 한 번에 생성합니다.
        
        Returns:
            dict: Repository명과 인스턴스의 매핑
                 예: {
                     "strategy": StrategyRepository,
                     "trigger": TriggerRepository,
                     "settings": SettingsRepository,
                     "market_data": MarketDataRepository,
                     "backtest": BacktestRepository
                 }
                 
        Raises:
            RepositoryCreationError: Repository 생성 실패 시
        """
        pass

    @abstractmethod
    def cleanup_resources(self) -> None:
        """
        리소스 정리
        
        모든 데이터베이스 연결을 종료하고 리소스를 해제합니다.
        애플리케이션 종료 시 호출됩니다.
        """
        pass

    @abstractmethod
    def is_factory_healthy(self) -> bool:
        """
        팩토리 상태 확인
        
        팩토리가 Repository를 생성할 수 있는 상태인지 확인합니다.
        
        Returns:
            bool: 팩토리 정상 동작 여부
        """
        pass

    # =====================================
    # 개발 및 테스트 지원
    # =====================================

    @abstractmethod
    def create_repository_for_testing(self, repository_type: str) -> object:
        """
        테스트용 Repository 생성
        
        단위 테스트나 통합 테스트에서 사용할 Repository를 생성합니다.
        In-Memory DB나 Mock 객체를 사용할 수 있습니다.
        
        Args:
            repository_type: Repository 타입
                           ('strategy', 'trigger', 'settings', 'market_data', 'backtest')
                           
        Returns:
            object: 테스트용 Repository 인스턴스
            
        Raises:
            ValueError: 지원하지 않는 Repository 타입
            RepositoryCreationError: Repository 생성 실패 시
        """
        pass

    @abstractmethod
    def reset_all_data(self) -> None:
        """
        모든 데이터 초기화
        
        테스트 환경에서 모든 데이터베이스 데이터를 초기화합니다.
        
        Warning:
            이 메서드는 테스트 환경에서만 사용해야 합니다.
            프로덕션 환경에서 호출하면 모든 데이터가 손실될 수 있습니다.
            
        Raises:
            ProductionEnvironmentError: 프로덕션 환경에서 호출 시
        """
        pass

    # =====================================
    # Repository 특화 팩토리 메서드
    # =====================================

    @abstractmethod
    def create_repository_with_custom_config(self,
                                            repository_type: str,
                                            custom_config: dict) -> object:
        """
        커스텀 설정으로 Repository 생성
        
        기본 설정과 다른 특별한 설정이 필요한 Repository를 생성합니다.
        
        Args:
            repository_type: Repository 타입
            custom_config: 커스텀 설정 딕셔너리
            
        Returns:
            object: 커스텀 설정이 적용된 Repository
            
        Example:
            >>> # 백테스팅용 읽기 전용 MarketDataRepository
            >>> config = {"read_only": True, "cache_size": 1000}
            >>> repo = factory.create_repository_with_custom_config(
            ...     "market_data", config
            ... )
        """
        pass

    @abstractmethod
    def get_repository_dependencies(self, repository_type: str) -> list:
        """
        Repository 의존성 조회
        
        특정 Repository가 의존하는 다른 Repository나 서비스 목록을 조회합니다.
        
        Args:
            repository_type: Repository 타입
            
        Returns:
            list: 의존성 목록
            
        Example:
            >>> deps = factory.get_repository_dependencies("trigger")
            >>> # ['settings_repository', 'strategy_repository']
        """
        pass

    @abstractmethod
    def create_repository_chain(self, repository_types: list) -> dict:
        """
        Repository 체인 생성
        
        서로 의존관계가 있는 Repository들을 올바른 순서로 생성합니다.
        
        Args:
            repository_types: 생성할 Repository 타입 목록
            
        Returns:
            dict: 의존성 순서대로 생성된 Repository 매핑
            
        Example:
            >>> repos = factory.create_repository_chain([
            ...     "settings", "strategy", "trigger"
            ... ])
            >>> # settings가 먼저 생성되고, 그 다음 strategy, trigger 순서
        """
        pass
