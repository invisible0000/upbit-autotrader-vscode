# 📋 MVP 조립 방법 문서화
>
> API Settings Factory에서 검증된 완벽한 MVP 패턴 조립 가이드

## 🎯 MVP 패턴 조립의 핵심 원칙

### Model-View-Presenter 분리와 연결

1. **Model (Services)**: 비즈니스 로직과 데이터 관리
2. **View (UI Components)**: 사용자 인터페이스와 상호작용
3. **Presenter (Business Logic Coordinator)**: View와 Model 사이의 중재자

## 🔧 완벽한 조립 순서 (API Settings 검증 완료)

### 1단계: Factory에서 Services 준비 (Model)

```python
# ApplicationServiceContainer를 통한 서비스 주입
app_container = self._get_application_container()

# 필요한 서비스들 주입
api_key_service = app_container.get_api_key_service()
logging_service = app_container.get_logging_service()
validation_service = app_container.get_validation_service()  # 선택적
```

**핵심 포인트:**

- ✅ DI 컨테이너를 통한 의존성 주입
- ✅ Infrastructure Layer 서비스들을 Model로 활용
- ✅ 서비스 초기화 상태 검증

### 2단계: View 컴포넌트 생성

```python
# View 생성 (순수 UI만)
view = ApiSettingsView(
    parent=parent,
    logging_service=component_logger  # 로깅만 주입
)
```

**핵심 포인트:**

- ✅ View는 UI 렌더링만 담당
- ✅ 비즈니스 로직 없음
- ✅ Presenter 의존성은 외부에서 주입

### 3단계: Presenter 생성 및 연결

```python
# Presenter 생성 (비즈니스 로직 중심)
from presentation.presenters.settings.api_settings_presenter import ApiSettingsPresenter

presenter = ApiSettingsPresenter(
    view=view,                  # View 의존성
    api_key_service=api_key_service,  # Model(Service) 의존성
    logging_service=presenter_logger   # 로깅 의존성
)
```

**핵심 포인트:**

- ✅ Presenter는 `presentation/` 레이어에 위치
- ✅ View와 Service 모두에 의존
- ✅ 비즈니스 로직 완전 격리

### 4단계: MVP 상호 연결

```python
# View ← Presenter 연결
view.set_presenter(presenter)

# 초기 데이터 로드 (Presenter → Model → View)
initial_data = presenter.load_initial_data()
view.update_ui_with_data(initial_data)

# 버튼 상태 동기화
view._update_button_states()
```

**핵심 포인트:**

- ✅ 양방향 의존성 설정
- ✅ 초기화 시점에 데이터 플로우 확립
- ✅ UI 상태와 비즈니스 로직 동기화

## 🔄 런타임 상호작용 패턴

### View → Presenter (사용자 이벤트)

```python
# View에서
def _on_save_clicked(self):
    if self.presenter:
        data = self._collect_input_data()
        self.presenter.save_data(**data)
```

### Presenter → Model (비즈니스 로직)

```python
# Presenter에서
def save_data(self, **data):
    # 1. 데이터 검증
    if not self._validate_data(**data):
        return False

    # 2. Service를 통한 저장
    success = self.service.save(**data)

    # 3. 결과 처리
    if success:
        self.view.show_success("저장 완료")
    else:
        self.view.show_error("저장 실패")
```

### Model → Presenter → View (결과 반영)

```python
# Service에서 데이터 변경
success = service.save_data(data)

# Presenter에서 View 업데이트
if success:
    self.view.show_success(message)
    self.view.update_ui_with_new_data(data)
```

## 🎯 성공 패턴 체크리스트

### Factory 레벨

- [ ] ApplicationServiceContainer 기반 서비스 주입
- [ ] MVP 3요소 모두 생성
- [ ] 올바른 조립 순서 준수
- [ ] 초기화 완료 후 컴포넌트 반환

### Presenter 레벨

- [ ] `presentation/presenters/` 위치에 배치
- [ ] View와 Service 의존성 모두 받음
- [ ] 비즈니스 로직 완전 분리
- [ ] Infrastructure 로깅 시스템 사용

### View 레벨

- [ ] 순수 UI 컴포넌트로만 구성
- [ ] `set_presenter()` 메서드로 Presenter 주입
- [ ] 사용자 이벤트를 Presenter로 전달
- [ ] Presenter에서 받은 결과로 UI 업데이트

### Service 레벨 (Model)

- [ ] DI 컨테이너를 통한 주입
- [ ] Repository 패턴 사용 시 명시적 커밋
- [ ] 도메인 로직과 Infrastructure 분리
- [ ] 적절한 오류 처리 및 로깅

## ✅ 검증된 성과

이 조립 패턴으로 달성한 결과:

- ✅ **실제 업비트 API 연동**: KRW 37,443원 잔고 확인
- ✅ **데이터베이스 무결성**: 트랜잭션 커밋 완전 동작
- ✅ **MVP 패턴 완성도**: 3계층 완전 분리 및 조립
- ✅ **DI 컨테이너 연동**: ApplicationServiceContainer 기반 완벽 주입

---

**이 패턴을 따르면 Database Settings, UI Settings 등 다른 Factory에서도 동일한 품질의 MVP 구현이 보장됩니다.**
