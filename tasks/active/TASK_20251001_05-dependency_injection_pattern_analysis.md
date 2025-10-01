# 📋 TASK_20251001_05: Dependency Injection 패턴 표준화 분석 및 조사

## 🎯 태스크 목표

### 주요 목표

**3-Container DI 시스템의 패턴 파편화 분석 및 표준 패턴 수립을 위한 종합 조사**

- **기술적 목표**: dependency-injector 라이브러리의 올바른 사용 패턴 규명
- **아키텍처 목표**: 3-Container (External, Application, Presentation) 간 일관된 DI 패턴 수립
- **품질 목표**: Provider Chain의 정확한 연결 체계 확립

### 완료 기준

- ✅ **패턴 파편화 완전 분석**: 현재 사용 중인 모든 DI 패턴 유형 식별
- ✅ **표준 패턴 정의**: dependency-injector 라이브러리 기준 올바른 패턴 수립
- ✅ **문제점 매트릭스 완성**: 각 파일별 구체적 문제점과 해결방법 매핑
- ✅ **후속 태스크 설계**: 실제 수정 작업을 위한 체계적 계획 수립

---

## 📊 현재 상황 분석

### 🚨 확인된 핵심 문제

```
ERROR | upbit.MainWindowPresenter | ❌ API 키 로드 실패:
'dependency_injector.providers.Factory' object has no attribute 'load_api_keys'
```

**근본 원인**: PresentationContainer에서 `external_container.provided.api_key_service.provider` 패턴으로 인한 Provider 객체 반환

### 🧩 패턴 파편화 현황

1. **MainWindow**: `@inject` + `Provide["service_name"]` 패턴
2. **PresentationContainer**: `.provided.service.provider` 패턴 ❌
3. **ExternalDependencyContainer**: `providers.Factory` 정의 패턴
4. **MainWindowPresenter**: `services.get('service_name')` Dictionary 접근 패턴

### 🔍 조사 필요 영역

- Container 간 서비스 참조 패턴 일관성
- Provider Chain의 올바른 연결 방법
- Wiring 모듈 범위와 패턴 통일성
- Runtime Service Resolution 체계

---

## 🔄 체계적 작업 절차 (필수 준수)

### 8단계 작업 절차

1. **📋 작업 항목 확인**: 태스크 문서에서 구체적 작업 내용 파악
2. **🔍 검토 후 세부 작업 항목 생성**: 작업을 더 작은 단위로 분해
3. **🔄 작업중 마킹**: 해당 작업 항목을 `[-]` 상태로 변경
4. **⚙️ 작업 항목 진행**: 실제 작업 수행
5. **✅ 작업 내용 확인**: 결과물 검증 및 품질 확인
6. **📝 상세 작업 내용 업데이트**: 태스크 문서에 진행사항 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 단계 진행 전 검토 및 승인

### 작업 상태 마커

- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

---

## 📋 작업 계획 - DI 패턴 종합 분석

### Phase 1: dependency-injector 표준 패턴 연구 및 정의 (예상 시간: 2시간)

#### 1.1 표준 패턴 문서 조사

- [ ] **dependency-injector 공식 문서 분석**
  - Container 간 서비스 참조 표준 패턴 조사
  - .provided vs .provided.provider vs () 호출 패턴 비교
  - Wiring 모듈과 @inject 데코레이터 올바른 사용법 연구

- [ ] **베스트 프랙티스 사례 연구**
  - GitHub 오픈소스 프로젝트에서 dependency-injector 사용 패턴 조사
  - 3-Container 아키텍처 유사 사례 분석
  - MVP 패턴과 DI 통합 사례 연구

#### 1.2 프로젝트별 표준 패턴 정의

- [ ] **3-Container 간 참조 표준 패턴 수립**
  - ExternalDependencyContainer → ApplicationServiceContainer 패턴
  - ApplicationServiceContainer → PresentationContainer 패턴
  - PresentationContainer 내부 서비스 주입 패턴

- [ ] **@inject 데코레이터 사용 표준 정의**
  - MainWindow @inject 패턴 표준화
  - Presenter services Dict 패턴과의 연동 표준
  - Wiring 모듈 범위 및 우선순위 정의

### Phase 2: 현재 프로젝트 DI 패턴 전면 분석 (예상 시간: 3시간)

#### 2.1 Container 정의 파일 분석

- [ ] **ExternalDependencyContainer 분석**
  - `upbit_auto_trading/infrastructure/dependency_injection/external_dependency_container.py`
  - 모든 Provider 정의 패턴 조사 (Factory, Singleton, Configuration)
  - wire_external_dependency_modules 함수 모듈 범위 분석
  - Dependency 체인 및 순환 참조 검사

- [ ] **ApplicationServiceContainer 분석**
  - `upbit_auto_trading/application/application_service_container.py`
  - ExternalDependencyContainer 참조 패턴 분석
  - Business Logic Services Provider 패턴 조사
  - Repository Container 연동 방식 검토

- [ ] **PresentationContainer 분석**
  - `upbit_auto_trading/presentation/presentation_container.py`
  - External/Application Container 참조 패턴 분석 (**핵심 문제 영역**)
  - MainWindowPresenter services Dict 패턴 검토
  - UI Infrastructure Provider 정의 방식 조사

#### 2.2 서비스 사용 패턴 분석

- [ ] **MainWindow DI 패턴 분석**
  - `upbit_auto_trading/ui/desktop/main_window.py`
  - @inject 데코레이터 사용 방식 검토
  - Provide["service_name"] 패턴 정확성 확인
  - Wiring 모듈 포함 여부 및 적용 범위 검사

- [ ] **MainWindowPresenter 서비스 접근 패턴 분석**
  - `upbit_auto_trading/presentation/presenters/main_window_presenter.py`
  - services.get() Dictionary 접근 패턴 검토
  - API Key Service, Theme Service 등 실제 사용 패턴 분석
  - 에러 발생 지점 정확한 원인 분석

#### 2.3 DILifecycleManager 통합 관리 패턴 분석

- [ ] **3-Container 생명주기 관리 분석**
  - `upbit_auto_trading/infrastructure/dependency_injection/di_lifecycle_manager.py`
  - Container 초기화 순서 및 의존성 주입 체계 검토
  - Wiring 설정 방식 및 모듈 포함 패턴 분석
  - get_main_window_presenter() 메서드 호출 체계 검토

### Phase 3: 패턴 파편화 매트릭스 작성 (예상 시간: 2시간)

#### 3.1 DI 패턴 분류 및 문제점 매핑

- [ ] **패턴 유형별 분류**
  - Container 정의 패턴들 (Factory, Singleton, Configuration, Dict)
  - Container 간 참조 패턴들 (.provided, .provided.provider, () 호출)
  - 서비스 주입 패턴들 (@inject, services dict, 직접 호출)
  - Wiring 설정 패턴들 (모듈 범위, 데코레이터 활성화)

- [ ] **문제점 매트릭스 작성**

  ```
  | 파일명 | 현재 패턴 | 문제점 | 표준 패턴 | 우선순위 |
  |--------|-----------|--------|-----------|----------|
  | PresentationContainer | .provided.service.provider | Factory 객체 반환 | .provided.service | 🔥 높음 |
  | MainWindow | @inject + Provide | Wiring 불완전 | 표준 @inject | 🟡 중간 |
  ```

#### 3.2 영향도 및 의존성 분석

- [ ] **변경 영향도 분석**
  - 각 패턴 수정 시 다른 컴포넌트에 미치는 영향 평가
  - Provider Chain 수정 시 Runtime 에러 가능성 분석
  - 순환 참조 및 의존성 충돌 위험도 평가

- [ ] **우선순위 매트릭스 작성**
  - 🔥 즉시 수정 필요 (시스템 오류 직접 원인)
  - 🟡 단기 수정 권장 (일관성 및 유지보수성)
  - 🟢 장기 개선 계획 (성능 및 확장성)

### Phase 4: 표준화 가이드라인 및 후속 태스크 설계 (예상 시간: 1시간)

#### 4.1 DI 패턴 표준화 가이드라인 작성

- [ ] **3-Container DI 패턴 표준 정의**
  - Container 간 서비스 참조 표준 패턴
  - Provider 정의 및 사용 표준 패턴
  - @inject 데코레이터 적용 표준 패턴
  - Wiring 모듈 설정 표준 패턴

- [ ] **코딩 스타일 가이드라인 수립**

  ```python
  # ✅ 표준 패턴 예시
  # Container 간 참조
  api_key_service=external_container.provided.api_key_service,

  # @inject 데코레이터 사용
  @inject
  def __init__(self, api_key_service=Provide["api_key_service"]):

  # Wiring 모듈 설정
  container.wire(modules=["실제_존재하는_모듈"])
  ```

#### 4.2 후속 태스크 설계

- [ ] **TASK_20251001_06 설계: DI 패턴 표준화 구현**
  - Phase별 수정 작업 계획 수립
  - 우선순위별 파일 수정 순서 결정
  - 테스트 및 검증 방법 정의
  - 롤백 계획 및 안전장치 설계

---

## 🛠️ 개발할 분석 도구

### `di_pattern_analyzer.py`: DI 패턴 분석 도구

```python
"""
dependency-injector 패턴 분석 및 검증 도구

기능:
- Container 파일 내 Provider 패턴 분석
- .provided 사용 패턴 검증
- @inject 데코레이터 적용 현황 조사
- Wiring 모듈 유효성 검사
"""
```

### `pattern_matrix_generator.py`: 패턴 매트릭스 생성 도구

```python
"""
DI 패턴 파편화 매트릭스 자동 생성 도구

출력:
- Markdown 테이블 형식 매트릭스
- 우선순위별 분류된 문제점 리스트
- 표준 패턴 변환 가이드
"""
```

---

## 🎯 성공 기준

### ✅ 조사 완료 기준

1. **패턴 파편화 완전 규명**: 모든 DI 사용 패턴이 분류되고 문제점이 식별됨
2. **표준 패턴 수립 완료**: dependency-injector 라이브러리 기준 올바른 패턴 정의됨
3. **문제점 매트릭스 완성**: 각 파일별 구체적 수정 방법이 매핑됨
4. **후속 태스크 설계 완료**: 실제 수정 작업을 위한 체계적 계획 수립됨

### ✅ 품질 기준

1. **정확성**: dependency-injector 공식 문서 기준 검증된 패턴만 채택
2. **완전성**: 프로젝트 내 모든 DI 사용 사례가 분석됨
3. **실행 가능성**: 후속 태스크에서 즉시 적용 가능한 구체적 가이드 제공
4. **안전성**: 변경 시 부작용 및 롤백 계획이 포함됨

---

## 💡 작업 시 주의사항

### 조사 정확성 원칙

- **공식 문서 우선**: dependency-injector 공식 문서를 최우선 참조 자료로 활용
- **실제 코드 검증**: 모든 패턴은 실제 동작하는 코드로 검증
- **다각도 검토**: Container, Service, Client 관점에서 다면적 분석
- **버전 호환성**: 현재 사용 중인 dependency-injector 버전과의 호환성 확인

### 분석 범위 원칙

- **전체 프로젝트 스캔**: 누락되는 DI 사용 사례가 없도록 전면 조사
- **의존성 체인 추적**: Provider → Consumer까지 전체 흐름 분석
- **에러 케이스 중점**: 실제 발생한 오류의 근본 원인 집중 분석
- **확장성 고려**: 향후 추가될 Container 및 Service에 대한 확장 가능성 고려

### 후속 태스크 연계 원칙

- **단계적 적용**: 위험도가 낮은 것부터 순차적 수정 계획
- **테스트 우선**: 모든 수정 사항에 대한 검증 방법 사전 정의
- **롤백 가능성**: 문제 발생 시 즉시 이전 상태로 복원 가능한 계획
- **문서화**: 변경 사항과 근거를 상세히 기록하여 향후 참조 가능하도록 함

---

## 🚀 즉시 시작할 작업

### 1단계: dependency-injector 공식 문서 조사 (30분)

```bash
# Context7 MCP를 활용한 dependency-injector 문서 조사
# 1. Container 간 참조 표준 패턴
# 2. .provided 사용법 및 베스트 프랙티스
# 3. @inject 데코레이터와 Wiring 연동 방법
```

### 2단계: 현재 프로젝트 DI 사용 현황 스캔 (15분)

```powershell
# DI 패턴 사용 파일 전체 스캔
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "providers\.|@inject|\.provided|Provide\[" | Group-Object Path

# Container 정의 파일 식별
Get-ChildItem upbit_auto_trading -Recurse -Include "*container*.py" | ForEach-Object { Write-Host "📁 $($_.FullName)" }

# Presenter 및 Service 파일 식별
Get-ChildItem upbit_auto_trading -Recurse -Include "*presenter*.py", "*service*.py" | ForEach-Object { Write-Host "🔧 $($_.FullName)" }
```

### 3단계: 핵심 문제 파일 우선 분석 (15분)

```
우선순위 분석 대상:
1. PresentationContainer.py (🔥 에러 직접 원인)
2. MainWindowPresenter.py (🔥 에러 발생 지점)
3. ExternalDependencyContainer.py (🟡 Provider 정의부)
4. DILifecycleManager.py (🟡 Container 통합 관리)
```

---

## 🔗 연관 태스크

### 선행 태스크

- **TASK_20251001_04**: 완전한 Container 아키텍처 재구축 (🔄 **진행 중** - 구조는 완성, DI 패턴 문제 발견)

### 후속 태스크 계획

- **TASK_20251001_06**: DI 패턴 표준화 구현 (🔥 **즉시 생성 예정** - 본 태스크 완료 후)
- **TASK_20251001_07**: 3-Container MVP 시스템 완전 검증 (📅 **계획됨** - 패턴 수정 후)

---

## 📚 참고 문서

### 기술 문서

- **dependency-injector 공식 문서**: Container 간 참조 패턴, @inject 데코레이터 사용법
- **TASK_20251001_04 분석 결과**: 3-Container 아키텍처 구조 및 발견된 DI 문제점
- **MVP 패턴 가이드**: Presenter-View 의존성 주입 체계

### 프로젝트 문서

- **.github/copilot-instructions.md**: DDD 아키텍처 및 3-Container 시스템 가이드라인
- **docs/COMPLETE_3_CONTAINER_DDD_ARCHITECTURE.md**: 3-Container 아키텍처 설계 원칙
- **docs/DEPENDENCY_INJECTION_ARCHITECTURE.md**: DI 패턴 및 구현 가이드

---

**문서 유형**: DI 패턴 표준화를 위한 종합 분석 태스크
**우선순위**: 🔥 최고 (시스템 오류 직접 원인 해결)
**예상 소요 시간**: 8시간 (체계적이고 완전한 분석)
**접근 방식**: 조사 → 분석 → 표준화 → 후속 태스크 설계

---

> **💡 핵심 메시지**: "코드 수정 전 완전한 분석으로 올바른 표준 패턴을 수립하자!"
>
> **🎯 성공 전략**: dependency-injector 공식 패턴 + 프로젝트 현황 분석 → 표준화 가이드라인!

---

**다음 에이전트 시작점**: Phase 1.1 dependency-injector 공식 문서 분석부터 시작하여 표준 패턴 정의 작업 진행
