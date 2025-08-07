# 🚀 ApiKeyService 빠른 참조 (LLM 에이전트용)

> **빠른 작업을 위한 핵심 메서드 치트시트**

## ⭐ 필수 메서드 TOP 10

### 🔑 **API 키 관리**
```python
# 1. 깔끔한 저장 (권장)
success, msg = service.save_api_keys_clean(access_key, secret_key)

# 2. 스마트 삭제 (권장)
result = service.delete_api_keys_smart()

# 3. 키 로드
access_key, secret_key, permission = service.load_api_keys()

# 4. 키 존재 확인
has_keys = service.has_valid_keys()
```

### ⚡ **API 인스턴스 (Task 2.3 - 83% 성능 향상)**
```python
# 5. 최적화된 인스턴스 획득 (권장)
api = service.get_or_create_api_instance()

# 6. 캐시만 확인
api = service.get_cached_api_instance()

# 7. 새로 생성하고 캐싱
api = service.cache_api_instance()

# 8. 캐시 무효화 (키 변경 시 자동 호출됨)
service.invalidate_api_cache()
```

### 🛠️ **디버깅/모니터링**
```python
# 9. 캐시 상태 확인
status = service.get_cache_status()

# 10. 캐시 완전 정리
service.clear_cache()
```

---

## 📋 메서드 분류별 치트시트

### 🟢 **Public API (사용 빈도순)**

| 메서드 | 용도 | 반환 | 라인 |
|--------|------|------|------|
| `get_or_create_api_instance()` | API 인스턴스 (권장) | `UpbitClient\|None` | 890 |
| `save_api_keys_clean()` | 깔끔한 저장 (권장) | `(bool, str)` | 607 |
| `delete_api_keys_smart()` | 스마트 삭제 (권장) | `str` | 451 |
| `load_api_keys()` | 키 복호화 로드 | `(str\|None, str\|None, bool)` | 248 |
| `has_valid_keys()` | 키 존재 확인 | `bool` | 341 |
| `get_cached_api_instance()` | 캐시된 인스턴스만 | `UpbitClient\|None` | 713 |
| `invalidate_api_cache()` | 캐시 무효화 | `None` | 801 |
| `get_cache_status()` | 캐시 상태 정보 | `dict` | 932 |
| `cache_api_instance()` | 새로 생성+캐싱 | `UpbitClient\|None` | 751 |
| `clear_cache()` | 캐시 정리 | `None` | 923 |
| `save_api_keys()` | 기본 저장 | `bool` | 190 |
| `delete_api_keys()` | 기본 삭제 | `bool` | 301 |
| `get_secret_key_mask_length()` | 마스킹 길이 | `int` | 353 |
| `test_api_connection()` | 연결 테스트 (미구현) | `(bool, str, dict)` | 286 |

### 🔴 **Private 메서드 (내부 작업용)**

| 분류 | 주요 메서드 | 용도 |
|------|-------------|------|
| **DB 관리** | `_save_encryption_key_to_db()` | DB 키 저장 |
|  | `_load_encryption_key_from_db()` | DB 키 로드 |
|  | `_delete_encryption_key_from_db()` | DB 키 삭제 |
| **파일 관리** | `_credentials_file_exists()` | 자격증명 파일 확인 |
|  | `_delete_credentials_file()` | 자격증명 파일 삭제 |
| **스마트 로직** | `_get_deletion_message()` | 삭제 메시지 생성 |
|  | `_execute_deletion()` | 실제 삭제 실행 |
| **캐시 검증** | `_is_cache_valid()` | TTL + 키 변경 검사 |

---

## 🔄 일반적인 작업 시나리오

### 1️⃣ **신규 API 키 설정**
```python
service = ApiKeyService(secure_keys_repository)
success, message = service.save_api_keys_clean("access_key", "secret_key")
if success:
    api = service.get_or_create_api_instance()
```

### 2️⃣ **기존 키로 API 사용**
```python
if service.has_valid_keys():
    api = service.get_or_create_api_instance()  # 캐시 활용
    if api:
        accounts = await api.get_accounts()
```

### 3️⃣ **키 교체**
```python
# 자동으로 기존 삭제 후 새로 저장
success, msg = service.save_api_keys_clean(new_access, new_secret)
# 캐시도 자동 무효화됨
```

### 4️⃣ **완전 삭제**
```python
result = service.delete_api_keys_smart()  # UI 확인 포함
print(result)  # "삭제 완료: 암호화 키(DB), 자격증명 파일"
```

### 5️⃣ **성능 모니터링**
```python
status = service.get_cache_status()
print(f"캐시 적중: {status['valid']}")
print(f"캐시 나이: {status['age_seconds']}초")
print(f"TTL: {status['ttl_seconds']}초")
```

### 6️⃣ **테스트/디버깅**
```python
service.clear_cache()  # 캐시 정리
status = service.get_cache_status()  # 상태 확인
api = service.cache_api_instance()  # 강제 새로 생성
```

---

## ⚡ 성능 가이드 (Task 2.3)

### 🚀 **최고 성능 패턴**
```python
# 권장: 83.7% 성능 향상
api = service.get_or_create_api_instance()

# 고급: 캐시 우선
api = service.get_cached_api_instance()
if api is None:
    api = service.cache_api_instance()
```

### 📊 **성능 메트릭**
- **기존**: `load_api_keys()` + `UpbitClient()` = 2.23ms
- **캐싱**: `get_or_create_api_instance()` = 0.57ms
- **개선**: **83.7% 성능 향상** ✅

### ⏰ **TTL 정보**
- **TTL**: 5분 (300초)
- **키 변경 감지**: SHA256 해시 비교
- **자동 무효화**: 키 저장/삭제 시

---

## 🛡️ 보안 고려사항

### ✅ **자동 보안 처리**
- 메모리에서 평문 키 즉시 삭제
- 가비지 컬렉션 유도 (`gc.collect()`)
- 키 해시 마스킹 (`1234****5678`)
- 암호화 키와 API 키 분리 저장

### ⚠️ **주의사항**
- TTL 캐싱은 5분간 메모리에 키 보존 (성능 vs 보안 균형점)
- 키 변경 시 자동 캐시 무효화로 보안 유지
- Repository 패턴으로 DB 접근 추상화

---

## 🔧 에러 처리 패턴

### 안전한 에러 처리
```python
# ✅ 올바른 방식: Exception 명확히 전파
access_key, secret_key, _ = service.load_api_keys()
if not access_key:
    raise ApiKeyNotFoundError("API 키가 설정되지 않았습니다")

# ✅ 폴백 패턴
api = service.get_cached_api_instance()
if api is None:
    api = service.cache_api_instance()
    if api is None:
        raise ApiKeyError("API 인스턴스 생성 실패")
```

---

## 📝 실제 코드 위치

**파일**: `upbit_auto_trading/infrastructure/services/api_key_service.py`

**주요 라인 번호**:
- Public API: 190~932
- TTL 캐싱: 713~932 (Task 2.3)
- 스마트 삭제: 451~605 (Task 1.3)
- 깔끔한 재생성: 607~709 (Task 1.4)

**관련 테스트**:
- `tests/infrastructure/services/test_api_caching.py`
- `tests/infrastructure/services/test_api_caching_advanced.py`

**사용 예시**:
- `examples/api_caching_usage_example.py`
- `examples/API_CACHING_MIGRATION_GUIDE.md`

---

**🎯 핵심**: `get_or_create_api_instance()` 하나면 대부분의 경우 충분합니다!**
