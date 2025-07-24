# 화면 명세서: 08 - 모니터링 및 알림 (Monitoring & Alerts)

## 1. 화면 개요

모니터링 및 알림 화면은 시장의 중요한 변화나 시스템 내부에서 발생하는 주요 이벤트를 사용자가 놓치지 않도록 알려주는 '감시탑' 역할을 합니다. 사용자는 이 화면에서 관심 종목의 시세를 실시간으로 모니터링하고, 특정 조건(가격 도달, 주문 체결 등)이 충족되었을 때 알림을 받도록 설정할 수 있습니다. 이를 통해 시장 변화에 신속하게 대응하고, 자동매매 시스템의 운영 현황을 투명하게 파악하는 것을 목표로 합니다.

---

## 2. UI 요소 및 기능 목록

| 요소 ID (Element ID) | 명칭 (Name) | 설명 | 연결 기능 (Backend/API) | 관련 코드 (Relevant Code) |
| :--- | :--- | :--- | :--- | :--- |
| **실시간 모니터링** | | | | |
| monitor-widget-realtime | 실시간 시장 모니터 | 주요 지수나 사용자가 선택한 대표 코인의 시세를 실시간으로 표시하는 위젯. | **Class**: DataCollector<br>**Method**: start_ohlcv_collection() | data_layer/collectors/data_collector.py |
| monitor-widget-selected | 선택 종목 모니터 | 사용자가 지정한 특정 코인의 가격, 거래량, 미니 차트를 상세하게 보여주는 위젯. | **Class**: DataCollector<br>**Method**: get_ohlcv_data() | data_layer/collectors/data_collector.py |
| **알림 설정** | | | | |
| alert-settings-panel | 알림 설정 패널 | 다양한 유형의 알림을 생성하고 관리하는 메인 컨트롤 영역. | **Model**: Notification (결과 저장)<br>**Class**: AlertManager (가칭, 로직 처리) | data_layer/models.py<br>business_logic/ (신규 구현 필요) |
| alert-type-selector | 알림 유형 선택 | 가격, 주문 체결, 시스템 오류, 기술적 지표 등 알림을 받을 조건을 선택합니다. | config.yaml의 notifications.types | config/config.yaml |
| alert-condition-inputs | 알림 조건 상세 설정 | 선택한 알림 유형에 맞는 상세 조건을 입력합니다. (예: BTC 가격이 5만 달러 이상일 때) | **Class**: DataProcessor (지표 계산)<br>**Class**: AlertManager (조건 검사) | data_layer/processors/data_processor.py |
| alert-delivery-method | 알림 전달 방식 | 알림을 받을 방법을 선택합니다. (예: 프로그램 내 팝업, 소리, 이메일) | config.yaml의 notifications.methods | config/config.yaml |
| alert-action-save | 알림 저장 버튼 | 설정된 알림 조건을 시스템에 저장하고 활성화합니다. | **Class**: AlertManager (가칭)<br>**Method**: save_alert_condition() | business_logic/ (신규 구현 필요) |
| **알림 기록** | | | | |
| alert-history-log-table | 알림 기록 로그 | 과거에 발생한 모든 알림의 내역을 시간순으로 보여주는 테이블. | **Model**: Notification<br>**Method**: session.query(Notification).all() | data_layer/models.py |
| alert-history-search | 알림 기록 검색 | 특정 키워드나 코인명으로 과거 알림 기록을 검색하는 기능. | session.query(Notification).filter(...) | data_layer/models.py |

---

## 3. UI 요소 상세 설명 및 사용자 경험 (UX)

### 알림 설정 패널 (Alert Settings Panel)

* **ID**: alert-settings-panel
* **설명**: 사용자가 '어떤 상황에', '어떻게' 알림을 받을지 정의하는 개인화된 감시 시스템 설정 공간입니다.
* **사용자 경험 (UX)**:
    * **동적 UI**: 사용자가 '알림 유형 선택'에서 '가격 알림(Price Alert)'을 선택하면, 코인을 선택하는 드롭다운과 목표 가격을 입력하는 필드가 나타나야 합니다. 만약 '기술적 지표 알림(Technical Indicator Alert)'을 선택하면, 코인 선택, 지표 종류(RSI, MACD 등), 그리고 조건(예: RSI가 30 미만일 때)을 설정하는 UI로 동적으로 변경되어야 합니다.
    * **명확한 피드백**: '알림 저장' 버튼을 누르면, "BTC 가격 5만 달러 도달 시 알림이 설정되었습니다." 와 같이 사용자가 설정한 내용을 요약하여 보여주는 확인 메시지(Toast popup)가 잠시 나타났다 사라져야 합니다.
* **구현 연동**:
    * **알림 로직**: `business_logic` 내에 새로운 `AlertManager` 클래스 구현이 필요합니다. 이 클래스는 알림 조건을 데이터베이스(신규 AlertCondition 모델 필요)에 저장(`save_alert_condition`)하고, 주기적으로 조건을 확인하여 만족 시 `Notification` 객체를 생성하는 역할을 합니다.
    * **기술적 지표 조건**: '기술적 지표 알림' 설정 시, `AlertManager`는 `DataProcessor.calculate_indicators()`를 사용하여 현재 지표 값을 계산하고, 사용자가 설정한 조건과 비교합니다.
    * **알림 유형/방식**: `config.yaml`의 `notifications` 섹션에 정의된 `types`와 `methods`를 읽어와 UI에 선택 가능한 옵션으로 제공합니다.

### 알림 기록 로그 (Alert History Log)

* **ID**: alert-history-log-table
* **설명**: 시스템이 사용자에게 보냈던 모든 알림의 발자취를 확인할 수 있는 공간입니다.
* **사용자 경험 (UX)**:
    * **시각적 구분**: 각 알림의 유형(가격, 주문, 시스템 오류 등)에 따라 행 앞에 다른 아이콘이나 색상 태그를 붙여주면, 사용자는 목록을 훑어보는 것만으로도 어떤 종류의 알림이었는지 빠르게 구분할 수 있습니다.
    * **효율적인 탐색**: 알림이 수백 개 이상 쌓일 것을 대비하여, 테이블 상단에 위치한 검색창은 필수적입니다. 사용자는 코인 이름('BTC'), 알림 유형('주문'), 또는 메시지 내용('체결') 등의 키워드로 원하는 기록을 즉시 찾아볼 수 있어야 합니다.
    * **상세 정보 확인**: 테이블의 각 행을 클릭하면, 알림 발생 시점의 상세한 시장 상황이나 관련 데이터(예: 주문 체결 알림 클릭 시, 해당 주문의 상세 내역)를 보여주는 팝업 창을 띄워주어 심층적인 분석을 지원할 수 있습니다.
* **구현 연동**:
    * **기록 조회**: 백엔드는 `data_layer/models.py`에 정의된 `Notification` 모델의 데이터를 조회합니다. `session.query(Notification).order_by(Notification.timestamp.desc()).all()`과 같은 SQLAlchemy 쿼리를 사용하여 전체 알림 기록을 가져옵니다.
    * **기록 검색**: `alert-history-search` 입력값에 따라 `session.query(Notification).filter(Notification.message.like(f"%{keyword}%"))` 와 같이 동적 필터를 적용하여 검색 결과를 반환합니다.