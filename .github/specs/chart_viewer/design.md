# 차트뷰어 설계 문서

## 📊 개요

마켓 데이터 DB 및 실시간 API/WebSocket 연동 테스트용 차트뷰어 구현. 3열 동적 레이아웃(1:4:2), 실시간 데이터 백본, 창 상태 기반 리소스 관리를 특징으로 합니다.

## 🏗️ 아키텍처 설계

### 핵심 설계 원칙

1. **기존 이벤트 버스 확장**: 현재 시스템을 안전하게 확장하여 호환성 보장
2. **마켓 데이터 백본**: 통합 데이터 관리 시스템으로 멀티소스(API+WebSocket) 수집
3. **동적 리소스 관리**: 창 상태에 따른 자동 리소스 제어 (활성화/비활성화)
4. **우선순위 기반 처리**: 기존 priority 시스템 확장으로 안전한 리소스 관리
5. **PyQtGraph 고성능**: 실시간 차트 렌더링 최적화
6. **구독 기반 아키텍처**: 차트뷰별 독립적 데이터 구독/해제

### UI 레이아웃 (3열 1:4:2 비율) - 호가창 우선 개발

```
┌──────────┬──────────────────────────────────────────────────┬─────────────┐
│  Coin    │            Chart Area (4) - Phase 2 구현         │  Orderbook  │
│  List    │  ┌────────────────────────────────────────────┐  │  (우선구현) │
│          │  │         Main Plot (Candlestick) 4 비율    │  │             │
│ (1 비율) │  ├────────────────────────────────────────────┤  │   실시간    │
│          │  │ Volume  │ MACD   │ RSI    │ STOCH  │ ATR   │  │   호가창    │
│          │  │ 1 비율  │ 1 비율 │ 1 비율 │ 1 비율 │ 1비율 │  │ + 호가모아  │
│          │  └────────────────────────────────────────────┘  │   보기      │
│          │        5개 서브플롯 (4:1:1:1:1:1 비율)            │  (2 비율)   │
└──────────┴──────────────────────────────────────────────────┴─────────────┘
```

### 기존 이벤트 버스 시스템 확장

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Existing InMemoryEventBus (확장)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐ │
│ │ Enhanced        │ │ Resource        │ │ Chart Viewer    │ │ Trading     │ │
│ │ Priority System │ │ Monitor         │ │ Extension       │ │ Compatibility│ │
│ │ - 기존 priority │ │ - 창 상태 감지  │ │ - 타임프레임    │ │ - 기존 시스템│ │
│ │ - 차트뷰어 확장 │ │ - 리소스 사용량 │ │ - 1개월 지원    │ │ - 영향 없음  │ │
│ │ - 안전한 처리   │ │ - 자동 조절     │ │ - WebSocket+API │ │ - 격리 처리  │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
              │                    │                    │
    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
    │ Trading Engine  │   │ Chart Viewer    │   │ Market Data     │
    │ (기존 유지)     │   │ (새로 추가)     │   │ Backbone (확장) │
    │ - 기존 로직     │   │ - 실시간 차트   │   │ - 1개월 지원    │
    │ - 영향 없음     │   │ - 안전한 처리   │   │ - 데이터 수집   │
    └─────────────────┘   └─────────────────┘   └─────────────────┘
```
    │ - 포지션 관리   │   │ - 호가창 업데이트│   │ - 캐시 관리     │
    │ - 리스크 제어   │   │ - 기술적 지표   │   │ - 구독 관리     │
    └─────────────────┘   └─────────────────┘   └─────────────────┘
```

### 마켓 데이터 백본 시스템

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Market Data Backbone                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐ │
│ │ Data Collection │ │ Memory Cache    │ │ Subscription    │ │ Lifecycle   │ │
│ │ Engine          │ │ Manager         │ │ Manager         │ │ Manager     │ │
│ │ - API + WS      │ │ - Redis Style   │ │ - 차트뷰별 구독  │ │ - 창 상태   │ │
│ │ - 데이터 검증    │ │ - 압축 저장     │ │ - 독립적 해제   │ │ - 리소스    │ │
│ │ - 실시간 동기화  │ │ - 인덱싱       │ │ - 라이프사이클  │ │ - 백그라운드│ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 컴포넌트 구조 (DDD + 이벤트 드리븐)

```
infrastructure/
├── event_bus/
│   ├── central_event_bus.py          # 중앙 이벤트 버스
│   ├── priority_queue_manager.py     # 우선순위 큐 관리
│   ├── async_task_scheduler.py       # 비동기 작업 스케줄러
│   ├── resource_pool_manager.py      # 리소스 풀 관리
│   └── event_router.py               # 이벤트 라우팅
├── market_data_backbone/
│   ├── data_collector.py             # API+WebSocket 수집기
│   ├── memory_cache.py               # Redis 스타일 캐시
│   ├── timeframe_converter.py        # 1분→3분,5분... 변환
│   └── resource_monitor.py           # 리소스 모니터링
├── chart_data_repository.py         # DB 차트 데이터
├── upbit_market_api.py               # 마켓 API
├── upbit_websocket_client.py         # WebSocket 클라이언트
└── technical_indicators.py          # 기술적 지표 계산

application/
├── event_handlers/
│   ├── market_data_event_handler.py  # 마켓 데이터 이벤트 처리
│   ├── chart_event_handler.py        # 차트 이벤트 처리
│   ├── trading_event_handler.py      # 매매 이벤트 처리
│   └── system_event_handler.py       # 시스템 이벤트 처리
├── market_data_backbone/
│   ├── data_collection_service.py    # 멀티소스 수집 엔진
│   ├── cache_manager.py              # 메모리 캐시 시스템
│   ├── subscription_manager.py       # 구독 관리
│   └── lifecycle_manager.py          # 창 상태 라이프사이클
├── chart_service.py                  # 차트 데이터 서비스
└── realtime_service.py               # 실시간 데이터 관리

presentation/chart_viewer/
├── views/
│   ├── chart_viewer_window.py        # 메인 윈도우 (3열 동적 레이아웃)
│   ├── coin_list_view.py             # 코인 리스트 (검색, 즐겨찾기)
│   ├── chart_area_view.py            # 차트 영역 (5개 서브플롯)
│   ├── orderbook_view.py             # 호가창 (실시간) - 우선 구현
│   └── control_panel_view.py         # 타임프레임/소스 컨트롤
├── presenters/
│   ├── window_lifecycle_presenter.py # 창 상태 기반 리소스 관리
│   ├── chart_presenter.py            # 차트 로직 (5개 서브플롯)
│   ├── coin_list_presenter.py        # 리스트 로직
│   └── orderbook_presenter.py        # 호가창 로직 (우선 구현)
└── widgets/
    ├── dynamic_splitter.py           # 동적 3열 스플리터
    ├── candlestick_widget.py         # PyQtGraph 캔들차트
    ├── multi_subplot_widget.py       # 5개 서브플롯 (Volume/MACD/RSI/STOCH/ATR)
    └── orderbook_widget.py           # 호가 바차트 (우선 구현)
```

## 📋 데이터 모델

### 이벤트 시스템 (기존 확장)
```python
# 기존 InMemoryEventBus 확장 - 호환성 보장
@dataclass(frozen=True)
class OrderbookEvent(DomainEvent):  # 호가창 우선 구현
    symbol: str
    orderbook_data: Dict[str, Any]
    timestamp: datetime
    window_active: bool = True  # 창 상태 기반 처리

@dataclass(frozen=True)
class ChartViewerEvent(DomainEvent):
    chart_id: str
    symbol: str
    data_type: str  # "candle", "orderbook", "indicator"
    timeframe: str  # "1m"~"1M" (1개월 포함)
    data: Any
    window_active: bool = True  # 창 상태 기반 처리

# 기존 priority 시스템 확장 (기존 코드 영향 없음)
class ChartViewerPriority:
    TRADING_CRITICAL = 1    # 기존 시스템 우선 (매매)
    ORDERBOOK_HIGH = 5      # 호가창 우선 구현 (기존 범위 내)
    CHART_HIGH = 5          # 차트뷰어 (기존 범위 내)
    CHART_BACKGROUND = 8    # 백그라운드 차트
    CHART_LOW = 10          # 최저 우선순위
```

### 차트 데이터 (1개월 지원)
```python
@dataclass(frozen=True)
class CandleData:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

@dataclass(frozen=True)
class ChartDataRequest:
    symbol: str
    timeframe: str  # "1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"
    count: int = 200
    source: str = "websocket"  # "websocket", "api", "hybrid"
    priority: int = ChartViewerPriority.CHART_HIGH  # 기존 시스템 호환
```

### 구독 관리
```python
@dataclass
class ChartSubscription:
    chart_id: str
    symbol: str
    timeframe: str  # 1M 포함
    window_active: bool = True
    priority: int = ChartViewerPriority.CHART_HIGH  # 기존 시스템 호환
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class SubscriptionState:
    active_subscriptions: Dict[str, ChartSubscription]
    background_subscriptions: Dict[str, ChartSubscription]
    resource_usage: float  # 0.0 ~ 1.0
```

### 호가 데이터 (우선 구현)
```python
@dataclass(frozen=True)
class OrderbookLevel:
    price: Decimal
    size: Decimal
    side: str  # "bid", "ask"

@dataclass(frozen=True)
class OrderbookData:
    symbol: str
    timestamp: datetime
    bids: List[OrderbookLevel]
    asks: List[OrderbookLevel]
    total_ask_size: Decimal  # 호가 매도 총 잔량
    total_bid_size: Decimal  # 호가 매수 총 잔량
    level: int = 0          # 호가 모아보기 단위
```

## 🔄 핵심 인터페이스 (기존 시스템 확장)

### 기존 이벤트 버스 확장 인터페이스
```python
# 기존 InMemoryEventBus 확장 - 완전 호환
class ChartViewerEventExtension:
    def __init__(self, existing_event_bus: InMemoryEventBus):
        self.event_bus = existing_event_bus

    def subscribe_chart_events(self, chart_id: str, symbol: str,
                              timeframe: str) -> str:
        """기존 subscribe 메서드 활용"""

    def publish_chart_event(self, event: ChartViewerEvent) -> None:
        """기존 publish 메서드 활용"""

    def set_window_priority(self, chart_id: str, active: bool) -> None:
        """창 상태에 따른 우선순위 조정 (기존 시스템 영향 없음)"""
```

### 마켓 데이터 백본 인터페이스 (1개월 지원)
```python
class MarketDataBackbone:
    def subscribe_chart_data(self, subscription: ChartSubscription) -> str
    def unsubscribe_chart_data(self, chart_id: str) -> None
    def get_historical_data(self, request: ChartDataRequest) -> List[CandleData]
    def get_realtime_data(self, symbol: str, timeframe: str) -> CandleData  # 1M 포함
    def set_window_state(self, chart_id: str, active: bool) -> None
    def get_resource_usage(self) -> float
    def is_timeframe_supported(self, timeframe: str) -> bool  # 1M 검증
```

### 차트 프레젠터 인터페이스 (기존 호환)
```python
class ChartPresenter:
    def __init__(self, event_bus: InMemoryEventBus):  # 기존 버스 활용
        self.event_bus = event_bus
        self._setup_event_handlers()

    def load_chart(self, symbol: str, timeframe: str) -> None  # 1M 포함
    def handle_chart_event(self, event: ChartViewerEvent) -> None
    def set_technical_indicators(self, indicators: List[str]) -> None
    def handle_window_state_change(self, active: bool) -> None
    def zoom_chart(self, zoom_level: float) -> None
    def scroll_chart(self, direction: int) -> None
```

### 호가창 프레젠터 인터페이스
```python
class OrderbookPresenter:
    def __init__(self, event_bus: InMemoryEventBus):  # 기존 버스 활용
        self.event_bus = event_bus

    def subscribe_orderbook(self, symbol: str) -> None
    def unsubscribe_orderbook(self) -> None
    def handle_orderbook_event(self, event: ChartViewerEvent) -> None
    def handle_price_click(self, price: Decimal) -> None
```

## 🎛️ 리소스 관리 전략 (기존 시스템 안전)

### 창 상태 기반 우선순위 조정 (기존 영향 없음)
```python
class ChartViewerResourceManager:
    def __init__(self):
        # 기존 시스템과 격리된 리소스 관리
        self.chart_priorities = {
            'active': ChartViewerPriority.CHART_HIGH,      # 5
            'background': ChartViewerPriority.CHART_BACKGROUND,  # 8
            'minimized': ChartViewerPriority.CHART_LOW     # 10
        }

    def adjust_chart_priority(self, chart_id: str, window_state: str) -> int:
        """기존 priority 범위 내에서 안전하게 조정"""
        return self.chart_priorities.get(window_state, 10)
```

### 창 상태별 리소스 제어 (기존 시스템 안전)
```python
class WindowLifecycleManager:
    def __init__(self, event_bus: InMemoryEventBus):  # 기존 버스 활용
        self.event_bus = event_bus
        self.resource_manager = ChartViewerResourceManager()

    def on_window_activated(self, chart_id: str):
        """창 활성화 시 우선순위 5로 조정 (기존 범위 내)"""

    def on_window_deactivated(self, chart_id: str):
        """창 비활성화 시 우선순위 8로 조정 (기존 시스템 영향 없음)"""

    def on_window_minimized(self, chart_id: str):
        """최소화 시 우선순위 10으로 조정 (최하위)"""

    def on_window_restored(self, chart_id: str):
        """복원 시 우선순위 5로 복원"""
```

### 1개월 타임프레임 지원
```python
class TimeframeSupport:
    SUPPORTED_TIMEFRAMES = {
        "1m": {"websocket": True, "api": True},
        "3m": {"websocket": True, "api": True},
        "5m": {"websocket": True, "api": True},
        "15m": {"websocket": True, "api": True},
        "30m": {"websocket": True, "api": True},
        "1h": {"websocket": True, "api": True},
        "4h": {"websocket": True, "api": True},
        "1d": {"websocket": True, "api": True},
        "1w": {"websocket": False, "api": True},  # API 전용
        "1M": {"websocket": False, "api": True}   # 1개월, API 전용
    }

    def get_data_source(self, timeframe: str) -> str:
        """타임프레임별 최적 데이터 소스 결정"""
        if timeframe in ["1w", "1M"]:
            return "api"  # WebSocket 미지원시 API 사용
        return "websocket"
class BackpressureController:
    def monitor_queue_depth(self) -> float
    def apply_backpressure(self, threshold: float = 0.8) -> None
    def drop_low_priority_tasks(self) -> int
    def throttle_data_collection(self, rate: float) -> None
    def emergency_resource_cleanup(self) -> None
```

### 메모리 관리
- **CRITICAL (매매)**: 무제한 메모리, 즉시 처리
- **HIGH (차트뷰어)**: 최대 256MB, 실시간 처리
- **NORMAL (백그라운드)**: 최대 128MB, 지연 허용
- **LOW (로깅)**: 최대 64MB, 배치 처리
- **백그라운드 모드**: 차트뷰어 우선순위 NORMAL → LOW 자동 전환

## 🔧 기술적 구현 세부사항

### 이벤트 버스 기반 비동기 시스템
```python
class CentralEventBus:
    def __init__(self):
        self.priority_queue = PriorityQueue()
        self.task_scheduler = AsyncTaskScheduler()
        self.resource_manager = PriorityResourceManager()
        self.event_router = EventRouter()

    async def process_events(self):
        """메인 이벤트 루프 - 우선순위 기반 처리"""
```

### 비동기 작업 스케줄러
```python
class AsyncTaskScheduler:
    def __init__(self):
        self.worker_pools = {
            EventPriority.CRITICAL: ThreadPoolExecutor(max_workers=4),
            EventPriority.HIGH: ThreadPoolExecutor(max_workers=3),
            EventPriority.NORMAL: ThreadPoolExecutor(max_workers=2),
            EventPriority.LOW: ThreadPoolExecutor(max_workers=1)
        }

    async def submit_task(self, task: AsyncTask) -> Future
    def monitor_task_health(self) -> Dict[str, Any]
    def handle_task_failure(self, task: AsyncTask, error: Exception) -> None
```

### PyQtGraph 차트 엔진 (이벤트 기반)
```python
class CandlestickWidget(pg.PlotWidget):
    def __init__(self, event_bus: CentralEventBus):
        self.event_bus = event_bus
        self.main_plot = self.getPlotItem()
        self.volume_plot = self.create_volume_subplot()
        self._setup_event_subscriptions()

    def handle_chart_update_event(self, event: ChartUpdateEvent):
        """이벤트 기반 실시간 캔들 업데이트"""

    def add_technical_indicator(self, indicator: str):
        """기술적 지표 오버레이"""

    def _setup_event_subscriptions(self):
        """차트 관련 이벤트 구독 설정"""
```

### WebSocket + API 하이브리드
```python
class HybridDataSource:
    def __init__(self):
        self.websocket_coverage = {
            "1m": True, "3m": True, "5m": True, "15m": True,
            "30m": True, "1h": True, "4h": True, "1d": True,
            "1w": False, "1M": False  # API 폴링으로 대체
        }

    def get_data_source(self, timeframe: str) -> str:
        """타임프레임별 최적 데이터 소스 결정"""
```

## 🎯 성능 목표

### 우선순위별 성능 기준
- **CRITICAL (매매)**: 1ms 이내 응답, 무제한 리소스
- **HIGH (차트뷰어)**: 16ms 이내 응답 (60fps), 256MB 메모리
- **NORMAL (백그라운드)**: 100ms 이내 응답, 128MB 메모리
- **LOW (로깅)**: 1초 이내 응답, 64MB 메모리

### 렌더링 성능
- **60fps**: 실시간 차트 업데이트 유지 (차트 활성 시)
- **30fps**: 백그라운드 모드 (차트 비활성 시)
- **200개 캔들**: 초기 로딩 1초 이내
- **스크롤**: 부드러운 과거 데이터 로딩

### 시스템 효율성
- **이벤트 처리**: 초당 1000개 이벤트 처리 가능
- **작업 큐**: 최대 10,000개 작업 대기열
- **백프레셔**: 대기열 80% 초과 시 자동 스로틀링
- **장애 격리**: 단일 컴포넌트 장애 시 시스템 전체 영향 최소화

### 메모리 효율성
- **전체 시스템**: 최대 1GB 메모리 사용
- **매매 엔진**: 512MB 보장
- **차트뷰어**: 256MB (활성), 64MB (비활성)
- **캐시 히트율**: 95% 이상

### 네트워크 효율성
- **WebSocket**: 실시간 연결 유지, 자동 재연결
- **API 호출**: 갭 데이터만 최소 요청
- **하이브리드 모드**: WebSocket 80% + API 20%
- **Rate Limiting**: Upbit API 제한 준수

## 🔍 주요 혁신 사항

1. **이벤트 버스 중심 아키텍처**: 비동기 메시지 기반으로 매매/차트뷰어 완전 분리
2. **우선순위 기반 스케줄링**: 실시간 매매 우선, 차트뷰어 적응적 리소스 할당
3. **마켓 데이터 백본**: 전체 시스템에서 공유 가능한 통합 데이터 관리
4. **동적 레이아웃**: 3열 비율 조정 가능한 스플리터
5. **창 상태 기반 최적화**: 리소스 사용량 90% 절약
6. **구독 모델**: 차트뷰별 독립적 데이터 관리
7. **하이브리드 데이터 소스**: WebSocket + API 자동 전환
8. **백프레셔 제어**: 시스템 과부하 시 자동 스로틀링
9. **장애 격리**: 컴포넌트별 독립적 장애 처리

## 🚀 실시간 매매 호환성

### 매매 엔진과의 공존 전략
1. **리소스 우선순위**: 매매 > 차트뷰어 > 백그라운드 작업
2. **동적 리소스 재할당**: 매매 모드 활성화 시 차트뷰어 자동 스로틀링
3. **공유 데이터 소스**: 동일한 마켓 데이터 백본 사용으로 중복 제거
4. **이벤트 기반 통신**: 직접 결합 없이 메시지 기반 협력
5. **독립적 장애 처리**: 차트뷰어 오류가 매매에 영향 없음

### 매매 모드 지원
```python
class TradingModeManager:
    def activate_trading_mode(self):
        """매매 모드 활성화 - 차트뷰어 리소스 자동 축소"""

    def deactivate_trading_mode(self):
        """매매 모드 비활성화 - 차트뷰어 리소스 복원"""

    def get_trading_priority_status(self) -> bool:
        """현재 매매 우선순위 모드 상태"""
```

---
*DDD 아키텍처와 Infrastructure v4.0 로깅 시스템을 준수하여 구현*
