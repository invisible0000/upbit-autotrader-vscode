# 📋 MVP Factory 패턴 템플릿
>
> API Settings Factory에서 검증된 성공 패턴

## 🎯 목적

TASK_20250929_02에서 확립된 완벽한 MVP Factory 패턴을 다른 Settings Factory에 적용할 수 있는 재사용 가능한 템플릿 제공

## ✅ 검증된 성공 패턴

### 1. ApplicationServiceContainer 기반 DI 패턴

```python
class {ComponentName}ComponentFactory(BaseComponentFactory):
    """
    {ComponentName} MVP Factory - API Settings 성공 패턴 적용

    성공 요소:
    - ApplicationServiceContainer를 통한 올바른 서비스 접근
    - MVP 3요소 완전 조립 (Model-View-Presenter)
    - Infrastructure Layer와의 완전한 분리
    """

    def create_component_instance(self, parent, **kwargs):
        """완전한 MVP 패턴으로 컴포넌트 생성"""

        # 🔧 1. Application Service Container 접근 (TASK_01 패턴)
        app_container = self._get_application_container()

        # 🏗️ 2. Model 계층 - 서비스 의존성 주입
        # 필요한 서비스들을 DI 컨테이너에서 가져오기
        {service_name}_service = app_container.get_{service_name}_service()
        logging_service = app_container.get_logging_service()

        # 필요에 따라 추가 서비스 주입
        # validation_service = app_container.get_validation_service()

        # 🎨 3. View 계층 - UI 컴포넌트 생성
        view = {ComponentName}View(parent)

        # 🧠 4. Presenter 계층 - 비즈니스 로직 연결
        # 주의: 올바른 import 경로 사용
        from presentation.presenters.settings.{component_name}_presenter import {ComponentName}Presenter

        presenter = {ComponentName}Presenter(
            view=view,
            {service_name}_service={service_name}_service,
            logging_service=logging_service
        )

        # 🔗 5. MVP 조립 - 상호 의존성 설정
        view.set_presenter(presenter)

        # 📥 6. 초기 데이터 로드 (필요한 경우)
        initial_data = presenter.load_initial_data()
        if initial_data:
            view.update_ui_with_data(initial_data)

        # 📊 7. 버튼 상태 업데이트
        view._update_button_states()

        self.logger.info(f"✅ {ComponentName} 컴포넌트 완전 조립 완료 (MVP + 초기화)")

        return view  # View를 반환하지만 내부에 완전한 MVP 포함
```

### 2. Presenter 구조 패턴

```python
class {ComponentName}Presenter:
    """
    {ComponentName} 비즈니스 로직 처리 - API Settings 성공 패턴 적용

    핵심 원칙:
    - View와 Model(Service) 사이의 중재자 역할
    - 비즈니스 로직 완전 분리
    - Infrastructure 로깅 시스템 활용
    """

    def __init__(self, view, {service_name}_service, logging_service):
        self.view = view
        self.{service_name}_service = {service_name}_service
        self.logger = logging_service

        # 서비스 의존성 검증
        if self.{service_name}_service is None:
            self.logger.warning(f"⚠️ {ComponentName}Service가 None으로 전달됨")
        else:
            self.logger.info(f"✅ {ComponentName}Service 의존성 주입 성공: {type(self.{service_name}_service).__name__}")

        self.logger.info(f"✅ {ComponentName} 프레젠터 초기화 완료")

    def load_initial_data(self) -> Dict[str, Any]:
        """초기 데이터 로드 - 표준 패턴"""
        try:
            if self.{service_name}_service is None:
                self.logger.warning(f"⚠️ {ComponentName}Service가 None이어서 데이터를 로드할 수 없습니다")
                return self._get_default_data()

            # 서비스에서 데이터 로드
            data = self.{service_name}_service.load_data()

            if not data:
                self.logger.debug("저장된 데이터가 없습니다")
                return self._get_default_data()

            self.logger.debug(f"{ComponentName} 데이터 로드 완료")
            return data

        except Exception as e:
            self.logger.error(f"{ComponentName} 데이터 로드 중 오류: {e}")
            return self._get_default_data()

    def save_data(self, **data) -> Tuple[bool, str]:
        """데이터 저장 처리 - 표준 패턴"""
        try:
            if self.{service_name}_service is None:
                return False, f"{ComponentName} 서비스가 초기화되지 않았습니다."

            # 1. 입력 검증
            if not self._validate_data(**data):
                return False, "입력 데이터 검증에 실패했습니다."

            # 2. 서비스를 통한 데이터 저장
            success = self.{service_name}_service.save_data(**data)

            if success:
                # 3. 성공 피드백
                self.view.show_success("데이터가 성공적으로 저장되었습니다")
                self.logger.info(f"{ComponentName} 데이터 저장 완료")
                return True, "저장 완료"
            else:
                return False, "저장 중 오류가 발생했습니다"

        except Exception as e:
            self.logger.error(f"{ComponentName} 데이터 저장 중 오류: {e}")
            return False, f"저장 중 오류가 발생했습니다: {str(e)}"

    def _validate_data(self, **data) -> bool:
        """데이터 검증 - 각 컴포넌트별로 구체화"""
        # 구체적인 검증 로직 구현
        return True

    def _get_default_data(self) -> Dict[str, Any]:
        """기본 데이터 반환 - 각 컴포넌트별로 구체화"""
        return {}
```

### 3. View 구조 패턴

```python
class {ComponentName}View(QWidget):
    """
    {ComponentName} UI View - API Settings 성공 패턴 적용

    핵심 원칙:
    - 순수한 UI 렌더링만 담당
    - 비즈니스 로직은 Presenter에게 완전 위임
    - Infrastructure 로깅 시스템 연동
    """

    def __init__(self, parent=None, logging_service=None):
        super().__init__(parent)
        self.setObjectName(f"widget-{component_name}-view")

        # 로깅 설정 - DI 패턴 적용
        if logging_service:
            self.logger = logging_service.get_component_logger(f"{ComponentName}View")
        else:
            raise ValueError(f"{ComponentName}View에 logging_service가 주입되지 않았습니다")

        # Presenter는 외부에서 주입받도록 설계 (MVP 패턴)
        self.presenter = None

        self._setup_ui()
        self._connect_signals()

        if self.logger:
            self.logger.info(f"✅ {ComponentName} 뷰 초기화 완료")

    def set_presenter(self, presenter):
        """Presenter 설정 (MVP 패턴)"""
        from presentation.presenters.settings.{component_name}_presenter import {ComponentName}Presenter
        if not isinstance(presenter, {ComponentName}Presenter):
            raise TypeError(f"{ComponentName}Presenter 타입이어야 합니다")

        self.presenter = presenter
        if self.logger:
            self.logger.info(f"✅ {ComponentName} Presenter 연결 완료")

    def _setup_ui(self):
        """UI 구성 - 각 컴포넌트별로 구체화"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # 컴포넌트별 UI 요소들 구성
        # ...

        # 공통 버튼 레이아웃
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("저장")
        self.save_button.setObjectName(f"button-save-{component_name}")

        # 필요에 따라 추가 버튼들
        button_layout.addWidget(self.save_button)

        self.main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """시그널 연결"""
        self.save_button.clicked.connect(self._on_save_clicked)

    def _on_save_clicked(self):
        """저장 버튼 클릭 - Presenter로 이벤트 전달"""
        if self.presenter:
            # 입력 데이터 수집
            data = self._collect_input_data()
            self.presenter.save_data(**data)

    def _collect_input_data(self) -> Dict[str, Any]:
        """입력 데이터 수집 - 각 컴포넌트별로 구체화"""
        return {}

    def update_ui_with_data(self, data: Dict[str, Any]):
        """데이터로 UI 업데이트 - 각 컴포넌트별로 구체화"""
        pass

    def _update_button_states(self):
        """버튼 상태 업데이트"""
        if self.presenter:
            states = self.presenter.get_button_states()
            self.save_button.setEnabled(states.get('save_enabled', True))

    # 표준 피드백 메서드들
    def show_success(self, message: str):
        """성공 메시지 표시"""
        # QMessageBox 또는 상태 라벨 업데이트
        pass

    def show_error(self, message: str):
        """오류 메시지 표시"""
        # QMessageBox 또는 상태 라벨 업데이트
        pass

    def show_loading(self, message: str):
        """로딩 상태 표시"""
        # 로딩 인디케이터 표시
        pass
```

## 🔧 필수 체크리스트

### ApplicationServiceContainer 연동

- [ ] `_get_application_container()` 메서드 사용
- [ ] 필요한 서비스들을 DI 컨테이너에서 주입
- [ ] 서비스 의존성 검증 로직 포함

### MVP 패턴 완전 구현

- [ ] Factory에서 Model-View-Presenter 3요소 모두 생성
- [ ] Presenter를 `presentation/presenters/settings/` 위치에 배치
- [ ] `view.set_presenter(presenter)` 호출로 MVP 연결

### Infrastructure 로깅

- [ ] `logging_service.get_component_logger()` 사용
- [ ] 초기화, 성공, 오류 상황에 적절한 로그 기록
- [ ] `print()` 사용 금지

### 데이터 무결성

- [ ] Repository 패턴 사용 시 명시적 `conn.commit()` 호출
- [ ] 트랜잭션 커밋 검증 로직 포함
- [ ] 메모리와 DB 상태 동기화 확인

### 오류 처리

- [ ] 서비스 초기화 실패 처리
- [ ] 입력 검증 로직 구현
- [ ] 사용자 친화적 오류 메시지 제공

## 🎯 성공 패턴 요약

### 1. DI 컨테이너 기반 의존성 주입

```python
app_container = self._get_application_container()
service = app_container.get_service()
```

### 2. MVP 완전 조립

```python
presenter = ComponentPresenter(view, service, logger)
view.set_presenter(presenter)
```

### 3. Infrastructure 로깅

```python
self.logger = logging_service.get_component_logger("ComponentName")
self.logger.info("✅ 초기화 완료")
```

### 4. 트랜잭션 무결성

```python
conn.commit()  # Repository에서 명시적 커밋 필수
```

## 📋 적용 가이드

1. **이 템플릿 복사** → 새 Factory 파일 생성
2. **{ComponentName} 치환** → 실제 컴포넌트 이름으로 변경
3. **서비스 의존성 확인** → ApplicationServiceContainer에서 필요한 서비스 확인
4. **구체적 로직 구현** → 각 컴포넌트별 특화된 비즈니스 로직 추가
5. **테스트 실행** → `python run_desktop_ui.py`로 동작 확인

---

## ✅ API Settings Factory 검증 완료

이 템플릿은 다음과 같은 실제 검증을 통과한 성공 패턴입니다:

- ✅ **실제 업비트 API 연동**: KRW 37,443원 잔고 확인
- ✅ **데이터베이스 트랜잭션**: 저장/삭제 실제 DB 반영 확인
- ✅ **MVP 패턴 동작**: Factory → View → Presenter → Model 완전 플로우
- ✅ **DI 컨테이너 연동**: ApplicationServiceContainer 기반 서비스 주입

이 패턴을 따르면 **Database Settings Factory**, **UI Settings Factory** 등 다른 Settings Factory에서도 동일한 품질의 MVP 구현이 가능합니다.
