"""
실제 코드로 보는 Factory 패턴의 2중 호출 해결 과정
"""

import threading
import time
from typing import Dict, Optional


print("=" * 60)
print("🔍 BEFORE: 2중 호출 문제가 있는 기존 방식")
print("=" * 60)

# 기존 방식 - 문제가 있는 코드
class ProblematicService:
    """문제가 있는 기존 방식"""
    def __init__(self):
        print(f"❌ ProblematicService 생성됨 (ID: {id(self)})")
        time.sleep(0.1)  # 초기화 시간 시뮬레이션

# 전역 변수로 관리 (문제 발생)
_service1 = None
_service2 = None

def get_service_old_way1():
    global _service1
    if _service1 is None:
        _service1 = ProblematicService()
    return _service1

def get_service_old_way2():
    global _service2
    if _service2 is None:
        _service2 = ProblematicService()
    return _service2

# 모듈 레벨에서 자동 생성 (더 큰 문제)
auto_created_service = ProblematicService()  # 즉시 생성!

print("\n📝 기존 방식 실행:")
svc1 = get_service_old_way1()
svc2 = get_service_old_way2()
print(f"   Service1 ID: {id(svc1)}")
print(f"   Service2 ID: {id(svc2)}")
print(f"   Auto Service ID: {id(auto_created_service)}")
print(f"   같은 객체? {svc1 is svc2}")  # False!
print(f"   총 생성된 인스턴스: 3개 (중복!)")

print("\n" + "=" * 60)
print("✅ AFTER: Factory + Caching으로 해결된 방식")
print("=" * 60)

class OptimizedService:
    """최적화된 서비스"""
    def __init__(self):
        print(f"✅ OptimizedService 생성됨 (ID: {id(self)})")
        time.sleep(0.1)  # 초기화 시간 시뮬레이션

class ServiceFactory:
    """Factory + Caching 패턴"""
    _instances: Dict[str, OptimizedService] = {}
    _lock = threading.Lock()

    @classmethod
    def get_service(cls, name: str = "default") -> OptimizedService:
        # Double-checked locking pattern
        if name not in cls._instances:
            with cls._lock:
                if name not in cls._instances:
                    print(f"🏭 Factory: 새 인스턴스 생성 중... ({name})")
                    cls._instances[name] = OptimizedService()
                else:
                    print(f"🔄 Factory: 락 안에서 기존 인스턴스 발견 ({name})")
            print(f"📦 Factory: 인스턴스 캐싱 완료 ({name})")
        else:
            print(f"⚡ Factory: 캐시에서 즉시 반환 ({name})")

        return cls._instances[name]

    @classmethod
    def get_cache_info(cls):
        return f"캐시된 인스턴스: {len(cls._instances)}개"

print("\n📝 Factory 방식 실행:")
print("1️⃣ 첫 번째 호출:")
factory_svc1 = ServiceFactory.get_service()

print("\n2️⃣ 두 번째 호출:")
factory_svc2 = ServiceFactory.get_service()

print("\n3️⃣ 다른 이름으로 호출:")
factory_svc3 = ServiceFactory.get_service("test")

print(f"\n📊 결과:")
print(f"   Service1 ID: {id(factory_svc1)}")
print(f"   Service2 ID: {id(factory_svc2)}")
print(f"   Service3 ID: {id(factory_svc3)}")
print(f"   svc1 is svc2? {factory_svc1 is factory_svc2}")  # True!
print(f"   svc1 is svc3? {factory_svc1 is factory_svc3}")  # False (다른 이름)
print(f"   {ServiceFactory.get_cache_info()}")

print("\n" + "=" * 60)
print("🧪 Thread Safety 테스트")
print("=" * 60)

import concurrent.futures

def worker(worker_id):
    """동시에 서비스를 요청하는 워커"""
    print(f"👷 Worker {worker_id} 시작")
    service = ServiceFactory.get_service("concurrent_test")
    print(f"👷 Worker {worker_id} 완료 - Service ID: {id(service)}")
    return id(service)

print("🚀 5개 스레드로 동시 접근 테스트:")
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(worker, i) for i in range(5)]
    results = [future.result() for future in concurrent.futures.as_completed(futures)]

print(f"\n📈 Thread Safety 결과:")
print(f"   모든 스레드가 같은 인스턴스를 받았나? {len(set(results)) == 1}")
print(f"   받은 인스턴스 ID들: {set(results)}")
print(f"   {ServiceFactory.get_cache_info()}")

print("\n" + "=" * 60)
print("📊 성능 비교 결과")
print("=" * 60)

print("🔴 기존 방식:")
print("   - 3개 인스턴스 생성 (중복)")
print("   - 메모리 사용량: 3x")
print("   - Thread-unsafe")
print("   - 모듈 로드 시 자동 생성")

print("\n🟢 Factory 방식:")
print("   - 필요한 만큼만 생성 (중복 없음)")
print("   - 메모리 사용량: 1x")
print("   - Thread-safe 보장")
print("   - 지연 로딩 (필요할 때만)")

print("\n💡 결론:")
print("Factory + Caching 패턴은 객체 생명주기를 완전히 제어하여")
print("중복 생성 문제를 근본적으로 해결합니다! 🎯")
