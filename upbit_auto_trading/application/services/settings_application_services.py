"""
Settings 전용 Application Layer 서비스들
완전한 DDD + MVP + DI 아키텍처 구현을 위한 서비스 계층
"""

from typing import Any, Dict, Optional, Protocol
from dataclasses import dataclass
from enum import Enum

from upbit_auto_trading.application.services.logging_application_service import (
    ApplicationLoggingService,
    IPresentationLogger
)


class ComponentLifecycleState(Enum):
    """컴포넌트 생명주기 상태"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    ERROR = "error"
    DISPOSED = "disposed"


@dataclass
class ComponentInfo:
    """컴포넌트 정보"""
    name: str
    component_type: str
    state: ComponentLifecycleState
    instance: Optional[Any] = None
    error_message: Optional[str] = None
    initialization_time: Optional[float] = None


class IComponentLifecycleService(Protocol):
    """컴포넌트 생명주기 관리 서비스 인터페이스"""

    def register_component(self, name: str, component_type: str, instance: Any) -> None:
        """컴포넌트 등록"""
        ...

    def get_component_state(self, name: str) -> ComponentLifecycleState:
        """컴포넌트 상태 조회"""
        ...

    def mark_error(self, name: str, error_message: str) -> None:
        """컴포넌트 에러 상태 마킹"""
        ...


class ComponentLifecycleService:
    """
    컴포넌트 생명주기 관리 서비스

    Settings Screen의 모든 하위 컴포넌트들의 초기화, 상태 추적, 에러 처리를 담당
    """

    def __init__(self, logging_service: ApplicationLoggingService):
        self._logging_service = logging_service
        self._logger = logging_service.get_component_logger("ComponentLifecycleService")
        self._components: Dict[str, ComponentInfo] = {}

        self._logger.info("ComponentLifecycleService 초기화 완료")

    def register_component(self, name: str, component_type: str, instance: Any) -> None:
        """컴포넌트 등록 및 상태 추적 시작"""
        import time

        self._components[name] = ComponentInfo(
            name=name,
            component_type=component_type,
            state=ComponentLifecycleState.INITIALIZING,
            instance=instance,
            initialization_time=time.time()
        )

        self._logger.info(f"📋 컴포넌트 등록: {name} ({component_type})")

        # 초기화 완료 후 상태 업데이트
        try:
            if hasattr(instance, '__post_init__'):
                instance.__post_init__()

            self._components[name].state = ComponentLifecycleState.INITIALIZED
            self._logger.debug(f"✅ 컴포넌트 초기화 성공: {name}")

        except Exception as e:
            self.mark_error(name, str(e))
            raise

    def get_component_state(self, name: str) -> ComponentLifecycleState:
        """컴포넌트 상태 조회"""
        if name not in self._components:
            return ComponentLifecycleState.NOT_INITIALIZED
        return self._components[name].state

    def mark_error(self, name: str, error_message: str) -> None:
        """컴포넌트 에러 상태 마킹"""
        if name in self._components:
            self._components[name].state = ComponentLifecycleState.ERROR
            self._components[name].error_message = error_message
            self._logger.error(f"❌ 컴포넌트 에러: {name} - {error_message}")
        else:
            self._logger.warning(f"⚠️ 미등록 컴포넌트 에러 보고: {name} - {error_message}")

    def get_component_instance(self, name: str) -> Optional[Any]:
        """컴포넌트 인스턴스 조회"""
        if name in self._components and self._components[name].state == ComponentLifecycleState.INITIALIZED:
            return self._components[name].instance
        return None

    def list_components(self) -> Dict[str, ComponentInfo]:
        """전체 컴포넌트 목록 반환"""
        return self._components.copy()

    def get_statistics(self) -> Dict[str, int]:
        """컴포넌트 상태별 통계"""
        stats = {}
        for state in ComponentLifecycleState:
            stats[state.value] = sum(1 for comp in self._components.values() if comp.state == state)
        return stats


class ISettingsValidationService(Protocol):
    """Settings 유효성 검증 서비스 인터페이스"""

    def validate_component_config(self, component_type: str, config: Dict[str, Any]) -> bool:
        """컴포넌트 설정 유효성 검증"""
        ...

    def get_validation_errors(self) -> list[str]:
        """검증 오류 목록 반환"""
        ...


class SettingsValidationService:
    """
    Settings 유효성 검증 서비스

    Settings Screen 컴포넌트들의 설정 데이터 검증을 담당
    """

    def __init__(self, logging_service: ApplicationLoggingService):
        self._logging_service = logging_service
        self._logger = logging_service.get_component_logger("SettingsValidationService")
        self._validation_errors: list[str] = []

        self._logger.info("SettingsValidationService 초기화 완료")

    def validate_component_config(self, component_type: str, config: Dict[str, Any]) -> bool:
        """컴포넌트 설정 유효성 검증"""
        self._validation_errors.clear()

        try:
            if component_type == "api_settings":
                return self._validate_api_settings(config)
            elif component_type == "database_settings":
                return self._validate_database_settings(config)
            elif component_type == "ui_settings":
                return self._validate_ui_settings(config)
            elif component_type == "logging_settings":
                return self._validate_logging_settings(config)
            elif component_type == "notification_settings":
                return self._validate_notification_settings(config)
            else:
                self._validation_errors.append(f"알 수 없는 컴포넌트 타입: {component_type}")
                return False

        except Exception as e:
            self._validation_errors.append(f"검증 중 오류: {str(e)}")
            self._logger.error(f"검증 오류: {component_type} - {e}")
            return False

    def _validate_api_settings(self, config: Dict[str, Any]) -> bool:
        """API 설정 검증"""
        required_keys = ["api_key_service", "logging_service"]
        for key in required_keys:
            if key not in config:
                self._validation_errors.append(f"API 설정에 필수 키 누락: {key}")

        return len(self._validation_errors) == 0

    def _validate_database_settings(self, config: Dict[str, Any]) -> bool:
        """데이터베이스 설정 검증"""
        required_keys = ["logging_service"]
        for key in required_keys:
            if key not in config:
                self._validation_errors.append(f"데이터베이스 설정에 필수 키 누락: {key}")

        return len(self._validation_errors) == 0

    def _validate_ui_settings(self, config: Dict[str, Any]) -> bool:
        """UI 설정 검증"""
        required_keys = ["logging_service"]
        for key in required_keys:
            if key not in config:
                self._validation_errors.append(f"UI 설정에 필수 키 누락: {key}")

        return len(self._validation_errors) == 0

    def _validate_logging_settings(self, config: Dict[str, Any]) -> bool:
        """로깅 설정 검증"""
        required_keys = ["logging_service"]
        for key in required_keys:
            if key not in config:
                self._validation_errors.append(f"로깅 설정에 필수 키 누락: {key}")

        return len(self._validation_errors) == 0

    def _validate_notification_settings(self, config: Dict[str, Any]) -> bool:
        """알림 설정 검증"""
        required_keys = ["logging_service"]
        for key in required_keys:
            if key not in config:
                self._validation_errors.append(f"알림 설정에 필수 키 누락: {key}")

        return len(self._validation_errors) == 0

    def get_validation_errors(self) -> list[str]:
        """검증 오류 목록 반환"""
        return self._validation_errors.copy()


class SettingsApplicationService:
    """
    Settings 통합 Application Service

    Settings Screen 관련 모든 비즈니스 로직을 통합 관리
    """

    def __init__(self,
                 logging_service: ApplicationLoggingService,
                 component_lifecycle_service: ComponentLifecycleService,
                 validation_service: SettingsValidationService):
        self._logging_service = logging_service
        self._lifecycle_service = component_lifecycle_service
        self._validation_service = validation_service
        self._logger = logging_service.get_component_logger("SettingsApplicationService")

        self._logger.info("SettingsApplicationService 초기화 완료")

    def create_validated_component(self, name: str, component_type: str,
                                   config: Dict[str, Any], factory_func) -> Any:
        """검증된 컴포넌트 생성"""

        # 1. 설정 검증
        if not self._validation_service.validate_component_config(component_type, config):
            errors = self._validation_service.get_validation_errors()
            error_msg = f"컴포넌트 설정 검증 실패: {', '.join(errors)}"
            self._logger.error(f"❌ {name} 생성 실패 - {error_msg}")
            raise ValueError(error_msg)

        # 2. 컴포넌트 생성
        try:
            instance = factory_func(**config)

            # 3. 생명주기 등록
            self._lifecycle_service.register_component(name, component_type, instance)

            self._logger.info(f"✅ 검증된 컴포넌트 생성 성공: {name}")
            return instance

        except Exception as e:
            self._lifecycle_service.mark_error(name, str(e))
            self._logger.error(f"❌ 컴포넌트 생성 실패: {name} - {e}")
            raise

    def get_service_statistics(self) -> Dict[str, Any]:
        """서비스 통계 정보"""
        return {
            "component_stats": self._lifecycle_service.get_statistics(),
            "logged_components": self._logging_service.list_component_names(),
            "total_components": len(self._lifecycle_service.list_components())
        }


# =============================================================================
# Factory 함수들 - DI 컨테이너에서 사용
# =============================================================================

def create_component_lifecycle_service(logging_service: ApplicationLoggingService) -> ComponentLifecycleService:
    """ComponentLifecycleService 팩토리 함수"""
    return ComponentLifecycleService(logging_service)


def create_settings_validation_service(logging_service: ApplicationLoggingService) -> SettingsValidationService:
    """SettingsValidationService 팩토리 함수"""
    return SettingsValidationService(logging_service)


def create_settings_application_service(
    logging_service: ApplicationLoggingService,
    component_lifecycle_service: ComponentLifecycleService,
    validation_service: SettingsValidationService
) -> SettingsApplicationService:
    """SettingsApplicationService 팩토리 함수"""
    return SettingsApplicationService(
        logging_service=logging_service,
        component_lifecycle_service=component_lifecycle_service,
        validation_service=validation_service
    )
