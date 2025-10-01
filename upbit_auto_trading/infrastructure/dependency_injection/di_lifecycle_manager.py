"""
DI Lifecycle Manager - DI 컨테이너 생명주기 관리 전담
Clean Architecture + dependency-injector 기반 컨테이너 생명주기 관리자
"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from upbit_auto_trading.application.application_service_container import ApplicationServiceContainer
    from upbit_auto_trading.presentation.presentation_container import PresentationContainer

from upbit_auto_trading.infrastructure.dependency_injection.external_dependency_container import (
    ExternalDependencyContainer,
    create_external_dependency_container,
    wire_external_dependency_modules,
    validate_external_dependency_container
)
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("DILifecycleManager")


class DILifecycleManagerError(Exception):
    """DI 생명주기 관리자 관련 오류"""
    pass


class DILifecycleManager:
    """
    DI 컨테이너 생명주기 관리자

    Container Management:
    - External Dependency Container 생명주기 관리
    - Application Service Container 연동
    - Wiring 설정 및 검증
    - Container 상태 모니터링

    Clean Architecture DI System의 핵심 컴포넌트로서
    모든 Container들의 생명주기를 중앙 집중식으로 관리합니다.
    """

    def __init__(self, external_container: Optional[ExternalDependencyContainer] = None):
        """
        Args:
            external_container: 사용할 ExternalDependencyContainer (None이면 새로 생성)
        """
        self._external_container: Optional[ExternalDependencyContainer] = external_container
        self._application_container: Optional['ApplicationServiceContainer'] = None
        self._presentation_container: Optional['PresentationContainer'] = None
        self._is_initialized = False
        logger.debug("DILifecycleManager 생성 - DI 컨테이너 생명주기 관리 모드")

    def initialize(self) -> None:
        """
        3-Container DI 시스템 초기화

        확장된 3-Container 초기화 프로세스:
        1. External Dependency Container 준비 (Infrastructure Layer)
        2. Application Service Container 생성 (Business Logic Layer)
        3. Presentation Container 생성 (UI Layer)
        4. Container 간 의존성 주입 설정
        5. 통합 Wiring 설정
        6. 전체 시스템 검증 완료
        """
        if self._is_initialized:
            logger.debug("DILifecycleManager가 이미 초기화되었습니다")
            return

        try:
            # 1. External Dependency Container 준비 (Infrastructure Layer)
            if self._external_container is None:
                self._external_container = create_external_dependency_container()
                logger.info("🏗️ ExternalDependencyContainer 생성 완료 (Infrastructure Layer)")
            else:
                logger.info("🏗️ 기존 ExternalDependencyContainer 사용 (Infrastructure Layer)")

            # 2. Application Service Container 생성 (Business Logic Layer)
            repository_container = self._external_container.repository_container()

            from upbit_auto_trading.application.application_service_container import ApplicationServiceContainer
            from upbit_auto_trading.application import set_application_container

            self._application_container = ApplicationServiceContainer(repository_container)
            set_application_container(self._application_container)
            logger.info("✅ ApplicationServiceContainer 생성 완료 (Business Logic Layer)")

            # 3. Presentation Container 생성 (UI Layer)
            from upbit_auto_trading.presentation.presentation_container import create_presentation_container

            self._presentation_container = create_presentation_container(
                external_container=self._external_container,
                application_container=self._application_container
            )
            logger.info("✅ PresentationContainer 생성 완료 (UI Layer)")

            # 4. Container 간 의존성 주입 검증
            if not validate_external_dependency_container(self._external_container):
                raise RuntimeError("External Dependency Container 등록 검증 실패")

            # 5. 통합 Wiring 설정
            wire_external_dependency_modules(self._external_container)
            self._wire_presentation_modules()

            self._is_initialized = True
            logger.info("🎉 3-Container DI 시스템 초기화 완료 - 모든 계층 활성화")

        except Exception as e:
            logger.error(f"❌ DILifecycleManager 초기화 실패: {e}")
            self._cleanup()
            raise RuntimeError(f"DILifecycleManager 초기화 실패: {e}") from e

    def get_external_container(self) -> ExternalDependencyContainer:
        """
        External Dependency Container 조회

        Returns:
            ExternalDependencyContainer: 현재 관리 중인 외부 의존성 컨테이너

        Raises:
            RuntimeError: 초기화되지 않은 경우
        """
        if not self._is_initialized or not self._external_container:
            raise RuntimeError("DILifecycleManager가 초기화되지 않았습니다")
        return self._external_container

    def get_application_container(self) -> 'ApplicationServiceContainer':
        """
        Application Service Container 조회

        Returns:
            ApplicationServiceContainer: 현재 관리 중인 애플리케이션 서비스 컨테이너

        Raises:
            RuntimeError: 초기화되지 않은 경우
        """
        if not self._is_initialized or not self._application_container:
            raise RuntimeError("DILifecycleManager가 초기화되지 않았습니다")
        return self._application_container

    def get_presentation_container(self) -> 'PresentationContainer':
        """
        Presentation Container 조회

        Returns:
            PresentationContainer: 현재 관리 중인 프레젠테이션 컨테이너

        Raises:
            RuntimeError: 초기화되지 않은 경우
        """
        if not self._is_initialized or not self._presentation_container:
            raise RuntimeError("DILifecycleManager가 초기화되지 않았습니다")
        return self._presentation_container

    @property
    def is_initialized(self) -> bool:
        """초기화 상태 확인"""
        return self._is_initialized

    def reload_configuration(self, config_path: str = "config/config.yaml") -> None:
        """
        설정 다시 로드

        Args:
            config_path: 설정 파일 경로
        """
        if not self._is_initialized or not self._external_container:
            logger.warning("초기화되지 않은 상태에서 설정 리로드를 시도합니다")
            return

        try:
            logger.info(f"📄 설정 파일 다시 로드: {config_path}")
            self._external_container.config.from_yaml(config_path)
            logger.info("✅ 설정 리로드 완료")

        except Exception as e:
            logger.error(f"❌ 설정 리로드 실패: {e}")
            # 폴백 설정으로 복구
            self._external_container.config.from_dict({
                "database": {
                    "fallback_settings_db": "data/settings.sqlite3",
                    "fallback_strategies_db": "data/strategies.sqlite3",
                    "fallback_market_data_db": "data/market_data.sqlite3"
                },
                "logging": {
                    "level": "INFO",
                    "console_enabled": True
                },
                "app_name": "Upbit Auto Trading",
                "app_version": "1.0.0"
            })
            logger.info("🔄 기본 설정으로 폴백 완료")

    def shutdown(self) -> None:
        """
        DI 시스템 종료

        Container와 관련 리소스를 정리합니다.
        """
        logger.info("🚀 DILifecycleManager 종료 시작")

        try:
            self._cleanup()
            logger.info("✅ DILifecycleManager 종료 완료")

        except Exception as e:
            logger.error(f"❌ DILifecycleManager 종료 중 오류: {e}")

    def _wire_presentation_modules(self) -> None:
        """
        Presentation Container Wiring 설정

        UI Layer 모듈들의 @inject 데코레이터 활성화
        """
        if not self._presentation_container:
            raise RuntimeError("PresentationContainer가 초기화되지 않았습니다")

        try:
            # Presentation Layer 모듈들 Wiring - 실제 존재하는 모듈만
            presentation_modules = [
                'upbit_auto_trading.presentation.presenters',
                'upbit_auto_trading.ui.desktop.common.widgets',
                # 'upbit_auto_trading.ui.desktop.views' 모듈은 존재하지 않으므로 제외
            ]

            self._presentation_container.wire(modules=presentation_modules)
            logger.info("✅ Presentation Container Wiring 설정 완료")

        except Exception as e:
            logger.warning(f"⚠️ Presentation Container Wiring 설정 중 오류: {e}")

    def _cleanup(self) -> None:
        """내부 리소스 정리 (3-Container 시스템)"""
        try:
            # Presentation Container 정리
            if self._presentation_container:
                self._presentation_container.unwire()
                self._presentation_container = None
                logger.debug("🧹 PresentationContainer 정리 완료")

            # Application Service Container 정리
            if self._application_container:
                self._application_container.clear_cache()
                self._application_container = None
                logger.debug("🧹 ApplicationServiceContainer 정리 완료")

            # External Dependency Container 정리 (dependency-injector가 자동 처리)
            self._external_container = None
            self._is_initialized = False
            logger.debug("🧹 3-Container DI 시스템 리소스 정리 완료")

        except Exception as e:
            logger.warning(f"⚠️ 리소스 정리 중 오류: {e}")

    def get_service(self, service_name: str):
        """
        서비스 조회 (편의 메서드)

        Args:
            service_name: Provider 이름 (예: "logging_service")

        Returns:
            Provider에서 생성된 서비스 인스턴스
        """
        if not self._is_initialized or not self._external_container:
            raise RuntimeError("DILifecycleManager가 초기화되지 않았습니다")

        try:
            provider = getattr(self._external_container, service_name)
            return provider()
        except AttributeError:
            raise ValueError(f"서비스를 찾을 수 없습니다: {service_name}")
        except Exception as e:
            logger.error(f"❌ 서비스 조회 실패 ({service_name}): {e}")
            raise

    def get_main_window_presenter(self):
        """
        MainWindow Presenter 조회 (run_desktop_ui.py에서 사용)

        Returns:
            MainWindowPresenter: MVP 패턴의 MainWindow Presenter 인스턴스

        Raises:
            RuntimeError: 3-Container 시스템이 초기화되지 않은 경우
        """
        if not self._is_initialized or not self._presentation_container:
            raise RuntimeError("3-Container DI 시스템이 초기화되지 않았습니다")

        try:
            return self._presentation_container.main_window_presenter()
        except Exception as e:
            logger.error(f"❌ MainWindow Presenter 조회 실패: {e}")
            raise RuntimeError(f"MainWindow Presenter 조회 실패: {e}") from e

    def resolve(self, service_type):
        """
        MainWindow 호환성을 위한 resolve 메서드

        Args:
            service_type: 서비스 타입 (클래스 또는 인터페이스)

        Returns:
            Provider에서 생성된 서비스 인스턴스
        """
        if not self._is_initialized or not self._external_container:
            raise RuntimeError("DILifecycleManager가 초기화되지 않았습니다")

        logger.warning(f"⚠️ Legacy resolve() 호출 감지: {service_type}. @inject 패턴으로 마이그레이션을 권장합니다.")

        service_name = str(service_type)
        if "ISettingsService" in service_name:
            try:
                return self._external_container.settings_service()
            except Exception as e:
                logger.warning(f"⚠️ SettingsService Provider 미구현: {e}")
                return None
        elif "IThemeService" in service_name:
            try:
                return self._external_container.theme_service()
            except Exception as e:
                logger.warning(f"⚠️ ThemeService Provider 미구현: {e}")
                return None
        elif "ApiKeyService" in service_name:
            try:
                return self._external_container.api_key_service()
            except Exception as e:
                logger.warning(f"⚠️ ApiKeyService Provider 미구현: {e}")
                return None
        elif "StyleManager" in service_name:
            try:
                return self._external_container.style_manager()
            except Exception as e:
                logger.warning(f"⚠️ StyleManager Provider 미구현: {e}")
                return None
        elif "NavigationBar" in service_name:
            try:
                # NavigationBar는 Application Container를 통해 접근
                if self._application_container:
                    from upbit_auto_trading.ui.desktop.common.widgets.navigation_bar import NavigationBar
                    return NavigationBar()
                return None
            except Exception as e:
                logger.warning(f"⚠️ NavigationBar Provider 미구현: {e}")
                return None
        elif "StatusBar" in service_name:
            try:
                # StatusBar는 Application Container를 통해 접근
                if self._application_container:
                    from upbit_auto_trading.ui.desktop.common.widgets.status_bar import StatusBar
                    from upbit_auto_trading.application.services.database_health_service import DatabaseHealthService
                    return StatusBar(DatabaseHealthService())
                return None
            except Exception as e:
                logger.warning(f"⚠️ StatusBar Provider 미구현: {e}")
                return None
        else:
            logger.warning(f"⚠️ 지원되지 않는 서비스 타입: {service_type}")
            return None

    def is_registered(self, service_type) -> bool:
        """
        MainWindow 호환성을 위한 is_registered 메서드

        Args:
            service_type: 서비스 타입 (클래스 또는 인터페이스)

        Returns:
            bool: 서비스가 등록되어 있는지 여부
        """
        if not self._is_initialized or not self._external_container:
            return False

        service_name = str(service_type)

        # External Dependency Container에서 제공하는 서비스들
        if "ISettingsService" in service_name:
            return hasattr(self._external_container, 'settings_service')
        elif "IThemeService" in service_name:
            return hasattr(self._external_container, 'theme_service')
        elif "ApiKeyService" in service_name:
            return hasattr(self._external_container, 'api_key_service')
        elif "StyleManager" in service_name:
            return hasattr(self._external_container, 'style_manager')
        elif "NavigationBar" in service_name or "StatusBar" in service_name:
            # UI 컴포넌트는 Application Container가 있으면 등록된 것으로 간주
            return self._application_container is not None
        else:
            logger.debug(f"🔍 미등록 서비스 타입 확인: {service_type}")
            return False

    def __enter__(self) -> 'DILifecycleManager':
        """컨텍스트 매니저 진입"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """컨텍스트 매니저 종료"""
        self.shutdown()

    def __repr__(self) -> str:
        """문자열 표현"""
        status = "initialized" if self._is_initialized else "not initialized"
        external_info = "with external_container" if self._external_container else "no external_container"
        app_info = "with app_container" if self._application_container else "no app_container"
        return f"DILifecycleManager({status}, {external_info}, {app_info})"


# =============================================================================
# 전역 DILifecycleManager 관리
# =============================================================================

_global_di_manager: Optional[DILifecycleManager] = None


def get_di_lifecycle_manager() -> DILifecycleManager:
    """
    전역 DILifecycleManager 조회

    싱글톤 패턴으로 전역 DI 생명주기 관리자 관리
    모든 DI Container들의 생명주기를 중앙에서 제어합니다.

    Returns:
        DILifecycleManager: 전역 DI 생명주기 관리자
    """
    global _global_di_manager
    if _global_di_manager is None:
        _global_di_manager = DILifecycleManager()
        _global_di_manager.initialize()
        logger.info("🌍 전역 DILifecycleManager 초기화 완료")
    return _global_di_manager


def set_di_lifecycle_manager(manager: DILifecycleManager) -> None:
    """
    전역 DILifecycleManager 설정

    Args:
        manager: 설정할 DILifecycleManager
    """
    global _global_di_manager
    if _global_di_manager and _global_di_manager.is_initialized:
        _global_di_manager.shutdown()
    _global_di_manager = manager
    logger.info("🌍 전역 DILifecycleManager 변경 완료")


def reset_di_lifecycle_manager() -> None:
    """
    전역 DILifecycleManager 초기화
    """
    global _global_di_manager
    if _global_di_manager and _global_di_manager.is_initialized:
        _global_di_manager.shutdown()
    _global_di_manager = None
    logger.info("🌍 전역 DILifecycleManager 초기화 완료")


def is_di_lifecycle_manager_initialized() -> bool:
    """
    전역 DILifecycleManager 초기화 상태 확인

    Returns:
        bool: 초기화 여부
    """
    global _global_di_manager
    return _global_di_manager is not None and _global_di_manager.is_initialized


# =============================================================================
# Legacy 호환성 (기존 ApplicationContext 호출 지원)
# =============================================================================

def get_application_context() -> DILifecycleManager:
    """
    Legacy 호환성을 위한 get_application_context() 별칭

    Warning: 이 함수는 하위 호환성을 위해 제공되며,
             새 코드에서는 get_di_lifecycle_manager()를 사용하세요.

    Returns:
        DILifecycleManager: DI 생명주기 관리자 인스턴스
    """
    logger.warning("⚠️ Legacy get_application_context() 호출 감지. get_di_lifecycle_manager() 사용을 권장합니다.")
    return get_di_lifecycle_manager()


def set_application_context(manager: DILifecycleManager) -> None:
    """Legacy 호환성을 위한 별칭"""
    logger.warning("⚠️ Legacy set_application_context() 호출 감지. set_di_lifecycle_manager() 사용을 권장합니다.")
    set_di_lifecycle_manager(manager)


def reset_application_context() -> None:
    """Legacy 호환성을 위한 별칭"""
    logger.warning("⚠️ Legacy reset_application_context() 호출 감지. reset_di_lifecycle_manager() 사용을 권장합니다.")
    reset_di_lifecycle_manager()


def is_application_context_initialized() -> bool:
    """Legacy 호환성을 위한 별칭"""
    return is_di_lifecycle_manager_initialized()


# Legacy alias
ApplicationContext = DILifecycleManager
ApplicationContextError = DILifecycleManagerError
