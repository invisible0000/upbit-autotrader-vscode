# 🚀 QAsync 이벤트 기반 실용 가이드

## 📋 빠른 판단 체크리스트

### ✅ QAsync 필요 (즉시 적용)

- [ ] WebSocket 실시간 데이터 처리
- [ ] 100ms 이상 또는 불확정 실행 시간 작업
- [ ] HTTP/API 호출과 UI 반응성 유지 필요
- [ ] 백그라운드 모니터링/스트리밍 작업
- [ ] 외부 네트워크 통신 (재시도/타임아웃 필요)

### ❌ QAsync 불필요 (동기 패턴)

- [ ] 100ms 미만 확정 시간 작업
- [ ] 로컬 파일/메모리만 사용
- [ ] 단순 UI 전환/설정 로딩
- [ ] 즉시 완료되는 계산/변환

---

## 🔧 3단계 QAsync 적용 패턴

### 1단계: @asyncSlot 패턴 적용

```python
from qasync import asyncSlot

class MyWidget(QWidget):
    @asyncSlot()
    async def on_button_clicked(self):
        try:
            self.button.setEnabled(False)
            result = await self.service.process_data()
            self.update_ui(result)
        finally:
            self.button.setEnabled(True)
```

### 2단계: AppKernel TaskManager 활용

```python
from upbit_auto_trading.infrastructure.runtime import get_kernel

async def start_background_task():
    kernel = get_kernel()
    task = kernel.create_task(
        monitor_function(),
        name="monitor_task",
        component="MyService"
    )
    return task
```

### 3단계: LoopGuard 보호 적용

```python
from upbit_auto_trading.infrastructure.runtime import ensure_main_loop

async def api_call(self):
    ensure_main_loop(where="MyService.api_call", component="MyService")
    # 안전한 비동기 작업 수행
```

---

## 📊 계층별 적용 가이드

### Presentation Layer ✅ **필수**

```python
class TradingWidget(QWidget):
    @asyncSlot()
    async def on_execute_trade(self):
        # UI 반응성 유지하며 거래 실행
        result = await self.trading_service.execute()
        self.show_result(result)
```

**패턴**: @asyncSlot + UI 업데이트

### Application Layer ✅ **필수**

```python
class TradingService:
    async def execute_trade(self):
        ensure_main_loop(where="TradingService.execute_trade")
        # 비즈니스 로직 + 외부 API 호출
```

**패턴**: ensure_main_loop + 비동기 서비스 호출

### Infrastructure Layer ✅ **필수**

```python
class WebSocketManager:
    async def connect(self):
        # 실시간 연결 관리
        # TaskManager로 백그라운드 작업 등록
```

**패턴**: TaskManager + 실시간 리소스 관리

### Domain Layer ⚠️ **선택적**

```python
# Domain은 순수 비즈니스 로직만
class TradingRule:
    def validate(self, order: Order) -> bool:
        # 동기 검증 로직
```

**패턴**: 도메인 순수성 유지

---

## 🎯 이벤트 타입별 선택 기준

| 상황 | 패턴 | 예시 |
|------|------|------|
| **UI 이벤트** | `@asyncSlot` | 버튼 클릭, 메뉴 선택 |
| **실시간 데이터** | `WebSocket + Callback` | 시세, 체결 정보 |
| **백그라운드 작업** | `TaskManager` | 모니터링, 주기적 작업 |
| **API 호출** | `async/await + aiohttp` | REST API, 외부 서비스 |

---

## ⚡ 즉시 적용 템플릿

### WebSocket 실시간 데이터 템플릿

```python
from qasync import asyncSlot

class MarketDataWidget(QWidget):
    price_updated = pyqtSignal(str, float)

    def __init__(self):
        super().__init__()
        # 비동기 초기화 지연
        QTimer.singleShot(100, self._init_websocket_async)

    def _init_websocket_async(self):
        asyncio.create_task(self._setup_websocket())

    async def _setup_websocket(self):
        # WebSocket 클라이언트 생성 및 구독
        self.ws_client = await create_websocket_client("MarketData")
        await self.ws_client.subscribe_ticker(["KRW-BTC"], self._on_ticker)

    def _on_ticker(self, event):
        # Qt Signal 발행 (스레드 안전)
        self.price_updated.emit(event.market, event.trade_price)

    def closeEvent(self, event):
        # 정리 작업 TaskManager에 위임
        if self.ws_client:
            kernel = get_kernel()
            kernel.create_task(
                self.ws_client.cleanup(),
                name="websocket_cleanup"
            )
```

### 백그라운드 서비스 템플릿

```python
class MonitorService:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def start(self):
        kernel = get_kernel()
        self._task = kernel.create_task(
            self._monitor_loop(),
            name="monitor_service",
            component="MonitorService"
        )

    async def stop(self):
        self._stop_event.set()
        if self._task:
            await asyncio.wait_for(self._task, timeout=5.0)

    async def _monitor_loop(self):
        while not self._stop_event.is_set():
            try:
                # 모니터링 로직 실행
                await self._check_conditions()

                # 30초 대기 (또는 중지 신호)
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=30.0
                )
            except asyncio.TimeoutError:
                continue  # 정상적인 30초 반복
```

### API 호출 템플릿

```python
class ApiService:
    @asyncSlot()
    async def fetch_data(self, symbol: str):
        ensure_main_loop(where="ApiService.fetch_data")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"/api/ticker/{symbol}") as response:
                    data = await response.json()
                    return data
        except asyncio.TimeoutError:
            self.logger.warning(f"API 호출 타임아웃: {symbol}")
            raise
        except Exception as e:
            self.logger.error(f"API 호출 실패: {e}")
            raise
```

---

## 🔍 문제 해결 가이드

### "RuntimeError: There is no current event loop"

1. **메인 진입점 확인**: qasync.QEventLoop 사용
2. **LoopGuard 활용**: ensure_main_loop() 호출
3. **QTimer 브릿지**: UI에서 비동기 시작시 QTimer.singleShot 사용

### "다중 이벤트 루프 감지"

1. **asyncio.new_event_loop() 제거**: 절대 새 루프 생성 금지
2. **기존 루프 활용**: asyncio.create_task() 사용
3. **AppKernel 통합**: TaskManager로 모든 태스크 관리

### "UI 멈춤 현상"

```python
# ❌ 나쁨: UI 블록킹
def slow_operation(self):
    result = requests.get(url, timeout=30)  # UI 멈춤

# ✅ 좋음: 비동기 처리
@asyncSlot()
async def slow_operation(self):
    async with aiohttp.ClientSession() as session:
        result = await session.get(url)  # UI 반응성 유지
```

### WebSocket 연결 불안정

```python
# 자동 재연결 패턴
async def maintain_connection(self):
    while not self._stop_event.is_set():
        try:
            await self.websocket.connect()
            await self.websocket.listen()
        except ConnectionError:
            self.logger.warning("WebSocket 재연결 시도...")
            await asyncio.sleep(5)  # 5초 후 재시도
```

---

## ⚠️ 피해야 할 안티패턴

### ❌ 동기 컨텍스트에서 비동기 호출

```python
# 나쁨
def ui_callback(self):
    result = asyncio.run(async_function())  # 새 루프 생성!
```

### ❌ Fire-and-Forget 태스크

```python
# 나쁨
asyncio.create_task(background_job())  # 참조 분실

# 좋음
kernel = get_kernel()
task = kernel.create_task(background_job(), name="job")
```

### ❌ 블로킹 호출

```python
# 나쁨
time.sleep(5)  # UI 블록킹
requests.get(url)  # 동기 HTTP

# 좋음
await asyncio.sleep(5)  # 비블로킹
async with aiohttp.ClientSession() as session:
    await session.get(url)  # 비동기 HTTP
```

---

## 🎯 성공 기준

### 코드 품질 지표

- [ ] **단일 이벤트 루프**: LoopGuard 위반 제로
- [ ] **UI 반응성**: 모든 긴 작업 @asyncSlot 적용
- [ ] **안전한 종료**: AppKernel을 통한 리소스 정리
- [ ] **실시간 안정성**: WebSocket 자동 재연결 동작

### 실행 검증

```python
# 정상 작동 확인
python run_desktop_ui.py
# → "QAsync 런타임 초기화 완료" 로그 확인
# → UI 반응성 유지하며 실시간 데이터 수신
# → 종료시 "모든 태스크 정리 완료" 확인
```

---

## 📚 참고 링크

- **상세 가이드**: `docs/QASYNC_EVENT_ARCHITECTURE.md`
- **런타임 구현**: `upbit_auto_trading/infrastructure/runtime/`
- **WebSocket 통합**: `upbit_auto_trading/infrastructure/external_apis/upbit/websocket/`

---

**🏆 핵심 원칙**: "하나의 루프로 모든 것을 처리하라"
