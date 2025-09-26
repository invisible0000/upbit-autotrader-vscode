# QAsync 통합 영향 범위 조사 (2025-09-26)

## 목적
- "docs/big_issues/EVENT_LOOP_ARCHITECTURE_CRISIS_20250926.md"에서 지적한 다중 이벤트 루프 충돌 문제를 해소하기 위해, upbit_auto_trading 메인 프로그램 경로 전반의 QAsync 통합 시 영향을 받는 파일과 폴더를 정리합니다.
- 단일 QAsync 이벤트 루프를 중심으로 비동기 흐름을 재정렬하는 데 필요한 작업 대상을 우선순위별로 제시해 효율적인 리팩터링 계획 수립을 돕습니다.

## 조사 요약
- 진입점(run_desktop_ui.py)은 QEventLoop를 생성하지만, 동기형 main()과 비동기형 run_application()이 공존하여 루프 관리가 이중화되어 있습니다.
- UI 계층의 여러 위젯이 asyncio.new_event_loop() 또는 별도 스레드/asyncio.run()을 사용해 독립 루프를 만들어 QAsync 루프와 충돌할 여지가 큽니다.
- Application/Infrastructure 계층은 asyncio.create_task, asyncio.get_event_loop()에 의존하는 부분이 다수이며, QAsync 루프에서 안전하게 실행되도록 명시적 루프 주입 또는 헬퍼가 필요합니다.
- 로깅/설정 UI와 전략 관리 탭 등 부가 화면도 자체 루프를 생성하고 있어 통합 대상에 포함됩니다.

## 주요 이슈 패턴
- 이중 진입점: run_desktop_ui.py에서 QEventLoop를 생성한 뒤 다시 loop.run_forever()를 호출하거나 별도 wrapper를 제공.
- 격리 루프 생성: asyncio.new_event_loop() + loop.run_until_complete() 패턴이 UI 위젯, 서비스, 로깅 모듈 전반에 산재.
- 직접 asyncio.run 호출: QAsync 환경에서 금지해야 할 루프 생성이 전략 탭, 서비스 내부에서 사용.
- 루프 추상화 부족: asyncio.get_event_loop() 사용으로 인해 QAsync 루프가 반환되지 않는 상황에서 실패 가능성이 존재.
- 백그라운드 태스크 관리 부재: asyncio.create_task로 생성한 작업에 대한 참조/취소 로직이 흩어져 있어 종료 시 정리가 어렵습니다.

## 우선순위별 작업 대상

### 1. Critical (즉시 통합 설계 필요)
| 영역 | 파일 | 현재 문제/패턴 | 예상 대응 |
| --- | --- | --- | --- |
| 진입점 | run_desktop_ui.py (라인 456, 479) | QEventLoop 생성 후 loop.run_until_complete, loop.run_forever 혼재. asyncio.set_event_loop 다중 호출. | 단일 진입 함수로 정리하고 QAsync 루프 수명주기를 명확히 관리. 앱 종료/정리 로직을 qasync.run 또는 컨텍스트 기반으로 재작성. |
| UI-차트 | ui/desktop/screens/chart_view/widgets/coin_list_widget.py (라인 223) | 스레드와 asyncio.new_event_loop()로 REST 호출 실행, 완료 후 set_event_loop(None). | QAsync에서 사용할 수 있는 asyncSlot 또는 asyncio.create_task 기반 호출로 변경하고 백그라운드 스레드 제거. |
| 인프라-서비스 | infrastructure/services/api_key_service.py (라인 326) | API 테스트용 별도 이벤트 루프 생성 및 스레드 실행. | QAsync 루프 주입 또는 asyncSlot 래퍼 도입, 메인 루프에서 await 가능하도록 서비스 인터페이스 분리. |
| 로깅 UI | ui/widgets/logging/event_driven_log_viewer_widget.py (라인 202) | 로깅 뷰어가 독립 루프에서 이벤트 버스를 시작(loop.run_until_complete). | QAsync 루프와 공유하도록 이벤트 시스템 초기화 함수 비동기화, UI 스레드에서 await. |
| 로깅 UI | ui/widgets/logging/event_driven_logging_configuration_section.py (라인 320) | 구성 위젯도 새 이벤트 루프 생성 후 loop.run_until_complete. | 위 뷰어와 동일하게 QAsync 친화적 초기화 헬퍼 제공. |
| 전략 관리 | ui/desktop/screens/strategy_management/tabs/trigger_builder/trigger_builder_tab.py (라인 126) | _run_async가 loop.run_until_complete, asyncio.run을 혼용. | QAsync 메인 루프에서 안전하게 태스크를 생성 또는 큐잉할 공용 헬퍼로 치환. |

### 2. High Priority (QAsync 루프와의 정합성 확보)
| 영역 | 파일 | 현재 문제/패턴 | 예상 대응 |
| --- | --- | --- | --- |
| UI-창 | ui/desktop/main_window.py (라인 362) | asyncio.create_task 호출 전 루프 실행 여부 검사. | 메인 윈도우 생성 시점에 QAsync 루프 접근 헬퍼 도입, 태스크 관리 리스트 추가. |
| UI-차트 | ui/desktop/screens/chart_view/chart_view_screen.py (라인 238) | InMemoryEventBus를 생성 후 asyncio.create_task로 start() 호출. | 이벤트 버스 시작과 종료를 MainWindow 수명주기와 연결하고 태스크 참조를 저장. |
| Presenter | ui/desktop/screens/chart_view/presenters/orderbook_presenter.py (라인 80) | asyncio.create_task로 REST 백업 갱신 수행. | QApplication 종료 시 태스크 취소, 에러 전파를 위한 헬퍼 사용. |
| UseCase | application/use_cases/orderbook_management_use_case.py (라인 63) | asyncSlot 기반이나 내부에서 REST와 WebSocket 호출 집중. | OrderbookDataService와 동일한 루프 정책 공유(루프 주입, await 체계 확인). |
| 데이터 서비스 | infrastructure/services/orderbook_data_service.py (라인 78) | asyncSlot을 통해 WebSocket과 REST 호출, 내부에서 QAsync 가정. | WebSocketMarketDataService와 UseCase에 명시적 루프 의존성 주입, 에러 핸들 강화. |
| 이벤트 버스 | infrastructure/events/domain_event_publisher_impl.py (라인 17) | asyncio.get_event_loop + loop.run_until_complete 사용. | QAsync 환경에서 안전한 publish 헬퍼 제공(asyncio.get_running_loop 사용, 필요 시 asyncio.create_task). |
| 이벤트 버스 | infrastructure/events/bus/in_memory_event_bus.py (라인 302) | 핸들러 실행 시 asyncio.get_event_loop로 executor 호출. | 현재 루프/스레드풀 정책을 QAsync 친화적으로 조정하고 필요 시 전용 executor 전달. |
| Application 서비스 | application/services/websocket_application_service.py (라인 301) | 헬스 체크 등 백그라운드 태스크를 asyncio.create_task로만 관리. | 태스크 레지스트리 도입, 종료/예외 처리 보강, QAsync 루프 의존성 명시. |

### 3. Medium Priority (통합 시 검토 권장)
| 영역 | 파일 또는 폴더 | 현재 문제/패턴 | 비고 |
| --- | --- | --- | --- |
| UI 차트 | ui/desktop/screens/chart_view/widgets/orderbook_widget.py | Presenter와 QTimer 기반 자동 갱신. 루프 직접 제어는 없으나 Presenter 의존성 상위 문제에 영향. | Critical 및 High 항목 해결 후 연쇄 테스트 필요. |
| Application | application/chart_viewer/coin_list_service.py | WebSocket과 REST 호출, UI 콜백 호출 시 루프 안전성 가정. | CoinListWidget 리팩토링 시 동시 고려. |
| Application | application/services/chart_market_data_service.py (라인 301) | 실시간 수집 태스크를 asyncio.create_task로 관리. | 종료 경로와 태스크 취소 루틴 재점검. |
| Infrastructure | infrastructure/services/websocket_market_data_service.py | 연결 유지 태스크와 재연결 루프 존재. | QAsync 루프 전달, 종료 시점 정리 필요. |
| 이벤트 시스템 | infrastructure/events/event_system_initializer.py | create_simple_event_system이 비동기 시작을 호출자에 위임. | 로깅 UI, 차트 화면 등에서 공통 초기화 헬퍼로 사용. |

### 4. Legacy 및 참고 대상
| 파일 또는 폴더 | 참고 사항 |
| --- | --- |
| ui/desktop/screens/chart_view/widgets/legacy 디렉터리 | 레거시 위젯 다수(coin_list_widget_legacy.py 등)가 asyncio.new_event_loop()를 반복 사용. 신규 구조 통합 후 단계적 제거 권장. |
| examples 및 tests 경로 | asyncio.run 호출이 다수 존재. 메인 UI와 직접 연결되지는 않으나, 통합 전략 결정 후 패턴 통일을 고려. |
| infrastructure/logging/performance/async_processor.py | 백그라운드 로그 처리 워커가 asyncio.create_task 기반. 로그 UI와 도메인 이벤트 정비 시 함께 검토. |

## 권장 작업 순서
1. 진입점 재정렬: run_desktop_ui.py를 단일 QAsync 실행 경로로 단순화하고 종료 루틴을 확정합니다.
2. UI 격리 루프 제거: CoinListWidget, 로깅 위젯, 전략 탭 등에서 asyncio.new_event_loop()와 asyncio.run을 치환합니다.
3. 서비스 및 이벤트 계층 정합화: DomainEventPublisher, InMemoryEventBus, ApiKeyService에서 메인 루프 주입 패턴을 통일합니다.
4. 태스크 라이프사이클 관리: asyncio.create_task 사용 지점마다 취소와 예외 처리 전략을 도입합니다.
5. 레거시 청산과 테스트: Legacy 위젯 및 예제 스크립트를 순차적으로 정리하고 통합 테스트 시나리오를 확보합니다.

## 추가 메모
- UI 계층 비동기 메서드는 가능한 한 asyncSlot 또는 QAsync 제공 슬롯을 사용해 Qt 시그널-슬롯 경계에서 루프 충돌을 방지하세요.
- 이벤트 버스와 WebSocket 서비스는 ApplicationContext에서 싱글톤으로 관리하면 리소스 공유에 유리합니다. 루프 통합 후 DI 컨테이너를 통해 동일 루프 객체를 전달하는 방식을 고려하십시오.
- 통합 단계별로 메모리와 태스크 누수 감지를 위해 asyncio.all_tasks() 체크나 로깅을 활용하는 것을 권장합니다.
