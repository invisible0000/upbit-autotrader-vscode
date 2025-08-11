# TASK-20250810-01: API 키 로드 오류 긴급 수정

## 📋 작업 개요
**우선순위**: 🔴 긴급
**담당자**: GitHub Copilot
**생성일**: 2025-08-10
**예상 소요**: 2-3시간

## 🎯 문제 정의
API 자격증명 파일(`config/secure/api_credentials.json`)과 암호화 키(`settings.sqlite3:secure_keys`)가 존재하지만 `ApiKeyService`에서 "API 키 로드 중 오류" 발생하여 실거래 기능 차단됨.

## 🔍 현재 상태 분석
- ✅ `config/secure/api_credentials.json` 파일 존재 확인됨
- ✅ `settings.sqlite3:secure_keys` 테이블에 3개 레코드 존재
- ❌ `ApiKeyService.load_api_keys()` 호출시 빈 예외 발생
- ❌ UI에서 "API 키 파일이 없습니다" 경고 표시

## 📊 서브 태스크 분할

### **서브태스크 1.1: 파일 경로 및 권한 검증** (난이도: ⭐)
- [ ] **1.1.1**: `config/secure/api_credentials.json` 파일 읽기 권한 확인
- [ ] **1.1.2**: 파일 내용 구조 검증 (JSON 형식, 필수 키 존재)
- [ ] **1.1.3**: 파일 크기 및 인코딩 확인

**TDD 테스트**:
```python
def test_api_credentials_file_accessibility():
    """API 자격증명 파일 접근성 테스트"""
    file_path = Path("config/secure/api_credentials.json")
    assert file_path.exists()
    assert file_path.is_file()
    assert os.access(file_path, os.R_OK)
```

### **서브태스크 1.2: 암호화 키 검증** (난이도: ⭐⭐)
- [ ] **1.2.1**: `settings.sqlite3:secure_keys` 테이블 구조 확인
- [ ] **1.2.2**: 암호화 키 유효성 검증 (key_type, key_value)
- [ ] **1.2.3**: 복호화 프로세스 단계별 테스트

**TDD 테스트**:
```python
def test_encryption_key_validity():
    """암호화 키 유효성 테스트"""
    service = ApiKeyService()
    encryption_keys = service._load_encryption_keys()
    assert len(encryption_keys) > 0
    for key in encryption_keys:
        assert key.key_type in ['master', 'api', 'backup']
        assert len(key.key_value) >= 32  # 최소 256bit
```

### **서브태스크 1.3: ApiKeyService 로직 디버깅** (난이도: ⭐⭐⭐)
- [ ] **1.3.1**: `load_api_keys()` 메서드 예외 처리 로직 검토
- [ ] **1.3.2**: 파일 읽기 → 복호화 → 파싱 단계별 분리 테스트
- [ ] **1.3.3**: 로깅 레벨 증가하여 상세 오류 추적

**TDD 테스트**:
```python
def test_api_key_loading_process():
    """API 키 로딩 프로세스 단계별 테스트"""
    service = ApiKeyService()

    # 1단계: 파일 읽기
    raw_data = service._read_credentials_file()
    assert raw_data is not None

    # 2단계: 복호화
    decrypted_data = service._decrypt_credentials(raw_data)
    assert decrypted_data is not None

    # 3단계: 파싱
    api_keys = service._parse_api_credentials(decrypted_data)
    assert 'access_key' in api_keys
    assert 'secret_key' in api_keys
```

### **서브태스크 1.4: 에러 메시지 상세화** (난이도: ⭐)
- [ ] **1.4.1**: 빈 예외 대신 구체적 오류 메시지 추가
- [ ] **1.4.2**: 단계별 실패 지점 식별 로깅 추가
- [ ] **1.4.3**: 사용자 친화적 오류 안내 메시지 작성

**UX 검증**:
```python
def test_user_friendly_error_messages():
    """사용자 친화적 오류 메시지 테스트"""
    try:
        service = ApiKeyService()
        service.load_api_keys()
    except ApiKeyLoadError as e:
        assert "파일을 찾을 수 없습니다" in str(e) or \
               "복호화에 실패했습니다" in str(e) or \
               "잘못된 형식입니다" in str(e)
        assert len(str(e)) > 10  # 의미있는 길이
```

## 🧪 통합 테스트 시나리오

### **시나리오 A: 정상 케이스**
1. 기존 자격증명 파일로 API 키 로드
2. Upbit API 연결 테스트 수행
3. UI에서 "연결됨" 상태 확인

### **시나리오 B: 파일 손상 케이스**
1. 자격증명 파일 일부 손상 시뮬레이션
2. 적절한 오류 메시지 표시 확인
3. 복구 가이드 제공 확인

### **시나리오 C: 암호화 키 불일치 케이스**
1. 잘못된 암호화 키로 복호화 시도
2. 보안을 위한 재설정 안내 확인
3. 데이터 무결성 검증

## ✅ 완료 조건
- [ ] API 키 로드 성공률 100% (기존 유효 파일 기준)
- [ ] 오류 발생시 구체적 메시지 제공 (최소 3가지 시나리오)
- [ ] UI에서 정확한 연결 상태 표시
- [ ] 모든 TDD 테스트 통과 (최소 커버리지 90%)

## 🚨 리스크 및 주의사항
1. **보안**: API 키 디버깅시 로그에 평문 노출 금지
2. **데이터 무결성**: 기존 암호화된 데이터 손상 방지
3. **UX**: 사용자가 이해할 수 있는 오류 메시지 필수
4. **성능**: 키 로딩 프로세스 5초 이내 완료

## 📝 검증 체크리스트
- [ ] 기존 API 키로 정상 로그인 확인
- [ ] 새로운 API 키 등록 프로세스 정상 동작
- [ ] 잘못된 API 키 입력시 적절한 오류 처리
- [ ] 프로덕션 환경에서 실거래 가능 상태 확인
- [ ] 개발 환경에서 모의거래 정상 동작 확인

## 🔄 다음 태스크 연계
성공시 → **TASK-20250810-05** (프로파일 전환시 API 키 유지)
실패시 → API 키 관리 시스템 전면 재검토 필요
