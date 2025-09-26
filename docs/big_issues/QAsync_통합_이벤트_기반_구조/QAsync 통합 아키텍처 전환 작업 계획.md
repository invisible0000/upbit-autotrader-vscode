# QAsync 통합 아키텍처 전환 작업 계획

## 1단계: 애플리케이션 진입점 및 이벤트 루프 통합 (Foundation)
* **목표**: 애플리케이션의 시작점에서부터 `qasync`를 Qt 이벤트 루프로 설정하여, 모든 비동기 작업의 기준이 될 단일 이벤트 루프를 마련합니다.
* **주요 작업 폴더**:
    * `/` (루트 디렉토리)
    * `upbit_auto_trading/`
    * `upbit_auto_trading/ui/desktop/`

## 2단계: 핵심 인프라 레이어 리팩토링 (Core Infrastructure)
* **목표**: `UpbitPublicClient`를 포함한 모든 외부 API 통신 및 공유 리소스가 1단계에서 생성된 단일 이벤트 루프를 사용하도록 수정합니다. 이벤트 루프 종속성을 제거하고 안정성을 확보하는 핵심 단계입니다.
* **주요 작업 폴더**:
    * `upbit_auto_trading/infrastructure/external_apis/upbit/`
    * `upbit_auto_trading/infrastructure/external_apis/upbit/websocket/`

## 3단계: 주요 UI 컴포넌트 및 서비스 수정 (UI Components & Services)
* **목표**: 문제의 원인이었던 `CoinListWidget`을 포함하여, 비동기 데이터 처리가 필요한 핵심 UI 컴포넌트들이 `asyncSlot` 대신 표준 `async/await`를 사용하며 단일 루프 위에서 동작하도록 수정합니다.
* **주요 작업 폴더**:
    * `upbit_auto_trading/ui/desktop/screens/chart_view/`
    * `upbit_auto_trading/application/chart_viewer/`
    * `upbit_auto_trading/application/use_cases/`

## 4단계: 전체 시스템 아키텍처 통일 (System-wide Unification)
* **목표**: `asyncio.run()`, `new_event_loop()` 등 격리된 이벤트 루프를 생성하는 모든 코드를 찾아 제거하고, 전체 애플리케이션이 `qasync` 기반의 단일 이벤트 루프 아키텍처를 따르도록 통일합니다.
* **주요 작업 폴더**:
    * `upbit_auto_trading/ui/desktop/screens/` (전체 스크린)
    * `upbit_auto_trading/application/services/` (전체 서비스)
    * `upbit_auto_trading/presentation/`

## 5단계: 테스트 및 검증 (Verification)
* **목표**: 변경된 아키텍처가 기존 기능을 해치지 않고, 이벤트 루프 충돌 문제가 완전히 해결되었는지 검증하는 통합 테스트를 진행합니다.
* **주요 작업 폴더**:
    * `tests/`
