# 🔔 TASK-20250808-06: 알림 설정 탭 DDD 리팩토링

## 📋 **태스크 개요**

**목표**: 알림 설정 탭을 완전한 DDD/DTO/MVP 패턴으로 리팩토링
**전제조건**: TASK-20250808-01 완료 (DDD 기반 구조)
**예상 기간**: 1-2 작업 세션

## 🎯 **알림 설정 탭 기능**

### **1. 거래 알림**
- **매수/매도 알림**: 거래 체결 시 즉시 알림
- **손익 알림**: 목표 수익률 달성 시 알림
- **리스크 알림**: 손실 한계 도달 시 경고
- **시장 변동 알림**: 급등/급락 시 알림

### **2. 시스템 알림**
- **연결 상태 알림**: API 연결 끊김/복구 알림
- **오류 알림**: 시스템 오류 발생 시 알림
- **보안 알림**: 보안 이벤트 감지 시 알림
- **업데이트 알림**: 소프트웨어 업데이트 안내

### **3. 알림 채널**
- **데스크톱 알림**: Windows 토스트 알림
- **이메일 알림**: SMTP 이메일 발송
- **SMS 알림**: 문자 메시지 발송 (선택)
- **푸시 알림**: 모바일 앱 연동 (선택)

### **4. 알림 스케줄**
- **시간대 설정**: 알림 허용 시간대
- **주말/휴일 설정**: 특정 날짜 알림 제어
- **빈도 제어**: 동일 알림 반복 방지
- **우선순위 설정**: 중요도별 알림 분류

## 🏗️ **DDD 아키텍처 설계**

### **Domain Layer**
```
📁 upbit_auto_trading/domain/notifications/
├── entities/
│   ├── notification_rule.py            # 알림 규칙 엔티티
│   ├── notification_channel.py         # 알림 채널 엔티티
│   ├── notification_schedule.py        # 알림 스케줄 엔티티
│   ├── notification_template.py        # 알림 템플릿 엔티티
│   └── notification_history.py         # 알림 이력 엔티티
├── value_objects/
│   ├── notification_type.py            # 알림 유형 값 객체
│   ├── notification_priority.py        # 알림 우선순위 값 객체
│   ├── channel_type.py                 # 채널 유형 값 객체
│   ├── delivery_status.py              # 전송 상태 값 객체
│   ├── time_window.py                  # 시간 창 값 객체
│   └── notification_frequency.py       # 알림 빈도 값 객체
├── services/
│   ├── notification_dispatcher.py      # 알림 발송 도메인 서비스
│   ├── channel_manager.py              # 채널 관리 도메인 서비스
│   ├── schedule_validator.py           # 스케줄 검증 도메인 서비스
│   ├── template_processor.py           # 템플릿 처리 도메인 서비스
│   └── frequency_controller.py         # 빈도 제어 도메인 서비스
└── repositories/
    ├── inotification_rule_repository.py # 알림 규칙 저장소 인터페이스
    ├── inotification_channel_repository.py # 알림 채널 저장소 인터페이스
    ├── inotification_history_repository.py # 알림 이력 저장소 인터페이스
    └── itemplate_repository.py         # 템플릿 저장소 인터페이스
```

### **Application Layer**
```
📁 upbit_auto_trading/application/notifications/
├── use_cases/
│   ├── create_notification_rule_use_case.py # 알림 규칙 생성 Use Case
│   ├── update_notification_rule_use_case.py # 알림 규칙 수정 Use Case
│   ├── delete_notification_rule_use_case.py # 알림 규칙 삭제 Use Case
│   ├── send_notification_use_case.py    # 알림 발송 Use Case
│   ├── configure_channel_use_case.py    # 채널 구성 Use Case
│   ├── test_notification_use_case.py    # 알림 테스트 Use Case
│   ├── manage_schedule_use_case.py      # 스케줄 관리 Use Case
│   └── generate_notification_report_use_case.py # 알림 리포트 생성 Use Case
├── services/
│   ├── notification_orchestration_service.py # 알림 오케스트레이션 서비스
│   ├── channel_coordination_service.py  # 채널 조정 서비스
│   └── notification_analytics_service.py # 알림 분석 서비스
└── dtos/
    ├── notification_rule_dto.py         # 알림 규칙 DTO
    ├── notification_channel_dto.py      # 알림 채널 DTO
    ├── notification_schedule_dto.py     # 알림 스케줄 DTO
    ├── notification_test_dto.py         # 알림 테스트 DTO
    ├── notification_delivery_dto.py     # 알림 전송 DTO
    └── notification_report_dto.py       # 알림 리포트 DTO
```

### **Infrastructure Layer**
```
📁 upbit_auto_trading/infrastructure/notifications/
├── repositories/
│   ├── notification_rule_repository.py  # 알림 규칙 Repository 구현체
│   ├── notification_channel_repository.py # 알림 채널 Repository 구현체
│   ├── notification_history_repository.py # 알림 이력 Repository 구현체
│   └── template_repository.py           # 템플릿 Repository 구현체
├── channels/
│   ├── desktop_notification_channel.py  # 데스크톱 알림 채널
│   ├── email_notification_channel.py    # 이메일 알림 채널
│   ├── sms_notification_channel.py      # SMS 알림 채널
│   └── push_notification_channel.py     # 푸시 알림 채널
├── providers/
│   ├── smtp_email_provider.py           # SMTP 이메일 제공자
│   ├── twilio_sms_provider.py           # Twilio SMS 제공자
│   ├── firebase_push_provider.py        # Firebase 푸시 제공자
│   └── windows_toast_provider.py        # Windows 토스트 제공자
├── external/
│   ├── email_service_connector.py       # 외부 이메일 서비스 커넥터
│   ├── sms_service_connector.py         # 외부 SMS 서비스 커넥터
│   └── push_service_connector.py        # 외부 푸시 서비스 커넥터
└── persistence/
    ├── notification_storage.py          # 알림 저장소
    └── notification_queue.py            # 알림 큐 관리
```

### **Presentation Layer (MVP)**
```
📁 upbit_auto_trading/ui/desktop/screens/settings/notifications/
├── presenters/
│   ├── notification_settings_presenter.py # 알림 설정 메인 프레젠터
│   ├── rule_manager_presenter.py        # 규칙 관리 프레젠터
│   ├── channel_manager_presenter.py     # 채널 관리 프레젠터
│   ├── schedule_manager_presenter.py    # 스케줄 관리 프레젠터
│   └── notification_tester_presenter.py # 알림 테스터 프레젠터
├── views/
│   ├── notification_settings_view.py    # 알림 설정 뷰 인터페이스
│   ├── rule_manager_view.py             # 규칙 관리 뷰 인터페이스
│   ├── channel_manager_view.py          # 채널 관리 뷰 인터페이스
│   ├── schedule_manager_view.py         # 스케줄 관리 뷰 인터페이스
│   └── notification_tester_view.py      # 알림 테스터 뷰 인터페이스
├── widgets/
│   ├── notification_settings_widget.py  # 알림 설정 메인 위젯
│   ├── rule_editor_widget.py            # 규칙 편집 위젯
│   ├── rule_list_widget.py              # 규칙 목록 위젯
│   ├── channel_configuration_widget.py  # 채널 구성 위젯
│   ├── schedule_editor_widget.py        # 스케줄 편집 위젯
│   ├── notification_preview_widget.py   # 알림 미리보기 위젯
│   ├── notification_test_widget.py      # 알림 테스트 위젯
│   ├── notification_history_widget.py   # 알림 이력 위젯
│   └── frequency_control_widget.py      # 빈도 제어 위젯
└── dialogs/
    ├── rule_creation_dialog.py          # 규칙 생성 대화상자
    ├── channel_setup_dialog.py          # 채널 설정 대화상자
    ├── notification_test_dialog.py      # 알림 테스트 대화상자
    └── schedule_picker_dialog.py        # 스케줄 선택 대화상자
```

## 📝 **작업 단계**

### **Phase 1: Domain Layer 알림 시스템 구축**
- [ ] **1.1** 알림 규칙 도메인
  - NotificationRule 엔티티
  - NotificationType 값 객체
  - NotificationPriority 값 객체

- [ ] **1.2** 알림 채널 도메인
  - NotificationChannel 엔티티
  - ChannelType 값 객체
  - DeliveryStatus 값 객체

- [ ] **1.3** 스케줄링 도메인
  - NotificationSchedule 엔티티
  - TimeWindow 값 객체
  - NotificationFrequency 값 객체

- [ ] **1.4** 알림 서비스
  - NotificationDispatcher
  - ChannelManager
  - ScheduleValidator
  - FrequencyController

### **Phase 2: Application Layer 구축**
- [ ] **2.1** 규칙 관리 Use Cases
  - CreateNotificationRuleUseCase
  - UpdateNotificationRuleUseCase
  - DeleteNotificationRuleUseCase

- [ ] **2.2** 채널 관리 Use Cases
  - ConfigureChannelUseCase
  - TestNotificationUseCase

- [ ] **2.3** 스케줄 관리 Use Cases
  - ManageScheduleUseCase
  - SendNotificationUseCase

- [ ] **2.4** 분석 및 리포팅 Use Cases
  - GenerateNotificationReportUseCase

### **Phase 3: Infrastructure Layer 구현**
- [ ] **3.1** Repository 구현체
  - NotificationRuleRepository
  - NotificationChannelRepository
  - NotificationHistoryRepository
  - TemplateRepository

- [ ] **3.2** 알림 채널 구현
  - DesktopNotificationChannel (Windows Toast)
  - EmailNotificationChannel (SMTP)
  - SmsNotificationChannel (선택사항)
  - PushNotificationChannel (선택사항)

- [ ] **3.3** 외부 서비스 연동
  - SmtpEmailProvider
  - WindowsToastProvider
  - (선택) TwilioSmsProvider
  - (선택) FirebasePushProvider

### **Phase 4: Presentation Layer MVP 구현**
- [ ] **4.1** 규칙 관리 MVP
  - RuleManagerPresenter
  - RuleEditorWidget
  - RuleListWidget

- [ ] **4.2** 채널 관리 MVP
  - ChannelManagerPresenter
  - ChannelConfigurationWidget

- [ ] **4.3** 스케줄 관리 MVP
  - ScheduleManagerPresenter
  - ScheduleEditorWidget

- [ ] **4.4** 테스트 및 미리보기 MVP
  - NotificationTesterPresenter
  - NotificationTestWidget
  - NotificationPreviewWidget

## 🔔 **알림 채널 사양**

### **데스크톱 알림 (Windows Toast)**
- **플랫폼**: Windows 10/11 Toast Notifications
- **표시 위치**: 화면 우하단
- **표시 시간**: 5-10초 (사용자 설정)
- **액션 버튼**: 확인, 무시, 설정으로 이동

### **이메일 알림**
- **프로토콜**: SMTP (TLS 1.2+)
- **지원 서비스**: Gmail, Outlook, Yahoo, 커스텀 SMTP
- **템플릿**: HTML + 텍스트 듀얼 포맷
- **첨부파일**: 거래 보고서, 차트 이미지 (선택)

### **SMS 알림 (선택사항)**
- **제공자**: Twilio, AWS SNS
- **국가 지원**: 한국, 미국, 기타
- **메시지 길이**: 160자 제한
- **요금**: 사용량 기반 과금

### **푸시 알림 (선택사항)**
- **플랫폼**: Firebase Cloud Messaging
- **대상**: 모바일 앱, 웹 앱
- **배치**: 배지, 사운드, 진동
- **딥링크**: 앱 내 특정 화면으로 이동

## 📋 **알림 규칙 사양**

### **거래 알림 규칙**
```yaml
trade_notifications:
  - name: "매수 체결 알림"
    type: "TRADE_BUY_EXECUTED"
    conditions:
      - amount_gte: 10000  # 1만원 이상
    channels: ["desktop", "email"]
    priority: "HIGH"

  - name: "손익 목표 달성"
    type: "PROFIT_TARGET_REACHED"
    conditions:
      - profit_rate_gte: 5.0  # 5% 이상 수익
    channels: ["desktop", "email", "sms"]
    priority: "CRITICAL"
```

### **시스템 알림 규칙**
```yaml
system_notifications:
  - name: "API 연결 끊김"
    type: "API_CONNECTION_LOST"
    conditions:
      - duration_gte: 30  # 30초 이상 끊김
    channels: ["desktop", "email"]
    priority: "HIGH"

  - name: "보안 이벤트"
    type: "SECURITY_EVENT"
    conditions:
      - event_type: ["login_failed", "api_key_changed"]
    channels: ["email", "sms"]
    priority: "CRITICAL"
```

### **스케줄 설정**
```yaml
schedule_settings:
  time_windows:
    - name: "거래 시간"
      start: "09:00"
      end: "15:30"
      days: ["MON", "TUE", "WED", "THU", "FRI"]

  frequency_limits:
    - rule_type: "PRICE_ALERT"
      max_per_hour: 5
      cooldown_minutes: 10
```

## 📊 **성공 기준**

### **기능적 기준**
- [ ] 모든 알림 유형 지원
- [ ] 다중 채널 동시 발송
- [ ] 스케줄 기반 알림 제어
- [ ] 알림 이력 및 통계

### **성능 기준**
- [ ] 알림 발송 시간 < 3초
- [ ] 동시 알림 처리 > 100개/분
- [ ] 이메일 전송 성공률 > 95%
- [ ] 데스크톱 알림 표시 시간 < 1초

### **안정성 기준**
- [ ] 네트워크 장애 시 재시도
- [ ] 알림 큐 지속성 보장
- [ ] 채널 장애 시 대체 채널 사용
- [ ] 스팸 방지 및 빈도 제어

### **사용성 기준**
- [ ] 직관적인 규칙 생성 인터페이스
- [ ] 실시간 알림 미리보기
- [ ] 쉬운 채널 설정
- [ ] 명확한 테스트 기능

## 🧪 **테스트 전략**

### **단위 테스트**
- [ ] 알림 규칙 검증 테스트
- [ ] 채널별 발송 테스트
- [ ] 스케줄링 로직 테스트
- [ ] 템플릿 처리 테스트

### **통합 테스트**
- [ ] 외부 서비스 연동 테스트
- [ ] 다중 채널 동시 발송 테스트
- [ ] 장애 복구 시나리오 테스트

### **사용자 테스트**
- [ ] 알림 설정 사용성 테스트
- [ ] 알림 수신 확인 테스트
- [ ] 스케줄 동작 검증 테스트

---
**작업 시작일**: 2025-08-08
**전제조건**: TASK-20250808-01 완료
**다음 태스크**: TASK-20250808-07 (고급 설정 탭)
**외부 의존성**: SMTP 서버, (선택) SMS 서비스
