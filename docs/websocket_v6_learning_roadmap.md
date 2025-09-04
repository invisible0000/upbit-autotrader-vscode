# 🚀 WebSocket v6 학습 로드맵

## 📚 **단계별 학습 가이드**

### **🥇 Level 1: 기초 이해 (1-2일)**

#### **1.1 핵심 개념 파악**
- [ ] 📖 [클라이언트 사용 가이드](./websocket_v6_client_usage_guide.md) 읽기
- [ ] 🔧 [개발자 API 레퍼런스](./websocket_v6_developer_api_reference.md) 참조
- [ ] 🌍 [실제 환경 시나리오](./websocket_v6_real_world_scenarios.md) 이해

#### **1.2 기본 실습**
```python
# 실습 1: 기본 구독
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.core.websocket_client import WebSocketClient

async def basic_practice():
    client = WebSocketClient("learning_basic")

    # ticker 구독
    await client.subscribe_ticker(['KRW-BTC'], lambda e: print(f"Price: {e.trade_price}"))

    # 30초 대기 후 정리
    await asyncio.sleep(30)
    await client.cleanup()

# 실행
asyncio.run(basic_practice())
```

**학습 목표:**
- [ ] WebSocketClient 생성 방법 이해
- [ ] 기본 구독 메서드 사용법 숙지
- [ ] 콜백 함수 작성 방법 습득
- [ ] cleanup() 사용법 이해

---

### **🥈 Level 2: 중급 응용 (3-5일)**

#### **2.1 복합 구독 마스터**
```python
async def composite_practice():
    client = WebSocketClient("learning_composite")

    def on_ticker(event):
        print(f"[Ticker] {event.symbol}: {event.trade_price}")

    def on_orderbook(event):
        print(f"[Orderbook] {event.symbol}: {len(event.orderbook_units)} levels")

    def on_trade(event):
        print(f"[Trade] {event.symbol}: {event.trade_volume}")

    # 복합 구독
    await client.subscribe_ticker(['KRW-BTC'], on_ticker)
    await client.subscribe_orderbook(['KRW-BTC'], on_orderbook)
    await client.subscribe_trade(['KRW-BTC'], on_trade)

    await asyncio.sleep(60)
    await client.cleanup()
```

**학습 목표:**
- [ ] 동일 클라이언트 복합 구독 이해
- [ ] 각 데이터 타입별 특성 파악
- [ ] 콜백 함수 분리 설계 패턴 습득

#### **2.2 구독 관리 실습**
```python
async def subscription_management_practice():
    client = WebSocketClient("learning_management")

    # 초기 구독
    print("1. KRW-BTC 구독 시작")
    await client.subscribe_ticker(['KRW-BTC'], lambda e: print(f"BTC: {e.trade_price}"))
    await asyncio.sleep(10)

    # 심볼 변경 (구독 교체)
    print("2. KRW-ETH로 변경")
    await client.subscribe_ticker(['KRW-ETH'], lambda e: print(f"ETH: {e.trade_price}"))
    await asyncio.sleep(10)

    # 다중 심볼 구독
    print("3. 다중 심볼 구독")
    await client.subscribe_ticker(['KRW-BTC', 'KRW-ETH', 'KRW-XRP'],
                                 lambda e: print(f"Multi: {e.symbol} = {e.trade_price}"))
    await asyncio.sleep(20)

    await client.cleanup()
```

**학습 목표:**
- [ ] 구독 교체 vs 누적 이해
- [ ] 다중 심볼 구독 방법 습득
- [ ] 구독 상태 변화 관찰

---

### **🥉 Level 3: 고급 설계 (1주)**

#### **3.1 아키텍처 설계 실습**
```python
class AdvancedTradingApp:
    def __init__(self):
        # 기능별 클라이언트 분리
        self.price_monitor = WebSocketClient("price_monitor")
        self.order_tracker = WebSocketClient("order_tracker")
        self.market_scanner = WebSocketClient("market_scanner")

        # 상태 관리
        self.current_prices = {}
        self.active_orders = {}
        self.alerts = []

    async def start_monitoring(self):
        # 주요 코인 가격 모니터링
        major_symbols = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA']
        await self.price_monitor.subscribe_ticker(major_symbols, self._on_price_update)

        # Private 데이터 모니터링 (API 키 필요)
        await self.order_tracker.subscribe_my_order(self._on_order_update)

        # 전체 마켓 스캔
        all_symbols = await self._get_all_krw_symbols()
        await self.market_scanner.subscribe_ticker(all_symbols, self._on_market_scan)

    def _on_price_update(self, event):
        self.current_prices[event.symbol] = event.trade_price

        # 가격 알림 체크
        if abs(event.change_rate) > 0.05:  # 5% 이상 변동
            self.alerts.append(f"🚨 {event.symbol}: {event.change_rate:.2%} 변동")

    def _on_order_update(self, event):
        self.active_orders[event.uuid] = event
        print(f"주문 업데이트: {event.side} {event.market} {event.state}")

    def _on_market_scan(self, event):
        # 거래량 상위 코인 감지
        if event.acc_trade_price_24h > 1000000000:  # 10억원 이상
            print(f"💰 고거래량 감지: {event.symbol}")

    async def cleanup_all(self):
        await asyncio.gather(
            self.price_monitor.cleanup(),
            self.order_tracker.cleanup(),
            self.market_scanner.cleanup()
        )

# 실습 실행
async def advanced_practice():
    app = AdvancedTradingApp()

    try:
        await app.start_monitoring()
        await asyncio.sleep(300)  # 5분간 실행
    finally:
        await app.cleanup_all()
```

**학습 목표:**
- [ ] 멀티 클라이언트 아키텍처 설계
- [ ] 상태 관리 패턴 구현
- [ ] Private 데이터 연동 (API 키 필요)
- [ ] 에러 처리 및 정리 로직

#### **3.2 성능 최적화 실습**
```python
class OptimizedSubscriptionManager:
    def __init__(self):
        self.client = WebSocketClient("optimized")
        self.current_symbols = set()
        self.update_queue = asyncio.Queue()
        self.batch_processor_task = None

    async def start(self):
        # 배치 처리 태스크 시작
        self.batch_processor_task = asyncio.create_task(self._process_updates())

    async def update_symbols(self, new_symbols: Set[str]):
        """최적화된 심볼 업데이트"""
        if new_symbols == self.current_symbols:
            return  # 불필요한 업데이트 방지

        # 변경 사항만 식별
        added = new_symbols - self.current_symbols
        removed = self.current_symbols - new_symbols

        print(f"심볼 변경: +{len(added)}, -{len(removed)}")

        self.current_symbols = new_symbols

        # 전체 재구독 (현재 시스템 한계)
        if new_symbols:
            await self.client.subscribe_ticker(list(new_symbols), self._on_data)

    async def _on_data(self, event):
        # 논블로킹 큐 처리
        await self.update_queue.put(event)

    async def _process_updates(self):
        """배치 업데이트 처리"""
        batch = []
        while True:
            try:
                # 100ms 대기 또는 10개 배치
                event = await asyncio.wait_for(self.update_queue.get(), timeout=0.1)
                batch.append(event)

                if len(batch) >= 10:
                    await self._flush_batch(batch)
                    batch = []

            except asyncio.TimeoutError:
                if batch:
                    await self._flush_batch(batch)
                    batch = []

    async def _flush_batch(self, events):
        """배치 처리 실행"""
        print(f"배치 처리: {len(events)}개 이벤트")
        # UI 업데이트 등 실제 처리 로직

    async def cleanup(self):
        if self.batch_processor_task:
            self.batch_processor_task.cancel()
        await self.client.cleanup()
```

**학습 목표:**
- [ ] 성능 최적화 기법 습득
- [ ] 배치 처리 패턴 구현
- [ ] 메모리 효율성 고려
- [ ] 비동기 프로그래밍 심화

---

### **🏆 Level 4: 실전 프로젝트 (2주+)**

#### **4.1 미니 프로젝트: 실시간 호가창**
```python
class RealTimeOrderbook:
    """실전 프로젝트: PyQt6 실시간 호가창"""

    def __init__(self):
        self.client = WebSocketClient("realtime_orderbook")
        self.current_symbol = "KRW-BTC"
        self.orderbook_data = None
        self.ui_update_timer = None

    async def start(self):
        # 초기 구독
        await self.client.subscribe_orderbook([self.current_symbol], self._on_orderbook)

        # UI 업데이트 타이머 (60fps)
        self.ui_update_timer = asyncio.create_task(self._ui_update_loop())

    async def change_symbol(self, new_symbol: str):
        """심볼 변경 (호가창 핵심 기능)"""
        if new_symbol != self.current_symbol:
            self.current_symbol = new_symbol

            # 구독 교체
            await self.client.subscribe_orderbook([new_symbol], self._on_orderbook)

            print(f"호가창 심볼 변경: {new_symbol}")

    def _on_orderbook(self, event):
        """호가 데이터 수신"""
        self.orderbook_data = event
        # 실제 구현에서는 UI 갱신 신호 발송

    async def _ui_update_loop(self):
        """60fps UI 업데이트 루프"""
        while True:
            if self.orderbook_data:
                # UI 업데이트 로직
                self._update_orderbook_display()
            await asyncio.sleep(1/60)  # 60fps

    def _update_orderbook_display(self):
        """호가창 UI 업데이트"""
        if not self.orderbook_data:
            return

        print(f"호가 업데이트: {self.current_symbol}")
        # 실제 PyQt6 테이블 업데이트 로직
```

#### **4.2 최종 프로젝트: 멀티 전략 봇**
```python
class MultiStrategyTradingBot:
    """최종 프로젝트: 다중 전략 자동매매 봇"""

    def __init__(self):
        self.strategies = {}
        self.risk_manager = RiskManager()
        self.order_manager = OrderManager()

    async def add_strategy(self, strategy_id: str, config: dict):
        """새 전략 추가"""
        strategy = TradingStrategy(strategy_id, config)

        # 전략별 WebSocket 클라이언트
        client = WebSocketClient(f"strategy_{strategy_id}")

        # 필요한 데이터 구독
        if "ticker" in config["data_sources"]:
            await client.subscribe_ticker(config["symbols"], strategy.on_ticker)
        if "orderbook" in config["data_sources"]:
            await client.subscribe_orderbook(config["symbols"], strategy.on_orderbook)

        self.strategies[strategy_id] = {
            "strategy": strategy,
            "client": client,
            "config": config
        }

    async def remove_strategy(self, strategy_id: str):
        """전략 제거"""
        if strategy_id in self.strategies:
            await self.strategies[strategy_id]["client"].cleanup()
            del self.strategies[strategy_id]

    async def run(self):
        """봇 실행"""
        # 계정 모니터링
        account_client = WebSocketClient("account_monitor")
        await account_client.subscribe_my_order(self._on_order_update)
        await account_client.subscribe_my_asset(self._on_balance_update)

        print(f"봇 시작: {len(self.strategies)}개 전략 활성화")

        # 무한 실행
        try:
            while True:
                await self._check_system_health()
                await asyncio.sleep(60)  # 1분마다 시스템 체크
        except KeyboardInterrupt:
            await self._shutdown()

    async def _shutdown(self):
        """안전한 종료"""
        print("봇 종료 중...")

        # 모든 클라이언트 정리
        cleanup_tasks = []
        for strategy_info in self.strategies.values():
            cleanup_tasks.append(strategy_info["client"].cleanup())

        await asyncio.gather(*cleanup_tasks)
        print("봇 종료 완료")
```

**최종 학습 목표:**
- [ ] 완전한 실전 애플리케이션 구현
- [ ] 에러 처리 및 복구 메커니즘
- [ ] 성능 모니터링 및 최적화
- [ ] 프로덕션 환경 고려 사항

---

## 📋 **학습 체크포인트**

### **Level 1 완료 조건**
- [ ] 기본 구독 코드 작성 가능
- [ ] 콜백 함수 이해 및 활용
- [ ] cleanup() 정상 동작 확인
- [ ] 간단한 가격 모니터링 구현

### **Level 2 완료 조건**
- [ ] 복합 구독 자유자재로 활용
- [ ] 구독 교체 vs 누적 구분 이해
- [ ] 다중 심볼 처리 가능
- [ ] 기본적인 에러 처리 구현

### **Level 3 완료 조건**
- [ ] 멀티 클라이언트 아키텍처 설계
- [ ] Private 데이터 연동 성공
- [ ] 성능 최적화 기법 적용
- [ ] 안정적인 장시간 실행

### **Level 4 완료 조건**
- [ ] 실전 프로젝트 완성
- [ ] 프로덕션 수준 코드 품질
- [ ] 종합적인 시스템 이해
- [ ] 독립적인 개발 능력 확보

---

## 🎯 **추천 학습 순서**

### **1주차 계획**
- **Day 1-2**: Level 1 기초 이해
- **Day 3-4**: Level 2 중급 실습
- **Day 5-7**: Level 3 고급 설계 시작

### **2주차 계획**
- **Day 8-10**: Level 3 고급 설계 완료
- **Day 11-14**: Level 4 실전 프로젝트

### **지속적 개선**
- 코드 리뷰 및 리팩터링
- 성능 모니터링 및 최적화
- 새로운 기능 요구사항 구현
- 커뮤니티 기여 및 지식 공유

---

## 📚 **추가 학습 자료**

### **필수 문서**
1. [WebSocket v6 클라이언트 사용 가이드](./websocket_v6_client_usage_guide.md)
2. [개발자 API 레퍼런스](./websocket_v6_developer_api_reference.md)
3. [실제 환경 시나리오](./websocket_v6_real_world_scenarios.md)
4. [기능 검증 체크리스트](./websocket_v6_feature_verification_checklist.md)

### **실습 환경 설정**
```bash
# 개발 환경 준비
cd d:\projects\upbit-autotrader-vscode

# 테스트 실행
python -m pytest tests/infrastructure/test_external_apis/upbit/test_websocket_v6/ -v

# UI 실행 (전체 시스템 확인)
python run_desktop_ui.py
```

### **커뮤니티 및 지원**
- 프로젝트 GitHub 이슈 트래커 활용
- 코드 리뷰 요청 및 피드백
- 실전 경험 공유 및 토론

이 로드맵을 따라 학습하시면 WebSocket v6 시스템을 완벽하게 마스터하실 수 있습니다! 🚀
