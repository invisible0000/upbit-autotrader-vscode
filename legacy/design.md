# 📊 차트 뷰어 설계 문서 (Design Document)

## 📋 개요

본 문서는 업비트 자동매매 시스템의 **3열 레이아웃 차트 뷰어**를 구현하기 위한 기술적 설계를 정의합니다. 코인 리스트, 실시간 차트, 호가창을 1:4:2 비율로 배치하여 마켓 데이터 DB와 API/WebSocket 통신을 테스트할 수 있는 종합적인 차트 뷰어를 구현합니다.

## 🎯 설계 목표

### 1. 핵심 목표
- **3열 레이아웃**: 코인 리스트 1 : 차트 4 : 호가창 2 비율의 동적 레이아웃
- **실시간 차트**: PyQtGraph 기반 고성능 캔들스틱 차트와 서브플롯
- **마켓 데이터 통합**: Market Data Backbone을 통한 통합 데이터 관리
- **하이브리드 데이터**: WebSocket(실시간) + API(일/주/월봉) 혼합 접근
- **리소스 최적화**: 윈도우 상태 기반 백그라운드 최적화

### 2. 성능 목표
- **차트 렌더링**: 1분봉 1000개 데이터 < 100ms 렌더링
- **실시간 업데이트**: WebSocket 데이터 수신 시 < 50ms 차트 반영
- **메모리 사용**: 최대 200MB (캔들 데이터 + 차트 캐시)
- **UI 응답성**: 창 크기 조정 시 60 FPS 유지

## 🏗️ 아키텍처 설계

### 1. DDD 4계층 구조 적용

```
┌─────────────────────────────────────────────────┐
│               Presentation Layer                │
│  ├─ ChartViewerView (MVP Passive View)          │
│  └─ ChartViewerPresenter (MVP Presenter)        │
├─────────────────────────────────────────────────┤
│              Application Layer                  │
│  ├─ ChartViewerUseCase                         │
│  ├─ MarketDataService                          │
│  └─ OrderbookService                           │
├─────────────────────────────────────────────────┤
│                Domain Layer                     │
│  ├─ CandleData (Value Object)                  │
│  ├─ OrderbookEntry (Value Object)              │
│  ├─ Symbol (Value Object)                      │
│  └─ Timeframe (Enum)                           │
├─────────────────────────────────────────────────┤
│            Infrastructure Layer                 │
│  ├─ UpbitWebSocketClient                       │
│  ├─ UpbitApiClient                             │
│  ├─ MarketDataRepository (SQLite)              │
│  └─ CacheManager                               │
└─────────────────────────────────────────────────┘
```

### 2. MVP 패턴 적용

```python
# Passive View Pattern
class ChartViewerView(QWidget):
    """MVP의 Passive View - 순수 UI 관심사만 담당"""

    def __init__(self):
        # UI 구성: 3열 1:4:2 분할 레이아웃
        # QSplitter(Qt.Horizontal) 기반
        pass

    def update_chart_data(self, candles: List[CandleData]) -> None:
        """Presenter에서 호출하는 차트 업데이트 메서드"""
        pass

    def update_orderbook(self, orderbook: OrderbookData) -> None:
        """Presenter에서 호출하는 호가창 업데이트 메서드"""
        pass

class ChartViewerPresenter:
    """MVP의 Presenter - 비즈니스 로직과 UI 연결"""

    def __init__(self, view: ChartViewerView, use_case: ChartViewerUseCase):
        self.view = view
        self.use_case = use_case
        self._setup_event_handlers()

    def handle_symbol_selection(self, symbol: str) -> None:
        """심볼 선택 이벤트 처리"""
        pass

    def handle_timeframe_change(self, timeframe: str) -> None:
        """타임프레임 변경 이벤트 처리"""
        pass
```

## 🎨 UI 컴포넌트 설계

### 1. 메인 레이아웃: 3열 1:4:2 분할

```python
class ChartViewerView(QWidget):
    def _setup_ui(self):
        # 메인 레이아웃: 수평 3분할
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setSizes([150, 600, 300])  # 1:4:2 비율

        # 좌측: 코인 리스트
        self.coin_list_panel = self._create_coin_list_panel()

        # 중앙: 차트 및 서브플롯
        self.chart_panel = self._create_chart_panel()

        # 우측: 호가창
        self.orderbook_panel = self._create_orderbook_panel()

        self.main_splitter.addWidget(self.coin_list_panel)
        self.main_splitter.addWidget(self.chart_panel)
        self.main_splitter.addWidget(self.orderbook_panel)
```

### 2. 좌측 패널: 코인 리스트

```python
def _create_coin_list_panel(self) -> QWidget:
    """코인 리스트 패널 생성"""
    panel = QWidget()
    layout = QVBoxLayout()

    # 검색 필터
    self.search_edit = QLineEdit()
    self.search_edit.setPlaceholderText("코인 검색...")
    layout.addWidget(QLabel("코인 목록"))
    layout.addWidget(self.search_edit)

    # 마켓 필터 (KRW, BTC, USDT)
    market_layout = QHBoxLayout()
    self.krw_checkbox = QCheckBox("KRW")
    self.krw_checkbox.setChecked(True)
    self.btc_checkbox = QCheckBox("BTC")
    self.usdt_checkbox = QCheckBox("USDT")

    market_layout.addWidget(self.krw_checkbox)
    market_layout.addWidget(self.btc_checkbox)
    market_layout.addWidget(self.usdt_checkbox)
    layout.addLayout(market_layout)

    # 코인 리스트 위젯
    self.coin_list_widget = QListWidget()
    self.coin_list_widget.setAlternatingRowColors(True)
    layout.addWidget(self.coin_list_widget)

    # 즐겨찾기 관리
    favorites_layout = QHBoxLayout()
    self.add_favorite_btn = QPushButton("즐겨찾기 추가")
    self.remove_favorite_btn = QPushButton("제거")
    favorites_layout.addWidget(self.add_favorite_btn)
    favorites_layout.addWidget(self.remove_favorite_btn)
    layout.addLayout(favorites_layout)

    panel.setLayout(layout)
    return panel
```

### 3. 중앙 패널: PyQtGraph 차트

```python
def _create_chart_panel(self) -> QWidget:
    """차트 패널 생성"""
    panel = QWidget()
    layout = QVBoxLayout()

    # 차트 툴바
    toolbar = self._create_chart_toolbar()
    layout.addWidget(toolbar)

    # 메인 차트 영역 (수직 분할)
    self.chart_splitter = QSplitter(Qt.Orientation.Vertical)

    # 상단: 캔들스틱 차트 (70%)
    self.price_chart_widget = pg.PlotWidget()
    self.price_chart_widget.setLabel('left', '가격 (KRW)')
    self.price_chart_widget.setLabel('bottom', '시간')
    self.price_chart_widget.showGrid(x=True, y=True)

    # 하단: 거래량 차트 (30%)
    self.volume_chart_widget = pg.PlotWidget()
    self.volume_chart_widget.setLabel('left', '거래량')
    self.volume_chart_widget.setLabel('bottom', '시간')

    self.chart_splitter.addWidget(self.price_chart_widget)
    self.chart_splitter.addWidget(self.volume_chart_widget)
    self.chart_splitter.setSizes([700, 300])  # 7:3 비율

    layout.addWidget(self.chart_splitter)

    panel.setLayout(layout)
    return panel

def _create_chart_toolbar(self) -> QWidget:
    """차트 툴바 생성"""
    toolbar = QWidget()
    layout = QHBoxLayout()

    # 심볼 정보 표시
    self.symbol_label = QLabel("KRW-BTC")
    self.symbol_label.setStyleSheet("font-weight: bold; font-size: 14px;")
    layout.addWidget(self.symbol_label)

    # 타임프레임 선택
    self.timeframe_combo = QComboBox()
    self.timeframe_combo.addItems(["1m", "5m", "15m", "1h", "4h", "1d", "1w", "1M"])
    self.timeframe_combo.setCurrentText("5m")
    layout.addWidget(QLabel("봉:"))
    layout.addWidget(self.timeframe_combo)

    # 차트 타입 선택
    self.chart_type_combo = QComboBox()
    self.chart_type_combo.addItems(["캔들스틱", "라인", "OHLC"])
    layout.addWidget(QLabel("타입:"))
    layout.addWidget(self.chart_type_combo)

    # 지표 토글 버튼들
    self.ma_checkbox = QCheckBox("이동평균")
    self.bollinger_checkbox = QCheckBox("볼린저밴드")
    self.rsi_checkbox = QCheckBox("RSI")

    layout.addWidget(self.ma_checkbox)
    layout.addWidget(self.bollinger_checkbox)
    layout.addWidget(self.rsi_checkbox)

    layout.addStretch()

    # 새로고침 버튼
    self.refresh_btn = QPushButton("새로고침")
    layout.addWidget(self.refresh_btn)

    toolbar.setLayout(layout)
    return toolbar
```

### 4. 우측 패널: 호가창

```python
def _create_orderbook_panel(self) -> QWidget:
    """호가창 패널 생성"""
    panel = QWidget()
    layout = QVBoxLayout()

    # 호가창 헤더
    header_layout = QHBoxLayout()
    header_layout.addWidget(QLabel("매도호가"))
    header_layout.addWidget(QLabel("수량"))
    header_layout.addWidget(QLabel("매수호가"))
    layout.addLayout(header_layout)

    # 호가 테이블
    self.orderbook_table = QTableWidget()
    self.orderbook_table.setColumnCount(3)
    self.orderbook_table.setHorizontalHeaderLabels(["매도가", "수량", "매수가"])
    self.orderbook_table.setRowCount(30)  # 15매도 + 15매수

    # 테이블 스타일링
    self.orderbook_table.setAlternatingRowColors(True)
    self.orderbook_table.verticalHeader().setVisible(False)
    self.orderbook_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

    layout.addWidget(self.orderbook_table)

    # 호가 요약 정보
    summary_layout = QVBoxLayout()
    self.current_price_label = QLabel("현재가: 0 KRW")
    self.price_change_label = QLabel("전일대비: 0 KRW (0%)")
    self.volume_label = QLabel("거래량: 0")

    summary_layout.addWidget(self.current_price_label)
    summary_layout.addWidget(self.price_change_label)
    summary_layout.addWidget(self.volume_label)
    layout.addLayout(summary_layout)

    panel.setLayout(layout)
    return panel
```

## 📊 PyQtGraph 차트 구현

### 1. 캔들스틱 차트 렌더러

```python
class CandlestickChart:
    """PyQtGraph 기반 캔들스틱 차트 렌더러"""

    def __init__(self, plot_widget: pg.PlotWidget):
        self.plot_widget = plot_widget
        self.candle_items = []
        self.volume_items = []
        self._setup_chart()

    def _setup_chart(self):
        """차트 초기 설정"""
        # 축 설정
        self.plot_widget.setLabel('left', '가격', units='KRW')
        self.plot_widget.setLabel('bottom', '시간')

        # 그리드 표시
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # 십자선 커서
        self.crosshair = pg.CrosshairPlot(self.plot_widget)

        # 확대/축소 설정
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.enableAutoRange(axis='y')

    def update_candlestick_data(self, candles: List[CandleData]):
        """캔들스틱 데이터 업데이트"""
        # 기존 아이템 제거
        self._clear_candles()

        if not candles:
            return

        # 캔들 바 생성
        for i, candle in enumerate(candles):
            # 캔들 몸체 (open-close)
            body_color = 'red' if candle.close >= candle.open else 'blue'
            body_height = abs(candle.close - candle.open)
            body_y = min(candle.open, candle.close)

            body_rect = pg.BarGraphItem(
                x=[i], height=[body_height], width=0.6,
                y0=[body_y], brush=body_color, pen=body_color
            )
            self.plot_widget.addItem(body_rect)
            self.candle_items.append(body_rect)

            # 캔들 심지 (high-low)
            wick_line = pg.PlotDataItem(
                [i, i], [candle.low, candle.high],
                pen=pg.mkPen(color=body_color, width=1)
            )
            self.plot_widget.addItem(wick_line)
            self.candle_items.append(wick_line)

        # X축 라벨 설정 (시간)
        self._setup_time_axis(candles)

    def _clear_candles(self):
        """기존 캔들 아이템 제거"""
        for item in self.candle_items:
            self.plot_widget.removeItem(item)
        self.candle_items.clear()

    def _setup_time_axis(self, candles: List[CandleData]):
        """시간 축 설정"""
        if not candles:
            return

        # 시간 축 틱 설정
        time_ticks = []
        for i, candle in enumerate(candles[::10]):  # 10개마다 표시
            time_str = candle.timestamp.strftime("%H:%M")
            time_ticks.append((i * 10, time_str))

        axis = self.plot_widget.getAxis('bottom')
        axis.setTicks([time_ticks])

    def add_moving_average(self, prices: List[float], period: int, color: str = 'yellow'):
        """이동평균선 추가"""
        if len(prices) < period:
            return

        ma_values = []
        for i in range(period - 1, len(prices)):
            ma = sum(prices[i - period + 1:i + 1]) / period
            ma_values.append(ma)

        # 이동평균선 플롯
        x_data = list(range(period - 1, len(prices)))
        ma_line = pg.PlotDataItem(
            x_data, ma_values,
            pen=pg.mkPen(color=color, width=2),
            name=f'MA{period}'
        )
        self.plot_widget.addItem(ma_line)
        self.candle_items.append(ma_line)

    def add_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2):
        """볼린저 밴드 추가"""
        if len(prices) < period:
            return

        import numpy as np

        upper_band = []
        lower_band = []
        middle_band = []

        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1:i + 1]
            mean = np.mean(window)
            std = np.std(window)

            middle_band.append(mean)
            upper_band.append(mean + std_dev * std)
            lower_band.append(mean - std_dev * std)

        x_data = list(range(period - 1, len(prices)))

        # 밴드 라인들
        upper_line = pg.PlotDataItem(x_data, upper_band, pen='red')
        middle_line = pg.PlotDataItem(x_data, middle_band, pen='yellow')
        lower_line = pg.PlotDataItem(x_data, lower_band, pen='red')

        # 밴드 영역 채우기
        fill_item = pg.FillBetweenItem(upper_line, lower_line, brush=(255, 0, 0, 50))

        self.plot_widget.addItem(upper_line)
        self.plot_widget.addItem(middle_line)
        self.plot_widget.addItem(lower_line)
        self.plot_widget.addItem(fill_item)

        self.candle_items.extend([upper_line, middle_line, lower_line, fill_item])
```

### 2. 거래량 차트 렌더러

```python
class VolumeChart:
    """거래량 차트 렌더러"""

    def __init__(self, plot_widget: pg.PlotWidget):
        self.plot_widget = plot_widget
        self.volume_items = []
        self._setup_chart()

    def _setup_chart(self):
        """차트 초기 설정"""
        self.plot_widget.setLabel('left', '거래량')
        self.plot_widget.setLabel('bottom', '시간')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

    def update_volume_data(self, candles: List[CandleData]):
        """거래량 데이터 업데이트"""
        # 기존 아이템 제거
        self._clear_volume()

        if not candles:
            return

        volumes = [candle.volume for candle in candles]
        x_data = list(range(len(volumes)))

        # 거래량 바 차트
        volume_bars = pg.BarGraphItem(
            x=x_data, height=volumes, width=0.8,
            brush='lightblue', pen='blue'
        )
        self.plot_widget.addItem(volume_bars)
        self.volume_items.append(volume_bars)

    def _clear_volume(self):
        """기존 거래량 아이템 제거"""
        for item in self.volume_items:
            self.plot_widget.removeItem(item)
        self.volume_items.clear()
```

## 📡 Market Data Backbone 시스템

### 1. 마켓 데이터 수집기

```python
from typing import Protocol, List, Optional
from datetime import datetime

class DataCollector:
    """통합 마켓 데이터 수집기"""

    def __init__(self, websocket_client, api_client, cache_manager):
        self.websocket_client = websocket_client
        self.api_client = api_client
        self.cache_manager = cache_manager
        self._subscriptions = {}

    async def subscribe_candle_data(self, symbol: str, timeframe: str) -> None:
        """캔들 데이터 구독"""
        if timeframe in ['1m', '5m', '15m', '1h', '4h']:
            # WebSocket으로 실시간 데이터 구독
            await self._subscribe_websocket_candles(symbol, timeframe)
        else:
            # API로 주기적 폴링
            await self._schedule_api_polling(symbol, timeframe)

    async def _subscribe_websocket_candles(self, symbol: str, timeframe: str):
        """WebSocket 캔들 구독"""
        def on_candle_received(data):
            candle = self._parse_websocket_candle(data)
            self.cache_manager.update_candle(symbol, timeframe, candle)
            self._notify_subscribers(symbol, timeframe, candle)

        await self.websocket_client.subscribe_candles(
            symbol, timeframe, on_candle_received
        )

    async def _schedule_api_polling(self, symbol: str, timeframe: str):
        """API 폴링 스케줄링"""
        import asyncio

        async def poll_candles():
            while True:
                try:
                    candles = await self.api_client.get_candles(symbol, timeframe, 200)
                    self.cache_manager.store_candles(symbol, timeframe, candles)
                    self._notify_subscribers(symbol, timeframe, candles[-1])
                except Exception as e:
                    print(f"API 폴링 에러: {e}")

                # 폴링 간격 (일봉: 1분, 주봉: 5분, 월봉: 10분)
                intervals = {'1d': 60, '1w': 300, '1M': 600}
                await asyncio.sleep(intervals.get(timeframe, 60))

        asyncio.create_task(poll_candles())

    def get_historical_candles(self, symbol: str, timeframe: str, count: int = 200) -> List[CandleData]:
        """과거 캔들 데이터 조회"""
        # 1. 캐시에서 조회
        cached_candles = self.cache_manager.get_candles(symbol, timeframe, count)
        if len(cached_candles) >= count:
            return cached_candles[-count:]

        # 2. API에서 조회 후 캐시 업데이트
        api_candles = self.api_client.get_candles_sync(symbol, timeframe, count)
        self.cache_manager.store_candles(symbol, timeframe, api_candles)
        return api_candles

    def _notify_subscribers(self, symbol: str, timeframe: str, candle: CandleData):
        """구독자들에게 알림"""
        key = f"{symbol}:{timeframe}"
        if key in self._subscriptions:
            for callback in self._subscriptions[key]:
                try:
                    callback(candle)
                except Exception as e:
                    print(f"구독자 알림 에러: {e}")

    def add_subscriber(self, symbol: str, timeframe: str, callback):
        """구독자 추가"""
        key = f"{symbol}:{timeframe}"
        if key not in self._subscriptions:
            self._subscriptions[key] = []
        self._subscriptions[key].append(callback)
```

### 2. 캐시 매니저

```python
import sqlite3
from typing import List, Optional
from datetime import datetime, timedelta

class CacheManager:
    """마켓 데이터 캐시 관리자"""

    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS candle_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    volume REAL NOT NULL,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    UNIQUE(symbol, timeframe, timestamp)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_candle_symbol_timeframe
                ON candle_cache(symbol, timeframe, timestamp DESC)
            """)

    def store_candles(self, symbol: str, timeframe: str, candles: List[CandleData]):
        """캔들 데이터 저장"""
        with sqlite3.connect(self.db_path) as conn:
            for candle in candles:
                conn.execute("""
                    INSERT OR REPLACE INTO candle_cache
                    (symbol, timeframe, timestamp, open_price, high_price, low_price, close_price, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, timeframe, int(candle.timestamp.timestamp()),
                    candle.open, candle.high, candle.low, candle.close, candle.volume
                ))

    def get_candles(self, symbol: str, timeframe: str, count: int = 200) -> List[CandleData]:
        """캔들 데이터 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT timestamp, open_price, high_price, low_price, close_price, volume
                FROM candle_cache
                WHERE symbol = ? AND timeframe = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (symbol, timeframe, count))

            candles = []
            for row in cursor.fetchall():
                timestamp, open_price, high_price, low_price, close_price, volume = row
                candle = CandleData(
                    timestamp=datetime.fromtimestamp(timestamp),
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume
                )
                candles.append(candle)

            return list(reversed(candles))  # 오래된 순으로 정렬

    def update_candle(self, symbol: str, timeframe: str, candle: CandleData):
        """실시간 캔들 업데이트"""
        self.store_candles(symbol, timeframe, [candle])

    def cleanup_old_data(self, days_to_keep: int = 30):
        """오래된 데이터 정리"""
        cutoff_timestamp = int((datetime.now() - timedelta(days=days_to_keep)).timestamp())

        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                DELETE FROM candle_cache
                WHERE timestamp < ?
            """, (cutoff_timestamp,))
            print(f"오래된 캔들 데이터 {result.rowcount}개 삭제됨")
```

## 🚀 성능 최적화 전략

### 1. 윈도우 라이프사이클 관리

```python
class WindowLifecycleManager:
    """윈도우 상태 기반 리소스 관리"""

    def __init__(self, chart_viewer):
        self.chart_viewer = chart_viewer
        self.is_window_visible = True
        self.is_window_minimized = False
        self._setup_window_events()

    def _setup_window_events(self):
        """윈도우 이벤트 연결"""
        # 윈도우 상태 변경 감지
        self.chart_viewer.view.changeEvent = self._on_window_state_changed
        self.chart_viewer.view.showEvent = self._on_window_shown
        self.chart_viewer.view.hideEvent = self._on_window_hidden

    def _on_window_state_changed(self, event):
        """윈도우 상태 변경 처리"""
        if event.type() == event.Type.WindowStateChange:
            self.is_window_minimized = self.chart_viewer.view.isMinimized()
            self._update_resource_usage()

    def _on_window_shown(self, event):
        """윈도우 표시됨"""
        self.is_window_visible = True
        self._update_resource_usage()

    def _on_window_hidden(self, event):
        """윈도우 숨겨짐"""
        self.is_window_visible = False
        self._update_resource_usage()

    def _update_resource_usage(self):
        """리소스 사용량 조정"""
        if self.is_window_minimized or not self.is_window_visible:
            # 백그라운드 모드: 업데이트 간격 늘리기
            self.chart_viewer.presenter.set_update_interval(5000)  # 5초
            self.chart_viewer.presenter.disable_chart_animations()
        else:
            # 활성 모드: 정상 업데이트
            self.chart_viewer.presenter.set_update_interval(1000)  # 1초
            self.chart_viewer.presenter.enable_chart_animations()
```

### 2. 동적 레이아웃 최적화

```python
class DynamicSplitter(QSplitter):
    """성능 최적화된 동적 스플리터"""

    def __init__(self, orientation=Qt.Orientation.Horizontal):
        super().__init__(orientation)
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._delayed_resize)
        self._target_sizes = []

    def setSizes(self, sizes: List[int]):
        """크기 설정 (디바운싱 적용)"""
        self._target_sizes = sizes
        self._resize_timer.stop()
        self._resize_timer.start(100)  # 100ms 지연

    def _delayed_resize(self):
        """지연된 크기 조정"""
        super().setSizes(self._target_sizes)

    def resizeEvent(self, event):
        """리사이즈 이벤트 최적화"""
        super().resizeEvent(event)

        # 차트 위젯들에게 크기 변경 알림
        for i in range(self.count()):
            widget = self.widget(i)
            if hasattr(widget, 'on_parent_resized'):
                widget.on_parent_resized(event.size())
```

## 📋 Use Case 구현

```python
class ChartViewerUseCase:
    """차트 뷰어 비즈니스 로직"""

    def __init__(self):
        self.data_collector = DataCollector(
            websocket_client=get_websocket_client(),
            api_client=get_api_client(),
            cache_manager=CacheManager()
        )
        self._current_symbol = "KRW-BTC"
        self._current_timeframe = "5m"
        self._subscribers = []

    async def initialize(self):
        """초기화"""
        # 기본 심볼 구독
        await self.subscribe_to_symbol(self._current_symbol, self._current_timeframe)

    async def subscribe_to_symbol(self, symbol: str, timeframe: str):
        """심볼 구독"""
        self._current_symbol = symbol
        self._current_timeframe = timeframe

        # 데이터 수집기에 구독
        await self.data_collector.subscribe_candle_data(symbol, timeframe)

        # 실시간 데이터 콜백 등록
        self.data_collector.add_subscriber(
            symbol, timeframe, self._on_candle_received
        )

        # 과거 데이터 로드
        historical_candles = self.data_collector.get_historical_candles(
            symbol, timeframe, 200
        )
        self._notify_subscribers('candles', historical_candles)

    def _on_candle_received(self, candle: CandleData):
        """실시간 캔들 수신"""
        self._notify_subscribers('candle_update', candle)

    async def get_orderbook_data(self, symbol: str) -> OrderbookData:
        """호가 데이터 조회"""
        return await self.data_collector.websocket_client.get_orderbook(symbol)

    def get_available_symbols(self) -> List[str]:
        """사용 가능한 심볼 목록"""
        return self.data_collector.api_client.get_market_symbols()

    def add_subscriber(self, callback):
        """구독자 추가"""
        self._subscribers.append(callback)

    def _notify_subscribers(self, event_type: str, data):
        """구독자들에게 알림"""
        for callback in self._subscribers:
            try:
                callback(event_type, data)
            except Exception as e:
                print(f"구독자 알림 에러: {e}")

    def calculate_technical_indicators(self, candles: List[CandleData]) -> dict:
        """기술적 지표 계산"""
        closes = [candle.close for candle in candles]

        indicators = {}

        # 이동평균 계산
        if len(closes) >= 20:
            ma20 = self._calculate_moving_average(closes, 20)
            ma60 = self._calculate_moving_average(closes, 60)
            indicators['MA20'] = ma20
            indicators['MA60'] = ma60

        # RSI 계산
        if len(closes) >= 14:
            rsi = self._calculate_rsi(closes, 14)
            indicators['RSI'] = rsi

        # 볼린저 밴드 계산
        if len(closes) >= 20:
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(closes, 20)
            indicators['BB_UPPER'] = bb_upper
            indicators['BB_MIDDLE'] = bb_middle
            indicators['BB_LOWER'] = bb_lower

        return indicators

    def _calculate_moving_average(self, prices: List[float], period: int) -> List[float]:
        """이동평균 계산"""
        ma_values = []
        for i in range(period - 1, len(prices)):
            ma = sum(prices[i - period + 1:i + 1]) / period
            ma_values.append(ma)
        return ma_values

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """RSI 계산"""
        if len(prices) < period + 1:
            return []

        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        rsi_values = []
        for i in range(period - 1, len(gains)):
            avg_gain = sum(gains[i - period + 1:i + 1]) / period
            avg_loss = sum(losses[i - period + 1:i + 1]) / period

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            rsi_values.append(rsi)

        return rsi_values

    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2):
        """볼린저 밴드 계산"""
        import statistics

        upper_band = []
        middle_band = []
        lower_band = []

        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1:i + 1]
            mean = statistics.mean(window)
            std = statistics.stdev(window)

            middle_band.append(mean)
            upper_band.append(mean + std_dev * std)
            lower_band.append(mean - std_dev * std)

        return upper_band, middle_band, lower_band
```

## 📁 파일 구조

```
upbit_auto_trading/ui/desktop/screens/chart_viewer/
├── __init__.py
├── chart_viewer_view.py                # MVP View
├── chart_viewer_presenter.py           # MVP Presenter
└── components/
    ├── __init__.py
    ├── candlestick_chart.py            # PyQtGraph 캔들스틱 차트
    ├── volume_chart.py                 # 거래량 차트
    ├── orderbook_widget.py             # 호가창 위젯
    ├── coin_list_widget.py             # 코인 리스트 위젯
    ├── dynamic_splitter.py             # 동적 스플리터
    └── window_lifecycle_manager.py     # 윈도우 라이프사이클 관리

upbit_auto_trading/application/use_cases/chart_viewer/
├── __init__.py
└── chart_viewer_use_case.py           # Use Case

upbit_auto_trading/infrastructure/market_data/
├── __init__.py
├── data_collector.py                  # 통합 데이터 수집기
├── cache_manager.py                   # 캐시 관리자
├── websocket_client.py                # WebSocket 클라이언트
└── api_client.py                      # API 클라이언트
```

## 🧪 테스트 전략

### 1. 단위 테스트
- CandlestickChart 렌더링 테스트
- CacheManager 데이터 저장/조회 테스트
- 기술적 지표 계산 정확성 테스트

### 2. 통합 테스트
- WebSocket + API 하이브리드 데이터 수집 테스트
- UI 이벤트 → Presenter → UseCase 플로우 테스트
- 실시간 데이터 수신 및 차트 업데이트 테스트

### 3. 성능 테스트
- 1000개 캔들 렌더링 성능 (<100ms)
- 메모리 사용량 모니터링 (<200MB)
- 실시간 업데이트 지연 측정 (<50ms)

## 📈 성공 지표

### 1. 기능적 지표
- ✅ **3열 레이아웃**: 1:4:2 비율 동적 조정 가능
- ✅ **실시간 차트**: PyQtGraph 기반 고성능 렌더링
- ✅ **마켓 데이터 통합**: WebSocket + API 하이브리드 동작
- ✅ **기술적 지표**: 이동평균, RSI, 볼린저밴드 표시

### 2. 성능 지표
- ✅ **차트 렌더링 < 100ms**: 1000개 캔들 데이터
- ✅ **실시간 업데이트 < 50ms**: WebSocket 데이터 수신 시
- ✅ **메모리 사용량 < 200MB**: 캔들 + 차트 캐시 포함
- ✅ **UI 응답성 60 FPS**: 창 크기 조정 시

### 3. 사용성 지표
- ✅ **직관적 레이아웃**: 코인 선택 → 차트 표시 → 호가 확인 플로우
- ✅ **부드러운 상호작용**: 확대/축소, 스크롤, 크기 조정
- ✅ **실시간 피드백**: 가격 변동 시 즉시 차트 반영

---

이 설계 문서는 DDD 아키텍처와 MVP 패턴을 엄격히 준수하며, PyQtGraph 기반 고성능 차트와 하이브리드 데이터 수집을 통해 완전한 차트 뷰어를 구현하기 위한 기술적 청사진입니다.
