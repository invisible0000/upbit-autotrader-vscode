# TASK-07: MainWindow DDD/MVP 리팩터링

## 📋 태스크 개요
- **목표**: 1148줄의 거대한 MainWindow를 DDD/MVP 패턴으로 분산 리팩터링
- **우선순위**: 높음 (아키텍처 개선 핵심)
- **예상 결과**: MainWindow 200-300줄로 축소, 서비스별 분리

## 🎯 분산 전략
### Phase 1: ScreenManagerService 분리 [✅]
- `_load_screen_lazy()` → Application Layer의 ScreenManagerService ✅
- `_change_screen()` → ScreenManagerService.change_screen() ✅
- `_add_screens()` → ScreenManagerService.initialize_screens() ✅

### Phase 2: WindowStateService 분리 [✅]
- `_load_window_state()` → WindowStateService.load_window_state() ✅
- `_save_settings()` → WindowStateService.save_window_state() ✅
- `_reset_window_size()` → WindowStateService.reset_window_size() ✅
- `_reset_window_size_medium()` → WindowStateService.reset_window_size_medium() ✅

### Phase 3: MenuService 분리 [ ]
- `_setup_menu_bar()` → MenuService

### Phase 4: MainWindowPresenter 생성 [ ]
- Presentation Logic 분리
- 의존성 주입 패턴 적용

## 🏗️ 목표 구조
```
MainWindow (View - PyQt6 UI만)
├── MainWindowPresenter (Presentation Logic)
├── WindowStateService (Application Service)
├── ScreenManagerService (Application Service)
├── ThemeManagerService (Application Service)
└── NavigationService (Application Service)
```

## 📍 현재 상태
- [x] 문제 인식 및 분석 완료
- [✅] **Phase 1 완료** (ScreenManagerService)
  - ✅ IScreenManagerService 인터페이스 정의
  - ✅ ScreenManagerService 구현 (Application Layer)
  - ✅ MainWindow에서 의존성 주입 및 사용
  - ✅ 기존 메서드들 리팩터링 (_add_screens, _change_screen, _load_screen_lazy)
  - ✅ Legacy 폴백 메커니즘 구현
  - ✅ 동작 검증 완료 (`python run_desktop_ui.py`)
- [✅] **Phase 2 완료** (WindowStateService)
  - ✅ IWindowStateService 인터페이스 정의
  - ✅ WindowStateService 구현 (Application Layer)
  - ✅ MainWindow에서 의존성 주입 및 사용
  - ✅ 기존 메서드들 리팩터링 (_load_window_state, _save_settings, _reset_window_size)
  - ✅ SettingsService 우선, QSettings 폴백 메커니즘 구현
  - ✅ 동작 검증 완료 (창 상태 로드/저장 정상 동작)
- [ ] Phase 3 시작 예정 (MenuService)
- [ ] 테스트 코드 작성
- [ ] 점진적 마이그레이션

## 🔗 연관 파일
- `upbit_auto_trading/ui/desktop/main_window.py` (1148줄)
- `upbit_auto_trading/application/` (서비스 레이어)
- `upbit_auto_trading/infrastructure/` (DI Container)

## 📝 참고사항
- DDD Golden Rules 준수
- 기존 기능 무결성 보장
- 점진적 리팩터링 (Big Bang 방식 금지)
