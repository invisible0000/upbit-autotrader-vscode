# 🌍 WebSocket v6 실제 환경 시나리오 가이드

## 📋 **목차**
1. [차트 애플리케이션 시나리오](#chart-application)
2. [자동매매 시스템 시나리오](#trading-system)
3. [마켓 모니터링 시나리오](#market-monitoring)
4. [성능 및 제약사항 분석](#performance-analysis)
5. [실전 팁 및 베스트 프랙티스](#best-practices)

---

## 🖥️ **차트 애플리케이션 시나리오** {#chart-application}

### **시나리오 1: 멀티 차트 뷰어**

#### **요구사항**
- 4개 차트를 동시에 표시 (KRW-BTC, KRW-ETH, KRW-XRP, KRW-ADA)
- 각 차트마다 ticker + orderbook + trade 데이터 필요
- 사용자가 개별 차트의 심볼을 변경 가능

#### **현재 시스템으로 구현 가능한 방법**

##### **방법 1: 차트별 독립 클라이언트 (권장)**
```python
class MultiChartViewer:
    def __init__(self):
        self.charts = {}

    async def create_chart(self, chart_id: str, symbol: str):
        """새 차트 생성"""
        client = WebSocketClient(f"chart_{chart_id}")

        # 복합 구독 (ticker + orderbook + trade)
        await client.subscribe_ticker([symbol], self._on_ticker)
        await client.subscribe_orderbook([symbol], self._on_orderbook)
        await client.subscribe_trade([symbol], self._on_trade)

        self.charts[chart_id] = {
            'client': client,
            'symbol': symbol
        }

    async def change_chart_symbol(self, chart_id: str, new_symbol: str):
        """차트 심볼 변경"""
        if chart_id in self.charts:
            client = self.charts[chart_id]['client']

            # 기존 구독 모두 해제
            await client.cleanup()

            # 새 심볼로 다시 구독
            await client.subscribe_ticker([new_symbol], self._on_ticker)
            await client.subscribe_orderbook([new_symbol], self._on_orderbook)
            await client.subscribe_trade([new_symbol], self._on_trade)

            self.charts[chart_id]['symbol'] = new_symbol

# 사용 예시
viewer = MultiChartViewer()
await viewer.create_chart("chart1", "KRW-BTC")
await viewer.create_chart("chart2", "KRW-ETH")
await viewer.create_chart("chart3", "KRW-XRP")
await viewer.create_chart("chart4", "KRW-ADA")

# 차트1 심볼 변경
await viewer.change_chart_symbol("chart1", "KRW-DOGE")
```

##### **방법 2: 통합 클라이언트 + 심볼 관리**
```python
class UnifiedChartViewer:
    def __init__(self):
        self.client = WebSocketClient("unified_charts")
        self.active_symbols = set()

    async def add_chart(self, symbol: str):
        """차트 추가"""
        self.active_symbols.add(symbol)
        await self._update_subscriptions()

    async def remove_chart(self, symbol: str):
        """차트 제거"""
        self.active_symbols.discard(symbol)
        await self._update_subscriptions()

    async def _update_subscriptions(self):
        """구독 상태 업데이트"""
        symbols = list(self.active_symbols)
        if symbols:
            # 모든 활성 심볼을 한 번에 구독
            await self.client.subscribe_ticker(symbols, self._on_ticker)
            await self.client.subscribe_orderbook(symbols, self._on_orderbook)
            await self.client.subscribe_trade(symbols, self._on_trade)
```

### **시나리오 2: 호가창 + 체결내역 동기화**

#### **요구사항**
- 호가창에서 심볼 변경 시 체결내역도 자동 변경
- 두 위젯 간 완벽한 동기화 필요

#### **구현 방법**
```python
class SyncOrderbookTrade:
    def __init__(self):
        self.current_symbol = "KRW-BTC"
        self.orderbook_client = WebSocketClient("orderbook_widget")
        self.trade_client = WebSocketClient("trade_widget")

    async def change_symbol(self, new_symbol: str):
        """심볼 변경 - 두 위젯 동기화"""
        old_symbol = self.current_symbol
        self.current_symbol = new_symbol

        # 동시 구독 변경
        await asyncio.gather(
            self.orderbook_client.subscribe_orderbook([new_symbol], self._on_orderbook),
            self.trade_client.subscribe_trade([new_symbol], self._on_trade)
        )

        print(f"심볼 변경: {old_symbol} → {new_symbol}")
```

---

## 🤖 **자동매매 시스템 시나리오** {#trading-system}

### **시나리오 3: 실시간 자동매매 봇**

#### **요구사항**
- 20개 심볼 동시 모니터링
- ticker로 가격 변동 감지
- trade로 거래량 급증 감지
- orderbook으로 호가 변화 분석
- Private 데이터로 내 주문/잔고 추적

#### **구현 방법**
```python
class TradingBot:
    def __init__(self):
        # 기능별 클라이언트 분리
        self.market_monitor = WebSocketClient("market_monitor")
        self.trading_engine = WebSocketClient("trading_engine")
        self.account_monitor = WebSocketClient("account_monitor")

        self.target_symbols = [
            "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOT",
            "KRW-LINK", "KRW-LTC", "KRW-BCH", "KRW-EOS", "KRW-TRX",
            "KRW-XLM", "KRW-ATOM", "KRW-NEO", "KRW-VET", "KRW-THETA",
            "KRW-ENJ", "KRW-QTUM", "KRW-BTT", "KRW-IOST", "KRW-CVC"
        ]

    async def start_monitoring(self):
        """모니터링 시작"""
        # 시장 데이터 구독
        await self.market_monitor.subscribe_ticker(
            self.target_symbols,
            self._on_price_change
        )
        await self.market_monitor.subscribe_trade(
            self.target_symbols,
            self._on_volume_spike
        )

        # 거래 관련 구독 (선택된 심볼만)
        await self.trading_engine.subscribe_orderbook(
            ["KRW-BTC", "KRW-ETH"],  # 주요 심볼만
            self._on_orderbook_analysis
        )

        # 계정 모니터링
        await self.account_monitor.subscribe_my_order(self._on_my_order)
        await self.account_monitor.subscribe_my_asset(self._on_balance_change)

    async def _on_price_change(self, event):
        """가격 변동 분석"""
        if abs(event.change_rate) > 0.05:  # 5% 이상 변동
            await self._analyze_trading_opportunity(event.symbol)

    async def _on_volume_spike(self, event):
        """거래량 급증 감지"""
        # 거래량 분석 로직
        pass

    async def add_trading_pair(self, symbol: str):
        """거래 대상 추가"""
        # 기존 구독에 심볼 추가하려면 전체 재구독 필요
        current_orderbook_symbols = ["KRW-BTC", "KRW-ETH"]
        current_orderbook_symbols.append(symbol)

        await self.trading_engine.subscribe_orderbook(
            current_orderbook_symbols,
            self._on_orderbook_analysis
        )
```

### **시나리오 4: 다중 전략 봇**

#### **요구사항**
- 전략별로 독립적인 심볼 그룹 모니터링
- 각 전략마다 다른 데이터 타입 필요
- 전략 추가/제거 시 구독 동적 변경

#### **구현 방법**
```python
class MultiStrategyBot:
    def __init__(self):
        self.strategies = {}

    async def add_strategy(self, strategy_id: str, symbols: List[str], data_types: List[str]):
        """전략 추가"""
        client = WebSocketClient(f"strategy_{strategy_id}")

        # 데이터 타입별 구독
        if "ticker" in data_types:
            await client.subscribe_ticker(symbols, self._create_handler(strategy_id, "ticker"))
        if "orderbook" in data_types:
            await client.subscribe_orderbook(symbols, self._create_handler(strategy_id, "orderbook"))
        if "trade" in data_types:
            await client.subscribe_trade(symbols, self._create_handler(strategy_id, "trade"))

        self.strategies[strategy_id] = {
            'client': client,
            'symbols': symbols,
            'data_types': data_types
        }

    async def remove_strategy(self, strategy_id: str):
        """전략 제거"""
        if strategy_id in self.strategies:
            await self.strategies[strategy_id]['client'].cleanup()
            del self.strategies[strategy_id]

    def _create_handler(self, strategy_id: str, data_type: str):
        """전략별 핸들러 생성"""
        def handler(event):
            print(f"Strategy {strategy_id} received {data_type}: {event.symbol}")
            # 전략별 로직 실행
        return handler

# 사용 예시
bot = MultiStrategyBot()

# 볼린저 밴드 전략 (ticker 필요)
await bot.add_strategy("bollinger", ["KRW-BTC", "KRW-ETH"], ["ticker"])

# 호가 스프레드 전략 (orderbook 필요)
await bot.add_strategy("spread", ["KRW-BTC"], ["orderbook"])

# 거래량 추세 전략 (trade 필요)
await bot.add_strategy("volume", ["KRW-XRP", "KRW-ADA"], ["trade"])
```

---

## 📊 **마켓 모니터링 시나리오** {#market-monitoring}

### **시나리오 5: 전체 마켓 스캐너**

#### **요구사항**
- 전체 KRW 마켓 (200+ 심볼) ticker 구독
- 가격 급등/급락 실시간 알림
- 상위 거래량 코인 추적

#### **구현 방법**
```python
class MarketScanner:
    def __init__(self):
        self.scanner_client = WebSocketClient("market_scanner")
        self.all_krw_symbols = []  # 전체 KRW 심볼 목록

    async def start_full_market_scan(self):
        """전체 마켓 스캔 시작"""
        # 업비트 전체 KRW 마켓 조회 (REST API)
        self.all_krw_symbols = await self._get_all_krw_symbols()

        # 한 번에 모든 심볼 구독
        await self.scanner_client.subscribe_ticker(
            self.all_krw_symbols,
            self._on_market_data
        )

        print(f"마켓 스캐너 시작: {len(self.all_krw_symbols)}개 심볼 모니터링")

    async def _on_market_data(self, event):
        """마켓 데이터 분석"""
        # 5% 이상 급등
        if event.change_rate > 0.05:
            await self._send_pump_alert(event)

        # 5% 이상 급락
        elif event.change_rate < -0.05:
            await self._send_dump_alert(event)

    async def add_volume_monitoring(self, top_n: int = 10):
        """거래량 상위 N개 코인 추가 모니터링"""
        top_symbols = await self._get_top_volume_symbols(top_n)

        # 별도 클라이언트로 거래량 모니터링
        volume_client = WebSocketClient("volume_monitor")
        await volume_client.subscribe_trade(top_symbols, self._on_volume_data)
```

### **시나리오 6: 다중 마켓 모니터링**

#### **요구사항**
- KRW, BTC, USDT 마켓 동시 모니터링
- 마켓간 가격 차이 분석 (김치 프리미엄)
- 아비트라지 기회 탐지

#### **구현 방법**
```python
class MultiMarketMonitor:
    def __init__(self):
        self.krw_client = WebSocketClient("krw_market")
        self.btc_client = WebSocketClient("btc_market")
        self.usdt_client = WebSocketClient("usdt_market")

        self.price_data = {}

    async def start_arbitrage_monitoring(self):
        """아비트라지 모니터링 시작"""
        # 주요 코인들의 마켓별 가격 모니터링
        major_coins = ["BTC", "ETH", "XRP", "ADA"]

        krw_symbols = [f"KRW-{coin}" for coin in major_coins]
        btc_symbols = [f"BTC-{coin}" for coin in major_coins if coin != "BTC"]
        usdt_symbols = [f"USDT-{coin}" for coin in major_coins]

        await asyncio.gather(
            self.krw_client.subscribe_ticker(krw_symbols, self._on_krw_price),
            self.btc_client.subscribe_ticker(btc_symbols, self._on_btc_price),
            self.usdt_client.subscribe_ticker(usdt_symbols, self._on_usdt_price)
        )

    async def _on_krw_price(self, event):
        """KRW 마켓 가격 업데이트"""
        self.price_data[event.symbol] = event.trade_price
        await self._check_arbitrage_opportunity(event.symbol)
```

---

## ⚡ **성능 및 제약사항 분석** {#performance-analysis}

### **WebSocket v6 시스템의 한계**

#### **1. 연결 수 제한**
```python
# ❌ 피해야 할 패턴
for i in range(100):
    client = WebSocketClient(f"client_{i}")  # 100개 클라이언트 생성
    await client.subscribe_ticker(["KRW-BTC"], callback)

# ✅ 권장 패턴
client = WebSocketClient("unified_client")
await client.subscribe_ticker(["KRW-BTC"] * 100, callback)  # 한 클라이언트로 처리
```

#### **2. cleanup() 성능 이슈**
```python
# 측정된 성능: cleanup() = 약 1초
# 빈번한 구독 변경 시 성능 저하 주의

class OptimizedSubscriptionManager:
    def __init__(self):
        self.client = WebSocketClient("optimized")
        self.current_symbols = set()

    async def update_symbols(self, new_symbols: Set[str]):
        """심볼 변경 최적화"""
        if new_symbols == self.current_symbols:
            return  # 변경 없음 - cleanup() 호출 방지

        self.current_symbols = new_symbols
        # 전체 재구독 (cleanup() 없이)
        await self.client.subscribe_ticker(list(new_symbols), self._callback)
```

#### **3. 메모리 사용량**
```python
# 대량 심볼 구독 시 메모리 모니터링
class MemoryEfficientScanner:
    def __init__(self):
        self.max_symbols_per_client = 50  # 클라이언트당 심볼 수 제한

    async def subscribe_large_symbol_list(self, symbols: List[str]):
        """대량 심볼을 청크 단위로 분할 구독"""
        chunks = [symbols[i:i+50] for i in range(0, len(symbols), 50)]

        for i, chunk in enumerate(chunks):
            client = WebSocketClient(f"chunk_{i}")
            await client.subscribe_ticker(chunk, self._callback)
```

### **Rate Limiter 고려사항**

#### **구독 요청 빈도 제한**
```python
class RateLimitAwareClient:
    def __init__(self):
        self.client = WebSocketClient("rate_limited")
        self.last_subscription_time = 0
        self.min_interval = 0.1  # 100ms 간격

    async def safe_subscribe(self, symbols: List[str]):
        """Rate Limit 고려한 안전한 구독"""
        now = time.time()
        elapsed = now - self.last_subscription_time

        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)

        await self.client.subscribe_ticker(symbols, self._callback)
        self.last_subscription_time = time.time()
```

---

## 🎯 **실전 팁 및 베스트 프랙티스** {#best-practices}

### **1. 아키텍처 설계 원칙**

#### **기능별 클라이언트 분리**
```python
# ✅ 권장: 기능별 분리
class TradingApplication:
    def __init__(self):
        self.price_monitor = WebSocketClient("price_monitor")    # 가격 모니터링
        self.order_manager = WebSocketClient("order_manager")    # 주문 관리
        self.risk_manager = WebSocketClient("risk_manager")      # 리스크 관리
        self.ui_updater = WebSocketClient("ui_updater")          # UI 업데이트
```

#### **복합 구독 vs 개별 구독 선택 기준**
```python
# 복합 구독 적합한 경우
if 같은_심볼_여러_데이터타입_필요:
    client = WebSocketClient("composite")
    await client.subscribe_ticker([symbol], ticker_callback)
    await client.subscribe_orderbook([symbol], orderbook_callback)
    await client.subscribe_trade([symbol], trade_callback)

# 개별 구독 적합한 경우
if 독립적_생명주기_관리_필요:
    ticker_client = WebSocketClient("ticker_only")
    orderbook_client = WebSocketClient("orderbook_only")
```

### **2. 에러 처리 및 복구**

#### **연결 끊김 대응**
```python
class ResilientWebSocketClient:
    def __init__(self, client_id: str):
        self.client = WebSocketClient(client_id)
        self.subscriptions = {}  # 구독 상태 백업

    async def subscribe_with_recovery(self, data_type: str, symbols: List[str], callback):
        """복구 가능한 구독"""
        # 구독 상태 백업
        self.subscriptions[data_type] = {
            'symbols': symbols,
            'callback': callback
        }

        try:
            if data_type == "ticker":
                await self.client.subscribe_ticker(symbols, callback)
            elif data_type == "orderbook":
                await self.client.subscribe_orderbook(symbols, callback)

        except Exception as e:
            print(f"구독 실패: {e}")
            await self._schedule_retry(data_type)

    async def _schedule_retry(self, data_type: str):
        """재시도 스케줄링"""
        await asyncio.sleep(5)  # 5초 후 재시도
        sub_info = self.subscriptions[data_type]
        await self.subscribe_with_recovery(data_type, sub_info['symbols'], sub_info['callback'])
```

### **3. 성능 최적화**

#### **배치 처리**
```python
class BatchProcessor:
    def __init__(self):
        self.pending_updates = []
        self.batch_size = 10

    async def process_ticker_event(self, event):
        """티커 이벤트 배치 처리"""
        self.pending_updates.append(event)

        if len(self.pending_updates) >= self.batch_size:
            await self._flush_batch()

    async def _flush_batch(self):
        """배치 업데이트 실행"""
        # UI 업데이트를 배치로 처리하여 성능 향상
        batch = self.pending_updates.copy()
        self.pending_updates.clear()

        for event in batch:
            # UI 업데이트 로직
            pass
```

#### **메모리 관리**
```python
class MemoryManagedClient:
    def __init__(self):
        self.data_cache = {}
        self.max_cache_size = 1000

    async def on_data_received(self, event):
        """메모리 효율적 데이터 처리"""
        # 캐시 크기 제한
        if len(self.data_cache) > self.max_cache_size:
            # 오래된 데이터 제거 (LRU)
            oldest_key = next(iter(self.data_cache))
            del self.data_cache[oldest_key]

        self.data_cache[event.symbol] = event
```

### **4. 모니터링 및 디버깅**

#### **구독 상태 추적**
```python
class SubscriptionTracker:
    def __init__(self):
        self.active_subscriptions = {}
        self.subscription_stats = {
            'total_messages': 0,
            'errors': 0,
            'last_message_time': None
        }

    def track_subscription(self, client_id: str, data_type: str, symbols: List[str]):
        """구독 추적"""
        key = f"{client_id}_{data_type}"
        self.active_subscriptions[key] = {
            'symbols': symbols,
            'created_at': time.time(),
            'message_count': 0
        }

    def on_message_received(self, client_id: str, data_type: str):
        """메시지 수신 추적"""
        key = f"{client_id}_{data_type}"
        if key in self.active_subscriptions:
            self.active_subscriptions[key]['message_count'] += 1

        self.subscription_stats['total_messages'] += 1
        self.subscription_stats['last_message_time'] = time.time()

    def get_health_status(self) -> Dict:
        """시스템 상태 반환"""
        now = time.time()
        last_message = self.subscription_stats['last_message_time']

        return {
            'active_subscriptions': len(self.active_subscriptions),
            'total_messages': self.subscription_stats['total_messages'],
            'seconds_since_last_message': now - last_message if last_message else None,
            'is_healthy': (now - last_message) < 30 if last_message else False
        }
```

---

## 📝 **요약 및 결론**

### **WebSocket v6 시스템으로 가능한 것들**
- ✅ 차트 애플리케이션의 모든 요구사항
- ✅ 실시간 자동매매 시스템 구축
- ✅ 전체 마켓 모니터링 (200+ 심볼)
- ✅ 다중 전략 봇 운영
- ✅ 아비트라지 모니터링
- ✅ Private 데이터 연동

### **주의해야 할 제약사항**
- ⚠️ cleanup() 성능 (약 1초 소요)
- ⚠️ Rate Limiter 고려 필요
- ⚠️ 메모리 사용량 관리
- ⚠️ 개별 구독 해제 불가 (전체 교체만 가능)

### **성공적인 구현을 위한 핵심 원칙**
1. **기능별 클라이언트 분리**로 독립성 확보
2. **복합 구독**으로 효율성 향상
3. **에러 처리 및 복구 메커니즘** 구축
4. **성능 모니터링**으로 시스템 안정성 확보

이 가이드를 통해 WebSocket v6 시스템의 모든 기능을 실제 환경에서 효과적으로 활용하실 수 있을 것입니다! 🚀
