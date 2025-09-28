# 📋 TASK_20250927_01: DI 시스템 구조적 완성

## 🎯 태스크 목표

- **주요 목표**: ApplicationContext DI 등록 시스템을 완성하여 핵심 서비스들의 정상 주입 보장
- **완료 기준**: API 키 설정 UI 정상 동작 및 모든 DI 서비스 등록 완료

## 🚨 Critical Issues 발견

### 문제 1: API 키 설정 UI 완전 불능 (🔴 Critical)

- **현상**: `self._api_key_service = None`으로 인한 API 설정 위젯 초기화 실패
- **원인**: `ApplicationContext._register_api_services()`가 완전히 빈 placeholder
- **영향**: 사용자가 API 키를 설정할 수 없어 시스템 사용 불가능

### 문제 2: 5개 핵심 서비스 DI 등록 누락 (🔴 Critical)

- **IApiKeyService**: 미등록 → API 설정 불가
- **IThemeService**: 미등록 → 테마 시스템 폴백
- **StyleManager**: 미등록 → 스타일 관리 폴백
- **NavigationBar**: 미등록 → 네비게이션 폴백
- **StatusBar**: 미등록 → 상태바 폴백

### 문제 3: DI Container 인터페이스 불일치 (🟡 Medium)

- **현상**: `ApplicationContext.is_registered` 메서드 부재
- **원인**: MainWindow가 `ApplicationContext` 받지만 `DIContainer` 메서드 호출
- **영향**: 모든 DI 등록 확인이 실패

---

## 🛠️ 구현 계획

### Phase 1: 즉시 복구 (1-2시간, 🔴 Critical)

#### 1.1 ApplicationContext.is_registered 메서드 추가

- [x] **현황 파악**: DIContainer에는 is_registered 존재, ApplicationContext에는 없음
- [ ] **메서드 구현**: ApplicationContext에 is_registered 위임 메서드 추가
- [ ] **검증**: MainWindow에서 정상 호출 확인

#### 1.2 IApiKeyService 긴급 등록

- [ ] **Repository 팩토리 구현**: DatabaseManager + SqliteSecureKeysRepository 생성
- [ ] **ApiKeyService 등록**: DI Container에 IApiKeyService 인스턴스 등록
- [ ] **API 설정 UI 복구**: SettingsScreen에서 정상 해결 확인

#### 1.3 DatabaseHealthService.check_overall_health 추가

- [ ] **메서드 구현**: get_current_status() 호출하는 래퍼 메서드 추가
- [ ] **StatusBar 연동**: DB 상태 체크 정상 동작 확인

### Phase 2: 완전 구현 (2-3시간, 🟡 Medium)

#### 2.1 _register_api_services() 완전 구현

- [ ] **Repository 팩토리**: 표준 Repository 생성 로직 구현
- [ ] **ApiKeyService 등록**: 표준 DI 등록 패턴 적용
- [ ] **에러 핸들링**: 등록 실패 시 적절한 폴백 처리

#### 2.2 _register_ui_services() 구현

- [ ] **IThemeService 등록**: 테마 시스템 DI 통합
- [ ] **StyleManager 등록**: 스타일 관리 시스템 DI 통합
- [ ] **UI 컴포넌트 등록**: NavigationBar, StatusBar DI 등록

#### 2.3 Repository 팩토리 패턴 통합

- [ ] **표준 팩토리 메서드**: 모든 Repository 생성을 위한 공통 패턴
- [ ] **DatabaseManager 통합**: 3-DB 분리 원칙 유지
- [ ] **Path Service 연동**: 기존 get_path_service() 활용

### Phase 3: 시스템 통합 및 검증 (1시간, 🟢 Low)

#### 3.1 통합 테스트

- [ ] **전체 UI 동작 확인**: `python run_desktop_ui.py` 실행 후 모든 기능 테스트
- [ ] **DI 해결 검증**: 모든 서비스가 정상 주입되는지 확인
- [ ] **에러 로그 제거**: ERROR 메시지 완전 제거 확인

#### 3.2 성능 및 안정성 검증

- [ ] **메모리 사용량**: DI Container 메모리 사용량 확인
- [ ] **초기화 시간**: 애플리케이션 시작 시간 측정
- [ ] **에러 복원력**: DI 실패 시 폴백 동작 확인

---

## 🧪 테스트 전략

### 기능 테스트

```python
# 1. API 설정 UI 테스트
python run_desktop_ui.py
# → 설정 → API 설정 탭 → API 키 입력 필드 정상 표시 확인

# 2. DI 해결 테스트
from upbit_auto_trading.infrastructure.dependency_injection.app_context import get_application_context
app_context = get_application_context()
api_service = app_context.resolve(IApiKeyService)
assert api_service is not None
```

### 회귀 테스트

```bash
# QAsync 마이그레이션 결과 유지 확인
python run_desktop_ui.py
# → WebSocket 연결 (Public + Private) 정상
# → 코인리스트, 호가창 동시 동작
# → 이벤트 루프 충돌 없음
```

---

## 🎯 성공 기준

### Critical Success Factors

- [ ] **API 키 설정 UI 완전 복구**: 사용자가 API 키 입력 및 저장 가능
- [ ] **모든 DI 서비스 정상 등록**: 5개 핵심 서비스 DI Container 등록 완료
- [ ] **ERROR 메시지 제로화**: `python run_desktop_ui.py` 실행 시 ERROR 없음

### Quality Metrics

- [ ] **WARNING 메시지 80% 감소**: 기존 11개 → 2개 이하
- [ ] **DI 해결 성공률 100%**: 모든 등록된 서비스 정상 해결
- [ ] **QAsync 마이그레이션 결과 유지**: 이벤트 루프 충돌 제로 유지

### User Experience

- [ ] **핵심 기능 완전 동작**: API 설정, 테마 변경, 상태 표시 모두 정상
- [ ] **초기화 시간 유지**: 애플리케이션 시작 시간 5초 이내
- [ ] **에러 복원력 확보**: DI 실패 시에도 기본 기능 동작

---

## 💡 작업 원칙

### DDD 아키텍처 준수

- **Domain 순수성 유지**: Repository 인터페이스 통한 Infrastructure 격리
- **의존성 역전 원칙**: 인터페이스 기반 DI 등록
- **계층 분리 엄수**: Presentation → Application → Domain ← Infrastructure

### 안전성 우선

- **점진적 구현**: Phase별로 단계적 적용 및 검증
- **폴백 메커니즘**: DI 실패 시 기존 방식으로 자동 폴백
- **테스트 병행**: 각 Phase 완료 후 즉시 동작 확인

### 성능 고려

- **지연 로딩**: 필요한 시점에만 서비스 인스턴스 생성
- **싱글톤 패턴**: 동일 서비스 재사용으로 메모리 최적화
- **에러 캐싱**: 실패한 DI 해결 결과 캐싱으로 성능 향상

---

## 🔧 구현 상세

### ApplicationContext.is_registered 구현

```python
def is_registered(self, service_type: Type) -> bool:
    """서비스 등록 여부 확인 (DIContainer 위임)"""
    if self._container:
        return self._container.is_registered(service_type)
    return False
```

### _register_api_services() 구현

```python
def _register_api_services(self) -> None:
    """API 서비스 등록"""
    try:
        # Repository 팩토리 패턴
        db_manager = self._create_database_manager()
        secure_keys_repo = SqliteSecureKeysRepository(db_manager)

        # ApiKeyService 생성 및 등록
        api_key_service = ApiKeyService(secure_keys_repo)
        self._container.register_instance(IApiKeyService, api_key_service)

        self._logger.info("✅ API 서비스 등록 완료")
    except Exception as e:
        self._logger.error(f"❌ API 서비스 등록 실패: {e}")
        # 폴백 처리는 UI Layer에서 담당
```

### DatabaseHealthService.check_overall_health 구현

```python
def check_overall_health(self) -> bool:
    """전체 DB 상태 확인 (StatusBar 호환성 메서드)"""
    return self.get_current_status()
```

---

## 📋 작업 상태

### 작업 진행 마커

- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

### 진행 상황

- **생성일**: 2025-09-27
- **현재 상태**: Phase 1 준비 중
- **담당**: GitHub Copilot + 개발팀
- **예상 소요**: 4-6시간 (3개 Phase)
- **우선순위**: 🔴 Critical (API 키 설정 불가능으로 인한 시스템 사용 불가)

### 의존 관계

- **선행 조건**: QAsync 마이그레이션 완료 (TASK_20250926_01 ✅)
- **후속 태스크**: TASK_20250926_02 (터미널 워닝 정리, 🟢 Low 우선순위)

---

**🚀 이 태스크는 시스템 핵심 기능 복구를 위한 Critical 태스크입니다!**
