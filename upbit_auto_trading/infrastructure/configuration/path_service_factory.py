"""
Path Service Factory - Factory + Caching 패턴 구현
DDD 기반 경로 관리 시스템의 핵심 팩토리

특징:
- 인스턴스 캐싱으로 중복 생성 방지
- 테스트용 clear_cache() 지원
- Thread-safe 구현
- 환경별 분리된 인스턴스 관리
"""

import threading
from typing import Dict, Optional
from pathlib import Path

from upbit_auto_trading.infrastructure.persistence.config_path_repository import ConfigPathRepository
from upbit_auto_trading.domain.configuration.services.path_configuration_service import PathConfigurationService
from upbit_auto_trading.infrastructure.logging import create_component_logger


class PathServiceFactory:
    """Path Service 생성 및 캐싱을 관리하는 팩토리"""

    _lock = threading.Lock()
    _instances: Dict[str, PathConfigurationService] = {}
    _logger = create_component_logger("PathServiceFactory")

    @classmethod
    def get_service(cls, environment: str = "default") -> PathConfigurationService:
        """
        Path Service 인스턴스를 반환합니다.

        Args:
            environment: 환경 식별자 (default, test, etc.)

        Returns:
            PathConfigurationService 인스턴스
        """
        # Double-checked locking pattern
        if environment not in cls._instances:
            with cls._lock:
                if environment not in cls._instances:
                    cls._logger.info(f"🏭 새로운 PathService 인스턴스 생성: {environment}")

                    # Config Repository 생성
                    config_repository = ConfigPathRepository()

                    # Path Service 생성
                    service = PathConfigurationService(config_repository)

                    # 디렉터리 초기화
                    service.initialize_directories()

                    # 캐시에 저장
                    cls._instances[environment] = service

                    cls._logger.info(f"✅ PathService 캐싱 완료: {environment}")
                else:
                    cls._logger.debug(f"🔄 기존 PathService 인스턴스 반환: {environment}")

        return cls._instances[environment]

    @classmethod
    def clear_cache(cls, environment: Optional[str] = None) -> None:
        """
        캐시된 인스턴스를 제거합니다.

        Args:
            environment: 특정 환경만 제거 (None이면 전체 제거)
        """
        with cls._lock:
            if environment is None:
                cls._logger.info("🧹 전체 PathService 캐시 정리")
                cls._instances.clear()
            elif environment in cls._instances:
                cls._logger.info(f"🧹 PathService 캐시 제거: {environment}")
                del cls._instances[environment]

    @classmethod
    def get_cached_instances(cls) -> Dict[str, PathConfigurationService]:
        """캐시된 인스턴스 목록 반환 (디버깅용)"""
        return cls._instances.copy()

    @classmethod
    def create_test_service(cls, test_config_path: Optional[Path] = None) -> PathConfigurationService:
        """
        테스트용 독립적인 Path Service 생성

        Args:
            test_config_path: 테스트용 설정 파일 경로 (현재 미지원)

        Returns:
            테스트용 PathConfigurationService (캐싱되지 않음)
        """
        cls._logger.info("🧪 테스트용 PathService 생성")

        # 테스트용 Config Repository
        config_repository = ConfigPathRepository()

        # 테스트용 Path Service (캐싱하지 않음)
        service = PathConfigurationService(config_repository)
        service.initialize_directories()

        return service


# 기본 서비스 접근 함수들
def get_path_service() -> PathConfigurationService:
    """기본 Path Service 인스턴스 반환"""
    return PathServiceFactory.get_service("default")


def get_test_path_service() -> PathConfigurationService:
    """테스트용 Path Service 인스턴스 반환"""
    return PathServiceFactory.get_service("test")


def clear_path_service_cache() -> None:
    """Path Service 캐시 정리 (테스트용)"""
    PathServiceFactory.clear_cache()


# Legacy 호환성 함수들 (단계적 제거 예정)
def create_path_service() -> PathConfigurationService:
    """
    ⚠️ Deprecated: get_path_service() 사용 권장
    Legacy 호환성을 위한 함수
    """
    return get_path_service()


def get_shared_path_service() -> PathConfigurationService:
    """
    ⚠️ Deprecated: get_path_service() 사용 권장
    Legacy 호환성을 위한 함수
    """
    return get_path_service()


__all__ = [
    'PathServiceFactory',
    'get_path_service',
    'get_test_path_service',
    'clear_path_service_cache',
    # Legacy (제거 예정)
    'create_path_service',
    'get_shared_path_service',
]
