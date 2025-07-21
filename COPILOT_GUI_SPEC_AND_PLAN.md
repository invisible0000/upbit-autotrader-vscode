# Upbit Autotrader GUI 명세 및 개발 계획

## 📋 최신 업데이트: 매매 전략 관리 V1.0.1 (2025.01.21)

### 🎯 주요 개선사항
- **조합 전략 지원**: 이산/웨이팅 조합으로 다중 전략 결합
- **고급 전략 추가**: 물타기, 불타기, 트레일링 스탑, 평균가 에버리징
- **탭 기반 UI**: 기본 전략과 조합 전략 분리 관리
- **UI 최적화**: 중복 버튼 제거, 검색/필터 기능 강화

### 🔗 관련 문서
- **상세 개발 계획**: `docs/STRATEGY_MANAGEMENT_V1.0.1_TASKS.md`
- **UI 개발 가이드**: `docs/UI_DEVELOPMENT_GUIDE.md`

## 1. 주요 화면 설계
- **메인 대시보드**: 글로벌 네비게이션(GNB), 사이드 메뉴, 포트폴리오 요약, 시장 개요, 실시간 거래 현황, 알림, 상태바
- **종목 스크리닝**: 필터 설정, 결과 테이블, 결과 저장/포트폴리오 추가/CSV 내보내기
- **매매전략 관리** 🆕: 탭 기반 (기본 전략 | 조합 전략), 8가지 전략 유형, 고급 파라미터 설정
- **백테스팅**: 전략/포트폴리오 선택, 기간/자본/수수료 입력, 실행/결과/성과지표/거래내역/차트
- **실시간 거래**: 활성 전략/포지션, 수동 주문 입력/실행, 실시간 시장 데이터/알림
- **포트폴리오 구성**: 코인/비중/성과지표, 추가/제거/비중 조정
- **설정/로그인**: API키 입력/저장/테스트, DB/알림/테마 설정, 로그인/세션 관리

## 2. 코드 샘플
```python
# 대시보드 화면 예시
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from .common.components import CardWidget, StyledTableWidget

class DashboardScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.portfolio_card = CardWidget("포트폴리오 요약")
        self.market_card = CardWidget("시장 개요")
        self.active_positions_card = CardWidget("실시간 거래 현황")
        self.portfolio_card.add_widget(StyledTableWidget(rows=5, columns=3))
        self.market_card.add_widget(StyledTableWidget(rows=10, columns=4))
        self.active_positions_card.add_widget(StyledTableWidget(rows=5, columns=5))
        layout.addWidget(self.portfolio_card)
        layout.addWidget(self.market_card)
        layout.addWidget(self.active_positions_card)
```

## 3. 개발 일정(예시)
| 주차 | 주요 목표 |
|------|-----------------------------|
| 1주차 | 메인 대시보드/설정/로그인 화면 완성, 공통 컴포넌트 정비 |
| 2주차 | 종목 스크리닝/매매전략 관리 화면 구현, 데이터 연동 |
| 3주차 | 백테스팅/실시간 거래/포트폴리오 화면 구현, 이벤트 처리 |
| 4주차 | 테마/UX/반응형/접근성 개선, 통합 테스트/버그 수정 |
| 5주차 | 사용자 피드백 반영, 문서화, 최종 배포 준비 |

## 4. 참고 문서/명세
- `reference/ui_spec_*.md`: 각 화면별 UI 명세
- `upbit_auto_trading/docs/ui_guide.md`: 전체 UI 구조/원칙/컴포넌트 설명
- `upbit_auto_trading/ui/desktop/common/components.py`: 공통 UI 컴포넌트 코드
- `upbit_auto_trading/ui/desktop/main.py`, `main_window.py`: 메인 대시보드 및 화면 전환/상태 관리

## 5. 화면별 상세 설계 및 추가 코드 샘플

### 1) 대시보드
- 구성: 포트폴리오 요약(CardWidget+StyledTableWidget), 시장 개요(CardWidget+StyledTableWidget), 실시간 거래 현황(CardWidget+StyledTableWidget), 알림(별도 위젯)
- 주요 이벤트: 화면 전환, 실시간 데이터 갱신, 알림 표시
```python
class DashboardScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.portfolio_card = CardWidget("포트폴리오 요약")
        self.market_card = CardWidget("시장 개요")
        self.active_positions_card = CardWidget("실시간 거래 현황")
        self.portfolio_card.add_widget(StyledTableWidget(rows=5, columns=3))
        self.market_card.add_widget(StyledTableWidget(rows=10, columns=4))
        self.active_positions_card.add_widget(StyledTableWidget(rows=5, columns=5))
        layout.addWidget(self.portfolio_card)
        layout.addWidget(self.market_card)
        layout.addWidget(self.active_positions_card)
```

### 2) 종목 스크리닝
- 구성: 필터 설정(StyledComboBox, StyledCheckBox 등), 결과 테이블(StyledTableWidget), 결과 저장/포트폴리오 추가/CSV 내보내기(PrimaryButton)
- 주요 이벤트: 필터 변경 시 실시간 결과 갱신, 결과 저장/내보내기
```python
class ScreenerScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.filter_box = StyledComboBox(items=["거래량", "변동성", "추세"])
        self.result_table = StyledTableWidget(rows=20, columns=6)
        self.save_button = PrimaryButton("결과 저장")
        layout.addWidget(self.filter_box)
        layout.addWidget(self.result_table)
        layout.addWidget(self.save_button)
```

### 3) 매매전략 관리 🆕 V1.0.1 개선
- **기존**: 단일 화면 3분할 구조 (목록-에디터-상세)
- **개선**: 탭 기반 분리 (기본 전략 | 조합 전략)
- **전략 유형 확장**: 4개 → 8개 (물타기, 불타기, 트레일링 스탑, 평균가 에버리징 추가)
- **조합 전략**: 이산 조합(AND/OR/MAJORITY), 웨이팅 조합(가중평균)

```python
class StrategyManagementScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # 검색/필터 툴바 (중복 버튼 제거)
        self.toolbar = self.create_improved_toolbar()
        layout.addWidget(self.toolbar)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        
        # 기본 전략 탭 (기존 UI 개선)
        basic_tab = BasicStrategyTab()
        self.tab_widget.addTab(basic_tab, "🔧 기본 전략")
        
        # 조합 전략 탭 (신규)
        composite_tab = CompositeStrategyTab()
        self.tab_widget.addTab(composite_tab, "🔗 조합 전략")
        
        layout.addWidget(self.tab_widget)

class CompositeStrategyTab(QWidget):
    """조합 전략 전용 탭"""
    def __init__(self):
        super().__init__()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 조합 전략 목록 (25%)
        self.composite_list = CompositeStrategyList()
        splitter.addWidget(self.composite_list)
        
        # 조합 에디터 (50%)
        self.composite_editor = CompositeStrategyEditor()
        splitter.addWidget(self.composite_editor)
        
        # 성과 비교 패널 (25%)
        self.performance_panel = PerformanceComparisonPanel()
        splitter.addWidget(self.performance_panel)
        
        splitter.setSizes([250, 500, 250])
```

**고급 전략 파라미터 예시:**
```python
# 물타기 전략 파라미터 UI
class DollarCostAveragingForm(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # 기본 설정
        self.initial_ratio = QDoubleSpinBox()  # 초기 투자 비율
        self.additional_count = QSpinBox()     # 추가 매수 횟수
        
        # 추가 매수 조건
        self.drop_thresholds = QLineEdit()     # 하락률 기준점 [-5,-10,-15]
        self.investment_ratios = QLineEdit()   # 추가 투자 비율 [0.2,0.25,0.25]
        
        # 익절/손절 설정
        self.profit_target = QDoubleSpinBox()  # 목표 수익률
        self.stop_loss = QDoubleSpinBox()      # 절대 손절선
        self.max_holding_days = QSpinBox()     # 최대 보유 기간
```

### 4) 백테스팅
- 구성: 전략/포트폴리오 선택(StyledComboBox), 기간/자본/수수료 입력(StyledLineEdit), 실행/결과/성과지표/거래내역/차트(StyledTableWidget, CardWidget)
- 주요 이벤트: 백테스트 실행, 결과 표시/저장
```python
class BacktestingScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.strategy_selector = StyledComboBox(items=["전략1", "전략2"])
        self.param_input = StyledLineEdit("기간/자본/수수료 입력")
        self.run_button = PrimaryButton("백테스트 실행")
        self.result_card = CardWidget("백테스트 결과")
        layout.addWidget(self.strategy_selector)
        layout.addWidget(self.param_input)
        layout.addWidget(self.run_button)
        layout.addWidget(self.result_card)
```

### 5) 실시간 거래
- 구성: 활성 전략/포지션(StyledTableWidget), 수동 주문 입력/실행(StyledLineEdit, PrimaryButton), 실시간 시장 데이터/알림(CardWidget)
- 주요 이벤트: 주문 실행, 실시간 데이터 갱신, 알림 표시

### 6) 포트폴리오 구성
- 구성: 코인/비중/성과지표(StyledTableWidget), 추가/제거/비중 조정(PrimaryButton, SecondaryButton)
- 주요 이벤트: 포트폴리오 수정/저장

### 7) 설정/로그인
- 구성: API키 입력/저장/테스트(StyledLineEdit, PrimaryButton), DB/알림/테마 설정(StyledComboBox, StyledCheckBox), 로그인/세션 관리
- 주요 이벤트: 로그인, 설정 저장/적용

---

## 6. 개발 일정 세분화 및 역할 분담(예시)
| 주차 | 주요 목표 | 담당 역할 |
|------|-----------------------------|----------------|
| 1주차 | 대시보드/설정/로그인 화면, 공통 컴포넌트 | UI/UX, 백엔드 연동, 테스트 |
| 2주차 | 스크리너/전략관리 화면, 데이터 연동 | UI/UX, 데이터 처리, 테스트 |
| 3주차 | 백테스팅/실시간 거래/포트폴리오 화면 | UI/UX, 이벤트 처리, 테스트 |
| 4주차 | 테마/UX/반응형/접근성 개선, 통합 테스트 | UI/UX, QA, 문서화 |
| 5주차 | 피드백 반영, 최종 배포/문서화 | UI/UX, QA, 문서화 |

---

세부 설계, 코드 샘플, 일정, 역할 분담은 실제 팀/진행 상황에 맞게 조정 가능합니다. 추가 요청 시 더 상세한 문서화 및 샘플 제공 가능합니다.
