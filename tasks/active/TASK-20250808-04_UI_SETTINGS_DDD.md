# 🎨 TASK-20250808-04: UI 설정 탭 DDD 리팩토링

## 📋 **태스크 개요**

**목표**: UI 설정 탭을 완전한 DDD/DTO/MVP 패턴으로 리팩토링
**전제조건**: TASK-20250808-01 완료 (DDD 기반 구조)
**예상 기간**: 1-2 작업 세션

## 🎯 **UI 설정 탭 기능**

### **1. 테마 관리**
- **라이트/다크 모드**: 시스템 테마 자동 감지
- **커스텀 테마**: 사용자 정의 색상 조합
- **테마 미리보기**: 실시간 테마 변경 미리보기
- **테마 저장/불러오기**: 커스텀 테마 관리

### **2. 폰트 및 크기 설정**
- **폰트 패밀리**: 시스템 폰트 선택
- **폰트 크기**: 가독성을 위한 크기 조절
- **줄 간격**: 텍스트 가독성 최적화
- **폰트 미리보기**: 설정 즉시 반영

### **3. 레이아웃 설정**
- **창 레이아웃**: 위젯 배치 커스터마이징
- **사이드바 설정**: 네비게이션 바 위치/크기
- **상태바 설정**: 정보 표시 항목 선택
- **툴바 커스터마이징**: 자주 사용하는 기능 배치

### **4. 접근성 설정**
- **고대비 모드**: 시각 장애인 지원
- **큰 텍스트 모드**: 텍스트 확대
- **키보드 네비게이션**: 키보드만으로 조작
- **스크린 리더 지원**: ARIA 라벨 및 설명

## 🏗️ **DDD 아키텍처 설계**

### **Domain Layer**
```
📁 upbit_auto_trading/domain/ui_settings/
├── entities/
│   ├── theme_configuration.py          # 테마 구성 엔티티
│   ├── font_configuration.py           # 폰트 설정 엔티티
│   ├── layout_preference.py            # 레이아웃 설정 엔티티
│   └── accessibility_setting.py        # 접근성 설정 엔티티
├── value_objects/
│   ├── color_scheme.py                 # 색상 체계 값 객체
│   ├── font_family.py                  # 폰트 패밀리 값 객체
│   ├── font_size.py                    # 폰트 크기 값 객체
│   ├── window_layout.py                # 창 레이아웃 값 객체
│   └── accessibility_level.py          # 접근성 레벨 값 객체
├── services/
│   ├── theme_validation_service.py     # 테마 검증 도메인 서비스
│   ├── layout_optimization_service.py  # 레이아웃 최적화 서비스
│   └── accessibility_service.py        # 접근성 지원 서비스
└── repositories/
    ├── itheme_repository.py            # 테마 저장소 인터페이스
    ├── ifont_repository.py             # 폰트 저장소 인터페이스
    ├── ilayout_repository.py           # 레이아웃 저장소 인터페이스
    └── iaccessibility_repository.py    # 접근성 저장소 인터페이스
```

### **Application Layer**
```
📁 upbit_auto_trading/application/ui_settings/
├── use_cases/
│   ├── change_theme_use_case.py        # 테마 변경 Use Case
│   ├── customize_font_use_case.py      # 폰트 커스터마이징 Use Case
│   ├── arrange_layout_use_case.py      # 레이아웃 배치 Use Case
│   ├── apply_accessibility_use_case.py # 접근성 적용 Use Case
│   ├── preview_theme_use_case.py       # 테마 미리보기 Use Case
│   └── reset_ui_settings_use_case.py   # UI 설정 초기화 Use Case
├── services/
│   ├── ui_application_service.py       # UI 애플리케이션 서비스
│   └── theme_orchestration_service.py  # 테마 오케스트레이션 서비스
└── dtos/
    ├── theme_change_dto.py             # 테마 변경 DTO
    ├── font_configuration_dto.py       # 폰트 설정 DTO
    ├── layout_arrangement_dto.py       # 레이아웃 배치 DTO
    ├── accessibility_config_dto.py     # 접근성 설정 DTO
    └── ui_preview_dto.py               # UI 미리보기 DTO
```

### **Infrastructure Layer**
```
📁 upbit_auto_trading/infrastructure/ui_settings/
├── repositories/
│   ├── theme_repository.py             # 테마 Repository 구현체
│   ├── font_repository.py              # 폰트 Repository 구현체
│   ├── layout_repository.py            # 레이아웃 Repository 구현체
│   └── accessibility_repository.py     # 접근성 Repository 구현체
├── services/
│   ├── system_theme_detector.py        # 시스템 테마 감지 서비스
│   ├── font_discovery_service.py       # 시스템 폰트 발견 서비스
│   └── screen_reader_service.py        # 스크린 리더 연동 서비스
└── persistence/
    ├── theme_persistence.py            # 테마 영속성 관리
    └── ui_settings_persistence.py      # UI 설정 영속성 관리
```

### **Presentation Layer (MVP)**
```
📁 upbit_auto_trading/ui/desktop/screens/settings/ui_settings/
├── presenters/
│   ├── ui_settings_presenter.py        # UI 설정 메인 프레젠터
│   ├── theme_selector_presenter.py     # 테마 선택 프레젠터
│   ├── font_configuration_presenter.py # 폰트 설정 프레젠터
│   ├── layout_designer_presenter.py    # 레이아웃 디자이너 프레젠터
│   └── accessibility_presenter.py      # 접근성 프레젠터
├── views/
│   ├── ui_settings_view.py             # UI 설정 뷰 인터페이스
│   ├── theme_selector_view.py          # 테마 선택 뷰 인터페이스
│   ├── font_configuration_view.py      # 폰트 설정 뷰 인터페이스
│   ├── layout_designer_view.py         # 레이아웃 디자이너 뷰 인터페이스
│   └── accessibility_view.py           # 접근성 뷰 인터페이스
├── widgets/
│   ├── ui_settings_widget.py           # UI 설정 메인 위젯
│   ├── theme_selector_widget.py        # 테마 선택 위젯
│   ├── color_picker_widget.py          # 색상 선택 위젯
│   ├── font_configuration_widget.py    # 폰트 설정 위젯
│   ├── layout_designer_widget.py       # 레이아웃 디자이너 위젯
│   ├── accessibility_widget.py         # 접근성 설정 위젯
│   └── ui_preview_widget.py            # UI 미리보기 위젯
└── dialogs/
    ├── custom_theme_dialog.py          # 커스텀 테마 생성 대화상자
    └── layout_reset_dialog.py          # 레이아웃 초기화 확인 대화상자
```

## 📝 **작업 단계**

### **Phase 1: Domain Layer 구축**
- [ ] **1.1** 테마 도메인 구현
  - ThemeConfiguration 엔티티
  - ColorScheme 값 객체
  - ThemeValidationService

- [ ] **1.2** 폰트 도메인 구현
  - FontConfiguration 엔티티
  - FontFamily, FontSize 값 객체

- [ ] **1.3** 레이아웃 도메인 구현
  - LayoutPreference 엔티티
  - WindowLayout 값 객체
  - LayoutOptimizationService

- [ ] **1.4** 접근성 도메인 구현
  - AccessibilitySetting 엔티티
  - AccessibilityLevel 값 객체
  - AccessibilityService

### **Phase 2: Application Layer 구축**
- [ ] **2.1** 테마 Use Cases
  - ChangeThemeUseCase
  - PreviewThemeUseCase

- [ ] **2.2** 폰트 Use Cases
  - CustomizeFontUseCase

- [ ] **2.3** 레이아웃 Use Cases
  - ArrangeLayoutUseCase

- [ ] **2.4** 접근성 Use Cases
  - ApplyAccessibilityUseCase

### **Phase 3: Infrastructure Layer 구현**
- [ ] **3.1** Repository 구현체
  - ThemeRepository (JSON/YAML 기반)
  - FontRepository
  - LayoutRepository
  - AccessibilityRepository

- [ ] **3.2** 시스템 연동 서비스
  - SystemThemeDetector
  - FontDiscoveryService
  - ScreenReaderService

### **Phase 4: Presentation Layer MVP 구현**
- [ ] **4.1** 테마 MVP
  - ThemeSelectorPresenter
  - ThemeSelectorWidget
  - 실시간 미리보기 기능

- [ ] **4.2** 폰트 MVP
  - FontConfigurationPresenter
  - FontConfigurationWidget

- [ ] **4.3** 레이아웃 MVP
  - LayoutDesignerPresenter
  - LayoutDesignerWidget

- [ ] **4.4** 접근성 MVP
  - AccessibilityPresenter
  - AccessibilityWidget

## 🎨 **UI/UX 사양**

### **테마 선택 UI**
- **테마 카드**: 미리보기가 포함된 테마 선택 카드
- **실시간 미리보기**: 선택 즉시 UI 반영
- **커스텀 테마 생성**: 색상 조합 직접 설정
- **테마 가져오기/내보내기**: JSON 형태로 테마 공유

### **폰트 설정 UI**
- **폰트 미리보기**: 실제 텍스트로 폰트 확인
- **크기 슬라이더**: 직관적인 크기 조절
- **가독성 테스트**: 다양한 텍스트로 가독성 확인

### **레이아웃 디자이너**
- **드래그 앤 드롭**: 위젯 위치 직접 조작
- **그리드 시스템**: 정렬을 위한 그리드 가이드
- **프리셋 레이아웃**: 미리 정의된 레이아웃 선택

### **접근성 설정**
- **고대비 모드**: 명확한 대비 색상
- **확대 설정**: 텍스트 및 UI 요소 확대
- **키보드 네비게이션**: Tab 키 순서 최적화

## 📊 **성공 기준**

### **기능적 기준**
- [ ] 모든 테마 변경이 즉시 반영
- [ ] 폰트 설정이 전체 UI에 적용
- [ ] 레이아웃 변경 후 재시작 시 유지
- [ ] 접근성 설정이 모든 화면에 적용

### **성능 기준**
- [ ] 테마 변경 시간 < 0.5초
- [ ] 폰트 변경 시간 < 0.3초
- [ ] 레이아웃 변경 시간 < 1초
- [ ] 설정 저장 시간 < 0.1초

### **사용성 기준**
- [ ] 직관적인 설정 인터페이스
- [ ] 명확한 미리보기 기능
- [ ] 설정 되돌리기 기능
- [ ] 설정 검색 및 필터링

### **접근성 기준**
- [ ] WCAG 2.1 AA 수준 준수
- [ ] 키보드만으로 모든 기능 접근 가능
- [ ] 스크린 리더 완전 지원
- [ ] 색상에 의존하지 않는 정보 전달

## 🧪 **테스트 전략**

### **단위 테스트**
- [ ] 각 Use Case별 테스트
- [ ] 도메인 서비스 테스트
- [ ] 값 객체 불변성 테스트

### **통합 테스트**
- [ ] Repository 구현체 테스트
- [ ] Presenter-View 상호작용 테스트
- [ ] 시스템 연동 서비스 테스트

### **UI 테스트**
- [ ] 테마 변경 시나리오 테스트
- [ ] 폰트 설정 시나리오 테스트
- [ ] 레이아웃 변경 시나리오 테스트
- [ ] 접근성 기능 테스트

---
**작업 시작일**: 2025-08-08
**전제조건**: TASK-20250808-01 완료
**다음 태스크**: TASK-20250808-05 (API 키 설정 탭)
