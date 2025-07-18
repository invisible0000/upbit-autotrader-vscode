# 대시보드 구현 가이드

## 개요

대시보드는 사용자가 시스템에 로그인했을 때 가장 먼저 마주하는 화면으로, 전체 자산 현황, 포트폴리오 요약, 실시간 거래 성과, 시장 개요 등 핵심 정보를 한눈에 파악할 수 있도록 설계되었습니다. 이 문서는 대시보드 화면의 구조와 각 위젯의 사용 방법을 설명합니다.

## 대시보드 구조

대시보드는 다음과 같은 주요 위젯으로 구성됩니다:

1. **포트폴리오 요약 위젯 (PortfolioSummaryWidget)**: 보유 자산의 구성을 도넛 차트와 목록으로 표시
2. **활성 거래 목록 위젯 (ActivePositionsWidget)**: 현재 진행 중인 거래 포지션을 테이블로 표시
3. **시장 개요 위젯 (MarketOverviewWidget)**: 주요 코인들의 시세 정보를 테이블로 표시

## 위젯 상세 설명

### 포트폴리오 요약 위젯 (PortfolioSummaryWidget)

포트폴리오 요약 위젯은 사용자의 보유 자산 구성을 시각적으로 표현합니다.

#### 주요 기능
- 도넛 차트를 통한 자산 구성 시각화
- 코인별 비중 테이블 표시
- 코인 선택 시 차트 뷰로 이동 (시그널 발생)

#### 사용 방법
```python
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.portfolio_summary_widget import PortfolioSummaryWidget

# 위젯 생성
portfolio_widget = PortfolioSummaryWidget()

# 코인 선택 시그널 연결
portfolio_widget.coin_selected.connect(lambda symbol: print(f"선택된 코인: {symbol}"))

# 데이터 새로고침
portfolio_widget.refresh_data()
```

#### 데이터 형식
포트폴리오 데이터는 다음과 같은 형식으로 제공되어야 합니다:
```python
portfolio_data = [
    {"symbol": "BTC", "name": "비트코인", "weight": 45.0, "color": "#F7931A"},
    {"symbol": "ETH", "name": "이더리움", "weight": 30.0, "color": "#627EEA"},
    # ...
]
```

### 활성 거래 목록 위젯 (ActivePositionsWidget)

활성 거래 목록 위젯은 현재 진행 중인 모든 거래 포지션을 테이블 형태로 표시합니다.

#### 주요 기능
- 거래 포지션 테이블 표시 (코인, 진입 시간, 진입가, 현재가, 수량, 평가손익 등)
- 수익/손실 시각적 표시 (색상 구분)
- 포지션 청산 기능

#### 사용 방법
```python
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.active_positions_widget import ActivePositionsWidget

# 위젯 생성
positions_widget = ActivePositionsWidget()

# 포지션 청산 시그널 연결
positions_widget.position_closed.connect(lambda position_id: print(f"청산된 포지션: {position_id}"))

# 데이터 새로고침
positions_widget.refresh_data()
```

#### 데이터 형식
활성 거래 데이터는 다음과 같은 형식으로 제공되어야 합니다:
```python
positions_data = [
    {
        "id": "pos-001",
        "symbol": "BTC",
        "name": "비트코인",
        "entry_time": "2025-07-18 09:30:00",
        "entry_price": 50000000,
        "current_price": 51000000,
        "quantity": 0.01,
        "profit_loss": 2.0,
        "profit_loss_amount": 100000
    },
    # ...
]
```

### 시장 개요 위젯 (MarketOverviewWidget)

시장 개요 위젯은 주요 코인들의 시세 정보를 테이블 형태로 표시합니다.

#### 주요 기능
- 코인 시세 정보 테이블 표시 (코인, 현재가, 24시간 변동률, 24시간 거래대금 등)
- 상승/하락 시각적 표시 (색상 구분)
- 차트 보기 기능

#### 사용 방법
```python
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.market_overview_widget import MarketOverviewWidget

# 위젯 생성
market_widget = MarketOverviewWidget()

# 코인 선택 시그널 연결
market_widget.coin_selected.connect(lambda symbol: print(f"차트 보기: {symbol}"))

# 데이터 새로고침
market_widget.refresh_data()
```

#### 데이터 형식
시장 데이터는 다음과 같은 형식으로 제공되어야 합니다:
```python
market_data = [
    {
        "symbol": "BTC",
        "name": "비트코인",
        "current_price": 51000000,
        "change_24h": 2.5,
        "volume_24h": 1500000000000
    },
    # ...
]
```

## 대시보드 화면 통합

대시보드 화면은 위의 위젯들을 통합하여 구성됩니다.

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import QTimer

from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.portfolio_summary_widget import PortfolioSummaryWidget
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.active_positions_widget import ActivePositionsWidget
from upbit_auto_trading.ui.desktop.screens.dashboard.widgets.market_overview_widget import MarketOverviewWidget

class DashboardScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboard-screen")
        
        # UI 설정
        self._setup_ui()
        
        # 타이머 설정 (5초마다 데이터 갱신)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_all_widgets)
        self.refresh_timer.start(5000)  # 5초마다 갱신
    
    def _setup_ui(self):
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        
        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # 스크롤 영역 내부 위젯
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 위젯 추가
        self.portfolio_summary_widget = PortfolioSummaryWidget()
        self.active_positions_widget = ActivePositionsWidget()
        self.market_overview_widget = MarketOverviewWidget()
        
        scroll_layout.addWidget(self.portfolio_summary_widget)
        scroll_layout.addWidget(self.active_positions_widget)
        scroll_layout.addWidget(self.market_overview_widget)
        
        # 스크롤 영역 설정
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
    
    def refresh_all_widgets(self):
        """모든 위젯 새로고침"""
        self.portfolio_summary_widget.refresh_data()
        self.active_positions_widget.refresh_data()
        self.market_overview_widget.refresh_data()
```

## 백엔드 연동

실제 구현에서는 각 위젯의 `refresh_data()` 메서드에서 백엔드 API를 호출하여 실시간 데이터를 가져와야 합니다. 화면 명세서에 정의된 연결 기능(Backend/API)을 참조하여 다음과 같이 구현할 수 있습니다:

### 포트폴리오 요약 위젯 백엔드 연동
```python
from business_logic.portfolio.portfolio_manager import PortfolioManager
from business_logic.portfolio.portfolio_performance import PortfolioPerformance

def refresh_data(self):
    # 포트폴리오 목록 가져오기
    portfolio_manager = PortfolioManager()
    portfolios = portfolio_manager.get_all_portfolios()
    
    # 포트폴리오 성과 계산
    portfolio_performance = PortfolioPerformance()
    portfolio_data = []
    
    for portfolio in portfolios:
        performance = portfolio_performance.calculate_portfolio_performance(portfolio)
        portfolio_data.append({
            "symbol": portfolio.symbol,
            "name": portfolio.name,
            "weight": performance.weight,
            "color": self._get_color_for_symbol(portfolio.symbol)
        })
    
    # 데이터 업데이트
    self.portfolio_data = portfolio_data
    self._update_chart()
    self._update_table()
```

### 활성 거래 목록 위젯 백엔드 연동
```python
from business_logic.trader.trading_engine import TradingEngine

def refresh_data(self):
    # 활성 포지션 가져오기
    trading_engine = TradingEngine()
    positions = trading_engine.get_active_positions()
    
    # 데이터 변환
    positions_data = []
    for position in positions:
        positions_data.append({
            "id": position.id,
            "symbol": position.symbol,
            "name": position.name,
            "entry_time": position.entry_time.strftime("%Y-%m-%d %H:%M:%S"),
            "entry_price": position.entry_price,
            "current_price": position.current_price,
            "quantity": position.quantity,
            "profit_loss": position.profit_loss_percent,
            "profit_loss_amount": position.profit_loss_amount
        })
    
    # 데이터 업데이트
    self.positions_data = positions_data
    self._update_table()
```

### 시장 개요 위젯 백엔드 연동
```python
from data_layer.collectors.data_collector import DataCollector

def refresh_data(self):
    # 시장 데이터 가져오기
    data_collector = DataCollector()
    tickers = data_collector.get_ohlcv_data(symbols=["BTC", "ETH", "XRP", "ADA", "SOL", "DOT", "DOGE"])
    
    # 데이터 변환
    market_data = []
    for symbol, ticker in tickers.items():
        market_data.append({
            "symbol": symbol,
            "name": self._get_name_for_symbol(symbol),
            "current_price": ticker["close"].iloc[-1],
            "change_24h": ((ticker["close"].iloc[-1] / ticker["close"].iloc[-24]) - 1) * 100,
            "volume_24h": ticker["volume"].iloc[-24:].sum() * ticker["close"].iloc[-1]
        })
    
    # 데이터 업데이트
    self.market_data = market_data
    self._update_table()
```

## 테스트

대시보드 화면과 위젯에 대한 테스트는 `upbit_auto_trading/tests/integration/test_08_2_dashboard.py` 파일에 구현되어 있습니다. 테스트를 실행하려면 다음 명령어를 사용합니다:

```bash
python -m unittest upbit_auto_trading/tests/integration/test_08_2_dashboard.py
```

## 참고 사항

- 대시보드 화면은 5초마다 자동으로 데이터를 갱신합니다.
- 각 위젯은 독립적으로 사용할 수도 있고, 대시보드 화면에 통합하여 사용할 수도 있습니다.
- 실제 구현에서는 백엔드 API를 호출하여 실시간 데이터를 가져와야 합니다.
- 화면 명세서에 정의된 요소 ID와 연결 기능을 참조하여 구현해야 합니다.