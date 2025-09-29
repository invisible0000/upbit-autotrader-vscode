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

- [ ] `settings_view_factory.py` 현재 Container 접근 패턴 파악
- [ ] 각 ComponentFactory별 의존성 분석
- [ ] 잘못된 접근 패턴 위치 식별

#### 1.2 백업 및 안전장치

- [ ] `settings_view_factory.py` → `settings_view_factory_backup.py` 백업 생성
- [ ] 현재 동작 상태 기준선 확인 (`python run_desktop_ui.py`)
- [ ] 롤백 계획 수립

### Phase 2: ApplicationServiceContainer 접근 방식 구현

#### 2.1 올바른 접근 패턴 구현

- [ ] `get_global_container()` → `get_application_container()` 변경
- [ ] 각 ComponentFactory에서 ApplicationServiceContainer 메서드 사용
- [ ] 계층별 접근 규칙 적용

#### 2.2 Container 접근 표준화

- [ ] BaseComponentFactory에 표준 Container 접근 메서드 추가
- [ ] 모든 하위 ComponentFactory에서 표준 메서드 사용
- [ ] 일관된 오류 처리 패턴 적용

### Phase 3: ApplicationContext 생명주기 통합

#### 3.1 Context 관리 통합

- [ ] ApplicationContext 초기화 확인
- [ ] Factory 생성 시점에서 Context 상태 검증
- [ ] 적절한 Wiring 및 Container 설정 확인

#### 3.2 생명주기 이벤트 처리

- [ ] Context 초기화 순서 준수
- [ ] Factory 생성 전 Context 준비 상태 확인
- [ ] 종료 시 안전한 리소스 해제

### Phase 4: MVP 구조 정리 (Option C - 단계적 접근)

#### 4.1 API Settings Presenter 이동 (우선 진행)

- [ ] `presentation/presenters/settings/` 폴더 생성
- [ ] `ui/desktop/screens/settings/api_settings/presenters/api_settings_presenter.py` → `presentation/presenters/settings/` 이동
- [ ] Factory에서 import 경로 수정
- [ ] UI 폴더에서 presenters 폴더 제거

#### 4.2 개별 ComponentFactory 수정

- [ ] ApiSettingsComponentFactory ApplicationServiceContainer 접근으로 변경
- [ ] `get_api_key_service()` 메서드 사용
- [ ] 이동된 Presenter와 MVP 패턴 조립 확인

#### 4.3 나머지 ComponentFactory 수정 준비

- [ ] DatabaseSettingsComponentFactory 분석
- [ ] UiSettingsComponentFactory 분석
- [ ] 공통 패턴 식별 및 템플릿화

### Phase 5: 테스트 및 검증

#### 5.1 개별 Factory 테스트

- [ ] API Settings Factory 단독 테스트
- [ ] 올바른 서비스 주입 확인
- [ ] MVP 연결 상태 검증

#### 5.2 통합 테스트

- [ ] `python run_desktop_ui.py` 실행
- [ ] 설정 화면 접근 테스트
- [ ] 오류 메시지 확인 및 해결

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
