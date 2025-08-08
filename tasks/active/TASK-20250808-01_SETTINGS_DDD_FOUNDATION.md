# 🏛️ TASK-20250808-01: 설정 화면 DDD 기반 구조 확립

## 📋 **태스크 개요**

**목표**: 모든 설정 화면 기능을 DDD, DTO, MVP 원칙으로 완전히 재구축
**우선순위**: 최고 (시스템 안정성 기반)
**예상 기간**: 3-4 작업 세션

## 🎯 **핵심 목표**

### **1. 시스템 시작 안정성 보장**
- 손상된 DB 감지 시 순정 DB 자동 생성
- 프로그램 실행 보장 (어떤 상황에서도 최소 기능으로 시작)
- 사용자 친화적 에러 메시지 (시스템 오류 메시지 제거)

### **2. DDD 아키텍처 완성**
- Domain Layer: 완전한 비즈니스 로직 분리
- Application Layer: Use Case 및 Service 패턴
- Infrastructure Layer: Repository 및 외부 연동
- Presentation Layer: MVP 패턴 완성

### **3. UX 개선**
- 명확한 사용자 피드백
- 일관된 에러 처리
- 직관적인 상태 표시

## 🏗️ **아키텍처 설계**

### **Domain Layer 구조**
```
📁 upbit_auto_trading/domain/settings/
├── entities/
│   ├── database_configuration.py      # DB 구성 엔티티
│   ├── system_health_status.py        # 시스템 건강 상태
│   ├── user_preference.py             # 사용자 설정 엔티티
│   └── backup_profile.py              # 백업 프로파일
├── value_objects/
│   ├── database_path.py               # DB 경로 값 객체
│   ├── health_check_result.py         # 건강 검사 결과
│   └── validation_error.py            # 검증 오류
├── services/
│   ├── database_validation_service.py # DB 검증 도메인 서비스
│   ├── backup_management_service.py   # 백업 관리 서비스
│   └── system_recovery_service.py     # 시스템 복구 서비스
└── repositories/
    ├── idatabase_config_repository.py # DB 구성 저장소 인터페이스
    ├── iuser_settings_repository.py   # 사용자 설정 저장소 인터페이스
    └── ibackup_repository.py          # 백업 저장소 인터페이스
```

### **Application Layer 구조**
```
📁 upbit_auto_trading/application/settings/
├── use_cases/
│   ├── validate_database_health_use_case.py    # DB 건강 검증
│   ├── change_database_path_use_case.py        # DB 경로 변경
│   ├── create_backup_use_case.py               # 백업 생성
│   ├── restore_backup_use_case.py              # 백업 복원
│   └── initialize_system_databases_use_case.py # 시스템 DB 초기화
├── services/
│   ├── settings_application_service.py         # 설정 애플리케이션 서비스
│   └── backup_orchestration_service.py         # 백업 오케스트레이션
└── dtos/
    ├── database_health_dto.py                  # DB 건강 상태 DTO
    ├── validation_result_dto.py                # 검증 결과 DTO
    ├── backup_info_dto.py                      # 백업 정보 DTO
    └── system_status_dto.py                    # 시스템 상태 DTO
```

### **Presentation Layer 구조 (MVP)**
```
📁 upbit_auto_trading/ui/desktop/screens/settings/
├── presenters/
│   ├── database_tab_presenter.py              # DB 탭 프레젠터
│   ├── api_settings_presenter.py              # API 설정 프레젠터
│   ├── ui_settings_presenter.py               # UI 설정 프레젠터
│   └── notification_presenter.py              # 알림 설정 프레젠터
├── views/
│   ├── database_tab_view.py                   # DB 탭 뷰 (인터페이스)
│   └── settings_main_view.py                  # 설정 메인 뷰
├── widgets/
│   ├── database_tab_widget.py                 # DB 탭 위젯
│   ├── database_status_widget.py              # DB 상태 위젯
│   ├── backup_management_widget.py            # 백업 관리 위젯
│   └── path_selector_widget.py                # 경로 선택 위젯
└── interfaces/
    ├── database_tab_view_interface.py         # DB 탭 뷰 인터페이스
    └── settings_view_interface.py             # 설정 뷰 인터페이스
```

## 📝 **작업 단계**

### **Phase 1: Domain Layer 구축 (세션 1)**
- [ ] **1.1** 핵심 엔티티 정의
  - DatabaseConfiguration 엔티티
  - SystemHealthStatus 엔티티
  - ValidationError 값 객체

- [ ] **1.2** 도메인 서비스 구현
  - DatabaseValidationService (DB 검증 로직)
  - SystemRecoveryService (복구 로직)

- [ ] **1.3** Repository 인터페이스 정의
  - IDatabaseConfigRepository
  - IUserSettingsRepository

### **Phase 2: Application Layer 구축 (세션 2)**
- [ ] **2.1** Use Case 구현
  - ValidateDatabaseHealthUseCase
  - ChangeDatabasePathUseCase
  - InitializeSystemDatabasesUseCase

- [ ] **2.2** DTO 시스템 완성
  - DatabaseHealthDto
  - ValidationResultDto
  - SystemStatusDto

- [ ] **2.3** 애플리케이션 서비스
  - SettingsApplicationService

### **Phase 3: Infrastructure Layer 완성 (세션 3)**
- [ ] **3.1** Repository 구현체
  - DatabaseConfigRepository (YAML 기반)
  - UserSettingsRepository
  - BackupRepository

- [ ] **3.2** 시스템 초기화 로직
  - 시작 시 DB 검증
  - 순정 DB 자동 생성
  - 복구 프로세스

### **Phase 4: Presentation Layer MVP 패턴 (세션 4)**
- [ ] **4.1** Presenter 구현
  - DatabaseTabPresenter (완전한 MVP 패턴)
  - Use Case 활용 구조

- [ ] **4.2** View 인터페이스 완성
  - 명확한 View 계약
  - 사용자 친화적 메시지

- [ ] **4.3** Widget 최적화
  - DB 상태를 기반으로 한 UI 업데이트
  - 실시간 상태 반영

## 🔧 **기술적 요구사항**

### **코딩 표준**
- **DDD 원칙 엄격 준수**: Domain → Application → Infrastructure ← Presentation
- **DTO 패턴**: 계층 간 데이터 전달
- **MVP 패턴**: UI 로직과 비즈니스 로직 완전 분리
- **의존성 주입**: DI Container 활용

### **에러 처리**
- **도메인 예외**: 비즈니스 규칙 위반 시
- **인프라 예외**: 외부 시스템 연동 실패 시
- **사용자 친화적 메시지**: 시스템 오류 메시지 금지

### **테스트 전략**
- **단위 테스트**: 각 Use Case별 테스트
- **통합 테스트**: Repository 구현체 테스트
- **UI 테스트**: Presenter-View 상호작용 테스트

## 📊 **성공 기준**

### **기능적 기준**
- [ ] 손상된 DB로 시스템 시작 시 자동 복구
- [ ] 모든 설정 변경이 실시간 반영
- [ ] 백업/복원 기능 정상 동작
- [ ] 사용자 친화적 에러 메시지

### **기술적 기준**
- [ ] DDD 계층 간 의존성 규칙 준수
- [ ] 모든 비즈니스 로직이 Domain Layer에 위치
- [ ] UI가 Domain 상태를 정확히 반영
- [ ] Repository 패턴으로 데이터 접근 추상화

### **사용자 경험 기준**
- [ ] 직관적인 설정 인터페이스
- [ ] 명확한 상태 피드백
- [ ] 오류 시 해결 방법 안내
- [ ] 일관된 UI/UX 패턴

## 🚀 **다음 태스크 연결**

이 태스크 완료 후:
- **TASK-20250808-02**: 엔터프라이즈급 프로파일 시스템
- **TASK-20250808-03**: 고급 백업/복원 시스템
- **TASK-20250808-04**: 설정 화면 고도화

## 📌 **완료 체크리스트**

작업 완료 시 다음을 확인:
- [ ] `python run_desktop_ui.py` 정상 실행
- [ ] 손상된 DB 테스트 통과
- [ ] 모든 설정 탭 정상 동작
- [ ] DDD 아키텍처 검증 완료
- [ ] 사용자 시나리오 테스트 통과

---
**작업 시작일**: 2025-08-08
**담당**: LLM Agent
**관련 문서**: database_configuration_enterprise_system.md, TASK_DDD_DATABASE_SETTINGS_INTEGRATION.md
