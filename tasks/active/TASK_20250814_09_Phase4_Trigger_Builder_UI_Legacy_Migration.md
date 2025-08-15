# 📋 TASK_20250814_09: Phase 4 - 기존 UI 기반 트리거 빌더 스크린 재구현

## 🎯 목표
기존 트리거 빌더 UI를 철저하게 따라하여 새로운 DDD 아키텍처로 재구현
Legacy 파일들을 기반으로 UI 설정을 그대로 복사하여 완전 동일한 레이아웃 구현

---

## 🚀 **전략 및 원칙**

### 📐 **UI 레이아웃 원칙**
1. **윈도우 크기 자동 대응**: 특별한 크기 제한 없이 상위 레이아웃에만 영향 받도록 제어
2. **크기 고정 최소화**: 모든 과정 완료 후 필요시에만 할당 또는 재사용 시 상위 다이얼로그 박스 크기용으로만 사용
3. **완전 호환성**: 기존 스크린샷과 100% 동일한 UI 구현

### 🔄 **Legacy 마이그레이션 + DDD 패턴 준수 전략**
1. **기존 DDD 구조 완전 활용**: Phase 1-3에서 완성된 Domain/Infrastructure/Application Layer 그대로 사용
2. **MVP 패턴 엄격 적용**: UI Layer에서만 Presenter ↔ View Interface ↔ Widget 구조 적용
3. **DTO 시스템 완전 연동**: 기존 TradingVariableDTO들을 Presenter에서 적극 활용
4. **UI 전용 유틸리티 분리**: services → utils로 이동하여 DDD 위반 방지
5. **Legacy UI 100% 복사**: DDD 패턴 적용과 무관하게 UI는 완전 동일하게 구현

---

## 📊 **Phase 4 상세 작업 계획**

### [ ] 4.0 준비 작업 - Legacy 파일 조사 및 폴더 구조 생성

#### [ ] 4.0.1 기존 UI 파일 위치 확인
- [ ] **메인 스크린 위치**: `upbit_auto_trading/ui/desktop/screens/strategy_management_backup/trigger_builder/trigger_builder_screen.py`
- [ ] **핵심 위젯들**: `trigger_builder/components/core/` 폴더 내 8개 컴포넌트
- [ ] **공유 위젯들**: `trigger_builder/components/shared/` 폴더 내 컴포넌트들
- [ ] **기존 스크린샷**: 참조용 이미지 파일 위치 확인

#### [ ] 4.0.2 DDD 패턴 준수한 새로운 폴더 구조 생성
```
upbit_auto_trading/ui/desktop/screens/strategy_management/
├── strategy_management_screen.py       # 메인 전략 관리 화면 (탭 컨테이너)
├── tabs/                              # 각 탭별 구현
│   ├── trigger_builder/               # 트리거 빌더 탭
│   │   ├── trigger_builder_tab.py     # 트리거 빌더 메인 탭 (View)
│   │   ├── trigger_builder_tab_legacy.py  # Legacy 보존
│   │   ├── presenters/               # MVP Presenter Layer
│   │   │   ├── trigger_builder_presenter.py     # 메인 Presenter
│   │   │   ├── trigger_list_presenter.py        # 트리거 목록 Presenter
│   │   │   ├── trigger_detail_presenter.py      # 트리거 상세 Presenter
│   │   │   └── condition_builder_presenter.py   # 컨디션 빌더 Presenter (shared 사용)
│   │   ├── views/                    # MVP View Interface Layer
│   │   │   ├── i_trigger_builder_view.py        # 메인 View Interface
│   │   │   ├── i_trigger_list_view.py           # 트리거 목록 View Interface
│   │   │   └── i_trigger_detail_view.py         # 트리거 상세 View Interface
│   │   └── widgets/                  # 구체적인 UI 구현 (View 구현체)
│   │       ├── trigger_list_widget.py           # ITriggerListView 구현
│   │       ├── trigger_detail_widget.py         # ITriggerDetailView 구현
│   │       └── trigger_composer_widget.py       # 트리거 조합기
│   ├── strategy_maker/               # 전략 메이커 탭
│   │   ├── strategy_maker_tab.py     # 전략 메이커 메인 탭
│   │   ├── presenters/
│   │   │   └── strategy_maker_presenter.py
│   │   ├── views/
│   │   │   └── i_strategy_maker_view.py
│   │   ├── widgets/                  # 전략 메이커 전용 위젯들
│   │   │   ├── strategy_list_widget.py
│   │   │   └── strategy_detail_widget.py
│   │   └── dialogs/                  # 재사용 컴포넌트의 다이얼로그 래퍼
│   │       ├── condition_edit_dialog.py  # shared 컴포넌트 래핑
│   │       └── mini_chart_dialog.py      # shared 컴포넌트 래핑
│   └── portfolio_analyzer/           # 포트폴리오 분석 탭 (향후)
├── shared/                           # 탭 간 공유 컴포넌트 (UI Layer 전용)
│   ├── components/                   # 재사용 가능한 UI 컴포넌트
│   │   ├── condition_builder/        # 컨디션 빌더 (재사용 핵심)
│   │   │   ├── condition_builder_widget.py     # 메인 위젯 (View 구현체)
│   │   │   ├── variable_selector_widget.py     # 변수 선택기
│   │   │   ├── parameter_input_widget.py       # 파라미터 입력
│   │   │   └── condition_preview_widget.py     # 조건 미리보기
│   │   ├── mini_chart/              # 미니 차트 (재사용 핵심)
│   │   │   ├── mini_chart_widget.py            # 메인 차트 위젯
│   │   │   ├── simulation_control_widget.py    # 시뮬레이션 컨트롤
│   │   │   └── simulation_result_widget.py     # 시뮬레이션 결과
│   │   └── compatibility/           # 호환성 검증 위젯
│   │       ├── compatibility_checker_widget.py
│   │       └── compatibility_result_widget.py
│   ├── presenters/                  # 공유 Presenter들 (MVP Pattern)
│   │   ├── condition_builder_presenter.py      # 컨디션 빌더 Presenter
│   │   ├── mini_chart_presenter.py             # 미니 차트 Presenter
│   │   └── compatibility_presenter.py          # 호환성 Presenter
│   ├── views/                       # 공유 View Interface들
│   │   ├── i_condition_builder_view.py         # 컨디션 빌더 View Interface
│   │   ├── i_mini_chart_view.py                # 미니 차트 View Interface
│   │   └── i_compatibility_view.py             # 호환성 View Interface
│   ├── dialogs/                     # 재사용 가능한 다이얼로그들
│   │   ├── condition_builder_dialog.py         # 다이얼로그 모드 래퍼
│   │   └── mini_chart_dialog.py                # 다이얼로그 모드 래퍼
│   └── utils/                       # UI Layer 전용 유틸리티
│       ├── dialog_size_manager.py              # UI 전용 유틸
│       ├── component_state_manager.py          # UI 전용 상태 관리
│       └── theme_adapter.py                    # UI 전용 테마 어댑터
└── legacy/                          # Legacy 파일 보관소
    ├── trigger_builder_screen_legacy.py
    └── widgets_legacy/              # Legacy 위젯들
        ├── condition_dialog_legacy.py
        ├── trigger_list_widget_legacy.py
        ├── simulation_control_widget_legacy.py
        └── ... (모든 legacy 위젯들)

# 🚨 중요: UI Layer 밖의 기존 DDD 구조는 그대로 사용
upbit_auto_trading/
├── domain/trigger_builder/          # ✅ 이미 완성됨 (Phase 1)
│   ├── entities/                    # TradingVariable, Condition
│   ├── value_objects/               # VariableParameter, ConditionValue 등
│   ├── services/                    # VariableCompatibilityService 등
│   └── repositories/                # Repository Interfaces
├── infrastructure/repositories/     # ✅ 이미 완성됨 (Phase 2)
│   └── sqlite_trading_variable_repository.py
└── application/                     # ✅ 이미 완성됨 (Phase 3)
    ├── use_cases/trigger_builder/   # TradingVariable UseCases
    └── dto/trigger_builder/         # TradingVariable DTOs
```

### 🎯 **DDD + MVP + DTO 패턴 준수 원칙**

#### 🏗️ **DDD 4계층 엄격 준수**
1. **Domain Layer**: 이미 완성 ✅ - 비즈니스 로직, Entity, Value Object, Domain Service
2. **Infrastructure Layer**: 이미 완성 ✅ - Repository 구현체, Database 연동
3. **Application Layer**: 이미 완성 ✅ - UseCase, DTO
4. **UI Layer**: Phase 4에서 구현 🔄 - Presenter, View, Widget

#### 🎨 **MVP 패턴 엄격 적용**
- **Presenter**: 비즈니스 로직 처리, UseCase 호출, DTO 변환
- **View Interface**: UI 추상화, 테스트 가능성 확보
- **View 구현체 (Widget)**: 순수 UI 로직만, Passive View 패턴

#### 📦 **DTO 패턴 완전 활용**
- **UI → Presenter**: UI 이벤트 데이터
- **Presenter → UseCase**: 기존 DTO 시스템 활용 (TradingVariableListDTO 등)
- **UseCase → Presenter**: 기존 DTO 시스템 활용
- **Presenter → View**: View 전용 ViewModel DTO

#### [ ] 4.0.3 기존 DDD 구조 활용 준비 (Phase 1-3 완성 구조)
- [ ] **Domain Layer 확인**: `upbit_auto_trading/domain/trigger_builder/` 구조 검토
  - ✅ Entities: TradingVariable, Condition
  - ✅ Value Objects: VariableParameter, UnifiedParameter, ConditionValue
  - ✅ Services: VariableCompatibilityService, ConditionValidationService
  - ✅ Repository Interfaces: ITradingVariableRepository, IConditionRepository
- [ ] **Infrastructure Layer 확인**: Repository 구현체들 검토
  - ✅ SqliteTradingVariableRepository 완성
- [ ] **Application Layer 확인**: UseCase와 DTO 시스템 검토
  - ✅ UseCases: ListTradingVariablesUseCase, GetVariableParametersUseCase 등
  - ✅ DTOs: TradingVariableListDTO, TradingVariableDetailDTO 등
- [ ] **RepositoryContainer 확인**: DI 컨테이너 UseCase 연결 확인

#### [ ] 4.0.4 Legacy 파일 마이그레이션 준비 (UI Layer만)
- [ ] **전략 관리 메인 화면**: 기존 strategy_management 관련 파일들 → legacy로 복사
- [ ] **트리거 빌더 탭**: 기존 `trigger_builder_screen.py` → `trigger_builder_tab_legacy.py`로 복사
- [ ] **핵심 위젯들**: 기존 `components/core/` 전체 → `legacy/widgets_legacy/`로 복사
- [ ] **공유 위젯들**: 기존 `components/shared/` 전체 → `legacy/shared_legacy/`로 복사
- [ ] **재사용 컴포넌트 식별**: 컨디션 빌더, 미니 차트 관련 파일들을 shared/components로 분류

---

### [ ] 4.1 메인 스크린 마이그레이션 - trigger_builder_screen.py

#### [ ] 4.1.1 Legacy 메인 스크린 분석
- [ ] **레이아웃 구조 분석**: 2x3 그리드 레이아웃 상세 분석
- [ ] **위젯 배치 분석**: 각 영역별 위젯 배치 및 크기 비율 분석
- [ ] **스타일 설정 분석**: QSS 스타일, 색상, 폰트, 간격 등 모든 UI 설정 추출
- [ ] **이벤트 연결 분석**: 시그널/슬롯 연결 패턴 분석

#### [ ] 4.1.2 새로운 Main View 생성
- [ ] **TriggerBuilderView** 클래스 생성 (MVP View)
- [ ] **레이아웃 그대로 복사**: Legacy의 그리드 레이아웃 설정 100% 복사
- [ ] **스타일 그대로 복사**: 모든 QSS 설정 그대로 적용
- [ ] **위젯 placeholder**: 각 영역에 임시 QLabel로 위치 확인

#### [ ] 4.1.3 MVP + DTO 연결 패턴 구현
- [ ] **Presenter 생성**: `TriggerBuilderPresenter` 클래스 생성
  ```python
  class TriggerBuilderPresenter:
      def __init__(self,
                   view: ITriggerBuilderView,
                   list_variables_usecase: ListTradingVariablesUseCase,
                   get_variable_details_usecase: GetVariableParametersUseCase):
          self._view = view
          self._list_variables_usecase = list_variables_usecase
          # UseCase 주입으로 Application Layer 연결
  ```
- [ ] **View Interface 정의**: `ITriggerBuilderView` 인터페이스 정의
  ```python
  from abc import ABC, abstractmethod

  class ITriggerBuilderView(ABC):
      @abstractmethod
      def display_variables(self, variables_dto: TradingVariableListDTO):
          pass

      @abstractmethod
      def show_variable_details(self, details_dto: TradingVariableDetailDTO):
          pass
  ```
- [ ] **DTO 활용**: 기존 Application Layer DTO 시스템 완전 활용
  - `TradingVariableListDTO` → UI 변수 목록 표시
  - `TradingVariableDetailDTO` → UI 변수 상세 표시
  - `VariableSearchRequestDTO` → UI 검색 요청

---

### [ ] 4.2 핵심 위젯 마이그레이션 (widgets 폴더 사용)

#### [ ] 4.2.1 ConditionBuilderWidget (컨디션 빌더 - shared/components/condition_builder/)
- [ ] **Legacy 분석**: `condition_dialog.py` → `condition_dialog_legacy.py`
- [ ] **공유 컴포넌트 생성**: `shared/components/condition_builder/condition_builder_widget.py`
- [ ] **UI 레이아웃 복사**:
  - 변수 선택 콤보박스 위치 및 크기
  - 파라미터 입력 영역 레이아웃
  - 조건 생성 버튼 배치
  - 미리보기 영역 설정
- [ ] **스타일 복사**: 모든 QSS 스타일 그대로 적용
- [ ] **MVP 적용**: ConditionBuilderPresenter와 연결

#### [ ] 4.2.2 TriggerListWidget (트리거 목록 - widgets/trigger_list_widget.py)
- [ ] **Legacy 분석**: `trigger_list_widget.py` → `trigger_list_widget_legacy.py`
- [ ] **위젯 생성**: `tabs/trigger_builder/widgets/trigger_list_widget.py`
- [ ] **UI 레이아웃 복사**:
  - QTreeWidget 설정 및 컬럼 구성
  - 컨텍스트 메뉴 설정
  - 툴바 버튼 배치
- [ ] **스타일 복사**: 트리 뷰 스타일, 선택 색상 등
- [ ] **MVP 적용**: TriggerListPresenter와 연결

#### [ ] 4.2.3 SimulationControlWidget (시뮬레이션 컨트롤 - shared/components/mini_chart/)
- [ ] **Legacy 분석**: `simulation_control_widget.py` → `simulation_control_widget_legacy.py`
- [ ] **공유 컴포넌트 생성**: `shared/components/mini_chart/simulation_control_widget.py`
- [ ] **UI 레이아웃 복사**:
  - 데이터 소스 선택 콤보박스
  - 기간 설정 위젯들
  - 실행 버튼 및 진행바
- [ ] **스타일 복사**: 버튼 스타일, 진행바 색상 등
- [ ] **MVP 적용**: SimulationControlPresenter와 연결

#### [ ] 4.2.4 ConditionDetailWidget (컨디션 상세 - shared/components/condition_builder/)
- [ ] **Legacy 분석**: `condition_storage.py` 관련 부분 분석
- [ ] **공유 컴포넌트 생성**: `shared/components/condition_builder/condition_preview_widget.py`
- [ ] **UI 레이아웃 복사**:
  - 조건 미리보기 영역
  - 호환성 검증 결과 표시
  - 파라미터 상세 설정 영역
- [ ] **스타일 복사**: 텍스트 색상, 배경색 등
- [ ] **MVP 적용**: ConditionDetailPresenter와 연결

#### [ ] 4.2.5 TriggerDetailWidget (트리거 상세 - widgets/trigger_detail_widget.py)
- [ ] **Legacy 분석**: `trigger_detail_widget.py` → `trigger_detail_widget_legacy.py`
- [ ] **위젯 생성**: `tabs/trigger_builder/widgets/trigger_detail_widget.py`
- [ ] **UI 레이아웃 복사**:
  - 트리거 정보 표시 영역
  - 실행 코드 텍스트 에디터
  - 성능 지표 표시 영역
- [ ] **스타일 복사**: 코드 하이라이팅, 폰트 설정 등
- [ ] **MVP 적용**: TriggerDetailPresenter와 연결

#### [ ] 4.2.6 SimulationResultWidget (시뮬레이션 결과 - shared/components/mini_chart/)
- [ ] **Legacy 분석**: `simulation_result_widget.py` → `simulation_result_widget_legacy.py`
- [ ] **공유 컴포넌트 생성**: `shared/components/mini_chart/simulation_result_widget.py`
- [ ] **UI 레이아웃 복사**:
  - matplotlib 차트 영역 설정
  - 결과 테이블 레이아웃
  - 탭 위젯 구성
- [ ] **스타일 복사**: 차트 배경, 테이블 헤더 등
- [ ] **MVP 적용**: SimulationResultPresenter와 연결

#### [ ] 4.2.7 ParameterInputWidget (파라미터 입력 - shared/components/condition_builder/)
- [ ] **Legacy 분석**: `parameter_widgets.py` → `parameter_widgets_legacy.py`
- [ ] **공유 컴포넌트 생성**: `shared/components/condition_builder/parameter_input_widget.py`
- [ ] **UI 레이아웃 복사**:
  - 동적 파라미터 입력 필드 생성
  - 검증 메시지 표시 영역
  - 기본값 복원 버튼
- [ ] **스타일 복사**: 입력 필드 스타일, 오류 색상 등
- [ ] **MVP 적용**: ParameterInputPresenter와 연결

#### [ ] 4.2.8 VariableSelectorWidget (변수 선택 - shared/components/condition_builder/)
- [ ] **Legacy 분석**: `variable_definitions.py` → `variable_definitions_legacy.py`
- [ ] **공유 컴포넌트 생성**: `shared/components/condition_builder/variable_selector_widget.py`
- [ ] **UI 레이아웃 복사**:
  - 카테고리별 트리 구조
  - 검색 입력 필드
  - 즐겨찾기 버튼들
- [ ] **스타일 복사**: 트리 아이템 스타일, 아이콘 등
- [ ] **MVP 적용**: VariableSelectorPresenter와 연결

---

### [ ] 4.3 공유 컴포넌트 vs 전용 위젯 구분

#### [ ] 4.3.1 공유 컴포넌트 (shared/components/) - 재사용 가능
- [ ] **컨디션 빌더 그룹**:
  - `condition_builder_widget.py` - 메인 컨디션 빌더
  - `variable_selector_widget.py` - 변수 선택기
  - `parameter_input_widget.py` - 파라미터 입력
  - `condition_preview_widget.py` - 조건 미리보기
- [ ] **미니 차트 그룹**:
  - `mini_chart_widget.py` - 메인 차트 위젯
  - `simulation_control_widget.py` - 시뮬레이션 컨트롤
  - `simulation_result_widget.py` - 시뮬레이션 결과
- [ ] **호환성 검증 그룹**:
  - `compatibility_checker_widget.py` - 호환성 체크
  - `compatibility_result_widget.py` - 호환성 결과

#### [ ] 4.3.2 전용 위젯 (tabs/*/widgets/) - 탭별 전용
- [ ] **트리거 빌더 전용**:
  - `trigger_list_widget.py` - 트리거 목록 관리
  - `trigger_detail_widget.py` - 트리거 상세 정보
  - `trigger_composer_widget.py` - 트리거 조합기
- [ ] **전략 메이커 전용**:
  - `strategy_list_widget.py` - 전략 목록 관리
  - `strategy_detail_widget.py` - 전략 상세 정보

#### [ ] 4.3.3 Legacy 위젯 분류 및 마이그레이션
- [ ] **호환성 검증**: `compatibility_validator.py` → shared/components/compatibility/
- [ ] **차트 시각화**: `chart_visualizer.py` → shared/components/mini_chart/
- [ ] **기타 공유 요소들**: shared/components로 분류 후 마이그레이션

---

### [ ] 4.4 UI 통합 및 테스트

#### [ ] 4.4.1 레이아웃 통합 테스트
- [ ] **메인 스크린 실행**: 새로운 trigger_builder_screen.py 실행
- [ ] **위젯 배치 확인**: 2x3 그리드의 각 영역별 위젯 정상 배치 확인
- [ ] **크기 조절 테스트**: 윈도우 크기 변경 시 자동 대응 확인

#### [ ] 4.4.2 스크린샷 비교 검증
- [ ] **기존 스크린샷 준비**: Legacy UI 스크린샷 캡처
- [ ] **새 UI 스크린샷**: 새로 구현한 UI 스크린샷 캡처
- [ ] **픽셀 단위 비교**: 레이아웃, 색상, 폰트, 간격 등 상세 비교
- [ ] **차이점 문서화**: 발견된 차이점들 상세 기록

#### [ ] 4.4.3 실패 시 롤백 대응
- [ ] **차이점 발견 시**: 새로 생성한 파일들 삭제
- [ ] **Legacy 직접 수정**: legacy 파일을 직접 수정하여 DDD 패턴 적용
- [ ] **점진적 리팩터링**: UI 변경 없이 내부 구조만 DDD로 전환

---

### [ ] 4.5 DDD 패턴 통합

#### [ ] 4.5.1 Presenter 레이어 완성
- [ ] **비즈니스 로직 분리**: 모든 UI 로직에서 비즈니스 로직 분리
- [ ] **UseCase 연결**: Application Layer의 UseCase들과 연결
- [ ] **이벤트 처리**: UI 이벤트를 Presenter에서 처리

#### [ ] 4.5.2 View 인터페이스 정의
- [ ] **IView 인터페이스들**: 각 위젯별 View 인터페이스 정의
- [ ] **Passive View 패턴**: View는 단순 표시만 담당
- [ ] **테스트 가능성**: Mock View로 테스트 가능한 구조

#### [ ] 4.5.3 의존성 주입 설정
- [ ] **Repository 주입**: Presenter에 Repository 주입
- [ ] **UseCase 주입**: 각 Presenter에 필요한 UseCase 주입
- [ ] **Service 주입**: Domain Service들 주입

---

### [ ] 4.6 성능 및 품질 검증

#### [ ] 4.6.1 메모리 사용량 테스트
- [ ] **메모리 프로파일링**: UI 실행 시 메모리 사용량 측정
- [ ] **메모리 누수 검사**: 위젯 생성/삭제 반복 시 누수 확인
- [ ] **최적화 적용**: 필요시 캐싱 및 지연 로딩 적용

#### [ ] 4.6.2 응답성 테스트
- [ ] **UI 반응 속도**: 버튼 클릭, 입력 필드 등 반응 속도 측정
- [ ] **데이터 로딩 시간**: 변수 목록, 트리거 목록 로딩 시간 측정
- [ ] **시뮬레이션 실행**: 백테스팅 실행 시 UI 블로킹 여부 확인

#### [ ] 4.6.3 테마 시스템 통합
- [ ] **다크/라이트 모드**: 기존 테마 시스템과 완전 호환 확인
- [ ] **동적 테마 변경**: 런타임 중 테마 변경 정상 동작 확인
- [ ] **차트 테마 연동**: matplotlib 차트 테마 자동 변경 확인

---

## 📋 체크리스트

### 🏗️ 폴더 구조 및 파일 준비
- [ ] 새로운 trigger_builder 폴더 구조 생성 완료
- [ ] Legacy 파일들 모두 _legacy 접미사로 보존 완료
- [ ] 기존 스크린샷 및 참조 자료 준비 완료

### 🎨 UI 마이그레이션 완성도
- [ ] 메인 스크린 레이아웃 100% 동일 구현
- [ ] 8개 핵심 위젯 모두 완전 마이그레이션
- [ ] 모든 스타일 (QSS, 색상, 폰트) 그대로 적용
- [ ] 윈도우 크기 변경 시 자동 대응 정상 동작

### 🔧 DDD 패턴 적용
- [ ] MVP 패턴 완전 적용 (Passive View)
- [ ] Presenter에서 모든 비즈니스 로직 처리
- [ ] UseCase와 Repository 정상 연결
- [ ] View 인터페이스 완전 분리

### 🏗️ DDD + MVP + DTO 패턴 준수 확인
- [ ] **Domain Layer 순수성**: UI Layer에서 Domain Entity 직접 사용 금지
- [ ] **Infrastructure 격리**: UI에서 Repository 직접 접근 금지, Presenter를 통해서만 UseCase 호출
- [ ] **Application UseCase 활용**: 모든 비즈니스 로직은 기존 UseCase 통해 처리
- [ ] **DTO 완전 활용**: UI ↔ Application 간 데이터 교환은 반드시 DTO 사용
- [ ] **MVP 패턴 완전 적용**: View는 Passive, Presenter가 모든 로직 처리
- [ ] **UI 전용 요소 분리**: Theme, Dialog Size 등은 utils/로 분리하여 DDD 위반 방지

### 🧪 품질 및 성능
- [ ] 스크린샷 비교로 100% 동일성 확인
- [ ] 메모리 누수 없음
- [ ] UI 응답성 기존 대비 동일 또는 향상
- [ ] 테마 시스템 완전 호환

### 🔄 롤백 대응
- [ ] 실패 시 롤백 절차 준비
- [ ] Legacy 직접 수정 대안 준비
- [ ] 점진적 리팩터링 계획 수립

---

## 🎯 성공 기준

### 🔥 최우선 성공 기준
1. **완전 동일 UI**: 기존 스크린샷과 픽셀 단위 동일성
2. **자동 크기 대응**: 윈도우 크기 변경 시 완벽한 자동 조정
3. **DDD 패턴**: MVP + UseCase + Repository 완전 적용
4. **성능 유지**: 기존 대비 동일하거나 향상된 성능

### 🎨 UI 품질 기준
```
레이아웃 검증:
✅ 2x3 그리드 완전 동일
✅ 각 위젯 크기 비율 동일
✅ 간격 및 여백 픽셀 단위 동일
✅ 스크롤바, 버튼 위치 완전 동일

스타일 검증:
✅ 색상 RGB 값 완전 동일
✅ 폰트 크기 및 타입 동일
✅ 테두리, 그림자 효과 동일
✅ 호버, 클릭 효과 동일
```

### 🔧 아키텍처 품질 기준
```
DDD 패턴:
✅ Domain Layer 순수성 유지
✅ Infrastructure 의존성 격리
✅ Application UseCase 완전 활용
✅ UI Presenter MVP 패턴 적용

성능 기준:
✅ 초기 로딩: < 2초
✅ 위젯 전환: < 100ms
✅ 데이터 로딩: < 500ms
✅ 메모리 사용량: 기존 대비 +10% 이내
```

---

**📌 핵심 전략**: Legacy UI를 100% 그대로 따라하되, 내부는 완전한 DDD 아키텍처로 재구현하여 향후 확장성과 재사용성을 확보!

**🎯 최종 목표**: 사용자는 UI 변화를 전혀 느끼지 못하지만, 개발자는 완전히 새로운 현대적 아키텍처를 얻는 것!
