# 📖 WebSocket v6.0 API 사용법 가이드

## 🚀 **빠른 시작**

### 1. **기본 설정 (API 키 없이 Public 기능만)**
```python
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v6 import WebSocketClientProxy

# 즉시 사용 가능 - API 키 불필요
ws = WebSocketClientProxy("my_component", "chart_system")

# Public 기능 확인
if ws.is_public_available():
    print("✅ Public WebSocket 사용 가능")
else:
    print("❌ Public WebSocket 초기화 실패")
```

### 2. **전체 설정 (API 키 포함 Private 기능까지)**
```python
import os
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v6 import GlobalWebSocketManager

# 환경변수에서 API 키 로드 (또는 ApiKeyService 자동 로드)
access_key = os.getenv("UPBIT_ACCESS_KEY")  # None이어도 됨
secret_key = os.getenv("UPBIT_SECRET_KEY")  # None이어도 됨

# 전역 관리자 초기화 (upbit_auth.py와 rate_limiter.py 내부에서 자동 사용)
global_manager = await GlobalWebSocketManager.get_instance()
await global_manager.initialize(access_key, secret_key)

# 이제 모든 컴포넌트에서 Public + Private 기능 사용 가능
ws = WebSocketClientProxy("trading_bot", "automated_system")
print(f"Public: {ws.is_public_available()}, Private: {ws.is_private_available()}")
```

## 🌐 **Public API (API 키 불필요)**

### **현재가 실시간 구독**
```python
async def on_ticker_update(symbol: str, data_type: str, data: dict):
    """현재가 업데이트 콜백"""
    price = data.get('trade_price', 0)
    print(f"{symbol} 현재가: {price:,}원")

# 실시간 현재가 구독
subscription_id = await ws.subscribe_ticker(
    symbols=["KRW-BTC", "KRW-ETH", "KRW-XRP"],
    callback=on_ticker_update
)

print(f"현재가 구독 ID: {subscription_id}")
```

### **호가 실시간 구독**
```python
async def on_orderbook_update(symbol: str, data_type: str, data: dict):
    """호가 업데이트 콜백"""
    orderbook_units = data.get('orderbook_units', [])
    if orderbook_units:
        best_bid = orderbook_units[0]['bid_price']
        best_ask = orderbook_units[0]['ask_price']
        print(f"{symbol} 매수호가: {best_bid:,}, 매도호가: {best_ask:,}")

# 실시간 호가 구독
await ws.subscribe_orderbook(
    symbols=["KRW-BTC"],
    callback=on_orderbook_update
)
```

### **체결내역 실시간 구독**
```python
async def on_trade_update(symbol: str, data_type: str, data: dict):
    """체결 업데이트 콜백"""
    trade_price = data.get('trade_price', 0)
    trade_volume = data.get('trade_volume', 0)
    ask_bid = data.get('ask_bid', 'UNKNOWN')
    print(f"{symbol} 체결: {trade_price:,}원 / {trade_volume} / {ask_bid}")

# 실시간 체결내역 구독
await ws.subscribe_trade(
    symbols=["KRW-BTC", "KRW-ETH"],
    callback=on_trade_update
)
```

### **캔들 실시간 구독**
```python
async def on_candle_update(symbol: str, data_type: str, data: dict):
    """캔들 업데이트 콜백"""
    opening_price = data.get('opening_price', 0)
    high_price = data.get('high_price', 0)
    low_price = data.get('low_price', 0)
    trade_price = data.get('trade_price', 0)
    print(f"{symbol} 캔들 OHLC: {opening_price} / {high_price} / {low_price} / {trade_price}")

# 1분봉 실시간 구독
await ws.subscribe_candle(
    symbols=["KRW-BTC"],
    interval="1m",  # 1s, 1m, 3m, 5m, 10m, 15m, 30m, 60m, 240m
    callback=on_candle_update
)
```

### **스냅샷 데이터 조회 (1회성)**
```python
# 현재가 스냅샷 조회
ticker_snapshot = await ws.get_ticker_snapshot(["KRW-BTC", "KRW-ETH"])
for symbol, data in ticker_snapshot.items():
    print(f"{symbol}: {data['trade_price']:,}원")

# 호가 스냅샷 조회
orderbook_snapshot = await ws.get_orderbook_snapshot(["KRW-BTC"])
for symbol, data in orderbook_snapshot.items():
    units = data['orderbook_units'][0]
    print(f"{symbol} 매수/매도: {units['bid_price']:,} / {units['ask_price']:,}")

# 캔들 스냅샷 조회
candle_snapshot = await ws.get_candle_snapshot(["KRW-BTC"], "1m")
for symbol, data in candle_snapshot.items():
    print(f"{symbol} 1분봉: {data['trade_price']:,}원")
```

## 🔒 **Private API (API 키 필요)**

### **내 주문 실시간 모니터링**
```python
async def on_my_order_update(symbol: str, data_type: str, data: dict):
    """내 주문 상태 변경 콜백"""
    order_uuid = data.get('uuid', 'N/A')
    state = data.get('state', 'N/A')
    side = data.get('side', 'N/A')
    price = data.get('price', 0)
    volume = data.get('volume', 0)

    print(f"주문 업데이트: {order_uuid}")
    print(f"  상태: {state}, 매수/매도: {side}")
    print(f"  가격: {price:,}원, 수량: {volume}")

# Private WebSocket 사용 가능한지 확인
if ws.is_private_available():
    # 내 주문 실시간 구독
    await ws.subscribe_my_orders(callback=on_my_order_update)
    print("✅ 내 주문 실시간 모니터링 시작")
else:
    print("❌ API 키가 없어 Private 기능 사용 불가")
    # REST API 폴링으로 대체
    await start_order_polling_fallback()
```

### **내 자산 실시간 모니터링**
```python
async def on_my_asset_update(symbol: str, data_type: str, data: dict):
    """내 자산 변경 콜백"""
    currency = data.get('currency', 'N/A')
    balance = data.get('balance', '0')
    locked = data.get('locked', '0')
    avg_buy_price = data.get('avg_buy_price', '0')

    print(f"자산 업데이트: {currency}")
    print(f"  보유: {balance}, 주문중: {locked}")
    print(f"  평균매수가: {avg_buy_price}")

# 내 자산 실시간 구독
if ws.is_private_available():
    await ws.subscribe_my_assets(callback=on_my_asset_update)
    print("✅ 내 자산 실시간 모니터링 시작")
```

## 🔧 **고급 사용법**

### **여러 데이터 타입 동시 구독**
```python
class MarketDataCollector:
    def __init__(self):
        self.ws = WebSocketClientProxy("market_collector", "data_analysis")
        self.data_cache = {}

    async def start_comprehensive_monitoring(self, symbols: List[str]):
        """종합 시장 데이터 모니터링 시작"""

        # 현재가 + 호가 + 체결 동시 구독
        await self.ws.subscribe_ticker(symbols, self.on_ticker)
        await self.ws.subscribe_orderbook(symbols, self.on_orderbook)
        await self.ws.subscribe_trade(symbols, self.on_trade)

        # Private 기능 가능하면 추가
        if self.ws.is_private_available():
            await self.ws.subscribe_my_orders(self.on_my_orders)

        print(f"✅ {len(symbols)}개 심볼 종합 모니터링 시작")

    async def on_ticker(self, symbol: str, data_type: str, data: dict):
        """현재가 데이터 저장"""
        self.data_cache[f"{symbol}_ticker"] = data

    async def on_orderbook(self, symbol: str, data_type: str, data: dict):
        """호가 데이터 저장"""
        self.data_cache[f"{symbol}_orderbook"] = data

    async def on_trade(self, symbol: str, data_type: str, data: dict):
        """체결 데이터 저장"""
        self.data_cache[f"{symbol}_trade"] = data

# 사용 예시
collector = MarketDataCollector()
await collector.start_comprehensive_monitoring(["KRW-BTC", "KRW-ETH", "KRW-XRP"])
```

### **조건부 구독 (API 키 상태에 따른 적응형 동작)**
```python
class AdaptiveTrading:
    def __init__(self):
        self.ws = WebSocketClientProxy("adaptive_trader", "trading_system")

    async def initialize_trading(self):
        """API 키 상태에 따른 적응형 초기화"""

        # Public 기능은 항상 활성화
        await self.ws.subscribe_ticker(["KRW-BTC"], self.on_market_signal)
        print("✅ 시장 데이터 모니터링 시작")

        # Private 기능 가능 여부에 따라 분기
        if self.ws.is_private_available():
            # API 키 있음: 실시간 주문 관리
            await self.ws.subscribe_my_orders(self.on_order_update)
            await self.ws.subscribe_my_assets(self.on_asset_update)
            print("✅ 실시간 주문/자산 관리 활성화")
            self.trading_mode = "realtime"
        else:
            # API 키 없음: 시뮬레이션 모드
            print("⚠️ API 키 없음 - 시뮬레이션 모드로 전환")
            self.trading_mode = "simulation"

    async def on_market_signal(self, symbol: str, data_type: str, data: dict):
        """시장 신호 분석 (항상 동작)"""
        price = data.get('trade_price', 0)

        if self.should_buy(price):
            if self.trading_mode == "realtime":
                await self.place_real_order(symbol, price)
            else:
                await self.simulate_order(symbol, price)

    async def place_real_order(self, symbol: str, price: float):
        """실제 주문 (Private 기능)"""
        print(f"💰 실제 주문: {symbol} @ {price:,}원")
        # REST API로 실제 주문 실행

    async def simulate_order(self, symbol: str, price: float):
        """시뮬레이션 주문 (API 키 없을 때)"""
        print(f"📊 시뮬레이션 주문: {symbol} @ {price:,}원")
        # 로컬 시뮬레이션
```

### **에러 처리 및 복구**
```python
class RobustWebSocketClient:
    def __init__(self):
        self.ws = WebSocketClientProxy("robust_client", "production_system")
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

    async def start_with_error_handling(self):
        """견고한 에러 처리가 포함된 시작"""
        try:
            await self.ws.subscribe_ticker(["KRW-BTC"], self.on_data)
            print("✅ WebSocket 구독 성공")
        except Exception as e:
            print(f"❌ 초기 구독 실패: {e}")
            await self.handle_connection_error()

    async def on_data(self, symbol: str, data_type: str, data: dict):
        """데이터 수신 처리 (에러 격리)"""
        try:
            # 실제 비즈니스 로직
            await self.process_market_data(data)
        except Exception as e:
            print(f"⚠️ 데이터 처리 오류 (계속 진행): {e}")
            # 개별 데이터 처리 오류는 전체 시스템에 영향 없음

    async def handle_connection_error(self):
        """연결 오류 시 자동 복구"""
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            delay = min(2 ** self.reconnect_attempts, 60)  # 지수 백오프

            print(f"🔄 {delay}초 후 재연결 시도 ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            await asyncio.sleep(delay)

            try:
                await self.start_with_error_handling()
                self.reconnect_attempts = 0  # 성공 시 리셋
            except Exception:
                await self.handle_connection_error()  # 재귀 재시도
        else:
            print("❌ 최대 재연결 시도 횟수 초과")
            # 알림 발송, 관리자 통지 등
```

## 🔍 **구독 관리 및 해제**

### **구독 상태 확인**
```python
# 현재 활성 구독 목록 조회
active_subscriptions = await ws.get_active_subscriptions()
print(f"활성 구독: {len(active_subscriptions)}개")

for sub_id, info in active_subscriptions.items():
    print(f"  {sub_id}: {info['data_type']} - {info['symbols']}")

# 특정 구독 상태 확인
subscription_info = await ws.get_subscription_info("ticker_20250901_001")
if subscription_info:
    print(f"구독 상태: {subscription_info['status']}")
    print(f"구독 심볼: {subscription_info['symbols']}")
```

### **선택적 구독 해제**
```python
# 특정 구독만 해제
subscription_id = await ws.subscribe_ticker(["KRW-BTC"], callback)
await asyncio.sleep(10)  # 10초 후
await ws.unsubscribe(subscription_id)
print("✅ 특정 구독 해제 완료")

# 특정 심볼만 제거
await ws.unsubscribe_symbols("ticker", ["KRW-BTC"])  # KRW-BTC만 해제
print("✅ KRW-BTC 현재가 구독 해제")

# 모든 구독 해제
await ws.unsubscribe_all()
print("✅ 모든 구독 해제 완료")
```

### **자동 정리 (권장)**
```python
# with 문 사용으로 자동 정리
async with WebSocketClientProxy("temp_client") as ws:
    await ws.subscribe_ticker(["KRW-BTC"], callback)
    await asyncio.sleep(60)  # 1분간 실행
    # with 블록 종료 시 자동으로 모든 구독 해제

# 또는 WeakRef 기반 자동 정리 (객체 소멸 시)
def create_temporary_monitor():
    ws = WebSocketClientProxy("temp_monitor")
    # ... 구독 설정
    return ws

monitor = create_temporary_monitor()
# monitor = None  # 객체 소멸 시 자동으로 구독 해제됨
```

## 📊 **상태 모니터링 및 디버깅**

### **연결 상태 확인**
```python
# 전체 시스템 상태 확인
system_status = await ws.get_system_status()
print(f"시스템 상태: {system_status['overall_status']}")
print(f"Public 연결: {system_status['public_connection']}")
print(f"Private 연결: {system_status['private_connection']}")
print(f"활성 구독: {system_status['active_subscriptions']}")

# 헬스체크
health = await ws.health_check()
print(f"건강도: {health['health_score']}/100")
print(f"업타임: {health['uptime_minutes']}분")
```

### **성능 메트릭**
```python
# 성능 지표 조회
metrics = await ws.get_performance_metrics()
print(f"초당 메시지 수: {metrics['messages_per_second']}")
print(f"평균 지연시간: {metrics['average_latency_ms']}ms")
print(f"에러율: {metrics['error_rate_percent']}%")
print(f"메모리 사용량: {metrics['memory_usage_mb']}MB")
```

## ⚠️ **주의사항 및 모범 사례**

### **DO - 권장사항**
```python
# ✅ 콜백에서 예외 처리
async def safe_callback(symbol: str, data_type: str, data: dict):
    try:
        await process_data(data)
    except Exception as e:
        logger.error(f"데이터 처리 오류: {e}")

# ✅ 적절한 client_id 사용
ws = WebSocketClientProxy("chart_btc_1min", "chart_module")

# ✅ 구독 전 상태 확인
if ws.is_public_available():
    await ws.subscribe_ticker(symbols, callback)

# ✅ 자원 정리
await ws.cleanup_on_shutdown()
```

### **DON'T - 피해야 할 사항**
```python
# ❌ 콜백에서 블로킹 작업
async def bad_callback(symbol: str, data_type: str, data: dict):
    time.sleep(1)  # 절대 금지!
    requests.get("http://api.com")  # 동기 HTTP 요청 금지!

# ❌ 동일한 client_id 재사용
ws1 = WebSocketClientProxy("same_id", "module1")
ws2 = WebSocketClientProxy("same_id", "module2")  # 충돌 위험!

# ❌ 예외 처리 없는 콜백
async def unsafe_callback(symbol: str, data_type: str, data: dict):
    result = data['some_key']  # KeyError 발생 가능!
    await risky_operation(result)  # 예외 처리 없음!
```

---

**Happy Trading! 🚀📈**
