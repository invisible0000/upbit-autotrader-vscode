# 📋 MVP Factory Base Patterns
>
> API Settings Factory 성공 사례 기반 재사용 가능한 패턴 라이브러리

## 🎯 목적

TASK_20250929_02에서 검증된 API Settings Factory의 성공 패턴을 분석하여, 다른 Settings Factory 구현 시 재사용할 수 있는 Base 패턴들을 추출.

## 🏗️ Base Factory 패턴

### 1. StandardMvpFactory 추상 클래스

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import QWidget

class StandardMvpFactory(BaseComponentFactory):
    """
    표준 MVP Factory 추상 클래스
    - API Settings Factory에서 검증된 패턴을 기반으로 함
    - 모든 Settings Factory의 공통 베이스 클래스
    """

    def create_component_instance(self, parent: Optional[QWidget], **kwargs) -> QWidget:
        """표준 MVP 생성 패턴 - Template Method Pattern 적용"""

        # 1️⃣ Container & Services - 공통 패턴
        app_container = self._get_application_container()
        services = self._get_required_services(app_container)

        # 2️⃣ View 생성 - 하위 클래스 구현
        view = self._create_view(parent, services)

        # 3️⃣ Presenter 생성 - 하위 클래스 구현
        presenter = self._create_presenter(view, services)

        # 4️⃣ MVP 조립 - 공통 패턴
        self._assemble_mvp(view, presenter)

        # 5️⃣ 초기화 - 하위 클래스 구현
        self._initialize_component(view, presenter, services)

        self._logger.info(f"✅ {self.get_component_type()} MVP 컴포넌트 완전 조립 완료")
        return view

    @abstractmethod
    def _get_required_services(self, app_container) -> Dict[str, Any]:
        """필요한 서비스들 조회 - 하위 클래스에서 구현"""
        pass

    @abstractmethod
    def _create_view(self, parent: Optional[QWidget], services: Dict[str, Any]) -> QWidget:
        """View 생성 - 하위 클래스에서 구현"""
        pass

    @abstractmethod
    def _create_presenter(self, view: QWidget, services: Dict[str, Any]) -> Any:
        """Presenter 생성 - 하위 클래스에서 구현"""
        pass

    def _assemble_mvp(self, view: QWidget, presenter: Any):
        """MVP 조립 - 공통 패턴"""
        try:
            view.set_presenter(presenter)
            self._logger.info("✅ MVP 패턴 연결 완료")
        except Exception as e:
            error_msg = f"❌ MVP 조립 실패: {e}"
            self._logger.error(error_msg)
            raise RuntimeError(f"Factory 실패: {error_msg}")

    def _initialize_component(self, view: QWidget, presenter: Any, services: Dict[str, Any]):
        """컴포넌트 초기화 - 하위 클래스에서 오버라이드 가능"""
        try:
            # 기본 초기화 로직
            if hasattr(presenter, 'load_initial_data'):
                initial_data = presenter.load_initial_data()
                if hasattr(view, 'update_ui_with_data') and initial_data:
                    view.update_ui_with_data(initial_data)

            if hasattr(view, '_update_button_states'):
                view._update_button_states()

        except Exception as e:
            self._logger.warning(f"⚠️ 초기화 중 경고: {e}")
```

### 2. Common Service Patterns

```python
class CommonServicePatterns:
    """자주 사용되는 서비스 조합 패턴"""

    @staticmethod
    def get_basic_services(app_container) -> Dict[str, Any]:
        """기본 서비스 조합 (모든 Factory에서 필요)"""
        return {
            'logging_service': app_container.get_logging_service(),
            'validation_service': app_container.get_settings_validation_service(),
            'lifecycle_service': app_container.get_component_lifecycle_service()
        }

    @staticmethod
    def get_api_services(app_container) -> Dict[str, Any]:
        """API 관련 서비스 조합"""
        services = CommonServicePatterns.get_basic_services(app_container)
        services.update({
            'api_key_service': app_container.get_api_key_service()
        })
        return services

    @staticmethod
    def get_database_services(app_container) -> Dict[str, Any]:
        """Database 관련 서비스 조합"""
        services = CommonServicePatterns.get_basic_services(app_container)
        services.update({
            'database_service': app_container.get_database_service()
        })
        return services

    @staticmethod
    def get_ui_services(app_container) -> Dict[str, Any]:
        """UI 관련 서비스 조합"""
        services = CommonServicePatterns.get_basic_services(app_container)
        services.update({
            'settings_service': app_container.get_settings_service()
        })
        return services
```

## 🧠 Base Presenter Patterns

### 1. StandardSettingsPresenter 추상 클래스

```python
class StandardSettingsPresenter(ABC):
    """표준 Settings Presenter 베이스 클래스"""

    def __init__(self, view, logging_service, **services):
        self.view = view
        self.logger = logging_service
        self.services = services

        # 공통 초기화 로직
        self._validate_dependencies()
        self._log_initialization()

    def _validate_dependencies(self):
        """의존성 검증 - 공통 패턴"""
        required_services = self.get_required_services()
        for service_name in required_services:
            if service_name not in self.services or self.services[service_name] is None:
                self.logger.warning(f"⚠️ {service_name}이 None으로 전달됨")

    def _log_initialization(self):
        """초기화 로깅 - 공통 패턴"""
        component_type = self.__class__.__name__.replace('Presenter', '')
        self.logger.info(f"✅ {component_type} 프레젠터 초기화 완료")

    @abstractmethod
    def get_required_services(self) -> list:
        """필요한 서비스 목록 반환"""
        pass

    def load_initial_data(self) -> Dict[str, Any]:
        """초기 데이터 로드 - Template Method Pattern"""
        try:
            data = self._fetch_data()
            if not data:
                self.logger.debug("저장된 데이터가 없습니다")
                return self._get_default_data()

            self.logger.debug(f"데이터 로드 완료")
            return data

        except Exception as e:
            self.logger.error(f"데이터 로드 중 오류: {e}")
            return self._get_default_data()

    @abstractmethod
    def _fetch_data(self) -> Dict[str, Any]:
        """실제 데이터 조회 - 하위 클래스 구현"""
        pass

    @abstractmethod
    def _get_default_data(self) -> Dict[str, Any]:
        """기본 데이터 - 하위 클래스 구현"""
        pass

    def save_data(self, **data) -> Tuple[bool, str]:
        """데이터 저장 - Template Method Pattern"""
        try:
            # 1. 검증
            if not self._validate_data(**data):
                return False, "입력 데이터 검증에 실패했습니다."

            # 2. 저장 실행
            success = self._execute_save(**data)

            if success:
                # 3. 성공 피드백
                self._handle_save_success()
                return True, "저장 완료"
            else:
                return False, "저장 중 오류가 발생했습니다"

        except Exception as e:
            self.logger.error(f"데이터 저장 중 오류: {e}")
            return False, f"저장 중 오류가 발생했습니다: {str(e)}"

    @abstractmethod
    def _validate_data(self, **data) -> bool:
        """데이터 검증 - 하위 클래스 구현"""
        pass

    @abstractmethod
    def _execute_save(self, **data) -> bool:
        """저장 실행 - 하위 클래스 구현"""
        pass

    def _handle_save_success(self):
        """저장 성공 처리 - 공통 패턴"""
        if hasattr(self.view, 'show_success'):
            self.view.show_success("데이터가 성공적으로 저장되었습니다")

        component_type = self.__class__.__name__.replace('Presenter', '')
        self.logger.info(f"{component_type} 데이터 저장 완료")
```

## 🎨 Base View Patterns

### 1. StandardSettingsView 추상 클래스

```python
class StandardSettingsView(QWidget):
    """표준 Settings View 베이스 클래스"""

    def __init__(self, parent=None, logging_service=None, **kwargs):
        super().__init__(parent)

        # 공통 초기화
        self._setup_logging(logging_service)
        self._setup_base_properties()

        # Template Method Pattern
        self._setup_ui()
        self._connect_signals()

        self.logger.info(f"✅ {self.__class__.__name__} 초기화 완료")

    def _setup_logging(self, logging_service):
        """로깅 설정 - 공통 패턴"""
        if logging_service:
            component_name = self.__class__.__name__
            self.logger = logging_service.get_component_logger(component_name)
        else:
            raise ValueError(f"{self.__class__.__name__}에 logging_service가 주입되지 않았습니다")

    def _setup_base_properties(self):
        """기본 속성 설정 - 공통 패턴"""
        component_name = self.__class__.__name__.lower().replace('view', '').replace('settings', '')
        self.setObjectName(f"widget-{component_name}-view")
        self.presenter = None

    def set_presenter(self, presenter):
        """Presenter 설정 - 공통 패턴"""
        expected_type = self.get_expected_presenter_type()
        if not isinstance(presenter, expected_type):
            raise TypeError(f"{expected_type.__name__} 타입이어야 합니다")

        self.presenter = presenter
        self.logger.info(f"✅ Presenter 연결 완료")

    @abstractmethod
    def get_expected_presenter_type(self):
        """예상되는 Presenter 타입 - 하위 클래스 구현"""
        pass

    @abstractmethod
    def _setup_ui(self):
        """UI 구성 - 하위 클래스 구현"""
        pass

    @abstractmethod
    def _connect_signals(self):
        """시그널 연결 - 하위 클래스 구현"""
        pass

    def _create_standard_button_layout(self) -> 'QHBoxLayout':
        """표준 버튼 레이아웃 생성 - 공통 패턴"""
        from PyQt6.QtWidgets import QHBoxLayout, QPushButton

        button_layout = QHBoxLayout()

        # 저장 버튼 (공통)
        self.save_button = QPushButton("저장")
        component_name = self.__class__.__name__.lower().replace('view', '').replace('settings', '')
        self.save_button.setObjectName(f"button-save-{component_name}")
        button_layout.addWidget(self.save_button)

        return button_layout

    # 표준 피드백 메서드들
    def show_success(self, message: str):
        """성공 메시지 표시 - 공통 패턴"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "성공", message)

    def show_error(self, message: str):
        """오류 메시지 표시 - 공통 패턴"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "오류", message)

    def show_loading(self, message: str):
        """로딩 상태 표시 - 공통 패턴"""
        # 기본 구현: 상태 바 또는 커서 변경
        self.setCursor(Qt.CursorShape.WaitCursor)

    def hide_loading(self):
        """로딩 해제 - 공통 패턴"""
        self.setCursor(Qt.CursorShape.ArrowCursor)
```

## 🔧 Mixin Patterns

### 1. ValidationMixin

```python
class ValidationMixin:
    """검증 관련 공통 기능"""

    def validate_required_fields(self, data: Dict[str, Any], required_fields: list) -> Tuple[bool, str]:
        """필수 필드 검증"""
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return False, f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}"
        return True, ""

    def validate_field_format(self, value: str, pattern: str, field_name: str) -> Tuple[bool, str]:
        """필드 형식 검증"""
        import re
        if not re.match(pattern, value):
            return False, f"{field_name} 형식이 올바르지 않습니다"
        return True, ""
```

### 2. TransactionMixin

```python
class TransactionMixin:
    """트랜잭션 관련 공통 기능"""

    def execute_with_commit(self, operation_func, *args, **kwargs):
        """트랜잭션과 함께 실행 - Repository 패턴에서 사용"""
        try:
            result = operation_func(*args, **kwargs)
            # Repository에서 명시적 커밋 필요 (API Settings Factory에서 발견된 패턴)
            if hasattr(self, 'repository') and hasattr(self.repository, '_connection'):
                self.repository._connection.commit()
            return result
        except Exception as e:
            if hasattr(self, 'repository') and hasattr(self.repository, '_connection'):
                self.repository._connection.rollback()
            raise e
```

## 📋 Factory 구현 체크리스트

### 필수 구현 사항

- [ ] `StandardMvpFactory` 상속
- [ ] `_get_required_services()` 구현
- [ ] `_create_view()` 구현
- [ ] `_create_presenter()` 구현
- [ ] Presenter는 `presentation/presenters/settings/` 위치에 배치

### 권장 구현 사항

- [ ] `CommonServicePatterns` 활용
- [ ] `StandardSettingsPresenter` 상속
- [ ] `StandardSettingsView` 상속
- [ ] 필요에 따라 Mixin 활용

### 검증 사항

- [ ] `python run_desktop_ui.py`로 동작 확인
- [ ] Repository 사용 시 명시적 커밋 확인
- [ ] Infrastructure 로깅 시스템 사용
- [ ] MVP 패턴 완전 조립 확인

---

## 🔗 관련 문서

- **MVP_FACTORY_PATTERN_TEMPLATE.md**: 구체적인 구현 템플릿
- **API Settings Factory**: 검증된 성공 사례
- **REPOSITORY_TRANSACTION_COMMIT_PATCH.md**: 트랜잭션 커밋 패치 가이드

이 Base Patterns를 활용하면 Database Settings Factory, UI Settings Factory 등을 더 빠르고 일관성 있게 구현할 수 있습니다.
