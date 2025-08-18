# 차트뷰 구현 예시 코드
> 핵심 컴포넌트별 구체적인 구현 방법과 예시 코드

## 🏗️ 동적 3열 레이아웃 구현

### 1. DynamicSplitter (자동 비율 조정)
```python
from PyQt6.QtWidgets import QSplitter, QWidget
from PyQt6.QtCore import QSettings, pyqtSignal

class DynamicSplitter(QSplitter):
    """
    동적 비율 조정이 가능한 3열 스플리터
    Features:
    - 1:4:2 기본 비율 유지
    - 최소 크기 보장
    - 설정 저장/복원
    - 리사이즈 이벤트 처리
    """

    layoutChanged = pyqtSignal(list)  # 새로운 크기 비율

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings()
        self.min_sizes = [200, 400, 150]  # 최소 크기
        self.default_ratios = [1, 4, 2]   # 기본 비율

    def setupWidgets(self, coin_list, chart_area, orderbook):
        """위젯 추가 및 초기 설정"""
        self.addWidget(coin_list)
        self.addWidget(chart_area)
        self.addWidget(orderbook)

        # 최소 크기 설정
        for i, min_size in enumerate(self.min_sizes):
            widget = self.widget(i)
            if self.orientation() == Qt.Horizontal:
                widget.setMinimumWidth(min_size)
            else:
                widget.setMinimumHeight(min_size)

        # 저장된 설정 복원 또는 기본 비율 적용
        self.restoreLayout()

    def restoreLayout(self):
        """저장된 레이아웃 복원"""
        saved_sizes = self.settings.value("chart_viewer/splitter_sizes")
        if saved_sizes:
            self.setSizes([int(s) for s in saved_sizes])
        else:
            self.setDefaultRatios()

    def setDefaultRatios(self):
        """기본 비율 적용"""
        total_size = self.width() if self.orientation() == Qt.Horizontal else self.height()
        total_ratio = sum(self.default_ratios)

        sizes = []
        for ratio in self.default_ratios:
            size = int(total_size * ratio / total_ratio)
            sizes.append(max(size, self.min_sizes[len(sizes)]))

        self.setSizes(sizes)

    def saveLayout(self):
        """현재 레이아웃 저장"""
        sizes = self.sizes()
        self.settings.setValue("chart_viewer/splitter_sizes", sizes)

    def resizeEvent(self, event):
        """크기 변경시 최소 크기 보장"""
        super().resizeEvent(event)
        self.enforceMinimumSizes()

    def enforceMinimumSizes(self):
        """최소 크기 강제 적용"""
        sizes = self.sizes()
        modified = False

        for i, (current_size, min_size) in enumerate(zip(sizes, self.min_sizes)):
            if current_size < min_size:
                sizes[i] = min_size
                modified = True

        if modified:
            self.setSizes(sizes)
```

## 🔄 마켓 데이터 백본 시스템

### 2. DataCollector (멀티소스 데이터 수집)
```python
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import asyncio
import websockets
import aiohttp
from typing import Dict, Set

class DataCollector(QObject):
    """
    멀티소스 데이터 수집기
    Features:
    - WebSocket + API 동시 수집
    - 실시간 데이터 검증
    - 타임프레임별 수집 관리
    - 연결 상태 모니터링
    """

    dataReceived = pyqtSignal(str, str, dict)  # symbol, timeframe, data
    connectionStateChanged = pyqtSignal(str, bool)  # source, connected

    def __init__(self):
        super().__init__()
        self.active_collections = {}  # {symbol_timeframe: CollectionState}
        self.websocket_client = None
        self.api_session = None
        self.loop = None

    async def startCollection(self, symbol: str, timeframe: str):
        """데이터 수집 시작"""
        key = f"{symbol}_{timeframe}"

        if key not in self.active_collections:
            state = CollectionState(symbol, timeframe)
            self.active_collections[key] = state

            # WebSocket 구독
            await self.subscribeWebSocket(symbol, timeframe)

            # API 폴링 시작 (백업용)
            self.startApiPolling(symbol, timeframe)

    async def subscribeWebSocket(self, symbol: str, timeframe: str):
        """WebSocket 구독"""
        if timeframe == "1M":
            # 1개월은 WebSocket 미지원, API만 사용
            return

        subscribe_msg = {
            "ticket": f"{symbol}_{timeframe}",
            "type": "ticker" if timeframe.endswith("m") else "candles",
            "codes": [symbol]
        }

        try:
            if self.websocket_client:
                await self.websocket_client.send(json.dumps(subscribe_msg))
        except Exception as e:
            logger.error(f"WebSocket 구독 실패: {e}")

    def startApiPolling(self, symbol: str, timeframe: str):
        """API 폴링 시작"""
        key = f"{symbol}_{timeframe}"
        state = self.active_collections.get(key)

        if state:
            # 타임프레임별 폴링 주기 설정
            interval = self.getPollingInterval(timeframe)

            timer = QTimer()
            timer.timeout.connect(lambda: self.pollApiData(symbol, timeframe))
            timer.start(interval)

            state.api_timer = timer

    def getPollingInterval(self, timeframe: str) -> int:
        """타임프레임별 폴링 주기 (ms)"""
        intervals = {
            "1m": 10000,    # 10초
            "3m": 30000,    # 30초
            "5m": 60000,    # 1분
            "15m": 180000,  # 3분
            "30m": 300000,  # 5분
            "1h": 600000,   # 10분
            "4h": 1800000,  # 30분
            "1d": 3600000,  # 1시간
            "1w": 7200000,  # 2시간
            "1M": 21600000, # 6시간 (1개월)
        }
        return intervals.get(timeframe, 60000)

    async def pollApiData(self, symbol: str, timeframe: str):
        """API 데이터 폴링"""
        try:
            # 업비트 API 호출
            url = f"https://api.upbit.com/v1/candles/{timeframe}"
            params = {"market": symbol, "count": 1}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.processApiData(symbol, timeframe, data)

        except Exception as e:
            logger.error(f"API 폴링 실패 {symbol}_{timeframe}: {e}")

class CollectionState:
    """수집 상태 관리"""
    def __init__(self, symbol: str, timeframe: str):
        self.symbol = symbol
        self.timeframe = timeframe
        self.websocket_connected = False
        self.api_timer = None
        self.last_update = None
        self.data_cache = []
```

### 3. CacheManager (인메모리 캐시)
```python
from collections import defaultdict, deque
import numpy as np
from threading import RLock

class CacheManager:
    """
    고성능 인메모리 캐시
    Features:
    - LRU 기반 메모리 관리
    - NumPy 배열 기반 빠른 접근
    - 타임프레임별 독립 캐시
    - 스레드 세이프
    """

    def __init__(self, max_memory_mb: int = 500):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache = defaultdict(lambda: defaultdict(deque))
        self.access_times = {}
        self.lock = RLock()
        self.current_memory = 0

    def put(self, symbol: str, timeframe: str, data: np.ndarray):
        """데이터 캐시 저장"""
        with self.lock:
            key = f"{symbol}_{timeframe}"

            # 기존 데이터 제거
            if key in self.cache:
                old_data = self.cache[symbol][timeframe]
                if old_data:
                    self.current_memory -= old_data[-1].nbytes

            # 새 데이터 추가
            self.cache[symbol][timeframe] = data
            self.current_memory += data.nbytes
            self.access_times[key] = time.time()

            # 메모리 한계 체크
            self.enforceMemoryLimit()

    def get(self, symbol: str, timeframe: str, start_idx: int = 0,
            count: int = None) -> np.ndarray:
        """데이터 캐시 조회"""
        with self.lock:
            key = f"{symbol}_{timeframe}"

            if symbol in self.cache and timeframe in self.cache[symbol]:
                data = self.cache[symbol][timeframe]
                self.access_times[key] = time.time()

                # 슬라이싱 적용
                if count is None:
                    return data[start_idx:]
                else:
                    return data[start_idx:start_idx + count]

            return np.array([])

    def enforceMemoryLimit(self):
        """메모리 한계 강제"""
        while self.current_memory > self.max_memory_bytes:
            # LRU 아이템 제거
            oldest_key = min(self.access_times.keys(),
                           key=lambda k: self.access_times[k])

            symbol, timeframe = oldest_key.split("_", 1)
            old_data = self.cache[symbol][timeframe]

            if old_data is not None:
                self.current_memory -= old_data.nbytes

            del self.cache[symbol][timeframe]
            del self.access_times[oldest_key]

            if not self.cache[symbol]:
                del self.cache[symbol]
```

## 🎨 실시간 호가창 구현

### 4. OrderbookBarChart (PyQtGraph 기반)
```python
import pyqtgraph as pg
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor

class OrderbookBarChart(pg.PlotWidget):
    """
    실시간 호가창 바 차트
    Features:
    - 수평 바 차트로 호가량 표시
    - 매수/매도 색상 구분
    - 실시간 애니메이션 업데이트
    - 가격 클릭 이벤트
    """

    def __init__(self, order_type="buy"):
        super().__init__()
        self.order_type = order_type  # "buy" or "sell"
        self.setupChart()
        self.orderbook_data = []

    def setupChart(self):
        """차트 초기 설정"""
        # 축 설정
        self.setLabel('left', '가격')
        self.setLabel('bottom', '수량')

        # 색상 설정
        if self.order_type == "buy":
            self.bar_color = QColor(0, 150, 0, 180)    # 초록색 (매수)
        else:
            self.bar_color = QColor(200, 0, 0, 180)    # 빨간색 (매도)

        # 배경 설정
        self.setBackground('black')

        # 바 차트 아이템
        self.bar_items = []

    def updateOrderbook(self, orderbook_data):
        """호가 데이터 업데이트"""
        self.orderbook_data = orderbook_data
        self.redrawBars()

    def redrawBars(self):
        """바 차트 다시 그리기"""
        # 기존 바 제거
        for item in self.bar_items:
            self.removeItem(item)
        self.bar_items.clear()

        # 새 바 추가
        max_quantity = max([order['quantity'] for order in self.orderbook_data], default=1)

        for i, order in enumerate(self.orderbook_data):
            price = order['price']
            quantity = order['quantity']

            # 바의 너비 (수량에 비례)
            width = (quantity / max_quantity) * 100

            # 바 그래프 아이템 생성
            bar = pg.BarGraphItem(
                x=[0], y=[price],
                width=width, height=0.5,
                brush=self.bar_color
            )

            self.addItem(bar)
            self.bar_items.append(bar)

        # Y축 범위 조정
        if self.orderbook_data:
            prices = [order['price'] for order in self.orderbook_data]
            self.setYRange(min(prices) * 0.999, max(prices) * 1.001)

class OrderbookView(QWidget):
    """
    완전한 호가창 뷰
    Features:
    - 매수/매도 호가 분리 표시
    - 현재가 표시
    - 실시간 업데이트
    - 스프레드 정보
    """

    def __init__(self):
        super().__init__()
        self.setupUI()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.requestOrderbookUpdate)

    def setupUI(self):
        """UI 구성"""
        layout = QVBoxLayout(self)

        # 헤더
        header = QLabel("호가창")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # 매도 호가 (위쪽)
        sell_label = QLabel("매도 호가")
        layout.addWidget(sell_label)

        self.sell_chart = OrderbookBarChart("sell")
        self.sell_chart.setMaximumHeight(200)
        layout.addWidget(self.sell_chart)

        # 현재가 및 스프레드
        self.current_price_layout = QHBoxLayout()
        self.current_price_label = QLabel("현재가: -")
        self.spread_label = QLabel("스프레드: -")

        self.current_price_layout.addWidget(self.current_price_label)
        self.current_price_layout.addWidget(self.spread_label)
        layout.addLayout(self.current_price_layout)

        # 매수 호가 (아래쪽)
        buy_label = QLabel("매수 호가")
        layout.addWidget(buy_label)

        self.buy_chart = OrderbookBarChart("buy")
        self.buy_chart.setMaximumHeight(200)
        layout.addWidget(self.buy_chart)

    def startRealtime(self, symbol: str):
        """실시간 업데이트 시작"""
        self.symbol = symbol
        self.update_timer.start(100)  # 100ms 간격

    def stopRealtime(self):
        """실시간 업데이트 중지"""
        self.update_timer.stop()

    def updateOrderbook(self, orderbook_data):
        """호가 데이터 업데이트"""
        # 매수/매도 호가 분리
        buy_orders = orderbook_data.get('buy_orders', [])
        sell_orders = orderbook_data.get('sell_orders', [])

        # 차트 업데이트
        self.buy_chart.updateOrderbook(buy_orders)
        self.sell_chart.updateOrderbook(sell_orders)

        # 현재가 및 스프레드 업데이트
        if buy_orders and sell_orders:
            highest_buy = max([order['price'] for order in buy_orders])
            lowest_sell = min([order['price'] for order in sell_orders])

            current_price = (highest_buy + lowest_sell) / 2
            spread = lowest_sell - highest_buy
            spread_percent = (spread / current_price) * 100

            self.current_price_label.setText(f"현재가: {current_price:,.0f}")
            self.spread_label.setText(f"스프레드: {spread:,.0f} ({spread_percent:.2f}%)")
```

## 🔄 창 상태 기반 리소스 관리

### 5. WindowLifecycleManager (완전한 구현)
```python
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication

class WindowLifecycleManager(QObject):
    """
    창 생명주기 기반 리소스 관리
    Features:
    - 창 활성화/비활성화 감지
    - 메모리 사용량 모니터링
    - 백그라운드 모드 자동 전환
    - 리소스 사용량 로깅
    """

    stateChanged = pyqtSignal(str)  # active, background, minimized
    resourceUsageChanged = pyqtSignal(dict)  # 리소스 사용량 정보

    def __init__(self, window, market_data_backbone):
        super().__init__()
        self.window = window
        self.backbone = market_data_backbone
        self.current_state = "active"

        # 모니터링 타이머
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitorResources)
        self.monitor_timer.start(5000)  # 5초 간격

        # 창 이벤트 연결
        self.window.installEventFilter(self)

    def eventFilter(self, obj, event):
        """창 이벤트 필터링"""
        if obj == self.window:
            if event.type() == QEvent.WindowActivate:
                self.onWindowActivated()
            elif event.type() == QEvent.WindowDeactivate:
                self.onWindowDeactivated()
            elif event.type() == QEvent.WindowStateChange:
                self.onWindowStateChanged(event)

        return super().eventFilter(obj, event)

    def onWindowActivated(self):
        """창 활성화"""
        if self.current_state != "active":
            logger.info("차트뷰 활성화 - 전체 리소스 모드 복원")
            self.current_state = "active"
            self.restoreFullMode()
            self.stateChanged.emit("active")

    def onWindowDeactivated(self):
        """창 비활성화"""
        if self.current_state == "active":
            logger.info("차트뷰 비활성화 - 절약 모드 전환")
            self.current_state = "background"
            self.enterBackgroundMode()
            self.stateChanged.emit("background")

    def onWindowStateChanged(self, event):
        """창 상태 변경 (최소화 등)"""
        if self.window.isMinimized():
            if self.current_state != "minimized":
                logger.info("차트뷰 최소화 - 최소 리소스 모드")
                self.current_state = "minimized"
                self.enterMinimizedMode()
                self.stateChanged.emit("minimized")
        else:
            if self.current_state == "minimized":
                logger.info("차트뷰 복원")
                self.onWindowActivated()

    def restoreFullMode(self):
        """전체 리소스 모드 복원"""
        # 실시간 데이터 구독 재개
        chart_view = self.window.findChild(ChartAreaView)
        if chart_view:
            symbol = chart_view.current_symbol
            timeframe = chart_view.current_timeframe
            self.backbone.subscribe("chart_view", symbol, timeframe)

        # 호가창 실시간 업데이트 재개
        orderbook_view = self.window.findChild(OrderbookView)
        if orderbook_view:
            orderbook_view.startRealtime(symbol)

        # 고빈도 차트 렌더링 재개 (60fps)
        if chart_view:
            chart_view.setRenderInterval(16)  # 16ms = 60fps

    def enterBackgroundMode(self):
        """백그라운드 절약 모드"""
        # 저빈도 업데이트로 전환 (10초 간격)
        chart_view = self.window.findChild(ChartAreaView)
        if chart_view:
            chart_view.setRenderInterval(10000)  # 10초

        # 호가창 업데이트 빈도 감소
        orderbook_view = self.window.findChild(OrderbookView)
        if orderbook_view and hasattr(orderbook_view, 'update_timer'):
            orderbook_view.update_timer.setInterval(1000)  # 1초로 감소

    def enterMinimizedMode(self):
        """최소화 모드 (최소 리소스)"""
        # 모든 실시간 업데이트 중단
        chart_view = self.window.findChild(ChartAreaView)
        if chart_view:
            symbol = chart_view.current_symbol
            timeframe = chart_view.current_timeframe
            self.backbone.unsubscribe("chart_view", symbol, timeframe)

        # 호가창 업데이트 중단
        orderbook_view = self.window.findChild(OrderbookView)
        if orderbook_view:
            orderbook_view.stopRealtime()

    def monitorResources(self):
        """리소스 사용량 모니터링"""
        import psutil
        process = psutil.Process()

        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent()

        resource_info = {
            "state": self.current_state,
            "memory_mb": memory_info.rss / 1024 / 1024,
            "cpu_percent": cpu_percent,
            "active_subscriptions": len(self.backbone.subscribers)
        }

        self.resourceUsageChanged.emit(resource_info)

        # 메모리 한계 체크 (500MB)
        if resource_info["memory_mb"] > 500:
            logger.warning(f"메모리 사용량 한계 초과: {resource_info['memory_mb']:.1f}MB")
            self.backbone.cache_manager.enforceMemoryLimit()
```

---
*PyQtGraph 기반 고성능 실시간 차트뷰의 핵심 구현 방법들*
