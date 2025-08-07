# 🔐 API 키 시스템 보안 강화 및 DB 기반 암호화 키 관리 구현 (TDD 방식)

## 배경과 작업 개요

### 🚨 현재 상황
- API 키 시스템의 치명적 보안 취약점 발견
- 암호화 키와 자격증명이 동일 폴더(`config/secure/`)에 저장되어 "원스톱 해킹" 가능
- 백업/클라우드 동기화 시 전체 보안 정보 노출 위험
- 암호화키-자격증명 불일치로 인한 복호화 실패 문제

### 🎯 목표
- DB 기반 하이브리드 아키텍처로 전환하여 보안 강화 (위험도 70% 감소)
- 암호화 키는 `settings.sqlite3`에 저장, 자격증명은 파일로 분리
- 기존 파일 기반 시스템에서 DB 기반으로 완전 마이그레이션
- **엄격한 TDD 방식**: 각 단계마다 테스트 작성 → 구현 → 검증

### 📋 핵심 변경사항
```
현재: config/secure/encryption_key.key + api_credentials.json (위험)
개선: settings.sqlite3/secure_keys + config/secure/api_credentials.json (안전)
```

### 🧪 TDD 테스트 전략
- **환경 변수 API 키 활용**: `.env` 파일의 실제 API 키로 전체 플로우 테스트
- **PyQt 신호 테스트**: UI 버튼 클릭을 신호 발생으로 독립 테스트
- **단위별 독립 검증**: GUI 실행 없이 모든 기능 검증 가능
- **레드-그린-리팩터**: 실패 테스트 → 최소 구현 → 개선

---

## [ ] 1. 📋 스키마 설계 및 DB 기반 테스트 인프라 구축 (TDD Phase 1)

### [ ] 1.1 테스트 먼저: DB 스키마 검증 테스트 작성
- [ ] **RED**: `tests/infrastructure/services/test_secure_keys_schema.py` 생성
  ```python
  def test_secure_keys_table_exists()  # 테이블 존재 검증
  def test_secure_keys_schema_structure()  # 컬럼 구조 검증
  def test_unique_constraint_on_key_type()  # UNIQUE 제약조건 검증
  def test_blob_storage_encryption_key()  # BLOB 타입 키 저장 검증
  ```
- [ ] **테스트 실행**: `pytest tests/infrastructure/services/test_secure_keys_schema.py -v`
- [ ] **예상 결과**: 모든 테스트 FAIL (테이블 미존재)

### [ ] 1.2 최소 구현: 스키마 생성
- [ ] **GREEN**: `data_info/upbit_autotrading_schema_settings.sql`에 테이블 정의 추가
  ```sql
  CREATE TABLE IF NOT EXISTS secure_keys (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      key_type TEXT NOT NULL UNIQUE,
      key_value BLOB NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```
- [ ] **테스트 실행**: 모든 스키마 테스트 PASS 확인

### [ ] 1.3 리팩터: DB 연결 유틸리티 개선
- [ ] **REFACTOR**: DB 연결 헬퍼 함수 최적화
- [ ] 테스트용 임시 DB 생성/삭제 유틸리티 추가
- [ ] **검증**: 테스트 재실행으로 기능 보장

---

## [ ] 2. 🔑 암호화 키 DB 저장/로드 로직 구현 (TDD Phase 2)

### [ ] 2.1 테스트 먼저: 키 저장/로드 기능 테스트 작성
- [ ] **RED**: `tests/infrastructure/services/test_encryption_key_db_operations.py` 생성
  ```python
  def test_save_encryption_key_to_db()  # DB 키 저장 테스트
  def test_load_encryption_key_from_db()  # DB 키 로드 테스트
  def test_key_not_exists_returns_none()  # 키 없을 때 None 반환
  def test_invalid_key_format_raises_error()  # 잘못된 키 형식 에러
  def test_duplicate_key_type_replaces_existing()  # 중복 키 교체
  ```
- [ ] **환경 설정**: 임시 DB 사용하여 격리된 테스트 환경
- [ ] **테스트 실행**: 모든 테스트 FAIL (메서드 미구현)

### [ ] 2.2 최소 구현: DB 기반 키 관리 메서드
- [ ] **GREEN**: `api_key_service.py`에 DB 메서드 구현
  ```python
  def _save_encryption_key_to_db(self, key: bytes) -> bool
  def _load_encryption_key_from_db(self) -> Optional[bytes]
  def _delete_encryption_key_from_db(self) -> bool
  def _create_new_encryption_key_in_db(self) -> bool  # 🔑 파일 없이 바로 DB 생성
  ```
- [ ] **핵심**: 암호화 키는 **파일로 생성되지 않고 바로 DB에 저장**
- [ ] **보안 강화**: 키가 파일 시스템에 노출되지 않음
- [ ] **구현 검증**: 모든 키 관리 테스트 PASS

### [ ] 2.3 리팩터: 에러 처리 및 로깅 강화
- [ ] **REFACTOR**: 상세한 예외 처리 및 로깅 추가
- [ ] DB 트랜잭션 원자성 보장
- [ ] **검증**: 테스트 재실행으로 안정성 확인

---

## [ ] 3. 🔄 마이그레이션 시스템 TDD 구현 (TDD Phase 3) - **단순화 버전**

### [ ] 3.1 테스트 먼저: 기본 마이그레이션 테스트 (간소화)
- [ ] **RED**: `tests/infrastructure/services/test_file_to_db_migration.py` 생성
  ```python
  def test_detect_legacy_file_key()  # 기존 파일 키 감지
  def test_migrate_file_key_to_db_simple()  # 🟡 간소화: 3단계 처리
  def test_skip_migration_if_db_key_exists()  # DB 키 있으면 스킵
  # 🚨 제거: 복잡한 롤백 테스트는 3순위로 이동
  ```
- [ ] **실제 파일 생성**: 테스트용 암호화 키 파일 생성/삭제
- [ ] **테스트 실행**: 기본 테스트 FAIL

### [ ] 3.2 최소 구현: 간소화된 마이그레이션 로직
- [ ] **GREEN**: 3단계 마이그레이션 메서드 구현
  ```python
  def _detect_legacy_encryption_file(self) -> bool
  def _migrate_file_key_to_db_simple(self) -> bool  # � 롤백 없는 기본 처리
  def _read_file_key_safely(self) -> Optional[bytes]  # 🟡 단순 파일 읽기
  ```
- [ ] **핵심 처리**: 파일감지 → DB저장 → 파일삭제 (실패시 수동정리)
- [ ] **로깅 강화**: 마이그레이션 과정을 상세 로깅으로 추적
- [ ] **테스트 실행**: 기본 마이그레이션 테스트 PASS

### [ ] 3.3 리팩터: 기본 상태 추적
- [ ] **REFACTOR**: 마이그레이션 상태 로깅
- [ ] 기본 에러 처리 및 사용자 안내
- [ ] **검증**: 성공 시나리오 위주 테스트

### [ ] 3.4 **고급 기능** (3순위 - 선택적 구현)
- [ ] **고급**: 백업/복구 로직 추가
  ```python
  def _backup_credentials_before_migration(self) -> str
  def _migrate_file_key_to_db_with_rollback(self) -> bool  # 🔴 복잡한 원자성 처리
  def test_migration_rollback_on_failure()  # 🔴 고난이도 롤백 테스트
  ```
- [ ] **고급**: 부분 실패 시 상태 복구 로직

---

## [ ] 4. 🔐 실제 API 키 암호화/복호화 통합 테스트 (TDD Phase 4) - **간소화 버전**

### [ ] 4.1 테스트 먼저: 환경변수 기반 통합 테스트 (핵심만)
- [ ] **RED**: `tests/integration/test_real_api_key_flow.py` 생성
  ```python
  @pytest.mark.skipif(not os.getenv('UPBIT_ACCESS_KEY'), reason="실제 API 키 필요")
  def test_save_real_api_keys_with_db_encryption()  # 🟡 핵심: 실제 키 저장
  def test_load_and_decrypt_real_api_keys()  # 🟡 핵심: 실제 키 로드
  def test_basic_api_connection_test()  # 🟡 간소화: 기본 연결만
  # 🚨 제거: 복잡한 전체 사이클은 수동 검증으로 대체
  ```
- [ ] **환경 변수 활용**: `.env`의 실제 업비트 API 키 사용 (선택적)
- [ ] **Mock 대체**: 실제 API 없어도 암호화/복호화는 테스트 가능

### [ ] 4.2 최소 구현: ApiKeyService 기본 통합
- [ ] **GREEN**: 기존 `save_api_keys()`, `load_api_keys()` 메서드 DB 전환
- [ ] DB 기반 암호화 키 자동 생성/로드 로직 통합
- [ ] **Mock 서비스**: 업비트 API 대신 Mock으로 기본 검증

### [ ] 4.3 리팩터: 기본 최적화
- [ ] **REFACTOR**: 기본 DB 연결 관리
- [ ] 메모리 보안 기본 처리
- [ ] **검증**: Mock 기반 테스트로 안정성 확인

### [ ] 4.4 **고급 기능** (2-3순위 - 선택적 구현)
- [ ] **고급**: 실제 업비트 API 연결 테스트
  ```python
  def test_api_connection_with_decrypted_keys()  # 🔴 실제 API 의존성
  def test_full_cycle_save_load_delete()  # 🔴 복잡한 전체 사이클
  ```
- [ ] **고급**: 성능 테스트 및 고급 최적화
- [ ] **고급**: DB 연결 풀링 및 캐싱

---

## [ ] 5. 🖱️ UI 로직 검증 (TDD Phase 5) - **수동 검증 우선**

### [ ] 5.1 **기본 접근**: 수동 GUI 검증 (권장)
- [ ] **수동 테스트**: `python run_desktop_ui.py` 실행
- [ ] **체크리스트 방식**:
  ```
  □ 저장 버튼 클릭 → API 키 저장 확인
  □ 로드 후 마스킹된 키 표시 확인
  □ 삭제 버튼 → 키 삭제 확인
  □ 에러 시 적절한 메시지 표시 확인
  ```
- [ ] **장점**: 복잡한 PyQt 테스트 코드 불필요
- [ ] **시간 절약**: 고난이도 QTest 구현 회피

### [ ] 5.2 **대안 접근**: 직접 메서드 테스트 (간소화)
- [ ] **간단한 테스트**: `tests/ui/test_api_key_ui_methods.py` 생성
  ```python
  def test_save_method_direct_call()  # 🟡 신호 없이 직접 호출
  def test_load_method_direct_call()  # 🟡 UI 없이 메서드만 테스트
  def test_input_validation_logic()   # 🟡 입력 검증 로직만
  # 🚨 제거: 복잡한 QSignalSpy, QTest 코드
  ```
- [ ] **Mock 활용**: ApiKeyService Mock으로 격리 테스트
- [ ] **핵심만**: UI 로직과 서비스 연결만 검증

### [ ] 5.3 최소 구현: UI-서비스 연결 개선
- [ ] **GREEN**: `api_key_manager_secure.py`의 메서드 직접 테스트
- [ ] 서비스 계층 호출 로직 검증
- [ ] **간단한 테스트**: 메서드 호출 결과만 확인

### [ ] 5.4 **고급 기능** (3순위 - 선택적 구현)
- [ ] **고급**: PyQt 신호 기반 테스트 (전문 지식 필요)
  ```python
  def test_save_button_signal_emission()  # 🔴 QTest + QSignalSpy
  def test_ui_update_after_successful_save()  # 🔴 복잡한 UI 상태 검증
  ```
- [ ] **고급**: 의존성 주입으로 테스트 용이성 향상

---

## [ ] 6. 🔍 보안 강화 효과 검증 (TDD Phase 6) - **핵심만 자동화**

### [ ] 6.1 테스트 먼저: 기본 보안 시나리오만 (간소화)
- [ ] **RED**: `tests/security/test_security_improvement.py` 생성
  ```python
  def test_config_folder_alone_undecryptable()  # 🟡 핵심: config만으로 복호화 불가
  def test_credentials_without_db_useless()  # 🟡 핵심: 자격증명만으로 무의미
  def test_basic_separation_verification()  # 🟡 간소화: 기본 분리 확인
  # 🚨 제거: 복잡한 정량적 측정, 다양한 탈취 시나리오
  ```
- [ ] **간단한 시나리오**: config 폴더 복사 → 복호화 시도 → 실패 확인
- [ ] **핵심 검증**: 파일/DB 분리 효과만 확인

### [ ] 6.2 최소 구현: 기본 보안 검증 도구
- [ ] **GREEN**: 보안 상태 검사 기본 기능
- [ ] 파일/DB 분리 상태 간단 확인
- [ ] **기본 테스트**: 핵심 보안 시나리오만 PASS

### [ ] 6.3 리팩터: 기본 보안 확인
- [ ] **REFACTOR**: 기본 보안 상태 체크
- [ ] 간단한 보안 위험 알림
- [ ] **검증**: 핵심 보안 분리 효과 확인

### [ ] 6.4 **고급 기능** (3순위 - 선택적 구현)
- [ ] **고급**: 정량적 보안 위험도 측정
  ```python
  def test_quantitative_risk_reduction()  # 🔴 복잡한 수치화
  def test_comprehensive_attack_scenarios()  # 🔴 다양한 해킹 시뮬레이션
  def test_partial_file_theft_simulation()  # 🔴 고급 시나리오
  ```
- [ ] **고급**: 실시간 보안 모니터링
- [ ] **고급**: 의심스러운 접근 패턴 탐지

---

## [ ] 7. 🧪 종합 통합 테스트 및 시나리오 검증 (TDD Phase 7)

### [ ] 7.1 5가지 시나리오 자동화 테스트
- [ ] **종합 테스트**: `tests/integration/test_all_scenarios.py` 생성
  ```python
  def test_scenario_1_clean_state()  # 완전 초기 상태
  def test_scenario_2_working_state()  # 정상 작동 상태
  def test_scenario_3_update_state()  # 키 업데이트 상태
  def test_scenario_4_reset_state()  # 초기화 상태
  def test_scenario_5_migration_state()  # 마이그레이션 상태
  ```
- [ ] **환경변수 API 키**: 모든 시나리오에서 실제 키 사용
- [ ] **상태 전환**: 각 시나리오 간 상태 전환 자동화

### [ ] 7.2 성능 및 안정성 검증
- [ ] **성능 테스트**: `tests/performance/test_api_key_performance.py`
  ```python
  def test_db_operation_performance()  # DB 작업 성능
  def test_encryption_decryption_speed()  # 암호화/복호화 속도
  def test_concurrent_access_safety()  # 동시 접근 안전성
  ```
- [ ] **메모리 누수**: 기존 `test_memory_leak.py` 확장

### [ ] 7.3 최종 GUI 통합 검증
- [ ] **GUI 스모크 테스트**: `python run_desktop_ui.py` 자동 실행
- [ ] **API 키 탭 자동 검증**: GUI 자동화 도구 활용
- [ ] **전체 플로우**: 저장→로드→표시→삭제 GUI 시나리오

---

## 📋 TDD 검증 체크리스트 및 파일 구조

### 🧪 테스트 파일 구조 (단순화된 버전)
```
tests/
├── infrastructure/services/
│   ├── test_secure_keys_schema.py           # 스키마 검증
│   ├── test_encryption_key_db_operations.py # DB 키 관리
│   ├── test_file_to_db_migration.py         # 🟡 기본 마이그레이션만
│   └── test_api_key_service_db_integration.py # 서비스 통합
├── integration/
│   ├── test_real_api_key_flow.py             # 🟡 핵심 플로우만
│   └── test_basic_scenarios.py              # 🟡 간소화된 시나리오
├── ui/
│   └── test_api_key_ui_methods.py            # 🟡 직접 메서드 테스트
├── security/
│   └── test_basic_security.py               # 🟡 핵심 보안만
└── performance/  # 🚨 3순위로 이동
    └── test_api_key_performance.py          # 성능 테스트 (선택적)
```

### 🎯 **단계별 구현 우선순위**

#### ✅ **1순위: MVP 핵심** (필수, 낮은-중간 위험)
- [ ] **Phase 1**: 스키마 테스트 100% PASS
- [ ] **Phase 2**: DB 키 관리 기본 테스트 100% PASS
- [ ] **Phase 4-기본**: 환경변수 통합 테스트 PASS

#### ⚠️ **2순위: 핵심 기능** (중요, 중간 위험)
- [ ] **Phase 3-기본**: 간소화된 마이그레이션 테스트 PASS
- [ ] **Phase 5-수동**: UI 수동 검증 완료
- [ ] **Phase 6-기본**: 핵심 보안 검증 PASS

#### 🔴 **3순위: 고급 기능** (선택적, 높은 위험)
- [ ] **Phase 3-고급**: 롤백 로직 구현
- [ ] **Phase 4-고급**: 실제 API 연결 테스트
- [ ] **Phase 5-고급**: PyQt 신호 테스트 구현
- [ ] **Phase 6-고급**: 정량적 보안 측정
- [ ] **Phase 7**: 성능 및 종합 테스트

#### 🔐 보안 검증 성공 기준 (간소화)
- [ ] config 폴더만으로 복호화 불가능 (100% 차단) - **핵심 검증**
- [ ] 자격증명 파일만으로 복호화 불가능 - **기본 검증**
- [ ] DB와 파일의 분리 상태 확인 - **간단한 확인**

#### 🧪 환경변수 API 키 테스트 성공 기준 (선택적)
- [ ] Mock 서비스로 암호화→저장→로드→복호화 체인 성공 - **핵심**
- [ ] 실제 API 키는 선택적 테스트 (`.env` 파일 있을 때만)
- [ ] GUI 실행 없이 핵심 기능 검증 완료 - **기본**

#### 🎯 **간소화된 성공 기준**
- [ ] **1순위 완료**: MVP 핵심 기능 (70% 가치)
- [ ] **2순위 완료**: 핵심 기능 (20% 가치)
- [ ] **3순위 선택**: 고급 기능 (10% 가치)

---

## 🚀 TDD 실행 전략

### 📝 개발 워크플로우
1. **RED**: 실패하는 테스트 작성 (기능 요구사항 명세)
2. **GREEN**: 테스트를 통과하는 최소 코드 작성
3. **REFACTOR**: 코드 품질 개선 (테스트는 계속 통과)
4. **INTEGRATE**: 통합 테스트로 전체 검증
5. **DOCUMENT**: 구현 결과 문서 업데이트

### ⚡ 빠른 피드백 루프 (단순화된 버전)
```bash
# 1순위: MVP 핵심 (안전 구간)
pytest tests/infrastructure/services/test_secure_keys_schema.py -v
pytest tests/infrastructure/services/test_encryption_key_db_operations.py -v

# 2순위: 핵심 기능 (중간 위험)
pytest tests/infrastructure/services/test_file_to_db_migration.py -v
pytest tests/integration/test_real_api_key_flow.py -v

# 3순위: 고급 기능 (선택적)
pytest tests/ -k "api_key" -v --env-file=.env  # 전체 테스트 (선택적)
```

### 🎯 **단순화 핵심 원칙**
1. **복잡한 롤백 로직** → 기본 3단계 처리로 간소화
2. **PyQt 신호 테스트** → 수동 GUI 검증 또는 직접 메서드 테스트
3. **정량적 보안 측정** → 핵심 분리 효과만 확인
4. **실제 API 연결** → Mock 우선, 실제 연결은 선택적

**🎯 핵심**: 70% 가치는 1-2순위로 확보, 나머지는 점진적 확장!

---

## 🧠 LLM 에이전트 구현 난이도 분석 및 완화 전략

### 📊 **전체 구현 난이도: 중상 (7/10)**
**핵심 위험 요소**: 보안 시스템 + DB 트랜잭션 + PyQt 테스트 + 마이그레이션 로직

### 🎯 **Phase별 난이도 및 완화 전략**

#### 🟢 **낮음 (3-4/10)**: Phase 1 (스키마), Phase 7 후반 (GUI 검증)
- **완화**: 기존 패턴 활용, 표준 SQL 사용

#### 🟡 **중간 (5-6/10)**: Phase 2 (DB 키 관리), Phase 4 (API 통합)
- **완화**: 단계별 분리, 환경변수 테스트 간소화

#### 🔴 **높음 (7-8/10)**: Phase 3 (마이그레이션), Phase 5 (PyQt UI), Phase 6 (보안 검증)
- **완화**: 복잡한 부분을 서브태스크로 분할

### ⚡ **구현 순서 최적화 제안**

#### 1순위: **Phase 1 + Phase 2 기본** (안전한 기반 구축)
- 스키마 생성 + 단순 DB 키 저장/로드
- **위험도**: 낮음, **학습 효과**: 높음

#### 2순위: **Phase 4 간소화** (핵심 기능 검증)
- 환경변수 API 키 테스트만 (복잡한 시나리오 제외)
- **위험도**: 중간, **비즈니스 가치**: 높음

#### 3순위: **Phase 3 마이그레이션** (점진적 고도화)
- 기본 파일→DB 이동 (롤백 로직 후순위)
- **위험도**: 높음, **필수성**: 높음

#### 4순위: **Phase 5/6 선택적** (고급 기능)
- PyQt 테스트는 수동 검증으로 대체 가능
- 보안 검증은 핵심만 자동화

### 🛠️ **복잡도 완화 구체적 방법**

#### **마이그레이션 간소화**
```python
# 🔴 복잡한 원본
def _migrate_file_key_to_db_with_rollback(self) -> bool:
    # 백업→읽기→저장→삭제→검증 (5단계 원자성)

# 🟡 간소화된 버전
def _migrate_file_key_to_db_simple(self) -> bool:
    # 읽기→저장→삭제 (3단계, 실패시 수동 복구)
```

#### **PyQt 테스트 간소화**
```python
# 🔴 복잡한 원본
def test_save_signal_with_qtest(self):
    # QSignalSpy + QTest + Mock Service

# 🟡 간소화된 버전
def test_save_method_direct_call(self):
    # 직접 메서드 호출 + 결과 검증
```

### 📋 **단계별 완화된 체크리스트**

- [ ] **Level 1**: Phase 1-2 기본 (필수, 낮은 난이도)
- [ ] **Level 2**: Phase 4 핵심 (필수, 중간 난이도)
- [ ] **Level 3**: Phase 3 기본 (필수, 높은 난이도)
- [ ] **Level 4**: Phase 5-6 선택 (선택, 최고 난이도)

---

## 🎯 **권장 구현 전략: 단계별 위험 관리**

### 📋 **단계별 완화된 체크리스트** (최종 버전)

#### ✅ **Level 1: MVP 핵심** (필수, 낮은-중간 난이도)
- [ ] **Phase 1**: 스키마 생성 및 기본 테스트 ⭐⭐⭐☆☆
- [ ] **Phase 2-A**: DB 키 저장 기본 기능 ⭐⭐⭐⭐☆
- [ ] **Phase 2-B**: DB 키 로드 기본 기능 ⭐⭐⭐⭐☆
- [ ] **Phase 4-A**: Mock 기반 저장/로드 테스트 ⭐⭐⭐⭐☆

#### ⚠️ **Level 2: 핵심 기능** (중요, 중간 난이도)
- [ ] **Phase 3-A**: 기본 마이그레이션 (롤백 없이) ⭐⭐⭐⭐⭐⭐☆
- [ ] **Phase 4-B**: 환경변수 API 키 테스트 (선택적) ⭐⭐⭐⭐⭐☆
- [ ] **Phase 5-A**: UI 수동 검증 ⭐⭐☆☆☆
- [ ] **Phase 6-A**: 핵심 보안 검증 ⭐⭐⭐⭐⭐☆

#### 🔴 **Level 3: 고급 기능** (선택적, 높은 난이도)
- [ ] **Phase 3-B**: 마이그레이션 롤백 로직 ⭐⭐⭐⭐⭐⭐⭐⭐
- [ ] **Phase 4-C**: 실제 업비트 API 연결 ⭐⭐⭐⭐⭐⭐☆
- [ ] **Phase 5-B**: PyQt 신호 테스트 ⭐⭐⭐⭐⭐⭐⭐⭐
- [ ] **Phase 6-B**: 정량적 보안 측정 ⭐⭐⭐⭐⭐⭐⭐☆
- [ ] **Phase 7**: 성능 및 종합 테스트 ⭐⭐⭐⭐⭐⭐☆

### 🎯 **구현 성공 전략**
1. **Level 1 완료** → 핵심 보안 기능 확보 (70% 가치)
2. **Level 2 완료** → 실용적 완성도 확보 (90% 가치)
3. **Level 3 선택** → 시간 여유시 고도화 (100% 가치)

### 🏆 **최종 목표 재정의**
- **최소 성공**: Level 1 완료 (DB 기반 키 관리 + 기본 보안)
- **권장 성공**: Level 1-2 완료 (실용적 완성도)
- **완벽 성공**: Level 1-3 완료 (모든 기능 구현)

**💡 핵심 철학**: 완벽보다는 안정성, 복잡성보다는 단순성!

### [ ] 2.2 키 생성 로직 DB 전환
- [ ] 기존 `_create_new_encryption_key()` 메서드를 `_create_new_encryption_key_in_db()`로 교체
- [ ] `INSERT OR REPLACE` 쿼리로 키 저장 로직 구현
- [ ] 트랜잭션 관리 추가 (키 생성 실패 시 롤백)
- [ ] 검토 파일: `upbit_auto_trading/infrastructure/services/api_key_service.py` (라인 100-130)

### [ ] 2.3 키 삭제 로직 DB 전환
- [ ] `delete_api_keys()` 메서드에 DB 키 삭제 로직 추가
- [ ] `DELETE FROM secure_keys WHERE key_type = 'encryption_key'` 쿼리 구현
- [ ] 파일 삭제 + DB 삭제 원자적 처리 보장
- [ ] 검토 파일: `upbit_auto_trading/infrastructure/services/api_key_service.py` (라인 320-360)

### [ ] 2.4 DB 연결 관리 개선
- [ ] `__init__()` 메서드에 DB 연결 초기화 추가
- [ ] `__del__()` 메서드에 DB 연결 해제 추가
- [ ] 연결 풀링 및 에러 핸들링 강화
- [ ] 검토 파일: `upbit_auto_trading/infrastructure/services/api_key_service.py` (라인 55-65)

---

## [ ] 3. 마이그레이션 시스템 구현

### [ ] 3.1 파일 기반 → DB 기반 자동 마이그레이션
- [ ] `_migrate_file_key_to_db()` 메서드 구현
- [ ] 기존 `config/secure/encryption_key.key` 파일 감지 로직
- [ ] 파일에서 키 읽기 → DB 저장 → 파일 삭제 프로세스
- [ ] 검토 파일: `upbit_auto_trading/infrastructure/services/api_key_service.py` (신규 메서드)

### [ ] 3.2 마이그레이션 안전성 보장
- [ ] 마이그레이션 전 기존 자격증명 백업 생성
- [ ] 마이그레이션 실패 시 롤백 로직 구현
- [ ] 마이그레이션 완료 후 복호화 테스트 실행
- [ ] 검토 파일: `upbit_auto_trading/infrastructure/services/api_key_service.py` (신규 메서드들)

### [ ] 3.3 마이그레이션 테스트 작성
- [ ] `tests/infrastructure/services/test_api_key_migration.py` 테스트 파일 생성
- [ ] 파일 → DB 마이그레이션 테스트
- [ ] 마이그레이션 실패 시나리오 테스트
- [ ] 복호화 호환성 테스트

---

## [ ] 4. ApiKeyService 클래스 완전 리팩토링

### [ ] 4.1 __init__ 메서드 개선
- [ ] DB 연결 초기화 로직 추가
- [ ] 마이그레이션 체크 및 자동 실행
- [ ] 기존 파일 기반 코드 제거
- [ ] 검토 파일: `upbit_auto_trading/infrastructure/services/api_key_service.py` (라인 50-70)

### [ ] 4.2 save_api_keys 메서드 DB 통합
- [ ] DB 기반 키 생성 로직으로 전환
- [ ] 자격증명 저장 전 DB 키 존재 여부 확인
- [ ] 에러 시 DB 트랜잭션 롤백 처리
- [ ] 검토 파일: `upbit_auto_trading/infrastructure/services/api_key_service.py` (라인 155-220)

### [ ] 4.3 load_api_keys 메서드 DB 통합
- [ ] DB에서 키 로드 실패 시 에러 처리 개선
- [ ] 복호화 실패와 키 없음 상황 구분
- [ ] 상세한 로깅 및 디버깅 정보 추가
- [ ] 검토 파일: `upbit_auto_trading/infrastructure/services/api_key_service.py` (라인 225-260)

### [ ] 4.4 has_valid_keys 메서드 로직 개선
- [ ] 파일 존재 여부 + DB 키 존재 여부 모두 확인
- [ ] 실제 복호화 테스트까지 포함한 유효성 검증
- [ ] 검토 파일: `upbit_auto_trading/infrastructure/services/api_key_service.py` (라인 360-375)

---

## [ ] 5. UI 계층 통합 및 에러 처리 개선

### [ ] 5.1 API 키 UI 에러 메시지 개선
- [ ] `upbit_auto_trading/ui/desktop/screens/settings/api_key_manager_secure.py`에서 에러 분류 개선
- [ ] "파일 없음" vs "복호화 실패" 구분하여 사용자에게 명확한 메시지 제공
- [ ] DB 연결 실패 시 별도 안내 메시지
- [ ] 검토 파일: `upbit_auto_trading/ui/desktop/screens/settings/api_key_manager_secure.py` (라인 200-250)

### [ ] 5.2 MainWindow API 상태 체크 개선
- [ ] `upbit_auto_trading/ui/desktop/main_window.py`의 `_check_initial_api_status()` 메서드 개선
- [ ] DB 기반 키 시스템과 호환되도록 상태 체크 로직 수정
- [ ] 마이그레이션 상태 감지 및 사용자 안내
- [ ] 검토 파일: `upbit_auto_trading/ui/desktop/main_window.py` (라인 380-420)

### [ ] 5.3 설정 화면 상태 표시 개선
- [ ] API 키 저장 상태를 명확히 표시 (DB 기반, 파일 기반 구분)
- [ ] 마이그레이션 진행 상황 표시
- [ ] 보안 강화 상태 시각적 피드백
- [ ] 검토 파일: `upbit_auto_trading/ui/desktop/screens/settings/api_key_manager_secure.py` (라인 100-150)

---

## [ ] 6. 테스트 시나리오 구현 및 검증

### [ ] 6.1 5가지 시나리오 테스트 구현
- [ ] **Clean State**: 완전 초기 상태 테스트
- [ ] **Working State**: 정상 작동 상태 테스트
- [ ] **Update State**: 키 업데이트 상태 테스트
- [ ] **Reset State**: 초기화 상태 테스트
- [ ] **Migration State**: 파일→DB 마이그레이션 테스트
- [ ] 검토 파일: `tests/infrastructure/services/test_api_key_scenarios.py` (신규 생성)

### [ ] 6.2 보안 강화 효과 검증 테스트
- [ ] 백업 파일 유출 시뮬레이션 테스트 (config 폴더만 복사)
- [ ] 부분 접근 시뮬레이션 테스트 (DB 없이 자격증명만 획득)
- [ ] 복호화 실패 시나리오 테스트
- [ ] 검토 파일: `tests/infrastructure/services/test_api_key_security.py` (신규 생성)

### [ ] 6.3 통합 테스트 구현
- [ ] 전체 API 키 설정 플로우 테스트 (저장→로드→표시→삭제)
- [ ] UI와 서비스 계층 통합 테스트
- [ ] 실제 GUI 시나리오 테스트 (`python run_desktop_ui.py`)
- [ ] 검토 파일: `tests/integration/test_api_key_integration.py` (신규 생성)

---

## [ ] 7. 문서 업데이트 및 마무리

### [ ] 7.1 기존 문서 업데이트
- [ ] `docs/API_KEY_SYSTEM_STATUS_REPORT_20250806.md` 구현 완료 상태로 업데이트
- [ ] `docs/API_KEY_SECURITY_IMPROVEMENT_PROPOSAL_20250807.md` 구현 결과 반영
- [ ] 새로운 DB 기반 아키텍처 문서화

### [ ] 7.2 코드 문서 개선
- [ ] `api_key_service.py`에 DB 기반 로직 상세 주석 추가
- [ ] 마이그레이션 로직 동작 방식 문서화
- [ ] 보안 강화 효과 주석으로 설명

### [ ] 7.3 사용자 가이드 작성
- [ ] 기존 파일 기반 사용자를 위한 마이그레이션 안내
- [ ] 새로운 보안 아키텍처 설명
- [ ] 문제 해결 가이드 (복호화 실패, DB 오류 등)

---

## [ ] 8. 최종 검증 및 배포 준비

### [ ] 8.1 전체 시스템 통합 테스트
- [ ] `python run_desktop_ui.py` 실행하여 GUI 정상 동작 확인
- [ ] API 키 설정 → 저장 → 삭제 → 재설정 전체 사이클 테스트
- [ ] 기존 사용자 데이터 마이그레이션 시나리오 테스트

### [ ] 8.2 성능 및 안정성 테스트
- [ ] DB 연결 부하 테스트
- [ ] 대용량 키 데이터 처리 테스트
- [ ] 메모리 누수 테스트 (기존 `test_memory_leak.py` 활용)

### [ ] 8.3 보안 강화 효과 검증
- [ ] 백업 시나리오에서 보안 개선 확인
- [ ] 파일 탈취 시나리오에서 복호화 불가 확인
- [ ] 전체 보안 위험도 감소 효과 측정

---

## 📋 핵심 파일 체크리스트

### 🔧 수정 필요 파일
- `upbit_auto_trading/infrastructure/services/api_key_service.py` (핵심 로직 90% 변경)
- `data_info/upbit_autotrading_schema_settings.sql` (스키마 추가)
- `upbit_auto_trading/ui/desktop/screens/settings/api_key_manager_secure.py` (에러 처리 개선)
- `upbit_auto_trading/ui/desktop/main_window.py` (상태 체크 개선)

### 🆕 신규 생성 파일
- `tests/infrastructure/services/test_api_key_service_db.py`
- `tests/infrastructure/services/test_api_key_migration.py`
- `tests/infrastructure/services/test_api_key_scenarios.py`
- `tests/infrastructure/services/test_api_key_security.py`
- `tests/integration/test_api_key_integration.py`

### 📚 문서 업데이트
- `docs/API_KEY_SYSTEM_STATUS_REPORT_20250806.md`
- `docs/API_KEY_SECURITY_IMPROVEMENT_PROPOSAL_20250807.md`

---

## 🎯 성공 기준

### ✅ 기능적 성공 기준
- [ ] 암호화 키가 `settings.sqlite3`에 안전하게 저장됨
- [ ] 자격증명 파일만으로는 복호화 불가능함
- [ ] 기존 파일 기반 사용자 데이터가 자동 마이그레이션됨
- [ ] API 키 설정/로드/삭제 전체 사이클이 안정적으로 동작함

### 🔐 보안 성공 기준
- [ ] config 폴더 백업 시 암호화 키가 포함되지 않음
- [ ] 자격증명 파일 탈취만으로는 복호화 불가능함
- [ ] 전체 보안 위험도가 70% 이상 감소함

### 🧪 테스트 성공 기준
- [ ] 모든 신규 테스트가 통과함
- [ ] 기존 API 키 관련 테스트가 여전히 통과함
- [ ] `python run_desktop_ui.py` 실행 시 에러 없이 동작함
