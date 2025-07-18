# 알림 센터 개발 가이드

## 개요

알림 센터는 업비트 자동매매 시스템의 중요한 구성 요소로, 사용자에게 가격 변동, 거래 체결, 시스템 상태 등에 관한 알림을 제공합니다. 이 문서는 알림 센터의 구조, 기능, 사용 방법에 대한 가이드를 제공합니다.

## 구조

알림 센터는 다음과 같은 주요 컴포넌트로 구성됩니다:

1. **알림 모델**
   - `NotificationType`: 알림 유형 열거형 (가격 알림, 거래 알림, 시스템 알림)
   - `Notification`: 알림 데이터 클래스
   - `NotificationManager`: 알림 관리 클래스

2. **알림 센터 UI**
   - `NotificationCenter`: 알림 센터 메인 화면
   - `NotificationList`: 알림 목록 화면
   - `NotificationFilter`: 알림 필터 기능
   - `NotificationSettings`: 알림 설정 화면

## 기능

### 알림 유형

알림 센터는 다음과 같은 유형의 알림을 지원합니다:

1. **가격 알림**
   - 설정된 임계값을 초과하거나 미만인 경우 발생
   - 예: "BTC 가격이 50,000,000원을 초과했습니다."

2. **거래 알림**
   - 주문 체결 시 발생
   - 예: "BTC 매수 주문이 체결되었습니다."

3. **시스템 알림**
   - 시스템 오류 또는 상태 변경 시 발생
   - 예: "데이터베이스 연결이 복구되었습니다."

### 알림 필터링

사용자는 다음과 같은 기준으로 알림을 필터링할 수 있습니다:

1. **알림 유형별**
   - 모든 알림
   - 가격 알림
   - 거래 알림
   - 시스템 알림

2. **읽음 상태별**
   - 모든 알림
   - 읽지 않은 알림
   - 읽은 알림

3. **시간 범위별**
   - 모든 기간
   - 오늘
   - 지난 7일
   - 지난 30일

### 알림 관리

사용자는 다음과 같은 방법으로 알림을 관리할 수 있습니다:

1. **알림 읽음 표시**
   - 개별 알림 읽음 표시
   - 모든 알림 읽음 표시

2. **알림 삭제**
   - 개별 알림 삭제
   - 모든 알림 삭제

### 알림 설정

사용자는 다음과 같은 알림 설정을 조정할 수 있습니다:

1. **알림 활성화**
   - 가격 알림 활성화/비활성화
   - 거래 알림 활성화/비활성화
   - 시스템 알림 활성화/비활성화

2. **알림 방법**
   - 소리 알림
   - 데스크톱 알림
   - 이메일 알림 (향후 지원 예정)

3. **알림 빈도**
   - 즉시 알림
   - 시간별 요약
   - 일별 요약

4. **방해 금지 시간**
   - 방해 금지 시간 활성화/비활성화
   - 시작 시간 및 종료 시간 설정

## 사용 방법

### 알림 센터 접근

1. 메인 윈도우의 네비게이션 바에서 "모니터링 및 알림" 메뉴를 클릭합니다.
2. 또는 메뉴 바에서 "보기" > "알림 센터"를 선택합니다.
3. 독립 실행형으로 실행하려면 다음 명령을 사용합니다:

```bash
# 기본 실행
python show_notification_center.py

# 샘플 알림 개수 지정
python show_notification_center.py --sample-count 10

# 읽음 상태 필터 적용
python show_notification_center.py --read-status read
python show_notification_center.py --read-status unread
```

### 알림 필터링

1. 알림 센터 좌측 패널에서 원하는 필터 옵션을 선택합니다.
2. 필터를 초기화하려면 "필터 초기화" 버튼을 클릭합니다.

### 알림 관리

1. 개별 알림을 읽음으로 표시하려면 해당 알림의 "읽음" 버튼을 클릭합니다.
2. 개별 알림을 삭제하려면 해당 알림의 "삭제" 버튼을 클릭합니다.
3. 모든 알림을 읽음으로 표시하려면 툴바의 "모두 읽음 표시" 버튼을 클릭합니다.
4. 모든 알림을 삭제하려면 툴바의 "모두 삭제" 버튼을 클릭합니다.

### 알림 설정

1. 알림 센터 툴바에서 "알림 설정" 버튼을 클릭하거나, 메인 윈도우의 "설정" 메뉴에서 "알림" 탭을 선택합니다.
2. 원하는 알림 설정을 조정합니다.
3. 설정은 자동으로 저장됩니다.

## 개발자 가이드

### 알림 생성

알림을 생성하는 방법에는 두 가지가 있습니다:

#### 1. NotificationManager 클래스 사용

`NotificationManager` 클래스를 사용하여 알림을 생성하고 관리할 수 있습니다:

```python
from upbit_auto_trading.ui.desktop.models.notification import NotificationManager, NotificationType

# 알림 관리자 인스턴스 생성
notification_manager = NotificationManager()

# 가격 알림 생성
notification_manager.add_notification(
    notification_type=NotificationType.PRICE_ALERT,
    title="가격 알림",
    message="BTC 가격이 50,000,000원을 초과했습니다.",
    related_symbol="KRW-BTC"
)

# 거래 알림 생성
notification_manager.add_notification(
    notification_type=NotificationType.TRADE_ALERT,
    title="거래 알림",
    message="BTC 매수 주문이 체결되었습니다.",
    related_symbol="KRW-BTC"
)

# 시스템 알림 생성
notification_manager.add_notification(
    notification_type=NotificationType.SYSTEM_ALERT,
    title="시스템 알림",
    message="데이터베이스 연결이 복구되었습니다."
)
```

#### 2. NotificationFactory 클래스 사용 (권장)

`NotificationFactory` 클래스는 팩토리 패턴을 구현하여 알림 생성 로직을 캡슐화합니다. 이 방법은 코드 재사용성과 유지보수성을 향상시킵니다:

```python
from show_notification_center import NotificationFactory

# 가격 알림 생성
price_alert = NotificationFactory.create_price_alert(
    symbol="KRW-BTC",
    price=50000000,
    is_above=True  # True: 가격 초과, False: 가격 미만
)

# 거래 알림 생성
trade_alert = NotificationFactory.create_trade_alert(
    symbol="KRW-BTC",
    price=49500000,
    quantity=0.01,
    is_buy=True  # True: 매수, False: 매도
)

# 시스템 알림 생성
system_alert = NotificationFactory.create_system_alert(
    message="데이터베이스 연결이 복구되었습니다."
)
```

`NotificationFactory`는 각 알림 유형에 맞는 메시지 형식을 자동으로 생성하고, 고유한 ID를 할당하여 알림 관리를 용이하게 합니다.

### 알림 센터 확장

알림 센터를 확장하려면 다음과 같은 방법을 사용할 수 있습니다:

1. **새 알림 유형 추가**
   - `NotificationType` 열거형에 새 유형 추가
   - 해당 유형에 맞는 아이콘 및 스타일 설정

2. **새 필터 옵션 추가**
   - `NotificationFilter` 클래스에 새 필터 옵션 추가
   - 필터 UI 및 로직 구현

3. **알림 전달 방법 추가**
   - `NotificationSettings` 클래스에 새 전달 방법 옵션 추가
   - 해당 전달 방법에 대한 설정 UI 및 로직 구현

### 테스트

알림 센터는 TDD(테스트 주도 개발) 방식으로 개발되었으며, 다음과 같은 테스트가 구현되어 있습니다:

1. **알림 센터 초기화 테스트**
   - 알림 센터가 올바르게 초기화되는지 확인

2. **알림 목록 표시 테스트**
   - 알림 목록이 올바르게 표시되는지 확인

3. **알림 필터 기능 테스트**
   - 알림 필터링이 올바르게 작동하는지 확인

4. **알림 작업 테스트**
   - 알림 읽음 표시 및 삭제 기능이 올바르게 작동하는지 확인

5. **알림 설정 통합 테스트**
   - 알림 설정이 알림 센터와 올바르게 통합되는지 확인

테스트를 실행하려면 다음 명령을 사용합니다:

```bash
python -m unittest upbit_auto_trading/ui/desktop/tests/test_08_5_notification_center.py
```

## 향후 개선 사항

1. **데이터 영속성**
   - 알림 데이터를 데이터베이스에 저장하여 애플리케이션 재시작 후에도 유지

2. **실시간 알림**
   - 시스템 트레이 알림 구현
   - 푸시 알림 구현

3. **알림 우선순위**
   - 알림 우선순위 설정 및 필터링 기능 추가

4. **알림 템플릿**
   - 사용자 정의 알림 템플릿 지원

5. **알림 통계**
   - 알림 발생 빈도 및 패턴 분석 기능 추가

## 결론

알림 센터는 업비트 자동매매 시스템의 중요한 구성 요소로, 사용자에게 시스템 상태 및 중요 이벤트에 대한 정보를 제공합니다. 이 문서에서는 알림 센터의 구조, 기능, 사용 방법에 대한 가이드를 제공했습니다. 향후 개선 사항을 통해 알림 센터의 기능과 사용자 경험을 더욱 향상시킬 계획입니다.