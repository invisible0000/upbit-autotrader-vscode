# 🏢 TASK-20250808-02: 엔터프라이즈급 프로파일 시스템

## 📋 **태스크 개요**

**목표**: 다중 환경 지원을 위한 엔터프라이즈급 데이터베이스 프로파일 관리 시스템 구현
**전제조건**: TASK-20250808-01 완료 (DDD 기반 구조 확립)
**예상 기간**: 2-3 작업 세션

## 🎯 **핵심 기능**

### **1. 다중 환경 프로파일**
- **개발 환경**: 로컬 개발용 DB 구성
- **테스트 환경**: 테스트 데이터 및 설정
- **운영 환경**: 실제 거래용 DB 구성
- **백업 환경**: 백업 전용 구성

### **2. 프로파일 관리**
- **프로파일 생성**: 새로운 환경 구성 생성
- **프로파일 복제**: 기존 환경을 기반으로 새 환경 생성
- **프로파일 전환**: 안전한 환경 전환 (검증 포함)
- **프로파일 삭제**: 안전한 삭제 (백업 확인 후)

### **3. 고급 백업 시스템**
- **전체 환경 백업**: 모든 DB + 설정 파일
- **증분 백업**: 변경된 내용만 백업
- **스케줄 백업**: 자동 백업 스케줄링
- **클라우드 백업**: 외부 저장소 연동 (선택사항)

## 🏗️ **확장 아키텍처**

### **Domain Layer 확장**
```
📁 upbit_auto_trading/domain/profiles/
├── entities/
│   ├── environment_profile.py         # 환경 프로파일 엔티티
│   ├── profile_template.py            # 프로파일 템플릿
│   ├── backup_schedule.py             # 백업 스케줄 엔티티
│   └── profile_migration.py           # 프로파일 마이그레이션
├── value_objects/
│   ├── environment_type.py            # 환경 타입 (DEV/TEST/PROD)
│   ├── backup_frequency.py            # 백업 주기
│   └── profile_status.py              # 프로파일 상태
├── services/
│   ├── profile_validation_service.py  # 프로파일 검증
│   ├── profile_migration_service.py   # 프로파일 마이그레이션
│   └── backup_strategy_service.py     # 백업 전략 서비스
└── repositories/
    ├── iprofile_repository.py          # 프로파일 저장소 인터페이스
    └── ibackup_schedule_repository.py  # 백업 스케줄 저장소
```

### **Application Layer 확장**
```
📁 upbit_auto_trading/application/profiles/
├── use_cases/
│   ├── create_profile_use_case.py      # 프로파일 생성
│   ├── switch_profile_use_case.py      # 프로파일 전환
│   ├── clone_profile_use_case.py       # 프로파일 복제
│   ├── backup_profile_use_case.py      # 프로파일 백업
│   └── migrate_profile_use_case.py     # 프로파일 마이그레이션
├── services/
│   ├── profile_orchestration_service.py # 프로파일 오케스트레이션
│   └── backup_automation_service.py     # 백업 자동화 서비스
└── dtos/
    ├── profile_info_dto.py             # 프로파일 정보 DTO
    ├── backup_status_dto.py            # 백업 상태 DTO
    └── migration_result_dto.py         # 마이그레이션 결과
```

### **UI 확장**
```
📁 upbit_auto_trading/ui/desktop/screens/profiles/
├── presenters/
│   ├── profile_manager_presenter.py    # 프로파일 관리 프레젠터
│   └── backup_scheduler_presenter.py   # 백업 스케줄러 프레젠터
├── widgets/
│   ├── profile_selector_widget.py      # 프로파일 선택 위젯
│   ├── profile_creator_widget.py       # 프로파일 생성 위젯
│   ├── backup_scheduler_widget.py      # 백업 스케줄러 위젯
│   └── environment_status_widget.py    # 환경 상태 위젯
└── dialogs/
    ├── profile_creation_dialog.py      # 프로파일 생성 대화상자
    └── backup_restore_dialog.py        # 백업/복원 대화상자
```

## 📝 **작업 단계**

### **Phase 1: Profile Domain 구축**
- [ ] **1.1** 프로파일 엔티티 구현
  - EnvironmentProfile 엔티티
  - ProfileTemplate 엔티티
  - EnvironmentType 값 객체

- [ ] **1.2** 프로파일 도메인 서비스
  - ProfileValidationService
  - ProfileMigrationService

### **Phase 2: Profile Use Cases**
- [ ] **2.1** 핵심 Use Case 구현
  - CreateProfileUseCase
  - SwitchProfileUseCase
  - CloneProfileUseCase

- [ ] **2.2** 백업 Use Cases
  - BackupProfileUseCase
  - RestoreProfileUseCase

### **Phase 3: UI Integration**
- [ ] **3.1** 프로파일 관리 UI
  - ProfileManagerPresenter
  - ProfileSelectorWidget

- [ ] **3.2** 백업 관리 UI
  - BackupSchedulerWidget
  - 자동 백업 설정

## 🔧 **기술적 사양**

### **프로파일 구조**
```yaml
# profile_template.yaml
profile:
  id: "dev_environment_001"
  name: "개발 환경"
  type: "DEVELOPMENT"
  created_at: "2025-08-08T20:00:00Z"
  databases:
    settings: "data/dev/settings.sqlite3"
    strategies: "data/dev/strategies.sqlite3"
    market_data: "data/dev/market_data.sqlite3"
  configurations:
    api_mode: "sandbox"
    log_level: "DEBUG"
    auto_backup: true
  backup_schedule:
    frequency: "DAILY"
    time: "02:00"
    retention_days: 30
```

### **백업 전략**
- **전체 백업**: 주 단위
- **증분 백업**: 일 단위
- **설정 백업**: 변경 시 즉시
- **압축 백업**: ZIP 형태로 저장

## 📊 **성공 기준**

### **기능적 기준**
- [ ] 3가지 이상 환경 프로파일 지원
- [ ] 프로파일 간 안전한 전환
- [ ] 자동 백업 시스템 동작
- [ ] 프로파일 마이그레이션 성공

### **성능 기준**
- [ ] 프로파일 전환 시간 < 5초
- [ ] 백업 완료 시간 < 30초
- [ ] UI 응답성 유지

### **안정성 기준**
- [ ] 프로파일 전환 실패 시 롤백
- [ ] 백업 무결성 검증
- [ ] 데이터 손실 방지

---
**작업 시작일**: 2025-08-08
**전제조건**: TASK-20250808-01 완료
**다음 태스크**: TASK-20250808-03
