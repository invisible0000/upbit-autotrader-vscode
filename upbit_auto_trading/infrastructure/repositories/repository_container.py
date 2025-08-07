#!/usr/bin/env python3
"""
Repository Container - 의존성 주입 컨테이너
===========================================

Infrastructure Layer의 모든 Repository 구현체들을 관리하는 의존성 주입 컨테이너입니다.
Domain Layer는 이 컨테이너를 통해 Repository 인터페이스를 구현체 없이 사용할 수 있습니다.

Features:
- Dependency Injection: Repository 인터페이스와 구현체 분리
- Singleton Pattern: Repository 인스턴스 재사용으로 성능 최적화
- Multi-DB Support: 3-DB 아키텍처 (settings, strategies, market_data) 지원
- Lazy Loading: 실제 사용 시점에 Repository 인스턴스 생성
- Testability: Mock Repository 주입 가능한 구조

Container Management:
- 모든 Repository 인스턴스의 라이프사이클 관리
- 데이터베이스 연결 풀링 및 트랜잭션 경계 제어
- Application Shutdown 시 리소스 정리
"""

from typing import Optional, Dict, Any
import logging

# Domain Repository 인터페이스들
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
from upbit_auto_trading.domain.repositories.trigger_repository import TriggerRepository
from upbit_auto_trading.domain.repositories.settings_repository import SettingsRepository
from upbit_auto_trading.domain.repositories.secure_keys_repository import SecureKeysRepository

# Infrastructure 구현체들
from upbit_auto_trading.infrastructure.repositories.sqlite_strategy_repository import SqliteStrategyRepository
from upbit_auto_trading.infrastructure.repositories.sqlite_trigger_repository import SqliteTriggerRepository
from upbit_auto_trading.infrastructure.repositories.sqlite_settings_repository import SqliteSettingsRepository
from upbit_auto_trading.infrastructure.repositories.sqlite_secure_keys_repository import SqliteSecureKeysRepository
from upbit_auto_trading.infrastructure.database.database_manager import (
    DatabaseConnectionProvider
)


class RepositoryContainer:
    """
    Repository들의 의존성 주입 컨테이너

    Application Layer와 Domain Layer가 Infrastructure 세부사항에 의존하지 않도록
    Repository 인터페이스와 구현체 간의 연결을 관리합니다.

    주요 특징:
    - Singleton Pattern: Repository 인스턴스 재사용
    - Lazy Loading: 필요한 시점에 인스턴스 생성
    - 리소스 관리: 데이터베이스 연결 및 트랜잭션 제어
    - Mock 지원: 테스트 환경에서 Mock Repository 주입 가능
    """

    def __init__(self, db_paths: Optional[Dict[str, str]] = None):
        """
        Repository Container 초기화

        Args:
            db_paths: 데이터베이스 파일 경로 딕셔너리
                     기본값: {'settings': 'data/settings.sqlite3', ...}
        """
        self._logger = logging.getLogger(__name__)

        # 기본 데이터베이스 경로 설정
        if db_paths is None:
            db_paths = {
                'settings': 'data/settings.sqlite3',
                'strategies': 'data/strategies.sqlite3',
                'market_data': 'data/market_data.sqlite3'
            }

        # 데이터베이스 연결 초기화
        try:
            provider = DatabaseConnectionProvider()
            provider.initialize(db_paths)
            self._db_manager = provider.get_manager()
            self._logger.info("✅ Repository Container 데이터베이스 연결 초기화 완료")
        except Exception as e:
            self._logger.error(f"❌ 데이터베이스 연결 초기화 실패: {e}")
            raise

        # Repository 인스턴스들 (Lazy Loading용)
        self._strategy_repository: Optional[StrategyRepository] = None
        self._trigger_repository: Optional[TriggerRepository] = None
        self._settings_repository: Optional[SettingsRepository] = None
        self._secure_keys_repository: Optional[SecureKeysRepository] = None

        # Mock Repository 오버라이드 (테스트용)
        self._mock_repositories: Dict[str, Any] = {}

    def get_strategy_repository(self) -> StrategyRepository:
        """
        Strategy Repository 반환

        Returns:
            StrategyRepository: 전략 도메인 Repository 인터페이스
        """
        # Mock Repository 확인
        if 'strategy' in self._mock_repositories:
            return self._mock_repositories['strategy']

        # Lazy Loading
        if self._strategy_repository is None:
            self._strategy_repository = SqliteStrategyRepository(self._db_manager)
            self._logger.info("✅ SqliteStrategyRepository 초기화 완료")

        return self._strategy_repository

    def get_trigger_repository(self) -> TriggerRepository:
        """
        Trigger Repository 반환

        Returns:
            TriggerRepository: 트리거 도메인 Repository 인터페이스
        """
        # Mock Repository 확인
        if 'trigger' in self._mock_repositories:
            return self._mock_repositories['trigger']

        # Lazy Loading
        if self._trigger_repository is None:
            self._trigger_repository = SqliteTriggerRepository(self._db_manager)  # type: ignore
            self._logger.debug("🔧 SqliteTriggerRepository 인스턴스 생성")

        return self._trigger_repository

    def get_settings_repository(self) -> SettingsRepository:
        """
        Settings Repository 반환 (읽기 전용)

        Returns:
            SettingsRepository: 설정 도메인 Repository 인터페이스
        """
        # Mock Repository 확인
        if 'settings' in self._mock_repositories:
            return self._mock_repositories['settings']

        # Lazy Loading
        if self._settings_repository is None:
            self._settings_repository = SqliteSettingsRepository(self._db_manager)  # type: ignore
            self._logger.debug("🔧 SqliteSettingsRepository 인스턴스 생성")

        return self._settings_repository

    def get_secure_keys_repository(self) -> SecureKeysRepository:
        """
        Secure Keys Repository 반환 (보안 키 관리)

        Returns:
            SecureKeysRepository: 보안 키 도메인 Repository 인터페이스
        """
        # Mock Repository 확인
        if 'secure_keys' in self._mock_repositories:
            return self._mock_repositories['secure_keys']

        # Lazy Loading
        if self._secure_keys_repository is None:
            self._secure_keys_repository = SqliteSecureKeysRepository(self._db_manager)  # type: ignore
            self._logger.debug("🔧 SqliteSecureKeysRepository 인스턴스 생성")

        return self._secure_keys_repository

    def get_market_data_repository(self):
        """
        Market Data Repository 반환 (추후 구현)

        Note:
            Phase 3에서 구현 예정
        """
        # Mock Repository 확인
        if 'market_data' in self._mock_repositories:
            return self._mock_repositories['market_data']

        # TODO: SqliteMarketDataRepository 구현
        self._logger.warning("⚠️ Market Data Repository는 추후 구현 예정")
        raise NotImplementedError("Market Data Repository는 Phase 3에서 구현 예정")

    def get_backtest_repository(self):
        """
        Backtest Repository 반환 (추후 구현)

        Note:
            Phase 4에서 구현 예정
        """
        # Mock Repository 확인
        if 'backtest' in self._mock_repositories:
            return self._mock_repositories['backtest']

        # TODO: SqliteBacktestRepository 구현
        self._logger.warning("⚠️ Backtest Repository는 추후 구현 예정")
        raise NotImplementedError("Backtest Repository는 Phase 4에서 구현 예정")

    # ===================================
    # 테스트 지원 메서드들
    # ===================================

    def set_mock_repository(self, repository_name: str, mock_instance: Any) -> None:
        """
        Mock Repository 설정 (테스트용)

        Args:
            repository_name: Repository 이름 ('strategy', 'trigger', 'settings', etc.)
            mock_instance: Mock Repository 인스턴스
        """
        self._mock_repositories[repository_name] = mock_instance
        self._logger.debug(f"🧪 Mock Repository 설정: {repository_name}")

    def clear_mock_repositories(self) -> None:
        """Mock Repository 설정 초기화"""
        self._mock_repositories.clear()
        self._logger.debug("🧹 Mock Repository 설정 초기화")

    def is_using_mock(self, repository_name: str) -> bool:
        """특정 Repository가 Mock을 사용 중인지 확인"""
        return repository_name in self._mock_repositories

    # ===================================
    # 리소스 관리 메서드들
    # ===================================

    def close_all_connections(self) -> None:
        """모든 데이터베이스 연결 종료"""
        try:
            if hasattr(self, '_db_manager') and self._db_manager:
                self._db_manager.close_all()
                self._logger.info("✅ 모든 데이터베이스 연결 종료 완료")
        except Exception as e:
            self._logger.error(f"❌ 데이터베이스 연결 종료 실패: {e}")

    def get_health_status(self) -> Dict[str, Any]:
        """
        Container 및 Repository 상태 확인

        Returns:
            Dict: 상태 정보 딕셔너리
        """
        status = {
            'database_connected': False,
            'active_repositories': [],
            'mock_repositories': list(self._mock_repositories.keys()),
            'timestamp': None
        }

        try:
            # 데이터베이스 연결 상태 확인
            if hasattr(self, '_db_manager') and self._db_manager:
                # 간단한 쿼리로 연결 테스트
                self._db_manager.execute_query('settings', 'SELECT 1 as test')
                status['database_connected'] = True

            # 활성 Repository 확인
            if self._trigger_repository is not None:
                status['active_repositories'].append('trigger')
            if self._settings_repository is not None:
                status['active_repositories'].append('settings')
            if self._strategy_repository is not None:
                status['active_repositories'].append('strategy')
            if self._secure_keys_repository is not None:
                status['active_repositories'].append('secure_keys')

            from datetime import datetime
            status['timestamp'] = datetime.now().isoformat()

        except Exception as e:
            self._logger.error(f"❌ 상태 확인 실패: {e}")
            status['error'] = str(e)

        return status

    def __enter__(self):
        """Context Manager 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager 종료 - 리소스 정리"""
        self.close_all_connections()

        if exc_type is not None:
            self._logger.error(f"❌ Repository Container 예외 발생: {exc_type.__name__}: {exc_val}")

        return False  # 예외 재발생

    def __del__(self):
        """소멸자 - 리소스 정리"""
        try:
            self.close_all_connections()
        except Exception:
            # 소멸자에서는 예외를 무시 (로깅도 위험할 수 있음)
            pass
