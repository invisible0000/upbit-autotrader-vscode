# 🤖 DDD 기반 업비트 자동매매 시스템 개발 시 반드시 지켜야 할 핵심 규칙

## 🚨 작업 중 꼭 지켜야 할 내용

### 1. 절대 원칙 (Golden Rules)

#### 기본 7규칙 전략 검증 (최우선)
**모든 개발은 기본 7규칙 전략 완전 구현을 최종 목표로 합니다.**
- RSI 과매도 진입, 수익시 불타기, 계획된 익절, 트레일링 스탑, 하락시 물타기, 급락 감지, 급등 감지
- **검증 명령**: `python run_desktop_ui.py` → 전략 관리 → 트리거 빌더에서 7규칙 구성 가능해야 함

#### PowerShell 전용 (Windows 환경)
```powershell
# ✅ 필수 사용
cmd1; cmd2                    # 명령어 연결
Get-ChildItem                 # 디렉토리 목록
$env:VAR = "value"           # 환경 변수
```

#### 3-DB 아키텍처 (절대 변경 금지)
- `data/settings.sqlite3`: 변수 정의, 파라미터 (data_info/*.yaml로 관리)
- `data/strategies.sqlite3`: 사용자 전략, 백테스팅 결과
- `data/market_data.sqlite3`: 시장 데이터, 지표 캐시

#### Infrastructure 로깅 시스템 (필수 사용)
```python
# 표준 로깅 사용법
from upbit_auto_trading.infrastructure.logging import create_component_logger
logger = create_component_logger("ComponentName")

# 환경변수 제어
$env:UPBIT_CONSOLE_OUTPUT='true'           # 콘솔 출력
$env:UPBIT_LOG_SCOPE='verbose'             # 로그 레벨 제어
$env:UPBIT_COMPONENT_FOCUS='ComponentName' # 특정 컴포넌트 집중
```

#### 파일명 일관성 유지 (필수 규칙)
**기존 기능을 교체할 시 파일명 연속성을 유지합니다.**
- 기존 파일을 `{original_name}_legacy.py` 또는 `{original_name}_backup.py`로 백업
- 새 구현체는 **원래 파일명을 그대로 사용**
- 임시 파일명 (`simple_`, `new_`, `temp_` 등) 사용 금지
- 파일명 변경으로 인한 import 경로 혼란 방지
- **파일 전체 재생성 시**: 기존 파일을 무조건 백업한 후 동일 이름으로 새 파일 생성

### 2. DDD 아키텍처 준수

#### 4계층 구조 엄격 준수
- **Presentation Layer**: PyQt6 UI (표시만, Passive View)
- **Application Layer**: Use Case 구현, Service 계층
- **Domain Layer**: 핵심 비즈니스 로직, Entity, Value Object
- **Infrastructure Layer**: 외부 연동, Repository 구현

#### 의존성 방향 (절대 위반 금지)
- Presentation → Application → Domain ← Infrastructure
- Domain Layer는 다른 계층에 의존하지 않음
- 모든 외부 의존성은 Infrastructure Layer로 격리

### 3. UI 개발 필수 규칙

#### 전역 스타일 관리 시스템 (절대 원칙)
**모든 UI는 upbit_auto_trading/ui/desktop/common/styles에서 중앙 관리됩니다.**
```python
# ✅ DDD+MVP 패턴에서 전역 스타일 사용 (필수)
from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager

# View Layer (MVP Passive View)
class EnvironmentProfileView(QWidget):
    def __init__(self):
        # 기본 QWidget 스타일 활용 (전역 테마 자동 적용)
        self.main_splitter = QSplitter()  # 전역 QSplitter 스타일

        # 특수한 경우에만 objectName 설정
        button.setObjectName("quick_env_button_development")  # 환경별 색상 필요시만
```

**전역 스타일 디렉토리 구조:**
```
upbit_auto_trading/ui/desktop/common/styles/
├── style_manager.py          # 중앙 스타일 관리자
├── default_style.qss         # 기본 라이트 테마
├── dark_style.qss           # 다크 테마
└── [component]_styles.qss   # 컴포넌트별 확장 스타일 (최소화)
```

**DDD+MVP 패턴 스타일 적용 원칙:**
- **View Layer**: 기본 Qt 위젯 스타일 최대 활용
- **Widget Components**: 표준 objectName 컨벤션 준수
- **Presenter Layer**: 스타일링 관여 금지 (비즈니스 로직만)
- **Individual QSS**: 절대 금지 (전역 시스템 일관성 보장)

#### QSS 테마 시스템 (하드코딩 금지)
```python
# ✅ 올바른 방법 (DDD+MVP 패턴)
widget.setObjectName("특정_위젯명")  # QSS 선택자용

# ❌ 절대 금지: 하드코딩된 스타일
widget.setStyleSheet("background-color: white;")  # 테마 무시
widget.setStyleSheet("color: #333333;")           # 고정 색상

# ✅ matplotlib 차트 테마 적용 (필수)
from upbit_auto_trading.ui.desktop.common.theme_notifier import apply_matplotlib_theme_simple
apply_matplotlib_theme_simple()  # 차트 그리기 전 반드시 호출
```

#### 스타일 통일성 보장 원칙
1. **중앙 집중 관리**: 모든 스타일은 common/styles에서 관리
2. **테마 일괄 변환**: 라이트/다크 테마 자동 전환 지원
3. **컴포넌트 확장**: 개별 컴포넌트는 전역 스타일을 확장만 가능
4. **objectName 표준화**: 표준 네이밍 컨벤션 준수 필수

#### 변수 호환성 3중 카테고리 검증
- **purpose_category**: trend, momentum, volatility, volume, price
- **chart_category**: overlay, subplot
- **comparison_group**: price_comparable, percentage_comparable, zero_centered
- **규칙**: 같은 comparison_group만 직접 비교 가능

---

## ❌ 하면 안되는 행위

### 1. 에러 처리 금지사항 (폴백 코드 절대 금지)

#### Domain Layer 에러 숨김 금지
```python
# ❌ 절대 금지: 에러 숨김
try:
    from domain.services import SomeService
except ImportError:
    class SomeService: pass  # 폴백으로 에러 숨김

# ✅ 필수: 에러 즉시 노출
from domain.services import SomeService  # 실패 시 즉시 ModuleNotFoundError
```

#### Business Logic 폴백 금지
```python
# ❌ 금지: Domain Rule 위반 무시
try:
    self._validate_rule_compatibility(rule)
    self._rules.append(rule)
except DomainRuleViolationError:
    pass  # 호환성 문제 무시 - 위험!

# ✅ 필수: Domain Exception 명확히 전파
self._validate_rule_compatibility(rule)  # 실패 시 즉시 Exception
self._rules.append(rule)
```

### 2. UI 스타일링 금지사항

#### UI 스타일링 금지사항

#### 하드코딩된 스타일 금지 (전역 스타일 위반)
```python
# ❌ 금지: 하드코딩된 색상 (전역 테마 시스템 무시)
widget.setStyleSheet("background-color: white;")
widget.setStyleSheet("background-color: #2c2c2c;")
widget.setStyleSheet("color: #333333;")

# ❌ 금지: 컴포넌트별 개별 QSS 파일 생성
# styles/my_component.qss  # 전역 관리 원칙 위반

# ✅ 필수: 전역 스타일 시스템 사용
widget.setObjectName("standard_button")  # 표준 objectName
# common/styles/에서 중앙 관리되는 스타일 적용

# ❌ 금지: 하드코딩된 차트 색상
ax.plot(data, color='blue')  # 테마 무시
ax.set_facecolor('white')    # 고정 배경색
```

#### DDD+MVP 패턴 스타일링 위반 금지
```python
# ❌ 금지: Presenter에서 스타일링 관여
class EnvironmentProfilePresenter:
    def update_view_style(self):
        self.view.setStyleSheet("...")  # Presenter는 비즈니스 로직만!

# ❌ 금지: View에서 개별 스타일 파일 로드
class EnvironmentProfileView(QWidget):
    def __init__(self):
        self.load_custom_styles()  # 전역 시스템 무시

# ✅ 필수: View는 기본 Qt 위젯 스타일 활용
class EnvironmentProfileView(QWidget):
    def __init__(self):
        self.main_splitter = QSplitter()  # 전역 QSplitter 스타일 자동 적용
```

#### Qt 미지원 CSS 속성 금지
```python
# ❌ 금지: Qt에서 지원하지 않는 속성
setStyleSheet("cursor: not-allowed;")  # Qt 미지원
setStyleSheet("box-shadow: 0 2px 4px rgba(0,0,0,0.1);")  # 브라우저용
```

### 3. 레거시 참조 금지

#### 폐기된 DB/파일 참조 금지
- `app_settings.sqlite3` 언급 금지 (현재는 settings.sqlite3 사용)
- `*.db` 확장자 파일 언급 금지 (현재는 *.sqlite3 사용)
- `component_system` 폴더 참조 금지 (존재하지 않음)

#### Unix/Linux 명령어 사용 금지
```bash
# ❌ 금지: Unix/Linux 명령어
cmd1 && cmd2
ls -la
export VAR=value
grep pattern file
```

---

## 💡 개발 조언

### 1. 개발 워크플로우

#### 작업 전 필수 확인
1. **기존 코드 분석**: 새 코드 작성 전 기존 코드베이스 충분히 분석
2. **DB 상태 확인**: 제공된 도구로 현재 DB 상태 파악
3. **Infrastructure 로깅**: 표준 로깅 시스템으로 실시간 모니터링

#### 개발 중 실시간 확인
```python
# Infrastructure 로깅으로 진행상황 추적
logger = create_component_logger("Development")
logger.info("개발 단계 시작")
logger.debug("상세 진행상황")  # 자동 필터링으로 제어됨
```

### 2. 성능 최적화 팁

#### DB 분석 도구 활용
```powershell
# DB 상태 확인
python tools/super_db_table_viewer.py settings

# 코드 참조 분석
python tools/super_db_table_reference_code_analyzer.py --tables tv_trading_variables
```

#### 메모리 및 UI 최적화
- **지연 로딩**: 보이지 않는 탭은 필요시에만 로드
- **캐싱**: 차트 데이터와 계산 결과 캐싱
- **이벤트 해제**: 위젯 삭제 시 이벤트 연결 해제

### 3. 에러 처리 모범 사례

#### 명확한 에러 메시지 제공
```python
# ✅ 구체적인 에러 메시지
if not config.get('entry_strategy'):
    raise ValidationError("진입 전략이 설정되지 않았습니다")

# ✅ Infrastructure 로깅과 함께
logger.error(f"❌ 트레이딩 변수 로드 실패: {e}")
raise TradingVariableError("변수 정의를 불러올 수 없습니다") from e
```

### 4. 코드 품질 유지

#### 기본 원칙
- **PEP 8 준수**: 79자 제한, 타입 힌트 필수
- **단일 책임**: 함수는 20줄 이하, 하나의 명확한 목적
- **의미있는 이름**: 축약어 없이 명확한 변수/함수명

#### 테스트 우선 개발
```python
# 단위 테스트 필수 작성
def test_strategy_creation():
    strategy = create_basic_7_rule_strategy()
    assert strategy.validate()
    assert len(strategy.rules) == 7
```
### 5. 최종 체크리스트 및 알림

#### 코드 생성 전 확인 사항:
-   [ ] **TASK 체크박스:** 작업 시작 시 `[ ]` → `[-]` 마킹했는가?
-   [ ] **코드박스 삭제:** 해당 단계의 예시 코드박스를 모두 삭제했는가?
-   [ ] **접근 전략:** 코드 작성 전 `🧠 접근 전략` 템플릿으로 계획을 제시했는가?
-   [ ] **기존 코드 분석:** 새 코드 작성 전 기존 코드베이스를 충분히 분석했는가?
-   [ ] **환경:** 내 명령어들이 PowerShell 구문인가?
-   [ ] **아키텍처:** 컴포넌트 기반 설계를 존중하고 있는가?
-   [ ] **데이터베이스:** 표준 경로와 연결 패턴을 사용하고 있는가?
-   [ ] **보안:** API 키는 환경 변수로 처리되는가? SQL 인젝션을 방지하고 있는가?
-   [ ] **로깅:** Infrastructure Layer 로깅 시스템을 사용하고 있는가?
-   [ ] **테스트:** 내 기능에 대한 `pytest` 테스트를 포함하고 있는가?
-   [ ] **작업 로그:** 완료 후 `📌 작업 로그` 템플릿으로 상세 기록할 예정인가?
-   [ ] **체크박스 완료:** 작업 완료 후 `[-]` → `[X]` 마킹할 예정인가?
-   [ ] **호환성:** 변수 호환성 규칙을 강제하고 있는가?
-   [ ] **자가 수정:** 내 초안에서 최소 3가지 약점을 식별하고 수정했는가?

**모든 개발 작업의 최종 행동은 `python run_desktop_ui.py`를 실행하여 무결성을 검증하는 것입니다.**

---

## 📚 참조 문서

### 핵심 통합 문서 (3개)
1. **CORE_ARCHITECTURE**: 시스템 아키텍처, DDD 설계, 에러 처리, DB 스키마
2. **UI_THEME_SYSTEM**: PyQt6 UI 개발, QSS 테마, 트리거 빌더, 호환성 시스템
3. **OPERATIONAL_SYSTEM**: 전략 시스템, 로깅 v4.0, 7규칙 전략, 기여 가이드

### 특정 작업별 문서
- **PROJECT_SPECIFICATIONS**: 프로젝트 전체 명세
- **DEV_CHECKLIST**: 개발 검증 체크리스트
- **STYLE_GUIDE**: 코딩 스타일 가이드
- **DDD_UBIQUITOUS_LANGUAGE_DICTIONARY**: DDD 용어 통일 사전
- **BASIC_7_RULE_STRATEGY_GUIDE**: 7규칙 전략 상세 가이드
- **TRIGGER_BUILDER_GUIDE**: 트리거 빌더 시스템 상세
- **VARIABLE_COMPATIBILITY**: 변수 호환성 검증 시스템
- **STRATEGY_SYSTEM**: 매매 전략 시스템 상세
- **COMPONENT_ARCHITECTURE**: DDD 컴포넌트 아키텍처
- **ERROR_HANDLING_POLICY**: 에러 처리 정책
- **DB_SCHEMA**: 데이터베이스 스키마 명세
- **UI_DESIGN_SYSTEM**: UI 디자인 시스템
- **LOGGING_REFACTORING_COMPLETE_REPORT**: 로깅 시스템 가이드
- **CONTRIBUTING**: 기여 가이드
- **LLM_AGENT_TASK_GUIDELINES**: LLM 에이전트 TASK 작업 가이드

---

**🎯 성공 기준**: 기본 7규칙 전략이 완벽하게 동작하는 시스템!
**💡 핵심**: 의심스러우면 7규칙 전략으로 검증, DDD 원칙 준수, 에러 투명성 유지!
