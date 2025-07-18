# **화면 명세서: 05 \- 백테스팅 (Backtesting)**

## **1\. 화면 개요**

백테스팅 화면은 사용자가 만든 매매 전략을 과거의 시장 데이터에 적용하여, 실제 돈을 투입하기 전에 해당 전략의 성과와 안정성을 미리 시험해보는 '가상 테스트 환경'입니다. 사용자는 이 화면을 통해 전략의 잠재적 수익률, 최대 손실폭, 승률 등을 객관적인 데이터로 확인하고, 전략을 더욱 정교하게 다듬을 수 있습니다.

## **2\. UI 요소 및 기능 목록**

| 요소 ID (Element ID) | 명칭 (Name) | 설명 | 연결 기능 (Backend/API) | 관련 코드 (Relevant Code) |
| :---- | :---- | :---- | :---- | :---- |
| **백테스트 설정** |  |  |  |  |
| backtest-setup-panel | 백테스트 설정 패널 | 테스트할 전략/포트폴리오, 기간, 초기 자본 등 테스트 조건을 설정하는 좌측 패널. | \- | ui/web/app.py |
| backtest-strategy-selector | 테스트 대상 선택 | '매매 전략 관리'에서 생성된 개별 전략 또는 '포트폴리오 구성'의 포트폴리오를 선택. | **Class**: StrategyManager, PortfolioManager\<br\>**Method**: get\_strategy\_list(), get\_all\_portfolios() | business\_logic/strategy/strategy\_manager.py\<br\>business\_logic/portfolio/portfolio\_manager.py |
| backtest-param-inputs | 테스트 조건 입력 | 테스트 기간(Time Range), 초기 자본(Initial Capital), 거래 수수료(Trading Fees), 슬리피지(Slippage) 등을 입력. | BacktestRunner 또는 PortfolioBacktest의 config 객체 구성 | business\_logic/backtester/backtest\_runner.py |
| backtest-action-run | 백테스트 실행 버튼 | 설정된 조건으로 백테스팅을 시작. | **Class**: BacktestRunner 또는 PortfolioBacktest\<br\>**Method**: execute\_backtest(), run\_portfolio\_backtest() | business\_logic/backtester/backtest\_runner.py\<br\>business\_logic/portfolio/portfolio\_backtest.py |
| **백테스트 결과** |  |  |  |  |
| backtest-results-panel | 백테스트 결과 패널 | 테스트 완료 후, 성과 지표, 자산 변화 그래프, 상세 거래 내역을 표시하는 메인 영역. | **Class**: BacktestAnalyzer\<br\>**Method**: generate\_report() | business\_logic/backtester/backtest\_analyzer.py |
| backtest-results-metrics | 핵심 성과 지표 | 총수익률(Profit/Loss), 승률(Win Rate), 최대 자본 하락률(Max Drawdown) 등 핵심 결과를 요약 표시. | **Class**: BacktestRunner\<br\>**Method**: calculate\_performance\_metrics() | business\_logic/backtester/backtest\_runner.py |
| backtest-results-chart | 자산 변화(Equity) 차트 | 테스트 기간 동안의 자산 변화를 시계열 그래프로 시각화. 매수/매도 시점이 마커로 표시. | **Class**: BacktestAnalyzer\<br\>**Method**: plot\_equity\_curve() | business\_logic/backtester/backtest\_analyzer.py |
| backtest-results-tradelog | 상세 거래 내역 | 테스트 중에 발생한 모든 개별 거래(진입/청산 시간, 가격, 손익 등)의 목록을 테이블로 표시. | BacktestRunner 결과의 trades 데이터 | business\_logic/backtester/backtest\_runner.py |
| backtest-action-save | 결과 저장 버튼 | 현재 백테스트 결과를 나중에 다시 보거나 다른 결과와 비교할 수 있도록 저장. | **Class**: BacktestResultsManager\<br\>**Method**: save\_backtest\_result() | business\_logic/backtester/backtest\_results\_manager.py |

## **3\. UI 요소 상세 설명 및 사용자 경험 (UX)**

### **백테스트 설정 패널 (Backtest Setup Panel)**

* **ID**: backtest-setup-panel  
* **설명**: 사용자가 백테스트를 실행하기 위해 필요한 모든 조건을 설정하는 컨트롤 타워입니다. 사용자는 테스트하고 싶은 전략이나 포트폴리오를 선택하고, 가상의 초기 자본금과 테스트 기간을 설정합니다.  
* **사용자 경험 (UX)**:  
  * **명확한 흐름**: 사용자는 위에서 아래로 순서대로 항목(전략 선택 \-\> 기간 설정 \-\> 자본금 입력)을 채워나가기만 하면 자연스럽게 테스트를 준비할 수 있도록 UI가 설계되어야 합니다.  
  * **피드백 및 가이드**: '초기 자본'이나 '거래 수수료' 필드에 마우스 커서를 올리면, 해당 항목이 무엇을 의미하는지 설명하는 툴팁을 제공하여 초보 사용자의 이해를 돕습니다.  
  * **실행 전 확인**: '백테스트 실행' 버튼을 누르기 전에, 설정된 조건들을 요약해서 보여주거나, 예상 소요 시간을 알려주는 기능을 제공하여 사용자 경험을 향상할 수 있습니다.  
* **구현 연동**:  
  * **테스트 대상 로드**: 화면 로드 시 StrategyManager.get\_strategy\_list()와 PortfolioManager.get\_all\_portfolios()를 호출하여 backtest-strategy-selector 드롭다운 목록을 채웁니다.  
  * **설정 객체 생성**: 사용자가 모든 조건을 입력하고 '백테스트 실행' 버튼을 누르면, 프론트엔드는 backtest-param-inputs의 값들을 모아 config 딕셔너리를 생성합니다. 이 config 객체는 BacktestRunner 클래스의 생성자에 전달될 파라미터와 일치해야 합니다. (예: {'symbol': 'KRW-BTC', 'timeframe': '1h', 'start\_date': ..., 'end\_date': ..., 'initial\_capital': ..., 'fee\_rate': ..., 'slippage': ...})  
  * **실행 호출**: 생성된 config 객체와 선택된 전략/포트폴리오 ID를 백엔드로 전달하여, BacktestRunner.execute\_backtest() 또는 PortfolioBacktest.run\_portfolio\_backtest()를 호출합니다.

### **백테스트 결과 패널 (Backtest Results Panel)**

* **ID**: backtest-results-panel  
* **설명**: 백테스트가 완료된 후, 그 결과를 다각도로 분석할 수 있는 리포트 영역입니다.  
* **사용자 경험 (UX)**:  
  * **진행 상태 표시**: 백테스팅은 시간이 소요될 수 있는 작업입니다. '실행' 버튼을 누르면, 결과 패널 영역이 로딩 상태로 전환되고, 진행률(%)이나 단계(데이터 로딩 중 \-\> 전략 계산 중 \-\> 결과 생성 중)를 표시하여 사용자가 지루하지 않게 기다릴 수 있도록 해야 합니다.  
  * **시각적 분석**: '자산 변화 차트'는 이 테스트의 성패를 가장 직관적으로 보여주는 요소입니다. 차트 위에 매수(Buy)/매도(Sell) 시점이 마커로 표시되어, 사용자는 '어떤 거래가 수익을 냈고, 어떤 거래가 손실을 냈는지'를 한눈에 파악할 수 있어야 합니다.  
  * **상호 연동**: 하단의 '상세 거래 내역' 테이블에서 특정 거래를 클릭하면, 상단의 '자산 변화 차트'에서 해당 거래가 발생한 시점의 마커가 하이라이트 되거나 중앙으로 이동해야 합니다.  
* **구현 연동**:  
  * 백테스트 실행 후, execute\_backtest() 또는 run\_portfolio\_backtest()가 반환한 results 딕셔너리를 BacktestAnalyzer 클래스의 생성자에 전달합니다.  
  * BacktestAnalyzer.generate\_report()를 호출하여 보고서 데이터를 생성합니다. 이 보고서에는 performance\_metrics, advanced\_metrics, drawdowns, 그리고 figures(시각화 객체) 등이 포함되어 있습니다.  
  * **핵심 성과 지표(backtest-results-metrics)**: results\['performance\_metrics'\] 딕셔너리(total\_return\_percent, win\_rate, max\_drawdown 등)의 값을 UI에 표시합니다.  
  * **자산 변화 차트(backtest-results-chart)**: BacktestAnalyzer.plot\_equity\_curve()가 생성한 Figure 객체를 사용하여 차트를 렌더링합니다. 이 메서드는 results\['equity\_curve'\] DataFrame과 results\['trades'\] 리스트를 사용하여 매수/매도 마커를 함께 표시합니다.  
  * **상세 거래 내역(backtest-results-tradelog)**: results\['trades'\] 리스트의 각 딕셔너리(개별 거래 정보)를 테이블 형태로 표시합니다.  
  * **결과 저장(backtest-action-save)**: '저장' 버튼 클릭 시, BacktestResultsManager.save\_backtest\_result(result)를 호출하여 results 딕셔너리 전체를 데이터베이스와 파일 시스템에 저장합니다.