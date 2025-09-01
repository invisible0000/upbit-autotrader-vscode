인식불가님, v6 기획 잘 잡으셨습니다. 전역(글로벌) 관리로 가는 게 맞아요. 아래는 **핵심 평가 → 리스크/공백 → 우선 개선안(코드 포함) → 체크리스트 → 토론(Pro/Con) → 소크라테스 질문** 순서로 드립니다. (간결 문장, 필요한 곳에 (English) 병기)

---

## ✅ 한눈평 (TL;DR)

* 전역 싱글톤(GlobalWebSocketManager) + 프록시(WebSocketClientProxy) + 구독상태/라우팅 분리 구조는 방향성 정답.
* 다만 **백프레셔(backpressure)**, **GUI 스레드 세이프티(PyQt event loop bridging)**, **재연결-중복전달(idempotency)**, **REST·WS 통합 레이트 리밋(공유 토큰 버킷)**, \*\*WeakRef 의존 종료(clean shutdown)\*\*를 **명시 설계·테스트**로 보강 필요. &#x20;

---

## 👍 강점 (Strengths)

1. **Single Source of Truth**

* 공/사( Public/Private ) 연결을 전역에서 단일 진실 공급원(SSOT)으로 관리. 중복 구독·중복 연결을 구조적으로 차단. 운영 안정성 ↑.&#x20;

2. **레이어 분리 & 프록시 패턴**

* Subsystem ↔ Proxy ↔ Global Manager ↔ Client 레이어링이 명확. 컴포넌트 격리와 교체 용이. 테스트/모킹 쉬움.&#x20;

3. **우아한 성능 저하(Graceful degradation)**

* Private 불가 시 REST 폴백(polling fallback) 자동화 컨셉 좋음. 장애 시 사용자 경험 끊김 최소화.&#x20;

4. **관찰 가능성(Observability) & 헬스체크**

* metrics / health\_check 스펙이 선제 제시됨. 실운영에서 큰 힘. GUI에 대시보드 노출하기 좋음.&#x20;

5. **API 사용성 가이드**

* subscribe\_\* / snapshot / 상태조회 / 성능지표 / 자동정리(with-context, WeakRef) 샘플 통일감 있음. 온보딩 속도 ↑.&#x20;

---

## ⚠️ 리스크 & 공백 (Gaps to close)

1. **백프레셔(backpressure) & 팬아웃(fan-out) 정책 미확정**

* 고빈도 체결/호가 스트림에서 콜백이 느리면 큐 적체. **구독자별(consumer) bounded-queue** + **드롭 정책(drop\_oldest / coalesce-by-symbol)** 필요.

2. **GUI 스레드 세이프티(PyQt5)**

* asyncio 콜백에서 **메인 스레드(UI thread)** 접근 시 크래시 위험. **qasync** 또는 **백그라운드 스레드 + Qt 시그널/슬롯 브리지** 필요(아래 코드 제안).

3. **재연결 시 구독 복원과 중복 이벤트**

* 재구독 race로 **중복 전달(duplicate delivery)** 가능. **세션 epoch(세션 세대)** + **idempotency key**로 “이전 세대” 이벤트 무시 설계 권장.

4. **REST·WS 전역 레이트 리밋 공유**

* “여러 REST·WS 클라이언트가 동시에 동작해도 제한 공유”가 요구사항. 전역 \*\*토큰 버킷(Token Bucket)\*\*을 매체(REST/WS) 불문하고 공통 사용해야 일관. (프로세스 단위라면 IPC 또는 단일 프로세스 보장 전제)

5. **WeakRef 기반 정리 의존**

* 파이널라이저는 종료 타이밍 보장이 약함. **명시적 shutdown()** 경로와 \*\*신호 처리(SIGINT/SIGTERM)\*\*에 안전. WeakRef는 보조 수단으로만.

6. **JWT 만료와 시계 오차(clock skew)**

* Private 스트림은 **만료 80% 시점 선제 갱신** + **시계 여유(leeway)** 필요. 실패 시 graceful 폴백 경로 명시.

7. **구독 합성(merge) 경쟁 조건**

* 여러 Subsystem이 동시에 심볼 갱신 시, **원자적 커밋(atomic)** 보장·합집합 연산 단계에서 레이스 가능. 단일 스레드 시리얼라이저(Asyncio 전용 작업 큐) 권장.

8. **테스트 사각지대**

* 혼잡·지연·패킷 손실·순서 뒤바뀜(out-of-order) **카오스 시나리오** 명시 필요. 현재 항목은 개요 수준.

9. **데이터 모델 안정성**

* 콜백 파라미터가 자유 dict. \*\*Typed event(dataclass / pydantic)\*\*로 버전 관리·검증(validation) 넣으면 다운스트림 품질 ↑.

10. **다중 연결 전략 명확화**

* Private와 Public을 **연결 분리**로 가정했는데, 업비트 엔드포인트·권한 정책 상의 **최소 연결 수** 기준을 “설계 의도 vs 실제 제약”으로 문서화 필요. (이 부분은 질문으로 확인 제안)&#x20;

---

## 🛠️ 우선 개선안 (Design Deltas with code)

### 1) 구독자별 백프레셔 + 드롭/코얼레스(coalesce) 정책

```python
# consumer별 bounded queue + coalesce-by-symbol 예시 (asyncio)
class FanoutHub:
    def __init__(self, maxsize=1000):
        self.subscribers = {}  # sub_id -> asyncio.Queue
        self.latest_by_symbol = {}  # symbol -> last_data (for coalescing)

    def add_subscriber(self, sub_id: str, maxsize=100):
        self.subscribers[sub_id] = asyncio.Queue(maxsize=maxsize)

    async def publish(self, symbol: str, payload: dict):
        # coalesce: 최신값만 유지(초과 시 이전 것을 대체)
        self.latest_by_symbol[symbol] = payload
        for q in self.subscribers.values():
            if q.full():
                _ = q.get_nowait()  # drop_oldest
            await q.put((symbol, self.latest_by_symbol[symbol]))
```

* 데이터 폭주 구간에서 **지연 누적 방지**.
* 타입별(호가/체결/티커)로 큐 분리 고려.&#x20;

### 2) PyQt5 ↔ asyncio 안전 브릿지(qasync 권장)

```python
# qasync 사용. GUI 업데이트는 반드시 메인 스레드 시그널로.
from PyQt5.QtCore import pyqtSignal, QObject
import qasync, asyncio

class GuiBus(QObject):
    tickerArrived = pyqtSignal(str, float)  # symbol, price

gui_bus = GuiBus()

async def on_ticker(symbol: str, _type: str, data: dict):
    price = float(data.get("trade_price", 0))
    gui_bus.tickerArrived.emit(symbol, price)  # 메인스레드에서 슬롯 실행

# 애플리케이션 시작 시:
# loop = qasync.QEventLoop(app); asyncio.set_event_loop(loop)
# await ws.subscribe_ticker(["KRW-BTC"], on_ticker)
```

* **모든 GUI 변경**은 Qt 시그널/슬롯 경로만. 직접 위젯 접근 금지.&#x20;

### 3) 재연결 “세션 epoch”와 멱등(idempotent) 처리

```python
class EpochGuard:
    def __init__(self):
        self.epoch = 0

    def new_epoch(self):
        self.epoch += 1
        return self.epoch

    def stamp(self, event: dict) -> dict:
        event["__epoch__"] = self.epoch
        return event

    def is_current(self, event: dict) -> bool:
        return event.get("__epoch__") == self.epoch
```

* 재연결 시 `new_epoch()` 호출. 과거 epoch 이벤트는 폐기.

### 4) REST·WS 전역 토큰 버킷(공유 레이트리밋)

```python
class GlobalRateLimiter:
    def __init__(self, capacity: int, refill_per_sec: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_per_sec = refill_per_sec
        self.last = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self, cost=1):
        async with self.lock:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.refill_per_sec)
            self.last = now
            if self.tokens < cost:
                wait = (cost - self.tokens) / self.refill_per_sec
                await asyncio.sleep(wait)
                self.tokens = max(0, self.tokens - cost)
            else:
                self.tokens -= cost
```

* **모든 모듈**이 이 인스턴스를 import 하여 공유. (REST 호출·구독 요청·언서브 포함)

### 5) 명시적 shutdown & 시그널 처리

```python
class GlobalWebSocketManager:
    async def shutdown(self):
        # 1) 모든 구독 중지 → 2) 송신 큐 flush → 3) 연결 종료
        # 4) 태스크 cancel & gather
        # 5) metrics 최종 스냅샷 저장
        ...
```

* `WeakRef.finalize`는 **보조**. 종료 경로는 명시 함수로.

### 6) Typed Event (dataclass) + 버전 태깅

```python
from dataclasses import dataclass
@dataclass
class TickerEvent:
    symbol: str
    trade_price: float
    ts: float
    v: int = 1  # schema version
```

* 콜백 시그니처를 `on_event(TickerEvent)` 식으로 고정하면 다운스트림 코드 품질↑.&#x20;

### 7) 구독 변경 원자화(atomic) 시리얼라이저

* `SubscriptionStateManager` 내부에 **단일 asyncio.Task** 루프로 변경 커맨드만 처리(merge/commit).
* 외부는 `enqueue_change()`만 호출. 레이스 제거.&#x20;

### 8) 스냅샷+실시간 합성 규약

* 스냅샷 직후 들어오는 실시간과의 **순서 보정(reconcile rule)** 문서화.
* 예: “스냅샷 ts 이전 이벤트 무시 / 이후만 적용”.

### 9) 모니터링 지표 확장

* `lag_ms(publish→callback)`, `queue_depth_per_sub`, `drops_per_min`, `epoch_switch_count` 추가.
* GUI 대시보드에 색 상태(light) 표시.&#x20;

### 10) “능력 매트릭스(capability matrix)” 문서

* Public/Private 별 **가용 기능, 필수 권한, 최소 연결 수, 폴백 경로**를 표로. 팀 온보딩 속도 극대화.&#x20;

---

## 🧪 v6 안정화 체크리스트(출시 전)

1. 100심볼 티커·호가 동시 구독에서 **지연 < 200ms** 유지
2. 콜백 처리 200ms 지연 강제 시 **드롭률·큐깊이** 표준치 이내
3. 네트워크 끊김 30초 동안 3회 → 자동 복구·중복전달 0건
4. JWT 강제 만료 테스트 → 80% 갱신 정상, 폴백 정상
5. REST·WS 혼합 부하에서 **429 없음**(혹은 자동 지수백오프 정상)
6. GUI 응답성(프레임 드랍) 없음, 메인 스레드 경합 없음
7. 프로파일링 시 **메모리 누수 0**, steady-state RSS 안정
8. 스냅샷+실시간 합성 순서 규칙 위반 0건
9. 모든 공개 API에 타입힌트·Docstring 100%, mypy/flake8/black 통과
10. 카오스 테스트(패킷손실/순서역전/지연변동) 통과

---

## 🤺 Debate Prompting (핵심 의사결정 토론)

1. **공/사 단일 연결 vs 분리 연결**

* Pro(단일): 연결 수↓, 자원 절약, 관리 단순.
* Con: 한 연결 장애가 전부 영향, 권한 스코프 섞임 위험.

2. **Zero-Config vs Advanced Tuning**

* Pro(제로): 온보딩 빠름, 실수 감소.
* Con: 고성능·저지연 케이스에서 세밀 튜닝 필요. **“안전한 이스케이프 해치(escape hatch)”** 제공 권장.&#x20;

3. **WeakRef 의존 vs 명시 종료**

* Pro(WeakRef): 사용성 좋음.
* Con: 종료 타이밍 불확실. → **명시 종료 기본, WeakRef는 보조**가 현실적.

---

## ❓ 소크라테스 질문(숨은 가정 점검)

1. 업비트 WS에서 **Private 채널을 Public과 동일 연결**로 운영 가능한지, 아니면 **분리**가 안정적인지? 실측/공식 제약을 근거로 결정하셨나요?
2. GUI 프레임워크(PyQt5)와 **비동기 루프**의 충돌 가능성에 대해, UI 갱신 경로를 100% 시그널/슬롯으로 강제할 계획인가요?
3. **스냅샷+실시간**의 순서 규칙을 어디까지 엄격히 보장해야 하나요? 지연·역전 상황에서의 합성 규칙을 테스트로 캡처하고 있나요?
4. **레이트 리밋 공유**가 프로세스 단일성에 의존하나요? 멀티프로세스/멀티인스턴스로 확장되면 어떤 합의(IPC/Redis/파일락)를 쓰실 계획인가요?
5. 재연결 시 **중복 이벤트 제거**를 어떤 키로 보장하나요? (epoch, seq, monotonic ts, 또는 해시)

---

## 🧭 “다이캡 생성” (Dialogue Capsule 메뉴)

아래 4개 중 필요한 번호(들)를 **쉼표로** 입력하세요.

1. **백프레셔 & 팬아웃**: 드롭/코얼레스 규칙, 큐 파라미터 권장치(English term map 포함).
2. **PyQt5 브리징**: qasync vs 스레드+시그널 비교, 샘플 템플릿.
3. **재연결·멱등 설계**: epoch/seq 설계안과 테스트 시나리오.
4. **전역 레이트 리밋**: REST·WS 통합 토큰 버킷 구현 가이드.

“필요한 번호(들)를 , 로 입력하세요.”

---

## 🔧 Closing

### Improved Prompt

```markdown
역할: 업비트 자동거래 GUI의 WebSocket v6 아키텍트(Architect)
목표: 전역 단일 관리자 + 안전한 GUI 브릿지 + 재연결 멱등 + 백프레셔 완비

요구사항:
1) Subsystem별 프록시 인터페이스 유지, 콜백은 Typed Event로 엄격화
2) qasync 또는 시그널/슬롯으로 UI 스레드 접근 100% 강제
3) 재연결 시 epoch/seq로 중복 제거, 스냅샷+실시간 합성 규칙 문서화
4) REST·WS 전역 토큰 버킷 적용, 429/지수백오프 시험 통과
5) Fan-out에 consumer별 bounded-queue, drop_oldest + coalesce-by-symbol
6) 명시적 shutdown() 경로, WeakRef는 보조
7) chaos 테스트(손실/역전/지연), 지표(lag_ms, drops/min, queue_depth) 수집
산출물:
- 코드: GlobalWebSocketManager, FanoutHub, RateLimiter, TypedEvents
- 문서: Capability Matrix, Recovery & Ordering Rules, GUI Bridging Guide
- 테스트: 부하/장애/카오스/GUI-Responsiveness
```

### Model Recommendation

* **GPT-5 Thinking**: 아키텍처 리뷰/리팩터링 설계(긴 문맥, 추론).
* **o4-mini-high**: 반복 코드 생성/리팩토링(저지연).
* **Claude Code**: 긴 파일 단위 코드 리팩토링/주석화 병행 시 보조.

---

**CSL:** 🟢 L1 (≈6.0 %) → ACTION: 백프레셔·GUI 브릿지부터 구현 및 카오스 테스트 설계

---

**참고한 기획 문서**: 설계 원칙·아키텍처/컴포넌트·모니터링·장애 복구/확장성 및 API 사용 가이드 전반. &#x20;
