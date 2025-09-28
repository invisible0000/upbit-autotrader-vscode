# 🔧 QAsync 통합 리팩토링 작업 가이드

**작성일**: 2025년 9월 26일
**목적**: QAsync 기반 단일 이벤트 루프 아키텍처로 전환하는 구체적 작업 지침
**대상**: 모든 개발자 (GitHub Copilot 포함)

---

## 📋 작업 개요

이 문서는 현재 시스템의 다중 이벤트 루프 충돌 문제를 해결하기 위한 **단계별 리팩토링 가이드**입니다. 각 패턴별로 수정 전/후 코드와 함께 구체적인 작업 순서를 제시합니다.

---

## ⚖️ 아키텍처 불변식 (Architecture Invariants)

> **목적**: 전략 A의 핵심 규칙을 **불변식으로 못 박아** 이후 어떤 기능개발도 이 원칙을 깨지 못하도록 합니다.

1. **EventLoop 단일성(Singleton Main Loop)**: 프로세스 내 `asyncio` 이벤트 루프는 **QAsync 통합 루프 1개만 존재**한다.
2. **Loop 경계 금지**: `asyncio.new_event_loop()`, `asyncio.run()`, `loop.run_until_complete()` **전면 금지**.
3. **UI-Async 브리지 표준**: Qt 신호→`@asyncSlot`→`await service(...)` **단일 경로만 허용**.
4. **Loop-바운드 리소스 단일화**: `aiohttp.ClientSession`, `asyncio.Lock` 등 **모두 메인 루프에 바인딩**. 생성은 **지연 초기화(lazy)**로만 허용.
5. **태스크 생명주기 관리 강제**: 모든 `create_task`는 **TaskManager**를 통해 등록·정리.
6. **종료시 안전 정리**: 앱 종료 이벤트에서 **모든 태스크 취소→gather→세션/소켓 종료**를 표준 시퀀스로 강제.

> **왜 필요한가?**
> • 재발 방지. 불변식은 "예외 없음"의 선언이며, 문서·리뷰·테스트의 기준점이 됩니다.
> • 팀 내 논쟁 단절. "케이스별 예외"를 허용하면 다시 다중 루프가 잠입합니다(회귀).

---

## 🎯 수정 패턴 가이드

### 패턴 1: 격리 이벤트 루프 제거

> **⚠️ 금지/허용 API 표** (개발자가 5초 안에 파악할 수 있도록)

| 분류     | 금지(Disallow)                                                             | 허용(Allow)                     |
| ------ | ------------------------------------------------------------------------ | ----------------------------- |
| 루프 제어  | `asyncio.new_event_loop()`, `asyncio.run()`, `loop.run_until_complete()` | **없음**                        |
| 루프 조회  | `asyncio.get_event_loop()` (비권장)                                         | `asyncio.get_running_loop()`  |
| UI 브리지 | 직접 스레드+루프 생성                                                             | `@qasync.asyncSlot` + `await` |
| 태스크    | fire-and-forget (참조 미보관)                                                 | `TaskManager.create(...)` 등록  |
| 세션/락   | 생성자 즉시 생성                                                                | **lazy**: 첫 `await` 시 생성      |

> **이유**: 개발자가 "무엇이 안 되고 무엇이 되는지"를 5초 안에 파악하도록 강제. **리뷰 기준**이 됩니다.

**문제 패턴**:

```python
# ❌ 제거해야 할 패턴
def _load_data(self):
    import asyncio
    import threading

    def load_isolated():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            result = new_loop.run_until_complete(async_call())
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)

    thread = threading.Thread(target=load_isolated, daemon=True)
    thread.start()
```

**수정 패턴**:

```python
# ✅ QAsync 통합 패턴
from qasync import asyncSlot

class Widget(QWidget):
    def __init__(self):
        super().__init__()
        self._task_manager = TaskManager()  # 태스크 관리자 추가

    @asyncSlot()
    async def _load_data(self):
        """QAsync 환경에서 안전한 비동기 데이터 로드"""
        try:
            result = await self.service.get_data()
            self._update_ui(result)
        except Exception as e:
            self._logger.error(f"데이터 로드 실패: {e}")
            self._handle_error(e)

    def _on_button_click(self):
        """버튼 클릭 → 비동기 작업 시작"""
        task = asyncio.create_task(self._load_data())
        self._task_manager.add_task(task)
```

### 패턴 2: 동기/비동기 혼합 호출 수정

**문제 패턴**:

```python
# ❌ 루프 상태에 따른 분기 처리
def publish(self, event):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(self._async_publish(event))
    else:
        loop.run_until_complete(self._async_publish(event))  # QAsync 충돌!
```

**수정 패턴**:

```python
# ✅ QAsync 환경 가정 패턴
def publish(self, event):
    """QAsync 환경에서는 항상 실행 중인 루프 가정"""
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(self._async_publish(event))
        # 태스크 관리자에 등록 (선택적)
        if hasattr(self, '_task_manager'):
            self._task_manager.add_task(task)
        return task
    except RuntimeError:
        # QAsync 환경이 아닌 경우 에러 로깅 및 복구
        self._logger.error("QAsync 환경이 아닙니다. 시스템 설정을 확인하세요.")
        raise
```

### 패턴 3: Infrastructure Layer 루프 인식

**문제 패턴**:

```python
# ❌ 루프 바인딩 문제
class UpbitPublicClient:
    def __init__(self):
        self._session = aiohttp.ClientSession()  # 현재 루프에 바인딩
        self._locks = {}
```

**수정 패턴**:

```python
# ✅ 루프 인식 생성 패턴
class UpbitPublicClient:
    def __init__(self, loop=None):
        self._loop = loop  # 명시적 루프 저장 (None은 나중에 추론)
        self._session = None
        self._locks = {}
        self._initialized = False

    async def _ensure_initialized(self):
        """지연 초기화로 루프 바인딩 문제 해결"""
        if not self._initialized:
            if self._loop is None:
                self._loop = asyncio.get_running_loop()

            # 루프 확정 후 리소스 생성
            self._session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(loop=self._loop)
            )
            self._initialized = True

    async def make_request(self, ...):
        await self._ensure_initialized()
        # 기존 로직...
```

#### LoopGuard (런타임 가드)

런타임에서 잘못된 루프 사용을 **즉시 감지·격리**합니다:

```python
# infrastructure/runtime/loop_guard.py
import asyncio, logging
log = logging.getLogger(__name__)

class LoopGuard:
    def __init__(self):
        self._main = None

    def set_main(self, loop: asyncio.AbstractEventLoop):
        self._main = loop

    def ensure_main(self, *, where: str):
        cur = asyncio.get_running_loop()
        if self._main is None:
            self._main = cur
        elif self._main is not cur:
            # hard-fail or auto-recreate policy 선택 가능
            log.error("EventLoop breach at %s", where)
            raise RuntimeError(f"Wrong loop at {where}")
```

**적용 지점**:

- `UpbitPublicClient._ensure_initialized()` 시작부
- `DomainEventPublisher.publish()`(async) 시작부
- `WebSocketManager.start()` 진입부

**이유**: 개발 환경/운영 중 **루프 오염(rogue loop)**을 조기 발견. 임시 봉합이 아닌 "구조적 안전장치".

### 패턴 4: 태스크 생명주기 관리

**추가 패턴**:

```python
# ✅ 태스크 매니저 패턴
class TaskManager:
    """QAsync 환경에서 태스크 생명주기 관리"""

    def __init__(self):
        self._tasks: Set[asyncio.Task] = set()
        self._logger = logging.getLogger(__name__)

    def add_task(self, task: asyncio.Task, name: str = None) -> asyncio.Task:
        """태스크 등록 및 완료 시 자동 정리"""
        self._tasks.add(task)
        task_name = name or f"task-{id(task)}"

        def cleanup_callback(task):
            self._tasks.discard(task)
            if task.cancelled():
                self._logger.debug(f"태스크 취소됨: {task_name}")
            elif task.exception():
                self._logger.error(f"태스크 실패: {task_name}, {task.exception()}")
            else:
                self._logger.debug(f"태스크 완료: {task_name}")

        task.add_done_callback(cleanup_callback)
        return task

    async def cleanup_all(self):
        """모든 태스크 정리 (앱 종료 시 호출)"""
        if not self._tasks:
            return

        self._logger.info(f"태스크 {len(self._tasks)}개 정리 시작")

        # 모든 태스크 취소
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # 완료 대기
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        self._logger.info("모든 태스크 정리 완료")
```

---

## 📁 수정 대상 파일 목록 (우선순위별)

### Phase 1: Critical Issues (즉시 수정 필요)

#### 1.1 진입점 및 앱 초기화

```
📁 root/
├── run_desktop_ui.py                    ⭐ Priority 1
│   ├── 라인 456-479: QEventLoop 이중 생성 문제
│   └── 수정: qasync.QApplication 사용, 단일 진입점 정리

📁 upbit_auto_trading/ui/desktop/
├── main_window.py                       ⭐ Priority 2
│   ├── 라인 362: asyncio.create_task 호출
│   └── 수정: TaskManager 도입, 생명주기 관리
```

#### 1.2 UI 위젯 (격리 루프 제거)

```
📁 upbit_auto_trading/ui/desktop/screens/chart_view/widgets/
├── coin_list_widget.py                  🔥 Critical
│   ├── 라인 232: new_event_loop() + threading
│   ├── 라인 424: 새로고침 시 격리 루프
│   └── 수정: @asyncSlot 패턴으로 전환
│
├── legacy/coin_list_widget_new.py       🔥 Critical
│   ├── 라인 131: new_event_loop() 패턴
│   └── 수정: 레거시 제거 또는 QAsync 패턴 적용
│
├── legacy/coin_list_widget_problematic.py   🔥 Critical
│   ├── 라인 138: 동일한 격리 루프 문제
│   └── 수정: 파일 삭제 고려
```

#### 1.3 로깅 UI 시스템

```
📁 upbit_auto_trading/ui/widgets/logging/
├── event_driven_log_viewer_widget.py    🔥 Critical
│   ├── 라인 202: new_event_loop() + run_until_complete
│   ├── 라인 333: asyncio.create_task 호출
│   └── 수정: QAsync 환경에서 이벤트 버스 시작
│
├── event_driven_logging_configuration_section.py   🔥 Critical
│   ├── 라인 336: 동일한 격리 루프 패턴
│   └── 수정: 로그 뷰어와 동일한 패턴 적용
```

#### 1.4 Infrastructure Layer

```
📁 upbit_auto_trading/infrastructure/services/
├── api_key_service.py                   🔥 Critical
│   ├── 라인 326: new_event_loop() + threading
│   ├── 라인 396: asyncio.run() 직접 호출
│   └── 수정: QAsync 환경에서 비동기 테스트

📁 upbit_auto_trading/infrastructure/events/
├── domain_event_publisher_impl.py       🔥 Critical
│   ├── 라인 21: get_event_loop() + run_until_complete
│   └── 수정: get_running_loop() 사용
```

### Phase 2: High Priority (안정화)

#### 2.1 전략 관리 시스템

```
📁 upbit_auto_trading/ui/desktop/screens/strategy_management/tabs/trigger_builder/
├── trigger_builder_tab.py               ⚡ High
│   ├── 라인 131: get_event_loop() 혼합 패턴
│   ├── 라인 137: run_until_complete 사용
│   ├── 라인 140: asyncio.run() 직접 호출
│   └── 수정: 통합 비동기 패턴 적용
```

#### 2.2 차트 뷰 시스템

```
📁 upbit_auto_trading/ui/desktop/screens/chart_view/
├── chart_view_screen.py                 ⚡ High
│   ├── 라인 255: asyncio.create_task로 이벤트 버스 시작
│   └── 수정: TaskManager 통합
│
├── presenters/orderbook_presenter.py    ⚡ High
│   ├── 라인 94: asyncio.create_task 사용
│   ├── 라인 175: 백업 새로고침 태스크
│   └── 수정: TaskManager 등록, 에러 핸들링 강화
```

#### 2.3 Infrastructure Services

```
📁 upbit_auto_trading/infrastructure/external_apis/upbit/
├── upbit_public_client.py               ⚡ High
│   ├── 라인 151: ClientSession 직접 생성
│   └── 수정: 루프 인식 지연 초기화 패턴
│
├── upbit_private_client.py              ⚡ High
│   └── 수정: upbit_public_client와 동일 패턴

├── websocket/core/websocket_manager.py  ⚡ High
│   ├── 라인 618: get_running_loop() 사용
│   └── 검토: QAsync 호환성 확인
```

### Phase 3: Medium Priority (최적화)

#### 3.1 Application Layer

```
📁 upbit_auto_trading/application/services/
├── websocket_application_service.py     ⭐ Medium
│   ├── 라인 322: 헬스 체크 태스크 생성
│   └── 수정: TaskManager 통합
│
├── chart_market_data_service.py         ⭐ Medium
│   ├── 라인 232: 데이터 수집 태스크
│   └── 수정: 태스크 생명주기 관리
```

#### 3.2 이벤트 시스템

```
📁 upbit_auto_trading/infrastructure/events/
├── bus/in_memory_event_bus.py           ⭐ Medium
│   ├── 라인 308: get_event_loop() 사용
│   └── 수정: QAsync 호환 패턴
│
├── event_system_initializer.py          ⭐ Medium
│   └── 검토: 초기화 패턴 QAsync 최적화
```

#### 3.3 기타 서비스

```
📁 upbit_auto_trading/infrastructure/services/
├── orderbook_data_service.py            ⭐ Medium
│   ├── @asyncSlot 사용 (이미 QAsync 호환)
│   └── 검토: 태스크 관리 최적화
│
├── websocket_market_data_service.py     ⭐ Medium
│   └── 검토: 연결 태스크 생명주기 관리
```

### Phase 4: Legacy & Cleanup

#### 4.1 Legacy 위젯들

```
📁 upbit_auto_trading/ui/desktop/screens/chart_view/widgets/legacy/
├── coin_list_widget_legacy.py           🗑️ Remove
├── orderbook_widget_legacy.py           🗑️ Remove
├── orderbook_widget_refactored.py       🗑️ Remove
└── 수정: 단계적 제거 또는 QAsync 패턴 적용
```

#### 4.2 테스트 및 예제

```
📁 tests/
├── **/*.py (asyncio.run 사용 파일들)    🔧 Update
└── 수정: pytest-asyncio + QAsync 호환 패턴

📁 examples/
├── **/*.py (격리 루프 사용)             🔧 Update
└── 수정: QAsync 예제로 전환
```

---

## 🛠️ 단계별 작업 순서 (회귀 방지 중심)

### Step 0: 가드레일 선배치 (신규)

**목표**: 회귀 방지 인프라 구축

1. **pre-commit + CI 정적 검사**:

   ```bash
   # 금지 패턴 검사 (빌드 실패 시 중단)
   Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "new_event_loop|run_until_complete|asyncio\.run\("
   ```

2. **pytest 고정장치 도입**:

   ```python
   # tests/conftest.py
   import asyncio, pytest, qasync

   @pytest.fixture(scope="session")
   def qasync_loop():
       app = qasync.QApplication([])
       loop = qasync.QEventLoop(app)
       asyncio.set_event_loop(loop)
       yield loop
       loop.close()

   @pytest.fixture(autouse=True)
   def _force_running_loop(qasync_loop):
       # 각 테스트가 실행 중 루프를 공유
       pass
   ```

3. **LoopGuard 런타임 가드 배치**:
   - `infrastructure/runtime/loop_guard.py` 생성
   - 핵심 Infrastructure 클래스에 가드 추가

> **이유**: 가드레일 없이는 Step1에서 고친 코드를 Step3에서 되돌릴 수 있음.

### Step 1: 진입점/런타임 커널(AppKernel) 도입

**목표**: 단일 조립점으로 책임 명료화

1. **AppKernel 신규 생성** (`runtime/app_kernel.py`):

   ```python
   class AppKernel:
       def __init__(self):
           self.loop_guard = LoopGuard()
           self.task_manager = TaskManager()
           self.event_bus = None
           self.http_clients = {}
           self.rate_limiter = None

       @classmethod
       def bootstrap(cls, app):
           kernel = cls()
           # loop_guard/task_manager/event_bus 준비
           return kernel
   ```

2. **진입점 수정** (`run_desktop_ui.py`):

   ```python
   # 수정 전 확인사항
   - QEventLoop 이중 생성 여부
   - asyncio.set_event_loop 다중 호출
   - loop.run_until_complete + loop.run_forever 혼재

   # 수정 후 목표 (AppKernel이 유일한 조립자)
   import qasync
   from runtime.app_kernel import AppKernel

   app = qasync.QApplication(sys.argv)
   loop = qasync.QEventLoop(app); asyncio.set_event_loop(loop)
   kernel = AppKernel.bootstrap(app)  # loop_guard/task_manager/event_bus 준비

   with loop:
       try:
           return loop.run_until_complete(kernel.run())
       finally:
           loop.run_until_complete(kernel.shutdown())
   ```

> **이유**: 런타임 소유권을 한 곳으로 모아 **책임·수명주기**를 명료화.

### Step 2: Infrastructure 먼저 고정 (선행 전환)

**목표**: UI 리팩토링 전 백엔드 안정화

1. **HTTP 클라이언트 루프 인식 패턴**:

   ```python
   # upbit_public_client.py/upbit_private_client.py 수정
   class UpbitPublicClient:
       def __init__(self, loop=None, loop_guard=None):
           self._loop = loop
           self._session = None
           self._loop_guard = loop_guard

       async def _ensure_initialized(self):
           if not self._initialized:
               if self._loop_guard:
                   self._loop_guard.ensure_main(where="UpbitPublicClient._ensure_initialized")
               if self._loop is None:
                   self._loop = asyncio.get_running_loop()
               self._session = aiohttp.ClientSession()
   ```

2. **이벤트 퍼블리셔 혼용 제거**:

   ```python
   # domain_event_publisher_impl.py
   # Before: loop.is_running() 분기 + run_until_complete
   # After: 단순화
   asyncio.get_running_loop().create_task(self._async_publish(evt))
   ```

> **이유**: UI보다 인프라를 먼저 고정해야 UI 리팩토링 시 **리소스 바인딩**이 안전.

### Step 3: UI 전면 QAsync화

**목표**: 모든 UI 컴포넌트를 통합 패턴으로 전환

1. **격리 루프 제거**:

   ```python
   # coin_list_widget.py 등
   # Before: threading + new_event_loop
   # After: @asyncSlot 통일
   from qasync import asyncSlot

   @asyncSlot()
   async def _load_real_data(self):
       data = await self._service.load()
       self._apply_data(data)
   ```

2. **공통 베이스 위젯** (`ui/common/AsyncWidgetBase.py` 신설, 선택적):

   - `attach_bus`, `attach_task_manager` 제공
   - 모든 `create_task`는 `TaskManager` 경유

> **이유**: UI 파편적 수정이 아니라 **한 번의 패턴 치환**으로 회귀 위험 축소.

### Step 4: 종료 시퀀스/관측성

**목표**: 안전한 생명주기와 모니터링

1. **AppKernel.shutdown() 표준화**:
   - 1) 새 작업 수락 중지 → 2) 태스크 취소/집합 → 3) 세션/소켓 종료 → 4) 로그 flush

2. **구조화 로깅**: `cid`(correlation-id), `comp`(component), `phase` 태그 통일

3. **이벤트 버스 백프레셔 정책**: 고빈도 토픽(tick/호가)은 **coalescing(latest-only)** 큐로 설정

4. **태스크 명명 규칙**: `TaskManager.add(task, name="mod:comp:op")`

> **이유**: 종료·장애시 **유실/유출/누수** 차단 + 원인 추적성 확보.

---

## 📋 검증 체크리스트

### CI/CD 통합 검사 명령어

```bash
# pre-commit hook 또는 CI 파이프라인에 추가
# 1. 금지 패턴 정적 검사 (실패 시 빌드 중단)
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "new_event_loop|run_until_complete|asyncio\.run\(" | ForEach-Object { Write-Error "금지된 패턴 발견: $_"; exit 1 }

# 2. QAsync 패턴 적용 확인
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "@asyncSlot|qasync\."

# 3. 태스크 관리 패턴 확인
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "create_task.*TaskManager|\.add_task\("

# 4. LoopGuard 적용 확인
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "loop_guard\.ensure_main"
```

### 테스트 환경 확인

```python
# tests/conftest.py가 올바르게 설정되었는지 확인
pytest tests/ -v
# → 모든 테스트가 qasync 환경에서 실행되는지 확인

# 시스템 실행 테스트
python run_desktop_ui.py
# → 이벤트 루프 충돌 없이 정상 시작되는지 확인

# 핵심 기능 테스트
# → 코인리스트 로드, 호가창 연결, 로깅 시스템 정상 동작 확인
```

### 성공 지표

- [ ] **이벤트 루프 오류 제로화**: `bound to a different event loop` 오류 발생하지 않음
- [ ] **UI 반응성 유지**: 모든 위젯이 정상적으로 데이터를 로드하고 업데이트
- [ ] **백그라운드 태스크 정상화**: asyncio.create_task로 생성된 모든 태스크가 정상 완료
- [ ] **메모리 사용량 안정**: 태스크 누수 없이 메모리 사용량 일정 유지
- [ ] **시스템 종료 정상화**: Ctrl+C 또는 창 닫기 시 모든 리소스 정상 정리

---

## 🚨 주의사항 및 함정

### 1. QAsync 관련 주의점

```python
# ❌ 피해야 할 패턴
QApplication.exec()  # 대신 qasync 버전 사용
asyncio.set_event_loop(None)  # QAsync 환경에서 금지
asyncio.new_event_loop()  # 격리 루프 생성 금지

# ✅ 권장 패턴
qasync.QApplication.exec()
# 루프 해제 없이 QAsync가 관리하도록 위임
```

### 2. Infrastructure Layer 함정

```python
# ❌ 생성자에서 바로 세션 생성
def __init__(self):
    self._session = aiohttp.ClientSession()  # 루프 바인딩!

# ✅ 지연 초기화 패턴
async def _ensure_session(self):
    if not self._session:
        self._session = aiohttp.ClientSession()
```

### 3. 태스크 관리 함정

```python
# ❌ Fire-and-forget 패턴
asyncio.create_task(some_coro())  # 참조 분실로 가비지 컬렉션 위험

# ✅ 참조 보관 패턴
task = asyncio.create_task(some_coro())
self._tasks.add(task)
task.add_done_callback(self._tasks.discard)
```

---

## 📞 지원 및 문의

### 개발 중 문제 발생 시

1. **이벤트 루프 오류**: 해당 파일의 패턴을 이 가이드와 비교
2. **QAsync 관련 문제**: qasync 공식 문서 참조
3. **Infrastructure 바인딩 문제**: 지연 초기화 패턴 적용
4. **성능 이슈**: 태스크 매니저 도입 검토

### 코드 리뷰 체크포인트

- [ ] `new_event_loop()`, `set_event_loop()`, `asyncio.run()` 사용 금지
- [ ] `@asyncSlot` 데코레이터 적절한 사용
- [ ] `create_task()` 사용 시 TaskManager 등록
- [ ] Infrastructure Layer의 지연 초기화 패턴 준수
- [ ] 에러 핸들링 및 로깅 적절한 구현

---

**이 가이드를 참조하여 단계별로 작업하면 QAsync 통합 아키텍처로 안전하게 전환할 수 있습니다.**

**작성**: GitHub Copilot
**마지막 업데이트**: 2025년 9월 26일
