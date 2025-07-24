# **화면 명세서: 03 - 자산 스크리닝 (Asset Screener)**

## **1. 화면 개요**

자산 스크리닝은 업비트(Upbit) 한국 코인 거래소의 KRW마켓에 상장된 암호화폐(코인)를 대상으로, 사용자가 원하는 특정 조건을 만족하는 종목들을 걸러내어 투자 기회를 발견하는 기능입니다. 거래량, 시가총액, 가격 변동성, 기술적 지표 등 다양한 필터를 조합하여 잠재력 있는 자산(코인)을 효율적으로 찾아내고, 분석 및 거래로 바로 연결하는 것을 목표로 합니다.

## **2. UI 요소 및 기능 목록**

| 요소 ID (Element ID) | 명칭 (Name) | 설명 | 연결 기능 (Backend/API) | 관련 코드 (Relevant Code) |
| :--- | :--- | :--- | :--- | :--- |
| **필터링** |  |  |  |  |
| screener-filter-sidebar | 필터 프리셋 | 자주 사용하는 필터 조합을 저장하거나, 기본 제공되는 프리셋을 선택하는 사이드바. | **Class**: ScreenerResult\<br\>**Method**: save\_screening\_result(), get\_screening\_results() | business\_logic/screener/screener\_result.py |
| screener-filter-controls | 필터 조건 설정 | 거래량, 가격 변동률, 추세 등 상세 필터 조건을 설정하는 컨트롤 영역. | **Class**: BaseScreener\<br\>**Method**: screen\_assets() | business\_logic/screener/base\_screener.py |
| screener-filter-custom | 사용자 정의 조건 | 여러 지표와 연산자를 조합하여 복잡한 맞춤형 필터 조건을 생성하는 기능. | **Class**: BaseScreener\<br\>**Method**: screen\_assets() | business\_logic/screener/base\_screener.py |
| **결과 표시** |  |  |  |  |
| screener-results-table | 스크리닝 결과 테이블 | 설정된 필터 조건에 맞는 자산 목록을 데이터 테이블 형태로 표시. | **Class**: ScreenerResult\<br\>**Method**: sort\_screening\_details() | business\_logic/screener/screener\_result.py |
| screener-table-row | 개별 자산 행 | 필터링된 개별 자산의 주요 정보를 담고 있는 테이블의 각 행. | 화면 라우팅 | 프론트엔드 기능 |
| **사용자 액션** |  |  |  |  |
| screener-action-save | 결과 저장 버튼 | 현재 스크리닝 결과를 이름과 설명과 함께 저장하는 버튼. | **Class**: ScreenerResult\<br\>**Method**: save\_screening\_result() | business\_logic/screener/screener\_result.py |
| screener-action-export | CSV로 내보내기 | 현재 스크리닝 결과를 CSV 파일로 다운로드하는 버튼. | **Class**: ScreenerResult\<br\>**Method**: export\_to\_csv() | business\_logic/screener/screener\_result.py |
| screener-action-portfolio | 포트폴리오 구성 버튼 | 선택된 자산들을 기반으로 '포트폴리오 구성' 화면으로 이동하는 버튼. | create\_portfolio() 연계 | business\_logic/portfolio/portfolio\_manager.py |

## **3. UI 요소 상세 설명 및 사용자 경험 (UX)**

### **필터 조건 설정 (Filter Configuration)**

* **ID**: screener-filter-controls
* **설명**: 사용자가 원하는 자산을 찾기 위한 핵심 도구입니다. '24시간 거래대금', '변동성', '추세' 등과 같은 필터를 슬라이더나 직접 입력 방식을 통해 설정할 수 있습니다.
* **사용자 경험 (UX)**:
  * 사용자가 필터 값을 변경하는 즉시, 하단의 결과 테이블은 실시간으로 다시 조회되어야 합니다. 조회 중에는 테이블 영역에 로딩 스피너(Loading Spinner)를 표시하여 시스템이 작동 중임을 알려줍니다.
  * **사용자 정의 조건(screener-filter-custom)**: 비개발자인 사용자를 위해, "만약(IF) \[지표\] \[연산자\] \[값\] 이면" 과 같은 자연어에 가까운 UI를 제공하여 복잡한 조건도 쉽게 만들 수 있도록 지원해야 합니다.
  * 사용자가 설정한 필터 조합을 저장하고 나중에 다시 불러올 수 있는 기능은 필수적입니다.
* **구현 연동**:
  * 프론트엔드의 각 필터 컨트롤(슬라이더, 드롭다운 등)은 criteria 배열을 구성하는 역할을 합니다. 예를 들어, 거래량 필터는 {'type': 'volume', 'params': {'min\_volume': 1000000000}}와 같은 객체를 생성합니다.
  * '검색' 또는 '적용' 버튼을 클릭하면, 이 criteria 배열을 인자로 BaseScreener.screen\_assets() 메서드를 호출합니다.
  * screen\_assets() 메서드는 criteria를 순회하며 screen\_by\_volume(), screen\_by\_volatility(), screen\_by\_trend() 등 내부 메서드를 호출하여 각 조건을 만족하는 자산 목록을 가져온 후, combine\_screening\_results()를 통해 최종 결과를 조합합니다.

### **스크리닝 결과 테이블 (Screening Results Table)**

* **ID**: screener-results-table
* **설명**: 필터링된 자산들의 목록을 보여주는 데이터 그리드입니다. 자산명, 심볼, 현재가, 등락률, 거래량, 그리고 필터 조건에 사용된 주요 지표 값들을 컬럼으로 표시합니다.
* **사용자 경험 (UX)**:
  * **정렬 기능**: 각 컬럼의 헤더(예: '24h Change')를 클릭하면 해당 컬럼을 기준으로 데이터가 정렬되어야 합니다. 한 번 더 클릭하면 오름차순/내림차순이 전환됩니다.
  * **상세 정보로 이동**: 테이블의 특정 행을 클릭하면, 해당 자산의 '차트 뷰'로 즉시 이동하여 심층적인 기술적 분석을 할 수 있도록 유도합니다.
  * **데이터 시각화**: 'Volume'이나 'RSI' 같은 수치 데이터는 단순히 숫자만 보여주는 것보다, 값의 크기에 따라 배경에 옅은 색의 막대그래프(Bar)를 함께 표시해주면 데이터를 비교하고 이해하기가 훨씬 쉬워집니다.
* **구현 연동**:
  * BaseScreener.screen\_assets()가 반환한 결과(자산 정보 목록)를 테이블 형태로 렌더링합니다.
  * 컬럼 헤더 클릭 시 정렬 기능은 프론트엔드에서 처리하거나, 백엔드의 ScreenerResult.sort\_screening\_details() 메서드를 호출하여 정렬된 데이터를 다시 받아올 수 있습니다.

### **결과 저장 및 활용 (Save & Utilize Results)**

* **ID**: screener-action-save, screener-action-export, screener-action-portfolio
* **설명**: 스크리닝을 통해 발견한 유망한 종목에 대해 다음 행동으로 연결하는 기능입니다.
* **사용자 경험 (UX)**:
  * **결과 저장**: '결과 저장' 버튼을 누르면, 현재 스크리닝 결과에 대한 이름과 설명을 입력하는 팝업이 나타납니다. 저장된 결과는 나중에 '필터 프리셋' 사이드바에서 다시 불러올 수 있습니다.
  * **내보내기**: 'CSV로 내보내기' 버튼을 누르면 현재 테이블의 데이터를 CSV 파일로 다운로드하여 Excel 등 다른 도구에서 분석할 수 있습니다.
  * **포트폴리오 구성**: 사용자가 테이블에서 하나 이상의 자산을 체크박스로 선택한 후 '포트폴리오 구성' 버튼을 누르면, "선택한 N개의 자산으로 새 포트폴리오를 구성하시겠습니까?" 라는 확인 창을 띄우고, '포트폴리오 구성' 화면으로 선택된 자산 목록을 전달하여 이동합니다.
* **구현 연동**:
  * **결과 저장**: '저장' 버튼 클릭 시, 프론트엔드는 현재 필터 조건(criteria)과 결과(results)를 ScreenerResult.save\_screening\_result(name, description, criteria, results) 메서드로 전달하여 데이터베이스에 저장합니다.
  * **내보내기**: ScreenerResult.export\_to\_csv(result\_id) 메서드를 호출하여 서버에 CSV 파일을 생성하고, 사용자에게 다운로드 링크를 제공합니다.
  * **포트폴리오 구성**: 선택된 자산 목록을 가지고 '포트폴리오 구성' 화면으로 이동합니다. 해당 화면에서는 PortfolioManager.create\_portfolio()와 add\_asset\_to\_portfolio()를 사용하여 새로운 포트폴리오를 생성하게 됩니다.