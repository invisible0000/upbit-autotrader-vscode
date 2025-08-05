"""
Application Context - 설정과 의존성 주입을 통합 관리하는 애플리케이션 컨텍스트
Clean Architecture Infrastructure Layer의 핵심 통합 컴포넌트
"""

from typing import Optional, Any
import logging
from pathlib import Path

from upbit_auto_trading.infrastructure.config.models.config_models import ApplicationConfig
from upbit_auto_trading.infrastructure.config.loaders.config_loader import ConfigLoader
from upbit_auto_trading.infrastructure.dependency_injection.container import DIContainer


class ApplicationContextError(Exception):
    """애플리케이션 컨텍스트 관련 오류"""
    pass


class ApplicationContext:
    """
    애플리케이션 컨텍스트 - 설정과 의존성 주입을 통합 관리

    Clean Architecture의 Infrastructure Layer에서 애플리케이션 전체 생명주기를 관리:
    - 환경별 설정 로드 및 검증
    - 로깅 시스템 설정
    - 의존성 주입 컨테이너 관리
    - 핵심 서비스들의 등록 및 생명주기 관리
    """

    def __init__(self, environment: Optional[str] = None, config_dir: str = "config"):
        """
        Args:
            environment: 실행 환경 (None이면 환경변수에서 자동 감지)
            config_dir: 설정 파일 디렉토리 경로
        """
        self._environment = environment
        self._config_dir = config_dir
        self._config: Optional[ApplicationConfig] = None
        self._container: Optional[DIContainer] = None
        self._logger = logging.getLogger(__name__)
        self._initialized = False

    def initialize(self) -> None:
        """
        애플리케이션 컨텍스트 초기화

        초기화 단계:
        1. 설정 로드 및 검증
        2. 로깅 시스템 설정
        3. 의존성 주입 컨테이너 설정
        4. 핵심 서비스 등록

        Raises:
            ApplicationContextError: 초기화 실패 시
        """
        if self._initialized:
            self._logger.debug("애플리케이션 컨텍스트가 이미 초기화되었습니다")
            return

        try:
            # 1. 설정 로드
            self._load_configuration()

            # 2. 로깅 설정
            self._setup_logging()

            # 3. 의존성 컨테이너 설정
            self._setup_dependency_injection()

            # 4. 핵심 서비스 등록
            self._register_core_services()

            self._initialized = True
            self._logger.info(
                f"✅ 애플리케이션 컨텍스트 초기화 완료 (환경: {self.config.environment.value})"
            )

        except Exception as e:
            self._logger.error(f"❌ 애플리케이션 컨텍스트 초기화 실패: {e}")
            # 실패 시 부분적으로 초기화된 상태 정리
            self._cleanup_on_failure()
            raise ApplicationContextError(f"애플리케이션 컨텍스트 초기화 실패: {e}") from e

    def _load_configuration(self) -> None:
        """설정 로드 및 검증"""
        try:
            config_loader = ConfigLoader(self._config_dir)
            self._config = config_loader.load_config(self._environment)

            self._logger.debug(f"설정 로드 완료: {self._config.environment.value}")
        except Exception as e:
            raise ApplicationContextError(f"설정 로드 실패: {e}") from e

    def _setup_logging(self) -> None:
        """로깅 시스템 설정"""
        try:
            if not self._config:
                raise ApplicationContextError("설정이 로드되지 않았습니다")

            log_config = self._config.logging

            # 루트 로거 레벨 설정
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, log_config.level.upper()))

            # 로그 디렉토리 생성
            if log_config.file_enabled:
                log_path = Path(log_config.file_path)
                log_path.parent.mkdir(parents=True, exist_ok=True)

            self._logger.debug("로깅 설정 완료")
        except Exception as e:
            raise ApplicationContextError(f"로깅 설정 실패: {e}") from e

    def _setup_dependency_injection(self) -> None:
        """의존성 주입 컨테이너 설정"""
        try:
            self._container = DIContainer()

            # 설정 객체를 컨테이너에 등록 (싱글톤)
            self._container.register_instance(ApplicationConfig, self._config)

            self._logger.debug("의존성 주입 컨테이너 설정 완료")
        except Exception as e:
            raise ApplicationContextError(f"의존성 주입 컨테이너 설정 실패: {e}") from e

    def _register_core_services(self) -> None:
        """핵심 서비스 등록"""
        try:
            # 각 서비스 등록을 단계별로 처리
            self._register_database_services()
            self._register_api_services()
            self._register_repositories()
            self._register_event_system()
            self._register_application_services()

            self._logger.debug("핵심 서비스 등록 완료")
        except Exception as e:
            raise ApplicationContextError(f"핵심 서비스 등록 실패: {e}") from e

    def _register_database_services(self) -> None:
        """데이터베이스 관련 서비스 등록"""
        # DatabaseManager 등록 (향후 구현)
        # 현재는 placeholder로 남겨둠
        self._logger.debug("데이터베이스 서비스 등록 (placeholder)")

    def _register_api_services(self) -> None:
        """API 클라이언트 서비스 등록"""
        # API 클라이언트들 등록 (향후 구현)
        # 현재는 placeholder로 남겨둠
        self._logger.debug("API 서비스 등록 (placeholder)")

    def _register_repositories(self) -> None:
        """Repository 등록"""
        # 이전 TASK에서 구현된 Repository들을 등록
        # 실제 구현에서는 다음과 같이 등록:
        # self._container.register_singleton(IStrategyRepository, SqliteStrategyRepository)
        # self._container.register_singleton(ITriggerRepository, SqliteTriggerRepository)
        # 현재는 placeholder로 남겨둠
        self._logger.debug("Repository 등록 (placeholder)")

    def _register_event_system(self) -> None:
        """Event System 등록"""
        # 이전 TASK에서 구현된 Event Bus를 등록
        # 실제 구현에서는 다음과 같이 등록:
        # self._container.register_singleton(IEventBus, InMemoryEventBus)
        # 현재는 placeholder로 남겨둠
        self._logger.debug("Event System 등록 (placeholder)")

    def _register_application_services(self) -> None:
        """Application Service 등록"""
        # Application Layer의 서비스들 등록
        # 실제 구현에서는 다음과 같이 등록:
        # self._container.register_transient(StrategyApplicationService)
        # self._container.register_transient(TriggerApplicationService)
        # 현재는 placeholder로 남겨둠
        self._logger.debug("Application Service 등록 (placeholder)")

    def _cleanup_on_failure(self) -> None:
        """초기화 실패 시 정리 작업"""
        if self._container:
            try:
                self._container.dispose()
            except Exception as e:
                self._logger.warning(f"컨테이너 정리 중 오류: {e}")
            self._container = None
        self._initialized = False

    @property
    def config(self) -> ApplicationConfig:
        """
        애플리케이션 설정 조회

        Returns:
            ApplicationConfig: 현재 애플리케이션 설정

        Raises:
            RuntimeError: 컨텍스트가 초기화되지 않은 경우
        """
        if not self._initialized or not self._config:
            raise RuntimeError("애플리케이션 컨텍스트가 초기화되지 않았습니다")
        return self._config

    @property
    def container(self) -> DIContainer:
        """
        의존성 주입 컨테이너 조회

        Returns:
            DIContainer: 의존성 주입 컨테이너

        Raises:
            RuntimeError: 컨텍스트가 초기화되지 않은 경우
        """
        if not self._initialized or not self._container:
            raise RuntimeError("애플리케이션 컨텍스트가 초기화되지 않았습니다")
        return self._container

    @property
    def is_initialized(self) -> bool:
        """초기화 상태 확인"""
        return self._initialized

    def resolve(self, service_type: type) -> Any:
        """
        서비스 해결 (의존성 주입 컨테이너 위임)

        Args:
            service_type: 해결할 서비스 타입

        Returns:
            Any: 해결된 서비스 인스턴스
        """
        return self.container.resolve(service_type)

    def create_scope(self) -> DIContainer:
        """
        새 의존성 스코프 생성

        Returns:
            DIContainer: 새로운 스코프 컨테이너
        """
        return self.container.create_scope()

    def reload_configuration(self) -> None:
        """
        설정 다시 로드

        주의: 이미 생성된 서비스 인스턴스들은 새 설정을 반영하지 않을 수 있음
        """
        if not self._initialized or not self._config or not self._container:
            self._logger.warning("컨텍스트가 초기화되지 않아 설정 리로드를 건너뜁니다")
            return

        try:
            self._logger.info("설정 다시 로드 중...")

            # 새 설정 로드
            config_loader = ConfigLoader(self._config_dir)
            new_config = config_loader.load_config(self._environment)

            # 설정 업데이트
            old_env = self._config.environment
            self._config = new_config

            # 컨테이너의 설정 인스턴스 업데이트
            self._container.register_instance(ApplicationConfig, self._config)

            self._logger.info(
                f"설정 다시 로드 완료: {old_env.value} -> {new_config.environment.value}"
            )

        except Exception as e:
            self._logger.error(f"설정 리로드 실패: {e}")
            raise ApplicationContextError(f"설정 리로드 실패: {e}") from e

    def dispose(self) -> None:
        """
        애플리케이션 컨텍스트 해제

        모든 관리되는 리소스를 정리하고 컨테이너를 해제합니다.
        """
        if not self._initialized:
            self._logger.debug("컨텍스트가 이미 해제되었거나 초기화되지 않았습니다")
            return

        try:
            if self._container:
                self._container.dispose()
                self._container = None

            self._config = None
            self._initialized = False

            self._logger.info("애플리케이션 컨텍스트 해제 완료")

        except Exception as e:
            self._logger.error(f"컨텍스트 해제 중 오류: {e}")
            # 해제 실패해도 상태는 정리
            self._container = None
            self._config = None
            self._initialized = False

    def __enter__(self) -> 'ApplicationContext':
        """컨텍스트 매니저 진입"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """컨텍스트 매니저 종료"""
        self.dispose()

    def __repr__(self) -> str:
        """문자열 표현"""
        if self._initialized and self._config:
            env = self._config.environment.value
            return f"ApplicationContext(environment={env}, initialized=True)"
        else:
            return f"ApplicationContext(environment={self._environment}, initialized=False)"


# 애플리케이션 전역 컨텍스트 (선택적 사용)
_app_context: Optional[ApplicationContext] = None


def get_application_context() -> ApplicationContext:
    """
    전역 애플리케이션 컨텍스트 조회

    싱글톤 패턴으로 전역 컨텍스트를 관리합니다.
    처음 호출 시 자동으로 초기화됩니다.

    Returns:
        ApplicationContext: 전역 애플리케이션 컨텍스트

    Raises:
        ApplicationContextError: 초기화 실패 시
    """
    global _app_context
    if _app_context is None:
        _app_context = ApplicationContext()
        _app_context.initialize()
    return _app_context


def set_application_context(context: ApplicationContext) -> None:
    """
    전역 애플리케이션 컨텍스트 설정

    기존 컨텍스트가 있다면 먼저 해제한 후 새 컨텍스트를 설정합니다.

    Args:
        context: 설정할 애플리케이션 컨텍스트
    """
    global _app_context
    if _app_context and _app_context.is_initialized:
        _app_context.dispose()
    _app_context = context


def reset_application_context() -> None:
    """
    전역 애플리케이션 컨텍스트 재설정

    현재 전역 컨텍스트를 해제하고 초기화 상태로 돌립니다.
    """
    global _app_context
    if _app_context and _app_context.is_initialized:
        _app_context.dispose()
    _app_context = None


def is_application_context_initialized() -> bool:
    """
    전역 애플리케이션 컨텍스트 초기화 상태 확인

    Returns:
        bool: 초기화 여부
    """
    global _app_context
    return _app_context is not None and _app_context.is_initialized
