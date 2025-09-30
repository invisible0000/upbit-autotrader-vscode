# 📋 TASK_20250929_04: 나머지 설정 Factory 일괄 수정

## 🎯 태스크 목표

### 주요 목표

**검증된 성공 패턴을 나머지 3개 설정 Factory에 일괄 적용하여 완전한 Factory 시스템 완성**

- TASK_01, 02, 03에서 확립된 성공 패턴을 Logging, Notification, Environment Profile Factory에 적용
- 6개 모든 설정 탭의 일관된 MVP 패턴 및 올바른 Container 사용 구현
- DDD + Clean Architecture + Factory 패턴의 완전한 통합 시스템 완성

### 완료 기준

- ✅ Logging Settings, Notification Settings, Environment Profile Settings Factory 모두 성공 패턴 적용
- ✅ 모든 Factory가 ApplicationServiceContainer를 통한 올바른 서비스 접근
- ✅ 6개 설정 탭의 Presenter가 `presentation/presenters/settings/`로 통합 이동
- ✅ MVP 패턴 3요소 완전 조립 및 일관된 구조 구현
- ✅ `python run_desktop_ui.py` → Settings → 모든 6개 탭에서 오류 없는 동작

---

## 📊 현재 상황 분석

### TASK_01, 02, 03 완료 후 예상 상태

#### ✅ 확립된 성공 패턴 (API Settings + Database Settings 기준)

- **올바른 Container 접근**: `get_application_container()` 사용
- **계층별 접근 규칙**: Presentation → Application → Infrastructure
- **MVP 구조 정리**: Presenter가 `presentation/presenters/settings/`에 위치
- **서비스 주입**: ApplicationServiceContainer를 통한 의존성 주입
- **MVP 조립**: Factory에서 View-Presenter-Model 완전 연결
- **오류 해결**: NoneType 및 서비스 누락 문제 해결 방법 확립

#### 🔧 나머지 3개 Factory 현재 상태

1. **LoggingSettingsComponentFactory**
   - 현재 위치: `ui/desktop/screens/settings/logging_settings/presenters/`
   - 예상 문제: Container 직접 접근, MVP 구조 혼란
   - 관련 서비스: LoggingService (이미 ApplicationServiceContainer에 존재)

2. **NotificationSettingsComponentFactory**
   - 현재 위치: `ui/desktop/screens/settings/notification_settings/presenters/`
   - 예상 문제: Container 접근, Notification 서비스 누락 가능성
   - 관련 서비스: NotificationService (확인 필요)

3. **EnvironmentProfileSettingsComponentFactory**
   - 현재 위치: `ui/desktop/screens/settings/environment_profile_settings/presenters/`
   - 예상 문제: 복잡한 Environment 관리 서비스 구조
   - 관련 서비스: EnvironmentService, ProfileService (확인 필요)

### 적용할 성공 패턴 템플릿

#### 검증된 Factory 패턴

```python
class {Setting}ComponentFactory(BaseComponentFactory):
    """성공 패턴 기반 {Setting} Factory"""

    def create_component_instance(self, parent, **kwargs):
        # 1️⃣ Application Service Container 접근 (TASK_01 패턴)
        app_container = self._get_application_container()

        # 2️⃣ Model 계층 - 서비스 주입
        {service}_service = app_container.get_{service}_service()
        logging_service = app_container.get_logging_service()

        # 3️⃣ View 계층 - UI 컴포넌트 생성
        view = {Setting}Component(parent)

        # 4️⃣ Presenter 계층 - 비즈니스 로직 연결
        from presentation.presenters.settings.{setting}_presenter import {Setting}Presenter
        presenter = {Setting}Presenter(
            view=view,
            {service}_service={service}_service,
            logging_service=logging_service
        )

        # 5️⃣ MVP 조립 - 상호 의존성 설정
        view.set_presenter(presenter)
        presenter.initialize()

        return view
```

---

## 🔄 체계적 작업 절차 (8단계)

### Phase 1: 현재 상태 분석 및 준비

#### 1.1 나머지 3개 Factory 현재 상태 파악

- [x] `LoggingSettingsComponentFactory` 현재 Container 접근 패턴 분석
  - ✅ 이미 `_get_application_container()` 사용 중 (올바른 패턴)
  - ⚠️ Presenter 위치: `ui/desktop/screens/settings/logging_management/presenters/` (이동 필요)
  - ✅ 서비스 접근: `get_logging_service()` 사용 중
- [x] `NotificationSettingsComponentFactory` 현재 구조 및 의존성 분석
  - ✅ 이미 `_get_application_container()` 사용 중 (올바른 패턴)
  - ⚠️ Presenter 위치: `ui/desktop/screens/settings/notification_settings/presenters/` (이동 필요)
  - ✅ 서비스 접근: `get_notification_service()` 사용 중 (확인 필요)
- [x] `EnvironmentProfileSettingsComponentFactory` 복잡도 및 서비스 요구사항 분석
  - ✅ 이미 `_get_application_container()` 사용 중 (올바른 패턴)
  - ⚠️ Presenter 위치: `ui/desktop/screens/settings/environment_profile/presenters/` (이동 필요)
  - ✅ 서비스 접근: `get_profile_service()` 사용 중 (확인 필요)
- [x] `EnvironmentProfileSettingsComponentFactory` 복잡도 및 서비스 요구사항 분석
  - ✅ LoggingManagementPresenter 주요 오류 해결 완료
  - ✅ NoneType 에러 및 DDD 계층 위반 문제 근본적 해결
  - ✅ ApplicationServiceContainer의 LoggingConfigManager 서비스 추가
  - ✅ 실시간 로그 모니터링 정상 동작 확인

#### 1.2 ApplicationServiceContainer 서비스 확인

- [x] `get_logging_service()` 존재 확인 (이미 있을 것으로 예상)
  - ✅ `get_logging_service()` 존재 및 정상 동작 중
- [x] `get_notification_service()` 존재 확인 및 필요시 추가
  - ✅ `get_notification_service()` 이미 존재하고 정상 동작 중
- [x] `get_environment_service()`, `get_profile_service()` 존재 확인 및 필요시 추가
  - ⚠️ `get_profile_service()` 없음 - ApplicationServiceContainer에 추가 필요
  - ✅ ProfileMetadataService 이미 존재 - 연결만 하면 됨

#### 1.3 백업 및 안전장치

- [x] 3개 Factory 관련 파일들 백업 생성
  - ✅ settings_view_factory.py 백업 완료
  - ✅ container.py 백업 완료 (profile_service 추가됨)
- [x] 현재 동작 상태 기준선 확인
  - ✅ python run_desktop_ui.py 정상 실행
  - ✅ Settings 화면 접근 정상
  - ✅ API Settings 탭 정상 동작 (TASK_02 완료 상태 확인)
- [x] 단계별 롤백 계획 수립
  - 📁 백업 파일들로 언제든 롤백 가능
  - 🔄 단계별 테스트로 문제 즉시 감지
  - 💾 Phase별로 작업 완료 후 즉시 검증

#### 1.4 LoggingManagement 서비스 의존성 문제 해결

**🔍 현재 상황 분석**

LoggingManagementPresenter에서 발생하는 에러들:

```
ERROR | upbit.LoggingManagementPresenter | ❌ 로깅 설정 로드 실패: 'NoneType' object has no attribute 'get_current_config'
ERROR | upbit.LoggingManagementPresenter | ❌ 로그 내용 새로고침 실패: 'MockBuffer' object has no attribute 'get_since'
ERROR | upbit.LoggingManagementPresenter | ❌ 콘솔 출력 갱신 실패: 'NoneType' object has no attribute 'get_recent_output'
```

**🚨 근본 원인 - 아키텍처 위반**

1. **DDD 계층 위반**: LoggingManagementPresenter가 Infrastructure Layer에 직접 접근
   - `get_live_log_buffer()`, `get_global_terminal_capturer()` 등 Infrastructure 함수 직접 호출
   - Presentation Layer가 Infrastructure Layer를 직접 의존하는 계층 위반

2. **서비스 의존성 누락**: ApplicationServiceContainer에서 필요한 서비스가 제대로 주입되지 않음
   - `logging_service.config_manager`가 None
   - LoggingManagementPresenter가 받는 logging_service가 ApplicationLoggingService이지만 config_manager 없음

3. **Factory 패턴 불일치**: LoggingSettingsComponentFactory가 성공 패턴을 따르지 않음
   - API Settings, Database Settings와 달리 올바른 서비스 주입 구조 미적용

**✅ 올바른 해결 방향**

**Phase 1.4.1: 서비스 계층 정리**

- [x] LoggingConfigurationService 생성 (Application Layer)
  - ✅ ApplicationServiceContainer에 `get_logging_config_service()` 추가
  - ✅ Infrastructure의 LoggingConfigManager 래핑 완료
  - ✅ DDD 계층 위반 해결 (Infrastructure → Application Layer 접근)
- [x] LoggingBufferService 생성 (Application Layer)
  - ✅ 기존 Infrastructure 로깅 버퍼 시스템 활용
  - ✅ Live log buffer 및 terminal capturer 정상 동작 확인
- [x] ApplicationServiceContainer에 위 서비스들 추가
  - ✅ `get_logging_config_service()` 메서드 추가 완료
  - ✅ TYPE_CHECKING import 추가로 타입 힌트 지원

**Phase 1.4.2: LoggingManagementPresenter 리팩터링**

- [x] Infrastructure Layer 직접 접근 제거
  - ✅ LoggingConfigManager를 ApplicationServiceContainer를 통해 접근
  - ✅ DDD 계층 위반 해결 (Presentation → Application → Infrastructure)
  - ✅ LogSyntaxHighlighter DDD 계층 위반 추가 해결
- [x] Application Layer 서비스만 의존하도록 수정
  - ✅ config_manager 접근 성공 확인 (로그에서 "Config Manager 접근 성공" 확인)
  - ✅ NoneType 에러 완전 해결
  - ✅ LogViewerWidget `name 'logger' is not defined` 에러 해결
- [x] MVP 패턴 준수: View-Presenter-Service 구조
  - ✅ Factory에서 올바른 서비스 주입 구조 완성
  - ✅ UI Layer → Application Layer → Infrastructure Layer 올바른 의존성 흐름 확립

**Phase 1.4.3: LoggingSettingsComponentFactory 수정**

- [x] API Settings, Database Settings와 동일한 패턴 적용
  - ✅ `_get_application_container()` 사용 (이미 올바른 패턴)
  - ✅ ApplicationServiceContainer를 통한 서비스 접근
- [x] ApplicationServiceContainer 통한 올바른 서비스 주입
  - ✅ LoggingConfigManager 서비스 정상 주입 확인
  - ✅ ApplicationLoggingService 정상 동작
- [x] MVP 조립 완성
  - ✅ View-Presenter 연결 성공
  - ✅ 실시간 로그 모니터링 시작 확인
  - ✅ 로그 구문 강조 기능 정상 작동 (DDD 계층 준수)

**🎯 예상 결과**

```python
# 올바른 의존성 구조
class LoggingManagementPresenter:
    def __init__(self, view, logging_config_service, logging_buffer_service, logging_service):
        self.logging_config_service = logging_config_service  # Application Layer
        self.logging_buffer_service = logging_buffer_service  # Application Layer
        self.logging_service = logging_service  # Infrastructure Logger
```

**⚠️ 중요**: 폴백/MockBuffer 사용은 문제 은폐이므로 금지. Golden Rules 준수하여 Fail Fast 원칙 적용

---

### Phase 2: MVP 구조 통합 정리

#### 2.1 Presenter 일괄 이동 (API, Database Settings 패턴 적용)

- [ ] `ui/desktop/screens/settings/logging_settings/presenters/logging_settings_presenter.py` → `presentation/presenters/settings/`
- [ ] `ui/desktop/screens/settings/notification_settings/presenters/notification_settings_presenter.py` → `presentation/presenters/settings/`
- [ ] `ui/desktop/screens/settings/environment_profile_settings/presenters/environment_profile_settings_presenter.py` → `presentation/presenters/settings/`

#### 2.2 기존 UI 폴더 정리

- [ ] UI 폴더에서 presenters 폴더 제거
- [ ] `presentation/presenters/settings/` 폴더에 6개 Presenter 모두 위치 확인
- [ ] Import 경로 일괄 수정

### Phase 3: ApplicationServiceContainer 서비스 추가

#### 3.1 Notification 서비스 확인 및 추가

- [ ] NotificationService 존재 여부 확인
- [ ] 필요시 ApplicationServiceContainer에 `get_notification_service()` 메서드 추가
- [ ] Infrastructure Layer에서 Notification 서비스 구현 확인

#### 3.2 Environment Profile 서비스 확인 및 추가

- [ ] EnvironmentService, ProfileService 존재 여부 확인
- [ ] 복잡한 Environment 관리 구조 분석
- [ ] 필요시 ApplicationServiceContainer에 관련 메서드 추가

### Phase 4: Factory별 순차 적용 (검증된 패턴 사용)

#### 4.1 LoggingSettingsComponentFactory 수정

- [ ] `get_global_container()` → `get_application_container()` 변경
- [ ] `app_container.get_logging_service()` 사용
- [ ] 이동된 Presenter와 MVP 조립
- [ ] API Settings, Database Settings와 동일한 구조 적용

#### 4.2 NotificationSettingsComponentFactory 수정

- [ ] Container 접근 패턴 변경
- [ ] Notification 서비스 정상 주입 확인
- [ ] MVP 패턴 완전 조립
- [ ] 알림 설정 기능 구현 (토글, 조건 설정 등)

#### 4.3 EnvironmentProfileSettingsComponentFactory 수정

- [ ] Container 접근 패턴 변경
- [ ] 복잡한 Environment/Profile 서비스 주입
- [ ] MVP 패턴 조립
- [ ] 환경 프로필 전환 기능 구현

### Phase 5: 개별 Factory 기능 구현

#### 5.1 Logging Settings 기능 완성

- [ ] 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR)
- [ ] 로그 파일 경로 설정
- [ ] 로그 포맷 설정
- [ ] 로그 로테이션 설정

#### 5.2 Notification Settings 기능 완성

- [ ] 알림 활성화/비활성화 토글
- [ ] 거래 완료 알림 설정
- [ ] 오류 발생 알림 설정
- [ ] 알림 방식 선택 (팝업, 사운드 등)

#### 5.3 Environment Profile Settings 기능 완성

- [ ] 환경 프로필 목록 표시 (Development, Production, Testing 등)
- [ ] 프로필 전환 기능
- [ ] 프로필별 설정 차이 표시
- [ ] 프로필 추가/삭제 기능

### Phase 6: 6개 Factory 통합 테스트

#### 6.1 개별 Factory 테스트

- [ ] API Settings Factory 정상 동작 재확인
- [ ] Database Settings Factory 정상 동작 재확인
- [ ] Logging Settings Factory 단독 테스트
- [ ] Notification Settings Factory 단독 테스트
- [ ] Environment Profile Settings Factory 단독 테스트

#### 6.2 Settings 화면 통합 테스트

- [ ] `python run_desktop_ui.py` 실행
- [ ] 6개 설정 탭 모두 접근 테스트
- [ ] 탭 간 전환 테스트
- [ ] 설정 저장/로드 통합 테스트

### Phase 7: 성능 최적화 및 사용자 경험 개선

#### 7.1 Factory 패턴 성능 최적화

- [ ] Lazy Loading 적용 확인
- [ ] 중복 서비스 생성 방지
- [ ] 메모리 사용량 최적화

#### 7.2 사용자 경험 통합 개선

- [ ] 일관된 UI/UX 패턴 적용
- [ ] 통일된 성공/실패 피드백 메시지
- [ ] 설정 변경 시 일관된 확인 다이얼로그

### Phase 8: 완성된 Factory 시스템 문서화

#### 8.1 성공 패턴 완전 정리

- [ ] 6개 Factory 공통 패턴 문서화
- [ ] Container 사용법 베스트 프랙티스 정리
- [ ] MVP 구조 가이드라인 완성

#### 8.2 TASK_E (통합 테스트) 준비

- [ ] 전체 시스템 성능 지표 수집 준비
- [ ] Factory 패턴 장점 실증 데이터 준비
- [ ] 현재 3-Container 구조 장점 문서화 준비

---

## 🛠️ 구체적 구현 계획

### LoggingSettingsComponentFactory 구현

#### Factory 수정

```python
class LoggingSettingsComponentFactory(BaseComponentFactory):
    """Logging Settings MVP Factory - 검증된 패턴 적용"""

    def create_component_instance(self, parent, **kwargs):
        # 1️⃣ Application Service Container 접근
        app_container = self._get_application_container()

        # 2️⃣ Model 계층 - 서비스 주입
        logging_service = app_container.get_logging_service()
        # configuration_service = app_container.get_configuration_service()  # 필요시

        # 3️⃣ View 계층 - UI 컴포넌트 생성
        view = LoggingSettingsComponent(parent)

        # 4️⃣ Presenter 계층 - 비즈니스 로직 연결
        from presentation.presenters.settings.logging_settings_presenter import LoggingSettingsPresenter
        presenter = LoggingSettingsPresenter(
            view=view,
            logging_service=logging_service
        )

        # 5️⃣ MVP 조립
        view.set_presenter(presenter)
        presenter.initialize()

        return view
```

#### Presenter 기능 구현

```python
class LoggingSettingsPresenter:
    """Logging Settings 비즈니스 로직 처리"""

    def __init__(self, view, logging_service):
        self.view = view
        self.logging_service = logging_service

    def initialize(self):
        """현재 로깅 설정 로드"""
        try:
            current_config = self.logging_service.get_current_config()
            self.view.display_logging_config(current_config)
        except Exception as e:
            self.view.show_error(f"로깅 설정 로드 실패: {e}")

    def update_log_level(self, level: str):
        """로그 레벨 업데이트"""
        try:
            self.logging_service.set_log_level(level)
            self.view.show_success(f"로그 레벨이 {level}로 변경되었습니다")
        except Exception as e:
            self.view.show_error(f"로그 레벨 변경 실패: {e}")

    def update_log_file_path(self, path: str):
        """로그 파일 경로 업데이트"""
        try:
            self.logging_service.set_log_file_path(path)
            self.view.show_success("로그 파일 경로가 업데이트되었습니다")
        except Exception as e:
            self.view.show_error(f"로그 파일 경로 설정 실패: {e}")
```

### NotificationSettingsComponentFactory 구현

#### 서비스 요구사항 확인

```python
# ApplicationServiceContainer에 추가 필요 (예상)
class ApplicationServiceContainer:
    def get_notification_service(self) -> NotificationService:
        """알림 서비스 반환"""
        if "notification_service" not in self._services:
            self._services["notification_service"] = self._create_notification_service()
        return self._services["notification_service"]
```

#### Factory 및 Presenter 구현

```python
class NotificationSettingsComponentFactory(BaseComponentFactory):
    def create_component_instance(self, parent, **kwargs):
        app_container = self._get_application_container()

        notification_service = app_container.get_notification_service()
        logging_service = app_container.get_logging_service()

        view = NotificationSettingsComponent(parent)

        from presentation.presenters.settings.notification_settings_presenter import NotificationSettingsPresenter
        presenter = NotificationSettingsPresenter(
            view=view,
            notification_service=notification_service,
            logging_service=logging_service
        )

        view.set_presenter(presenter)
        presenter.initialize()

        return view

class NotificationSettingsPresenter:
    def __init__(self, view, notification_service, logging_service):
        self.view = view
        self.notification_service = notification_service
        self.logging_service = logging_service

    def toggle_notification(self, notification_type: str, enabled: bool):
        """특정 알림 타입 활성화/비활성화"""
        try:
            self.notification_service.set_notification_enabled(notification_type, enabled)
            status = "활성화" if enabled else "비활성화"
            self.view.show_success(f"{notification_type} 알림이 {status}되었습니다")
        except Exception as e:
            self.view.show_error(f"알림 설정 변경 실패: {e}")
```

### EnvironmentProfileSettingsComponentFactory 구현

#### 복잡한 서비스 구조 처리

```python
class EnvironmentProfileSettingsComponentFactory(BaseComponentFactory):
    def create_component_instance(self, parent, **kwargs):
        app_container = self._get_application_container()

        # Environment 관련 서비스들 (복잡한 구조 예상)
        environment_service = app_container.get_environment_service()
        profile_service = app_container.get_profile_service()
        configuration_service = app_container.get_configuration_service()
        logging_service = app_container.get_logging_service()

        view = EnvironmentProfileSettingsComponent(parent)

        from presentation.presenters.settings.environment_profile_settings_presenter import EnvironmentProfileSettingsPresenter
        presenter = EnvironmentProfileSettingsPresenter(
            view=view,
            environment_service=environment_service,
            profile_service=profile_service,
            configuration_service=configuration_service,
            logging_service=logging_service
        )

        view.set_presenter(presenter)
        presenter.initialize()

        return view

class EnvironmentProfileSettingsPresenter:
    def switch_environment_profile(self, profile_name: str):
        """환경 프로필 전환"""
        try:
            self.view.show_loading("환경 프로필 전환 중...")

            # 프로필 전환 로직
            success = self.profile_service.switch_profile(profile_name)
            if success:
                self.environment_service.reload_configuration()
                self.view.show_success(f"{profile_name} 프로필로 전환되었습니다")
            else:
                self.view.show_error("프로필 전환에 실패했습니다")

        except Exception as e:
            self.view.show_error(f"프로필 전환 실패: {e}")
        finally:
            self.view.hide_loading()
```

---

## 🎯 성공 기준

### 기술적 검증

#### Factory 패턴 완성도

- ✅ **6개 Factory 일관성**: 모든 Factory가 동일한 패턴 사용
- ✅ **Container 접근**: ApplicationServiceContainer 통한 올바른 서비스 접근
- ✅ **MVP 조립**: View-Presenter-Model 완전 분리 및 조립
- ✅ **서비스 주입**: 각 Factory별 필요한 서비스 정상 주입

#### 아키텍처 품질

- ✅ **DDD 준수**: Domain 순수성 유지 및 계층별 접근 규칙
- ✅ **Clean Architecture**: 의존성 방향 완전 준수
- ✅ **SOLID 원칙**: 각 Factory 및 Presenter의 단일 책임
- ✅ **DRY 원칙**: 공통 패턴 재사용 및 중복 제거

### 동작 검증

#### 엔드투엔드 테스트

1. **앱 시작**: `python run_desktop_ui.py` 완전 오류 없는 실행
2. **Settings 접근**: Settings 메뉴 정상 로드
3. **6개 탭 접근**: API, Database, Logging, Notification, Environment Profile Settings 모두 정상 접근
4. **기능 동작**: 각 탭의 주요 기능 정상 동작
5. **설정 저장**: 모든 설정 변경사항 정상 저장
6. **앱 재시작**: 재시작 후 설정 정상 로드

#### 개별 기능 검증

##### API Settings (TASK_02 완료)

- ✅ API 키 저장/로드/검증

##### Database Settings (TASK_03 완료)

- ✅ 데이터베이스 경로 설정/테스트

##### Logging Settings (신규)

- ✅ 로그 레벨 변경 (DEBUG → INFO → WARNING → ERROR)
- ✅ 로그 파일 경로 설정
- ✅ 로그 포맷 및 로테이션 설정

##### Notification Settings (신규)

- ✅ 거래 완료 알림 활성화/비활성화
- ✅ 오류 발생 알림 설정
- ✅ 알림 방식 선택 및 테스트

##### Environment Profile Settings (신규)

- ✅ 프로필 목록 표시 (Development, Production, Testing)
- ✅ 프로필 전환 기능
- ✅ 프로필별 설정 차이 표시

### 성능 및 사용자 경험

#### 성능 지표

- ✅ **초기화 시간**: 각 Factory 초기화 0.5초 이내
- ✅ **메모리 사용**: Lazy Loading으로 불필요한 메모리 사용 최소화
- ✅ **반응성**: UI 상호작용 즉시 반응 (100ms 이내)

#### 사용자 경험

- ✅ **일관성**: 모든 설정 탭의 동일한 UI/UX 패턴
- ✅ **피드백**: 명확하고 일관된 성공/실패 메시지
- ✅ **안정성**: 오류 발생시 안전한 처리 및 복구

---

## 💡 작업 시 주의사항

### 단계별 안전 적용

#### 순차 적용 원칙

1. **한 번에 하나씩**: LoggingSettings → NotificationSettings → EnvironmentProfileSettings 순서
2. **즉시 테스트**: 각 Factory 수정 후 개별 동작 확인
3. **문제 발생시**: 즉시 이전 Factory 패턴 적용 및 롤백
4. **성공 검증**: 정상 동작 확인 후 다음 Factory 진행

#### 백업 및 롤백

- **필수 백업**: 각 Factory 수정 전 관련 파일 백업
- **단계별 커밋**: 각 Factory 완료 후 Git 커밋
- **롤백 계획**: 문제 발생시 이전 단계로 즉시 복원

### 서비스 의존성 관리

#### ApplicationServiceContainer 확장

```python
# 서비스 추가시 안전한 패턴
def get_notification_service(self) -> NotificationService:
    """알림 서비스 반환 - 안전한 초기화"""
    if "notification_service" not in self._services:
        try:
            self._services["notification_service"] = self._create_notification_service()
        except Exception as e:
            logger.error(f"NotificationService 초기화 실패: {e}")
            # Fallback 서비스 또는 Mock 서비스 반환
            self._services["notification_service"] = MockNotificationService()

    return self._services["notification_service"]
```

#### 서비스 누락 대응

- **점진적 확인**: 각 서비스의 존재 여부 단계별 확인
- **Fallback 서비스**: 서비스가 없는 경우 Mock 서비스 임시 사용
- **명확한 오류**: 서비스 누락시 명확한 오류 메시지 및 해결 방안 제시

### MVP 구조 일관성

#### Presenter 이동 표준화

```powershell
# 표준 이동 명령어 (각 Factory별)
Move-Item "ui\desktop\screens\settings\{setting}_settings\presenters\{setting}_settings_presenter.py" "presentation\presenters\settings\"

# 기존 UI 폴더 정리
Remove-Item "ui\desktop\screens\settings\{setting}_settings\presenters\" -Recurse
```

#### Import 경로 통일

```python
# 모든 Factory에서 동일한 Import 패턴 사용
from presentation.presenters.settings.{setting}_settings_presenter import {Setting}SettingsPresenter
```

---

## 🚀 즉시 시작할 작업

### 1단계: 현재 상태 분석

```powershell
# 나머지 3개 Factory 현재 Container 접근 패턴 확인
Get-Content upbit_auto_trading\application\factories\settings_view_factory.py | Select-String "LoggingSettingsComponentFactory\|NotificationSettingsComponentFactory\|EnvironmentProfileSettingsComponentFactory" -A 10 -B 2

# ApplicationServiceContainer에서 사용 가능한 서비스 확인
Get-Content upbit_auto_trading\application\container.py | Select-String "def get_.*service" -A 1
```

### 2단계: MVP 구조 통합 정리

```powershell
# Presenter 일괄 이동 (한 번에 하나씩 확인하며 진행)
# 1. Logging Settings
if (Test-Path "ui\desktop\screens\settings\logging_settings\presenters\logging_settings_presenter.py") {
    Move-Item "ui\desktop\screens\settings\logging_settings\presenters\logging_settings_presenter.py" "presentation\presenters\settings\"
    Remove-Item "ui\desktop\screens\settings\logging_settings\presenters\" -Recurse -Force
    Write-Host "✅ Logging Settings Presenter 이동 완료"
}

# 2. Notification Settings
if (Test-Path "ui\desktop\screens\settings\notification_settings\presenters\notification_settings_presenter.py") {
    Move-Item "ui\desktop\screens\settings\notification_settings\presenters\notification_settings_presenter.py" "presentation\presenters\settings\"
    Remove-Item "ui\desktop\screens\settings\notification_settings\presenters\" -Recurse -Force
    Write-Host "✅ Notification Settings Presenter 이동 완료"
}

# 3. Environment Profile Settings
if (Test-Path "ui\desktop\screens\settings\environment_profile_settings\presenters\environment_profile_settings_presenter.py") {
    Move-Item "ui\desktop\screens\settings\environment_profile_settings\presenters\environment_profile_settings_presenter.py" "presentation\presenters\settings\"
    Remove-Item "ui\desktop\screens\settings\environment_profile_settings\presenters\" -Recurse -Force
    Write-Host "✅ Environment Profile Settings Presenter 이동 완료"
}
```

### 3단계: ApplicationServiceContainer 서비스 확인 및 추가

```powershell
# 필요한 서비스들이 있는지 확인
Get-Content upbit_auto_trading\application\container.py | Select-String "notification\|environment\|profile" -i
```

### 4단계: Factory별 순차 적용

1. **LoggingSettingsComponentFactory** (가장 단순할 것으로 예상)
2. **NotificationSettingsComponentFactory** (중간 복잡도)
3. **EnvironmentProfileSettingsComponentFactory** (가장 복잡할 것으로 예상)

### 5단계: 각 수정 후 즉시 테스트

```powershell
# 각 Factory 수정 후 즉시 테스트
python run_desktop_ui.py

# 특정 Factory 단독 테스트
python -c "
from upbit_auto_trading.application.factories.settings_view_factory import LoggingSettingsComponentFactory
factory = LoggingSettingsComponentFactory()
print('LoggingSettings Factory 초기화 성공')
"
```

---

## 🔗 연관 태스크

### 선행 태스크

- **TASK_01**: 올바른 Container 사용법 적용 (필수 완료)
- **TASK_02**: API Settings Factory MVP 완성 (필수 완료 - 성공 패턴 제공)
- **TASK_03**: Database Settings Factory 수정 (필수 완료 - 패턴 검증)

### 후속 태스크

- **TASK_E**: 통합 테스트 및 성능 검증 (이 태스크 완료 후)

### 종속성

- **TASK_01, 02, 03 의존**: 확립된 성공 패턴 및 문제 해결 노하우 적용 필수
- **패턴 확산**: 검증된 패턴을 3개 Factory에 일괄 적용

### 전파 효과

#### 완성된 Factory 시스템

- **6개 Factory 통합**: 모든 설정 Factory가 일관된 패턴으로 완성
- **MVP 아키텍처**: 완전한 MVP 분리 및 일관된 구조 확립
- **Container 사용법**: 올바른 ApplicationServiceContainer 사용 정착
- **DDD + Clean Architecture**: 완벽한 계층별 접근 및 의존성 관리

#### 시스템 안정성

- **오류 방지**: NoneType 등 공통 오류 패턴 완전 해결
- **확장성**: 새로운 설정 Factory 추가시 참고할 완벽한 템플릿
- **유지보수성**: 일관된 구조로 인한 코드 이해 및 수정 용이성

---

## 📚 참고 자료

### 성공 패턴 참조

- **TASK_02 결과물**: API Settings Factory 완성된 패턴
- **TASK_03 결과물**: Database Settings Factory 완성된 패턴
- **`presentation/presenters/settings/`**: 이동된 Presenter들 구조 참고

### 아키텍처 문서

- **`MVP_QUICK_GUIDE.md`**: MVP 패턴 구현 가이드
- **`DEPENDENCY_INJECTION_QUICK_GUIDE.md`**: DI 패턴 적용 방법
- **`CURRENT_ARCHITECTURE_ADVANTAGES.md`**: 현재 구조의 올바른 사용법

### ApplicationServiceContainer 확장

- **`upbit_auto_trading/application/container.py`**: 서비스 추가 방법
- **Infrastructure Services**: 각종 Infrastructure Layer 서비스들
- **Service Interface**: 서비스 인터페이스 및 구현 패턴

---

## 🎉 예상 결과

### 완성된 6개 Factory 시스템

#### 기술적 성과

- ✅ **Factory Pattern 완성**: 6개 모든 설정 Factory가 일관된 패턴 구현
- ✅ **MVP Architecture**: View-Presenter-Model 완전 분리 및 일관된 구조
- ✅ **DI Pattern**: ApplicationServiceContainer 기반 완벽한 의존성 주입
- ✅ **Clean Architecture**: 계층별 접근 규칙 100% 준수

#### 사용자 경험

- ✅ **완전한 설정 관리**: 6개 모든 설정 탭 완벽 동작
- ✅ **일관된 UI/UX**: 통일된 인터페이스 및 상호작용 패턴
- ✅ **안정성**: 오류 없는 설정 저장/로드 및 기능 동작
- ✅ **성능**: 빠른 초기화 및 즉각적인 반응성

#### 개발자 가치

- ✅ **패턴 템플릿**: 새로운 Factory 추가시 참고할 완벽한 패턴
- ✅ **확장성**: 플러그인 아키텍처 지원 및 쉬운 기능 확장
- ✅ **유지보수성**: 일관된 구조로 인한 코드 이해 및 수정 용이성
- ✅ **테스트 용이성**: Mock을 통한 단위 테스트 완벽 지원

### 시스템 아키텍처 완성도

#### DDD + MVP + Factory + DI 통합

```text
✅ 완성된 아키텍처 스택

Presentation Layer (MVP)
├── 📁 presentation/presenters/settings/
│   ├── 📄 api_settings_presenter.py           ✅ TASK_02
│   ├── 📄 database_settings_presenter.py      ✅ TASK_03
│   ├── 📄 logging_settings_presenter.py       ⭐ TASK_04
│   ├── 📄 notification_settings_presenter.py  ⭐ TASK_04
│   └── 📄 environment_profile_settings_presenter.py ⭐ TASK_04
├── 🏭 factories/settings_view_factory.py      ✅ 6개 Factory 완성
└── 🖼️ ui/desktop/screens/settings/            ✅ Pure View Layer

Application Layer (Business Logic)
├── 📦 container.py (ApplicationServiceContainer) ✅ 올바른 사용
└── 🔧 services/ (Business Services)           ✅ 완전 주입

Infrastructure Layer (External Resources)
├── 📦 container.py (ApplicationContainer)      ✅ 적절한 격리
└── 🔌 services/ (Infrastructure Services)     ✅ 완전 구현
```

---

**다음 에이전트 시작점**:

1. TASK_01, 02, 03 완료 상태 확인
2. 나머지 3개 Factory 현재 상태 분석
3. ApplicationServiceContainer 필요한 서비스 확인 및 추가
4. Presenter 일괄 이동 (`presentation/presenters/settings/`)
5. LoggingSettings → NotificationSettings → EnvironmentProfileSettings 순차 적용
6. 각 Factory 수정 후 즉시 개별 테스트
7. 6개 Factory 완성 후 통합 테스트
8. TASK_E (통합 테스트 및 성능 검증) 준비

---

**문서 유형**: 확산 적용 태스크
**우선순위**: 📈 확장 적용 (검증된 패턴을 나머지 Factory에 일괄 적용)
**예상 소요 시간**: 2-3시간
**성공 기준**: 6개 모든 설정 Factory 완성 + 일관된 MVP 패턴 구현 + 완벽한 DDD + Clean Architecture 시스템 완성
