# 📋 Factory 마이그레이션 가이드라인
>
> Database Settings & UI Settings Factory 적용 가이드

## 🎯 목적

API Settings Factory에서 검증된 MVP 패턴을 Database Settings Factory와 UI Settings Factory에 적용하는 구체적인 단계별 가이드.

## 📊 적용 우선순위

### 1순위: Database Settings Factory

**이유**: Repository 패턴 활용으로 트랜잭션 커밋 검증 가능

### 2순위: UI Settings Factory

**이유**: 상대적으로 단순한 구조, 빠른 적용 가능

### 3순위: 나머지 Factory들

**이유**: 패턴 확립 후 일괄 적용

## 🔧 Database Settings Factory 마이그레이션 (TASK_C)

### Phase 1: 현재 상태 분석

```powershell
# 현재 DatabaseSettingsComponentFactory 구조 파악
Get-Content upbit_auto_trading\application\factories\settings_view_factory.py -TotalCount 300 | Select-String "DatabaseSettingsComponentFactory" -A 20 -B 5

# Database 관련 서비스들 확인
Get-Content upbit_auto_trading\application\container.py | Select-String "database" -i
```

### Phase 2: 필요한 서비스 식별

**예상 서비스 의존성**:

- `database_service` (필수): DB 연결 관리
- `logging_service` (필수): Infrastructure 로깅
- `validation_service` (권장): 설정 검증
- `lifecycle_service` (필수): 컴포넌트 생명주기

### Phase 3: MVP 구조 적용

#### 3.1 Factory 수정

```python
class DatabaseSettingsComponentFactory(StandardMvpFactory):
    def get_component_type(self) -> str:
        return "database_settings"

    def _get_required_services(self, app_container) -> Dict[str, Any]:
        return CommonServicePatterns.get_database_services(app_container)

    def _create_view(self, parent: Optional[QWidget], services: Dict[str, Any]) -> QWidget:
        from upbit_auto_trading.ui.desktop.screens.settings.database_settings.views.database_settings_view import DatabaseSettingsView

        return DatabaseSettingsView(
            parent=parent,
            logging_service=services['logging_service']
        )

    def _create_presenter(self, view: QWidget, services: Dict[str, Any]) -> Any:
        from presentation.presenters.settings.database_settings_presenter import DatabaseSettingsPresenter

        return DatabaseSettingsPresenter(
            view=view,
            database_service=services['database_service'],
            logging_service=services['logging_service']
        )
```

#### 3.2 Presenter 이동 및 생성

```powershell
# Presenter 디렉토리 생성 (필요한 경우)
New-Item -ItemType Directory -Path "presentation\presenters\settings" -Force

# 기존 Presenter가 있다면 이동
# Move-Item "ui\desktop\screens\settings\database_settings\presenters\*" "presentation\presenters\settings\"
```

#### 3.3 Presenter 구현

```python
# presentation/presenters/settings/database_settings_presenter.py
class DatabaseSettingsPresenter(StandardSettingsPresenter):
    def get_required_services(self) -> list:
        return ['database_service']

    def _fetch_data(self) -> Dict[str, Any]:
        database_service = self.services['database_service']
        return {
            'connection_string': database_service.get_connection_string(),
            'max_connections': database_service.get_max_connections(),
            # ... 기타 DB 설정들
        }

    def _get_default_data(self) -> Dict[str, Any]:
        return {
            'connection_string': 'sqlite:///data/default.db',
            'max_connections': 10,
            'timeout': 30
        }

    def _validate_data(self, **data) -> bool:
        # DB 연결 문자열 검증
        connection_string = data.get('connection_string', '')
        if not connection_string:
            return False

        # 추가 검증 로직
        return True

    def _execute_save(self, **data) -> bool:
        database_service = self.services['database_service']

        # TransactionMixin 활용
        return self.execute_with_commit(
            database_service.save_configuration,
            **data
        )
```

### Phase 4: 트랜잭션 커밋 검증

**중요**: API Settings Factory에서 발견된 트랜잭션 커밋 이슈를 Database Settings에서도 검증

```python
# Repository에서 명시적 커밋 확인
def save_database_settings(self, **settings):
    # 데이터 저장
    result = self.repository.save(**settings)

    # 명시적 커밋 (필수!)
    self.repository.connection.commit()

    return result
```

## 🎨 UI Settings Factory 마이그레이션 (TASK_D)

### Phase 1: 현재 상태 분석

```powershell
# UI Settings 구조 파악
Get-Content upbit_auto_trading\application\factories\settings_view_factory.py | Select-String "UiSettingsComponentFactory" -A 20 -B 5

# UI 관련 서비스들 확인
Get-Content upbit_auto_trading\application\container.py | Select-String "ui\|theme\|style" -i
```

### Phase 2: 필요한 서비스 식별

**예상 서비스 의존성**:

- `settings_service` (필수): UI 설정 관리
- `logging_service` (필수): Infrastructure 로깅
- `theme_service` (옵션): 테마 관리
- `validation_service` (권장): 설정 검증

### Phase 3: MVP 구조 적용

#### 3.1 Factory 수정

```python
class UiSettingsComponentFactory(StandardMvpFactory):
    def get_component_type(self) -> str:
        return "ui_settings"

    def _get_required_services(self, app_container) -> Dict[str, Any]:
        return CommonServicePatterns.get_ui_services(app_container)

    def _create_view(self, parent: Optional[QWidget], services: Dict[str, Any]) -> QWidget:
        from upbit_auto_trading.ui.desktop.screens.settings.ui_settings.views.ui_settings_view import UiSettingsView

        return UiSettingsView(
            parent=parent,
            logging_service=services['logging_service']
        )

    def _create_presenter(self, view: QWidget, services: Dict[str, Any]) -> Any:
        from presentation.presenters.settings.ui_settings_presenter import UiSettingsPresenter

        return UiSettingsPresenter(
            view=view,
            settings_service=services['settings_service'],
            logging_service=services['logging_service']
        )
```

#### 3.2 Presenter 구현

```python
# presentation/presenters/settings/ui_settings_presenter.py
class UiSettingsPresenter(StandardSettingsPresenter, ValidationMixin):
    def get_required_services(self) -> list:
        return ['settings_service']

    def _fetch_data(self) -> Dict[str, Any]:
        settings_service = self.services['settings_service']
        return {
            'theme': settings_service.get_theme(),
            'font_size': settings_service.get_font_size(),
            'language': settings_service.get_language(),
            # ... 기타 UI 설정들
        }

    def _get_default_data(self) -> Dict[str, Any]:
        return {
            'theme': 'dark',
            'font_size': 12,
            'language': 'ko_KR',
            'auto_save': True
        }

    def _validate_data(self, **data) -> bool:
        # ValidationMixin 활용
        required_fields = ['theme', 'font_size', 'language']
        is_valid, message = self.validate_required_fields(data, required_fields)

        if not is_valid:
            self.logger.error(f"UI 설정 검증 실패: {message}")
            return False

        # 추가 검증 (범위 체크 등)
        font_size = data.get('font_size', 0)
        if not (8 <= font_size <= 24):
            self.logger.error("폰트 크기는 8-24 범위여야 합니다")
            return False

        return True

    def _execute_save(self, **data) -> bool:
        settings_service = self.services['settings_service']
        return settings_service.save_ui_settings(**data)
```

## 📋 공통 적용 체크리스트

### 🔧 마이그레이션 준비

- [ ] 현재 Factory 파일 백업
- [ ] ApplicationServiceContainer에서 필요한 서비스 메서드 확인
- [ ] 기존 View/Presenter 파일 위치 파악

### 🏗️ 구조 변경

- [ ] `StandardMvpFactory` 상속으로 변경
- [ ] `CommonServicePatterns` 활용
- [ ] Presenter를 `presentation/presenters/settings/` 로 이동
- [ ] `StandardSettingsPresenter` 상속

### 🧪 검증 및 테스트

- [ ] `python run_desktop_ui.py` 실행 테스트
- [ ] Settings 탭 접근 및 기능 동작 확인
- [ ] 데이터 저장/로드 완전 동작 검증
- [ ] Repository 사용 시 트랜잭션 커밋 확인

### 📊 로깅 및 모니터링

- [ ] Infrastructure 로깅 시스템 적용
- [ ] 초기화/성공/실패 상황 적절한 로그 기록
- [ ] `print()` 사용 제거

## ⚠️ 주의사항

### 트랜잭션 커밋

**API Settings Factory에서 발견된 패턴**: Repository 사용 시 반드시 명시적 `conn.commit()` 호출

### Import 경로

**올바른 경로**: `from presentation.presenters.settings.{component_name}_presenter import {ComponentName}Presenter`

### 서비스 의존성

**필수 검증**: ApplicationServiceContainer에서 필요한 서비스가 구현되어 있는지 확인

### MVP 조립

**필수 패턴**: `view.set_presenter(presenter)` 호출로 MVP 연결 완료

## 🚀 실행 순서

1. **TASK_C: Database Settings Factory**
   - Repository 패턴 + 트랜잭션 검증에 중점
   - 데이터 무결성 확보가 핵심

2. **TASK_D: UI Settings Factory**
   - 상대적으로 단순한 구조로 빠른 적용
   - 사용자 경험 개선에 중점

3. **검증 및 문서화**
   - 양쪽 Factory 모두 성공 후 패턴 문서 업데이트
   - 다른 Factory 적용을 위한 가이드 보완

각 Factory별로 이 가이드라인을 따르면 API Settings Factory와 동일한 품질의 MVP 패턴 구현이 가능합니다.
