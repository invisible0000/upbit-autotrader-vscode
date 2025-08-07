# 🤖 LLM 에이전트 작업 인수인계 가이드

## 🎯 핵심 개념: DDD 기반 업비트 자동매매 시스템

### 📋 필수 확인사항 (30초 체크)
```bash
# 1. 환경 확인
python run_desktop_ui.py  # 시스템 무결성 검증

# 2. DB 상태 확인
python tools/super_db_table_viewer.py settings

# 3. 로깅 환경변수 설정 (Windows PowerShell 전용)
$env:UPBIT_CONSOLE_OUTPUT='true'
$env:UPBIT_LOG_SCOPE='verbose'
```

## 🔄 현재 진행 상황 (Task 시리즈)

### ✅ 완료된 Task들
- **Task 1.3**: 스마트 삭제 로직 (13개 테스트 PASS)
- **Task 1.4.1**: 깔끔한 재생성 로직 (5개 테스트 PASS)

### 📍 핵심 구현체들
```python
# Task 1.3: 스마트 삭제
api_service.delete_api_keys_smart(confirm_callback)

# Task 1.4: 깔끔한 재생성 (Task 1.3 로직 재사용)
api_service.save_api_keys_clean(access, secret, confirm_callback)
```

---

## 🏗️ DDD 아키텍처 핵심 패턴

### 4계층 구조 (절대 위반 금지)
```
Presentation → Application → Domain ← Infrastructure
```

### Infrastructure Layer 핵심 클래스들

#### 1. 로깅 시스템 (모든 코드에서 필수)
```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
logger = create_component_logger("ComponentName")
logger.info("✅ 작업 완료")
```

#### 2. Repository Container (데이터 액세스 통합)
```python
from upbit_auto_trading.infrastructure.repositories.repository_container import RepositoryContainer

# 초기화
repo_container = RepositoryContainer()
secure_keys_repo = repo_container.get_secure_keys_repository()

# 종료 시 필수
repo_container.close_all_connections()
```

#### 3. API Key Service (보안 키 관리)
```python
from upbit_auto_trading.infrastructure.services.api_key_service import ApiKeyService

# 초기화
api_service = ApiKeyService(secure_keys_repo)

# 핵심 메서드들
success, message = api_service.save_api_keys_clean(access, secret, confirm_callback)
access, secret, permission = api_service.load_api_keys()
result_message = api_service.delete_api_keys_smart(confirm_callback)
```

---

## 📊 3-DB 아키텍처 (절대 변경 금지)

### DB 파일들
- `data/settings.sqlite3`: 변수 정의, 파라미터 (data_info/*.yaml로 관리)
- `data/strategies.sqlite3`: 사용자 전략, 백테스팅 결과
- `data/market_data.sqlite3`: 시장 데이터, 지표 캐시

### Repository 패턴 사용법
```python
# SecureKeysRepository 예시
if secure_keys_repo.key_exists("encryption"):
    key = secure_keys_repo.get_key("encryption")
    secure_keys_repo.delete_key("encryption")

secure_keys_repo.save_key("encryption", new_key)
```

---

## 🧪 테스트 작성 패턴

### Infrastructure 테스트 클래스 템플릿
```python
class TestYourFeature:
    def __init__(self):
        # 로깅 초기화
        self.logger = create_component_logger("Test-YourFeature")

        # Repository Container
        self.repo_container = RepositoryContainer()
        self.secure_keys_repo = self.repo_container.get_secure_keys_repository()

        # Services
        self.api_service = ApiKeyService(self.secure_keys_repo)

        # Mock 콜백 시스템
        self._confirm_responses = []
        self._confirm_calls = []

    def _mock_confirm_callback(self, message: str, details: str) -> bool:
        self._confirm_calls.append((message, details))
        return self._confirm_responses.pop(0) if self._confirm_responses else True

    def teardown_method(self):
        self.repo_container.close_all_connections()
```

### 테스트 실행 패턴
```python
def test_your_feature(self):
    # 콜백 히스토리 초기화 (테스트마다 필수!)
    self._confirm_calls = []
    self._confirm_responses = []

    # 테스트 데이터 정리
    try:
        self.secure_keys_repo.delete_key("encryption")
    except Exception:
        pass

    # 실제 테스트 로직
    # ...
```

---

## 🧪 최근 Task 1.4.1: 깔끔한 재생성 로직 테스트

### 핵심 테스트 클래스 사용법
```python
# tests/infrastructure/services/test_clean_regeneration.py
class TestCleanRegeneration:
    """깔끔한 재생성 로직 테스트 - 완전 구현됨"""

    def test_clean_regeneration_flow(self):
        """기본 삭제→생성 흐름 ✅"""

    def test_regeneration_with_no_existing_data(self):
        """초기 상태에서 생성 ✅"""

    def test_regeneration_reuses_deletion_logic(self):
        """Task 1.3 로직 재사용 검증 ✅"""

    def test_regeneration_with_user_cancel(self):
        """사용자 취소 시나리오 ✅"""

    def test_regeneration_error_handling(self):
        """에러 처리 테스트 ✅"""

# 실행 명령
python "tests/infrastructure/services/test_clean_regeneration.py"
```

### ApiKeyService.save_api_keys_clean() 핵심 동작
```python
# 스마트 재생성: Task 1.3 삭제 로직 재사용
success, message = api_service.save_api_keys_clean(
    access_key, secret_key, confirm_callback
)

# 동작 원리:
# 1. 기존 데이터 체크 → 2. 사용자 확인 → 3. 스마트 삭제 → 4. 새 키 생성
# 기존 데이터 없으면 확인 콜백 호출 안함 (정상 설계)
```

---

## 🎮 UI 개발 핵심 규칙

### QSS 테마 시스템 (하드코딩 금지)
```python
# ✅ 올바른 방법
widget.setObjectName("특정_위젯명")  # QSS 선택자용

# ✅ matplotlib 차트 테마 적용 (필수)
from upbit_auto_trading.ui.desktop.common.theme_notifier import apply_matplotlib_theme_simple
apply_matplotlib_theme_simple()  # 차트 그리기 전 반드시 호출
```

### 변수 호환성 검증 (3중 카테고리)
- **purpose_category**: trend, momentum, volatility, volume, price
- **chart_category**: overlay, subplot
- **comparison_group**: price_comparable, percentage_comparable, zero_centered

---

## 🚨 절대 금지사항

### 1. 에러 숨김 금지
```python
# ❌ 절대 금지
try:
    from domain.services import SomeService
except ImportError:
    class SomeService: pass  # 폴백으로 에러 숨김

# ✅ 필수: 에러 즉시 노출
from domain.services import SomeService  # 실패 시 즉시 ModuleNotFoundError
```

### 2. 하드코딩된 스타일 금지
```python
# ❌ 금지
widget.setStyleSheet("background-color: white;")
ax.plot(data, color='blue')

# ✅ QSS 테마 시스템 사용
widget.setObjectName("data_chart")  # QSS에서 스타일링
```

### 3. PowerShell 전용 (Windows)
```powershell
# ✅ 필수 사용
cmd1; cmd2                    # 명령어 연결
Get-ChildItem                 # 디렉토리 목록
$env:VAR = "value"           # 환경 변수

# ❌ 금지: Unix/Linux 명령어
cmd1 && cmd2
ls -la
export VAR=value
```

---

## 🎯 최종 검증 명령

```powershell
# 모든 작업 완료 후 필수 실행
python run_desktop_ui.py
```

**성공 기준**: 전략 관리 → 트리거 빌더에서 기본 7규칙 전략 구성 가능

---

## 📚 상세 문서 참조

- **CORE_ARCHITECTURE**: 시스템 아키텍처, DDD 설계
- **UI_THEME_SYSTEM**: PyQt6 UI 개발, QSS 테마
- **OPERATIONAL_SYSTEM**: 전략 시스템, 로깅, 7규칙 전략
- **BASIC_7_RULE_STRATEGY_GUIDE**: 7규칙 전략 상세
- **COMPONENT_ARCHITECTURE**: DDD 컴포넌트 아키텍처

---

## 🔄 작업 인수인계 체크리스트

- [ ] 로깅 시스템 이해 (`create_component_logger`)
- [ ] Repository Container 패턴 이해
- [ ] API Key Service 핵심 메서드 파악
- [ ] 3-DB 아키텍처 구조 확인
- [ ] 테스트 작성 패턴 숙지
- [ ] PowerShell 환경 설정 확인
- [ ] QSS 테마 시스템 이해
- [ ] 절대 금지사항 숙지
- [ ] `python run_desktop_ui.py` 최종 검증

**💡 핵심 원칙**: 의심스러우면 7규칙 전략으로 검증, DDD 원칙 준수, 에러 투명성 유지!
