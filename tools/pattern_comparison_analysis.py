"""
패턴 비교 분석: 공유 인스턴스 vs 싱글톤

DDD Infrastructure Layer 경로 관리 시스템에서의 적용 검토
"""

from typing import Optional
from pathlib import Path
import threading


# ==========================================
# 1. 현재 구현: 모듈 레벨 공유 인스턴스
# ==========================================

class ModuleLevelSharedInstance:
    """모듈 레벨 공유 인스턴스 패턴"""

    def __init__(self):
        self.config_loaded = False
        self.paths = {}

    def load_config(self):
        if not self.config_loaded:
            # 설정 로드 로직
            self.config_loaded = True

# 모듈 레벨에서 하나의 인스턴스만 생성
_shared_instance: Optional[ModuleLevelSharedInstance] = None

def get_shared_instance():
    global _shared_instance
    if _shared_instance is None:
        _shared_instance = ModuleLevelSharedInstance()
    return _shared_instance


# ==========================================
# 2. 고전적 싱글톤 패턴
# ==========================================

class ClassicSingleton:
    """고전적 싱글톤 패턴 (Thread-Safe)"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.config_loaded = False
            self.paths = {}
            self._initialized = True


# ==========================================
# 3. 메타클래스 기반 싱글톤
# ==========================================

class SingletonMeta(type):
    """메타클래스 기반 싱글톤"""
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class MetaclassSingleton(metaclass=SingletonMeta):
    """메타클래스 기반 싱글톤 구현"""

    def __init__(self):
        self.config_loaded = False
        self.paths = {}


# ==========================================
# 4. 의존성 주입 컨테이너 (현대적 접근)
# ==========================================

class DIContainer:
    """의존성 주입 컨테이너 (Singleton 인스턴스 관리)"""

    def __init__(self):
        self._singletons = {}
        self._lock = threading.Lock()

    def register_singleton(self, interface, implementation):
        """싱글톤으로 서비스 등록"""
        with self._lock:
            self._singletons[interface] = implementation

    def get_singleton(self, interface):
        """싱글톤 인스턴스 조회"""
        return self._singletons.get(interface)


# ==========================================
# 5. Factory + 캐싱 패턴 (우리 프로젝트에 적합)
# ==========================================

class PathServiceFactory:
    """팩토리 + 캐싱 패턴"""

    _cache = {}
    _lock = threading.Lock()

    @classmethod
    def create_path_service(cls, config_type: str = "default"):
        """캐시된 Path Service 생성"""
        if config_type not in cls._cache:
            with cls._lock:
                if config_type not in cls._cache:
                    # 실제 서비스 생성 로직
                    cls._cache[config_type] = f"PathService-{config_type}"
        return cls._cache[config_type]

    @classmethod
    def clear_cache(cls):
        """테스트용 캐시 클리어"""
        with cls._lock:
            cls._cache.clear()


if __name__ == "__main__":
    print("패턴 비교 분석용 코드 - 실행하지 마세요")
