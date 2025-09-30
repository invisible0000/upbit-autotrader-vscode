# 📋 TASK_20251001_01: 컨테이너 파일명 혼동 문제 해결

## 🎯 태스크 목표

### 주요 목표

**현재 3-Container 구조의 파일명 혼동 문제 해결을 통한 명확성 향상**

- 동일한 "Application" 키워드가 다른 계층에서 중복 사용되는 문제 해결
- 각 컨테이너의 역할과 책임을 명확히 구분할 수 있는 네이밍 적용
- 기존 코드의 안정성을 유지하면서 점진적 개선 수행

### 완료 기준

- ✅ 3개 컨테이너의 역할이 파일명으로 명확히 구분됨
- ✅ Import 구문에서 어떤 Container를 사용하는지 즉시 파악 가능
- ✅ 모든 기존 코드가 정상 동작 (하위 호환성 보장)
- ✅ 새로운 네이밍 규칙 문서화 완료

---

## 📊 현재 상황 분석

### 🚨 발견된 문제점

#### 1. 파일명 혼동 문제

| 현재 파일 위치 | 클래스명 | 실제 역할 | 혼동 요소 |
|----------------|----------|-----------|-----------|
| `application/container.py` | `ApplicationServiceContainer` | Application Layer 서비스 조합 | "Application"이 중복 |
| `infrastructure/.../container.py` | `ApplicationContainer` | Infrastructure DI Provider | "Application"인데 Infrastructure에 있음 |
| `infrastructure/.../app_context.py` | `ApplicationContext` | Context 생명주기 관리 | 역할이 명확하지 않음 |

#### 2. 잘못된 사용 패턴 발견

```python
# ❌ 현재 발견된 잘못된 패턴 (application/container.py 내부)
from upbit_auto_trading.infrastructure.dependency_injection.container import get_global_container
infrastructure_container = get_global_container()  # Infrastructure 직접 접근
self._services["api_key_service"] = infrastructure_container.api_key_service()
```

#### 3. Import 혼동 사례

```python
# 🔍 현재 Import 상황 - 어떤 Container인지 구분 어려움
from upbit_auto_trading.application.container import ApplicationServiceContainer
from upbit_auto_trading.infrastructure.dependency_injection.container import ApplicationContainer

# 둘 다 "Application"이라는 이름을 포함하여 역할 구분 어려움
```

### 📊 현재 구조 분석

#### 컨테이너별 실제 역할

1. **ApplicationContainer** (Infrastructure Layer)
   - **실제 역할**: External Dependencies DI Provider
   - **책임**: DB, API 클라이언트, 로깅, 설정 등 Infrastructure 서비스
   - **문제점**: "Application"이라는 이름이지만 Infrastructure에 위치

2. **ApplicationServiceContainer** (Application Layer)
   - **실제 역할**: Business Logic Service Orchestrator
   - **책임**: Use Case, Application Service, Domain Service 조합
   - **문제점**: "Application"이 중복되어 구분 어려움

3. **ApplicationContext** (Context Management)
   - **실제 역할**: Container Lifecycle Manager
   - **책임**: Container 초기화, Wiring, 생명주기 관리
   - **문제점**: "Application"과 "Context"로 역할이 명확하지 않음

---

## 🔄 체계적 작업 절차 (8단계 준수)

### Phase 1: 새로운 네이밍 전략 설계

#### 1.1 역할 기반 네이밍 규칙 수립

- [ ] Infrastructure Container: `ExternalDependencyContainer` 또는 `InfrastructureContainer`
- [ ] Application Container: `BusinessServiceContainer` 또는 `ApplicationServiceContainer` (유지)
- [ ] Context Manager: `ContainerLifecycleManager` 또는 `DIContextManager`

#### 1.2 네이밍 일관성 검증

- [ ] DDD 계층별 명확한 구분
- [ ] 역할과 책임이 이름으로 즉시 파악 가능
- [ ] 기존 패턴과의 호환성 고려

### Phase 2: 점진적 파일명 변경

#### 2.1 Infrastructure Container 개명

- [ ] 파일명: `container.py` → `infrastructure_container.py`
- [ ] 클래스명: `ApplicationContainer` → `InfrastructureContainer`
- [ ] Import 경로 업데이트

#### 2.2 Context Manager 개명

- [ ] 파일명: `app_context.py` → `di_lifecycle_manager.py`
- [ ] 클래스명: `ApplicationContext` → `DILifecycleManager`
- [ ] 메서드명 일관성 확보

#### 2.3 Application Service Container 명확화

- [ ] 클래스명 유지: `ApplicationServiceContainer` (이미 명확함)
- [ ] 파일 내 주석으로 역할 명시 강화
- [ ] 메서드명 일관성 점검

### Phase 3: Import 구문 일괄 업데이트

#### 3.1 Infrastructure Container Import 수정

- [ ] `get_global_container` → `get_infrastructure_container`
- [ ] 모든 관련 파일의 import 구문 업데이트
- [ ] Factory 내부의 잘못된 접근 패턴 수정

#### 3.2 Context Manager Import 수정

- [ ] `get_application_context` → `get_di_lifecycle_manager`
- [ ] 초기화 및 생명주기 관리 코드 업데이트

#### 3.3 Application Service Container 접근 표준화

- [ ] Factory에서 올바른 접근 패턴 강제 적용
- [ ] Infrastructure 직접 접근 패턴 제거

### Phase 4: 하위 호환성 보장

#### 4.1 Legacy Wrapper 제공

- [ ] 기존 함수명에 대한 Deprecation Warning 함수 생성
- [ ] 점진적 마이그레이션을 위한 호환 계층 유지

#### 4.2 문서화 업데이트

- [ ] 새로운 네이밍 규칙 가이드 작성
- [ ] Import 패턴 Best Practice 문서
- [ ] Migration Guide 제공

---

## 🛠️ 구체적 구현 계획

### 📋 새로운 네이밍 체계

#### Option A: 역할 명시형 (권장)

```python
# Infrastructure Layer
from upbit_auto_trading.infrastructure.dependency_injection.infrastructure_container import (
    InfrastructureContainer,
    get_infrastructure_container
)

# Application Layer
from upbit_auto_trading.application.service_container import (
    ApplicationServiceContainer,
    get_application_service_container
)

# Context Management
from upbit_auto_trading.infrastructure.dependency_injection.di_lifecycle_manager import (
    DILifecycleManager,
    get_di_lifecycle_manager
)
```

#### Option B: 계층 명시형

```python
# Infrastructure Layer
from upbit_auto_trading.infrastructure.dependency_injection.infrastructure_di_container import (
    InfrastructureDIContainer,
    get_infrastructure_di_container
)

# Application Layer (변경 없음)
from upbit_auto_trading.application.container import (
    ApplicationServiceContainer,
    get_application_container
)

# Context Management
from upbit_auto_trading.infrastructure.dependency_injection.container_context_manager import (
    ContainerContextManager,
    get_container_context_manager
)
```

### 🔧 점진적 마이그레이션 전략

#### 1단계: 새 파일 생성 + 기존 파일 Deprecated 마킹

```python
# 새 파일: infrastructure_container.py
class InfrastructureContainer(containers.DeclarativeContainer):
    """Infrastructure Layer DI Container - 외부 의존성 관리 전담"""
    pass

# 기존 파일: container.py
import warnings
from .infrastructure_container import InfrastructureContainer

class ApplicationContainer(InfrastructureContainer):
    """DEPRECATED: InfrastructureContainer를 사용하세요"""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "ApplicationContainer는 deprecated입니다. InfrastructureContainer를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
```

#### 2단계: Factory 패턴 수정

```python
# ApplicationServiceContainer 표준 접근 패턴 강제
class BaseComponentFactory(ABC):
    def _get_infrastructure_container(self):
        """Infrastructure Container 직접 접근 (최후 수단)"""
        warnings.warn(
            "Infrastructure Container 직접 접근은 권장되지 않습니다. "
            "ApplicationServiceContainer를 통해 접근하세요.",
            UserWarning,
            stacklevel=2
        )
        from upbit_auto_trading.infrastructure.dependency_injection.infrastructure_container import (
            get_infrastructure_container
        )
        return get_infrastructure_container()

    def _get_service_via_application_container(self, service_getter, service_name: str):
        """✅ 권장: ApplicationServiceContainer를 통한 서비스 접근"""
        container = self._get_application_container()
        return self._get_service(service_getter, service_name)
```

---

## 🎯 성공 기준

### ✅ 기능적 성공 기준

1. **명확한 구분**: Import 시 어떤 Container인지 즉시 파악 가능
2. **정상 동작**: 모든 Factory가 새로운 네이밍으로 정상 동작
3. **하위 호환**: 기존 코드가 Warning과 함께 정상 동작
4. **표준화**: Factory에서 Infrastructure 직접 접근 패턴 제거

### ✅ 품질 기준

1. **코드 품질**: Import 구문이 명확하고 일관성 있음
2. **문서화**: 새로운 네이밍 규칙이 완전히 문서화됨
3. **안전성**: 모든 변경사항이 테스트를 통과
4. **유지보수성**: 향후 개발자가 즉시 이해 가능한 구조

### ✅ 아키텍처 기준

1. **DDD 준수**: 계층별 책임이 네이밍에 명확히 반영
2. **Clean Architecture**: 의존성 방향이 네이밍으로 표현
3. **Factory 패턴**: 올바른 Container 접근 패턴 확립
4. **확장성**: 새로운 Container 추가 시 일관된 네이밍 적용 가능

---

## 🚨 위험 요소 및 완화 방안

### 주요 위험 요소

| 위험 | 확률 | 영향도 | 완화 방안 |
|------|------|--------|-----------|
| **기존 코드 파손** | 중간 | 높음 | 점진적 변경, Legacy Wrapper 제공 |
| **Import 혼동 증가** | 낮음 | 중간 | 명확한 네이밍 규칙, IDE 자동완성 |
| **성능 영향** | 낮음 | 낮음 | Deprecation Warning 최소화 |
| **문서화 누락** | 중간 | 중간 | 체계적 문서 업데이트, 예제 제공 |

### 완화 전략

- **백업 필수**: 모든 Container 관련 파일 백업
- **점진적 적용**: 새 파일 생성 → 기존 파일 Deprecated → 완전 교체
- **테스트 강화**: 각 단계별 전체 시스템 동작 확인
- **문서 우선**: 변경사항을 즉시 문서에 반영

---

## 📋 상세 작업 계획

### Phase 1: 새로운 네이밍 설계 (예상 시간: 1시간)

- [x] 현재 문제점 분석 완료
- [ ] 새로운 네이밍 규칙 확정 (Option A vs Option B 결정)
- [ ] 마이그레이션 전략 세부 계획 수립
- [ ] 하위 호환성 전략 설계

### Phase 2: Infrastructure Container 개명 (예상 시간: 2시간)

- [ ] 새 파일 `infrastructure_container.py` 생성
- [ ] `InfrastructureContainer` 클래스 구현
- [ ] `get_infrastructure_container()` 함수 구현
- [ ] 기존 `container.py`에 Deprecation Warning 추가

### Phase 3: Context Manager 개명 (예상 시간: 1.5시간)

- [ ] 새 파일 `di_lifecycle_manager.py` 생성
- [ ] `DILifecycleManager` 클래스 구현
- [ ] `get_di_lifecycle_manager()` 함수 구현
- [ ] 기존 `app_context.py`에 Deprecation Warning 추가

### Phase 4: Import 구문 업데이트 (예상 시간: 2-3시간)

- [ ] Factory 내부의 Infrastructure 직접 접근 패턴 수정
- [ ] ApplicationServiceContainer를 통한 표준 접근 패턴 강제
- [ ] 모든 관련 파일의 Import 구문 업데이트
- [ ] Warning 메시지로 올바른 사용법 안내

### Phase 5: 문서화 및 검증 (예상 시간: 1시간)

- [ ] 새로운 네이밍 규칙 가이드 작성
- [ ] Import 패턴 Best Practice 문서 업데이트
- [ ] `python run_desktop_ui.py` 전체 동작 확인
- [ ] 모든 Factory 정상 동작 검증

---

## 💡 핵심 원칙 및 가이드라인

### 🎯 네이밍 원칙

1. **역할 명시성**: 파일명과 클래스명에서 역할이 즉시 파악되어야 함
2. **계층 구분성**: DDD 계층이 네이밍에 명확히 반영되어야 함
3. **일관성**: 동일한 패턴으로 모든 Container 네이밍
4. **확장성**: 새로운 Container 추가 시 일관된 규칙 적용 가능

### 🔄 마이그레이션 원칙

1. **점진적 변경**: 기존 코드 안정성 우선
2. **하위 호환성**: Deprecation Warning으로 점진적 마이그레이션 유도
3. **명확한 안내**: Warning 메시지에 올바른 사용법 포함
4. **문서 우선**: 모든 변경사항을 즉시 문서화

### 📊 검증 원칙

1. **기능 검증**: 모든 Factory 정상 동작 확인
2. **성능 검증**: Warning 오버헤드 최소화
3. **사용성 검증**: 개발자가 쉽게 이해하고 사용 가능
4. **유지보수성**: 향후 변경이 용이한 구조

---

## 🚀 즉시 시작할 작업

### 다음 단계: 네이밍 규칙 확정

1. **Option A vs Option B 결정**: 역할 명시형 vs 계층 명시형
2. **세부 네이밍 확정**: 정확한 클래스명과 함수명 결정
3. **마이그레이션 순서 확정**: 어떤 파일부터 변경할지 결정

### 준비 작업

```powershell
# 현재 Container 파일들 백업
Copy-Item "upbit_auto_trading\application\container.py" "upbit_auto_trading\application\container_backup_20251001.py"
Copy-Item "upbit_auto_trading\infrastructure\dependency_injection\container.py" "upbit_auto_trading\infrastructure\dependency_injection\container_backup_20251001.py"
Copy-Item "upbit_auto_trading\infrastructure\dependency_injection\app_context.py" "upbit_auto_trading\infrastructure\dependency_injection\app_context_backup_20251001.py"
```

---

## 📚 참고 문서

### 관련 분석 문서

- **Factory 패턴 전체 브리프**: `TASK_20250929_00-factory_pattern_project_brief.md`
- **현재 구조 장점 분석**: `CURRENT_ARCHITECTURE_ADVANTAGES.md`
- **DDD 통합 가이드**: `INTEGRATED_ARCHITECTURE_GUIDE.md`

### 영향받는 파일들

- **Factory**: `upbit_auto_trading/application/factories/settings_view_factory.py`
- **Application Container**: `upbit_auto_trading/application/container.py`
- **Infrastructure Container**: `upbit_auto_trading/infrastructure/dependency_injection/container.py`
- **Context Manager**: `upbit_auto_trading/infrastructure/dependency_injection/app_context.py`
- **Main Window**: `upbit_auto_trading/ui/desktop/main_window.py`

---

## 🎉 예상 최종 결과

### 기술적 성과

- ✅ 파일명과 클래스명에서 역할 즉시 파악 가능
- ✅ Import 구문의 명확성과 일관성 100% 달성
- ✅ Factory에서 올바른 Container 접근 패턴 확립
- ✅ 하위 호환성 보장으로 기존 코드 안정성 유지

### 아키텍처 가치

- **명확성**: 각 Container의 역할과 책임이 네이밍으로 표현
- **일관성**: 동일한 패턴으로 모든 Container 관리
- **확장성**: 새로운 Container 추가 시 일관된 네이밍 적용
- **유지보수성**: 개발자가 즉시 이해할 수 있는 명확한 구조

---

**문서 유형**: 상세 태스크 계획서
**우선순위**: 🔥 높음 (Factory 패턴 완성의 기반)
**예상 소요 시간**: 6-8시간
**종속성**: 없음 (독립 실행 가능)

---

> **💡 핵심 메시지**: "좋은 네이밍은 코드의 가독성과 유지보수성을 결정짓는 핵심 요소"
>
> **🎯 성공 전략**: 점진적 변경으로 안정성을 보장하면서, 명확한 네이밍 규칙으로 장기적 유지보수성 확보!

---

**다음 에이전트 시작점**: Phase 1에서 Option A (역할 명시형) vs Option B (계층 명시형) 네이밍 규칙 확정 후 구현 시작
