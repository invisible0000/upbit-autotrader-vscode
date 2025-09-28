"""
애플리케이션 컨텍스트 - Container 관리 전담
Clean Architecture + dependency-injector 기반 단순화된 컨텍스트
"""

from typing import Optional
from dependency_injector.wiring import inject, Provide

from upbit_auto_trading.infrastructure.dependency_injection.container import (
    ApplicationContainer,
    create_application_container,
    wire_container_modules,
    validate_container_registration
)
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("AppContext")


class ApplicationContextError(Exception):
    """애플리케이션 컨텍스트 관련 오류"""
    pass


class ApplicationContext:
    """
    애플리케이션 컨텍스트 - Container 관리 전담

    기존의 복잡한 초기화 로직을 제거하고 DI Container 관리에만 집중

    주요 책임:
    - ApplicationContainer 생명주기 관리
    - Wiring 설정 및 검증
    - Container 상태 모니터링
    """

    def __init__(self, container: Optional[ApplicationContainer] = None):
        """
        Args:
            container: 사용할 ApplicationContainer (None이면 새로 생성)
        """
        self._container: Optional[ApplicationContainer] = container
        self._is_initialized = False
        logger.debug("ApplicationContext 생성 - Container 관리 전담 모드")

    def initialize(self) -> None:
        """
        애플리케이션 컨텍스트 초기화

        단순화된 초기화:
        1. Container 생성 또는 검증
        2. Wiring 설정
        3. 등록 상태 검증
        """
        if self._is_initialized:
            logger.debug("ApplicationContext가 이미 초기화되었습니다")
            return

        try:
            # 1. Container 준비
            if self._container is None:
                self._container = create_application_container()
                logger.info("🏗️ 새 ApplicationContainer 생성 완료")
            else:
                logger.info("🏗️ 기존 ApplicationContainer 사용")

            # 2. Wiring 설정
            wire_container_modules(self._container)

            # 3. 등록 상태 검증
            if validate_container_registration(self._container):
                self._is_initialized = True
                logger.info("✅ ApplicationContext 초기화 완료")
            else:
                raise RuntimeError("Container 등록 검증 실패")

        except Exception as e:
            logger.error(f"❌ ApplicationContext 초기화 실패: {e}")
            self._cleanup()
            raise RuntimeError(f"ApplicationContext 초기화 실패: {e}") from e

    def container(self) -> ApplicationContainer:
        """
        ApplicationContainer 조회

        Returns:
            ApplicationContainer: 현재 관리 중인 컨테이너

        Raises:
            RuntimeError: 초기화되지 않은 경우
        """
        if not self._is_initialized or not self._container:
            raise RuntimeError("ApplicationContext가 초기화되지 않았습니다")
        return self._container

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
        if not self._is_initialized or not self._container:
            logger.warning("초기화되지 않은 상태에서 설정 리로드를 시도합니다")
            return

        try:
            logger.info(f"📄 설정 파일 다시 로드: {config_path}")
            self._container.config.from_yaml(config_path)
            logger.info("✅ 설정 리로드 완료")

        except Exception as e:
            logger.error(f"❌ 설정 리로드 실패: {e}")
            # 폴백 설정으로 복구
            self._container.config.from_dict({
                "app_name": "Upbit Auto Trading",
                "app_version": "1.0.0"
            })
            logger.info("🔄 기본 설정으로 폴백 완료")

    def shutdown(self) -> None:
        """
        애플리케이션 컨텍스트 종료

        Container와 관련 리소스를 정리합니다.
        """
        logger.info("🚀 ApplicationContext 종료 시작")

        try:
            self._cleanup()
            logger.info("✅ ApplicationContext 종료 완료")

        except Exception as e:
            logger.error(f"❌ ApplicationContext 종료 중 오류: {e}")

    def _cleanup(self) -> None:
        """내부 리소스 정리"""
        try:
            # Container 정리는 dependency-injector가 자동으로 처리
            self._container = None
            self._is_initialized = False
            logger.debug("🧹 내부 리소스 정리 완료")

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
        if not self._is_initialized or not self._container:
            raise RuntimeError("ApplicationContext가 초기화되지 않았습니다")

        try:
            provider = getattr(self._container, service_name)
            return provider()
        except AttributeError:
            raise ValueError(f"서비스를 찾을 수 없습니다: {service_name}")
        except Exception as e:
            logger.error(f"❌ 서비스 조회 실패 ({service_name}): {e}")
            raise

    def resolve(self, service_type):
        """
        MainWindow 호환성을 위한 resolve 메서드

        Args:
            service_type: 서비스 타입 (클래스 또는 인터페이스)

        Returns:
            Provider에서 생성된 서비스 인스턴스
        """
        if not self._is_initialized or not self._container:
            raise RuntimeError("ApplicationContext가 초기화되지 않았습니다")

        logger.warning(f"⚠️ Legacy resolve() 호출 감지: {service_type}. @inject 패턴으로 마이그레이션을 권장합니다.")

        service_name = str(service_type)
        if "ISettingsService" in service_name:
            try:
                return self._container.settings_service()
            except Exception as e:
                logger.warning(f"⚠️ SettingsService Provider 미구현: {e}")
                return None
        elif "IThemeService" in service_name:
            try:
                return self._container.theme_service()
            except Exception as e:
                logger.warning(f"⚠️ ThemeService Provider 미구현: {e}")
                return None
        elif "ApiKeyService" in service_name:
            try:
                return self._container.api_key_service()
            except Exception as e:
                logger.warning(f"⚠️ ApiKeyService Provider 미구현: {e}")
                return None
        elif "StyleManager" in service_name:
            try:
                return self._container.style_manager()
            except Exception as e:
                logger.warning(f"⚠️ StyleManager Provider 미구현: {e}")
                return None
        elif "NavigationBar" in service_name:
            try:
                return self._container.navigation_service()
            except Exception as e:
                logger.warning(f"⚠️ NavigationBar Provider 미구현: {e}")
                return None
        elif "StatusBar" in service_name:
            try:
                return self._container.status_bar_service()
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
        if not self._is_initialized or not self._container:
            return False

        service_name = str(service_type)

        # 현재 구현된 Provider들 확인
        if "ISettingsService" in service_name:
            return hasattr(self._container, 'settings_service')
        elif "IThemeService" in service_name:
            return hasattr(self._container, 'theme_service')
        elif "ApiKeyService" in service_name:
            return hasattr(self._container, 'api_key_service')
        elif "StyleManager" in service_name:
            return hasattr(self._container, 'style_manager')
        elif "NavigationBar" in service_name:
            return hasattr(self._container, 'navigation_service')
        elif "StatusBar" in service_name:
            return hasattr(self._container, 'status_bar_service')
        else:
            logger.debug(f"🔍 미등록 서비스 타입 확인: {service_type}")
            return False

    def __enter__(self) -> 'ApplicationContext':
        """컨텍스트 매니저 진입"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """컨텍스트 매니저 종료"""
        self.shutdown()

    def __repr__(self) -> str:
        """문자열 표현"""
        status = "initialized" if self._is_initialized else "not initialized"
        container_info = "with container" if self._container else "no container"
        return f"ApplicationContext({status}, {container_info})"


# =============================================================================
# 전역 ApplicationContext 관리 (선택적 사용)
# =============================================================================

_global_app_context: Optional[ApplicationContext] = None


def get_application_context() -> ApplicationContext:
    """
    전역 ApplicationContext 조회

    싱글톤 패턴으로 전역 컨텍스트 관리

    Returns:
        ApplicationContext: 전역 애플리케이션 컨텍스트
    """
    global _global_app_context
    if _global_app_context is None:
        _global_app_context = ApplicationContext()
        _global_app_context.initialize()
        logger.info("🌍 전역 ApplicationContext 초기화 완료")
    return _global_app_context


def set_application_context(context: ApplicationContext) -> None:
    """
    전역 ApplicationContext 설정

    Args:
        context: 설정할 ApplicationContext
    """
    global _global_app_context
    if _global_app_context and _global_app_context.is_initialized:
        _global_app_context.shutdown()
    _global_app_context = context
    logger.info("🌍 전역 ApplicationContext 변경 완료")


def reset_application_context() -> None:
    """
    전역 ApplicationContext 초기화
    """
    global _global_app_context
    if _global_app_context and _global_app_context.is_initialized:
        _global_app_context.shutdown()
    _global_app_context = None
    logger.info("🌍 전역 ApplicationContext 초기화 완료")


def is_application_context_initialized() -> bool:
    """
    전역 ApplicationContext 초기화 상태 확인

    Returns:
        bool: 초기화 여부
    """
    global _global_app_context
    return _global_app_context is not None and _global_app_context.is_initialized
