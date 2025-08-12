from typing import Dict, Any, TypeVar, Type, Callable, Optional, List
import inspect
from enum import Enum
import threading
import logging

T = TypeVar('T')

class LifetimeScope(Enum):
    """객체 생명주기 범위"""
    TRANSIENT = "transient"    # 매번 새 인스턴스
    SINGLETON = "singleton"    # 앱 전체에서 하나
    SCOPED = "scoped"         # 스코프 내에서 하나

class ServiceRegistration:
    """서비스 등록 정보"""

    def __init__(self, service_type: Type, implementation: Any,
                 lifetime: LifetimeScope = LifetimeScope.TRANSIENT,
                 factory: Optional[Callable] = None):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.factory = factory
        self.instance: Optional[Any] = None

class DIContainer:
    """의존성 주입 컨테이너"""

    def __init__(self, parent: Optional['DIContainer'] = None):
        """
        Args:
            parent: 부모 컨테이너 (계층적 컨테이너 지원)
        """
        self._services: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._parent = parent
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        self._disposing = False

    def register_singleton(self, service_type: Type,
                           implementation: Any = None) -> 'DIContainer':
        """싱글톤으로 서비스 등록"""
        return self._register(service_type, implementation, LifetimeScope.SINGLETON)

    def register_transient(self, service_type: Type,
                           implementation: Any = None) -> 'DIContainer':
        """일시적(매번 새 인스턴스)으로 서비스 등록"""
        return self._register(service_type, implementation, LifetimeScope.TRANSIENT)

    def register_scoped(self, service_type: Type,
                        implementation: Any = None) -> 'DIContainer':
        """스코프 내 싱글톤으로 서비스 등록"""
        return self._register(service_type, implementation, LifetimeScope.SCOPED)

    def register_factory(self, service_type: Type,
                         factory: Callable[[], Any],
                         lifetime: LifetimeScope = LifetimeScope.TRANSIENT) -> 'DIContainer':
        """팩토리 함수로 서비스 등록"""
        registration = ServiceRegistration(
            service_type=service_type,
            implementation=None,
            lifetime=lifetime,
            factory=factory
        )

        with self._lock:
            self._services[service_type] = registration

        return self

    def register_instance(self, service_type: Type, instance: Any) -> 'DIContainer':
        """기존 인스턴스로 서비스 등록 (싱글톤)"""
        registration = ServiceRegistration(
            service_type=service_type,
            implementation=instance,
            lifetime=LifetimeScope.SINGLETON
        )
        registration.instance = instance

        with self._lock:
            self._services[service_type] = registration
            self._instances[service_type] = instance

        return self

    def _register(self, service_type: Type, implementation: Any,
                  lifetime: LifetimeScope) -> 'DIContainer':
        """내부 등록 메서드"""
        if implementation is None:
            implementation = service_type

        registration = ServiceRegistration(
            service_type=service_type,
            implementation=implementation,
            lifetime=lifetime
        )

        with self._lock:
            self._services[service_type] = registration

        return self

    def resolve(self, service_type: Type) -> Any:
        """서비스 해결"""
        if self._disposing:
            raise RuntimeError("컨테이너가 해제된 상태입니다")

        with self._lock:
            # 현재 컨테이너에서 찾기
            if service_type in self._services:
                return self._create_instance(service_type)

            # 부모 컨테이너에서 서비스 등록 정보만 찾기 (SCOPED는 현재 스코프에서 인스턴스 생성)
            if self._parent and service_type in self._parent._services:
                parent_registration = self._parent._services[service_type]

                # SCOPED 서비스는 현재 스코프에서 새로 생성
                if parent_registration.lifetime == LifetimeScope.SCOPED:
                    # 부모 등록 정보를 복사하여 현재 컨테이너에서 관리
                    self._services[service_type] = ServiceRegistration(
                        service_type=parent_registration.service_type,
                        implementation=parent_registration.implementation,
                        lifetime=parent_registration.lifetime,
                        factory=parent_registration.factory
                    )
                    return self._create_instance(service_type)
                else:
                    # SINGLETON, TRANSIENT는 부모에게 위임
                    return self._parent.resolve(service_type)

            raise ServiceNotRegisteredError(f"서비스가 등록되지 않았습니다: {service_type}")

    def try_resolve(self, service_type: Type) -> Optional[Any]:
        """서비스 해결 시도 (실패 시 None 반환)"""
        try:
            return self.resolve(service_type)
        except ServiceNotRegisteredError:
            return None

    def _create_instance(self, service_type: Type) -> Any:
        """인스턴스 생성"""
        registration = self._services[service_type]

        # 싱글톤 인스턴스 확인
        if registration.lifetime == LifetimeScope.SINGLETON:
            if registration.instance is not None:
                return registration.instance

            if service_type in self._instances:
                return self._instances[service_type]

        # 스코프 인스턴스 확인
        elif registration.lifetime == LifetimeScope.SCOPED:
            if service_type in self._instances:
                return self._instances[service_type]

        # 새 인스턴스 생성
        if registration.factory:
            instance = registration.factory()
        else:
            # implementation이 클래스인지 확인
            if inspect.isclass(registration.implementation):
                instance = self._create_instance_with_injection(registration.implementation)
            elif callable(registration.implementation):
                # callable이지만 클래스가 아닌 경우 (함수 등)
                instance = registration.implementation()
            else:
                # callable이 아니면 그대로 반환 (예: 문자열, 숫자 등)
                instance = registration.implementation

        # 인스턴스 캐싱
        if registration.lifetime == LifetimeScope.SINGLETON:
            registration.instance = instance
            self._instances[service_type] = instance
        elif registration.lifetime == LifetimeScope.SCOPED:
            self._instances[service_type] = instance

        return instance

    def _create_instance_with_injection(self, implementation_type: Type) -> Any:
        """의존성 주입을 통한 인스턴스 생성"""
        try:
            # 생성자 시그니처 분석
            init_signature = inspect.signature(implementation_type.__init__)

            # 생성자 매개변수 해결
            kwargs = {}
            for param_name, param in init_signature.parameters.items():
                if param_name == 'self':
                    continue

                # 타입 힌트가 있는 경우
                if param.annotation != inspect.Parameter.empty:
                    try:
                        kwargs[param_name] = self.resolve(param.annotation)
                    except ServiceNotRegisteredError:
                        # 기본값이 있으면 사용
                        if param.default != inspect.Parameter.empty:
                            kwargs[param_name] = param.default
                        else:
                            raise DependencyResolutionError(
                                f"{implementation_type} 생성자의 매개변수 '{param_name}' "
                                f"(타입: {param.annotation})을 해결할 수 없습니다"
                            )

                # 기본값 사용
                elif param.default != inspect.Parameter.empty:
                    kwargs[param_name] = param.default

            return implementation_type(**kwargs)

        except Exception as e:
            self._logger.error(f"인스턴스 생성 실패 {implementation_type}: {e}")
            raise DependencyResolutionError(f"인스턴스 생성 실패: {e}") from e

    def is_registered(self, service_type: Type) -> bool:
        """서비스 등록 여부 확인"""
        if service_type in self._services:
            return True
        if self._parent:
            return self._parent.is_registered(service_type)
        return False

    def create_scope(self) -> 'DIContainer':
        """새 스코프 생성"""
        return DIContainer(parent=self)

    def get_registrations(self) -> List[ServiceRegistration]:
        """등록된 서비스 목록 조회"""
        with self._lock:
            return list(self._services.values())

    def dispose(self) -> None:
        """컨테이너 해제"""
        with self._lock:
            self._disposing = True

            # IDisposable 인터페이스를 구현한 인스턴스들 해제
            for instance in self._instances.values():
                if hasattr(instance, 'dispose'):
                    try:
                        instance.dispose()
                    except Exception as e:
                        self._logger.warning(f"인스턴스 해제 실패: {e}")

            self._instances.clear()
            self._services.clear()

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.dispose()

class ServiceNotRegisteredError(Exception):
    """서비스가 등록되지 않은 경우 발생하는 예외"""
    pass

class DependencyResolutionError(Exception):
    """의존성 해결 실패 시 발생하는 예외"""
    pass

# 전역 컨테이너 (선택적 사용)
_global_container: Optional[DIContainer] = None

def get_global_container() -> DIContainer:
    """전역 컨테이너 조회"""
    global _global_container
    if _global_container is None:
        _global_container = DIContainer()
    return _global_container

def set_global_container(container: DIContainer) -> None:
    """전역 컨테이너 설정"""
    global _global_container
    _global_container = container

def reset_global_container() -> None:
    """전역 컨테이너 재설정"""
    global _global_container
    if _global_container:
        _global_container.dispose()
    _global_container = None
