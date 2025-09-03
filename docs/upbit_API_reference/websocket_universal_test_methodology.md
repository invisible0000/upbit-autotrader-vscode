# 🧪 범용 WebSocket 테스트 방법론 v6.0

> **"실제 API + 전역 관리자 + 자동 정리 = 간결하고 강력한 테스트"**

## 📋 문서 정보

- **문서 유형**: 범용 테스트 방법론
- **적용 대상**: WebSocket v6 기반 모든 시스템
- **핵심 원칙**: 실제 API 우선, 5테스트 패턴
- **작성일**: 2025년 9월 3일
- **분량**: 180줄 / 600줄 (30% 사용) 🟢

---

## 🎯 핵심 테스트 전략

### 📊 5테스트 패턴 개요

| 테스트 레이어 | 목적 | 실행 시간 | API 키 필요 |
|--------------|------|----------|-------------|
| **Manager** | 전역 관리자 기본 기능 | 5초 | ❌ |
| **Client** | 상위 레벨 인터페이스 | 10초 | ❌ |
| **Public** | Public 데이터 통합 | 15초 | ❌ |
| **Private** | Private 데이터 통합 | 20초 | ✅ |
| **Integration** | 실제 시나리오 | 30초 | ✅ |

### 🏗️ 테스트 아키텍처

```
테스트 계층 구조:
├── conftest.py          # 공통 픽스처 (전역 관리자)
├── test_manager.py      # 매니저 핵심 테스트
├── test_client.py       # 클라이언트 인터페이스
├── test_public.py       # Public 기능 검증
├── test_private.py      # Private 기능 검증 (API 키)
└── test_integration.py  # 시나리오 통합 테스트
```

---

## 🔧 표준 테스트 패턴

### 1. 📱 Manager 테스트 (기반 검증)

```python
# test_websocket_manager.py
@pytest.mark.asyncio
async def test_manager_singleton():
    """전역 관리자 싱글톤 검증"""
    manager1 = await get_global_websocket_manager()
    manager2 = await get_global_websocket_manager()
    assert manager1 is manager2

@pytest.mark.asyncio
async def test_manager_lifecycle():
    """생명주기 관리 검증"""
    manager = await get_global_websocket_manager()
    await manager.start()
    assert manager.get_state() == GlobalManagerState.ACTIVE
    await manager.stop()
```

### 2. 🎛️ Client 테스트 (인터페이스 검증)

```python
# test_websocket_client.py
@pytest.mark.asyncio
async def test_client_context_manager():
    """컨텍스트 매니저 자동 정리"""
    async with WebSocketClient("test_client") as client:
        assert client.is_active
    # 자동 정리 검증은 WeakRef로 처리됨

@pytest.mark.asyncio
async def test_client_subscription():
    """구독 기본 동작"""
    client = WebSocketClient("test_ticker")

    events = []
    def on_ticker(event):
        events.append(event)

    result = await client.subscribe_ticker(
        symbols=["KRW-BTC"],
        callback=on_ticker
    )
    assert result is True
```

### 3. 🌐 Public 테스트 (실제 API)

```python
# test_public_features.py
@pytest.mark.asyncio
async def test_ticker_realtime_subscription():
    """실제 현재가 데이터 수신"""
    events = []

    async with WebSocketClient("ticker_test") as client:
        await client.subscribe_ticker(
            symbols=["KRW-BTC"],
            callback=lambda e: events.append(e)
        )

        # 실제 데이터 대기 (최대 10초)
        await asyncio.wait_for(
            wait_for_events(events, 1),
            timeout=10.0
        )

    assert len(events) >= 1
    assert events[0].symbol == "KRW-BTC"
    assert events[0].trade_price is not None
```

### 4. 🔐 Private 테스트 (API 키 필요)

```python
# test_private_features.py
@pytest.mark.skipif(not has_api_keys(), reason="API 키 없음")
@pytest.mark.asyncio
async def test_myorder_subscription():
    """내 주문 실시간 수신"""
    events = []

    async with WebSocketClient("order_test") as client:
        await client.subscribe_my_order(
            callback=lambda e: events.append(e)
        )

        # Private 연결은 즉시 스냅샷 수신 가능
        await asyncio.sleep(5.0)

    # 주문이 없어도 연결 성공은 검증
    health = await client.get_health_status()
    assert health.status == "healthy"
```

### 5. 🔄 Integration 테스트 (실제 시나리오)

```python
# test_integration_scenarios.py
@pytest.mark.asyncio
async def test_multi_data_subscription():
    """다중 데이터 타입 동시 구독"""
    ticker_events = []
    trade_events = []

    async with WebSocketClient("multi_test") as client:
        await client.subscribe_ticker(
            symbols=["KRW-BTC"],
            callback=lambda e: ticker_events.append(e)
        )
        await client.subscribe_trade(
            symbols=["KRW-BTC"],
            callback=lambda e: trade_events.append(e)
        )

        await asyncio.sleep(15.0)

    assert len(ticker_events) >= 1
    assert len(trade_events) >= 1
```

---

## 🛠️ 공통 테스트 유틸리티

### 📋 conftest.py (공통 픽스처)

```python
# conftest.py
@pytest.fixture(scope="session")
async def global_manager():
    """전역 WebSocket 매니저"""
    manager = await get_global_websocket_manager()
    await manager.start()
    yield manager
    await manager.stop()

@pytest.fixture
def api_keys():
    """API 키 로딩"""
    return load_api_keys_if_available()

def has_api_keys() -> bool:
    """API 키 존재 여부"""
    return load_api_keys_if_available() is not None

async def wait_for_events(events_list, count, timeout=10.0):
    """이벤트 대기 헬퍼"""
    start_time = time.time()
    while len(events_list) < count:
        if time.time() - start_time > timeout:
            raise TimeoutError(f"이벤트 {count}개 대기 시간 초과")
        await asyncio.sleep(0.1)
```

---

## ⚡ 실행 명령어

### 🚀 기본 테스트 (API 키 불필요)

```bash
# 전체 기본 테스트
pytest tests/websocket_v6/ -v

# 단계별 실행
pytest tests/websocket_v6/test_manager.py -v     # 1단계: 매니저
pytest tests/websocket_v6/test_client.py -v      # 2단계: 클라이언트
pytest tests/websocket_v6/test_public.py -v      # 3단계: Public API
```

### 🔐 완전 검증 (API 키 필요)

```bash
# Private 기능 포함 전체 테스트
pytest tests/websocket_v6/ -v --run-private

# 성능 벤치마크 포함
pytest tests/websocket_v6/ -v --benchmark
```

### 🎯 선택적 실행

```bash
# 빠른 검증 (매니저 + 클라이언트만)
pytest tests/websocket_v6/test_manager.py tests/websocket_v6/test_client.py

# 실제 API 통합 테스트만
pytest tests/websocket_v6/test_public.py tests/websocket_v6/test_integration.py
```

---

## 🎯 성공 기준

### ✅ 기본 성공 조건

| 테스트 영역 | 성공 기준 | 실행 시간 |
|------------|----------|----------|
| **Manager** | 싱글톤 + 생명주기 | < 5초 |
| **Client** | 컨텍스트 + 구독 | < 10초 |
| **Public** | 실제 데이터 1회 수신 | < 15초 |
| **Private** | 연결 성공 (데이터 선택) | < 20초 |
| **Integration** | 다중 구독 성공 | < 30초 |

### 📊 성능 벤치마크

```python
# 성능 기준 (업비트 API 기준)
PERFORMANCE_CRITERIA = {
    'connection_time': 3.0,      # 연결 시간 < 3초
    'first_message': 5.0,        # 첫 메시지 < 5초
    'message_rate': 10,          # 초당 메시지 >= 10개
    'memory_usage': 50,          # 메모리 사용량 < 50MB
    'reconnect_time': 5.0        # 재연결 시간 < 5초
}
```

---

## 🔍 실패 시 진단

### 🚨 공통 오류 패턴

| 오류 유형 | 원인 | 해결책 |
|----------|------|--------|
| **연결 실패** | 네트워크/API 키 | API 키 확인, 네트워크 상태 점검 |
| **타임아웃** | Rate Limit | 대기 시간 증가, 재시도 간격 조정 |
| **메시지 없음** | 심볼 오류 | 유효한 심볼 사용 (KRW-BTC 등) |
| **메모리 누수** | 정리 미흡 | WeakRef 자동 정리 확인 |

### 📝 디버깅 팁

```python
# 로깅 활성화
import logging
logging.getLogger("WebSocketManager").setLevel(logging.DEBUG)

# 상태 모니터링
manager = await get_global_websocket_manager()
print(manager.get_all_connection_metrics())
print(manager.get_rate_limiter_status())
```

---

## 🎉 적용 가이드

### 🏗️ 새 프로젝트 적용

1. **테스트 구조 복사**: 5테스트 패턴 파일 생성
2. **픽스처 설정**: conftest.py로 공통 관리자 설정
3. **점진적 확장**: Manager → Client → Public → Private → Integration
4. **CI/CD 통합**: API 키 없는 기본 테스트를 CI에 포함

### 🔄 기존 시스템 마이그레이션

1. **호환성 검증**: 기존 Mock 테스트와 병행 실행
2. **단계별 전환**: 레이어별로 실제 API 테스트로 전환
3. **성능 모니터링**: 실제 API 테스트의 성능 영향 측정
4. **안정성 확보**: 일정 기간 dual-testing 후 완전 전환

---

**핵심 메시지**: "Mock 대신 실제 API로, 복잡함 대신 5테스트 패턴으로"

**문서 분량**: 180줄 / 600줄 (30% 사용) 🟢
**적용 범위**: WebSocket v6 기반 모든 실시간 데이터 시스템
**다음 읽기**: [WebSocket v6 아키텍처 가이드](WEBSOCKET_V6_UNIFIED_ARCHITECTURE.md)
