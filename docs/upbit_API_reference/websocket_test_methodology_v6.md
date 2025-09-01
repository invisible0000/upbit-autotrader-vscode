# 업비트 WebSocket API 테스트 방법론 v6.0

## 🎯 **핵심 원칙**
- **전역 관리자 기반**: GlobalWebSocketManager 중심 테스트
- **API 키 선택적**: Public/Private 기능 분리 테스트
- **간결한 5테스트 패턴**: 필수 기능만 검증
- **Mock 우선**: 단위 테스트 시 실제 API 호출 최소화
- **WebSocketClientProxy 활용**: 상위 레벨 인터페이스 테스트

## 🚀 **v6.0 주요 개선사항**
- **중앙 집중 테스트**: 하나의 전역 관리자로 모든 기능 테스트
- **자동 인증 관리**: API 키 설정 자동화, 테스트 코드 단순화
- **프록시 패턴**: WebSocketClientProxy를 통한 고수준 API 테스트
- **리소스 자동 정리**: WeakRef 기반 자동 정리로 테스트 격리 보장

## 📁 **파일 구조 (v6.0 간소화)**
```
tests/infrastructure/test_external_apis/upbit/websocket_v6/
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
    def test01_initialization(self):
        """초기화: 기본 설정으로 컴포넌트 초기화"""

    def test02_core_functionality(self):
        """핵심기능: 주요 기능 정상 동작 확인"""

    def test03_error_handling(self):
        """에러처리: 예외 상황 적절한 처리 확인"""

    def test04_resource_cleanup(self):
        """리소스정리: 자동 정리 메커니즘 검증"""

    def test05_edge_cases(self):
        """경계사례: 특수 상황 및 극한 케이스 검증"""
```

## 🔧 **conftest.py 설정 (v6.0 전역 관리자)**

```python
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v6 import (
    GlobalWebSocketManager, WebSocketClientProxy
)

@pytest.fixture
async def global_manager():
    """전역 WebSocket 관리자 (API 키 선택적)"""
    manager = await GlobalWebSocketManager.get_instance()

    # API 키 환경변수에서 자동 로드 시도
    await manager.initialize()

    yield manager

    # 테스트 후 정리
    await manager.cleanup()

@pytest.fixture
async def public_client(global_manager):
    """Public 전용 클라이언트 프록시"""
    client = WebSocketClientProxy("test_public")
    yield client
    await client.cleanup()

@pytest.fixture
async def private_client(global_manager):
    """Private 클라이언트 프록시 (API 키 필요)"""
    if not global_manager.is_private_available():
        pytest.skip("API 키 필요 - Private 테스트 건너뜀")

    client = WebSocketClientProxy("test_private")
    yield client
    await client.cleanup()

@pytest.fixture
def mock_websocket():
    """Mock WebSocket 연결"""
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.recv = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws

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

## 🚀 **실행 명령어 (v6.0)**

### **빠른 검증 (핵심만)**
```powershell
# 전역 관리자 테스트 (필수)
pytest tests/infrastructure/test_external_apis/upbit/websocket_v6/test_global_websocket_manager.py -v

# 프록시 인터페이스 테스트 (중요)
pytest tests/infrastructure/test_external_apis/upbit/websocket_v6/test_websocket_client_proxy.py -v

# Public 기능 (API 키 불필요)
pytest tests/infrastructure/test_external_apis/upbit/websocket_v6/test_public_features.py -v
```

### **완전 검증 (API 키 필요)**
```powershell
# Private 기능 포함 전체 테스트
pytest tests/infrastructure/test_external_apis/upbit/websocket_v6/ -v

# 통합 시나리오 테스트
pytest tests/infrastructure/test_external_apis/upbit/websocket_v6/test_integration_scenarios.py -v
```

### **Mock 기반 단위 테스트**
```powershell
# 실제 API 호출 없는 빠른 테스트
pytest tests/infrastructure/test_external_apis/upbit/websocket_v6/ -m "not integration" -v
```

## 🔍 **핵심 검증 패턴**

### **Mock을 활용한 단위 테스트**
```python
@pytest.mark.asyncio
async def test_subscription_with_mock(mock_websocket):
    """Mock WebSocket으로 구독 로직 단위 테스트"""
    # Given: Mock WebSocket 연결
    with patch('websockets.connect', return_value=mock_websocket):
        manager = await GlobalWebSocketManager.get_instance()

        # When: 구독 요청
        subscription_id = await manager.subscribe_ticker(['KRW-BTC'])

        # Then: 올바른 메시지 전송 확인
        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]

        assert '"type":"ticker"' in call_args
        assert '"codes":["KRW-BTC"]' in call_args
        assert subscription_id is not None
```

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
