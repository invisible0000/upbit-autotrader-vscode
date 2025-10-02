# 📚 초기화 시퀀스 리팩터링 - 의도 파악 요약

> **작성 배경**: 첨부된 대화 내용 분석 및 프로젝트 구조 검토
> **핵심 질문**: "프로그램 시작 시 어떤 순서로 초기화해야 하는가?"
> **최종 목표**: 기술 부채가 쌓이기 전 `run_desktop_ui.py`부터 체계적으로 정리

---

## 🎯 귀하의 의도 추론

### 명시된 의도
>
> "구현 초기인 지금 정리를 해야 기술 부채가 관리될 것"
> "`run_desktop_ui.py`부터 다듬어 나가는 작업을 하고 싶다"

### 숨겨진 의도 (대화 맥락 기반)

1. **아키텍처 원칙의 실제 적용 검증**
   - DDD 4계층, MVP 패턴, DI를 **개념으로만 알고 있는 것이 아니라 실제 코드에 제대로 적용**되었는지 확인하고 싶음
   - 특히 **서비스 초기화 순서**가 논리적으로 타당한지 검증 필요

2. **명시적 vs 암묵적 의존성 명확화**
   - "경로 서비스가 먼저냐, 설정 서비스가 먼저냐" 같은 질문의 본질:
   - **"의존성이 코드에 명확히 드러나는가?"**
   - 싱글톤 vs DI 논의의 본질: **"Mock 주입으로 테스트 가능한가?"**

3. **책임 소재의 명확화**
   - "DB 파일 생성은 누구 책임인가?" 같은 질문:
   - **각 컴포넌트의 책임 경계를 명확히** 하고 싶음
   - SRP(Single Responsibility Principle) 위반 사례 찾기

4. **미래 확장성 확보**
   - 지금 정리하지 않으면:
     - 새 서비스 추가 시 어디에 넣어야 할지 모호
     - 초기화 순서 꼬임 → 런타임 에러 급증
     - 테스트 작성 불가능 → 리팩터링 공포

---

## 🔍 대화 내용에서 포착한 핵심 논점

### 논점 1: 초기화 순서의 논리적 정당성

**대화 핵심**:

```
Q: "프로그램 시작 시 첫 번째 서비스는?"
A: "경로 서비스 (PathService)"
이유: "설정 파일이 어디 있는지 알아야 읽을 수 있다"
```

**함의**:

- **물리적 리소스(파일/디렉터리)가 논리적 개념(설정/데이터)보다 선행**되어야 함
- 의존성 체인: `경로 확정` → `파일 위치 파악` → `파일 읽기` → `데이터 사용`
- 이 원칙이 현재 `run_desktop_ui.py`에 반영되어 있는가? → **검증 필요**

**현재 코드 검토 결과**:

```python
# run_desktop_ui.py (현재)
self.kernel = AppKernel.bootstrap(self.qapp, kernel_config)  # ❓ 여기서 경로 초기화?
self.di_manager = get_di_lifecycle_manager()  # ❓ 여기서 설정 로드?
```

→ **초기화 순서가 명시적이지 않음** (AppKernel 내부 로직에 숨겨짐)

---

### 논점 2: 책임 소재 (DB 파일 생성 예시)

**대화 핵심**:

```
Q: "DB 파일 생성은 파일시스템 서비스? DB 서비스?"
A: "DB 서비스의 책임"
역할 분리:
  - 파일시스템 서비스: "어디에(Where)?" - 경로 제공, 디렉터리 생성
  - DB 서비스: "무엇을? 어떻게(What/How)?" - 파일 생성, 스키마 초기화, 연결 관리
```

**함의**:

- **책임 경계가 명확해야 함**: 각 서비스가 "한 가지만 잘하기"
- **협력 구조 명확화**: PathService → 경로 제공 → DatabaseService → 파일 생성
- 현재 코드에서 이 경계가 잘 지켜지고 있는가? → **검증 필요**

**현재 코드 검토 필요 사항**:

- DatabaseConnection이 경로를 직접 하드코딩하고 있지 않은가?
- PathService를 주입받아 사용하는가?
- 디렉터리 생성 로직이 DatabaseService에 섞여있지 않은가?

---

### 논점 3: 싱글톤 패턴의 함정

**대화 핵심**:

```
Q: "DDD에서 qasync 사용 시 싱글톤 써야 하나?"
A: "전통적 싱글톤 ❌, DI 컨테이너의 Singleton Provider ✅"

이유:
  전통적 싱글톤:
    - 강한 결합 (구체 클래스에 직접 의존)
    - 테스트 불가 (Mock 주입 어려움)
    - 숨겨진 의존성 (생성자에 드러나지 않음)

  DI Singleton Provider:
    - 명시적 주입 (생성자 인자로)
    - 느슨한 결합 (인터페이스 의존)
    - 테스트 용이 (Mock 쉽게 주입)
```

**함의**:

- **"유일한 인스턴스"는 필요하지만, 방법이 중요함**
- DI 컨테이너가 생명주기 관리 → **제어의 역전(IoC) 달성**
- 현재 코드에 전통적 싱글톤 패턴이 남아있는가? → **찾아서 제거 필요**

**현재 코드 검토 필요 사항**:

```python
# 이런 패턴이 있는가?
class SomeService:
    _instance = None
    @classmethod
    def get_instance(cls): ...

# 또는
some_service = SomeService.get_instance()  # 전역에서 직접 호출
```

---

## 📐 현재 구조의 문제점 (추정)

### 문제 1: 초기화 책임 분산

```
현재:
  AppKernel: 일부 초기화 담당
  DILifecycleManager: 일부 초기화 담당
  run_desktop_ui.py: 일부 초기화 담당 (MainWindow 생성 등)

문제:
  - 어느 컴포넌트가 무엇을 초기화하는지 불명확
  - 순서 보장이 어려움
  - 새 서비스 추가 시 어디에 넣어야 할지 모호

이상적:
  ApplicationBootstrapper: 모든 초기화를 단계별로 중앙 관리
    Phase 1: PathService
    Phase 2: ConfigLoader
    Phase 3: LoggingService
    Phase 4: DI Container
    Phase 5-7: 계층별 서비스들
```

### 문제 2: 경로 서비스 최우선 보장 없음

```
현재:
  PathServiceFactory는 지연 초기화 (lazy)
  → 어느 컴포넌트가 먼저 호출하느냐에 따라 순서 변동 가능

문제:
  - 명시적인 "최우선 초기화" 보장 없음
  - 다른 서비스가 먼저 초기화되면 경로 불확실성

이상적:
  ApplicationBootstrapper.bootstrap() 시작 시:
    1. 가장 먼저 PathServiceFactory.get_service() 호출 (강제)
    2. 다른 모든 서비스는 이후에만 초기화
```

### 문제 3: MVP 패턴 수동 연결

```
현재:
  presenter = di_manager.get_main_window_presenter()
  main_window = MainWindow()
  main_window.presenter = presenter  # 수동
  presenter.set_view(main_window)    # 수동
  main_window.complete_initialization()

문제:
  - 수동 연결 로직 많음 (보일러플레이트)
  - 에러 처리 복잡
  - 연결 누락 가능성

이상적:
  @inject 데코레이터로 자동 주입:
    main_window = MainWindow()  # Presenter 자동 주입됨
    main_window.show()
```

---

## 🎯 리팩터링 최종 목표 (귀하의 의도 구현)

### 목표 1: "프로그램 흐름을 한눈에 파악 가능"

```python
# run_desktop_ui.py (리팩터링 후)

async def main_async():
    app = qasync.QApplication(sys.argv)

    # 🔍 명확한 단계별 초기화
    bootstrapper = ApplicationBootstrapper(app)

    if not await bootstrapper.bootstrap():
        logger.error("초기화 실패")
        return 1

    # 🔍 초기화 완료 후 메인 루프
    return await bootstrapper.run()
```

**달성 효과**:

- 신규 개발자가 5분 내에 초기화 흐름 파악 가능
- 에러 발생 시 어느 단계에서 실패했는지 즉시 알 수 있음

### 목표 2: "서비스 추가 시 어디에 넣을지 명확함"

```python
# ApplicationBootstrapper (리팩터링 후)

async def bootstrap(self):
    # Phase 1: 경로 (최우선)
    await self._init_path_service()

    # Phase 2: 설정 (경로 필요)
    await self._init_config_service()

    # Phase 3: 로깅 (경로 + 설정 필요)
    await self._init_logging_service()

    # Phase 4: DI 컨테이너 (모든 기반 준비됨)
    await self._init_di_container()

    # 🆕 새 서비스 추가 시: 의존성 보고 적절한 Phase에 배치
```

**달성 효과**:

- "이 서비스는 Phase 5에 들어가야겠구나" (명확한 판단 기준)
- 의존성 순환 불가능 (선형적 단계 구조)

### 목표 3: "테스트 가능한 구조"

```python
# tests/test_services.py (리팩터링 후)

def test_order_service_with_mock():
    # ✅ DI 덕분에 Mock 쉽게 주입 가능
    mock_repository = MockOrderRepository()
    mock_api = MockUpbitApi()

    order_service = OrderApplicationService(
        repository=mock_repository,
        api=mock_api
    )

    # 실제 API 호출 없이 로직 테스트
    result = order_service.place_order(...)
    assert result.success
```

**달성 효과**:

- 비즈니스 로직을 외부 의존성(DB, API) 없이 테스트
- CI/CD 파이프라인에서 빠른 테스트 실행

---

## 🚀 실행 로드맵 (우선순위 기반)

### Week 1: 기반 다지기

**Priority 1 (긴급)**:

- [ ] PathService 최우선 초기화 검증
- [ ] ApplicationBootstrapper 스켈레톤 생성
- [ ] Phase 1-3 (경로/설정/로깅) 구현

**Why**: 모든 다른 작업의 전제 조건

### Week 2: DI 시스템 정리

**Priority 2 (중요)**:

- [ ] 현재 DI 컨테이너들 역할 명확화
- [ ] UnifiedDIContainer 설계
- [ ] 점진적 마이그레이션

**Why**: 테스트 가능성과 확장성의 핵심

### Week 3: UI 레이어 자동화

**Priority 3 (일반)**:

- [ ] MVP 패턴 @inject 자동 주입
- [ ] 수동 연결 로직 제거
- [ ] run_desktop_ui.py 최종 정리

**Why**: 사용자 경험과 유지보수성 개선

---

## 📊 성공 지표

### 코드 레벨

- [ ] `run_desktop_ui.py` 라인 수 50% 감소 (보일러플레이트 제거)
- [ ] 초기화 단계가 명시적으로 7단계로 분리됨
- [ ] 전통적 싱글톤 패턴 0개 (모두 DI로 전환)

### 개발자 경험

- [ ] 신규 개발자가 초기화 흐름 파악 시간: 30분 이내
- [ ] 새 서비스 추가 시 배치 위치 판단: 5분 이내
- [ ] 에러 발생 시 원인 단계 파악: 즉시

### 품질

- [ ] 단위 테스트 커버리지: 70% 이상
- [ ] 통합 테스트 성공률: 100%
- [ ] 실제 실행 검증: `python run_desktop_ui.py` 정상 작동

---

## 💬 추가 논의 필요 사항

### 질문 1: AppKernel의 미래 역할

- AppKernel과 ApplicationBootstrapper의 관계는?
- AppKernel을 계속 사용할 것인가, 아니면 Bootstrapper로 대체?

### 질문 2: DILifecycleManager vs ExternalDependencyContainer

- 두 컴포넌트를 통합할 것인가, 역할 분리할 것인가?
- 통합 시 이름은 무엇으로? (UnifiedDIContainer?)

### 질문 3: 비동기 초기화의 필요성

- 모든 Phase를 async로 만들어야 하는가?
- 동기 초기화로 충분한 Phase는? (예: PathService)

---

## 📚 관련 문서

1. **상세 계획서**: `INITIALIZATION_SEQUENCE_REFACTORING_PLAN.md`
   - 전체 리팩터링 아키텍처 설계
   - Phase별 상세 구현 가이드

2. **퀵 스타트**: `INITIALIZATION_REFACTORING_QUICK_START.md`
   - 즉시 실행 가능한 액션 아이템
   - 단계별 체크리스트

3. **현재 아키텍처**: `docs/ARCHITECTURE_GUIDE.md`
   - DDD 4계층 구조
   - 트리거 시스템 설계

4. **DI 가이드**: `docs/DEPENDENCY_INJECTION_ARCHITECTURE.md`
   - 의존성 주입 패턴
   - Container 설계 원칙

---

## 🎓 결론: 귀하께서 원하시는 것

**핵심 한 문장**:
> "프로그램 시작부터 종료까지의 흐름이 명확하고, 각 컴포넌트의 책임이 뚜렷하며, 테스트 가능하고, 확장하기 쉬운 구조"

**구체적으로**:

1. ✅ `run_desktop_ui.py` 열면 **프로그램 전체 흐름이 한눈에 보임**
2. ✅ 새 서비스 추가 시 **어디에 넣을지 명확함** (의존성 기반 Phase 배치)
3. ✅ 각 서비스의 **책임 경계가 명확함** (SRP 준수)
4. ✅ **테스트 작성이 쉬움** (Mock 주입 자유롭게)
5. ✅ **에러 추적이 쉬움** (단계별 로깅, 명확한 실패 지점)

**지금 시작해야 하는 이유**:

- ✅ 구현 초기 단계 (변경 비용 낮음)
- ✅ 기술 부채가 쌓이기 전 (리팩터링 난이도 낮음)
- ✅ 팀 규모가 작을 때 (의사결정 빠름)

**기대 효과**:

- 🎯 6개월 후에도 코드를 이해하고 수정할 수 있음
- 🎯 신규 개발자 온보딩 시간 50% 단축
- 🎯 버그 발생률 감소 (명확한 구조 → 실수 감소)
- 🎯 자신감 있는 리팩터링 (테스트 커버리지 확보)

---

**다음 단계**: `INITIALIZATION_REFACTORING_QUICK_START.md`의 **Action 1**부터 시작하세요!
