### 1. 코인 리스트 위젯 관련 (Phase 1: 최우선)
- **upbit_auto_trading/ui/desktop/screens/chart_view/widgets/coin_list_widget.py**
- **upbit_auto_trading/ui/desktop/screens/chart_view/widgets/legacy/coin_list_widget_new.py**
- **upbit_auto_trading/ui/desktop/screens/chart_view/widgets/legacy/coin_list_widget_legacy.py**
- **upbit_auto_trading/ui/desktop/screens/chart_view/widgets/legacy/coin_list_widget_problematic.py**

> 위 파일들은 `asyncio.new_event_loop()`로 별도 루프를 생성하며 스레드에서 `run_until_complete`를 호출합니다:contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}. QAsync 기반 루프에 맞게 비동기 함수로 분리하고 `asyncSlot`으로 UI 스레드와 연결해야 합니다.

### 2. 이벤트 기반 로깅 UI 관련 (Phase 2)
- **upbit_auto_trading/ui/widgets/logging/event_driven_logging_configuration_section.py**
- **upbit_auto_trading/ui/widgets/logging/event_driven_log_viewer_widget.py**

> 이벤트 버스 초기화 시 새 루프를 만들고 `loop.run_until_complete`로 시작하는 부분을 제거해야 합니다:contentReference[oaicite:4]{index=4}:contentReference[oaicite:5]{index=5}. QAsync 루프에서 `asyncio.create_task`로 이벤트 버스를 실행하도록 수정합니다.

### 3. 인프라스트럭처 서비스 (Phase 3)
- **upbit_auto_trading/infrastructure/services/api_key_service.py**

> API 키 테스트에서 별도 스레드와 이벤트 루프를 생성하여 `run_until_complete`를 호출하고 있습니다:contentReference[oaicite:6]{index=6}. QAsync 루프 안에서 비동기 함수로 재작성하여 리소스 바인딩 충돌을 제거합니다.

### 4. 도메인 이벤트 시스템 (Phase 4)
- **upbit_auto_trading/infrastructure/events/domain_event_publisher_impl.py**

> 현재 `run_until_complete`로 비동기 퍼블리시를 동기식으로 실행합니다. QAsync 환경에서는 `asyncio.get_event_loop().create_task`를 사용하여 비동기 작업을 스케줄하는 형태로 변경해야 합니다.

### 참고 (지원·검토)
- **run_desktop_ui.py** – 이미 QAsync 루프를 설정하여 앱을 실행하므로 큰 수정은 없으나, 통합 후 정상 동작을 다시 확인합니다:contentReference[oaicite:7]{index=7}.
