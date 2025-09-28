# 🚨 QAsync 이벤트 루프 충돌 위기: 종합 진단 보고서

**발견일**: 2025년 9월 26일
**심각도**: CRITICAL
**범위**: 전체 시스템 아키텍처
**분류**: 근본적 설계 결함

---

## 📋 Executive Summary

업비트 자동매매 시스템에서 **다중 이벤트 루프 충돌로 인한 Infrastructure Layer 마비** 현상이 확인되었습니다. 이는 단순한 버그가 아닌 **전체 비동기 아키텍처의 근본적 설계 결함**으로 판단됩니다.

### 핵심 문제

- **이벤트 루프 분리**: PyQt6/QAsync와 asyncio.new_event_loop() 간의 충돌
- **Infrastructure 바인딩**: HTTP 세션, Rate Limiter Lock이 서로 다른 루프에 바인딩
- **아키텍처 불일치**: 이벤트 기반 시스템과 Infrastructure Layer 간의 호환성 문제

### 즉시 영향

- ✅ **호가창 서비스**: QAsync 환경에서 정상 동작 (DDD Infrastructure 준수)
- ❌ **코인리스트 위젯**: 격리 루프에서 Infrastructure 충돌로 완전 마비
- ❌ **로깅 UI 시스템**: 독립 루프 생성으로 시스템 불안정
- ❌ **API 키 테스트**: 스레드 기반 격리 루프로 인한 연결 실패

---

## 🔍 기술적 조사 결과

### 1. 현재 시스템 상태 분석 (Pylance MCP 기반)

**Python 환경 상태**:

- 현재 환경: `.venv\Scripts\python.exe` (Python 3.13)
- 핵심 의존성: `qasync`, `PyQt6`, `aiohttp`, `asyncio` 모두 설치 확인

**Import 분석 결과**:

- ✅ `qasync`, `PyQt6`, `aiohttp` 정상 import 가능
- ✅ Infrastructure Layer 모듈들 정상 로드
- ⚠️ 일부 모듈에서 `typer`, `httpx` 등 누락 발견

### 2. 이벤트 루프 충돌 패턴 식별

**발견된 문제 패턴들**:

#### Critical Issues (20개 발견)

```python
# 패턴 1: 격리 루프 생성 + 스레드 실행
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(coroutine)
asyncio.set_event_loop(None)  # 정리 시도하나 충돌 유발

# 패턴 2: 동기/비동기 혼합
loop = asyncio.get_event_loop()
if loop.is_running():
    loop.create_task(coro)  # 문제 없음
else:
    loop.run_until_complete(coro)  # QAsync와 충돌!

# 패턴 3: asyncio.run 직접 호출
asyncio.run(coroutine)  # QAsync 환경에서 금지!
```

#### 주요 발생 지점

1. **UI 위젯**: `coin_list_widget.py` (라인 232, 424)
2. **로깅 시스템**: `event_driven_log_viewer_widget.py` (라인 202)
3. **API 서비스**: `api_key_service.py` (라인 326)
4. **이벤트 퍼블리셔**: `domain_event_publisher_impl.py` (라인 21)
5. **전략 관리 탭**: `trigger_builder_tab.py` (라인 137)

### 3. Infrastructure Layer 바인딩 분석

**공유 리소스 충돌 확인**:

```python
# UpbitPublicClient.py
self._session: Optional[aiohttp.ClientSession] = None
# → ClientSession이 특정 이벤트 루프에 바인딩됨

# Rate Limiter
self._locks: Dict[str, asyncio.Lock] = {}
# → asyncio.Lock도 루프 종속적
```

**문제 시나리오**:

1. QAsync 루프에서 UpbitPublicClient 초기화 → 세션이 QAsync 루프에 바인딩
2. 코인리스트에서 `new_event_loop()` 생성 → 새로운 루프에서 같은 클라이언트 호출
3. `<asyncio.locks.Lock object> is bound to a different event loop` 오류 발생
4. 전체 Infrastructure Layer 마비

### 4. 태스크 관리 상태 분석

**asyncio.create_task 사용 현황** (30+ 지점 발견):

- ✅ **정상 사용**: QAsync 환경에서 태스크 생성 (OrderbookPresenter 등)
- ❌ **위험 사용**: 태스크 참조 미보관으로 가비지 컬렉션 위험
- ❌ **취소 로직 부재**: 앱 종료 시 태스크 정리 메커니즘 없음

**예상 부작용**:

- 메모리 누수 가능성
- 백그라운드 태스크 무한 실행
- 앱 종료 시 강제 종료 필요

---

## 🎯 근본 원인 분석

### 1. 아키텍처 설계 철학의 충돌

**이벤트 기반 시스템 vs Infrastructure Layer**:

- **이벤트 기반**: 느슨한 결합, 유연한 컴포넌트 협업
- **Infrastructure Layer**: 공유 리소스 기반 효율성, 싱글톤 패턴
- **충돌 지점**: Infrastructure의 공유 리소스가 이벤트 루프에 바인딩됨

### 2. 개발 패턴의 일관성 부족

**패턴 혼재 문제**:

- **QAsync 패턴**: 호가창 위젯 (정상 동작)
- **격리 루프 패턴**: 코인리스트 위젯 (충돌 발생)
- **혼합 패턴**: 로깅 UI, 전략 관리 (불안정)

### 3. PyQt6와 asyncio 통합의 복잡성

**기술적 제약사항**:

- PyQt6의 이벤트 루프와 asyncio의 이벤트 루프는 본질적으로 다름
- QAsync는 이를 통합하지만 완벽하지 않음
- 개발자의 패턴 이해 부족으로 우회 시도

---

## 📊 영향도 평가

### 즉시 영향 (High Severity)

| 컴포넌트 | 상태 | 영향 | 우선순위 |
|---------|------|------|---------|
| 코인리스트 위젯 | 완전 마비 | 차트 뷰 핵심 기능 불가 | Critical |
| 로깅 UI 시스템 | 불안정 | 시스템 모니터링 불가 | High |
| API 키 검증 | 간헐적 실패 | 설정 저장 불가 | High |
| 전략 관리 탭 | 부분 기능 장애 | 전략 생성 제약 | Medium |

### 연쇄 영향 (Medium Severity)

- **전체 REST API 호출**: Infrastructure Layer 마비 시 전면 불가
- **WebSocket 연결**: 재연결 시 루프 충돌 가능성
- **백그라운드 태스크**: 예측 불가능한 중단 및 누수

### 장기 위험 (Long-term Risk)

- **새 기능 개발 지연**: 패턴 선택 혼란으로 개발 속도 저하
- **기술 부채 누적**: 임시 해결책으로 아키텍처 복잡도 증가
- **시스템 안정성 저하**: 예측 불가능한 충돌로 사용자 경험 악화

---

## 🛠️ 해결 방향 제안

### 권장 솔루션: 통합 QAsync 아키텍처 전환

**전략적 선택 근거**:

1. **아키텍처 일관성**: 단일 이벤트 루프로 모든 비동기 작업 통합
2. **Infrastructure 안정성**: 공유 리소스의 루프 바인딩 문제 해결
3. **개발 생산성**: 명확한 패턴으로 개발자 혼란 제거
4. **장기 유지보수성**: 표준화된 접근 방식으로 기술 부채 최소화

**핵심 변경사항**:

#### 1. 진입점 통합

```python
# Before (문제 패턴)
app = QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)
return loop.run_until_complete(run_application_async(app))

# After (권장 패턴)
import qasync

app = qasync.QApplication(sys.argv)
loop = qasync.QEventLoop(app)
asyncio.set_event_loop(loop)

with loop:
    return loop.run_until_complete(run_application_async(app))
```

#### 2. 위젯 비동기 패턴 표준화

```python
# Before (격리 루프)
def _load_real_data(self):
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    result = new_loop.run_until_complete(self.service.get_data())

# After (QAsync 통합)
@qasync.asyncSlot()
async def _load_real_data(self):
    result = await self.service.get_data()
    self._update_ui(result)
```

#### 3. Infrastructure Layer 루프 인식

```python
# Before (루프 바인딩 문제)
class UpbitPublicClient:
    def __init__(self):
        self._session = aiohttp.ClientSession()

# After (루프 인식 패턴)
class UpbitPublicClient:
    def __init__(self, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._session = None

    async def _ensure_session(self):
        if not self._session:
            self._session = aiohttp.ClientSession(loop=self._loop)
```

#### 4. 태스크 생명주기 관리

```python
# After (태스크 매니저 패턴)
class TaskManager:
    def __init__(self):
        self._tasks: Set[asyncio.Task] = set()

    def create_task(self, coro):
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def cleanup(self):
        for task in self._tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
```

#### 5. LoopGuard 런타임 안전장치

```python
# infrastructure/runtime/loop_guard.py
class LoopGuard:
    def __init__(self):
        self._main = None

    def ensure_main(self, *, where: str):
        cur = asyncio.get_running_loop()
        if self._main is None:
            self._main = cur
        elif self._main is not cur:
            raise RuntimeError(f"EventLoop breach at {where}")
```

**적용 지점**: Infrastructure 각 컴포넌트의 핵심 메서드 진입부

#### 6. AppKernel 중앙집중식 관리

```python
# runtime/app_kernel.py
class AppKernel:
    def __init__(self):
        self.loop_guard = LoopGuard()
        self.task_manager = TaskManager()
        self.event_bus = None
        self.http_clients = {}

    @classmethod
    def bootstrap(cls, app):
        # 단일 진입점에서 모든 런타임 리소스 초기화
        return cls()
```

**효과**: 런타임 소유권 명료화 + 수명주기 가시성 확보

### 대안 솔루션 비교 분석

| 전략 | 초기 변경 | 장기 안정성 | 구조적 안전장치 | **추천도** |
|------|------------|------------|----------------|----------|
| **A(단일 루프)** | 크다 | 최고 | 강력 (LoopGuard/AppKernel) | **⭐⭐⭐** |
| B(루프별 격리) | 작다 | 낮다 | 없음 (리소스 중복) | ⭐ |
| C(하이브리드) | 중간 | 중간 | 약함 (패턴 혼재) | ⭐⭐ |

#### 전략 A의 결정적 우위

1. **회귀 방지**: 다른 전략들은 같은 문제가 재발할 가능성이 높음
2. **운영 복잡도**: 단일 루프만 모니터링하면 되어 운영 용이
3. **개발 생산성**: 표준 패턴 통일로 신규 기능 개발 속도 향상
4. **기술 부채 감소**: 임시 방편을 따를 필요 없어 전체적 코드 품질 개선

---

## 📈 마이그레이션 로드맵

### Phase 1: 응급 복구 (1-2일)

1. **코인리스트 위젯 임시 수정**
   - 격리 루프 제거
   - QAsync 패턴 적용
   - 기본 기능 복구

2. **Infrastructure Layer 보호**
   - 루프 충돌 감지 및 에러 핸들링 강화
   - 세션 재생성 로직 추가

### Phase 2: 핵심 컴포넌트 전환 (1주)

1. **UI 위젯 표준화**
   - 로깅 UI 시스템 QAsync 전환
   - 전략 관리 탭 비동기 패턴 수정
   - API 키 서비스 통합 패턴 적용

2. **Infrastructure Layer 리팩터링**
   - 루프 인식 생성자 패턴 도입
   - 공유 리소스 관리 개선

### Phase 3: 전체 시스템 통합 (2주)

1. **아키텍처 표준화**
   - 전체 코드베이스 QAsync 패턴 적용
   - 태스크 생명주기 관리 시스템 구축
   - 종합 테스트 및 검증

2. **개발 가이드라인 수립**
   - 코드 리뷰 체크리스트 작성
   - 개발자 교육 및 문서화

---

## 🎯 성공 지표

### 기술적 지표

- [ ] 이벤트 루프 충돌 제로화
- [ ] API 호출 성공률 99.9% 이상 복구
- [ ] 메모리 사용량 20% 이하 증가 유지
- [ ] 시스템 응답 시간 기존 대비 10% 이내

### 품질 지표

- [ ] 코드 리뷰 시 아키텍처 이슈 90% 감소
- [ ] 새 컴포넌트 개발 시 패턴 일관성 100%
- [ ] 단위 테스트 커버리지 90% 이상 유지
- [ ] 시스템 안정성 지표 99% 이상

### 개발 지표

- [ ] 새 기능 개발 속도 20% 향상
- [ ] 버그 재발률 50% 감소
- [ ] 기술 부채 지표 개선

---

## ⚠️ 위험 요소 및 대응 방안

### 높은 위험 (High Risk)

| 위험 요소 | 확률 | 영향 | 대응 방안 |
|----------|------|------|----------|
| 전체 시스템 불안정화 | 중간 | 높음 | **Step 0 가드레일 선배치**, 단계별 롤백 계획 |
| 새로운 버그 도입 | 중간 | 중간 | **LoopGuard 예외 강제**, CI 정적 검사 |
| **회귀 문제** (신규) | 높음 | 높음 | **아키텍처 불변식 강제**, pre-commit hook |

### 중간 위험 + 구조적 대응

| 위험 요소 | 기존 대응 | **강화된 대응** |
|----------|------------|---------------|
| 개발 일정 지연 | 핵심 기능 우선 | **AppKernel 도입으로 목표 명료화** |
| 팀 학습 곡선 | 내부 교육 | **금지/허용 API 표 제공** |
| 성능 회귀 | 벤치마크 테스트 | **TaskManager로 자원 누수 방지** |

### 중간 위험 (Medium Risk)

- **팀 학습 곡선**: 내부 교육, 페어 프로그래밍으로 대응
- **성능 회귀**: 벤치마크 테스트, 모니터링 강화
- **의존성 충돌**: 점진적 업데이트, 테스트 환경 분리

---

## 🏁 결론 및 권고사항

### 핵심 메시지

이 문제는 **단순한 버그가 아닌 아키텍처 레벨의 근본적 설계 결함**입니다. 이벤트 기반 시스템 자체는 우수하나, **PyQt6 환경에서 asyncio와의 통합 방식**에 대한 명확한 표준이 시급합니다.

### 즉시 조치 사항 (24시간 내)

1. **코인리스트 위젯 응급 수정** - 격리 루프 제거, QAsync 패턴 임시 적용
2. **Infrastructure Layer 안정화** - 루프 충돌 감지 및 복구 로직 강화
3. **모니터링 강화** - 이벤트 루프 상태 추적, 알림 시스템 구축

### 전략적 결정 (1주 내)

1. **QAsync 통합 아키텍처 채택** - 전체 시스템의 표준 패턴으로 확정
2. **아키텍처 불변식 승인** - 6가지 핵심 규칙을 후발 개발의 절대 원칙으로 확정
3. **구조적 안전장치 도입** - LoopGuard + AppKernel + CI 검사로 회귀 방지
4. **마이그레이션 계획 승인** - Step 0-4 로드맵 실행 결정 (가드레일 선배치)
5. **개발팀 교육 계획** - 금지/허용 API 표 + QAsync 패턴 역량 강화

### 장기 비전 (1개월 내)

**통합 QAsync 아키텍처**로의 전환을 통해 시스템의 안정성과 개발 생산성을 동시에 확보하고, 향후 확장 가능한 아키텍처 기반을 마련할 것을 권장합니다.

---

## 📚 참고 자료

- [QAsync 공식 문서](https://github.com/CabbageDevelopment/qasync)
- [PyQt6 비동기 프로그래밍 가이드](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [asyncio 이벤트 루프 문서](https://docs.python.org/3/library/asyncio-eventloop.html)
- DDD Infrastructure Layer 패턴 가이드 (내부 문서)

---

**문서 작성**: GitHub Copilot
**검토일**: 2025년 9월 26일
**승인**: [대기 중]
**다음 리뷰**: 1주 후 진행 상황 점검

---

## ⚖️ 아키텍처 불변식 (Architecture Invariants)

> **목적**: 전략 A의 핵심 규칙을 **불변식으로 못 박아** 향후 어떤 기능개발도 이 원칙을 깨지 못하도록 합니다.

### 핵심 규칙

1. **EventLoop 단일성(Singleton Main Loop)**: 프로세스 내 `asyncio` 이벤트 루프는 **QAsync 통합 루프 1개만 존재**
2. **Loop 경계 금지**: `asyncio.new_event_loop()`, `asyncio.run()`, `loop.run_until_complete()` **전면 금지**
3. **UI-Async 브리지 표준**: Qt 신호→`@asyncSlot`→`await service(...)` **단일 경로만 허용**
4. **Loop-바운드 리소스 단일화**: `aiohttp.ClientSession`, `asyncio.Lock` 등 **모두 메인 루프에 바인딩**
5. **태스크 생명주기 관리 강제**: 모든 `create_task`는 **TaskManager**를 통해 등록·정리
6. **종료시 안전 정리**: 앱 종료 이벤트에서 **모든 태스크 취소→gather→세션/소켓 종료** 표준 시퀀스

### 강제 수단

- **CI/CD 검사**: 금지 패턴 정적 검사로 빌드 시 위반 차단
- **LoopGuard**: 런타임 루프 오염 조기 감지 및 예외 발생
- **AppKernel**: 단일 진입점으로 런타임 소유권 명료화
- **테스트 환경**: pytest fixture로 qasync 환경 강제

> **예상 효과**: 회귀 방지 + 개발자 혼란 제거 + 아키텍처 일관성 확보
