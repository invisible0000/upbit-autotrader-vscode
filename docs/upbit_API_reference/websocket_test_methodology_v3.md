# 업비트 WebSocket API 테스트 방법론 v3.0

## 🎯 핵심 원칙
- **1파일 = 1데이터타입 = 7테스트** (관리 단순화)
- **표준 7테스트 템플릿** (일관성 보장)
- **실제 업비트 서버 통신** (완전 검증)

## 📁 파일 구조
```
tests/infrastructure/external_apis/upbit/websocket_v5/
├── conftest.py                    # pytest 공통 설정
├── public/
│   ├── test01_ticker.py             # 현재가 7테스트
│   ├── test02_orderbook.py          # 호가 7테스트
│   ├── test03_trade.py              # 체결 7테스트
│   ├── test04_candle.py             # 캔들 7테스트
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
class TestTicker:
    def test01_single_symbol_single_request(self):
        """기본: KRW-BTC 1회(스냅샷)"""

    def test02_multi_symbol_single_request(self):
        """일괄: 전체 KRW 마켓 1회(스냅샷)"""

    def test03_single_symbol_multi_request(self):
        """연속: KRW-BTC 10회 연속(스냅샷)"""

    def test04_multi_symbol_multi_request(self):
        """고부하: 전체 KRW 마켓 5회 연속(스냅샷)"""

    def test05_only_realtime_stream(self):
        """스트림: 5초 실시간(리얼타임)"""

    def test06_multi_snapshot_with_stream(self):
        """하이브리드: 스냅샷 + 스트림 병행(기본값,핸들러 구분)"""

    def test07_error_recovery(self):
        """복구: 오류 생성 및 복구"""
```

### Mixed 테스트 (조합 처리)
```python
class TestMixedPublic:
    def test01_all_types_single_symbol(self):
        """단일심볼 전체타입: KRW-BTC 4타입 동시(스냅샷)"""

    def test02_all_types_multi_symbol(self):
        """다중심볼 전체타입: 10심볼 4타입 연속(스냅샷)"""

    def test03_all_types_realtime_stream(self):
        """전체타입 스트림: 4타입 동시 5초(리얼타임)"""

    def test04_all_types_snapshot_with_stream(self):
        """전체타입 하이브리드: 4타입 스냅샷+스트림(기본값,핸들러 구분)"""

    def test05_random_symbol_rotation(self):
        """랜덤심볼 순회: 4타입 고정, 심볼만 랜덤 변경(스냅샷)"""

    def test06_ticket_efficiency(self):
        """티켓효율성: 3티켓 최대 활용(스냅샷)"""

    def test07_performance_benchmark(self):
        """성능측정: 200+ 심볼 처리(스냅샷)"""
```

### 구독 관리 테스트
```python
class TestSubscriptionMgmt:
    def test01_basic_subscribe_unsubscribe(self):
        """기본: 구독→해제 순환"""

    def test02_multiple_subscription_management(self):
        """다중구독: 여러 구독 동시 관리"""

    def test03_subscription_modification(self):
        """구독수정: 심볼 추가/제거"""

    def test04_auto_reconnection(self):
        """자동재연결: 연결 끊김 복구"""

    def test05_ticket_pool_optimization(self):
        """티켓최적화: 효율적 티켓 사용"""

    def test06_subscription_state_tracking(self):
        """상태추적: 구독 상태 모니터링"""

    def test07_subscription_error_handling(self):
        """오류처리: 구독 오류 복구"""
```

## 🔄 랜덤 심볼 순회 (Random Symbol Rotation)

### 개념 설명
- **고정**: 모든 데이터 타입 (ticker, trade, orderbook, candle)
- **변경**: 각 타입별 구독 심볼을 랜덤하게 순환

### 구현 예시
```python
async def test05_random_symbol_rotation(self, client):
    """4타입 고정, 심볼만 랜덤 순환"""

    # 심볼 풀 정의
    symbol_pools = {
        'major': ['KRW-BTC', 'KRW-ETH'],
        'mid': ['KRW-XRP', 'KRW-ADA', 'KRW-DOT'],
        'minor': ['KRW-DOGE', 'KRW-SHIB', 'KRW-AVAX']
    }

    # 3라운드 랜덤 조합
    for round_num in range(3):
        # 각 타입별 랜덤 심볼 선택
        ticker_symbols = random.choice(list(symbol_pools.values()))[:2]
        trade_symbols = random.choice(list(symbol_pools.values()))[:1]
        orderbook_symbols = random.choice(list(symbol_pools.values()))[:1]
        candle_symbols = random.choice(list(symbol_pools.values()))[:1]

        print(f"라운드 {round_num+1}:")
        print(f"  ticker: {ticker_symbols}")
        print(f"  trade: {trade_symbols}")
        print(f"  orderbook: {orderbook_symbols}")
        print(f"  candle: {candle_symbols}")

        # 모든 타입 동시 구독
        await client.subscribe_ticker(ticker_symbols)
        await client.subscribe_trade(trade_symbols)
        await client.subscribe_orderbook(orderbook_symbols)
        await client.subscribe_candle(candle_symbols)

        # 5초 동작 확인
        await asyncio.sleep(5)

        # 다음 라운드를 위한 구독 해제
        await client.unsubscribe_all()
```

## 📊 성능 기준
```python
CRITERIA = {
    "connection_time": 1.0,        # 연결 < 1초
    "first_message": 1.0,          # 첫메시지 < 1초
    "message_rate": 100,           # 처리속도 > 100 msg/s
    "memory_usage": 200,           # 메모리 < 200MB
    "uptime": 86400,               # 24시간 무중단
    "ticket_efficiency": 60        # 티켓효율 > 60%
}
```

## 🚀 실행 명령어

### 개별 테스트
```powershell
# Public 개별 타입
pytest tests/websocket_v5/public/test_ticker.py -v -s
pytest tests/websocket_v5/public/test_orderbook.py -v

# Private 개별 타입
pytest tests/websocket_v5/private/test_asset.py -v
pytest tests/websocket_v5/private/test_order.py -v

# 조합 테스트
pytest tests/websocket_v5/public/test_mixed_public.py -v
pytest tests/websocket_v5/private/test_mixed_private.py -v

# 구독 관리 테스트
pytest tests/websocket_v5/public/test_subscription_mgmt.py -v
pytest tests/websocket_v5/private/test_subscription_mgmt.py -v
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
async def public_client():
    client = UpbitWebSocketPublicV5()
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
```

## 📋 검증 패턴
```python
# Given-When-Then 패턴
async def test01_single_symbol_single_request(self, client, krw_symbols):
    # Given
    symbol = krw_symbols[0]

    # When
    await client.subscribe_ticker([symbol])
    messages = await client.receive_messages(count=1, timeout=10)

    # Then
    assert len(messages) == 1
    assert messages[0]['code'] == symbol
    assert 'trade_price' in messages[0]
```

---
**v3.0: 간결하고 명확한 테스트 방법론**
