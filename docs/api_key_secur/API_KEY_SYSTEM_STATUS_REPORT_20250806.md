# 📋 API 키 시스템 현황 보고서 및 구현 분석

**작성일**: 2025년 8월 6일
**세션**: 업비트 자동매매 시스템 API 키 관리 시스템 개발
**상태**: 🔴 키 복호화 실패 - 암호화키/자격증명 불일치 문제

---

## 🚨 현재 발생 중인 문제

### 1. 핵심 문제: 암호화키-자격증명 불일치
```bash
# 현재 상태 확인 결과
Keys valid: True          # 파일은 존재함
Access key loaded: False  # 하지만 복호화 실패
Secret key loaded: False  # 하지만 복호화 실패
Trade permission: False   # 기본값으로 설정됨
```

**문제 원인**: 기존에 저장된 암호화된 자격증명과 현재 암호화 키가 서로 다른 키로 생성되어 복호화가 불가능한 상태

### 2. 파일 시스템 상태
- ✅ `config/secure/api_credentials.json` - 존재 (암호화된 데이터)
- ✅ `config/secure/encryption_key.key` - 존재
- ❌ **암호화키와 자격증명이 서로 다른 세션에서 생성되어 호환되지 않음**

### 3. UI 동작 문제
- API 키 탭에서 access_key가 로드되지 않음 (복호화 실패)
- 삭제 버튼 클릭 시 "키 파일이 없다"고 표시 (실제로는 복호화 실패)

---

## 🏗️ 현재 구현된 API 키 시스템 아키텍처

### 1. 새로운 암호화 키 생성 정책 (2025-08-06 구현)

#### 기존 정책 (문제있던 방식)
```python
# ❌ 문제: 프로그램 시작 시마다 키 생성
def __init__(self):
    self._setup_encryption_key()  # 매번 새 키 생성 위험
```

#### 새로운 정책 (수정된 방식)
```python
# ✅ 개선: 저장 시에만 키 생성
def __init__(self):
    self._try_load_existing_encryption_key()  # 기존 키만 로드

def save_api_keys(self, access_key, secret_key, trade_permission):
    if self.fernet is None:
        self._create_new_encryption_key()  # 저장 시에만 새 키 생성
```

### 2. 4단계 암호화 키 라이프사이클

#### 단계 1: 프로그램 시작 시
```python
def _try_load_existing_encryption_key(self):
    if encryption_key_path.exists():
        # 기존 암호화 키 로드
        self.encryption_key = key_file.read()
        self.fernet = Fernet(self.encryption_key)
    else:
        # 키가 없으면 None으로 유지
        self.encryption_key = None
        self.fernet = None
```

#### 단계 2: 저장 버튼 클릭 시
```python
def save_api_keys(self, access_key, secret_key, trade_permission):
    if self.fernet is None:
        # 새로운 암호화 키 생성 및 기존 파일 정리
        self._create_new_encryption_key()

    # API 키 암호화 및 저장
```

#### 단계 3: 로드 시
```python
def load_api_keys(self):
    if self.fernet is None:
        self.logger.error("암호화 키가 없어서 API 키를 복호화할 수 없습니다.")
        return None, None, False

    # 복호화 및 반환
```

#### 단계 4: 삭제 시
```python
def delete_api_keys(self):
    # API 자격증명 파일 삭제
    # 암호화 키 파일 삭제
    # 메모리에서 키 정보 제거
```

### 3. 보안 아키텍처

#### 파일 시스템 구조
```
config/secure/           # .gitignore로 보호됨
├── encryption_key.key   # Fernet 암호화 키 (바이너리)
└── api_credentials.json # 암호화된 자격증명
```

#### 암호화 방식
- **라이브러리**: `cryptography.fernet` (AES 128 + HMAC)
- **키 생성**: `Fernet.generate_key()` - 32바이트 랜덤 키
- **저장 형식**: Base64 인코딩된 암호화 텍스트

#### 메모리 보안
```python
# 사용 후 즉시 메모리 정리
access_key = ""
secret_key = ""
gc.collect()
```

---

## 📋 API 키 설정 시나리오별 로직 분석

### 시나리오 1: 완전 초기 상태 (Clean State)
**상황**: 암호화 키도 자격증명도 없는 상태

```python
# 파일 상태
encryption_key.key: ❌ 없음
api_credentials.json: ❌ 없음

# 로직 흐름
1. 프로그램 시작 → _try_load_existing_encryption_key() → self.fernet = None
2. UI 로드 → load_api_keys() → None, None, False 반환
3. 사용자 입력 후 저장 → _create_new_encryption_key() → 새 키 생성
4. API 키 암호화 저장 → 완료
```

### 시나리오 2: 정상 작동 상태 (Working State)
**상황**: 올바른 암호화 키와 자격증명이 모두 존재

```python
# 파일 상태
encryption_key.key: ✅ 존재하고 올바름
api_credentials.json: ✅ 존재하고 호환됨

# 로직 흐름
1. 프로그램 시작 → 암호화 키 로드 성공
2. UI 로드 → 복호화 성공 → 화면에 표시
3. 수정 시 → 기존 키로 재암호화
```

### 시나리오 3: 키 업데이트 상태 (Update State)
**상황**: 사용자가 새로운 API 키로 교체하려는 경우

```python
# 파일 상태
encryption_key.key: ✅ 존재
api_credentials.json: ✅ 존재 (기존 키)

# 로직 흐름
1. 기존 키 로드 및 표시
2. 사용자가 새 키 입력
3. 저장 → 기존 암호화 키로 새 API 키 암호화
4. 덮어쓰기 완료
```

### 시나리오 4: 초기화 상태 (Reset State)
**상황**: 사용자가 삭제 버튼을 눌러 완전 초기화

```python
# 로직 흐름
1. delete_api_keys() 호출
2. api_credentials.json 삭제
3. encryption_key.key 삭제
4. 메모리에서 self.fernet = None
5. 시나리오 1 상태로 복귀
```

### 시나리오 5: 오류 복구 상태 (Error Recovery) ⚠️ **현재 상황**
**상황**: 암호화 키와 자격증명이 호환되지 않는 상태

```python
# 파일 상태 (현재)
encryption_key.key: ✅ 존재 (키 A)
api_credentials.json: ✅ 존재 (키 B로 암호화됨)

# 문제점
- 복호화 시도 → cryptography.fernet.InvalidToken 에러
- load_api_keys() → None, None, False 반환
- UI에서 "키가 없다"고 표시

# 복구 방법
1. 두 파일 모두 삭제 (시나리오 4)
2. 새로 입력받아 저장 (시나리오 1)
```

---

## 🔧 PyQt6 보안 입력 시스템 구현

### 1. 보안 입력 위젯 설정
```python
# upbit_auto_trading/ui/desktop/screens/settings/api_key_manager_secure.py
class SecureApiKeyInputWidget(QWidget):
    def setup_secure_inputs(self):
        # Access Key 입력
        self.access_key_input = QLineEdit()
        self.access_key_input.setEchoMode(QLineEdit.EchoMode.Normal)

        # Secret Key 보안 입력
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.secret_key_input.setInputMethodHints(
            Qt.InputMethodHint.ImhHiddenText |
            Qt.InputMethodHint.ImhSensitiveData
        )
```

### 2. 데이터 바인딩 및 검증
```python
# 저장 로직
def save_api_keys(self):
    access_key = self.access_key_input.text().strip()
    secret_key = self.secret_key_input.text().strip()
    trade_permission = self.trade_permission_checkbox.isChecked()

    # Infrastructure Layer 서비스 호출
    success = self.api_key_service.save_api_keys(
        access_key, secret_key, trade_permission
    )
```

### 3. UI 상태 관리
```python
def update_ui_state(self):
    """API 키 존재 여부에 따른 UI 상태 업데이트"""
    has_keys = self.api_key_service.has_valid_keys()

    if has_keys:
        access_key, secret_key, trade_perm = self.api_key_service.load_api_keys()
        if access_key:  # 복호화 성공
            self.access_key_input.setText(access_key)
            # Secret Key는 마스킹 처리
            mask_length = self.api_key_service.get_secret_key_mask_length()
            self.secret_key_input.setText("*" * mask_length)
```

---

## 🗃️ 데이터베이스 vs 파일 시스템 검토

### 질문: "암호화 키를 DB에 저장하는 방법을 사용했나요?"

**답변**: 아니오, 현재는 파일 시스템을 사용합니다.

#### 현재 구현 (파일 시스템)
```python
# 경로: config/secure/encryption_key.key
encryption_key_path = self.paths.SECURE_DIR / "encryption_key.key"
with open(encryption_key_path, "wb") as key_file:
    key_file.write(key)
```

#### DB 저장 방식 (미구현)
```python
# 가능한 DB 저장 방식 (현재 사용 안함)
# settings.sqlite3의 secure_keys 테이블에 저장
INSERT INTO secure_keys (key_type, encrypted_value)
VALUES ('encryption_key', ?)
```

#### 현재 파일 시스템 사용 이유
1. **분리된 보안**: DB 백업과 암호화 키를 분리
2. **간단한 관리**: 파일 삭제로 완전 초기화 가능
3. **성능**: DB 연결 없이 빠른 키 액세스

---

## 🛠️ 즉시 해결 방법

### 방법 1: 완전 초기화 (권장)
```powershell
# 1. 현재 키 파일들 삭제
Remove-Item "config\secure\encryption_key.key" -Force
Remove-Item "config\secure\api_credentials.json" -Force

# 2. 프로그램 재시작
python run_desktop_ui.py

# 3. API 키 탭에서 새로 입력 및 저장
```

### 방법 2: 프로그래밍 방식 복구
```python
# API 키 서비스를 통한 완전 초기화
service = ApiKeyService()
service.delete_api_keys()  # 모든 키 파일 삭제
```

### 방법 3: 디버깅 모드 실행
```python
# 에러 상세 정보 확인
import logging
logging.basicConfig(level=logging.DEBUG)

service = ApiKeyService()
try:
    keys = service.load_api_keys()
except Exception as e:
    print(f"복호화 에러: {e}")
```

---

## 📊 구현 품질 평가

### ✅ 잘 구현된 부분
1. **보안 아키텍처**: Fernet 암호화, 메모리 정리, 파일 분리
2. **에러 처리**: 예외 상황에 대한 안전한 처리
3. **로깅 시스템**: Infrastructure Layer 로깅으로 추적 가능
4. **DDD 준수**: Infrastructure Layer 서비스로 적절히 분리

### ⚠️ 개선 필요 부분
1. **키 호환성 검증**: 암호화키-자격증명 매칭 검증 로직 필요
2. **마이그레이션 지원**: 기존 데이터 복구 기능 없음
3. **UI 에러 표시**: 복호화 실패 시 명확한 에러 메시지 필요
4. **백업/복구**: 자격증명 백업 및 복구 기능 부재

### 🔄 권장 개선사항
1. **호환성 체크**: 로드 시 복호화 테스트 후 UI 업데이트
2. **에러 분류**: 파일 없음 vs 복호화 실패 구분
3. **자동 복구**: 불일치 감지 시 사용자에게 재설정 안내
4. **검증 로직**: 저장 후 즉시 로드하여 성공 여부 확인

---

## 🚨 보안 취약점 발견 (2025-08-07 추가)

### 치명적 보안 문제: "All-in-One" 파일 시스템
**현재 상태**: 암호화 키와 자격증명이 동일 폴더에 저장
```
config/secure/
├── encryption_key.key    # 🔑 암호화 키 (평문)
└── api_credentials.json  # 🔒 암호화된 자격증명
```

**위험도**: 🔴 **CRITICAL**
- 두 파일을 모두 획득하면 즉시 복호화 가능
- 백업/클라우드 동기화 시 전체 보안 정보 노출
- 물리적 접근 시 완전한 자격증명 탈취 가능

### 🛡️ 보안 강화 제안: DB 기반 하이브리드 아키텍처

#### 새로운 분리 저장 구조 (권장)
```
📁 파일 시스템 (백업 대상)
└── config/secure/
    └── api_credentials.json  # 🔒 암호화된 자격증명

🗃️ 데이터베이스 (로컬 전용)
└── settings.sqlite3
    └── secure_keys 테이블
        └── encryption_key    # 🔑 암호화 키 (DB 내부)
```

#### 보안 강화 효과
| 공격 벡터 | 현재 위험도 | 개선 후 | 위험도 감소 |
|-----------|-------------|---------|-------------|
| 백업 유출 | 🔴 CRITICAL | 🟢 LOW | **80%** |
| 물리적 접근 | 🔴 HIGH | 🟡 MEDIUM | **50%** |
| 부분 탈취 | 🔴 HIGH | 🟢 LOW | **70%** |

**상세 분석**: `API_KEY_SECURITY_IMPROVEMENT_PROPOSAL_20250807.md` 참조

---

## 🎯 최종 권장사항 (업데이트)

### 즉시 실행할 조치
1. **현재 파일 삭제**: 불일치 상태 해결 ✅ **완료**
2. **새로 설정**: API 키 재입력 및 저장
3. **동작 확인**: 저장→로드→표시 전체 사이클 테스트

### 🔐 보안 개선 과제 (우선순위)
1. **🔴 긴급**: DB 기반 암호화 키 저장으로 전환
2. **🟡 중요**: 호환성 검증 로직 추가
3. **🟢 일반**: 에러 메시지 개선
4. **🟢 일반**: 자동 복구 시스템 구현

### 🚀 다음 단계
**Phase 1**: DB 기반 암호화 키 관리 시스템 구현
**Phase 2**: 파일 초기화 후 새로운 API 키 설정 테스트

**🚀 다음 단계**: 파일 초기화 후 새로운 API 키 설정 테스트
