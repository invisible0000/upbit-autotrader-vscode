# 🚀 DB 마이그레이션 시스템 사용법

## 📋 **빠른 시작 가이드**

### 🆘 **긴급상황 (원클릭 초기화)**
```bash
# 백테스트 결과 보존하며 초기화
python tools/db_cleanup_tool.py --safe-reset

# 모든 데이터 삭제하고 완전 초기화  
python tools/db_cleanup_tool.py --quick-reset --force
```

### 🔍 **현재 상태 확인**
```bash
# 테이블 형식으로 분석 결과 출력
python tools/db_cleanup_tool.py --analyze

# JSON 형식으로 상세 분석
python tools/db_cleanup_tool.py --analyze --report-format json
```

### 🎯 **안전한 스키마 업그레이드**
```bash
# 백업과 함께 최신 스키마로 업그레이드
python tools/db_cleanup_tool.py --reset-to-latest --backup-name "before_v2_upgrade"

# 특정 스키마 버전 적용
python tools/db_cleanup_tool.py --apply-schema v2.0-strategy-combination
```

### 🧙‍♂️ **대화형 도구 사용**
```bash
# 사용자 친화적인 마이그레이션 도우미
python tools/migration_wizard.py
```

---

## 🛠️ **주요 명령어**

| 명령어 | 설명 | 위험도 |
|--------|------|--------|
| `--analyze` | 현재 DB 상태 분석 | 🟢 안전 |
| `--list-versions` | 스키마 버전 목록 | 🟢 안전 |
| `--safe-reset` | 백테스트 보존 초기화 | 🟡 주의 |
| `--reset-to-latest` | 최신 스키마 적용 | 🟠 위험 |
| `--quick-reset` | 완전 초기화 | 🔴 매우위험 |

---

## 📊 **상황별 사용법**

### 🎯 **기획 변경 후 깨끗한 시작**
```bash
# 1. 현재 상태 백업
python tools/db_cleanup_tool.py --analyze --report-format json > db_state_before.json

# 2. 백업 생성 후 초기화
python tools/db_cleanup_tool.py --reset-to-latest --backup-name "before_new_feature"

# 3. 결과 확인
python tools/db_cleanup_tool.py --analyze
```

### 🐛 **DB 오류 발생 시 긴급 복구**
```bash
# 1. 상태 진단
python tools/db_cleanup_tool.py --analyze

# 2. 문제가 있으면 안전 초기화
python tools/db_cleanup_tool.py --safe-reset

# 3. 대화형 도구로 세부 작업
python tools/migration_wizard.py
```

### 🔄 **개발 환경별 DB 초기화**
```bash
# 개발 환경 (빠른 초기화)
python tools/db_cleanup_tool.py --quick-reset --force

# 테스트 환경 (백테스트 보존)  
python tools/db_cleanup_tool.py --safe-reset

# 프로덕션 환경 (신중한 마이그레이션)
python tools/migration_wizard.py
```

---

## 🔧 **고급 옵션**

### 🧪 **Dry Run (실제 실행 없이 미리보기)**
```bash
# 실제로 실행하지 않고 수행할 작업만 확인
python tools/db_cleanup_tool.py --reset-to-latest --dry-run
```

### 📦 **백업 관리**
```bash
# 사용자 정의 백업 이름
python tools/db_cleanup_tool.py --reset-to-latest --backup-name "feature_xyz_backup"

# 백업 생성 건너뛰기 (위험!)
python tools/db_cleanup_tool.py --quick-reset --skip-backup --force
```

### 📝 **상세 로깅**
```bash
# 상세한 실행 과정 출력
python tools/db_cleanup_tool.py --analyze --verbose

# 확인 없이 강제 실행
python tools/db_cleanup_tool.py --quick-reset --force
```

---

## ⚠️ **주의사항 및 안전 수칙**

### 🛡️ **안전 수칙**
1. **항상 백업 먼저**: 중요한 작업 전에는 반드시 백업 생성
2. **Dry Run 활용**: `--dry-run` 옵션으로 미리 확인
3. **단계적 진행**: 한 번에 모든 것을 바꾸지 말고 단계별로 진행
4. **테스트 환경 먼저**: 프로덕션 적용 전 테스트 환경에서 검증

### ⚠️ **주의사항**
- `--quick-reset`은 모든 데이터를 삭제합니다
- `--skip-backup`은 복구 불가능한 상황을 만들 수 있습니다
- `--force` 옵션은 확인 절차를 건너뜁니다

### 🚨 **긴급상황 복구**
만약 실수로 데이터를 삭제했다면:
1. 당황하지 말고 작업 중단
2. `data/` 폴더의 백업 파일 확인
3. 백업 매니저를 통한 복구 시도
4. 복구 불가능시 이전 Git 커밋에서 데이터 복원

---

## 📈 **성능 최적화 팁**

### ⚡ **빠른 실행**
```bash
# 소용량 DB 빠른 분석
python tools/db_cleanup_tool.py --analyze --report-format json | jq '.schema_version'

# 백업 없이 빠른 초기화 (개발용)
python tools/db_cleanup_tool.py --quick-reset --skip-backup --force
```

### 💾 **용량 절약**
```bash
# 분석 후 불필요한 테이블 정리
python tools/db_cleanup_tool.py --analyze
# → 빈 테이블들 확인 후 수동 정리
```

---

## 🎯 **실제 사용 시나리오**

### 📋 **시나리오 1: 새로운 전략 조합 기능 개발**
```bash
# Before: 기존 DB 백업
python tools/db_cleanup_tool.py --analyze > current_state.txt
python tools/db_cleanup_tool.py --reset-to-latest --backup-name "before_strategy_combination"

# After: 검증
python tools/db_cleanup_tool.py --analyze
```

### 📋 **시나리오 2: 개발 중 DB 꼬임 현상**
```bash
# 1. 문제 진단
python tools/db_cleanup_tool.py --analyze --verbose

# 2. 대화형 도구로 안전하게 처리
python tools/migration_wizard.py
# → "2. 긴급 DB 초기화" → "1. 안전 초기화" 선택
```

### 📋 **시나리오 3: 정기적인 DB 정리**
```bash
# 매주 정기 백업 및 상태 체크
python tools/db_cleanup_tool.py --analyze --report-format json > weekly_report_$(date +%Y%m%d).json

# 필요시 최적화
python tools/migration_wizard.py
```

---

## 🔗 **관련 파일들**

```
🗂️ DB 마이그레이션 시스템
├── 📁 upbit_auto_trading/data_layer/storage/
│   ├── 🔧 db_cleanup_manager.py          # 핵심 정리 로직
│   ├── 🗄️ migration_manager.py           # 기존 마이그레이션 관리자  
│   └── 💾 backup_manager.py              # 백업 관리자
├── 📁 upbit_auto_trading/data_layer/migrations/
│   └── 📁 schema_definitions/
│       └── 📋 version_registry.py         # 스키마 버전 관리
├── 📁 tools/
│   ├── ⚡ db_cleanup_tool.py             # CLI 도구
│   └── 🧙‍♂️ migration_wizard.py            # 대화형 도우미
└── 📁 docs/
    └── 📖 DB_MIGRATION_AND_CLEANUP_PLAN.md  # 전체 계획서
```

---

> **💡 핵심**: 기획이 바뀌거나 DB에 문제가 생겼을 때, **5분 내에 깨끗한 상태**로 돌아갈 수 있는 것이 목표!

**🎯 다음 단계**: 이 시스템을 실제로 테스트해보고 필요한 부분을 보완해나가세요!
