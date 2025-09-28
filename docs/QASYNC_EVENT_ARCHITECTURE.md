# 🔄 QAsync 통합 이벤트 기반 아키텍처 가이드

## 🎯 개요

본 문서는 업비트 자동매매 시스템에서 구축한 QAsync 통합 이벤트 기반 아키텍처에 대한 종합적인 가이드입니다. PyQt6와 asyncio의 완벽한 통합, 단일 이벤트 루프 관리, 그리고 안전한 비동기 처리 패턴을 제시합니다.

---

## 1. QAsync 이벤트 기반 시스템이란? 📡

### 1.1 비개발자를 위한 간단한 설명

QAsync 시스템을 **"스마트 지휘센터"** 로 생각해보세요.

**🏭 기존 방식 (문제점)**:

- 여러 공장(이벤트 루프)이 각자 일정을 따로 관리
- A공장에서 B공장에 부품을 요청하면 일정 충돌 발생
- 각 공장마다 다른 시계를 사용해서 협업 불가능
- **문제**: 공장들 간의 소통이 어려워 전체 시스템이 불안정

**✨ QAsync 통합 방식**:

- 하나의 마스터 지휘센터가 모든 일정을 통합 관리
- 모든 공장이 같은 시계와 일정표를 공유
- UI 이벤트와 백그라운드 작업이 완벽히 조율됨
- **장점**: 전체 시스템이 하나의 리듬으로 움직여 안정적

### 1.2 기술적 개요

QAsync는 **PyQt의 이벤트 루프와 asyncio의 이벤트 루프를 단일화**하는 Python 라이브러리입니다.

**핵심 아키텍처**:

- **AppKernel**: 중앙 런타임 관리자, 모든 비동기 리소스 생명주기 관리
- **LoopGuard**: 이벤트 루프 위반 실시간 감지 및 보호
- **TaskManager**: 백그라운드 태스크 안전한 생성/정리
- **WebSocket Integration**: 실시간 데이터 스트리밍과 UI 완벽 통합

**해결하는 문제들**:

- RuntimeError: There is no current event loop
- 다중 이벤트 루프 충돌
- WebSocket 연결과 UI 업데이트 동기화
- 애플리케이션 종료시 리소스 정리

---

## 2. 이벤트 기반 패턴 비교 🔄

### 2.1 QAsync 통합 패턴 🏆 **채택**

```python
# 메인 진입점
import qasync

app = qasync.QApplication(sys.argv)
loop = qasync.QEventLoop(app)

with loop:
    kernel = AppKernel.bootstrap(app)
    return loop.run_until_complete(main_async())
```

**장점**:

- PyQt와 asyncio 완벽 통합
- 단일 이벤트 루프 보장
- 자동 리소스 정리

### 2.2 스레드 기반 패턴 ❌ **회피**

```python
# 안티패턴
def ui_callback():
    loop = asyncio.new_event_loop()  # 위험!
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_task())
```

**문제점**:

- 다중 이벤트 루프 생성
- 스레드 간 동기화 복잡성
- 리소스 누수 가능성

### 2.3 QTimer 브릿지 패턴 ✅ **허용**

```python
from PyQt6.QtCore import QTimer

def bridge_to_async():
    def callback():
        # 기존 루프에서 태스크 생성
        asyncio.create_task(async_handler())

    QTimer.singleShot(100, callback)
```

**용도**: UI 이벤트에서 비동기 작업 시작

### 2.4 @asyncSlot 패턴 🎯 **표준**

```python
from qasync import asyncSlot

class Widget(QWidget):
    @asyncSlot()
    async def on_button_clicked(self):
        # 직접 비동기 처리 가능
        result = await self.service.process_data()
        self.update_ui(result)
```

**장점**:

- Qt 시그널과 asyncio 직접 연결
- 예외 처리 자동화
- 코드 간소화

---

## 3. 우리의 QAsync 아키텍처 구축 개요 🏗️

### 3.1 핵심 구성 요소

#### AppKernel - 런타임 중앙 관리자

- 📁 `upbit_auto_trading/infrastructure/runtime/app_kernel.py`
- QAsync 통합 런타임 커널
- 모든 비동기 리소스 생명주기 관리

#### LoopGuard - 이벤트 루프 보호자

- 📁 `upbit_auto_trading/infrastructure/runtime/loop_guard.py`
- 다중 루프 위반 실시간 감지
- 개발 시점 즉시 에러 발생으로 회귀 방지

#### WebSocketManager - 실시간 데이터 허브

- 📁 `upbit_auto_trading/infrastructure/external_apis/upbit/websocket/core/websocket_manager.py`
- 싱글톤 패턴 WebSocket 연결 관리
- Event 기반 연결 모니터링

#### WebSocketApplicationService - 애플리케이션 추상화

- 📁 `upbit_auto_trading/application/services/websocket_application_service.py`
- Application Layer WebSocket 추상화
- 비즈니스 로직과 Infrastructure 분리

### 3.2 아키텍처 흐름도

```mermaid
graph TB
    subgraph "QAsync Runtime"
        A[QApplication] --> B[QEventLoop]
        B --> C[AppKernel]
    end

    subgraph "Event Management"
        C --> D[TaskManager]
        C --> E[LoopGuard]
        D --> F[Background Tasks]
    end

    subgraph "Infrastructure Layer"
        G[WebSocketManager] --> H[Connection Pool]
        G --> I[Rate Limiter]
        G --> J[Event Broadcaster]
    end

    subgraph "Application Layer"
        K[WebSocketApplicationService] --> G
        L[TradingApplicationService] --> K
    end

    subgraph "Presentation Layer"
        M[MainWindow] --> L
        N[@asyncSlot Methods] --> K
        O[UI Components] --> N
    end

    E -.->|Guards| F
    E -.->|Guards| G
    E -.->|Guards| K

    J -->|Events| K
    K -->|Signals| N
```

### 3.3 실행 흐름

1. **QApplication + QEventLoop 생성** (단일 통합 루프)
2. **AppKernel 부트스트랩** (TaskManager, LoopGuard 초기화)
3. **WebSocketManager 싱글톤 생성** (Infrastructure Layer)
4. **ApplicationServices 등록** (DI Container 통합)
5. **MainWindow @asyncSlot 연결** (UI-Async 브릿지)
6. **실시간 이벤트 스트리밍 시작**

---

## 4. 이벤트 기반 패턴이 필요한 상황과 구분 가이드 🎯

### 4.1 QAsync 패턴 필수 적용 대상 ✅

#### WebSocket 실시간 통신

```python
class WebSocketService:
    @asyncSlot()
    async def on_data_received(self, data):
        # UI 업데이트가 필요한 실시간 데이터
        await self.process_market_data(data)
        self.data_updated.emit(data)  # Qt Signal
```

**이유**: WebSocket 데이터와 UI 업데이트 동기화 필요

#### 장기 실행 백그라운드 작업

```python
async def start_trading_monitor():
    kernel = get_kernel()
    task = kernel.create_task(
        monitor_trading_positions(),
        name="trading_monitor",
        component="TradingEngine"
    )
    return task
```

**이유**: 메인 UI를 블록하지 않는 백그라운드 처리

#### API 호출과 UI 반응성

```python
class TradingWidget(QWidget):
    @asyncSlot()
    async def on_buy_button_clicked(self):
        self.buy_button.setEnabled(False)
        try:
            result = await self.trading_service.execute_buy_order()
            self.show_success_message(result)
        finally:
            self.buy_button.setEnabled(True)
```

**이유**: API 지연시에도 UI 반응성 유지

### 4.2 일반 동기 패턴으로 충분한 경우 ❌

#### 단순 계산 및 UI 업데이트

```python
def calculate_profit(self, price: float, quantity: float) -> float:
    profit = (price * quantity) - self.base_cost
    self.profit_label.setText(f"수익: {profit:,.0f}원")
    return profit
```

**이유**: 즉시 완료되는 작업, 비동기화 불필요

#### 설정 파일 로딩

```python
def load_config(self) -> dict:
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)
```

**이유**: 애플리케이션 시작시 한 번만 실행

#### 단순 이벤트 처리

```python
def on_menu_clicked(self):
    self.stacked_widget.setCurrentWidget(self.settings_page)
```

**이유**: 동기적 UI 전환

### 4.3 판별 기준

| 기준 | QAsync 필요 | 동기 패턴 충분 |
|------|-------------|---------------|
| **실행 시간** | 100ms 이상 또는 불확정 | 100ms 미만 확정 |
| **UI 블록킹** | UI 반응성 유지 필요 | 즉시 완료 |
| **외부 네트워크** | HTTP/WebSocket 통신 | 로컬 파일/메모리만 |
| **실시간성** | 스트리밍 데이터 처리 | 일회성 처리 |
| **에러 복잡도** | 재시도/타임아웃 필요 | 단순 예외 처리 |

---

## 5. QAsync 작업 체크포인트와 체크리스트 ✅

### 5.1 설계 단계 체크포인트

#### Phase 1: 이벤트 루프 통합

- [ ] **QApplication 생성 시점 확인**: 모든 초기화보다 먼저
- [ ] **단일 이벤트 루프 보장**: qasync.QEventLoop 단독 사용
- [ ] **AppKernel 부트스트랩**: 런타임 리소스 중앙 관리
- [ ] **LoopGuard 활성화**: 다중 루프 위반 감지

#### Phase 2: 비동기 서비스 통합

- [ ] **WebSocket 서비스 단일화**: WebSocketManager 싱글톤
- [ ] **TaskManager 등록**: 모든 백그라운드 작업 추적
- [ ] **Rate Limiter 통합**: API 호출 제한 중앙 관리
- [ ] **이벤트 브로드캐스터**: Infrastructure → Application 이벤트 전파

### 5.2 구현 단계 체크리스트

#### @asyncSlot 패턴 적용

```python
# ✅ 올바른 패턴
class TradingWidget(QWidget):
    @asyncSlot()
    async def on_execute_trade(self):
        try:
            # 비동기 서비스 호출
            result = await self.trading_service.execute_trade()
            # UI 업데이트 (메인 스레드에서 안전)
            self.update_result(result)
        except Exception as e:
            self.show_error(str(e))

# ❌ 잘못된 패턴
class TradingWidget(QWidget):
    def on_execute_trade(self):
        # 동기 컨텍스트에서 비동기 호출 시도
        result = asyncio.run(self.trading_service.execute_trade())  # 위험!
```

- [ ] **@asyncSlot 데코레이터 추가**
- [ ] **await 키워드 사용**: 비동기 서비스 호출
- [ ] **예외 처리**: try-except-finally 패턴
- [ ] **UI 업데이트**: 메인 스레드에서 안전한 업데이트

#### AppKernel TaskManager 활용

```python
# TaskManager를 통한 안전한 태스크 생성
async def start_monitoring():
    kernel = get_kernel()
    task = kernel.create_task(
        monitor_websocket_health(),
        name="websocket_monitor",
        component="WebSocketService"
    )
    return task
```

- [ ] **TaskManager 사용**: 직접 create_task 금지
- [ ] **태스크 이름 지정**: 디버깅 및 관리 용이성
- [ ] **컴포넌트 명시**: 소속 모듈 표시
- [ ] **태스크 참조 보관**: Weak Reference 방지

#### LoopGuard 보호 패턴

```python
from upbit_auto_trading.infrastructure.runtime import ensure_main_loop

class UpbitApiClient:
    async def make_request(self, endpoint: str):
        # 루프 검증 (개발시 위반 즉시 감지)
        ensure_main_loop(
            where="UpbitApiClient.make_request",
            component="UpbitAPI"
        )

        async with self.session.get(endpoint) as response:
            return await response.json()
```

- [ ] **ensure_main_loop 호출**: 모든 비동기 메서드 진입시
- [ ] **위치 정보 명시**: 디버깅 추적성
- [ ] **컴포넌트 정보**: 위반 발생시 책임 추적
- [ ] **예외 전파**: 위반시 즉시 RuntimeError 발생

### 5.3 테스트 단계 검증

#### QAsync 테스트 환경

```python
# tests/conftest.py
import pytest
import qasync

@pytest.fixture(scope="session")
def qasync_app():
    app = qasync.QApplication([])
    yield app
    app.quit()

@pytest.fixture
def qasync_loop(qasync_app):
    loop = qasync.QEventLoop(qasync_app)
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
```

- [ ] **QAsync 테스트 환경**: 프로덕션과 동일한 루프
- [ ] **Fixture 격리**: 테스트간 상태 독립성
- [ ] **AppKernel 테스트**: 부트스트랩 및 종료 검증
- [ ] **WebSocket Mock**: 실시간 데이터 시뮬레이션

### 5.4 배포 단계 체크리스트

- [ ] **이벤트 루프 위반 제로**: LoopGuard 위반 기록 없음
- [ ] **WebSocket 연결 안정성**: 재연결 로직 검증
- [ ] **메모리 누수 방지**: 태스크 정리 완료 확인
- [ ] **Graceful Shutdown**: 모든 리소스 안전한 해제
- [ ] **성능 모니터링**: 이벤트 루프 지연시간 측정

---

## 6. QAsync 이벤트 패턴 가이드 📋

### 6.1 표준 패턴 템플릿

#### WebSocket 실시간 데이터 처리

```python
from qasync import asyncSlot
from upbit_auto_trading.infrastructure.runtime import get_kernel

class MarketDataWidget(QWidget):
    # Qt 시그널 정의
    price_updated = pyqtSignal(str, float)  # symbol, price

    def __init__(self):
        super().__init__()
        self.websocket_client = None
        self._setup_ui()

        # 비동기 초기화 (UI 로드 후)
        QTimer.singleShot(100, self._initialize_websocket_async)

    def _initialize_websocket_async(self):
        """WebSocket 비동기 초기화"""
        def start_init():
            try:
                asyncio.create_task(self._setup_websocket())
            except RuntimeError:
                QTimer.singleShot(100, start_init)  # 재시도
        start_init()

    async def _setup_websocket(self):
        """WebSocket 연결 설정"""
        kernel = get_kernel()

        # WebSocket 클라이언트 생성
        from upbit_auto_trading.infrastructure.external_apis.upbit.websocket import create_websocket_client
        self.websocket_client = create_websocket_client("MarketDataWidget")

        # 실시간 데이터 구독
        await self.websocket_client.subscribe_ticker(
            symbols=["KRW-BTC", "KRW-ETH"],
            callback=self._on_ticker_received
        )

    @asyncSlot()
    async def on_subscribe_button_clicked(self):
        """구독 버튼 클릭 시 처리"""
        symbol = self.symbol_input.text()

        if not symbol:
            self._show_warning("심볼을 입력하세요")
            return

        try:
            self.subscribe_button.setEnabled(False)

            success = await self.websocket_client.subscribe_ticker(
                symbols=[symbol],
                callback=self._on_ticker_received
            )

            if success:
                self._show_info(f"{symbol} 구독 완료")
            else:
                self._show_error(f"{symbol} 구독 실패")

        except Exception as e:
            self._show_error(f"구독 오류: {e}")
        finally:
            self.subscribe_button.setEnabled(True)

    def _on_ticker_received(self, ticker_event):
        """실시간 시세 데이터 수신 (콜백)"""
        symbol = ticker_event.market
        price = float(ticker_event.trade_price)

        # Qt Signal 발행 (스레드 안전)
        self.price_updated.emit(symbol, price)

    def closeEvent(self, event):
        """위젯 종료시 정리"""
        if self.websocket_client:
            # 비동기 정리를 TaskManager에 위임
            kernel = get_kernel()
            kernel.create_task(
                self.websocket_client.cleanup(),
                name="websocket_cleanup",
                component="MarketDataWidget"
            )
        event.accept()
```

#### 백그라운드 서비스 패턴

```python
from upbit_auto_trading.infrastructure.runtime import get_kernel, ensure_main_loop

class TradingMonitorService:
    def __init__(self):
        self.logger = create_component_logger("TradingMonitor")
        self._monitoring_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def start_monitoring(self):
        """거래 모니터링 시작"""
        ensure_main_loop(where="TradingMonitorService.start_monitoring")

        if self._monitoring_task and not self._monitoring_task.done():
            self.logger.warning("모니터링이 이미 실행 중입니다")
            return

        # AppKernel을 통한 안전한 태스크 생성
        kernel = get_kernel()
        self._monitoring_task = kernel.create_task(
            self._monitor_loop(),
            name="trading_monitor",
            component="TradingMonitorService"
        )

        self.logger.info("거래 모니터링 시작됨")

    async def stop_monitoring(self):
        """거래 모니터링 중지"""
        if self._monitoring_task:
            self._stop_event.set()
            try:
                await asyncio.wait_for(self._monitoring_task, timeout=5.0)
                self.logger.info("거래 모니터링 정상 중지")
            except asyncio.TimeoutError:
                self._monitoring_task.cancel()
                self.logger.warning("거래 모니터링 강제 중지")

    async def _monitor_loop(self):
        """실제 모니터링 루프"""
        while not self._stop_event.is_set():
            try:
                # 포지션 확인 및 처리
                positions = await self.trading_service.get_positions()
                await self._check_stop_loss(positions)
                await self._check_take_profit(positions)

                # Event 기반 대기 (30초 또는 중지 신호)
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=30.0
                )

            except asyncio.TimeoutError:
                continue  # 30초마다 반복
            except Exception as e:
                self.logger.error(f"모니터링 오류: {e}")
                await asyncio.sleep(5.0)  # 오류시 5초 대기
```

#### Application Service 통합 패턴

```python
class WebSocketApplicationService:
    def __init__(self):
        self.logger = create_component_logger("WebSocketApplicationService")
        self._manager: Optional[WebSocketManager] = None
        self._clients: Dict[str, WebSocketClient] = {}

    async def initialize(self) -> bool:
        """서비스 초기화"""
        ensure_main_loop(where="WebSocketApplicationService.initialize")

        try:
            # Infrastructure WebSocketManager 초기화
            from .core.websocket_manager import get_websocket_manager
            self._manager = await get_websocket_manager()

            self.logger.info("WebSocket Application Service 초기화 완료")
            return True

        except Exception as e:
            self.logger.error(f"WebSocket 서비스 초기화 실패: {e}")
            return False

    async def create_client(self, component_id: str) -> Optional[WebSocketClient]:
        """컴포넌트별 WebSocket 클라이언트 생성"""
        if not self._manager:
            await self.initialize()

        if component_id in self._clients:
            return self._clients[component_id]

        try:
            from .core.websocket_client import WebSocketClient
            client = WebSocketClient(component_id)
            self._clients[component_id] = client

            self.logger.info(f"WebSocket 클라이언트 생성: {component_id}")
            return client

        except Exception as e:
            self.logger.error(f"클라이언트 생성 실패: {e}")
            return None
```

### 6.2 통합 이벤트 시스템 패턴

#### Infrastructure → Application → Presentation 이벤트 흐름

```python
# Infrastructure Layer (이벤트 발행)
class WebSocketManager:
    async def _broadcast_event_to_components(self, event: BaseWebSocketEvent):
        """등록된 모든 컴포넌트에게 이벤트 브로드캐스트"""
        for client_id, callback in self._event_callbacks.items():
            try:
                # 콜백이 코루틴인지 확인
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                self.logger.warning(f"이벤트 브로드캐스트 실패 ({client_id}): {e}")

# Application Layer (이벤트 변환)
class WebSocketApplicationService:
    async def _handle_infrastructure_event(self, event: BaseWebSocketEvent):
        """Infrastructure 이벤트를 Application 이벤트로 변환"""
        if isinstance(event, TickerEvent):
            # 비즈니스 로직 적용
            processed_data = await self._process_ticker_data(event)

            # Application 이벤트 발행
            app_event = MarketDataUpdateEvent(
                symbol=event.market,
                price=processed_data.price,
                change_rate=processed_data.change_rate
            )
            await self._publish_application_event(app_event)

# Presentation Layer (이벤트 수신)
class PriceDisplayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._connect_to_application_events()

    def _connect_to_application_events(self):
        """Application Layer 이벤트 구독"""
        from upbit_auto_trading.application.events import get_event_bus
        event_bus = get_event_bus()

        # 이벤트 구독 (Qt Signal로 브릿지)
        event_bus.subscribe(
            MarketDataUpdateEvent,
            self._on_market_data_updated
        )

    @asyncSlot()
    async def _on_market_data_updated(self, event: MarketDataUpdateEvent):
        """실시간 시세 업데이트"""
        # 메인 스레드에서 UI 업데이트
        self.price_label.setText(f"{event.price:,.0f}원")
        self.change_label.setText(f"{event.change_rate:+.2f}%")

        # 색상 업데이트 (상승/하락)
        color = "red" if event.change_rate > 0 else "blue"
        self.price_label.setStyleSheet(f"color: {color}")
```

### 6.3 안전한 리소스 정리 패턴

#### AppKernel Shutdown 통합

```python
class QAsyncApplication:
    async def shutdown(self) -> None:
        """애플리케이션 종료 및 정리"""
        logger.info("🧹 애플리케이션 종료 시퀀스 시작...")

        try:
            # 1. UI 윈도우 정리
            if self.main_window:
                self.main_window.close()

            # 2. Application Services 정리
            if self.app_context:
                await self.app_context.shutdown()

            # 3. AppKernel 종료 (모든 태스크 자동 정리)
            if self.kernel:
                await self.kernel.shutdown()

            # 4. QApplication 정리
            if self.qapp:
                self.qapp.quit()

            logger.info("🏆 애플리케이션 완전 종료")

        except Exception as e:
            logger.error(f"❌ 종료 시퀀스 오류: {e}")
```

#### WebSocket 연결 정리

```python
class WebSocketClient:
    async def cleanup(self):
        """클라이언트 정리"""
        try:
            # 구독 해제
            await self.unsubscribe_all()

            # 매니저에서 클라이언트 제거
            if self._manager:
                await self._manager.remove_client(self._component_id)

            self.logger.info(f"WebSocket 클라이언트 정리 완료: {self._component_id}")

        except Exception as e:
            self.logger.error(f"클라이언트 정리 오류: {e}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 종료시 자동 정리"""
        await self.cleanup()
```

---

## 7. 전문가 마무리 조언 🎓

### 7.1 QAsync 아키텍처 성공 요인

#### "단일 루프 원칙" 철저 준수

- **QAsync QEventLoop 하나만 사용**: 절대 예외 없음
- **LoopGuard 활용**: 개발시 위반 즉시 감지
- **AppKernel 중심 설계**: 모든 리소스 생명주기 중앙 관리

#### "이벤트 기반 설계" 사고

- Infrastructure → Application → Presentation 단방향 이벤트 흐름
- Qt Signal과 asyncio 이벤트의 명확한 역할 분리
- 컴포넌트 간 느슨한 결합 유지

#### "안전한 비동기 패턴" 습관

- @asyncSlot로 UI-Async 브릿지
- TaskManager로 백그라운드 작업 관리
- Graceful Shutdown으로 리소스 정리

### 7.2 주요 안티패턴 회피

#### 다중 이벤트 루프 생성 금지

```python
# ❌ 절대 금지
def ui_callback():
    loop = asyncio.new_event_loop()  # 위험!
    loop.run_until_complete(async_task())

# ✅ 올바른 방법
@asyncSlot()
async def ui_callback(self):
    await async_task()  # 기존 루프 활용
```

#### 블로킹 호출 회피

```python
# ❌ UI 블록킹
def slow_operation(self):
    result = requests.get(url)  # UI 멈춤
    self.update_ui(result)

# ✅ 비동기 처리
@asyncSlot()
async def slow_operation(self):
    async with aiohttp.ClientSession() as session:
        result = await session.get(url)  # UI 반응성 유지
        self.update_ui(result)
```

#### Fire-and-Forget 태스크 금지

```python
# ❌ 참조 분실 위험
asyncio.create_task(background_job())  # Weak Reference

# ✅ TaskManager 관리
kernel = get_kernel()
task = kernel.create_task(
    background_job(),
    name="background_job",
    component="MyService"
)
```

### 7.3 성능 최적화 가이드

#### 비동기 I/O 최적화

- **Connection Pooling**: aiohttp Session 재사용
- **Batch Processing**: 여러 API 요청 동시 처리
- **Lazy Initialization**: 필요시점에 리소스 생성

#### 메모리 관리

- **Weak References**: 순환 참조 방지
- **Task Cleanup**: 완료된 태스크 자동 정리
- **Connection Limits**: WebSocket 연결수 제한

#### 실시간성 보장

- **Rate Limiting**: API 제한 준수하면서 최대 처리량
- **Event Batching**: 빈번한 업데이트 일괄 처리
- **Priority Queues**: 중요 이벤트 우선 처리

### 7.4 장기적 관점

#### 확장성 고려사항

- **Microservice 아키텍처**: 서비스별 독립적 스케일링
- **Event Sourcing**: 상태 변화 이벤트 기록
- **CQRS 패턴**: 읽기/쓰기 모델 분리

#### 모니터링 및 관리

- **헬스체크 시스템**: WebSocket 연결 상태 실시간 모니터링
- **성능 메트릭**: 이벤트 처리 지연시간 측정
- **장애 복구**: 자동 재연결 및 복구 로직

#### 팀 협업 문화

- **QAsync 패턴 코드 리뷰**: 이벤트 루프 위반 즉시 차단
- **성능 테스트 자동화**: CI/CD에 QAsync 테스트 포함
- **문서 지속 개선**: 새로운 패턴 발견시 가이드 업데이트

---

## 🎯 결론

QAsync 통합 이벤트 기반 아키텍처는 **실시간 금융 데이터 처리의 핵심**입니다.

**업비트 자동매매 시스템**에서 달성한 성과:

- ✅ 단일 이벤트 루프 통합 (PyQt + asyncio)
- ✅ 실시간 WebSocket 데이터 안정적 처리
- ✅ UI 반응성과 백그라운드 작업 완벽 분리
- ✅ LoopGuard를 통한 회귀 방지 체계

**지속적인 개선**을 통해 더욱 안정적이고 확장 가능한 시스템으로 발전시켜 나가길 바랍니다.

---

**📚 참고 자료**:

- [QAsync 공식 문서](https://github.com/CabbageDevelopment/qasync)
- [asyncio 공식 문서](https://docs.python.org/3/library/asyncio.html)
- [PyQt6 비동기 프로그래밍](https://doc.qt.io/qtforpython/)

**📁 관련 파일**:

- `upbit_auto_trading/infrastructure/runtime/app_kernel.py`
- `upbit_auto_trading/infrastructure/runtime/loop_guard.py`
- `run_desktop_ui.py`
- `docs/big_issues/issue_01_20250926/QAsync_REFACTORING_WORK_GUIDE.md`
