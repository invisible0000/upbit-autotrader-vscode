"""
Settings View Factory 패턴 구현
컴포넌트 생성 책임을 View에서 분리하여 확장성과 테스트 용이성 확보
"""

from typing import Any, Dict, Optional, Protocol
from abc import ABC, abstractmethod

from PyQt6.QtWidgets import QWidget

from upbit_auto_trading.application.services.logging_application_service import ApplicationLoggingService
from upbit_auto_trading.application.services.settings_application_services import (
    ComponentLifecycleService,
    SettingsValidationService,
    SettingsApplicationService
)


class ISettingsComponentFactory(Protocol):
    """Settings 컴포넌트 생성을 담당하는 Factory 인터페이스"""

    def create_api_settings_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """API 설정 컴포넌트 생성"""
        ...

    def create_database_settings_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """데이터베이스 설정 컴포넌트 생성"""
        ...

    def create_ui_settings_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """UI 설정 컴포넌트 생성"""
        ...

    def create_logging_management_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """로깅 관리 컴포넌트 생성"""
        ...

    def create_notification_settings_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """알림 설정 컴포넌트 생성"""
        ...

    def create_environment_profile_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """환경 프로필 컴포넌트 생성"""
        ...


class BaseComponentFactory(ABC):
    """컴포넌트 Factory 기본 클래스"""

    def __init__(self,
                 logging_service: ApplicationLoggingService,
                 lifecycle_service: ComponentLifecycleService,
                 validation_service: SettingsValidationService):
        self._logging_service = logging_service
        self._lifecycle_service = lifecycle_service
        self._validation_service = validation_service
        self._logger = logging_service.get_component_logger(f"{self.__class__.__name__}")

    @abstractmethod
    def get_component_type(self) -> str:
        """컴포넌트 타입 반환"""
        pass

    @abstractmethod
    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        """컴포넌트 인스턴스 생성 (하위 클래스에서 구현)"""
        pass

    def create_component(self, parent: Optional[QWidget] = None, **kwargs) -> QWidget:
        """검증과 생명주기 관리가 포함된 컴포넌트 생성"""
        component_type = self.get_component_type()
        component_name = f"{component_type}_component"

        try:
            # 1. 설정 검증
            config = {
                "logging_service": self._logging_service,
                "parent": parent,
                **kwargs
            }

            if not self._validation_service.validate_component_config(component_type, config):
                errors = self._validation_service.get_validation_errors()
                raise ValueError(f"컴포넌트 설정 검증 실패: {', '.join(errors)}")

            # 2. 컴포넌트 생성
            instance = self.create_component_instance(parent, **kwargs)

            # 3. 생명주기 등록
            self._lifecycle_service.register_component(component_name, component_type, instance)

            self._logger.info(f"✅ 컴포넌트 생성 성공: {component_name}")
            return instance

        except Exception as e:
            self._lifecycle_service.mark_error(component_name, str(e))
            self._logger.error(f"❌ 컴포넌트 생성 실패: {component_name} - {e}")
            raise


class ApiSettingsComponentFactory(BaseComponentFactory):
    """API 설정 컴포넌트 전용 Factory"""

    def __init__(self,
                 logging_service: ApplicationLoggingService,
                 lifecycle_service: ComponentLifecycleService,
                 validation_service: SettingsValidationService,
                 api_key_service: Any = None):
        super().__init__(logging_service, lifecycle_service, validation_service)
        self._api_key_service = api_key_service

    def get_component_type(self) -> str:
        return "api_settings"

    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        """API 설정 컴포넌트 생성"""
        from upbit_auto_trading.ui.desktop.screens.settings.api_settings.views.api_settings_view import ApiSettingsView

        component_logger = self._logging_service.get_component_logger("ApiSettingsView")

        return ApiSettingsView(
            parent=parent,
            logging_service=component_logger,
            api_key_service=self._api_key_service
        )


class DatabaseSettingsComponentFactory(BaseComponentFactory):
    """데이터베이스 설정 컴포넌트 전용 Factory"""

    def get_component_type(self) -> str:
        return "database_settings"

    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        """데이터베이스 설정 컴포넌트 생성"""
        from upbit_auto_trading.ui.desktop.screens.settings.database_settings.views.database_settings_view import DatabaseSettingsView

        component_logger = self._logging_service.get_component_logger("DatabaseSettingsView")

        return DatabaseSettingsView(
            parent=parent,
            logging_service=component_logger
        )


class UiSettingsComponentFactory(BaseComponentFactory):
    """UI 설정 컴포넌트 전용 Factory"""

    def get_component_type(self) -> str:
        return "ui_settings"

    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        """UI 설정 컴포넌트 생성"""
        from upbit_auto_trading.ui.desktop.screens.settings.ui_settings.views.ui_settings_view import UISettingsView

        return UISettingsView(
            parent=parent,
            logging_service=self._logging_service
        )


class LoggingSettingsComponentFactory(BaseComponentFactory):
    """로깅 설정 컴포넌트 전용 Factory"""

    def get_component_type(self) -> str:
        return "logging_settings"

    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        """로깅 설정 컴포넌트 생성"""
        from upbit_auto_trading.ui.desktop.screens.settings.logging_management.logging_management_view import LoggingManagementView

        component_logger = self._logging_service.get_component_logger("LoggingManagementView")

        return LoggingManagementView(
            parent=parent,
            logging_service=component_logger
        )


class NotificationSettingsComponentFactory(BaseComponentFactory):
    """알림 설정 컴포넌트 전용 Factory"""

    def get_component_type(self) -> str:
        return "notification_settings"

    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        """알림 설정 컴포넌트 생성"""
        from upbit_auto_trading.ui.desktop.screens.settings.notification_settings.views.notification_settings_view import NotificationSettingsView

        component_logger = self._logging_service.get_component_logger("NotificationSettingsView")

        return NotificationSettingsView(
            parent=parent,
            logging_service=component_logger
        )


class EnvironmentProfileComponentFactory(BaseComponentFactory):
    """환경 프로필 컴포넌트 전용 Factory"""

    def get_component_type(self) -> str:
        return "environment_profile"

    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        """환경 프로필 컴포넌트 생성"""
        from upbit_auto_trading.ui.desktop.screens.settings.environment_profile.environment_profile_view import EnvironmentProfileView

        component_logger = self._logging_service.get_component_logger("EnvironmentProfileView")

        return EnvironmentProfileView(
            parent=parent,
            logging_service=component_logger
        )


class SettingsViewFactory:
    """
    Settings View와 관련된 모든 컴포넌트를 생성하는 메인 Factory

    Factory 패턴을 통해 View의 컴포넌트 생성 책임을 완전히 분리
    """

    def __init__(self,
                 settings_app_service: SettingsApplicationService,
                 logging_service: ApplicationLoggingService,
                 lifecycle_service: ComponentLifecycleService,
                 validation_service: SettingsValidationService,
                 api_key_service: Any = None):
        self._settings_app_service = settings_app_service
        self._logging_service = logging_service
        self._lifecycle_service = lifecycle_service
        self._validation_service = validation_service
        self._api_key_service = api_key_service

        self._logger = logging_service.get_component_logger("SettingsViewFactory")

        # 하위 Factory들 초기화
        self._api_factory = ApiSettingsComponentFactory(
            logging_service, lifecycle_service, validation_service, api_key_service
        )
        self._database_factory = DatabaseSettingsComponentFactory(
            logging_service, lifecycle_service, validation_service
        )
        self._ui_factory = UiSettingsComponentFactory(
            logging_service, lifecycle_service, validation_service
        )
        self._logging_factory = LoggingSettingsComponentFactory(
            logging_service, lifecycle_service, validation_service
        )
        self._notification_factory = NotificationSettingsComponentFactory(
            logging_service, lifecycle_service, validation_service
        )
        self._environment_factory = EnvironmentProfileComponentFactory(
            logging_service, lifecycle_service, validation_service
        )

        self._component_cache: Dict[str, QWidget] = {}
        self._logger.info("SettingsViewFactory 초기화 완료")

    def create_api_settings_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """API 설정 컴포넌트 생성 (캐싱 지원)"""
        return self._get_or_create_component("api_settings", self._api_factory, parent)

    def create_database_settings_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """데이터베이스 설정 컴포넌트 생성 (캐싱 지원)"""
        return self._get_or_create_component("database_settings", self._database_factory, parent)

    def create_ui_settings_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """UI 설정 컴포넌트 생성 (캐싱 지원)"""
        return self._get_or_create_component("ui_settings", self._ui_factory, parent)

    def create_logging_management_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """로깅 관리 컴포넌트 생성 (캐싱 지원)"""
        return self._get_or_create_component("logging_management", self._logging_factory, parent)

    def create_notification_settings_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """알림 설정 컴포넌트 생성 (캐싱 지원)"""
        return self._get_or_create_component("notification_settings", self._notification_factory, parent)

    def create_environment_profile_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """환경 프로필 컴포넌트 생성 (캐싱 지원)"""
        return self._get_or_create_component("environment_profile", self._environment_factory, parent)

    def create_component_by_name(self, component_name: str, parent: Optional[QWidget] = None) -> QWidget:
        """컴포넌트 이름으로 동적 생성"""
        factory_map = {
            "API 설정": self._api_factory,
            "데이터베이스 설정": self._database_factory,
            "UI 설정": self._ui_factory,
            "로깅 관리": self._logging_factory,
            "알림 설정": self._notification_factory,
            "환경 프로필": self._environment_factory,
        }

        if component_name not in factory_map:
            raise ValueError(f"알 수 없는 컴포넌트: {component_name}")

        factory = factory_map[component_name]
        cache_key = component_name.replace(" ", "_").lower()

        return self._get_or_create_component(cache_key, factory, parent)

    def _get_or_create_component(self, cache_key: str, factory: BaseComponentFactory,
                                 parent: Optional[QWidget]) -> QWidget:
        """캐싱을 지원하는 컴포넌트 생성"""
        if cache_key not in self._component_cache:
            self._logger.debug(f"🏭 새 컴포넌트 생성: {cache_key}")
            self._component_cache[cache_key] = factory.create_component(parent)
        else:
            self._logger.debug(f"📦 캐시된 컴포넌트 재사용: {cache_key}")

        return self._component_cache[cache_key]

    def clear_cache(self) -> None:
        """컴포넌트 캐시 정리"""
        cleared_count = len(self._component_cache)
        self._component_cache.clear()
        self._logger.info(f"🧹 컴포넌트 캐시 정리 완료: {cleared_count}개")

    def get_factory_statistics(self) -> Dict[str, Any]:
        """Factory 통계 정보"""
        return {
            "cached_components": list(self._component_cache.keys()),
            "component_count": len(self._component_cache),
            "lifecycle_stats": self._lifecycle_service.get_statistics(),
            "service_stats": self._settings_app_service.get_service_statistics()
        }


# =============================================================================
# Factory 함수 - DI 컨테이너에서 사용
# =============================================================================

def create_settings_view_factory(
    settings_app_service: SettingsApplicationService,
    logging_service: ApplicationLoggingService,
    lifecycle_service: ComponentLifecycleService,
    validation_service: SettingsValidationService,
    api_key_service: Any = None
) -> SettingsViewFactory:
    """SettingsViewFactory 팩토리 함수"""
    return SettingsViewFactory(
        settings_app_service=settings_app_service,
        logging_service=logging_service,
        lifecycle_service=lifecycle_service,
        validation_service=validation_service,
        api_key_service=api_key_service
    )
