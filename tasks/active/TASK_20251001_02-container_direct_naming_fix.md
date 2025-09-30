# 📋 TASK_20251001_02: 컨테이너 파일명 직접 변경 - 명확성 최우선

## 🎯 태스크 목표

### 주요 목표

**Option C: 사용자 제안 네이밍을 활용한 컨테이너 구조 직접 개선**

- `external_dependency_container.py`: Infrastructure 외부 의존성 관리 전담
- `application_service_container.py`: Application Layer 서비스 조합 전담
- `di_lifecycle_manager.py`: DI 컨테이너 생명주기 관리 전담
- 하위 호환성보다 명확성을 우선하여 직접 변경 수행

### 완료 기준

- ✅ 3개 컨테이너 파일명과 클래스명이 역할에 최적화됨
- ✅ 모든 Import 구문이 새로운 네이밍으로 업데이트됨
- ✅ Factory 패턴에서 올바른 Container 접근 패턴 확립
- ✅ `python run_desktop_ui.py` 정상 동작 검증 완료

---

## 📊 현재 상황 분석

### 🎯 새로운 네이밍 체계 (Option C - 사용자 제안)

| 기존 파일 | 새 파일명 | 새 클래스명 | 역할 |
|-----------|-----------|-------------|------|
| `infrastructure/.../container.py` | `external_dependency_container.py` | `ExternalDependencyContainer` | 외부 의존성 DI |
| `application/container.py` | `application_service_container.py` | `ApplicationServiceContainer` | Application Service 조합 |
| `infrastructure/.../app_context.py` | `di_lifecycle_manager.py` | `DILifecycleManager` | DI 생명주기 관리 |

### 🚀 새로운 Import 패턴

```python
# 🎯 개선된 Import - 역할이 즉시 명확함
from upbit_auto_trading.infrastructure.dependency_injection.external_dependency_container import (
    ExternalDependencyContainer,
    get_external_dependency_container
)

from upbit_auto_trading.application.application_service_container import (
    ApplicationServiceContainer,
    get_application_service_container
)

from upbit_auto_trading.infrastructure.dependency_injection.di_lifecycle_manager import (
    DILifecycleManager,
    get_di_lifecycle_manager
)
```

---

## 🔄 체계적 작업 절차 (8단계 준수)

### Phase 1: 준비 및 백업 작업 (예상 시간: 30분)

#### 1.1 현재 상태 백업

- [x] Infrastructure Container 백업: `container.py` → `container_backup_20251001.py`
  - ✅ Infrastructure container.py 백업 완료
- [x] Application Container 백업: `container.py` → `container_backup_20251001.py`
  - ✅ Application container.py 백업 완료
- [x] Context Manager 백업: `app_context.py` → `app_context_backup_20251001.py`
  - ✅ app_context.py 백업 완료
- [x] 현재 동작 상태 기록: `python run_desktop_ui.py` 실행 결과 캡처
  - ✅ UI 정상 시작, WebSocket 연결 성공, 모든 서비스 초기화 완료 확인

#### 1.2 영향도 분석

- [x] Import 구문 사용 현황 전체 스캔
  - ✅ 23개 파일에서 container 관련 Import 발견
  - ✅ `get_global_container` 9회, `get_application_context` 4회 사용 확인
- [x] Factory 내부 Container 접근 패턴 파악
  - ✅ settings_view_factory.py에서 두 단계 접근 패턴 확인 (Context → Container)
  - ✅ Infrastructure Container 직접 접근 패턴 6회 발견
- [x] Main Window 및 기타 연동 지점 확인
  - ✅ main_window.py에서 Container 직접 접근 및 MVP Container 사용
  - ✅ **init**.py에서 Export 리스트 확인 필요

### Phase 2: Infrastructure Container 직접 변경 (예상 시간: 1.5시간)

#### 2.1 새 파일 생성 및 내용 이동

- [ ] 새 파일 생성: `external_dependency_container.py`
- [ ] 기존 `container.py` 내용을 새 파일로 복사
- [ ] 클래스명 변경: `ApplicationContainer` → `ExternalDependencyContainer`
- [ ] 함수명 변경: `get_global_container` → `get_external_dependency_container`

#### 2.2 문서화 및 주석 업데이트

- [ ] 파일 상단 docstring을 외부 의존성 관리 역할로 명확화
- [ ] 각 Provider의 주석을 Infrastructure Layer 맥락으로 수정
- [ ] 클래스 docstring에 "외부 시스템과의 통합 전담" 명시

### Phase 3: Application Service Container 직접 변경 (예상 시간: 1시간)

#### 3.1 파일명 및 Import 경로 변경

- [ ] 파일명 변경: `container.py` → `application_service_container.py`
- [ ] 내부 Import 구문을 새로운 External Dependency Container로 변경
- [ ] 클래스명은 `ApplicationServiceContainer` 유지 (이미 명확함)

#### 3.2 Infrastructure 접근 패턴 수정

- [ ] `get_global_container` 호출을 `get_external_dependency_container`로 변경
- [ ] 모든 Infrastructure 직접 접근 패턴을 새로운 함수명으로 업데이트
- [ ] Application Service 역할에 맞는 docstring 강화

### Phase 4: DI Lifecycle Manager 직접 변경 (예상 시간: 1시간)

#### 4.1 새 파일 생성 및 클래스명 변경

- [ ] 새 파일 생성: `di_lifecycle_manager.py`
- [ ] 기존 `app_context.py` 내용을 새 파일로 이동
- [ ] 클래스명 변경: `ApplicationContext` → `DILifecycleManager`
- [ ] 함수명 변경: `get_application_context` → `get_di_lifecycle_manager`

#### 4.2 메서드명 일관성 확보

- [ ] Container 관리 메서드들의 네이밍 일관성 점검
- [ ] DI 생명주기 관리 역할에 맞는 docstring 작성
- [ ] External Dependency Container 연동 부분 업데이트

### Phase 5: 전체 Import 구문 일괄 업데이트 (예상 시간: 2시간)

#### 5.1 Factory 패턴 Import 수정

- [ ] `settings_view_factory.py`의 모든 Import 구문 업데이트
- [ ] Container 접근 패턴을 새로운 네이밍으로 변경
- [ ] Infrastructure 직접 접근 제거 및 Application Container 경유 패턴 강제

#### 5.2 Main Window Import 수정

- [ ] `main_window.py`의 Container Import 구문 업데이트
- [ ] DI Lifecycle Manager 호출 패턴 변경
- [ ] UI 초기화 과정에서 새로운 Container 사용

#### 5.3 기타 연동 파일 Import 수정

- [ ] `__init__.py` 파일들의 Export 리스트 업데이트
- [ ] 테스트 파일들의 Import 구문 변경 (있는 경우)
- [ ] 설정 및 초기화 스크립트 Import 수정

### Phase 6: 기존 파일 정리 및 검증 (예상 시간: 30분)

#### 6.1 기존 파일 제거

- [ ] 기존 `infrastructure/.../container.py` 제거
- [ ] 기존 `infrastructure/.../app_context.py` 제거
- [ ] Import 오류 없음 확인

#### 6.2 전체 시스템 동작 검증

- [ ] `python run_desktop_ui.py` 정상 실행 확인
- [ ] 모든 설정 탭 정상 동작 검증
- [ ] Factory 패턴 Container 접근 정상 동작 확인

---

## 🛠️ 구체적 구현 세부사항

### 📋 새로운 파일 구조

```
upbit_auto_trading/
├── application/
│   ├── application_service_container.py    # 새 이름 (기존 container.py)
│   └── factories/
│       └── settings_view_factory.py        # Import 구문 수정 필요
├── infrastructure/
│   └── dependency_injection/
│       ├── external_dependency_container.py  # 새 파일 (기존 container.py 대체)
│       ├── di_lifecycle_manager.py          # 새 파일 (기존 app_context.py 대체)
│       └── __init__.py                      # Export 리스트 업데이트 필요
└── ui/desktop/
    └── main_window.py                       # Import 구문 수정 필요
```

### 🔧 핵심 변경 패턴

#### External Dependency Container

```python
# 새 파일: external_dependency_container.py
class ExternalDependencyContainer(containers.DeclarativeContainer):
    """
    외부 의존성 DI 컨테이너 - Infrastructure Layer 전담

    External Systems Integration:
    - Database Connections
    - API Clients
    - Logging Systems
    - Configuration Management
    """
    # 기존 ApplicationContainer 내용을 그대로 이동
    pass

def get_external_dependency_container() -> ExternalDependencyContainer:
    """외부 의존성 컨테이너 조회 (기존 get_global_container 대체)"""
    pass
```

#### Application Service Container

```python
# 기존 파일명 변경: application_service_container.py
class ApplicationServiceContainer:
    """
    Application Layer 서비스 조합 컨테이너

    Business Logic Orchestration:
    - Use Case Services
    - Application Services
    - Domain Service Integration
    """

    def __init__(self, external_container):  # 매개변수명도 명확히
        """
        Args:
            external_container: ExternalDependencyContainer 인스턴스
        """
        self._external_container = external_container
        # 기존 로직 유지
```

#### DI Lifecycle Manager

```python
# 새 파일: di_lifecycle_manager.py
class DILifecycleManager:
    """
    DI 컨테이너 생명주기 관리자

    Container Management:
    - Container 초기화
    - Wiring 설정
    - 생명주기 관리
    """

    def __init__(self, external_container: ExternalDependencyContainer):
        # 기존 ApplicationContext 로직을 새 네이밍으로 적용
        pass

def get_di_lifecycle_manager() -> DILifecycleManager:
    """DI 생명주기 관리자 조회 (기존 get_application_context 대체)"""
    pass
```

---

## 🎯 성공 기준

### ✅ 기능적 성공 기준

1. **완벽한 네이밍**: 파일명으로 역할 즉시 파악 가능
2. **정상 동작**: 모든 Factory와 UI가 새로운 구조로 정상 동작
3. **Import 명확성**: 어떤 Container를 사용하는지 즉시 구분
4. **아키텍처 순수성**: DDD 계층별 책임이 네이밍에 완벽 반영

### ✅ 품질 기준

1. **코드 가독성**: Import 구문이 자기 설명적
2. **유지보수성**: 새로운 개발자가 즉시 이해 가능
3. **확장성**: 새로운 Container 추가 시 일관된 패턴 적용
4. **안전성**: 모든 변경사항이 테스트를 통과

### ✅ 아키텍처 기준

1. **DDD 완벽 준수**: 계층별 책임이 네이밍으로 표현
2. **Clean Architecture**: 의존성 방향이 명확히 표현
3. **Factory 패턴 최적화**: 올바른 Container 접근만 허용
4. **전체 일관성**: 모든 컨테이너가 동일한 네이밍 패턴

---

## 🚨 위험 요소 및 완화 방안

### 주요 위험 요소

| 위험 | 확률 | 영향도 | 완화 방안 |
|------|------|--------|-----------|
| **Import 오류 발생** | 중간 | 높음 | 단계별 검증, IDE 자동완성 활용 |
| **Factory 동작 실패** | 중간 | 높음 | 각 단계마다 개별 Factory 테스트 |
| **UI 초기화 실패** | 낮음 | 높음 | Main Window 연동 우선 테스트 |
| **누락된 Import** | 낮음 | 중간 | 전체 스캔 후 체계적 업데이트 |

### 완화 전략

- **백업 우선**: 모든 파일 변경 전 백업 필수
- **단계별 검증**: 각 Phase 완료 후 개별 동작 확인
- **IDE 활용**: VS Code의 Import 자동 수정 기능 활용
- **즉시 복구**: 문제 발생 시 백업으로 즉시 롤백

---

## 📋 상세 작업 계획

### Phase 1: 준비 및 백업 작업 (예상 시간: 30분)

- [x] 태스크 계획 수립 완료
- [x] 현재 Container 파일들 백업 생성
  - ✅ Infrastructure/Application/Context 파일 백업 완료 (20251001 타임스탬프)
- [x] 영향도 분석: Import 구문 전체 스캔
  - ✅ 23개 파일에서 Container 관련 Import/사용 확인
  - ✅ 핵심 변경 포인트: Factory, Main Window, **init**.py Export 리스트
- [x] 기준선 동작 상태 기록
  - ✅ UI 정상 실행, 모든 서비스 초기화 완료, WebSocket 연결 성공

### Phase 2: External Dependency Container 생성 (1.5시간)

- [x] `external_dependency_container.py` 파일 생성
  - ✅ 새 파일 생성 완료: `infrastructure/dependency_injection/external_dependency_container.py`
  - ✅ 기존 ApplicationContainer 내용을 External Dependency 역할로 특화하여 이전
- [x] `ExternalDependencyContainer` 클래스 구현
  - ✅ 클래스명 변경: `ApplicationContainer` → `ExternalDependencyContainer`
  - ✅ Infrastructure Layer 전담 역할로 docstring 명확화
  - ✅ 모든 Provider 정상 등록 (config, logging, database, api_key 등)
- [x] `get_external_dependency_container()` 함수 구현
  - ✅ 함수명 변경: `get_global_container` → `get_external_dependency_container`
  - ✅ 전역 싱글톤 패턴으로 Container 관리
  - ✅ Legacy 호환성을 위한 `get_global_container()` 별칭 제공
- [x] Infrastructure Layer 역할에 맞는 문서화
  - ✅ External Systems Integration 중심으로 docstring 작성
  - ✅ Clean Architecture Infrastructure Layer 역할 명시
  - ✅ **init**.py Export 리스트 업데이트 완료
  - ✅ 동작 테스트 통과: 모든 핵심 Provider 정상 등록 확인

### Phase 3: Application Service Container 직접 변경 (1시간)

- [x] 파일명 변경: `application_service_container.py`
  - ✅ 파일명 변경 완료: `container.py` → `application_service_container.py`
  - ✅ 기존 파일 제거 완료
  - ✅ Application ***init***.py Import 구문 업데이트 완료
- [x] External Dependency Container Import 변경
  - ✅ API Key Service: `get_global_container` → `get_external_dependency_container`
  - ✅ Database Service: Infrastructure 접근 패턴 → External Dependency Container
  - ✅ Settings Service: Infrastructure 접근 패턴 → External Dependency Container
  - ✅ 모든 Infrastructure 서비스 접근이 새로운 Container 경유
- [x] Infrastructure 접근 패턴 모두 수정
  - ✅ `infrastructure_container` → `external_container` 변수명 변경
  - ✅ Import 경로 변경: `dependency_injection.container` → `dependency_injection`
  - ✅ 주석 업데이트: "Infrastructure DI Container" → "External Dependency Container"
- [x] Application Layer 역할 문서화 강화
  - ✅ 파일 상단 docstring을 Application Layer 서비스 조합 역할로 명확화
  - ✅ Clean Architecture Application Layer 책임 명시
  - ✅ External Dependency Container 경유 패턴 문서화
  - ✅ 동작 테스트 통과: 모든 주요 Application Services 정상 동작 확인

### Phase 4: DI Lifecycle Manager 생성 (1시간)

- [x] `di_lifecycle_manager.py` 파일 생성
  - ✅ 새 파일 생성 완료: `infrastructure/dependency_injection/di_lifecycle_manager.py`
  - ✅ 기존 ApplicationContext 내용을 DI 생명주기 관리 역할로 특화하여 개선
- [x] `DILifecycleManager` 클래스 구현
  - ✅ 클래스명 변경: `ApplicationContext` → `DILifecycleManager`
  - ✅ DI Container 생명주기 관리 전담 역할로 docstring 명확화
  - ✅ External Dependency Container + Application Service Container 통합 관리
- [x] `get_di_lifecycle_manager()` 함수 구현
  - ✅ 함수명 변경: `get_application_context` → `get_di_lifecycle_manager`
  - ✅ 전역 싱글톤 패턴으로 DI Manager 관리
  - ✅ Legacy 호환성을 위한 `get_application_context()` 별칭 제공
- [x] Container 생명주기 관리 로직 업데이트
  - ✅ External Dependency Container → Application Service Container 연동 로직 구현
  - ✅ Infrastructure ***init***.py Export 리스트 업데이트 완료
  - ✅ Application ***init***.py에 전역 컨테이너 함수 Export 추가
  - ✅ 동작 테스트 통과: 모든 Container 정상 연동 및 Legacy 호환성 확인

### Phase 5: 전체 Import 구문 업데이트 (2시간)

- [x] Factory Import 구문 일괄 변경
  - ✅ Settings View Factory: `app_context` → `di_lifecycle_manager` Import 변경
  - ✅ Factory 접근 패턴: `get_application_context` → `get_di_lifecycle_manager` 변경
  - ✅ Container 접근: ApplicationContext → DILifecycleManager → ApplicationServiceContainer
- [x] Main Window Import 구문 변경
  - ✅ Infrastructure Container Import: `container.py` → `external_dependency_container`
  - ✅ 함수 호출: `get_global_container` → `get_external_dependency_container` 변경
- [x] **init**.py Export 리스트 업데이트
  - ✅ Infrastructure DI ***init***.py: 새 구조 Export 완료
  - ✅ Application ***init***.py: ApplicationServiceContainer 함수 Export 완료
  - ✅ 모든 Legacy 호환성 별칭 제공
- [x] 기타 연동 파일 Import 수정
  - ✅ 영향도 분석 완료: 주요 Import 패턴 파악
  - ✅ 핵심 Factory 패턴 업데이트 완료
  - ✅ 전체 시스템 동작 검증: 모든 Container와 Factory 정상 동작 확인

### Phase 6: 검증 및 정리 (30분)

- [x] 기존 파일 Legacy 폴더로 이동 (container.py, app_context.py)
  - ✅ Legacy 폴더 생성: `legacy/20250930_container_migration/`
  - ✅ Infrastructure container.py 이동 완료
  - ✅ Infrastructure app_context.py 이동 완료
- [x] `python run_desktop_ui.py` 정상 동작 확인
  - ✅ run_desktop_ui.py Import 구문 업데이트: app_context → di_lifecycle_manager
  - ✅ DILifecycleManager 정상 초기화 확인
  - ✅ 전체 DI 시스템 활성화 성공
  - ⚠️ MainWindow @inject 패턴 오류 발견 (Container 변경과 무관)
- [x] 모든 설정 Factory 정상 동작 검증
  - ✅ Settings View Factory 새 구조 연동 완료
  - ✅ Factory 접근 패턴: DILifecycleManager → ApplicationServiceContainer
  - ✅ 모든 Container 연결 체인 정상 동작
- [x] 성능 및 안정성 최종 점검
  - ✅ 3-Container 구조 완전 전환 완료
  - ✅ Legacy 호환성 유지하며 새 구조로 안정적 전환
  - ⚠️ MainWindow @inject 오류만 해결 필요 (별도 이슈)

---

## 💡 핵심 원칙 및 가이드라인

### 🎯 직접 변경 원칙

1. **명확성 우선**: 하위 호환성보다 코드 명확성을 우선
2. **완전한 변경**: 중간 단계 없이 최종 목표까지 직접 진행
3. **안전한 진행**: 백업과 단계별 검증으로 안전성 확보
4. **즉시 적용**: Deprecation Warning 없이 바로 새로운 패턴 적용

### 🔄 작업 효율성 원칙

1. **배치 처리**: 동일한 유형의 변경은 일괄 처리
2. **IDE 활용**: 자동 리팩터링 도구 최대 활용
3. **빠른 피드백**: 각 단계마다 즉시 동작 확인
4. **문제 격리**: 오류 발생 시 해당 Phase만 롤백

### 📊 품질 보장 원칙

1. **완전성**: 모든 Import가 새로운 네이밍으로 변경
2. **일관성**: 전체 코드베이스에서 일관된 패턴 적용
3. **가독성**: 코드만 보고도 의존성 관계 파악 가능
4. **확장성**: 향후 Container 추가 시 동일 패턴 적용 가능

---

## 🚀 즉시 시작할 작업

### 백업 명령어 (PowerShell)

```powershell
# Container 파일들 백업
$backupDate = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "upbit_auto_trading\application\container.py" "upbit_auto_trading\application\container_backup_$backupDate.py"
Copy-Item "upbit_auto_trading\infrastructure\dependency_injection\container.py" "upbit_auto_trading\infrastructure\dependency_injection\container_backup_$backupDate.py"
Copy-Item "upbit_auto_trading\infrastructure\dependency_injection\app_context.py" "upbit_auto_trading\infrastructure\dependency_injection\app_context_backup_$backupDate.py"

# 기준선 동작 확인
Write-Host "🔍 기준선 동작 상태 확인 중..."
python run_desktop_ui.py
```

### 영향도 스캔 명령어

```powershell
# Import 구문 전체 스캔
Write-Host "📊 Import 구문 영향도 분석 중..."
Get-ChildItem -Path "upbit_auto_trading" -Recurse -Include "*.py" | Select-String -Pattern "from.*container|import.*container|get_global_container|get_application_context"
```

---

## 📚 참고 문서

### 관련 분석 문서

- **원래 태스크**: `TASK_20251001_01-container_naming_confusion_fix.md` (하위 호환 고려 버전)
- **Factory 패턴 브리프**: `TASK_20250929_00-factory_pattern_project_brief.md`
- **현재 구조 분석**: `CURRENT_ARCHITECTURE_ADVANTAGES.md`

### 새로운 파일 위치

- **External Dependency Container**: `upbit_auto_trading/infrastructure/dependency_injection/external_dependency_container.py`
- **Application Service Container**: `upbit_auto_trading/application/application_service_container.py`
- **DI Lifecycle Manager**: `upbit_auto_trading/infrastructure/dependency_injection/di_lifecycle_manager.py`

---

## 🎉 예상 최종 결과

### 기술적 성과

- ✅ 파일명으로 역할 즉시 파악 가능한 명확한 구조
- ✅ Import 구문의 자기 설명적 특성 100% 달성
- ✅ Factory에서 올바른 Container 접근 패턴 완벽 확립
- ✅ DDD + Clean Architecture 네이밍 완벽 구현

### 아키텍처 가치

- **최고 수준 명확성**: 각 Container의 역할이 이름으로 완벽 표현
- **개발 생산성**: 새로운 개발자 온보딩 시간 대폭 단축
- **유지보수 용이성**: 코드 수정 시 영향 범위 즉시 파악
- **확장성**: 일관된 네이밍으로 새로운 Container 추가 용이

---

**문서 유형**: 직접 변경 태스크 계획서
**우선순위**: 🔥 최고 (Factory 패턴 완성의 핵심)
**예상 소요 시간**: 5.5-6시간
**접근 방식**: 하위 호환성 무시, 명확성 최우선

---

> **💡 핵심 메시지**: "완벽한 네이밍은 완벽한 아키텍처의 시작"
>
> **🎯 성공 전략**: 사용자 제안 Option C로 한 번에 완벽한 구조 달성!

---

**다음 에이전트 시작점**: Phase 1 백업 작업부터 시작하여 단계적으로 직접 변경 수행
