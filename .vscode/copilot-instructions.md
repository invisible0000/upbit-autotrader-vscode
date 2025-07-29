# Upbit Auto Trading 프로젝트 - GitHub Copilot 지침

> **⚡ 빠른 참조**: DB는 `.sqlite3`, `data/` 폴더, 테스트는 `python run_desktop_ui.py`

## 🏠 개발 환경 (최우선 준수)
- **OS**: Windows 10/11
- **Shell**: PowerShell 5.1+ (기본)
- **IDE**: VS Code
- **Python**: 3.9+
- **❗ 중요**: 모든 터미널 명령어는 PowerShell 구문으로 작성

### Windows PowerShell 명령어 매핑 (필수 준수)
| ❌ 금지 (Unix/Linux) | ✅ 사용 (PowerShell) | 설명 |
|---------------------|---------------------|------|
| `command1 && command2` | `command1; command2` | 명령어 연결 |
| `cat file.txt` | `Get-Content file.txt` | 파일 내용 읽기 |
| `ls -la` | `Get-ChildItem` | 디렉토리 목록 |
| `ls *.py` | `Get-ChildItem *.py` | 파일 필터링 |
| `grep pattern file` | `Select-String pattern file` | 텍스트 검색 |
| `find . -name "*.py"` | `Get-ChildItem -Recurse -Filter "*.py"` | 파일 재귀 검색 |
| `export VAR=value` | `$env:VAR = "value"` | 환경변수 설정 |
| `which python` | `Get-Command python` | 명령어 경로 찾기 |

### PowerShell 명령어 예시
```powershell
# ✅ 올바른 PowerShell 구문
cd "d:\projects\upbit-autotrader-vscode"; python run_desktop_ui.py
Get-ChildItem -Path "upbit_auto_trading" -Recurse -Filter "*.py"
Get-Content "config.json" | Select-String "database"

# ❌ 금지된 Unix/Linux 구문  
cd /path/to/project && python run_desktop_ui.py
find upbit_auto_trading -name "*.py"
cat config.json | grep database
```

## 🎯 프로젝트 개요
## 🎯 프로젝트 개요
**upbit-autotrader-vscode**는 업비트 거래소를 위한 자동매매 시스템입니다.
- **언어**: Python 3.9+
- **UI 프레임워크**: PyQt6
- **데이터베이스**: SQLite3
- **아키텍처**: 컴포넌트 기반 모듈러 설계

## 📚 상세 가이드 참조
개발 전 반드시 아래 문서들을 확인하세요:

### 🎨 **스타일 가이드 (필수)**
- **코딩 스타일**: `.vscode/STYLE_GUIDE.md` ⭐ **반드시 준수**
  - UI/UX 테마 시스템 규칙
  - PyQt6 스타일링 가이드라인
  - matplotlib 차트 테마 적용 방법
  - 금지사항 및 권장사항
- **개발 체크리스트**: `.vscode/DEV_CHECKLIST.md` 📝 **커밋 전 확인**
- **프로젝트 명세**: `.vscode/project-specs.md` (243줄 - 비즈니스 로직)
- **README**: `.vscode/README.md` (프로젝트 개요)

### 🎯 전략 시스템 가이드 
- **진입 전략**: `.vscode/strategy/entry-strategies.md` (454줄 - 6개 진입 전략 상세)
- **관리 전략**: `.vscode/strategy/management-strategies.md` (관리 전략 구현)
- **조합 규칙**: `.vscode/strategy/combination-rules.md` (전략 조합 로직)

### 🔧 트리거 빌더 시스템 (핵심 ⭐⭐⭐)
- **트리거 빌더 가이드**: `.vscode/guides/trigger-builder-system.md` (전체 시스템 개요)
  - 3중 카테고리 시스템 (purpose, chart, comparison)
  - 새로운 DB 스키마 구조 (trading_variables, variable_parameters)
  - 동적 파라미터 관리 시스템
  - 통합 호환성 검증 시스템
- **변수 호환성**: `.vscode/guides/variable-compatibility.md` (호환성 규칙 상세)

### 🏛️ 아키텍처 & 기술 가이드
- **전체 아키텍처**: `.vscode/guides/architecture.md` (시스템 구조)
- **컴포넌트 설계**: `.vscode/architecture/component-design.md` (컴포넌트 패턴)
- **DB 설계**: `.vscode/guides/database.md` (데이터베이스 구조 + 트리거 빌더 DB)

### 🎨 UI/UX 가이드
- **디자인 시스템**: `.vscode/ui/design-system.md` (560줄 - 컴포넌트, 색상, 레이아웃)

> **💡 개발 팁**: 특정 기능 구현 전에는 해당 분야의 문서를 먼저 읽어보세요! 

---

## 🗄️ 데이터베이스 개발 원칙 (필수 준수)

### 표준 규칙
```bash
# ✅ 올바른 DB 파일 구조 (반드시 준수)
data/
├── app_settings.sqlite3      # 프로그램 설정 (전략, 조건, 시스템 설정)
└── market_data.sqlite3       # 백테스팅용 시장 데이터

# ❌ 금지사항
- 루트 폴더의 .db 파일들
- .db 확장자 사용 (반드시 .sqlite3)
- 서로 다른 폴더의 DB 파일들
```

### DB 연결 표준 패턴
```python
# ✅ 모든 DB 클래스는 이 패턴을 따라야 함

# 프로그램 설정 관련
class ConditionStorage:
    def __init__(self, db_path: str = "data/app_settings.sqlite3"):
        self.db_path = db_path

# 시장 데이터 관련  
class BacktestEngine:
    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path
```

---

## 🏗️ 아키텍처 원칙

### 컴포넌트 기반 설계
```
upbit_auto_trading/
├── component_system/          # 핵심 컴포넌트 시스템
├── ui/desktop/screens/        # 화면별 UI 컴포넌트들
└── data_providers/           # 데이터 제공자들
```

### 전략 시스템 (V1.0.1)
```python
# 진입/관리 전략의 명확한 역할 분리
if position_state == "waiting_entry":
    # 진입 전략만 활성화
    entry_signal = entry_strategy.generate_signal()
    
elif position_state == "position_management":
    # 관리 전략들만 활성화
    mgmt_signal = mgmt_strategy.generate_signal()
```

---

## 🎨 UI 개발 지침

### 필수 컴포넌트 사용
```python
# 항상 이 컴포넌트들을 사용
from upbit_auto_trading.ui.desktop.common.components import (
    PrimaryButton,      # 주요 동작 (파란색)
    SecondaryButton,    # 보조 동작 (회색)
    DangerButton,       # 위험 동작 (빨간색)
    StyledLineEdit,     # 입력 필드
    StyledComboBox,     # 드롭다운
    StyledDialog        # 다이얼로그
)
```

### PyQt6 표준 패턴
```python
class MyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """UI 구성 요소 초기화"""
        layout = QVBoxLayout(self)
        # 스타일된 컴포넌트 사용
        
    def connect_signals(self):
        """시그널과 슬롯 연결"""
        pass
```

---

## 🔧 개발 워크플로우

### 필수 테스트
모든 코드 변경 후에는 반드시:
```powershell
# PowerShell 구문 사용
python run_desktop_ui.py
```

### 🔬 디버그 로깅 시스템 v2.3 (조건부 컴파일 통합)
**위치**: `upbit_auto_trading/utils/debug_logger.py`  
**가이드**: `upbit_auto_trading/utils/DEBUG_LOGGER_USAGE_GUIDE_v2.2.md`

#### 스마트 로그 필터링 (NEW)
```powershell
# 환경변수 설정으로 로그 레벨 제어
$env:UPBIT_ENV = "production"      # ERROR/CRITICAL만 표시
$env:UPBIT_ENV = "development"     # 모든 로그 표시 (기본값)
$env:UPBIT_BUILD_TYPE = "release"  # 최적화된 로그 필터링
$env:UPBIT_DEBUG_MODE = "false"    # 디버그 로그 완전 제거
```

#### 기본 사용법
```python
# 🟦 기본 사용법 (ComponentLogger 권장)
from upbit_auto_trading.utils.debug_logger import get_logger

logger = get_logger("MyComponent")  # 자동으로 컴포넌트명 포함

# 모든 로그 메서드 지원
logger.info("📊 시장 데이터 업데이트")
logger.warning("⚠️ API 응답 지연")
logger.error("❌ 거래 실행 실패")
logger.success("✅ 조건 저장 완료")  # v2.3 신규
logger.performance("⚡ DB 쿼리 시간: 0.5초")  # v2.3 신규

# 🟦 조건부 컴파일 사용법 (프로덕션 최적화)
if logger.should_log_debug():  # 환경에 따라 자동 판단
    logger.debug("🔍 상세 디버그 정보")

# 원라인 조건부 로깅
logger.conditional_debug(lambda: f"🔍 복잡한 계산 결과: {expensive_calculation()}")
```

#### 듀얼 파일 시스템
- **메인 로그**: `logs/upbit_auto_trading.log` (최신 로그가 맨 위, 에이전트 친화적)
- **세션별**: `logs/session_YYYYMMDD_HHMMSS.log` (전체 로그 백업)
- **자동 관리**: 헤더 중복 제거, 한글 완벽 지원, 성능 최적화

#### 환경별 최적화 (v2.3)
```python
# 개발 환경 (기본값)
UPBIT_ENV=development → 모든 로그 레벨 표시
UPBIT_DEBUG_MODE=true → debug(), performance() 메서드 활성화

# 프로덕션 환경
UPBIT_ENV=production → ERROR, CRITICAL만 표시
UPBIT_DEBUG_MODE=false → debug(), performance() 완전 제거 (제로 오버헤드)
```

### 터미널 명령어 작성 시 주의사항 ⚠️
```powershell
# ✅ 올바른 PowerShell 예시
cd "d:\projects\upbit-autotrader-vscode"; python -c "import sys; print(sys.version)"
Get-ChildItem "upbit_auto_trading" -Recurse -Filter "*.py" | Measure-Object

# ❌ 절대 사용 금지 (Unix/Linux 구문)
cd /path/to/project && python -c "import sys; print(sys.version)"
find upbit_auto_trading -name "*.py" | wc -l
```

### 🚨 폴백 코드 제거 정책 (핵심 ⭐⭐⭐)

#### "종기의 고름을 뺀다" - 폴백 코드의 역기능
- **문제**: 폴백 코드가 실제 에러를 숨겨서 디버깅을 방해
- **원칙**: "동작이 안되면 화면이 비고 에러가 표시되는게 훨씬 개발에 도움이 됩니다"
- **해결**: 모든 폴백 코드를 제거하여 **실제 문제가 명확히 드러나도록**

#### 폴백 제거 가이드라인
```python
# ❌ 폴백 코드 (문제를 숨김)
try:
    from .components.condition_storage import ConditionStorage
except ImportError:
    # 폴백으로 더미 클래스 생성 - 문제를 숨김!
    class ConditionStorage:
        def __init__(self): pass

# ✅ 폴백 제거 (문제를 명확히 드러냄)
from .components.core.condition_storage import ConditionStorage
# 에러가 발생하면 바로 ModuleNotFoundError로 정확한 경로 문제를 알 수 있음
```

#### 허용되는 최소 폴백
- **UI 틀 보존**: 화면이 완전히 깨지지 않도록 하는 최소한의 구조적 폴백만 허용
- **에러 표시**: 폴백 실행 시에도 반드시 에러 메시지 표시
- **import 에러**: 절대 숨기지 말고 정확한 경로 문제를 드러내기

#### 폴백 제거의 효과
1. **명확한 에러 메시지**: `ModuleNotFoundError: No module named 'x.y.z'`
2. **정확한 경로 파악**: 실제 파일 위치를 빠르게 찾을 수 있음
3. **디버깅 효율성**: 문제 해결 시간 대폭 단축
4. **코드 품질**: 실제 동작하는 코드만 남김

### 복잡한 버그 추적 방법론 (권장)
복잡한 코드베이스에서는 **천천히 가는 것이 빠르게 가는 방법**입니다:

#### 1. 문제 정의 단계
```
🎯 문제: 특정 UI 요소가 예상대로 표시되지 않음
📝 증상: 외부변수 파라미터 정보가 "저장되지 않음"으로 표시
🔍 범위: 데이터 저장 → 로드 → 표시 과정 전체
```

#### 2. 코드 경로 추적 (필수)
```python
# 실행 경로를 완전히 파악
# 예: run_desktop_ui.py → main_window.py → strategy_management_screen.py 
#     → integrated_condition_manager.py → on_trigger_selected()

# 각 단계에서 데이터 형태 확인
print(f"🔍 데이터 확인: {variable_name} = {data_structure}")
```

#### 3. 데이터 구조 분석
```python
# 저장 형태 vs 표시 로직의 불일치 확인
# 예: 
# - DB 저장: external_variable = {"variable_id": "sma", "variable_name": "단순이동평균"}
# - 표시 코드 기대: external_variable_params 키를 찾음
# → 불일치 발견!
```

#### 4. 단계별 수정 접근법
```python
# 🔄 데이터 수집 단계 수정 (condition_dialog.py)
def collect_condition_data(self):
    # 외부변수 파라미터를 external_variable 객체에 포함
    external_variable_info = {
        'variable_id': external_var_id,
        'variable_name': self.external_variable_combo.currentText(),
        'category': self.external_category_combo.currentData(),
        'variable_params': external_params  # 🆕 파라미터 추가
    }

# 🔄 표시 로직 수정 (integrated_condition_manager.py)  
def on_trigger_selected(self, item, column):
    # 외부변수 파라미터 안전하게 추출
    ext_var_params = external_variable_info.get('variable_params', {})
    if ext_var_params:
        # 파라미터 표시 로직
    else:
        # 대체 표시 로직
```

#### 5. 검증 및 테스트
```powershell
# 각 수정 사항을 즉시 테스트 (PowerShell 구문)
python run_desktop_ui.py
# → 조건 생성 → 저장 → 로드 → 표시 확인
```

### 디버깅 도구 활용
```python
# 🔍 데이터 구조 상세 확인
import json
print(f"📊 데이터 구조: {json.dumps(data, indent=2, ensure_ascii=False)}")

# 🔍 객체 타입 확인  
print(f"🏷️ 타입 확인: {type(variable)} - {isinstance(variable, dict)}")

# 🔍 조건부 디버깅
if debug_mode:
    print(f"🔧 디버그: {variable_name} = {value}")
```

### 에러 처리 및 품질 관리
- try-catch 블록으로 안전한 코드 작성
- 적절한 로깅 메시지 포함
- 사용자 친화적인 에러 메시지
- **점진적 수정**: 한 번에 여러 부분을 수정하지 말고 단계별로 접근

### 성능 고려사항
- UI 스레드 블로킹 방지
- 메모리 누수 주의
- 리소스 정리 (close, deleteLater) 필수
- **토큰 효율성**: 복잡한 문제일수록 충분한 조사와 단계별 접근이 결과적으로 더 효율적

---

## 💡 성공적인 개발을 위한 원칙

### "천천히 가는 것이 빠르게 가는 방법"
복잡한 코드베이스에서는:
1. **충분한 조사** - 코드 경로와 데이터 구조를 완전히 파악
2. **단계별 접근** - 한 번에 하나의 문제만 해결
3. **즉시 검증** - 각 수정 사항을 바로 테스트
4. **문서화** - 발견한 패턴과 해결책을 기록
5. **패턴 인식** - 유사한 문제에 적용할 수 있는 방법론 확립

### 토큰 사용 철학
- **품질 있는 조사**: 문제 해결을 위한 충분한 도구 사용 환영
- **체계적 접근**: 무작정 시도하기보다는 계획적인 디버깅
- **지속가능성**: 한 번 해결한 방법을 재사용 가능하도록 문서화

---

## 🚨 중요 고려사항

### 변수 호환성 규칙 (핵심 시스템 ⭐⭐⭐)
- **필수 문서**: `.vscode/guides/variable-compatibility.md` 및 `.vscode/guides/trigger-builder-system.md` 참조
- **핵심 원칙**: 의미있는 변수 조합만 허용, 논리적으로 맞지 않는 비교 방지
- **3중 카테고리 시스템**:
  1. **Purpose Category**: trend, momentum, volatility, volume, price
  2. **Chart Category**: overlay, subplot  
  3. **Comparison Group**: price_comparable, percentage_comparable, volume_comparable 등
- **구현 우선순위**:
  1. **최우선**: UI 레벨 실시간 검증 (사용자가 호환되지 않는 변수 선택 시 즉시 차단)
  2. **필수**: 백엔드 검증 (조건 저장 전 최종 호환성 재검증)
  3. **권장**: DB 제약 조건 및 성능 최적화
- **예시 호환성**:
  - ✅ RSI ↔ 스토캐스틱 (같은 momentum/percentage_comparable)
  - ✅ 현재가 ↔ 이동평균 (같은 price/price_comparable)
  - ❌ RSI ↔ MACD (다른 comparison_group)
  - ❌ 현재가 ↔ 거래량 (완전히 다른 단위와 의미)
  - ✅ 현재가 ↔ 이동평균 (같은 가격 단위)
  - ❌ RSI ↔ MACD (다른 카테고리, 스케일 불일치)
  - ❌ 현재가 ↔ 거래량 (완전히 다른 단위와 의미)

### 보안
- API 키 하드코딩 금지
- 환경변수 또는 설정 파일 활용
- 민감한 데이터 로깅 방지

### 코딩 스타일
- PEP 8 준수
- 타입 힌트 사용 권장
- Docstring 작성

이 지침을 따라 일관성 있고 품질 높은 코드를 작성해주세요.