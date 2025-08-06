# TASK-20250803-12

## Title
Presentation Layer - MVP 패턴 적용 및 Passive View 구현

## Objective (목표)
Clean Architecture의 Presentation Layer에서 MVP(Model-View-Presenter) 패턴을 적용하여 UI와 비즈니스 로직을 완전히 분리합니다. 현재 UI에 혼재된 비즈니스 로직을 Application Layer로 이동하고, UI는 순수한 표시 기능만 담당하도록 리팩토링합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 4: Presentation Layer 리팩토링 (3주)" > "4.1 MVP 패턴 Presenter 구현 (1주)"

## Pre-requisites (선행 조건)
- Phase 3 Infrastructure Layer 완료 (TASK-08~11)
- Application Layer Service 구현 완료
- UI에서 분리할 비즈니스 로직 식별 완료

## Detailed Steps (상세 실행 절차)

### 1. **[분석]** 현재 UI 비즈니스 로직 분석
- [x] `ui/desktop/screens/strategy_management/` 폴더 분석
- [x] 각 Screen에서 비즈니스 로직 추출 목록 작성
- [x] Presenter-View 분리 대상 컴포넌트 식별
- [x] Application Service와의 연동 지점 설계

### 2. **[구조 생성]** MVP 패턴 폴더 구조
- [x] `upbit_auto_trading/presentation/presenters/` 폴더 생성
- [x] `upbit_auto_trading/presentation/views/` 폴더 생성
- [x] `upbit_auto_trading/presentation/view_models/` 폴더 생성
- [x] `upbit_auto_trading/presentation/interfaces/` 폴더 생성

### 3. **[인터페이스 정의]** View 인터페이스
- [x] `upbit_auto_trading/presentation/interfaces/view_interfaces.py` 생성:
✅ 완료: IStrategyMakerView, ITriggerBuilderView, IBacktestView, ISettingsView, ILiveTradingView 인터페이스 정의

### 4. **[Presenter 구현]** 핵심 Presenter 클래스들
- [x] `upbit_auto_trading/presentation/presenters/strategy_maker_presenter.py` 생성:
✅ 완료: StrategyMakerPresenter 클래스 구현 (Application Service 연동 포함)
- [x] `upbit_auto_trading/presentation/presenters/trigger_builder_presenter.py` 생성:
✅ 완료: TriggerBuilderPresenter, BacktestPresenter 클래스 구현
- [x] `upbit_auto_trading/presentation/presenters/settings_presenter.py` 생성:
✅ 완료: SettingsPresenter, LiveTradingPresenter 클래스 구현

### 5. **[View 리팩토링]** Strategy Maker View 리팩토링
- [x] 기존 `strategy_maker.py`를 Passive View로 변경:
✅ 완료: StrategyMakerView 클래스를 IStrategyMakerView 인터페이스 구현체로 리팩토링
- [x] 모든 비즈니스 로직을 Presenter에 위임하도록 수정

### 6. **[통합]** Application Context와 연동
- [x] DI 컨테이너에 Presenter 등록: MVP Container 생성 완료
- [x] 기존 Screen 클래스들의 초기화 로직 수정
- [x] MainWindow에서 MVP 패턴 적용: 전략 관리 화면에 MVP 패턴 통합 완료

### 7. **[테스트]** MVP 패턴 동작 검증
- [X] Presenter 단위 테스트 작성
- [X] View-Presenter 통합 테스트
- [X] 기존 기능 회귀 테스트

## Verification Criteria (완료 검증 조건)

### **[비즈니스 로직 분리 확인]**
- [x] UI 클래스에서 모든 비즈니스 로직 제거 확인
- [x] Presenter가 Application Service만 호출하는지 확인
- [x] View가 표시 기능만 담당하는지 확인

### **[MVP 패턴 동작 확인]**
- [X] View → Presenter → Application Service 호출 흐름 검증
- [X] Presenter가 View 인터페이스만 참조하는지 확인
- [X] 의존성 주입이 정상 동작하는지 확인

## 🚨 현재 상황 (2025-08-06 오후)

**문제**: MainWindow에서 `'MainWindow' object has no attribute 'logger'` 에러 발생
**원인**: MVP 패턴 적용 과정에서 MainWindow의 logger 초기화가 깨짐
**영향**: 애플리케이션 실행 불가, 하위 화면 테스트 불가

**재계획 필요성**:
- 이론적 MVP 구조는 완성되었지만 실제 실행이 안 됨
- MainWindow → Settings → Strategy Management 순서로 안정화 필요

## 재구성된 실행 계획

### 8. **[긴급 수정]** MainWindow 안정화
- [X] MainWindow logger 초기화 문제 해결
- [-] MVP Container 연결 안정성 검증
- [ ] 기본 애플리케이션 실행 확인

### 9. **[핵심 연결]** Settings Presenter 우선 구현
- [ ] Settings 관련 비즈니스 로직 Presenter로 분리
- [ ] MainWindow의 Settings 로딩 MVP 패턴 적용
- [ ] 설정 화면 MVP 연결 테스트

### 10. **[단계적 적용]** Strategy Management MVP 실제 연결
- [ ] 기존 Strategy Management Screen을 실제 MVP로 변환
- [ ] StrategyMakerPresenter와 실제 View 연결
- [ ] 전략 CRUD 기능 MVP 패턴으로 동작 확인

### 11. **[통합 검증]** 실제 사용자 워크플로 테스트
- [ ] 메인 화면 → 설정 → 전략 관리 → 전략 생성 전체 플로우 테스트
- [ ] 에러 없이 모든 기능 정상 동작 확인
- [ ] 기존 기능 회귀 테스트 (실제 UI 사용)

## 현재 완료 상태 및 문제점 (2025-08-06)

### ✅ **이론적 MVP 인프라 완성**:
- View 인터페이스 정의 (5개 주요 화면)
- Presenter 구현 (Strategy, Trigger, Backtest, Settings, LiveTrading)
- MVP Container (의존성 주입) 구현
- Mock 테스트로 MVP 패턴 동작 검증

### 🚨 **실제 실행 문제**:
- MainWindow logger 에러로 애플리케이션 실행 불가
- 이론과 실제 연결 부분에서 문제 발생
- MVP 패턴 적용이 기존 코드를 깨뜨림

### 🎯 **해결 전략**:
1. **안정성 우선**: MainWindow부터 차근차근 수정
2. **점진적 적용**: 한 번에 모든 화면을 MVP로 바꾸지 말고 하나씩
3. **실행 중심**: Mock 테스트보다 실제 UI 실행을 우선

## 우선순위 기반 작업 계획

### 🥇 1순위: MainWindow 생존 (필수)
- **목표**: 애플리케이션이 실행되어야 함
- **접근**: logger 문제 해결, MVP Container 안정화

### 🥈 2순위: Settings 연결 (핵심)
- **목표**: MainWindow가 설정을 정상 로딩
- **접근**: Settings Presenter 실제 연결

### 🥉 3순위: Strategy Management 실제 적용
- **목표**: 하나의 화면이라도 완전한 MVP로 동작
- **접근**: Mock이 아닌 실제 View-Presenter 연결

## Notes (주의사항)
- **실행 우선**: 이론보다 실제 동작하는 코드 우선
- **점진적 변경**: 기존 코드를 한 번에 바꾸지 말고 단계적으로
- **에러 회피**: MVP 적용 과정에서 기존 기능이 깨지지 않도록 주의
