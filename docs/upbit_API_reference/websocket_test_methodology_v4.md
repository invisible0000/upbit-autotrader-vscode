# 업비트 WebSocket API 테스트 방법론 v4.0

## 🎯 핵심 원칙
- **1파일 = 1데이터타입 = 7테스트** (관리 단순화)
- **표준 7테스트 템플릿** (일관성 보장)
- **실제 업비트 서버 통신** (완전 검증)
- **캔들 9종 완전 지원** (1s~240m)

## 📁 파일 구조
```
tests\infrastructure\test_external_apis\upbit\test_websocket_v5
├── conftest.py                    # pytest 공통 설정
├── public/
│   ├── test01_ticker.py             # 현재가 7테스트
│   ├── test02_orderbook.py          # 호가 7테스트
│   ├── test03_trade.py              # 체결 7테스트
│   ├── test04_candle.py             # 캔들 7테스트 (9종)
│   ├── test05_mixed_public.py       # Public 조합 7테스트
│   └── test06_subscription_mgmt.py  # 구독 관리 7테스트
└── private/
    ├── test01_asset.py              # 자산 7테스트
    ├── test02_order.py              # 주문 7테스트
    ├── test03_mixed_private.py      # Private 조합 7테스트
    └── test04_subscription_mgmt.py  # Private 구독 관리 7테스트
```

## 🧪 표준 7테스트 템플릿

### 개별 데이터 타입 (ticker/orderbook/trade/candle/asset/order)
```python
class TestDataType:
    def test01_single_symbol_snapshot(self):
        """기본: KRW-BTC 스냅샷 요청"""

    def test02_multi_symbol_snapshot(self):
        """일괄: 전체 KRW 마켓 스냅샷 요청"""

    def test03_single_symbol_realtime(self):
        """실시간: KRW-BTC 실시간 스트림"""

    def test04_multi_symbol_realtime(self):
        """고부하: 전체 KRW 마켓 실시간 스트림"""

    def test05_random_symbol_rotation(self):
        """랜덤순회: 심볼+옵션 4시나리오 빠른순환"""

    def test06_snapshot_realtime_hybrid(self):
        """하이브리드: 스냅샷+실시간 혼합사용"""

    def test07_connection_error_recovery(self):
        """복구: 연결오류 및 자동복구"""
```

### Mixed 테스트 (조합 처리)
```python
class TestMixedDataTypes:
    def test01_all_types_single_symbol(self):
        """단일심볼 전체타입: KRW-BTC 모든타입 동시"""

    def test02_all_types_multi_symbol(self):
        """다중심볼 전체타입: 10심볼 모든타입 처리"""

    def test03_all_types_realtime_stream(self):
        """전체타입 실시간: 모든타입 동시 실시간"""

    def test04_snapshot_realtime_mixed(self):
        """혼합사용: 타입별 스냅샷+실시간 조합"""

    def test05_client_id_isolation(self):
        """클라이언트분리: 다중 클라이언트 독립처리"""

    def test06_subscription_optimization(self):
        """구독최적화: 중복구독 통합 및 효율성"""

    def test07_enterprise_performance(self):
        """성능측정: 대규모 처리 Enterprise급 테스트"""
```

### 구독 관리 테스트
```python
class TestSubscriptionManagement:
    def test01_request_realtime_data(self):
        """실시간요청: 실시간 데이터 구독 관리"""

    def test02_request_snapshot_data(self):
        """스냅샷요청: 스냅샷 데이터 즉시 반환"""

    def test03_stop_realtime_data(self):
        """실시간중단: 실시간 구독 중단 처리"""

    def test04_auto_connection_management(self):
        """자동연결: Public/Private 자동 판단"""

    def test05_subscription_optimization(self):
        """구독최적화: 지능적 구독 통합 엔진"""

    def test06_lifecycle_management(self):
        """생명주기: 자동 정리 및 성능 모니터링"""

    def test07_force_reconnect_recovery(self):
        """강제재연결: 성능 저하시 자동 재연결"""
```

## 🔄 랜덤 심볼 순회 (Random Symbol Rotation) v4.0

### 개념 설명
- **4시나리오**: 랜덤조합 3종 + 무구독상태 1종
- **빠른순환**: 각 시나리오 3초씩 총 12초 테스트
- **완전랜덤**: 심볼, 옵션(스냅샷/실시간/기본값), 데이터타입 모두 랜덤

### 구현 시나리오
```python
async def test05_random_symbol_rotation(self):
    """심볼+옵션 완전랜덤 4시나리오 빠른순환"""

    scenarios = [
        # 시나리오 1: 랜덤 조합 A
        {
            "name": "랜덤조합A",
            "symbols": random.sample(all_krw_symbols, 5),
            "options": random.choice(["snapshot", "realtime", "default"]),
            "data_types": random.sample(all_data_types, 2)
        },
        # 시나리오 2: 랜덤 조합 B
        {
            "name": "랜덤조합B",
            "symbols": random.sample(all_krw_symbols, 8),
            "options": random.choice(["snapshot", "realtime", "default"]),
            "data_types": random.sample(all_data_types, 3)
        },
        # 시나리오 3: 랜덤 조합 C
        {
            "name": "랜덤조합C",
            "symbols": random.sample(all_krw_symbols, 3),
            "options": random.choice(["snapshot", "realtime", "default"]),
            "data_types": random.sample(all_data_types, 1)
        },
        # 시나리오 4: 무구독 상태
        {
            "name": "무구독상태",
            "symbols": [],
            "options": None,
            "data_types": []
        }
    ]

    for scenario in scenarios:
        print(f"🔄 {scenario['name']}: {len(scenario['symbols'])}심볼, {scenario['options']}")

        # 구독 적용
        if scenario['symbols']:
            await apply_subscription(scenario)
        else:
            await clear_all_subscriptions()

        # 3초 동작 확인
        await asyncio.sleep(3)
```

## 📊 데이터 타입 전체 목록

### Public 데이터 (6종)
- **ticker**: 현재가
- **orderbook**: 호가
- **trade**: 체결
- **candle**: 캔들 (9종 - 1s/1m/3m/5m/10m/15m/30m/60m/240m)

### Private 데이터 (2종)
- **myorder**: 내 주문 및 체결
- **myasset**: 내 자산

### 옵션 종류 (3종)
- **snapshot**: 스냅샷만 (is_only_snapshot=true)
- **realtime**: 실시간만 (is_only_realtime=true)
- **default**: 기본값 (스냅샷+실시간)

## 📊 성능 기준
```python
CRITERIA = {
    "connection_time": 1.0,        # 연결 < 1초
    "first_message": 1.0,          # 첫메시지 < 1초
    "message_rate": 100,           # 처리속도 > 100 msg/s
    "memory_usage": 200,           # 메모리 < 200MB
    "uptime": 3600,                # 1시간 무중단
    "subscription_efficiency": 80   # 구독효율 > 80%
}
```

## 🚀 실행 명령어

### 개별 테스트
```powershell
# Public 개별 타입
pytest tests/websocket_v5/public/test01_ticker.py -v
pytest tests/websocket_v5/public/test04_candle.py -v

# Private 개별 타입
pytest tests/websocket_v5/private/test01_asset.py -v
pytest tests/websocket_v5/private/test02_order.py -v

# 조합 테스트
pytest tests/websocket_v5/public/test05_mixed_public.py -v
pytest tests/websocket_v5/private/test03_mixed_private.py -v

# 구독 관리 테스트
pytest tests/websocket_v5/public/test06_subscription_mgmt.py -v
pytest tests/websocket_v5/private/test04_subscription_mgmt.py -v
```

### 통합 테스트
```powershell
# Public 전체
pytest tests/websocket_v5/public/ -v

# Private 전체
pytest tests/websocket_v5/private/ -v

# 전체 실행
pytest tests/websocket_v5/ -v
```

## 🔧 conftest.py 설정
```python
import pytest
import asyncio

@pytest.fixture
async def websocket_client():
    client = WebSocketClient()
    await client.connect()
    yield client
    await client.disconnect()

@pytest.fixture
def krw_symbols():
    return ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']

@pytest.fixture
def all_krw_symbols():
    # 실제 마켓 API에서 동적 로드
    return get_all_krw_markets()

@pytest.fixture
def candle_types():
    return ['1s', '1m', '3m', '5m', '10m', '15m', '30m', '60m', '240m']

@pytest.fixture
def all_data_types():
    return ['ticker', 'orderbook', 'trade'] + \
           [f'candle.{t}' for t in candle_types()]
```

## 📋 검증 패턴
```python
# Given-When-Then 패턴
async def test01_single_symbol_snapshot(self, client, krw_symbols):
    # Given
    symbol = krw_symbols[0]

    # When
    result = await client.request_snapshot_data([symbol], "ticker")

    # Then
    assert len(result) == 1
    assert result[0]['code'] == symbol
    assert 'trade_price' in result[0]
```

## 🎯 테스트 목표
- **WebSocket 클라이언트 기본 기능 빠른 검증**
- **캔들 9종 완전 지원 확인**
- **랜덤 순회로 실제 사용케이스 모사**
- **연결 오류 복구 메커니즘 검증**
- **구독 최적화 성능 측정**

---
**v4.0: 캔들 9종 + 랜덤순회 + 범용 간결성**
