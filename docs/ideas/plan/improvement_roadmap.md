# 🚀 업비트 자동매매 시스템 개선 로드맵

## 🎯 개선 목표

**비전**: Legacy 패턴을 현대적 패턴으로 완전 전환하여 일관성 있는 아키텍처 달성
**원칙**: 기능 안정성을 유지하며 점진적 개선
**기간**: 3개월 (단계별 1개월씩)

---

## 📋 Phase 1: 의존성 주입 마이그레이션 완료 (1개월)

### 🎯 목표

Legacy resolve() 패턴을 @inject 패턴으로 100% 전환

### 📊 현재 상태 분석

#### Legacy 패턴 사용 현황

```python
# 발견된 Legacy 코드 패턴
logger.warning(f"⚠️ Legacy resolve() 호출 감지: {service_type}")

# 추정 위치
- Container.resolve() 직접 호출
- AppContext.resolve() 직접 호출
- 수동 서비스 인스턴스 생성
```

#### @inject 패턴 적용 현황

```python
# 이미 적용된 곳들
✅ MainWindow (ui/desktop/main_window.py)
✅ OrderbookPresenter
✅ DataService
✅ UseCase classes
```

### 🔧 구체적 작업 계획

#### 1.1 Legacy 호출 전면 조사 (1주)

**목표**: 모든 Legacy resolve() 호출 위치 식별

**작업**:

```powershell
# 1. Legacy 패턴 검색
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "\.resolve\("
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "container\."
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "app_context\."

# 2. @inject 미적용 클래스 식별
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "class.*Service|class.*Repository|class.*Manager"
```

**산출물**:

- `docs/ideas/plan/legacy_code_inventory.md` - 전체 현황표
- `docs/ideas/plan/injection_priority_matrix.md` - 우선순위 매트릭스

#### 1.2 핵심 서비스 우선 전환 (2주)

**우선순위**:

1. **Application Services** (가장 높음)
2. **Infrastructure Services**
3. **Repository Implementations**
4. **UI Presenters** (가장 낮음)

**전환 템플릿**:

```python
# Before (Legacy)
class TradingService:
    def __init__(self):
        container = get_app_context().container
        self.repository = container.resolve(IStrategyRepository)
        self.api_client = container.resolve(IUpbitClient)

# After (@inject)
@inject
def __init__(
    self,
    repository: IStrategyRepository = Provide["strategy_repository"],
    api_client: IUpbitClient = Provide["upbit_client"]
):
    self.repository = repository
    self.api_client = api_client
```

**검증 방법**:

```python
# 매 전환 후 실행
python run_desktop_ui.py  # UI 정상 동작 확인
pytest tests/  # 테스트 통과 확인
```

#### 1.3 Container 정리 및 최적화 (1주)

**목표**: Legacy 지원 코드 제거 및 Wiring 최적화

**작업**:

1. Legacy resolve() 메서드 제거
2. Wiring 모듈 목록 업데이트
3. Provider 등록 순서 최적화
4. 순환 의존성 검증

### 🎯 성공 기준

- [ ] Legacy resolve() 호출 0건
- [ ] 모든 서비스 @inject 패턴 적용
- [ ] Container 경고 메시지 제거
- [ ] 기존 기능 100% 정상 동작

---

## 📋 Phase 2: UI 컴포넌트 현대화 (1개월)

### 🎯 목표

Legacy UI 패턴을 DI + @asyncSlot + 전역 스타일 시스템으로 전환

### 📊 현재 상태 분석

#### Legacy UI 코드 현황

```
upbit_auto_trading/ui/desktop/screens/strategy_management/tabs/trigger_builder/
├── trigger_list_widget.py      ← "Legacy UI 기반 MVP 구현"
├── trigger_detail_widget.py    ← "Legacy UI 기반 MVP 구현"
├── trigger_builder_widget.py   ← "Legacy 레이아웃 100% 복사"
└── widgets/                    ← 관련 위젯들
```

#### 문제점 분석

1. **DI 패턴 미적용**: 서비스 수동 생성
2. **@asyncSlot 미사용**: 동기 UI 이벤트 처리
3. **하드코딩된 스타일**: setStyleSheet 직접 사용
4. **MVP 패턴 불완전**: Presenter 계층 모호함

### 🔧 구체적 작업 계획

#### 2.1 TriggerBuilder 컴포넌트 리팩터링 (2주)

**우선순위**: TriggerBuilder → TriggerList → TriggerDetail 순

**현대화 템플릿**:

```python
# Before (Legacy)
class TriggerBuilderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = TriggerService()  # 직접 생성
        self.setup_ui()

    def on_button_clicked(self):
        result = self.service.create_trigger()  # 동기 호출
        self.update_ui(result)

# After (Modern)
class TriggerBuilderWidget(QWidget):
    @inject
    def __init__(
        self,
        trigger_service: ITriggerService = Provide["trigger_service"],
        theme_service: IThemeService = Provide["theme_service"],
        parent=None
    ):
        super().__init__(parent)
        self._trigger_service = trigger_service
        self._theme_service = theme_service
        self._setup_ui()

    @asyncSlot()
    async def on_button_clicked(self):
        try:
            self.button.setEnabled(False)
            result = await self._trigger_service.create_trigger_async()
            self._update_ui(result)
        finally:
            self.button.setEnabled(True)
```

#### 2.2 전역 스타일 시스템 통합 (1주)

**목표**: 하드코딩된 setStyleSheet 제거

**작업**:

1. 위젯별 objectName 설정
2. 전역 StyleManager 적용
3. 테마 변경 이벤트 연결

#### 2.3 MVP 패턴 명확화 (1주)

**목표**: Presenter 계층 명확한 분리

**구조**:

```
View (Widget) ←→ Presenter ←→ UseCase (Application Service)
     ↓               ↓              ↓
   UI 로직        변환 로직      비즈니스 로직
```

### 🎯 성공 기준

- [ ] 모든 UI 컴포넌트 @inject 패턴 적용
- [ ] @asyncSlot으로 비동기 이벤트 처리
- [ ] 전역 스타일 시스템 100% 적용
- [ ] MVP 패턴 명확한 계층 분리

---

## 📋 Phase 3: 코드 품질 및 일관성 강화 (1개월)

### 🎯 목표

시스템 전반의 일관성 확보 및 품질 지표 개선

### 🔧 구체적 작업 계획

#### 3.1 로깅 시스템 통일 (1주)

**현재 문제**: CLI에서 print() 직접 사용

**해결책**:

```python
# Before
print("사용 가능한 명령어:")

# After
logger = create_component_logger("CLIApp")
logger.info("사용 가능한 명령어:")
```

#### 3.2 테스트 코드 작성 (2주)

**목표**: 주요 컴포넌트 테스트 커버리지 확보

**우선순위**:

1. Application Services (가장 중요)
2. Domain Services
3. Infrastructure Services
4. UI Presenters

**테스트 템플릿**:

```python
class TestTradingService:
    def setup_method(self):
        self.container = ApplicationContainer()
        self.mock_repository = Mock(spec=IStrategyRepository)
        self.container.strategy_repository.override(self.mock_repository)

    def test_execute_trade_success(self):
        # Given
        service = self.container.trading_service()

        # When
        result = service.execute_trade(command)

        # Then
        assert result.success is True
        self.mock_repository.save.assert_called_once()
```

#### 3.3 성능 모니터링 시스템 (1주)

**목표**: 런타임 성능 지표 수집

**구성 요소**:

1. AppKernel 헬스체크 시스템
2. TaskManager 성능 메트릭
3. WebSocket 연결 상태 모니터링
4. DI Container 초기화 시간 측정

### 🎯 성공 기준

- [ ] 전체 시스템 로깅 패턴 100% 통일
- [ ] 핵심 컴포넌트 테스트 커버리지 80% 이상
- [ ] 성능 모니터링 대시보드 구축
- [ ] 코드 품질 지표 A급 달성

---

## 📊 전체 로드맵 타임라인

```
Month 1: 의존성 주입 마이그레이션
├── Week 1: Legacy 코드 전면 조사
├── Week 2-3: 핵심 서비스 우선 전환
└── Week 4: Container 정리 및 최적화

Month 2: UI 컴포넌트 현대화
├── Week 1-2: TriggerBuilder 컴포넌트 리팩터링
├── Week 3: 전역 스타일 시스템 통합
└── Week 4: MVP 패턴 명확화

Month 3: 품질 및 일관성 강화
├── Week 1: 로깅 시스템 통일
├── Week 2-3: 테스트 코드 작성
└── Week 4: 성능 모니터링 시스템
```

---

## 🎯 리스크 관리

### 높은 리스크

1. **기능 회귀**: 마이그레이션 중 기존 기능 손상
   - **대응**: 단계별 테스트, 롤백 계획 수립

2. **DI 순환 의존성**: 복잡한 서비스 간 의존성
   - **대응**: 의존성 그래프 사전 분석, Lazy Provider 활용

### 중간 리스크

1. **성능 저하**: DI 오버헤드
   - **대응**: 벤치마크 측정, Singleton 패턴 적절 활용

2. **개발자 학습 곡선**: 새로운 패턴 적응
   - **대응**: 문서화, 코드 리뷰 강화

### 낮은 리스크

1. **UI 레이아웃 변경**: 스타일 시스템 변경
   - **대응**: 점진적 적용, 사용자 피드백 수집

---

## 📋 다음 문서

- `docs/ideas/plan/migration_strategy.md` - 단계별 마이그레이션 전략
- `docs/ideas/plan/long_term_vision.md` - 장기 아키텍처 비전
- `docs/ideas/plan/testing_strategy.md` - 테스트 전략 상세

---

**🎯 핵심 성공 요인**: 점진적 개선 + 기능 안정성 + 코드 일관성
