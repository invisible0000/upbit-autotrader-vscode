# 매매 전략 관리 기능 심층 분석 문서

## 1. 문서 개요

본 문서는 `upbit_auto_trading` 프로젝트의 매매 전략 관리 기능에 대한 심층 분석 결과를 담고 있습니다. `strategy_management_screen.py` 파일을 시작으로, 관련 UI 컴포넌트, 비즈니스 로직, 아키텍처 패턴 등을 추적하여 기능의 의도와 구현 로직을 상세히 설명합니다.

### 1.1. 목적
사용자가 자신만의 매매 전략을 생성, 관리, 시뮬레이션할 수 있도록 하는 UI 및 백엔드 로직의 구조와 작동 방식을 이해하고 문서화합니다.

### 1.2. 분석 대상
*   `strategy_management_screen.py`
*   `trigger_builder_tab.py`
*   `i_trigger_builder_view.py`
*   `trigger_builder_presenter.py`
*   `trigger_builder_widget.py`
*   `condition_builder_widget.py`
*   관련 UseCase, DTO, Repository (추론 기반)

### 1.3. 핵심 아키텍처 패턴
*   **도메인 주도 설계 (Domain-Driven Design, DDD):** 복잡한 '매매 전략' 도메인을 명확하게 모델링하고, 비즈니스 로직을 코드에 반영합니다.
*   **MVP (Model-View-Presenter):** UI(View)와 비즈니스 로직(Model)을 분리하고, Presenter가 그 사이를 중재하여 결합도를 낮추고 테스트 용이성을 높입니다.

---

## 2. `StrategyManagementScreen` (메인 화면) 분석

`strategy_management_screen.py`는 매매 전략 관리 기능의 최상위 UI 컨테이너입니다.

### 2.1. 역할 및 책임
*   전략 관리 기능의 메인 화면을 구성합니다.
*   `QTabWidget`을 사용하여 여러 하위 기능(트리거 빌더, 전략 메이커, 전략 목록, 시뮬레이션)을 탭 형태로 제공합니다.
*   MVP 패턴의 View로서, 하위 탭들을 초기화하고 관리합니다.

### 2.2. UI 구성
*   `PyQt6`의 `QWidget`을 상속받아 구현되었습니다.
*   `QVBoxLayout` 내부에 `QTabWidget`을 배치하여 탭 기반의 인터페이스를 제공합니다.
*   **`TriggerBuilderTab`:** 현재 유일하게 실제 구현된 탭으로, 매매 조건을 생성하는 핵심 기능을 담당합니다.
*   **`전략 메이커`, `전략 목록`, `시뮬레이션` 탭:** 현재는 `create_placeholder_screen`으로 구현된 플레이스홀더이며, 향후 기능 확장을 위한 자리입니다.

### 2.3. 아키텍처 통합
*   `set_mvp_container`, `set_style_manager` 메서드를 통해 `DIContainer`와 `StyleManager`를 주입받습니다. 이는 의존성 주입(Dependency Injection)을 통해 컴포넌트 간의 결합도를 낮추고 유연성을 확보하려는 설계 의도를 보여줍니다.

---

## 3. `TriggerBuilderTab` (트리거 빌더 탭) 분석

`TriggerBuilderTab`은 `StrategyManagementScreen` 내에서 매매 조건을 생성하는 핵심 탭입니다.

### 3.1. 역할 및 책임
*   MVP 패턴의 View 역할을 수행하며, `TriggerBuilderWidget`을 실제 UI 컴포넌트로 포함합니다.
*   `TriggerBuilderPresenter`와 시그널-슬롯 메커니즘을 통해 통신합니다.
*   `_setup_mvp` 메서드에서 `RepositoryContainer`, `VariableCompatibilityService`, 여러 `UseCase` 객체들을 생성하고 `TriggerBuilderPresenter`에 주입하여 의존성을 관리합니다.

### 3.2. MVP 패턴 설정 (`_setup_mvp`)
*   **의존성 주입 (수동):** `RepositoryContainer`를 통해 `trading_variable_repository`를 가져오고, `VariableCompatibilityService`를 생성합니다.
*   **UseCase 인스턴스 생성:**
    *   `ListTradingVariablesUseCase`
    *   `GetVariableParametersUseCase`
    *   `SearchTradingVariablesUseCase`
    *   `CheckVariableCompatibilityUseCase`
    *   이 UseCase들은 Presenter에 주입되어 비즈니스 로직을 수행합니다.
*   **View (`TriggerBuilderWidget`) 생성:** 실제 UI를 담당하는 `TriggerBuilderWidget` 인스턴스를 생성합니다.
*   **Presenter (`TriggerBuilderPresenter`) 생성 및 연결:** `TriggerBuilderPresenter`를 생성하면서 `_view` (TriggerBuilderWidget)와 모든 `UseCase` 인스턴스를 주입합니다.

### 3.3. 시그널 연결 (`_connect_signals`)
*   `TriggerBuilderWidget`에서 발생하는 사용자 인터랙션 시그널(예: `variable_selected`, `search_requested`, `simulation_start_requested`, `compatibility_check_requested`)을 `TriggerBuilderPresenter`의 해당 `handle_` 메서드에 연결합니다.
*   대부분의 시그널 연결은 `_run_async` 유틸리티 함수를 통해 비동기적으로 처리되어 UI 응답성을 유지합니다.

### 3.4. 비동기 처리 (Asynchronous Operations)
*   `_run_async` 메서드는 `asyncio`를 사용하여 비동기 코루틴을 실행합니다. 이는 데이터 로딩, 검색, 호환성 검사 등 시간이 소요될 수 있는 작업들이 UI 스레드를 블로킹하지 않도록 합니다.
*   `initialize` 메서드는 탭 로드 시 Presenter의 `initialize_view`를 비동기적으로 호출하여 초기 데이터를 로드합니다.

---

## 4. `ITriggerBuilderView` (View 인터페이스) 분석

`i_trigger_builder_view.py`는 `TriggerBuilderPresenter`와 `TriggerBuilderWidget` 간의 계약을 정의하는 추상 인터페이스입니다.

### 4.1. 역할 및 책임
*   MVP 패턴에서 Presenter가 View의 구체적인 구현에 의존하지 않고 소통할 수 있도록 하는 추상 계층을 제공합니다.
*   View가 구현해야 할 모든 UI 관련 메서드를 정의합니다.

### 4.2. 주요 메서드
*   **데이터 표시:** `display_variables`, `show_variable_details`, `show_external_variable_details`, `update_compatibility_status`
*   **사용자 피드백:** `show_error_message`, `show_success_message`
*   **UI 상태 제어:** `enable_simulation_controls`, `update_simulation_progress`, `update_data_source`
*   **시뮬레이션 실행 지시:** `run_simulation` (Presenter가 View에게 시뮬레이션 실행을 직접 지시)

---

## 5. `TriggerBuilderPresenter` (Presenter) 분석

`trigger_builder_presenter.py`는 `TriggerBuilderTab` (View)와 비즈니스 로직 (UseCase) 사이의 핵심적인 중재자입니다.

### 5.1. 역할 및 책임
*   View의 이벤트를 수신하고, `UseCase`를 호출하여 비즈니스 로직을 실행합니다.
*   `UseCase`의 실행 결과를 받아 다시 View에 반영하여 UI를 업데이트합니다.

### 5.2. 의존성 주입
*   생성자를 통해 `ITriggerBuilderView` 인터페이스를 구현한 View 객체와 4가지 `UseCase` 객체들을 주입받습니다. 이는 느슨한 결합을 통해 테스트 용이성과 유연성을 확보합니다.

### 5.3. View 초기화 (`initialize_view`)
*   `_list_variables_usecase.execute()`를 호출하여 시스템에 정의된 모든 트레이딩 변수 목록을 가져와 `_view.display_variables()`를 통해 View에 표시하도록 지시합니다.

### 5.4. 사용자 인터랙션 처리
*   `handle_variable_selected`, `handle_external_variable_selected`, `handle_search_variables`, `handle_simulation_start`, `handle_simulation_stop`, `handle_compatibility_check` 등의 메서드를 통해 사용자 액션을 처리합니다.
*   View로부터 전달받은 데이터를 DTO로 변환하고, 해당 액션에 맞는 `UseCase`의 `execute()` 메서드를 호출하여 비즈니스 로직을 실행합니다.
*   `UseCase`의 실행 결과를 받아 View의 적절한 메서드를 호출하여 UI를 업데이트합니다.
*   대부분의 `handle_` 메서드는 비동기적으로 동작하여 UI 응답성을 보장합니다.

### 5.5. 시뮬레이션 로직
*   `handle_simulation_start` 시 View의 시뮬레이션 컨트롤을 비활성화하고, `_view.run_simulation()`을 직접 호출하여 시뮬레이션을 실행합니다. 이는 시뮬레이션이 UI와 밀접하게 연관된 복잡한 시각화나 실시간 업데이트를 포함할 가능성을 시사합니다.

### 5.6. 데이터 소스 변경
*   `handle_data_source_changed` 시 View의 `update_data_source`를 호출하여 데이터 소스 변경을 반영합니다.

### 5.7. 의도
*   **책임 분리:** View는 UI, Presenter는 비즈니스 로직 조율 및 View 업데이트를 담당하여 책임을 명확히 분리합니다.
*   **테스트 용이성:** View와 UseCase의 인터페이스에만 의존하므로, 단위 테스트를 통해 비즈니스 로직의 정확성을 검증하기 용이합니다.
*   **비동기 처리 관리:** 복잡한 비동기 작업을 Presenter 계층에서 관리하여 View 코드를 간결하게 유지하고, UI 응답성을 보장합니다.
*   **도메인 로직 캡슐화:** UseCase를 통해 도메인 로직을 캡슐화하고, Presenter는 이 UseCase를 호출하는 방식으로 도메인 계층과의 상호작용을 추상화합니다.

---

## 6. `TriggerBuilderWidget` (View 구현체) 분석

`trigger_builder_widget.py`는 `ITriggerBuilderView` 인터페이스를 구현하고, PyQt6 위젯들을 사용하여 실제 사용자 인터페이스를 구성하는 클래스입니다.

### 6.1. 역할 및 책임
*   `ITriggerBuilderView` 인터페이스의 구체적인 구현체로서, UI 렌더링과 사용자 입력 수집을 담당합니다.
*   사용자 인터랙션 발생 시 `pyqtSignal`을 발생시켜 Presenter에게 이벤트를 전달합니다.

### 6.2. UI 레이아웃 (`_setup_ui`)
*   `QVBoxLayout`과 `QGridLayout`을 사용하여 UI 컴포넌트들을 배치합니다.
*   화면을 3x2 그리드로 분할하며, 각 영역은 다음과 같습니다:
    *   `condition_builder_area` (좌측, 2행)
    *   `trigger_list_area` (중앙 상단)
    *   `simulation_area` (우측 상단)
    *   `trigger_detail_area` (중앙 하단)
    *   `test_result_area` (우측 하단)

### 6.3. 하위 위젯을 통한 모듈화
*   `ConditionBuilderWidget`, `TriggerListWidget`, `SimulationControlWidget`, `TriggerDetailWidget`, `SimulationResultWidget` 등 여러 전문화된 하위 위젯들을 조합하여 구성됩니다.
*   `try-except ImportError` 블록을 사용하여 하위 위젯 로딩 실패 시에도 플레이스홀더를 표시하여 견고성을 확보합니다.

### 6.4. 시그널 정의 및 연결
*   `variable_selected`, `external_variable_selected`, `trigger_selected`, `search_requested`, `simulation_start_requested`, `simulation_stop_requested`, `compatibility_check_requested` 등의 `pyqtSignal`을 정의합니다.
*   하위 위젯에서 발생한 시그널을 받아 자신의 시그널로 `emit`하여 이벤트를 `TriggerBuilderTab` (그리고 Presenter)로 전파합니다.

### 6.5. `ITriggerBuilderView` 인터페이스 구현
*   `display_variables`, `show_variable_details`, `show_external_variable_details`, `update_compatibility_status` 등의 메서드는 대부분 `condition_builder` 하위 위젯에게 실제 표시 로직을 위임합니다.
*   `show_error_message`, `show_success_message`는 `QMessageBox`를 사용합니다.
*   `enable_simulation_controls`, `update_simulation_progress`, `run_simulation`, `update_data_source`는 현재 `TODO` 주석으로 표시되어 있어, 시뮬레이션 관련 UI 로직이 아직 개발 중임을 나타냅니다.

### 6.6. 내부 시그널 핸들러
*   `_on_trigger_selected`, `_on_simulation_requested` 등의 메서드는 하위 위젯의 시그널을 처리하고, 필요한 경우 `TriggerBuilderWidget`의 시그널을 `emit`하여 상위 계층으로 이벤트를 전달합니다.

---

## 7. `ConditionBuilderWidget` (조건 빌더 위젯) 분석

`condition_builder_widget.py`는 사용자가 매매 조건을 시각적으로 구성할 수 있도록 돕는 `TriggerBuilderWidget`의 핵심 하위 컴포넌트입니다.

### 7.1. 역할 및 책임
*   사용자가 트레이딩 변수, 연산자, 비교값 등을 선택하여 매매 조건을 정의하는 UI를 제공합니다.
*   `IConditionBuilderView` 인터페이스를 구현하며, `TriggerBuilderPresenter`로부터 데이터를 받아 UI에 표시하고, 사용자 입력을 시그널로 Presenter에 전달합니다.

### 7.2. UI 구성 (`_init_ui`)
*   `QVBoxLayout`을 사용하여 UI를 여러 섹션으로 나눕니다.
*   **변수 선택 영역 (`_create_variable_selection_area`):**
    *   `QComboBox`로 카테고리 및 변수를 선택합니다.
    *   `help_button`으로 변수 상세 도움말을 제공합니다.
    *   `ParameterInputWidget`을 포함하여 선택된 변수의 파라미터를 입력받습니다.
*   **조건 설정 영역 (`_create_condition_setup_area`):**
    *   `QComboBox`로 연산자(`>`, `<`, `상향 돌파` 등)를 선택합니다.
    *   비교값 타입(`직접 입력`, `외부 변수`)을 선택하며, 이에 따라 `QLineEdit` 또는 `external_variable_combo`가 활성화됩니다.
*   **호환성 검토 결과 영역 (`_create_compatibility_status_area`):**
    *   `CompatibilityStatusWidget`을 포함하여 변수 간 호환성 검사 결과를 표시합니다. 초기에는 숨겨져 있습니다.
*   **외부 변수 영역 (`_create_external_variable_area`):**
    *   기본 변수 선택 영역과 유사하게 외부 변수의 카테고리, 변수 선택, 도움말 버튼, 파라미터 입력 기능을 제공합니다. '외부 변수' 비교값 타입 선택 시 활성화됩니다.
*   **조건 미리보기 영역 (`_create_condition_preview_area`):**
    *   `ConditionPreviewWidget`을 포함하여 현재 설정된 조건의 텍스트 미리보기를 실시간으로 보여줍니다.

### 7.3. 시그널 정의 및 연결
*   `variable_selected`, `external_variable_selected`, `category_changed`, `condition_created`, `condition_preview_requested`, `compatibility_check_requested` 등의 `pyqtSignal`을 정의합니다.
*   콤보박스 선택 변경, 텍스트 입력 변경, 버튼 클릭 등 사용자 인터랙션에 따라 이 시그널들이 발생하며, 내부 이벤트 핸들러를 거쳐 `TriggerBuilderPresenter`로 전달됩니다.

### 7.4. `IConditionBuilderView` 인터페이스 구현
*   `display_variables`: `TradingVariableListDTO`를 받아 변수 콤보박스들을 업데이트합니다. 기본 변수 선택에서는 '메타변수'를 제외하고, 외부 변수 선택에서는 모든 변수를 포함하는 필터링 로직이 적용됩니다.
*   `show_variable_details`, `show_external_variable_details`: `TradingVariableDetailDTO`를 받아 `ParameterInputWidget`에 상세 정보를 전달하여 파라미터 입력 UI를 동적으로 구성합니다.
*   `update_compatibility_status`: `VariableCompatibilityResultDTO`를 받아 `CompatibilityStatusWidget`에 호환성 검사 결과를 표시하고, `compatibility_group`의 가시성을 제어합니다.

### 7.5. 내부 로직
*   **변수 필터링:** `_filter_variables_by_category`, `_filter_external_variables_by_category` 메서드를 통해 카테고리별로 변수 목록을 필터링합니다.
*   **비교값 타입 변경 처리 (`_on_value_type_changed`):** '직접 입력'과 '외부 변수' 타입에 따라 UI 요소의 활성화 상태를 변경하고, '외부 변수' 선택 시 호환성 검사를 요청합니다.
*   **호환성 검토 요청 (`_request_compatibility_check`):** 현재 선택된 기본 변수와 외부 변수를 기반으로 호환성 검사를 요청하는 시그널을 `TriggerBuilderPresenter`로 보냅니다.
*   **도움말 기능 (`_on_help_clicked`, `_on_external_help_clicked`):** `VariableHelpDialog`를 통해 변수 상세 도움말을 제공하며, `VariableHelpRepository`를 사용하여 도움말 정보를 조회합니다.
*   **조건 미리보기 (`_update_condition_preview`, `_generate_preview_text`):** 사용자가 조건을 설정할 때마다 실시간으로 조건의 텍스트 미리보기를 생성하여 `ConditionPreviewWidget`에 표시합니다.
*   **현재 조건 반환 (`get_current_condition`):** 현재 UI에 설정된 모든 조건 요소(변수 ID, 연산자, 비교값, 파라미터 등)를 딕셔너리 형태로 반환합니다.

### 7.6. 의도
`ConditionBuilderWidget`은 사용자가 복잡한 매매 조건을 직관적으로 구성할 수 있도록 설계된 핵심 UI 컴포넌트입니다. 다양한 트레이딩 변수, 연산자, 비교값(직접 입력 또는 다른 변수)을 조합하고, 각 변수의 파라미터를 설정하며, 실시간으로 조건의 미리보기를 확인하고, 변수 간의 호환성까지 검사할 수 있는 강력한 기능을 제공하여 사용자가 유효하고 정교한 전략을 만들 수 있도록 돕습니다.

---

## 8. UseCase 및 도메인 객체 (Model) 추론

UI와 Presenter의 상호작용을 이해했으므로, 이들을 뒷받침하는 비즈니스 로직과 데이터 모델을 추론합니다.

### 8.1. UseCase의 역할
`TriggerBuilderPresenter`에 주입된 UseCase들은 `upbit_auto_trading.application.use_cases.trigger_builder` 경로에 위치할 것으로 예상되며, 각각 특정 비즈니스 시나리오를 처리합니다.

*   **`ListTradingVariablesUseCase`:** `TradingVariableRepository`를 통해 모든 `TradingVariable` 객체를 조회하고, `TradingVariableListDTO` 형태로 반환합니다.
*   **`GetVariableParametersUseCase`:** `TradingVariableRepository`를 통해 특정 `variable_id`의 `TradingVariable` 객체를 조회하고, 파라미터 정의를 `TradingVariableDetailDTO` 형태로 반환합니다.
*   **`SearchTradingVariablesUseCase`:** `TradingVariableRepository`를 통해 변수를 조회하고, `VariableCompatibilityService`를 사용하여 검색 조건에 맞는 변수를 필터링합니다. `TradingVariableListDTO` 형태로 반환합니다.
*   **`CheckVariableCompatibilityUseCase`:** `TradingVariableRepository`를 통해 두 변수의 상세 정보를 가져오고, `VariableCompatibilityService`를 사용하여 호환성을 판단합니다. `VariableCompatibilityResultDTO` 형태로 반환합니다.

### 8.2. 예상되는 도메인 객체 (Entities/Value Objects)
*   **`TradingVariable`:** `variable_id`, `display_name_ko`, `category`, `description`, `parameters` (파라미터 정의), `data_type`, `compatibility_rules` 등의 속성을 가질 것으로 예상됩니다.
*   **`Trigger`:** `trigger_id`, `name`, `condition` (하나 이상의 `Condition` 객체), `action`, `is_active` 등의 속성을 가질 것입니다.
*   **`Condition`:** `main_variable`, `operator`, `comparison_value`, `external_variable`, `main_variable_parameters`, `external_variable_parameters` 등의 속성을 가질 것입니다.

### 8.3. 예상되는 DTO (Data Transfer Objects)
*   **`TradingVariableListDTO`:** `ListTradingVariablesUseCase`의 결과로, `TradingVariable` 요약 정보 리스트.
*   **`TradingVariableDetailDTO`:** `GetVariableParametersUseCase`의 결과로, 특정 `TradingVariable`의 상세 정보.
*   **`VariableSearchRequestDTO`:** `SearchTradingVariablesUseCase`의 입력으로, 검색어와 카테고리.
*   **`VariableCompatibilityRequestDTO`:** `CheckVariableCompatibilityUseCase`의 입력으로, 메인 변수 ID와 외부 변수 ID.
*   **`VariableCompatibilityResultDTO`:** `CheckVariableCompatibilityUseCase`의 결과로, 호환성 여부, 메시지, 상세 정보.

---

## 9. 데이터 저장소 (Repository) 추론

`TriggerBuilderTab`에서 `RepositoryContainer`를 통해 `trading_variable_repository`를 가져오는 것을 확인했습니다. 이는 `TradingVariable` 객체들이 어떤 형태로든 영속화되고 있음을 의미합니다.

### 9.1. `TradingVariableRepository`의 역할
*   `get_all_trading_variables()`: 모든 트레이딩 변수 목록 조회.
*   `get_trading_variable_by_id(variable_id)`: 특정 ID의 트레이딩 변수 조회.
*   `search_trading_variables(search_term, category)`: 검색 조건에 맞는 트레이딩 변수 조회.

### 9.2. 데이터 저장 방식
*   **YAML 파일:** 프로젝트의 `config` 디렉토리에 `.yaml` 파일들이 많은 것으로 보아, `TradingVariable` 정의가 YAML 파일 형태로 저장될 수 있습니다. 이는 사람이 읽고 편집하기 용이하며, 복잡한 구조를 표현하기 좋습니다.
*   **SQLite 데이터베이스:** `data_info`에 `.sql` 파일들이 있는 것으로 보아, 데이터베이스 스키마를 정의하는 것으로 보입니다. `TradingVariable`이나 `Trigger`와 같은 도메인 객체들이 SQLite 데이터베이스에 저장될 수도 있습니다. `VariableHelpRepository`가 DB에서 도움말을 조회하는 것을 보면, 데이터베이스 사용 가능성이 높습니다. 실제로는 YAML 파일에 정의된 변수 메타데이터를 로드하여 데이터베이스에 캐싱하거나, 직접 데이터베이스에 저장하는 하이브리드 방식일 가능성도 있습니다.

---

## 10. 종합 결론 및 시사점

`strategy_management_screen.py`로 시작된 분석은 `TriggerBuilderTab`, `TriggerBuilderPresenter`, `ITriggerBuilderView`, `TriggerBuilderWidget`, 그리고 `ConditionBuilderWidget`에 이르기까지 깊이 있는 아키텍처 분석으로 이어졌습니다.

이 코인 거래 프로그램의 매매 전략 관리 기능은 다음과 같은 특징을 가집니다:

*   **강력한 아키텍처:** DDD와 MVP 패턴을 철저히 적용하여 UI, 비즈니스 로직, 데이터 모델의 책임이 명확하게 분리되어 있습니다. 이는 코드의 모듈성, 테스트 용이성, 유지보수성, 그리고 확장성을 극대화합니다.
*   **사용자 중심의 조건 빌더:** `ConditionBuilderWidget`은 사용자가 복잡한 매매 조건을 직관적으로 구성할 수 있도록 설계되었습니다. 다양한 트레이딩 변수, 연산자, 비교값, 파라미터 설정, 실시간 미리보기, 그리고 변수 호환성 검사 기능까지 제공하여 사용자가 유효하고 정교한 전략을 만들 수 있도록 돕습니다.
*   **비동기 처리:** UI의 응답성을 유지하기 위해 비동기 프로그래밍(`asyncio`)을 적극적으로 활용합니다. 이는 데이터 로딩이나 복잡한 계산이 UI를 블로킹하지 않도록 합니다.
*   **도메인 모델의 중요성:** `TradingVariable`, `Trigger`, `Condition`과 같은 도메인 객체들이 비즈니스 로직의 핵심을 이루며, UseCase를 통해 이들이 조작됩니다. DTO는 계층 간 데이터 전달을 표준화합니다.
*   **확장 가능한 설계:** 현재는 '트리거 빌더' 탭만 구현되어 있지만, '전략 메이커', '전략 목록', '시뮬레이션' 탭이 플레이스홀더로 존재하여 향후 기능 확장을 위한 기반이 마련되어 있습니다. 특히 `ConditionBuilderWidget`이 `shared.components`에 위치하는 것은 이 컴포넌트가 다른 화면이나 기능에서도 재사용될 수 있음을 의미합니다.
*   **데이터 영속성:** `VariableHelpRepository`와 `RepositoryContainer`의 존재는 트레이딩 변수 및 관련 정보가 데이터베이스(SQLite 예상) 또는 파일(YAML 예상)을 통해 영속적으로 관리됨을 시사합니다.

결론적으로, 이 `strategy_management_screen.py`와 그 주변 코드들은 단순한 UI 화면이 아니라, 복잡한 도메인 문제를 해결하기 위한 견고하고 체계적인 소프트웨어 엔지니어링 원칙이 적용된 모범적인 사례를 보여줍니다. 사용자는 이 화면을 통해 자신의 트레이딩 아이디어를 구체적인 자동 매매 전략으로 변환하고, 시스템은 이를 안정적으로 실행하고 관리할 수 있는 기반을 제공합니다.
