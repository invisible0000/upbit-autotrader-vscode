"""
권장 구현: Factory + 캐싱 패턴
DDD Infrastructure Layer 경로 관리에 최적화
"""

import threading
from typing import Dict, Optional
from pathlib import Path

from upbit_auto_trading.domain.configuration.repositories.path_configuration_repository import IPathConfigurationRepository
from upbit_auto_trading.domain.configuration.services.path_configuration_service import PathConfigurationService
from upbit_auto_trading.infrastructure.persistence.config_path_repository import ConfigPathRepository
from upbit_auto_trading.infrastructure.logging import create_component_logger


class PathServiceFactory:
    """
    Path Service Factory + 캐싱 패턴

    장점:
    - DDD 원칙 준수: Factory는 Infrastructure, Service는 Domain
    - 테스트 용이성: clear_cache()로 완전 격리
    - 확장성: 다양한 설정 타입 지원
    - Thread-Safe: Lock 보장
    """

    _cache: Dict[str, PathConfigurationService] = {}
    _lock = threading.Lock()
    _logger = create_component_logger("PathServiceFactory")

    @classmethod
    def create_path_service(cls, config_type: str = "default") -> PathConfigurationService:
        """캐시된 Path Service 생성"""

        if config_type not in cls._cache:
            with cls._lock:
                # Double-checked locking
                if config_type not in cls._cache:
                    cls._logger.info(f"🏭 PathService 생성: {config_type}")

                    # Repository 생성 (Infrastructure)
                    config_repository = cls._create_repository(config_type)

                    # Domain Service 생성
                    path_service = PathConfigurationService(config_repository)
                    path_service.initialize_directories()

                    cls._cache[config_type] = path_service
                    cls._logger.info(f"✅ PathService 캐싱 완료: {config_type}")

        return cls._cache[config_type]

    @classmethod
    def _create_repository(cls, config_type: str) -> IPathConfigurationRepository:
        """설정 타입별 Repository 생성"""

        if config_type == "test":
            # 테스트용 별도 설정 파일
            test_config = Path("config/paths_config_test.yaml")
            return ConfigPathRepository(test_config)
        elif config_type == "custom":
            # 사용자 정의 설정
            custom_config = Path("config/paths_config_custom.yaml")
            return ConfigPathRepository(custom_config)
        else:
            # 기본 설정
            return ConfigPathRepository()

    @classmethod
    def get_cached_service(cls, config_type: str = "default") -> Optional[PathConfigurationService]:
        """캐시된 서비스 조회 (생성하지 않음)"""
        return cls._cache.get(config_type)

    @classmethod
    def clear_cache(cls, config_type: Optional[str] = None) -> None:
        """캐시 클리어 (테스트용)"""
        with cls._lock:
            if config_type:
                cls._cache.pop(config_type, None)
                cls._logger.info(f"🧹 PathService 캐시 클리어: {config_type}")
            else:
                cls._cache.clear()
                cls._logger.info("🧹 PathService 전체 캐시 클리어")

    @classmethod
    def get_cache_status(cls) -> Dict[str, str]:
        """캐시 상태 조회 (디버깅용)"""
        return {
            config_type: f"Loaded-{service.__class__.__name__}"
            for config_type, service in cls._cache.items()
        }


# 편의 함수들
def get_path_service(config_type: str = "default") -> PathConfigurationService:
    """Path Service 조회 (권장 사용법)"""
    return PathServiceFactory.create_path_service(config_type)


def get_default_path_service() -> PathConfigurationService:
    """기본 Path Service 조회"""
    return PathServiceFactory.create_path_service("default")


def get_test_path_service() -> PathConfigurationService:
    """테스트용 Path Service 조회"""
    return PathServiceFactory.create_path_service("test")


# Legacy 호환성 (점진적 마이그레이션용)
def get_shared_path_service() -> PathConfigurationService:
    """Legacy 호환성 함수"""
    return get_default_path_service()


if __name__ == "__main__":
    # 사용 예시
    service = get_path_service()
    print(f"Data Dir: {service.get_directory_path('data')}")

    # 테스트용
    test_service = get_test_path_service()
    PathServiceFactory.clear_cache("test")
