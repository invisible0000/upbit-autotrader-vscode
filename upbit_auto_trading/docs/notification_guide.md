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

### 알림 중복 방지

알림 시스템에서 가장 중요한 문제 중 하나는 동일한 알림이 반복적으로 발생하는 것입니다. 이를 방지하기 위해 알림 이력을 관리하는 메커니즘을 구현해야 합니다:

```python
# 알림 이력 관리를 위한 집합 생성
self.notified_errors = set()

def notify_error(self, component, message, is_critical=False):
    # 중복 알림 방지를 위한 키 생성
    error_key = f"{component}:{message}"
    if error_key in self.notified_errors:
        return
    
    # 알림 생성 로직...
    
    # 알림 이력에 추가
    self.notified_errors.add(error_key)
```

임계값 변경 시 관련 알림 이력을 초기화하는 것이 좋습니다:

```python
def set_cpu_threshold(self, threshold):
    self.cpu_threshold = max(1, min(100, threshold))
    # 임계값 변경 시 알림 이력 초기화
    self.notified_resources = set(r for r in self.notified_resources if not r.startswith("cpu:"))
```

### 멀티스레딩 안전성

알림 시스템은 여러 스레드에서 동시에 접근할 수 있으므로, 스레드 안전성을 보장해야 합니다:

```python
import threading

# 락 객체 생성
self.lock = threading.Lock()

def get_notifications(self):
    # 공유 데이터 접근 시 락 사용
    with self.lock:
        return self._notifications.copy()
```

모니터링 스레드는 데몬 스레드로 설정하여 메인 프로그램 종료 시 자동으로 종료되도록 합니다:

```python
def start_monitoring(self):
    # 모니터링 스레드 시작
    self.monitoring_thread = threading.Thread(target=monitoring_task, daemon=True)
    self.monitoring_thread.start()
```

### 파일 경로 및 권한 관리

알림 설정 저장 및 로드 시 파일 경로와 권한을 적절히 관리해야 합니다:

```python
def save_settings(self, file_path):
    try:
        # 디렉토리 경로 확인
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # 설정 저장 로직...
        
    except Exception as e:
        print(f"알림 설정 저장 중 오류 발생: {e}")
        return False
```

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

## 개발 시 주의사항 및 모범 사례

모니터링 및 알림 시스템 구현 과정에서 발견한 주요 문제점과 해결 방법, 그리고 향후 개발 시 고려해야 할 사항들을 정리했습니다. 자세한 내용은 [개발 진행 현황](development_progress.md) 문서에서도 확인할 수 있습니다.

### 1. 알림 중복 방지

알림 시스템에서 가장 중요한 문제 중 하나는 동일한 알림이 반복적으로 발생하는 것입니다. 이는 사용자 경험을 저하시키고 중요한 알림을 놓치게 만들 수 있습니다.

#### 구현 방법

```python
# 알림 이력 관리를 위한 집합 생성
self.notified_errors = set()

def notify_error(self, component, message, is_critical=False):
    # 중복 알림 방지를 위한 키 생성
    error_key = f"{component}:{message}"
    if error_key in self.notified_errors:
        return
    
    # 알림 생성 로직...
    
    # 알림 이력에 추가
    self.notified_errors.add(error_key)
```

#### 모범 사례

- 알림 유형별로 별도의 이력 관리 집합을 사용합니다.
- 임계값 변경 시 관련 알림 이력을 초기화합니다.
- 시간 기반 알림 재설정 메커니즘을 구현합니다(예: 24시간 후 동일 알림 재발생 허용).

### 2. 멀티스레딩 안전성

알림 시스템은 여러 스레드에서 동시에 접근할 수 있으므로, 스레드 안전성을 보장해야 합니다.

#### 구현 방법

```python
import threading

# 락 객체 생성
self.lock = threading.Lock()

def get_notifications(self):
    # 공유 데이터 접근 시 락 사용
    with self.lock:
        return self._notifications.copy()
```

#### 모범 사례

- 공유 데이터 접근 시 항상 락을 사용합니다.
- 데이터 반환 시 원본이 아닌 복사본을 반환합니다.
- 모니터링 스레드는 데몬 스레드로 설정하여 메인 프로그램 종료 시 자동으로 종료되도록 합니다.
- 장시간 실행되는 작업은 별도의 스레드로 분리하여 UI 응답성을 유지합니다.

### 3. 알림 설정 관리

사용자가 알림 설정을 쉽게 관리할 수 있도록 직관적인 인터페이스와 영속적인 설정 저장 메커니즘을 제공해야 합니다.

#### 구현 방법

```python
def save_settings(self, file_path):
    try:
        # 디렉토리 경로 확인
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # 설정 데이터
        settings = {
            "enable_price_alerts": self.enable_price_alerts,
            "enable_trade_alerts": self.enable_trade_alerts,
            "enable_system_alerts": self.enable_system_alerts,
            # 기타 설정...
        }
        
        # JSON 파일로 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"알림 설정 저장 중 오류 발생: {e}")
        return False
```

#### 모범 사례

- 설정 파일은 사용자 홈 디렉토리나 애플리케이션 데이터 디렉토리와 같은 표준 위치에 저장합니다.
- 설정 변경 시 자동으로 저장하여 사용자 설정이 유지되도록 합니다.
- 설정 로드 실패 시 기본값을 사용하여 애플리케이션이 정상적으로 동작하도록 합니다.
- 설정 UI는 직관적이고 사용하기 쉽게 설계합니다.

### 4. 외부 의존성 관리

알림 시스템은 다양한 외부 패키지에 의존할 수 있습니다. 이러한 의존성을 적절히 관리하여 시스템의 안정성을 보장해야 합니다.

#### 구현 방법

```python
# psutil 패키지 임포트 시도
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil package not available. Resource monitoring will be limited.")

def check_cpu_usage(self):
    if not PSUTIL_AVAILABLE:
        # 대체 로직 또는 기능 비활성화
        return
    # 정상 로직 실행
```

#### 모범 사례

- 핵심 기능에 필수적인 패키지와 선택적 기능에 사용되는 패키지를 구분하여 관리합니다.
- 선택적 패키지는 없어도 기본 기능이 동작하도록 예외 처리를 추가합니다.
- 모든 외부 패키지 의존성은 `requirements.txt`에 명시적으로 기록합니다.
- 애플리케이션 시작 시 필요한 패키지가 설치되어 있는지 확인하고, 없으면 사용자에게 알림을 제공합니다.

## 향후 개선 사항

1. **데이터 영속성**
   - 알림 데이터를 데이터베이스에 저장하여 애플리케이션 재시작 후에도 유지
   - SQLite 또는 PostgreSQL을 사용하여 알림 데이터 저장 및 관리

2. **실시간 알림**
   - 시스템 트레이 알림 구현
   - 푸시 알림 구현
   - 이메일 알림 지원

3. **알림 우선순위 및 그룹화**
   - 알림 우선순위 설정 및 필터링 기능 추가
   - 유사한 알림을 그룹화하여 표시하는 기능 구현
   - 알림 발생 빈도 제한 메커니즘 구현

4. **알림 템플릿 및 사용자 정의**
   - 사용자 정의 알림 템플릿 지원
   - 알림 형식 및 내용 커스터마이징 기능
   - 조건부 알림 설정 지원

5. **알림 통계 및 분석**
   - 알림 발생 빈도 및 패턴 분석 기능 추가
   - 알림 대시보드 구현
   - 알림 효과성 분석 도구 제공

6. **분산 환경 지원**
   - 여러 인스턴스 간 알림 동기화 메커니즘 구현
   - 중앙 집중식 알림 관리 시스템 구축
   - 클라우드 기반 알림 서비스 통합

## 결론

알림 센터는 업비트 자동매매 시스템의 중요한 구성 요소로, 사용자에게 시스템 상태 및 중요 이벤트에 대한 정보를 제공합니다. 이 문서에서는 알림 센터의 구조, 기능, 사용 방법에 대한 가이드를 제공했습니다. 향후 개선 사항을 통해 알림 센터의 기능과 사용자 경험을 더욱 향상시킬 계획입니다.