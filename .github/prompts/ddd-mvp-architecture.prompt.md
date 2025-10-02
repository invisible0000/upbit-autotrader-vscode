# 🏗️ DDD + MVP 아키텍처 구현

#file:../../.github/copilot-instructions.md

DDD + Clean Architecture + MVP 패턴을 준수하여 컴포넌트를 구현해 주세요.

## 아키텍처 원칙 적용

### 계층별 역할 분리
```
Presentation Layer (MVP)
├── Views (UI 컴포넌트)          → ui/desktop/screens/
├── Presenters (비즈니스 로직)    → presentation/presenters/
└── ViewModels (데이터 바인딩)   → presentation/view_models/

Application Layer
├── Use Cases (비즈니스 시나리오) → application/use_cases/
├── Services (응용 서비스)        → application/services/
└── Factories (컴포넌트 생성)     → application/factories/

Domain Layer (순수 비즈니스 로직)
├── Entities (도메인 엔티티)      → domain/entities/
├── Value Objects (값 객체)      → domain/value_objects/
└── Services (도메인 서비스)      → domain/services/

Infrastructure Layer
├── Repositories (데이터 접근)    → infrastructure/repositories/
├── External APIs (외부 연동)    → infrastructure/external_apis/
└── Logging (로깅 시스템)        → infrastructure/logging/
```

### 의존성 방향 규칙
- **Presentation → Application → Domain ← Infrastructure**
- **Domain Layer는 외부 의존성 없음** (순수 비즈니스 로직)
- **Infrastructure는 Domain 인터페이스 구현**

## MVP 패턴 구현

### Presenter 구현 원칙
```python
class [Component]Presenter:
    def __init__(self, view, service, logging_service):
        self.view = view
        self.service = service
        self.logger = logging_service.get_component_logger("[Component]Presenter")

    def handle_[action](self, data):
        try:
            # 1. 데이터 검증
            # 2. 비즈니스 로직 실행
            # 3. View 업데이트
            self.logger.info(f"[Component] {action} 완료")
        except Exception as e:
            self.logger.error(f"[Component] {action} 실패: {e}")
            raise  # Golden Rules: 에러 숨김 금지
```

### View 구현 원칙
```python
class [Component]View(QWidget):
    def __init__(self):
        super().__init__()
        self.presenter = None
        self.logger = None

    def set_presenter(self, presenter):
        self.presenter = presenter
        # MVP 연결 완료 로깅
```

## Factory 패턴 (ApplicationServiceContainer)

### 표준 Factory 구현
```python
class [Component]Factory(BaseComponentFactory):
    def create_component_instance(self, parent, **kwargs):
        # 1. ApplicationServiceContainer 접근
        app_container = self._get_application_container()

        # 2. 필요한 서비스들 안전하게 획득
        service = self._get_service(
            app_container.get_[service_type]_service,
            "[ServiceName]"
        )

        # 3. MVP 컴포넌트 조립
        view = [Component]View()
        presenter = [Component]Presenter(view, service, logging_service)
        view.set_presenter(presenter)

        self.logger.info("[Component] 컴포넌트 완전 조립 완료")
        return view
```

## Golden Rules 준수

### 필수 원칙들
1. **에러 숨김/폴백 금지**: try/except로 도메인 규칙 실패를 삼키지 말 것
2. **Fail Fast**: 문제 발생 시 즉시 명확한 에러 발생
3. **Infrastructure 로깅**: `create_component_logger("[ComponentName]")` 사용
4. **계층 위반 금지**: Domain에 외부 의존성 import 절대 금지

### 로깅 패턴
```python
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("[ComponentName]")
logger.info("✅ [Component] 초기화 완료")
logger.error("❌ [Component] 생성 실패: {error}")
```

## 사용 시나리오

다음과 같이 요청하시면 됩니다:

### 새 컴포넌트 생성
```
"[ComponentName]을 DDD + MVP 패턴으로 구현해 주세요.
- Factory: ApplicationServiceContainer 사용
- Presenter: presentation/presenters/ 위치
- View: ui/desktop/screens/ 위치
- Golden Rules 준수"
```

### 기존 컴포넌트 리팩터링
```
"[ComponentName]을 올바른 MVP 구조로 리팩터링해 주세요.
- 계층 위반 사항 수정
- Container 접근 방식 표준화
- Infrastructure 로깅 적용"
```

### 아키텍처 검증
```
"[ComponentName]의 DDD + MVP 아키텍처 준수 여부를 검증하고 개선해 주세요.
- 의존성 방향 확인
- 계층별 역할 분리 상태
- Golden Rules 위반 사항"
```

이 프롬프트를 사용하면 프로젝트 아키텍처 원칙을 완벽하게 준수하는 고품질 컴포넌트를 구현할 수 있습니다!
