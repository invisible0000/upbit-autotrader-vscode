# 🔐 API 키 시스템 보안 강화 TDD 구현 계획 (v2.0)
## 난이도 분석 기반 단계별 구현 전략

**작성일**: 2025년 8월 7일
**기반 문서**:
- `API_KEY_SYSTEM_STATUS_REPORT_20250806.md`
- `API_KEY_SECURITY_IMPROVEMENT_PROPOSAL_20250807.md`
- `LLM_AGENT_IMPLEMENTATION_DIFFICULTY_ANALYSIS_REPORT.md`

---

## 📋 프로젝트 개요

### 🚨 현재 문제점
```
현재: config/secure/encryption_key.key + api_credentials.json
위험: 두 파일 획득 시 즉시 복호화 가능 → "원스톱 해킹"
```

### 🎯 목표 아키텍처
```
개선: settings.sqlite3/secure_keys + config/secure/api_credentials.json
효과: 키-자격증명 분리로 보안 위험도 70% 감소
```

### 🧪 구현 전략
- **단계별 위험 관리**: 낮은 난이도부터 점진적 구현
- **TDD 방식**: 각 단계마다 테스트 먼저 → 구현 → 검증
- **3단계 우선순위**: Level 1(필수) → Level 2(중요) → Level 3(선택)

---

## 🎯 Level 1: MVP 핵심 구현 (필수, 낮은-중간 난이도)

### 📋 **Task 1.1**: DB 스키마 설계 및 생성
**난이도**: ⭐⭐⭐☆☆ (3/10) | **우선순위**: 최고

#### 1.1.1 스키마 테스트 작성
- [ ] **파일 생성**: `tests/infrastructure/services/test_secure_keys_schema.py`
- [ ] **테스트 함수**:
  ```python
  def test_secure_keys_table_exists()      # 테이블 존재 검증
  def test_secure_keys_schema_structure()  # 컬럼 구조 검증
  def test_unique_constraint_on_key_type() # UNIQUE 제약조건 검증
  def test_blob_storage_encryption_key()   # BLOB 타입 키 저장 검증
  ```
- [ ] **예상 결과**: 모든 테스트 FAIL (테이블 미존재)

#### 1.1.2 스키마 구현
- [ ] **파일 수정**: `data_info/upbit_autotrading_schema_settings.sql`
- [ ] **스키마 추가**:
  ```sql
  CREATE TABLE IF NOT EXISTS secure_keys (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      key_type TEXT NOT NULL UNIQUE,
      key_value BLOB NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  CREATE UNIQUE INDEX IF NOT EXISTS idx_secure_keys_type
  ON secure_keys(key_type);
  ```
- [ ] **검증**: 모든 스키마 테스트 PASS

#### 1.1.3 DB 연결 헬퍼 개선
- [ ] **기능**: 테스트용 임시 DB 생성/삭제 유틸리티
- [ ] **목적**: 격리된 테스트 환경 제공

---

### 🔑 **Task 1.2**: DB 기반 암호화 키 저장/로드 (기본)
**난이도**: ⭐⭐⭐⭐☆ (4/10) | **우선순위**: 최고

#### 1.2.1 키 관리 테스트 작성
- [ ] **파일 생성**: `tests/infrastructure/services/test_encryption_key_db_operations.py`
- [ ] **테스트 함수**:
  ```python
  def test_save_encryption_key_to_db()        # DB 키 저장 테스트
  def test_load_encryption_key_from_db()      # DB 키 로드 테스트
  def test_key_not_exists_returns_none()      # 키 없을 때 None 반환
  def test_duplicate_key_type_replaces()      # 중복 키 교체 테스트
  ```
- [ ] **환경**: 임시 DB 사용하여 격리된 테스트

#### 1.2.2 DB 키 관리 메서드 구현
- [ ] **파일 수정**: `upbit_auto_trading/infrastructure/services/api_key_service.py`
- [ ] **핵심 메서드**:
  ```python
  def _get_settings_db_connection(self) -> sqlite3.Connection
  def _save_encryption_key_to_db(self, key: bytes) -> bool
  def _load_encryption_key_from_db(self) -> Optional[bytes]
  def _delete_encryption_key_from_db(self) -> bool
  ```
- [ ] **보안 강화**: 키가 파일 시스템에 노출되지 않음

#### 1.2.3 키 생성 로직 DB 전환
- [ ] **기능**: 새 키 생성 시 바로 DB 저장 (파일 우회)
- [ ] **메서드**: `_create_new_encryption_key_in_db()`
- [ ] **트랜잭션**: DB 원자성 보장

---

### 🔧 **Task 1.3**: ApiKeyService DB 통합 (기본)
**난이도**: ⭐⭐⭐⭐⭐ (5/10) | **우선순위**: 최고

#### 1.3.1 서비스 통합 테스트 작성
- [ ] **파일 생성**: `tests/infrastructure/services/test_api_key_service_db_integration.py`
- [ ] **테스트 함수**:
  ```python
  def test_service_init_with_db_connection()   # DB 연결 초기화
  def test_save_api_keys_creates_db_key()      # 저장 시 DB 키 생성
  def test_load_api_keys_uses_db_key()         # 로드 시 DB 키 사용
  def test_delete_removes_both_file_and_db()   # 삭제 시 파일+DB 정리
  ```

#### 1.3.2 ApiKeyService 클래스 수정
- [ ] **__init__ 메서드**: DB 연결 초기화 추가
- [ ] **save_api_keys 메서드**: DB 키 생성/사용으로 전환
- [ ] **load_api_keys 메서드**: DB에서 키 로드하도록 수정
- [ ] **delete_api_keys 메서드**: DB 키도 함께 삭제

#### 1.3.3 기본 에러 처리
- [ ] **DB 연결 실패**: 명확한 에러 메시지
- [ ] **키 없음 vs 복호화 실패**: 상황별 구분
- [ ] **로깅 강화**: Infrastructure 로깅 시스템 활용

---

## ⚠️ Level 2: 핵심 기능 구현 (중요, 중간 난이도)

### 🔄 **Task 2.1**: 기본 마이그레이션 시스템 (간소화)
**난이도**: ⭐⭐⭐⭐⭐⭐ (6/10) | **우선순위**: 높음

#### 2.1.1 기본 마이그레이션 테스트 작성
- [ ] **파일 생성**: `tests/infrastructure/services/test_file_to_db_migration.py`
- [ ] **테스트 함수** (간소화된 버전):
  ```python
  def test_detect_legacy_file_key()           # 기존 파일 키 감지
  def test_migrate_file_key_to_db_simple()    # 3단계 기본 마이그레이션
  def test_skip_migration_if_db_key_exists()  # DB 키 있으면 스킵
  ```
- [ ] **제외**: 복잡한 롤백 테스트 (Level 3으로 이동)

#### 2.1.2 간소화된 마이그레이션 로직 구현
- [ ] **3단계 처리**: 파일감지 → DB저장 → 파일삭제
- [ ] **메서드**:
  ```python
  def _detect_legacy_encryption_file(self) -> bool
  def _migrate_file_key_to_db_simple(self) -> bool
  def _read_file_key_safely(self) -> Optional[bytes]
  ```
- [ ] **실패 처리**: 수동 정리 (자동 롤백 제외)

#### 2.1.3 마이그레이션 상태 추적
- [ ] **로깅**: 마이그레이션 과정 상세 기록
- [ ] **사용자 안내**: 마이그레이션 진행 상황 표시
- [ ] **성공 시나리오**: 정상 케이스 위주 검증

---

### 🔐 **Task 2.2**: Mock 기반 통합 테스트 (핵심만)
**난이도**: ⭐⭐⭐⭐⭐ (5/10) | **우선순위**: 높음

#### 2.2.1 Mock 기반 통합 테스트 작성
- [ ] **파일 생성**: `tests/integration/test_api_key_flow_mock.py`
- [ ] **테스트 함수**:
  ```python
  def test_save_keys_with_db_encryption_mock()  # Mock API로 저장 테스트
  def test_load_and_decrypt_keys_mock()         # Mock API로 로드 테스트
  def test_full_cycle_mock()                    # 전체 사이클 Mock 테스트
  ```
- [ ] **장점**: 실제 API 의존성 없이 핵심 로직 검증

#### 2.2.2 환경변수 기반 선택적 테스트
- [ ] **파일 생성**: `tests/integration/test_real_api_key_flow.py` (선택적)
- [ ] **조건부 실행**:
  ```python
  @pytest.mark.skipif(not os.getenv('UPBIT_ACCESS_KEY'), reason="실제 API 키 필요")
  ```
- [ ] **목적**: 실제 환경에서 추가 검증 (선택적)

---

### 🖱️ **Task 2.3**: UI 검증 (수동 우선)
**난이도**: ⭐⭐☆☆☆ (2/10) | **우선순위**: 중간

#### 2.3.1 수동 GUI 검증 (권장 방법)
- [ ] **실행**: `python run_desktop_ui.py`
- [ ] **체크리스트**:
  ```
  □ API 키 설정 탭 정상 표시
  □ 저장 버튼 클릭 → 키 저장 성공 메시지
  □ 로드 후 마스킹된 키 표시 확인
  □ 삭제 버튼 → 키 삭제 확인
  □ 에러 시 적절한 메시지 표시
  ```
- [ ] **장점**: 복잡한 PyQt 테스트 코드 불필요

#### 2.3.2 간단한 메서드 테스트 (대안)
- [ ] **파일 생성**: `tests/ui/test_api_key_ui_methods.py` (선택적)
- [ ] **직접 호출**: UI 신호 없이 메서드만 테스트
- [ ] **Mock 서비스**: ApiKeyService Mock으로 격리

---

### 🔍 **Task 2.4**: 기본 보안 검증
**난이도**: ⭐⭐⭐⭐☆ (4/10) | **우선순위**: 중간

#### 2.4.1 핵심 보안 시나리오 테스트
- [ ] **파일 생성**: `tests/security/test_basic_security.py`
- [ ] **테스트 함수**:
  ```python
  def test_config_folder_alone_undecryptable()  # config만으로 복호화 불가
  def test_credentials_without_db_useless()     # 자격증명만으로 무의미
  def test_basic_separation_verification()      # 기본 분리 효과 확인
  ```

#### 2.4.2 간단한 보안 검증 구현
- [ ] **시나리오**: config 폴더 복사 → 복호화 시도 → 실패 확인
- [ ] **검증**: 파일/DB 분리 상태 확인
- [ ] **제외**: 복잡한 정량적 측정 (Level 3으로 이동)

---

## 🔴 Level 3: 고급 기능 구현 (선택적, 높은 난이도)

### 🛡️ **Task 3.1**: 고급 마이그레이션 (롤백 포함)
**난이도**: ⭐⭐⭐⭐⭐⭐⭐⭐ (8/10) | **우선순위**: 낮음 (선택)

#### 3.1.1 롤백 로직 구현 (고급)
- [ ] **백업/복구**: 마이그레이션 전 자격증명 백업
- [ ] **원자성**: 5단계 원자적 처리 (백업→읽기→저장→검증→삭제)
- [ ] **실패 처리**: 롤백 로직 구현

#### 3.1.2 복잡한 마이그레이션 테스트
- [ ] **테스트 추가**: `test_migration_rollback_on_failure()`
- [ ] **시나리오**: 부분 실패 상황 재현 및 복구

---

### 🌐 **Task 3.2**: 실제 API 연결 테스트 (고급)
**난이도**: ⭐⭐⭐⭐⭐⭐ (6/10) | **우선순위**: 낮음 (선택)

#### 3.2.1 실제 업비트 API 테스트
- [ ] **전제 조건**: `.env` 파일에 실제 API 키 필요
- [ ] **테스트**: 복호화된 키로 실제 API 연결
- [ ] **네트워크 의존성**: 외부 API 상태에 따라 결과 변동

---

### 🖱️ **Task 3.3**: PyQt 신호 기반 UI 테스트 (고급)
**난이도**: ⭐⭐⭐⭐⭐⭐⭐⭐ (8/10) | **우선순위**: 낮음 (선택)

#### 3.3.1 복잡한 PyQt 테스트
- [ ] **전문 지식**: QTest, QSignalSpy 숙련 필요
- [ ] **비동기 처리**: 신호 발생 → 처리 완료 대기
- [ ] **Mock 통합**: UI + 서비스 Mock 조합

---

### 📊 **Task 3.4**: 정량적 보안 측정 (고급)
**난이도**: ⭐⭐⭐⭐⭐⭐⭐ (7/10) | **우선순위**: 낮음 (선택)

#### 3.4.1 고급 보안 분석
- [ ] **다양한 시나리오**: 12가지 탈취 상황 시뮬레이션
- [ ] **수치화**: 보안 위험도 감소 효과 정량 측정
- [ ] **보안 전문성**: 해킹 시나리오 구현 지식 필요

---

## 📊 구현 우선순위 요약

### ✅ **즉시 시작** (Level 1 - MVP)
1. **Task 1.1**: DB 스키마 (난이도 3/10)
2. **Task 1.2**: DB 키 관리 (난이도 4/10)
3. **Task 1.3**: 서비스 통합 (난이도 5/10)

### ⚠️ **다음 단계** (Level 2 - 핵심)
4. **Task 2.1**: 기본 마이그레이션 (난이도 6/10)
5. **Task 2.2**: Mock 통합 테스트 (난이도 5/10)
6. **Task 2.3**: UI 수동 검증 (난이도 2/10)
7. **Task 2.4**: 기본 보안 검증 (난이도 4/10)

### 🔴 **선택적 고도화** (Level 3 - 고급)
8. **Task 3.1**: 고급 마이그레이션 (난이도 8/10) - 선택
9. **Task 3.2**: 실제 API 테스트 (난이도 6/10) - 선택
10. **Task 3.3**: PyQt UI 테스트 (난이도 8/10) - 선택
11. **Task 3.4**: 정량적 보안 (난이도 7/10) - 선택

---

## 🎯 성공 기준

### ✅ **최소 성공**: Level 1 완료
- DB 기반 키 관리 시스템 구축
- 기본 보안 분리 효과 확보
- **가치**: 전체의 70%

### 🎯 **권장 성공**: Level 1-2 완료
- 실용적 완성도 확보
- 기존 사용자 마이그레이션 지원
- **가치**: 전체의 90%

### 🏆 **완벽 성공**: Level 1-3 완료
- 모든 고급 기능 포함
- 완전한 보안 강화 달성
- **가치**: 전체의 100%

---

## 🚀 실행 명령어

### 단계별 테스트 실행
```bash
# Level 1: MVP 핵심
pytest tests/infrastructure/services/test_secure_keys_schema.py -v
pytest tests/infrastructure/services/test_encryption_key_db_operations.py -v
pytest tests/infrastructure/services/test_api_key_service_db_integration.py -v

# Level 2: 핵심 기능
pytest tests/infrastructure/services/test_file_to_db_migration.py -v
pytest tests/integration/test_api_key_flow_mock.py -v
pytest tests/security/test_basic_security.py -v

# Level 3: 고급 기능 (선택적)
pytest tests/integration/test_real_api_key_flow.py -v  # 실제 API 키 필요
pytest tests/ui/test_api_key_ui_signals.py -v         # PyQt 전문 지식 필요
```

### 최종 검증
```bash
# GUI 수동 검증
python run_desktop_ui.py

# 전체 API 키 관련 테스트
pytest tests/ -k "api_key" -v
```

---

## 💡 핵심 원칙

1. **단순함이 복잡함을 이긴다**: 완벽보다는 안정성 우선
2. **점진적 발전**: Level 1부터 차근차근 구축
3. **위험 관리**: 고난이도 작업은 선택적으로 처리
4. **실용성 우선**: 70% 가치로 90% 만족도 달성

**🎯 최종 목표**: 안전하고 실용적인 DB 기반 API 키 보안 시스템 구축!
