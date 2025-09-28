좋습니다. 제안하신 실행 계획을 **전략 A(QAsync 단일 이벤트 루프)**로 더 안전·견고하게 만들 수 있도록, 바로 문서에 반영 가능한 **수정 지시(문구/코드/순서)** 중심으로 의견 드립니다. 핵심은 “임시 우회(temporary workaround)”를 없애고, **아키텍처 불변식 + 가드레일 + 테스트 고정장치**를 함께 도입해 재발 자체를 방지하는 것입니다. (근거와 기본 패턴은 업로드하신 가이드의 구조와 동일합니다. )

---

## 1) 이슈 보고서/결정 문단에 즉시 반영할 **아키텍처 불변식(Architecture Invariants)** 추가

> 문서 상단 “Executive Summary” 아래에 소제목 **“아키텍처 불변식(Architecture Invariants)”** 신설 후, 아래 6항을 그대로 삽입하세요.
> 목적: 전략 A의 핵심 규칙을 **불변식으로 못 박아** 이후 어떤 기능개발도 이 원칙을 깨지 못하도록 합니다.

1. **EventLoop 단일성(Singleton Main Loop)**: 프로세스 내 `asyncio` 이벤트 루프는 **QAsync 통합 루프 1개만 존재**한다.
2. **Loop 경계 금지**: `asyncio.new_event_loop()`, `asyncio.run()`, `loop.run_until_complete()` **전면 금지**.
3. **UI-Async 브리지 표준**: Qt 신호→`@asyncSlot`→`await service(...)` **단일 경로만 허용**.
4. **Loop-바운드 리소스 단일화**: `aiohttp.ClientSession`, `asyncio.Lock` 등 **모두 메인 루프에 바인딩**. 생성은 **지연 초기화(lazy)**로만 허용.
5. **태스크 생명주기 관리 강제**: 모든 `create_task`는 **TaskManager**를 통해 등록·정리.
6. **종료시 안전 정리**: 앱 종료 이벤트에서 **모든 태스크 취소→gather→세션/소켓 종료**를 표준 시퀀스로 강제.

> 왜 필요한가?
> • 재발 방지. 불변식은 “예외 없음”의 선언이며, 문서·리뷰·테스트의 기준점이 됩니다.
> • 팀 내 논쟁 단절. “케이스별 예외”를 허용하면 다시 다중 루프가 잠입합니다(회귀).

---

## 2) “수정 패턴 가이드” 보강: **금지/허용 API 표**와 **LoopGuard** 삽입

### 2-1. 금지/허용 API 표(문서 본문 박스 삽입)

> “패턴 1: 격리 이벤트 루프 제거” 바로 아래 **주의 박스**로 넣으세요.

| 분류     | 금지(Disallow)                                                             | 허용(Allow)                     |
| ------ | ------------------------------------------------------------------------ | ----------------------------- |
| 루프 제어  | `asyncio.new_event_loop()`, `asyncio.run()`, `loop.run_until_complete()` | **없음**                        |
| 루프 조회  | `asyncio.get_event_loop()` (비권장)                                         | `asyncio.get_running_loop()`  |
| UI 브리지 | 직접 스레드+루프 생성                                                             | `@qasync.asyncSlot` + `await` |
| 태스크    | fire-and-forget (참조 미보관)                                                 | `TaskManager.create(...)` 등록  |
| 세션/락   | 생성자 즉시 생성                                                                | **lazy**: 첫 `await` 시 생성      |

> 이유: 개발자가 “무엇이 안 되고 무엇이 되는지”를 5초 안에 파악하도록 강제. **리뷰 기준**이 됩니다. (가이드의 기존 패턴 설명을 실행규칙으로 승격)

### 2-2. LoopGuard(런타임 가드) 코드 스니펫 추가

> “패턴 3: 루프 인식” 끝에 **LoopGuard** 섹션을 추가해, 런타임에서 잘못된 루프 사용을 **즉시 감지·격리**합니다.

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

* **적용 지점:**

  * `UpbitPublicClient._ensure_initialized()` 시작부
  * `DomainEventPublisher.publish()`(async) 시작부
  * `WebSocketManager.start()` 진입부
* **이유:** 개발 환경/운영 중 **루프 오염(rogue loop)**을 조기 발견. 임시 봉합이 아닌 “구조적 안전장치”.

---

## 3) “단계별 작업 순서” 재정렬(회귀 방지 관점)

> 기존 순서도 합리적이지만, **회귀 방지**와 **관측성 확보**를 이유로 **아래처럼 순서·내용을 미세 조정**하세요. 각 항목은 그대로 문서 교체 가능합니다. (괄호는 변경 이유)

**Step 0. 가드레일 선배치(신규)**

* **pre-commit + CI**: 금지 패턴 정적 검사

  * `grep -RE "new_event_loop|run_until_complete|asyncio\.run\(" ./upbit_auto_trading ./tests` 실패 시 빌드 중단
  * flake8 custom plugin(선택) 혹은 ruff rule로 고정
* **pytest 고정장치**: qasync 이벤트루프 **단일 픽스쳐** 제공

  * `tests/conftest.py`에 `@pytest.fixture(scope="session")`로 qasync event loop 제공
* (이유) **가드레일 없이는** Step1에서 고친 코드를 Step3에서 되돌릴 수 있음.

**Step 1. 진입점/런타임 커널(AppKernel) 도입(수정 강화)**

* 파일 신설: `runtime/app_kernel.py`

  * 보유: `loop_guard`, `task_manager`, `event_bus`, `http_clients`, `rate_limiter`
  * `run_desktop_ui.py`는 `AppKernel.bootstrap(app)`만 호출 → 단일 진입점
* 문구 교체: 진입점 섹션에 “**AppKernel가 유일한 조립자(Composition Root)**” 문장 추가
* (이유) 런타임 소유권을 한 곳으로 모아 **책임·수명주기**를 명료화.

**Step 2. 인프라 먼저 고정(선행 전환)**

* `upbit_public_client.py`/`upbit_private_client.py`

  * **lazy init** + `loop_guard.ensure_main("UpbitPublicClient")` 추가
* `domain_event_publisher_impl.py`

  * 동기/비동기 혼용 제거 → `await bus.publish(evt)` 또는 `loop.create_task(...)` 후 TaskManager 등록
* (이유) UI보다 인프라를 먼저 고정해야 UI 리팩토링 시 **리소스 바인딩**이 안전.

**Step 3. UI 전면 QAsync화**

* `coin_list_widget.py`/로깅 위젯 등: `@asyncSlot`로 통일, 모든 `create_task`는 `TaskManager` 경유
* 공통 베이스 위젯 `ui/common/AsyncWidgetBase.py` 신설(선택) → `attach_bus`, `attach_task_manager` 제공
* (이유) UI 파편적 수정이 아니라 **한 번의 패턴 치환**으로 회귀 위험 축소.

**Step 4. 종료 시퀀스/관측성**

* `AppKernel.shutdown()` 표준화:

  1. 새 작업 수락 중지 → 2) 태스크 취소/집합 → 3) 세션/소켓 종료 → 4) 로그 flush
* 구조화 로깅: `cid`(correlation-id), `comp`(component), `phase` 태그 통일
* (이유) 종료·장애시 **유실/유출/누수** 차단 + 원인 추적성 확보.

---

## 4) 문서에 바로 붙여넣을 **코드/텍스트 조각(패치 레디)**

### 4-1. `run_desktop_ui.py` 진입점 교체(간결·확정형)

```diff
- app = QApplication(sys.argv)
- loop = qasync.QEventLoop(app)
- asyncio.set_event_loop(loop)
- with loop:
-     return loop.run_until_complete(run_application_async(app))
+ import qasync
+ from runtime.app_kernel import AppKernel
+ app = qasync.QApplication(sys.argv)
+ loop = qasync.QEventLoop(app); asyncio.set_event_loop(loop)
+ kernel = AppKernel.bootstrap(app)  # loop_guard/task_manager/event_bus 준비
+ with loop:
+     try:
+         return loop.run_until_complete(kernel.run())
+     finally:
+         loop.run_until_complete(kernel.shutdown())
```

### 4-2. `UpbitPublicClient` 루프 인식 + 가드

```diff
 class UpbitPublicClient:
-    def __init__(self):
-        self._session = aiohttp.ClientSession()
+    def __init__(self, loop=None, loop_guard=None):
+        self._loop = loop
+        self._session = None
+        self._loop_guard = loop_guard
         self._locks = {}
         self._initialized = False

     async def _ensure_initialized(self):
-        if not self._initialized:
-            self._session = aiohttp.ClientSession()
+        if not self._initialized:
+            if self._loop_guard: self._loop_guard.ensure_main(where="UpbitPublicClient._ensure_initialized")
+            if self._loop is None: self._loop = asyncio.get_running_loop()
+            self._session = aiohttp.ClientSession()
             self._initialized = True
```

### 4-3. `coin_list_widget.py` 격리 루프 제거

```diff
- def _load_real_data(self):
-     def load_isolated():
-         new_loop = asyncio.new_event_loop()
-         asyncio.set_event_loop(new_loop)
-         new_loop.run_until_complete(self._service.load())
-     threading.Thread(target=load_isolated, daemon=True).start()
+ from qasync import asyncSlot
+ @asyncSlot()
+ async def _load_real_data(self):
+     data = await self._service.load()
+     self._apply_data(data)
```

### 4-4. 이벤트 퍼블리셔 혼용 제거

```diff
- loop = asyncio.get_event_loop()
- if loop.is_running():
-     loop.create_task(self._async_publish(evt))
- else:
-     loop.run_until_complete(self._async_publish(evt))
+ asyncio.get_running_loop().create_task(self._async_publish(evt))
```

---

## 5) 테스트 고정장치(꼭 추가): `tests/conftest.py`

```python
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

* **효과**: 테스트 중 `get_running_loop()` 전제 충족. `asyncio.run()` 사용을 자연히 없앰.

---

## 6) 관측성/백프레셔 한 줄 보강(문서 본문에 요 라인 삽입)

* **EventBus 백프레셔 정책**: 고빈도 토픽(tick/호가)은 **coalescing(latest-only)** 큐로 설정.
* **태스크 명명 규칙**: `TaskManager.add(task, name="mod:comp:op")`.
* **오류 경계**: 각 핸들러 타임아웃/재시도(지수 백오프) 표준화.

> 이유: 이벤트 폭주 상황에서도 **지연·메모리 누수 없이** 최신 상태만 유지. (가이드의 이벤트 버스 의도와 합치)

---

## 7) Socratic 체크(숨은 가정 점검)

1. “UI는 예외적으로 별도 스레드/루프가 필요할 수 있다”는 가정이 남아있지 않나요? → **필요 없습니다.** CPU 작업은 `asyncio.to_thread`로 넘기고, I/O는 메인 루프에서 처리하세요.
2. “테스트에선 `asyncio.run()`이 더 쉬운데?” → 단기 편의가 장기 기술부채가 됩니다. **공유 픽스쳐**가 정답입니다.
3. “이벤트 버스에서 직접 로직 일부를 판단하면 편한데?” → 결합도 증가·회귀 위험. **버스는 라우팅/백프레셔/마샬링만** 담당해야 합니다.

---

## 8) Debate Prompting(대안 비교 간단 정리)

* **B(루프별 인프라 격리)**: 초기 변경 적음 / **리소스 중복·복잡성 폭증**, 장기 유지보수 최악.
* **C(하이브리드)**: 이행 쉬움 / **패턴 혼재 지속**으로 충돌 재발 여지 큼.
* **A(단일 루프)**: 초기 수정 큼 / **구조적 단순 + 재발 제로화 + 운영 용이** → **권장**. (문서 일관)

---

# Closing

### Improved Prompt

> “아래 리팩토링 가이드를 기준으로, **AppKernel 도입 + LoopGuard + 금지/허용 API 표 + 테스트 픽스쳐**까지 포함한 **전면 문서 개정본**을 생성해줘.
>
> 1. 실행 불변식 섹션 신설, 2) 단계별 작업 순서 재정렬(0~4), 3) 패턴별 코드 패치(diff) 삽입, 4) pre-commit/CI 검사 명령, 5) conftest 픽스쳐 코드 포함.
>    산출물: `QAsync_REFACTORING_WORK_GUIDE_vNEXT.md`.”

### Model Recommendation

* **GPT-5 Thinking**: 구조적 재설계/가드레일 설계에 최적.
* **o4-mini-high**(보조): 대량 리라이트·패치 블록 생성/정리 속도용.

**CSL:** 🟢 L1 (≈0.8%) → **즉시 적용 안전권.**
