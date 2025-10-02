# 📋 TASK_20250929_02: Settings Screen 연결 고리 복구 전략 수립

## 🎯 태스크 목표

- **주요 목표**: 진단 결과를 바탕으로 SettingsScreen ↔ SettingsViewFactory ↔ ApplicationContainer ↔ ApplicationServices 간 연결을 복구하는 구체적 전략 수립
- **완료 기준**: 최소 변경으로 최대 효과를 낼 수 있는 지점 식별 및 단계별 복구 계획 완성

## 📊 현재 상황 분석 (태스크 1 진단 결과)

### 🔍 식별된 5대 핵심 문제점

1. **MVP Container 연결 완전 단절** - ScreenManagerService에서 mvp_container 항상 None
2. **main_presenter 초기화 실패** - NoneType 에러의 정확한 원인 (첫 번째 스크린샷 에러)
3. **Factory 패턴 완전 미사용** - 완성된 SettingsViewFactory가 전혀 사용되지 않음
4. **ApplicationContainer 분리** - 완성된 서비스들이 실제로 연결되지 않음
5. **ApiKeyService 바인딩 누락** - ApplicationContainer에 get_api_key_service() 메서드 없음

### ✅ 사용 가능한 완성된 구조들

- ApplicationLayer 서비스 4개 (ApplicationLoggingService, ComponentLifecycleService 등)
- SettingsViewFactory + 6개 전용 Factory 완전 구현
- 28건 DI 패턴 모든 컴포넌트 적용 완료
- ApplicationContainer에 Settings 서비스들 완벽 바인딩

## 🔄 체계적 작업 절차

### 8단계 작업 절차

1. **📋 작업 항목 확인**: 5개 핵심 문제점별 복구 전략 수립
2. **🔍 검토 후 세부 작업 항목 생성**: 우선순위별 단계적 복구 계획
3. **🔄 작업중 마킹**: 각 전략 수립 항목을 [-] 상태로 변경
4. **⚙️ 작업 항목 진행**: 최소 변경 최대 효과 지점 분석
5. **✅ 작업 내용 확인**: 전략 타당성 및 실행 가능성 검증
6. **📝 상세 작업 내용 업데이트**: 구체적 실행 계획 상세 기록
7. **[x] 작업 완료 마킹**: 각 전략 수립 완료 표시
8. **⏳ 작업 승인 대기**: 다음 단계(실제 복구 실행) 진행 전 검토

## 🛠️ 복구 전략 수립 계획

### Strategy 1: MVP Container 연결 복구 (최우선)

- [-] ScreenManagerService dependencies에 MVP Container 전달 방법 분석
- [ ] ApplicationContainer에서 MVP Container 생성 및 바인딩 전략
- [ ] SettingsScreen 생성 시 올바른 MVP Container 주입 방법

### Strategy 2: ApplicationContainer 통합 복구

- [ ] ScreenManagerService가 ApplicationContainer를 사용하도록 변경 전략
- [ ] get_api_key_service() 메서드 ApplicationContainer에 추가 전략
- [ ] Infrastructure DI Container와 Application Container 연동 방법

### Strategy 3: Factory 패턴 활성화

- [ ] Settings Screen lazy loading 메서드들에 Factory 패턴 적용 전략
- [ ] 직접 생성 방식을 Factory 기반으로 변경하는 최소 변경 방법
- [ ] SettingsViewFactory 실제 사용 연결 지점 설계

### Strategy 4: Presenter 초기화 복구

- [ ] main_presenter 생성 성공을 위한 MVP Container 요구사항 분석
- [ ] load_initial_settings 메서드 실행 보장 전략
- [ ] 각 설정 탭별 Presenter 올바른 초기화 방법

### Strategy 5: 통합 검증 및 폴백 제거

- [ ] 모든 폴백 패턴 완전 제거 전략
- [ ] DI 실패 시 명확한 예외 발생 로직 설계
- [ ] 단계별 테스트 및 검증 방법론

## 🎯 복구 전략 상세 분석

### 🔥 Strategy 1: MVP Container 연결 복구 (Critical Path)

**문제 분석**:

```python
# ScreenManagerService._load_settings_screen() Line 191
mvp_container = dependencies.get('mvp_container')  # → 항상 None
```

**근본 원인**: ScreenManagerService 호출 지점에서 mvp_container를 전달하지 않음

**복구 전략 옵션**:

**옵션 A: ScreenManagerService에 ApplicationContainer 직접 통합** (권장)

- **장점**: 가장 직접적이고 확실한 해결
- **변경점**: ScreenManagerService 생성자에 ApplicationContainer 주입
- **영향도**: 낮음 (ScreenManagerService 생성 지점 1곳만 수정)

**옵션 B: dependencies 딕셔너리에 mvp_container 전달**

- **장점**: 기존 구조 최대 보존
- **변경점**: ScreenManagerService 호출 시 dependencies에 mvp_container 추가
- **영향도**: 중간 (여러 호출 지점 수정 필요)

**선택**: **옵션 A** - ApplicationContainer 직접 통합 (근본적 해결)

### 📋 Strategy 2: ApplicationContainer 통합 복구

**문제 분석**:

- ApplicationContainer에 완벽한 Settings 서비스들이 바인딩되어 있음
- 하지만 ScreenManagerService가 이를 전혀 사용하지 않음
- get_api_key_service() 메서드만 누락됨

**복구 전략**:

**단계 1**: ApplicationContainer에 get_api_key_service() 추가

```python
def get_api_key_service(self) -> 'ApiKeyService':
    if "api_key_service" not in self._services:
        # Infrastructure DI Container에서 가져오기
        from upbit_auto_trading.infrastructure.dependency_injection.container import Container
        container = Container()
        self._services["api_key_service"] = container.api_key_service()
    return self._services["api_key_service"]
```

**단계 2**: ScreenManagerService 생성자 변경

```python
class ScreenManagerService:
    def __init__(self, application_container: ApplicationServiceContainer):
        self._app_container = application_container
        # 모든 서비스를 ApplicationContainer에서 가져오도록 변경
```

### 🏭 Strategy 3: Factory 패턴 활성화

**문제 분석**:

```python
# 현재: 직접 생성 방식 (settings_screen.py)
self.api_key_manager = ApiSettingsView(parent=self, logging_service=self._logging_service)

# 목표: Factory 패턴 사용
self.api_key_manager = self._factory.create_api_settings_component(parent=self)
```

**복구 전략**:

**단계 1**: SettingsScreen에 Factory 주입

```python
class SettingsScreen(QWidget):
    def __init__(self, parent=None, settings_service=None, api_key_service=None,
                 logging_service=None, mvp_container=None, settings_factory=None):
        # settings_factory 매개변수 추가
        self._settings_factory = settings_factory
```

**단계 2**: lazy loading 메서드들을 Factory 기반으로 변경

```python
def _initialize_api_settings(self):
    if self.api_key_manager is not None:
        return

    if self._settings_factory:
        self.api_key_manager = self._settings_factory.create_api_settings_component(parent=self)
    else:
        raise ValueError("SettingsViewFactory가 주입되지 않았습니다")
```

## 🚀 실행 우선순위 및 순서

### Phase 1: 핵심 연결 복구 (1-2시간)

1. **ApplicationContainer에 get_api_key_service() 추가** (15분)
2. **ScreenManagerService에 ApplicationContainer 주입** (30분)
3. **MVP Container 생성 및 전달 로직 구현** (45분)

### Phase 2: Factory 패턴 활성화 (1시간)

1. **SettingsScreen에 Factory 주입 추가** (15분)
2. **lazy loading 메서드 Factory 기반으로 변경** (45분)

### Phase 3: 폴백 제거 및 검증 (30분)

1. **모든 폴백 패턴 완전 제거** (15분)
2. **통합 테스트 및 에러 검증** (15분)

## 💡 예상 효과 및 리스크 분석

### ✅ 예상 효과

- **즉시 해결**: 3개 Critical Errors 완전 해결
- **아키텍처 완성**: 완성된 28건 DI + Factory 패턴 실제 활용
- **확장성 확보**: 새로운 설정 탭 추가 시 자동으로 아키텍처 원칙 준수

### ⚠️ 주요 리스크

**리스크 1**: ScreenManagerService 변경으로 인한 다른 Screen들 영향

- **대응**: ApplicationContainer 주입을 선택적으로 처리 (기존 Screen들은 영향 없음)

**리스크 2**: Infrastructure와 Application Container 간 순환 참조

- **대응**: Infrastructure 서비스는 지연 로딩으로 가져오기

**리스크 3**: Factory 패턴 변경 시 기존 동작 중단

- **대응**: 단계별 적용으로 각 단계마다 검증

## 🎯 성공 기준

- ✅ 3개 Critical Errors 완전 해결 (NoneType, ApiKeyService, 각 설정 탭 에러)
- ✅ Factory 패턴 실제 사용 확인 (lazy loading에서 Factory 메서드 호출)
- ✅ ApplicationContainer 서비스들 실제 주입 확인
- ✅ 폴백 패턴 완전 제거 (try-except 폴백 로직 0개)
- ✅ 모든 설정 탭이 ERROR 없이 로드

## 🚀 즉시 시작할 작업

**Phase 1 단계 1**: ApplicationContainer에 get_api_key_service() 메서드 추가

- 파일: `upbit_auto_trading/application/container.py`
- 작업: Infrastructure DI Container에서 ApiKeyService 가져오는 메서드 구현

---

**다음 에이전트 시작점**: Phase 1 단계 1부터 실행. ApplicationContainer에 get_api_key_service() 메서드를 추가한 후, ScreenManagerService ApplicationContainer 주입, MVP Container 생성 순으로 진행하세요.
