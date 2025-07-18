# 레퍼런스 문서 활용 가이드

## 개요

`reference` 폴더에는 업비트 자동매매 시스템의 설계 및 구현에 필요한 상세 문서들이 포함되어 있습니다. 이 문서들은 시스템 아키텍처, 데이터베이스 스키마, API 명세, 화면 설계 등에 대한 상세 정보를 제공합니다. 이 가이드는 레퍼런스 문서를 효과적으로 활용하는 방법을 설명합니다.

## 레퍼런스 문서 구성

레퍼런스 폴더에는 다음과 같은 문서들이 포함되어 있습니다:

1. **시스템 아키텍처 설계서**: 시스템의 전체적인 구조와 컴포넌트 간 관계를 설명
2. **데이터베이스 스키마 명세서**: 데이터베이스 테이블 구조와 관계를 정의
3. **API 명세서**: 외부 API 및 내부 API의 인터페이스를 정의
4. **배포 및 운영 가이드**: 시스템 배포 및 운영 방법을 설명
5. **보안 설계 문서**: 시스템의 보안 요구사항과 구현 방법을 설명
6. **화면 명세서**: 각 화면의 UI 요소와 기능을 상세히 설명

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

시스템 아키텍처 설계서는 시스템의 전체적인 구조와 컴포넌트 간 관계를 이해하는 데 중요합니다.

### 시스템 아키텍처 활용 단계

1. **계층 구조 이해**: 시스템의 계층 구조(UI 계층, 비즈니스 로직 계층, 데이터 계층)를 이해합니다.
2. **컴포넌트 식별**: 각 계층에 포함된 주요 컴포넌트와 그 역할을 식별합니다.
3. **데이터 흐름 파악**: 컴포넌트 간 데이터 흐름을 파악하여 기능 구현 시 참조합니다.
4. **기술 스택 확인**: 각 컴포넌트에 사용되는 기술 스택을 확인하여 구현에 활용합니다.

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