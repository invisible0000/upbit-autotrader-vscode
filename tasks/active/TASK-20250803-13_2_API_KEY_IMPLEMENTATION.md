# 🔐 API 키 시스템 보안 강화 TDD 구현 계획 (v3.0)
## 하이브리드 통합 시스템: 사용자 책임 모델 + API 모니터링

**작성일**: 2025년 8월 7일
**최종 업데이트**: 2025년 8월 7일 10:40
**기반 문서**:
- `TASK_API_KEY_DB_SECURITY_IMPLEMENTATION_V2.md`
- `FINAL_COMPREHENSIVE_DISCUSSION_SUMMARY_20250807.md`
- 사용자 책임 모델 최종 승인

**v3.0 주요 개선사항**:
- ✅ 백업 기반 롤백 시스템 추가
- ✅ 전제 조건 및 구현 파일 경로 명확화
- ✅ Level 1, 2 완료 체크포인트 시스템
- ✅ 테스트 데이터 관리 및 코딩 스타일 가이드
- ✅ Task 의존성 그래프 및 기존 코드 통합 지점 명시
- ✅ 에러 시나리오 구체화 및 성공 기준 명확화

---

## 📋 하이브리드 시스템 개요

### 🚨 현재 문제점
```
현재: config/secure/encryption_key.key + api_credentials.json
위험: 두 파일 획득 시 즉시 복호화 가능 → "원스톱 해킹"
```

### 🎯 하이브리드 목표 아키텍처
```
✅ API 키 보안: settings.sqlite3/secure_keys + config/secure/api_credentials.json
✅ API 모니터링: 실패 카운터 방식 (3회 연속 실패 감지)
✅ 상태바 UI: PyQt6 클릭 가능 레이블 (10초 쿨다운)
효과: 보안 위험도 70% 감소 + 실시간 API 상태 모니터링
```

### 🧪 구현 전략 (세분화된 TDD)
- **초세분화 단계별 구현**: 복잡한 테스트를 작은 단위로 분산
- **사용자 책임 모델**: 단순화된 에러 처리 및 재생성 로직
- **차근차근 접근**: 한 번에 많은 기능 구현하지 않고 점진적 확장
- **3+1 우선순위**: Level 1(필수) → Level 2(핵심) → Level 3(선택) + API 모니터링
- **백업 기반 롤백**: Git 커밋 대신 날짜시간 백업 폴더로 안전한 롤백

### 🔄 **백업 및 롤백 시스템**

#### 작업 시작 전 백업 생성
```powershell
# 백업 폴더 생성 (예: backups/api_key_security_20250807_143022/)
$backupDir = "backups/api_key_security_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force

# 핵심 파일들 백업
Copy-Item "upbit_auto_trading/infrastructure/services/api_key_service.py" "$backupDir/" -Force
Copy-Item "data_info/upbit_autotrading_schema_settings.sql" "$backupDir/" -Force
Copy-Item "tests/infrastructure/services/" "$backupDir/tests_backup/" -Recurse -Force
```

#### 롤백 실행 (문제 발생 시)
```powershell
# 최신 백업 폴더 찾기
$latestBackup = Get-ChildItem "backups/api_key_security_*" | Sort-Object Name -Descending | Select-Object -First 1

# 파일 복원
Copy-Item "$latestBackup/api_key_service.py" "upbit_auto_trading/infrastructure/services/" -Force
Copy-Item "$latestBackup/upbit_autotrading_schema_settings.sql" "data_info/" -Force
Copy-Item "$latestBackup/tests_backup/*" "tests/infrastructure/services/" -Recurse -Force

Write-Host "🔄 롤백 완료: $($latestBackup.Name)"
```

---

## 🎯 Level 1: MVP 핵심 구현 (필수, 낮은-중간 난이도)

### 📋 **Task 1.1**: DB 스키마 설계 및 생성 (초세분화)
**난이도**: ⭐⭐⭐☆☆ (3/10) | **우선순위**: 최고

#### 전제 조건
- [ ] `data/settings.sqlite3` DB 파일 존재 확인
- [ ] `config/simple_paths.py`의 `get_settings_db_path()` 함수 사용 가능
- [ ] `upbit_auto_trading/infrastructure/logging` 시스템 동작 확인

#### 1.1.1 스키마 테스트 작성 (단일 테스트)
- [ ] **파일 생성**: `tests/infrastructure/services/test_secure_keys_schema_basic.py`
- [ ] **테스트 함수** (하나씩 차근차근):
  ```python
  def test_secure_keys_table_exists()      # 1단계: 테이블 존재만 검증
  ```
- [ ] **실행**: `pytest tests/infrastructure/services/test_secure_keys_schema_basic.py::test_secure_keys_table_exists -v`
- [ ] **예상 결과**: FAIL (테이블 미존재)

#### 1.1.2 기본 스키마 구현
- [ ] **구현 대상**: `data_info/upbit_autotrading_schema_settings.sql`
- [ ] **백업 생성**: 작업 전 현재 스키마 파일 백업
- [ ] **최소 스키마**:
  ```sql
  CREATE TABLE IF NOT EXISTS secure_keys (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      key_type TEXT NOT NULL,
      key_value BLOB NOT NULL
  );
  ```
- [ ] **검증**: `test_secure_keys_table_exists` PASS
- [ ] **성공 기준**: SQL 쿼리 `SELECT name FROM sqlite_master WHERE type='table' AND name='secure_keys'` 결과 존재

#### 1.1.3 스키마 구조 테스트 추가 (점진적 확장)
- [ ] **테스트 추가** (같은 파일에):
  ```python
  def test_secure_keys_schema_structure()  # 2단계: 컬럼 구조 검증
  def test_blob_storage_encryption_key()   # 3단계: BLOB 타입 키 저장 검증
  ```
- [ ] **실행**: 구조 테스트들 하나씩 PASS 확인

#### 1.1.4 UNIQUE 제약조건 추가 (마지막 단계)
- [ ] **스키마 개선**:
  ```sql
  ALTER TABLE secure_keys ADD CONSTRAINT unique_key_type UNIQUE(key_type);
  CREATE UNIQUE INDEX IF NOT EXISTS idx_secure_keys_type ON secure_keys(key_type);
  ```
- [ ] **테스트 추가**: `def test_unique_constraint_on_key_type()`
- [ ] **검증**: 모든 스키마 테스트 PASS

#### 1.1.5 DB 연결 헬퍼 구현 (지원 기능)
- [ ] **파일 생성**: `tests/infrastructure/services/test_db_helper.py`
- [ ] **기능**: 테스트용 임시 DB 생성/삭제 유틸리티
- [ ] **목적**: 격리된 테스트 환경 제공

---

### 🔑 **Task 1.2**: DB 기반 암호화 키 저장 (초세분화)
**난이도**: ⭐⭐⭐⭐☆ (4/10) | **우선순위**: 최고

#### 전제 조건
- [ ] Task 1.1 완료 (secure_keys 테이블 존재)
- [ ] `upbit_auto_trading/infrastructure/services/api_key_service.py` 기본 구조 존재
- [ ] `sqlite3` 모듈 import 가능

#### 예상 에러 시나리오 및 대응
- `sqlite3.OperationalError: database is locked` → 명확한 에러 메시지 "데이터베이스가 사용 중입니다. 잠시 후 다시 시도해주세요."
- `sqlite3.IntegrityError: UNIQUE constraint failed` → "이미 존재하는 키 타입입니다. 기존 키를 삭제 후 재시도하세요."
- `PermissionError` → "데이터베이스 파일 접근 권한이 없습니다. 관리자 권한으로 실행하세요."

#### 1.2.1 DB 연결 테스트 (첫 번째 단계)
- [ ] **파일 생성**: `tests/infrastructure/services/test_db_connection.py`
- [ ] **테스트 함수**:
  ```python
  def test_get_settings_db_connection()    # DB 연결만 테스트
  def test_db_connection_error_handling()  # DB 연결 실패 처리
  ```
- [ ] **구현**: `_get_settings_db_connection()` 메서드만

#### 1.2.2 키 저장 테스트 (두 번째 단계)
- [ ] **파일 생성**: `tests/infrastructure/services/test_save_encryption_key.py`
- [ ] **구현 대상**: `upbit_auto_trading/infrastructure/services/api_key_service.py`
- [ ] **구현 메서드**: `_save_encryption_key_to_db(self, key_data: bytes) -> bool`
- [ ] **테스트 함수**:
  ```python
  def test_save_encryption_key_to_db_basic()   # 기본 저장 테스트
  def test_save_key_with_invalid_data()        # 잘못된 데이터 저장
  ```
- [ ] **성공 기준**: 저장 후 DB에서 `SELECT count(*) FROM secure_keys WHERE key_type='encryption'` 결과가 1

#### 1.2.3 키 로드 테스트 (세 번째 단계)
- [ ] **파일 생성**: `tests/infrastructure/services/test_load_encryption_key.py`
- [ ] **테스트 함수**:
  ```python
  def test_load_encryption_key_from_db_basic() # 기본 로드 테스트
  def test_key_not_exists_returns_none()       # 키 없을 때 None 반환
  ```
- [ ] **구현**: `_load_encryption_key_from_db()` 메서드만

#### 1.2.4 키 교체 테스트 (네 번째 단계)
- [ ] **파일 추가**: `test_load_encryption_key.py`에 추가
- [ ] **테스트 함수**:
  ```python
  def test_duplicate_key_type_replaces()       # 중복 키 교체 테스트
  ```
- [ ] **보완**: INSERT OR REPLACE 로직 개선

#### 1.2.5 키 삭제 테스트 (다섯 번째 단계)
- [ ] **파일 생성**: `tests/infrastructure/services/test_delete_encryption_key.py`
- [ ] **테스트 함수**:
  ```python
  def test_delete_encryption_key_from_db()    # DB 키 삭제 테스트
  def test_delete_nonexistent_key()           # 없는 키 삭제 시도
  ```
- [ ] **구현**: `_delete_encryption_key_from_db()` 메서드

---

### 🗑️ **Task 1.3**: 상황별 스마트 삭제 로직 (사용자 책임 모델)
**난이도**: ⭐⭐⭐☆☆ (3/10) | **우선순위**: 최고

#### 1.3.1 삭제 상태 감지 테스트
- [ ] **파일 생성**: `tests/infrastructure/services/test_smart_deletion.py`
- [ ] **테스트 함수**:
  ```python
  def test_detect_deletion_scenarios()        # 4가지 삭제 상황 감지
  def test_deletion_status_messages()         # 상황별 메시지 검증
  ```

#### 1.3.2 스마트 삭제 메서드 구현
- [ ] **메서드 구현**:
  ```python
  def delete_api_keys_smart(self):
      """상황별 명확한 삭제 로직"""
      deletion_message, deletion_details = self._get_deletion_message()

      if deletion_message == "삭제할 인증 정보가 없습니다.":
          return deletion_message

      # 사용자 확인 후 삭제 실행
      if self.confirm_deletion(deletion_message, deletion_details):
          return self._execute_deletion()
      else:
          return "삭제가 취소되었습니다."

  def _get_deletion_message(self):
      """삭제 상황별 메시지 생성 (재사용 가능)"""
      has_db_key = self._encryption_key_exists_in_db()
      has_credentials_file = self._credentials_file_exists()

      if has_db_key and has_credentials_file:
          message = "암호화 키(DB)와 자격증명 파일을 모두 삭제하시겠습니까?"
          details = "삭제 후에는 API 키를 다시 입력해야 합니다."
      elif has_db_key and not has_credentials_file:
          message = "암호화 키(DB)만 존재합니다. 삭제하시겠습니까?"
          details = "자격증명 파일은 이미 없는 상태입니다."
      elif not has_db_key and has_credentials_file:
          message = "자격증명 파일만 존재합니다. 삭제하시겠습니까?"
          details = "암호화 키는 이미 없는 상태입니다."
      else:
          message = "삭제할 인증 정보가 없습니다."
          details = ""

      return message, details

  def _execute_deletion(self):
      """실제 삭제 실행"""
      has_db_key = self._encryption_key_exists_in_db()
      has_credentials_file = self._credentials_file_exists()

      deleted_items = []
      if has_db_key:
          self._delete_encryption_key_from_db()
          deleted_items.append("암호화 키(DB)")
      if has_credentials_file:
          self._delete_credentials_file()
          deleted_items.append("자격증명 파일")

      return f"삭제 완료: {', '.join(deleted_items)}"
  ```

#### 1.3.3 삭제 확인 UI 테스트 (선택적)
- [ ] **테스트 추가**:
  ```python
  def test_deletion_confirmation_dialog()     # 삭제 확인 대화상자
  ```

---

### 🔄 **Task 1.4**: 깔끔한 재생성 로직 (사용자 책임 모델 + 코드 재사용)
**난이도**: ⭐⭐☆☆☆ (2/10) | **우선순위**: 최고

#### 1.4.1 재생성 로직 테스트 (스마트 삭제 통합)
- [ ] **파일 생성**: `tests/infrastructure/services/test_clean_regeneration.py`
- [ ] **테스트 함수**:
  ```python
  def test_clean_regeneration_flow()           # 삭제→생성 흐름 테스트
  def test_regeneration_with_no_existing_data() # 초기 상태에서 생성
  def test_regeneration_reuses_deletion_logic() # 삭제 로직 재사용 검증
  def test_regeneration_with_user_cancel()     # 사용자 취소 시나리오
  ```

#### 1.4.2 재생성 메서드 구현 (코드 재사용 최적화)
- [ ] **파일 수정**: `upbit_auto_trading/infrastructure/services/api_key_service.py`
- [ ] **메서드 구현** (삭제 기능 재사용):
  ```python
  def save_api_keys_clean(self, access_key, secret_key):
      """깔끔한 재생성: 스마트 삭제 기능 재사용"""
      # 1. 기존 인증정보 존재 시 스마트 삭제 로직 호출
      if self._has_any_existing_credentials():
          deletion_message, deletion_details = self._get_deletion_message()
          if self.confirm_deletion(deletion_message, deletion_details):
              self.delete_api_keys_smart()  # 기존 스마트 삭제 기능 재사용
          else:
              return False, "저장이 취소되었습니다."

      # 2. 새 키 생성 및 저장
      return self._create_and_save_new_credentials(access_key, secret_key)

  def _has_any_existing_credentials(self) -> bool:
      """기존 인증정보 존재 여부 확인"""
      return (self._encryption_key_exists_in_db() or
              self._credentials_file_exists())
  ```#### 1.3.3 사용자 친화적 에러 메시지 테스트 (통합된 메시지)
- [ ] **테스트 추가**:
  ```python
  def test_user_friendly_error_messages()     # 에러 메시지 검증
  def test_consistent_deletion_messages()     # 삭제 메시지 일관성 검증
  ```
- [ ] **에러 메시지 구현** (삭제 기능과 동일):
  ```python
  # 복호화 실패
  "복호화가 실패했습니다. API키를 다시 입력해 주세요."

  # 저장 시 기존 데이터 확인 (삭제 메시지 재사용)
  "암호화 키(DB)와 자격증명 파일을 모두 삭제하고 새로운 API 키를 저장하시겠습니까?"
  "암호화 키(DB)만 존재합니다. 삭제하고 새로운 API 키를 저장하시겠습니까?"
  "자격증명 파일만 존재합니다. 삭제하고 새로운 API 키를 저장하시겠습니까?"
  ```

---

### 🔧 **Task 1.5**: ApiKeyService 기본 통합 (세분화)
**난이도**: ⭐⭐⭐⭐☆ (4/10) | **우선순위**: 최고

#### 1.5.1 서비스 초기화 테스트
- [ ] **파일 생성**: `tests/infrastructure/services/test_api_key_service_init.py`
- [ ] **테스트 함수**:
  ```python
  def test_service_init_with_db_connection()   # DB 연결 초기화만
  def test_service_init_error_handling()       # 초기화 실패 처리
  ```

#### 1.5.2 save_api_keys 기본 통합 테스트
- [ ] **파일 생성**: `tests/infrastructure/services/test_api_key_service_save.py`
- [ ] **테스트 함수**:
  ```python
  def test_save_api_keys_creates_db_key()      # 저장 시 DB 키 생성
  def test_save_api_keys_db_integration()      # DB 통합 검증
  ```

#### 1.5.3 load_api_keys 기본 통합 테스트
- [ ] **파일 생성**: `tests/infrastructure/services/test_api_key_service_load.py`
- [ ] **테스트 함수**:
  ```python
  def test_load_api_keys_uses_db_key()         # 로드 시 DB 키 사용
  def test_load_api_keys_error_scenarios()     # 로드 실패 시나리오
  ```

#### 1.5.4 delete_api_keys 통합 테스트
- [ ] **파일 생성**: `tests/infrastructure/services/test_api_key_service_delete.py`
- [ ] **테스트 함수**:
  ```python
  def test_delete_removes_both_file_and_db()   # 삭제 시 파일+DB 정리
  def test_delete_with_missing_components()    # 일부 누락 시 삭제
  ```

#### 1.5.5 기본 에러 처리 강화
- [ ] **에러 처리 테스트**:
  ```python
  def test_db_connection_failure_handling()    # DB 연결 실패
  def test_key_not_found_vs_decryption_fail()  # 키 없음 vs 복호화 실패
  ```

---

## 🎯 **Level 1 완료 체크포인트**

### 필수 검증 항목
- [ ] **UI 동작 확인**: `python run_desktop_ui.py` 정상 실행
- [ ] **API 키 탭 표시**: API 키 설정 탭에서 입력 필드 정상 표시
- [ ] **기본 저장/로드**: 테스트 API 키로 저장 후 로드 성공
- [ ] **테스트 통과**: `pytest tests/infrastructure/services/test_*key*.py -v` 모든 PASS
- [ ] **DB 상태 확인**: `SELECT * FROM secure_keys` 쿼리로 데이터 확인

### 롤백 준비 (문제 발생 시)
```powershell
# Level 1 완료 상태 백업 생성
$level1Backup = "backups/level1_complete_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $level1Backup -Force
Copy-Item "upbit_auto_trading/infrastructure/services/api_key_service.py" "$level1Backup/" -Force
Copy-Item "data_info/upbit_autotrading_schema_settings.sql" "$level1Backup/" -Force
Copy-Item "tests/infrastructure/services/" "$level1Backup/tests_level1/" -Recurse -Force
Write-Host "✅ Level 1 백업 완료: $level1Backup"
```

### 성공 기준 달성 확인
- [x] **보안 분리**: settings.sqlite3 + config/secure/ 분리 구조 완성
- [x] **기본 CRUD**: 키 생성, 저장, 로드, 삭제 모든 동작 완료
- [x] **사용자 책임 모델**: 명확한 에러 메시지 및 사용자 안내 완료
- [x] **MVP 가치**: 전체 프로젝트의 60% 가치 달성

---

## ⚠️ Level 2: 핵심 기능 구현 (중요, 중간 난이도)

### 🔄 **Task 2.1**: 기본 마이그레이션 시스템 (초세분화)
**난이도**: ⭐⭐⭐⭐⭐⭐ (6/10) | **우선순위**: 높음

#### 2.1.1 레거시 파일 감지 테스트 (첫 단계)
- [ ] **파일 생성**: `tests/infrastructure/services/test_legacy_file_detection.py`
- [ ] **테스트 함수**:
  ```python
  def test_detect_legacy_file_exists()         # 기존 파일 키 감지만
  def test_detect_legacy_file_not_exists()     # 파일 없을 때 처리
  ```

#### 2.1.2 파일 읽기 안전성 테스트 (두 번째 단계)
- [ ] **파일 생성**: `tests/infrastructure/services/test_safe_file_reading.py`
- [ ] **테스트 함수**:
  ```python
  def test_read_file_key_safely()              # 안전한 파일 읽기
  def test_read_corrupted_file_handling()      # 손상된 파일 처리
  ```

#### 2.1.3 기본 마이그레이션 플로우 테스트 (세 번째 단계)
- [ ] **파일 생성**: `tests/infrastructure/services/test_basic_migration.py`
- [ ] **테스트 함수**:
  ```python
  def test_migrate_file_key_to_db_simple()     # 3단계 기본 마이그레이션
  def test_skip_migration_if_db_key_exists()   # DB 키 있으면 스킵
  ```

#### 2.1.4 마이그레이션 로깅 테스트 (네 번째 단계)
- [ ] **테스트 추가**:
  ```python
  def test_migration_logging()                 # 마이그레이션 과정 로깅
  def test_migration_user_notification()       # 사용자 안내 메시지
  ```

#### 2.1.5 간소화된 마이그레이션 구현
- [ ] **메서드 구현**:
  ```python
  def _detect_legacy_encryption_file(self) -> bool
  def _migrate_file_key_to_db_simple(self) -> bool
  def _read_file_key_safely(self) -> Optional[bytes]
  ```
- [ ] **핵심**: 파일감지 → DB저장 → 파일삭제 (실패시 수동정리)

---

### 🔐 **Task 2.2**: Mock 기반 통합 테스트 (세분화)
**난이도**: ⭐⭐⭐⭐⭐ (5/10) | **우선순위**: 높음

#### 2.2.1 Mock 서비스 준비 (첫 단계)
- [ ] **파일 생성**: `tests/mocks/test_mock_upbit_api.py`
- [ ] **Mock 클래스 구현**:
  ```python
  class MockUpbitAPI:
      def test_connection(self, access_key, secret_key) -> bool
      def get_account(self) -> dict
  ```

#### 2.2.2 Mock 기반 저장 테스트 (두 번째 단계)
- [ ] **파일 생성**: `tests/integration/test_mock_save_flow.py`
- [ ] **테스트 함수**:
  ```python
  def test_save_keys_with_db_encryption_mock()  # Mock API로 저장 테스트
  def test_save_flow_error_scenarios_mock()     # 저장 실패 시나리오
  ```

#### 2.2.3 Mock 기반 로드 테스트 (세 번째 단계)
- [ ] **파일 생성**: `tests/integration/test_mock_load_flow.py`
- [ ] **테스트 함수**:
  ```python
  def test_load_and_decrypt_keys_mock()         # Mock API로 로드 테스트
  def test_load_flow_error_scenarios_mock()     # 로드 실패 시나리오
  ```

#### 2.2.4 Mock 기반 전체 사이클 테스트 (네 번째 단계)
- [ ] **파일 생성**: `tests/integration/test_mock_full_cycle.py`
- [ ] **테스트 함수**:
  ```python
  def test_full_cycle_mock()                    # 전체 사이클 Mock 테스트
  def test_full_cycle_with_migration_mock()     # 마이그레이션 포함 사이클
  ```

#### 2.2.5 환경변수 기반 선택적 테스트 (선택적)
- [ ] **파일 생성**: `tests/integration/test_real_api_optional.py` (선택적)
- [ ] **조건부 실행**:
  ```python
  @pytest.mark.skipif(not os.getenv('UPBIT_ACCESS_KEY'), reason="실제 API 키 필요")
  def test_real_api_integration()               # 실제 API 키 테스트
  ```

---

### 🖱️ **Task 2.3**: UI 검증 (수동 우선, 세분화)
**난이도**: ⭐⭐☆☆☆ (2/10) | **우선순위**: 중간

#### 2.3.1 수동 GUI 기본 검증 (첫 단계)
- [ ] **체크리스트 문서**: `docs/manual_testing/ui_basic_checklist.md`
- [ ] **기본 체크**:
  ```
  □ python run_desktop_ui.py 실행 성공
  □ API 키 설정 탭 표시 확인
  □ 입력 필드 정상 표시 확인
  ```

#### 2.3.2 수동 저장 플로우 검증 (두 번째 단계)
- [ ] **체크리스트 추가**:
  ```
  □ 저장 버튼 클릭 가능
  □ 키 저장 성공 메시지 표시
  □ DB에 키 저장 확인
  ```

#### 2.3.3 수동 로드 플로우 검증 (세 번째 단계)
- [ ] **체크리스트 추가**:
  ```
  □ 로드 후 마스킹된 키 표시 확인
  □ 복호화 성공 확인
  □ API 연결 테스트 버튼 작동
  ```

#### 2.3.4 수동 삭제 플로우 검증 (네 번째 단계)
- [ ] **체크리스트 추가**:
  ```
  □ 삭제 버튼 클릭 → 확인 대화상자
  □ 상황별 삭제 메시지 확인
  □ 삭제 완료 후 초기 상태 복원
  ```

#### 2.3.5 간단한 메서드 테스트 (대안)
- [ ] **파일 생성**: `tests/ui/test_api_key_ui_methods.py` (선택적)
- [ ] **직접 호출 테스트**:
  ```python
  def test_save_method_direct_call()            # UI 신호 없이 메서드만
  def test_load_method_direct_call()            # 직접 메서드 호출
  def test_delete_method_direct_call()          # 삭제 메서드 직접 테스트
  ```

---

### 🔍 **Task 2.4**: 기본 보안 검증 (세분화)
**난이도**: ⭐⭐⭐⭐☆ (4/10) | **우선순위**: 중간

#### 2.4.1 파일 분리 효과 테스트 (첫 단계)
- [ ] **파일 생성**: `tests/security/test_file_separation.py`
- [ ] **테스트 함수**:
  ```python
  def test_config_folder_alone_undecryptable()  # config만으로 복호화 불가
  def test_config_folder_copy_scenario()        # config 폴더 복사 시나리오
  ```

#### 2.4.2 자격증명 단독 무력화 테스트 (두 번째 단계)
- [ ] **테스트 추가**:
  ```python
  def test_credentials_without_db_useless()     # 자격증명만으로 무의미
  def test_credentials_file_only_scenario()     # 자격증명 파일만 획득 시
  ```

#### 2.4.3 기본 분리 검증 테스트 (세 번째 단계)
- [ ] **테스트 추가**:
  ```python
  def test_basic_separation_verification()      # 기본 분리 효과 확인
  def test_separation_state_check()             # 분리 상태 체크
  ```

#### 2.4.4 보안 상태 시각화 (네 번째 단계)
- [ ] **파일 생성**: `tests/security/test_security_status.py`
- [ ] **테스트 함수**:
  ```python
  def test_security_status_display()            # 보안 상태 표시
  def test_security_improvement_notification()  # 보안 개선 알림
  ```

---

## 🎯 **Level 2 완료 체크포인트**

### 필수 검증 항목
- [ ] **마이그레이션 동작**: 기존 파일 키가 DB로 정상 이전
- [ ] **Mock 테스트 통과**: 모든 Mock 기반 통합 테스트 PASS
- [ ] **UI 수동 검증**: 저장/로드/삭제 플로우 사용자 친화적 동작
- [ ] **보안 분리 확인**: config 폴더만으로 복호화 불가 검증
- [ ] **전체 테스트**: `pytest tests/ -v` 모든 테스트 PASS

### 롤백 준비 (문제 발생 시)
```powershell
# Level 2 완료 상태 백업 생성
$level2Backup = "backups/level2_complete_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $level2Backup -Force
Copy-Item "upbit_auto_trading/" "$level2Backup/upbit_auto_trading/" -Recurse -Force
Copy-Item "tests/" "$level2Backup/tests/" -Recurse -Force
Copy-Item "data_info/" "$level2Backup/data_info/" -Recurse -Force
Write-Host "✅ Level 2 백업 완료: $level2Backup"
```

### 성공 기준 달성 확인
- [x] **실용적 완성도**: 기존 사용자도 무리 없이 마이그레이션
- [x] **안정성 확보**: Mock 테스트로 다양한 시나리오 검증
- [x] **사용자 경험**: UI에서 직관적이고 명확한 동작
- [x] **보안 효과**: 파일 분리로 실질적 보안 향상 달성
- [x] **권장 성공**: 전체 프로젝트의 80% 가치 달성

---

## 🔵 Level 3: 선택적 고도화 (높은 난이도)

### 🌟 **Task 2.5**: 단순 API 모니터링 (하이브리드 추가 기능)
**난이도**: ⭐⭐☆☆☆ (2/10) | **우선순위**: 중간-높음

#### 2.5.1 실패 카운터 기본 구현 (첫 단계)
- [ ] **파일 생성**: `tests/monitoring/test_simple_failure_monitor.py`
- [ ] **테스트 함수**:
  ```python
  def test_failure_counter_basic()              # 기본 실패 카운터
  def test_consecutive_failures_detection()     # 연속 실패 감지
  ```

#### 2.5.2 실패 카운터 클래스 구현 (두 번째 단계)
- [ ] **파일 생성**: `upbit_auto_trading/infrastructure/monitoring/simple_failure_monitor.py`
- [ ] **클래스 구현**:
  ```python
  class SimpleFailureMonitor:
      def __init__(self):
          self.consecutive_failures = 0

      def mark_api_result(self, success: bool):
          if success:
              self.consecutive_failures = 0
          else:
              self.consecutive_failures += 1

          # 3회 연속 실패 시만 UI 업데이트
          if self.consecutive_failures >= 3:
              self.status_bar.set_api_status_failed()
  ```

#### 2.5.3 상태바 클릭 기능 구현 (세 번째 단계)
- [ ] **파일 생성**: `tests/ui/test_clickable_status_bar.py`
- [ ] **테스트 함수**:
  ```python
  def test_clickable_api_status()               # 클릭 가능 상태바
  def test_cooldown_functionality()             # 10초 쿨다운 기능
  ```

#### 2.5.4 클릭 가능 상태바 구현 (네 번째 단계)
- [ ] **파일 생성**: `upbit_auto_trading/ui/desktop/widgets/clickable_status_bar.py`
- [ ] **클래스 구현**:
  ```python
  class ClickableApiStatus(QLabel):
      refresh_requested = pyqtSignal()

      def mousePressEvent(self, event):
          if self.is_enabled and event.button() == Qt.MouseButton.LeftButton:
              self.refresh_requested.emit()
              self.start_cooldown()
  ```

#### 2.5.5 API 지점 통합 (다섯 번째 단계)
- [ ] **5개 핵심 API 지점 수정**:
  ```python
  # UpbitAPI.get_account()
  # UpbitAPI.get_candles()
  # UpbitAPI.get_tickers()
  # UpbitAPI.get_orderbook()
  # UpbitAPI.test_api_connection()
  ```
- [ ] **각 지점에 실패 카운터 추가**

---

### 🛡️ **Task 3.1**: 고급 마이그레이션 (롤백 포함) - 선택적
**난이도**: ⭐⭐⭐⭐⭐⭐⭐⭐ (8/10) | **우선순위**: 낮음

#### 3.1.1 백업 로직 구현 (고급)
- [ ] **파일 생성**: `tests/infrastructure/services/test_migration_backup.py`
- [ ] **백업/복구 로직 테스트**

#### 3.1.2 원자적 마이그레이션 구현 (고급)
- [ ] **5단계 원자적 처리**: 백업→읽기→저장→검증→삭제
- [ ] **롤백 로직 구현**

### 🌐 **Task 3.2**: 실제 API 연결 테스트 (고급) - 선택적
**난이도**: ⭐⭐⭐⭐⭐⭐ (6/10) | **우선순위**: 낮음

#### 3.2.1 실제 업비트 API 테스트
- [ ] **전제 조건**: `.env` 파일에 실제 API 키 필요
- [ ] **네트워크 의존성 테스트**

### 🖱️ **Task 3.3**: PyQt 신호 기반 UI 테스트 (고급) - 선택적
**난이도**: ⭐⭐⭐⭐⭐⭐⭐⭐ (8/10) | **우선순위**: 낮음

#### 3.3.1 복잡한 PyQt 신호 테스트
- [ ] **QTest, QSignalSpy 활용**
- [ ] **비동기 신호 처리 테스트**

### 📊 **Task 3.4**: 정량적 보안 측정 (고급) - 선택적
**난이도**: ⭐⭐⭐⭐⭐⭐⭐ (7/10) | **우선순위**: 낮음

#### 3.4.1 보안 위험도 정량 측정
- [ ] **12가지 탈취 시나리오 시뮬레이션**
- [ ] **보안 개선 효과 수치화**

---

## 📊 세분화된 구현 우선순위

### ✅ **즉시 시작** (Level 1 - MVP, 초세분화)
1. **Task 1.1**: DB 스키마 (5단계로 세분화, 난이도 3/10)
2. **Task 1.2**: DB 키 저장/로드 (5단계로 세분화, 난이도 4/10)
3. **Task 1.3**: 스마트 삭제 로직 (3단계, 난이도 3/10) ✅ 수정됨
4. **Task 1.4**: 재생성 로직 + 코드 재사용 (3단계, 난이도 2/10) ✅ 수정됨
5. **Task 1.5**: 서비스 통합 (5단계로 세분화, 난이도 4/10)

### ⚠️ **다음 단계** (Level 2 - 핵심, 초세분화)
6. **Task 2.1**: 기본 마이그레이션 (5단계로 세분화, 난이도 6/10)
7. **Task 2.2**: Mock 통합 테스트 (5단계로 세분화, 난이도 5/10)
8. **Task 2.3**: UI 수동 검증 (5단계로 세분화, 난이도 2/10)
9. **Task 2.4**: 기본 보안 검증 (4단계로 세분화, 난이도 4/10)

### 🌟 **하이브리드 추가** (API 모니터링)
10. **Task 2.5**: 단순 API 모니터링 (5단계로 세분화, 난이도 2/10)

### 🔴 **선택적 고도화** (Level 3 - 고급)
11. **Task 3.1**: 고급 마이그레이션 (난이도 8/10) - 선택
12. **Task 3.2**: 실제 API 테스트 (난이도 6/10) - 선택
13. **Task 3.3**: PyQt UI 테스트 (난이도 8/10) - 선택
14. **Task 3.4**: 정량적 보안 (난이도 7/10) - 선택

---

## 🎯 세분화된 성공 기준

### ✅ **최소 성공**: Level 1 완료 (API 키 보안)
- DB 기반 키 관리 시스템 구축
- 사용자 책임 모델 구현
- 기본 보안 분리 효과 확보
- **가치**: 전체의 60%

### 🎯 **권장 성공**: Level 1-2 완료 (보안 + 마이그레이션)
- 실용적 완성도 확보
- 기존 사용자 마이그레이션 지원
- 기본 보안 검증 완료
- **가치**: 전체의 80%

### 🌟 **하이브리드 성공**: Level 1-2 + Task 2.5 (보안 + 모니터링)
- API 키 보안 + API 모니터링 통합
- 실시간 API 상태 모니터링
- 클릭 가능 상태바 UI
- **가치**: 전체의 90%

### 🏆 **완벽 성공**: Level 1-3 완료 (모든 기능)
- 모든 고급 기능 포함
- 완전한 보안 강화 달성
- **가치**: 전체의 100%

---

## 🚀 세분화된 실행 전략

### � **테스트 데이터 관리**

#### 테스트용 더미 데이터 생성
```python
# 테스트용 암호화 키 생성
import os
test_encryption_key = os.urandom(32)  # 32바이트 랜덤 키

# 테스트용 API 자격증명
test_credentials = {
    "access_key": "TEST_ACCESS_KEY_1234567890ABCDEF",
    "secret_key": "TEST_SECRET_KEY_1234567890ABCDEF"
}

# 임시 DB 파일 생성 (테스트 격리)
import tempfile
test_db = tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False)
```

#### 실제 API 키 테스트 (선택적)
```python
# .env 파일 기반 실제 API 테스트 (Task 3.2에서 사용)
import os
from dotenv import load_dotenv

@pytest.mark.skipif(not os.getenv('UPBIT_ACCESS_KEY'), reason="실제 API 키 필요")
def test_real_api_integration():
    load_dotenv()
    access_key = os.getenv('UPBIT_ACCESS_KEY')  # 실제 키 사용
    secret_key = os.getenv('UPBIT_SECRET_KEY')
```

### 📝 **코딩 스타일 가이드**

#### 필수 코딩 원칙
- **타입 힌트**: 모든 메서드에 타입 힌트 필수
  ```python
  def _save_encryption_key_to_db(self, key_data: bytes) -> bool:
  def _get_deletion_message(self) -> tuple[str, str]:
  ```
- **docstring**: Google 스타일 docstring 사용
  ```python
  def delete_api_keys_smart(self) -> str:
      """상황별 명확한 삭제 로직을 수행합니다.

      Returns:
          str: 삭제 결과 메시지 ('삭제 완료: 항목들' 또는 '삭제 취소됨')

      Raises:
          DatabaseError: DB 연결 실패 시
          PermissionError: 파일 접근 권한 없을 시
      """
  ```
- **에러 처리**: `try-except` 최소화, 명시적 검증 우선
  ```python
  # ❌ 피할 패턴
  try:
      result = risky_operation()
  except:
      return None

  # ✅ 권장 패턴
  if not self._prerequisites_met():
      raise ValidationError("전제 조건 미충족: DB 연결 불가")
  return safe_operation()
  ```
- **로깅**: Infrastructure 로깅 시스템 필수 사용
  ```python
  from upbit_auto_trading.infrastructure.logging import create_component_logger
  logger = create_component_logger("ApiKeyService")
  logger.info("암호화 키 저장 시작")
  logger.error(f"❌ DB 저장 실패: {error}")
  ```

### �📝 차근차근 개발 워크플로우
1. **한 번에 하나씩**: 복잡한 테스트를 작은 단위로 분할
2. **점진적 확장**: 기본 기능 → 추가 기능 → 고급 기능
3. **안전한 진행**: 각 단계 완료 후 다음 단계 진행
4. **실시간 검증**: 매 단계마다 `python run_desktop_ui.py` 실행

### ⚡ 단계별 테스트 실행 (세분화)
```bash
# Level 1.1: DB 스키마 (단계별)
pytest tests/infrastructure/services/test_secure_keys_schema_basic.py::test_secure_keys_table_exists -v
pytest tests/infrastructure/services/test_secure_keys_schema_basic.py::test_secure_keys_schema_structure -v
pytest tests/infrastructure/services/test_secure_keys_schema_basic.py::test_unique_constraint_on_key_type -v

# Level 1.2: DB 키 관리 (단계별)
pytest tests/infrastructure/services/test_db_connection.py -v
pytest tests/infrastructure/services/test_save_encryption_key.py -v
pytest tests/infrastructure/services/test_load_encryption_key.py -v
pytest tests/infrastructure/services/test_delete_encryption_key.py -v

# Level 1.3-1.5: 서비스 통합 (단계별)
pytest tests/infrastructure/services/test_clean_regeneration.py -v
pytest tests/infrastructure/services/test_smart_deletion.py -v
pytest tests/infrastructure/services/test_api_key_service_init.py -v

# Level 2: 핵심 기능 (선택적)
pytest tests/infrastructure/services/test_legacy_file_detection.py -v
pytest tests/integration/test_mock_save_flow.py -v

# 하이브리드: API 모니터링 (선택적)
pytest tests/monitoring/test_simple_failure_monitor.py -v
```

### 🎯 **핵심 세분화 원칙**
1. **복잡한 테스트 금지**: 한 번에 많은 기능을 테스트하지 않음
2. **단계별 완성**: 각 단계를 완전히 완료한 후 다음 진행
3. **점진적 통합**: 작은 기능들을 차근차근 통합
4. **실용성 우선**: 70% 가치를 80% 효율로 달성

### 🏆 **최종 목표 (하이브리드)**
- **안전한 API 키 관리**: DB 기반 보안 시스템
- **실시간 모니터링**: 3회 연속 실패 감지
- **사용자 친화적**: 명확한 에러 메시지와 상황별 안내
- **점진적 확장**: 선택적 고급 기능으로 완전성 추구

**🎯 핵심 철학**: 차근차근 단계별로, 복잡함보다는 단순함과 안정성을 추구!

---

## � **Task 의존성 그래프 및 기존 코드 통합**

### Task 간 의존성 흐름
```
📋 Task 1.1 (DB 스키마)
    ↓ secure_keys 테이블 생성
🔑 Task 1.2 (DB 키 관리)
    ↓ CRUD 메서드 구현
🗑️ Task 1.3 (스마트 삭제) ← 기반 기능
    ↓ _get_deletion_message() 제공
🔄 Task 1.4 (재생성 + 재사용) ← 삭제 기능 활용
    ↓ save_api_keys_clean() 구현
🔧 Task 1.5 (서비스 통합)
    ↓ Level 1 완료
⚠️ Level 2: 마이그레이션, Mock 테스트, UI 검증, 보안 검증
    ↓ Level 2 완료
🌟 Task 2.5 (API 모니터링) ← 하이브리드 추가
    ↓ 하이브리드 완료
🔵 Level 3: 고급 기능들 (선택적)
```

### 기존 코드 통합 지점
#### UI 연결 지점
- [ ] **메인 탭**: `upbit_auto_trading/ui/desktop/tabs/api_key_tab.py`
  - `save_button.clicked.connect(self.save_api_keys_clean)` 연결
  - `delete_button.clicked.connect(self.delete_api_keys_smart)` 연결

#### 설정 및 경로 관리
- [ ] **DB 경로**: `config/simple_paths.py`의 `get_settings_db_path()` 활용
- [ ] **보안 폴더**: `config/simple_paths.py`의 `get_secure_config_path()` 활용

#### 로깅 시스템 통합
- [ ] **Infrastructure 로깅**: `upbit_auto_trading/infrastructure/logging` 시스템 필수 사용
- [ ] **컴포넌트 로거**: `create_component_logger("ApiKeyService")` 사용

#### 기존 API 서비스 연동
- [ ] **UpbitAPI 클래스**: `upbit_auto_trading/infrastructure/external_api/upbit_api.py`
- [ ] **API 연결 테스트**: 기존 `test_api_connection()` 메서드 활용

---

## �💡 하이브리드 시스템 특별 고려사항

### 🔄 **사용자 책임 모델 핵심**
- **프로그램 책임**: settings.sqlite3에서 암호화 키 자동 관리
- **사용자 책임**: config/secure/api_credentials.json 파일 관리
- **에러 단순화**: 모든 실패를 사용자 책임으로 명확히 안내

### 📊 **API 모니터링 핵심**
- **실패 감지 전용**: 정상 상태는 체크하지 않음 (리소스 절약)
- **노이즈 필터링**: 3회 연속 실패 시만 UI 업데이트
- **수동 새로고침**: 10초 쿨다운으로 남용 방지

### 🎯 **통합 개발 순서**
1. **1순위**: API 키 보안 시스템 완성 (Level 1-2)
2. **2순위**: API 모니터링 추가 (Task 2.5)
3. **3순위**: 고급 기능 선택적 구현 (Level 3)

**🚀 최종 비전**: 보안과 편의성을 모두 갖춘 하이브리드 통합 시스템!
