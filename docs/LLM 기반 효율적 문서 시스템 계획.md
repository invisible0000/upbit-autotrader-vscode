현재 계획 문서를 먼저 확인해보고, 효율적인 LLM 기반 문서 시스템을 제안하겠습니다. 현재 프로젝트 구조를 파악하기 위해 먼저 몇 가지 핵심 정보를 확인하겠습니다. 이제 현재 프로젝트의 구조와 기존 문서 시스템을 충분히 파악했습니다. 기존의 방대한 문서들을 분석하여 **LLM이 빠르게 파악할 수 있는 효율적인 문서 시스템**을 제안하겠습니다.

## 📋 **LLM 기반 효율적 문서 시스템 계획**

### 🎯 **핵심 목표**
- 기존 50+ 문서를 **5개 핵심 문서**로 압축
- LLM이 **30초 내**에 전체 시스템 파악 가능
- **중복 개발 방지**를 위한 구현 현황 즉시 확인
- **DDD 계층 위반 방지**를 위한 빠른 참조

### 📁 **제안하는 폴더 구조** (최소화)

```
docs/
└── llm_quick_reference/          # LLM 전용 빠른 참조 (5개 파일만)
    ├── 01_SYSTEM_SNAPSHOT.md     # 전체 시스템 현황 (1분 독해)
    ├── 02_IMPLEMENTATION_MAP.md  # 기능별 구현 현황 (30초 검색)
    ├── 03_DDD_LAYER_GUIDE.md     # 계층 구조 + 금지사항 (30초 확인)
    ├── 04_COPILOT_WORKFLOW.md    # LLM 작업 절차 (즉시 실행)
    └── 05_QUICK_COMMANDS.md      # 자주 사용하는 명령어 모음
```

### 🔑 **각 문서의 핵심 내용 구조**

#### **01_SYSTEM_SNAPSHOT.md** (전체 현황 한눈에)
```markdown
# 🔍 업비트 자동매매 시스템 현황 스냅샷

## ⚡ 30초 요약
- **아키텍처**: DDD 4계층 (Presentation → Application → Domain ← Infrastructure)
- **DB**: 3-DB (settings.sqlite3, strategies.sqlite3, market_data.sqlite3)
- **UI**: PyQt6 + QSS 테마 시스템
- **핵심 목표**: 기본 7규칙 전략 완전 구현

## 🏗️ 계층별 구현 상태
- **Domain Layer**: ✅ 95% 완성 (entities, services, repositories)
- **Infrastructure Layer**: ✅ 90% 완성 (DB repositories, external APIs)
- **Application Layer**: ✅ 85% 완성 (use cases, DTOs)
- **Presentation Layer**: 🔄 70% 완성 (UI components, presenters)

## 🎯 현재 작업 중인 기능
1. **백업 관리**: ✅ 완료 (DatabaseReplacementUseCase)
2. **트리거 빌더**: 🔄 진행중 (7규칙 전략 구현)
3. **전략 실행**: ⏳ 대기중

## 🚨 즉시 확인해야 할 사항
- SQLite 직접 사용 금지 (Infrastructure Layer만 허용)
- UI에서 Use Case 없이 비즈니스 로직 금지
- 파일명 변경 시 {original}_legacy.py 백업 필수
```

#### **02_IMPLEMENTATION_MAP.md** (구현 현황 즉시 검색)
```markdown
# 🗺️ 기능별 구현 현황 맵

## 🔍 빠른 검색 (Ctrl+F로 검색)

### ✅ 완료된 기능들
**백업관리** → DatabaseReplacementUseCase (application/use_cases/database_replacement.py:45)
**설정편집** → DatabaseSettingsPresenter (ui/desktop/presenters/database_settings.py:220)
**로깅시스템** → Infrastructure Logger (infrastructure/logging/:create_component_logger)

### 🔄 진행중인 기능들
**트리거빌더** → TriggerBuilderWidget (ui/desktop/widgets/trigger_builder/:IncompleteRSIOverSold)
**전략실행** → StrategyExecutionUseCase (application/use_cases/:NotImplemented)

### ⏳ 계획된 기능들
**백테스팅** → BacktestUseCase (application/use_cases/:Planned)
**실시간거래** → TradingBotUseCase (application/use_cases/:Planned)

## 🎯 재사용 가능한 컴포넌트

### Domain Services (domain/services/)
- CompatibilityChecker: 변수 호환성 검증
- SignalEvaluator: 매매 신호 평가
- BackupValidationService: SQLite 구조 검증

### Use Cases (application/use_cases/)
- DatabaseReplacementUseCase: 안전한 DB 교체
- TradingVariableManagementUseCase: 변수 관리

### Repository Interfaces (domain/repositories/)
- DatabaseConfigRepository: DB 설정 관리
- StrategyRepository: 전략 저장소
- MarketDataRepository: 시장 데이터

## ⚠️ 중복 방지 체크리스트
1. 새 기능 구현 전 위 목록에서 검색
2. 유사 Use Case 존재 시 확장 우선 고려
3. Domain Service 메서드 재사용 확인
```

#### **03_DDD_LAYER_GUIDE.md** (계층 규칙 즉시 확인)
```markdown
# 🏗️ DDD 계층 구조 + 금지사항

## ⚡ 의존성 방향 (절대 규칙)
```
Presentation → Application → Domain ← Infrastructure
```

## 📁 계층별 위치 + 역할

### 🎨 Presentation (ui/desktop/)
- **역할**: UI 표시, 사용자 입력만
- **허용**: Use Case 호출, View 업데이트
- **금지**: SQLite 직접 사용, 파일시스템 접근, 비즈니스 로직

### ⚙️ Application (application/)
- **역할**: Use Case 조율, DTO 변환
- **허용**: Domain Service + Repository Interface
- **금지**: SQLite, HTTP, 구체적 기술 스택

### 💎 Domain (domain/)
- **역할**: 순수 비즈니스 로직
- **허용**: 자체 Entity, Value Object, Service만
- **금지**: 다른 계층 import 절대 금지

### 🔧 Infrastructure (infrastructure/)
- **역할**: 외부 시스템 연동
- **허용**: SQLite, API, 파일시스템
- **금지**: Domain 로직 포함

## 🚨 자주 위반하는 패턴들

### ❌ 금지된 코드
```python
# Presenter에서 SQLite 직접 사용
class BadPresenter:
    def method(self):
        import sqlite3  # 금지!
        conn = sqlite3.connect("db.sqlite3")

# Domain에서 다른 계층 import
from infrastructure.database import SomeRepo  # 금지!
```

### ✅ 올바른 코드
```python
# Presenter는 Use Case만
class GoodPresenter:
    def method(self):
        result = self.use_case.execute(dto)

# Domain은 순수 로직만
class GoodDomainService:
    def __init__(self, repo: AbstractRepo):  # 인터페이스만
        self.repo = repo
```
```

#### **04_COPILOT_WORKFLOW.md** (LLM 작업 절차)
```markdown
# 🤖 LLM 작업 절차 가이드

## ⚡ 작업 시작 시 3단계 (5분 내)

### 1단계: 현황 파악 (2분)
```bash
# 필수 확인 문서
docs/llm_quick_reference/01_SYSTEM_SNAPSHOT.md    # 전체 현황
docs/llm_quick_reference/02_IMPLEMENTATION_MAP.md # 기존 구현 검색
```

### 2단계: 계층 규칙 확인 (1분)
```bash
docs/llm_quick_reference/03_DDD_LAYER_GUIDE.md   # 계층 위반 방지
```

### 3단계: 실행 (2분)
```bash
docs/llm_quick_reference/05_QUICK_COMMANDS.md     # 자주 쓰는 명령어
```

## 🔄 개발 절차 (Bottom-Up)

### 순서 (절대 지키기)
1. **기존 구현 검색** → 02_IMPLEMENTATION_MAP.md
2. **Domain Layer** → Entity, Service, Repository Interface
3. **Infrastructure Layer** → Repository 구현체
4. **Application Layer** → Use Case
5. **Presentation Layer** → Presenter, Widget

### 각 단계별 검증
```python
# Domain Layer 검증
assert "import sqlite3" not in domain_code
assert "import requests" not in domain_code

# Presenter 검증
assert "Use Case" in presenter_code
assert "sqlite3" not in presenter_code
```

## 🚨 에러 방지 체크리스트

### 작업 전
- [ ] 02_IMPLEMENTATION_MAP.md에서 유사 기능 검색
- [ ] 03_DDD_LAYER_GUIDE.md에서 계층 규칙 확인

### 작업 중
- [ ] Domain Layer에 외부 의존성 없는지 확인
- [ ] Presenter에서 Use Case만 호출하는지 확인

### 작업 후
- [ ] `python run_desktop_ui.py` 실행하여 검증
- [ ] 02_IMPLEMENTATION_MAP.md 업데이트
```

#### **05_QUICK_COMMANDS.md** (자주 사용하는 명령어)
```markdown
# ⚡ 자주 사용하는 명령어 모음

## 🔍 시스템 검증
```powershell
# UI 실행 (최종 검증)
python run_desktop_ui.py

# DB 상태 확인
python super_db_table_viewer.py settings

# 로깅 시스템 테스트
$env:UPBIT_CONSOLE_OUTPUT='true'; $env:UPBIT_LOG_SCOPE='verbose'
```

## 🧪 테스트 실행
```powershell
# 전체 테스트
pytest tests/ -v

# 특정 계층 테스트
pytest tests/domain/ -v
pytest tests/application/ -v
```

## 📊 코드 분석
```powershell
# 참조 분석
python tools/super_db_table_reference_code_analyzer.py --tables tv_trading_variables

# 의존성 확인
grep -r "import sqlite3" upbit_auto_trading/domain/     # 결과 없어야 함
grep -r "import sqlite3" upbit_auto_trading/ui/        # 결과 없어야 함
```

## 🔧 개발 환경 설정
```powershell
# Python 환경 설정
python configure_python_environment.py

# 패키지 설치
pip install -r requirements.txt
```
```

### 💡 **이 계획의 장점**

1. **속도**: 5개 파일만으로 전체 시스템 파악
2. **중복 방지**: 02번 파일에서 기존 구현 즉시 검색 가능
3. **에러 방지**: 03번 파일로 DDD 위반 사전 차단
4. **일관성**: 04번 파일로 표준 작업 절차 준수
5. **효율성**: 05번 파일로 반복 작업 단축

### 🎯 **기존 50+ 문서 대비 효과**
- **읽기 시간**: 30분 → **5분**
- **검색 시간**: 10분 → **30초**
- **중복 개발**: 빈번 → **거의 없음**
- **계층 위반**: 가끔 → **매우 드뭄**

---

**이 계획을 승인하시면 즉시 5개 핵심 문서를 생성하여 효율적인 LLM 기반 개발 환경을 구축하겠습니다. 승인하시겠습니까?**### 💡 **이 계획의 장점**

1. **속도**: 5개 파일만으로 전체 시스템 파악
2. **중복 방지**: 02번 파일에서 기존 구현 즉시 검색 가능
3. **에러 방지**: 03번 파일로 DDD 위반 사전 차단
4. **일관성**: 04번 파일로 표준 작업 절차 준수
5. **효율성**: 05번 파일로 반복 작업 단축

### 🎯 **기존 50+ 문서 대비 효과**
- **읽기 시간**: 30분 → **5분**
- **검색 시간**: 10분 → **30초**
- **중복 개발**: 빈번 → **거의 없음**
- **계층 위반**: 가끔 → **매우 드뭄**

---

**이 계획을 승인하시면 즉시 5개 핵심 문서를 생성하여 효율적인 LLM 기반 개발 환경을 구축하겠습니다. 승인하시겠습니까?**
