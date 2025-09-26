# QAsync 통합 아키텍처 전환 작업 계획 (파일 레벨)

## 1단계: 애플리케이션 진입점 및 이벤트 루프 통합 (Foundation)
* **목표**: 애플리케이션의 시작점에서부터 `qasync`를 Qt 이벤트 루프로 설정하여, 모든 비동기 작업의 기준이 될 단일 이벤트 루프를 마련합니다.
* **주요 작업 파일**:
    1.  `run_desktop_ui.py`: `QApplication`을 `qasync.QApplication`으로 교체하고, `qasync` 이벤트 루프를 설정하는 코드를 추가합니다.
    2.  `upbit_auto_trading/ui/desktop/main_window.py`: 애플리케이션의 메인 윈도우로, 이벤트 루프 설정에 따른 초기화 코드 변경이 필요할 수 있습니다.
    3.  `upbit_auto_trading/application/container.py`: 의존성 주입 컨테이너로, 이벤트 루프와 관련된 서비스(특히 WebSocket) 생성 방식을 수정해야 할 수 있습니다.

---

## 2단계: 핵심 인프라 레이어 리팩토링 (Core Infrastructure)
* **목표**: `UpbitPublicClient`를 포함한 모든 외부 API 통신 및 공유 리소스가 1단계에서 생성된 단일 이벤트 루프를 사용하도록 수정합니다. 이벤트 루프 종속성을 제거하고 안정성을 확보하는 핵심 단계입니다.
* **주요 작업 파일**:
    1.  `upbit_auto_trading/infrastructure/external_apis/upbit/upbit_public_client.py`: `aiohttp.ClientSession`이 단일 이벤트 루프를 사용하도록 수정합니다.
    2.  `upbit_auto_trading/infrastructure/external_apis/upbit/upbit_private_client.py`: `UpbitPublicClient`와 동일하게 `aiohttp.ClientSession`을 수정합니다.
    3.  `upbit_auto_trading/infrastructure/external_apis/upbit/websocket/core/websocket_manager.py`: WebSocket 연결이 단일 이벤트 루프를 사용하도록 수정합니다.
    4.  `upbit_auto_trading/infrastructure/external_apis/upbit/rate_limiter/upbit_rate_limiter.py`: Rate Limiter의 `asyncio.Lock`이 단일 이벤트 루프에 바인딩되도록 수정합니다.

---

## 3단계: 주요 UI 컴포넌트 및 서비스 수정 (UI Components & Services)
* **목표**: 문제의 원인이었던 `CoinListWidget`을 포함하여, 비동기 데이터 처리가 필요한 핵심 UI 컴포넌트들이 `asyncSlot` 대신 표준 `async/await`를 사용하며 단일 루프 위에서 동작하도록 수정합니다.
* **주요 작업 파일**:
    1.  `upbit_auto_trading/ui/desktop/screens/chart_view/widgets/coin_list_widget.py`: **가장 시급한 수정 대상**입니다. `asyncio.run`을 제거하고, 모든 비동기 로직이 `qasync` 이벤트 루프 위에서 동작하도록 수정합니다.
    2.  `upbit_auto_trading/application/chart_viewer/coin_list_service.py`: `CoinListWidget`이 사용하는 서비스로, 위젯의 변경에 맞춰 비동기 호출 방식을 수정합니다.
    3.  `upbit_auto_trading/ui/desktop/screens/chart_view/widgets/orderbook_widget.py`: `@asyncSlot`을 제거하고 표준 `async/await` 방식으로 비동기 코드를 수정합니다.
    4.  `upbit_auto_trading/application/use_cases/orderbook_management_use_case.py`: `OrderbookWidget`에서 사용하는 Use Case로, 비동기 처리 방식을 일관되게 수정합니다.
    5.  `upbit_auto_trading/ui/desktop/screens/chart_view/chart_view_screen.py`: `CoinListWidget`과 `OrderbookWidget`을 포함하는 상위 뷰이므로, 위젯들의 변경에 따른 상호작용 코드를 수정합니다.

---

## 4단계: 전체 시스템 아키텍처 통일 (System-wide Unification)
* **목표**: `asyncio.run()`, `new_event_loop()` 등 격리된 이벤트 루프를 생성하는 모든 코드를 찾아 제거하고, 전체 애플리케이션이 `qasync` 기반의 단일 이벤트 루프 아키텍처를 따르도록 통일합니다.
* **주요 작업 파일**:
    * 이 단계에서는 `grep -r "asyncio.run\|new_event_loop"` 등의 명령어로 프로젝트 전체에서 격리된 이벤트 루프를 사용하는 모든 파일을 찾아 수정해야 합니다. 아래는 예상되는 주요 파일 목록입니다.
    1.  `upbit_auto_trading/application/services/strategy_application_service.py`
    2.  `upbit_auto_trading/application/services/backtest_application_service.py`
    3.  `upbit_auto_trading/ui/desktop/screens/strategy_management/tabs/trigger_builder/trigger_builder_tab.py`
    4.  `upbit_auto_trading/ui/desktop/screens/settings/database_settings/presenters/database_settings_presenter.py`
    5.  `upbit_auto_trading/ui/desktop/screens/settings/api_settings/presenters/api_settings_presenter.py`
    6.  `upbit_auto_trading/ui/desktop/screens/settings/logging_management/presenters/logging_management_presenter.py`

---

## 5단계: 테스트 및 검증 (Verification)
* **목표**: 변경된 아키텍처가 기존 기능을 해치지 않고, 이벤트 루프 충돌 문제가 완전히 해결되었는지 검증하는 통합 테스트를 진행합니다.
* **주요 작업 파일**:
    1.  `tests/` 디렉토리 하위의 모든 테스트 파일을 검토하고, 변경된 비동기 코드에 맞춰 테스트 코드를 수정합니다. 특히 `pytest-asyncio`와 `qasync`의 호환성을 확인하며 테스트 환경을 재구성해야 합니다.
