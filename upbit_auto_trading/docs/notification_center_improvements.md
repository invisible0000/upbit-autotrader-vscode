# 알림 센터 개선 사항 문서

## 개요

이 문서는 `show_notification_center.py` 스크립트의 개선 사항을 설명합니다. 코드 품질, 유지보수성, 확장성을 향상시키기 위한 여러 개선 사항이 적용되었습니다.

## 주요 개선 사항

### 1. 코드 구조화 및 모듈화

- **팩토리 패턴 도입**: `NotificationFactory` 클래스를 통해 알림 생성 로직을 캡슐화하여 코드 재사용성과 유지보수성을 향상시켰습니다.
- **함수 분리**: 하드코딩된 샘플 데이터를 `create_sample_notifications()` 함수로 분리하여 가독성을 높였습니다.
- **유틸리티 함수 추가**: `set_notifications()` 함수를 통해 내부 구현 세부 사항을 숨기고 인터페이스를 단순화했습니다.

### 2. 유지보수성 향상

- **상수 정의**: 하드코딩된 값을 상수로 분리하여 코드의 가독성과 유지보수성을 향상시켰습니다.
  ```python
  BTC_PRICE_THRESHOLD = 50_000_000  # 5천만원
  ETH_PRICE_THRESHOLD = 3_000_000   # 3백만원
  BTC_SYMBOL = "KRW-BTC"
  ETH_SYMBOL = "KRW-ETH"
  ```

- **명확한 주석 및 문서화**: 함수와 클래스에 자세한 docstring을 추가하여 코드의 목적과 사용 방법을 명확히 했습니다.

- **예외 처리 추가**: 예외 처리를 통해 프로그램의 안정성을 높였습니다.
  ```python
  try:
      # 코드 실행
  except Exception as e:
      print(f"오류 발생: {e}")
      sys.exit(1)
  ```

### 3. 확장성 개선

- **명령줄 인자 처리**: `argparse` 모듈을 사용하여 명령줄 인자를 처리함으로써 스크립트의 유연성을 높였습니다.
  ```python
  parser.add_argument("--sample-count", type=int, default=5, help="생성할 샘플 알림 개수")
  parser.add_argument("--read-status", choices=["all", "read", "unread"], default="all", help="알림 읽음 상태 필터")
  ```

- **팩토리 패턴**: 다양한 유형의 알림을 생성하는 팩토리 클래스를 통해 알림 생성 로직을 확장 가능하게 만들었습니다.

### 4. 테스트 가능성 향상

- **단위 테스트 추가**: 새로 추가된 기능에 대한 단위 테스트를 작성하여 코드의 신뢰성을 높였습니다.
  - `test_notification_factory.py`: 알림 팩토리 테스트
  - `test_sample_notification_generator.py`: 샘플 알림 생성기 테스트
  - `test_notification_center_integration.py`: 통합 테스트

## 사용 방법

개선된 스크립트는 다음과 같이 사용할 수 있습니다:

```bash
# 기본 실행
python show_notification_center.py

# 샘플 알림 개수 지정
python show_notification_center.py --sample-count 10

# 읽음 상태 필터 적용
python show_notification_center.py --read-status read
python show_notification_center.py --read-status unread
```

## 향후 개선 방향

1. **지연 로딩 (Lazy Loading)**: 알림 데이터를 필요할 때만 로드하여 초기 로딩 시간을 단축할 수 있습니다.
2. **가상 스크롤링 (Virtual Scrolling)**: 많은 알림이 있을 경우 화면에 보이는 부분만 렌더링하여 성능을 향상시킬 수 있습니다.
3. **옵저버 패턴 도입**: 알림 이벤트를 처리하기 위한 옵저버 패턴을 도입하여 알림 생성과 표시를 분리할 수 있습니다.