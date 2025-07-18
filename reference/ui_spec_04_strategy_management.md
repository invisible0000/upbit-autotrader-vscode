# **화면 명세서: 04 \- 매매 전략 관리 (Strategy Management)**

## **1\. 화면 개요**

매매 전략 관리 화면은 자동매매 시스템의 '두뇌'를 설계하는 곳입니다. 사용자는 이 화면에서 코딩 지식 없이, 시각적인 인터페이스를 통해 '언제 사서 언제 팔 것인가'에 대한 규칙(전략)을 만들고, 편집하며, 성과를 관리할 수 있습니다. 잘 만들어진 전략은 백테스팅을 통해 검증된 후 실시간 거래에 투입됩니다.

## **2\. UI 요소 및 기능 목록**

| 요소 ID (Element ID) | 명칭 (Name) | 설명 | 연결 기능 (Backend/API) | 관련 코드 (Relevant Code) |
| :---- | :---- | :---- | :---- | :---- |
| **전략 목록** |  |  |  |  |
| strategy-list-table | 기존 전략 목록 | 사용자가 생성한 모든 전략의 리스트를 표시하는 테이블. | **Class**: StrategyManager\<br\>**Method**: get\_strategy\_list() | business\_logic/strategy/strategy\_manager.py |
| strategy-list-item | 개별 전략 행 | 목록의 개별 전략 항목. 클릭 시 해당 전략을 '전략 에디터'와 '상세 정보 패널'에 불러옵니다. | **Class**: StrategyManager\<br\>**Method**: load\_strategy() | business\_logic/strategy/strategy\_manager.py |
| strategy-action-create | 새 전략 생성 버튼 | 목록 상단에 위치하며, 클릭 시 '전략 에디터'를 초기화하여 새 전략을 만들 수 있게 합니다. | 프론트엔드 기능 | ui/web/app.py |
| **전략 편집** |  |  |  |  |
| strategy-editor-panel | 전략 에디터 패널 | 매수/매도 조건을 시각적인 블록(노드)으로 조립하여 전략의 로직을 구성하는 핵심 영역. | **Class**: StrategyManager\<br\>**Method**: save\_strategy(), update\_strategy() | business\_logic/strategy/strategy\_manager.py\<br\>business\_logic/strategy/basic\_strategies.py |
| strategy-editor-toolbox | 에디터 도구상자 | '이동 평균 교차', 'RSI' 등 사용 가능한 전략 유형과 파라미터를 제공. | **Class**: StrategyFactory\<br\>**Method**: get\_available\_strategies() | business\_logic/strategy/strategy\_factory.py |
| strategy-editor-node | 전략 구성 노드 | '단기/장기 기간', 'RSI 과매도/과매수' 등 개별 파라미터를 설정하는 에디터 내의 UI 컴포넌트. | **Class**: StrategyParameterManager\<br\>**Method**: validate() | business\_logic/strategy/strategy\_parameter.py |
| **상세 정보 및 실행** |  |  |  |  |
| strategy-details-panel | 전략 상세 정보 패널 | 선택된 전략의 요약 정보와 백테스팅 기반 성과 지표(승률, 손익비 등)를 표시. | **Class**: BacktestResultsManager\<br\>**Method**: list\_backtest\_results() | business\_logic/backtester/backtest\_results\_manager.py |
| strategy-action-buttons | 전략 실행 버튼 그룹 | 선택된 전략을 저장, 삭제, 또는 실시간 거래에 적용('Launch')하는 버튼 모음. | **Class**: StrategyManager, TradingEngine\<br\>**Method**: save\_strategy(), delete\_strategy(), start\_trading() | business\_logic/strategy/strategy\_manager.py\<br\>business\_logic/trader/ (구현 예정) |

## **3\. UI 요소 상세 설명 및 사용자 경험 (UX)**

### **전략 에디터 패널 (Strategy Editor Panel)**

* **ID**: strategy-editor-panel  
* **설명**: 이 화면의 심장부로, 사용자가 코딩 없이 거래 로직을 설계하는 비주얼 프로그래밍 공간입니다. 사용자는 도구상자(strategy-editor-toolbox)에서 '이동 평균 교차'와 같은 전략 유형을 선택하고, 해당 전략에 필요한 파라미터(예: 단기/장기 기간)를 입력하여 하나의 완성된 전략을 만듭니다.  
* **사용자 경험 (UX)**:  
  * **직관적인 설계**: "만약(IF) \[A 조건\]을 만족하고(AND) \[B 조건\]을 만족하면, \[매수(Buy) 액션\]을 실행한다"와 같이, 생각을 그대로 옮길 수 있는 자연스러운 흐름으로 로직을 구성할 수 있어야 합니다.  
  * **파라미터 설정**: 각 지표 블록(노드)을 더블클릭하면, 세부 파라미터를 설정할 수 있는 팝업 창이 나타나야 합니다. (예: 이동 평균선 블록 클릭 \-\> 단기/장기 기간 입력 창 표시)  
  * **오류 방지**: 사용자가 논리적으로 맞지 않는 값(예: 단기 기간 \> 장기 기간)을 입력하면, 시각적인 피드백과 함께 저장을 막아 사용자의 실수를 방지해야 합니다.  
* **구현 연동**:  
  * **전략 유형 로드**: 화면 로드 시 StrategyFactory.get\_available\_strategies()를 호출하여 '이동 평균 교차', 'RSI' 등 사용 가능한 전략 유형 목록을 가져와 도구상자에 표시합니다.  
  * **파라미터 유효성 검사**: 사용자가 파라미터 값을 입력할 때, 해당 전략 클래스(예: MovingAverageCrossStrategy)의 validate\_parameters() 메서드를 실시간으로 호출하여 유효성을 검사하고 UI에 피드백을 줍니다.  
  * **전략 저장**: '저장' 버튼 클릭 시, 프론트엔드는 사용자가 입력한 이름, 설명, 선택한 전략 유형, 그리고 파라미터들을 모아 StrategyManager.save\_strategy(strategy\_id, strategy\_type, name, description, parameters) 또는 update\_strategy()를 호출합니다. parameters는 {"short\_window": 10, "long\_window": 30}와 같은 JSON 객체 형태여야 합니다.

### **기존 전략 목록 (Existing Strategies Table)**

* **ID**: strategy-list-table  
* **설명**: 사용자가 만들고 저장한 모든 전략들을 관리하는 목록입니다.  
* **사용자 경험 (UX)**:  
  * **상태 표시**: 'Active', 'Testing' 컬럼은 해당 전략의 현재 상태를 나타냅니다. 'Active'는 실시간 거래에 사용 중인 상태, 'Testing'은 생성 후 아직 실거래에 투입되지 않은 상태를 의미합니다.  
  * **빠른 탐색**: 전략이 많아질 것을 대비하여, 목록 상단에 이름으로 전략을 검색할 수 있는 검색창을 제공해야 합니다.  
  * **원클릭 로딩**: 목록에서 특정 전략을 클릭하는 즉시, 중앙의 '전략 에디터'와 우측의 '상세 정보 패널'에 해당 전략의 내용과 성과가 바로 로드되어야 합니다.  
* **구현 연동**:  
  * 화면 로드 시 StrategyManager.get\_strategy\_list()를 호출하여 데이터베이스에 저장된 모든 전략의 목록을 가져옵니다. 반환된 리스트에는 Strategy 모델의 id, name, description, parameters 등이 포함됩니다.  
  * 특정 전략을 클릭하면, 해당 전략의 id를 사용하여 StrategyManager.load\_strategy(strategy\_id)를 호출하고, 반환된 전략 객체의 정보로 에디터 UI를 채웁니다.

### **전략 상세 정보 패널 (Strategy Details Panel)**

* **ID**: strategy-details-panel  
* **설명**: 선택된 전략의 '성적표'와 '관리 버튼'을 모아놓은 공간입니다.  
* **사용자 경험 (UX)**:  
  * **성과 지표**: 이 패널에 표시되는 Win Rate(승률), Profit/Loss(손익비) 등의 지표는 해당 전략의 가장 최근 백테스트 결과를 기반으로 합니다.  
  * **명확한 버튼 명칭**: 'Launch'는 '실거래 시작' 또는 '활성화'로 명칭을 명확히 하는 것이 좋습니다.  
  * **안전장치**: 'Delete'(삭제)나 'Launch'(실거래 시작)처럼 중요한 액션 버튼은, 클릭 시 확인 대화상자를 한 번 더 보여주어 사용자의 실수를 방지해야 합니다.  
* **구현 연동**:  
  * 전략 목록에서 특정 전략을 선택하면, 해당 strategy\_id를 키로 BacktestResultsManager.list\_backtest\_results(filter\_params={'strategy\_id': '...' })를 호출하여 이 전략으로 실행된 가장 최근 백테스트 결과를 가져옵니다.  
  * 가져온 백테스트 결과의 performance\_metrics를 파싱하여 승률, 손익비 등의 성과 지표를 UI에 표시합니다.  
  * 'Delete' 버튼은 StrategyManager.delete\_strategy(strategy\_id)를 호출합니다.  
  * 'Launch' 버튼은 business\_logic/trader/에 구현될 TradingEngine.start\_trading(strategy\_id, ...) 메서드를 호출하게 됩니다.