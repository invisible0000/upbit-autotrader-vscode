현재까지의 경험을 바탕으로 DDD/MVP 아키텍처에서 코파일럿이 연속성을 유지하며 개발할 수 있는 개발문서 시스템을 체계적으로 정리하겠습니다.

## 📚 DDD 기반 개발문서 시스템 구성 계획

### 🎯 목표
- 복잡한 4계층 DDD 아키텍처에서 기능 추적 어려움 해결
- 기존 구현 발견 어려움으로 인한 중복 개발 방지
- 계층간 의존성 위반(SQLite 직접 사용 등) 방지
- 코파일럿의 연속성 있는 개발 지원

### 📁 제안하는 폴더 구조

```
docs/
├── architecture/
│   ├── DDD_LAYER_MAP.md              # 계층별 파일 매핑 (핵심)
│   ├── FEATURE_IMPLEMENTATION_MAP.md  # 기능별 구현 현황 (핵심)
│   ├── DEPENDENCY_GRAPH.md           # 의존성 그래프
│   └── ARCHITECTURE_OVERVIEW.md      # 전체 아키텍처 개요
├── features/
│   ├── backup_management/
│   │   ├── FEATURE_OVERVIEW.md       # 기능 개요
│   │   ├── IMPLEMENTATION_STATUS.md  # 구현 상태
│   │   ├── LAYER_MAPPING.md          # 4계층별 파일 위치
│   │   ├── API_CONTRACTS.md          # 인터페이스 계약
│   │   └── TESTING_STATUS.md         # 테스트 현황
│   ├── database_settings/
│   ├── trading_strategies/
│   ├── api_key_management/
│   └── _template/                    # 신규 기능용 템플릿
├── quick_reference/
│   ├── USE_CASE_DIRECTORY.md         # Use Case 전체 목록
│   ├── REPOSITORY_DIRECTORY.md       # Repository 구현체 목록
│   ├── SERVICE_DIRECTORY.md          # Domain Service 목록
│   ├── PRESENTER_DIRECTORY.md        # Presenter 목록
│   └── DTO_DIRECTORY.md              # DTO 클래스 목록
├── development_guides/
│   ├── NEW_FEATURE_CHECKLIST.md      # 신규 기능 개발 체크리스트
│   ├── DDD_COMPLIANCE_GUIDE.md       # DDD 준수 가이드
│   ├── LAYER_VIOLATION_PREVENTION.md # 계층 위반 방지 가이드
│   ├── TESTING_STRATEGY.md           # TDD 테스트 전략
│   └── COPILOT_WORKFLOW.md           # 코파일럿 작업 흐름
└── status/
    ├── CURRENT_ISSUES.md             # 현재 알려진 문제들
    ├── TECH_DEBT.md                  # 기술 부채 목록
    └── RECENT_CHANGES.md             # 최근 변경사항 로그
```

### 🔑 핵심 문서 내용 구조

#### 1. `FEATURE_IMPLEMENTATION_MAP.md` (최우선)
```markdown
# 기능별 구현 현황 매핑

## 🔍 빠른 검색 가이드
- **백업 관리**: ✅ 완료 → 라인 67-89
- **설정 편집**: 🔄 진행중 → 라인 112-134
- **API 키 관리**: ✅ 완료 → 라인 156-178

---

## 📦 백업 관리 기능
- **상태**: ✅ 완료 (2025-08-09)
- **핵심 Use Case**: `DatabaseReplacementUseCase`
- **Domain Service**: `DatabaseBackupService`
- **Repository**: `DatabaseConfigRepository`
- **Presenter**: `DatabaseSettingsPresenter` (L649: update_backup_description)
- **View**: `DatabaseBackupWidget`

### 주요 메서드 위치
```python
# 백업 생성
DatabaseSettingsPresenter.create_database_backup()  # L220
# 백업 목록
DatabaseSettingsPresenter.get_backup_list()        # L156
# 백업 삭제
DatabaseSettingsPresenter.delete_database_backup()  # L385
# 설명 편집
DatabaseSettingsPresenter.update_backup_description() # L649
# 파일 검증 (DDD 준수)
DatabaseBackupService._verify_sqlite_structure()    # Domain Layer
```

### DDD 준수 상태
- ✅ SQLite 직접 사용 제거됨
- ✅ Domain Service 통해서만 DB 검증
- ✅ Use Case를 통한 안전한 백업/복원
- ⚠️ 메타데이터 저장은 JSON 파일 (향후 Repository로 이전 고려)

### 테스트 현황
- ❌ 단위 테스트 없음 (TDD 적용 필요)
- ✅ 수동 테스트 완료 (백업 생성/삭제/편집)
```

#### 2. `DDD_LAYER_MAP.md`
```markdown
# DDD 계층별 파일 매핑

## 🚨 계층 의존성 규칙 (절대 위반 금지)
```
Presentation → Application → Domain ← Infrastructure
     ↓              ↓            ↑           ↑
   View/MVP     Use Cases    Business    Repository
                              Logic       Impl
```

## 📁 Presentation Layer
- 위치: `upbit_auto_trading/ui/desktop/`
- 역할: UI 표시, 사용자 입력 처리
- **금지사항**: SQLite 직접 사용, 파일시스템 직접 접근

```python
# ✅ 올바른 Presenter 패턴
class DatabaseSettingsPresenter:
    def create_backup(self, db_type: str):
        # Use Case 호출만
        result = self.replacement_use_case.execute_backup(...)

# ❌ 금지된 패턴
class BadPresenter:
    def create_backup(self, db_type: str):
        import sqlite3  # 금지!
        conn = sqlite3.connect(...)  # 계층 위반!
```

## 🏢 Application Layer
- 위치: `upbit_auto_trading/application/use_cases/`
- 역할: 비즈니스 워크플로우 조정
- **의존성**: Domain Service + Repository Interface만

## 🧠 Domain Layer
- 위치: `upbit_auto_trading/domain/`
- 역할: 순수 비즈니스 로직
- **금지사항**: 다른 계층 import 절대 금지

## 🔧 Infrastructure Layer
- 위치: `upbit_auto_trading/infrastructure/`
- 역할: 외부 시스템 연동 (DB, API, 파일시스템)
```

#### 3. `NEW_FEATURE_CHECKLIST.md`
```markdown
# 신규 기능 개발 체크리스트

## 🔍 개발 시작 전 (중복 방지)
- [ ] `FEATURE_IMPLEMENTATION_MAP.md`에서 유사 기능 검색
- [ ] `USE_CASE_DIRECTORY.md`에서 재사용 가능한 Use Case 확인
- [ ] `SERVICE_DIRECTORY.md`에서 Domain Service 메서드 확인
- [ ] 기존 구현체에서 패턴 학습

## 🏗️ DDD 계층 구현 순서 (Bottom-Up)
1. [ ] **Domain Layer**: Entity, Value Object, Domain Service
2. [ ] **Domain Layer**: Repository Interface 정의
3. [ ] **Infrastructure Layer**: Repository 구현체
4. [ ] **Application Layer**: Use Case 구현
5. [ ] **Presentation Layer**: Presenter, View, Widget

## 📋 각 계층별 검증 포인트

### Domain Layer 체크포인트
- [ ] `import` 문에 다른 계층 의존성 없음
- [ ] 순수한 비즈니스 로직만 포함
- [ ] SQLite, HTTP, 파일시스템 등 기술적 세부사항 배제
- [ ] Domain Service는 Repository Interface만 의존

### Application Layer 체크포인트
- [ ] Domain Service와 Repository Interface만 의존
- [ ] DTO를 통한 계층간 데이터 전달
- [ ] Use Case별 단일 책임 원칙 준수
- [ ] 트랜잭션 경계 명확히 정의

### Infrastructure Layer 체크포인트
- [ ] Repository Interface 구현
- [ ] SQLite, 파일시스템 등 기술적 세부사항 캡슐화
- [ ] Domain Entity ↔ DB Record 매핑 처리

### Presentation Layer 체크포인트
- [ ] Application Layer Use Case만 호출
- [ ] SQLite, 파일시스템 직접 접근 절대 금지
- [ ] View Interface를 통한 UI 업데이트
- [ ] Presenter에서 비즈니스 로직 금지

## 🧪 TDD 테스트 체크포인트
- [ ] Domain Service 단위 테스트
- [ ] Use Case 통합 테스트
- [ ] Repository 구현체 테스트
- [ ] Presenter Mock 테스트

## 📝 문서화 체크포인트
- [ ] `FEATURE_IMPLEMENTATION_MAP.md` 업데이트
- [ ] 해당 기능 폴더에 상세 문서 작성
- [ ] Quick Reference 디렉토리들 업데이트
```

#### 4. `COPILOT_WORKFLOW.md`
```markdown
# 코파일럿 작업 흐름 가이드

## 🎯 코파일럿이 개발 시작 시 반드시 확인할 문서들

### 1순위 (필수)
1. `FEATURE_IMPLEMENTATION_MAP.md` - 기존 구현 확인
2. `DDD_LAYER_MAP.md` - 계층 구조 파악
3. `NEW_FEATURE_CHECKLIST.md` - 개발 절차 확인

### 2순위 (참고)
4. 해당 기능의 `/features/{기능명}/` 폴더
5. `USE_CASE_DIRECTORY.md` - 재사용 가능한 로직
6. `LAYER_VIOLATION_PREVENTION.md` - 금지사항

## 🚫 코파일럿이 절대 하면 안되는 행동

### 계층 위반 금지
```python
# ❌ Presenter에서 SQLite 직접 사용 (절대 금지)
class BadPresenter:
    def method(self):
        import sqlite3
        conn = sqlite3.connect("db.sqlite3")

# ✅ 올바른 패턴 - Use Case 활용
class GoodPresenter:
    def method(self):
        result = self.use_case.execute(request_dto)
```

### 파일 구조 변경 금지
- 기존 파일명 변경 금지 (import 경로 혼란 방지)
- 대신 `{original}_legacy.py`로 백업 후 동일 파일명 사용

### 중복 구현 금지
- 새 기능 구현 전 반드시 기존 구현 검색
- 유사 로직 발견 시 재사용 우선 고려

## 📋 코파일럿 표준 작업 절차

### 1단계: 현황 파악
```bash
# 1. 기능 구현 현황 확인
docs/architecture/FEATURE_IMPLEMENTATION_MAP.md 검토

# 2. 유사 기능 검색
docs/features/ 폴더 내 관련 문서 확인

# 3. 계층별 파일 위치 파악
docs/architecture/DDD_LAYER_MAP.md 참조
```

### 2단계: 구현 계획
```bash
# 1. 체크리스트 기반 계획 수립
docs/development_guides/NEW_FEATURE_CHECKLIST.md 활용

# 2. DDD 순서 준수 확인
Domain → Infrastructure → Application → Presentation
```

### 3단계: 구현 및 검증
```bash
# 1. 각 계층별 체크포인트 확인
# 2. 계층 위반 검증
# 3. 테스트 작성 (TDD)
```

### 4단계: 문서 업데이트
```bash
# 1. FEATURE_IMPLEMENTATION_MAP.md 업데이트
# 2. 관련 Quick Reference 업데이트
# 3. 기능별 상세 문서 작성
```
```

### 🚀 다음 세션 액션 플랜

1. **문서 시스템 구축** (1단계)
   - `docs/` 폴더 구조 생성
   - 핵심 문서 4개 우선 작성 (FEATURE_IMPLEMENTATION_MAP, DDD_LAYER_MAP, NEW_FEATURE_CHECKLIST, COPILOT_WORKFLOW)

2. **현재 구현 현황 정리** (2단계)
   - 백업 관리 기능 완전 문서화
   - 다른 기능들 현황 조사 및 정리

3. **템플릿 및 가이드 완성** (3단계)
   - 신규 기능 개발 템플릿 제작
   - 계층 위반 방지 자동 체크 가이드

4. **실전 테스트** (4단계)
   - 새로운 기능을 문서 시스템 기반으로 개발
   - 코파일럿 연속성 검증

이 계획을 통해 다음 세션에서는 체계적인 문서 시스템을 구축하고, DDD 아키텍처에서 코파일럿이 일관성 있게 개발할 수 있는 환경을 만들어보겠습니다!### 🚀 다음 세션 액션 플랜

1. **문서 시스템 구축** (1단계)
   - `docs/` 폴더 구조 생성
   - 핵심 문서 4개 우선 작성 (FEATURE_IMPLEMENTATION_MAP, DDD_LAYER_MAP, NEW_FEATURE_CHECKLIST, COPILOT_WORKFLOW)

2. **현재 구현 현황 정리** (2단계)
   - 백업 관리 기능 완전 문서화
   - 다른 기능들 현황 조사 및 정리

3. **템플릿 및 가이드 완성** (3단계)
   - 신규 기능 개발 템플릿 제작
   - 계층 위반 방지 자동 체크 가이드

4. **실전 테스트** (4단계)
   - 새로운 기능을 문서 시스템 기반으로 개발
   - 코파일럿 연속성 검증

이 계획을 통해 다음 세션에서는 체계적인 문서 시스템을 구축하고, DDD 아키텍처에서 코파일럿이 일관성 있게 개발할 수 있는 환경을 만들어보겠습니다!
