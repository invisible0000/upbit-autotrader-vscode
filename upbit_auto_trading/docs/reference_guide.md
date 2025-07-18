# 레퍼런스 문서 활용 가이드

## 개요

`reference` 폴더에는 업비트 자동매매 시스템의 설계 및 구현에 필요한 상세 문서들이 포함되어 있습니다. 이 문서들은 시스템 아키텍처, 데이터베이스 스키마, API 명세, 화면 설계 등에 대한 상세 정보를 제공합니다. 이 가이드는 레퍼런스 문서를 효과적으로 활용하는 방법을 설명합니다.

> **참고**: 레퍼런스 문서는 정기적으로 업데이트됩니다. 최신 버전의 문서를 참조하여 개발을 진행하세요.

## 레퍼런스 문서 구성

레퍼런스 폴더에는 다음과 같은 문서들이 포함되어 있습니다:

1. **시스템 아키텍처 설계서** (`01_system_architecture_design.md`): C4 모델 기반으로 시스템의 전체적인 구조와 컴포넌트 간 관계를 설명
2. **데이터베이스 스키마 명세서** (`02_database_schema_specification_erd.md`): 데이터베이스 테이블 구조와 관계를 정의
3. **API 명세서** (`03_api_specification.md`): 외부 API 및 내부 API의 인터페이스를 정의
4. **배포 및 운영 가이드** (`04_deployment_and_operations_guide.md`): 시스템 배포 및 운영 방법을 설명
5. **보안 설계 문서** (`05_security_design_document.md`): 시스템의 보안 요구사항과 구현 방법을 설명
6. **화면 명세서** (`ui_spec_01_main_dashboard.md` 등): 각 화면의 UI 요소와 기능을 상세히 설명

## 데이터베이스 스키마 명세서 활용 방법

데이터베이스 스키마 명세서는 시스템의 데이터 모델과 테이블 구조를 이해하는 데 중요합니다. 이 문서는 ERD(Entity-Relationship Diagram)와 각 테이블의 상세 명세를 포함하고 있습니다.

### 데이터베이스 스키마 활용 단계

1. **ERD 검토**: 문서에 포함된 ERD를 통해 테이블 간의 관계를 파악합니다.
2. **테이블 구조 이해**: 각 테이블의 컬럼, 데이터 타입, 제약 조건을 확인합니다.
3. **관계 파악**: 테이블 간의 관계(1:1, 1:N, N:M)를 이해합니다.
4. **데이터 모델 구현**: SQLAlchemy 모델 클래스 구현 시 명세서를 참조합니다.

### 데이터베이스 스키마 예시

예를 들어, `Strategy` 테이블을 구현하는 경우:

```python
from sqlalchemy import Column, String, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Strategy(Base):
    """매매 전략 모델"""
    __tablename__ = 'strategy'
    
    # 데이터베이스 스키마 명세서의 컬럼 정의를 참조하여 구현
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parameters = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
```

## 화면 명세서 활용 방법

화면 명세서는 UI 구현 시 가장 중요한 참조 문서입니다. 각 화면 명세서는 다음과 같은 구조로 되어 있습니다:

1. **화면 개요**: 화면의 목적과 주요 기능을 설명
2. **UI 요소 및 기능 목록**: 화면에 포함된 모든 UI 요소와 그 기능을 표로 정리
3. **UI 요소 상세 설명 및 사용자 경험(UX)**: 각 UI 요소의 상세 설명과 사용자 경험 설계

### 화면 명세서 활용 단계

1. **요구사항 이해**: 화면 명세서의 '화면 개요' 섹션을 통해 해당 화면의 목적과 요구사항을 이해합니다.
2. **UI 요소 식별**: 'UI 요소 및 기능 목록' 표를 참조하여 구현해야 할 모든 UI 요소를 식별합니다.
3. **백엔드 연결 계획**: 각 UI 요소의 '연결 기능(Backend/API)' 열을 참조하여 UI와 백엔드 로직의 연결 방법을 계획합니다.
4. **사용자 경험 구현**: 'UI 요소 상세 설명 및 사용자 경험(UX)' 섹션을 참조하여 사용자 경험을 구현합니다.
5. **일관성 유지**: 화면 명세서에 정의된 요소 ID, 명칭, 설명을 그대로 코드에 반영하여 일관성을 유지합니다.

### 화면 명세서 예시

예를 들어, '메인 대시보드' 화면 명세서를 활용하여 대시보드 화면을 구현하는 경우:

1. 화면 명세서에서 정의한 요소 ID를 그대로 사용합니다:
   ```python
   # 화면 명세서의 요소 ID 활용
   self.total_assets_widget = TotalAssetsWidget()
   self.total_assets_widget.setObjectName("widget-total-assets")
   ```

2. 백엔드 연결 정보를 참조하여 데이터를 가져옵니다:
   ```python
   # 화면 명세서의 연결 기능 정보 활용
   from data_layer.collectors.upbit_api import UpbitAPI
   from business_logic.portfolio.portfolio_performance import PortfolioPerformance
   
   api = UpbitAPI()
   account_data = api.get_account()
   
   portfolio = PortfolioPerformance()
   total_value = portfolio.calculate_portfolio_performance(account_data)
   ```

3. 사용자 경험 설계를 참조하여 UI 동작을 구현합니다:
   ```python
   # 화면 명세서의 사용자 경험 설계 활용
   def _update_total_assets(self, value, change, change_percent):
       self.value_label.setText(f"{value:,} KRW")
       
       # 수익/손실에 따른 색상 변경 (화면 명세서 UX 참조)
       if change >= 0:
           self.change_label.setStyleSheet("color: green;")
       else:
           self.change_label.setStyleSheet("color: red;")
       
       self.change_label.setText(f"{change:+,} KRW ({change_percent:+.2f}%)")
   ```

## 시스템 아키텍처 설계서 활용 방법

시스템 아키텍처 설계서(`reference/01_system_architecture_design.md`)는 시스템의 전체적인 구조와 컴포넌트 간 관계를 이해하는 데 중요합니다. 이 문서는 Mermaid 다이어그램을 사용하여 시스템 구조를 시각적으로 표현하며, C4 모델 기반으로 시스템을 여러 레벨에서 설명합니다.

### 시스템 아키텍처 활용 단계

1. **계층 구조 이해**: 시스템의 계층 구조(UI 계층, 비즈니스 로직 계층, 데이터 계층)를 이해합니다.
2. **컴포넌트 식별**: 각 계층에 포함된 주요 컴포넌트와 그 역할을 식별합니다.
3. **데이터 흐름 파악**: 컴포넌트 간 데이터 흐름을 파악하여 기능 구현 시 참조합니다.
4. **기술 스택 확인**: 각 컴포넌트에 사용되는 기술 스택을 확인하여 구현에 활용합니다.
5. **다이어그램 활용**: Mermaid 다이어그램을 통해 시스템 구조를 시각적으로 이해합니다.

### 시스템 아키텍처 예시

예를 들어, 백테스트 실행 기능을 구현하는 경우:

1. 시스템 아키텍처 설계서의 '데이터 흐름 예시' 섹션을 참조하여 백테스트 실행 과정을 이해합니다.
2. 각 단계에 관련된 컴포넌트(BacktestRunner, DataCollector, DataProcessor, Strategy 등)를 식별합니다.
3. 컴포넌트 간 상호작용 방식을 참조하여 기능을 구현합니다.

```python
# 시스템 아키텍처 설계서의 데이터 흐름 참조
def run_backtest(self, strategy_id, symbol, timeframe, start_date, end_date, initial_capital):
    # 1. 설정 객체 생성
    config = BacktestConfig(strategy_id, symbol, timeframe, start_date, end_date, initial_capital)
    
    # 2. 시장 데이터 로드
    data_collector = DataCollector()
    market_data = data_collector.load_market_data(symbol, timeframe, start_date, end_date)
    
    # 3. 기술적 지표 계산
    data_processor = DataProcessor()
    processed_data = data_processor.calculate_indicators(market_data, self.strategy.required_indicators)
    
    # 4. 매매 신호 생성
    strategy = StrategyFactory.create_strategy(strategy_id)
    signals = strategy.generate_signals(processed_data)
    
    # 5. 가상 거래 시뮬레이션
    trades, equity_curve = self._simulate_trades(processed_data, signals, initial_capital)
    
    # 6. 결과 분석
    analyzer = BacktestAnalyzer()
    results = analyzer.analyze(trades, equity_curve, processed_data)
    
    return results
```

## 레퍼런스 문서와 스펙 문서의 관계

레퍼런스 폴더의 문서들은 `.kiro/specs/upbit-auto-trading/` 폴더의 스펙 문서(requirements.md, design.md, tasks.md)와 함께 활용해야 합니다:

1. **요구사항 문서(requirements.md)**: 시스템이 충족해야 할 기능적/비기능적 요구사항을 정의
2. **설계 문서(design.md)**: 시스템의 전체적인 설계와 아키텍처를 설명
3. **태스크 문서(tasks.md)**: 구현해야 할 태스크의 목록과 우선순위를 정의

레퍼런스 문서는 이러한 스펙 문서를 보완하여 더 상세한 정보를 제공합니다.

## 레퍼런스 문서 활용 시 주의사항

1. **최신성 확인**: 레퍼런스 문서가 현재 구현된 코드와 일치하는지 확인합니다. 불일치가 있다면 문서를 업데이트하거나 구현 시 조정합니다.
2. **우선순위 설정**: 모든 기능을 한 번에 구현하기보다 중요도와 의존성에 따라 순차적으로 구현합니다.
3. **반복적인 검증**: 각 기능 구현 후 레퍼런스 문서와 비교하여 누락된 요소가 없는지 확인합니다.
4. **문서 간 일관성**: 레퍼런스 문서와 스펙 문서 간의 일관성을 유지합니다. 불일치가 있다면 스펙 문서를 우선시합니다.

## 결론

레퍼런스 폴더의 문서들은 업비트 자동매매 시스템의 구현에 필요한 상세 정보를 제공합니다. 이 문서들을 효과적으로 활용하면 요구사항에 맞는 고품질의 시스템을 구현할 수 있습니다. 특히 UI 구현 시에는 화면 명세서를 적극 활용하여 일관된 사용자 경험을 제공하는 것이 중요합니다.
#
# 차트 뷰 구현 가이드

차트 뷰는 업비트 자동매매 시스템의 핵심 기능 중 하나로, 암호화폐의 가격 데이터를 시각화하고 기술적 지표를 분석하는 기능을 제공합니다. 차트 뷰 구현 시 다음과 같은 가이드를 참조하세요.

### 차트 뷰 컴포넌트 구조

차트 뷰는 다음과 같은 주요 컴포넌트로 구성됩니다:

1. **ChartViewScreen**: 차트 뷰의 메인 화면 클래스
2. **CandlestickChart**: 캔들스틱 차트 렌더링 클래스
3. **IndicatorOverlay**: 기술적 지표 오버레이 클래스
4. **TradeMarker**: 거래 시점 마커 클래스

### 차트 뷰 구현 시 참조 문서

차트 뷰 구현 시 다음 문서들을 참조하세요:

1. **화면 명세서: 02 - 차트 뷰**: 차트 뷰 화면의 UI 요소와 기능을 상세히 설명
2. **요구사항 8.2**: 다양한 시간대와 지표를 선택할 수 있는 옵션 제공
3. **요구사항 5.4**: 백테스팅 결과 표시 시 가격 차트와 거래 시점 시각화

### PyQtGraph 활용 방법

차트 뷰는 PyQtGraph 라이브러리를 사용하여 구현됩니다. PyQtGraph는 고성능 그래픽 및 GUI 라이브러리로, 실시간 데이터 시각화에 적합합니다.

```python
# PyQtGraph 기본 사용 예시
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication
import numpy as np

app = QApplication([])

# 플롯 위젯 생성
plot_widget = pg.PlotWidget()

# 데이터 생성
x = np.arange(100)
y = np.sin(x/10)

# 데이터 플롯
plot_widget.plot(x, y, pen='b')

# 위젯 표시
plot_widget.show()

# 애플리케이션 실행
app.exec()
```

### 캔들스틱 차트 구현 방법

캔들스틱 차트는 PyQtGraph의 `GraphicsObject`를 상속받아 구현합니다. 다음은 캔들스틱 차트 구현의 핵심 부분입니다:

```python
class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.picture = None
        self.generatePicture()
    
    def generatePicture(self):
        self.picture = pg.QtGui.QPicture()
        painter = pg.QtGui.QPainter(self.picture)
        
        # 각 캔들 그리기
        for i in range(len(self.data)):
            # 캔들 데이터 추출
            t = i
            open_price = self.data['open'].iloc[i]
            high_price = self.data['high'].iloc[i]
            low_price = self.data['low'].iloc[i]
            close_price = self.data['close'].iloc[i]
            
            # 상승/하락 여부 확인
            is_bull = close_price >= open_price
            color = self.bull_color if is_bull else self.bear_color
            
            # 캔들 몸통 그리기
            painter.setPen(pg.mkPen(color))
            painter.setBrush(pg.mkBrush(color))
            rect = QRectF(t - 0.4, min(open_price, close_price), 0.8, abs(close_price - open_price))
            painter.drawRect(rect)
            
            # 캔들 심지 그리기
            painter.setPen(pg.mkPen(color, width=1))
            painter.drawLine(QPointF(t, high_price), QPointF(t, max(open_price, close_price)))
            painter.drawLine(QPointF(t, min(open_price, close_price)), QPointF(t, low_price))
        
        painter.end()
    
    def paint(self, painter, option, widget):
        painter.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        # 데이터 범위 계산
        min_x = 0
        max_x = len(self.data)
        min_y = self.data['low'].min()
        max_y = self.data['high'].max()
        margin = (max_y - min_y) * 0.1
        
        return QRectF(min_x - 1, min_y - margin, max_x + 1, (max_y - min_y) + 2 * margin)
```

### 기술적 지표 구현 방법

기술적 지표는 pandas와 numpy를 사용하여 계산하고, PyQtGraph의 `plot` 메서드를 사용하여 시각화합니다:

```python
# 이동 평균 계산 및 시각화 예시
def add_moving_average(chart, data, window=20, color=(0, 0, 255)):
    # 이동 평균 계산
    ma = data.rolling(window=window).mean()
    
    # 차트에 플롯
    return chart.plot(
        x=range(len(ma)),
        y=ma.values,
        pen=pg.mkPen(color=color, width=2),
        name=f"MA({window})"
    )
```

### 거래 마커 구현 방법

거래 마커는 PyQtGraph의 `GraphicsObject`를 상속받아 구현합니다:

```python
class TradeMarker(pg.GraphicsObject):
    def __init__(self, timestamp, price, trade_type="buy", size=10):
        super().__init__()
        self.timestamp = timestamp
        self.price = price
        self.trade_type = trade_type  # "buy" 또는 "sell"
        self.size = size
        self.picture = None
        self.generatePicture()
    
    def generatePicture(self):
        self.picture = pg.QtGui.QPicture()
        painter = pg.QtGui.QPainter(self.picture)
        
        # 매수/매도에 따른 색상 및 모양 설정
        color = QColor(76, 175, 80) if self.trade_type == "buy" else QColor(244, 67, 54)
        
        # 삼각형 그리기
        painter.setPen(pg.mkPen(color, width=2))
        painter.setBrush(pg.mkBrush(color))
        
        half_size = self.size / 2
        if self.trade_type == "buy":
            # 매수 마커 (위쪽 방향 삼각형)
            triangle = QPolygonF([
                QPointF(0, -half_size),
                QPointF(-half_size, half_size),
                QPointF(half_size, half_size)
            ])
        else:
            # 매도 마커 (아래쪽 방향 삼각형)
            triangle = QPolygonF([
                QPointF(0, half_size),
                QPointF(-half_size, -half_size),
                QPointF(half_size, -half_size)
            ])
        
        painter.drawPolygon(triangle)
        painter.end()
    
    def paint(self, painter, option, widget):
        painter.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        half_size = self.size / 2
        return pg.QtCore.QRectF(-half_size, -half_size, self.size, self.size)
```

### 차트 뷰 구현 시 주의사항

1. **성능 최적화**: 대량의 데이터를 처리할 때 성능 이슈가 발생할 수 있으므로, 데이터 다운샘플링이나 뷰포트 최적화 기법을 적용합니다.
2. **메모리 관리**: 차트 업데이트 시 이전 아이템을 제거하고 새 아이템을 추가하여 메모리 누수를 방지합니다.
3. **예외 처리**: 데이터 로드 및 처리 과정에서 발생할 수 있는 예외를 적절히 처리합니다.
4. **UI 응답성**: 무거운 계산은 별도의 스레드에서 처리하여 UI 응답성을 유지합니다.
5. **타입 호환성**: PyQt6와 PyQtGraph 간의 타입 호환성 문제에 주의합니다. 특히 `drawLine` 메서드 사용 시 인자 타입을 올바르게 지정해야 합니다.

### 차트 뷰 테스트 방법

차트 뷰 구현 후에는 다음과 같은 테스트를 수행하여 기능을 검증합니다:

1. **기본 렌더링 테스트**: 캔들스틱 차트가 올바르게 렌더링되는지 확인
2. **지표 오버레이 테스트**: 기술적 지표가 올바르게 계산되고 표시되는지 확인
3. **거래 마커 테스트**: 거래 시점 마커가 올바른 위치에 표시되는지 확인
4. **상호작용 테스트**: 확대/축소, 이동 등의 상호작용이 정상 작동하는지 확인
5. **시간대 변경 테스트**: 다양한 시간대로 변경 시 차트가 올바르게 업데이트되는지 확인

자세한 내용은 `upbit_auto_trading/docs/chart_view_guide.md` 문서를 참조하세요.