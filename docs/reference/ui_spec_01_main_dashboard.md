# **화면 명세서: 01 - 메인 대시보드 (Main Dashboard)**

## **1. 화면 개요**

메인 대시보드는 사용자가 시스템에 로그인했을 때 가장 먼저 마주하는 화면입니다. 전체 자산 현황, 포트폴리오 요약, 실시간 거래 성과, 시장 개요 등 핵심 정보를 한눈에 파악하여 사용자가 신속하게 의사결정을 내릴 수 있도록 돕는 것을 목표로 합니다. 각 위젯은 요약 정보를 제공하며, 클릭 시 해당 기능의 상세 화면으로 이동하는 관문(Gateway) 역할을 수행합니다.

## **2. UI 요소 및 기능 목록**

| 요소 ID (Element ID) | 명칭 (Name) | 설명 | 연결 기능 (Backend/API) | 관련 코드 (Relevant Code) |
| :--- | :--- | :--- | :--- | :--- |
| **GNB (전역 메뉴)** |  |  |  |  |
| nav-main | 메인 네비게이션 바 | 시스템의 모든 주요 기능(대시보드, 차트 뷰, 종목 스크리닝 등)으로 이동할 수 있는 최상단 또는 좌측 메뉴. | ui.web.app 또는 ui.cli.app의 화면 라우팅(Routing) | upbit\_auto\_trading/ui/web/app.py |
| **자산 및 성과 요약** |  |  |  |  |
| widget-total-assets | 총 자산 위젯 | 사용자의 총 보유 자산 가치(KRW)와 실시간 손익을 표시. UpbitAPI를 통해 개별 자산 정보를 가져오고, PortfolioPerformance를 통해 전체 가치를 계산. | **Class**: UpbitAPI, PortfolioPerformance<br>**Method**: get\_account(), calculate\_portfolio\_performance() | data\_layer/collectors/upbit\_api.py<br>business\_logic/portfolio/portfolio\_performance.py |
| widget-portfolio-summary | 포트폴리오 요약 위젯 | 보유 자산의 구성을 보여주는 도넛 차트와 목록. PortfolioManager를 통해 포트폴리오 목록을 가져오고 각 포트폴리오의 비중을 표시. | **Class**: PortfolioManager<br>**Method**: get\_all\_portfolios() | business\_logic/portfolio/portfolio\_manager.py |
| widget-real-time-performance | 실시간 성과 위젯 | 현재 실행 중인 실시간 자동매매의 전체 성과(총 수익률, 총 손익 등)를 요약하여 표시. | **Class**: TradingEngine (가칭)<br>**Method**: get\_overall\_trading\_status() | business\_logic/trader/ (구현 예정) |
| **거래 및 시장 현황** |  |  |  |  |
| widget-active-positions | 실시간 거래 현황 위젯 | 현재 진입해 있는 모든 포지션의 상세 내역(코인명, 진입가, 현재가, 평가손익 등)을 테이블 형태로 표시. | **Class**: TradingEngine (가칭)<br>**Method**: get\_active\_positions() | business\_logic/trader/ (구현 예정) |
| widget-market-overview | 시장 개요 위젯 | DataCollector를 통해 주기적으로 수집된 대표 코인들의 시세(Ticker) 정보를 표시. | **Class**: DataCollector<br>**Method**: start\_ohlcv\_collection(), get\_ohlcv\_data() | data\_layer/collectors/data\_collector.py |
| **알림 및 로그** |  |  |  |  |
| widget-notifications | 최근 알림/로그 위젯 | Notification 모델에 저장된 최신 시스템 이벤트, 거래 체결, 가격 알림 등을 시간순으로 표시. | **Model**: Notification<br>**Method**: session.query(Notification).order\_by(...) | data\_layer/models.py |

## **3. UI 요소 상세 설명 및 사용자 경험 (UX)**

### **GNB (Global Navigation Bar)**

* **ID**: nav-main
* **설명**: 화면 좌측에 수직으로 배치된 메인 메뉴입니다. 대시보드, 종목 스크리너, 전략 관리 등 시스템의 핵심 기능들로 즉시 이동할 수 있는 링크를 제공합니다.
* **사용자 경험 (UX)**:
    * 현재 사용자가 보고 있는 화면의 메뉴(예: 'Dashboard')는 다른 메뉴와 다른 색상이나 굵기로 표시하여 현재 위치를 명확하게 인지시켜야 합니다.
    * 각 메뉴 아이콘에 마우스 커서를 올리면 메뉴명이 텍스트 툴팁으로 나타나 아이콘의 의미를 쉽게 파악할 수 있도록 돕습니다.
* **구현 연동**:
    * UI 프레임워크(Flask 등)의 라우팅 기능을 통해 화면 간 전환을 처리합니다. (upbit\_auto\_trading/ui/web/app.py 참조)

### **총 자산 위젯 (Total Assets Widget)**

* **ID**: widget-total-assets
* **설명**: 사용자가 보유한 모든 암호화폐 자산과 현금(KRW)을 합산한 총가치를 실시간으로 보여줍니다. 아래에는 기준 시간(예: 24시간) 대비 자산 증감액과 수익률이 함께 표시됩니다.
* **사용자 경험 (UX)**:
    * 화면 최상단 좌측에 배치하여 주목도를 높입니다.
    * 자산 가치가 변동될 때마다 숫자가 부드럽게 변경되는 애니메이션 효과를 적용합니다.
    * 수익일 때는 녹색, 손실일 때는 붉은색으로 표시하여 직관적으로 손익 상황을 인지할 수 있게 합니다.
    * 위젯 전체를 클릭하면 자산 상세 내역 페이지로 이동하여 포트폴리오의 각 코인별 평가금액과 수량을 확인할 수 있도록 합니다.
* **구현 연동**:
    * 백엔드는 UpbitAPI.get\_account()를 호출하여 사용자의 업비트 계좌에 있는 모든 자산(코인, KRW)의 수량과 평균 매입가를 가져옵니다.
    * 각 코인의 현재가는 DataCollector를 통해 실시간으로 수집된 Ticker 데이터를 사용합니다.
    * 수집된 정보를 PortfolioPerformance 클래스 또는 유사한 자산 계산 로직에 전달하여 총 평가금액, 평가손익, 수익률을 계산하고, 이 결과를 위젯에 전달합니다.

### **포트폴리오 요약 위젯 (Portfolio Summary Widget)**

* **ID**: widget-portfolio-summary
* **설명**: 어떤 코인을 얼마나 보유하고 있는지 시각적으로 보여주는 위젯입니다. 도넛 차트를 통해 각 코인이 전체 자산에서 차지하는 비중을, 우측 목록을 통해 각 코인의 명칭과 비중(%)을 텍스트로 보여줍니다.
* **사용자 경험 (UX)**:
    * 도넛 차트의 특정 부분에 마우스를 올리면(Hover) 해당 코인의 이름, 심볼, 보유 비중이 포함된 툴팁(Tooltip)이 나타나 상세 정보를 쉽게 확인할 수 있습니다.
    * 목록에서 특정 코인을 클릭하면 해당 코인의 상세 차트 뷰(Chart View) 화면으로 바로 이동하여 심층 분석을 유도합니다.
* **구현 연동**:
    * PortfolioManager.get\_all\_portfolios()를 호출하여 저장된 모든 포트폴리오 목록을 가져옵니다.
    * 각 포트폴리오에 대해 PortfolioPerformance.calculate\_portfolio\_performance()를 실행하여 현재 평가금액을 계산합니다.
    * 계산된 포트폴리오별 평가금액을 기반으로 전체 자산 대비 각 포트폴리오의 비중을 계산하여 도넛 차트와 목록을 렌더링합니다.

### **실시간 거래 현황 위젯 (Active Positions Widget)**

* **ID**: widget-active-positions
* **설명**: 현재 '실시간 거래' 기능에 의해 자동으로 진입된 모든 포지션의 목록을 테이블 형태로 제공합니다. 각 행은 개별 거래를 의미하며, 진입 시점, 진입 가격, 현재 가격, 평가 손익, 수량 등의 정보를 포함합니다.
* **사용자 경험 (UX)**:
    * 테이블의 데이터는 요구사항 문서의 '성능 요구사항 2번'에 따라 1초 이내의 지연시간으로 갱신되어야 합니다.
    * 평가 손익(P/L) 컬럼은 숫자의 색상을 통해 수익(녹색)/손실(붉은색) 상태를 즉각적으로 파악할 수 있게 합니다.
    * 테이블의 각 행 우측 끝에 작은 'X' 버튼을 두어 해당 포지션을 즉시 '수동 청산'할 수 있는 빠른 접근 경로를 제공할 수 있습니다. (단, 이 기능은 사용자의 실수를 유발할 수 있으므로 "정말 청산하시겠습니까?"와 같은 확인 절차가 필수적입니다.)
* **구현 연동**:
    * business\_logic/trader/ 내에 구현될 거래 엔진(가칭 TradingEngine)은 현재 활성화된 모든 거래 세션(TradingSession 모델)의 상태를 관리합니다.
    * 이 위젯은 TradingEngine.get\_active\_positions() 와 같은 메서드를 주기적으로 호출하여 최신 포지션 목록과 각 포지션의 실시간 평가 손익 정보를 받아 테이블을 업데이트합니다.

### **최근 알림/로그 위젯 (Recent Notifications/Logs Widget)**

* **ID**: widget-notifications
* **설명**: 시스템 운영과 관련된 모든 중요한 이벤트의 최신 기록을 보여줍니다. '주문 체결', '가격 도달 알림', '시스템 오류' 등의 로그가 시간 역순으로 나열됩니다.
* **사용자 경험 (UX)**:
    * 각 알림 유형(시스템, 거래, 가격)에 따라 다른 아이콘을 사용하여 로그의 종류를 시각적으로 쉽게 구분할 수 있도록 합니다.
    * '시스템 오류'와 같이 중요한 로그는 다른 로그보다 눈에 띄는 색상(예: 노란색 또는 붉은색 배경)으로 강조하여 사용자의 주의를 즉시 끌 수 있도록 합니다.
    * 위젯 하단의 '전체 보기' 링크를 클릭하면 모든 로그를 상세히 검색하고 필터링할 수 있는 '모니터링 및 알림' 화면으로 이동합니다.
* **구현 연동**:
    * 백엔드는 data\_layer/models.py에 정의된 Notification 모델의 데이터를 조회합니다.
    * session.query(Notification).order\_by(Notification.timestamp.desc()).limit(10).all()과 같은 SQLAlchemy 쿼리를 사용하여 최신 10개의 알림을 가져와 위젯에 표시합니다.