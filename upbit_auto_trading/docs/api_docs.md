# API 문서

## 데이터 계층 API

### 데이터 수집기 (Collectors)

#### UpbitAPI 클래스

업비트 API를 통해 시장 데이터를 수집하는 클래스입니다.

```python
from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI

# 인스턴스 생성
api = UpbitAPI(access_key="your_access_key", secret_key="your_secret_key")

# 시장 데이터 수집
candles = api.get_candles(symbol="KRW-BTC", timeframe="1h", count=200)

# 호가 데이터 수집
orderbook = api.get_orderbook(symbol="KRW-BTC")

# 티커 데이터 수집
tickers = api.get_tickers(symbols=["KRW-BTC", "KRW-ETH"])
```

**주요 메서드:**

- `get_candles(symbol: str, timeframe: str, count: int = 200) -> pd.DataFrame`: 캔들 데이터 조회
  - `symbol`: 코인 심볼 (예: "KRW-BTC")
  - `timeframe`: 시간대 (예: "1m", "5m", "15m", "1h", "4h", "1d")
  - `count`: 조회할 캔들 개수 (최대 200)
  - 반환값: OHLCV 데이터가 포함된 DataFrame

- `get_orderbook(symbol: str) -> Dict`: 호가 데이터 조회
  - `symbol`: 코인 심볼 (예: "KRW-BTC")
  - 반환값: 호가 정보가 포함된 딕셔너리

- `get_tickers(symbols: List[str] = None) -> pd.DataFrame`: 티커 데이터 조회
  - `symbols`: 코인 심볼 목록 (None인 경우 모든 KRW 마켓 코인)
  - 반환값: 티커 정보가 포함된 DataFrame

### 데이터 처리기 (Processors)

#### TechnicalIndicator 클래스

기술적 지표를 계산하는 클래스입니다.

```python
from upbit_auto_trading.data_layer.processors.technical_indicator import TechnicalIndicator

# 인스턴스 생성
indicator = TechnicalIndicator()

# 이동 평균 계산
data_with_sma = indicator.add_sma(data, window=20, column="close")

# RSI 계산
data_with_rsi = indicator.add_rsi(data, window=14)

# 볼린저 밴드 계산
data_with_bb = indicator.add_bollinger_bands(data, window=20, num_std=2)
```

**주요 메서드:**

- `add_sma(data: pd.DataFrame, window: int, column: str = "close") -> pd.DataFrame`: 단순 이동 평균 계산
  - `data`: OHLCV 데이터
  - `window`: 이동 평균 기간
  - `column`: 계산에 사용할 컬럼 이름
  - 반환값: SMA 컬럼이 추가된 DataFrame

- `add_rsi(data: pd.DataFrame, window: int = 14) -> pd.DataFrame`: RSI 계산
  - `data`: OHLCV 데이터
  - `window`: RSI 계산 기간
  - 반환값: RSI 컬럼이 추가된 DataFrame

- `add_bollinger_bands(data: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame`: 볼린저 밴드 계산
  - `data`: OHLCV 데이터
  - `window`: 이동 평균 기간
  - `num_std`: 표준 편차 배수
  - 반환값: 볼린저 밴드 컬럼이 추가된 DataFrame

### 데이터 저장소 (Storage)

#### DatabaseManager 클래스

데이터베이스 연결 및 관리를 담당하는 클래스입니다.

```python
from upbit_auto_trading.data_layer.storage.database_manager import DatabaseManager

# 인스턴스 생성
db_manager = DatabaseManager(config_path="config/config.yaml")

# 데이터베이스 연결
engine = db_manager.get_engine()

# 세션 생성
session = db_manager.get_session()

# 데이터베이스 초기화
db_manager.initialize_database()
```

**주요 메서드:**

- `get_engine() -> Engine`: SQLAlchemy 엔진 반환
- `get_session() -> Session`: SQLAlchemy 세션 반환
- `initialize_database() -> None`: 데이터베이스 스키마 초기화

#### MarketDataRepository 클래스

시장 데이터 저장 및 조회를 담당하는 클래스입니다.

```python
from upbit_auto_trading.data_layer.storage.market_data_repository import MarketDataRepository

# 인스턴스 생성
repository = MarketDataRepository(db_manager)

# 캔들 데이터 저장
repository.save_candles(candles_df, symbol="KRW-BTC", timeframe="1h")

# 캔들 데이터 조회
candles = repository.get_candles(symbol="KRW-BTC", timeframe="1h", start_date="2023-01-01", end_date="2023-01-31")

# 오래된 데이터 정리
deleted_count = repository.cleanup_old_data(days_to_keep=90)
```

**주요 메서드:**

- `save_candles(candles: pd.DataFrame, symbol: str, timeframe: str) -> bool`: 캔들 데이터 저장
  - `candles`: OHLCV 데이터
  - `symbol`: 코인 심볼
  - `timeframe`: 시간대
  - 반환값: 저장 성공 여부

- `get_candles(symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame`: 캔들 데이터 조회
  - `symbol`: 코인 심볼
  - `timeframe`: 시간대
  - `start_date`: 시작 날짜 (YYYY-MM-DD 형식)
  - `end_date`: 종료 날짜 (YYYY-MM-DD 형식)
  - 반환값: OHLCV 데이터가 포함된 DataFrame

- `cleanup_old_data(days_to_keep: int = 90) -> int`: 오래된 데이터 정리
  - `days_to_keep`: 보관할 데이터 기간 (일)
  - 반환값: 삭제된 레코드 수

## 비즈니스 로직 계층 API

### 스크리너 (Screener)

#### MarketScreener 클래스

거래량, 변동성, 가격 추세 등을 기반으로 코인을 필터링하는 클래스입니다.

```python
from upbit_auto_trading.business_logic.screener.market_screener import MarketScreener

# 인스턴스 생성
screener = MarketScreener(upbit_api, market_data_repository)

# 거래량 기준 스크리닝
volume_coins = screener.screen_by_volume(min_volume=1000000000, timeframe="1d")

# 변동성 기준 스크리닝
volatility_coins = screener.screen_by_volatility(min_volatility=0.05, max_volatility=0.20, timeframe="1d")

# 추세 기준 스크리닝
trend_coins = screener.screen_by_trend(trend_type="uptrend", timeframe="1d")

# 복합 기준 스크리닝
criteria = [
    {
        "type": "volume",
        "params": {
            "min_volume": 1000000000,
            "timeframe": "1d"
        }
    },
    {
        "type": "volatility",
        "params": {
            "min_volatility": 0.05,
            "max_volatility": 0.20,
            "timeframe": "1d"
        }
    }
]
screened_coins = screener.get_screened_coins(criteria)
```

**주요 메서드:**

- `screen_by_volume(min_volume: float, timeframe: str) -> List[str]`: 거래량 기준 스크리닝
  - `min_volume`: 최소 거래량 (KRW)
  - `timeframe`: 시간대
  - 반환값: 필터링된 코인 심볼 목록

- `screen_by_volatility(min_volatility: float, max_volatility: float, timeframe: str) -> List[str]`: 변동성 기준 스크리닝
  - `min_volatility`: 최소 변동성
  - `max_volatility`: 최대 변동성
  - `timeframe`: 시간대
  - 반환값: 필터링된 코인 심볼 목록

- `screen_by_trend(trend_type: str, timeframe: str) -> List[str]`: 추세 기준 스크리닝
  - `trend_type`: 추세 유형 ("uptrend", "downtrend", "sideways")
  - `timeframe`: 시간대
  - 반환값: 필터링된 코인 심볼 목록

- `get_screened_coins(criteria: List[Dict]) -> List[Dict]`: 복합 기준 스크리닝
  - `criteria`: 스크리닝 기준 목록
  - 반환값: 필터링된 코인 정보 목록

### 전략 관리 (Strategy)

#### StrategyManager 클래스

매매 전략을 생성, 수정, 저장, 관리하는 클래스입니다.

```python
from upbit_auto_trading.business_logic.strategy.strategy_manager import StrategyManager

# 인스턴스 생성
strategy_manager = StrategyManager(strategy_repository)

# 전략 생성
strategy_id = strategy_manager.create_strategy(
    name="이동 평균 교차 전략",
    description="단기 이동 평균이 장기 이동 평균을 상향 돌파하면 매수, 하향 돌파하면 매도",
    parameters={
        "strategy_type": "moving_average_crossover",
        "params": {
            "short_window": 20,
            "long_window": 50,
            "signal_line": 9
        }
    }
)

# 전략 수정
strategy_manager.update_strategy(
    strategy_id=strategy_id,
    parameters={
        "strategy_type": "moving_average_crossover",
        "params": {
            "short_window": 10,
            "long_window": 30,
            "signal_line": 9
        }
    }
)

# 전략 조회
strategy = strategy_manager.get_strategy(strategy_id)

# 모든 전략 조회
strategies = strategy_manager.get_strategies()

# 전략 삭제
strategy_manager.delete_strategy(strategy_id)
```

**주요 메서드:**

- `create_strategy(name: str, description: str, parameters: Dict) -> str`: 전략 생성
  - `name`: 전략 이름
  - `description`: 전략 설명
  - `parameters`: 전략 매개변수
  - 반환값: 생성된 전략 ID

- `update_strategy(strategy_id: str, parameters: Dict) -> bool`: 전략 수정
  - `strategy_id`: 전략 ID
  - `parameters`: 수정할 전략 매개변수
  - 반환값: 수정 성공 여부

- `get_strategy(strategy_id: str) -> Dict`: 전략 조회
  - `strategy_id`: 전략 ID
  - 반환값: 전략 정보

- `get_strategies() -> List[Dict]`: 모든 전략 조회
  - 반환값: 전략 목록

- `delete_strategy(strategy_id: str) -> bool`: 전략 삭제
  - `strategy_id`: 전략 ID
  - 반환값: 삭제 성공 여부

### 백테스터 (Backtester) - 구현 완료

#### BacktestRunner 클래스

전략을 과거 데이터에 적용하여 백테스팅을 실행하고 결과를 생성하는 클래스입니다. 모든 기능이 구현되어 테스트 완료되었습니다.

```python
from upbit_auto_trading.business_logic.backtester import BacktestRunner
from upbit_auto_trading.business_logic.strategy.strategy_factory import StrategyFactory

# 전략 가져오기
strategy_factory = StrategyFactory(session)
strategy = strategy_factory.get_strategy("strategy-123", session)

# 백테스트 설정
config = {
    "symbol": "KRW-BTC",
    "timeframe": "1h",
    "start_date": datetime(2023, 1, 1),
    "end_date": datetime(2023, 3, 31),
    "initial_capital": 10000000,
    "fee_rate": 0.0005,
    "slippage": 0.0002
}

# 백테스트 실행기 생성
backtest_runner = BacktestRunner(strategy, config)

# 백테스트 실행
result = backtest_runner.execute_backtest()

# 백테스트 결과 저장
result_id = backtest_runner.save_backtest_result(result, session)

# 백테스트 결과 불러오기
loaded_result = backtest_runner.load_backtest_result(result_id, session)
```

**주요 메서드:**

- `execute_backtest() -> Dict[str, Any]`: 백테스트 실행
  - 반환값: 백테스트 결과 딕셔너리 (거래 내역, 성과 지표, 자본 곡선 등)

- `save_backtest_result(result: Dict[str, Any], session) -> str`: 백테스트 결과 저장
  - `result`: 백테스트 결과 딕셔너리
  - `session`: SQLAlchemy 세션
  - 반환값: 저장된 결과 ID

- `load_backtest_result(result_id: str, session) -> Dict[str, Any]`: 백테스트 결과 불러오기
  - `result_id`: 결과 ID
  - `session`: SQLAlchemy 세션
  - 반환값: 백테스트 결과 딕셔너리

#### BacktestAnalyzer 클래스

백테스트 결과를 분석하고 시각화하는 클래스입니다. 모든 기능이 구현되어 테스트 완료되었습니다.

```python
from upbit_auto_trading.business_logic.backtester import BacktestAnalyzer

# 백테스트 결과 분석기 생성
analyzer = BacktestAnalyzer(backtest_result)

# 고급 성과 지표 계산
advanced_metrics = analyzer.calculate_advanced_metrics()

# 거래 내역 분석
trade_analysis = analyzer.analyze_trades()

# 손실폭(Drawdown) 분석
drawdowns = analyzer.analyze_drawdowns()

# 월별 수익률 분석
monthly_returns = analyzer.analyze_monthly_returns()

# 자본 곡선 시각화
equity_curve_fig = analyzer.plot_equity_curve()

# 보고서 생성
report = analyzer.generate_report()
```

**주요 메서드:**

- `calculate_advanced_metrics() -> Dict[str, Any]`: 고급 성과 지표 계산
  - 반환값: 고급 성과 지표 딕셔너리

- `analyze_trades() -> Dict[str, Any]`: 거래 내역 분석
  - 반환값: 거래 분석 결과 딕셔너리

- `analyze_drawdowns() -> pd.DataFrame`: 손실폭(Drawdown) 분석
  - 반환값: 손실폭 분석 결과 DataFrame

- `analyze_monthly_returns() -> pd.DataFrame`: 월별 수익률 분석
  - 반환값: 월별 수익률 분석 결과 DataFrame

- `plot_equity_curve() -> Figure`: 자본 곡선 시각화
  - 반환값: matplotlib Figure 객체

- `generate_report() -> Dict[str, Any]`: 백테스트 결과 보고서 생성
  - 반환값: 보고서 딕셔너리

#### BacktestResultsManager 클래스

백테스트 결과를 저장, 불러오기, 비교하는 기능을 제공하는 클래스입니다. 모든 기능이 구현되어 테스트 완료되었습니다.

```python
from upbit_auto_trading.business_logic.backtester import BacktestResultsManager

# 백테스트 결과 관리자 생성
results_manager = BacktestResultsManager(session)

# 백테스트 결과 저장
result_id = results_manager.save_backtest_result(backtest_result)

# 백테스트 결과 불러오기
loaded_result = results_manager.load_backtest_result(result_id)

# 포트폴리오 백테스트 결과 저장
portfolio_result_id = results_manager.save_portfolio_backtest_result(portfolio_backtest_result)

# 포트폴리오 백테스트 결과 불러오기
loaded_portfolio_result = results_manager.load_portfolio_backtest_result(portfolio_result_id)

# 백테스트 결과 목록 조회
results_list = results_manager.list_backtest_results()

# 백테스트 결과 비교
comparison = results_manager.compare_backtest_results(["backtest-1", "backtest-2"])

# 백테스트 결과 삭제
success = results_manager.delete_backtest_result(result_id)
```

**주요 메서드:**

- `save_backtest_result(result: Dict[str, Any]) -> str`: 백테스트 결과 저장
  - `result`: 백테스트 결과 딕셔너리
  - 반환값: 저장된 결과 ID

- `load_backtest_result(result_id: str) -> Dict[str, Any]`: 백테스트 결과 불러오기
  - `result_id`: 결과 ID
  - 반환값: 백테스트 결과 딕셔너리

- `save_portfolio_backtest_result(result: Dict[str, Any]) -> str`: 포트폴리오 백테스트 결과 저장
  - `result`: 포트폴리오 백테스트 결과 딕셔너리
  - 반환값: 저장된 결과 ID

- `load_portfolio_backtest_result(result_id: str) -> Dict[str, Any]`: 포트폴리오 백테스트 결과 불러오기
  - `result_id`: 결과 ID
  - 반환값: 포트폴리오 백테스트 결과 딕셔너리

- `list_backtest_results(filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`: 백테스트 결과 목록 조회
  - `filter_params`: 필터링 매개변수 (예: {"symbol": "KRW-BTC", "timeframe": "1h"})
  - 반환값: 백테스트 결과 요약 목록

- `compare_backtest_results(result_ids: List[str]) -> Dict[str, Any]`: 백테스트 결과 비교
  - `result_ids`: 비교할 백테스트 결과 ID 목록
  - 반환값: 비교 결과 딕셔너리

- `delete_backtest_result(result_id: str) -> bool`: 백테스트 결과 삭제
  - `result_id`: 결과 ID
  - 반환값: 삭제 성공 여부

### 거래 엔진 (Trader)

#### TradingEngine 클래스

실시간 시장 모니터링 및 주문 실행을 담당하는 클래스입니다.

```python
from upbit_auto_trading.business_logic.trader.trading_engine import TradingEngine

# 인스턴스 생성
trading_engine = TradingEngine(upbit_api, strategy_manager)

# 거래 시작
trading_id = trading_engine.start_trading(
    strategy_id="strategy-123",
    symbol="KRW-BTC",
    amount=1000000,
    risk_params={
        "max_loss_percent": 5.0,
        "take_profit_percent": 10.0,
        "stop_loss_percent": 3.0,
        "max_position_size": 0.3
    }
)

# 주문 실행
order = trading_engine.execute_order(
    symbol="KRW-BTC",
    order_type="market",
    side="buy",
    amount=100000
)

# 거래 상태 조회
status = trading_engine.get_trading_status(trading_id)

# 거래 중지
trading_engine.stop_trading(trading_id)
```

**주요 메서드:**

- `start_trading(strategy_id: str, symbol: str, amount: float, risk_params: Dict) -> str`: 거래 시작
  - `strategy_id`: 전략 ID
  - `symbol`: 코인 심볼
  - `amount`: 거래 금액
  - `risk_params`: 위험 관리 설정
  - 반환값: 거래 ID

- `execute_order(symbol: str, order_type: str, side: str, amount: float, price: float = None) -> Dict`: 주문 실행
  - `symbol`: 코인 심볼
  - `order_type`: 주문 유형 ("market", "limit")
  - `side`: 주문 방향 ("buy", "sell")
  - `amount`: 주문 금액
  - `price`: 주문 가격 (지정가 주문인 경우)
  - 반환값: 주문 정보

- `get_trading_status(trading_id: str) -> Dict`: 거래 상태 조회
  - `trading_id`: 거래 ID
  - 반환값: 거래 상태 정보

- `stop_trading(trading_id: str) -> bool`: 거래 중지
  - `trading_id`: 거래 ID
  - 반환값: 중지 성공 여부

### 포트폴리오 관리 (Portfolio)

#### PortfolioManager 클래스

여러 코인과 전략 조합을 관리하는 클래스입니다.

```python
from upbit_auto_trading.business_logic.portfolio.portfolio_manager import PortfolioManager

# 인스턴스 생성
portfolio_manager = PortfolioManager(portfolio_repository, strategy_manager)

# 포트폴리오 생성
portfolio_id = portfolio_manager.create_portfolio(
    name="균형 포트폴리오",
    description="대형 코인과 중소형 코인의 균형 배분"
)

# 코인 추가
portfolio_manager.add_coin_to_portfolio(
    portfolio_id=portfolio_id,
    symbol="KRW-BTC",
    strategy_id="strategy-123",
    weight=0.4
)

# 코인 가중치 수정
portfolio_manager.update_coin_weight(
    portfolio_id=portfolio_id,
    symbol="KRW-BTC",
    weight=0.5
)

# 포트폴리오 성과 계산
performance = portfolio_manager.calculate_portfolio_performance(portfolio_id)

# 코인 제거
portfolio_manager.remove_coin_from_portfolio(
    portfolio_id=portfolio_id,
    symbol="KRW-BTC"
)
```

**주요 메서드:**

- `create_portfolio(name: str, description: str) -> str`: 포트폴리오 생성
  - `name`: 포트폴리오 이름
  - `description`: 포트폴리오 설명
  - 반환값: 생성된 포트폴리오 ID

- `add_coin_to_portfolio(portfolio_id: str, symbol: str, strategy_id: str, weight: float) -> bool`: 포트폴리오에 코인 추가
  - `portfolio_id`: 포트폴리오 ID
  - `symbol`: 코인 심볼
  - `strategy_id`: 전략 ID
  - `weight`: 가중치
  - 반환값: 추가 성공 여부

- `update_coin_weight(portfolio_id: str, symbol: str, weight: float) -> bool`: 코인 가중치 수정
  - `portfolio_id`: 포트폴리오 ID
  - `symbol`: 코인 심볼
  - `weight`: 새 가중치
  - 반환값: 수정 성공 여부

- `calculate_portfolio_performance(portfolio_id: str) -> Dict`: 포트폴리오 성과 계산
  - `portfolio_id`: 포트폴리오 ID
  - 반환값: 포트폴리오 성과 지표

- `remove_coin_from_portfolio(portfolio_id: str, symbol: str) -> bool`: 포트폴리오에서 코인 제거
  - `portfolio_id`: 포트폴리오 ID
  - `symbol`: 코인 심볼
  - 반환값: 제거 성공 여부## 사
용자 인터페이스 계층 API

### 메인 애플리케이션 프레임워크

#### MainWindow 클래스

애플리케이션의 메인 윈도우를 관리하는 클래스입니다.

```python
from upbit_auto_trading.ui.desktop.main_window import MainWindow
from PyQt6.QtWidgets import QApplication

# 애플리케이션 생성
app = QApplication([])

# 메인 윈도우 생성
main_window = MainWindow()

# 메인 윈도우 표시
main_window.show()

# 애플리케이션 실행
app.exec()
```

**주요 메서드:**

- `_setup_ui() -> None`: UI 설정
- `_change_screen(screen_name: str) -> None`: 화면 전환
  - `screen_name`: 화면 이름 (예: "dashboard", "chart_view", "settings" 등)
- `_toggle_theme() -> None`: 테마 전환
- `_show_about_dialog() -> None`: 정보 대화상자 표시
- `_load_settings() -> None`: 설정 로드
- `_save_settings() -> None`: 설정 저장

#### NavigationBar 클래스

애플리케이션의 주요 화면 간 이동을 위한 네비게이션 바입니다.

```python
from upbit_auto_trading.ui.desktop.common.widgets.navigation_bar import NavigationBar

# 네비게이션 바 생성
nav_bar = NavigationBar()

# 화면 전환 시그널 연결
nav_bar.screen_changed.connect(lambda screen_name: print(f"화면 전환: {screen_name}"))

# 활성 화면 설정
nav_bar.set_active_screen("dashboard")
```

**주요 메서드:**

- `set_active_screen(screen_name: str) -> None`: 활성 화면 설정
  - `screen_name`: 화면 이름 (예: "dashboard", "chart_view", "settings" 등)

**시그널:**

- `screen_changed(str)`: 화면 전환 시그널
  - 매개변수: 화면 이름

#### StatusBar 클래스

애플리케이션의 상태 정보를 표시하는 상태 바입니다.

```python
from upbit_auto_trading.ui.desktop.common.widgets.status_bar import StatusBar

# 상태 바 생성
status_bar = StatusBar()

# API 연결 상태 설정
status_bar.set_api_status(connected=True)

# 데이터베이스 연결 상태 설정
status_bar.set_db_status(connected=True)

# 메시지 표시
status_bar.show_message("작업이 완료되었습니다.", timeout=3000)
```

**주요 메서드:**

- `set_api_status(connected: bool) -> None`: API 연결 상태 설정
  - `connected`: 연결 상태
- `set_db_status(connected: bool) -> None`: 데이터베이스 연결 상태 설정
  - `connected`: 연결 상태
- `show_message(message: str, timeout: int = 0) -> None`: 메시지 표시
  - `message`: 표시할 메시지
  - `timeout`: 메시지 표시 시간(ms). 0이면 계속 표시.

#### StyleManager 클래스

애플리케이션의 테마 및 스타일을 관리하는 클래스입니다.

```python
from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager, Theme

# 스타일 관리자 생성
style_manager = StyleManager()

# 테마 적용
style_manager.apply_theme(Theme.DARK)

# 테마 전환
style_manager.toggle_theme()
```

**주요 메서드:**

- `apply_theme(theme: Theme = None) -> None`: 테마 적용
  - `theme`: 적용할 테마. None인 경우 현재 테마 적용.
- `toggle_theme() -> None`: 테마 전환 (라이트 ↔ 다크)