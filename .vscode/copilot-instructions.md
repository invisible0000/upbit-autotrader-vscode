# Upbit Auto T### 🎨 **스타일 가이드 (필수)**
- **코딩 스타일**: `.vscode/STYLE_GUIDE.md` ⭐ **반드시 준수**
  - UI/UX 테마 시스템 규칙
  - PyQt6 스타일링 가이드라인
  - matplotlib 차트 테마 적용 방법
  - 금지사항 및 권장사항
- **개발 체크리스트**: `.vscode/DEV_CHECKLIST.md` 📝 **커밋 전 확인** 프로젝트 - GitHub Copilot 지침

> **⚡ 빠른 참조**: DB는 `.sqlite3`, `data/` 폴더, 테스트는 `python run_desktop_ui.py`

## 🎯 프로젝트 개요
**upbit-autotrader-vscode**는 업비트 거래소를 위한 자동매매 시스템입니다.
- **언어**: Python 3.9+
- **UI 프레임워크**: PyQt6
- **데이터베이스**: SQLite3
- **아키텍처**: 컴포넌트 기반 모듈러 설계

## 📚 상세 가이드 참조
개발 전 반드시 아래 문서들을 확인하세요:

### � **스타일 가이드 (필수)**
- **코딩 스타일**: `.vscode/STYLE_GUIDE.md` ⭐ **반드시 준수**
  - UI/UX 테마 시스템 규칙
  - PyQt6 스타일링 가이드라인
  - matplotlib 차트 테마 적용 방법
  - 금지사항 및 권장사항

### �🏗️ 핵심 설계 문서
- **프로젝트 명세**: `.vscode/project-specs.md` (243줄 - 비즈니스 로직)
- **README**: `.vscode/README.md` (프로젝트 개요)

### 🎯 전략 시스템 가이드 
- **진입 전략**: `.vscode/strategy/entry-strategies.md` (454줄 - 6개 진입 전략 상세)
- **관리 전략**: `.vscode/strategy/management-strategies.md` (관리 전략 구현)
- **조합 규칙**: `.vscode/strategy/combination-rules.md` (전략 조합 로직)

### 🏛️ 아키텍처 & 기술 가이드
- **전체 아키텍처**: `.vscode/guides/architecture.md` (시스템 구조)
- **컴포넌트 설계**: `.vscode/architecture/component-design.md` (컴포넌트 패턴)
- **DB 설계**: `.vscode/guides/database.md` (데이터베이스 구조)

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
```bash
python run_desktop_ui.py
```

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
```python
# 각 수정 사항을 즉시 테스트
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
- **필수 문서**: `.vscode/guides/variable-compatibility.md` 참조
- **핵심 원칙**: 의미있는 변수 조합만 허용, 논리적으로 맞지 않는 비교 방지
- **구현 우선순위**:
  1. **최우선**: UI 레벨 실시간 검증 (사용자가 호환되지 않는 변수 선택 시 즉시 차단)
  2. **필수**: 백엔드 검증 (조건 저장 전 최종 호환성 재검증)
  3. **권장**: DB 제약 조건 및 성능 최적화
- **예시 호환성**:
  - ✅ RSI ↔ 스토캐스틱 (같은 오실레이터, 0-100 스케일)
  - ✅ 현재가 ↔ 이동평균 (같은 가격 단위)
  - ❌ RSI ↔ MACD (다른 카테고리, 스케일 불일치)
  - ❌ 현재가 ↔ 거래량 (완전히 다른 단위와 의미)

### 터미널 환경 및 명령어
- **운영체제**: Windows
- **기본 셸**: PowerShell (powershell.exe v5.1)
- **명령어 생성 시 주의사항**:
  - Windows PowerShell 명령어 구문 사용
  - Linux/macOS 명령어(cat, ls, grep 등) 대신 PowerShell 명령어 사용
  - 명령어 연결 시 `;` 사용 (&&가 아닌)
  - 파일 경로는 백슬래시(`\`) 사용
  - PowerShell 특유의 명령어 구문 활용 (Get-ChildItem, Select-String 등)

### 보안
- API 키 하드코딩 금지
- 환경변수 또는 설정 파일 활용
- 민감한 데이터 로깅 방지

### 코딩 스타일
- PEP 8 준수
- 타입 힌트 사용 권장
- Docstring 작성

이 지침을 따라 일관성 있고 품질 높은 코드를 작성해주세요.