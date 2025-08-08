# 🔐 TASK-20250808-05: API 키 설정 탭 DDD 리팩토링

## 📋 **태스크 개요**

**목표**: API 키 설정 탭을 완전한 DDD/DTO/MVP 패턴으로 리팩토링
**전제조건**: TASK-20250808-01 완료 (DDD 기반 구조)
**예상 기간**: 1-2 작업 세션

## 🎯 **API 키 설정 탭 기능**

### **1. API 키 관리**
- **키 입력/수정**: 안전한 키 입력 인터페이스
- **키 암호화 저장**: AES 암호화로 안전 보관
- **키 마스킹**: 화면에 마스킹된 형태로 표시
- **키 검증**: 입력된 키의 형식 및 유효성 검증

### **2. 연결 테스트**
- **실시간 연결 테스트**: API 엔드포인트 연결 확인
- **권한 확인**: API 키 권한 범위 확인
- **계좌 정보 조회**: 연결된 계좌 정보 표시
- **응답 시간 측정**: API 응답 성능 모니터링

### **3. 보안 설정**
- **키 만료 관리**: 키 사용 기간 설정
- **액세스 로그**: 키 사용 이력 추적
- **자동 갱신**: 주기적 키 갱신 알림
- **백업 키 관리**: 보조 키 설정

### **4. 권한 관리**
- **읽기 권한**: 조회 전용 권한 설정
- **거래 권한**: 매매 권한 설정
- **출금 권한**: 출금 권한 관리 (보안 강화)
- **권한 세분화**: 기능별 세밀한 권한 제어

## 🏗️ **DDD 아키텍처 설계**

### **Domain Layer**
```
📁 upbit_auto_trading/domain/api_settings/
├── entities/
│   ├── api_credential.py               # API 자격증명 엔티티
│   ├── connection_profile.py           # 연결 프로파일 엔티티
│   ├── security_policy.py              # 보안 정책 엔티티
│   ├── access_permission.py            # 접근 권한 엔티티
│   └── api_usage_log.py                # API 사용 로그 엔티티
├── value_objects/
│   ├── encrypted_api_key.py            # 암호화된 API 키 값 객체
│   ├── api_key_format.py               # API 키 형식 값 객체
│   ├── permission_scope.py             # 권한 범위 값 객체
│   ├── connection_status.py            # 연결 상태 값 객체
│   └── expiration_period.py            # 만료 기간 값 객체
├── services/
│   ├── api_key_validation_service.py   # API 키 검증 도메인 서비스
│   ├── encryption_service.py           # 암호화 도메인 서비스
│   ├── permission_management_service.py # 권한 관리 도메인 서비스
│   └── security_audit_service.py       # 보안 감사 도메인 서비스
└── repositories/
    ├── iapi_credential_repository.py   # API 자격증명 저장소 인터페이스
    ├── isecurity_policy_repository.py  # 보안 정책 저장소 인터페이스
    ├── iaccess_log_repository.py       # 접근 로그 저장소 인터페이스
    └── iencryption_key_repository.py   # 암호화 키 저장소 인터페이스
```

### **Application Layer**
```
📁 upbit_auto_trading/application/api_settings/
├── use_cases/
│   ├── save_api_key_use_case.py        # API 키 저장 Use Case
│   ├── update_api_key_use_case.py      # API 키 업데이트 Use Case
│   ├── delete_api_key_use_case.py      # API 키 삭제 Use Case
│   ├── test_connection_use_case.py     # 연결 테스트 Use Case
│   ├── validate_permissions_use_case.py # 권한 검증 Use Case
│   ├── rotate_api_key_use_case.py      # API 키 로테이션 Use Case
│   ├── audit_api_usage_use_case.py     # API 사용 감사 Use Case
│   └── export_credentials_use_case.py  # 자격증명 내보내기 Use Case
├── services/
│   ├── api_security_service.py         # API 보안 애플리케이션 서비스
│   ├── connection_orchestration_service.py # 연결 오케스트레이션 서비스
│   └── credential_management_service.py # 자격증명 관리 서비스
└── dtos/
    ├── api_credential_dto.py           # API 자격증명 DTO
    ├── connection_test_result_dto.py   # 연결 테스트 결과 DTO
    ├── permission_validation_dto.py    # 권한 검증 DTO
    ├── security_audit_dto.py           # 보안 감사 DTO
    └── credential_export_dto.py        # 자격증명 내보내기 DTO
```

### **Infrastructure Layer**
```
📁 upbit_auto_trading/infrastructure/api_settings/
├── repositories/
│   ├── api_credential_repository.py    # API 자격증명 Repository 구현체
│   ├── security_policy_repository.py   # 보안 정책 Repository 구현체
│   ├── access_log_repository.py        # 접근 로그 Repository 구현체
│   └── encryption_key_repository.py    # 암호화 키 Repository 구현체
├── services/
│   ├── upbit_api_client.py             # 업비트 API 클라이언트
│   ├── encryption_provider.py          # 암호화 제공자 (AES)
│   ├── key_derivation_service.py       # 키 유도 서비스 (PBKDF2)
│   └── hardware_security_module.py     # 하드웨어 보안 모듈 (선택)
├── external/
│   ├── upbit_api_connector.py          # 업비트 API 커넥터
│   └── market_data_validator.py        # 시장 데이터 검증기
└── persistence/
    ├── encrypted_storage.py            # 암호화된 저장소
    └── secure_key_vault.py             # 보안 키 저장소
```

### **Presentation Layer (MVP)**
```
📁 upbit_auto_trading/ui/desktop/screens/settings/api_settings/
├── presenters/
│   ├── api_settings_presenter.py       # API 설정 메인 프레젠터
│   ├── api_key_manager_presenter.py    # API 키 관리 프레젠터
│   ├── connection_tester_presenter.py  # 연결 테스터 프레젠터
│   ├── security_manager_presenter.py   # 보안 관리 프레젠터
│   └── permission_manager_presenter.py # 권한 관리 프레젠터
├── views/
│   ├── api_settings_view.py            # API 설정 뷰 인터페이스
│   ├── api_key_manager_view.py         # API 키 관리 뷰 인터페이스
│   ├── connection_tester_view.py       # 연결 테스터 뷰 인터페이스
│   ├── security_manager_view.py        # 보안 관리 뷰 인터페이스
│   └── permission_manager_view.py      # 권한 관리 뷰 인터페이스
├── widgets/
│   ├── api_settings_widget.py          # API 설정 메인 위젯
│   ├── secure_input_widget.py          # 보안 입력 위젯
│   ├── masked_display_widget.py        # 마스킹된 표시 위젯
│   ├── connection_status_widget.py     # 연결 상태 위젯
│   ├── permission_matrix_widget.py     # 권한 매트릭스 위젯
│   ├── api_test_widget.py              # API 테스트 위젯
│   ├── security_audit_widget.py        # 보안 감사 위젯
│   └── key_rotation_widget.py          # 키 로테이션 위젯
└── dialogs/
    ├── api_key_input_dialog.py         # API 키 입력 대화상자
    ├── connection_test_dialog.py       # 연결 테스트 대화상자
    ├── security_warning_dialog.py      # 보안 경고 대화상자
    └── key_export_dialog.py            # 키 내보내기 대화상자
```

## 📝 **작업 단계**

### **Phase 1: Domain Layer 보안 구축**
- [ ] **1.1** API 자격증명 도메인
  - ApiCredential 엔티티
  - EncryptedApiKey 값 객체
  - ApiKeyValidationService

- [ ] **1.2** 보안 정책 도메인
  - SecurityPolicy 엔티티
  - ExpirationPeriod 값 객체
  - EncryptionService

- [ ] **1.3** 권한 관리 도메인
  - AccessPermission 엔티티
  - PermissionScope 값 객체
  - PermissionManagementService

- [ ] **1.4** 보안 감사 도메인
  - ApiUsageLog 엔티티
  - SecurityAuditService

### **Phase 2: Application Layer 구축**
- [ ] **2.1** API 키 관리 Use Cases
  - SaveApiKeyUseCase (암호화 포함)
  - UpdateApiKeyUseCase
  - DeleteApiKeyUseCase
  - RotateApiKeyUseCase

- [ ] **2.2** 연결 및 검증 Use Cases
  - TestConnectionUseCase
  - ValidatePermissionsUseCase

- [ ] **2.3** 보안 관리 Use Cases
  - AuditApiUsageUseCase
  - ExportCredentialsUseCase

### **Phase 3: Infrastructure Layer 보안 구현**
- [ ] **3.1** Repository 구현체 (암호화)
  - ApiCredentialRepository (AES 암호화)
  - SecurityPolicyRepository
  - AccessLogRepository

- [ ] **3.2** 외부 연동 서비스
  - UpbitApiClient (실제 API 연동)
  - EncryptionProvider (AES-256)
  - KeyDerivationService (PBKDF2)

- [ ] **3.3** 보안 저장소
  - EncryptedStorage
  - SecureKeyVault

### **Phase 4: Presentation Layer MVP 구현**
- [ ] **4.1** API 키 관리 MVP
  - ApiKeyManagerPresenter
  - SecureInputWidget (마스킹 입력)
  - MaskedDisplayWidget

- [ ] **4.2** 연결 테스트 MVP
  - ConnectionTesterPresenter
  - ConnectionStatusWidget
  - ApiTestWidget

- [ ] **4.3** 보안 관리 MVP
  - SecurityManagerPresenter
  - SecurityAuditWidget
  - KeyRotationWidget

- [ ] **4.4** 권한 관리 MVP
  - PermissionManagerPresenter
  - PermissionMatrixWidget

## 🔒 **보안 사양**

### **암호화 표준**
- **알고리즘**: AES-256-GCM
- **키 유도**: PBKDF2 (100,000 iterations)
- **솔트**: 랜덤 256비트 솔트
- **MAC**: HMAC-SHA256 (무결성 확인)

### **키 저장 보안**
- **마스터 키**: 시스템 키체인/DPAPI 활용
- **키 분할**: 키를 여러 부분으로 분할 저장
- **메모리 보호**: 메모리에서 키 즉시 삭제
- **백업 암호화**: 백업 파일도 암호화

### **입력 보안**
- **실시간 마스킹**: 입력 중 즉시 마스킹
- **클립보드 보호**: 클립보드 내용 자동 삭제
- **스크린샷 보호**: 키 입력 시 화면 캡처 방지
- **키로거 방지**: 가상 키보드 옵션

### **접근 제어**
- **세션 타임아웃**: 비활성 시 자동 잠금
- **PIN/비밀번호**: 추가 인증 계층
- **생체 인증**: Windows Hello 지원 (선택)
- **하드웨어 토큰**: FIDO2/WebAuthn 지원 (선택)

## 📊 **보안 요구사항**

### **데이터 보호**
- [ ] API 키 AES-256 암호화
- [ ] 메모리에서 즉시 키 삭제
- [ ] 네트워크 전송 TLS 1.3
- [ ] 로그에 민감 정보 비포함

### **접근 통제**
- [ ] 사용자 인증 필수
- [ ] 세션 관리 (타임아웃)
- [ ] 권한별 접근 제어
- [ ] 감사 로그 기록

### **무결성 보장**
- [ ] 디지털 서명 검증
- [ ] 체크섬 확인
- [ ] 변조 감지
- [ ] 백업 무결성 확인

### **가용성 확보**
- [ ] 장애 복구 메커니즘
- [ ] 백업 키 지원
- [ ] 오프라인 모드 지원
- [ ] 성능 최적화

## 🧪 **보안 테스트 전략**

### **암호화 테스트**
- [ ] 암호화/복호화 정확성
- [ ] 키 유도 함수 테스트
- [ ] 랜덤성 테스트
- [ ] 성능 벤치마크

### **침투 테스트**
- [ ] SQL 인젝션 방지
- [ ] XSS 방지
- [ ] 메모리 덤프 분석
- [ ] 네트워크 스니핑 방지

### **사용성 테스트**
- [ ] 키 입력 사용성
- [ ] 에러 처리 명확성
- [ ] 복구 시나리오
- [ ] 성능 영향 최소화

---
**작업 시작일**: 2025-08-08
**전제조건**: TASK-20250808-01 완료
**다음 태스크**: TASK-20250808-06 (알림 설정 탭)
**보안 등급**: HIGH (암호화 및 보안 강화 필수)
