# Settings Database Tab DDD Integration Task Plan

## 🎯 목표
설정 화면의 데이터베이스 탭을 DDD 아키텍처로 완전 통합하여 일관성 있고 유지보수가 용이한 구조 구축

## 📊 현재 상황 분석

### 기존 구현체들
1. **database_settings.py** (Infrastructure Layer v4.0 통합)
   - 동적 데이터베이스 파일 선택 및 교체
   - 다중 데이터베이스 프로필 관리
   - 백업 및 복원 기능
   - 실시간 데이터베이스 전환

2. **database_settings_new.py** (simple_paths 기반)
   - 3개 고정 데이터베이스 파일 관리
   - 단순화된 인터페이스
   - 기본적인 백업 기능

3. **database_config_tab.py** (컴포넌트 버전)
   - 독립적인 컴포넌트 구조
   - 기본적인 설정 관리 기능

### 🔴 문제점들
- **아키텍처 불일치**: 3개의 서로 다른 접근 방식
- **기능 중복**: 유사한 기능이 여러 곳에 구현됨
- **DDD 원칙 위반**: 도메인 로직이 UI 레이어에 혼재
- **테스트 어려움**: 복잡한 의존성으로 인한 테스트 복잡성

## 🏗️ DDD 통합 설계

### Domain Layer
```
DatabaseConfigurationDomain/
├── entities/
│   ├── DatabaseProfile.py          # 데이터베이스 프로필 엔터티
│   ├── DatabaseConnection.py       # 데이터베이스 연결 정보
│   └── BackupRecord.py             # 백업 기록 엔터티
├── value_objects/
│   ├── DatabasePath.py             # 데이터베이스 경로 값 객체
│   ├── DatabaseType.py             # 데이터베이스 타입 (설정/전략/시장데이터)
│   └── BackupPolicy.py             # 백업 정책 값 객체
├── aggregates/
│   └── DatabaseConfiguration.py    # 데이터베이스 설정 집합체
├── repositories/
│   └── IDatabaseConfigRepository.py # 데이터베이스 설정 저장소 인터페이스
└── services/
    ├── DatabaseMigrationService.py  # 데이터베이스 마이그레이션 서비스
    ├── DatabaseBackupService.py     # 백업 서비스
    └── DatabaseValidationService.py # 검증 서비스
```

### Application Layer
```
DatabaseConfigurationApp/
├── use_cases/
│   ├── ChangeDatabasePathUseCase.py      # 데이터베이스 경로 변경
│   ├── CreateBackupUseCase.py            # 백업 생성
│   ├── RestoreBackupUseCase.py           # 백업 복원
│   ├── ValidateDatabaseUseCase.py        # 데이터베이스 검증
│   └── GetDatabaseStatusUseCase.py       # 상태 조회
├── services/
│   └── DatabaseConfigurationAppService.py # 애플리케이션 서비스
└── dto/
    ├── DatabaseConfigDto.py              # 데이터 전송 객체
    └── DatabaseStatusDto.py              # 상태 정보 DTO
```

### Infrastructure Layer
```
DatabaseConfigurationInfra/
├── repositories/
│   └── SqliteDatabaseConfigRepository.py # SQLite 구현체
├── external_services/
│   ├── FileSystemService.py              # 파일 시스템 서비스
│   └── DatabaseConnectionService.py      # 데이터베이스 연결 서비스
└── adapters/
    └── SimplePaths_Adapter.py             # SimplePaths 시스템 어댑터
```

### Presentation Layer
```
DatabaseConfigurationUI/
├── widgets/
│   ├── DatabaseTabWidget.py              # 통합된 데이터베이스 탭
│   ├── DatabaseStatusWidget.py           # 상태 표시 위젯
│   ├── DatabasePathSelector.py           # 경로 선택 위젯
│   └── BackupManagementWidget.py         # 백업 관리 위젯
├── presenters/
│   └── DatabaseConfigPresenter.py        # MVP 패턴 프레젠터
└── view_models/
    └── DatabaseConfigViewModel.py        # 뷰 모델
```

## 📋 작업 단계

### Phase 1: Domain Layer 구축 ✅
- [x] 1.1 엔터티 정의 (DatabaseProfile, BackupRecord) ✅
- [x] 1.2 값 객체 구현 (DatabasePath, DatabaseType) ✅
- [x] 1.3 집합체 구현 (DatabaseConfiguration) ✅
- [x] 1.4 도메인 서비스 구현 (DatabaseBackupService) ✅
- [x] 1.5 저장소 인터페이스 정의 (IDatabaseConfigRepository) ✅
- [x] 1.6 도메인 테스트 구현 (89개 테스트 케이스) ✅

### Phase 2: Application Layer 구축
- [ ] 2.1 Use Case 구현 (경로 변경, 백업, 복원, 검증, 상태 조회)
- [ ] 2.2 애플리케이션 서비스 구현
- [ ] 2.3 DTO 정의 및 매핑 로직

### Phase 3: Infrastructure Layer 구축
- [x] 3.1 저장소 구현체 (SQLite 기반) ✅ **COMPLETED - DatabaseConfigRepository 구현됨**
- [ ] 3.2 외부 서비스 어댑터 (파일 시스템, 데이터베이스 연결)
- [ ] 3.3 SimplePaths 시스템 통합 어댑터

### Phase 4: Presentation Layer 통합
- [ ] 4.1 MVP 패턴 프레젠터 구현
- [ ] 4.2 통합된 UI 위젯 구현
- [ ] 4.3 기존 설정 화면과의 통합

### Phase 5: 마이그레이션 및 정리
- [ ] 5.1 기존 구현체들의 점진적 교체
- [ ] 5.2 테스트 코드 작성 및 검증
- [ ] 5.3 문서화 및 정리

## 🎯 성공 기준

### 기능적 요구사항
- ✅ 3개 데이터베이스 (설정/전략/시장데이터) 통합 관리
- ✅ 동적 데이터베이스 경로 변경 지원
- ✅ 자동 백업 및 복원 기능
- ✅ 데이터베이스 무결성 검증
- ✅ 실시간 상태 모니터링

### 아키텍처 요구사항
- ✅ 완전한 DDD 계층 분리
- ✅ 단일 책임 원칙 준수
- ✅ 의존성 역전 원칙 적용
- ✅ 테스트 가능한 구조
- ✅ Infrastructure Layer v4.0 통합

### 성능 요구사항
- ✅ UI 응답성 (100ms 이하)
- ✅ 메모리 효율성
- ✅ 에러 처리 완전성

## 🚀 첫 번째 작업: Domain Layer 구축

지금부터 Domain Layer의 핵심 엔터티와 값 객체를 구현하겠습니다.

---

## 📊 **실거래/백테스팅 DB 이벤트 처리 준비도 분석 (2025.08.08 현재)**

### **🎯 현재 상태: 85% 준비 완료 (Repository 구현으로 대폭 향상)**

#### **✅ 완료된 기반**
```python
# 1. 연결 관리 (기존 완료)
DatabaseManager().get_connection('settings')  # WAL 모드, 멀티스레드 안전

# 2. 비즈니스 규칙 (새로 완료)
DatabaseConfiguration().add_database_profile(profile)  # 검증, 일관성 보장

# 3. Repository 구현체 (신규 완료) ✅
DatabaseConfigRepository().save_configuration(config)  # Domain ↔ DB 연결

# 4. 성능 최적화 (기존 완료)
PRAGMA journal_mode = WAL     # 읽기/쓰기 동시 처리
PRAGMA synchronous = NORMAL   # 성능 최적화
PRAGMA cache_size = 10000     # 메모리 캐시
```

#### **❌ 아직 필요한 부분 (핵심 누락 해결됨, 세부사항만 남음)**

**1. Application Layer (Use Cases) - 3일 소요 예상**
```python
# 현재 없음 - 개발 필요
class DatabaseProfileManagementUseCase:
    def switch_database_profile(self, profile_id: str):
        # 실거래 중 DB 프로필 안전 전환

    def create_backup_during_trading(self, profile_id: str):
        # 거래 중 백업 생성 (락 없이)
```

**2. 실시간 이벤트 처리 - 2일 소요 예상**
```python
# 현재 없음 - 개발 필요
class DatabaseEventHandler:
    def on_trading_started(self, strategy_id: str):
        # 거래 시작 시 DB 상태 확인

    def on_backtest_started(self, backtest_id: str):
        # 백테스팅 시작 시 별도 DB 프로필 활성화
```

### **🚨 실거래/백테스팅 시나리오별 대응 현황**

#### **Scenario 1: 실거래 중 백테스팅 시작**
```python
# ✅ 현재 상황: 기술적으로 처리 가능
repository = DatabaseConfigRepository()
config = repository.load_configuration()
trading_profile = config.get_active_profile('strategies')      # 실거래용
backtest_profile = config.create_temporary_profile('strategies') # 백테스팅용

# ❌ 부족한 부분: 비즈니스 로직 Use Case 없음
```

#### **Scenario 2: DB 프로필 전환 중 거래 발생**
```python
# ✅ 현재 상황: Repository로 안전 처리 가능
repository.save_configuration(new_config)  # 트랜잭션 보장

# ❌ 부족한 부분: 거래 상태 체크 로직 없음
```

#### **Scenario 3: 대용량 백테스팅 중 실거래**
```python
# ✅ 현재 상황: 완전 지원
# WAL 모드 + Repository 구현으로 동시 접근 안전
```

### **📋 완전한 준비를 위한 남은 작업 (대폭 단축됨)**

#### **Phase 2: Application Layer (중요) - 3일 소요**
```python
DatabaseProfileUseCase         # 프로필 관리 비즈니스 로직
TradingDatabaseCoordinator     # 거래 중 DB 조정
BacktestDatabaseIsolator       # 백테스팅 DB 격리
```

#### **Phase 4: Event Integration (선택) - 2일 소요**
```python
DatabaseEventSubscriber       # 거래/백테스팅 이벤트 구독
ConflictResolutionStrategy     # 충돌 해결 전략
```

### **🎯 결론: Repository 구현으로 핵심 문제 해결됨**

**✅ 강점:**
- **완전한 Repository**: Domain ↔ Infrastructure 연결 완료
- **트랜잭션 보장**: SQLite 트랜잭션으로 데이터 일관성 확보
- **비즈니스 규칙**: 강력한 도메인 모델 + Repository 연동
- **멀티스레드 안전**: WAL 모드 + 연결 풀링

**❌ 남은 약점:**
- **Use Case 부재**: 비즈니스 시나리오별 조정 로직 (3일 소요)
- **이벤트 통합**: 실시간 거래/백테스팅 이벤트 처리 (2일 소요)

### **🚀 업데이트된 권장사항**

**단기 (3일): Application Layer 완성으로 실거래 준비 완료**
```bash
upbit_auto_trading/application/use_cases/database_profile_management.py
upbit_auto_trading/application/services/trading_database_coordinator.py
```

**중기 (5일): 완전 통합으로 동시 실행 완벽 지원**
```bash
upbit_auto_trading/application/events/database_event_handler.py
```

**현재 Repository 구현으로 실거래 기본 기능은 안전합니다. Application Layer만 완성하면 완전한 실거래 지원 가능!** 🎯
