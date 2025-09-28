# UI Layer (사용자 인터페이스 계층)

## 🎯 UI 계층이란?

**사용자와 상호작용**하는 곳입니다. 버튼, 텍스트박스, 화면 등 **보이는 모든 것**들이 여기 있습니다.

- **MVP 패턴** 사용: View(보여주기) + Presenter(처리하기)
- **Application Layer만 호출** (Domain, Infrastructure 직접 호출 금지)

## 📂 폴더 구조

```
ui/desktop/screens/settings/environment_profile/
├── environment_profile_view.py        # 메인 뷰 (MVP의 V)
├── presenters/
│   └── environment_profile_presenter.py  # 프레젠터 (MVP의 P)
└── widgets/
    ├── profile_selector_section.py       # 프로파일 선택기
    ├── yaml_editor_section.py            # YAML 편집기
    ├── quick_environment_buttons.py      # 퀵 환경 버튼
    ├── yaml_syntax_highlighter.py        # YAML 구문 강조
    ├── advanced_yaml_text_edit.py        # 고급 YAML 편집기
    └── profile_metadata_dialog.py        # 메타데이터 다이얼로그
```

## 🎭 MVP 패턴 설명

### View (뷰) - "화면에 보이는 것"

- **UI 요소들**: 버튼, 텍스트박스, 레이아웃
- **사용자 입력 받기**: 클릭, 타이핑 등
- **화면에 결과 표시**: 텍스트 출력, 색상 변경 등
- **비즈니스 로직 없음**: 단순히 보여주고 받기만

### Presenter (프레젠터) - "실제 처리하는 것"

- **View에서 온 입력 처리**: "저장 버튼 눌렸네, 어떻게 할까?"
- **Application Service 호출**: 실제 저장 작업 요청
- **결과를 View에게 전달**: "저장 완료, 화면 업데이트해줘"

## 🔄 현재 Environment Profile 시스템 구조

### View (environment_profile_view.py)

```python
class EnvironmentProfileView(QWidget):
    # 시그널 정의 (사용자 액션을 Presenter에게 알림)
    profile_selected = pyqtSignal(str)
    environment_quick_switch = pyqtSignal(str)
    edit_mode_requested = pyqtSignal()
    save_requested = pyqtSignal(str, str)

    def __init__(self):
        # UI 레이아웃 설정
        self._setup_splitter_layout()    # 좌우 1:2 분할
        self._setup_profile_selector()   # 왼쪽: 프로파일 선택기
        self._setup_yaml_editor()        # 오른쪽: YAML 편집기
        self._connect_signals()          # 시그널 연결
```

### Presenter (environment_profile_presenter.py)

```python
class EnvironmentProfilePresenter:
    def __init__(self, view):
        self.view = view
        # Application Services 주입
        self.metadata_service = ProfileMetadataService()
        self.session_service = ProfileEditSessionService()
        self.validation_service = ProfileValidationService()

    # View에서 온 시그널 처리
    def _on_environment_quick_switch(self, env_name):
        # 1. 환경에 맞는 프로파일 로드
        # 2. YAML 내용 표시
        # 3. View 업데이트
```

## 🚀 현재 구현된 기능들

### Profile Selector Section (프로파일 선택기)

- **QuickEnvironmentButtons**: development/production/testing 버튼
- **프로파일 콤보박스**: 사용 가능한 프로파일 목록
- **액션 버튼들**: 적용, 저장, 삭제 버튼

### YAML Editor Section (YAML 편집기)

- **YamlSyntaxHighlighter**: YAML 구문 강조
- **AdvancedYamlTextEdit**: 고급 편집 기능
- **실시간 검증**: 타이핑하면서 오류 체크

### 시그널 흐름

```
사용자가 "development" 버튼 클릭
    ↓
QuickEnvironmentButtons.environment_selected 시그널 발생
    ↓
ProfileSelectorSection.environment_quick_switch 시그널 전달
    ↓
EnvironmentProfileView.environment_quick_switch 시그널 전달
    ↓
EnvironmentProfilePresenter._on_environment_quick_switch() 호출
    ↓
Application Services 호출하여 실제 작업 수행
    ↓
View 업데이트
```

## 🐛 현재 발견된 문제들과 해결 방안

### 1. 콤보박스 목록이 비어있음

**원인**: Presenter 초기화 시 프로파일 목록 로드 안함
**해결**: `_initialize_data()` 메서드에서 프로파일 목록 로드

### 2. 기본 환경 프로파일 편집 방지 필요

**원인**: development/production/testing은 보호되어야 함
**해결**: 편집 모드 진입 시 프로파일 타입 체크

### 3. Infrastructure 서비스 미활용

**원인**: Application Service에서 Infrastructure 제대로 안씀
**해결**: ProfileMetadataService 등에 Infrastructure 서비스 주입

## 🔧 해결해야 할 작업들

### 1. Presenter 초기화 개선

```python
def _initialize_data(self):
    # 프로파일 목록 로드하여 콤보박스에 설정
    profiles = self.metadata_service.list_all_profiles()
    self.view.profile_selector.update_profile_list(profiles)
```

### 2. 프로파일 보호 로직 추가

```python
def _on_edit_mode_requested(self):
    current_profile = self.view.get_selected_profile()
    if current_profile in ['development', 'production', 'testing']:
        # 기본 환경 프로파일은 편집 불가
        self.view.show_warning("기본 환경 프로파일은 편집할 수 없습니다")
        return
```

### 3. Infrastructure 서비스 연동

Application Service들에 Infrastructure 서비스 주입하여 실제 파일 처리

## 📋 사용자 수용 테스트 체크리스트

- [ ] development 버튼 클릭 → 프로파일 정보 표시
- [ ] 콤보박스에 프로파일 목록 표시
- [ ] 우측 편집기에 YAML 내용 출력
- [ ] 기본 환경 프로파일 편집 방지
- [ ] 기본 환경 프로파일 삭제 방지
- [ ] Infrastructure 서비스 활용
