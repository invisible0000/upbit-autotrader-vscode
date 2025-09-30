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

    def _ensure_application_context(self):
        """ApplicationContext 초기화 상태 확인"""
        from upbit_auto_trading.infrastructure.dependency_injection.app_context import get_application_context

        context = get_application_context()
        if not context or not hasattr(context, 'is_initialized') or not context.is_initialized:
            self._logger.warning("⚠️ ApplicationContext가 초기화되지 않았지만 계속 진행")
        return context

    def _get_application_container(self):
        """표준 ApplicationServiceContainer 접근 - 모든 Factory에서 일관된 패턴 사용"""
        # 1. ApplicationContext 상태 확인 (경고만, 실패하지 않음)
        try:
            self._ensure_application_context()
        except Exception as e:
            self._logger.warning(f"⚠️ ApplicationContext 확인 중 문제: {e}")

        # 2. ApplicationServiceContainer 가져오기 (필수)
        from upbit_auto_trading.application.container import get_application_container
        container = get_application_container()

        if container is None:
            error_msg = "❌ ApplicationServiceContainer가 None - DI 시스템 초기화 실패"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패 ({self.__class__.__name__}): {error_msg}")

        return container

    def _get_service(self, service_getter, service_name: str):
        """서비스 로드 - Golden Rules: 에러 숨김/폴백 금지 (Fail Fast)"""
        service = service_getter()
        if service is None:
            raise RuntimeError(f"{service_name} 서비스 로드 실패 - 시스템 중단 ({self.__class__.__name__})")
        return service

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

            # API 설정의 경우 api_key_service 추가
            if component_type == "api_settings" and hasattr(self, '_api_key_service'):
                config["api_key_service"] = self._api_key_service

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
        """API 설정 컴포넌트 생성 - 표준 Container 접근 패턴 사용"""
        # 1. 표준 Container 접근 (생성자 우선, 표준 메서드 사용)
        if self._api_key_service is not None:
            # 생성자에서 주입된 서비스 우선 사용 (가장 안정적)
            api_key_service = self._api_key_service
            app_logging_service = self._logging_service
            self._logger.info("✅ 생성자 주입 서비스 사용 (정상 경로)")
        else:
            # 표준 ApplicationServiceContainer 접근
            container = self._get_application_container()

            api_key_service = self._get_service(
                container.get_api_key_service, "ApiKey"
            )
            app_logging_service = self._get_service(
                container.get_logging_service, "Logging"
            )
            self._logger.info("✅ 표준 ApplicationContainer 서비스 사용 (정상 경로)")

        # 2. View 생성 (실패 시 즉시 에러)
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.api_settings.views.api_settings_view import ApiSettingsView
            component_logger = self._logging_service.get_component_logger("ApiSettingsView")

            view = ApiSettingsView(
                parent=parent,
                logging_service=component_logger,
                api_key_service=api_key_service
            )
        except Exception as e:
            error_msg = f"❌ ApiSettingsView 생성 실패: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패: {error_msg}")

        # 3. Presenter 생성 및 연결 (실패 시 즉시 에러)
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.api_settings.presenters.api_settings_presenter import ApiSettingsPresenter

            presenter_logger = app_logging_service.get_component_logger("ApiSettingsPresenter")
            presenter = ApiSettingsPresenter(
                view=view,
                api_key_service=api_key_service,
                logging_service=presenter_logger
            )

            # 4. MVP 패턴 연결 (실패 시 즉시 에러)
            view.set_presenter(presenter)
        except Exception as e:
            error_msg = f"❌ ApiSettingsPresenter 생성/연결 실패: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패: {error_msg}")

        # 5. 초기 데이터 로드 (실패해도 View는 반환, 하지만 에러 로그 남김)
        try:
            initial_settings = presenter.load_api_settings()
            view.credentials_widget.set_credentials(
                initial_settings['access_key'],
                initial_settings['secret_key']
            )
            view.permissions_widget.set_trade_permission(initial_settings['trade_permission'])
            view._update_button_states()

            self._logger.info("✅ API 설정 컴포넌트 완전 조립 완료 (MVP + 초기화)")
        except Exception as e:
            error_msg = f"❌ 초기 데이터 로드 실패: {e}"
            self._logger.error(error_msg)
            # 초기 데이터 실패는 치명적이지 않으므로 View는 반환하되 명확한 에러 로그

        return view


class DatabaseSettingsComponentFactory(BaseComponentFactory):
    """데이터베이스 설정 컴포넌트 전용 Factory"""

    def get_component_type(self) -> str:
        return "database_settings"

    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        """데이터베이스 설정 컴포넌트 생성 - 표준 Container 접근 패턴 사용"""
        # 1. 표준 ApplicationServiceContainer 접근
        container = self._get_application_container()

        # Database 설정에 필요한 서비스들 로드
        database_service = self._get_service(
            container.get_database_service, "Database"
        )
        app_logging_service = self._get_service(
            container.get_logging_service, "Logging"
        )
        self._logger.info("✅ 표준 ApplicationContainer 서비스 사용 (정상 경로)")

        # 2. View 생성 (실패 시 즉시 에러)
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.database_settings.views.database_settings_view import (
                DatabaseSettingsView
            )
            component_logger = self._logging_service.get_component_logger("DatabaseSettingsView")

            view = DatabaseSettingsView(
                parent=parent,
                logging_service=component_logger
            )
        except Exception as e:
            error_msg = f"❌ DatabaseSettingsView 생성 실패: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패: {error_msg}")

        # 3. Presenter 생성 및 연결 (실패 시 즉시 에러)
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.database_settings.presenters import (
                database_settings_presenter
            )
            DatabaseSettingsPresenter = database_settings_presenter.DatabaseSettingsPresenter

            presenter_logger = app_logging_service.get_component_logger("DatabaseSettingsPresenter")
            presenter = DatabaseSettingsPresenter(
                view=view,
                database_service=database_service,
                logging_service=presenter_logger
            )

            # 4. MVP 패턴 연결 (실패 시 즉시 에러)
            view.set_presenter(presenter)
        except Exception as e:
            error_msg = f"❌ DatabaseSettingsPresenter 생성/연결 실패: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패: {error_msg}")

        # 5. 초기화 완료
        self._logger.info("✅ Database 설정 컴포넌트 완전 조립 완료 (MVP + 초기화)")

        return view


class UiSettingsComponentFactory(BaseComponentFactory):
    """UI 설정 컴포넌트 전용 Factory"""

    def get_component_type(self) -> str:
        return "ui_settings"

    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        """UI 설정 컴포넌트 생성 - 표준 Container 접근 패턴 사용"""
        # 1. 표준 ApplicationServiceContainer 접근
        container = self._get_application_container()

        # UI 설정에 필요한 서비스들 로드
        settings_service = self._get_service(
            container.get_settings_service, "Settings"
        )
        app_logging_service = self._get_service(
            container.get_logging_service, "Logging"
        )
        self._logger.info("✅ 표준 ApplicationContainer 서비스 사용 (정상 경로)")

        # 2. View 생성 (실패 시 즉시 에러)
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.ui_settings.views.ui_settings_view import UISettingsView
            component_logger = self._logging_service.get_component_logger("UISettingsView")

            view = UISettingsView(
                parent=parent,
                logging_service=component_logger
            )
        except Exception as e:
            error_msg = f"❌ UISettingsView 생성 실패: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패: {error_msg}")

        # 3. Presenter 생성 및 연결 (실패 시 즉시 에러)
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.ui_settings.presenters.ui_settings_presenter import (
                UISettingsPresenter
            )

            presenter_logger = app_logging_service.get_component_logger("UISettingsPresenter")
            presenter = UISettingsPresenter(
                view=view,
                settings_service=settings_service,
                logging_service=presenter_logger
            )

            # 4. MVP 패턴 연결 (실패 시 즉시 에러)
            view.set_presenter(presenter)
        except Exception as e:
            error_msg = f"❌ UISettingsPresenter 생성/연결 실패: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패: {error_msg}")

        # 5. 초기 데이터 로드 (실패해도 View는 반환, 하지만 에러 로그 남김)
        try:
            presenter.load_settings()
            self._logger.info("✅ UI 설정 컴포넌트 완전 조립 완료 (MVP + 초기화)")
        except Exception as e:
            error_msg = f"❌ 초기 설정 로드 실패: {e}"
            self._logger.error(error_msg)
            # 초기 데이터 실패는 치명적이지 않으므로 View는 반환하되 명확한 에러 로그

        return view


class LoggingSettingsComponentFactory(BaseComponentFactory):
    """로깅 설정 컴포넌트 전용 Factory"""

    def get_component_type(self) -> str:
        return "logging_settings"

    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        """로깅 관리 컴포넌트 생성 - 표준 Container 접근 패턴 사용"""
        # 1. 표준 ApplicationServiceContainer 접근
        container = self._get_application_container()

        # Logging 관리에 필요한 서비스 로드
        app_logging_service = self._get_service(
            container.get_logging_service, "Logging"
        )
        self._logger.info("✅ 표준 ApplicationContainer 서비스 사용 (정상 경로)")

        # 2. View 생성 (실패 시 즉시 에러)
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.logging_management.logging_management_view import (
                LoggingManagementView
            )
            component_logger = self._logging_service.get_component_logger("LoggingManagementView")

            view = LoggingManagementView(
                parent=parent,
                logging_service=component_logger
            )
        except Exception as e:
            error_msg = f"❌ LoggingManagementView 생성 실패: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패: {error_msg}")

        # 3. Presenter 생성 및 연결 (실패 시 즉시 에러)
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.logging_management.presenters import (
                logging_management_presenter
            )
            LoggingManagementPresenter = logging_management_presenter.LoggingManagementPresenter

            presenter_logger = app_logging_service.get_component_logger("LoggingManagementPresenter")
            presenter = LoggingManagementPresenter(
                view=view,
                logging_service=presenter_logger
            )

            # 4. MVP 패턴 연결 (실패 시 즉시 에러)
            view.set_presenter(presenter)
        except Exception as e:
            error_msg = f"❌ LoggingManagementPresenter 생성/연결 실패: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패: {error_msg}")

        # 5. 초기화 완료
        self._logger.info("✅ Logging 관리 컴포넌트 완전 조립 완료 (MVP + 초기화)")

        return view


class NotificationSettingsComponentFactory(BaseComponentFactory):
    """알림 설정 컴포넌트 전용 Factory"""

    def get_component_type(self) -> str:
        return "notification_settings"

    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        """알림 설정 컴포넌트 생성 - 표준 Container 접근 패턴 사용"""
        # 1. 표준 ApplicationServiceContainer 접근
        container = self._get_application_container()

        # Notification 설정에 필요한 서비스들 로드
        notification_service = self._get_service(
            container.get_notification_service, "Notification"
        )
        app_logging_service = self._get_service(
            container.get_logging_service, "Logging"
        )
        self._logger.info("✅ 표준 ApplicationContainer 서비스 사용 (정상 경로)")

        # 2. View 생성 (실패 시 즉시 에러)
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.notification_settings.views.notification_settings_view import (
                NotificationSettingsView
            )
            component_logger = self._logging_service.get_component_logger("NotificationSettingsView")

            view = NotificationSettingsView(
                parent=parent,
                logging_service=component_logger
            )
        except Exception as e:
            error_msg = f"❌ NotificationSettingsView 생성 실패: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패: {error_msg}")

        # 3. Presenter 생성 및 연결 (실패 시 즉시 에러)
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.notification_settings.presenters import (
                notification_settings_presenter
            )
            NotificationSettingsPresenter = notification_settings_presenter.NotificationSettingsPresenter

            presenter_logger = app_logging_service.get_component_logger("NotificationSettingsPresenter")
            presenter = NotificationSettingsPresenter(
                view=view,
                notification_service=notification_service,
                logging_service=presenter_logger
            )

            # 4. MVP 패턴 연결 (실패 시 즉시 에러)
            view.set_presenter(presenter)
        except Exception as e:
            error_msg = f"❌ NotificationSettingsPresenter 생성/연결 실패: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패: {error_msg}")

        # 5. 초기화 완료
        self._logger.info("✅ Notification 설정 컴포넌트 완전 조립 완료 (MVP + 초기화)")

        return view


class EnvironmentProfileComponentFactory(BaseComponentFactory):
    """환경 프로필 컴포넌트 전용 Factory"""

    def get_component_type(self) -> str:
        return "environment_profile"

    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        """환경 프로필 컴포넌트 생성 - 표준 Container 접근 패턴 사용"""
        # 1. 표준 ApplicationServiceContainer 접근
        container = self._get_application_container()

        # Environment Profile에 필요한 서비스들 로드
        profile_service = self._get_service(
            container.get_profile_service, "Profile"
        )
        app_logging_service = self._get_service(
            container.get_logging_service, "Logging"
        )
        self._logger.info("✅ 표준 ApplicationContainer 서비스 사용 (정상 경로)")

        # 2. View 생성 (실패 시 즉시 에러)
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.environment_profile.environment_profile_view import (
                EnvironmentProfileView
            )
            component_logger = self._logging_service.get_component_logger("EnvironmentProfileView")

            view = EnvironmentProfileView(
                parent=parent,
                logging_service=component_logger
            )
        except Exception as e:
            error_msg = f"❌ EnvironmentProfileView 생성 실패: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패: {error_msg}")

        # 3. Presenter 생성 및 연결 (실패 시 즉시 에러)
        try:
            from upbit_auto_trading.ui.desktop.screens.settings.environment_profile.presenters import (
                environment_profile_presenter
            )
            EnvironmentProfilePresenter = environment_profile_presenter.EnvironmentProfilePresenter

            presenter_logger = app_logging_service.get_component_logger("EnvironmentProfilePresenter")
            presenter = EnvironmentProfilePresenter(
                view=view,
                profile_service=profile_service,
                logging_service=presenter_logger
            )

            # 4. MVP 패턴 연결 (실패 시 즉시 에러)
            view.set_presenter(presenter)
        except Exception as e:
            error_msg = f"❌ EnvironmentProfilePresenter 생성/연결 실패: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패: {error_msg}")

        # 5. 초기화 완료
        self._logger.info("✅ Environment Profile 컴포넌트 완전 조립 완료 (MVP + 초기화)")

        return view


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
