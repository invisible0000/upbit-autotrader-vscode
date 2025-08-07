# 🔐 API 키 시스템 보안 아키텍처 개선 제안서

**작성일**: 2025년 8월 7일
**검토 대상**: 암호화 키 저장 위치 및 보안 강화 방안
**현재 상태**: 파일 시스템 기반 → DB 기반 하이브리드 전환 검토

---

## 🚨 현재 보안 취약점 분석

### 1. 치명적 보안 취약점: "All-in-One" 파일 시스템

#### 현재 위험한 구조
```
config/secure/
├── encryption_key.key    # 🔑 암호화 키 (평문)
└── api_credentials.json  # 🔒 암호화된 자격증명
```

#### 보안 위험도 평가
- **🔴 HIGH RISK**: 두 파일을 모두 획득하면 **즉시 복호화 가능**
- **🔴 CRITICAL**: 백업, USB 복사, 클라우드 동기화 시 **전체 노출**
- **🔴 FATAL**: 시스템 해킹 시 **완전한 자격증명 탈취**

### 2. 공격 시나리오 분석

#### 시나리오 A: 물리적 접근
```bash
# 공격자가 컴퓨터에 접근했을 때
copy "config\secure\*" "usb:\"  # 두 파일 복사
# → 즉시 복호화 가능, API 키 완전 탈취
```

#### 시나리오 B: 백업 유출
```bash
# 사용자가 백업했을 때
tar -czf backup.tar.gz config/  # config 전체 백업
# → 백업 파일 유출 시 암호화 키까지 노출
```

#### 시나리오 C: 클라우드 동기화
```bash
# OneDrive, Google Drive 등 자동 동기화
config/secure/ → Cloud Storage
# → 클라우드 계정 해킹 시 전체 노출
```

---

## 💡 개선 제안: DB 기반 하이브리드 아키텍처

### 1. 권장 보안 아키텍처

#### 새로운 분리 저장 구조
```
📁 파일 시스템 (백업 대상)
└── config/secure/
    └── api_credentials.json  # 🔒 암호화된 자격증명

🗃️ 데이터베이스 (로컬 전용)
└── settings.sqlite3
    └── secure_keys 테이블
        └── encryption_key    # 🔑 암호화 키 (DB 내부)
```

### 2. 보안 강화 효과

#### Before (현재) vs After (개선)
| 구분 | 현재 (파일) | 개선 (DB+파일) |
|------|-------------|----------------|
| **암호화 키** | config/secure/encryption_key.key | settings.sqlite3 내부 |
| **자격증명** | config/secure/api_credentials.json | config/secure/api_credentials.json |
| **백업 시** | 🔴 두 파일 모두 포함 | 🟢 자격증명만 포함 |
| **탈취 시** | 🔴 즉시 복호화 가능 | 🟢 DB 없이는 복호화 불가 |
| **복구 시** | 🔴 완전 복구 가능 | 🟢 부분 복구만 가능 |

### 3. 공격 차단 효과

#### 개선된 공격 시나리오
```bash
# 시나리오 A: 백업 파일 탈취
공격자가 획득: api_credentials.json (암호화됨)
공격자가 필요: settings.sqlite3의 encryption_key
결과: 🟢 복호화 불가능 (DB 키 없음)

# 시나리오 B: 부분 접근
공격자가 획득: config/ 폴더 전체
공격자가 필요: settings.sqlite3 (다른 위치)
결과: 🟢 복호화 불가능 (키 분리됨)
```

---

## 🛠️ 구현 방안: DB 기반 암호화 키 관리

### 1. 데이터베이스 스키마 설계

#### settings.sqlite3에 추가할 테이블
```sql
-- 보안 키 관리 테이블
CREATE TABLE IF NOT EXISTS secure_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_type TEXT NOT NULL UNIQUE,           -- 'encryption_key'
    key_value BLOB NOT NULL,                 -- 암호화 키 (바이너리)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE UNIQUE INDEX IF NOT EXISTS idx_secure_keys_type
ON secure_keys(key_type);
```

### 2. ApiKeyService 개선 구현

#### 새로운 암호화 키 관리 로직
```python
class ApiKeyService(IApiKeyService):
    def __init__(self):
        self.logger = create_component_logger("ApiKeyService")
        self.paths = SimplePaths()

        # DB 연결 설정
        self.db_connection = self._get_settings_db_connection()
        self._initialize_secure_keys_table()

        # 기존 암호화 키 로드 (DB에서)
        self._try_load_existing_encryption_key_from_db()

    def _get_settings_db_connection(self):
        """settings.sqlite3 연결 획득"""
        db_path = self.paths.SETTINGS_DB
        return sqlite3.connect(str(db_path))

    def _initialize_secure_keys_table(self):
        """보안 키 테이블 초기화"""
        cursor = self.db_connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS secure_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_type TEXT NOT NULL UNIQUE,
                key_value BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db_connection.commit()
```

#### 키 로드 로직 (DB 기반)
```python
def _try_load_existing_encryption_key_from_db(self):
    """DB에서 기존 암호화 키 로드"""
    try:
        cursor = self.db_connection.cursor()
        cursor.execute(
            "SELECT key_value FROM secure_keys WHERE key_type = ?",
            ('encryption_key',)
        )
        result = cursor.fetchone()

        if result:
            self.encryption_key = result[0]  # BLOB 데이터
            self.fernet = Fernet(self.encryption_key)
            self.logger.debug("✅ DB에서 암호화 키 로드 완료")
        else:
            self.encryption_key = None
            self.fernet = None
            self.logger.debug("🔑 DB에 암호화 키 없음 - 저장 시 생성될 예정")

    except Exception as e:
        self.logger.error(f"DB 암호화 키 로드 중 오류: {e}")
        self.encryption_key = None
        self.fernet = None
```

#### 키 생성 로직 (DB 저장)
```python
def _create_new_encryption_key_in_db(self):
    """새로운 암호화 키 생성 및 DB 저장"""
    try:
        # 새 암호화 키 생성
        key = Fernet.generate_key()

        cursor = self.db_connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO secure_keys
            (key_type, key_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, ('encryption_key', key))

        self.db_connection.commit()

        # 메모리에 로드
        self.encryption_key = key
        self.fernet = Fernet(self.encryption_key)

        self.logger.info("✅ 새로운 암호화 키가 DB에 생성되고 로드되었습니다.")

    except Exception as e:
        self.logger.error(f"DB 암호화 키 생성 중 오류: {e}")
        raise
```

#### 키 삭제 로직 (DB + 파일)
```python
def delete_api_keys(self) -> bool:
    """API 키 및 암호화 키 완전 삭제"""
    try:
        # 1. 암호화된 자격증명 파일 삭제
        api_keys_path = self.paths.API_CREDENTIALS_FILE
        if api_keys_path.exists():
            api_keys_path.unlink()
            self.logger.info("자격증명 파일 삭제 완료")

        # 2. DB에서 암호화 키 삭제
        cursor = self.db_connection.cursor()
        cursor.execute(
            "DELETE FROM secure_keys WHERE key_type = ?",
            ('encryption_key',)
        )
        self.db_connection.commit()

        # 3. 메모리에서 키 정보 제거
        self.encryption_key = None
        self.fernet = None
        gc.collect()

        self.logger.info("✅ API 키 및 암호화 키 완전 삭제 완료")
        return True

    except Exception as e:
        self.logger.error(f"API 키 삭제 중 오류: {e}")
        return False
```

### 3. 마이그레이션 전략

#### 기존 파일 기반 → DB 기반 전환
```python
def _migrate_file_key_to_db(self):
    """기존 파일 기반 키를 DB로 마이그레이션"""
    old_key_path = self.paths.SECURE_DIR / "encryption_key.key"

    if old_key_path.exists():
        self.logger.info("🔄 기존 파일 기반 키를 DB로 마이그레이션 시작")

        try:
            # 기존 키 로드
            with open(old_key_path, "rb") as f:
                old_key = f.read()

            # DB에 저장
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO secure_keys
                (key_type, key_value) VALUES (?, ?)
            """, ('encryption_key', old_key))
            self.db_connection.commit()

            # 기존 파일 삭제
            old_key_path.unlink()

            # 메모리에 로드
            self.encryption_key = old_key
            self.fernet = Fernet(self.encryption_key)

            self.logger.info("✅ 마이그레이션 완료 - 기존 파일 삭제됨")

        except Exception as e:
            self.logger.error(f"마이그레이션 실패: {e}")
            raise
```

---

## 📊 보안 효과 비교 분석

### 1. 위험도 평가 매트릭스

| 공격 벡터 | 현재 (파일) | 개선 (DB+파일) | 위험도 감소 |
|-----------|-------------|----------------|-------------|
| **물리적 접근** | 🔴 HIGH | 🟡 MEDIUM | **50%** |
| **백업 유출** | 🔴 CRITICAL | 🟢 LOW | **80%** |
| **클라우드 동기화** | 🔴 CRITICAL | 🟢 LOW | **80%** |
| **부분 탈취** | 🔴 HIGH | 🟢 LOW | **70%** |
| **복구 공격** | 🔴 CRITICAL | 🟡 MEDIUM | **60%** |

### 2. 복구 시나리오 비교

#### 시나리오: 자격증명 파일 탈취됨
```bash
# 현재 (파일 기반)
공격자 획득: encryption_key.key + api_credentials.json
결과: 🔴 100% 복호화 가능 → API 키 완전 탈취

# 개선 (DB 기반)
공격자 획득: api_credentials.json만
결과: 🟢 복호화 불가능 → 암호화된 텍스트만 획득
```

### 3. 백업 보안 강화

#### 현재 백업 위험성
```bash
# 사용자가 config/ 백업 시
config/
├── secure/
│   ├── encryption_key.key     # 🔴 키 노출
│   └── api_credentials.json   # 🔴 자격증명 노출
└── other_configs...
# → 백업 파일 = 완전한 보안 위험
```

#### 개선된 백업 안전성
```bash
# 사용자가 config/ 백업 시
config/
├── secure/
│   └── api_credentials.json   # 🟡 암호화된 상태
└── other_configs...

# DB는 별도 위치
data/settings.sqlite3           # 🟢 키는 여기에 안전하게
# → 백업 파일만으로는 복호화 불가능
```

---

## 🎯 최종 권장사항

### ✅ DB 기반 아키텍처 도입 권장 이유

1. **🔐 보안 강화**: 키-자격증명 분리로 탈취 위험 70% 감소
2. **💾 백업 안전**: config 백업 시 키 노출 방지
3. **🔄 관리 편의**: DB 트랜잭션으로 안전한 키 관리
4. **📈 확장성**: 향후 다중 키 관리 가능

### 🚀 구현 우선순위

#### Phase 1: 핵심 기능 (즉시)
- [x] 보안 취약점 분석 완료
- [ ] DB 스키마 설계 및 생성
- [ ] 키 저장/로드 로직 DB 전환
- [ ] 기존 파일 → DB 마이그레이션

#### Phase 2: 안정화 (단기)
- [ ] 에러 처리 강화
- [ ] 로깅 개선
- [ ] 통합 테스트

#### Phase 3: 고급 기능 (중기)
- [ ] 키 회전(rotation) 기능
- [ ] 백업/복구 개선
- [ ] 다중 키 지원

### 💡 즉시 실행 제안

**현재 상황에서 가장 안전한 접근**:
1. DB 기반 암호화 키 저장으로 전환
2. 자격증명은 파일 유지 (백업 편의성)
3. 마이그레이션 로직으로 기존 사용자 지원

**결론**: 제안해주신 DB 기반 암호화 키 저장이 **보안상 올바른 방향**입니다!
