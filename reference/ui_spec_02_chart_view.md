# **화면 명세서: 02 \- 차트 뷰 (Chart View)**

## **1\. 화면 개요**

차트 뷰는 기술적 분석의 핵심이 되는 공간입니다. 사용자는 이 화면에서 특정 암호화폐의 가격 움직임을 시각적으로 확인하고, 이동평균선, 볼린저 밴드, RSI 등 다양한 기술적 지표를 적용하여 시장의 추세를 분석할 수 있습니다. 또한, 백테스팅이나 실시간 거래에서 발생한 매수/매도 시점을 차트 위에 직접 표시하여 전략의 유효성을 직관적으로 검증하는 것을 목표로 합니다.

## **2\. UI 요소 및 기능 목록**

| 요소 ID (Element ID) | 명칭 (Name) | 설명 | 연결 기능 (Backend/API) | 관련 코드 (Relevant Code) |
| :---- | :---- | :---- | :---- | :---- |
| **차트 헤더** |  |  |  |  |
| chart-header-pair | 페어 선택 및 시세 표시 | 현재 선택된 코인 페어(예: KRW-BTC)와 실시간 가격, 등락률을 표시합니다. | **Class**: UpbitAPI\<br\>**Method**: get\_tickers() | data\_layer/collectors/upbit\_api.py |
| chart-header-timeframe | 시간대(Timeframe) 선택 | 1분, 5분, 1시간, 1일 등 차트의 시간 단위를 변경하는 버튼 그룹입니다. | **Class**: DataProcessor\<br\>**Method**: resample\_data() | data\_layer/processors/data\_processor.py |
| **차트 툴바** |  |  |  |  |
| chart-toolbar | 차트 도구 모음 | 차트 위에 선을 긋거나, 알림을 추가하고, 현재 차트 설정을 저장/로드하는 기능 아이콘 모음입니다. | UI 상태 저장/로드 | 프론트엔드 기능 |
| **차트 본문** |  |  |  |  |
| chart-pane-main | 메인 가격 차트 | 캔들스틱(Candlestick) 형태로 가격(시가, 고가, 저가, 종가)을 표시하는 주 영역입니다. | **Class**: DataCollector\<br\>**Method**: collect\_historical\_ohlcv() | data\_layer/collectors/data\_collector.py |
| chart-pane-volume | 거래량 차트 | 가격 차트 하단에 막대그래프 형태로 해당 시간대의 거래량을 표시합니다. | DataCollector로부터 받은 데이터 사용 | data\_layer/collectors/data\_collector.py |
| chart-marker-trade | 매매 시점 마커 | 백테스트 또는 실시간 거래의 매수(Buy)/매도(Sell) 시점을 차트 위에 아이콘으로 표시합니다. | **Class**: BacktestRunner\<br\>**Method**: execute\_backtest()의 결과 | business\_logic/backtester/backtest\_runner.py |
| **지표 패널** |  |  |  |  |
| indicator-panel | 기술적 지표 패널 | 사용 가능한 모든 기술적 지표 목록을 보여주고, 차트에 적용/해제할 수 있는 우측 사이드바입니다. | **Class**: DataProcessor\<br\>**Method**: calculate\_indicators() | data\_layer/processors/data\_processor.py |
| indicator-item | 개별 지표 항목 | 지표의 이름, 설정값, 미리보기 차트 등을 포함하는 패널 내의 각 항목입니다. | **Class**: DataProcessor\<br\>**Method**: calculate\_indicators() | data\_layer/processors/data\_processor.py |

## **3\. UI 요소 상세 설명 및 사용자 경험 (UX)**

### **페어 선택 및 시세 표시 (Pair Selection & Price Display)**

* **ID**: chart-header-pair  
* **설명**: 화면 좌측 상단에 위치하며, 현재 분석 중인 코인의 이름(예: 비트코인 / KRW-BTC)과 실시간 가격을 표시합니다.  
* **사용자 경험 (UX)**:  
  * 코인 이름을 클릭하면, 거래 가능한 모든 코인 목록을 검색하고 선택할 수 있는 드롭다운 메뉴나 팝업 창이 나타나야 합니다. 사용자가 다른 코인을 선택하는 즉시 차트 데이터는 해당 코인의 것으로 변경되어야 합니다.  
  * 실시간 가격은 요구사항 문서의 '성능 요구사항 2번'에 따라 1초 이내의 지연시간으로 업데이트되며, 가격 상승 시에는 녹색, 하락 시에는 붉은색으로 표시되어 변화를 즉각적으로 인지할 수 있게 합니다.  
* **구현 연동**:  
  * 백엔드는 UpbitAPI.get\_tickers()를 주기적으로 호출하여 최신 시세 정보를 가져옵니다.  
  * 코인 목록은 UpbitAPI.get\_markets()를 통해 거래 가능한 전체 마켓 목록을 가져와 프론트엔드에 제공합니다.

### **시간대(Timeframe) 선택**

* **ID**: chart-header-timeframe  
* **설명**: '1m', '15m', '1h', '1d' 등 다양한 시간 단위를 선택할 수 있는 버튼 그룹입니다.  
* **사용자 경험 (UX)**:  
  * 사용자가 특정 시간대(예: '1h')를 클릭하면, 시스템은 1시간 봉 데이터에 맞게 차트를 다시 그립니다. 이 과정은 0.5초 이내에 부드럽게 처리되어야 하며(성능 요구사항 3번), 사용자가 여러 시간대를 오가며 단기 및 장기 추세를 빠르게 분석할 수 있도록 지원합니다.  
* **구현 연동**:  
  * 기본 데이터는 분봉(minute candle) 데이터를 기준으로 합니다. 사용자가 다른 시간대(예: '1h')를 선택하면, 프론트엔드 또는 백엔드에서 DataProcessor.resample\_data() 메서드를 호출하여 기존 데이터를 해당 시간대로 변환(리샘플링)하여 차트를 다시 렌더링합니다.

### **메인 가격 차트 (Main Price Chart)**

* **ID**: chart-pane-main  
* **설명**: 화면의 가장 큰 영역을 차지하는 캔들스틱 차트입니다. 사용자는 이 차트를 통해 가격의 흐름을 분석합니다.  
* **사용자 경험 (UX)**:  
  * **인터랙션**: 사용자는 마우스 휠 스크롤을 통해 차트를 확대/축소하여 미세한 가격 변동을 보거나 전체적인 추세를 볼 수 있어야 합니다. 차트를 클릭 후 드래그하여 과거 데이터를 탐색할 수 있어야 합니다.  
  * **정보 표시**: 마우스 커서를 특정 캔들 위로 이동시키면, 해당 캔들의 날짜, 시간, 시가, 고가, 저가, 종가, 거래량 정보가 차트 상단이나 커서 주변에 표시되어야 합니다.  
  * **실시간 업데이트**: 현재 시간대의 가장 마지막 캔들은 실시간으로 가격 변동을 반영하여 계속해서 형태가 바뀌어야 합니다.  
* **구현 연동**:  
  * 차트에 필요한 과거 데이터는 DataCollector.collect\_historical\_ohlcv()를 통해 지정된 기간만큼 가져옵니다. 이 메서드는 내부적으로 UpbitAPI.get\_historical\_candles()를 호출하여 데이터를 수집하고 데이터베이스에 저장합니다.  
  * 저장된 데이터는 MarketDataStorage.load\_market\_data()를 통해 빠르게 불러올 수 있습니다.

### **기술적 지표 패널 (Technical Indicator Panel)**

* **ID**: indicator-panel  
* **설명**: 화면 우측에 위치하며, 사용자가 원하는 기술적 지표를 차트에 추가하거나 제거할 수 있는 컨트롤 타워입니다.  
* **사용자 경험 (UX)**:  
  * **지표 추가**: 사용자가 '지표 추가(Add Indicator)' 버튼을 누르면, '이동 평균(Moving Averages)', '볼린저 밴드(Bollinger Bands)', 'RSI' 등 선택 가능한 지표 목록이 나타납니다.  
  * **파라미터 설정**: 특정 지표를 선택하면, 해당 지표의 세부 설정(예: 이동 평균의 '기간(period)' 값)을 입력할 수 있는 설정 창이 나타납니다. 사용자가 설정을 완료하고 '적용' 버튼을 누르면 지표가 메인 차트나 하단 영역에 그려집니다.  
  * **직관적 제어**: 패널에 추가된 지표 목록에는 이름과 함께 토글스위치가 있어, 복잡한 설정 없이도 특정 지표를 잠시 끄거나 켤 수 있어야 합니다.  
* **구현 연동**:  
  * 사용자가 지표를 추가하고 파라미터를 설정하면, 프론트엔드는 이 정보를 백엔드에 전달합니다.  
  * 백엔드는 DataProcessor.calculate\_indicators() 메서드를 호출하여 요청된 지표들을 계산합니다. 이 메서드는 내부적으로 \_calculate\_sma, \_calculate\_bollinger\_bands 등 개별 지표 계산 함수를 사용합니다.  
  * 계산된 지표 데이터가 포함된 DataFrame이 프론트엔드로 반환되어 차트에 렌더링됩니다.