# 📋 TASK_20250929_01: 올바른 Container 사용법 적용

## 🎯 태스크 목표

### 주요 목표

**Factory 패턴에서 ApplicationServiceContainer를 통한 올바른 계층별 접근 구현**

- Factory에서 ApplicationContainer 직접 접근을 ApplicationServiceContainer 경유로 변경
- DDD + Clean Architecture 계층별 접근 규칙 엄격 적용
- ApplicationContext 생명주기 관리 통합

### 완료 기준

- ✅ `settings_view_factory.py`에서 모든 Factory가 ApplicationServiceContainer 사용
- ✅ `get_global_container()` → `get_application_container()` 변경 완료
- ✅ 계층별 접근 규칙 100% 준수 (Presentation → Application → Infrastructure)
- ✅ ApplicationContext 생명주기 관리 통합 적용
- ✅ 최소 1개 Factory (API Settings)가 올바른 패턴으로 정상 동작

---

## 📊 현재 상황 분석

### 문제점

1. **잘못된 Container 접근**

   ```python
   # ❌ 현재 잘못된 패턴
   container = get_global_container()  # ApplicationContainer 직접 접근
   api_service = container.api_key_service()  # Infrastructure 직접 접근
   ```

2. **컨테이너 파일명 및 역할 혼동**
   - `container.py` (두 개 다른 파일에 동일한 파일명)
   - `ApplicationContainer` vs `ApplicationServiceContainer` 역할 구분 어려움
   - "Application"이라는 이름이 Infrastructure에 있는 모순

3. **계층 위반**
   - Presentation Layer (Factory)에서 Infrastructure Layer (ApplicationContainer) 직접 접근
   - Application Layer (ApplicationServiceContainer) 우회
   - DDD + Clean Architecture 원칙 위반

4. **생명주기 관리 누락**
   - ApplicationContext 없이 직접 Container 사용
   - 적절한 초기화 순서 및 Wiring 관리 부재

5. **MVP 폴더 구조 혼란**
   - Presenter가 `ui/desktop/screens/*/presenters/` 에 분산됨 (MVP 위반)
   - 올바른 위치는 `presentation/presenters/`
   - 찾기 어렵고 일관성 없는 구조

### 사용 가능한 리소스

#### 핵심 파일

- **Factory**: `upbit_auto_trading/application/factories/settings_view_factory.py`
- **ApplicationServiceContainer**: `upbit_auto_trading/application/container.py`
- **ApplicationContainer**: `upbit_auto_trading/infrastructure/dependency_injection/container.py`
- **ApplicationContext**: `upbit_auto_trading/infrastructure/dependency_injection/app_context.py`

#### 참고 문서

- **`CURRENT_ARCHITECTURE_ADVANTAGES.md`**: 현재 구조의 올바른 사용법
- **`INTEGRATED_ARCHITECTURE_GUIDE.md`**: DDD + MVP + Factory + DI 가이드

---

## 🔄 체계적 작업 절차 (8단계 필수 준수)

### Phase 1: 현재 상태 분석 및 백업

#### 1.1 현재 Factory 파일 분석

- [x] `settings_view_factory.py` 현재 Container 접근 패턴 파악
- [x] 각 ComponentFactory별 의존성 분석
- [x] 잘못된 접근 패턴 위치 식별

**📊 1.1 분석 완료 결과:**

**현재 Container 접근 패턴:**

- ✅ 모든 Factory가 이미 `get_application_container()` 사용 중 (12개 위치)
- ❌ `get_global_container()` 호출 없음 - 예상과 다름
- 📍 위치: 6개 ComponentFactory에서 각각 2줄씩 호출

**각 ComponentFactory별 의존성:**

1. `ApiSettingsComponentFactory`: api_key_service, logging_service 필요
2. `DatabaseSettingsComponentFactory`: database_service, logging_service 필요
3. `UiSettingsComponentFactory`: settings_service, logging_service 필요
4. `LoggingSettingsComponentFactory`: logging_service만 필요
5. `NotificationSettingsComponentFactory`: notification_service(옵션), logging_service 필요
6. `EnvironmentProfileComponentFactory`: profile_service(옵션), logging_service 필요

**🚨 실제 문제점 발견:**

- Factory들이 이미 올바른 `get_application_container()` 사용 중
- **문제는 ApplicationServiceContainer 메서드명 불일치 가능성**
- 예상: `container.get_database_service()` vs 실제: `container.database_service()`

**컨테이너 구조 확인:**

- `ApplicationServiceContainer` (application/container.py): Application Layer 서비스 조합
- `ApplicationContainer` (infrastructure/.../container.py): Infrastructure DI Provider (dependency-injector)

#### 1.2 백업 및 안전장치

- [x] `settings_view_factory.py` → `settings_view_factory_backup.py` 백업 생성
- [x] 현재 동작 상태 기준선 확인 (`python run_desktop_ui.py`)
- [x] 롤백 계획 수립

**📊 1.2 백업 및 안전장치 완료 결과:**

**백업 생성:**

- ✅ 백업 파일: `settings_view_factory_backup_20250929_214641.py` (33,904 bytes)
- 📅 생성 시간: 2025-09-29 오후 6:58:38
- 🔒 롤백 명령: `Copy-Item "settings_view_factory_backup_*.py" "settings_view_factory.py"`

**현재 동작 상태 기준선:**

- 🚨 **핵심 오류 확인**: `'ApplicationServiceContainer' object has no attribute 'get_database_service'`
- 🔍 **추가 오류들**:
  - LoggingSettingsWidget에 logging_service 미주입
  - NotificationSettingsWidget에 logging_service 미주입
  - API 키 관련 경고 (정상 - 설정 전 상태)

**롤백 계획:**

1. 문제 발생 시: `Copy-Item "settings_view_factory_backup_20250929_214641.py" "settings_view_factory.py"`
2. UI 프로세스 종료: `Get-Process python | Stop-Process`
3. 테스트 실행: `python run_desktop_ui.py`

**🎯 핵심 발견**: ApplicationServiceContainer에 `get_database_service()` 메서드가 없음 - 예상한 메서드명 불일치 문제 확실!

### Phase 2: ApplicationServiceContainer 접근 방식 구현

#### 2.1 올바른 접근 패턴 구현

- [x] `get_global_container()` → `get_application_container()` 변경 (이미 완료됨)
- [x] 각 ComponentFactory에서 ApplicationServiceContainer 메서드 사용 (누락 메서드 추가 완료)
- [x] 계층별 접근 규칙 적용 (DDD 준수 확인)

**📊 2.1 ApplicationServiceContainer 메서드 추가 완료 결과:**

**추가된 메서드들:**

- ✅ `get_database_service()` → Infrastructure의 `database_manager()` 래핑
- ✅ `get_settings_service()` → Infrastructure의 `settings_service()` 래핑
- ✅ TYPE_CHECKING import 추가로 타입 힌트 오류 해결

**백업 파일:**

- 🔒 `container_backup_20250929_215238.py` (11,029 bytes)

**테스트 결과:**

- 🎯 **핵심 성공**: `get_database_service()` 오류 해결됨!
- ⚠️ **남은 문제들**:
  - DatabaseSettingsView 생성 시 'NoneType' object 오류 (다른 원인)
  - LoggingSettingsWidget, NotificationSettingsWidget DI 문제 (위젯 레벨)
  - API 키 경고 (정상 - 미설정 상태)

**🎉 핵심 목표 달성**: ApplicationServiceContainer 메서드명 불일치 문제 완전 해결!

#### 2.2 Container 접근 표준화

- [x] BaseComponentFactory에 표준 Container 접근 메서드 추가
- [x] 모든 하위 ComponentFactory에서 표준 메서드 사용
- [x] 일관된 오류 처리 패턴 적용

**📊 2.2 Container 접근 표준화 완료 결과:**

**표준 메서드 구현:**

- ✅ `_get_service(service_getter, service_name)`: Golden Rules 준수 Fail Fast 패턴
- ✅ 에러 숨김/폴백 완전 제거 (`required=True/False` 구분 제거)
- ✅ getattr 패턴 제거 (불확실한 메서드 접근 차단)

**모든 ComponentFactory 표준화:**

- ✅ ApiSettingsComponentFactory: 표준 메서드 사용
- ✅ DatabaseSettingsComponentFactory: 표준 메서드 사용 + 정상 동작 확인
- ✅ UiSettingsComponentFactory: 표준 메서드 사용
- ✅ LoggingSettingsComponentFactory: 표준 메서드 사용 + 정상 동작 확인
- ✅ NotificationSettingsComponentFactory: 표준 메서드 사용 + 정상 동작 확인
- ✅ EnvironmentProfileComponentFactory: 표준 메서드 사용

**테스트 결과:**

- 🎯 **핵심 성공**: Container 접근 관련 오류 완전 해결
- 🎯 **MVP 조립**: 모든 Factory에서 "컴포넌트 완전 조립 완료" 확인
- 🎯 **Golden Rules 준수**: Fail Fast 원칙으로 에러 숨김 없이 명확한 실패
- 🎯 **일관성 확보**: 모든 Factory가 동일한 표준 패턴 사용

### Phase 3: ApplicationContext 생명주기 통합

#### 3.1 Context 관리 통합

- [x] ApplicationContext 초기화 확인
- [x] Factory 생성 시점에서 Context 상태 검증
- [x] 적절한 Wiring 및 Container 설정 확인

**📊 3.1 ApplicationContext 생명주기 통합 완료 결과:**

**ApplicationContext 초기화 확인:**

- ✅ `ApplicationContext.initialize()` 메서드 구현 완료
- ✅ `is_initialized` 속성으로 상태 추적
- ✅ 전역 Context 관리 (`get_application_context()`) 완료
- ✅ ApplicationServiceContainer와의 연결 로직 구현됨

**Factory에서 Context 상태 검증:**

- ✅ `BaseComponentFactory._ensure_application_context()` 메서드 구현 완료
- ✅ Context 미초기화 시 명확한 RuntimeError 발생 (Golden Rules 준수)
- ✅ `_get_application_container()` 메서드에 Context 검증 통합
- ✅ 모든 ComponentFactory가 자동으로 Context 검증 수행

**Wiring 및 Container 설정:**

- ✅ ApplicationContainer → ApplicationServiceContainer 어댑터 패턴 구현
- ✅ DI Container wiring 자동 설정 (`wire_container_modules()`)
- ✅ Container 등록 상태 검증 (`validate_container_registration()`)
- ✅ 전역 ApplicationServiceContainer 설정 완료

**테스트 결과:**

- 🎯 **UI 시스템 완전 동작**: `python run_desktop_ui.py` 정상 실행
- 🎯 **Context 검증 자동화**: 모든 Factory에서 Context 상태 자동 확인
- 🎯 **Golden Rules 준수**: 에러 숨김 없는 Fail Fast 패턴
- 🎯 **DDD + Clean Architecture**: 계층별 접근 규칙 100% 준수

#### 3.2 생명주기 이벤트 처리

- [x] Context 초기화 순서 준수
- [x] Factory 생성 전 Context 준비 상태 확인
- [x] 종료 시 안전한 리소스 해제

**📊 3.2 생명주기 이벤트 처리 완료 결과:**

**Context 초기화 순서:**

- ✅ `run_desktop_ui.py`에서 올바른 초기화 순서 구현
- ✅ AppKernel → ApplicationContext → MainWindow 순서
- ✅ Context 초기화 실패 시 안전한 폴백

**Factory 생성 전 Context 준비:**

- ✅ BaseComponentFactory에서 Context 상태 자동 검증
- ✅ Context 미준비 시 명확한 에러 메시지 및 중단
- ✅ ApplicationServiceContainer 준비 상태 확인

**안전한 리소스 해제:**

- ✅ ApplicationContext.shutdown() 메서드 구현
- ✅ Context Manager 패턴 지원 (`__enter__`, `__exit__`)
- ✅ `reset_application_context()` 전역 정리 기능

### Phase 4: MVP 구조 정리 (Option C - 단계적 접근)

#### 4.1 API Settings Presenter 이동 (완료)

- [x] `presentation/presenters/settings/` 폴더 생성
- [x] `ui/desktop/screens/settings/api_settings/presenters/api_settings_presenter.py` → `presentation/presenters/settings/` 이동
- [x] Factory에서 import 경로 수정
- [x] UI 폴더에서 presenters 폴더 제거

**📊 4.1 완료 결과:**

**MVP 구조 정리:**

- ✅ **올바른 위치**: `presentation/presenters/settings/api_settings_presenter.py` 생성 완료
- ✅ **Legacy 정리**: 원본 파일들을 `legacy/mvp_restructure_20250930/`로 이동
  - `api_settings_presenter_original.py`
  - `api_settings_presenter_backup.py`
  - `presenters_init_py_original.py`
- ✅ **폴더 구조 정리**: UI 폴더에서 불필요한 presenters 폴더 완전 제거

**Import 경로 수정:**

- ✅ **Factory 수정**: `settings_view_factory.py`에서 새 경로 사용
- ✅ **DI Container 수정**: `container.py`의 wiring 경로 업데이트
- ✅ **View 수정**: `api_settings_view.py`에서 절대 경로로 변경
- ✅ **Examples 수정**: `auto_generated_component_data.py` 경로 업데이트
- ✅ **Init 정리**: 순환 참조 방지를 위한 import 제거

**설정 화면 진입 성공:**

- 🎯 **구문 오류 해결**: `unexpected character after line continuation character` 완전 해결
- 🎯 **MVP 패턴 준수**: Presenter가 올바른 계층 위치로 이동
- 🎯 **UI 정상 동작**: 설정 화면 진입 및 탭 전환 가능
- 🎯 **DDD 준수**: Presentation → Application → Infrastructure 계층 규칙 준수

#### 4.2 개별 ComponentFactory 수정

- [x] ApiSettingsComponentFactory ApplicationServiceContainer 접근으로 변경
  - ✅ 표준 `_get_application_container()` 메서드 사용 중 (이미 올바름)
  - ✅ ApplicationContext 상태 검증 자동화 적용
  - ✅ Golden Rules 준수: Fail Fast 패턴으로 에러 숨김 없이 명확한 실패
- [x] `get_api_key_service()` 메서드 사용
  - ✅ `container.get_api_key_service()` 정상 호출 확인
  - ✅ `container.get_logging_service()` 정상 호출 확인
  - ✅ ApplicationServiceContainer 메서드 정상 접근
- [x] 이동된 Presenter와 MVP 패턴 조립 확인
  - ✅ `from presentation.presenters.settings.api_settings_presenter` 정상 import
  - ✅ View ↔ Presenter MVP 패턴 완전 연결
  - ✅ UI 테스트 통과: API 키 탭 정상 접근 및 표시

#### 4.3 나머지 ComponentFactory 수정 준비

- [x] DatabaseSettingsComponentFactory 분석
  - ✅ 표준 ApplicationServiceContainer 접근 패턴 사용 중 (이미 올바름)
  - ✅ `container.get_database_service()`, `container.get_logging_service()` 정상 호출
  - ✅ MVP 패턴 완전 조립: Database 설정 컴포넌트 완전 조립 완료
  - ✅ UI 테스트 통과: 데이터베이스 탭 정상 접근 및 3-DB 상태 표시
- [x] UiSettingsComponentFactory 분석
  - ✅ 표준 ApplicationServiceContainer 접근 패턴 사용 중 (이미 올바름)
  - ✅ `container.get_settings_service()`, `container.get_logging_service()` 정상 호출
  - ✅ MVP 패턴 완전 조립: UI 설정 컴포넌트 완전 조립 완료
  - ✅ UI 테스트 통과: UI 설정 탭 정상 접근 및 테마/창 설정 표시
- [x] 공통 패턴 식별 및 템플릿화
  - ✅ 모든 ComponentFactory가 동일한 표준 패턴 사용 확인
  - ✅ Container 접근 → 서비스 로드 → View 생성 → Presenter 생성 → MVP 연결 → 초기화 템플릿 완료
  - ✅ LoggingSettingsComponentFactory, NotificationSettingsComponentFactory도 동일 패턴 확인
  - ✅ Golden Rules 준수: 모든 Factory에서 Fail Fast 패턴과 에러 숨김 없는 명확한 실패 처리

### Phase 5: 테스트 및 검증

#### 5.1 개별 Factory 테스트

- [x] API Settings Factory 단독 테스트
  - ✅ ApiSettingsComponentFactory 정상 동작: 생성자 주입 서비스 사용
  - ✅ Container 접근: `_get_application_container()` 표준 메서드 동작
  - ✅ 서비스 로드: `get_api_key_service()`, `get_logging_service()` 정상 호출
- [x] 올바른 서비스 주입 확인
  - ✅ ApiKeyService 의존성 주입 성공: "ApiKeyService 의존성 주입 성공"
  - ✅ ApplicationLoggingService 정상 주입: 컴포넌트별 로거 생성 확인
  - ✅ ComponentLifecycleService 정상 동작: 컴포넌트 등록 완료
- [x] MVP 연결 상태 검증
  - ✅ View 생성: ApiSettingsView 초기화 완료
  - ✅ Presenter 생성: ApiSettingsPresenter 초기화 완료
  - ✅ MVP 패턴 조립: "API 설정 컴포넌트 완전 조립 완료 (MVP + 초기화)"
  - ✅ UI 표시: API 키 탭 정상 접근 및 화면 렌더링

#### 5.2 통합 테스트

- [x] `python run_desktop_ui.py` 실행
  - ✅ UI 시스템 정상 시작: MainWindow, NavigationBar, StatusBar 완전 초기화
  - ✅ ApplicationContext 정상 초기화: DI 시스템 완전 가동
  - ✅ WebSocket 시스템 정상 동작: Public 연결 성공, Rate Limiter 정상
- [x] 설정 화면 접근 테스트
  - ✅ 설정 화면 지연 로딩: ScreenManagerService를 통한 MVP Container 생성
  - ✅ 탭 전환 정상: API 키 탭 lazy loading 및 Factory 자동 생성
  - ✅ 모든 하위 컴포넌트 정상: UI 설정, API 설정, Database 설정 완전 조립
- [x] 오류 메시지 확인 및 해결
  - ✅ Container 접근 오류 해결: ApplicationServiceContainer 메서드명 불일치 문제 완전 해결
  - ✅ MVP 패턴 조립 성공: Presenter 위치 이동 및 import 경로 정상화 완료
  - ✅ DDD 계층 준수 확인: Domain 순수성 유지, Infrastructure 로깅 사용
  - ⚠️ 남은 경고: API 키 미설정 (정상 - 초기 상태), 암호화 키 없음 (정상 - 설정 전)

---

## 🛠️ 구체적 구현 계획

### 올바른 Container 접근 패턴

#### Before (현재 잘못된 방식)

```python
class ApiSettingsComponentFactory(BaseComponentFactory):
    def create_component_instance(self, parent, **kwargs):
        # ❌ Infrastructure 직접 접근
        container = get_global_container()
        api_key_service = container.api_key_service()
        logging_service = container.application_logging_service()
```

#### After (올바른 방식)

```python
class ApiSettingsComponentFactory(BaseComponentFactory):
    def create_component_instance(self, parent, **kwargs):
        # ✅ Application Layer 경유 접근
        app_container = get_application_container()
        if app_container is None:
            raise RuntimeError("ApplicationServiceContainer not initialized")

        api_key_service = app_container.get_api_key_service()
        logging_service = app_container.get_logging_service()
```

### 컨테이너 역할 명확화 (단계적 접근)

#### 현재 컨테이너들의 실제 역할

```python
# 🚀 Infrastructure DI Container (container.py 내 ApplicationContainer)
# 역할: DB, API, 외부 리소스 접근 제공
# 위치: infrastructure/dependency_injection/container.py
class ApplicationContainer:  # 이름 혼동 요소!
    def api_key_service(self) -> Singleton[ApiKeyService]
    def database_service(self) -> Singleton[DatabaseService]

# 🎯 Application Service Container (container.py 내 ApplicationServiceContainer)
# 역할: 비즈니스 서비스 조합 및 제공
# 위치: application/container.py
class ApplicationServiceContainer:
    def get_api_key_service(self) -> ApiKeyService
    def get_logging_service(self) -> LoggingService

# 🔧 Context Manager (app_context.py 내 ApplicationContext)
# 역할: 생명주기 및 Context 관리
# 위치: infrastructure/dependency_injection/app_context.py
class ApplicationContext:
    def initialize(self)
    def get_infrastructure_container(self)
```

#### 1단계: 주석으로 역할 명확화 (지금 진행)

```python
# Infrastructure DI Provider - 단순 외부 의존성 제공
class ApplicationContainer:  # TODO: InfrastructureDIContainer로 이름 변경 고려
    """Infrastructure Layer DI Container
    역할: 데이터베이스, API, 외부 리소스 접근 제공
    주의: Presentation Layer에서 직접 접근 금지!
    """

# Application Service Orchestrator - 비즈니스 서비스 조합
class ApplicationServiceContainer:
    """Application Layer Service Container
    역할: 비즈니스 로직을 위한 서비스 조합 및 제공
    사용: Factory, Presenter에서 이 컨테이너를 통해 서비스 접근
    """
```

### ApplicationContext 통합

#### Context 상태 검증

```python
def _ensure_application_context(self):
    """ApplicationContext 초기화 상태 확인"""
    from upbit_auto_trading.infrastructure.dependency_injection.app_context import get_application_context

    context = get_application_context()
    if not context or not context.is_initialized:
        raise RuntimeError("ApplicationContext not properly initialized")
    return context
```

#### 표준 Container 접근 메서드

```python
def _get_application_container(self):
    """표준 ApplicationServiceContainer 접근"""
    self._ensure_application_context()

    from upbit_auto_trading.application.container import get_application_container
    app_container = get_application_container()

    if app_container is None:
        raise RuntimeError("ApplicationServiceContainer not available")
    return app_container
```

---

## 🎯 성공 기준

### 기술적 검증

- ✅ **계층 준수**: Factory → ApplicationServiceContainer → ApplicationContainer
- ✅ **서비스 접근**: `app_container.get_xxx_service()` 패턴 사용
- ✅ **Context 관리**: ApplicationContext 초기화 상태 확인
- ✅ **MVP 조립**: View-Presenter 정상 연결

### 동작 검증

- ✅ **API Settings**: Factory로 생성된 API 설정 탭 정상 동작
- ✅ **오류 없음**: RuntimeError, AttributeError 등 해결
- ✅ **UI 반응**: 설정 화면 접근 시 정상 로드
- ✅ **데이터 흐름**: 서비스 → Presenter → View 정상 흐름

### 아키텍처 품질

- ✅ **DDD 준수**: Domain 순수성 유지
- ✅ **Clean Architecture**: 의존성 방향 준수
- ✅ **SOLID 원칙**: 각 Container의 단일 책임 유지
- ✅ **일관성**: 모든 Factory가 동일한 패턴 사용
- ✅ **MVP 분리**: Presenter가 올바른 위치에 위치 (`presentation/presenters/`)

---

## 💡 작업 시 주의사항

### 안전성 원칙

#### 백업 및 롤백

- **필수 백업**: `settings_view_factory.py` 수정 전 백업
- **점진적 적용**: 한 번에 하나의 ComponentFactory씩 수정
- **즉시 테스트**: 각 수정 후 동작 확인
- **롤백 준비**: 문제 발생 시 즉시 이전 상태 복원

#### 오류 방지

- **Null 체크**: Container 및 Service가 None인지 확인
- **예외 처리**: RuntimeError로 명확한 실패 신호
- **상태 검증**: ApplicationContext 초기화 상태 확인
- **로깅 활용**: 각 단계별 로그 메시지 추가

### 코드 품질

#### 일관성 유지

- **표준 패턴**: 모든 Factory에서 동일한 Container 접근 방식
- **네이밍 규칙**: `get_xxx_service()` 메소드명 일관성
- **오류 메시지**: 명확하고 일관된 에러 메시지
- **주석 추가**: 왜 이렇게 변경했는지 설명
- **컨테이너 역할 명확화**: 각 컨테이너의 역할을 주석으로 명시

#### 성능 고려

- **Lazy Loading**: 필요할 때만 Container 접근
- **캐싱**: ApplicationServiceContainer 인스턴스 재사용
- **메모리**: 불필요한 객체 생성 방지
- **초기화**: Context 중복 초기화 방지

---

## 🚀 즉시 시작할 작업

### 1단계: 현재 상태 분석

```powershell
# 현재 Factory 파일에서 Container 접근 패턴 확인
Get-Content upbit_auto_trading\application\factories\settings_view_factory.py | Select-String "get_global_container\|get_application_container" -n
```

### 2단계: 백업 생성

```powershell
# 안전한 백업 생성
Copy-Item "upbit_auto_trading\application\factories\settings_view_factory.py" "upbit_auto_trading\application\factories\settings_view_factory_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').py"
```

### 3단계: ApplicationServiceContainer 메서드 확인

```powershell
# ApplicationServiceContainer에서 사용 가능한 메서드 확인
Get-Content upbit_auto_trading\application\container.py | Select-String "def get_" -A 2
```

### 4단계: MVP 구조 정리 (Option C)

```powershell
# API Settings Presenter 이동
New-Item -ItemType Directory -Path "presentation\presenters\settings" -Force
Move-Item "ui\desktop\screens\settings\api_settings\presenters\api_settings_presenter.py" "presentation\presenters\settings\"
```

### 5단계: Factory 수정

- `ApiSettingsComponentFactory.create_component_instance()` 메서드 수정
- `get_global_container()` → `get_application_container()` 변경
- Presenter import 경로 수정: `from presentation.presenters.settings.api_settings_presenter import ApiSettingsPresenter`
- `container.api_key_service()` → `app_container.get_api_key_service()` 변경

---

## 🔗 연관 태스크

### 선행 태스크

- **TASK_0**: 전체 프로젝트 브리프 (완료)

### 후속 태스크

- **TASK_B**: API Settings Factory MVP 완성 (이 태스크 완료 후)
- **TASK_C**: Database Settings Factory 수정 (이 태스크 완료 후)
- **TASK_D**: 나머지 설정 Factory 수정 (TASK B, C 완료 후)
- **TASK_E**: 통합 테스트 및 성능 검증 (모든 태스크 완료 후)

### 종속성

- **없음**: 이 태스크는 모든 후속 태스크의 기반
- **영향**: 이 태스크의 성공 패턴이 다른 모든 Factory에 적용됨

### 미래 계획 (선택적)

- **컨테이너 파일명 변경**: Factory 작업 완료 후 고려
  - `ApplicationContainer` → `InfrastructureDIContainer`
  - `container.py` → `infrastructure_di_container.py`
  - `app_context.py` → `context_manager.py`
- **Import 구문 일괄 업데이트**: 필요시 진행

---

**다음 에이전트 시작점**:

1. `upbit_auto_trading/application/factories/settings_view_factory.py` 파일 열기
2. 현재 Container 접근 패턴 분석
3. ApiSettingsComponentFactory부터 올바른 패턴으로 수정 시작
4. 각 수정 후 `python run_desktop_ui.py`로 동작 확인

---

**문서 유형**: 핵심 기반 태스크
**우선순위**: 🔥 최우선 (모든 태스크의 기반)
**예상 소요 시간**: 2-3시간
**성공 기준**: API Settings Factory 올바른 패턴으로 정상 동작
