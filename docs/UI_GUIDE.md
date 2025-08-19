# 🎨 UI 시스템 완전 가이드

## 🎯 UI 디자인 철학

**핵심 목표**: 초보자도 80% 기능을 무도움으로 사용할 수 있는 직관적 인터페이스
**설계 패턴**: MVP/MVVM 패턴 + DDD 계층 분리
**테마 시스템**: 중앙 집중식 전역 스타일 관리

### 기본 원칙
- **반응성**: 사용자 입력 0.5초 내 반응
- **접근성**: 최소 1280x720 해상도 지원
- **일관성**: 전체 애플리케이션 통일된 스타일
- **7규칙 중심**: 기본 7규칙 전략 워크플로 최적화

### ⚠️ PyQt6 개발 주의사항
- **위젯 검증**: `if widget is None:` 사용 (❌ `if not widget:`)
- **빈 컨테이너**: `QListWidget`, `QComboBox` 등은 빈 상태에서 `bool() = False`
- **상세 가이드**: [PyQt6 빈 위젯 Bool 이슈](PyQt6_Empty_Widget_Bool_Issue.md)

## 📐 레이아웃 시스템

### 메인 윈도우 크기 및 구조
```python
# 권장 크기
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 1000

# 최소 지원 크기
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 800
```

### 트리거 빌더 레이아웃 (3분할 구조)
```
┌─────────────────────────────────────────────────────┐
│                메인 윈도우 (1600x1000)                │
├─────────────┬─────────────────┬─────────────────────┤
│  조건 빌더   │  트리거 관리     │   시뮬레이션 영역    │
│   (2:5)     │    (3:5)        │      (2:5)         │
│             │                │                    │
│ 변수 선택   │ 생성된 조건 목록  │ 백테스팅 차트      │
│ 파라미터    │ 드래그앤드롭     │ 성능 지표          │
│ 호환성 검증  │ 조건 조합       │ 실시간 미리보기     │
└─────────────┴─────────────────┴─────────────────────┘
```

## 🏗️ UI 아키텍처 (DDD + MVP 패턴)

### 계층별 구조
```
upbit_auto_trading/ui/desktop/
├── main_window.py                # 메인 애플리케이션
├── presenters/                   # MVP 패턴 Presenter
│   ├── strategy_presenter.py     # 전략 관리 프레젠터
│   ├── trigger_presenter.py      # 트리거 빌더 프레젠터
│   └── backtest_presenter.py     # 백테스팅 프레젠터
├── views/                        # Passive View 구현
│   ├── strategy_view.py          # 전략 관리 뷰
│   ├── trigger_view.py           # 트리거 빌더 뷰
│   └── backtest_view.py          # 백테스팅 뷰
└── common/                       # 공통 UI 시스템
    ├── styles/                   # 통합 스타일 시스템 ⭐
    ├── widgets/                  # 재사용 위젯
    └── theme_notifier.py         # 테마 관리
```

### MVP 패턴 구현 예시
```python
# Passive View (표시만 담당)
class TriggerBuilderView(QWidget):
    # 신호 정의 (Presenter와 소통)
    condition_created = pyqtSignal(dict)
    rule_updated = pyqtSignal(dict)
    compatibility_check_requested = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.apply_global_theme()  # 전역 테마 적용

    def display_compatibility_result(self, result: CompatibilityResult):
        """Presenter가 제공한 결과만 표시"""
        pass

    def update_available_variables(self, variables: List[Variable]):
        """Presenter가 필터링한 변수 목록 표시"""
        pass

# Presenter (비즈니스 로직 처리)
class TriggerBuilderPresenter:
    def __init__(self, view: TriggerBuilderView,
                 compatibility_service: VariableCompatibilityDomainService):
        self.view = view
        self.compatibility_service = compatibility_service
        self.connect_signals()

    def on_compatibility_check_requested(self, var1_id: str, var2_id: str):
        """호환성 검증 비즈니스 로직"""
        result = self.compatibility_service.check_compatibility(var1_id, var2_id)
        self.view.display_compatibility_result(result)
```

## 🎨 통합 스타일 시스템 (필수 규칙)

### 전역 스타일 관리 구조
```
upbit_auto_trading/ui/desktop/common/styles/
├── style_manager.py          # 중앙 스타일 관리자 ⭐
├── default_style.qss         # 기본 라이트 테마
├── dark_style.qss           # 다크 테마
└── component_styles.qss     # 컴포넌트별 확장 스타일
```

### ✅ 올바른 스타일 사용법
```python
# 표준 QWidget 스타일 활용 (권장)
class EnvironmentProfileView(QWidget):
    def __init__(self):
        super().__init__()
        self.main_splitter = QSplitter()  # 전역 QSplitter 스타일 자동 적용

        # 특수한 경우에만 objectName 설정
        self.quick_env_button = QPushButton("개발환경")
        self.quick_env_button.setObjectName("quick_env_button_development")

# matplotlib 차트 테마 적용
from upbit_auto_trading.ui.desktop.common.theme_notifier import apply_matplotlib_theme_simple

def create_chart(self):
    apply_matplotlib_theme_simple()  # 차트 그리기 전 필수 호출
    fig, ax = plt.subplots()
    # 차트 생성 로직...
```

### ❌ 금지된 스타일 사용법
```python
# 하드코딩된 스타일 금지 (전역 테마 시스템 무시)
widget.setStyleSheet("background-color: white;")
widget.setStyleSheet("color: #333333;")

# 개별 QSS 파일 생성 금지
# styles/my_component.qss  # 전역 관리 원칙 위반

# matplotlib 하드코딩 금지
ax.plot(data, color='blue')      # 테마 무시
ax.set_facecolor('white')        # 고정 배경색
```

### 테마 시스템 동작 방식
```python
# StyleManager가 중앙에서 모든 스타일 관리
class StyleManager:
    def __init__(self):
        self.current_theme = 'default'
        self.load_theme_styles()

    def switch_theme(self, theme_name: str):
        """테마 전환 시 모든 위젯에 자동 적용"""
        self.current_theme = theme_name
        self.load_theme_styles()
        self.apply_to_all_widgets()

    def apply_to_all_widgets(self):
        """모든 활성 위젯에 새 테마 적용"""
        app = QApplication.instance()
        app.setStyleSheet(self.get_current_stylesheet())
```

## 🎯 트리거 빌더 UI 상세 설계

### 조건 생성 워크플로
```python
class ConditionBuilderWidget(QWidget):
    """조건 생성 단계별 UI"""

    def __init__(self):
        super().__init__()
        self.setup_step_workflow()

    def setup_step_workflow(self):
        """4단계 조건 생성 워크플로"""
        self.steps = [
            ("1단계", "기본 변수 선택", self.setup_base_variable_step),
            ("2단계", "비교 연산자 선택", self.setup_operator_step),
            ("3단계", "외부 변수/값 선택", self.setup_external_step),
            ("4단계", "파라미터 설정", self.setup_parameter_step)
        ]

    def on_base_variable_selected(self, variable_id: str):
        """1단계: 기본 변수 선택 → 호환 변수 필터링"""
        compatible_vars = self.presenter.get_compatible_variables(variable_id)
        self.update_external_variable_options(compatible_vars)
```

### 실시간 호환성 검증 UI
```python
class CompatibilityIndicator(QWidget):
    """실시간 호환성 표시 위젯"""

    def __init__(self):
        super().__init__()
        self.setObjectName("compatibility_indicator")

    def show_compatibility_status(self, status: CompatibilityResult):
        if status.is_compatible():
            self.setProperty("status", "compatible")
            self.setText("✅ 호환됨")
        elif status.needs_normalization():
            self.setProperty("status", "warning")
            self.setText("⚠️ 정규화 필요")
        else:
            self.setProperty("status", "incompatible")
            self.setText("❌ 비호환")

        self.style().unpolish(self)  # QSS 재적용 강제
        self.style().polish(self)
```

### 드래그 앤 드롭 시스템
```python
class RuleBuilderWidget(QWidget):
    """규칙 조합을 위한 드래그앤드롭"""

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-condition"):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        condition_data = event.mimeData().data("application/x-condition")
        condition = self.deserialize_condition(condition_data)

        # 호환성 검증 후 추가
        if self.presenter.validate_rule_compatibility(condition):
            self.add_condition_to_rule(condition)
        else:
            self.show_compatibility_error()
```

## 📊 차트 및 시각화 시스템

### matplotlib 통합 테마
```python
def apply_matplotlib_theme_simple():
    """matplotlib 차트에 현재 테마 적용"""
    current_theme = StyleManager.get_current_theme()

    if current_theme == 'dark':
        plt.style.use('dark_background')
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    else:
        plt.style.use('default')
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    # 전역 설정 적용
    plt.rcParams['axes.prop_cycle'] = plt.cycler(color=colors)
    plt.rcParams['figure.facecolor'] = get_theme_color('chart_background')
```

### 실시간 차트 업데이트
```python
class BacktestChartWidget(QWidget):
    """백테스팅 결과 차트"""

    def __init__(self):
        super().__init__()
        self.setup_chart()

    def update_chart_realtime(self, data: BacktestData):
        """실시간 백테스팅 결과 업데이트"""
        apply_matplotlib_theme_simple()  # 테마 적용

        self.ax.clear()
        self.ax.plot(data.timestamps, data.portfolio_value)
        self.ax.set_title("포트폴리오 가치 변화")

        self.canvas.draw()
```

## ⚙️ 설정 시스템

### 완전 구현된 기능
- **테마 설정**: 라이트/다크 테마 전환 (완료)
- **로깅 설정**: 실시간 설정 변경 지원 (완료)
- **언어 설정**: 다국어 지원 준비 (완료)

### 미구현 기능 (UI만 존재)

#### 1. 창 설정
```python
# 구현 필요: MainWindow에서 설정값 적용
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.apply_window_settings()  # 미구현

    def apply_window_settings(self):
        """설정에서 창 크기/위치 복원"""
        # TODO: settings에서 값 로드
        # TODO: 다중 모니터 환경 처리
        pass

    def closeEvent(self, event):
        """창 닫기 시 현재 크기/위치 저장"""
        # TODO: 현재 창 상태 저장
        super().closeEvent(event)
```

#### 2. 애니메이션 설정
```python
# 구현 필요: 전역 애니메이션 시스템
class AnimationManager:
    @classmethod
    def create_fade_animation(cls, widget, duration=300):
        """페이드 애니메이션 생성"""
        # TODO: 설정값 확인하여 활성화/비활성화
        pass

    @classmethod
    def create_slide_animation(cls, widget, direction='left'):
        """슬라이드 애니메이션 생성"""
        # TODO: 구현 필요
        pass
```

#### 3. 차트 설정
```python
# 구현 필요: 차트 스타일 적용
class ChartStyleManager:
    @classmethod
    def apply_chart_settings(cls, ax, chart_type='candlestick'):
        """설정에 따른 차트 스타일 적용"""
        # TODO: 캔들스틱/라인/바 차트 전환
        # TODO: 업데이트 간격 설정 적용
        pass
```

## 🎯 7규칙 전략 중심 UI 최적화

### 빠른 7규칙 구성 템플릿
```python
class Quick7RuleTemplate(QWidget):
    """기본 7규칙 전략 빠른 구성"""

    def __init__(self):
        super().__init__()
        self.setup_quick_template()

    def setup_quick_template(self):
        """원클릭으로 7규칙 구성"""
        template_button = QPushButton("기본 7규칙 전략 생성")
        template_button.clicked.connect(self.create_basic_7_rule_strategy)

    def create_basic_7_rule_strategy(self):
        """기본 7규칙 전략 자동 생성"""
        rules = [
            ("RSI 과매도 진입", "RSI < 30"),
            ("수익시 불타기", "수익률 > 3%마다 추가매수"),
            ("계획된 익절", "수익률 >= 15% 시 전량 매도"),
            ("트레일링 스탑", "최고점 대비 -5% 손절"),
            ("하락시 물타기", "손실률 -5%마다 추가매수"),
            ("급락 감지", "15분간 -10% 하락 시 전량 매도"),
            ("급등 감지", "15분간 +15% 상승 시 일부 매도")
        ]

        for rule_name, rule_desc in rules:
            self.presenter.add_predefined_rule(rule_name, rule_desc)
```

## 🧪 UI 테스트 및 검증

### 반응성 테스트
```python
def test_ui_responsiveness():
    """UI 반응성 0.5초 내 검증"""
    start_time = time.time()

    # 사용자 액션 시뮬레이션
    trigger_builder.select_base_variable("RSI")

    response_time = time.time() - start_time
    assert response_time < 0.5, f"응답 시간 초과: {response_time}초"
```

### 호환성 검증 테스트
```python
def test_compatibility_ui_integration():
    """호환성 시스템과 UI 통합 테스트"""

    # RSI 선택 시 호환 변수만 표시되는지 확인
    trigger_builder.select_base_variable("RSI")
    available_vars = trigger_builder.get_available_external_variables()

    assert "Stochastic_K" in available_vars  # 호환 변수
    assert "MACD" not in available_vars      # 비호환 변수
    assert "Volume" not in available_vars    # 비호환 변수
```

## 📚 관련 문서

- **[트리거 빌더 가이드](TRIGGER_BUILDER_GUIDE.md)**: 트리거 빌더 상세 기능
- **[전략 가이드](STRATEGY_GUIDE.md)**: 전략 시스템과 UI 연동
- **[아키텍처 가이드](ARCHITECTURE_GUIDE.md)**: DDD + MVP 패턴 설계
- **[통합 설정 관리 가이드](UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md)**: 설정 시스템

---

**🎯 핵심 목표**: 기본 7규칙 전략을 5분 내에 구성할 수 있는 직관적 UI!

**💡 UI 철학**: "복잡한 것을 단순하게, 하지만 기능은 강력하게"
