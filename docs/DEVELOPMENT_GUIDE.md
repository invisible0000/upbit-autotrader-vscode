# 🛠️ 개발 가이드 (통합)

## 🎯 개발 철학

**핵심 목표**: DDD 기반 견고한 아키텍처 + 기본 7규칙 전략 완벽 구현
**검증 기준**: 모든 개발은 기본 7규칙 전략 동작으로 검증
**에러 원칙**: "에러를 숨기지 말고 명확히 드러내라"

## ✅ 개발 체크리스트

### 🏆 1단계: 기본 7규칙 전략 검증 (최우선)
- [ ] **RSI 과매도 진입**: 트리거 빌더에서 `RSI < 30` 조건 생성 가능
- [ ] **수익시 불타기**: 수익률 3%마다 추가 매수 설정 가능
- [ ] **계획된 익절**: 수익률 15% 도달 시 전량 매도 설정 가능
- [ ] **트레일링 스탑**: 최고점 대비 -5% 손절 설정 가능
- [ ] **하락시 물타기**: 손실률 -5%마다 추가 매수 설정 가능
- [ ] **급락 감지**: 15분간 -10% 하락 시 전량 매도 설정 가능
- [ ] **급등 감지**: 15분간 +15% 상승 시 일부 매도 설정 가능

**검증 명령**: `python run_desktop_ui.py` → 전략 관리 → 트리거 빌더

### 🧪 1.5단계: 복잡한 시스템 테스트 (필수)
- [ ] **Live Testing**: `python run_desktop_ui.py`로 실제 동작 확인
- [ ] **로그 분석**: Infrastructure 로깅으로 문제점 추적
- [ ] **계층별 검증**: UI → Application → Domain → Infrastructure 순서
- [ ] **점진적 개선**: 작은 단위 수정 → 즉시 검증 → 누적 개선

**📖 자세한 가이드**: [COMPLEX_SYSTEM_TESTING_GUIDE.md](COMPLEX_SYSTEM_TESTING_GUIDE.md)

### 🏗️ 2단계: DDD 아키텍처 준수
```
Domain Layer (핵심 비즈니스)
├── 도메인 엔티티에 비즈니스 로직 포함
├── 값 객체로 ID, Signal 등 관리
├── 도메인 서비스로 복잡한 규칙 처리
└── Repository 인터페이스 정의

Application Layer (Use Cases)
├── Application Service로 Use Case 구현
├── DTO로 계층 간 데이터 전송
├── Command/Query 분리
└── 트랜잭션 경계 관리

Infrastructure Layer (외부 연동)
├── Repository 구체 구현
├── 외부 API 접근 격리
├── Infrastructure 로깅 시스템 사용
└── 의존성 주입으로 인터페이스 연결

Presentation Layer (UI)
├── MVP 패턴 (Passive View + Presenter)
├── 통합 스타일 시스템 사용
├── PyQt6 신호/슬롯 패턴
└── 사용자 친화적 에러 표시
```

### 🗄️ 3단계: 3-DB 아키텍처 준수
- [ ] **settings.sqlite3**: 변수 정의, 파라미터 (data_info/*.yaml 기반)
- [ ] **strategies.sqlite3**: 사용자 전략, 백테스팅 결과
- [ ] **market_data.sqlite3**: 시장 데이터, 지표 캐시
- [ ] **표준 경로**: `data/*.sqlite3` 파일만 사용
- [ ] **폐기 파일**: `app_settings.sqlite3`, `*.db` 언급 금지

## 🚨 에러 처리 정책

### Domain Layer 에러 숨김 절대 금지
```python
# ❌ 절대 금지: 에러 숨김으로 Domain 문제 은폐
try:
    from domain.services import StrategyValidationService
except ImportError:
    class StrategyValidationService: pass  # 폴백으로 에러 숨김

# ✅ 필수: 에러 즉시 노출로 문제 파악
from domain.services import StrategyValidationService  # 실패 시 즉시 ModuleNotFoundError
```

### Business Logic 폴백 금지
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

### 계층별 에러 처리 원칙
```python
# Domain Layer: 비즈니스 규칙 위반
class DomainRuleViolationError(Exception):
    pass

# Application Layer: 사용 사례 실패
class UseCaseExecutionError(Exception):
    pass

# Infrastructure Layer: 외부 연동 실패
class ExternalServiceError(Exception):
    pass

# Presentation Layer: 사용자 입력 오류
class UserInputValidationError(Exception):
    pass
```

## 🎨 UI 개발 규칙

### 통합 스타일 시스템 (필수)
```python
# ✅ 올바른 방법: 전역 스타일 시스템 사용
widget.setObjectName("primary_button")  # QSS에서 스타일 정의

# ❌ 금지: 하드코딩된 색상
widget.setStyleSheet("background-color: white;")  # 테마 시스템 무시
widget.setStyleSheet("color: #333333;")           # 고정 색상

# ✅ matplotlib 차트 테마 적용
from upbit_auto_trading.ui.desktop.common.theme_notifier import apply_matplotlib_theme_simple
apply_matplotlib_theme_simple()  # 차트 그리기 전 반드시 호출
```

### MVP 패턴 구현
```python
# Passive View (표시만 담당)
class TriggerBuilderView(QWidget):
    condition_created = pyqtSignal(dict)  # Presenter와 소통

    def display_compatibility_result(self, result):
        """Presenter가 제공한 결과만 표시"""
        pass

# Presenter (비즈니스 로직 처리)
class TriggerBuilderPresenter:
    def __init__(self, view, domain_service):
        self.view = view
        self.domain_service = domain_service

    def on_compatibility_check(self, var1, var2):
        result = self.domain_service.check_compatibility(var1, var2)
        self.view.display_compatibility_result(result)
```

## 🔧 Infrastructure 로깅 시스템

### 표준 로깅 사용법
```python
from upbit_auto_trading.infrastructure.logging import create_component_logger

# 기본 사용
logger = create_component_logger("TriggerBuilder")
logger.info("트리거 생성 시작")
logger.debug("상세 진행상황")  # 환경변수로 제어

# 환경변수 제어
$env:UPBIT_CONSOLE_OUTPUT='true'           # 콘솔 출력
$env:UPBIT_LOG_SCOPE='verbose'             # 로그 레벨
$env:UPBIT_COMPONENT_FOCUS='TriggerBuilder' # 특정 컴포넌트 집중
```

### 실시간 설정 변경
- **config/logging_config.yaml** 수정 시 즉시 반영
- 재시작 없이 로그 레벨, 컴포넌트 포커스 변경
- 개발 환경별 자동 설정 적용

## 📋 코딩 스타일 규칙

### Python 코드 작성
```python
# PEP 8 준수
def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """RSI 계산 함수

    Args:
        data: 가격 데이터
        period: RSI 계산 기간

    Returns:
        RSI 값 시리즈
    """
    delta = data.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 타입 힌트 필수
def validate_strategy(strategy: Strategy) -> ValidationResult:
    pass

# 의미있는 변수명 (축약어 금지)
user_strategy = load_strategy()  # ✅
usr_strtgy = load_strategy()     # ❌
```

### 파일 구조 및 네이밍
```
upbit_auto_trading/
├── domain/                     # Domain Layer
│   ├── entities/
│   ├── value_objects/
│   ├── services/
│   └── repositories/
├── application/                # Application Layer
│   ├── services/
│   ├── dto/
│   └── use_cases/
├── infrastructure/             # Infrastructure Layer
│   ├── logging/
│   ├── repositories/
│   └── external_apis/
└── ui/                        # Presentation Layer
    └── desktop/
        ├── presenters/
        ├── views/
        └── common/
```

### 파일명 일관성 유지 (중요)
```python
# 기존 기능 교체 시 파일명 연속성 유지
strategy_service.py          # 기존 파일
strategy_service_legacy.py   # 백업 파일
strategy_service.py          # 새 구현체 (동일 이름 사용)

# 임시 파일명 사용 금지
simple_strategy_service.py   # ❌ 금지
new_strategy_service.py      # ❌ 금지
temp_strategy_service.py     # ❌ 금지
```

## 🧪 테스트 및 검증

### 단위 테스트 필수 작성
```python
def test_basic_7_rule_strategy():
    """기본 7규칙 전략 동작 검증"""
    strategy = Basic7RuleStrategy()

    # 각 규칙별 검증
    assert strategy.has_rsi_entry_rule()
    assert strategy.has_profit_averaging_up()
    assert strategy.has_planned_take_profit()
    assert strategy.has_trailing_stop()
    assert strategy.has_loss_averaging_down()
    assert strategy.has_crash_detection()
    assert strategy.has_surge_detection()

    # 전체 시스템 검증
    backtest_result = run_backtest(strategy, test_data)
    assert backtest_result.total_trades > 0
    assert backtest_result.win_rate is not None
```

### 호환성 검증 테스트
```python
def test_variable_compatibility():
    """변수 호환성 시스템 검증"""
    checker = VariableCompatibilityDomainService()

    # 호환 가능한 조합
    assert checker.check_compatibility("SMA", "EMA").is_compatible()
    assert checker.check_compatibility("RSI", "Stochastic").is_compatible()

    # 비호환 조합 (차단)
    assert checker.check_compatibility("RSI", "MACD").is_incompatible()
    assert checker.check_compatibility("Volume", "RSI").is_incompatible()
```

## 💻 개발 환경 설정

### PowerShell 전용 (Windows)
```powershell
# 명령어 연결
cmd1; cmd2

# 환경 변수 설정
$env:UPBIT_CONSOLE_OUTPUT='true'
$env:UPBIT_LOG_SCOPE='verbose'

# 디렉토리 이동
cd d:\projects\upbit-autotrader-vscode

# 애플리케이션 실행
python run_desktop_ui.py
```

### 개발 워크플로우
1. **기존 코드 분석**: 새 코드 작성 전 기존 코드베이스 분석
2. **Infrastructure 로깅**: 실시간 모니터링으로 진행상황 추적
3. **DDD 계층 준수**: 각 계층의 역할과 의존성 방향 확인
4. **7규칙 검증**: 개발 완료 후 기본 7규칙 전략으로 동작 검증

## 🚀 성능 최적화

### DB 최적화
```python
# 연결 풀 사용
database_manager = DatabaseManager()
with database_manager.get_connection() as conn:
    # DB 작업

# 인덱스 활용
CREATE INDEX idx_tv_trading_variables_name ON tv_trading_variables(name);
CREATE INDEX idx_strategies_created_at ON user_strategies(created_at);
```

### UI 최적화
```python
# 지연 로딩
def setup_ui(self):
    self.tabs.currentChanged.connect(self.on_tab_changed)

def on_tab_changed(self, index):
    if not self.tabs.widget(index).is_loaded:
        self.tabs.widget(index).load_content()  # 필요시에만 로드

# 메모리 관리
def closeEvent(self, event):
    self.disconnect_all_signals()  # 이벤트 연결 해제
    super().closeEvent(event)
```

## ⚠️ PyQt6 개발 주의사항

### 빈 위젯 Bool 평가 이슈
```python
# ❌ 위험한 패턴
list_widget = QListWidget()
if not list_widget:  # False! (빈 위젯)
    raise Error("생성 실패")

# ✅ 안전한 패턴
if list_widget is None:
    raise Error("생성 실패")
```

**영향받는 위젯**: `QListWidget`, `QComboBox`, `QTableWidget`, `QTreeWidget`
**상세 가이드**: [PyQt6 빈 위젯 Bool 이슈](PyQt6_Empty_Widget_Bool_Issue.md)

## 📚 참고 문서

- **[기본 7규칙 전략 가이드](BASIC_7_RULE_STRATEGY_GUIDE.md)**: 시스템 검증 기준
- **[아키텍처 가이드](ARCHITECTURE_GUIDE.md)**: DDD 설계 원칙
- **[전략 가이드](STRATEGY_GUIDE.md)**: 전략 시스템 구현
- **[UI 가이드](UI_GUIDE.md)**: UI 개발 표준
- **[통합 설정 관리 가이드](UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md)**: 설정 시스템

---

**🎯 개발 성공 기준**: `python run_desktop_ui.py` 실행 → 기본 7규칙 전략 완벽 구성 가능!

**💡 핵심 원칙**: DDD 아키텍처 준수 + 에러 투명성 + 7규칙 검증
