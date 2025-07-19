# 화면 명세서: 07 - 포트폴리오 구성 (Portfolio Configuration)

## 1. 화면 개요

포트폴리오 구성 화면은 개별 코인과 매매 전략을 하나의 '투자 조합(포트폴리오)'으로 묶어 관리하는 공간입니다. 사용자는 이 화면에서 여러 자산에 분산 투자하여 위험을 관리하고, 각 자산의 비중(가중치)을 조절하여 전체 포트폴리오의 기대 수익률과 변동성을 최적화할 수 있습니다. 완성된 포트폴리오는 백테스팅을 통해 검증하거나 실시간 거래에 바로 투입할 수 있습니다.

---

## 2. UI 요소 및 기능 목록

| 요소 ID (Element ID) | 명칭 (Name) | 설명 | 연결 기능 (Backend/API) | 관련 코드 (Relevant Code) |
| :--- | :--- | :--- | :--- | :--- |
| **포트폴리오 관리** | | | | |
| portfolio-list-sidebar | 포트폴리오 목록 | 저장된 모든 포트폴리오의 리스트를 보여주는 좌측 사이드바. '새 포트폴리오 생성' 버튼 포함. | **Class**: PortfolioManager<br>**Method**: get_all_portfolios(), create_portfolio() | business_logic/portfolio/portfolio_manager.py |
| portfolio-action-save | 포트폴리오 저장 버튼 | 현재 구성 중인 포트폴리오의 이름, 설명, 자산 구성을 저장/업데이트. | **Class**: PortfolioManager<br>**Method**: update_portfolio(), update_coin_weight() | business_logic/portfolio/portfolio_manager.py |
| **포트폴리오 구성** | | | | |
| portfolio-composition-panel | 포트폴리오 구성 패널 | 포트폴리오에 포함된 자산의 비중을 시각화하고, 개별 자산을 추가/제거/편집하는 메인 영역. | - | ui/web/app.py |
| portfolio-chart-donut | 자산 비중 차트 | 포트폴리오 내 각 자산(코인+전략)이 차지하는 비중을 보여주는 도넛 차트. | PortfolioManager의 get_portfolio() 결과 기반 | business_logic/portfolio/portfolio_manager.py |
| portfolio-add-asset-btn | 자산 추가 버튼 | 포트폴리오에 새로운 코인을 추가하는 기능. | **Class**: PortfolioManager<br>**Method**: add_coin_to_portfolio() | business_logic/portfolio/portfolio_manager.py |
| portfolio-assets-table | 자산 목록 테이블 | 포트폴리오에 포함된 개별 자산의 상세 정보(코인, 적용 전략, 설정 가중치)를 표시 및 수정. | **Class**: PortfolioManager<br>**Method**: remove_coin_from_portfolio(), update_coin_weight() | business_logic/portfolio/portfolio_manager.py |
| **성과 예측 및 분석** | | | | |
| portfolio-performance-panel | 포트폴리오 성과 패널 | 구성된 포트폴리오의 예상 성과 지표를 표시하는 영역. | **Class**: PortfolioPerformance<br>**Method**: calculate_portfolio_performance() | business_logic/portfolio/portfolio_performance.py |
| portfolio-metrics-expected | 기대 성과 지표 | 과거 데이터를 기반으로 계산된 '기대 수익률', '변동성', '샤프 지수' 등을 표시. | calculate_portfolio_performance()의 결과 | business_logic/portfolio/portfolio_performance.py |
| **실행 및 연동** | | | | |
| portfolio-action-backtest | 포트폴리오 백테스트 버튼 | 현재 구성된 포트폴리오 전체를 대상으로 백테스팅을 실행. | **Class**: PortfolioBacktest<br>**Method**: run_portfolio_backtest() | business_logic/portfolio/portfolio_backtest.py |
| portfolio-action-live-trade | 실시간 거래 시작 버튼 | 구성 및 검증이 완료된 포트폴리오를 실시간 거래에 투입. | **Class**: TradingEngine (가칭)<br>**Method**: start_portfolio_trading() | business_logic/trader/ (구현 예정) |

---

## 3. UI 요소 상세 설명 및 사용자 경험 (UX)

### 포트폴리오 구성 패널 (Portfolio Composition Panel)

* **ID**: portfolio-composition-panel
* **설명**: 사용자가 포트폴리오의 구성 요소를 직접 제어하는 핵심 영역입니다. 도넛 차트를 통해 전체적인 자산 배분을 직관적으로 파악하고, 테이블을 통해 개별 자산의 세부 설정을 관리합니다.
* **사용자 경험 (UX)**:
    * **자산 추가 흐름**: '자산 추가' 버튼을 누르면, 1) 코인 검색, 2) 적용할 '매매 전략' 선택, 3) 할당할 '비중(%)'을 입력하는 단계별 모달(Modal) 창이 나타나야 합니다.
    * **시각적 연동**: 도넛 차트의 특정 부분에 마우스를 올리면, 하단의 자산 목록 테이블에서 해당 자산의 행이 하이라이트 되어야 합니다.
    * **동적 가중치 조절**: 자산 목록 테이블에서 특정 자산의 가중치를 수정하면, 도넛 차트의 크기가 실시간으로 변경되어야 합니다. 전체 가중치의 합이 100%를 초과할 경우, 시각적인 경고를 표시하여 사용자 실수를 방지해야 합니다.
* **구현 연동**:
    * **포트폴리오 목록**: portfolio-list-sidebar는 PortfolioManager.get_all_portfolios()를 호출하여 목록을 구성합니다. '새 포트폴리오 생성'은 PortfolioManager.create_portfolio()를 호출합니다.
    * **자산 추가**: portfolio-add-asset-btn 클릭 후 모달에서 정보를 입력하고 '추가'하면, PortfolioManager.add_coin_to_portfolio(portfolio_id, symbol, strategy_id, weight)를 호출하여 PortfolioCoin 모델에 데이터를 추가합니다.
    * **자산 수정/삭제**: portfolio-assets-table 내에서 가중치 수정 시 PortfolioManager.update_coin_weight()를, 자산 삭제 시 PortfolioManager.remove_coin_from_portfolio()를 호출합니다.
    * **가중치 검증**: 가중치 변경 시마다 PortfolioManager.validate_portfolio_weights()를 호출하여 합계가 1.0에 가까운지 확인하고 UI에 피드백을 줍니다.

---

### 포트폴리오 성과 패널 (Portfolio Performance Panel)

* **ID**: portfolio-performance-panel
* **설명**: '만약 이 포트폴리오를 과거에 운영했다면 어땠을까?'에 대한 시뮬레이션 결과를 보여줍니다.
* **사용자 경험 (UX)**:
    * **자동 계산 및 피드백**: 사용자가 포트폴리오의 구성(자산 추가/제거, 가중치 변경)을 수정할 때마다, '기대 수익률'과 '변동성'이 자동으로 업데이트되어야 합니다. 사용자는 자신의 결정이 포트폴리오의 위험과 수익에 어떤 영향을 미치는지 즉각적으로 피드백 받을 수 있습니다.
    * **이해하기 쉬운 지표**: '기대 수익률' 외에도, 위험 대비 수익성을 나타내는 '샤프 지수(Sharpe Ratio)'와 같은 표준화된 지표를 함께 제공하여 초보 사용자도 포트폴리오의 질을 객관적으로 평가할 수 있도록 돕습니다.
* **구현 연동**:
    * 포트폴리오 구성에 변경이 생길 때마다(자산 추가/제거, 가중치 수정), 프론트엔드는 해당 portfolio_id를 인자로 PortfolioPerformance.calculate_portfolio_performance(portfolio_id)를 호출합니다.
    * 이 메서드는 내부적으로 각 자산의 저장된 백테스트 결과(Backtest 모델)를 기반으로 calculate_expected_return(), calculate_portfolio_volatility(), calculate_portfolio_sharpe_ratio() 등을 순차적으로 실행하여 종합적인 성과 지표를 계산하고 반환합니다.
    * 반환된 딕셔너리 값을 portfolio-metrics-expected UI 요소에 업데이트합니다.

---

### 실행 및 연동 (Actions and Integrations)

* **ID**: portfolio-action-backtest, portfolio-action-live-trade
* **설명**: 잘 짜인 포트폴리오를 다음 단계로 연결하는 관문입니다.
* **사용자 경험 (UX)**:
    * **원클릭 테스트**: '포트폴리오 백테스트' 버튼을 누르면, 현재 구성된 자산 목록과 가중치 설정이 그대로 '백테스팅' 화면으로 전달되어야 합니다. 사용자는 복잡한 재설정 과정 없이 기간과 초기 자본만 입력하고 바로 테스트를 시작할 수 있습니다.
    * **안전한 실전 투입**: '실시간 거래 시작' 버튼을 누르면, "총 N개의 자산으로 구성된 OOO 포트폴리오의 실시간 거래를 시작합니다. 실제 자본이 사용됩니다." 와 같은 강력한 경고 및 확인 대화상자를 표시해야 합니다.
* **구현 연동**:
    * **백테스트**: '포트폴리오 백테스트' 버튼 클릭 시, 현재 portfolio_id와 백테스트 설정(config 객체)을 인자로 PortfolioBacktest.run_portfolio_backtest(portfolio_id, config)를 호출합니다. 이후 '백테스팅' 화면으로 이동하여 해당 결과를 표시합니다.
    * **실시간 거래**: '실시간 거래 시작' 버튼 클릭 시, business_logic/trader/에 구현될 TradingEngine.start_portfolio_trading(portfolio_id)과 같은 메서드를 호출하여 포트폴리오 전체를 하나의 거래 단위로 활성화합니다.