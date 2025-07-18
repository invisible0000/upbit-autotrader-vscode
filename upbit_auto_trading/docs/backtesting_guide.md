# 백테스팅 가이드

이 문서는 업비트 자동매매 시스템의 백테스팅 기능 사용 방법을 설명합니다.

## 개요

백테스팅은 과거 시장 데이터를 사용하여 거래 전략의 성능을 평가하는 과정입니다. 이 시스템은 다음과 같은 백테스팅 기능을 제공합니다:

- 단일 코인에 대한 전략 백테스팅
- 포트폴리오 백테스팅 (여러 코인과 전략 조합)
- 백테스트 결과 분석 및 시각화
- 백테스트 결과 저장 및 비교

## 백테스팅 컴포넌트

### BacktestRunner

`BacktestRunner`는 전략을 과거 데이터에 적용하여 백테스팅을 실행하고 결과를 생성하는 클래스입니다.

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

### BacktestAnalyzer

`BacktestAnalyzer`는 백테스트 결과를 분석하고 시각화하는 클래스입니다.

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

### BacktestResultsManager

`BacktestResultsManager`는 백테스트 결과를 저장, 불러오기, 비교하는 기능을 제공하는 클래스입니다.

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

## 백테스트 실행 방법

### 단일 전략 백테스트

1. 전략 선택 또는 생성
2. 백테스트 설정 구성 (코인, 시간대, 기간, 초기 자본 등)
3. `BacktestRunner` 인스턴스 생성
4. `execute_backtest()` 메서드 호출
5. 결과 분석 및 저장

### 포트폴리오 백테스트

1. 포트폴리오 생성 및 코인 추가
2. 각 코인에 전략 할당 및 가중치 설정
3. 백테스트 설정 구성
4. 포트폴리오 백테스트 실행
5. 결과 분석 및 저장

## 백테스트 결과 분석

백테스트 결과는 다음과 같은 성과 지표를 포함합니다:

- **총 수익률**: 백테스트 기간 동안의 총 수익률
- **연간 수익률**: 연간화된 수익률
- **최대 손실폭(MDD)**: 최대 낙폭
- **승률**: 수익이 발생한 거래의 비율
- **수익 요인**: 총 수익 / 총 손실
- **샤프 비율**: 위험 조정 수익률
- **소티노 비율**: 하방 위험 조정 수익률
- **거래 횟수**: 총 거래 횟수

`BacktestAnalyzer`를 사용하여 다음과 같은 추가 분석을 수행할 수 있습니다:

- 거래 내역 분석
- 손실폭(Drawdown) 분석
- 월별/연도별 수익률 분석
- 자본 곡선 시각화
- 거래 시점 시각화

## 백테스트 결과 비교

여러 전략 또는 설정의 백테스트 결과를 비교하려면 `BacktestResultsManager`의 `compare_backtest_results()` 메서드를 사용합니다:

```python
# 백테스트 결과 비교
comparison = results_manager.compare_backtest_results(["backtest-1", "backtest-2"])

# 비교 결과 확인
comparison_metrics = comparison["comparison_metrics"]
visualization = comparison["visualization"]
```

비교 결과는 다음 정보를 포함합니다:

- 각 백테스트의 성과 지표 비교
- 자본 곡선 비교 시각화
- 성과 지표 비교 시각화
- 월별 수익률 비교 시각화

## 백테스트 결과 저장 및 관리

백테스트 결과는 데이터베이스와 파일 시스템에 저장됩니다:

- 데이터베이스: 기본 정보 및 성과 지표
- 파일 시스템: 자세한 거래 내역, 자본 곡선 등

`BacktestResultsManager`를 사용하여 다음과 같은 작업을 수행할 수 있습니다:

- 결과 저장 및 불러오기
- 결과 목록 조회 및 필터링
- 결과 비교
- 결과 삭제

## 백테스트 모범 사례

1. **충분한 데이터 사용**: 최소 1년 이상의 데이터로 백테스트하여 다양한 시장 상황을 포함시킵니다.
2. **과적합 방지**: 과도한 매개변수 최적화를 피하고, 다양한 시장 조건에서 테스트합니다.
3. **현실적인 가정**: 수수료, 슬리피지, 유동성 제약 등 현실적인 거래 조건을 반영합니다.
4. **견고성 테스트**: 다양한 시장 상황과 매개변수 변화에 대한 전략의 견고성을 테스트합니다.
5. **포트폴리오 접근**: 단일 코인보다는 포트폴리오 백테스트를 통해 위험 분산 효과를 평가합니다.

## 주의사항

- 과거 성과가 미래 성과를 보장하지 않습니다.
- 백테스트 결과는 이상적인 조건을 가정하므로, 실제 거래에서는 차이가 발생할 수 있습니다.
- 백테스팅 전에 충분한 데이터가 수집되었는지 확인하세요.
- 백테스트 결과를 맹신하지 말고, 실제 시장 상황과 위험 관리를 항상 고려하세요.