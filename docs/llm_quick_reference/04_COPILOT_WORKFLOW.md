# 🤖 LLM 작업 절차 가이드
*최종 업데이트: 2025년 8월 9일*

## ⚡ 작업 시작 시 3단계 (5분 내)

### 1단계: 현황 파악 (2분)
```bash
# 🔍 필수 확인 문서 (순서대로)
docs/llm_quick_reference/01_SYSTEM_SNAPSHOT.md    # 전체 현황
docs/llm_quick_reference/02_IMPLEMENTATION_MAP.md # 기존 구현 검색
```

**체크포인트:**
- [ ] 현재 계층별 구현 상태 확인 (Domain 95%, Infrastructure 90%, etc.)
- [ ] 내가 구현할 기능이 이미 있는지 02번 문서에서 `Ctrl+F` 검색
- [ ] 재사용 가능한 컴포넌트 목록 확인

### 2단계: 계층 규칙 확인 (1분)
```bash
docs/llm_quick_reference/03_DDD_LAYER_GUIDE.md   # 계층 위반 방지
```

**체크포인트:**
- [ ] 의존성 방향 확인: `Presentation → Application → Domain ← Infrastructure`
- [ ] 내가 작업할 계층의 허용/금지사항 확인
- [ ] 자주 위반하는 패턴들 미리 숙지

### 3단계: 실행 준비 (2분)
```bash
docs/llm_quick_reference/05_QUICK_COMMANDS.md     # 자주 쓰는 명령어
```

**체크포인트:**
- [ ] 필요한 검증 명령어 준비
- [ ] 로깅 환경변수 설정 확인
- [ ] 테스트 실행 방법 확인

---

## 🔄 개발 절차 (Bottom-Up 순서)

### 📋 개발 전 필수 검증
```python
# 1. 기존 구현 검색 (중복 방지)
# 02_IMPLEMENTATION_MAP.md에서 유사 기능 검색

# 2. 재사용 컴포넌트 확인
# Domain Services, Use Cases, Repository 재사용 가능성 확인

# 3. 계층 위반 방지
# 03_DDD_LAYER_GUIDE.md에서 내 계층의 금지사항 확인
```

### 🏗️ 구현 순서 (절대 지키기)
1. **Domain Layer** → Entity, Service, Repository Interface
2. **Infrastructure Layer** → Repository 구현체
3. **Application Layer** → Use Case
4. **Presentation Layer** → Presenter, Widget

### 🧪 각 단계별 검증
```python
# Domain Layer 검증
assert "import sqlite3" not in domain_code
assert "import requests" not in domain_code
assert "from PyQt6" not in domain_code

# Presenter 검증
assert "Use Case" in presenter_code
assert "sqlite3" not in presenter_code
assert ".execute(" in presenter_code  # Use Case 호출 확인
```

---

## 🚨 에러 방지 체크리스트

### 🔍 작업 전
- [ ] `02_IMPLEMENTATION_MAP.md`에서 유사 기능 검색했는가?
- [ ] `03_DDD_LAYER_GUIDE.md`에서 계층 규칙 확인했는가?
- [ ] 재사용 가능한 Domain Service가 있는가?
- [ ] Repository Interface가 이미 정의되어 있는가?

### 🛠️ 작업 중
- [ ] Domain Layer에 외부 의존성 없는가? (`grep -r "import sqlite3" domain/`)
- [ ] Presenter에서 Use Case만 호출하는가?
- [ ] Use Case에서 UI 직접 조작하지 않는가?
- [ ] Infrastructure 로깅 시스템 사용하는가? (`create_component_logger`)

### ✅ 작업 후
- [ ] `python run_desktop_ui.py` 실행하여 UI 무결성 검증
- [ ] 관련 pytest 테스트 실행하여 기능 검증
- [ ] `02_IMPLEMENTATION_MAP.md` 업데이트 (새 기능 추가)

---

## 💻 표준 코딩 패턴

### 🏗️ Infrastructure 로깅 사용 (필수)
```python
# ✅ 모든 컴포넌트에서 필수 사용
from upbit_auto_trading.infrastructure.logging import create_component_logger
logger = create_component_logger("ComponentName")

logger.info("✅ 작업 시작")
logger.warning("⚠️ 주의사항")
logger.error("❌ 오류 발생")
```

### 🎭 MVP 패턴 적용
```python
# ✅ Presenter 패턴
class GoodPresenter:
    def __init__(self, view, use_case):
        self.view = view
        self.use_case = use_case

    def handle_action(self):
        result = self.use_case.execute(dto)
        self.view.update_display(result)
```

### 🔧 Repository 패턴 사용
```python
# ✅ Use Case에서 Repository Interface 사용
class GoodUseCase:
    def __init__(self, repo: IStrategyRepository):
        self.repo = repo  # Interface만 의존

    def execute(self, request):
        entity = self.repo.find_by_id(request.id)
        # 비즈니스 로직
        self.repo.save(entity)
```

---

## 🎯 작업 완료 기준

### ✅ 최소 완료 조건
1. **기능 동작**: `python run_desktop_ui.py`에서 오류 없이 실행
2. **계층 준수**: Domain Layer에 외부 의존성 없음
3. **로깅 적용**: Infrastructure 로깅 시스템 사용
4. **문서 업데이트**: `02_IMPLEMENTATION_MAP.md`에 새 기능 추가

### 🌟 우수 완료 조건
1. **테스트 포함**: pytest 단위 테스트 작성
2. **재사용성**: 다른 기능에서 재사용 가능한 컴포넌트 설계
3. **성능 고려**: 불필요한 DB 접근이나 UI 업데이트 최소화
4. **에러 처리**: 예상 가능한 오류 상황에 대한 적절한 처리

---

## 🔧 자주 사용하는 검증 명령어

### 🔍 계층 위반 검사
```powershell
# Domain Layer 순수성 검증
grep -r "import sqlite3" upbit_auto_trading/domain/     # 결과 없어야 함
grep -r "import requests" upbit_auto_trading/domain/    # 결과 없어야 함
grep -r "from PyQt6" upbit_auto_trading/domain/         # 결과 없어야 함

# Presenter 순수성 검증
grep -r "sqlite3" upbit_auto_trading/ui/                # 결과 없어야 함
grep -r "sqlite3" upbit_auto_trading/presentation/      # 결과 없어야 함
```

### 🧪 기능 검증
```powershell
# UI 통합 검증 (최종 검증)
python run_desktop_ui.py

# 특정 계층 테스트
pytest tests/domain/ -v
pytest tests/application/ -v
pytest tests/infrastructure/ -v

# 로깅 시스템 테스트
$env:UPBIT_CONSOLE_OUTPUT='true'; $env:UPBIT_LOG_SCOPE='verbose'
```

---

## ⚠️ 자주 하는 실수들

### ❌ 하지 말아야 할 것들
1. **Domain에서 SQLite import** → Infrastructure Layer로 이동
2. **Presenter에서 복잡한 계산** → Use Case로 위임
3. **Use Case에서 UI 조작** → Presenter에서 처리
4. **기존 기능 재구현** → 02번 문서에서 재사용 가능한 것 찾기
5. **표준 로깅 무시** → `create_component_logger` 필수 사용

### ✅ 올바른 대응책
1. **기능 중복 발견** → 기존 컴포넌트 확장 우선 고려
2. **계층 위반 발견** → 해당 로직을 적절한 계층으로 이동
3. **복잡한 로직** → Domain Service로 분리
4. **UI 로직** → Presenter로 분리
5. **데이터 접근** → Repository Pattern 사용

---

## 🎯 성공하는 개발 마인드셋

### 💡 기본 원칙
- **중복 방지**: 구현 전 기존 코드 검색 필수
- **계층 준수**: 의심스러우면 Domain Layer 의존성 확인
- **점진적 개발**: Bottom-Up으로 안전하게 구현
- **테스트 우선**: 기능 구현과 함께 테스트 작성

### 🔥 핵심 기억사항
1. **Domain Layer가 다른 계층을 import하면 안됨** (절대 규칙!)
2. **02번 문서에서 재사용 가능한 컴포넌트 먼저 찾기**
3. **Infrastructure 로깅 시스템 필수 사용**
4. **최종엔 `python run_desktop_ui.py`로 검증**

---

**🚀 성공 공식**: 현황 파악 → 기존 코드 재사용 → 계층 규칙 준수 → 점진적 구현 → 통합 검증

**⚡ 빠른 시작**: 이 문서의 체크리스트만 따라도 80% 성공!
