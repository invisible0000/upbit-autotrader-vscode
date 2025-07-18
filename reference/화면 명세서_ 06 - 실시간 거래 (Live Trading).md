# **화면 명세서: 06 \- 실시간 거래 (Live Trading)**

## **1\. 화면 개요**

실시간 거래 화면은 백테스팅을 마친 전략을 실제 자본으로 운용하는 '실전 관제 센터'입니다. 이 화면에서 사용자는 현재 가동 중인 모든 자동매매 전략의 성과를 실시간으로 모니터링하고, 필요 시 즉각적으로 개입하거나 수동으로 주문을 실행할 수 있습니다. 모든 데이터는 1초 이내의 지연시간으로 갱신되어야 하며, 사용자의 자산을 안전하게 관리하는 것을 최우선 목표로 합니다.

## **2\. UI 요소 및 기능 목록**

| 요소 ID (Element ID) | 명칭 (Name) | 설명 | 연결 기능 (Backend/API) | 관련 코드 (Relevant Code) |
| :---- | :---- | :---- | :---- | :---- |
| **실시간 전략 관리** |  |  |  |  |
| live-active-strategies-table | 활성 전략 현황 | 현재 실시간 거래에 투입된 모든 전략(포지션)의 목록과 성과를 표시하는 테이블. | **Model**: TradingSession\<br\>**Class**: TradingEngine (가칭)\<br\>**Method**: get\_trading\_status() | data\_layer/models.py\<br\>business\_logic/trader/ |
| live-strategy-item-chart | 개별 전략 성과 차트 | 각 활성 전략의 실시간 수익률 변화를 보여주는 작은 라인 차트. | get\_trading\_status()의 거래 내역 기반 | business\_logic/trader/ |
| live-strategy-stop-button | 개별 전략 중지 버튼 | 특정 활성 전략의 자동매매를 즉시 중단시키는 버튼. | **Class**: TradingEngine (가칭)\<br\>**Method**: stop\_trading(trading\_id) | business\_logic/trader/ |
| live-emergency-stop-all | 긴급 전체 중지 버튼 | 화면 상단에 위치하며, 클릭 시 모든 활성 전략을 즉시 중단시키는 비상 버튼. | **Class**: TradingEngine (가칭)\<br\>**Method**: stop\_all\_trading() | business\_logic/trader/ |
| **수동 주문** |  |  |  |  |
| live-manual-order-panel | 수동 주문 패널 | 자동매매와 별개로 사용자가 직접 주문(시장가, 지정가 등)을 실행할 수 있는 위젯. | **Class**: UpbitAPI\<br\>**Method**: place\_order() | data\_layer/collectors/upbit\_api.py |
| live-manual-order-type | 주문 유형 선택 | 시장가(Market), 지정가(Limit) 등 주문 방식을 선택하는 버튼. | place\_order()의 ord\_type 파라미터 | data\_layer/collectors/upbit\_api.py |
| **실시간 시장 데이터** |  |  |  |  |
| live-orderbook-widget | 실시간 오더북(호가창) | 선택된 코인의 실시간 매수/매도 호가 잔량을 시각적으로 표시. | **Class**: DataCollector\<br\>**Method**: start\_orderbook\_collection() | data\_layer/collectors/data\_collector.py |
| **거래 내역** |  |  |  |  |
| live-history-panel | 거래 내역 패널 | 최근 체결 내역, 미체결 주문 목록 등 모든 주문 관련 기록을 표시하는 우측 사이드바. | **Class**: UpbitAPI\<br\>**Method**: get\_orders() | data\_layer/collectors/upbit\_api.py |
| live-open-orders-list | 미체결 주문 목록 | 아직 체결되지 않은 지정가 주문 목록. 주문 취소 기능을 제공. | **Class**: UpbitAPI\<br\>**Method**: get\_orders(state='wait'), cancel\_order() | data\_layer/collectors/upbit\_api.py |
| live-trade-history-list | 최근 체결 내역 | 최근에 체결된 모든 거래의 목록을 시간순으로 표시. | **Class**: UpbitAPI\<br\>**Method**: get\_orders(state='done') | data\_layer/collectors/upbit\_api.py |

## **3\. UI 요소 상세 설명 및 사용자 경험 (UX)**

### **활성 전략 현황 (Current Active Strategies Table)**

* **ID**: live-active-strategies-table  
* **설명**: 이 화면의 핵심으로, 현재 실제 돈으로 운영 중인 모든 자동매매 포지션의 상태를 실시간으로 보여줍니다. 코인명, 보유 수량, 진입 가격, 현재 가격, 그리고 가장 중요한 실시간 평가손익(Profit/Loss)을 표시합니다.  
* **사용자 경험 (UX)**:  
  * **실시간 피드백**: 평가손익과 현재 가격은 요구사항 문서 2번에 따라 1초 이내로 갱신되어야 합니다. 숫자가 바뀔 때마다 색상(수익: 녹색, 손실: 붉은색)과 함께 부드럽게 업데이트되어야 합니다.  
  * **즉각적인 제어**: 각 전략(행)의 우측 끝에는 '중지(Stop)' 버튼이 있어, 특정 전략의 성과가 좋지 않다고 판단될 때 즉시 자동매매를 중단시킬 수 있어야 합니다.  
  * **긴급 상황 대비**: 화면의 잘 보이는 곳에 모든 자동매매를 일괄 정지시키는 '긴급 전체 중지' 버튼을 배치해야 합니다. 이는 시장 급락 등 예기치 못한 상황에서 사용자의 자산을 보호하는 가장 중요한 안전장치입니다.  
* **구현 연동**:  
  * 백엔드의 거래 엔진(가칭 TradingEngine)은 data\_layer/models.py의 TradingSession 모델을 사용하여 활성화된 거래 세션을 관리합니다.  
  * 이 테이블은 TradingEngine.get\_trading\_status()와 같은 메서드를 주기적으로 호출하여 TradingSession 테이블에서 'active' 상태인 모든 세션 정보를 가져옵니다.  
  * 각 세션의 실시간 평가손익은 UpbitAPI.get\_tickers()로 현재가를 조회하고, TradingSession에 기록된 진입 가격 및 수량을 기반으로 계산됩니다.  
  * '중지' 버튼은 해당 세션의 trading\_id를 인자로 TradingEngine.stop\_trading(trading\_id)를 호출하여 세션 상태를 'stopped'로 변경하고 관련 포지션을 정리합니다.

### **수동 주문 패널 (Manual Buy/Order Panel)**

* **ID**: live-manual-order-panel  
* **설명**: 자동매매 로직과 상관없이 사용자가 직접 시장에 개입하고 싶을 때 사용하는 기능입니다.  
* **사용자 경험 (UX)**:  
  * **실수 방지 설계**: 주문 수량이나 가격을 입력하면, 예상 체결 금액이 자동으로 계산되어 표시되어야 합니다. '매수/매도' 버튼을 누르면, 주문 내용을 최종적으로 확인하는 대화상자가 반드시 나타나야 합니다.  
  * **빠른 접근성**: 자동매매로 진입한 포지션을 일부 정리하거나, 급하게 추가 매수를 해야 하는 상황을 위해 화면에서 쉽게 접근할 수 있는 위치에 배치되어야 합니다.  
* **구현 연동**:  
  * 사용자가 주문 정보를 입력하고 '매수/매도' 버튼을 클릭하면, 프론트엔드는 해당 정보를 UpbitAPI.place\_order() 메서드로 전달합니다.  
  * 주문 유형(live-manual-order-type)에 따라 ord\_type 파라미터가 'limit'(지정가), 'price'(시장가 매수), 'market'(시장가 매도) 등으로 설정됩니다.  
  * place\_order()는 업비트 API에 실제 주문을 요청하고 그 결과를 반환합니다.

### **거래 내역 패널 (Trade History Panel)**

* **ID**: live-history-panel  
* **설명**: 시스템을 통해 발생한 모든 주문의 기록을 투명하게 보여주는 공간입니다.  
* **사용자 경험 (UX)**:  
  * **명확한 상태 구분**: '미체결 주문'과 '체결 내역'은 명확하게 탭이나 섹션으로 구분되어야 합니다.  
  * **미체결 주문 관리**: '미체결 주문' 목록에서는 각 주문 옆에 '취소(Cancel)' 버튼이 있어, 사용자가 쉽게 주문을 철회할 수 있도록 해야 합니다.  
  * **상세 정보 제공**: '체결 내역'에서 특정 거래를 클릭하면, 체결 시간, 가격, 수량, 수수료 등 모든 상세 정보를 포함한 팝업이나 상세 뷰를 제공하여 투명성을 높여야 합니다.  
* **구현 연동**:  
  * **미체결 주문(live-open-orders-list)**: UpbitAPI.get\_orders(state='wait')를 주기적으로 호출하여 미체결 주문 목록을 가져옵니다. '취소' 버튼은 해당 주문의 uuid를 인자로 UpbitAPI.cancel\_order(uuid)를 호출합니다.  
  * **최근 체결 내역(live-trade-history-list)**: UpbitAPI.get\_orders(state='done')를 호출하여 최근 체결된 주문 목록을 가져와 표시합니다.