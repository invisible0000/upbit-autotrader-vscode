# 차트뷰 기술 명세서
> 마켓 데이터 DB 및 실시간 API/WebSocket 연동 테스트용 차트뷰 기술 구현 방안

## 🛠️ 기술 스택 선정

### 1. 차트 라이브러리 비교 분석

| 라이브러리 | 장점 | 단점 | 적합성 |
|-----------|------|------|--------|
| **PyQtGraph** ⭐ | • PyQt6 네이티브 통합<br/>• 고성능 실시간 플롯팅<br/>• GPU 가속 지원<br/>• 확대/축소 내장 | • 캔들스틱 직접 구현 필요<br/>• 커스텀 차트 학습곡선 | **최적** |
| **mplfinance + Qt** | • 전문 금융차트<br/>• 캔들스틱 내장<br/>• 기술적 지표 풍부 | • Qt 통합 복잡<br/>• 실시간 성능 제한<br/>• 상호작용 제한적 | 보통 |
| **Plotly + QWebEngineView** | • 인터랙티브 차트<br/>• 웹 기반 UI<br/>• 호가창 구현 가능 | • 웹뷰 오버헤드<br/>• 실시간 성능 이슈<br/>• 복잡한 통합 | 보통 |

### 2. 최종 선택: **PyQtGraph 기반 커스텀 구현**

#### 선택 근거:
- **실시간 성능**: 60fps+ 업데이트 가능
- **PyQt6 네이티브**: 별도 의존성 없이 완전 통합
- **GPU 가속**: OpenGL 백엔드로 대량 데이터 처리
- **완전한 제어**: 호가창, 캔들스틱 등 모든 요소 커스터마이징 가능

#### 구현 방법:
```python
import pyqtgraph as pg
from pyqtgraph import PlotWidget, GraphicsObject
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
```

## 📦 필수 패키지 목록

### Core Dependencies
```txt
PyQt6>=6.4.0
pyqtgraph>=0.13.7
numpy>=1.24.0
pandas>=2.0.0
```

### Optional Enhanced Features
```txt
numba>=0.57.0          # 성능 최적화
talib>=0.4.25          # 기술적 지표 (C 구현)
pandas-ta>=0.3.14b     # 기술적 지표 (Python 구현)
websocket-client>=1.6.0 # WebSocket 클라이언트
aiohttp>=3.8.0         # 비동기 HTTP 클라이언트
```

## 🏗️ 상세 아키텍처 설계

### 1. 컴포넌트 구조
```
chart_viewer/
├── core/
│   ├── __init__.py
│   ├── chart_engine.py           # PyQtGraph 기반 차트 엔진
│   ├── data_manager.py           # 데이터 캐싱 및 관리
│   └── realtime_manager.py       # 실시간 데이터 스트림
├── widgets/
│   ├── __init__.py
│   ├── candlestick_item.py       # 커스텀 캔들스틱 그래픽 아이템
│   ├── volume_bars_item.py       # 거래량 바 차트
│   ├── orderbook_widget.py       # 호가창 위젯
│   ├── indicator_plots.py        # 기술적 지표 플롯
│   └── crosshair_item.py         # 십자선 커서
├── views/
│   ├── __init__.py
│   ├── main_chart_view.py        # 메인 차트 뷰
│   ├── coin_list_view.py         # 코인 리스트 뷰
│   ├── control_panel_view.py     # 상단 컨트롤
│   └── chart_viewer_window.py    # 메인 윈도우
├── presenters/
│   ├── __init__.py
│   ├── chart_presenter.py        # 차트 비즈니스 로직
│   ├── coin_list_presenter.py    # 리스트 관리 로직
│   └── realtime_presenter.py     # 실시간 데이터 처리
├── services/
│   ├── __init__.py
│   ├── market_data_service.py    # 마켓 데이터 API
│   ├── websocket_service.py      # WebSocket 연결
│   └── indicator_service.py      # 기술적 지표 계산
└── models/
    ├── __init__.py
    ├── chart_data.py             # 차트 데이터 모델
    ├── market_info.py            # 마켓 정보 모델
    └── indicator_data.py         # 지표 데이터 모델
```

### 2. 핵심 컴포넌트 설계

#### 2.1 CandlestickItem (PyQtGraph GraphicsObject)
```python
class CandlestickItem(pg.GraphicsObject):
    """
    Custom candlestick chart implementation for PyQtGraph
    Features:
    - High-performance rendering with QPainter
    - Real-time data updates
    - Custom styling (colors, thickness)
    - Hover interactions
    """

    def __init__(self):
        super().__init__()
        self.data = None
        self.bull_color = QColor(0, 150, 0)    # 상승 캔들
        self.bear_color = QColor(200, 0, 0)    # 하락 캔들

    def setData(self, ohlc_data):
        """OHLC 데이터 설정 및 화면 갱신"""
        pass

    def paint(self, painter, option, widget):
        """QPainter를 사용한 캔들스틱 렌더링"""
        pass

    def boundingRect(self):
        """바운딩 박스 계산"""
        pass
```

#### 2.4 WindowLifecycleManager (창 상태 기반 리소스 관리)
```python
class WindowLifecycleManager(QObject):
    """
    창 상태에 따른 리소스 관리
    Features:
    - 창 활성화/비활성화 감지
    - 자동 리소스 할당/해제
    - 백그라운드 모드 전환
    - 메모리 사용량 모니터링
    """

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.is_active = True
        self.background_mode = False

    def onWindowActivated(self):
        """창 활성화시 리소스 복원"""
        self.is_active = True
        self.restoreFullMode()

    def onWindowDeactivated(self):
        """창 비활성화시 리소스 절약 모드"""
        self.is_active = False
        self.enterBackgroundMode()

    def restoreFullMode(self):
        """전체 리소스 모드 복원"""
        # WebSocket 재연결
        # 실시간 업데이트 재개
        # 고빈도 차트 렌더링 재개
        pass

    def enterBackgroundMode(self):
        """백그라운드 절약 모드"""
        # WebSocket 최소 모드
        # 저빈도 업데이트 (10초 간격)
        # 차트 렌더링 중단
        pass
```

#### 2.5 MarketDataBackbone (통합 데이터 관리)
```python
class MarketDataBackbone(QObject):
    """
    마켓 데이터 통합 관리 백본
    Features:
    - 멀티소스 데이터 수집
    - 실시간 동기화
    - 타임프레임 변환
    - 구독/해제 관리
    """

    dataUpdated = pyqtSignal(str, dict)  # symbol, data

    def __init__(self):
        super().__init__()
        self.subscribers = {}
        self.cache_manager = CacheManager()
        self.data_collector = DataCollector()

    def subscribe(self, subscriber_id, symbol, timeframe):
        """데이터 구독"""
        key = f"{symbol}_{timeframe}"
        if key not in self.subscribers:
            self.subscribers[key] = set()
        self.subscribers[key].add(subscriber_id)

        # 첫 구독자면 데이터 수집 시작
        if len(self.subscribers[key]) == 1:
            self.data_collector.startCollection(symbol, timeframe)

    def unsubscribe(self, subscriber_id, symbol, timeframe):
        """데이터 구독 해제"""
        key = f"{symbol}_{timeframe}"
        if key in self.subscribers:
            self.subscribers[key].discard(subscriber_id)

            # 구독자가 없으면 수집 중단
            if not self.subscribers[key]:
                self.data_collector.stopCollection(symbol, timeframe)
                del self.subscribers[key]
```

#### 2.6 OrderbookWidget (호가창)
```python
class OrderbookWidget(QWidget):
    """
    실시간 호가창 위젯 (우측 패널 2 비율)
    Features:
    - 매수/매도 호가 표시
    - 호가량에 따른 바 차트
    - 실시간 업데이트 (WebSocket)
    - 가격 클릭 이벤트
    """

    def __init__(self):
        super().__init__()
        self.setupUI()
        self.orderbook_data = None

    def setupUI(self):
        """호가창 UI 구성"""
        layout = QVBoxLayout(self)

        # 매도 호가 (상단)
        self.sell_orders = pg.PlotWidget()
        self.sell_orders.setMaximumHeight(200)

        # 현재가 표시
        self.current_price_label = QLabel("현재가: -")

        # 매수 호가 (하단)
        self.buy_orders = pg.PlotWidget()
        self.buy_orders.setMaximumHeight(200)

        layout.addWidget(QLabel("매도 호가"))
        layout.addWidget(self.sell_orders)
        layout.addWidget(self.current_price_label)
        layout.addWidget(QLabel("매수 호가"))
        layout.addWidget(self.buy_orders)

    def updateOrderbook(self, orderbook_data):
        """실시간 호가 데이터 업데이트"""
        # 매수/매도 호가 바차트 업데이트
        pass
```
```
#### 2.6 OrderbookWidget (호가창)
    """
    실시간 호가창 위젯
    Features:
    - 매수/매도 호가 표시
    - 호가량에 따른 바 차트
    - 실시간 업데이트 (WebSocket)
    - 가격 클릭 이벤트
    """

    def __init__(self):
        super().__init__()
        self.setupUI()
        self.orderbook_data = None

    def setupUI(self):
        """호가창 UI 구성"""
        # PyQtGraph 기반 바 차트 or QTableWidget
        pass

    def updateOrderbook(self, orderbook_data):
        """실시간 호가 데이터 업데이트"""
        pass
```

#### 2.7 RealtimeManager (실시간 데이터 관리)
```python
class RealtimeManager(QObject):
    """
    실시간 데이터 스트림 관리
    Features:
    - WebSocket 연결 관리
    - API 폴링 (80% 빈도)
    - 데이터 병합 및 검증
    - 에러 처리 및 재연결
    """

    candleUpdated = pyqtSignal(dict)      # 캔들 업데이트 시그널
    orderbookUpdated = pyqtSignal(dict)   # 호가 업데이트 시그널

    def __init__(self):
        super().__init__()
        self.websocket_client = None
        self.api_timer = QTimer()

    def startWebSocket(self, symbol):
        """WebSocket 연결 시작"""
        pass

    def startAPIPolling(self, symbol, interval_ms):
        """API 폴링 시작 (80% 빈도)"""
        pass
```

## 🎨 UI/UX 구현 상세

### 1. 메인 레이아웃 구현 (1:4:2 비율)
```python
class ChartViewerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUI()
        self.lifecycle_manager = WindowLifecycleManager(self)

    def setupUI(self):
        # 1:4:2 비율 3열 스플리터
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 좌측: 코인 리스트 (1 비율)
        coin_list_widget = CoinListView()

        # 중앙: 차트 영역 (4 비율)
        chart_area = self.createChartArea()

        # 우측: 호가창 (2 비율)
        orderbook_widget = OrderbookView()

        main_splitter.addWidget(coin_list_widget)
        main_splitter.addWidget(chart_area)
        main_splitter.addWidget(orderbook_widget)
        main_splitter.setSizes([1, 4, 2])

        # 최소 크기 설정
        coin_list_widget.setMinimumWidth(200)
        chart_area.setMinimumWidth(400)
        orderbook_widget.setMinimumWidth(150)

        self.setCentralWidget(main_splitter)
```

### 2. 차트 영역 구성 (3:1 비율)
```python
def createChartArea(self):
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # 상단 컨트롤 (타임프레임, 데이터소스)
    control_panel = ControlPanelView()
    layout.addWidget(control_panel)

    # 차트 스플리터 (메인:서브 = 3:1)
    chart_splitter = QSplitter(Qt.Orientation.Vertical)

    # 메인 플롯 (캔들스틱 + 지표)
    main_plot = pg.PlotWidget()
    main_plot.addItem(CandlestickItem())

    # 서브 플롯 (거래량/MACD/RSI/ATR/STOCH)
    sub_plot = pg.PlotWidget()
    sub_plot.addItem(VolumeItem())

    chart_splitter.addWidget(main_plot)
    chart_splitter.addWidget(sub_plot)
    chart_splitter.setSizes([3, 1])

    layout.addWidget(chart_splitter)
    return widget
```

### 3. 실시간 상호작용 구현
```python
class ChartInteractionHandler:
    def __init__(self, plot_widget):
        self.plot = plot_widget
        self.setupInteractions()

    def setupInteractions(self):
        # 마우스 휠 이벤트
        self.plot.wheelEvent = self.wheelZoom

        # 마우스 드래그 이벤트
        self.plot.mousePressEvent = self.startPan
        self.plot.mouseMoveEvent = self.panChart

        # 십자선 커서
        self.crosshair = CrosshairItem()
        self.plot.addItem(self.crosshair)

    def wheelZoom(self, event):
        """마우스 휠로 확대/축소"""
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        self.plot.scaleBy((zoom_factor, 1.0))

        # 스케일 변경시 추가 데이터 로딩
        self.requestMoreData()

    def requestMoreData(self):
        """차트 범위 변경시 추가 데이터 요청"""
        view_range = self.plot.getViewBox().viewRange()
        # DB에서 추가 캔들 데이터 로딩
        pass
```

## 📊 데이터 플로우 설계

### 1. 실시간 데이터 파이프라인
```
WebSocket → RealtimeManager → DataValidator → ChartPresenter → ChartView
     ↓              ↓               ↓              ↓             ↓
API Polling → DataMerger → DatabaseCache → SignalEmitter → UIUpdate
```

### 2. 히스토리 데이터 로딩
```
UserScroll → ViewRangeChanged → DataRequest → SQLiteQuery → DataCache → ChartUpdate
```

### 3. 기술적 지표 계산
```
OHLC Data → IndicatorService → [TA-Lib/pandas-ta] → IndicatorCache → SubplotUpdate
```

## ⚡ 성능 최적화 전략

### 1. 렌더링 최적화
- **LOD (Level of Detail)**: 확대 수준에 따라 렌더링 디테일 조정
- **Viewport Culling**: 화면 밖 데이터 렌더링 스킵
- **Batch Rendering**: 다중 캔들을 한 번에 렌더링

### 2. 데이터 최적화
- **Lazy Loading**: 필요한 시점에만 데이터 로딩
- **데이터 압축**: NumPy 배열 활용으로 메모리 최적화
- **LRU Cache**: 최근 사용 데이터 캐싱

### 3. 실시간 최적화
- **Throttling**: UI 업데이트 빈도 제한 (60fps)
- **Background Processing**: 지표 계산 백그라운드 처리
- **Connection Pooling**: API/WebSocket 연결 재사용

## 🔧 개발 단계별 구현 계획

### Phase 1: 마켓 데이터 백본 구축 (3-4일)
- [ ] 데이터 수집 엔진 구현
- [ ] 멀티소스 데이터 동기화
- [ ] 메모리 캐시 시스템
- [ ] 타임프레임 변환 로직
- [ ] 구독/해제 관리 시스템

### Phase 2: 동적 3열 레이아웃 (2-3일)
- [ ] 1:4:2 비율 QSplitter 구현
- [ ] 창 상태 기반 리소스 관리
- [ ] 최소 크기 및 리사이즈 처리
- [ ] 레이아웃 설정 저장/복원

### Phase 3: PyQtGraph 차트 엔진 (3-4일)
- [ ] CandlestickItem 커스텀 구현
- [ ] 백본과 차트뷰 연동
- [ ] 200개 초기 데이터 로딩
- [ ] 타임프레임 선택 (1M 포함)
- [ ] 서브플롯 (거래량)

### Phase 4: 실시간 연동 및 호가창 (3-4일)
- [ ] 실시간 캔들 업데이트
- [ ] 호가창 바차트 구현
- [ ] WebSocket/API 하이브리드 모드
- [ ] 창 활성화 상태별 리소스 제어

### Phase 5: 코인 리스트 및 상호작용 (2-3일)
- [ ] 마켓 선택 및 검색 필터
- [ ] 즐겨찾기 기능
- [ ] 마우스 상호작용 (확대/축소/팬)
- [ ] 호가 클릭 이벤트

### Phase 6: 고급 기능 및 최적화 (4-5일)
- [ ] 기술적 지표 (MACD, RSI, ATR, STOCH)
- [ ] 이동평균선, 볼린저밴드
- [ ] 성능 최적화 및 메모리 관리
- [ ] 에러 처리 강화

### Phase 7: 테스트 및 안정화 (2-3일)
- [ ] 마켓 데이터 백본 스트레스 테스트
- [ ] 장시간 실행 안정성 테스트
- [ ] 메모리 누수 검사
- [ ] 동적 레이아웃 테스트
- [ ] 문서화

## 🎯 기술적 도전 과제 및 해결 방안

### 1. 호가창 구현
**도전**: PyQtGraph에서 복잡한 호가 바차트 구현
**해결**:
- CustomGraphicsItem으로 호가 바 구현
- QPainterPath 활용한 효율적 렌더링
- 색상 그라데이션으로 호가량 시각화

### 2. 실시간 성능
**도전**: 고빈도 데이터 업데이트시 UI 지연
**해결**:
- QTimer 기반 배치 업데이트 (16ms = 60fps)
- Dirty Flag 패턴으로 불필요한 렌더링 방지
- Background Thread에서 지표 계산

### 3. 메모리 관리
**도전**: 대량 히스토리 데이터 메모리 사용량
**해결**:
- Sliding Window 방식 (최대 10,000 캔들)
- WeakReference 기반 캐시
- NumPy 뷰 활용한 메모리 공유

## 📋 최종 검증 체크리스트

### 기능 검증
- [ ] 코인 선택시 차트 즉시 표시
- [ ] WebSocket/API 동시 연동 정상 동작
- [ ] 마우스 상호작용 부드러운 동작
- [ ] 실시간 캔들 업데이트 (< 1초 지연)
- [ ] 기술적 지표 정확한 계산

### 성능 검증
- [ ] 60fps 이상 부드러운 차트 업데이트
- [ ] 10,000+ 캔들 로딩시 < 2초
- [ ] 메모리 사용량 < 500MB
- [ ] CPU 사용률 < 10% (idle 상태)

### 안정성 검증
- [ ] 연속 24시간 실행 안정성
- [ ] 네트워크 연결 오류 복구
- [ ] 대량 데이터 처리 안정성
- [ ] UI 응답성 유지

---
*PyQtGraph 기반 고성능 실시간 차트뷰 구현으로 업비트 차트 수준의 UX 제공 목표*
