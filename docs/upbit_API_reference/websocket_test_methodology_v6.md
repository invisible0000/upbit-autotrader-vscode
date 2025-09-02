# 업비트 WebSocket API 테스트 방법론 v6.0 (실제 API 기반)

## 🎯 **핵심 원칙**
- **전역 관리자 기반**: GlobalWebSocketManager 중심 테스트
- **API 키 선택적**: Public/Private 기능 분리 테스트
- **실제 API 우선**: Mock 없이 실제 업비트 API로 검증
- **간결한 5테스트 패턴**: 필수 기능만 검증
- **WebSocketClientProxy 활용**: 상위 레벨 인터페이스 테스트

## 🚀 **v6.0 주요 개선사항**
- **실제 API 테스트**: Mock 제거, 실제 업비트 WebSocket API 연동
- **DDD 통합**: Application Service로 WebSocket v6 생명주기 관리
- **자동 인증 관리**: API 키 설정 자동화, 테스트 코드 단순화
- **프록시 패턴**: WebSocketClientProxy를 통한 고수준 API 테스트
- **리소스 자동 정리**: WeakRef 기반 자동 정리로 테스트 격리 보장
- **pytest-asyncio 자동화**: --asyncio-mode=auto로 비동기 테스트 단순화

## 📁 **파일 구조 (v6.0 간소화)**
```
tests/infrastructure/test_external_apis/upbit/test_websocket_v6/
├── conftest.py                          # 공통 픽스처 (전역 관리자)
├── test_global_websocket_manager.py     # 전역 관리자 핵심 테스트
├── test_websocket_client_proxy.py       # 프록시 클라이언트 테스트
├── test_public_features.py              # Public 기능 통합 테스트
├── test_private_features.py             # Private 기능 통합 테스트 (API 키 필요)
└── test_integration_scenarios.py       # 실제 시나리오 통합 테스트
```

## 🧪 **표준 5테스트 패턴**

### **핵심 컴포넌트 테스트**
```python
class TestComponent:
    @pytest.mark.asyncio
    async def test01_initialization(self):
        """초기화: 기본 설정으로 컴포넌트 초기화"""

    @pytest.mark.asyncio
    async def test02_core_functionality(self):
        """핵심기능: 주요 기능 정상 동작 확인"""

    @pytest.mark.asyncio
    async def test03_error_handling(self):
        """에러처리: 예외 상황 적절한 처리 확인"""

    @pytest.mark.asyncio
    async def test04_resource_cleanup(self):
        """리소스정리: 자동 정리 메커니즘 검증"""

    @pytest.mark.asyncio
    async def test05_edge_cases(self):
        """경계사례: 특수 상황 및 극한 케이스 검증"""
```

## 🔧 **conftest.py 설정 (v6.0 실제 API 기반)**

```python
import pytest
import asyncio
import os
import time
from typing import Dict, Any

from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v6 import (
    WebSocketClientProxy,
    get_global_websocket_manager,
    WebSocketType
)

@pytest.fixture(scope="session")
def event_loop():
    """세션 레벨 이벤트 루프"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def global_manager():
    """전역 WebSocket 관리자 (실제 API 연결)"""
    logger.info("전역 WebSocket 관리자 초기화 시작")

    try:
        # 전역 관리자 인스턴스 가져오기
        manager = await get_global_websocket_manager()

        # API 키 환경변수 확인
        access_key = os.getenv('UPBIT_ACCESS_KEY')
        secret_key = os.getenv('UPBIT_SECRET_KEY')

        if access_key and secret_key:
            logger.info("API 키 발견 - Private API 테스트 가능")
        else:
            logger.info("API 키 없음 - Public API만 테스트")

        yield manager

    except Exception as e:
        logger.error(f"전역 관리자 초기화 실패: {e}")
        raise
    finally:
        # 테스트 후 정리
        try:
            if 'manager' in locals():
                await manager.shutdown(timeout=5.0)
        except Exception as e:
            logger.warning(f"정리 중 오류: {e}")

@pytest.fixture
async def public_client(global_manager):
    """Public 전용 클라이언트 프록시 (실제 API)"""
    client = WebSocketClientProxy("test_public_client")
    yield client
    await client.cleanup()

@pytest.fixture
async def private_client(global_manager):
    """Private 클라이언트 프록시 (API 키 필요)"""
    if not os.getenv('UPBIT_ACCESS_KEY'):
        pytest.skip("API 키 필요 - Private 테스트 건너뜀")

    client = WebSocketClientProxy("test_private_client")
    yield client
    await client.cleanup()

@pytest.fixture
def sample_symbols():
    """테스트용 심볼 목록"""
    return ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
```

## 📊 **테스트 대상별 우선순위**

### **1. 핵심 컴포넌트 (필수)**
```python
# test_global_websocket_manager.py
class TestGlobalWebSocketManager:
    def test01_singleton_pattern(self, global_manager):
        """싱글톤: 전역 관리자 유일성 보장"""

    def test02_api_key_auto_loading(self, global_manager):
        """API키 자동로딩: 환경변수/ApiKeyService 자동 감지"""

    def test03_connection_management(self, global_manager):
        """연결관리: WebSocket 연결 생성/해제"""

    def test04_subscription_lifecycle(self, global_manager):
        """구독생명주기: 구독 생성/관리/정리"""

    def test05_error_recovery(self, global_manager):
        """에러복구: 연결 끊김 시 자동 복구"""
```

### **2. 프록시 인터페이스 (중요)**
```python
# test_websocket_client_proxy.py
class TestWebSocketClientProxy:
    def test01_proxy_initialization(self, public_client):
        """프록시 초기화: 클라이언트 ID 및 설정"""

    def test02_public_api_access(self, public_client):
        """Public API: 인증 없이 공개 데이터 접근"""

    def test03_private_api_protection(self, public_client):
        """Private API 보호: API 키 없을 때 적절한 예외"""

    def test04_automatic_cleanup(self, public_client):
        """자동정리: WeakRef 기반 구독 자동 해제"""

    def test05_concurrent_clients(self, global_manager):
        """동시클라이언트: 여러 프록시 동시 사용"""
```

### **3. 기능 테스트 (검증)**
```python
# test_public_features.py
class TestPublicFeatures:
    def test01_ticker_subscription(self, public_client, sample_symbols):
        """현재가 구독: 기본 실시간 데이터"""

    def test02_orderbook_snapshot(self, public_client, sample_symbols):
        """호가 스냅샷: 호가창 데이터 요청"""

    def test03_trade_realtime(self, public_client, sample_symbols):
        """체결 실시간: 체결 내역 스트림"""

    def test04_mixed_subscriptions(self, public_client, sample_symbols):
        """혼합구독: 여러 데이터 타입 동시 구독"""

    def test05_large_symbol_list(self, public_client):
        """대량심볼: 전체 KRW 마켓 구독"""

# test_private_features.py (API 키 필요)
class TestPrivateFeatures:
    def test01_asset_monitoring(self, private_client):
        """자산모니터링: 계좌 자산 실시간 확인"""

    def test02_order_monitoring(self, private_client):
        """주문모니터링: 주문 체결/취소 알림"""

    def test03_jwt_token_refresh(self, private_client):
        """JWT 토큰 갱신: 자동 인증 토큰 갱신"""

    def test04_private_public_mixed(self, private_client, sample_symbols):
        """Private+Public 혼합: 동시 구독"""

    def test05_authentication_failure(self, global_manager):
        """인증실패: 잘못된 API 키 처리"""
```

## 🚀 **실행 명령어 (v6.0 실제 API)**

### **기본 테스트 실행**
```powershell
# 전역 관리자 테스트 (필수)
python -m pytest tests/infrastructure/test_external_apis/upbit/test_websocket_v6/test_global_websocket_manager.py -v --asyncio-mode=auto

# 프록시 인터페이스 테스트 (중요)
python -m pytest tests/infrastructure/test_external_apis/upbit/test_websocket_v6/test_websocket_client_proxy.py -v --asyncio-mode=auto

# Public 기능 (API 키 불필요)
python -m pytest tests/infrastructure/test_external_apis/upbit/test_websocket_v6/test_public_features.py -v --asyncio-mode=auto
```

### **완전 검증 (API 키 필요)**
```powershell
# Private 기능 포함 전체 테스트
python -m pytest tests/infrastructure/test_external_apis/upbit/test_websocket_v6/ -v --asyncio-mode=auto

# 통합 시나리오 테스트
python -m pytest tests/infrastructure/test_external_apis/upbit/test_websocket_v6/test_integration_scenarios.py -v --asyncio-mode=auto
```

### **API 키 설정**
```powershell
# 환경변수 설정 (PowerShell)
$env:UPBIT_ACCESS_KEY = "your_access_key"
$env:UPBIT_SECRET_KEY = "your_secret_key"

# 테스트 실행 시 자동 감지됨
python -m pytest tests/infrastructure/test_external_apis/upbit/test_websocket_v6/ -v --asyncio-mode=auto
```

### **성능 및 안정성 테스트**
```powershell
# 느린 테스트 포함 (연결 안정성)
python -m pytest tests/infrastructure/test_external_apis/upbit/test_websocket_v6/ -v --asyncio-mode=auto -m slow

# 성능 벤치마크
python -m pytest tests/infrastructure/test_external_apis/upbit/test_websocket_v6/ -v --asyncio-mode=auto -m performance
```

## 🔍 **핵심 검증 패턴**

### **실제 API 통합 테스트**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api_integration(global_manager, sample_symbols):
    """실제 업비트 API와 통합 테스트"""
    # Given: 실제 WebSocket 연결
    client = WebSocketClientProxy("integration_test")

    # When: 실제 구독 요청
    messages = []
    async def callback(data):
        messages.append(data)

    subscription_id = await client.subscribe_ticker(sample_symbols, callback)

    # Then: 실제 데이터 수신 확인
    await asyncio.sleep(2)  # 2초 대기

    assert len(messages) > 0
    assert 'trade_price' in messages[0]

    # 정리
    await client.unsubscribe(subscription_id)
```

### **성능 검증 패턴**
```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_performance_benchmark(global_manager, performance_monitor):
    """성능 벤치마크 테스트"""
    # Given: 성능 모니터 시작
    monitor = performance_monitor.start()

    # When: 대량 구독 요청
    tasks = []
    for symbol in large_symbol_list:
        task = asyncio.create_task(
            manager.subscribe_ticker([symbol])
        )
        tasks.append(task)

    subscription_ids = await asyncio.gather(*tasks)
    monitor.end()

    # Then: 성능 기준 확인
    monitor.assert_faster_than(5.0, "대량 구독")
    assert len(subscription_ids) > 0
```

### **연결 안정성 검증**
```python
@pytest.mark.slow
@pytest.mark.asyncio
async def test_connection_stability(global_manager):
    """장시간 연결 안정성 테스트"""
    # Given: 초기 연결 상태
    initial_health = await manager.get_health_status()

    # When: 30초 안정성 테스트
    await asyncio.sleep(30)

    # Then: 연결 유지 확인
    final_health = await manager.get_health_status()
    assert final_health.status == "healthy"
```

## 📈 **성능 기준 (v6.0 최적화)**
```python
PERFORMANCE_CRITERIA_V6 = {
    "manager_initialization": 1.0,       # 전역 관리자 초기화 < 1초
    "proxy_creation": 0.1,               # 프록시 생성 < 100ms
    "subscription_response": 0.5,        # 구독 응답 < 500ms
    "memory_overhead": 30,               # 메모리 오버헤드 < 30MB
    "concurrent_proxies": 50,            # 동시 프록시 수 > 50개
    "auto_cleanup_time": 5.0,            # 자동 정리 < 5초
}
```

## 🎯 **테스트 전략 요약**

### **개발 단계별 테스트 적용**
1. **개발 중**: Mock 기반 단위 테스트 (빠른 피드백)
2. **통합 단계**: Public 기능 실제 API 테스트
3. **배포 전**: Private 기능 포함 완전 검증
4. **운영 모니터링**: 지속적 성능 벤치마크

### **API 키 관리 전략**
- **CI/CD**: 환경변수로 API 키 주입
- **로컬 개발**: `.env` 파일 또는 ApiKeyService 활용
- **테스트 격리**: 각 테스트 후 자동 정리

### **실패 처리 방침**
- **API 키 없음**: Private 테스트 자동 스킵
- **네트워크 오류**: 재시도 후 실패 시 건너뜀
- **Rate Limit**: 지수 백오프 자동 적용

---

## 🆕 **v6.0 테스트 방법론 특징**

### **1. 전역 관리자 중심**
- 하나의 GlobalWebSocketManager로 모든 기능 통합 테스트
- 중복 연결 방지 및 자원 효율성 극대화

### **2. 프록시 패턴 활용**
- WebSocketClientProxy를 통한 고수준 API 테스트
- 개별 컴포넌트별 격리된 테스트 환경

### **3. 선택적 API 키 지원**
- Public 기능은 API 키 없이 완전 테스트
- Private 기능은 API 키 있을 때만 테스트

### **4. 자동화된 리소스 관리**
- WeakRef 기반 자동 정리로 테스트 간 격리 보장
- 메모리 누수 없는 안정적 테스트 환경

**v6.0: 전역 관리자 + 프록시 패턴 + 자동 리소스 관리**
